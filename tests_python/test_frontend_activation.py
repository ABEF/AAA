"""Full preparation boundary tests. Fixtures are not live-venue qualification."""
import copy
import unittest

from frontend_api.activation import ActivationTransactions, ActivationInputError, GAS_CAP
from frontend_api.activation_config import MODULES, ZERO_HASH
from frontend_api.activation_trace import EXECUTE, RESULT, MINT, INCREASE, SOURCE, SHARES, selector
from frontend_api.service import Projection, ProjectionError, ZERO
from zzz_ops.abi import calldata, decode_words, keccak256
from zzz_ops.rpc import RpcError, Rpc
from zzz_ops.errors import WorkLimit
from tests_python.test_frontend_api import MockRPC, configuration, addr, words

USD=10**18


class ActivationRPC(MockRPC):
    def __init__(self, native=False, conversion=False, increase=False, new_pool=False, source_decimals=18):
        super().__init__()
        self.trace_mutation=None; self.trace_count=0; self.estimate=500000; self.gas_price=10**9
        self.source_decimals=source_decimals
        self.balance=1000*USD; self.allowance=10**30; self.original_amount=100*10**source_decimals
        self.economics=(100*USD,1000*USD,1000*USD,1000*USD,1099*USD,0,200)
        self.pins={r:c['address'] for r,c in configuration()['contracts'].items()}
        self.pins.update({r:addr(40+i) for i,r in enumerate(list(MODULES)+['entry','activation_assets','budget'])})
        self.pins.update(dict(zip(('position_manager','pool_manager','state_view','permit2'),map(addr,range(60,64)))))
        self.native=native;self.conversion=conversion;self.new_pool=new_pool
        self.lp_id=9; self.bucket=5
        if new_pool:self.economics=(100*USD,0,0,0,99*USD,0,200)
        self.pool_values=[ZERO if native else addr(20),addr(21),0,60,ZERO,1,1,2000,500,100,200,3600,100*USD,10**30]
        self.pool='0x'+keccak256(bytes.fromhex(words(*self.pool_values[:5])[2:])).hex()
        self.source=ZERO if native else addr(22) if conversion else addr(20)
        self.request={'action':'increase' if increase else 'activate','wallet':addr(30),'token_id':str(self.nft_id),
                      'pool_id':self.pool,'source_asset':self.source,'amount_in':str(self.original_amount),'slippage_bps':50}
        self.config={'schema':1,'contracts':{},'tokens':[],'dependencies':[],'sources':[],
                     'sequencer':{'address':ZERO,'policy_id':ZERO_HASH},'call_pins':[],'storage_pins':[],
                     'fee_policy':{'estimate_includes_all_fees':True,'review_hash':'0x'+'f'*64,'max_gas_price_wei':'100000000000'}}
        for role in list(MODULES)+['entry','activation_assets','budget']:
            target=self.pins[role]; self.codes[target]='0x'+bytes([0x60,int(target,16),0]).hex()
            self.config['contracts'][role]={'address':target,'code_hash':self.digest(target)}
            self.put(target,'access()',values=(addr(1),))
            if role in MODULES:self.put(addr(1),'module(bytes32)',('0x'+keccak256(MODULES[role].encode()).hex(),),(target,))
        for n in range(60,70):
            self.codes[addr(n)]='0x'+bytes([0x60,n,0]).hex()
            self.config['dependencies'].append({'address':addr(n),'code_hash':self.digest(addr(n))})
        for n in (20,21,22):
            t,f=addr(n),addr(n+60)
            self.codes[t]='0x'+bytes([0x60,n,0]).hex();self.codes[f]='0x600100'
            decimals=source_decimals if t==(addr(20) if native else self.source) else 18
            self.config['tokens'].append({'address':t,'code_hash':self.digest(t),'decimals':decimals,'feed':f,
                                         'feed_code_hash':self.digest(f),'feed_decimals':8,'max_age':3600})
            self.put(t,'decimals()',values=(decimals,));self.put(f,'decimals()',values=(8,))
            self.put(self.pins['oracle'],'feeds(address)',(t,),(f,3600,8,decimals))
            self.put(self.pins['oracle'],'price(address)',(t,),(USD,))
        bindings=[('pools','activationEntry()','entry'),('pools','activationAssets()','activation_assets'),
                  ('entry','registry()','pools'),('entry','activationAssets()','activation_assets'),
                  ('activation_assets','registry()','pools'),('vault','migrationBudget()','budget'),('budget','vault()','vault'),
                  ('liquidity','positionManager()','position_manager'),('liquidity','poolManager()','pool_manager'),
                  ('liquidity','stateView()','state_view'),('liquidity','permit2()','permit2'),
                  ('position_manager','poolManager()','pool_manager'),('position_manager','permit2()','permit2'),
                  ('state_view','poolManager()','pool_manager')]
        for a,method,b in bindings:self.put(self.pins[a],method,values=(self.pins[b],))
        for method in ('sequencerFeed()','activeSequencerPolicy()'):self.put(self.pins['oracle'],method)
        self.put(self.pins['pools'],'get(bytes32)',(self.pool,),self.pool_values)
        self.put(self.pins['pools'],'accounting(bytes32)',(self.pool,),[addr(20)]+self.pool_values[1:])
        self.put(self.pins['pools'],'nativeAsset(bytes32)',(self.pool,),(addr(20),))
        source=addr(20) if native else self.source;policy='0x'+'d'*64
        self.put(self.pins['activation_assets'],'activePolicy(address)',(source,),(policy,))
        self.put(self.pins['activation_assets'],'policies(bytes32)',(policy,),
                 (source,1,self.digest(source),'0x'+'e'*64,source_decimals,1))
        self.put(self.pins['activation_assets'],'value(address,uint256)',(source,self.original_amount),(100*USD,))
        route=ZERO_HASH
        if conversion:
            router,factory,pool=addr(64),addr(65),addr(66)
            values=(source,addr(20),router,factory,pool,500)+tuple(self.digest(t) for t in (router,factory,pool,source,addr(20)))+('0x'+'a'*64,)
            route='0x'+keccak256(bytes.fromhex(words(*values)[2:])).hex()
            self.put(self.pins['entry'],'route(bytes32)',(route,),values)
            for method in ('routeExists(bytes32)','routeEnabled(bytes32)'):self.put(self.pins['entry'],method,(route,),(1,))
            self.put(router,'factory()',values=(factory,));self.put(factory,'getPool(address,address,uint24)',(source,addr(20),500),(pool,))
            for method,value in [('factory()',factory),('token0()',addr(20)),('token1()',source),('fee()',500),('liquidity()',10000)]:
                self.put(pool,method,values=(value,))
        self.config['sources']=[{'pool_id':self.pool,'source_asset':self.source,'route_id':route,'asset_policy_id':policy}]
        self.put(addr(3),'nftStatus(uint256)',(self.nft_id,),(1 if increase else 5,))
        self.put(addr(3),'contributionUSD(uint256)',(self.nft_id,),(100*USD if increase else 0,))
        self.put(addr(3),'poolBucket(bytes32)',(self.pool,),(0 if new_pool else self.bucket,))
        self.put(addr(8),'bucketIdentity(bytes32)',(self.pool,),(self.bucket,))
        self.put(addr(3),'group(uint256)',(self.bucket,),(self.pool,self.lp_id,0,0,1000*USD,2**96,1,1,31337,addr(3),addr(68),addr(20),addr(21),31337,addr(3)))
        self.put(self.pins['state_view'],'getSlot0(bytes32)',(self.pool,),(2**96,0,0,0))
        self.put(self.pins['strategy'],'validatePrice(bytes32)',(self.pool,),(2**96,))
        self.put(self.pins['strategy'],'target(bytes32)',(self.pool,),((1<<256)-120,120,2**96))
        self.put(self.pins['liquidity'],'ticks(uint256)',(self.lp_id,),((1<<256)-120,120))
        self.put(self.pins['strategy'],'needsRebalance(uint256)',(self.bucket,),(0,))
        self.put(self.pins['strategy'],'rangeUpdatePending(uint256)',(self.bucket,),(0,))
        self.put(self.pins['oracle'],'referenceX96(address,address)',(addr(20),addr(21)),(2**96,))

    def digest(self,target):return '0x'+keccak256(bytes.fromhex(self.codes[target][2:])).hex()

    def trace(self,tx):
        q=[int(w,16) for w in decode_words('0x'+tx['data'][10:])]
        nft,_,_,amount,route,minout,minlp,deadline,increase=q
        gross=amount*USD//10**self.source_decimals
        acquired=gross-gross//1000 if route else amount
        vaultsig='increase(uint256,uint256,uint256,uint128,uint256)' if increase else 'activate(uint256,bytes32,uint256,uint256,uint128,uint256)'
        args=(nft,acquired,0,minlp,deadline) if increase else (nft,self.pool,acquired,0,minlp,deadline)
        def frame(frm,to,data,output='0x',kind='CALL'):
            return {'type':kind,'from':frm,'to':to,'input':data,'output':output,'gasUsed':'0x100','value':'0x0'}
        root=frame(tx['from'],tx['to'],tx['data']);root['value']=tx['value'];root['gasUsed']=hex(400000+self.trace_count)
        vault=frame(self.pins['entry'],addr(3),calldata(vaultsig,*args));root['calls']=[vault]
        _,supply,incumbent,_,deployed,idle,_=self.economics
        net=deployed+idle-incumbent;issued=supply*net//incumbent if supply else net
        budget=frame(addr(3),self.pins['budget'],calldata(RESULT,*self.economics),words(issued,net),'STATICCALL')
        create=self.new_pool
        params=(self.pool,-120,120,1000,1000,minlp,deadline) if create else (self.pool,self.lp_id,1000,1000,minlp,deadline)
        mint_data=selector(MINT)+words(self.pool,(1<<256)-120,120,1000,1000,minlp,deadline)[2:] if create else calldata(INCREASE,*params)
        mint=frame(addr(3),self.pins['liquidity'],mint_data,words(self.lp_id,1000,1000) if create else words(1000,1000))
        mint['calls']=[frame(self.pins['liquidity'],self.pins['position_manager'],calldata('getPositionLiquidity(uint256)',self.lp_id),words(n),'STATICCALL') for n in ([10000] if create else [20000,30000])]
        vault['calls']=[mint,budget]
        root['logs']=[{'address':self.pins['entry'],'topics':[SOURCE,words(tx['from']),words(nft),self.pool],
                       'data':words(self.source,amount,gross,addr(20),acquired,increase)}]
        vault['logs']=[{'address':addr(3),'topics':[SHARES,words(nft),words(self.bucket)],'data':words(issued,net)}]
        if self.trace_mutation:self.trace_mutation(root)
        return root

    def call(self,method,params):
        if method in ('debug_traceCall','eth_estimateGas','eth_gasPrice','eth_getBalance','eth_getStorageAt') or method=='eth_call' and 'from' in params[0]:
            self.calls.append((method,copy.deepcopy(params)))
            if method=='debug_traceCall':
                self.trace_count+=1
                assert params[1]=={'blockHash':self.hash,'requireCanonical':True}
                assert params[2]=={'tracer':'callTracer','timeout':'5s','tracerConfig':{'withLog':True}}
                return self.trace(params[0])
            if method=='eth_estimateGas':return hex(self.estimate)
            if method=='eth_gasPrice':return hex(self.gas_price)
            if method=='eth_getBalance':return hex(self.balance)
            if method=='eth_getStorageAt':return words(1)
            return words(1)
        if method=='eth_call':
            data=params[0]['data']
            if data==calldata('balanceOf(address)',addr(30)):
                self.put(params[0]['to'],'balanceOf(address)',(addr(30),),(self.balance,))
            if data==calldata('allowance(address,address)',addr(30),self.pins['entry']):
                self.put(params[0]['to'],'allowance(address,address)',(addr(30),self.pins['entry']),(self.allowance,))
        return super().call(method,params)


class ActivationPreparationTests(unittest.TestCase):
    def service(self,rpc=None):
        self.rpc=rpc or ActivationRPC();self.p=Projection(configuration(),self.rpc,clock=lambda:1000)
        return ActivationTransactions(self.p,self.rpc.config)

    def small_contribution(self, *, value, increase=True, pool_minimum=USD, **options):
        rpc=ActivationRPC(increase=increase, **options)
        rpc.pool_values[12]=pool_minimum
        rpc.put(rpc.pins['pools'],'get(bytes32)',(rpc.pool,),rpc.pool_values)
        rpc.put(rpc.pins['pools'],'accounting(bytes32)',(rpc.pool,),[addr(20)]+rpc.pool_values[1:])
        amount=value*10**rpc.source_decimals//USD
        rpc.request['amount_in']=str(amount)
        source=addr(20) if rpc.native else rpc.source
        rpc.put(rpc.pins['activation_assets'],'value(address,uint256)',(source,amount),(value,))
        floor=value-value//100
        rpc.economics=(value,1000*USD,1000*USD,1000*USD,1000*USD+floor,0,200)
        return rpc

    def test_five_dollar_topup_direct_native_and_six_decimal_conversion(self):
        for options in ({},{'native':True},{'conversion':True,'source_decimals':6}):
            rpc=self.small_contribution(value=5*USD, **options)
            result=self.service(rpc).prepare(rpc.request)
            self.assertTrue(result['activation_ready'])
            self.assertEqual(result['minimum_deployed_usd_18'],str(495*USD//100))
            self.assertFalse(result['network_gas']['included_in_execution_loss'])

    def test_topup_floor_and_higher_pool_minimum_reject_before_approval_or_trace(self):
        for kw in ({'value':5*USD-1},{'value':5*USD,'pool_minimum':6*USD},
                   {'value':100*USD-1,'increase':False}):
            rpc=self.small_contribution(**kw);rpc.allowance=0
            with self.assertRaises(ActivationInputError):self.service(rpc).prepare(rpc.request)
            self.assertEqual(rpc.trace_count,0)

    def test_complete_direct_native_conversion_new_and_existing_pool(self):
        for options in ({},{'native':True},{'conversion':True},{'conversion':True,'source_decimals':6},
                        {'increase':True},{'native':True,'increase':True},{'new_pool':True}):
            with self.subTest(options=options):
                svc=self.service(ActivationRPC(**options));r=svc.prepare(self.rpc.request)
                self.assertTrue(r['activation_ready']);self.assertEqual(self.rpc.trace_count,2)
                self.assertEqual(r['contribution']['marginal_deployed_usd_18'],str(99*USD))
                self.assertEqual(r['current_attached_value']['usd_18'],str(1432*USD))
                self.assertEqual(r['minimum_liquidity_raw'],'9950')
                self.assertEqual(r['network_gas']['estimated_fee_wei'],str(500000*10**9))
                self.assertFalse(r['network_gas']['included_in_execution_loss'])
                self.assertFalse(r['state_overrides']);self.assertEqual(r['transaction']['to'],self.rpc.pins['entry'])
                final=[p[0] for m,p in self.rpc.calls if m=='debug_traceCall'][-1]
                self.assertEqual(final['data'],r['transaction']['data'])
                self.assertEqual(r['onchain_deadline'],1060)

    def test_exact_approval_requires_new_quote_no_fake_allowance(self):
        for allowance in (0,1):
            svc=self.service();self.rpc.allowance=allowance;r=svc.prepare(self.rpc.request)
            self.assertFalse(r['activation_ready']);self.assertEqual(r['kind'],'approval_required')
            self.assertIsNone(r['contribution']);self.assertIsNone(r['onchain_deadline']);self.assertEqual(self.rpc.trace_count,0)
            amount=100*USD
            self.assertEqual(r['transaction']['data'],calldata('approve(address,uint256)',self.rpc.pins['entry'],amount))
            self.assertTrue(r['approval_steps'][0]['reprepare_after_confirmation'])
            self.assertFalse(r['approval_steps'][0]['reset_first'])

    def test_reset_only_or_false_returning_token_never_returns_a_zero_approval(self):
        for failure in ('revert','false'):
            svc=self.service();self.rpc.allowance=1;original=self.rpc.call
            approval=calldata('approve(address,uint256)',self.rpc.pins['entry'],100*USD)
            def call(method,params):
                if method=='eth_call' and params[0].get('data')==approval:
                    if failure=='revert':raise ProjectionError('token requires reset')
                    return words(0)
                return original(method,params)
            self.rpc.call=call
            with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)
            self.assertEqual(self.rpc.trace_count,0)

    def test_original_source_floor_cannot_be_paid_from_incumbent_idle_or_compound(self):
        for deployed,idle,incumbent in ((1099*USD-1,0,1000*USD),(1098*USD,2*USD,1000*USD),(1100*USD,0,1002*USD)):
            svc=self.service();self.rpc.economics=(100*USD,1000*USD,incumbent,incumbent,deployed,idle,200)
            with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)

    def test_final_simulation_economics_cannot_change(self):
        svc=self.service()
        def mutate(t):
            if self.rpc.trace_count==2:t['calls'][0]['calls'][0]['calls'][1]['output']=words(30001)
        self.rpc.trace_mutation=mutate
        with self.assertRaisesRegex(ProjectionError,'disagree'):svc.prepare(self.rpc.request)

    def test_malformed_or_spoofed_trace_never_produces_a_draft(self):
        mutations=[lambda t:t.update(error='execution reverted'),lambda t:t.update(to=addr(99)),
                   lambda t:t.update(input='0x1234'),lambda t:t.update(gasUsed=hex(GAS_CAP+1)),
                   lambda t:t.pop('logs'),lambda t:t['logs'].append(copy.deepcopy(t['logs'][0])),
                   lambda t:t['logs'][0].update(data=words(addr(20),100*USD,101*USD,addr(20),100*USD,0)),
                   lambda t:t['calls'][0]['calls'][1].update(type='CALL'),
                   lambda t:t['calls'][0]['calls'][1].update(output=words(100*USD,99*USD)),
                   lambda t:t['calls'][0]['logs'][0].update(data=words(1,1)),
                   lambda t:t['calls'][0]['calls'][0]['calls'].pop(),
                   lambda t:t['calls'][0]['calls'][0]['calls'][1].update(output=words(19999)),
                   lambda t:t['calls'].append(copy.deepcopy(t['calls'][0]))]
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)):
                svc=self.service();self.rpc.trace_mutation=mutate
                with self.assertRaises((ProjectionError,ValueError)):svc.prepare(self.rpc.request)

    def test_governed_bindings_and_values_fail_closed(self):
        cases=[('access','preparationActive()',(),(1,)),('access','paused()',(),(1,)),
               ('entry','registry()',(),(addr(99),)),('budget','vault()',(),(addr(99),)),
               ('oracle','price(address)',(addr(20),),(2*USD,)),('oracle','sequencerFeed()',(),(addr(69),)),
               ('liquidity','positionManager()',(),(addr(99),))]
        for role,method,args,value in cases:
            with self.subTest(method=method):
                svc=self.service();self.rpc.put(self.rpc.pins[role],method,args,value)
                with self.assertRaises((ProjectionError,ActivationInputError)):svc.prepare(self.rpc.request)
        for method,value in [('ownerOf(uint256)',addr(31)),('traitsReady(uint256)',0)]:
            svc=self.service();self.rpc.put(addr(2),method,(self.rpc.nft_id,),(value,))
            with self.assertRaises(ActivationInputError):svc.prepare(self.rpc.request)

    def test_route_disabled_or_different_policy_rejected(self):
        for method in ('routeExists(bytes32)','routeEnabled(bytes32)'):
            svc=self.service(ActivationRPC(conversion=True));route=self.rpc.config['sources'][0]['route_id']
            self.rpc.put(self.rpc.pins['entry'],method,(route,),(0,))
            with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)
        svc=self.service();self.rpc.put(self.rpc.pins['activation_assets'],'activePolicy(address)',(addr(20),),(ZERO_HASH,))
        with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)

    def test_code_feed_and_storage_pins(self):
        for target in (addr(20),addr(80),addr(60),addr(47)):
            svc=self.service();self.rpc.codes[target]='0x00'
            with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)
        rpc=ActivationRPC();rpc.config['storage_pins']=[{'target':addr(20),'slot':'0x'+'1'*64,'expected':words(2)}]
        svc=self.service(rpc)
        with self.assertRaises(ProjectionError):svc.prepare(rpc.request)

    def test_stale_reorg_and_expiry_rejected(self):
        for mode in ('age','future','reorg','expiry','chain'):
            svc=self.service()
            if mode=='age':self.rpc.header_timestamp=800
            if mode=='future':self.rpc.header_timestamp=1040
            if mode=='reorg':self.rpc.reorg_after_calls=True
            if mode=='expiry':self.p.clock=lambda:1000 if self.rpc.trace_count<2 else 1061
            if mode=='chain':self.rpc.chain=4663
            expected = WorkLimit if mode == 'expiry' else ProjectionError
            with self.subTest(mode=mode),self.assertRaises(expected):svc.prepare(self.rpc.request)

    def test_rpc_capability_failure_has_no_fallback(self):
        for failed in ('debug_traceCall','eth_estimateGas','eth_gasPrice'):
            svc=self.service();original=self.rpc.call
            def call(method,params):
                if method==failed:raise RpcError('unsupported')
                return original(method,params)
            self.rpc.call=call
            with self.assertRaises(RpcError):svc.prepare(self.rpc.request)

    def test_gas_limits_price_and_balance(self):
        for attribute,value in [('estimate',GAS_CAP+1),('estimate',0),('gas_price',10**15),('gas_price',0),('balance',0)]:
            svc=self.service();setattr(self.rpc,attribute,value)
            with self.subTest(attribute=attribute,value=value),self.assertRaises((ProjectionError,ActivationInputError)):
                svc.prepare(self.rpc.request)

    def test_strict_input_no_arbitrary_destination_calldata_value_or_overrides(self):
        for key,value in [('to',addr(99)),('data','0x'),('value','0x0'),('stateOverride',{}),
                          ('amount_in','100.0'),('slippage_bps',101),('slippage_bps',True),('source_asset',addr(99))]:
            svc=self.service();req={**self.rpc.request,key:value}
            with self.subTest(key=key),self.assertRaises(ActivationInputError):svc.prepare(req)

    def test_every_state_read_and_simulation_uses_same_confirmed_hash(self):
        svc=self.service();svc.prepare(self.rpc.request)
        for method,params in self.rpc.calls:
            if method in ('eth_call','eth_getCode','eth_getBalance','eth_estimateGas','eth_getStorageAt','debug_traceCall'):
                self.assertEqual(params[1] if method=='debug_traceCall' else params[-1],{'blockHash':self.rpc.hash,'requireCanonical':True})
        self.assertFalse(any(m.startswith(('eth_send','personal_','wallet_')) for m,p in self.rpc.calls))
        self.assertIn('debug_traceCall',Rpc.READ_METHODS)
        self.assertNotIn('eth_sendRawTransaction',Rpc.READ_METHODS)

    def test_network_fee_review_cannot_be_implicit(self):
        for field in ('estimate_includes_all_fees','review_hash','max_gas_price_wei'):
            rpc=ActivationRPC();rpc.config['fee_policy'].pop(field)
            with self.assertRaises(ValueError):self.service(rpc)

    def test_loss_floor_rounds_up_and_unavailable_current_value_is_not_zero(self):
        svc=self.service();rpc=self.rpc;amount=100*USD+7
        rpc.request['amount_in']=str(amount)
        rpc.put(rpc.pins['activation_assets'],'value(address,uint256)',(addr(20),amount),(amount,))
        floor=amount-amount//100
        rpc.economics=(amount,1000*USD,1000*USD,1000*USD,1000*USD+floor,0,200)
        rpc.put(addr(2),'currentLPValue(uint256)',(rpc.nft_id,),(0,0))
        result=svc.prepare(rpc.request)
        self.assertEqual(result['minimum_deployed_usd_18'],str(99*USD+7))
        self.assertIsNone(result['current_attached_value']['usd_18'])
        rpc.economics=(amount,1000*USD,1000*USD,1000*USD,1000*USD+floor-1,0,200)
        with self.assertRaises(ProjectionError):svc.prepare(rpc.request)

    def test_trace_bounded_shape_and_current_value_consistency(self):
        from unittest.mock import patch
        svc=self.service()
        with patch('frontend_api.activation_trace.MAX_FRAMES',2),self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)
        for mutate in (lambda t:t['logs'][0].update(topics=None),lambda t:t.update(calls=[None]),
                       lambda t:t.update(input=None)):
            svc=self.service();self.rpc.trace_mutation=mutate
            with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)
        svc=self.service();self.rpc.put(addr(2),'currentLPValue(uint256)',(self.rpc.nft_id,),(0,USD))
        with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)


if __name__=='__main__':unittest.main()
