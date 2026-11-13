"""Future-only zero-tip fee profile: inert signer and captured read-only data.

Imported classes provide setup helpers only; none of their old methods run.
The actual receipt retains its real fields. Its keeper journal is an explicit
test construction, never a claim that PoPL submitted that public transaction.
"""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper as basic
from tests_python import test_keeper_fees as fee_fixtures
from zzz_ops.rpc import RpcError

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'eip1559_zero_tip'


class KeeperZeroTipProfileTests(unittest.TestCase):
    def submission(self, profile=2):
        fixture = basic.KeeperTests('runTest')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.enable_test_signer()
        k, rpc, cfg = fixture.k, fixture.rpc, fixture.cfg
        cfg.update(chain_id=4663, receipt_fee_policy='included', l1_fee_allowance_wei=0)
        k.chain = 4663; k.state['chain_id'] = 4663
        if profile is not None: cfg['submission_fee_profile'] = profile
        k._validate_accounting_version = lambda: None
        k._validate_checkpoint = lambda: None
        k._defer_for_lifecycle = lambda *_: False
        return k, rpc, cfg

    def pending(self, schema=2):
        fixture = fee_fixtures.KeeperSignedFeeTests('runTest')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        k, rpc = fixture.k, fixture.rpc
        k.chain = 4663; k.config.update(chain_id=4663, submission_fee_profile=2)
        k.state['chain_id'] = 4663
        rpc.tx.update(chainId=hex(4663), maxPriorityFeePerGas='0x0')
        rpc.receipt['effectiveGasPrice'] = '0x3'
        if schema == 2:
            k.state['pending']['fee_review'].update(schema=2, execution_fee_model=MODEL)
        k.save()
        return k, rpc

    def rejected_without_change(self, k):
        state, raw = copy.deepcopy(k.state), k.path.read_bytes()
        with self.assertRaises(RpcError): k.poll_pending()
        self.assertEqual(k.state, state); self.assertEqual(k.path.read_bytes(), raw)

    @staticmethod
    def submit(k, rpc):
        return k.submit('vault', 'collectFees(uint256,uint256)', (1, rpc.now+180), 'qualification:harvest')

    def test_profile2_is_explicit_strict_and_robinhood_inclusive_only(self):
        k, rpc, cfg = self.submission()
        self.assertEqual(k._submission_fee_profile(), 2)
        for changes in ({'submission_fee_profile': True}, {'submission_fee_profile': '2'},
                {'submission_fee_profile': 2.0}, {'submission_fee_profile': 0},
                {'submission_fee_profile': 3}, {'receipt_fee_policy': 'separate_l1_fee'},
                {'receipt_fee_policy': 'unverified'}, {'l1_fee_allowance_wei': 1}, {'chain_id': 1}):
            fresh = {**cfg, **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError): Keeper(fresh, rpc=rpc)

    def test_profile2_persists_exact_review_before_mock_signer_and_fixes_fee_envelope(self):
        k, rpc, cfg = self.submission(); before = copy.deepcopy(k.state['spent'])
        def sign(command, **kwargs):
            pending = json.loads(k.path.read_text())['pending']
            self.assertEqual(pending['fee_review'], dict(schema=2, gas_limit=125, max_fee_per_gas=2,
                l1_fee_allowance_wei=0, maximum_cost_wei=250, receipt_fee_policy='included', execution_fee_model=MODEL))
            self.assertIsNone(pending['hash'])
            self.assertEqual(command[command.index('--gas-price')+1], '2')
            self.assertEqual(command[command.index('--priority-gas-price')+1], '0')
            self.assertEqual(command.count('--priority-gas-price'), 1)
            self.assertNotIn('--legacy', command)
            self.assertNotIn('ETH_PRIORITY_GAS_PRICE', kwargs['env'])
            self.assertNotIn('ETH_LEGACY', kwargs['env'])
            return subprocess.CompletedProcess(command, 0, basic.H, '')
        with patch.dict(os.environ, {'ETH_PRIORITY_GAS_PRICE': '99', 'ETH_LEGACY': 'true'}), \
                patch('keeper.monitor.subprocess.run', side_effect=sign) as signer:
            self.assertTrue(self.submit(k, rpc))
        signer.assert_called_once(); self.assertEqual(k.state['spent'], before)
        self.assertEqual(sum(m == 'eth_gasPrice' for m, _ in rpc.calls), 1)
        actions = [(m, p) for m, p in rpc.calls if m == 'eth_estimateGas' or m == 'eth_call' and 'from' in p[0]]
        self.assertEqual([m for m, _ in actions], ['eth_call', 'eth_estimateGas'])
        for _, params in actions:
            self.assertEqual({name: params[0][name] for name in ('type', 'maxFeePerGas', 'maxPriorityFeePerGas')},
                dict(type='0x2', maxFeePerGas='0x2', maxPriorityFeePerGas='0x0'))
            self.assertNotIn('gasPrice', params[0]); self.assertEqual(params[0]['gas'], hex(cfg['max_gas_limit']))

    def test_profile2_final_rebalance_and_compound_use_the_same_frozen_dynamic_envelope(self):
        for name, signature in (('vault', 'rebalance(uint256,uint128,uint256)'),
                ('compounder', 'compound(uint256,uint128,uint256)')):
            with self.subTest(action=name):
                k, rpc, _ = self.submission()
                k._validate_lp_routing = lambda **_: None
                k._rebalance_submission_ready = lambda _: True
                k._compound_submission_ready = lambda _: True
                with patch('keeper.monitor.subprocess.run', return_value=subprocess.CompletedProcess([], 0, basic.H, '')):
                    self.assertTrue(k.submit(name, signature, (1, 1, rpc.now+180), 'qualification:'+name))
                calls = [p[0] for m, p in rpc.calls if m == 'eth_call' and 'from' in p[0]]
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[1], {**calls[0], 'gas': hex(125)})
                self.assertNotIn('gasPrice', calls[1])
                self.assertEqual(calls[1]['maxPriorityFeePerGas'], '0x0')

    def test_omitted_and_explicit_profile1_keep_original_order_command_and_schema(self):
        for profile in (None, 1):
            with self.subTest(profile=profile):
                k, rpc, _ = self.submission(profile)
                with patch('keeper.monitor.subprocess.run', return_value=subprocess.CompletedProcess([], 0, basic.H, '')) as signer:
                    self.assertTrue(self.submit(k, rpc))
                self.assertNotIn('--priority-gas-price', signer.call_args.args[0])
                self.assertEqual(k.state['pending']['fee_review']['schema'], 1)
                self.assertNotIn('execution_fee_model', k.state['pending']['fee_review'])
                methods = [m for m, _ in rpc.calls]
                self.assertLess(methods.index('eth_estimateGas'), methods.index('eth_gasPrice'))
                for m, p in rpc.calls:
                    if m == 'eth_estimateGas' or m == 'eth_call' and 'from' in p[0]:
                        self.assertNotIn('maxFeePerGas', p[0]); self.assertNotIn('type', p[0])

    def test_schema2_rejects_nonzero_priority_legacy_wrong_chain_and_missing_priority(self):
        for changes in ({'maxPriorityFeePerGas': '0x1'}, {'type': '0x0', 'gasPrice': '0xa', 'v': hex(4663*2+35)},
                {'type': '0x1', 'gasPrice': '0xa'}, {'chainId': '0x1'}, {'maxPriorityFeePerGas': None}):
            k, rpc = self.pending(); rpc.tx.update(changes)
            with self.subTest(changes=changes): self.rejected_without_change(k)

    def test_schema2_review_is_exact_and_cannot_enable_separate_fees_or_unknown_models(self):
        for changes in ({'execution_fee_model': 'ethereum'}, {'execution_fee_model': None},
                {'receipt_fee_policy': 'separate_l1_fee'}, {'l1_fee_allowance_wei': 1, 'maximum_cost_wei': 2571},
                {'max_fee_per_gas': 0, 'maximum_cost_wei': 10}, {'schema': True}, {'schema': 3}, {'extra': 0}):
            k, _ = self.pending(); k.state['pending']['fee_review'].update(changes); k.save()
            with self.subTest(changes=changes): self.rejected_without_change(k)

    def test_schema1_pending_is_not_reinterpreted_when_future_profile2_is_configured(self):
        k, rpc = self.pending(schema=1)
        rpc.tx['maxPriorityFeePerGas'] = '0x2'
        original = copy.deepcopy(k.state['pending']['fee_review'])
        self.assertFalse(k.poll_pending())
        self.assertEqual(original['schema'], 1)
        self.assertEqual(k.state['last_fee_observation']['execution_price_wei'], 5)
        self.assertEqual(k.state['spent'][dt.datetime.fromtimestamp(rpc.now, dt.timezone.utc).date().isoformat()], 510)

    def test_schema2_recovery_uses_saved_model_even_with_invalid_future_settings(self):
        k, rpc = self.pending(); review = copy.deepcopy(k.state['pending']['fee_review'])
        k.config.update(submission_fee_profile='invalid future profile', l1_fee_allowance_wei=99)
        reloaded = Keeper(k.config, rpc=rpc)
        self.assertEqual(reloaded.state['pending']['fee_review'], review)
        self.assertFalse(reloaded.poll_pending())
        self.assertEqual(reloaded.state['last_fee_observation']['execution_price_wei'], 3)

    def test_schema2_bad_receipt_price_or_canonical_cap_preserves_journal(self):
        for reported in ('0x2', '0x4', None):
            k, rpc = self.pending(); rpc.receipt['effectiveGasPrice'] = reported
            with self.subTest(price=reported): self.rejected_without_change(k)
        k, rpc = self.pending(); original = rpc.call
        rpc.call = lambda m, p: {**original(m, p), 'baseFeePerGas': '0xb'} if m == 'eth_getBlockByNumber' else original(m, p)
        self.rejected_without_change(k)

    def test_provider_upfront_full_cap_funding_failure_does_not_sign_or_widen(self):
        k, rpc, _ = self.submission(); original = rpc.call; before = copy.deepcopy(k.state)
        def unavailable(method, params):
            if method == 'eth_estimateGas': raise RpcError('insufficient funds for the full simulated fee envelope')
            return original(method, params)
        rpc.call = unavailable
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(RpcError): self.submit(k, rpc)
            signer.assert_not_called()
        self.assertEqual(k.state, before); self.assertFalse(k.path.exists())
        self.assertEqual(sum(m == 'eth_gasPrice' for m, _ in rpc.calls), 1)

    def test_new_profile_keeps_original_gas_price_transaction_and_daily_caps(self):
        for field, value in (('max_gas_limit', 124), ('max_gas_price_wei', 1),
                ('max_transaction_cost_wei', 249), ('max_daily_cost_wei', 249)):
            k, rpc, cfg = self.submission(); cfg[field] = value; before = copy.deepcopy(k.state)
            with self.subTest(field=field), patch('keeper.monitor.subprocess.run') as signer:
                self.assertFalse(self.submit(k, rpc)); signer.assert_not_called()
            self.assertEqual(k.state, before); self.assertFalse(k.path.exists())

    def test_signer_failure_keeps_schema2_intent_and_never_resends(self):
        k, rpc, _ = self.submission()
        with patch('keeper.monitor.subprocess.run', side_effect=subprocess.TimeoutExpired('/mock/cast', 90)) as signer:
            with self.assertRaises(subprocess.TimeoutExpired): self.submit(k, rpc)
            raw = k.path.read_bytes(); pending = copy.deepcopy(k.state['pending'])
            self.assertEqual(pending['fee_review']['schema'], 2); self.assertIsNone(pending['hash'])
            k.config['submission_fee_profile'] = 'invalid future setting'
            self.assertFalse(self.submit(k, rpc)); self.assertEqual(signer.call_count, 1)
            self.assertEqual(k.path.read_bytes(), raw); self.assertEqual(k.state['pending'], pending)

    def test_zero_tip_revert_counts_only_gas_once_and_keeps_native_value_unspent(self):
        k, rpc = self.pending(); rpc.receipt['status'] = '0x0'
        self.assertFalse(k.poll_pending())
        day = dt.datetime.fromtimestamp(rpc.now, dt.timezone.utc).date().isoformat()
        self.assertEqual(k.state['spent'][day], 300)
        self.assertFalse(k.poll_pending()); self.assertEqual(k.state['spent'][day], 300)

    def test_actual_zero_tip_receipt_replays_without_changing_its_public_fields(self):
        rows = json.loads((ROOT/'reports/rpc-fees-20261113/network/RPC.json').read_text())['rows']
        zero = [r for r in rows if r.get('phase') == 'permitted/pinax-zero-tip']
        def result(method): return next(r['rpc_response']['result'] for r in zero if r['request']['method'] == method)
        transaction, receipt, header = (result(name) for name in ('eth_getTransactionByHash', 'eth_getTransactionReceipt', 'eth_getBlockByNumber'))
        originals = copy.deepcopy((transaction, receipt, header))
        self.assertEqual(transaction['type'], '0x2'); self.assertEqual(transaction['maxPriorityFeePerGas'], '0x0')
        self.assertEqual(receipt['effectiveGasPrice'], header['baseFeePerGas'])
        class ActualReadOnlyTranscript:
            def call(self, method, params):
                if method == 'eth_getTransactionByHash': return transaction
                if method == 'eth_getTransactionReceipt': return receipt
                if method == 'eth_getBlockByNumber': return header
                raise AssertionError(method)
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        cfg = {'chain_id': 4663, 'sender': transaction['from'], 'submission_fee_profile': 2,
            'receipt_fee_policy': 'included', 'contracts': {role: basic.B for role in ('access','vault','strategy','fees','compounder','buyback','pools')},
            'state_path': str(Path(temp.name)/'actual-receipt-test-journal.json'), 'confirmations': 1}
        k = Keeper(cfg, rpc=ActualReadOnlyTranscript())
        price, gas, value = (int(transaction[name], 16) for name in ('maxFeePerGas', 'gas', 'value'))
        k.state.update(next_nonce=int(transaction['nonce'], 16), pending={
            'key': 'qualification:actual-receipt', 'nonce': int(transaction['nonce'], 16), 'to': transaction['to'],
            'data': transaction['input'], 'value': value, 'day': '2026-11-13', 'hash': transaction['hash'],
            'fee_review': dict(schema=2, gas_limit=gas, max_fee_per_gas=price, l1_fee_allowance_wei=0,
                maximum_cost_wei=gas*price+value, receipt_fee_policy='included', execution_fee_model=MODEL)})
        k.save()
        with patch('keeper.monitor.time.time', return_value=int(header['timestamp'], 16)), patch('keeper.monitor.log'):
            self.assertFalse(k.poll_pending())
        expected = int(receipt['gasUsed'], 16)*int(header['baseFeePerGas'], 16)+value
        self.assertEqual(k.state['spent']['2026-11-13'], expected)
        self.assertEqual(k.state['last_fee_observation']['execution_price_wei'], int(header['baseFeePerGas'], 16))
        self.assertEqual((transaction, receipt, header), originals)
        self.assertIsNone(k.state['pending'])


if __name__ == '__main__':
    unittest.main()
