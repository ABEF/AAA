"""Execute two new allocation/claim regressions without rerunning unchanged suites.

Uses the prior closed AST source inventory, refreshed from disk, and the normal
compiler profile. No RPC, existing Anvil service, signer or journal is accessed.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE = EXTERNAL / 'keeper-lp-audit-20261026/core/after'
NORMAL = EXTERNAL / 'deep-cleanup-20261025/solidity/source-size-gates.json'
DRIVER = ROOT / 'reports/simplification-20261025/solidity/run-focused.py'
REPORT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    destination = EXTERNAL / 'reward-allocation-20261026/solidity-attempt2'
    destination.mkdir(parents=True, exist_ok=False)
    payload = json.loads((BASE / 'input.json').read_text())
    sizes = json.loads(NORMAL.read_text())
    normal = {**sizes['source_sha256'], **sizes['dependency_source_sha256'], **sizes['build_input_sha256']}
    assert sizes['all_pass'] and all(sha(ROOT / n) == h for n, h in normal.items())
    assert sha(DRIVER) == 'd95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'
    changed = [name for name, row in payload['sources'].items()
               if (ROOT / name).read_bytes().decode('utf-8-sig') != row['content']]
    assert changed == ['test/NativeFeeRewards.t.sol'], changed
    before = {name: sha(ROOT / name) for name in payload['sources']}
    for name in payload['sources']:
        payload['sources'][name] = {'content': (ROOT / name).read_bytes().decode('utf-8-sig')}
    compiler_input = destination / 'input.json'
    compiler_output = destination / 'output.json'
    compiler_input.write_text(json.dumps(payload), encoding='utf-8')
    start = time.monotonic()
    process = subprocess.run([str(EXTERNAL / 'toolchain-0.8.26/solc.exe'), '--standard-json',
                              '--base-path', str(ROOT)], input=compiler_input.read_bytes(),
                             capture_output=True, cwd=ROOT, timeout=1200)
    output = process.stdout[process.stdout.find(b'{'):]
    compiler_output.write_bytes(output)
    (destination / 'typecheck-stderr.log').write_bytes(process.stderr)
    compiled = json.loads(output)
    errors = [row for row in compiled.get('errors', []) if row.get('severity') == 'error']
    save(REPORT / 'typecheck.json', {'exit_code': process.returncode, 'errors': errors,
         'changed_inputs': changed, 'source_count': len(before), 'seconds': round(time.monotonic() - start, 3),
         'input_sha256': sha(compiler_input), 'output_sha256': sha(compiler_output)})
    assert process.returncode == 0 and not errors, errors
    spec = importlib.util.spec_from_file_location('allocation_regression_driver', DRIVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SELECTION = {'NativeFeeRewardsTest': {
        'testThreeHolderClaimsPreserveExactSplitAndDormantExclusion',
        'testFuzzClaimOrderAndFrequencyCannotRedistributeAnyNftRewards',
    }}
    sys.argv = [str(DRIVER), '--evidence', str(destination / 'execution'),
                '--compiler-input', str(compiler_input), '--compiler-output', str(compiler_output),
                '--size-evidence', str(NORMAL)]
    code = module.main()
    assert before == {name: sha(ROOT / name) for name in before}
    assert all(sha(ROOT / n) == h for n, h in normal.items())
    save(REPORT / 'bindings.json', {'source_sha256': before, 'reused_normal_sha256': normal,
         'reused_size_evidence_sha256': sha(NORMAL), 'driver_sha256': sha(DRIVER),
         'AST_input_sha256': sha(compiler_input), 'AST_output_sha256': sha(compiler_output),
         'production_solidity_changed': False, 'all_inputs_unchanged_during_execution': True})
    for source, target in [('focused-summary.json', 'solidity-summary.json'),
                           ('focused-results.json', 'solidity-results.json'),
                           ('focused-stderr.log', 'solidity-stderr.log')]:
        (REPORT / target).write_bytes((destination / 'execution' / source).read_bytes())
    raise SystemExit(code)


if __name__ == '__main__':
    main()
