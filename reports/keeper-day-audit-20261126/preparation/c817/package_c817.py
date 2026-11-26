"""Offline pinned closure and explicit affected-method preparation; no run."""
from pathlib import Path
import argparse,ast,gzip,hashlib,io,json,os,subprocess,sys,tarfile

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
HEAD='1cc67c50ece5b41fbd8c78b902ceb7ab70f96914'
NEW=('tests_python/test_keeper_backup_audit.py','tests_python/test_keeper_alert_audit.py','tests_python/test_keeper_process_audit.py')
OVERRIDES=('keeper/recovery_bundle.py','keeper/alerts.py','keeper/cast_process.py','zzz_ops/read_process.py')
CLASSES=dict(zip(NEW,('KeeperBackupAuditTests','KeeperAlertAuditTests','KeeperProcessAuditTests')))
PREPARATION=('package_c817.py','capsule_template.py','run_selected_template.py','host_control.py','orchestrate_c817.py')
STATIC=('reports/ubuntu-backup-recovery-20261126/evidence/c814/model-DRY.json',
 'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json')
HEALTH=('keeper/monitor.py','keeper/ops.py','keeper/health.py','keeper/rebalance_confirmation.py',
 'keeper/compound_policy.py','keeper/cast_process.py','zzz_ops/protocol_policy.py','zzz_ops/lp_execution.py',
 'zzz_ops/execution_price.py','zzz_ops/rebalance_confirmation.py','zzz_ops/abi.py','zzz_ops/rpc.py','zzz_ops/state.py')
OBSERVER=('keeper/alerts.py','scripts/keeper-alerts.py','keeper/recovery_bundle.py','scripts/keeper-recovery.py')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
enc=lambda value:(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()

def git(*args):
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1')
    result=subprocess.run(['git',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
    assert len(result.stdout)<=8*1024*1024
    return result.stdout

def write(name,raw):
    with(BASE/name).open('xb')as f:f.write(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('--review-pins',type=Path,required=True);a=p.parse_args()
    review=json.loads(a.review_pins.read_bytes())
    assert set(review)=={'source_head','reviewed_worktree_files','reviewed_preparation_files','selection'}and review['source_head']==HEAD
    assert set(review['reviewed_worktree_files'])==set(NEW+OVERRIDES)
    assert set(review['reviewed_preparation_files'])==set(PREPARATION)
    preparation={}
    for name in PREPARATION:
        raw=(BASE/name).read_bytes();assert sha(raw)==review['reviewed_preparation_files'][name]
        if name!='capsule_template.py'and name!='run_selected_template.py':ast.parse(raw,filename=name)
        preparation[name]=raw
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    names=set(git('ls-tree','-r','--name-only',HEAD).decode().splitlines());overrides={}
    for name in NEW+OVERRIDES:
        path=ROOT/name;assert path.is_file()and not path.is_symlink()
        raw=path.read_bytes();assert len(raw)<=1024*1024 and sha(raw)==review['reviewed_worktree_files'][name]
        ast.parse(raw,filename=name);overrides[name]=raw
    assert all(name not in names for name in NEW)and all(name in names for name in OVERRIDES)
    selection=review['selection'];assert type(selection)is list and len(selection)==1
    selected=[];selected_ast={};seen=set()
    for row in selection:
        assert type(row)is dict and set(row)=={'file','class','methods'}and row['file']not in seen
        assert CLASSES[row['file']]==row['class'];seen.add(row['file'])
        tree=ast.parse(overrides[row['file']]);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==row['class'])
        assert len(cls.bases)==1 and isinstance(cls.bases[0],ast.Attribute)and cls.bases[0].attr=='TestCase'
        methods={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name.startswith('test_')}
        assert type(row['methods'])is list and len(row['methods'])==len(set(row['methods']))and row['file']=='tests_python/test_keeper_alert_audit.py' and row['methods']==['test_actual_observer_source_change_alerts_without_resetting_pending_age'] and set(row['methods'])<=set(methods)
        for name in row['methods']:
            identifier=row['class']+'.'+name;selected.append(identifier)
            selected_ast[identifier]=sha(ast.dump(methods[name],include_attributes=False).encode())
    assert seen=={'tests_python/test_keeper_alert_audit.py'}and len(selected)==1 and len(selected)==len(set(selected))
    members={};source_rows={};import_edges={};queue=list(NEW+HEALTH+OBSERVER)
    def project_path(module):
        stem=module.replace('.','/')
        for path in(stem+'.py',stem+'/__init__.py'):
            if path in names or path in overrides:return path
    while queue:
        name=queue.pop(0)
        if name in source_rows:continue
        assert len(source_rows)<256
        raw=overrides[name]if name in overrides else git('show',HEAD+':'+name)
        assert len(raw)<=1024*1024
        tree=ast.parse(raw,filename=name);members['source/'+name]=raw
        source_rows[name]={'stage':'new_reviewed_source'if name in NEW else'reviewed_worktree_override'if name in OVERRIDES else'exact_HEAD',**pin(raw)}
        parts=name.split('/')
        for count in range(1,len(parts)):
            package='/'.join(parts[:count])+'/__init__.py'
            if package in names and package not in source_rows:queue.append(package)
        dependencies=set()
        for node in ast.walk(tree):
            requested=[]
            if isinstance(node,ast.Import):requested=[alias.name for alias in node.names]
            elif isinstance(node,ast.ImportFrom):
                module=node.module or''
                if node.level:
                    package=name.removesuffix('.py').replace('/','.').split('.')[:-1]
                    module='.'.join(package[:len(package)-node.level+1]+([module]if module else[]))
                requested=[module,*[module+'.'+alias.name for alias in node.names if alias.name!='*']]
            for module in requested:
                path=project_path(module)
                if path is not None:dependencies.add(path)
                elif module.split('.')[0]not in('keeper','zzz_ops','frontend_api','indexer','scripts','tests_python'):
                    assert module.split('.')[0]in sys.stdlib_module_names,('Unreviewed dependency',name,module)
        import_edges[name]=sorted(dependencies);queue.extend(sorted(dependencies))
    for name in STATIC:
        raw=(ROOT/name).read_bytes();assert raw==git('show',HEAD+':'+name)and len(raw)<=1024*1024
        members['source/'+name]=raw
    template=preparation['run_selected_template.py'].decode()
    runner=template.replace('__SELECTION__',repr(tuple(selection))).replace('__SELECTED__',repr(tuple(selected)))
    ast.parse(runner);members['source/run_selected.py']=runner.encode()
    manifest={'schema':1,'source_head':HEAD,'selection':selection,'selected_methods':selected,
        'selected_method_AST_sha256':selected_ast,'source_files':source_rows,'static_import_edges':import_edges,
        'explicit_reviewed_worktree_overrides':list(OVERRIDES),'new_reviewed_files':list(NEW),
        'health_source_changed_files':['keeper/cast_process.py'],'health_sources':list(HEALTH),
        'observer_core_cli_producer_files':list(OBSERVER),'reviewed_preparation_sha256':review['reviewed_preparation_files'],
        'static_published_JSON_only':list(STATIC),'old_test_helpers_imported_not_test_bodies':['tests_python/test_keeper_alerts.py'],
        'affected_method_rerun':True,'original_campaign':'c816','previously_green_methods_run':0,'all_selected_methods_NEW_and_not_previously_executed':False,'old_test_bodies':0,
        'only_private_loopback_HTTP_and_same_process_SIGINT':True,'Anvil_Cast_signer_or_service_adoption':False,
        'members':{n:pin(b)for n,b in members.items()}}
    source_raw=enc(manifest);members['SOURCE_MANIFEST.json']=source_raw
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0)as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT)as archive:
            for name,raw in sorted(members.items()):
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o444;item.uid=item.gid=0;item.uname=item.gname='root';item.mtime=0
                archive.addfile(item,io.BytesIO(raw))
    bundle=out.getvalue();assert len(bundle)<=2*1024*1024 and sum(map(len,members.values()))<=8*1024*1024
    capsule=preparation['capsule_template.py'].decode().replace('__MEMBERS__',repr({n:pin(b)for n,b in members.items()})).replace('__BUNDLE_SHA__',repr(sha(bundle))).replace('__SOURCE_MANIFEST_SHA__',repr(sha(source_raw))).replace('__SELECTED__',repr(tuple(selected)))
    ast.parse(capsule);assert len(capsule.encode())<=65536
    # No template/core may drift during generation. Never package first and
    # later pretend a different template was the reviewed one.
    assert all((BASE/n).read_bytes()==raw for n,raw in preparation.items())
    assert all((ROOT/n).read_bytes()==raw for n,raw in overrides.items())
    write('c817.inputs.tar.gz',bundle);write('SOURCE_MANIFEST.json',source_raw);write('run_selected.py',runner.encode());write('remote_capsule.py',capsule.encode())
    build={'schema':1,'bundle':pin(bundle),'controller':pin(capsule.encode()),'source_manifest':pin(source_raw),'runner':pin(runner.encode()),
        'source_head':HEAD,'source_members':len(source_rows),'archive_members':len(members),'selected_affected_methods':selected,'affected_method_rerun':True,'previously_green_methods_run':0,
        'health_identity_changed_files':['keeper/cast_process.py'],'existing_environments_adopted':False,
        'tests_run':0,'network_actions':0,'unit':'popl-keeper-day-audit-20261126-c817.service',
        'work_seconds':180,'combined_output_bytes':65536,'stop_seconds':2}
    write('BUILD_RECEIPT.json',enc(build));print(json.dumps(build,sort_keys=True))

if __name__=='__main__':main()
