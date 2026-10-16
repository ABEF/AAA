"""A capacity reservation is enumerated before it owns any liquidity."""
import json
import unittest
from unittest.mock import patch

from tests_python import test_keeper as fixtures
from zzz_ops.abi import calldata


class KeeperReservationTests(unittest.TestCase):
    def setUp(self):
        # Reuse only the existing static-ABI fixture, not its test cases. Neither
        # Keeper.view nor Keeper._bucket is mocked by these regressions.
        self.fixture = fixtures.PoolKeeperTests('test_empty_inventory_submits_nothing')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.reserved, self.active = 7, 9
        self.fixture.ids = [self.reserved, self.active]
        self.original_call = self.fixture.rpc.call
        self.fixture.rpc.call = self.reservation_call

    def reservation_call(self, method, params):
        if method == 'eth_call' and 'from' not in params[0]:
            data = params[0]['data']
            selector = data[:10]
            args = [int(data[offset:offset+64], 16) for offset in range(10, len(data), 64)]
            if data == calldata('group(uint256)', self.reserved):
                self.fixture.rpc.calls.append((method, params))
                return '0x' + '0' * (15 * 64)  # Actual default Position ABI: None.
            for signature in ('bucketTotalShares(uint256)', 'rewardReceiver(uint256)',
                              'needsRebalance(uint256)', 'compoundBalance(uint256,address)',
                              'remoteIndividual(uint256,address)', 'remoteCollective(uint256,address)'):
                placeholders = [self.reserved, fixtures.B] if ',address)' in signature else [self.reserved]
                if selector == calldata(signature, *placeholders)[:10] and args[0] == self.reserved:
                    self.fail('Unfunded reserved bucket reached financial maintenance reads')
            for signature in ('poolBucket(bytes32)', 'get(bytes32)', 'accounting(bytes32)', 'nativeAsset(bytes32)'):
                if selector == calldata(signature, '0x' + '0' * 64)[:10] and args[0] == 0:
                    self.fail('Reserved None state attempted to read its nonexistent pool')
        return self.original_call(method, params)

    def assert_healthy_preview(self):
        keeper = self.fixture.k
        health = json.loads(keeper.health_path.read_text())
        self.assertEqual(health['status'], 'dry_run')
        self.assertEqual(health['skipped_buckets'], 0)
        self.assertEqual(health['blocked_actions'], 0)
        self.assertEqual(health['consecutive_failures'], 0)
        self.assertFalse(health['pending'])

    def test_reserved_none_before_active_is_skipped_without_degradation_or_starvation(self):
        keeper = self.fixture.k
        with patch.object(keeper, 'submit', return_value=True) as submit:
            self.assertTrue(keeper.run_cycle())
        submit.assert_called_once_with('vault', 'rebalance(uint256,uint128,uint256)',
                                       (self.active, 1, self.fixture.rpc.now + 180), f'rebalance:{self.active}')
        group_selector = calldata('group(uint256)', 0)[:10]
        groups = [int(params[0]['data'][10:], 16) for method, params in self.fixture.rpc.calls
                  if method == 'eth_call' and params[0]['data'].startswith(group_selector)]
        self.assertEqual(groups, [self.reserved, self.active])
        self.assertEqual(keeper.state['bucket_cursor'], 2)
        self.assert_healthy_preview()

    def test_one_slot_scan_persists_progress_past_none_before_next_active_cycle(self):
        keeper = self.fixture.k
        keeper.batch_size = 1
        with patch.object(keeper, 'submit', return_value=True) as submit:
            self.assertTrue(keeper.run_cycle())
            submit.assert_not_called()
            self.assertEqual(keeper.state['bucket_cursor'], 1)
            self.assertEqual(json.loads(keeper.path.read_text())['bucket_cursor'], 1)
            self.assert_healthy_preview()
            self.assertTrue(keeper.run_cycle())
        submit.assert_called_once_with('vault', 'rebalance(uint256,uint128,uint256)',
                                       (self.active, 1, self.fixture.rpc.now + 180), f'rebalance:{self.active}')
        self.assertEqual(keeper.state['bucket_cursor'], 2)
        self.assert_healthy_preview()


if __name__ == '__main__':
    unittest.main()
