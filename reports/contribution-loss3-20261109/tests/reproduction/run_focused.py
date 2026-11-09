"""Isolated focused tests; no fork/network/FFI, existing caches left untouched."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path.cwd()
CAMPAIGN=Path(__file__).resolve().parent
V=CAMPAIGN.parent
OUT=CAMPAIGN/'tests'/sys.argv[1]
OUT.mkdir(parents=True,exist_ok=False)
forge=V/'foundry-v1.4.4/forge.exe'
solc=V/'toolchain-0.8.26/solc.exe'
match=sys.argv[2]
args=[str(forge),'test','--root',str(ROOT),'--use',str(solc),'--offline',
      '--out',str(OUT/'out'),'--cache-path',str(OUT/'cache'),
      '--build-info','--build-info-path',str(OUT/'build-info'),
      '--match-contract',match,'--match-path','test/ContributionThreePercent.t.sol','-vv']
files=sorted([*ROOT.joinpath('src').rglob('*.sol'),*ROOT.joinpath('test').rglob('*.sol'),ROOT/'foundry.toml'])
snapshot=lambda:{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=snapshot()
record={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':args,
        'source_before':before,'tool_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (forge,solc)},
        'scope':'Selected deterministic contribution accounting/Entry tests; no target-chain, public wallet, provider, gas or independent-audit qualification.'}
(OUT/'before.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
start=time.monotonic()
with (OUT/'stdout.log').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:
    done=subprocess.run(args,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=1200)
record.update(exit_code=done.returncode,seconds=time.monotonic()-start,
              completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_after=snapshot())
record['source_unchanged']=record['source_before']==record['source_after']
(OUT/'result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'attempt':str(OUT),'exit_code':done.returncode,'seconds':record['seconds'],'source_unchanged':record['source_unchanged']}))
print((OUT/'stdout.log').read_text(encoding='utf-8',errors='replace')[-10000:])
print((OUT/'stderr.log').read_text(encoding='utf-8',errors='replace')[-2500:])
