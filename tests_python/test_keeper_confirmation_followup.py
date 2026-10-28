"""Second-review confirmation incidents; synthetic RPC and no real signer."""
import copy
import unittest
from unittest.mock import patch

from keeper.monitor import CONFIRMATION_CLEARS, CONFIRMATION_RESETS, CONFIRMATION_STATE
from tests_python import test_keeper_rebalance_confirmation as fixtures
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class KeeperConfirmationFollowupTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.KeeperConfirmationTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.k,self.rpc=self.f.k,self.f.rpc
        self.k._confirmation_seen_buckets.add(7)

    def cycle(self):
        with patch('keeper.monitor.time.time',side_effect=lambda:self.rpc.now), \
                patch('keeper.monitor.secrets.randbelow',return_value=0), \
                patch.object(self.k,'submit',return_value=False) as submit:
            self.k.cycle()
        return submit

    def mature(self):
        self.f.record=[self.f.identity,self.rpc.now-900,self.rpc.now-100,1]
        self.cycle()
        self.assertTrue(self.k.state[CONFIRMATION_STATE]['7']['execute_after'])

    def raw_fault(self,signature,*args,result=None):
        original=self.rpc.call;data=calldata(signature,*args)
        def call(method,params):
            if method=='eth_call' and 'from' not in params[0] and params[0]['data']==data:
                if result is not None:return result
                raise RpcError('inert raw dependency outage')
            return original(method,params)
        return patch.object(self.rpc,'call',side_effect=call)

    def assert_reset(self):
        self.assertTrue(self.k.state.get(CONFIRMATION_RESETS,{}).get('7'))
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_STATE,{}))
        self.assertIsNone(self.k.state['pending'])

    def test_foreign_record_after_healthy_empty_clear_still_requires_reset(self):
        self.k.state[CONFIRMATION_CLEARS]={'7':dict(number=98,hash=fixtures.basic.H,
            timestamp=self.rpc.now-10,nonce=6,awaiting_healthy_read=True)}
        # No observation intent was persisted: e.g. gas refusal before signing.
        self.cycle().assert_called_once_with('rebalance_confirmation','observe(uint256)',(7,),
            'rebalance_observation:7')
        self.assertFalse(self.k.state[CONFIRMATION_CLEARS]['7']['awaiting_healthy_read'])
        self.rpc.now+=300;self.f.record=[self.f.identity,self.rpc.now-299,self.rpc.now,1]
        self.cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),
            'rebalance_reset:7')
        self.assert_reset()

    def test_raw_group_outage_discards_mature_jitter_before_recovery(self):
        self.mature()
        with self.raw_fault('group(uint256)',7):self.cycle().assert_not_called()
        self.assert_reset();self.rpc.now+=60
        self.cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),
            'rebalance_reset:7')

    def test_malformed_raw_group_requires_reset(self):
        self.mature()
        with self.raw_fault('group(uint256)',7,result='0x'):self.cycle().assert_not_called()
        self.assert_reset()

    def test_raw_pool_policy_outage_requires_reset(self):
        self.mature()
        with self.raw_fault('get(bytes32)',self.f.base.pool):self.cycle().assert_not_called()
        self.assert_reset()

    def test_malformed_raw_accounting_policy_requires_reset(self):
        self.mature()
        with self.raw_fault('accounting(bytes32)',self.f.base.pool,result='0x'):self.cycle().assert_not_called()
        self.assert_reset()

    def test_unrelated_share_inventory_fault_preserves_confirmation(self):
        self.mature();before=copy.deepcopy(self.k.state[CONFIRMATION_STATE])
        with self.raw_fault('bucketTotalShares(uint256)',7):self.cycle().assert_not_called()
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}))
        self.assertEqual(before,self.k.state[CONFIRMATION_STATE])

    def test_initial_access_faults_reset_only_known_confirmation_windows(self):
        self.mature();before=copy.deepcopy(self.k.state)
        original=self.k.view
        for signature in ('canonicalState()','paused()','preparationActive()','lpExitStarted()',
                'isSealed()','keepers(address)'):
            self.k.state=copy.deepcopy(before)
            def view(name,method,*args):
                if name=='access' and method==signature:raise RpcError('inert raw access outage')
                return original(name,method,*args)
            with self.subTest(signature=signature):
                with patch.object(self.k,'view',side_effect=view),self.assertRaises(RpcError):self.cycle()
                self.assert_reset();self.assertEqual({'7'},set(self.k.state[CONFIRMATION_RESETS]))

    def test_initial_scheduling_clock_fault_resets_known_windows(self):
        self.mature()
        with patch.object(self.k,'_head',side_effect=RpcError('inert scheduling clock outage')), \
                self.assertRaises(RpcError):self.cycle()
        self.assert_reset()

    def test_pending_recovery_fault_does_not_apply_global_raw_resets(self):
        self.mature();self.k.state['pending']={'key':'harvest:7'};before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'poll_pending',side_effect=RpcError('inert pending outage')), \
                patch.object(self.k,'canonical_state',side_effect=AssertionError('pending first')), \
                self.assertRaises(RpcError):self.cycle()
        self.assertEqual(before,self.k.state)


if __name__=='__main__':unittest.main()
