"""Package an explicit public allowlist; never recurse into credentials/runtime."""
from pathlib import Path
import hashlib
import json
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-keeper-20261121')
REPORT = ROOT / 'reports/ubuntu-keeper-20261121'
ACTION_DIRECTORIES = (
    'transport/upload-01', 'transport/install-01', 'transport/upload-02', 'transport/install-02',
    'run/start-preflight-01', 'run/stop-failed-preflight-01',
    'run2/start-preflight-01', 'run2/bootstrap-preflight-01', 'run2/cache-events-preflight-01',
    'run2/cache-upload-01', 'run2/freeze-01', 'run2/stop-preflight-01', 'run2/start-final-01',
    'run2/bootstrap-final-01', 'run2/cache-events-final-01', 'run2/stop-final-01',
)
EXACT_FILES = (
    'transport/LAB.json', 'transport/LAB2.json',
    'run/key-01/stdout.json', 'run/key-01/EXECUTION.json',
    'run/start-preflight-01/DIAGNOSTIC.json', 'run/start-preflight-01/STARTUP_WIRE.json',
    'run2/key-01/stdout.json', 'run2/key-01/EXECUTION.json',
    'run2/prefetch-events-02.json',
    'run2/prefetch-01/MANIFEST.json', 'run2/prefetch-01/public-read-wire.jsonl',
    'run2/prefetch-02/MANIFEST.json', 'run2/prefetch-02/public-read-wire.jsonl',
    'run2/automine-01/stdout.json', 'run2/automine-01/stderr.raw',
    'run2/reconcile-setup-01/stdout.json', 'run2/reconcile-setup-01/stderr.raw',
    'run2/reconcile-setup-02/stdout.json', 'run2/reconcile-setup-02/stderr.raw',
    'verification/runtime-02/stdout.json', 'verification/runtime-02/stderr.raw', 'verification/runtime-02/EXECUTION.json',
    'verification/host-after/HOST_AFTER_RAW.json', 'verification/host-after/HOST_PRESERVATION.json',
    'verification/host-after/stderr.raw', 'verification/host-after/EXECUTION.json',
    'verification/cleanup-final/CLEANUP.json', 'verification/cleanup-final/stderr.raw', 'verification/cleanup-final/EXECUTION.json',
    'code-review/process-lock/RESULT.json', 'code-review/process-lock/transport.stderr', 'code-review/process-lock/EXECUTION.json',
    'code-review/diagnostics-before/RESULT.json', 'code-review/diagnostics-before/TESTS.log',
    'code-review/diagnostics-before/operation_review.before.py',
    'code-review/diagnostics-after/RESULT.json', 'code-review/diagnostics-after/TESTS.log',
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    content = {}
    files = [*EXACT_FILES, *(directory + '/' + name for directory in ACTION_DIRECTORIES
                           for name in ('stdout.raw', 'stderr.raw', 'EXECUTION.json'))]
    assert len(files) == len(set(files))
    for name in files:
        assert not {'runtime', 'secrets'}.intersection(Path(name).parts)
        assert Path(name).name not in ('config.json', 'state.json', 'password', 'id_ed25519')
        path = EXTERNAL / name
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(EXTERNAL)
        raw = path.read_bytes()
        assert len(raw) <= 4 * 1024 * 1024 and b'-----BEGIN OPENSSH PRIVATE KEY-----' not in raw
        assert b'-----BEGIN PRIVATE KEY-----' not in raw
        content[name] = raw
    # Key actions expose only the driver's already-enforced public schema.
    for name in ('run/key-01/stdout.json', 'run2/key-01/stdout.json'):
        row = json.loads(content[name])
        assert set(row) == {'phase', 'sender', 'secret_exported', 'mode', 'uid', 'rpc_urls_fixed'}
        assert row['secret_exported'] is False
    # Freeze original fixture source bytes from each hash-bound input archive.
    for number in (1, 2):
        base = EXTERNAL / f'inputs/attempt{number}'
        raw = (base / 'BUNDLE.json').read_bytes()
        receipt = json.loads(raw)
        archive = base / 'public-capsule-inputs.tar.gz'
        assert archive.stat().st_size <= 8 * 1024 * 1024 and sha(archive.read_bytes()) == receipt['archive_sha256']
        prefix = f'source-stage{number}/'
        content[prefix + 'BUNDLE.json'] = raw
        with tarfile.open(archive, 'r:gz') as packed:
            content[prefix + 'INPUT_MANIFEST.json'] = packed.extractfile('INPUT_MANIFEST.json').read()
            assert sha(content[prefix + 'INPUT_MANIFEST.json']) == receipt['input_manifest_sha256']
            for name in ('capsule.py', 'offline_cache.py', 'prepare_config.py', 'rpc_proxy.py'):
                member = 'source/reports/ubuntu-keeper-20261121/run/' + name
                blob = packed.extractfile(member).read()
                assert sha(blob) == receipt['manifest']['members'][member]['sha256']
                content[prefix + name] = blob
    assert sum(map(len, content.values())) <= 16 * 1024 * 1024
    manifest = {
        'schema': 1, 'scope': 'preserved_incomplete_Ubuntu_setup_and_new_code_checks_not_daemon_acceptance',
        'members': {name: {'sha256': sha(raw), 'bytes': len(raw)} for name, raw in sorted(content.items())},
        'input_archives_omitted_with_hash_bound_manifests': True,
        'runtime_config_state_keystore_password_environment_included': False,
        'normal_daemon_signing_recovery_qualified': False,
    }
    content['MEMBERS.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    archive = REPORT / 'evidence.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as packed:
        for name, raw in sorted(content.items()):
            packed.writestr(name, raw)
    with zipfile.ZipFile(archive) as packed:
        assert set(packed.namelist()) == set(content)
        for name, raw in content.items():
            assert packed.read(name) == raw
    result = {'schema': 1, 'archive': 'evidence.zip', 'sha256': sha(archive.read_bytes()),
              'bytes': archive.stat().st_size, 'members': len(content), 'member_manifest': manifest,
              'packager_sha256': sha(Path(__file__).read_bytes())}
    with (REPORT / 'EVIDENCE.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'member_manifest'}))


if __name__ == '__main__':
    main()
