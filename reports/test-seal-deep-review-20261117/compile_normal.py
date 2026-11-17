"""Rebuild the four changed production sources under the accepted normal profile.

No test execution, signer, RPC, deployment or toolchain override. Outputs are
exclusive; this is a source-scoped evidence producer, not a deployment tool.
"""
from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/operator-behavior-followup-20261117/build'
COMPILER_SHA = '537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    compiler, destination = (Path(v).resolve() for v in sys.argv[1:])
    if sha(compiler.read_bytes()) != COMPILER_SHA:
        raise ValueError('Pinned compiler identity differs')
    destination.mkdir(exist_ok=False)
    old = gzip.decompress((BASE / 'compiler-input.json.gz').read_bytes())
    source = json.loads(old)
    changed, pins = [], {}
    for name, row in source['sources'].items():
        raw = (ROOT / name).read_bytes()
        pins[name] = sha(raw)
        if row['content'].encode() != raw:
            changed.append(name)
            row['content'] = raw.decode('utf-8')
    if set(changed) != {'src/ZZZVault.sol', 'src/ZZZNFTMetadata.sol', 'src/ZZZMigrationBudget.sol', 'src/ZZZCustodyValidation.sol'} or len(pins) != 100:
        raise ValueError('Unexpected source drift from the accepted normal build')
    payload = json.dumps(source, separators=(',', ':'), ensure_ascii=True).encode()
    (destination / 'compiler-input.json').write_bytes(payload)
    command = [str(compiler), '--standard-json']
    start = dict(command=command, compiler_sha256=COMPILER_SHA,
                 baseline_input_sha256=sha(old), input_sha256=sha(payload),
                 source_sha256=pins, changed_sources=changed,
                 settings=source['settings'], codegen_settings_unchanged=True,
                 old_test_methods_executed=0, production_approved=False)
    save(destination / 'START.json', start)
    keep = ('SystemRoot', 'WINDIR', 'SystemDrive', 'COMSPEC', 'PATHEXT',
            'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'PROGRAMDATA')
    environment = {k: os.environ[k] for k in keep if k in os.environ}
    environment['PATH'] = str(compiler.parent) + os.pathsep + str(Path(environment.get('SystemRoot', 'C:/Windows')) / 'System32')
    began = time.monotonic()
    with (destination / 'compiler-input.json').open('rb') as inp, \
            (destination / 'compiler-output.json').open('xb') as out, \
            (destination / 'stderr.txt').open('xb') as err:
        process = subprocess.Popen(command, stdin=inp, stdout=out, stderr=err,
                                   cwd=destination, env=environment,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        save(destination / 'PID.json', {'owned_pid': process.pid})
        try:
            status = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
            raise
    if pins != {name: sha((ROOT / name).read_bytes()) for name in pins}:
        raise ValueError('Source changed during compilation')
    if sha(compiler.read_bytes()) != COMPILER_SHA:
        raise ValueError('Compiler changed during compilation')
    raw = (destination / 'compiler-output.json').read_bytes()
    compiled = json.loads(raw)
    errors = [x for x in compiled.get('errors', []) if x['severity'] == 'error']
    gates = []
    if not errors:
        for gate in json.loads((BASE / 'normal-size-evidence.json').read_bytes())['gates']:
            obj = compiled['contracts'][gate['path']][gate['name']]
            runtime = len(obj['evm']['deployedBytecode']['object']) // 2
            creation = len(obj['evm']['bytecode']['object']) // 2
            gates.append({**gate, 'runtime': runtime, 'creation': creation,
                          'runtime_margin': 24576 - runtime,
                          'maximum_total_argument_bytes': 49152 - creation,
                          'runtime_ok': runtime <= 24576,
                          'creation_ok': creation + gate['minimum_args'] <= 49152})
    result = dict(exit_code=status, seconds=time.monotonic() - began, errors=errors,
                  gates=gates, all_pass=status == 0 and not errors and len(gates) == 48 and
                  all(g['runtime_ok'] and g['creation_ok'] for g in gates),
                  source_unchanged=True, settings=source['settings'],
                  source_sha256={n: h for n, h in pins.items() if n.startswith('src/')},
                  dependency_source_sha256={n: h for n, h in pins.items() if not n.startswith('src/')},
                  compiler_content_sha256={n: sha(v['content'].encode()) for n, v in source['sources'].items()},
                  compiler_input_sha256=sha(payload), compiler_output_sha256=sha(raw),
                  solc_exit_code=status, solc_executable_sha256=COMPILER_SHA,
                  solc_executable_unchanged=True, source_count=100,
                  compiled_source_count=len(compiled.get('sources', {})),
                  closed_input_inventory=True, unchanged_before_build=True,
                  unchanged_during_build=True, unexpected_implicit_sources=[],
                  missing_compiled_sources=[], production_approved=False,
                  normal_limits={'runtime_bytes': 24576,
                    'initcode_with_original_minimum_arguments_bytes': 49152})
    # The function catalogue also authenticates the retained normal profile.
    previous_inputs = json.loads((BASE / 'normal-size-evidence.json').read_bytes())['build_input_sha256']
    final_inputs = {name: sha((ROOT/name).read_bytes()) for name in previous_inputs}
    for name, pin in previous_inputs.items():
        if final_inputs[name] != pin:
            if name != 'foundry.toml': raise ValueError('Unexpected build-input change: '+name)
            current = (ROOT/name).read_bytes()
            permission = b', { access = "read", path = "./test/fixtures/seal-critical-003c8d8" }'
            if current.count(permission)!=1 or sha(current.replace(permission,b''))!=pin:
                raise ValueError('Unexpected Foundry configuration delta')
    result['build_input_sha256'] = final_inputs
    result['build_input_delta'] = 'Only read permission for pinned public test fixtures; compiler/size/gas/ffi settings unchanged.'
    save(destination / 'normal-size-evidence.json', result)
    print(json.dumps({k: result[k] for k in ('exit_code', 'seconds', 'all_pass', 'errors')}))
    print(json.dumps({'changed_gates': [g for g in gates if g['name'] in ('ZZZVault','ZZZNFTMetadata','ZZZMigrationBudget','ZZZCustodyValidation','ZZZMigration')]}))
    return 0 if result['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
