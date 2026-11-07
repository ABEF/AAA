"""Operator-only reviewed gas flexibility; no wallet/signing or RPC network."""
import copy
import unittest

from frontend_api.service import Projection, ProjectionError
from frontend_api.transactions import Transactions, TransactionConfig, TransactionInputError, GasHeadroomError
from tests_python.test_frontend_api import configuration, addr
from tests_python.test_frontend_transactions import transaction_config
from tests_python import test_claim_planner as planner_fixtures
from zzz_ops.errors import RemoteRPCError


class GasRPC(planner_fixtures.PlannerRPC):
    def __init__(self):
        super().__init__()
        self.block_limit = 40_000_000
        self.gas_header = None
        self.block_error = None
        self.block_reads = 0
        self.change_limit_at = None

    def call(self, method, params):
        if method == 'eth_getBlockByHash':
            self.calls.append((method, copy.deepcopy(params))); self.block_reads += 1
            if self.block_error:
                raise self.block_error
            if self.change_limit_at == self.block_reads:
                self.block_limit -= 1
            if self.gas_header is not None:
                return copy.deepcopy(self.gas_header)
            return dict(number=hex(self.head-11), hash=self.hash,
                        timestamp=hex(self.header_timestamp), gasLimit=hex(self.block_limit))
        return super().call(method, params)


class TransactionGasPolicyTests(unittest.TestCase):
    def setUp(self):
        self.rpc = GasRPC(); self.now = 1000
        self.p = Projection(configuration(), self.rpc, clock=lambda: self.now)
        self.config = transaction_config(self.p)
        self.config['schema'] = 2
        self.config['fee_policy']['max_gas_limit'] = '40000000'
        self.config['fee_policy']['max_network_fee_wei'] = '1000000000000000000'
        self.service = Transactions(self.p, self.config)

    def mint(self, **overrides):
        return self.service.prepare(dict(action='mint', wallet=addr(30), **overrides))

    def many(self, count):
        # Reuse the older fixture's input construction, not its test methods.
        helper = planner_fixtures.ClaimPlannerTests(); helper.rpc = self.rpc
        return helper.many(count)

    def plan(self, count):
        return self.service.plan_claims(dict(action='claim', wallet=addr(30), claims=self.many(count)))

    def test_opt_in_large_cap_is_same_for_simulation_estimate_and_review(self):
        self.rpc.estimate = 31_085_813
        result = self.mint()
        self.assertEqual(result['schema'], 2)
        self.assertEqual(result['simulation']['gas_cap'], '40000000')
        self.assertEqual(result['network_gas']['suggested_limit'], '37302976')
        self.assertEqual(result['network_gas']['confirmed_block_gas_limit'], '40000000')
        self.assertTrue(result['network_gas']['full_twenty_percent_headroom'])
        self.assertEqual(self.rpc.simulations[0][0]['gas'], hex(40_000_000))
        self.assertNotIn('gas', result['transaction']); self.assertNotIn('nonce', result['transaction'])
        self.assertTrue(all(name not in ('eth_sendTransaction', 'eth_sendRawTransaction') for name, _ in self.rpc.calls))

    def test_schema1_is_byte_shape_compatible_and_keeps_12m_without_extra_header_read(self):
        legacy = Transactions(self.p, transaction_config(self.p))
        self.rpc.block_error = RemoteRPCError('eth_getBlockByHash', -32603)
        result = legacy.prepare(dict(action='mint', wallet=addr(30)))
        self.assertEqual(result['schema'], 1); self.assertEqual(result['simulation']['gas_cap'], '12000000')
        self.assertNotIn('policy_schema', result['network_gas']); self.assertEqual(self.rpc.block_reads, 0)

    def test_block_limit_clamps_policy_without_relaxing_margin(self):
        self.rpc.block_limit = 10_000_000; self.rpc.estimate = 8_000_000
        result = self.mint()
        self.assertEqual(result['simulation']['gas_cap'], '10000000')
        self.assertEqual(result['network_gas']['configured_gas_limit'], '40000000')
        self.assertEqual(result['network_gas']['suggested_limit'], '9600000')

    def test_policy2_requires_full_headroom_instead_of_silently_truncating_it(self):
        self.rpc.block_limit = 12_000_000; self.rpc.estimate = 11_000_000
        with self.assertRaises(GasHeadroomError): self.mint()

    def test_operator_cap_is_bounded_strict_canonical_decimal_not_request_input(self):
        for bad in (None, True, False, 40_000_000, 4e7, '', '0', '20999', '64000001',
                    '040000000', '-1', '1e7', '0x100000', '40000000\n', '9'*1000):
            with self.subTest(value=repr(bad)[:30]):
                cfg = copy.deepcopy(self.config); cfg['fee_policy']['max_gas_limit'] = bad
                with self.assertRaises(ValueError): Transactions(self.p, cfg)
        with self.assertRaises(TransactionInputError): self.mint(max_gas_limit='64000000')

    def test_maximum_and_minimum_engineering_values_are_explicit_and_identity_bound(self):
        identities = []
        for limit in ('21000', '64000000'):
            cfg = copy.deepcopy(self.config); cfg['fee_policy']['max_gas_limit'] = limit
            parsed = TransactionConfig(cfg, self.p); self.assertEqual(parsed.max_gas_limit, int(limit))
            identities.append(parsed.identity)
        self.assertNotEqual(*identities)

    def test_missing_extra_or_schema1_gas_fields_rejected_before_rpc(self):
        for kind in ('missing', 'extra', 'legacy'):
            cfg = copy.deepcopy(self.config)
            if kind == 'missing': del cfg['fee_policy']['max_gas_limit']
            if kind == 'extra': cfg['fee_policy']['unreviewed_override'] = 1
            if kind == 'legacy': cfg['schema'] = 1
            with self.subTest(kind=kind), self.assertRaises(ValueError): Transactions(self.p, cfg)
        self.assertEqual(self.rpc.calls, [])

    def test_header_identity_and_gas_fail_closed_without_zero_or_number_fallback(self):
        good = dict(number=hex(self.rpc.head-11), hash=self.rpc.hash,
                    timestamp=hex(self.rpc.header_timestamp), gasLimit=hex(40_000_000))
        for key, bad in [('hash', '0x'+'c'*64), ('number', '0x1'), ('timestamp', '0x1'),
                         ('gasLimit', None), ('gasLimit', True), ('gasLimit', '0x1'),
                         ('gasLimit', hex(1 << 64))]:
            self.rpc.gas_header = {**good, key: bad}
            with self.subTest(key=key, value=bad), self.assertRaises(ProjectionError): self.mint()
        self.assertEqual(self.rpc.simulations, [])

    def test_header_transport_error_does_not_fall_back_to_configured_or_legacy_cap(self):
        self.rpc.block_error = RemoteRPCError('eth_getBlockByHash', -32005, 'rate_limited')
        with self.assertRaises(RemoteRPCError): self.mint()
        self.assertEqual(self.rpc.simulations, [])

    def test_fee_and_wallet_balance_bounds_still_apply_to_larger_reviews(self):
        self.rpc.estimate = 20_000_000
        cfg = copy.deepcopy(self.config); cfg['fee_policy']['max_network_fee_wei'] = '1000000000'
        with self.assertRaises(ProjectionError): Transactions(self.p, cfg).prepare(dict(action='mint', wallet=addr(30)))
        self.rpc.native_balance = 1
        with self.assertRaises(TransactionInputError): self.mint()

    def test_planner_smaller_prefix_has_full_margin_and_preserves_remaining_claims(self):
        self.rpc.block_limit = 12_000_000; self.rpc.gas_per_claim = 2_000_000
        result = self.plan(8)
        self.assertEqual(result['schema'], 2)
        self.assertEqual(len(result['next_batch']['claim_operations']), 5)
        self.assertEqual(len(result['remaining_claims']), 3)
        self.assertEqual(result['next_batch']['network_gas']['suggested_limit'], '12000000')
        self.assertEqual(result['planning']['simulation_gas_cap'], '12000000')

    def test_planner_detects_changed_same_hash_block_policy_between_trials(self):
        self.rpc.change_limit_at = 2
        with self.assertRaises(ProjectionError): self.plan(2)

    def test_larger_config_does_not_hide_global_price_or_provider_errors(self):
        self.rpc.gas_per_claim = 20_000_000; self.rpc.gas_price = 10**15
        with self.assertRaises(ProjectionError): self.plan(4)
        self.assertEqual(len(self.rpc.simulations), 1)

    def test_per_instance_policy_cannot_leak_across_concurrent_user_preparers(self):
        small = copy.deepcopy(self.config); small['fee_policy']['max_gas_limit'] = '1000000'
        other = Transactions(self.p, small)
        a = self.mint(); b = other.prepare(dict(action='mint', wallet=addr(30))); c = self.mint()
        self.assertEqual([x['simulation']['gas_cap'] for x in (a,b,c)], ['40000000', '1000000', '40000000'])
