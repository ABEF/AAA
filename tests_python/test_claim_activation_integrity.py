"""Unsigned current-profile claims reject impossible activation/balance states.

Byte-level read/simulation fixtures only: no signing, RPC network, service or
existing local-chain state. Historical profiles retain their original boundary.
"""
import unittest
from unittest.mock import patch

from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.transactions import Transactions, TransactionInputError
from tests_python.test_current_fee_integrity import CurrentFeeRPC
from tests_python.test_frontend_api import addr, configuration, words
from tests_python.test_frontend_transactions import TransactionRPC, transaction_config
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class ClaimIntegrityRPC(TransactionRPC, CurrentFeeRPC):
    def __init__(self, version=3):
        # TransactionRPC.super() reaches CurrentFeeRPC then MockRPC in this MRO.
        super().__init__()
        if version != 3:
            self.responses = CurrentFeeRPC(version).responses
        self.version = version


class ClaimActivationIntegrityTests(unittest.TestCase):
    def service(self, *, version=3, dormant=False):
        rpc = ClaimIntegrityRPC(version)
        config = configuration()
        config['accounting_version'] = version
        if version == 3:
            config['fee_intake_version'] = 1
        if dormant:
            rpc.dormant()
        projection = Projection(config, rpc, clock=lambda: 1000)
        return rpc, Transactions(projection, transaction_config(projection))

    @staticmethod
    def entry(rpc, *, identifier=None, royalty=False, asset=ZERO):
        return {'token_id': str(rpc.nft_id if identifier is None else identifier),
                'asset': asset, 'royalty': royalty}

    def prepare(self, rpc, service, entries=None, *, owner=None):
        return service.prepare({'action': 'claim', 'wallet': owner or addr(30),
                                'claims': entries or [self.entry(rpc)]})

    @staticmethod
    def weight_reads(rpc):
        selector = calldata('weightOf(uint256)', 1)[:10]
        return [params for method, params in rpc.calls if method == 'eth_call'
                and params[0].get('to') == addr(5) and params[0]['data'].startswith(selector)]

    def test_dormant_positive_lp_or_royalty_balance_cannot_become_a_wallet_review(self):
        for royalty, assets in ((False, (ZERO, addr(20), addr(21))), (True, (ZERO, addr(21)))):
            for asset in assets:
                with self.subTest(royalty=royalty, asset=asset):
                    rpc, service = self.service(dormant=True)
                    rpc.put(addr(5 if royalty else 4), 'claimable(uint256,address)',
                            (rpc.nft_id, asset), (17,))
                    with self.assertRaisesRegex(ProjectionError, 'Inactive NFT'):
                        self.prepare(rpc, service, [self.entry(rpc, royalty=royalty, asset=asset)])
                    self.assertEqual(rpc.simulations, [])

    def test_honest_dormant_zero_remains_an_empty_claim_input_error(self):
        rpc, service = self.service(dormant=True)
        with self.assertRaisesRegex(TransactionInputError, 'no funded balance'):
            self.prepare(rpc, service)
        self.assertEqual(rpc.simulations, [])

    def test_out_of_range_current_activation_weight_fails_before_simulation(self):
        for weight in (4, (1 << 256) - 1):
            with self.subTest(weight=weight):
                rpc, service = self.service()
                rpc.put(addr(5), 'weightOf(uint256)', (rpc.nft_id,), (weight,))
                with self.assertRaisesRegex(ProjectionError, 'weight'):
                    self.prepare(rpc, service)
                self.assertEqual(rpc.simulations, [])

    def test_malformed_activation_abi_cannot_be_treated_as_active(self):
        for raw in ('0x', '0x01', words(1, 2), '0x'+'g'*64):
            with self.subTest(raw=raw):
                rpc, service = self.service()
                rpc.responses[addr(5), calldata('weightOf(uint256)', rpc.nft_id)] = raw
                with self.assertRaises(ProjectionError):
                    self.prepare(rpc, service)
                self.assertEqual(rpc.simulations, [])

    def test_activation_view_outage_cannot_fall_back_to_positive_claimable(self):
        rpc, service = self.service()
        original = rpc.call
        key = addr(5), calldata('weightOf(uint256)', rpc.nft_id)
        def outage(method, params):
            if method == 'eth_call' and (params[0]['to'], params[0]['data']) == key:
                raise RpcError('Synthetic core activation view outage')
            return original(method, params)
        with patch.object(rpc, 'call', side_effect=outage), self.assertRaises(RpcError):
            self.prepare(rpc, service)
        self.assertEqual(rpc.simulations, [])

    def test_all_three_active_rarity_weights_keep_native_lp_and_royalty_claims(self):
        for weight in (1, 2, 3):
            with self.subTest(weight=weight):
                rpc, service = self.service()
                rpc.put(addr(5), 'weightOf(uint256)', (rpc.nft_id,), (weight,))
                entries = [self.entry(rpc), self.entry(rpc, royalty=True)]
                result = self.prepare(rpc, service, entries)
                self.assertEqual(len(result['claim_operations']), 2)
                self.assertEqual(len(rpc.simulations), 1)

    def test_activation_is_read_once_per_distinct_nft_across_assets_and_ledgers(self):
        rpc, service = self.service()
        entries = [self.entry(rpc), self.entry(rpc, asset=addr(20)),
                   self.entry(rpc, royalty=True), self.entry(rpc, royalty=True, asset=addr(21))]
        self.prepare(rpc, service, entries)
        self.assertEqual(len(self.weight_reads(rpc)), 1)
        self.assertEqual(self.weight_reads(rpc)[0][-1], {'blockHash': rpc.hash, 'requireCanonical': True})

    def test_later_inactive_nft_prevents_entire_mixed_batch_review(self):
        rpc, service = self.service()
        second = rpc.nft_id + 1
        rpc.put(addr(2), 'mintOrdinalOf(uint256)', (second,), (2,))
        rpc.put(addr(2), 'tokenAtOrdinal(uint256)', (2,), (second,))
        rpc.put(addr(2), 'ownerOf(uint256)', (second,), (addr(30),))
        rpc.put(addr(5), 'weightOf(uint256)', (second,), (0,))
        rpc.put(addr(4), 'claimable(uint256,address)', (second, ZERO), (9,))
        with self.assertRaisesRegex(ProjectionError, 'Inactive NFT'):
            self.prepare(rpc, service, [self.entry(rpc), self.entry(rpc, identifier=second)])
        self.assertEqual(rpc.simulations, [])

    def test_active_parked_and_outbound_principal_states_keep_earned_claims(self):
        for status in (1, 2, 4):
            with self.subTest(status=status):
                rpc, service = self.service()
                rpc.put(addr(3), 'nftStatus(uint256)', (rpc.nft_id,), (status,))
                result = self.prepare(rpc, service)
                self.assertEqual(result['claim_operations'][0]['view_raw'], str(7*10**18))

    def test_deferred_optional_currency_does_not_remove_global_activation_rights(self):
        rpc, service = self.service()
        rpc.put(addr(5), 'eligibleFor(uint256,address)', (rpc.nft_id, addr(21)), (0,))
        result = self.prepare(rpc, service, [self.entry(rpc), self.entry(rpc, royalty=True)])
        self.assertEqual(len(result['claim_operations']), 2)

    def test_failed_optional_currency_does_not_block_healthy_native_claims(self):
        rpc, service = self.service()
        rpc.responses[addr(21), calldata('decimals()')] = '0x01'
        result = self.prepare(rpc, service, [self.entry(rpc), self.entry(rpc, royalty=True)])
        self.assertEqual(len(result['claim_operations']), 2)
        self.assertTrue(all(row['asset'] == ZERO for row in result['claim_operations']))

    def test_legacy_profiles_do_not_gain_a_new_activation_getter_requirement(self):
        for version in (1, 2):
            with self.subTest(version=version):
                rpc, service = self.service(version=version)
                rpc.put(addr(5), 'weightOf(uint256)', (rpc.nft_id,), (0,))
                result = self.prepare(rpc, service, [self.entry(rpc, asset=addr(20))])
                self.assertEqual(len(result['claim_operations']), 1)
                self.assertEqual(self.weight_reads(rpc), [])

    def test_ownership_is_checked_before_activation_or_simulation(self):
        rpc, service = self.service()
        with self.assertRaisesRegex(TransactionInputError, 'does not own'):
            self.prepare(rpc, service, owner=addr(31))
        self.assertEqual(self.weight_reads(rpc), [])
        self.assertEqual(rpc.simulations, [])

    def test_valid_simulation_difference_still_keeps_separate_currency_amounts(self):
        rpc, service = self.service()
        result = self.prepare(rpc, service, [self.entry(rpc), self.entry(rpc, royalty=True, asset=addr(21))])
        first = result['claim_operations'][0]
        self.assertNotEqual(first['view_raw'], first['simulated_raw'])
        self.assertEqual([row['decimals'] for row in result['claim_operations']], [18, 6])
        self.assertNotIn('total', result)
        self.assertTrue(all('send' not in method.lower() and 'sign' not in method.lower()
                            for method, _ in rpc.calls))


if __name__ == '__main__':
    unittest.main()
