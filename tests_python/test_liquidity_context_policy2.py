"""Confirmed outside-only maintenance profile; inert RPC, no signer/network."""
import copy
import unittest

from frontend_api.activation import ActivationTransactions
from frontend_api.service import Projection, ProjectionError, ZERO
from tests_python.test_current_activation_profile import CurrentActivationRPC
from tests_python.test_frontend_api import addr, configuration
from zzz_ops.abi import calldata, keccak256
from zzz_ops.tick_math import sqrt_price_at_tick


def setup_service(*, policy=2, increase=True, new_pool=False):
    rpc = CurrentActivationRPC(increase=increase, new_pool=new_pool)
    config = configuration()
    config.update(accounting_version=4, fee_intake_version=1)
    config['assets'] = [config['assets'][0], dict(address=addr(21),decimals=18,
        symbol='ZZZ',code_hash=rpc.digest(addr(21)))]
    config['contracts']['principal_exit'] = dict(rpc.config['contracts']['migration'])
    module = config['contracts']['principal_exit']['address']
    rpc.put(module,'CUSTODY_VERSION()',values=(3,))
    rpc.put(module,'exitPhase()',values=(0,))
    rpc.put(addr(1),'lpExitStarted()',values=(0,))
    rpc.put(addr(3),'ACCOUNTING_VERSION()',values=(4,))
    rpc.put(addr(7),'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5').hex(),))
    rpc.config['maintenance_policy_version'] = policy
    rpc.config['range_policy_version'] = 1
    rpc.config['range_policies'] = [dict(pool_id=rpc.pool,orientation=1,
        keeper=dict(enabled=False,narrow_trigger_bps=0,widen_trigger_bps=0,
        minimum_interval_seconds=0,configuration_hash='0x'+'0'*64,review_hash='0x'+'0'*64))]
    for getter,values in [('RANGE_POLICY_VERSION()',(1,)),('rangeOrientation(bytes32)',(1,)),
            ('keeperRangePolicy(bytes32)',(0,0,0,0,0,0,0)),('keeperRangeTarget(bytes32)',(0,)),
            ('MAINTENANCE_POLICY_VERSION()',(2,))]:
        rpc.put(rpc.pins['strategy'],getter,() if getter.endswith('()') else (rpc.pool,),values)
    rpc.put(rpc.pins['budget'],'IDLE_COMPOUNDING_VERSION()',values=(3,))
    projection = Projection(config,rpc,clock=lambda:1000)
    return rpc,projection,ActivationTransactions(projection,rpc.config)


def market(rpc,tick=0,*,sqrt_tick=None,cooldown=600,pending=False,eligible=None):
    values=list(rpc.pool_values);values[11]=cooldown
    for getter in ('get(bytes32)','accounting(bytes32)'):
        rpc.put(rpc.pins['pools'],getter,(rpc.pool,),values)
    price=sqrt_price_at_tick(tick if sqrt_tick is None else sqrt_tick)
    rpc.put(rpc.pins['state_view'],'getSlot0(bytes32)',(rpc.pool,),
        (price,tick if tick>=0 else 2**256+tick,0,values[2]))
    rpc.put(rpc.pins['strategy'],'validatePrice(bytes32)',(rpc.pool,),(price,))
    rpc.put(rpc.pins['strategy'],'rangeUpdatePending(uint256)',(rpc.bucket,),(int(pending),))
    if eligible is None:eligible = cooldown<=999 and (tick < -120 or tick >=120 or pending)
    rpc.put(rpc.pins['strategy'],'needsRebalance(uint256)',(rpc.bucket,),(int(eligible),))


class OutsideOnlyContextTests(unittest.TestCase):
    def prepare(self,rpc,service):
        return service.prepare(rpc.request)

    def test_inside_range_ignores_large_reference_displacement(self):
        rpc,_p,service=setup_service();market(rpc)
        rpc.native_put(rpc.pins['oracle'],'referenceX96(address,address)',(ZERO,addr(21)),(2**96*2,))
        result=self.prepare(rpc,service);r=result['liquidity_context']['rebalance']
        self.assertFalse(r['eligible_at_snapshot'])
        self.assertEqual(r['status'],'waiting_for_range_exit')
        self.assertIsNone(r['price_trigger_met']);self.assertIsNone(r['trigger_bps'])
        self.assertFalse(r['outside_range_met'])
        self.assertTrue(result['activation_ready'])

    def test_actual_lower_inclusive_upper_exclusive_boundaries(self):
        for tick,expected in [(-121,True),(-120,False),(0,False),(119,False),(120,True),(121,True)]:
            with self.subTest(tick=tick):
                rpc,_p,service=setup_service();market(rpc,tick)
                result=self.prepare(rpc,service);c=result['liquidity_context'];r=c['rebalance']
                self.assertEqual(not expected,c['in_range'])
                self.assertEqual(expected,r['outside_range_met'])
                self.assertEqual(expected,r['eligible_at_snapshot'])

    def test_downward_boundary_uses_stored_tick_not_sqrt_approximation(self):
        rpc,_p,service=setup_service();market(rpc,-121,sqrt_tick=-120)
        context=self.prepare(rpc,service)['liquidity_context']
        self.assertFalse(context['in_range'])
        self.assertTrue(context['rebalance']['eligible_at_snapshot'])

    def test_twelve_hour_cooldown_is_not_bypassed_by_range_exit(self):
        rpc,_p,service=setup_service();market(rpc,121,cooldown=43200)
        r=self.prepare(rpc,service)['liquidity_context']['rebalance']
        self.assertEqual(r['status'],'cooldown');self.assertEqual(r['earliest_eligible_at'],43201)
        self.assertFalse(r['eligible_at_snapshot']);self.assertTrue(r['outside_range_met'])
        self.assertIn('physical range',r['explanation'])

    def test_explicit_operator_width_change_is_eligible_inside_after_cooldown(self):
        rpc,_p,service=setup_service();market(rpc,0,pending=True)
        r=self.prepare(rpc,service)['liquidity_context']['rebalance']
        self.assertEqual(r['eligibility_reason'],'range_update')
        self.assertTrue(r['eligible_at_snapshot']);self.assertFalse(r['outside_range_met'])

    def test_range_change_still_waits_for_hard_cooldown(self):
        rpc,_p,service=setup_service();market(rpc,0,pending=True,cooldown=43200)
        r=self.prepare(rpc,service)['liquidity_context']['rebalance']
        self.assertEqual(r['status'],'cooldown');self.assertFalse(r['eligible_at_snapshot'])

    def test_both_actual_causes_are_explicit_and_do_not_promise_a_timer(self):
        rpc,_p,service=setup_service();market(rpc,121,pending=True)
        result=self.prepare(rpc,service);r=result['liquidity_context']['rebalance']
        self.assertEqual(r['eligibility_reason'],'out_of_range_and_range_update')
        self.assertIsNone(r['next_keeper_check_at']);self.assertIsNone(r['expected_execution_at'])
        self.assertEqual(r['schedule_source'],'unavailable')
        self.assertEqual(result['provenance']['maintenance_policy_version'],2)

    def test_approval_also_reports_actual_outside_state_without_submitting(self):
        rpc,_p,service=setup_service();market(rpc,121)
        rpc.request['source_asset']=addr(21);rpc.allowance=0
        result=self.prepare(rpc,service)
        self.assertEqual(result['kind'],'approval_required')
        self.assertFalse(result['activation_ready'])
        self.assertTrue(result['liquidity_context']['rebalance']['outside_range_met'])
        self.assertEqual(rpc.trace_count,0)

    def test_contradictory_contract_eligibility_is_rejected_for_all_causes(self):
        for tick,pending,cooldown,eligible in [(0,False,600,True),(121,False,600,False),
                (0,True,600,False),(121,False,43200,True)]:
            with self.subTest(tick=tick,pending=pending,cooldown=cooldown):
                rpc,_p,service=setup_service();market(rpc,tick,pending=pending,cooldown=cooldown,eligible=eligible)
                with self.assertRaisesRegex(ProjectionError,'eligibility disagrees'):self.prepare(rpc,service)

    def test_initial_position_does_not_invent_old_outside_eligibility(self):
        rpc,_p,service=setup_service(increase=False,new_pool=True);market(rpc)
        r=self.prepare(rpc,service)['liquidity_context']['rebalance']
        self.assertEqual(r['status'],'new_position');self.assertIsNone(r['earliest_eligible_at'])
        self.assertFalse(r['eligible_at_snapshot'])

    def test_new_capabilities_are_authenticated_once_at_same_pinned_block(self):
        rpc,_p,service=setup_service();market(rpc)
        self.prepare(rpc,service)
        for role,getter in [('strategy','MAINTENANCE_POLICY_VERSION()'),('budget','IDLE_COMPOUNDING_VERSION()')]:
            calls=[args for method,args in rpc.calls if method=='eth_call' and args[0]['to']==rpc.pins[role]
                and args[0]['data']==calldata(getter)]
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0][1],{'blockHash':rpc.hash,'requireCanonical':True})

    def test_missing_malformed_or_wrong_capabilities_never_fall_back(self):
        for role,getter,values in [('strategy','MAINTENANCE_POLICY_VERSION()',()),
                ('strategy','MAINTENANCE_POLICY_VERSION()',(1,)),('strategy','MAINTENANCE_POLICY_VERSION()',(2,2)),
                ('budget','IDLE_COMPOUNDING_VERSION()',()),('budget','IDLE_COMPOUNDING_VERSION()',(2,))]:
            with self.subTest(role=role,values=values):
                rpc,_p,service=setup_service();market(rpc)
                rpc.put(rpc.pins[role],getter,values=values)
                with self.assertRaises(ProjectionError):self.prepare(rpc,service)
                self.assertEqual(rpc.trace_count,0)

    def test_profile4_policy_must_be_explicit_and_strict(self):
        rpc,p,_service=setup_service()
        for value in [None,True,0,3,'2']:
            config=copy.deepcopy(rpc.config)
            if value is None:config.pop('maintenance_policy_version')
            else:config['maintenance_policy_version']=value
            with self.subTest(value=value),self.assertRaises(ValueError):ActivationTransactions(p,config)

    def test_new_policy_requires_explicit_range_metadata(self):
        rpc,p,_service=setup_service()
        config=copy.deepcopy(rpc.config);config.pop('range_policy_version');config.pop('range_policies')
        with self.assertRaises(ValueError):ActivationTransactions(p,config)

    def test_historical_profile4_policy_retains_movement_semantics_and_no_new_reads(self):
        rpc,_p,service=setup_service(policy=1);market(rpc,121,eligible=False)
        result=self.prepare(rpc,service)
        self.assertFalse(result['liquidity_context']['rebalance']['eligible_at_snapshot'])
        self.assertEqual(result['liquidity_context']['rebalance']['status'],'waiting_for_price_trigger')
        self.assertNotIn('outside_range_met',result['liquidity_context']['rebalance'])
        new={calldata('MAINTENANCE_POLICY_VERSION()'),calldata('IDLE_COMPOUNDING_VERSION()')}
        self.assertFalse(any(method=='eth_call' and args[0]['data'] in new for method,args in rpc.calls))

    def test_new_policy_cannot_be_relabelled_as_earlier_accounting(self):
        rpc,_p,_service=setup_service()
        config=configuration();config.update(accounting_version=3,fee_intake_version=1)
        p=Projection(config,rpc)
        with self.assertRaises(ValueError):ActivationTransactions(p,rpc.config)


if __name__=='__main__':unittest.main()
