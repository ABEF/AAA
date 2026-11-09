"""New audit instructions are versioned without reinterpreting old archives."""
import io
import json
import unittest
import zipfile

from tests_python import test_review_bundle as fixtures
from zzz_ops import review_bundle as bundle


def legacy_archive():
    raw, _ = fixtures.build()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(members['manifest.json'])
    manifest['schema'] = 1
    members['HANDOFF.md'] = bundle.handoff(fixtures.COMMIT, 1)
    manifest['handoff_sha256'] = bundle.digest(members['HANDOFF.md'])
    members['manifest.json'] = bundle.canonical(manifest)
    return bundle.zip_bytes(members, {'source/'+r['path']: r['mode'] for r in manifest['files']})


class ReviewBundleProfileTests(unittest.TestCase):
    def test_default_schema2_uses_current_profile_and_preserves_qualification_limits(self):
        raw, manifest = fixtures.build()
        self.assertEqual(manifest['schema'], 2)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            instructions = archive.read('HANDOFF.md').decode()
        self.assertIn('--config config/production.holder-exit.example.json', instructions)
        self.assertIn('current schema6/accounting4/custody3/same-chain holder-exit V5', instructions)
        self.assertIn('No external custody exit', instructions)
        self.assertIn('near-total principal loss', instructions)
        self.assertIn('MUST remain blocked', instructions)
        self.assertIn('An unpublished candidate is not exported', instructions)
        self.assertTrue(bundle.verify(raw, bundle.digest(raw))['ok'])

    def test_schema1_handoff_and_archive_bytes_retain_their_original_identity(self):
        # Captured from the pre-change encoder at the fixed fixture commit.
        self.assertEqual(bundle.digest(bundle.handoff(fixtures.COMMIT, 1)),
                         'dc1f262561c42ce51b94c422037f818864773f5521feb17d9062dd9479e259a6')
        raw = legacy_archive()
        self.assertEqual(bundle.digest(raw),
                         '331d306eb6e587a8dc6e0455618fe4f38f4ba37e53f8e46b37cbc9fa1b99975f')
        self.assertTrue(bundle.verify(raw, bundle.digest(raw))['ok'])

    def test_handoff_cannot_be_relabelled_by_changing_only_the_schema(self):
        for raw, target in ((fixtures.build()[0], 1), (legacy_archive(), 2)):
            changed = fixtures.rewrite(raw, mutate=lambda m: m.update(schema=target))
            with self.assertRaisesRegex(bundle.BundleError, 'Handoff identity'):
                bundle.verify(changed, bundle.digest(changed))

    def test_unknown_and_boolean_schema_values_fail_closed(self):
        raw, _ = fixtures.build()
        for value in (0, 3, True, '2', None):
            with self.subTest(schema=value):
                changed = fixtures.rewrite(raw, mutate=lambda m: m.update(schema=value))
                with self.assertRaises(bundle.BundleError): bundle.verify(changed, bundle.digest(changed))
                with self.assertRaises(bundle.BundleError): bundle.handoff(fixtures.COMMIT, value)

    def test_current_schema_still_excludes_local_context_memory_and_runtime_data(self):
        for name in ('AGENTS.md', 'PROJECT_CONTEXT.md', '.env', 'keeper/live.json', '.git/config'):
            self.assertFalse(bundle.admitted(name))
        self.assertTrue(bundle.admitted('config/production.holder-exit.example.json'))
        self.assertTrue(bundle.admitted('docs/OPERATOR_MANUAL.md'))


if __name__ == '__main__':
    unittest.main()
