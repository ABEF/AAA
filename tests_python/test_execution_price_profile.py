"""Explicit execution-price1 consumer profile; injected bytes, no live acceptance."""
import copy
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from frontend_api.activation_config import ActivationConfig
from frontend_api import activation_trace as T
from frontend_api.service import Projection,ProjectionError
from tests_python.test_direct_entry_profile import direct_verifier
from tests_python.test_exact_lp_profile7 import Fresh7API
from tests_python.test_frontend_api import addr,words
from zzz_ops import execution_price as E,production_v15 as P
from zzz_ops.production_observer_v15 import Observer
from zzz_ops.abi import calldata,decode_words
from zzz_ops.lp_execution import observe as observe_lp
from zzz_ops.tick_math import sqrt_price_at_tick


def verifier():
    rpc,p,cfg=direct_verifier()
    # This fragment isolates the complete existing activation verifier graph;
    # actual read-profile admission is covered independently below.
    p.accounting_version=7;p.execution_price_version=1
    cfg.update(execution_price_version=1,lp_routing_version=3)
    cfg['tokens']=[row for row in cfg['tokens'] if row['address'] in (T.ZERO,addr(21))]
    rpc.put(rpc.pins['vault'],'ACCOUNTING_VERSION()',values=(7,))
    for role in E.ROLES:rpc.put(rpc.pins[role],'EXECUTION_PRICE_VERSION()',values=(1,))
    rpc.put(rpc.pins['lp_balance_math'],'EXECUTION_PRICE_VERSION()',values=(1,))
    rpc.put(rpc.pins['liquidity'],'executionStrategy()',values=(rpc.pins['lp_balance_math'],))
    for role in ('liquidity','balancing_router'):rpc.put(rpc.pins[role],'LP_ROUTING_VERSION()',values=(3,))
    rpc.put(rpc.pins['oracle'],'executionActive()',values=(0,))
    rpc.put(rpc.pins['oracle'],'executionSourceRevision()',values=(2,))
    return rpc,p,cfg


class ExecutionPriceProfileTests(unittest.TestCase):
    def test_flag_types_unknown_versions_and_old_accounting_are_rejected_before_rpc(self):
        for value in (True,False,None,'1',1.0,2,-1):
            rpc,p,cfg=verifier();cfg['execution_price_version']=value;before=len(rpc.calls)
            with self.subTest(value=value),self.assertRaises(ValueError):ActivationConfig(cfg,p)
            self.assertEqual(before,len(rpc.calls))
        rpc,p,cfg=verifier();p.accounting_version=6
        with self.assertRaises(ValueError):ActivationConfig(cfg,p)

    def test_optional_omission_is_historical_and_cannot_adopt_routing3(self):
        rpc,p,cfg=direct_verifier();self.assertEqual(0,ActivationConfig(cfg,p).execution_price_version)
        cfg['execution_price_version']=0;self.assertEqual(0,ActivationConfig(cfg,p).execution_price_version)
        cfg['lp_routing_version']=3
        with self.assertRaisesRegex(ValueError,'execution-price'):ActivationConfig(cfg,p)

    def test_read_and_activation_profiles_must_match(self):
        rpc,p,cfg=verifier();p.execution_price_version=0
        with self.assertRaisesRegex(ValueError,'profiles differ'):ActivationConfig(cfg,p)

    def verify(self,rpc,p,cfg):
        observed={};config=ActivationConfig(cfg,p)
        result=config.verify(p,{'blockHash':rpc.hash,'requireCanonical':True},
            [T.ZERO,addr(21)],timestamp=990,execution_observation=observed)
        return result,observed

    def test_six_exact_capabilities_and_inactive_context_preserve_live_dual_observations(self):
        rpc,p,cfg=verifier();_result,observed=self.verify(rpc,p,cfg)
        self.assertEqual(3,observed['version']);self.assertEqual(1,observed['execution_price_version'])
        self.assertEqual(2,observed['execution_price']['source_revision'])
        self.assertFalse(observed['execution_price']['context_active'])
        self.assertEqual(set(E.ROLES),set(observed['execution_price']['contracts']))
        calls=[params for method,params in rpc.calls if method=='eth_call']
        self.assertTrue(any(row[0]['data']==T.static_data('priceBounds(address)',T.ZERO) for row in calls))
        self.assertFalse(any(row[0]['data'][:10]==T.selector('executionBounds(address)') for row in calls))
        self.assertTrue(all(row[1]=={'blockHash':rpc.hash,'requireCanonical':True} for row in calls))

    def test_each_missing_malformed_or_wrong_capability_and_runtime_fails_closed(self):
        for role in E.ROLES:
            for output in (words(0),'0x','0x01'):
                rpc,p,cfg=verifier();rpc.responses[rpc.pins[role],calldata('EXECUTION_PRICE_VERSION()')]=output
                with self.subTest(role=role,output=output),self.assertRaises((ValueError,ProjectionError)):
                    self.verify(rpc,p,cfg)
            rpc,p,cfg=verifier();rpc.codes[rpc.pins[role]]='0x6000'
            with self.subTest(role=role,runtime=True),self.assertRaises(ProjectionError):self.verify(rpc,p,cfg)

    def test_busy_noncanonical_context_or_oversized_source_revision_is_unavailable(self):
        for method,output in (('executionActive()',words(1)),('executionActive()',words(2)),
                ('executionActive()','0x'),('executionSourceRevision()',words(2**64))):
            rpc,p,cfg=verifier();rpc.responses[rpc.pins['oracle'],calldata(method)]=output
            with self.subTest(method=method,output=output),self.assertRaises((ValueError,ProjectionError)):
                self.verify(rpc,p,cfg)

    def test_read_only_profile_needs_no_new_oracle_roles_or_source_reads(self):
        f=Fresh7API(self);old=set(f.config['contracts']);f.config['execution_price_version']=1
        for role in ('liquidity','balancing_router','strategy','lp_position_executor','lp_balance_math'):
            f.rpc.put(f.c[role],'EXECUTION_PRICE_VERSION()',values=(1,))
        f.rpc.put(f.c['liquidity'],'executionStrategy()',values=(f.c['lp_balance_math'],))
        for role in ('liquidity','balancing_router'):f.rpc.put(f.c[role],'LP_ROUTING_VERSION()',values=(3,))
        p=Projection(f.config,f.rpc,clock=lambda:4000)
        self.assertEqual('operating',p._verify_deployment(f.block())['state'])
        self.assertEqual(old,set(p.contracts));self.assertNotIn('oracle',p.contracts)
        self.assertEqual('18',p.nft(f.rpc.nft_id)['claimable']['lp'][0]['raw'])
        f.rpc.put(f.c['liquidity'],'LP_ROUTING_VERSION()',values=(2,))
        with self.assertRaises(ProjectionError):p._verify_deployment(f.block())

    def test_lp3_without_context_or_context_on_lp2_never_reads_or_guesses(self):
        for routing,context in ((3,0),(2,1),(3,True)):
            with self.subTest(routing=routing,context=context),self.assertRaises(ValueError):
                observe_lp(lambda *_:self.fail('Profile validation must precede reads'),
                    liquidity=addr(1),router=addr(2),pool_manager=addr(3),state_view=addr(4),access=addr(5),pools=addr(6),
                    routing_version=routing,execution_price_version=context)

    def test_schema17_selects_exact_existing_caps_without_changing_canonical_shape(self):
        f=json.loads((Path(__file__).resolve().parents[1]/'config/production.example.json').read_text())
        old=P.expected_bindings(f['chains'][0]);fresh=P.expected_bindings(f['chains'][0],1)
        self.assertEqual(old['modules']['canonical'],fresh['modules']['canonical'])
        self.assertEqual(set(old['helpers']),set(fresh['helpers']))
        for group,role in E.INVENTORY_ROLES:self.assertEqual(1,fresh[group][role]['EXECUTION_PRICE_VERSION'])
        self.assertFalse(fresh['modules']['oracle']['executionActive'])
        for group,role in (('modules','liquidity'),('helpers','balancing_router')):
            self.assertEqual(2,old[group][role]['LP_ROUTING_VERSION']);self.assertEqual(3,fresh[group][role]['LP_ROUTING_VERSION'])
        f.update(execution_price_version=1,lp_routing_version=3)
        with patch.object(P.BASE,'_validate',return_value={}) as validate:P.validate(f)
        args=validate.call_args.kwargs
        self.assertEqual(1,args['versions']['execution_price_version']);self.assertEqual(3,args['versions']['lp_routing_version'])
        self.assertIn('execution_price_version',args['top_fields']);self.assertIsNotNone(args['execution_validator'])

    def test_observer_new_getters_use_strict_bool_and_uint_codecs(self):
        observer=object.__new__(Observer)
        observer.read=lambda target,signature:[f'{1:064x}']
        self.assertEqual(1,observer.typed(addr(1),'EXECUTION_PRICE_VERSION',1))
        self.assertIs(True,observer.typed(addr(1),'executionActive',False))
        observer.read=lambda target,signature:[f'{2:064x}']
        with self.assertRaises(ValueError):observer.typed(addr(1),'executionActive',False)

    def test_observer_selection_is_explicit_and_preserves_the_input(self):
        from zzz_ops import production_observer_v15 as O
        f=json.loads((Path(__file__).resolve().parents[1]/'config/production.example.json').read_text())
        f.update(execution_price_version=1,lp_routing_version=3);before=copy.deepcopy(f)
        with patch.object(P,'precheck_chain'),patch.object(O.BASE,'_observe',return_value={'injected':True}) as actual:
            self.assertEqual({'injected':True},O.observe(f,object()))
        profile=actual.call_args.kwargs['profile']
        self.assertEqual(3,profile.VERSIONS['lp_routing_version'])
        self.assertEqual(1,profile.expected_bindings(f['chains'][0])['modules']['oracle']['EXECUTION_PRICE_VERSION'])
        self.assertEqual(before,f)
        for value in (True,False,'1',2,None):
            f['execution_price_version']=value
            with self.subTest(value=value),patch.object(P,'precheck_chain') as check,self.assertRaises(ValueError):O.observe(f,object())
            check.assert_not_called()

    def test_manual_reader_supports_lp3_with_existing_guards_and_explicit_force(self):
        from tests_python.test_manual_lp_review import ManualLPReviewTests
        from zzz_ops import manual_lp_review as M
        case=ManualLPReviewTests('runTest')
        case.catalog=SimpleNamespace(reference_sha256='1'*64,source_snapshot_sha256='2'*64)
        case.setUp();self.addCleanup(case.doCleanups)
        case.config['execution_price_version']=1
        for role in E.ROLES+('lp_balance_math',):case.put(role,'EXECUTION_PRICE_VERSION()',1)
        for role in ('liquidity','balancing_router'):case.put(role,'LP_ROUTING_VERSION()',3)
        case.put('liquidity','executionStrategy()',case.targets['lp_balance_math'])
        case.put('oracle','executionActive()',0);case.put('oracle','executionSourceRevision()',1)
        p=Projection(case.config,case.rpc,clock=lambda:4000)
        for action,checks in (('B','14'),('C','0'),('D','0')):
            case.request.update(action=action,checks=checks)
            case.rpc.price_failure=checks=='0'
            reader=M.Reader(p,case.extra,case.f.block())
            snapshot=reader.snapshot(M.selection(case.request),case.gov,full=True)
            self.assertEqual(case.gov,snapshot['governance'])
            self.assertEqual(2,snapshot['physical']['portfolio_version'])
            self.assertEqual(1,snapshot['execution_price']['source_revision'])
            if checks=='0':self.assertEqual('not_retained',snapshot['financial']['state'])
        changed=copy.deepcopy(snapshot);changed['execution_price']['source_revision']+=1
        self.assertNotEqual(M.controls(snapshot),M.controls(changed))


class ExecutionPriceTraceTests(unittest.TestCase):
    """Synthetic hostile derivatives; original actual source9 bytes stay intact."""
    def setUp(self):
        path=Path(__file__).parent/'fixtures/source9-entry3-actual-trace7.json.gz'
        self.old=json.loads(gzip.decompress(path.read_bytes()))
        self.root=copy.deepcopy(self.old['actual_trace_call']['result'])
        self.req=copy.deepcopy(self.old['request']);self.pins=self.old['pins']
        self.req.update(execution_price_version=1,lp_routing_version=3)
        self.flat=[]
        def visit(frame):
            self.flat.append(frame)
            for nested in frame.get('calls',[]):visit(nested)
        visit(self.root)
        helper=self.pins['contribution_pricing'];oracle=self.pins['oracle']
        self.begun=next(x for x in self.root['calls'] if x.get('to')==helper and x['input'][:10]==T.selector(T.BEGIN_ENTRY_REVIEWED_V2))
        self.ended=next(x for x in self.root['calls'] if x.get('to')==helper and x['input']==calldata('endEntry()'))
        def frame(signature,*args):return dict(type='CALL',**{'from':helper},to=oracle,input=calldata(signature,*args),output='0x',value='0x0',calls=[])
        self.open=frame('beginExecution(address)',self.req['token1']);self.close=frame('endExecution()')
        self.begun['calls'].insert(0,self.open);self.ended.setdefault('calls',[]).append(self.close)
        for item in self.flat:
            if item.get('from')==helper and item.get('to')==oracle and item['input'][:10]==T.selector('priceBounds(address)'):
                item['input']=T.selector('executionBounds(address)')+item['input'][10:]
        self.finish=next(x for x in self.flat if x.get('to')==helper and x.get('input','')[:10]==T.selector(T.FINISH_PRICING))
        self.old_phases=[x for x in self.finish['calls'] if x.get('from')==helper and x.get('input','')[:10] in
            (T.selector('compositionEpoch(uint256)'),T.selector('compoundBalance(uint256,address)'))]
        self.finish['calls']=[x for x in self.finish['calls'] if x not in self.old_phases]
        self.plan=next(x for x in self.flat if x.get('to')==self.pins['balancing_router'] and x.get('input','')[:10]==T.selector('plan(bytes32,int24,int24,uint256,uint256)'))
        self.old_plan=self.plan['output'];values=[int(x,16) for x in decode_words(self.old_plan)]
        lo,hi=-887272,887271
        while lo<hi:
            mid=(lo+hi+1)//2
            if sqrt_price_at_tick(mid)<=values[5]:lo=mid
            else:hi=mid-1
        self.plan['output']='0x'+''.join(f'{x%(1<<256):064x}' for x in values+[values[5],lo,0,10020,10**24])

    def measure(self):
        return T.measure(self.root,self.old['actual_trace_call']['params'][0],self.pins,self.req,
            self.old['gross_usd_18'],self.old['max_slippage_bps'])

    def test_explicit_synthetic_graph_preserves_exact_marginal_lp_and_shares(self):
        self.assertEqual(self.old['expected_measurement'],self.measure())

    def test_old_trace_cannot_be_promoted_by_only_setting_the_new_flag(self):
        self.root=copy.deepcopy(self.old['actual_trace_call']['result'])
        with self.assertRaises(ProjectionError):self.measure()

    def test_missing_duplicate_or_foreign_begin_and_missing_end_fail_closed(self):
        for kind in ('missing','duplicate','foreign','end'):
            with self.subTest(kind=kind):
                saved=copy.deepcopy(self.root)
                if kind=='missing':self.begun['calls'].remove(self.open)
                elif kind=='duplicate':self.begun['calls'].append(copy.deepcopy(self.open))
                elif kind=='foreign':self.open['from']=self.pins['entry']
                else:self.ended['calls'].remove(self.close)
                with self.assertRaises(ProjectionError):self.measure()
                self.setUp()

    def test_changed_capture_or_live_reread_cannot_reprice_entrant(self):
        bound=next(x for x in self.flat if x.get('from')==self.pins['contribution_pricing'] and x.get('input','')[:10]==T.selector('executionBounds(address)'))
        original=dict(bound)
        bound['output']=words(1,1,1)
        with self.assertRaises(ProjectionError):self.measure()
        bound.update(original);bound['input']=T.selector('priceBounds(address)')+bound['input'][10:]
        with self.assertRaises(ProjectionError):self.measure()

    def test_historical_epoch_and_nine_word_plan_are_rejected_by_new_profile(self):
        self.finish['calls'].extend(self.old_phases)
        with self.assertRaises(ProjectionError):self.measure()
        self.finish['calls']=[x for x in self.finish['calls'] if x not in self.old_phases]
        self.plan['output']=self.old_plan
        with self.assertRaises(ProjectionError):self.measure()

    def test_malformed_physical_transition_cannot_supply_lp3_proof(self):
        values=decode_words(self.plan['output']);values[9]=f'{int(values[9],16)+1:064x}'
        self.plan['output']='0x'+''.join(values)
        with self.assertRaises(ProjectionError):self.measure()
