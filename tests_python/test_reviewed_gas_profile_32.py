"""32M activation candidate boundaries, with injected RPC only.

Historical fixtures are reused without collecting or running their test classes.
These checks do not qualify markets, provider capacity, complete fees or rollout.
"""
import copy
import json
from pathlib import Path
import unittest

from frontend_api.activation import (
    ActivationGasHeadroomError, ActivationInputError, ActivationTransactions,
)
from frontend_api.activation_config import ActivationConfig
from frontend_api.service import ProjectionError
from frontend_api.transaction_gas import DEFAULT_GAS_LIMIT
from tests_python import test_reviewed_gas_profiles_20_24 as historical_profiles


ROOT = Path(__file__).resolve().parents[1]


class Activation32MProfileTests(unittest.TestCase):
    def fixture(self):
        owner = historical_profiles.Activation20MProfileTests()
        rpc, projection, config, old_service, header, tx = owner.fixture()
        config = copy.deepcopy(config)
        config['fee_policy'].update(max_gas_limit='32000000',
                                    max_network_fee_wei='64000000')
        rpc.estimate = 26_000_000
        service = ActivationTransactions(projection, config)
        return owner, rpc, projection, config, old_service, service, header, tx

    def test_candidate_is_matching_unsigned_overlay_without_fee_approval(self):
        package = json.loads((ROOT / 'config/activation-gas-32m.candidate.json').read_text())
        for flag in ('production_approved', 'live_adoption',
                     'global_defaults_changed', 'public_signing_enabled'):
            self.assertIs(package[flag], False)
        contribution = package['profiles']['contribution']
        self.assertEqual(contribution['gas_limit'], '32000000')
        self.assertEqual(contribution['estimate_padding_percent'], 20)
        self.assertEqual(contribution['maximum_estimate_before_padding'], '26666666')
        overlay = package['activation_configuration_overlay']
        self.assertEqual(overlay['schema'], 2)
        fee = overlay['fee_policy']
        self.assertEqual(fee['max_gas_limit'], contribution['gas_limit'])
        self.assertIs(fee['estimate_includes_all_fees'], False)
        for name in ('review_hash', 'max_gas_price_wei', 'max_network_fee_wei'):
            self.assertIsNone(fee[name])
        website = package['website_manifest_overlay']
        self.assertEqual(website['activation_policy_schema'], 2)
        self.assertIs(type(website['limits']['gas']), int)
        self.assertEqual(website['limits']['gas'], int(fee['max_gas_limit']))
        self.assertIsNone(website['activation_sha256'])
        self.assertIsNone(website['activation_fee_review'])
        self.assertIsNone(website['limits']['gas_price_wei'])
        self.assertIsNone(website['limits']['network_fee_wei'])
        for name in ('maintenance_keeper', 'maintenance_manual'):
            self.assertEqual(int(package['profiles'][name]['gas_limit']), 24_000_000)
            self.assertEqual(package['profiles'][name]['estimate_padding_percent'], 25)

    def test_full_twenty_percent_boundary_is_not_clipped(self):
        for estimate, accepted in ((26_666_666, True), (26_666_667, False)):
            with self.subTest(estimate=estimate):
                _owner, rpc, _p, _cfg, _old, service, header, tx = self.fixture()
                rpc.estimate = estimate
                review = service._gas_review(header)
                block = {'blockHash': rpc.hash, 'requireCanonical': True}
                if accepted:
                    result = service._gas(tx, block, review)
                    self.assertEqual(result['suggested_limit'], '32000000')
                    self.assertEqual(result['effective_gas_limit'], '32000000')
                    self.assertTrue(result['full_twenty_percent_headroom'])
                else:
                    with self.assertRaises(ActivationGasHeadroomError):
                        service._gas(tx, block, review)
                calls = [args for method, args in rpc.calls if method == 'eth_estimateGas']
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][0]['gas'], hex(32_000_000))

    def test_synthetic_header_cannot_raise_budget_and_smaller_header_binds(self):
        for block_limit, estimate, padded in (
                (1 << 50, 26_000_000, 31_200_000),
                (24_000_000, 20_000_000, 24_000_000)):
            with self.subTest(block_limit=block_limit):
                owner, rpc, _p, _cfg, _old, service, header, tx = self.fixture()
                owner.block_limit = block_limit
                rpc.estimate = estimate
                review = service._gas_review(header)
                result = service._gas(tx, {'blockHash': rpc.hash, 'requireCanonical': True}, review)
                self.assertEqual(review.effective, min(32_000_000, block_limit))
                self.assertEqual(result['suggested_limit'], str(padded))
                self.assertEqual(result['configured_gas_limit'], '32000000')
                self.assertEqual(result['confirmed_block_gas_limit'], str(block_limit))

    def test_separate_price_fee_and_funding_limits_remain_binding(self):
        for fault in ('price', 'fee', 'balance'):
            with self.subTest(fault=fault):
                _owner, rpc, _p, _cfg, _old, service, header, tx = self.fixture()
                if fault == 'price':
                    rpc.gas_price = 3
                elif fault == 'fee':
                    service.config.max_network_fee = 62_399_999
                else:
                    tx['value'] = hex(rpc.balance - 62_400_000 + 1)
                original = copy.deepcopy(tx)
                with self.assertRaises((ProjectionError, ActivationInputError)):
                    service._gas(tx, {'blockHash': rpc.hash, 'requireCanonical': True},
                                 service._gas_review(header))
                self.assertEqual(tx, original)
                self.assertEqual(service.config.max_gas_limit, 32_000_000)

    def test_default_and_saved_twenty_million_identity_remain_distinct(self):
        _owner, rpc, projection, config, old_service, service, _header, _tx = self.fixture()
        legacy = copy.deepcopy(config)
        legacy['schema'] = 1
        legacy['fee_policy'].pop('max_gas_limit')
        legacy['fee_policy'].pop('max_network_fee_wei')
        default = ActivationConfig(legacy, projection)
        self.assertEqual(DEFAULT_GAS_LIMIT, 12_000_000)
        self.assertEqual(default.max_gas_limit, 12_000_000)
        self.assertEqual(old_service.config.max_gas_limit, 20_000_000)
        self.assertEqual(len({default.identity, old_service.config.identity,
                              service.config.identity}), 3)
        self.assertEqual(rpc.calls, [])

    def test_larger_budget_does_not_approve_missing_fee_review(self):
        _owner, _rpc, projection, config, _old, _service, _header, _tx = self.fixture()
        for field, value in (('estimate_includes_all_fees', False), ('review_hash', None),
                             ('max_network_fee_wei', None), ('max_gas_price_wei', None)):
            bad = copy.deepcopy(config)
            bad['fee_policy'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                ActivationConfig(bad, projection)

    def test_wallet_allowance_is_fresh_padded_estimate_not_entire_ceiling(self):
        _owner, rpc, _p, _cfg, _old, service, header, tx = self.fixture()
        rpc.estimate = 16_460_899
        result = service._gas(tx, {'blockHash': rpc.hash, 'requireCanonical': True},
                              service._gas_review(header))
        self.assertEqual(result['suggested_limit'], '19753079')
        self.assertEqual(result['configured_gas_limit'], '32000000')
        self.assertEqual(result['suggested_limit_cost_wei'], '39506158')
        self.assertIs(result['included_in_execution_loss'], False)


if __name__ == '__main__':
    unittest.main()
