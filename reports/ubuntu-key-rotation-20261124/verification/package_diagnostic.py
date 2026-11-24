"""Package an explicitly reviewed new isolated lab; no remote action or worker execution."""
from pathlib import Path
import argparse,ast,gzip,hashlib,io,json,re,tarfile,subprocess
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE=Path(__file__).resolve().parent
OLD=V/'ubuntu-complete-20261124/keeper-lp-jobs'
TARGETS={'rotation-diagnostic':'c802'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda data:(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
def write(path,raw):
    if path.exists():assert path.read_bytes()==raw,path;return
    with path.open('xb')as stream:stream.write(raw)
def main():
    p=argparse.ArgumentParser();p.add_argument('feature',choices=TARGETS);args=p.parse_args()
    folder=BASE/args.feature;tag=TARGETS[args.feature];feature=args.feature.removesuffix('-diagnostic');stem='popl-ubuntu-key-'+feature+'-20261124-'+tag
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
    query=b''.join(('55e90d7d665bd3a310db163d95f2dba51083ae0b:'+name.removeprefix('source/contracts/')+'\n').encode()for name in names)
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
    source_meta={'schema':1,'source_head':'55e90d7d665bd3a310db163d95f2dba51083ae0b',
      'byte_equal_to_base_HEAD':True,'frozen_F6_Solidity_modified':False,
      'unrelated_dirty_worktree_files_excluded':True,
      'members':{row['path']:{'bytes':row['bytes'],'sha256':row['sha256']}for row in current},
      'prior_source_manifest_sha256':sha(original['inputs/SOURCE_MANIFEST.json']),
      'current_overrides_from_prior':changed_from_base}
    members['inputs/SOURCE_MANIFEST.json']=enc(source_meta)
    helpers={}
    for name in('keeper_runtime.py','keeper_jobs.py','job_cases.py','run_jobs.py'):
        path=folder/name
        if name=='keeper_runtime.py'and not path.exists():write(path,original['source/helpers/'+name])
        raw=path.read_bytes();ast.parse(raw,filename=name);helpers[name]=raw;members['source/helpers/'+name]=raw
    assert lab.encode()in helpers['keeper_jobs.py']
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
      'scope':'NEW_missing_'+args.feature+'_positive_partition_no_old_test_bodies',
      'current_source_commit':'55e90d7d665bd3a310db163d95f2dba51083ae0b',
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
    constant('BUNDLE_SHA',sha(bundle));constant('MANIFEST_SHA',sha(manifest_raw));constant('WORKER_SHA',sha(helpers['run_jobs.py']));constant('UTILITY_SHA',sha(helpers['keeper_jobs.py']));constant('INDEXER_SHA',sha(helpers['job_cases.py']));constant('ALLOWED',tuple(sorted(members)))
    sourcehash=sha(members['inputs/SOURCE_MANIFEST.json']);constant('SOURCE_MANIFEST_SHA',sourcehash)
    pattern=r"^    for name,digest in .*:require\(sha\(data\['source/helpers/'\+name\]\)==digest,'Reviewed helper differs'\)$"
    controller,count=re.subn(pattern,lambda m:"    for name,digest in "+repr(tuple((name,sha(raw))for name,raw in helpers.items()))+":require(sha(data['source/helpers/'+name])==digest,'Reviewed helper differs')",controller,flags=re.M);assert count==1
    public={'SUMMARY.json':None,'RESULT.json':'jobs/RESULT.json','FAILURE.json':None,'CLEANUP.json':None,'EVENTS.json':'jobs/EVENTS.json','controller.stdout.log':'controller.stdout.log','controller.stderr.log':'controller.stderr.log'}
    names=('BINDINGS','BINDING_REFUSAL','RESULT','SETUP','RECEIPTS','RAW_REVIEWS','CLOCK_REPAIR','FEE_MODEL','FEE_READBACK','FEE_READBACK-BEFORE_JOB','FEE_READBACK-AFTER_INPUT_REPAIR','ANVIL_HELP_REVIEW','CONTROLLED_FEES','FINAL_ACCOUNTING_VIEWS','CONFIRMED_ANCHOR','MARKET_MOVE','CONVERSION_REVIEW','CONVERSION_BEFORE','CONVERSION_AFTER','DEPTH_REVIEW','ACCOUNTING_REVIEW','BURN_PRE_REVIEW','BURN_REVIEW','SUPPLY_RESTORE','PRE_ON','POST_ON','MODE_OFF_PENDING','POST_OFF','CLOCK_BOUNDARY','HYBRID_REVIEW','REPLACEMENT_ON','REPLACEMENT_OFF','FAILED_REVIEW','MODE_ON','MODE_OFF',*(f'RAW_RECEIPT-{i:02d}'for i in range(1,13)),*(f'CYCLE-{i:02d}'for i in range(1,15)))
    names += ('CLOCK_SEAM','LOGICAL_CLOCK_TRANSITION','TOGGLE_ON','TOGGLE_OFF','BEFORE_ON','AFTER_ON','REVIEW_ON','BEFORE_OFF','AFTER_OFF','REVIEW_OFF','MIXED_RESIDUAL')
    extra_public=prepared['public_records'];assert type(extra_public)is list and len(extra_public)<=40
    assert all(type(n)is str and re.fullmatch('[A-Z0-9_]+',n)for n in extra_public)
    names+=tuple(extra_public)
    # Labels are fixed in the reviewed worker and may use confirmation/buyback.
    for label in(feature,{'rebalance':'confirmation','burn':'buyback'}.get(feature,feature)):
        for name in names:public[label+'-'+name+'.json']='jobs/'+label+'/'+name+'.json'
    constant('PUBLIC_PATHS',public)
    ast.parse(controller,filename='remote_capsule.py');write(folder/'remote_capsule.py',controller.encode())
    host=(OLD/'host_control.py').read_text().replace('ubuntu-complete-20261124/keeper-lp-jobs','ubuntu-key-rotation-20261124/'+args.feature).replace(oldstem,stem)
    ast.parse(host,filename='host_control.py');write(folder/'host_control.py',host.encode())
    receipt={'schema':1,'feature':args.feature,'bundle':pin(bundle),'manifest':pin(manifest_raw),'lab':lab,'helpers':{name:pin(raw)for name,raw in helpers.items()},'controller':pin(controller.encode()),'host_wrapper':pin(host.encode()),'source_manifest_sha256':sourcehash,'current_production_members_byte_identical':len(current),'source_updates_from_previous_bundle':changed_from_base,'production_sources_changed':False,'remote_actions':0,'runtime_executed':False,'extra_reviewed_inputs':extra,'limits':{'RPC_requests':6000,'worker_seconds':900,'maintenance_gas':24000000,'padding_percent':25,'single_maximum_cost_wei':str(10**16),'daily_maximum_cost_wei':str(5*10**16),'confirmations':12}}
    write(folder/'BUILD_RECEIPT.json',enc(receipt));print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
