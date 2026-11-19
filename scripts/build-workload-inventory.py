"""Build/check a source-pinned workload inventory; never infer test coverage.

Reads the reviewed F6 compiler AST and function catalogue without compiling,
executing application modules, running tests, contacting RPC or signing.
"""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
BUILD_ID = 'activation-final-six-20261118'
# A caller-supplied plan is not a positive trust manifest. Future builds or
# reference revisions require an explicit reviewed update to this allowlist.
TRUSTED_INPUTS = {
    'trusted_build_record': {
        'path': 'reports/activation-final-six-20261118/build/final/normal-size-evidence.json',
        'sha256': '4c321ea3783eaede93bdf39d8de77254b5cdf3e99ea4126d726134c8cd4ceac2',
    },
    'function_reference': {
        'path': 'docs/function-reference.json',
        'sha256': '210c0f84c297b8f94dc4e103cf19e8f1aa3aed8d4d8bd8a2b1de9dbf4bf8bcfe',
    },
    'compiler_output': {
        'path': 'reports/activation-final-six-20261118/build/final/compiler-output.json.gz',
        'sha256': 'aceb5510485a5a0c28945cb4b4df71c66305dff7f1cb058435a464ff42df4a89',
        'decoded_sha256': '4614afcbd97bd5d1ced6e68982559256045ef56ec67d632f971d8a590b6eb983',
    },
}
PYTHON_COMPONENTS = ('frontend_api', 'keeper', 'indexer', 'zzz_ops', 'scripts')
PRESERVED_HEAD_PYTHON = frozenset(('scripts/run-fork-checks.py',))
MAX_PLAN_BYTES = 2 * 1024 * 1024
MAX_REFERENCE_BYTES = 16 * 1024 * 1024
MAX_COMPRESSED_BYTES = 32 * 1024 * 1024
MAX_COMPILER_BYTES = 128 * 1024 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_PYTHON_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_PYTHON_FILES = 2000
MAX_AST_NODES = 2_000_000
MAX_SECONDS = 120


class InventoryError(ValueError):
    """A missing, malformed, stale or unreviewed inventory input."""


def require(condition, message):
    if not condition:
        raise InventoryError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def duplicate_safe(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON member')
        result[key] = value
    return result


def decode_json(data, label):
    try:
        value = json.loads(data.decode('utf-8-sig'), object_pairs_hook=duplicate_safe,
                           parse_constant=lambda _x: (_ for _ in ()).throw(
                               InventoryError('Nonfinite JSON number')))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InventoryError('Invalid UTF-8 JSON: ' + label) from exc
    require(isinstance(value, dict), 'Expected JSON object: ' + label)
    return value


def canonical(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def relative_path(value):
    require(isinstance(value, str) and value and '\\' not in value and '\x00' not in value,
            'Expected canonical repository-relative path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and value == path.as_posix() and
            not any(part in ('', '.', '..') for part in path.parts) and
            ':' not in value, 'Path must stay inside the repository')
    return value


def repo_path(value):
    relative_path(value)
    path = ROOT / value
    require(path.resolve().is_relative_to(ROOT), 'Input path resolves outside repository')
    return path


def bounded_read(path, maximum):
    require(path.is_file(), 'Missing input: ' + str(path.relative_to(ROOT))
            if path.is_relative_to(ROOT) else 'Missing input file')
    require(path.stat().st_size <= maximum, 'Input exceeds byte budget')
    with path.open('rb') as handle:
        data = handle.read(maximum + 1)
    require(len(data) <= maximum, 'Input grew beyond byte budget')
    return data


def pinned(plan, name, maximum):
    item = plan.get(name)
    require(isinstance(item, dict) and set(item) >= {'path', 'sha256'},
            'Missing pinned plan input: ' + name)
    require(item == TRUSTED_INPUTS.get(name),
            'Unreviewed pinned inventory input: ' + name)
    require(isinstance(item['sha256'], str) and re.fullmatch('[0-9a-f]{64}', item['sha256']),
            'Expected lowercase SHA256: ' + name)
    data = bounded_read(repo_path(item['path']), maximum)
    require(digest(data) == item['sha256'], 'Pinned input hash differs: ' + name)
    return data


def git(*args):
    try:
        result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                                timeout=30, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise InventoryError('Required read-only Git operation failed') from exc
    return result.stdout


def check_deadline(start):
    require(time.monotonic() - start <= MAX_SECONDS, 'Inventory work deadline exceeded')


def canonical_type(item):
    kind = item.get('type')
    require(isinstance(kind, str), 'Missing ABI type')
    if kind.startswith('tuple'):
        parts = item.get('components')
        require(isinstance(parts, list), 'Missing tuple ABI components')
        return '(' + ','.join(canonical_type(x) for x in parts) + ')' + kind[5:]
    return kind


def abi_identity(item):
    kind = item.get('type')
    require(kind in ('function', 'constructor', 'receive', 'fallback'), 'Unsupported callable kind')
    name = item.get('name') if kind == 'function' else kind
    require(isinstance(name, str) and name, 'Missing callable name')
    args = item.get('inputs', [])
    require(isinstance(args, list), 'Malformed callable arguments')
    return kind, name + '(' + ','.join(canonical_type(x) for x in args) + ')'


def parameter_inventory(parameters):
    require(isinstance(parameters, dict) and isinstance(parameters.get('parameters'), list),
            'Malformed AST parameter list')
    return [{'name': p.get('name', ''), 'type': p.get('typeDescriptions', {}).get('typeString'),
             'storage_location': p.get('storageLocation'), 'ast_id': p.get('id')}
            for p in parameters['parameters']]


def source_location(node, source_id, source):
    raw = node.get('src')
    require(isinstance(raw, str) and re.fullmatch(r'\d+:\d+:\d+', raw),
            'Malformed compiler source location')
    start, length, index = map(int, raw.split(':'))
    require(index == source_id and start + length <= len(source),
            'Compiler source location differs from authenticated source')
    return {'byte_start': start, 'byte_length': length, 'compiler_source_index': index,
            'line': source[:start].count(b'\n') + 1}


def solidity_definitions(compiler, sources, source_families, source_bytes, start):
    definitions, modifiers = [], []
    bodyless = 0
    ids = set()
    visited = 0
    for path in sorted(sources):
        tree = compiler['sources'][path]
        require(type(tree.get('id')) is int and isinstance(tree.get('ast'), dict),
                'Compiler output has no source AST: ' + path)
        require(tree['ast'].get('absolutePath') == path, 'Compiler AST source path differs')
        stack = [(tree['ast'], None)]
        while stack:
            check_deadline(start)
            node, owner = stack.pop()
            visited += 1
            require(visited <= MAX_AST_NODES, 'Compiler AST node budget exceeded')
            if not isinstance(node, dict):
                continue
            kind = node.get('nodeType')
            if kind == 'ContractDefinition':
                owner = node.get('name')
                require(isinstance(owner, str) and owner, 'Unnamed compiler contract')
            if kind in ('FunctionDefinition', 'ModifierDefinition'):
                implemented = isinstance(node.get('body'), dict)
                if kind == 'FunctionDefinition' and not implemented:
                    bodyless += 1
                elif implemented:
                    node_id = node.get('id')
                    require(type(node_id) is int and node_id not in ids, 'Duplicate AST definition ID')
                    ids.add(node_id)
                    item = {'id': 'solidity:' + path + ':' + str(node_id),
                            'source': path, 'source_sha256': sources[path], 'contract': owner,
                            'families': sorted(source_families[path]), 'ast_id': node_id,
                            'kind': node.get('kind', 'modifier' if kind == 'ModifierDefinition' else None),
                            'name': node.get('name', ''), 'visibility': node.get('visibility'),
                            'state_mutability': node.get('stateMutability'), 'implemented': True,
                            'parameters': parameter_inventory(node['parameters']),
                            'location': source_location(node, tree['id'], source_bytes[path]),
                            'coverage_status': 'inventory_only_not_dynamic_coverage'}
                    if kind == 'FunctionDefinition':
                        item['outputs'] = parameter_inventory(node['returnParameters'])
                        item['modifier_references'] = [
                            {'name': m.get('modifierName', {}).get('name'),
                             'referenced_declaration': m.get('modifierName', {}).get('referencedDeclaration')}
                            for m in node.get('modifiers', [])]
                        item['selector'] = node.get('functionSelector')
                        definitions.append(item)
                    else:
                        modifiers.append(item)
            for value in node.values():
                if isinstance(value, dict):
                    stack.append((value, owner))
                elif isinstance(value, list):
                    stack.extend((child, owner) for child in reversed(value) if isinstance(child, dict))
    return (sorted(definitions, key=lambda x: (x['source'], x['location']['byte_start'], x['ast_id'])),
            sorted(modifiers, key=lambda x: (x['source'], x['location']['byte_start'], x['ast_id'])), bodyless)


def python_arguments(node):
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    default_start = len(positional) - len(args.defaults)
    result = []
    for i, argument in enumerate(positional):
        result.append({'name': argument.arg, 'kind': 'positional_only' if i < len(args.posonlyargs)
                       else 'positional_or_keyword', 'has_default': i >= default_start})
    if args.vararg:
        result.append({'name': args.vararg.arg, 'kind': 'varargs', 'has_default': False})
    result.extend({'name': argument.arg, 'kind': 'keyword_only', 'has_default': default is not None}
                  for argument, default in zip(args.kwonlyargs, args.kw_defaults))
    if args.kwarg:
        result.append({'name': args.kwarg.arg, 'kind': 'kwargs', 'has_default': False})
    return result


def python_inventory(plan, start):
    raw = git('ls-files', '-z', '--', *PYTHON_COMPONENTS)
    require(len(raw) <= MAX_PLAN_BYTES, 'Tracked Python path inventory exceeds byte budget')
    paths = [p for p in raw.decode('utf-8').split('\0') if p.endswith('.py')]
    require(len(paths) == len(set(paths)), 'Repeated tracked Python path')
    extra = plan.get('additional_python_paths', [])
    require(isinstance(extra, list) and len(extra) == len(set(extra)), 'Repeated additional Python path')
    for name in extra:
        relative_path(name)
        require(name.endswith('.py') and PurePosixPath(name).parts[0] in PYTHON_COMPONENTS,
                'Additional Python path is outside production components')
        require(name not in PRESERVED_HEAD_PYTHON, 'Cannot adopt a protected Python working tree')
    names = sorted(set(paths) | set(extra))
    require(0 < len(names) <= MAX_PYTHON_FILES, 'Python file count exceeds budget')
    files, definitions, total = [], [], 0
    for name in names:
        check_deadline(start)
        relative_path(name)
        preserved = name in PRESERVED_HEAD_PYTHON
        if preserved:
            data = git('show', 'HEAD:' + name)
            require(len(data) <= MAX_SOURCE_BYTES, 'Protected Git source exceeds byte budget')
            origin = 'preserved_historical_HEAD_blob'
        else:
            data = bounded_read(repo_path(name), MAX_SOURCE_BYTES)
            origin = 'explicit_plan_working_tree' if name in extra else 'tracked_working_tree'
        total += len(data)
        require(total <= MAX_TOTAL_PYTHON_BYTES, 'Aggregate Python byte budget exceeded')
        try:
            tree = ast.parse(data, filename=name)
        except (SyntaxError, ValueError, UnicodeError, RecursionError) as exc:
            raise InventoryError('Invalid Python source: ' + name) from exc
        file_hash = digest(data)
        files.append({'path': name, 'sha256': file_hash, 'byte_length': len(data),
                      'content_source': origin,
                      'working_tree_adopted': not preserved,
                      'git_blob_id': git('rev-parse', 'HEAD:' + name).decode('ascii').strip()
                      if preserved else None})
        stack = [(tree, ())]
        while stack:
            node, owners = stack.pop()
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = '.'.join((*owners, node.name))
                definitions.append({'id': 'python:' + name + ':' + qualified + ':' + str(node.lineno),
                                    'source': name, 'source_sha256': file_hash,
                                    'component': PurePosixPath(name).parts[0],
                                    'qualified_name': qualified,
                                    'kind': 'class' if isinstance(node, ast.ClassDef) else
                                    'async_function' if isinstance(node, ast.AsyncFunctionDef) else 'function',
                                    'line': node.lineno, 'end_line': node.end_lineno,
                                    'arguments': [] if isinstance(node, ast.ClassDef) else python_arguments(node),
                                    'content_source': origin,
                                    'coverage_status': 'inventory_only_not_dynamic_coverage'})
                owners = (*owners, node.name)
            stack.extend((child, owners) for child in reversed(list(ast.iter_child_nodes(node))))
    return files, sorted(definitions, key=lambda x: (x['source'], x['line'], x['id']))


def build(plan_path):
    start = time.monotonic()
    plan_data = bounded_read(plan_path, MAX_PLAN_BYTES)
    plan = decode_json(plan_data, 'workload plan')
    require(type(plan.get('schema')) is int and plan['schema'] == 1, 'Unsupported workload plan schema')
    build_data = pinned(plan, 'trusted_build_record', MAX_REFERENCE_BYTES)
    record = decode_json(build_data, 'trusted build record')
    require(record.get('candidate_build_id') == BUILD_ID and record.get('pass') is True and
            record.get('all_pass') is True and record.get('actual_filesystem_matches_compiler_input') is True,
            'Build record is not the trusted admitted closed F6 graph')
    maps = {}
    source_bytes = {}
    for key, count in (('source_sha256', 61), ('dependency_source_sha256', 39), ('build_input_sha256', 4)):
        mapping = record.get(key)
        require(isinstance(mapping, dict) and len(mapping) == count, 'Trusted source count differs: ' + key)
        for name, expected in mapping.items():
            check_deadline(start)
            require(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected), 'Invalid source pin')
            data = bounded_read(repo_path(name), MAX_SOURCE_BYTES)
            require(digest(data) == expected, 'Current source differs from trusted build: ' + name)
            if key == 'source_sha256':
                source_bytes[name] = data
        maps[key] = mapping
    reference_data = pinned(plan, 'function_reference', MAX_REFERENCE_BYTES)
    reference = decode_json(reference_data, 'function reference')
    snapshot = reference.get('source_snapshot')
    require(isinstance(snapshot, dict), 'Missing function-reference source snapshot')
    require(all(snapshot.get(key) == value for key, value in maps.items()),
            'Function reference source graph differs from trusted build')
    require(snapshot.get('compiler_output_sha256') == record.get('compiler_output_sha256'),
            'Function reference compiler output differs')
    require(snapshot.get('size_evidence_sha256') == digest(build_data) and
            snapshot.get('compiler_settings') == record.get('settings'),
            'Function reference size/settings evidence differs')
    compressed = pinned(plan, 'compiler_output', MAX_COMPRESSED_BYTES)
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as handle:
            decoded = handle.read(MAX_COMPILER_BYTES + 1)
    except (OSError, EOFError) as exc:
        raise InventoryError('Malformed compressed compiler output') from exc
    require(len(decoded) <= MAX_COMPILER_BYTES, 'Decoded compiler output exceeds budget')
    require(plan['compiler_output'].get('decoded_sha256') == digest(decoded) == record.get('compiler_output_sha256'),
            'Decoded compiler output hash differs')
    compiler = decode_json(decoded, 'compiler output')
    require(isinstance(compiler.get('sources'), dict) and isinstance(compiler.get('contracts'), dict),
            'Compiler output has no sources/contracts')
    require(set(compiler['sources']) == set(maps['source_sha256']) | set(maps['dependency_source_sha256']),
            'Compiler output closed source domain differs')

    families = plan.get('families')
    require(isinstance(families, list) and families, 'Missing workload families')
    family_ids, contract_families, source_families = set(), {}, {}
    for family in families:
        require(isinstance(family, dict), 'Malformed workload family')
        identity = family.get('id')
        require(isinstance(identity, str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', identity)
                and identity not in family_ids, 'Missing or repeated workload-family ID')
        family_ids.add(identity)
        contracts, sources = family.get('contracts'), family.get('sources')
        require(isinstance(contracts, list) and isinstance(sources, list) and
                len(contracts) == len(set(contracts)) and len(sources) == len(set(sources)),
                'Repeated/malformed workload-family members')
        for name in contracts:
            require(isinstance(name, str) and name not in contract_families, 'Unreviewed duplicate contract family')
            contract_families[name] = identity
        for name in sources:
            require(name in maps['source_sha256'], 'Family names an unreviewed project source')
            source_families.setdefault(name, []).append(identity)
    require(set(source_families) == set(maps['source_sha256']), 'Project source missing a workload family')
    contracts = reference.get('contracts')
    require(isinstance(contracts, list) and len(contracts) == 40, 'Function-reference contract count differs')
    require(set(contract_families) == {x['name'] for x in contracts} and len(contract_families) == 40,
            'Missing or unknown callable contract in workload plan')
    require(isinstance(reference.get('gaps'), list) and not reference['gaps'] and
            all(reference.get('counts', {}).get(key) == 0 for key in
                ('explanation_gaps', 'unannotated_inputs', 'unannotated_outputs')),
            'Function-reference explanatory gaps remain')
    abi_rows = []
    for ci, contract in enumerate(contracts):
        name, source = contract['name'], contract['source']
        require(source in maps['source_sha256'] and contract_families[name] in source_families[source],
                'Callable contract source is not in its declared family')
        actual = compiler['contracts'].get(source, {}).get(name, {}).get('abi')
        require(isinstance(actual, list), 'Missing compiler ABI: ' + name)
        saved_abi = reference.get('abi_snapshot', {}).get(name, {}).get('abi')
        require(saved_abi == actual, 'Function-reference ABI differs from trusted compiler output: ' + name)
        actual_ids = [abi_identity(x) for x in actual if x.get('type') in ('function', 'constructor', 'receive', 'fallback')]
        require(len(actual_ids) == len(set(actual_ids)), 'Duplicate compiled callable identity')
        functions = contract.get('functions')
        require(isinstance(functions, list), 'Missing contract reference rows')
        reference_ids = [(f['kind'], f['signature']) for f in functions]
        require(len(reference_ids) == len(set(reference_ids)) and set(reference_ids) == set(actual_ids),
                'Reference callable identities differ: ' + name)
        for fi, function in enumerate(functions):
            row = {key: function.get(key) for key in ('kind', 'name', 'signature', 'state_mutability',
                                                     'purpose', 'access', 'inputs', 'outputs', 'native_value', 'notes')}
            row.update(id='abi:' + source + ':' + name + ':' + function['kind'] + ':' + function['signature'],
                       contract=name, family=contract_families[name], source=source,
                       source_sha256=maps['source_sha256'][source], contract_purpose=contract.get('purpose'),
                       reference_pointer='/contracts/' + str(ci) + '/functions/' + str(fi),
                       coverage_status='inventory_only_not_dynamic_coverage')
            abi_rows.append(row)
    kinds = {kind: sum(row['kind'] == kind for row in abi_rows) for kind in ('function', 'constructor', 'receive', 'fallback')}
    require(kinds == {'function': 968, 'constructor': 40, 'receive': 13, 'fallback': 0},
            'Trusted callable-row counts differ')
    excluded = reference.get('excluded_objects')
    require(isinstance(excluded, list) and len(excluded) == 8, 'Internal-only object count differs')
    internal_objects = []
    for item in excluded:
        require(item.get('source') in maps['source_sha256'], 'Unknown internal object source')
        require(item.get('contract') in compiler['contracts'].get(item['source'], {}),
                'Excluded internal object absent from compiler output')
        internal_objects.append({**item, 'families': sorted(source_families[item['source']]),
                                 'source_sha256': maps['source_sha256'][item['source']],
                                 'coverage_status': 'internal_code_still_requires_verification'})
    definitions, modifiers, bodyless = solidity_definitions(
        compiler, maps['source_sha256'], source_families, source_bytes, start)
    python_files, python_defs = python_inventory(plan, start)
    check_deadline(start)
    return {'schema': 1, 'kind': 'source_pinned_workload_inventory', 'trusted_build_id': BUILD_ID,
            'inventory_is_dynamic_coverage': False, 'production_approved': False,
            'scope': 'All callable rows and implemented project AST definitions, plus lexical production Python definitions. No tests or behavior executed.',
            'limitations': ['Presence, names and family assignment do not establish assertion strength or dynamic coverage.',
                            'Future builds/reference inputs require an explicitly reviewed allowlist update; a rewritten plan cannot admit them.',
                            'Python runtime dispatch, dynamically generated definitions and external services require separate review.',
                            'Bodyless interfaces are counted separately; dependency implementations are pinned but not inventoried as project code.',
                            'Internal-only objects and modifiers remain obligations; an empty callable ABI does not exclude their code.',
                            'Protected run-fork working-tree changes are not adopted; its unchanged published HEAD blob is inventoried.'],
            'inputs': {'plan': {'path': str(plan_path.relative_to(ROOT)), 'sha256': digest(plan_data)},
                       **{key: plan[key] for key in ('trusted_build_record', 'function_reference', 'compiler_output')}},
            'authenticated_source_maps': maps,
            'counts': {'callable_contracts': 40, 'abi_rows': len(abi_rows), 'abi_kinds': kinds,
                       'project_sources': 61, 'dependency_sources': 39, 'build_controls': 4,
                       'solidity_implemented_definitions': len(definitions), 'solidity_modifiers': len(modifiers),
                       'solidity_bodyless_declarations': bodyless, 'excluded_internal_objects': len(internal_objects),
                       'python_files': len(python_files), 'python_definitions': len(python_defs)},
            'families': [{'id': x['id'], 'contracts': x['contracts'], 'sources': x['sources']} for x in families],
            'abi_rows': abi_rows, 'solidity_implemented_definitions': definitions,
            'solidity_modifiers': modifiers, 'excluded_internal_objects': internal_objects,
            'python_sources': python_files, 'python_definitions': python_defs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', default='docs/WORKLOAD_PLAN.json')
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--output', type=Path, help='Exclusive new JSON output; parent directory must exist')
    target.add_argument('--check', type=Path, help='Verify an existing canonical inventory; write nothing')
    args = parser.parse_args()
    try:
        plan_path = repo_path(relative_path(args.plan))
        report = build(plan_path)
        encoded = canonical(report)
        require(len(encoded) <= MAX_OUTPUT_BYTES, 'Inventory output exceeds byte budget')
        if args.check:
            require(bounded_read(args.check, MAX_OUTPUT_BYTES) == encoded,
                    'Existing workload inventory differs from current pinned inputs')
            action = 'verified'
        else:
            require(args.output.parent.is_dir() and not os.path.lexists(args.output),
                    'Output parent must exist and output must be unoccupied')
            with args.output.open('xb') as handle:
                handle.write(encoded)
            action = 'created'
        print(json.dumps({'action': action, 'inventory_only': True, 'output_bytes': len(encoded),
                          'output_sha256': digest(encoded), 'counts': report['counts']}, sort_keys=True))
    except (InventoryError, OSError, KeyError, TypeError, ValueError, RecursionError) as exc:
        print('Workload inventory refused: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)


if __name__ == '__main__':
    main()
