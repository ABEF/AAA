"""Check scenario inventory/source bindings; this is not an execution test suite."""
from pathlib import Path
from collections import Counter
import ast
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
NORMAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/deep-cleanup-20261025/solidity/source-size-gates.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    catalog_path = ROOT / 'docs/function-reference.json'
    catalog = json.loads(catalog_path.read_text())
    expected = {(c['name'], f['kind'], f['signature'])
                for c in catalog['contracts'] for f in c['functions']}
    by_contract = Counter(c['name'] for c in catalog['contracts'] for _f in c['functions'])
    found = set(); counts = Counter(); scenarios = 0; sources = {}; partitions = []
    for name, field in (('rights-review.json', 'rows'), ('principal-review.json', 'functions'),
                        ('custody-review.json', 'functions')):
        data = json.loads((HERE / name).read_text())
        rows = data[field]
        for row in rows:
            key = (row['contract'], row['kind'], row['signature'])
            assert key in expected and key not in found, key
            found.add(key); counts[row['kind']] += 1
            assert len(row['scenarios']) >= 3 and len(set(row['scenarios'])) == len(row['scenarios']), key
            assert all(isinstance(s, str) and s.strip() for s in row['scenarios']), key
            scenarios += len(row['scenarios'])
            locations = row.get('source_locations') or [row['source_location']]
            for loc in locations:
                if isinstance(loc, str):
                    path, line = loc.rsplit(':', 1); line = int(line)
                else:
                    path, line = loc.get('path', loc.get('file')), loc['line']
                assert type(line) is int and 1 <= line <= len((ROOT / path).read_text(encoding='utf-8-sig').splitlines()), (key, loc)
        for name_, digest in data['source_sha256'].items():
            assert sha(ROOT / name_) == digest, name_
            if name_ in sources: assert sources[name_] == digest, name_
            sources[name_] = digest
        partitions.append({'path': name, 'sha256': sha(HERE / name), 'rows': len(rows),
                           'assessment': 'Static source/call-path scenario review, not new execution of each scenario.'})
    assert found == expected and counts == {'function': 608, 'constructor': 31, 'receive': 13}
    # This interface has no deployed implementation: its record/header fields
    # and signatures were separately checked against concrete NFT/companion paths.
    interface = 'src/interfaces/IZZZNFTCanonical.sol'
    sources[interface] = sha(ROOT / interface)
    local_sources = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'src').rglob('*.sol')}
    assert local_sources <= sources.keys() and len(local_sources) == 44
    for name, digest in catalog['source_snapshot']['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    normal = json.loads(NORMAL.read_text())
    assert normal['all_pass']
    reused = {**normal['source_sha256'], **normal['dependency_source_sha256'], **normal['build_input_sha256']}
    for name, digest in reused.items(): assert sha(ROOT / name) == digest, name
    save('coverage.json', {'catalog_sha256': sha(catalog_path), 'partitions': partitions,
        'contracts': len(by_contract), 'counts': dict(counts), 'callable_rows': len(found),
        'scenario_instances': scenarios, 'minimum_scenarios_per_row': 3,
        'missing': [], 'duplicates': [], 'source_sha256': sources,
        'production_solidity_units': len(local_sources), 'production_solidity_changed': False,
        'normal_evidence_sha256': sha(NORMAL), 'reused_normal_sha256': reused,
        'normal_object_gates_reused': len(normal['gates']), 'fresh_solidity_tests': 0,
        'fresh_full_static_analysis': False, 'scenario_mapping_is_not_execution_or_security_proof': True})
    methods = set(); executions = []; skips = []
    for path in ('affected-suite.json',):
        data = json.loads((HERE / path).read_text())
        assert data['successful'] and not data['failures'] and not data['errors']
        assert not data['source_changes_during_run']
        ids = data.get('executed_methods', data['selected_methods'])
        assert len(ids) == len(set(ids)) == data['tests_run']
        assert not methods.intersection(ids), 'Overlapping execution scopes must not be added'
        methods.update(ids)
        skips.extend(data['skips'])
        for name, digest in data['source_sha256_after'].items(): assert sha(ROOT / name) == digest, name
        executions.append({'path': path, 'tests_run': data['tests_run'], 'sha256': sha(HERE / path)})
    # The CLI and transport-only stages overlap the final post-watchdog selection.
    for path in ('phase1-rpc/affected-suite.json', 'ops-input/after.json'):
        earlier = json.loads((HERE / path).read_text())
        earlier_ids = earlier.get('executed_methods', earlier['selected_methods'])
        assert set(earlier_ids) <= methods
    save('execution-scopes.json', {'receipts': executions, 'unique_executed_methods': len(methods),
        'passes': len(methods) - len(skips), 'skips': skips,
        'method_ids': sorted(methods), 'source_inputs_stable': True,
        'new_method_prefixes': ['tests_python.test_rpc_integrity.', 'tests_python.test_holder_inventory_input.',
                                'tests_python.test_keeper_watchdog.'],
        'new_methods_in_final_scopes': sum(i.startswith(('tests_python.test_rpc_integrity.',
            'tests_python.test_holder_inventory_input.', 'tests_python.test_keeper_watchdog.')) for i in methods),
        'scope': 'Actual read-RPC, budgets, history adapter, holder CLI, keeper watchdog/main/recovery local fixtures; not actual systemd/operating qualification.',
        'installed_service_or_public_transaction': False, 'production_approved': False})
    baseline = subprocess.check_output(['git', 'show', 'c3289a844f304803495597298688b1d6d89862be:keeper/monitor.py'],
                                       cwd=ROOT, stderr=subprocess.DEVNULL).decode()
    current = (ROOT / 'keeper/monitor.py').read_text()
    def keeper_ast(text):
        return ast.dump(next(n for n in ast.parse(text).body if isinstance(n, ast.ClassDef) and n.name == 'Keeper'),
                        include_attributes=False)
    assert keeper_ast(baseline) == keeper_ast(current), 'Do not conflate main supervision with financial/recovery edits'
    save('keeper-core-equivalence.json', {'baseline': 'c3289a844f304803495597298688b1d6d89862be',
        'class_Keeper_ast_identical': True, 'source_change': 'watchdog import/main startup and progress integration only',
        'current_monitor_sha256': sha(ROOT / 'keeper/monitor.py'),
        'watchdog_sha256': sha(ROOT / 'keeper/watchdog.py'),
        'unit_sha256': sha(ROOT / 'keeper/zzz-keeper.service'),
        'unit_is_example_only_no_service_rollout': True})
    print(json.dumps({'contracts': len(by_contract), 'callable_rows': len(found), 'scenario_instances': scenarios,
                      'production_sources': len(local_sources), 'unique_affected_python': len(methods)}))


if __name__ == '__main__':
    main()
