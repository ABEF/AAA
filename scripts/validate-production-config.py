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
    'compounder','buyback','migration','bridge','receiver','oracle','pools','routes')
EVIDENCE = ('toolchain','static_analysis','invariants','uniswap_fork','multi_chain',
    'staging','operations_recovery','gas_benchmarks','deployment_review','economic_approval',
    'independent_audit','remediation')
ROUTE_FIELDS = (('sourceChain','uint256'),('sourceAdapter','address'),('sourceVault','address'),
    ('sourceReceiver','address'),('destinationChain','uint256'),('destinationAdapter','address'),
    ('destinationVault','address'),('destinationReceiver','address'),('destinationPool','bytes32'),
    ('sourceToken0','address'),('sourceToken1','address'),('destinationToken0','address'),
    ('destinationToken1','address'),('token0Decimals','uint8'),('token1Decimals','uint8'))

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
    g.check(config.get('schema_version')==1 and type(config.get('schema_version')) is int,
        'schema_version','schema.unsupported','Only schema version 1 is supported')
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
    audit=g.obj(evidence.get('independent_audit'),'evidence.independent_audit')
    g.text(audit.get('auditor'),'evidence.independent_audit.auditor')
    g.check(audit.get('independent') is True,'evidence.independent_audit.independent','audit.internal','An independent external audit is required')
    g.check(audit.get('kind')=='external_security_audit','evidence.independent_audit.kind','audit.internal','An AI/internal review cannot fulfill the external audit gate')
    for level in ('critical','high'):
        g.check(g.num(audit.get('open_'+level),'evidence.independent_audit.open_'+level)==0,
            'evidence.independent_audit.open_'+level,'audit.unresolved','No unresolved critical/high findings may remain')
    chains={};pool_ids={};token_maps={}
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
        dependencies=g.obj(chain.get('dependencies'),path+'.dependencies')
        for name in ('position_manager','state_view','pool_manager','permit2','zzz','transport'):
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
        transport=dependencies.get('transport',{})
        g.text(transport.get('provider'),path+'.dependencies.transport.provider')
        for key in ('immutable_endpoint','authenticated_delivery','funded_equivalent_assets','nonce_domain_replay_protection','finality_and_retries_reviewed'):
            g.check(transport.get(key) is True,path+'.dependencies.transport.'+key,'transport.incomplete','Reviewed production transport semantics are required')
        g.proof(transport.get('integration_evidence'),path+'.dependencies.transport.integration_evidence')
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
    routes=[];seen=set()
    for ri,item in enumerate(g.items(config.get('routes'),'routes')):
        rp=f'routes[{ri}]';route=g.obj(item,rp);values={}
        for key,typ in ROUTE_FIELDS:
            values[key]=g.hex(route.get(key),rp+'.'+key,20,zero=key.startswith(('sourceToken','destinationToken'))) if typ=='address' else \
                g.hex(route.get(key),rp+'.'+key,zero=True) if typ=='bytes32' else g.num(route.get(key),rp+'.'+key,0 if typ=='uint8' else 1,18 if typ=='uint8' else 2**256-1)
        rid=g.hex(route.get('route_id'),rp+'.route_id');g.check(rid not in seen,rp+'.route_id','route.replay','Append-only route identities must not be duplicated');seen.add(rid)
        if all(value is not None for value in values.values()):
            g.check(rid==identity([(values[key],typ) for key,typ in ROUTE_FIELDS]),rp+'.route_id','route.identity','Route ID must hash every immutable Route field')
            source=values['sourceChain'];destination=values['destinationChain']
            g.check(source!=destination and source in chains and destination in chains,rp,'route.chain','Distinct inventoried source/destination chains are required')
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
                g.check(any((p.get('currency0'),p.get('currency1'))==(values['sourceToken0'],values['sourceToken1']) for p in pool_ids.get(source,{}).values()),rp,'route.source_pool','Principal source tokens must match source PoolKey ordering')
                if source!=home and destination!=home:
                    g.proof(route.get('canonical_graph_evidence'),rp+'.canonical_graph_evidence')
            g.check(route.get('enabled') is True,rp+'.enabled','route.disabled','Release routes must explicitly be enabled')
        route.update(values)
        g.proof(route.get('asset_and_authority_evidence'),rp+'.asset_and_authority_evidence');routes.append(route)
    for route in routes:
        if route.get('kind')=='principal':
            reverse=[r for r in routes if r.get('sourceChain')==route.get('destinationChain') and r.get('destinationChain')==route.get('sourceChain')]
            g.check(any(r.get('kind')=='ack' for r in reverse),'routes','route.ack_missing','Every principal hop needs a reviewed source-completion ACK route')
            if route.get('destinationChain')!=home:
                if route.get('sourceChain')!=home:
                    g.check(any(r.get('kind')=='ack' and r.get('sourceChain')==route.get('destinationChain') and r.get('destinationChain')==home for r in routes),
                        'routes','route.home_ack_missing','Onward satellite hops also require a canonical-location ACK route')
                for slot in (0,1):
                    token=route.get(f'destinationToken{slot}')
                    g.check(any(r.get('kind')=='reward' and r.get('sourceChain')==route.get('destinationChain') and r.get('destinationChain')==home and r.get('sourceToken0')==token for r in routes),
                        'routes','route.rewards_missing','Satellite principal assets need funded reward paths to the canonical chain')
    return {'schema_version':1,'status':'blocked' if g.issues else 'ready','ready':not g.issues,
        'release_commit':g.commit,'deployment_authorized':False,'issues':g.issues,
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
