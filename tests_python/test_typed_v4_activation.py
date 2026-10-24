"""Pinned typed-v4 preparation fixtures, not real-provider qualification."""
import copy
import unittest

from frontend_api.activation import ActivationTransactions, ActivationInputError
from frontend_api.activation_config import ActivationConfig, ZERO_HASH, NATIVE_ASSET_CODE_HASH
from frontend_api.activation_trace import CONFIGURABLE_RESULT, RESULT, selector
from frontend_api.activation_v4 import DOMAIN, route_output
from frontend_api.service import Projection, ProjectionError, ZERO
from tests_python.test_frontend_api import configuration, addr, words
from tests_python.test_frontend_activation import ActivationRPC, USD
from tests_python.test_native_backend_boundary import NativeActivationRPC
from zzz_ops.abi import calldata, decode_words, keccak256


class TypedActivationRPC(NativeActivationRPC):
    def __init__(self, *, routed=True, loss=100, native_source=False, **options):
        super().__init__(**options)
        self.loss=loss; self.routed=routed; self.output=addr(21) if native_source else ZERO
        self.config['routing_version']=2
        helper=addr(90); self.pins['v4_executor']=helper
        self.codes[helper]='0x600090'
        self.config['contracts']['v4_executor']={'address':helper,'code_hash':self.digest(helper)}
        self.put(helper,'parent()',values=(self.pins['entry'],))
        self.put(self.pins['entry'],'v4Executor()',values=(helper,))
        self.put(self.pins['budget'],'MAX_LOSS_BPS()',values=(1000,))
        self.put(self.pins['budget'],'contributionLossBps()',values=(loss,))
        source=addr(22) if routed and not native_source else ZERO
        self.source=source; self.request['source_asset']=source
        policy='0x'+'d'*64
        if routed:
            self.native_put(self.pins['activation_assets'],'activePolicy(address)',(source,),(policy,))
            source_hash=NATIVE_ASSET_CODE_HASH if source==ZERO else self.digest(source)
            self.put(self.pins['activation_assets'],'policies(bytes32)',(policy,),
                     (source,1,source_hash,'0x'+'e'*64,18,1))
            self.native_put(self.pins['activation_assets'],'value(address,uint256)',(source,self.original_amount),(100*USD,))
            manager,state=self.pins['pool_manager'],self.pins['state_view']
            output_hash=NATIVE_ASSET_CODE_HASH if self.output==ZERO else self.digest(self.output)
            self.v4_values=[source,self.output,min(source,self.output),max(source,self.output),500,10,ZERO,manager,state,
                            source_hash,output_hash,self.digest(manager),self.digest(state),'0x'+'f'*64]
            encoded=bytes.fromhex(words(*self.v4_values)[2:])
            self.route='0x'+keccak256(DOMAIN+(31337).to_bytes(32,'big')+int(helper,16).to_bytes(32,'big')+
                                         int(self.pins['entry'],16).to_bytes(32,'big')+encoded).hex()
            for target,signature in ((self.pins['entry'],'v4Route(bytes32)'),(helper,'route(bytes32)'),(helper,'validate(bytes32)')):
                self.put(target,signature,(self.route,),self.v4_values)
            self.put(self.pins['entry'],'routeKind(bytes32)',(self.route,),(2,))
            for method in ('routeExists(bytes32)','routeEnabled(bytes32)'):
                self.put(self.pins['entry'],method,(self.route,),(1,))
            pool='0x'+keccak256(bytes.fromhex(words(*self.v4_values[2:7])[2:])).hex()
            self.put(state,'getSlot0(bytes32)',(pool,),(2**96,0,0,500))
        else:self.route=ZERO_HASH
        self.config['sources']=[dict(pool_id=self.pool,source_asset=source,route_id=self.route,
                                    asset_policy_id=policy,route_kind=2 if routed else 0)]

    def trace(self,tx):
        mutation=self.trace_mutation;self.trace_mutation=None
        result=ActivationRPC.trace(self,tx)
        self.trace_mutation=mutation
        values=[int(w,16) for w in decode_words('0x'+tx['data'][10:])]
        nft,_,_,amount,_,minimum,_,deadline,_=values
        acquired=amount-amount//1000 if self.routed else amount
        vault=result['calls'][0];vault['value']=hex(acquired if self.output==ZERO else 0)
        if self.output!=ZERO:
            arguments=decode_words('0x'+vault['input'][10:]);offset=1 if values[-1] else 2
            arguments[offset]='0'*64;arguments[offset+1]=f'{acquired:064x}'
            vault['input']=vault['input'][:10]+''.join(arguments)
        mint,budget=vault['calls']
        params=decode_words('0x'+mint['input'][10:])
        mint['value']=hex(int(params[3 if self.new_pool else 2],16))
        packed=list(self.economics);packed[-1]|=self.loss<<16
        budget['input']=calldata(CONFIGURABLE_RESULT,self.bucket,*packed)
        event=decode_words(result['logs'][0]['data']);event[3]=f'{int(self.output,16):064x}'
        result['logs'][0]['data']='0x'+''.join(event)
        if self.routed:
            result['calls'].insert(0,dict(type='CALL',**{'from':self.pins['entry'],'to':self.pins['v4_executor'],
                'input':calldata('execute(bytes32,uint256,uint256,uint256)',self.route,amount,minimum,deadline),
                'output':words(acquired),'value':hex(amount if self.source==ZERO else 0)}))
        if mutation:mutation(result)
        return result


class TypedV4ActivationTests(unittest.TestCase):
    def service(self,**options):
        rpc=TypedActivationRPC(**options);cfg=configuration();cfg['accounting_version']=2
        p=Projection(cfg,rpc,clock=lambda:1000)
        return rpc,p,ActivationTransactions(p,rpc.config)

    def test_explicit_v4_prepares_exact_erc20_to_native_with_separate_gas(self):
        rpc,_,svc=self.service()
        result=svc.prepare(rpc.request)
        self.assertTrue(result['activation_ready']);self.assertEqual(result['transaction']['value'],'0x0')
        self.assertEqual(result['provenance']['routing_version'],2)
        self.assertEqual(result['minimum_deployed_usd_18'],str(99*USD))
        self.assertFalse(result['network_gas']['included_in_execution_loss'])

    def test_direct_and_increase_use_same_configurable_policy_without_v4_call(self):
        for options in ({'routed':False},{'increase':True},{'new_pool':True}):
            with self.subTest(options=options):
                rpc,_,svc=self.service(**options)
                self.assertTrue(svc.prepare(rpc.request)['activation_ready'])

    def test_native_input_v4_conversion_carries_exact_child_value(self):
        rpc,_,svc=self.service(native_source=True)
        result=svc.prepare(rpc.request)
        self.assertTrue(result['activation_ready'])
        self.assertEqual(result['transaction']['value'],hex(rpc.original_amount))
        self.assertEqual(result['source']['asset'],ZERO)

    def test_configurable_floor_supports_zero_and_ten_percent_without_changing_default(self):
        for loss in (0,100,1000):
            with self.subTest(loss=loss):
                rpc,_,svc=self.service(routed=False,loss=loss)
                if loss==0:rpc.economics=(*rpc.economics[:4],1100*USD,0,200)
                result=svc.prepare(rpc.request)
                self.assertEqual(result['execution_limit_bps'],loss)
                self.assertEqual(result['minimum_deployed_usd_18'],str(100*USD-100*USD*loss//10000))

    def test_cap_outside_hard_max_or_changed_hard_policy_fails_closed(self):
        for method,value in (('MAX_LOSS_BPS()',999),('contributionLossBps()',1001)):
            rpc,_,svc=self.service();rpc.put(rpc.pins['budget'],method,values=(value,))
            with self.subTest(method=method),self.assertRaises(ProjectionError):svc.prepare(rpc.request)

    def test_reviewed_cap_must_equal_early_contract_snapshot(self):
        rpc,_,svc=self.service()
        rpc.trace_mutation=lambda t:t['calls'][1]['calls'][1].update(
            input=calldata(CONFIGURABLE_RESULT,rpc.bucket,*rpc.economics[:-1],200|(1000<<16)))
        with self.assertRaisesRegex(ProjectionError,'snapshot'):svc.prepare(rpc.request)

    def test_legacy_result_is_rejected_under_new_profile(self):
        rpc,_,svc=self.service()
        rpc.trace_mutation=lambda t:t['calls'][1]['calls'][1].update(input=calldata(RESULT,rpc.bucket,*rpc.economics))
        with self.assertRaisesRegex(ProjectionError,'profile'):svc.prepare(rpc.request)

    def test_exact_approval_then_fresh_review_is_not_automatic_execution(self):
        rpc,_,svc=self.service();rpc.allowance=0
        result=svc.prepare(rpc.request)
        self.assertEqual(result['kind'],'approval_required')
        self.assertEqual(result['approval_steps'][0]['amount_raw'],str(rpc.original_amount))
        self.assertEqual(rpc.trace_count,0)

    def test_signed_settlement_bound_rejected_before_an_approval(self):
        rpc,_,svc=self.service();rpc.request['amount_in']=str(2**127);rpc.allowance=0
        with self.assertRaisesRegex(ProjectionError,'signed settlement'):svc.prepare(rpc.request)
        self.assertEqual(rpc.trace_count,0)

    def test_helper_binding_runtime_and_route_kind_fail_closed(self):
        for target,method,value in (('entry','v4Executor()',addr(91)),('v4_executor','parent()',addr(91)),
                                     ('entry','routeKind(bytes32)',1)):
            rpc,_,svc=self.service()
            rpc.put(rpc.pins[target],method,(rpc.route,) if method.startswith('routeKind') else (),values=(value,))
            with self.subTest(method=method),self.assertRaises(ProjectionError):svc.prepare(rpc.request)
        rpc,_,svc=self.service();rpc.codes[rpc.pins['v4_executor']]='0x600091'
        with self.assertRaises(ProjectionError):svc.prepare(rpc.request)

    def test_v4_descriptor_validate_and_domain_cannot_be_substituted(self):
        for index,value in ((0,addr(23)),(4,501),(6,addr(1)),(9,'0x'+'e'*64),(13,ZERO_HASH)):
            rpc,_,svc=self.service();data=rpc.v4_values.copy();data[index]=value
            for target,method in ((rpc.pins['entry'],'v4Route(bytes32)'),(rpc.pins['v4_executor'],'route(bytes32)'),
                                  (rpc.pins['v4_executor'],'validate(bytes32)')):
                rpc.put(target,method,(rpc.route,),data)
            with self.subTest(index=index),self.assertRaises(ProjectionError):svc.prepare(rpc.request)

    def test_missing_native_sentinel_and_pool_fee_or_init_mismatch_rejected(self):
        for price,fee in ((0,500),(2**96,501)):
            rpc,_,svc=self.service();pool='0x'+keccak256(bytes.fromhex(words(*rpc.v4_values[2:7])[2:])).hex()
            rpc.put(rpc.pins['state_view'],'getSlot0(bytes32)',(pool,),(price,0,0,fee))
            with self.subTest(price=price,fee=fee),self.assertRaises(ProjectionError):svc.prepare(rpc.request)

    def test_exact_helper_child_value_output_target_and_calldata_are_required(self):
        for change in (dict(value='0x1'),dict(output=words(1)),dict(to=addr(91)),dict(input='0x12345678')):
            rpc,_,svc=self.service();rpc.trace_mutation=lambda t,c=change:t['calls'][0].update(**c)
            with self.subTest(change=change),self.assertRaises(ProjectionError):svc.prepare(rpc.request)

    def test_profile_route_kind_and_native_legacy_fail_without_fallback(self):
        rpc,p,_=self.service()
        for value in (True,3,'2',None):
            cfg=copy.deepcopy(rpc.config);cfg['routing_version']=value
            with self.subTest(value=value),self.assertRaises(ValueError):ActivationConfig(cfg,p)
        for value in (True,0,1,3):
            cfg=copy.deepcopy(rpc.config);cfg['sources'][0]['route_kind']=value
            if value==1:cfg['sources'][0]['source_asset']=ZERO
            with self.subTest(kind=value),self.assertRaises(ValueError):ActivationConfig(cfg,p)


if __name__=='__main__':unittest.main()
