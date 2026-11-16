"""Offline coverage inventory, not an execution or approval certificate."""
import collections
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256
from zzz_ops.function_reference import canonical_json

reference = json.loads((ROOT/'docs/function-reference.json').read_text(encoding='utf-8'))
examples = json.loads((ROOT/'docs/operator-call-examples.json').read_text(encoding='utf-8'))
operator_roles = {'G', 'B', 'K', 'N'}
family = {
    'ZZZAccessController': 'authority-bootstrap-pause-canonical-notice',
    'ZZZActivationAssets': 'source-token-admission',
    'ZZZBuyback': 'buyback-reserve-conversion',
    'ZZZCanonicalHandoff': 'canonical-freeze-import-commit-abort-recovery',
    'ZZZCompounder': 'compound-existing-geometry',
    'ZZZLPBalancer': 'execution-venue-solver-policy',
    'ZZZLPRewardConverter': 'earned-LP-currency-conversion',
    'ZZZMigration': 'principal-custody-recovery-terminal-exit',
    'ZZZMigrationBudget': 'loss-and-compound-cadence-policy',
    'ZZZNFT': 'mint-royalty-metadata-administration',
    'ZZZOracle': 'independent-pricing-source-policy',
    'ZZZPoolRegistry': 'pool-key-contribution-and-maintenance-policy',
    'ZZZPortfolioPolicy': 'main-residual-mode-geometry-policy',
    'ZZZProtocolPolicy': 'future-operating-sale-gas-VRF-policy',
    'ZZZRebalanceConfirmation': 'sampled-confirmation',
    'ZZZRewards': 'fixed-LP-assets-binding-and-conversion',
    'ZZZRoyaltyRewards': 'original-currency-recovery-allocation',
    'ZZZSeaDropMint': 'primary-sale-coordination',
    'ZZZStrategy': 'range-orientation-and-execution-quality',
    'ZZZVault': 'rebalance-and-permanent-bucket-reservation',
}
source_files = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8')
                for p in (ROOT/'src').rglob('*.sol')}


def locations(name, preferred):
    pattern = re.compile(r'\bfunction\s+' + re.escape(name) + r'\s*\(')
    candidates = []
    for path, text in source_files.items():
        if path == preferred or path.startswith('src/base/'):
            for match in pattern.finditer(text):
                candidates.append({'path': path, 'line': text[:match.start()].count('\n')+1})
    return candidates


def flatten(parameters, prefix=''):
    result = []
    for parameter in parameters:
        label = prefix + parameter['label']
        row = {k: parameter[k] for k in ('type', 'canonical_type', 'internal_type', 'explanation')}
        row['path'] = label
        row['shape'] = 'tuple-container' if 'components' in parameter else 'value-or-array-elements'
        result.append(row)
        result.extend(flatten(parameter.get('components', []), label+parameter['type'][5:]+'.'))
    return result


rows = []
for contract in reference['contracts']:
    for function in contract['functions']:
        identity = contract['name'] + '.' + function['signature']
        role = examples['rows'][identity]['role']
        operator = role in operator_roles
        rows.append({
            'id': identity, 'source': contract['source'], 'role': role,
            'kind': function['kind'], 'mutability': function['state_mutability'],
            'selector': ('0x'+keccak256(function['signature'].encode())[:4].hex()
                         if function['kind'] == 'function' else None),
            'purpose': function['purpose'], 'authority_and_lifecycle': function['access'],
            'native_value': function['native_value'], 'operation_notes': function['notes'],
            'inputs': flatten(function['inputs']), 'outputs': flatten(function['outputs']),
            'example_arguments': examples['rows'][identity]['arguments'],
            'example_value': examples['rows'][identity]['value'],
            'operator_target': operator,
            'assessment_scope': ('operator input/authority source-reference reconciliation; no new execution proof'
                                 if operator else 'exact ABI and documentation coverage only; transitive/interference review in family reports'),
            'family': family.get(contract['name'], 'bound-helper-holder-public-read-or-constructor'),
            'definition_candidates': locations(function['name'], contract['source'])
                                     if function['kind'] == 'function' else [],
            'moving_market_rule': (
                'Use original manifest/floors/deadline. Current price may change; fixed position boundaries do not. '
                'Revalidate authority, lifecycle, runtime, policy and the operation-specific state at inclusion. '
                'A catalogue row is not market/provider/gas qualification.'
                if operator else
                'Read/module/public/holder/callback/deployment classification does not make this a governance action.'),
        })
roles = dict(sorted(collections.Counter(row['role'] for row in rows).items()))
operator_rows = [row for row in rows if row['operator_target']]
operator_fields = [field for row in operator_rows for field in row['inputs']]
operator_leaves = [field for field in operator_fields if field['shape'] != 'tuple-container']
assert len({row['id'] for row in rows}) == len(rows)
assert all(field['explanation'] for field in operator_fields)
result = {
    'schema': 1,
    'approval': False,
    'reference_sha256': hashlib.sha256(canonical_json(reference).encode()).hexdigest(),
    'production_source_sha256': reference['source_snapshot']['source_sha256'],
    'counts': {**reference['counts'], 'total_entries': len(rows), 'roles': roles,
               'operator_targets': len(operator_rows), 'operator_input_records_including_containers': len(operator_fields),
               'operator_input_leaves': len(operator_leaves),
               'operator_nested_records': sum('.' in field['path'] for field in operator_fields)},
    'limits': [
        'ABI inventory completeness is not proof that all economic or adversarial executions are safe.',
        'Definition candidates retain overload ambiguity; authoritative signature and ABI order remain in each row.',
        'Examples are unresolved documentation; no chain read, live input adoption or transaction is performed.',
        'Only operator-role inputs receive the new complete nested-leaf annotation; other inputs retain their documented scope.',
        'Specific dynamic, gas, dependency and operating evidence remains source-scoped in linked family reports.',
    ],
    'rows': rows,
}
directory = Path(__file__).resolve().parent
(directory/'inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
lines = ['# Operator inventory and input coverage', '',
         'This is a source/reference reconciliation and documentation inventory, not approval or a claim that every ABI row was dynamically tested.', '',
         f"Current ABI: {len(rows)} entries = 963 functions + 40 constructors + 13 receivers across 40 concrete contracts.", '',
         f"Actual operator/nominated targets: {len(operator_rows)} = 72 governance/configuration + 11 bootstrap + 7 keeper + 2 nominated acceptances. Other roles: 689 reads, 159 module endpoints, 19 permissionless, 12 holder, 5 callbacks, 40 constructors.", '',
         f"Every operator input now has prose: {len(operator_fields)} records including tuple containers, {len(operator_leaves)} leaves, {result['counts']['operator_nested_records']} nested records. Units/bounds and current hash domains were checked against their defining source; executing all combinations is not implied.", '',
         'The machine-readable [inventory](inventory.json) has every exact overload/selector, caller/lifecycle, all recursively expanded input/output fields, unresolved examples, and explicit assessment limits.', '',
         '## Confirmed corrections', '',
         '- Three LP converter controls incorrectly called their boolean/basis-point value a native mint payment. They now state the actual type, unit and bounds.',
         '- Nested tuple component notes were always discarded by the reference producer. Optional strict nested notes preserve all operator field explanations in ABI order, with legacy string-note compatibility.',
         '- Operator expanded examples were keyed only by Solidity struct name. Distinct parking/close/consolidation/replacement semantics now keep separate anchors and field meanings instead of borrowing the first operation’s template.', '',
         '## Operator targets', '',
         '| Contract-qualified exact signature | Role | Family | Input leaves |',
         '| --- | --- | --- | --- |']
for row in operator_rows:
    lines.append('| `'+row['id']+'` | '+row['role']+' | '+row['family']+' | '+str(sum(field['shape']!='tuple-container' for field in row['inputs']))+' |')
lines += ['', '## Evidence limits and retained rights', '',
          'No production Solidity, ABI, storage, economics, guards or environment changes. LP fees and royalties remain distinct. FeeController.flushDust is module-restricted; Vault.collectFees remains public. Same-main consolidateResidual already atomically sets residual mode OFF; residual-only close does not. External swaps move current price, not existing LP bounds. Each emergency bit retains its stated guard; a raw mask never bypasses authority/accounting/terminal locks.', '',
          'Source-aware behavioral and economic conclusions are recorded in the main audit and contract-family report; this generated ledger must not be cited as 1,016 independently executed security cases.', '']
(directory/'INVENTORY.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps(result['counts']))
