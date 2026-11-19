"""Run only the new maximum-state producer, using owned outputs.

Only an owned export permission is temporarily added, then restored exactly.
Compiler settings, old artifacts, nodes and deployments remain unchanged.
The large aggregate harness allowance is not a transaction-admission budget.
"""
from pathlib import Path
from contextlib import contextmanager
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import tomllib

ROOT = Path.cwd().resolve()
V = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OWN = V / 'maximum-workload-20261119'
TARGET = 'MaximumWorkload20261119'
METHOD = 'testMaximum1000TwoLP65CurrenciesReverseOrderContributionsAndMaintenance20261119()'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
TOOLS = {
    'foundry-v1.4.4/forge.exe': '8500da38f541a1ebd5b97a34c8c5b9b057eba5ad160c657a5224b4e1c8f8e101',
    'toolchain-0.8.26/solc.exe': '537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67',
}


@contextmanager
def export_permissions(original, temporary, folder):
    path = ROOT / 'foundry.toml'
    assert path.read_bytes() == original, 'Concurrent configuration change'
    path.write_bytes(temporary)
    try:
        yield
    finally:
        current = path.read_bytes()
        if current == temporary:
            path.write_bytes(original)
        elif current != original:
            (folder / 'UNEXPECTED_foundry.toml').write_bytes(current)
            raise RuntimeError('Concurrent config preserved rather than overwritten')


def closure(start, configuration):
    remaps = [tuple(row.split('=', 1)) for row in tomllib.loads(configuration.decode())['profile']['default']['remappings']]
    found, todo = {}, [start]
    while todo:
        name = todo.pop()
        if name in found:
            continue
        raw = (ROOT / name).read_bytes()
        found[name] = raw
        text = re.sub(r'/\*.*?\*/', '', raw.decode(), flags=re.S)
        for imp in re.findall(r'^\s*import\s+[^;]*?[\"\']([^\"\']+)[\"\']\s*;', text, flags=re.M):
            if imp.startswith('.'):
                path = os.path.normpath(str(Path(name).parent / imp)).replace('\\', '/')
            else:
                path = imp
                for prefix, replacement in remaps:
                    if imp.startswith(prefix):
                        path = replacement + imp[len(prefix):]
                        break
            assert not path.startswith('../') and (ROOT / path).is_file(), (name, imp, path)
            todo.append(path)
    return found


def main():
    stage = sys.argv[1] if len(sys.argv) == 2 else 'producer01'
    assert len(sys.argv) <= 2 and re.fullmatch(r'producer[0-9]{2}', stage)
    assert (ROOT / 'src/ZZZVault.sol').is_file()
    baseline = json.loads((OWN / 'BASELINE.json').read_bytes())
    original = (ROOT / 'foundry.toml').read_bytes()
    assert SHA(original) == baseline['foundry_toml_sha256']
    for name, pin in {**baseline['source_sha256'], **baseline['protected_sha256']}.items():
        assert SHA((ROOT / name).read_bytes()) == pin, name
    d = OWN / stage
    d.mkdir(exist_ok=False)
    exports = d / 'exports'
    exports.mkdir()
    sources = closure('test/' + TARGET + '.t.sol', original)
    before = {name: SHA(raw) for name, raw in sorted(sources.items())}
    (d / 'COMPILED_INPUT_SOURCE_POOL.json.gz').write_bytes(gzip.compress(json.dumps(
        {'sources': {name: {'content': raw.replace(b'\r\n', b'\n').decode()} for name, raw in sources.items()}},
        separators=(',', ':')).encode(), mtime=0))
    for name in sources:
        if name.startswith('test/Maximum'):
            (d / Path(name).name).write_bytes(sources[name])
    assert original.count(b'fs_permissions = [') == 1
    configuration = original.replace(b'fs_permissions = [', ('fs_permissions = [{ access = "read-write", path = "' + exports.as_posix() + '" }, ').encode())
    config = d / 'foundry.toml'
    config.write_bytes(configuration)
    forge, solc = (V / name for name in TOOLS)
    for name, pin in TOOLS.items():
        assert SHA((V / name).read_bytes()) == pin
    env = {key: value for key, value in os.environ.items() if key.upper() in (
        'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'COMSPEC', 'PATHEXT')}
    env.update(PATH=str(solc.parent) + os.pathsep + str(Path(env.get('SystemRoot', 'C:/Windows')) / 'System32'),
        RAYON_NUM_THREADS='2', POPL_REFERENCE_EXPORT_PATH=str(exports / 'setup'),
        POPL_GAS_PROFILE_EXPORT_ROOT=str(exports), FOUNDRY_GAS_LIMIT='10000000000', FOUNDRY_MEMORY_LIMIT='536870912')
    common = ['--root', str(ROOT)]
    cmd = [str(forge), 'test', '--offline', '--use', str(solc), *common,
        '--match-path', 'test/' + TARGET + '.t.sol', '--match-contract', TARGET + 'Test',
        '--match-test', '^' + METHOD[:-2], '--out', str(OWN / 'test-out'),
        '--cache-path', str(OWN / 'test-cache'), '--code-size-limit', '1000000', '-vv', '--json']
    retained = {Path(name).name for name in sources}
    skipped = sorted({p.name for p in (ROOT / 'test').rglob('*.sol') if p.name not in retained})
    for name in skipped:
        cmd += ['--skip', name]
    start = {'schema': 1, 'baseline_main': baseline['baseline_main'], 'normal_build': baseline['normal_build'],
        'method': METHOD, 'command': cmd, 'runner_sha256': SHA(Path(__file__).read_bytes()),
        'source_before': before, 'compiled_closure_files': len(sources), 'tools': TOOLS,
        'config_sha256': SHA(configuration), 'tracked_config_sha256': SHA(original),
        'compiled_input_pool_sha256': SHA((d / 'COMPILED_INPUT_SOURCE_POOL.json.gz').read_bytes()),
        'skipped_unrelated_test_roots': skipped, 'public_requests_or_transactions': 0,
        'environment': 'Allowlisted OS variables and owned export paths only; no credentials or RPC variables',
        'started_unix': time.time(), 'harness_only_resources': {'gas': 10_000_000_000,
            'memory': 536_870_912, 'test_code_size': 1_000_000, 'contribution': 32_000_000,
            'maintenance': 24_000_000, 'not_cold_transaction_qualification': True}}
    (d / 'START.json').write_text(json.dumps(start, indent=2) + '\n', encoding='utf-8')
    begin = time.monotonic()
    code, error = None, None
    with export_permissions(original, configuration, d):
        probe = subprocess.run([str(forge), 'config', '--json', *common], cwd=ROOT, env=env, capture_output=True, timeout=30)
        (d / 'CONFIG_PROBE.json').write_bytes(probe.stdout)
        (d / 'CONFIG_PROBE.stderr').write_bytes(probe.stderr)
        assert probe.returncode == 0
        parsed = json.loads(probe.stdout)
        assert parsed['gas_limit'] == 10_000_000_000 and parsed['memory_limit'] == 536_870_912
        assert parsed['evm_version'] == 'cancun' and parsed['via_ir'] is True
        assert parsed['optimizer'] is True and parsed['optimizer_runs'] == 1 and parsed['optimizer_details']['yul'] is False
        assert parsed['fs_permissions'][0]['path'] == exports.as_posix()
        assert Path(parsed['src']).resolve() == ROOT / 'src'
        with (d / 'raw.json').open('xb') as out, (d / 'stderr.log').open('xb') as err:
            process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=out, stderr=err,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            (d / 'PID.json').write_text(json.dumps({'pid': process.pid, 'command': cmd}) + '\n', encoding='utf-8')
            try:
                code = process.wait(timeout=2400)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=15)
                error = 'Owned producer timeout; not a pass'
    after = {name: SHA((ROOT / name).read_bytes()) for name in sources}
    methods = []
    try:
        for host, body in json.loads((d / 'raw.json').read_bytes()).items():
            for name, result in body.get('test_results', {}).items():
                methods.append({'id': host + ':' + name, 'status': result.get('status'), 'reason': result.get('reason'),
                    'decoded_logs': result.get('decoded_logs')})
    except (ValueError, AttributeError):
        pass
    artifact = OWN / 'test-out' / (TARGET + '.t.sol') / (TARGET + 'Test.json')
    metadata_verified = False
    if artifact.exists():
        raw = artifact.read_bytes()
        (d / 'producer-artifact.json').write_bytes(raw)
        metadata = json.loads(raw)['metadata']
        sys.path.insert(0, str(ROOT))
        from zzz_ops.abi import keccak256
        assert set(metadata['sources']) == set(sources)
        for name, row in metadata['sources'].items():
            assert row['keccak256'] == '0x' + keccak256(sources[name].replace(b'\r\n', b'\n')).hex(), name
        metadata_verified = True
    expected = 'test/' + TARGET + '.t.sol:' + TARGET + 'Test:' + METHOD
    result = {'schema': 1, 'exit_code': code, 'error': error, 'elapsed_seconds': time.monotonic() - begin,
        'methods': methods, 'source_after': after, 'source_bracket_stable': before == after,
        'tracked_config_unchanged': (ROOT / 'foundry.toml').read_bytes() == original,
        'compiled_source_metadata_verified': metadata_verified, 'unchanged_old_tests_executed': 0,
        'public_requests_or_transactions': 0, 'production_approved': False,
        'raw_sha256': SHA((d / 'raw.json').read_bytes()),
        'artifact_sha256': SHA(artifact.read_bytes()) if artifact.exists() else None}
    result['pass'] = (code == 0 and error is None and len(methods) == 1 and methods[0]['id'] == expected
        and methods[0]['status'] == 'Success' and before == after and result['tracked_config_unchanged'] and metadata_verified)
    (d / 'EXECUTION.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key not in ('source_after', 'methods')}), flush=True)
    for row in methods:
        print(json.dumps({key: value for key, value in row.items() if key != 'decoded_logs'}), flush=True)
    if not methods:
        print((d / 'raw.json').read_text(encoding='utf-8', errors='replace')[-3000:])
    return 0 if result['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
