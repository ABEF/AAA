"""Inert evidence admission: no project suite, RPC, signer or services are run."""
from contextlib import redirect_stdout
import importlib
import importlib.util
import io
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def subject(name):
    spec = importlib.util.spec_from_file_location('evidence_subject_'+name.replace('.', '_'), ROOT/'scripts'/name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inert_module(name, bodies):
    module = types.ModuleType(name)
    module.Sentinel = type('Sentinel', (unittest.TestCase,), {
        '__module__': name, 'test_inert': lambda self: bodies.append(name)})
    return module


class VerificationOutputOwnershipTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.output = self.directory/'evidence.json'

    def test_keeper_existing_output_is_preserved_before_import_or_test_work(self):
        self.output.write_bytes(b'ORIGINAL EVIDENCE\n')
        self.output.with_suffix('.log').write_bytes(b'ORIGINAL LOG\n')
        bodies = []
        original = importlib.import_module
        def importer(name, *args, **kwargs):
            return inert_module(name, bodies) if name.startswith('tests_python.') else original(name, *args, **kwargs)
        with patch.object(sys, 'argv', ['keeper', '--output', str(self.output)]), \
                patch('importlib.import_module', side_effect=importer) as imports, redirect_stdout(io.StringIO()):
            try:
                runpy.run_path(str(ROOT/'scripts/run-keeper-tests.py'), run_name='__main__')
            except (FileExistsError, ValueError, SystemExit):
                pass
        self.assertEqual(b'ORIGINAL EVIDENCE\n', self.output.read_bytes())
        self.assertEqual(b'ORIGINAL LOG\n', self.output.with_suffix('.log').read_bytes())
        self.assertFalse(bodies)
        self.assertFalse(any(call.args[0].startswith('tests_python.') for call in imports.call_args_list))

    def test_python_runner_reserves_nonpass_pair_before_test_module_discovery(self):
        runner = subject('run_python_tests.py')
        bodies = []
        def select():
            self.assertTrue(self.output.is_file())
            self.assertTrue(self.output.with_suffix('.log').is_file())
            marker = json.loads(self.output.read_text(encoding='utf-8'))
            self.assertEqual('in_progress', marker['evidence_status'])
            self.assertIs(marker['successful'], False)
            module = inert_module('tests_python.test_admission_sentinel', bodies)
            return runner.select_original(('test_admission_sentinel',), lambda _: module)
        runner.select_original = runner.select_tests
        with patch.object(runner, 'select_tests', side_effect=select), patch.object(runner, 'inputs', return_value={}), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(0, runner.main(['--output', str(self.output)]))
        self.assertEqual(['tests_python.test_admission_sentinel'], bodies)
        result = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual('complete', result['evidence_status'])
        self.assertEqual(result['selected_methods'], result['executed_methods'])

    def test_source_checks_refuse_existing_output_before_scanning(self):
        runner = subject('source_checks.py')
        self.output.write_bytes(b'ORIGINAL SOURCE EVIDENCE\n')
        source = self.directory/'src'
        source.mkdir()
        (source/'Tiny.sol').write_text('pragma solidity 0.8.26; contract Tiny {}', encoding='utf-8')
        with patch.object(runner, 'ROOT', self.directory), redirect_stdout(io.StringIO()):
            try:
                runner.main(['--output', str(self.output)])
            except (FileExistsError, ValueError):
                pass
        self.assertEqual(b'ORIGINAL SOURCE EVIDENCE\n', self.output.read_bytes())

    def test_keeper_fresh_admission_and_order_are_visible_to_inert_module_imports(self):
        bodies, imported = [], []
        original = importlib.import_module
        def importer(name, *args, **kwargs):
            if not name.startswith('tests_python.'):
                return original(name, *args, **kwargs)
            imported.append(name)
            marker = json.loads(self.output.read_text(encoding='utf-8'))
            self.assertEqual('in_progress', marker['evidence_status'])
            self.assertFalse(marker['successful'])
            self.assertTrue(self.output.with_suffix('.log').is_file())
            return inert_module(name, bodies)
        with patch.object(sys, 'argv', ['keeper', '--output', str(self.output)]), \
                patch('importlib.import_module', side_effect=importer), redirect_stdout(io.StringIO()), \
                self.assertRaises(SystemExit) as exited:
            runpy.run_path(str(ROOT/'scripts/run-keeper-tests.py'), run_name='__main__')
        self.assertEqual(0, exited.exception.code)
        report = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(imported, bodies)
        self.assertEqual(report['selected_methods'], report['executed_methods'])
        self.assertEqual(len(imported), report['tests_run'])

    def test_import_failure_leaves_nonpass_marker_without_running_a_test(self):
        runner = subject('run_python_tests.py')
        with patch.object(runner, 'select_tests', side_effect=ImportError('PRIVATE INPUT DO NOT ECHO')), \
                patch('unittest.TextTestRunner.run') as run, self.assertRaises(ImportError):
            runner.main(['--output', str(self.output)])
        run.assert_not_called()
        report = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertFalse(report['successful'])
        self.assertEqual('failed', report['evidence_status'])
        self.assertNotIn('PRIVATE INPUT', json.dumps(report))

    def test_source_default_creates_distinct_outputs_and_preserves_legacy_file(self):
        runner = subject('source_checks.py')
        reports = self.directory/'reports'
        reports.mkdir()
        old = reports/'source-checks.json'
        old.write_bytes(b'KEEP ORIGINAL DIRTY REPORT\n')
        (self.directory/'src').mkdir()
        (self.directory/'src/Tiny.sol').write_text('pragma solidity 0.8.26; contract Tiny {}', encoding='utf-8')
        with patch.object(runner, 'ROOT', self.directory), patch.object(runner, 'EXPECTED', []), \
                patch.object(runner, 'HELPERS', []), redirect_stdout(io.StringIO()):
            self.assertFalse(runner.main([]))
            self.assertFalse(runner.main([]))
        self.assertEqual(b'KEEP ORIGINAL DIRTY REPORT\n', old.read_bytes())
        fresh = [p for p in reports.glob('source-checks-*.json')]
        self.assertEqual(2, len(fresh))
        self.assertTrue(all(json.loads(p.read_text())['evidence_status'] == 'complete' for p in fresh))

    def test_keeper_selector_rejects_unreviewed_custom_loader(self):
        runner = subject('run-keeper-tests.py')
        module = inert_module('tests_python.test_admission_sentinel', [])
        module.load_tests = lambda *args: None
        with self.assertRaises(ValueError):
            runner.select_tests(('test_admission_sentinel',), lambda _: module)

    def selection_mutation(self, script):
        runner = subject(script)
        imported_source = self.directory/'lazy_fixture.py'
        imported_source.write_bytes(b'original before selected import\n')
        bodies = []
        module = inert_module('tests_python.test_provenance_sentinel', bodies)
        selected = runner.select_tests(('test_provenance_sentinel',), lambda _: module)
        def pins():
            return {'scripts/lazy_fixture.py': hashlib.sha256(imported_source.read_bytes()).hexdigest()}
        before = pins()
        def importing():
            imported_source.write_bytes(b'changed while selecting/importing tests\n')
            return selected
        with patch.object(runner, 'select_tests', side_effect=importing), patch.object(runner, 'inputs', side_effect=pins), \
                redirect_stdout(io.StringIO()):
            status = runner.main(['--output', str(self.output)])
        report = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(1, status)
        self.assertFalse(report['successful'])
        self.assertEqual(before, report['source_sha256_before'])
        self.assertEqual(['scripts/lazy_fixture.py'], report['source_changes_during_run'])
        self.assertEqual(report['selected_methods'], report['executed_methods'])
        self.assertEqual(['tests_python.test_provenance_sentinel'], bodies)

    def test_python_import_time_source_change_is_not_pinned_as_an_unchanged_pass(self):
        self.selection_mutation('run_python_tests.py')

    def test_keeper_import_time_source_change_is_not_pinned_as_an_unchanged_pass(self):
        self.selection_mutation('run-keeper-tests.py')

    def test_keeper_inventory_pins_lazy_script_helpers_outside_loaded_module_names(self):
        scripts = self.directory/'scripts'
        scripts.mkdir()
        original = ROOT/'scripts/run-keeper-tests.py'
        copied = scripts/'run-keeper-tests.py'
        copied.write_bytes(original.read_bytes())
        (scripts/'rehearse-keeper.py').write_text('# inert required fixture\n', encoding='utf-8')
        lazy = scripts/'helper_not_loaded_in_sys_modules.py'
        lazy.write_text('# inert lazy helper\n', encoding='utf-8')
        (self.directory/'keeper/rehearsal').mkdir(parents=True)
        (self.directory/'keeper/rehearsal/KeeperVenue.sol').write_text('// inert source pin\n', encoding='utf-8')
        (self.directory/'keeper/staging.py').write_text('# inert staging source pin\n', encoding='utf-8')
        spec = importlib.util.spec_from_file_location('unprefixed_copied_runner', copied)
        runner = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'path', list(sys.path)):
            spec.loader.exec_module(runner)
            pinned = runner.inputs()
        self.assertIn('scripts/helper_not_loaded_in_sys_modules.py', pinned)
        self.assertEqual(hashlib.sha256(lazy.read_bytes()).hexdigest(), pinned['scripts/helper_not_loaded_in_sys_modules.py'])


class EvidenceAdmissionTests(unittest.TestCase):
    def setUp(self):
        from zzz_ops.evidence import Evidence
        self.Evidence = Evidence
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.output = self.directory/'evidence.json'

    def test_existing_json_or_log_or_directory_refuses_all_work(self):
        for target, directory in ((self.output, False), (self.output.with_suffix('.log'), False), (self.output, True)):
            with self.subTest(target=target.name, directory=directory):
                if directory:
                    target.mkdir()
                else:
                    target.write_bytes(b'UNCHANGED')
                with self.assertRaises((FileExistsError, ValueError, IsADirectoryError)):
                    with self.Evidence(self.output, with_log=True):
                        self.fail('work must not start')
                if directory:
                    target.rmdir()
                else:
                    self.assertEqual(b'UNCHANGED', target.read_bytes())
                    target.unlink()

    def test_live_and_dangling_symlinks_are_refused_without_following_them(self):
        for dangling in (False, True):
            target = self.directory/('missing' if dangling else 'original')
            if not dangling:
                target.write_bytes(b'UNCHANGED TARGET')
            try:
                self.output.symlink_to(target)
            except OSError:
                self.skipTest('Symlink creation unavailable on this host')
            try:
                with self.assertRaises((FileExistsError, ValueError)):
                    with self.Evidence(self.output):
                        self.fail('symlink must not admit work')
                if not dangling:
                    self.assertEqual(b'UNCHANGED TARGET', target.read_bytes())
            finally:
                self.output.unlink()

    def test_log_reservation_race_preserves_the_winner_and_marks_owned_json_failed(self):
        from zzz_ops import evidence
        original = evidence.os.open
        competitor = self.output.with_suffix('.log')
        def raced(path, flags, *args, **kwargs):
            if Path(path) == competitor and flags & os.O_EXCL:
                competitor.write_bytes(b'RACE WINNER')
            return original(path, flags, *args, **kwargs)
        with patch.object(evidence.os, 'open', side_effect=raced), self.assertRaises(FileExistsError):
            with self.Evidence(self.output, with_log=True):
                self.fail('race collision must prevent work')
        self.assertEqual(b'RACE WINNER', competitor.read_bytes())
        marker = json.loads(self.output.read_text())
        self.assertFalse(marker['successful'])
        self.assertEqual('failed', marker['evidence_status'])

    def test_interrupted_producer_retains_partial_log_and_a_nonpass_marker(self):
        with self.assertRaises(KeyboardInterrupt):
            with self.Evidence(self.output, with_log=True) as output:
                output.log.write('partial inert diagnostic\n')
                raise KeyboardInterrupt('PRIVATE INPUT')
        marker = json.loads(self.output.read_text())
        self.assertFalse(marker['successful'])
        self.assertEqual('interrupted', marker['evidence_status'])
        self.assertNotIn('PRIVATE INPUT', json.dumps(marker))
        self.assertIn('partial inert diagnostic', self.output.with_suffix('.log').read_text())

    def test_failed_check_is_complete_evidence_and_never_becomes_a_pass(self):
        with self.Evidence(self.output, with_log=True) as output:
            output.log.write('inert failed check\n')
            output.finish({'successful': False, 'tests_run': 1, 'failures': 1})
        marker = json.loads(self.output.read_text())
        self.assertFalse(marker['successful'])
        self.assertEqual('complete', marker['evidence_status'])

    def test_nonfinite_final_payload_is_not_written_as_successful_evidence(self):
        with self.assertRaises(ValueError):
            with self.Evidence(self.output) as output:
                output.finish({'successful': True, 'amount': float('nan')})
        self.assertFalse(json.loads(self.output.read_text())['successful'])

    def test_final_writes_never_clobber_a_replacement_path(self):
        with self.assertRaises((OSError, ValueError)):
            with self.Evidence(self.output, with_log=True) as output:
                try:
                    self.output.unlink()
                except PermissionError:
                    self.skipTest('Host prohibits replacing an open evidence file')
                self.output.write_bytes(b'REPLACEMENT OWNER')
                output.finish({'successful': True})
        self.assertEqual(b'REPLACEMENT OWNER', self.output.read_bytes())

    def test_missing_final_report_or_zero_system_exit_cannot_return_success(self):
        for explicit_exit in (False, True):
            with self.subTest(explicit_exit=explicit_exit), self.assertRaises(RuntimeError):
                with self.Evidence(self.output) as output:
                    if explicit_exit:
                        raise SystemExit(0)
            self.assertFalse(json.loads(self.output.read_text())['successful'])
            self.output.unlink()

    def test_reserved_marker_is_synced_before_work_and_utf8_success_is_owned(self):
        from zzz_ops import evidence
        with patch.object(evidence.os, 'fsync', wraps=evidence.os.fsync) as sync:
            with self.Evidence(self.output, with_log=True) as output:
                self.assertGreater(sync.call_count, 0)
                self.assertFalse(json.loads(self.output.read_text())['successful'])
                output.log.write('Café λ\n')
                self.assertEqual('Café λ\n', output.read_log())
                output.finish({'successful': True, 'label': 'Café λ'})
        self.assertTrue(json.loads(self.output.read_text(encoding='utf-8'))['successful'])
        self.assertEqual('Café λ\n', self.output.with_suffix('.log').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
