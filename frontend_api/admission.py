"""Bounded per-client admission for read/unsigned-preparation services.

Client addresses are capacity keys, never authentication or wallet identities.
No background timer, request queue, signer or persistent personal data.
"""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import math
import re
import threading
import time
from urllib.parse import urlsplit


class AdmissionRejected(Exception):
    def __init__(self, status, code, retry_after=None):
        self.status, self.code, self.retry_after = status, code, retry_after
        super().__init__(code)


def public_origin(value):
    """One explicit HTTPS origin, not a URL/path, wildcard or trusted network."""
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'https://[a-z0-9.-]+(?::[0-9]{1,5})?', value):
        raise ValueError('proxy origin must be an exact lower-case HTTPS origin')
    parsed = urlsplit(value)
    labels = parsed.hostname.split('.')
    if len(parsed.hostname) > 253 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in labels):
        raise ValueError('invalid origin hostname')
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError('invalid origin port')
    return value


def client_key(request, proxy_origin):
    peer = ip_address(request.client_address[0])
    headers = request.headers.get_all('X-PoPL-Client-IP', [])
    if proxy_origin is None:
        if headers:
            raise AdmissionRejected(400, 'unexpected_proxy_identity')
        identity = peer
    else:
        # The CLI only binds 127.0.0.1. Even a custom embedding must not trust
        # this header over an arbitrary network or from a remote peer.
        if str(peer) != '127.0.0.1' or len(headers) != 1:
            raise AdmissionRejected(400, 'invalid_proxy_identity')
        raw = headers[0]
        if len(raw) > 45 or raw != raw.strip() or '%' in raw:
            raise AdmissionRejected(400, 'invalid_proxy_identity')
        try:
            identity = ip_address(raw)
        except ValueError:
            raise AdmissionRejected(400, 'invalid_proxy_identity') from None
        origins = request.headers.get_all('Origin', [])
        if origins not in ([], [proxy_origin]) or (request.command == 'POST' and origins != [proxy_origin]):
            raise AdmissionRejected(403, 'origin_not_allowed')
        fetch = request.headers.get_all('Sec-Fetch-Site', [])
        if fetch not in ([], ['same-origin'], ['none']):
            raise AdmissionRejected(403, 'origin_not_allowed')
    # Equivalent IPv4/mapped-IPv6 spellings share capacity. Forwarded/XFF and
    # wallet addresses never participate in the key.
    return str(getattr(identity, 'ipv4_mapped', None) or identity)


@dataclass
class _Client:
    last: float
    reads: float = 12.0
    prepares: float = 2.0
    active: int = 0


class ClientAdmission:
    """Per process: 2 active; reads 1/s burst12, preparations 6/min burst2."""

    def __init__(self, *, max_active=2, capacity=4096, clock=time.monotonic):
        if type(max_active) is not int or not 1 <= max_active <= 4:
            raise ValueError('per-client active limit must be between 1 and 4')
        if type(capacity) is not int or not 1 <= capacity <= 16384:
            raise ValueError('client capacity must be between 1 and 16384')
        self.max_active, self.capacity, self.clock = max_active, capacity, clock
        self._clients = {}
        self._lock = threading.Lock()

    def acquire(self, key, *, preparation=False):
        with self._lock:
            now = self.clock()
            row = self._clients.get(key)
            if row is None:
                if len(self._clients) >= self.capacity:
                    # Only forget fully replenished, idle clients. Evicting a
                    # depleted/active entry would reset its budget or lease.
                    self._clients = {k: r for k, r in self._clients.items()
                                     if r.active or now - r.last < 20}
                if len(self._clients) >= self.capacity:
                    raise AdmissionRejected(503, 'admission_capacity_unavailable', 1)
                row = self._clients[key] = _Client(now)
            elapsed = max(0, now - row.last)
            row.reads = min(12., row.reads + elapsed)
            row.prepares = min(2., row.prepares + elapsed * .1)
            row.last = now
            if row.active >= self.max_active:
                raise AdmissionRejected(429, 'client_busy', 1)
            field, rate = ('prepares', .1) if preparation else ('reads', 1.)
            tokens = getattr(row, field)
            if tokens < 1:
                raise AdmissionRejected(429, 'client_rate_limited', max(1, math.ceil((1 - tokens) / rate)))
            setattr(row, field, tokens - 1)
            row.active += 1
        released = False

        def release():
            nonlocal released
            with self._lock:
                if not released:
                    row.active -= 1
                    released = True
        return release


def add_arguments(parser):
    parser.add_argument('--per-client-active', type=int, default=2, choices=range(1, 5),
                        help='Maximum simultaneous work requests per client IP (1-4)')
    parser.add_argument('--proxy-origin', type=public_origin,
                        help='Opt in to a reviewed local proxy and exact HTTPS website origin')
