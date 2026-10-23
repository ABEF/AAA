import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('custody_release_gate',ROOT/'scripts/validate-production-config.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

class CustodyInventoryTests(unittest.TestCase):
    def test_new_layout_is_explicitly_blocked_not_validated_as_legacy_bridge(self):
        result=gate.validate({'custody_architecture':'governed-v1'})
        self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
        self.assertEqual(result['issues'][0]['code'],'custody.inventory_schema_pending')

    def test_updated_template_declares_layout_and_does_not_redeploy_retired_modules(self):
        config=json.loads((ROOT/'config/production.example.json').read_text())
        self.assertEqual(config['custody_architecture'],'governed-v1')
        for chain in config['chains']:
            self.assertFalse({'bridge','receiver','routes','transport'} & chain['modules'].keys())
            self.assertNotIn('pair_migration',chain)
            self.assertIn('custody_handoff',chain)
        self.assertFalse(gate.validate(config)['ready'])

    def test_manifest_flags_cannot_self_certify_new_inventory(self):
        result=gate.validate({'custody_architecture':'governed-v1','ready':True,'deployment_authorized':True,'reviewed':True})
        self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
