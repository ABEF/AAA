"""Source-level browser RPC boundaries only; no network, EVM or DTO fixtures."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('source9_rehearsal_api_boundary',
    ROOT / 'scripts' / 'source9_rehearsal_api.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)


class Source9RehearsalBrowserBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.block = dict(blockHash='0x' + 'ab' * 32, requireCanonical=True)
        self.owner = '0x' + '11' * 20
        self.target = '0x' + '22' * 20
        self.tx = {'from': self.owner, 'to': self.target, 'data': '0x12345678',
                   'value': '0x0', 'gas': '0xb71b00'}

    def valid(self, method, params):
        self.assertTrue(API._browser_params(method, params), method)

    def invalid(self, method, params):
        self.assertFalse(API._browser_params(method, params), method)

    def test_ordinary_source9_public_reads_and_exact_simulations_are_admitted(self):
        for method in ('eth_chainId', 'eth_blockNumber', 'eth_gasPrice'):
            with self.subTest(method=method):
                self.valid(method, [])
        self.valid('eth_getBlockByNumber', ['0x0', False])
        self.valid('eth_getBlockByNumber', ['0x1234', False])
        self.valid('eth_getCode', [self.target, self.block])
        self.valid('eth_getBalance', [self.owner, self.block])
        self.valid('eth_call', [{'to': self.target, 'data': '0x313ce567'}, self.block])
        self.valid('eth_call', [self.tx, self.block])
        self.valid('eth_estimateGas', [self.tx, self.block])

    def test_state_override_parameters_never_reach_the_reader(self):
        override = {self.owner: {'balance': '0xffff'}}
        for method in ('eth_call', 'eth_estimateGas'):
            with self.subTest(method=method):
                self.invalid(method, [self.tx, self.block, override])
                self.invalid(method, [self.tx, self.block, override, {}])

    def test_nonce_fields_are_rejected_from_call_and_estimate(self):
        for method in ('eth_call', 'eth_estimateGas'):
            for nonce in ('0x0', '0x1', 0, None):
                with self.subTest(method=method, nonce=nonce):
                    self.invalid(method, [{**self.tx, 'nonce': nonce}, self.block])

    def test_state_reads_require_the_exact_canonical_hash_object(self):
        blocks = (None, {}, {'blockHash': self.block['blockHash']},
            {**self.block, 'requireCanonical': False},
            {**self.block, 'requireCanonical': 1},
            {**self.block, 'blockHash': '0x1234'},
            {**self.block, 'blockNumber': '0x1'})
        for block in blocks:
            for method, first in (('eth_call', self.tx), ('eth_estimateGas', self.tx),
                    ('eth_getCode', self.target), ('eth_getBalance', self.owner)):
                with self.subTest(method=method, block=block):
                    self.invalid(method, [first, block])

    def test_latest_pending_and_number_selected_state_reads_are_rejected(self):
        for block in ('latest', 'pending', 'safe', 'finalized', '0x1234', 1234):
            for method, first in (('eth_call', self.tx), ('eth_estimateGas', self.tx),
                    ('eth_getCode', self.target), ('eth_getBalance', self.owner)):
                with self.subTest(method=method, block=block):
                    self.invalid(method, [first, block])

    def test_wrong_arity_cannot_add_arguments_or_drop_snapshot_pins(self):
        for method in ('eth_chainId', 'eth_blockNumber', 'eth_gasPrice'):
            with self.subTest(method=method):
                self.invalid(method, ['latest'])
        for method, first in (('eth_call', self.tx), ('eth_estimateGas', self.tx),
                ('eth_getCode', self.target), ('eth_getBalance', self.owner)):
            for params in ([], [first], [first, self.block, {}]):
                with self.subTest(method=method, count=len(params)):
                    self.invalid(method, params)

    def test_wallet_submission_signing_nonce_and_debug_methods_are_unavailable(self):
        methods = ('eth_sendTransaction', 'eth_sendRawTransaction', 'eth_sign',
            'eth_signTransaction', 'personal_sign', 'eth_requestAccounts',
            'eth_accounts', 'eth_getTransactionCount', 'debug_traceCall', 'anvil_setCode')
        for method in methods:
            with self.subTest(method=method):
                self.assertNotIn(method, API.BROWSER_METHODS)
                self.invalid(method, [self.tx, self.block])

    def test_block_headers_cannot_request_transactions_or_noncanonical_numbers(self):
        params = ([], ['0x1'], ['0x1', True], ['0x1', False, {}],
            ['0x00', False], ['0x01', False], ['pending', False], [1, False])
        for value in params:
            with self.subTest(params=value):
                self.invalid('eth_getBlockByNumber', value)

    def test_unexpected_transaction_fields_and_malformed_targets_are_rejected(self):
        transactions = ({**self.tx, 'stateOverride': {}}, {**self.tx, 'blockOverrides': {}},
            {**self.tx, 'to': None}, {**self.tx, 'to': '0x1234'},
            {**self.tx, 'data': None}, {**self.tx, 'data': '0x123'},
            {'to': self.target, 'input': self.tx['data']},
            {key: value for key, value in self.tx.items() if key != 'to'})
        for tx in transactions:
            for method in ('eth_call', 'eth_estimateGas'):
                with self.subTest(method=method, tx=tx):
                    self.invalid(method, [tx, self.block])


class Source9RehearsalActivationPolicyTests(unittest.TestCase):
    def test_default_keeps_schema_one_twelve_million_and_no_new_wire_fields(self):
        self.assertEqual(dict(schema=1,limit=12000000,fee_fields={},manifest_fields={}),
            API._activation_gas_policy(None))

    def test_explicit_reviewed_limit_selects_only_activation_policy_two(self):
        for value in (16000000,'16000000',21000,'64000000'):
            with self.subTest(value=value):
                actual=API._activation_gas_policy(value)
                self.assertEqual(2,actual['schema']);self.assertEqual(int(value),actual['limit'])
                self.assertEqual({'activation_policy_schema':2},actual['manifest_fields'])
                self.assertEqual(str(int(value)),actual['fee_fields']['max_gas_limit'])
                self.assertEqual(str(10**18),actual['fee_fields']['max_network_fee_wei'])
                self.assertEqual(1,API.PROFILE['transaction_policy_schema'])

    def test_invalid_opt_in_cannot_widen_or_silently_use_the_default(self):
        for value in (False,True,0,20999,64000001,'016000000','0x1000000',16e6,'',None.__class__):
            with self.subTest(value=value),self.assertRaises(ValueError):
                API._activation_gas_policy(value)


if __name__ == '__main__':
    unittest.main()
