"""Used-signer checkpoint faults must not preserve sampled readiness; inert only."""
import copy
import unittest
from unittest.mock import patch

from keeper.monitor import CONFIRMATION_RESETS, CONFIRMATION_STATE
from tests_python import test_keeper_confirmation_followup as fixtures
from zzz_ops.rpc import RpcError


class KeeperCheckpointConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.KeeperConfirmationFollowupTests('runTest')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.k,self.rpc=self.f.k,self.f.rpc
        self.f.mature()
        self.k.state['next_nonce']=7
        self.k.state['receipt_anchor']={'number':98,'hash':fixtures.fixtures.basic.H,
            'timestamp':self.rpc.now-10,'nonce':6}
        self.k.save()

    def assert_reset(self):
        self.assertTrue(self.k.state.get(CONFIRMATION_RESETS,{}).get('7'))
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_STATE,{}))
        self.assertIsNone(self.k.state['pending'])

    def checkpoint_header(self,method,params):
        result=self.original(method,params)
        if method=='eth_getBlockByNumber' and params[0]=='0x62':
            return {**result,'timestamp':hex(self.rpc.now-10)}
        return result

    def test_no_pending_checkpoint_head_outage_resets_known_window(self):
        with patch.object(self.k,'_head',side_effect=RpcError('inert checkpoint clock outage')), \
                self.assertRaises(RpcError):self.f.cycle()
        self.assert_reset()

    def test_no_pending_checkpoint_header_outage_resets_known_window(self):
        self.original=self.rpc.call
        def call(method,params):
            if method=='eth_getBlockByNumber' and params[0]=='0x62':
                raise RpcError('inert checkpoint header outage')
            return self.checkpoint_header(method,params)
        with patch.object(self.rpc,'call',side_effect=call),self.assertRaises(RpcError):self.f.cycle()
        self.assert_reset()

    def test_no_pending_malformed_or_changed_checkpoint_resets_without_new_work(self):
        original_state=copy.deepcopy(self.k.state);self.original=self.rpc.call
        for mutation in ('missing','number','hash','timestamp'):
            self.k.state=copy.deepcopy(original_state)
            def call(method,params):
                result=self.checkpoint_header(method,params)
                if method=='eth_getBlockByNumber' and params[0]=='0x62':
                    if mutation=='missing':return None
                    return {**result,mutation:True if mutation=='number' else
                        '0x'+'cd'*32 if mutation=='hash' else hex(self.rpc.now-11)}
                return result
            with self.subTest(mutation=mutation),patch.object(self.rpc,'call',side_effect=call), \
                    patch.object(self.k,'submit') as submit,self.assertRaises(RpcError):self.k.cycle()
            submit.assert_not_called();self.assert_reset()

    def test_healthy_used_signer_checkpoint_preserves_window(self):
        self.original=self.rpc.call;before=copy.deepcopy(self.k.state[CONFIRMATION_STATE])
        with patch.object(self.rpc,'call',side_effect=self.checkpoint_header):self.f.cycle()
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}))
        self.assertEqual(before,self.k.state[CONFIRMATION_STATE])

    def test_unrelated_saved_pending_fault_keeps_original_recovery_isolation(self):
        self.k.state['pending']={'key':'harvest:7'};before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'_head',side_effect=RpcError('inert pending checkpoint outage')), \
                patch.object(self.k,'_mark_known_confirmation_resets',side_effect=AssertionError('pending first')) as reset, \
                self.assertRaises(RpcError):self.f.cycle()
        reset.assert_not_called();self.assertEqual(before,self.k.state)

    def test_related_saved_pending_fault_is_deferred_not_a_global_reset(self):
        from zzz_ops.abi import calldata
        self.k.state['pending']={'key':'rebalance_observation:7',
            'to':self.k.contracts['rebalance_confirmation'],'data':calldata('observe(uint256)',7)}
        before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'_head',side_effect=RpcError('inert related checkpoint outage')), \
                patch.object(self.k,'_mark_known_confirmation_resets',side_effect=AssertionError('pending first')) as reset, \
                self.assertRaises(RpcError):self.f.cycle()
        reset.assert_not_called();self.assertEqual(before,self.k.state)
        self.assertEqual({7},self.k._confirmation_recovery_interrupted)

    def test_historical_confirmation_zero_does_not_reset_or_probe_new_dependencies(self):
        self.k.rebalance_confirmation.version=0;before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'_head',side_effect=RpcError('inert legacy checkpoint outage')), \
                patch.object(self.k.rebalance_confirmation,'validate',side_effect=AssertionError('historical')) as validate, \
                self.assertRaises(RpcError):self.f.cycle()
        validate.assert_not_called();self.assertEqual(before,self.k.state)


if __name__=='__main__':unittest.main()
