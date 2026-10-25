"""Only the native royalty-custody deferred-eligibility producer boundary.

Reuse unchanged production-size evidence and the hash-pinned AST driver.  All
current project/dependency inputs and compiler bindings are checked before/after.
No RPC, public signer or existing Anvil instance is used.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BUILD = EXTERNAL / 'day-readiness-20261025/solidity'
NORMAL = EXTERNAL / 'deep-cleanup-20261025/solidity/source-size-gates.json'
SUMMARY = ROOT / 'reports/day-readiness-20261025/solidity/typecheck-summary.json'
EVIDENCE = BUILD / 'native-custody-boundary'
DRIVER = ROOT / 'reports/simplification-20261025/solidity/run-focused.py'
DRIVER_SHA = 'd95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')


def bindings(stage):
    assert digest(DRIVER) == DRIVER_SHA
    summary = load(SUMMARY)
    sizes = load(NORMAL)
    compiler_input = BUILD / 'all-source-typecheck-input.json'
    compiler_output = BUILD / 'all-source-typecheck.json'
    assert summary['all_pass'] and sizes['all_pass']
    assert digest(compiler_input) == summary['compiler_input_sha256']
    assert digest(compiler_output) == summary['compiler_output_sha256']
    assert digest(NORMAL) == summary['normal_size_evidence_reused_sha256']
    assert digest(EXTERNAL / 'toolchain-0.8.26/solc.exe') == summary['compiler_binary_sha256']
    expected = summary['source_sha256']
    provided = load(compiler_input)['sources']
    assert len(expected) == len(provided) == 265
    actual = {name: digest(ROOT / name) for name in expected}
    assert actual == expected, 'Project/dependency input drift after current AST'
    for name, item in provided.items():
        assert (ROOT / name).read_bytes().decode('utf-8-sig') == item['content'], name
    normal = dict(sizes['source_sha256'])
    normal.update(sizes['dependency_source_sha256'])
    assert len(normal) == 75
    assert all(actual[name] == value for name, value in normal.items())
    project = sum(name.startswith(('src/', 'test/', 'script/')) for name in expected)
    return {'stage': stage, 'driver_sha256': DRIVER_SHA,
            'compiler_input_sha256': digest(compiler_input),
            'compiler_output_sha256': digest(compiler_output),
            'normal_size_evidence_sha256': digest(NORMAL),
            'project_inputs': project, 'installed_dependency_inputs': len(expected)-project,
            'normal_build_inputs': len(normal), 'all_match': True,
            'source_sha256': actual}


EVIDENCE.mkdir(parents=True, exist_ok=True)
save(EVIDENCE / 'bindings-before.json', bindings('before'))
spec = importlib.util.spec_from_file_location('day_readiness_custody_runner', DRIVER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.SELECTION = {'RoyaltyCustodyTest': {
    'testNativeCustodyDefersOnlyNewNativeEligibilityWithoutRetroactiveFees',
}}
sys.argv = [str(DRIVER), '--evidence', str(EVIDENCE),
            '--compiler-input', str(BUILD / 'all-source-typecheck-input.json'),
            '--compiler-output', str(BUILD / 'all-source-typecheck.json'),
            '--size-evidence', str(NORMAL), *sys.argv[1:]]
try:
    code = module.main()
finally:
    save(EVIDENCE / 'bindings-after.json', bindings('after'))
    assert load(EVIDENCE / 'bindings-before.json')['source_sha256'] == load(EVIDENCE / 'bindings-after.json')['source_sha256']
raise SystemExit(code)
