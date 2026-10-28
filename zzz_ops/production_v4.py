"""Explicit schema-6 holder-exit inventory. Offline consistency, never approval.

Historical schema-5 code remains unchanged. Shared strict price/route primitives
do not reinterpret its removed custody model as this deployment's accounting.
"""
from __future__ import annotations
import copy
import time
from zzz_ops import production_v2 as V
from zzz_ops.abi import keccak256

ZERO, ZERO_HASH = V.ZERO, V.ZERO_HASH
SCHEMA_NAME = 'ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5'
SCHEMA_HASH = '0x'+keccak256(SCHEMA_NAME.encode()).hex()
MODULES = V.MODULES
HELPERS = V.LP_ONLY_HELPERS + ('balancing_router','rebalance_confirmation')
VERSIONS = dict(schema_version=6, accounting_version=4, governance_version=2,
    fee_intake_version=1, custody_version=3, routing_version=2, pricing_version=2,
    review_policy_version=1, range_policy_version=1, maintenance_policy_version=2,
    compound_capability_version=3, lp_routing_version=1, execution_quality_version=1,
    mint_integration_version=1,rebalance_confirmation_version=1)
TOP_FIELDS = set(V.TOP_FIELDS) | set(VERSIONS) | {'canonical_schema'}
CHAIN_FIELDS = (set(V.CHAIN_FIELDS)-{'custody'}) | {'holder_exit','lp_execution','maintenance','rebalance_confirmation'}
EVIDENCE = tuple(name for name in V.EVIDENCE if name != 'custody_handoff') + ('holder_return',)
SERVICE_PROFILES = dict(rpc='eip1898_hash_pinned_debug_trace',pricing='independent_dual_usd_v2',
    randomness='verified_coordinator_two_words',keeper='accounting4_upkeep2_compound3_lp1_quality1_confirmation1',
    api='accounting4_custody3_holder_exit_v5_confirmation1',metadata='content_addressed_v2',opensea='primary_mint_current_nft')


def expected_bindings(chain):
    """Code-owned current getters; no retired recipient or royalty custody read."""
    result = V.expected_bindings(chain,range_policy_version=1,fee_intake_version=1)
    m = lambda role: V._obj(V._obj(chain.get('modules')).get(role)).get('address')
    h = lambda role: V._obj(V._obj(chain.get('helpers')).get(role)).get('address')
    d = lambda role: V._obj(V._obj(chain.get('dependencies')).get(role)).get('address')
    quality = V._obj(chain.get('lp_execution'))
    result['modules']['access'].pop('paused')  # Dynamic pause belongs in the observed lifecycle.
    result['modules']['vault']['ACCOUNTING_VERSION'] = 4
    result['modules']['migration']['CUSTODY_VERSION'] = 3
    result['modules']['migration'].update(MAX_BATCH=32,PAYOUT_GAS=180000)
    result['modules']['canonical']['SCHEMA'] = SCHEMA_HASH
    result['helpers']['royalty_rewards'].pop('custodyCount')
    result['modules']['pools']['configurationRevision'] = quality.get('registry_configuration_revision')
    result['modules']['liquidity'].update(LP_ROUTING_VERSION=1,EXECUTION_QUALITY_VERSION=1,balancingRouter=h('balancing_router'))
    result['modules']['strategy'].update(MAINTENANCE_POLICY_VERSION=2,EXECUTION_QUALITY_VERSION=1,
        MAX_ADDITIONAL_LOSS_BPS=1000,additionalLossBps=quality.get('additional_loss_bps'),
        executionQualityRevision=quality.get('quality_policy_revision'),REBALANCE_CONFIRMATION_VERSION=1,
        rebalanceConfirmation=h('rebalance_confirmation'))
    result['helpers']['migration_budget'].update(IDLE_COMPOUNDING_VERSION=3,REBALANCE_CONFIRMATION_VERSION=1)
    result['helpers']['balancing_router'] = dict(access=m('access'),liquidityManager=m('liquidity'),
        poolManager=d('pool_manager'),stateView=d('state_view'),LP_ROUTING_VERSION=1,
        EXECUTION_QUALITY_VERSION=1,MAX_EXECUTION_POOLS=4,MAX_ADDITIONAL_LOSS_BPS=1000,
        additionalLossBps=quality.get('additional_loss_bps'),executionRevision=quality.get('execution_revision'),
        searchIterations=quality.get('search_iterations'),quoteGasLimit=quality.get('quote_gas_limit'))
    confirmation=V._obj(chain.get('rebalance_confirmation'))
    result['helpers']['rebalance_confirmation']=dict(access=m('access'),strategy=m('strategy'),
        REBALANCE_CONFIRMATION_VERSION=1,duration=confirmation.get('duration'),maxObservationGap=confirmation.get('max_observation_gap'),
        policyRevision=confirmation.get('policy_revision'),reviewHash=confirmation.get('review_hash'))
    return result


def execution_expected(chain):
    q = V._obj(chain.get('lp_execution'))
    h = V._obj(chain.get('helpers')); m = V._obj(chain.get('modules'))
    return dict(version=1,router=V._obj(h.get('balancing_router')).get('address'),
        execution_revision=q.get('execution_revision'),registry_configuration_revision=q.get('registry_configuration_revision'),
        search_iterations=q.get('search_iterations'),quote_gas_limit=q.get('quote_gas_limit'),
        execution_pools=q.get('execution_pools'),swaps_enabled=bool(q.get('execution_pools')),
        catalog_frozen_by_wallet_review=False,execution_quality=dict(version=1,
            additional_loss_bps=q.get('additional_loss_bps'),maximum_additional_loss_bps=1000,
            policy_owner=V._obj(m.get('strategy')).get('address'),quality_policy_revision=q.get('quality_policy_revision'),
            known_pool_fees_excluded_from_additional_limit=True,policy_frozen_by_wallet_review=False))


def _anchor(g, chain, path, home, now):
    cid = g.num(chain.get('chain_id'),path+'.chain_id',1)
    g.check(type(chain.get('chain_id')) is int and cid == home == 4663,path+'.chain_id','chain.unsupported',
        'Use the reviewed Robinhood canonical chain 4663; do not relabel another chain.')
    genesis = g.hex(chain.get('genesis_hash'),path+'.genesis_hash')
    block = g.obj(chain.get('observed_block'),path+'.observed_block')
    number = g.num(block.get('number'),path+'.observed_block.number')
    digest = g.hex(block.get('hash'),path+'.observed_block.hash')
    stamp = g.num(block.get('timestamp'),path+'.observed_block.timestamp',1)
    age = g.num(chain.get('maximum_snapshot_age_seconds'),path+'.maximum_snapshot_age_seconds',1,86400)
    confirms = g.num(chain.get('minimum_confirmations'),path+'.minimum_confirmations',1,256)
    g.check(stamp is not None and age is not None and 0 <= now-stamp <= age,path+'.observed_block',
        'snapshot.stale','Collect a fresh canonical snapshot; future timestamps are invalid.','services')
    obs = g.obj(chain.get('observation'),path+'.observation')
    head = g.num(obs.get('observed_head'),path+'.observation.observed_head')
    g.check(type(obs.get('chain_id')) is int and obs.get('chain_id') == cid and obs.get('genesis_hash') == genesis and
        type(obs.get('block_number')) is int and obs.get('block_number') == number and obs.get('block_hash') == digest and
        obs.get('complete') is True and obs.get('errors') == [] and head is not None and number is not None and
        confirms is not None and head-number >= confirms,path+'.observation','observation.incomplete',
        'Resolve every read failure at the exact reviewed canonical anchor.','bindings')


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


def _pools(g,chain,path,tokens,deps):
    """Current LP1 venue bounds; schema5's old 200bps ceiling stays unchanged."""
    pools = {}; zzz = V._obj(deps.get('zzz')).get('address')
    for index,item in enumerate(g.items(chain.get('pools'),path+'.pools',16,1)):
        pp=f'{path}.pools[{index}]'; pool=g.obj(item,pp)
        c0=g.hex(pool.get('currency0'),pp+'.currency0',20,zero=True); c1=g.hex(pool.get('currency1'),pp+'.currency1',20)
        pid=g.hex(pool.get('pool_id'),pp+'.pool_id'); fee=g.num(pool.get('fee'),pp+'.fee',1,100000)
        spacing=g.num(pool.get('tickSpacing'),pp+'.tickSpacing',1,32767)
        hook=g.hex(pool.get('hooks'),pp+'.hooks',20,zero=True)
        g.check(c0 == ZERO and c1 == zzz and c0 in tokens and c1 in tokens and hook == ZERO,pp,'pool.assets',
            'Only native ETH/fixed ZZZ static hookless principal pools are supported.','native')
        if None not in (c0,c1,fee,spacing,hook):
            g.check(pid == V.identity([(c0,'address'),(c1,'address'),(fee,'uint24'),(spacing,'uint24'),(hook,'address')]),
                pp+'.pool_id','pool.identity','Use the exact immutable PoolKey hash.','routes')
        width=g.num(pool.get('rangeBps'),pp+'.rangeBps',100,5000)
        trigger=g.num(pool.get('triggerBps'),pp+'.triggerBps',100,4999)
        deviation=g.num(pool.get('maxSpotDeviationBps'),pp+'.maxSpotDeviationBps',1,500)
        slip=g.num(pool.get('maxSlippageBps'),pp+'.maxSlippageBps',1,1000)
        g.check(None not in (width,trigger,deviation,slip) and trigger < width and deviation < width,pp,'pool.guards',
            'Preserve bounded settings; movement does not authorize policy2 rebalancing.')
        interval=g.num(pool.get('minRebalanceInterval'),pp+'.minRebalanceInterval',600,604800)
        low=g.num(pool.get('minDepositUSD'),pp+'.minDepositUSD',1); high=g.num(pool.get('maxPositionUSD'),pp+'.maxPositionUSD',1)
        g.check(low is not None and high is not None and low <= 5*10**18 <= 100*10**18 <= high,pp,'pool.bounds',
            'Qualify $100 activation/$5 growth and the actual cumulative per-NFT maximum.')
        for key in ('depositsEnabled','operationsEnabled'):
            g.check(type(pool.get(key)) is bool,pp+'.'+key,'pool.mode','Record an exact boolean mode.')
        wanted={key:pool.get(key) for key in V.POOL_FIELDS}
        for key in ('minDepositUSD','maxPositionUSD'): wanted[key]=V._numeric(wanted[key])
        g.check(V._equal(pool.get('observed_config'),wanted),pp+'.observed_config','pool.observation','Compare every PoolConfig field.','bindings')
        g.check(V._equal(pool.get('observed_accounting'),dict(currency0=c0,currency1=c1)),pp,'pool.accounting','No wrapper substitution.','native')
        slot=g.obj(pool.get('slot0'),pp+'.slot0')
        price=g.num(slot.get('sqrt_price_x96'),pp+'.slot0.sqrt_price_x96',1,2**160-1)
        protocol=g.num(slot.get('protocol_fee'),pp+'.slot0.protocol_fee',0,2**24-1)
        g.check(V._consistent_slot0(price,protocol,slot,fee),pp+'.slot0','pool.state',
            'Validate actual tick/sqrt/static fee and both protocol-fee directions.','routes')
        g.num(pool.get('liquidity'),pp+'.liquidity',1,2**128-1)
        from zzz_ops.range_policy import verify
        raw=[f'{int(pool[k],16) if isinstance(pool[k],str) and pool[k].startswith("0x") else int(pool[k]):064x}' for k in V.POOL_FIELDS]
        policy=verify(pool.get('range_policy'),pool.get('observed_range_policy'),raw,chain['observed_block']['timestamp'])
        g.check(policy['orientation']==1 and policy['keeper']['enabled'] is False,pp+'.range_policy','range.manual',
            'Use explicit ZZZ-price-in-ETH orientation and operator-selected widths.','bindings')
        review=V._bound_proof(g,pool.get('review_evidence'),pp+'.review_evidence',chain,kind='principal_pool_qualification')
        g.check(review.get('configuration_sha256') == V.configuration_hash(V.pool_configuration(chain,pool)),pp,'pool.qualification_scope',
            'Bind real pool review to its complete current policy and dependency pins.','security')
        g.check(pid is not None and pid not in pools,pp+'.pool_id','pool.duplicate','Do not duplicate pool IDs.')
        if pid is not None: pools[pid]=pool
    selected=chain.get('contribution_pool')
    g.check([pid for pid,pool in pools.items() if pool.get('depositsEnabled') is True]==[selected] and
        V._obj(pools.get(selected)).get('operationsEnabled') is True,path+'.contribution_pool','pool.contribution',
        'Exactly one admitted pool may accept contributions.','routes')
    maintenance=g.obj(chain.get('maintenance'),path+'.maintenance')
    intervals=g.obj(maintenance.get('compound_intervals'),path+'.maintenance.compound_intervals')
    g.check(set(intervals)==set(pools),path+'.maintenance.compound_intervals','compound.inventory','Review every admitted pool interval.')
    for pid,interval in intervals.items(): g.num(interval,path+'.maintenance.compound_intervals.'+str(pid),600,604800)
    g.check(V._equal(maintenance.get('observed_compound_intervals'),intervals),path+'.maintenance','compound.observation',
        'Read Budget3 compoundInterval for each pool at the same block.','bindings')
    return pools


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
        path+'.lp_execution.execution_pools','execution.catalog','Review unique admitted operations-enabled venues; empty means no swaps.','routes')
    g.check(V._equal(q.get('observed'),execution_expected(chain)),path+'.lp_execution.observed','execution.observation',
        'Bind Manager/Balancer/actual Strategy capabilities, policy owner and both revisions at the canonical block.','bindings')
    V._bound_proof(g,q.get('review_evidence'),path+'.lp_execution.review_evidence',chain,kind='lp_execution_quality_qualification')


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
        g.keys(b,{'id','total_shares','position','settlement','lp_owner','lp_liquidity'},bp)
        shares=g.num(b.get('total_shares'),bp+'.total_shares'); group=g.items(b.get('position'),bp+'.position',8,8)
        if len(group)!=8: continue
        g.check(bid not in by_bucket,bp+'.id','exit.bucket_duplicate','Read every registered bucket once.');by_bucket[bid]=b
        state=group[7]; lp=group[1]
        g.check(all(type(v) is int and 0<=v<2**256 for v in group),bp+'.position','exit.position','Use exact eight-word accounting4 Position.');
        g.check(0<=group[5]<2**160 and 0<=group[6]<2**64 and group[6]<=chain['observed_block']['timestamp'],
            bp+'.position','exit.position_precision','Enforce uint160 centre/uint64 past checkpoint precision, not an arbitrary uint256 row.')
        if not shares: g.check(state==lp==group[2]==group[3]==0,bp,'exit.empty','Empty buckets cannot hide principal.')
        else: g.check(state in (1,4,5) and (state!=1 or lp>0) and (state==1 or lp==0),bp,'exit.position_state','Validate active/parked/exited physical custody.')
        if shares and phase==0:g.check(state in (1,4),bp,'exit.premature_terminal','A terminal position requires collective exit.')
        if state==1:g.check(b.get('lp_owner')==chain['modules']['vault']['address'] and type(b.get('lp_liquidity')) is int and
            0<b['lp_liquidity']<2**128,bp,'exit.lp_custody','Authenticate actual LP NFT ownership and positive uint128 liquidity.')
        else:g.check(b.get('lp_owner') is None and b.get('lp_liquidity') is None,bp,'exit.no_lp','No invented physical LP for closed/parked/empty buckets.')
        admitted={int(p['pool_id'],16) for p in chain['pools']}
        if shares:g.check(group[0] in admitted,bp,'exit.pool_identity','Registered principal must use an inventoried native ETH/ZZZ pool.')
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


def _safe(g,path,action):
    try:return action()
    except (ValueError,TypeError,KeyError,ArithmeticError,IndexError,AttributeError):
        g.check(False,path,'inventory.malformed','Resolve malformed/incomplete current-profile data; never infer missing observations.');return None


def confirmation_controls_allow(chain):
    """Raw Strategy need can remain true while lifecycle suppresses the helper."""
    holder=V._obj(V._obj(chain.get('holder_exit')).get('observed'))
    canonical=V._obj(chain.get('canonical_handoff'));governance=V._obj(chain.get('governance'))
    return (governance.get('sealed') is True and holder.get('paused') is False and
        holder.get('lp_exit_started') is False and canonical.get('preparation_active') is False and
        type(canonical.get('state')) is int and canonical.get('state')==0)


def _confirmation(g,chain,path):
    c=g.obj(chain.get('rebalance_confirmation'),path+'.rebalance_confirmation');p=path+'.rebalance_confirmation'
    g.keys(c,{'duration','max_observation_gap','policy_revision','review_hash','observed','review_evidence'},p)
    duration=g.num(c.get('duration'),p+'.duration',60,604800)
    gap=g.num(c.get('max_observation_gap'),p+'.max_observation_gap',0,302400)
    revision=g.num(c.get('policy_revision'),p+'.policy_revision',0,2**64-1)
    review=g.hex(c.get('review_hash'),p+'.review_hash')
    g.check(type(c.get('duration')) is int and type(c.get('max_observation_gap')) is int and type(c.get('policy_revision')) is int,
        p,'confirmation.type','Review exact integer duration, gap and revision.')
    g.check(duration is not None and gap is not None and 0<gap<=duration//2,p,'confirmation.unconfigured',
        'Choose and qualify the maximum observation gap explicitly; zero stops ordinary confirmation and is not release-ready.','services')
    obs=g.obj(c.get('observed'),p+'.observed')
    g.keys(obs,{'duration','max_observation_gap','policy_revision','review_hash','buckets'},p+'.observed')
    g.check(all(V._equal(obs.get(key),c.get(key)) for key in ('duration','max_observation_gap','policy_revision','review_hash')),
        p+'.observed','confirmation.policy','Compare actual helper policy/review/revision at the canonical block.','bindings')
    buckets=g.items(obs.get('buckets'),p+'.observed.buckets',4)
    wanted=V._obj(chain.get('holder_exit')).get('observed',{}).get('buckets',[])
    g.check([b.get('id') for b in buckets]==[b.get('id') for b in wanted],p,'confirmation.inventory','Observe readiness for every current registered bucket.','bindings')
    stamp=chain['observed_block']['timestamp']
    allowed=confirmation_controls_allow(chain)
    by_bucket={b.get('id'):b for b in wanted}
    for row in buckets:
        rp=p+'.observed.buckets.'+str(row.get('id'))
        g.keys(row,{'id','condition_side','condition_identity','manual','stored_identity','first_seen','last_seen','stored_side','ready','raw_needed'},rp)
        side=g.num(row.get('condition_side'),rp+'.condition_side',0,2)
        stored_side=g.num(row.get('stored_side'),rp+'.stored_side',0,2)
        identity=g.hex(row.get('condition_identity'),rp+'.condition_identity',zero=True)
        stored=g.hex(row.get('stored_identity'),rp+'.stored_identity',zero=True)
        first=g.num(row.get('first_seen'),rp+'.first_seen',0,2**64-1);last=g.num(row.get('last_seen'),rp+'.last_seen',0,2**64-1)
        for key in ('manual','ready','raw_needed'):g.check(type(row.get(key)) is bool,rp+'.'+key,'confirmation.boolean','Read canonical boolean readiness.')
        empty=stored_side==0 and stored==ZERO_HASH and first==last==0
        initialized=stored_side in (1,2) and stored not in (None,ZERO_HASH) and first is not None and last is not None and 0<first<=last<=stamp
        g.check(empty or initialized,rp,'confirmation.observation','Validate empty or bounded monotonic observation state.')
        if allowed:
            g.check((row.get('raw_needed') is False and side==0 and identity==ZERO_HASH and row.get('manual') is False) or
                (row.get('raw_needed') is True and ((row.get('manual') is True and side==0 and identity==ZERO_HASH) or
                (row.get('manual') is False and side in (1,2) and identity not in (None,ZERO_HASH)))),
                rp,'confirmation.condition','Operating raw eligibility requires an ordinary identified side or the deliberate manual exception.')
        else:
            g.check(side==0 and identity==ZERO_HASH and row.get('manual') is False and row.get('ready') is False,
                rp,'confirmation.lifecycle','Pause, preparation, unsealed or terminal lifecycle suppress helper conditions and readiness, not stored history or raw Strategy need.')
        if row.get('raw_needed') is True:
            b=V._obj(by_bucket.get(row.get('id')));position=b.get('position',[])
            pool=next((c for c in chain['pools'] if len(position)==8 and int(c['pool_id'],16)==position[0]),{})
            g.check(len(position)==8 and position[7]==1 and position[1]>0 and position[5]>0 and
                pool.get('operationsEnabled') is True and type(pool.get('minRebalanceInterval')) is int and
                position[6]+pool['minRebalanceInterval']<=stamp,
                rp,'confirmation.raw_position','Raw need requires active positive LP/centre, enabled operations and the actual elapsed hard cooldown.')
        if row.get('manual'):g.check(side==0 and row.get('raw_needed') is True,rp,'confirmation.manual','Manual range exception retains every raw on-chain guard.')
        expected_ready=allowed and row.get('raw_needed') is True and (row.get('manual') is True or
            (initialized and duration is not None and gap is not None and gap>0 and side!=0 and
            side==stored_side and identity==stored and stamp-first>=duration and stamp-last<=gap))
        g.check(row.get('ready') is expected_ready,rp,'confirmation.ready_view','Independently recompute sampled confirmation readiness; this is not continuous-price proof.')
        if row.get('ready'):
            g.check(row.get('raw_needed') is True,rp,'confirmation.raw_required','Confirmation cannot bypass raw cooldown/range/price eligibility.')
            if not row.get('manual'):
                g.check(initialized and duration is not None and gap is not None and gap>0 and side==stored_side and identity==stored and
                    stamp-first>=duration and stamp-last<=gap,rp,'confirmation.readiness',
                    'Ordinary readiness requires current-side/identity agreement, elapsed buffer and fresh bounded observations.')
    V._bound_proof(g,c.get('review_evidence'),p+'.review_evidence',chain,kind='observed_rebalance_confirmation_qualification')


def validate(config, *, expected_commit=None, now=None):
    """Current profile only. Unsupported OpenSea code always remains a blocker."""
    cfg=copy.deepcopy(config) if isinstance(config,dict) else {};g=V.Gate(cfg.get('release_commit'))
    g.commit=g.hex(g.commit,'release_commit',20,prefix=False)
    for key,value in VERSIONS.items():g.check(type(cfg.get(key)) is int and cfg.get(key)==value,key,'schema.unsupported','Use the explicit schema6/accounting4/custody3/V5 current capabilities.')
    g.check(cfg.get('canonical_schema')==SCHEMA_NAME,'canonical_schema','schema.canonical','Do not reinterpret an earlier canonical schema.')
    g.check(set(cfg)-{'_notes'}==TOP_FIELDS,'config','schema.keys','Use exact schema6 fields; no removed custody recipient or bridge inventory.')
    if expected_commit is not None:g.check(g.commit==expected_commit,'release_commit','commit.mismatch','Use the exact independently reviewed source revision.')
    home=g.num(cfg.get('canonical_chain_id'),'canonical_chain_id',1)
    g.check(cfg.get('accounting_model')=='shared-pools-native-v4' and cfg.get('custody_architecture')=='collective-holder-return-v3',
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
    chains=g.items(cfg.get('chains'),'chains',1,1)
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
        _safe(g,path+'.rebalance_confirmation',lambda:_confirmation(g,chain,path))
        _safe(g,path+'.release',lambda:_release_records(g,chain,path,home,tokens))
        _safe(g,path+'.mint',lambda:V._mint_integration(g,chain,path))
    # A schema6 manifest cannot manufacture the missing primary-mint interface.
    if not any(i['code']=='mint.opensea_unsupported' for i in g.issues):
        g.check(False,'services.opensea','mint.opensea_unsupported','Current direct mint is not OpenSea primary-drop integration.','services')
    groups={}
    for issue in g.issues:groups.setdefault(issue['group'],[]).append(issue)
    return dict(schema_version=6,status='blocked',ready=False,deployment_authorized=False,current_release_gate=True,
        inventory_profile_supported=True,production_qualification_supported=False,release_commit=g.commit,
        inventory_consistent=not any(i['code']!='mint.opensea_unsupported' for i in g.issues),issues=g.issues,blockers=groups,
        opensea_primary_mint_supported=False,primary_mint_implementation=V.MINT_IMPLEMENTATION_PROFILE,
        protocol_bridge_enabled=False,external_custody_exit_supported=False,collective_holder_return_supported=True,
        limitations=['Read observations and offline consistency cannot authenticate providers, evidence or independent review.',
            'No result authorizes deployment, sealing, signing, service rollout or transactions.',
            'Historical schema5/accounting3 remains explicit historical inspection; no deployment or journal migration.'])


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
    native=dict(version=4,asset=ZERO,decimals=18,runtime_hash=None,canonical_schema=SCHEMA_HASH,
        wrapper_independent=True,eth_weth_principal_boundary=False,legacy_v1_import=False)
    g.check(V._equal(chain.get('native_accounting'),native),path+'.native_accounting','native.profile','Use exact accounting4 native identity/canonical V5.')
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


def governance_configuration(chain):
    gov=V._obj(chain.get('governance'))
    return dict(chain_id=chain.get('chain_id'),controller=V._obj(chain['modules'].get('access')).get('address'),
        policy={key:gov.get(key) for key in ('multisig','signers','threshold','keeper','guardian','sealed','bootstrap')})


def _authority(g,chain,path):
    gov=g.obj(chain.get('governance'),path+'.governance')
    address=g.hex(gov.get('multisig'),path+'.governance.multisig',20)
    signers=[g.hex(v,path+'.governance.signers',20) for v in g.items(gov.get('signers'),path+'.governance.signers',64,1)]
    g.check(len(set(signers))==len(signers),path+'.governance','authority.duplicate','Review distinct signers and threshold; one human operator is allowed.')
    g.num(gov.get('threshold'),path+'.governance.threshold',1,len(signers))
    keeper=g.hex(gov.get('keeper'),path+'.governance.keeper',20);guardian=g.hex(gov.get('guardian'),path+'.governance.guardian',20)
    expected=dict(governance=address,pending_governance=ZERO,keeper=keeper,keeper_enabled=True,guardian=guardian,guardian_enabled=True)
    g.check(V._equal(gov.get('observed_roles'),expected),path+'.governance.observed_roles','authority.observation','Observe actual direct governance and limited grants.','authorities')
    g.check(not {'proposers','executors','timelock_seconds','controller_admin'} & set(gov),path+'.governance','authority.retired_roles','Do not add timelock roles.')
    g.check(gov.get('sealed') is True and gov.get('bootstrap')==ZERO and gov.get('role_history_complete') is True,path+'.governance','authority.seal','Verify seal/bootstrap and full role history.')
    if keeper in (address,guardian) or guardian==address:g.text(gov.get('overlap_review'),path+'.governance.overlap_review')
    p=V._bound_proof(g,gov.get('review_evidence'),path+'.governance.review_evidence',chain,kind='immediate_governance_review')
    g.check(p.get('configuration_sha256')==V.configuration_hash(governance_configuration(chain)) and all(p.get(k) is True for k in
        ('no_notice_risk_accepted','loss_limit_authority_reviewed','all_roles_inventoried')),path+'.governance','authority.trust','Review immediate bounded governance and actual signature/role policy.','authorities')


def _nft(g,chain,path,tokens):
    """Reuse current draw/content/VRF checks, with explicit custody3 asset semantics."""
    # Common checks are source-copied to keep historical validator behavior fixed.
    np=path+'.nft_inventory';nft=g.obj(chain.get('nft_inventory'),np);ctor=V._obj(chain.get('constructor'))
    bindings=g.obj(nft.get('observed_bindings'),np+'.observed_bindings')
    royalty=chain['helpers']['royalty_rewards']['address'];nft_address=chain['modules']['nft']['address']
    g.check(bindings.get('royaltyReceiver')==royalty and type(bindings.get('royaltyBps')) is int and bindings.get('royaltyBps')==500,np,'nft.royalty_receiver','ERC2981 points to the royalty ledger at5%, not an operator.')
    minted=g.num(bindings.get('mintedCount'),np+'.mintedCount',0,1000);cursor=g.num(bindings.get('nextToFinalize'),np+'.nextToFinalize',1,1001)
    remaining=g.num(bindings.get('remainingToReveal'),np+'.remainingToReveal',0,1000)
    quotas=g.items(bindings.get('rarityRemaining'),np+'.rarityRemaining',3,3)
    g.check(None not in (minted,cursor,remaining) and cursor<=minted+1 and remaining==1001-cursor and len(quotas)==3 and
        all(type(v) is int and 0<=v<=bound for v,bound in zip(quotas,(600,300,100))) and sum(quotas)==remaining,np,'nft.draw_accounting','Preserve ordered exact-quota inventory.')
    g.check(minted==V._obj(chain['holder_exit'].get('observed')).get('minted_count'),np,'nft.inventory_match','NFT and holder inventory share the same count.')
    import re
    base=ctor.get('nft_base_uri');art=g.obj(nft.get('artwork_publication'),np+'.artwork_publication')
    g.check(isinstance(base,str) and re.fullmatch(r'(?:ipfs://(?:Qm[1-9A-HJ-NP-Za-km-z]{44}|b[a-z2-7]{20,})|ar://[A-Za-z0-9_-]{43})/(?:[^\s"<>]*/)?',base) is not None,np,'artwork.content_addressed','Use a reviewed immutable content root.')
    paths=g.items(art.get('asset_paths'),np+'.artwork_publication.asset_paths',len(V.ARTWORK_FILES),len(V.ARTWORK_FILES))
    digest=g.hex(art.get('manifest_sha256'),np+'.artwork_publication.manifest_sha256',prefix=False)
    g.check(art.get('base_uri')==base and art.get('asset_count')==len(V.ARTWORK_FILES) and all(isinstance(v,str) for v in paths) and
        len(set(paths))==len(paths) and set(paths)==set(V.ARTWORK_FILES),np,'artwork.inventory','Publish exactly the prepared2784 states.')
    p=g.proof(art.get('review_evidence'),np+'.artwork_publication.review_evidence',independent=True,kind='content_addressed_artwork_review')
    g.check(p.get('base_uri')==base and p.get('asset_manifest_sha256')==digest,np,'artwork.review','Bind content review to root and manifest.')
    vrf=g.obj(nft.get('randomness'),np+'.randomness');coordinator,_=V._runtime(g,dict(vrf,address=vrf.get('coordinator')),np+'.randomness')
    key=g.hex(vrf.get('keyHash'),np+'.randomness.keyHash');subscription=g.num(vrf.get('subscriptionId'),np+'.randomness.subscriptionId',1)
    confirms=g.num(vrf.get('requestConfirmations'),np+'.randomness.requestConfirmations',3,200);gas=g.num(vrf.get('callbackGasLimit'),np+'.randomness.callbackGasLimit',200000,10000000)
    g.check(type(vrf.get('nativePayment')) is bool and vrf.get('immutable_provider_configuration') is True and
        vrf.get('mutable_request_parameters')==['requestConfirmations','callbackGasLimit'] and vrf.get('no_admin_reroll') is True and 'immutable_configuration' not in vrf,np,'randomness.policy','Provider/lane/subscription stay immutable; no reroll.')
    review=g.proof(vrf.get('review_evidence'),np+'.randomness.review_evidence',independent=True,kind='verified_randomness_coordinator_review')
    integration=V._bound_proof(g,vrf.get('integration_evidence'),np+'.randomness.integration_evidence',chain,kind='coordinator_staged_randomness')
    for record in (review,integration):g.check(record.get('chain_id')==chain.get('chain_id') and record.get('coordinator')==coordinator and
        record.get('nft')==nft_address and record.get('keyHash')==key and record.get('subscriptionId')==subscription and record.get('nativePayment') is vrf.get('nativePayment'),np,'randomness.scope','Qualify actual coordinator, consumer, lane and payment mode.')
    g.check(confirms is not None and gas is not None and integration.get('requestConfirmations')==confirms and integration.get('callbackGasLimit')==gas and
        integration.get('original_request_recovery_tested') is True and V._numeric(integration.get('fulfilled_request_id')) not in (None,0) and
        V._numeric(integration.get('finalized_token_id')) not in (None,0),np,'randomness.integration','Retain actual original-request fulfillment/recovery evidence.')
    V._ledger_assets(g,chain,path+'.reward_assets',chain.get('reward_assets'),tokens,33)
    inv=g.obj(nft.get('royalty_assets'),np+'.royalty_assets');entries=g.items(inv.get('assets'),np+'.royalty_assets.assets',17,1)
    g.check(type(inv.get('asset_count')) is int and inv.get('asset_count')==len(entries) and inv.get('observed_asset_count')==len(entries) and inv.get('complete_admission_history') is True,np,'royalty.assets_complete','Read the exact admitted currency inventory.')
    seen=set()
    for i,asset in enumerate(entries):
        address=g.hex(asset.get('address'),np+'.royalty_assets.address',20,zero=True)
        g.check(address in tokens and address not in seen and (i!=0 or address==ZERO) and asset.get('observed_asset')==address and
            asset.get('observed_is_asset') is True and 'custody_amount' not in asset,np,'royalty.asset','No retired external custody ledger; preserve exact admitted currencies.');seen.add(address)
        p=g.proof(asset.get('review_evidence'),np+'.royalty_assets.review_evidence',independent=True)
        g.check(p.get('outage_isolation_reviewed') is True and p.get('old_receipts_preserved') is True,np,'royalty.outage','Review failure isolation and earlier cohorts.')
        routes=chain.get('_validated_routes',{})
        g.check(address==ZERO and asset.get('strategy')=='native' or address!=ZERO and asset.get('strategy')=='convert_to_eth' and any(
            role=='royalty' and r.get('enabled') is True and r.get('source_asset')==address for (role,_),r in routes.items()),np,'royalty.route','Qualify actual optional-currency ETH conversion; no arbitrary custody recovery.')
