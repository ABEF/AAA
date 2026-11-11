"""Typed, read-only terminal holder-return adapters; never reward claims.

The caller authenticates the source/runtime graph and governance envelope through
Reader.base. Each adapter preserves the exact supplied selection and only reads
the principal ledgers relevant to this one operation. No generic recipient,
automatic batch progression, signature, journal or transaction submission exists.
"""
from __future__ import annotations

import copy

from frontend_api.service import ZERO, _bool
from keeper.compound_policy import observe as physical_portfolio
from keeper.monitor import rpc_quantity
from zzz_ops import operator_review as offline
from zzz_ops.abi import calldata, keccak256
from zzz_ops.manual_lp_review import integer
from zzz_ops.management_base import ManagementBlocked
from zzz_ops.position import decode_position

ACTIONS = frozenset(('collective_exit_begin', 'close_bucket',
    'allocate_principal', 'distribute_principal'))
MAX_BUCKETS = 4
MAX_NFTS = 1000
MAX_BATCH = 32


def validate(action, parameters):
    """Validate only explicit operator choices, without choosing amounts/IDs."""
    result = copy.deepcopy(parameters)
    if action == 'collective_exit_begin':
        offline._keys(parameters, {'confirm_terminal_exit'})
        if parameters['confirm_terminal_exit'] is not True:
            raise ValueError('Explicit irreversible collective-exit confirmation is required')
    elif action == 'close_bucket':
        offline._keys(parameters, {'bucket', 'minimumETH', 'minimumZZZ'})
        result['bucket'] = integer(parameters['bucket'], positive=True)
        for field in ('minimumETH', 'minimumZZZ'):
            result[field] = integer(parameters[field])
    elif action == 'allocate_principal':
        offline._keys(parameters, {'maximum'})
        result['maximum'] = integer(parameters['maximum'], positive=True)
        if result['maximum'] > MAX_BATCH:
            raise ValueError('Allocation selection must be one through32 mint ordinals')
    elif action == 'distribute_principal':
        offline._keys(parameters, {'nft_ids'})
        identifiers = parameters['nft_ids']
        if not isinstance(identifiers, list) or not 1 <= len(identifiers) <= MAX_BATCH:
            raise ValueError('Distribution selection must contain one through32 NFT IDs')
        result['nft_ids'] = [integer(value, positive=True) for value in identifiers]
        if len(set(result['nft_ids'])) != len(result['nft_ids']):
            raise ValueError('Distribution selection contains duplicate NFT IDs')
    else:
        raise ValueError('Unsupported terminal management action')
    return result


def _owner(reader, identifier):
    number = reader.uint('nft', 'ownerOf(uint256)', identifier)
    if not 0 < number < 1 << 160:
        raise ManagementBlocked('invalid_current_owner', 'Invalid current NFT owner')
    return '0x' + f'{number:040x}'


def _settlement(reader, bucket):
    words = reader.read('principal_exit', 'bucketSettlement(uint256)', bucket, count=7)
    values = [int(word, 16) for word in words[:6]]
    total, eth, zzz, allocated, allocated_eth, allocated_zzz = values
    closed = _bool(words[6])
    if (total == 0 or allocated > total or allocated_eth > eth or allocated_zzz > zzz or
            not closed and any(values[1:]) or
            closed and (allocated_eth != eth * allocated // total or
                allocated_zzz != zzz * allocated // total)):
        raise ManagementBlocked('inconsistent_settlement', 'Inconsistent captured bucket settlement')
    return dict(bucket=str(bucket), total_shares=str(total), eth_amount=str(eth),
        zzz_amount=str(zzz), allocated_shares=str(allocated), allocated_eth=str(allocated_eth),
        allocated_zzz=str(allocated_zzz), closed=closed)


def _position(reader, bucket, zzz):
    raw = reader.read('vault', 'group(uint256)', bucket, count=8)
    position = decode_position(raw, 7)
    shares = reader.uint('vault', 'bucketTotalShares(uint256)', bucket)
    record = dict(bucket=str(bucket), position_words=raw, shares=str(shares),
        custody_epoch=str(reader.uint('principal_exit', 'custodyEpoch(uint256)', bucket)),
        parking_nonce=str(reader.uint('principal_exit', 'parkingNonce(uint256)', bucket)))
    market = {}
    if shares:
        if (position['status'] not in ('active', 'parked') or
                position['status'] == 'active' and not position['lp_token_id'] or
                position['status'] == 'parked' and position['lp_token_id']):
            raise ManagementBlocked('bucket_custody_changed', 'Funded exit bucket must retain Active or Parked custody')
        config = reader.read('pools', 'accounting(bytes32)', position['pool_id'], count=14)
        if int(config[0], 16) != 0 or int(config[1], 16) != int(zzz, 16):
            raise ManagementBlocked('exit_pair_changed', 'Exit bucket differs from the fixed native ETH/ZZZ pair')
        record['pool_configuration'] = config
        if position['status'] == 'active':
            hashes = {role: item.code_hash for role, item in reader.p.contracts.items()}
            physical = physical_portfolio(reader.read,
                lambda target: reader.p.rpc.call('eth_getCode', [target, reader.block]),
                contracts=reader.targets, code_hashes=hashes, bucket=bucket,
                accounting_version=7, physical_only=True,execution_price_version=reader.p.execution_price_version)
            market['physical_amounts'] = physical.pop('portfolio_amounts')
            record['physical'] = physical
    elif position['lp_token_id'] or position['idle0'] or position['idle1'] or position['status'] != 'none':
        raise ManagementBlocked('zero_share_backing_mismatch', 'Zero-share exit bucket contains custody or attributed principal')
    return record, market


def _asset(reader):
    number = reader.uint('principal_exit', 'currentZZZ()')
    if not 0 < number < 1 << 160:
        raise ManagementBlocked('fixed_token_unavailable', 'Fixed principal-return token is unavailable')
    return '0x' + f'{number:040x}'


def _terminal(reader, phase, zzz):
    count = reader.uint('principal_exit', 'settlementBucketCount()')
    remaining = reader.uint('principal_exit', 'remainingBuckets()')
    minted = reader.uint('principal_exit', 'exitMintedCount()')
    cursor = reader.uint('principal_exit', 'allocationCursor()')
    if not 1 <= count <= MAX_BUCKETS or not 1 <= minted <= MAX_NFTS:
        raise ManagementBlocked('exit_inventory_invalid', 'Captured exit inventory exceeds reviewed bounds')
    if reader.uint('nft', 'mintedCount()') != minted:
        raise ManagementBlocked('exit_mint_count_changed', 'Captured exit mint count changed')
    review = reader.hashed('principal_exit', 'exitReviewHash()')
    buckets = []
    seen = set()
    for index in range(count):
        bucket = reader.uint('principal_exit', 'settlementBucketAt(uint256)', index)
        if not bucket or bucket in seen:
            raise ManagementBlocked('exit_bucket_inventory_invalid', 'Duplicate or empty captured exit bucket')
        seen.add(bucket)
        buckets.append(_settlement(reader, bucket))
    unclosed = sum(not row['closed'] for row in buckets)
    if (remaining != unclosed or phase == 1 and not remaining or
            phase in (2, 3) and remaining or
            phase == 1 and cursor != 0 or
            phase == 2 and not 1 <= cursor <= minted or
            phase == 3 and cursor != minted + 1):
        raise ManagementBlocked('exit_progress_changed', 'Exit phase/cursor differs from captured settlement inventory')
    if phase == 3 and any(row['allocated_shares'] != row['total_shares'] or
            row['allocated_eth'] != row['eth_amount'] or row['allocated_zzz'] != row['zzz_amount']
            for row in buckets):
        raise ManagementBlocked('allocation_incomplete', 'Ready exit is not completely allocated')
    eth = reader.uint('principal_exit', 'remainingETH()')
    token = reader.uint('principal_exit', 'remainingZZZ()')
    totals = [sum(int(row[key]) for row in buckets if row['closed'])
        for key in ('eth_amount', 'zzz_amount')]
    if (max(totals) >= 1 << 256 or eth > totals[0] or token > totals[1] or
            phase in (1, 2) and [eth, token] != totals):
        raise ManagementBlocked('principal_counters_inconsistent', 'Principal counters differ from captured closed backing')
    target = reader.targets['principal_exit']
    native_balance = rpc_quantity(reader.p.rpc.call('eth_getBalance', [target, reader.block]),
        'terminal principal native backing')
    token_balance = reader.uint(zzz, 'balanceOf(address)', target)
    if native_balance < eth or token_balance < token:
        raise ManagementBlocked('principal_backing_shortfall', 'Returned principal is not fully backed')
    return dict(review_hash=review, minted_count=minted, allocation_cursor=cursor,
        remaining_buckets=remaining, remaining_eth=str(eth), remaining_zzz=str(token),
        settlement_buckets=buckets), dict(native_balance_wei=str(native_balance),
            zzz_balance_raw=str(token_balance), prefunds_excluded_from_allocations=True)


def _principal(reader, identifier):
    row = reader.read('principal_exit', 'principalOf(uint256)', identifier, count=4)
    eth, zzz = (int(value, 16) for value in row[:2])
    allocated, paid = _bool(row[2]), _bool(row[3])
    if not allocated and (eth or zzz or paid):
        raise ManagementBlocked('principal_ledger_inconsistent', 'Unallocated NFT has principal or paid status')
    return dict(eth_amount=str(eth), zzz_amount=str(zzz), allocated=allocated, paid=paid)


def observe(reader, selected, governance):
    """Capture exact selected rights/controls; no swaps, rewards or USD reads."""
    action, parameters = selected['action'], selected['parameters']
    if action not in ACTIONS:
        raise ValueError('Unsupported terminal management action')
    phase = {'collective_exit_begin': 0, 'close_bucket': 1,
        'allocate_principal': 2, 'distribute_principal': 3}[action]
    base = reader.base(governance, paused=True if phase in (0, 1) else None, phase=phase)
    zzz = _asset(reader)
    controls = dict(base=base, fixed_zzz=zzz)
    market = {}
    if action == 'collective_exit_begin':
        maximum = reader.uint('vault', 'MAX_BUCKETS()')
        count = reader.uint('vault', 'bucketCount()')
        minted = reader.uint('nft', 'mintedCount()')
        if not 1 <= maximum <= MAX_BUCKETS or not 1 <= count <= maximum or not 1 <= minted <= MAX_NFTS:
            raise ManagementBlocked('exit_inventory_unavailable', 'No bounded funded collection can start collective exit')
        buckets, seen = [], set()
        for index in range(count):
            bucket = reader.uint('vault', 'bucketAt(uint256)', index)
            if not bucket or bucket in seen:
                raise ManagementBlocked('vault_bucket_inventory_invalid', 'Duplicate or empty Vault bucket identity')
            seen.add(bucket)
            record, observation = _position(reader, bucket, zzz)
            buckets.append(record)
            market[str(bucket)] = observation
        if not any(int(row['shares']) for row in buckets):
            raise ManagementBlocked('no_funded_bucket', 'Collection has no funded bucket to exit')
        residual_count = sum(bool(row.get('physical', {}).get('secondary_id')) for row in buckets)
        if reader.uint('liquidity', 'activeSecondaryCount()') != residual_count:
            raise ManagementBlocked('residual_inventory_mismatch', 'Exit inventory omits a registered residual position')
        controls.update(minted_count=minted, maximum_buckets=maximum, buckets=buckets,
            irreversible=True, lp_earnings_end_on_bucket_closure=True,
            nft_transfers_old_rewards_and_future_royalties_preserved=True)
    else:
        terminal, backing = _terminal(reader, phase, zzz)
        controls['terminal'] = terminal
        market['principal_backing'] = backing
        if action == 'close_bucket':
            bucket = parameters['bucket']
            matches = [row for row in terminal['settlement_buckets'] if row['bucket'] == str(bucket)]
            if len(matches) != 1 or matches[0]['closed']:
                raise ManagementBlocked('exit_bucket_not_open', 'Choose an unclosed captured exit bucket')
            position, observation = _position(reader, bucket, zzz)
            if position['shares'] != matches[0]['total_shares']:
                raise ManagementBlocked('exit_shares_changed', 'Captured exit shares changed')
            controls['selected_bucket'] = position
            market['selected_bucket'] = observation
        elif action == 'allocate_principal':
            cursor, minted = terminal['allocation_cursor'], terminal['minted_count']
            end = min(cursor + parameters['maximum'], minted + 1)
            rows, seen = [], set()
            settlements = {int(row['bucket']): row for row in terminal['settlement_buckets']}
            cumulative = {bucket: int(row['allocated_shares']) for bucket, row in settlements.items()}
            for ordinal in range(cursor, end):
                identifier = reader.uint('nft', 'tokenAtOrdinal(uint256)', ordinal)
                if not identifier or identifier in seen or reader.uint('nft', 'mintOrdinalOf(uint256)', identifier) != ordinal:
                    raise ManagementBlocked('allocation_ordinal_changed', 'Allocation ordinal identity is inconsistent')
                seen.add(identifier)
                principal = _principal(reader, identifier)
                if principal['allocated']:
                    raise ManagementBlocked('ordinal_already_allocated', 'Selected ordinal is already allocated')
                shares = reader.uint('vault', 'sharesOf(uint256)', identifier)
                bucket = reader.uint('vault', 'nftBucket(uint256)', identifier)
                if not shares and bucket or shares and bucket not in settlements:
                    raise ManagementBlocked('nft_exit_shares_inconsistent', 'NFT shares differ from captured exit bucket')
                if shares:
                    cumulative[bucket] += shares
                    if cumulative[bucket] > int(settlements[bucket]['total_shares']):
                        raise ManagementBlocked('allocation_shares_overflow', 'Selected ordinal shares exceed settlement denominator')
                rows.append(dict(ordinal=ordinal, token_id=str(identifier), shares=str(shares),
                    bucket=str(bucket), principal=principal))
            controls.update(selected_ordinals=rows, allocation_end_exclusive=end)
        else:
            payout_gas = reader.uint('protocol_policy', 'payoutGas()')
            if not 100_000 <= payout_gas <= 1_000_000:
                raise ManagementBlocked('payout_gas_invalid', 'Payout gas lies outside the reviewed source bounds')
            entries, eligible, sums = [], 0, [0, 0]
            settlements = {int(row['bucket']): row for row in terminal['settlement_buckets']}
            for identifier in parameters['nft_ids']:
                ordinal = reader.uint('nft', 'mintOrdinalOf(uint256)', identifier)
                if not 1 <= ordinal <= terminal['minted_count'] or reader.uint('nft', 'tokenAtOrdinal(uint256)', ordinal) != identifier:
                    raise ManagementBlocked('distribution_nft_unavailable', 'Distribution NFT is not in the captured mint inventory')
                principal = _principal(reader, identifier)
                if not principal['allocated']:
                    raise ManagementBlocked('selected_nft_unallocated', 'Ready exit contains an unallocated selected NFT')
                current_owner = _owner(reader, identifier)
                eth, token = int(principal['eth_amount']), int(principal['zzz_amount'])
                shares = reader.uint('vault', 'sharesOf(uint256)', identifier)
                bucket = reader.uint('vault', 'nftBucket(uint256)', identifier)
                if (not shares and (bucket or eth or token) or shares and
                        (bucket not in settlements or shares > int(settlements[bucket]['total_shares']) or
                            eth > int(settlements[bucket]['eth_amount']) or token > int(settlements[bucket]['zzz_amount']))):
                    raise ManagementBlocked('nft_principal_rights_inconsistent',
                        'NFT principal differs from its captured LP shares and bucket')
                status = 'already_paid' if principal['paid'] else 'zero' if not (eth or token) else 'eligible'
                claim = reader.read('principal_exit', 'claimablePrincipal(uint256)', identifier, count=2)
                if [int(word, 16) for word in claim] != ([0, 0] if principal['paid'] else [eth, token]):
                    raise ManagementBlocked('principal_view_inconsistent', 'Principal claimable view differs from its whole allocation')
                if status == 'eligible':
                    eligible += 1
                    sums[0] += eth
                    sums[1] += token
                entries.append(dict(token_id=str(identifier), ordinal=ordinal, owner=current_owner,
                    status=status, principal=principal, shares=str(shares), bucket=str(bucket)))
            if not eligible:
                raise ManagementBlocked('no_unpaid_principal', 'Selected distribution has no unpaid nonzero allocations')
            if sums[0] > int(terminal['remaining_eth']) or sums[1] > int(terminal['remaining_zzz']):
                raise ManagementBlocked('selected_principal_exceeds_backing', 'Selected payouts exceed remaining principal backing')
            controls['payout'] = dict(selected_entries=entries, eligible_count=eligible,
                payout_gas=payout_gas, beneficiary_rule='current_owner_at_inclusion',
                all_selected_paid_guaranteed=False, rewards_and_royalties_not_included=True)
    return {'controls': controls, 'market_observations': market}


def call_spec(selected, snapshot, review_hash):
    """Only four fixed Migration selectors; array order is operator-selected."""
    offline._hex(review_hash, 32, nonzero=True)
    action, parameters = selected['action'], selected['parameters']
    if action == 'collective_exit_begin':
        signature = 'beginCollectiveExit(bytes32)'
        args = {'reviewHash': review_hash}
        data = calldata(signature, review_hash)
    elif action == 'close_bucket':
        signature = 'closeBucket(uint256,uint256,uint256,uint256)'
        args = {key: str(parameters[key]) for key in ('bucket', 'minimumETH', 'minimumZZZ')}
        args['deadline'] = str(selected['expires_at'])
        data = calldata(signature, *args.values())
    elif action == 'allocate_principal':
        signature = 'allocatePrincipal(uint256)'
        args = {'maximum': str(parameters['maximum'])}
        data = calldata(signature, parameters['maximum'])
    elif action == 'distribute_principal':
        signature = 'distributePrincipal(uint256[])'
        identifiers = parameters['nft_ids']
        args = {'ids': [str(value) for value in identifiers]}
        data = ('0x' + keccak256(signature.encode()).hex()[:8] + f'{32:064x}' +
            f'{len(identifiers):064x}' + ''.join(f'{value:064x}' for value in identifiers))
    else:
        raise ValueError('Unsupported terminal management action')
    return signature, args, data
