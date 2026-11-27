"""NEW opt-in earnings read scope and composed economic equivalence checks.

Only the existing exact7 fixture's setup/helpers are reused, never its test
bodies. Its RPC/code/clock are controlled and SQLite/builder/checkpoint/replay
are real. This is not normal F6, provider, HTTP or production qualification.
"""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from frontend_api import canonical_cache as cache
from frontend_api.earnings import Earnings
from frontend_api.service import Projection
from tests_python import test_earnings_checkpoint_v2 as exact_fixture
from zzz_ops.abi import calldata
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, BudgetedRPC, checkpoint, consume, request_scope

BLOCK = {'blockHash': '0x'+'ab'*32, 'requireCanonical': True}
PARAMS = [{'to': '0x'+'01'*20, 'data': '0x12345678'}, BLOCK]
MISSING = object()


class Wire:
    def __init__(self, inner=None):
        self.inner = inner
        self.calls = []
        self.fail = False

    def call(self, method, params=None):
        consume('posts')
        self.calls.append((method, deepcopy(params)))
        if self.fail:
            raise RpcError('Unavailable canonical getter')
        if self.inner is not None:
            return self.inner.call(method, params)
        if method == 'eth_call':
            return '0x'+f'{17:064x}'
        if method == 'eth_getBlockByNumber':
            return {'observed': len(self.calls)}
        if method == 'eth_chainId':
            return 4663
        raise AssertionError('Unexpected read')

    def __getattr__(self, name):
        if self.inner is None:
            raise AttributeError(name)
        return getattr(self.inner, name)


def reader(profile=1):
    wire = Wire()
    e = Earnings.__new__(Earnings)
    e.p = Projection.__new__(Projection)
    e.p.rpc = BudgetedRPC(wire)
    e.p.lineage = None
    if profile is not MISSING:
        e.p.wallet_read_batch = profile
    return e, wire


def canonical_counts(calls):
    keys = []
    for method, params in calls:
        if method in ('eth_call', 'eth_getCode') and isinstance(params, list) and len(params) == 2:
            block = params[1]
            if isinstance(block, dict) and block.get('requireCanonical') is True:
                keys.append((method, json.dumps(params, sort_keys=True, separators=(',', ':'))))
    return len(keys), len(set(keys))


class EarningsReadCacheScopeTests(unittest.TestCase):
    def test_actual_exact_checkpoint_and_suffix_keep_payout_transfer_and_full_day(self):
        f = exact_fixture.Checkpoint2APITests('runTest')
        self.addCleanup(f.doCleanups)
        f.setUp()
        saved = f.install()
        immutable = saved.read_bytes()
        observed = Wire(f.rpc)
        f.rpc = observed
        metrics = []

        def compare(identifier):
            outputs = []
            calls = []
            for profile in (0, 1):
                config = deepcopy(f.config)
                config['wallet_read_batch'] = profile
                p = f.projection(config)
                original = p.rpc
                observed.calls.clear()
                outputs.append(p.earnings(str(identifier)))
                calls.append(deepcopy(observed.calls))
                self.assertIs(p.rpc, original)
                self.assertIsNone(cache._current.get())
                self.assertIsNone(checkpoint())
            before, after = outputs
            comparable = deepcopy(outputs)
            for value in comparable:
                value['provenance'].pop('configuration_sha256')
            self.assertNotEqual(before['provenance']['configuration_sha256'],
                                after['provenance']['configuration_sha256'])
            self.assertEqual(comparable[0], comparable[1])
            self.assertEqual(after['window']['through_timestamp_inclusive']-
                             after['window']['after_timestamp_exclusive'], 86400)
            plain, opted = map(canonical_counts, calls)
            self.assertGreater(plain[0], plain[1])
            self.assertEqual(opted[0], opted[1])
            self.assertLess(opted[0], plain[0])
            live = lambda rows: [row for row in rows if row[0] in
                                ('eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber')]
            self.assertEqual(live(calls[0]), live(calls[1]))
            metrics.append({'NFT': str(identifier), 'legacy_canonical_reads': plain[0],
                            'optin_canonical_reads': opted[0], 'live_proof_reads': len(live(calls[1]))})
            return after

        prefix = compare(f.i)
        # The neutral physical fixture uses bucket7, while this actual local
        # event ledger uses bucket5. Bind the existing same main/key/ticks/custody
        # transcript to that ledger bucket; no economic getter is replaced.
        q = f.inner.responses.physical
        for role, method in (('vault', 'group(uint256)'),
                             ('portfolio_policy', 'configurationPending(uint256)')):
            target = f.c[role]
            f.inner.responses.selected[target, calldata(method, 5)] = (target, method, (5,))
        q.overrides[f.c['vault'], 'poolBucket(bytes32)'] = [f'{5:064x}']
        nft_outputs = []
        nft_calls = []
        for profile in (0, 1):
            config = deepcopy(f.config)
            config['wallet_read_batch'] = profile
            p = f.projection(config)
            original = p.rpc
            observed.calls.clear()
            item = p.nft(f.i)
            nft_calls.append(deepcopy(observed.calls))
            item['provenance'].pop('configuration_sha256')  # Opt-in changes config identity only.
            nft_outputs.append(item)
            self.assertIs(p.rpc, original)
            self.assertIsNone(cache._current.get())
            self.assertIsNone(checkpoint())
        self.assertEqual(nft_outputs[0], nft_outputs[1])
        physical = nft_outputs[1]['position']['local_custody']['portfolio']
        self.assertEqual(len(physical['physical_legs']), 1)
        self.assertEqual(physical['bucket_id'], '5')
        plain, opted = map(canonical_counts, nft_calls)
        self.assertGreater(plain[0], plain[1])
        self.assertEqual(opted[0], opted[1])
        self.assertLess(opted[0], plain[0])
        live = lambda rows: [row for row in rows if row[0] in
                            ('eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber')]
        self.assertEqual(live(nft_calls[0]), live(nft_calls[1]))
        metrics.append({'kind': 'NFT_detail_one_leg', 'legacy_canonical_reads': plain[0],
                        'optin_canonical_reads': opted[0], 'live_proof_reads': len(live(nft_calls[1]))})
        f.suffix()  # Actual raw transfer, activation, growth, conversion and claims.
        active = compare(f.i)
        late = compare(f.j)
        dormant = compare(f.k)
        self.assertNotEqual(prefix['owner'], active['owner'])
        self.assertEqual(active['owner'], exact_fixture.addr(32))
        self.assertEqual(active['provenance']['epochs'][0]['history']['claim_events'], 3)
        self.assertEqual(active['provenance']['epochs'][0]['history']['lp_conversion_events'], 2)
        rows = {row['asset']: row for row in active['all_time']}
        self.assertEqual(rows[exact_fixture.ZERO]['royalties_raw'], '10')
        self.assertEqual(next(row for row in late['all_time'] if row['asset'] == exact_fixture.ZERO)['royalties_raw'], '6')
        self.assertTrue(all(int(value) == 0 for row in dormant['all_time']
                            for key, value in row.items() if key.endswith('_raw')))
        self.assertEqual(saved.read_bytes(), immutable)
        type(self).actual_metrics = metrics

    def test_optin_exact_keys_preserve_alias_boundaries_live_proofs_and_legacy(self):
        for route in ('earnings', 'nft'):
            for profile in (MISSING, 0, 1):
                with self.subTest(route=route, profile='omitted' if profile is MISSING else profile):
                    e, wire = reader(profile)
                    original = e.p.rpc
                    changed_sender = deepcopy(PARAMS)
                    changed_sender[0]['from'] = '0x'+'02'*20
                    changed_block = deepcopy(PARAMS)
                    changed_block[1]['blockHash'] = '0x'+'cd'*32

                    def read(_):
                        e.p.rpc.call('eth_call', PARAMS)
                        e.p.rpc.call('eth_call', PARAMS)
                        e.p.rpc.call('eth_call', changed_sender)
                        e.p.rpc.call('eth_call', changed_block)
                        first = e.p.rpc.call('eth_getBlockByNumber', ['0x1', False])
                        second = e.p.rpc.call('eth_getBlockByNumber', ['0x1', False])
                        self.assertNotEqual(first, second)
                        for _ in range(2):
                            self.assertEqual(e.p.rpc.call('eth_chainId', []), 4663)
                        return {'raw': '17'}

                    target, private, public = (e, '_read', e.read) if route == 'earnings' else (e.p, '_nft', e.p.nft)
                    with patch.object(target, private, side_effect=read), request_scope(Budget(calls=10, posts=10)):
                        self.assertEqual(public(1), {'raw': '17'})
                    self.assertEqual(len(wire.calls), 7 if profile == 1 else 8)
                    self.assertIs(e.p.rpc, original)
                    self.assertIsNone(cache._current.get())

    def test_cached_read_still_obeys_expiry_and_stricter_outer_budget(self):
        for route in ('earnings', 'nft'):
            e, wire = reader()
            original = e.p.rpc
            now = [0.0]
            budget = Budget(seconds=25, calls=1, posts=1, clock=lambda: now[0])

            def expired(_):
                e.p.rpc.call('eth_call', PARAMS)
                now[0] = 25
                return e.p.rpc.call('eth_call', PARAMS)

            target, private, public = (e, '_read', e.read) if route == 'earnings' else (e.p, '_nft', e.p.nft)
            with patch.object(target, private, side_effect=expired):
                with self.assertRaisesRegex(WorkLimit, 'deadline'):
                    with request_scope(budget):
                        public(1)
            self.assertEqual(len(wire.calls), 1)
            self.assertEqual((budget.calls, budget.posts), (0, 0))
            self.assertIs(e.p.rpc, original)
            self.assertIsNone(cache._current.get())
            self.assertIsNone(checkpoint())
            defaults = Budget()
            self.assertEqual((defaults.calls, defaults.posts), (1024, 2048))
            self.assertLessEqual(defaults.deadline-defaults.clock(), 25)

    def test_getter_failure_propagates_and_cannot_poison_a_later_request(self):
        for route in ('earnings', 'nft'):
            e, wire = reader()
            original = e.p.rpc
            wire.fail = True
            target, private, public = (e, '_read', e.read) if route == 'earnings' else (e.p, '_nft', e.p.nft)
            with patch.object(target, private, side_effect=lambda _: e.p.rpc.call('eth_call', PARAMS)):
                with self.assertRaisesRegex(RpcError, 'Unavailable canonical getter'):
                    with request_scope():
                        public(1)
                self.assertIs(e.p.rpc, original)
                self.assertIsNone(cache._current.get())
                wire.fail = False
                with request_scope():
                    self.assertEqual(public(1), '0x'+f'{17:064x}')
                with request_scope():
                    self.assertEqual(public(1), '0x'+f'{17:064x}')
            self.assertEqual(len(wire.calls), 3)
            self.assertIs(e.p.rpc, original)
            self.assertIsNone(cache._current.get())
            self.assertIsNone(checkpoint())


if __name__ == '__main__':
    unittest.main()
