"""Read-only schema6 observer. No historical custody, signer or pin adoption.

All state uses one canonical hash, including complete bounded holder inventory.
Actual provider latency/capacity and evidence authenticity remain qualification.
"""
from __future__ import annotations
import copy
import time
from zzz_ops import production_observer as O
from zzz_ops import production_v4 as P
from zzz_ops.lp_execution import observe as observe_execution

UINT_GETTERS = frozenset(('MAX_BATCH','PAYOUT_GAS','configurationRevision','LP_ROUTING_VERSION',
    'EXECUTION_QUALITY_VERSION','MAX_ADDITIONAL_LOSS_BPS','additionalLossBps','executionQualityRevision',
    'IDLE_COMPOUNDING_VERSION','MAX_EXECUTION_POOLS','executionRevision','searchIterations','quoteGasLimit',
    'REBALANCE_CONFIRMATION_VERSION','EMERGENCY_REBALANCE_VERSION','MAINTENANCE_POLICY_VERSION','duration','maxObservationGap','policyRevision'))
MAX_READS = 12000
MAX_SECONDS = 60


class Observer(O.Observer):
    def __init__(self,rpc,chain):
        super().__init__(rpc,chain)
        self.started=time.monotonic();self.read_count=0
        self.accounting_version=4;self.pricing_version=2;self.range_policy_version=1

    def request(self,method,params):
        if method not in O.READ_METHODS | {'eth_getBalance'}:
            raise ValueError('Only bounded inventory reads are permitted')
        self.read_count+=1
        if self.read_count>MAX_READS or time.monotonic()-self.started>MAX_SECONDS:
            raise ValueError('Current inventory observation work budget exhausted')
        result=self.rpc.call(method,params)
        if time.monotonic()-self.started>MAX_SECONDS:
            raise ValueError('Current inventory observation deadline exceeded')
        return result

    def typed(self,target,getter,expected):
        if getter in ('requireReferenceExit','emergencyActive'):return O._decode(self.read(target,getter+'()')[0],False)
        if getter in UINT_GETTERS:return O._decode(self.read(target,getter+'()')[0],0)
        if getter in ('balancingRouter','liquidityManager','rebalanceConfirmation','strategy'):return O._decode(self.read(target,getter+'()')[0],O.ZERO)
        if getter in ('reviewHash','referenceReviewHash'):return '0x'+self.read(target,getter+'()')[0]
        return super().typed(target,getter,expected)

    def governance(self):
        gov=self.chain['governance'];access=self.chain['modules']['access']['address'];observed={}
        for key,getter in (('governance','governance'),('pending_governance','pendingGovernance')):
            observed[key]=self.attempt('governance.'+key,'authority.unavailable',lambda g=getter:
                O._decode(self.read(access,g+'()')[0],O.ZERO))
        for role,getter in (('keeper','keepers'),('guardian','guardians')):
            observed[role]=gov.get(role)
            observed[role+'_enabled']=self.attempt('governance.'+role,'authority.unavailable',lambda g=getter,r=role:
                O._decode(self.read(access,g+'(address)',O._address(gov.get(r)))[0],False))
        gov['observed_roles']=observed
        wanted=dict(governance=gov.get('multisig'),pending_governance=O.ZERO,keeper=gov.get('keeper'),
            keeper_enabled=True,guardian=gov.get('guardian'),guardian_enabled=True)
        if not O._same(observed,wanted):self.errors.append(dict(path='governance',code='authority.mismatch'))

    def ledgers(self):
        # Custody3 has no custodyAmount/custodyCount royalty ledger getters.
        for name,inventory,ledger,maximum in (
                ('reward_assets',self.chain['reward_assets'],self.chain['modules']['rewards']['address'],33),
                ('royalty_assets',self.chain['nft_inventory']['royalty_assets'],self.chain['helpers']['royalty_rewards']['address'],17)):
            entries=inventory.get('assets')
            if not isinstance(entries,list) or len(entries)>maximum:raise ValueError('Unbounded ledger inventory')
            count=self.attempt(name,'ledger_assets.unavailable',lambda:int(self.read(ledger,'assetCount()')[0],16))
            inventory['observed_asset_count']=count
            if count!=len(entries) or count!=inventory.get('asset_count'):
                self.errors.append(dict(path=name,code='ledger_assets.mismatch'))
            for index,record in enumerate(entries):
                path=name+'.'+str(index)
                record['observed_asset']=self.attempt(path,'ledger_asset.unavailable',lambda i=index:
                    O._decode(self.read(ledger,'assets(uint256)',i)[0],O.ZERO))
                record['observed_is_asset']=self.attempt(path,'ledger_asset.unavailable',lambda r=record:
                    O._decode(self.read(ledger,'isAsset(address)',r['address'])[0],False))
                if record['observed_asset']!=record.get('address') or record['observed_is_asset'] is not True:
                    self.errors.append(dict(path=path,code='ledger_asset.mismatch'))

    def maintenance(self):
        budget=self.chain['helpers']['migration_budget']['address'];observed={}
        for pool in self.chain['pools']:
            pid=pool['pool_id']
            observed[pid]=self.attempt('maintenance.'+pid,'compound_interval.unavailable',lambda p=pid:
                int(self.read(budget,'compoundInterval(bytes32)',p)[0],16))
        self.chain['maintenance']['observed_compound_intervals']=observed

    def execution(self):
        m=self.chain['modules'];h=self.chain['helpers'];d=self.chain['dependencies']
        self.chain['lp_execution']['observed']=self.attempt('lp_execution','execution.unavailable',lambda:
            observe_execution(lambda target,method,*args:self.read(target,method,*args),
                liquidity=m['liquidity']['address'],router=h['balancing_router']['address'],
                pool_manager=d['pool_manager']['address'],state_view=d['state_view']['address'],
                access=m['access']['address'],pools=m['pools']['address'],quality_version=1,strategy=m['strategy']['address']))
        if not O._same(self.chain['lp_execution']['observed'],P.execution_expected(self.chain)):
            self.errors.append(dict(path='lp_execution',code='execution.mismatch'))

    def holder_exit(self):
        m=self.chain['modules'];access=m['access']['address'];vault=m['vault']['address'];nft=m['nft']['address'];exit=m['migration']['address']
        def uint(target,method,*args):return int(self.read(target,method,*args)[0],16)
        def flag(target,method):return O._decode(self.read(target,method)[0],False)
        def capture():
            observed={key:uint(exit,getter+'()') for key,getter in (
                ('phase','exitPhase'),('exit_minted_count','exitMintedCount'),('allocation_cursor','allocationCursor'),
                ('remaining_buckets','remainingBuckets'),('remaining_eth','remainingETH'),('remaining_zzz','remainingZZZ'))}
            observed.update(lp_exit_started=flag(access,'lpExitStarted()'),paused=flag(access,'paused()'),
                minted_count=uint(nft,'mintedCount()'),exit_review_hash='0x'+self.read(exit,'exitReviewHash()')[0],buckets=[],nfts=[])
            zzz=O._decode(self.read(exit,'currentZZZ()')[0],O.ZERO)
            if zzz!=self.chain['dependencies']['zzz']['address']:raise ValueError('Wrong fixed exit token')
            observed['balance_eth']=O._quantity(self.request('eth_getBalance',[exit,self.block]))
            observed['balance_zzz']=uint(zzz,'balanceOf(address)',exit)
            maximum=uint(vault,'MAX_BUCKETS()');count=uint(vault,'bucketCount()')
            if maximum!=4 or count>maximum or observed['minted_count']>1000:raise ValueError('Unbounded holder inventory')
            settlements=uint(exit,'settlementBucketCount()')
            if settlements>count:raise ValueError('Unbounded settlement inventory')
            actual_settlements=[uint(exit,'settlementBucketAt(uint256)',i) for i in range(settlements)]
            if len(set(actual_settlements))!=len(actual_settlements):raise ValueError('Duplicate settlement buckets')
            observed['settlement_buckets']=actual_settlements
            for i in range(count):
                bid=uint(vault,'bucketAt(uint256)',i)
                group=[int(w,16) for w in self.read(vault,'group(uint256)',bid,count=8)]
                settlement=self.read(exit,'bucketSettlement(uint256)',bid,count=7)
                row=dict(id=bid,position=group,total_shares=uint(vault,'bucketTotalShares(uint256)',bid),
                    settlement=[int(w,16) for w in settlement[:6]]+[O._decode(settlement[6],False)])
                if group[7]==1:
                    posm=self.chain['dependencies']['position_manager']['address']
                    ticks=[int(word,16) for word in self.read(m['liquidity']['address'],'ticks(uint256)',group[1],count=2)]
                    ticks=[tick-2**256 if tick>=2**255 else tick for tick in ticks]
                    if not -887272<=ticks[0]<ticks[1]<=887272:raise ValueError('Invalid physical LP ticks')
                    physical=self.read(posm,'getPoolAndPositionInfo(uint256)',group[1],count=6)
                    P.verify_position_identity(physical[:5],physical[5],group[0],ticks)
                    row.update(lp_owner=O._decode(self.read(posm,'ownerOf(uint256)',group[1])[0],O.ZERO),
                        lp_liquidity=uint(posm,'getPositionLiquidity(uint256)',group[1]),lp_ticks=ticks,
                        lp_pool_key=physical[:5],lp_position_info=physical[5])
                else:row.update(lp_owner=None,lp_liquidity=None,lp_ticks=None,lp_pool_key=None,lp_position_info=None)
                observed['buckets'].append(row)
            for ordinal in range(1,observed['minted_count']+1):
                identifier=uint(nft,'tokenAtOrdinal(uint256)',ordinal)
                raw=self.read(exit,'principalOf(uint256)',identifier,count=4)
                row=dict(id=identifier,ordinal=ordinal,reverse_ordinal=uint(nft,'mintOrdinalOf(uint256)',identifier),
                    owner=O._decode(self.read(nft,'ownerOf(uint256)',identifier)[0],O.ZERO),
                    bucket=uint(vault,'nftBucket(uint256)',identifier),shares=uint(vault,'sharesOf(uint256)',identifier),
                    eth=int(raw[0],16),zzz=int(raw[1],16),allocated=O._decode(raw[2],False),paid=O._decode(raw[3],False),claimable=None)
                if observed['phase']==3:row['claimable']=[int(w,16) for w in self.read(exit,'claimablePrincipal(uint256)',identifier,count=2)]
                observed['nfts'].append(row)
            return observed
        self.chain['holder_exit']['observed']=self.attempt('holder_exit','holder_exit.unavailable',capture)

    def contribution_reservation(self):
        def capture():
            m=self.chain['modules'];vault=m['vault']['address'];canonical=m['vault_canonical']['address']
            pool=self.chain['contribution_pool']
            def uint(target,method,*args):return int(self.read(target,method,*args)[0],16)
            bucket=uint(vault,'poolBucket(bytes32)',pool)
            canonical_bucket=uint(canonical,'bucketIdentity(bytes32)',pool)
            return dict(pool_id=pool,bucket_id=bucket,canonical_bucket_id=canonical_bucket,
                alias_bucket_id=uint(canonical,'aliasBucket(bytes32)',pool),
                target_registered=O._decode(self.read(vault,'registeredBucket(uint256)',bucket or canonical_bucket)[0],False),
                bucket_count=uint(vault,'bucketCount()'),maximum_buckets=uint(vault,'MAX_BUCKETS()'))
        self.chain['contribution_reservation']=self.attempt('contribution_reservation','reservation.unavailable',capture)

    def confirmation(self):
        target=self.chain['helpers']['rebalance_confirmation']['address'];strategy=self.chain['modules']['strategy']['address']
        def capture():
            result=dict(duration=int(self.read(target,'duration()')[0],16),
                max_observation_gap=int(self.read(target,'maxObservationGap()')[0],16),
                policy_revision=int(self.read(target,'policyRevision()')[0],16),review_hash='0x'+self.read(target,'reviewHash()')[0],
                reference_exit_required=O._decode(self.read(target,'requireReferenceExit()')[0],False),
                reference_review_hash='0x'+self.read(target,'referenceReviewHash()')[0],buckets=[])
            for bucket in self.chain['holder_exit']['observed']['buckets']:
                bid=bucket['id'];condition=self.read(target,'condition(uint256)',bid,count=3)
                stored=self.read(target,'observations(uint256)',bid,count=4)
                ready=O._decode(self.read(target,'ready(uint256)',bid)[0],False)
                raw=O._decode(self.read(strategy,'needsRebalance(uint256)',bid)[0],False)
                if ready!=O._decode(self.read(strategy,'rebalanceReady(uint256)',bid)[0],False):
                    raise ValueError('Strategy and helper confirmation readiness differ')
                pending=None
                physical=None;reference=None
                if P.confirmation_controls_allow(self.chain):
                    pending=O._decode(self.read(strategy,'rangeUpdatePending(uint256)',bid)[0],False)
                    if O._decode(condition[2],False)!=(raw and pending):
                        raise ValueError('Manual confirmation exception differs from the current range policy')
                    if raw and not pending:
                        physical,reference=[int(word,16) for word in self.read(target,'marketSides(uint256)',bid,count=2)]
                result['buckets'].append(dict(id=bid,condition_side=int(condition[0],16),condition_identity='0x'+condition[1],
                    manual=O._decode(condition[2],False),stored_identity='0x'+stored[0],first_seen=int(stored[1],16),
                    last_seen=int(stored[2],16),stored_side=int(stored[3],16),
                    ready=ready,raw_needed=raw,range_pending=pending,physical_side=physical,reference_side=reference))
            return result
        self.chain['rebalance_confirmation']['observed']=self.attempt('rebalance_confirmation','confirmation.unavailable',capture)


def observe(config,rpc):
    if not isinstance(config,dict) or any(type(config.get(k)) is not int or config.get(k)!=v for k,v in P.VERSIONS.items()) or config.get('canonical_schema')!=P.SCHEMA_NAME:
        raise ValueError('Use explicit schema6/accounting4/custody3/V5 capabilities')
    if not isinstance(config.get('chains'),list) or len(config['chains'])!=1:raise ValueError('Use one canonical chain inventory')
    output=copy.deepcopy(config);chain=output['chains'][0]
    for group,roles in (('modules',P.MODULES),('helpers',P.HELPERS)):
        if not isinstance(chain.get(group),dict) or set(chain[group])!=set(roles):raise ValueError('Use exact current module/helper inventory')
    for key,maximum in (('dependencies',32),('tokens',33),('pools',16),('activation_sources',64),('conversion_routes',64)):
        value=chain.get(key)
        if not isinstance(value,dict if key=='dependencies' else list) or len(value)>maximum:raise ValueError('Unbounded declared inventory')
    for key in ('holder_exit','lp_execution','maintenance','rebalance_confirmation'):
        if not isinstance(chain.get(key),dict):raise ValueError('Missing current-profile observation section')
    observer=Observer(rpc,chain);chain_id,genesis=observer.anchor()
    observer.records(P.expected_bindings(chain));observer.dependencies();observer.tokens();observer.sequencer()
    observer.governance();observer.pools();observer.sources();observer.ledgers();observer.nft()
    observer.wrappers();observer.routes();observer.maintenance();observer.execution();observer.holder_exit();observer.contribution_reservation();observer.confirmation();observer.finish()
    chain['observation']=dict(chain_id=chain_id,genesis_hash=genesis,block_number=observer.start['number'],
        block_hash=observer.start['hash'],observed_head=observer.head['number'],complete=not observer.errors,errors=observer.errors)
    return output
