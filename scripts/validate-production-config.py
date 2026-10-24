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
from itertools import combinations
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256,word
from zzz_ops.state import integer

ZERO = '0x'+'00'*20
MODULES = ('access','vault','nft','liquidity','rewards','membership','fees','strategy',
    'compounder','buyback','migration','bridge','receiver','oracle','pools','routes','transport',
    'canonical','nft_canonical','vault_canonical','fees_canonical')
EVIDENCE = ('toolchain','static_analysis','invariants','uniswap_fork',
    'staging','operations_recovery','gas_benchmarks','deployment_review','economic_approval',
    'independent_audit','remediation')
ARTWORK_COLORS = ('cyan','blue','violet','emerald','amber','crimson','ivory','onyx')
ARTWORK_ANCHORS = frozenset(('amber','crimson','ivory','onyx'))
ARTWORK_ADDITIONS = frozenset(('amber','crimson','onyx'))
ARTWORK_PATTERNS = ('arcs','panels','orbits','ribs')
def allowed_artwork_palette(colors):
    if len(colors)==1:return True
    if len(colors)==2:return bool(ARTWORK_ANCHORS.intersection(colors))
    return any(color in ARTWORK_ADDITIONS and ARTWORK_ANCHORS.intersection(
        other for other in colors if other!=color) for color in colors)
ARTWORK_PALETTES = tuple('-'.join(colors) for count in (1,2,3)
    for colors in combinations(ARTWORK_COLORS,count) if allowed_artwork_palette(colors))
ARTWORK_FILES = tuple(f'{palette}-{pattern}-{rarity}-{stage}.svg' for palette in ARTWORK_PALETTES
    for pattern in ARTWORK_PATTERNS for rarity in ('commun','rare','legendary')
    for stage in ('dormant','activated','enhanced','singularity'))
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
    if isinstance(config,dict) and config.get('custody_architecture') == 'governed-v1':
        return {'schema_version':4,'status':'blocked','ready':False,'deployment_authorized':False,
            'issues':[{'code':'custody.inventory_schema_pending','path':'custody_architecture',
                'message':'Governed custody changes module bindings, external principal/royalty trust, finality and recovery inventory. The legacy v3 release gate cannot approve this candidate; a separately reviewed inventory/schema update is required.'}],
            'limitations':['No current-source production approval, verifier/provider qualification or public transaction authorization.']}
    config=copy.deepcopy(config) if isinstance(config,dict) else {}
    gate=Gate(config.get('release_commit'));g=gate;now=int(time.time()) if now is None else now
    g.check(config.get('schema_version')==4 and type(config.get('schema_version')) is int,
        'schema_version','schema.unsupported','Schema version 4 with equal activated membership and separate NFT royalties is required')
    g.check(config.get('accounting_model')=='shared-pools-v2','accounting_model','accounting.unsupported',
        'Current shared-pool accounting must be explicitly reviewed; legacy per-NFT and Power-weighted manifests are unsupported')
    g.commit=g.hex(g.commit,'release_commit',length=20,prefix=False)
    if expected_commit is not None:g.check(g.commit==expected_commit,'release_commit','commit.mismatch','Manifest differs from the expected commit')
    home=g.num(config.get('canonical_chain_id'),'canonical_chain_id',1)
    economics=g.obj(config.get('economics'),'economics')
    reward_model=economics.get('reward_model')
    g.check(reward_model in ('conventional_lp_fees','external_funded_revenue'),'economics.reward_model',
        'reward.unsupported','Choose supported conventional LP fees or actual externally funded revenue; this does not enable native/hooked LP custody')
    if reward_model=='external_funded_revenue':
        policy=g.obj(economics.get('external_reward_policy'),'economics.external_reward_policy')
        for field,expected in {'payment_method':'plain_transfers','allocation_timing':'processing_time',
            'owner_weights':'bucket_shares','collective_weights':'equal_activated_nfts',
            'revenue_entitlement':'received_funds_only'}.items():
            g.check(policy.get(field)==expected,'economics.external_reward_policy.'+field,
                'reward.policy','External funding uses plain transfers, bucket owner shares and equal activated-NFT collective shares, without guaranteed historical revenue')
        g.text(policy.get('source_description'),'economics.external_reward_policy.source_description')
        g.proof(policy.get('terms_evidence'),'economics.external_reward_policy.terms_evidence')
    g.check(g.num(economics.get('mint_price_wei'),'economics.mint_price_wei')==50_000_000_000_000_000,
        'economics.mint_price_wei','mint.price','Implemented mint price is exactly 0.05 ETH')
    g.check(g.num(economics.get('minimum_activation_usd18'),'economics.minimum_activation_usd18')==100*10**18,
        'economics.minimum_activation_usd18','activation.minimum','Implemented activation minimum is $100 original gross source input')
    g.check(economics.get('activation_minimum_basis')=='gross_source_input' and
        type(economics.get('maximum_entry_loss_bps')) is int and economics.get('maximum_entry_loss_bps')==100 and
        economics.get('network_gas_separate') is True,
        'economics','activation.execution_budget','Direct or atomic routed entry requires at least 99% of the original gross source value as marginal deployed LP; gas is separate.')
    split=economics.get('fee_split_bps')
    g.check(isinstance(split,list) and all(type(n) is int for n in split) and split==[8000,1000,500,500],
        'economics.fee_split_bps','reward.split','Implemented allocation is owner/collective/compound/burn = 80/10/5/5')
    g.check(economics.get('collective_weights')=='equal_activated_nfts',
        'economics.collective_weights','reward.collective','The 10% collective allocation is equal per activated NFT, independently of LP size or rarity')
    g.check(g.num(economics.get('maximum_membership_dust_raw'),'economics.maximum_membership_dust_raw')==19,
        'economics.maximum_membership_dust_raw','reward.dust','Twenty-unit fee baskets settle at most nineteen raw token units to incumbent owners at membership boundaries')
    nft_policy=g.obj(config.get('nft_policy'),'nft_policy')
    for key,expected in {'rarity_counts':[600,300,100],'initial_rarity_bps':[6000,3000,1000],'royalty_weights':[1,2,3]}.items():
        value=nft_policy.get(key)
        g.check(isinstance(value,list) and all(type(n) is int for n in value) and value==expected,
            'nft_policy.'+key,'nft.policy','The exact collection rarity quotas, initial odds and activated NFT royalty weights must match the implemented policy')
    for key,expected in {'max_supply':1000,'marketplace_royalty_bps':500,'received_royalty_distribution_bps':10000}.items():
        g.check(g.num(nft_policy.get(key),'nft_policy.'+key)==expected,
            'nft_policy.'+key,'nft.policy','Supply is capped at 1000; marketplace royalties are 5%, with all received royalties in the separate NFT royalty ledger')
    for key,expected in {'rarity_distribution':'fixed_quotas_without_replacement',
        'rarity_randomization':'vrf_mint_order_without_replacement',
        'royalty_eligibility':'activated_nfts_only','royalty_entitlement':'received_funds_only',
        'evolution_basis':'current_attributed_lp_value_usd18','unavailable_valuation':'unavailable',
        'randomness_policy':'verified_coordinator_two_words'}.items():
        g.check(nft_policy.get(key)==expected,'nft_policy.'+key,'nft.policy','Explicit current NFT behavior must match the reviewed implementation')
    thresholds=g.items(nft_policy.get('evolution_thresholds_usd18'),'nft_policy.evolution_thresholds_usd18')
    values=[g.num(value,f'nft_policy.evolution_thresholds_usd18[{i}]') for i,value in enumerate(thresholds)]
    g.check(values==[0,100*10**18,1000*10**18,10000*10**18],
        'nft_policy.evolution_thresholds_usd18','nft.evolution','Current attributed LP thresholds must be Dormant/Activated/Enhanced/Singularity = $0/$100/$1,000/$10,000')
    g.proof(nft_policy.get('economic_review_evidence'),'nft_policy.economic_review_evidence')
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
        g.check('power' not in modules,path+'.modules.power','binding.legacy','Legacy Power modules cannot replace or accompany equal activated membership')
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
        cp=path+'.canonical_handoff';canonical=g.obj(chain.get('canonical_handoff'),cp)
        chain['canonical_handoff']=canonical
        g.check(canonical.get('transport')=='same_chain_only' and canonical.get('remote_activation_enabled') is False,
            cp,'canonical.transport','This candidate has no qualified cross-chain canonical handoff or multisig override')
        g.check(type(canonical.get('state')) is int and canonical.get('state')==0 and
            canonical.get('settling') is False and canonical.get('preparation_active') is False and
            type(canonical.get('phase')) is int and canonical.get('phase') in (0,5),
            cp,'canonical.lifecycle','Funded operation requires an active canonical deployment, not a frozen, importing or retired one')
        g.check(type(canonical.get('observed_chain_id')) is int and canonical.get('observed_chain_id')==cid and
            type(canonical.get('observed_block_number')) is int and canonical.get('observed_block_number')==observed.get('number') and
            canonical.get('observed_block_hash')==observed.get('hash'),cp,'canonical.observation',
            'Observe lifecycle, bound modules, helper owners and factories at the exact inventory block')
        bindings=g.obj(canonical.get('observed_bindings'),cp+'.observed_bindings')
        origin_chain=g.num(canonical.get('origin_chain_id'),cp+'.origin_chain_id',1)
        origin_vault=g.hex(canonical.get('origin_vault'),cp+'.origin_vault',20)
        canonical['origin_chain_id']=origin_chain
        canonical['origin_vault']=origin_vault
        g.check(type(bindings.get('origin_chain_id')) is int and bindings.get('origin_chain_id')==origin_chain and origin_chain is not None and
            bindings.get('origin_vault')==origin_vault and origin_vault is not None,
            cp+'.observed_bindings','canonical.lineage','Observe the Vault companion origin domain without replacing it by current custody')
        for name,owner in (('nft_canonical','nft'),('vault_canonical','vault'),('fees_canonical','fees')):
            g.check(bindings.get(name)==modules[name].get('address') and bindings.get(name+'_owner')==modules[owner].get('address'),
                cp+'.observed_bindings.'+name,'canonical.binding','Each sealed companion must bind its exact custody/ledger owner')
        g.check(bindings.get('canonical')==modules['canonical'].get('address'),cp+'.observed_bindings.canonical',
            'canonical.binding','Access.canonicalHandoff must match the sealed coordinator')
        canonical_factories=[]
        for name,owner in (('royalty_factory','access'),('reward_receiver_factory','fees')):
            fp=cp+'.'+name;factory=g.obj(canonical.get(name),fp)
            factory_address=g.hex(factory.get('address'),fp+'.address',20);canonical_factories.append(factory_address)
            factory['address']=factory_address
            g.hex(factory.get('runtime_hash'),fp+'.runtime_hash')
            g.check(factory_address is not None and factory_address not in addresses and
                factory.get('immutable') is True and factory.get('owner')==modules[owner].get('address') and
                factory.get('controller')==modules['access'].get('address') and
                bindings.get(name)==factory_address,fp,'canonical.factory','Immutable factories must match their observed controller/Fees bindings')
        g.check(len(set(canonical_factories))==2,cp,'canonical.factory','The two factory addresses must be distinct')
        cr=g.proof(canonical.get('review_evidence'),cp+'.review_evidence')
        g.check(all(cr.get(key) is True for key in ('independent','complete_accounting_tested','exact_backing_tested',
            'abort_restoration_tested','single_successor_tested','late_receipts_tested','onward_migration_tested')),
            cp+'.review_evidence','canonical.review','Require independent review of exact rights, backing, cancellation and onward lifecycle')
        if canonical.get('phase')==0:
            g.check(canonical.get('incoming_source')==ZERO,cp+'.incoming_source','canonical.origin','An unused coordinator has no source')
            g.check(origin_chain==home and origin_vault==modules['vault'].get('address'),cp,'canonical.lineage',
                'An original deployment starts with its configured canonical chain and own Vault origin')
        elif canonical.get('phase')==5:
            g.hex(canonical.get('incoming_source'),cp+'.incoming_source',20)
            g.check(cid==home and origin_chain==home and migration_enabled is False,cp,'canonical.transport',
                'The same-chain successor is canonical locally; legacy v3 bridging must remain disabled')
            ar=g.proof(canonical.get('activation_evidence'),cp+'.activation_evidence')
            g.check(ar.get('kind')=='atomic_same_chain_canonical_activation' and
                ar.get('source_permanently_retired') is True and ar.get('all_backing_verified') is True and
                type(ar.get('origin_chain_id')) is int and ar.get('origin_chain_id')==origin_chain and ar.get('origin_vault')==origin_vault and
                origin_vault is not None,
                cp+'.activation_evidence','canonical.activation','A replacement needs exact finalized retirement/activation and backing evidence')
        ap=path+'.activation_assets';activation=g.obj(chain.get('activation_assets'),ap)
        activation_address=g.hex(activation.get('address'),ap+'.address',20)
        g.hex(activation.get('runtime_hash'),ap+'.runtime_hash')
        g.check(activation_address is not None and activation_address not in addresses and
            activation.get('immutable') is True and activation.get('registry')==modules['pools'].get('address') and
            activation.get('controller')==modules['access'].get('address'),ap,'activation.binding',
            'The immutable activation helper must bind this pool registry and access controller, separately from custody modules')
        g.check(activation.get('observed_registry_helper')==activation_address and activation_address is not None and
            type(activation.get('observed_chain_id')) is int and activation.get('observed_chain_id')==cid and
            type(activation.get('observed_block_number')) is int and activation.get('observed_block_number')==observed.get('number') and
            activation.get('observed_block_hash')==observed.get('hash'),ap,'activation.observation',
            'Registry.activationAssets, helper bindings and runtime must be observed at the exact inventory block')
        activation_review=g.proof(activation.get('review_evidence'),ap+'.review_evidence')
        g.check(activation_review.get('independent') is True and
            activation_review.get('add_disable_reenable_tested') is True and
            activation_review.get('active_policies_reviewed') is True and
            activation_review.get('no_claim_or_exit_dependency') is True,ap+'.review_evidence','activation.review',
            'Independently review current policy history, asset add/disable/re-enable and admission-independent claims/exits')
        ep=path+'.activation_entry';entry=g.obj(chain.get('activation_entry'),ep)
        entry_address=g.hex(entry.get('address'),ep+'.address',20)
        g.hex(entry.get('runtime_hash'),ep+'.runtime_hash')
        g.check(entry_address is not None and entry_address not in addresses and entry_address!=activation_address and
            entry.get('immutable') is True and entry.get('registry')==modules['pools'].get('address') and
            entry.get('controller')==modules['access'].get('address') and entry.get('activation_assets')==activation_address,
            ep,'entry.binding','Atomic Entry must be the immutable Registry child bound to its exact access/asset policies')
        g.check(entry.get('observed_registry_entry')==entry_address and entry_address is not None and
            type(entry.get('observed_chain_id')) is int and entry.get('observed_chain_id')==cid and
            type(entry.get('observed_block_number')) is int and entry.get('observed_block_number')==observed.get('number') and
            entry.get('observed_block_hash')==observed.get('hash'),ep,'entry.observation',
            'Observe Registry.activationEntry, immutable Entry bindings and runtime at the exact inventory block')
        er=g.proof(entry.get('review_evidence'),ep+'.review_evidence')
        g.check(all(er.get(key) is True for key in ('independent','original_source_value_tested','aggregate_loss_budget_tested',
            'callback_owner_context_reviewed','typed_routes_reviewed','complete_route_history_reviewed')),
            ep+'.review_evidence','entry.review','Independently review source custody/value, total loss, callback context and complete typed-route policy history')
        bp=path+'.migration_budget';budget=g.obj(chain.get('migration_budget'),bp)
        budget_address=g.hex(budget.get('address'),bp+'.address',20)
        budget['address']=budget_address
        g.hex(budget.get('runtime_hash'),bp+'.runtime_hash')
        g.check(budget_address is not None and budget_address not in addresses and
            budget_address not in (activation_address,entry_address) and budget.get('immutable') is True and
            budget.get('vault')==modules['vault'].get('address') and
            budget.get('controller')==modules['access'].get('address'),bp,'migration_budget.binding',
            'The immutable budget helper must be created by and bound to this Vault and controller')
        g.check(budget_address is not None and budget.get('observed_vault_helper')==budget_address and
            type(budget.get('observed_chain_id')) is int and budget.get('observed_chain_id')==cid and
            type(budget.get('observed_block_number')) is int and budget.get('observed_block_number')==observed.get('number') and
            budget.get('observed_block_hash')==observed.get('hash'),bp,'migration_budget.observation',
            'Observe Vault.migrationBudget, helper.vault/access and runtime at the exact inventory block')
        br=g.proof(budget.get('review_evidence'),bp+'.review_evidence')
        g.check(all(br.get(key) is True for key in ('independent','aggregate_loss_tested','compound_not_subsidy_tested',
            'callback_price_snapshot_tested','local_scope_reviewed')),bp+'.review_evidence','migration_budget.review',
            'Review the aggregate local move/resume budget and its exclusions; it is not an asynchronous bridge guarantee')
        pp=path+'.pair_migration';pair=g.obj(chain.get('pair_migration'),pp)
        pair_address=g.hex(pair.get('address'),pp+'.address',20);pair['address']=pair_address
        g.hex(pair.get('runtime_hash'),pp+'.runtime_hash')
        g.check(pair_address is not None and pair_address not in addresses and
            pair_address not in (activation_address,entry_address,budget_address) and pair.get('immutable') is True and
            pair.get('migration')==modules['migration'].get('address') and pair.get('controller')==modules['access'].get('address') and
            pair.get('vault')==modules['vault'].get('address') and pair.get('budget')==budget_address and
            pair.get('vault_canonical')==modules['vault_canonical'].get('address'),pp,'pair_migration.binding',
            'Inventory the fixed Migration-created pair companion and its exact custody/controller bindings')
        g.check(pair_address is not None and pair.get('observed_migration_helper')==pair_address and
            type(pair.get('observed_chain_id')) is int and pair.get('observed_chain_id')==cid and
            type(pair.get('observed_block_number')) is int and pair.get('observed_block_number')==observed.get('number') and
            pair.get('observed_block_hash')==observed.get('hash') and
            type(pair.get('active_bucket')) is int and pair.get('active_bucket')==0 and
            pair.get('active_request')=='0x'+'00'*32 and pair.get('taking_reserves') is False and
            pair.get('budget_pair_executor')==ZERO,pp,'pair_migration.observation',
            'Observe Migration.pairMigration, fixed bindings/runtime and empty atomic contexts at the inventory block')
        pr=g.proof(pair.get('review_evidence'),pp+'.review_evidence')
        g.check(all(pr.get(key) is True for key in ('independent','fixed_price_aggregate_loss_tested',
            'historical_compound_tested','unchanged_reward_currencies_tested','exact_transient_custody_tested',
            'composition_epoch_import_tested','v3_boundary_reviewed','bounded_gas_qualified')),
            pp+'.review_evidence','pair_migration.review','Review local conversion, historic rights, atomic custody, epoch imports and the blocked V3 boundary')
        governance=g.obj(chain.get('governance'),path+'.governance')
        gov=g.hex(governance.get('multisig'),path+'.governance.multisig',20)
        proposers=[g.hex(a,path+'.governance.proposers',20) for a in g.items(governance.get('proposers'),path+'.governance.proposers')]
        g.check(gov in proposers and gov is not None,path+'.governance.proposers','governance.proposer','The reviewed governance multisig must be a governance-controller proposer')
        for a in g.items(governance.get('executors'),path+'.governance.executors'):g.hex(a,path+'.governance.executors',20,zero=True)
        signers=[g.hex(a,path+'.governance.signers',20) for a in g.items(governance.get('signers'),path+'.governance.signers')]
        g.check(len(set(signers))==len(signers),path+'.governance.signers','governance.duplicate','Multisig signers must be unique')
        g.num(governance.get('threshold'),path+'.governance.threshold',1,len(signers))
        keeper=g.hex(governance.get('keeper'),path+'.governance.keeper',20)
        guardian=g.hex(governance.get('guardian'),path+'.governance.guardian',20)
        g.check(keeper not in proposers and keeper!=gov,path+'.governance.keeper','role.keeper','Use a dedicated keeper account, not the governance wallet')
        if guardian==gov or guardian==keeper:g.text(governance.get('overlap_review'),path+'.governance.overlap_review')
        g.num(governance.get('timelock_seconds'),path+'.governance.timelock_seconds',0,0)
        g.check(governance.get('delay_fixed') is True,path+'.governance.delay_fixed','timelock.mutable','The current controller rejects delay updates')
        g.check(governance.get('post_seal_routes_timelocked') is False,path+'.governance.post_seal_routes_timelocked','timelock.routes','Post-seal onboarding is governance-authorized without a waiting period')
        g.check(governance.get('migration_delay_seconds')==0 and type(governance.get('migration_delay_seconds')) is int,
            path+'.governance.migration_delay_seconds','migration.delay','Approved migrations have no additional time delay')
        g.check(governance.get('sealed') is True and governance.get('bootstrap')==ZERO,
            path+'.governance','seal.incomplete','Before funded operation, sealing must revoke bootstrap and fix all bindings')
        authority_review=g.proof(governance.get('roles_and_seal_evidence'),path+'.governance.roles_and_seal_evidence')
        g.check(all(authority_review.get(key) is True for key in (
            'zero_delay_governance_tested','immediate_migration_tested','no_notice_risk_accepted')),
            path+'.governance.roles_and_seal_evidence','governance.immediate_review',
            'Verify immediate exact-call authorization and migrations, and explicitly accept no governance notice window')
        recovery=g.proof(governance.get('parking_rehearsal'),path+'.governance.parking_rehearsal')
        g.check(all(recovery.get(key) is True for key in ('independent','oracle_independent_close_tested',
            'close_only_minimums_tested','governance_pause_nonce_tested','oracle_guarded_resume_tested',
            'parked_rewards_and_migration_tested')),path+'.governance.parking_rehearsal','recovery.review',
            'Require independent current-source parking/resume rehearsal: exact raw close bounds, immediate governance/pause/snapshot/nonce, preserved claims and migration')
        constructor=g.obj(chain.get('constructor'),path+'.constructor')
        g.check(constructor.get('canonical_chain_id')==home and type(constructor.get('canonical_chain_id')) is int,
            path+'.constructor.canonical_chain_id','canonical.mismatch','Every vault must share the canonical chain ID')
        recipient=g.hex(constructor.get('mint_proceeds_recipient'),path+'.constructor.mint_proceeds_recipient',20)
        constructor['mint_proceeds_recipient']=recipient
        g.check(not set(canonical_factories).intersection((activation_address,entry_address,budget_address,pair_address,recipient)),
            cp,'canonical.factory','Factories cannot alias other helpers or the mint recipient')
        g.check(recipient not in addresses,path+'.constructor.mint_proceeds_recipient','mint.custody','Mint proceeds must stay outside protocol custody/reward modules')
        g.check(recipient not in (activation_address,entry_address,budget_address,pair_address),path+'.constructor.mint_proceeds_recipient','mint.custody',
            'Mint proceeds cannot be sent to noncustodial helpers')
        g.proof(constructor.get('recipient_payment_evidence'),path+'.constructor.recipient_payment_evidence')
        g.text(constructor.get('nft_base_uri'),path+'.constructor.nft_base_uri')
        if cid==home:
            np=path+'.nft_inventory';nft=g.obj(chain.get('nft_inventory'),np)
            nft_address=modules['nft'].get('address')
            artwork_base=constructor.get('nft_base_uri')
            g.check(isinstance(artwork_base,str) and re.fullmatch(
                r'(?:ipfs://(?:Qm[1-9A-HJ-NP-Za-km-z]{44}|b[a-z2-7]{20,})|ar://[A-Za-z0-9_-]{43})/(?:[^\s"<>]*/)?',artwork_base) is not None,
                path+'.constructor.nft_base_uri','nft.artwork','Production artwork must use a reviewed IPFS/Arweave content root and trailing slash')
            helper_addresses=[]
            for name in ('royalty_rewards','metadata_renderer','claim_router'):
                hp=np+'.'+name;helper=g.obj(nft.get(name),hp)
                helper_address=g.hex(helper.get('address'),hp+'.address',20);helper_addresses.append(helper_address)
                g.hex(helper.get('runtime_hash'),hp+'.runtime_hash')
                g.check(helper_address is not None and helper_address not in addresses and helper_address!=recipient and
                    helper_address not in (activation_address,entry_address,budget_address,pair_address),
                    hp+'.address','nft.helper','NFT-owned helpers must be distinct from modules and the mint recipient')
                g.check(helper.get('immutable') is True,hp+'.immutable','nft.helper','NFT helper addresses must be immutable constructor bindings')
                review=g.proof(helper.get('review_evidence'),hp+'.review_evidence')
                g.check(review.get('independent') is True,hp+'.review_evidence','nft.review','Independent helper admission review is required')
                if name in ('royalty_rewards','claim_router'):
                    g.check(helper.get('nft')==nft_address and nft_address is not None,
                        hp+'.nft','nft.binding','The NFT-owned claim/royalty helper must bind the canonical NFT')
                else:
                    g.check(helper.get('controller')==modules['access'].get('address') and helper.get('controller') is not None,
                        hp+'.controller','nft.binding','The metadata renderer must bind the reviewed access controller')
                if name=='claim_router':
                    g.check(helper.get('controller')==modules['access'].get('address') and helper.get('controller') is not None and
                        helper.get('royalties')==helper_addresses[0] and helper_addresses[0] is not None and
                        type(helper.get('max_claims')) is int and helper.get('max_claims')==32,
                        hp,'nft.binding','Claim router must bind the canonical access/royalty ledger and the 32-operation bound')
            g.check(len(set(helper_addresses))==len(helper_addresses),np,'nft.helper','NFT helper implementations must be distinct')
            g.check(not set(canonical_factories).intersection(helper_addresses),np,'canonical.factory',
                'Factory implementations cannot alias NFT-owned ledgers, renderer or router')
            g.check(type(nft.get('observed_chain_id')) is int and nft.get('observed_chain_id')==cid and
                type(nft.get('observed_block_number')) is int and nft.get('observed_block_number')==observed.get('number') and
                nft.get('observed_block_hash')==observed.get('hash'),np,'nft.observation',
                'NFT/helper code and bindings must be observed at the exact confirmed inventory block')
            bindings=g.obj(nft.get('observed_bindings'),np+'.observed_bindings')
            g.check(bindings.get('nft')==nft_address and nft_address is not None and
                bindings.get('royaltyRewards')==helper_addresses[0] and bindings.get('metadataRenderer')==helper_addresses[1] and
                bindings.get('claimRouter')==helper_addresses[2] and helper_addresses[2] is not None and
                bindings.get('claimRouterNft')==nft_address and bindings.get('claimRouterController')==modules['access'].get('address') and
                bindings.get('claimRouterRoyalties')==helper_addresses[0] and type(bindings.get('MAX_CLAIMS')) is int and bindings.get('MAX_CLAIMS')==32 and
                bindings.get('artworkBaseURI')==artwork_base and isinstance(artwork_base,str) and
                bindings.get('royaltyReceiver')==helper_addresses[0] and
                type(bindings.get('royaltyBps')) is int and bindings.get('royaltyBps')==500,
                np+'.observed_bindings','nft.binding','Observed NFT getters and ERC-2981 royaltyInfo must match immutable helpers and the 5% royalty rate')
            ap=np+'.artwork_publication';artwork=g.obj(nft.get('artwork_publication'),ap)
            manifest_hash=g.hex(artwork.get('manifest_sha256'),ap+'.manifest_sha256',prefix=False)
            files=g.items(artwork.get('asset_paths'),ap+'.asset_paths')
            g.check(artwork.get('base_uri')==artwork_base and isinstance(artwork_base,str) and
                g.num(artwork.get('asset_count'),ap+'.asset_count',1)==len(ARTWORK_FILES) and len(files)==len(ARTWORK_FILES) and
                all(isinstance(value,str) for value in files) and set(files)==set(ARTWORK_FILES),
                ap,'nft.artwork','Content publication must inventory exactly the 2,784 supported 58-palette/four-pattern/three-rarity/four-evolution SVG paths')
            publication=g.proof(artwork.get('review_evidence'),ap+'.review_evidence')
            g.check(publication.get('independent') is True and publication.get('kind')=='content_addressed_artwork_review' and
                publication.get('base_uri')==artwork_base and isinstance(artwork_base,str) and
                publication.get('asset_manifest_sha256')==manifest_hash and manifest_hash is not None,
                ap+'.review_evidence','nft.artwork_review','Independent publication evidence must pin the reviewed content root and exact asset manifest hash')
            rp=np+'.royalty_assets';royalty_assets=g.obj(nft.get('royalty_assets'),rp)
            asset_count=g.num(royalty_assets.get('asset_count'),rp+'.asset_count',1,17)
            asset_records=g.items(royalty_assets.get('assets'),rp+'.assets')
            g.check(asset_count==len(asset_records) and royalty_assets.get('complete_admission_history') is True,
                rp,'nft.royalty_assets','Native plus at most sixteen ERC20 royalty assets require a complete assetCount/assets/isAsset admission inventory')
            g.proof(royalty_assets.get('observation_evidence'),rp+'.observation_evidence')
            seen_assets=set()
            for ai,item in enumerate(asset_records):
                asp=rp+f'.assets[{ai}]';asset=g.obj(item,asp)
                token=g.hex(asset.get('address'),asp+'.address',20,zero=True)
                g.check(token is not None and token not in seen_assets and (ai!=0 or token==ZERO),
                    asp,'nft.royalty_assets','Royalty assets must be unique and native ETH must be the first admitted asset')
                seen_assets.add(token)
                g.check(asset.get('observed_asset')==token and token is not None and asset.get('observed_is_asset') is True,
                    asp,'nft.royalty_assets','Observed assets(index) and isAsset(asset) must match each admitted royalty asset at the inventory block')
                decimals=g.num(asset.get('decimals'),asp+'.decimals',0,18)
                if token==ZERO:
                    g.check(ai==0 and asset.get('kind')=='native' and decimals==18 and asset.get('runtime_hash') is None,
                        asp,'nft.royalty_assets','Native ETH is the default first asset, with 18 decimals and no ERC20 runtime hash')
                else:
                    g.hex(asset.get('runtime_hash'),asp+'.runtime_hash')
                    g.check(asset.get('kind')=='erc20' and asset.get('non_rebasing') is True and asset.get('transfer_tax') is False,
                        asp,'nft.royalty_asset_semantics','Only independently reviewed conventional non-rebasing, exact-transfer ERC20 royalty assets may be admitted')
                admission=g.proof(asset.get('admission_evidence'),asp+'.admission_evidence')
                g.check(admission.get('independent') is True and admission.get('kind')=='royalty_asset_admission' and
                    admission.get('asset')==token and token is not None and type(admission.get('chain_id')) is int and
                    admission.get('chain_id')==cid and admission.get('exact_transfers_reviewed') is True and
                    admission.get('authority_risks_reviewed') is True and admission.get('activation_griefing_reviewed') is True,
                    asp+'.admission_evidence','nft.royalty_asset_review','Independent exact-chain asset admission must review exact transfers, upgrade/authority risks and cross-asset activation griefing')
            maximum=g.num(bindings.get('MAX_SUPPLY'),np+'.observed_bindings.MAX_SUPPLY',1)
            minted=g.num(bindings.get('mintedCount'),np+'.observed_bindings.mintedCount',0,1000)
            next_ordinal=g.num(bindings.get('nextToFinalize'),np+'.observed_bindings.nextToFinalize',1,1001)
            remaining=g.num(bindings.get('remainingToReveal'),np+'.observed_bindings.remainingToReveal',0,1000)
            quotas=g.items(bindings.get('rarityRemaining'),np+'.observed_bindings.rarityRemaining')
            remaining_counts=[g.num(value,f'{np}.observed_bindings.rarityRemaining[{i}]',0) for i,value in enumerate(quotas)]
            g.check(maximum==1000 and minted is not None and next_ordinal is not None and remaining is not None and
                len(remaining_counts)==3 and all(value is not None and value<=limit for value,limit in zip(remaining_counts,(600,300,100))) and
                sum(remaining_counts)==remaining and next_ordinal==1000-remaining+1 and minted>=1000-remaining,
                np+'.observed_bindings','nft.quotas','Observed supply and remaining rarity quotas must conserve the exact 1000 NFT / 600 Commun / 300 Rare / 100 Legendary policy and mint-order finalization')
            rp=np+'.randomness';randomness=g.obj(nft.get('randomness'),rp)
            coordinator=g.hex(randomness.get('coordinator'),rp+'.coordinator',20)
            g.hex(randomness.get('runtime_hash'),rp+'.runtime_hash')
            key_hash=g.hex(randomness.get('keyHash'),rp+'.keyHash')
            subscription=g.num(randomness.get('subscriptionId'),rp+'.subscriptionId',1)
            confirmations=g.num(randomness.get('requestConfirmations'),rp+'.requestConfirmations',3,200)
            callback_gas=g.num(randomness.get('callbackGasLimit'),rp+'.callbackGasLimit',200000,10000000)
            native=randomness.get('nativePayment')
            g.check(type(native) is bool,rp+'.nativePayment','nft.randomness','Native-payment mode must be selected explicitly')
            g.check(randomness.get('immutable_provider_configuration') is True and
                randomness.get('mutable_request_parameters')==['requestConfirmations','callbackGasLimit'] and
                'immutable_configuration' not in randomness and randomness.get('no_admin_reroll') is True,
                rp,'nft.randomness','Fixed coordinator/lane/subscription/payment policy, bounded future-request tuning and absence of a privileged reroll must be reviewed')
            g.check(bindings.get('randomnessConfigured') is True and bindings.get('randomnessCoordinator')==coordinator and coordinator is not None and
                bindings.get('keyHash')==key_hash and key_hash is not None and
                g.num(bindings.get('subscriptionId'),np+'.observed_bindings.subscriptionId',1)==subscription and
                g.num(bindings.get('requestConfirmations'),np+'.observed_bindings.requestConfirmations',3,200)==confirmations and
                g.num(bindings.get('callbackGasLimit'),np+'.observed_bindings.callbackGasLimit',200000,10000000)==callback_gas and
                type(bindings.get('nativePayment')) is bool and bindings.get('nativePayment')==native,
                rp,'nft.randomness','Observed NFT randomness getters must match the reviewed provider configuration and current future-request settings')
            review=g.proof(randomness.get('review_evidence'),rp+'.review_evidence')
            g.check(review.get('independent') is True and review.get('kind')=='verified_randomness_coordinator_review' and
                type(review.get('chain_id')) is int and review.get('chain_id')==cid and review.get('coordinator')==coordinator and coordinator is not None,
                rp+'.review_evidence','nft.randomness_review','An independent exact-chain coordinator/funding/security review is required; coordinator availability cannot be assumed')
            staged=g.proof(randomness.get('integration_evidence'),rp+'.integration_evidence')
            g.check(staged.get('kind')=='coordinator_staged_randomness' and type(staged.get('chain_id')) is int and staged.get('chain_id')==cid and
                staged.get('coordinator')==coordinator and coordinator is not None and staged.get('nft')==nft_address and nft_address is not None,
                rp+'.integration_evidence','nft.randomness_staging','Actual staged coordinator fulfillment must identify this chain, coordinator and canonical NFT; mock/model evidence is insufficient')
            g.num(staged.get('fulfilled_request_id'),rp+'.integration_evidence.fulfilled_request_id',1)
            g.num(staged.get('finalized_token_id'),rp+'.integration_evidence.finalized_token_id',1)
            g.proof(nft.get('observation_evidence'),np+'.observation_evidence')
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
            g.hex(sequencer.get('active_policy_id'),path+'.sequencer.active_policy_id')
            g.num(sequencer.get('policy_count'),path+'.sequencer.policy_count',1)
            sp=g.obj(sequencer.get('observed_policy'),path+'.sequencer.observed_policy')
            g.hex(sp.get('review_hash'),path+'.sequencer.observed_policy.review_hash')
            g.check(sp.get('source')==sequencer.get('address') and sp.get('expected_code_hash')==sequencer.get('runtime_hash') and
                type(sp.get('bootstrap_admission')) is bool,path+'.sequencer','sequencer.binding',
                'Observe the active append-only sequencer source policy and exact runtime pin')
            replacement=g.proof(sequencer.get('replacement_review'),path+'.sequencer.replacement_review')
            g.check(replacement.get('independent') is True and replacement.get('failed_source_replacement_tested') is True and
                replacement.get('zero_bypass_disabled') is True,path+'.sequencer.replacement_review','sequencer.recovery',
                'Review immediate governance-authorized failed-source replacement, retained uptime/grace checks and forbidden zero-feed bypass')
        else:g.check(sequencer.get('address')==ZERO and sequencer.get('active_policy_id')=='0x'+'00'*32 and
            type(sequencer.get('policy_count')) is int and sequencer.get('policy_count')==0,
            path+'.sequencer.address','sequencer.address','No-feed mode requires the initial zero-source state with no admitted policy')
        g.check(sequencer.get('observed_oracle_feed')==sequencer.get('address') and sequencer.get('address') is not None,
            path+'.sequencer','sequencer.binding','Observe Oracle.sequencerFeed at the exact inventory block')
        g.proof(sequencer.get('review'),path+'.sequencer.review')
        pools={}
        for pi,item in enumerate(g.items(chain.get('pools'),path+'.pools')):
            pp=path+f'.pools[{pi}]';pool=g.obj(item,pp);pid=g.hex(pool.get('pool_id'),pp+'.pool_id')
            t0=g.hex(pool.get('currency0'),pp+'.currency0',20);t1=g.hex(pool.get('currency1'),pp+'.currency1',20)
            fee=g.num(pool.get('fee'),pp+'.fee',0 if reward_model=='external_funded_revenue' else 1,100000)
            spacing=g.num(pool.get('tickSpacing'),pp+'.tickSpacing',1,32767)
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
                g.check(bounds['minDepositUSD']<=100*10**18<=bounds['maxPositionUSD'],
                    pp,'pool.activation_minimum','Admitted pool contribution bounds must allow the advertised $100 activation')
            g.check(pool.get('depositsEnabled') is True and pool.get('operationsEnabled') is True,pp,'pool.disabled','The release pool must explicitly enable reviewed deposits and operations')
            if None not in (t0,t1,fee,spacing) and pool.get('hooks')==ZERO:
                g.check(pid==identity([(t0,'address'),(t1,'address'),(fee,'uint24'),(spacing,'uint24'),(ZERO,'address')]),pp+'.pool_id','pool.identity','Pool ID must hash the complete PoolKey')
            pool['currency0']=t0;pool['currency1']=t1
            if pid:g.check(pid not in pools,pp+'.pool_id','pool.duplicate','Pool IDs must be unique');pools[pid]=pool
        pool_ids[cid]=pools
    g.check(home in chains,'canonical_chain_id','canonical.absent','Canonical chain must be present in the inventory')
    total_receivers=0
    for cid,chain in chains.items():
        path=f'chains[{cid}].external_rewards'
        external=chain.get('external_rewards')
        if external is None:
            if reward_model=='external_funded_revenue' and cid==home:
                g.check(False,path,'reward.inventory','External funding requires the canonical receiver inventory and exact-block observations')
            continue
        external=g.obj(external,path)
        # One immutable receiver per home bucket; the Vault's combined-workload
        # cap of four is tighter than the receiver factory's independent limit.
        count=g.num(external.get('receiver_count'),path+'.receiver_count',0,4)
        records=g.items(external.get('receivers'),path+'.receivers',required=False)
        g.check(count==len(records),path,'reward.inventory','Count must match complete verified RewardReceiverCreated history and current receiver getters')
        g.proof(external.get('observation_evidence'),path+'.observation_evidence')
        g.check(cid==home or not records,path,'reward.canonical','External receiver funding is canonical-only; satellites use authenticated reward transport')
        if reward_model!='external_funded_revenue':
            g.check(not records,path,'reward.model','Declare external_funded_revenue when registered receivers may accept payments')
        seen_receivers=set();seen_buckets=set()
        modules=chain.get('modules',{});fees=modules.get('fees',{}).get('address')
        vault=modules.get('vault',{}).get('address')
        observed=chain.get('observed_block') if isinstance(chain.get('observed_block'),dict) else {}
        for index,item in enumerate(records):
            rp=path+f'.receivers[{index}]';record=g.obj(item,rp)
            receiver=g.hex(record.get('address'),rp+'.address',20)
            g.hex(record.get('runtime_hash'),rp+'.runtime_hash')
            bucket=g.num(record.get('bucket_id'),rp+'.bucket_id',1)
            origin=g.hex(record.get('home_pool_id'),rp+'.home_pool_id')
            token0=g.hex(record.get('token0'),rp+'.token0',20)
            token1=g.hex(record.get('token1'),rp+'.token1',20)
            wrapper=g.hex(record.get('wrapped_native'),rp+'.wrapped_native',20,zero=True)
            bound_fees=g.hex(record.get('fees'),rp+'.fees',20)
            pool=pool_ids.get(home,{}).get(origin,{})
            g.check(cid==home and bound_fees is not None and bound_fees==fees,
                rp,'reward.binding','Receiver must bind the canonical fee controller')
            g.check(bool(pool) and (token0,token1)==(pool.get('currency0'),pool.get('currency1')),
                rp,'reward.assets','Immutable receiver currencies must match the original canonical pool and admitted assets')
            computed=None
            lineage=chain.get('canonical_handoff') if isinstance(chain.get('canonical_handoff'),dict) else {}
            origin_chain=lineage.get('origin_chain_id');origin_vault=lineage.get('origin_vault')
            if type(origin_chain) is int and origin_vault is not None and origin is not None:
                computed=int(identity([(origin_chain,'uint256'),(origin_vault,'address'),(origin,'bytes32')]),16)
            g.check(bucket is not None and computed==bucket,rp+'.bucket_id','reward.bucket',
                'Receiver bucket must hash canonical chain, vault and permanent original home pool')
            g.check(receiver not in seen_receivers and bucket not in seen_buckets,rp,'reward.duplicate',
                'One immutable receiver per canonical bucket; addresses and buckets must be unique')
            seen_receivers.add(receiver);seen_buckets.add(bucket)
            constructor=chain.get('constructor') if isinstance(chain.get('constructor'),dict) else {}
            nft_inventory=chain.get('nft_inventory') if isinstance(chain.get('nft_inventory'),dict) else {}
            nft_helpers=[helper_record.get('address') for helper_record in
                (nft_inventory.get('royalty_rewards'),nft_inventory.get('metadata_renderer'),nft_inventory.get('claim_router')) if isinstance(helper_record,dict)]
            activation_record=chain.get('activation_assets') if isinstance(chain.get('activation_assets'),dict) else {}
            entry_record=chain.get('activation_entry') if isinstance(chain.get('activation_entry'),dict) else {}
            budget_record=chain.get('migration_budget') if isinstance(chain.get('migration_budget'),dict) else {}
            pair_record=chain.get('pair_migration') if isinstance(chain.get('pair_migration'),dict) else {}
            factories=[lineage.get(name,{}).get('address') for name in ('royalty_factory','reward_receiver_factory')
                if isinstance(lineage.get(name),dict)]
            g.check(receiver not in [m.get('address') for m in modules.values() if isinstance(m,dict)] and
                receiver not in nft_helpers and receiver!=constructor.get('mint_proceeds_recipient') and
                receiver not in (activation_record.get('address'),entry_record.get('address'),budget_record.get('address'),pair_record.get('address')) and
                receiver not in factories,rp+'.address','reward.custody',
                'Reward receivers must be separate from modules, immutable helpers and the mint-proceeds recipient')
            g.check(record.get('immutable_configuration') is True and record.get('upgradeable') is False,
                rp,'reward.mutable','Receiver code and bucket/currency/wrapper bindings must be immutable and reviewed')
            g.check(type(record.get('observed_chain_id')) is int and record.get('observed_chain_id')==cid and
                record.get('observed_receiver')==receiver and record.get('observed_fee_receiver')==receiver and
                type(record.get('observed_block_number')) is int and record.get('observed_block_number')==observed.get('number') and
                record.get('observed_block_hash')==observed.get('hash'),rp,'reward.observation',
                'Receiver code/getters and Fees.rewardReceiver(bucket) must be observed at the exact confirmed inventory block')
            bindings=g.obj(record.get('observed_bindings'),rp+'.observed_bindings')
            observed_bucket=g.num(bindings.get('bucket_id'),rp+'.observed_bindings.bucket_id',1)
            g.num(record.get('observed_total_shares'),rp+'.observed_total_shares',1)
            g.check(observed_bucket==bucket and all(bindings.get(key)==value for key,value in
                {'fees':bound_fees,'token0':token0,'token1':token1,'wrapped_native':wrapper}.items()),
                rp+'.observed_bindings','reward.observation','Observed immutable getters must match every reviewed receiver binding')
            review=g.proof(record.get('review_evidence'),rp+'.review_evidence')
            g.check(review.get('independent') is True,rp+'.review_evidence','reward.review','An independent receiver/wrapper admission review is required')
            g.text(review.get('reviewer'),rp+'.review_evidence.reviewer')
            if wrapper is not None and wrapper!=ZERO:
                wrapped=token_maps.get(home,{}).get(wrapper,{})
                g.check(wrapper in (token0,token1) and wrapped.get('decimals')==18,
                    rp+'.wrapped_native','reward.wrapper','Native wrapping requires an admitted 18-decimal original pool currency')
                wr=g.obj(record.get('wrapper_review'),rp+'.wrapper_review')
                code=g.hex(wr.get('runtime_hash'),rp+'.wrapper_review.runtime_hash')
                token_code=wrapped.get('runtime_hash')
                g.check(wr.get('address')==wrapper and code is not None and isinstance(token_code,str) and code==token_code.lower() and
                    wr.get('upgradeable') is False and wr.get('conversion')=='deposit:exact_1_to_1',
                    rp+'.wrapper_review','reward.wrapper','Review immutable one-for-one native deposit behavior and the exact inventoried wrapper runtime')
                g.proof(wr.get('evidence'),rp+'.wrapper_review.evidence')
            else:g.check(record.get('wrapper_review') is None,rp+'.wrapper_review','reward.wrapper','An ERC20-only receiver must not declare native wrapping')
        total_receivers+=len(records) if cid==home else 0
    if reward_model=='external_funded_revenue':
        g.check(total_receivers>0,'economics.reward_model','reward.inventory','External revenue mode requires at least one independently reviewed canonical receiver')
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
            canonical_vault=chains.get(home,{}).get('canonical_handoff',{}).get('origin_vault')
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
    return {'schema_version':4,'status':'blocked' if g.issues else 'ready','ready':not g.issues,
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
        result={'schema_version':4,'status':'blocked','ready':False,'deployment_authorized':False,
            'issues':[{'code':'config.unreadable','path':'config','message':type(exc).__name__}]}
    encoded=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.output:Path(args.output).write_text(encoded,encoding='utf-8')
    print(encoded,end='');return 0 if result['ready'] else 1

if __name__=='__main__':sys.exit(main())
