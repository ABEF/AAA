__name__='_preserved_c828_controller'
"""Fixed c828 controls. Original host services, journals and source labs are untouched."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,math,os,re,selectors,signal,stat,subprocess,sys,time,zlib

LAB=Path('/opt/popl-keeper-clean-restart-20261127-c828')
LOGICAL=Path('/run/popl-keeper-clean-restart-20261127-c828')
BASE='popl-keeper-clean-restart-20261127-c828'
OLD=Path('/opt/popl-ubuntu-backup-recovery-20261126-c814')
FIXTURE=OLD/'inputs'
SOURCE_PIN='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
SOURCE_FILES={'keeper/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'keeper/alerts.py': {'bytes': 23149, 'sha256': '053ac2a70f38801b77afde8ba107c78e322a11630cb04620e1aa35a3f811fe13'}, 'keeper/cast_process.py': {'bytes': 5694, 'sha256': '5856fec6fb15e1abb66750394c2fb7a24314686e964eca0e9363b5007aa5ba3a'}, 'keeper/compound_policy.py': {'bytes': 17260, 'sha256': '129d330417c37747e16456fd18c892550cf870bdad31847e328b42a5c7270e29'}, 'keeper/health.py': {'bytes': 24415, 'sha256': 'dd25d2151295d09dcdebc4b0331b82c8d2b384a5501b49d0bfeb483d396b5c04'}, 'keeper/monitor.py': {'bytes': 194496, 'sha256': '90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'}, 'keeper/operation_review.py': {'bytes': 43774, 'sha256': '75f6fc17399ae28791f81d97d5afea2f98a3061662cbb6e9f072b562d6f72f48'}, 'keeper/ops.py': {'bytes': 14444, 'sha256': 'da396ec9c65295fe540f9dc812a0612d8ed27f1ab677fd388b479e2f2372ad89'}, 'keeper/principal.py': {'bytes': 9171, 'sha256': 'b602340db5c7a52ad281c6b60885e2f74cc2708b731595fac5eeb9e026da6874'}, 'keeper/rebalance_confirmation.py': {'bytes': 11926, 'sha256': '6cc29d78aaf4c3804379e9b15d0ff177ff537da1158e66a3111ae2c85d6d317d'}, 'keeper/recovery_bundle.py': {'bytes': 36532, 'sha256': '022cd3b9a3692f9b5576fded8fb15d4aca2797f4ad3bd449561a4d57173de550'}, 'keeper/royalties.py': {'bytes': 17321, 'sha256': '02e04783068eed60db827673c9c27d3a37175edd7dccfa5ddefb8b54c055904c'}, 'keeper/scheduling.py': {'bytes': 17800, 'sha256': 'd79be28db6bac2978f7c8efdfb641e037ce6d2024faa4e60e02f6f7c62049f4a'}, 'keeper/sidecar_recovery.py': {'bytes': 22768, 'sha256': 'eda3b43e316adab4fb8a2161a7d5e5f750ba4e1e0c9b3432037d6acf39396546'}, 'keeper/watchdog.py': {'bytes': 5707, 'sha256': '59b4bb7783453a8f271fd5ab265fd5d2857d55096479be34f10ffe56c8408372'}, 'scripts/keeper-alerts.py': {'bytes': 2629, 'sha256': '4f3b6b3efa9401c4039b9dcdc1fa9bf0c4136c2342f02c7286c895bc0ef027c5'}, 'scripts/keeper-recovery.py': {'bytes': 3423, 'sha256': '450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'}, 'scripts/keeper-schedule.py': {'bytes': 2140, 'sha256': '5c07ec965eba5c5a2d94895ba050f17d49b9689923cf67a05f20f2d0bf29c0b4'}, 'scripts/keeper-sidecar-recovery.py': {'bytes': 2924, 'sha256': '408858a48eb2eb464d9745e7767603c1142f03aa96ba7b280ae7081f8deeca58'}, 'tests_python/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'tests_python/test_keeper_alerts.py': {'bytes': 32525, 'sha256': 'f960f5a50dd1469b3d1f9c1bfb1002e68e1c83982586bc59eec390db83915b6d'}, 'tests_python/test_keeper_scheduling.py': {'bytes': 15979, 'sha256': '15a4f2bf088fc1853437838c3925f2eb5be9295305880dbaa052ef390bedae72'}, 'tests_python/test_keeper_sidecar_recovery.py': {'bytes': 18390, 'sha256': '6811351e1e41563e7a7fe23c494b43938a3afeb81576b64c7b9d6d05239486ef'}, 'zzz_ops/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'zzz_ops/abi.py': {'bytes': 4797, 'sha256': 'c4c755f1a9bf8db70b1ecb81e2b4e6765581961289f6f550502983e375293d91'}, 'zzz_ops/errors.py': {'bytes': 992, 'sha256': '1dcc2855b45af8f806835f70f7f75200aa5b93ef84ddcf862e1e0f067aba5305'}, 'zzz_ops/ethereum_fees.py': {'bytes': 2464, 'sha256': '8c832b5e28beb7d7d5c8d90d6df102bb084a680cf251ded850a2f00fe0cb2ffe'}, 'zzz_ops/execution_price.py': {'bytes': 2280, 'sha256': '1d0ff892d43ec450438e7d2a1c2f783e6d9f9aec66f1fe98e3c35f5b09de47e2'}, 'zzz_ops/lp_execution.py': {'bytes': 6860, 'sha256': '90c985622387a4de8d52dd075856a4cf25e8c2e5bc62f4a3490978fc8cf746b0'}, 'zzz_ops/physical_portfolio.py': {'bytes': 2125, 'sha256': 'f119b665860cb4aaa9fbebe81aa1f2564906dff8466d1febf96ea4eef46e719b'}, 'zzz_ops/position.py': {'bytes': 2437, 'sha256': '54075cb2329e6e1defb4942683378d6a3995a74a6ea5e1f239a8fcf611e30d4d'}, 'zzz_ops/price_policy.py': {'bytes': 7148, 'sha256': '2f5e41da367c04fd811ac14a09bf0662abf8fe46f7a7619a17efa58295ce2958'}, 'zzz_ops/production_v2.py': {'bytes': 102622, 'sha256': '109531b48b9c8a85166c9585351dc40b4b534ec5eea14c5b81d895c1b2209889'}, 'zzz_ops/production_v4.py': {'bytes': 65998, 'sha256': 'ffa0e95b06ca1c166e7e56debcba8829764a204a3f7b7e377fa2310499073d5c'}, 'zzz_ops/protocol_policy.py': {'bytes': 5907, 'sha256': '4d73e7a3f6d6b98c91f083e2c557a48259ac9bcc0dbe2fb7752f74c4335bb5c3'}, 'zzz_ops/range_policy.py': {'bytes': 5859, 'sha256': '4d4d8c1772b45417d98e2aa336e100f59674c7bbbe7f4a35efa8d07f87d90171'}, 'zzz_ops/rebalance_confirmation.py': {'bytes': 17194, 'sha256': '77a41f2520be5d5c6768505e7bfe75f68db79d37f611062750ecd02f58185331'}, 'zzz_ops/rpc.py': {'bytes': 9709, 'sha256': '6b76610b1bc042196198657e069b30ef1009aff3237d71979e8d21495fb6380f'}, 'zzz_ops/state.py': {'bytes': 4644, 'sha256': '78985688f9fc0cebf4aa5912b1401a338ac1e9ce21d8c787393e0e2d421976cf'}, 'zzz_ops/tick_math.py': {'bytes': 4949, 'sha256': '5224a360f3fecbc9c1d42094863e74771cee8036a60d8b81647d9e6d45e0c70a'}, 'zzz_ops/work_budget.py': {'bytes': 3633, 'sha256': 'd60de944ee02fc8be02cdbdde0210c84fff02dea8bb63b386cc73688061a535b'}}
HELPERS={'shared.py': {'bytes': 12015, 'sha256': 'f8105871fc3ee10e3456b8af29c69e076d2741e2ed90eba5d07b7641faa77128'}, 'gateway.py': {'bytes': 7437, 'sha256': '3a6e380fd34c4b0479d9e5fe7d41d7b666d4fc721ec844b761e80b11ef436292'}, 'driver.py': {'bytes': 13350, 'sha256': 'c1b0f4a87ca0a1a31a4a3fc7e364ac4878ec4ba7c626e37c988c68a2163195ab'}, 'runtime_support.py': {'bytes': 8075, 'sha256': 'd447e2571919d0bbd7b80f3f7bdd0c0a4df4e96a128a10026293125e12beac72'}, 'target_worker.py': {'bytes': 19299, 'sha256': '4e3691ed4722701d42f7abe724fc5e0d9d4cc18d2702b23b6dfba35db840f236'}}
TOOLS={'anvil':('/opt/popl-history-export-20261124-c7eb/tools/anvil','05ee0cf1758024ea5e23dae562d92955ace205ab299091a43d2fa5bdeb6933bd'),
    'cast':('/opt/popl-ubuntu-20261121-8a629f43/bin/cast','d55f540256f0dd8b940a125d435919948a5e8c140262e9923067cbfa95ef2970')}
INPUTS={'restore-state.json':(13643211,'42ab11fd14bd02868359fb3fdd84e961f3f8050245f0cb370d1962be823d9b9a'),
    'instances.json':(4845414,'e94a9dc5d4f3f04211ad77e62612b2284301584c3e363203198311d34d128e56'),
    'entry-receipts.json':(696971,'425902fae92cdbb210f3a12afc80908b9bd186ec1ae80060c427d9f302f3c519')}
ROLES=('node','gateway','bootstrap','initialize','source','capture','target','final','fresh')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def need(value,code='fixed_c828_refused'):
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
    spec=importlib.util.spec_from_file_location('fixed_c828_runtime',path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


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
    need(message['kind']=='c828-preparation'and set(files)==expected,'preparation_inventory')
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
    return{'schema':1,'kind':'c828-private-native-capture','files':files,'INCLUDED':decode(read(LAB/'evidence/INCLUDED.json')),
        'raw_records_private':True,'source_release_exported':False,'signer_material_exported':False}


def install_target(a):
    identity=owned();need(not os.path.lexists(LAB/'target-root')and props('target').get('LoadState')=='not-found','fresh_target_root')
    need(type(a.proof_sha256)is str and re.fullmatch('[0-9a-f]{64}',a.proof_sha256)is not None,'desktop_proof_pin')
    need(a.runtime_sha256==identity['runtime_review_sha256'],'external_runtime_review_pin')
    message,files=packet();expected={'SOURCE_MANIFEST.json','CONFIG.json','bundle/manifest.json','bundle/journal.json',
        *('source/'+name for name in SOURCE_FILES)}
    need(message['kind']=='c828-desktop-recovery-kit'and set(files)==expected and len(files)==45,'target_kit_inventory')
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
        need(empty('target',state)and state.get('ExecMainCode')=='1','target_fenced_before_private_fetch')
        result_path=logical/'witness/RESULT.json'
        result_present=os.path.lexists(result_path)
        result=decode(read(result_path,32768))if result_present else None
        target_success=state.get('ExecMainStatus')=='0'and type(result)is dict and result.get('success')is True
        wanted={'STATE-BEFORE.json':'witness/STATE-BEFORE.json','STATE-SETTLED.json':'witness/STATE-SETTLED.json',
            'STATE-DRY.json':'witness/STATE-DRY.json','HEALTH-RECOVERY.json':'witness/HEALTH-RECOVERY.json',
            'HEALTH-DRY.json':'witness/HEALTH-DRY.json','RESTORE_PLAN.json':'witness/native-restored/RESTORE_PLAN.json',
            'TARGET_IDENTITY.json':'TARGET_IDENTITY.json','CONFIG.json':'actor/config.json'}
        files={};missing=[]
        for name,relative in wanted.items():
            if not os.path.lexists(logical/relative):missing.append(name);continue
            data=read(logical/relative,32768);files[name]={'bytes':len(data),'sha256':sha(data),'raw_base64':base64.b64encode(data).decode('ascii')}
        if target_success:need(not missing and result_present,'successful_target_private_records_complete')
        captured=decode(read(LAB/'evidence/INCLUDED.json'))
        need(sha(read(LAB/'actor/config.json'))==captured['configuration_sha256']
            and sha(read(LAB/'actor/state.json'))==captured['pending_journal_sha256'],'source_inputs_preserved')
        packet=enc({'schema':1,'kind':'c828-private-target-records','files':files,
            'missing':missing,'target_success':target_success,'target_result_present':result_present,'target_unit_status':state,
            'source_configuration_and_journal_unchanged':True,'raw_records_must_remain_private':True,
            'missing_records_reconstructed_or_execution_repeated':False})
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
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'fixed_code':code,'scope':'c828_only'}));raise SystemExit(1)from None

OLD_CONTROLLER='22d459431d168fa5822ea8917544a2de166f2e1a820b1d9f6de39516a1d31a91'
ROOT2=LAB/'target2-root'
LOG2=ROOT2/str(LOGICAL).lstrip('/')
ROLES=(*ROLES,'target2','fresh2')


def pair(path):return[path.lstat().st_dev,path.lstat().st_ino]


def start2(a):
    identity=owned();old=props('target')
    fresh=props('fresh2');need(empty('fresh2',fresh)and fresh.get('ExecMainCode')=='1'
        and fresh.get('ExecMainStatus')=='0','fresh_confirmed_anchor_before_target2')
    need(empty('target',old)and old.get('ExecMainCode')=='1'and old.get('ExecMainStatus')=='226','original_preexec_namespace_failure')
    need(not ROOT2.exists()and props('target2').get('LoadState')=='not-found','fresh_target2')
    original=LAB/'target-root'/str(LOGICAL).lstrip('/')
    installed=decode(read(LAB/'TARGET_INSTALL.json',32768))
    need(not(original/'actor/health.json').exists()and not(original/'actor/keeper.lock').exists()
        and not(original/'witness/RESULT.json').exists(),'original_target_never_executed')
    files={}
    for name,row in installed['files'].items():
        path=original/('actor/config.json'if name=='CONFIG.json'else name)
        raw=read(path,1048576);need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'cached_desktop_file_pin')
        files[name]=raw
    need(len(files)==45,'cached_desktop_inventory')
    runtime=module('runtime_support.py').runtime_review()
    need(sha(enc(runtime))==identity['runtime_review_sha256'],'runtime_changed')
    ROOT2.mkdir(mode=0o755);LOG2.mkdir(parents=True,mode=0o755)
    for name,raw in files.items():write(LOG2/('actor/config.json'if name=='CONFIG.json'else name),raw,0o444)
    os.chown(LOG2/'actor',65534,65534);os.chmod(LOG2/'actor',0o700)
    write(LOG2/'actor/state.json',files['bundle/journal.json'],0o600,65534)
    for name in('witness','tmp','empty-home'):
        (LOG2/name).mkdir(mode=0o700);os.chown(LOG2/name,65534,65534)
    (LOG2/'shared').mkdir(mode=0o755)
    for name in('shared.py','runtime_support.py','target_worker.py'):
        raw=read(LAB/'helpers'/name,65536);need(sha(raw)==HELPERS[name]['sha256'],'original_harness_pin')
        if name=='target_worker.py':
            before=b"old + '/target-root'";after=b"old + '/target2-root'"
            need(raw.count(before)==1,'one_namespace_literal')
            raw=raw.replace(before,after);worker2_pin=sha(raw)
        write(LOG2/'helpers'/name,raw,0o444)
    target_identity=decode(read(original/'TARGET_IDENTITY.json',65536))
    target_identity.update(target_root_inode_pair=pair(ROOT2),target_host_root=str(ROOT2),
        target_input_inode_pairs={name:pair(LOG2/name)for name in target_identity['target_input_inode_pairs']})
    need(all(target_identity['target_input_inode_pairs'][name]!=pair(original/name)
        and target_identity['target_input_inode_pairs'][name]!=target_identity['original_input_inode_pairs'][name]
        for name in target_identity['target_input_inode_pairs']),'fresh_target2_input_inodes')
    write(LOG2/'TARGET_IDENTITY.json',enc(target_identity),0o444)
    write(LOG2/'RUNTIME_REVIEW.json',enc(runtime),0o444)
    for row in runtime['mounts']:
        path=ROOT2/row['target'].lstrip('/');path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
        if Path(row['source']).is_dir():path.mkdir(mode=0o755)
        else:write(path,b'',0o444)
    need(sha(read(LOG2/'actor/state.json'))==target_identity['pending_journal_sha256']
        and sha(read(LOG2/'actor/config.json'))==target_identity['configuration_sha256'],'target2_exact_inputs')
    review={'schema':1,'old_controller_sha256':OLD_CONTROLLER,'continuation_sha256':CONTINUATION_SHA,
        'cached_desktop_proof_sha256':installed['desktop_proof_sha256'],'cached_desktop_files':installed['files'],
        'worker2_sha256':worker2_pin,'worker_only_change':'fixed target_host_root literal target-root to target2-root',
        'failed_root_and_unit_preserved':True,'source_or_node_or_setup_replayed':False,
        'application_source_and_configuration_unchanged':True,'readiness_approved':False,'production_approved':False}
    write(LAB/'TARGET2_CONTINUATION_REVIEW.json',enc(review),0o600)
    policy=common('target2')
    policy.update(RootDirectory=str(ROOT2),MountAPIVFS='yes',WorkingDirectory=str(LOGICAL/'source'),
        BindReadOnlyPaths=' '.join([*(row['source']+':'+row['target']for row in runtime['mounts']),str(ROOT2/'run')+':/run']),
        BindPaths=str(LAB/'shared')+':'+str(LOGICAL/'shared'),
        ReadWritePaths=' '.join('+'+str(LOGICAL/name)for name in('actor','witness','shared','tmp','empty-home')))
    return launch('target2',['/usr/bin/python3','-S','-B',str(LOGICAL/'helpers/target_worker.py')],policy)


def status2(a):
    owned();p=props('target2')
    return{'target2':p,'group_empty':empty('target2',p),'result_present':(LOG2/'witness/RESULT.json').exists(),
        'node':props('node'),'original_target':props('target'),'fresh2':props('fresh2')}


def fresh2(a):
    owned()
    code="import sys;sys.dont_write_bytecode=True;sys.path.insert(0,"+repr(str(LOGICAL/'helpers'))+");import shared as S;S.namespace_guard();[S.mine() for _ in range(12)]"
    return launch('fresh2',['/usr/bin/python3','-S','-B','-c',code],mapped(common('fresh2')))


def result2(a):
    owned();raw=read(LOG2/'witness/RESULT.json',32768)
    return{'name':'TARGET2_RESULT.json','bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}


def private2(a):
    owned();p=props('target2');need(empty('target2',p)and p.get('ExecMainCode')=='1','target2_stopped')
    result_path=LOG2/'witness/RESULT.json';result=decode(read(result_path,32768))if result_path.exists()else None
    success=p.get('ExecMainStatus')=='0'and type(result)is dict and result.get('success')is True
    wanted={'STATE-BEFORE.json':'witness/STATE-BEFORE.json','STATE-SETTLED.json':'witness/STATE-SETTLED.json',
        'STATE-DRY.json':'witness/STATE-DRY.json','HEALTH-RECOVERY.json':'witness/HEALTH-RECOVERY.json',
        'HEALTH-DRY.json':'witness/HEALTH-DRY.json','RESTORE_PLAN.json':'witness/native-restored/RESTORE_PLAN.json',
        'TARGET_IDENTITY.json':'TARGET_IDENTITY.json','CONFIG.json':'actor/config.json'}
    files={};missing=[]
    for name,relative in wanted.items():
        if not(LOG2/relative).exists():missing.append(name);continue
        raw=read(LOG2/relative,32768);files[name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    if success:need(not missing,'target2_records_complete')
    captured=decode(read(LAB/'evidence/INCLUDED.json'))
    need(sha(read(LAB/'actor/state.json'))==captured['pending_journal_sha256']
        and sha(read(LAB/'actor/config.json'))==captured['configuration_sha256'],'source_inputs_preserved')
    packet=enc({'schema':1,'kind':'c828-private-target2-records','files':files,'missing':missing,
        'target_success':success,'target_unit_status':p,'raw_records_must_remain_private':True})
    need(len(packet)<=131072,'private_packet_bound');raw=zlib.compress(packet,9);need(len(raw)<=32768,'compressed_bound')
    return{'name':'TARGET2_PRIVATE.zlib','bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}


def final2(a):
    owned();p=props('target2');need(empty('target2',p)and p.get('ExecMainCode')=='1'and p.get('ExecMainStatus')=='0'
        and decode(read(LOG2/'witness/RESULT.json',32768))['success']is True,'target2_success_before_final')
    return launch('final',['/usr/bin/python3','-S','-B',str(LOGICAL/'helpers/driver.py'),'final'],mapped(common('final')))


def stop2(a):
    owned();states={}
    for role in('target2','fresh2'):
        p=props(role)
        if p.get('LoadState')!='not-found':code,_,_=run(['/usr/bin/systemctl','stop',unit(role)]);need(code==0,'target2_stop')
        p=props(role);need(empty(role,p),'target2_group_empty');states[role]=p
    if not(LAB/'TARGET2_STOP.json').exists():write(LAB/'TARGET2_STOP.json',enc({'schema':1,'group_empty':True,'units':states}),0o600)
    return{'target2_group_empty':True,'units':states}


def continuation_main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('fresh2','start2','status2','result2','private2','final2','stop2'))
    p.add_argument('--controller-sha256',required=True);a=p.parse_args()
    globals()['CONTINUATION_SHA']=a.controller_sha256;globals()['ACTIVE_CONTROLLER_SHA']=OLD_CONTROLLER
    need(re.fullmatch('[0-9a-f]{64}',CONTINUATION_SHA)is not None,'continuation_pin')
    print(json.dumps(globals()[a.action](a),sort_keys=True))


try:continuation_main()
except Exception as exc:
    print(json.dumps({'refused':True,'error_type':type(exc).__name__,
        'fixed_code':str(exc)if type(exc)is ValueError and re.fullmatch('[A-Za-z0-9_]{1,64}',str(exc))else None,
        'scope':'c828_target2_only'}));raise SystemExit(1)from None
