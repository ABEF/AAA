"""Pinned, read-only sampled confirmation observations; never a keeper schedule."""
import re
from zzz_ops.abi import address


def observe(read, *, strategy, budget, confirmation, access, bucket=None,
            timestamp=None, raw_eligible=None, range_pending=None):
    """Caller must pin every read to the same canonical block and verify code."""
    def words(target, method, *args, count=1):
        values=read(target,method,*args,count=count)
        if not isinstance(values,list) or len(values)!=count:
            raise ValueError('Malformed rebalance-confirmation result')
        if any(not isinstance(value,str) or re.fullmatch(r'[0-9a-fA-F]{64}',value) is None for value in values):
            raise ValueError('Malformed rebalance-confirmation word')
        parsed=[int(value,16) for value in values]
        if any(not 0<=value<2**256 for value in parsed):
            raise ValueError('Invalid rebalance-confirmation word')
        return parsed
    def scalar(target, method, *args):return words(target,method,*args)[0]
    def binding(target,method,expected):
        if scalar(target,method)!=int(address(expected),16):
            raise ValueError('Rebalance-confirmation binding differs')
    for target in (strategy,budget,confirmation):
        if scalar(target,'REBALANCE_CONFIRMATION_VERSION()')!=1:
            raise ValueError('Unsupported rebalance-confirmation capability')
    binding(strategy,'rebalanceConfirmation()',confirmation)
    binding(confirmation,'strategy()',strategy)
    binding(confirmation,'access()',access)
    seconds=scalar(confirmation,'duration()')
    gap=scalar(confirmation,'maxObservationGap()')
    revision=scalar(confirmation,'policyRevision()')
    review=scalar(confirmation,'reviewHash()')
    if (scalar(confirmation,'MAX_DURATION()')!=604800 or not 60<=seconds<=604800 or
            not 0<=gap<=seconds//2 or not 0<=revision<2**64 or gap and review==0):
        raise ValueError('Invalid rebalance-confirmation policy')
    result={'version':1,'helper':address(confirmation),'duration_seconds':seconds,
            'max_observation_gap_seconds':gap,'configured':gap!=0,
            'policy_revision':revision,'review_hash':'0x'+f'{review:064x}',
            'evidence_kind':'bounded_recorded_onchain_observations',
            'continuous_price_proof':False,'schedule_source':'unavailable'}
    if bucket is None:return result
    if type(bucket) is not int or not 0<bucket<2**256 or type(timestamp) is not int or timestamp<0:
        raise ValueError('Invalid rebalance-confirmation snapshot')
    if raw_eligible is None:
        raw=scalar(strategy,'needsRebalance(uint256)',bucket)
        if raw not in (0,1):raise ValueError('Invalid raw rebalance eligibility')
        raw_eligible=bool(raw)
    elif type(raw_eligible) is not bool:
        raise ValueError('Invalid raw rebalance eligibility')
    side,identity,manual=words(confirmation,'condition(uint256)',bucket,count=3)
    prior,first,last,prior_side=words(confirmation,'observations(uint256)',bucket,count=4)
    ready=scalar(confirmation,'ready(uint256)',bucket)
    strategy_ready=scalar(strategy,'rebalanceReady(uint256)',bucket)
    if (side not in (0,1,2) or manual not in (0,1) or ready not in (0,1) or
            strategy_ready!=ready or prior_side not in (0,1,2)):
        raise ValueError('Invalid rebalance-confirmation state')
    if (not raw_eligible and (side or identity or manual) or
            raw_eligible and not manual and (side==0 or identity==0) or
            manual and (not raw_eligible or side or identity) or
            range_pending is not None and (type(range_pending) is not bool or bool(manual)!=(raw_eligible and range_pending))):
        raise ValueError('Confirmation and raw rebalance conditions disagree')
    empty=prior==first==last==prior_side==0
    if not empty and (prior==0 or prior_side==0 or not 0<first<=last<=timestamp or last>=2**64):
        raise ValueError('Malformed recorded rebalance observations')
    matches=not empty and prior==identity and prior_side==side
    fresh=matches and gap!=0 and timestamp-last<=gap
    expected=bool(manual or raw_eligible and fresh and timestamp-first>=seconds)
    if bool(ready)!=expected:
        raise ValueError('Confirmation readiness contradicts its recorded observations')
    status=('manual_range_exception' if manual else 'raw_not_due' if not raw_eligible else
            'unconfigured' if gap==0 else 'waiting_first_observation' if not matches else
            'observation_stale' if not fresh else 'ready' if ready else 'confirming')
    result.update({'status':status,'ready_at_snapshot':bool(ready),'raw_eligible_at_snapshot':raw_eligible,
        'manual_range_exception':bool(manual),'exit_side':side,
        'condition_identity':'0x'+f'{identity:064x}',
        'recorded_identity':'0x'+f'{prior:064x}','first_observed_at':first or None,
        'last_observed_at':last or None,'record_matches_condition':matches,
        'observation_expires_at':last+gap if matches and gap else None,
        'earliest_confirmation_at':first+seconds if fresh else None,
        'seconds_remaining':max(first+seconds-timestamp,0) if fresh else None})
    return result
