"""Source-fixture closure and immutable legacy exports; no source deployment."""
import json
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from tests_python import test_review_bundle as fixtures
from zzz_ops import review_bundle as bundle

EXAMPLES = 'docs/operator-call-examples.json'
REQUIRED = (EXAMPLES, 'docs/function-reference.json', 'docs/function-reference-notes.json',
            'docs/CONTRACT_FUNCTIONS.md', 'docs/OPERATOR_MANUAL.md')
LEGACY_HASHES = {
    1: '7242e43da2b2c6655909901e74a653521791ab4bef090e54f39e78426e11de32',
    2: '1c01ee5a5d83bd319630335d1d4c282d4a7b01db8fc669ac3974f33f4f5f4bef',
    3: '7b497cc1d7fabf864abfba89e0be686eb91351e4a0fbfb17580e99ab67b18bf1',
}


def inputs(*, examples=True):
    files = fixtures.inputs()
    files['scripts/generate-operator-reference.py'] = b'# explicit operator reference consumer\n'
    for name in REQUIRED:
        if name != EXAMPLES or examples:
            files[name] = b'{}\n' if name.endswith('.json') else b'# frozen operator fixture\n'
    return files


class ReviewBundleSchema4Tests(unittest.TestCase):
    def test_git_snapshot_admission_dispatches_by_explicit_archive_schema(self):
        files = inputs()
        files['docs/private-runtime.json'] = b'{"synthetic":"excluded"}\n'
        objects = {}
        tree = []
        for name, raw in sorted(files.items()):
            oid = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            objects[oid] = raw
            tree.append(f'100644 blob {oid} {len(raw)}\t{name}'.encode() + b'\0')
        def git(_root, *args, data=None):
            if args[:2] == ('rev-parse', '--verify'):
                return (fixtures.COMMIT + '\n').encode()
            if args[0] == 'rev-parse':
                return (fixtures.TREE + '\n').encode()
            if args[0] == 'ls-tree':
                return b''.join(tree)
            if args == ('cat-file', '--batch'):
                return b''.join(oid + b' blob ' + str(len(objects[oid.decode()])).encode() +
                                b'\n' + objects[oid.decode()] + b'\n' for oid in data.splitlines())
            raise AssertionError('Unexpected synthetic Git read')
        with patch.object(bundle, 'git', side_effect=git):
            for schema in (1, 2, 3, 4):
                with self.subTest(schema=schema):
                    _, _, _, exported, excluded = bundle.frozen_files(Path('synthetic'), fixtures.COMMIT, schema=schema)
                    self.assertEqual(EXAMPLES in exported, schema == 4)
                    self.assertEqual(EXAMPLES in {row['path'] for row in excluded}, schema != 4)
                    self.assertNotIn('docs/private-runtime.json', exported)

    def test_default_fresh_schema4_binds_exact_operator_examples(self):
        raw, manifest = fixtures.build(inputs())
        self.assertEqual(manifest['schema'], 4)
        self.assertIn(EXAMPLES, {row['path'] for row in manifest['files']})
        self.assertTrue(bundle.verify(raw, bundle.digest(raw))['ok'])
        self.assertFalse(manifest['tests_executed'])
        self.assertFalse(manifest['production_approved'])

    def test_only_exact_new_document_fixture_is_admitted(self):
        self.assertTrue(bundle.admitted(EXAMPLES))
        for name in ('docs/private-runtime.json', 'docs/operator-call-examples-copy.json',
                     'docs/secrets/operator-call-examples.json', '.git/config', 'keeper/live.json'):
            with self.subTest(name=name):
                self.assertFalse(bundle.admitted(name))

    def test_all_operator_generator_inputs_are_required_for_fresh_exports(self):
        for name in REQUIRED:
            files = inputs()
            del files[name]
            with self.subTest(name=name), self.assertRaises(bundle.BundleError):
                fixtures.build(files)

    def test_module_or_test_consumer_also_requires_its_fixture_closure(self):
        for consumer in ('zzz_ops/operator_reference.py', 'tests_python/test_operator_reference.py'):
            files = fixtures.inputs()
            files[consumer] = b'# explicit operator reference consumer\n'
            with self.subTest(consumer=consumer), self.assertRaises(bundle.BundleError):
                fixtures.build(files)

    def test_historical_schemas_keep_exact_bytes_and_exclusion_meaning(self):
        excluded = [{'path': EXAMPLES, 'reason': 'outside_review_source_allowlist'}]
        for schema, expected in LEGACY_HASHES.items():
            with self.subTest(schema=schema):
                raw, manifest = fixtures.build(inputs(examples=False), excluded=excluded, schema=schema)
                self.assertEqual(bundle.digest(raw), expected)
                self.assertEqual(manifest['excluded_files'], excluded)
                self.assertTrue(bundle.verify(raw, expected)['ok'])

    def test_historical_schema_does_not_silently_admit_the_new_fixture(self):
        for schema in (1, 2, 3):
            with self.subTest(schema=schema):
                raw, _ = fixtures.build(inputs(), schema=schema)
                with self.assertRaises(bundle.BundleError):
                    bundle.verify(raw, bundle.digest(raw))

    def test_fresh_verifier_refuses_removed_fixture_despite_recomputed_hashes(self):
        raw, _ = fixtures.build(inputs())
        def remove(members):
            manifest = json.loads(members['manifest.json'])
            del members['source/' + EXAMPLES]
            manifest['files'] = [row for row in manifest['files'] if row['path'] != EXAMPLES]
            manifest['excluded_files'] = [{'path': EXAMPLES, 'reason': 'outside_review_source_allowlist'}]
            members['manifest.json'] = bundle.canonical(manifest)
        changed = fixtures.rewrite(raw, member_change=remove)
        with self.assertRaises(bundle.BundleError):
            bundle.verify(changed, bundle.digest(changed))

    def test_fresh_handoff_requires_authenticated_git_checkout_not_fake_history(self):
        text = ' '.join(bundle.handoff(fixtures.COMMIT).decode().split())
        for required in ('Schema 4', 'independently authenticated Git checkout',
                         'byte-compare every included', 'Do not run `git init`',
                         'not from the extracted archive alone', 'Schemas 1, 2 and 3'):
            self.assertIn(required, text)

    def test_new_schema_cannot_be_relabelled_as_historical(self):
        raw, manifest = fixtures.build(inputs())
        self.assertEqual(manifest['schema'], 4)
        for schema in (1, 2, 3):
            changed = fixtures.rewrite(raw, mutate=lambda m: m.update(schema=schema))
            with self.subTest(schema=schema), self.assertRaises(bundle.BundleError):
                bundle.verify(changed, bundle.digest(changed))

    def test_boolean_and_unknown_schemas_remain_rejected(self):
        for schema in (True, False, 0, 5, '4', None):
            with self.subTest(schema=schema), self.assertRaises(bundle.BundleError):
                bundle.handoff(fixtures.COMMIT, schema)
