"""Synthetic pinned reader evidence; not market/feed or operating qualification."""
import unittest
from unittest.mock import patch
from frontend_api.activation import ActivationTransactions
from frontend_api.service import ProjectionError
from tests_python.test_rebalance_confirmation_api import setup_confirmation, IDENTITY, ZERO_HASH
from zzz_ops.abi import calldata


def setup_market(*, reference=2, required=True, review=ZERO_HASH):
    rpc,p,_=setup_confirmation()
    rpc.config['rebalance_confirmation_version']=2
    for role in ('strategy','budget','rebalance_confirmation'):
        rpc.put(rpc.pins[role],'REBALANCE_CONFIRMATION_VERSION()',values=(2,))
    helper=rpc.pins['rebalance_confirmation']
    rpc.put(helper,'requireReferenceExit()',values=(int(required),))
    rpc.put(helper,'referenceReviewHash()',values=(review,))
    rpc.put(helper,'marketSides(uint256)',(rpc.bucket,),(2,reference))
    if required and reference!=2:
        rpc.put(helper,'condition(uint256)',(rpc.bucket,),(0,ZERO_HASH,0))
        for role,method in (('strategy','rebalanceReady(uint256)'),('rebalance_confirmation','ready(uint256)')):
            rpc.put(rpc.pins[role],method,(rpc.bucket,),(0,))
    return rpc,p,ActivationTransactions(p,rpc.config)


class ReferenceConfirmationV2Tests(unittest.TestCase):
    def test_same_side_confirmation_is_reported_with_explicit_version(self):
        rpc,_,service=setup_market();r=service.prepare(rpc.request)
        proof=r['liquidity_context']['rebalance_confirmation']
        self.assertEqual(2,proof['version']);self.assertTrue(proof['reference_exit_required'])
        self.assertEqual(2,proof['physical_exit_side']);self.assertEqual(2,proof['reference_exit_side'])
        self.assertTrue(proof['ready_at_snapshot']);self.assertEqual(2,r['provenance']['rebalance_confirmation_version'])

    def test_target_only_and_opposite_side_are_blocked_not_unavailable(self):
        for reference in (0,1):
            with self.subTest(reference=reference):
                rpc,_,service=setup_market(reference=reference);c=service.prepare(rpc.request)['liquidity_context']
                self.assertEqual('reference_disagreement',c['rebalance']['status'])
                self.assertTrue(c['rebalance']['raw_eligible_at_snapshot'])
                self.assertFalse(c['rebalance']['eligible_at_snapshot'])
                self.assertIsNone(c['rebalance']['expected_execution_at'])

    def test_reviewed_relaxation_is_visible_and_cannot_be_guessed(self):
        rpc,_,service=setup_market(reference=0,required=False,review=IDENTITY)
        proof=service.prepare(rpc.request)['liquidity_context']['rebalance_confirmation']
        self.assertFalse(proof['reference_exit_required']);self.assertTrue(proof['ready_at_snapshot'])
        rpc,_,service=setup_market(reference=0,required=False)
        with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_contradictory_helper_market_condition_rejects(self):
        rpc,_,service=setup_market(reference=0)
        rpc.put(rpc.pins['rebalance_confirmation'],'condition(uint256)',(rpc.bucket,),(2,IDENTITY,0))
        with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_noncanonical_policy_boolean_rejects(self):
        rpc,_,service=setup_market()
        rpc.put(rpc.pins['rebalance_confirmation'],'requireReferenceExit()',values=(2,))
        with self.assertRaises(ProjectionError):service.prepare(rpc.request)


class KeeperReferenceConfirmationV2Tests(unittest.TestCase):
    def setUp(self):
        from tests_python.test_keeper_rebalance_confirmation import KeeperConfirmationTests, words
        from keeper.monitor import Keeper
        f=self.f=KeeperConfirmationTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        f.cfg['rebalance_confirmation_version']=2
        for target in (f.cfg['contracts']['strategy'],f.helper,f.budget):
            f.bad[target,calldata('REBALANCE_CONFIRMATION_VERSION()')]=words(2)
        original=f.rpc.call
        self.required=True;self.reference=1;self.review=0
        def call(method,params):
            if method=='eth_call':
                target,data=params[0]['to'],params[0]['data']
                if target==f.helper:
                    values={calldata('requireReferenceExit()'):(int(self.required),),
                        calldata('referenceReviewHash()'):(self.review,),
                        calldata('marketSides(uint256)',7):(1,self.reference)}
                    if data in values:return words(*values[data])
                if target==f.cfg['contracts']['strategy'] and data==calldata('needsRebalance(uint256)',7):return words(1)
            return original(method,params)
        f.rpc.call=call;self.k=Keeper(f.cfg,rpc=f.rpc)

    def status(self):
        with patch('keeper.monitor.time.time',return_value=self.f.rpc.now):return self.k.rebalance_confirmation.status(7)

    def test_policy2_market_disagreement_needs_no_observation_when_already_empty(self):
        self.reference=0;self.f.side=0
        status=self.status()
        self.assertEqual(2,status['version']);self.assertEqual(0,status['side'])
        self.assertFalse(status['ready']);self.assertTrue(status['reference_exit_required'])
        self.assertFalse(self.k.rebalance_confirmation.observation_due(status,self.f.rpc.now))

    def test_market_disagreement_clears_existing_window_instead_of_extending_it(self):
        self.reference=0;self.f.side=0
        self.f.record=[self.f.identity,self.f.rpc.now-300,self.f.rpc.now-1,1]
        self.assertTrue(self.k.rebalance_confirmation.observation_due(self.status(),self.f.rpc.now))

    def test_observed_disagreement_requires_durable_clear_even_if_market_recovers_before_inclusion(self):
        from keeper.monitor import CONFIRMATION_RESETS
        self.reference=0;self.f.side=0
        self.f.record=[self.f.identity,self.f.rpc.now-300,self.f.rpc.now-1,1]
        self.k._confirmation_seen_buckets.add(7) # Exercise incident handling, not the separate startup reset.
        with patch('keeper.monitor.time.time',return_value=self.f.rpc.now):
            self.assertFalse(self.k._confirmed_rebalance_due(7,IDENTITY,self.f.rpc.now,force=True))
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertEqual(7,self.k._rebalance_reset_due)
        self.assertIsNone(self.k._rebalance_observation_due)
        self.reference=1;self.f.side=1 # Recovery cannot erase the saved reset obligation.
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])

    def test_keeper_rejects_wrong_helper_condition_for_market_sides(self):
        from zzz_ops.rpc import RpcError
        self.reference=0 # Original fixture still claims physical side1 is eligible.
        with self.assertRaises(RpcError):self.status()

    def test_relaxed_policy_requires_nonzero_review_and_remains_explicit(self):
        from zzz_ops.rpc import RpcError
        self.required=False
        with self.assertRaises(RpcError):self.status()
        self.review=1;status=self.status()
        self.assertFalse(status['reference_exit_required'])

    def test_matching_policy2_health_has_explicit_capabilities_and_reference_policy(self):
        from keeper.health import observe_confirmation_health,confirmation_reasons,HEALTH_SCHEMA
        with patch('keeper.monitor.time.time',return_value=self.f.rpc.now):
            report=observe_confirmation_health(self.k,{})
        self.assertEqual('observed_this_cycle',report['state'])
        data={'health_schema':HEALTH_SCHEMA,'rebalance_confirmation_health':{
            'version':2,'check_interval_seconds':240,'policy':report}}
        self.assertEqual([],confirmation_reasons(data,self.f.cfg,now=self.f.rpc.now,max_age=1800))
