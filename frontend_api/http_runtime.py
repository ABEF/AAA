"""Bounded loopback HTTP admission; no signing, identity or result caching."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
from socketserver import ThreadingMixIn
import threading
import time

from zzz_ops.errors import RpcError
from frontend_api.admission import AdmissionRejected, client_key, public_origin

INGRESS_SECONDS = 5
CONNECTION_SECONDS = 45  # Includes ingress, 30s worker budget, cleanup and output.
HEADER_BYTES = 32 * 1024
LINE_BYTES = 8 * 1024


class ServiceBusy(RpcError):
    """Admission failed before starting any upstream work."""


class HeaderLimit(ValueError):
    pass


class HeaderReader:
    def __init__(self, stream):
        self.stream = stream
        self.remaining = HEADER_BYTES

    def readline(self, limit=-1):
        maximum = min(LINE_BYTES, self.remaining)
        data = self.stream.readline(min(limit, maximum + 1) if limit >= 0 else maximum + 1)
        if len(data) > maximum:
            raise HeaderLimit()
        self.remaining -= len(data)
        return data

    def __getattr__(self, name):
        return getattr(self.stream, name)


class BoundedHandler(BaseHTTPRequestHandler):
    """Absolute ingress deadline also defeats slow, continuously trickled bodies."""

    def setup(self):
        super().setup()
        self._admission_release = None
        self.rfile = HeaderReader(self.rfile)
        self._expired = threading.Event()
        self._ingress_end = time.monotonic() + INGRESS_SECONDS
        self._ingress = threading.Timer(INGRESS_SECONDS, self._expire)
        self._deadline = threading.Timer(CONNECTION_SECONDS, self._expire)
        self._ingress.daemon = self._deadline.daemon = True
        self._ingress.start()
        self._deadline.start()

    def _expire(self):
        self._expired.set()
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def begin_work(self):
        # Called only after complete framing/body validation, immediately before
        # bounded service dispatch. The overall connection deadline still holds.
        self._ingress.cancel()
        if self._expired.is_set() or time.monotonic() >= self._ingress_end:
            raise TimeoutError('Request ingress deadline exceeded')
        admission = getattr(self.server, 'admission', None)
        if admission is not None:
            if self._admission_release is not None:
                raise RuntimeError('Request work already admitted')
            key = client_key(self, self.server.proxy_origin)
            self._admission_release = admission.acquire(key, preparation=self.command == 'POST')

    def admission_rejected(self, error):
        self._retry_after = error.retry_after
        self._json(error.status, {'error': error.code})
        # Fixed labels only: no IP, path, body, wallet, upstream or exception.
        print(json.dumps({'event': 'api_admission_rejected', 'status': error.status,
                          'reason': error.code}), flush=True)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except HeaderLimit:
            self.close_connection = True
            # Request parsing may not yet have initialized these attributes.
            self.request_version = 'HTTP/1.0'
            self.requestline = ''
            self.command = ''
            try:
                self._json(431, {'error': 'request_headers_too_large'})
            except OSError:
                pass
        except (OSError, TimeoutError):
            self.close_connection = True

    def finish(self):
        self._ingress.cancel()
        self._deadline.cancel()
        try:
            super().finish()
        except OSError:
            pass
        finally:
            release = getattr(self, '_admission_release', None)
            if release is not None:
                release()


class BoundedHTTPServer(ThreadingMixIn, HTTPServer):
    # No per-request unbounded thread queue. Active HTTP connections and expensive
    # child workers have independent caps, including partial/invalid requests.
    daemon_threads = False
    block_on_close = True
    request_queue_size = 16

    def __init__(self, *args, max_connections=8, admission=None, proxy_origin=None, **kwargs):
        if type(max_connections) is not int or not 1 <= max_connections <= 32:
            raise ValueError('max_connections must be between 1 and 32')
        self._connections = threading.BoundedSemaphore(max_connections)
        self.proxy_origin = public_origin(proxy_origin)
        if self.proxy_origin is not None and admission is None:
            raise ValueError('proxy mode requires client admission')
        self.admission = admission
        super().__init__(*args, **kwargs)

    def get_request(self):
        connection, peer = super().get_request()
        connection.settimeout(INGRESS_SECONDS)
        return connection, peer

    def process_request(self, request, client_address):
        if not self._connections.acquire(blocking=False):
            body = b'{"error":"service_busy"}\n'
            try:
                # The accept thread must not block behind a non-reading client.
                request.settimeout(.05)
                request.sendall(b'HTTP/1.0 503 Service Unavailable\r\nContent-Type: application/json\r\n'
                                b'Cache-Control: no-store\r\nRetry-After: 1\r\nConnection: close\r\n'
                                + f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
            except OSError:
                pass
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._connections.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._connections.release()

    def handle_error(self, request, client_address):
        # No exception strings, paths, wallet addresses, endpoints or peer data.
        print(json.dumps({'event': 'api_http_failure', 'outcome': 'internal_error'}), flush=True)
