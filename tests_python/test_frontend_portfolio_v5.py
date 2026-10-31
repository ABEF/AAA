"""Fresh portfolio API boundaries; synthetic transcripts, no network or signer."""
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from frontend_api.service import Contract,Projection,ProjectionError
from frontend_api.portfolio_v5 import ROLES,verify_profile,read_bucket
from frontend_api import activation_trace as trace
from frontend_api.activation_config import ActivationConfig
from tests_python.test_frontend_api import addr,configuration
from tests_python.test_holder_exit_profile import setup_api
from tests_python.test_keeper_portfolio_policy import PortfolioRPC
from zzz_ops.abi import keccak256
from zzz_ops.tick_math import sqrt_price_at_tick


def fresh_configuration():
    config,rpc=setup_api()
    config['accounting_version']=5
    for ordinal,role in enumerate(ROLES,100):
        code='0x'+bytes((0x60,ordinal,0)).hex()
        config['contracts'][role]={'address':addr(ordinal),'code_hash':'0x'+keccak256(bytes.fromhex(code[2:])).hex()}
        rpc.codes[addr(ordinal)]=code
    return config,rpc


class ProfileTranscript:
    def __init__(self):
        names=('access','vault','principal_exit')+ROLES
        self.contracts={role:Contract(addr(ordinal),'0x'+'a'*64) for ordinal,role in enumerate(names,1)}
        self.values={};self.calls=[];self.block={'blockHash':'0x'+'b'*64,'requireCanonical':True}
        self.bindings=(('vault','migrationBudget()','budget'),('budget','vault()','vault'),
            ('strategy','portfolioPolicy()','portfolio_policy'),('portfolio_policy','strategy()','strategy'),
            ('strategy','rebalanceConfirmation()','rebalance_confirmation'),('rebalance_confirmation','strategy()','strategy'),
            ('liquidity','balancingRouter()','balancing_router'),('balancing_router','liquidityManager()','liquidity'),
            ('balancing_router','balanceMath()','lp_balance_math'),('lp_balance_math','balancer()','balancing_router'),
            ('balancing_router','poolManager()','pool_manager'),('balancing_router','stateView()','state_view'),
            ('liquidity','positionOperator()','lp_position_executor'),('lp_position_executor','liquidityManager()','liquidity'),
            ('lp_position_executor','positionManager()','position_manager'),('lp_position_executor','stateView()','state_view'),
            ('lp_position_executor','poolManager()','pool_manager'),('lp_position_executor','permit2()','permit2'),
            ('lp_position_executor','balancingRouter()','balancing_router'),
            ('liquidity','positionManager()','position_manager'),('liquidity','stateView()','state_view'),
            ('liquidity','poolManager()','pool_manager'),('liquidity','permit2()','permit2'),
            ('state_view','poolManager()','pool_manager'),('position_manager','poolManager()','pool_manager'),
            ('position_manager','permit2()','permit2'))
        for role,method,target in self.bindings:self.values[role,method,()]=int(self.contracts[target].address,16)
        for role in ('pools','liquidity','strategy','budget','portfolio_policy','rebalance_confirmation','balancing_router','lp_position_executor'):
            self.values[role,'access()',()]=int(self.contracts['access'].address,16)
        for role,label in (('pools','ZZZPoolRegistry'),('liquidity','ZZZLiquidityManager'),('strategy','ZZZStrategy')):
            self.values['access','module(bytes32)',('0x'+keccak256(label.encode()).hex(),)]=int(self.contracts[role].address,16)
        versions={'vault':{'ACCOUNTING_VERSION()':5},'strategy':{'MAINTENANCE_POLICY_VERSION()':3,'REBALANCE_CONFIRMATION_VERSION()':3},
            'rebalance_confirmation':{'REBALANCE_CONFIRMATION_VERSION()':3},
            'budget':{'IDLE_COMPOUNDING_VERSION()':4,'REBALANCE_CONFIRMATION_VERSION()':3,'EMERGENCY_REBALANCE_VERSION()':2},
            'principal_exit':{'EMERGENCY_REBALANCE_VERSION()':2},
            'liquidity':{'PORTFOLIO_VERSION()':1,'LP_ROUTING_VERSION()':2,'EMERGENCY_REBALANCE_VERSION()':2},
            'balancing_router':{'LP_ROUTING_VERSION()':2},'lp_balance_math':{'LP_BALANCE_MATH_VERSION()':1},
            'lp_position_executor':{'LP_POSITION_EXECUTOR_VERSION()':1},
            'portfolio_policy':{'PORTFOLIO_VERSION()':1,'minimumMainBps()':6000,'maximumResidualBps()':4000}}
        for role,methods in versions.items():
            for method,value in methods.items():self.values[role,method,()]=value

    def _call(self,target,method,*args,block,words=1):
        if block!=self.block:raise AssertionError('Not the reviewed canonical block')
        role=next(role for role,item in self.contracts.items() if item.address==target)
        self.calls.append((role,method,args,block))
        value=self.values[role,method,args]
        return [f'{value:064x}']


class FrontendPortfolioV5Tests(unittest.TestCase):
    def test_fresh_profile_requires_every_explicit_helper_pin(self):
        config,rpc=fresh_configuration()
        projection=Projection(config,rpc)
        self.assertEqual(5,projection.accounting_version)
        self.assertEqual(3,projection.dormant_status)
        for role in ROLES:
            bad=copy.deepcopy(config);bad['contracts'].pop(role)
            with self.subTest(role=role),self.assertRaises(ValueError):Projection(bad,rpc)

    def test_old_profile_contract_inventory_is_not_relabelled(self):
        config,rpc=setup_api();legacy=Projection(config,rpc)
        self.assertEqual(4,legacy.accounting_version);self.assertNotIn('portfolio_policy',legacy.contracts)
        bad=copy.deepcopy(config);bad['accounting_version']=5
        with self.assertRaises(ValueError):Projection(bad,rpc)
        oldest=Projection(configuration(),rpc)
        self.assertEqual(1,oldest.accounting_version);self.assertEqual(5,oldest.dormant_status)

    def test_new_capabilities_and_reverse_bindings_are_block_pinned(self):
        p=ProfileTranscript();verify_profile(p,p.block)
        self.assertGreater(len(p.calls),30)
        for role,method,target in p.bindings:
            altered=ProfileTranscript();altered.values[role,method,()]=int(addr(999),16)
            with self.subTest(role=role,method=method),self.assertRaises(ProjectionError):verify_profile(altered,altered.block)

    def test_historical_capabilities_cannot_pass_fresh_profile(self):
        for role,method,old in (('vault','ACCOUNTING_VERSION()',4),('strategy','MAINTENANCE_POLICY_VERSION()',2),
                ('budget','IDLE_COMPOUNDING_VERSION()',3),('rebalance_confirmation','REBALANCE_CONFIRMATION_VERSION()',2),
                ('liquidity','LP_ROUTING_VERSION()',1),('liquidity','EMERGENCY_REBALANCE_VERSION()',1),
                ('portfolio_policy','minimumMainBps()',0),('lp_balance_math','LP_BALANCE_MATH_VERSION()',0)):
            p=ProfileTranscript();p.values[role,method,()]=old
            with self.subTest(role=role,method=method),self.assertRaises(ProjectionError):verify_profile(p,p.block)

    def test_fresh_unsigned_configuration_requires_matching_reviewed_helpers_and_versions(self):
        from tests_python.test_lp_execution_profile import routing_service
        rpc,_old,_service=routing_service()
        cfg=copy.deepcopy(rpc.config)
        cfg.update(maintenance_policy_version=3,lp_routing_version=2,execution_quality_version=1,
            rebalance_confirmation_version=3,portfolio_version=1)
        for ordinal,role in enumerate(('portfolio_policy','rebalance_confirmation','lp_balance_math','lp_position_executor'),150):
            target=addr(ordinal);rpc.codes[target]='0x'+bytes((0x60,ordinal,0)).hex();rpc.pins[role]=target
            cfg['contracts'][role]=dict(address=target,code_hash=rpc.digest(target))
        read=configuration();read.update(accounting_version=5,fee_intake_version=1)
        read['assets']=[read['assets'][0],dict(address=addr(21),decimals=18,symbol='ZZZ',code_hash=rpc.digest(addr(21)))]
        read['contracts']['principal_exit']=dict(cfg['contracts']['migration'])
        for role in ROLES:
            target=rpc.pins[role]
            read['contracts'][role]=dict(address=target,code_hash=rpc.digest(target))
        p=Projection(read,rpc);accepted=ActivationConfig(cfg,p)
        self.assertEqual(1,accepted.portfolio_version);self.assertEqual(2,accepted.lp_routing_version)
        for key,value in (('maintenance_policy_version',2),('lp_routing_version',1),('portfolio_version',0),
                ('rebalance_confirmation_version',2),('execution_quality_version',0)):
            bad=copy.deepcopy(cfg);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):ActivationConfig(bad,p)
        bad=copy.deepcopy(cfg);bad['contracts']['portfolio_policy']['code_hash']='0x'+'e'*64
        with self.assertRaisesRegex(ValueError,'pins differ'):ActivationConfig(bad,p)
        bad=copy.deepcopy(cfg);bad['dependencies'][0]['code_hash']='0x'+'e'*64
        with self.assertRaisesRegex(ValueError,'dependency pins differ'):ActivationConfig(bad,p)

    def physical(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        rpc=PortfolioRPC(Path(tmp.name)/'inert-state.json')
        block={'blockHash':'0x'+'ab'*32,'requireCanonical':True}
        contracts={role:Contract(target,rpc.pin) for role,target in rpc.contracts.items()}
        def call(target,method,*args,block,words=1):
            if block!={'blockHash':'0x'+'ab'*32,'requireCanonical':True}:raise AssertionError('Unpinned portfolio read')
            result=rpc.read(target,method,*args,count=words)
            if len(result)!=words:raise AssertionError('Unexpected fixture result length')
            return result
        return rpc,SimpleNamespace(contracts=contracts,_call=call,rpc=rpc),block

    def test_single_and_two_leg_principal_are_exact_aggregate_not_liquidity_sum(self):
        rpc,p,block=self.physical();single=read_bucket(p,7,block)
        self.assertIsNone(single['secondary_lp_token_id']);self.assertEqual(['100','200'],single['principal_amounts_raw'])
        rpc.secondary=124;rpc.secondary_count=1;rpc.summed=(130,240)
        dual=read_bucket(p,7,block)
        self.assertEqual('124',dual['secondary_lp_token_id']);self.assertEqual(2,len(dual['physical_legs']))
        self.assertEqual(['130','240'],dual['principal_amounts_raw'])

    def test_disabled_desired_mode_preserves_live_residual_until_merge(self):
        rpc,p,block=self.physical();rpc.mode=0;rpc.secondary=124;rpc.secondary_count=1;rpc.summed=(130,240)
        value=read_bucket(p,7,block)
        self.assertFalse(value['desired_residual_enabled']);self.assertEqual('124',value['secondary_lp_token_id'])

    def test_missing_wrong_owner_duplicate_or_omitted_secondary_fails_closed(self):
        for fault in ('owner','duplicate','amounts','count','geometry'):
            rpc,p,block=self.physical();rpc.secondary=124;rpc.secondary_count=1;rpc.summed=(130,240)
            if fault=='owner':rpc.fail_leg_owner=True
            elif fault=='duplicate':rpc.secondary=123
            elif fault=='amounts':rpc.summed=(100,200)
            elif fault=='count':rpc.secondary_count=0
            else:rpc.aux_ticks=(110,205)
            with self.subTest(fault=fault),self.assertRaises(ProjectionError):read_bucket(p,7,block)

    def test_bad_physical_runtime_is_never_accepted_as_zero_principal(self):
        rpc,p,block=self.physical();rpc.code_overrides[rpc.contracts['state_view']]='0x6001'
        with self.assertRaises(ProjectionError):read_bucket(p,7,block)

    def test_exact_executor_ancestry_is_required_only_for_fresh_trace(self):
        pins={'liquidity':addr(1),'lp_position_executor':addr(2)}
        data=trace.selector(trace.INCREASE)+'00'*192
        child=dict(type='CALL',**{'from':addr(1),'to':addr(2),'input':data,'output':'0x'+'00'*64,'value':'0x123'})
        parent=dict(type='CALL',**{'from':addr(3),'to':addr(1),'input':data,'output':child['output'],'value':'0x123','calls':[child]})
        req=dict(accounting_version=5,lp_routing_version=2,portfolio_version=1)
        execution,operator=trace.lp_execution_frame(parent,pins,req,False)
        self.assertIs(child,execution);self.assertEqual(addr(2),operator)
        legacy,operator=trace.lp_execution_frame(parent,pins,{'accounting_version':4},False)
        self.assertIs(parent,legacy);self.assertEqual(addr(1),operator)
        for field,value in (('value','0x124'),('output','0x'),('type','STATICCALL'),('from',addr(99))):
            bad=copy.deepcopy(parent);bad['calls'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ProjectionError):trace.lp_execution_frame(bad,pins,req,False)
        bad=copy.deepcopy(parent);bad['calls'].append(copy.deepcopy(child))
        with self.assertRaises(ProjectionError):trace.lp_execution_frame(bad,pins,req,False)

    def context(self):
        from tests_python.test_keeper_compound_range_policy import words
        rpc,p,block=self.physical();p.accounting_version=5
        p.contracts['budget']=Contract(rpc.budget,rpc.pin)
        strategy=rpc.contracts['strategy'];rpc.tick=90
        for method,values in (('RANGE_POLICY_VERSION()',(1,)),('keeperRangePolicy(bytes32)',(0,0,0,0,0,0,0)),
                ('keeperRangeTarget(bytes32)',(0,)),('validatePrice(bytes32)',(sqrt_price_at_tick(90),))):
            rpc.overrides[strategy,method]=words(*values)
        rpc.overrides[rpc.contracts['liquidity'],'executionPortfolioFingerprint(uint256)']=words(303)
        intended=dict(orientation=1,keeper=dict(enabled=False,narrow_trigger_bps=0,widen_trigger_bps=0,
            minimum_interval_seconds=0,configuration_hash='0x'+'00'*32,review_hash='0x'+'00'*32))
        pins={role:item.address for role,item in p.contracts.items()}
        return rpc,p,pins,block,intended

    def test_fresh_context_separates_inside_range_trigger_cooldown_and_sampled_readiness(self):
        from frontend_api.portfolio_v5 import contribution_context
        from tests_python.test_keeper_compound_range_policy import words
        rpc,p,pins,block,intended=self.context();rpc.position[6]=rpc.now-3600
        result=contribution_context(p,pins,rpc.pool,7,words(*rpc.position),words(*rpc.config),
            {'timestamp':rpc.now},block,range_policy_version=1,range_policy=intended,
            maintenance_policy_version=3,rebalance_confirmation_version=3)
        self.assertTrue(result['in_range']);self.assertTrue(result['rebalance']['price_trigger_met'])
        self.assertFalse(result['rebalance']['raw_eligible_at_snapshot'])
        self.assertFalse(result['rebalance']['eligible_at_snapshot']);self.assertEqual('cooldown',result['rebalance']['status'])
        self.assertEqual(8500,result['rebalance']['trigger_bps'])
        self.assertEqual('0x'+f'{303:064x}',result['portfolio']['execution_portfolio_fingerprint'])
        self.assertIn('accumulate before',result['rebalance']['explanation'])

    def test_fresh_context_does_not_infer_confirmation_from_elapsed_cooldown(self):
        from frontend_api.portfolio_v5 import contribution_context
        from tests_python.test_keeper_compound_range_policy import words
        rpc,p,pins,block,intended=self.context()
        result=contribution_context(p,pins,rpc.pool,7,words(*rpc.position),words(*rpc.config),
            {'timestamp':rpc.now},block,range_policy_version=1,range_policy=intended,
            maintenance_policy_version=3,rebalance_confirmation_version=3)
        self.assertTrue(result['rebalance']['raw_eligible_at_snapshot'])
        self.assertFalse(result['rebalance']['eligible_at_snapshot'])
        self.assertEqual('waiting_first_observation',result['rebalance']['status'])
        self.assertIsNone(result['rebalance']['expected_execution_at'])
        with self.assertRaises(ProjectionError):
            contribution_context(p,pins,rpc.pool,7,words(*rpc.position),words(*rpc.config),
                {'timestamp':rpc.now},block,range_policy_version=1,range_policy=intended,
                maintenance_policy_version=2,rebalance_confirmation_version=2)


if __name__=='__main__':unittest.main()
