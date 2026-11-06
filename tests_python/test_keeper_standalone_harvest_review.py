"""Standalone harvest timing and canonical recovery; inert RPC/temp journals only."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_hourly_harvest as hourly
from tests_python import test_keeper_harvest_coalescing as coalescing
from tests_python.test_keeper_policy_v6 import PolicyRPC
from tests_python.test_keeper_portfolio_policy import PortfolioRPC
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class StandaloneHarvestTimingTests(unittest.TestCase):
    def setUp(self):
        self.f=hourly.HourlyHarvestTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.k,self.rpc=self.f.k,self.f.fixture.rpc
        self.k.state['last']['harvest:7']=self.rpc.now-3600

    def cycle(self):
        with patch('keeper.monitor.time.time',side_effect=lambda:self.rpc.now), \
                patch.object(self.k,'submit',return_value=True) as submit:
            self.k.cycle()
        return submit

    def test_slow_successful_maintenance_prepares_fresh_harvest_deadline(self):
        original=self.k._rebalance_due
        def slow(*args):
            result=original(*args);self.rpc.now+=240;return result
        with patch.object(self.k,'_rebalance_due',side_effect=slow):submit=self.cycle()
        submit.assert_called_once_with('vault','collectFees(uint256,uint256)',
            (7,self.rpc.now+180),'harvest:7')
        self.assertIsNone(self.k.state['pending']);self.assertEqual({},self.k.state['spent'])

    def test_failed_final_head_does_not_submit_an_old_deadline(self):
        original=self.k._rebalance_due
        def slow(*args):
            result=original(*args)
            self.k._head=lambda:(_ for _ in ()).throw(RpcError('inert harvest head unavailable'))
            return result
        with patch.object(self.k,'_rebalance_due',side_effect=slow):submit=self.cycle()
        submit.assert_not_called();self.assertIsNone(self.k.state['pending'])
        self.assertEqual({},self.k.state['spent']);self.assertEqual(1,self.k.skipped_buckets)

    def test_no_extra_harvest_head_when_not_due_or_disabled(self):
        for disabled in (False,True):
            with self.subTest(disabled=disabled):
                self.k.maintenance['harvest']=not disabled
                self.k.state['last']['harvest:7']=self.rpc.now
                original=self.k._head
                with patch.object(self.k,'_head',wraps=original) as head:submit=self.cycle()
                before=head.call_count
                self.k.state['last']['harvest:7']=self.rpc.now-3600
                with patch.object(self.k,'_head',wraps=original) as head:self.cycle()
                self.assertEqual(before+(0 if disabled else 1),head.call_count)
                submit.assert_not_called()


class StandaloneHarvestRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f=coalescing.KeeperHarvestCoalescingTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.k,self.rpc=self.f.k,self.f.rpc
        self.prepare()

    def prepare(self, *, key='harvest:1',bucket=1,target=None,value=0,data=None):
        pending=self.k.state['pending']
        pending.update(key=key,to=target or self.k.contracts['vault'],
            data=data or calldata('collectFees(uint256,uint256)',bucket,self.rpc.now+180),value=value)
        pending['fee_review']['maximum_cost_wei']=2560+value
        self.rpc.tx.update(to=pending['to'],input=pending['data'],value=hex(value))
        self.rpc.receipt.update(to=pending['to'],logs=[self.event(bucket)])
        self.k.save()

    def event(self,*args,**kwargs):
        self.f.k=self.k
        return self.f.event(*args,**kwargs)

    def recover(self):
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.poll_pending())
        signer.assert_not_called();self.assertIsNone(self.k.state['pending'])
        self.assertEqual(8,self.k.state['next_nonce'])
        self.assertEqual(500+int(self.rpc.tx['value'],16),sum(self.k.state['spent'].values()))
        self.assertEqual(self.k.state,json.loads(self.k.path.read_bytes()))

    def test_actual_collection_zeros_and_nonzero_both_advance_only_own_clock(self):
        for amounts in ((0,0),(7,11)):
            with self.subTest(amounts=amounts):
                self.setUp();before=copy.deepcopy(self.k.state['last'])
                self.rpc.receipt['logs']=[self.event(amount0=amounts[0],amount1=amounts[1])]
                self.recover()
                self.assertEqual(self.rpc.now,self.k.state['last']['harvest:1'])
                for key in ('harvest:2','compound:1','rebalance:1'):
                    self.assertEqual(before[key],self.k.state['last'][key])

    def test_restored_wrong_bucket_key_cannot_publish_unrelated_clock(self):
        self.prepare(key='harvest:2',bucket=1)
        self.k=Keeper(self.f.cfg,rpc=self.rpc)
        before=copy.deepcopy(self.k.state['last'])
        with patch('keeper.monitor.log') as events:self.recover()
        self.assertEqual(before,self.k.state['last'])
        events.assert_any_call('harvest_clock_unverified',action='harvest:2',reason='saved_call_or_receipt_not_proved')
        self.assertEqual(1,sum(call.args[0]=='harvest_clock_unverified' for call in events.call_args_list))

    def test_wrong_selector_target_value_or_noncanonical_key_cannot_advance_clock(self):
        variants=({'key':'harvest:01'},{'target':coalescing.OTHER},{'value':10},
            {'data':calldata('rebalance(uint256,uint128,uint256)',1,1,self.rpc.now+180)},
            {'data':calldata('collectFees(uint256,uint256)',1,self.rpc.now+180)+'00'})
        for variant in variants:
            with self.subTest(variant=variant):
                self.setUp();self.prepare(**variant)
                before=copy.deepcopy(self.k.state['last']);self.recover()
                self.assertEqual(before,self.k.state['last'])

    def test_missing_or_foreign_event_preserves_clock_and_paid_recovery(self):
        variants=(None,[],[{'address':coalescing.OTHER}],)
        for logs in variants:
            with self.subTest(logs=logs):
                self.setUp();self.rpc.receipt['logs']=logs
                before=copy.deepcopy(self.k.state['last']);self.recover()
                self.assertEqual(before,self.k.state['last'])

    def test_event_wrong_bucket_or_inclusion_cannot_prove_standalone_harvest(self):
        for event in (self.event(2),{**self.event(),'blockHash':'0x'+'cd'*32},
                      {**self.event(),'transactionHash':'0x'+'cd'*32},
                      {**self.event(),'removed':True}):
            with self.subTest(event=event):
                self.setUp();self.rpc.receipt['logs']=[event]
                before=copy.deepcopy(self.k.state['last']);self.recover()
                self.assertEqual(before,self.k.state['last'])

    def test_duplicate_event_does_not_advance_even_after_valid_first_event(self):
        self.rpc.receipt['logs']=[self.event(),self.event()]
        before=copy.deepcopy(self.k.state['last']);self.recover()
        self.assertEqual(before,self.k.state['last'])

    def test_reverted_standalone_preserves_clock_and_records_actual_cost_retry(self):
        self.rpc.receipt['status']='0x0';before=copy.deepcopy(self.k.state['last'])
        self.recover();self.assertEqual(before,self.k.state['last'])
        self.assertEqual(self.rpc.now+self.k.retry_cooldown,self.k.state['retry_after']['harvest:1'])

    def test_unmined_or_ambiguous_standalone_has_no_state_or_signer_effect(self):
        for ambiguous in (False,True):
            with self.subTest(ambiguous=ambiguous):
                self.setUp()
                if ambiguous:self.k.state['pending']['hash']=None
                else:self.rpc.receipt=None
                self.k.save();before=copy.deepcopy(self.k.state);disk=self.k.path.read_bytes()
                with patch('keeper.monitor.subprocess.run') as signer:self.assertTrue(self.k.poll_pending())
                signer.assert_not_called();self.assertEqual(before,self.k.state)
                self.assertEqual(disk,self.k.path.read_bytes())

    def test_failed_save_restores_harvest_nonce_spend_and_pending_together(self):
        before=copy.deepcopy(self.k.state);disk=self.k.path.read_bytes()
        with patch.object(self.k,'save',side_effect=OSError('inert failed save')),self.assertRaises(OSError):
            self.k.poll_pending()
        self.assertEqual(before,self.k.state);self.assertEqual(disk,self.k.path.read_bytes())

    def test_last_canonical_header_change_does_not_commit_proved_harvest(self):
        original=self.rpc.call;reads=0
        def call(method,params):
            nonlocal reads
            result=original(method,params)
            if method=='eth_getBlockByNumber' and params[0]=='0x63':
                reads+=1
                if reads>1:return {**result,'hash':'0x'+'cd'*32}
            return result
        self.rpc.call=call
        before=copy.deepcopy(self.k.state);disk=self.k.path.read_bytes()
        with patch('keeper.monitor.subprocess.run') as signer,self.assertRaises(RpcError):self.k.poll_pending()
        signer.assert_not_called();self.assertEqual(before,self.k.state)
        self.assertEqual(disk,self.k.path.read_bytes())

    def test_restart_keeps_proved_clock_and_does_not_double_charge_receipt(self):
        self.recover();self.k=Keeper(self.f.cfg,rpc=self.rpc)
        before=copy.deepcopy(self.k.state);disk=self.k.path.read_bytes()
        self.assertFalse(self.k.poll_pending())
        self.assertEqual(before,self.k.state);self.assertEqual(disk,self.k.path.read_bytes())

    def test_new_profile5_and6_recovery_require_explicit_profiles_and_same_proof(self):
        for kind,version in ((PortfolioRPC,5),(PolicyRPC,6)):
            with self.subTest(version=version):
                self.setUp();cfg=copy.deepcopy(kind(Path(self.f.f.tmp.name)/f'profile{version}.json').cfg)
                cfg.update(chain_id=self.f.cfg['chain_id'],sender=self.f.cfg['sender'],
                    state_path=str(Path(self.f.f.tmp.name)/f'recovery{version}.json'))
                self.k=Keeper(cfg,rpc=self.rpc)
                self.k.state.update(next_nonce=7,pending=copy.deepcopy(self.f.k.state['pending']),
                    last=copy.deepcopy(self.f.k.state['last']))
                self.prepare();self.recover()
                self.assertEqual(version,self.k.state['accounting_version'])
                self.assertEqual(self.rpc.now,self.k.state['last']['harvest:1'])

    def test_historical1_to3_recovery_keeps_existing_key_based_clock(self):
        for version in (1,2,3):
            with self.subTest(version=version):
                self.setUp();cfg=copy.deepcopy(self.f.cfg)
                cfg.update(accounting_version=version,fee_intake_version=0 if version==1 else 1,
                    state_path=str(Path(self.f.f.tmp.name)/f'historical{version}.json'))
                self.k=Keeper(cfg,rpc=self.rpc)
                self.k.state.update(next_nonce=7,pending=copy.deepcopy(self.f.k.state['pending']),
                    last=copy.deepcopy(self.f.k.state['last']))
                self.prepare(key='harvest:2',bucket=1);self.rpc.receipt['logs']=[];self.recover()
                self.assertEqual(self.rpc.now,self.k.state['last']['harvest:2'])


if __name__=='__main__':unittest.main()
