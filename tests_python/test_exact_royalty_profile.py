"""Explicit fresh exact-unit identity; historical inventories never auto-upgrade."""
import importlib.util
import json
import unittest
from pathlib import Path

from zzz_ops import production_v10 as OLD, production_v11 as NEW
from zzz_ops.production_observer_v11 import observe
from zzz_ops.production_observer_v11 import Observer

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('exact_gate',ROOT/'scripts/validate-production-config.py')
GATE=importlib.util.module_from_spec(spec)
spec.loader.exec_module(GATE)


class ExactRoyaltyProfileTest(unittest.TestCase):
    def setUp(self):
        self.current=json.loads((ROOT/'config/production.schema13.example.json').read_text())
        self.old=json.loads((ROOT/'config/production.royalty3.example.json').read_text())

    def test_archived_exact_inventory_remains_explicit_and_unqualified(self):
        self.assertEqual(self.current['schema_version'],13)
        self.assertEqual(self.current['canonical_schema'],NEW.SCHEMA_NAME)
        report=GATE.validate(self.current,now=1793880000)
        self.assertFalse(report['ready'])
        self.assertFalse(report['deployment_authorized'])

    def test_exact_and_old_bindings_stay_separate(self):
        chain=self.current['chains'][0]
        exact=NEW.expected_bindings(chain);old=OLD.expected_bindings(self.old['chains'][0])
        self.assertEqual(exact['helpers']['royalty_rewards']['ROYALTY_SETTLEMENT_VERSION'],4)
        self.assertEqual(old['helpers']['royalty_rewards']['ROYALTY_SETTLEMENT_VERSION'],3)
        self.assertEqual(exact['modules']['canonical']['SCHEMA'],NEW.SCHEMA_HASH)
        self.assertEqual(old['modules']['canonical']['SCHEMA'],OLD.SCHEMA_HASH)
        self.assertNotEqual(NEW.SCHEMA_HASH,OLD.SCHEMA_HASH)
        self.assertEqual(len(NEW.HELPERS),18)
        self.assertEqual(OLD.VERSIONS['schema_version'],12)

    def test_current_gate_rejects_old_or_missing_identity(self):
        for value in [self.old,{},dict(self.current,schema_version=True),dict(self.current,schema_version=12)]:
            report=GATE.validate(value)
            self.assertFalse(report['ready'])
            self.assertFalse(report['deployment_authorized'])
            self.assertEqual(report['schema_version'],16)

    def test_observer_rejects_old_before_rpc(self):
        class NoRpc:
            def call(self,*args,**kwargs):
                raise AssertionError('Historical profile must not initiate an RPC')
        with self.assertRaisesRegex(ValueError,'schema13'):
            observe(self.old,NoRpc())

    def test_new_api_profile_is_not_a_renamed_old_config(self):
        self.assertNotEqual(NEW.SERVICE_PROFILES['api'],OLD.SERVICE_PROFILES['api'])
        self.assertIn('royalty4_exact_units',NEW.SERVICE_PROFILES['api'])
        binding=NEW.expected_bindings(self.current['chains'][0])
        self.assertEqual(binding['helpers']['royalty_rewards']['ACTIVATION_WINDOW'],3600)

    def test_fixed_factory_payload_is_a_code_owned_hash_binding(self):
        wanted=NEW.ROYALTY_CREATION_CODE_HASH
        bindings=NEW.expected_bindings(self.current['chains'][0])
        self.assertEqual(bindings['helpers']['royalty_factory']['royaltyCodeHash'],wanted)
        observer=object.__new__(Observer)
        calls=[]
        def read(target,method):
            calls.append((target,method))
            return [wanted[2:]]
        observer.read=read
        self.assertEqual(observer.typed('0x'+'1'*40,'royaltyCodeHash',None),wanted)
        self.assertEqual(calls,[('0x'+'1'*40,'royaltyCodeHash()')])

    def test_observer_and_gate_share_reviewed_expanded_inventory_bound(self):
        from zzz_ops.production_observer_v6 import _observe
        class AnchorReached:
            def anchor(self):
                raise RuntimeError('anchor reached; no qualification implied')
        self.current['chains'][0]['buyback_maximum_usd18']=str(100*10**18)
        for count in (34, NEW.MAX_TOKEN_RECORDS):
            self.current['chains'][0]['tokens']=[{} for _ in range(count)]
            with self.subTest(count=count),self.assertRaisesRegex(RuntimeError,'anchor reached'):
                _observe(self.current,None,profile=NEW,observer_class=lambda *_:AnchorReached())
        self.current['chains'][0]['tokens']=[{} for _ in range(NEW.MAX_TOKEN_RECORDS+1)]
        with self.assertRaisesRegex(ValueError,'Unbounded declared inventory'):
            _observe(self.current,None,profile=NEW,observer_class=lambda *_:self.fail('RPC must not start'))

    def test_historical_inventory_bound_is_not_silently_raised(self):
        from zzz_ops.production_observer_v6 import _observe
        self.old['chains'][0]['buyback_maximum_usd18']=str(100*10**18)
        self.old['chains'][0]['tokens']=[{} for _ in range(34)]
        with self.assertRaisesRegex(ValueError,'Unbounded declared inventory'):
            _observe(self.old,None,profile=OLD,observer_class=lambda *_:self.fail('RPC must not start'))


if __name__=='__main__':
    unittest.main()
