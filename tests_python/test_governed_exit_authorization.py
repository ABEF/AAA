"""Custody5 authority/profile and reward-read regressions; synthetic RPCs only."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from frontend_api.service import Projection,ProjectionError
from keeper.principal import PrincipalDistribution
from tests_python import test_frontend_policy_v6 as policy_fixture
from tests_python.test_portfolio_lineage_admission import configuration as lineage_config
from tests_python import production_v7_fixtures as F
from zzz_ops import production_v8 as P,production_observer_v8 as O

class GovernedExitReads(unittest.TestCase):
    def setUp(self):
        self.base=policy_fixture.FrontendPolicyV6Tests();self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.cfg=copy.deepcopy(self.base.config);self.cfg['custody_version']=5
        self.rpc=self.base.rpc;self.exit=self.cfg['contracts']['principal_exit']['address']
        self.rpc.put(self.exit,'CUSTODY_VERSION()',values=(5,))
    def projection(self,cfg=None):return Projection(cfg or self.cfg,self.rpc,clock=lambda:1000)
    def test_explicit_custody5_preserves_owner_and_funded_reward_reads_during_price_outage(self):
        self.base.base.outage();result=self.projection().nft(self.rpc.nft_id)
        self.assertEqual('0x'+'0'*38+'1e',result['owner'])
        self.assertFalse(result['position']['current_lp_value']['available'])
        self.assertEqual('17',result['claimable']['lp'][0]['raw'])
        self.assertEqual('33333333333333333333',result['claimable']['royalties'][0]['raw'])
    def test_missing_old_or_boolean_custody_labels_never_adopt_new_runtime(self):
        for value in (None,4):
            bad=copy.deepcopy(self.cfg)
            if value is None:bad.pop('custody_version')
            else:bad['custody_version']=value
            with self.subTest(value=value),self.assertRaises(ProjectionError):self.projection(bad).nft(self.rpc.nft_id)
        for value in (True,'5',0,3,6):
            bad=copy.deepcopy(self.cfg);bad['custody_version']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.projection(bad)
    def test_new_config_rejects_old_runtime_and_historical_default_remains_four(self):
        self.rpc.put(self.exit,'CUSTODY_VERSION()',values=(4,))
        with self.assertRaises(ProjectionError):self.projection().nft(self.rpc.nft_id)
        old=copy.deepcopy(self.cfg);old.pop('custody_version');self.assertEqual(4,self.projection(old).custody_version)
        self.assertEqual('17',self.projection(old).nft(self.rpc.nft_id)['claimable']['lp'][0]['raw'])
    def test_lineage_requires_explicit_peer_custody_and_never_inherits_successor_five(self):
        cfg,rpc=lineage_config(6);cfg['custody_version']=5
        with self.assertRaises(ValueError):Projection(cfg,rpc,clock=lambda:1000)
        cfg['predecessors'][0]['custody_version']=4;p=Projection(cfg,rpc,clock=lambda:1000)
        self.assertEqual(5,p.custody_version);self.assertEqual(4,p.lineage.entries[0].projection.custody_version)

class GovernedExitKeeper(unittest.TestCase):
    def worker(self,enabled,pending=False):
        return SimpleNamespace(config={'principal_distribution':{'enabled':enabled}},
            state={'pending':{'hash':'0x'+'1'*64}} if pending else {},custody_version=5,accounting_version=6)
    def test_keeper_cannot_enable_governance_principal_batches_but_disabled_is_valid(self):
        with self.assertRaisesRegex(ValueError,'governance-only'):PrincipalDistribution(self.worker(True))
        task=PrincipalDistribution(self.worker(False));self.assertTrue(task.configured);self.assertFalse(task.enabled)
    def test_existing_pending_recovery_is_not_blocked_by_new_distribution_config(self):
        task=PrincipalDistribution(self.worker(True,pending=True));self.assertFalse(task.configured)
        with self.assertRaisesRegex(ValueError,'governance-only'):task.configure()

class GovernedExitInventory(unittest.TestCase):
    def setUp(self):
        for context in (patch.object(F.H.H.F.old,'HASH',F.RUNTIME),patch.object(P.V,'NATIVE_DEPENDENCIES',{
                role:(a,F.RUNTIME) for role,(a,_h) in P.V.NATIVE_DEPENDENCIES.items()})):
            context.start();self.addCleanup(context.stop)
        self.cfg=F.fixture();self.cfg.update(P.VERSIONS);chain=self.cfg['chains'][0]
        for group,records in P.expected_bindings(chain).items():
            for role,values in records.items():
                chain[group][role]['observed_bindings']=copy.deepcopy(values)
                if group=='helpers':chain[group][role]['bindings']=copy.deepcopy(values)
        for role,profile in P.SERVICE_PROFILES.items():
            chain['services'][role]['profile']=profile;chain['services'][role]['evidence']['profile']=profile
    def result(self,cfg=None):return P.validate(cfg or self.cfg,expected_commit=F.COMMIT,now=F.NOW)
    def test_fresh_inventory_observer_reads_custody5_without_rewriting_historical_or_entry_wire(self):
        result=self.result();self.assertTrue(result['inventory_consistent'],result['issues']);self.assertFalse(result['ready'])
        self.assertEqual(20,len(self.cfg['chains'][0]['helpers']))
        rpc=F.RPC(self.cfg);rpc.expected=P.expected_bindings(rpc.chain);old=copy.deepcopy(self.cfg)
        seen=O.observe(self.cfg,rpc);self.assertEqual(old,self.cfg)
        self.assertTrue(seen['chains'][0]['observation']['complete'],seen['chains'][0]['observation']['errors'])
        self.assertTrue(self.result(seen)['inventory_consistent'],self.result(seen)['issues'])
    def test_schema9_old_custody_or_wrong_observation_cannot_qualify_new_profile(self):
        class NoRPC:
            def call(self,*args):raise AssertionError('No RPC before profile rejection')
        for key,value in (('schema_version',9),('custody_version',4),('custody_version',True)):
            bad=copy.deepcopy(self.cfg);bad[key]=value
            with self.subTest(key=key,value=value):
                self.assertFalse(self.result(bad)['inventory_consistent'])
                with self.assertRaises(ValueError):O.observe(bad,NoRPC())
        bad=copy.deepcopy(self.cfg);bad['chains'][0]['modules']['migration']['observed_bindings']['CUSTODY_VERSION']=4
        self.assertFalse(self.result(bad)['inventory_consistent'])
    def test_old_keeper_service_profile_cannot_be_relabelled_as_governance_distribution(self):
        bad=copy.deepcopy(self.cfg);profile=F.P.SERVICE_PROFILES['keeper']
        bad['chains'][0]['services']['keeper']['profile']=profile
        self.assertFalse(self.result(bad)['inventory_consistent'])
