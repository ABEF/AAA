"""Current source inventory checks, not compiler or deployed helper assurance."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_inventory_subject',ROOT/'scripts/source_checks.py')
subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(subject)


class SourceInventoryTests(unittest.TestCase):
    def test_required_source_classes_match_compiler_bound_callable_inventory(self):
        reference=json.loads((ROOT/'docs/function-reference.json').read_text(encoding='utf-8'))
        self.assertEqual({c['name'] for c in reference['contracts']},set(subject.EXPECTED+subject.HELPERS+subject.CODE_DATA))
        self.assertEqual(subject.CODE_DATA,['ZZZRoyaltyCodeData'])
        self.assertNotIn('ZZZRoyaltyCodeData',subject.HELPERS)

    def test_new_standalone_policy_sources_cannot_silently_disappear(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);shutil.copytree(ROOT/'src',root/'src')
            for name in ('ZZZProtocolPolicy','ZZZPortfolioPolicy','ZZZRebalanceConfirmation',
                         'ZZZLPBalanceMath','ZZZLPPositionExecutor','ZZZPythPriceFeed','ZZZRoyaltyCodeData'):
                path=root/'src'/(name+'.sol');original=path.read_bytes();path.unlink()
                output=root/(name+'.json')
                try:
                    with self.subTest(contract=name),patch.object(subject,'ROOT',root),redirect_stdout(io.StringIO()):
                        self.assertEqual(1,subject.main(['--output',str(output)]))
                        report=json.loads(output.read_text(encoding='utf-8'))
                        self.assertIn('Missing required contract '+name,report['errors'])
                        self.assertFalse(report['security_audit_pass'])
                        self.assertFalse(report['solidity_compiled'])
                finally:path.write_bytes(original)


if __name__=='__main__':unittest.main()
