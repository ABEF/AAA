"""Versioned outside-only scheduling using inert contract/RPC transcripts.

No signer, running keeper, public RPC or chain state is touched.
"""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, NATIVE_ASSET, OUTSIDE_REBALANCE_STATE
from tests_python import test_holder_exit_profile as H
from tests_python import test_keeper as K
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


class KeeperOutsideScheduleTests(unittest.TestCase):
    def setUp(self):
        self.f = H.HolderExitKeeperTests('runTest')
        self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.cfg,self.rpc,self.base = self.f.cfg,self.f.rpc,self.f.f.base
        self.cfg['maintenance_policy_version'] = 2
        self.cfg['maintenance'] = {'compound':False,'harvest':False}
        self.pin = '0x'+keccak256(bytes.fromhex('6000')).hex()
        self.cfg['code_hashes'].update(strategy=self.pin,pools=self.pin)
        self.base.ids=[7]
        self.base.config_words[11]=43200
        self.base.group_words[6]=self.rpc.now-43200
        self.needed,self.manual,self.orientation,self.policy_version = 1,0,1,2
        self.strategy_binding = int(self.cfg['contracts']['strategy'],16)
        self.pools_binding = int(self.cfg['contracts']['pools'],16)
        self.controller_binding = int(self.cfg['contracts']['access'],16)
        self.response = {}
        original=self.rpc.call
        def call(method,params):
            if method=='eth_call' and 'from' not in params[0]:
                data=params[0]['data']
                values={
                    calldata('MAINTENANCE_POLICY_VERSION()'):self.policy_version,
                    calldata('access()'):self.controller_binding,
                    calldata('module(bytes32)','0x'+keccak256(b'ZZZStrategy').hex()):self.strategy_binding,
                    calldata('module(bytes32)','0x'+keccak256(b'ZZZPoolRegistry').hex()):self.pools_binding,
                    calldata('rangeOrientation(bytes32)',self.base.pool):self.orientation,
                    calldata('rangeUpdatePending(uint256)',7):self.manual,
                    calldata('needsRebalance(uint256)',7):self.needed,
                }
                if data in values:
                    self.rpc.calls.append((method,params))
                    if data in self.response:
                        result=self.response[data]
                        if isinstance(result,Exception):raise result
                        return result
                    return '0x'+f'{values[data]:064x}'
            return original(method,params)
        self.rpc.call=call
        self.k=self.base.k=Keeper(self.cfg,rpc=self.rpc)

    def cycle(self):
        with patch('keeper.monitor.time.time',side_effect=lambda:self.rpc.now), \
                patch.object(self.k,'submit',return_value=True) as submit:
            self.k.cycle()
        return submit

    def scheduled(self):
        return self.k.state.get(OUTSIDE_REBALANCE_STATE,{}).get('7')

    def reads(self,signature):
        data=calldata(signature,*((7,) if 'uint256' in signature else ()))
        return [params for method,params in self.rpc.calls if method=='eth_call' and params[0]['data']==data]

    def test_initial_hard_cooldown_does_not_schedule_even_when_outside(self):
        self.base.group_words[6]=self.rpc.now-3600
        with patch('keeper.monitor.secrets.randbelow') as random:
            self.cycle().assert_not_called(); random.assert_not_called()
        self.assertIsNone(self.scheduled())
        self.assertFalse(self.reads('needsRebalance(uint256)'))

    def test_exact_cooldown_schedules_one_bounded_delay_before_rebalance(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0) as random:
            self.cycle().assert_not_called(); random.assert_called_once_with(541)
        self.assertEqual(self.rpc.now+60,self.scheduled()['execute_after'])
        self.rpc.now+=59; self.cycle().assert_not_called()
        self.rpc.now+=1
        self.cycle().assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'rebalance:7')

    def test_upper_random_delay_is_ten_minutes(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=540):self.cycle()
        self.assertEqual(self.rpc.now+600,self.scheduled()['execute_after'])

    def test_restart_keeps_identical_jitter_without_redrawing(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=200):self.cycle()
        expected=copy.deepcopy(self.scheduled())
        self.k=self.base.k=Keeper(self.cfg,rpc=self.rpc)
        self.rpc.now+=30
        with patch('keeper.monitor.secrets.randbelow') as random:
            self.cycle().assert_not_called();random.assert_not_called()
        self.assertEqual(expected,self.scheduled())

    def test_inside_range_evaluates_hourly_without_drawing_jitter(self):
        self.needed=0
        with patch('keeper.monitor.secrets.randbelow') as random:self.cycle();random.assert_not_called()
        self.assertEqual(self.rpc.now+3600,self.scheduled()['next_check_at'])
        initial=len(self.reads('needsRebalance(uint256)'))
        self.needed=1;self.rpc.now+=3599
        self.cycle().assert_not_called()
        self.assertEqual(initial,len(self.reads('needsRebalance(uint256)')))
        self.rpc.now+=1
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.assertEqual(self.rpc.now+60,self.scheduled()['execute_after'])

    def test_operator_width_request_does_not_wait_for_the_next_hourly_check(self):
        self.needed=0;self.cycle();self.rpc.now+=30
        self.manual=1;self.needed=1
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.assertEqual(self.rpc.now+60,self.scheduled()['execute_after'])
        self.rpc.now+=60
        self.cycle().assert_called_once()

    def test_manual_width_request_still_obeys_hard_cooldown(self):
        self.manual=1;self.base.group_words[6]=self.rpc.now-43199
        self.cycle().assert_not_called();self.assertIsNone(self.scheduled())

    def test_return_inside_cancels_queued_execution_and_resumes_hourly_checks(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.rpc.now+=60;self.needed=0
        self.cycle().assert_not_called()
        self.assertEqual(0,self.scheduled()['execute_after'])
        self.assertEqual(self.rpc.now+3600,self.scheduled()['next_check_at'])

    def test_topups_idle_and_harvest_do_not_redraw_or_reset_jitter(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=100):self.cycle()
        expected=copy.deepcopy(self.scheduled())
        self.base.group_words[2]+=100;self.base.group_words[3]+=50;self.base.group_words[4]+=1000
        self.k.state['last']['harvest:7']=self.rpc.now
        self.rpc.now+=30
        with patch('keeper.monitor.secrets.randbelow') as random:
            self.cycle().assert_not_called();random.assert_not_called()
        self.assertEqual(expected,self.scheduled())

    def test_confirmed_new_lp_invalidates_old_jitter_and_starts_new_chain_cooldown(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.base.group_words[1]+=1;self.base.group_words[6]=self.rpc.now
        self.cycle().assert_not_called();self.assertIsNone(self.scheduled())

    def test_policy_change_discards_old_timer_and_requires_a_new_durable_delay(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        old=self.scheduled()['identity']
        self.base.config_words[7]=2500
        with patch('keeper.monitor.secrets.randbelow',return_value=540):self.cycle()
        self.assertNotEqual(old,self.scheduled()['identity'])
        self.assertEqual(self.rpc.now+600,self.scheduled()['execute_after'])

    def test_downtime_evaluates_current_state_once_without_replaying_missed_cycles(self):
        self.needed=0;self.cycle()
        self.rpc.now+=86400;self.needed=1
        with patch('keeper.monitor.secrets.randbelow',return_value=0) as random:
            self.cycle().assert_not_called();random.assert_called_once()
        self.assertEqual(self.rpc.now+60,self.scheduled()['execute_after'])

    def test_waiting_jitter_preserves_independent_due_hourly_harvest(self):
        self.k.maintenance['harvest']=True
        with patch('keeper.monitor.secrets.randbelow',return_value=540):
            self.cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',
                (7,self.rpc.now+180),'harvest:7')
        self.assertGreater(self.scheduled()['execute_after'],self.rpc.now)

    def test_hourly_inside_wait_preserves_independent_harvest(self):
        self.needed=0;self.cycle();self.k.maintenance['harvest']=True
        self.rpc.now+=60
        self.cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',
            (7,self.rpc.now+180),'harvest:7')

    def test_pending_recovery_precedes_new_policy_or_schedule_reads(self):
        self.k.state['pending']={'key':'saved'}
        with patch.object(self.k,'poll_pending',return_value=True), \
                patch.object(self.k,'_validate_upkeep_policy') as policy:
            self.cycle().assert_not_called();policy.assert_not_called()
        self.assertIsNone(self.scheduled())

    def test_failed_schedule_save_preserves_disk_and_never_reaches_submission(self):
        self.k.save();before=self.k.path.read_bytes()
        with patch.object(self.k,'save',side_effect=OSError('inert storage fault')), \
                patch('keeper.monitor.secrets.randbelow',return_value=0), \
                patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(OSError):self.cycle()
            signer.assert_not_called()
        self.assertEqual(before,self.k.path.read_bytes());self.assertIsNone(self.scheduled())
        self.assertIsNone(self.k.state['pending'])

    def test_clock_retreat_and_malformed_eligibility_fail_closed(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.rpc.now-=1
        self.cycle().assert_not_called();self.assertEqual(1,self.k.blocked_actions)
        self.rpc.now+=1
        for name in ('manual','needed','orientation'):
            old=getattr(self,name);setattr(self,name,2)
            if name=='orientation':setattr(self,name,3)
            with self.subTest(name=name):self.cycle().assert_not_called()
            setattr(self,name,old)

    def test_fresh_due_submission_revalidates_and_cancels_if_inside(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.rpc.now+=60;self.needed=0
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.submit('vault','rebalance(uint256,uint128,uint256)',
                (7,1,self.rpc.now+180),'rebalance:7'))
            signer.assert_not_called()
        self.assertEqual(0,self.scheduled()['execute_after'])
        self.assertIsNone(self.k.state['pending'])

    def test_direct_service_submission_cannot_skip_initial_jitter(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0),patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.submit('vault','rebalance(uint256,uint128,uint256)',
                (7,1,self.rpc.now+180),'rebalance:7'))
            signer.assert_not_called()
        self.assertEqual(self.rpc.now+60,self.scheduled()['execute_after'])

    def test_range_return_during_gas_review_is_rechecked_before_durable_intent(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.rpc.now+=60;self.base.enable_test_signer()
        original=self.rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='eth_estimateGas':self.needed=0
            return result
        self.rpc.call=call
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.submit('vault','rebalance(uint256,uint128,uint256)',
                (7,1,self.rpc.now+180),'rebalance:7'))
            signer.assert_not_called()
        self.assertIsNone(self.k.state['pending'])
        self.assertEqual(0,self.scheduled()['execute_after'])

    def test_policy_version_runtime_and_controller_bindings_fail_without_legacy_fallback(self):
        cases=(('policy_version',1),('strategy_binding',int(K.A,16)),
            ('pools_binding',int(K.A,16)),('controller_binding',int(K.A,16)))
        for name,value in cases:
            old=getattr(self,name);setattr(self,name,value)
            with self.subTest(name=name),self.assertRaises(RpcError):self.k.cycle()
            setattr(self,name,old)
        with patch.object(self.rpc,'call',side_effect=RpcError('inert unavailable provider')):
            with self.assertRaises(RpcError):self.k._validate_upkeep_policy()
        previous=self.cfg['code_hashes']['strategy'];self.cfg['code_hashes']['strategy']='0x'+'00'*32
        with self.assertRaises(RpcError):self.k._validate_upkeep_policy()
        self.cfg['code_hashes']['strategy']=previous

    def test_malformed_version_getter_is_not_an_old_profile(self):
        self.response[calldata('MAINTENANCE_POLICY_VERSION()')]='0x'
        with self.assertRaises(ValueError):self.k.cycle()
        self.assertIsNone(self.k.state['pending'])

    def test_new_profile_is_explicit_and_rejects_unknown_or_adaptive_configuration(self):
        for value in (0,3,'2',True,None):
            cfg=copy.deepcopy(self.cfg);cfg['maintenance_policy_version']=value
            with self.subTest(value=value),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
        cfg=copy.deepcopy(self.cfg);cfg['adaptive_range']={'enabled':True,'policy_version':1}
        with self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)

    def test_historical_accounting4_absent_or_explicit1_does_not_probe_new_getters(self):
        for explicit in (False,True):
            cfg=copy.deepcopy(self.cfg);cfg.pop('maintenance_policy_version')
            if explicit:cfg['maintenance_policy_version']=1
            keeper=Keeper(cfg,rpc=self.rpc)
            before=len(self.reads('MAINTENANCE_POLICY_VERSION()'))
            self.assertEqual(1,keeper.maintenance_policy_version)
            with patch.object(keeper,'submit',return_value=True) as submit:keeper.cycle()
            submit.assert_called_once()
            self.assertEqual(before,len(self.reads('MAINTENANCE_POLICY_VERSION()')))

    def test_new_namespace_validation_rejects_malformed_and_oversized_records(self):
        record=dict(identity=K.H,observed_at=self.rpc.now,next_check_at=0,execute_after=self.rpc.now+60)
        cases=[{'07':record},{'0':record},{str(1 << 256):record},{'7':dict(record,execute_after=True)},
            {'7':dict(record,execute_after=self.rpc.now+601)}, {'7':dict(record,extra=1)},
            {'7':dict(record,identity='bad')}, {'7':dict(record,next_check_at=1)},[]]
        for invalid in cases:
            self.k.state[OUTSIDE_REBALANCE_STATE]=invalid;self.k.save()
            with self.subTest(shape=type(invalid).__name__),self.assertRaises((ValueError,RpcError)):
                Keeper(self.cfg,rpc=self.rpc)
        self.k.state[OUTSIDE_REBALANCE_STATE]={'7':record,'8':record};self.k.save()
        cfg=copy.deepcopy(self.cfg);cfg['bucket_discovery']={'maximum_count':1,'max_per_cycle':1}
        with self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)

    def test_inactive_position_removes_only_its_new_schedule_namespace(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.cycle()
        self.k.state['last']['harvest:7']=123;self.k.state['spent']['2026-10-27']=456
        self.base.group_words[7]=4;self.base.group_words[1]=0
        self.cycle().assert_not_called()
        self.assertIsNone(self.scheduled())
        self.assertEqual(123,self.k.state['last']['harvest:7'])
        self.assertEqual(456,self.k.state['spent']['2026-10-27'])

    def test_separate_compound_capability3_is_required_only_by_new_policy(self):
        budget='0x'+'92'*20
        self.cfg['idle_compounding_budget']=budget
        self.cfg['code_hashes']['idle_compounding_budget']=self.pin
        original=self.rpc.call;version=3
        def call(method,params):
            if method=='eth_call' and 'from' not in params[0]:
                data=params[0]['data'];target=params[0]['to']
                values={calldata('migrationBudget()'):int(budget,16)}
                if target==budget:values={calldata('vault()'):int(self.k.contracts['vault'],16),
                    calldata('IDLE_COMPOUNDING_VERSION()'):version,calldata('compoundReady(uint256)',7):1}
                if data in values:return '0x'+f'{values[data]:064x}'
            return original(method,params)
        self.rpc.call=call
        self.assertTrue(self.k._compound_ready(7))
        version=2
        with self.assertRaises(RpcError):self.k._compound_ready(7)
        version=3;self.k.maintenance_policy_version=1
        with self.assertRaises(RpcError):self.k._compound_ready(7)

    def test_enabled_fresh_compounding_requires_currency_map(self):
        cfg=copy.deepcopy(self.cfg);cfg['maintenance']['compound']=True
        with self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
        cfg['maintenance']['compound_thresholds']={NATIVE_ASSET:'100',K.C:'100'}
        Keeper(cfg,rpc=self.rpc)


if __name__=='__main__':unittest.main()
