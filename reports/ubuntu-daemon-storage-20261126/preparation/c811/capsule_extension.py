"""Prepared closed c811 actions, appended to authenticated fixed installer."""
import importlib.util
import selectors
import signal
import sys
from types import SimpleNamespace
sys.dont_write_bytecode=True
CONTROL=LAB/'control'
NATIVE_PINS=__NATIVE_PINS__
BASE_SHA=__BASE_SHA__
CONTROL_SHA=__CONTROL_SHA__

def run(argv,timeout=12):
    require(type(argv)is list and argv and 0<timeout<=20,'Invalid fixed controller work bound')
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        start_new_session=True,close_fds=True,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'})
    outputs=[bytearray(),bytearray()];size=0;finished=False;deadline=time.monotonic()+timeout
    try:
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                require(time.monotonic()<deadline,'Fixed controller command deadline exceeded')
                for key,_ in selector.select(min(.2,max(.001,deadline-time.monotonic()))):
                    chunk=os.read(key.fd,min(16384,256*1024+1-size))
                    if not chunk:selector.unregister(key.fileobj);continue
                    size+=len(chunk);require(size<=256*1024,'Fixed controller command output bound exceeded');outputs[key.data].extend(chunk)
        require(time.monotonic()<deadline,'Fixed controller completion deadline exceeded')
        code=child.wait(timeout=max(.001,deadline-time.monotonic()));finished=True
        return SimpleNamespace(returncode=code,stdout=bytes(outputs[0]),stderr=bytes(outputs[1]))
    finally:
        if not finished:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait(timeout=2)
        child.stdout.close();child.stderr.close()

def native():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    for name,pin in (('native_base.py',BASE_SHA),('storage_control.py',CONTROL_SHA)):
        path=LAB/'source/helpers'/name;checked_read(path,2*1024*1024,expected=pin)
        module_name='native_base'if name=='native_base.py'else'fixed_c811_storage'
        spec=importlib.util.spec_from_file_location(module_name,path);module=importlib.util.module_from_spec(spec)
        sys.modules[module_name]=module;spec.loader.exec_module(module)
    return module

def invoke(method,*args):
    n=native()
    try:return getattr(n,method)(*args)
    except n.N.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def record_control(name,value):
    require(name in {'FAULT_PROOF.json','REPAIR.json','RESOLUTION_RECEIPT.json','RESOLUTION_COMPLETE.json','RESUME.json','FINAL_STOP.json'},'Closed restart record name')
    if not CONTROL.exists():
        CONTROL.mkdir(mode=0o755);os.chmod(CONTROL,0o755,follow_symlinks=False)
    st=CONTROL.lstat();require(stat.S_ISDIR(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o755,'Restart control directory differs')
    raw=json.dumps(value,sort_keys=True,allow_nan=False).encode()+b'\n';require(len(raw)<=2*1024*1024,'Restart record exceeds bound')
    target=CONTROL/name;require(not os.path.lexists(target),'Restart control record already exists')
    mode=0o644 if name=='RESOLUTION_COMPLETE.json'else 0o600
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    os.fchmod(fd,mode)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return sha(raw)

def verify_installed():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    manifest=json.loads(checked_read(LAB/'MANIFEST.json',2*1024*1024,expected=MANIFEST_SHA))
    for name,pin in manifest['members'].items():
        require(len(checked_read(LAB/name,member_maximum(name),expected=pin['sha256']))==pin['bytes'],'Installed member size differs')

def start(a):
    verify_installed();return {'phase':'model_started','native':invoke('start_model',NATIVE_PINS)}

def startkeeper(a):return {'phase':'stock_keeper_started','native':invoke('start_keeper')}

def stopkeeper(a):return {'phase':'keeper_fence_requested','native':invoke('stopkeeper')}

def public_files():
    result={}
    for name,(kind,relative)in PUBLIC_PATHS.items():
        path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
        if path.exists():
            item=secure_file(path,owner=65534 if kind=='model'else 0,maximum=2*1024*1024)
            result[name]={'bytes':item.st_size,'uid':item.st_uid}
    return result

def status(a):
    value=invoke('status')
    return {'phase':'native_status','native':value,'original_failure_complete':value['original_failure_complete'],'public_files':public_files()}

def prove(a):
    proof=invoke('prove_fault');digest=record_control('FAULT_PROOF.json',proof)
    return {'phase':'actual_hash_save_EACCES_proved','sha256':digest,'accepted_hash':proof['accepted_hash'],
        'journal_sha256':proof['journal_sha256'],'keeper_fenced_empty':True}

def repair(a):
    original=json.loads(checked_read(CONTROL/'FAULT_PROOF.json',2*1024*1024))
    require(not(CONTROL/'REPAIR.json').exists(),'Directory repair already recorded')
    result=invoke('repair_restart',original);digest=record_control('REPAIR.json',result)
    return {'phase':'repaired_directory_same_journal_restarted','sha256':digest,'result':result}

def resolve(a):
    require(not(CONTROL/'RESOLUTION_RECEIPT.json').exists()and not(CONTROL/'RESOLUTION_COMPLETE.json').exists(),'Original resolution already recorded')
    result=invoke('resolve');receipt=record_control('RESOLUTION_RECEIPT.json',result)
    marker={key:result[key]for key in ('schema','accepted_hash','state_sha256','signing_enabled','manager_wait_completion')}
    digest=record_control('RESOLUTION_COMPLETE.json',marker)
    return {'phase':'original_actual_hash_adopted_without_signing','receipt_sha256':receipt,'marker_sha256':digest,'result':result}

def resume(a):
    original=json.loads(checked_read(CONTROL/'RESOLUTION_RECEIPT.json',2*1024*1024))
    require(not(CONTROL/'RESUME.json').exists(),'Original normal recovery already requested')
    result=invoke('resume',original);digest=record_control('RESUME.json',result)
    return {'phase':'same_journal_normal_recovery_started','sha256':digest,'result':result}

def stop(a):
    result=invoke('stop_owned')
    if result.get('phase')=='stopped'and not(CONTROL/'FINAL_STOP.json').exists():record_control('FINAL_STOP.json',result)
    return result

def fetch(a):
    ownership();require(a.artifact in PUBLIC_PATHS,'Unapproved public artifact')
    kind,relative=PUBLIC_PATHS[a.artifact]
    path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
    raw=checked_read(path,2*1024*1024,owners=(0,65534)if kind=='model'else(0,))
    return {'phase':'public_artifact','attempt':1,'artifact':a.artifact,'bytes':len(raw),
        'sha256':sha(raw),'base64':base64.b64encode(raw).decode('ascii'),'private_material_exported':False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('install','start','startkeeper','status','stopkeeper','prove','repair','resolve','resume','stop','fetch'))
    parser.add_argument('--controller-sha256',required=True);parser.add_argument('--bundle-sha256')
    parser.add_argument('--attempt',type=int,default=1);parser.add_argument('--artifact');a=parser.parse_args()
    globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256
    try:
        require(a.attempt==1 and re.fullmatch('[0-9a-f]{64}',a.controller_sha256)is not None,'Fixed controller identity differs')
        if a.action=='install':require(re.fullmatch('[0-9a-f]{64}',a.bundle_sha256 or'')is not None,'Invalid bundle pin')
        result=globals()[a.action](a)
    except BaseException as exc:
        site={'function':None,'line':None};trace=exc.__traceback__
        while trace is not None:
            name=trace.tb_frame.f_code.co_name
            if trace.tb_frame.f_code.co_filename==__file__ and name!='require'and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,63}',name)and 0<trace.tb_lineno<10000:
                site={'function':name,'line':trace.tb_lineno}
            trace=trace.tb_next
        kind=type(exc).__name__
        kind=kind if kind in {'ControlRefusal','FileNotFoundError','PermissionError','OSError','ValueError','JSONDecodeError','TimeoutExpired'}else'Other'
        guard=str(exc)if type(exc)is ControlRefusal else None
        if guard is not None and(len(guard)>160 or any(ord(char)<32 or ord(char)>126 for char in guard)):guard=None
        print(json.dumps({'phase':a.action,'failed':True,'reason':'bounded_owned_lab_control_failed',
            'error_type':kind,'fixed_guard':guard,'site':site,'lab':str(LAB),'unit':UNIT}))
        raise SystemExit(1)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
