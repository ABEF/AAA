"""Active B/C/D and explicit Parked emergency-D unsigned preparation.

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
from zzz_ops.errors import RpcError, RemoteRPCError, WorkLimit
from zzz_ops.rpc import Rpc
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

# Static local comparisons only. Unknown RPC/decoder/revert text is never parsed.
LOCAL_CODES=frozenset(('unsupported_selection','unsupported_parked_selection','invalid_evidence',
    'invalid_request_bounds','inconsistent_swap_fields','invalid_guarded_b','invalid_integer',
    'simulation_header_changed','unexpected_simulation_output','gas_headroom_exceeded',
    'gas_price_exceeded','network_fee_budget_exceeded',
    'insufficient_governance_gas','reserve_abi_mismatch','helper_binding_mismatch','parked_pool_mismatch',
    'parked_live_lp_present','residual_inventory_invalid','parked_fingerprint_mismatch','pool_alias_mismatch',
    'bucket_inventory_invalid','unregistered_bucket','module_binding_mismatch','capability_mismatch',
    'fee_profile_mismatch','not_sealed','pause_required','preparation_active','canonical_not_operating',
    'terminal_exit_started','exit_phase_not_idle','governance_changed','governance_permission_missing',
    'malformed_governance_code','position_state_mismatch',
    'fixed_asset_mismatch','asset_pin_missing','asset_decimals_mismatch','empty_bucket_shares',
    'same_main_ticks_changed','invalid_tick_spacing','main_outside_range','no_residual_or_idle',
    'operations_disabled','no_parked_principal','invalid_swap_pool','swap_operations_disabled',
    'swap_exceeds_principal','invalid_price_bounds','financial_limits_invalid','unbounded_routes',
    'custody_counter_overflow','custody_hash_mismatch','unsupported_policy','source_catalog_mismatch',
    'noncanonical_extra_address','invalid_fee_policy','unsupported_profile','read_configuration_mismatch',
    'duplicate_runtime_roles','invalid_original_deadline','original_deadline_or_head_changed',
    'custody_or_controls_changed','final_anchor_changed','review_expired','local_inputs_changed',
    'invalid_cli_arguments','existing_output_preserved'))
STAGES=frozenset(('input_validation','configuration_validation','preparation','initial_snapshot','manifest_preparation',
    'initial_simulation','final_snapshot','final_simulation','final_canonicality',
    'artifact_rendering','artifact_publication'))
LOCAL_MESSAGES={
    'unsupported_selection':'Select a supported explicit manual action and selection schema.',
    'unsupported_parked_selection':'Schema2 requires actionD and an explicitly Parked source.',
    'invalid_evidence':'Select one through fifteen distinct reviewed evidence hashes.',
    'invalid_request_bounds':'The supplied request exceeds its exact integer, tick or check-mask bounds.',
    'inconsistent_swap_fields':'The explicit swap amount, venue, direction and output floor are inconsistent.',
    'invalid_guarded_b':'Guarded same-main actionB requires checks14 and no explicit swap.',
    'invalid_integer':'An exact bounded integer input is invalid.',
    'simulation_header_changed':'The simulation block identity differs from its captured canonical header.',
    'unexpected_simulation_output':'The exact void simulation returned unexpected data.',
    'gas_headroom_exceeded':'The estimate does not fit the unchanged gas cap with full25% headroom.',
    'gas_price_exceeded':'The observed gas price exceeds the original reviewed price ceiling.',
    'network_fee_budget_exceeded':'The padded gas cost exceeds the original reviewed network-fee budget.',
    'insufficient_governance_gas':'Governance lacks native currency for the reviewed network-fee amount.',
    'reserve_abi_mismatch':'A required reserve getter returned an incompatible ABI shape.',
    'helper_binding_mismatch':'A pinned helper points to a different required parent or module.',
    'parked_pool_mismatch':'The Parked pool key or canonical fixed-pair configuration differs.',
    'parked_live_lp_present':'The Parked source unexpectedly retains a physical main or residual LP.',
    'residual_inventory_invalid':'The observed residual count exceeds the supported bound.',
    'parked_fingerprint_mismatch':'The Parked zero-ID portfolio fingerprint differs from the pinned implementation.',
    'pool_alias_mismatch':'The source pool is not reserved to the selected bucket.',
    'bucket_inventory_invalid':'The registered bucket bound or count differs from the supported profile.',
    'unregistered_bucket':'The registered bucket inventory is invalid or does not contain the selected source.',
    'module_binding_mismatch':'The controller module binding differs from its reviewed pin.',
    'capability_mismatch':'A required manual-management capability version differs.',
    'fee_profile_mismatch':'The required fee-intake capability differs.',
    'not_sealed':'The deployment is not sealed.',
    'pause_required':'Pause the protocol before this manual management operation.',
    'preparation_active':'Canonical preparation is active; this manual operation is unavailable.',
    'canonical_not_operating':'The canonical deployment is not in its operating lifecycle.',
    'terminal_exit_started':'Terminal holder exit has started; this recovery cannot reopen principal.',
    'exit_phase_not_idle':'The terminal-exit module is not in its idle pre-exit phase.',
    'governance_changed':'The current governance address differs from the reviewed caller.',
    'governance_permission_missing':'The reviewed governance caller lacks current configuration permission.',
    'malformed_governance_code':'The governance runtime response is malformed.',
    'position_state_mismatch':'The source position state does not match the explicitly selected profile.',
    'fixed_asset_mismatch':'The deployment fixed-ZZZ identity or native pair differs.',
    'asset_pin_missing':'The fixed ZZZ lacks a reviewed asset runtime pin.',
    'asset_decimals_mismatch':'The fixed ZZZ decimals differ from the reviewed asset pin.',
    'empty_bucket_shares':'The source bucket has no authenticated shares.',
    'same_main_ticks_changed':'Same-main consolidation must retain the exact existing main bounds.',
    'invalid_tick_spacing':'The selected ticks do not fit the admitted pool spacing.',
    'main_outside_range':'Guarded same-main consolidation requires the existing main to be active.',
    'no_residual_or_idle':'There is no residual or attributed idle for the selected same-main operation.',
    'operations_disabled':'The retained source-pool operations flag is disabled.',
    'no_parked_principal':'The Parked source has no attributed idle or designated compound principal.',
    'invalid_swap_pool':'The explicit swap venue is not the admitted fixed native pair.',
    'swap_operations_disabled':'The retained swap-venue operations flag is disabled.',
    'swap_exceeds_principal':'The explicit swap input exceeds the exact captured operation principal.',
    'invalid_price_bounds':'The returned independent price bounds are inconsistent.',
    'financial_limits_invalid':'An observed financial limit exceeds the fixed governance ceiling.',
    'unbounded_routes':'The automatic execution route catalogue exceeds its supported bound.',
    'custody_counter_overflow':'The Parked custody nonce or epoch exceeds uint64.',
    'custody_hash_mismatch':'The emergency custody hash differs from the exact captured Parked state.',
    'unsupported_policy':'Select the supported reviewed manual-policy schema.',
    'source_catalog_mismatch':'The policy source or function catalogue binding differs.',
    'noncanonical_extra_address':'Extra runtime addresses must use canonical lower-case encoding.',
    'invalid_fee_policy':'Supply a bounded reviewed complete network-fee policy.',
    'unsupported_profile':'This tool requires explicit accounting7, custody5 and fee-intake1.',
    'read_configuration_mismatch':'The exact reviewed read configuration or maximum age differs.',
    'duplicate_runtime_roles':'Distinct runtime roles cannot share a target address.',
    'invalid_original_deadline':'Preserve an original deadline within600seconds of the confirmed snapshot.',
    'original_deadline_or_head_changed':'The original deadline or later canonical head is no longer valid.',
    'custody_or_controls_changed':'Custody or governed controls changed; prepare a new review.',
    'final_anchor_changed':'The final simulation anchor changed; discard this review.',
    'review_expired':'The original review expired after final simulation.',
    'local_inputs_changed':'Local reviewed inputs changed during preparation.',
    'invalid_cli_arguments':'Supply the required typed manual-preparation arguments.',
    'existing_output_preserved':'The existing output path was preserved; no replacement or transaction was submitted.'}


class ManualInputBlocked(ValueError):
    """Known local validation, retaining the existing ValueError contract."""
    def __init__(self,code,message):
        if code not in LOCAL_CODES:raise ValueError('Unsupported manual diagnostic code')
        self.manual_code=code;super().__init__(message)


class ManualReadBlocked(RpcError):
    """Known local read comparison, retaining the existing RpcError contract."""
    def __init__(self,code,message):
        if code not in LOCAL_CODES:raise ValueError('Unsupported manual diagnostic code')
        self.manual_code=code;super().__init__(message)


class UnsupportedGovernanceEnvelope(ValueError):
    """Contract/delegated wallets require a separately prepared outer envelope."""


class IncompatibleParkedGuards(ValueError):
    """Pinned Active-only guards cannot be retained by a Parked request."""


def digest(value):return hashlib.sha256(offline.canonical(value)).hexdigest()


def integer(value, *, bits=256, signed=False, positive=False):
    try:offline._integer(value,bits,signed=signed,positive=positive)
    except ValueError as exc:raise ManualInputBlocked('invalid_integer','Invalid exact integer input') from exc
    return int(value)


def selection(raw):
    schema=raw.get('schema') if isinstance(raw,dict) else None
    fields={'schema','action','bucket','checks','lower','upper','swapPool','zeroForOne',
        'amountIn','minimumOut','minimumLiquidity','deadline','review_notes_sha256','evidence_sha256'}
    offline._keys(raw,fields|({'expected_position_status'} if type(schema) is int and schema==2 else set()))
    if type(schema) is not int or schema not in (1,2) or raw['action'] not in ('B','C','D'):
        raise ManualInputBlocked('unsupported_selection','Select exactly Active-state manual action B, C or D')
    if schema==2 and (raw['action']!='D' or raw['expected_position_status']!='parked'):
        raise ManualInputBlocked('unsupported_parked_selection','Schema2 requires explicit Parked emergency action D only')
    result=copy.deepcopy(raw)
    for field,bits,signed,positive in [('bucket',256,False,True),('checks',8,False,False),
            ('lower',24,True,False),('upper',24,True,False),('amountIn',128,False,False),
            ('minimumOut',128,False,False),('minimumLiquidity',128,False,True),('deadline',256,False,True)]:
        result[field]=integer(raw[field],bits=bits,signed=signed,positive=positive)
    offline._hex(raw['swapPool'],32)
    offline._hex(raw['review_notes_sha256'],32,nonzero=True,prefix=False)
    evidence=raw['evidence_sha256']
    if not isinstance(evidence,list) or not 1<=len(evidence)<=15 or len(set(evidence))!=len(evidence):
        raise ManualInputBlocked('invalid_evidence','Select one through fifteen distinct evidence hashes')
    for value in evidence:offline._hex(value,32,nonzero=True,prefix=False)
    if (type(raw['zeroForOne']) is not bool or result['checks']>31 or
            not MIN_TICK<=result['lower']<result['upper']<=MAX_TICK or
            max(result['amountIn'],result['minimumOut'])>=1<<127):
        raise ManualInputBlocked('invalid_request_bounds','Manual request exceeds supported exact bounds')
    swap=result['amountIn']>0
    if (swap and (int(raw['swapPool'],16)==0 or result['minimumOut']==0) or
            not swap and (int(raw['swapPool'],16)!=0 or result['minimumOut']!=0 or raw['zeroForOne'])):
        raise ManualInputBlocked('inconsistent_swap_fields','Explicit swap fields are inconsistent')
    if raw['action']=='B' and (result['checks']!=14 or swap):
        raise ManualInputBlocked('invalid_guarded_b','Guarded B requires checks14 and no explicit swap')
    # These retained guards require an Active physical LP in the pinned source.
    # Never silently clear the caller's mask or claim a Parked call can pass them.
    if schema==2 and result['checks']&17:
        raise IncompatibleParkedGuards('Parked emergency cannot retain Active trigger or sampled confirmation guards (bits1/16)')
    return result


def parked_safeguards(checks):
    """Disclose consent, never substitute mask bits for execution evidence."""
    names=((1,'ordinary_trigger_and_hard_cooldown'),(2,'independent_price_and_spot_checks'),
        (4,'retained_value_and_execution_loss'),(8,'pool_operations_flags'),
        (16,'sampled_price_confirmation'))
    return {'checks':checks,
        'retained':[{'bit':bit,'name':name,'status':'retained_for_exact_simulation'}
            for bit,name in names if checks&bit],
        'bypassed':[{'bit':bit,'name':name,'status':'explicitly_bypassed_by_caller'}
            for bit,name in names if not checks&bit],
        'usd_required':bool(checks&6),'mask_is_eligibility_proof':False,
        'mandatory_controls':['current_governance_only','sealed_paused_operating_pre_exit',
            'direct_empty_code_governance_eoa','pinned_module_and_asset_identities',
            'registered_bucket_alias_and_shares','zero_live_main_and_residual',
            'exact_attributed_idle_and_designated_compound','custody_hash_nonce_epoch',
            'caller_swap_floors_liquidity_floor_deadline','atomic_accounting_callbacks_and_rollback',
            'unchanged_calldata_confirmed_and_canonical_tip_simulation','original_gas_fee_and_funding_limits'],
        'protocol_remains_paused':True,
        'warning':'Bypassed financial guards may permit near-total principal loss; this review is not execution approval.'}


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
        raise ManualReadBlocked('simulation_header_changed','Manual simulation header changed')
    block_limit=rpc_quantity(raw.get('gasLimit'),'manual block gas limit',minimum=21000)
    cap=min(integer(fee['max_gas_limit'],positive=True),block_limit)
    tx={**transaction,'gas':hex(cap)}
    if p.rpc.call('eth_call',[tx,block])!='0x':raise ManualReadBlocked('unexpected_simulation_output','Manual void simulation returned unexpected data')
    estimate=rpc_quantity(p.rpc.call('eth_estimateGas',[tx,block]),'manual estimated gas',minimum=21000)
    padded=(estimate*125+99)//100
    price=rpc_quantity(p.rpc.call('eth_gasPrice',[]),'manual gas price',minimum=1)
    cost=padded*price
    if padded>cap:raise ManualReadBlocked('gas_headroom_exceeded','Manual review exceeds original gas/fee limits')
    if price>integer(fee['max_gas_price_wei'],positive=True):
        raise ManualReadBlocked('gas_price_exceeded','Manual review exceeds original gas/fee limits')
    if cost>integer(fee['max_network_fee_wei'],positive=True):
        raise ManualReadBlocked('network_fee_budget_exceeded','Manual review exceeds original gas/fee limits')
    balance=rpc_quantity(p.rpc.call('eth_getBalance',[transaction['from'],block]),'manual governance balance')
    if balance<cost:raise ManualReadBlocked('insufficient_governance_gas','Governance balance is below the reviewed network fee')
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
            if len(values)!=count:raise ManualReadBlocked('reserve_abi_mismatch','Manual reserve getter ABI differs')
            return values
        return self.p._call(self.targets.get(role,role),method,*args,block=self.block,words=count)

    def uint(self,role,method,*args):return int(self.read(role,method,*args)[0],16)
    def flag(self,role,method,*args):return _bool(self.read(role,method,*args)[0])
    def hashed(self,role,method,*args):
        value='0x'+self.read(role,method,*args)[0]
        return offline._hex(value,32,nonzero=True)

    def binding(self,role,method,expected):
        if self.uint(role,method)!=int(self.targets[expected],16):raise ManualReadBlocked('helper_binding_mismatch','Manual helper binding differs')

    def parked_pool(self,pool,zzz):
        """Authenticate the complete fixed native pair without a live LP read."""
        config=self.read('pools','accounting(bytes32)',pool,count=14)
        values=[int(word,16) for word in config]
        widths=(160,160,24,24,160,1,1,16,16,16,16,32,256,256)
        if (any(value>=1<<width for value,width in zip(values,widths)) or
                values[0]!=0 or values[1]!=zzz or values[4]!=0 or
                not 1<=values[3]<=32767 or values[2]>100000 or
                '0x'+keccak256(bytes.fromhex(''.join(config[:5]))).hex()!=pool or
                self.read('pools','get(bytes32)',pool,count=14)!=config):
            raise ManualReadBlocked('parked_pool_mismatch','Parked pool key or canonical configuration differs')
        return config

    def parked_physical(self,position,bucket):
        """Prove absent live legs using the pinned Manager/Executor zero-ID ABI.

        Zero-ID portfolio hashes are nonzero domain fingerprints. Calling the
        Active physical reader, ticks(0) or portfolioAmounts(0) is invalid.
        """
        if position['lp_token_id']!=0 or self.uint('liquidity','secondaryId(uint256)',0)!=0:
            raise ManualReadBlocked('parked_live_lp_present','Parked source retains a physical main or residual')
        count=self.uint('liquidity','activeSecondaryCount()')
        if count>4:raise ManualReadBlocked('residual_inventory_invalid','Parked residual inventory exceeds its bound')
        stable='0x'+keccak256(bytes.fromhex(f'{int(self.targets["lp_position_executor"],16):064x}'+'0'*64)).hex()
        execution='0x'+keccak256(bytes.fromhex(stable[2:]+'0'*128)).hex()
        if (self.hashed('liquidity','portfolioFingerprint(uint256)',0)!=stable or
                self.hashed('liquidity','executionPortfolioFingerprint(uint256)',0)!=execution):
            raise ManualReadBlocked('parked_fingerprint_mismatch','Parked zero-ID portfolio fingerprint differs')
        pool=position['pool_id']
        if self.uint('vault','poolBucket(bytes32)',pool)!=bucket:
            raise ManualReadBlocked('pool_alias_mismatch','Parked source pool alias differs')
        total=self.uint('vault','bucketCount()');maximum=self.uint('vault','MAX_BUCKETS()')
        if maximum!=4 or not 1<=total<=maximum:
            raise ManualReadBlocked('bucket_inventory_invalid','Parked custody bucket inventory exceeds its bound')
        buckets=[self.uint('vault','bucketAt(uint256)',i) for i in range(total)]
        if any(identifier==0 for identifier in buckets) or len(set(buckets))!=total or bucket not in buckets:
            raise ManualReadBlocked('unregistered_bucket','Parked source is absent from registered custody inventory')
        return {'scope':'parked_no_live_lp','pool_id':pool,'lp_token_id':0,'secondary_id':0,
            'physical_legs':[],'active_secondary_count':count,'registered_buckets':list(map(str,buckets)),
            'portfolio_fingerprint':stable,'execution_portfolio_fingerprint':execution}

    def snapshot(self,s,governance,*,full):
        p=self.p;b=s['bucket'];c=self.targets
        execution_prices=None
        if full:
            life=p._verify_deployment(self.block)
            for role,item in self.extra.items():p._code(item['address'],item['code_hash'],self.block)
            for role,label in [('oracle','ZZZOracle'),('fees','ZZZFeeController')]:
                if self.uint('access','module(bytes32)','0x'+keccak256(label.encode()).hex())!=int(c[role],16):
                    raise ManualReadBlocked('module_binding_mismatch','Manual module binding differs')
                self.binding(role,'access()','access')
            for role,method,expected in [('principal_exit','validation()','custody_validation'),
                    ('custody_validation','migration()','principal_exit'),('custody_validation','access()','access'),
                    ('pools','activationAssets()','activation_assets'),('activation_assets','registry()','pools'),
                    ('activation_assets','access()','access'),('oracle','contributionPricing()','contribution_pricing'),
                    ('contribution_pricing','oracle()','oracle'),('contribution_pricing','access()','access')]:
                self.binding(role,method,expected)
            for role in ('principal_exit','vault','budget','portfolio_policy','contribution_pricing'):
                if self.uint(role,'RESIDUAL_REINVEST_VERSION()')!=1:raise ManualReadBlocked('capability_mismatch','Manual extension capability differs')
            if self.uint('fees','FEE_INTAKE_VERSION()')!=1:raise ManualReadBlocked('fee_profile_mismatch','Manual fee profile differs')
            if p.execution_price_version:
                from zzz_ops.execution_price import observe
                execution_prices=observe(lambda target,method,*,count:self.read(target,method,count=count),c)
        # Preserve the original short-circuit read order; stop at the first
        # locally observed mismatch, never add reads to guess an opaque failure.
        for invalid,code in (
                (lambda:not self.flag('access','isSealed()'),'not_sealed'),
                (lambda:not self.flag('access','paused()'),'pause_required'),
                (lambda:self.flag('access','preparationActive()'),'preparation_active'),
                (lambda:self.uint('access','canonicalState()')!=0,'canonical_not_operating'),
                (lambda:self.flag('access','lpExitStarted()'),'terminal_exit_started'),
                (lambda:self.uint('principal_exit','exitPhase()')!=0,'exit_phase_not_idle'),
                (lambda:self.uint('access','governance()')!=int(governance,16),'governance_changed'),
                (lambda:not self.flag('access','canConfigure(address)',governance),'governance_permission_missing')):
            if invalid():raise ManualReadBlocked(code,'Paused current governance and operating pre-exit lifecycle are required')
        governance_code=p.rpc.call('eth_getCode',[governance,self.block])
        if not isinstance(governance_code,str) or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',governance_code) is None:
            raise ManualReadBlocked('malformed_governance_code','Malformed governance runtime code')
        if governance_code!='0x':
            raise UnsupportedGovernanceEnvelope('unsupported_contract_wallet_envelope: direct empty-code governance EOA required')
        raw=self.read('vault','group(uint256)',b,count=8);position=decode_position(raw,7)
        parked=s['schema']==2
        if parked:
            if position['status']!='parked':raise ManualInputBlocked('position_state_mismatch','Explicit Parked emergency source state differs')
            physical=self.parked_physical(position,b)
        else:
            if position['status']!='active':raise ManualInputBlocked('position_state_mismatch','Only Active-state manual B/C/D is supported; Parked is unsupported')
            hashes={role:item.code_hash for role,item in p.contracts.items()}
            physical=physical_portfolio(self.read,lambda target:p.rpc.call('eth_getCode',[target,self.block]),
                contracts=c,code_hashes=hashes,bucket=b,accounting_version=7,physical_only=True,
                execution_price_version=p.execution_price_version)
        pool=position['pool_id'];main=position['lp_token_id'];legs=physical['physical_legs']
        config=None if parked else self.read('pools','accounting(bytes32)',pool,count=14)
        zzz=self.uint('activation_assets','zzz()')
        if parked:config=self.parked_pool(pool,zzz)
        if (int(config[0],16)!=0 or int(config[1],16)!=zzz or zzz==0 or
                self.uint('principal_exit','currentZZZ()')!=zzz):raise ManualReadBlocked('fixed_asset_mismatch','Manual fixed asset identity differs')
        asset='0x'+f'{zzz:040x}'
        if asset not in p.assets:raise ManualReadBlocked('asset_pin_missing','Fixed ZZZ lacks a reviewed asset pin')
        p._code(asset,p.assets[asset].code_hash,self.block)
        if self.uint(asset,'decimals()')!=p.assets[asset].decimals:raise ManualReadBlocked('asset_decimals_mismatch','Fixed ZZZ decimals differ')
        shares=self.uint('vault','bucketTotalShares(uint256)',b)
        if shares==0:raise ManualReadBlocked('empty_bucket_shares','Manual bucket has no authenticated shares')
        lower,upper=((s['lower'],s['upper']) if parked else (legs[0]['tick_lower'],legs[0]['tick_upper']))
        if s['action']!='D' and (s['lower'],s['upper'])!=(lower,upper):
            raise ManualInputBlocked('same_main_ticks_changed','Same-main request must keep the exact current ticks')
        spacing=int(config[3],16)
        if s['lower']%spacing or s['upper']%spacing:raise ManualInputBlocked('invalid_tick_spacing','Manual ticks do not fit pool spacing')
        if s['action']=='B':
            from zzz_ops.tick_math import decode_slot0
            _,tick,_,_=decode_slot0(self.read('state_view','getSlot0(bytes32)',pool,count=4),expected_fee=int(config[2],16))
            if not lower<=tick<upper:raise ManualReadBlocked('main_outside_range','Guarded same-main requires an active unchanged main')
        if s['action']!='D' and not physical['secondary_id'] and not(position['idle0'] or position['idle1']):
            raise ManualReadBlocked('no_residual_or_idle','Same-main operation has no residual or attributed idle')
        if s['checks']&8 and not _bool(config[6]):raise ManualReadBlocked('operations_disabled','Retained operations flag is disabled')
        reserves=[self.uint('fees','compoundBalance(uint256,address)',b,t) for t in (ZERO,asset)]
        if parked and not any((position['idle0'],position['idle1'],*reserves)):
            raise ManualReadBlocked('no_parked_principal','Parked source has no attributed or designated principal')
        swap=None
        if s['amountIn']:
            swap_config=(self.parked_pool(s['swapPool'],zzz) if parked else
                self.read('pools','accounting(bytes32)',s['swapPool'],count=14))
            if (swap_config[:2]!=config[:2] or int(swap_config[4],16)!=0 or
                    '0x'+keccak256(bytes.fromhex(''.join(swap_config[:5]))).hex()!=s['swapPool']):
                raise ManualReadBlocked('invalid_swap_pool','Explicit swap venue is not the admitted fixed pair')
            if s['checks']&8 and not _bool(swap_config[6]):raise ManualReadBlocked('swap_operations_disabled','Retained swap operations flag is disabled')
            available=[position['idle0'],position['idle1']]
            selected=legs if s['action']=='D' else legs[1:]
            for leg in selected:
                amounts=[int(w,16) for w in self.read('liquidity','amounts(uint256)',leg['lp_token_id'],count=2)]
                available=[a+b for a,b in zip(available,amounts)]
            if s['action']=='D':available=[a+b for a,b in zip(available,reserves)]
            if (parked or s['action']!='D') and s['amountIn']>available[0 if s['zeroForOne'] else 1]:
                raise ManualReadBlocked('swap_exceeds_principal','Explicit swap exceeds captured attributed operation principal')
            swap={'config':swap_config,'available_principal_raw':list(map(str,available)),
                'availability_scope':('attributed_idle_and_designated_compound_only' if parked else
                    'observed_lower_bound_excludes_future_harvest' if s['action']=='D'
                    else 'captured_residual_and_attributed_idle_only'),
                'captured_amount_is_preflight_ceiling':parked or s['action']!='D'}
        financial={'state':'not_retained','price_bounds':None,'maintenance_policy':None}
        if s['checks']&6:
            bounds=[self.read('oracle','priceBounds(address)',token,count=3) for token in (ZERO,asset)]
            for row in bounds:
                if not 0<int(row[0],16)<=int(row[1],16) or int(row[2],16)==0:raise ManualReadBlocked('invalid_price_bounds','Invalid independent price bounds')
            financial.update(state='observed',price_bounds=bounds,
                execution_quality_revision=str(self.uint('strategy','executionQualityRevision()')),
                price_policy_ids=[self.hashed('oracle','activePolicy(address)',token) for token in (ZERO,asset)],
                sequencer_policy='0x'+self.read('oracle','activeSequencerPolicy()')[0])
        if s['checks']&4:
            maintenance=policy_observation(self.read,policy=c['protocol_policy'],access=c['access'],domain='maintenance')
            loss=self.uint('budget','maintenanceLossBps()');additional=self.uint('strategy','additionalLossBps()')
            if max(loss,additional)>1000:raise ManualReadBlocked('financial_limits_invalid','Financial limits exceed fixed ceilings')
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
            if count>4:raise ManualReadBlocked('unbounded_routes','Unbounded automatic route catalogue')
            routing={'revision':self.uint('balancing_router','executionRevision()'),
                'pools':[self.hashed('balancing_router','executionPoolAt(uint256)',i) for i in range(count)]}
        custody=self.hashed('principal_exit','emergencyCustodyHash(uint256)' if s['action']=='D' else 'consolidationCustodyHash(uint256)',b)
        nonce=self.uint('principal_exit','parkingNonce(uint256)',b);epoch=self.uint('principal_exit','custodyEpoch(uint256)',b)
        if parked:
            if max(nonce,epoch)>=1<<64:raise ManualReadBlocked('custody_counter_overflow','Parked custody nonce or epoch exceeds uint64')
            expected='0x'+keccak256(bytes.fromhex(''.join([
                f'{p.chain:064x}',f'{int(c["vault"],16):064x}',f'{b:064x}',*raw,
                f'{shares:064x}',physical['execution_portfolio_fingerprint'][2:]]))).hex()
            if custody!=expected:raise ManualReadBlocked('custody_hash_mismatch','Parked emergency custody hash differs from exact source state')
        return {'governance':governance,'governance_code':governance_code,
            'governance_wallet_scope':'direct_empty_code_governance_eoa_only',
            'position_words':raw,'shares':str(shares),'physical':physical,
            'custody_hash':custody,'parking_nonce':str(nonce),
            'custody_epoch':str(epoch),
            'pool_configuration':config,'registry_revision':str(self.uint('pools','configurationRevision()')),
            'portfolio_control':self.hashed('portfolio_policy','controlFingerprint(bytes32)',pool),
            'compound_reserves_raw':list(map(str,reserves)),'financial':financial,'timing':timing,'swap':swap,'routing':routing,
            **({'execution_price':execution_prices} if p.execution_price_version else {}),
            **({'source_position_status':'parked','selection_schema':2,'selection_sha256':s['_selection_sha256']}
                if parked else {})}


def validate_policy(policy,catalog):
    """Authenticate shared manual-review inputs without choosing operating limits."""
    offline._keys(policy,{'schema','projection_sha256','reference_sha256','source_snapshot_sha256',
        'governance','extra_contracts','fee_policy'})
    if type(policy['schema']) is not int or policy['schema']!=1:raise ManualInputBlocked('unsupported_policy','Unsupported manual policy schema')
    if (policy['reference_sha256']!=catalog.reference_sha256 or
            policy['source_snapshot_sha256']!=catalog.source_snapshot_sha256):raise ManualInputBlocked('source_catalog_mismatch','Manual source/catalog binding differs')
    governance=address(policy['governance']);offline._keys(policy['extra_contracts'],EXTRAS)
    for item in policy['extra_contracts'].values():
        offline._keys(item,{'address','code_hash'});address(item['address']);offline._hex(item['code_hash'],32,nonzero=True)
        if address(item['address'])!=item['address']:raise ManualInputBlocked('noncanonical_extra_address','Extra runtime addresses must be canonical lower-case')
    fee=policy['fee_policy'];offline._keys(fee,{'max_gas_limit','max_gas_price_wei','max_network_fee_wei',
        'estimate_includes_all_fees','review_hash'})
    gas=integer(fee['max_gas_limit'],positive=True);integer(fee['max_gas_price_wei'],positive=True)
    integer(fee['max_network_fee_wei'],positive=True);offline._hex(fee['review_hash'],32,nonzero=True)
    if not 21000<=gas<=MAX_GAS or fee['estimate_includes_all_fees'] is not True:raise ManualInputBlocked('invalid_fee_policy','Bounded reviewed complete fee policy is required')
    return governance,fee


def prepare(read_config,policy,request,*,rpc=None,clock=None,catalog=None):
    """Prepare one explicitly selected call, or fail without a partial draft."""
    stage='input_validation'
    try:
        clock=clock or time.time;catalog=catalog or offline.Catalog()
        input_references=(read_config,policy,request)
        original=[digest(value) for value in input_references]
        config=copy.deepcopy(read_config);policy=copy.deepcopy(policy);s=selection(request)
        if s['schema']==2:s['_selection_sha256']=original[2]
        stage='configuration_validation'
        governance,fee=validate_policy(policy,catalog)
        with request_scope(Budget(seconds=MAX_SECONDS,calls=MAX_CALLS,posts=1536)):
            p=Projection(config,rpc=rpc,clock=clock)
            if (p.accounting_version,p.custody_version,p.fee_intake_version)!=(7,5,1):raise ManualInputBlocked('unsupported_profile','Only explicit accounting7/custody5 is supported')
            if p.identity!=policy['projection_sha256'] or p.max_age>120:raise ManualInputBlocked('read_configuration_mismatch','Exact fresh reviewed read configuration required')
            all_targets=[item.address for item in p.contracts.values()]+[item['address'] for item in policy['extra_contracts'].values()]
            if len(set(all_targets))!=len(all_targets):raise ManualInputBlocked('duplicate_runtime_roles','Manual runtime roles must be distinct')
            stage='initial_snapshot'
            header,head,block=p._snapshot();expire_at(min(s['deadline'],header['timestamp']+p.max_age),clock)
            if not header['timestamp']<=s['deadline']<=header['timestamp']+600:raise ManualInputBlocked('invalid_original_deadline','Preserve an original deadline within600seconds')
            reader=Reader(p,policy['extra_contracts'],block)
            snapshot=reader.snapshot(s,governance,full=True)
            stage='manifest_preparation'
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
            stage='initial_simulation'
            initial_simulation=simulation(p,header,block,tx,fee,confirmed=True)
            # Controls remain fixed; healthy market motion gets one final exact call
            # at the later canonical tip, with the original floors and deadline.
            stage='final_snapshot'
            final_number=rpc_quantity(p.rpc.call('eth_blockNumber',[]),'manual final head')
            latest=p._header(hex(final_number));p._fresh(latest)
            if latest['number']<head or latest['timestamp']<header['timestamp'] or not latest['timestamp']<=s['deadline']<=latest['timestamp']+600:
                raise ManualReadBlocked('original_deadline_or_head_changed','Manual preparation head retreated or original deadline expired')
            final_block={'blockHash':latest['hash'],'requireCanonical':True}
            final=Reader(p,policy['extra_contracts'],final_block)
            final_snapshot=final.snapshot(s,governance,full=True)
            if controls(final_snapshot)!=controls(snapshot):raise ManualReadBlocked('custody_or_controls_changed','Manual custody or governed controls changed')
            stage='final_simulation'
            final_simulation=simulation(p,latest,final_block,tx,fee,confirmed=False)
            stage='final_canonicality'
            if p._header(hex(latest['number']))!=latest:raise ManualReadBlocked('final_anchor_changed','Final manual control head changed')
            p._finish(header)
            last_number=rpc_quantity(p.rpc.call('eth_blockNumber',[]),'manual last head')
            last_head=p._header(hex(last_number));p._fresh(last_head)
            if last_number==latest['number'] and last_head!=latest:
                raise ManualReadBlocked('final_anchor_changed','Final manual control head changed after simulation')
            if (last_number<latest['number'] or last_head['timestamp']<latest['timestamp'] or
                    not last_head['timestamp']<=s['deadline']<=last_head['timestamp']+600):
                raise ManualReadBlocked('original_deadline_or_head_changed','Manual original deadline expired after final review')
            if [digest(value) for value in input_references]!=original:raise ManualReadBlocked('local_inputs_changed','Manual configuration changed during preparation')
            if clock()>=min(s['deadline'],header['timestamp']+p.max_age):raise ManualReadBlocked('review_expired','Manual preparation expired')
            result={'schema':1,'kind':'unsigned_manual_lp_preparation','action':s['action'],
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
            if s['schema']==2:
                result.update(schema=2,expected_position_status='parked',selection_sha256=original[2],
                    safeguards=parked_safeguards(s['checks']))
                result['limitations'][0]=('Explicit Parked emergency D only; bits1/16 are incompatible and are never silently cleared. '
                    'No floor selection, signing, unpause, new destination or future inclusion guarantee.')
            return result
    except Exception as exc:
        try:exc.manual_stage=stage
        except Exception:pass  # Diagnostics must never replace the original error.
        raise


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


def _metadata(exc,name):
    try:return getattr(exc,name,None)
    except Exception:return None


def diagnostic(exc,stage,*,publishing=False):
    """Static messages and trusted typed metadata; never exception text/URLs."""
    reason='manual_preparation_unavailable_or_invalid';extra={}
    message='The required review is unavailable or invalid; no fallback transaction was prepared.'
    if isinstance(exc,UnsupportedGovernanceEnvelope):
        reason='unsupported_contract_wallet_envelope'
        message='This tool requires a direct empty-code governance wallet; prepare contract-wallet envelopes separately.'
    elif isinstance(exc,IncompatibleParkedGuards):
        reason='parked_active_trigger_or_confirmation_incompatible'
        message='Parked recovery cannot retain Active trigger or confirmation bits1/16; select the mask explicitly.'
    elif isinstance(exc,(ManualInputBlocked,ManualReadBlocked)):
        code=_metadata(exc,'manual_code')
        if type(code) is str and code in LOCAL_CODES:
            reason=code;message=LOCAL_MESSAGES.get(code,'A known local review condition failed; inspect the cause before preparing again.')
    elif isinstance(exc,WorkLimit):
        value=_metadata(exc,'reason')
        if type(value) is str and value in ('deadline','rpc_budget','snapshot_expired'):
            reason='work_limit_'+value
            message='The bounded read-only review expired or exhausted its work budget; no fallback transaction was prepared.'
    elif isinstance(exc,RemoteRPCError):
        value=_metadata(exc,'reason')
        value=value if type(value) is str and value in ('unavailable_block','invalid_params','rate_limited','unclassified') else 'unclassified'
        reason='rpc_'+value
        method=_metadata(exc,'method');code=_metadata(exc,'code')
        extra={'rpc_method':method if type(method) is str and method in Rpc.READ_METHODS else None,
            'rpc_code':code if type(code) is int and -(1<<31)<=code<(1<<31) else None}
        message='A required RPC read or exact simulation failed; the underlying contract cause is not established.'
    # Use known base names, never attacker-selected exception class names.
    error_type=next((name for kind,name in ((UnsupportedGovernanceEnvelope,'UnsupportedGovernanceEnvelope'),
        (IncompatibleParkedGuards,'IncompatibleParkedGuards'),(WorkLimit,'WorkLimit'),(RemoteRPCError,'RemoteRPCError'),
        (RpcError,'RpcError'),(ValueError,'ValueError'),(TypeError,'TypeError'),(OSError,'OSError'))
        if isinstance(exc,kind)),'Exception')
    recorded=_metadata(exc,'manual_stage')
    if type(recorded) is str and recorded in STAGES:stage=recorded
    if type(stage) is not str or stage not in STAGES:stage='preparation'
    if publishing:stage='artifact_publication'
    existing=reason=='existing_output_preserved'
    if publishing:
        reason='artifact_publication_uncertain'
        message='Artifact publication or reporting failed; a complete artifact may already exist. Inspect it before any new attempt.'
    elif existing:message='The existing output path was preserved; no replacement or transaction was submitted.'
    return {'ok':False,'error_type':error_type,'read_only':True,'transaction_submitted':False,
        'output_may_exist':publishing or existing,'stage':stage,'reason':reason,'message':message,**extra}


def main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self,message):raise ManualInputBlocked('invalid_cli_arguments','Invalid typed manual-preparation arguments')
    parser=Parser(description=__doc__)
    for name in ('read-config','policy','selection','output'):parser.add_argument('--'+name,required=True,type=Path)
    stage='input_validation';publishing=False
    try:
        args=parser.parse_args(argv)
        if os.path.lexists(args.output):raise ManualInputBlocked('existing_output_preserved','Output must be a new file')
        config=offline.load(args.read_config);policy=offline.load(args.policy);chosen=offline.load(args.selection)
        stage='preparation'
        result=prepare(config,policy,chosen)
        stage='artifact_rendering';raw=offline.render(result)
        stage='artifact_publication';publishing=True
        write_exclusive(args.output,raw)
        print(json.dumps({'created':True,'kind':'unsigned_manual_lp_preparation','ready_for_submission':False}))
        return 0
    except Exception as exc:
        # Never echo transport text, endpoint credentials, paths or raw inputs.
        print(json.dumps(diagnostic(exc,stage,publishing=publishing)),file=sys.stderr)
        return 1
