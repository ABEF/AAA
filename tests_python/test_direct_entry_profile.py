"""Direct Entry3 ABI, full helper verifier and inventory/old-profile boundaries."""
import copy
import unittest
from unittest.mock import patch
from frontend_api.activation_config import ActivationConfig
from frontend_api import activation_trace as T
from frontend_api.service import Projection,ProjectionError,ZERO
from zzz_ops.abi import calldata,decode_words
from zzz_ops import production_v7 as P,production_observer_v7 as O
from tests_python import production_v7_fixtures as F
from tests_python.test_frontend_api import addr
from tests_python.test_protocol_policy_v6 import PolicyTranscript
from tests_python.test_portfolio_activation_bindings import fresh_verifier


def direct_verifier():
    rpc,_old,_old_cfg,read,cfg=fresh_verifier(return_configs=True)
    policy=PolicyTranscript();policy.access=rpc.pins['access'];target=policy.target
    rpc.codes[target]=policy.code;rpc.pins['protocol_policy']=target
    pin=dict(address=target,code_hash=policy.digest)
    cfg['contracts']['protocol_policy']=dict(pin);read['contracts']['protocol_policy']=dict(pin)
    read.update(accounting_version=6,protocol_policy_version=1)
    cfg.update(routing_version=3,review_policy_version=2,portfolio_version=2)
    del cfg['contracts']['v4_executor']
    for source in cfg['sources']:
        source.pop('route_id');source.pop('route_kind')
    for role,method,value in (('entry','ENTRY_ROUTING_VERSION()',3),('entry','REVIEW_POLICY_VERSION()',2),
            ('contribution_pricing','ENTRY_REVIEW_VERSION()',2),('vault','ACCOUNTING_VERSION()',6),
            ('liquidity','PORTFOLIO_VERSION()',2),('strategy','PORTFOLIO_VERSION()',2),('portfolio_policy','PORTFOLIO_VERSION()',2)):
        rpc.put(rpc.pins[role],method,values=(value,))
    rpc.put(rpc.pins['access'],'protocolPolicy()',values=(target,));rpc.put(target,'access()',values=(policy.access,))
    rpc.put(target,'PROTOCOL_POLICY_VERSION()',values=(1,))
    for method,values in policy.values.items():rpc.put(target,method,values=tuple(int(x,16) for x in values))
    p=Projection(read,rpc,clock=lambda:1000)
    return rpc,p,cfg


class DirectEntryABITests(unittest.TestCase):
    def args(self):return (1,'0x'+'11'*32,ZERO,100,'0x'+'0'*64,0,1,1000,False)
    def encode(self,*args,**kw):return T.request_data(*(args or self.args()),routing_version=3,
        review_policy_version=2,maximum_loss_bps=200,expected_contribution_policy='0x'+'22'*32,**kw)
    def test_seven_field_request_plus_two_review_words_and_distinct_selector(self):
        raw=self.encode();words=decode_words('0x'+raw[10:])
        self.assertEqual(9,len(words));self.assertEqual(T.selector(T.EXECUTE_DIRECT_V3),raw[:10])
        self.assertNotEqual(T.selector(T.EXECUTE_REVIEWED_V2),raw[:10])
        self.assertEqual([1,int('11'*32,16),0,100,1,1000,0,200,int('22'*32,16)],[int(x,16) for x in words])
    def test_route_or_conversion_minimum_cannot_be_smuggled_into_direct_request(self):
        for index,value in ((4,'0x'+'1'*64),(5,1),(5,True),(8,1)):
            args=list(self.args());args[index]=value
            with self.subTest(index=index),self.assertRaises(ValueError):self.encode(*args)
    def test_old_routed_abi_remains_explicit_and_unchanged(self):
        raw=T.request_data(*self.args(),routing_version=2,review_policy_version=2,maximum_loss_bps=200,
            expected_contribution_policy='0x'+'22'*32)
        self.assertEqual(T.selector(T.EXECUTE_REVIEWED_V2),raw[:10]);self.assertEqual(11,len(decode_words('0x'+raw[10:])))
    def verify(self,rpc,p,cfg):
        return ActivationConfig(cfg,p).verify(p,{'blockHash':rpc.hash,'requireCanonical':True},[ZERO,addr(21)],timestamp=990)
    def test_direct_config_full_verifier_has_no_entry_executor_or_route_query(self):
        rpc,p,cfg=direct_verifier();pins,prices=self.verify(rpc,p,cfg)
        self.assertNotIn('v4_executor',pins);self.assertEqual({ZERO,addr(21)},set(prices))
        entry=rpc.pins['entry'];seen=[params[0]['data'] for method,params in rpc.calls if method=='eth_call' and params[0]['to']==entry]
        self.assertIn(calldata('ENTRY_ROUTING_VERSION()'),seen);self.assertNotIn(calldata('v4Executor()'),seen)
    def test_direct_config_rejects_removed_source_fields_and_executor_before_reads(self):
        for fault in ('route','kind','executor','old_accounting'):
            rpc,p,cfg=direct_verifier()
            if fault=='route':cfg['sources'][0]['route_id']='0x'+'0'*64
            elif fault=='kind':cfg['sources'][0]['route_kind']=0
            elif fault=='executor':cfg['contracts']['v4_executor']=dict(address=addr(999),code_hash='0x'+'1'*64)
            else:p.accounting_version=5
            before=len(rpc.calls)
            with self.subTest(fault=fault),self.assertRaises(ValueError):ActivationConfig(cfg,p)
            self.assertEqual(before,len(rpc.calls))
    def test_entry_version_or_runtime_mismatch_never_uses_routed_fallback(self):
        for fault in ('version','missing','runtime'):
            rpc,p,cfg=direct_verifier();entry=rpc.pins['entry']
            if fault=='version':rpc.put(entry,'ENTRY_ROUTING_VERSION()',values=(2,))
            elif fault=='missing':rpc.responses[entry,calldata('ENTRY_ROUTING_VERSION()')]='0x'
            else:rpc.codes[entry]='0x6000'
            with self.subTest(fault=fault),self.assertRaises((ProjectionError,ValueError)):self.verify(rpc,p,cfg)


class DirectEntryInventoryTests(unittest.TestCase):
    def setUp(self):
        for context in (patch.object(F.H.H.F.old,'HASH',F.RUNTIME),patch.object(P.V,'NATIVE_DEPENDENCIES',{
                role:(a,F.RUNTIME) for role,(a,_h) in P.V.NATIVE_DEPENDENCIES.items()})):
            context.start();self.addCleanup(context.stop)
        self.cfg=F.fixture()
    def result(self,cfg=None):return P.validate(cfg or self.cfg,expected_commit=F.COMMIT,now=F.NOW)
    def test_schema9_has_twenty_helpers_and_preserves_both_reward_executors(self):
        r=self.result();self.assertTrue(r['inventory_consistent'],r['issues']);self.assertFalse(r['ready'])
        helpers=self.cfg['chains'][0]['helpers'];self.assertEqual(20,len(helpers))
        self.assertNotIn('entry_v4_executor',helpers)
        self.assertIn('lp_v4_executor',helpers);self.assertIn('royalty_v4_executor',helpers)
        self.assertEqual({'mint.opensea_unsupported'},{i['code'] for i in r['issues']})
    def test_observer_roundtrip_reads_new_abi_without_modifying_input(self):
        original=copy.deepcopy(self.cfg);rpc=F.RPC(self.cfg);seen=O.observe(self.cfg,rpc)
        self.assertEqual(original,self.cfg);self.assertTrue(seen['chains'][0]['observation']['complete'],seen['chains'][0]['observation']['errors'])
        self.assertTrue(self.result(seen)['inventory_consistent'],self.result(seen)['issues'])
    def test_schema8_and_misdeclared_capabilities_never_promote(self):
        class NoRPC:
            def call(self,*args):raise AssertionError('Profile validation must precede RPC')
        for key in P.VERSIONS:
            bad=copy.deepcopy(self.cfg);bad[key]=True
            with self.subTest(key=key):
                self.assertFalse(self.result(bad)['inventory_consistent'])
                with self.assertRaises(ValueError):O.observe(bad,NoRPC())
    def test_removed_entry_routes_or_helper_are_not_admitted(self):
        for fault in ('source','descriptor','helper','binding'):
            bad=copy.deepcopy(self.cfg);chain=bad['chains'][0]
            if fault=='source':chain['activation_sources'][0]['route_kind']=2
            elif fault=='descriptor':chain['conversion_routes'].append({'role':'entry'})
            elif fault=='helper':chain['helpers']['entry_v4_executor']={}
            else:chain['helpers']['activation_entry']['observed_bindings']['ENTRY_ROUTING_VERSION']=2
            with self.subTest(fault=fault):self.assertFalse(self.result(bad)['inventory_consistent'])
