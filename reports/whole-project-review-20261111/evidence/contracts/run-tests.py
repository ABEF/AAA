from pathlib import Path
import hashlib,json,re,shutil,subprocess,os,time,uuid,sys
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
B=Path(__file__).resolve().parent
P=B/('focused-'+uuid.uuid4().hex[:10]);P.mkdir()
shutil.copytree(R/'src',P/'src')
seen=set()
pattern=re.compile(r'''\bimport\s+(?:\{[^}]*\}\s*from\s*|(?:\*\s*as\s+\w+|\w+)\s*from\s*)?["']([^"']+)["']\s*;''',re.S)
remaps={'@openzeppelin/contracts/':'node_modules/@openzeppelin/contracts/','@uniswap/v4-core/':'node_modules/@uniswap/v4-core/','@uniswap/v4-periphery/':'node_modules/@uniswap/v4-periphery/','v4-core/':'node_modules/@uniswap/v4-core/','permit2/':'node_modules/@uniswap/v4-periphery/lib/permit2/','solmate/':'node_modules/@uniswap/v4-core/lib/solmate/','forge-std/':'lib/forge-std/src/'}
def add(path):
    path=path.resolve()
    if path in seen:return
    assert path.is_relative_to(R)
    seen.add(path);dest=P/path.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    for name in pattern.findall(path.read_text(encoding='utf-8-sig')):
        if name.startswith('.'):dep=path.parent/name
        else:
            matching=sorted((k for k in remaps if name.startswith(k)),key=len,reverse=True)
            assert matching,name
            prefix=matching[0];dep=R/(remaps[prefix]+name[len(prefix):])
        add(dep)
for file in json.loads(sys.argv[1]):add(R/file)
(P/'empty').mkdir()
config='[profile.default]\nsrc="empty"\ntest="test"\nout="out"\ncache_path="cache"\nevm_version="cancun"\noptimizer=true\noptimizer_runs=1\noptimizer_details={yul=false}\nvia_ir=true\nffi=false\nremappings=[\n'
for prefix,target in remaps.items():config+=json.dumps(prefix+'='+target)+',\n'
config+=']\n[profile.default.fuzz]\nruns=1000\n[profile.default.invariant]\nruns=32\ndepth=128\nfail_on_revert=true\n'
(P/'foundry.toml').write_text(config,encoding='utf-8',newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
watched=sorted(seen|set((R/'src').rglob('*.sol')))
before={p.relative_to(R).as_posix():sha(p) for p in watched}
command=[str(V/'foundry-v1.4.4/forge.exe'),'test','--root',str(P),'--use',str(V/'toolchain-0.8.26/solc.exe'),'--match-contract',sys.argv[2],'--json']
if len(sys.argv)>3:command+=['--match-test',sys.argv[3]]
(P/'START.json').write_text(json.dumps({'command':command,'sources':before,'normal_settings':True,'scope':'focused changed contract paths; synthetic fixtures, no RPC/deployment/existing Anvil'},indent=2)+'\n')
env=os.environ.copy();env['RAYON_NUM_THREADS']='2'
start=time.monotonic()
with (P/'forge.json').open('xb') as out,(P/'forge.stderr.log').open('xb') as err:
    proc=subprocess.run(command,cwd=P,env=env,stdout=out,stderr=err,timeout=1200)
try:
    output=json.loads((P/'forge.json').read_bytes())
    cases=[{'suite':suite,'test':name,'status':value.get('status'),'reason':value.get('reason'),'gas':value.get('gas')} for suite,body in output.items() for name,value in body.get('test_results',{}).items()]
except Exception:cases=[]
after={p.relative_to(R).as_posix():sha(p) for p in watched}
snapshot={p.relative_to(R).as_posix():sha(P/p.relative_to(R)) for p in watched}
report={'exit_code':proc.returncode,'seconds':round(time.monotonic()-start,2),'command':command,'tests':cases,'source_unchanged':before==after,'snapshot_exact':before==snapshot,'sources':before,'forge_sha256':sha(V/'foundry-v1.4.4/forge.exe'),'solc_sha256':sha(V/'toolchain-0.8.26/solc.exe')}
(P/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(str(P),flush=True)
print(json.dumps({'exit_code':proc.returncode,'tests':cases,'source_unchanged':before==after,'snapshot_exact':before==snapshot}),flush=True)
raise SystemExit(proc.returncode if before==after and before==snapshot and cases else 1)
