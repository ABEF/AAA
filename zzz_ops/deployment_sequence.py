"""Conditional direct-EOA CREATE sequencing, never deployment or nonce adoption.

The existing constructor reviewer stays byte-identical. This wrapper supplies
only the 25 conditional top-level addresses; factory children remain unknown.
One ordinary successful transaction per step is an explicit unverified premise.
"""
from __future__ import annotations
import copy
from zzz_ops import deployment_plan as D

MAX_ACCOUNT_NONCE = (1 << 64)-1
TRANSACTION_COUNT = 44
EXPECTED_ORDER_SHA256 = 'cc20f3dee4bf1893c67ec970369589e007616dcffe27a32ad07fed951da5a498'
EXPECTED_GRAPH_SHA256 = '9b77ae9780bb3c16478bfa260c7894ca4e83bd77ae92a51932ddee0b88c84188'
PRODUCER_FILES = ('zzz_ops/deployment_sequence.py', 'scripts/prepare-deployment-sequence.py',
                  'zzz_ops/deployment_plan.py', 'zzz_ops/abi.py')
TRANSACTION_KINDS = frozenset(('conditional_constructor', 'bootstrap_binding',
                              'bootstrap_module_binding', 'bootstrap_helper_binding'))


def producer_sources():
    return {n:D.sha((D.ROOT/n).read_bytes().replace(b'\r\n',b'\n')) for n in PRODUCER_FILES}


def validate_sender_nonce(deployer, starting_nonce):
    sender=D._address(deployer)
    if sender in set(D.NATIVE.values()) | {D.SEADROP}:
        D.fail('deployer_is_known_contract')
    nonce=int(D._uint(starting_nonce,64))
    # EIP-2681 forbids tx nonces >=2^64-1. Also refuse a construction
    # phase that leaves bootstrap with no possible later setup transaction.
    # This reserves no nonce and does not guess how many setup calls are needed.
    if nonce+TRANSACTION_COUNT >= MAX_ACCOUNT_NONCE:
        D.fail('sequence_exhausts_account_nonce')
    return sender,nonce


def create_address(deployer, nonce):
    sender=D._address(deployer)
    if type(nonce) is not int or not 0 <= nonce < MAX_ACCOUNT_NONCE:
        D.fail('invalid_create_nonce')
    value=nonce.to_bytes((nonce.bit_length()+7)//8,'big')
    encoded=(value if len(value)==1 and value[0]<128 else bytes([0x80+len(value)])+value)
    payload=b'\x94'+bytes.fromhex(sender[2:])+encoded
    return '0x'+D.keccak256(bytes([0xc0+len(payload)])+payload)[12:].hex()


def _order():
    graph={'top':D.TOP,'internal':D.INTERNAL,'modules':D.MODULES}
    if D.sha(D.canonical(graph))!=EXPECTED_GRAPH_SHA256:
        D.fail('sequence_constructor_graph_changed')
    rows=D.construction_order()
    if D.sha(D.canonical(rows))!=EXPECTED_ORDER_SHA256:
        D.fail('sequence_construction_order_changed')
    transactions=[row for row in rows if row['kind'] in TRANSACTION_KINDS]
    kinds={kind:sum(row['kind']==kind for row in transactions) for kind in TRANSACTION_KINDS}
    if (len(transactions),kinds['conditional_constructor'],kinds['bootstrap_binding'],
            kinds['bootstrap_module_binding'],kinds['bootstrap_helper_binding']) != (44,25,1,16,2):
        D.fail('sequence_transaction_counts_changed')
    return transactions,[row for row in rows if row['kind']=='unverified_setup_checklist']


def derive(deployer, starting_nonce):
    sender,start=validate_sender_nonce(deployer,starting_nonce)
    order,setup=_order()
    predicted={row['role']:create_address(sender,start+n) for n,row in enumerate(order)
               if row['kind']=='conditional_constructor'}
    if len(predicted)!=25 or len(set(predicted.values()))!=25 or sender in predicted.values() or \
            set(predicted.values()) & (set(D.NATIVE.values())|{D.SEADROP}):
        D.fail('predicted_address_collision')
    top={role:(name,refs) for role,name,refs in D.TOP};created=set();seen=set();transactions=[]
    for offset,step in enumerate(order):
        if not set(step['requires'])<=seen:D.fail('sequence_dependency_not_created')
        row={'id':step['id'],'kind':step['kind'],'nonce':str(start+offset),'from':sender,
             'authority_verified':False,'caller_condition':'same direct EOA must be actual unsealed Access.bootstrap()'}
        if step['kind']=='conditional_constructor':
            role=step['role'];name,refs=top[role]
            for ref in refs:
                if ref.startswith('p:') and ref[2:] not in created:D.fail('sequence_forward_constructor_reference')
                if ref not in ('chain','zero') and not ref.startswith(('p:','i:')):D.fail('sequence_unresolved_constructor_reference')
            row.update(role=role,contract=name,to=None,predicted_address=predicted[role])
            created.add(role)
        else:
            if step['kind']=='bootstrap_module_binding':
                role=step['role'];target='access'
                row.update(role=role,module_id=step['module_id'])
            elif step['id']=='bind:protocol_policy':role='protocol_policy';target='access'
            elif step['id']=='bind:lp_converter':role='lp_converter';target='rewards'
            elif step['id']=='bind:seadrop_mint':role='seadrop_mint';target='nft'
            else:D.fail('sequence_unknown_binding')
            if role not in created or target not in created:D.fail('sequence_binding_target_not_created')
            row.update(to=predicted[target],bound_role=role,bound_address=predicted[role],
                       call=step['call'],calldata_prepared=False)
        transactions.append(row);seen.add(step['id'])
    return {'schema':1,'kind':'offline_deployment_sequence_prediction','chain_id':'4663',
        'deployer':sender,'deployer_kind':'assumed_direct_eoa','starting_nonce':str(start),
        'last_nonce':str(start+TRANSACTION_COUNT-1),'next_nonce':str(start+TRANSACTION_COUNT),
        'remaining_legal_transactions':str(MAX_ACCOUNT_NONCE-start-TRANSACTION_COUNT),
        'transaction_count':44,'creation_count':25,'binding_count':19,
        'construction_order_sha256':EXPECTED_ORDER_SHA256,'constructor_graph_sha256':EXPECTED_GRAPH_SHA256,
        'predicted_addresses':predicted,'transactions':transactions,'unprepared_setup_checklist':copy.deepcopy(setup),
        'prediction_scope':'Conditional direct-EOA top-level CREATE only; not observed, reserved or simulated.',
        'child_address_predictions_performed':False,'factory_nonce_assumed':False,'nonce_reserved':False,
        'rpc_performed':False,'simulation_performed':False,'transaction_submitted':False,
        'ready_for_submission':False,'production_approved':False,'binding_addresses_verified':False,
        'assumptions':[
            'One ordinary successful transaction per listed step, in exact order, from this same direct bootstrap EOA.',
            'No inserted, omitted, failed, cancelled or replacement transaction and no other use of the sender nonce.',
            'No contract/factory/Safe/user-operation/batch/delegated-account or authorization-list deployment path.',
            'Sender code, balance, control, live confirmed/pending nonce and target address availability are not checked.',
            'Chain4663 must be verified live; CREATE address mathematics itself is not chain-specific.',
            'Later configuration and sealing calls consume additional unplanned nonces; remaining capacity is not approval.']}


def prepare(raw, deployer, starting_nonce, root=D.ROOT, build_profile=D.DEFAULT_BUILD_PROFILE):
    D.trusted_build(build_profile)
    sequence=derive(deployer,starting_nonce);producer=producer_sources()
    value=D.validate(copy.deepcopy(raw));original=copy.deepcopy(value)
    for role,predicted in sequence['predicted_addresses'].items():
        assigned=value['planned_addresses'][role]
        if assigned is not None and assigned!=predicted:D.fail('predicted_address_mismatch')
        value['planned_addresses'][role]=predicted
    value=D.validate(value)  # Preserve constructor/authority/native collisions after derivation.
    plan=D.prepare(value,root=root,build_profile=build_profile)
    if plan['inputs']!=value or plan['construction_order']!=D.construction_order() or \
            plan['counts']!={'top_level':25,'internal_helpers':12,'inert_data_children':2,'total_instances':39}:
        D.fail('sequence_constructor_plan_differs')
    if any(plan[flag] is not False for flag in ('rpc_performed','simulation_performed','ready_for_submission',
            'production_approved','transaction_submitted','binding_addresses_verified','address_predictions_performed')):
        D.fail('sequence_constructor_plan_claim_changed')
    by_role={row['role']:row for row in plan['instances'] if row['mode']=='top_level'}
    for row in sequence['transactions']:
        if row['kind']=='conditional_constructor':
            instance=by_role[row['role']]
            if instance['planned_address']!=row['predicted_address']:D.fail('sequence_constructor_address_differs')
            row.update(constructor_payload_complete=instance['constructor_payload_complete'],
                       full_initcode_sha256=None if instance['full_initcode_hex'] is None else
                            D.sha(bytes.fromhex(instance['full_initcode_hex'][2:])),
                       constructor_plan_role=instance['role'])
    complete=plan['input_assignments_complete'] and plan['top_level_constructor_payloads_complete']
    result={**sequence,'kind':'offline_deployment_sequence_preparation','profile':D.PROFILE,'build_profile':build_profile,
        'offline_only':True,'address_predictions_performed':True,'producer_sources':producer,
        'status':'offline_sequence_and_top_level_payloads_complete_pending_live_verification' if complete else 'blocked_preview_missing_inputs',
        'original_input_sha256':D.sha(D.canonical(original)),
        'sequence_input_sha256':D.sha(D.canonical({'deployer':sequence['deployer'],'starting_nonce':sequence['starting_nonce'],
            'constructor_input':value,'construction_order_sha256':EXPECTED_ORDER_SHA256,'build_profile':build_profile})),
        'constructor_plan':plan,
        'constructor_plan_scope':'Unmodified component regards its input addresses as assignments; only this wrapper derives conditional top-level addresses.',
        'release_prerequisites':[
            'Independently verify direct EOA control/empty-code policy, network4663 and exact confirmed/pending starting nonce.',
            'Verify actual CREATE receipts, address availability, bootstrap/getters, runtime immutables and every binding before relying on them.',
            'Any changed/failed/unplanned/cancelled/replaced transaction requires reviewed reconciliation; this fresh-phase tool cannot resume a partial deployment or shift saved nonces.',
            'Read every factory-created child from actual authenticated getters; predictions do not freeze permissionless factory nonces.',
            'Review remaining configuration, additional nonces, gas/fees, feeds/routes/VRF/OpenSea/content/services and independent release approval.']}
    if derive(deployer,starting_nonce)!=sequence_without_payload(sequence) or producer_sources()!=producer:
        D.fail('sequence_source_or_graph_changed_during_preparation')
    result['manifest_sha256']=D.sha(D.canonical(result))
    return result


def sequence_without_payload(sequence):
    """Remove only this wrapper's post-review links for exact final graph recheck."""
    value=copy.deepcopy(sequence)
    for row in value['transactions']:
        for key in ('constructor_payload_complete','full_initcode_sha256','constructor_plan_role'):row.pop(key,None)
    return value
