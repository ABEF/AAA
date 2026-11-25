"""Closed bounded command capture and recursive fixed cgroup inspection."""
import selectors
import signal
from types import SimpleNamespace

def run(argv,timeout=12):
    # Only callers above construct fixed reviewed argv; never a shell.
    require(type(argv)is list and argv and 0<timeout<=20,'Invalid fixed controller work bound')
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'})
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
        require(time.monotonic()<deadline,'Fixed controller command completion deadline exceeded')
        code=child.wait(timeout=max(.001,deadline-time.monotonic()));finished=True
        return SimpleNamespace(returncode=code,stdout=bytes(outputs[0]),stderr=bytes(outputs[1]))
    finally:
        if not finished:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:raise ControlRefusal('Fixed controller command cleanup exceeded bound')from None
        child.stdout.close();child.stderr.close()

def owned_cgroup():
    root=Path('/sys/fs/cgroup/system.slice')/UNIT
    pending=[root];groups=[];pids=set()
    while pending:
        path=pending.pop()
        try:identity=path.lstat()
        except FileNotFoundError:continue
        require(stat.S_ISDIR(identity.st_mode)and not path.is_symlink()and path.is_relative_to(root),'Unexpected owned cgroup subtree')
        groups.append(str(path.relative_to(root)));require(len(groups)<=64,'Owned cgroup subtree bound exceeded')
        try:
            raw=(path/'cgroup.procs').read_bytes();require(len(raw)<=16384,'Owned cgroup PID bytes exceeded bound')
            pids.update(int(value)for value in raw.splitlines());require(len(pids)<=128,'Owned PID bound exceeded')
            for child in path.iterdir():
                if stat.S_ISDIR(child.lstat().st_mode):pending.append(child)
        except FileNotFoundError:pass
    return {'fixed_path':'/system.slice/'+UNIT,'exists':root.exists(),'groups':groups,'pids':sorted(pids)}

def status(a):
    record=ownership();require(record['controller_sha256']==a.controller_sha256,'Controller source changed')
    values=properties();pid=int(values.get('MainPID','0'));namespace={}
    group=values.get('ControlGroup','');require(not group or group=='/system.slice/'+UNIT,'Unexpected owned cgroup')
    if pid:
        for name,path in [('host','/proc/self/ns/net'),('owned','/proc/%d/ns/net'%pid),('host_mount','/proc/self/ns/mnt'),('owned_mount','/proc/%d/ns/mnt'%pid)]:
            try:namespace[name]=os.readlink(path)
            except FileNotFoundError:namespace[name]=None
    census=owned_cgroup();files={};target=runtime(a)
    for name,relative in PUBLIC_PATHS.items():
        if relative is None:continue
        path=target/relative
        if path.exists():
            st=secure_file(path,owner=65534,maximum=2*1024*1024)
            files[name]={'bytes':st.st_size,'uid':st.st_uid,'mode':oct(st.st_mode&0o777)}
    return {'phase':'status','attempt':a.attempt,'unit':UNIT,'properties':values,'network_namespace':namespace,'owned_cgroup_pids':census['pids'],'owned_cgroup':census,'public_files':files}

_original_start = start

def start(a):
    result=_original_start(a);loaded=result['properties']
    require(loaded.get('PrivateNetwork')=='yes'and loaded.get('PrivateMounts')=='yes','Required private namespaces were not loaded')
    require(str(LAB/'runtime/storage')in loaded.get('TemporaryFileSystem',''),'Required private tmpfs was not loaded')
    require(loaded.get('User')=='nobody'and loaded.get('Group')=='nogroup'and loaded.get('NoNewPrivileges')=='yes','Required unprivileged execution was not loaded')
    return result
