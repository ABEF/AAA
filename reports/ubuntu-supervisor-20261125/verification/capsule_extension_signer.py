"""Separate c806 actions appended to fixed controller; lazy Linux-only loading."""
import importlib.util
import sys
import time
sys.dont_write_bytecode=True
CONTROL=LAB/'control'
NATIVE_PINS=__NATIVE_PINS__
NATIVE_SHA=__NATIVE_SHA__
CONTROL_NAMES={'BASELINE.json','WITNESS_STATE.json','NATIVE_RESTART_PROOF.json','JOURNAL_DURING_RESTART.json','SIGNER_KILL.json','STOP_KEEPER.json','RESOLUTION_REQUEST.json','RESOLUTION_COMPLETE.json','NORMAL_RESUME.json'}

def native():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    path=LAB/'source/helpers/native_control.py';checked_read(path,2*1024*1024,expected=NATIVE_SHA)
    spec=importlib.util.spec_from_file_location('fixed_native_c806',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def native_call(n,function,*args,**kwargs):
    try:return function(*args,**kwargs)
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def record_control(name,value):
    require(name in CONTROL_NAMES,'Closed native record name')
    if not CONTROL.exists():CONTROL.mkdir(mode=0o700)
    st=CONTROL.lstat();require(stat.S_ISDIR(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o700,'Native control directory differs')
    raw=json.dumps(value,sort_keys=True,allow_nan=False).encode()+b'\n';require(len(raw)<=2*1024*1024,'Native record exceeds bound')
    target=CONTROL/name;temporary=CONTROL/(name+'.tmp')
    if target.exists():secure_file(target,maximum=2*1024*1024)
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,target)
    fd=os.open(CONTROL,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def control_json(name):
    require(name in CONTROL_NAMES,'Closed native read record name')
    return json.loads(checked_read(CONTROL/name,2*1024*1024))

def verify_installed():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    raw=checked_read(LAB/'MANIFEST.json',2*1024*1024,expected=MANIFEST_SHA);manifest=json.loads(raw)
    for name,pin in manifest['members'].items():require(len(checked_read(LAB/name,member_maximum(name),expected=pin['sha256']))==pin['bytes'],'Installed member size differs')

def start(a):
    verify_installed();n=native()
    try:return {'phase':'model_started','native':n.native_start_model(NATIVE_PINS)}
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def startkeeper(a):
    n=native();require(not(CONTROL/'SIGNER_KILL.json').exists(),'Initial native keeper already interrupted')
    try:return {'phase':'keeper_started','native':n.native_start_keeper(),'next_action':'killmain promptly; it waits up to20s for the held actual Cast reply'}
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def public_files():
    result={}
    for name,(kind,relative)in PUBLIC_PATHS.items():
        path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
        if path.exists():
            st=secure_file(path,owner=65534 if kind=='model'else 0,maximum=2*1024*1024)
            result[name]={'bytes':st.st_size,'uid':st.st_uid}
    return result

def status(a):return {'phase':'native_status','native':native().native_status(),'public_files':public_files()}

def lock_identity(n,probe=False):
    import fcntl
    path=n.LIVE/'keeper.lock';fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        st=os.fstat(fd);require(stat.S_ISREG(st.st_mode)and st.st_uid==65534,'Native lock identity differs')
        if probe:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(fd,fcntl.LOCK_UN)
        return {'dev':st.st_dev,'ino':st.st_ino,'uid':st.st_uid,'exclusive_probe_when_empty':probe}
    finally:os.close(fd)

def killmain(a):
    """Call immediately after startkeeper; native capture+kill in one SSH action."""
    n=native();require(not(CONTROL/'SIGNER_KILL.json').exists()and not(CONTROL/'BASELINE.json').exists(),'Native main kill already recorded')
    # Waiting here avoids a status/fetch round trip consuming the75s Cast hold.
    until=time.monotonic()+20
    while not n.HELD.exists()and time.monotonic()<until:time.sleep(.2)
    require(n.HELD.exists(),'Actual accepted Cast reply is not held yet')
    receipt=native_call(n,n.native_kill_keeper_main);w=native_call(n,n.RestartWitness,receipt)
    raw=native_call(n,n._read,n.LIVE/'state.json',2*1024*1024,owners=(0,65534))
    require(sha(raw)==receipt['hashless_journal_sha256'],'Hashless journal changed during deliberate main kill')
    data={'snapshot':receipt['before'],'lock':lock_identity(n),'journal_sha256':sha(raw),'journal_raw_utf8':raw.decode('utf8'),'state':json.loads(raw),'known_accepted_hash':receipt['known_accepted_hash']}
    record_control('SIGNER_KILL.json',receipt);record_control('BASELINE.json',data);record_control('WITNESS_STATE.json',w.__dict__)
    return {'phase':'actual_cast_captured_and_main_killed','watchdog_experiment':False,'journal_sha256':sha(raw),'old_main_pid':w.old_main,'actual_cast_pid':receipt['actual_cast_before_main_kill']['pid'],'known_accepted_hash':receipt['known_accepted_hash'],'next_action':'observe immediately until native restart proof exists'}

def observe(a):
    n=native();require((CONTROL/'BASELINE.json').exists(),'Native baseline absent')
    base=control_json('BASELINE.json');stored=control_json('WITNESS_STATE.json');w=native_call(n,n.RestartWitness,control_json('SIGNER_KILL.json'));w.__dict__.update(stored)
    until=time.monotonic()+25;count=0
    while time.monotonic()<until:
        native_call(n,w.capture);count+=1
        if w.empty_before_restart is not None and not(CONTROL/'JOURNAL_DURING_RESTART.json').exists():
            raw=n._read(n.LIVE/'state.json',2*1024*1024,owners=(0,65534));require(sha(raw)==base['journal_sha256'],'Pending journal changed before native restart')
            lock=lock_identity(n,probe=True);require((lock['dev'],lock['ino'])==(base['lock']['dev'],base['lock']['ino']),'Native lock inode changed')
            record_control('JOURNAL_DURING_RESTART.json',{'raw_utf8':raw.decode('utf8'),'sha256':sha(raw),'lock':lock,'old_generation_empty_at':w.empty_before_restart})
        if w.new_invocation is not None:
            proof=native_call(n,w.finish);after=lock_identity(n);require((after['dev'],after['ino'])==(base['lock']['dev'],base['lock']['ino']),'Restarted lock inode changed')
            proof['lock_before']=base['lock'];proof['lock_after']=after;record_control('NATIVE_RESTART_PROOF.json',proof);break
        time.sleep(4)
    record_control('WITNESS_STATE.json',w.__dict__)
    return {'phase':'native_observed','samples_added':count,'samples_total':len(w.samples),'old_empty_seen':w.empty_before_restart is not None,'new_invocation_seen':w.new_invocation is not None,'proof_available':(CONTROL/'NATIVE_RESTART_PROOF.json').exists(),'hashless_restart_block_available':n.BLOCKED.exists(),'watchdog_experiment':False}

def stopkeeper(a):
    n=native();require((CONTROL/'NATIVE_RESTART_PROOF.json').exists()and n.BLOCKED.exists(),'Native restart and stock hashless block evidence required')
    proof=control_json('NATIVE_RESTART_PROOF.json');require(proof.get('watchdog_experiment')is False and proof['new_invocation']['all_old_generations_dead']is True,'Native signal cleanup proof differs')
    result=native_call(n,n.native_request_stop,n.KEEPER_UNIT);record_control('STOP_KEEPER.json',result)
    return {'phase':'intentional_keeper_stop_requested','native':result,'model_preserved_for_explicit_resolution':True}

def resolve(a):
    n=native();require((CONTROL/'NATIVE_RESTART_PROOF.json').exists()and(CONTROL/'STOP_KEEPER.json').exists()and not(CONTROL/'RESOLUTION_REQUEST.json').exists(),'Ordered native stop and unused resolver required')
    result=native_call(n,n.native_resolve_saved_hash);record_control('RESOLUTION_REQUEST.json',result);record_control('RESOLUTION_COMPLETE.json',result)
    return {'phase':'explicit_stock_hash_resolution_completed','native':result,'signing_enabled':False,'model_remains_active':True,'manager_wait_completion':True}

def resume(a):
    n=native();require((CONTROL/'RESOLUTION_COMPLETE.json').exists()and not(CONTROL/'NORMAL_RESUME.json').exists(),'Recorded completed resolution and unused normal resume required')
    result=native_call(n,n.native_resume_keeper,control_json('RESOLUTION_COMPLETE.json'));record_control('NORMAL_RESUME.json',result);return result

def stop(a):
    n=native()
    try:return n.native_stop_owned()
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def fetch(a):
    ownership();require(a.artifact in PUBLIC_PATHS,'Unapproved public artifact')
    kind,relative=PUBLIC_PATHS[a.artifact];path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
    data=checked_read(path,2*1024*1024,owners=(0,65534)if kind=='model'else(0,))
    return {'phase':'public_artifact','attempt':1,'artifact':a.artifact,'bytes':len(data),'sha256':sha(data),'base64':base64.b64encode(data).decode('ascii'),'private_material_exported':False}
