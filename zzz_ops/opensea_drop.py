"""Offline PoPL SeaDrop phase manifests and proofs; never RPC, sign or submit.

SeaDrop V1 uses one keccak256(abi.encode(address, MintParams)) leaf, not
OpenZeppelin StandardMerkleTree's default double-hashed leaf. Its stage supply
ceilings and wallet limits are lifetime/cumulative. Independent PoPL phase caps
and reviewed rollover policy are REQUIRED; this artifact does not enforce them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import sys
import tempfile
import tomllib

from zzz_ops.abi import address, keccak256, word

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = b'ZZZ_POPL_OPENSEA_DROP_MANIFEST_V1\n'
SCHEMA = 1
MAX_SUPPLY = 1000
MAX_INPUT = 512 * 1024
MAX_OUTPUT = 8 * 1024 * 1024
MAX_SOURCE = 1024 * 1024
ZERO_HASH = '0x' + '0' * 64
SOURCE_PATHS = ('zzz_ops/opensea_drop.py', 'zzz_ops/abi.py',
                'zzz_ops/__init__.py', 'foundry.toml',
                'scripts/prepare-opensea-drop.py', 'src/ZZZNFT.sol',
                'src/ZZZVault.sol', 'src/ZZZProtocolPolicy.sol',
                'src/ZZZSeaDropMint.sol', 'src/interfaces/IZZZSeaDrop.sol')
BOUNDARIES = dict(offline_only=True, ready_for_submission=False,
                  network_access_performed=False, signing_performed=False,
                  onchain_snapshot_verified=False, target_runtime_verified=False,
                  authority_verified=False, simulation_performed=False,
                  opensea_primary_drop_accepted=False,
                  independent_phase_caps_verified=False,
                  gas_or_batch_acceptance_verified=False,
                  proof_is_authority_or_payment_evidence=False)
REQUIRED = {'schema', 'chain_id', 'nft_contract', 'seadrop',
            'seadrop_runtime_keccak256', 'creator_payout_address',
            'mint_price_wei', 'fee_bps', 'fee_recipient', 'public_wallet_limit',
            'max_batch', 'team', 'allowlist', 'team_window', 'allowlist_window',
            'allowed_payers',
            'public_window', 'release_unused_team_to_public',
            'review_notes_sha256', 'source_sha256'}
OPTIONAL = {'team_allocation', 'allowlist_allocation'}
PARAM_FIELDS = ('mintPrice', 'maxTotalMintableByWallet', 'startTime', 'endTime',
                'dropStageIndex', 'maxTokenSupplyForStage', 'feeBps',
                'restrictFeeRecipients')
CONFIG_FIELDS = ('teamAllocation', 'allowlistAllocation', 'publicWalletLimit',
                 'feeBps', 'maxBatch', 'teamStart', 'teamEnd', 'allowlistStart',
                 'allowlistEnd', 'publicStart', 'publicEnd',
                 'releaseUnusedTeamToPublic', 'merkleRoot', 'feeRecipient',
                 'allowedPayersHash')
MINT_REVIEW_DOMAIN = b'ZZZ_POPL_OPENSEA_MINT_INTENT_REVIEW_V1\n'
PUBLIC_MINT = 'mintPublic(address,address,address,uint256)'
ALLOWLIST_MINT = ('mintAllowList(address,address,address,uint256,'
                  '(uint256,uint256,uint256,uint256,uint256,uint256,uint256,bool),bytes32[])')
MAX_MINT_CALLDATA = 4 + 13 * 32 + 32 + 10 * 32


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError('Unexpected or missing fields')


def _uint(value, maximum=(1 << 256) - 1, *, minimum=0):
    if (not isinstance(value, str) or len(value) > 78 or
            re.fullmatch(r'(?:0|[1-9][0-9]*)', value) is None):
        raise ValueError('Use canonical decimal strings for quantities')
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError('Integer exceeds permitted bounds')
    return number


def _hex(value, *, prefix=False, nonzero=True):
    pattern = ('0x' if prefix else '') + r'[0-9a-f]{64}'
    if (not isinstance(value, str) or re.fullmatch(pattern, value) is None or
            nonzero and int(value, 16) == 0):
        raise ValueError('Use an exact lower-case nonzero 32-byte hash')
    return value


def _pair(a, b):
    return keccak256(min(a, b) + max(a, b))


def merkle_tree(leaves):
    """Sorted leaves/pairs; promote an unpaired node unchanged at each level."""
    if (not isinstance(leaves, list) or len(leaves) > MAX_SUPPLY or
            any(not isinstance(leaf, bytes) or len(leaf) != 32 for leaf in leaves) or
            len(set(leaves)) != len(leaves)):
        raise ValueError('Invalid or duplicate Merkle leaves')
    if not leaves:
        return ZERO_HASH, {}
    level = sorted(leaves)
    proofs = {leaf: [] for leaf in level}
    groups = [[leaf] for leaf in level]
    while len(level) > 1:
        next_level, next_groups = [], []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                next_level.append(level[index])
                next_groups.append(groups[index])
                continue
            left, right = level[index:index + 2]
            for leaf in groups[index]:
                proofs[leaf].append('0x' + right.hex())
            for leaf in groups[index + 1]:
                proofs[leaf].append('0x' + left.hex())
            next_level.append(_pair(left, right))
            next_groups.append(groups[index] + groups[index + 1])
        level, groups = next_level, next_groups
    return '0x' + level[0].hex(), proofs


def verify_proof(leaf, proof, root):
    if (not isinstance(leaf, bytes) or len(leaf) != 32 or
            not isinstance(proof, list) or len(proof) > 10):
        raise ValueError('Invalid bounded proof')
    _hex(root, prefix=True, nonzero=False)
    result = leaf
    for sibling in proof:
        _hex(sibling, prefix=True, nonzero=False)
        result = _pair(result, bytes.fromhex(sibling[2:]))
    return '0x' + result.hex() == root


def mint_leaf(minter, params):
    """The exact nine static ABI words consumed by SeaDrop V1."""
    _keys(params, PARAM_FIELDS)
    values = [word(address(minter), 'address')]
    for field in PARAM_FIELDS[:-1]:
        values.append(word(_uint(params[field]), 'uint256'))
    if type(params['restrictFeeRecipients']) is not bool:
        raise ValueError('Fee restriction must be a JSON boolean')
    values.append(word(params['restrictFeeRecipients'], 'bool'))
    return keccak256(bytes.fromhex(''.join(values)))


def address_list_hash(addresses):
    """keccak256(abi.encode(address[])), canonical ascending address order."""
    if (not isinstance(addresses, list) or len(addresses) > MAX_SUPPLY or
            addresses != sorted(set(address(item) for item in addresses))):
        raise ValueError('Address list must be canonical, unique and sorted')
    encoded = word(32, 'uint256') + word(len(addresses), 'uint256')
    encoded += ''.join(word(item, 'address') for item in addresses)
    return '0x' + keccak256(bytes.fromhex(encoded)).hex()


def team_list_hash(team):
    """keccak256(abi.encode(address[],uint256[])); team order is canonical."""
    addresses = [item['address'] for item in team]
    address_list_hash(addresses)
    quantities = [_uint(item['quantity'], MAX_SUPPLY, minimum=1) for item in team]
    first = word(len(team), 'uint256') + ''.join(word(a, 'address') for a in addresses)
    second = word(len(team), 'uint256') + ''.join(word(n, 'uint256') for n in quantities)
    encoded = word(64, 'uint256') + word(64 + len(bytes.fromhex(first)), 'uint256')
    return '0x' + keccak256(bytes.fromhex(encoded + first + second)).hex()


def source_identity(root=ROOT, additional=()):
    result = {}
    names = set(SOURCE_PATHS) | set(additional)
    root = Path(root).resolve()
    # Bind the entire fresh source graph, including modules reached by typed
    # external calls rather than a Solidity import from the mint entry point.
    names.update(path.relative_to(root).as_posix() for path in (root / 'src').rglob('*.sol'))
    with (root / 'foundry.toml').open('rb') as stream:
        configuration = tomllib.load(stream)
    remappings = configuration.get('profile', {}).get('default', {}).get('remappings', [])
    if (not isinstance(remappings, list) or len(remappings) > 32 or
            any(not isinstance(item, str) or item.count('=') != 1 for item in remappings)):
        raise ValueError('Unsupported source import remappings')
    remappings = sorted((item.split('=', 1) for item in remappings), key=lambda item: -len(item[0]))
    pending = set(names)
    while pending:
        if len(names) > 256:
            raise ValueError('Source binding count exceeds limit')
        name = min(pending)
        pending.remove(name)
        if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_@./-]{1,240}', name) or
                '\\' in name or any(part in ('', '.', '..') for part in name.split('/')) or
                name not in SOURCE_PATHS and not
                (name.startswith(('src/', 'node_modules/', 'lib/')) and name.endswith('.sol'))):
            raise ValueError('Only reviewed repository source paths can be bound')
        path = root / name
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError('Source binding is unavailable or outside repository')
        with path.open('rb') as stream:
            raw = stream.read(MAX_SOURCE + 1)
        if len(raw) > MAX_SOURCE:
            raise ValueError('Source binding exceeds limit')
        result[name] = hashlib.sha256(raw).hexdigest()
        if name.endswith('.sol'):
            for imported in re.findall(r'\bimport\s+(?:[^;]*?\bfrom\s+)?["\']([^"\']+)["\']\s*;', raw.decode('utf-8')):
                if imported.startswith('.'):
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), imported))
                else:
                    selected = next(((prefix, target) for prefix, target in remappings
                                     if imported.startswith(prefix)), None)
                    if selected is None:
                        raise ValueError('Unresolved Solidity import in source binding')
                    target = posixpath.normpath(selected[1] + imported[len(selected[0]):])
                if target not in names:
                    names.add(target)
                    pending.add(target)
    return result


def _window(value):
    _keys(value, ('start', 'end'))
    start = _uint(value['start'], (1 << 48) - 1, minimum=1)
    end = _uint(value['end'], (1 << 48) - 1, minimum=1)
    if start > end:
        raise ValueError('Sale window ends before it begins')
    return {'start': str(start), 'end': str(end)}


def _parameters(price, wallet, window, phase, ceiling, fee):
    return dict(zip(PARAM_FIELDS, (str(price), str(wallet), window['start'],
        window['end'], str(phase), str(ceiling), str(fee), True)))


def prepare(request, root=ROOT):
    """Validate explicit public inputs and produce a source-bound offline record."""
    if (not isinstance(request, dict) or not REQUIRED <= set(request) or
            set(request) - REQUIRED - OPTIONAL or type(request.get('schema')) is not int or
            request['schema'] != SCHEMA):
        raise ValueError('Unsupported or incomplete phase manifest')
    chain = _uint(request['chain_id'], minimum=1)
    price = _uint(request['mint_price_wei'], (1 << 80) - 1, minimum=1)
    fee = _uint(request['fee_bps'], 10000)
    wallet = _uint(request['public_wallet_limit'], MAX_SUPPLY, minimum=1)
    batch = _uint(request['max_batch'], 10, minimum=1)
    team_quota = _uint(request.get('team_allocation', '20'), MAX_SUPPLY)
    allow_quota = _uint(request.get('allowlist_allocation', '500'), MAX_SUPPLY)
    if team_quota + allow_quota > MAX_SUPPLY:
        raise ValueError('Phase allocations exceed 1000 lifetime NFTs')
    if type(request['release_unused_team_to_public']) is not bool:
        raise ValueError('Unused team rollover requires an explicit boolean decision')
    normalized = dict(request, chain_id=str(chain), mint_price_wei=str(price),
        fee_bps=str(fee), public_wallet_limit=str(wallet), max_batch=str(batch),
        team_allocation=str(team_quota), allowlist_allocation=str(allow_quota))
    for field in ('nft_contract', 'seadrop', 'creator_payout_address', 'fee_recipient'):
        normalized[field] = address(request[field])
    if normalized['nft_contract'] == normalized['seadrop']:
        raise ValueError('Collection and SeaDrop must be distinct contracts')
    if normalized['creator_payout_address'] in (normalized['nft_contract'], normalized['seadrop']):
        raise ValueError('Creator payout cannot be the minting contracts')
    _hex(request['seadrop_runtime_keccak256'], prefix=True)
    _hex(request['review_notes_sha256'])
    windows = [ _window(request[name + '_window']) for name in ('team', 'allowlist', 'public') ]
    if any(int(windows[i]['end']) >= int(windows[i + 1]['start']) for i in range(2)):
        raise ValueError('Inclusive sale phases must be disjoint and sequential')
    for name, window in zip(('team', 'allowlist', 'public'), windows):
        normalized[name + '_window'] = window
    if (not isinstance(request['team'], list) or len(request['team']) > MAX_SUPPLY or
            not isinstance(request['allowlist'], list) or len(request['allowlist']) > MAX_SUPPLY):
        raise ValueError('Eligible address lists exceed the bounded 1000-entry capacity')
    team = []
    for item in request['team']:
        _keys(item, ('address', 'quantity'))
        team.append(dict(address=address(item['address']),
                         quantity=str(_uint(item['quantity'], MAX_SUPPLY, minimum=1))))
    team.sort(key=lambda item: item['address'])
    team_addresses = [item['address'] for item in team]
    allowlist = sorted(address(item) for item in request['allowlist'])
    if (len(set(team_addresses)) != len(team_addresses) or len(set(allowlist)) != len(allowlist) or
            set(team_addresses) & set(allowlist)):
        raise ValueError('Team and allowlist must contain unique, distinct addresses')
    listed_team = sum(int(item['quantity']) for item in team)
    if listed_team > team_quota or len(allowlist) > allow_quota:
        raise ValueError('Proof entitlements exceed their explicit phase allocation')
    if team_quota and not team or allow_quota and not allowlist:
        raise ValueError('Every positive phase allocation requires reviewed eligibility leaves')
    if len(team) + len(allowlist) > MAX_SUPPLY:
        raise ValueError('Combined proof count exceeds 1000')
    normalized.update(team=team, allowlist=allowlist)
    payers = request['allowed_payers']
    if not isinstance(payers, list) or len(payers) > 16:
        raise ValueError('Explicit allowed payer list exceeds 16 entries')
    payers = sorted(address(item) for item in payers)
    if len(set(payers)) != len(payers):
        raise ValueError('Allowed payers must be unique')
    normalized['allowed_payers'] = payers
    sources = request['source_sha256']
    if not isinstance(sources, dict) or not set(SOURCE_PATHS) <= set(sources):
        raise ValueError('Required implementation source bindings are missing')
    for expected in sources.values():
        _hex(expected)
    actual_sources = source_identity(root, sources)
    if sources != actual_sources:
        raise ValueError('Source bytes differ from the reviewed manifest')
    records = []
    for item in team:
        params = _parameters(0, int(item['quantity']), windows[0], 1, team_quota, 0)
        records.append(dict(phase='team', minter=item['address'], mint_params=params,
                            leaf='0x' + mint_leaf(item['address'], params).hex()))
    for minter in allowlist:
        params = _parameters(price, 1, windows[1], 2, team_quota + allow_quota, fee)
        records.append(dict(phase='allowlist', minter=minter, mint_params=params,
                            leaf='0x' + mint_leaf(minter, params).hex()))
    root_hash, proofs = merkle_tree([bytes.fromhex(record['leaf'][2:]) for record in records])
    if root_hash == ZERO_HASH and team_quota + allow_quota != 0:
        raise ValueError('Reserved eligibility phases require at least one reviewed proof leaf')
    for record in records:
        record['proof'] = proofs[bytes.fromhex(record['leaf'][2:])]
    config = dict(zip(CONFIG_FIELDS, (str(team_quota), str(allow_quota), str(wallet),
        str(fee), str(batch), windows[0]['start'], windows[0]['end'],
        windows[1]['start'], windows[1]['end'], windows[2]['start'], windows[2]['end'],
        request['release_unused_team_to_public'], root_hash, normalized['fee_recipient'],
        address_list_hash(payers))))
    payload = dict(schema=SCHEMA, kind='popl_seadrop_offline_phase_manifest_v1',
        request=normalized, source_sha256=actual_sources, boundaries=dict(BOUNDARIES),
        mint_config=config,
        allowlist_root=root_hash, team_addresses_hash=address_list_hash(team_addresses),
        team_manifest_hash=team_list_hash(team), allowlist_addresses_hash=address_list_hash(allowlist),
        allowed_payers_hash=address_list_hash(payers),
        allocations=dict(lifetime_max='1000', team=str(team_quota), allowlist=str(allow_quota),
            public_base=str(MAX_SUPPLY - team_quota - allow_quota),
            unused_allowlist_to_public=True,
            release_unused_team_to_public=request['release_unused_team_to_public'],
            unlisted_team_capacity=str(team_quota - listed_team),
            unlisted_allowlist_capacity=str(allow_quota - len(allowlist))),
        public_drop=dict(mintPrice=str(price), startTime=windows[2]['start'],
            endTime=windows[2]['end'], maxTotalMintableByWallet=str(wallet),
            feeBps=str(fee), restrictFeeRecipients=True),
        proofs=records, royalty_open_delay_seconds='3600',
        requirements=[
            'PoPL must enforce independent phase caps; SeaDrop stage ceilings are cumulative.',
            'Allowlist wallet limit is one lifetime mint; team and allowlist addresses cannot overlap.',
            'Public capacity includes unused allowlist slots, plus unused team slots only when explicitly released.',
            'Configured price must match the current governed price; listed amounts are not on-chain observations.',
            'Fee recipient, payer permissions, payout, runtime, phase bindings and batch gas require actual qualification.',
            'OpenSea primary-drop onboarding and matching canonical NFT integration remain unverified.',
            'No sale-end change or one-hour royalty opening is executed by this artifact.'])
    review_hash = '0x' + hashlib.sha256(DOMAIN + canonical(payload)).hexdigest()
    result = dict(payload, review_hash=review_hash,
                  configure_arguments=[[config[field] for field in CONFIG_FIELDS], str(price), review_hash])
    if len(render(result)) > MAX_OUTPUT:
        raise ValueError('Proof artifact exceeds limit')
    return result


def check(artifact, root=ROOT):
    if not isinstance(artifact, dict) or 'request' not in artifact:
        raise ValueError('Malformed proof artifact')
    rebuilt = prepare(artifact['request'], root)
    if canonical(artifact) != canonical(rebuilt):
        raise ValueError('Proof artifact differs from its source-bound reconstruction')
    return dict(artifact_matches=True, review_hash=rebuilt['review_hash'],
                proof_count=len(rebuilt['proofs']), boundaries=dict(BOUNDARIES))


def _mint_address(value, *, zero=False):
    """Decode a canonical ABI address word; only recipient shorthand permits zero."""
    if not 0 <= value < 1 << 160 or value == 0 and not zero:
        raise ValueError('Invalid mint calldata address word')
    return '0x' + f'{value:040x}'


def review_mint(request, root=ROOT):
    """Review saved calldata against explicit intent, never establish live readiness.

    The input is this tool's normalized offline format, not an assumed OpenSea
    REST/SDK envelope. Original transaction fields and calldata are retained.
    A match cannot prove the sender, timestamp, upstream configuration or remaining
    mint entitlement at execution; those still require actual qualified review.
    """
    _keys(request, ('schema', 'manifest', 'intent', 'unsigned_transaction'))
    if type(request['schema']) is not int or request['schema'] != 1:
        raise ValueError('Unsupported mint-intent review schema')
    manifest = request['manifest']
    manifest_review = check(manifest, root)
    intent, transaction = request['intent'], request['unsigned_transaction']
    _keys(intent, ('caller', 'minter', 'phase', 'quantity', 'review_timestamp'))
    _keys(transaction, ('chain_id', 'from', 'to', 'value', 'data'))
    caller, minter = address(intent['caller']), address(intent['minter'])
    quantity = _uint(intent['quantity'], MAX_SUPPLY, minimum=1)
    timestamp = _uint(intent['review_timestamp'], (1 << 64) - 1, minimum=1)
    phase = intent['phase']
    if phase not in ('team', 'allowlist', 'public'):
        raise ValueError('Unknown mint phase')
    chain = _uint(transaction['chain_id'], minimum=1)
    declared = manifest['request']
    if (chain != 4663 or transaction['chain_id'] != declared['chain_id'] or
            address(transaction['from']) != caller or
            address(transaction['to']) != declared['seadrop']):
        raise ValueError('Mint transaction identity differs from review')
    value = _uint(transaction['value'])
    encoded = transaction['data']
    if (not isinstance(encoded, str) or len(encoded) > 2 + 2 * MAX_MINT_CALLDATA or
            re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', encoded) is None):
        raise ValueError('Invalid bounded mint calldata')
    raw = bytes.fromhex(encoded[2:])
    signature = PUBLIC_MINT if phase == 'public' else ALLOWLIST_MINT
    if raw[:4] != keccak256(signature.encode('ascii'))[:4] or (len(raw) - 4) % 32:
        raise ValueError('Unsupported or malformed mint function')
    words = [int.from_bytes(raw[index:index + 32], 'big')
             for index in range(4, len(raw), 32)]
    if len(words) < 4:
        raise ValueError('Mint calldata is truncated')
    nft = _mint_address(words[0])
    fee_recipient = _mint_address(words[1])
    encoded_minter = _mint_address(words[2], zero=True)
    recipient = caller if words[2] == 0 else encoded_minter
    if (nft != declared['nft_contract'] or fee_recipient != declared['fee_recipient'] or
            recipient != minter or words[3] != quantity or
            quantity > int(declared['max_batch'])):
        raise ValueError('Mint calldata differs from intended NFT, recipient or quantity')
    if recipient != caller and caller not in declared['allowed_payers']:
        raise ValueError('Delegated mint payer was not reviewed')
    window = declared[phase + '_window']
    if not int(window['start']) <= timestamp <= int(window['end']):
        raise ValueError('Reviewed timestamp is outside the selected phase')
    if phase == 'public':
        public_capacity = MAX_SUPPLY - (0 if declared['release_unused_team_to_public']
                                       else int(declared['team_allocation']))
        if (len(raw) != 4 + 4 * 32 or quantity > int(declared['public_wallet_limit']) or
                quantity > public_capacity):
            raise ValueError('Public mint calldata or wallet quantity is invalid')
        mint_price = int(declared['mint_price_wei'])
    else:
        if len(words) < 14 or words[12] != 13 * 32:
            raise ValueError('Noncanonical allowlist proof offset')
        proof_count = words[13]
        if proof_count > 10 or len(words) != 14 + proof_count or words[11] not in (0, 1):
            raise ValueError('Noncanonical bounded allowlist proof')
        record = next((row for row in manifest['proofs']
                       if row['phase'] == phase and row['minter'] == minter), None)
        if record is None:
            raise ValueError('Recipient has no reviewed phase entitlement')
        params = record['mint_params']
        expected = [int(params[field]) for field in PARAM_FIELDS[:-1]] + [1]
        proof = ['0x' + f'{item:064x}' for item in words[14:]]
        if (words[4:12] != expected or proof != record['proof'] or
                quantity > int(params['maxTotalMintableByWallet']) or
                not verify_proof(mint_leaf(minter, params), proof, manifest['allowlist_root'])):
            raise ValueError('Allowlist terms or proof differ from reviewed entitlement')
        mint_price = int(params['mintPrice'])
    if value != quantity * mint_price:
        raise ValueError('Gross native mint value differs from reviewed price')
    payload = dict(schema=1, kind='popl_seadrop_offline_mint_intent_review_v1',
        manifest_review_hash=manifest_review['review_hash'],
        manifest_sha256=hashlib.sha256(canonical(manifest)).hexdigest(),
        request_sha256=hashlib.sha256(canonical(request)).hexdigest(),
        original_transaction_sha256=hashlib.sha256(canonical(transaction)).hexdigest(),
        calldata_sha256=hashlib.sha256(raw).hexdigest(),
        intent=dict(intent), unsigned_transaction=dict(transaction),
        function=signature, phase=phase, recipient=minter, payer=caller,
        quantity=str(quantity), gross_native_value_wei=str(value),
        manifest_matches=True, transaction_matches_reviewed_intent=True,
        calldata_modified=False, source_sha256=dict(manifest['source_sha256']),
        boundaries=dict(BOUNDARIES),
        limitations=[
            'Normalized offline input is not an authenticated REST or SDK response.',
            'Reviewed time is supplied intent, not a verified chain timestamp.',
            'Current configuration, minted counts, remaining entitlement, payer authority and balances are unverified.',
            'No runtime, simulation, gas/fees, OpenSea onboarding or submission readiness is established.',
            'No calldata is generated, altered, signed, sent or queued.'])
    payload['review_hash'] = '0x' + hashlib.sha256(MINT_REVIEW_DOMAIN + canonical(payload)).hexdigest()
    if len(render(payload)) > MAX_OUTPUT:
        raise ValueError('Mint review exceeds output limit')
    return payload


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def _reject(_value):
    raise ValueError('Only exact integer JSON numbers are permitted')


def decode(raw, maximum=MAX_INPUT):
    if not isinstance(raw, bytes) or len(raw) > maximum:
        raise ValueError('JSON input exceeds limit')
    text = raw.decode('utf-8-sig')
    depth, quoted, escape = 0, False, False
    for char in text:
        if quoted:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > 12:
                raise ValueError('JSON nesting exceeds limit')
        elif char in ']}':
            depth -= 1
    return json.loads(text, object_pairs_hook=_pairs, parse_float=_reject, parse_constant=_reject)


def render(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')


def publish(path, raw):
    """Publish complete bytes exclusively; an existing path is never replaced."""
    path = Path(path)
    if len(raw) > MAX_OUTPUT or not path.parent.is_dir():
        raise ValueError('Output exceeds limit or its parent directory is unavailable')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.popl-drop-', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        if hasattr(os, 'O_DIRECTORY'):
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None, *, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    profile = sub.add_parser('profile')
    profile.add_argument('--output', type=Path)
    for command in ('prepare', 'check', 'review-mint'):
        selected = sub.add_parser(command)
        selected.add_argument('input', type=Path)
        selected.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'profile':
            result = dict(schema=SCHEMA, source_sha256=source_identity(root),
                          allocation_defaults=dict(team_allocation='20', allowlist_allocation='500'),
                          required_fields=sorted(REQUIRED), boundaries=dict(BOUNDARIES))
        else:
            maximum = MAX_OUTPUT if args.command in ('check', 'review-mint') else MAX_INPUT
            with args.input.open('rb') as stream:
                request = decode(stream.read(maximum + 1), maximum)
            if args.command == 'review-mint':
                result = review_mint(request, root)
            else:
                result = prepare(request, root) if args.command == 'prepare' else check(request, root)
        raw = render(result)
        if args.output:
            publish(args.output, raw)
        else:
            sys.stdout.write(raw.decode('ascii'))
        return 0
    except (OSError, TypeError, ValueError, KeyError, UnicodeError, RecursionError):
        print('Offline drop manifest rejected; check exact inputs, source bindings and output availability.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
