"""Prepare an exact source/docs publication allowlist; never writes Git state."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-seal-deep-review-20261117')


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    baseline = json.loads((OWN / 'BASELINE.json').read_text())
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert git('rev-parse', 'HEAD').decode().strip() == baseline['baseline_commit']
    assert not git('diff', '--cached', '--name-only').strip()
    protected = set(baseline['protected'])
    changed = set(git('diff', '--name-only').decode().splitlines()) - protected
    new_files = {'docs/SEAL_READINESS.md', 'test/SeaDropArtworkBoundary20261117.t.sol',
                 'test/SealCriticalInputs20261117.t.sol', 'test/helpers/AccountingExecutionFixture.sol'}
    for folder in (OWN, ROOT / 'test/fixtures/seal-critical-003c8d8'):
        for path in folder.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                new_files.add(path.relative_to(ROOT).as_posix())
    manifest_path = OWN / 'PUBLICATION_PREPARATION.json'
    new_files.add(manifest_path.relative_to(ROOT).as_posix())
    paths = sorted(changed | new_files)
    assert not (set(paths) & protected)
    raw = json.loads((OWN / 'RETAINED_OBSERVATIONS.json').read_text())
    archive = OWN / raw['archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == raw['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == {row['path'] for row in raw['files']}
        for row in raw['files']:
            with z.open(row['path']) as f:
                h = hashlib.sha256()
                for block in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(block)
            assert h.hexdigest() == row['sha256'], row['path']
    record = {'schema': 1, 'baseline': baseline['baseline_commit'], 'branch': 'main',
              'exact_expected_staged_paths': paths, 'excluded_protected_files': sorted(protected),
              'unrelated_untracked_drafts_included': False, 'archive_entries_verified': len(raw['files']),
              'source_docs_only': True, 'deploy_seal_sign_service_or_existing_chain_actions': []}
    manifest_path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    (EXTERNAL / 'publication-paths.txt').write_text('\n'.join(paths) + '\n', encoding='utf-8')
    print(json.dumps({'publication_paths': len(paths), 'archive_entries_verified': len(raw['files']),
                      'protected_excluded': len(protected)}))


if __name__ == '__main__':
    main()
