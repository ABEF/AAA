"""Typed custody-only operator adapters; no signer, sizing or state mutation.

Raw parking/residual close authenticate physical custody without consulting USD
feeds or ordinary operations flags. Resume deliberately retains the contract's
normal deployment policy and executes only through the caller's exact simulation.
"""
from __future__ import annotations

import copy

from frontend_api.service import ZERO, _bool
from keeper.compound_policy import observe as physical_portfolio
from zzz_ops import operator_review as offline
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError
from zzz_ops.manual_lp_review import integer
from zzz_ops.management_base import ManagementBlocked
from zzz_ops.position import decode_position
from zzz_ops.protocol_policy import observe as policy_observation
from zzz_ops.tick_math import MIN_TICK, MAX_TICK, MIN_SQRT, MAX_SQRT, decode_slot0

ACTIONS = frozenset(('park', 'resume', 'close_residual'))
PARKING_TUPLE = '(uint256,bytes32,uint256,uint256,uint256,uint64,uint64,address,address,uint128,uint128,uint256,bytes32,bytes32)'
PARKING_FIELDS = ('bucketId', 'poolId', 'lpTokenId', 'totalShares', 'depositUSD',
    'custodyEpoch', 'nonce', 'token0', 'token1', 'minimum0', 'minimum1', 'deadline',
    'reviewHash', 'portfolioHash')


def validate(action, parameters):
    """Validate explicit caller floors; zero raw-close floors remain explicit."""
    if action not in ACTIONS:
        raise ValueError('Unsupported custody management action')
    required = ({'bucket', 'destination_pool', 'minimumLiquidity'} if action == 'resume'
        else {'bucket', 'minimum0', 'minimum1'})
    offline._keys(parameters, required)
    result = {'bucket': integer(parameters['bucket'], positive=True)}
    if action == 'resume':
        result.update(destination_pool=offline._hex(parameters['destination_pool'], 32, nonzero=True),
            minimumLiquidity=integer(parameters['minimumLiquidity'], bits=128, positive=True))
    else:
        for key in ('minimum0', 'minimum1'):
            result[key] = integer(parameters[key], bits=128)
    return result


def _pool(reader, pool, zzz):
    config = reader.read('pools', 'accounting(bytes32)', pool, count=14)
    values = [int(word, 16) for word in config]
    bounds = (160, 160, 24, 24, 160, 1, 1, 16, 16, 16, 16, 32, 256, 256)
    if (len(values) != 14 or any(value >= 1 << width for value, width in zip(values, bounds)) or
            values[0] != 0 or values[1] != int(zzz, 16) or values[4] != 0 or
            not 1 <= values[3] <= 32767 or values[2] > 100000 or
            '0x' + keccak256(bytes.fromhex(''.join(config[:5]))).hex() != pool or
            reader.read('pools', 'get(bytes32)', pool, count=14) != config):
        raise RpcError('Custody pool key or canonical configuration differs')
    return config


def _position(reader, bucket, expected):
    raw = reader.read('vault', 'group(uint256)', bucket, count=8)
    position = decode_position(raw, 7)
    shares = reader.uint('vault', 'bucketTotalShares(uint256)', bucket)
    if position['status'] != expected or shares == 0:
        raise ManagementBlocked('bucket_state_mismatch', 'Custody action does not match funded bucket state')
    if reader.uint('vault', 'poolBucket(bytes32)', position['pool_id']) != bucket:
        raise RpcError('Custody source pool alias differs')
    return raw, position, shares


def _raw_close(reader, selected, governance):
    action, parameters = selected['action'], selected['parameters']
    base = reader.base(governance, paused=True, phase=0, allow_preparation=action == 'park')
    bucket = parameters['bucket']
    raw, position, shares = _position(reader, bucket, 'active')
    if position['lp_token_id'] == 0:
        raise RpcError('Raw custody close has no physical main position')
    zzz_number = reader.uint('principal_exit', 'currentZZZ()')
    if not 0 < zzz_number < 1 << 160:
        raise RpcError('Raw custody close lacks fixed ZZZ identity')
    zzz = '0x' + f'{zzz_number:040x}'
    config = _pool(reader, position['pool_id'], zzz)
    hashes = {role: item.code_hash for role, item in reader.p.contracts.items()}
    physical = physical_portfolio(reader.read,
        lambda target: reader.p.rpc.call('eth_getCode', [target, reader.block]),
        contracts=reader.targets, code_hashes=hashes, bucket=bucket,
        accounting_version=7, physical_only=True)
    if action == 'close_residual' and not physical['secondary_id']:
        raise ManagementBlocked('residual_absent', 'Residual-only close has no registered residual')
    nonce = reader.uint('principal_exit', 'parkingNonce(uint256)', bucket)
    epoch = reader.uint('principal_exit', 'custodyEpoch(uint256)', bucket)
    if max(nonce, epoch) >= 1 << 64:
        raise RpcError('Custody nonce or epoch exceeds uint64')
    controls = dict(global_state=base, position_words=raw, shares=str(shares),
        source_configuration=config, physical=copy.deepcopy(physical),
        parking_nonce=str(nonce), custody_epoch=str(epoch),
        registry_revision=str(reader.uint('pools', 'configurationRevision()')),
        portfolio_control=reader.hashed('portfolio_policy', 'controlFingerprint(bytes32)', position['pool_id']),
        fixed_zzz=zzz)
    # Principal quantities can change when ordinary traders move spot. Both
    # physical identities/keys/ticks/L remain fixed in the execution fingerprint.
    amounts = controls['physical'].pop('portfolio_amounts')
    return {'controls': controls, 'market_observations': {'physical_principal_raw': amounts}}


def _resume(reader, selected, governance):
    parameters = selected['parameters'];bucket = parameters['bucket']
    base = reader.base(governance, paused=False, phase=0)
    raw, position, shares = _position(reader, bucket, 'parked')
    if position['lp_token_id'] != 0:
        raise RpcError('Parked resume source retains a main LP')
    zzz_number = reader.uint('principal_exit', 'currentZZZ()')
    if not 0 < zzz_number < 1 << 160:
        raise RpcError('Resume lacks fixed ZZZ identity')
    zzz = '0x' + f'{zzz_number:040x}'
    source = _pool(reader, position['pool_id'], zzz)
    destination = parameters['destination_pool']
    target = _pool(reader, destination, zzz)
    if not _bool(target[6]):
        raise ManagementBlocked('destination_operations_disabled', 'Resume destination operations are disabled')
    # Deposit admission governs new NFT contributions; it is not a resume guard.
    reserved = reader.uint('vault', 'poolBucket(bytes32)', destination)
    if reserved not in (0, bucket):
        raise ManagementBlocked('destination_reserved_elsewhere', 'Resume destination belongs to another bucket')
    count = reader.uint('vault', 'bucketCount()')
    maximum = reader.uint('vault', 'MAX_BUCKETS()')
    if maximum != 4 or not 1 <= count <= maximum:
        raise RpcError('Resume custody bucket inventory exceeds its bound')
    bucket_ids = [reader.uint('vault', 'bucketAt(uint256)', i) for i in range(count)]
    if len(set(bucket_ids)) != count or bucket not in bucket_ids:
        raise RpcError('Resume source is absent from registered custody inventory')
    reserves = [reader.uint('fees', 'compoundBalance(uint256,address)', bucket, token) for token in (ZERO, zzz)]
    if not any((position['idle0'], position['idle1'], *reserves)):
        raise ManagementBlocked('no_resume_principal', 'Resume has no attributed or designated principal')
    prices = [reader.read('oracle', 'priceBounds(address)', token, count=3) for token in (ZERO, zzz)]
    for row in prices:
        if not 0 < int(row[0], 16) <= int(row[1], 16) or int(row[2], 16) == 0:
            raise RpcError('Resume independent price bounds are inconsistent')
    maintenance = policy_observation(reader.read, policy=reader.targets['protocol_policy'],
        access=reader.targets['access'], domain='maintenance')
    loss = reader.uint('budget', 'maintenanceLossBps()')
    additional = reader.uint('strategy', 'additionalLossBps()')
    if max(loss, additional) > 1000:
        raise RpcError('Resume financial limits exceed approved ceilings')
    route_count = reader.uint('balancing_router', 'executionPoolCount()')
    if route_count > 4:
        raise RpcError('Resume execution venue catalogue is unbounded')
    venues = [reader.hashed('balancing_router', 'executionPoolAt(uint256)', i) for i in range(route_count)]
    if len(set(venues)) != len(venues):
        raise RpcError('Resume execution venue catalogue repeats a pool')
    venue_configs = [_pool(reader, venue, zzz) for venue in venues]
    slot = reader.read('state_view', 'getSlot0(bytes32)', destination, count=4)
    decode_slot0(slot, expected_fee=int(target[2], 16))
    current_target = reader.read('strategy', 'target(bytes32)', destination, count=3)
    target_ticks = [int(value, 16) for value in current_target[:2]]
    target_ticks = [value - (1 << 256) if value >= 1 << 255 else value for value in target_ticks]
    if (not MIN_TICK <= target_ticks[0] < target_ticks[1] <= MAX_TICK or
            any(value % int(target[3], 16) for value in target_ticks) or
            not MIN_SQRT <= int(current_target[2], 16) < MAX_SQRT):
        raise RpcError('Resume current target geometry is inconsistent')
    nonce = reader.uint('principal_exit', 'parkingNonce(uint256)', bucket)
    epoch = reader.uint('principal_exit', 'custodyEpoch(uint256)', bucket)
    if max(nonce, epoch) >= 1 << 64:
        raise RpcError('Resume custody nonce or epoch exceeds uint64')
    controls = dict(global_state=base, position_words=raw, shares=str(shares), fixed_zzz=zzz,
        source_configuration=source, destination_configuration=target,
        destination_reservation=str(reserved), registered_buckets=list(map(str, bucket_ids)),
        registry_revision=str(reader.uint('pools', 'configurationRevision()')),
        parking_nonce=str(nonce), custody_epoch=str(epoch),
        compound_reserves_raw=list(map(str, reserves)), maintenance_policy=maintenance,
        maintenance_loss_bps=loss, additional_loss_bps=additional,
        execution_quality_revision=str(reader.uint('strategy', 'executionQualityRevision()')),
        price_policy_ids=[reader.hashed('oracle', 'activePolicy(address)', token) for token in (ZERO, zzz)],
        sequencer_policy='0x' + reader.read('oracle', 'activeSequencerPolicy()')[0],
        source_confirmation_control=reader.hashed('rebalance_confirmation', 'controlFingerprint(bytes32)', position['pool_id']),
        target_portfolio_control=reader.hashed('portfolio_policy', 'controlFingerprint(bytes32)', destination),
        portfolio_revision=str(reader.uint('portfolio_policy', 'revision()')),
        route_revision=str(reader.uint('balancing_router', 'executionRevision()')),
        execution_venues=venues, execution_venue_configurations=venue_configs)
    return {'controls': controls, 'market_observations': {'price_bounds': prices,
        'destination_slot0': slot, 'current_target_words': current_target}}


def observe(reader, selected, governance):
    if selected['action'] not in ACTIONS:
        raise ValueError('Unsupported custody management action')
    return _resume(reader, selected, governance) if selected['action'] == 'resume' else _raw_close(reader, selected, governance)


def call_spec(selected, snapshot, review_hash):
    """Return exact ABI argument names, ordering and calldata; never choose minima."""
    action, parameters = selected['action'], selected['parameters']
    if action == 'resume':
        signature = 'resume(uint256,bytes32,uint128,uint256)'
        arguments = dict(id=str(parameters['bucket']), pool=parameters['destination_pool'],
            minimum=str(parameters['minimumLiquidity']), deadline=str(selected['expires_at']))
        return signature, arguments, calldata(signature, *arguments.values())
    if action not in ('park', 'close_residual'):
        raise ValueError('Unsupported custody management action')
    offline._hex(review_hash, 32, nonzero=True)
    state = snapshot['controls'];position = decode_position(state['position_words'], 7)
    request = dict(bucketId=str(parameters['bucket']), poolId=position['pool_id'],
        lpTokenId=str(position['lp_token_id']), totalShares=state['shares'],
        depositUSD=str(position['deposit_usd']), custodyEpoch=state['custody_epoch'],
        nonce=state['parking_nonce'], token0=ZERO, token1=state['fixed_zzz'],
        minimum0=str(parameters['minimum0']), minimum1=str(parameters['minimum1']),
        deadline=str(selected['expires_at']), reviewHash=review_hash,
        portfolioHash=state['physical']['execution_portfolio_fingerprint'])
    signature = ('park' if action == 'park' else 'closeResidual') + '(' + PARKING_TUPLE + ')'
    encoded = ''.join(f'{int(request[key], 16) if key in ("poolId", "token0", "token1", "reviewHash", "portfolioHash") else int(request[key]):064x}' for key in PARKING_FIELDS)
    return signature, {'r': request}, '0x' + keccak256(signature.encode()).hex()[:8] + encoded
