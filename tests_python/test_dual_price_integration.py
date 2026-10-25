"""Versioned dual-source integration; every provider/round is a synthetic fixture."""
import copy
import unittest
from unittest.mock import patch

from frontend_api.activation import ActivationTransactions
from frontend_api import activation_trace as T
from frontend_api.earnings_prices import Prices
from frontend_api.service import Projection, ProjectionError
from zzz_ops import price_policy as D, production_v2 as P, production_observer as O
from zzz_ops.abi import calldata, keccak256
from tests_python.test_frontend_api import configuration, addr, words
from tests_python.test_native_backend_boundary import NativeActivationRPC, native_data, BLOCK
from tests_python.test_typed_v4_activation import TypedActivationRPC
from tests_python import test_production_v2 as G
from tests_python.test_production_observer import CompositionRPC, RUNTIME, encoded, selector

H = '0x'+'88'*32


def make_policy(asset,decimals,oracle,ordinal=0,source_base=8000,code_hash=H):
    policy = {'token':asset,'primary':{'source':addr(source_base),'expectedCodeHash':code_hash,
        'independenceId':'0x'+'11'*32,'maxAge':3600,'feedDecimals':8},
        'secondary':{'source':addr(source_base+1),'expectedCodeHash':code_hash,
        'independenceId':'0x'+'22'*32,'maxAge':3600,'feedDecimals':8},
        'maxDeviationBps':50,'assetDecimals':decimals,'reviewHash':H}
    return {'policy_id':D.policy_id(oracle,ordinal,policy),'ordinal':ordinal,'policy':policy}


def source_round(answer,stamp=980):
    return [2,answer,stamp-10,stamp,2]


def bounds(record,oracle,chain=31337,answer=10**8,stamp=980,seq=D.ZERO_HASH):
    raw = source_round(answer,stamp)+source_round(answer,stamp)
    return {'lower':answer*10**10,'upper':answer*10**10,
        'fingerprint':D.hash_words([D.DOMAIN,chain,oracle,record['policy_id'],seq]+raw)}


def install(rpc):
    oracle = rpc.pins['oracle']; rpc.config['pricing_version']=2; rpc.config['review_policy_version']=1
    helper=addr(91);rpc.pins['contribution_pricing']=helper;rpc.codes[helper]='0x600091'
    rpc.config['contracts']['contribution_pricing']={'address':helper,'code_hash':rpc.digest(helper)}
    rpc.put(helper,'access()',values=(addr(1),));rpc.put(helper,'oracle()',values=(oracle,));rpc.put(helper,'active()',values=(0,))
    rpc.put(oracle,'contributionPricing()',values=(helper,))
    rpc.put(oracle,'PRICING_VERSION()',values=(2,))
    rpc.put(rpc.pins['entry'],'REVIEW_POLICY_VERSION()',values=(1,))
    rpc.put(helper,'ENTRY_REVIEW_VERSION()',values=(1,))
    rpc.put(oracle,'policyCount()',values=(len(rpc.config['tokens']),))
    for i,token in enumerate(rpc.config['tokens']):
        token.update(price_policy=make_policy(token['address'],token['decimals'],oracle,i,8000+2*i,
            '0x'+keccak256(b'dual-source').hex()))
        for key in ('feed','feed_code_hash','feed_decimals','max_age'): token.pop(key)
        record=token['price_policy']
        rpc.responses[oracle,native_data('activePolicy(address)',token['address'])]=words(record['policy_id'])
        rpc.put(oracle,'policyAt(uint256)',(i,),(record['policy_id'],))
        rpc.put(oracle,'policy(bytes32)',(record['policy_id'],),D.flat(record['policy']))
        value=bounds(record,oracle)
        rpc.responses[oracle,native_data('priceBounds(address)',token['address'])]=words(value['lower'],value['upper'],value['fingerprint'])
        for role in ('primary','secondary'):
            source=record['policy'][role]['source'];rpc.codes[source]='0x'+b'dual-source'.hex()
            rpc.put(source,'decimals()',values=(8,));rpc.put(source,'latestRoundData()',values=source_round(10**8))
    return rpc


def gate_fixture():
    config=G.fixture()
    if config.get('pricing_version')==2:return config
    config['pricing_version']=2;chain=config['chains'][0]
    oracle=chain['modules']['oracle']['address']
    for i,token in enumerate(chain['tokens']):
        old=token.pop('feed');record=make_policy(token['address'],token['decimals'],oracle,i,11000+2*i,G.HASH)
        answer=old['answer'];value=bounds(record,oracle,4663,answer,G.NOW-30)
        record.update(observed_pricing_version=2,observed_policy_id=record['policy_id'],
            observed_policy=copy.deepcopy(record['policy']),observed_policy_count=2,
            observed_ordinal_id=record['policy_id'],observed_bounds=value,sources=[])
        for role in ('primary','secondary'):
            source=record['policy'][role]
            record['sources'].append(dict(source=source['source'],runtime_hash=G.HASH,observed_runtime_hash=G.HASH,
                denomination='USD',decimals=8,round_id=2,answer=answer,started_at=G.NOW-40,updated_at=G.NOW-30,answered_in_round=2,
                review_evidence=G.proof(independent_price_source=True,depeg_and_manipulation_reviewed=True,
                    underlying_sources_reviewed=True,proxy_implementation_reviewed=True,chain_id=4663,
                    asset=token['address'],source=source['source'],runtime_hash=G.HASH,independence_id=source['independenceId'])))
        record['review_evidence']=G.proof(kind='dual_source_pricing_review',chain_id=4663,asset=token['address'],
            oracle=oracle,policy_id=record['policy_id'],onchain_review_hash=record['policy']['reviewHash'],
            sources_independent=True,common_mode_risk_reviewed=True,bounds_and_outage_reviewed=True)
        token['price_policy']=record
    chain['services']['pricing']['profile']='independent_dual_usd_v2'
    chain['services']['pricing']['evidence']['profile']='independent_dual_usd_v2'
    return config


class DualCompositionRPC(CompositionRPC):
    def call(self,method,params=None):
        if method=='eth_call':
            target,data=params[0]['to'],params[0]['data'];chain=self.chain;oracle=chain['modules']['oracle']['address']
            if self.bad is not None and self.bad(target,data): raise ValueError('secret-provider-message')
            if (target,data) in self.overrides:return self.overrides[target,data]
            if target==oracle:
                if data==selector('PRICING_VERSION()'):return encoded(2)
                if data==selector('policyCount()'):return encoded(len(chain['tokens']))
                if data==selector('activeSequencerPolicy()'):return encoded(chain['sequencer'].get('active_policy_id',D.ZERO_HASH))
            for token in chain['tokens']:
                record=token['price_policy'];policy=record['policy']
                if target==token['address'] and data==selector('decimals()'):return encoded(token['decimals'])
                for index,role in enumerate(('primary','secondary')):
                    if target==policy[role]['source']:
                        if data==selector('decimals()'):return encoded(policy[role]['feedDecimals'])
                        observed=record['sources'][index]
                        if data==selector('latestRoundData()'):return encoded(*(observed[key] for key in ('round_id','answer','started_at','updated_at','answered_in_round')))
                if target==oracle:
                    if data==selector('activePolicy(address)')+O._word(token['address']):return encoded(record['policy_id'])
                    if data==selector('policyAt(uint256)')+O._word(record['ordinal']):return encoded(record['policy_id'])
                    if data==selector('policy(bytes32)')+O._word(record['policy_id']):return encoded(*D.flat(policy))
                    if data==selector('priceBounds(address)')+O._word(token['address']):return encoded(*(record['observed_bounds'][key] for key in ('lower','upper','fingerprint')))
        # Parent's historical feed loop must not interpret current records.
        restored=[]
        for token in self.chain['tokens']:
            restored.append(token.get('feed'))
            if 'feed' not in token:token['feed']={'source':addr(999999),'decimals':8,'round_id':2,'answer':1,'updated_at':1,'answered_in_round':2,'maximum_age_seconds':1}
        try:return super().call(method,params)
        finally:
            for token,old in zip(self.chain['tokens'],restored):
                if old is None:token.pop('feed',None)
                else:token['feed']=old


class DualActivationRPC(TypedActivationRPC):
    def __init__(self,*,routed=False,**kwargs):super().__init__(routed=routed,**kwargs)
    def trace(self,tx):
        mutation=self.trace_mutation;self.trace_mutation=None
        root=super().trace(tx);self.trace_mutation=mutation
        q=[int(w,16) for w in T.decode_words('0x'+tx['data'][10:])]
        nft,_,_,amount,_,_,minimum,_,increase=q[:9]
        vault=next(frame for frame in root['calls'] if frame['to']==addr(3));mint,check=vault['calls'];helper=self.pins['contribution_pricing'];budget=self.pins['budget']
        conversions=[frame for frame in root['calls'] if frame is not vault]
        economics=[int(w,16) for w in T.decode_words('0x'+check['input'][10:])][1:]
        gross,supply,incumbent,old_deployed,deployed,idle,limits=economics
        def frame(caller,target,sig,args=(),output='0x',kind='CALL'):
            return {'type':kind,'from':caller,'to':target,'input':T.static_data(sig,*args),'output':output,'value':'0x0','calls':[]}
        begin=frame(self.pins['entry'],helper,T.BEGIN_ENTRY_REVIEWED,(nft,self.pool,self.source,amount,q[9]),words(gross))
        for token in self.config['tokens']:
            if token['address'] not in (self.source,D.ZERO,addr(21)) and not (self.historical and token['address']==addr(22)):continue
            value=bounds(token['price_policy'],self.pins['oracle'])
            begin['calls'].append(frame(helper,self.pins['oracle'],'priceBounds(address)',(token['address'],),
                words(value['lower'],value['upper'],value['fingerprint']),'STATICCALL'))
        params=[int(w,16) for w in T.decode_words('0x'+vault['input'][10:])];offset=1 if increase else 2
        packed=params[offset] | params[offset+1]<<128
        validation=frame(addr(3),budget,T.VALIDATE_PRICING,(nft,self.bucket,gross,packed,minimum,int(not increase)),words(D.ZERO,addr(21),limits))
        validation['calls']=[frame(budget,helper,T.BEGIN_PRICING,(nft,self.bucket,packed,gross,limits))]
        navs=[]
        for a,b in ((old_deployed,0),(old_deployed,0),(deployed,idle)):
            nav=frame(addr(3),budget,T.NAV_PRICING,(self.bucket,),words(a,b))
            nav['calls']=[frame(budget,helper,T.NAV_PRICING,(self.bucket,),words(a,b))];navs.append(nav)
        compound=[]
        for _ in range(2 if supply else 1):
            value=frame(addr(3),budget,'valueBucket(uint256,uint256,uint256)',(self.bucket,0,0),words(0),'STATICCALL')
            value['calls']=[frame(budget,helper,'valueBucket(uint256,uint256,uint256)',(self.bucket,0,0),words(0),'STATICCALL')]
            compound.append(value)
        check['type']='CALL';finish=frame(budget,helper,T.FINISH_PRICING,(self.bucket,*economics),check['output']);check['calls']=[finish]
        for asset,amount in [(D.ZERO,0),(addr(21),0)]+([(addr(22),self.historical)] if self.historical else []):
            finish['calls'].append(frame(helper,self.pins['fees'],'compoundBalance(uint256,address)',(self.bucket,asset),words(amount),'STATICCALL'))
        if supply:
            finish['calls'].append(frame(helper,budget,'compositionEpoch(uint256)',(self.bucket,),words(1 if self.historical else 0),'STATICCALL'))
            if self.historical:finish['calls'].append(frame(helper,self.pins['fees'],'compoundBalance(uint256,address)',(self.bucket,addr(22)),words(self.historical),'STATICCALL'))
        issued,net=map(lambda w:int(w,16),T.decode_words(check['output']))
        finish['logs']=[{'address':helper,'topics':[T.VERIFIED,words(nft),words(self.bucket)],
            'data':words(gross,gross,deployed-old_deployed,net,2**96,H)}]
        vault['calls']=[validation,navs[0]]+([compound[0]] if supply else [])+[navs[1],mint,compound[-1],navs[2],check]
        root['calls']=[begin,*conversions,vault,frame(self.pins['entry'],helper,'endEntry()')]
        if mutation:mutation(root)
        return root


class DualPriceIntegrationTests(unittest.TestCase):
    def setup_activation(self,**options):
        rpc=install(DualActivationRPC(**options));cfg=configuration();cfg['accounting_version']=2
        p=Projection(cfg,rpc,clock=lambda:1000)
        return rpc,p,ActivationTransactions(p,rpc.config)

    def test_native_and_erc20_dual_activation_policy_verification(self):
        rpc,p,service=self.setup_activation()
        pins,prices=service.config.verify(p,BLOCK,[D.ZERO,addr(21)],timestamp=990)
        self.assertEqual(prices,{D.ZERO:10**18,addr(21):10**18})
        self.assertEqual(pins['oracle'],rpc.pins['oracle'])

    def test_full_activation_uses_reviewed_dual_prices(self):
        rpc,p,service=self.setup_activation()
        self.assertTrue(service.prepare(rpc.request)['activation_ready'])

    def test_routed_erc20_new_lp_and_growth_use_dual_pricing_phases(self):
        for options in ({'routed':True},{'increase':True},{'new_pool':True}):
            with self.subTest(options=options):
                rpc,p,service=self.setup_activation(**options)
                self.assertTrue(service.prepare(rpc.request)['activation_ready'])

    def test_pricing_phase_witness_rejects_missing_reordered_or_changed_callbacks(self):
        def vault(trace):return next(x for x in trace['calls'] if x['to']==addr(3))
        def helper_finish(trace):return vault(trace)['calls'][-1]['calls'][0]
        def remove_nav(trace):vault(trace)['calls'].pop(1)
        def reorder(trace):trace['calls'][0],trace['calls'][1]=trace['calls'][1],trace['calls'][0]
        def change_raw(trace):
            frame=vault(trace)['calls'][0];parts=T.decode_words('0x'+frame['input'][10:]);parts[3]=f'{1:064x}';frame['input']=frame['input'][:10]+''.join(parts)
        def change_fingerprint(trace):trace['calls'][0]['calls'][0]['output']=words(10**18,10**18,H)
        def change_nav(trace):vault(trace)['calls'][-2]['output']=words(999999999999999999999999,0)
        def change_upper_event(trace):
            event=helper_finish(trace)['logs'][0];parts=T.decode_words(event['data']);parts[1]=f'{1:064x}';event['data']='0x'+''.join(parts)
        def static_finish(trace):helper_finish(trace)['type']='STATICCALL'
        def remove_end(trace):trace['calls'].pop()
        for mutation in (remove_nav,reorder,change_raw,change_fingerprint,change_nav,change_upper_event,static_finish,remove_end):
            with self.subTest(mutation=mutation.__name__):
                rpc,p,service=self.setup_activation();rpc.trace_mutation=mutation
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_pricing_helper_misbinding_or_stale_active_context_blocks(self):
        for method,value in (('oracle()',addr(222)),('active()',1)):
            rpc,p,service=self.setup_activation();rpc.put(rpc.pins['contribution_pricing'],method,values=(value,))
            with self.assertRaises(ProjectionError):service.config.verify(p,BLOCK,[D.ZERO],timestamp=990)

    def test_composed_historical_compound_is_marked_twice_but_counted_once(self):
        rpc,p,service=self.setup_activation(historical=100*10**18)
        result=service.prepare(rpc.request)
        self.assertEqual(result['contribution']['shares_added_raw'],str(1000*10**18*99//1100))

    def test_historical_compound_mismatch_or_duplicate_in_one_phase_fails(self):
        def changed(trace):trace['calls'][1]['calls'][-1]['calls'][0]['calls'][-1]['output']=words(101*10**18)
        def duplicated(trace):
            calls=trace['calls'][1]['calls'][-1]['calls'][0]['calls'];calls.append(copy.deepcopy(calls[-1]))
        def changed_fingerprint(trace):trace['calls'][0]['calls'][-1]['output']=words(10**18,10**18,H)
        def missing_historical_frame(trace):trace['calls'][0]['calls'].pop()
        for mutation in (changed,duplicated,changed_fingerprint,missing_historical_frame):
            rpc,p,service=self.setup_activation(historical=100*10**18);rpc.trace_mutation=mutation
            with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_declared_v2_cannot_accept_legacy_single_feed_fields(self):
        rpc=NativeActivationRPC();rpc.config['pricing_version']=2;cfg=configuration();cfg['accounting_version']=2
        with self.assertRaises(ValueError):ActivationTransactions(Projection(cfg,rpc,clock=lambda:1000),rpc.config)

    def test_accounting_and_routing_versions_do_not_imply_pricing_upgrade(self):
        rpc=NativeActivationRPC();cfg=configuration();cfg['accounting_version']=2
        self.assertEqual(ActivationTransactions(Projection(cfg,rpc,clock=lambda:1000),rpc.config).config.pricing_version,1)

    def test_source_runtime_or_decimals_change_blocks_activation(self):
        for changed in ('runtime','decimals'):
            rpc,p,service=self.setup_activation();source=rpc.config['tokens'][0]['price_policy']['policy']['secondary']['source']
            if changed=='runtime':rpc.codes[source]='0x6000'
            else:rpc.put(source,'decimals()',values=(6,))
            with self.assertRaises(ProjectionError):service.config.verify(p,BLOCK,[D.ZERO],timestamp=990)

    def test_missing_source_or_bad_round_blocks_without_single_feed_fallback(self):
        for values in (None,[0,10**8,970,980,2],[2,0,970,980,2],[2,10**8,990,980,2],[2,10**8,970,980,1]):
            rpc,p,service=self.setup_activation();source=rpc.config['tokens'][0]['price_policy']['policy']['secondary']['source']
            if values is None:rpc.responses.pop((source,calldata('latestRoundData()')))
            else:rpc.put(source,'latestRoundData()',values=values)
            with self.assertRaises((ProjectionError,AssertionError)):service.config.verify(p,BLOCK,[D.ZERO],timestamp=990)

    def test_backend_independently_rejects_future_or_stale_source_rounds(self):
        for timestamp,updated in ((990,991),(5000,980)):
            rpc,p,service=self.setup_activation()
            source=rpc.config['tokens'][0]['price_policy']['policy']['secondary']['source']
            rpc.put(source,'latestRoundData()',values=[2,10**8,970,updated,2])
            with self.assertRaises(ProjectionError):
                service.config.verify(p,BLOCK,[D.ZERO],timestamp=timestamp)

    def test_dual_backend_cannot_skip_confirmed_timestamp_checks(self):
        rpc,p,service=self.setup_activation()
        with self.assertRaises(ProjectionError):service.config.verify(p,BLOCK,[D.ZERO])

    def test_spread_or_fingerprint_mismatch_blocks(self):
        for changed in ('spread','fingerprint'):
            rpc,p,service=self.setup_activation();record=rpc.config['tokens'][0]['price_policy']
            if changed=='spread':rpc.put(record['policy']['secondary']['source'],'latestRoundData()',values=source_round(2*10**8))
            else:rpc.responses[rpc.pins['oracle'],native_data('priceBounds(address)',D.ZERO)]=words(10**18,10**18,H)
            with self.assertRaises(ProjectionError):service.config.verify(p,BLOCK,[D.ZERO],timestamp=990)

    def test_policy_version_and_active_ordinal_are_exact(self):
        for getter,value in (('PRICING_VERSION()',1),('policyCount()',0),('policyAt(uint256)',H)):
            rpc,p,service=self.setup_activation()
            rpc.put(rpc.pins['oracle'],getter,(0,) if getter.startswith('policyAt') else (), (value,))
            with self.assertRaises(ProjectionError):service.config.verify(p,BLOCK,[D.ZERO],timestamp=990)

    def test_earnings_native_dual_price_is_bounded_and_unavailability_is_not_zero(self):
        rpc,p,service=self.setup_activation();oracle=rpc.pins['oracle'];record=rpc.config['tokens'][0]['price_policy']
        config={'pricing_version':2,'oracle':{'address':oracle,'code_hash':rpc.digest(oracle)},'sequencer':None,
            'feeds':[{'asset':D.ZERO,'priced_token':D.ZERO,'token_code_hash':None,'price_policy':record}]}
        prices=Prices(config,p,p.assets);result=prices.read(BLOCK,timestamp=990)
        self.assertEqual(result[D.ZERO]['usd_per_token_18'],str(10**18));self.assertEqual(result[D.ZERO]['pricing_version'],2)
        rpc.codes[record['policy']['secondary']['source']]='0x6000'
        missing=prices.read(BLOCK,timestamp=990)[D.ZERO]
        self.assertFalse(missing['available']);self.assertIsNone(missing['usd_per_token_18'])

    def test_policy_identity_source_independence_and_bounds_are_strict(self):
        valid=make_policy(D.ZERO,18,addr(50))
        for field,value in (('source',valid['policy']['primary']['source']),('independenceId',valid['policy']['primary']['independenceId']),('maxAge',0),('feedDecimals',19)):
            item=copy.deepcopy(valid);item['policy']['secondary'][field]=value
            with self.assertRaises(ValueError):D.record(item,D.ZERO,18,addr(50))
        for deviation in (-1,501,True):
            item=copy.deepcopy(valid);item['policy']['maxDeviationBps']=deviation
            with self.assertRaises(ValueError):D.record(item,D.ZERO,18,addr(50))

    def test_exact_price_word_codec_rejects_ambiguous_numeric_values(self):
        for value in (True,False,1.5,None,'1','0x'+'1'*65,1<<256,-(1<<255)-1):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):D.words([value])
        self.assertEqual(D.words([0,1,-1,'0x01']),['0'*64,'0'*63+'1','f'*64,'0'*63+'1'])

    def test_gate_complete_dual_policy_is_consistency_only(self):
        result=P.validate(gate_fixture(),expected_commit=G.COMMIT,now=G.NOW)
        self.assertTrue(result['ready'],result['issues']);self.assertFalse(result['deployment_authorized'])

    def test_gate_legacy_single_feed_inventory_cannot_be_current_ready(self):
        legacy=G.fixture();legacy.pop('pricing_version')
        for token in legacy['chains'][0]['tokens']:token.pop('price_policy')
        result=P.validate(legacy,now=G.NOW)
        self.assertFalse(result['ready']);self.assertIn('pricing.policy',{i['code'] for i in result['issues']})

    def test_gate_missing_independence_or_misbound_review_blocks(self):
        for field,value in (('sources_independent',False),('common_mode_risk_reviewed',False),('oracle',addr(333)),('policy_id',H)):
            config=gate_fixture();config['chains'][0]['tokens'][1]['price_policy']['review_evidence'][field]=value
            self.assertIn('pricing.independence',{i['code'] for i in P.validate(config,now=G.NOW)['issues']})

    def test_gate_stale_future_incomplete_or_changed_price_blocks(self):
        for field,value in (('updated_at',G.NOW-4000),('updated_at',G.NOW+1),('answer',0),('round_id',0),('answered_in_round',1),('started_at',G.NOW)):
            config=gate_fixture();config['chains'][0]['tokens'][0]['price_policy']['sources'][1][field]=value
            self.assertIn('pricing.round',{i['code'] for i in P.validate(config,now=G.NOW)['issues']})

    def test_gate_fingerprint_or_round_data_cannot_be_copied_between_assets(self):
        config=gate_fixture();tokens=config['chains'][0]['tokens']
        tokens[1]['price_policy']['observed_bounds']=copy.deepcopy(tokens[0]['price_policy']['observed_bounds'])
        self.assertIn('pricing.bounds',{i['code'] for i in P.validate(config,now=G.NOW)['issues']})

    def test_observer_and_gate_composition_preserves_approved_policy(self):
        deps={role:(target,RUNTIME) for role,(target,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(G,'HASH',RUNTIME):
            config=gate_fixture();original=copy.deepcopy(config)
            result=O.observe(config,DualCompositionRPC(config))
            self.assertTrue(result['chains'][0]['observation']['complete'],result['chains'][0]['observation']['errors'])
            gate=P.validate(result,now=G.NOW)
            self.assertTrue(gate['ready'],gate['issues']);self.assertFalse(gate['deployment_authorized'])
            self.assertEqual(config,original)

    def test_observer_failure_clears_copied_success_and_does_not_upgrade_review(self):
        deps={role:(target,RUNTIME) for role,(target,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(G,'HASH',RUNTIME):
            config=gate_fixture();rpc=DualCompositionRPC(config);record=config['chains'][0]['tokens'][0]['price_policy']
            source=record['policy']['secondary']['source'];rpc.bad=lambda target,data:target==source
            result=O.observe(config,rpc);observed=result['chains'][0]['tokens'][0]['price_policy']
            self.assertFalse(result['chains'][0]['observation']['complete']);self.assertIsNone(observed['observed_bounds'])
            self.assertIsNone(observed['sources'][1]['answer']);self.assertEqual(observed['review_evidence'],record['review_evidence'])
            self.assertFalse(P.validate(result,now=G.NOW)['ready'])


if __name__=='__main__':unittest.main()
