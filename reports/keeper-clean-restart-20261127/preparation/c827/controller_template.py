"""Fixed c827 controls. Original host services, journals and source labs are untouched."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,math,os,re,selectors,signal,stat,subprocess,sys,time,zlib

LAB=Path('/opt/popl-keeper-clean-restart-20261127-c827')
LOGICAL=Path('/run/popl-keeper-clean-restart-20261127-c827')
BASE='popl-keeper-clean-restart-20261127-c827'
OLD=Path('/opt/popl-ubuntu-backup-recovery-20261126-c814')
FIXTURE=OLD/'inputs'
SOURCE_PIN='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
SOURCE_FILES=__SOURCE_PINS__
HELPERS=__HELPER_PINS__
TOOLS={'anvil':('/opt/popl-history-export-20261124-c7eb/tools/anvil','05ee0cf1758024ea5e23dae562d92955ace205ab299091a43d2fa5bdeb6933bd'),
    'cast':('/opt/popl-ubuntu-20261121-8a629f43/bin/cast','d55f540256f0dd8b940a125d435919948a5e8c140262e9923067cbfa95ef2970')}
INPUTS={'restore-state.json':(13643211,'42ab11fd14bd02868359fb3fdd84e961f3f8050245f0cb370d1962be823d9b9a'),
    'instances.json':(4845414,'e94a9dc5d4f3f04211ad77e62612b2284301584c3e363203198311d34d128e56'),
    'entry-receipts.json':(696971,'425902fae92cdbb210f3a12afc80908b9bd186ec1ae80060c427d9f302f3c519')}
ROLES=('node','gateway','bootstrap','initialize','source','capture','target','final','fresh')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def need(value,code='fixed_c827_refused'):
    if not value:raise ValueError(code)


def decode(raw):
    def pairs(rows):
        result={}
        for key,item in rows:need(key not in result,'duplicate_JSON_key');result[key]=item
        return result
    def invalid(_):raise ValueError('nonfinite_JSON')
    def number(raw):
        item=float(raw);need(math.isfinite(item),'nonfinite_JSON');return item
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid,parse_float=number)


def read(path,maximum=2097152,owners=(0,65534)):
    before=path.lstat();need(stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_uid in owners
        and not before.st_mode&0o022 and before.st_size<=maximum,'file_metadata')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        raw=bytearray()
        while True:
            part=os.read(fd,min(65536,maximum+1-len(raw)))
            if not part:break
            raw.extend(part);need(len(raw)<=maximum,'file_bound')
        key=lambda item:(item.st_dev,item.st_ino,item.st_uid,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns)
        need(key(before)==key(os.fstat(fd))==key(path.lstat())and len(raw)==before.st_size,'file_changed');return bytes(raw)
    finally:os.close(fd)


def write(path,raw,mode=0o600,owner=0):
    need(len(raw)<=134217728,'write_bound');path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno());os.fchown(stream.fileno(),owner,owner);os.fchmod(stream.fileno(),mode)


def run(argv,seconds=30):
    child=owned=None;parts=[bytearray(),bytearray()];size=0;end=time.monotonic()+seconds
    try:
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'},start_new_session=True,close_fds=True);owned=child
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<end,'control_deadline')
                for selected,_ in selector.select(min(.1,max(.001,end-time.monotonic()))):
                    raw=os.read(selected.fd,min(16384,65537-size))
                    if not raw:selector.unregister(selected.fileobj);continue
                    size+=len(raw);need(size<=65536,'control_output_bound');parts[selected.data].extend(raw)
        code=child.wait(timeout=max(.001,end-time.monotonic()));owned=None;return code,bytes(parts[0]),bytes(parts[1])
    finally:
        try:
            if owned is not None:
                if owned.poll()is None:
                    try:os.killpg(owned.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                owned.wait(timeout=2)
        finally:
            if child is not None:child.stdout.close();child.stderr.close()


def unit(role):need(role in ROLES);return BASE+'-'+role+'.service'


def props(role):
    code,out,_=run(['/usr/bin/systemctl','show',unit(role),'--no-pager','--property=Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,Restart,User,Group,PrivateNetwork,JoinsNamespaceOf,RootDirectory,BindPaths,BindReadOnlyPaths,ReadWritePaths,ExecSearchPath,InvocationID'])
    result=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and result.get('LoadState')=='not-found','unit_properties');return result


def empty(role,p):
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group=='/system.slice/'+unit(role),'group_scope')
    path=Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs'
    try:raw=path.read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096,'group_bound');return not raw.strip()


def module(name):
    path=LAB/'helpers'/name;need(sha(read(path,65536))==HELPERS[name]['sha256'],'helper_pin')
    spec=importlib.util.spec_from_file_location('fixed_c827_runtime',path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def owned():
    need(os.getuid()==0 and LAB.lstat().st_uid==0 and stat.S_IMODE(LAB.lstat().st_mode)==0o700,'private_lab')
    identity=decode(read(LAB/'LAB_ID.json',65536));need(identity['controller_sha256']==ACTIVE_CONTROLLER_SHA,'controller_identity')
    for name,row in HELPERS.items():need(sha(read(LAB/'helpers'/name,65536))==row['sha256'],'helper_pin')
    for name,row in SOURCE_FILES.items():need(sha(read(LAB/'source'/name))==row['sha256'],'source_pin')
    need(sha(read(LAB/'SOURCE_MANIFEST.json'))==SOURCE_PIN,'source_manifest');return identity


def packet():
    compressed=sys.stdin.buffer.read(2097153);need(0<len(compressed)<=2097152,'compressed_input')
    stream=zlib.decompressobj();raw=stream.decompress(compressed,2097153)
    need(0<len(raw)<=2097152 and stream.eof and not stream.unconsumed_tail and not stream.unused_data,'expanded_input')
    result=decode(raw);need(type(result)is dict and result['schema']==1 and type(result['files'])is dict,'packet_schema')
    files={};total=0
    for name,row in result['files'].items():
        need(type(name)is str and not name.startswith('/')and'..'not in Path(name).parts and'\\'not in name,'packet_path')
        data=base64.b64decode(row['raw_base64'],validate=True);need(len(data)==row['bytes']and sha(data)==row['sha256'],'packet_member')
        total+=len(data);need(total<=1048576,'packet_total');files[name]=data
    return result,files


def fixture_snapshot():
    result={}
    selected={str(FIXTURE/name):(size,digest)for name,(size,digest)in INPUTS.items()}
    selected.update({path:(None,digest)for path,digest in TOOLS.values()})
    for name,(size,digest)in selected.items():
        path=Path(name);raw=read(path,134217728);item=path.lstat()
        need(sha(raw)==digest and(size is None or len(raw)==size),'immutable_fixture_pin')
        result[name]={'bytes':len(raw),'sha256':digest,'metadata':[item.st_dev,item.st_ino,item.st_uid,
            item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns]}
    return result


def prepare(a):
    need(os.getuid()==0 and not os.path.lexists(LAB)and all(props(role).get('LoadState')=='not-found'for role in ROLES),'fresh_lab')
    message,files=packet();expected={'SOURCE_MANIFEST.json',*('source/'+name for name in SOURCE_FILES),*('helpers/'+name for name in HELPERS)}
    need(message['kind']=='c827-preparation'and set(files)==expected,'preparation_inventory')
    need(sha(files['SOURCE_MANIFEST.json'])==SOURCE_PIN,'source_manifest')
    for name,row in SOURCE_FILES.items():need(len(files['source/'+name])==row['bytes']and sha(files['source/'+name])==row['sha256'],'source_pin')
    for name,row in HELPERS.items():need(len(files['helpers/'+name])==row['bytes']and sha(files['helpers/'+name])==row['sha256'],'helper_pin')
    LAB.mkdir(mode=0o700)
    need(not os.path.lexists(LOGICAL),'new_logical_mount_root')
    LOGICAL.mkdir(mode=0o755)
    for name in('source','helpers','actor','evidence','shared','node','tmp','empty-home','tools','inputs','control','witness'):
        (LOGICAL/name).mkdir(mode=0o755)
    for name,data in files.items():write(LAB/name,data,0o444)
    for name in('actor','evidence','shared','node','tmp','empty-home','witness'):
        path=LAB/name;path.mkdir(mode=0o700);os.chown(path,65534,65534)
    (LAB/'control').mkdir(mode=0o755)
    write(LAB/'shared/budget.lock',b'',0o600,65534)
    # The 900s work clock begins with start-node, never during preparation/review.
    fixture_data={}
    for name,(size,digest)in INPUTS.items():
        raw=read(FIXTURE/name,16777216);need(len(raw)==size and sha(raw)==digest,'immutable_fixture')
        if name!='restore-state.json':fixture_data[name]=decode(raw)
    rows=fixture_data['instances.json'];roles={row['role']:{key:row[key]for key in('address','runtime_keccak256')}for row in rows}
    feeds={row['label'].split(':')[1]:row['receipt']['contractAddress'].lower()for row in fixture_data['entry-receipts.json']if row['label'].startswith('helper:')and'feed_'in row['label']}
    need(len(roles)==39 and set(feeds)=={'eth_feed_a','eth_feed_b','zzz_feed_a','zzz_feed_b'},'fixture_metadata')
    write(LAB/'fixture.json',enc({'schema':1,'roles':roles,'feeds':feeds}),0o444)
    for name,(path,digest)in TOOLS.items():need(sha(read(Path(path),134217728))==digest,'fixture_tool')
    write(LAB/'FIXTURE_PRESERVATION.json',enc(fixture_snapshot()),0o600)
    runtime=module('runtime_support.py').runtime_review()
    write(LAB/'RUNTIME_REVIEW.json',enc(runtime),0o600)
    write(LAB/'LAB_ID.json',enc({'schema':1,'controller_sha256':ACTIVE_CONTROLLER_SHA,'runtime_review_sha256':sha(enc(runtime)),
        'source_manifest_sha256':SOURCE_PIN,'private_outer_mode':448,'source_from_desktop':True}),0o600)
    return{'prepared':True,'controller_sha256':ACTIVE_CONTROLLER_SHA,'runtime_review':runtime,'runtime_review_sha256':sha(enc(runtime)),
        'initial_source_files':41,'fixture_reused_read_only':True,'source_body_read_from_old_host_lab':False}


def common(role):
    policy={'Type':'oneshot','User':'nobody','Group':'nogroup','PrivateNetwork':'yes','PrivateTmp':'yes','PrivateDevices':'yes',
        'ProtectSystem':'strict','ProtectHome':'yes','ProtectProc':'invisible','ProcSubset':'pid','NoNewPrivileges':'yes',
        'ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectControlGroups':'yes','RestrictSUIDSGID':'yes',
        'LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'','RestrictAddressFamilies':'AF_UNIX AF_INET',
        'UMask':'0077','Restart':'no','RemainAfterExit':'yes','TimeoutStartSec':'180','TimeoutStopSec':'2','KillMode':'control-group',
        'SendSIGKILL':'yes','FinalKillSignal':'SIGKILL','MemoryMax':'768M'if role=='node'else'256M','MemorySwapMax':'0','TasksMax':'32',
        'LimitCORE':'0','LimitFSIZE':'65536','StartLimitIntervalSec':'0',
        'UnsetEnvironment':'PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONINSPECT PYTHONUSERBASE'}
    if role in('node','gateway'):policy['RuntimeMaxSec']='900'
    if role not in('node',):policy.update(JoinsNamespaceOf=unit('node'),Requires=unit('node'),After=unit('node'))
    return policy


def launch(role,argv,policy,env=None):
    need(props(role).get('LoadState')=='not-found'and not(LAB/('START-'+role+'.json')).exists()
        and not(LAB/('ATTEMPT-'+role+'.json')).exists(),'no_unit_restart')
    for suffix in('stdout','stderr'):write(LAB/'evidence'/(role+'.'+suffix),b'',0o600,65534)
    policy.update(StandardOutput='append:'+str(LAB/'evidence'/(role+'.stdout')),StandardError='append:'+str(LAB/'evidence'/(role+'.stderr')))
    command=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+unit(role)]
    command+=['--property='+key+'='+value for key,value in policy.items()]
    environment=env or{'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}
    if role!='node':
        node=props('node');need(node.get('ActiveState')=='active'and int(node.get('MainPID','0'))>1,'retained_node_active')
        environment=dict(environment,POPL_C826_NODE_PID=node['MainPID'],
            POPL_C826_NODE_CGROUP=node['ControlGroup'],POPL_C826_HOST_NET_NS=os.readlink('/proc/self/ns/net'))
    command+=['--setenv='+key+'='+value for key,value in environment.items()]
    write(LAB/('ATTEMPT-'+role+'.json'),enc({'schema':1,'role':role,'argv':argv,'policy':policy,
        'no_replay_after_client_interruption_or_failure':True}),0o600)
    code,client_out,client_err=run([*command,'--',*argv])
    write(LAB/'launch'/(role+'.stdout'),client_out,0o600)
    write(LAB/'launch'/(role+'.stderr'),client_err,0o600)
    write(LAB/('LAUNCH-'+role+'.json'),enc({'schema':1,'role':role,'returncode':code,
        'stdout_bytes':len(client_out),'stdout_sha256':sha(client_out),
        'stderr_bytes':len(client_err),'stderr_sha256':sha(client_err),
        'argv':argv,'policy':policy,'client_output_preserved_before_success_guard':True}),0o600)
    need(code==0,'native_launch')
    write(LAB/('START-'+role+'.json'),enc({'schema':1,'role':role,'argv':argv,'policy':policy}),0o600)
    return{'started':role,'properties':props(role)}


def mapped(policy,*,write_actor=False):
    readonly=[str(LAB/'source')+':'+str(LOGICAL/'source'),str(LAB/'helpers')+':'+str(LOGICAL/'helpers'),
        str(LAB/'fixture.json')+':'+str(LOGICAL/'fixture.json'),str(LAB/'control')+':'+str(LOGICAL/'control')]
    if not write_actor:readonly.append(str(LAB/'actor')+':'+str(LOGICAL/'actor'))
    writebinds=[str(LAB/name)+':'+str(LOGICAL/name)for name in('evidence','shared','tmp','empty-home')]
    if write_actor:writebinds.append(str(LAB/'actor')+':'+str(LOGICAL/'actor'))
    readonly.extend(path+':'+str(LOGICAL/'tools'/name)for name,(path,_)in TOOLS.items())
    policy.update(BindReadOnlyPaths=' '.join(readonly),BindPaths=' '.join(writebinds),
        ReadWritePaths=' '.join(str(LOGICAL/name)for name in('evidence','shared','tmp','empty-home',*(('actor',)if write_actor else()))),
        WorkingDirectory=str(LOGICAL/'source'))
    return policy


def start_node(a):
    owned();need(not(LAB/'shared/BUDGET.json').exists(),'one_budget')
    write(LAB/'shared/BUDGET.json',enc({'schema':1,'started_monotonic':time.monotonic(),'RPC_requests':0,
        'raw_attempts':0,'raw_forwarded':0,'transaction_method_attempts':0,'accepted_hash':None,'accepted_transaction_verified':False}),0o600,65534)
    policy=common('node');policy.update(Type='exec',RemainAfterExit='no',TimeoutStartSec='30',LimitFSIZE='65536',
        ExecSearchPath=str(LOGICAL/'tools'),
        BindReadOnlyPaths=TOOLS['anvil'][0]+':'+str(LOGICAL/'tools/anvil')+' '+str(FIXTURE/'restore-state.json')+':'+str(LOGICAL/'inputs/restore-state.json'),
        BindPaths=str(LAB/'node')+':'+str(LOGICAL/'node'),ReadWritePaths=str(LOGICAL/'node'),WorkingDirectory=str(LOGICAL/'node'))
    argv=[str(LOGICAL/'tools/anvil'),'--host','127.0.0.1','--port','19626','--accounts','0','--silent','--chain-id','4663',
        '--hardfork','cancun','--gas-limit','32000000','--gas-price','1000000000','--block-base-fee-per-gas','1',
        '--load-state',str(LOGICAL/'inputs/restore-state.json')]
    return launch('node',argv,policy)


def action(a):
    owned();role=a.action
    if role=='gateway':
        return launch(role,['/usr/bin/python3','-S','-B',str(LOGICAL/'helpers/gateway.py')],mapped({**common(role),'Type':'exec','RemainAfterExit':'no'}))
    if role in('bootstrap','capture','final','fresh'):
        if role=='final':
            target_props=props('target');result_path=LAB/'target-root'/str(LOGICAL).lstrip('/')/'witness/RESULT.json'
            need(target_props.get('ExecMainCode')=='1'and target_props.get('ExecMainStatus')=='0'
                and empty('target',target_props)and decode(read(result_path,32768))['success']is True,'successful_target_before_final')
        selected={'bootstrap':'bootstrap','capture':'capture-include','final':'final','fresh':'fresh-head'}[role]
        return launch(role,['/usr/bin/python3','-S','-B',str(LOGICAL/'helpers/driver.py'),selected],mapped(common(role),write_actor=role=='bootstrap'))
    if role in('initialize','source'):
        argv=['/usr/bin/python3','-S','-B','-m','keeper.monitor','--config',str(LOGICAL/'actor/config.json')]
        argv+=['--initialize-state']if role=='initialize'else['--once','--live']
        if role=='source':
            initial=props('initialize')
            need((LAB/'actor/state.json').exists()and initial.get('ExecMainCode')=='1'and initial.get('ExecMainStatus')=='0'
                and empty('initialize',initial),'initialized_source')
        return launch(role,argv,mapped(common(role),write_actor=True))
    raise ValueError('closed_action')


def fence(a):
    owned();before=props('source');need(before.get('LoadState')!='not-found'and empty('source',before)
        and before.get('ExecMainCode')=='1'and before.get('ExecMainStatus')=='0','source_once_completed')
    code,_,_=run(['/usr/bin/systemctl','stop',unit('source')]);need(code==0,'source_stop')
    after=props('source');need(empty('source',after)and after.get('Restart')=='no','source_group_empty')
    jobs,out,_=run(['/usr/bin/systemctl','list-jobs','--no-legend','--no-pager']);need(jobs==0 and unit('source').encode()not in out,'source_restart_fenced')
    raw=read(LAB/'actor/state.json');state=decode(raw);need(type(state['pending'])is dict and state['pending']['hash'],'source_known_hash')
    write(LAB/'control/SOURCE_FENCED.json',enc({'schema':1,'source_group_empty':True,'restart_inhibited':True,
        'source_journal_sha256':sha(raw),'accepted_hash':state['pending']['hash'],'source_after':after}),0o444)
    # Capture and include automatically in one dispatch, before the 180s TTL.
    return action(argparse.Namespace(action='capture'))


def export(a):
    owned();need(empty('source',props('source'))and(LAB/'evidence/INCLUDED.json').exists(),'included_fenced_source')
    files={}
    for name,path in(('CONFIG.json',LAB/'evidence/ORIGINAL_CONFIG.json'),('bundle/manifest.json',LAB/'evidence/bundle/manifest.json'),('bundle/journal.json',LAB/'evidence/bundle/journal.json')):
        raw=read(path,65536);files[name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    return{'schema':1,'kind':'c827-private-native-capture','files':files,'INCLUDED':decode(read(LAB/'evidence/INCLUDED.json')),
        'raw_records_private':True,'source_release_exported':False,'signer_material_exported':False}


def install_target(a):
    identity=owned();need(not os.path.lexists(LAB/'target-root')and props('target').get('LoadState')=='not-found','fresh_target_root')
    need(type(a.proof_sha256)is str and re.fullmatch('[0-9a-f]{64}',a.proof_sha256)is not None,'desktop_proof_pin')
    need(a.runtime_sha256==identity['runtime_review_sha256'],'external_runtime_review_pin')
    message,files=packet();expected={'SOURCE_MANIFEST.json','CONFIG.json','bundle/manifest.json','bundle/journal.json',
        *('source/'+name for name in SOURCE_FILES)}
    need(message['kind']=='c827-desktop-recovery-kit'and set(files)==expected and len(files)==45,'target_kit_inventory')
    proof_raw=base64.b64decode(message['proof_base64'],validate=True)
    need(0<len(proof_raw)<=16384 and sha(proof_raw)==a.proof_sha256,'desktop_proof_pin')
    proof=decode(proof_raw);filepins={name:{'bytes':len(raw),'sha256':sha(raw)}for name,raw in files.items()}
    need(proof['schema']==1 and proof['unsigned']is True and proof['readiness_approved']is False
        and proof['production_approved']is False and proof['files']==filepins,'desktop_proof_binding')
    need(sha(files['SOURCE_MANIFEST.json'])==SOURCE_PIN,'target_source_manifest')
    for name,row in SOURCE_FILES.items():
        need(len(files['source/'+name])==row['bytes']and sha(files['source/'+name])==row['sha256'],'target_desktop_source')
    captured=decode(read(LAB/'evidence/INCLUDED.json'))
    need(sha(files['CONFIG.json'])==captured['configuration_sha256']
        and sha(files['bundle/manifest.json'])==captured['backup_manifest_sha256']
        and sha(files['bundle/journal.json'])==captured['pending_journal_sha256'],'source_capture_trust')
    runtime=module('runtime_support.py').runtime_review()
    need(sha(enc(runtime))==a.runtime_sha256,'runtime_changed')
    root=LAB/'target-root';root.mkdir(mode=0o755);logical=root/str(LOGICAL).lstrip('/');logical.mkdir(parents=True,mode=0o755)
    for name,raw in files.items():
        destination=logical/name
        if name=='CONFIG.json':destination=logical/'actor/config.json'
        write(destination,raw,0o444)
    (logical/'actor').chmod(0o700);os.chown(logical/'actor',65534,65534)
    write(logical/'actor/state.json',files['bundle/journal.json'],0o600,65534)
    for name in('witness','tmp','empty-home'):
        (logical/name).mkdir(mode=0o700);os.chown(logical/name,65534,65534)
    (logical/'shared').mkdir(mode=0o755)
    for name in('target_worker.py','shared.py','runtime_support.py'):write(logical/'helpers'/name,read(LAB/'helpers'/name,65536),0o444)
    manifest=decode(files['bundle/manifest.json'])
    selected={'SOURCE_MANIFEST.json':('SOURCE_MANIFEST.json','SOURCE_MANIFEST.json'),
        'source/keeper/monitor.py':('source/keeper/monitor.py','source/keeper/monitor.py'),
        'actor/config.json':('actor/config.json','actor/config.json'),'actor/state.json':('actor/state.json','actor/state.json')}
    inode_pair=lambda path:[path.lstat().st_dev,path.lstat().st_ino]
    target_pairs={key:inode_pair(logical/target_path)for key,(_,target_path)in selected.items()}
    original_pairs={key:inode_pair(LAB/original_path)for key,(original_path,_)in selected.items()}
    need(all(target_pairs[key]!=original_pairs[key]for key in selected),'target_input_inodes_new')
    target_identity={'schema':1,'kind':'popl-clean-restart-target-identity','configuration_sha256':captured['configuration_sha256'],
        'pending_journal_sha256':captured['pending_journal_sha256'],'journal_manifest_sha256':captured['backup_manifest_sha256'],
        'source_manifest_sha256':SOURCE_PIN,'desktop_proof_sha256':a.proof_sha256,
        'accepted_hash':captured['accepted_hash'],'next_nonce':0,'created_at':manifest['created_at'],'review_max_age_seconds':900,
        'runtime_review_sha256':a.runtime_sha256,'target_root_inode_pair':inode_pair(root),'target_host_root':str(root),
        'target_input_inode_pairs':target_pairs,'original_input_inode_pairs':original_pairs}
    write(logical/'TARGET_IDENTITY.json',enc(target_identity),0o444)
    write(logical/'RUNTIME_REVIEW.json',enc(runtime),0o444)
    for row in runtime['mounts']:
        destination=root/row['target'].lstrip('/');destination.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
        if Path(row['source']).is_dir():destination.mkdir(mode=0o755)
        else:write(destination,b'',0o444)
    config=decode(files['CONFIG.json'])
    need(config['state_path']==str(LOGICAL/'actor/state.json')and config['rpc_urls']==['http://127.0.0.1:19627']
        and config['interval_seconds']==240 and config['confirmations']==12 and config['max_gas_limit']==24000000
        and config['maintenance']['harvest_interval_seconds']==3600,'unchanged_target_configuration')
    need(not(logical/'actor/secrets').exists()and not(logical/'tools').exists(),'target_signer_and_Cast_absent')
    report={'schema':1,'files':filepins,'desktop_proof_sha256':a.proof_sha256,'runtime_review_sha256':a.runtime_sha256,
        'root_directory':str(root),'application_files_from_desktop_kit_only':True,'source_application_fallback':False,
        'original_configuration_rewritten':False,'source_journal_unchanged':sha(read(LAB/'actor/state.json'))==captured['pending_journal_sha256'],
        'signer_and_Cast_absent':True,'readiness_approved':False,'production_approved':False}
    need(report['source_journal_unchanged'],'source_journal_changed')
    write(LAB/'TARGET_INSTALL.json',enc(report),0o600)
    return{'target_installed':True,'file_count':45,'desktop_proof_sha256':a.proof_sha256,
        'application_files_from_desktop_kit_only':True,'signer_and_Cast_absent':True}


def target(a):
    identity=owned();need((LAB/'TARGET_INSTALL.json').exists(),'desktop_target_required')
    root=LAB/'target-root';logical=root/str(LOGICAL).lstrip('/')
    target_identity=decode(read(logical/'TARGET_IDENTITY.json'))
    need(sha(read(logical/'actor/state.json'))==target_identity['pending_journal_sha256'],'target_pending_exists_exact')
    runtime=module('runtime_support.py').runtime_review();need(sha(enc(runtime))==identity['runtime_review_sha256'],'target_runtime_changed')
    policy=common('target')
    policy.update(RootDirectory=str(root),MountAPIVFS='yes',WorkingDirectory=str(LOGICAL/'source'),
        BindReadOnlyPaths=' '.join(row['source']+':'+row['target']for row in runtime['mounts']),
        BindPaths=str(LAB/'shared')+':'+str(LOGICAL/'shared'),
        ReadWritePaths=' '.join('+'+str(LOGICAL/name)for name in('actor','witness','shared','tmp','empty-home')))
    return launch('target',['/usr/bin/python3','-S','-B',str(LOGICAL/'helpers/target_worker.py')],policy)


def status(a):
    owned();result={}
    for role in ROLES:
        p=props(role);result[role]={'properties':p,'group_empty':empty(role,p)}
    return{'units':result,'capture_complete':(LAB/'evidence/INCLUDED.json').exists(),
        'target_result_present':(LAB/'target-root'/str(LOGICAL).lstrip('/')/'witness/RESULT.json').exists(),
        'budget':decode(read(LAB/'shared/BUDGET.json',65536))if(LAB/'shared/BUDGET.json').exists()else None}


def stop(a):
    owned();result={}
    # Node stops last; independent final physical reads must precede this action.
    for role in('target','source','initialize','capture','bootstrap','final','fresh','gateway','node'):
        p=props(role)
        if p.get('LoadState')!='not-found':code,_,_=run(['/usr/bin/systemctl','stop',unit(role)]);need(code==0,'new_unit_stop')
        p=props(role);need(empty(role,p),'new_group_not_empty');result[role]=p
    preserved=fixture_snapshot();unchanged=preserved==decode(read(LAB/'FIXTURE_PRESERVATION.json',65536))
    need(unchanged,'old_immutable_fixture_changed')
    if not(LAB/'FINAL_STOP.json').exists():write(LAB/'FINAL_STOP.json',enc({'schema':1,'all_new_groups_empty':True,'units':result,
        'final_physical_capture_present':(LAB/'evidence/FINAL_CHAIN.json').exists(),'old_immutable_fixture_unchanged':True,
        'old_fixture_snapshot_sha256':sha(enc(preserved))}),0o600)
    return{'all_new_groups_empty':True,'units':result,'old_immutable_fixture_unchanged':True}


def fetch(a):
    owned();allowed={'BOOTSTRAP.json','FINANCIAL_INITIAL.json','FINANCIAL_INCLUDED.json','CANONICAL.json','INCLUDED.json',
        'FINANCIAL_FINAL.json','FINAL_CHAIN.json','FINAL_STOP.json','TARGET_INSTALL.json','TARGET_RESULT.json','RUNTIME_REVIEW.json'}
    allowed.update(role+'.'+kind for role in ROLES for kind in('stdout','stderr'))
    allowed.update('launch-'+role+'.'+kind for role in ROLES for kind in('stdout','stderr'))
    allowed.update('LAUNCH-'+role+'.json'for role in ROLES)
    allowed.add('TARGET_PRIVATE.zlib')
    need(a.artifact in allowed,'artifact_allowlist')
    if a.artifact=='TARGET_PRIVATE.zlib':
        state=props('target');logical=LAB/'target-root'/str(LOGICAL).lstrip('/')
        need(empty('target',state)and state.get('ExecMainCode')=='1'and state.get('ExecMainStatus')=='0'
            and decode(read(logical/'witness/RESULT.json',32768))['success']is True,'target_fenced_before_private_fetch')
        wanted={'STATE-BEFORE.json':'witness/STATE-BEFORE.json','STATE-SETTLED.json':'witness/STATE-SETTLED.json',
            'STATE-DRY.json':'witness/STATE-DRY.json','HEALTH-RECOVERY.json':'witness/HEALTH-RECOVERY.json',
            'HEALTH-DRY.json':'witness/HEALTH-DRY.json','RESTORE_PLAN.json':'witness/native-restored/RESTORE_PLAN.json',
            'TARGET_IDENTITY.json':'TARGET_IDENTITY.json','CONFIG.json':'actor/config.json'}
        files={}
        for name,relative in wanted.items():
            data=read(logical/relative,32768);files[name]={'bytes':len(data),'sha256':sha(data),'raw_base64':base64.b64encode(data).decode('ascii')}
        captured=decode(read(LAB/'evidence/INCLUDED.json'))
        need(sha(read(LAB/'actor/config.json'))==captured['configuration_sha256']
            and sha(read(LAB/'actor/state.json'))==captured['pending_journal_sha256'],'source_inputs_preserved')
        packet=enc({'schema':1,'kind':'c827-private-target-records','files':files,
            'source_configuration_and_journal_unchanged':True,'raw_records_must_remain_private':True})
        need(len(packet)<=131072,'private_packet_bound');raw=zlib.compress(packet,9);need(len(raw)<=32768,'private_compressed_bound')
        return{'name':a.artifact,'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    if a.artifact.startswith('launch-'):
        path=LAB/'launch'/a.artifact[len('launch-'):]
    elif a.artifact.startswith('LAUNCH-'):path=LAB/a.artifact
    elif a.artifact=='TARGET_RESULT.json':path=LAB/'target-root'/str(LOGICAL).lstrip('/')/'witness/RESULT.json'
    elif a.artifact in('FINAL_STOP.json','TARGET_INSTALL.json','RUNTIME_REVIEW.json'):path=LAB/a.artifact
    else:path=LAB/'evidence'/a.artifact
    raw=read(path,32768);return{'name':a.artifact,'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','start-node','bootstrap','gateway','initialize','source','fence','export','status','stop','fetch','fresh','final','install-target','target'))
    p.add_argument('--controller-sha256',required=True);p.add_argument('--artifact');p.add_argument('--proof-sha256');p.add_argument('--runtime-sha256');a=p.parse_args()
    need(re.fullmatch('[0-9a-f]{64}',a.controller_sha256)is not None);globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256
    handler=globals().get(a.action.replace('-','_'))
    answer=handler(a)if handler is not None else action(a)
    print(json.dumps(answer,sort_keys=True))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        code=str(exc)if type(exc)is ValueError and re.fullmatch('[A-Za-z0-9_]{1,64}',str(exc))is not None else None
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'fixed_code':code,'scope':'c827_only'}));raise SystemExit(1)from None
