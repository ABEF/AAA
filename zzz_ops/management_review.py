"""Typed read-only custody/exit reviews; no signer, journal, retries or execution.

Each review preserves the operator's original inputs, captures authority/custody
twice and simulates identical calldata and transaction gas at both snapshots.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import time

from frontend_api.service import Projection
from keeper.monitor import rpc_hash, rpc_quantity
from zzz_ops import operator_review as offline
from zzz_ops.errors import RpcError, RemoteRPCError, WorkLimit
from zzz_ops.management_base import ManagementBlocked, ManagementReader
from zzz_ops.rpc import Rpc
from zzz_ops.manual_lp_review import (UnsupportedGovernanceEnvelope, digest,
    integer, validate_policy, write_exclusive)
from zzz_ops.work_budget import Budget, expire_at, request_scope

MAX_CALLS=1536
MAX_SECONDS=30
CUSTODY_ACTIONS=('park','resume','close_residual')
EXIT_ACTIONS=('collective_exit_begin','close_bucket','allocate_principal','distribute_principal')
EFFECTS={
    'park':'Close both physical legs into Vault-attributed idle; principal and earned rewards remain separate. Unpausing alone does not reopen LP.',
    'resume':'Guarded redeployment of parked principal into the selected reviewed same-pair pool; actual portfolio follows the approved policy.',
    'close_residual':'Close only the residual into attributed idle. Main, desired residual mode and designated compound remain unchanged; reinvestment is separate.',
    'collective_exit_begin':'Irreversibly stop new LP activity. Bucket closure, allocation and current-owner payment require separate explicit operations.',
    'close_bucket':'Close both legs of this snapshotted bucket and classify actual ETH/ZZZ principal. No swap, reward claim or holder payout.',
    'allocate_principal':'Allocate the next bounded mint-ordinal cohort at the cursor read by the included transaction. This operation pays no holder.',
    'distribute_principal':'Attempt only the selected principal payouts to current owners. Some can defer or remain unpaid; reconcile actual events and ledgers.'}


def selection(raw):
    from zzz_ops import management_custody, management_exit
    offline._keys(raw,{'schema','action','parameters','expires_at','review_notes_sha256','evidence_sha256'})
    if type(raw['schema']) is not int or raw['schema']!=1 or raw['action'] not in CUSTODY_ACTIONS+EXIT_ACTIONS:
        raise ValueError('Select an explicit supported management action')
    result=copy.deepcopy(raw)
    result['expires_at']=integer(raw['expires_at'],positive=True)
    offline._hex(raw['review_notes_sha256'],32,nonzero=True,prefix=False)
    evidence=raw['evidence_sha256']
    if not isinstance(evidence,list) or not 1<=len(evidence)<=15 or len(set(evidence))!=len(evidence):
        raise ValueError('One through fifteen distinct evidence hashes are required')
    for value in evidence:offline._hex(value,32,nonzero=True,prefix=False)
    adapter=management_custody if raw['action'] in CUSTODY_ACTIONS else management_exit
    result['parameters']=adapter.validate(raw['action'],raw['parameters'])
    return result,adapter


def _canonical_arguments(value):
    if type(value) is bool:return value
    if type(value) is int:return str(value)
    if isinstance(value,dict):return {k:_canonical_arguments(v) for k,v in value.items()}
    if isinstance(value,list):return [_canonical_arguments(v) for v in value]
    return value


def _mark_review_hash(value):
    if isinstance(value,dict):
        return {k:offline.MARKER if k=='reviewHash' else _mark_review_hash(v) for k,v in value.items()}
    if isinstance(value,list):return [_mark_review_hash(v) for v in value]
    return value


def _returned(raw, maximum_paid):
    if maximum_paid is None:
        if raw!='0x':raise ManagementBlocked('unexpected_simulation_output','A void management call returned unexpected data.')
        return {'kind':'void'}
    if not isinstance(raw,str) or re.fullmatch(r'0x[0-9a-fA-F]{64}',raw) is None:
        raise ManagementBlocked('unexpected_simulation_output','The distribution return value is malformed.')
    try:paid=int(raw[2:],16)
    except ValueError as exc:raise ManagementBlocked('unexpected_simulation_output','The distribution return value is malformed.') from exc
    if not 1<=paid<=maximum_paid:
        raise ManagementBlocked('no_valid_payout_progress','The simulation did not prove any valid successful holder payout.')
    return {'kind':'distribution_count','paid_count':paid,'eligible_count':maximum_paid,
        'partial':paid<maximum_paid,'per_nft_success_proven':False,
        'inspect_receipt_events_and_principal_ledger':True}


def simulate(p,header,block,tx,fee,*,confirmed,execution_gas=None,maximum_paid=None):
    """Probe, then validate the exact unsigned gas envelope, never a smaller batch."""
    raw=p.rpc.call('eth_getBlockByNumber',[hex(header['number']),False])
    if (not isinstance(raw,dict) or rpc_hash(raw.get('hash'),'management block hash')!=header['hash'] or
            rpc_quantity(raw.get('number'),'management block number')!=header['number'] or
            rpc_quantity(raw.get('timestamp'),'management block timestamp',minimum=1)!=header['timestamp']):
        raise ManagementBlocked('header_changed','The simulation block identity changed.')
    block_limit=rpc_quantity(raw.get('gasLimit'),'management block gas limit',minimum=21000)
    if block_limit>=1<<64:raise ManagementBlocked('invalid_block_gas','The confirmed block gas limit is invalid.')
    cap=min(integer(fee['max_gas_limit'],positive=True),block_limit)
    probe={**tx,'gas':hex(cap)}
    probed=p.rpc.call('eth_call',[probe,block]);_returned(probed,maximum_paid)
    estimate=rpc_quantity(p.rpc.call('eth_estimateGas',[probe,block]),'management estimated gas',minimum=21000)
    padded=(estimate*125+99)//100
    if padded>cap:
        raise ManagementBlocked('gas_headroom_exceeded','The estimate lacks the original reviewed25% gas headroom.')
    # distributePrincipal can return successfully after a gasleft() early break.
    # Its estimator does not prove a completed batch. Keep the explicitly
    # configured (block-bounded) budget, never an estimated cheaper prefix.
    limit=(cap if maximum_paid is not None else padded) if execution_gas is None else execution_gas
    if not 21000<=limit<=cap or padded>limit:
        raise ManagementBlocked('frozen_gas_insufficient','The unchanged transaction gas budget no longer fits this operation.')
    price=rpc_quantity(p.rpc.call('eth_gasPrice',[]),'management gas price',minimum=1)
    cost=limit*price
    if price>integer(fee['max_gas_price_wei'],positive=True) or cost>integer(fee['max_network_fee_wei'],positive=True):
        raise ManagementBlocked('fee_budget_exceeded','Network fees exceed the original operator limits.')
    balance=rpc_quantity(p.rpc.call('eth_getBalance',[tx['from'],block]),'management governance balance')
    if balance<cost:
        raise ManagementBlocked('insufficient_governance_gas','Governance lacks native currency for the full reviewed gas budget.')
    exact=p.rpc.call('eth_call',[{**tx,'gas':hex(limit)},block])
    result=_returned(exact,maximum_paid)
    if maximum_paid is None and exact!=probed:
        raise ManagementBlocked('simulation_output_changed','Exact-gas simulation differs from the full probe.')
    return {'state':'complete_at_confirmed_snapshot' if confirmed else 'complete_at_canonical_tip',
        'finality':'confirmation_depth_only' if confirmed else 'latest_canonical_only_not_confirmed',
        'header':header,'estimated_gas':str(estimate),'minimum_25_percent_padded_gas':str(padded),
        'transaction_gas':str(limit),'gas_limit_cap':str(cap),'block_gas_limit':str(block_limit),
        'gas_price_wei':str(price),'maximum_network_fee_wei':str(cost),'governance_balance_wei':str(balance),
        'gas_strategy':'explicit_batch_budget' if maximum_paid is not None else 'frozen_initial_padded_estimate',
        'result':result}


def _source_pins():
    root=Path(__file__).resolve().parents[1]
    names=('zzz_ops/management_review.py','zzz_ops/management_base.py','zzz_ops/management_custody.py',
        'zzz_ops/management_exit.py','zzz_ops/manual_lp_review.py')
    return {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}


def prepare(read_config,policy,request,*,rpc=None,clock=None,catalog=None):
    clock=clock or time.time;catalog=catalog or offline.Catalog();stage='input_validation'
    try:
        references=(read_config,policy,request);original=[digest(value) for value in references]
        config=copy.deepcopy(read_config);policy=copy.deepcopy(policy);s,adapter=selection(request)
        governance,fee=validate_policy(policy,catalog);source_pins=_source_pins()
        with request_scope(Budget(seconds=MAX_SECONDS,calls=MAX_CALLS,posts=3072)):
            p=Projection(config,rpc=rpc,clock=clock)
            if (p.accounting_version,p.custody_version,p.fee_intake_version)!=(7,5,1):
                raise ValueError('Only explicit accounting7/custody5 is supported')
            if p.identity!=policy['projection_sha256'] or p.max_age>120:
                raise ValueError('Exact fresh reviewed read configuration required')
            targets=[item.address for item in p.contracts.values()]+[item['address'] for item in policy['extra_contracts'].values()]
            if len(targets)!=len(set(targets)):raise ValueError('Manual runtime roles must be distinct')
            stage='initial_snapshot';header,head,block=p._snapshot()
            expire_at(min(s['expires_at'],header['timestamp']+p.max_age),clock)
            if not header['timestamp']<=s['expires_at']<=header['timestamp']+600:
                raise ManagementBlocked('invalid_original_expiry','Preserve an original expiry within600seconds of the snapshot.')
            snapshot=adapter.observe(ManagementReader(p,policy['extra_contracts'],block),s,governance)
            commitment=digest({'snapshot':snapshot,'policy_sha256':digest(policy),'configuration_sha256':p.identity,
                'selection_sha256':digest(request),'preparer_source_sha256':source_pins,'header':header})
            signature,args,_=adapter.call_spec(s,snapshot,'0x'+'1'*64)
            manifest={'schema':1,'profile':offline.PROFILE,'reference_sha256':catalog.reference_sha256,
                'source_snapshot_sha256':catalog.source_snapshot_sha256,
                'chain':{'id':str(p.chain),'controller':p.contracts['access'].address,'governance':governance,
                    'target':p.contracts['principal_exit'].address,'target_runtime_keccak256':p.contracts['principal_exit'].code_hash},
                'snapshot':{'block_number':str(header['number']),'block_hash':header['hash'],'timestamp':str(header['timestamp'])},
                'contract':'ZZZMigration','signature':signature,'arguments':_mark_review_hash(_canonical_arguments(args)),
                'review_notes_sha256':s['review_notes_sha256'],'evidence_sha256':s['evidence_sha256']+[commitment]}
            review=catalog.prepare(manifest);signature,args,data=adapter.call_spec(s,snapshot,review['review_hash'])
            tx={'from':governance,'to':p.contracts['principal_exit'].address,'data':data,'value':'0x0'}
            distribution=s['action']=='distribute_principal'
            maximum_paid=snapshot['controls']['payout']['eligible_count'] if distribution else None
            stage='initial_simulation'
            initial=simulate(p,header,block,tx,fee,confirmed=True,maximum_paid=maximum_paid)
            gas=int(initial['transaction_gas']);tx['gas']=hex(gas)
            stage='final_snapshot';number=rpc_quantity(p.rpc.call('eth_blockNumber',[]),'management final head')
            latest=p._header(hex(number));p._fresh(latest)
            if number<head or latest['timestamp']<header['timestamp'] or not latest['timestamp']<=s['expires_at']<=latest['timestamp']+600:
                raise ManagementBlocked('original_expiry_or_head_changed','The original expiry or canonical head is no longer valid.')
            final_block={'blockHash':latest['hash'],'requireCanonical':True}
            final_snapshot=adapter.observe(ManagementReader(p,policy['extra_contracts'],final_block),s,governance)
            if snapshot['controls']!=final_snapshot['controls']:
                raise ManagementBlocked('custody_or_controls_changed','Custody, ownership, exit progress or governed controls changed; prepare again.')
            final_spec=adapter.call_spec(s,final_snapshot,review['review_hash'])
            if final_spec!=(signature,args,data):
                raise ManagementBlocked('exact_arguments_changed','The original exact operation inputs changed.')
            stage='final_simulation'
            final=simulate(p,latest,final_block,tx,fee,confirmed=False,execution_gas=gas,maximum_paid=maximum_paid)
            stage='final_canonicality';p._finish(header)
            last_number=rpc_quantity(p.rpc.call('eth_blockNumber',[]),'management last head')
            last=p._header(hex(last_number));p._fresh(last)
            if p._header(hex(latest['number']))!=latest:
                raise ManagementBlocked('final_anchor_changed','The final simulation anchor changed.')
            if (last_number<number or last['timestamp']<latest['timestamp'] or
                    not last['timestamp']<=s['expires_at']<=last['timestamp']+600 or
                    clock()>=min(s['expires_at'],header['timestamp']+p.max_age)):
                raise ManagementBlocked('review_expired','The original review expired after the final simulation.')
            if [digest(value) for value in references]!=original or _source_pins()!=source_pins:
                raise ManagementBlocked('local_inputs_changed','Local source or reviewed inputs changed during preparation.')
            onchain_deadline=s['action'] in ('park','resume','close_residual','close_bucket')
            return {'schema':1,'kind':'unsigned_operator_management_preparation','action':s['action'],
                'read_only':True,'production_approved':False,'ready_for_submission':False,
                'governance_wallet_scope':'direct_empty_code_governance_eoa_only','operator_revalidation_required':True,
                'transaction':{**tx,'chainId':hex(p.chain)},'signature':signature,'arguments':_canonical_arguments(args),
                'review':review,'configuration_sha256':p.identity,'policy_sha256':digest(policy),
                'snapshot_commitment_sha256':commitment,'preparer_source_sha256':source_pins,
                'runtime_pins':{**{role:{'address':item.address,'code_hash':item.code_hash} for role,item in p.contracts.items()},
                    **copy.deepcopy(policy['extra_contracts'])},'original_selection':copy.deepcopy(request),
                'original_fee_policy':copy.deepcopy(fee),'snapshot':snapshot,'final_snapshot':final_snapshot,
                'operator_effect':EFFECTS[s['action']],
                'provenance':{**header,'finality':'confirmation_depth_only','confirmations':p.confirmations,
                    'eip1898_require_canonical':True},'final_control_head':{**latest,'finality':'latest_canonical_only_not_confirmed',
                    'eip1898_require_canonical':True},'last_head':last,'simulation':{'initial':initial,'final':final},
                'network_gas':{key:final[key] for key in ('transaction_gas','gas_limit_cap','gas_price_wei','maximum_network_fee_wei','gas_strategy')},
                'expires_at':min(s['expires_at'],header['timestamp']+p.max_age),'operator_original_expiry':s['expires_at'],
                'contract_deadline_enforced':onchain_deadline,
                'inclusion_semantics':{'onchain_deadline_enforced':onchain_deadline,
                    'allocation_cohort':'cursor_at_inclusion' if s['action']=='allocate_principal' else None,
                    'distribution_beneficiary':'current_owner_at_inclusion' if distribution else None,
                    'receipt_reconciliation_required':s['action'] in EXIT_ACTIONS,
                    'exact_post_inclusion_cohort_or_beneficiary_guaranteed':False},
                'work_budget':{'rpc_calls':MAX_CALLS,'seconds':MAX_SECONDS,'posts':3072},
                'limitations':['Read-only direct-EOA preparation, not signing, a nonce reservation, pending-journal review or execution approval.',
                    'Later market, ownership, exit cursor, settings, reorgs, local I/O and inclusion can invalidate the review.',
                    'Distribution returns a count only; no simulated per-ID success or automatic retry queue is inferred.',
                    'Existing B/C/D has its separate explicit selection format; no automatic force, floor or route selection.',
                    'Runtime/source pins and simulations do not prove RPC honesty or target gas/host qualification.']}
    except Exception as exc:
        exc.management_stage=stage
        raise


def main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self,message):raise ValueError('Invalid typed management arguments')
    parser=Parser(description=__doc__)
    for name in ('read-config','policy','selection','output'):parser.add_argument('--'+name,required=True,type=Path)
    publishing=False
    try:
        args=parser.parse_args(argv)
        if args.output.exists():raise ManagementBlocked('existing_output_preserved','The output already exists; preserve and inspect it or select a new filename.')
        config=offline.load(args.read_config);policy=offline.load(args.policy);chosen=offline.load(args.selection)
        result=prepare(config,policy,chosen);raw=offline.render(result);publishing=True
        write_exclusive(args.output,raw)
        print(json.dumps({'created':True,'kind':'unsigned_operator_management_preparation','ready_for_submission':False,
            'transaction_submitted':False}))
        return 0
    except Exception as exc:
        reason='management_preparation_unavailable_or_invalid';message='The selected operation or a required read could not be validated; no draft was created.'
        extra={}
        if publishing:
            reason='artifact_publication_uncertain';message='Inspect any complete output artifact; publication was not confirmed. Do not overwrite it or assume a transaction was sent.'
        elif isinstance(exc,ManagementBlocked):reason=exc.code;message=exc.message
        elif isinstance(exc,UnsupportedGovernanceEnvelope):reason='unsupported_contract_wallet_envelope';message='This adapter requires the current direct empty-code governance wallet.'
        elif isinstance(exc,WorkLimit):reason='work_'+exc.reason;message='The bounded review expired or exhausted its read budget.'
        elif isinstance(exc,RemoteRPCError):
            reason='rpc_'+exc.reason;message='A required RPC read or exact simulation failed; no fallback transaction was prepared.'
            extra={'rpc_method':exc.method if isinstance(exc.method,str) and exc.method in Rpc.READ_METHODS else None,
                'rpc_code':exc.code if type(exc.code) is int else None}
        print(json.dumps({'ok':False,'read_only':True,'transaction_submitted':False,
            'output_may_exist':publishing or isinstance(exc,ManagementBlocked) and exc.code=='existing_output_preserved',
            'stage':'artifact_publication' if publishing else getattr(exc,'management_stage','input_or_output'),
            'reason':reason,'message':message,**extra}),file=sys.stderr)
        return 1
