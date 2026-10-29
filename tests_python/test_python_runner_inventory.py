"""Full verification must select canonical, defined test cases once."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('full_python_runner', ROOT/'scripts/run_python_tests.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PythonRunnerInventoryTests(unittest.TestCase):
    def fixture(self):
        module = types.ModuleType('tests_python.test_full_fixture')
        module.Foreign = type('Foreign', (unittest.TestCase,), {
            '__module__': 'tests_python.test_other', 'test_foreign': lambda self: None})
        module.Own = type('Own', (unittest.TestCase,), {
            '__module__': module.__name__, 'test_local': lambda self: None})
        module.Alias = module.Own
        module.Child = type('Child', (module.Foreign,), {'__module__': module.__name__})
        return module

    def test_imported_cases_and_aliases_do_not_execute_again(self):
        module=self.fixture()
        tests,classes=runner.select_tests(('test_full_fixture',),lambda _:module)
        self.assertEqual(set(tests), {module.__name__+'.Own.test_local',module.__name__+'.Child.test_foreign'})
        self.assertEqual(len(classes),2)

    def test_empty_or_duplicate_module_selection_fails(self):
        for modules in ((),('test_full_fixture',)*2):
            with self.subTest(modules=modules), self.assertRaises(ValueError):
                runner.select_tests(modules,lambda _:self.fixture())

    def test_wrong_module_identity_or_import_failure_is_not_a_pass(self):
        with self.assertRaises(ValueError):runner.select_tests(('test_wrong',),lambda _:self.fixture())
        def fail(_):raise ImportError('inert import failure')
        with self.assertRaises(ImportError):runner.select_tests(('test_full_fixture',),fail)

    def test_imported_only_module_is_not_successful_zero_tests(self):
        module=self.fixture();del module.Own;del module.Alias;del module.Child
        with self.assertRaises(ValueError):runner.select_tests(('test_full_fixture',),lambda _:module)

    def test_custom_loader_is_not_silently_ignored(self):
        module=self.fixture();module.load_tests=lambda *args:None
        with self.assertRaises(ValueError):runner.select_tests(('test_full_fixture',),lambda _:module)

    def test_duplicate_method_identity_fails_closed(self):
        module=self.fixture();module.Second=type('Own',(unittest.TestCase,),{
            '__module__':module.__name__,'test_local':lambda self:None})
        with self.assertRaises(ValueError):runner.select_tests(('test_full_fixture',),lambda _:module)

    def test_list_mode_never_runs_tests_and_does_not_create_pass_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'selection.json'
            with patch.object(runner,'select_tests',return_value=runner.select_tests(('test_full_fixture',),lambda _:self.fixture())), \
                 patch.object(runner,'inputs',return_value={'fixture':'hash'}), \
                 patch('unittest.TextTestRunner.run',side_effect=AssertionError('must not run')), \
                 patch('sys.stdout',new_callable=io.StringIO):
                self.assertEqual(runner.main(['--list','--output',str(output)]),0)
            data=json.loads(output.read_bytes())
            self.assertFalse(data['execution_performed']);self.assertEqual(data['tests_run'],0)
            self.assertEqual(data['executed_methods'],[]);self.assertTrue(data['selected_methods'])
            self.assertFalse(output.with_suffix('.log').exists())

    def test_explicit_output_cannot_overwrite_old_evidence_before_selection(self):
        for suffix in ('.json','.log'):
            with self.subTest(suffix=suffix),tempfile.TemporaryDirectory() as tmp:
                output=Path(tmp)/'run.json';target=output.with_suffix(suffix);target.write_bytes(b'old evidence')
                with patch.object(runner,'select_tests',side_effect=AssertionError('must reject first')), \
                     self.assertRaises(ValueError):runner.main(['--output',str(output)])
                self.assertEqual(target.read_bytes(),b'old evidence')

    def test_source_drift_cannot_report_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(runner,'select_tests',return_value=runner.select_tests(('test_full_fixture',),lambda _:self.fixture())), \
                 patch.object(runner,'inputs',side_effect=[{'fixture':'before'},{'fixture':'after'}]), \
                 patch('sys.stdout',new_callable=io.StringIO):
                self.assertEqual(runner.main(['--output',str(Path(tmp)/'run.json')]),1)
            data=json.loads((Path(tmp)/'run.json').read_bytes())
            self.assertFalse(data['successful']);self.assertEqual(data['source_changes_during_run'],['fixture'])
            self.assertEqual(data['tests_run'],2)

    def test_default_run_preserves_previous_reports_in_a_new_unique_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'reports').mkdir()
            for suffix in ('.json','.log'):(root/('reports/python-tests'+suffix)).write_bytes(b'original evidence')
            with patch.object(runner,'ROOT',root), \
                 patch.object(runner,'select_tests',return_value=runner.select_tests(('test_full_fixture',),lambda _:self.fixture())), \
                 patch.object(runner,'inputs',return_value={'fixture':'hash'}), \
                 patch('sys.stdout',new_callable=io.StringIO):self.assertEqual(runner.main([]),0)
            for suffix in ('.json','.log'):
                self.assertEqual((root/('reports/python-tests'+suffix)).read_bytes(),b'original evidence')
            created=list((root/'reports').glob('python-tests-*.json'));self.assertEqual(len(created),1)
            self.assertTrue(json.loads(created[0].read_bytes())['successful'])
