"""Explicit activation gas reviews; controlled RPC/trace fixtures, no network."""
import copy
import unittest

from frontend_api.activation import ActivationTransactions, ActivationInputError, ActivationGasHeadroomError, GAS_CAP
from frontend_api.activation_config import ActivationConfig
from frontend_api.service import Projection, ProjectionError
from tests_python.test_frontend_activation import ActivationRPC
from tests_python.test_frontend_api import configuration
from zzz_ops.errors import RpcError


class GasActivationRPC(ActivationRPC):
    def __init__(self, **options):
        super().__init__(**options)
        self.block_limit = 40_000_000
        self.gas_header = None
        self.block_error = None
        self.gas_header_reads = 0
        self.trace_gas = None

    def call(self, method, params):
        if method == 'eth_getBlockByHash':
            self.calls.append((method, copy.deepcopy(params)))
            self.gas_header_reads += 1
            if self.block_error:
                raise self.block_error
            if self.gas_header is not None:
                return copy.deepcopy(self.gas_header)
            return dict(number=hex(self.head-11), hash=self.hash,
                        timestamp=hex(self.header_timestamp), gasLimit=hex(self.block_limit))
        return super().call(method, params)

    def trace(self, tx):
        result = super().trace(tx)
        if self.trace_gas is not None:
            result['gasUsed'] = hex(self.trace_gas)
        return result


class ActivationGasPolicy2Tests(unittest.TestCase):
    def service(self, rpc=None, *, limit='40000000', schema=2, fee='1000000000000000000'):
        rpc = rpc or GasActivationRPC()
        projection = Projection(configuration(), rpc, clock=lambda: 1000)
        config = copy.deepcopy(rpc.config)
        config['schema'] = schema
        if schema == 2:
            config['fee_policy'].update(max_gas_limit=limit, max_network_fee_wei=fee)
        return rpc, projection, ActivationTransactions(projection, config)

    def test_same_confirmed_cap_bounds_both_traces_measurement_and_final_estimate(self):
        rpc, _p, service = self.service()
        rpc.block_limit = 30_000_000
        rpc.estimate = 20_000_000
        rpc.trace_gas = 20_000_000  # The trace measurer must receive the same larger cap.
        result = service.prepare(rpc.request)
        self.assertEqual(result['schema'], 2)
        self.assertEqual(rpc.gas_header_reads, 1)
        self.assertEqual(result['network_gas']['suggested_limit'], '24000000')
        self.assertEqual(result['network_gas']['configured_gas_limit'], '40000000')
        self.assertEqual(result['network_gas']['confirmed_block_gas_limit'], '30000000')
        self.assertEqual(result['network_gas']['effective_gas_limit'], '30000000')
        self.assertTrue(result['network_gas']['full_twenty_percent_headroom'])
        calls = [params for method, params in rpc.calls if method in ('debug_traceCall', 'eth_estimateGas')]
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(call[0]['gas'] == hex(30_000_000) for call in calls))
        self.assertTrue(all(call[1] == {'blockHash': rpc.hash, 'requireCanonical': True} for call in calls))
        self.assertNotEqual(calls[0][0]['data'], calls[1][0]['data'])
        self.assertEqual(calls[1][0]['data'], calls[2][0]['data'])
        self.assertEqual(result['transaction']['data'], calls[2][0]['data'])
        self.assertNotIn('gas', result['transaction'])
        self.assertNotIn('nonce', result['transaction'])
        self.assertFalse(result['network_gas']['included_in_execution_loss'])

    def test_schema1_keeps_old_shape_12m_and_no_extra_header_read(self):
        rpc, _p, service = self.service(schema=1)
        rpc.block_error = RpcError('this method is unavailable')
        rpc.estimate = 11_000_000  # Historical policy still clips its advisory padding.
        result = service.prepare(rpc.request)
        self.assertEqual(result['schema'], 1)
        self.assertEqual(result['network_gas']['suggested_limit'], str(GAS_CAP))
        self.assertEqual(rpc.gas_header_reads, 0)
        self.assertNotIn('policy_schema', result['network_gas'])
        self.assertNotIn('effective_gas_limit', result['network_gas'])
        self.assertTrue(all(params[0]['gas'] == hex(GAS_CAP) for method, params in rpc.calls
                            if method in ('debug_traceCall', 'eth_estimateGas')))

    def test_full_twenty_percent_boundary_rounding_never_truncates(self):
        for estimate, expected in ((10_000_000, '12000000'), (10_000_001, None), (31_085_813, '37302976')):
            with self.subTest(estimate=estimate):
                rpc, _p, service = self.service(limit='12000000' if estimate < 20_000_000 else '40000000')
                rpc.estimate = estimate
                if expected is None:
                    with self.assertRaises(ActivationGasHeadroomError):
                        service.prepare(rpc.request)
                    self.assertEqual(rpc.trace_count, 2)
                else:
                    self.assertEqual(service.prepare(rpc.request)['network_gas']['suggested_limit'], expected)

    def test_approval_uses_same_explicit_cap_and_requires_new_preparation(self):
        rpc, _p, service = self.service()
        rpc.block_limit = 10_000_000
        rpc.estimate = 8_000_000
        rpc.allowance = 0
        result = service.prepare(rpc.request)
        self.assertEqual(result['schema'], 2)
        self.assertEqual(result['kind'], 'approval_required')
        self.assertFalse(result['activation_ready'])
        self.assertEqual(rpc.trace_count, 0)
        self.assertTrue(result['approval_steps'][0]['reprepare_after_confirmation'])
        execution = [(method, params) for method, params in rpc.calls
                     if method == 'eth_estimateGas' or method == 'eth_call' and 'from' in params[0]]
        self.assertEqual(len(execution), 2)
        self.assertTrue(all(params[0]['gas'] == hex(10_000_000) for _, params in execution))
        self.assertEqual(result['network_gas']['suggested_limit'], '9600000')
        rpc.allowance = 10**30
        rpc.block_limit = 9_000_000
        with self.assertRaises(ActivationGasHeadroomError):
            service.prepare(rpc.request)
        self.assertEqual(rpc.gas_header_reads, 2)

    def test_strict_operator_config_bounds_identity_and_no_payload_override(self):
        for bad in (None, True, 40_000_000, 4e7, '', '0', '20999', '64000001',
                    '040000000', '-1', '1e7', '0x10000', '40000000\n', '9'*1000):
            with self.subTest(limit=repr(bad)[:30]), self.assertRaises(ValueError):
                self.service(limit=bad)
        identities = []
        for valid in ('21000', '64000000'):
            rpc, _p, service = self.service(limit=valid)
            self.assertEqual(service.config.max_gas_limit, int(valid))
            identities.append(service.config.identity)
            self.assertEqual(rpc.calls, [])
        self.assertNotEqual(*identities)
        rpc, _p, service = self.service()
        with self.assertRaises(ActivationInputError):
            service.prepare({**rpc.request, 'max_gas_limit': '64000000'})
        self.assertEqual(rpc.calls, [])

    def test_schema2_fee_fields_are_required_strict_and_cannot_leak_into_schema1(self):
        for kind in ('missing_limit', 'missing_fee', 'extra', 'schema1'):
            rpc, p, service = self.service()
            cfg = copy.deepcopy(rpc.config)
            cfg['schema'] = 2
            cfg['fee_policy'].update(max_gas_limit='40000000', max_network_fee_wei='1000000000000000000')
            if kind == 'missing_limit': del cfg['fee_policy']['max_gas_limit']
            if kind == 'missing_fee': del cfg['fee_policy']['max_network_fee_wei']
            if kind == 'extra': cfg['fee_policy']['override'] = True
            if kind == 'schema1': cfg['schema'] = 1
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                ActivationConfig(cfg, p)
            self.assertEqual(rpc.calls, [])
        for bad in (True, 1000000, '', '0', '01', '1e18', '-1', '9'*21):
            with self.subTest(fee=bad), self.assertRaises(ValueError):
                self.service(fee=bad)

    def test_confirmed_header_inconsistency_fails_before_execution_without_fallback(self):
        good = dict(number=hex(99), hash='0x'+'b'*64, timestamp=hex(990), gasLimit=hex(40_000_000))
        for key, bad in (('hash', '0x'+'c'*64), ('number', '0x1'), ('timestamp', '0x1'),
                         ('gasLimit', None), ('gasLimit', True), ('gasLimit', '0x1'), ('gasLimit', hex(1<<64))):
            with self.subTest(key=key, value=bad):
                rpc, _p, service = self.service()
                rpc.gas_header = {**good, key: bad}
                with self.assertRaises(ProjectionError): service.prepare(rpc.request)
                self.assertEqual(rpc.trace_count, 0)
                self.assertFalse(any(method == 'eth_estimateGas' for method, _ in rpc.calls))

    def test_provider_error_does_not_fall_back_to_configured_or_historical_cap(self):
        rpc, _p, service = self.service()
        rpc.block_error = RpcError('confirmed hash unavailable')
        with self.assertRaises(RpcError): service.prepare(rpc.request)
        self.assertEqual(rpc.trace_count, 0)
        self.assertFalse(any(method == 'eth_estimateGas' for method, _ in rpc.calls))

    def test_padded_network_fee_and_native_balance_remain_separate_from_principal(self):
        rpc, _p, service = self.service(fee='599999999999999')
        # 500k estimate pads to600k; at1gwei the padded fee is0.0006ETH.
        with self.assertRaises(ProjectionError): service.prepare(rpc.request)
        rpc, _p, service = self.service(GasActivationRPC(native=True))
        rpc.balance = rpc.original_amount + 600000*rpc.gas_price - 1
        with self.assertRaises(ActivationInputError): service.prepare(rpc.request)

    def test_per_preparer_policy_is_not_global_and_successful_traces_cannot_override_estimate(self):
        rpc, p, large = self.service()
        small_cfg = copy.deepcopy(rpc.config)
        small_cfg['schema'] = 2
        small_cfg['fee_policy'].update(max_gas_limit='1000000', max_network_fee_wei='1000000000000000000')
        small = ActivationTransactions(p, small_cfg)
        a = large.prepare(rpc.request)
        b = small.prepare(rpc.request)
        c = large.prepare(rpc.request)
        self.assertEqual([x['network_gas']['effective_gas_limit'] for x in (a,b,c)],
                         ['40000000', '1000000', '40000000'])
        rpc.estimate = 1_000_001
        with self.assertRaises(ProjectionError): small.prepare(rpc.request)
        self.assertEqual(GAS_CAP, 12_000_000)


if __name__ == '__main__':
    unittest.main()
