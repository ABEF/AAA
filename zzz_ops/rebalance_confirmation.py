"""Pinned, read-only sampled confirmation observations; never a keeper schedule."""
import re
from zzz_ops.abi import address


def observe(read, *, strategy, budget, confirmation, access, bucket=None,
            timestamp=None, raw_eligible=None, range_pending=None, version=1, portfolio_policy=None,accounting_version=5):
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
    if type(version) is not int or version not in (1,2,3):raise ValueError('Unsupported confirmation profile')
    for target in (strategy,budget,confirmation):
        if scalar(target,'REBALANCE_CONFIRMATION_VERSION()')!=version:
            raise ValueError('Unsupported rebalance-confirmation capability')
    binding(strategy,'rebalanceConfirmation()',confirmation)
    binding(confirmation,'strategy()',strategy)
    binding(confirmation,'access()',access)
    if version==3:
        return _observe_portfolio(words,scalar,binding,strategy=strategy,budget=budget,
            confirmation=confirmation,access=access,bucket=bucket,timestamp=timestamp,
            raw_eligible=raw_eligible,range_pending=range_pending,policy=portfolio_policy,accounting_version=accounting_version)
    seconds=scalar(confirmation,'duration()')
    gap=scalar(confirmation,'maxObservationGap()')
    revision=scalar(confirmation,'policyRevision()')
    review=scalar(confirmation,'reviewHash()')
    if (scalar(confirmation,'MAX_DURATION()')!=604800 or not 60<=seconds<=604800 or
            not 0<=gap<=seconds//2 or not 0<=revision<2**64 or gap and review==0):
        raise ValueError('Invalid rebalance-confirmation policy')
    result={'version':version,'helper':address(confirmation),'duration_seconds':seconds,
            'max_observation_gap_seconds':gap,'configured':gap!=0,
            'policy_revision':revision,'review_hash':'0x'+f'{review:064x}',
            'evidence_kind':'bounded_recorded_onchain_observations',
            'continuous_price_proof':False,'schedule_source':'unavailable'}
    reference_required=False
    if version == 2:
        required=scalar(confirmation,'requireReferenceExit()')
        reference_review=scalar(confirmation,'referenceReviewHash()')
        if required not in (0,1) or not required and reference_review==0:
            raise ValueError('Invalid independent-reference confirmation policy')
        reference_required=bool(required)
        result.update(reference_exit_required=reference_required,reference_review_hash='0x'+f'{reference_review:064x}')
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
    reference_blocked=False
    if version == 2 and raw_eligible and not manual:
        physical,reference=words(confirmation,'marketSides(uint256)',bucket,count=2)
        if physical not in (1,2) or reference not in (0,1,2):
            raise ValueError('Invalid physical/reference exit sides')
        reference_blocked=reference_required and physical!=reference
        if side!=(0 if reference_blocked else physical):
            raise ValueError('Confirmation disagrees with independent-market evidence')
        result.update(physical_exit_side=physical,reference_exit_side=reference)
    prior,first,last,prior_side=words(confirmation,'observations(uint256)',bucket,count=4)
    ready=scalar(confirmation,'ready(uint256)',bucket)
    strategy_ready=scalar(strategy,'rebalanceReady(uint256)',bucket)
    if (side not in (0,1,2) or manual not in (0,1) or ready not in (0,1) or
            strategy_ready!=ready or prior_side not in (0,1,2)):
        raise ValueError('Invalid rebalance-confirmation state')
    if (not raw_eligible and (side or identity or manual) or
            raw_eligible and not manual and not reference_blocked and (side==0 or identity==0) or
            reference_blocked and (side!=0 or identity!=0) or
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
            'reference_disagreement' if reference_blocked else 'unconfigured' if gap==0 else 'waiting_first_observation' if not matches else
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


def _observe_portfolio(words,scalar,binding,*,strategy,budget,confirmation,access,
                       bucket,timestamp,raw_eligible,range_pending,policy,accounting_version):
    """Fresh profile3: sampled threshold can accumulate BEFORE hard cooldown.

    This is a read-only consistency projection, never a local jitter schedule.
    All callees must be runtime-authenticated and block-pinned by the caller.
    """
    if policy is None:raise ValueError('Portfolio confirmation requires the reviewed policy address')
    policy=address(policy)
    for target,method,value in ((strategy,'portfolioPolicy()',policy),
            (strategy,'access()',access),(policy,'strategy()',strategy),(policy,'access()',access),(budget,'access()',access)):
        binding(target,method,value)
    if type(accounting_version) is not int or accounting_version not in (5,6):raise ValueError('Unsupported explicit portfolio accounting')
    portfolio_version=2 if accounting_version==6 else 1
    if (scalar(policy,'PORTFOLIO_VERSION()')!=portfolio_version or scalar(strategy,'MAINTENANCE_POLICY_VERSION()')!=3 or
            scalar(budget,'IDLE_COMPOUNDING_VERSION()')!=4):
        raise ValueError('Portfolio confirmation capability differs')
    seconds=scalar(confirmation,'duration()');gap=scalar(confirmation,'maxObservationGap()')
    revision=scalar(confirmation,'policyRevision()');review=scalar(confirmation,'reviewHash()')
    threshold=scalar(policy,'thresholdBps()');portfolio_revision=scalar(policy,'revision()')
    required=scalar(confirmation,'requireReferenceExit()');reference_review=scalar(confirmation,'referenceReviewHash()')
    if (scalar(confirmation,'MAX_DURATION()')!=604800 or not 60<=seconds<=604800 or
            not 0<=gap<=seconds//2 or not 0<=revision<2**64 or gap and review==0 or
            not 0<threshold<=10000 or not 0<=portfolio_revision<2**64 or
            required not in (0,1) or not required and reference_review==0 or
            accounting_version==5 and (scalar(policy,'minimumMainBps()')!=6000 or scalar(policy,'maximumResidualBps()')!=4000)):
        raise ValueError('Invalid portfolio-confirmation policy')
    result={'version':3,'helper':address(confirmation),'duration_seconds':seconds,
        'max_observation_gap_seconds':gap,'configured':gap!=0,'policy_revision':revision,
        'review_hash':'0x'+f'{review:064x}','reference_exit_required':bool(required),
        'reference_review_hash':'0x'+f'{reference_review:064x}',
        'portfolio_version':portfolio_version,'portfolio_policy':policy,'portfolio_policy_revision':portfolio_revision,
        'threshold_bps':threshold,'threshold_basis':'ZZZ_in_ETH_actual_centre_to_physical_boundary',
        'minimum_main_bps':6000 if accounting_version==5 else None,'maximum_residual_bps':4000 if accounting_version==5 else None,
        'evidence_kind':'bounded_recorded_onchain_observations','continuous_price_proof':False,
        'schedule_source':'unavailable'}
    # Policy-only health/preflight must validate these bindings during cooldown
    # too, not defer the Budget/Vault identity until a candidate exists.
    from zzz_ops.abi import keccak256
    vault=scalar(budget,'vault()')
    if not 0<vault<2**160:raise ValueError('Invalid portfolio Vault binding')
    vault='0x'+f'{vault:040x}'
    if scalar(access,'module(bytes32)','0x'+keccak256(b'ZZZVault').hex())!=int(vault,16):
        raise ValueError('Portfolio Vault module differs')
    binding(vault,'migrationBudget()',budget)
    if scalar(access,'module(bytes32)','0x'+keccak256(b'ZZZStrategy').hex())!=int(address(strategy),16):
        raise ValueError('Portfolio Strategy module differs')
    if scalar(vault,'ACCOUNTING_VERSION()')!=accounting_version:raise ValueError('Portfolio accounting capability differs')
    if bucket is None:return result
    if type(bucket) is not int or not 0<bucket<2**256 or type(timestamp) is not int or not 0<=timestamp<2**64:
        raise ValueError('Invalid portfolio-confirmation snapshot')
    if raw_eligible is None:
        raw=scalar(strategy,'needsRebalance(uint256)',bucket)
        if raw not in (0,1):raise ValueError('Invalid raw portfolio eligibility')
        raw_eligible=bool(raw)
    elif type(raw_eligible) is not bool:raise ValueError('Invalid raw portfolio eligibility')
    # The same-block main checkpoint supplies an exact cooldown, not a guessed ETA.
    group=words(vault,'group(uint256)',bucket,count=8);pool='0x'+f'{group[0]:064x}'
    if accounting_version==6:
        minimum=scalar(policy,'minimumMainBps(bytes32)',pool);maximum=scalar(policy,'maximumResidualBps(bytes32)',pool)
        gap_spacings=scalar(policy,'residualGapSpacings(bytes32)',pool)
        if not 6000<=minimum<10000 or maximum!=10000-minimum or not 1<=gap_spacings<2**24:
            raise ValueError('Portfolio2 per-pool allocation/gap differs')
        result.update(minimum_main_bps=minimum,maximum_residual_bps=maximum,residual_gap_spacings=gap_spacings)
    registry=scalar(access,'module(bytes32)','0x'+keccak256(b'ZZZPoolRegistry').hex())
    if not 0<registry<2**160:raise ValueError('Invalid portfolio Registry binding')
    config=words('0x'+f'{registry:040x}','accounting(bytes32)',pool,count=14)
    last=group[6];interval=config[11]
    if group[7]!=1 or group[1]==0 or not 0<group[5]<2**160 or not 0<=last<=timestamp or not 600<=interval<=604800:
        raise ValueError('Invalid portfolio physical checkpoint')
    if (keccak256(bytes.fromhex(''.join(f'{value:064x}' for value in config[:5]))).hex()!=pool[2:] or
            config[0]!=0 or not 0<config[1]<2**160 or config[5] not in (0,1) or config[6]!=1):
        raise ValueError('Portfolio pool identity/operations differ')
    enabled=scalar(policy,'enabled(bytes32)',pool);pending=scalar(policy,'configurationPending(uint256)',bucket)
    geometry=scalar(policy,'geometryRevision(bytes32)',pool);applied=scalar(policy,'appliedRevision(uint256)',group[1])
    residual_side=scalar(policy,'residualSideBps(bytes32)',pool)
    if enabled not in (0,1) or pending not in (0,1) or max(geometry,applied)>=2**64:
        raise ValueError('Invalid portfolio mode/revision')
    if not 0<residual_side<=10000:raise ValueError('Invalid residual price-distance policy')
    width=scalar(strategy,'rangeUpdatePending(uint256)',bucket)
    if width not in (0,1):raise ValueError('Invalid portfolio width flag')
    manual_expected=bool(width or pending)
    fingerprint=scalar(policy,'controlFingerprint(bytes32)',pool)
    if fingerprint==0 or bool(pending)!=(geometry!=applied):
        raise ValueError('Portfolio mode/control projection differs')
    if range_pending is not None and (type(range_pending) is not bool or range_pending!=bool(width)):
        raise ValueError('Portfolio range-update projection differs')
    side,identity,manual=words(confirmation,'condition(uint256)',bucket,count=3)
    physical,reference=(0,0) if manual_expected else words(confirmation,'marketSides(uint256)',bucket,count=2)
    if physical not in (0,1,2) or reference not in (0,1,2) or manual not in (0,1):
        raise ValueError('Invalid physical/reference threshold side')
    blocked=bool(required and physical and physical!=reference)
    expected_side=0 if blocked or manual_expected else physical
    if (bool(manual)!=manual_expected or side!=expected_side or
            (side==0)!=(identity==0)):
        raise ValueError('Portfolio condition disagrees with market/policy evidence')
    cooldown=timestamp>=last+interval
    if raw_eligible!=(cooldown and (manual_expected or physical!=0)):
        # Strategy raw need deliberately does not erase a physical trigger merely
        # because reference confirmation disagrees; ready adds that requirement.
        raise ValueError('Portfolio cooldown/raw condition differs')
    prior,first,seen,prior_side=words(confirmation,'observations(uint256)',bucket,count=4)
    if prior_side not in (0,1,2) or not 0<=first<=seen<=timestamp or seen>=2**64 or (
            prior==0 and (first or seen or prior_side)) or (prior!=0 and (first==0 or prior_side==0)):
        raise ValueError('Invalid recorded portfolio observations')
    matches=side!=0 and prior==identity and prior_side==side
    fresh=bool(matches and gap and timestamp-seen<=gap)
    mature=bool(fresh and timestamp-first>=seconds)
    ready=scalar(confirmation,'ready(uint256)',bucket)
    if ready not in (0,1) or scalar(strategy,'rebalanceReady(uint256)',bucket)!=ready or bool(ready)!=(raw_eligible and (manual_expected or mature)):
        raise ValueError('Portfolio readiness differs from cooldown/recorded evidence')
    status=('manual_policy_exception' if manual_expected and cooldown else 'manual_policy_cooldown' if manual_expected else
        'reference_disagreement' if blocked else 'threshold_not_met' if not side else 'unconfigured' if gap==0 else
        'waiting_first_observation' if not matches else 'observation_stale' if not fresh else
        'confirming' if not mature else 'cooldown' if not cooldown else 'ready')
    result.update(status=status,ready_at_snapshot=bool(ready),raw_eligible_at_snapshot=raw_eligible,
        threshold_condition_at_snapshot=bool(side),physical_threshold_side=None if manual_expected else physical,
        reference_threshold_side=None if manual_expected else reference,
        threshold_observation_scope='manual_configuration_exception' if manual_expected else 'ordinary_market_threshold',
        manual_range_exception=bool(manual),configuration_pending=bool(pending),enabled=bool(enabled),
        geometry_revision=geometry,applied_revision=applied,cooldown_elapsed=cooldown,
        residual_side_bps=residual_side,
        portfolio_control_fingerprint='0x'+f'{fingerprint:064x}',
        earliest_cooldown_at=last+interval,exit_side=side,condition_identity='0x'+f'{identity:064x}',
        recorded_identity='0x'+f'{prior:064x}',recorded_side=prior_side,
        first_observed_at=first or None,last_observed_at=seen or None,
        record_matches_condition=matches,observation_expires_at=seen+gap if fresh else None,
        earliest_confirmation_at=first+seconds if fresh else None,sampled_mature=mature,
        seconds_remaining=max(first+seconds-timestamp,0) if fresh else None)
    return result
