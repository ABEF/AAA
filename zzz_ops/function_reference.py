"""Source-bound ABI documentation; never compiles, signs, or sends transactions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any

MAX_JSON_BYTES = 64 * 1024 * 1024
CALLABLE_KINDS = frozenset(('function', 'constructor', 'receive', 'fallback'))
SNAPSHOT_SCHEMA = 2
BUILD_INPUTS = frozenset(('foundry.toml','package.json','package-lock.json','scripts/install-deps.sh'))


class ReferenceError(ValueError):
    pass


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ReferenceError('Duplicate JSON key')
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ReferenceError('Reference input exceeds size limit')
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ReferenceError('Nonfinite JSON value')))


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_type(item: dict) -> str:
    if not isinstance(item, dict) or not isinstance(item.get('type'), str):
        raise ReferenceError('Invalid ABI parameter')
    typ = item['type']
    if typ.startswith('tuple'):
        suffix = typ[5:]
        if not re.fullmatch(r'(?:\[(?:[1-9][0-9]*)?\])*', suffix) or not isinstance(item.get('components'), list):
            raise ReferenceError('Invalid tuple ABI')
        return '(' + ','.join(canonical_type(x) for x in item['components']) + ')' + suffix
    match = re.fullmatch(r'([A-Za-z][A-Za-z0-9]*)(\[.*\])?', typ)
    if not match or 'components' in item:
        raise ReferenceError('Invalid scalar ABI')
    base, suffix = match[1], match[2] or ''
    if not re.fullmatch(r'(?:\[(?:[1-9][0-9]*)?\])*', suffix):
        raise ReferenceError('Invalid ABI array')
    base = {'uint': 'uint256', 'int': 'int256', 'fixed': 'fixed128x18', 'ufixed': 'ufixed128x18'}.get(base, base)
    if base not in ('address', 'bool', 'bytes', 'string', 'function') and not re.fullmatch(
            r'(?:u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)|bytes(?:[1-9]|[12][0-9]|3[0-2])|u?fixed[0-9]+x[0-9]+)', base):
        raise ReferenceError('Unsupported ABI type')
    return base + suffix


def signature(entry: dict) -> str:
    kind = entry.get('type')
    if kind not in CALLABLE_KINDS:
        raise ReferenceError('Not a callable ABI entry')
    name = entry.get('name') if kind == 'function' else kind
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
        raise ReferenceError('Invalid callable name')
    inputs = entry.get('inputs', [])
    if not isinstance(inputs, list):
        raise ReferenceError('Invalid callable inputs')
    return name + '(' + ','.join(canonical_type(x) for x in inputs) + ')'


def _hex_object(value):
    if not isinstance(value, str):
        raise ReferenceError('Missing compiler bytecode')
    value = value.removeprefix('0x')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{2})*', value):
        raise ReferenceError('Unlinked or malformed compiler bytecode')
    return value.lower()


def _source(root: Path, name: str) -> Path:
    if (not isinstance(name,str) or '\\' in name or not name.startswith('src/') or
            any(part in ('','.','..') for part in name.split('/'))):
        raise ReferenceError('Invalid project source path')
    directory=(root/'src').resolve()
    path = (root / name).resolve()
    if (not directory.is_relative_to(root.resolve()) or not path.is_relative_to(directory) or
            path.suffix != '.sol' or not path.is_file()):
        raise ReferenceError('Source path escaped the project or is missing')
    return path


def _dependency_source(root: Path, name: str) -> Path:
    if (not isinstance(name,str) or '\\' in name or
            not name.startswith(('node_modules/','lib/')) or
            any(part in ('','.','..') for part in name.split('/'))):
        raise ReferenceError('Invalid dependency source path')
    directory = root / name.split('/',1)[0]
    path = (root/name).resolve()
    if (not directory.resolve().is_relative_to(root.resolve()) or
            not path.is_relative_to(directory.resolve()) or path.suffix != '.sol' or not path.is_file()):
        raise ReferenceError('Dependency source escaped its directory or is missing')
    return path


def _check_sources(root, snapshot):
    if type(snapshot.get('snapshot_schema')) is not int or snapshot['snapshot_schema'] != SNAPSHOT_SCHEMA:
        raise ReferenceError('Regenerate the reference with explicit dependency/build bindings')
    for field in ('compiler_input_sha256','compiler_output_sha256','size_evidence_sha256'):
        if not isinstance(snapshot.get(field),str) or not re.fullmatch(r'[0-9a-f]{64}',snapshot[field]):
            raise ReferenceError('Invalid compiler artifact binding')
    expected = snapshot.get('source_sha256')
    if not isinstance(expected, dict) or not expected:
        raise ReferenceError('Missing source bindings')
    actual_names = {x.relative_to(root).as_posix() for x in (root / 'src').rglob('*.sol')}
    if set(expected) != actual_names:
        raise ReferenceError('Production source inventory changed')
    for name, digest in expected.items():
        if not re.fullmatch(r'[0-9a-f]{64}', str(digest)) or sha(_source(root, name).read_bytes()) != digest:
            raise ReferenceError('Production source changed: ' + name)
    dependencies = snapshot.get('dependency_source_sha256')
    build_inputs = snapshot.get('build_input_sha256')
    if not isinstance(dependencies,dict) or not isinstance(build_inputs,dict) or not set(build_inputs) <= BUILD_INPUTS:
        raise ReferenceError('Missing or invalid dependency/build bindings')
    if set(build_inputs) != {name for name in BUILD_INPUTS if (root/name).is_file()}:
        raise ReferenceError('Build input inventory changed')
    for name,digest in dependencies.items():
        if not re.fullmatch(r'[0-9a-f]{64}',str(digest)) or sha(_dependency_source(root,name).read_bytes()) != digest:
            raise ReferenceError('Dependency source changed: '+name)
    for name,digest in build_inputs.items():
        path=root/name
        if (not re.fullmatch(r'[0-9a-f]{64}',str(digest)) or
                not path.resolve().is_relative_to(root.resolve()) or not path.is_file() or sha(path.read_bytes()) != digest):
            raise ReferenceError('Build input changed: '+name)


def import_compiler(root: Path, compiler_input: Path, compiler_output: Path, size_report: Path) -> dict:
    root = root.resolve()
    supplied = load_json(compiler_input)
    output = load_json(compiler_output)
    sizes = load_json(size_report)
    if not all(isinstance(x, dict) for x in (supplied, output, sizes)):
        raise ReferenceError('Compiler inputs must be JSON objects')
    if supplied.get('language') != 'Solidity' or any(x.get('severity') == 'error' for x in output.get('errors', [])):
        raise ReferenceError('Compiler input/output is not a successful Solidity result')
    settings = supplied.get('settings')
    if settings != sizes.get('settings') or sizes.get('all_pass') is not True or sizes.get('errors') != []:
        raise ReferenceError('Compiler settings or normal size evidence differs')
    sources = supplied.get('sources')
    hashes = sizes.get('source_sha256')
    dependencies = sizes.get('dependency_source_sha256')
    compiled_sources = output.get('sources')
    contents = sizes.get('compiler_content_sha256')
    if (not isinstance(sources,dict) or not isinstance(hashes,dict) or not isinstance(dependencies,dict) or
            not isinstance(compiled_sources,dict) or not isinstance(contents,dict) or set(contents) != set(sources) or
            set(hashes)&set(dependencies) or
            set(sources) != set(hashes)|set(dependencies) or set(compiled_sources) != set(sources)):
        raise ReferenceError('Compiler source inventory differs from size evidence')
    for name, value in sources.items():
        source = _source(root,name) if name in hashes else _dependency_source(root,name)
        text = source.read_bytes().decode('utf-8-sig')
        if value != {'content': text} or sha(text.encode()) != sizes.get('compiler_content_sha256', {}).get(name):
            raise ReferenceError('Compiler source content differs: ' + name)
    snapshot = {'snapshot_schema':SNAPSHOT_SCHEMA,'source_sha256':hashes,
        'dependency_source_sha256':dependencies,'build_input_sha256':sizes.get('build_input_sha256'),
        'compiler_settings': settings,
        'compiler_input_sha256': sha(compiler_input.read_bytes()), 'compiler_output_sha256': sha(compiler_output.read_bytes()),
        'size_evidence_sha256': sha(size_report.read_bytes())}
    _check_sources(root, snapshot)
    gate_rows = sizes.get('gates')
    if not isinstance(gate_rows, list) or any(not isinstance(x, dict) for x in gate_rows):
        raise ReferenceError('Missing normal object gates')
    gates = {(x['path'], x['name']): x for x in gate_rows}
    if len(gates) != len(gate_rows) or not isinstance(output.get('contracts'), dict):
        raise ReferenceError('Duplicate object gate or missing compiled contracts')
    objects, excluded = {}, []
    for source, contracts in output.get('contracts', {}).items():
        if not source.startswith('src/'):
            continue
        if source not in sources:
            raise ReferenceError('Unexpected compiled project source')
        for name, obj in contracts.items():
            creation = _hex_object(obj.get('evm', {}).get('bytecode', {}).get('object', ''))
            if not creation:
                continue
            runtime = _hex_object(obj.get('evm', {}).get('deployedBytecode', {}).get('object', ''))
            gate = gates.get((source, name))
            if (not gate or type(gate.get('creation')) is not int or type(gate.get('runtime')) is not int or
                    len(creation)//2 != gate['creation'] or len(runtime)//2 != gate['runtime'] or
                    gate.get('creation_ok') is not True or gate.get('runtime_ok') is not True):
                raise ReferenceError('Compiler object differs from normal size evidence')
            abi = obj.get('abi')
            if not isinstance(abi, list):
                raise ReferenceError('Missing compiler ABI')
            if source.startswith('src/libraries/'):
                if any(x.get('type') in CALLABLE_KINDS for x in abi):
                    raise ReferenceError('A callable project library needs explicit documentation policy')
                excluded.append({'contract': name, 'source': source, 'reason': 'Internal-only library; no callable ABI.'})
                continue
            if name in objects:
                raise ReferenceError('Duplicate concrete contract name')
            objects[name] = {'source': source, 'abi': abi, 'abi_sha256': sha(canonical_json(abi).encode())}
    if len(objects) + len(excluded) != len(gates):
        raise ReferenceError('Incomplete concrete object inventory')
    return {'schema': 1, 'source_snapshot': snapshot, 'abi_snapshot': objects,
            'excluded_objects': sorted(excluded, key=lambda x: x['contract'])}


def merge_notes(files: list[Path]) -> dict:
    result = {'schema': 1, 'contracts': {}}
    for path in files:
        obj = load_json(path)
        if not isinstance(obj, dict) or obj.get('schema') != 1 or not isinstance(obj.get('contracts'), dict):
            raise ReferenceError('Notes require schema1 and contracts')
        for name, notes in obj['contracts'].items():
            if name in result['contracts']:
                raise ReferenceError('Contract notes overlap: ' + name)
            result['contracts'][name] = notes
    return result


def _explanation(value, label):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ReferenceError('Invalid explanation for ' + label)
    return value.strip()


def _parameters(items, side, notes):
    if not isinstance(items, list) or not isinstance(notes, dict):
        raise ReferenceError('Invalid parameters or parameter notes')
    result, accepted = [], set()
    for index, item in enumerate(items):
        name = item.get('name', '')
        if not isinstance(name, str):
            raise ReferenceError('Invalid ABI parameter name')
        positional = side[:-1] + str(index)
        candidates = [str(index), positional, name] if name else [str(index), positional]
        values = [notes[key] for key in candidates if key in notes]
        if len(values) > 1:
            raise ReferenceError('Ambiguous parameter explanation')
        accepted.update(key for key in candidates if key in notes)
        parameter = {'position': index, 'name': name, 'label': name or positional,
            'type': item['type'], 'canonical_type': canonical_type(item), 'internal_type': item.get('internalType', item['type']),
            'explanation': _explanation(values[0], positional) if values else None}
        if item['type'].startswith('tuple'):
            parameter['components'] = _parameters(item['components'], 'fields', {})
        result.append(parameter)
    if set(notes) != accepted:
        raise ReferenceError('Unknown parameter explanation: ' + ', '.join(sorted(set(notes) - accepted)))
    return result


def build_reference(root: Path, base: dict, notes: dict) -> dict:
    root = root.resolve()
    if base.get('schema') != 1 or not isinstance(base.get('abi_snapshot'), dict):
        raise ReferenceError('Invalid ABI snapshot')
    _check_sources(root, base['source_snapshot'])
    contract_notes = notes.get('contracts')
    if notes.get('schema') != 1 or not isinstance(contract_notes, dict):
        raise ReferenceError('Invalid notes')
    if set(contract_notes) - set(base['abi_snapshot']):
        raise ReferenceError('Notes name an unknown contract')
    result = {key: base[key] for key in ('schema', 'source_snapshot', 'abi_snapshot', 'excluded_objects')}
    result['notes_sha256'] = sha(canonical_json(notes).encode())
    contracts, gaps = [], []
    for name, info in sorted(base['abi_snapshot'].items()):
        if sha(canonical_json(info['abi']).encode()) != info['abi_sha256']:
            raise ReferenceError('Stored ABI snapshot changed: ' + name)
        _source(root, info['source'])
        cn = contract_notes.get(name, {})
        if not isinstance(cn, dict) or set(cn) - {'purpose', 'functions', 'constructor', 'receive', 'fallback', 'category'}:
            raise ReferenceError('Unknown contract note fields: ' + name)
        purpose = _explanation(cn.get('purpose'), name) or 'Not yet explained.'
        if purpose == 'Not yet explained.':
            gaps.append({'contract': name, 'field': 'purpose'})
        fn = cn.get('functions', {})
        if not isinstance(fn, dict):
            raise ReferenceError('Invalid function notes')
        entries, known = [], set()
        for abi in info['abi']:
            if abi.get('type') not in CALLABLE_KINDS:
                continue
            sig = signature(abi)
            if sig in known:
                raise ReferenceError('Duplicate callable ABI: ' + name + '.' + sig)
            known.add(sig)
            kind = abi['type']
            note = fn.get(sig, {}) if kind == 'function' else cn.get(kind, {})
            if not isinstance(note, dict) or set(note) - {'purpose', 'access', 'inputs', 'outputs', 'status', 'value', 'notes'}:
                raise ReferenceError('Unknown callable note fields: ' + name + '.' + sig)
            item = {'signature': sig, 'kind': kind, 'name': abi.get('name', kind),
                'state_mutability': abi.get('stateMutability'), 'purpose': _explanation(note.get('purpose'), sig) or 'Not yet explained.',
                'access': _explanation(note.get('access'), sig) or 'Not yet explained.',
                'status': note.get('status', 'documented' if note.get('purpose') and note.get('access') else 'incomplete'),
                'inputs': _parameters(abi.get('inputs', []), 'inputs', note.get('inputs', {})),
                'outputs': _parameters(abi.get('outputs', []), 'outputs', note.get('outputs', {})),
                'native_value': _explanation(note.get('value'), sig), 'notes': _explanation(note.get('notes'), sig)}
            if item['state_mutability'] not in ('view', 'pure', 'nonpayable', 'payable'):
                raise ReferenceError('Invalid callable mutability')
            if item['status'] not in ('documented', 'incomplete', 'retired', 'unavailable', 'internal'):
                raise ReferenceError('Invalid callable status')
            for field in ('purpose', 'access'):
                if item[field] == 'Not yet explained.':
                    gaps.append({'contract': name, 'signature': sig, 'field': field})
            if item['state_mutability'] == 'payable' and item['native_value'] is None:
                gaps.append({'contract': name, 'signature': sig, 'field': 'native_value'})
            entries.append(item)
        expected_functions = {x['signature'] for x in entries if x['kind'] == 'function'}
        if set(fn) - expected_functions:
            raise ReferenceError('Notes name an unknown function: ' + name + '.' + ', '.join(sorted(set(fn) - expected_functions)))
        for kind in ('constructor', 'receive', 'fallback'):
            if kind in cn and not any(x['kind'] == kind for x in entries):
                raise ReferenceError('Notes name a missing special entry: ' + name + '.' + kind)
        contracts.append({'name': name, 'source': info['source'], 'purpose': purpose, 'category': cn.get('category', 'Project contract'),
                          'functions': sorted(entries, key=lambda x: (x['kind'], x['signature']))})
    result['contracts'] = contracts
    result['gaps'] = gaps
    result['counts'] = {'contracts': len(contracts), 'functions': sum(x['kind'] == 'function' for c in contracts for x in c['functions']),
        'constructors': sum(x['kind'] == 'constructor' for c in contracts for x in c['functions']),
        'receive_hooks': sum(x['kind'] == 'receive' for c in contracts for x in c['functions']),
        'fallback_hooks': sum(x['kind'] == 'fallback' for c in contracts for x in c['functions']), 'explanation_gaps': len(gaps),
        'unannotated_inputs': sum(p['explanation'] is None for c in contracts for x in c['functions'] for p in x['inputs']),
        'unannotated_outputs': sum(p['explanation'] is None for c in contracts for x in c['functions'] for p in x['outputs'])}
    return result


def _text(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')


def _params(items):
    lines = []
    def visit(item, prefix=''):
        label = prefix + item['label']
        typ = item['canonical_type']
        line = '`' + _text(label) + ': ' + _text(typ) + '`'
        if item['internal_type'] != item['type']:
            line += ' (' + _text(item['internal_type']) + ')'
        if item['explanation']:
            line += ' — ' + _text(item['explanation'])
        elif not item['name']:
            line += ' — unnamed ABI position ' + str(item['position']) + '; see purpose.'
        lines.append(line)
        for child in item.get('components', []):
            visit(child, label + item['type'][5:] + '.')
    for item in items:
        visit(item)
    return '<br>'.join(lines) if lines else 'None in ABI.'


def render_markdown(reference):
    counts = reference['counts']
    lines = ['# Contract function reference', '',
        'Generated from the source-bound Solidity ABI and reviewed explanations. Update the notes and regenerate; do not edit this file by hand.', '',
        f"Covers **{counts['contracts']} concrete project contracts, {counts['functions']} functions, {counts['constructors']} constructors and {counts['receive_hooks']} receive hooks**. Inherited ERC-721 and governance functions are included. Internal-only libraries, abstract bases and external dependency interfaces are not separate operator targets.", '',
        '**Reads** use `view`/`pure`; on-chain calls still consume gas and can revert. **Writes** require a transaction and the stated permissions. A returned value from a write is available to simulation or another contract; a wallet receipt does not automatically contain that return value. Functions with no ABI outputs change state and/or emit events; no artificial return is invented.', '',
        '`msg.sender`, payable `msg.value`, network/contract identity and operating-state guards are not ABI arguments. Payable does not mean arbitrary ETH is accepted. Unnamed parameters retain explicit zero-based positions. Tuple fields are expanded in ABI order; integer units and zero-address meaning depend on the reviewed operation, not the Solidity type alone.', '',
        'The reference documents an undeployed candidate. It is not permission to broadcast, select providers or approve production. **Production NOT APPROVED.**', '',
        f"Missing function-purpose, caller or payable-value explanations: **{counts['explanation_gaps']}**. Top-level input positions without a dedicated explanation: **{counts['unannotated_inputs']}**. Output positions without a dedicated explanation: **{counts['unannotated_outputs']}**; their result meaning may instead be explained by the function purpose. These counts do not claim that every nested tuple field has a separate prose annotation. Missing semantics are not guessed from a Solidity type or vague name.", '',
        '## Contracts', '', '| Contract | Responsibility | Functions |', '| --- | --- | ---: |']
    for contract in reference['contracts']:
        anchor = contract['name'].lower()
        count = sum(x['kind'] == 'function' for x in contract['functions'])
        lines.append(f"| [{contract['name']}](#{anchor}) | {_text(contract['purpose'])} | {count} |")
    for contract in reference['contracts']:
        lines += ['', '## ' + contract['name'], '', contract['purpose'], '',
                  '[Source](../' + contract['source'] + '). Category: ' + _text(contract['category']) + '.']
        groups = [('Deployment', lambda x: x['kind'] == 'constructor'),
                  ('Read functions', lambda x: x['kind'] == 'function' and x['state_mutability'] in ('view', 'pure')),
                  ('Write functions', lambda x: x['kind'] == 'function' and x['state_mutability'] not in ('view', 'pure')),
                  ('Native ETH and fallback hooks', lambda x: x['kind'] in ('receive', 'fallback'))]
        for heading, predicate in groups:
            rows = [x for x in contract['functions'] if predicate(x)]
            if not rows:
                continue
            lines += ['', '### ' + heading, '', '| Function / mutability | Purpose | Who / conditions | Inputs | Outputs |', '| --- | --- | --- | --- | --- |']
            for item in rows:
                purpose = _text(item['purpose'])
                if item['status'] in ('retired', 'unavailable', 'internal'):
                    purpose = '**' + item['status'].upper() + '.** ' + purpose
                if item['native_value']:
                    purpose += '<br>**Native value:** ' + _text(item['native_value'])
                if item['notes']:
                    purpose += '<br>' + _text(item['notes'])
                lines.append('| `' + _text(item['signature']) + '`<br>' + item['state_mutability'] + ' | ' + purpose + ' | ' +
                    _text(item['access']) + ' | ' + _params(item['inputs']) + ' | ' + _params(item['outputs']) + ' |')
    lines += ['', '<a id="maintenance"></a>', '', '## Coverage and maintenance', '',
        'The machine-readable [reference snapshot](function-reference.json) retains full ABI, canonical signatures, source hashes, reviewed explanations and uncovered explanations. [Explanation inputs](function-reference-notes.json) are the editable source. `python scripts/generate-function-reference.py --check` checks current source bindings and deterministic generated content without compiling or rerunning contract tests.', '',
        'After a contract change, first obtain source-matching compiler input/output and normal size evidence, update the explanations, then regenerate. Unchanged source needs only the documentation check. A stale ABI, unknown note, duplicate signature, unexpected contract or altered generated file fails that check.', '',
        'From the repository root, edit `docs/function-reference-notes.json`, then replace these example artifact paths with the reviewed matching files. Use `python3` if that is the Python command in your environment. This command imports existing compiler evidence; it does not compile or rerun contract tests.', '',
        '```text',
        'python scripts/generate-function-reference.py --compiler-input reviewed/compiler-input.json --compiler-output reviewed/compiler-output.json --size-report reviewed/size-gates.json',
        'python scripts/generate-function-reference.py --check',
        '```', '',
        str(len(reference['excluded_objects'])) + ' current internal-only libraries have no callable ABI and are excluded: ' + ', '.join('`' + x['contract'] + '`' for x in reference['excluded_objects']) + '.', '']
    return '\n'.join(lines)


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, mode='w', encoding='utf-8', newline='\n', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def generate(root: Path, notes_file: Path, output_json: Path, output_md: Path, *, base=None, check=False):
    notes = load_json(notes_file)
    stored = load_json(output_json) if check or base is None else None
    if base is None:
        base = stored
    reference = build_reference(root.resolve(), base, notes)
    markdown = render_markdown(reference)
    if check:
        if reference['counts']['explanation_gaps'] or reference['counts']['unannotated_inputs']:
            raise ReferenceError('Function reference is incomplete: ' + str(reference['counts']['explanation_gaps']) +
                ' missing function/caller/payable explanations and ' + str(reference['counts']['unannotated_inputs']) +
                ' missing top-level input explanations')
        if stored != reference or output_md.read_text(encoding='utf-8-sig') != markdown:
            raise ReferenceError('Generated function reference differs; update notes and regenerate')
    else:
        # Validate and render completely before replacing either destination.
        write_atomic(output_json, json.dumps(reference, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        write_atomic(output_md, markdown)
    return reference['counts']
