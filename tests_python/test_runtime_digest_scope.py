"""NEW bounded runtime-digest witnesses; no EVM, provider or old test body.

Actual Projection._code and the keeper's own expected-pin comparison execute.
Only synthetic code transport and explicitly controlled test clocks are used.
"""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from frontend_api import canonical_cache as cache
from frontend_api.service import Projection, ProjectionError
from keeper import compound_policy
from zzz_ops.abi import keccak256
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import Budget, BudgetedRPC, checkpoint, consume, request_scope

DOMAIN = 'popl_runtime_keccak256_v1'
BLOCK = {'blockHash': '0x'+'ab'*32, 'requireCanonical': True}
CODE = '0x6000'


def addr(n):
    return '0x'+f'{n:040x}'


def hashed(raw):
    return '0x'+keccak256(bytes.fromhex(raw[2:])).hex()


def size(value):
    return len(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode())


class CodeWire:
    def __init__(self, code=CODE):
        self.default = code
        self.codes = {}
        self.calls = []

    def call(self, method, params=None):
        consume('posts')
        if method != 'eth_getCode':
            raise AssertionError('No hidden provider read is allowed')
        self.calls.append((method, deepcopy(params)))
        return self.codes.get(params[0], self.default)


def projection(wire=None, flag=1):
    wire = wire or CodeWire()
    p = Projection.__new__(Projection)
    p.rpc = BudgetedRPC(wire)
    p.wallet_read_batch = flag
    p.lineage = None
    return p, wire


class RuntimeDigestScopeTests(unittest.TestCase):
    def test_both_consumers_reject_wrong_pins_after_hits_and_exact_raw_aliases(self):
        p, wire = projection()
        original = p.rpc
        expected = hashed(CODE)
        wrong = '0x'+'ff'*32
        contracts = {role: addr(i+1) for i, role in enumerate(
            ('access','vault','strategy','pools','liquidity','pool_manager','state_view',
             'portfolio_policy','rebalance_confirmation','lp_position_executor','balancing_router','lp_balance_math'))}
        access = contracts['access']
        state = None
        with patch.object(cache, 'keccak256', wraps=keccak256) as hashing:
            with request_scope(), cache.scope(p):
                state = cache._current.get()
                p._code(access, expected, BLOCK)
                p._code(access, expected, BLOCK)
                self.assertEqual((len(wire.calls), hashing.call_count), (1, 1))
                with self.assertRaisesRegex(ProjectionError, 'Runtime code differs'):
                    p._code(access, wrong, BLOCK)
                self.assertEqual(hashing.call_count, 1)
                pins = {role: expected for role in contracts}
                pins['access'] = wrong

                def unread(*args, **kwargs):
                    raise AssertionError('Wrong first runtime pin must stop before state reads')

                code = lambda target: p.rpc.call('eth_getCode', [target, BLOCK])
                shared = lambda target, raw: cache.runtime_digest(p, BLOCK, target, raw)
                for callback in (shared, None):
                    with self.assertRaisesRegex(ValueError, 'Compound policy runtime differs'):
                        compound_policy.observe(unread, code, contracts=contracts, code_hashes=pins,
                            bucket=1, accounting_version=7, physical_only=True, code_digest=callback)
                self.assertEqual((len(wire.calls), hashing.call_count), (1, 1))
                # Identical content may share a digest only after each address,
                # canonical block and transport has its own retained code reply.
                p._code(addr(20), expected, BLOCK)
                self.assertEqual((len(wire.calls), hashing.call_count), (2, 1))
                retained = state.retained_bytes
                self.assertEqual(cache.runtime_digest(p, BLOCK, addr(21), CODE), expected)
                self.assertEqual((state.retained_bytes, hashing.call_count), (retained, 2))
                p._code(addr(21), expected, BLOCK)
                changed = {'blockHash': '0x'+'cd'*32, 'requireCanonical': True}
                p._code(access, expected, changed)
                self.assertEqual((len(wire.calls), hashing.call_count), (4, 2))
                p._code(access, expected, 'latest')
                self.assertEqual((len(wire.calls), hashing.call_count), (5, 3))
                other, other_wire = projection()
                with cache.scope(other):
                    retained = state.retained_bytes
                    self.assertEqual(cache.runtime_digest(other, BLOCK, access, CODE), expected)
                    self.assertEqual((len(other_wire.calls), hashing.call_count), (0, 4))
                    self.assertEqual(state.retained_bytes, retained)
                    other._code(access, expected, BLOCK)
                    self.assertEqual((len(other_wire.calls), hashing.call_count), (1, 4))
                with self.assertRaisesRegex(ProjectionError, 'Conflicting read-only batch replies'):
                    cache.runtime_digest(p, BLOCK, access, '0x6001')
                self.assertEqual(hashing.call_count, 4)
        self.assertIs(p.rpc, original)
        self.assertIsNone(cache._current.get())
        self.assertIsNone(checkpoint())
        self.assertFalse(state.active)
        self.assertEqual((state.replies, state.retained_bytes), ({}, 0))

    def test_metadata_charges_original_bounds_falls_back_and_expires_without_leaks(self):
        p, wire = projection()
        expected = hashed(CODE)
        with request_scope(), cache.scope(p):
            raw = p.rpc.call('eth_getCode', [addr(1), BLOCK])
            state = cache._current.get()
            before = state.retained_bytes
            self.assertEqual(cache.runtime_digest(p, BLOCK, addr(1), raw), expected)
            charge = size((DOMAIN, raw))+size(expected)
            self.assertEqual(state.retained_bytes-before, charge)
            self.assertLessEqual(charge, 65536)
            self.assertEqual(state.replies[(DOMAIN, CODE)], expected)
            before = state.retained_bytes
            cache.runtime_digest(p, BLOCK, addr(1), raw)
            self.assertEqual(state.retained_bytes, before)
        self.assertEqual(state.replies, {})
        # Disabled/inactive requests compute correctly without digest retention.
        off, _ = projection(flag=0)
        with request_scope(), cache.scope(off), patch.object(cache, 'keccak256', wraps=keccak256) as hashing:
            raw = off.rpc.call('eth_getCode', [addr(1), BLOCK])
            before = cache._current.get().retained_bytes
            for _ in range(2):
                self.assertEqual(cache.runtime_digest(off, BLOCK, addr(1), raw), expected)
            self.assertEqual(hashing.call_count, 2)
            self.assertEqual(cache._current.get().retained_bytes, before)
            with self.assertRaises(ProjectionError):
                cache.runtime_digest(off, BLOCK, addr(1), '0x6001')
        with request_scope(), patch.object(cache, 'keccak256', wraps=keccak256) as hashing:
            self.assertEqual(cache.runtime_digest(p, BLOCK, addr(1), CODE), expected)
            self.assertEqual(cache.runtime_digest(p, BLOCK, addr(1), CODE), expected)
            self.assertEqual(hashing.call_count, 2)
            self.assertIsNone(cache._current.get())
        # A code reply too large for the existing entry limit is not retained.
        oversized = '0x'+'60'*(65536//2)
        over, _ = projection(CodeWire(oversized))
        with request_scope(), cache.scope(over):
            raw = over.rpc.call('eth_getCode', [addr(1), BLOCK])
            self.assertEqual(cache._current.get().replies, {})
            self.assertEqual(cache.runtime_digest(over, BLOCK, addr(1), raw), hashed(raw))
            self.assertEqual(cache._current.get().retained_bytes, 0)
        # Fill the actual unchanged8MiB raw cache, without modifying its caps.
        large = '0x'+'60'*32500
        full, full_wire = projection(CodeWire(large))
        with request_scope(), cache.scope(full):
            state = cache._current.get()
            for identifier in range(1, 161):
                full.rpc.call('eth_getCode', [addr(identifier), BLOCK])
            large_charge = size((DOMAIN, large))+size(hashed(large))
            for identifier in range(1000, 1010):
                if 8*1048576-state.retained_bytes < large_charge:
                    break
                full_wire.codes[addr(identifier)] = CODE
                before = state.retained_bytes
                full.rpc.call('eth_getCode', [addr(identifier), BLOCK])
                self.assertGreater(state.retained_bytes, before)
            self.assertLess(8*1048576-state.retained_bytes, large_charge)
            before = state.retained_bytes
            with patch.object(cache, 'keccak256', wraps=keccak256) as hashing:
                value = cache.runtime_digest(full, BLOCK, addr(1), large)
                self.assertEqual(cache.runtime_digest(full, BLOCK, addr(1), large), value)
                self.assertEqual(hashing.call_count, 2)
            self.assertNotIn((DOMAIN, large), state.replies)
            self.assertEqual(state.retained_bytes, before)
            self.assertLessEqual(before, 8*1048576)
        self.assertEqual((state.replies, state.retained_bytes), ({}, 0))
        # Even a digest hit remains subject to the current request's deadline.
        now = [0.0]
        expiring, _ = projection()
        budget = Budget(seconds=25, calls=1024, posts=2048, clock=lambda: now[0])
        with self.assertRaisesRegex(WorkLimit, 'deadline'):
            with request_scope(budget), cache.scope(expiring):
                raw = expiring.rpc.call('eth_getCode', [addr(1), BLOCK])
                cache.runtime_digest(expiring, BLOCK, addr(1), raw)
                state = cache._current.get()
                now[0] = 25
                cache.runtime_digest(expiring, BLOCK, addr(1), raw)
        self.assertEqual((state.replies, state.retained_bytes), ({}, 0))
        self.assertIsNone(cache._current.get())
        self.assertIsNone(checkpoint())
        self.assertEqual((cache.MAX_ENTRY_BYTES, cache.MAX_RETAINED_BYTES), (65536, 8*1048576))


if __name__ == '__main__':
    unittest.main()
