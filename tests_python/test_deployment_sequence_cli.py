"""New offline sequence CLI/publication contracts; no old test body executes.

Constructor preparation is injected here. Core integration/address arithmetic
is exercised separately; these checks cover strict inputs, public-only options,
bounded parsing/rendering and exclusive local artifact publication.
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
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
SPEC = importlib.util.spec_from_file_location(
    'deployment_sequence_cli_subject', ROOT/'scripts/prepare-deployment-sequence.py')
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)
D = CLI.D
DEPLOYER = '0x'+'ab'*20


class DeploymentSequenceCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='popl-deployment-sequence-cli-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'input.json'
        self.value = {'greeting': 'Revue étudiée'}
        self.original = (json.dumps(self.value, ensure_ascii=False)+'\n').encode('utf-8')
        self.source.write_bytes(self.original)
        self.output = self.root/'new-sequence.json'
        self.result = dict(schema=1, status='offline_sequence_and_top_level_payloads_complete_pending_live_verification',
            build_profile=D.DEFAULT_BUILD_PROFILE, manifest_sha256='a'*64,
            offline_only=True, ready_for_submission=False, production_approved=False,
            transaction_submitted=False, nonce_reserved=False,
            constructor_plan=dict(input_assignments_complete=True, top_level_constructor_payloads_complete=True))

    def argv(self, **changes):
        fields = {'--input': str(self.source), '--deployer': DEPLOYER,
                  '--starting-nonce': '0', '--output': str(self.output)}
        fields.update(changes)
        return [item for pair in fields.items() for item in pair]

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = CLI.main(args)
        return code, out.getvalue(), err.getvalue()

    def denied_before_read(self, args, reason=None):
        with patch.object(CLI.S, 'prepare') as prepare, \
                patch.object(Path, 'open', side_effect=AssertionError('No input or artifact read')) as opened:
            code, out, err = self.invoke(args)
        self.assertEqual(1, code); self.assertEqual('', out)
        report = json.loads(err)
        if reason is not None: self.assertEqual(reason, report['reason'])
        self.assertEqual('input', report['stage'])
        self.assertFalse(report['ready_for_submission'])
        self.assertFalse(report['transaction_submitted'])
        prepare.assert_not_called(); opened.assert_not_called()
        self.assertEqual(self.original, self.source.read_bytes())
        return report

    def test_each_required_public_input_is_explicit_before_any_read(self):
        for flag in ('--input', '--deployer', '--starting-nonce', '--output'):
            args = self.argv(); index = args.index(flag)
            with self.subTest(flag=flag):
                self.denied_before_read(args[:index]+args[index+2:], 'invalid_cli_arguments')

    def test_no_key_signer_rpc_nonce_reservation_deploy_or_seal_switch_exists(self):
        for flag in ('--private-key', '--keystore', '--rpc-url', '--sign', '--broadcast',
                     '--deploy', '--seal', '--reserve-nonce', '--install', '--root'):
            with self.subTest(flag=flag):
                self.denied_before_read(self.argv()+[flag, 'not-a-real-secret'], 'invalid_cli_arguments')

    def test_bad_sender_spellings_and_zero_are_rejected_before_reading_input(self):
        for value in ('', '0x'+'0'*40, 'ab'*20, '0x'+'a'*39, '0x'+'gg'*20, 'https://invalid.test'):
            with self.subTest(value=value): self.denied_before_read(self.argv(**{'--deployer': value}))

    def test_nonce_requires_a_bounded_canonical_decimal_string(self):
        for value in ('', '00', '-1', '+1', '0x1', '1.0', '1e3', '1\n', '٠١', str(1 << 64)):
            with self.subTest(value=value): self.denied_before_read(self.argv(**{'--starting-nonce': value}))

    def test_unknown_build_never_opens_caller_selected_paths_or_falls_back(self):
        for value in ('unknown', '../arbitrary', '', D.DEFAULT_BUILD_PROFILE+'-fallback'):
            with self.subTest(value=value):
                self.denied_before_read(self.argv(**{'--build-profile': value}), 'unsupported_build_profile')

    def test_invalid_arguments_never_echo_fake_credentials_or_tokens(self):
        secret = 'https://user:FAKE_ONLY_SECRET@provider.invalid/path?token=FAKE_ONLY_TOKEN'
        samples = [self.argv()+['--rpc-url', secret], self.argv(**{'--deployer': secret}),
                   self.argv(**{'--starting-nonce': secret}), self.argv(**{'--build-profile': secret})]
        for args in samples:
            with self.subTest(args=args), patch.object(CLI.S, 'prepare') as prepare:
                code, out, err = self.invoke(args)
                self.assertEqual(1, code); self.assertEqual('', out)
                self.assertNotIn('FAKE_ONLY_SECRET', err); self.assertNotIn('FAKE_ONLY_TOKEN', err)
                self.assertNotIn(secret, err); prepare.assert_not_called()

    def test_existing_file_directory_or_input_alias_is_preserved_before_read(self):
        self.output.write_bytes(b'preserve original review')
        report = self.denied_before_read(self.argv(), 'existing_output_preserved')
        self.assertTrue(report['output_may_exist'])
        self.assertEqual(b'preserve original review', self.output.read_bytes())
        folder = self.root/'existing-directory'; folder.mkdir()
        self.denied_before_read(self.argv(**{'--output': str(folder)}), 'existing_output_preserved')
        self.denied_before_read(self.argv(**{'--output': str(self.source)}), 'existing_output_preserved')

    def test_dangling_entry_is_preserved_even_when_exists_would_be_false(self):
        # Portable entry-presence injection; this does not claim real symlink privilege.
        with patch.object(CLI.os.path, 'lexists', return_value=True):
            report = self.denied_before_read(self.argv(), 'existing_output_preserved')
        self.assertTrue(report['output_may_exist'])

    def test_hardlinked_output_cannot_overwrite_its_input_inode(self):
        os.link(self.source, self.output)
        self.assertTrue(os.path.samefile(self.source, self.output))
        self.denied_before_read(self.argv(), 'existing_output_preserved')
        self.assertEqual(self.original, self.output.read_bytes())

    def test_missing_output_parent_is_not_created_and_input_remains_unchanged(self):
        output = self.root/'missing-parent'/'new.json'
        self.denied_before_read(self.argv(**{'--output': str(output)}), 'output_parent_missing')
        self.assertFalse(output.parent.exists())

    def test_bounded_json_duplicate_fraction_nonfinite_and_bad_utf8_fail_before_prepare(self):
        variants = (b'{"schema":1,"schema":1}', b'{"amount":1.2}', b'{"amount":NaN}',
                    b'\xff', b' '*(D.MAX_INPUT+1))
        for raw in variants:
            with self.subTest(raw_length=len(raw)), patch.object(CLI.S, 'prepare') as prepare:
                self.source.write_bytes(raw)
                code, out, err = self.invoke(self.argv())
                self.assertEqual(1, code); self.assertEqual('', out)
                self.assertEqual('input', json.loads(err)['stage'])
                self.assertFalse(self.output.exists()); prepare.assert_not_called()
                self.assertEqual(raw, self.source.read_bytes())

    def test_complete_result_publishes_exact_review_without_any_execution_authority(self):
        with patch.object(CLI.S, 'prepare', return_value=self.result) as prepare:
            code, out, err = self.invoke(self.argv())
        self.assertEqual((0, ''), (code, err))
        prepare.assert_called_once_with(self.value, DEPLOYER, '0', build_profile=D.DEFAULT_BUILD_PROFILE)
        self.assertEqual(D.render(self.result), self.output.read_bytes())
        summary = json.loads(out)
        self.assertTrue(summary['artifact_created']); self.assertTrue(summary['offline_only'])
        for flag in ('ready_for_submission','production_approved','transaction_submitted','nonce_reserved'):
            self.assertIs(summary[flag], False, flag)
        self.assertEqual(self.result['manifest_sha256'], summary['manifest_sha256'])
        self.assertEqual(self.original, self.source.read_bytes())

    def test_utf8_and_explicit_closed_build_are_forwarded_without_silent_relabeling(self):
        result = copy.deepcopy(self.result); result['build_profile'] = D.LEGACY_BUILD_PROFILE
        sender = '0x'+'AB'*20
        with patch.object(CLI.S, 'prepare', return_value=result) as prepare:
            code, _out, err = self.invoke(self.argv(**{'--deployer': sender, '--starting-nonce': '127',
                                                       '--build-profile': D.LEGACY_BUILD_PROFILE}))
        self.assertEqual((0, ''), (code, err))
        prepare.assert_called_once_with(self.value, sender, '127', build_profile=D.LEGACY_BUILD_PROFILE)
        self.assertEqual('Revue étudiée', json.loads(self.source.read_bytes())['greeting'])

    def test_missing_constructor_or_assignment_inputs_publish_only_a_blocked_preview(self):
        for n, flag in enumerate(('input_assignments_complete','top_level_constructor_payloads_complete')):
            result = copy.deepcopy(self.result); result['constructor_plan'][flag] = False
            result['status'] = 'blocked_preview_missing_inputs'
            output = self.root/f'preview-{n}.json'
            with self.subTest(flag=flag), patch.object(CLI.S, 'prepare', return_value=result):
                code, out, err = self.invoke(self.argv(**{'--output': str(output)}))
            self.assertEqual((2, ''), (code, err))
            self.assertFalse(json.loads(out)['ready_for_submission'])
            self.assertEqual(result, json.loads(output.read_bytes()))

    def test_known_preparation_error_has_typed_reason_without_output(self):
        with patch.object(CLI.S, 'prepare', side_effect=D.PlanError('planned_address_mismatch')):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out))
        self.assertEqual('planned_address_mismatch', report['reason'])
        self.assertEqual('offline_sequence_preparation', report['stage'])
        self.assertFalse(report['output_may_exist']); self.assertFalse(self.output.exists())

    def test_unexpected_preparation_error_is_sanitized_and_never_published(self):
        for error in (OSError('FAKE_ONLY_SECRET/path'), ValueError('FAKE_ONLY_SECRET/provider')):
            with self.subTest(error=type(error).__name__), patch.object(CLI.S, 'prepare', side_effect=error):
                code, out, err = self.invoke(self.argv())
                report = json.loads(err)
                self.assertEqual((1, ''), (code, out))
                self.assertEqual('offline_sequence_unavailable', report['reason'])
                self.assertNotIn('FAKE_ONLY_SECRET', err)
                self.assertFalse(report['output_may_exist']); self.assertFalse(self.output.exists())

    def test_render_bound_is_not_raised_for_the_wrapped_constructor_plan(self):
        result = copy.deepcopy(self.result); result['oversized'] = 'x'*D.MAX_OUTPUT
        with patch.object(CLI.S, 'prepare', return_value=result):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertEqual('output_size', report['reason'])
        self.assertEqual('rendering', report['stage'])
        self.assertFalse(report['output_may_exist']); self.assertFalse(self.output.exists())

    def test_late_publication_error_preserves_complete_artifact_and_reports_uncertainty(self):
        writer = D.write_exclusive
        def late(path, raw):
            writer(path, raw)
            raise OSError('FAKE_ONLY_SECRET late reporting detail')
        with patch.object(CLI.S, 'prepare', return_value=self.result), patch.object(CLI.D, 'write_exclusive', side_effect=late):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertTrue(report['output_may_exist'])
        self.assertEqual('publication_uncertain', report['reason'])
        self.assertEqual('publication', report['stage']); self.assertNotIn('FAKE_ONLY_SECRET', err)
        self.assertEqual(D.render(self.result), self.output.read_bytes())
        self.assertEqual(self.original, self.source.read_bytes())

    def test_publication_collision_after_preflight_cannot_replace_another_artifact(self):
        writer = D.write_exclusive
        def collision(path, raw):
            path.write_bytes(b'other reviewed artifact')
            writer(path, raw)
        with patch.object(CLI.S, 'prepare', return_value=self.result), patch.object(CLI.D, 'write_exclusive', side_effect=collision):
            code, out, err = self.invoke(self.argv())
        report = json.loads(err)
        self.assertEqual((1, ''), (code, out)); self.assertTrue(report['output_may_exist'])
        self.assertEqual('publication_uncertain', report['reason'])
        self.assertEqual(b'other reviewed artifact', self.output.read_bytes())
        self.assertEqual([], list(self.root.glob('.deployment-plan-*')))

    def test_help_documents_only_offline_inputs_and_does_no_preparation(self):
        out = io.StringIO()
        with patch.object(CLI.S, 'prepare') as prepare, redirect_stdout(out), self.assertRaises(SystemExit) as exited:
            CLI.main(['--help'])
        self.assertEqual(0, exited.exception.code); prepare.assert_not_called()
        self.assertIn('--deployer', out.getvalue()); self.assertIn('--starting-nonce', out.getvalue())
        for token in ('--private-key','--rpc-url','--broadcast','--seal'):
            self.assertNotIn(token, out.getvalue())


if __name__ == '__main__':
    unittest.main()
