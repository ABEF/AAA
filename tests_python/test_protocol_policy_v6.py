"""Scoped mutable-policy integration: synthetic pinned RPC, no live signing."""
import copy
import unittest
from frontend_api.activation_config import ActivationConfig
from frontend_api.activation_trace import request_data,selector,EXECUTE_REVIEWED_V2,EXECUTE_REVIEWED
from frontend_api.service import Projection,ProjectionError
from frontend_api.portfolio_v6 import verify_profile
from tests_python.test_frontend_api import addr,configuration
from tests_python.test_frontend_portfolio_v5 import ProfileTranscript
from tests_python.test_portfolio_activation_bindings import fresh_verifier
from zzz_ops.abi import keccak256
from zzz_ops.protocol_policy import observe,DOMAINS


class PolicyTranscript:
    def __init__(self):
        self.target=addr(500);self.access=addr(1);self.values={};self.calls=[]
        self.code='0x600001';self.digest='0x'+keccak256(bytes.fromhex(self.code[2:])).hex()
        self.set('entry',(150*10**18,8*10**18,1500,2))
        self.set('maintenance',(1700,3));self.set('gas',(180000,500000,250000,1))
        self.set('sale',(7*10**16,int(addr(900),16),0,9))
        self.set('metadata',(2000*10**18,20000*10**18,4))
    def set(self,domain,values):
        getter,fingerprint,_names,_widths=DOMAINS[domain]
        raw=[f'{value:064x}' for value in values]
        self.values[getter]=raw
        self.values[fingerprint]=[keccak256(bytes.fromhex(f'{int(self.target,16):064x}'+''.join(raw))).hex()]
    def read(self,target,method,*args,count=1):
        self.calls.append((target,method,args,count))
        if target==self.access and method=='protocolPolicy()':return [f'{int(self.target,16):064x}']
        if target!=self.target:raise AssertionError('Unexpected policy target')
        if method=='PROTOCOL_POLICY_VERSION()':return [f'{1:064x}']
        if method=='access()':return [f'{int(self.access,16):064x}']
        return self.values[method]
    def observe(self,domain='entry',**kwargs):
        return observe(self.read,policy=self.target,access=self.access,domain=domain,**kwargs)


def fresh6_verifier():
    rpc,old,previous=fresh_verifier();cfg=copy.deepcopy(rpc.config)
    # fresh_verifier deliberately does not mutate its historical config object.
    cfg.update(maintenance_policy_version=3,lp_routing_version=2,execution_quality_version=1,
        rebalance_confirmation_version=3,portfolio_version=2,review_policy_version=2)
    cfg['contracts']={k:dict(address=v.address,code_hash=v.code_hash) for k,v in previous.contracts.items()}
    policy=PolicyTranscript();policy.access=old.contracts['access'].address
    rpc.codes[policy.target]=policy.code;rpc.pins['protocol_policy']=policy.target
    cfg['contracts']['protocol_policy']=dict(address=policy.target,code_hash=policy.digest)
    read=configuration();read.update(accounting_version=6,fee_intake_version=1,protocol_policy_version=1)
    read['contracts']={k:dict(address=v.address,code_hash=v.code_hash) for k,v in old.contracts.items()}
    read['contracts']['protocol_policy']=dict(cfg['contracts']['protocol_policy'])
    read['assets']=[read['assets'][0],dict(address=addr(21),decimals=18,symbol='ZZZ',code_hash=rpc.digest(addr(21)))]
    for role,method,value in (('vault','ACCOUNTING_VERSION()',6),('liquidity','PORTFOLIO_VERSION()',2),
            ('strategy','PORTFOLIO_VERSION()',2),('portfolio_policy','PORTFOLIO_VERSION()',2),
            ('entry','REVIEW_POLICY_VERSION()',2),('contribution_pricing','ENTRY_REVIEW_VERSION()',2)):
        rpc.put(rpc.pins[role],method,values=(value,))
    rpc.put(policy.access,'protocolPolicy()',values=(policy.target,))
    rpc.put(policy.target,'access()',values=(policy.access,))
    rpc.put(policy.target,'PROTOCOL_POLICY_VERSION()',values=(1,))
    for method,raw in policy.values.items():rpc.put(policy.target,method,values=tuple(int(w,16) for w in raw))
    p=Projection(read,rpc,clock=lambda:1000)
    return rpc,p,ActivationConfig(cfg,p),policy,read,cfg


class ProtocolPolicyV6Tests(unittest.TestCase):
    def test_each_domain_recomputes_abi_fingerprint_and_exact_large_amounts(self):
        p=PolicyTranscript()
        for domain in DOMAINS:
            result=p.observe(domain,code=lambda target:p.code,expected_code_hash=p.digest)
            self.assertEqual(domain,result['domain']);self.assertEqual(1,result['version'])
        self.assertEqual(150*10**18,p.observe()['minimum_activation_usd_18'])
        self.assertEqual(addr(900),p.observe('sale')['recipient'])

    def test_parent_runtime_fingerprint_and_abi_width_fail_closed(self):
        for fault in ('runtime','fingerprint','overflow','zero_revision','malformed','wrong_controller'):
            p=PolicyTranscript();kwargs={}
            if fault=='runtime':kwargs=dict(code=lambda target:'0x6000',expected_code_hash=p.digest)
            elif fault=='fingerprint':p.values['entryFingerprint()']=['a'*64]
            elif fault=='overflow':p.set('entry',(2**128,10**18,0,1))
            elif fault=='zero_revision':p.set('entry',(10**18,10**18,0,0))
            elif fault=='malformed':p.values['entryPolicy()']=['0x1']
            else:p.access=addr(999);old=p.read;p.read=lambda target,method,*args,count=1: ['0'*64] if method=='access()' else old(target,method,*args,count=count)
            with self.subTest(fault=fault),self.assertRaises(ValueError):p.observe(**kwargs)

    def test_domain_boundaries_reject_policy_that_source_cannot_configure(self):
        for domain,values in (('entry',(99,10**18,500,1)),('entry',(10**18,2*10**18,500,1)),
                ('entry',(10**18,10**18,4001,1)),('maintenance',(4001,1)),
                ('gas',(99999,500000,250000,1)),('sale',(0,1,0,1)),('metadata',(100,100,1))):
            p=PolicyTranscript();p.set(domain,values)
            with self.subTest(domain=domain,values=values),self.assertRaises(ValueError):p.observe(domain)

    def test_metadata_and_sale_change_do_not_invalidate_entry_fingerprint(self):
        p=PolicyTranscript();before=p.observe()['fingerprint']
        p.set('metadata',(3000*10**18,40000*10**18,8));p.set('sale',(9*10**16,3,0,10))
        self.assertEqual(before,p.observe()['fingerprint'])
        p.set('entry',(200*10**18,10*10**18,500,3));self.assertNotEqual(before,p.observe()['fingerprint'])

    def test_review2_exact_selector_commits_entry_policy_and_rejects_missing_or_old_adoption(self):
        args=(1,'0x'+'2'*64,addr(3),10**24,'0x'+'0'*64,0,1,1000,False)
        fingerprint='0x'+'4'*64
        data=request_data(*args,review_policy_version=2,maximum_loss_bps=200,expected_contribution_policy=fingerprint)
        self.assertTrue(data.startswith(selector(EXECUTE_REVIEWED_V2)));self.assertEqual(10+11*64,len(data))
        self.assertTrue(data.endswith(fingerprint[2:]));self.assertNotEqual(data[:10],selector(EXECUTE_REVIEWED))
        for revision,fp in ((2,None),(2,'0x'+'0'*64),(2,'0x1'),(1,fingerprint),(0,fingerprint)):
            with self.subTest(revision=revision,fp=fp),self.assertRaises(ValueError):
                request_data(*args,review_policy_version=revision,maximum_loss_bps=200,expected_contribution_policy=fp)

    def test_fresh6_read_configuration_requires_explicit_policy_pin_and_version(self):
        rpc,p,cfg,policy,raw,activation=fresh6_verifier()
        self.assertEqual(6,p.accounting_version);self.assertEqual(2,cfg.portfolio_version);self.assertEqual(2,cfg.review_policy_version)
        for key in ('protocol_policy_version',):
            bad=copy.deepcopy(raw);bad.pop(key)
            with self.assertRaises(ValueError):Projection(bad,rpc)
        bad=copy.deepcopy(raw);bad['contracts'].pop('protocol_policy')
        with self.assertRaises(ValueError):Projection(bad,rpc)
        for key,value in (('portfolio_version',1),('review_policy_version',1)):
            bad=copy.deepcopy(activation);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):ActivationConfig(bad,p)

    def test_actual_activation_verifier_authenticates_entry2_policy_and_rejects_drift(self):
        rpc,p,cfg,policy,_,_=fresh6_verifier();block={'blockHash':rpc.hash,'requireCanonical':True};observation={}
        cfg.verify(p,block,[addr(21)],timestamp=990,execution_observation=observation)
        self.assertEqual(2,observation['portfolio_version']);self.assertEqual(2,observation['rebalance_confirmation_policy']['portfolio_version'])
        for fault in ('runtime','fingerprint','entry_version'):
            rpc,p,cfg,policy,_,_=fresh6_verifier()
            if fault=='runtime':rpc.codes[policy.target]='0x6000'
            elif fault=='fingerprint':rpc.put(policy.target,'entryFingerprint()',values=(5,))
            else:rpc.put(rpc.pins['entry'],'REVIEW_POLICY_VERSION()',values=(1,))
            with self.subTest(fault=fault),self.assertRaises(ProjectionError):cfg.verify(p,block,[addr(21)],timestamp=990)

    def test_actual_preparation_rejects_below_new_growth_minimum_before_approval_or_trace(self):
        from frontend_api.activation import ActivationTransactions,ActivationInputError
        rpc,p,cfg,policy,_,raw=fresh6_verifier()
        rpc.put(p.contracts['handoff'].address,'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6').hex(),))
        rpc.put(p.contracts['principal_exit'].address,'CUSTODY_VERSION()',values=(4,))
        policy.set('entry',(150*10**18,101*10**18,1500,3))
        for method in ('entryPolicy()','entryFingerprint()'):
            rpc.put(policy.target,method,values=tuple(int(w,16) for w in policy.values[method]))
        service=ActivationTransactions(p,raw)
        with self.assertRaises(ActivationInputError):service.prepare(rpc.request)
        self.assertEqual(0,rpc.trace_count)

    def test_profile6_checks_new_policy_parent_without_old_noarg_allocation_getters(self):
        p=ProfileTranscript();p.contracts['protocol_policy']=type(next(iter(p.contracts.values())))(addr(500),'0x'+'a'*64)
        p.values['vault','ACCOUNTING_VERSION()',()]=6
        for role in ('strategy','liquidity','portfolio_policy'):p.values[role,'PORTFOLIO_VERSION()',()]=2
        p.values['protocol_policy','PROTOCOL_POLICY_VERSION()',()]=1
        p.values['protocol_policy','access()',()]=int(p.contracts['access'].address,16)
        p.values['access','protocolPolicy()',()]=500
        verify_profile(p,p.block)
        self.assertFalse(any(method in ('minimumMainBps()','maximumResidualBps()') for _,method,_,_ in p.calls))
        p.values['access','protocolPolicy()',()]=501
        with self.assertRaises(ProjectionError):verify_profile(p,p.block)
