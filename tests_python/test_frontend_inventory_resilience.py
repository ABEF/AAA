"""Ownership inventory survives optional currency faults, not core faults.

Use the existing byte-level RPC and actual SQLite/indexer history fixture without
inheriting its test cases. No wallet, network or installed service is accessed.
"""
import unittest
from unittest.mock import patch

from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.history import HistoryError
from tests_python.test_frontend_api import addr, configuration
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError, WorkLimit


class FrontendInventoryResilienceTests(unittest.TestCase):
    def setUp(self):
        from tests_python.test_frontend_history import ConfirmedHistoryTests
        self.fixture = ConfirmedHistoryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.rpc = self.fixture.rpc

    def projection(self, version=3):
        config = configuration()
        config.update(history=self.fixture.config, accounting_version=version, fee_intake_version=1)
        self.rpc.put(addr(3), 'ACCOUNTING_VERSION()', values=(version,))
        domain = b'ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5' if version == 4 else b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4'
        self.rpc.put(addr(7), 'SCHEMA()', values=('0x' + keccak256(domain).hex(),))
        self.rpc.put(addr(1), 'GOVERNANCE_VERSION()', values=(2,))
        self.rpc.put(addr(1), 'governance()', values=(addr(40),))
        self.rpc.put(addr(4), 'assetCount()', values=(3,))
        for index, asset in enumerate((ZERO, addr(20), addr(21))):
            self.rpc.put(addr(4), 'assets(uint256)', (index,), (asset,))
        if version == 4:
            code = bytes((0x60, 9, 0))
            self.rpc.codes[addr(9)] = '0x' + code.hex()
            config['contracts']['principal_exit'] = dict(address=addr(9), code_hash='0x' + keccak256(code).hex())
            self.rpc.put(addr(1), 'module(bytes32)', ('0x' + keccak256(b'ZZZMigration').hex(),), (addr(9),))
            self.rpc.put(addr(9), 'access()', values=(addr(1),))
            self.rpc.put(addr(9), 'CUSTODY_VERSION()', values=(3,))
            self.rpc.put(addr(1), 'lpExitStarted()', values=(0,))
            self.rpc.put(addr(9), 'exitPhase()', values=(0,))
        return Projection(config, self.rpc, clock=lambda: 1000)

    def assert_inventory(self, p):
        value = p.wallet(addr(30))
        self.assertTrue(value['available'])
        self.assertEqual(value['count'], 1)
        self.assertEqual(value['token_ids'], [str(self.rpc.nft_id)])
        self.assertEqual(value['wallet'], addr(30))
        self.assertEqual(value['provenance']['block_number'], 99)
        self.assertEqual(value['provenance']['block_hash'], self.rpc.hash)
        self.assertNotIn('claimable', value)
        self.assertNotIn('current_lp_value', value)
        self.assertFalse(any(method.startswith(('eth_send', 'personal_', 'wallet_')) for method, _ in self.rpc.calls))

    def test_current_profiles_keep_canonical_inventory_during_optional_metadata_outage(self):
        for version in (3, 4):
            with self.subTest(version=version):
                p = self.projection(version)
                self.rpc.put(addr(21), 'decimals()', values=(6,))
                self.assert_inventory(p)
                self.rpc.responses[addr(21), calldata('decimals()')] = '0x01'
                self.assert_inventory(p)
                self.rpc.put(addr(21), 'decimals()', values=(6,))

    def test_token_runtime_or_decimals_change_does_not_invent_financial_values(self):
        p = self.projection()
        self.rpc.codes[addr(21)] = '0x6000'
        self.assert_inventory(p)
        self.rpc.codes[addr(21)] = '0x' + b'USDC'.hex()
        self.rpc.put(addr(21), 'decimals()', values=(18,))
        self.assert_inventory(p)

    def test_optional_token_rpc_failure_is_isolated_but_work_limit_is_not(self):
        p = self.projection()
        original = self.rpc.call
        def fail(error):
            def call(method, params):
                if method == 'eth_call' and params[0]['to'] == addr(21):
                    raise error
                return original(method, params)
            return call
        with patch.object(self.rpc, 'call', side_effect=fail(RpcError('Synthetic token outage'))):
            self.assert_inventory(p)
        with patch.object(self.rpc, 'call', side_effect=fail(WorkLimit('rpc_budget'))):
            with self.assertRaises(WorkLimit):
                p.wallet(addr(30))

    def test_changed_admitted_inventory_still_fails_closed(self):
        p = self.projection()
        self.rpc.put(addr(5), 'assets(uint256)', (1,), (addr(22),))
        with self.assertRaisesRegex(ProjectionError, 'allowlist'):
            p.wallet(addr(30))

    def test_required_module_fault_still_fails_before_optional_metadata(self):
        p = self.projection()
        self.rpc.codes[addr(3)] = '0x6000'
        self.rpc.responses[addr(21), calldata('decimals()')] = '0x01'
        with self.assertRaisesRegex(ProjectionError, 'Runtime code'):
            p.wallet(addr(30))

    def test_inventory_owner_and_canonical_finish_remain_strict(self):
        p = self.projection()
        self.rpc.put(addr(2), 'ownerOf(uint256)', (self.rpc.nft_id,), (addr(31),))
        with self.assertRaisesRegex(HistoryError, 'canonical wallet'):
            p.wallet(addr(30))
        self.rpc.put(addr(2), 'ownerOf(uint256)', (self.rpc.nft_id,), (addr(30),))
        original = self.rpc.call
        def lose_depth(method, params):
            value = original(method, params)
            if method == 'eth_call' and params[0]['data'] == calldata('ownerOf(uint256)', self.rpc.nft_id):
                self.rpc.head = 99
            return value
        with patch.object(self.rpc, 'call', side_effect=lose_depth):
            with self.assertRaisesRegex(ProjectionError, 'confirmation depth'):
                p.wallet(addr(30))

    def test_zero_holdings_are_verified_during_optional_outage(self):
        p = self.projection(4)
        self.rpc.responses[addr(21), calldata('decimals()')] = '0x01'
        value = p.wallet(addr(32))
        self.assertEqual(value['count'], 0)
        self.assertEqual(value['token_ids'], [])
        self.assertTrue(value['available'])


if __name__ == '__main__':
    unittest.main()
