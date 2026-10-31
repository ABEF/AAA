"""Fresh unsigned-review verifier executes real pinned RPC helper checks.

Synthetic RPC only; no signer, network, transaction, service or state writes.
"""
import copy
import unittest

from frontend_api.activation_config import ActivationConfig
from frontend_api.portfolio_v5 import ROLES
from frontend_api.service import Projection,ProjectionError,ZERO
from tests_python.test_frontend_api import addr,configuration
from tests_python.test_frontend_portfolio_v5 import ProfileTranscript
from tests_python.test_lp_execution_profile import routing_service
from zzz_ops.abi import keccak256


def fresh_verifier():
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
        target=rpc.pins[role];read['contracts'][role]=dict(address=target,code_hash=rpc.digest(target))
    c={**rpc.pins,'principal_exit':rpc.pins['migration']}
    graph=ProfileTranscript()
    for role,method,target in graph.bindings:rpc.put(c[role],method,values=(c[target],))
    for (role,method,args),value in graph.values.items():
        if method.endswith('VERSION()') or method in ('minimumMainBps()','maximumResidualBps()'):
            rpc.put(c[role],method,args,(value,))
    for role in ('portfolio_policy','rebalance_confirmation','lp_position_executor'):
        rpc.put(c[role],'access()',values=(c['access'],))
    for role,label in (('vault','ZZZVault'),('strategy','ZZZStrategy')):
        rpc.put(c['access'],'module(bytes32)',('0x'+keccak256(label.encode()).hex(),),(c[role],))
    for role in ('liquidity','balancing_router','strategy'):
        rpc.put(c[role],'EXECUTION_QUALITY_VERSION()',values=(1,))
    for role in ('balancing_router','strategy'):
        rpc.put(c[role],'MAX_ADDITIONAL_LOSS_BPS()',values=(1000,))
        rpc.put(c[role],'additionalLossBps()',values=(100,))
    rpc.put(c['strategy'],'executionQualityRevision()',values=(1,))
    for method,value in (('duration()',600),('MAX_DURATION()',604800),('maxObservationGap()',300),
            ('policyRevision()',1),('reviewHash()',1),('requireReferenceExit()',1),('referenceReviewHash()',0)):
        rpc.put(c['rebalance_confirmation'],method,values=(value,))
    for method,value in (('thresholdBps()',8500),('revision()',1)):
        rpc.put(c['portfolio_policy'],method,values=(value,))
    p=Projection(read,rpc,clock=lambda:1000)
    return rpc,p,ActivationConfig(cfg,p)


class PortfolioActivationBindingTests(unittest.TestCase):
    def verify(self,rpc,p,config):
        observation={}
        pins,prices=config.verify(p,{'blockHash':rpc.hash,'requireCanonical':True},
            [ZERO,addr(21)],timestamp=990,execution_observation=observation)
        return pins,prices,observation

    def test_complete_fresh_verifier_checks_typed_executor_and_prices(self):
        rpc,p,config=fresh_verifier();pins,prices,observation=self.verify(rpc,p,config)
        self.assertEqual(pins['lp_position_executor'],observation['position_executor'])
        self.assertEqual(pins['lp_balance_math'],observation['math_helper'])
        self.assertEqual(2,observation['version'])
        self.assertEqual(3,observation['rebalance_confirmation_policy']['version'])
        self.assertEqual({ZERO,addr(21)},set(prices))
        self.assertTrue(all(value>0 for value in prices.values()))

    def test_typed_executor_parent_and_runtime_changes_fail_closed(self):
        for method in ('liquidityManager()','access()','poolManager()','stateView()',
                'balancingRouter()','positionManager()','permit2()'):
            with self.subTest(method=method):
                rpc,p,config=fresh_verifier()
                rpc.put(rpc.pins['lp_position_executor'],method,values=(addr(999),))
                with self.assertRaises(ProjectionError):self.verify(rpc,p,config)
        rpc,p,config=fresh_verifier();rpc.codes[rpc.pins['lp_position_executor']]='0x6000'
        with self.assertRaises(ProjectionError):self.verify(rpc,p,config)

    def test_math_and_executor_cannot_be_interchanged_or_legacy(self):
        for role,method,value in (('liquidity','positionOperator()',addr(152)),
                ('balancing_router','balanceMath()',addr(153)),
                ('lp_position_executor','LP_POSITION_EXECUTOR_VERSION()',0)):
            with self.subTest(role=role,method=method):
                rpc,p,config=fresh_verifier();rpc.put(rpc.pins[role],method,values=(value,))
                with self.assertRaises(ProjectionError):self.verify(rpc,p,config)
