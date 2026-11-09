"""Disposable cache boundaries; fake upstreams never qualify a public provider."""
from __future__ import annotations

import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.parse
import urllib.request

from scripts import source9_rehearsal_fork as cache


ANCHOR = 123456
BLOCK_HASH = '0x' + 'a' * 64
ACCOUNT = '0x' + '1' * 40
TX_HASH = '0x' + 'c' * 64


def receipt():
    return {'transactionHash': TX_HASH, 'blockHash': BLOCK_HASH, 'blockNumber': hex(ANCHOR),
        'transactionIndex': '0x0', 'from': ACCOUNT, 'to': None, 'contractAddress': ACCOUNT,
        'cumulativeGasUsed': '0x5208', 'gasUsed': '0x5208', 'status': '0x1',
        'logs': [], 'logsBloom': '0x' + '0' * 512}


def transaction(*, pending=False):
    return {'hash': TX_HASH, 'from': ACCOUNT, 'to': None, 'input': '0x6001',
        'value': '0x0', 'nonce': '0x1', 'gas': '0x5208',
        'blockHash': None if pending else BLOCK_HASH, 'blockNumber': None if pending else hex(ANCHOR),
        'transactionIndex': None if pending else '0x0'}


def request(method, params=None, identifier=1):
    return cache._bytes({'jsonrpc': '2.0', 'id': identifier, 'method': method, 'params': params or []})


def response(body, result):
    return 200, cache._bytes({'jsonrpc': '2.0', 'id': json.loads(body)['id'], 'result': result})


class ForkCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / 'evidence'

    def core(self, post):
        now = [0.0]
        self.sleeps = []
        def sleep(seconds):
            self.sleeps.append(seconds)
            now[0] += seconds
        result = cache._ForkCache(cache.PUBLIC_ENDPOINT, ANCHOR, BLOCK_HASH, self.directory,
            3, _post=post, _clock=lambda: now[0], _sleep=sleep)
        self.addCleanup(result.close, False)
        return result

    def test_endpoint_pin_and_new_evidence_are_required(self):
        for endpoint in ('http://127.0.0.1:1234', 'https://rpc.example.org',
                         cache.PUBLIC_ENDPOINT + '/PRIVATE_SENTINEL',
                         'https://user:PRIVATE_SENTINEL@robinhood.rpc.pinax.network'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                cache._ForkCache(endpoint, ANCHOR, BLOCK_HASH, self.directory, 3)
        self.assertFalse(self.directory.exists())
        self.directory.mkdir()
        with self.assertRaises(FileExistsError):
            cache._ForkCache(cache.PUBLIC_ENDPOINT, ANCHOR, BLOCK_HASH, self.directory, 3)

    def test_exact_immutable_cache_rewraps_ids_and_never_caches_latest_or_errors(self):
        calls = []
        def post(body):
            selected = json.loads(body)
            calls.append(selected)
            if selected['method'] == 'eth_getProof':
                return 200, cache._bytes({'jsonrpc': '2.0', 'id': selected['id'],
                    'error': {'code': -32601, 'message': 'PRIVATE_SENTINEL', 'data': 'PRIVATE_SENTINEL'}})
            return response(body, '0x6001')
        core = self.core(post)
        for index, block in enumerate((hex(ANCHOR), {'blockHash': BLOCK_HASH, 'requireCanonical': True}, '0x0')):
            for identifier in (10 + index, 'different-id'):
                status, raw = core.handle(request('eth_getCode', [ACCOUNT, block], identifier))
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(raw)['id'], identifier)
                self.assertEqual(json.loads(raw)['result'], '0x6001')
        self.assertEqual(len(calls), 3)
        for block in ('latest', 'pending', hex(ANCHOR - 1), {'blockHash': BLOCK_HASH, 'requireCanonical': False}):
            for _ in range(2):
                core.handle(request('eth_getCode', [ACCOUNT, block]))
        self.assertEqual(len(calls), 11)
        for _ in range(2):
            status, raw = core.handle(request('eth_getProof', [ACCOUNT, [], hex(ANCHOR)]))
            self.assertEqual(status, 200)
            self.assertNotIn(b'PRIVATE_SENTINEL', raw)
            self.assertEqual(json.loads(raw)['error']['code'], -32601)
        self.assertEqual(len(calls), 13)
        self.assertEqual(core._counts['cache_hits'], 3)
        self.assertTrue(all(wait >= 1 / 3 - 1e-9 for wait in self.sleeps))
        self.assertNotIn('PRIVATE_SENTINEL', (self.directory / 'events.jsonl').read_text())

    def test_only_429_and_503_retry_three_times_with_recorded_backoff(self):
        calls = []
        def post(body):
            calls.append(body)
            return 429 if len(calls) % 2 else 503, b'PRIVATE_SENTINEL'
        core = self.core(post)
        status, raw = core.handle(request('eth_getBalance', [ACCOUNT, hex(ANCHOR)]))
        self.assertEqual(status, 503)
        self.assertEqual(len(calls), 4)
        self.assertEqual(core._counts['retries'], 3)
        self.assertEqual([wait for wait in self.sleeps if wait >= 1], [1, 2, 4])
        self.assertEqual(len(core._cache), 0)
        self.assertNotIn(b'PRIVATE_SENTINEL', raw)
        events = [json.loads(line) for line in (self.directory / 'events.jsonl').read_text().splitlines()]
        self.assertEqual([row['http_status'] for row in events if row['event'] == 'upstream_attempt'], [429, 503, 429, 503])

    def test_mutations_overrides_duplicates_and_oversized_requests_never_reach_upstream(self):
        calls = []
        core = self.core(lambda body: calls.append(body))
        invalid = [request(method) for method in ('eth_sendTransaction', 'eth_sendRawTransaction',
            'eth_sign', 'personal_unlockAccount', 'anvil_setBalance', 'debug_traceCall')]
        invalid.extend([request('eth_call', [{'to': ACCOUNT}, hex(ANCHOR), {}]),
            b'{"jsonrpc":"2.0","id":1,"method":"eth_chainId","method":"eth_call","params":[]}',
            b'x' * (cache.MAX_REQUEST + 1), request('eth_getCode', [ACCOUNT, {'blockHash': BLOCK_HASH, 'extra': True}])])
        for method in cache.TRANSACTION_READS:
            invalid.extend(request(method, params) for params in ([], [ACCOUNT], [TX_HASH, 'latest'], [{'hash': TX_HASH}]))
        for raw in invalid:
            with self.subTest(raw_length=len(raw)):
                status, answer = core.handle(raw)
                self.assertEqual(status, 403)
                self.assertIn('error', json.loads(answer))
        self.assertEqual(calls, [])
        self.assertEqual(core._counts['rejected_requests'], len(invalid))
        for response in (b'x' * (cache.MAX_RESPONSE + 1),
                b'{"jsonrpc":"2.0","id":1,"result":"0x00","result":"0x01"}',
                b'{"jsonrpc":"2.0","id":1,"result":{"error":"PRIVATE_SENTINEL"}}'):
            core._post = lambda _body, selected=response: (200, selected)
            status, answer = core.handle(request('eth_getCode', [ACCOUNT, hex(ANCHOR)]))
            self.assertEqual(status, 502)
            self.assertEqual(core._cache, {})
            self.assertNotIn(b'PRIVATE_SENTINEL', answer)

    def test_anchor_witness_rejects_mismatch_and_retains_failure(self):
        def post(body):
            selected = json.loads(body)
            return response(body, '0x1237' if selected['method'] == 'eth_chainId' else
                {'hash': '0x' + 'b' * 64, 'number': hex(ANCHOR)})
        core = self.core(post)
        with self.assertRaises(ValueError):
            core.verify_anchor()
        core.close(False)
        summary = json.loads((self.directory / 'summary.json').read_text())
        self.assertFalse(summary['anchor_verified'])
        self.assertFalse(summary['context_completed'])
        self.assertEqual(summary['cached_entries'], 1)

    def test_real_ephemeral_http_context_cleans_up_and_preserves_upstream_data(self):
        seen = []
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                selected = json.loads(body)
                seen.append(selected['method'])
                method = selected['method']
                occurrence = seen.count(method)
                result = ('0x1237' if method == 'eth_chainId' else
                    {'hash': BLOCK_HASH, 'number': hex(ANCHOR), 'test_witness': 'unchanged'} if
                    method == 'eth_getBlockByNumber' else
                    (None if occurrence == 1 else receipt() if occurrence == 2 else
                     {**receipt(), 'transactionHash': '0x' + 'd' * 64}) if method == 'eth_getTransactionReceipt' else
                    (None if occurrence == 1 else transaction(pending=True) if occurrence == 2 else
                     transaction() if occurrence == 3 else {**transaction(), 'blockNumber': None}) if
                    method == 'eth_getTransactionByHash' else '0x60016000')
                _, raw = response(body, result)
                self.send_response(200)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        upstream = f'http://127.0.0.1:{server.server_address[1]}'
        def local_post(_public_url, body):
            with urllib.request.urlopen(urllib.request.Request(upstream, body,
                    {'Content-Type': 'application/json'}), timeout=3) as selected:
                return selected.status, selected.read(cache.MAX_RESPONSE + 1)
        with patch.object(cache, '_https_post', side_effect=local_post):
            with cache.cached_fork_provider(cache.PUBLIC_ENDPOINT, ANCHOR, BLOCK_HASH, self.directory) as provider:
                endpoint = urllib.parse.urlsplit(provider.url)
                connection = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=3)
                connection.request('POST', '/', request('eth_getBlockByNumber', [hex(ANCHOR), False], 90), {'Content-Type': 'application/json'})
                reply = connection.getresponse()
                selected = json.loads(reply.read())
                connection.close()
                self.assertEqual(selected['id'], 90)
                self.assertEqual(selected['result']['test_witness'], 'unchanged')
                self.assertEqual(seen, ['eth_chainId', 'eth_getBlockByNumber'])
                for method, outcomes in (('eth_getTransactionReceipt', [None, receipt(), 'invalid']),
                        ('eth_getTransactionByHash', [None, transaction(pending=True), transaction(), 'invalid'])):
                    for index, expected in enumerate(outcomes):
                        identifier = f'{method}-{index}'
                        connection = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=3)
                        connection.request('POST', '/', request(method, [TX_HASH], identifier), {'Content-Type': 'application/json'})
                        reply = connection.getresponse()
                        selected = json.loads(reply.read())
                        connection.close()
                        self.assertEqual(selected['id'], identifier)
                        if expected == 'invalid':
                            self.assertEqual(reply.status, 502)
                            self.assertIn('error', selected)
                        else:
                            self.assertEqual(reply.status, 200)
                            self.assertEqual(selected['result'], expected)
                    self.assertEqual(seen.count(method), len(outcomes))
            with self.assertRaises(OSError):
                socket.create_connection((endpoint.hostname, endpoint.port), timeout=.2)
        summary = json.loads((self.directory / 'summary.json').read_text())
        self.assertTrue(summary['anchor_verified'])
        self.assertTrue(summary['context_completed'])
        self.assertFalse(summary['production_approved'])
        self.assertEqual(summary['cache_hits'], 1)


if __name__ == '__main__':
    unittest.main()
