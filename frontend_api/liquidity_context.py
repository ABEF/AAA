"""Confirmed range and maintenance context, never a promised keeper schedule."""
from datetime import datetime, timezone

from frontend_api.service import ProjectionError, _address_word, _bool


def signed_tick(word):
    raw = int(word, 16)
    value = raw if raw < 2**255 else raw - 2**256
    if not -887272 <= value <= 887272:
        raise ProjectionError('Invalid canonical signed tick')
    return value


def contribution_context(p, pins, pool, bucket, position, config, header, block):
    """All RPC reads use the caller's pinned hash, including approval previews."""
    def read(role, method, *args, count=1):
        return p._call(pins[role], method, *args, block=block, words=count)

    slot = read('state_view', 'getSlot0(bytes32)', pool, count=4)
    spot, tick = int(slot[0], 16), signed_tick(slot[1])
    if not 4295128739 <= spot < 1461446703485210103287273052203988822378723970342:
        raise ProjectionError('Invalid pool sqrt price')
    # Check the admitted strategy's oracle/deviation guard even for an approval
    # response: a stale price must never be presented as a usable LP quote.
    if int(read('strategy', 'validatePrice(bytes32)', pool)[0], 16) != spot:
        raise ProjectionError('Strategy and pool price observations disagree')
    existing = position is not None and int(position[7], 16) == 1
    cooldown = int(config[11], 16)
    if existing:
        lp = int(position[1], 16)
        if (lp == 0 or int(position[8], 16) != p.chain or int(position[13], 16) != p.chain or
                _address_word(position[9]) != pins['vault'] or _address_word(position[14]) != pins['vault']):
            raise ProjectionError('Active shared position has invalid local custody')
        lower, upper = map(signed_tick, read('liquidity', 'ticks(uint256)', lp, count=2))
        last, center = int(position[6], 16), int(position[5], 16)
        if last > header['timestamp'] or last >= 2**64 or not 0 < center < 2**160:
            raise ProjectionError('Invalid shared-position rebalance checkpoint')
        earliest = last + cooldown
        eligible = _bool(read('strategy', 'needsRebalance(uint256)', bucket)[0])
        range_pending = _bool(read('strategy', 'rangeUpdatePending(uint256)', bucket)[0])
        ref = int(read('oracle', 'referenceX96(address,address)',
                       _address_word(config[0], native=p.accounting_version == 2), _address_word(config[1]))[0], 16)
        if not 0 < ref < 2**160:
            raise ProjectionError('Invalid oracle reference price')
        root_ratio = ref * 10**18 // center
        movement = abs(root_ratio * root_ratio // 10**18 - 10**18)
        trigger = movement >= int(config[8], 16) * 10**14
        if eligible != (header['timestamp'] >= earliest and (trigger or range_pending)):
            raise ProjectionError('Rebalance eligibility disagrees with its confirmed conditions')
        status = 'eligible_now' if eligible else 'cooldown' if header['timestamp'] < earliest else 'waiting_for_price_trigger'
        reason = 'price_and_range' if trigger and range_pending else 'range_update' if range_pending else 'price_trigger' if trigger else None
    else:
        target = read('strategy', 'target(bytes32)', pool, count=3)
        lower, upper = map(signed_tick, target[:2])
        lp, last, earliest, trigger, eligible, status = None, None, None, None, False, 'new_position'
        range_pending, reason = False, None
    spacing = int(config[3], 16)
    if spacing <= 0 or lower >= upper or lower % spacing or upper % spacing:
        raise ProjectionError('Invalid current/target LP range')
    # slot0.tick, rather than sqrt alone, respects downward crossing at an exact
    # tick boundary. Uniswap active intervals are [lower, upper).
    in_range = lower <= tick < upper
    utc = None if earliest is None else datetime.fromtimestamp(earliest, timezone.utc).isoformat()
    if status == 'eligible_now':
        timing = ('Rebalance eligible now for an approved range update; ' if range_pending else 'Rebalance eligible now; ') + 'execution awaits a keeper check and successful safety checks.'
    elif status == 'cooldown':
        timing = (f'Earliest rebalance eligibility: {utc}; an approved range update is pending and safety checks must also pass.'
                  if range_pending else f'Earliest rebalance eligibility: {utc}; the price trigger and safety checks must also pass.')
    elif status == 'waiting_for_price_trigger':
        timing = 'Cooldown complete; the next rebalance awaits the configured price trigger and safety checks.'
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
            'rebalance': {'status': status, 'eligible_at_snapshot': eligible,
                          'last_rebalance_at': last, 'cooldown_seconds': cooldown,
                          'earliest_eligible_at': earliest, 'earliest_eligible_utc': utc,
                          'price_trigger_met': trigger, 'trigger_bps': int(config[8], 16),
                          'range_update_pending': range_pending, 'eligibility_reason': reason,
                          'next_keeper_check_at': None, 'expected_execution_at': None,
                          'schedule_source': 'unavailable', 'explanation': timing},
            'warnings': warnings, 'reprepare_on_position_or_range_change': True}
