"""Offline inventory CLI safety; no chain or real evidence is used."""
import importlib.util
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/validate-production-config.py'
spec=importlib.util.spec_from_file_location('native_preflight_cli',SCRIPT)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)


class ProductionPreflightCLITests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-X','utf8',str(SCRIPT),*map(str,args)],
            capture_output=True,text=True,timeout=30,cwd=ROOT)

    def test_historical_governed_layout_keeps_exact_block(self):
        report=gate.validate({'custody_architecture':'governed-v1','ready':True})
        self.assertFalse(report['ready']);self.assertFalse(report['deployment_authorized'])
        self.assertEqual(report['issues'][0]['code'],'custody.inventory_schema_pending')

    def test_native_schema_dispatch_lists_real_missing_requirements(self):
        report=gate.validate({'schema_version':5,'custody_architecture':'governed-v1'})
        self.assertEqual(report['schema_version'],5)
        self.assertFalse(report['ready']);self.assertFalse(report['deployment_authorized'])
        self.assertNotIn('custody.inventory_schema_pending',[i['code'] for i in report['issues']])
        self.assertGreater(len(report['issues']),1)

    def test_float_version_cannot_enter_new_profile(self):
        report=gate.validate({'schema_version':5.0,'custody_architecture':'governed-v1'})
        self.assertFalse(report['ready']);self.assertEqual(report['schema_version'],4)

    def test_duplicate_keys_and_nonfinite_numbers_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.json'
            for raw in ('{"schema_version":4,"schema_version":5}',
                        '{"nested":{"status":"pending","status":"passed"}}',
                        '{"amount":NaN}','{"amount":Infinity}','{"amount":-Infinity}'):
                path.write_text(raw,encoding='utf-8')
                with self.subTest(raw=raw),self.assertRaises(ValueError):gate.read_config(path)

    def test_inventory_file_size_is_bounded_before_parsing(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.json';path.write_bytes(b' '*(8*1024*1024+1))
            with self.assertRaisesRegex(ValueError,'bounded'):gate.read_config(path)

    def test_report_replacement_is_atomic_and_cleans_failed_temporary(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'report.json';path.write_text('original',encoding='utf-8')
            with patch.object(gate.os,'replace',side_effect=OSError('private internal diagnostic')):
                with self.assertRaises(OSError):gate.write_report(path,'new')
            self.assertEqual(path.read_text(),'original')
            self.assertEqual(list(Path(folder).iterdir()),[path])
            gate.write_report(path,'new\n');self.assertEqual(path.read_text(),'new\n')

    def test_cli_refuses_to_overwrite_inventory_with_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.json';raw='{"custody_architecture":"governed-v1"}'
            path.write_text(raw,encoding='utf-8')
            result=self.run_cli('--config',path,'--output',path)
            self.assertEqual(result.returncode,1);report=json.loads(result.stdout)
            self.assertEqual(report['issues'][0]['code'],'output.path_conflict')
            self.assertEqual(path.read_text(),raw)

    def test_cli_sanitizes_invalid_input_and_unavailable_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.json';output=Path(folder)/'report.json'
            path.write_text('{private RPC credential bytes',encoding='utf-8')
            result=self.run_cli('--config',path,'--output',output)
            self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout),json.loads(output.read_text()))
            self.assertNotIn('private RPC',result.stdout+result.stderr)
            path.write_text('{"custody_architecture":"governed-v1"}',encoding='utf-8')
            result=self.run_cli('--config',path,'--output',Path(folder)/'absent'/'report.json')
            self.assertEqual(result.returncode,1)
            self.assertEqual(json.loads(result.stdout)['issues'][0]['code'],'output.unavailable')
            self.assertFalse(result.stderr)

    def fixture_main(self,config,*flags):
        from tests_python.test_production_v2 import NOW
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'inventory.json'
            path.write_text(json.dumps(config),encoding='utf-8')
            output=io.StringIO()
            with patch.object(sys,'argv',[str(SCRIPT),'--config',str(path),*flags]), \
                    patch.object(gate.time,'time',return_value=NOW), redirect_stdout(output):
                status=gate.main()
            return status,json.loads(output.getvalue())

    def test_default_current_gate_rejects_omitted_zero_boolean_or_legacy_profile(self):
        from tests_python.test_production_v2 import fixture
        for version in ('absent',0,True,False):
            with self.subTest(version=version):
                config=fixture()
                if version != 'absent':config['mint_integration_version']=version
                status,report=self.fixture_main(config)
                self.assertEqual(status,1)
                self.assertFalse(report['ready'])
                self.assertIn('current_profile_required',{i['code'] for i in report['issues']})
                self.assertTrue(report['current_release_gate'])
                self.assertFalse(report['production_qualification_supported'])
                self.assertFalse(report['deployment_authorized'])
        status,report=self.fixture_main({'schema_version':4})
        self.assertEqual(status,1)
        self.assertIn('current_profile_required',{i['code'] for i in report['issues']})

    def test_explicit_historical_mode_can_only_report_consistency(self):
        from tests_python.test_production_v2 import fixture
        status,report=self.fixture_main(fixture(),'--historical-consistency')
        self.assertEqual(status,0,report['issues'])
        self.assertTrue(report['ready'])
        self.assertFalse(report['current_release_gate'])
        self.assertFalse(report['production_qualification_supported'])
        self.assertFalse(report['deployment_authorized'])
        self.assertEqual('historical_manifest_consistency_only',report['approval_scope'])

    def test_current_profile_still_blocks_unimplemented_opensea_primary_mint(self):
        from tests_python.test_mint_integration_qualification import current_fixture
        status,report=self.fixture_main(current_fixture())
        self.assertEqual(status,1)
        self.assertEqual({'mint.opensea_unsupported'},{i['code'] for i in report['issues']})
        self.assertTrue(report['current_release_gate'])
        self.assertTrue(report['production_qualification_supported'])
        self.assertFalse(report['deployment_authorized'])

    def test_historical_opt_in_does_not_erase_current_source_incompatibility(self):
        from tests_python.test_mint_integration_qualification import current_fixture
        status,report=self.fixture_main(current_fixture(),'--historical-consistency')
        self.assertEqual(status,1)
        self.assertIn('mint.opensea_unsupported',{i['code'] for i in report['issues']})
        self.assertFalse(report['current_release_gate'])
        self.assertFalse(report['production_qualification_supported'])


if __name__=='__main__':unittest.main()
