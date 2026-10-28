"""Synthetic current-profile inventory; never live provider/authority evidence."""
import copy
from zzz_ops import production_v4 as P
from zzz_ops import production_v2 as V
from zzz_ops import production_observer as O
from zzz_ops.abi import keccak256
from zzz_ops.tick_math import sqrt_price_at_tick
from tests_python import test_production_v2 as old
from tests_python.test_production_observer import CompositionRPC, encoded, selector, CODE, RUNTIME

NOW,COMMIT=old.NOW,old.COMMIT


def fixture():
    cfg=old.range_fixture(False);cfg.update(P.VERSIONS,canonical_schema=P.SCHEMA_NAME,
        accounting_model='shared-pools-native-v4',custody_architecture='collective-holder-return-v3')
    chain=cfg['chains'][0];chain.pop('custody')
    chain['helpers'].pop('reward_receiver_factory')
    for role,number in (('activation_assets_factory',10020),('balancing_router',10021),('rebalance_confirmation',10022)):
        chain['helpers'][role]=dict(address=old.addr(number),runtime_hash=old.HASH,observed_runtime_hash=old.HASH,
            immutable=True,review_evidence=old.proof())
    for record in chain['modules'].values():record['immutable']=True
    chain['native_accounting'].update(version=4,canonical_schema=P.SCHEMA_HASH)
    gov=chain['governance']
    for key in ('proposers','executors','timelock_seconds','controller_admin'):gov.pop(key,None)
    gov['observed_roles']=dict(governance=gov['multisig'],pending_governance=P.ZERO,keeper=gov['keeper'],
        keeper_enabled=True,guardian=gov['guardian'],guardian_enabled=True)
    gov['review_evidence']['configuration_sha256']=V.configuration_hash(P.governance_configuration(chain))
    limits=chain['execution_loss_policy'];limits['contribution_bps']=200
    for source in chain['activation_sources']:source['review_evidence']['current_loss_bps']=200
    pool=chain['pools'][0];pool['minRebalanceInterval']=43200
    pool['observed_config']['minRebalanceInterval']=43200
    pool['review_evidence']['configuration_sha256']=V.configuration_hash(V.pool_configuration(chain,pool))
    chain['maintenance']=dict(compound_intervals={pool['pool_id']:3600},observed_compound_intervals={pool['pool_id']:3600})
    chain['lp_execution']=dict(execution_revision=2,registry_configuration_revision=3,quality_policy_revision=4,
        additional_loss_bps=100,search_iterations=8,quote_gas_limit=200000,execution_pools=[pool['pool_id']],
        review_evidence=old.proof(chain_id=4663,block_number=100,block_hash=old.HASH,
            deployment=chain['modules']['access']['address'],kind='lp_execution_quality_qualification'))
    chain['lp_execution']['observed']=P.execution_expected(chain)
    chain['rebalance_confirmation']=dict(duration=900,max_observation_gap=300,policy_revision=1,review_hash=old.HASH,
        review_evidence=old.proof(chain_id=4663,block_number=100,block_hash=old.HASH,deployment=chain['modules']['access']['address'],
            kind='observed_rebalance_confirmation_qualification'))
    chain['rebalance_confirmation']['observed']=dict(duration=900,max_observation_gap=300,policy_revision=1,review_hash=old.HASH,buckets=[])
    chain['holder_exit']=dict(review_evidence=old.proof(chain_id=4663,block_number=100,block_hash=old.HASH,
        deployment=chain['modules']['access']['address'],kind='collective_holder_return_qualification'),observed=dict(
            phase=0,lp_exit_started=False,paused=False,minted_count=0,exit_minted_count=0,allocation_cursor=0,
            remaining_buckets=0,remaining_eth=0,remaining_zzz=0,balance_eth=0,balance_zzz=0,
            exit_review_hash=P.ZERO_HASH,buckets=[],nfts=[],settlement_buckets=[]))
    cfg['evidence']['holder_return']=cfg['evidence'].pop('custody_handoff')
    for asset in chain['nft_inventory']['royalty_assets']['assets']:asset.pop('custody_amount',None)
    vrf=chain['nft_inventory']['randomness']
    vrf.update(request_profile=V.VRF_REQUEST_PROFILE,request_selector=V.VRF_REQUEST_SELECTOR,num_words=2,
        recovery_policy=dict(unserved_request='original_request_remains_valid',refund_or_expiry='cannot_invalidate_original_fulfillment',
            failed_callback='same_request_same_result',reroll='none'),funding=dict(source='external_subscription_reserve',owner=old.addr(9800)))
    vrf['integration_evidence'].update(recovery_request_id=1,original_result_sha256=old.SHA,recovered_result_sha256=old.SHA,
        request_selector=V.VRF_REQUEST_SELECTOR,callback_words_count=2,invalid_proof_rejection_sha256=old.SHA,
        unauthenticated_callback_rejection_sha256=old.SHA)
    for role,profile in P.SERVICE_PROFILES.items():
        chain['services'][role]['profile']=profile;chain['services'][role]['evidence']['profile']=profile
    chain['services']['opensea']['integration']=dict(requested_product='opensea_seadrop_v1',implementation_profile=V.MINT_IMPLEMENTATION_PROFILE)
    refresh_bindings(cfg)
    return cfg


def refresh_bindings(cfg):
    chain=cfg['chains'][0]
    for group,records in P.expected_bindings(chain).items():
        for role,values in records.items():
            chain[group][role]['observed_bindings']=copy.deepcopy(values)
            if group=='helpers':chain[group][role]['bindings']=copy.deepcopy(values)
    chain['observed_modules']={role:record['address'] for role,record in chain['modules'].items() if role!='access'}
    chain['observed_modules'].update({role:P.ZERO for role in V.RETIRED_MODULES})


def physical_position(pool,ticks):
    # Installed periphery1.0.3: high200 PoolId | upper24 | lower24 | subscriber8.
    words=[f'{int(pool[key],16) if isinstance(pool[key],str) else pool[key]:064x}'
        for key in ('currency0','currency1','fee','tickSpacing','hooks')]
    info=(int(pool['pool_id'],16)>>56)<<56
    info|=(ticks[0]%(2**24))<<8 | (ticks[1]%(2**24))<<32
    return dict(lp_pool_key=words,lp_position_info=f'{info:064x}')


def exited(cfg,phase=3,count=2):
    chain=cfg['chains'][0];e=chain['holder_exit']['observed'];pid=chain['pools'][0]['pool_id']
    e.update(phase=phase,lp_exit_started=True,paused=True,minted_count=count,exit_minted_count=count,
        allocation_cursor=count+1 if phase==3 else 2,remaining_buckets=0,remaining_eth=100,remaining_zzz=200,
        balance_eth=107,balance_zzz=211,exit_review_hash=old.HASH,settlement_buckets=[7])
    e['buckets']=[dict(id=7,position=[int(pid,16),0,0,0,100,2**96,NOW-50000,5],total_shares=count,
        settlement=[count,100,200,count if phase==3 else 1,100 if phase==3 else 100//count,200 if phase==3 else 200//count,True],
        lp_owner=None,lp_liquidity=None,lp_ticks=None,lp_pool_key=None,lp_position_info=None)]
    e['nfts']=[]
    for ordinal in range(1,count+1):
        allocated=phase==3 or ordinal<e['allocation_cursor']
        eth=(100*ordinal//count-100*(ordinal-1)//count) if allocated else 0
        zzz=(200*ordinal//count-200*(ordinal-1)//count) if allocated else 0
        e['nfts'].append(dict(id=100+ordinal,ordinal=ordinal,reverse_ordinal=ordinal,owner=old.addr(20000+ordinal),bucket=7,shares=1,
            eth=eth,zzz=zzz,allocated=allocated,paid=False,claimable=[eth,zzz] if phase==3 else None))
    chain['nft_inventory']['observed_bindings'].update(mintedCount=count,nextToFinalize=1,remainingToReveal=1000,rarityRemaining=[600,300,100])
    chain['rebalance_confirmation']['observed']['buckets']=[dict(id=7,condition_side=0,condition_identity=P.ZERO_HASH,manual=False,
        stored_identity=P.ZERO_HASH,first_seen=0,last_seen=0,stored_side=0,ready=False,raw_needed=False,range_pending=None)]
    return cfg


def active(cfg):
    chain=cfg['chains'][0];e=chain['holder_exit']['observed'];pid=chain['pools'][0]['pool_id']
    e['minted_count']=1
    e['buckets']=[dict(id=7,position=[int(pid,16),99,0,0,100,sqrt_price_at_tick(-10000),NOW-50000,1],total_shares=1,
        settlement=[0,0,0,0,0,0,False],lp_owner=chain['modules']['vault']['address'],lp_liquidity=100000,lp_ticks=[-14200,-3000],
        **physical_position(chain['pools'][0],[-14200,-3000]))]
    e['nfts']=[dict(id=101,ordinal=1,reverse_ordinal=1,owner=old.addr(20000),bucket=7,shares=1,eth=0,zzz=0,
        allocated=False,paid=False,claimable=None)]
    chain['nft_inventory']['observed_bindings']['mintedCount']=1
    chain['rebalance_confirmation']['observed']['buckets']=[dict(id=7,condition_side=2,condition_identity=old.HASH,
        manual=False,stored_identity=old.HASH,first_seen=NOW-900,last_seen=NOW-1,stored_side=2,ready=True,raw_needed=True,range_pending=False)]
    return cfg


class RPC(CompositionRPC):
    def __init__(self,cfg):
        super().__init__(cfg);self.expected=P.expected_bindings(self.chain);self.reorg=False;self.anchor_reads=0

    def call(self,method,params=None):
        c=self.chain;m=c['modules'];h=c['helpers'];e=c['holder_exit']['observed'];q=c['lp_execution']
        if method=='eth_getBalance':self.calls.append((method,params));return hex(e['balance_eth'])
        if method=='eth_getBlockByNumber' and params[0] not in ('latest','0x0'):
            self.anchor_reads+=1
            if self.reorg and self.anchor_reads>1:
                return dict(number=params[0],hash='0x'+'ff'*32,timestamp=hex(NOW))
        if method=='eth_call':
            target,data=params[0]['to'],params[0]['data']
            if (target,data) in self.overrides:return super().call(method,params)
            if self.bad is not None and self.bad(target,data):return super().call(method,params)
            result=None
            if target==m['access']['address']:
                if data==selector('lpExitStarted()'):result=encoded(int(e['lp_exit_started']))
                if data==selector('paused()'):result=encoded(int(e['paused']))
            if target==m['migration']['address']:
                for key,getter in (('phase','exitPhase'),('exit_minted_count','exitMintedCount'),('allocation_cursor','allocationCursor'),
                        ('remaining_buckets','remainingBuckets'),('remaining_eth','remainingETH'),('remaining_zzz','remainingZZZ'),('exit_review_hash','exitReviewHash')):
                    if data==selector(getter+'()'):result=encoded(e[key])
                if data==selector('settlementBucketCount()'):result=encoded(len(e['settlement_buckets']))
                if data[:10]==selector('settlementBucketAt(uint256)'):result=encoded(e['settlement_buckets'][int(data[10:],16)])
                if data[:10]==selector('bucketSettlement(uint256)'):
                    row=next(b for b in e['buckets'] if b['id']==int(data[10:],16));result=encoded(*[int(v) if type(v) is bool else v for v in row['settlement']])
                for row in e['nfts']:
                    if data==selector('principalOf(uint256)')+O._word(row['id']):result=encoded(row['eth'],row['zzz'],int(row['allocated']),int(row['paid']))
                    if data==selector('claimablePrincipal(uint256)')+O._word(row['id']):result=encoded(*row['claimable'])
            if target==c['dependencies']['zzz']['address'] and data==selector('balanceOf(address)')+O._word(m['migration']['address']):result=encoded(e['balance_zzz'])
            if target==c['dependencies']['position_manager']['address']:
                for row in e['buckets']:
                    if row['position'][7]==1:
                        if data==selector('ownerOf(uint256)')+O._word(row['position'][1]):result=encoded(row['lp_owner'])
                        if data==selector('getPositionLiquidity(uint256)')+O._word(row['position'][1]):result=encoded(row['lp_liquidity'])
                        if data==selector('getPoolAndPositionInfo(uint256)')+O._word(row['position'][1]):
                            result='0x'+''.join(row['lp_pool_key'])+row['lp_position_info']
            if target==m['liquidity']['address']:
                for row in e['buckets']:
                    if row['position'][7]==1 and data==selector('ticks(uint256)')+O._word(row['position'][1]):
                        result=encoded(*[tick%(2**256) for tick in row['lp_ticks']])
            if target==m['vault']['address']:
                if data==selector('MAX_BUCKETS()'):result=encoded(4)
                if data==selector('bucketCount()'):result=encoded(len(e['buckets']))
                if data[:10]==selector('bucketAt(uint256)'):result=encoded(e['buckets'][int(data[10:],16)]['id'])
                for row in e['buckets']:
                    if data==selector('group(uint256)')+O._word(row['id']):result=encoded(*row['position'])
                    if data==selector('bucketTotalShares(uint256)')+O._word(row['id']):result=encoded(row['total_shares'])
                for row in e['nfts']:
                    if data==selector('nftBucket(uint256)')+O._word(row['id']):result=encoded(row['bucket'])
                    if data==selector('sharesOf(uint256)')+O._word(row['id']):result=encoded(row['shares'])
            if target==m['nft']['address']:
                if data[:10]==selector('tokenAtOrdinal(uint256)'):result=encoded(e['nfts'][int(data[10:],16)-1]['id'])
                for row in e['nfts']:
                    if data==selector('mintOrdinalOf(uint256)')+O._word(row['id']):result=encoded(row['reverse_ordinal'])
                    if data==selector('ownerOf(uint256)')+O._word(row['id']):result=encoded(row['owner'])
            if target==h['migration_budget']['address'] and data[:10]==selector('compoundInterval(bytes32)'):
                result=encoded(c['maintenance']['compound_intervals']['0x'+data[10:]])
            if target==h['balancing_router']['address']:
                if data==selector('executionPoolCount()'):result=encoded(len(q['execution_pools']))
                if data[:10]==selector('executionPoolAt(uint256)'):result=encoded(q['execution_pools'][int(data[10:],16)])
            if target in (h['rebalance_confirmation']['address'],m['strategy']['address']):
                for row in c['rebalance_confirmation']['observed']['buckets']:
                    bid=row['id']
                    if target==m['strategy']['address'] and data==selector('needsRebalance(uint256)')+O._word(bid):result=encoded(int(row['raw_needed']))
                    if target==m['strategy']['address'] and data==selector('rebalanceReady(uint256)')+O._word(bid):result=encoded(int(row['ready']))
                    if target==m['strategy']['address'] and data==selector('rangeUpdatePending(uint256)')+O._word(bid):result=encoded(int(row['range_pending']))
                    if target==h['rebalance_confirmation']['address']:
                        if data==selector('condition(uint256)')+O._word(bid):result=encoded(row['condition_side'],row['condition_identity'],int(row['manual']))
                        if data==selector('observations(uint256)')+O._word(bid):result=encoded(row['stored_identity'],row['first_seen'],row['last_seen'],row['stored_side'])
                        if data==selector('ready(uint256)')+O._word(bid):result=encoded(int(row['ready']))
            if result is not None:self.calls.append((method,params));return result
        return super().call(method,params)
