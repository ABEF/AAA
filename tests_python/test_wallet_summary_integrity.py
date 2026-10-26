"""Wallet chunk integrity separates invalid data from an unavailable view.

The existing confirmed-snapshot fixture supplies deterministic ABI words; no
public provider, database, signing or production capacity is exercised here.
"""
import unittest

from frontend_api.portfolio import read
from frontend_api.service import Projection, ProjectionError
from zzz_ops.errors import RpcError, WorkLimit
from tests_python import test_wallet_summary as fixtures


class WalletSummaryIntegrityTests(unittest.TestCase):
    def broken_lp(self, failure):
        projection = fixtures.Snapshot(2)
        original = projection._call

        def call(target, method, identifier, *, block, words):
            if identifier == 1:
                if isinstance(failure, Exception):
                    raise failure
                return list(failure)
            return original(target, method, identifier, block=block, words=words)

        projection._call = call
        return projection

    def test_nonboolean_lp_availability_rejects_the_entire_chunk(self):
        for flag in (2, 255, 2**256 - 1):
            with self.subTest(flag=flag):
                projection = self.broken_lp((f'{flag:064x}', f'{100:064x}'))
                with self.assertRaises(ProjectionError):
                    read(projection, fixtures.OWNER, 90, 0)

    def test_unavailable_lp_with_nonzero_amount_rejects_the_entire_chunk(self):
        projection = self.broken_lp((f'{0:064x}', f'{100:064x}'))
        with self.assertRaisesRegex(ProjectionError, 'Unavailable LP contains a value'):
            read(projection, fixtures.OWNER, 90, 0)

    def test_genuine_lp_view_outage_preserves_healthy_eth_without_partial_lp(self):
        projection = self.broken_lp(RpcError('synthetic optional view outage'))
        result = read(projection, fixtures.OWNER, 90, 0)
        self.assertIsNone(result['lp_usd_18'])
        self.assertEqual(result['claimable_eth_wei'], '15')
        self.assertEqual(result['token_ids'], ['1', '2'])

    def test_work_limit_is_never_converted_into_unavailable_lp(self):
        projection = self.broken_lp(WorkLimit('rpc_budget'))
        with self.assertRaises(WorkLimit):
            read(projection, fixtures.OWNER, 90, 0)

    def test_consistent_lp_and_eth_totals_retain_the_same_snapshot(self):
        projection = fixtures.Snapshot(2)
        result = read(projection, fixtures.OWNER, 90, 0)
        self.assertEqual(result['lp_usd_18'], '300')
        self.assertEqual(result['claimable_eth_wei'], '15')
        self.assertEqual(result['provenance']['block_number'], 90)
        self.assertEqual(result['provenance']['block_hash'], fixtures.HASH)
        self.assertIsNone(result['next_offset'])

    def test_malformed_native_claimable_abi_rejects_the_entire_chunk(self):
        projection = fixtures.Snapshot(2)
        original = projection._uint
        reader = object.__new__(Projection)
        reader.accounting_version = 3
        reader.contracts = {
            role: type('Contract', (), {'address': '0x' + str(n) * 40})()
            for n, role in enumerate(('rewards', 'royalties'), 4)
        }
        reader.rpc = type('MalformedTransport', (), {'call': lambda self, method, params: '0x01'})()

        def read_uint(role, signature, *args, block):
            if role == 'rewards' and signature == 'claimable(uint256,address)' and args[0] == 1:
                return reader._uint(role, signature, *args, block=block)
            return original(role, signature, *args, block=block)

        projection._uint = read_uint
        with self.assertRaisesRegex(ProjectionError, 'Malformed static ABI result'):
            read(projection, fixtures.OWNER, 90, 0)

    def test_genuine_native_claimable_outage_preserves_lp_without_partial_eth(self):
        projection = fixtures.Snapshot(2)
        projection.eth_missing = 1
        result = read(projection, fixtures.OWNER, 90, 0)
        self.assertEqual(result['lp_usd_18'], '300')
        self.assertIsNone(result['claimable_eth_wei'])

    def inactive(self, lp_raw=0, individual=0, royalties=0, *, lp_failure=None):
        projection = fixtures.Snapshot(2)
        projection.weights[1] = 0
        uint, call = projection._uint, projection._call

        def read_uint(role, signature, *args, block):
            if signature == 'claimable(uint256,address)' and args[0] == 1:
                projection.calls.append((signature, args, block))
                return individual if role == 'rewards' else royalties
            return uint(role, signature, *args, block=block)

        def read_call(target, signature, identifier, *, block, words):
            if identifier == 1:
                projection.calls.append((signature, (identifier,), block))
                if lp_failure:
                    raise lp_failure
                return [f'{1:064x}', f'{lp_raw:064x}']
            return call(target, signature, identifier, block=block, words=words)

        projection._uint, projection._call = read_uint, read_call
        return projection

    def test_current_inactive_nft_cannot_add_lp_or_either_native_reward(self):
        for component in ('lp_raw', 'individual', 'royalties'):
            with self.subTest(component=component):
                projection = self.inactive(**{component: 7})
                with self.assertRaises(ProjectionError):
                    read(projection, fixtures.OWNER, 90, 0)

    def test_current_inactive_views_are_read_not_assumed_zero(self):
        projection = self.inactive()
        result = read(projection, fixtures.OWNER, 90, 0)
        self.assertEqual(result['lp_usd_18'], '200')
        self.assertEqual(result['claimable_eth_wei'], '10')
        self.assertEqual(sum(method == 'claimable(uint256,address)' and args[0] == 1
                             for method, args, block in projection.calls), 2)
        projection = self.inactive(lp_failure=RpcError('synthetic unavailable dormant view'))
        result = read(projection, fixtures.OWNER, 90, 0)
        self.assertIsNone(result['lp_usd_18'])
        self.assertEqual(result['claimable_eth_wei'], '10')

    def test_current_invalid_royalty_weight_rejects_before_aggregation(self):
        for weight in (4, 2**256 - 1):
            with self.subTest(weight=weight):
                projection = fixtures.Snapshot(2)
                projection.weights[1] = weight
                with self.assertRaises(ProjectionError):
                    read(projection, fixtures.OWNER, 90, 0)

    def test_historical_profiles_keep_their_original_read_shape(self):
        for version in (1, 2):
            with self.subTest(version=version):
                projection = fixtures.Snapshot(2)
                projection.accounting_version = version
                projection.weights = {i: 0 for i in projection.ids}
                result = read(projection, fixtures.OWNER, 90, 0)
                self.assertEqual(result['lp_usd_18'], '300')
                self.assertEqual(result['claimable_eth_wei'], '15')
                self.assertFalse(any(method == 'weightOf(uint256)' for method, args, block in projection.calls))


if __name__ == '__main__':
    unittest.main()
