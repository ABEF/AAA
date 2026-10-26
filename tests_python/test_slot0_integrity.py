"""Contradictory v4 state must not become a quote or release observation.

All RPC responses are offline fixtures. These checks do not qualify a provider.
"""
import unittest

from frontend_api.service import ProjectionError
from tests_python import test_current_activation_profile as current
from tests_python import test_production_observer as observer
from tests_python import test_production_v2 as inventory
from tests_python import test_typed_v4_activation as typed
from zzz_ops.abi import keccak256
from zzz_ops.tick_math import (MAX_SQRT, MAX_TICK, MIN_SQRT, MIN_TICK,
                              decode_slot0, sqrt_price_at_tick, validate_slot0)


def slot_words(price, tick, protocol=0, fee=0):
    return [f'{value % (1 << 256):064x}' for value in (price, tick, protocol, fee)]


class TickMathStateTests(unittest.TestCase):
    def test_exact_known_endpoints_and_rounding(self):
        for tick, price in ((MIN_TICK, MIN_SQRT), (-1, 79224201403219477170569942574),
                            (0, 2**96), (1, 79232123823359799118286999568),
                            (MAX_TICK, MAX_SQRT)):
            with self.subTest(tick=tick):
                self.assertEqual(sqrt_price_at_tick(tick), price)
        for tick in (True, 0.0, '0', MIN_TICK-1, MAX_TICK+1):
            with self.subTest(tick=tick), self.assertRaises(ValueError):
                sqrt_price_at_tick(tick)

    def test_integer_interval_edges_and_only_exact_downward_boundary(self):
        ticks = (MIN_TICK, MIN_TICK+1, -500000, -120, -1, 0, 1, 120, 500000, MAX_TICK-1)
        for tick in ticks:
            low, high = sqrt_price_at_tick(tick), sqrt_price_at_tick(tick+1)
            for price in (low, (low+high)//2, high-1):
                with self.subTest(tick=tick, price=price):
                    self.assertEqual(decode_slot0(slot_words(price,tick))[:2], (price,tick))
            if high < MAX_SQRT:
                # A downward crossing stores tickNext-1, not a reconstructed floor.
                self.assertEqual(decode_slot0(slot_words(high,tick))[:2], (high,tick))
                self.assertEqual(decode_slot0(slot_words(high,tick+1))[:2], (high,tick+1))
            for price in (low-1, high+1):
                with self.subTest(tick=tick, price=price), self.assertRaises(ValueError):
                    decode_slot0(slot_words(price,tick))

    def test_abi_domain_and_directional_fees_fail_closed(self):
        maximum_protocol = 1000 + (1000 << 12)
        self.assertEqual(decode_slot0(slot_words(2**96,-1,maximum_protocol,1_000_000)),
                         (2**96,-1,maximum_protocol,1_000_000))
        for values in ((0,0,0,0), (MIN_SQRT-1,MIN_TICK,0,0), (MAX_SQRT,MAX_TICK,0,0),
                       (2**160,0,0,0), (2**96,MAX_TICK,0,0), (2**96,(1<<24)-1,0,0),
                       (2**96,0,1001,0), (2**96,0,1001<<12,0), (2**96,0,1<<24,0),
                       (2**96,0,0,1_000_001), (2**96,0,0,0x800000), (2**96,0,0,1<<24)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                decode_slot0(slot_words(*values))
        for malformed in (None, [], ['0'*64]*3, ['0'*65]*4,
                          ['0x'+'0'*64]*4, ['g'*64]*4, [0]*4):
            with self.subTest(words=malformed), self.assertRaises(ValueError):
                decode_slot0(malformed)
        for value in (True, '0', 0.0, None):
            with self.subTest(protocol=value), self.assertRaises(ValueError):
                validate_slot0(2**96,0,value,0)
        with self.assertRaises(ValueError):
            decode_slot0(slot_words(2**96,0,0,500), expected_fee=501)
        with self.assertRaises(ValueError):
            decode_slot0(slot_words(2**96,0,0,0), expected_fee=False)


class Slot0IntegrationTests(unittest.TestCase):
    def test_current_activation_rejects_contradictory_tick_before_simulation(self):
        for approval in (False, True):
            rpc, _projection, service = current.CurrentActivationProfileTests().service()
            if approval:
                rpc.request['source_asset'] = current.addr(21)
                rpc.allowance = 0
            rpc.put(rpc.pins['state_view'], 'getSlot0(bytes32)', (rpc.pool,),
                    (2**96, 500000, 0, 0))
            with self.subTest(approval=approval), self.assertRaisesRegex(ProjectionError, 'slot0'):
                service.prepare(rpc.request)
            self.assertEqual(rpc.trace_count, 0)

    def test_exact_downward_boundary_keeps_actual_tick_for_range_membership(self):
        for boundary, tick, inside in ((-120,-121,False), (-120,-120,True),
                                        (120,119,True), (120,120,False)):
            rpc, _projection, service = current.CurrentActivationProfileTests().service()
            price = sqrt_price_at_tick(boundary)
            rpc.put(rpc.pins['state_view'], 'getSlot0(bytes32)', (rpc.pool,),
                    (price, tick % (1<<256), 0, 0))
            rpc.put(rpc.pins['strategy'], 'validatePrice(bytes32)', (rpc.pool,), (price,))
            with self.subTest(boundary=boundary,tick=tick):
                context = service.prepare(rpc.request)['liquidity_context']
                self.assertEqual(context['current_tick'], tick)
                self.assertEqual(context['sqrt_price_x96'], str(price))
                self.assertEqual(context['in_range'], inside)

    def test_static_fee_or_directional_protocol_corruption_prevents_approval(self):
        for protocol, fee in ((1001,0),(1001<<12,0),(1<<24,0),(0,500)):
            rpc, _projection, service = current.CurrentActivationProfileTests().service()
            rpc.request['source_asset'] = current.addr(21); rpc.allowance = 0
            rpc.put(rpc.pins['state_view'], 'getSlot0(bytes32)', (rpc.pool,),
                    (2**96, 0, protocol, fee))
            with self.subTest(protocol=protocol,fee=fee), self.assertRaisesRegex(ProjectionError, 'slot0'):
                service.prepare(rpc.request)
            self.assertEqual(rpc.trace_count, 0)

    def test_typed_conversion_route_rejects_contradictory_tick(self):
        rpc, _projection, service = typed.TypedV4ActivationTests().service()
        pool = '0x' + keccak256(bytes.fromhex(typed.words(*rpc.v4_values[2:7])[2:])).hex()
        rpc.put(rpc.pins['state_view'], 'getSlot0(bytes32)', (pool,),
                (2**96, 500000, 0, 500))
        with self.assertRaisesRegex(ProjectionError, 'slot0'):
            service.prepare(rpc.request)
        self.assertEqual(rpc.trace_count, 0)

    def test_observer_does_not_publish_contradictory_slot_as_confirmed(self):
        config, expected = observer.fixture()
        rpc = observer.FakeRPC(config, expected)
        target = observer.addr(21)
        data = observer.selector('getSlot0(bytes32)') + observer.HASH[2:]
        rpc.overrides[target, data] = observer.encoded(2**96, 500000, 0, 10020)
        result, _rpc = observer.ProductionObserverTests().run_observer(config, expected, rpc)
        chain = result['chains'][0]
        self.assertIsNone(chain['pools'][0]['slot0'])
        self.assertFalse(chain['observation']['complete'])
        self.assertTrue(any(issue['code'] == 'slot0.unavailable'
                            for issue in chain['observation']['errors']))

    def test_observer_preserves_valid_downward_boundary(self):
        config, expected = observer.fixture()
        rpc = observer.FakeRPC(config, expected)
        data = observer.selector('getSlot0(bytes32)') + observer.HASH[2:]
        rpc.overrides[observer.addr(21), data] = observer.encoded(2**96, (1<<256)-1, 0, 10020)
        result, _rpc = observer.ProductionObserverTests().run_observer(config, expected, rpc)
        chain = result['chains'][0]
        self.assertTrue(chain['observation']['complete'], chain['observation']['errors'])
        self.assertEqual(chain['pools'][0]['slot0']['tick'], -1)

    def test_direct_inventory_cannot_bypass_observer_validation(self):
        for route in (False, True):
            config = inventory.fixture()
            chain = config['chains'][0]
            record = (chain['conversion_routes'][0]['venue_observation']
                      if route else chain['pools'][0])
            record['slot0']['tick'] = 500000
            result = inventory.P.validate(config, expected_commit=inventory.COMMIT,
                                          now=inventory.NOW)
            with self.subTest(route=route):
                self.assertFalse(result['ready'])
                self.assertTrue(any(issue['code'] == ('route.pool_state' if route else 'pool.state')
                                    for issue in result['issues']))

    def test_direct_inventory_handles_bad_types_prices_and_fees_without_crashing(self):
        for field, value in (('tick',True),('tick',2**24-1),('tick','0'),
                             ('sqrt_price_x96',MIN_SQRT-1),('sqrt_price_x96',MAX_SQRT),
                             ('protocol_fee',1001<<12),('lp_fee',1_000_001)):
            config = inventory.fixture()
            config['chains'][0]['pools'][0]['slot0'][field] = value
            result = inventory.P.validate(config, expected_commit=inventory.COMMIT, now=inventory.NOW)
            with self.subTest(field=field,value=value):
                self.assertFalse(result['ready'])
                self.assertTrue(any(issue['code'] == 'pool.state' for issue in result['issues']))
        config = inventory.fixture()
        config['chains'][0]['pools'][0]['slot0']['tick'] = -1
        result = inventory.P.validate(config, expected_commit=inventory.COMMIT, now=inventory.NOW)
        self.assertTrue(result['ready'],result['issues'])


if __name__ == '__main__':
    unittest.main()
