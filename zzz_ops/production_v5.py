"""Fresh schema7: bounded main/residual custody, never deployment approval.

Common frozen primitives are reused directly; no manifest is rewritten to a
historical accounting profile to obtain a pass. Schema6 retains its own reader.
"""
from __future__ import annotations
import copy
import time
from zzz_ops import production_v2 as V
from zzz_ops import production_v4 as H
from zzz_ops.abi import keccak256
ZERO,ZERO_HASH=H.ZERO,H.ZERO_HASH
SCHEMA_NAME,SCHEMA_HASH=H.SCHEMA_NAME,H.SCHEMA_HASH
MODULES=H.MODULES
HELPERS=H.HELPERS+('portfolio_policy','lp_balance_math','lp_position_executor')
VERSIONS=dict(H.VERSIONS,schema_version=7,accounting_version=5,custody_version=4,
    maintenance_policy_version=3,compound_capability_version=4,lp_routing_version=2,
    rebalance_confirmation_version=3,emergency_rebalance_version=2,portfolio_version=1)
TOP_FIELDS=H.TOP_FIELDS|set(VERSIONS)
CHAIN_FIELDS=H.CHAIN_FIELDS|{'portfolio'}
EVIDENCE=H.EVIDENCE+('portfolio',)
SERVICE_PROFILES=dict(H.SERVICE_PROFILES,
    keeper='accounting5_portfolio1_upkeep3_compound4_lp2_quality1_confirmation3',
    api='accounting5_custody4_holder_exit_v5_portfolio1_confirmation3')
_anchor=H._anchor
_pools=H._pools
_contribution_reservation=H._contribution_reservation
_safe=H._safe
_authority=H._authority
_nft=H._nft
governance_configuration=H.governance_configuration
expected_position_ticks=H.expected_position_ticks
verify_position_identity=H.verify_position_identity
confirmation_controls_allow=H.confirmation_controls_allow


def expected_bindings(chain):
    """Explicit fresh graph; dynamic parents must resolve the sealed registry."""
    result=H.expected_bindings(chain)
    m=lambda role:V._obj(V._obj(chain.get('modules')).get(role)).get('address')
    h=lambda role:V._obj(V._obj(chain.get('helpers')).get(role)).get('address')
    d=lambda role:V._obj(V._obj(chain.get('dependencies')).get(role)).get('address')
    p=V._obj(chain.get('portfolio'))
    result['modules']['vault']['ACCOUNTING_VERSION']=5
    result['modules']['migration'].update(CUSTODY_VERSION=4,EMERGENCY_REBALANCE_VERSION=2)
    result['modules']['liquidity'].update(LP_ROUTING_VERSION=2,PORTFOLIO_VERSION=1,
        EMERGENCY_REBALANCE_VERSION=2,positionOperator=h('lp_position_executor'))
    result['modules']['strategy'].update(MAINTENANCE_POLICY_VERSION=3,REBALANCE_CONFIRMATION_VERSION=3,
        PORTFOLIO_VERSION=1,portfolioPolicy=h('portfolio_policy'))
    result['helpers']['migration_budget'].update(IDLE_COMPOUNDING_VERSION=4,REBALANCE_CONFIRMATION_VERSION=3,
        EMERGENCY_REBALANCE_VERSION=2)
    result['helpers']['balancing_router'].update(LP_ROUTING_VERSION=2,balanceMath=h('lp_balance_math'))
    result['helpers']['rebalance_confirmation']['REBALANCE_CONFIRMATION_VERSION']=3
    result['helpers']['portfolio_policy']=dict(access=m('access'),strategy=m('strategy'),PORTFOLIO_VERSION=1,
        thresholdBps=p.get('threshold_bps'),revision=p.get('policy_revision'),minimumMainBps=6000,
        maximumResidualBps=4000,DEFAULT_RESIDUAL_SIDE_BPS=5000)
    result['helpers']['lp_balance_math']=dict(balancer=h('balancing_router'),LP_BALANCE_MATH_VERSION=1)
    result['helpers']['lp_position_executor']=dict(access=m('access'),liquidityManager=m('liquidity'),
        positionManager=d('position_manager'),stateView=d('state_view'),poolManager=d('pool_manager'),
        permit2=d('permit2'),balancingRouter=h('balancing_router'),LP_POSITION_EXECUTOR_VERSION=1)
    return result


def execution_expected(chain):
    result=H.execution_expected(chain)
    result.update(version=2,portfolio_version=1,
        math_helper=V._obj(V._obj(chain.get('helpers')).get('lp_balance_math')).get('address'),
        position_executor=V._obj(V._obj(chain.get('helpers')).get('lp_position_executor')).get('address'))
    return result


def _execution(g,chain,path,pools):
    q=g.obj(chain.get('lp_execution'),path+'.lp_execution')
    g.keys(q,{'execution_revision','registry_configuration_revision','quality_policy_revision','search_iterations',
        'quote_gas_limit','additional_loss_bps','execution_pools','observed','review_evidence'},path+'.lp_execution')
    for key,lo,hi in (('execution_revision',0,2**64-1),('registry_configuration_revision',0,2**64-1),
            ('quality_policy_revision',0,2**64-1),('search_iterations',4,12),('quote_gas_limit',100000,300000),('additional_loss_bps',0,1000)):
        g.check(type(q.get(key)) is int,path+'.lp_execution.'+key,'execution.type','Use exact integer observations.')
        g.num(q.get(key),path+'.lp_execution.'+key,lo,hi)
    catalog=g.items(q.get('execution_pools'),path+'.lp_execution.execution_pools',4)
    g.check(len(set(catalog))==len(catalog) and all(pid in pools and pools[pid].get('operationsEnabled') is True for pid in catalog),
        path+'.lp_execution.execution_pools','execution.catalog','Review bounded admitted operations-enabled venues; an empty list disables swaps.','routes')
    g.check(V._equal(q.get('observed'),execution_expected(chain)),path+'.lp_execution.observed','execution.observation',
        'Bind routing2/portfolio1 Manager, fixed Balancer/math child and actual Strategy quality policy at one canonical block.','bindings')
    V._bound_proof(g,q.get('review_evidence'),path+'.lp_execution.review_evidence',chain,kind='lp_execution_quality_qualification')


def physical_amounts(price,ticks,liquidity):
    """Exact floor principal amounts, independent of Manager-reported totals."""
    from zzz_ops.tick_math import sqrt_price_at_tick,MIN_SQRT,MAX_SQRT
    if (type(price) is not int or not MIN_SQRT<=price<MAX_SQRT or type(liquidity) is not int or
            not 0<liquidity<2**128 or not isinstance(ticks,list) or len(ticks)!=2 or
            any(type(t) is not int for t in ticks) or not -887272<=ticks[0]<ticks[1]<=887272):
        raise ValueError('Invalid physical principal inputs')
    a,b=map(sqrt_price_at_tick,ticks)
    first=0 if price>=b else ((liquidity<<96)*(b-max(price,a))//b)//max(price,a)
    second=0 if price<=a else liquidity*(min(price,b)-a)//(1<<96)
    return [first,second]


def threshold_side(center,ticks,price,threshold):
    """Mirror outward-rounded ZZZ-in-ETH interpolation, never tick distance."""
    from zzz_ops.tick_math import sqrt_price_at_tick,MIN_SQRT,MAX_SQRT
    if (any(type(v) is not int for v in (center,price,threshold)) or not 0<threshold<=10000 or
            not MIN_SQRT<=price<MAX_SQRT or not isinstance(ticks,list) or len(ticks)!=2 or
            any(type(t) is not int for t in ticks) or not -887272<=ticks[0]<ticks[1]<=887272):
        raise ValueError('Invalid threshold inputs')
    a,b=map(sqrt_price_at_tick,ticks);unit=10**18
    if not a<center<b:raise ValueError('Recorded centre outside physical bounds')
    if price<=a:return 1
    if price>=b:return 2
    if price==center:return 0
    def ratio(n,d,up):
        root=(n*unit+d-1)//d if up else n*unit//d
        return (root*root+unit-1)//unit if up else root*root//unit
    if price<center:
        observed=ratio(center,price,False);edge=ratio(center,a,True)
        trigger=unit+((edge-unit)*threshold+9999)//10000
        return 1 if observed>=trigger else 0
    observed=ratio(center,price,True);edge=ratio(center,b,False)
    trigger=unit-((unit-edge)*threshold+9999)//10000
    return 2 if observed<=trigger else 0


def portfolio_fingerprints(chain,pool,legs):
    """Typed child stable identity and separate liquidity-sensitive manifest."""
    if not legs:raise ValueError('No physical main identity')
    h=chain['helpers'];d=chain['dependencies'];m=chain['modules']
    main=legs[0];aux=legs[1] if len(legs)==2 else None
    values=[(h['lp_position_executor']['address'],'address'),(d['position_manager']['address'],'address'),
        (m['vault']['address'],'address'),(pool,'bytes32'),(main['id'],'uint256'),
        (int(main['position_info'],16),'uint256'),(aux['id'] if aux else 0,'uint256'),
        (int(aux['position_info'],16) if aux else 0,'uint256')]
    stable=V.identity(values)
    execution=V.identity([(stable,'bytes32'),(main['liquidity'],'uint128'),(aux['liquidity'] if aux else 0,'uint128')])
    return stable,execution


def portfolio_control_fingerprint(chain,policy):
    p=chain['portfolio']
    return V.identity([(chain['helpers']['portfolio_policy']['address'],'address'),
        (chain['modules']['strategy']['address'],'address'),(p['policy_revision'],'uint64'),
        (policy['pool_id'],'bytes32'),(policy['enabled'],'bool'),(p['threshold_bps'],'uint16'),
        (policy['geometry_revision'],'uint64'),(policy['residual_side_bps'],'uint16'),
        (policy['mode_review_hash'],'bytes32'),(policy['residual_review_hash'],'bytes32'),
        (p['trigger_review_hash'],'bytes32')])


def _portfolio(g,chain,path):
    p=g.obj(chain.get('portfolio'),path+'.portfolio');pp=path+'.portfolio'
    declarations={'threshold_bps','policy_revision','trigger_review_hash','pools','source_check_interval_seconds'}
    g.keys(p,declarations|{'observed','review_evidence'},pp)
    threshold=g.num(p.get('threshold_bps'),pp+'.threshold_bps',1,10000)
    revision=g.num(p.get('policy_revision'),pp+'.policy_revision',0,2**64-1)
    g.hex(p.get('trigger_review_hash'),pp+'.trigger_review_hash',zero=True)
    g.check(threshold==8500 or p.get('trigger_review_hash') not in (None,ZERO_HASH),pp,
        'portfolio.trigger_review','A changed trigger requires its actual nonzero governance review.','bindings')
    g.check(type(p.get('threshold_bps')) is int and type(p.get('policy_revision')) is int,pp,'portfolio.types','Use exact uint16/uint64 policy values.')
    g.check(type(p.get('source_check_interval_seconds')) is int and p['source_check_interval_seconds']==240,
        pp,'portfolio.cadence','The fresh source checks at240seconds; this is not a receipt or uptime guarantee.','services')
    desired=g.items(p.get('pools'),pp+'.pools',16)
    wanted={pool.get('pool_id'):pool for pool in chain['pools']}
    g.check(len(desired)==len(wanted) and {r.get('pool_id') for r in desired}==set(wanted),pp,'portfolio.pool_inventory','Review every admitted pool, including disabled modes.')
    for i,row in enumerate(desired):
        rp=f'{pp}.pools[{i}]'
        g.keys(row,{'pool_id','enabled','geometry_revision','residual_side_bps','mode_review_hash','residual_review_hash'},rp)
        g.hex(row.get('pool_id'),rp+'.pool_id')
        g.check(type(row.get('enabled')) is bool,rp,'portfolio.mode','Desired mode is explicit; never infer it from a missing secondary.')
        geometry=g.num(row.get('geometry_revision'),rp+'.geometry_revision',0,2**64-1)
        residual=g.num(row.get('residual_side_bps'),rp+'.residual_side_bps',1,10000)
        for key in ('mode_review_hash','residual_review_hash'):g.hex(row.get(key),rp+'.'+key,zero=True)
        g.check(geometry is not None and revision is not None and geometry<=revision and
            (not row.get('enabled') or geometry>0) and (geometry==0 or row.get('mode_review_hash') not in (None,ZERO_HASH)) and
            (residual==5000 or row.get('residual_review_hash') not in (None,ZERO_HASH)),rp,
            'portfolio.policy_history','Review monotonic geometry/global revisions and actual nondefault-setting review hashes.','bindings')
    o=g.obj(p.get('observed'),pp+'.observed')
    g.keys(o,{'version','threshold_bps','policy_revision','trigger_review_hash','minimum_main_bps','maximum_residual_bps',
        'default_residual_side_bps','active_secondary_count','pools','buckets'},pp+'.observed')
    g.check(all(type(o.get(key)) is int and o[key]==value for key,value in
        (('version',1),('threshold_bps',threshold),('policy_revision',revision),('minimum_main_bps',6000),
         ('maximum_residual_bps',4000),('default_residual_side_bps',5000))) and
        o.get('trigger_review_hash')==p.get('trigger_review_hash'),pp,'portfolio.global_policy','Read actual fresh policy constants/trigger/revision; no default is an observation.','bindings')
    actual_pools=g.items(o.get('pools'),pp+'.observed.pools',16)
    g.check(len(actual_pools)==len(desired),pp,'portfolio.pool_observation','No omitted or duplicated observed pool policy.','bindings')
    by_pool={}
    for expected,actual in zip(desired,actual_pools):
        g.keys(actual,set(expected)|{'control_fingerprint'},pp+'.observed.pools')
        g.check(all(V._equal(actual.get(k),v) for k,v in expected.items()),pp,'portfolio.policy_observation','Observed desired policy must equal its reviewed declaration.','bindings')
        pid=actual.get('pool_id');by_pool[pid]=actual
        g.hex(actual.get('control_fingerprint'),pp+'.control_fingerprint')
        g.check(actual.get('control_fingerprint')==portfolio_control_fingerprint(chain,actual),pp,
            'portfolio.control_fingerprint','Independently encode the exact reviewed policy/geometry identity.','bindings')
    holder=chain['holder_exit']['observed']['buckets'];rows=g.items(o.get('buckets'),pp+'.observed.buckets',4)
    g.check([r.get('id') for r in rows]==[b.get('id') for b in holder],pp,'portfolio.bucket_inventory','Observe every registered physical portfolio once.','bindings')
    observations={r.get('id'):r for r in rows};ids=set();active_count=0
    for bucket in holder:
        bp=pp+'.buckets.'+str(bucket['id']);group=bucket['position'];record=V._obj(bucket.get('portfolio'))
        row=g.obj(observations.get(bucket['id']),bp)
        g.keys(row,{'id','main_id','secondary_id','applied_revision','configuration_pending'},bp)
        g.check(row.get('main_id')==group[1],bp,'portfolio.main_identity','Position remains the actual main ID, never a synthetic token.')
        if group[7]!=1:
            g.check(bucket.get('portfolio') is None and row.get('secondary_id')==0 and row.get('applied_revision') is None and
                row.get('configuration_pending') is False,bp,'portfolio.no_physical','Parked/closed/empty buckets retain no physical residual or invented revision.','bindings')
            continue
        g.keys(record,{'version','secondary_id','fingerprint','execution_fingerprint','amounts','legs'},bp+'.portfolio')
        secondary=g.num(record.get('secondary_id'),bp+'.secondary_id')
        g.check(type(record.get('version')) is int and record['version']==1 and secondary!=group[1] and
            row.get('secondary_id')==secondary,bp,'portfolio.association','Read exact main-to-secondary association; at most one residual.','bindings')
        legs=g.items(record.get('legs'),bp+'.legs',2,1)
        g.check([leg.get('id') for leg in legs]==[group[1]]+([secondary] if secondary else []),bp,'portfolio.leg_inventory','No missing, extra, duplicated or reordered physical IDs.','bindings')
        aggregate=[0,0];pool='0x'+f'{group[0]:064x}';policy=by_pool.get(pool,{})
        for n,leg in enumerate(legs):
            lp=bp+'.legs.'+str(n);g.keys(leg,{'id','owner','liquidity','ticks','pool_key','position_info','amounts'},lp)
            identifier=g.num(leg.get('id'),lp+'.id',1)
            g.check(identifier not in ids,lp,'portfolio.duplicate_id','Physical IDs cannot be reused across legs/buckets.','bindings');ids.add(identifier)
            g.check(leg.get('owner')==chain['modules']['vault']['address'],lp,'portfolio.custody','Vault must own both physical NFTs.','bindings')
            liquidity=g.num(leg.get('liquidity'),lp+'.liquidity',1,2**128-1)
            ticks=leg.get('ticks');spacing=V._obj(wanted.get(pool)).get('tickSpacing')
            g.check(isinstance(ticks,list) and len(ticks)==2 and all(type(t) is int for t in ticks) and
                -887272<=ticks[0]<ticks[1]<=887272 and type(spacing) is int and spacing>0 and all(t%spacing==0 for t in ticks),
                lp,'portfolio.ticks','Authenticate each physical range and spacing.','bindings')
            verify_position_identity(leg.get('pool_key'),leg.get('position_info'),group[0],ticks)
            price=V._numeric(V._obj(wanted.get(pool)).get('slot0',{}).get('sqrt_price_x96'))
            amounts=physical_amounts(price,ticks,liquidity)
            g.check(V._equal(leg.get('amounts'),amounts),lp,'portfolio.physical_amounts','Recompute floor principal from actual current slot0, bounds and liquidity.','bindings')
            aggregate=[a+b for a,b in zip(aggregate,amounts)]
        if legs:
            main=legs[0]
            g.check(main.get('owner')==bucket.get('lp_owner') and main.get('liquidity')==bucket.get('lp_liquidity') and
                main.get('ticks')==bucket.get('lp_ticks') and main.get('pool_key')==bucket.get('lp_pool_key') and
                main.get('position_info')==bucket.get('lp_position_info'),bp,'portfolio.main_projection','Legacy-shaped main fields must match the actual first leg.','bindings')
            stable,execution=portfolio_fingerprints(chain,pool,legs)
            g.check(record.get('fingerprint')==stable and record.get('execution_fingerprint')==execution,
                bp,'portfolio.fingerprint','Distinguish stable sample identity from liquidity-sensitive custody manifests.','bindings')
        g.check(V._equal(record.get('amounts'),aggregate) and all(value<2**256 for value in aggregate),bp,'portfolio.aggregate','Sum both physical token amounts exactly; never sum raw liquidity across different ranges.','bindings')
        applied=g.num(row.get('applied_revision'),bp+'.applied_revision',0,2**64-1)
        g.check(applied is not None and type(policy.get('geometry_revision')) is int and applied<=policy['geometry_revision'] and
            type(row.get('configuration_pending')) is bool and row['configuration_pending']==(applied!=policy.get('geometry_revision')),
            bp,'portfolio.applied_policy','Mode/geometry pending remains distinct from auxiliary presence and market price.','bindings')
        if secondary:active_count+=1
    g.check(type(o.get('active_secondary_count')) is int and 0<=o['active_secondary_count']<=4 and
        o['active_secondary_count']==active_count,pp,'portfolio.count','Cross-check the global residual count against complete bucket inventory.','bindings')
    V._bound_proof(g,p.get('review_evidence'),pp+'.review_evidence',chain,kind='bounded_portfolio_qualification')


def _confirmation(g,chain,path):
    c=g.obj(chain.get('rebalance_confirmation'),path+'.rebalance_confirmation');p=path+'.rebalance_confirmation'
    policy_keys={'duration','max_observation_gap','policy_revision','review_hash','reference_exit_required','reference_review_hash'}
    g.keys(c,policy_keys|{'observed','review_evidence'},p)
    duration=g.num(c.get('duration'),p+'.duration',60,604800);gap=g.num(c.get('max_observation_gap'),p+'.max_observation_gap',1,302400)
    g.num(c.get('policy_revision'),p+'.policy_revision',0,2**64-1);g.hex(c.get('review_hash'),p+'.review_hash')
    g.check(type(c.get('reference_exit_required')) is bool,p,'confirmation.reference_policy','Select explicit independent same-side threshold confirmation.')
    g.hex(c.get('reference_review_hash'),p+'.reference_review_hash',zero=c.get('reference_exit_required') is True)
    g.check(duration is not None and gap is not None and 240<=gap<=duration//2,p,'confirmation.cadence','Review actual600/300 initial policy and240-second source cadence; governance changes need renewed qualification.','services')
    o=g.obj(c.get('observed'),p+'.observed');g.keys(o,policy_keys|{'buckets'},p+'.observed')
    g.check(all(V._equal(o.get(k),c.get(k)) for k in policy_keys),p,'confirmation.policy','Read actual helper policy at the canonical anchor.','bindings')
    rows=g.items(o.get('buckets'),p+'.observed.buckets',4);holder=chain['holder_exit']['observed']['buckets']
    g.check([r.get('id') for r in rows]==[b.get('id') for b in holder],p,'confirmation.inventory','No omitted registered candidate.','bindings')
    by_bucket={b['id']:b for b in holder};portfolio=chain['portfolio'];policies={r['pool_id']:r for r in portfolio['observed']['pools']}
    applied={r['id']:r for r in portfolio['observed']['buckets']};stamp=chain['observed_block']['timestamp'];allowed=confirmation_controls_allow(chain)
    for row in rows:
        rp=p+'.buckets.'+str(row.get('id'))
        g.keys(row,{'id','condition_side','condition_identity','manual','stored_identity','first_seen','last_seen','stored_side',
            'ready','raw_needed','range_pending','physical_side','reference_side','reference_x96'},rp)
        side=g.num(row.get('condition_side'),rp+'.condition_side',0,2);oldside=g.num(row.get('stored_side'),rp+'.stored_side',0,2)
        identity=g.hex(row.get('condition_identity'),rp+'.condition_identity',zero=True);old=g.hex(row.get('stored_identity'),rp+'.stored_identity',zero=True)
        first=g.num(row.get('first_seen'),rp+'.first_seen',0,2**64-1);last=g.num(row.get('last_seen'),rp+'.last_seen',0,2**64-1)
        for key in ('manual','ready','raw_needed'):g.check(type(row.get(key)) is bool,rp,'confirmation.boolean','Read canonical booleans.')
        empty=old==ZERO_HASH and first==last==oldside==0
        initialized=old not in (None,ZERO_HASH) and oldside in (1,2) and first is not None and last is not None and 0<first<=last<=stamp
        g.check(empty or initialized,rp,'confirmation.observation','Stored observations are empty or strictly bounded/monotonic.')
        b=by_bucket[row['id']];group=b['position'];active=group[7]==1 and group[1]>0 and group[5]>0
        pool=next((v for v in chain['pools'] if int(v['pool_id'],16)==group[0]),{})
        pending=False;physical=0;reference=0
        if active:
            pending=b['lp_ticks']!=expected_position_ticks(pool,group[5]) or applied[row['id']]['configuration_pending']
            if not pending:
                physical=threshold_side(group[5],b['lp_ticks'],V._numeric(pool['slot0']['sqrt_price_x96']),portfolio['threshold_bps'])
            if allowed and not pending:
                price=g.num(row.get('reference_x96'),rp+'.reference_x96',1,2**160-1)
                reference=threshold_side(group[5],b['lp_ticks'],price,portfolio['threshold_bps'])
        due=bool(active and pool.get('operationsEnabled') is True and group[6]+pool['minRebalanceInterval']<=stamp and (pending or physical))
        g.check(row.get('raw_needed') is due,rp,'confirmation.raw_physical','Raw need uses85% actual price distance/explicit geometry plus hard cooldown.','bindings')
        if allowed and active:
            g.check(type(row.get('range_pending')) is bool and row['range_pending']==bool(pending),rp,'confirmation.range_pending','Manual pending includes width AND desired/applied portfolio geometry.','bindings')
            g.check(all(row.get(k) is None for k in ('physical_side','reference_side','reference_x96')) if pending else
                row.get('physical_side')==physical and type(row.get('physical_side')) is int and
                row.get('reference_side')==reference and type(row.get('reference_side')) is int,
                rp,'confirmation.market_sides','Recompute ordinary threshold sides during cooldown; a deliberate geometry repair has no fabricated threshold observation.','bindings')
            operations=pool.get('operationsEnabled') is True
            blocked=c['reference_exit_required'] and physical!=reference
            manual=bool(operations and pending)
            expected_side=0 if not operations or manual or blocked else physical
            g.check(row.get('manual') is manual and side==expected_side and (identity==ZERO_HASH)==(side==0),
                rp,'confirmation.condition','Sampling precedes cooldown; manual geometry is distinct from execution readiness.','bindings')
        else:
            g.check(side==0 and identity==ZERO_HASH and row.get('manual') is False and row.get('ready') is False,
                rp,'confirmation.lifecycle','Nonoperating/empty conditions suppress new readiness, not historical records.','bindings')
            g.check(all(row.get(k) is None for k in ('range_pending','physical_side','reference_side','reference_x96')),
                rp,'confirmation.market_scope','No invented market observation outside an active operating scope.','bindings')
        mature=initialized and side!=0 and old==identity and oldside==side and duration is not None and gap is not None and stamp-first>=duration and stamp-last<=gap
        expected=bool(allowed and due and (pending or mature))
        g.check(row.get('ready') is expected,rp,'confirmation.ready_view','Recompute sampled maturity AND hard cooldown, never uninterrupted-price proof.','bindings')
    V._bound_proof(g,c.get('review_evidence'),p+'.review_evidence',chain,kind='observed_rebalance_confirmation_qualification')

def _contracts(g, chain, path):
    expected = expected_bindings(chain); addresses = []
    for group,roles in (('modules',MODULES),('helpers',HELPERS)):
        records = g.obj(chain.get(group),path+'.'+group); g.keys(records,roles,path+'.'+group)
        for role in roles:
            rp = path+'.'+group+'.'+role; record = g.obj(records.get(role),rp)
            address,_ = V._runtime(g,record,rp)
            if address is not None: addresses.append(address)
            g.check(record.get('immutable') is True,rp+'.immutable','module.upgradeable',
                'Review the exact immutable deployment and constructor-resolved runtime.','bindings')
            g.proof(record.get('review_evidence'),rp+'.review_evidence',independent=True)
            V._bindings(g,record,expected[group][role],rp,helper=group=='helpers')
    g.check(len(addresses) == len(set(addresses)),path,'binding.alias','Modules/helpers must have distinct addresses.','bindings')
    wanted = {role:V._obj(chain['modules'].get(role)).get('address') for role in MODULES if role != 'access'}
    wanted.update({role:ZERO for role in V.RETIRED_MODULES})
    g.check(V._equal(chain.get('observed_modules'),wanted),path+'.observed_modules','binding.registry',
        'Read every canonical module and confirm all retired bridge slots are zero.','bindings')
    return addresses

def _holder_exit(g,chain,path):
    e=g.obj(chain.get('holder_exit'),path+'.holder_exit'); obs=g.obj(e.get('observed'),path+'.holder_exit.observed')
    g.keys(e,{'observed','review_evidence'},path+'.holder_exit')
    g.keys(obs,{'phase','lp_exit_started','paused','minted_count','exit_minted_count','allocation_cursor','remaining_buckets',
        'remaining_eth','remaining_zzz','balance_eth','balance_zzz','exit_review_hash','buckets','nfts','settlement_buckets'},path+'.holder_exit.observed')
    phase=g.num(obs.get('phase'),path+'.holder_exit.observed.phase',0,3)
    started=obs.get('lp_exit_started'); paused=obs.get('paused')
    g.check(type(started) is bool and type(paused) is bool and started == bool(phase),path+'.holder_exit','exit.lifecycle',
        'The irreversible Access flag and holder-return phase must agree.','bindings')
    count=g.num(obs.get('minted_count'),path+'.holder_exit.minted_count',0,1000)
    frozen=g.num(obs.get('exit_minted_count'),path+'.holder_exit.exit_minted_count',0,1000)
    cursor=g.num(obs.get('allocation_cursor'),path+'.holder_exit.allocation_cursor',0,1001)
    remaining_buckets=g.num(obs.get('remaining_buckets'),path+'.holder_exit.remaining_buckets',0,4)
    remaining_eth=g.num(obs.get('remaining_eth'),path+'.holder_exit.remaining_eth')
    remaining_zzz=g.num(obs.get('remaining_zzz'),path+'.holder_exit.remaining_zzz')
    balance_eth=g.num(obs.get('balance_eth'),path+'.holder_exit.balance_eth')
    balance_zzz=g.num(obs.get('balance_zzz'),path+'.holder_exit.balance_zzz')
    review=g.hex(obs.get('exit_review_hash'),path+'.holder_exit.exit_review_hash',zero=True)
    buckets=g.items(obs.get('buckets'),path+'.holder_exit.buckets',4)
    nfts=g.items(obs.get('nfts'),path+'.holder_exit.nfts',1000)
    g.check(count is not None and len(nfts)==count,path+'.holder_exit.nfts','exit.inventory','Observe every minted ordinal exactly once.','bindings')
    g.check(None not in (remaining_eth,remaining_zzz,balance_eth,balance_zzz) and balance_eth >= remaining_eth and balance_zzz >= remaining_zzz,
        path+'.holder_exit','exit.backing','Principal liabilities require actual ETH and fixed-ZZZ backing; prefunds may exceed liabilities.','security')
    if phase==0:
        g.check(frozen==cursor==remaining_buckets==remaining_eth==remaining_zzz==0 and review==ZERO_HASH,
            path+'.holder_exit','exit.operating','Operating mode must not contain terminal settlement accounting.')
    else:
        g.check(count==frozen and count is not None and count>0 and review not in (None,ZERO_HASH),
            path+'.holder_exit','exit.frozen_inventory','Preserve the frozen mint count and exit review.')
        g.check((phase==1 and cursor==0 and remaining_buckets is not None and remaining_buckets>0) or
            (phase==2 and remaining_buckets==0 and cursor is not None and 1<=cursor<=frozen) or
            (phase==3 and remaining_buckets==0 and cursor==frozen+1),path+'.holder_exit','exit.phase','Verify phase/cursor/count progression.')
        g.check(False,path+'.holder_exit','release.principal_exit_terminal','An exited deployment cannot be approved for new LP/mint activity.','services')
    by_bucket={}; unpaid=[0,0]; sums={}; identifiers=set(); cumulative={}; previous={}; paid_total=[0,0]
    for index,row in enumerate(buckets):
        bp=f'{path}.holder_exit.buckets[{index}]'; b=g.obj(row,bp); bid=g.num(b.get('id'),bp+'.id',1)
        g.keys(b,{'id','total_shares','position','settlement','lp_owner','lp_liquidity','lp_ticks','lp_pool_key','lp_position_info','portfolio'},bp)
        shares=g.num(b.get('total_shares'),bp+'.total_shares'); group=g.items(b.get('position'),bp+'.position',8,8)
        if len(group)!=8: continue
        g.check(bid not in by_bucket,bp+'.id','exit.bucket_duplicate','Read every registered bucket once.');by_bucket[bid]=b
        state=group[7]; lp=group[1]
        g.check(all(type(v) is int and 0<=v<2**256 for v in group),bp+'.position','exit.position','Use exact eight-word accounting5 Position.');
        g.check(0<=group[5]<2**160 and 0<=group[6]<2**64 and group[6]<=chain['observed_block']['timestamp'],
            bp+'.position','exit.position_precision','Enforce uint160 centre/uint64 past checkpoint precision, not an arbitrary uint256 row.')
        if not shares: g.check(state==lp==group[2]==group[3]==0,bp,'exit.empty','Empty buckets cannot hide principal.')
        else: g.check(state in (1,4,5) and (state!=1 or lp>0) and (state==1 or lp==0),bp,'exit.position_state','Validate active/parked/exited physical custody.')
        if shares and phase==0:g.check(state in (1,4),bp,'exit.premature_terminal','A terminal position requires collective exit.')
        if state==5:g.check(group[2]==group[3]==0,bp,'exit.terminal_idle','Exited principal cannot retain Vault idle balances.')
        if state==1:g.check(b.get('lp_owner')==chain['modules']['vault']['address'] and type(b.get('lp_liquidity')) is int and
            0<b['lp_liquidity']<2**128,bp,'exit.lp_custody','Authenticate actual LP NFT ownership and positive uint128 liquidity.')
        else:g.check(b.get('lp_owner') is None and b.get('lp_liquidity') is None,bp,'exit.no_lp','No invented physical LP for closed/parked/empty buckets.')
        admitted={int(p['pool_id'],16) for p in chain['pools']}
        if shares:g.check(group[0] in admitted,bp,'exit.pool_identity','Registered principal must use an inventoried native ETH/ZZZ pool.')
        if state==1:
            pool=next((p for p in chain['pools'] if int(p['pool_id'],16)==group[0]),{})
            ticks=b.get('lp_ticks');spacing=pool.get('tickSpacing')
            g.check(isinstance(ticks,list) and len(ticks)==2 and all(type(t) is int for t in ticks) and
                -887272<=ticks[0]<ticks[1]<=887272 and type(spacing) is int and spacing>0 and
                all(t%spacing==0 for t in ticks),bp+'.lp_ticks','exit.lp_ticks',
                'Read canonical physical Manager ticks at the same block; never infer them from target width.','bindings')
            try:
                verify_position_identity(b.get('lp_pool_key'),b.get('lp_position_info'),group[0],ticks)
                physical_identity=True
            except (ValueError,TypeError):physical_identity=False
            g.check(physical_identity,bp,'exit.lp_pool_identity',
                'Bind canonical PosM PoolKey and packed PositionInfo to the Vault pool and Manager ticks at the same block.','bindings')
        else:g.check(b.get('lp_ticks') is None and b.get('lp_pool_key') is None and b.get('lp_position_info') is None,
            bp,'exit.no_lp_ticks','Closed/parked/empty buckets have no physical LP ticks, PoolKey or PositionInfo.')
        settlement=g.items(b.get('settlement'),bp+'.settlement',7,7)
        if len(settlement)==7:
            ss,eth,zzz,allocated,ae,az,closed=settlement
            g.check(all(type(v) is int and 0<=v<2**256 for v in settlement[:-1]) and type(closed) is bool,bp,'exit.settlement','Use exact settlement integers and boolean.')
            g.check(allocated<=ss and ae<=eth and az<=zzz,bp,'exit.allocation_bounds','Allocation cannot exceed snapshotted backing.')
            if phase==0: g.check(settlement==[0,0,0,0,0,0,False],bp,'exit.preexisting_settlement','No settlement exists before exit.')
            elif shares:
                g.check(ss==shares and (closed == (state==5)),bp,'exit.closed_state','Closed settlement and terminal Vault state must agree.')
                if phase in (2,3): g.check(closed,bp,'exit.unclosed','All funded buckets must close before allocation.')
                if phase==3: g.check(allocated==ss and ae==eth and az==zzz,bp,'exit.conservation','Final cumulative allocation must conserve every raw unit.')
    for index,row in enumerate(nfts):
        np=f'{path}.holder_exit.nfts[{index}]'; n=g.obj(row,np)
        g.keys(n,{'id','ordinal','reverse_ordinal','owner','bucket','shares','eth','zzz','allocated','paid','claimable'},np)
        nid=g.num(n.get('id'),np+'.id',1); ordinal=g.num(n.get('ordinal'),np+'.ordinal',1,1000)
        g.check(nid not in identifiers and ordinal==index+1 and n.get('reverse_ordinal')==ordinal,np,'exit.nft_identity','Verify complete immutable ordinal identity.');identifiers.add(nid)
        g.hex(n.get('owner'),np+'.owner',20)
        bid=g.num(n.get('bucket'),np+'.bucket'); shares=g.num(n.get('shares'),np+'.shares')
        eth=g.num(n.get('eth'),np+'.eth'); zzz=g.num(n.get('zzz'),np+'.zzz'); allocated=n.get('allocated');paid=n.get('paid')
        g.check(type(allocated) is bool and type(paid) is bool,np,'exit.boolean','Allocation/paid flags must be booleans.')
        g.check(not paid or allocated and phase==3,np,'exit.paid','Only a ready allocated entitlement may be paid.')
        g.check(allocated or (eth==zzz==0 and paid is False),np,'exit.unallocated','Unallocated entries cannot contain principal or paid flags.')
        if ordinal is not None and phase is not None: g.check(allocated == (phase==3 or phase==2 and ordinal<cursor),np,'exit.cursor_membership','Allocation must match the frozen cursor.')
        if shares is not None and bid is not None:
            g.check((shares==0 and bid==0 and eth==zzz==0) or (shares>0 and bid in by_bucket),np,'exit.nft_bucket','Tie every positive share to its registered bucket.')
            sums[bid]=sums.get(bid,0)+shares
        if allocated and shares:
            settlement=by_bucket[bid]['settlement'];cumulative[bid]=cumulative.get(bid,0)+shares
            total=[settlement[1]*cumulative[bid]//settlement[0],settlement[2]*cumulative[bid]//settlement[0]]
            prior=previous.get(bid,[0,0])
            g.check([eth,zzz]==[total[0]-prior[0],total[1]-prior[1]],np,'exit.proportional_allocation',
                'Independently reproduce cumulative-floor apportionment in immutable mint order.')
            previous[bid]=total
        if phase==3:
            g.check(n.get('claimable')==([0,0] if paid else [eth,zzz]),np,'exit.claimable','Claimable view must match paid/allocation truth.')
        if not paid and allocated and eth is not None and zzz is not None: unpaid[0]+=eth;unpaid[1]+=zzz
        if paid and eth is not None and zzz is not None:paid_total[0]+=eth;paid_total[1]+=zzz
    for bid,b in by_bucket.items():g.check(sums.get(bid,0)==b.get('total_shares'),path+'.holder_exit','exit.share_conservation','NFT shares must sum to each bucket total.')
    if phase==3:g.check(unpaid==[remaining_eth,remaining_zzz],path+'.holder_exit','exit.unpaid_conservation','Remaining liabilities equal all unpaid NFT allocations.')
    for bid,b in by_bucket.items():
        if len(b.get('settlement',[]))==7:
            g.check(b['settlement'][3]==cumulative.get(bid,0) and b['settlement'][4:6]==previous.get(bid,[0,0]),
                path+'.holder_exit','exit.progress_conservation','Per-bucket allocation counters must match the observed NFT prefix.')
    actual_settlements=obs.get('settlement_buckets')
    wanted_settlements=[] if phase==0 else [b['id'] for b in buckets if b['total_shares']>0]
    g.check(V._equal(actual_settlements,wanted_settlements),path+'.holder_exit.settlement_buckets','exit.settlement_inventory',
        'Read every settlement bucket in registered order; no omitted or duplicate principal.')
    closed_total=[sum(b['settlement'][i] for b in buckets if b['settlement'][6]) for i in (1,2)]
    g.check([remaining_eth,remaining_zzz]==[closed_total[0]-paid_total[0],closed_total[1]-paid_total[1]],
        path+'.holder_exit','exit.receipt_conservation','Actual closed principal minus paid allocations equals remaining liabilities.')
    closed=sum(1 for b in buckets if isinstance(b,dict) and len(b.get('settlement',[]))==7 and b['settlement'][6] is True and b.get('total_shares',0)>0)
    if phase==1:g.check(remaining_buckets==sum(1 for b in buckets if b.get('total_shares',0)>0)-closed,path+'.holder_exit','exit.remaining_buckets','Read exact remaining funded bucket count.')
    V._bound_proof(g,e.get('review_evidence'),path+'.holder_exit.review_evidence',chain,kind='collective_holder_return_qualification')

def _release_records(g,chain,path,home,tokens):
    """Current authority/canonical/NFT/service qualification, without retired custody."""
    ctor=g.obj(chain.get('constructor'),path+'.constructor')
    recipient=g.hex(ctor.get('mint_proceeds_recipient'),path+'.constructor.mint_proceeds_recipient',20)
    addresses=[r.get('address') for group in ('modules','helpers') for r in V._obj(chain.get(group)).values() if isinstance(r,dict)]
    g.check(recipient is not None and recipient not in addresses,path+'.constructor','mint.recipient','Mint proceeds cannot use a protocol custody/helper address.')
    g.check(ctor.get('canonical_chain_id')==home,path+'.constructor','canonical.chain','Preserve the canonical construction chain.')
    hard=g.num(ctor.get('maximum_buyback_usd18'),path+'.constructor.maximum_buyback_usd18',1)
    operating=g.num(chain.get('operating_buyback_usd18'),path+'.operating_buyback_usd18')
    g.check(hard is not None and operating is not None and operating<=hard,path,'buyback.ceiling','Retain deployment maximum and reviewed operating ceiling.')
    g.proof(ctor.get('recipient_payment_evidence'),path+'.constructor.recipient_payment_evidence')
    native=dict(version=5,asset=ZERO,decimals=18,runtime_hash=None,canonical_schema=SCHEMA_HASH,
        wrapper_independent=True,eth_weth_principal_boundary=False,legacy_v1_import=False)
    g.check(V._equal(chain.get('native_accounting'),native),path+'.native_accounting','native.profile','Use exact accounting5 native identity/canonical V5.')
    _authority(g,chain,path)
    canonical=g.obj(chain.get('canonical_handoff'),path+'.canonical_handoff')
    g.num(canonical.get('state'),path+'.canonical_handoff.state',0,0)
    g.num(canonical.get('phase'),path+'.canonical_handoff.phase',0,5)
    g.check(type(canonical.get('state')) is int and type(canonical.get('phase')) is int,path+'.canonical_handoff','canonical.type','Lifecycle enum values are integers, never boolean aliases.')
    g.check(canonical.get('transport')=='same_chain_only' and canonical.get('remote_activation_enabled') is False and
        canonical.get('state')==0 and canonical.get('settling') is False and canonical.get('preparation_active') is False and
        canonical.get('phase') in (0,5),path+'.canonical_handoff','canonical.lifecycle','Only one active canonical deployment may operate. No remote handoff.')
    origin=g.hex(canonical.get('origin_vault'),path+'.canonical_handoff.origin_vault',20)
    g.check(canonical.get('origin_chain_id')==home,path+'.canonical_handoff','canonical.lineage','Preserve original home chain.')
    if canonical.get('phase')==0:g.check(origin==chain['modules']['vault']['address'] and canonical.get('incoming_source')==ZERO,path+'.canonical_handoff','canonical.origin','Original deployment has its own Vault origin and no predecessor.')
    else:
        p=V._bound_proof(g,canonical.get('activation_evidence'),path+'.canonical_handoff.activation_evidence',chain,kind='atomic_same_chain_canonical_activation')
        source=g.hex(canonical.get('incoming_source'),path+'.canonical_handoff.incoming_source',20)
        g.check(source!=chain['modules']['access']['address'] and p.get('source_controller')==source and p.get('source_permanently_retired') is True and
            p.get('all_backing_verified') is True and p.get('origin_vault')==origin and p.get('origin_chain_id')==home,path+'.canonical_handoff','canonical.activation','Verify funded atomic retirement/activation and exact lineage.')
    V._bound_proof(g,canonical.get('review_evidence'),path+'.canonical_handoff.review_evidence',chain,kind='native_canonical_handoff_review')
    history=g.obj(chain.get('inventory_history'),path+'.inventory_history')
    g.check(history.get('complete') is True,path+'.inventory_history','history.incomplete','Retain complete creation-to-anchor pools/routes/source/asset/role history.')
    V._bound_proof(g,history.get('evidence'),path+'.inventory_history.evidence',chain,kind='complete_deployment_inventory',exact_block=True)
    _nft(g,chain,path,tokens)
    services=g.obj(chain.get('services'),path+'.services');g.keys(services,SERVICE_PROFILES,path+'.services')
    for role,profile in SERVICE_PROFILES.items():
        sp=path+'.services.'+role;s=g.obj(services.get(role),sp)
        g.check(s.get('status')=='qualified' and s.get('profile')==profile and s.get('chain_id')==home and s.get('controller')==chain['modules']['access']['address'],sp,'service.'+role,'Qualify the exact current-profile real service and runtime/configuration.','services')
        digest=g.hex(s.get('configuration_sha256'),sp+'.configuration_sha256',prefix=False)
        p=V._bound_proof(g,s.get('evidence'),sp+'.evidence',chain,kind=role+'_production_qualification')
        g.check(digest is not None and p.get('configuration_sha256')==digest and p.get('profile')==profile,sp,'service.scope','Bind actual service evidence to exact reviewed configuration.','services')
        if role=='keeper':g.check(all(p.get(k) is True for k in ('crash_recovery_tested','off_host_backup_tested','nonce_and_pending_recovery_tested')),sp,'service.keeper_recovery','Rehearse actual process/host/signing recovery.','services')

def validate(config, *, expected_commit=None, now=None):
    """Current profile only. Unsupported OpenSea code always remains a blocker."""
    cfg=copy.deepcopy(config) if isinstance(config,dict) else {};g=V.Gate(cfg.get('release_commit'))
    g.commit=g.hex(g.commit,'release_commit',20,prefix=False)
    for key,value in VERSIONS.items():g.check(type(cfg.get(key)) is int and cfg.get(key)==value,key,'schema.unsupported','Use the explicit schema7/accounting5/custody4/portfolio1/V5 current capabilities.')
    g.check(cfg.get('canonical_schema')==SCHEMA_NAME,'canonical_schema','schema.canonical','Do not reinterpret an earlier canonical schema.')
    g.check(set(cfg)-{'_notes'}==TOP_FIELDS,'config','schema.keys','Use exact schema7 fields; no removed custody recipient or bridge inventory.')
    if expected_commit is not None:g.check(g.commit==expected_commit,'release_commit','commit.mismatch','Use the exact independently reviewed source revision.')
    home=g.num(cfg.get('canonical_chain_id'),'canonical_chain_id',1)
    g.check(cfg.get('accounting_model')=='shared-pools-native-v5' and cfg.get('custody_architecture')=='collective-holder-return-v4',
        'config','schema.architecture','Use the native holder-return model, not external custody.')
    _safe(g,'policies',lambda:V._policies(g,cfg))
    evidence=g.obj(cfg.get('evidence'),'evidence')
    for name in EVIDENCE:g.proof(evidence.get(name),'evidence.'+name)
    audit=V._obj(evidence.get('independent_audit'))
    for severity in ('critical','high'):g.num(audit.get('open_'+severity),'evidence.independent_audit.open_'+severity,0,0)
    g.check(audit.get('independent') is True and audit.get('kind')=='external_security_audit' and audit.get('open_critical')==0 and audit.get('open_high')==0,
        'evidence.independent_audit','audit.independent','Independent audit and remediation remain mandatory.','security')
    g.text(audit.get('auditor'),'evidence.independent_audit.auditor')
    tool=V._obj(evidence.get('toolchain'));gas=V._obj(evidence.get('gas_benchmarks'))
    g.check(tool.get('solidity_version')=='0.8.26' and tool.get('evm_version')=='cancun' and all(tool.get(k) is True for k in
        ('normal_size_limits','constructor_arguments_included','all_production_objects')),'evidence.toolchain','compiler.profile','Review exact normal compiler and all constructor arguments.','security')
    used=g.num(gas.get('maximum_observed_transaction_gas'),'evidence.gas_benchmarks.maximum_observed_transaction_gas',1)
    limit=g.num(gas.get('reviewed_block_gas_limit'),'evidence.gas_benchmarks.reviewed_block_gas_limit',1)
    g.check(gas.get('chain_id')==home and used is not None and limit is not None and used<limit and gas.get('complete_operating_rehearsal') is True,
        'evidence.gas_benchmarks','gas.qualification','Qualify actual current release gas, depth, batches and operation settings.','security')
    chains=g.items(cfg.get('chains'),'chains',1,1);reservation_status=None
    for index,item in enumerate(chains):
        chain=g.obj(item,f'chains[{index}]');path=f'chains[{index}]'
        g.check(set(chain)-{'_notes'}==CHAIN_FIELDS,path,'schema.keys','Use exact current chain fields; external custody is removed.')
        _safe(g,path+'.anchor',lambda:_anchor(g,chain,path,home,int(time.time()) if now is None else now))
        addresses=_safe(g,path+'.contracts',lambda:_contracts(g,chain,path)) or []
        deps=_safe(g,path+'.dependencies',lambda:V._dependencies(g,chain,path,addresses)) or {}
        tokens=_safe(g,path+'.tokens',lambda:V._tokens(g,chain,path,now,addresses)) or {}
        pools=_safe(g,path+'.pools',lambda:_pools(g,chain,path,tokens,deps)) or {}
        limits=g.obj(chain.get('execution_loss_policy'),path+'.execution_loss_policy')
        for name in ('contribution_bps','maintenance_bps','lp_conversion_bps','royalty_conversion_bps'):
            g.check(type(limits.get(name)) is int,path+'.execution_loss_policy.'+name,'loss.type','Read exact current basis points.')
            g.num(limits.get(name),path+'.execution_loss_policy.'+name,0,1000)
        g.check(limits.get('hard_maximum_bps')==1000 and limits.get('gas_separate') is True,path+'.execution_loss_policy','loss.policy','Retain hard1000bps ceilings and separate gas.')
        _safe(g,path+'.routes',lambda:V._routes(g,chain,path,tokens,deps,pools,limits,1))
        _safe(g,path+'.execution',lambda:_execution(g,chain,path,pools))
        _safe(g,path+'.holder_exit',lambda:_holder_exit(g,chain,path))
        reservation_status=_safe(g,path+'.contribution_reservation',lambda:_contribution_reservation(g,chain,path))
        _safe(g,path+'.portfolio',lambda:_portfolio(g,chain,path))
        _safe(g,path+'.rebalance_confirmation',lambda:_confirmation(g,chain,path))
        _safe(g,path+'.release',lambda:_release_records(g,chain,path,home,tokens))
        _safe(g,path+'.mint',lambda:V._mint_integration(g,chain,path))
    # A schema7 manifest cannot manufacture the missing primary-mint interface.
    if not any(i['code']=='mint.opensea_unsupported' for i in g.issues):
        g.check(False,'services.opensea','mint.opensea_unsupported','Current direct mint is not OpenSea primary-drop integration.','services')
    groups={}
    for issue in g.issues:groups.setdefault(issue['group'],[]).append(issue)
    return dict(schema_version=7,status='blocked',ready=False,deployment_authorized=False,current_release_gate=True,
        inventory_profile_supported=True,production_qualification_supported=False,release_commit=g.commit,
        inventory_consistent=not any(i['code']!='mint.opensea_unsupported' for i in g.issues),issues=g.issues,blockers=groups,
        contribution_reservation_status=reservation_status,
        opensea_primary_mint_supported=False,primary_mint_implementation=V.MINT_IMPLEMENTATION_PROFILE,
        protocol_bridge_enabled=False,external_custody_exit_supported=False,collective_holder_return_supported=True,
        limitations=['Read observations and offline consistency cannot authenticate providers, evidence or independent review.',
            'No result authorizes deployment, sealing, signing, service rollout or transactions.',
            'Historical schema6/accounting4 and older records remain explicit inspection only; no deployment or journal migration.'])
