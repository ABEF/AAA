"""Deadline scheduling with inert RPCs and a mocked serial submission boundary.

No operating journal, signer, service or RPC endpoint is used. Queue pressure is
deliberately continuous; a fair cursor alone cannot meet a strict sample gap.
"""
import contextlib
import copy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from keeper.monitor import CONFIRMATION_RESETS, CONFIRMATION_STATE, main
from tests_python import test_keeper_rebalance_confirmation as fixtures
from zzz_ops.rpc import RpcError


class _StopMain(Exception):
    pass


class KeeperConfirmationPriorityTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.KeeperConfirmationTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.k, self.rpc, self.cfg = self.f.k, self.f.rpc, self.f.cfg

    def tracked(self):
        self.f.cycle()
        self.k._confirmation_seen_buckets.add(7)
        self.f.record = [self.f.identity, self.rpc.now, self.rpc.now, 1]

    def busy(self, *, kind='conversion'):
        self.k.lp_rewards.enabled = False
        self.k.royalties.enabled = False
        self.k.metadata_enabled = False
        if kind == 'conversion':
            self.k.lp_rewards = SimpleNamespace(enabled=True, key='lp_conversion',
                scan_once=lambda: self.k.submit('rewards', 'inert-conversion', (), 'conversion'))
            self.k.state['conversion_turn'] = 0
        elif kind == 'buyback':
            self.k.state['buyback_priority'] = True
            return patch.object(self.k, '_buyback_tasks', return_value=[{}]), patch.object(
                self.k, '_buyback_once', side_effect=lambda tasks:
                self.k.submit('buyback', 'inert-buyback', (), 'buyback'))
        else:
            self.k.metadata_enabled = True
            self.k.state['metadata_refresh'] = {'next_first': True}
            return patch.object(self.k, '_refresh_metadata', side_effect=lambda:
                self.k.submit('nft', 'inert-metadata', (), 'metadata')),
        return ()

    def cycle(self):
        self.f.k = self.k
        return self.f.cycle()

    def test_due_existing_window_precedes_busy_optional_queues(self):
        self.tracked()
        self.rpc.now += 240
        for kind in ('conversion', 'buyback', 'metadata'):
            with self.subTest(queue=kind), contextlib.ExitStack() as stack:
                before = copy.deepcopy(self.k.state)
                stack.callback(setattr, self.k, 'state', before)
                for manager in self.busy(kind=kind):
                    stack.enter_context(manager)
                self.cycle().assert_called_once_with('rebalance_confirmation', 'observe(uint256)',
                    (7,), 'rebalance_observation:7')

    def test_outer_240_cannot_lose_an_existing_renewal_to_a_conversion(self):
        self.cfg['interval_seconds'] = 240
        self.tracked()
        self.rpc.now += 240
        self.busy()
        self.cycle().assert_called_once_with('rebalance_confirmation', 'observe(uint256)',
            (7,), 'rebalance_observation:7')
        self.assertEqual((self.f.duration, self.f.gap), (900, 300))

    def test_cold_and_not_due_windows_preserve_optional_queue_priority(self):
        self.busy()
        self.cycle().assert_called_once_with('rewards', 'inert-conversion', (), 'conversion')
        self.k.lp_rewards.enabled = False
        self.tracked()
        self.rpc.now += 239
        self.busy()
        self.cycle().assert_called_once_with('rewards', 'inert-conversion', (), 'conversion')

    def test_gap_boundaries_never_turn_expired_evidence_into_a_rebalance(self):
        self.tracked()
        original = self.rpc.now
        for elapsed in (240, 300, 301):
            self.rpc.now = original + elapsed
            self.k.state[CONFIRMATION_STATE]['7'].update(last_checked_at=original,
                next_check_at=original + 240, observed_at=original, execute_after=0)
            self.busy()
            with self.subTest(elapsed=elapsed):
                self.cycle().assert_called_once_with('rebalance_confirmation', 'observe(uint256)',
                    (7,), 'rebalance_observation:7')

    def test_confirmed_jitter_deadline_precedes_optional_work_with_fresh_guards(self):
        self.tracked()
        self.f.record = [self.f.identity, self.rpc.now - 1000, self.rpc.now, 1]
        self.rpc.now += 240
        self.f.record[2] = self.rpc.now
        with patch('keeper.monitor.secrets.randbelow', return_value=0):
            self.cycle()
        self.rpc.now += 60
        self.busy()
        self.cycle().assert_called_once_with('vault', 'rebalance(uint256,uint128,uint256)',
            (7, 1, self.rpc.now + 180), 'rebalance:7')

    def test_existing_reset_precedes_optional_work_and_does_not_renew_evidence(self):
        self.k.state[CONFIRMATION_RESETS] = {'7': True}
        self.busy()
        self.cycle().assert_called_once_with('rebalance_confirmation', 'resetObservation(uint256)',
            (7,), 'rebalance_reset:7')

    def test_pending_first_performs_no_priority_reads_or_cursor_writes(self):
        self.tracked()
        self.rpc.now += 301
        self.busy()
        before = copy.deepcopy(self.k.state)
        with patch.object(self.k, 'poll_pending', return_value=True), \
                patch.object(self.k, '_head', side_effect=AssertionError('pending first')), \
                patch.object(self.k, 'save') as save:
            self.cycle().assert_not_called()
        save.assert_not_called()
        self.assertEqual(before, self.k.state)

    def test_shared_authority_failure_blocks_priority_and_keeps_reset_truth(self):
        self.tracked()
        self.rpc.now += 240
        self.busy()
        original = self.k.view
        def revoked(name, signature, *args):
            return 0 if signature == 'keepers(address)' else original(name, signature, *args)
        with patch.object(self.k, 'view', side_effect=revoked), \
                patch.object(self.k, 'submit') as submit, self.assertRaises(RpcError):
            self.k.cycle()
        submit.assert_not_called()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])

    def test_multiple_due_buckets_use_earliest_deadline_and_one_serial_submission(self):
        self.tracked()
        first = copy.deepcopy(self.k.state[CONFIRMATION_STATE]['7'])
        self.k.state[CONFIRMATION_STATE]['8'] = dict(first,
            last_checked_at=first['last_checked_at'] - 60,
            next_check_at=first['next_check_at'] - 60,
            observed_at=first['observed_at'] - 60)
        self.rpc.now += 240
        self.busy()
        fields, tokens = self.k._bucket(7)
        def due(bucket, _fields, _now, **_):
            self.k._rebalance_reset_due = None
            self.k._rebalance_observation_due = bucket
            return False
        with patch.object(self.k, '_bucket', return_value=(fields, tokens)), \
                patch.object(self.k, '_rebalance_due', side_effect=due):
            self.cycle().assert_called_once_with('rebalance_confirmation', 'observe(uint256)',
                (8,), 'rebalance_observation:8')

    def test_blocked_priority_submission_is_not_repeated_in_the_same_cycle(self):
        self.tracked()
        self.rpc.now += 240
        with patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                patch.object(self.k, 'submit', return_value=False) as submit:
            self.k.cycle()
        observations = [call for call in submit.call_args_list if call.args[0] == 'rebalance_confirmation']
        self.assertEqual(1, len(observations))

    def test_failed_priority_schedule_save_stops_before_any_optional_submission(self):
        self.tracked()
        self.rpc.now += 240
        self.busy()
        self.k.save()
        before, disk = copy.deepcopy(self.k.state), self.k.path.read_bytes()
        with patch.object(self.k, 'save', side_effect=OSError('inert disk failure')), \
                patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                patch.object(self.k, 'submit') as submit, self.assertRaises(OSError):
            self.k.cycle()
        submit.assert_not_called()
        self.assertEqual((before, disk), (self.k.state, self.k.path.read_bytes()))

    def test_priority_clock_failure_invalidates_known_windows_before_optional_work(self):
        self.tracked()
        self.rpc.now += 240
        self.busy()
        head = self.k._head()
        with patch.object(self.k, '_head', side_effect=[head, RpcError('inert raw clock fault')]), \
                patch.object(self.k, 'submit') as submit, self.assertRaises(RpcError):
            self.k.cycle()
        submit.assert_not_called()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7', self.k.state[CONFIRMATION_STATE])

    def test_priority_clock_retreat_cannot_hide_behind_a_future_deadline(self):
        self.tracked()
        self.rpc.now -= 1
        self.busy()
        with patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                patch.object(self.k, 'submit') as submit, self.assertRaises(RpcError):
            self.k.cycle()
        submit.assert_not_called()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7', self.k.state[CONFIRMATION_STATE])

    def test_secondary_priority_head_retreat_is_a_global_raw_fault(self):
        self.tracked()
        self.rpc.now += 240
        self.busy()
        number, now = self.k._head()
        with patch.object(self.k, '_head', side_effect=[(number, now), (number, now - 1)]), \
                patch.object(self.k, 'submit') as submit, self.assertRaises(RpcError):
            self.k.cycle()
        submit.assert_not_called()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])

    def test_routing_fault_keeps_independent_harvest_and_does_not_reset_price_evidence(self):
        self.tracked()
        self.rpc.now += 240
        self.k.maintenance['harvest'] = True
        with patch.object(self.k, '_validate_lp_routing', side_effect=RpcError('inert router outage')):
            self.cycle().assert_called_once_with('vault', 'collectFees(uint256,uint256)',
                (7, self.rpc.now + 180), 'harvest:7')
        self.assertNotIn('7', self.k.state.get(CONFIRMATION_RESETS, {}))

    def main_sleep_count(self):
        path = self.k.path.with_name('inert-main-config.json')
        path.write_text(json.dumps(self.cfg))
        forced = 0
        def pulse(*, force=False):
            nonlocal forced
            if force:
                forced += 1
                if forced == 5:
                    raise _StopMain()
        watchdog = SimpleNamespace(enabled=False, pulse=pulse)
        with patch('sys.argv', ['keeper.monitor', '--config', str(path)]), \
                patch('keeper.monitor.signal.signal'), \
                patch('keeper.monitor.process_lock', return_value=contextlib.nullcontext()), \
                patch('keeper.monitor.ProgressWatchdog.from_environment', return_value=watchdog), \
                patch('keeper.monitor.Keeper', return_value=self.k), \
                patch.object(self.k, 'run_cycle', return_value=False), \
                patch('keeper.monitor.time.sleep') as sleep, self.assertRaises(_StopMain):
            main()
        return sleep.call_count

    def test_optional_degradation_keeps_telemetry_without_delaying_known_confirmation(self):
        self.tracked()
        self.k.cycle_failures = 2
        def blocked_optional():
            self.k.blocked_actions += 1
        with patch.object(self.k, 'cycle', side_effect=blocked_optional), \
                patch.object(self.k, '_observe_revert_cooldowns'), \
                patch.object(self.k, '_observe_execution_health'), \
                patch('keeper.monitor.observe_confirmation_health', return_value={'state': 'observed_this_cycle'}):
            self.assertFalse(self.k.run_cycle())
        health = json.loads(self.k.health_path.read_text())
        self.assertEqual(('degraded', 1, 3),
            (health['status'], health['blocked_actions'], health['consecutive_failures']))
        self.assertEqual(60, self.main_sleep_count())

    def test_global_rpc_failure_keeps_exponential_backoff_and_reset_safety(self):
        self.tracked()
        self.k.cycle_failures = 2
        with patch.object(self.k, 'cycle', side_effect=RpcError('inert global outage')):
            self.assertFalse(self.k.run_cycle())
        self.assertEqual(480, self.main_sleep_count())

    def test_nonce_reconciliation_retains_global_backoff_without_signing_or_spending(self):
        self.tracked()
        self.k.live = True
        for name in self.k.contracts:
            self.k.config['code_hashes'].setdefault(name, self.f.f.pin)
        self.k.state['next_nonce'] = 7
        before = copy.deepcopy(self.k.state)
        original = self.rpc.call
        def nonce_mismatch(method, params):
            return '0x0' if method == 'eth_getTransactionCount' else original(method, params)
        with patch.object(self.rpc, 'call', side_effect=nonce_mismatch), \
                patch.object(self.k, '_validate_checkpoint'), \
                patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                patch('keeper.monitor.subprocess.run') as signer, self.assertRaises(RpcError):
            self.k.submit('rebalance_confirmation', 'observe(uint256)', (7,), 'rebalance_observation:7')
        signer.assert_not_called()
        self.assertTrue(self.k._cycle_error)
        self.assertEqual(before, self.k.state)
        self.k.cycle_failures = 3
        self.assertEqual(480, self.main_sleep_count())

    def test_cold_and_historical_profiles_keep_existing_backoff(self):
        self.k.cycle_failures = 3
        self.assertEqual(480, self.main_sleep_count())
        self.tracked()
        self.k.rebalance_confirmation.version = 0
        self.assertEqual(480, self.main_sleep_count())

    def test_cli_rejects_ambiguous_config_before_keeper_construction(self):
        path = self.k.path.with_name('inert-ambiguous-config.json')
        path.write_text('{"chain_id":31337,"chain_id":1}')
        with patch('sys.argv', ['keeper.monitor', '--config', str(path), '--once']), \
                patch('keeper.monitor.signal.signal'), \
                patch('keeper.monitor.process_lock', return_value=contextlib.nullcontext()), \
                patch('keeper.monitor.ProgressWatchdog.from_environment',
                    return_value=SimpleNamespace(enabled=False, pulse=lambda **_: None)), \
                patch('keeper.monitor.Keeper', side_effect=RuntimeError('Ambiguous configuration reached construction')) as construct, \
                self.assertRaises(ValueError):
            main()
        construct.assert_not_called()


class KeeperConfirmationV2PriorityTests(unittest.TestCase):
    def test_reference_disagreement_prioritizes_clear_and_never_bypasses_policy(self):
        from tests_python.test_reference_confirmation_v2 import KeeperReferenceConfirmationV2Tests
        fixture = KeeperReferenceConfirmationV2Tests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        f, k = fixture.f, fixture.k
        f.k = k
        f.cycle()
        k._confirmation_seen_buckets.add(7)
        f.record = [f.identity, f.rpc.now, f.rpc.now, 1]
        f.rpc.now += 240
        fixture.reference = 0
        f.side = 0
        k.lp_rewards = SimpleNamespace(enabled=True, key='lp_conversion',
            scan_once=lambda: k.submit('rewards', 'inert-conversion', (), 'conversion'))
        k.state['conversion_turn'] = 0
        f.cycle().assert_called_once_with('rebalance_confirmation', 'resetObservation(uint256)',
            (7,), 'rebalance_reset:7')
        self.assertTrue(k.state[CONFIRMATION_RESETS]['7'])
        self.assertEqual((900, 300), (f.duration, f.gap))


if __name__ == '__main__':
    unittest.main()
