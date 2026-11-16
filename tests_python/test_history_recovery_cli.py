"""New offline history-recovery CLI contracts; no live databases or network.

Core SQLite snapshot/restore cases are defined in the companion new module.
These cases inject only the operations while exercising real argument parsing,
strict inputs, shared work scope, output safety messaging and source pinning.
No historical test body is selected or executed.
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, checkpoint, request_scope, _current


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('history_recovery_cli_subject', ROOT/'scripts/history-recovery.py')
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)
SHA = 'a'*64


class HistoryRecoveryCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='popl-history-recovery-cli-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = self.root/'reviewed-api.json'
        self.config.write_bytes('{"note":"Revue étudiée","private_rpc":"not-a-real-credential"}\n'.encode('utf-8'))
        self.original = self.config.read_bytes()
        self.output = self.root/'new-backup'
        self.bundle = self.root/'approved-bundle'
        self.review = self.root/'approved-import-review.json'
        self.review.write_bytes(b'{"approved":false}\n')
        self.loaded = {'note': 'Revue étudiée'}
        self.manifest = {'schema': 1, 'production_approved': False, 'installed': False}

    def argv(self, action='backup', *extra):
        if action == 'backup': args = ['backup', '--config', str(self.config), '--output', str(self.output)]
        elif action == 'verify': args = ['verify', '--bundle', str(self.bundle), '--manifest-sha256', SHA]
        else: args = ['restore', '--bundle', str(self.bundle), '--manifest-sha256', SHA, '--output', str(self.output)]
        return args+list(extra)

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = CLI.main(args)
        return result, out.getvalue(), err.getvalue()

    def mocks(self, stack):
        loaded = stack.enter_context(patch.object(CLI, 'load_config', return_value=self.loaded))
        backup = stack.enter_context(patch.object(CLI, 'backup', return_value=(self.manifest, SHA)))
        verify = stack.enter_context(patch.object(CLI, 'verify', return_value=self.manifest))
        restore = stack.enter_context(patch.object(CLI, 'restore', return_value=(self.manifest, SHA)))
        return loaded, backup, verify, restore

    def assert_preflight_rejected(self, args):
        with ExitStack() as stack:
            operations = self.mocks(stack)
            code, out, err = self.invoke(args)
        self.assertEqual(1, code)
        self.assertEqual('', out)
        self.assertTrue(err)
        for operation in operations: operation.assert_not_called()
        self.assertEqual(self.original, self.config.read_bytes())

    def test_action_and_each_action_specific_required_input_are_mandatory(self):
        samples = [[], ['unknown'], ['backup'], ['verify'], ['restore']]
        for action, required in (('backup', ('--config', '--output')),
                                 ('verify', ('--bundle', '--manifest-sha256')),
                                 ('restore', ('--bundle', '--manifest-sha256', '--output'))):
            for flag in required:
                args = self.argv(action); at = args.index(flag)
                samples.append(args[:at]+args[at+2:])
        for args in samples:
            with self.subTest(args=args), ExitStack() as stack:
                operations = self.mocks(stack)
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as rejected:
                    CLI.main(args)
                self.assertEqual(2, rejected.exception.code)
                for operation in operations: operation.assert_not_called()

    def test_no_signing_installation_network_or_live_replacement_switch_exists(self):
        for flag in ('--sign', '--broadcast', '--install', '--approve', '--replace', '--delete',
                     '--rpc-url', '--private-key', '--gas-limit', '--max-calls', '--max-posts'):
            for action in ('backup', 'verify', 'restore'):
                with self.subTest(action=action, flag=flag), ExitStack() as stack:
                    operations = self.mocks(stack)
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as rejected:
                        CLI.main(self.argv(action, flag))
                    self.assertEqual(2, rejected.exception.code)
                    for operation in operations: operation.assert_not_called()

    def test_arguments_for_other_actions_cannot_be_silently_ignored(self):
        samples = (self.argv('verify', '--config', str(self.config)),
                   self.argv('verify', '--output', str(self.output)),
                   self.argv('backup', '--manifest-sha256', SHA),
                   self.argv('backup', '--bundle', str(self.bundle)),
                   self.argv('restore', '--review', str(self.review)))
        for args in samples:
            with self.subTest(args=args), ExitStack() as stack:
                operations = self.mocks(stack)
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as rejected:
                    CLI.main(args)
                self.assertEqual(2, rejected.exception.code)
                for operation in operations: operation.assert_not_called()

    def test_optional_review_file_and_digest_must_be_supplied_together(self):
        self.assert_preflight_rejected(self.argv('backup', '--review', str(self.review)))
        self.assert_preflight_rejected(self.argv('backup', '--review-sha256', SHA))

    def test_reviewed_manifest_digests_are_exact_lowercase_sha256(self):
        for value in ('', 'a'*63, 'a'*65, 'A'*64, 'g'*64, '0x'+SHA, 'a'*63+'\n'):
            for action in ('verify', 'restore'):
                with self.subTest(action=action, value=value):
                    args = self.argv(action);args[args.index('--manifest-sha256')+1] = value
                    self.assert_preflight_rejected(args)

    def test_optional_review_digest_is_validated_before_loading_config(self):
        for value in ('', 'A'*64, '0x'+SHA, 'g'*64, SHA+'\n'):
            with self.subTest(value=value):
                self.assert_preflight_rejected(self.argv('backup', '--review', str(self.review), '--review-sha256', value))

    def test_time_budget_keeps_existing_offline_bounds(self):
        for value in ('0', '-1', '3601'):
            for action in ('backup', 'verify', 'restore'):
                with self.subTest(action=action, value=value):
                    self.assert_preflight_rejected(self.argv(action, '--max-seconds', value))

    def test_payload_budget_has_a_positive_bounded_offline_ceiling(self):
        for value in ('0', '-1', str((1 << 40)+1)):
            for action in ('backup', 'verify', 'restore'):
                with self.subTest(action=action, value=value):
                    self.assert_preflight_rejected(self.argv(action, '--max-bytes', value))

    def test_noninteger_limit_text_is_rejected_by_argument_parser(self):
        for flag in ('--max-seconds', '--max-bytes'):
            for value in ('1.5', 'true', 'nan', 'inf', '0x10'):
                with self.subTest(flag=flag, value=value), ExitStack() as stack:
                    operations = self.mocks(stack)
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as rejected:
                        CLI.main(self.argv('backup', flag, value))
                    self.assertEqual(2, rejected.exception.code)
                    for operation in operations: operation.assert_not_called()

    def test_backup_forwards_reviewed_config_and_fresh_paths_with_defaults(self):
        with ExitStack() as stack:
            loaded, backup, verify, restore = self.mocks(stack)
            code, out, err = self.invoke(self.argv())
        self.assertEqual(0, code);self.assertEqual('', err)
        loaded.assert_called_once_with(self.config)
        self.assertEqual((self.loaded, self.output), backup.call_args.args)
        self.assertIsNone(backup.call_args.kwargs.get('review'))
        self.assertEqual(1 << 30, backup.call_args.kwargs['max_bytes'])
        verify.assert_not_called();restore.assert_not_called()
        self.assertIn(SHA, out);self.assertIn('not approved', out.lower())
        self.assertNotIn('not-a-real-credential', out+err)
        self.assertEqual(self.original, self.config.read_bytes())

    def test_backup_forwards_optional_review_exactly_without_approving_it(self):
        with ExitStack() as stack:
            loaded, backup, verify, restore = self.mocks(stack)
            code, out, err = self.invoke(self.argv('backup', '--review', str(self.review), '--review-sha256', SHA,
                                                   '--max-seconds', '120', '--max-bytes', '1234567'))
        self.assertEqual(0, code);self.assertEqual('', err)
        review = backup.call_args.kwargs['review']
        self.assertEqual(self.review, Path(review['path']))
        self.assertEqual(SHA, review['sha256'])
        self.assertEqual(1234567, backup.call_args.kwargs['max_bytes'])
        self.assertIn('not approved', out.lower())
        self.assertEqual(b'{"approved":false}\n', self.review.read_bytes())
        verify.assert_not_called();restore.assert_not_called()

    def test_verify_uses_only_bundle_digest_and_offline_limits(self):
        with ExitStack() as stack:
            loaded, backup, verify, restore = self.mocks(stack)
            code, out, err = self.invoke(self.argv('verify', '--max-seconds', '120', '--max-bytes', '1234567'))
        self.assertEqual(0, code);self.assertEqual('', err)
        self.assertEqual((self.bundle, SHA), verify.call_args.args)
        self.assertEqual(1234567, verify.call_args.kwargs['max_bytes'])
        loaded.assert_not_called();backup.assert_not_called();restore.assert_not_called()
        self.assertIn('not approved', out.lower())

    def test_restore_uses_new_directory_without_loading_or_rewriting_config(self):
        with ExitStack() as stack:
            loaded, backup, verify, restore = self.mocks(stack)
            code, out, err = self.invoke(self.argv('restore'))
        self.assertEqual(0, code);self.assertEqual('', err)
        self.assertEqual((self.bundle, SHA, self.output), restore.call_args.args)
        self.assertEqual(1 << 30, restore.call_args.kwargs['max_bytes'])
        loaded.assert_not_called();backup.assert_not_called();verify.assert_not_called()
        self.assertIn(SHA, out);self.assertIn('not approved', out.lower())
        self.assertEqual(self.original, self.config.read_bytes())

    def test_load_and_action_share_one_outer_work_budget(self):
        seen = []
        def load(path):
            seen.append(_current.get());checkpoint();return self.loaded
        def backup(*args, **kwargs):
            seen.append(_current.get());checkpoint()
            self.assertIs(kwargs['budget'], seen[-1])
            return self.manifest, SHA
        with patch.object(CLI, 'load_config', side_effect=load), patch.object(CLI, 'backup', side_effect=backup):
            code, out, err = self.invoke(self.argv())
        self.assertEqual(0, code);self.assertEqual('', err)
        self.assertEqual(2, len(seen));self.assertIs(seen[0], seen[1]);self.assertIsNotNone(seen[0])
        self.assertIsNone(_current.get())

    def test_existing_outer_budget_cannot_be_replaced_by_cli_defaults(self):
        outer = Budget(seconds=10, calls=1, posts=1)
        def action(*args, **kwargs):
            self.assertIs(outer, _current.get());return self.manifest, SHA
        with request_scope(outer), patch.object(CLI, 'load_config', return_value=self.loaded), \
                patch.object(CLI, 'backup', side_effect=action):
            code, out, err = self.invoke(self.argv())
            self.assertIs(outer, _current.get())
        self.assertEqual(0, code);self.assertEqual('', err)
        self.assertIsNone(_current.get())

    def test_known_failures_are_sanitized_and_never_retried(self):
        secret = 'https://dummy:private@invalid.example/?token=never-print-this'
        for error in (OSError(secret), ValueError(secret), RpcError(secret), KeyError(secret),
                      TypeError(secret), RecursionError(secret), sqlite3.DatabaseError(secret), WorkLimit('deadline')):
            for action in ('backup', 'verify', 'restore'):
                with self.subTest(error=type(error).__name__, action=action), ExitStack() as stack:
                    loaded, backup, verify, restore = self.mocks(stack)
                    operation = {'backup': backup, 'verify': verify, 'restore': restore}[action]
                    operation.side_effect = error
                    code, out, err = self.invoke(self.argv(action))
                    self.assertEqual(1, code);self.assertEqual('', out)
                    self.assertNotIn(secret, out+err)
                    self.assertIn('preserve', err.lower());self.assertIn('output', err.lower())
                    self.assertIn('unapproved', err.lower())
                    self.assertEqual(1, operation.call_count)
                    self.assertEqual(self.original, self.config.read_bytes())

    def test_config_loading_failures_do_not_start_any_backup_or_leak_contents(self):
        for error in (ValueError('untrusted-private-json'), OSError('private-path'), RecursionError('private')):
            with self.subTest(error=type(error).__name__), ExitStack() as stack:
                loaded, backup, verify, restore = self.mocks(stack);loaded.side_effect = error
                code, out, err = self.invoke(self.argv())
                self.assertEqual(1, code);self.assertEqual('', out)
                self.assertNotIn(str(error), err)
                backup.assert_not_called();verify.assert_not_called();restore.assert_not_called()

    def test_partial_outputs_are_preserved_after_late_failure(self):
        def incomplete(*args, **kwargs):
            self.output.mkdir();(self.output/'partial.bin').write_bytes(b'preserve this evidence')
            raise OSError('private failure detail')
        with patch.object(CLI, 'load_config', return_value=self.loaded), patch.object(CLI, 'backup', side_effect=incomplete) as backup:
            code, out, err = self.invoke(self.argv())
        self.assertEqual(1, code);self.assertEqual('', out)
        self.assertEqual(1, backup.call_count)
        self.assertEqual(b'preserve this evidence', (self.output/'partial.bin').read_bytes())
        self.assertIn('output', err.lower());self.assertIn('preserve', err.lower())
        self.assertNotIn('private failure detail', err)

    def test_argument_parser_rejects_without_echoing_private_values_and_keeps_valid_control(self):
        private_url = 'https://dummy:PRIVATE_CLI_SENTINEL@invalid.example/path?token=DO_NOT_LOG_CLI_TOKEN'
        samples = (self.argv('backup', '--rpc-url', private_url),
                   self.argv('backup', '--max-seconds', private_url),
                   self.argv('backup', '--max-bytes', private_url),
                   [private_url])
        for args in samples:
            with self.subTest(args=args), ExitStack() as stack:
                operations = self.mocks(stack)
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as rejected:
                    CLI.main(args)
                self.assertEqual(2, rejected.exception.code)
                for operation in operations: operation.assert_not_called()
                self.assertEqual('', out.getvalue())
                self.assertTrue(err.getvalue())
                for secret in (private_url, 'PRIVATE_CLI_SENTINEL', 'DO_NOT_LOG_CLI_TOKEN'):
                    self.assertNotIn(secret, out.getvalue()+err.getvalue())
        with ExitStack() as stack:
            loaded, backup, verify, restore = self.mocks(stack)
            code, out, err = self.invoke(self.argv())
        self.assertEqual(0, code);self.assertEqual('', err)
        loaded.assert_called_once_with(self.config);backup.assert_called_once()
        verify.assert_not_called();restore.assert_not_called()
        self.assertIn(SHA, out);self.assertIn('not approved', out.lower())
        self.assertEqual(self.original, self.config.read_bytes())


if __name__ == '__main__':
    unittest.main()
