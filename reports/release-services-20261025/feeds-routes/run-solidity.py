"""Isolated, source-bound new adapter checks; normal compiler/optimizer limits."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[3]
E=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
B=E/'release-services-20261025'/'feeds-routes'; B.mkdir(parents=True,exist_ok=True)
P=B/'pyth-reader-profile'; P.mkdir(exist_ok=True)
shutil.copytree(R/'src',P/'src',dirs_exist_ok=True)
seen=set()
def add(path):
    path=path.resolve()
    if path in seen:return
    seen.add(path); dest=P/path.relative_to(R); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
    for name in re.findall(r'(?:from\s*|import\s*)[\"\x27]([^\"\x27]+)[\"\x27]',path.read_text(encoding='utf-8-sig')):
        if name.startswith('.'):
            dep=(path.parent/name).resolve()
            if dep.is_relative_to(R/'test'):add(dep)
add(R/'test/PythPriceFeed.t.sol')
(P/'empty').mkdir(exist_ok=True)
config='[profile.default]\nsrc="empty"\ntest="test"\nout="out"\ncache_path="cache"\nevm_version="cancun"\noptimizer=true\noptimizer_runs=1\noptimizer_details={yul=false}\nvia_ir=true\nffi=false\nremappings=[\n'
for a,b in {'@openzeppelin/contracts/':'node_modules/@openzeppelin/contracts/','@uniswap/v4-core/':'node_modules/@uniswap/v4-core/','@uniswap/v4-periphery/':'node_modules/@uniswap/v4-periphery/','v4-core/':'node_modules/@uniswap/v4-core/','permit2/':'node_modules/@uniswap/v4-periphery/lib/permit2/','solmate/':'node_modules/@uniswap/v4-core/lib/solmate/','forge-std/':'lib/forge-std/src/'}.items():
    config+=json.dumps(a+'='+R.as_posix()+'/'+b)+',\n'
config+=']\n[profile.default.fuzz]\nruns=1000\n'
(P/'foundry.toml').write_text(config,encoding='utf-8',newline='\n')
pins={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in list((R/'src').rglob('*.sol'))+list(seen)}
(B/'pyth-reader-inputs.json').write_text(json.dumps(pins,indent=2)+'\n')
cmd=[str(E/'foundry-v1.4.4/forge.exe'),'test','--root',str(P),'--use',str(E/'toolchain-0.8.26/solc.exe'),'--match-contract','PythPriceFeedTest','--json']
if len(sys.argv)>1:cmd+=['--match-test',sys.argv[1]]
start=time.time(); env=os.environ.copy(); env['RAYON_NUM_THREADS']='2'
p=subprocess.run(cmd,capture_output=True,env=env,timeout=1200)
tag='pyth-reader'+('-repair' if len(sys.argv)>1 else '')
(B/(tag+'.json')).write_bytes(p.stdout); (B/(tag+'.stderr.log')).write_bytes(p.stderr)
try:
    data=json.loads(p.stdout)
    cases=[{'suite':suite,'test':name,'status':v.get('status'),'reason':v.get('reason')} for suite,z in data.items() for name,v in z.get('test_results',{}).items()]
except Exception:cases=[]
report={'exit_code':p.returncode,'elapsed_seconds':round(time.time()-start,2),'command':cmd,'cases':cases,
        'diagnostic':p.stdout.decode(errors='replace')[:3500] if not cases else None}
(B/(tag+'-summary.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2)); sys.exit(p.returncode)
