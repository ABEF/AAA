"""Prepare a closed c808 source bundle/controller; no network or worker execution."""
from pathlib import Path
import argparse,ast,gzip,hashlib,io,json,re,subprocess,tarfile
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE=Path(__file__).resolve().parent
OLD=V/'ubuntu-complete-20261124/keeper-lp-jobs'
FOLDER=BASE/'c808'
HEAD='352ebe0aa479a10f2220857edadbf049720616c5'
REVIEWED_MONITOR_SHA='5ab6bbb20eea21e301d81d2e829a827594079561e2f10770336ec8585b234631'
REVIEWED_VERIFY_SHA='fec6b85a42d95d2015cb77653b8e5d844e7e117949e2b230af3cf171d548aaf1'
STEM='popl-ubuntu-storage-20261125-c808'
LAB='/opt/'+STEM
FROZEN={'keeper_runtime.py':'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4','keeper_jobs.py':'363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4','job_cases.py':'7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'}
sha=lambda b:hashlib.sha256(b).hexdigest()
pin=lambda b:{'bytes':len(b),'sha256':sha(b)}
enc=lambda j:(json.dumps(j,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def write(p,b):
 if p.exists():assert p.read_bytes()==b,p
 else:
  with p.open('xb')as f:f.write(b)
def main():
 p=argparse.ArgumentParser();p.add_argument('--monitor-sha256',required=True);p.add_argument('--worker-sha256',required=True);args=p.parse_args()
 assert args.monitor_sha256==REVIEWED_MONITOR_SHA and re.fullmatch('[0-9a-f]{64}',args.worker_sha256)
 originalraw=(OLD/'c7f0.inputs.tar.gz').read_bytes();assert sha(originalraw)=='e1b14a9b883e3dba45e0ede5fc0ffe0efbee8e3e32ade16e6db21c0c0632694a'
 with tarfile.open(fileobj=io.BytesIO(originalraw),mode='r:gz')as arc:original={m.name:arc.extractfile(m).read()for m in arc if m.isfile()}
 prior=json.loads(original['MANIFEST.json'])
 for name,expected in prior['members'].items():assert pin(original[name])==expected
 members={n:b for n,b in original.items()if n.startswith('source/contracts/')or n.startswith('inputs/')}
 names=[n for n in members if n.startswith('source/contracts/')];assert len(names)==190
 query=b''.join((HEAD+':'+n.removeprefix('source/contracts/')+'\n').encode()for n in names)
 out=subprocess.run(['git','cat-file','--batch'],input=query,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=60).stdout
 offset=0;published={}
 for name in names:
  end=out.index(b'\n',offset);header=out[offset:end].split();assert len(header)==3 and header[1]==b'blob';size=int(header[2]);offset=end+1;published[name]=out[offset:offset+size];offset+=size+1;assert out[offset-1:offset]==b'\n'
 assert offset==len(out)
 current={};fromprior=[];overrides=[]
 expectedcontrol={'keeper/staging-install.sh':'b66878fee51f54ac36656646d41f57e70955b9b43c5aff228b5ecd02b3e258b3','scripts/verify.sh':'0a3e54ce89fadb434aaf032299db8a1aa955bd41d0108f1e209a26ce4328598f'}
 for name in names:
  rel=name.removeprefix('source/contracts/');baseline=published[name];raw=(ROOT/rel).read_bytes()
  if rel=='keeper/monitor.py':
   assert sha(raw)==args.monitor_sha256 and raw!=baseline
   overrides.append({'path':rel,'published':pin(baseline),'current':pin(raw),'scope':'bounded errno storage diagnostics only'})
  elif rel=='scripts/verify.sh':
   assert sha(raw)==REVIEWED_VERIFY_SHA and raw!=baseline
   overrides.append({'path':rel,'published':pin(baseline),'current':pin(raw),'scope':'current workload inventory pointer only; not executed by lab'})
  elif rel=='scripts/run-fork-checks.py':raw=baseline
  else:assert raw==baseline,'Unreviewed source difference: '+rel
  if baseline!=original[name]:assert rel in expectedcontrol and sha(baseline)==expectedcontrol[rel];fromprior.append({'path':rel,'original':pin(original[name]),'published':pin(baseline),'not_executed_by_job':True})
  members[name]=raw;current[rel]=pin(raw)
 source={'schema':1,'source_head':HEAD,'byte_equal_to_base_HEAD':False,'frozen_F6_Solidity_modified':False,'unrelated_dirty_worktree_files_excluded':True,'members':current,'prior_source_manifest_sha256':sha(original['inputs/SOURCE_MANIFEST.json']),'current_overrides_from_prior':fromprior,'approved_worktree_overrides':overrides}
 assert len(overrides)==2
 members['inputs/SOURCE_MANIFEST.json']=enc(source);sourcehash=sha(members['inputs/SOURCE_MANIFEST.json'])
 helpers={}
 for name in(*FROZEN,'run_storage.py'):
  raw=(FOLDER/name).read_bytes();ast.parse(raw,filename=name)
  assert sha(raw)==(FROZEN[name]if name in FROZEN else args.worker_sha256)
  helpers[name]=raw;members['source/helpers/'+name]=raw
 assert LAB.encode()in helpers['run_storage.py']
 prepared={'remote_root':LAB,'helper_pins':{n:pin(b)for n,b in helpers.items()},'public_records':[]}
 write(FOLDER/'PREPARED_HELPERS.json',enc(prepared))
 manifest={**{k:v for k,v in prior.items()if k!='members'},'scope':'NEW_isolated_OS_storage_failure_intent_hash_receipt_no_old_test_bodies','current_source_commit':HEAD,'approved_worktree_overrides':overrides,'namespace_private_tmpfs_bytes':1048576,'physical_host_disk_filled':False,'lab_only_controlled_fees_not_target_fee_qualification':True,'members':{n:pin(b)for n,b in members.items()}}
 manifestbytes=enc(manifest);members['MANIFEST.json']=manifestbytes
 sink=io.BytesIO()
 with gzip.GzipFile(fileobj=sink,mode='wb',filename='',mtime=0)as gz:
  with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT)as arc:
   for n,b in sorted(members.items()):
    ti=tarfile.TarInfo(n);ti.size=len(b);ti.mode=0o444;ti.uid=ti.gid=0;ti.uname=ti.gname='root';ti.mtime=0;arc.addfile(ti,io.BytesIO(b))
 bundle=sink.getvalue();assert len(bundle)<=96*1024*1024;write(FOLDER/'c808.inputs.tar.gz',bundle)
 controller=(OLD/'remote_capsule.py').read_text();oldstem='popl-ubuntu-lp-jobs-20261124-c7f0';controller=controller.replace(oldstem,STEM)
 def constant(name,value):
  nonlocal controller
  controller,count=re.subn(r'^'+name+r'=.*$',lambda m:name+'='+repr(value),controller,flags=re.M);assert count==1,name
 for n,v in{'BUNDLE_SHA':sha(bundle),'MANIFEST_SHA':sha(manifestbytes),'SOURCE_MANIFEST_SHA':sourcehash,'WORKER_SHA':sha(helpers['run_storage.py']),'UTILITY_SHA':FROZEN['keeper_jobs.py'],'INDEXER_SHA':FROZEN['job_cases.py'],'ALLOWED':tuple(sorted(members))}.items():constant(n,v)
 pat=r"^    for name,digest in .*:require\(sha\(data\['source/helpers/'\+name\]\)==digest,'Reviewed helper differs'\)$"
 controller,count=re.subn(pat,lambda m:"    for name,digest in "+repr(tuple((n,sha(b))for n,b in helpers.items()))+":require(sha(data['source/helpers/'+name])==digest,'Reviewed helper differs')",controller,flags=re.M);assert count==1
 public={name+'.json':'storage-run/'+name+'.json'for name in('RESULT','EVENTS','SOURCE','FILESYSTEM','INITIAL_JOURNAL','FINAL_JOURNAL','BEFORE','AFTER','BRANCHES','TRANSACTIONS','ACCEPTED_0','ACCEPTED_1','JOURNAL_AT_STOP')}
 for name in('BINDINGS','CLOCK_REPAIR','SETUP','RECEIPTS','RAW_REVIEWS','RESULT'):public['storage-'+name+'.json']='storage-run/storage/'+name+'.json'
 public.update({'SUMMARY.json':None,'FAILURE.json':None,'CLEANUP.json':None,'controller.stdout.log':'controller.stdout.log','controller.stderr.log':'controller.stderr.log'})
 constant('PUBLIC_PATHS',public)
 controller=controller.replace("path=runtime(a)/'jobs/RESULT.json'","path=runtime(a)/'storage-run/RESULT.json'")
 controller=controller.replace("'PrivateNetwork':'yes','PrivateDevices'","'PrivateNetwork':'yes','PrivateMounts':'yes','TemporaryFileSystem':str(LAB/'runtime/storage')+':size=1M,mode=0700,uid=65534,gid=65534','PrivateDevices'",1)
 controller=controller.replace("MemoryMax,MemorySwapMax,TasksMax,CPUQuotaPerSecUSec,CPUWeight,IOWeight,Nice'","MemoryMax,MemorySwapMax,TasksMax,CPUQuotaPerSecUSec,CPUWeight,IOWeight,Nice,PrivateMounts,TemporaryFileSystem'",1)
 line="    command+=['/usr/bin/python3','-B',str(LAB/'source/helpers/run_storage.py'),'--source-manifest-sha256',SOURCE_MANIFEST_SHA,'--base-sha256',"+repr(FROZEN['keeper_runtime.py'])+",'--jobs-sha256',"+repr(FROZEN['keeper_jobs.py'])+",'--cases-sha256',"+repr(FROZEN['job_cases.py'])+"]"
 controller,count=re.subn(r"^    command\+=\['/usr/bin/python3'.*$",lambda m:line,controller,flags=re.M);assert count==1
 extension=(BASE/'controller_extension_c808.py').read_text()
 controller=controller.replace("if __name__=='__main__':main()",extension+"\nif __name__=='__main__':main()")
 ast.parse(controller);write(FOLDER/'remote_capsule.py',controller.encode())
 host=(OLD/'host_control.py').read_text().replace('ubuntu-complete-20261124/keeper-lp-jobs','ubuntu-storage-20261125/c808').replace(oldstem,STEM)
 ast.parse(host);write(FOLDER/'host_control.py',host.encode())
 receipt={'schema':1,'feature':'storage_os_failures','bundle':pin(bundle),'manifest':pin(manifestbytes),'lab':LAB,'helpers':{n:pin(b)for n,b in helpers.items()},'controller':pin(controller.encode()),'host_wrapper':pin(host.encode()),'source_manifest_sha256':sourcehash,'published_source_base':HEAD,'current_production_members':190,'approved_worktree_overrides':overrides,'source_updates_from_previous_bundle':fromprior,'remote_actions':0,'runtime_executed':False,'limits':{'RPC_requests':6000,'worker_seconds':900,'maintenance_gas':24000000,'padding_percent':25,'confirmations':12,'gas_price_wei':5000000000,'single_maximum_cost_wei':str(10**16),'daily_maximum_cost_wei':str(5*10**16),'namespace_private_tmpfs_bytes':1048576}}
 write(FOLDER/'BUILD_RECEIPT.json',enc(receipt));print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
