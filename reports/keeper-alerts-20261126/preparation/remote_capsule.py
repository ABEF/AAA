"""Closed c815 read-only alert selection in a fresh private-network unit."""
from pathlib import Path,PurePosixPath
import argparse,base64,hashlib,io,json,os,re,selectors,signal,stat,subprocess,sys,tarfile,time

LAB=Path('/opt/popl-keeper-alerts-20261126-c815')
UNIT='popl-keeper-alerts-20261126-c815.service'
EXPECTED={'source/keeper/alerts.py': {'bytes': 22978, 'sha256': '41717ebe4045c82d32edfa3758c5b80c9481aeef2b4d2a5426c99fd12b6122fd'}, 'source/scripts/keeper-alerts.py': {'bytes': 2629, 'sha256': '4f3b6b3efa9401c4039b9dcdc1fa9bf0c4136c2342f02c7286c895bc0ef027c5'}, 'source/tests_python/test_keeper_alerts.py': {'bytes': 32525, 'sha256': 'f960f5a50dd1469b3d1f9c1bfb1002e68e1c83982586bc59eec390db83915b6d'}, 'source/keeper/monitor.py': {'bytes': 194496, 'sha256': '90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'}, 'source/keeper/ops.py': {'bytes': 14444, 'sha256': 'da396ec9c65295fe540f9dc812a0612d8ed27f1ab677fd388b479e2f2372ad89'}, 'source/keeper/health.py': {'bytes': 24415, 'sha256': 'dd25d2151295d09dcdebc4b0331b82c8d2b384a5501b49d0bfeb483d396b5c04'}, 'source/keeper/rebalance_confirmation.py': {'bytes': 11926, 'sha256': '6cc29d78aaf4c3804379e9b15d0ff177ff537da1158e66a3111ae2c85d6d317d'}, 'source/keeper/compound_policy.py': {'bytes': 17260, 'sha256': '129d330417c37747e16456fd18c892550cf870bdad31847e328b42a5c7270e29'}, 'source/keeper/cast_process.py': {'bytes': 4617, 'sha256': 'b6203067b022625bce2bfb415bb6ed85620dc8c7002b51f2d3d4c9296c5ac3e1'}, 'source/zzz_ops/protocol_policy.py': {'bytes': 5907, 'sha256': '4d73e7a3f6d6b98c91f083e2c557a48259ac9bcc0dbe2fb7752f74c4335bb5c3'}, 'source/zzz_ops/lp_execution.py': {'bytes': 6860, 'sha256': '90c985622387a4de8d52dd075856a4cf25e8c2e5bc62f4a3490978fc8cf746b0'}, 'source/zzz_ops/execution_price.py': {'bytes': 2280, 'sha256': '1d0ff892d43ec450438e7d2a1c2f783e6d9f9aec66f1fe98e3c35f5b09de47e2'}, 'source/zzz_ops/rebalance_confirmation.py': {'bytes': 17194, 'sha256': '77a41f2520be5d5c6768505e7bfe75f68db79d37f611062750ecd02f58185331'}, 'source/zzz_ops/abi.py': {'bytes': 4797, 'sha256': 'c4c755f1a9bf8db70b1ecb81e2b4e6765581961289f6f550502983e375293d91'}, 'source/zzz_ops/rpc.py': {'bytes': 9709, 'sha256': '6b76610b1bc042196198657e069b30ef1009aff3237d71979e8d21495fb6380f'}, 'source/zzz_ops/state.py': {'bytes': 4644, 'sha256': '78985688f9fc0cebf4aa5912b1401a338ac1e9ce21d8c787393e0e2d421976cf'}, 'source/scripts/keeper-recovery.py': {'bytes': 3423, 'sha256': '450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'}, 'source/keeper/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'source/keeper/recovery_bundle.py': {'bytes': 36223, 'sha256': 'fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268'}, 'source/tests_python/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'source/keeper/principal.py': {'bytes': 9171, 'sha256': 'b602340db5c7a52ad281c6b60885e2f74cc2708b731595fac5eeb9e026da6874'}, 'source/keeper/royalties.py': {'bytes': 17321, 'sha256': '02e04783068eed60db827673c9c27d3a37175edd7dccfa5ddefb8b54c055904c'}, 'source/keeper/watchdog.py': {'bytes': 5707, 'sha256': '59b4bb7783453a8f271fd5ab265fd5d2857d55096479be34f10ffe56c8408372'}, 'source/zzz_ops/errors.py': {'bytes': 992, 'sha256': '1dcc2855b45af8f806835f70f7f75200aa5b93ef84ddcf862e1e0f067aba5305'}, 'source/zzz_ops/ethereum_fees.py': {'bytes': 2464, 'sha256': '8c832b5e28beb7d7d5c8d90d6df102bb084a680cf251ded850a2f00fe0cb2ffe'}, 'source/zzz_ops/position.py': {'bytes': 2437, 'sha256': '54075cb2329e6e1defb4942683378d6a3995a74a6ea5e1f239a8fcf611e30d4d'}, 'source/zzz_ops/range_policy.py': {'bytes': 5859, 'sha256': '4d4d8c1772b45417d98e2aa336e100f59674c7bbbe7f4a35efa8d07f87d90171'}, 'source/keeper/operation_review.py': {'bytes': 43774, 'sha256': '75f6fc17399ae28791f81d97d5afea2f98a3061662cbb6e9f072b562d6f72f48'}, 'source/zzz_ops/physical_portfolio.py': {'bytes': 2125, 'sha256': 'f119b665860cb4aaa9fbebe81aa1f2564906dff8466d1febf96ea4eef46e719b'}, 'source/zzz_ops/production_v4.py': {'bytes': 65998, 'sha256': 'ffa0e95b06ca1c166e7e56debcba8829764a204a3f7b7e377fa2310499073d5c'}, 'source/zzz_ops/tick_math.py': {'bytes': 4949, 'sha256': '5224a360f3fecbc9c1d42094863e74771cee8036a60d8b81647d9e6d45e0c70a'}, 'source/zzz_ops/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'source/zzz_ops/work_budget.py': {'bytes': 3633, 'sha256': 'd60de944ee02fc8be02cdbdde0210c84fff02dea8bb63b386cc73688061a535b'}, 'source/zzz_ops/production_v2.py': {'bytes': 102622, 'sha256': '109531b48b9c8a85166c9585351dc40b4b534ec5eea14c5b81d895c1b2209889'}, 'source/zzz_ops/price_policy.py': {'bytes': 7148, 'sha256': '2f5e41da367c04fd811ac14a09bf0662abf8fe46f7a7619a17efa58295ce2958'}, 'source/reports/ubuntu-backup-recovery-20261126/evidence/c814/model-DRY.json': {'bytes': 11810, 'sha256': 'ad430c2dfbb5909f7925196d575965b91dff0f6c8397f9f54133749c2ac36d13'}, 'source/reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json': {'bytes': 7965, 'sha256': '70b4e6081c561092d7c7cadf173da48180b912839818ee262c2cf830b83e463f'}, 'source/run_selected.py': {'bytes': 6492, 'sha256': '78af5193870b435b1618dba8e582dca8396f4f9adaaa87b87b24c89bdddf8f63'}, 'SOURCE_MANIFEST.json': {'bytes': 21477, 'sha256': '281bef464b778fc5578b143c3b20662baec3b5ff970568d17e615c9110d7659a'}}
BUNDLE_SHA='02f210e48ba3853471e2099310df1c02b087b98cdebddf5782b72b9446fc9859'
SOURCE_MANIFEST_SHA='281bef464b778fc5578b143c3b20662baec3b5ff970568d17e615c9110d7659a'
SELECTED=('test_backup_rotation_and_hash_publication_preserve_pending_age_and_outbox', 'test_competing_sidecar_lock_refuses_without_mutating_state', 'test_configuration_race_preserves_outbox_and_cannot_emit_recovery', 'test_corrupt_health_is_sanitized_and_does_not_hide_backup_result', 'test_dropped_ack_is_at_least_once_with_same_event_id', 'test_dry_health_requires_explicit_alert_mode', 'test_failed_durable_publication_sends_nothing_and_keeps_original_outbox', 'test_full_publicly_generated_outbox_drains_without_pruning_or_reset', 'test_hashless_pending_and_mismatched_health_never_receive_known_hash_grace', 'test_health_and_backup_age_failures_are_independently_visible', 'test_incident_dedup_is_durable_across_repeated_one_shots', 'test_known_pending_grace_tracks_first_observation_across_restarts', 'test_pending_grace_cannot_mask_wrong_configuration_or_source', 'test_real_current_health_and_backup_validators_compose_without_side_effects', 'test_real_local_receiver_acknowledges_incident_and_later_recovery', 'test_recovery_requires_fresh_health_and_a_verified_backup', 'test_redirect_is_not_followed_and_environment_proxies_are_ignored', 'test_slow_trickle_headers_obey_absolute_delivery_budget', 'test_snapshot_adapter_has_identical_checks_without_rereading_health_file', 'test_unsafe_receiver_resource_bounds_and_input_aliases_fail_without_secret_echo', 'test_wrong_ack_keeps_event_for_identical_retry')
MAX_ARCHIVE=2*1024*1024
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def need(value):
    if not value:raise ValueError('Fixed isolated alert selection refused')

def clear_signal_mask():
    signal.pthread_sigmask(signal.SIG_SETMASK,set())

def run(argv,timeout=15):
    """Bound one fixed manager query; never reap before ownership is cleared."""
    mask={signal.SIGALRM,signal.SIGTERM,signal.SIGHUP,signal.SIGINT}
    owned=None;child=None;outputs=[bytearray(),bytearray()];size=0;end=time.monotonic()+timeout
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,mask)
    try:
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'},start_new_session=True,close_fds=True,preexec_fn=clear_signal_mask)
        owned=child
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
    try:
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<end)
                for key,_ in selector.select(min(.1,max(.001,end-time.monotonic()))):
                    raw=os.read(key.fd,min(16384,65537-size))
                    if not raw:selector.unregister(key.fileobj);continue
                    size+=len(raw);need(size<=65536);outputs[key.data].extend(raw)
        previous=signal.pthread_sigmask(signal.SIG_BLOCK,mask)
        try:code=child.wait(timeout=max(.001,end-time.monotonic()));owned=None
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
        return code,bytes(outputs[0]),bytes(outputs[1])
    finally:
        if owned is not None:
            try:os.killpg(owned.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            previous=signal.pthread_sigmask(signal.SIG_BLOCK,mask)
            try:owned.wait(timeout=2);owned=None
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
        if child is not None:child.stdout.close();child.stderr.close()

def properties():
    code,out,err=run(['/usr/bin/systemctl','show',UNIT,'--no-pager','--property=Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,ExecStart,User,Group,PrivateNetwork,PrivateDevices,ProtectSystem,ProtectHome,NoNewPrivileges,Restart,NRestarts,KillMode,RuntimeMaxUSec,TimeoutStopUSec,MemoryMax,MemorySwapMax,TasksMax,WorkingDirectory,ReadWritePaths'])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found')
    return value

def secure_read(path,maximum,owner=0,mode=None):
    st=path.lstat();need(stat.S_ISREG(st.st_mode)and not path.is_symlink()and st.st_uid==owner
        and st.st_nlink==1 and not st.st_mode&0o022 and 0<=st.st_size<=maximum)
    if mode is not None:need(stat.S_IMODE(st.st_mode)==mode)
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
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
    owned();need(a.artifact in ('RESULT.json','FINAL.json'))
    if a.artifact=='RESULT.json':raw=secure_read(LAB/'runtime/RESULT.json',65536,owner=65534,mode=0o600)
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
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'fixed_scope':'isolated_c815_alert_selection'}))
        raise SystemExit(1)from None
