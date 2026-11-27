"""NEW build-hook/cache boundaries; economic replay is not replaced or qualified.

The patched private builder isolates only the public build hook. Real canonical
cache and logical/physical work budgets execute; no old test body or RPC runs.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api import canonical_cache as cache
from frontend_api import earnings_checkpoint as checkpoints
from frontend_api import earnings_checkpoint_build as builder
from frontend_api.history import HistoryError
from zzz_ops.work_budget import BudgetedRPC, checkpoint, consume, request_scope

BLOCK = {'blockHash': '0x'+'ab'*32, 'requireCanonical': True}
PARAMS = [{'to': '0x'+'01'*20, 'data': '0x12345678'}, BLOCK]
MISSING = object()


class Wire:
    def __init__(self):
        self.calls = []

    def call(self, method, params=None):
        consume('posts')
        self.calls.append((method, deepcopy(params)))
        if method == 'eth_call':
            return '0x'+f'{17:064x}'
        if method == 'eth_getCode':
            return '0x6000'
        if method == 'eth_chainId':
            return 4663
        if method == 'eth_getBlockByNumber':
            return {'number': '0x1', 'hash': BLOCK['blockHash'], 'observed': len(self.calls)}
        raise AssertionError('Unexpected read')


def engine(profile=1):
    wire = Wire()
    projection = SimpleNamespace(rpc=BudgetedRPC(wire), lineage=None)
    if profile is not MISSING:
        projection.wallet_read_batch = profile
    return SimpleNamespace(p=projection), wire


class CheckpointBuildCacheScopeTests(unittest.TestCase):
    def test_optin_reuses_canonical_reads_but_keeps_headers_and_chain_live(self):
        e, wire = engine()
        original = e.p.rpc
        budget = builder.BuildBudget(calls=8, posts=8)

        def construct(actual, number):
            self.assertIs(actual, e)
            self.assertEqual(number, 1)
            for method, params in (('eth_call', PARAMS), ('eth_getCode', [PARAMS[0]['to'], BLOCK])):
                self.assertEqual(actual.p.rpc.call(method, params), actual.p.rpc.call(method, params))
            before = actual.p.rpc.call('eth_getBlockByNumber', ['0x1', False])
            after = actual.p.rpc.call('eth_getBlockByNumber', ['0x1', False])
            self.assertNotEqual(before['observed'], after['observed'])
            for _ in range(2):
                self.assertEqual(actual.p.rpc.call('eth_chainId', []), 4663)
            return b'unchanged candidate bytes'

        with patch.object(builder, '_build', side_effect=construct):
            self.assertEqual(builder.build(e, 1, budget=budget), b'unchanged candidate bytes')
        self.assertEqual([row[0] for row in wire.calls],
                         ['eth_call', 'eth_getCode', 'eth_getBlockByNumber', 'eth_getBlockByNumber',
                          'eth_chainId', 'eth_chainId'])
        self.assertEqual((budget.calls, budget.posts), (2, 2))
        self.assertIs(e.p.rpc, original)
        self.assertIsNone(cache._current.get())
        self.assertIsNone(checkpoint())

    def test_refusal_restores_transport_and_no_reply_survives_the_build_job(self):
        e, wire = engine()
        original = e.p.rpc

        def refused(actual, number):
            actual.p.rpc.call('eth_call', PARAMS)
            actual.p.rpc.call('eth_call', PARAMS)
            raise HistoryError('confirmed entitlement mismatch')

        with patch.object(builder, '_build', side_effect=refused):
            for expected in (1, 2):
                with self.assertRaisesRegex(HistoryError, 'entitlement mismatch'):
                    builder.build(e, 1, budget=builder.BuildBudget(calls=1, posts=1))
                self.assertEqual(len(wire.calls), expected)
                self.assertIs(e.p.rpc, original)
                self.assertIsNone(cache._current.get())
                self.assertIsNone(checkpoint())
        with request_scope(builder.BuildBudget(calls=1, posts=1)) as outer:
            with patch.object(builder, '_build', side_effect=lambda actual, _: actual.p.rpc.call('eth_call', PARAMS)):
                builder.build(e, 1)
            self.assertEqual((outer.calls, outer.posts), (0, 0))

    def test_omitted_and_zero_profiles_keep_legacy_transport_and_default_limits(self):
        for profile in (MISSING, 0):
            with self.subTest(profile='omitted' if profile is MISSING else profile):
                e, wire = engine(profile)
                original = e.p.rpc

                def legacy(actual, _):
                    self.assertIs(actual.p.rpc, original)
                    actual.p.rpc.call('eth_call', PARAMS)
                    actual.p.rpc.call('eth_call', PARAMS)
                    return b'legacy'

                with patch.object(builder, '_build', side_effect=legacy):
                    self.assertEqual(builder.build(e, 1), b'legacy')
                self.assertEqual(len(wire.calls), 2)
        defaults = builder.BuildBudget()
        self.assertEqual((defaults.calls, defaults.posts), (4096, 8192))
        self.assertGreater(defaults.deadline-defaults.clock(), 0)
        self.assertLessEqual(defaults.deadline-defaults.clock(), 60)
        self.assertEqual((cache.MAX_ENTRY_BYTES, cache.MAX_RETAINED_BYTES), (65536, 8*1048576))

    def test_changed_builder_source_rejects_old_checkpoint_before_identity_or_state(self):
        sources = checkpoints.source_identity(2)
        previous = 'f5eca20abda61ef591d3a8dc65a50eb8275aea363e07e0ed25a3b8134d64e192'
        self.assertNotEqual(sources['frontend_api/earnings_checkpoint_build.py'], previous)
        sources['frontend_api/earnings_checkpoint_build.py'] = previous
        payload = dict(schema=2, sources=sources, identity=None, anchor=None, state=None, previous_sha256=None)
        raw = (json.dumps(payload)+'\n').encode()
        e = SimpleNamespace(p=SimpleNamespace(lineage=None, accounting_version=7, custody_version=5,
                            fee_intake_version=1, royalty_reporting=SimpleNamespace(schema=5)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'old-source.json'
            path.write_bytes(raw)
            with patch.object(checkpoints, 'identity', side_effect=AssertionError('Untrusted state reached')):
                with self.assertRaisesRegex(HistoryError, 'semantic source changed'):
                    checkpoints.Checkpoint({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}, e)


if __name__ == '__main__':
    unittest.main()
