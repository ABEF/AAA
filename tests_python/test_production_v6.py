"""Current policy inventory and observer adversarial boundary tests."""
import copy
import unittest
from unittest.mock import patch
from zzz_ops import production_v6 as P,production_observer_v6 as O
from tests_python import production_v6_fixtures as F

class PolicyProductionV6Tests(unittest.TestCase):
    def setUp(self):
        for context in (patch.object(F.H.F.old,'HASH',F.RUNTIME),patch.object(P.V,'NATIVE_DEPENDENCIES',{
                role:(a,F.RUNTIME) for role,(a,h) in P.V.NATIVE_DEPENDENCIES.items()})):
            context.start();self.addCleanup(context.stop)
        self.cfg=F.fixture()
    def result(self,cfg=None):return P.validate(cfg or self.cfg,expected_commit=F.COMMIT,now=F.NOW)
    def test_exact_schema8_twentyone_helpers_never_approve_release(self):
        r=self.result();self.assertTrue(r['inventory_consistent'],r['issues'])
        self.assertEqual(21,len(self.cfg['chains'][0]['helpers']))
        self.assertEqual({'mint.opensea_unsupported'},{i['code'] for i in r['issues']})
        self.assertFalse(r['ready']);self.assertFalse(r['deployment_authorized'])
    def test_all_version_fields_reject_bool_and_old_profile(self):
        for name in P.VERSIONS:
            cfg=copy.deepcopy(self.cfg);cfg[name]=True
            with self.subTest(name=name):
                self.assertFalse(self.result(cfg)['inventory_consistent'])
                with self.assertRaises(ValueError):O.observe(cfg,F.RPC(cfg))
    def test_policy_fingerprint_bounds_parent_and_runtime_are_not_guessed(self):
        for fault in ('fingerprint','idle','revision','parent','runtime'):
            cfg=copy.deepcopy(self.cfg);chain=cfg['chains'][0]
            if fault=='fingerprint':chain['protocol_policy']['entry']['fingerprint']='0x'+'a'*64
            elif fault=='idle':chain['protocol_policy']['entry']['maximum_idle_bps']=4001
            elif fault=='revision':chain['protocol_policy']['entry']['revision']=True
            elif fault=='parent':chain['helpers']['protocol_policy']['bindings']['access']=P.ZERO
            else:chain['helpers']['protocol_policy']['observed_runtime_hash']='0x'+'a'*64
            with self.subTest(fault=fault):self.assertFalse(self.result(cfg)['inventory_consistent'])
    def test_real_observer_roundtrip_reads_scoped_policy_and_perpool_allocation(self):
        before=copy.deepcopy(self.cfg);rpc=F.RPC(self.cfg);observed=O.observe(self.cfg,rpc)
        self.assertEqual(before,self.cfg)
        self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
        r=self.result(observed);self.assertTrue(r['inventory_consistent'],r['issues'])
        for method,params in rpc.calls:
            if method in ('eth_call','eth_getCode','eth_getBalance'):self.assertEqual({'blockHash':F.RUNTIME,'requireCanonical':True},params[-1])
            if method=='eth_call':self.assertNotEqual(F.H.F.selector('PAYOUT_GAS()'),params[0]['data'])
    def test_missing_policy_and_wrong_live_revision_leave_incomplete_observation(self):
        for fault in ('binding','revision'):
            cfg=copy.deepcopy(self.cfg);rpc=F.RPC(cfg)
            target=cfg['chains'][0]['helpers']['protocol_policy']['address']
            key='access()' if fault=='binding' else 'entryFingerprint()'
            rpc.overrides[target,F.H.F.selector(key)]=F.H.F.encoded(999)
            observed=O.observe(cfg,rpc)
            with self.subTest(fault=fault):
                self.assertFalse(observed['chains'][0]['observation']['complete'])
                self.assertFalse(self.result(observed)['inventory_consistent'])
