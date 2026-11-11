"""Active-state B/C/D preparation for direct empty-code governance EOAs only.

No signing, journal access, generic call targets, guessed floors, force fallback,
deadline extension or execution approval. Configured runtime pins still require
reviewed source/build/deployment provenance and actual provider qualification.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time

from frontend_api.service import Projection, ZERO, _bool
from keeper.compound_policy import observe as physical_portfolio
from zzz_ops import operator_review as offline
from zzz_ops.abi import address, keccak256, calldata, decode_words
from zzz_ops.errors import RpcError
from zzz_ops.position import decode_position
from zzz_ops.protocol_policy import observe as policy_observation
from zzz_ops.tick_math import MIN_TICK, MAX_TICK
from zzz_ops.work_budget import Budget, request_scope, expire_at
from keeper.monitor import rpc_quantity, rpc_hash

MAX_CALLS=768
MAX_SECONDS=25
MAX_GAS=64_000_000  # Engineering bound, never target-chain qualification.
EXTRAS={'oracle','fees','activation_assets','custody_validation','contribution_pricing'}
TUPLE='(uint256,bytes32,uint8,int24,int24,bytes32,bool,uint128,uint128,uint128,uint256,bytes32)'
FIELDS=('bucket','custodyHash','checks','lower','upper','swapPool','zeroForOne','amountIn',
        'minimumOut','minimumLiquidity','deadline','reviewHash')


class UnsupportedGovernanceEnvelope(ValueError):
    """Contract/delegated wallets require a separately prepared outer envelope."""


def digest(value):return hashlib.sha256(offline.canonical(value)).hexdigest()


def integer(value, *, bits=256, signed=False, positive=False):
    offline._integer(value,bits,signed=signed,positive=positive)
    return int(value)


def selection(raw):
    offline._keys(raw,{'schema','action','bucket','checks','lower','upper','swapPool','zeroForOne',
        'amountIn','minimumOut','minimumLiquidity','deadline','review_notes_sha256','evidence_sha256'})
    if type(raw['schema']) is not int or raw['schema']!=1 or raw['action'] not in ('B','C','D'):
        raise ValueError('Select exactly Active-state manual action B, C or D')
    result=copy.deepcopy(raw)
    for field,bits,signed,positive in [('bucket',256,False,True),('checks',8,False,False),
            ('lower',24,True,False),('upper',24,True,False),('amountIn',128,False,False),
            ('minimumOut',128,False,False),('minimumLiquidity',128,False,True),('deadline',256,False,True)]:
        result[field]=integer(raw[field],bits=bits,signed=signed,positive=positive)
    offline._hex(raw['swapPool'],32)
    offline._hex(raw['review_notes_sha256'],32,nonzero=True,prefix=False)
    evidence=raw['evidence_sha256']
    if not isinstance(evidence,list) or not 1<=len(evidence)<=15 or len(set(evidence))!=len(evidence):
        raise ValueError('Select one through fifteen distinct evidence hashes')
    for value in evidence:offline._hex(value,32,nonzero=True,prefix=False)
    if (type(raw['zeroForOne']) is not bool or result['checks']>31 or
            not MIN_TICK<=result['lower']<result['upper']<=MAX_TICK or
            max(result['amountIn'],result['minimumOut'])>=1<<127):
        raise ValueError('Manual request exceeds supported exact bounds')
    swap=result['amountIn']>0
    if (swap and (int(raw['swapPool'],16)==0 or result['minimumOut']==0) or
            not swap and (int(raw['swapPool'],16)!=0 or result['minimumOut']!=0 or raw['zeroForOne'])):
        raise ValueError('Explicit swap fields are inconsistent')
    if raw['action']=='B' and (result['checks']!=14 or swap):
        raise ValueError('Guarded B requires checks14 and no explicit swap')
    return result


def encode(request, action):
    """One static typed tuple; no arbitrary selector, dynamic offsets or target."""
    signature=('emergencyRebalance('+TUPLE+')' if action=='D' else 'consolidateResidual('+TUPLE+',bool)')
    values=[request[field] for field in FIELDS]
    words=[]
    for value in values:
        number=int(value,16) if isinstance(value,str) and value.startswith('0x') else int(value)
        words.append(f'{number%(1<<256):064x}')
    if action!='D':words.append(f'{int(action=="C"):064x}')
    return signature,'0x'+keccak256(signature.encode()).hex()[:8]+''.join(words)


def controls(snapshot):
    """Price rounds and physical composition can move without changing consent."""
    result=copy.deepcopy(snapshot)
    result['physical'].pop('portfolio_amounts',None)
    result['financial'].pop('price_bounds',None)
    result['timing'].pop('raw_trigger',None)
    if result['swap'] is not None:result['swap'].pop('available_principal_raw',None)
    return result


def simulation(p,header,block,transaction,fee,*,confirmed):
    """One exact full call and estimate, bounded by this canonical block's gas."""
    raw=p.rpc.call('eth_getBlockByNumber',[hex(header['number']),False])
    if (not isinstance(raw,dict) or rpc_quantity(raw.get('number'),'manual block number')!=header['number'] or
            rpc_hash(raw.get('hash'),'manual block hash')!=header['hash'] or
            rpc_quantity(raw.get('timestamp'),'manual block timestamp',minimum=1)!=header['timestamp']):
        raise RpcError('Manual simulation header changed')
    block_limit=rpc_quantity(raw.get('gasLimit'),'manual block gas limit',minimum=21000)
    cap=min(integer(fee['max_gas_limit'],positive=True),block_limit)
    tx={**transaction,'gas':hex(cap)}
    if p.rpc.call('eth_call',[tx,block])!='0x':raise RpcError('Manual void simulation returned unexpected data')
    estimate=rpc_quantity(p.rpc.call('eth_estimateGas',[tx,block]),'manual estimated gas',minimum=21000)
    padded=(estimate*125+99)//100
    price=rpc_quantity(p.rpc.call('eth_gasPrice',[]),'manual gas price',minimum=1)
    cost=padded*price
    if (padded>cap or price>integer(fee['max_gas_price_wei'],positive=True) or
            cost>integer(fee['max_network_fee_wei'],positive=True)):
        raise RpcError('Manual review exceeds original gas/fee limits')
    balance=rpc_quantity(p.rpc.call('eth_getBalance',[transaction['from'],block]),'manual governance balance')
    if balance<cost:raise RpcError('Governance balance is below the reviewed network fee')
    return {'state':'complete_at_confirmed_snapshot' if confirmed else 'complete_at_canonical_tip',
        'finality':'confirmation_depth_only' if confirmed else 'latest_canonical_only_not_confirmed',
        'header':header,'estimated_gas':str(estimate),
        'padded_gas':str(padded),'gas_limit_cap':str(cap),'block_gas_limit':str(block_limit),
        'gas_price_wei':str(price),'maximum_network_fee_wei':str(cost),'governance_balance_wei':str(balance)}


class Reader:
    def __init__(self,p,extra,block):
        self.p,self.block=p,block
        self.extra=extra
        self.targets={role:item.address for role,item in p.contracts.items()}
        self.targets.update({role:item['address'] for role,item in extra.items()})

    def read(self,role,method,*args,count=1):
        if method=='compoundBalance(uint256,address)' and args[1]==ZERO:
            data=calldata(method,args[0],'0x'+'0'*39+'1')[:-64]+'0'*64
            values=decode_words(self.p.rpc.call('eth_call',[{'to':self.targets[role],'data':data},self.block]))
            if len(values)!=count:raise RpcError('Manual reserve getter ABI differs')
            return values
        return self.p._call(self.targets.get(role,role),method,*args,block=self.block,words=count)

    def uint(self,role,method,*args):return int(self.read(role,method,*args)[0],16)
    def flag(self,role,method,*args):return _bool(self.read(role,method,*args)[0])
    def hashed(self,role,method,*args):
        value='0x'+self.read(role,method,*args)[0]
        return offline._hex(value,32,nonzero=True)

    def binding(self,role,method,expected):
        if self.uint(role,method)!=int(self.targets[expected],16):raise RpcError('Manual helper binding differs')

    def snapshot(self,s,governance,*,full):
        p=self.p;b=s['bucket'];c=self.targets
        execution_prices=None
        if full:
            life=p._verify_deployment(self.block)
            for role,item in self.extra.items():p._code(item['address'],item['code_hash'],self.block)
            for role,label in [('oracle','ZZZOracle'),('fees','ZZZFeeController')]:
                if self.uint('access','module(bytes32)','0x'+keccak256(label.encode()).hex())!=int(c[role],16):
                    raise RpcError('Manual module binding differs')
                self.binding(role,'access()','access')
            for role,method,expected in [('principal_exit','validation()','custody_validation'),
                    ('custody_validation','migration()','principal_exit'),('custody_validation','access()','access'),
                    ('pools','activationAssets()','activation_assets'),('activation_assets','registry()','pools'),
                    ('activation_assets','access()','access'),('oracle','contributionPricing()','contribution_pricing'),
                    ('contribution_pricing','oracle()','oracle'),('contribution_pricing','access()','access')]:
                self.binding(role,method,expected)
            for role in ('principal_exit','vault','budget','portfolio_policy','contribution_pricing'):
                if self.uint(role,'RESIDUAL_REINVEST_VERSION()')!=1:raise RpcError('Manual extension capability differs')
            if self.uint('fees','FEE_INTAKE_VERSION()')!=1:raise RpcError('Manual fee profile differs')
            if p.execution_price_version:
                from zzz_ops.execution_price import observe
                execution_prices=observe(lambda target,method,*,count:self.read(target,method,count=count),c)
        if (not self.flag('access','isSealed()') or not self.flag('access','paused()') or
                self.flag('access','preparationActive()') or self.uint('access','canonicalState()')!=0 or
                self.flag('access','lpExitStarted()') or self.uint('principal_exit','exitPhase()')!=0 or
                self.uint('access','governance()')!=int(governance,16) or not self.flag('access','canConfigure(address)',governance)):
            raise RpcError('Paused current governance and operating pre-exit lifecycle are required')
        governance_code=p.rpc.call('eth_getCode',[governance,self.block])
        if not isinstance(governance_code,str) or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',governance_code) is None:
            raise RpcError('Malformed governance runtime code')
        if governance_code!='0x':
            raise UnsupportedGovernanceEnvelope('unsupported_contract_wallet_envelope: direct empty-code governance EOA required')
        raw=self.read('vault','group(uint256)',b,count=8);position=decode_position(raw,7)
        if position['status']!='active':raise ValueError('Only Active-state manual B/C/D is supported; Parked is unsupported')
        hashes={role:item.code_hash for role,item in p.contracts.items()}
        physical=physical_portfolio(self.read,lambda target:p.rpc.call('eth_getCode',[target,self.block]),
            contracts=c,code_hashes=hashes,bucket=b,accounting_version=7,physical_only=True,
            execution_price_version=p.execution_price_version)
        pool=position['pool_id'];main=position['lp_token_id'];legs=physical['physical_legs']
        config=self.read('pools','accounting(bytes32)',pool,count=14)
        zzz=self.uint('activation_assets','zzz()')
        if (int(config[0],16)!=0 or int(config[1],16)!=zzz or zzz==0 or
                self.uint('principal_exit','currentZZZ()')!=zzz):raise RpcError('Manual fixed asset identity differs')
        asset='0x'+f'{zzz:040x}'
        if asset not in p.assets:raise RpcError('Fixed ZZZ lacks a reviewed asset pin')
        p._code(asset,p.assets[asset].code_hash,self.block)
        if self.uint(asset,'decimals()')!=p.assets[asset].decimals:raise RpcError('Fixed ZZZ decimals differ')
        shares=self.uint('vault','bucketTotalShares(uint256)',b)
        if shares==0:raise RpcError('Manual bucket has no authenticated shares')
        lower,upper=legs[0]['tick_lower'],legs[0]['tick_upper']
        if s['action']!='D' and (s['lower'],s['upper'])!=(lower,upper):
            raise ValueError('Same-main request must keep the exact current ticks')
        spacing=int(config[3],16)
        if s['lower']%spacing or s['upper']%spacing:raise ValueError('Manual ticks do not fit pool spacing')
        if s['action']=='B':
            from zzz_ops.tick_math import decode_slot0
            _,tick,_,_=decode_slot0(self.read('state_view','getSlot0(bytes32)',pool,count=4),expected_fee=int(config[2],16))
            if not lower<=tick<upper:raise RpcError('Guarded same-main requires an active unchanged main')
        if s['action']!='D' and not physical['secondary_id'] and not(position['idle0'] or position['idle1']):
            raise RpcError('Same-main operation has no residual or attributed idle')
        if s['checks']&8 and not _bool(config[6]):raise RpcError('Retained operations flag is disabled')
        reserves=[self.uint('fees','compoundBalance(uint256,address)',b,t) for t in (ZERO,asset)]
        swap=None
        if s['amountIn']:
            swap_config=self.read('pools','accounting(bytes32)',s['swapPool'],count=14)
            if (swap_config[:2]!=config[:2] or int(swap_config[4],16)!=0 or
                    '0x'+keccak256(bytes.fromhex(''.join(swap_config[:5]))).hex()!=s['swapPool']):
                raise RpcError('Explicit swap venue is not the admitted fixed pair')
            if s['checks']&8 and not _bool(swap_config[6]):raise RpcError('Retained swap operations flag is disabled')
            available=[position['idle0'],position['idle1']]
            selected=legs if s['action']=='D' else legs[1:]
            for leg in selected:
                amounts=[int(w,16) for w in self.read('liquidity','amounts(uint256)',leg['lp_token_id'],count=2)]
                available=[a+b for a,b in zip(available,amounts)]
            if s['action']=='D':available=[a+b for a,b in zip(available,reserves)]
            if s['action']!='D' and s['amountIn']>available[0 if s['zeroForOne'] else 1]:
                raise RpcError('Explicit swap exceeds captured attributed operation principal')
            swap={'config':swap_config,'available_principal_raw':list(map(str,available)),
                'availability_scope':('observed_lower_bound_excludes_future_harvest' if s['action']=='D'
                    else 'captured_residual_and_attributed_idle_only'),
                'captured_amount_is_preflight_ceiling':s['action']!='D'}
        financial={'state':'not_retained','price_bounds':None,'maintenance_policy':None}
        if s['checks']&6:
            bounds=[self.read('oracle','priceBounds(address)',token,count=3) for token in (ZERO,asset)]
            for row in bounds:
                if not 0<int(row[0],16)<=int(row[1],16) or int(row[2],16)==0:raise RpcError('Invalid independent price bounds')
            financial.update(state='observed',price_bounds=bounds,
                execution_quality_revision=str(self.uint('strategy','executionQualityRevision()')),
                price_policy_ids=[self.hashed('oracle','activePolicy(address)',token) for token in (ZERO,asset)],
                sequencer_policy='0x'+self.read('oracle','activeSequencerPolicy()')[0])
        if s['checks']&4:
            maintenance=policy_observation(self.read,policy=c['protocol_policy'],access=c['access'],domain='maintenance')
            loss=self.uint('budget','maintenanceLossBps()');additional=self.uint('strategy','additionalLossBps()')
            if max(loss,additional)>1000:raise RpcError('Financial limits exceed fixed ceilings')
            financial.update(maintenance_policy=maintenance,maintenance_loss_bps=loss,additional_loss_bps=additional)
        timing={}
        if s['checks']&1:timing['raw_trigger']=self.flag('strategy','needsRebalance(uint256)',b)
        if s['checks']&16:
            timing['observations']=self.read('rebalance_confirmation','observations(uint256)',b,count=4)
            timing['duration']=self.uint('rebalance_confirmation','duration()')
            timing['max_gap']=self.uint('rebalance_confirmation','maxObservationGap()')
            timing['policy_revision']=self.uint('rebalance_confirmation','policyRevision()')
        routing=None
        if s['action']=='B':
            count=self.uint('balancing_router','executionPoolCount()')
            if count>4:raise RpcError('Unbounded automatic route catalogue')
            routing={'revision':self.uint('balancing_router','executionRevision()'),
                'pools':[self.hashed('balancing_router','executionPoolAt(uint256)',i) for i in range(count)]}
        custody=self.hashed('principal_exit','emergencyCustodyHash(uint256)' if s['action']=='D' else 'consolidationCustodyHash(uint256)',b)
        return {'governance':governance,'governance_code':governance_code,
            'governance_wallet_scope':'direct_empty_code_governance_eoa_only',
            'position_words':raw,'shares':str(shares),'physical':physical,
            'custody_hash':custody,'parking_nonce':str(self.uint('principal_exit','parkingNonce(uint256)',b)),
            'custody_epoch':str(self.uint('principal_exit','custodyEpoch(uint256)',b)),
            'pool_configuration':config,'registry_revision':str(self.uint('pools','configurationRevision()')),
            'portfolio_control':self.hashed('portfolio_policy','controlFingerprint(bytes32)',pool),
            'compound_reserves_raw':list(map(str,reserves)),'financial':financial,'timing':timing,'swap':swap,'routing':routing,
            **({'execution_price':execution_prices} if p.execution_price_version else {})}


def validate_policy(policy,catalog):
    """Authenticate shared manual-review inputs without choosing operating limits."""
    offline._keys(policy,{'schema','projection_sha256','reference_sha256','source_snapshot_sha256',
        'governance','extra_contracts','fee_policy'})
    if type(policy['schema']) is not int or policy['schema']!=1:raise ValueError('Unsupported manual policy schema')
    if (policy['reference_sha256']!=catalog.reference_sha256 or
            policy['source_snapshot_sha256']!=catalog.source_snapshot_sha256):raise ValueError('Manual source/catalog binding differs')
    governance=address(policy['governance']);offline._keys(policy['extra_contracts'],EXTRAS)
    for item in policy['extra_contracts'].values():
        offline._keys(item,{'address','code_hash'});address(item['address']);offline._hex(item['code_hash'],32,nonzero=True)
        if address(item['address'])!=item['address']:raise ValueError('Extra runtime addresses must be canonical lower-case')
    fee=policy['fee_policy'];offline._keys(fee,{'max_gas_limit','max_gas_price_wei','max_network_fee_wei',
        'estimate_includes_all_fees','review_hash'})
    gas=integer(fee['max_gas_limit'],positive=True);integer(fee['max_gas_price_wei'],positive=True)
    integer(fee['max_network_fee_wei'],positive=True);offline._hex(fee['review_hash'],32,nonzero=True)
    if not 21000<=gas<=MAX_GAS or fee['estimate_includes_all_fees'] is not True:raise ValueError('Bounded reviewed complete fee policy is required')
    return governance,fee


def prepare(read_config,policy,request,*,rpc=None,clock=None,catalog=None):
    """Prepare one explicitly selected call, or fail without a partial draft."""
    clock=clock or time.time;catalog=catalog or offline.Catalog()
    input_references=(read_config,policy,request)
    original=[digest(value) for value in input_references]
    config=copy.deepcopy(read_config);policy=copy.deepcopy(policy);s=selection(request)
    governance,fee=validate_policy(policy,catalog)
    with request_scope(Budget(seconds=MAX_SECONDS,calls=MAX_CALLS,posts=1536)):
        p=Projection(config,rpc=rpc,clock=clock)
        if (p.accounting_version,p.custody_version,p.fee_intake_version)!=(7,5,1):raise ValueError('Only explicit accounting7/custody5 is supported')
        if p.identity!=policy['projection_sha256'] or p.max_age>120:raise ValueError('Exact fresh reviewed read configuration required')
        all_targets=[item.address for item in p.contracts.values()]+[item['address'] for item in policy['extra_contracts'].values()]
        if len(set(all_targets))!=len(all_targets):raise ValueError('Manual runtime roles must be distinct')
        header,head,block=p._snapshot();expire_at(min(s['deadline'],header['timestamp']+p.max_age),clock)
        if not header['timestamp']<=s['deadline']<=header['timestamp']+600:raise ValueError('Preserve an original deadline within600seconds')
        reader=Reader(p,policy['extra_contracts'],block)
        snapshot=reader.snapshot(s,governance,full=True)
        commitment=digest({'snapshot':snapshot,'policy_sha256':digest(policy),'configuration_sha256':p.identity,'header':header})
        inputs={field:(s[field] if field=='zeroForOne' else str(s[field])) for field in FIELDS if field not in ('custodyHash','reviewHash')}
        inputs.update(swapPool=s['swapPool'],custodyHash=snapshot['custody_hash'],reviewHash=offline.MARKER)
        signature,_=encode({**inputs,'reviewHash':'0x'+'1'*64},s['action'])
        manifest={'schema':1,'profile':offline.PROFILE,'reference_sha256':catalog.reference_sha256,
            'source_snapshot_sha256':catalog.source_snapshot_sha256,'chain':{'id':str(p.chain),
                'controller':p.contracts['access'].address,'governance':governance,
                'target':p.contracts['principal_exit'].address,'target_runtime_keccak256':p.contracts['principal_exit'].code_hash},
            'snapshot':{'block_number':str(header['number']),'block_hash':header['hash'],'timestamp':str(header['timestamp'])},
            'contract':'ZZZMigration','signature':signature,'arguments':{'request':inputs},
            'review_notes_sha256':s['review_notes_sha256'],'evidence_sha256':s['evidence_sha256']+[commitment]}
        if s['action']!='D':manifest['arguments']['forced']=s['action']=='C'
        review=catalog.prepare(manifest);inputs['reviewHash']=review['review_hash'];signature,data=encode(inputs,s['action'])
        tx={'from':governance,'to':p.contracts['principal_exit'].address,'data':data,'value':'0x0'}
        initial_simulation=simulation(p,header,block,tx,fee,confirmed=True)
        # Controls remain fixed; healthy market motion gets one final exact call
        # at the later canonical tip, with the original floors and deadline.
        final_number=rpc_quantity(p.rpc.call('eth_blockNumber',[]),'manual final head')
        latest=p._header(hex(final_number));p._fresh(latest)
        if latest['number']<head or latest['timestamp']<header['timestamp'] or not latest['timestamp']<=s['deadline']<=latest['timestamp']+600:
            raise RpcError('Manual preparation head retreated or original deadline expired')
        final_block={'blockHash':latest['hash'],'requireCanonical':True}
        final=Reader(p,policy['extra_contracts'],final_block)
        final_snapshot=final.snapshot(s,governance,full=True)
        if controls(final_snapshot)!=controls(snapshot):raise RpcError('Manual custody or governed controls changed')
        final_simulation=simulation(p,latest,final_block,tx,fee,confirmed=False)
        if p._header(hex(latest['number']))!=latest:raise RpcError('Final manual control head changed')
        p._finish(header)
        last_number=rpc_quantity(p.rpc.call('eth_blockNumber',[]),'manual last head')
        last_head=p._header(hex(last_number));p._fresh(last_head)
        if last_number==latest['number'] and last_head!=latest:
            raise RpcError('Final manual control head changed after simulation')
        if (last_number<latest['number'] or last_head['timestamp']<latest['timestamp'] or
                not last_head['timestamp']<=s['deadline']<=last_head['timestamp']+600):
            raise RpcError('Manual original deadline expired after final review')
        if [digest(value) for value in input_references]!=original:raise RpcError('Manual configuration changed during preparation')
        if clock()>=min(s['deadline'],header['timestamp']+p.max_age):raise RpcError('Manual preparation expired')
        return {'schema':1,'kind':'unsigned_manual_lp_preparation','action':s['action'],
            'read_only':True,'production_approved':False,'ready_for_submission':False,
            'governance_wallet_scope':'direct_empty_code_governance_eoa_only',
            'operator_revalidation_required':True,'transaction':{**tx,'chainId':hex(p.chain)},'signature':signature,'arguments':inputs,
            'liquidity_floor_kind':'new_position_liquidity' if s['action']=='D' else 'added_main_liquidity',
            'configuration_sha256':p.identity,'policy_sha256':digest(policy),'snapshot_commitment_sha256':commitment,
            'runtime_pins':{**{role:{'address':item.address,'code_hash':item.code_hash} for role,item in p.contracts.items()},
                **copy.deepcopy(policy['extra_contracts'])},'original_fee_policy':copy.deepcopy(fee),
            'snapshot':snapshot,'provenance':{**header,'finality':'confirmation_depth_only',
                'confirmations':p.confirmations,'eip1898_require_canonical':True},
            'final_control_head':{**latest,'finality':'latest_canonical_only_not_confirmed',
                'eip1898_require_canonical':True},'review':review,
            'final_market_observations':final_snapshot,'last_head':last_head,
            'simulation':{'initial':initial_simulation,'final':final_simulation},
            'network_gas':{key:final_simulation[key] for key in ('padded_gas','gas_limit_cap','gas_price_wei','maximum_network_fee_wei')},
            'expires_at':min(s['deadline'],header['timestamp']+p.max_age),
            'work_budget':{'rpc_calls':MAX_CALLS,'seconds':MAX_SECONDS,'posts':1536},
            'limitations':['Active-state B/C/D only; no Parked emergency, floor selection, signing or future inclusion guarantee.',
                'Geometry coherence uses the same upstream source; provider honesty and actual host/gas require qualification.',
                'Review hash is provenance, not authority; exact custody hash and inclusion-time on-chain checks remain mandatory.']}


def write_exclusive(path,raw):
    """Publish complete bytes with exclusive atomic hard-link admission."""
    path=Path(path);temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.manual-lp-',delete=False) as stream:
            temporary=Path(stream.name);stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.link(temporary,path)  # Fails atomically if output already exists.
        if hasattr(os,'O_DIRECTORY'):
            directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self,message):raise ValueError('Invalid typed manual-preparation arguments')
    parser=Parser(description=__doc__)
    for name in ('read-config','policy','selection','output'):parser.add_argument('--'+name,required=True,type=Path)
    try:
        args=parser.parse_args(argv)
        config=offline.load(args.read_config);policy=offline.load(args.policy);chosen=offline.load(args.selection)
        if args.output.exists():raise ValueError('Output must be a new file')
        result=prepare(config,policy,chosen)
        write_exclusive(args.output,offline.render(result))
        print(json.dumps({'created':True,'kind':'unsigned_manual_lp_preparation','ready_for_submission':False}))
        return 0
    except Exception as exc:
        # Never echo transport text, endpoint credentials, paths or raw inputs.
        print(json.dumps({'ok':False,'error_type':type(exc).__name__,
            'reason':('unsupported_contract_wallet_envelope' if isinstance(exc,UnsupportedGovernanceEnvelope)
                else 'manual_preparation_unavailable_or_invalid')}),file=sys.stderr)
        return 1
