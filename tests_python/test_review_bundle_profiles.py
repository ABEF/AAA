"""Versioned audit instructions preserve every historical archive identity."""
import io
import json
import unittest
import zipfile

from tests_python import test_review_bundle as fixtures
from zzz_ops import review_bundle as bundle


HISTORICAL = {
    1: ('dc1f262561c42ce51b94c422037f818864773f5521feb17d9062dd9479e259a6',
        '331d306eb6e587a8dc6e0455618fe4f38f4ba37e53f8e46b37cbc9fa1b99975f'),
    2: ('91c80897916ea5f14a2f1ed5e67dd662781579c6f8acc7ab0e86e21d1a75fad5',
        'eee1ac2371714a90b50e5d9aa6bf6b9bb1164cb238395f3a6ef727a04bc11397'),
}


def legacy_archive():
    return fixtures.build(schema=1)[0]


class ReviewBundleProfileTests(unittest.TestCase):
    def test_default_schema3_uses_current_instructions_without_claiming_approval(self):
        raw, manifest = fixtures.build()
        self.assertEqual(manifest['schema'], 3)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            instructions = ' '.join(archive.read('HANDOFF.md').decode().split())
        for text in ('Schema 3', 'schema17/accounting7/mint2/helper1/canonicalV10',
                     '--config config/production.example.json', '600/300',
                     '240-second', '3% total contribution', '97% marginal',
                     'conversion1%/maintenance3%', 'MUST remain blocked',
                     'An unpublished candidate is not exported',
                     'Actual OpenSea onboarding', 'Anvil-only'):
            self.assertIn(text, instructions)
        self.assertNotIn('--config config/production.holder-exit.example.json', instructions)
        self.assertNotIn('requires explicit mint_integration_version 1', instructions)
        self.assertNotIn('production_qualification_supported true', instructions)
        self.assertFalse(manifest['production_approved'])
        self.assertFalse(manifest['tests_executed'])
        self.assertTrue(bundle.verify(raw, bundle.digest(raw))['ok'])

    def test_schema1_handoff_and_archive_bytes_keep_original_identity(self):
        self._historical_identity(1)

    def test_schema2_handoff_and_archive_bytes_keep_original_identity(self):
        self._historical_identity(2)

    def _historical_identity(self, schema):
        handoff_hash, archive_hash = HISTORICAL[schema]
        self.assertEqual(bundle.digest(bundle.handoff(fixtures.COMMIT, schema)), handoff_hash)
        raw, manifest = fixtures.build(schema=schema)
        self.assertEqual(manifest['schema'], schema)
        self.assertEqual(bundle.digest(raw), archive_hash)
        self.assertTrue(bundle.verify(raw, bundle.digest(raw))['ok'])

    def test_no_schema_can_be_relabelled_as_another(self):
        for source in (1, 2, 3):
            raw, _ = fixtures.build(schema=source)
            for target in (1, 2, 3):
                if source == target:
                    continue
                with self.subTest(source=source, target=target):
                    changed = fixtures.rewrite(raw, mutate=lambda m: m.update(schema=target))
                    with self.assertRaisesRegex(bundle.BundleError, 'Handoff identity'):
                        bundle.verify(changed, bundle.digest(changed))

    def test_mixed_handoff_rejects_even_with_recomputed_digest(self):
        raw, _ = fixtures.build()
        for historical in (1, 2):
            def change(members):
                manifest = json.loads(members['manifest.json'])
                members['HANDOFF.md'] = bundle.handoff(fixtures.COMMIT, historical)
                manifest['handoff_sha256'] = bundle.digest(members['HANDOFF.md'])
                members['manifest.json'] = bundle.canonical(manifest)
            changed = fixtures.rewrite(raw, member_change=change)
            with self.assertRaisesRegex(bundle.BundleError, 'Handoff identity'):
                bundle.verify(changed, bundle.digest(changed))

    def test_unknown_and_boolean_schema_values_fail_closed(self):
        raw, _ = fixtures.build()
        for value in (0, 4, True, '3', None):
            with self.subTest(schema=value):
                changed = fixtures.rewrite(raw, mutate=lambda m: m.update(schema=value))
                with self.assertRaises(bundle.BundleError):
                    bundle.verify(changed, bundle.digest(changed))
                with self.assertRaises(bundle.BundleError):
                    bundle.handoff(fixtures.COMMIT, value)

    def test_current_schema_excludes_context_memory_and_runtime(self):
        for name in ('AGENTS.md', 'PROJECT_CONTEXT.md', '.env', 'keeper/live.json', '.git/config'):
            self.assertFalse(bundle.admitted(name))
        self.assertTrue(bundle.admitted('config/production.example.json'))
        self.assertTrue(bundle.admitted('docs/OPERATOR_MANUAL.md'))


if __name__ == '__main__':
    unittest.main()
