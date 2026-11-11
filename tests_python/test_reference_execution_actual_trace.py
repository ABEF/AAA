"""Replay actual isolated-Anvil context1 traces; no public market/gas approval.

The production12M profile rejects these exact operations. Separate diagnostic
policy2 simulations retain all financial guards and full20% headroom. MockAccess,
registry/admission, Permit2, ETH/VRF publications and funded markets are explicit
fixture seams. This test does not call RPC, sign or broadcast transactions.
"""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from frontend_api.activation_trace import measure

FIXTURES = Path(__file__).with_name('fixtures')
HASHES = {'eth-activate': 'de36111deb841209c207284155922221e74b3e4bcad9bbfe56c6cc7b0ef22067', 'zzz-activate': '35f9501c21707943df20c1ac51d3f4f6039455f496420ea81ccbe7abfe4da946', 'eth-grow': 'bd4fd01f7fca7a4e50993f907276d7374d7464bcee8a818addbfc1bb66430cdf', 'zzz-grow': '19a51161b5f5d0b7163796a73758a2cedda629a94b6661f80fe277c9e60122b5'}

class ActualReferenceExecutionTraceTests(unittest.TestCase):
    def check_actual(self, name, increase, source_is_native):
        path=FIXTURES/('reference-execution1-actual-'+name+'.json.gz')
        encoded=path.read_bytes()
        self.assertEqual(hashlib.sha256(encoded).hexdigest(),HASHES[name])
        fixture=json.loads(gzip.decompress(encoded))
        trace_call=fixture['actual_trace_call'];tx=trace_call['params'][0]
        self.assertEqual(trace_call['method'],'debug_traceCall')
        self.assertTrue(trace_call['params'][1]['requireCanonical'])
        self.assertTrue(trace_call['params'][2]['tracerConfig']['withLog'])
        self.assertEqual(tx['from'],trace_call['result']['from'])
        self.assertEqual(tx['to'],trace_call['result']['to'])
        for key in ('from','to','data','value'):self.assertEqual(tx[key],fixture['default_call']['params'][0][key])
        self.assertEqual(len(fixture['materialized_runtime_hashes']),35)
        self.assertEqual(len(fixture['omitted_harness']),1)
        req=copy.deepcopy(fixture['request'])
        self.assertEqual(req['execution_price_version'],1)
        self.assertEqual(req['lp_routing_version'],3)
        self.assertEqual(req['increase'],increase)
        self.assertEqual(req['source']=='0x'+'0'*40,source_is_native)
        self.assertFalse(fixture['default_policy']['accepted'])
        self.assertFalse(fixture['default_policy']['eth_call_succeeded'])
        self.assertEqual(fixture['default_policy']['gas_cap'],12_000_000)
        self.assertIn('error',fixture['default_call']['response'])
        self.assertEqual(int(fixture['default_call']['params'][0]['gas'],16),12_000_000)
        policy=fixture['diagnostic_policy2']
        self.assertFalse(policy['enabled_for_production'])
        self.assertEqual(int(tx['gas'],16),policy['effective_gas_cap'])
        self.assertLessEqual(policy['effective_gas_cap'],policy['confirmed_block_gas_limit'])
        self.assertLessEqual(policy['effective_gas_cap'],64_000_000)
        self.assertGreaterEqual(policy['full_twenty_percent_limit'],(policy['estimated_gas']*120+99)//100)
        self.assertLessEqual(policy['full_twenty_percent_limit'],policy['effective_gas_cap'])
        self.assertEqual(policy['reviewed_maximum_fee_wei'],policy['full_twenty_percent_limit']*policy['gas_price_wei'])
        self.assertLessEqual(policy['reviewed_maximum_fee_wei'],policy['network_fee_budget_wei'])
        observed=measure(trace_call['result'],tx,fixture['pins'],req,fixture['gross_usd_18'],fixture['max_slippage_bps'])
        self.assertEqual(observed,fixture['expected_measurement'])
        self.assertGreaterEqual(observed['marginal_deployed_usd_18'],observed['required_deployed_usd_18'])
        self.assertGreater(observed['shares_added_raw'],0)
        self.assertGreater(observed['lp_liquidity_added_raw'],0)
        self.assertLessEqual((observed['simulation_gas_used']*120+99)//100,policy['full_twenty_percent_limit'])
        self.assertTrue(fixture['contract_source_sha256'])
        self.assertTrue(fixture['runtime_hashes'])

    def test_actual_eth_activation(self):self.check_actual('eth-activate',False,True)
    def test_actual_zzz_activation(self):self.check_actual('zzz-activate',False,False)
    def test_actual_eth_growth(self):self.check_actual('eth-grow',True,True)
    def test_actual_zzz_growth(self):self.check_actual('zzz-grow',True,False)
