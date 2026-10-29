"""Relevant LP identity faults invalidate sampled work, using inert RPCs only."""
import copy
import unittest
from unittest.mock import patch

from keeper.monitor import CONFIRMATION_CLEARS, CONFIRMATION_RESETS, CONFIRMATION_STATE
from tests_python import test_keeper_confirmation_followup as fixtures
from zzz_ops.rpc import RpcError


class KeeperBucketFaultResetTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.KeeperConfirmationFollowupTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.k, self.rpc = self.fixture.k, self.fixture.rpc
        self.fixture.mature()

    def occupancy_fault(self, *, contradictory=False):
        original = self.k.view
        def view(role, signature, *args):
            if role == 'vault' and signature == 'poolBucket(bytes32)':
                if contradictory:
                    return 999
                raise RpcError('inert pool occupancy outage')
            return original(role, signature, *args)
        return patch.object(self.k, 'view', side_effect=view)

    def assert_reset(self):
        self.assertIs(self.k.state.get(CONFIRMATION_RESETS, {}).get('7'), True)
        self.assertNotIn('7', self.k.state.get(CONFIRMATION_STATE, {}))
        self.assertIsNone(self.k.state['pending'])

    def test_occupancy_outage_or_contradiction_resets_only_affected_bucket(self):
        self.k.state[CONFIRMATION_STATE]['8'] = copy.deepcopy(self.k.state[CONFIRMATION_STATE]['7'])
        saved = copy.deepcopy(self.k.state)
        for contradictory in (False, True):
            self.k.state = copy.deepcopy(saved)
            with self.subTest(contradictory=contradictory), self.occupancy_fault(contradictory=contradictory) as view:
                with self.assertRaises(RpcError):
                    self.k._bucket(7)
                self.assertIn(('vault', 'poolBucket(bytes32)', self.fixture.f.base.pool),
                              [call.args for call in view.call_args_list])
                self.assert_reset()
                self.assertEqual(saved[CONFIRMATION_STATE]['8'], self.k.state[CONFIRMATION_STATE]['8'])
                self.assertEqual({'7'}, set(self.k.state[CONFIRMATION_RESETS]))

    def test_active_or_parked_physical_identity_fault_requires_reset(self):
        before = copy.deepcopy(self.k.state)
        original = list(self.fixture.f.base.group_words)
        for status, lp in ((1, 0), (4, original[1])):
            self.k.state = copy.deepcopy(before)
            self.fixture.f.base.group_words[:] = original
            self.fixture.f.base.group_words[1] = lp
            self.fixture.f.base.group_words[7] = status
            with self.subTest(status=status):
                with self.assertRaises(RpcError):
                    self.k._bucket(7)
                self.assert_reset()

    def test_missing_pool_identity_requires_reset_before_further_inventory_reads(self):
        self.fixture.f.base.group_words[0] = 0
        with patch.object(self.k, 'view', wraps=self.k.view) as view, self.assertRaises(RpcError):
            self.k._bucket(7)
        self.assertNotIn('bucketTotalShares(uint256)', [call.args[1] for call in view.call_args_list])
        self.assert_reset()

    def test_recovery_cannot_reuse_old_jitter_before_canonical_clear(self):
        old = copy.deepcopy(self.k.state)
        with self.occupancy_fault():
            self.fixture.cycle().assert_not_called()
        self.assert_reset()
        self.rpc.now += 60
        self.fixture.cycle().assert_called_once_with('rebalance_confirmation', 'resetObservation(uint256)',
                                                   (7,), 'rebalance_reset:7')
        self.assert_reset()
        self.assertEqual(old['spent'], self.k.state['spent'])
        self.assertEqual(old['last'], self.k.state['last'])

    def test_share_inventory_outage_remains_unrelated_to_the_sample(self):
        before = copy.deepcopy(self.k.state)
        with self.fixture.raw_fault('bucketTotalShares(uint256)', 7), self.assertRaises(RpcError):
            self.k._bucket(7)
        self.assertEqual(before, self.k.state)

    def test_terminal_stop_does_not_create_new_confirmation_reset_work(self):
        self.k.principal_exit_started = True
        before = copy.deepcopy(self.k.state)
        with self.occupancy_fault(), self.assertRaises(RpcError):
            self.k._bucket(7)
        self.assertEqual(before, self.k.state)

    def test_existing_clear_receipt_waits_for_recovery_without_repeated_paid_resets(self):
        self.k.state[CONFIRMATION_CLEARS] = {'7': dict(number=98, hash=fixtures.fixtures.basic.H,
            timestamp=self.rpc.now-10, nonce=6, awaiting_healthy_read=False)}
        with self.occupancy_fault(), patch.object(self.k, 'save', wraps=self.k.save) as save:
            for _ in range(2):
                with self.assertRaises(RpcError):
                    self.k._bucket(7)
            self.assertEqual(1, save.call_count)
        self.assertNotIn('7', self.k.state.get(CONFIRMATION_RESETS, {}))
        self.assertNotIn('7', self.k.state.get(CONFIRMATION_STATE, {}))
        self.assertTrue(self.k.state[CONFIRMATION_CLEARS]['7']['awaiting_healthy_read'])

    def test_coherent_position_does_not_invalidate_saved_sample(self):
        before = copy.deepcopy(self.k.state)
        fields, tokens = self.k._bucket(7)
        self.assertEqual(8, len(fields))
        self.assertEqual(2, len(tokens))
        self.assertEqual(before, self.k.state)

    def test_saved_intent_recovery_precedes_any_bucket_identity_read(self):
        self.k.state['pending'] = {'key': 'harvest:7'}
        before = copy.deepcopy(self.k.state)
        with patch.object(self.k, 'poll_pending', return_value=True), \
                patch.object(self.k, '_bucket', side_effect=AssertionError('pending recovery first')):
            self.k.cycle()
        self.assertEqual(before, self.k.state)

    def test_failed_reset_persistence_preserves_the_original_state_and_propagates(self):
        before = copy.deepcopy(self.k.state)
        stored = self.k.path.read_bytes()
        with self.occupancy_fault(), patch.object(self.k, 'save', side_effect=OSError('inert disk failure')), \
                self.assertRaises(OSError):
            self.k._bucket(7)
        self.assertEqual(before, self.k.state)
        self.assertEqual(stored, self.k.path.read_bytes())

    def test_fresh_confirmation2_uses_the_same_durable_identity_fault_reset(self):
        from tests_python import test_reference_confirmation_v2 as current
        fixture = current.KeeperReferenceConfirmationV2Tests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        keeper = fixture.k
        self.assertEqual(2, keeper.rebalance_confirmation.version)
        # An already tracked window uses the same explicit schedule format.
        keeper._store_rebalance_schedule(7, copy.deepcopy(self.k.state[CONFIRMATION_STATE]['7']))
        original = keeper.view
        def view(role, signature, *args):
            if role == 'vault' and signature == 'poolBucket(bytes32)':
                raise RpcError('inert current-profile identity outage')
            return original(role, signature, *args)
        with patch.object(keeper, 'view', side_effect=view), self.assertRaises(RpcError):
            keeper._bucket(7)
        self.assertTrue(keeper.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7', keeper.state[CONFIRMATION_STATE])


if __name__ == '__main__':
    unittest.main()
