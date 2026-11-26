"""Offline c822 source/command closure and immutable package; no runtime imports."""
from pathlib import Path
import argparse,ast,gzip,hashlib,io,json,os,subprocess,sys,tarfile

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
HEAD='7436933c153246f57eaa01cf42c5f3ec90363dad'
PREPARATION=('build.py','capsule_template.py','host_control.py','lab_driver.py','lab_common.py',
    'schedule_worker.py','model_service.py')
FROZEN={'keeper_runtime.py':'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4',
    'keeper_jobs.py':'363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4',
    'job_cases.py':'7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'}
MODEL_SHA='c829059ff6ec73c13037b82995e267397ab59073de5fc48eaf8a9f436e9e82e5'
FIXTURES=ROOT/'reports/ubuntu-daemon-storage-20261126/preparation/shared'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
enc=lambda value:(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()


def git(*args):
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1')
    result=subprocess.run(['git',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
    assert len(result.stdout)<=8*1024*1024
    return result.stdout


def write(name,raw):
    with(BASE/name).open('xb')as stream:stream.write(raw)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review-pins',type=Path,required=True);args=parser.parse_args()
    review=json.loads(args.review_pins.read_bytes())
    assert set(review)=={'source_head','preparation_sha256'}and review['source_head']==HEAD
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert set(review['preparation_sha256'])==set(PREPARATION)
    prepared={}
    for name in PREPARATION:
        raw=(BASE/name).read_bytes();assert sha(raw)==review['preparation_sha256'][name]
        ast.parse(raw,filename=name);prepared[name]=raw
    assert sha(prepared['model_service.py'])==MODEL_SHA
    helpers={}
    for name,digest in FROZEN.items():
        raw=(FIXTURES/name).read_bytes();assert sha(raw)==digest;ast.parse(raw,filename=name);helpers[name]=raw
    helpers.update({name:prepared[name]for name in('lab_common.py','schedule_worker.py','model_service.py')})
    tracked=set(git('ls-tree','-r','--name-only',HEAD).decode().splitlines())
    blobs={}
    def source(name):
        if name not in blobs:blobs[name]=git('show',HEAD+':'+name)
        return blobs[name]
    def declaration(path,name):
        nodes=[node.value for node in ast.parse(source(path)).body if isinstance(node,ast.Assign)
            and any(isinstance(target,ast.Name)and target.id==name for target in node.targets)]
        assert len(nodes)==1
        return nodes[0]
    health=ast.literal_eval(declaration('keeper/health.py','SOURCE_FILES'))
    recovery=ast.literal_eval(declaration('keeper/recovery_bundle.py','SOURCE_FILES'))
    producer=ast.literal_eval(declaration('keeper/recovery_bundle.py','PRODUCER_FILES'))
    assert health==recovery and len(health)==13 and len(producer)==2
    expected="('keeper/alerts.py','scripts/keeper-alerts.py',*recovery_bundle.PRODUCER_FILES)"
    assert ast.dump(declaration('keeper/alerts.py','OBSERVER_SOURCE_FILES'))==ast.dump(ast.parse(expected,mode='eval').body)
    observer=('keeper/alerts.py','scripts/keeper-alerts.py',*producer)
    expected="tuple(dict.fromkeys((*recovery.SOURCE_FILES,*alerts.OBSERVER_SOURCE_FILES,'keeper/scheduling.py','scripts/keeper-schedule.py')))"
    assert ast.dump(declaration('keeper/scheduling.py','SOURCE_FILES'))==ast.dump(ast.parse(expected,mode='eval').body)
    scheduling=tuple(dict.fromkeys((*recovery,*observer,'keeper/scheduling.py','scripts/keeper-schedule.py')))
    assert len(scheduling)==19
    groups={'health13':health,'recovery13':recovery,'recovery_producer2':producer,
        'observer4':observer,'scheduling19':scheduling}
    roots=tuple(dict.fromkeys((*scheduling,'keeper/monitor.py')))
    queue=list(roots);rows={};edges={}
    project_roots={'keeper','zzz_ops','frontend_api','indexer','scripts'}
    def module_path(module):
        stem=module.replace('.','/')
        return next((path for path in(stem+'.py',stem+'/__init__.py')if path in tracked),None)
    def dependencies(raw,name):
        result=set()
        for node in ast.walk(ast.parse(raw,filename=name)):
            requested=[]
            if isinstance(node,ast.Import):requested=[alias.name for alias in node.names]
            elif isinstance(node,ast.ImportFrom):
                module=node.module or''
                if node.level:
                    here=name.removesuffix('.py').replace('/','.').split('.')[:-1]
                    module='.'.join(here[:len(here)-node.level+1]+([module]if module else[]))
                requested=[module,*[module+'.'+alias.name for alias in node.names if alias.name!='*']]
            for module in requested:
                path=module_path(module)
                if path is not None:result.add(path)
                elif module.split('.')[0]not in project_roots|set(FROZEN)|{'keeper_runtime','keeper_jobs','job_cases','lab_common'}:
                    assert module.split('.')[0]in sys.stdlib_module_names,('unknown_dependency',name,module)
        return sorted(result)
    for name,raw in helpers.items():queue.extend(dependencies(raw,'source/helpers/'+name))
    while queue:
        name=queue.pop(0)
        if name in rows:continue
        assert len(rows)<128 and name.endswith('.py')and not name.startswith('tests')
        raw=source(name);assert len(raw)<=1024*1024
        rows[name]=pin(raw);edges[name]=dependencies(raw,name);queue.extend(edges[name])
        for index in range(1,len(name.split('/'))):
            path='/'.join(name.split('/')[:index])+'/__init__.py'
            if path in tracked:queue.append(path)
    for group in groups.values():assert set(group)<=set(rows)
    # Frozen validate_source explicitly requires this current event schema even
    # though this narrow composition does not run the historical indexer body.
    data_files={'indexer/event_schema.json'}
    for raw in helpers.values():
        data_files.update(node.value for node in ast.walk(ast.parse(raw))
            if isinstance(node,ast.Constant)and type(node.value)is str
            and node.value.endswith('.json')and node.value in tracked)
    if 'indexer/events.py'in rows:data_files.add('indexer/event_schema.json')
    if 'indexer/historical.py'in rows:data_files.add('indexer/historical_event_schema.json')
    for name in sorted(data_files):
        raw=source(name);json.loads(raw);assert len(raw)<=1024*1024;rows[name]=pin(raw)
    stringpaths={node.value for name in rows if name.endswith('.py')for node in ast.walk(ast.parse(source(name)))
        if isinstance(node,ast.Constant)and type(node.value)is str and node.value.endswith('.py')and node.value in tracked}
    assert stringpaths<=set(rows),('missing_source_string',sorted(stringpaths-set(rows)))
    # Reuse the original identity pins, rather than relabel old source/journals.
    old=json.loads((ROOT/'reports/keeper-sidecar-recovery-20261126/preparation/c821/SOURCE_MANIFEST.json').read_bytes())
    assert all(rows[name]=={key:value for key,value in old['source_files'][name].items()if key in('bytes','sha256')}for name in scheduling)
    production={'schema':1,'source_head':HEAD,'members':rows,'byte_equal_to_base_HEAD':True,
        'current_unchanged_source19':list(scheduling),'approved_worktree_overrides':[],
        'scope':'current_keeper_and_sidecar_composition_no_test_bodies','runtime_attestation':False}
    production_raw=enc(production)
    model_args=[]
    for key,value in(('source-manifest',sha(production_raw)),('base',FROZEN['keeper_runtime.py']),
        ('jobs',FROZEN['keeper_jobs.py']),('cases',FROZEN['job_cases.py'])):
        model_args+=['--'+key+'-sha256',value]
    driver=prepared['lab_driver.py'].decode().replace('__MODEL_ARGS__',repr(model_args)).encode()
    ast.parse(driver);helpers['lab_driver.py']=driver
    members={'source/contracts/'+name:source(name)for name in rows}
    members.update({'source/helpers/'+name:raw for name,raw in helpers.items()})
    members['inputs/SOURCE_MANIFEST.json']=production_raw
    manifest={'schema':1,'source_head':HEAD,'source_files':rows,'static_import_edges':edges,
        'dynamic_source_groups':groups,'explicit_data_dependencies':sorted(data_files),
        'dynamic_command_entrypoints':['python3 -m keeper.monitor','scripts/keeper-schedule.py'],
        'helpers':{name:pin(raw)for name,raw in helpers.items()},'source19_unchanged':True,
        'old_component_test_bodies_run':0,'all_source_and_command_inputs_packaged':True,
        'controlled_copied_F6_state_only':True,'actual_local_Cast_daemon_execution_planned':True,
        'public_transactions':0,'production_approved':False,'source_overrides':[],
        'production_source_manifest_sha256':sha(production_raw),
        'reviewed_preparation_sha256':review['preparation_sha256'],
        'members':{name:pin(raw)for name,raw in members.items()}}
    manifest_raw=enc(manifest);members['SOURCE_MANIFEST.json']=manifest_raw
    sink=io.BytesIO()
    with gzip.GzipFile(fileobj=sink,mode='wb',filename='',mtime=0)as zipped:
        with tarfile.open(fileobj=zipped,mode='w',format=tarfile.USTAR_FORMAT)as packet:
            for name,raw in sorted(members.items()):
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o444;item.uid=item.gid=0
                item.uname=item.gname='root';item.mtime=0;packet.addfile(item,io.BytesIO(raw))
    bundle=sink.getvalue();assert len(bundle)<=2*1024*1024 and sum(map(len,members.values()))<=8*1024*1024
    controller=prepared['capsule_template.py'].decode().replace('__MEMBERS__',repr({name:pin(raw)for name,raw in members.items()}))
    controller=controller.replace('__BUNDLE_SHA__',repr(sha(bundle))).replace('__SOURCE_MANIFEST_SHA__',repr(sha(manifest_raw)))
    ast.parse(controller);assert len(controller.encode())<=65536
    assert all((BASE/name).read_bytes()==raw for name,raw in prepared.items())
    for name,raw in(('c822.inputs.tar.gz',bundle),('remote_capsule.py',controller.encode()),
        ('SOURCE_MANIFEST.json',manifest_raw),('PRODUCTION_SOURCE_MANIFEST.json',production_raw),('generated_lab_driver.py',driver)):
        write(name,raw)
    receipt={'schema':1,'source_head':HEAD,'bundle':pin(bundle),'controller':pin(controller.encode()),
        'source_manifest':pin(manifest_raw),'host_wrapper':pin(prepared['host_control.py']),
        'source_members':len(rows),'archive_members':len(members),'frozen_helpers':FROZEN,
        'model':pin(prepared['model_service.py']),'old_test_bodies_run':0,'tests_run':0,'server_actions':0,
        'production_source_overrides':[],'new_owned_services':7,'new_owned_timers':2,
        'limits':{'seconds':900,'RPC':6000,'normal_poll_seconds':240,'confirmations':12,'harvest_seconds':3600,
            'maintenance_gas':24000000,'padding_percent':25,'raw_submissions':1,'max_backups':32,
            'backup_timer_seconds':45,'observer_timer_seconds':10,'sidecar_bytes':16777216,
            'sidecar_seconds':60,'stdout_stderr_bytes':65536,'records':128},
        'existing_environment_adoption':False,'production_approved':False}
    write('BUILD_RECEIPT.json',enc(receipt));print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':main()
