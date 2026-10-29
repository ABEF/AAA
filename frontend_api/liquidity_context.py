from zzz_ops.position import decode_position, is_local_position
"""Confirmed range and maintenance context, never a promised keeper schedule."""
from datetime import datetime, timezone

from frontend_api.service import ProjectionError, _address_word, _bool
from zzz_ops.tick_math import decode_slot0


def signed_tick(word):
    raw = int(word, 16)
    value = raw if raw < 2**255 else raw - 2**256
    if not -887272 <= value <= 887272:
        raise ProjectionError('Invalid canonical signed tick')
    return value


def contribution_context(p, pins, pool, bucket, position, config, header, block,
                         *, range_policy_version=0, range_policy=None, maintenance_policy_version=0,
                         rebalance_confirmation_version=0):
    """All RPC reads use the caller's pinned hash, including approval previews."""
    def read(role, method, *args, count=1):
        return p._call(pins[role], method, *args, block=block, words=count)

    slot = read('state_view', 'getSlot0(bytes32)', pool, count=4)
    try:
        spot, tick, _protocol_fee, _lp_fee = decode_slot0(slot, expected_fee=int(config[2], 16))
    except ValueError as exc:
        raise ProjectionError('Invalid or contradictory confirmed pool slot0') from exc
    # Check the admitted strategy's oracle/deviation guard even for an approval
    # response: a stale price must never be presented as a usable LP quote.
    if int(read('strategy', 'validatePrice(bytes32)', pool)[0], 16) != spot:
        raise ProjectionError('Strategy and pool price observations disagree')
    policy_metadata = None
    orientation = 0
    if range_policy_version == 1:
        from zzz_ops.range_policy import observe, verify
        try:
            observed = observe(lambda method,*args,count: read('strategy',method,*args,count=count),pool)
            policy_metadata = verify(range_policy,observed,config,header['timestamp'])
            orientation = policy_metadata['orientation']
        except (ValueError,TypeError,KeyError) as exc:
            raise ProjectionError('Confirmed Strategy range policy differs from the reviewed profile') from exc
    elif range_policy_version != 0:
        raise ProjectionError('Unsupported explicit range-policy profile')
    if type(maintenance_policy_version) is not int or maintenance_policy_version not in (0,1,2):
        raise ProjectionError('Unsupported explicit maintenance-policy profile')
    if (type(rebalance_confirmation_version) is not int or rebalance_confirmation_version not in (0,1,2) or
            rebalance_confirmation_version in (1,2) and (maintenance_policy_version != 2 or p.accounting_version != 4)):
        raise ProjectionError('Unsupported explicit rebalance-confirmation profile')
    spacing = int(config[3], 16)
    def active_range(lower, upper):
        if spacing <= 0 or lower >= upper or lower % spacing or upper % spacing:
            raise ProjectionError('Invalid current/target LP range')
        # Preserve slot0.tick at a legitimate exact downward crossing.
        return lower <= tick < upper
    existing = position is not None and int(position[7], 16) == 1
    cooldown = int(config[11], 16)
    if existing:
        lp = int(position[1], 16)
        decoded = decode_position(position,p.accounting_version)
        if lp == 0 or not is_local_position(decoded,p.accounting_version,p.chain,pins['vault']):
            raise ProjectionError('Active shared position has invalid local custody')
        lower, upper = map(signed_tick, read('liquidity', 'ticks(uint256)', lp, count=2))
        in_range = active_range(lower, upper)
        last, center = int(position[6], 16), int(position[5], 16)
        if last > header['timestamp'] or last >= 2**64 or not 0 < center < 2**160:
            raise ProjectionError('Invalid shared-position rebalance checkpoint')
        earliest = last + cooldown
        eligible = _bool(read('strategy', 'needsRebalance(uint256)', bucket)[0])
        range_pending = _bool(read('strategy', 'rangeUpdatePending(uint256)', bucket)[0])
        if maintenance_policy_version == 2:
            trigger = None
            needed = not in_range or range_pending
            status = 'eligible_now' if eligible else 'cooldown' if header['timestamp'] < earliest else 'waiting_for_range_exit'
            reason = ('out_of_range_and_range_update' if not in_range and range_pending else
                      'range_update' if range_pending else 'out_of_range' if not in_range else None)
        else:
            ref = int(read('oracle', 'referenceX96(address,address)',
                           _address_word(config[0], native=p.accounting_version in (2, 3, 4)), _address_word(config[1]))[0], 16)
            if not 0 < ref < 2**160:
                raise ProjectionError('Invalid oracle reference price')
            root_ratio = (center * 10**18 // ref if orientation == 1 else ref * 10**18 // center)
            movement = abs(root_ratio * root_ratio // 10**18 - 10**18)
            trigger = movement >= int(config[8], 16) * 10**14
            needed = trigger or range_pending
            status = 'eligible_now' if eligible else 'cooldown' if header['timestamp'] < earliest else 'waiting_for_price_trigger'
            reason = 'price_and_range' if trigger and range_pending else 'range_update' if range_pending else 'price_trigger' if trigger else None
        if eligible != (header['timestamp'] >= earliest and needed):
            raise ProjectionError('Rebalance eligibility disagrees with its confirmed conditions')
    else:
        target = read('strategy', 'target(bytes32)', pool, count=3)
        lower, upper = map(signed_tick, target[:2])
        in_range = active_range(lower, upper)
        lp, last, earliest, trigger, eligible, status = None, None, None, None, False, 'new_position'
        range_pending, reason = False, None
    raw_eligible=eligible
    confirmation=None
    if rebalance_confirmation_version in (1,2):
        from zzz_ops.rebalance_confirmation import observe as observe_confirmation
        try:
            confirmation=observe_confirmation(
                lambda target,method,*args,count:p._call(target,method,*args,block=block,words=count),
                strategy=pins['strategy'],budget=pins['budget'],
                confirmation=pins['rebalance_confirmation'],access=pins['access'],
                bucket=bucket if existing else None,timestamp=header['timestamp'],
                raw_eligible=raw_eligible,range_pending=range_pending,version=rebalance_confirmation_version)
        except (ValueError,TypeError,KeyError) as exc:
            raise ProjectionError('Confirmed rebalance observations are inconsistent or unavailable') from exc
        if existing:
            if raw_eligible and not range_pending and confirmation.get('physical_exit_side',confirmation['exit_side'])!=(1 if tick<lower else 2):
                raise ProjectionError('Confirmation direction differs from the confirmed physical range')
            eligible=confirmation['ready_at_snapshot']
            if raw_eligible and not eligible:
                status={'unconfigured':'confirmation_unconfigured',
                        'reference_disagreement':'reference_disagreement',
                        'waiting_first_observation':'confirmation_not_started',
                        'observation_stale':'confirmation_stale',
                        'confirming':'confirmation_pending'}[confirmation['status']]
    utc = None if earliest is None else datetime.fromtimestamp(earliest, timezone.utc).isoformat()
    if status == 'eligible_now':
        timing = ('Rebalance eligible now for an approved range update; ' if range_pending else 'Rebalance eligible now; ') + 'execution awaits a keeper check and successful safety checks.'
    elif status == 'cooldown':
        timing = (f'Earliest rebalance eligibility: {utc}; an approved range update is pending and safety checks must also pass.'
                  if range_pending else f'Earliest rebalance eligibility: {utc}; '
                  + ('the LP must remain outside its physical range and safety checks must also pass.'
                     if maintenance_policy_version == 2 else 'the price trigger and safety checks must also pass.'))
    elif status == 'waiting_for_range_exit':
        timing = 'Cooldown complete; the LP remains in its physical range. Rebalancing awaits range exit or an approved range update and safety checks.'
    elif status == 'waiting_for_price_trigger':
        timing = 'Cooldown complete; the next rebalance awaits the configured price trigger and safety checks.'
    elif status == 'confirmation_unconfigured':
        timing = 'Cooldown complete and the LP is outside range, but the on-chain confirmation gap policy is unconfigured or stopped.'
    elif status == 'confirmation_not_started':
        timing = 'Cooldown complete; recorded out-of-range confirmation has not started for this LP and policy.'
    elif status == 'reference_disagreement':
        timing = 'Our LP is outside range, but the independent reference does not confirm the same side. Ordinary automatic rebalancing is blocked.'
    elif status == 'confirmation_stale':
        timing = 'Recorded out-of-range observations are stale; confirmation must restart before rebalancing.'
    elif status == 'confirmation_pending':
        timing = (f'Cooldown complete; recorded out-of-range confirmation is in progress. '
                  f"At least {confirmation['seconds_remaining']} seconds remain, with further timely observations required. "
                  'This is sampled confirmation, not proof of uninterrupted price history.')
    else:
        timing = 'A new LP range will be created; there is no previous rebalance checkpoint.'
    warnings = []
    if not in_range:
        warnings.append({'code': 'LP_OUT_OF_RANGE', 'message':
            'This LP is outside its trading range and is not active swap liquidity. ' + timing +
            ' Next keeper check: unavailable. No execution time is guaranteed. '
            'Funded claims and activated-NFT royalty eligibility remain unchanged.'})
    elif eligible:
        warnings.append({'code': 'REBALANCE_ELIGIBLE', 'message': timing +
                         ' Next keeper check: unavailable. Reprepare if the LP position changes.'})
    return {'bucket_id': str(bucket), 'lp_token_id': None if lp is None else str(lp),
            'range_basis': 'existing_position' if existing else 'proposed_initial_position',
            'lower_tick': lower, 'upper_tick': upper, 'current_tick': tick,
            'sqrt_price_x96': str(spot), 'in_range': in_range,
            'configured_target_half_width_bps': int(config[7], 16),
            **({'maintenance_policy_version':maintenance_policy_version} if maintenance_policy_version else {}),
            **({'rebalance_confirmation_version':rebalance_confirmation_version,'rebalance_confirmation':confirmation}
               if rebalance_confirmation_version else {}),
            'range_policy_version':range_policy_version, 'range_orientation':orientation,
            'range_price_unit':'token0_per_token1' if orientation == 1 else 'token1_per_token0',
            'keeper_range_policy':policy_metadata,
            'rebalance': {'status': status, 'eligible_at_snapshot': eligible,
                          **({'raw_eligible_at_snapshot':raw_eligible} if rebalance_confirmation_version else {}),
                          'last_rebalance_at': last, 'cooldown_seconds': cooldown,
                          'earliest_eligible_at': earliest, 'earliest_eligible_utc': utc,
                          'price_trigger_met': trigger, 'trigger_bps': None if maintenance_policy_version == 2 else int(config[8], 16),
                          **({'outside_range_met':not in_range,
                              'eligibility_rule':'outside_or_operator_range_update'} if maintenance_policy_version == 2 else {}),
                          'range_update_pending': range_pending, 'eligibility_reason': reason,
                          'next_keeper_check_at': None, 'expected_execution_at': None,
                          'schedule_source': 'unavailable', 'explanation': timing},
            'warnings': warnings, 'reprepare_on_position_or_range_change': True}
