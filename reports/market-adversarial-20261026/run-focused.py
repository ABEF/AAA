"""Affected actual-v4 integration fixture: new market cases plus its existing behaviors.

Uses refreshed closed AST and the existing normal-profile test selector. Never
contacts an RPC, signer, running Anvil instance, service or transaction journal.
"""
from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE = EXTERNAL / 'reward-resilience-20261026/solidity'
NORMAL = EXTERNAL / 'deep-cleanup-20261025/solidity/source-size-gates.json'
DRIVER = ROOT / 'reports/simplification-20261025/solidity/run-focused.py'
REPORT = Path(__file__).parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value): path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')

def main():
    destination = EXTERNAL / 'market-adversarial-20261026/solidity-final'
    destination.mkdir(parents=True, exist_ok=False)
    payload = json.loads((BASE / 'input.json').read_text())
    normal = json.loads(NORMAL.read_text())
    pins = {**normal['source_sha256'], **normal['dependency_source_sha256'], **normal['build_input_sha256']}
    assert normal['all_pass'] and all(sha(ROOT / name) == expected for name, expected in pins.items())
    assert sha(DRIVER) == 'd95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'
    changed = [name for name, row in payload['sources'].items()
               if (ROOT / name).read_bytes().decode('utf-8-sig') != row['content']]
    assert changed == ['test/IntegratedEconomicConservation.t.sol'], changed
    before = {name: sha(ROOT / name) for name in payload['sources']}
    for name in payload['sources']:
        payload['sources'][name] = {'content': (ROOT / name).read_bytes().decode('utf-8-sig')}
    input_path = destination / 'input.json'; output_path = destination / 'output.json'
    input_path.write_text(json.dumps(payload), encoding='utf-8')
    start = time.monotonic()
    process = subprocess.run([str(EXTERNAL / 'toolchain-0.8.26/solc.exe'), '--standard-json', '--base-path', str(ROOT)],
                             input=input_path.read_bytes(), cwd=ROOT, capture_output=True, timeout=1200)
    output_path.write_bytes(process.stdout[process.stdout.find(b'{'):])
    (destination / 'typecheck-stderr.log').write_bytes(process.stderr)
    compiled = json.loads(output_path.read_bytes())
    errors = [row for row in compiled.get('errors', []) if row.get('severity') == 'error']
    save(REPORT / 'typecheck.json', {'exit_code': process.returncode, 'errors': errors, 'changed_inputs': changed,
         'source_count': len(before), 'seconds': round(time.monotonic() - start, 3),
         'input_sha256': sha(input_path), 'output_sha256': sha(output_path)})
    assert process.returncode == 0 and not errors, errors
    spec = importlib.util.spec_from_file_location('resilience_driver', DRIVER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    import re
    # configureZZZ corrects a shared bootstrap fixture. Recheck the existing
    # composed methods using that fixture, not unrelated Solidity suites.
    module.SELECTION = {'IntegratedEconomicConservationTest': set(re.findall(
        r'function (test\w+)\(', (ROOT / 'test/IntegratedEconomicConservation.t.sol').read_text()))}
    sys.argv = [str(DRIVER), '--evidence', str(destination / 'execution'), '--compiler-input', str(input_path),
                '--compiler-output', str(output_path), '--size-evidence', str(NORMAL)]
    code = module.main()
    assert before == {name: sha(ROOT / name) for name in before}
    assert all(sha(ROOT / name) == expected for name, expected in pins.items())
    save(REPORT / 'bindings.json', {'source_sha256': before, 'reused_normal_sha256': pins,
         'driver_sha256': sha(DRIVER), 'normal_evidence_sha256': sha(NORMAL),
         'input_sha256': sha(input_path), 'output_sha256': sha(output_path),
         'production_solidity_changed': False, 'all_inputs_stable': True})
    for original, target in [('focused-summary.json', 'solidity-summary.json'),
                             ('focused-results.json', 'solidity-results.json'), ('focused-stderr.log', 'solidity-stderr.log')]:
        (REPORT / target).write_bytes((destination / 'execution' / original).read_bytes())
    raise SystemExit(code)

if __name__ == '__main__': main()
