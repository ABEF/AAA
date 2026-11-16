"""New offline pre-seal CLI/publication checks; core preparation is injected.

Only argument admission, sanitized reporting, bounded bytes and exclusive local
publication are exercised here. Actual signatures/order/semantics have separate
new core checks. No existing test method or network/signer is used.
"""
from contextlib import redirect_stderr, redirect_stdout
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('preseal_cli_subject', ROOT/'scripts/prepare-preseal.py')
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)
D = CLI.D


class PresealCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='popl-preseal-cli-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'input.json'; self.output = self.root/'new-review.json'
        self.value = {'operator_note': 'Préparer, vérifier, puis examiner'}
        self.original = (json.dumps(self.value, ensure_ascii=False)+'\n').encode('utf-8')
        self.source.write_bytes(self.original)
        self.result = dict(schema=1, status='complete_unsigned_preseal_review_pending_live_verification',
            configuration_inputs_complete=True, build_profile=D.DEFAULT_BUILD_PROFILE,
            manifest_sha256='a'*64, offline_only=True, ready_for_submission=False,
            production_approved=False, transaction_submitted=False, rpc_performed=False,
            simulation_performed=False, authority_verified=False,
            steps=[dict(id='configure:fixed_zzz', unsigned_call_complete=True,
                        conditional_calldata='0x12345678', live_authority_verified=False)])

    def argv(self, **changes):
        fields = {'--input': str(self.source), '--output': str(self.output)}
        fields.update(changes)
        return [item for pair in fields.items() for item in pair]

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err): code = CLI.main(args)
        return code, out.getvalue(), err.getvalue()

    def denied_before_read(self, args, reason=None):
        with patch.object(CLI.P, 'prepare') as prepare, \
                patch.object(Path, 'open', side_effect=AssertionError('No input/artifact read')) as opened:
            code, out, err = self.invoke(args)
        self.assertEqual((1, ''), (code, out))
        report = json.loads(err)
        if reason is not None: self.assertEqual(reason, report['reason'])
        self.assertEqual('input', report['stage'])
        for flag in ('ready_for_submission', 'production_approved', 'transaction_submitted', 'authority_verified'):
            self.assertIs(report[flag], False, flag)
        prepare.assert_not_called(); opened.assert_not_called()
        self.assertEqual(self.original, self.source.read_bytes())
        return report

    def test_both_input_and_new_output_are_required_before_any_read(self):
        for flag in ('--input', '--output'):
            args = self.argv(); i = args.index(flag)
            with self.subTest(flag=flag):
                self.denied_before_read(args[:i]+args[i+2:], 'invalid_cli_arguments')

    def test_execution_key_rpc_root_and_abbreviated_options_are_not_accepted(self):
        for flag in ('--private-key', '--keystore', '--rpc-url', '--sign', '--broadcast', '--deploy',
                     '--seal', '--configure', '--install', '--nonce', '--root', '--in', '--out', '--build'):
            with self.subTest(flag=flag):
                self.denied_before_read(self.argv()+[flag, 'FAKE_ONLY_VALUE'], 'invalid_cli_arguments')

    def test_unknown_build_is_rejected_before_input_or_caller_selected_artifact_reads(self):
        for value in ('', 'unknown', '../caller-artifacts', D.DEFAULT_BUILD_PROFILE+'-fallback'):
            with self.subTest(value=value):
                self.denied_before_read(self.argv(**{'--build-profile': value}), 'unsupported_build_profile')

    def test_parse_errors_never_echo_fake_credentials_or_private_paths(self):
        private = 'https://user:FAKE_ONLY_PASSWORD@provider.invalid/?token=FAKE_ONLY_TOKEN'
        for args in (self.argv()+['--rpc-url', private], self.argv(**{'--build-profile': private}),
                     ['--input', private, '--output']):
            with self.subTest(args=args), patch.object(CLI.P, 'prepare') as prepare:
                code, out, err = self.invoke(args)
                self.assertEqual((1, ''), (code, out)); prepare.assert_not_called()
                for part in (private, 'FAKE_ONLY_PASSWORD', 'FAKE_ONLY_TOKEN'):
                    self.assertNotIn(part, err)

    def test_existing_file_directory_input_alias_and_hardlink_are_preserved(self):
        self.output.write_bytes(b'previous reviewed bytes')
        report = self.denied_before_read(self.argv(), 'existing_output_preserved')
        self.assertTrue(report['output_may_exist'])
        self.assertEqual(b'previous reviewed bytes', self.output.read_bytes())
        folder = self.root/'existing'; folder.mkdir()
        self.denied_before_read(self.argv(**{'--output': str(folder)}), 'existing_output_preserved')
        self.denied_before_read(self.argv(**{'--output': str(self.source)}), 'existing_output_preserved')
        alias = self.root/'linked.json'; os.link(self.source, alias)
        self.denied_before_read(self.argv(**{'--output': str(alias)}), 'existing_output_preserved')
        self.assertTrue(os.path.samefile(self.source, alias)); self.assertEqual(self.original, alias.read_bytes())

    def test_dangling_existing_entry_is_preserved_without_claiming_symlink_privilege(self):
        with patch.object(CLI.os.path, 'lexists', return_value=True):
            report = self.denied_before_read(self.argv(), 'existing_output_preserved')
        self.assertTrue(report['output_may_exist'])

    def test_missing_output_parent_is_not_created_or_replaced(self):
        path = self.root/'missing'/'new-review.json'
        self.denied_before_read(self.argv(**{'--output': str(path)}), 'output_parent_missing')
        self.assertFalse(path.parent.exists())

    def test_input_byte_bound_and_strict_json_reject_before_preparation(self):
        samples = (b'{"schema":1,"schema":2}', b'{"value":1.2}', b'{"value":NaN}',
                   b'{"value":Infinity}', b'\xff', b' '*(D.MAX_INPUT+1))
        for raw in samples:
            with self.subTest(length=len(raw)), patch.object(CLI.P, 'prepare') as prepare:
                self.source.write_bytes(raw)
                code, out, err = self.invoke(self.argv())
                self.assertEqual((1, ''), (code, out)); prepare.assert_not_called()
                self.assertEqual('input', json.loads(err)['stage'])
                self.assertFalse(self.output.exists()); self.assertEqual(raw, self.source.read_bytes())

    def test_complete_review_publishes_exact_bytes_with_no_execution_or_permission_claim(self):
        with patch.object(CLI.P, 'prepare', return_value=self.result) as prepare:
            code, out, err = self.invoke(self.argv())
        self.assertEqual((0, ''), (code, err))
        prepare.assert_called_once_with(self.value, build_profile=D.DEFAULT_BUILD_PROFILE)
        self.assertEqual(D.render(self.result), self.output.read_bytes())
        report = json.loads(out)
        self.assertTrue(report['artifact_created']); self.assertTrue(report['configuration_inputs_complete'])
        for flag in ('ready_for_submission', 'production_approved', 'transaction_submitted', 'authority_verified'):
            self.assertIs(report[flag], False, flag)
        self.assertEqual(self.original, self.source.read_bytes())

    def test_unknown_inputs_publish_only_blocked_review_without_filled_call_data(self):
        result = copy.deepcopy(self.result)
        result.update(configuration_inputs_complete=False, status='blocked_preview_missing_inputs',
                      missing_inputs=['settings.dual_usd', 'bootstrap'])
        result['steps'] = [dict(id='configure:dual_usd', unsigned_call_complete=False, conditional_calldata=None)]
        with patch.object(CLI.P, 'prepare', return_value=result): code, out, err = self.invoke(self.argv())
        self.assertEqual((2, ''), (code, err))
        self.assertFalse(json.loads(out)['configuration_inputs_complete'])
        self.assertEqual(result, json.loads(self.output.read_bytes()))
        self.assertIsNone(json.loads(self.output.read_bytes())['steps'][0]['conditional_calldata'])

    def test_utf8_and_explicit_trusted_build_are_forwarded_without_relabeling(self):
        with patch.object(CLI.P, 'prepare', return_value=self.result) as prepare:
            code, _out, err = self.invoke(self.argv(**{'--build-profile': D.DEFAULT_BUILD_PROFILE}))
        self.assertEqual((0, ''), (code, err))
        prepare.assert_called_once_with(self.value, build_profile=D.DEFAULT_BUILD_PROFILE)
        self.assertEqual('Préparer, vérifier, puis examiner', json.loads(self.source.read_bytes())['operator_note'])

    def test_malformed_or_inconsistent_internal_result_is_not_published(self):
        cases = [('configuration_inputs_complete', 1), ('status', 'approved'), ('offline_only', False),
                 ('build_profile', 'unreviewed'), ('manifest_sha256', None)]
        cases.extend((flag, True) for flag in ('ready_for_submission', 'production_approved',
            'transaction_submitted', 'rpc_performed', 'simulation_performed', 'authority_verified'))
        for field, value in cases:
            result = copy.deepcopy(self.result); result[field] = value
            with self.subTest(field=field), patch.object(CLI.P, 'prepare', return_value=result):
                code, out, err = self.invoke(self.argv())
                self.assertEqual((1, ''), (code, out))
                self.assertEqual('offline_preseal_preparation', json.loads(err)['stage'])
                self.assertFalse(self.output.exists())

    def test_known_preparation_error_retains_only_typed_reason(self):
        with patch.object(CLI.P, 'prepare', side_effect=D.PlanError('preseal_setting_mismatch')):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertEqual('preseal_setting_mismatch', report['reason'])
        self.assertEqual('offline_preseal_preparation', report['stage'])
        self.assertFalse(report['output_may_exist']); self.assertFalse(self.output.exists())

    def test_unexpected_input_or_core_error_never_discloses_fake_secret(self):
        with patch.object(Path, 'open', side_effect=OSError('FAKE_ONLY_SECRET/private-input')):
            code, out, err = self.invoke(self.argv())
        self.assertEqual((1, ''), (code, out)); self.assertEqual('input', json.loads(err)['stage'])
        self.assertNotIn('FAKE_ONLY_SECRET', err)
        with patch.object(CLI.P, 'prepare', side_effect=ValueError('FAKE_ONLY_SECRET/provider')):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertEqual('offline_preseal_unavailable', report['reason'])
        self.assertNotIn('FAKE_ONLY_SECRET', err); self.assertFalse(report['output_may_exist'])

    def test_existing_output_render_bound_is_not_raised_for_preseal_review(self):
        result = copy.deepcopy(self.result); result['oversized'] = 'x'*D.MAX_OUTPUT
        with patch.object(CLI.P, 'prepare', return_value=result): code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertEqual('output_size', report['reason'])
        self.assertEqual('rendering', report['stage']); self.assertFalse(report['output_may_exist'])
        self.assertFalse(self.output.exists())

    def test_late_publication_error_preserves_complete_unapproved_artifact(self):
        writer = D.write_exclusive
        def late(path, raw):
            writer(path, raw)
            raise OSError('FAKE_ONLY_SECRET late publication detail')
        with patch.object(CLI.P, 'prepare', return_value=self.result), patch.object(CLI.D, 'write_exclusive', side_effect=late):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertTrue(report['output_may_exist'])
        self.assertEqual('publication_uncertain', report['reason']); self.assertEqual('publication', report['stage'])
        self.assertNotIn('FAKE_ONLY_SECRET', err); self.assertEqual(D.render(self.result), self.output.read_bytes())
        self.assertEqual(self.original, self.source.read_bytes())

    def test_racing_publication_cannot_replace_another_review(self):
        writer = D.write_exclusive
        def collision(path, raw):
            path.write_bytes(b'another complete review')
            writer(path, raw)
        with patch.object(CLI.P, 'prepare', return_value=self.result), patch.object(CLI.D, 'write_exclusive', side_effect=collision):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertTrue(report['output_may_exist'])
        self.assertEqual('publication_uncertain', report['reason'])
        self.assertEqual(b'another complete review', self.output.read_bytes())
        self.assertEqual(self.original, self.source.read_bytes())

    def test_help_has_only_unsigned_offline_inputs_and_does_not_prepare(self):
        out = io.StringIO()
        with patch.object(CLI.P, 'prepare') as prepare, redirect_stdout(out), self.assertRaises(SystemExit) as exited:
            CLI.main(['--help'])
        self.assertEqual(0, exited.exception.code); prepare.assert_not_called()
        for value in ('--input', '--output', '--build-profile'): self.assertIn(value, out.getvalue())
        for value in ('--private-key', '--rpc-url', '--broadcast', '--seal', '--nonce'):
            self.assertNotIn(value, out.getvalue())


if __name__ == '__main__':
    unittest.main()
