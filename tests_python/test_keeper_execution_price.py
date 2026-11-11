"""Explicit fresh LP3 keeper reads/recovery admission; no signer or rollout."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.health import _health_profile_valid,execution_reasons,observe_confirmation_health
from tests_python.test_exact_lp_profile7 import Fresh7KeeperRPC
from tests_python.test_frontend_api import addr
from zzz_ops.abi import calldata
from zzz_ops.execution_price import ROLES
from zzz_ops.rpc import RpcError


class KeeperExecutionPriceTests(unittest.TestCase):
    def fixture(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        rpc=Fresh7KeeperRPC(Path(directory.name)/'state.json');cfg=rpc.cfg
        cfg.update(execution_price_version=1,lp_routing_version=3)
        for role,index in (('oracle',15501),('contribution_pricing',15502)):
            rpc.contracts[role]=addr(index);cfg['code_hashes'][role]=rpc.pin
        replies={}
        def add(role,signature,value):replies[rpc.contracts[role],calldata(signature)]=f'{value:064x}'
        for role in ROLES+('lp_balance_math',):add(role,'EXECUTION_PRICE_VERSION()',1)
        for role in ('liquidity','balancing_router'):add(role,'LP_ROUTING_VERSION()',3)
        add('liquidity','executionStrategy()',int(rpc.contracts['lp_balance_math'],16))
        for role in ('oracle','contribution_pricing'):add(role,'access()',int(rpc.contracts['access'],16))
        add('oracle','contributionPricing()',int(rpc.contracts['contribution_pricing'],16))
        add('contribution_pricing','oracle()',int(rpc.contracts['oracle'],16))
        add('oracle','executionActive()',0);add('oracle','executionSourceRevision()',3)
        original=rpc.call
        def call(method,params):
            if method=='eth_getBlockByNumber' and params[0]!='latest':
                return {**original(method,params),'number':params[0]}
            if method=='eth_call' and 'from' not in params[0] and (params[0]['to'],params[0]['data']) in replies:
                return '0x'+replies[params[0]['to'],params[0]['data']]
            return original(method,params)
        rpc.call=call
        original_read=rpc.read
        def read(target,signature,*args,count=1):
            if not args and (target,calldata(signature)) in replies:return [replies[target,calldata(signature)]]
            return original_read(target,signature,*args,count=count)
        rpc.read=read
        return rpc,cfg,replies

    def test_explicit_profile_reads_all_capabilities_and_existing_math_binding(self):
        rpc,cfg,_=self.fixture();k=Keeper(cfg,rpc=rpc)
        with patch('keeper.monitor.time.time',return_value=rpc.now):
            header=rpc.call('eth_getBlockByNumber',['latest',False]);result=k._lp_routing_snapshot(header)
        metadata=result['metadata']
        self.assertEqual(3,metadata['version']);self.assertEqual(1,metadata['execution_price_version'])
        self.assertEqual(3,metadata['execution_price']['source_revision'])
        self.assertFalse(metadata['execution_price']['context_active'])
        self.assertTrue({'oracle','contribution_pricing','lp_balance_math'}<=set(result['runtime_code_hashes']))
        self.assertTrue(_health_profile_valid(cfg))

    def test_source_and_compound_readers_keep_the_full_physical_portfolio(self):
        rpc,cfg,_=self.fixture();k=Keeper(cfg,rpc=rpc)
        with patch('keeper.monitor.time.time',return_value=rpc.now):result=k._compound_policy_status(7)
        self.assertEqual(2,result['portfolio_version']);self.assertEqual(0,result['secondary_id'])
        self.assertTrue(result['in_range'])
        self.assertEqual('waiting_adjustment_threshold',result['status'])

    def test_missing_caps_busy_context_or_wrong_helper_block_new_reads(self):
        for role,signature,value in (('oracle','EXECUTION_PRICE_VERSION()',0),
                ('contribution_pricing','EXECUTION_PRICE_VERSION()',0),('oracle','executionActive()',1),
                ('liquidity','executionStrategy()',1)):
            rpc,cfg,replies=self.fixture();k=Keeper(cfg,rpc=rpc)
            replies[rpc.contracts[role],calldata(signature)]=f'{value:064x}'
            with self.subTest(role=role,signature=signature),patch('keeper.monitor.time.time',return_value=rpc.now),self.assertRaises(RpcError):
                k._lp_routing_snapshot(rpc.call('eth_getBlockByNumber',['latest',False]))

    def test_actual_health_observations_authenticate_normalized_profile_and_context(self):
        for mixed_case in (False,True):
            rpc,cfg,_=self.fixture();cfg=copy.deepcopy(cfg)
            if mixed_case:
                cfg['contracts']={role:value[:2]+value[2:].upper() for role,value in cfg['contracts'].items()}
            k=Keeper(cfg,rpc=rpc);k.canonical_lifecycle=0;k.preparing=False
            with patch('keeper.monitor.time.time',return_value=rpc.now):
                k._observe_execution_health();confirmation=observe_confirmation_health(k)
            data={'health_schema':2,'lp_execution_health':k.lp_execution_health,
                'rebalance_confirmation_health':{'version':3,'check_interval_seconds':240,'policy':confirmation}}
            with self.subTest(mixed_case=mixed_case):
                self.assertEqual([],execution_reasons(data,cfg,now=rpc.now,max_age=1800))
                data['lp_execution_health']['last_confirmed']['metadata']['execution_price']['context_active']=True
                self.assertIn('execution_price_observation_invalid',execution_reasons(data,cfg,now=rpc.now,max_age=1800))

    def test_old_or_misdeclared_profile_never_adopts_lp3_or_a_saved_journal(self):
        rpc,cfg,_=self.fixture()
        for value in (True,False,'1',2,None):
            bad=copy.deepcopy(cfg);bad['execution_price_version']=value
            with self.subTest(value=value),self.assertRaises(ValueError):Keeper(bad,rpc=rpc)
            self.assertFalse(_health_profile_valid(bad))
        bad=copy.deepcopy(cfg);bad.pop('execution_price_version')
        with self.assertRaises(ValueError):Keeper(bad,rpc=rpc)
        k=Keeper(cfg,rpc=rpc);k.save();saved=json.loads(k.path.read_text());saved.pop('execution_price_version')
        k.path.write_text(json.dumps(saved));before=k.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'execution-price profile'):Keeper(cfg,rpc=rpc)
        self.assertEqual(before,k.path.read_bytes())
