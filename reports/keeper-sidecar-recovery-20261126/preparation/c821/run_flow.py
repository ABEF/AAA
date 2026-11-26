"""Actual unsigned CLI capture/verify/restore, then mapped-namespace observation."""
from pathlib import Path
import json,os,stat,sys,time,traceback
from lab_common import LAB,SOURCE,RUNTIME,sha,need,publish,read_json,file_pin,run

def mask_probe():
    rows=[]
    for name in ('keystore.secret','password.secret'):
        path=RUNTIME/'working'/name;st=path.lstat()
        need(stat.S_ISREG(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0
            and st.st_size==0 and st.st_nlink==1,'mask_identity')
        try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        except PermissionError:pass
        else:os.close(fd);raise ValueError('mask_readable')
        rows.append([st.st_dev,st.st_ino])
    need(len(set(map(tuple,rows)))==2,'mask_alias')
    return rows

def paths():
    selected=read_json(RUNTIME/'schedule/selected.json')
    return{'scheduler/selected.json':RUNTIME/'schedule/selected.json',
        'alerts/state.json':RUNTIME/'alerts/state.json',
        'backups/'+selected['generation']+'/manifest.json':RUNTIME/'backups'/selected['generation']/'manifest.json',
        'backups/'+selected['generation']+'/journal.json':RUNTIME/'backups'/selected['generation']/'journal.json'}

def pins(values):return{name:file_pin(path)for name,path in values.items()}

def cli(script,arguments,*,expected=0):
    code,out,err=run(['/usr/bin/python3','-B',str(SOURCE/'scripts'/script),*arguments],timeout=60)
    need(not err,'cli_stderr')
    value=json.loads(out)
    need(value['unsigned']is True and value['readiness_approved']is False,'cli_authority')
    need(code==expected,'cli_exit')
    return value

def source():
    policy=RUNTIME/'policy.json';policy_pin=sha(policy.read_bytes())
    initialized=cli('keeper-schedule.py',['init','--policy',str(policy),'--policy-sha256',policy_pin],expected=1)
    need(initialized['scheduler_initialized']is True,'source_init')
    observer=read_json(RUNTIME/'alerts/state.json')
    need(observer['pending']is not None and bool(observer['outbox']),'missing_recovery_history')
    before=pins(paths());policy_before=file_pin(policy);config_before=file_pin(RUNTIME/'keeper-config.json')
    locks={name:[path.stat().st_dev,path.stat().st_ino]for name,path in{
        'schedule':RUNTIME/'schedule/schedule.lock','alert':RUNTIME/'alerts/alert.lock'}.items()}
    backup=cli('keeper-sidecar-recovery.py',['backup','--policy',str(policy),
        '--policy-sha256',policy_pin,'--output',str(RUNTIME/'sidecar-bundle')])
    pin=backup['manifest_sha256']
    common=['--bundle',str(RUNTIME/'sidecar-bundle'),'--manifest-sha256',pin,
        '--policy',str(policy),'--policy-sha256',policy_pin,'--max-age-seconds','900']
    verified=cli('keeper-sidecar-recovery.py',['verify',*common])
    restored=cli('keeper-sidecar-recovery.py',['restore',*common,'--output',str(RUNTIME/'restored')])
    need(before==pins(paths()),'source_snapshot_mutated')
    need(policy_before==file_pin(policy)and config_before==file_pin(RUNTIME/'keeper-config.json'),'source_inputs_mutated')
    target_files={name:RUNTIME/'restored'/name for name in before}
    need(before==pins(target_files),'restore_bytes_differ')
    target_locks={name:[path.stat().st_dev,path.stat().st_ino]for name,path in{
        'schedule':RUNTIME/'restored/scheduler/schedule.lock','alert':RUNTIME/'restored/alerts/alert.lock'}.items()}
    need(all(target_locks[k]!=locks[k]for k in locks),'portable_lock_falsehood')
    for path in(RUNTIME/'restored/scheduler/schedule.lock',RUNTIME/'restored/alerts/alert.lock'):
        st=path.stat();need(st.st_uid==65534 and stat.S_IMODE(st.st_mode)==0o600 and st.st_size==0,'restore_lock_mode')
    plan=RUNTIME/'restored/RESTORE_PLAN.json'
    need(file_pin(plan)['sha256']==restored['restore_plan_sha256'],'restore_plan_pin')
    plan_value=read_json(plan)
    need(plan_value['unsigned']is True and all(plan_value[key]is False for key in(
        'readiness_approved','old_sidecars_fenced','canonical_state_verified','signer_material_included',
        'policy_or_configuration_installed','services_restarted','runtime_paths_mapped',
        'lock_ownership_restored','selected_generation_freshness_approved')),'restore_approval_invented')
    need(plan_value['restored_directories']=={'scheduler_directory':'scheduler','alert_directory':'alerts',
        'backup_directory':'backups'},'unexpected_restore_mapping')
    return{'source_files':before,'restored_files':pins(target_files),
        'policy_pin':policy_pin,'config_pin':config_before,'selected':read_json(RUNTIME/'schedule/selected.json'),
        'observer_before':observer,'bundle_manifest_pin':pin,'verified':verified,
        'restore_plan_pin':file_pin(plan),'restore_plan':plan_value,'source_locks':locks,'fresh_restore_locks':target_locks,
        'source_state_unchanged':True,'policy_and_configuration_unchanged':True,
        'raw_records_rewritten':False,'restore_does_not_adopt':True}

def target():
    evidence=read_json(RUNTIME/'SOURCE_RESULT.json');need(evidence['success']is True,'missing_source_acceptance')
    before=read_json(RUNTIME/'alerts/state.json')
    need(before==evidence['observer_before'],'mapped_state_not_exact')
    need(pins(paths())==evidence['restored_files'],'mapped_files_not_exact')
    policy=RUNTIME/'policy.json';need(sha(policy.read_bytes())==evidence['policy_pin'],'policy_rewritten')
    observed=cli('keeper-schedule.py',['observe','--policy',str(policy),
        '--policy-sha256',evidence['policy_pin']],expected=1)
    after=read_json(RUNTIME/'alerts/state.json')
    need(after['pending']==before['pending'],'pending_clock_reset')
    need(after['sequence']==before['sequence'],'event_ids_replaced')
    need(after['active']==before['active']and after['outbox']==[],'outbox_not_drained')
    delivery=observed['observation']['delivery']
    need(delivery['acknowledged']==len(before['outbox'])and delivery['state']=='acknowledged','delivery_incomplete')
    return{'observer_before':before,'observer_after':after,
        'same_queued_ids':[e['event_id']for e in before['outbox']],
        'pending_first_seen_preserved':after['pending']['first_seen'],
        'observation':observed,'fresh_target_namespace':True,
        'logical_paths_and_raw_policy_unchanged':True,'delivery_is_at_least_once':True}

def main():
    need(os.getuid()==os.getgid()==65534 and set(os.getgroups())<={65534},'wrong_uid')
    need(len(sys.argv)==2 and sys.argv[1]in('source','target'),'wrong_flow')
    role=sys.argv[1];result={'schema':1,'success':False,'role':role,'unsigned':True,
        'readiness_approved':False,'public_transactions':0,'signer_contents_read':False}
    began=time.monotonic()
    try:result['mask_inode_pairs']=mask_probe();result.update(globals()[role]());result['success']=True
    except BaseException as exc:
        result['error_type']=type(exc).__name__
        text=str(exc)
        result['error_code']=text if isinstance(exc,ValueError)and text.replace('_','').isalnum()else'scoped_failure'
        result['frames']=[{'file':Path(frame.filename).name,'line':frame.lineno,'function':frame.name}
            for frame in traceback.extract_tb(exc.__traceback__)[-8:]]
    result['elapsed_seconds']=time.monotonic()-began
    publish('SOURCE_RESULT.json'if role=='source'else'TARGET_RESULT.json',result)
    print(json.dumps({'role':role,'success':result['success']}))
    return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
