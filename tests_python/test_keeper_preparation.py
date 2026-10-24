"""Preparation defers new upkeep while recovery and funded drains remain usable."""
import copy
import json
import subprocess
import unittest
from unittest.mock import patch

from keeper.ops import health_check, preflight
from tests_python import test_keeper as fixtures
from tests_python import test_keeper_ops as ops_fixtures
from tests_python import test_metadata_keeper as metadata_fixtures
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


def word(value):
    return '0x'+f'{value:064x}'


class KeeperPreparationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PoolKeeperTests('test_empty_inventory_submits_nothing')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.fixture.ids = [7]
        self.k = self.fixture.k
        self.rpc = self.fixture.rpc
        self.original_call = self.rpc.call

    def override_flag(self, response):
        def call(method, params):
            if method == 'eth_call' and params[0]['data'] == calldata('preparationActive()'):
                if isinstance(response, Exception): raise response
                return response
            return self.original_call(method, params)
        self.rpc.call = call

    def test_preparing_skips_rebalance_compound_buyback_and_keeps_healthy_observation(self):
        self.fixture.preparing = True
        self.fixture.reserves[fixtures.C] = 100
        self.k.maintenance = {'harvest':False}
        self.k.config['buybacks'] = [{'token':fixtures.B,'amount':1,'pool_id':fixtures.H}]
        with patch.object(self.k, 'submit', return_value=True) as submit:
            self.assertTrue(self.k.run_cycle())
        submit.assert_not_called()
        selectors = [params[0]['data'][:10] for method,params in self.rpc.calls if method == 'eth_call']
        for signature,args in (('needsRebalance(uint256)',(7,)),
                               ('compoundBalance(uint256,address)',(7,fixtures.B)),
                               ('buybackBalance(address)',(fixtures.B,))):
            self.assertNotIn(calldata(signature,*args)[:10],selectors)
        health = json.loads(self.k.health_path.read_text())
        self.assertTrue(health['preparation_active'])
        self.assertEqual(health['consecutive_failures'],0)
        self.assertTrue(health_check(self.fixture.cfg,allow_dry_run=True)['ok'])

    def test_preparing_keeps_harvest_available(self):
        self.fixture.preparing = True
        submit = self.fixture.invoke()
        submit.assert_called_once_with('vault','collectFees(uint256,uint256)',
                                       (7,self.rpc.now+180),'harvest:7')

    def test_preparing_keeps_funded_inbox_settlement_available(self):
        self.fixture.preparing = True
        self.fixture.inbox = int(fixtures.A,16)
        self.fixture.inbox_pending = [100,0]
        self.fixture.invoke().assert_called_once_with('fees','syncExternal(uint256)',(7,),'external_rewards:7')

    def test_preparing_refuses_retired_reward_scheduling_without_sending(self):
        self.fixture.preparing = True
        self.fixture.group_words[7] = 2
        self.k.maintenance = {'reward_routes':[{'token':fixtures.B,'minimum_units':1,'route_id':fixtures.H}]}
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaisesRegex(ValueError,'retired'): self.fixture.invoke()
            signer.assert_not_called()
        self.assertIsNone(self.k.state['pending'])

    def test_unknown_or_malformed_preparation_abi_never_reaches_simulation_or_signer(self):
        for response in ('0x','0x00',word(2),word(0)+word(0)[2:],None,RpcError('unknown selector')):
            with self.subTest(response=response):
                self.override_flag(response)
                with patch('keeper.monitor.subprocess.run') as signer:
                    with self.assertRaises(RpcError):
                        self.k.submit('vault','rebalance(uint256,uint128,uint256)',(7,1,self.rpc.now+180),'rebalance:7')
                signer.assert_not_called()
                self.assertIsNone(self.k.state['pending'])
        self.assertFalse(any(method == 'eth_estimateGas' for method,_ in self.rpc.calls))

    def test_all_new_upkeep_selectors_are_deferred_before_simulation(self):
        self.fixture.preparing = True
        tasks = (('vault','rebalance(uint256,uint128,uint256)',(7,1,self.rpc.now+180)),
                 ('compounder','compound(uint256,uint128,uint256)',(7,1,self.rpc.now+180)),
                 ('buyback','execute(address,uint256,bytes32,uint256)',(fixtures.B,1,fixtures.H,self.rpc.now+180)))
        for name,signature,args in tasks:
            with self.subTest(name=name),patch('keeper.monitor.subprocess.run') as signer:
                self.assertFalse(self.k.submit(name,signature,args,name))
                signer.assert_not_called()
        self.assertFalse(any(method == 'eth_estimateGas' for method,_ in self.rpc.calls))
        self.assertIsNone(self.k.state['pending'])

    def test_preparation_start_during_last_balance_read_prevents_durable_intent(self):
        self.fixture.enable_test_signer()
        before = copy.deepcopy(self.k.state)
        def call(method, params):
            result = self.original_call(method, params)
            if method == 'eth_getBalance': self.fixture.preparing = True
            return result
        self.rpc.call = call
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.submit('vault','rebalance(uint256,uint128,uint256)',
                                          (7,1,self.rpc.now+180),'rebalance:7'))
        signer.assert_not_called()
        self.assertEqual(self.k.state,before)
        self.assertFalse(self.k.path.exists())
        self.assertTrue(self.k.preparing)

    def test_preparation_unknown_at_final_read_prevents_durable_intent(self):
        self.fixture.enable_test_signer()
        reads = 0
        def call(method, params):
            nonlocal reads
            if method == 'eth_call' and params[0]['data'] == calldata('preparationActive()'):
                reads += 1
                if reads == 3: return '0x'
            return self.original_call(method, params)
        self.rpc.call = call
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(RpcError):
                self.k.submit('vault','rebalance(uint256,uint128,uint256)',(7,1,self.rpc.now+180),'rebalance:7')
        signer.assert_not_called()
        self.assertEqual(reads,3)
        self.assertIsNone(self.k.state['pending'])
        self.assertFalse(self.k.path.exists())

    def test_harvest_can_use_actual_submission_path_during_preparation(self):
        self.fixture.preparing = True
        self.fixture.enable_test_signer()
        with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,fixtures.H,'')) as signer:
            self.assertTrue(self.k.submit('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7'))
        signer.assert_called_once()
        self.assertEqual(self.k.state['pending']['hash'],fixtures.H)
        self.assertEqual(self.k.state['pending']['key'],'harvest:7')

    def test_pending_recovery_is_not_blocked_by_unavailable_preparation_getter(self):
        self.override_flag(RpcError('unsupported getter'))
        self.k.state['pending'] = {'hash':None,'nonce':7,'key':'rebalance:7'}
        before = copy.deepcopy(self.k.state)
        with patch.object(self.k,'preparation_active',side_effect=AssertionError('must reconcile first')):
            self.k.cycle()
        self.assertEqual(self.k.state,before)

    def test_preparation_observation_logs_only_transitions(self):
        self.fixture.preparing = True
        with patch('keeper.monitor.log') as log:
            self.k.preparation_active(); self.k.preparation_active(); self.k.preparation_active()
            log.assert_called_once_with('canonical_preparation_observed',active=True)
            self.fixture.preparing = False
            self.k.preparation_active(); self.k.preparation_active()
            self.assertEqual(log.call_count,2)
            log.assert_called_with('canonical_preparation_observed',active=False)

    def test_preparation_cancellation_restores_current_maintenance(self):
        self.fixture.preparing = True
        self.k.maintenance = {'harvest':False}
        self.fixture.invoke().assert_not_called()
        self.fixture.preparing = False
        self.fixture.invoke().assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
                                                    (7,1,self.rpc.now+180),'rebalance:7')

    def test_metadata_refresh_remains_available_during_preparation(self):
        fixture = metadata_fixtures.MetadataKeeperTests('test_dry_run_does_not_mark_notified_or_sign')
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        fixture.rpc.preparing = True
        with patch.object(fixture.keeper,'submit',return_value=True) as submit:
            fixture.keeper.cycle()
        self.assertEqual(submit.call_count,1)
        self.assertEqual(submit.call_args.args[:2],('nft','refreshMetadataRange(uint256,uint256)'))

    def test_preflight_identifies_intentional_restriction_without_changing_state(self):
        fixture = ops_fixtures.OpsTests('test_preflight_is_read_only_and_never_calls_signer')
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        original = fixture.rpc.call
        def call(method, params):
            if method == 'eth_call' and params[0]['data'] == calldata('preparationActive()'): return word(1)
            return original(method, params)
        fixture.rpc.call = call
        before = fixture.k.path.read_bytes()
        with patch('keeper.monitor.subprocess.run') as signer:
            report = preflight(fixture.cfg,rpc=fixture.rpc)
        signer.assert_not_called()
        self.assertEqual(report['reasons'],['canonical_preparation_active'])
        self.assertTrue(report['preparation_active'])
        self.assertEqual(fixture.k.path.read_bytes(),before)


if __name__ == '__main__':
    unittest.main()
