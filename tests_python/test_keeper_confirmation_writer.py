"""Exercise the real heartbeat path with policy-only inert chain observations."""
import json
import unittest
from unittest.mock import patch

from keeper.health import execution_reasons
from tests_python import test_keeper_confirmation_health as fixtures
from zzz_ops.abi import calldata


class KeeperConfirmationWriterTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.KeeperConfirmationHealthTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.k,self.rpc=self.f.k,self.f.rpc
        self.k.canonical_lifecycle=0;self.k.principal_exit_started=False;self.k.preparing=False

    def run_writer(self):
        before=self.k.path.read_bytes()
        with patch.object(self.k,'cycle'),patch.object(self.k,'_observe_revert_cooldowns'), \
                patch.object(self.k,'_observe_execution_health'), \
                patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer:
            result=self.k.run_cycle()
        signer.assert_not_called();self.assertEqual(before,self.k.path.read_bytes())
        return result,json.loads(self.k.health_path.read_text())

    def test_cooldown_without_compounding_still_exports_actual_budget_binding(self):
        ok,data=self.run_writer();self.assertTrue(ok)
        self.assertEqual('dry_run_v2',data['status'])
        observed=data['rebalance_confirmation_health']['policy']['last_observed']
        self.assertEqual(self.f.f.budget,observed['validated_bindings']['vault_budget'])
        self.assertEqual([],execution_reasons(data,self.f.cfg,now=self.rpc.now,max_age=1800))

    def test_failed_policy_cannot_refresh_last_healthy_time_or_claim_success(self):
        self.k.last_success_at='2000-01-01T00:00:00+00:00';self.k.cycle_failures=2
        self.f.f.bad[self.f.f.budget,calldata('REBALANCE_CONFIRMATION_VERSION()')]='0x'+f'{0:064x}'
        ok,data=self.run_writer();self.assertFalse(ok);self.assertEqual('degraded',data['status'])
        self.assertEqual('2000-01-01T00:00:00+00:00',data['last_success_at'])
        self.assertEqual(3,data['consecutive_failures'])
        self.assertEqual('unavailable',data['rebalance_confirmation_health']['policy']['state'])

    def test_saved_pending_recovery_never_adds_new_policy_dependency(self):
        self.k.state['pending']={'key':'saved'};self.k.save()
        with patch('keeper.rebalance_confirmation.RebalanceConfirmation.validate',side_effect=AssertionError('Recovery first')) as validate:
            _ok,data=self.run_writer()
        validate.assert_not_called()
        self.assertEqual('pending_recovery',data['rebalance_confirmation_health']['policy']['state'])

    def test_intentional_stop_is_reported_but_cycle_work_is_not_cancelled(self):
        self.f.f.gap=0
        ok,data=self.run_writer();self.assertFalse(ok)
        self.assertEqual('stopped',data['rebalance_confirmation_health']['policy']['state'])
        self.assertEqual('degraded',data['status'])

    def test_post_exit_stop_does_not_mark_remaining_royalty_operations_unhealthy(self):
        self.f.f.gap=0;self.k.principal_exit_started=True
        ok,data=self.run_writer();self.assertTrue(ok)
        self.assertEqual('dry_run_v2',data['status'])
        self.assertEqual([],execution_reasons(data,self.f.cfg,now=self.rpc.now,max_age=1800))


if __name__=='__main__':unittest.main()
