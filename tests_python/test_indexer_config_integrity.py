"""Actual indexer CLI configuration admission; no lock, database or RPC opened."""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT=Path(__file__).resolve().parents[1]


class IndexerConfigIntegrityTests(unittest.TestCase):
    def setUp(self):
        source=Path(os.environ.get('POPL_INDEXER_CONFIG_SUBJECT',ROOT/'indexer/monitor.py'))
        spec=importlib.util.spec_from_file_location('indexer_config_subject',source)
        self.subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.subject)
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)/'configuration.json'
        self.valid={'chain_id':4663,'start_block':1,'contracts':['0x'+'1'*40],
                    'rpc_urls':['https://uncontacted.invalid'],'database':'not-created.sqlite'}

    def invoke(self):
        with patch.object(sys,'argv',['indexer.monitor','--config',str(self.path),'--once']), \
                patch.object(self.subject,'process_lock') as lock, \
                patch.object(self.subject,'Indexer') as index, \
                patch.object(self.subject.signal,'signal') as signals, \
                patch('sys.stdout',new=io.StringIO()):
            self.lock,self.index,self.signals=lock,index,signals
            index.return_value.step.return_value=0
            index.return_value.next_block=1
            self.subject.main()

    def rejected(self,raw,exception=ValueError):
        self.path.write_text(raw,encoding='utf-8')
        original=self.path.read_bytes()
        with self.assertRaises(exception):self.invoke()
        self.lock.assert_not_called();self.index.assert_not_called();self.signals.assert_not_called()
        self.assertEqual(self.path.read_bytes(),original)

    def test_duplicate_configuration_identity_is_rejected_before_resources(self):
        encoded=json.dumps(self.valid)
        for pair in ('"start_block":99','"start_\\u0062lock":99','"chain_id":46630'):
            with self.subTest(pair=pair):self.rejected(encoded[:-1]+','+pair+'}')

    def test_nested_duplicate_configuration_is_not_silently_last_value_wins(self):
        self.rejected(json.dumps(self.valid)[:-1]+',"metadata":{"mode":"one","mode":"two"}}')

    def test_nonfinite_numbers_are_rejected_even_in_optional_fields(self):
        for value in ('NaN','Infinity','-Infinity','1e9999'):
            with self.subTest(value=value):self.rejected(json.dumps(self.valid)[:-1]+',"optional":'+value+'}')

    def test_nonobject_configuration_is_rejected_before_signals_or_locks(self):
        for raw in ('null','[]','true','1','"value"'):
            with self.subTest(raw=raw):self.rejected(raw)

    def test_missing_configuration_preserves_missing_file_classification(self):
        with self.assertRaises(FileNotFoundError):self.invoke()
        self.lock.assert_not_called();self.index.assert_not_called();self.signals.assert_not_called()
        self.assertFalse(self.path.exists())

    def test_malformed_json_has_fixed_safe_diagnostic(self):
        secret='SYNTHETIC-CONFIG-MARKER'
        self.path.write_text('{"'+secret+'":',encoding='utf-8')
        with self.assertRaises(ValueError) as caught:self.invoke()
        self.assertEqual(str(caught.exception),'Invalid indexer configuration JSON')
        self.assertNotIn(secret,str(caught.exception));self.lock.assert_not_called();self.index.assert_not_called()

    def test_parser_resource_error_is_normalized_without_starting_work(self):
        self.path.write_text('{}',encoding='utf-8')
        with patch.object(self.subject,'read_json',side_effect=RecursionError('SYNTHETIC-CONFIG-MARKER')):
            with self.assertRaises(ValueError) as caught:self.invoke()
        self.assertEqual(str(caught.exception),'Invalid indexer configuration JSON')
        self.lock.assert_not_called();self.index.assert_not_called();self.signals.assert_not_called()

    def test_valid_object_preserves_values_and_existing_defaults(self):
        value={**self.valid,'optional':{'label':'é','fraction':1.25}}
        self.path.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
        self.invoke()
        self.index.assert_called_once_with(value)
        self.lock.assert_called_once_with('var/indexer.lock')
        self.index.return_value.step.assert_called_once_with()
        self.index.return_value.close.assert_called_once_with()
        self.assertEqual(json.loads(self.path.read_text(encoding='utf-8')),value)


if __name__=='__main__':unittest.main()
