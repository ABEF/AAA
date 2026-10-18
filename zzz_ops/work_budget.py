"""Request-local read budgets; no signer, global alarm or background worker."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import time
from zzz_ops.errors import WorkLimit


class Budget:
    def __init__(self, seconds=25, calls=1024, posts=2048, *, clock=None):
        if type(seconds) not in (int, float) or not 0 < seconds <= 60:
            raise ValueError('Request duration must be positive and at most 60 seconds')
        if any(type(n) is not int or not 1 <= n <= 4096 for n in (calls, posts)):
            raise ValueError('Request RPC bounds must be 1..4096')
        self.clock = clock or time.monotonic
        self.deadline = self.clock() + seconds
        self.calls, self.posts = calls, posts
        self.expiries = []

    def check(self):
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise WorkLimit('deadline')
        if any(clock() >= expiry for expiry, clock in self.expiries):
            raise WorkLimit('snapshot_expired')
        return remaining

    def consume(self, kind):
        self.check()
        value = getattr(self, kind)
        if value <= 0:
            raise WorkLimit('rpc_budget')
        setattr(self, kind, value - 1)

    def expire_at(self, expiry, wall_clock):
        # Both clocks are enforced: a backward wall jump cannot extend work;
        # a forward jump must invalidate a draft before another RPC is started.
        remaining = expiry - wall_clock()
        if remaining <= 0:
            raise WorkLimit('snapshot_expired')
        self.deadline = min(self.deadline, self.clock() + remaining)
        if len(self.expiries) >= 32:
            raise WorkLimit('rpc_budget')
        self.expiries.append((expiry, wall_clock))
        self.check()


_current = ContextVar('popl_request_budget', default=None)


def checkpoint():
    budget = _current.get()
    return budget.check() if budget else None


def consume(kind):
    budget = _current.get()
    if budget:
        budget.consume(kind)


def expire_at(expiry, clock):
    budget = _current.get()
    if budget:
        budget.expire_at(expiry, clock)


def timeout(maximum):
    remaining = checkpoint()
    return maximum if remaining is None else min(maximum, remaining)


@contextmanager
def request_scope(budget=None):
    # Nested projections/predecessors share one budget; they cannot reset it.
    current = _current.get()
    token = _current.set(budget or Budget()) if current is None else None
    try:
        checkpoint()
        yield _current.get()
        checkpoint()
    finally:
        if token is not None:
            _current.reset(token)


def bounded_request(function):
    @wraps(function)
    def bounded(*args, **kwargs):
        with request_scope():
            return function(*args, **kwargs)
    return bounded


class BudgetedRPC:
    """Includes injected transports in checks and shares predecessor budgets."""
    def __init__(self, rpc):
        self.inner = rpc

    def call(self, method, params=None):
        consume('calls')
        result = self.inner.call(method, params)
        checkpoint()
        return result

    def __getattr__(self, name):
        return getattr(self.inner, name)
