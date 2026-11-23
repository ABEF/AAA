"""Static, hash-bound supplement. Never imports or executes production modules."""
from collections import Counter
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
CURRENT = ROOT / 'reports/wallet-stack-20261123/FUNCTION_INVENTORY.json'
PREVIOUS = ROOT / 'reports/compact-wallet-20261121/FUNCTION_INVENTORY.json'
YUL = ROOT / 'reports/readiness-advance-20261120/ANONYMOUS_CODE_INVENTORY.json'
OUTPUT = ROOT / 'reports/wallet-stack-20261123/ANONYMOUS_CODE_INVENTORY.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    current_raw = CURRENT.read_bytes()
    current = json.loads(current_raw)
    previous = json.loads(PREVIOUS.read_bytes())
    assert current['authenticated_source_maps'] == previous['authenticated_source_maps']
    assert {k: current['counts'][k] for k in ('project_sources', 'dependency_sources', 'build_controls', 'abi_rows')} == {
        'project_sources': 61, 'dependency_sources': 39, 'build_controls': 4, 'abi_rows': 1021}
    rows = []
    for entry in current['python_sources']:
        path = entry['path']
        if entry['content_source'] == 'preserved_historical_HEAD_blob':
            raw = subprocess.run(['git', 'show', 'HEAD:' + path], cwd=ROOT,
                                 check=True, capture_output=True, timeout=30).stdout
        else:
            raw = (ROOT / path).read_bytes()
        assert sha(raw) == entry['sha256'] and len(raw) == entry['byte_length']
        tree = ast.parse(raw, filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Lambda):
                rows.append({'source': path, 'source_sha256': entry['sha256'],
                             'line': node.lineno, 'column': node.col_offset,
                             'end_line': node.end_lineno, 'kind': 'lambda',
                             'coverage_status': 'source_inventory_only_not_execution'})
    yul_raw = YUL.read_bytes()
    prior_yul = json.loads(yul_raw)
    yul_rows = prior_yul['solidity_named_yul_helpers']
    assert len(yul_rows) == prior_yul['named_yul_helper_count'] == 2
    assert all(row['source'] in current['authenticated_source_maps']['source_sha256'] for row in yul_rows)
    return {'schema': 1, 'kind': 'anonymous_code_source_inventory_not_execution',
            'function_inventory_sha256': sha(current_raw),
            'python_files': len(current['python_sources']),
            'python_named_definition_kinds': dict(sorted(Counter(row['kind'] for row in current['python_definitions']).items())),
            'python_lambdas': sorted(rows, key=lambda row: (row['source'], row['line'], row['column'])),
            'lambda_count': len(rows), 'solidity_named_yul_helpers': yul_rows,
            'named_yul_helper_count': len(yul_rows),
            'yul_reuse': {'path': YUL.relative_to(ROOT).as_posix(), 'sha256': sha(yul_raw),
                         'unchanged_authenticated_f6_source_maps': True},
            'inline_assembly_and_generator_bodies': 'Remain within authenticated parent-function source; no dynamic coverage claimed.',
            'source_boundary': 'Current hash-checked production Python list; protected run-fork edits remain excluded in favor of HEAD. No application, tests, network or compiler executed.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    document = build()
    encoded = (json.dumps(document, sort_keys=True, indent=2) + '\n').encode()
    if args.check:
        assert OUTPUT.read_bytes() == encoded
    else:
        with OUTPUT.open('xb') as stream:
            stream.write(encoded)
    print(json.dumps({'checked': args.check, 'sha256': sha(encoded),
                      'python_files': document['python_files'],
                      'named_kinds': document['python_named_definition_kinds'],
                      'lambdas': document['lambda_count'],
                      'named_yul_helpers': document['named_yul_helper_count']}, sort_keys=True))
