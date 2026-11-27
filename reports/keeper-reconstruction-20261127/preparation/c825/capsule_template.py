"""Fixed c825 coordinator. Reconstructs only two new private RootDirectories."""
from pathlib import Path
import argparse,base64,hashlib,json,os,re,selectors,signal,stat,subprocess,sys,time,zlib

LAB=Path('/opt/popl-keeper-reconstruction-20261127-c825')
OLD=Path('/opt/popl-keeper-sidecar-recovery-20261126-c821')
UNIT_BASE='popl-keeper-reconstruction-20261127-c825'
MODES=('negative','complete')
OLD_BASE='popl-keeper-sidecar-recovery-20261126-c821'
OLD_UNITS=(OLD_BASE+'.service',*(OLD_BASE+'-'+job+'.service'for job in('checks','source','target')))
SOURCE_PIN='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
CONFIG_PIN='1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
POLICY_PIN='7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
OUTER='a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED='911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
SOURCE_FILES=__SOURCE_PINS__
PACKAGE_FILES={'manifest.json':{'bytes':None,'sha256':OUTER},
    'selection.json':{'bytes':2354,'sha256':'dfdabc2c7d8e2510efeaab4861fb034af2536269705ee0000f805ccaadce9bb2'},
    'alert-state.json':{'bytes':812,'sha256':'f256fd8ca53e4d45ac11b5c75333f6b4172b8f9579460a1fd7bab48536b3dc98'},
    'selected/manifest.json':{'bytes':3867,'sha256':NESTED},
    'selected/journal.json':{'bytes':2752,'sha256':'dbb5f86672bd14f017d9c99f3b8ff6b8e6a8cf041d2aa9c2eada60b7598a9112'}}
WORKER=__WORKER_BASE64__
WORKER_SHA=__WORKER_SHA__
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def need(value,code='fixed_c825_refused'):
    if not value:raise ValueError(code)


def run(argv,timeout=15):
    child=owned=None;parts=[bytearray(),bytearray()];size=0;end=time.monotonic()+timeout
    try:
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'},start_new_session=True,close_fds=True);owned=child
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<end,'control_deadline')
                for key,_ in selector.select(min(.1,max(.001,end-time.monotonic()))):
                    raw=os.read(key.fd,min(16384,65537-size))
                    if not raw:selector.unregister(key.fileobj);continue
                    size+=len(raw);need(size<=65536,'control_capture_bound');parts[key.data].extend(raw)
        code=child.wait(timeout=max(.001,end-time.monotonic()));owned=None
        return code,bytes(parts[0]),bytes(parts[1])
    finally:
        try:
            if owned is not None:
                if owned.poll()is None:
                    try:os.killpg(owned.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                owned.wait(timeout=2)
        finally:
            if child is not None:child.stdout.close();child.stderr.close()


def read(path,maximum=1048576,owner=0):
    before=path.lstat();need(stat.S_ISREG(before.st_mode)and before.st_uid==owner and before.st_nlink==1
        and not before.st_mode&0o022 and before.st_size<=maximum,'file_metadata')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        raw=bytearray()
        while True:
            part=os.read(fd,min(65536,maximum+1-len(raw)))
            if not part:break
            raw.extend(part);need(len(raw)<=maximum,'file_bound')
        key=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns)
        need(key(before)==key(os.fstat(fd))==key(path.lstat())and len(raw)==before.st_size,'file_changed')
        return bytes(raw)
    finally:os.close(fd)


def unique(pairs):
    result={}
    for key,value in pairs:need(key not in result,'duplicate_key');result[key]=value
    return result


def invalid(_):raise ValueError('invalid_number')


def decode(raw):return json.loads(raw,object_pairs_hook=unique,parse_float=invalid,parse_constant=invalid)


def properties(unit):
    need(unit in(*OLD_UNITS,*(UNIT_BASE+'-'+mode+'.service'for mode in MODES)))
    fields='Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,User,Group,PrivateNetwork,Restart,KillMode,RootDirectory,BindReadOnlyPaths,ReadWritePaths,RestrictAddressFamilies,InvocationID'
    code,out,_=run(['/usr/bin/systemctl','show',unit,'--no-pager','--property='+fields])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found');return value


def empty(unit,p):
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group=='/system.slice/'+unit)
    try:raw=(Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096);return not raw.strip()


def original_snapshot():
    fence={}
    for unit in OLD_UNITS:
        props=properties(unit);need(empty(unit,props)and props.get('ActiveState')in('inactive','failed',None))
        need(props.get('LoadState')=='not-found'or props.get('Restart')=='no');fence[unit]=props
    manifest=read(OLD/'SOURCE_MANIFEST.json');need(sha(manifest)==SOURCE_PIN,'original_source_manifest')
    pins={}
    for name,row in SOURCE_FILES.items():
        raw=read(OLD/'source'/name);need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'original_source_pin');pins[name]=row
    refs={}
    for name,digest,owner in(('keeper-config.json',CONFIG_PIN,65534),('policy.json',POLICY_PIN,0)):
        raw=read(OLD/'runtime'/name,65536,owner);need(sha(raw)==digest,'original_reference_pin')
        refs[name]={'bytes':len(raw),'sha256':digest}
    retained={}
    for name in('working/runtime/journal.json','schedule/selected.json','alerts/state.json',
            *('sidecar-bundle/'+name for name in PACKAGE_FILES)):
        path=OLD/'runtime'/name;raw=read(path,65536,65534);item=path.lstat()
        retained[name]={'bytes':len(raw),'sha256':sha(raw),'metadata':[item.st_dev,item.st_ino,item.st_uid,
            item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns]}
        if name.startswith('sidecar-bundle/'):
            expected=PACKAGE_FILES[name[len('sidecar-bundle/'):]]
            need(sha(raw)==expected['sha256']and(expected['bytes']is None or len(raw)==expected['bytes']),'original_package_pin')
    metadata=[]
    for path in(OLD/'runtime/schedule/schedule.lock',OLD/'runtime/alerts/alert.lock'):
        item=path.lstat();need(stat.S_ISREG(item.st_mode)and item.st_uid==65534 and item.st_nlink==1
            and stat.S_IMODE(item.st_mode)==0o600,'old_lock_metadata')
        metadata.append([item.st_dev,item.st_ino,item.st_uid,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns])
    st=(OLD/'SOURCE_MANIFEST.json').lstat()
    return{'fenced_units':fence,'source_manifest_sha256':SOURCE_PIN,'source_files':pins,'references':refs,'retained_original_files':retained,
        'old_lock_metadata':metadata,'old_source_manifest_inode_pair':[st.st_dev,st.st_ino]}


def unchanged(before,after):
    return all(before[key]==after[key]for key in('source_manifest_sha256','source_files','references','retained_original_files','old_lock_metadata','old_source_manifest_inode_pair'))


def runtime_tree(folder):
    allowed_links={'sitecustomize.py':'/etc/python3.12/sitecustomize.py',
        '_sysconfigdata__linux_x86_64-linux-gnu.py':'_sysconfigdata__x86_64-linux-gnu.py',
        'config-3.12-x86_64-linux-gnu/libpython3.12.so':'../../x86_64-linux-gnu/libpython3.12.so.1'}
    rows=[];total=0;visited=0;links=set();stack=[(folder,0)];end=time.monotonic()+20
    while stack:
        directory,depth=stack.pop();need(depth<=16 and time.monotonic()<end,'runtime_inventory_deadline')
        with os.scandir(directory)as entries:
            for entry in entries:
                visited+=1;need(visited<=8192 and time.monotonic()<end,'runtime_inventory_bound')
                if entry.name in('site-packages','dist-packages'):continue
                item=entry.stat(follow_symlinks=False);path=Path(entry.path)
                if stat.S_ISDIR(item.st_mode):stack.append((path,depth+1));continue
                if path.suffix not in('.py','.so','.pyc'):continue
                relative=str(path.relative_to(folder))
                if stat.S_ISLNK(item.st_mode):
                    need(relative in allowed_links and item.st_uid==0 and item.st_nlink==1,'runtime_link_metadata')
                    key=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
                    target=os.readlink(path);need(target==allowed_links[relative]and key(item)==key(path.lstat()),'runtime_link_target')
                    need(os.readlink(path)==target and key(item)==key(path.lstat()),'runtime_link_changed')
                    rows.append(['symlink',relative,target,item.st_uid,stat.S_IMODE(item.st_mode),item.st_nlink]);links.add(relative);continue
                need(stat.S_ISREG(item.st_mode)and not item.st_mode&0o022,'runtime_file_metadata')
                raw=read(path,16777216);total+=len(raw);need(total<=134217728 and len(rows)<4096,'runtime_inventory_bound')
                rows.append(['file',relative,len(raw),sha(raw)])
    rows.sort()
    need(rows and links==set(allowed_links),'runtime_required_links')
    return{'files':len(rows)-len(links),'symlinks':len(links),'entries':len(rows),'bytes':total,'sha256':sha(enc(rows))}


def runtime_review():
    # Only OS stdlib imports. This explicitly supplies and records the external runtime.
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode,'controller_python_isolation')
    import copy,datetime,decimal,fcntl,functools,http.client,math,secrets,shutil,socket,ssl,tempfile,typing,urllib.error,urllib.request,bz2,lzma
    stdlib=Path(os.__file__).resolve().parent;need(re.fullmatch('/usr/lib/python3\\.[0-9]+',str(stdlib))is not None,'OS_stdlib_path')
    executable=Path(sys.executable).resolve();need(re.fullmatch('/usr/bin/python3\\.[0-9]+',str(executable))is not None,'OS_interpreter_path')
    mapped=set()
    with Path('/proc/self/maps').open('rb')as stream:maps_raw=stream.read(65537)
    need(len(maps_raw)<=65536,'OS_maps_bound')
    for line in maps_raw.decode('utf8','strict').splitlines():
        part=line.split(None,5)
        if len(part)==6 and part[5].startswith('/'):
            candidate=Path(part[5]).resolve()
            if '.so'in candidate.name and not candidate.is_relative_to(stdlib):
                need(str(candidate).startswith('/usr/lib/x86_64-linux-gnu/'),'OS_library_scope');mapped.add(candidate)
    need(0<len(mapped)<=32,'OS_library_count')
    mounts=[{'source':str(executable),'target':'/usr/bin/python3'},
        {'source':str(stdlib),'target':str(stdlib)}]
    mounts.extend({'source':str(path),'target':str(path)}for path in sorted(mapped))
    loader=Path('/lib64/ld-linux-x86-64.so.2').resolve();need(loader in mapped,'OS_loader_not_mapped')
    mounts.append({'source':str(loader),'target':'/lib64/ld-linux-x86-64.so.2'})
    # Exact paths observed by the separate c824 loader/LDD diagnosis. These are
    # six file mounts in the NEW root, never a host library-directory mount.
    aliases={
        '/lib/x86_64-linux-gnu/libm.so.6':('/usr/lib/x86_64-linux-gnu/libm.so.6',952616,'5dcc4d25466e29ca390ed6fabb371c69b65dff6fa4e91c34561057a020d6994a'),
        '/lib/x86_64-linux-gnu/libz.so.1':('/usr/lib/x86_64-linux-gnu/libz.so.1.3',113000,'f61677c7bdb7c2aa2a243ea781bfd16afcb361cede7b4ef76127a9d8eb9a5242'),
        '/lib/x86_64-linux-gnu/libexpat.so.1':('/usr/lib/x86_64-linux-gnu/libexpat.so.1.9.1',186624,'286682ecbc5e59a638963b1a4e6351e65eb32fcf4bdcb9cb7569b6a61fe06a8d'),
        '/lib/x86_64-linux-gnu/libc.so.6':('/usr/lib/x86_64-linux-gnu/libc.so.6',2129424,'755a371e86cc9f564ab54f66140747700fb0a103f698f659f2060f707897e09a'),
        '/lib/x86_64-linux-gnu/libbz2.so.1.0':('/usr/lib/x86_64-linux-gnu/libbz2.so.1.0.4',78944,'cc08c9f50a8009ffd6391e0116a100369b11ca9238fa52392c019e6645b122a1'),
        '/lib/x86_64-linux-gnu/liblzma.so.5':('/usr/lib/x86_64-linux-gnu/liblzma.so.5.4.5',202904,'26b37d25f7ca2a2d348de8ecabacda12e921cd933b21fa069a179760db77219d')}
    alias_review={}
    for logical,(canonical,size,digest)in aliases.items():
        path=Path(logical);before=path.lstat();source=Path(canonical)
        need(before.st_uid==0 and before.st_nlink==1 and(stat.S_ISREG(before.st_mode)or stat.S_ISLNK(before.st_mode)),'OS_alias_metadata')
        need(path.resolve(strict=True)==source and source in mapped,'OS_alias_canonical')
        raw=read(source,16777216);need(len(raw)==size and sha(raw)==digest,'OS_alias_pin')
        key=lambda item:(item.st_dev,item.st_ino,item.st_uid,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns,item.st_ctime_ns)
        need(key(path.lstat())==key(before)and path.resolve(strict=True)==source
            and(source.stat().st_dev,source.stat().st_ino)==(path.stat().st_dev,path.stat().st_ino),'OS_alias_changed')
        mounts.append({'source':canonical,'target':logical})
        alias_review[logical]={'source':canonical,'bytes':size,'sha256':digest,
            'host_uid':before.st_uid,'host_mode':stat.S_IMODE(before.st_mode),'host_link_count':before.st_nlink}
    files={}
    for row in mounts:
        if row['target']==str(stdlib):continue
        raw=read(Path(row['source']),16777216);files[row['target']]={'bytes':len(raw),'sha256':sha(raw)}
    return{'schema':1,'kind':'popl-c825-external-OS-runtime','version':sys.version,'stdlib':str(stdlib),
        'stdlib_tree':runtime_tree(stdlib),'stdlib_inventory_scope':'regular .py/.so/.pyc bytes including caches plus exactly3 reviewed link metadata; pruned site-packages/dist-packages; link targets never followed',
        'mounts':mounts,'files':files,'required_logical_aliases':alias_review,
        'site_packages_enabled':False,'OS_runtime_is_external':True,
        'OS_disaster_recovery_proved':False,'actual_second_host':False}


def export(a):
    need(os.getuid()==0);before=original_snapshot();files={}
    for name,owner in(('keeper-config.json',65534),('policy.json',0)):
        raw=read(OLD/'runtime'/name,65536,owner);files['references/'+name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    runtime=runtime_review();after=original_snapshot();need(unchanged(before,after))
    response={'schema':1,'kind':'popl-keeper-reconstruction-reference-export','files':files,'runtime_review':runtime,
        'runtime_review_sha256':sha(enc(runtime)),'original_snapshot_sha256':sha(enc(before)),
        'source_manifest_sha256':SOURCE_PIN,'source_files_count':41,'original_unchanged':True,
        'source_bodies_exported':False,'working_journal_exported':False,'signer_material_exported':False,
        'unsigned':True,'readiness_approved':False}
    need(len(enc(response))<=65536,'reference_export_bound');return response


def write(path,raw,mode=0o444,owner=0):
    need(len(raw)<=2097152,'write_bound');path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno());os.fchown(stream.fileno(),owner,owner);os.fchmod(stream.fileno(),mode)


def expected_files():
    result={'source/'+name:row for name,row in SOURCE_FILES.items()}
    result.update({'SOURCE_MANIFEST.json':{'bytes':None,'sha256':SOURCE_PIN},
        'references/keeper-config.json':{'bytes':5254,'sha256':CONFIG_PIN},'references/policy.json':{'bytes':None,'sha256':POLICY_PIN}})
    result.update({'package/'+name:row for name,row in PACKAGE_FILES.items()});need(len(result)==49);return result


def packet_files(packet):
    need(type(packet)is dict and set(packet)=={'schema','kind','files','desktop_proof_base64'}
        and type(packet['schema'])is int and packet['schema']==1 and packet['kind']=='popl-keeper-reconstruction-import','import_schema')
    expected=expected_files();need(type(packet['files'])is dict and set(packet['files'])==set(expected),'input_inventory')
    files={};total=0
    for name,row in packet['files'].items():
        need(type(row)is dict and set(row)=={'bytes','sha256','raw_base64'},'member_schema')
        raw=base64.b64decode(row['raw_base64'],validate=True);pin=expected[name]
        need(type(row['bytes'])is int and row['bytes']==len(raw)and 0<len(raw)<=1048576
            and sha(raw)==row['sha256']==pin['sha256']and(pin['bytes']is None or len(raw)==pin['bytes']),'member_pin')
        files[name]=raw;total+=len(raw);need(total<=1048576,'raw_kit_bound')
    return files


def owned():
    need(os.getuid()==0);item=LAB.lstat();need(stat.S_ISDIR(item.st_mode)and item.st_uid==0 and not item.st_mode&0o022)
    identity=decode(read(LAB/'LAB_ID.json',32768));need(identity['controller_sha256']==ACTIVE_CONTROLLER_SHA and identity['worker_sha256']==WORKER_SHA)
    need(sha(read(LAB/'worker.py',65536))==WORKER_SHA);return identity


def install(a):
    need(os.getuid()==0 and not os.path.lexists(LAB),'new_lab_only')
    need(all(properties(UNIT_BASE+'-'+mode+'.service').get('LoadState')=='not-found'for mode in MODES),'unit_exists')
    for digest in(a.desktop_proof_sha256,a.runtime_review_sha256):need(type(digest)is str and re.fullmatch('[0-9a-f]{64}',digest)is not None,'review_pin')
    compressed=sys.stdin.buffer.read(2097153);need(0<len(compressed)<=2097152,'compressed_wire_bound')
    inflater=zlib.decompressobj();raw=inflater.decompress(compressed,2097153)
    need(0<len(raw)<=2097152 and inflater.eof and not inflater.unconsumed_tail and not inflater.unused_data,'expanded_wire_bound')
    packet=decode(raw);files=packet_files(packet);proof_raw=base64.b64decode(packet['desktop_proof_base64'],validate=True)
    need(0<len(proof_raw)<=16384 and sha(proof_raw)==a.desktop_proof_sha256,'desktop_proof_pin');proof=decode(proof_raw)
    need(proof['schema']==1 and proof['kind']=='popl-unsigned-recovery-kit-review'and proof['ok']is True
        and proof['unsigned']is True and proof['readiness_approved']is False and proof['production_approved']is False,'desktop_proof_flags')
    need(proof['source_manifest_sha256']==SOURCE_PIN and proof['configuration_sha256']==CONFIG_PIN and proof['policy_sha256']==POLICY_PIN
        and proof['outer_manifest_sha256']==OUTER and proof['nested_manifest_sha256']==NESTED,'desktop_proof_trust')
    input_files={name:{'bytes':len(data),'sha256':sha(data)}for name,data in files.items()};need(proof['files']==input_files,'desktop_input_binding')
    before=original_snapshot();runtime=runtime_review();need(sha(enc(runtime))==a.runtime_review_sha256,'OS_runtime_review_changed')
    worker=base64.b64decode(WORKER,validate=True);need(sha(worker)==WORKER_SHA)
    LAB.mkdir(mode=0o700);write(LAB/'worker.py',worker)
    for mode in MODES:
        root=LAB/(mode+'-root');root.mkdir(mode=0o755);base=root/'reconstruction';base.mkdir(mode=0o755)
        write(base/'worker.py',worker);write(base/'SOURCE_MANIFEST.json',files['SOURCE_MANIFEST.json'])
        write(base/'RUNTIME_REVIEW.json',enc(runtime))
        identity={'schema':1,'input_files':input_files,'old_source_manifest_inode_pair':before['old_source_manifest_inode_pair'],
            'old_lock_inode_pairs':[row[:2]for row in before['old_lock_metadata']]}
        write(base/'IDENTITY.json',enc(identity))
        for name,data in files.items():
            if name.startswith('source/'):path=root/str(OLD).lstrip('/')/name
            elif name=='references/policy.json':path=root/str(OLD/'runtime/policy.json').lstrip('/')
            elif name=='references/keeper-config.json':
                if mode=='negative':continue
                path=root/str(OLD/'runtime/keeper-config.json').lstrip('/')
            elif name.startswith('package/'):path=base/name
            else:continue
            write(path,data)
        # Only layout prerequisites, never an original live state/lock/signer.
        configuration=decode(files['references/keeper-config.json']);policy=decode(files['references/policy.json'])
        need(policy['configuration']==str(OLD/'runtime/keeper-config.json')and policy['working_directory']==str(OLD/'runtime/working'),'original_logical_paths')
        for logical in[policy['working_directory'],*map(lambda key:str(Path(policy[key]).parent),('scheduler_directory','backup_directory','alert_directory'))]:
            need(Path(logical).is_relative_to(OLD),'layout_scope');(root/logical.lstrip('/')).mkdir(parents=True,exist_ok=True,mode=0o755)
        working=root/policy['working_directory'].lstrip('/');os.chown(working,65534,65534);os.chmod(working,0o700)
        for key in('keystore','password_file'):
            need(Path(configuration[key]).is_relative_to(OLD/'runtime/working'),'fixture_signer_path')
            need(not os.path.lexists(root/configuration[key].lstrip('/')),'signer_material_present')
        runtime_dir=base/'runtime';runtime_dir.mkdir(mode=0o700);os.chown(runtime_dir,65534,65534)
        for name in('stdout.log','stderr.log'):write(runtime_dir/name,b'',0o600,65534)
        for mount in runtime['mounts']:
            target=root/mount['target'].lstrip('/');target.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
            if Path(mount['source']).is_dir():target.mkdir(mode=0o755)
            else:write(target,b'',0o444)
    after=original_snapshot();need(unchanged(before,after),'original_changed')
    write(LAB/'INSTALL.json',enc({'schema':1,'original_before':before,'original_after_snapshot_sha256':sha(enc(after)),'original_unchanged':True,
        'input_files':input_files,'desktop_proof_sha256':a.desktop_proof_sha256,'runtime_review_sha256':a.runtime_review_sha256,
        'runtime_mounts':runtime['mounts'],'compressed_wire_bytes':len(compressed),'expanded_wire_bytes':len(raw),
        'outer_private_directory_uid':LAB.lstat().st_uid,'outer_private_directory_mode':stat.S_IMODE(LAB.lstat().st_mode),
        'source_fallback':False,'configuration_or_policy_rewritten':False,'original_host_opt_bound':False}),0o600)
    write(LAB/'LAB_ID.json',enc({'schema':1,'controller_sha256':ACTIVE_CONTROLLER_SHA,'worker_sha256':WORKER_SHA,
        'desktop_proof_sha256':a.desktop_proof_sha256,'runtime_review_sha256':a.runtime_review_sha256}),0o600)
    return{'phase':'installed','input_file_count':49,'compressed_wire_bytes':len(compressed),'expanded_wire_bytes':len(raw),
        'desktop_proof_sha256':a.desktop_proof_sha256,'runtime_review_sha256':a.runtime_review_sha256,
        'original_unchanged':True,'root_directories_created':2,'original_host_opt_bound':False}


def start(a):
    identity=owned();mode=a.mode;unit=UNIT_BASE+'-'+mode+'.service';root=LAB/(mode+'-root')
    need(mode in MODES and not(LAB/('START-'+mode+'.json')).exists()and properties(unit).get('LoadState')=='not-found','no_restart_or_rerun')
    if mode=='complete':
        negative=decode(read(LAB/'negative-root/reconstruction/runtime/RESULT.json',32768,65534))
        need(negative['success']is True and negative['native_refusal_before_restore']is True,'negative_required_first')
        prior=properties(UNIT_BASE+'-negative.service');need(empty(UNIT_BASE+'-negative.service',prior),'negative_not_settled')
    before=original_snapshot();runtime=runtime_review();need(sha(enc(runtime))==identity['runtime_review_sha256'],'runtime_changed')
    binds=' '.join(row['source']+':'+row['target']for row in runtime['mounts'])
    policy={'Type':'oneshot','User':'nobody','Group':'nogroup','RootDirectory':str(root),'MountAPIVFS':'yes',
        'PrivateNetwork':'yes','PrivateTmp':'yes','PrivateDevices':'yes','ProtectSystem':'strict','ProtectHome':'yes',
        'ProtectProc':'invisible','ProcSubset':'pid',
        'NoNewPrivileges':'yes','ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectControlGroups':'yes',
        'RestrictSUIDSGID':'yes','LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
        'RestrictAddressFamilies':'AF_UNIX','ReadWritePaths':'+/reconstruction/runtime','UMask':'0077','Restart':'no',
        'RemainAfterExit':'yes','TimeoutStartSec':'180','TimeoutStopSec':'2','KillMode':'control-group','SendSIGKILL':'yes',
        'FinalKillSignal':'SIGKILL','MemoryMax':'256M','MemorySwapMax':'0','TasksMax':'32','LimitCORE':'0',
        'LimitFSIZE':'65536','StartLimitIntervalSec':'0','BindReadOnlyPaths':binds,
        'StandardOutput':'append:'+str(root/'reconstruction/runtime/stdout.log'),
        'StandardError':'append:'+str(root/'reconstruction/runtime/stderr.log'),'WorkingDirectory':'/reconstruction'}
    argv=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+unit]
    argv+=['--property='+key+'='+item for key,item in policy.items()]
    argv+=['--setenv='+key+'='+item for key,item in{'PATH':'/usr/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}.items()]
    code,_,_=run([*argv,'--','/usr/bin/python3','-I','-S','-B','/reconstruction/worker.py',mode]);need(code==0,'unit_start_refused')
    write(LAB/('START-'+mode+'.json'),enc({'schema':1,'original_before':before,'policy':policy,'only_new_unit_started':unit}),0o600)
    return{'phase':'started','mode':mode,'unit':unit,'properties':properties(unit)}


def status(a):
    owned();result={}
    for mode in MODES:
        unit=UNIT_BASE+'-'+mode+'.service';props=properties(unit);folder=LAB/(mode+'-root')/'reconstruction/runtime'
        sizes={name:(folder/name).stat().st_size for name in('stdout.log','stderr.log')};need(sum(sizes.values())<=65536,'unit_output_bound')
        result[mode]={'properties':props,'group_empty':empty(unit,props),'result_present':(folder/'RESULT.json').exists(),'output_bytes':sizes}
    return{'phase':'status','units':result}


def stop(a):
    owned();states={}
    for mode in MODES:
        unit=UNIT_BASE+'-'+mode+'.service';before=properties(unit)
        if before.get('LoadState')!='not-found':code,_,_=run(['/usr/bin/systemctl','stop',unit]);need(code==0)
        after=properties(unit);need(empty(unit,after),'group_not_empty');states[mode]={'before_stop':before,'after_stop':after,'group_empty':True}
    original=original_snapshot();installed=decode(read(LAB/'INSTALL.json',32768));need(unchanged(installed['original_before'],original),'original_changed')
    if not(LAB/'FINAL.json').exists():write(LAB/'FINAL.json',enc({'schema':1,'units':states,'new_groups_empty':True,
        'original_after':original,'original_unchanged':True,'old_four_groups_fenced':True}),0o600)
    return{'phase':'stopped','new_groups_empty':True,'original_unchanged':True,'old_four_groups_fenced':True}


def fetch(a):
    owned();need(a.artifact in('RESULT-negative.json','RESULT-complete.json','INSTALL.json','FINAL.json'))
    if a.artifact.startswith('RESULT-'):path=LAB/(a.artifact[7:-5]+'-root')/'reconstruction/runtime/RESULT.json';owner=65534
    else:path=LAB/a.artifact;owner=0
    raw=read(path,32768,owner);return{'name':a.artifact,'bytes':len(raw),'sha256':sha(raw),'base64':base64.b64encode(raw).decode('ascii')}


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('export','install','start','status','stop','fetch'))
    p.add_argument('--controller-sha256',required=True);p.add_argument('--desktop-proof-sha256');p.add_argument('--runtime-review-sha256')
    p.add_argument('--mode',choices=MODES);p.add_argument('--artifact');a=p.parse_args()
    need(re.fullmatch('[0-9a-f]{64}',a.controller_sha256)is not None);globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256
    print(json.dumps(globals()[a.action](a),sort_keys=True))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        code=str(exc)if type(exc)is ValueError and re.fullmatch('[a-z_]{1,64}',str(exc))is not None else None
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'refusal_code':code,'scope':'fixed_c825_only'}));raise SystemExit(1)from None
