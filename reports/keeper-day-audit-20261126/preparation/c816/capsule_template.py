"""Closed c816 read-only day-audit selection in a fresh private-network unit."""
from pathlib import Path,PurePosixPath
import argparse,base64,hashlib,io,json,os,re,selectors,signal,stat,subprocess,sys,tarfile,time

LAB=Path('/opt/popl-keeper-day-audit-20261126-c816')
UNIT='popl-keeper-day-audit-20261126-c816.service'
EXPECTED=__MEMBERS__
BUNDLE_SHA=__BUNDLE_SHA__
SOURCE_MANIFEST_SHA=__SOURCE_MANIFEST_SHA__
SELECTED=__SELECTED__
MAX_ARCHIVE=2*1024*1024
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def need(value):
    if not value:raise ValueError('Fixed isolated day-audit selection refused')

def clear_signal_mask():
    signal.pthread_sigmask(signal.SIG_SETMASK,set())

def run(argv,timeout=15):
    """Bound one fixed manager query; never reap before ownership is cleared."""
    mask={signal.SIGALRM,signal.SIGTERM,signal.SIGHUP,signal.SIGINT}
    owned=None;child=None;outputs=[bytearray(),bytearray()];size=0;end=time.monotonic()+timeout
    try:
        previous=signal.pthread_sigmask(signal.SIG_BLOCK,mask)
        try:
            child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'},start_new_session=True,close_fds=True,preexec_fn=clear_signal_mask)
            owned=child
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<end)
                for key,_ in selector.select(min(.1,max(.001,end-time.monotonic()))):
                    raw=os.read(key.fd,min(16384,65537-size))
                    if not raw:selector.unregister(key.fileobj);continue
                    size+=len(raw);need(size<=65536);outputs[key.data].extend(raw)
        while True:
            need(time.monotonic()<end)
            previous=signal.pthread_sigmask(signal.SIG_BLOCK,mask)
            try:
                code=child.wait(timeout=min(.05,max(.001,end-time.monotonic())))
                owned=None
                return code,bytes(outputs[0]),bytes(outputs[1])
            except subprocess.TimeoutExpired:pass
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
    finally:
        if owned is not None:
            previous=signal.pthread_sigmask(signal.SIG_BLOCK,mask)
            try:
                # Popen may have reaped while handling an interrupt. A reused
                # numeric process-group ID must never be signalled then.
                if owned.returncode is None:
                    try:os.killpg(owned.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                owned.wait(timeout=2);owned=None
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
        if child is not None:child.stdout.close();child.stderr.close()

def properties():
    code,out,err=run(['/usr/bin/systemctl','show',UNIT,'--no-pager','--property=Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,ExecStart,User,Group,PrivateNetwork,PrivateDevices,ProtectSystem,ProtectHome,NoNewPrivileges,Restart,NRestarts,KillMode,RuntimeMaxUSec,TimeoutStartUSec,TimeoutStopUSec,MemoryMax,MemorySwapMax,TasksMax,WorkingDirectory,ReadWritePaths'])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found')
    return value

def secure_read(path,maximum,owner=0,mode=None):
    st=path.lstat();need(stat.S_ISREG(st.st_mode)and not path.is_symlink()and st.st_uid==owner
        and st.st_nlink==1 and not st.st_mode&0o022 and 0<=st.st_size<=maximum)
    if mode is not None:need(stat.S_IMODE(st.st_mode)==mode)
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        first=os.fstat(fd);need((first.st_dev,first.st_ino)==(st.st_dev,st.st_ino))
        data=b''
        while True:
            raw=os.read(fd,min(65536,maximum+1-len(data)))
            if not raw:break
            data+=raw;need(len(data)<=maximum)
        last=os.fstat(fd);name=path.lstat()
        key=lambda v:(v.st_dev,v.st_ino,v.st_uid,v.st_mode,v.st_nlink,v.st_size,v.st_mtime_ns)
        need(key(st)==key(first)==key(last)==key(name)and len(data)==st.st_size)
        return data
    finally:os.close(fd)

def owned():
    need(os.geteuid()==0)
    for path in (Path('/opt'),LAB):
        st=path.lstat();need(stat.S_ISDIR(st.st_mode)and st.st_uid==0 and not st.st_mode&0o022)
    record=json.loads(secure_read(LAB/'LAB_ID.json',16384))
    need(record=={'schema':1,'unit':UNIT,'lab':str(LAB),'controller_sha256':ACTIVE_CONTROLLER_SHA,
        'bundle_sha256':BUNDLE_SHA,'source_manifest_sha256':SOURCE_MANIFEST_SHA})

def source_identity():
    result={}
    for name,pin in EXPECTED.items():
        raw=secure_read(LAB/name,1024*1024);need(len(raw)==pin['bytes']and sha(raw)==pin['sha256'])
        need(not(LAB/name).stat().st_mode&0o222);result[name]=sha(raw)
    return result

def write_root(name,value):
    need(name in ('LAB_ID.json','INSTALL.json','START.json','FINAL.json'))
    raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(len(raw)<=65536)
    fd=os.open(LAB/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())

def install(a):
    need(os.geteuid()==0 and not os.path.lexists(LAB)and properties().get('LoadState')=='not-found')
    raw=sys.stdin.buffer.read(MAX_ARCHIVE+1);need(0<len(raw)<=MAX_ARCHIVE and sha(raw)==BUNDLE_SHA)
    data={};total=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz')as archive:
        for item in archive:
            need(len(data)<len(EXPECTED)and item.name in EXPECTED and item.name not in data
                and item.isfile()and item.name==str(PurePosixPath(item.name))and not item.name.startswith('/')
                and '..'not in PurePosixPath(item.name).parts and '\\'not in item.name and ':'not in item.name
                and 0<=item.size<=1024*1024)
            total+=item.size;need(total<=8*1024*1024)
            value=archive.extractfile(item).read(1024*1024+1)
            need(EXPECTED[item.name]=={'bytes':len(value),'sha256':sha(value)});data[item.name]=value
    need(set(data)==set(EXPECTED)and sha(data['SOURCE_MANIFEST.json'])==SOURCE_MANIFEST_SHA)
    manifest=json.loads(data['SOURCE_MANIFEST.json']);need(manifest['selected_methods']==list(SELECTED))
    LAB.mkdir(mode=0o755);os.chmod(LAB,0o755)
    for name,value in sorted(data.items()):
        path=LAB/name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444);os.fchmod(fd,0o444)
        with os.fdopen(fd,'wb')as f:f.write(value);f.flush();os.fsync(f.fileno())
    for path in sorted((p for p in LAB.rglob('*')if p.is_dir()),key=lambda p:len(p.parts),reverse=True):os.chmod(path,0o755)
    runtime=LAB/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,65534,65534)
    for name in ('tmp','home'):
        path=runtime/name;path.mkdir(mode=0o700);os.chown(path,65534,65534)
    for name in ('stdout.log','stderr.log'):
        path=runtime/name;fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.fchown(fd,65534,65534);os.close(fd)
    write_root('INSTALL.json',{'schema':1,'source_before':source_identity()})
    write_root('LAB_ID.json',{'schema':1,'unit':UNIT,'lab':str(LAB),'controller_sha256':a.controller_sha256,
        'bundle_sha256':BUNDLE_SHA,'source_manifest_sha256':SOURCE_MANIFEST_SHA})
    return {'phase':'installed','source':source_identity(),'existing_units_changed':False}

def start(a):
    owned();need(not(LAB/'START.json').exists()and properties().get('LoadState')=='not-found')
    before=source_identity();runtime=LAB/'runtime'
    policy={'Type':'oneshot','User':'nobody','Group':'nogroup','PrivateNetwork':'yes','PrivateTmp':'yes',
        'PrivateDevices':'yes','ProtectSystem':'strict','ProtectHome':'yes','NoNewPrivileges':'yes',
        'ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectControlGroups':'yes',
        'RestrictSUIDSGID':'yes','LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
        'RestrictAddressFamilies':'AF_UNIX AF_INET AF_INET6','ReadWritePaths':str(runtime),'UMask':'0077',
        'Restart':'no','RemainAfterExit':'yes','RuntimeMaxSec':'180','TimeoutStartSec':'180','TimeoutStopSec':'2',
        'KillMode':'control-group','SendSIGKILL':'yes','FinalKillSignal':'SIGKILL','MemoryMax':'512M',
        'MemorySwapMax':'0','TasksMax':'64','CPUQuota':'100%','LimitCORE':'0','LimitFSIZE':'65536',
        'WorkingDirectory':str(LAB/'source'),'StandardOutput':'append:'+str(runtime/'stdout.log'),
        'StandardError':'append:'+str(runtime/'stderr.log')}
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(LAB/'source'),'PYTHONDONTWRITEBYTECODE':'1',
        'PYTHONNOUSERSITE':'1','PYTHONUNBUFFERED':'1','TMPDIR':str(runtime/'tmp'),'HOME':str(runtime/'home'),
        'POPL_LAB_HOST_NETWORK_NAMESPACE':os.readlink('/proc/self/ns/net')}
    argv=['/usr/bin/python3','-B',str(LAB/'source/run_selected.py')]
    command=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+UNIT]
    for key,value in policy.items():command.append('--property='+key+'='+value)
    for key,value in env.items():command.append('--setenv='+key+'='+value)
    code,out,err=run([*command,'--',*argv]);need(code==0)
    write_root('START.json',{'schema':1,'source_before':before,'policy':policy,'environment':env,'argv':argv,
        'no_signer_or_existing_journal':True,'selected_methods':list(SELECTED)})
    return {'phase':'started','unit':UNIT,'properties':properties()}

def group_empty(p):
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group=='/system.slice/'+UNIT)
    path=Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs'
    try:raw=path.read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096);return not raw.strip()

def status(a):
    owned();p=properties();counts={}
    for name in ('stdout.log','stderr.log'):
        st=(LAB/'runtime'/name).lstat();need(stat.S_ISREG(st.st_mode)and st.st_uid==65534 and st.st_nlink==1)
        counts[name]=st.st_size
    overflow=sum(counts.values())>65536
    if overflow and not group_empty(p):run(['/usr/bin/systemctl','stop','--no-block',UNIT]);p=properties()
    terminal=group_empty(p)and p.get('SubState')in ('dead','failed','exited')
    return {'phase':'status','unit':UNIT,'properties':p,'group_empty':group_empty(p),'terminal':terminal,
        'combined_output_bytes':sum(counts.values()),'output_limit_exceeded':overflow,
        'result_present':(LAB/'runtime/RESULT.json').exists()}

def stop(a):
    owned();before=properties()
    if before.get('LoadState')!='not-found':
        code,out,err=run(['/usr/bin/systemctl','stop',UNIT],timeout=10);need(code==0)
    final=status(a);need(final['group_empty'])
    if not(LAB/'FINAL.json').exists():
        start_record=json.loads(secure_read(LAB/'INSTALL.json',65536));after=source_identity()
        write_root('FINAL.json',{'schema':1,'source_before':start_record['source_before'],'source_after':after,
            'source_unchanged':start_record['source_before']==after,'all_owned_group_empty':True,'status':final})
    return {'phase':'stopped','all_owned_group_empty':True,'status':final}

def fetch(a):
    owned();need(a.artifact in ('RESULT.json','FINAL.json','PROGRESS.json'))
    if a.artifact in ('RESULT.json','PROGRESS.json'):raw=secure_read(LAB/'runtime'/a.artifact,65536,owner=65534,mode=0o600)
    else:raw=secure_read(LAB/'FINAL.json',65536)
    return {'phase':'saved_artifact','name':a.artifact,'bytes':len(raw),'sha256':sha(raw),'base64':base64.b64encode(raw).decode('ascii')}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('install','start','status','stop','fetch'))
    p.add_argument('--controller-sha256',required=True);p.add_argument('--artifact');a=p.parse_args()
    need(re.fullmatch('[0-9a-f]{64}',a.controller_sha256)is not None)
    globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256
    value=globals()[a.action](a);print(json.dumps(value,sort_keys=True))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'fixed_scope':'isolated_c816_alert_selection'}))
        raise SystemExit(1)from None
