"""New reported-hash diagnostics at the inert signer/save boundary.

FakeRpc and a fake Cast result supply data; real submit/reload/guard logic runs.
This does not prove node acceptance, Unix signer startup or actual disk refusal.
"""
import copy
import errno
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python.test_keeper import A, B, H, FakeRpc
from zzz_ops.abi import keccak256


class KeeperStorageHashDiagnosticTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.rpc = FakeRpc()
        roles = ('access', 'vault', 'strategy', 'fees', 'compounder', 'buyback', 'pools')
        self.config = {
            'chain_id': 1, 'sender': A,
            'contracts': {name: B for name in roles},
            'code_hashes': {name: '0x' + keccak256(bytes.fromhex('6000')).hex() for name in roles},
            'state_path': str(Path(temporary.name) / 'state.json'),
            'confirmations': 2, 'receipt_fee_policy': 'included',
            'max_gas_limit': 100000, 'max_gas_price_wei': 100,
            'max_transaction_cost_wei': 1000000, 'max_daily_cost_wei': 10000000,
        }
        self.k = Keeper(self.config, rpc=self.rpc)
        self.k.state.update(next_nonce=7, receipt_anchor={
            'number': 98, 'hash': H, 'timestamp': self.rpc.now, 'nonce': 6})
        self.k.save()
        self.previous = copy.deepcopy(self.k.state)
        # Explicit seam: start at submit(), after signer-file startup validation.
        self.k.live = True
        self.k.cast = '/inert/cast'
        self.k.keystore = Path('/inert/key')
        self.k.password = Path('/inert/password')

    def submit(self, keeper=None):
        return (keeper or self.k).submit(
            'vault', 'collectFees(uint256,uint256)',
            (1, self.rpc.now + 180), 'harvest:1')

    def test_valid_reported_hash_survives_in_diagnostic_when_hash_save_fails(self):
        reported = '0x' + 'Bc' * 32
        durable, logged = [], []
        original_save = self.k.save
        refusal = OSError(errno.ENOSPC, 'SECRET disk details', '/SECRET/state')

        def save():
            if self.k.state.get('pending', {}).get('hash') is not None:
                raise refusal
            original_save()

        def signer(command, **_kwargs):
            durable.append(self.k.path.read_bytes())
            self.assertIsNone(json.loads(durable[-1])['pending']['hash'])
            return subprocess.CompletedProcess(command, 0, json.dumps(
                {'transactionHash': reported}), 'SECRET signer stderr')

        with patch.object(self.k, 'save', side_effect=save), \
                patch('keeper.monitor.run_cast', side_effect=signer) as cast, \
                patch('keeper.monitor.log', side_effect=lambda event, **fields: logged.append((event, fields))):
            with self.assertRaises(OSError) as raised:
                self.submit()
        self.assertIs(raised.exception, refusal)
        cast.assert_called_once()
        self.assertEqual(len(durable), 1)
        self.assertEqual(self.k.path.read_bytes(), durable[0])
        self.assertIsNone(json.loads(durable[0])['pending']['hash'])
        self.assertEqual(self.k.state['pending']['hash'], reported.lower())
        self.assertEqual([name for name, _ in logged], ['submission_requires_reconciliation'])
        details = logged[0][1]
        self.assertEqual(details['reported_transaction'], reported.lower())
        self.assertEqual(details['os_errno'], 'ENOSPC')
        self.assertEqual(details['error_type'], type(refusal).__name__)
        self.assertNotIn('transaction', details)
        self.assertNotIn('SECRET', json.dumps(logged))
        for name in ('next_nonce', 'spent', 'last', 'receipt_anchor'):
            self.assertEqual(self.k.state[name], self.previous[name])
        restored = Keeper(self.config, rpc=self.rpc)
        with patch('keeper.monitor.run_cast') as resend:
            self.assertTrue(restored.poll_pending())
            self.assertFalse(self.submit(restored))
        resend.assert_not_called()
        self.assertEqual(restored.path.read_bytes(), durable[0])

    def test_malformed_signer_candidate_never_reaches_reconciliation_diagnostic(self):
        durable, logged = [], []
        malformed = {'transactionHash': {'password': 'SECRET https://credential@rpc.invalid'}}

        def signer(command, **_kwargs):
            durable.append(self.k.path.read_bytes())
            return subprocess.CompletedProcess(command, 0, json.dumps(malformed), 'SECRET stderr')

        with patch('keeper.monitor.run_cast', side_effect=signer) as cast, \
                patch('keeper.monitor.log', side_effect=lambda event, **fields: logged.append((event, fields))):
            with self.assertRaisesRegex(RuntimeError, 'Signer did not return a transaction hash'):
                self.submit()
        cast.assert_called_once()
        self.assertEqual(len(durable), 1)
        self.assertEqual(self.k.path.read_bytes(), durable[0])
        self.assertIsNone(self.k.state['pending']['hash'])
        self.assertEqual([name for name, _ in logged], ['submission_requires_reconciliation'])
        self.assertNotIn('reported_transaction', logged[0][1])
        self.assertNotIn('transaction', logged[0][1])
        self.assertNotIn('os_errno', logged[0][1])
        self.assertEqual(logged[0][1]['error_type'], 'RuntimeError')
        self.assertNotIn('SECRET', json.dumps(logged))
        for name in ('next_nonce', 'spent', 'last', 'receipt_anchor'):
            self.assertEqual(self.k.state[name], self.previous[name])


if __name__ == '__main__':
    unittest.main()
