"""Real loopback HTTP boundary for opt-in unsigned transaction preparation."""
import contextlib
import http.client
import io
import json
import socket
import threading
import unittest
from unittest.mock import MagicMock, patch

from frontend_api.server import MAX_PREPARATION_BODY, ReadServer, handler, main
from frontend_api.service import Projection, ProjectionError, UnknownNFT, ZERO
from frontend_api.transactions import TransactionInputError, Transactions, MINT_PRICE
from tests_python.test_frontend_api import MockRPC, addr, configuration
from tests_python.test_frontend_transactions import TransactionRPC, transaction_config
from zzz_ops.rpc import RpcError


class Preparer:
    def __init__(self):
        self.calls = []
        self.failure = None

    def prepare(self, payload):
        self.calls.append(payload)
        if self.failure is not None:
            raise self.failure
        return {'schema': 1, 'transaction': {'to': addr(3), 'value': '0x0', 'data': '0x12345678'},
                'signed': False, 'broadcast': False}


class TransactionHTTPTests(unittest.TestCase):
    def setUp(self):
        self.rpc = MockRPC()
        self.projection = Projection(configuration(), self.rpc, clock=lambda: 1000)
        self.preparer = Preparer()
        self.server = ReadServer(('127.0.0.1', 0), handler(self.projection, self.preparer))
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.body = json.dumps({'action': 'mint', 'wallet': addr(30)}).encode()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, *, method='POST', path='/v1/transactions/prepare', body=None, headers=None, half_close=False):
        body = self.body if body is None else body
        if headers is None:
            headers = [('Host', f'127.0.0.1:{self.server.server_port}'),
                       ('Content-Length', str(len(body))), ('Content-Type', 'application/json')]
        request = f'{method} {path} HTTP/1.1\r\n'.encode()
        request += b''.join(f'{name}: {value}\r\n'.encode() for name, value in headers) + b'\r\n' + body
        with socket.create_connection(('127.0.0.1', self.server.server_port), timeout=5) as connection:
            connection.sendall(request)
            if half_close:
                connection.shutdown(socket.SHUT_WR)
            response = http.client.HTTPResponse(connection)
            response.begin()
            try:
                return response.status, dict(response.getheaders()), json.loads(response.read())
            finally:
                response.close()

    def headers(self, *, host=None, length=None, content_type='application/json'):
        return [('Host', host or f'127.0.0.1:{self.server.server_port}'),
                ('Content-Length', str(len(self.body)) if length is None else length),
                ('Content-Type', content_type)]

    def test_enabled_endpoint_only_prepares_unsigned_json_with_no_store(self):
        status, headers, result = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(self.preparer.calls, [json.loads(self.body)])
        self.assertFalse(result['signed'])
        self.assertFalse(result['broadcast'])
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['Connection'], 'close')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertNotIn('Access-Control-Allow-Origin', headers)
        self.assertEqual(self.rpc.calls, [])

    def test_default_handler_still_rejects_post_without_preparation(self):
        self.server.RequestHandlerClass = handler(self.projection)
        status, _, result = self.request()
        self.assertEqual(status, 405)
        self.assertEqual(result, {'error': 'read_only_get_required'})
        self.assertEqual(self.preparer.calls, [])
        self.assertEqual(self.rpc.calls, [])

    def test_read_endpoint_remains_available_when_preparation_enabled(self):
        status, _, result = self.request(method='GET', path=f'/v1/nfts/{self.rpc.nft_id}', body=b'')
        self.assertEqual(status, 200)
        self.assertEqual(result['owner'], addr(30))
        self.assertEqual(self.preparer.calls, [])

    def test_other_methods_paths_and_query_overrides_never_prepare(self):
        for method, path, expected in (('PUT', '/v1/transactions/prepare', 405),
                ('OPTIONS', '/v1/transactions/prepare', 405),
                ('POST', '/v1/transactions/prepare?rpc=SECRET', 404),
                ('POST', '/v1/transactions/prepare/', 404),
                ('POST', '/v1/transactions/send', 404),
                ('GET', '/v1/transactions/prepare', 404)):
            with self.subTest(method=method, path=path):
                status, _, _ = self.request(method=method, path=path, body=b'' if method == 'GET' else None)
                self.assertEqual(status, expected)
        self.assertEqual(self.preparer.calls, [])
        self.assertEqual(self.rpc.calls, [])

    def test_missing_duplicate_and_untrusted_hosts_are_rejected(self):
        base = self.headers()
        for headers in (base[1:], self.headers(host='evil.invalid'),
                        base + [('Host', base[0][1])], self.headers(host='127.0.0.1:1')):
            with self.subTest(headers=headers):
                self.assertEqual(self.request(headers=headers)[0], 400)
        self.assertEqual(self.preparer.calls, [])

    def test_content_length_must_be_single_canonical_and_bounded(self):
        base = self.headers()
        cases = [([base[0], base[2]], 400), (base + [('Content-Length', base[1][1])], 400)]
        cases.extend((self.headers(length=value), 400) for value in ('01', '+1', '-1', '1, 1', '1.0', ''))
        cases.append((self.headers(length=str(MAX_PREPARATION_BODY + 1)), 413))
        for headers, expected in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.request(headers=headers)[0], expected)
        self.assertEqual(self.preparer.calls, [])

    def test_exact_body_limit_is_accepted_without_truncation(self):
        body = self.body + b' ' * (MAX_PREPARATION_BODY - len(self.body))
        self.assertEqual(self.request(body=body)[0], 200)
        self.assertEqual(self.preparer.calls, [json.loads(self.body)])

    def test_incomplete_body_and_transfer_encodings_are_rejected(self):
        self.assertEqual(self.request(body=b'{}', headers=self.headers(length='5'), half_close=True)[0], 400)
        for extra in ([('Transfer-Encoding', 'chunked')], [('Transfer-Encoding', '')], [('Expect', '100-continue')]):
            with self.subTest(extra=extra):
                self.assertEqual(self.request(headers=self.headers() + extra)[0], 400)
        self.assertEqual(self.preparer.calls, [])

    def test_content_type_requires_one_json_header(self):
        for headers in (self.headers()[:-1], self.headers(content_type='text/plain'),
                        self.headers(content_type='application/x-www-form-urlencoded'),
                        self.headers() + [('Content-Type', 'application/json')]):
            with self.subTest(headers=headers):
                self.assertEqual(self.request(headers=headers)[0], 415)
        self.assertEqual(self.preparer.calls, [])
        self.assertEqual(self.request(headers=self.headers(content_type='application/json; charset=utf-8'))[0], 200)

    def test_ambiguous_or_non_json_payloads_are_rejected_before_preparation(self):
        bodies = (b'{"action":"mint","action":"claim"}',
                  b'{"claims":[{"asset":"a","asset":"b"}]}',
                  b'{"wallet":"a","\\u0077allet":"b"}', b'{"amount":NaN}',
                  b'{"amount":Infinity}', b'[]', b'null', b'"mint"', b'{', b'{}{}', b'\xff',
                  b'{"a":' * 1500 + b'0' + b'}' * 1500)
        for body in bodies:
            with self.subTest(body=body[:60]):
                status, _, result = self.request(body=body)
                self.assertEqual(status, 400)
                self.assertEqual(result, {'error': 'invalid_json_body'})
        self.assertEqual(self.preparer.calls, [])

    def test_service_errors_are_typed_and_never_echoed_or_logged(self):
        secret = 'SECRET body provider credentials'
        for error, status, code in ((TransactionInputError(secret), 400, 'invalid_transaction_request'),
                (UnknownNFT(secret), 404, 'nft_not_minted'),
                (ProjectionError(secret), 503, 'transaction_preparation_unavailable'),
                (RpcError(secret), 503, 'transaction_preparation_unavailable'),
                (ValueError(secret), 503, 'transaction_preparation_unavailable'),
                (RuntimeError(secret), 503, 'transaction_preparation_unavailable')):
            with self.subTest(exception=type(error).__name__):
                self.preparer.failure = error
                logs = io.StringIO()
                with contextlib.redirect_stderr(logs):
                    actual, headers, result = self.request()
                self.assertEqual(actual, status)
                self.assertEqual(result, {'error': code})
                self.assertEqual(headers['Cache-Control'], 'no-store')
                self.assertNotIn(secret, json.dumps(result))
                self.assertEqual(logs.getvalue(), '')

    def test_actual_preparer_mint_and_mixed_claims_cross_real_http_boundary(self):
        rpc = TransactionRPC()
        projection = Projection(configuration(), rpc, clock=lambda: 1000)
        self.server.RequestHandlerClass = handler(projection, Transactions(projection, transaction_config(projection)))
        status, _, mint = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(mint['transaction']['to'], addr(3))
        self.assertEqual(mint['transaction']['value'], hex(MINT_PRICE))
        self.assertEqual(mint['transaction']['chainId'], hex(31337))
        self.assertTrue(mint['wallet_revalidation_required'])
        claims = {'action': 'claim', 'wallet': addr(30), 'claims': [
            {'token_id': str(rpc.nft_id), 'asset': addr(21), 'royalty': False},
            {'token_id': str(rpc.nft_id), 'asset': ZERO, 'royalty': True}]}
        status, _, claim = self.request(body=json.dumps(claims).encode())
        self.assertEqual(status, 200)
        self.assertEqual(claim['transaction']['to'], addr(6))
        self.assertEqual(claim['transaction']['value'], '0x0')
        self.assertEqual(len(claim['claim_operations']), 2)
        self.assertEqual(len(rpc.simulations), 2)
        self.assertTrue(all(method in ('eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber',
                                      'eth_getCode', 'eth_call', 'eth_estimateGas', 'eth_gasPrice', 'eth_getBalance') for method, _ in rpc.calls))

    def test_actual_preparer_failed_simulation_never_returns_a_draft(self):
        rpc = TransactionRPC()
        rpc.simulation_error = True
        projection = Projection(configuration(), rpc, clock=lambda: 1000)
        self.server.RequestHandlerClass = handler(projection, Transactions(projection, transaction_config(projection)))
        status, _, result = self.request()
        self.assertEqual(status, 503)
        self.assertEqual(result, {'error': 'transaction_preparation_unavailable'})
        self.assertEqual(len(rpc.simulations), 1)

    def test_cli_flag_is_required_to_construct_the_preparer(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                context = MagicMock()
                context.__enter__.return_value.serve_forever.side_effect = KeyboardInterrupt
                argv = ['frontend_api.server', '--config', 'operator-reviewed.json']
                if enabled:
                    argv += ['--transaction-config', 'reviewed-fees.json']
                output = io.StringIO()
                policy = transaction_config(self.projection)
                reads = [json.dumps(configuration())] + ([json.dumps(policy)] if enabled else [])
                with patch('sys.argv', argv), patch('frontend_api.server.Path.read_text', side_effect=reads), \
                        patch('frontend_api.worker.WorkerPool', return_value=self.projection) as constructor, \
                        patch('frontend_api.server.ReadServer', return_value=context), \
                        patch('frontend_api.server.handler') as route, contextlib.redirect_stdout(output):
                    main()
                route.assert_called_once_with(self.projection, self.projection if enabled else None)
                constructor.assert_called_once_with(configuration(), transaction_config=policy if enabled else None, workers=4)
                self.assertEqual(json.loads(output.getvalue())['transaction_preparation_enabled'], enabled)


if __name__ == '__main__':
    unittest.main()
