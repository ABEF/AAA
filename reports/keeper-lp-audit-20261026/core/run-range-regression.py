"""One stale-state domain regression, using the pinned existing AST driver.

The failing method runs before the repair; its nine-method fixture runs after
the test-only enum bound repair, each in a new external workspace.
No RPC, signing, running Anvil, journal or operating service is contacted.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE = EXTERNAL / 'full-audit-20261025/principal-gas-attempt2'
NORMAL = EXTERNAL / 'deep-cleanup-20261025/solidity/source-size-gates.json'
DRIVER = ROOT / 'reports/simplification-20261025/solidity/run-focused.py'
METHOD = 'testInactiveAndMissingIdentityCannotAuthorizeRebalance'
TARGET = Path(__file__).parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    phase = sys.argv[1]
    if phase not in ('before', 'after'):
        raise ValueError('Explicit before/after required')
    destination = EXTERNAL / 'keeper-lp-audit-20261026/core' / phase
    if destination.exists():
        raise RuntimeError('Preserve the original attempt, never overwrite it')
    destination.mkdir(parents=True)
    payload = json.loads((BASE / 'input.json').read_text())
    old_output = BASE / 'output.json'
    sizes = json.loads(NORMAL.read_text())
    assert digest(DRIVER) == 'd95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'
    assert len(payload['sources']) == 265
    normal = {**sizes['source_sha256'], **sizes['dependency_source_sha256'], **sizes['build_input_sha256']}
    assert sizes['all_pass'] and all(digest(ROOT / n) == h for n, h in normal.items())
    original = {n: (ROOT / n).read_bytes() for n in payload['sources']}
    changes = [n for n, item in payload['sources'].items()
               if original[n].decode('utf-8-sig') != item['content']]
    assert changes == ([] if phase == 'before' else ['test/RangePolicy.t.sol']), changes
    if phase == 'before':
        compiler_input = BASE / 'input.json'
        compiler_output = old_output
    else:
        for n, raw in original.items():
            payload['sources'][n] = {'content': raw.decode('utf-8-sig')}
        compiler_input = destination / 'input.json'
        compiler_input.write_bytes(json.dumps(payload, sort_keys=True).encode())
        compiler_output = destination / 'output.json'
        start = time.monotonic()
        process = subprocess.run([str(EXTERNAL / 'toolchain-0.8.26/solc.exe'), '--standard-json',
                                  '--base-path', str(ROOT)], input=compiler_input.read_bytes(),
                                 capture_output=True, cwd=ROOT, timeout=1200)
        output = process.stdout[process.stdout.find(b'{'):]
        compiler_output.write_bytes(output)
        (destination / 'typecheck-stderr.log').write_bytes(process.stderr)
        compiled = json.loads(output)
        errors = [row for row in compiled.get('errors', []) if row.get('severity') == 'error']
        save(destination / 'typecheck-summary.json', {'exit_code': process.returncode,
             'errors': errors, 'changed_input': changes, 'inputs': len(original),
             'seconds': round(time.monotonic() - start, 3),
             'compiler_input_sha256': digest(compiler_input), 'compiler_output_sha256': digest(compiler_output)})
        assert process.returncode == 0 and not errors, errors
    before = {n: hashlib.sha256(raw).hexdigest() for n, raw in original.items()}
    save(TARGET / (phase + '-bindings.json'), {'phase': phase, 'source_sha256': before,
         'reused_normal_source_dependency_build_sha256': normal,
         'reused_normal_evidence_sha256': digest(NORMAL), 'AST_input_sha256': digest(compiler_input),
         'AST_output_sha256': digest(compiler_output), 'changed_AST_inputs': changes})
    spec = importlib.util.spec_from_file_location('range_regression_driver', DRIVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SELECTION = {'RangePolicyTest': {METHOD} if phase == 'before' else '*'}
    sys.argv = [str(DRIVER), '--evidence', str(destination / 'execution'),
                '--compiler-input', str(compiler_input), '--compiler-output', str(compiler_output),
                '--size-evidence', str(NORMAL)]
    code = module.main()
    actual = {n: digest(ROOT / n) for n in original}
    assert actual == before and all(digest(ROOT / n) == h for n, h in normal.items())
    summary = json.loads((destination / 'execution/focused-summary.json').read_text())
    save(TARGET / (phase + '-summary.json'), {**summary, 'phase': phase,
         'all_265_sources_unchanged_during_execution': True, 'production_source_changed': False,
         'normal_37_object_evidence_reused': True,
         'compiler_input_sha256': digest(compiler_input), 'compiler_output_sha256': digest(compiler_output)})
    (TARGET / (phase + '-results.json')).write_bytes((destination / 'execution/focused-results.json').read_bytes())
    (TARGET / (phase + '-stderr.log')).write_bytes((destination / 'execution/focused-stderr.log').read_bytes())
    if phase == 'after' and code:
        raise SystemExit(code)


if __name__ == '__main__':
    main()
