"""NEW bounded composition wrapper: original CLI; separate disclosed race hook."""
from pathlib import Path
from contextlib import contextmanager
import json,os,stat,sys,time
from lab_common import SOURCE,RUNTIME,need,enc,sha,run,read_json,file_pin


def marker(name,value):
    need(name in ('RACE_READY.json','RACE_RESULT.json','HOLD_READY.json','HOLD_RESULT.json'))
    raw=enc(value);need(len(raw)<=32768)
    temporary=RUNTIME/(name+'.partial');target=RUNTIME/name;need(not target.exists(),'marker_exists')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.rename(temporary,target)


def control(name,seconds=60):
    need(name in ('RELEASE_RACE','HOLD','RELEASE_HOLD'))
    until=time.monotonic()+seconds;path=RUNTIME/'control'/(name+'.json')
    while not path.exists():need(time.monotonic()<until,'barrier_deadline');time.sleep(.1)
    st=path.lstat();need(stat.S_ISREG(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o444)
    need(read_json(path)=={'schema':1,'name':name},'barrier_control')


def masks(cfg):
    values=[]
    for key in ('keystore','password_file'):
        path=Path(cfg[key]);st=path.lstat()
        need(stat.S_ISREG(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0
            and st.st_size==0 and st.st_nlink==1,'mask_identity')
        try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        except PermissionError:pass
        else:os.close(fd);raise ValueError('mask_readable')
        values.append([st.st_dev,st.st_ino])
    need(len({tuple(row)for row in values})==2,'mask_alias');return values


def ordinary(action,policy,pin):
    code,out,err=run(['/usr/bin/python3','-B',str(SOURCE/'scripts/keeper-schedule.py'),
        action,'--policy',str(policy),'--policy-sha256',pin],timeout=75)
    need(not err,'cli_stderr');value=json.loads(out)
    need(value['unsigned']is True and value['readiness_approved']is False and code in (0,1),'cli_result')
    return code,value,sha(out)


def barrier(policy,pin,cfg):
    # This timing seam belongs ONLY to this new lab wrapper. The stock daemon,
    # original timer CLI and all source-identity files remain unchanged.
    from keeper import scheduling,recovery_bundle
    from zzz_ops.state import process_lock
    journal=Path(cfg['state_path']);selected=RUNTIME/'schedule/selected.json'
    original_read=recovery_bundle._read;original_guard=scheduling.process_lock
    first=True;before=None;under_lock=None;captured=None;race=None
    def paused(path,*args,**kwargs):
        nonlocal first,captured
        raw=original_read(path,*args,**kwargs)
        if Path(path)==journal and first:
            first=False;captured=sha(raw)
            marker('RACE_READY.json',{'schema':1,'captured_journal_sha256':captured,
                'selection_before':before,'monotonic':time.monotonic(),'instrumented_read_barrier':True})
            control('RELEASE_RACE',60)
        return raw
    @contextmanager
    def checked_guard(path):
        nonlocal before,under_lock
        with original_guard(path):
            before=file_pin(selected)
            try:yield
            finally:under_lock=file_pin(selected)
    recovery_bundle._read=paused;scheduling.process_lock=checked_guard
    try:
        try:scheduling.run_once('backup',policy,pin)
        except scheduling.ScheduleRefusal as exc:race={'refusal_code':exc.code,'cause_code':exc.cause_code}
        need(race=={'refusal_code':'backup_capture','cause_code':'source_snapshot_changed'},'race_not_refused')
        need(first is False and captured!=file_pin(journal)['sha256']and under_lock==before,'race_not_witnessed')
    finally:recovery_bundle._read=original_read;scheduling.process_lock=original_guard
    marker('RACE_RESULT.json',{'schema':1,'success':True,**race,'captured_journal_sha256':captured,
        'actual_journal_sha256':file_pin(journal)['sha256'],'selection_before':before,
        'selection_after_under_lock':under_lock,'production_sources_changed':False,
        'instrumented_read_barrier':True,'monotonic':time.monotonic()})
    control('HOLD',60)
    with process_lock(RUNTIME/'schedule/schedule.lock'):
        snapshot={name:file_pin(path)for name,path in {
            'selection':selected,'observer':RUNTIME/'alerts/state.json'}.items()}
        pending=read_json(RUNTIME/'alerts/state.json')
        need(pending['pending']is not None and bool(pending['outbox']),'missing_pending_history')
        marker('HOLD_READY.json',{'schema':1,'monotonic':time.monotonic(),'files':snapshot,
            'pending':pending['pending'],'sequence':pending['sequence'],
            'queued_ids':[event['event_id']for event in pending['outbox']]})
        control('RELEASE_HOLD',60)
        after={name:file_pin(path)for name,path in {
            'selection':selected,'observer':RUNTIME/'alerts/state.json'}.items()}
        need(after==snapshot,'contention_mutated_state')
        marker('HOLD_RESULT.json',{'schema':1,'success':True,'files_before':snapshot,
            'files_after':after,'pending':pending['pending'],'queued_ids':[e['event_id']for e in pending['outbox']],
            'monotonic':time.monotonic()})
    return 0,{'schema':1,'ok':True,'unsigned':True,'readiness_approved':False,
        'instrumented_race_and_explicit_lock_holder':True},None


def main():
    need(os.getuid()==os.getgid()==65534 and set(os.getgroups())<={65534},'wrong_uid')
    need(len(sys.argv)==2 and sys.argv[1]in('init','backup','observe','barrier'),'unknown_action')
    action=sys.argv[1];policy=RUNTIME/'policy.json';pin=sha(policy.read_bytes())
    cfg=read_json(Path(read_json(policy)['configuration']));began=time.monotonic()
    result={'schema':1,'action':action,'started_monotonic':began,'mask_inode_pairs':masks(cfg)}
    code=1
    try:
        code,value,raw_sha=barrier(policy,pin,cfg)if action=='barrier'else ordinary(action,policy,pin)
        result.update(returncode=code,value=value,cli_output_sha256=raw_sha)
    except BaseException as exc:result.update(error_type=type(exc).__name__,error_sha256=sha(str(exc).encode()))
    result['ended_monotonic']=time.monotonic()
    raw=enc(result);need(len(raw)<=32768,'record_bound')
    path=RUNTIME/'records'/(action+'-'+str(time.monotonic_ns())+'.json')
    temporary=path.with_suffix('.partial')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.rename(temporary,path)
    need(len(list((RUNTIME/'records').iterdir()))<=128,'record_count')
    print(json.dumps({'action':action,'returncode':code,'record_sha256':sha(raw)},sort_keys=True))
    return code


if __name__=='__main__':raise SystemExit(main())
