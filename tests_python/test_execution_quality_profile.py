"""Explicit fee-adjusted quality observations; inert RPC, no wallet or network."""
import copy
import unittest
from unittest.mock import patch

from frontend_api.activation import ActivationTransactions
from frontend_api.service import ProjectionError
from keeper.monitor import Keeper
from tests_python import test_lp_execution_profile as LP
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


def quality_service(additional=100):
    rpc,projection,_service=LP.routing_service()
    rpc.config['execution_quality_version']=1
    for role in ('liquidity','balancing_router'):
        rpc.put(rpc.pins[role],'EXECUTION_QUALITY_VERSION()',values=(1,))
    rpc.put(rpc.pins['balancing_router'],'MAX_ADDITIONAL_LOSS_BPS()',values=(1000,))
    rpc.put(rpc.pins['balancing_router'],'additionalLossBps()',values=(additional,))
    rpc.put(rpc.pins['access'],'module(bytes32)',('0x'+keccak256(b'ZZZStrategy').hex(),),(rpc.pins['strategy'],))
    for signature,value in (('EXECUTION_QUALITY_VERSION()',1),('MAX_ADDITIONAL_LOSS_BPS()',1000),
            ('additionalLossBps()',additional),('executionQualityRevision()',2)):
        rpc.put(rpc.pins['strategy'],signature,values=(value,))
    return rpc,projection,ActivationTransactions(projection,rpc.config)


class ExecutionQualityAPITests(unittest.TestCase):
    def test_default_and_governed_bounds_are_observed_without_changing_total_loss(self):
        for limit in (0,100,1000):
            with self.subTest(limit=limit):
                rpc,_projection,service=quality_service(limit)
                result=service.prepare(rpc.request)
                self.assertTrue(result['activation_ready'])
                self.assertEqual(1,result['provenance']['execution_quality_version'])
                quality=result['provenance']['lp_execution']['execution_quality']
                self.assertEqual(limit,quality['additional_loss_bps'])
                self.assertEqual(1000,quality['maximum_additional_loss_bps'])
                self.assertEqual(rpc.pins['strategy'],quality['policy_owner'])
                self.assertEqual(2,quality['quality_policy_revision'])
                self.assertTrue(quality['known_pool_fees_excluded_from_additional_limit'])
                self.assertFalse(quality['policy_frozen_by_wallet_review'])
                self.assertEqual(rpc.loss,result['execution_limit_bps'])
                self.assertEqual(str(99*LP.USD),result['contribution']['marginal_deployed_usd_18'])

    def test_all_quality_reads_use_the_same_canonical_snapshot(self):
        rpc,_projection,service=quality_service()
        service.prepare(rpc.request)
        signatures={calldata(s) for s in ('EXECUTION_QUALITY_VERSION()',
            'MAX_ADDITIONAL_LOSS_BPS()','additionalLossBps()','executionQualityRevision()')}
        observations=[params for method,params in rpc.calls if method=='eth_call' and params[0]['data'] in signatures]
        self.assertEqual(8,len(observations))
        self.assertTrue(all(params[1]=={'blockHash':rpc.hash,'requireCanonical':True} for params in observations))

    def test_manager_helper_and_policy_mismatches_fail_closed(self):
        cases=(('liquidity','EXECUTION_QUALITY_VERSION()',0),
            ('balancing_router','EXECUTION_QUALITY_VERSION()',2),
            ('balancing_router','MAX_ADDITIONAL_LOSS_BPS()',999),
            ('balancing_router','MAX_ADDITIONAL_LOSS_BPS()',1001),
            ('balancing_router','additionalLossBps()',1001))
        for role,signature,value in cases:
            with self.subTest(role=role,signature=signature,value=value):
                rpc,_projection,service=quality_service()
                rpc.put(rpc.pins[role],signature,values=(value,))
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_empty_policy_result_does_not_fall_back_to_historical(self):
        rpc,_projection,service=quality_service()
        rpc.responses[rpc.pins['balancing_router'],calldata('additionalLossBps()')]='0x'
        with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_strategy_owner_forwarding_and_revision_must_match(self):
        for signature,value in (('EXECUTION_QUALITY_VERSION()',0),('access()',LP.addr(999)),
                ('MAX_ADDITIONAL_LOSS_BPS()',999),('additionalLossBps()',99),
                ('executionQualityRevision()',1<<64)):
            with self.subTest(signature=signature):
                rpc,_projection,service=quality_service()
                rpc.put(rpc.pins['strategy'],signature,values=(value,))
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)
        rpc,_projection,service=quality_service()
        rpc.put(rpc.pins['access'],'module(bytes32)',('0x'+keccak256(b'ZZZStrategy').hex(),),(LP.addr(999),))
        with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_historical_lp1_never_probes_new_quality_getters(self):
        rpc,_projection,service=LP.routing_service()
        result=service.prepare(rpc.request)
        self.assertEqual(0,result['provenance']['execution_quality_version'])
        self.assertNotIn('execution_quality',result['provenance']['lp_execution'])
        signatures={calldata(s) for s in ('EXECUTION_QUALITY_VERSION()',
            'MAX_ADDITIONAL_LOSS_BPS()','additionalLossBps()')}
        self.assertFalse(any(method=='eth_call' and params[0]['data'] in signatures for method,params in rpc.calls))

    def test_invalid_or_incompatible_explicit_profiles_are_rejected(self):
        for value in (True,2,'1'):
            with self.subTest(value=value):
                rpc,projection,_service=LP.routing_service()
                rpc.config['execution_quality_version']=value
                with self.assertRaises(ValueError):ActivationTransactions(projection,rpc.config)
        rpc,projection,_service=LP.routing_service()
        rpc.config.update(execution_quality_version=1,lp_routing_version=0)
        with self.assertRaisesRegex(ValueError,'requires explicit LP-routing'):ActivationTransactions(projection,rpc.config)


class ExecutionQualityKeeperTests(unittest.TestCase):
    def setUp(self):
        self.fixture=LP.KeeperLPExecutionProfileTests('runTest')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.cfg,self.rpc=self.fixture.cfg,self.fixture.rpc
        self.cfg['execution_quality_version']=1
        c=self.cfg['contracts']
        for role in ('liquidity','balancing_router'):
            self.fixture.values[c[role],calldata('EXECUTION_QUALITY_VERSION()')]=LP.words(1)
        self.fixture.values[c['balancing_router'],calldata('MAX_ADDITIONAL_LOSS_BPS()')]=LP.words(1000)
        self.fixture.values[c['balancing_router'],calldata('additionalLossBps()')]=LP.words(100)
        self.fixture.values[c['access'],calldata('module(bytes32)','0x'+keccak256(b'ZZZStrategy').hex())]=LP.words(c['strategy'])
        for signature,value in (('access()',c['access']),('EXECUTION_QUALITY_VERSION()',1),
                ('MAX_ADDITIONAL_LOSS_BPS()',1000),('additionalLossBps()',100),('executionQualityRevision()',2)):
            self.fixture.values[c['strategy'],calldata(signature)]=LP.words(value)
        self.k=Keeper(self.cfg,rpc=self.rpc)

    def test_quality_is_pinned_to_one_block_without_signing(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('keeper.monitor.subprocess.run') as signer:
            self.k._validate_lp_routing();signer.assert_not_called()
        self.assertEqual(100,self.k.lp_execution_observation['execution_quality']['additional_loss_bps'])
        self.assertEqual(self.cfg['contracts']['strategy'],self.k.lp_execution_observation['execution_quality']['policy_owner'])
        self.assertEqual(2,self.k.lp_execution_observation['execution_quality']['quality_policy_revision'])
        methods={calldata(s) for s in ('EXECUTION_QUALITY_VERSION()',
            'MAX_ADDITIONAL_LOSS_BPS()','additionalLossBps()','executionQualityRevision()')}
        calls=[params for method,params in self.rpc.calls if method=='eth_call' and params[0]['data'] in methods]
        self.assertEqual(8,len(calls))
        self.assertTrue(all(params[1]==self.fixture.block for params in calls))

    def test_bad_policy_or_capability_blocks_balancing_without_signing(self):
        for role,signature,value in (('liquidity','EXECUTION_QUALITY_VERSION()',0),
                ('balancing_router','EXECUTION_QUALITY_VERSION()',2),
                ('balancing_router','MAX_ADDITIONAL_LOSS_BPS()',1001),
                ('balancing_router','additionalLossBps()',1001)):
            key=self.cfg['contracts'][role],calldata(signature);old=self.fixture.values[key]
            self.fixture.values[key]=LP.words(value)
            try:
                with self.subTest(role=role,signature=signature),patch('keeper.monitor.time.time',return_value=self.rpc.now), \
                        patch('keeper.monitor.subprocess.run') as signer,self.assertRaises(RpcError):
                    self.k.submit('compounder','compound(uint256,uint128,uint256)',(7,1,self.rpc.now+180),'compound:7')
                signer.assert_not_called();self.assertIsNone(self.k.state['pending'])
            finally:self.fixture.values[key]=old

    def test_strategy_binding_forwarding_revision_and_runtime_are_checked(self):
        for role,signature,args,value in (
                ('strategy','access()',(),LP.addr(999)),
                ('strategy','EXECUTION_QUALITY_VERSION()',(),0),
                ('strategy','MAX_ADDITIONAL_LOSS_BPS()',(),999),
                ('strategy','additionalLossBps()',(),99),
                ('strategy','executionQualityRevision()',(),1<<64),
                ('access','module(bytes32)',('0x'+keccak256(b'ZZZStrategy').hex(),),LP.addr(999))):
            key=self.cfg['contracts'][role],calldata(signature,*args);old=self.fixture.values[key]
            self.fixture.values[key]=LP.words(value)
            try:
                with self.subTest(role=role,signature=signature),patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):
                    self.k._validate_lp_routing()
            finally:self.fixture.values[key]=old
        self.k.config['code_hashes']['strategy']='0x'+'ab'*32
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaises(RpcError):self.k._validate_lp_routing()

    def test_unknown_config_versions_require_explicit_lp1(self):
        for version in (True,2,'1'):
            with self.subTest(version=version):
                cfg=copy.deepcopy(self.cfg);cfg['execution_quality_version']=version
                with self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
        cfg=copy.deepcopy(self.cfg);cfg['lp_routing_version']=0
        with self.assertRaisesRegex(ValueError,'requires explicit LP-routing'):Keeper(cfg,rpc=self.rpc)

    def test_historical_lp1_preserves_no_quality_probe(self):
        cfg=copy.deepcopy(self.cfg);cfg.pop('execution_quality_version')
        keeper=Keeper(cfg,rpc=self.rpc)
        self.fixture.values.pop((cfg['contracts']['balancing_router'],calldata('additionalLossBps()')))
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):keeper._validate_lp_routing()
        self.assertNotIn('execution_quality',keeper.lp_execution_observation)

    def test_helper_outage_preserves_independent_due_harvest(self):
        self.fixture.values[self.cfg['contracts']['balancing_router'],calldata('additionalLossBps()')]='0x'
        self.k.maintenance=self.cfg['maintenance']={'compound':False,'harvest':True,'harvest_interval_seconds':3600}
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch.object(self.k,'submit',return_value=True) as submitted:
            self.k.cycle()
        submitted.assert_called_once_with('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7')

    def test_existing_pending_recovery_skips_unavailable_new_quality_metadata(self):
        self.k.state['next_nonce']=7
        self.k.state['pending']=dict(key='harvest:7',nonce=7,to=self.cfg['contracts']['vault'],
            data=calldata('collectFees(uint256,uint256)',7,self.rpc.now+180),value=0,
            day='2026-10-28',hash=LP.scheduling.K.H)
        self.k.save();before=self.k.path.read_bytes()
        loaded=Keeper(self.cfg,rpc=self.rpc)
        with patch.object(loaded,'poll_pending',return_value=True), \
                patch.object(loaded,'_validate_lp_routing',side_effect=AssertionError('New policy must not block saved hash')) as quality:
            loaded.cycle();quality.assert_not_called()
        self.assertEqual(before,loaded.path.read_bytes())


if __name__=='__main__':unittest.main()
