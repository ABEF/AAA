"""Independent signed-fee and durable-budget regression vectors.

The RPC is a deterministic inclusion transcript, not a signer or a provider
qualification. Assertions compare canonical arithmetic and unchanged recovery
bytes instead of deriving expected cost from the implementation under test.
"""
import copy
import datetime as dt
import tempfile
import time
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python.test_keeper import A, B, H, FakeRpc
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class InclusionTranscript:
    def __init__(self):
        self.now = int(time.time())
        self.receipt = {'transactionHash': H, 'blockNumber': '0x63', 'blockHash': H,
            'transactionIndex': '0x0', 'from': A, 'to': B, 'status': '0x1',
            'gasUsed': '0x64', 'effectiveGasPrice': '0x63'}
        self.tx = {'hash': H, 'from': A, 'to': B, 'nonce': '0x7',
            'input': calldata('collectFees(uint256,uint256)', 1, 123), 'value': '0xa',
            'blockNumber': '0x63', 'blockHash': H, 'transactionIndex': '0x0',
            'gas': '0x100', 'type': '0x2', 'chainId': '0x1',
            'maxFeePerGas': '0xa', 'maxPriorityFeePerGas': '0x2'}

    def call(self, method, params):
        if method == 'eth_getTransactionReceipt': return self.receipt
        if method == 'eth_getTransactionByHash': return self.tx
        if method == 'eth_getBlockByNumber':
            return {'number': '0x64' if params[0] == 'latest' else params[0],
                    'timestamp': hex(self.now), 'hash': H, 'baseFeePerGas': '0x3'}
        raise AssertionError(method)


class KeeperSignedFeeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.rpc = InclusionTranscript()
        self.cfg = {'chain_id': 1, 'sender': A,
            'contracts': {k: B for k in ('access','vault','strategy','fees','compounder','buyback','pools')},
            'state_path': str(Path(self.tmp.name) / 'state.json'), 'confirmations': 2,
            'receipt_fee_policy': 'included', 'max_gas_limit': 100000,
            'max_gas_price_wei': 100, 'max_transaction_cost_wei': 1000000,
            'max_daily_cost_wei': 10000000}
        self.k = Keeper(self.cfg, rpc=self.rpc)
        self.review = {'schema': 1, 'gas_limit': 256, 'max_fee_per_gas': 10,
                       'l1_fee_allowance_wei': 0, 'maximum_cost_wei': 2570,
                       'receipt_fee_policy': 'included'}
        self.k.state.update(next_nonce=7, pending={'key': 'harvest:1', 'nonce': 7,
            'to': B, 'data': self.rpc.tx['input'], 'value': 10, 'day': '2026-10-14',
            'hash': H, 'fee_review': copy.deepcopy(self.review)})
        self.k.save()
        quiet = patch('keeper.monitor.log'); quiet.start(); self.addCleanup(quiet.stop)

    def reject_without_mutation(self):
        before = self.k.path.read_bytes(); state = copy.deepcopy(self.k.state)
        with self.assertRaises(RpcError): self.k.poll_pending()
        self.assertEqual(self.k.path.read_bytes(), before)
        self.assertEqual(self.k.state, state)

    def test_dynamic_reported_price_is_not_actual_cost(self):
        self.assertFalse(self.k.poll_pending())
        day = dt.datetime.fromtimestamp(self.rpc.now, dt.timezone.utc).date().isoformat()
        # min(10, 3+2) * 100 gas + 10 value. Reported 99 is not signed truth.
        self.assertEqual(self.k.state['spent'][day], 510)

    def test_dynamic_fee_cap_binds_canonical_base_fee(self):
        self.rpc.tx['maxPriorityFeePerGas'] = '0x9'
        self.assertFalse(self.k.poll_pending())
        day = dt.datetime.fromtimestamp(self.rpc.now, dt.timezone.utc).date().isoformat()
        self.assertEqual(self.k.state['spent'][day], 1010)

    def test_signed_chain_does_not_inherit_rpc_chain(self):
        self.rpc.tx['chainId'] = '0x2'; self.reject_without_mutation()

    def test_typed_missing_chain_id_is_not_inferred(self):
        self.rpc.tx.pop('chainId'); self.reject_without_mutation()

    def test_changed_gas_or_fee_review_keeps_pending(self):
        for field, value in (('gas', '0x101'), ('maxFeePerGas', '0xb')):
            original = copy.deepcopy(self.rpc.tx)
            self.rpc.tx[field] = value
            with self.subTest(field=field): self.reject_without_mutation()
            self.rpc.tx = original

    def test_base_fee_above_signed_cap_is_rejected(self):
        original = self.rpc.call
        def call(method, params):
            value = original(method, params)
            return {**value, 'baseFeePerGas': '0xb'} if method == 'eth_getBlockByNumber' else value
        self.rpc.call = call
        self.reject_without_mutation()

    def test_invalid_priority_or_unknown_type_is_rejected(self):
        for field, value in (('maxPriorityFeePerGas','0xb'), ('type','0x3')):
            original = copy.deepcopy(self.rpc.tx); self.rpc.tx[field] = value
            with self.subTest(field=field): self.reject_without_mutation()
            self.rpc.tx = original

    def test_legacy_pending_review_is_not_invented(self):
        self.k.state['pending'].pop('fee_review'); self.k.save()
        with patch('keeper.monitor.log') as logger:
            self.reject_without_mutation()
        logger.assert_called_once_with('pending_fee_review_required',
            operator_action='preserve_and_review_original_evidence_never_resend')

    def test_separate_l1_fee_cannot_exceed_captured_allowance(self):
        self.k.fee_policy = 'separate_l1_fee'
        self.k.state['pending']['fee_review'].update(receipt_fee_policy='separate_l1_fee',
            l1_fee_allowance_wei=7, maximum_cost_wei=2577)
        self.k.save(); self.rpc.receipt['l1Fee'] = '0x8'
        self.reject_without_mutation()

    def test_budget_policy_change_does_not_reinterpret_pending(self):
        self.k.fee_policy = 'separate_l1_fee'; self.rpc.receipt['l1Fee'] = '0x1'
        self.reject_without_mutation()

    def test_reorg_during_last_read_preserves_fee_budget(self):
        original = self.rpc.call; seen = 0
        def call(method, params):
            nonlocal seen
            result = original(method, params)
            if method == 'eth_getBlockByNumber' and params[0] == '0x63':
                seen += 1
                if seen > 1: return {**result, 'hash': '0x' + 'cd' * 32}
            return result
        self.rpc.call = call
        self.reject_without_mutation()

    def test_revert_charges_gas_once_without_native_value(self):
        self.rpc.receipt['status'] = '0x0'
        self.assertFalse(self.k.poll_pending())
        day = dt.datetime.fromtimestamp(self.rpc.now, dt.timezone.utc).date().isoformat()
        self.assertEqual(self.k.state['spent'][day], 500)
        self.assertFalse(self.k.poll_pending())
        self.assertEqual(self.k.state['spent'][day], 500)

    def test_legacy_price_must_match_signed_gas_price(self):
        self.rpc.tx.update(type='0x0', gasPrice='0xa', v='0x25')
        self.reject_without_mutation()

    def test_pending_cost_ceiling_cannot_be_malformed(self):
        self.k.state['pending']['fee_review']['maximum_cost_wei'] += 1
        self.k.save(); self.reject_without_mutation()

    def test_final_canonical_base_fee_change_is_rejected(self):
        original = self.rpc.call; seen = 0
        def call(method, params):
            nonlocal seen
            result = original(method, params)
            if method == 'eth_getBlockByNumber' and params[0] == '0x63':
                seen += 1
                if seen > 1: return {**result, 'baseFeePerGas':'0x4'}
            return result
        self.rpc.call = call
        self.reject_without_mutation()

    def test_original_fee_policy_survives_current_config_change(self):
        self.k.fee_policy = 'separate_l1_fee'
        self.cfg.update(max_gas_price_wei=1, max_transaction_cost_wei=1)
        # Reconcile what was actually reviewed/sent, never reinterpret it using
        # a later lower limit. New submissions independently use current caps.
        self.assertFalse(self.k.poll_pending())
        self.assertEqual(self.k.state['last_fee_observation']['execution_price_wei'],5)

    def test_submit_saves_fee_review_before_external_signer(self):
        self.k.state['pending'] = None
        self.k.state['receipt_anchor'] = {'number':98,'hash':H,'timestamp':self.rpc.now,'nonce':6}
        self.k.rpc = FakeRpc(); self.k.live = True
        self.k.cast = '/mock/cast'; self.k.keystore = Path('/mock/key'); self.k.password = Path('/mock/pass')
        self.k._validate_code_hashes = lambda: None
        def sign(*args,**kwargs):
            saved = __import__('json').loads(self.k.path.read_text())['pending']
            self.assertEqual(saved['fee_review'], {'schema':1,'gas_limit':125,'max_fee_per_gas':2,
                'l1_fee_allowance_wei':0,'maximum_cost_wei':250,'receipt_fee_policy':'included'})
            return subprocess.CompletedProcess(args[0],0,H,'')
        with patch('keeper.monitor.subprocess.run',side_effect=sign):
            self.assertTrue(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'harvest:1'))
