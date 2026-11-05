"""Last-day royalty/backend regressions; synthetic chain transcripts only."""
import copy
import json
import unittest

from frontend_api.earnings_checkpoint import decode
from frontend_api.service import Projection, ProjectionError
from tests_python import test_earnings_checkpoints as checkpoint_fixtures
from tests_python.test_earnings import event
from tests_python.test_frontend_api import addr
from tests_python import test_royalty_launch_window as window_fixtures
from zzz_ops.abi import keccak256

ZERO = '0x' + '0' * 40


class RoyaltyOpeningCheckpointTests(unittest.TestCase):
    def setUp(self):
        f = checkpoint_fixtures.CheckpointAPITests('runTest')
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f = f
        f.config['royalty_reporting'] = {'schema': 4, 'converter': None}
        f.put(addr(5), 'ROYALTY_SETTLEMENT_VERSION()', values=(3,))
        f.put(f.c['handoff'], 'SCHEMA()', values=(
            '0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_ROYALTY_OPENING_V7').hex(),))
        self.end = int(f.rpc.header(13)['timestamp'], 16) + 100
        self.cutoff = self.end + 3600
        for sig, value in [('mintEnd()', self.end), ('royaltiesOpenAt()', self.cutoff), ('royaltiesOpen()', 1)]:
            f.put(addr(5), sig, values=(value,))
        for a in (ZERO, addr(21)):
            f.put(addr(5), 'openingPool(address)', (a,), (0,))
        with f.index.db:
            f.index.db.execute('DELETE FROM logs WHERE address=? AND block_number=21', (addr(5),))
        for ev in (
            event('royalties', 'MintEndConfigured', (), (self.end, self.cutoff), 10, 2),
            event('royalties', 'RoyaltyOpeningFinalized', (), (self.cutoff, 1, 1), 21),
            event('royalties', 'RoyaltiesReceived', (ZERO,), (100, 0), 21, 1),
            event('royalties', 'InitialRoyaltiesAllocated', (ZERO,), (100, 1, 1), 21, 2),
            event('royalties', 'InitialRoyaltiesAllocated', (addr(21),), (0, 1, 1), 21, 3),
        ):
            f.insert(ev)

    def test_post_opening_builder_reconciles_every_nft_and_carries_window_state(self):
        raw = self.f.candidate()
        state = decode(json.loads(raw)['state'])
        self.assertEqual(state['shared']['royalty_opening'], (self.cutoff, 1, 1))
        self.assertEqual(state['shared']['initial_royalty_allocations'], {ZERO, addr(21)})
        self.assertEqual(state['accounts'][self.f.i]['royalties', ZERO] // 10**36, 100)
        self.assertTrue(all(v == 0 for v in state['accounts'][self.f.j].values()))

    def test_post_opening_checkpoint_restore_and_suffix_match_full_replay(self):
        self.f.install()
        self.f.suffix()
        full = copy.deepcopy(self.f.config)
        del full['earnings_history']['checkpoint']
        for identifier in (None, str(self.f.i), str(self.f.j)):
            seeded = self.f.projection().earnings(identifier)
            replayed = self.f.projection(full).earnings(identifier)
            for key in ('all_time', 'last_24h', 'window', 'event_count'):
                self.assertEqual(seeded[key], replayed[key])

    def test_builder_reconciles_a_currency_whose_initial_pool_is_still_pending(self):
        f = self.f
        with f.index.db:
            f.index.db.execute('DELETE FROM logs WHERE address=? AND block_number=21 AND log_index=3', (addr(5),))
        f.put(addr(5), 'openingPool(address)', (addr(21),), (6,))
        f.put(addr(5), 'pending(address)', (addr(21),), (2,))
        f.put(addr(5), 'claimable(uint256,address)', (f.i, addr(21)), (8,))
        state = decode(json.loads(f.candidate())['state'])
        self.assertEqual(state['shared']['initial_royalty_allocations'], {ZERO})
        self.assertEqual(state['accounts'][f.i].get(('royalties', addr(21)), 0), 0)

    def test_builder_preserves_lazy_global_finalization_and_pending_initial_entitlement(self):
        f = self.f
        with f.index.db:
            f.index.db.execute('DELETE FROM logs WHERE address=? AND block_number=21', (addr(5),))
        f.insert(event('royalties', 'RoyaltiesReceived', (ZERO,), (100, 0), 15))
        f.put(addr(5), 'index(address)', (ZERO,), (0,))
        f.put(addr(5), 'openingPool(address)', (ZERO,), (100,))
        state = decode(json.loads(f.candidate())['state'])
        self.assertIsNone(state['shared']['royalty_opening'])
        self.assertEqual(state['shared']['initial_royalty_allocations'], set())
        self.assertEqual(state['accounts'][f.i].get(('royalties', ZERO), 0), 0)


class RoyaltyOpeningSnapshotTests(unittest.TestCase):
    def test_reported_open_flag_must_match_the_confirmed_snapshot_timestamp(self):
        for opened, timestamp in ((True, 990), (False, 4800), (False, 4801)):
            fixture = window_fixtures.RoyaltyWindowReportingTests('runTest')
            config, rpc = fixture.fixture(opened=opened)
            rpc.header_timestamp = timestamp
            with self.subTest(opened=opened, timestamp=timestamp):
                with self.assertRaisesRegex(ProjectionError, 'opening.*timestamp'):
                    Projection(config, rpc, clock=lambda: timestamp+1).nft(str(rpc.nft_id))

    def test_exact_opening_timestamp_is_accepted_and_preserved(self):
        fixture = window_fixtures.RoyaltyWindowReportingTests('runTest')
        config, rpc = fixture.fixture(opened=True)
        rpc.header_timestamp = 4800
        value = Projection(config, rpc, clock=lambda: 4801).nft(str(rpc.nft_id))
        self.assertTrue(value['royalty_reporting']['opening']['claims_open'])


if __name__ == '__main__':
    unittest.main()
