"""Principal is observable, but must never enter fee-income replay."""
import importlib.util
import json
from pathlib import Path
import unittest
from frontend_api.earnings_replay import SPECS
from indexer.events import SCHEMA, decode
from zzz_ops.abi import keccak256

ROOT = Path(__file__).resolve().parents[1]

class HolderExitEventTests(unittest.TestCase):
    def test_principal_payment_decodes_separately_from_income(self):
        signature = 'PrincipalPaid(uint256,address,address,uint256,uint256)'
        topic = '0x' + keccak256(signature.encode()).hex()
        w = lambda n: '0x' + f'{n:064x}'
        name, values = decode({'topics':[topic,w(444),w(0xA11CE),w(0xB0B)],
                               'data':'0x'+f'{123:064x}'+f'{456:064x}'})
        self.assertEqual(name, 'PrincipalPaid')
        self.assertEqual(values, dict(nftId='444',owner='0x'+'0'*35+'a11ce',
            recipient='0x'+'0'*37+'b0b',ethAmount='123',zzzAmount='456'))
        self.assertNotIn(signature, {sig for _,sig in SPECS})

    def test_old_custody_topics_remain_historical_only(self):
        historical=json.loads((ROOT/'indexer/historical_event_schema.json').read_text())
        for signature in ('RoyaltyCustodyExited(bytes32,address,address,uint256,bytes32)',
                          'RoyaltyCustodyReturned(bytes32,address,uint256)'):
            topic='0x'+keccak256(signature.encode()).hex()
            self.assertIn(topic,historical)
            self.assertEqual(SCHEMA[topic],historical[topic])

    def test_generated_event_inventory_matches_current_and_historical_source(self):
        spec=importlib.util.spec_from_file_location('holder_event_generator',ROOT/'scripts/generate_event_schema.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(SCHEMA,module.source_schema())

class HolderExitReleaseGateTests(unittest.TestCase):
    def test_ready_field_or_old_inventory_cannot_approve_new_source(self):
        spec=importlib.util.spec_from_file_location('holder_release_gate',ROOT/'scripts/validate-production-config.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for version in (3,4,True,4.0,None):
            with self.subTest(version=version):
                result=module.validate({'accounting_version':version,'ready':True,'production_approved':True})
                self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
                self.assertEqual(result['issues'][0]['code'],'holder_exit_qualification_pending')
