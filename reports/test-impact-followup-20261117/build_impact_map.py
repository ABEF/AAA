"""Offline baseline test dependency map. This is NOT execution or branch coverage."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
BASE = 'fdb7562bf56b11d8bade612fdaf7f9a54daf118a'
PARENT = '003c8d8dc88b60cbfbcc8caf61fa864c6487b40f'


def main():
    corpus = json.loads((ROOT / 'reports/test-seal-deep-review-20261117/TEST_CORPUS_SOLIDITY.json').read_text())
    files = {row['file']: row for row in corpus['files']}
    changed = subprocess.check_output(['git', 'diff', '--name-only', PARENT, BASE, '--', 'test'], cwd=ROOT).decode().splitlines()
    roots = set(changed) & files.keys()
    edges = {}; parser_changes = {}
    for name, row in files.items():
        source = subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT).decode('utf-8-sig')
        # Valid Solidity also allows compact `}from` imports. Re-read actual
        # baseline source rather than inheriting the older inventory's parser.
        refs = re.findall(r'\bimport\s+(?:[^;"\']*\bfrom\s*)?["\']([^"\']+)["\'](?:\s+as\s+\w+)?\s*;',source)
        edges[name] = {posixpath.normpath(str(PurePosixPath(name).parent / ref)) for ref in refs if ref.startswith('.')} & files.keys()
        previous = {posixpath.normpath(str(PurePosixPath(name).parent / ref))
                    for ref in row['test_dependencies'] if ref.startswith('.')} & files.keys()
        if edges[name] != previous:
            parser_changes[name] = {'added':sorted(edges[name]-previous),'removed':sorted(previous-edges[name])}
    def closure(name):
        found = set(); pending = [name]
        while pending:
            current = pending.pop()
            if current in found:
                continue
            found.add(current); pending.extend(edges.get(current, set()) - found)
        return found
    consumers = []
    for name, row in sorted(files.items()):
        dependencies = closure(name)
        affected = sorted(roots & dependencies)
        if not affected:
            continue
        consumers.append({'file': name, 'baseline_raw_sha256': row['raw_source_sha256'],
                          'changed_file_itself': name in roots, 'affected_roots': affected,
                          'test_contracts_and_bases': row['contracts'],
                          'declared_test_invariant_methods': row['test_invariant_declarations'],
                          'direct_production_imports': row['production_imports'],
                          'import_dependency_scope': 'Exact relative test imports; not symbol use, reachability or branch coverage',
                          'execution_status': 'Use separately recorded finite observations; no pass inferred from this map'})
    result = {'schema': 1, 'baseline': BASE, 'previous_test_repair_parent': PARENT,
              'changed_test_roots': sorted(roots), 'consumers': consumers,
              'root_count': len(roots), 'consumer_files': len(consumers),
              'declared_methods_in_consumer_files': sum(len(row['declared_test_invariant_methods']) for row in consumers),
              'inherited_methods_not_duplicated_as_declarations': True,
              'recomputed_import_differences_from_old_inventory': parser_changes,
              'runtime_branch_coverage_or_complete_test_audit': False}
    (OWN / 'BASELINE_IMPACT_MAP.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = ['# Repaired test infrastructure: baseline dependency exposure', '',
             'This map locates dependent declarations. It does not prove execution,',
             'assertion strength or branch coverage. Behavior reviews and finite',
             'observations are recorded separately.', '',
             '| Consumer | Changed test roots in dependency closure | Declared methods |',
             '| --- | --- | ---: |']
    for row in consumers:
        lines.append('| `' + row['file'] + '` | ' + ', '.join('`' + name + '`' for name in row['affected_roots']) +
                     ' | ' + str(len(row['declared_test_invariant_methods'])) + ' |')
    (OWN / 'BASELINE_IMPACT_MAP.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('root_count', 'consumer_files', 'declared_methods_in_consumer_files')}))


if __name__ == '__main__':
    main()
