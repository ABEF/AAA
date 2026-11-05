"""Source-bound operator examples. Documentation only: never RPC or signing."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from zzz_ops import function_reference as ref

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- BEGIN GENERATED OPERATOR CALLS -->'
END = '<!-- END GENERATED OPERATOR CALLS -->'
ROLES = {'R', 'G', 'B', 'K', 'H', 'P', 'N', 'M', 'C', 'D'}
GROUPS = (
    ('safety', 'Safety, governance and permissions', ('ZZZAccessController',)),
    ('liquidity', 'Daily LP management', ('ZZZVault', 'ZZZStrategy', 'ZZZRebalanceConfirmation',
                                       'ZZZCompounder', 'ZZZBuyback')),
    ('policy', 'Pools, ranges, execution and prices', ('ZZZPoolRegistry', 'ZZZActivationAssets',
              'ZZZPortfolioPolicy', 'ZZZProtocolPolicy', 'ZZZOracle', 'ZZZLPBalancer', 'ZZZMigrationBudget')),
    ('revenue', 'LP rewards, royalties and claims', ('ZZZFeeController', 'ZZZMembership', 'ZZZRewards',
                'ZZZRoyaltyRewards', 'ZZZLPRewardConverter', 'ZZZRoyaltyConverter', 'ZZZClaimRouter')),
    ('recovery', 'Parking, holder return and canonical replacement', ('ZZZMigration', 'ZZZCanonicalHandoff')),
    ('holders', 'NFTs, contributions and metadata', ('ZZZNFT', 'ZZZActivationEntry', 'ZZZNFTMetadata')),
    ('internals', 'Bound modules, helpers and factories', ('ZZZContributionPricing', 'ZZZLiquidityManager',
     'ZZZLPPositionExecutor', 'ZZZLPBalanceMath', 'ZZZV4RouteExecutor', 'ZZZCustodyValidation',
     'ZZZFeesCanonical', 'ZZZNFTCanonical', 'ZZZVaultCanonical', 'ZZZPythPriceFeed',
     'ZZZActivationAssetsFactory', 'ZZZRoyaltyFactory')),
)
WRITE_ORDER = {
    'ZZZAccessController': ('setPaused', 'setKeeper', 'setGuardian', 'proposeGovernance', 'acceptGovernance',
                            'startPreparation', 'cancelPreparation', 'bindProtocolPolicy', 'bind', 'seal'),
    'ZZZVault': ('collectFees', 'rebalance', 'activate', 'increase', 'mintDormant', 'reservePool'),
    'ZZZPortfolioPolicy': ('setMode', 'configureMainAllocation', 'configureResidualSide',
                          'configureResidualGap', 'setTriggerBps'),
    'ZZZProtocolPolicy': ('setEntryPolicy', 'setMaintenancePolicy', 'setGasPolicy', 'setMintPrice',
                         'proposeMintRecipient', 'acceptMintRecipient', 'setEvolutionThresholds',
                         'configureRandomness', 'setRandomnessRequestSettings', 'rotateRandomness'),
    'ZZZMigration': ('park', 'closeResidual', 'resume', 'moveFunds', 'emergencyRebalance',
                    'beginCollectiveExit', 'closeBucket', 'allocatePrincipal', 'distributePrincipal',
                    'claimPrincipal', 'invalidateParking', 'configureZZZ'),
    'ZZZRoyaltyRewards': ('sync', 'syncAll', 'convertBatch', 'recoverUnallocated', 'claim',
                         'forwardLate', 'fund', 'bindConverter'),
}


class ExampleError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ExampleError(message)


def key(contract, function):
    return contract['name'] + '.' + function['signature']


def symbol(value):
    return isinstance(value, str) and re.fullmatch(r'\$[A-Z][A-Z0-9_]*', value) is not None


def validate_value(parameter, value):
    """Check representation and ABI shape, not prices, permissions or readiness."""
    typ = parameter['type']
    if symbol(value):
        # A symbol is deliberately unresolved. Never turn it into a live value.
        require(not (typ.startswith('tuple') or '[' in typ), 'Expand every tuple/array example')
        require(re.fullmatch(r'bool|address|string|u?int\d*|bytes\d*', typ) is not None,
                'Unsupported ABI example type: ' + typ)
        return
    array = re.search(r'\[(\d*)\]$', typ)
    if array:
        require(isinstance(value, list), 'Array example must remain an array')
        require(len(value) == int(array[1]) if array[1] else len(value) > 0,
                'Wrong fixed array length or ambiguous empty example')
        element = dict(parameter, type=typ[:array.start()])
        for item in value:
            validate_value(element, item)
    elif typ == 'tuple':
        require(isinstance(value, list) and len(value) == len(parameter['components']),
                'Tuple fields must be complete and in ABI order')
        for field, item in zip(parameter['components'], value):
            validate_value(field, item)
    elif typ == 'bool':
        require(type(value) is bool, 'Boolean example is not canonical')
    elif re.fullmatch(r'u?int\d*', typ):
        require(type(value) is int, 'Integer example must be exact')
        signed = not typ.startswith('u')
        bits = int(re.search(r'\d+', typ)[0]) if re.search(r'\d+', typ) else 256
        require(-(1 << (bits - 1)) <= value < (1 << (bits - 1)) if signed else 0 <= value < (1 << bits),
                'Example integer exceeds ABI range')
    elif typ == 'address':
        require(isinstance(value, str) and re.fullmatch(r'0x[0-9a-f]{40}', value),
                'Address example must be exact or an unresolved symbol')
    elif typ == 'string':
        require(isinstance(value, str), 'String example is invalid')
    elif typ.startswith('bytes'):
        require(isinstance(value, str) and re.fullmatch(r'0x(?:[0-9a-f]{2})*', value),
                'Byte example must remain hexadecimal')
        if typ != 'bytes':
            require(len(value) == 2 + 2 * int(typ[5:]), 'Fixed bytes example has wrong length')
    else:
        raise ExampleError('Unsupported ABI example type: ' + typ)


def check_examples(reference, examples):
    require(isinstance(examples, dict) and set(examples) == {'schema', 'reference_sha256', 'rows'},
            'Unknown example schema fields')
    require(type(examples['schema']) is int and examples['schema'] == 1, 'Unknown example schema')
    digest = hashlib.sha256(ref.canonical_json(reference).encode()).hexdigest()
    require(examples['reference_sha256'] == digest, 'Review examples against the current complete function reference')
    expected = {key(c, f): f for c in reference['contracts'] for f in c['functions']}
    require(isinstance(examples['rows'], dict) and set(examples['rows']) == set(expected),
            'Missing, retired or extra callable examples')
    require(set(c['name'] for c in reference['contracts']) == {n for _, _, ns in GROUPS for n in ns},
            'Review navigation for the changed contract inventory')
    for identity, row in examples['rows'].items():
        f = expected[identity]
        require(isinstance(row, dict) and set(row) == {'role', 'short', 'arguments', 'value'},
                'Unknown or missing example fields: ' + identity)
        require(isinstance(row['role'], str) and row['role'] in ROLES,
                'Missing caller classification: ' + identity)
        require(isinstance(row['short'], str) and 1 <= len(row['short'].split()) <= 5 and
                not re.search(r'[|<>\r\n`]', row['short']), 'Explanation must be one to five words: ' + identity)
        require(isinstance(row['arguments'], list) and len(row['arguments']) == len(f['inputs']),
                'Missing or reordered top-level arguments: ' + identity)
        for parameter, value in zip(f['inputs'], row['arguments']):
            validate_value(parameter, value)
        require((row['value'] is not None) == (f['state_mutability'] == 'payable'),
                'Payable value must be separate and explicit: ' + identity)
        if row['value'] is not None:
            validate_value({'type': 'uint256'}, row['value'])
        access = f['access'].lower()
        if row['role'] == 'G':
            require('governance' in access and access.startswith((
                'before sealing:', 'current governance', 'selected source governance',
                'selected governance', 'governance only', 'drain-authorized governance')),
                'Governance classification contradicts the reviewed caller: ' + identity)
        elif row['role'] == 'K':
            require(access.startswith(('authorized keeper', 'enabled keeper', 'wallet must be keeper')),
                    'Keeper classification contradicts the reviewed caller: ' + identity)
        elif row['role'] == 'P':
            require(access.startswith(('permissionless', 'anyone', 'any payer', 'any address')) or
                    f['kind'] == 'receive' and identity == 'ZZZRoyaltyRewards.receive()',
                    'Permissionless classification contradicts the reviewed caller: ' + identity)
        elif row['role'] == 'B':
            require('bootstrap' in access, 'Bootstrap classification contradicts the reviewed caller: ' + identity)
        elif row['role'] == 'H':
            require(access.startswith(('current nft owner', 'current owner', 'owner,', 'owner or',
                                       'nft owner', 'actual current nft owner')),
                    'Holder classification contradicts the reviewed caller: ' + identity)
        elif row['role'] == 'C':
            require(f['name'] in {'rawFulfillRandomWords', 'unlockCallback', 'onERC721Received'},
                    'Review the new authenticated callback explicitly: ' + identity)
        elif row['role'] == 'N':
            require(f['name'] in {'acceptGovernance', 'acceptMintRecipient'} and 'pending' in access,
                    'Review the new nominated caller explicitly: ' + identity)
        if f['kind'] == 'function' and f['state_mutability'] in ('view', 'pure'):
            require(row['role'] in {'R', 'C'}, 'A read must not be presented as an ordinary transaction')
        elif f['kind'] == 'constructor':
            require(row['role'] == 'D', 'Constructor must remain deployment-only')
        else:
            require(row['role'] not in {'R', 'D'}, 'Write/receive has an invalid caller class')
    return expected


def display(value, *, nested=False):
    if symbol(value):
        return json.dumps(value[1:]) if nested else value[1:]
    if isinstance(value, list):
        return '[' + ', '.join(display(item, nested=True) for item in value) + ']'
    if type(value) is int and nested:
        # Explorer/JSON tooling must not round uint256 IDs through JS Number.
        return json.dumps(str(value))
    if isinstance(value, str) and value.startswith('0x'):
        return json.dumps(value) if nested else value
    return json.dumps(value, ensure_ascii=True)


def tuple_name(parameter):
    name = parameter['internal_type'].replace('struct ', '')
    return name + parameter['type'][5:] if '[' not in name else name


def render(reference, examples):
    check_examples(reference, examples)
    by_name = {c['name']: c for c in reference['contracts']}
    tuples = {}

    def arguments(f, row):
        labels = []
        for parameter, value in zip(f['inputs'], row['arguments']):
            typ = parameter['type']
            if typ.startswith('tuple'):
                name = tuple_name(parameter)
                anchor = 'input-' + re.sub(r'[^a-z0-9-]', '', name.lower().replace('.', '-').replace('[]', '-array'))
                known = tuples.setdefault(name, (anchor, parameter, value))
                labels.append('`' + parameter['label'] + '` [' + name + '](#' + known[0] + ')')
            else:
                labels.append('`' + parameter['label'] + ': ' + typ + '`')
        if f['state_mutability'] == 'payable':
            labels.append('`value: wei` (separate)')
        return '<br>'.join(labels) or 'None'

    def table(c, functions):
        result = ['| Function name | Expected input | Example call inputs | Explanation |',
                  '| --- | --- | --- | --- |']
        for f in functions:
            row = examples['rows'][key(c, f)]
            target = c['name'].removeprefix('ZZZ')
            label = target + '.' + (f['name'] if f['kind'] == 'function' else f['kind'])
            name = '[' + label + '](CONTRACT_FUNCTIONS.md#' + c['name'].lower() + ')'
            args = '(' + ', '.join(display(value) for value in row['arguments']) + ')'
            call = 'deploy ' + target + args if f['kind'] == 'constructor' else 'send ETH; data=0x' if f['kind'] == 'receive' else f['name'] + args
            if row['value'] is not None:
                call += '; value=' + display(row['value']) + ' wei'
            result.append('| `' + row['role'] + '` ' + name + ' | ' + arguments(f, row) + ' | `' + call + '` | ' + row['short'] + ' |')
        return result + ['']

    counts = reference['counts']
    lines = [BEGIN, '', '## Operator call tables', '',
             f"Source-bound coverage: **{counts['functions']} functions, {counts['constructors']} constructors and {counts['receive_hooks']} ETH receivers**. Every overload has its own row. Internal Solidity functions are not external entrypoints.", '',
             'Four columns only; explanations contain at most five words. Click a function for outputs, full caller restrictions and safety conditions. These are **unresolved input templates**, not simulated or approved transactions. Replace ALL uppercase symbols from the reviewed deployment/current snapshot. Never paste a symbol, guessed address, stale hash or illustrative setting into a wallet.', '',
             'Resolve [IDs, hashes and units](#resolve-ids-hashes-and-amounts) first; see [wallet/token approvals](#wallet-flows-and-external-token-approvals) for exact funding and transaction value.', '',
             '**Caller keys:** `G` governance after seal/bootstrap before seal; `B` bootstrap only; `K` keeper-authorized wallet; `H` NFT owner/approved NFT transfer caller as specified; `P` permissionless; `N` exact nominated recipient/provider; `M` fixed module/parent only; `C` authenticated callback only; `D` deployment only; `R` read, possibly guarded. These keys do not replace the linked exact permission. Governance is not automatically keeper-authorized. Guardian may pause, never unpause.', '',
             '**Input format:** examples show function(arguments), not transaction calldata. Tuple/array brackets preserve ABI order; addresses and decimal integers are quoted for JSON precision. Quoted uppercase names are unresolved replacements, not literal values; replace boolean placeholders with true/false. Enter separate arguments/expanded tuple fields in the explorer or reviewed ABI tool. A tuple/array is ONE top-level argument. Use exact integer strings, never floats. Transaction value/gas are separate. Direct mint examples do not implement OpenSea primary mint.', '',
             '**Order:** read identities/state → capture current inputs → review → simulate exact caller/value/calldata → sign if authorized → verify receipt/state. Failed/reverted/unresolved operations need receipt reconciliation; do not guess success, resend, reset journals or restart services from this table.', '',
             '### Table navigation', '']
    for slug, title, _ in GROUPS:
        lines.append('- [' + title + '](#calls-' + slug + ')')
    lines += ['- [Expanded tuple examples](#expanded-tuple-examples)',
              '- [Deployment constructors](#deployment-constructors)', '- [ETH receive hooks](#eth-receive-hooks)', '']
    for slug, title, names in GROUPS:
        lines += ['<a id="calls-' + slug + '"></a>', '', '### ' + title, '']
        for name in names:
            c = by_name[name]
            fs = [f for f in c['functions'] if f['kind'] == 'function']
            ordinary = [f for f in fs if examples['rows'][key(c, f)]['role'] not in {'R', 'M', 'C'}]
            reads = [f for f in fs if examples['rows'][key(c, f)]['role'] == 'R']
            restricted = [f for f in fs if examples['rows'][key(c, f)]['role'] in {'M', 'C'}]
            ordering = WRITE_ORDER.get(name, ())
            ordinary.sort(key=lambda f: (ordering.index(f['name']) if f['name'] in ordering else len(ordering),
                                         f['signature']))
            lines += ['<a id="' + name.lower() + '"></a>', '', '#### ' + name.removeprefix('ZZZ'), '']
            if ordinary:
                lines += table(c, ordinary)
            for title_, subset in [('Read functions and constants', reads), ('Contract-only calls: use the parent workflow', restricted)]:
                if subset:
                    lines += ['<details>', '<summary>' + title_ + ' (' + str(len(subset)) + ')</summary>', '']
                    lines += table(c, subset)
                    lines += ['</details>', '']
    lines += ['### Expanded tuple examples', '',
              'Fields are expanded recursively in exact ABI order. Uppercase symbols remain required snapshot/review inputs. These examples prove neither venue feasibility nor historical entitlement. Parameter semantics and bounds remain in the linked function/procedure.', '']
    for name, (anchor, parameter, value) in sorted(tuples.items()):
        lines += ['<details>', '<summary>' + name + '</summary>', '', '<a id="' + anchor + '"></a>', '',
                  '| Field | ABI type | Example input |', '| --- | --- | --- |']
        def visit(p, v, label):
            lines.append('| `' + label + '` | `' + p['canonical_type'] + '` | `' + display(v) + '` |')
            if p['type'].endswith(']'):
                element = dict(p, type=p['type'][:p['type'].rindex('[')],
                               canonical_type=p['canonical_type'][:p['canonical_type'].rindex('[')])
                visit(element, v[0], label + '[0]')
            elif p['type'] == 'tuple':
                for child, item in zip(p['components'], v):
                    visit(child, item, label + '.' + child['label'])
        visit(parameter, value, parameter['label'])
        lines += ['', '</details>', '']
    lines += ['### Deployment constructors', '', '<details>', '<summary>Deployment-only inputs; no deployment authorization</summary>', '']
    for c in reference['contracts']:
        lines += table(c, [f for f in c['functions'] if f['kind'] == 'constructor'])
    lines += ['</details>', '', '### ETH receive hooks', '', '<details>',
              '<summary>No ABI arguments; sender/value authentication still applies</summary>', '']
    for c in reference['contracts']:
        fs = [f for f in c['functions'] if f['kind'] in {'receive', 'fallback'}]
        if fs:
            lines += table(c, fs)
    lines += ['</details>', '', END]
    return '\n'.join(lines)


def generate(root=ROOT, *, check=False):
    root = Path(root)
    ref.generate(root, root/'docs/function-reference-notes.json', root/'docs/function-reference.json',
                 root/'docs/CONTRACT_FUNCTIONS.md', check=True)
    reference = ref.load_json(root/'docs/function-reference.json')
    examples = ref.load_json(root/'docs/operator-call-examples.json')
    manual = root/'docs/OPERATOR_MANUAL.md'
    original = manual.read_text(encoding='utf-8')
    require(original.count(BEGIN) == original.count(END) == 1, 'Operator table markers are missing or repeated')
    before, body = original.split(BEGIN)
    _, after = body.split(END)
    replacement = before + render(reference, examples) + after
    if check:
        require(original == replacement, 'Operator tables are stale; review examples and regenerate')
    else:
        newline = '\r\n' if b'\r\n' in manual.read_bytes() else '\n'
        manual.write_text(replacement, encoding='utf-8', newline=newline)
    return {**reference['counts'], 'example_rows': len(examples['rows']), 'ready_for_submission': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = generate(check=args.check)
    except (ExampleError, ref.ReferenceError, ValueError, OSError) as exc:
        parser.exit(1, 'Operator documentation check failed: ' + str(exc) + '\n')
    print(json.dumps(result))
    return 0
