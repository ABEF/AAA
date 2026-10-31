"""Fresh schema7 consistency/physical observations; synthetic data only."""
import copy
import importlib.util
import json
import io
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout,redirect_stderr
from unittest.mock import patch

from zzz_ops import production_v4 as Historical
from zzz_ops import production_v5 as P
from zzz_ops import production_observer_v5 as O
from zzz_ops.tick_math import sqrt_price_at_tick
from tests_python import production_v5_fixtures as F

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('portfolio_release_cli',ROOT/'scripts/validate-production-config.py')
CLI=importlib.util.module_from_spec(spec);spec.loader.exec_module(CLI)
spec=importlib.util.spec_from_file_location('portfolio_observer_cli',ROOT/'scripts/observe-production-config.py')
OBS_CLI=importlib.util.module_from_spec(spec);spec.loader.exec_module(OBS_CLI)


class PortfolioProductionTests(unittest.TestCase):
    def setUp(self):
        for context in (patch.object(F.F.old,'HASH',F.RUNTIME),patch.object(P.V,'NATIVE_DEPENDENCIES',{
                role:(a,F.RUNTIME) for role,(a,h) in P.V.NATIVE_DEPENDENCIES.items()})):
            context.start();self.addCleanup(context.stop)
        self.cfg=F.fixture(active=True,residual=True);self.chain=self.cfg['chains'][0]

    def report(self,cfg=None):return P.validate(cfg or self.cfg,expected_commit=F.COMMIT,now=F.NOW)
    def codes(self,cfg=None):return {r['code'] for r in self.report(cfg)['issues']}

    def refresh_physical(self):
        pool=self.chain['pools'][0];price=int(pool['slot0']['sqrt_price_x96'])
        for b in self.chain['holder_exit']['observed']['buckets']:
            portfolio=b['portfolio']
            if not portfolio:continue
            for leg in portfolio['legs']:
                raw=F.F.physical_position(pool,leg['ticks'])
                leg.update(pool_key=raw['lp_pool_key'],position_info=raw['lp_position_info'],
                    amounts=P.physical_amounts(price,leg['ticks'],leg['liquidity']))
            main=portfolio['legs'][0]
            b.update(lp_ticks=main['ticks'],lp_pool_key=main['pool_key'],lp_position_info=main['position_info'])
            stable,execution=P.portfolio_fingerprints(self.chain,pool['pool_id'],portfolio['legs'])
            portfolio.update(fingerprint=stable,execution_fingerprint=execution,
                amounts=[sum(l['amounts'][n] for l in portfolio['legs']) for n in range(2)])

    def test_empty_single_and_two_leg_inventories_are_explicit_and_never_release_approved(self):
        for active,residual in ((False,False),(True,False),(True,True)):
            cfg=F.fixture(active=active,residual=residual);report=self.report(cfg)
            with self.subTest(active=active,residual=residual):
                self.assertTrue(report['inventory_consistent'],report['issues'])
                self.assertEqual({'mint.opensea_unsupported'},self.codes(cfg))
                self.assertFalse(report['ready']);self.assertFalse(report['deployment_authorized'])
                self.assertEqual(20,len(cfg['chains'][0]['helpers']))

    def test_all_fresh_capabilities_are_exact_and_no_legacy_fallback_exists(self):
        for name,value in P.VERSIONS.items():
            cfg=copy.deepcopy(self.cfg);cfg[name]=True
            with self.subTest(name=name):
                self.assertIn('schema.unsupported',self.codes(cfg))
                with self.assertRaises(ValueError):O.observe(cfg,F.RPC(cfg))
        self.assertEqual(6,Historical.VERSIONS['schema_version'])
        self.assertEqual(4,Historical.VERSIONS['accounting_version'])

    def test_schema6_is_historical_not_qualified_by_default_cli(self):
        old=F.F.fixture()
        with patch.object(Historical,'validate',side_effect=AssertionError('Historical engine entered default gate')):
            report=CLI.validate(old,now=F.NOW)
        self.assertEqual(8,report['schema_version']);self.assertFalse(report['ready'])
        self.assertFalse(report.get('inventory_consistent',False));self.assertTrue(report['current_release_gate'])
        with self.assertRaises(ValueError):O.observe(old,F.RPC(self.cfg))

    def test_three_new_helpers_have_exact_parent_dependency_and_runtime_bindings(self):
        for role in ('portfolio_policy','lp_balance_math','lp_position_executor'):
            cfg=copy.deepcopy(self.cfg);cfg['chains'][0]['helpers'].pop(role)
            with self.subTest(role=role):self.assertFalse(self.report(cfg)['inventory_consistent'])
        cfg=copy.deepcopy(self.cfg);cfg['chains'][0]['helpers']['lp_position_executor']['bindings']['liquidityManager']=P.ZERO
        self.assertFalse(self.report(cfg)['inventory_consistent'])
        cfg=copy.deepcopy(self.cfg);cfg['chains'][0]['helpers']['lp_balance_math']['address']=self.chain['modules']['liquidity']['address']
        self.assertIn('binding.alias',self.codes(cfg))

    def test_two_physical_leg_observer_roundtrip_is_pinned_and_preserves_input(self):
        before=copy.deepcopy(self.cfg);rpc=F.RPC(self.cfg)
        with patch('subprocess.run',side_effect=AssertionError('No signer')):observed=O.observe(self.cfg,rpc)
        self.assertEqual(before,self.cfg)
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
        self.assertTrue(self.report(observed)['inventory_consistent'],self.report(observed)['issues'])
        for method,params in rpc.calls:
            self.assertIn(method,{'eth_chainId','eth_getBlockByNumber','eth_call','eth_getCode','eth_getBalance'})
            if method in ('eth_call','eth_getCode','eth_getBalance'):
                self.assertEqual({'blockHash':F.RUNTIME,'requireCanonical':True},params[-1])
        self.assertEqual(before['evidence'],observed['evidence'])

    def test_aggregate_cannot_omit_secondary_or_sum_liquidity_instead_of_amounts(self):
        b=self.chain['holder_exit']['observed']['buckets'][0];p=b['portfolio']
        p['amounts']=list(p['legs'][0]['amounts'])
        self.assertIn('portfolio.aggregate',self.codes())
        p['amounts']=[sum(l['liquidity'] for l in p['legs']),0]
        self.assertIn('portfolio.aggregate',self.codes())

    def test_wrong_owner_empty_liquidity_and_foreign_pool_are_rejected(self):
        for field,value in (('owner',F.F.old.addr(1234)),('liquidity',0),('position_info','0'*64)):
            cfg=copy.deepcopy(self.cfg);leg=cfg['chains'][0]['holder_exit']['observed']['buckets'][0]['portfolio']['legs'][1]
            leg[field]=value
            with self.subTest(field=field):self.assertFalse(self.report(cfg)['inventory_consistent'])

    def test_duplicate_main_secondary_and_extra_third_leg_are_rejected(self):
        p=self.chain['holder_exit']['observed']['buckets'][0]['portfolio'];p['secondary_id']=p['legs'][0]['id']
        self.assertIn('portfolio.association',self.codes())
        p['secondary_id']=100;p['legs'].append(copy.deepcopy(p['legs'][1]))
        self.assertIn('portfolio.leg_inventory',self.codes())

    def test_stable_identity_excludes_liquidity_but_execution_manifest_does_not(self):
        legs=self.chain['holder_exit']['observed']['buckets'][0]['portfolio']['legs'];pool=self.chain['pools'][0]['pool_id']
        before=P.portfolio_fingerprints(self.chain,pool,legs);legs[0]['liquidity']+=1
        after=P.portfolio_fingerprints(self.chain,pool,legs)
        self.assertEqual(before[0],after[0]);self.assertNotEqual(before[1],after[1])
        self.assertIn('portfolio.fingerprint',self.codes())

    def test_disable_request_keeps_live_residual_until_guarded_merge(self):
        p=self.chain['portfolio'];p['policy_revision']+=1
        for row in (p['pools'][0],p['observed']['pools'][0]):row.update(enabled=False,geometry_revision=2)
        p['observed']['policy_revision']=p['policy_revision'];p['observed']['buckets'][0]['configuration_pending']=True
        c=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        c.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=True,range_pending=True,
            ready=True,physical_side=None,reference_side=None,reference_x96=None)
        F.refresh_bindings(self.cfg)
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])
        self.assertEqual(2,len(self.chain['holder_exit']['observed']['buckets'][0]['portfolio']['legs']))
        observed=O.observe(self.cfg,F.RPC(self.cfg))
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])

    def test_half_side_is_default_but_full_side_requires_governance_review(self):
        self.assertEqual(5000,self.chain['portfolio']['pools'][0]['residual_side_bps'])
        self.assertTrue(self.report()['inventory_consistent'])
        policy=self.chain['portfolio'];policy['policy_revision']+=1
        policy['observed']['policy_revision']=policy['policy_revision']
        for row in (policy['pools'][0],policy['observed']['pools'][0]):
            row['residual_side_bps']=10000
        F.refresh_bindings(self.cfg)
        self.assertIn('portfolio.policy_history',self.codes())
        for row in (policy['pools'][0],policy['observed']['pools'][0]):
            row['residual_review_hash']=F.RUNTIME
        F.refresh_bindings(self.cfg)
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])

    def test_enabled_mode_does_not_require_nonzero_residual(self):
        self.cfg=F.fixture(active=True,residual=False);self.chain=self.cfg['chains'][0]
        p=self.chain['portfolio'];p['pools'][0]['enabled']=p['observed']['pools'][0]['enabled']=True
        for row in (p['pools'][0],p['observed']['pools'][0]):row.update(geometry_revision=1,mode_review_hash=F.RUNTIME)
        p['observed']['buckets'][0]['applied_revision']=1
        F.refresh_bindings(self.cfg)
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])

    def test_closed_position_cannot_keep_unaccounted_physical_auxiliary(self):
        b=self.chain['holder_exit']['observed']['buckets'][0]
        b['position'][1]=0;b['position'][7]=4
        for key in ('lp_owner','lp_liquidity','lp_ticks','lp_pool_key','lp_position_info'):b[key]=None
        self.assertIn('portfolio.no_physical',self.codes())

    def test_confirmation_can_accumulate_before_hard_cooldown(self):
        self.chain['holder_exit']['observed']['buckets'][0]['position'][6]=F.NOW-3600
        c=self.chain['rebalance_confirmation']['observed']['buckets'][0];c.update(raw_needed=False,ready=False)
        self.assertEqual(2,c['condition_side'])
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])
        observed=O.observe(self.cfg,F.RPC(self.cfg))
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])

    def test_physical_threshold_and_independent_side_are_recomputed(self):
        c=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        c['physical_side']=1;self.assertIn('confirmation.market_sides',self.codes())
        c['physical_side']=2;c['reference_side']=1
        self.assertIn('confirmation.market_sides',self.codes())

    def test_reference_disagreement_blocks_readiness_not_raw_cooldown_evidence(self):
        c=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        c.update(reference_x96=self.chain['holder_exit']['observed']['buckets'][0]['position'][5],reference_side=0,
            condition_side=0,condition_identity=P.ZERO_HASH,ready=False)
        self.assertTrue(c['raw_needed']);self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])

    def test_inside_main_can_cross_the_85_percent_price_threshold(self):
        self.cfg=F.fixture(active=True);self.chain=self.cfg['chains'][0];pool=self.chain['pools'][0]
        b=self.chain['holder_exit']['observed']['buckets'][0];b['position'][5]=1<<96
        ticks=P.expected_position_ticks(pool,b['position'][5]);b['portfolio']['legs'][0]['ticks']=ticks
        pool['slot0'].update(tick=6000,sqrt_price_x96=str(sqrt_price_at_tick(6000)))
        self.refresh_physical();c=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        c.update(reference_x96=sqrt_price_at_tick(6000),physical_side=2,reference_side=2)
        self.assertTrue(ticks[0]<=6000<ticks[1]);self.assertEqual(2,P.threshold_side(1<<96,ticks,sqrt_price_at_tick(6000),8500))
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])

    def test_strict_gap_source_cadence_and_false_ready_are_not_repaired(self):
        for gap in (0,239,301):
            cfg=copy.deepcopy(self.cfg);c=cfg['chains'][0]['rebalance_confirmation'];c['max_observation_gap']=gap;c['observed']['max_observation_gap']=gap
            with self.subTest(gap=gap):self.assertFalse(self.report(cfg)['inventory_consistent'])
        self.chain['portfolio']['source_check_interval_seconds']=300
        self.assertIn('portfolio.cadence',self.codes())

    def test_policy_fingerprint_and_monotonic_revision_cannot_be_fabricated(self):
        row=self.chain['portfolio']['observed']['pools'][0];row['control_fingerprint']=P.ZERO_HASH
        self.assertIn('portfolio.control_fingerprint',self.codes())
        F.refresh_bindings(self.cfg)
        self.chain['portfolio']['observed']['buckets'][0]['applied_revision']=2
        self.assertIn('portfolio.applied_policy',self.codes())

    def test_missing_physical_read_stays_unavailable_and_does_not_invent_zero(self):
        rpc=F.RPC(self.cfg);target=self.chain['modules']['liquidity']['address']
        rpc.overrides[target,F.F.selector('portfolioAmounts(uint256)')+O.O._word(99)]='0x'
        observed=O.observe(self.cfg,rpc);chain=observed['chains'][0]
        self.assertFalse(chain['observation']['complete']);self.assertIsNone(chain['holder_exit']['observed'])
        self.assertFalse(self.report(observed)['inventory_consistent'])

    def test_new_reference_reader_is_fixed_to_current_oracle_and_inventoried_pair(self):
        observer=O.Observer(F.RPC(self.cfg),copy.deepcopy(self.chain));observer.anchor()
        for target,args in ((self.chain['modules']['liquidity']['address'],(P.ZERO,self.chain['dependencies']['zzz']['address'])),
                (self.chain['modules']['oracle']['address'],(P.ZERO,F.F.old.addr(1234)))):
            with self.subTest(target=target),self.assertRaises(ValueError):observer.read(target,'referenceX96(address,address)',*args)

    def test_manual_old_centre_repair_skips_only_threshold_interpolation(self):
        b=self.chain['holder_exit']['observed']['buckets'][0];b['position'][5]=1<<96
        c=self.chain['rebalance_confirmation']['observed']['buckets'][0]
        c.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=True,range_pending=True,ready=True,
            physical_side=None,reference_side=None,reference_x96=None)
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])
        rpc=F.RPC(self.cfg);helper=self.chain['helpers']['rebalance_confirmation']['address']
        rpc.overrides[helper,F.F.selector('marketSides(uint256)')+O.O._word(7)]='0x'
        observed=O.observe(self.cfg,rpc)
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
        self.assertIsNone(observed['chains'][0]['rebalance_confirmation']['observed']['buckets'][0]['physical_side'])

    def test_historical_cli_requires_explicit_opt_in_and_never_labels_it_current(self):
        cfg=F.F.fixture()
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'input.json';source.write_text(json.dumps(cfg),encoding='utf-8')
            output=io.StringIO()
            with (patch('sys.argv',['validate-production-config.py','--config',str(source),'--historical-consistency']),
                    patch.object(CLI.time,'time',return_value=F.NOW),redirect_stdout(output)):
                status=CLI.main()
            report=json.loads(output.getvalue())
            self.assertEqual(1,status);self.assertFalse(report['current_release_gate'])
            self.assertEqual('historical_manifest_consistency_only',report['approval_scope'])
            self.assertTrue(report['inventory_consistent']);self.assertFalse(report['deployment_authorized'])

    def test_observer_cli_preserves_historical_output_without_explicit_opt_in(self):
        cfg=F.F.fixture()
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'input.json';source.write_text(json.dumps(cfg),encoding='utf-8')
            target=Path(directory)/'observed.json';target.write_text('prior observation',encoding='utf-8')
            args=['--config',str(source),'--rpc-env','POPL_READ_RPC_URL','--output',str(target)]
            with patch.dict(OBS_CLI.os.environ,{'POPL_READ_RPC_URL':'https://inert.example'}),patch.object(
                    OBS_CLI,'Rpc',return_value=F.F.RPC(cfg)),redirect_stderr(io.StringIO()):
                self.assertEqual(1,OBS_CLI.main(args))
            self.assertEqual('prior observation',target.read_text(encoding='utf-8'))
            with patch.dict(OBS_CLI.os.environ,{'POPL_READ_RPC_URL':'https://inert.example'}),patch.object(
                    OBS_CLI,'Rpc',return_value=F.F.RPC(cfg)),redirect_stdout(io.StringIO()):
                self.assertEqual(0,OBS_CLI.main(args+['--historical-consistency']))
            self.assertEqual(6,json.loads(target.read_text(encoding='utf-8'))['schema_version'])

    def test_example_is_current_unqualified_schema8_without_relabelling_schema7(self):
        cfg=json.loads((ROOT/'config/production.example.json').read_text(encoding='utf-8'))
        self.assertEqual(8,cfg['schema_version']);self.assertEqual(21,len(cfg['chains'][0]['helpers']))
        chain=cfg['chains'][0]
        self.assertIsNone(chain['observation']);self.assertIsNone(chain['portfolio']['observed'])
        self.assertIsNone(chain['holder_exit']['observed']);self.assertFalse(self.report(cfg)['ready'])


if __name__=='__main__':unittest.main()
