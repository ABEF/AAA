from pathlib import Path
import datetime as dt,gzip,hashlib,json,os,subprocess,time
R=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(__file__).resolve().parent
D=V/'validation-reuse'/'normal';D.mkdir(parents=True,exist_ok=False)
T=R/'reports/test-seal-deep-review-20261117/build'
C=V.parent/'toolchain-0.8.26/solc.exe'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(C.read_bytes())=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
template=gzip.decompress((T/'compiler-input.json.gz').read_bytes());prior=gzip.decompress((T/'compiler-output.json.gz').read_bytes())
inp=json.loads(template);old=json.loads(prior);gates=json.loads((T/'normal-size-evidence.json').read_bytes())['gates']
assert len(inp['sources'])==100 and len(gates)==48
before={n:sha((R/n).read_bytes())for n in inp['sources']}
changed=[n for n,row in inp['sources'].items()if (R/n).read_bytes().decode()!=row['content']]
assert set(changed)=={'src/ZZZLiquidityManager.sol','src/ZZZContributionPricing.sol'},changed
for n,row in inp['sources'].items():row['content']=(R/n).read_bytes().decode()
assert set(n for n in inp['sources']if n.startswith('src/'))=={p.relative_to(R).as_posix()for p in(R/'src').rglob('*.sol')}
payload=json.dumps(inp,separators=(',',':'),ensure_ascii=True).encode();(D/'compiler-input.json').write_bytes(payload)
start={'schema':1,'time':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'normal closed100-source48-size-gate check of2 private-proof-reuse edits',
 'command':[str(C),'--standard-json'],'compiler_sha256':sha(C.read_bytes()),'source_before_sha256':before,
 'input_sha256':sha(payload),'baseline_input_sha256':sha(template),'baseline_output_sha256':sha(prior),
 'settings_exactly_unchanged':True,'settings':inp['settings'],'expected_changed_sources':changed,
 'foundry_sha256':sha((R/'foundry.toml').read_bytes()),'foundry_not_consumed':True,'production_approved':False}
(D/'START.json').write_text(json.dumps(start,indent=2)+'\n')
env={k:os.environ[k]for k in('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')if k in os.environ}
env['PATH']=str(C.parent)+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32')
tick=time.monotonic()
with(D/'compiler-input.json').open('rb')as src,(D/'compiler-output.json').open('xb')as out,(D/'stderr.log').open('xb')as err:
 p=subprocess.Popen([str(C),'--standard-json'],stdin=src,stdout=out,stderr=err,cwd=D,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 (D/'PID.json').write_text(json.dumps({'pid':p.pid})+'\n')
 try:status=p.wait(timeout=900)
 except subprocess.TimeoutExpired:p.kill();p.wait();raise
after={n:sha((R/n).read_bytes())for n in inp['sources']};assert before==after
raw=(D/'compiler-output.json').read_bytes();compiled=json.loads(raw)
errors=[x for x in compiled.get('errors',[])if x['severity']=='error']
def semantic_type(layout,key,seen=()):
 r=layout['types'][key];out={k:r[k]for k in('encoding','label','numberOfBytes')}
 if key in seen:return dict(out,recursive=True)
 for k in('key','value','base'):
  if k in r:out[k]=semantic_type(layout,r[k],(*seen,key))
 if 'members'in r:out['members']=[{'label':x['label'],'slot':x['slot'],'offset':x['offset'],'type':semantic_type(layout,x['type'],(*seen,key))}for x in r['members']]
 return out
def storage(obj):
 l=obj['storageLayout'];return[{'contract':x['contract'],'label':x['label'],'slot':x['slot'],'offset':x['offset'],'type':semantic_type(l,x['type'])}for x in l['storage']]
rows=[];abis=[];layouts=[]
if not errors:
 for row in gates:
  o=compiled['contracts'][row['path']][row['name']];b=old['contracts'][row['path']][row['name']]
  runtime=len(o['evm']['deployedBytecode']['object'])//2;creation=len(o['evm']['bytecode']['object'])//2
  rows.append({**row,'runtime':runtime,'creation':creation,'runtime_margin':24576-runtime,
   'maximum_total_argument_bytes':49152-creation,'runtime_ok':runtime<=24576,'creation_ok':creation+row['minimum_args']<=49152,
   'runtime_delta':runtime-len(b['evm']['deployedBytecode']['object'])//2,'creation_delta':creation-len(b['evm']['bytecode']['object'])//2})
  abis.append({'contract':row['name'],'equal':o['abi']==b['abi']});layouts.append({'contract':row['name'],'equal':storage(o)==storage(b)})
result={'schema':1,'time':dt.datetime.now(dt.timezone.utc).isoformat(),'exit_code':status,'seconds':time.monotonic()-tick,
 'errors':errors,'source_after_sha256':after,'source_before_after_identical':before==after,
 'compiler_output_sha256':sha(raw),'source_count':len(compiled.get('sources',{})),
 'closure_exact':set(compiled.get('sources',{}))==set(inp['sources']), 'gates':rows,
 'all_pass':status==0 and not errors and len(rows)==48 and all(x['runtime_ok']and x['creation_ok']for x in rows),
 'abi_all48_unchanged':len(abis)==48 and all(x['equal']for x in abis),'storage_all48_unchanged':len(layouts)==48 and all(x['equal']for x in layouts),
 'abi':abis,'storage':layouts,'settings_exactly_unchanged':True,'production_approved':False}
(D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k]for k in('exit_code','seconds','errors','all_pass','abi_all48_unchanged','storage_all48_unchanged')}))
print(json.dumps([x for x in rows if x['runtime_delta']or x['creation_delta']]))
