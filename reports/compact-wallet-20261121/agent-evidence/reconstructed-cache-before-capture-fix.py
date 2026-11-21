"""Opt-in reuse of identical canonical reads within one bounded request.

Only raw successful eth_call/eth_getCode responses are memoized. Callers still
decode and authenticate each response, and all head/chain/header/final checks
remain live. The proxy sits outside an existing BudgetedRPC: a miss retains its
ordinary call/POST charges, while a hit checks the same request's deadline and
snapshot expiry without starting another RPC. No result survives scope exit.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import json
import re

from zzz_ops.work_budget import BudgetedRPC, checkpoint


_current = ContextVar('popl_canonical_read_cache', default=None)
_HASH = re.compile(r'0x[0-9a-fA-F]{64}')


class _State:
    def __init__(self):
        self.replies = {}
        # Retain transports as well as their IDs; object IDs cannot be reused
        # for another transport during this scope, including nested scopes.
        self.transports = {}
        self.active = True


def _key(transport, method, params):
    if method not in ('eth_call', 'eth_getCode') or type(params) is not list or len(params) != 2:
        return None
    block = params[1]
    if (type(block) is not dict or set(block) != {'blockHash', 'requireCanonical'} or
            block['requireCanonical'] is not True or type(block['blockHash']) is not str or
            _HASH.fullmatch(block['blockHash']) is None):
        return None
    try:
        # Preserve the complete wire input, including sender/gas/value and any
        # other transaction field. Sorting only object keys is JSON-equivalent.
        encoded = json.dumps(params, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        return None
    return id(transport), method, encoded


class _CanonicalRPC:
    def __init__(self, rpc):
        self.inner = rpc

    def call(self, method, params=None):
        state = _current.get()
        if state is None or not state.active:
            return self.inner.call(method, params)
        checkpoint()
        key = _key(self.inner, method, params)
        if key is None:
            return self.inner.call(method, params)
        if key in state.replies:
            result = deepcopy(state.replies[key])
            checkpoint()
            return result
        # Both key and transport input describe the captured request, even if a
        # transport or caller later mutates its original parameter containers.
        captured = deepcopy(params)
        result = self.inner.call(method, captured)
        checkpoint()
        saved = deepcopy(result)
        returned = deepcopy(saved)
        checkpoint()
        state.transports[id(self.inner)] = self.inner
        state.replies[key] = saved
        return returned

    def eth_call(self, to, data, sender=None, block='latest'):
        tx = {'to': to, 'data': data}
        if sender:
            tx['from'] = sender
        return self.call('eth_call', [tx, block])

    def __getattr__(self, name):
        return getattr(self.inner, name)


def _projections(projections):
    pending = [projections] if hasattr(projections, 'rpc') else list(projections)
    seen = set()
    result = []
    while pending:
        projection = pending.pop()
        if id(projection) in seen:
            continue
        seen.add(id(projection))
        rpc = projection.rpc
        if not isinstance(rpc, (BudgetedRPC, _CanonicalRPC)):
            raise TypeError('Canonical reuse requires an existing budgeted RPC')
        result.append(projection)
        lineage = getattr(projection, 'lineage', None)
        if lineage is not None:
            pending.extend(entry.projection for entry in lineage.entries)
    return result


@contextmanager
def scope(projections):
    """Temporarily wrap projections and their configured lineage peers.

    Accept one Projection or an iterable of projections. Enter inside the
    existing request_scope/bounded_request; this helper never opens a budget.
    Nested scopes share raw replies and the existing budget. Projection/RPC
    construction precedes this scope, as in the isolated API worker. Original
    RPC objects are restored on success, refusal, expiry or any other failure.
    """
    if checkpoint() is None:
        raise RuntimeError('Canonical reuse requires an active request budget')
    selected = _projections(projections)
    state = _current.get()
    token = None
    if state is None or not state.active:
        state = _State()
        token = _current.set(state)
    restored = []
    proxies = {}
    try:
        for projection in selected:
            original = projection.rpc
            if isinstance(original, _CanonicalRPC):
                continue
            proxy = proxies.get(id(original))
            if proxy is None:
                proxy = proxies[id(original)] = _CanonicalRPC(original)
            projection.rpc = proxy
            restored.append((projection, original, proxy))
        checkpoint()
        yield
        checkpoint()
    finally:
        for projection, original, proxy in reversed(restored):
            # Do not overwrite an explicit intervening owner change.
            if projection.rpc is proxy:
                projection.rpc = original
        if token is not None:
            state.active = False
            state.replies.clear()
            state.transports.clear()
            _current.reset(token)
