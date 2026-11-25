"""Package separate c806 Cast interruption; offline assembly only, no lab execution."""
from pathlib import Path
import argparse,ast,gzip,hashlib,io,json,re,tarfile,subprocess
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE=Path(__file__).resolve().parent
OLD=V/'ubuntu-complete-20261124/keeper-lp-jobs'
TARGETS={'signer':'c806'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda data:(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
def write(path,raw):
    if path.exists():assert path.read_bytes()==raw,path;return
    with path.open('xb')as stream:stream.write(raw)
def main():
    p=argparse.ArgumentParser();p.add_argument('feature',choices=TARGETS);args=p.parse_args()
    folder=BASE/args.feature;tag=TARGETS[args.feature];feature=args.feature.removesuffix('-fee-retry');stem='popl-ubuntu-supervisor-20261125-'+tag
    lab='/opt/'+stem
    original_raw=(OLD/'c7f0.inputs.tar.gz').read_bytes()
    assert sha(original_raw)=='e1b14a9b883e3dba45e0ede5fc0ffe0efbee8e3e32ade16e6db21c0c0632694a'
    with tarfile.open(fileobj=io.BytesIO(original_raw),mode='r:gz')as archive:
        original={m.name:archive.extractfile(m).read()for m in archive if m.isfile()}
    oldmanifest=json.loads(original['MANIFEST.json'])
    for name,row in oldmanifest['members'].items():assert pin(original[name])==row
    members={n:raw for n,raw in original.items()if n.startswith('source/contracts/')or n.startswith('inputs/')}
    current=[];changed_from_base=[]
    names=[name for name in members if name.startswith('source/contracts/')]
    query=b''.join(('7f862557df8e8cbaf8494c7b1c12f18e07be436d:'+name.removeprefix('source/contracts/')+'\n').encode()for name in names)
    objects=subprocess.run(['git','cat-file','--batch'],input=query,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=True).stdout
    offset=0;published={}
    for name in names:
        end=objects.index(b'\n',offset);header=objects[offset:end].split();assert len(header)==3 and header[1]==b'blob'
        length=int(header[2]);offset=end+1;published[name]=objects[offset:offset+length];offset+=length+1;assert objects[offset-1:offset]==b'\n'
    assert offset==len(objects)
    for name,raw in list(members.items()):
        if name.startswith('source/contracts/'):
            path=ROOT/name.removeprefix('source/contracts/')
            actual=published[name]
            relative=str(path.relative_to(ROOT)).replace('\\','/')
            assert actual==path.read_bytes()or relative=='scripts/run-fork-checks.py','Unreviewed working source difference'
            if actual!=raw:
                expected={'keeper/staging-install.sh':'b66878fee51f54ac36656646d41f57e70955b9b43c5aff228b5ecd02b3e258b3','scripts/verify.sh':'0a3e54ce89fadb434aaf032299db8a1aa955bd41d0108f1e209a26ce4328598f'}
                assert relative in expected and sha(actual)==expected[relative],relative
                changed_from_base.append({'path':relative,'original':pin(raw),'current':pin(actual),'not_executed_by_jobs':True})
            members[name]=actual
            current.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),**pin(actual)})
    source_meta={'schema':1,'source_head':'7f862557df8e8cbaf8494c7b1c12f18e07be436d',
      'byte_equal_to_base_HEAD':True,'frozen_F6_Solidity_modified':False,
      'unrelated_dirty_worktree_files_excluded':True,
      'members':{row['path']:{'bytes':row['bytes'],'sha256':row['sha256']}for row in current},
      'prior_source_manifest_sha256':sha(original['inputs/SOURCE_MANIFEST.json']),
      'current_overrides_from_prior':changed_from_base}
    members['inputs/SOURCE_MANIFEST.json']=enc(source_meta)
    helpers={}
    for name in('keeper_runtime.py','keeper_jobs.py','job_cases.py','model_service_base.py','model_service.py','native_control.py'):
        path=folder/name
        if name=='keeper_runtime.py'and not path.exists():write(path,original['source/helpers/'+name])
        raw=path.read_bytes();ast.parse(raw,filename=name);helpers[name]=raw;members['source/helpers/'+name]=raw
    assert lab.encode()in helpers['model_service.py']
    assert sha(helpers['model_service_base.py'])=='9054e71cd737a95185dc9228d7ccfac114b8bb227df0baddab1953f2fef23bda','Exact preserved c804 model dependency differs'
    assert helpers['model_service_base.py']==(BASE/'body/model_service.py').read_bytes(),'Preserved c804 dependency changed'
    prepared=json.loads((folder/'PREPARED_HELPERS.json').read_bytes())
    assert prepared['remote_root']==lab
    for name,raw in helpers.items():assert pin(raw)==prepared['helper_pins'][name]
    extra_path=folder/'DRAFT_INPUTS.json'
    extra=json.loads(extra_path.read_bytes())if extra_path.exists()else[]
    if type(extra)is dict:
        for row in extra['helpers']:assert pin(helpers[row['file']])=={'bytes':row['bytes'],'sha256':row['sha256']}
        selected=[]
        for row in extra['extra_reviewed_inputs']:
            assert row['target']=='inputs/'+row['local']
            assert pin((folder/row['local']).read_bytes())=={'bytes':row['bytes'],'sha256':row['sha256']}
            selected.append(row['local'])
        extra=selected
    assert type(extra)is list and len(extra)<=8
    for name in extra:
        assert type(name)is str and re.fullmatch('[A-Z0-9_]+\\.json',name)
        raw=(folder/name).read_bytes();assert len(raw)<=16*1024*1024
        json.loads(raw);members['inputs/'+name]=raw
    manifest={**{k:v for k,v in oldmanifest.items()if k!='members'},
      'scope':'NEW_actual_Cast_cleanup_after_deliberate_main_kill_hashless_block_explicit_stock_resolution_no_old_test_bodies',
      'current_source_commit':'7f862557df8e8cbaf8494c7b1c12f18e07be436d',
      'lab_only_controlled_fees_not_target_fee_qualification':True,
      'members':{n:pin(raw)for n,raw in members.items()}}
    manifest_raw=enc(manifest);members['MANIFEST.json']=manifest_raw
    buffer=io.BytesIO()
    with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0,filename='')as gz:
        with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT)as archive:
            for name,raw in sorted(members.items()):
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o444;item.uid=item.gid=0;item.uname=item.gname='root';item.mtime=0;archive.addfile(item,io.BytesIO(raw))
    bundle=buffer.getvalue();assert len(bundle)<=96*1024*1024
    write(folder/(tag+'.inputs.tar.gz'),bundle)
    controller=(OLD/'remote_capsule.py').read_text()
    oldstem='popl-ubuntu-lp-jobs-20261124-c7f0';controller=controller.replace(oldstem,stem)
    def constant(name,value):
        nonlocal controller
        controller,count=re.subn(r'^'+name+r'=.*$',lambda m:name+'='+repr(value),controller,flags=re.M);assert count==1,name
    constant('BUNDLE_SHA',sha(bundle));constant('MANIFEST_SHA',sha(manifest_raw));constant('WORKER_SHA',sha(helpers['model_service.py']));constant('UTILITY_SHA',sha(helpers['keeper_jobs.py']));constant('INDEXER_SHA',sha(helpers['job_cases.py']));constant('ALLOWED',tuple(sorted(members)))
    sourcehash=sha(members['inputs/SOURCE_MANIFEST.json']);constant('SOURCE_MANIFEST_SHA',sourcehash)
    pattern=r"^    for name,digest in .*:require\(sha\(data\['source/helpers/'\+name\]\)==digest,'Reviewed helper differs'\)$"
    controller,count=re.subn(pattern,lambda m:"    for name,digest in "+repr(tuple((name,sha(raw))for name,raw in helpers.items()))+":require(sha(data['source/helpers/'+name])==digest,'Reviewed helper differs')",controller,flags=re.M);assert count==1
    public={}
    for name in ('READY','COMPLETE','RESULT','EVENTS'):
        public['model-'+name+'.json']=('model','model/'+name+'.json')
    for name in ('BINDINGS','BINDING_REFUSAL','CLOCK_REPAIR','INITIAL_JOURNAL','FINANCIAL_BEFORE','CAST_REPLY_HELD','CAST_CLIENT_CLOSED','HELD_REPLY_RETURNED','HASHLESS_RESTART_BLOCKED','RECOVERED_JOURNAL','HEALTHY_NORMAL_CYCLE','FINANCIAL_AFTER','FRONTEND_REFUSAL','SETUP','RECEIPTS','RAW_REVIEWS','RESULT'):
        public['case-'+name+'.json']=('model','model/supervisor/'+name+'.json')
    for name in ('BASELINE','WITNESS_STATE','SIGNER_KILL','NATIVE_RESTART_PROOF','JOURNAL_DURING_RESTART','STOP_KEEPER','RESOLUTION_REQUEST','RESOLUTION_COMPLETE','NORMAL_RESUME'):
        public['native-'+name+'.json']=('control',name+'.json')
    for kind in ('model','keeper','resolve'):
        for stream in ('stdout','stderr'):
            public['native-'+kind+'.'+stream+'.log']=('model','native-'+kind+'.'+stream+'.log')
    constant('PUBLIC_PATHS',public)
    constant('UNIT',stem+'-model.service')
    native_pins={'source_manifest_sha256':sourcehash,'base_sha256':sha(helpers['keeper_runtime.py']),'jobs_sha256':sha(helpers['keeper_jobs.py']),'cases_sha256':sha(helpers['job_cases.py']),'model_sha256':sha(helpers['model_service.py']),'base_model_sha256':sha(helpers['model_service_base.py'])}
    extension=(BASE/'capsule_extension_signer.py').read_text().replace('__NATIVE_PINS__',repr(native_pins)).replace('__NATIVE_SHA__',repr(sha(helpers['native_control.py'])))
    controller=controller.replace("choices=('install','start','status','stop','fetch')","choices=('install','start','startkeeper','killmain','observe','stopkeeper','resolve','resume','status','stop','fetch')")
    controller=controller.replace('a=parser.parse_args()\n    try:',"a=parser.parse_args()\n    globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256\n    try:")
    controller=controller.replace("if __name__=='__main__':main()",extension+"\nif __name__=='__main__':main()")
    ast.parse(controller,filename='remote_capsule.py');write(folder/'remote_capsule.py',controller.encode())
    host=(OLD/'host_control.py').read_text().replace('ubuntu-complete-20261124/keeper-lp-jobs','ubuntu-supervisor-20261125/'+args.feature).replace(oldstem,stem)
    host=host.replace("('validate-bundle','upload','install','start','status','stop','fetch')","('validate-bundle','upload','install','start','startkeeper','killmain','observe','stopkeeper','resolve','resume','status','stop','fetch')")
    ast.parse(host,filename='host_control.py');write(folder/'host_control.py',host.encode())
    receipt={'schema':1,'feature':args.feature,'bundle':pin(bundle),'manifest':pin(manifest_raw),'lab':lab,'helpers':{name:pin(raw)for name,raw in helpers.items()},'controller':pin(controller.encode()),'host_wrapper':pin(host.encode()),'source_manifest_sha256':sourcehash,'current_production_members_byte_identical':len(current),'source_updates_from_previous_bundle':changed_from_base,'production_sources_changed':False,'remote_actions':0,'runtime_executed':False,'old_test_bodies_run':0,'manual_main_kill_not_watchdog':True,'base_model_dependency_sha256':sha(helpers['model_service_base.py']),'extra_reviewed_inputs':extra,'limits':{'RPC_requests':6000,'worker_seconds':900,'maintenance_gas':24000000,'padding_percent':25,'single_maximum_cost_wei':str(10**16),'daily_maximum_cost_wei':str(5*10**16),'confirmations':12,'combined_fixture_memory_MiB':2048,'combined_fixture_CPU_percent':150,'combined_fixture_tasks':128}}
    write(folder/'BUILD_RECEIPT.json',enc(receipt));print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
