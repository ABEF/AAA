"""Focused schema6 consistency/observer tests. All RPC data is synthetic."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from zzz_ops import production_v4 as P
from zzz_ops import production_observer_v4 as O
from tests_python import production_v4_fixtures as F

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('holder_exit_release_cli',ROOT/'scripts/validate-production-config.py')
CLI=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(CLI)


class CurrentProductionTests(unittest.TestCase):
    def setUp(self):
        self.runtime=patch.object(F.old,'HASH',F.RUNTIME);self.runtime.start();self.addCleanup(self.runtime.stop)
        self.native=patch.object(P.V,'NATIVE_DEPENDENCIES',{role:(address,F.RUNTIME) for role,(address,_pin) in P.V.NATIVE_DEPENDENCIES.items()})
        self.native.start();self.addCleanup(self.native.stop)
        self.cfg=F.fixture();self.chain=self.cfg['chains'][0]

    def result(self,cfg=None):return P.validate(cfg or self.cfg,expected_commit=F.COMMIT,now=F.NOW)
    def codes(self,cfg=None):return {item['code'] for item in self.result(cfg)['issues']}
    def observe(self,cfg=None):
        cfg=cfg or self.cfg;rpc=F.RPC(cfg);return O.observe(cfg,rpc),rpc

    def test_complete_synthetic_inventory_is_consistent_but_never_primary_mint_ready(self):
        report=self.result()
        self.assertEqual({'mint.opensea_unsupported'},self.codes(),report['issues'])
        self.assertTrue(report['inventory_consistent']);self.assertFalse(report['ready']);self.assertFalse(report['deployment_authorized'])
        self.assertTrue(report['inventory_profile_supported']);self.assertFalse(report['production_qualification_supported'])

    def test_current_observer_composes_into_offline_gate_without_adopting_approval(self):
        before=copy.deepcopy(self.cfg);observed,rpc=self.observe()
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
        self.assertEqual(before,self.cfg);self.assertTrue(self.result(observed)['inventory_consistent'],self.result(observed)['issues'])
        for method,params in rpc.calls:
            self.assertIn(method,{'eth_chainId','eth_getBlockByNumber','eth_call','eth_getCode','eth_getBalance'})
            if method in ('eth_call','eth_getCode','eth_getBalance'):self.assertEqual({'blockHash':F.RUNTIME,'requireCanonical':True},params[-1])
        self.assertEqual(before['evidence'],observed['evidence'])
        self.assertEqual(before['chains'][0]['modules']['vault']['runtime_hash'],observed['chains'][0]['modules']['vault']['runtime_hash'])

    def test_no_retired_royalty_custody_or_timelock_getter_is_read(self):
        _,rpc=self.observe()
        forbidden={F.selector(s) for s in ('custodyAmount(address)','custodyCount()','getMinDelay()','hasRole(bytes32,address)')}
        self.assertFalse(any(method=='eth_call' and params[0]['data'][:10] in forbidden for method,params in rpc.calls))

    def test_each_current_profile_is_explicit_and_bool_is_not_a_version(self):
        for key,value in P.VERSIONS.items():
            for bad in (True,None,value+1):
                with self.subTest(key=key,bad=bad):
                    cfg=copy.deepcopy(self.cfg);cfg[key]=bad
                    self.assertIn('schema.unsupported',self.codes(cfg))
                    with self.assertRaises(ValueError):O.observe(cfg,F.RPC(cfg))

    def test_old_schema_stays_explicit_historical_and_default_does_not_relabel(self):
        old=F.old.fixture();report=CLI.validate(old,now=F.NOW)
        self.assertFalse(report['ready']);self.assertEqual('holder_exit_qualification_pending',report['issues'][0]['code'])
        with self.assertRaises(ValueError):O.observe(old,F.RPC(self.cfg))
        self.assertEqual(6,CLI.validate(self.cfg,now=F.NOW)['schema_version'])

    def test_wrong_runtime_parent_owner_and_forwarded_quality_are_not_approved(self):
        cases=(('helpers','balancing_router','observed_runtime_hash',F.old.addr(999)),
               ('helpers','balancing_router','observed_bindings',{}),('modules','strategy','observed_bindings',{}))
        for group,role,key,value in cases:
            with self.subTest(role=role):
                cfg=copy.deepcopy(self.cfg);cfg['chains'][0][group][role][key]=value
                self.assertFalse(self.result(cfg)['inventory_consistent'])
        self.chain['lp_execution']['observed']['execution_quality']['policy_owner']=F.old.addr(999)
        self.assertIn('execution.observation',self.codes())

    def test_cap_zero_and_ten_percent_do_not_change_total_loss_policy(self):
        for cap in (0,1000):
            cfg=copy.deepcopy(self.cfg);c=cfg['chains'][0];c['lp_execution']['additional_loss_bps']=cap
            c['lp_execution']['observed']=P.execution_expected(c);F.refresh_bindings(cfg)
            self.assertTrue(self.result(cfg)['inventory_consistent'],self.result(cfg)['issues'])
            self.assertEqual(200,c['execution_loss_policy']['contribution_bps'])
        self.chain['lp_execution']['additional_loss_bps']=1001;self.assertIn('integer.invalid',self.codes())

    def test_quality_revision_catalog_and_solver_observations_are_exact(self):
        for key,bad in (('quality_policy_revision',1<<64),('search_iterations',13),('quote_gas_limit',300001),('execution_revision',True)):
            cfg=copy.deepcopy(self.cfg);cfg['chains'][0]['lp_execution'][key]=bad
            self.assertFalse(self.result(cfg)['inventory_consistent'])
        self.chain['lp_execution']['execution_pools']=[self.chain['contribution_pool']]*2
        self.assertIn('execution.catalog',self.codes())

    def test_empty_catalog_reports_swaps_disabled_without_target_fallback(self):
        self.chain['lp_execution']['execution_pools']=[];self.chain['lp_execution']['observed']=P.execution_expected(self.chain)
        self.assertTrue(self.result()['inventory_consistent'],self.result()['issues'])
        observed,_=self.observe();self.assertFalse(observed['chains'][0]['lp_execution']['observed']['swaps_enabled'])

    def test_governed_venue_ceiling_is_current_not_historical_two_percent(self):
        pool=self.chain['pools'][0];pool['maxSlippageBps']=500;pool['observed_config']['maxSlippageBps']=500
        pool['review_evidence']['configuration_sha256']=P.V.configuration_hash(P.V.pool_configuration(self.chain,pool))
        self.assertTrue(self.result()['inventory_consistent'],self.result()['issues'])
        pool['maxSlippageBps']=1001;self.assertIn('integer.invalid',self.codes())

    def test_snapshot_age_future_and_incomplete_observations_fail_closed(self):
        for stamp in (F.NOW+1,F.NOW-601):
            cfg=copy.deepcopy(self.cfg);cfg['chains'][0]['observed_block']['timestamp']=stamp
            self.assertIn('snapshot.stale',self.codes(cfg))
        self.chain['observation']['complete']=False;self.assertIn('observation.incomplete',self.codes())

    def test_reorg_discards_observation_instead_of_publishing_mixed_state(self):
        rpc=F.RPC(self.cfg);rpc.reorg=True
        with self.assertRaisesRegex(ValueError,'anchor changed'):O.observe(self.cfg,rpc)

    def test_failed_quality_read_is_unavailable_and_sanitized(self):
        rpc=F.RPC(self.cfg);rpc.bad=lambda target,data:data==F.selector('executionQualityRevision()')
        observed=O.observe(self.cfg,rpc)
        self.assertFalse(observed['chains'][0]['observation']['complete'])
        self.assertIsNone(observed['chains'][0]['lp_execution']['observed'])
        self.assertNotIn('provider-secret',json.dumps(observed))

    def test_unknown_fields_and_removed_custody_cannot_enter_current_profile(self):
        self.chain['custody']={'recipient_trust_accepted':True};self.assertIn('schema.keys',self.codes())
        self.chain.pop('custody');self.chain['helpers']['royalty_rewards']['observed_bindings']['custodyCount']=0
        self.assertIn('binding.observed',self.codes())

    def test_phase_three_payout_backing_and_current_owners_compose(self):
        F.exited(self.cfg);observed,rpc=self.observe()
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
        self.assertEqual({'mint.opensea_unsupported','release.principal_exit_terminal'},self.codes(observed),self.result(observed)['issues'])
        self.assertTrue(any(method=='eth_getBalance' for method,_ in rpc.calls))

    def test_partial_allocation_prefix_is_conserved(self):
        F.exited(self.cfg,phase=2)
        self.assertEqual({'mint.opensea_unsupported','release.principal_exit_terminal'},self.codes(),self.result()['issues'])

    def test_paid_principal_is_not_repaid_and_remaining_is_exact(self):
        F.exited(self.cfg);e=self.chain['holder_exit']['observed'];n=e['nfts'][0];n['paid']=True;n['claimable']=[0,0]
        e['remaining_eth']-=n['eth'];e['remaining_zzz']-=n['zzz']
        self.assertEqual({'mint.opensea_unsupported','release.principal_exit_terminal'},self.codes(),self.result()['issues'])
        n['claimable']=[n['eth'],n['zzz']];self.assertIn('exit.claimable',self.codes())

    def test_conserved_but_wrong_per_nft_allocations_are_rejected(self):
        F.exited(self.cfg);e=self.chain['holder_exit']['observed'];e['nfts'][0]['eth']+=1;e['nfts'][1]['eth']-=1
        for n in e['nfts']:n['claimable']=[n['eth'],n['zzz']]
        self.assertIn('exit.proportional_allocation',self.codes())

    def test_missing_holder_share_or_bucket_is_not_truncated(self):
        F.exited(self.cfg);e=self.chain['holder_exit']['observed'];e['nfts'].pop()
        self.assertIn('exit.inventory',self.codes());self.assertIn('exit.share_conservation',self.codes())
        e['settlement_buckets']=[];self.assertIn('exit.settlement_inventory',self.codes())

    def test_actual_backing_can_exceed_liability_but_not_fall_below_it(self):
        F.exited(self.cfg);e=self.chain['holder_exit']['observed'];e['balance_eth']=99
        self.assertIn('exit.backing',self.codes());e['balance_eth']=1000
        self.assertNotIn('exit.backing',self.codes())

    def test_phase_flag_cursor_and_share_boundary_contradictions_are_rejected(self):
        for key,value in (('lp_exit_started',False),('allocation_cursor',2),('exit_minted_count',3)):
            cfg=F.exited(copy.deepcopy(self.cfg));cfg['chains'][0]['holder_exit']['observed'][key]=value
            self.assertFalse(self.result(cfg)['inventory_consistent'])

    def test_thousand_nft_allocation_checks_are_bounded_and_conserve_rounding(self):
        F.exited(self.cfg,count=1000)
        self.assertEqual({'mint.opensea_unsupported','release.principal_exit_terminal'},self.codes(),self.result()['issues'])
        self.chain['holder_exit']['observed']['nfts'][999]['reverse_ordinal']=998
        self.assertIn('exit.nft_identity',self.codes())

    def test_malformed_inputs_return_blockers_not_zero_or_ready(self):
        for value in (None,[],{},True):
            report=P.validate(value,now=F.NOW);self.assertFalse(report['ready']);self.assertFalse(report['inventory_consistent'])
        F.exited(self.cfg);self.chain['holder_exit']['observed']['buckets'][0]['settlement'][0]=0
        self.assertFalse(self.result()['inventory_consistent'])

    def test_fabricated_qualified_opensea_service_cannot_add_missing_contract_interface(self):
        self.chain['services']['opensea']['integration']['implementation_profile']='seadrop_v999'
        self.assertIn('mint.opensea_unsupported',self.codes());self.assertIn('mint.implementation_profile',self.codes())

    def test_confirmation_child_is_separately_pinned_and_observed(self):
        F.active(self.cfg);observed,rpc=self.observe()
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
        self.assertTrue(self.result(observed)['inventory_consistent'],self.result(observed)['issues'])
        self.chain['helpers']['rebalance_confirmation']['observed_bindings']['strategy']=F.old.addr(999)
        self.assertIn('binding.observed',self.codes())

    def test_confirmation_requires_an_explicit_gap_not_an_invented_default(self):
        for gap in (None,0,451):
            cfg=copy.deepcopy(self.cfg);c=cfg['chains'][0];c['rebalance_confirmation']['max_observation_gap']=gap
            c['rebalance_confirmation']['observed']['max_observation_gap']=gap;F.refresh_bindings(cfg)
            self.assertIn('confirmation.unconfigured',self.codes(cfg))

    def test_confirmation_pending_stale_side_and_policy_changes_never_become_ready(self):
        for field,value in (('first_seen',F.NOW-899),('last_seen',F.NOW-301),('condition_side',1),('condition_identity',P.ZERO_HASH)):
            cfg=F.active(copy.deepcopy(self.cfg));row=cfg['chains'][0]['rebalance_confirmation']['observed']['buckets'][0];row[field]=value
            self.assertIn('confirmation.ready_view',self.codes(cfg))

    def test_manual_range_exception_retains_raw_eligibility(self):
        F.active(self.cfg);row=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        row.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=True,stored_identity=P.ZERO_HASH,
            first_seen=0,last_seen=0,stored_side=0,ready=True)
        self.assertTrue(self.result()['inventory_consistent'],self.result()['issues'])
        row['raw_needed']=False;self.assertIn('confirmation.raw_required',self.codes())

    def test_confirmation_unavailable_boolean_or_version_is_never_a_fallback(self):
        rpc=F.RPC(self.cfg)
        target=self.chain['helpers']['rebalance_confirmation']['address']
        rpc.overrides[target,F.selector('REBALANCE_CONFIRMATION_VERSION()')]=F.encoded(0)
        observed=O.observe(self.cfg,rpc)
        self.assertFalse(observed['chains'][0]['observation']['complete'])
        self.assertIn('binding.observed',self.codes(observed))

    def test_live_lp_custody_is_verified_separately_from_nft_shares(self):
        F.active(self.cfg);self.chain['holder_exit']['observed']['buckets'][0]['lp_owner']=F.old.addr(999)
        self.assertIn('exit.lp_custody',self.codes())

    def test_observer_work_bound_never_accepts_arbitrary_methods(self):
        rpc=F.RPC(self.cfg);observer=O.Observer(rpc,self.chain)
        with self.assertRaises(ValueError):observer.request('eth_sendRawTransaction',['0x00'])
        observer.read_count=O.MAX_READS
        with self.assertRaises(ValueError):observer.request('eth_chainId',[])

    def test_closing_phase_preserves_parked_principal_without_inventing_payouts(self):
        F.exited(self.cfg,phase=2);e=self.chain['holder_exit']['observed']
        e.update(phase=1,allocation_cursor=0,remaining_buckets=1,remaining_eth=0,remaining_zzz=0)
        e['buckets'][0].update(position=[int(self.chain['contribution_pool'],16),0,100,200,100,2**96,F.NOW-50000,4],settlement=[2,0,0,0,0,0,False])
        for n in e['nfts']:n.update(allocated=False,paid=False,eth=0,zzz=0,claimable=None)
        self.assertEqual({'mint.opensea_unsupported','release.principal_exit_terminal'},self.codes(),self.result()['issues'])
        e['remaining_buckets']=0;self.assertIn('exit.phase',self.codes())

    def test_checked_in_fresh_scaffold_remains_unconfigured_and_blocked(self):
        cfg=json.loads((ROOT/'config/production.holder-exit.example.json').read_text(encoding='utf8'))
        report=P.validate(cfg,now=F.NOW)
        self.assertFalse(report['ready']);self.assertFalse(report['inventory_consistent'])
        self.assertEqual(6,cfg['schema_version']);self.assertEqual(300,cfg['chains'][0]['rebalance_confirmation']['max_observation_gap'])
        self.assertIsNone(cfg['chains'][0]['rebalance_confirmation']['review_hash'])
        self.assertIsNone(cfg['chains'][0]['rebalance_confirmation']['observed'])
        self.assertIn('mint.opensea_unsupported',{i['code'] for i in report['issues']})

    def test_nested_exit_fields_cannot_add_a_retired_recipient_or_override_policy(self):
        for section in ('holder_exit','lp_execution','rebalance_confirmation'):
            cfg=copy.deepcopy(self.cfg);cfg['chains'][0][section]['custody_recipient']=F.old.addr(999)
            self.assertIn('schema.keys',self.codes(cfg))
        F.exited(self.cfg);self.chain['holder_exit']['observed']['nfts'][0]['recipient']=F.old.addr(999)
        self.assertIn('schema.keys',self.codes())

    def test_false_boolean_does_not_stand_in_for_zero_open_findings_or_lifecycle(self):
        for severity in ('critical','high'):
            cfg=copy.deepcopy(self.cfg);cfg['evidence']['independent_audit']['open_'+severity]=False
            self.assertIn('integer.invalid',self.codes(cfg))
        self.chain['canonical_handoff']['state']=False;self.assertIn('canonical.type',self.codes())

    def test_position_precision_and_future_checkpoint_are_not_arbitrary_uint256(self):
        for index,value in ((5,1<<160),(6,1<<64),(6,F.NOW+1)):
            cfg=F.active(copy.deepcopy(self.cfg));cfg['chains'][0]['holder_exit']['observed']['buckets'][0]['position'][index]=value
            self.assertIn('exit.position_precision',self.codes(cfg))

    def test_operating_raw_candidate_cannot_disappear_without_an_identity(self):
        F.active(self.cfg);row=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        row.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=False,ready=False)
        self.assertIn('confirmation.condition',self.codes())

    def test_paused_candidate_cannot_be_ready_but_can_retain_stored_history(self):
        F.active(self.cfg);self.chain['holder_exit']['observed']['paused']=True
        self.assertIn('confirmation.lifecycle',self.codes())
        row=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        row.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=False,ready=False)
        self.assertTrue(self.result()['inventory_consistent'],self.result()['issues'])
        observed,_rpc=self.observe()
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])

    def test_raw_readiness_requires_active_cooled_operations_enabled_principal(self):
        for mode in ('parked','cooldown','disabled'):
            cfg=F.active(copy.deepcopy(self.cfg));chain=cfg['chains'][0]
            if mode=='parked':
                bucket=chain['holder_exit']['observed']['buckets'][0]
                bucket['position'][1]=0;bucket['position'][7]=4;bucket.update(lp_owner=None,lp_liquidity=None)
            elif mode=='cooldown':chain['holder_exit']['observed']['buckets'][0]['position'][6]=F.NOW-1
            else:chain['pools'][0]['operationsEnabled']=False
            self.assertIn('confirmation.raw_position',self.codes(cfg))

    def test_observer_checks_strategy_ready_and_manual_exception_at_same_hash(self):
        for method,value in (('rebalanceReady(uint256)',0),('rangeUpdatePending(uint256)',1)):
            cfg=F.active(copy.deepcopy(self.cfg));rpc=F.RPC(cfg);chain=cfg['chains'][0]
            target=chain['modules']['strategy']['address'];data=F.selector(method)+F.O._word(7)
            rpc.overrides[target,data]=F.encoded(value)
            observed=O.observe(cfg,rpc)
            self.assertFalse(observed['chains'][0]['observation']['complete'])
            self.assertIn({'path':'rebalance_confirmation','code':'confirmation.unavailable'},observed['chains'][0]['observation']['errors'])

    def test_paused_observer_does_not_require_the_manual_exception_dependency(self):
        F.active(self.cfg);self.chain['holder_exit']['observed']['paused']=True
        row=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        row.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=False,ready=False)
        rpc=F.RPC(self.cfg);target=self.chain['modules']['strategy']['address']
        data=F.selector('rangeUpdatePending(uint256)')+F.O._word(7)
        rpc.overrides[target,data]='0x'
        observed=O.observe(self.cfg,rpc)
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])


if __name__=='__main__':unittest.main()
