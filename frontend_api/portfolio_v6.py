"""Fresh accounting6 portfolio authentication at one caller-pinned block.

Historical profiles never enter this adapter. No cached latest state, inferred
second leg, synthetic value or transaction submission is introduced here.
"""
from frontend_api.service import ProjectionError, _address_word
from zzz_ops.abi import keccak256

ROLES = ('pools', 'liquidity', 'strategy', 'budget', 'portfolio_policy',
         'rebalance_confirmation', 'balancing_router', 'lp_balance_math',
         'lp_position_executor', 'protocol_policy', 'pool_manager', 'state_view', 'position_manager', 'permit2')


def verify_profile(p, block):
    pins = {role: item.address for role, item in p.contracts.items()}
    def number(role, method, *args):
        return int(p._call(pins[role], method, *args, block=block)[0], 16)
    def binding(role, method, expected):
        if _address_word(p._call(pins[role], method, block=block)[0]) != pins[expected]:
            raise ProjectionError('Accounting6 portfolio helper binding differs')
    for role, label in (('pools', 'ZZZPoolRegistry'), ('liquidity', 'ZZZLiquidityManager'), ('strategy', 'ZZZStrategy')):
        binding(role, 'access()', 'access')
        if number('access', 'module(bytes32)', '0x'+keccak256(label.encode()).hex()) != int(pins[role], 16):
            raise ProjectionError('Accounting6 portfolio module differs from the sealed controller')
    for role in ('budget', 'portfolio_policy', 'rebalance_confirmation', 'balancing_router', 'lp_position_executor'):
        binding(role, 'access()', 'access')
    for role, method, expected in (
            ('vault','migrationBudget()','budget'), ('budget','vault()','vault'),
            ('strategy','portfolioPolicy()','portfolio_policy'), ('portfolio_policy','strategy()','strategy'),
            ('strategy','rebalanceConfirmation()','rebalance_confirmation'), ('rebalance_confirmation','strategy()','strategy'),
            ('liquidity','balancingRouter()','balancing_router'), ('balancing_router','liquidityManager()','liquidity'),
            ('balancing_router','balanceMath()','lp_balance_math'), ('lp_balance_math','balancer()','balancing_router'),
            ('balancing_router','poolManager()','pool_manager'), ('balancing_router','stateView()','state_view'),
            ('liquidity','positionOperator()','lp_position_executor'), ('lp_position_executor','liquidityManager()','liquidity'),
            ('lp_position_executor','positionManager()','position_manager'), ('lp_position_executor','stateView()','state_view'),
            ('lp_position_executor','poolManager()','pool_manager'), ('lp_position_executor','permit2()','permit2'),
            ('lp_position_executor','balancingRouter()','balancing_router'),
            ('access','protocolPolicy()','protocol_policy'), ('protocol_policy','access()','access'),
            ('liquidity','positionManager()','position_manager'), ('liquidity','stateView()','state_view'),
            ('liquidity','poolManager()','pool_manager'), ('liquidity','permit2()','permit2'),
            ('state_view','poolManager()','pool_manager'), ('position_manager','poolManager()','pool_manager'),
            ('position_manager','permit2()','permit2')):
        binding(role, method, expected)
    for role, method, expected in (
            ('vault','ACCOUNTING_VERSION()',6), ('strategy','MAINTENANCE_POLICY_VERSION()',3),
            ('strategy','REBALANCE_CONFIRMATION_VERSION()',3), ('rebalance_confirmation','REBALANCE_CONFIRMATION_VERSION()',3),
            ('budget','IDLE_COMPOUNDING_VERSION()',4), ('budget','REBALANCE_CONFIRMATION_VERSION()',3),
            ('budget','EMERGENCY_REBALANCE_VERSION()',2), ('principal_exit','EMERGENCY_REBALANCE_VERSION()',2),
            ('liquidity','PORTFOLIO_VERSION()',2), ('strategy','PORTFOLIO_VERSION()',2), ('portfolio_policy','PORTFOLIO_VERSION()',2), ('protocol_policy','PROTOCOL_POLICY_VERSION()',1),
            ('liquidity','LP_ROUTING_VERSION()',2), ('balancing_router','LP_ROUTING_VERSION()',2),
            ('lp_balance_math','LP_BALANCE_MATH_VERSION()',1), ('lp_position_executor','LP_POSITION_EXECUTOR_VERSION()',1),
            ('liquidity','EMERGENCY_REBALANCE_VERSION()',2)):
        if number(role, method) != expected:
            raise ProjectionError('Accounting6 portfolio capability differs from the explicit profile')


def read_bucket(p, bucket, block):
    """Reuses the same read-only physical adapter as keeper diagnostics.

    It authenticates both actual LP keys, owners, ticks and nonzero liquidity,
    then verifies portfolioAmounts equals the sum of physical amounts. Mixed or
    fully converted residuals stay represented when desired mode is disabled.
    Reference-price/maintenance diagnostics are deliberately separate: a USD
    outage must not hide ownership or already-funded reward claims.
    """
    from keeper.compound_policy import observe
    pins = {role: item.address for role, item in p.contracts.items()}
    hashes = {role: item.code_hash for role, item in p.contracts.items()}
    try:
        result = observe(
            lambda target, method, *args, count: p._call(target, method, *args, block=block, words=count),
            lambda target: p.rpc.call('eth_getCode', [target, block]),
            contracts=pins, code_hashes=hashes, bucket=bucket, accounting_version=6, physical_only=True)
    except (ValueError, TypeError, KeyError) as exc:
        raise ProjectionError('Accounting6 portfolio identity or aggregate principal is inconsistent') from exc
    return {'version': 2, 'minimum_main_bps':result['minimum_main_bps'],
            'maximum_residual_bps':result['maximum_residual_bps'], 'residual_gap_spacings':result['residual_gap_spacings'], 'bucket_id':str(bucket),'pool_id':result['pool_id'],
            'main_lp_token_id': str(result['lp_token_id']),
            'secondary_lp_token_id': str(result['secondary_id']) if result['secondary_id'] else None,
            'physical_legs': [{**leg, 'lp_token_id': str(leg['lp_token_id'])} for leg in result['physical_legs']],
            'principal_amounts_raw': result['portfolio_amounts'],
            'portfolio_fingerprint': result['portfolio_fingerprint'],
            'desired_residual_enabled': result['desired_residual_enabled'],
            'configuration_pending': result['portfolio_configuration_pending'],
            'residual_side_bps': result['residual_side_bps'],
            'scope': 'Both physical LPs at the same confirmed canonical block; rewards and reserves are separate.'}


def contribution_context(p,pins,pool,bucket,position,config,header,block,*,range_policy_version,
                         range_policy,maintenance_policy_version,rebalance_confirmation_version):
    """Fresh85% trigger semantics; never reinterpret historical outside-only data."""
    from datetime import datetime,timezone
    from frontend_api.service import _bool
    from frontend_api.liquidity_context import signed_tick
    from zzz_ops.tick_math import decode_slot0
    from zzz_ops.range_policy import observe as observe_range,verify as verify_range
    from zzz_ops.rebalance_confirmation import observe as observe_confirmation
    if (range_policy_version,maintenance_policy_version,rebalance_confirmation_version)!=(1,3,3):
        raise ProjectionError('Accounting6 requires explicit range1/maintenance3/confirmation3')
    def read(role,method,*args,count=1):return p._call(pins[role],method,*args,block=block,words=count)
    try:
        spot,tick,_,_=decode_slot0(read('state_view','getSlot0(bytes32)',pool,count=4),expected_fee=int(config[2],16))
        if int(read('strategy','validatePrice(bytes32)',pool)[0],16)!=spot:
            raise ValueError('Strategy and physical pool observations differ')
        observed=observe_range(lambda method,*args,count:read('strategy',method,*args,count=count),pool)
        range_metadata=verify_range(range_policy,observed,config,header['timestamp'])
    except (ValueError,TypeError,KeyError) as exc:
        raise ProjectionError('Accounting6 confirmed price/range policy differs') from exc
    existing=position is not None and int(position[7],16)==1
    spacing=int(config[3],16);cooldown=int(config[11],16)
    portfolio=None;confirmation=None;raw=False;eligible=False;manual=False;trigger=None
    last=None;earliest=None;lp=None;reason=None
    policy_fingerprint='0x'+read('portfolio_policy','controlFingerprint(bytes32)',pool)[0]
    threshold=int(read('portfolio_policy','thresholdBps()')[0],16)
    if int(policy_fingerprint,16)==0 or not 0<threshold<=10000:
        raise ProjectionError('Accounting6 portfolio policy is missing or malformed')
    if existing:
        portfolio=read_bucket(p,bucket,block);lp=int(position[1],16)
        if portfolio['pool_id']!=pool or int(portfolio['main_lp_token_id'])!=lp:
            raise ProjectionError('Accounting6 contribution portfolio differs from its bucket')
        lower,upper=map(signed_tick,read('liquidity','ticks(uint256)',lp,count=2))
        last=int(position[6],16);earliest=last+cooldown
        if not 0<=last<=header['timestamp'] or last>=2**64:
            raise ProjectionError('Accounting6 rebalance checkpoint is invalid')
        raw=_bool(read('strategy','needsRebalance(uint256)',bucket)[0])
        manual=_bool(read('strategy','rangeUpdatePending(uint256)',bucket)[0])
        try:
            confirmation=observe_confirmation(
                lambda target,method,*args,count:p._call(target,method,*args,block=block,words=count),
                strategy=pins['strategy'],budget=pins['budget'],confirmation=pins['rebalance_confirmation'],
                access=pins['access'],bucket=bucket,timestamp=header['timestamp'],raw_eligible=raw,
                range_pending=manual,version=3,portfolio_policy=pins['portfolio_policy'],accounting_version=6)
        except (ValueError,TypeError,KeyError) as exc:
            raise ProjectionError('Accounting6 threshold evidence or cooldown is inconsistent') from exc
        eligible=confirmation['ready_at_snapshot'];trigger=bool(confirmation['physical_threshold_side'])
        execution_fingerprint='0x'+read('liquidity','executionPortfolioFingerprint(uint256)',lp)[0]
        if int(execution_fingerprint,16)==0:raise ProjectionError('Accounting6 execution portfolio identity is empty')
        portfolio['execution_portfolio_fingerprint']=execution_fingerprint
        reason='operator_geometry_update' if manual else 'threshold_distance' if trigger else None
        status='eligible_now' if eligible else 'cooldown' if not confirmation['cooldown_elapsed'] else confirmation['status']
    else:
        target=read('strategy','target(bytes32)',pool,count=3)
        lower,upper=map(signed_tick,target[:2]);status='new_position'
    if spacing<=0 or lower>=upper or lower%spacing or upper%spacing:
        raise ProjectionError('Accounting6 main range is invalid')
    in_range=lower<=tick<upper
    utc=None if earliest is None else datetime.fromtimestamp(earliest,timezone.utc).isoformat()
    if not existing:
        timing='The contribution creates the main LP. Optional residual mode applies only to a later guarded portfolio adjustment.'
    elif eligible:
        timing='The guarded portfolio adjustment is eligible; execution still awaits the keeper, persisted random delay and transaction safety checks.'
    elif confirmation['status']=='reference_disagreement':
        timing='Our pool and the independent reference do not confirm the same85%threshold side. Ordinary automatic adjustment is blocked.'
    elif not confirmation['cooldown_elapsed']:
        timing=f'Earliest cooldown completion: {utc}. Timely threshold observations may accumulate before that time; confirmation and execution checks still apply.'
    elif confirmation['status']=='threshold_not_met':
        timing='The main has not crossed the configured centre-to-boundary price threshold; no ordinary portfolio adjustment is due.'
    elif confirmation['status']=='unconfigured':
        timing='The sampled-confirmation policy is unconfigured or stopped; ordinary adjustment cannot proceed.'
    elif confirmation['status']=='observation_stale':
        timing='The maximum confirmed observation gap was exceeded; sampled confirmation must restart.'
    else:
        remaining=confirmation.get('seconds_remaining')
        timing=('Timely sampled threshold observations are required before adjustment. '+
                (f'At least {remaining} seconds remain. ' if remaining is not None else '')+
                'This does not prove uninterrupted price history or promise an execution time.')
    warnings=[]
    if not in_range:
        warnings.append({'code':'LP_OUT_OF_RANGE','message':'The main LP is outside its trading range. '+timing+
            ' Funded claims and activated-NFT royalty eligibility remain unchanged.'})
    elif existing and (trigger or manual):
        warnings.append({'code':'PORTFOLIO_ADJUSTMENT_PENDING','message':timing+' Reprepare if the physical portfolio or policy changes.'})
    return {'bucket_id':str(bucket),'lp_token_id':str(lp) if lp is not None else None,
        'range_basis':'existing_position' if existing else 'proposed_initial_position',
        'lower_tick':lower,'upper_tick':upper,'current_tick':tick,'sqrt_price_x96':str(spot),'in_range':in_range,
        'configured_target_half_width_bps':int(config[7],16),'maintenance_policy_version':3,
        'rebalance_confirmation_version':3,'rebalance_confirmation':confirmation,'portfolio_version':2,
        'portfolio':portfolio,'portfolio_policy_fingerprint':policy_fingerprint,
        'range_policy_version':1,'range_orientation':range_metadata['orientation'],
        'range_price_unit':'ZZZ_in_ETH','keeper_range_policy':range_metadata,
        'rebalance':{'status':status,'eligible_at_snapshot':eligible,'raw_eligible_at_snapshot':raw,
            'last_rebalance_at':last,'cooldown_seconds':cooldown,'earliest_eligible_at':earliest,
            'earliest_eligible_utc':utc,'price_trigger_met':trigger,'trigger_bps':threshold,
            'trigger_basis':'actual_centre_to_physical_boundary_price_distance','outside_range_met':not in_range,
            'eligibility_rule':'confirmed_threshold_or_operator_geometry_update','range_update_pending':manual,
            'eligibility_reason':reason,'next_keeper_check_at':None,'expected_execution_at':None,
            'schedule_source':'unavailable','explanation':timing},
        'warnings':warnings,'reprepare_on_position_or_range_change':True}
