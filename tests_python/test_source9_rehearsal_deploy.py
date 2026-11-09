"""Recovery controls for the disposable rehearsal sender; no EVM/network work."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('source9_rehearsal_deploy_tested', ROOT / 'scripts/source9_rehearsal_deploy.py')
DEPLOY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEPLOY)
from zzz_ops.errors import RpcError

TX_HASH = '0x' + 'a' * 64
BLOCK_HASH = '0x' + 'b' * 64
OWNER = '0x' + '1' * 40


class DeploymentJournalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.log = Path(self.temporary.name) / 'transactions.ndjson'
        self.lab = DEPLOY.RehearsalDeployment.__new__(DEPLOY.RehearsalDeployment)
        self.lab.owner = OWNER
        self.lab.contracts = {}
        self.lab.receipts = []
        self.lab.pending_submission = None
        self.lab.intent_sequence = 0
        self.lab.txlog = self.log.open('x', encoding='utf-8', newline='\n')
        self.addCleanup(self.lab.txlog.close)
        self.submissions = 0
        self.reads = 0
        self.read_behavior = lambda: self.receipt()
        self.send_error = None
        self.synced_events = []
        real_sync = os.fsync

        def observed_sync(fd):
            real_sync(fd)
            self.synced_events.append(self.events()[-1]['event'])

        self.sync = patch.object(DEPLOY.os, 'fsync', side_effect=observed_sync)
        self.sync.start()
        self.addCleanup(self.sync.stop)
        self.sleep = patch.object(DEPLOY.time, 'sleep', return_value=None)
        self.sleep.start()
        self.addCleanup(self.sleep.stop)
        self.lab.rpc = self.rpc

    def events(self):
        return [json.loads(line) for line in self.log.read_text(encoding='utf-8').splitlines()]

    def receipt(self, status='0x1'):
        return dict(transactionHash=TX_HASH, status=status, blockNumber='0x8', blockHash=BLOCK_HASH)

    def rpc(self, method, params):
        if method == 'eth_estimateGas':
            return hex(100000)
        if method == 'eth_getBlockByNumber':
            return dict(number='0x7', hash=BLOCK_HASH, gasLimit=hex(64_000_000))
        if method == 'eth_getTransactionCount':
            self.assertEqual(params, [OWNER, 'pending'])
            return '0x0'
        if method == 'eth_sendTransaction':
            self.submissions += 1
            # The exact calldata, nonce and budget are durable before send.
            self.assertEqual(self.events()[-1]['event'], 'intent')
            self.assertEqual(self.synced_events[-1], 'intent')
            self.assertEqual(self.events()[-1]['transaction'], params[0])
            self.assertEqual(params[0]['nonce'], '0x0')
            if self.send_error:
                raise self.send_error
            return TX_HASH
        if method == 'eth_getTransactionReceipt':
            self.reads += 1
            self.assertEqual(params, [TX_HASH])
            # At the injected read fault, an independent file read already
            # observes the submitted hash and the fsync has completed.
            submitted = [e for e in self.events() if e['event'] == 'submitted']
            self.assertEqual(len(submitted), 1)
            self.assertEqual(submitted[0]['transaction_hash'], TX_HASH)
            self.assertIn('submitted', self.synced_events)
            return self.read_behavior()
        self.fail('Unexpected RPC method: ' + method)

    def test_transient_receipt_fault_retries_only_same_durable_hash(self):
        def read():
            if self.reads == 1:
                raise RpcError('injected receipt read unavailable')
            return self.receipt()
        self.read_behavior = read
        result = self.lab.send('controlled-deployment', data='0x1234')
        self.assertEqual(result['transactionHash'], TX_HASH)
        self.assertEqual((self.submissions, self.reads), (1, 2))
        self.assertEqual([e['event'] for e in self.events()], ['intent', 'submitted', 'receipt_read_error', 'confirmed'])
        self.assertEqual(self.synced_events, ['intent', 'submitted', 'receipt_read_error', 'confirmed'])
        self.assertIsNone(self.lab.pending_submission)
        self.assertEqual(len(self.lab.receipts), 1)

    def test_unknown_submission_retains_intent_and_blocks_any_new_send(self):
        self.send_error = RpcError('injected disconnect after possible submission')
        with self.assertRaises(DEPLOY.SubmissionUncertain):
            self.lab.send('unknown-submission', data='0x12')
        with self.assertRaises(DEPLOY.SubmissionUncertain):
            self.lab.send('forbidden-new-send', data='0x34')
        self.assertEqual((self.submissions, self.reads), (1, 0))
        self.assertEqual([e['event'] for e in self.events()], ['intent', 'submission_unknown'])
        self.assertEqual(self.lab.pending_submission['state'], 'submission_unknown')
        self.assertEqual(self.lab.receipts, [])

    def test_receipt_deadline_retains_hash_without_failed_or_resubmitted_outcome(self):
        self.read_behavior = lambda: (_ for _ in ()).throw(RpcError('read still unavailable'))
        with patch.object(DEPLOY.time, 'monotonic', side_effect=[0, 0, 121, 121]):
            with self.assertRaises(DEPLOY.ReceiptUnresolved):
                self.lab.send('bounded-receipt-wait')
        self.assertEqual((self.submissions, self.reads), (1, 1))
        self.assertEqual(self.events()[-1]['event'], 'receipt_unresolved')
        self.assertEqual(self.lab.pending_submission['transaction_hash'], TX_HASH)
        self.assertEqual(self.lab.receipts, [])
        with self.assertRaises(DEPLOY.SubmissionUncertain):
            self.lab.send('forbidden-after-deadline')

    def test_non_rpc_receipt_error_aborts_without_retry_or_hash_loss(self):
        self.read_behavior = lambda: (_ for _ in ()).throw(ValueError('programming fault'))
        with self.assertRaisesRegex(ValueError, 'programming fault'):
            self.lab.send('non-rpc-abort')
        self.assertEqual((self.submissions, self.reads), (1, 1))
        self.assertEqual([e['event'] for e in self.events()], ['intent', 'submitted'])
        self.assertEqual(self.lab.pending_submission['transaction_hash'], TX_HASH)

    def test_authenticated_revert_is_recorded_distinctly_from_unknown_receipt(self):
        self.read_behavior = lambda: self.receipt('0x0')
        with self.assertRaisesRegex(ValueError, 'reverted'):
            self.lab.send('actual-revert')
        self.assertEqual((self.submissions, self.reads), (1, 1))
        self.assertEqual(self.events()[-1]['event'], 'reverted')
        self.assertEqual(len(self.lab.receipts), 1)
        self.assertIsNone(self.lab.pending_submission)

    def test_mismatched_receipt_keeps_submitted_hash_unresolved(self):
        def read():
            receipt = self.receipt()
            receipt['transactionHash'] = '0x' + 'c' * 64
            return receipt
        self.read_behavior = read
        with self.assertRaises(DEPLOY.ReceiptUnresolved):
            self.lab.send('mismatched-receipt')
        self.assertEqual((self.submissions, self.reads), (1, 1))
        self.assertEqual(self.events()[-1]['event'], 'receipt_rejected')
        self.assertEqual(self.lab.pending_submission['transaction_hash'], TX_HASH)
        self.assertEqual(self.lab.receipts, [])


class FundingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / 'new-evidence'
        self.calls = []
        self.balance = 17
        self.snapshots = {}
        self.final_write_seen = False
        self.fail_final_verification = False
        self.allow_restore_log_fault = False
        self.synced_events = []
        self.final_path = self.output / ('fixture-zzz-funding-' + OWNER[2:] + '.json')
        self.intent_path = self.output / ('fixture-zzz-funding-' + OWNER[2:] + '-intent.json')
        self.journal_path = self.output / ('fixture-zzz-funding-' + OWNER[2:] + '-journal.ndjson')
        transport = patch.object(DEPLOY, '_transport', side_effect=lambda rpc: rpc)
        transport.start()
        self.addCleanup(transport.stop)
        real_sync = os.fsync

        def observed_sync(fd):
            real_sync(fd)
            if self.journal_path.exists():
                events = self.events()
                if events:
                    self.synced_events.append(events[-1]['event'])

        sync = patch.object(DEPLOY.os, 'fsync', side_effect=observed_sync)
        sync.start()
        self.addCleanup(sync.stop)

    def events(self):
        return [json.loads(line) for line in self.journal_path.read_text(encoding='utf-8').splitlines()]

    def rpc(self, method, params):
        self.calls.append((method, params))
        if method == 'eth_accounts':
            return [OWNER]
        if method == 'eth_call':
            if self.final_write_seen and self.fail_final_verification:
                raise RpcError('injected verification read failure after actual local write')
            return '0x' + f'{self.balance:064x}'
        # Every administrative call observes files already reserved/writable,
        # plus its matching exact intent durably flushed before the call.
        self.assertTrue(self.final_path.is_file())
        self.assertEqual(json.loads(self.intent_path.read_text())['requested_balance'], '1000')
        latest = self.events()[-1]['event']
        if not (method == 'evm_revert' and self.allow_restore_log_fault):
            self.assertEqual(self.synced_events[-1], latest)
        if method == 'evm_snapshot':
            self.assertEqual(latest, 'probe_snapshot_intent')
            identifier = '0x1'
            self.snapshots[identifier] = self.balance
            return identifier
        if method == 'anvil_setStorageAt':
            self.assertIn(latest, ('probe_write_intent', 'funding_write_intent'))
            self.balance = int(params[2], 16)
            self.final_write_seen = latest == 'funding_write_intent'
            return True
        if method == 'evm_revert':
            self.assertEqual(latest, 'probe_restore_intent')
            self.balance = self.snapshots[params[0]]
            return True
        self.fail('Unexpected funding RPC method: ' + method)

    def test_invalid_output_location_fails_before_any_rpc(self):
        self.output.write_bytes(b'not a directory')
        with self.assertRaises(FileExistsError):
            DEPLOY.fund_zzz(self.rpc, OWNER, 1000, self.output)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.balance, 17)

    def test_existing_record_is_preserved_and_rejected_before_any_rpc(self):
        self.output.mkdir()
        self.final_path.write_bytes(b'original funding evidence\x00')
        with self.assertRaises(FileExistsError):
            DEPLOY.fund_zzz(self.rpc, OWNER, 1000, self.output)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.final_path.read_bytes(), b'original funding evidence\x00')
        self.assertEqual(self.balance, 17)

    def test_missing_directory_is_reserved_and_intents_fsynced_before_mutation(self):
        self.assertFalse(self.output.exists())
        result = DEPLOY.fund_zzz(self.rpc, OWNER, 1000, self.output)
        self.assertEqual(result['state'], 'verified')
        self.assertEqual(result['balance_before'], '17')
        self.assertEqual(result['balance_after'], '1000')
        self.assertEqual(json.loads(self.final_path.read_text()), result)
        self.assertEqual([method for method, _ in self.calls if method != 'eth_call' and method != 'eth_accounts'],
                         ['evm_snapshot', 'anvil_setStorageAt', 'evm_revert', 'anvil_setStorageAt'])
        self.assertIn('funding_intent', self.synced_events)
        self.assertIn('funding_write_intent', self.synced_events)
        self.assertEqual(self.events()[-1]['event'], 'funding_verified')

    def test_post_write_read_fault_keeps_intent_and_forbids_automatic_replay(self):
        self.fail_final_verification = True
        with self.assertRaises(RpcError):
            DEPLOY.fund_zzz(self.rpc, OWNER, 1000, self.output)
        self.assertEqual(self.balance, 1000)
        self.assertEqual(self.events()[-1]['event'], 'funding_aborted')
        self.assertEqual(self.events()[-1]['phase'], 'final_balance_verification')
        self.assertNotEqual(json.loads(self.final_path.read_text())['state'], 'verified')
        before_replay = list(self.calls)
        with self.assertRaises(FileExistsError):
            DEPLOY.fund_zzz(self.rpc, OWNER, 1000, self.output)
        self.assertEqual(self.calls, before_replay)
        self.assertIn('funding_write_intent', self.synced_events)

    def test_probe_snapshot_is_restored_even_if_restore_intent_fsync_faults(self):
        self.allow_restore_log_fault = True
        synced = DEPLOY.os.fsync
        faulted = False

        def fail_restore_once(fd):
            nonlocal faulted
            if self.journal_path.exists() and self.events() and self.events()[-1]['event'] == 'probe_restore_intent' and not faulted:
                faulted = True
                raise OSError('injected restore-intent evidence storage fault')
            return synced(fd)

        with patch.object(DEPLOY.os, 'fsync', side_effect=fail_restore_once):
            with self.assertRaisesRegex(OSError, 'evidence storage fault'):
                DEPLOY.fund_zzz(self.rpc, OWNER, 1000, self.output)
        self.assertTrue(faulted)
        self.assertEqual(self.balance, 17)
        self.assertEqual([method for method, _ in self.calls if method not in ('eth_call', 'eth_accounts')],
                         ['evm_snapshot', 'anvil_setStorageAt', 'evm_revert'])
        self.assertFalse(self.final_write_seen)
        self.assertEqual(self.events()[-1]['event'], 'funding_aborted')


if __name__ == '__main__':
    unittest.main()
