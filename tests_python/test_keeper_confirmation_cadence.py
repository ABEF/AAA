"""Four-minute service scheduling, with strict five-minute on-chain evidence.

No contract configuration, running journal, signer or service is changed.
"""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.health import HEALTH_SCHEMA, execution_reasons, observe_confirmation_health
from keeper.monitor import Keeper, CONFIRMATION_RESETS, CONFIRMATION_STATE
from keeper.rebalance_confirmation import CHECK_SECONDS
from tests_python import test_keeper_rebalance_confirmation as fixtures
from tests_python import test_keeper_confirmation_writer as writer_fixtures
from zzz_ops.abi import calldata


class KeeperConfirmationCadenceTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.KeeperConfirmationTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.k, self.cfg, self.rpc = self.f.k, self.f.cfg, self.f.rpc

    def seed_legacy_schedule(self):
        self.f.side = 0
        self.f.cycle().assert_not_called()
        self.k.state[CONFIRMATION_STATE]['7']['next_check_at'] = self.rpc.now + 300
        self.k.save()

    def pending(self):
        self.k.state['next_nonce'] = 0
        self.k.state['pending'] = {'key': 'harvest:7', 'nonce': 0,
            'to': self.cfg['contracts']['vault'], 'data': calldata('collectFees(uint256,uint256)', 7, self.rpc.now + 180),
            'value': 0, 'day': '2026-10-29', 'hash': '0x' + 'ab' * 32,
            'fee_review': {'schema': 1, 'gas_limit': 100, 'max_fee_per_gas': 1,
                'l1_fee_allowance_wei': 0, 'maximum_cost_wei': 100, 'receipt_fee_policy': 'included'}}
        self.k._validate_state()
        self.k.save()

    def test_fresh_checks_run_at_240_seconds_without_changing_900_300_policy(self):
        self.f.side = 0
        self.f.cycle().assert_not_called()
        self.rpc.now += 239
        self.f.side = 1
        self.f.cycle().assert_not_called()
        self.rpc.now += 1
        self.f.cycle().assert_called_once_with('rebalance_confirmation', 'observe(uint256)', (7,), 'rebalance_observation:7')
        self.assertEqual(240, CHECK_SECONDS)
        self.assertEqual(self.rpc.now + 240, self.f.schedule()['next_check_at'])
        with patch('keeper.monitor.time.time', return_value=self.rpc.now):
            policy = self.k.rebalance_confirmation.validate()
        self.assertEqual((900, 300), (policy['duration_seconds'], policy['maximum_gap_seconds']))

    def test_legacy_300_schedule_is_read_without_rewrite_then_checks_at_240(self):
        self.seed_legacy_schedule()
        before = copy.deepcopy(self.k.state)
        disk = self.k.path.read_bytes()
        restarted = Keeper(self.cfg, rpc=self.rpc)
        self.assertEqual(restarted.state, before)
        self.assertEqual(restarted.path.read_bytes(), disk)
        self.f.k = restarted
        self.rpc.now += 239
        self.f.side = 1
        self.f.cycle().assert_not_called()
        self.rpc.now += 1
        self.f.cycle().assert_called_once_with('rebalance_confirmation', 'observe(uint256)', (7,), 'rebalance_observation:7')
        saved = json.loads(restarted.path.read_text())
        self.assertEqual(self.rpc.now + 240, saved[CONFIRMATION_STATE]['7']['next_check_at'])

    def test_restore_accepts_only_new_240_or_explicit_legacy_300_schedule(self):
        self.seed_legacy_schedule()
        for delta in (240, 300, 239, 241, 299, 301):
            self.k.state[CONFIRMATION_STATE]['7']['next_check_at'] = self.rpc.now + delta
            self.k.save()
            with self.subTest(delta=delta):
                if delta in (240, 300):
                    Keeper(self.cfg, rpc=self.rpc)
                else:
                    with self.assertRaisesRegex(ValueError, 'schedule bounds'):
                        Keeper(self.cfg, rpc=self.rpc)

    def test_pending_recovery_preserves_legacy_schedule_reset_markers_and_nonce(self):
        self.seed_legacy_schedule()
        self.k.state[CONFIRMATION_RESETS] = {'7': True}
        self.pending()
        before = copy.deepcopy(self.k.state)
        disk = self.k.path.read_bytes()
        restarted = Keeper(self.cfg, rpc=self.rpc)
        with patch.object(restarted, 'submit') as submit, patch.object(restarted, 'save') as save:
            restarted.cycle()
        submit.assert_not_called()
        save.assert_not_called()
        self.assertEqual(restarted.state, before)
        self.assertEqual(restarted.path.read_bytes(), disk)

    def test_startup_does_not_adopt_foreign_samples_or_old_jitter(self):
        self.k._confirmation_seen_buckets.add(7)
        self.f.record = [self.f.identity, self.rpc.now - 900, self.rpc.now, 1]
        with patch('keeper.monitor.secrets.randbelow', return_value=540):
            self.f.cycle()
        saved = self.k.state[CONFIRMATION_STATE]['7']
        saved['next_check_at'] = saved['last_checked_at'] + 300
        self.k.save()
        before = copy.deepcopy(self.k.state)
        restarted = Keeper(self.cfg, rpc=self.rpc)
        self.assertEqual(restarted.state, before)
        self.f.k = restarted
        self.rpc.now += 240
        self.f.record[2] = self.rpc.now
        self.f.cycle().assert_called_once_with('rebalance_confirmation', 'resetObservation(uint256)', (7,), 'rebalance_reset:7')
        self.assertTrue(restarted.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7', restarted.state.get(CONFIRMATION_STATE, {}))

    def test_writer_and_checker_require_explicit_current_240_cadence(self):
        fixture = writer_fixtures.KeeperConfirmationWriterTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        ok, data = fixture.run_writer()
        self.assertTrue(ok)
        outer = data['rebalance_confirmation_health']
        self.assertEqual(240, outer['check_interval_seconds'])
        self.assertEqual([], execution_reasons(data, fixture.f.cfg, now=fixture.rpc.now, max_age=1800))
        for value in (300, 60, True, None):
            bad = copy.deepcopy(data)
            bad['rebalance_confirmation_health']['check_interval_seconds'] = value
            with self.subTest(value=value):
                self.assertIn('confirmation_service_cadence_mismatch',
                    execution_reasons(bad, fixture.f.cfg, now=fixture.rpc.now, max_age=1800))

    def test_gap_admission_tracks_service_cadence_without_overriding_governance(self):
        for gap, state in ((239, 'incompatible_cadence'), (240, 'observed_this_cycle'), (300, 'observed_this_cycle')):
            self.f.gap = gap
            with patch('keeper.monitor.time.time', return_value=self.rpc.now):
                report = observe_confirmation_health(self.k)
            self.assertEqual(state, report['state'])
            self.assertEqual(gap, report['last_observed']['maximum_gap_seconds'])
            data = {'health_schema': HEALTH_SCHEMA, 'rebalance_confirmation_health': {
                'version': 1, 'check_interval_seconds': 240, 'policy': report}}
            reasons = execution_reasons(data, self.cfg, now=self.rpc.now, max_age=1800)
            self.assertEqual(gap < 240, 'rebalance_confirmation_cadence_incompatible' in reasons)
