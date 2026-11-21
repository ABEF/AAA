"""New bounded-capture integration cases; inert fresh7 RPC and signer hook.

Existing fixtures are composed only for setup/helpers. No inherited old test
method, real wallet, chain, service or Cast invocation runs in this module.
"""
import copy
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import types
import unittest
from unittest.mock import patch

from keeper.cast_process import CastCaptureError
from keeper.health import HEALTH_SCHEMA, execution_reasons
from keeper.monitor import Keeper
from tests_python import test_keeper_intent_shutdown as intent
from tests_python import test_keeper_execution_telemetry as execution
from tests_python import test_keeper_confirmation_health as confirmation


class SigningPath:
    """Explicit Unix metadata fixture; no real keystore is opened."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def resolve(self):
        return self

    def stat(self):
        return types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=1234)


class KeeperCastCaptureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = intent.KeeperIntentShutdownTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.k, self.rpc = self.fixture.k, self.fixture.rpc

    def assert_unchanged_accounting(self, state):
        for field in ('next_nonce', 'spent', 'last', 'receipt_anchor'):
            self.assertEqual(self.k.state[field], state[field], field)

    def fail_send(self, error):
        previous = copy.deepcopy(self.k.state)
        published = []
        def capture(command, *, env, timeout):
            published.append(self.k.path.read_bytes())
            self.assertIsNone(json.loads(published[-1])['pending']['hash'])
            self.assertEqual(timeout, 90)
            self.assertEqual(env['ETH_RPC_URL'], self.rpc.active_url)
            raise error
        with patch('keeper.monitor.run_cast', side_effect=capture) as signer:
            with self.assertRaises(type(error)):
                self.fixture.submit()
        signer.assert_called_once()
        self.assertEqual(len(published), 1)
        self.assertEqual(self.k.path.read_bytes(), published[0])
        self.assertIsNone(self.k.state['pending']['hash'])
        self.assert_unchanged_accounting(previous)
        restored = Keeper(self.fixture.cfg, rpc=self.rpc)
        restored.live = True
        with patch('keeper.monitor.run_cast') as resend:
            self.assertFalse(self.fixture.submit(restored))
            restored.cycle()
            resend.assert_not_called()
        self.assertEqual(restored.state, self.k.state)
        self.assertEqual(restored.path.read_bytes(), published[0])

    def test_capture_overflow_and_invalid_encoding_preserve_exact_pending_intent(self):
        # Both post-start failure classes are conservative broadcast uncertainty.
        for message in ('Cast output exceeded its byte limit', 'Cast output was not valid UTF-8'):
            with self.subTest(error=message):
                fixture = intent.KeeperIntentShutdownTests()
                fixture.setUp()
                previous = self.fixture
                self.fixture = fixture
                self.k, self.rpc = fixture.k, fixture.rpc
                try:
                    self.fail_send(CastCaptureError(message))
                finally:
                    fixture.doCleanups()
                    self.fixture = previous
                    self.k, self.rpc = previous.k, previous.rpc

    def test_capture_timeout_preserves_exact_pending_intent_and_never_resends(self):
        self.fail_send(subprocess.TimeoutExpired('Cast', 90))

    def test_successful_bounded_hook_preserves_original_review_and_hash(self):
        previous = copy.deepcopy(self.k.state)
        published = []
        mixed = '0x' + 'Bc' * 32
        def capture(command, *, env, timeout):
            published.append(json.loads(self.k.path.read_bytes()))
            self.assertEqual(timeout, 90)
            self.assertEqual(env['ETH_RPC_URL'], self.rpc.active_url)
            saved = published[-1]['pending']
            for flag, value in (('--nonce', saved['nonce']), ('--value', saved['value']),
                                ('--gas-limit', saved['fee_review']['gas_limit']),
                                ('--gas-price', saved['fee_review']['max_fee_per_gas'])):
                self.assertEqual(command[command.index(flag)+1], str(value))
            self.assertEqual(command[3], saved['data'])
            return subprocess.CompletedProcess(command, 0, json.dumps({'hash': mixed}), '')
        with patch('keeper.monitor.run_cast', side_effect=capture) as signer:
            self.assertTrue(self.fixture.submit())
        signer.assert_called_once()
        final = json.loads(self.k.path.read_bytes())
        self.assertEqual(final, self.k.state)
        self.assertEqual(final['pending']['hash'], mixed.lower())
        for key in ('key', 'nonce', 'to', 'data', 'value', 'day', 'fee_review'):
            self.assertEqual(final['pending'][key], published[0]['pending'][key])
        self.assert_unchanged_accounting(previous)

    def test_shutdown_after_intent_does_not_invoke_new_capture_hook(self):
        before = copy.deepcopy(self.k.state)
        save = self.k.save
        def stop_after_save():
            save()
            self.fixture.stopping = True
        with patch.object(self.k, 'save', side_effect=stop_after_save), \
                patch('keeper.monitor.run_cast') as signer:
            self.assertFalse(self.fixture.submit())
        signer.assert_not_called()
        self.assertIsNone(self.k.state['pending']['hash'])
        self.assert_unchanged_accounting(before)

    def signer_paths(self):
        self.k.config.update(keystore='/inert/capture-key', password_file='/inert/capture-password')
        return SigningPath

    def test_address_capture_overflow_is_bounded_to_30_seconds_without_journal_change(self):
        self.k.save()
        before = self.k.path.read_bytes()
        with patch('keeper.monitor.shutil.which', return_value='/inert/cast'), \
                patch('keeper.monitor.Path', side_effect=self.signer_paths()), \
                patch('keeper.monitor.os.getuid', return_value=1234, create=True), \
                patch('keeper.monitor.run_cast', side_effect=CastCaptureError('Cast output exceeded its byte limit')) as capture:
            with self.assertRaises(CastCaptureError):
                self.k._validate_signer()
        capture.assert_called_once()
        self.assertEqual(capture.call_args.kwargs['timeout'], 30)
        self.assertEqual(capture.call_args.args[0][1:3], ['wallet', 'address'])
        self.assertEqual(self.k.path.read_bytes(), before)

    def test_address_capture_still_rejects_wrong_address_and_nonzero_exit(self):
        for result in (subprocess.CompletedProcess([], 0, '0x'+'12'*20, ''),
                       subprocess.CompletedProcess([], 1, self.k.sender, '')):
            with self.subTest(returncode=result.returncode), \
                    patch('keeper.monitor.shutil.which', return_value='/inert/cast'), \
                    patch('keeper.monitor.Path', side_effect=self.signer_paths()), \
                    patch('keeper.monitor.os.getuid', return_value=1234, create=True), \
                    patch('keeper.monitor.run_cast', return_value=result):
                with self.assertRaises(ValueError):
                    self.k._validate_signer()

    def test_execution_health_authenticates_the_capture_helper_source(self):
        fixture = execution.KeeperExecutionTelemetryTests()
        fixture.setUp()
        try:
            fixture.k.save()
            before = fixture.k.path.read_bytes()
            with patch('keeper.monitor.run_cast', side_effect=AssertionError('Read-only health must not run Cast')):
                record = fixture._observe()
            data = {'health_schema': HEALTH_SCHEMA, 'lp_execution_health': record}
            self.assertEqual([], execution_reasons(data, fixture.cfg, now=fixture.rpc.now, max_age=1800))
            source = 'keeper/cast_process.py'
            expected = hashlib.sha256(Path(source).read_bytes()).hexdigest()
            self.assertEqual(record['last_confirmed']['source_files_sha256'][source], expected)
            for mutation in ('missing', 'changed'):
                changed = copy.deepcopy(data)
                pins = changed['lp_execution_health']['last_confirmed']['source_files_sha256']
                if mutation == 'missing': pins.pop(source)
                else: pins[source] = '0' * 64
                self.assertIn('execution_observation_source_mismatch', execution_reasons(
                    changed, fixture.cfg, now=fixture.rpc.now, max_age=1800))
            self.assertEqual(before, fixture.k.path.read_bytes())
        finally:
            fixture.doCleanups()

    def test_confirmation_health_authenticates_the_capture_helper_source(self):
        fixture = confirmation.KeeperConfirmationHealthTests()
        fixture.setUp()
        try:
            before = fixture.k.path.read_bytes()
            with patch('keeper.monitor.run_cast', side_effect=AssertionError('Read-only health must not run Cast')):
                report = fixture.observe()
            data = fixture.data(report)
            self.assertEqual([], fixture.reasons(data))
            source = 'keeper/cast_process.py'
            expected = hashlib.sha256(Path(source).read_bytes()).hexdigest()
            self.assertEqual(report['last_observed']['source_files_sha256'][source], expected)
            for mutation in ('missing', 'changed'):
                changed = copy.deepcopy(data)
                pins = changed['rebalance_confirmation_health']['policy']['last_observed']['source_files_sha256']
                if mutation == 'missing': pins.pop(source)
                else: pins[source] = '0' * 64
                self.assertIn('confirmation_observation_source_mismatch', fixture.reasons(changed))
            self.assertEqual(before, fixture.k.path.read_bytes())
        finally:
            fixture.doCleanups()


if __name__ == '__main__':
    unittest.main()
