"""Read-only schema8 observer. No historical custody, signer or pin adoption.

All state uses one canonical hash, including complete bounded holder inventory.
Actual provider latency/capacity and evidence authenticity remain qualification.
"""
from __future__ import annotations
import copy
import time
from zzz_ops import production_observer as O
from zzz_ops import production_v6 as P
from zzz_ops.lp_execution import observe as observe_execution

UINT_GETTERS = frozenset(('MAX_BATCH','PAYOUT_GAS','configurationRevision','LP_ROUTING_VERSION',
    'EXECUTION_QUALITY_VERSION','MAX_ADDITIONAL_LOSS_BPS','additionalLossBps','executionQualityRevision',
    'IDLE_COMPOUNDING_VERSION','MAX_EXECUTION_POOLS','executionRevision','searchIterations','quoteGasLimit',
    'REBALANCE_CONFIRMATION_VERSION','EMERGENCY_REBALANCE_VERSION','MAINTENANCE_POLICY_VERSION','duration','maxObservationGap','policyRevision','PORTFOLIO_VERSION','LP_BALANCE_MATH_VERSION','LP_POSITION_EXECUTOR_VERSION','thresholdBps','revision','triggerRevision','PROTOCOL_POLICY_VERSION','mintPrice','DEFAULT_RESIDUAL_SIDE_BPS'))
MAX_READS = 12000
MAX_SECONDS = 60


class Observer(O.Observer):
    def __init__(self,rpc,chain):
        super().__init__(rpc,chain)
        self.started=time.monotonic();self.read_count=0
        self.accounting_version=6;self.pricing_version=2;self.range_policy_version=1
        self._holder_bucket_inventory=None

    def read(self,target,signature,*args,count=1):
        if signature=='referenceX96(address,address)':
            if (target!=self.chain['modules']['oracle']['address'] or len(args)!=2 or count!=1 or
                    not any(tuple(args)==(p['currency0'],p['currency1']) for p in self.chain['pools'])):
                raise ValueError('Reference read differs from inventoried native pair')
            target=O._address(target)
            args=(O._address(args[0],native=True),O._address(args[1]))
            data='0x'+O.keccak256(signature.encode()).hex()[:8]+''.join(O._word(a) for a in args)
            values=O.decode_words(self.request('eth_call',[{'to':target,'data':data,'gas':hex(O.MAX_GETTER_GAS)},self.block]))
            if len(values)!=1:raise ValueError('Malformed reference price ABI')
            return values
        return super().read(target,signature,*args,count=count)

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
        if getter in ('balancingRouter','liquidityManager','rebalanceConfirmation','strategy','portfolioPolicy','protocolPolicy','balanceMath','balancer','positionOperator'):return O._decode(self.read(target,getter+'()')[0],O.ZERO)
        if getter in ('reviewHash','referenceReviewHash','mintPolicyFingerprint'):return '0x'+self.read(target,getter+'()')[0]
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
                access=m['access']['address'],pools=m['pools']['address'],quality_version=1,strategy=m['strategy']['address'],
                routing_version=2,math_helper=h['lp_balance_math']['address'],position_executor=h['lp_position_executor']['address'],portfolio_version=2))
        if not O._same(self.chain['lp_execution']['observed'],P.execution_expected(self.chain)):
            self.errors.append(dict(path='lp_execution',code='execution.mismatch'))

    def holder_exit(self):
        self._holder_bucket_inventory=None
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
            bucket_ids=set()
            for i in range(count):
                bid=uint(vault,'bucketAt(uint256)',i)
                if bid==0 or bid in bucket_ids:raise ValueError('Invalid registered bucket inventory')
                bucket_ids.add(bid)
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
                row['portfolio']=self.physical_portfolio(group) if group[7]==1 else None
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
        observed=self.attempt('holder_exit','holder_exit.unavailable',capture)
        self.chain['holder_exit']['observed']=observed
        if observed is not None:
            self._holder_bucket_inventory=(copy.deepcopy(self.block),tuple(row['id'] for row in observed['buckets']))

    def physical_portfolio(self,group):
        """Read exactly one or two Vault-owned physical legs at this anchor."""
        m=self.chain['modules'];manager=m['liquidity']['address'];posm=self.chain['dependencies']['position_manager']['address']
        def uint(target,method,*args):return int(self.read(target,method,*args)[0],16)
        main=group[1];secondary=uint(manager,'secondaryId(uint256)',main)
        if main==0 or secondary==main:raise ValueError('Invalid main/residual association')
        pool=next((p for p in self.chain['pools'] if int(p['pool_id'],16)==group[0]),None)
        if pool is None:raise ValueError('Uninventoried physical portfolio pool')
        price=O._uint(pool['slot0']['sqrt_price_x96']);legs=[];aggregate=[0,0]
        for identifier in [main]+([secondary] if secondary else []):
            ticks=[int(v,16) for v in self.read(manager,'ticks(uint256)',identifier,count=2)]
            ticks=[v-2**256 if v>=2**255 else v for v in ticks]
            physical=self.read(posm,'getPoolAndPositionInfo(uint256)',identifier,count=6)
            P.verify_position_identity(physical[:5],physical[5],group[0],ticks)
            owner=O._decode(self.read(posm,'ownerOf(uint256)',identifier)[0],O.ZERO)
            liquidity=uint(posm,'getPositionLiquidity(uint256)',identifier)
            if owner!=m['vault']['address'] or not 0<liquidity<2**128:raise ValueError('Physical portfolio custody/liquidity differs')
            amounts=[int(v,16) for v in self.read(manager,'amounts(uint256)',identifier,count=2)]
            if amounts!=P.physical_amounts(price,ticks,liquidity):raise ValueError('Physical portfolio amount view differs')
            aggregate=[a+b for a,b in zip(aggregate,amounts)]
            legs.append(dict(id=identifier,owner=owner,liquidity=liquidity,ticks=ticks,
                pool_key=physical[:5],position_info=physical[5],amounts=amounts))
        amounts=[int(v,16) for v in self.read(manager,'portfolioAmounts(uint256)',main,count=2)]
        stable='0x'+self.read(manager,'portfolioFingerprint(uint256)',main)[0]
        execution='0x'+self.read(manager,'executionPortfolioFingerprint(uint256)',main)[0]
        if aggregate!=amounts or (stable,execution)!=P.portfolio_fingerprints(self.chain,pool['pool_id'],legs):
            raise ValueError('Physical portfolio total or fingerprint differs')
        return dict(version=2,secondary_id=secondary,fingerprint=stable,execution_fingerprint=execution,amounts=amounts,legs=legs)

    def portfolio(self):
        def capture():
            m=self.chain['modules'];target=self.chain['helpers']['portfolio_policy']['address'];manager=m['liquidity']['address']
            def uint(where,method,*args):return int(self.read(where,method,*args)[0],16)
            result=dict(version=uint(target,'PORTFOLIO_VERSION()'),threshold_bps=uint(target,'thresholdBps()'),
                policy_revision=uint(target,'revision()'),trigger_revision=uint(target,'triggerRevision()'),trigger_review_hash='0x'+self.read(target,'triggerReviewHash()')[0],
                default_residual_side_bps=uint(target,'DEFAULT_RESIDUAL_SIDE_BPS()'),
                active_secondary_count=uint(manager,'activeSecondaryCount()'),pools=[],buckets=[])
            count=0
            for pool in self.chain['pools']:
                pid=pool['pool_id']
                result['pools'].append(dict(pool_id=pid,enabled=O._decode(self.read(target,'enabled(bytes32)',pid)[0],False),
                    geometry_revision=uint(target,'geometryRevision(bytes32)',pid),control_revision=uint(target,'controlRevision(bytes32)',pid),
                    minimum_main_bps=uint(target,'minimumMainBps(bytes32)',pid),residual_gap_spacings=uint(target,'residualGapSpacings(bytes32)',pid),residual_side_bps=uint(target,'residualSideBps(bytes32)',pid),
                    mode_review_hash='0x'+self.read(target,'modeReviewHash(bytes32)',pid)[0],
                    residual_review_hash='0x'+self.read(target,'residualReviewHash(bytes32)',pid)[0],
                    control_fingerprint='0x'+self.read(target,'controlFingerprint(bytes32)',pid)[0]))
            for bucket in self.chain['holder_exit']['observed']['buckets']:
                bid=bucket['id'];group=bucket['position'];active=group[7]==1
                secondary=uint(manager,'secondaryId(uint256)',group[1]) if active else 0
                result['buckets'].append(dict(id=bid,main_id=group[1],secondary_id=secondary,
                    applied_revision=uint(target,'appliedRevision(uint256)',group[1]) if active else None,
                    configuration_pending=O._decode(self.read(target,'configurationPending(uint256)',bid)[0],False)))
                if secondary:count+=1
            if not 0<=result['active_secondary_count']<=4 or count!=result['active_secondary_count']:
                raise ValueError('Secondary count differs from complete registered custody')
            return result
        self.chain['portfolio']['observed']=self.attempt('portfolio','portfolio.unavailable',capture)

    def confirmation(self):
        target=self.chain['helpers']['rebalance_confirmation']['address'];m=self.chain['modules'];strategy=m['strategy']['address']
        def capture():
            result=dict(duration=int(self.read(target,'duration()')[0],16),
                max_observation_gap=int(self.read(target,'maxObservationGap()')[0],16),
                policy_revision=int(self.read(target,'policyRevision()')[0],16),review_hash='0x'+self.read(target,'reviewHash()')[0],
                reference_exit_required=O._decode(self.read(target,'requireReferenceExit()')[0],False),
                reference_review_hash='0x'+self.read(target,'referenceReviewHash()')[0],buckets=[])
            for bucket in self.chain['holder_exit']['observed']['buckets']:
                bid=bucket['id'];group=bucket['position'];condition=self.read(target,'condition(uint256)',bid,count=3)
                stored=self.read(target,'observations(uint256)',bid,count=4)
                ready=O._decode(self.read(target,'ready(uint256)',bid)[0],False)
                raw=O._decode(self.read(strategy,'needsRebalance(uint256)',bid)[0],False)
                if ready!=O._decode(self.read(strategy,'rebalanceReady(uint256)',bid)[0],False):
                    raise ValueError('Strategy/helper readiness differs')
                pending=physical=reference=reference_x96=None
                if P.confirmation_controls_allow(self.chain) and group[7]==1:
                    pending=O._decode(self.read(strategy,'rangeUpdatePending(uint256)',bid)[0],False)
                    if not pending:
                        physical,reference=[int(w,16) for w in self.read(target,'marketSides(uint256)',bid,count=2)]
                        pool=next(p for p in self.chain['pools'] if int(p['pool_id'],16)==group[0])
                        reference_x96=int(self.read(m['oracle']['address'],'referenceX96(address,address)',pool['currency0'],pool['currency1'])[0],16)
                        sides=[P.threshold_side(group[5],bucket['lp_ticks'],value,self.chain['portfolio']['observed']['threshold_bps'])
                            for value in (O._uint(pool['slot0']['sqrt_price_x96']),reference_x96)]
                        if sides!=[physical,reference]:raise ValueError('Physical/reference threshold sides differ')
                result['buckets'].append(dict(id=bid,condition_side=int(condition[0],16),condition_identity='0x'+condition[1],
                    manual=O._decode(condition[2],False),stored_identity='0x'+stored[0],first_seen=int(stored[1],16),
                    last_seen=int(stored[2],16),stored_side=int(stored[3],16),ready=ready,raw_needed=raw,
                    range_pending=pending,physical_side=physical,reference_side=reference,reference_x96=reference_x96))
            return result
        self.chain['rebalance_confirmation']['observed']=self.attempt('rebalance_confirmation','confirmation.unavailable',capture)

    def protocol_policy(self):
        from zzz_ops.protocol_policy import DOMAINS,observe,observe_mint
        def capture():
            target=self.chain['helpers']['protocol_policy']['address'];access=self.chain['modules']['access']['address']
            result={domain:observe(self.read,policy=target,access=access,domain=domain) for domain in DOMAINS}
            result['mint']=observe_mint(self.read,policy=target,access=access)
            result.update(configuration_hash='0x'+self.read(target,'configurationHash()')[0],
                vrf_revision=int(self.read(target,'vrfRevision()')[0],16))
            return result
        result=self.attempt('protocol_policy','protocol_policy.unavailable',capture)
        self.chain['protocol_policy']['observed']=result
        expected={k:v for k,v in self.chain['protocol_policy'].items() if k not in ('observed','review_evidence')}
        if result is not None and not O._same(result,expected):
            self.errors.append(dict(path='protocol_policy',code='protocol_policy.mismatch'))

    def contribution_reservation(self):
        def capture():
            m=self.chain['modules'];vault=m['vault']['address'];canonical=m['vault_canonical']['address']
            pool=self.chain['contribution_pool']
            def uint(target,method,*args):return int(self.read(target,method,*args)[0],16)
            inventory=self._holder_bucket_inventory
            if inventory is None or self.block is None or inventory[0]!=self.block:
                raise ValueError('Fresh same-block holder inventory is unavailable')
            bucket_ids=inventory[1]
            count=uint(vault,'bucketCount()');maximum=uint(vault,'MAX_BUCKETS()')
            if maximum!=4 or count!=len(bucket_ids) or count>maximum:
                raise ValueError('Registered bucket count differs from the complete holder inventory')
            bucket=uint(vault,'poolBucket(bytes32)',pool)
            canonical_bucket=uint(canonical,'bucketIdentity(bytes32)',pool)
            # registeredBucket is private in accounting4. Registration is derived
            # from this run's complete bucketAt inventory: _registerBucket writes
            # its private flag and appends once atomically; no removal exists.
            return dict(pool_id=pool,bucket_id=bucket,canonical_bucket_id=canonical_bucket,
                alias_bucket_id=uint(canonical,'aliasBucket(bytes32)',pool),
                target_registered=(bucket or canonical_bucket) in bucket_ids,
                bucket_count=count,maximum_buckets=maximum)
        self.chain['contribution_reservation']=self.attempt('contribution_reservation','reservation.unavailable',capture)



def observe(config,rpc):
    if not isinstance(config,dict) or any(type(config.get(k)) is not int or config.get(k)!=v for k,v in P.VERSIONS.items()) or config.get('canonical_schema')!=P.SCHEMA_NAME:
        raise ValueError('Use explicit schema8/accounting6/custody4/portfolio2/V6 capabilities')
    if not isinstance(config.get('chains'),list) or len(config['chains'])!=1:raise ValueError('Use one canonical chain inventory')
    output=copy.deepcopy(config);chain=output['chains'][0]
    for group,roles in (('modules',P.MODULES),('helpers',P.HELPERS)):
        if not isinstance(chain.get(group),dict) or set(chain[group])!=set(roles):raise ValueError('Use exact current module/helper inventory')
    for key,maximum in (('dependencies',32),('tokens',33),('pools',16),('activation_sources',64),('conversion_routes',64)):
        value=chain.get(key)
        if not isinstance(value,dict if key=='dependencies' else list) or len(value)>maximum:raise ValueError('Unbounded declared inventory')
    for key in ('holder_exit','lp_execution','maintenance','rebalance_confirmation','portfolio','protocol_policy'):
        if not isinstance(chain.get(key),dict):raise ValueError('Missing current-profile observation section')
    observer=Observer(rpc,chain);chain_id,genesis=observer.anchor()
    observer.records(P.expected_bindings(chain));observer.dependencies();observer.tokens();observer.sequencer()
    observer.governance();observer.protocol_policy();observer.pools();observer.sources();observer.ledgers();observer.nft()
    observer.wrappers();observer.routes();observer.maintenance();observer.execution();observer.holder_exit();observer.contribution_reservation();observer.portfolio();observer.confirmation();observer.finish()
    chain['observation']=dict(chain_id=chain_id,genesis_hash=genesis,block_number=observer.start['number'],
        block_hash=observer.start['hash'],observed_head=observer.head['number'],complete=not observer.errors,errors=observer.errors)
    return output
