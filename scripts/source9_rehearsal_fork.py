"""Disposable fixed-block fork cache, never a production/provider qualification.

The only public transport is the existing documented keyless Pinax endpoint.
All writes/signing/admin methods and state overrides are rejected locally. Only
successful exact-anchor/genesis reads and chain identity can enter this cache.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import re
import threading
import time
from types import SimpleNamespace
import urllib.error
import urllib.parse
import urllib.request


MAX_REQUEST = 1024 * 1024
MAX_RESPONSE = 8 * 1024 * 1024
MAX_CACHE_BYTES = 64 * 1024 * 1024
MAX_CACHE_ENTRIES = 16384
READ_METHODS = frozenset({'eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber',
    'eth_getBlockByHash', 'eth_getCode', 'eth_getBalance', 'eth_getTransactionCount',
    'eth_getStorageAt', 'eth_getProof', 'eth_call', 'eth_getTransactionReceipt',
    'eth_getTransactionByHash'})
TRANSACTION_READS = frozenset({'eth_getTransactionReceipt', 'eth_getTransactionByHash'})
PUBLIC_ENDPOINT = 'https://robinhood.rpc.pinax.network'
QUANTITY = re.compile(r'0x(?:0|[1-9a-f][0-9a-f]{0,63})\Z')
HASH = re.compile(r'0x[0-9a-f]{64}\Z')
ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}\Z')


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _reject_number(_value):
    raise ValueError('Noninteger JSON number')


def _loads(raw):
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject_number,
                      parse_float=_reject_number)


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf8')


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _endpoint(value):
    # Exact allowlisting also excludes credentials, provider keys in paths/query,
    # redirects, non-HTTPS aliases and an accidentally selected private endpoint.
    if value not in (PUBLIC_ENDPOINT, PUBLIC_ENDPOINT + '/'):
        raise ValueError('Only the documented keyless public fork endpoint is permitted')
    return PUBLIC_ENDPOINT


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _https_post(public_url, body):
    request = urllib.request.Request(public_url, body,
        {'Content-Type': 'application/json', 'Accept': 'application/json'}, method='POST')
    # No inherited proxy authentication or redirect target is admitted.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirects())
    try:
        with opener.open(request, timeout=15) as response:
            length = response.headers.get('Content-Length')
            if length is not None and (not length.isdecimal() or int(length) > MAX_RESPONSE):
                raise ValueError('Oversized upstream response')
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError('Oversized upstream response')
            return response.status, raw
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        return status, b''


class _ForkCache:
    """Serialized cache core; the private post/clock hooks serve unit tests only."""
    def __init__(self, public_url, anchor_number, anchor_hash, evidence_dir,
                 requests_per_second, *, _post=None, _clock=time.monotonic, _sleep=None):
        self._public_url = _endpoint(public_url)
        if type(anchor_number) is not int or not 0 < anchor_number < 2**64 or not isinstance(anchor_hash, str) or not HASH.fullmatch(anchor_hash):
            raise ValueError('An explicit integer anchor and lowercase block hash are required')
        if isinstance(requests_per_second, bool) or not isinstance(requests_per_second, (int, float)) or not math.isfinite(requests_per_second) or not 0 < requests_per_second <= 3:
            raise ValueError('Fork upstream rate must be positive and at most three requests per second')
        self.anchor_number, self.anchor_hash = anchor_number, anchor_hash
        self._interval, self._clock = 1 / requests_per_second, _clock
        self._closing = threading.Event()
        self._sleep = _sleep or self._closing.wait
        self._post = _post or (lambda body: _https_post(self._public_url, body))
        self._lock, self._cache, self._last_start = threading.Lock(), {}, None
        self._cache_bytes = 0
        self._verified, self._finished = False, False
        self._directory = Path(evidence_dir).resolve()
        self._directory.mkdir(parents=True, exist_ok=False)
        self._events = (self._directory / 'events.jsonl').open('x', encoding='utf8')
        self._counts = {'requests': 0, 'cache_hits': 0, 'upstream_attempts': 0,
                        'retries': 0, 'rejected_requests': 0}

    def _record(self, event, **fields):
        self._events.write(json.dumps({'time_utc': datetime.now(timezone.utc).isoformat(),
            'event': event, **fields}, sort_keys=True, separators=(',', ':')) + '\n')
        self._events.flush()

    @staticmethod
    def _error(identifier, message, code=-32000):
        return {'jsonrpc': '2.0', 'id': identifier, 'error': {'code': code, 'message': message}}

    @staticmethod
    def _block(value):
        if isinstance(value, str):
            return bool(QUANTITY.fullmatch(value)) or value in ('latest', 'pending', 'earliest', 'safe', 'finalized')
        if not isinstance(value, dict):
            return False
        if set(value) in ({'blockHash'}, {'blockHash', 'requireCanonical'}):
            return isinstance(value['blockHash'], str) and bool(HASH.fullmatch(value['blockHash'])) and (
                'requireCanonical' not in value or type(value['requireCanonical']) is bool)
        return set(value) == {'blockNumber'} and isinstance(value['blockNumber'], str) and bool(QUANTITY.fullmatch(value['blockNumber']))

    def _validate(self, request):
        if not isinstance(request, dict) or set(request) != {'jsonrpc', 'id', 'method', 'params'} or request['jsonrpc'] != '2.0' or (
                type(request['id']) not in (str, int) or isinstance(request['id'], str) and len(request['id']) > 128):
            raise ValueError('Malformed JSON-RPC request')
        method, params = request['method'], request['params']
        if not isinstance(method, str) or method not in READ_METHODS or not isinstance(params, list):
            raise PermissionError('RPC method is not allowlisted')
        if method in ('eth_chainId', 'eth_blockNumber'):
            valid = not params
        elif method == 'eth_getBlockByNumber':
            valid = len(params) == 2 and isinstance(params[0], str) and self._block(params[0]) and type(params[1]) is bool
        elif method == 'eth_getBlockByHash':
            valid = len(params) == 2 and isinstance(params[0], str) and bool(HASH.fullmatch(params[0])) and type(params[1]) is bool
        elif method in TRANSACTION_READS:
            valid = len(params) == 1 and isinstance(params[0], str) and bool(HASH.fullmatch(params[0]))
        elif method == 'eth_call':
            valid = len(params) == 2 and isinstance(params[0], dict) and self._block(params[1]) and set(params[0]) <= {
                'from', 'to', 'data', 'input', 'value', 'gas', 'gasPrice', 'maxFeePerGas', 'maxPriorityFeePerGas', 'accessList', 'type'}
        else:
            expected = 3 if method in ('eth_getStorageAt', 'eth_getProof') else 2
            valid = len(params) == expected and isinstance(params[0], str) and bool(ADDRESS.fullmatch(params[0])) and self._block(params[-1])
            if valid and method == 'eth_getStorageAt':
                valid = isinstance(params[1], str) and bool(re.fullmatch(r'0x[0-9a-fA-F]{1,64}', params[1]))
            if valid and method == 'eth_getProof':
                valid = isinstance(params[1], list) and len(params[1]) <= 1024 and all(isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{1,64}', value) for value in params[1])
        if not valid:
            raise ValueError('Malformed read parameters or unsupported state overrides')
        return method, params

    def _cacheable(self, method, params):
        if method == 'eth_chainId':
            return True
        if method == 'eth_blockNumber' or method in TRANSACTION_READS:
            return False
        if method == 'eth_getBlockByHash':
            return params[0] == self.anchor_hash
        block = params[0] if method == 'eth_getBlockByNumber' else params[-1]
        if isinstance(block, str):
            return block == hex(self.anchor_number) or block == '0x0'
        return (isinstance(block, dict) and block == {'blockHash': self.anchor_hash, 'requireCanonical': True})

    @staticmethod
    def _valid_result(method, result, params):
        if result is None:
            return method in ('eth_getBlockByHash', 'eth_getBlockByNumber') or method in TRANSACTION_READS
        if method in TRANSACTION_READS:
            if not isinstance(result, dict):
                return False
            quantity = lambda value: isinstance(value, str) and bool(QUANTITY.fullmatch(value))
            address = lambda value: isinstance(value, str) and bool(ADDRESS.fullmatch(value))
            block = (isinstance(result.get('blockHash'), str) and bool(HASH.fullmatch(result['blockHash'])) and
                     quantity(result.get('blockNumber')) and quantity(result.get('transactionIndex')))
            if method == 'eth_getTransactionByHash':
                pending = all(key in result and result[key] is None for key in ('blockHash', 'blockNumber', 'transactionIndex'))
                return (result.get('hash') == params[0] and address(result.get('from')) and 'to' in result and
                        (result['to'] is None or address(result['to'])) and (pending or block) and
                        all(quantity(result.get(key)) for key in ('value', 'nonce', 'gas')) and
                        isinstance(result.get('input'), str) and bool(re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', result['input'])))
            return (result.get('transactionHash') == params[0] and block and address(result.get('from')) and
                    'to' in result and (result['to'] is None or address(result['to'])) and
                    'contractAddress' in result and (result['contractAddress'] is None or address(result['contractAddress'])) and
                    all(quantity(result.get(key)) for key in ('cumulativeGasUsed', 'gasUsed')) and
                    result.get('status') in ('0x0', '0x1') and isinstance(result.get('logs'), list) and
                    len(result['logs']) <= 8192 and all(isinstance(item, dict) for item in result['logs']) and
                    isinstance(result.get('logsBloom'), str) and bool(re.fullmatch(r'0x[0-9a-fA-F]{512}', result['logsBloom'])))
        if method in ('eth_chainId', 'eth_blockNumber', 'eth_getBalance', 'eth_getTransactionCount'):
            return isinstance(result, str) and bool(QUANTITY.fullmatch(result))
        if method in ('eth_getCode', 'eth_call'):
            return isinstance(result, str) and bool(re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', result))
        if method == 'eth_getStorageAt':
            return isinstance(result, str) and bool(re.fullmatch(r'0x[0-9a-fA-F]{64}', result))
        if method == 'eth_getProof':
            return isinstance(result, dict) and {'address', 'balance', 'codeHash', 'nonce', 'storageHash', 'accountProof', 'storageProof'} <= set(result)
        return (isinstance(result, dict) and isinstance(result.get('hash'), str) and bool(HASH.fullmatch(result['hash'])) and
                isinstance(result.get('number'), str) and bool(QUANTITY.fullmatch(result['number'])))

    def handle(self, raw):
        identifier, method, key = None, 'invalid', None
        with self._lock:
            if self._closing.is_set():
                return 503, _bytes(self._error(None, 'Disposable fork proxy is closing'))
            self._counts['requests'] += 1
            try:
                if not isinstance(raw, bytes) or len(raw) > MAX_REQUEST:
                    raise ValueError('Malformed JSON-RPC request')
                request = _loads(raw)
                if isinstance(request, dict) and type(request.get('id')) in (str, int):
                    identifier = request['id'] if not isinstance(request['id'], str) or len(request['id']) <= 128 else None
                method, params = self._validate(request)
                key = _digest({'method': method, 'params': params})
            except (ValueError, TypeError, RecursionError, PermissionError):
                self._counts['rejected_requests'] += 1
                self._record('request_rejected', method='not_admitted')
                return 403, _bytes(self._error(identifier, 'Only bounded allowlisted fork reads are permitted', -32600))
            cacheable = self._cacheable(method, params)
            if cacheable and key in self._cache:
                self._counts['cache_hits'] += 1
                self._record('cache_hit', method=method, request_sha256=key)
                return 200, _bytes({'jsonrpc': '2.0', 'id': identifier, 'result': self._cache[key]})
            payload = _bytes({'jsonrpc': '2.0', 'id': identifier, 'method': method, 'params': params})
            for attempt in range(4):
                if self._closing.is_set():
                    return 503, _bytes(self._error(identifier, 'Disposable fork proxy is closing'))
                if self._last_start is not None:
                    self._sleep(max(0, self._interval - (self._clock() - self._last_start)))
                if self._closing.is_set():
                    return 503, _bytes(self._error(identifier, 'Disposable fork proxy is closing'))
                self._last_start = self._clock()
                self._counts['upstream_attempts'] += 1
                try:
                    status, response = self._post(payload)
                    if type(status) is not int or not isinstance(response, bytes) or len(response) > MAX_RESPONSE:
                        raise ValueError('Malformed upstream response')
                    self._record('upstream_attempt', method=method, request_sha256=key,
                        attempt=attempt + 1, http_status=status, response_bytes=len(response))
                except Exception:
                    self._record('upstream_unavailable', method=method, request_sha256=key, attempt=attempt + 1)
                    return 502, _bytes(self._error(identifier, 'Public archive read unavailable'))
                if status in (429, 503) and attempt < 3:
                    self._counts['retries'] += 1
                    self._record('retry_wait', method=method, request_sha256=key, seconds=2**attempt)
                    self._sleep(2**attempt)
                    continue
                if status != 200:
                    return 503 if status in (429, 503) else 502, _bytes(self._error(identifier, 'Public archive HTTP read failed'))
                try:
                    answer = _loads(response)
                    if not isinstance(answer, dict) or answer.get('jsonrpc') != '2.0' or type(answer.get('id')) is not type(identifier) or answer['id'] != identifier or (
                            ('result' in answer) == ('error' in answer)):
                        raise ValueError('Malformed upstream envelope')
                    if 'error' in answer:
                        code = answer['error'].get('code') if isinstance(answer['error'], dict) else None
                        code = code if type(code) is int and -(2**31) <= code < 2**31 else -32000
                        self._record('upstream_rpc_error', method=method, request_sha256=key, code=code)
                        return 200, _bytes(self._error(identifier, 'Public archive rejected the read', code))
                    result = answer['result']
                    if not self._valid_result(method, result, params):
                        raise ValueError('Malformed Ethereum read result')
                    if method == 'eth_chainId' and result != '0x1237':
                        raise ValueError('Public chain identity differs')
                    if ((method == 'eth_getBlockByNumber' and params[0] == hex(self.anchor_number)) or
                            (method == 'eth_getBlockByHash' and params[0] == self.anchor_hash)):
                        if not isinstance(result, dict) or result.get('hash') != self.anchor_hash or result.get('number') != hex(self.anchor_number):
                            raise ValueError('Public anchor identity differs')
                    result_size = len(_bytes(result))
                    cached = cacheable and result is not None and result_size <= MAX_CACHE_BYTES
                    if cached:
                        while self._cache and (len(self._cache) >= MAX_CACHE_ENTRIES or self._cache_bytes + result_size > MAX_CACHE_BYTES):
                            first = next(iter(self._cache))
                            self._cache_bytes -= len(_bytes(self._cache.pop(first)))
                        self._cache[key] = result
                        self._cache_bytes += result_size
                    self._record('read_result', method=method, request_sha256=key,
                        result_sha256=_digest(result), cached=cached)
                    return 200, _bytes({'jsonrpc': '2.0', 'id': identifier, 'result': result})
                except (ValueError, TypeError, RecursionError, KeyError):
                    self._record('upstream_invalid', method=method, request_sha256=key)
                    return 502, _bytes(self._error(identifier, 'Public archive returned invalid or mismatched data'))
            raise AssertionError('Bounded retry loop exhausted')

    def verify_anchor(self):
        for identifier, method, params in ((1, 'eth_chainId', []),
                (2, 'eth_getBlockByNumber', [hex(self.anchor_number), False])):
            status, raw = self.handle(_bytes({'jsonrpc': '2.0', 'id': identifier, 'method': method, 'params': params}))
            if status != 200 or 'error' in _loads(raw):
                raise ValueError('The public chain and exact fork anchor were not witnessed')
        self._verified = True
        with self._lock:
            self._record('anchor_verified', anchor_number=self.anchor_number, anchor_hash=self.anchor_hash)

    def close(self, completed):
        self._closing.set()
        with self._lock:
            if self._finished:
                return
            self._finished = True
            summary = {'schema': 1, 'kind': 'disposable_source9_fork_cache',
                'development_only': True, 'production_approved': False, 'provider_qualified': False,
                'anchor_number': self.anchor_number, 'anchor_hash': self.anchor_hash,
                'anchor_verified': self._verified, 'context_completed': completed,
                'maximum_upstream_requests_per_second': 1 / self._interval,
                'cache_scope': 'Exact anchor or genesis numeric block; exact canonical anchor hash; chain ID. No latest/pending/errors/transaction/receipt caching.',
                'cached_entries': len(self._cache), 'cached_result_bytes': self._cache_bytes, **self._counts}
            self._record('context_closed', completed=completed)
            self._events.close()
            with (self._directory / 'summary.json').open('x', encoding='utf8') as output:
                json.dump(summary, output, indent=2, sort_keys=True)
                output.write('\n')


@contextmanager
def cached_fork_provider(public_url, anchor_number, anchor_hash, evidence_dir, requests_per_second=3):
    """Yield ``.url`` for an owned ephemeral fork; evidence_dir must be new.

    The caller must stop its owned Anvil process before leaving this context.
    No running service, existing chain, public transaction or wallet is touched.
    """
    core = _ForkCache(public_url, anchor_number, anchor_hash, evidence_dir, requests_per_second)
    server = thread = None
    completed = False
    try:
        core.verify_anchor()

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.0'

            def setup(self):
                super().setup()
                self.connection.settimeout(5)

            def log_message(self, *_args):
                pass

            def do_POST(self):
                port = self.server.server_address[1]
                lengths = self.headers.get_all('Content-Length', [])
                valid = self.path == '/' and self.headers.get_all('Host', []) == [f'127.0.0.1:{port}'] and (
                    len(lengths) == 1 and lengths[0].isdecimal() and 0 < int(lengths[0]) <= MAX_REQUEST) and (
                    self.headers.get_all('Transfer-Encoding') is None and self.headers.get_all('Expect') is None)
                if not valid:
                    status, raw = 400, _bytes(core._error(None, 'Invalid disposable fork request framing'))
                else:
                    try:
                        body = self.rfile.read(int(lengths[0]))
                        status, raw = core.handle(body) if len(body) == int(lengths[0]) else (400, _bytes(core._error(None, 'Incomplete disposable fork request')))
                    except OSError:
                        return
                try:
                    self.send_response(status)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(raw)))
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    self.wfile.write(raw)
                except OSError:
                    pass

        class Server(ThreadingHTTPServer):
            daemon_threads = False
            request_queue_size = 128

        server = Server(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .05}, daemon=True)
        thread.start()
        yield SimpleNamespace(url=f'http://127.0.0.1:{server.server_address[1]}', evidence_dir=core._directory)
        completed = True
    finally:
        core._closing.set()
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        core.close(completed)
