"""Loopback-only reads and opt-in unsigned transaction preparation."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
from typing import Any

from frontend_api.service import Projection, UnknownNFT, token_id
from zzz_ops.abi import address
from zzz_ops.rpc import RpcError

MAX_PREPARATION_BODY = 16 * 1024
MAX_PREPARATION_DEPTH = 16


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _reject_constant(_):
    raise ValueError('Nonfinite JSON number')


def _bounded_depth(payload):
    pending = [(payload, 1)]
    while pending:
        item, depth = pending.pop()
        if depth > MAX_PREPARATION_DEPTH:
            raise ValueError('JSON nesting exceeds request bound')
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        pending.extend((child, depth + 1) for child in children if isinstance(child, (dict, list)))


def handler(projection: Projection, preparer=None) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'
        server_version = 'PoPLReadAPI/1'
        sys_version = ''

        def _json(self, status: int, value: dict[str, Any]) -> None:
            body = (json.dumps(value, separators=(',', ':'), ensure_ascii=True) + '\n').encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            port = self.server.server_address[1]
            if self.headers.get('Host') not in (f'127.0.0.1:{port}', f'localhost:{port}'):
                self._json(400, {'error': 'invalid_host'})
                return
            if self.headers.get('Content-Length') not in (None, '0') or self.headers.get('Transfer-Encoding'):
                self._json(400, {'error': 'request_body_not_allowed'})
                return
            match = re.fullmatch(r'/v1/nfts/(0|[1-9][0-9]{0,77})', self.path)
            wallet = re.fullmatch(r'/v1/wallets/(0x[0-9a-fA-F]{40})/nfts', self.path)
            protocol = self.path == '/v1/protocol'
            readiness = self.path == '/v1/mint-readiness'
            earned = re.fullmatch(r'/v1/nfts/(0|[1-9][0-9]{0,77})/earnings', self.path)
            collection_earnings = self.path == '/v1/earnings'
            if not match and not wallet and not protocol and not readiness and not earned and not collection_earnings:
                self._json(404, {'error': 'unknown_endpoint'})
                return
            try:
                identifier = token_id((match or earned)[1]) if match or earned else address(wallet[1]) if wallet else None
            except ValueError:
                self._json(400, {'error': 'invalid_token_id' if match or earned else 'invalid_wallet_address'})
                return
            try:
                result = projection.earnings(identifier) if earned or collection_earnings else projection.mint_readiness() if readiness else projection.protocol() if protocol else projection.nft(identifier) if match else projection.wallet(identifier)
            except UnknownNFT:
                self._json(404, {'error': 'nft_not_minted'})
            except (RpcError, ValueError, KeyError, TypeError, OverflowError):
                # Never disclose upstream errors, configured endpoints or keys.
                self._json(503, {'error': 'confirmed_projection_unavailable'})
            else:
                self._json(200, result)

        def do_POST(self) -> None:
            # The default service remains GET-only. Enabling this adapter only
            # prepares unsigned calls; it never enables signing or broadcast.
            if preparer is None:
                self._method_not_allowed()
                return
            port = self.server.server_address[1]
            hosts = self.headers.get_all('Host', [])
            if len(hosts) != 1 or hosts[0] not in (f'127.0.0.1:{port}', f'localhost:{port}'):
                self._json(400, {'error': 'invalid_host'})
                return
            if self.path != '/v1/transactions/prepare':
                self._json(404, {'error': 'unknown_endpoint'})
                return
            if self.headers.get_all('Transfer-Encoding') is not None or self.headers.get_all('Expect') is not None:
                self._json(400, {'error': 'unsupported_request_framing'})
                return
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or re.fullmatch(r'0|[1-9][0-9]{0,4}', lengths[0]) is None:
                self._json(400, {'error': 'invalid_content_length'})
                return
            length = int(lengths[0])
            if length > MAX_PREPARATION_BODY:
                self._json(413, {'error': 'request_body_too_large'})
                return
            types = self.headers.get_all('Content-Type', [])
            if len(types) != 1 or types[0].lower() not in ('application/json', 'application/json; charset=utf-8'):
                self._json(415, {'error': 'application_json_required'})
                return
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError('Incomplete request body')
                payload = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                                     parse_constant=_reject_constant)
                if not isinstance(payload, dict):
                    raise ValueError('Expected a JSON object')
                _bounded_depth(payload)
            except (OSError, ValueError, RecursionError):
                self._json(400, {'error': 'invalid_json_body'})
                return
            from frontend_api.transactions import TransactionInputError
            try:
                result = preparer.prepare(payload)
            except TransactionInputError:
                self._json(400, {'error': 'invalid_transaction_request'})
            except UnknownNFT:
                self._json(404, {'error': 'nft_not_minted'})
            except Exception:
                # Include unexpected service failures in the same fail-closed
                # boundary. Never echo bodies, RPC errors or exception text.
                self._json(503, {'error': 'transaction_preparation_unavailable'})
            else:
                self._json(200, result)

        def _method_not_allowed(self) -> None:
            self._json(405, {'error': 'read_only_get_required'})

        do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = _method_not_allowed

        def log_message(self, format: str, *args: Any) -> None:
            # Paths and query text are untrusted and are not logged. Operators
            # can use the reverse proxy's bounded structured status/access log.
            pass

    return Handler


class ReadServer(HTTPServer):
    """Serial handler bounds concurrent upstream work; proxy must rate-limit."""
    request_queue_size = 8

    def get_request(self):
        connection, peer = super().get_request()
        connection.settimeout(5)
        return connection, peer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--transaction-config',
                        help='Reviewed fee policy for opt-in unsigned mint/claim preparation; no signing')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('port must be between 1024 and 65535')
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    from frontend_api.worker import WorkerClient
    transaction_config = json.loads(Path(args.transaction_config).read_text(encoding='utf-8')) if args.transaction_config else None
    projection = WorkerClient(config, transaction_config=transaction_config)
    preparer = None
    if transaction_config is not None:
        preparer = projection
    with ReadServer(('127.0.0.1', args.port), handler(projection, preparer)) as server:
        print(json.dumps({'event': 'frontend_read_api_started', 'port': args.port,
                          'chain_id': projection.chain, 'transaction_preparation_enabled': preparer is not None}), flush=True)
        try:
            server.serve_forever(poll_interval=.5)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
