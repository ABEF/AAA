"""Offline AST source closure and exact NEW-method capsule preparation."""
from pathlib import Path
import argparse,ast,gzip,hashlib,io,json,os,subprocess,sys,tarfile

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
HEAD='fe2db714e0ef14252cf43f8afb7c1f0d772c1bbd'
NEW=('keeper/alerts.py','scripts/keeper-alerts.py','tests_python/test_keeper_alerts.py')
OVERRIDES=('keeper/ops.py',)
STATIC=('reports/ubuntu-backup-recovery-20261126/evidence/c814/model-DRY.json',
 'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json')
HEALTH=('keeper/monitor.py','keeper/ops.py','keeper/health.py','keeper/rebalance_confirmation.py',
 'keeper/compound_policy.py','keeper/cast_process.py','zzz_ops/protocol_policy.py','zzz_ops/lp_execution.py',
 'zzz_ops/execution_price.py','zzz_ops/rebalance_confirmation.py','zzz_ops/abi.py','zzz_ops/rpc.py','zzz_ops/state.py')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
enc=lambda value:(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()

def git(*args):
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1')
    result=subprocess.run(['git',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
    assert len(result.stdout)<=8*1024*1024
    return result.stdout

def write(name,raw):
    with (BASE/name).open('xb')as f:f.write(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('--review-pins',type=Path,required=True);a=p.parse_args()
    review=json.loads(a.review_pins.read_bytes())
    assert set(review)=={'source_head','reviewed_worktree_files','selected_methods'}and review['source_head']==HEAD
    assert set(review['reviewed_worktree_files'])==set(NEW+OVERRIDES)
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    names=set(git('ls-tree','-r','--name-only',HEAD).decode().splitlines());overrides={}
    for name in NEW+OVERRIDES:
        path=ROOT/name;assert path.is_file()and not path.is_symlink()
        raw=path.read_bytes();assert len(raw)<=1024*1024 and sha(raw)==review['reviewed_worktree_files'][name]
        ast.parse(raw,filename=name);overrides[name]=raw
    for name in NEW:assert name not in names
    assert all(name in names for name in OVERRIDES)
    members={};source_rows={};import_edges={};queue=list(NEW+HEALTH+('scripts/keeper-recovery.py',))
    def project_path(module):
        stem=module.replace('.','/')
        for path in (stem+'.py',stem+'/__init__.py'):
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
                elif module.split('.')[0]not in ('keeper','zzz_ops','frontend_api','indexer','scripts','tests_python'):
                    assert module.split('.')[0]in sys.stdlib_module_names,('Unreviewed dependency',name,module)
        import_edges[name]=sorted(dependencies);queue.extend(sorted(dependencies))
    test_tree=ast.parse(overrides['tests_python/test_keeper_alerts.py'])
    cls=next(n for n in test_tree.body if isinstance(n,ast.ClassDef)and n.name=='KeeperAlertsTests')
    methods={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name.startswith('test_')}
    selected=tuple(review['selected_methods']);assert len(selected)==len(set(selected))and set(selected)==set(methods)
    selected_ast={n:sha(ast.dump(methods[n],include_attributes=False).encode())for n in selected}
    for name in STATIC:
        raw=(ROOT/name).read_bytes();assert raw==git('show',HEAD+':'+name)and len(raw)<=1024*1024
        members['source/'+name]=raw
    template=(BASE/'run_selected_template.py').read_text()
    runner=template.replace('__SELECTED__',repr(selected)).replace('__CLASS__',repr('KeeperAlertsTests')).replace('__TEST_FILE__',repr('tests_python/test_keeper_alerts.py'))
    ast.parse(runner);members['source/run_selected.py']=runner.encode()
    source_manifest={'schema':1,'source_head':HEAD,'selected_class':'KeeperAlertsTests','selected_methods':list(selected),
        'selected_method_AST_sha256':selected_ast,'source_files':source_rows,'static_import_edges':import_edges,
        'explicit_reviewed_worktree_overrides':list(OVERRIDES),'new_reviewed_files':list(NEW),
        'health_source_changed_files':['keeper/ops.py'],'health_sources':list(HEALTH),
        'static_published_JSON_only':list(STATIC),'all_methods_NEW_and_not_previously_executed':True,
        'only_loopback_HTTP_inside_private_network':True,'old_test_bodies':0,'Anvil_Cast_signer_or_service_adoption':False,
        'members':{n:pin(b)for n,b in members.items()}}
    source_raw=enc(source_manifest);members['SOURCE_MANIFEST.json']=source_raw
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0)as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT)as archive:
            for name,raw in sorted(members.items()):
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o444;item.uid=item.gid=0;item.uname=item.gname='root';item.mtime=0
                archive.addfile(item,io.BytesIO(raw))
    bundle=out.getvalue();assert len(bundle)<=2*1024*1024 and sum(len(b)for b in members.values())<=8*1024*1024
    capsule=(BASE/'capsule_template.py').read_text().replace('__MEMBERS__',repr({n:pin(b)for n,b in members.items()})).replace('__BUNDLE_SHA__',repr(sha(bundle))).replace('__SOURCE_MANIFEST_SHA__',repr(sha(source_raw))).replace('__SELECTED__',repr(selected))
    ast.parse(capsule);assert len(capsule.encode())<=65536
    write('c815.inputs.tar.gz',bundle);write('SOURCE_MANIFEST.json',source_raw);write('run_selected.py',runner.encode());write('remote_capsule.py',capsule.encode())
    build={'schema':1,'bundle':pin(bundle),'controller':pin(capsule.encode()),'source_manifest':pin(source_raw),'runner':pin(runner.encode()),
        'source_head':HEAD,'source_members':len(source_rows),'archive_members':len(members),'selected_NEW_methods':list(selected),
        'health_identity_changed_files':['keeper/ops.py'],'existing_environments_adopted':False,'tests_run':0,'network_actions':0,
        'unit':'popl-keeper-alerts-20261126-c815.service','work_seconds':180,'combined_output_bytes':65536,'stop_seconds':2}
    write('BUILD_RECEIPT.json',enc(build));print(json.dumps(build,sort_keys=True))

if __name__=='__main__':main()
