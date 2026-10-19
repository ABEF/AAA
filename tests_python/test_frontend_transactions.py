"""Unsigned wallet actions: exact intent, no signing, one canonical snapshot."""
import copy
import json
from pathlib import Path
import unittest

from frontend_api.service import Projection, ProjectionError, UnknownNFT, ZERO
from frontend_api.transactions import Transactions, TransactionInputError, MINT_PRICE, Claim, claim_calldata
from tests_python.test_frontend_api import MockRPC, configuration, addr, words
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError
from zzz_ops.errors import WorkLimit


def transaction_config(projection):
    return {'schema': 1, 'chain_id': projection.chain, 'projection_sha256': projection.identity,
            'fee_policy': {'estimate_includes_all_fees': True, 'review_hash': '0x'+'9'*64,
                           'max_gas_price_wei': '10000000000', 'max_network_fee_wei': '10000000000000000'}}


class TransactionRPC(MockRPC):
    def __init__(self):
        super().__init__()
        self.simulations = []
        self.simulated = None
        self.simulation_error = False
        self.after_simulation = None
        self.estimate = 100000
        self.gas_price = 1000000000
        self.native_balance = 10**18
        self.put(addr(1), 'paused()', values=(0,))
        self.put(addr(3), 'MINT_PRICE()', values=(MINT_PRICE,))
        self.put(addr(2), 'MAX_SUPPLY()', values=(1000,))
        self.put(addr(2), 'mintedCount()', values=(1,))

    def call(self, method, params):
        if method in ('eth_estimateGas', 'eth_gasPrice', 'eth_getBalance'):
            self.calls.append((method, copy.deepcopy(params)))
            if method != 'eth_gasPrice':
                if params[-1] != {'blockHash': self.hash, 'requireCanonical': True}:
                    raise RpcError('Canonical hash is no longer available')
            if method == 'eth_estimateGas':
                assert params[0] == self.simulations[-1][0]
            return hex({'eth_estimateGas': self.estimate, 'eth_gasPrice': self.gas_price,
                        'eth_getBalance': self.native_balance}[method])
        if method == 'eth_call' and 'from' in params[0]:
            self.calls.append((method, copy.deepcopy(params)))
            self.simulations.append(copy.deepcopy(params))
            if self.fail_hash_pin or params[1] != {'blockHash': self.hash, 'requireCanonical': True}:
                raise RpcError('No canonical hash support')
            tx = params[0]
            assert set(tx) == {'from', 'to', 'data', 'value', 'gas'}
            if self.simulation_error:
                raise RpcError('Simulated contract reverted')
            if self.after_simulation:
                self.after_simulation()
            if self.simulated is not None:
                return self.simulated
            if tx['to'] == addr(3):
                assert tx['data'] == calldata('mintDormant()') and tx['value'] == hex(MINT_PRICE)
                return words(self.nft_id)
            assert tx['to'] == addr(6) and tx['value'] == '0x0'
            raw = tx['data'][10:]
            assert int(raw[:64], 16) == 32
            count = int(raw[64:128], 16)
            assert len(raw) == 128 + count * 192
            return words(32, count, *(10**22 + i for i in range(count)))
        return super().call(method, params)


class FrontendTransactionTests(unittest.TestCase):
    def setUp(self):
        self.rpc = TransactionRPC()
        self.now = 1000
        self.p = Projection(configuration(), self.rpc, clock=lambda: self.now)
        self.service = Transactions(self.p, transaction_config(self.p))

    def mint(self, **overrides):
        return self.service.prepare({'action': 'mint', 'wallet': addr(30), **overrides})

    def entry(self, *, royalty=False, asset=None, identifier=None):
        return {'token_id': str(self.rpc.nft_id if identifier is None else identifier),
                'asset': asset or addr(21), 'royalty': royalty}

    def claim(self, entries=None, **overrides):
        return self.service.prepare({'action': 'claim', 'wallet': addr(30),
                                     'claims': entries if entries is not None else [self.entry()], **overrides})

    def test_mint_exact_target_value_chain_and_simulation_no_reserved_identity(self):
        r = self.mint()
        self.assertEqual(r['transaction'], {'from': addr(30), 'to': addr(3), 'data': calldata('mintDormant()'),
                                          'value': hex(50_000_000_000_000_000), 'chainId': hex(31337)})
        self.assertEqual(r['expires_at'], 1060)
        self.assertEqual(r['claim_operations'], [])
        self.assertNotIn('token_id', r)
        self.assertTrue(r['wallet_revalidation_required'])
        self.assertFalse(r['approvals_required'])
        self.assertNotIn('gas', r['transaction'])
        self.assertNotIn('nonce', r['transaction'])
        self.assertEqual(r['simulation']['gas_estimate'], '100000')
        self.assertEqual(self.rpc.simulations[0][0]['gas'], hex(12_000_000))

    def test_mixed_lp_erc20_and_native_royalty_same_nft_and_asset_allowed(self):
        entries = [self.entry(), self.entry(royalty=True), self.entry(royalty=True, asset=ZERO)]
        r = self.claim(entries)
        self.assertEqual(r['transaction']['value'], '0x0')
        self.assertEqual(r['transaction']['to'], addr(6))
        self.assertEqual([x['view_raw'] for x in r['claim_operations']], ['1234567', '25000001', '33333333333333333333'])
        self.assertEqual([x['simulated_raw'] for x in r['claim_operations']], [str(10**22+i) for i in range(3)])
        self.assertEqual([x['decimals'] for x in r['claim_operations']], [6, 6, 18])
        self.assertEqual(r['transaction']['data'], claim_calldata(tuple(Claim(int(e['token_id']), e['asset'], e['royalty']) for e in entries)))
        self.assertNotIn('total', r)

    def test_duplicate_and_more_than_32_rejected_before_rpc(self):
        for entries in ([], [self.entry(), self.entry()], [self.entry(identifier=i) for i in range(33)]):
            with self.subTest(entries=len(entries)), self.assertRaises(TransactionInputError):
                self.claim(entries)
        self.assertEqual(self.rpc.calls, [])

    def test_exact_32_distinct_nfts_are_one_simulation_in_input_order(self):
        entries = []
        for n in range(1, 33):
            identifier = 10**60 + n
            self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', (identifier,), (n,))
            self.rpc.put(addr(2), 'tokenAtOrdinal(uint256)', (n,), (identifier,))
            self.rpc.put(addr(2), 'ownerOf(uint256)', (identifier,), (addr(30),))
            self.rpc.put(addr(4), 'claimable(uint256,address)', (identifier, addr(21)), (n,))
            entries.append(self.entry(identifier=identifier))
        r = self.claim(entries)
        self.assertEqual(len(self.rpc.simulations), 1)
        self.assertEqual([x['token_id'] for x in r['claim_operations']], [e['token_id'] for e in entries])
        self.assertEqual(len(r['transaction']['data']), 10 + 64 * (2 + 32 * 3))

    def test_user_cannot_supply_call_target_value_chain_rpc_approval_or_recipient(self):
        for field in ('to', 'value', 'data', 'chainId', 'rpc_url', 'gas', 'nonce', 'recipient', 'approve', 'block', 'stateOverrides'):
            with self.subTest(field=field), self.assertRaises(TransactionInputError):
                self.mint(**{field: addr(40)})
        for action in ('activate', 'increase', 'approve', 'claimFor', 'sendTransaction', None, []):
            with self.subTest(action=action), self.assertRaises(TransactionInputError):
                self.mint(action=action)
        self.assertFalse(self.rpc.calls)

    def test_claim_shape_requires_lossless_canonical_ids_and_boolean(self):
        invalid_ids = [1, True, 1.1, '01', '-1', '+1', '1e3', '0x1', str(1 << 256), '9'*1000]
        for identifier in invalid_ids:
            entry = {**self.entry(), 'token_id': identifier}
            with self.subTest(identifier=identifier), self.assertRaises(TransactionInputError):
                self.claim([entry])
        for flag in (0, 1, 'false', None):
            with self.subTest(flag=flag), self.assertRaises(TransactionInputError):
                self.claim([{**self.entry(), 'royalty': flag}])
        with self.assertRaises(TransactionInputError):
            self.claim([{**self.entry(), 'recipient': addr(40)}])
        self.assertFalse(self.rpc.calls)

    def test_bad_wallet_and_native_lp_rejected_before_rpc(self):
        for owner in (ZERO, None, '', '0x123', 30):
            with self.subTest(owner=owner), self.assertRaises(TransactionInputError):
                self.mint(wallet=owner)
        with self.assertRaises(TransactionInputError):
            self.claim([self.entry(asset=ZERO)])
        self.assertFalse(self.rpc.calls)

    def test_duplicate_addresses_normalized_before_detection(self):
        a = self.entry(asset=addr(20))
        a['asset'] = '0x' + a['asset'][2:].upper()
        with self.assertRaises(TransactionInputError):
            self.claim([a, self.entry(asset=addr(20))])

    def test_wrong_owner_or_approval_is_not_claim_authority(self):
        with self.assertRaises(TransactionInputError):
            self.claim(wallet=addr(31))
        self.assertFalse(self.rpc.simulations)

    def test_unknown_and_inconsistent_token_identity_rejected(self):
        self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', (self.rpc.nft_id,), (0,))
        with self.assertRaises(UnknownNFT):
            self.claim()
        self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', (self.rpc.nft_id,), (1001,))
        with self.assertRaises(ProjectionError):
            self.claim()
        self.assertFalse(self.rpc.simulations)

    def test_wrong_ledger_or_unfunded_selection_rejected(self):
        with self.assertRaises(TransactionInputError):
            self.claim([self.entry(royalty=True, asset=addr(20))])
        self.rpc.put(addr(4), 'claimable(uint256,address)', (self.rpc.nft_id, addr(21)), (0,))
        with self.assertRaises(TransactionInputError):
            self.claim()
        self.assertFalse(self.rpc.simulations)

    def test_paused_mint_rejected_but_claim_still_available(self):
        self.rpc.put(addr(1), 'paused()', values=(1,))
        with self.assertRaises(TransactionInputError):
            self.mint()
        self.assertEqual(self.claim()['action'], 'claim')

    def test_mint_cap_price_and_max_supply_checked_before_simulation(self):
        for target, method, value, error in ((3, 'MINT_PRICE()', 1, ProjectionError),
                                            (2, 'MAX_SUPPLY()', 1001, ProjectionError),
                                            (2, 'mintedCount()', 1000, TransactionInputError)):
            with self.subTest(method=method):
                self.setUp()
                self.rpc.put(addr(target), method, values=(value,))
                with self.assertRaises(error):
                    self.mint()
                self.assertFalse(self.rpc.simulations)

    def test_wrong_chain_and_code_pins_fail_without_simulation(self):
        self.rpc.chain = 1
        with self.assertRaises(ProjectionError):
            self.mint()
        self.rpc.chain = 31337
        self.rpc.codes[addr(6)] = '0x6000'
        with self.assertRaises(ProjectionError):
            self.claim()
        self.assertFalse(self.rpc.simulations)

    def test_simulation_revert_has_no_unsigned_success_result(self):
        self.rpc.simulation_error = True
        with self.assertRaises(RpcError):
            self.mint()
        with self.assertRaises(RpcError):
            self.claim()

    def test_reorg_during_simulation_and_unsupported_hash_fail_closed(self):
        self.rpc.after_simulation = lambda: setattr(self.rpc, 'hash', '0x'+'c'*64)
        with self.assertRaises(RpcError):
            self.claim()
        self.setUp()
        self.rpc.fail_hash_pin = True
        with self.assertRaises(RpcError):
            self.mint()

    def test_slow_simulation_cannot_publish_expired_draft(self):
        self.rpc.after_simulation = lambda: setattr(self, 'now', 1111)
        with self.assertRaises(WorkLimit):
            self.claim()

    def test_preparation_age_stricter_than_relaxed_projection_age(self):
        self.p.max_age = 86400
        self.now = 1111
        with self.assertRaises(ProjectionError):
            self.mint()
        self.assertFalse(self.rpc.simulations)

    def test_expiry_never_extends_source_freshness(self):
        self.now = 1080
        self.assertEqual(self.claim()['expires_at'], 1110)
        self.now = 1110
        with self.assertRaises(WorkLimit):
            self.claim()

    def test_malformed_or_wrong_length_simulation_result_rejected(self):
        for raw in ('0x', words(64, 1, 10), words(32, 2, 10), words(32, 1, 10, 99), words(32, 1, 0), '0x'+'g'*192):
            with self.subTest(raw=raw):
                self.rpc.simulated = raw
                with self.assertRaises(ProjectionError):
                    self.claim()
        self.rpc.simulated = words(1, 2)
        with self.assertRaises(ProjectionError):
            self.mint()

    def test_each_state_read_and_simulation_same_hash_no_write_rpc(self):
        r = self.claim([self.entry(), self.entry(royalty=True, asset=ZERO)])
        for method, params in self.rpc.calls:
            self.assertNotIn('sign', method.lower())
            self.assertNotIn('send', method.lower())
            if method in ('eth_call', 'eth_getCode'):
                self.assertEqual(params[-1], {'blockHash': self.rpc.hash, 'requireCanonical': True})
        self.assertFalse(r['provenance']['protocol_finalized'])
        self.assertEqual(r['provenance']['configuration_sha256'], self.p.identity)

    def test_matches_independently_compiled_solidity_abi_vectors(self):
        # These frozen vectors were checked against the actual router using
        # Solidity abi.encodeCall in a separately compiled Foundry fixture.
        vectors = json.loads((Path(__file__).parent / 'fixtures/claim-calldata.json').read_text())
        asset = '0x1234567890abcdef1234567890abcdef12345678'
        samples = {
            'OneClaim': (Claim((1 << 256)-1, asset, False),),
            'MixedThree': (Claim(444, asset, False), Claim(444, asset, True), Claim(2, ZERO, True)),
            'Maximum32': tuple(Claim((1 << 255)+i, ZERO if i % 3 == 0 else asset, i % 3 != 1) for i in range(32)),
        }
        for name, entries in samples.items():
            with self.subTest(name=name):
                actual = claim_calldata(entries)
                self.assertEqual(actual, vectors[name]['hex'])
                self.assertEqual((len(actual)-2)//2, vectors[name]['bytes'])


if __name__ == '__main__':
    unittest.main()
