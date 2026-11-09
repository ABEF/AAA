"""Adversarial checks for the offline reviewer export, not protocol execution."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from zzz_ops import review_bundle as b

COMMIT = 'a' * 40
TREE = 'b' * 40


def inputs():
    packages = {'@review/dependency': '1.2.3'}
    return {
        'foundry.toml': b'[profile.default]\nsolc_version="0.8.26"\nevm_version="cancun"\n',
        'package.json': b.canonical({'devDependencies': packages}),
        'package-lock.json': b.canonical({'lockfileVersion': 3, 'packages': {
            '': {'devDependencies': packages}, 'node_modules/@review/dependency': {
                'version': '1.2.3', 'integrity': 'sha512-explicit-fixture'}}}),
        'scripts/install-deps.sh': b'forge_std_commit=77041d2ce690e692d6e03cc812b57d1ddaa4d505\n',
        'src/Fixture.sol': b'contract Fixture {}\n',
    }


def build(files=None, gitlinks=None, excluded=None):
    files = inputs() if files is None else files
    records = []
    for name, raw in sorted(files.items()):
        records.append({'path': name, 'mode': '100644', 'size': len(raw), 'sha256': b.digest(raw),
                        'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()})
    if excluded is None:
        excluded = [{'path': row['path'], 'reason': 'gitlink_dependency_not_bundled'} for row in gitlinks or []]
    with patch.object(b, 'frozen_files', return_value=(TREE, records, gitlinks or [], files, excluded)):
        return b.pack(Path('unused'), COMMIT)


def rewrite(raw, mutate=None, member_change=None):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = {i.filename: archive.read(i) for i in archive.infolist()}
    manifest = json.loads(members['manifest.json'])
    if mutate:
        mutate(manifest)
        members['manifest.json'] = b.canonical(manifest)
    if member_change:
        member_change(members)
    return b.zip_bytes(members, {'source/' + r['path']: r['mode'] for r in manifest['files']})


class ReviewBundleTests(unittest.TestCase):
    def rejected(self, raw):
        with self.assertRaises(b.BundleError):
            b.verify(raw, b.digest(raw))

    def test_deterministic_frozen_inputs_and_dependency_limitations(self):
        raw, manifest = build()
        self.assertEqual(raw, build()[0])
        result = b.verify(raw, b.digest(raw))
        self.assertEqual(result['source_commit'], COMMIT)
        self.assertFalse(result['production_approved'])
        self.assertFalse(result['tests_executed'])
        self.assertFalse(result['dependencies_bundled'])
        self.assertFalse(manifest['dependencies']['self_contained'])

    def test_gitlink_pin_is_carried_but_never_claimed_bundled(self):
        files = inputs()
        files['.gitmodules'] = b'[submodule "example"]\npath = lib/example\nurl = https://example.invalid/example.git\n'
        raw, manifest = build(files, gitlinks=[{'path': 'lib/example', 'commit': 'c' * 40}])
        self.assertEqual(manifest['dependencies']['gitlinks'][0]['commit'], 'c' * 40)
        self.assertTrue(b.verify(raw, b.digest(raw))['ok'])

    def test_requires_exact_commit_before_git_is_read(self):
        with patch.object(b, 'git') as git:
            for value in ['HEAD', 'main', 'A' * 40, 'a' * 39, COMMIT + ';ignored']:
                with self.assertRaises(b.BundleError):
                    b.frozen_files(Path('unused'), value)
            git.assert_not_called()

    def test_allowlist_excludes_runtime_secrets_history_and_memories(self):
        for name in ['.env', '.env.example', '.git/config', 'keeper/live.json', 'reports/old.json',
                     'AGENTS.md', 'PROJECT_CONTEXT.md', 'wallet.key', 'node_modules/a.py',
                     'src/secrets/wallet.py', 'docs/private-runtime.json']:
            self.assertFalse(b.admitted(name), name)
        for name in ['test/PrivatePermissions.t.sol', 'tests_python/test_signer.py',
                     'indexer/event_schema.json', 'config/production.example.json',
                     'reports/production/keccak-vectors.json', 'slither.config.json',
                     'design/nft-metadata/palette-system-v1/packed-catalog.json',
                     'docs/function-reference.json', 'docs/function-reference-notes.json']:
            self.assertTrue(b.admitted(name), name)

    def test_callable_reference_consumer_requires_frozen_explanations_and_snapshot(self):
        files = inputs()
        files['scripts/generate-function-reference.py'] = b'# explicit reference consumer\n'
        for required in ['docs/function-reference.json', 'docs/function-reference-notes.json', 'docs/CONTRACT_FUNCTIONS.md']:
            with self.assertRaises(b.BundleError):
                build(files)
            files[required] = b'{}\n' if required.endswith('.json') else b'# fixed callable reference\n'
        raw, manifest = build(files)
        self.assertTrue(b.verify(raw, b.digest(raw))['ok'])
        self.assertTrue({'docs/function-reference.json', 'docs/function-reference-notes.json'} <=
                        {row['path'] for row in manifest['files']})

    def test_declared_catalog_and_abi_consumers_require_exact_fixture_inputs(self):
        for consumer in ['scripts/generate-artwork-library.py', 'tests_python/test_abi.py']:
            files = inputs()
            files[consumer] = b'# explicit consumer fixture\n'
            with self.assertRaises(b.BundleError):
                build(files)
        files.update({'reports/production/keccak-vectors.json': b'{"vectors":[]}\n'})
        raw, _ = build(files)
        self.assertTrue(b.verify(raw, b.digest(raw))['ok'])

    def test_rejects_portable_path_ambiguities(self):
        for name in ['../outside', '/absolute', 'source//duplicate', 'source/./dot', 'x\\file',
                     'C:foo', 'src/a.', 'src/con.sol', 'src/LPT1', 'src/a|b.py', 'src/nonascii-é.py']:
            with self.assertRaises(b.BundleError, msg=name):
                b.path_name(name)

    def test_missing_or_changed_dependency_pin_is_rejected(self):
        for missing in ['package-lock.json', 'scripts/install-deps.sh', 'foundry.toml']:
            files = inputs()
            del files[missing]
            with self.assertRaises(b.BundleError):
                build(files)
        files = inputs()
        files['scripts/install-deps.sh'] = b'forge_std_commit=main\n'
        with self.assertRaises(b.BundleError):
            build(files)

    def test_gitlink_metadata_cannot_be_omitted(self):
        with self.assertRaises(b.BundleError):
            build(gitlinks=[{'path': 'lib/example', 'commit': 'c' * 40}])

    def test_excluded_paths_are_recorded_without_copying_their_bytes(self):
        excluded = [{'path': 'reports/prior.json', 'reason': 'outside_review_source_allowlist'}]
        raw, manifest = build(excluded=excluded)
        self.assertEqual(manifest['excluded_files'], excluded)
        self.assertTrue(b.verify(raw, b.digest(raw))['ok'])
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            self.assertNotIn('source/reports/prior.json', archive.namelist())
        self.rejected(rewrite(raw, mutate=lambda m: m['excluded_files'].append(
            {'path': 'src/Omitted.sol', 'reason': 'outside_review_source_allowlist'})))

    def test_credential_bearing_dependency_url_is_not_exported(self):
        files = inputs()
        files['.gitmodules'] = b'[submodule "fixture"]\nurl = https://fixture:NOT_A_SECRET@example.invalid/repo\n'
        with self.assertRaises(b.BundleError):
            build(files)

    def test_verify_requires_trusted_expected_hash(self):
        raw, _ = build()
        for value in [None, '', '0' * 64, b.digest(raw).upper()]:
            with self.assertRaises(b.BundleError):
                b.verify(raw, value)

    def test_changed_source_without_matching_manifest_fails(self):
        raw, _ = build()
        self.rejected(rewrite(raw, member_change=lambda m: m.__setitem__('source/src/Fixture.sol', b'changed')))

    def test_extra_or_missing_member_fails(self):
        raw, _ = build()
        self.rejected(rewrite(raw, member_change=lambda m: m.__setitem__('source/extra.py', b'not listed')))
        self.rejected(rewrite(raw, member_change=lambda m: m.pop('source/src/Fixture.sol')))

    def test_approval_or_handoff_forgery_is_rejected(self):
        raw, _ = build()
        self.rejected(rewrite(raw, mutate=lambda m: m.__setitem__('production_approved', True)))
        self.rejected(rewrite(raw, member_change=lambda m: m.__setitem__('HANDOFF.md', b'approved')))
        self.rejected(rewrite(raw, mutate=lambda m: m['dependencies'].__setitem__('self_contained', True)))

    def test_duplicate_manifest_keys_and_zip_members_are_rejected(self):
        raw, _ = build()
        self.rejected(rewrite(raw, member_change=lambda m: m.__setitem__('manifest.json', b'{"schema":1,"schema":1}')))
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as archive:
            archive.writestr('manifest.json', b'{}')
            archive.writestr('HANDOFF.md', b'fixture')
            archive.writestr('source/Foo.py', b'a')
            archive.writestr('source/foo.py', b'a')
        self.rejected(out.getvalue())

    def test_symlink_compression_and_trailing_payload_are_rejected(self):
        raw, _ = build()
        self.rejected(raw + b'unlisted trailing payload')
        for mode, compression in [(0o120777, zipfile.ZIP_STORED), (0o100644, zipfile.ZIP_DEFLATED)]:
            out = io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(raw)) as original, zipfile.ZipFile(out, 'w') as archive:
                for info in original.infolist():
                    contents = original.read(info.filename)
                    info.external_attr = mode << 16
                    info.compress_type = compression
                    archive.writestr(info, contents)
            self.rejected(out.getvalue())

    def test_member_count_and_expanded_size_limits_apply_before_read(self):
        raw, _ = build()
        with patch.object(b, 'MAX_MEMBERS', 3):
            self.rejected(raw)
        with patch.object(b, 'MAX_TOTAL', 2):
            self.rejected(raw)
        with patch.object(b, 'MAX_FILE', 2):
            self.rejected(raw)

    def test_exclusive_atomic_publication_preserves_existing_archive(self):
        raw, _ = build()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'review.zip'
            b.publish(output, raw, root / 'source')
            with self.assertRaises(b.BundleError):
                b.publish(output, b'different bytes', root / 'source')
            self.assertEqual(output.read_bytes(), raw)
            self.assertEqual(list(root.iterdir()), [output])
            with self.assertRaises(b.BundleError):
                b.publish(root / 'source' / 'bad.zip', raw, root / 'source')


if __name__ == '__main__':
    unittest.main()
