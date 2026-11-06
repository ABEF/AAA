"""Late ordinary-LP submission races; inert RPC and signer, no live service.

Runtime/profile admission and economic execution have separate tests. This
transport fixture isolates changes AFTER the original successful simulation.
"""
import copy
import datetime as dt
import json
import subprocess
import unittest
from unittest.mock import patch

from keeper.compound_policy import classify_range
from keeper.health import summary
from keeper.monitor import Keeper
from tests_python import test_keeper as basic
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError

LP_ACTIONS=(('vault','rebalance(uint256,uint128,uint256)','rebalance:7'),
            ('compounder','compound(uint256,uint128,uint256)','compound:7'))


class KeeperLateLPReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture=basic.KeeperTests('runTest')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.fixture.enable_test_signer()
        self.k,self.rpc,self.cfg=self.fixture.k,self.fixture.rpc,self.fixture.cfg
        self.k._validate_accounting_version=lambda:None
        self.k._validate_checkpoint=lambda:None
        self.k._validate_lp_routing=lambda **_:None
        self.k._validate_code_hashes=lambda:None
        self.lifecycle=False;self.stopping=False
        self.k._defer_for_lifecycle=lambda *_:self.lifecycle
        self.k.stop_requested=lambda:self.stopping
        self.readiness={'vault':True,'compounder':True}
        self.readiness_calls=[]
        def ready(name,args):
            self.readiness_calls.append((name,tuple(args)))
            return self.readiness[name]
        self.k._rebalance_submission_ready=lambda args:ready('vault',args)
        self.k._compound_submission_ready=lambda args:ready('compounder',args)
        self.original=self.rpc.call
        self.simulations=[];self.late=None
        def call(method,params):
            if method=='eth_call' and 'from' in params[0]:
                self.simulations.append(copy.deepcopy(params))
                if 'gas' in params[0] and self.late is not None:
                    return self.late(method,params)
            return self.original(method,params)
        self.rpc.call=call
        self.clock=patch('keeper.monitor.time.time',side_effect=lambda:self.rpc.now)
        self.clock.start();self.addCleanup(self.clock.stop)

    def args(self):return (7,123456789,self.rpc.now+180)

    def submit(self,action=LP_ACTIONS[0],args=None):
        return self.k.submit(action[0],action[1],args or self.args(),action[2])

    def assert_no_intent(self,before):
        self.assertEqual(before,self.k.state)
        self.assertIsNone(self.k.state['pending'])
        self.assertFalse(self.k.path.exists())

    def test_both_methods_simulate_exact_original_bytes_and_reviewed_gas_before_durable_signing(self):
        for action in LP_ACTIONS:
            with self.subTest(action=action[0]):
                args=self.args();original_state=copy.deepcopy(self.k.state)
                self.simulations.clear();self.readiness_calls.clear()
                if self.k.path.exists():self.k.path.unlink()
                def sign(command,**_):
                    saved=json.loads(self.k.path.read_text())['pending']
                    self.assertIsNone(saved['hash']);self.assertEqual(saved['nonce'],7)
                    self.assertEqual(saved['data'],calldata(action[1],*args))
                    self.assertEqual(command[3],saved['data'])
                    self.assertEqual(command[command.index('--gas-limit')+1],'125')
                    self.assertEqual(command[command.index('--gas-price')+1],'2')
                    self.assertEqual(saved['fee_review']['maximum_cost_wei'],250)
                    self.assertEqual(len(self.simulations),2)
                    self.assertEqual(self.rpc.calls[-1],('eth_getBlockByNumber',['latest',False]))
                    return subprocess.CompletedProcess(command,0,basic.H,'')
                with patch('keeper.monitor.subprocess.run',side_effect=sign) as signer:
                    self.assertTrue(self.submit(action,args))
                self.assertEqual(signer.call_count,1)
                first,last=self.simulations
                self.assertEqual(last,[{**first[0],'gas':'0x7d','gasPrice':'0x2'},'latest'])
                self.assertEqual(last[0]['data'],calldata(action[1],*args))
                self.assertEqual(self.readiness_calls,[(action[0],args)]*3)
                self.assertEqual(self.k.state['spent'],original_state['spent'])
                self.k.state=original_state

    def test_late_market_or_gas_failure_never_saves_signs_or_spends(self):
        before=copy.deepcopy(self.k.state)
        for action in LP_ACTIONS:
            for reason in ('changed market floor','route exceeds gas envelope'):
                def fail(*_):raise RpcError(reason)
                self.late=fail
                with self.subTest(action=action[0],reason=reason),patch('keeper.monitor.subprocess.run') as signer:
                    with self.assertRaises(RpcError):self.submit(action)
                    signer.assert_not_called();self.assert_no_intent(before)
                    self.assertEqual(self.k.gas_review_health['last_review']['reason'],'lp_final_simulation_unavailable')

    def test_void_result_is_exact_and_provider_payload_is_not_exported(self):
        before=copy.deepcopy(self.k.state)
        for result in (None,True,'0x00','0x'+'0'*64,'0X','DO-NOT-EXPORT https://secret.invalid',{'result':'0x'}):
            self.late=lambda *_:result
            with self.subTest(result_type=type(result).__name__),patch('keeper.monitor.subprocess.run') as signer:
                with self.assertRaises(RpcError):self.submit()
                signer.assert_not_called();self.assert_no_intent(before)
                self.assertNotIn('DO-NOT-EXPORT',json.dumps(self.k.gas_review_health))

    def test_changed_market_can_recover_on_a_new_explicit_attempt_without_saved_intent(self):
        before=copy.deepcopy(self.k.state)
        def fail(*_):raise RpcError('old market unavailable')
        self.late=fail
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(RpcError):self.submit()
            signer.assert_not_called();self.assert_no_intent(before)
        self.late=None
        with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,basic.H,'')) as signer:
            self.assertTrue(self.submit())
        signer.assert_called_once()

    def test_expired_or_too_far_original_deadline_is_deferred_without_extension(self):
        before=copy.deepcopy(self.k.state)
        original_now=self.rpc.now
        for advance in (181,-1):
            self.rpc.now=original_now
            args=(7,123456789,original_now+180 if advance>0 else original_now+601)
            def change(*_):
                if advance>0:self.rpc.now+=advance
                return '0x'
            self.late=change
            with self.subTest(advance=advance),patch('keeper.monitor.subprocess.run') as signer:
                self.assertFalse(self.submit(args=args))
                signer.assert_not_called();self.assert_no_intent(before)
                self.assertEqual(self.simulations[-1][0]['data'],calldata(LP_ACTIONS[0][1],*args))
                self.assertEqual(self.k.gas_review_health['last_review']['reason'],'lp_submission_deadline_invalid')

    def test_head_or_timestamp_retreat_is_not_accepted_as_fresh(self):
        before=copy.deepcopy(self.k.state)
        for kind in ('height','timestamp'):
            self.rpc.now=int(dt.datetime(2026,11,6,12,tzinfo=dt.timezone.utc).timestamp())
            def late(*_):
                if kind=='timestamp':self.rpc.now-=1
                return '0x'
            self.late=late
            with self.subTest(kind=kind),patch('keeper.monitor.subprocess.run') as signer:
                if kind=='height':
                    old=self.rpc.call
                    def height(method,params):
                        result=old(method,params)
                        if method=='eth_getBlockByNumber' and self.simulations and 'gas' in self.simulations[-1][0]:
                            return {**result,'number':'0x63'}
                        return result
                    with patch.object(self.rpc,'call',side_effect=height):
                        with self.assertRaises(RpcError):self.submit()
                else:
                    with self.assertRaises(RpcError):self.submit()
                signer.assert_not_called();self.assert_no_intent(before)
            self.simulations.clear()

    def test_utc_day_cost_cap_is_rechecked_after_late_review(self):
        self.rpc.now=int(dt.datetime(2026,11,6,23,59,50,tzinfo=dt.timezone.utc).timestamp())
        tomorrow='2026-11-07';self.k.state['spent'][tomorrow]=self.cfg['max_daily_cost_wei']-249
        before=copy.deepcopy(self.k.state)
        def late(*_):self.rpc.now+=20;return '0x'
        self.late=late
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit())
            signer.assert_not_called();self.assert_no_intent(before)
        self.assertEqual(self.k.gas_review_health['last_review']['reason'],'cost_cap')

    def test_unrepresentable_late_utc_head_is_a_sanitized_rpc_failure(self):
        before=copy.deepcopy(self.k.state);review={}
        timestamp=1<<63
        tx={'from':self.k.sender,'to':self.k.contracts['vault'],
            'data':calldata(LP_ACTIONS[0][1],7,1,timestamp+180),'value':'0x0'}
        with patch.object(self.k,'_head',return_value=(101,timestamp)), \
                patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaisesRegex(RpcError,'UTC date'):
                self.k._late_lp_submission_review('vault',LP_ACTIONS[0][1],tx,(7,1,timestamp+180),'rebalance:7',
                    review_head=100,reviewed_at=self.rpc.now,gas_limit=125,gas_price=2,cost=250,nonce=7,gas_review=review)
            signer.assert_not_called();self.assert_no_intent(before)
        self.assertEqual(review['reason'],'lp_submission_head_invalid')

    def test_success_after_midnight_records_current_day_without_charging_a_submission(self):
        self.rpc.now=int(dt.datetime(2026,11,6,23,59,50,tzinfo=dt.timezone.utc).timestamp())
        before=copy.deepcopy(self.k.state['spent'])
        def late(*_):self.rpc.now+=20;return '0x'
        self.late=late
        with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,basic.H,'')):
            self.assertTrue(self.submit())
        self.assertEqual(self.k.state['pending']['day'],'2026-11-07')
        self.assertEqual(self.k.state['spent'],before)

    def test_retry_restriction_observed_during_late_review_is_preserved_without_signing(self):
        def late(*_):
            self.k.state.setdefault('retry_after',{})['rebalance:7']=self.rpc.now+60
            return '0x'
        self.late=late
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit())
            signer.assert_not_called()
        self.assertIsNone(self.k.state['pending']);self.assertFalse(self.k.path.exists())
        self.assertEqual(self.k.state['spent'],{})
        self.assertEqual(self.k.state['retry_after']['rebalance:7'],self.rpc.now+60)
        self.assertEqual(self.k.gas_review_health['last_review']['reason'],'lp_submission_retry_cooldown')

    def test_nonce_change_during_late_review_preserves_original_recovery_state(self):
        before=copy.deepcopy(self.k.state)
        changed=False
        def late(*_):
            nonlocal changed
            changed=True;return '0x'
        self.late=late;original=self.original
        def call(method,params):
            if method=='eth_getTransactionCount' and changed:return '0x8'
            return original(method,params)
        self.original=call
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(RpcError):self.submit()
            signer.assert_not_called();self.assert_no_intent(before)

    def test_funding_loss_during_late_review_never_creates_an_intent(self):
        before=copy.deepcopy(self.k.state)
        changed=False
        def late(*_):
            nonlocal changed
            changed=True;return '0x'
        self.late=late;original=self.original
        self.original=lambda method,params:'0x0' if method=='eth_getBalance' and changed else original(method,params)
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(RpcError):self.submit()
            signer.assert_not_called();self.assert_no_intent(before)

    def test_stop_or_lifecycle_start_during_late_review_never_signs(self):
        before=copy.deepcopy(self.k.state)
        for kind in ('stop','lifecycle'):
            self.stopping=self.lifecycle=False
            def late(*_):
                if kind=='stop':self.stopping=True
                else:self.lifecycle=True
                return '0x'
            self.late=late
            with self.subTest(kind=kind),patch('keeper.monitor.subprocess.run') as signer:
                self.assertFalse(self.submit())
                signer.assert_not_called();self.assert_no_intent(before)

    def test_readiness_changes_during_late_economic_call_prevent_both_submissions(self):
        before=copy.deepcopy(self.k.state)
        for action in LP_ACTIONS:
            self.readiness[action[0]]=True
            def late(*_):self.readiness[action[0]]=False;return '0x'
            self.late=late
            with self.subTest(action=action[0]),patch('keeper.monitor.subprocess.run') as signer:
                self.assertFalse(self.submit(action))
                signer.assert_not_called();self.assert_no_intent(before)

    def test_stop_arriving_during_last_service_read_is_checked_before_pending(self):
        before=copy.deepcopy(self.k.state);reads=0
        def ready(_):
            nonlocal reads
            reads+=1
            if reads==3:self.stopping=True
            return True
        self.k._rebalance_submission_ready=ready
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit())
            signer.assert_not_called();self.assert_no_intent(before)
        self.assertEqual(reads,3)

    def test_deadline_expiry_during_final_service_reads_is_deferred_before_pending(self):
        before=copy.deepcopy(self.k.state);args=self.args();reads=0
        def ready(_):
            nonlocal reads
            reads+=1
            if reads==3:self.rpc.now+=181
            return True
        self.k._rebalance_submission_ready=ready
        with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,basic.H,'')) as signer:
            self.assertFalse(self.submit(args=args))
            signer.assert_not_called();self.assert_no_intent(before)
        self.assertEqual(self.simulations[-1][0]['data'],calldata(LP_ACTIONS[0][1],*args))

    def test_midnight_during_final_compound_policy_reads_rechecks_current_day_cap(self):
        self.rpc.now=int(dt.datetime(2026,11,6,23,59,50,tzinfo=dt.timezone.utc).timestamp())
        self.k.state['spent']['2026-11-07']=self.cfg['max_daily_cost_wei']-249
        before=copy.deepcopy(self.k.state);reads=0
        def ready(_):
            nonlocal reads
            reads+=1
            if reads==3:self.rpc.now+=20
            return True
        self.k._compound_submission_ready=ready
        with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,basic.H,'')) as signer:
            self.assertFalse(self.submit(LP_ACTIONS[1]))
            signer.assert_not_called();self.assert_no_intent(before)

    def test_real_compound_service_gate_still_waits_for_range_and_pending_geometry(self):
        self.k.accounting_version=6;self.k.maintenance_policy_version=3
        self.k.maintenance['compound_thresholds']={basic.B:1}
        self.k._compound_submission_ready=Keeper._compound_submission_ready.__get__(self.k)
        for kind in ('outside_before_12h','outside_after_12h','pending_geometry','threshold'):
            tick=0;pending=False;threshold=False
            elapsed=3600 if kind=='outside_before_12h' else 13*3600
            proofs=[]
            def physical(_):
                status=classify_range(lower=-100,upper=100,tick=tick,range_update_pending=pending)
                if threshold:status.update(allowed=False,status='waiting_adjustment_threshold')
                status['last_rebalance']=self.rpc.now-elapsed
                proofs.append(copy.deepcopy(status))
                return status
            self.k._compound_policy_status=physical
            def late(*_):
                nonlocal tick,pending,threshold
                if kind.startswith('outside'):tick=100
                elif kind=='pending_geometry':pending=True
                else:threshold=True
                return '0x'
            self.late=late;before=copy.deepcopy(self.k.state)
            with self.subTest(kind=kind),patch('keeper.monitor.subprocess.run') as signer:
                self.assertFalse(self.submit(LP_ACTIONS[1]))
                signer.assert_not_called();self.assert_no_intent(before)
                self.assertEqual(len(proofs),3)
                self.assertEqual(self.rpc.now-proofs[-1]['last_rebalance'],elapsed)
                self.assertTrue(proofs[0]['allowed']);self.assertFalse(proofs[-1]['allowed'])

    def test_pending_recovery_skips_new_review_and_dry_run_never_adds_a_signer_stage(self):
        self.k.state['pending']={'hash':None,'nonce':7,'key':'rebalance:7'}
        before=copy.deepcopy(self.k.state)
        with patch.object(self.rpc,'call',side_effect=AssertionError('Must recover saved intent first')), \
                patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit())
            signer.assert_not_called();self.assertEqual(self.k.state,before)
        self.k.state['pending']=None;self.k.live=False
        self.late=lambda *_:self.fail('Dry-run must not enter live late submission stage')
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit())
            signer.assert_not_called();self.assertEqual(len(self.simulations),1)

    def test_harvesting_keeps_its_existing_independent_submission_path(self):
        self.late=lambda *_:self.fail('Fee-only harvest must not acquire LP late-review policy')
        with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,basic.H,'')):
            self.assertTrue(self.k.submit('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7'))
        self.assertEqual(len(self.simulations),1)

    def test_new_diagnostics_are_static_allowlisted_and_arbitrary_provider_text_is_hidden(self):
        for reason in ('lp_final_simulation_unavailable','lp_submission_head_invalid','lp_submission_deadline_invalid',
                'lp_submission_retry_cooldown','lp_submission_nonce_changed','lp_submission_balance_insufficient'):
            with self.subTest(reason=reason):
                self.assertEqual(summary({'gas_review':{'last_review':{'reason':reason}}})['gas_review']['reason'],reason)
        result=summary({'gas_review':{'last_review':{'reason':'https://DO-NOT-EXPORT'}}})
        self.assertEqual(result['gas_review']['reason'],'unknown')
        self.assertNotIn('DO-NOT-EXPORT',json.dumps(result))


if __name__=='__main__':unittest.main()
