"""Sampled confirmation scheduling/reset recovery with inert RPC transcripts."""
import copy
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, CONFIRMATION_CLEARS, CONFIRMATION_RESETS, CONFIRMATION_STATE
from keeper.rebalance_confirmation import RebalanceConfirmation
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError
from tests_python import test_keeper_outside_schedule as schedules
from tests_python import test_keeper as basic


def words(*values):
    return '0x'+''.join(f'{int(value,16) if isinstance(value,str) else int(value):064x}' for value in values)


class KeeperConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.f=schedules.KeeperOutsideScheduleTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.cfg,self.rpc,self.base=self.f.cfg,self.f.rpc,self.f.base
        self.helper='0x'+'93'*20
        self.cfg['rebalance_confirmation_version']=1
        self.cfg['interval_seconds']=60
        self.cfg['contracts']['rebalance_confirmation']=self.helper
        self.cfg['code_hashes']['rebalance_confirmation']=self.f.pin
        self.budget='0x'+'92'*20
        self.cfg['idle_compounding_budget']=self.budget
        self.cfg['code_hashes']['idle_compounding_budget']=self.f.pin
        self.duration,self.gap,self.revision,self.side,self.manual=900,300,1,1,False
        self.identity=int('12'*32,16);self.record=[0,0,0,0];self.bad={}
        original=self.rpc.call
        def call(method,params):
            if method=='eth_call' and 'from' not in params[0]:
                target,data=params[0]['to'],params[0]['data']
                answers={}
                if target==self.cfg['contracts']['strategy']:
                    answers={calldata('rebalanceConfirmation()'):(self.helper,),
                        calldata('REBALANCE_CONFIRMATION_VERSION()'):(1,),
                        calldata('rebalanceReady(uint256)',7):(self.ready(),)}
                if target==self.helper:
                    answers={calldata('strategy()'):(self.cfg['contracts']['strategy'],),
                        calldata('access()'):(self.cfg['contracts']['access'],),
                        calldata('REBALANCE_CONFIRMATION_VERSION()'):(1,),calldata('duration()'):(self.duration,),
                        calldata('maxObservationGap()'):(self.gap,),calldata('policyRevision()'):(self.revision,),
                        calldata('reviewHash()'):(1,),
                        calldata('condition(uint256)',7):(0 if self.manual else self.side,
                            0 if self.manual or self.side==0 else self.identity,self.manual),
                        calldata('observations(uint256)',7):tuple(self.record),
                        calldata('ready(uint256)',7):(self.ready(),)}
                if target==self.budget:
                    answers={calldata('vault()'):(self.cfg['contracts']['vault'],),
                        calldata('access()'):(self.cfg['contracts']['access'],),
                        calldata('REBALANCE_CONFIRMATION_VERSION()'):(1,)}
                if target==self.cfg['contracts']['vault']:
                    answers.update({calldata('migrationBudget()'):(self.budget,)})
                if target==self.cfg['contracts']['access']:
                    answers.update({calldata('module(bytes32)','0x'+keccak256(b'ZZZVault').hex()):
                        (self.cfg['contracts']['vault'],)})
                if data in answers:
                    self.rpc.calls.append((method,copy.deepcopy(params)))
                    if (target,data) in self.bad:
                        result=self.bad[target,data]
                        if isinstance(result,Exception):raise result
                        return result
                    return words(*answers[data])
            return original(method,params)
        self.rpc.call=call
        self.k=Keeper(self.cfg,rpc=self.rpc)

    def ready(self):
        identity,first,last,side=self.record
        return self.manual or bool(self.gap and self.side and identity==self.identity and side==self.side and
            first and first<=last<=self.rpc.now and self.rpc.now-last<=self.gap and self.rpc.now-first>=self.duration)

    def cycle(self):
        with patch('keeper.monitor.time.time',side_effect=lambda:self.rpc.now), \
                patch.object(self.k,'submit',return_value=True) as submit:
            self.k.cycle()
        return submit

    def schedule(self):return self.k.state.get(CONFIRMATION_STATE,{}).get('7')

    def test_explicit_profile_and_helper_pins_fail_closed_without_legacy_fallback(self):
        for value in (True,'1',2):
            cfg=copy.deepcopy(self.cfg);cfg['rebalance_confirmation_version']=value
            with self.subTest(value=value),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
        cfg=copy.deepcopy(self.cfg);cfg['code_hashes'].pop('rebalance_confirmation')
        with self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
        cfg=copy.deepcopy(self.cfg);cfg.pop('rebalance_confirmation_version')
        old=Keeper(cfg,rpc=self.rpc)
        self.assertEqual(0,old.rebalance_confirmation.version)

    def test_policy_condition_and_readiness_are_pinned_and_consistent(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):status=self.k.rebalance_confirmation.status(7)
        self.assertEqual(900,status['duration_seconds']);self.assertEqual(300,status['maximum_gap_seconds'])
        self.assertFalse(status['ready']);self.assertTrue(RebalanceConfirmation.observation_due(status,self.rpc.now))
        calls=[p for m,p in self.rpc.calls if m=='eth_call' and p[0]['to']==self.helper]
        self.assertTrue(calls);self.assertTrue(all(isinstance(p[1],dict) and p[1]['requireCanonical'] is True for p in calls))

    def test_hard_cooldown_does_not_submit_observations(self):
        self.base.group_words[6]=self.rpc.now-43199
        self.cycle().assert_not_called();self.assertIsNone(self.schedule())

    def test_outside_starts_observation_not_rebalance_or_jitter(self):
        with patch('keeper.monitor.secrets.randbelow') as random:
            self.cycle().assert_called_once_with('rebalance_confirmation','observe(uint256)',(7,),'rebalance_observation:7')
        random.assert_not_called();self.assertEqual(0,self.schedule()['execute_after'])
        self.assertEqual(self.rpc.now+240,self.schedule()['next_check_at'])

    def test_inside_and_pending_conditions_are_checked_every_four_minutes(self):
        self.side=0;self.cycle().assert_not_called();initial=len(self.rpc.calls)
        self.rpc.now+=239;self.side=1;self.cycle().assert_not_called()
        helper_before=sum(m=='eth_call' and p[0]['to']==self.helper for m,p in self.rpc.calls)
        self.rpc.now+=1;self.cycle().assert_called_once()
        self.assertGreater(sum(m=='eth_call' and p[0]['to']==self.helper for m,p in self.rpc.calls),helper_before)
        self.assertGreater(len(self.rpc.calls),initial)

    def test_sampled_readiness_starts_jitter_and_refreshes_samples_during_wait(self):
        self.k._confirmation_seen_buckets.add(7)
        self.record=[self.identity,self.rpc.now-900,self.rpc.now-300,1]
        with patch('keeper.monitor.secrets.randbelow',return_value=540):
            self.cycle().assert_called_once_with('rebalance_confirmation','observe(uint256)',(7,),'rebalance_observation:7')
        first=copy.deepcopy(self.schedule());self.assertEqual(self.rpc.now+600,first['execute_after'])
        self.record[2]=self.rpc.now;self.rpc.now+=300
        with patch('keeper.monitor.secrets.randbelow') as random:self.cycle().assert_called_once();random.assert_not_called()
        self.assertEqual(first['execute_after'],self.schedule()['execute_after'])
        self.record[2]=self.rpc.now;self.rpc.now+=300
        self.cycle().assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'rebalance:7')

    def test_deliberate_width_change_bypasses_buffer_but_not_jitter(self):
        self.manual=True;self.f.manual=1;self.gap=0
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle().assert_not_called()
        self.assertEqual(self.rpc.now+60,self.schedule()['execute_after'])
        self.rpc.now+=60
        self.cycle().assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'rebalance:7')

    def test_unconfigured_gap_blocks_ordinary_work_but_independent_harvest_continues(self):
        self.gap=0;self.k.maintenance['harvest']=True
        self.cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',
            (7,self.rpc.now+180),'harvest:7')
        self.assertEqual(1,self.k.blocked_actions);self.assertEqual(0,self.schedule()['execute_after'])

    def test_restart_with_existing_candidate_requires_a_receipt_backed_reset(self):
        self.record=[self.identity,self.rpc.now-900,self.rpc.now-100,1]
        self.cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7')
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.k=Keeper(self.cfg,rpc=self.rpc)
        self.cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7')

    def test_observed_rpc_fault_persists_reset_marker_without_claiming_chain_reset(self):
        self.k._confirmation_seen_buckets.add(7)
        self.record=[self.identity,self.rpc.now-900,self.rpc.now-100,1]
        self.bad[self.helper,calldata('condition(uint256)',7)]=RpcError('DO-NOT-EXPORT')
        self.k.maintenance['harvest']=True
        self.cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7')
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7']);self.assertNotEqual([0,0,0,0],self.record)
        self.assertNotIn('DO-NOT-EXPORT',self.k.path.read_text())
        self.bad.clear();self.k.maintenance['harvest']=False
        self.cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7')

    def test_bad_gap_version_and_contradictory_ready_never_submit_an_observation(self):
        for signature,value in (('maxObservationGap()',451),('REBALANCE_CONFIRMATION_VERSION()',0)):
            self.bad[self.helper,calldata(signature)]=words(value)
            with self.subTest(signature=signature),patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):
                self.k.rebalance_confirmation.status(7)
            self.bad.clear()
        self.bad[self.helper,calldata('ready(uint256)',7)]=words(True)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):self.k.rebalance_confirmation.status(7)

    def test_pending_receipt_recovery_precedes_all_new_profile_reads(self):
        self.k.state['pending']={'key':'saved'}
        before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'poll_pending',return_value=True), \
                patch.object(self.k.rebalance_confirmation,'status',side_effect=AssertionError('Recovery first')) as status:
            self.cycle().assert_not_called();status.assert_not_called()
        self.assertEqual(before,self.k.state)

    def test_reset_receipt_clears_only_its_marker_after_exact_canonical_success(self):
        receipt_fixture=basic.KeeperTests('runTest')
        receipt_fixture.k=self.k;receipt_fixture.rpc=self.rpc
        self.k.state['next_nonce']=7;self.k.state[CONFIRMATION_RESETS]={'7':True,'8':True}
        for success in (False,True):
            receipt_fixture.receipt(success)
            pending=self.k.state['pending'];data=calldata('resetObservation(uint256)',7)
            pending.update(to=self.helper,data=data,value=0,key='rebalance_reset:7')
            pending['fee_review']['maximum_cost_wei']=517
            self.rpc.tx.update(to=self.helper,input=data,value='0x0')
            self.rpc.receipt['to']=self.helper
            with patch('keeper.monitor.time.time',return_value=self.rpc.now):self.assertFalse(self.k.poll_pending())
            self.assertEqual(not success,'7' in self.k.state[CONFIRMATION_RESETS])
            self.assertTrue(self.k.state[CONFIRMATION_RESETS]['8'])
            if success:
                clear=self.k.state[CONFIRMATION_CLEARS]['7']
                self.assertEqual(99,clear['number']);self.assertEqual(7,clear['nonce'])
                self.assertEqual(basic.H,clear['hash']);self.assertTrue(clear['awaiting_healthy_read'])

    def test_reset_journal_save_failure_preserves_prior_state_and_stops_work(self):
        self.k.save();before=self.k.path.read_bytes()
        with patch.object(self.k,'save',side_effect=OSError('inert storage failure')),self.assertRaises(OSError):
            self.k._mark_confirmation_reset(7)
        self.assertEqual(before,self.k.path.read_bytes());self.assertNotIn(CONFIRMATION_RESETS,self.k.state)

    def test_reset_validation_does_not_need_prices_or_candidate_readiness(self):
        self.bad[self.helper,calldata('condition(uint256)',7)]=RpcError('inert unavailable price')
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer:
            self.assertFalse(self.k.submit('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7'))
        signer.assert_not_called();self.assertIsNone(self.k.state['pending'])
        self.assertEqual('within_configured_caps',self.k.gas_review_health['last_review']['state'])

    def test_observed_pause_queues_reset_once_without_repeated_successful_noops(self):
        self.base.paused=True
        self.cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7')
        self.k.state[CONFIRMATION_RESETS].pop('7')
        self.cycle().assert_not_called()
        self.assertIn(7,self.k._confirmation_pause_seen)

    def test_pending_rpc_fault_never_rewrites_pending_and_defers_reset_until_recovery(self):
        self.k._confirmation_seen_buckets.add(7)
        self.k.state['pending']={'key':'rebalance_observation:7','to':self.helper,
            'data':calldata('observe(uint256)',7)};self.k.save();before=self.k.path.read_bytes()
        with patch.object(self.k,'poll_pending',side_effect=RpcError('inert receipt outage')):
            self.assertFalse(self.k.run_cycle())
        self.assertEqual(before,self.k.path.read_bytes());self.assertTrue(self.k._confirmation_recovery_interrupted)
        self.k.state['pending']=None
        with patch.object(self.k,'poll_pending',return_value=False):
            self.cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7')
        self.assertFalse(self.k._confirmation_recovery_interrupted)

    def test_budget_runtime_parent_and_confirmation_gate_are_required(self):
        cases=((self.budget,'REBALANCE_CONFIRMATION_VERSION()',0),
            (self.budget,'vault()',basic.A),(self.budget,'access()',basic.A),
            (self.cfg['contracts']['vault'],'migrationBudget()',basic.A))
        for target,signature,value in cases:
            self.bad[target,calldata(signature)]=words(value)
            with self.subTest(signature=signature),patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):
                self.k.rebalance_confirmation.status(7)
            self.bad.clear()
        self.cfg['code_hashes']['idle_compounding_budget']='0x'+'11'*32
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):self.k.rebalance_confirmation.validate()

    def test_subfour_minute_gap_is_not_paid_forever_by_the_four_minute_worker(self):
        self.gap=239;self.k.maintenance['harvest']=True
        self.cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7')
        self.assertEqual(1,self.k.blocked_actions);self.assertEqual(0,self.schedule()['execute_after'])

    def test_receipt_latency_does_not_skip_the_next_scheduled_observation(self):
        self.k._confirmation_seen_buckets.add(7)
        self.record=[self.identity,self.rpc.now-900,self.rpc.now-298,1]
        with patch('keeper.monitor.secrets.randbelow',return_value=540):
            self.cycle().assert_called_once_with('rebalance_confirmation','observe(uint256)',(7,),'rebalance_observation:7')
        self.assertEqual(self.rpc.now+240,self.schedule()['next_check_at'])

    def test_confirmation_rejects_a_vault_outside_the_active_access_module(self):
        selector=calldata('module(bytes32)','0x'+keccak256(b'ZZZVault').hex())
        self.bad[self.cfg['contracts']['access'],selector]=words(basic.A)
        before=copy.deepcopy(self.k.state)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer, \
                self.assertRaisesRegex(RpcError,'Vault module differs'):
            self.k.rebalance_confirmation.validate()
        signer.assert_not_called();self.assertEqual(before,self.k.state)


if __name__=='__main__':unittest.main()
