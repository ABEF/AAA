import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path.cwd();C=Path(__file__).resolve().parent;V=C.parent
out=C/'tests'/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
forge=V/'foundry-v1.4.4/forge.exe';solc=V/'toolchain-0.8.26/solc.exe'
spec=json.loads(sys.argv[2]);cache=C/'tests'/'attempt1'/'cache';artifacts=C/'tests'/'attempt1'/'out'
args=[str(forge),'test','--root',str(ROOT),'--use',str(solc),'--offline','--out',str(artifacts),'--cache-path',str(cache),'--build-info','--build-info-path',str(out/'build-info'),'--match-path',spec['path'],'--match-contract',spec['contract'],'--match-test',spec['test'],'-vv']
paths=sorted([*ROOT.joinpath('src').rglob('*.sol'),*ROOT.joinpath('test').rglob('*.sol'),ROOT/'foundry.toml'])
snapshot=lambda:{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':args,'before':snapshot(),'tools':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (forge,solc)},'scope':spec.get('scope'),'normal_profile':{'solc':'0.8.26','evm':'cancun','via_ir':True,'optimizer_runs':1,'yul':False}}
(out/'before.json').write_text(json.dumps(r,indent=2)+'\n')
env=os.environ.copy();env.pop('RUN_CURRENT_POOL_FORK',None)
start=time.monotonic()
with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
 done=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=1800)
r.update(exit_code=done.returncode,seconds=time.monotonic()-start,after=snapshot(),completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());r['source_unchanged']=r['before']==r['after']
(out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'attempt':str(out),'exit_code':done.returncode,'seconds':r['seconds'],'source_unchanged':r['source_unchanged']}))
print((out/'stdout.log').read_text(errors='replace')[-12000:]);print((out/'stderr.log').read_text(errors='replace')[-2000:])
