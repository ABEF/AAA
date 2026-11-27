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
