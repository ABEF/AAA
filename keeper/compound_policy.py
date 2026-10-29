"""Read-only keeper policy, separate from on-chain compound eligibility."""
import re

from zzz_ops.abi import address, keccak256
from zzz_ops.position import decode_position
from zzz_ops.production_v4 import verify_position_identity
from zzz_ops.tick_math import MIN_TICK, MAX_TICK, decode_slot0


def classify_range(*, lower, upper, tick, range_update_pending):
    if (any(type(value) is not int for value in (lower, upper, tick)) or
            not MIN_TICK <= lower < upper <= MAX_TICK or not MIN_TICK <= tick < MAX_TICK or
            type(range_update_pending) is not bool):
        raise ValueError('Invalid physical compound policy inputs')
    inside = lower <= tick < upper
    status = 'waiting_outside_range' if not inside else 'waiting_range_change' if range_update_pending else 'in_range'
    return {'allowed': inside and not range_update_pending, 'status': status,
            'in_range': inside, 'range_update_pending': range_update_pending,
            'tick': tick, 'tick_lower': lower, 'tick_upper': upper,
            'scope': 'keeper_policy_not_contract_eligibility'}


def observe(read, code, *, contracts, code_hashes, bucket):
    """Caller pins every read/code callback to one canonical block hash.

    No scheduling, journal, nonce, reset or confirmation observation is mutated.
    """
    if type(bucket) is not int or not 0 < bucket < 1 << 256:
        raise ValueError('Invalid compound policy bucket')
    roles = ('access', 'vault', 'strategy', 'pools', 'liquidity', 'pool_manager', 'state_view')
    targets = {role: address(contracts[role]) for role in roles}
    for role, target in targets.items():
        raw, expected = code(target), code_hashes.get(role)
        if (not isinstance(expected, str) or re.fullmatch(r'0x[0-9a-fA-F]{64}', expected) is None or
                not isinstance(raw, str) or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', raw) is None or
                '0x' + keccak256(bytes.fromhex(raw[2:])).hex() != expected.lower()):
            raise ValueError('Compound policy runtime differs')
    def words(role, signature, *args, count=1):
        result = read(targets.get(role, role), signature, *args, count=count)
        if not isinstance(result, list) or len(result) != count or any(
                not isinstance(word, str) or re.fullmatch(r'[0-9a-fA-F]{64}', word) is None for word in result):
            raise ValueError('Malformed compound policy response')
        return [word.lower() for word in result]
    def number(role, signature, *args): return int(words(role, signature, *args)[0], 16)
    for role, label in (('vault', 'ZZZVault'), ('strategy', 'ZZZStrategy'),
                        ('pools', 'ZZZPoolRegistry'), ('liquidity', 'ZZZLiquidityManager')):
        if (number('access', 'module(bytes32)', '0x' + keccak256(label.encode()).hex()) != int(targets[role], 16) or
                number(role, 'access()') != int(targets['access'], 16)):
            raise ValueError('Compound policy module binding differs')
    if (number('strategy', 'MAINTENANCE_POLICY_VERSION()') != 2 or
            number('liquidity', 'stateView()') != int(targets['state_view'], 16) or
            number('liquidity', 'poolManager()') != int(targets['pool_manager'], 16) or
            number('state_view', 'poolManager()') != int(targets['pool_manager'], 16)):
        raise ValueError('Compound policy physical reader binding differs')
    position = decode_position(words('vault', 'group(uint256)', bucket, count=8), 4)
    if position['status'] != 'active' or position['lp_token_id'] == 0 or position['center_x96'] == 0:
        raise ValueError('Compound policy requires an active physical LP')
    pool, lp = position['pool_id'], position['lp_token_id']
    config = words('pools', 'get(bytes32)', pool, count=14)
    if ('0x' + keccak256(bytes.fromhex(''.join(config[:5]))).hex() != pool or
            words('pools', 'accounting(bytes32)', pool, count=14) != config or
            number('vault', 'poolBucket(bytes32)', pool) != bucket):
        raise ValueError('Compound policy pool identity differs')
    spacing = int(config[3], 16)
    raw_ticks = words('liquidity', 'ticks(uint256)', lp, count=2)
    ticks = [int(word, 16) for word in raw_ticks]
    ticks = [value - (1 << 256) if value >= 1 << 255 else value for value in ticks]
    if not 1 <= spacing <= 32767 or any(value % spacing for value in ticks):
        raise ValueError('Compound policy physical tick spacing differs')
    posm = number('liquidity', 'positionManager()')
    if not 0 < posm < 1 << 160: raise ValueError('Invalid physical position manager')
    posm = '0x' + f'{posm:040x}'
    physical = words(posm, 'getPoolAndPositionInfo(uint256)', lp, count=6)
    verify_position_identity(physical[:5], physical[5], int(pool, 16), ticks)
    if number(posm, 'ownerOf(uint256)', lp) != int(targets['vault'], 16):
        raise ValueError('Compound policy physical LP custody differs')
    if not 0 < number(posm, 'getPositionLiquidity(uint256)', lp) < 1 << 128:
        raise ValueError('Compound policy physical LP is empty')
    _, tick, _, _ = decode_slot0(words('state_view', 'getSlot0(bytes32)', pool, count=4),
                                expected_fee=int(config[2], 16))
    manual = number('strategy', 'rangeUpdatePending(uint256)', bucket)
    if manual not in (0, 1): raise ValueError('Malformed compound range-change flag')
    result = classify_range(lower=ticks[0], upper=ticks[1], tick=tick, range_update_pending=bool(manual))
    return {**result, 'bucket_id': bucket, 'pool_id': pool, 'lp_token_id': lp,
            'last_rebalance': position['last_rebalance']}
