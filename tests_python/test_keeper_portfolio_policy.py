"""Fresh portfolio policy transcripts; no network, signer or deployed-state edits."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.compound_policy import observe as compound_observe
from keeper.health import confirmation_reasons, execution_reasons, observe_confirmation_health
from keeper.monitor import Keeper, CONFIRMATION_RESETS, CONFIRMATION_STATE
from keeper.rebalance_confirmation import PORTFOLIO_STATE_NAMESPACE
from keeper.operation_review import Review, PinnedReads, review
from tests_python.test_keeper_operation_review import ReportRPC
from tests_python.test_keeper_compound_range_policy import words
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rebalance_confirmation import observe
from zzz_ops.rpc import RpcError


class PortfolioRPC(ReportRPC):
    def __init__(self,path):
        super().__init__(path)
        self.contracts['portfolio_policy']='0x'+'b4'*20
        self.contracts['lp_balance_math']='0x'+'b5'*20
        self.contracts['lp_position_executor']='0x'+'b6'*20
        self.cfg['code_hashes']['portfolio_policy']=self.pin
        self.cfg['code_hashes']['lp_balance_math']=self.pin
        self.cfg['code_hashes']['lp_position_executor']=self.pin
        self.cfg.update(accounting_version=5,portfolio_version=1,maintenance_policy_version=3,
                        lp_routing_version=2,rebalance_confirmation_version=3)
        self.duration=600;self.threshold=8500;self.physical_side=2;self.reference=2
        self.mode=0;self.geometry=0;self.applied=0;self.policy_revision=1;self.fingerprint=101
        self.secondary=0;self.secondary_count=0;self.aux_ticks=(110,200)
        self.amounts={123:(100,200),124:(30,40)}
        self.summed=(100,200);self.fail_leg_owner=False

    def raw(self):
        return int(bool(self.now>=self.position[6]+43200 and (self.physical_side or self.manual or self.geometry!=self.applied)))

    def sample(self):
        manual=bool(self.manual or self.geometry!=self.applied)
        side=0 if manual or self.physical_side!=self.reference else self.physical_side
        identity=1 if side else 0
        old,first,last,prior=self.record
        mature=bool(self.gap and side and old==identity and prior==side and first and
                    self.now-last<=self.gap and self.now-first>=self.duration)
        return side,identity,bool(self.raw() and (manual or mature))

    def read(self,target,signature,*args,count=1):
        c=self.contracts
        values={'ACCOUNTING_VERSION()':5,'MAINTENANCE_POLICY_VERSION()':3,'CUSTODY_VERSION()':4,
            'PORTFOLIO_VERSION()':1,'LP_ROUTING_VERSION()':2,'REBALANCE_CONFIRMATION_VERSION()':3,
            'IDLE_COMPOUNDING_VERSION()':4,'portfolioPolicy()':int(c['portfolio_policy'],16),
            'rebalanceConfirmation()':int(c['rebalance_confirmation'],16),
            'strategy()':int(c['strategy'],16),'vault()':int(c['vault'],16),
            'migrationBudget()':int(self.budget,16),'duration()':self.duration,'MAX_DURATION()':604800,
            'maxObservationGap()':self.gap,'policyRevision()':1,'reviewHash()':1,
            'requireReferenceExit()':1,'referenceReviewHash()':0,'thresholdBps()':self.threshold,
            'revision()':self.policy_revision,'minimumMainBps()':6000,'maximumResidualBps()':4000,
            'enabled(bytes32)':self.mode,'configurationPending(uint256)':int(self.geometry!=self.applied),
            'geometryRevision(bytes32)':self.geometry,'appliedRevision(uint256)':self.applied,
            'controlFingerprint(bytes32)':self.fingerprint,'secondaryId(uint256)':self.secondary,
            'activeSecondaryCount()':self.secondary_count,'portfolioFingerprint(uint256)':202,
            'rangeOrientation(bytes32)':1,
            'residualSideBps(bytes32)':5000,
            'balanceMath()':int(c['lp_balance_math'],16),'balancer()':int(c['balancing_router'],16),
            'LP_BALANCE_MATH_VERSION()':1,
            'positionOperator()':int(c['lp_position_executor'],16),'LP_POSITION_EXECUTOR_VERSION()':1,
            'permit2()':int('d3'*20,16),'liquidityManager()':int(c['liquidity'],16),
            'balancingRouter()':int(c['balancing_router'],16),
            'rangeUpdatePending(uint256)':int(bool(self.manual or self.geometry!=self.applied)),
            'needsRebalance(uint256)':self.raw(),'ready(uint256)':int(self.sample()[2]),
            'rebalanceReady(uint256)':int(self.sample()[2])}
        if (target,signature) in self.overrides:
            value=self.overrides[target,signature]
            if isinstance(value,Exception):raise value
            return value
        if signature in values:return words(values[signature])
        if signature=='condition(uint256)':
            side,identity,_=self.sample()
            return words(side,identity,int(bool(self.manual or self.geometry!=self.applied)))
        if signature=='marketSides(uint256)':return words(self.physical_side,self.reference)
        if signature=='observations(uint256)':return words(*self.record)
        if signature=='portfolioAmounts(uint256)':return words(*self.summed)
        if signature=='amounts(uint256)':return words(*self.amounts[args[0]])
        if signature=='ticks(uint256)' and args==(124,):return words(*self.aux_ticks)
        if signature=='getPoolAndPositionInfo(uint256)' and args==(124,):
            lo,hi=self.aux_ticks
            info=((int(self.pool,16)>>56)<<56)|((hi%(1<<24))<<32)|((lo%(1<<24))<<8)
            return words(*self.config[:5],info)
        if signature=='ownerOf(uint256)' and args==(124,) and self.fail_leg_owner:return words(1)
        return super().read(target,signature,*args,count=count)

    def call(self,method,params):
        if method=='eth_call' and 'from' not in params[0]:
            target,data=params[0]['to'],params[0]['data']
            methods=('ACCOUNTING_VERSION()','MAINTENANCE_POLICY_VERSION()','CUSTODY_VERSION()',
                'PORTFOLIO_VERSION()','LP_ROUTING_VERSION()','REBALANCE_CONFIRMATION_VERSION()',
                'IDLE_COMPOUNDING_VERSION()','portfolioPolicy()','rebalanceConfirmation()','strategy()',
                'vault()','migrationBudget()','duration()','MAX_DURATION()','maxObservationGap()',
                'policyRevision()','reviewHash()','requireReferenceExit()','referenceReviewHash()',
                'thresholdBps()','revision()','minimumMainBps()','maximumResidualBps()', 'activeSecondaryCount()',
                'balanceMath()','balancer()','LP_BALANCE_MATH_VERSION()','positionOperator()',
                'LP_POSITION_EXECUTOR_VERSION()','permit2()','liquidityManager()')
            pairs=[(sig,()) for sig in methods]
            pairs += [(sig,(7,)) for sig in ('configurationPending(uint256)','rangeUpdatePending(uint256)',
                'needsRebalance(uint256)','ready(uint256)','rebalanceReady(uint256)','condition(uint256)',
                'marketSides(uint256)','observations(uint256)')]
            pairs += [(sig,(self.pool,)) for sig in ('enabled(bytes32)','geometryRevision(bytes32)','controlFingerprint(bytes32)','rangeOrientation(bytes32)','residualSideBps(bytes32)')]
            pairs += [(sig,(123,)) for sig in ('appliedRevision(uint256)','secondaryId(uint256)',
                'portfolioFingerprint(uint256)','portfolioAmounts(uint256)','amounts(uint256)')]
            pairs += [(sig,(124,)) for sig in ('ticks(uint256)','getPoolAndPositionInfo(uint256)',
                'ownerOf(uint256)','getPositionLiquidity(uint256)','amounts(uint256)')]
            for signature,args in pairs:
                if data==calldata(signature,*args):return '0x'+''.join(self.read(target,signature,*args))
        return super().call(method,params)

    def eth_call(self,target,data):
        header=self.call('eth_getBlockByNumber',['latest',False])
        return self.call('eth_call',[{'to':target,'data':data},{'blockHash':header['hash'],'requireCanonical':True}])


class KeeperPortfolioPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.rpc=PortfolioRPC(Path(self.tmp.name)/'state.json');self.cfg=self.rpc.cfg
        self.k=Keeper(self.cfg,rpc=self.rpc)

    def projection(self,**kw):
        return observe(self.rpc.read,strategy=self.rpc.contracts['strategy'],budget=self.rpc.budget,
            confirmation=self.rpc.contracts['rebalance_confirmation'],access=self.rpc.contracts['access'],
            portfolio_policy=self.rpc.contracts['portfolio_policy'],bucket=7,timestamp=self.rpc.now,version=3,**kw)

    def status(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):return self.k.rebalance_confirmation.status(7)

    def due(self,force=False):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            return self.k._rebalance_due(7,words(*self.rpc.position),self.rpc.now,force=force)

    def physical(self):
        return compound_observe(self.rpc.read,self.rpc.code,contracts=self.rpc.contracts,
            code_hashes=self.cfg['code_hashes'],bucket=7,accounting_version=5)

    def test_fresh_profile_is_explicit_not_a_legacy_relabel(self):
        for key,value in (('accounting_version',4),('portfolio_version',0),('maintenance_policy_version',2),
                          ('lp_routing_version',1),('rebalance_confirmation_version',2),('execution_quality_version',0)):
            cfg=copy.deepcopy(self.cfg);cfg[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)

    def test_fresh_profile_requires_reviewed_policy_address_and_runtime(self):
        for section in ('contracts','code_hashes'):
            cfg=copy.deepcopy(self.cfg);cfg[section].pop('portfolio_policy')
            with self.subTest(section=section),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)

    def test_early_cooldown_checks_raw_threshold_without_paying_for_ordinary_samples(self):
        self.rpc.position[6]=self.rpc.now-3600
        p=self.projection()
        self.assertEqual(2,p['exit_side']);self.assertFalse(p['raw_eligible_at_snapshot'])
        self.assertFalse(p['ready_at_snapshot']);self.assertTrue(p['threshold_condition_at_snapshot'])
        self.assertFalse(self.due());self.assertIsNone(self.k._rebalance_observation_due)
        self.assertEqual(0,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['execute_after'])
        self.assertEqual(self.rpc.now+240,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['next_check_at'])

    def test_paid_enrollment_opens_exactly_duration_plus_gap_before_cooldown(self):
        self.rpc.position[6]=self.rpc.now-43200+901
        self.assertFalse(self.due());self.assertIsNone(self.k._rebalance_observation_due)
        self.assertEqual(self.rpc.now+1,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['next_check_at'])
        self.rpc.now+=1;self.assertFalse(self.due());self.assertEqual(7,self.k._rebalance_observation_due)
        self.assertFalse(self.projection()['raw_eligible_at_snapshot'])

    def test_late_enrollment_preserves_stale_onchain_record_then_requires_new_window(self):
        self.rpc.position[6]=self.rpc.now-43200+1000
        self.rpc.record=(1,self.rpc.now-3600,self.rpc.now-1000,2);self.k._confirmation_seen_buckets.add(7)
        old=self.rpc.record
        self.assertFalse(self.due());self.assertIsNone(self.k._rebalance_observation_due)
        self.assertEqual(old,self.rpc.record)
        self.rpc.now+=100;self.assertFalse(self.due(force=True));self.assertEqual(7,self.k._rebalance_observation_due)
        self.assertEqual(old,self.rpc.record)
        # The simulated canonical observe receipt restarts the stale record;
        # prior firstSeen cannot stand in for the missing recent evidence.
        self.rpc.record=(1,self.rpc.now,self.rpc.now,2)
        p=self.projection();self.assertFalse(p['sampled_mature']);self.assertFalse(p['ready_at_snapshot'])

    def test_foreign_record_and_fault_reset_keep_priority_before_enrollment(self):
        self.rpc.position[6]=self.rpc.now-3600;self.rpc.record=(1,self.rpc.now-600,self.rpc.now-10,2)
        self.assertFalse(self.due());self.assertEqual(7,self.k._rebalance_reset_due)
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertIsNone(self.k._rebalance_observation_due)

    def test_enrollment_recomputes_clock_and_does_not_wake_on_early_maturity(self):
        self.rpc.position[6]=self.rpc.now-3600;self.rpc.record=(1,self.rpc.now-480,self.rpc.now,2)
        self.k._confirmation_seen_buckets.add(7)
        self.assertFalse(self.due());self.assertIsNone(self.k._rebalance_observation_due)
        self.assertEqual(self.rpc.now+240,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['next_check_at'])
        # A changed actual replacement checkpoint changes the policy basis and
        # makes the late enrollment window open without a restart or journal edit.
        self.rpc.position[6]=self.rpc.now-43200+600
        self.assertFalse(self.due(force=True));self.assertEqual(7,self.k._rebalance_observation_due)

    def test_manual_mode_pending_during_cooldown_does_not_guess_from_secondary(self):
        self.rpc.mode=1;self.rpc.geometry=1;self.rpc.position[6]=self.rpc.now-1
        p=self.projection();self.assertTrue(p['manual_range_exception']);self.assertTrue(p['configuration_pending'])
        self.assertFalse(p['ready_at_snapshot']);self.assertFalse(self.due())
        self.assertIsNone(self.k._rebalance_observation_due)

    def test_mode_pending_after_cooldown_gets_jitter_without_sample_window(self):
        self.rpc.mode=1;self.rpc.geometry=1;self.rpc.gap=0
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.assertFalse(self.due())
        r=self.k.state[PORTFOLIO_STATE_NAMESPACE]['7'];self.assertEqual(self.rpc.now+60,r['execute_after'])
        self.rpc.now+=60;self.assertTrue(self.due(force=True))

    def test_target_only_opposite_and_reference_only_cannot_ready(self):
        for physical,reference in ((2,0),(2,1),(0,2)):
            self.rpc.physical_side,self.rpc.reference=physical,reference
            p=self.projection()
            self.assertFalse(p['ready_at_snapshot']);self.assertEqual(0,p['exit_side'])
            self.assertEqual('threshold_not_met' if not physical else 'reference_disagreement',p['status'])

    def test_unconfigured_confirmation_fails_closed(self):
        self.rpc.gap=0;p=self.projection()
        self.assertEqual('unconfigured',p['status']);self.assertFalse(p['ready_at_snapshot'])

    def test_false_ready_or_contradictory_raw_flag_rejected(self):
        for target,signature in ((self.rpc.contracts['strategy'],'needsRebalance(uint256)'),
                                  (self.rpc.contracts['rebalance_confirmation'],'ready(uint256)')):
            self.rpc.overrides[target,signature]=words(0 if 'needs' in signature else 1)
            with self.subTest(signature=signature),self.assertRaises(ValueError):self.projection()
            self.rpc.overrides.clear()

    def test_sample_maturity_cannot_bypass_hard_interval(self):
        self.rpc.position[6]=self.rpc.now-3600;self.rpc.record=(1,self.rpc.now-600,self.rpc.now-20,2)
        p=self.projection();self.assertTrue(p['sampled_mature']);self.assertFalse(p['ready_at_snapshot'])
        self.k._confirmation_seen_buckets.add(7)
        with patch('keeper.monitor.secrets.randbelow') as draw:self.assertFalse(self.due());draw.assert_not_called()

    def test_exact_five_minute_gap_is_fresh_but_one_second_later_is_stale(self):
        self.rpc.record=(1,self.rpc.now-600,self.rpc.now-300,2)
        self.assertTrue(self.projection()['ready_at_snapshot'])
        self.rpc.record=(1,self.rpc.now-600,self.rpc.now-301,2)
        p=self.projection();self.assertEqual('observation_stale',p['status']);self.assertFalse(p['ready_at_snapshot'])

    def test_ten_minute_maturity_wakes_before_the_next_four_minute_sample(self):
        self.rpc.record=(1,self.rpc.now-480,self.rpc.now,2);self.k._confirmation_seen_buckets.add(7)
        self.assertFalse(self.due())
        self.assertEqual(self.rpc.now+120,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['next_check_at'])

    def test_jitter_is_bounded_durable_and_never_redrawn_for_same_candidate(self):
        self.rpc.record=(1,self.rpc.now-600,self.rpc.now,2);self.k._confirmation_seen_buckets.add(7)
        with patch('keeper.monitor.secrets.randbelow',return_value=240) as draw:
            self.assertFalse(self.due());draw.assert_called_once_with(241)
        first=copy.deepcopy(self.k.state[PORTFOLIO_STATE_NAMESPACE]['7'])
        self.assertEqual(300,first['execute_after']-first['observed_at'])
        self.rpc.now+=30
        with patch('keeper.monitor.secrets.randbelow') as draw:self.assertFalse(self.due());draw.assert_not_called()
        self.assertEqual(first,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7'])
        restored=Keeper(self.cfg,rpc=self.rpc)
        self.assertEqual(first,restored.state[PORTFOLIO_STATE_NAMESPACE]['7'])
        self.assertEqual(300,restored.state['adjustment_jitter_last_v3']['7'])

    def test_next_jitter_draw_cannot_equal_preceding_delay(self):
        self.k.state['adjustment_jitter_last_v3']={'7':60}
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.assertEqual(61,self.k._rebalance_delay(7))
        self.k.state['adjustment_jitter_last_v3']={'7':300}
        with patch('keeper.monitor.secrets.randbelow',return_value=239):self.assertEqual(299,self.k._rebalance_delay(7))

    def test_entrant_idle_and_deposit_growth_do_not_redraw_the_same_candidate(self):
        self.rpc.record=(1,self.rpc.now-600,self.rpc.now,2);self.k._confirmation_seen_buckets.add(7)
        with patch('keeper.monitor.secrets.randbelow',return_value=70):self.due()
        before=copy.deepcopy(self.k.state[PORTFOLIO_STATE_NAMESPACE]['7'])
        self.rpc.position[2]+=10;self.rpc.position[3]+=20;self.rpc.position[4]+=30;self.rpc.now+=30
        with patch('keeper.monitor.secrets.randbelow') as draw:self.assertFalse(self.due());draw.assert_not_called()
        self.assertEqual(before,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7'])

    def test_compound_reference_disagreement_clears_a_known_candidate(self):
        self.rpc.reference=0
        proof=self.physical()
        self.k.state[PORTFOLIO_STATE_NAMESPACE]={'7':{'identity':'0x'+'12'*32,'observed_at':self.rpc.now,
            'last_checked_at':self.rpc.now,'next_check_at':self.rpc.now+240,'execute_after':self.rpc.now+60}}
        with patch.object(self.k,'_compound_policy_status',return_value=proof),patch.object(
                self.k,'_compound_confirmation_record',return_value={'nonempty':True,'side':2}):
            self.assertFalse(self.k._compound_policy_allowed(7))
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7',self.k.state[PORTFOLIO_STATE_NAMESPACE])

    def test_failed_save_cannot_retain_a_new_delay_or_candidate_in_memory(self):
        before=copy.deepcopy(self.k.state)
        row=dict(identity='0x'+'12'*32,observed_at=self.rpc.now,last_checked_at=self.rpc.now,
                 next_check_at=self.rpc.now+240,execute_after=self.rpc.now+60)
        with patch.object(self.k,'save',side_effect=OSError('inert disk fault')),self.assertRaises(OSError):
            self.k._store_rebalance_schedule(7,row)
        self.assertEqual(before,self.k.state)

    def test_return_inside_or_side_reversal_queues_clear_and_removes_jitter(self):
        self.rpc.record=(1,self.rpc.now-600,self.rpc.now,2);self.k._confirmation_seen_buckets.add(7)
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.due()
        self.rpc.now+=60;self.rpc.physical_side=self.rpc.reference=1
        self.assertFalse(self.due(force=True));self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7',self.k.state[PORTFOLIO_STATE_NAMESPACE])

    def test_mode_revision_invalidates_jitter_without_erasing_pending_intent(self):
        self.rpc.mode=1;self.rpc.geometry=1
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.due()
        first=self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['identity']
        self.rpc.policy_revision+=1;self.rpc.fingerprint+=1;self.rpc.now+=1
        self.k.state['pending']={'hash':'preserved-inert-pending'}
        with patch('keeper.monitor.secrets.randbelow',return_value=1):self.assertFalse(self.due(force=True))
        self.assertNotEqual(first,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['identity'])
        self.assertEqual({'hash':'preserved-inert-pending'},self.k.state['pending'])

    def test_historical_namespace_is_not_adopted_by_fresh_reader(self):
        self.k.state[CONFIRMATION_STATE]={'7':dict(identity='0x'+'12'*32,observed_at=self.rpc.now,
            last_checked_at=self.rpc.now,next_check_at=self.rpc.now+240,execute_after=self.rpc.now+60)}
        before=copy.deepcopy(self.k.state[CONFIRMATION_STATE]);self.due()
        self.assertEqual(before,self.k.state[CONFIRMATION_STATE]);self.assertEqual(0,self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['execute_after'])

    def test_pending_recovery_precedes_all_fresh_profile_reads(self):
        self.k.state['pending']={'key':'saved'};before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'poll_pending',return_value=True),patch.object(self.k,'_validate_accounting_version',side_effect=AssertionError('recovery first')):
            self.k.cycle()
        self.assertEqual(before,self.k.state)

    def test_policy_only_validation_checks_budget_even_without_candidate(self):
        self.rpc.overrides[self.rpc.budget,'IDLE_COMPOUNDING_VERSION()']=words(3)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):
            self.k.rebalance_confirmation.validate()

    def test_changed_canonical_confirmation_anchor_is_rejected(self):
        self.rpc.canonical_changed=True
        with self.assertRaises(RpcError):self.status()

    def test_two_physical_legs_are_verified_and_summed_without_requiring_current_mode(self):
        self.rpc.secondary=124;self.rpc.secondary_count=1;self.rpc.summed=(130,240)
        p=self.physical();self.assertEqual(2,len(p['physical_legs']));self.assertEqual(['130','240'],p['portfolio_amounts'])
        self.assertFalse(p['desired_residual_enabled']);self.assertEqual(124,p['secondary_id'])

    def test_secondary_wrong_owner_duplicate_or_missing_accounting_is_rejected(self):
        self.rpc.secondary=124;self.rpc.secondary_count=1;self.rpc.summed=(130,240)
        self.rpc.fail_leg_owner=True
        with self.assertRaises(ValueError):self.physical()
        self.rpc.fail_leg_owner=False;self.rpc.summed=(100,200)
        with self.assertRaises(ValueError):self.physical()
        self.rpc.summed=(130,240);self.rpc.secondary=123
        with self.assertRaises(ValueError):self.physical()

    def test_compound_waits_at_threshold_including_during_cooldown(self):
        self.rpc.position[6]=self.rpc.now-3600
        p=self.physical();self.assertTrue(p['in_range']);self.assertFalse(p['allowed'])
        self.assertEqual('waiting_adjustment_threshold',p['status'])
        self.rpc.physical_side=0;self.assertTrue(self.physical()['allowed'])
        self.rpc.mode=1;self.rpc.geometry=1;self.assertFalse(self.physical()['allowed'])

    def test_harvest_custody_checks_aux_without_market_or_price_reads(self):
        self.rpc.secondary=124;self.rpc.secondary_count=1
        self.k.rpc=PinnedReads(self.rpc,self.rpc.call('eth_getBlockByNumber',['latest',False]))
        reviewer=Review(self.k,{'timestamp':hex(self.rpc.now)},False,simulate=False)
        self.rpc.overrides[self.rpc.contracts['rebalance_confirmation'],'marketSides(uint256)']=RpcError('inert market outage')
        with patch.object(reviewer,'read',side_effect=lambda role,sig,*args,count=1:self.rpc.read(
                self.rpc.contracts.get(role,role),sig,*args,count=count)):
            p=reviewer.harvest_custody({'lp_token_id':123,'pool_id':self.rpc.pool})
        self.assertTrue(p['allowed']);self.assertEqual(2,len(p['physical_legs']))

    def test_fresh_health_binds_policy_runtime_and_explicit_capabilities(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):p=observe_confirmation_health(self.k)
        self.assertEqual('observed_this_cycle',p['state'])
        data={'health_schema':2,'rebalance_confirmation_health':{'version':3,'check_interval_seconds':240,'policy':p}}
        self.assertEqual([],confirmation_reasons(data,self.cfg,now=self.rpc.now,max_age=600))
        p['last_observed']['validated_capabilities']['budget_compounding']=3
        self.assertIn('confirmation_observation_bindings_invalid',confirmation_reasons(data,self.cfg,now=self.rpc.now,max_age=600))

    def test_new_operation_report_explains_inside_range_threshold_and_aggregate_portfolio(self):
        self.rpc.secondary=124;self.rpc.secondary_count=1;self.rpc.summed=(130,240);self.k.save()
        result=review(self.cfg,[7],rpc=self.rpc,now=lambda:self.rpc.now)
        rows={row['operation']:row for row in result['operations']}
        self.assertEqual(1,result['profile']['portfolio_version'])
        self.assertEqual('not_due',rows['rebalance']['state'])
        self.assertEqual(['confirmation_not_started'],rows['rebalance']['reasons'])
        market=rows['rebalance']['checks']['physical_range']['value']
        self.assertTrue(market['in_range']);self.assertEqual(['130','240'],market['portfolio_amounts'])
        self.assertEqual(['waiting_adjustment_threshold'],rows['compound']['reasons'])
        self.assertEqual('observed_eligible',rows['harvest']['state'])

    def test_new_operation_report_shows_confirmation_during_hard_cooldown(self):
        self.rpc.position[6]=self.rpc.now-3600;self.k.save()
        result=review(self.cfg,[7],rpc=self.rpc,now=lambda:self.rpc.now)
        row=next(row for row in result['operations'] if row['operation']=='rebalance')
        self.assertEqual(['hard_rebalance_interval'],row['reasons'])
        self.assertTrue(row['checks']['confirmation']['available'])
        self.assertTrue(row['checks']['confirmation']['value']['threshold_condition_at_snapshot'])
        self.assertFalse(row['checks']['source_observation_enrollment']['paid_window_open'])
        self.assertEqual(self.rpc.position[6]+43200-900,
            row['checks']['source_observation_enrollment']['earliest_paid_observation_at'])

    def test_fresh_execution_reader_and_health_require_the_math_helper_pin(self):
        header=self.rpc.call('eth_getBlockByNumber',['latest',False])
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            execution=self.k._lp_routing_snapshot(header)
            confirmation=observe_confirmation_health(self.k)
        self.assertEqual(2,execution['metadata']['version'])
        self.assertEqual(self.rpc.contracts['lp_balance_math'],execution['metadata']['math_helper'])
        self.assertEqual(self.rpc.pin,execution['runtime_code_hashes']['lp_balance_math'])
        execution.update(head_number=101,observed_at_unix=self.rpc.now,source_files_sha256=self.k.source_files_sha256,
            source_identity_scope='local_files_at_keeper_start_not_runtime_attestation')
        data={'health_schema':2,'rebalance_confirmation_health':{'version':3,'check_interval_seconds':240,'policy':confirmation},
            'lp_execution_health':{'schema':1,'state':'observed_this_cycle','last_confirmed':execution}}
        self.assertEqual([],execution_reasons(data,self.cfg,now=self.rpc.now,max_age=600))
        execution['runtime_code_hashes'].pop('lp_balance_math')
        self.assertIn('execution_observation_runtime_mismatch',execution_reasons(data,self.cfg,now=self.rpc.now,max_age=600))

    def test_report_does_not_advertise_paid_window_for_stopped_or_incompatible_schedule(self):
        for gap,state,reason in ((0,'unconfigured','confirmation_stopped'),
                (239,'blocked','confirmation_source_cadence_incompatible')):
            self.rpc.gap=gap;self.k.save()
            with self.subTest(maximum_gap=gap):
                result=review(self.cfg,[7],rpc=self.rpc,now=lambda:self.rpc.now)
                row=next(row for row in result['operations'] if row['operation']=='rebalance')
                self.assertEqual(state,row['state']);self.assertEqual([reason],row['reasons'])
                enrollment=row['checks']['source_observation_enrollment']
                self.assertFalse(enrollment['cadence_supported'])
                self.assertFalse(enrollment['paid_window_open'])
                self.assertIsNone(enrollment['earliest_paid_observation_at'])

    def test_fresh_missing_math_helper_binding_cannot_fallback_to_router1(self):
        for section in ('contracts','code_hashes'):
            cfg=copy.deepcopy(self.cfg);cfg[section].pop('lp_balance_math')
            with self.subTest(section=section),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
        self.rpc.overrides[self.rpc.contracts['lp_balance_math'],'balancer()']=words(1)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):
            self.k._lp_routing_snapshot(self.rpc.call('eth_getBlockByNumber',['latest',False]))

    def test_manual_geometry_repair_does_not_require_invalid_old_centre_threshold(self):
        self.rpc.manual=1;self.rpc.position[5]=1<<100
        self.rpc.overrides[self.rpc.contracts['rebalance_confirmation'],'marketSides(uint256)']=RpcError('invalid old centre')
        result=self.projection()
        self.assertTrue(result['manual_range_exception']);self.assertTrue(result['ready_at_snapshot'])
        self.assertIsNone(result['physical_threshold_side']);self.assertIsNone(result['reference_threshold_side'])
        self.assertEqual('manual_configuration_exception',result['threshold_observation_scope'])
        proof=self.physical();self.assertFalse(proof['allowed']);self.assertIsNone(proof['threshold_side'])

    def test_fresh_position_executor_runtime_and_parent_cannot_be_omitted(self):
        for section in ('contracts','code_hashes'):
            cfg=copy.deepcopy(self.cfg);cfg[section].pop('lp_position_executor')
            with self.subTest(section=section),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
        self.rpc.overrides[self.rpc.contracts['lp_position_executor'],'liquidityManager()']=words(1)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):
            self.k._lp_routing_snapshot(self.rpc.call('eth_getBlockByNumber',['latest',False]))


if __name__=='__main__':unittest.main()
