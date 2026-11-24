"""NEW recovery/writer cadence composition; inert inclusion, no network/signing.

Uses existing constructor helpers only. No existing test body is executed. The
real poll_pending validates a canonical signed-fee transcript and publishes the
exact nonce/spend checkpoint; route-observer seams are explicit, not F6 runtime.
"""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper_execution_telemetry as quality_fixtures
from tests_python.test_keeper_fees import InclusionTranscript
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


class KeeperRecoveryRefreshTests(unittest.TestCase):
    def setUp(self):
        self.f = quality_fixtures.KeeperExecutionTelemetryTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        cfg = copy.deepcopy(self.f.cfg)
        cfg.update(state_path=str(Path(self.tmp.name) / 'state.json'),
                   health_path=str(Path(self.tmp.name) / 'health.json'),
                   lock_path=str(Path(self.tmp.name) / 'keeper.lock'),
                   confirmations=2, receipt_fee_policy='included')
        self.rpc = InclusionTranscript()
        self.k = Keeper(cfg, rpc=self.rpc)
        self.k.canonical_lifecycle = 0
        self.k.preparing = False
        self.k.principal_exit_started = False
        self.k.last_success_at = '2000-01-01T00:00:00+00:00'
        self.rpc.tx.update(**{'from': self.k.sender, 'to': self.k.contracts['vault'],
                            'chainId': hex(self.k.chain), 'value': '0x0',
                            'input': calldata('collectFees(uint256,uint256)', 1, self.rpc.now + 180)})
        self.rpc.receipt.update(**{'from': self.k.sender, 'to': self.k.contracts['vault']})
        topic = '0x' + keccak256(b'FeesCollected(uint256,uint256,uint256)').hex()
        self.rpc.receipt['logs'] = [{
            'address': self.k.contracts['vault'], 'topics': [topic, '0x' + f'{1:064x}'],
            'data': '0x' + '0' * 128, 'blockNumber': '0x63',
            'blockHash': self.rpc.receipt['blockHash'],
            'transactionHash': self.rpc.receipt['transactionHash'],
            'transactionIndex': '0x0', 'logIndex': '0x0', 'removed': False}]
        self.k.state.update(next_nonce=7, pending={
            'key': 'harvest:1', 'nonce': 7, 'to': self.k.contracts['vault'],
            'data': self.rpc.tx['input'], 'value': 0, 'day': '2026-10-14',
            'hash': self.rpc.tx['hash'], 'fee_review': {
                'schema': 1, 'gas_limit': 256, 'max_fee_per_gas': 10,
                'l1_fee_allowance_wei': 0, 'maximum_cost_wei': 2560,
                'receipt_fee_policy': 'included'}})
        self.k.save()

    def run_recovery(self, body=None):
        # Deliberately isolate writer/cadence coordination around REAL receipt
        # reconciliation. The broader ordinary cycle and live Cast are the
        # separate Ubuntu partition, not hidden inside this unit transcript.
        with patch.object(self.k, 'cycle', side_effect=body or self.k.poll_pending), \
                patch.object(self.k, '_observe_execution_health',
                             side_effect=AssertionError('Recovery must remain independent')) as observer, \
                patch('keeper.monitor.observe_confirmation_health',
                      side_effect=AssertionError('Recovery must remain independent')) as confirmation, \
                patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                patch('keeper.monitor.log'), patch('keeper.monitor.run_cast') as signer:
            result = self.k.run_cycle()
        observer.assert_not_called()
        confirmation.assert_not_called()
        signer.assert_not_called()
        return result, json.loads(self.k.health_path.read_bytes())

    def assert_paid_once(self):
        day = dt.datetime.fromtimestamp(self.rpc.now, dt.timezone.utc).date().isoformat()
        # Signed cap10, canonical base3 + priority2,100 gas; reported99 is not cost.
        self.assertIsNone(self.k.state['pending'])
        self.assertEqual(8, self.k.state['next_nonce'])
        self.assertEqual({day: 500}, self.k.state['spent'])
        self.assertEqual(self.k.state, json.loads(self.k.path.read_bytes()))

    def test_paid_recovery_keeps_health_unfresh_but_uses_normal_refresh_cadence(self):
        ok, health = self.run_recovery()
        self.assertFalse(ok)
        self.assert_paid_once()
        self.assertEqual('degraded', health['status'])
        self.assertEqual('pending_recovery', health['lp_execution_health']['state'])
        self.assertEqual('2000-01-01T00:00:00+00:00', health['last_success_at'])
        self.assertEqual(240, self.k.poll_delay(240))
        self.assertNotIn('_recovery_refresh_due', self.k.state)

    def test_recovery_rpc_failure_retains_intent_and_global_backoff(self):
        before = self.k.path.read_bytes()
        with patch.object(self.rpc, 'call', side_effect=RpcError('fixture recovery outage')):
            ok, health = self.run_recovery()
        self.assertFalse(ok)
        self.assertEqual('error', health['status'])
        self.assertEqual(before, self.k.path.read_bytes())
        self.assertIsNotNone(self.k.state['pending'])
        self.assertEqual(480, self.k.poll_delay(240))

    def test_unmined_and_hashless_intents_keep_existing_wait_backoff(self):
        for kind in ('unmined', 'hashless'):
            with self.subTest(kind=kind):
                self.rpc.receipt = None
                if kind == 'hashless':
                    self.k.state['pending']['hash'] = None
                    self.k.save()
                self.k.cycle_failures = 2
                before = self.k.path.read_bytes()
                ok, health = self.run_recovery()
                self.assertTrue(ok)
                self.assertTrue(health['pending'])
                self.assertEqual(before, self.k.path.read_bytes())
                self.assertEqual(960, self.k.poll_delay(240))

    def test_paid_revert_keeps_action_cooldown_and_failure_backoff(self):
        self.rpc.receipt['status'] = '0x0'
        ok, health = self.run_recovery()
        self.assertFalse(ok)
        self.assert_paid_once()
        self.assertEqual('degraded', health['status'])
        self.assertNotIn('harvest:1', self.k.state['last'])
        self.assertEqual(self.rpc.now + 3600, self.k.state['retry_after']['harvest:1'])
        self.assertEqual(480, self.k.poll_delay(240))

    def test_rpc_failure_after_paid_recovery_still_uses_global_backoff(self):
        def body():
            self.k.poll_pending()
            raise RpcError('fixture later cycle outage')
        ok, health = self.run_recovery(body)
        self.assertFalse(ok)
        self.assert_paid_once()
        self.assertEqual('error', health['status'])
        self.assertEqual(480, self.k.poll_delay(240))

    def test_unavailable_component_after_recovery_is_not_a_refresh_only_delay(self):
        def body():
            self.k.poll_pending()
            self.k.lp_execution_health['state'] = 'unavailable'
        ok, health = self.run_recovery(body)
        self.assertFalse(ok)
        self.assert_paid_once()
        self.assertEqual('degraded', health['status'])
        self.assertEqual('unavailable', health['lp_execution_health']['state'])
        self.assertEqual(480, self.k.poll_delay(240))

    def test_refresh_exception_resets_and_only_fresh_observation_restores_health(self):
        self.run_recovery()
        self.assertEqual(240, self.k.poll_delay(240))
        before = self.k.path.read_bytes()
        def unavailable():
            self.k.lp_execution_health['state'] = 'unavailable'
        with patch.object(self.k, 'cycle'), patch.object(self.k, '_observe_execution_health', side_effect=unavailable), \
                patch('keeper.monitor.time.time', return_value=self.rpc.now), patch('keeper.monitor.log'), \
                patch('keeper.monitor.run_cast') as signer:
            self.assertFalse(self.k.run_cycle())
        signer.assert_not_called()
        self.assertEqual(before, self.k.path.read_bytes())
        self.assertEqual(960, self.k.poll_delay(240))
        def observed():
            self.k.lp_execution_health['state'] = 'observed_this_cycle'
        with patch.object(self.k, 'cycle'), patch.object(self.k, '_observe_execution_health', side_effect=observed), \
                patch('keeper.monitor.time.time', return_value=self.rpc.now), patch('keeper.monitor.log'), \
                patch('keeper.monitor.run_cast') as signer:
            self.assertTrue(self.k.run_cycle())
        signer.assert_not_called()
        final = json.loads(self.k.health_path.read_bytes())
        self.assertEqual('dry_run_v2', final['status'])
        self.assertNotEqual('2000-01-01T00:00:00+00:00', final['last_success_at'])
        self.assertEqual(240, self.k.poll_delay(240))
        self.assertEqual(before, self.k.path.read_bytes())


    def confirmation_deadline(self, *, next_in=20, execute_in=0):
        # Construct a supported confirmation3/portfolio policy using the existing
        # inert policy factory. Only constructors run, never its old test bodies.
        from tests_python.test_keeper_policy_v6 import PolicyRPC
        from keeper.rebalance_confirmation import PORTFOLIO_STATE_NAMESPACE
        policy = PolicyRPC(Path(self.tmp.name) / 'deadline-state.json')
        cfg = copy.deepcopy(policy.cfg)
        cfg.update(interval_seconds=240, confirmations=2, receipt_fee_policy='included',
                   state_path=str(Path(self.tmp.name) / 'deadline-state.json'),
                   health_path=str(Path(self.tmp.name) / 'deadline-health.json'),
                   lock_path=str(Path(self.tmp.name) / 'deadline.lock'))
        pending = copy.deepcopy(self.k.state['pending'])
        self.k = Keeper(cfg, rpc=self.rpc)
        self.k.canonical_lifecycle = 0
        self.k.preparing = False
        self.k.principal_exit_started = False
        self.k.last_success_at = '2000-01-01T00:00:00+00:00'
        pending.update(to=self.k.contracts['vault'])
        self.rpc.tx.update(**{'from': self.k.sender, 'to': pending['to'],
                            'chainId': hex(self.k.chain)})
        self.rpc.receipt.update(**{'from': self.k.sender, 'to': pending['to']})
        self.rpc.receipt['logs'][0]['address'] = pending['to']
        self.k.state.update(next_nonce=7, pending=pending)
        self.k.state[PORTFOLIO_STATE_NAMESPACE] = {'1': {
            'identity': '0x' + '12' * 32, 'observed_at': self.rpc.now - 600,
            'last_checked_at': self.rpc.now, 'next_check_at': self.rpc.now + next_in,
            # Ten seconds remaining models an already-drawn lawful jitter,
            # not a change to the60-second minimum new draw.
            'execute_after': self.rpc.now + execute_in if execute_in else 0}}
        self.k.save()
        ok, health = self.run_recovery()
        self.assertFalse(ok)
        self.assert_paid_once()
        self.assertEqual('degraded', health['status'])
        self.assertEqual('pending_recovery', health['lp_execution_health']['state'])
        self.assertEqual('pending_recovery', health['rebalance_confirmation_health']['policy']['state'])
        self.assertIsNotNone(self.k._poll_clock)
        before = self.k.path.read_bytes()
        with patch('keeper.monitor.time.monotonic', return_value=self.k._poll_clock[1]), \
                patch('keeper.monitor.secrets.randbelow') as random:
            delay = self.k.poll_delay(240)
        random.assert_not_called()
        self.assertEqual(before, self.k.path.read_bytes())
        return delay

    def test_paid_recovery_preserves_earlier_sample_deadline(self):
        self.assertEqual(20, self.confirmation_deadline(next_in=20))

    def test_paid_recovery_preserves_earlier_existing_jitter(self):
        self.assertEqual(10, self.confirmation_deadline(next_in=240, execute_in=10))

    def test_paid_recovery_preserves_bounded_overdue_retry(self):
        self.assertEqual(60, self.confirmation_deadline(next_in=-1))


if __name__ == '__main__':
    unittest.main()
