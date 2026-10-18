"""Loopback-only HTTP adapter for the deployment-pinned read projection."""
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


def handler(projection: Projection) -> type[BaseHTTPRequestHandler]:
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
            if not match and not wallet and not protocol:
                self._json(404, {'error': 'unknown_endpoint'})
                return
            try:
                identifier = token_id(match[1]) if match else address(wallet[1]) if wallet else None
            except ValueError:
                self._json(400, {'error': 'invalid_token_id' if match else 'invalid_wallet_address'})
                return
            try:
                result = projection.protocol() if protocol else projection.nft(identifier) if match else projection.wallet(identifier)
            except UnknownNFT:
                self._json(404, {'error': 'nft_not_minted'})
            except (RpcError, ValueError, KeyError, TypeError, OverflowError):
                # Never disclose upstream errors, configured endpoints or keys.
                self._json(503, {'error': 'confirmed_projection_unavailable'})
            else:
                self._json(200, result)

        def _method_not_allowed(self) -> None:
            self._json(405, {'error': 'read_only_get_required'})

        do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = _method_not_allowed

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
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('port must be between 1024 and 65535')
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    projection = Projection(config)
    with ReadServer(('127.0.0.1', args.port), handler(projection)) as server:
        print(json.dumps({'event': 'frontend_read_api_started', 'port': args.port,
                          'chain_id': projection.chain}), flush=True)
        try:
            server.serve_forever(poll_interval=.5)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
