"""Keeper CI selection must include its regressions without running them twice."""
import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('keeper_test_runner', ROOT / 'scripts/run-keeper-tests.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class KeeperRunnerInventoryTests(unittest.TestCase):
    def test_every_keeper_test_module_is_selected(self):
        required = {path.stem for path in (ROOT / 'tests_python').glob('test_keeper*.py')}
        required.update({'test_metadata_keeper', 'test_royalty_keeper',
                         'test_typed_v4_conversion_keeper', 'test_lp_conversion',
                         'test_rpc', 'test_rpc_integrity', 'test_state', 'test_staging_monitor',
                         'test_state_json_integrity',
                         'test_reference_confirmation_v2'})
        self.assertEqual(set(RUNNER.MODULES), required)
        self.assertEqual(len(RUNNER.MODULES), len(required))

    def fixture(self):
        module = types.ModuleType('tests_python.test_keeper_selection_fixture')
        # Imported fixture classes must not execute again in their importing module.
        module.Foreign = type('Foreign', (unittest.TestCase,), {
            '__module__': 'tests_python.some_other_fixture', 'test_imported': lambda self: None})
        module.Own = type('Own', (unittest.TestCase,), {
            '__module__': module.__name__, 'test_second': lambda self: None,
            'test_first': lambda self: None})
        return module

    def test_only_defined_classes_selected_and_aliases_not_duplicated(self):
        module = self.fixture()
        module.Alias = module.Own
        tests, classes = RUNNER.select_tests(('test_keeper_selection_fixture',), lambda _: module)
        self.assertEqual(classes, [module.__name__ + '.Own'])
        self.assertEqual(list(tests), [module.__name__ + '.Own.test_first',
                                      module.__name__ + '.Own.test_second'])

    def test_duplicate_module_fails_closed(self):
        module = self.fixture()
        with self.assertRaisesRegex(ValueError, 'repeated keeper module'):
            RUNNER.select_tests(('test_keeper_selection_fixture',) * 2, lambda _: module)

    def test_foreign_import_does_not_make_empty_selection_successful(self):
        module = self.fixture()
        del module.Own
        with self.assertRaisesRegex(ValueError, 'defines no test methods'):
            RUNNER.select_tests(('test_keeper_selection_fixture',), lambda _: module)

    def test_duplicate_method_identity_fails_even_without_python_assertions(self):
        module = self.fixture()
        module.Second = type('Own', (unittest.TestCase,), {
            '__module__': module.__name__, 'test_first': lambda self: None})
        with self.assertRaisesRegex(ValueError, 'Repeated keeper test identity'):
            RUNNER.select_tests(('test_keeper_selection_fixture',), lambda _: module)

    def test_wrong_import_identity_fails_closed(self):
        with self.assertRaises(ValueError):
            RUNNER.select_tests(('different_fixture',), lambda _: self.fixture())

    def test_import_failure_is_not_silently_skipped(self):
        def fail(_):
            raise ImportError('inert missing selected module')
        with self.assertRaises(ImportError):
            RUNNER.select_tests(('fixture',), fail)

    def test_real_selection_has_unique_defined_method_ids_without_execution(self):
        tests, classes = RUNNER.select_tests()
        self.assertTrue(tests)
        self.assertEqual(len(classes), len(set(classes)))
        self.assertEqual(list(tests), [test.id() for test in tests.values()])
        self.assertEqual(set(RUNNER.MODULES),
                         {name.split('.')[1] for name in classes})
        for identity, test in tests.items():
            self.assertEqual('.'.join(identity.split('.')[:-2]), test.__class__.__module__)

    def test_list_cli_writes_inventory_without_executing_selected_methods(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'inventory.json'
            arguments = ['run-keeper-tests.py', '--list', '--output', str(output)]
            with patch.object(sys, 'argv', arguments), patch('sys.stdout', new_callable=io.StringIO), \
                    patch('unittest.TextTestRunner.run', side_effect=AssertionError('must not execute')), \
                    self.assertRaises(SystemExit) as exited:
                runpy.run_path(str(ROOT / 'scripts/run-keeper-tests.py'), run_name='__main__')
            self.assertEqual(exited.exception.code, 0)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertTrue(report['successful'])
            self.assertFalse(report['execution_performed'])
            self.assertEqual(report['tests_run'], 0)
            self.assertEqual(report['executed_methods'], [])
            self.assertTrue(report['selected_methods'])
            self.assertEqual(set(report['modules']), set(RUNNER.MODULES))
