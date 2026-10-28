"""LP-routing1 read/trace boundaries; synthetic RPC only, no signer/service."""
import copy
import unittest
from unittest.mock import patch

from frontend_api.activation import ActivationTransactions
from frontend_api import activation_trace as T
from frontend_api.service import ProjectionError
from keeper.monitor import Keeper
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError
from tests_python.test_frontend_api import addr, words
from tests_python.test_liquidity_context_policy2 import setup_service
from tests_python import test_keeper_outside_schedule as scheduling

USD=10**18


def routing_service(*, capped=True, incumbent_idle=0, fresh=0, late=0, new_pool=False):
    rpc,p,_service=setup_service(new_pool=new_pool,increase=not new_pool)
    router=addr(92);rpc.codes[router]='0x600092';rpc.pins['balancing_router']=router
    rpc.config['lp_routing_version']=1
    rpc.config['contracts']['balancing_router']=dict(address=router,code_hash=rpc.digest(router))
    bindings={rpc.pins['liquidity']:{'LP_ROUTING_VERSION()':1,'balancingRouter()':router},router:{
        'LP_ROUTING_VERSION()':1,'access()':addr(1),'liquidityManager()':rpc.pins['liquidity'],
        'poolManager()':rpc.pins['pool_manager'],'stateView()':rpc.pins['state_view'],
        'executionRevision()':1,'MAX_EXECUTION_POOLS()':4,'executionPoolCount()':1,
        'searchIterations()':8,'quoteGasLimit()':200000},rpc.pins['pools']:{'configurationRevision()':1}}
    for target,fields in bindings.items():
        for method,value in fields.items():rpc.put(target,method,values=(value,))
    rpc.put(router,'executionPoolAt(uint256)',(0,),(rpc.pool,))
    original=rpc.trace
    rpc.routing_mutation=None
    def trace(tx):
        root=original(tx);vault=next(x for x in root['calls'] if x['to']==addr(3))
        children=vault['calls'];mint=next(x for x in children if x['to']==rpc.pins['liquidity'])
        navs=[x for x in children if x['input'].startswith(T.selector(T.NAV_PRICING))]
        check=children[-1];finish=check['calls'][0]
        supply=0 if new_pool else 1000*USD;old=0 if new_pool else 1000*USD
        idle=(incumbent_idle+fresh+late)*USD
        nav=old+idle;deployed=old+99*USD;net=99*USD
        limits=rpc.economics[-1]|rpc.loss<<16
        economics=[100*USD,supply,nav,old if capped else nav,deployed,idle,limits]
        issued=supply*net//nav if supply else net
        check.update(input=calldata(T.CONFIGURABLE_RESULT,rpc.bucket,*economics),output=words(issued,net))
        finish.update(input=calldata(T.FINISH_PRICING,rpc.bucket,*economics),output=check['output'])
        finish['logs'][0]['data']=words(100*USD,100*USD,99*USD,net,2**96,'0x'+'88'*32)
        vault['logs'][0]['data']=words(issued,net)
        for frame,values in zip(navs,[(old,incumbent_idle*USD),(old,(100+incumbent_idle+fresh)*USD),(deployed,idle)]):
            frame['output']=words(*values);frame['calls'][0]['output']=frame['output']
        compounds=[x for x in children if x['input'].startswith(T.selector('valueBucket(uint256,uint256,uint256)'))]
        for frame,value in zip(compounds,([fresh*USD,late*USD] if supply else [late*USD])):
            frame['output']=words(value);frame['calls'][0]['output']=frame['output']
        q=[int(w,16) for w in T.words('0x'+vault['input'][10:],5 if rpc.request['action']=='increase' else 6)]
        offset=1 if rpc.request['action']=='increase' else 2
        raw0,raw1=q[offset:offset+2];deadline=q[-1]
        balanced=dict(type='CALL',**{'from':addr(3),'to':rpc.pins['liquidity'],
            'input':calldata(T.BALANCE,rpc.pool,0 if new_pool else rpc.lp_id,raw0,raw1,deadline),
            'output':words(50*USD,49*USD),'value':hex(raw0),'calls':[]})
        def context():
            nested=dict(type='STATICCALL',**{'from':rpc.pins['budget'],'to':rpc.pins['liquidity'],
                'input':calldata('balanceContext(bytes32)',rpc.pool),'output':words(123),'calls':[]})
            return dict(type='STATICCALL',**{'from':addr(3),'to':rpc.pins['budget'],
                'input':calldata('balanceContext(uint256)',rpc.bucket),'output':words(123),'calls':[nested]})
        children[children.index(navs[1]):children.index(navs[1])]=[context(),balanced,context()]
        params=T.words('0x'+mint['input'][10:],7 if new_pool else 6);index=3 if new_pool else 2
        params[index:index+2]=[f'{50*USD:064x}',f'{49*USD:064x}']
        mint['input']=mint['input'][:10]+''.join(params);mint['value']=hex(50*USD)
        mint['output']=words(rpc.lp_id,50*USD,49*USD) if new_pool else words(50*USD,49*USD)
        if rpc.routing_mutation:rpc.routing_mutation(root)
        return root
    rpc.trace=trace
    return rpc,p,ActivationTransactions(p,rpc.config)


class LPExecutionProfileTests(unittest.TestCase):
    def test_fresh_capped_contribution_preserves_incumbent_idle_and_compound(self):
        rpc,_p,service=routing_service(incumbent_idle=5,fresh=2,late=3)
        result=service.prepare(rpc.request)
        self.assertTrue(result['activation_ready'])
        self.assertEqual(result['provenance']['lp_routing_version'],1)
        self.assertEqual(result['contribution']['marginal_deployed_usd_18'],str(99*USD))
        self.assertEqual(result['contribution']['shares_added_raw'],str(1000*USD*99//1010))
        self.assertEqual(result['provenance']['lp_execution']['execution_pools'],[rpc.pool])
        self.assertFalse(result['provenance']['lp_execution']['catalog_frozen_by_wallet_review'])

    def test_current_new_lp_exact_balance_and_put_are_accepted(self):
        rpc,_p,service=routing_service(new_pool=True)
        self.assertTrue(service.prepare(rpc.request)['activation_ready'])

    def test_old_subsidizing_equation_is_rejected_under_new_profile(self):
        rpc,_p,service=routing_service(capped=False,incumbent_idle=5)
        with self.assertRaisesRegex(ProjectionError,'incumbent assets'):service.prepare(rpc.request)

    def test_exact_balance_budget_and_capped_put_cannot_include_incumbents(self):
        def children(root):return next(x for x in root['calls'] if x['to']==addr(3))['calls']
        def overbalance(root):
            frame=next(x for x in children(root) if x['input'].startswith(T.selector(T.BALANCE)))
            params=T.words('0x'+frame['input'][10:],5);params[2]=f'{101*USD:064x}'
            frame['input']=frame['input'][:10]+''.join(params)
        def overput(root):
            frame=next(x for x in children(root) if x['input'].startswith(T.selector(T.INCREASE)))
            params=T.words('0x'+frame['input'][10:],6);params[2]=f'{55*USD:064x}'
            frame['input']=frame['input'][:10]+''.join(params)
        def removebalance(root):children(root)[:]=[x for x in children(root) if not x['input'].startswith(T.selector(T.BALANCE))]
        for mutation in (overbalance,overput,removebalance):
            with self.subTest(mutation=mutation.__name__):
                rpc,_p,service=routing_service();rpc.routing_mutation=mutation
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_router_runtime_parent_version_and_solver_metadata_fail_closed(self):
        for method,value in [('liquidityManager()',addr(300)),('poolManager()',addr(300)),
                ('stateView()',addr(300)),('LP_ROUTING_VERSION()',0),('searchIterations()',13),
                ('quoteGasLimit()',99999),('executionPoolCount()',5),('executionRevision()',1<<64)]:
            with self.subTest(method=method):
                rpc,_p,service=routing_service();rpc.put(addr(92),method,values=(value,))
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)
        rpc,_p,service=routing_service();rpc.codes[addr(92)]='0x600093'
        with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_empty_catalog_reported_without_synthetic_target_fallback(self):
        rpc,_p,service=routing_service();rpc.put(addr(92),'executionPoolCount()',values=(0,))
        observation={}
        pins,_prices=service.config.verify(service.p,{'blockHash':rpc.hash,'requireCanonical':True},[rpc.source],timestamp=990,execution_observation=observation)
        self.assertIn('balancing_router',pins)
        self.assertFalse(observation['swaps_enabled'])
        self.assertEqual(observation['execution_pools'],[])

    def test_policy_boundary_change_rejected_and_expected_quote_revert_allowed(self):
        def children(root):return next(x for x in root['calls'] if x['to']==addr(3))['calls']
        def changed(root):
            frame=[x for x in children(root) if x['input'].startswith(T.selector('balanceContext(uint256)'))][-1]
            frame['output']=words(124);frame['calls'][0]['output']=words(124)
        rpc,_p,service=routing_service();rpc.routing_mutation=changed
        with self.assertRaisesRegex(ProjectionError,'policy changed'):service.prepare(rpc.request)
        def quoted(root):
            frame=next(x for x in children(root) if x['input'].startswith(T.selector(T.BALANCE)))
            frame['calls']=[dict(type='CALL',**{'from':rpc.pins['balancing_router'],
                'to':rpc.pins['pool_manager'],'input':'0x12345678','output':'0x12345678','error':'execution reverted','calls':[]})]
        rpc,_p,service=routing_service();rpc.routing_mutation=quoted
        self.assertTrue(service.prepare(rpc.request)['activation_ready'])

    def test_new_swap_guard_ceiling_is_explicit_not_applied_to_historical_profiles(self):
        for current in (True,False):
            rpc,_p,service=routing_service() if current else setup_service()
            rpc.economics=(*rpc.economics[:-1],500);rpc.pool_values[10]=500
            for getter in ('get(bytes32)','accounting(bytes32)'):rpc.put(rpc.pins['pools'],getter,(rpc.pool,),rpc.pool_values)
            if current:self.assertTrue(service.prepare(rpc.request)['activation_ready'])
            else:
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_historical_profile_stays_explicit_zero_without_router_reads(self):
        rpc,_p,service=setup_service()
        result=service.prepare(rpc.request)
        self.assertEqual(result['provenance']['lp_routing_version'],0)
        self.assertNotIn('lp_execution',result['provenance'])
        self.assertFalse(any(method=='eth_call' and params[0]['data']==calldata('LP_ROUTING_VERSION()') for method,params in rpc.calls))


class KeeperLPExecutionProfileTests(unittest.TestCase):
    def setUp(self):
        self.fixture=scheduling.KeeperOutsideScheduleTests('runTest');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.cfg,self.rpc=self.fixture.cfg,self.fixture.rpc
        for role,n in [('liquidity',92),('balancing_router',93),('pool_manager',94),('state_view',95)]:
            self.cfg['contracts'][role]=addr(n);self.cfg['code_hashes'][role]=self.fixture.pin
        self.cfg['lp_routing_version']=1
        c=self.cfg['contracts'];self.values={}
        def put(role,method,value,*args):self.values[c[role],calldata(method,*args)]=words(value)
        for role in ('liquidity','balancing_router'):
            put(role,'LP_ROUTING_VERSION()',1);put(role,'access()',c['access'])
        for role,method,target in [('liquidity','balancingRouter()','balancing_router'),
                ('liquidity','poolManager()','pool_manager'),('liquidity','stateView()','state_view'),
                ('balancing_router','liquidityManager()','liquidity'),('balancing_router','poolManager()','pool_manager'),
                ('balancing_router','stateView()','state_view')]:put(role,method,c[target])
        for method,value in [('executionRevision()',1),('searchIterations()',8),('quoteGasLimit()',200000),
                ('executionPoolCount()',0),('MAX_EXECUTION_POOLS()',4)]:put('balancing_router',method,value)
        put('pools','configurationRevision()',1);put('pools','access()',c['access'])
        for role,label in [('pools','ZZZPoolRegistry'),('liquidity','ZZZLiquidityManager')]:
            put('access','module(bytes32)',c[role],'0x'+keccak256(label.encode()).hex())
        self.original=self.rpc.call;self.block={'blockHash':'0x'+'44'*32,'requireCanonical':True}
        def call(method,params):
            if method=='eth_getBlockByNumber' and params[0]=='latest':return dict(number='0x64',hash=self.block['blockHash'],timestamp=hex(self.rpc.now))
            if method=='eth_getCode' and params[1]==self.block:return '0x6000'
            if method=='eth_call' and params[1]==self.block:
                self.rpc.calls.append((method,copy.deepcopy(params)))
                key=params[0]['to'],params[0]['data']
                if key not in self.values:raise AssertionError(key)
                return self.values[key]
            return self.original(method,params)
        self.rpc.call=call
        self.k=Keeper(self.cfg,rpc=self.rpc)

    def test_capability_metadata_is_pinned_to_one_block_and_no_signer(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('keeper.monitor.subprocess.run') as signer:
            self.k._validate_lp_routing()
            signer.assert_not_called()
        self.assertFalse(self.k.lp_execution_observation['swaps_enabled'])
        self.assertTrue(all(params[1]==self.block for method,params in self.rpc.calls if method=='eth_call' and params[0]['data']==calldata('LP_ROUTING_VERSION()')))

    def test_wrong_helper_parent_and_unbounded_metadata_rejected(self):
        for method,value in [('liquidityManager()',addr(999)),('LP_ROUTING_VERSION()',0),('executionPoolCount()',5)]:
            key=self.cfg['contracts']['balancing_router'],calldata(method);original=self.values[key]
            self.values[key]=words(value)
            with self.subTest(method=method),patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):self.k._validate_lp_routing()
            self.values[key]=original

    def test_bad_profile_or_missing_runtime_is_rejected_before_signer(self):
        for value in (True,2,'1'):
            with self.subTest(value=value):
                config=copy.deepcopy(self.cfg);config['lp_routing_version']=value
                with self.assertRaises(ValueError):Keeper(config,rpc=self.rpc)
        config=copy.deepcopy(self.cfg);del config['code_hashes']['balancing_router']
        with self.assertRaises(ValueError):Keeper(config,rpc=self.rpc)

    def test_router_observation_failure_does_not_block_independent_due_harvest(self):
        self.k.maintenance=self.cfg['maintenance']={'compound':False,'harvest':True,'harvest_interval_seconds':3600}
        with patch('keeper.monitor.time.time',return_value=self.rpc.now), \
                patch.object(self.k,'_validate_lp_routing',side_effect=RpcError('router unavailable')), \
                patch.object(self.k,'submit',return_value=True) as submitted:
            self.k.cycle()
        submitted.assert_called_once_with('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7')

    def test_live_startup_preserves_pending_recovery_during_helper_outage(self):
        self.cfg.update(reviewed_for_live_use=True,receipt_fee_policy='included')
        self.k.state['next_nonce']=7
        self.k.state['receipt_anchor']=dict(number=98,nonce=6,timestamp=self.rpc.now,hash=scheduling.K.H)
        pending=dict(key='harvest:7',nonce=7,to=self.cfg['contracts']['vault'],
            data=calldata('collectFees(uint256,uint256)',7,self.rpc.now+180),value=0,
            day='2026-10-28',hash=scheduling.K.H,
            fee_review=dict(schema=1,gas_limit=256,max_fee_per_gas=2,l1_fee_allowance_wei=0,
                maximum_cost_wei=512,receipt_fee_policy='included'))
        for has_pending in (True,False):
            self.k.state['pending']=copy.deepcopy(pending) if has_pending else None
            self.k.save();original=self.k.path.read_bytes()
            with self.subTest(has_pending=has_pending),patch('keeper.monitor.time.time',return_value=self.rpc.now), \
                    patch.object(Keeper,'_validate_runtime_files') as files, \
                    patch.object(Keeper,'_validate_signer') as wallet, \
                    patch.object(Keeper,'_validate_code_hashes') as runtime, \
                    patch.object(Keeper,'_validate_lp_routing',side_effect=RpcError('router unavailable')) as router:
                if has_pending:
                    loaded=Keeper(self.cfg,live=True,rpc=self.rpc)
                    self.assertTrue(loaded.poll_pending())
                    self.assertEqual(loaded.state['pending'],pending)
                    router.assert_not_called()
                else:
                    with self.assertRaises(RpcError):Keeper(self.cfg,live=True,rpc=self.rpc)
                    router.assert_called_once()
                files.assert_called_once();wallet.assert_called_once();runtime.assert_called_once()
            self.assertEqual(self.k.path.read_bytes(),original)

    def test_next_balance_submission_still_requires_healthy_router_and_never_signs(self):
        with patch.object(self.k,'_validate_lp_routing',side_effect=RpcError('router unavailable')), \
                patch('keeper.monitor.subprocess.run') as signer, \
                self.assertRaises(RpcError):
            self.k.submit('compounder','compound(uint256,uint128,uint256)',(7,1,self.rpc.now+180),'compound:7')
        signer.assert_not_called();self.assertIsNone(self.k.state['pending'])


if __name__=='__main__':unittest.main()
