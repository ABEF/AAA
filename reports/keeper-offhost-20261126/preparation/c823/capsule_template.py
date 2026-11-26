"""Fixed c823 exact off-host transport and unsigned restore; no live adoption."""
from pathlib import Path
import argparse,base64,hashlib,json,os,re,selectors,signal,stat,subprocess,sys,time
LAB=Path('/opt/popl-keeper-offhost-20261126-c823')
UNIT='popl-keeper-offhost-20261126-c823.service'
OLD=Path('/opt/popl-keeper-sidecar-recovery-20261126-c821')
OLD_UNIT='popl-keeper-sidecar-recovery-20261126-c821'
OLD_UNITS=(OLD_UNIT+'.service',*(OLD_UNIT+'-'+job+'.service'for job in('checks','source','target')))
POLICY_PIN='7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
CONFIG_PIN='1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
OLD_SOURCE_PIN='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
TRUST_REPORT_PIN='9bec125bedd73b6f80cb3f316a7822aa09aeb9198927ca8d901c476f3798c371'
OUTER='a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED='911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
FILES={'manifest.json':(None,OUTER),
 'selection.json':(2354,'dfdabc2c7d8e2510efeaab4861fb034af2536269705ee0000f805ccaadce9bb2'),
 'alert-state.json':(812,'f256fd8ca53e4d45ac11b5c75333f6b4172b8f9579460a1fd7bab48536b3dc98'),
 'selected/manifest.json':(3867,NESTED),
 'selected/journal.json':(2752,'dbb5f86672bd14f017d9c99f3b8ff6b8e6a8cf041d2aa9c2eada60b7598a9112')}
WORKER=__WORKER_BASE64__
WORKER_SHA=__WORKER_SHA__
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def need(value):
    if not value:
        raise ValueError('Fixed isolated scheduling control refused')

def run(argv, timeout=15):
    mask = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM}
    child = owned = None
    output = [bytearray(), bytearray()]
    size = 0
    end = time.monotonic()+timeout
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'},
            start_new_session=True, close_fds=True)
        owned = child
        with selectors.DefaultSelector() as selector:
            for index, pipe in enumerate((child.stdout, child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, index)
            while selector.get_map():
                need(time.monotonic() < end)
                for key, _ in selector.select(min(.1, max(.001, end-time.monotonic()))):
                    raw = os.read(key.fd, min(16384, 65537-size))
                    if not raw:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(raw)
                    need(size <= 65536)
                    output[key.data].extend(raw)
        while True:
            need(time.monotonic() < end)
            previous = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
            try:
                try:
                    code = child.wait(timeout=min(.05, max(.001, end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    continue
                owned = None
                return code, bytes(output[0]), bytes(output[1])
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous)
    finally:
        try:
            if owned is not None:
                previous = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
                try:
                    if owned.returncode is None:
                        try:
                            os.killpg(owned.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    owned.wait(timeout=2)
                    owned = None
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        finally:
            if child is not None:
                child.stdout.close()
                child.stderr.close()

def read(path, maximum, owner=0):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_uid == owner and
        before.st_nlink == 1 and not before.st_mode & 0o022 and 0 <= before.st_size <= maximum)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        data = bytearray()
        while True:
            part = os.read(fd, min(65536, maximum+1-len(data)))
            if not part:
                break
            data.extend(part)
            need(len(data) <= maximum)
        final = os.fstat(fd)
        named = path.lstat()
        key = lambda st: (st.st_dev, st.st_ino, st.st_uid, st.st_mode, st.st_nlink, st.st_size, st.st_mtime_ns)
        need(key(before) == key(opened) == key(final) == key(named) and len(data) == before.st_size)
        return bytes(data)
    finally:
        os.close(fd)

def write_root(name, value):
    need(name in ('LAB_ID.json', 'INSTALL.json', 'START.json', 'FINAL.json'))
    raw = (json.dumps(value, sort_keys=True, allow_nan=False)+'\n').encode()
    need(len(raw) <= 32768)
    fd = os.open(LAB/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result);result[key]=value
    return result


def invalid_number(_):raise ValueError('Unsupported transport number')


def decode(raw):return json.loads(raw,object_pairs_hook=unique,parse_float=invalid_number,parse_constant=invalid_number)


def properties(unit=UNIT):
    need(unit in (UNIT,*OLD_UNITS))
    fields='Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,Type,User,Group,PrivateNetwork,Restart,KillMode,TimeoutStartUSec,TimeoutStopUSec,BindReadOnlyPaths,ReadWritePaths,RestrictAddressFamilies,ExecMainStartTimestampMonotonic,InvocationID'
    code,out,_=run(['/usr/bin/systemctl','show',unit,'--no-pager','--property='+fields])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found');return value


def empty(unit,p):
    need(unit in (UNIT,*OLD_UNITS))
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group=='/system.slice/'+unit)
    try:raw=(Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096);return not raw.strip()


def fenced_original():
    result={}
    for unit in OLD_UNITS:
        p=properties(unit);need(empty(unit,p)and p.get('ActiveState')in('inactive','failed',None))
        need(p.get('LoadState')=='not-found'or p.get('Restart')=='no');result[unit]=p
    return result


def package_inventory():
    folder=OLD/'runtime/sidecar-bundle'
    for path,expected in((folder,{'manifest.json','selection.json','alert-state.json','selected'}),
            (folder/'selected',{'manifest.json','journal.json'})):
        before=path.lstat();need(stat.S_ISDIR(before.st_mode)and before.st_uid==65534 and not before.st_mode&0o077)
        found=set()
        with os.scandir(path)as entries:
            for entry in entries:
                need(len(found)<len(expected)and entry.name in expected and entry.name not in found)
                item=entry.stat(follow_symlinks=False)
                need(stat.S_ISDIR(item.st_mode)if entry.name=='selected'else stat.S_ISREG(item.st_mode)and item.st_nlink==1)
                need(item.st_uid==65534 and not item.st_mode&0o077);found.add(entry.name)
        after=path.lstat();need(found==expected and (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino))


def original_snapshot():
    fence=fenced_original();package_inventory();raw=read(OLD/'SOURCE_MANIFEST.json',65536)
    need(sha(raw)==OLD_SOURCE_PIN);source=decode(raw);pins={}
    for name,row in source['source_files'].items():
        data=read(OLD/'source'/name,1024*1024)
        need(len(data)==row['bytes']and sha(data)==row['sha256']);pins[name]=sha(data)
    refs={}
    for name,digest in(('policy.json',POLICY_PIN),('keeper-config.json',CONFIG_PIN)):
        data=read(OLD/'runtime'/name,65536,owner=0 if name=='policy.json'else 65534)
        need(sha(data)==digest);refs[name]=sha(data)
    for name in('working/runtime/journal.json','schedule/selected.json','alerts/state.json'):
        refs[name]=sha(read(OLD/'runtime'/name,65536,owner=65534))
    package={}
    for name,(size,digest)in FILES.items():
        data=read(OLD/'runtime/sidecar-bundle'/name,65536,owner=65534)
        need(sha(data)==digest and (size is None or len(data)==size));package[name]={'bytes':len(data),'sha256':digest}
    package_inventory()
    return{'fenced_units':fence,'protected_reference_hashes':refs,'source_files_sha256':pins,
        'package_files':package,'source_manifest_sha256':OLD_SOURCE_PIN}


def unchanged(before,after):
    return all(before[key]==after[key]for key in('protected_reference_hashes','source_files_sha256','package_files','source_manifest_sha256'))


def package_data(files):
    need(type(files)is dict and set(files)==set(FILES));result={};total=0
    for name,(size,digest)in FILES.items():
        row=files[name];need(type(row)is dict and set(row)=={'bytes','sha256','raw_base64'})
        raw=base64.b64decode(row['raw_base64'],validate=True)
        need(type(row['bytes'])is int and row['bytes']==len(raw)and 0<len(raw)<=65536
            and sha(raw)==row['sha256']==digest and (size is None or len(raw)==size))
        total+=len(raw);need(total<=65536);result[name]=raw
    return result


def export(a):
    need(os.getuid()==0)
    before=original_snapshot();files={}
    for name in FILES:
        raw=read(OLD/'runtime/sidecar-bundle'/name,65536,owner=65534)
        files[name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    package_data(files);after=original_snapshot();need(unchanged(before,after))
    result={'schema':1,'kind':'popl-keeper-offhost-export','unsigned':True,'readiness_approved':False,
        'files':files,'original_fenced_before_and_after':True,'original_reference_snapshot_sha256':sha(enc(before)),
        'source_trust_report_sha256':TRUST_REPORT_PIN,'original_files_unchanged':True,
        'policy_configuration_and_signer_material_exported':False}
    need(len(enc(result))<=65536);return result


def owned():
    need(os.getuid()==0)
    item=LAB.lstat();need(stat.S_ISDIR(item.st_mode)and item.st_uid==0 and not item.st_mode&0o022)
    identity=decode(read(LAB/'LAB_ID.json',32768))
    need(identity['controller_sha256']==ACTIVE_CONTROLLER_SHA and identity['worker_sha256']==WORKER_SHA)
    need(sha(read(LAB/'worker.py',65536))==WORKER_SHA)
    need(sha(read(LAB/'desktop-proof.json',8192))==identity['desktop_proof_sha256'])
    return identity


def install(a):
    need(os.getuid()==0 and not os.path.lexists(LAB)and properties().get('LoadState')=='not-found')
    need(type(a.desktop_proof_sha256)is str and re.fullmatch('[0-9a-f]{64}',a.desktop_proof_sha256)is not None)
    raw=sys.stdin.buffer.read(65537);need(0<len(raw)<=65536);packet=decode(raw)
    need(type(packet)is dict and set(packet)=={'schema','kind','files','desktop_proof_base64'}
        and type(packet['schema'])is int and packet['schema']==1 and packet['kind']=='popl-keeper-offhost-import')
    files=package_data(packet['files']);proof_raw=base64.b64decode(packet['desktop_proof_base64'],validate=True)
    need(0<len(proof_raw)<=8192 and sha(proof_raw)==a.desktop_proof_sha256);proof=decode(proof_raw)
    need(type(proof['schema'])is int and proof['schema']==1 and proof['kind']=='popl-keeper-offhost-desktop-proof'and proof['ok']is True
        and proof['unsigned']is True and proof['readiness_approved']is False and proof['production_approved']is False)
    need(proof['outer_manifest_sha256']==OUTER and proof['nested_manifest_sha256']==NESTED
        and proof['policy_sha256']==POLICY_PIN and proof['configuration_sha256']==CONFIG_PIN
        and proof['source_trust_report_sha256']==TRUST_REPORT_PIN)
    need(proof['files']=={name:{'bytes':len(data),'sha256':sha(data)}for name,data in files.items()})
    before=original_snapshot();worker=base64.b64decode(WORKER,validate=True);need(sha(worker)==WORKER_SHA)
    LAB.mkdir(mode=0o755);runtime=LAB/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,65534,65534)
    imported=runtime/'imported';imported.mkdir(mode=0o700);os.chown(imported,65534,65534)
    (imported/'selected').mkdir(mode=0o700);os.chown(imported/'selected',65534,65534)
    for name,data in files.items():
        path=imported/name;fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno());os.fchown(stream.fileno(),65534,65534)
    for name,data in(('worker.py',worker),('desktop-proof.json',proof_raw)):
        fd=os.open(LAB/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
        with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o444)
    masks=LAB/'masks';masks.mkdir(mode=0o755)
    for name in('key.empty','password.empty'):
        fd=os.open(masks/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0);os.fchmod(fd,0);os.close(fd)
    os.chmod(masks,0o555)
    for name in('stdout.log','stderr.log'):
        fd=os.open(runtime/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.fchown(fd,65534,65534);os.close(fd)
    after=original_snapshot();need(unchanged(before,after))
    write_root('INSTALL.json',{'schema':1,'original_before':before,'original_after':after,'original_unchanged':True,
        'desktop_proof_sha256':a.desktop_proof_sha256,'input_wire_bytes':len(raw),'input_files':proof['files']})
    write_root('LAB_ID.json',{'schema':1,'controller_sha256':a.controller_sha256,'worker_sha256':WORKER_SHA,
        'desktop_proof_sha256':a.desktop_proof_sha256,'input_files':proof['files']})
    return{'phase':'installed','same_desktop_bytes_imported':True,'input_wire_bytes':len(raw),
        'input_files':proof['files'],'desktop_proof_sha256':a.desktop_proof_sha256,'original_unchanged':True}


def start(a):
    owned();before=original_snapshot();need(not(LAB/'START.json').exists()and properties().get('LoadState')=='not-found')
    masks=[(LAB/'masks'/name).lstat()for name in('key.empty','password.empty')]
    need(all(stat.S_ISREG(item.st_mode)and item.st_uid==0 and item.st_nlink==1 and item.st_size==0
        and stat.S_IMODE(item.st_mode)==0 for item in masks)and len({(item.st_dev,item.st_ino)for item in masks})==2)
    binds=[str(OLD/'source'),str(OLD/'runtime'),str(LAB/'masks/key.empty')+':'+str(OLD/'runtime/working/keystore.secret'),
        str(LAB/'masks/password.empty')+':'+str(OLD/'runtime/working/password.secret')]
    policy={'Type':'oneshot','User':'nobody','Group':'nogroup','PrivateNetwork':'yes','PrivateTmp':'yes',
        'PrivateDevices':'yes','ProtectSystem':'strict','ProtectHome':'yes','NoNewPrivileges':'yes',
        'ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectControlGroups':'yes',
        'RestrictSUIDSGID':'yes','LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
        'RestrictAddressFamilies':'AF_UNIX','ReadWritePaths':str(LAB/'runtime'),'UMask':'0077','Restart':'no',
        'RemainAfterExit':'yes','TimeoutStartSec':'180','TimeoutStopSec':'2','KillMode':'control-group',
        'SendSIGKILL':'yes','FinalKillSignal':'SIGKILL','MemoryMax':'256M','MemorySwapMax':'0','TasksMax':'32',
        'LimitCORE':'0','LimitFSIZE':'65536','StartLimitIntervalSec':'0','BindReadOnlyPaths':' '.join(binds),
        'StandardOutput':'append:'+str(LAB/'runtime/stdout.log'),'StandardError':'append:'+str(LAB/'runtime/stderr.log'),
        'WorkingDirectory':str(LAB)}
    argv=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+UNIT]
    argv+=['--property='+key+'='+value for key,value in policy.items()]
    argv+=['--setenv='+key+'='+value for key,value in{'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}.items()]
    code,_,_=run([*argv,'--','/usr/bin/python3','-B',str(LAB/'worker.py')]);need(code==0)
    write_root('START.json',{'schema':1,'original_before':before,'policy':policy,'only_new_unit_started':UNIT})
    return{'phase':'started','unit':UNIT,'properties':properties()}


def status(a):
    owned();p=properties();raw_sizes={name:(LAB/'runtime'/name).stat().st_size for name in('stdout.log','stderr.log')}
    need(sum(raw_sizes.values())<=65536)
    return{'phase':'status','properties':p,'group_empty':empty(UNIT,p),'result_present':(LAB/'runtime/RESULT.json').exists(),
        'actual_execution_started':p.get('ExecMainStartTimestampMonotonic','0').isdigit()and int(p.get('ExecMainStartTimestampMonotonic','0'))>0,
        'output_bytes':raw_sizes}


def stop(a):
    owned();before=properties()
    if before.get('LoadState')!='not-found':code,_,_=run(['/usr/bin/systemctl','stop',UNIT]);need(code==0)
    after=properties();need(empty(UNIT,after));original=original_snapshot()
    installed=decode(read(LAB/'INSTALL.json',32768));need(unchanged(installed['original_before'],original))
    if not(LAB/'FINAL.json').exists():write_root('FINAL.json',{'schema':1,'before_stop':before,'after_stop':after,
        'new_group_empty':True,'original_after':original,'original_unchanged':True,'old_four_groups_fenced':True})
    return{'phase':'stopped','new_group_empty':True,'old_four_groups_fenced':True,'original_unchanged':True}


def fetch(a):
    owned();need(a.artifact in('RESULT.json','PROGRESS.json','FINAL.json','INSTALL.json'))
    path=LAB/a.artifact if a.artifact in('FINAL.json','INSTALL.json')else LAB/'runtime'/a.artifact
    raw=read(path,32768,owner=0 if a.artifact in('FINAL.json','INSTALL.json')else 65534)
    return{'phase':'saved_artifact','name':a.artifact,'bytes':len(raw),'sha256':sha(raw),'base64':base64.b64encode(raw).decode('ascii')}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('export','install','start','status','stop','fetch'))
    parser.add_argument('--controller-sha256',required=True);parser.add_argument('--desktop-proof-sha256');parser.add_argument('--artifact')
    args=parser.parse_args();need(re.fullmatch('[0-9a-f]{64}',args.controller_sha256)is not None)
    globals()['ACTIVE_CONTROLLER_SHA']=args.controller_sha256
    print(json.dumps(globals()[args.action](args),sort_keys=True))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'scope':'fixed_c823_only'}))
        raise SystemExit(1)from None
