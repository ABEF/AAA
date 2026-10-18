"""Canonical handoff locks all new keeper work while preserving receipt recovery."""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.ops import health_check, preflight
from tests_python import test_keeper as fixtures
from tests_python import test_keeper_ops as ops_fixtures
from tests_python import test_metadata_keeper as metadata_fixtures
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


def word(value): return '0x' + f'{value:064x}'


class KeeperCanonicalTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PoolKeeperTests('test_empty_inventory_submits_nothing')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.fixture.ids = [7]
        self.k, self.rpc = self.fixture.k, self.fixture.rpc
        self.original_call = self.rpc.call

    def override_state(self, response):
        def call(method, params):
            if method == 'eth_call' and params[0]['data'] == calldata('canonicalState()'):
                if isinstance(response, Exception): raise response
                return response
            return self.original_call(method, params)
        self.rpc.call = call

    def test_every_locked_state_stops_every_new_action_before_simulation(self):
        actions = (
            ('vault', 'rebalance(uint256,uint128,uint256)', (7,1,self.rpc.now+180)),
            ('compounder', 'compound(uint256,uint128,uint256)', (7,1,self.rpc.now+180)),
            ('buyback', 'execute(address,uint256,bytes32,uint256)', (fixtures.B,1,fixtures.H,self.rpc.now+180)),
            ('vault', 'collectFees(uint256,uint256)', (7,self.rpc.now+180)),
            ('fees', 'syncExternal(uint256)', (7,)),
            ('fees', 'bridgeRewards(uint256,address,bytes32)', (7,fixtures.B,fixtures.H)),
            ('nft', 'refreshMetadataRange(uint256,uint256)', (1,2)),
        )
        before = copy.deepcopy(self.k.state)
        for state in range(1,5):
            self.fixture.canonical_state = state
            for name, signature, args in actions:
                with self.subTest(state=state,action=name+signature), patch('keeper.monitor.subprocess.run') as signer:
                    self.assertFalse(self.k.submit(name,signature,args,'test'))
                    signer.assert_not_called()
        self.assertEqual(self.k.state,before)
        self.assertFalse(self.k.path.exists())
        self.assertFalse(any(method == 'eth_estimateGas' or method == 'eth_call' and 'from' in params[0]
                             for method,params in self.rpc.calls))

    def test_unknown_or_malformed_state_fails_closed(self):
        for response in ('0x','0x00',word(5),word(256),word(0)+word(0)[2:],None,True,RpcError('unsupported')):
            with self.subTest(response=response):
                self.override_state(response)
                with patch('keeper.monitor.subprocess.run') as signer, self.assertRaises(RpcError):
                    self.k.submit('fees','syncExternal(uint256)',(7,),'sync:7')
                signer.assert_not_called()
                self.assertIsNone(self.k.canonical_lifecycle)
                self.assertIsNone(self.k.state['pending'])

    def test_locked_cycle_never_discovers_pools_or_metadata(self):
        for state in range(1,5):
            self.fixture.canonical_state = state
            with self.subTest(state=state), patch.object(self.k,'_bucket_batch') as buckets, \
                    patch.object(self.k,'_refresh_metadata') as metadata, patch.object(self.k,'submit') as submit:
                self.k.cycle()
                buckets.assert_not_called(); metadata.assert_not_called(); submit.assert_not_called()

    def test_lock_during_gas_estimation_stops_before_dry_run_or_intent(self):
        def call(method,params):
            result = self.original_call(method,params)
            if method == 'eth_estimateGas': self.fixture.canonical_state = 1
            return result
        self.rpc.call = call
        with patch('keeper.monitor.subprocess.run') as signer, patch('keeper.monitor.log') as logger:
            self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7'))
        signer.assert_not_called()
        self.assertNotIn('dry_run',[entry.args[0] for entry in logger.call_args_list])
        self.assertIsNone(self.k.state['pending'])

    def test_lock_at_last_balance_read_prevents_durable_intent_and_signing(self):
        self.fixture.enable_test_signer()
        before = copy.deepcopy(self.k.state)
        def call(method,params):
            result = self.original_call(method,params)
            if method == 'eth_getBalance': self.fixture.canonical_state = 3
            return result
        self.rpc.call = call
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7'))
        signer.assert_not_called(); self.assertEqual(self.k.state,before); self.assertFalse(self.k.path.exists())

    def test_missing_getter_at_final_read_prevents_intent(self):
        self.fixture.enable_test_signer()
        reads = 0
        def call(method,params):
            nonlocal reads
            if method == 'eth_call' and params[0]['data'] == calldata('canonicalState()'):
                reads += 1
                if reads == 3: return '0x'
            return self.original_call(method,params)
        self.rpc.call = call
        with patch('keeper.monitor.subprocess.run') as signer, self.assertRaises(RpcError):
            self.k.submit('fees','syncExternal(uint256)',(7,),'sync:7')
        signer.assert_not_called(); self.assertEqual(reads,3)
        self.assertIsNone(self.k.state['pending']); self.assertIsNone(self.k.canonical_lifecycle)

    def test_pending_reconciliation_does_not_depend_on_lifecycle_getter(self):
        self.k.state['pending'] = {'hash':None,'nonce':7,'key':'harvest:7'}
        before = copy.deepcopy(self.k.state)
        with patch.object(self.k,'canonical_state',side_effect=AssertionError('reconcile first')):
            self.k.cycle()
        self.assertEqual(self.k.state,before)

    def test_confirmed_receipt_is_saved_before_unavailable_lifecycle_getter(self):
        fixture = fixtures.KeeperTests('test_success_accounts_actual_cost')
        self.addCleanup(fixture.doCleanups); fixture.setUp(); fixture.receipt()
        with patch.object(fixture.k,'canonical_state',side_effect=RpcError('unsupported')):
            self.assertFalse(fixture.k.run_cycle())
        self.assertIsNone(fixture.k.state['pending'])
        self.assertEqual(sum(fixture.k.state['spent'].values()),215)
        self.assertIsNone(json.loads(fixture.k.path.read_text())['pending'])

    def test_lifecycle_observation_logs_transitions_only(self):
        with patch('keeper.monitor.log') as logger:
            self.k.canonical_state(); self.k.canonical_state()
            logger.assert_not_called()
            self.fixture.canonical_state = 1
            self.k.canonical_state(); self.k.canonical_state()
            logger.assert_called_once_with('canonical_lifecycle_observed',state=1,name='frozen')
            self.fixture.canonical_state = 0
            self.k.canonical_state(); self.k.canonical_state()
            self.assertEqual(logger.call_count,2)
            logger.assert_called_with('canonical_lifecycle_observed',state=0,name='operating')

    def test_abort_restores_maintenance_without_reinitializing_recovery_state(self):
        self.fixture.canonical_state = 1
        self.fixture.invoke().assert_not_called()
        self.fixture.canonical_state = 0
        self.fixture.invoke().assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'rebalance:7')

    def test_locked_observation_is_explicit_in_health_without_counting_a_keeper_crash(self):
        self.fixture.canonical_state = 3
        self.assertTrue(self.k.run_cycle())
        health = json.loads(self.k.health_path.read_text())
        self.assertEqual(health['status'],'canonical_locked'); self.assertEqual(health['canonical_state'],3)
        self.assertEqual(health['consecutive_failures'],0)
        report = health_check(self.fixture.cfg,allow_dry_run=True)
        self.assertFalse(report['ok']); self.assertIn('canonical_lifecycle_locked',report['reasons'])
        self.assertNotIn('preparation_state_unknown',report['reasons'])

    def test_missing_lifecycle_health_field_cannot_assert_compatibility(self):
        self.k.run_cycle()
        health = json.loads(self.k.health_path.read_text()); health.pop('canonical_state')
        self.k.health_path.write_text(json.dumps(health))
        self.assertIn('canonical_state_unknown',health_check(self.fixture.cfg,allow_dry_run=True)['reasons'])

    def test_frozen_metadata_cycle_never_scans_or_submits(self):
        fixture = metadata_fixtures.MetadataKeeperTests('test_dry_run_does_not_mark_notified_or_sign')
        self.addCleanup(fixture.doCleanups); fixture.setUp(); fixture.rpc.canonical_state = 1
        with patch.object(fixture.keeper,'_refresh_metadata') as refresh, patch.object(fixture.keeper,'submit') as submit:
            fixture.keeper.cycle()
        refresh.assert_not_called(); submit.assert_not_called()

    def test_preflight_reports_locked_lifecycle_without_writes_or_signing(self):
        fixture = ops_fixtures.OpsTests('test_preflight_is_read_only_and_never_calls_signer')
        self.addCleanup(fixture.doCleanups); fixture.setUp()
        original = fixture.rpc.call
        def call(method,params):
            if method == 'eth_call' and params[0]['data'] == calldata('canonicalState()'): return word(2)
            return original(method,params)
        fixture.rpc.call = call; before = fixture.k.path.read_bytes()
        with patch('keeper.monitor.subprocess.run') as signer: result = preflight(fixture.cfg,rpc=fixture.rpc)
        signer.assert_not_called(); self.assertEqual(fixture.k.path.read_bytes(),before)
        self.assertEqual(result['reasons'],['canonical_lifecycle_locked']); self.assertEqual(result['canonical_state'],2)


if __name__ == '__main__': unittest.main()
