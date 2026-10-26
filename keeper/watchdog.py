"""Optional main-process systemd progress notifications, never a timer thread.

Socket timeouts are not total DNS/header/body deadlines. A supervised keeper
must stop notifying while blocked so systemd can kill its whole service group.
Without the reviewed unit/manager, this helper is not a hard I/O deadline.
"""
from __future__ import annotations

import math
import os
import re
import socket
import time


class WatchdogError(RuntimeError):
    """Fixed sanitized operational error; no environment/socket value is exposed."""


def _number(value, maximum):
    if not isinstance(value, str) or re.fullmatch(r'[1-9][0-9]{0,19}', value) is None:
        raise ValueError()
    result = int(value)
    if result > maximum:
        raise ValueError()
    return result


class ProgressWatchdog:
    def __init__(self, address=None, seconds=None, *, owner=None, clock=None):
        self.address = address
        self.seconds = seconds
        self.owner = owner
        self.clock = clock or time.monotonic
        self.last = None
        # Default120s supervision must accommodate a legitimate90s cast call.
        # A60s notification cadence could leave too little margin before that
        # call, so progress is reported at most10s apart when work completes.
        self.cadence = min(10.0, seconds / 3) if seconds is not None else None

    @property
    def enabled(self):
        return self.address is not None

    @classmethod
    def from_environment(cls, environment=None, *, clock=None, pid=None):
        # Consume only during main startup, like sd_watchdog_enabled(unset=1).
        # Signer subprocesses must not inherit notification credentials. Explicit
        # injected dictionaries are not mutated; they are inert test inputs.
        env = dict(os.environ if environment is None else environment)
        if environment is None:
            for name in ('WATCHDOG_USEC', 'WATCHDOG_PID', 'NOTIFY_SOCKET'):
                os.environ.pop(name, None)
        if 'WATCHDOG_USEC' not in env:
            return cls(clock=clock)
        try:
            owner = os.getpid() if pid is None else pid
            if type(owner) is not int or owner <= 0:
                raise ValueError()
            # A valid different PID is intended for an ancestor, not this process.
            if 'WATCHDOG_PID' in env and _number(env['WATCHDOG_PID'], 2**31 - 1) != owner:
                return cls(clock=clock)
            usec = _number(env['WATCHDOG_USEC'], 2**64 - 1)
            target = env.get('NOTIFY_SOCKET')
            if (not isinstance(target, str) or len(target) < 2 or
                    target[0] not in ('/', '@') or any(c in target for c in '\0\r\n')):
                raise ValueError()
            encoded = os.fsencode(target)
            # Leave room for the terminating NUL of a filesystem sockaddr_un;
            # Linux abstract addresses use the leading NUL in place of '@'.
            if len(encoded) > 107 or not hasattr(socket, 'AF_UNIX'):
                raise ValueError()
            address = b'\0' + encoded[1:] if target[0] == '@' else encoded
            return cls(address, usec / 1_000_000, owner=owner, clock=clock)
        except (TypeError, ValueError, OSError):
            raise WatchdogError('Invalid systemd watchdog configuration') from None

    def pulse(self, *, force=False):
        if not self.enabled:
            return False
        if os.getpid() != self.owner:
            raise WatchdogError('Systemd watchdog process identity changed')
        now = self.clock()
        if (type(now) not in (int, float) or not math.isfinite(now) or
                self.last is not None and (now < self.last or now - self.last >= self.seconds)):
            # A late return must not revive progress after the expected watchdog
            # deadline. Supervision/pending recovery must resolve that outage.
            raise WatchdogError('Systemd watchdog progress deadline exceeded')
        if self.last is not None and not force and now - self.last < self.cadence:
            return False
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as channel:
                channel.setblocking(False)
                if channel.sendto(b'WATCHDOG=1', self.address) != len(b'WATCHDOG=1'):
                    raise OSError()
        except (OSError, ValueError, AttributeError):
            raise WatchdogError('Systemd watchdog notification unavailable') from None
        self.last = now
        return True


class ProgressRPC:
    """Transparent read transport wrapper; only completed calls report progress.

    No thread, resend, new RPC, state mutation or notification during a blocked
    call exists. Bounded error returns are progress too; health still reports the
    failure. A stuck read cannot keep the systemd watchdog alive.
    """
    def __init__(self, inner, watchdog):
        self.inner = inner
        self.watchdog = watchdog

    def call(self, method, params=None):
        try:
            return self.inner.call(method, params)
        finally:
            self.watchdog.pulse()

    def eth_call(self, to, data, sender=None, block='latest'):
        # Keep Rpc.eth_call's exact request shape but route through OUR call.
        # Delegating a bound inner.eth_call would bypass progress on Keeper.view.
        transaction = {'to': to, 'data': data}
        if sender:
            transaction['from'] = sender
        return self.call('eth_call', [transaction, block])

    def __getattr__(self, name):
        return getattr(self.inner, name)
