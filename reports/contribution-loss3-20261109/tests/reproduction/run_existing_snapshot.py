from pathlib import Path
import json,re,hashlib,subprocess,datetime,time,os
root=Path.cwd();c=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/contribution-three-percent-20261109-793c8e0');v=c.parent
out=c/'tests/attempt4-existing';out.mkdir(parents=True,exist_ok=False);snapshot=out/'project';snapshot.mkdir()
prior=json.loads(next((c/'tests/attempt2-entry/build-info').glob('*.json')).read_text())
remappings=prior['input']['settings']['remappings'];mapping=sorted([tuple(x.split('=',1)) for x in remappings],key=lambda x:-len(x[0]))
selected=['test/GovernedExecutionLoss.t.sol','test/IntegratedEconomicConservation.t.sol','test/NativeVaultFlows.t.sol','test/OptionalPortfolioCore.t.sol','test/CurrentNativePoolFork.t.sol']
pending=[root/x for x in selected]+list((root/'src').rglob('*.sol'));sources={}
pattern=re.compile(r'import\s+(?:[^;]*?\sfrom\s+)?[\"\x27]([^\"\x27]+)[\"\x27]',re.MULTILINE)
while pending:
 p=pending.pop().resolve();name=p.relative_to(root).as_posix()
 if name in sources:continue
 b=p.read_bytes();sources[name]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
 for imp in pattern.findall(b.decode('utf-8')):
  if imp.startswith('.'):
   q=p.parent/imp
  else:
   found=next(((key,value) for key,value in mapping if imp.startswith(key)),None)
   q=root/(found[1]+imp[len(found[0]):]) if found else root/imp
  if not q.is_file():raise RuntimeError(f'Unresolved import {imp} from {name}')
  pending.append(q)
config=(root/'foundry.toml').read_bytes();(snapshot/'foundry.toml').write_bytes(config)
manifest={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_root':str(root),'snapshot_root':str(snapshot),'selected_roots':selected,'sources':sources,'foundry_toml_sha256':hashlib.sha256(config).hexdigest(),'original_remappings':remappings,'scope':'Byte-exact isolated import closure; no rewritten test or production source, config copied exactly; no .env/credential/RPC/config/runtime copied. Offline current-fork opt-in forced false. Four affected existing methods only; prior brace-glob no-tests attempt retained and never counted.'}
(out/'snapshot.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
spec=json.loads((c/'tests/existing-selection.json').read_text());forge=v/'foundry-v1.4.4/forge.exe';solc=v/'toolchain-0.8.26/solc.exe'
args=[str(forge),'test','--root',str(snapshot),'--use',str(solc),'--offline','--out',str(out/'out'),'--cache-path',str(out/'cache'),'--build-info','--build-info-path',str(out/'build-info'),'--match-path','test/*.t.sol','--match-contract',spec['contract'],'--match-test',spec['test'],'-vv']
env=os.environ.copy();env['RUN_CURRENT_POOL_FORK']='false';env['FOUNDRY_REMAPPINGS']='\n'.join(remappings)
manifest['command']=args;manifest['tools']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (forge,solc)}
(out/'before.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
start=time.monotonic()
with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:r=subprocess.run(args,cwd=snapshot,env=env,stdout=stdout,stderr=stderr,timeout=1800)
manifest.update(exit_code=r.returncode,seconds=time.monotonic()-start,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
manifest['snapshot_unchanged']=all(hashlib.sha256((snapshot/p).read_bytes()).hexdigest()==row['sha256'] for p,row in sources.items())
manifest['original_sources_unchanged']=all(hashlib.sha256((root/p).read_bytes()).hexdigest()==row['sha256'] for p,row in sources.items())
(out/'result.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:manifest[k] for k in ['exit_code','seconds','snapshot_unchanged','original_sources_unchanged']}));print((out/'stdout.log').read_text(errors='replace')[-11000:]);print((out/'stderr.log').read_text(errors='replace')[-2000:])