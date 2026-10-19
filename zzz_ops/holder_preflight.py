"""Read-only, pinned NFT-holder inventory. Never authorizes a handoff."""
from __future__ import annotations

import hashlib
import json
import re
import time

from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.rpc import RpcError
from zzz_ops.work_budget import Budget, BudgetedRPC, request_scope

MAX_PAGE = 50
MAX_SUPPLY = 1000


def integer(value, minimum=0, maximum=2**256-1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError('Invalid inventory integer')
    return value


def hash32(value):
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', value):
        raise ValueError('Expected a 32-byte hash')
    return value.lower()


def code_bytes(value):
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value):
        raise RpcError('Malformed account code')
    raw = bytes.fromhex(value[2:])
    if len(raw) > 49152:
        raise RpcError('Account code exceeds inventory bound')
    return raw


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def scan_page(rpc, config, *, first=1, limit=MAX_PAGE, now=None):
    """Read <=50 ordinals at one explicit canonical block with a 60s work cap.

    Fixed block configuration allows independent pages/retries without silently
    mixing ownership snapshots. A failed page produces no successful inventory.
    """
    first = integer(first, 1, MAX_SUPPLY)
    limit = integer(limit, 1, MAX_PAGE)
    chain = integer(config['chain_id'], 1)
    block = integer(config['block_number'])
    block_hash = hash32(config['block_hash'])
    confirmations = integer(config['minimum_confirmations'], 1, 100000)
    # Configurable chain-specific confirmations are not a proof of finality.
    source = config['source']
    controller, nft = address(source['controller']), address(source['nft'])
    if controller == nft:
        raise ValueError('Distinct controller and NFT required')
    wall_time = time.time if now is None else now
    with request_scope(Budget(seconds=60, calls=256, posts=1024)):
        rpc = BudgetedRPC(rpc)
        if rpc.call('eth_chainId', []) != chain:
            raise RpcError('Inventory chain mismatch')
        header = rpc.call('eth_getBlockByNumber', [hex(block), False])
        if (not isinstance(header, dict) or header.get('number') != hex(block)
                or hash32(header.get('hash')) != block_hash
                or not re.fullmatch(r'0x[0-9a-fA-F]+', header.get('timestamp', ''))
                or int(header['timestamp'], 16) > wall_time() + 60):
            raise RpcError('Invalid inventory anchor')
        selector = {'blockHash': block_hash, 'requireCanonical': True}

        def get(target, signature, *args):
            values = decode_words(rpc.call('eth_call', [
                {'to': target, 'data': calldata(signature, *args)}, selector]))
            if len(values) != 1:
                raise RpcError('Unexpected inventory getter ABI')
            return int(values[0], 16)

        def pinned(target, expected):
            raw = code_bytes(rpc.call('eth_getCode', [target, selector]))
            actual = '0x' + keccak256(raw).hex()
            if not raw or actual != hash32(expected):
                raise RpcError('Inventory runtime pin mismatch')
            return actual

        def binding(cfg):
            c, n = address(cfg['controller']), address(cfg['nft'])
            if c == n:
                raise ValueError('Distinct controller and NFT required')
            pins = {key: pinned(target, cfg[key + '_code_hash'])
                    for key, target in (('controller', c), ('nft', n))}
            module = '0x' + keccak256(b'ZZZNFT').hex()
            if (get(c, 'module(bytes32)', module) != int(n, 16)
                    or get(n, 'access()') != int(c, 16)
                    or get(c, 'isSealed()') != 1):
                raise RpcError('Inventory deployment binding mismatch')
            return {'controller': c, 'nft': n, 'runtime_hashes': pins,
                    'canonical_state': get(c, 'canonicalState()')}

        observed_source = binding(source)
        if observed_source['canonical_state'] not in (0, 1):
            raise RpcError('Inventory source is not active or frozen')
        preparation = get(controller, 'preparationActive()')
        if preparation not in (0, 1):
            raise RpcError('Invalid preparation boolean')
        observed_source['preparation_active'] = bool(preparation)
        observed_source['preparation_hash'] = '0x' + format(get(controller, 'preparationHash()'), '064x')
        destination = None
        if config.get('destination') is not None:
            destination = binding(config['destination'])
            if (destination['canonical_state'] != 2
                    or destination['controller'] == controller
                    or destination['nft'] == nft):
                raise RpcError('Replacement must be a distinct inert importer')
        count = integer(get(nft, 'mintedCount()'), 0, MAX_SUPPLY)
        if first > max(count, 1):
            raise ValueError('Inventory page starts beyond minted supply')
        rows, owners = [], {}
        for ordinal in range(first, min(count, first + limit - 1) + 1):
            token = get(nft, 'tokenAtOrdinal(uint256)', ordinal)
            owner_word = get(nft, 'ownerOf(uint256)', token)
            if not 0 < owner_word < 2**160:
                raise RpcError('Malformed or zero NFT owner')
            owner = '0x' + format(owner_word, '040x')
            if owner not in owners:
                raw = code_bytes(rpc.call('eth_getCode', [owner, selector]))
                kind = ('no_code_at_snapshot' if not raw else
                        'delegated_account' if len(raw) == 23 and raw[:3] == b'\xef\x01\x00'
                        else 'contract')
                owners[owner] = {'owner': owner, 'kind': kind,
                    'code_hash': '0x' + keccak256(raw).hex(), 'code_size': len(raw)}
                if kind == 'delegated_account':
                    owners[owner]['delegation_target'] = '0x' + raw[3:].hex()
            rows.append({'ordinal': ordinal, 'token_id': str(token), 'owner': owner})
        if len({r['token_id'] for r in rows}) != len(rows):
            raise RpcError('Duplicate NFT inventory')
        # Recheck after all dependent calls, including confirmation depth.
        if rpc.call('eth_getBlockByNumber', [hex(block), False]) != header:
            raise RpcError('Inventory anchor changed')
        head = rpc.call('eth_getBlockByNumber', ['latest', False])
        if (not isinstance(head, dict) or not re.fullmatch(r'0x[0-9a-fA-F]+', head.get('number', ''))
                or int(head['number'], 16) < block + confirmations):
            raise RpcError('Insufficient inventory confirmations')
        page = {'schema': 1, 'snapshot': {'chain_id': chain, 'block_number': block,
            'block_hash': block_hash, 'timestamp': int(header['timestamp'], 16),
            'minimum_confirmations': confirmations, 'source': observed_source,
            'destination': destination, 'minted_count': count},
            'first': first, 'rows': rows, 'owners': owners}
        page['sha256'] = digest(page)
        return page


def summarize(pages):
    """Combine locally produced pages; report unresolved cases, never approval.

    SHA256 catches accidental edits, not forged RPC/local evidence. No receiver
    callback/interface probe can establish withdrawal compatibility.
    """
    if not isinstance(pages, list) or not 1 <= len(pages) <= MAX_SUPPLY:
        raise ValueError('Invalid inventory pages')
    snapshot, rows, owners = None, {}, {}
    token_ids = set()
    for page in pages:
        if page.get('schema') != 1 or page.get('sha256') != digest({k: v for k, v in page.items() if k != 'sha256'}):
            raise ValueError('Inventory page checksum mismatch')
        if snapshot is None:
            snapshot = page['snapshot']
        if snapshot != page['snapshot']:
            raise ValueError('Mixed inventory snapshots')
        integer(snapshot['minted_count'], 0, MAX_SUPPLY)
        first = integer(page['first'], 1, MAX_SUPPLY)
        if not isinstance(page['rows'], list) or len(page['rows']) > MAX_PAGE:
            raise ValueError('Invalid inventory page size')
        used = set()
        for offset, row in enumerate(page['rows']):
            ordinal = integer(row['ordinal'], 1, snapshot['minted_count'])
            if ordinal != first + offset or ordinal in rows:
                raise ValueError('Duplicate or unordered inventory ordinal')
            token = row['token_id']
            if not isinstance(token, str) or not re.fullmatch(r'0|[1-9][0-9]{0,77}', token) or int(token) >= 2**256 or token in token_ids:
                raise ValueError('Duplicate or invalid inventory token')
            owner = address(row['owner']); info = page['owners'][owner]
            if info['owner'] != owner or info['kind'] not in ('contract', 'delegated_account', 'no_code_at_snapshot'):
                raise ValueError('Malformed owner inventory')
            size = integer(info['code_size'], 0, 49152)
            if (size == 0) != (info['kind'] == 'no_code_at_snapshot'):
                raise ValueError('Inconsistent owner code classification')
            hash32(info['code_hash'])
            if owner in owners and owners[owner] != info:
                raise ValueError('Conflicting owner observations')
            owners[owner] = info; used.add(owner); rows[ordinal] = row; token_ids.add(token)
        if used != set(page['owners']):
            raise ValueError('Unreferenced owner observations')
    missing = sorted(set(range(1, snapshot['minted_count'] + 1)) - set(rows))
    unresolved = [dict(info, token_ids=[row['token_id'] for _, row in sorted(rows.items()) if row['owner'] == owner])
                  for owner, info in sorted(owners.items()) if info['kind'] != 'no_code_at_snapshot']
    return {'schema': 1, 'snapshot': snapshot, 'complete': not missing,
            'inventoried_nfts': len(rows), 'missing_ordinals': missing,
            'unresolved_contract_holders': unresolved, 'release_approved': False,
            'requires_frozen_rescan': snapshot['source']['canonical_state'] != 1,
            'replacement_not_supplied': snapshot['destination'] is None,
            'page_checksums': [p['sha256'] for p in pages],
            'limitations': ['Snapshot evidence only; not a finality proof or authorization.',
                'All code-bearing owners require a release/claim rehearsal for the exact replacement.',
                'No code at this block does not prove key control or future EOA behavior.',
                'Runtime hashes do not pin proxy implementation, admin or delegated-account behavior.',
                'Recheck canonical freeze, snapshot and all reviews immediately before commit.']}
