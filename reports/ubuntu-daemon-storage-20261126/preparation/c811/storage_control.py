"""Closed c811 native controls; no action on import, no arbitrary command/path.

Frozen c806 utilities supply bounded PID1/cgroup inspection only. All callable
operations below are fixed to this new lab and authenticate its source/intent.
"""
from pathlib import Path
import copy
import json
import os
import re
import stat
import native_base as N

LAB=Path('/opt/popl-ubuntu-daemon-storage-20261126-c811')
MODEL_UNIT=LAB.name+'-model.service'
KEEPER_UNIT=LAB.name+'-keeper.service'
RESOLVE_UNIT=LAB.name+'-resolve.service'
for key,value in {'LAB':LAB,'MODEL_UNIT':MODEL_UNIT,'KEEPER_UNIT':KEEPER_UNIT,
    'RESOLVE_UNIT':RESOLVE_UNIT,'UNITS':(MODEL_UNIT,KEEPER_UNIT,RESOLVE_UNIT),
    'SOURCE':LAB/'source/contracts','HELPERS':LAB/'source/helpers',
    'RUN':LAB/'runtime/run-001','MODEL':LAB/'runtime/run-001/model',
    'LIVE':LAB/'runtime/run-001/model/supervisor/actor',
    'CONFIG':LAB/'runtime/run-001/model/supervisor/actor/config.json',
    'READY':LAB/'runtime/run-001/model/READY.json',
    'HELD':LAB/'runtime/run-001/model/supervisor/HASH_SAVE_FAULT_ARMED.json',
    'BLOCKED':LAB/'runtime/run-001/model/supervisor/HASHLESS_RESTART_BLOCKED.json'}.items():setattr(N,key,value)
need=N.need

def ready():
    N._ownership()
    value=json.loads(N._read(N.READY,65536,owners=(0,N.UID)))
    raw=N._read(N.CONFIG,256*1024,owners=(0,N.UID));config=json.loads(raw)
    need(value.get('configuration_path')==str(N.CONFIG)and value.get('configuration_sha256')==N.digest(raw)
        and value.get('state_path')==str(N.LIVE/'state.json'),'Fixed ready configuration differs')
    exact={'chain_id':4663,'rpc_urls':['http://127.0.0.1:19592'],
        'cast_binary':str(LAB/'tools/cast'),'keystore':str(N.LIVE/'secrets/keeper'),
        'password_file':str(N.LIVE/'secrets/password'),'state_path':str(N.LIVE/'state.json'),
        'health_path':str(N.LIVE/'health.json'),'lock_path':str(N.LIVE/'keeper.lock'),
        'interval_seconds':240,'confirmations':12,'max_gas_limit':24000000,
        'max_gas_price_wei':'5000000000','max_transaction_cost_wei':'10000000000000000',
        'max_daily_cost_wei':'50000000000000000','l1_fee_allowance_wei':'0','receipt_fee_policy':'included',
        'maintenance':{'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600},
        'bucket_overrides':{},'adaptive_range':{'enabled':False},'royalty_conversion':{'enabled':False},
        'lp_conversion':{'enabled':False},'metadata_refresh':{'enabled':False},
        'principal_distribution':{'enabled':False},'buybacks':[]}
    need(all(config.get(key)==value for key,value in exact.items()),'Fixed keeper guards/jobs differ')
    return value

def start_model(pins):
    N._ownership()
    expected={'source_manifest_sha256','base_sha256','jobs_sha256','cases_sha256','model_sha256'}
    need(type(pins)is dict and set(pins)==expected and all(type(v)is str and re.fullmatch('[0-9a-f]{64}',v)for v in pins.values()),'Model source pin set differs')
    for path,key in ((LAB/'inputs/SOURCE_MANIFEST.json','source_manifest_sha256'),
            (N.HELPERS/'keeper_runtime.py','base_sha256'),(N.HELPERS/'keeper_jobs.py','jobs_sha256'),
            (N.HELPERS/'job_cases.py','cases_sha256'),(N.HELPERS/'model_service.py','model_sha256')):
        N._read(path,2*1024*1024,expected=pins[key])
    for name,pin in (('cast',N.CAST_SHA),('anvil',N.ANVIL_SHA)):N._read(LAB/'tools'/name,128*1024*1024,expected=pin)
    need(all(N._properties(unit).get('LoadState')=='not-found'for unit in N.UNITS),'All new native unit names must be unused')
    for path in (LAB/'runtime',N.RUN,N.RUN/'native-tmp'):N._runtime_directory(path)
    need(not os.path.lexists(N.MODEL),'New model output already exists')
    policy=N._common_policy('model');policy.update(Restart='no',TimeoutStopSec='120s')
    env={'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(N.HELPERS),
        'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONNOUSERSITE':'1',
        'POPL_LAB_HOST_NETWORK_NAMESPACE':os.readlink('/proc/self/ns/net'),'TMPDIR':str(N.RUN/'native-tmp')}
    argv=['/usr/bin/python3','-B',str(N.HELPERS/'model_service.py')]
    for key in ('source_manifest_sha256','base_sha256','jobs_sha256','cases_sha256'):argv+=['--'+key.replace('_','-'),pins[key]]
    return N._start(MODEL_UNIT,argv,policy,env)

def _keeper_start(reuse):
    evidence=ready();model=N._properties(MODEL_UNIT)
    need(model.get('ActiveState')=='active'and int(model.get('MainPID','0'))>1,'Private model is not active')
    proc=N._proc(int(model['MainPID']))
    need(proc is not None and proc['uid']==N.UID and proc['network_namespace']==evidence['namespace']
        and proc['network_namespace']!=os.readlink('/proc/self/ns/net'),'Model namespace differs')
    argv,policy,env=N._keeper_launch_parts(reuse_logs=reuse)
    need(evidence.get('monitor_argv')==argv and evidence.get('monitor_working_directory')==str(N.SOURCE),'Stock daemon ExecStart differs')
    if N._properties(KEEPER_UNIT).get('LoadState')!='not-found':
        N._inactive_empty(KEEPER_UNIT)
        r=N._run(['/usr/bin/systemctl','reset-failed',KEEPER_UNIT]);need(r['returncode']==0,'Owned reset failed')
    if N._properties(KEEPER_UNIT).get('LoadState')=='not-found':result=N._start(KEEPER_UNIT,argv,policy,env)
    else:
        r=N._run(['/usr/bin/systemctl','start','--no-block',KEEPER_UNIT]);need(r['returncode']==0,'Owned start failed')
        result={'unit':KEEPER_UNIT,'properties':N._properties(KEEPER_UNIT),'same_loaded_unit':True}
    N._keeper_policy_checks(result['properties']);return result

def start_keeper():return _keeper_start(False)
def _failure_log():
    path=N.RUN/'native-keeper.stdout.log'
    if not path.exists():return [],[],[]
    raw=N._read(path,N.MAX_OUTPUT,owners=(0,N.UID));events=[json.loads(line)for line in raw.splitlines()]
    errors=[row for row in events if row.get('event')=='cycle_failed'and row.get('os_errno')=='EACCES']
    halts=[row for row in events if row.get('event')=='keeper_halted'and row.get('os_errno')=='EACCES']
    return events,errors,halts

def status():
    snapshot=N.native_status();keeper=snapshot['units'][KEEPER_UNIT]
    # The append-only stock log is read only after its whole cgroup is empty.
    # A live partial line/change must not turn status polling into a lab fault.
    empty=(keeper['properties'].get('MainPID','0')=='0'and not keeper['cgroup']['pids'])
    events,errors,halts=_failure_log()if empty else([],[],[])
    exits=[row for row in keeper['manager_journal']if row.get('MESSAGE_ID')=='98e322203f7a4ed290d09fe03c09fe15'
        and row.get('EXIT_CODE')=='exited'and str(row.get('EXIT_STATUS'))=='1']
    complete=bool(errors and halts and events.index(errors[0])<events.index(halts[0])and exits
        and keeper['properties'].get('MainPID','0')=='0'and not keeper['cgroup']['pids'])
    snapshot['original_failure_complete']=complete
    snapshot['original_main_exit_records']=exits
    lock=N.LIVE/'keeper.lock'
    if lock.exists():
        item=lock.lstat();need(stat.S_ISREG(item.st_mode)and item.st_uid==N.UID and item.st_nlink==1,'Existing private lock differs')
        snapshot['lock_identity']=[item.st_dev,item.st_ino]
    return snapshot
def stopkeeper():return N.native_request_stop(KEEPER_UNIT)

def _fault():
    raw=N._read(N.HELD,2*1024*1024,owners=(0,N.UID));value=json.loads(raw)
    need(type(value.get('accepted_hash'))is str and re.fullmatch('0x[0-9a-f]{64}',value['accepted_hash'])
        and int(value['accepted_hash'],16)!=0,'Known actual accepted hash differs')
    journal=N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID));state=json.loads(journal)
    need(value.get('journal_sha256')==N.digest(journal) and state.get('pending')==value.get('intent')
        and type(state.get('pending'))is dict and state['pending'].get('hash')is None
        and state.get('next_nonce')==0,'Original exact hashless journal differs')
    return value,journal,state

def prove_fault():
    N._ownership();N._inactive_empty(KEEPER_UNIT);ready();fault,journal,state=_fault()
    st=N.LIVE.lstat();need(stat.S_ISDIR(st.st_mode)and st.st_uid==N.UID and stat.S_IMODE(st.st_mode)==0o500,'Exact injected directory mode differs')
    lock=(N.LIVE/'keeper.lock').lstat();need(stat.S_ISREG(lock.st_mode)and lock.st_uid==N.UID and lock.st_nlink==1,'Existing private lock differs')
    snapshot=status();need(snapshot['original_failure_complete'],'Original natural exit1 with completed EACCES log is absent')
    events,errors,halts=_failure_log()
    need(errors and halts and events.index(errors[0])<events.index(halts[0]),'Original cycle error did not precede storage halt')
    need(any(row.get('event')=='submission_requires_reconciliation'and row.get('reported_transaction')==fault['accepted_hash']for row in events),'Strict actual reported hash diagnostic absent')
    return {'schema':1,'success':True,'accepted_hash':fault['accepted_hash'],'journal_sha256':N.digest(journal),
        'keeper_fenced_empty':True,'lock_identity':[lock.st_dev,lock.st_ino],
        'exact_directory_mode_before':'0500','cycle_errors':errors,'halts':halts,
        'stock_log_events':events,'stock_log_sha256':N.digest(N._read(N.RUN/'native-keeper.stdout.log',N.MAX_OUTPUT,owners=(0,N.UID))),
        'native_snapshot':snapshot}

def repair_restart(proof):
    need(type(proof)is dict and proof.get('success')is True,'Captured exact failure proof required')
    current=prove_fault();need(current['journal_sha256']==proof['journal_sha256']and current['lock_identity']==proof['lock_identity'],'Captured storage proof changed')
    os.chmod(N.LIVE,0o700,follow_symlinks=False)
    need(stat.S_IMODE(N.LIVE.lstat().st_mode)==0o700,'Owned directory repair failed')
    fault,journal,state=_fault();result=_keeper_start(True)
    return {'schema':1,'accepted_hash':fault['accepted_hash'],'repair':'ONLY_actor_directory_0500_to_0700',
        'journal_unchanged_before_restart':True,'journal_sha256':N.digest(journal),'lock_identity':proof['lock_identity'],'result':result}

def resolve():
    N._ownership();N._inactive_empty(KEEPER_UNIT);ready();held,journal,state=_fault()
    blocked=json.loads(N._read(N.BLOCKED,2*1024*1024,owners=(0,N.UID)))
    need(blocked.get('accepted_hash')==held['accepted_hash']and blocked.get('no_resend')is True
        and blocked.get('journal_sha256')==N.digest(journal),'Actual restarted daemon hashless-block proof differs')
    need(stat.S_IMODE(N.LIVE.lstat().st_mode)==0o700,'Directory repair did not persist')
    policy=N._common_policy('resolve');policy.update(Restart='no',TimeoutStopSec='120s',JoinsNamespaceOf=MODEL_UNIT,Requires=MODEL_UNIT,After=MODEL_UNIT)
    env={'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(N.SOURCE),
        'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONNOUSERSITE':'1','TMPDIR':str(N.MODEL/'tmp'),'HOME':str(N.LIVE/'secrets')}
    argv=['/usr/bin/python3','-m','keeper.monitor','--config',str(N.CONFIG),'--resolve-pending',held['accepted_hash']]
    result=N._start(RESOLVE_UNIT,argv,policy,env,wait=True);N._inactive_empty(RESOLVE_UNIT)
    afterraw=N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID));after=json.loads(afterraw)
    expected=copy.deepcopy(state);expected['pending']['hash']=held['accepted_hash']
    need(after==expected,'No-live resolution changed more than original actual pending hash')
    return {'schema':1,'accepted_hash':held['accepted_hash'],'state_sha256':N.digest(afterraw),
        'signing_enabled':False,'manager_wait_completion':True,'original_hashless_journal_sha256':N.digest(journal),
        'hash_only_change':True,'result':result}

def resume(resolution):
    N._inactive_empty(KEEPER_UNIT);N._inactive_empty(RESOLVE_UNIT);ready()
    need(type(resolution)is dict and resolution.get('manager_wait_completion')is True and resolution.get('hash_only_change')is True,'Exact no-live resolver proof required')
    raw=N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID));state=json.loads(raw)
    need(N.digest(raw)==resolution['state_sha256']and state['pending']['hash']==resolution['accepted_hash']and state['next_nonce']==0,'Original resolved journal changed before recovery')
    receipt=json.loads(N._read(N.MODEL/'supervisor/RESOLUTION_READY.json',2*1024*1024,owners=(0,N.UID)))
    need(receipt.get('accepted_hash')==resolution['accepted_hash'],'Original confirmation-ready identity differs')
    return {'schema':1,'phase':'same_journal_normal_recovery_started','state_sha256':N.digest(raw),'result':_keeper_start(True)}

def stop_owned():return N.native_stop_owned()
