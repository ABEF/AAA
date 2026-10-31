"""Fresh scoped policies do not relabel schedules or soften physical guards."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from keeper.monitor import Keeper
from keeper.compound_policy import observe
from keeper.health import observe_confirmation_health,confirmation_reasons
from tests_python.test_keeper_portfolio_policy import PortfolioRPC
from tests_python.test_protocol_policy_v6 import PolicyTranscript
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError

class PolicyRPC(PortfolioRPC):
    def __init__(self,path):
        super().__init__(path)
        self.policy=PolicyTranscript();self.policy.access=self.contracts['access']
        self.contracts['protocol_policy']=self.policy.target
        self.cfg['code_hashes']['protocol_policy']=self.pin
        self.cfg.update(accounting_version=6,protocol_policy_version=1,portfolio_version=2)
        self.minimum_main=7000;self.residual_gap=3
    def read(self,target,signature,*args,count=1):
        if (target,signature) in self.overrides:return super().read(target,signature,*args,count=count)
        if target==self.policy.target or signature=='protocolPolicy()':return self.policy.read(target,signature,*args,count=count)
        if signature=='ACCOUNTING_VERSION()':return [f'{6:064x}']
        if signature=='PORTFOLIO_VERSION()':return [f'{2:064x}']
        if signature=='minimumMainBps(bytes32)':return [f'{self.minimum_main:064x}']
        if signature=='maximumResidualBps(bytes32)':return [f'{10000-self.minimum_main:064x}']
        if signature=='residualGapSpacings(bytes32)':return [f'{self.residual_gap:064x}']
        return super().read(target,signature,*args,count=count)
    def call(self,method,params):
        if method=='eth_call' and 'from' not in params[0]:
            target,data=params[0]['to'],params[0]['data']
            items=[('protocolPolicy()',()),('PORTFOLIO_VERSION()',()),('ACCOUNTING_VERSION()',())]
            items.extend((method,()) for method in ('access()','PROTOCOL_POLICY_VERSION()','maintenancePolicy()','maintenanceFingerprint()') if target==self.policy.target)
            items.extend((method,(self.pool,)) for method in ('minimumMainBps(bytes32)','maximumResidualBps(bytes32)','residualGapSpacings(bytes32)'))
            for signature,args in items:
                if data==calldata(signature,*args):return '0x'+''.join(self.read(target,signature,*args))
        return super().call(method,params)

class KeeperPolicyV6Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.rpc=PolicyRPC(Path(tmp.name)/'isolated.json');self.k=Keeper(self.rpc.cfg,rpc=self.rpc)
    def physical(self,**kwargs):
        return observe(self.rpc.read,self.rpc.code,contracts=self.rpc.contracts,
            code_hashes=self.rpc.cfg['code_hashes'],bucket=7,accounting_version=6,**kwargs)
    def test_explicit_source6_constructor_and_policy_only_health(self):
        self.assertEqual(2,self.k.portfolio_version);self.assertEqual(1,self.k.protocol_policy_version)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            data=observe_confirmation_health(self.k)
        self.assertEqual('observed_this_cycle',data['state'])
        observation=data['last_observed']
        self.assertEqual(2,observation['portfolio_version']);self.assertIsNone(observation['minimum_main_bps'])
        self.assertEqual(1700,observation['maintenance_policy']['maximum_idle_bps'])
        self.assertIn('protocol_policy',observation['runtime_code_hashes'])
    def test_mutable_floor_and_gap_are_current_perpool_values_not_hard_envelope(self):
        result=self.physical(physical_only=True)
        self.assertEqual(7000,result['minimum_main_bps']);self.assertEqual(3000,result['maximum_residual_bps'])
        self.assertEqual(3,result['residual_gap_spacings']);self.assertNotIn('allowed',result)
        self.rpc.minimum_main=8000;self.rpc.residual_gap=4
        result=self.physical(physical_only=True)
        self.assertEqual(8000,result['minimum_main_bps']);self.assertEqual(4,result['residual_gap_spacings'])
    def test_default_keeper_requires_policy_while_raw_physical_claim_read_does_not(self):
        self.rpc.overrides[self.rpc.policy.target,'maintenanceFingerprint()']=[f'{1:064x}']
        self.assertEqual('physical_portfolio_not_maintenance_eligibility',self.physical(physical_only=True)['scope'])
        with self.assertRaises(ValueError):self.physical()
    def test_historical_profile_cannot_adopt_policy_or_portfolio2(self):
        for key,value in (('accounting_version',5),('protocol_policy_version',0),('portfolio_version',1)):
            cfg=copy.deepcopy(self.rpc.cfg);cfg[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
    def test_actual_confirmation_reads_pool_allocation_and_retains_raw_sample_separation(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):result=self.k.rebalance_confirmation.status(7)
        self.assertEqual(7000,result['minimum_main_bps']);self.assertEqual(3000,result['maximum_residual_bps'])
        self.assertTrue(result['raw_eligible_at_snapshot']);self.assertFalse(result['ready_at_snapshot'])
        self.assertFalse(result['continuous_price_proof'])
