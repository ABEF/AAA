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


def observe(read, code, *, contracts, code_hashes, bucket, accounting_version=4, physical_only=False):
    """Caller pins every read/code callback to one canonical block hash.

    No scheduling, journal, nonce, reset or confirmation observation is mutated.
    Fresh physical-only readers authenticate custody/principal independently of
    optional maintenance/reference diagnostics. They return no trading permission.
    """
    if type(bucket) is not int or not 0 < bucket < 1 << 256:
        raise ValueError('Invalid compound policy bucket')
    if type(accounting_version) is not int or accounting_version not in (4,5,6):
        raise ValueError('Unsupported explicit compound physical profile')
    if type(physical_only) is not bool or physical_only and accounting_version not in (5,6):
        raise ValueError('Physical-only inventory requires explicit accounting5')
    portfolio=accounting_version in (5,6)
    roles = ('access', 'vault', 'strategy', 'pools', 'liquidity', 'pool_manager', 'state_view')+(
        ('portfolio_policy','rebalance_confirmation','lp_position_executor','balancing_router','lp_balance_math') if portfolio else ())+(
        ('protocol_policy',) if accounting_version==6 and not physical_only else ())
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
    if (number('strategy', 'MAINTENANCE_POLICY_VERSION()') != (3 if portfolio else 2) or
            number('liquidity', 'stateView()') != int(targets['state_view'], 16) or
            number('liquidity', 'poolManager()') != int(targets['pool_manager'], 16) or
            number('state_view', 'poolManager()') != int(targets['pool_manager'], 16)):
        raise ValueError('Compound policy physical reader binding differs')
    if portfolio:
        for role,method,value in (('vault','ACCOUNTING_VERSION()',accounting_version),('liquidity','PORTFOLIO_VERSION()',2 if accounting_version==6 else 1),
                ('liquidity','LP_ROUTING_VERSION()',2),('portfolio_policy','PORTFOLIO_VERSION()',2 if accounting_version==6 else 1),
                ('rebalance_confirmation','REBALANCE_CONFIRMATION_VERSION()',3),
                ('strategy','portfolioPolicy()',int(targets['portfolio_policy'],16)),
                ('strategy','rebalanceConfirmation()',int(targets['rebalance_confirmation'],16)),
                ('portfolio_policy','strategy()',int(targets['strategy'],16)),
                ('portfolio_policy','access()',int(targets['access'],16)),
                ('rebalance_confirmation','strategy()',int(targets['strategy'],16)),
                ('rebalance_confirmation','access()',int(targets['access'],16)),
                ('liquidity','positionOperator()',int(targets['lp_position_executor'],16)),
                ('lp_position_executor','LP_POSITION_EXECUTOR_VERSION()',1),
                ('lp_position_executor','liquidityManager()',int(targets['liquidity'],16)),
                ('lp_position_executor','access()',int(targets['access'],16)),
                ('lp_position_executor','poolManager()',int(targets['pool_manager'],16)),
                ('lp_position_executor','stateView()',int(targets['state_view'],16)),
                ('lp_position_executor','balancingRouter()',int(targets['balancing_router'],16)),
                ('balancing_router','LP_ROUTING_VERSION()',2),
                ('balancing_router','liquidityManager()',int(targets['liquidity'],16)),
                ('balancing_router','access()',int(targets['access'],16)),
                ('balancing_router','poolManager()',int(targets['pool_manager'],16)),
                ('balancing_router','stateView()',int(targets['state_view'],16)),
                ('balancing_router','balanceMath()',int(targets['lp_balance_math'],16)),
                ('lp_balance_math','LP_BALANCE_MATH_VERSION()',1),
                ('lp_balance_math','balancer()',int(targets['balancing_router'],16))):
            if number(role,method)!=value:raise ValueError('Compound portfolio binding differs')
    position = decode_position(words('vault', 'group(uint256)', bucket, count=8), accounting_version)
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
    if (not 1 <= spacing <= 32767 or not MIN_TICK <= ticks[0] < ticks[1] <= MAX_TICK or
            any(value % spacing for value in ticks)):
        raise ValueError('Compound policy physical tick spacing differs')
    posm = number('liquidity', 'positionManager()')
    if not 0 < posm < 1 << 160: raise ValueError('Invalid physical position manager')
    posm = '0x' + f'{posm:040x}'
    if portfolio and (number('lp_position_executor','positionManager()')!=int(posm,16) or
            number('lp_position_executor','permit2()')!=number('liquidity','permit2()')):
        raise ValueError('Compound position executor dependency differs')
    physical = words(posm, 'getPoolAndPositionInfo(uint256)', lp, count=6)
    verify_position_identity(physical[:5], physical[5], int(pool, 16), ticks)
    if number(posm, 'ownerOf(uint256)', lp) != int(targets['vault'], 16):
        raise ValueError('Compound policy physical LP custody differs')
    if not 0 < number(posm, 'getPositionLiquidity(uint256)', lp) < 1 << 128:
        raise ValueError('Compound policy physical LP is empty')
    _, tick, _, _ = decode_slot0(words('state_view', 'getSlot0(bytes32)', pool, count=4),
                                expected_fee=int(config[2], 16))
    manual = 0
    if physical_only:
        result = {'scope': 'physical_portfolio_not_maintenance_eligibility'}
    else:
        manual = number('strategy', 'rangeUpdatePending(uint256)', bucket)
        if manual not in (0, 1): raise ValueError('Malformed compound range-change flag')
        result = classify_range(lower=ticks[0], upper=ticks[1], tick=tick, range_update_pending=bool(manual))
        if accounting_version==6:
            from zzz_ops.protocol_policy import observe as observe_policy
            result['maintenance_policy']=observe_policy(read,policy=targets['protocol_policy'],
                access=targets['access'],domain='maintenance')
    if portfolio:
        secondary=number('liquidity','secondaryId(uint256)',lp)
        count=number('liquidity','activeSecondaryCount()')
        if secondary==lp or not 0<=secondary<2**256 or not 0<=count<=4 or secondary and count==0:
            raise ValueError('Compound secondary inventory differs')
        mode=number('portfolio_policy','enabled(bytes32)',pool)
        pending=number('portfolio_policy','configurationPending(uint256)',bucket)
        geometry=number('portfolio_policy','geometryRevision(bytes32)',pool)
        applied=number('portfolio_policy','appliedRevision(uint256)',lp)
        residual_side=number('portfolio_policy','residualSideBps(bytes32)',pool)
        if (mode not in (0,1) or pending not in (0,1) or max(geometry,applied)>=2**64 or
                bool(pending)!=(geometry!=applied) or (not physical_only and pending and not manual) or
                not 0<residual_side<=10000):
            raise ValueError('Compound desired/applied portfolio policy differs')
        if accounting_version==6:
            minimum=number('portfolio_policy','minimumMainBps(bytes32)',pool)
            maximum=number('portfolio_policy','maximumResidualBps(bytes32)',pool)
            gap=number('portfolio_policy','residualGapSpacings(bytes32)',pool)
            if not 6000<=minimum<10000 or maximum!=10000-minimum or not 1<=gap<2**24 or gap*spacing>=MAX_TICK-MIN_TICK:
                raise ValueError('Portfolio2 allocation or residual gap exceeds approved bounds')
            result.update(minimum_main_bps=minimum,maximum_residual_bps=maximum,residual_gap_spacings=gap)
        # Disabling desired mode never makes an existing residual disappear.
        # Its actual identity/custody remains required until atomic merging.
        legs=[{'lp_token_id':lp,'tick_lower':ticks[0],'tick_upper':ticks[1]}]
        if secondary:
            secondary_ticks=[int(word,16) for word in words('liquidity','ticks(uint256)',secondary,count=2)]
            secondary_ticks=[value-2**256 if value>=2**255 else value for value in secondary_ticks]
            if (not MIN_TICK<=secondary_ticks[0]<secondary_ticks[1]<=MAX_TICK or
                    any(value%spacing for value in secondary_ticks)):
                raise ValueError('Compound residual tick geometry differs')
            physical=words(posm,'getPoolAndPositionInfo(uint256)',secondary,count=6)
            verify_position_identity(physical[:5],physical[5],int(pool,16),secondary_ticks)
            if (number(posm,'ownerOf(uint256)',secondary)!=int(targets['vault'],16) or
                    not 0<number(posm,'getPositionLiquidity(uint256)',secondary)<2**128):
                raise ValueError('Compound residual custody/liquidity differs')
            legs.append({'lp_token_id':secondary,'tick_lower':secondary_ticks[0],'tick_upper':secondary_ticks[1]})
        fingerprint=number('liquidity','portfolioFingerprint(uint256)',lp)
        if fingerprint==0:raise ValueError('Empty physical portfolio fingerprint')
        principal=words('liquidity','portfolioAmounts(uint256)',lp,count=2)
        amounts=[int(word,16) for word in words('liquidity','amounts(uint256)',lp,count=2)]
        if secondary:
            extra=[int(word,16) for word in words('liquidity','amounts(uint256)',secondary,count=2)]
            amounts=[a+b for a,b in zip(amounts,extra)]
        if any(value>=2**256 for value in amounts) or amounts!=[int(word,16) for word in principal]:
            raise ValueError('Compound portfolio amounts omit or duplicate a physical leg')
        result.update(portfolio_version=2 if accounting_version==6 else 1,secondary_id=secondary,active_secondary_count=count,
            portfolio_fingerprint='0x'+f'{fingerprint:064x}',physical_legs=legs,
            portfolio_amounts=[str(int(word,16)) for word in principal],
            desired_residual_enabled=bool(mode),portfolio_configuration_pending=bool(pending),
            residual_side_bps=residual_side)
        if not physical_only:
            physical_side,reference_side=([0,0] if manual else
                [int(word,16) for word in words('rebalance_confirmation','marketSides(uint256)',bucket,count=2)])
            required=number('rebalance_confirmation','requireReferenceExit()')
            if physical_side not in (0,1,2) or reference_side not in (0,1,2) or required not in (0,1):
                raise ValueError('Compound threshold observation differs')
            # Optional compound swaps wait while adjustment is being considered;
            # this is economic coordination, not a ban on entrant contributions.
            # Physical fingerprint excludes changing liquidity. Harvest is separate.
            waiting=result['allowed'] and physical_side!=0
            result.update(allowed=result['allowed'] and not physical_side,
                status='waiting_adjustment_threshold' if waiting else result['status'],
                threshold_side=None if manual else physical_side,reference_threshold_side=None if manual else reference_side,
                threshold_observation_scope='manual_configuration_exception' if manual else 'ordinary_market_threshold',
                reference_threshold_required=bool(required))
    return {**result, 'bucket_id': bucket, 'pool_id': pool, 'lp_token_id': lp,
            'last_rebalance': position['last_rebalance']}
