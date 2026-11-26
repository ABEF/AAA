"""New c814 independent, offline private-vector checker.

Only stdlib imports and fixed read-only paths. verify() returns public hashes,
checks and arithmetic; it never exports configuration or signer contents, imports
the application, makes RPC/process calls, writes files or trusts model success.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import stat
import time

LAB=Path('/opt/popl-ubuntu-backup-recovery-20261126-c814')
SOURCE=LAB/'source/contracts'
MODEL=LAB/'runtime/run-001/model'
CASE=MODEL/'supervisor'
CONTROL=LAB/'control'
HEAD='5662a81ad9c9c5953d3578974e0c5840d626ba97'
SOURCE_FILES=('keeper/monitor.py','keeper/ops.py','keeper/health.py',
 'keeper/rebalance_confirmation.py','keeper/compound_policy.py','keeper/cast_process.py',
 'zzz_ops/protocol_policy.py','zzz_ops/lp_execution.py','zzz_ops/execution_price.py',
 'zzz_ops/rebalance_confirmation.py','zzz_ops/abi.py','zzz_ops/rpc.py','zzz_ops/state.py')
PRODUCERS=('keeper/recovery_bundle.py','scripts/keeper-recovery.py')
PINS={'keeper/monitor.py':'90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f',
 'keeper/recovery_bundle.py':'fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268',
 'scripts/keeper-recovery.py':'450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'}
FLAGS={'unsigned':True,'live_ready':False,'canonical_state_verified':False,
 'old_keeper_fenced':False,'signer_material_included':False,
 'configuration_installed':False,'service_restarted':False}


def need(value,label):
    if not value:raise ValueError('Independent c814 review refused: '+label)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')


def pairs(rows):
    value={}
    for key,item in rows:
        need(key not in value,'duplicate JSON field');value[key]=item
    return value


def decode(raw):
    def constant(_):raise ValueError('Independent c814 review refused: nonfinite JSON')
    value=json.loads(raw.decode('utf8'),object_pairs_hook=pairs,parse_constant=constant)
    need(type(value)is dict,'object required')
    return value


def uint(value,maximum=(1<<256)-1):
    need(type(value)is int and 0<=value<=maximum,'unsigned integer required');return value


def quantity(value):
    need(type(value)is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})',value),
         'canonical RPC quantity required')
    return int(value,16)


def digest(value):
    need(type(value)is str and re.fullmatch('[0-9a-f]{64}',value),'SHA256 required');return value


def txhash(value):
    need(type(value)is str and re.fullmatch('0x[0-9a-fA-F]{64}',value)and int(value,16),
         'nonzero transaction/block hash required');return value.lower()


def verify():
    deadline=time.monotonic()+30;artifacts={};checks=[]
    def read(path,maximum=2*1024*1024):
        need(time.monotonic()<deadline,'cooperative review deadline')
        need(path.is_absolute()and path.is_relative_to(LAB),'fixed lab path required')
        for part in (*reversed(path.parents),path):
            info=part.lstat();need(not stat.S_ISLNK(info.st_mode),'linked evidence refused')
        before=path.lstat()
        need(stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_uid in (0,65534)
             and not before.st_mode&0o022 and 0<before.st_size<=maximum,'bounded regular evidence required')
        with path.open('rb')as stream:raw=stream.read(maximum+1)
        after=path.lstat()
        need(len(raw)==before.st_size and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
             (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'evidence changed while reading')
        artifacts[str(path.relative_to(LAB))]={'bytes':len(raw),'sha256':sha(raw)}
        return raw
    def load(path):return decode(read(path))
    def root_marker(name):
        need(name in ('FENCED.json','RECOVERY_COMPLETE.json','DRY_COMPLETE.json'),
             'closed root marker name required')
        parent=CONTROL.lstat();item=(CONTROL/name).lstat()
        need(stat.S_ISDIR(parent.st_mode)and parent.st_uid==0 and not parent.st_mode&0o022 and
             item.st_uid==0 and stat.S_IMODE(item.st_mode)==0o644,
             'root acknowledgment ownership or permissions differ')
        return load(CONTROL/name)
    def passed(label):checks.append({'check':label,'passed':True})
    def fixed_flags(value):
        need(all(value.get(k)is v for k,v in FLAGS.items()),'unsigned flags changed')

    source_manifest=load(LAB/'inputs/SOURCE_MANIFEST.json')
    need(source_manifest.get('source_head')==HEAD and source_manifest.get('approved_worktree_overrides')==[],
         'reviewed HEAD source required')
    members=source_manifest['members'];source_hashes={}
    for name in (*SOURCE_FILES,*PRODUCERS):
        raw=read(SOURCE/name)
        need(members[name]['sha256']==sha(raw)and members[name]['bytes']==len(raw),'source manifest pin differs')
        if name in PINS:need(sha(raw)==PINS[name],'independently reviewed production pin differs')
        if name in SOURCE_FILES:source_hashes[name]=sha(raw)
    passed('exact_HEAD_and_thirteen_daemon_sources_with_reviewed_tool_sources')

    evidence=load(CASE/'EVIDENCE.json')
    need(evidence.get('source_head')==HEAD and evidence.get('same_host_only')is True and
         evidence.get('raw_configuration_exported')is False and evidence.get('signer_material_bundled')is False,
         'declared fixture scope differs')
    old_raw=read(CASE/'ORIGINAL_CONFIG.json');old=decode(old_raw)
    target_raw=read(CASE/'TARGET_CONFIG.json');target=decode(target_raw)
    need(read(CASE/'actor/config.json')==old_raw,'original actual configuration changed')
    changed=sorted(k for k in set(old)|set(target)if encode(old.get(k))!=encode(target.get(k)))
    expected_paths={'state_path':str(CASE/'restore-001/keeper-state.json'),
                    'health_path':str(CASE/'restore-001/health.json'),
                    'lock_path':str(CASE/'restore-001/keeper.lock')}
    need(changed==['health_path','lock_path','state_path'] and
         changed==evidence['changed_configuration_keys'] and
         all(target[k]==v for k,v in expected_paths.items()),'only three reviewed runtime paths may change')
    need(old['state_path']==str(CASE/'actor/state.json'),'original runtime path differs')
    need(sha(old_raw)==evidence['configuration_raw_sha256'] and
         sha(encode(old))==evidence['configuration_semantic_sha256'] and
         sha(target_raw)==evidence['target_configuration_raw_sha256'] and
         sha(encode(target))==evidence['target_configuration_semantic_sha256'],
         'raw or semantic configuration identity differs')
    need(old['chain_id']==4663 and type(old['chain_id'])is int and old['interval_seconds']==240 and
         old['confirmations']==12 and old['max_gas_limit']==24000000 and
         int(old['max_gas_price_wei'])==5000000000 and
         int(old['max_transaction_cost_wei'])==10**16 and int(old['max_daily_cost_wei'])==5*10**16 and
         old['receipt_fee_policy']=='included' and old['maintenance']['harvest_interval_seconds']==3600,
         'original operating limits differ')
    passed('private_actual_configuration_diff_is_exactly_three_runtime_paths_original_preserved')

    pending_raw=read(CASE/'PENDING.json');pending_state=decode(pending_raw)
    identity_fields=('chain_id','sender','contracts','accounting_model','accounting_version',
      'custody_version','fee_intake_version','portfolio_version','maintenance_policy_version',
      'rebalance_confirmation_version','execution_quality_version','protocol_policy_version',
      'execution_price_version','lp_routing_version','royalty_settlement_version')
    expected_identity={key:old[key]for key in identity_fields}
    journal_identity=('chain_id','sender','contracts','accounting_model','accounting_version',
                      'fee_intake_version','execution_price_version')
    need(encode({key:pending_state[key]for key in journal_identity})==
         encode({key:old[key]for key in journal_identity}),
         'full original journal deployment and accounting identity differs')
    restored_raw=read(CASE/'RESTORED_BEFORE_LOAD.json')
    need(pending_raw==restored_raw==read(CASE/'bundle-001/journal.json') and
         sha(pending_raw)==evidence['pending_journal_sha256']==evidence['restored_journal_sha256'] and
         read(CASE/'actor/state.json')==pending_raw,'initial restoration or original journal bytes differ')
    intent=pending_state['pending'];h=txhash(intent['hash'])
    need(h==evidence['known_hash'] and intent['nonce']==pending_state['next_nonce']==0 and
         type(intent['nonce'])is int and pending_state['spent']=={} and pending_state['receipt_anchor']is None,
         'fresh known pending identity differs')
    data=intent['data']
    need(type(data)is str and re.fullmatch('0x6cae7bf7[0-9a-fA-F]{128}',data)and
         intent['key']=='harvest:'+str(int(data[10:74],16)) and
         intent['to']==pending_state['contracts']['vault'] and intent['value']==0,
         'only original exact harvest may recover')
    manifest_raw=read(CASE/'bundle-001/manifest.json');manifest=decode(manifest_raw)
    need(sha(manifest_raw)==evidence['backup_manifest_sha256'],'trusted backup pin differs')
    fixed_flags(manifest)
    need(manifest['configuration_raw_sha256']==sha(old_raw) and
         manifest['configuration_sha256']==sha(encode(old)) and manifest['source_files_sha256']==source_hashes,
         'backup configuration or source identities differ')
    need(encode(manifest['identity'])==encode(expected_identity), 'backup typed identity differs')
    need(manifest['files']==[{'path':'journal.json','bytes':len(pending_raw),'sha256':sha(pending_raw)}] and
         evidence['bundle_file_names']==['journal.json','manifest.json'] and
         evidence['restore_file_names']==['RESTORE_PLAN.json','keeper-state.json'],
         'fixed package inventory differs')
    plan_raw=read(CASE/'restore-001/RESTORE_PLAN.json');plan=decode(plan_raw);fixed_flags(plan)
    need(sha(plan_raw)==evidence['restore_plan_sha256'] and
         plan['manifest_sha256']==sha(manifest_raw) and
         plan['journal']=={'path':'keeper-state.json','bytes':len(pending_raw),'sha256':sha(pending_raw)} and
         plan['configuration_raw_sha256']==sha(old_raw) and
         plan['configuration_sha256']==sha(encode(old)), 'unsigned restore plan binding differs')
    need(encode(plan['identity'])==encode(expected_identity), 'restore plan typed identity differs')
    runs=evidence['tool_runs']
    need([r['action']for r in runs]==['backup','verify','restore'] and
         all(r['returncode']==0 and r['signing_enabled']is False and r['secret_contents_exported']is False and
             r['configuration_sha256']==sha(old_raw)for r in runs) and
         [r['digest']for r in runs]==[sha(manifest_raw),sha(manifest_raw),sha(plan_raw)],
         'actual unsigned tool composition differs')
    passed('exact_private_pending_backup_restore_bytes_and_unsigned_manifest_plan_provenance')

    fence=root_marker('FENCED.json')
    need(encode(fence)==encode(evidence['fence_marker']) and fence.get('schema')==1 and
         fence.get('accepted_hash')==h and fence.get('journal_sha256')==sha(pending_raw) and
         fence.get('keeper_fenced_empty')is True and fence.get('automatic_restart_inhibited')is True,
         'root source-writer fence acknowledgment differs')
    need(stat.S_IMODE((CASE/'actor/secrets').lstat().st_mode)==0,'signer directory was not made unreadable')
    for name,status in (('RECOVERY_COMPLETE.json',1),('DRY_COMPLETE.json',0)):
        marker=root_marker(name)
        need(marker.get('schema')==1 and marker.get('signing_enabled')is False and
             marker.get('accepted_hash')==h and marker.get('actual_exit_status')==status,
             'root unsigned process completion differs')
        need(marker.get('direct_exec_argv')==['/usr/bin/python3','-m','keeper.monitor','--config',
                                            str(CASE/'TARGET_CONFIG.json'),'--once'],
             'unsigned stock argv differs')
    passed('root_fence_acknowledgment_and_two_unsigned_process_results_with_unreadable_signer_directory')

    canonical=load(CASE/'CANONICAL.json');tx=canonical['transaction_without_signature']
    receipt,block,head=(canonical[k]for k in ('receipt','receipt_block','head'))
    fee=intent['fee_review']
    need(not {'r','s','v','yParity','raw','rawTransaction'}&set(tx),'signature material in public transaction')
    need(txhash(tx['hash'])==h==txhash(receipt['transactionHash']) and
         tx['from'].lower()==old['sender']==pending_state['sender'] and tx['to'].lower()==intent['to'] and
         tx['input']==data and quantity(tx['nonce'])==0 and quantity(tx['value'])==0 and
         quantity(tx['chainId'])==4663 and quantity(tx['gas'])==fee['gas_limit'],
         'actual accepted transaction differs from original intent')
    kind=quantity(tx['type']);need(kind in (0,1,2),'unsupported transaction type')
    cap=quantity(tx['maxFeePerGas']if kind==2 else tx['gasPrice'])
    if kind==2:
        base=quantity(block['baseFeePerGas']);tip=quantity(tx['maxPriorityFeePerGas'])
        need(base<=cap and tip<=cap,'invalid canonical dynamic fee inputs');price=min(cap,base+tip)
    else:price=cap
    gas=quantity(receipt['gasUsed']);l1=quantity(receipt.get('l1Fee','0x0'));paid=gas*price+l1
    need(fee['schema']in (1,2) and type(fee['schema'])is int and
         0<gas<=quantity(tx['gas'])<=24000000 and 0<price<=cap==fee['max_fee_per_gas']<=5000000000 and
         fee['receipt_fee_policy']=='included' and l1==fee['l1_fee_allowance_wei']==0 and
         fee['maximum_cost_wei']==fee['gas_limit']*cap<=10**16,
         'original fee envelope or canonical cost differs')
    if fee['schema']==2:
        need(kind==2 and quantity(tx['maxPriorityFeePerGas'])==0 and
             fee['execution_fee_model']=='eip1559_zero_tip','captured zero-tip profile differs')
    need(receipt['status']=='0x1' and receipt['blockHash']==tx['blockHash']==block['hash'] and
         receipt['blockNumber']==tx['blockNumber']==block['number'] and
         receipt['transactionIndex']==tx['transactionIndex'] and
         quantity(head['number'])-quantity(block['number'])+1==12==canonical['confirmations'] and
         quantity(block['timestamp'])<=int(data[74:],16), 'canonical inclusion or twelve confirmations differ')
    settled_raw=read(CASE/'SETTLED_JOURNAL.json');settled=decode(settled_raw)
    dry_raw=read(CASE/'DRY_JOURNAL.json');dry=decode(dry_raw)
    need(read(CASE/'restore-001/keeper-state.json')==dry_raw,'actual target final journal differs')
    day=dt.datetime.fromtimestamp(quantity(block['timestamp']),dt.timezone.utc).date().isoformat()
    observation={'transaction':h,'reported_price_wei':quantity(receipt['effectiveGasPrice']),
                 'execution_price_wei':price,'gas_used':gas,'l1_fee_wei':l1,
                 'receipt_fee_policy':'included','cost_wei':paid}
    anchor={'number':quantity(block['number']),'hash':block['hash'],
            'timestamp':quantity(block['timestamp']),'nonce':0}
    need(settled['pending']is None and type(settled['next_nonce'])is int and settled['next_nonce']==1 and
         encode(settled['spent'])==encode({day:paid}) and settled['receipt_anchor']==anchor and
         settled['last_fee_observation']==observation and settled['last'][intent['key']]==anchor['timestamp'],
         'settled accounting not exactly original receipt once')
    for key in ('pending','next_nonce','spent','receipt_anchor','last_fee_observation','last'):
        need(encode(dry.get(key))==encode(settled.get(key)),'dry review repeated or changed settled accounting')
    need(dry.get('conversion_turn',0)==(settled.get('conversion_turn',0)+1)%3,
         'ordinary dry-cycle conversion turn did not advance once')
    allowed={'conversion_turn','bucket_cursor'}
    need({k for k in set(settled)|set(dry)if encode(settled.get(k))!=encode(dry.get(k))}<=allowed,
         'unexpected ordinary-cycle journal mutation')
    passed('independent_canonical_receipt_fee_day_anchor_nonce_once_and_documented_dry_scheduler_delta')

    recovered=load(MODEL/'SETTLED.json');fresh=load(MODEL/'DRY.json')
    for row,status,exit_status in ((recovered,'degraded',1),(fresh,'dry_run_v2',0)):
        health=row['health']
        need(row['accepted_hash']==h and row['actual_exit_status']==exit_status and
             health['status']==status and health['live']is False and health['pending']is False and
             health['pending_action']is None and health['configuration_sha256']==sha(encode(target)) and
             health['sender']==old['sender'] and health['chain_id']==4663,
             'actual unsigned health phase differs')
    need(recovered['health']['rebalance_confirmation_health']['policy']['state']=='pending_recovery' and
         fresh['health']['rebalance_confirmation_health']['policy']['state']=='observed_this_cycle',
         'receipt refresh and fresh metadata phases not distinct')
    initial=load(CASE/'FINANCIAL_INITIAL.json');included=load(CASE/'FINANCIAL_INCLUDED.json')
    final=load(CASE/'FINANCIAL_FINAL.json')
    need(set(initial)==set(included)==set(final)=={'rights','physical','money','vault_balances'},
         'physical financial vector scope differs')
    need(encode(initial['rights'])==encode(included['rights'])==encode(final['rights']) and
         encode(initial['physical'])==encode(included['physical'])==encode(final['physical']),
         'harvest changed NFT rights or physical LP principal')
    need(encode(included)==encode(final),'unsigned recovery changed post-inclusion financial state')
    preserved=load(CASE/'SOURCE_PRESERVED.json')
    need(preserved['original_configuration_unchanged']is True and preserved['original_journal_unchanged']is True and
         preserved['configuration_sha256']==sha(old_raw) and preserved['journal_sha256']==sha(pending_raw),
         'actual source preservation readback differs')
    need(encode(preserved['node_nonces'])==encode({'latest':1,'pending':1})and
         all(type(preserved.get(key))is int and preserved[key]==1 for key in
             ('raw_attempts','raw_forwarded','raw_validated','raw_gateway_attempts')),
         'actual one-submission/no-resend and node nonce vectors differ')
    passed('actual_unsigned_health_transition_and_all_three_financial_vectors_with_original_source_readback')

    return {'schema':1,'success':True,'source_head':HEAD,'checks':checks,'artifacts':artifacts,
      'configuration_contents_exported':False,'checker_opened_signer_material':False,
      'original_configuration_raw_sha256':sha(old_raw),'target_configuration_raw_sha256':sha(target_raw),
      'exact_changed_configuration_keys':changed,'pending_journal_sha256':sha(pending_raw),
      'restored_before_load_sha256':sha(restored_raw),'settled_journal_sha256':sha(settled_raw),
      'dry_journal_sha256':sha(dry_raw),'actual_paid_keeper_transactions':1,
      'keeper_raw_resends':0,
      'canonical_execution_price_wei':price,'gas_used':gas,'paid_wei':paid,
      'financial_initial_sha256':sha(encode(initial)),'financial_included_sha256':sha(encode(included)),
      'financial_final_sha256':sha(encode(final)),'financial_after_vectors_available':True,
      'same_host_only':True,'native_argv_and_final_cleanup_review_required':True,
      'original_host_preservation_review_required':True,'public_transactions':0,'new_seals':0,
      'old_test_bodies_run':0,'production_approved':False,
      'verifier_sha256':sha(read(Path(__file__)))}
