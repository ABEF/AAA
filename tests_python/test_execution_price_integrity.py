"""Receipt fee observations must agree with signed fixed-price transactions."""
import unittest

from tests_python import test_keeper_fees as keeper_fixtures
from tests_python import test_local_browser as browser_fixtures
from zzz_ops.ethereum_fees import execution_price


class ExecutionPriceIntegrityTests(unittest.TestCase):
    def test_legacy_and_access_list_require_exact_signed_price(self):
        for kind in ('0x0', '0x1'):
            transaction = dict(type=kind, gasPrice='0x64')
            self.assertEqual(execution_price(transaction, {}, {'effectiveGasPrice': '0x64'}), 100)
            for reported in ('0x0', '0x63', '0x65'):
                with self.subTest(kind=kind, reported=reported), self.assertRaises(ValueError):
                    execution_price(transaction, {}, {'effectiveGasPrice': reported})

    def test_missing_or_malformed_fixed_price_evidence_remains_unavailable(self):
        for transaction, receipt in (({}, {'effectiveGasPrice': '0x64'}),
                ({'gasPrice': '0x64'}, {}), ({'gasPrice': '0x64'}, {'effectiveGasPrice': None}),
                ({'type': '0x1', 'gasPrice': '0x64'}, {'effectiveGasPrice': True})):
            with self.subTest(transaction=transaction, receipt=receipt), self.assertRaises(ValueError):
                execution_price(transaction, {}, receipt)

    def test_dynamic_price_still_uses_signed_caps_and_canonical_base(self):
        transaction = dict(type='0x2', maxFeePerGas='0xa', maxPriorityFeePerGas='0x2')
        for receipt in ({}, {'effectiveGasPrice': '0x63'}, {'effectiveGasPrice': None}):
            self.assertEqual(execution_price(transaction, {'baseFeePerGas': '0x3'}, receipt), 5)
        with self.assertRaises(ValueError): execution_price(transaction, {}, {})
        with self.assertRaises(ValueError): execution_price({**transaction, 'type': '0x3'}, {}, {})

    def test_browser_receipt_observation_rejects_underreported_fixed_price_without_actions(self):
        fixture = browser_fixtures.BrowserTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for kind in ('0x0', '0x1'):
            fixture.transaction['type'] = kind
            fixture.receipt['effectiveGasPrice'] = '0x63'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                fixture.browser._receipt(browser_fixtures.HASH, fixture.tx)
        self.assertEqual(fixture.lab.operations.items, {})
        self.assertEqual(fixture.lab.receipts, [])
        fixture.lab.call.assert_not_called()
        fixture.lab.sync.assert_not_called()

    def test_keeper_recovery_preserves_pending_and_spend_on_underreported_access_list_price(self):
        fixture = keeper_fixtures.KeeperSignedFeeTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.rpc.tx.update(type='0x1', gasPrice='0xa')
        fixture.rpc.receipt['effectiveGasPrice'] = '0x9'
        fixture.reject_without_mutation()


if __name__ == '__main__':
    unittest.main()
