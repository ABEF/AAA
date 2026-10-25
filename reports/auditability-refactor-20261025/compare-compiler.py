"""Compare saved compiler evidence; never compiles, tests, signs or contacts RPC.

Only identical ABI error duplicates and the deliberate converter struct-owner
provenance change are normalized. Constructor/parameter/tuple names remain exact.
Storage normalization removes compiler AST/type IDs, retaining recursive layout.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')


def read(path):
    raw = path.read_bytes()
    if len(raw) > 128 * 1024 * 1024:
        raise ValueError('Compiler evidence exceeds bounded input size')
    return json.loads(raw)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def provenance(value):
    return value.replace('ZZZRoyaltyConverter.', 'ZZZRewardConverter.')


def normalize_abi(abi):
    substitutions = []
    def walk(value, path):
        if isinstance(value, list):
            return [walk(item, path + [index]) for index, item in enumerate(value)]
        if not isinstance(value, dict):
            return value
        result = {}
        for key, item in value.items():
            if key == 'internalType' and isinstance(item, str) and item.startswith('struct ZZZRoyaltyConverter.'):
                replacement = provenance(item)
                substitutions.append({'path': path + [key], 'before': item, 'normalized': replacement})
                result[key] = replacement
            else:
                result[key] = walk(item, path + [key])
        return result
    normalized = walk(abi, [])
    # Other duplicate entry kinds remain significant and cannot be hidden.
    entries = []; seen_errors = set(); duplicates = []
    for entry in normalized:
        key = encoded(entry)
        if entry.get('type') == 'error':
            if key in seen_errors:
                duplicates.append(entry)
                continue
            seen_errors.add(key)
        entries.append(entry)
    return sorted(entries, key=encoded), substitutions, duplicates


def normalize_storage(layout):
    types = layout.get('types') or {}
    def resolve(identifier, parents=()):
        if len(parents) > 64:
            raise ValueError('Unexpected recursive storage depth')
        value = types[identifier]
        if identifier in parents:
            return {'recursive_type': provenance(value['label'])}
        result = {key: provenance(item) if key == 'label' else item
                  for key, item in value.items() if key not in ('key', 'value', 'base', 'members')}
        for key in ('key', 'value', 'base'):
            if key in value:
                result[key] = resolve(value[key], parents + (identifier,))
        if 'members' in value:
            result['members'] = [row(member, parents + (identifier,)) for member in value['members']]
        return result
    def row(item, parents=()):
        return {'label': item['label'], 'slot': item['slot'], 'offset': item['offset'],
                'type': resolve(item['type'], parents)}
    return [row(item) for item in layout.get('storage', [])]


def strip_metadata(value):
    if not value:
        return b'', 0
    if not re.fullmatch(r'(?:[0-9a-fA-F]{2})+', value):
        raise ValueError('Unlinked or malformed compiler bytecode')
    raw = bytes.fromhex(value)
    length = int.from_bytes(raw[-2:], 'big') if len(raw) >= 2 else 0
    if length and length + 2 <= len(raw):
        metadata = raw[-length - 2:-2]
        # Solidity metadata is a CBOR map containing its compiler identifier.
        if 0xa0 <= metadata[0] <= 0xbf and b'solc' in metadata:
            return raw[:-length - 2], length + 2
    return raw, 0


def flatten(output):
    return {(path, name): value for path, contracts in output['contracts'].items()
            if path.startswith('src/') for name, value in contracts.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir', type=Path, default=EXTERNAL / 'architecture-pruning-20261025/solidity')
    parser.add_argument('--candidate-dir', type=Path, default=EXTERNAL / 'auditability-refactor-20261025/solidity')
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output-name', default='compiler-comparison')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,80}', args.output_name):
        raise ValueError('Use a simple evidence filename stem')
    output_json = args.output_dir / (args.output_name + '.json')
    output_md = args.output_dir / (args.output_name + '.md')
    if output_json.exists() or output_md.exists():
        raise ValueError('Preserve earlier evidence; select a fresh output name')
    artifact_hashes = {}
    loaded = []
    for directory in (args.baseline_dir, args.candidate_dir):
        records = {}
        for name in ('source-build.json', 'source-build-input.json', 'source-size-gates.json'):
            path = directory / name
            artifact_hashes[str(path)] = digest(path.read_bytes())
            records[name] = read(path)
        loaded.append(records)
    before, after = loaded
    old = flatten(before['source-build.json']); new = flatten(after['source-build.json'])
    common = sorted(set(old) & set(new)); comparisons = []
    for key in common:
        a, b = old[key], new[key]
        old_abi, old_aliases, old_duplicates = normalize_abi(a['abi'])
        new_abi, new_aliases, new_duplicates = normalize_abi(b['abi'])
        storage_before = normalize_storage(a['storageLayout'])
        storage_after = normalize_storage(b['storageLayout'])
        result = {'path': key[0], 'contract': key[1],
            'raw_abi_equal': sorted(a['abi'], key=encoded) == sorted(b['abi'], key=encoded),
            'abi_equal_after_only_permitted_normalization': old_abi == new_abi,
            'baseline_struct_provenance_normalization': old_aliases,
            'candidate_struct_provenance_normalization': new_aliases,
            'baseline_identical_error_duplicates': old_duplicates,
            'candidate_identical_error_duplicates': new_duplicates,
            'normalized_recursive_storage_equal': storage_before == storage_after,
            'storage_sha256_before': digest(encoded(storage_before).encode()),
            'storage_sha256_after': digest(encoded(storage_after).encode())}
        if old_abi != new_abi:
            ca, cb = collections.Counter(map(encoded, old_abi)), collections.Counter(map(encoded, new_abi))
            result['unexpected_abi_removed'] = [json.loads(value) for value in (ca - cb).elements()]
            result['unexpected_abi_added'] = [json.loads(value) for value in (cb - ca).elements()]
        if storage_before != storage_after:
            result.update(storage_before=storage_before, storage_after=storage_after)
        comparisons.append(result)
    bytecode = []
    for name in ('ZZZVault', 'ZZZMigration', 'ZZZCanonicalHandoff'):
        key = ('src/' + name + '.sol', name)
        record = {'path': key[0], 'contract': name}
        for kind in ('bytecode', 'deployedBytecode'):
            a, stripped_a = strip_metadata(old[key]['evm'][kind]['object'])
            b, stripped_b = strip_metadata(new[key]['evm'][kind]['object'])
            record[kind] = {'executable_equal': a == b, 'executable_bytes_before': len(a),
                'executable_bytes_after': len(b), 'sha256_before': digest(a), 'sha256_after': digest(b),
                'metadata_trailer_bytes_before': stripped_a, 'metadata_trailer_bytes_after': stripped_b}
        bytecode.append(record)
    old_gates = {(r['path'], r['name']): r for r in before['source-size-gates.json']['gates']}
    sizes = []
    for saved in after['source-size-gates.json']['gates']:
        key = (saved['path'], saved['name']); abi = new[key]['abi']
        runtime = len(bytes.fromhex(new[key]['evm']['deployedBytecode']['object']))
        creation = len(bytes.fromhex(new[key]['evm']['bytecode']['object']))
        constructor = next((row.get('inputs', []) for row in abi if row['type'] == 'constructor'), [])
        dynamic = any(row['type'] in ('string', 'bytes', 'tuple') or '[' in row['type'] for row in constructor)
        static = None if dynamic else 32 * len(constructor)
        previous = old_gates.get(key)
        sizes.append({'path': key[0], 'contract': key[1], 'runtime_bytes': runtime,
            'runtime_margin': 24576 - runtime, 'creation_object_bytes': creation,
            'static_argument_bytes': static, 'creation_with_static_arguments': None if dynamic else creation + static,
            'initcode_argument_capacity': 49152 - creation,
            'exact_dynamic_constructor_arguments_still_required': dynamic,
            'runtime_delta': None if previous is None else runtime - previous['runtime'],
            'creation_delta': None if previous is None else creation - previous['creation'],
            'runtime_gate_pass': runtime <= 24576, 'creation_object_and_known_static_args_pass': creation + (static or 0) <= 49152,
            'saved_gate_bytes_match': runtime == saved['runtime'] and creation == saved['creation'] and static == saved['static_argument_bytes']})
    hashes = after['source-size-gates.json']['source_sha256']
    actual_paths = {p.relative_to(args.repo_root).as_posix() for p in (args.repo_root / 'src').rglob('*.sol')}
    mismatches = [path for path, value in hashes.items() if not (args.repo_root / path).is_file()
                  or digest((args.repo_root / path).read_bytes()) != value]
    source_match = not mismatches and actual_paths == set(hashes)
    baseline_input_match = all(digest(item['content'].encode()) == before['source-size-gates.json']['compiler_content_sha256'].get(path)
                               for path, item in before['source-build-input.json']['sources'].items())
    candidate_input_match = all(digest(item['content'].encode()) == after['source-size-gates.json']['compiler_content_sha256'].get(path)
                                for path, item in after['source-build-input.json']['sources'].items())
    abi_ok = all(r['abi_equal_after_only_permitted_normalization'] for r in comparisons)
    storage_ok = all(r['normalized_recursive_storage_equal'] for r in comparisons)
    size_ok = all(r['runtime_gate_pass'] and r['creation_object_and_known_static_args_pass'] and r['saved_gate_bytes_match'] for r in sizes)
    report = {'scope': 'Read-only comparison of two already-executed normal compiler campaigns. No compiler/test rerun, deployment, chain, RPC or service action.',
        'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'baseline_directory': str(args.baseline_dir), 'candidate_directory': str(args.candidate_dir),
        'artifact_sha256': artifact_hashes, 'comparison_script_sha256': digest(Path(__file__).read_bytes()),
        'compiler_settings_equal': before['source-build-input.json']['settings'] == after['source-build-input.json']['settings'],
        'compiler_input_content_hashes_match': {'baseline': baseline_input_match, 'candidate': candidate_input_match},
        'candidate_current_source_hashes_match': source_match, 'current_source_mismatches': mismatches,
        'current_source_path_set_difference': sorted(actual_paths ^ set(hashes)),
        'common_project_objects': len(common), 'all_common_wire_abis_equal_with_explicit_exceptions': abi_ok,
        'all_common_recursive_storage_layouts_equal': storage_ok, 'object_comparisons': comparisons,
        'objects_removed': [{'path': p, 'contract': n, 'has_creation_code': bool(old[p, n]['evm']['bytecode']['object'])} for p, n in sorted(set(old) - set(new))],
        'objects_added': [{'path': p, 'contract': n, 'has_creation_code': bool(new[p, n]['evm']['bytecode']['object'])} for p, n in sorted(set(new) - set(old))],
        'metadata_stripped_bytecode': bytecode, 'candidate_normal_object_gate_count': len(sizes),
        'all_recomputed_normal_object_gates_pass': size_ok, 'sizes': sizes,
        'normalization_limits': ['Only struct internalType/type-label owner ZZZRoyaltyConverter→ZZZRewardConverter and byte-identical duplicate ABI errors are normalized.',
            'Constructor/input/output/tuple names and order, external wire types, mutability, error/event signatures and indexing are retained exactly.',
            'Storage compiler AST/type IDs and declaration provenance are not physical layout; recursive member names/types/slots/offsets are compared.',
            'Solidity CBOR metadata trailers alone are removed from executable comparisons. Unequal remaining bytes are reported, never treated as equivalent.',
            'NFT dynamic constructor arguments remain a release-specific qualification; object/static gates alone do not qualify its actual chosen URI.',
            'This is not deployment/upgrade approval, a fresh execution regression, a gas proof, real-service qualification or independent audit.']}
    report['comparison_checks_pass'] = (source_match and baseline_input_match and candidate_input_match and
        report['compiler_settings_equal'] and abi_ok and storage_ok and size_ok)
    lines = ['# Saved compiler comparison', '',
        'This compares saved normal compiler outputs; no compiler or tests were rerun.', '',
        f'- Common project objects: **{len(common)}**. Wire ABI checks pass: **{abi_ok}**; recursive storage checks pass: **{storage_ok}**.',
        f'- Current source hashes match the candidate compilation: **{source_match}**.',
        f'- All **{len(sizes)}** recomputed normal runtime/initcode object gates pass: **{size_ok}**.', '',
        'Only converter struct-owner metadata and identical duplicate ABI error entries are normalized. Names, tuple members, events, indexing, errors and mutability otherwise remain exact.', '',
        '## Explicit ABI metadata exceptions', '']
    for r in comparisons:
        if not r['raw_abi_equal']:
            lines.append(f"- `{r['contract']}`: baseline struct-owner paths={len(r['baseline_struct_provenance_normalization'])}; candidate identical error duplicates={len(r['candidate_identical_error_duplicates'])}. Normalized ABI equal: {r['abi_equal_after_only_permitted_normalization']}.")
    lines += ['', '## Size changes', '', '| Object | Runtime delta | Creation delta | Current runtime / margin |', '| --- | ---: | ---: | ---: |']
    for r in sizes:
        if r['runtime_delta'] != 0 or r['creation_delta'] != 0:
            lines.append(f"| {r['contract']} | {'new' if r['runtime_delta'] is None else format(r['runtime_delta'],'+d')} | {'new' if r['creation_delta'] is None else format(r['creation_delta'],'+d')} | {r['runtime_bytes']} / {r['runtime_margin']} |")
    lines += ['', '## Executable comparison', '']
    for r in bytecode:
        lines.append(f"- `{r['contract']}` metadata-stripped creation/runtime equal: **{r['bytecode']['executable_equal']} / {r['deployedBytecode']['executable_equal']}**.")
    lines += ['', 'Vault and Migration naming changes are distinguished from Handoff named-constant code generation. Any unequal executable output is reported honestly; ABI/storage equality is not a formal behavioral-equivalence proof.', '',
        'NFT creation has dynamic URI arguments; exact final ABI-encoded arguments still need qualification. The internal v3 library adds one compiler object, not a new externally linked execution dependency or a production deployment.', '',
        'See `compiler-comparison.json` for every object, normalization exception, hash and gate. Actual execution tests and their source scope are recorded separately. Production remains NOT APPROVED.', '']
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    output_md.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('common_project_objects', 'all_common_wire_abis_equal_with_explicit_exceptions',
        'all_common_recursive_storage_layouts_equal', 'candidate_current_source_hashes_match', 'candidate_normal_object_gate_count',
        'all_recomputed_normal_object_gates_pass', 'comparison_checks_pass')}, indent=2))
    return 0 if report['comparison_checks_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
