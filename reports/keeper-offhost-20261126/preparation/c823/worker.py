"""NEW unsigned off-host-package restore witness; original protected layout only."""
from pathlib import Path
import hashlib,json,os,re,selectors,signal,stat,subprocess,time,traceback

LAB=Path('/opt/popl-keeper-offhost-20261126-c823');RUNTIME=LAB/'runtime'
ORIGINAL=Path('/opt/popl-keeper-sidecar-recovery-20261126-c821')
SOURCE=ORIGINAL/'source';POLICY=ORIGINAL/'runtime/policy.json';CONFIG=ORIGINAL/'runtime/keeper-config.json'
OUTER='a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED='911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
POLICY_PIN='7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
CONFIG_PIN='1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
END=time.monotonic()+165
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def need(value,code='offhost_assertion'):
    if not value:raise ValueError(code)


def read(path):
    before=path.lstat();need(stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_size<=65536,'file_bound')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        parts=[];size=0
        while True:
            part=os.read(fd,min(16384,65537-size))
            if not part:break
            size+=len(part);need(size<=65536,'file_bound');parts.append(part)
        raw=b''.join(parts);after=os.fstat(fd);named=path.lstat()
        key=lambda item:(item.st_dev,item.st_ino,item.st_size,item.st_mtime_ns)
        need(len(raw)<=65536 and len(raw)==before.st_size and key(before)==key(after)==key(named),'file_changed')
        return raw
    finally:os.close(fd)


def value(path):return json.loads(read(path))


def original_locks():
    result=[]
    for path in(ORIGINAL/'runtime/schedule/schedule.lock',ORIGINAL/'runtime/alerts/alert.lock'):
        item=path.lstat();need(stat.S_ISREG(item.st_mode)and item.st_nlink==1
            and item.st_uid==65534 and stat.S_IMODE(item.st_mode)==0o600,'original_lock_metadata')
        result.append([item.st_dev,item.st_ino,item.st_mode,item.st_uid,item.st_nlink,item.st_size,item.st_mtime_ns])
    need(len({tuple(row[:2])for row in result})==2,'original_lock_alias');return result


def publish(name,data):
    need(name in('PROGRESS.json','RESULT.json'));raw=enc(data);need(len(raw)<=32768,'result_bound')
    path=RUNTIME/name;temp=path.with_suffix('.partial')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temp,path)


def run(script,args):
    need(script in('keeper-recovery.py','keeper-sidecar-recovery.py'),'command_scope')
    argv=['/usr/bin/python3','-B',str(SOURCE/'scripts'/script),*args]
    started=time.monotonic();deadline=min(END,started+75);child=owned=None;parts=[bytearray(),bytearray()];size=0
    try:
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            start_new_session=True,close_fds=True);owned=child
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<deadline,'command_deadline')
                for key,_ in selector.select(min(.1,max(.001,deadline-time.monotonic()))):
                    raw=os.read(key.fd,min(16384,65537-size))
                    if not raw:selector.unregister(key.fileobj);continue
                    size+=len(raw);need(size<=65536,'command_capture_bound');parts[key.data].extend(raw)
        code=child.wait(timeout=max(.001,deadline-time.monotonic()));owned=None
        out,err=map(bytes,parts);need(code==0 and not err,'original_cli_refused')
        if script=='keeper-sidecar-recovery.py':
            parsed=json.loads(out);need(parsed['ok']is True and parsed['unsigned']is True and parsed['readiness_approved']is False,'sidecar_cli_result')
        else:
            match=re.search(r'^(?:Manifest|Restore plan) SHA-256: ([0-9a-f]{64})$',out.decode('utf8','strict'),re.M)
            need(match is not None,'native_cli_result');parsed={'manifest_or_plan_sha256':match[1]}
        return{'script':script,'action':args[0],'argv':argv,'returncode':code,
            'elapsed_seconds':time.monotonic()-started,'stdout_sha256':sha(out),'stdout_bytes':len(out),'parsed':parsed}
    finally:
        try:
            if owned is not None:
                if owned.poll()is None:
                    try:os.killpg(owned.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                owned.wait(timeout=2)
        finally:
            if child is not None:child.stdout.close();child.stderr.close()


def main():
    need(os.getuid()==os.getgid()==65534 and set(os.getgroups())<={65534},'wrong_uid')
    result={'schema':1,'success':False,'unsigned':True,'readiness_approved':False,
        'production_approved':False,'public_transactions':0,'RPC_calls':0,'test_bodies_run':0,
        'source_services_started':False,'old_policy_changed':False,'new_review_max_age_seconds':86400,
        'operating_policy_max_backup_age_seconds':900,'restores_are_review_only':True}
    calls=[];began=time.monotonic()
    try:
        need(sha(read(POLICY))==POLICY_PIN and sha(read(CONFIG))==CONFIG_PIN,'separate_reference_pin')
        policy=value(POLICY);config=value(CONFIG)
        need(policy['max_backup_age_seconds']==900 and policy['max_bytes']==16777216 and policy['max_seconds']==60,'original_policy')
        mask_ids=[]
        for key in('keystore','password_file'):
            path=Path(config[key]);item=path.lstat()
            need(stat.S_ISREG(item.st_mode)and item.st_uid==0 and stat.S_IMODE(item.st_mode)==0
                and item.st_size==0 and item.st_nlink==1,'mask_metadata')
            try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
            except PermissionError:pass
            else:os.close(fd);raise ValueError('mask_readable')
            mask_ids.append([item.st_dev,item.st_ino])
        need(len({tuple(row)for row in mask_ids})==2,'mask_alias')
        package=RUNTIME/'imported';outer=value(package/'manifest.json');nested=value(package/'selected/manifest.json')
        need(sha(read(package/'manifest.json'))==OUTER and sha(read(package/'selected/manifest.json'))==NESTED,'transport_pins')
        current=int(time.time());ages={'outer':current-outer['created_at'],'nested':current-nested['created_at']}
        need(all(0<=age<=86400 for age in ages.values()),'review_capture_age')
        result.update(capture_ages_seconds=ages,original_capture_times={'outer':outer['created_at'],'nested':nested['created_at']},
            operational_freshness_approved=False,outside_original_operating_age=all(age>900 for age in ages.values()),
            asof_clock_override=False,signer_masks_distinct_unreadable=mask_ids)
        old_locks=original_locks()
        native=['--config',str(CONFIG),'--bundle',str(package/'selected'),'--manifest-sha256',NESTED,
            '--max-age-seconds','86400','--minimum-created-at',str(nested['created_at'])]
        side=['--policy',str(POLICY),'--policy-sha256',POLICY_PIN,'--bundle',str(package),
            '--manifest-sha256',OUTER,'--max-age-seconds','86400','--minimum-created-at',str(outer['created_at'])]
        tasks=[('keeper-recovery.py',['verify',*native]),
            ('keeper-recovery.py',['restore',*native,'--output',str(RUNTIME/'keeper-review')]),
            ('keeper-sidecar-recovery.py',['verify',*side]),
            ('keeper-sidecar-recovery.py',['restore',*side,'--output',str(RUNTIME/'sidecar-review')])]
        for script,args in tasks:
            publish('PROGRESS.json',{'schema':1,'completed':calls,'next':script+':'+args[0]})
            calls.append(run(script,args))
        keeper=RUNTIME/'keeper-review';sidecar=RUNTIME/'sidecar-review'
        selected=value(package/'selection.json');generation=selected['generation']
        comparisons={
            'keeper-state.json':(package/'selected/journal.json',keeper/'keeper-state.json'),
            'scheduler/selected.json':(package/'selection.json',sidecar/'scheduler/selected.json'),
            'alerts/state.json':(package/'alert-state.json',sidecar/'alerts/state.json'),
            'selected/manifest.json':(package/'selected/manifest.json',sidecar/'backups'/generation/'manifest.json'),
            'selected/journal.json':(package/'selected/journal.json',sidecar/'backups'/generation/'journal.json')}
        compared={}
        for name,(source,target)in comparisons.items():
            raw=read(source);need(raw==read(target),'restored_raw_bytes_differ');compared[name]={'bytes':len(raw),'sha256':sha(raw)}
        native_plan=value(keeper/'RESTORE_PLAN.json');side_plan=value(sidecar/'RESTORE_PLAN.json')
        native_plan_pin=sha(read(keeper/'RESTORE_PLAN.json'));side_plan_pin=sha(read(sidecar/'RESTORE_PLAN.json'))
        need(calls[0]['parsed']['manifest_or_plan_sha256']==NESTED
            and calls[1]['parsed']['manifest_or_plan_sha256']==native_plan_pin
            and calls[2]['parsed']['manifest_sha256']==OUTER
            and calls[3]['parsed']['manifest_sha256']==OUTER
            and calls[3]['parsed']['restore_plan_sha256']==side_plan_pin,'CLI_output_binding')
        need(native_plan['unsigned']is True and all(native_plan[key]is False for key in
            ('live_ready','canonical_state_verified','old_keeper_fenced','signer_material_included','configuration_installed','service_restarted')),'native_adoption_flag')
        need(side_plan['unsigned']is True and all(side_plan[key]is False for key in
            ('readiness_approved','old_sidecars_fenced','canonical_state_verified','signer_material_included',
             'policy_or_configuration_installed','services_restarted','runtime_paths_mapped','lock_ownership_restored','selected_generation_freshness_approved')),'sidecar_adoption_flag')
        locks=[]
        for path in(sidecar/'scheduler/schedule.lock',sidecar/'alerts/alert.lock'):
            item=path.lstat();need(stat.S_ISREG(item.st_mode)and item.st_uid==65534
                and stat.S_IMODE(item.st_mode)==0o600 and item.st_nlink==1 and item.st_size==0,'new_lock_metadata')
            need(read(path)==b'','new_lock_not_empty')
            locks.append([item.st_dev,item.st_ino])
        need(len({tuple(row)for row in locks})==2,'new_lock_alias')
        need(original_locks()==old_locks and {tuple(row)for row in locks}.isdisjoint(
            {tuple(row[:2])for row in old_locks}),'original_lock_reused_or_changed')
        observer=value(sidecar/'alerts/state.json');state=value(keeper/'keeper-state.json')
        need(observer==value(package/'alert-state.json')and state==value(package/'selected/journal.json'),'accounting_state_changed')
        need(sha(read(POLICY))==POLICY_PIN and sha(read(CONFIG))==CONFIG_PIN,'separate_reference_changed')
        result.update(success=True,calls=calls,restored_files=compared,
            native_restore_plan_sha256=native_plan_pin,sidecar_restore_plan_sha256=side_plan_pin,
            all_adoption_flags_false=True,new_empty_lock_inode_pairs=locks,
            original_lock_metadata_unchanged=old_locks,new_locks_disjoint_from_originals=True,
            pending_summary=side_plan['observer_summary']['pending'],outbox_ids=[e['event_id']for e in observer['outbox']],
            sequence=observer['sequence'],raw_records_rewritten=False,original_timestamps_preserved=True)
    except BaseException as exc:
        result.update(error_type=type(exc).__name__,error_sha256=sha(str(exc).encode()),calls=calls,
            frames=[{'file':Path(frame.filename).name,'line':frame.lineno,'function':frame.name}
                for frame in traceback.extract_tb(exc.__traceback__)[-8:]])
    result['elapsed_seconds']=time.monotonic()-began;publish('RESULT.json',result)
    print(json.dumps({'success':result['success'],'completed_original_CLI_calls':len(calls)}))
    return 0 if result['success']else 1


if __name__=='__main__':raise SystemExit(main())
