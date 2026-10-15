"""Offline production inventory gate. Never signs, deploys, or contacts a chain.

Passing checks proves manifest consistency, not evidence authenticity or safety.
Runtime hashes must include immutable constructor values of each actual deployment.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256,word
from zzz_ops.state import integer

ZERO = '0x'+'00'*20
MODULES = ('access','vault','nft','liquidity','rewards','power','fees','strategy',
    'compounder','buyback','migration','bridge','receiver','oracle','pools','routes','transport')
EVIDENCE = ('toolchain','static_analysis','invariants','uniswap_fork',
    'staging','operations_recovery','gas_benchmarks','deployment_review','economic_approval',
    'independent_audit','remediation')
ROUTE_FIELDS = (('sourceChain','uint256'),('sourceAdapter','address'),('sourceVault','address'),
    ('sourceReceiver','address'),('destinationChain','uint256'),('destinationAdapter','address'),
    ('destinationVault','address'),('destinationReceiver','address'),('destinationPool','bytes32'),
    ('sourceToken0','address'),('sourceToken1','address'),('destinationToken0','address'),
    ('destinationToken1','address'),('token0Decimals','uint8'),('token1Decimals','uint8'))
POLICY_FIELDS = (('providerId','bytes32'),('sourceChain','uint256'),('sourceRouter','address'),
    ('sourceProvider','address'),('sourceCodeHash','bytes32'),('sourceConfigurationHash','bytes32'),
    ('destinationChain','uint256'),('destinationRouter','address'),('destinationProvider','address'),
    ('destinationCodeHash','bytes32'),('destinationConfigurationHash','bytes32'),('channelId','bytes32'),('reviewHash','bytes32'))

def identity(values: list[tuple[Any,str]]) -> str:
    # Route ACK zero addresses are legitimate; the general address codec forbids them.
    encoded = ''.join(f'{int(value,16):064x}' if typ=='address' else word(value,typ) for value,typ in values)
    return '0x'+keccak256(bytes.fromhex(encoded)).hex()

class Gate:
    def __init__(self,commit: Any):
        self.commit=commit;self.issues:list[dict[str,str]]=[]
    def check(self,condition: bool,path: str,code: str,message: str) -> bool:
        if not condition:self.issues.append({'path':path,'code':code,'message':message})
        return bool(condition)
    def obj(self,value: Any,path: str) -> dict[str,Any]:
        return value if self.check(isinstance(value,dict),path,'object.required','An object is required') else {}
    def items(self,value: Any,path: str,*,required: bool=True) -> list[Any]:
        valid=isinstance(value,list) and (bool(value) or not required)
        return value if self.check(valid,path,'list.required','A nonempty list is required' if required else 'A list is required') else []
    def num(self,value: Any,path: str,minimum: int=0,maximum: int=2**256-1) -> int|None:
        try:result=integer(value,path,minimum=minimum)
        except ValueError:result=None
        return result if self.check(result is not None and result<=maximum,path,'integer.invalid',
            f'An integer from {minimum} through {maximum} is required; floats/bools are rejected') else None
    def hex(self,value: Any,path: str,length: int=32,*,zero: bool=False,prefix: bool=True) -> str|None:
        pattern=('0x' if prefix else '')+f'[0-9a-fA-F]{{{length*2}}}'
        valid=isinstance(value,str) and re.fullmatch(pattern,value) is not None
        valid=valid and (zero or int(value,16)!=0)
        return value.lower() if self.check(valid,path,'hex.invalid','A correctly sized non-placeholder hex value is required') else None
    def text(self,value: Any,path: str) -> bool:
        return self.check(isinstance(value,str) and bool(value.strip()) and not re.search(
            r'\b(?:pending|placeholder|tbd|todo|unknown|unset)\b|<[^>]+>',value,re.I),path,'decision.pending','Reviewed non-placeholder text is required')
    def proof(self,value: Any,path: str) -> dict[str,Any]:
        record=self.obj(value,path)
        self.check(record.get('status')=='passed',path+'.status','evidence.missing','Explicit passing evidence is required')
        self.check(record.get('commit')==self.commit,path+'.commit','evidence.stale','Evidence must name the exact release commit')
        self.hex(record.get('sha256'),path+'.sha256',prefix=False)
        self.text(record.get('reference'),path+'.reference')
        return record

def validate(config: Any,*,expected_commit: str|None=None,now: int|None=None) -> dict[str,Any]:
    config=copy.deepcopy(config) if isinstance(config,dict) else {}
    gate=Gate(config.get('release_commit'));g=gate;now=int(time.time()) if now is None else now
    g.check(config.get('schema_version')==3 and type(config.get('schema_version')) is int,
        'schema_version','schema.unsupported','Schema version 3 with pooled custody and the fixed bridge router is required')
    g.check(config.get('accounting_model')=='shared-pools-v1','accounting_model','accounting.unsupported',
        'Shared-pool accounting must be explicitly reviewed; legacy per-NFT manifests are unsupported')
    g.commit=g.hex(g.commit,'release_commit',length=20,prefix=False)
    if expected_commit is not None:g.check(g.commit==expected_commit,'release_commit','commit.mismatch','Manifest differs from the expected commit')
    home=g.num(config.get('canonical_chain_id'),'canonical_chain_id',1)
    economics=g.obj(config.get('economics'),'economics')
    g.check(economics.get('reward_model')=='conventional_lp_fees','economics.reward_model',
        'reward.unsupported','The current implementation supports collected conventional LP fees; hook revenue remains unimplemented')
    g.check(g.num(economics.get('mint_price_wei'),'economics.mint_price_wei')==50_000_000_000_000_000,
        'economics.mint_price_wei','mint.price','Implemented mint price is exactly 0.05 ETH')
    g.check(g.num(economics.get('minimum_activation_usd18'),'economics.minimum_activation_usd18')==500*10**18,
        'economics.minimum_activation_usd18','activation.minimum','Implemented activation minimum is $500 of deployed LP')
    split=economics.get('fee_split_bps')
    g.check(isinstance(split,list) and all(type(n) is int for n in split) and split==[5000,3000,1000,1000],
        'economics.fee_split_bps','reward.split','Implemented allocation is owner/collective/compound/burn = 50/30/10/10')
    evidence=g.obj(config.get('evidence'),'evidence')
    for key in EVIDENCE:g.proof(evidence.get(key),'evidence.'+key)
    migration=g.obj(config.get('migration'),'migration');migration_enabled=migration.get('enabled')
    g.check(type(migration_enabled) is bool,'migration.enabled','migration.mode','Choose migration.enabled explicitly as true or false')
    g.proof(migration.get('future_onboarding_evidence'),'migration.future_onboarding_evidence')
    if migration_enabled is True:
        delivery=g.proof(evidence.get('multi_chain'),'evidence.multi_chain')
        g.check(delivery.get('kind')=='provider_staged_multichain','evidence.multi_chain.kind','provider.evidence','Actual staged provider delivery evidence is required, not mock/model migration tests')
    else:g.proof(migration.get('disabled_scope_approval'),'migration.disabled_scope_approval')
    audit=g.obj(evidence.get('independent_audit'),'evidence.independent_audit')
    g.text(audit.get('auditor'),'evidence.independent_audit.auditor')
    g.check(audit.get('independent') is True,'evidence.independent_audit.independent','audit.internal','An independent external audit is required')
    g.check(audit.get('kind')=='external_security_audit','evidence.independent_audit.kind','audit.internal','An AI/internal review cannot fulfill the external audit gate')
    for level in ('critical','high'):
        g.check(g.num(audit.get('open_'+level),'evidence.independent_audit.open_'+level)==0,
            'evidence.independent_audit.open_'+level,'audit.unresolved','No unresolved critical/high findings may remain')
    chains={};pool_ids={};token_maps={};provider_maps={}
    for index,item in enumerate(g.items(config.get('chains'),'chains')):
        path=f'chains[{index}]';chain=g.obj(item,path);cid=g.num(chain.get('chain_id'),path+'.chain_id',1)
        if cid is not None:
            g.check(cid not in chains,path+'.chain_id','chain.duplicate','Chain inventory must be unique');chains[cid]=chain
        observed=g.obj(chain.get('observed_block'),path+'.observed_block')
        g.num(observed.get('number'),path+'.observed_block.number');g.hex(observed.get('hash'),path+'.observed_block.hash')
        timestamp=g.num(observed.get('timestamp'),path+'.observed_block.timestamp',1)
        age=g.num(chain.get('maximum_snapshot_age_seconds'),path+'.maximum_snapshot_age_seconds',1)
        g.check(timestamp is not None and age is not None and 0<=now-timestamp<=age,
            path+'.observed_block','snapshot.stale','Observed snapshot must satisfy the explicitly selected age policy')
        modules=g.obj(chain.get('modules'),path+'.modules');chain['modules']=modules;addresses=[]
        for name in MODULES:
            module=g.obj(modules.get(name),path+'.modules.'+name);modules[name]=module
            addr=g.hex(module.get('address'),path+'.modules.'+name+'.address',20)
            module['address']=addr
            g.hex(module.get('runtime_hash'),path+'.modules.'+name+'.runtime_hash')
            if addr:addresses.append(addr)
            if name!='access':
                controller=g.hex(module.get('controller'),path+'.modules.'+name+'.controller',20)
                g.check(controller is not None and controller==modules['access'].get('address'),
                    path+'.modules.'+name+'.controller','binding.controller','Every module must bind the configured access controller')
        g.check(len(set(addresses))==len(addresses),path+'.modules','binding.duplicate','Module implementations must be distinct')
        governance=g.obj(chain.get('governance'),path+'.governance')
        gov=g.hex(governance.get('multisig'),path+'.governance.multisig',20)
        proposers=[g.hex(a,path+'.governance.proposers',20) for a in g.items(governance.get('proposers'),path+'.governance.proposers')]
        g.check(gov in proposers and gov is not None,path+'.governance.proposers','governance.proposer','The reviewed governance multisig must be a timelock proposer')
        for a in g.items(governance.get('executors'),path+'.governance.executors'):g.hex(a,path+'.governance.executors',20,zero=True)
        signers=[g.hex(a,path+'.governance.signers',20) for a in g.items(governance.get('signers'),path+'.governance.signers')]
        g.check(len(set(signers))==len(signers),path+'.governance.signers','governance.duplicate','Multisig signers must be unique')
        g.num(governance.get('threshold'),path+'.governance.threshold',1,len(signers))
        keeper=g.hex(governance.get('keeper'),path+'.governance.keeper',20)
        guardian=g.hex(governance.get('guardian'),path+'.governance.guardian',20)
        g.check(keeper not in proposers and keeper!=gov,path+'.governance.keeper','role.keeper','Use a dedicated keeper account, not the governance wallet')
        if guardian==gov or guardian==keeper:g.text(governance.get('overlap_review'),path+'.governance.overlap_review')
        g.num(governance.get('timelock_seconds'),path+'.governance.timelock_seconds',86400)
        g.check(governance.get('delay_fixed') is True,path+'.governance.delay_fixed','timelock.mutable','The current controller rejects delay updates')
        g.check(governance.get('post_seal_routes_timelocked') is True,path+'.governance.post_seal_routes_timelocked','timelock.routes','Post-seal route onboarding must pass through the fixed governance timelock')
        g.check(governance.get('migration_delay_seconds')==172800 and type(governance.get('migration_delay_seconds')) is int,
            path+'.governance.migration_delay_seconds','migration.delay','The implemented additional migration delay is two days')
        g.check(governance.get('sealed') is True and governance.get('bootstrap')==ZERO,
            path+'.governance','seal.incomplete','Before funded operation, sealing must revoke bootstrap and fix all bindings')
        g.proof(governance.get('roles_and_seal_evidence'),path+'.governance.roles_and_seal_evidence')
        constructor=g.obj(chain.get('constructor'),path+'.constructor')
        g.check(constructor.get('canonical_chain_id')==home and type(constructor.get('canonical_chain_id')) is int,
            path+'.constructor.canonical_chain_id','canonical.mismatch','Every vault must share the canonical chain ID')
        recipient=g.hex(constructor.get('mint_proceeds_recipient'),path+'.constructor.mint_proceeds_recipient',20)
        g.check(recipient not in addresses,path+'.constructor.mint_proceeds_recipient','mint.custody','Mint proceeds must stay outside protocol custody/reward modules')
        g.proof(constructor.get('recipient_payment_evidence'),path+'.constructor.recipient_payment_evidence')
        g.text(constructor.get('nft_base_uri'),path+'.constructor.nft_base_uri')
        g.num(constructor.get('maximum_buyback_usd18'),path+'.constructor.maximum_buyback_usd18',1)
        adapter_transport=g.hex(constructor.get('adapter_transport'),path+'.constructor.adapter_transport',20)
        g.check(adapter_transport is not None and adapter_transport==modules['transport'].get('address'),
            path+'.constructor.adapter_transport','router.binding','The adapter immutable transport must equal the sealed Ids.TRANSPORT router')
        router=g.obj(chain.get('bridge_router'),path+'.bridge_router');chain['bridge_router']=router
        g.check(router.get('immutable_module') is True and router.get('upgradeable') is False,
            path+'.bridge_router','router.mutable','The deployment must contain the fixed, non-upgradeable router module')
        policy_count=g.num(router.get('policy_count'),path+'.bridge_router.policy_count')
        outbound_count=g.num(router.get('outbound_policy_count'),path+'.bridge_router.outbound_policy_count')
        registered=g.items(router.get('registered_policy_ids'),path+'.bridge_router.registered_policy_ids',required=False)
        router['registered_policy_ids']=[g.hex(value,path+'.bridge_router.registered_policy_ids') for value in registered]
        g.check(policy_count is not None and outbound_count is not None and outbound_count<=policy_count,
            path+'.bridge_router','router.counts','Observed outbound policies cannot exceed registered policies')
        if migration_enabled is not True:g.check(policy_count==outbound_count==0 and not registered,
            path+'.bridge_router','migration.not_disabled','Migration-disabled initial launch must verify zero registered/outbound policies')
        g.proof(router.get('observation_evidence'),path+'.bridge_router.observation_evidence')
        dependencies=g.obj(chain.get('dependencies'),path+'.dependencies')
        for name in ('position_manager','state_view','pool_manager','permit2','zzz'):
            dependency=g.obj(dependencies.get(name),path+'.dependencies.'+name);dependencies[name]=dependency
            dependency['address']=g.hex(dependency.get('address'),path+'.dependencies.'+name+'.address',20)
            g.hex(dependency.get('runtime_hash'),path+'.dependencies.'+name+'.runtime_hash')
            g.proof(dependency.get('authority_review'),path+'.dependencies.'+name+'.authority_review')
        pm=dependencies.get('position_manager',{});sv=dependencies.get('state_view',{})
        manager=dependencies.get('pool_manager',{}).get('address');permit=dependencies.get('permit2',{}).get('address')
        g.check(pm.get('pool_manager')==manager and sv.get('pool_manager')==manager and pm.get('permit2')==permit,
            path+'.dependencies','uniswap.binding','PosM, StateView, PoolManager and Permit2 identities must agree')
        zzz=dependencies.get('zzz',{})
        g.check(zzz.get('burn_model')=='burn(uint256):exact_local_supply_reduction',path+'.dependencies.zzz.burn_model',
            'burn.unsupported','The buyback requires burn(uint256) to reduce local supply and balance by the exact amount')
        g.proof(zzz.get('burn_evidence'),path+'.dependencies.zzz.burn_evidence')
        providers={}
        provider_items=g.items(chain.get('providers'),path+'.providers',required=False)
        if migration_enabled is not True:g.check(not provider_items,path+'.providers','migration.not_disabled','Initial disabled launch must not invent approved provider wrappers')
        for wi,item in enumerate(provider_items):
            wp=path+f'.providers[{wi}]';provider=g.obj(item,wp)
            provider_id=g.hex(provider.get('provider_id'),wp+'.provider_id');channel_id=g.hex(provider.get('channel_id'),wp+'.channel_id')
            addr=g.hex(provider.get('address'),wp+'.address',20);provider['address']=addr
            provider['runtime_hash']=g.hex(provider.get('runtime_hash'),wp+'.runtime_hash')
            provider['router']=g.hex(provider.get('router'),wp+'.router',20)
            provider['configuration_hash']=g.hex(provider.get('configuration_hash'),wp+'.configuration_hash')
            g.check(provider.get('router')==modules['transport'].get('address') and provider.get('router') is not None,
                wp+'.router','provider.router','Wrapper router() must match the fixed local router')
            g.check(provider.get('upgradeable') is False and provider.get('immutable_configuration') is True,
                wp,'provider.mutable','Review immutable wrapper code/configuration; runtime hashing alone does not exclude proxy/dependency upgrades')
            for key in ('authenticated_delivery','funded_equivalent_assets','nonce_domain_replay_protection','finality_and_retries_reviewed'):
                g.check(provider.get(key) is True,wp+'.'+key,'transport.incomplete','Reviewed production provider/channel semantics are required')
            for key in ('authority_review','integration_evidence'):g.proof(provider.get(key),wp+'.'+key)
            integration=g.obj(provider.get('integration_evidence'),wp+'.integration_evidence')
            g.check(integration.get('kind')=='provider_staged_delivery' and integration.get('provider_id')==provider_id and
                integration.get('channel_id')==channel_id and type(integration.get('chain_id')) is int and integration.get('chain_id')==cid,
                wp+'.integration_evidence','provider.evidence','Staged delivery evidence must identify this exact provider/channel/chain')
            identity_key=(provider_id,channel_id,addr)
            g.check(identity_key not in providers,wp,'provider.duplicate','A provider/channel/wrapper identity must be unique on a chain')
            providers[identity_key]=provider
        provider_maps[cid]=providers
        tokens={}
        for ti,item in enumerate(g.items(chain.get('tokens'),path+'.tokens')):
            tp=path+f'.tokens[{ti}]';token=g.obj(item,tp);addr=g.hex(token.get('address'),tp+'.address',20)
            decimals=g.num(token.get('decimals'),tp+'.decimals',0,18);g.hex(token.get('runtime_hash'),tp+'.runtime_hash')
            g.text(token.get('canonical_asset'),tp+'.canonical_asset')
            g.check(token.get('non_rebasing') is True and token.get('transfer_tax') is False and token.get('reward_asset') is True,
                tp,'token.unsupported','Only reviewed conventional, tax-free ERC20 reward assets are supported')
            token['decimals']=decimals
            if addr:g.check(addr not in tokens,tp+'.address','token.duplicate','Token inventory must be unique');tokens[addr]=token
            feed=g.obj(token.get('feed'),tp+'.feed');g.hex(feed.get('source'),tp+'.feed.source',20);g.hex(feed.get('runtime_hash'),tp+'.feed.runtime_hash')
            fd=g.num(feed.get('decimals'),tp+'.feed.decimals',0,18);max_age=g.num(feed.get('maximum_age_seconds'),tp+'.feed.maximum_age_seconds',1,86400)
            g.check(feed.get('denomination')=='USD',tp+'.feed.denomination','oracle.denomination','USD feeds are required')
            answer=g.num(feed.get('answer'),tp+'.feed.answer',1);updated=g.num(feed.get('updated_at'),tp+'.feed.updated_at',1)
            rid=g.num(feed.get('round_id'),tp+'.feed.round_id',1,2**80-1);answered=g.num(feed.get('answered_in_round'),tp+'.feed.answered_in_round',1,2**80-1)
            g.check(None not in (timestamp,updated,max_age,rid,answered) and 0<=timestamp-updated<=max_age and answered>=rid,
                tp+'.feed','oracle.stale','Fresh, complete oracle rounds must match the observed block')
            g.check(answer is not None and fd is not None and answer*10**(18-fd)<=10**36,tp+'.feed.answer','oracle.bounds','Normalized price must satisfy the implemented bound')
            g.proof(feed.get('review'),tp+'.feed.review')
        token_maps[cid]=tokens
        g.check(len(tokens)<=32,path+'.tokens','reward.asset_limit','The current reward contract supports at most 32 admitted assets')
        g.check(zzz.get('address') in tokens,path+'.dependencies.zzz','burn.asset','Reviewed ZZZ token metadata/feed must be inventoried')
        sequencer=g.obj(chain.get('sequencer'),path+'.sequencer');mode=sequencer.get('mode')
        g.check(mode in ('feed','not_applicable'),path+'.sequencer.mode','sequencer.policy','An explicit chain-specific sequencer policy is required')
        if mode=='feed':
            g.hex(sequencer.get('address'),path+'.sequencer.address',20);g.hex(sequencer.get('runtime_hash'),path+'.sequencer.runtime_hash')
            started=g.num(sequencer.get('started_at'),path+'.sequencer.started_at',1)
            g.check(type(sequencer.get('answer')) is int and sequencer.get('answer')==0 and timestamp is not None and started is not None and timestamp-started>3600,
                path+'.sequencer','sequencer.down','Sequencer must be up beyond the implemented one-hour grace')
        else:g.check(sequencer.get('address')==ZERO,path+'.sequencer.address','sequencer.address','No-feed policy must match the immutable zero feed')
        g.proof(sequencer.get('review'),path+'.sequencer.review')
        pools={}
        for pi,item in enumerate(g.items(chain.get('pools'),path+'.pools')):
            pp=path+f'.pools[{pi}]';pool=g.obj(item,pp);pid=g.hex(pool.get('pool_id'),pp+'.pool_id')
            t0=g.hex(pool.get('currency0'),pp+'.currency0',20);t1=g.hex(pool.get('currency1'),pp+'.currency1',20)
            fee=g.num(pool.get('fee'),pp+'.fee',1,100000);spacing=g.num(pool.get('tickSpacing'),pp+'.tickSpacing',1,32767)
            g.check(pool.get('hooks')==ZERO,pp+'.hooks','pool.hook','Native/hooked pools are unsupported, including the selected Robinhood pool')
            g.check(t0 is not None and t1 is not None and t0<t1 and t0 in tokens and t1 in tokens,
                pp,'pool.assets','Sorted supported ERC20 currencies with reviewed feeds/reward eligibility are required')
            bounds={key:g.num(pool.get(key),pp+'.'+key,*limits) for key,limits in {
                'rangeBps':(100,5000),'triggerBps':(100,4999),'maxSpotDeviationBps':(1,500),
                'maxSlippageBps':(1,200),'minRebalanceInterval':(600,604800),'minDepositUSD':(1,2**256-1),'maxPositionUSD':(1,2**256-1)}.items()}
            if all(n is not None for n in bounds.values()):
                g.check(bounds['triggerBps']<bounds['rangeBps'] and bounds['maxSpotDeviationBps']<bounds['rangeBps'] and
                    fee is not None and fee<bounds['maxSlippageBps']*100 and bounds['maxPositionUSD']>=bounds['minDepositUSD'],
                    pp,'pool.bounds','Strategy/fee/value bounds must satisfy ZZZPoolRegistry')
            g.check(pool.get('depositsEnabled') is True and pool.get('operationsEnabled') is True,pp,'pool.disabled','The release pool must explicitly enable reviewed deposits and operations')
            if None not in (t0,t1,fee,spacing) and pool.get('hooks')==ZERO:
                g.check(pid==identity([(t0,'address'),(t1,'address'),(fee,'uint24'),(spacing,'uint24'),(ZERO,'address')]),pp+'.pool_id','pool.identity','Pool ID must hash the complete PoolKey')
            pool['currency0']=t0;pool['currency1']=t1
            if pid:g.check(pid not in pools,pp+'.pool_id','pool.duplicate','Pool IDs must be unique');pools[pid]=pool
        pool_ids[cid]=pools
    g.check(home in chains,'canonical_chain_id','canonical.absent','Canonical chain must be present in the inventory')
    reservations={}
    for cid,chain in chains.items():
        inventory={};path=f'chains[{cid}].bucket_reservations'
        observed=chain.get('observed_block') if isinstance(chain.get('observed_block'),dict) else {}
        observed_number=g.num(observed.get('number'),f'chains[{cid}].observed_block.number')
        observed_hash=g.hex(observed.get('hash'),f'chains[{cid}].observed_block.hash')
        for index,item in enumerate(g.items(chain.get('bucket_reservations'),path,required=False)):
            rp=path+f'[{index}]';record=g.obj(item,rp)
            pool_id=g.hex(record.get('pool_id'),rp+'.pool_id')
            bucket_id=g.num(record.get('bucket_id'),rp+'.bucket_id',1)
            origin_chain=g.num(record.get('home_chain_id'),rp+'.home_chain_id',1)
            origin_vault=g.hex(record.get('home_vault'),rp+'.home_vault',20)
            origin_pool=g.hex(record.get('home_pool_id'),rp+'.home_pool_id')
            canonical_vault=chains.get(home,{}).get('modules',{}).get('vault',{}).get('address')
            g.check(origin_chain==home and origin_vault is not None and origin_vault==canonical_vault,
                rp,'reservation.origin','Bucket origin must identify the inventoried canonical vault and chain')
            local_pool=pool_ids.get(cid,{}).get(pool_id,{})
            home_pool=pool_ids.get(home,{}).get(origin_pool,{})
            g.check(bool(local_pool) and bool(home_pool),rp,'reservation.pool',
                'The reserved local pool and canonical origin pool must both be inventoried')
            if None not in (origin_chain,origin_vault,origin_pool,bucket_id):
                computed=int(identity([(origin_chain,'uint256'),(origin_vault,'address'),(origin_pool,'bytes32')]),16)
                g.check(bucket_id==computed,rp+'.bucket_id','reservation.identity',
                    'Bucket ID must hash canonical home chain, vault and original PoolKey identity')
            if local_pool and home_pool:
                local_assets=[(token_maps.get(cid,{}).get(local_pool.get(key),{}).get('canonical_asset'),
                    token_maps.get(cid,{}).get(local_pool.get(key),{}).get('decimals')) for key in ('currency0','currency1')]
                home_assets=[(token_maps.get(home,{}).get(home_pool.get(key),{}).get('canonical_asset'),
                    token_maps.get(home,{}).get(home_pool.get(key),{}).get('decimals')) for key in ('currency0','currency1')]
                g.check(local_assets==home_assets or local_assets==home_assets[::-1],rp,'reservation.assets',
                    'Reserved pool assets must match the canonical bucket assets and nominal decimals in either order')
            observed_chain=g.num(record.get('observed_chain_id'),rp+'.observed_chain_id',1)
            observed_vault=g.hex(record.get('observed_vault'),rp+'.observed_vault',20)
            observed_bucket=g.num(record.get('observed_bucket_id'),rp+'.observed_bucket_id',1)
            block_number=g.num(record.get('observed_block_number'),rp+'.observed_block_number')
            block_hash=g.hex(record.get('observed_block_hash'),rp+'.observed_block_hash')
            g.check(observed_chain==cid and observed_vault is not None and
                observed_vault==chain.get('modules',{}).get('vault',{}).get('address') and
                observed_bucket is not None and observed_bucket==bucket_id and
                block_number is not None and block_number==observed_number and
                block_hash is not None and block_hash==observed_hash,
                rp,'reservation.observation',
                'Observed vault.poolBucket(pool_id) must equal the bucket at the exact inventoried chain, vault and block')
            review=g.proof(record.get('review_evidence'),rp+'.review_evidence')
            g.check(review.get('independent') is True,rp+'.review_evidence.independent','reservation.review',
                'An independent reservation and destination-custody review must be explicit')
            g.text(review.get('reviewer'),rp+'.review_evidence.reviewer')
            g.check(pool_id not in inventory,rp+'.pool_id','reservation.duplicate',
                'A local pool cannot have multiple or conflicting bucket reservation records')
            if pool_id is not None:inventory[pool_id]={'bucket_id':bucket_id,'home_chain_id':origin_chain,
                'home_vault':origin_vault,'home_pool_id':origin_pool}
        reservations[cid]=inventory
    policies={}
    policy_items=g.items(config.get('transport_policies'),'transport_policies',required=migration_enabled is True)
    if migration_enabled is not True:g.check(not policy_items,'transport_policies','migration.not_disabled','Initial disabled launch must have no approved transport policies')
    for pi,item in enumerate(policy_items):
        pp=f'transport_policies[{pi}]';policy=g.obj(item,pp);values={}
        for key,typ in POLICY_FIELDS:
            values[key]=g.hex(policy.get(key),pp+'.'+key,20 if typ=='address' else 32) if typ!='uint256' else g.num(policy.get(key),pp+'.'+key,1)
        policy_id=g.hex(policy.get('policy_id'),pp+'.policy_id')
        g.check(policy_id not in policies,pp+'.policy_id','policy.replay','Append-only policy identities must not be duplicated')
        g.check(type(policy.get('outbound_enabled')) is bool,pp+'.outbound_enabled','policy.mode','Outbound activation must be explicit; registration defaults disabled')
        if all(value is not None for value in values.values()):
            g.check(policy_id==identity([(values[key],typ) for key,typ in POLICY_FIELDS]),pp+'.policy_id','policy.identity','Policy ID must hash every immutable TransportPolicy field')
            g.check(values['sourceChain']!=values['destinationChain'] and values['sourceChain'] in chains and values['destinationChain'] in chains,
                pp,'policy.chain','Policy needs distinct reviewed participating chains')
            for side in ('source','destination'):
                cid=values[side+'Chain'];modules=chains.get(cid,{}).get('modules',{})
                g.check(values[side+'Router']==modules.get('transport',{}).get('address'),pp+'.'+side+'Router','policy.router','Policy router must match the fixed counterpart module')
                wrapper=provider_maps.get(cid,{}).get((values['providerId'],values['channelId'],values[side+'Provider']),{})
                g.check(bool(wrapper) and wrapper.get('runtime_hash')==values[side+'CodeHash'] and wrapper.get('router')==values[side+'Router'] and
                    wrapper.get('configuration_hash')==values[side+'ConfigurationHash'],pp+'.'+side+'Provider','policy.provider','Reviewed wrapper code and channel configuration must match the immutable policy pins')
        policy.update(values);review=g.proof(policy.get('review_evidence'),pp+'.review_evidence')
        g.check(policy.get('reviewHash')=='0x'+str(review.get('sha256')),pp+'.reviewHash','policy.review','Pinned review hash must identify the supplied policy review evidence')
        policies[policy_id]=policy
    for cid,chain in chains.items():
        router=chain['bridge_router'];relevant=[p for p in policies.values() if cid in (p.get('sourceChain'),p.get('destinationChain'))]
        listed=router['registered_policy_ids'];registered=set(listed)
        g.check(len(listed)==len(registered),f'chains[{cid}].bridge_router.registered_policy_ids','router.duplicate','Registered policy IDs must be unique')
        g.check(all(policy_id is not None and policy_id in policies for policy_id in registered),
            f'chains[{cid}].bridge_router.registered_policy_ids','router.unknown','Every observed registered policy must appear in the complete global inventory')
        g.check(all(policy_id in registered for policy_id,policy in policies.items() if policy in relevant),
            f'chains[{cid}].bridge_router.registered_policy_ids','router.unlisted','Every declared local source/destination policy must be registered on that chain')
        raw_routes=config.get('routes') if isinstance(config.get('routes'),list) else []
        for policy_id in registered:
            policy=policies.get(policy_id,{})
            if not policy or cid in (policy.get('sourceChain'),policy.get('destinationChain')):continue
            graph=[route for route in raw_routes if isinstance(route,dict) and route.get('kind')=='principal' and
                route.get('policy_id')==policy_id and route.get('sourceChain')==policy.get('sourceChain') and route.get('destinationChain')==policy.get('destinationChain')]
            g.check(cid==home and bool(graph),f'chains[{cid}].bridge_router.registered_policy_ids','router.remote_registration',
                'Remote-only policies are allowed only on the canonical chain with corresponding principal graph metadata')
            for route in graph:g.proof(route.get('canonical_graph_evidence'),f'chains[{cid}].bridge_router.remote_graph_evidence')
        count=g.num(router.get('policy_count'),f'chains[{cid}].bridge_router.policy_count')
        outbound=g.num(router.get('outbound_policy_count'),f'chains[{cid}].bridge_router.outbound_policy_count')
        g.check(count==len(registered) and outbound==sum(policies.get(policy_id,{}).get('sourceChain')==cid and policies.get(policy_id,{}).get('outbound_enabled') is True for policy_id in registered),
            f'chains[{cid}].bridge_router','router.inventory','Counts must match complete verified registration history and enabled listed local sends')
    routes=[];seen=set()
    route_items=g.items(config.get('routes'),'routes',required=migration_enabled is True)
    if migration_enabled is not True:g.check(not route_items,'routes','migration.not_disabled','Initial disabled launch must have no migration routes')
    for ri,item in enumerate(route_items):
        rp=f'routes[{ri}]';route=g.obj(item,rp);values={}
        for key,typ in ROUTE_FIELDS:
            values[key]=g.hex(route.get(key),rp+'.'+key,20,zero=key.startswith(('sourceToken','destinationToken'))) if typ=='address' else \
                g.hex(route.get(key),rp+'.'+key,zero=True) if typ=='bytes32' else g.num(route.get(key),rp+'.'+key,0 if typ=='uint8' else 1,18 if typ=='uint8' else 2**256-1)
        rid=g.hex(route.get('route_id'),rp+'.route_id');g.check(rid not in seen,rp+'.route_id','route.replay','Append-only route identities must not be duplicated');seen.add(rid)
        policy_id=g.hex(route.get('policy_id'),rp+'.policy_id');route['policy_id']=policy_id;policy=policies.get(policy_id,{})
        g.check(bool(policy),rp+'.policy_id','route.policy','Route must bind an existing reviewed immutable transport policy')
        if all(value is not None for value in values.values()) and policy_id is not None:
            g.check(rid==identity([(values[key],typ) for key,typ in ROUTE_FIELDS]+[(policy_id,'bytes32')]),rp+'.route_id','route.identity','Route ID must hash the complete Route and its immutable policy ID')
            source=values['sourceChain'];destination=values['destinationChain']
            g.check(source!=destination and source in chains and destination in chains,rp,'route.chain','Distinct inventoried source/destination chains are required')
            g.check(policy.get('sourceChain')==source and policy.get('destinationChain')==destination and
                (route.get('enabled') is not True or policy.get('outbound_enabled') is True),
                rp+'.policy_id','route.policy','Immutable route direction must match its policy; active routes also require outbound activation')
            for side,cid in (('source',source),('destination',destination)):
                modules=chains.get(cid,{}).get('modules',{})
                for suffix,module in (('Adapter','bridge'),('Vault','vault'),('Receiver','receiver')):
                    g.check(values[side+suffix]==modules.get(module,{}).get('address'),rp+'.'+side+suffix,'route.binding','Route endpoint must match the reviewed chain module')
            kind=route.get('kind');count={'principal':2,'reward':1,'ack':0}.get(kind) if isinstance(kind,str) else None
            g.check(count is not None,rp+'.kind','route.kind','Route kind must be principal, reward, or ack')
            for slot in (0,1):
                st=values[f'sourceToken{slot}'];dtok=values[f'destinationToken{slot}']
                required=count is not None and slot<count
                g.check((st!=ZERO and dtok!=ZERO) if required else st==ZERO and dtok==ZERO,
                    rp+f'.token{slot}','route.assets','Asset presence must match the bridge message kind')
                if required:
                    a=token_maps.get(source,{}).get(st,{});b=token_maps.get(destination,{}).get(dtok,{})
                    g.check(bool(a) and bool(b) and a.get('canonical_asset')==b.get('canonical_asset') and
                        a.get('decimals')==b.get('decimals')==values[f'token{slot}Decimals'],rp+f'.token{slot}','route.equivalence','Bridge assets must be reviewed equivalents at identical decimals/nominal units')
            if kind=='principal':
                pool=pool_ids.get(destination,{}).get(values['destinationPool'],{})
                g.check({pool.get('currency0'),pool.get('currency1')}=={values['destinationToken0'],values['destinationToken1']},rp+'.destinationPool','route.pool','Destination pool must contain the equivalent principal assets')
                bucket_id=g.num(route.get('bucket_id'),rp+'.bucket_id',1)
                source_pool_id=g.hex(route.get('source_pool_id'),rp+'.source_pool_id')
                source_pool=pool_ids.get(source,{}).get(source_pool_id,{})
                g.check(bool(source_pool) and (source_pool.get('currency0'),source_pool.get('currency1'))==
                    (values['sourceToken0'],values['sourceToken1']),rp+'.source_pool_id','route.source_pool',
                    'Principal source pool must be explicit and match source PoolKey token ordering')
                source_reservation=reservations.get(source,{}).get(source_pool_id,{})
                destination_reservation=reservations.get(destination,{}).get(values['destinationPool'],{})
                g.check(bucket_id is not None and bool(source_reservation) and bool(destination_reservation) and
                    source_reservation.get('bucket_id')==bucket_id==destination_reservation.get('bucket_id'),
                    rp,'route.reservation',
                    'Both principal pools must be observed permanently reserved to this exact canonical bucket before a funded migration')
                if source!=home and destination!=home:
                    g.proof(route.get('canonical_graph_evidence'),rp+'.canonical_graph_evidence')
            g.check(type(route.get('enabled')) is bool,rp+'.enabled','route.mode','Declare active or historical/inbound-only route enablement explicitly')
        route.update(values)
        g.proof(route.get('asset_and_authority_evidence'),rp+'.asset_and_authority_evidence');routes.append(route)
    active=[r for r in routes if r.get('enabled') is True and policies.get(r.get('policy_id'),{}).get('outbound_enabled') is True]
    if migration_enabled is True:g.check(any(r.get('kind')=='principal' for r in active),'routes','route.active_principal','Enabled migration requires an active reviewed principal route')
    for route in active:
        if route.get('kind')=='principal':
            reverse=[r for r in active if r.get('sourceChain')==route.get('destinationChain') and r.get('destinationChain')==route.get('sourceChain')]
            g.check(any(r.get('kind')=='ack' for r in reverse),'routes','route.ack_missing','Every principal hop needs a reviewed source-completion ACK route')
            if route.get('destinationChain')!=home:
                if route.get('sourceChain')!=home:
                    g.check(any(r.get('kind')=='ack' and r.get('sourceChain')==route.get('destinationChain') and r.get('destinationChain')==home for r in active),
                        'routes','route.home_ack_missing','Onward satellite hops also require a canonical-location ACK route')
                for slot in (0,1):
                    token=route.get(f'destinationToken{slot}')
                    g.check(any(r.get('kind')=='reward' and r.get('sourceChain')==route.get('destinationChain') and r.get('destinationChain')==home and r.get('sourceToken0')==token for r in active),
                        'routes','route.rewards_missing','Satellite principal assets need funded reward paths to the canonical chain')
    return {'schema_version':3,'status':'blocked' if g.issues else 'ready','ready':not g.issues,
        'release_commit':g.commit,'deployment_authorized':False,'issues':g.issues,
        'migration_enabled':migration_enabled is True,
        'limitations':['Offline manifest checks do not authenticate evidence, runtime code, authorities, or current chain state.',
            'A complete manifest is not an audit, a safety guarantee, or deployment/sealing/transaction authorization.']}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--expected-commit');parser.add_argument('--output')
    args=parser.parse_args()
    try:result=validate(json.loads(Path(args.config).read_text(encoding='utf-8')),expected_commit=args.expected_commit)
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        result={'status':'blocked','ready':False,'deployment_authorized':False,
            'issues':[{'code':'config.unreadable','path':'config','message':type(exc).__name__}]}
    encoded=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.output:Path(args.output).write_text(encoded,encoding='utf-8')
    print(encoded,end='');return 0 if result['ready'] else 1

if __name__=='__main__':sys.exit(main())
