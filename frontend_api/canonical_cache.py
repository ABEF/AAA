"""Opt-in reuse of identical canonical reads within one bounded request.

Raw successful eth_call/eth_getCode responses and explicitly prefetched static
getter failures are memoized. Callers still
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
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.abi import keccak256


_current = ContextVar('popl_canonical_read_cache', default=None)
_HASH = re.compile(r'0x[0-9a-fA-F]{64}')
MAX_ENTRY_BYTES = 64 * 1024
# Include encoded keys and raw JSON results. A current graph's legitimate
# runtime hex can exceed 1MiB; this finite cache allowance is not provider or
# maximum-workload qualification and changes no RPC/POST/body/work budget.
MAX_RETAINED_BYTES = 8 * 1024 * 1024
_RUNTIME_DIGEST_DOMAIN = 'popl_runtime_keccak256_v1'


def _conflict():
    # An integrity contradiction must never become an isolated financial
    # availability error. Import at use time to avoid the Projection cycle.
    from frontend_api.service import ProjectionError
    raise ProjectionError('Conflicting read-only batch replies')


class _State:
    def __init__(self):
        self.replies = {}
        # A reviewed static batch may include a reverted getter. Remember that
        # outcome for this request so normal consumers cannot retry around it.
        self.failures = set()
        # Retain transports as well as their IDs; object IDs cannot be reused
        # for another transport during this scope, including nested scopes.
        self.transports = {}
        self.retained_bytes = 0
        self.active = True


def _json_size(value, maximum):
    """Screen retention before copying raw results; uncacheable is not failure."""
    if maximum < 0:
        return None
    size = 0
    try:
        for chunk in json.JSONEncoder(sort_keys=True, separators=(',', ':'),
                                      ensure_ascii=True, allow_nan=False).iterencode(value):
            size += len(chunk)  # ensure_ascii makes this exact UTF-8 byte size.
            if size > maximum:
                return None
    except (TypeError, ValueError, RecursionError):
        return None
    return size


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
        if key is None or _json_size(key, MAX_ENTRY_BYTES) is None:
            return self.inner.call(method, params)
        # The lookup must use the same captured containers as a possible miss.
        # Never bind a later captured query to an earlier caller-owned key.
        captured = deepcopy(params)
        key = _key(self.inner, method, captured)
        key_bytes = None if key is None else _json_size(key, MAX_ENTRY_BYTES)
        if key_bytes is None:
            return self.inner.call(method, captured)
        if key in state.failures:
            raise RpcError('Read-only batch getter failed')
        if key in state.replies:
            result = deepcopy(state.replies[key])
            checkpoint()
            return result
        # Both key and transport input describe the captured request, even if a
        # transport or caller later mutates its original parameter containers.
        result = self.inner.call(method, captured)
        checkpoint()
        result_bytes = _json_size(result, min(MAX_ENTRY_BYTES - key_bytes,
            MAX_RETAINED_BYTES - state.retained_bytes - key_bytes))
        checkpoint()
        if result_bytes is None:
            return result
        saved = deepcopy(result)
        returned = deepcopy(saved)
        checkpoint()
        state.transports[id(self.inner)] = self.inner
        state.replies[key] = saved
        state.retained_bytes += key_bytes + result_bytes
        return returned

    def eth_call(self, to, data, sender=None, block='latest'):
        tx = {'to': to, 'data': data}
        if sender:
            tx['from'] = sender
        return self.call('eth_call', [tx, block])

    def __getattr__(self, name):
        return getattr(self.inner, name)


def runtime_digest(projection, block, target, raw):
    """Hash actual code; reuse only after its exact canonical read is retained.

    The content-keyed metadata is request-local and carries no expected pin.
    Every caller still compares this digest to its own reviewed runtime pin.
    Metadata shares the existing entry/total byte limits and scope cleanup.
    """
    checkpoint()
    if type(raw) is not str or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', raw) is None:
        _conflict()

    def calculate():
        value = '0x'+keccak256(bytes.fromhex(raw[2:])).hex()
        checkpoint()
        return value

    state, rpc = _current.get(), projection.rpc
    if state is None or not state.active or not isinstance(rpc, _CanonicalRPC):
        return calculate()
    key = _key(rpc.inner, 'eth_getCode', [target, deepcopy(block)])
    if key is None:
        return calculate()
    if key in state.failures:
        _conflict()
    if key not in state.replies:
        return calculate()
    if state.replies[key] != raw:
        _conflict()
    if getattr(projection, 'wallet_read_batch', 0) != 1:
        return calculate()
    # RPC keys start with a transport ID (an integer). This separate string
    # domain cannot alias a provider reply, and shares identical actual code
    # across roles only after each role's own canonical read matched above.
    memo = (_RUNTIME_DIGEST_DOMAIN, raw)
    if memo in state.replies:
        value = state.replies[memo]
        if type(value) is not str or _HASH.fullmatch(value) is None:
            _conflict()
        checkpoint()
        return value
    value = calculate()
    key_bytes = _json_size(memo, MAX_ENTRY_BYTES)
    result_bytes = _json_size(value, MAX_ENTRY_BYTES)
    if (key_bytes is None or result_bytes is None or
            key_bytes+result_bytes > MAX_ENTRY_BYTES or
            state.retained_bytes+key_bytes+result_bytes > MAX_RETAINED_BYTES):
        return value
    state.replies[memo] = value
    state.retained_bytes += key_bytes+result_bytes
    checkpoint()
    return value


def prefetch(projection, block, entries):
    """Seed exact raw getter replies from the fixed reviewed static reader.

    This internal seam is not an HTTP input or an alternative trust source.
    The reader must authenticate its fixed constructor output before calling
    here. Existing target/ABI decoding remains in the ordinary Projection calls.
    A None reply means that exact getter reverted, never an uncached retry.
    All entries commit atomically within the unchanged retention bounds.
    """
    checkpoint()
    state = _current.get()
    rpc = projection.rpc
    if state is None or not state.active or not isinstance(rpc, _CanonicalRPC):
        raise RuntimeError('Read-only prefetch requires an active canonical scope')
    if not isinstance(entries, (tuple, list)) or not 1 <= len(entries) <= 256:
        raise ValueError('Invalid read-only prefetch entries')
    pending = {}
    size = 0
    for row in entries:
        checkpoint()
        if not isinstance(row, tuple) or len(row) != 3:
            raise ValueError('Invalid read-only prefetch row')
        target, data, result = row
        if (type(target) is not str or re.fullmatch(r'0x[0-9a-f]{40}', target) is None or
                target == '0x'+'0'*40 or type(data) is not str or
                re.fullmatch(r'0x[0-9a-f]{8}(?:[0-9a-f]{64}){1,2}', data) is None or
                result is not None and (type(result) is not str or
                    re.fullmatch(r'0x(?:[0-9a-f]{64}){1,2}', result) is None)):
            raise ValueError('Invalid read-only prefetch value')
        key = _key(rpc.inner, 'eth_call', [{'to': target, 'data': data}, deepcopy(block)])
        key_bytes = None if key is None else _json_size(key, MAX_ENTRY_BYTES)
        result_bytes = _json_size(result, MAX_ENTRY_BYTES)
        if key_bytes is None or result_bytes is None or key_bytes+result_bytes > MAX_ENTRY_BYTES:
            raise ValueError('Invalid read-only prefetch identity')
        if key in pending:
            if pending[key] != result:
                _conflict()
            continue
        if key in state.failures:
            if result is not None:
                _conflict()
            continue
        if key in state.replies:
            if state.replies[key] != result:
                _conflict()
            continue
        pending[key] = result
        size += key_bytes+result_bytes
        if state.retained_bytes+size > MAX_RETAINED_BYTES:
            raise WorkLimit('rpc_budget')
    checkpoint()
    for key, result in pending.items():
        if result is None:
            state.failures.add(key)
        else:
            state.replies[key] = result
    state.transports[id(rpc.inner)] = rpc.inner
    state.retained_bytes += size
    checkpoint()


def batch_rpc(projection):
    """Return the existing budgeted transport for the fixed static reader.

    Its constructor response is not retained a second time beside the decoded
    getter replies. This does not open a budget or bypass transport accounting.
    """
    checkpoint()
    state = _current.get()
    rpc = projection.rpc
    if state is None or not state.active or not isinstance(rpc, _CanonicalRPC):
        raise RuntimeError('Read-only batching requires an active canonical scope')
    if not isinstance(rpc.inner, BudgetedRPC):
        raise TypeError('Read-only batching requires an existing budgeted RPC')
    return rpc.inner


def cached(projection, block, target, data):
    """Inspect one exact same-request getter, including its remembered failure."""
    transport = batch_rpc(projection)
    state = _current.get()
    key = _key(transport, 'eth_call', [{'to': target, 'data': data}, deepcopy(block)])
    if key is None:
        raise ValueError('Invalid read-only cache lookup identity')
    if key in state.failures:
        return True, None
    if key in state.replies:
        result = deepcopy(state.replies[key])
        checkpoint()
        return True, result
    return False, None


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
            state.failures.clear()
            state.transports.clear()
            state.retained_bytes = 0
            _current.reset(token)
