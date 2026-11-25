"""Appended to the fixed reviewed installer/controller; never standalone."""
import importlib.util
import sys
import time
sys.dont_write_bytecode=True
CONTROL=LAB/'control'
NATIVE_PINS=__NATIVE_PINS__
NATIVE_SHA=__NATIVE_SHA__

def native():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    path=LAB/'source/helpers/native_control.py';checked_read(path,2*1024*1024,expected=NATIVE_SHA)
    spec=importlib.util.spec_from_file_location('fixed_native',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def record_control(name,value):
    require(name in {'BASELINE.json','WITNESS_STATE.json','NATIVE_RESTART_PROOF.json','JOURNAL_DURING_RESTART.json','SIGNER_KILL.json'},'Closed native record name')
    if not CONTROL.exists():CONTROL.mkdir(mode=0o700)
    st=CONTROL.lstat();require(stat.S_ISDIR(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o700,'Native control directory differs')
    raw=json.dumps(value,sort_keys=True,allow_nan=False).encode()+b'\n';require(len(raw)<=2*1024*1024,'Native record exceeds bound')
    target=CONTROL/name;temporary=CONTROL/(name+'.tmp')
    if target.exists():secure_file(target,maximum=2*1024*1024)
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,target)

def control_json(name):return json.loads(checked_read(CONTROL/name,2*1024*1024))

def verify_installed():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    raw=checked_read(LAB/'MANIFEST.json',2*1024*1024,expected=MANIFEST_SHA);manifest=json.loads(raw)
    for name,pin in manifest['members'].items():require(len(checked_read(LAB/name,member_maximum(name),expected=pin['sha256']))==pin['bytes'],'Installed member size differs')

def start(a):
    verify_installed();n=native()
    try:return {'phase':'model_started','native':n.native_start_model(NATIVE_PINS)}
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def startkeeper(a):
    n=native()
    try:return {'phase':'keeper_started','native':n.native_start_keeper()}
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

def baseline(a):
    n=native();require(not(CONTROL/'BASELINE.json').exists(),'Native baseline already exists')
    snapshot=n.native_status(include_journal=False);w=n.RestartWitness(snapshot)
    journal=n._read(n.LIVE/'state.json',2*1024*1024,owners=(0,65534));state=json.loads(journal)
    require(type(state.get('pending'))is dict,'Native baseline needs pending work')
    data={'snapshot':snapshot,'lock':lock_identity(n),'journal_sha256':sha(journal),'journal_raw_utf8':journal.decode('utf8'),'state':state}
    record_control('BASELINE.json',data);record_control('WITNESS_STATE.json',w.__dict__)
    return {'phase':'native_baseline_saved','journal_sha256':sha(journal),'old_main_pid':w.old_main,'old_process_count':len(w.old_processes)}

def observe(a):
    n=native();require((CONTROL/'BASELINE.json').exists(),'Native baseline absent')
    base=control_json('BASELINE.json');stored=control_json('WITNESS_STATE.json');w=n.RestartWitness(base['snapshot']);w.__dict__.update(stored)
    until=time.monotonic()+25;count=0
    while time.monotonic()<until:
        w.capture();count+=1
        if w.empty_before_restart is not None and not(CONTROL/'JOURNAL_DURING_RESTART.json').exists():
            raw=n._read(n.LIVE/'state.json',2*1024*1024,owners=(0,65534));require(sha(raw)==base['journal_sha256'],'Pending journal changed before native restart')
            lock=lock_identity(n,probe=True);require((lock['dev'],lock['ino'])==(base['lock']['dev'],base['lock']['ino']),'Native lock inode changed')
            record_control('JOURNAL_DURING_RESTART.json',{'raw_utf8':raw.decode('utf8'),'sha256':sha(raw),'lock':lock,'old_generation_empty_at':w.empty_before_restart})
        if w.new_invocation is not None:
            proof=w.finish();after=lock_identity(n);require((after['dev'],after['ino'])==(base['lock']['dev'],base['lock']['ino']),'Restarted lock inode changed')
            proof['lock_before']=base['lock'];proof['lock_after']=after;record_control('NATIVE_RESTART_PROOF.json',proof);break
        time.sleep(4)
    record_control('WITNESS_STATE.json',w.__dict__)
    return {'phase':'native_observed','samples_added':count,'samples_total':len(w.samples),'old_empty_seen':w.empty_before_restart is not None,'new_invocation_seen':w.new_invocation is not None,'proof_available':(CONTROL/'NATIVE_RESTART_PROOF.json').exists()}

def stop(a):
    n=native()
    try:return n.native_stop_owned()
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def fetch(a):
    ownership();require(a.artifact in PUBLIC_PATHS,'Unapproved public artifact')
    kind,relative=PUBLIC_PATHS[a.artifact];path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
    data=checked_read(path,2*1024*1024,owners=(0,65534)if kind=='model'else(0,))
    return {'phase':'public_artifact','attempt':1,'artifact':a.artifact,'bytes':len(data),'sha256':sha(data),'base64':base64.b64encode(data).decode('ascii'),'private_material_exported':False}
