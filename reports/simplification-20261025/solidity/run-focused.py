"""Run exact AST-selected test methods in an isolated normal-profile workspace.

Unselected project test* FunctionDefinitions are replaced only with whitespace.
Selected functions, constructors, modifiers and all other helpers stay byte-exact.
This limits code generation; it does not claim full regression or equivalence of
unexecuted tests. No public RPC, signer, service or existing Anvil state is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import tomllib

ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
SELECTION = {
    'ContributionSourcePolicyTest': '*',
    'NativeFeeRewardsTest': '*',
    'NativeCustodyTest': '*',
    'NativeCanonicalFundingTest': '*',
    'CustodyHandoffTest': '*',
    'GlobalMembershipDustTest': '*',
    'LPOnlyEntryBoundaryTest': '*',
    'EntryReviewPolicyTest': '*',
    'AccessControllerTest': {
        'testCanonicalZZZIdentityMustBeBoundBeforeSeal',
        'testMissingOrMismatchedExitZZZCannotPermanentlySeal',
        'testSealErasesBootstrap',
        'testRetiredBridgeModulesCannotBeBoundEvenBeforeSeal',
    },
    'CanonicalHandoffTest': {
        'testCompleteHandoffPreservesOwnersSharesTraitsAndBothRewardLedgers',
        'testAbortAfterFundingRequiresExactReturnedBacking',
        'testFullThousandNFTInventoryImportsExactlyOnceWithCompleteDenominators',
        'testMaximumLocalAssetAndBucketDomainsPreserveEveryImportedLedger',
        'testDormantImportedNFTCanActivateIntoExistingSharedBucket',
    },
}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def load(path):
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('Input exceeds bounded AST size')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def span(node, source_id, raw):
    start, length, identity = map(int, node['src'].split(':'))
    if identity != source_id or start < 0 or length < 0 or start + length > len(raw):
        raise ValueError('AST byte span does not match its source')
    return start, length


def visit(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from visit(value)
    elif isinstance(node, list):
        for value in node:
            yield from visit(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--external', type=Path, default=EXTERNAL)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--compiler-input', type=Path)
    parser.add_argument('--compiler-output', type=Path)
    parser.add_argument('--size-evidence', type=Path)
    parser.add_argument('--timeout', type=int, default=1200)
    args = parser.parse_args()
    root = args.root.resolve()
    external = args.external.resolve()
    evidence = args.evidence or external / 'simplification-audit-20261025/solidity'
    evidence.mkdir(parents=True, exist_ok=True)
    input_path = args.compiler_input or evidence / 'all-source-typecheck-input-7.json'
    output_path = args.compiler_output or evidence / 'all-source-typecheck-7.json'
    size_path = args.size_evidence or evidence / 'source-size-gates.json'
    supplied, compiled, sizes = load(input_path), load(output_path), load(size_path)
    if supplied.get('language') != 'Solidity' or any(x.get('severity') == 'error' for x in compiled.get('errors', [])):
        raise ValueError('AST must come from successful Solidity typechecking')
    profile_keys = ('evmVersion', 'viaIR', 'optimizer')
    settings = supplied['settings']
    if settings.get('evmVersion') != 'cancun' or settings.get('viaIR') is not True or settings.get('optimizer') != {
        'enabled': True, 'runs': 1, 'details': {'yul': False}
    }:
        raise ValueError('Normal compiler profile differs')
    if not sizes.get('all_pass') or any(settings.get(k) != sizes['settings'].get(k) for k in profile_keys):
        raise ValueError('Normal size evidence/profile does not match')
    normal = tomllib.loads((root / 'foundry.toml').read_text(encoding='utf-8-sig'))['profile']['default']
    ast_remaps = dict(x.split('=', 1) for x in settings['remappings'])
    normal_remaps = dict(x.split('=', 1) for x in normal['remappings'])
    production_remaps = dict(x.split('=', 1) for x in sizes['settings']['remappings'])
    # The source-only production compiler does not need every test-dependency
    # alias. Common aliases must agree, and the full AST set must match the
    # repository's unchanged normal Foundry profile exactly.
    if ast_remaps != normal_remaps or any(ast_remaps.get(key) != value for key, value in production_remaps.items()):
        raise ValueError('Normal dependency remappings differ')
    provided = supplied['sources']
    production_names = {p.relative_to(root).as_posix() for p in (root / 'src').rglob('*.sol')}
    if production_names != set(sizes['source_sha256']):
        raise ValueError('Production source inventory changed')
    original = {}
    for name, item in provided.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or set(item) != {'content'}:
            raise ValueError('Unexpected compiler input source')
        raw = path.read_bytes()
        if raw.decode('utf-8-sig') != item['content']:
            raise ValueError('Source changed since final AST: ' + name)
        original[name] = item['content'].encode('utf-8')
    for name in production_names:
        if name not in original or digest((root / name).read_bytes()) != sizes['source_sha256'][name]:
            raise ValueError('Production source drift: ' + name)

    # Resolve imports through compiler AST rather than lexical import discovery.
    contracts = {}
    for name, source in compiled['sources'].items():
        if name not in provided or not name.startswith('test/'):
            continue
        for node in source['ast'].get('nodes', []):
            if node.get('nodeType') == 'ContractDefinition':
                if node['name'] in contracts:
                    raise ValueError('Ambiguous project test contract')
                contracts[node['name']] = (name, node)
    selected = {}
    selected_ids = set()
    for name, policy in SELECTION.items():
        source, contract = contracts[name]
        methods = {f['name']: f for f in contract.get('nodes', []) if f.get('nodeType') == 'FunctionDefinition'
                   and f.get('name', '').startswith('test')}
        chosen = set(methods) if policy == '*' else set(policy)
        if not chosen or not chosen <= set(methods):
            raise ValueError('Missing or empty selected test set: ' + name)
        selected[name] = {'source': source, 'methods': sorted(chosen)}
        selected_ids.update(methods[x]['id'] for x in chosen)

    closure = set()
    def add(name):
        if name in closure:
            return
        if name not in provided:
            raise ValueError('Project import missing from reviewed compiler input: ' + name)
        closure.add(name)
        for node in compiled['sources'][name]['ast'].get('nodes', []):
            if node.get('nodeType') == 'ImportDirective':
                child = node['absolutePath']
                if child.startswith(('src/', 'test/')):
                    add(child)
    for info in selected.values():
        add(info['source'])

    omitted = []
    omitted_ids = set()
    retained = []
    transformed = {}
    for name in sorted(closure):
        raw = original[name]
        if not name.startswith('test/'):
            transformed[name] = raw
            continue
        source = compiled['sources'][name]
        edits = []
        for contract in source['ast'].get('nodes', []):
            if contract.get('nodeType') != 'ContractDefinition':
                continue
            for function in contract.get('nodes', []):
                if function.get('nodeType') != 'FunctionDefinition':
                    continue
                start, length = span(function, source['id'], raw)
                entry = {'source': name, 'contract': contract['name'], 'function': function.get('name', function.get('kind')),
                         'ast_id': function['id'], 'start': start, 'length': length,
                         'original_sha256': digest(raw[start:start + length])}
                if function.get('name', '').startswith('test') and function['id'] not in selected_ids:
                    omitted.append(entry)
                    omitted_ids.add(function['id'])
                    edits.append((start, length))
                    documentation = function.get('documentation')
                    if isinstance(documentation, dict) and documentation.get('src'):
                        dstart, dlength = span(documentation, source['id'], raw)
                        edits.append((dstart, dlength))
                        entry['attached_documentation_span'] = {'start': dstart, 'length': dlength}
                else:
                    entry['selected_test'] = function['id'] in selected_ids
                    body = function.get('body')
                    if body:
                        bstart, blength = span(body, source['id'], raw)
                        entry['body_sha256'] = digest(raw[bstart:bstart + blength])
                    retained.append(entry)
        result = bytearray(raw)
        changed = bytearray(len(raw))
        for start, length in edits:
            for index in range(start, start + length):
                changed[index] = 1
                if result[index] not in (10, 13):
                    result[index] = 32
        final = bytes(result)
        if len(final) != len(raw) or any(a != b and not changed[i] for i, (a, b) in enumerate(zip(raw, final))):
            raise ValueError('Transformation changed nonexcluded bytes')
        for entry in (x for x in retained if x['source'] == name):
            start, length = entry['start'], entry['length']
            if final[start:start + length] != raw[start:start + length]:
                raise ValueError('A retained function/helper changed')
        transformed[name] = final

    # Fail rather than silently omitting a test method called by a retained helper.
    def inspect(node):
        if isinstance(node, dict):
            if node.get('nodeType') == 'FunctionDefinition' and node.get('id') in omitted_ids:
                return
            if node.get('referencedDeclaration') in omitted_ids or any(x in omitted_ids for x in node.get('baseFunctions', [])):
                raise ValueError('Retained code depends on an excluded test method')
            for value in node.values():
                inspect(value)
        elif isinstance(node, list):
            for value in node:
                inspect(value)
    for name in closure:
        if name.startswith('test/'):
            inspect(compiled['sources'][name]['ast'])

    profile = Path(tempfile.mkdtemp(prefix='ast-focused-profile-', dir=evidence))
    for name in production_names | closure:
        path = profile / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(transformed.get(name, original[name]))
    (profile / 'empty').mkdir()
    mappings = {x.split('=', 1)[0]: x.split('=', 1)[1] for x in settings['remappings']}
    config = ('[profile.default]\nsrc="empty"\ntest="test"\nout="out"\ncache_path="cache"\n'
              'evm_version="cancun"\noptimizer=true\noptimizer_runs=1\noptimizer_details={yul=false}\n'
              'via_ir=true\nffi=false\nremappings=[\n')
    config += ''.join(json.dumps(key + '=' + (root / value).as_posix() + '/') + ',\n' for key, value in mappings.items())
    config += ']\n[profile.default.fuzz]\nruns=1000\n'
    (profile / 'foundry.toml').write_text(config, encoding='utf-8', newline='\n')
    manifest = {
        'schema': 1, 'purpose': 'Bounded AST-selected execution, not full regression.',
        'compiler_input_sha256': digest(input_path.read_bytes()), 'compiler_output_sha256': digest(output_path.read_bytes()),
        'size_evidence_sha256': digest(size_path.read_bytes()), 'production_sources': sizes['source_sha256'],
        'selection': selected, 'selected_methods': len(selected_ids), 'omitted_methods': omitted,
        'retained_function_bodies_and_helpers': retained, 'profile': str(profile),
        'sources': {name: {'original_sha256': digest(original[name]), 'transformed_sha256': digest(transformed.get(name, original[name])),
                           'bytes': len(original[name]), 'changed': original[name] != transformed.get(name, original[name])}
                    for name in sorted(production_names | closure)},
        'limitations': ['Only unselected project test function/attached-documentation spans are whitespace omitted.',
                       'Every selected method and retained helper is byte-identical, but unexecuted tests are not verified.',
                       'No compiler/optimizer/gas/size limit is relaxed; normal production gates are separate reused evidence.',
                       'No real provider, live market, wallet or service qualification is inferred.'],
    }
    save(evidence / 'focused-transformation.json', manifest)
    command = [str(external / 'foundry-v1.4.4/forge.exe'), 'test', '--root', str(profile), '--use',
               str(external / 'toolchain-0.8.26/solc.exe'), '--match-contract',
               '^(' + '|'.join(map(re.escape, SELECTION)) + ')$', '--json']
    environment = os.environ.copy()
    environment['RAYON_NUM_THREADS'] = '2'
    start = time.monotonic()
    result = subprocess.run(command, capture_output=True, env=environment, timeout=args.timeout)
    (evidence / 'focused-results.json').write_bytes(result.stdout)
    (evidence / 'focused-stderr.log').write_bytes(result.stderr)
    try:
        data = json.loads(result.stdout)
        cases = [{'suite': suite, 'method': method, 'status': outcome.get('status'), 'reason': outcome.get('reason'),
                  'gas': outcome.get('gas'), 'kind': outcome.get('kind')}
                 for suite, detail in data.items() for method, outcome in detail.get('test_results', {}).items()]
    except (ValueError, AttributeError):
        cases = []
    expected = {(contract, name) for contract, info in selected.items() for name in info['methods']}
    actual = {(case['suite'].split(':')[-1], case['method'].split('(')[0]) for case in cases}
    complete = actual == expected and len(cases) == len(expected)
    summary = {'schema': 1, 'exit_code': result.returncode, 'elapsed_seconds': round(time.monotonic() - start, 3),
               'command': command, 'selected_methods': len(expected), 'complete_selection_executed': complete,
               'missing': sorted(expected - actual), 'unexpected': sorted(actual - expected), 'cases': cases,
               'manifest_sha256': digest((evidence / 'focused-transformation.json').read_bytes())}
    if not cases:
        summary['diagnostic'] = result.stdout.decode(errors='replace')[:10000]
    save(evidence / 'focused-summary.json', summary)
    print(json.dumps({'exit_code': result.returncode, 'elapsed_seconds': summary['elapsed_seconds'],
                      'selected': len(expected), 'executed': len(cases), 'complete': complete,
                      'failed': [x for x in cases if x['status'] != 'Success'], 'profile': str(profile)}), flush=True)
    return result.returncode or (0 if complete else 1)


if __name__ == '__main__':
    raise SystemExit(main())
