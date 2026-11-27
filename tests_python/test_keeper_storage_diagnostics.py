"""New storage-diagnostic branches, with inert cycle/write failures only.

The actual Keeper cycle boundary and temporary journal/health writer run. These
methods do not qualify real ENOSPC/EACCES, Cast, supervision or a financial job.
Only the existing FakeRpc data helper is reused; no old TestCase is inherited.
"""
import copy
import errno
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, atomic_json, error_context
from tests_python.test_keeper import A, B, FakeRpc
from zzz_ops.rpc import RpcError


class KeeperStorageDiagnosticTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.rpc = FakeRpc()
        config = {
            'chain_id': 1, 'sender': A,
            'contracts': {name: B for name in
                          ('access', 'vault', 'strategy', 'fees', 'compounder', 'buyback', 'pools')},
            'state_path': str(Path(temporary.name) / 'state.json'),
            'confirmations': 2, 'max_gas_limit': 100000,
            'max_gas_price_wei': 100, 'max_transaction_cost_wei': 1000000,
            'max_daily_cost_wei': 10000000,
        }
        self.k = Keeper(config, rpc=self.rpc)
        self.k.save()
        self.original_raw = self.k.path.read_bytes()
        self.original_state = copy.deepcopy(self.k.state)

    def test_reviewed_os_errnos_are_fixed_names_without_exception_contents(self):
        for number, name in ((errno.ENOSPC, 'ENOSPC'), (errno.EACCES, 'EACCES'),
                             (errno.EPERM, 'EPERM'), (errno.EROFS, 'EROFS'),
                             (errno.EIO, 'EIO'), (errno.EDQUOT, 'EDQUOT')):
            with self.subTest(errno=name):
                try:
                    raise OSError(number, 'SECRET https://credential@rpc.invalid', '/SECRET/keystore')
                except OSError as exc:
                    details = error_context(exc)
                    self.assertEqual(details['error_type'], type(exc).__name__)
                self.assertEqual(set(details), {'error_type', 'error_site', 'os_errno'})
                self.assertEqual(details['os_errno'], name)
                self.assertIn('test_reviewed_os_errnos', details['error_site'])
                serialized = json.dumps(details)
                for secret in ('SECRET', 'credential', 'rpc.invalid', 'keystore'):
                    self.assertNotIn(secret, serialized)

    def test_unreviewed_or_noninteger_errnos_preserve_original_two_fields(self):
        errors = (ValueError('SECRET'), OSError(None, 'SECRET'),
                  OSError(1234567, 'SECRET'), OSError(True, 'SECRET'),
                  OSError('ENOSPC', 'SECRET'))
        for error in errors:
            with self.subTest(type=type(error).__name__, errno=getattr(error, 'errno', None)):
                try:
                    raise error
                except Exception as exc:
                    details = error_context(exc)
                self.assertEqual(set(details), {'error_type', 'error_site'})
                self.assertEqual(details['error_type'], type(error).__name__)
                self.assertNotIn('SECRET', json.dumps(details))

    def test_journal_and_failure_health_refusals_retain_first_diagnostic(self):
        journal_error = OSError(errno.ENOSPC, 'SECRET journal details', '/SECRET/state')
        health_error = OSError(errno.EACCES, 'SECRET health details', '/SECRET/health')
        events, logged = [], []
        health_calls = 0

        def write(path, value, **kwargs):
            nonlocal health_calls
            if Path(path) == self.k.path:
                events.append('journal_write')
                raise journal_error
            self.assertEqual(Path(path), self.k.health_path)
            health_calls += 1
            if health_calls == 1:
                self.assertEqual(value['status'], 'running')
                events.append('health_running')
                return atomic_json(path, value, **kwargs)
            events.append('health_failure')
            raise health_error

        def record(event, **fields):
            events.append(event)
            logged.append((event, fields))

        with patch('keeper.monitor.atomic_json', side_effect=write), \
                patch('keeper.monitor.log', side_effect=record), \
                patch.object(self.k, 'cycle', side_effect=self.k.save), \
                patch('keeper.monitor.run_cast') as signer:
            with self.assertRaises(PermissionError) as raised:
                self.k.run_cycle()
        self.assertIs(raised.exception, health_error)
        self.assertEqual(events, ['health_running', 'journal_write', 'cycle_failed', 'health_failure'])
        self.assertEqual(len(logged), 1)
        self.assertFalse(logged[0][1]['retryable'])
        self.assertEqual(logged[0][1]['os_errno'], 'ENOSPC')
        self.assertEqual(logged[0][1]['error_type'], type(journal_error).__name__)
        self.assertNotIn('SECRET', json.dumps(logged))
        self.assertIsNone(self.k._lp_metadata_cache)
        self.assertEqual(self.k.cycle_failures, 1)
        self.assertTrue(self.k._cycle_error)
        self.assertEqual(self.k.path.read_bytes(), self.original_raw)
        self.assertEqual(self.k.state, self.original_state)
        self.assertEqual(json.loads(self.k.health_path.read_bytes())['status'], 'running')
        self.assertEqual(self.rpc.calls, [])
        signer.assert_not_called()

    def test_retryable_cycle_with_failed_health_still_raises_storage_error(self):
        original_error = RpcError('SECRET https://credential@rpc.invalid')
        health_error = OSError(errno.ENOSPC, 'SECRET health details', '/SECRET/health')
        events, logged = [], []

        def write(path, value, **kwargs):
            self.assertEqual(Path(path), self.k.health_path)
            events.append(value['status'])
            if value['status'] == 'running':
                return atomic_json(path, value, **kwargs)
            raise health_error

        def record(event, **fields):
            events.append(event)
            logged.append((event, fields))

        with patch('keeper.monitor.atomic_json', side_effect=write), \
                patch('keeper.monitor.log', side_effect=record), \
                patch.object(self.k, 'cycle', side_effect=original_error), \
                patch('keeper.monitor.run_cast') as signer:
            with self.assertRaises(OSError) as raised:
                self.k.run_cycle()
        self.assertIs(raised.exception, health_error)
        self.assertEqual(events, ['running', 'cycle_failed', 'error'])
        self.assertEqual(len(logged), 1)
        self.assertTrue(logged[0][1]['retryable'])
        self.assertEqual(logged[0][1]['error_type'], 'RpcError')
        self.assertNotIn('os_errno', logged[0][1])
        self.assertNotIn('SECRET', json.dumps(logged))
        self.assertIsNone(self.k._lp_metadata_cache)
        self.assertEqual(self.k.path.read_bytes(), self.original_raw)
        self.assertEqual(self.k.state, self.original_state)
        signer.assert_not_called()

    def test_writable_failure_health_keeps_original_exception_and_errno(self):
        error = OSError(errno.EIO, 'SECRET journal details', '/SECRET/state')
        logged = []
        with patch('keeper.monitor.log', side_effect=lambda event, **fields: logged.append((event, fields))), \
                patch.object(self.k, 'cycle', side_effect=error), \
                patch('keeper.monitor.run_cast') as signer:
            with self.assertRaises(OSError) as raised:
                self.k.run_cycle()
        self.assertIs(raised.exception, error)
        health = json.loads(self.k.health_path.read_bytes())
        self.assertEqual(health['status'], 'halted')
        self.assertEqual(health['os_errno'], 'EIO')
        self.assertEqual(health['error_type'], type(error).__name__)
        self.assertEqual(health['consecutive_failures'], 1)
        self.assertFalse(health['pending'])
        self.assertIsNone(health['last_success_at'])
        self.assertEqual(len(logged), 1)
        self.assertFalse(logged[0][1]['retryable'])
        self.assertNotIn('SECRET', json.dumps(health))
        self.assertEqual(self.k.path.read_bytes(), self.original_raw)
        self.assertEqual(self.k.state, self.original_state)
        self.assertIsNone(self.k._lp_metadata_cache)
        signer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
