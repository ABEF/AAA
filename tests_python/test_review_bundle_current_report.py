"""New exact report-admission checks; existing fixture builders supply data only."""
import io
import unittest
import zipfile

from tests_python import test_review_bundle as fixtures
from zzz_ops import review_bundle as bundle


REPORT = 'reports/CURRENT_REVIEW.md'


class ReviewBundleCurrentReportTests(unittest.TestCase):
    def test_exact_current_report_is_admitted_only_in_schema4(self):
        self.assertTrue(bundle.admitted(REPORT))
        self.assertTrue(bundle.admitted(REPORT, schema=4))
        for schema in (1, 2, 3):
            with self.subTest(schema=schema):
                self.assertFalse(bundle.admitted(REPORT, schema=schema))

    def test_schema4_archive_preserves_exact_public_report_bytes_without_approval(self):
        files = fixtures.inputs()
        report = b'# Current review\n\nHistorical evidence is source-scoped; production remains unapproved.\n'
        files[REPORT] = report
        raw, manifest = fixtures.build(files, schema=4)
        checked = bundle.verify(raw, bundle.digest(raw))
        self.assertTrue(checked['ok'])
        self.assertEqual(manifest['schema'], 4)
        self.assertFalse(manifest['production_approved'])
        self.assertFalse(manifest['tests_executed'])
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            self.assertEqual(archive.read('source/' + REPORT), report)
            self.assertEqual(archive.read('HANDOFF.md'), bundle.handoff(fixtures.COMMIT, 4))
        row = next(item for item in manifest['files'] if item['path'] == REPORT)
        self.assertEqual(row['sha256'], bundle.digest(report))
        self.assertEqual(row['size'], len(report))

    def test_legacy_verifiers_reject_report_even_with_valid_member_and_manifest_hashes(self):
        files = fixtures.inputs()
        files[REPORT] = b'# Explicitly unapproved current review\n'
        for schema in (1, 2, 3):
            with self.subTest(schema=schema):
                # The fixture seam supplies a coherent but unadmitted record;
                # real verify() must reject it, rather than relabel old schemas.
                raw, manifest = fixtures.build(files, schema=schema)
                self.assertEqual(manifest['schema'], schema)
                with self.assertRaisesRegex(bundle.BundleError, 'Source inventory is not admitted'):
                    bundle.verify(raw, bundle.digest(raw))

    def test_unrelated_reports_and_prefix_lookalikes_remain_excluded(self):
        names = ('reports/old/REVIEW.md', 'reports/other.json', 'reports/current_review.md',
                 'reports/archive/CURRENT_REVIEW.md', 'reports/CURRENT_REVIEW.md.bak',
                 'reports/CURRENT_REVIEW.md.json', 'reports/CURRENT_REVIEW.md/extra.md',
                 'reports/secrets/CURRENT_REVIEW.md')
        for schema in (1, 2, 3, 4):
            for name in names:
                with self.subTest(schema=schema, name=name):
                    self.assertFalse(bundle.admitted(name, schema=schema))
            self.assertTrue(bundle.admitted('reports/production/keccak-vectors.json', schema=schema))


if __name__ == '__main__':
    unittest.main()
