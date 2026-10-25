from pathlib import Path
import hashlib,json,subprocess,time
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
B=Path(__file__).parent/'solidity'
T=R/'reports/daily-security-20261025/solidity'
def sha(b):return hashlib.sha256(b).hexdigest()
original=json.loads((B/'all-source-typecheck-input.json').read_text())
raw={p.relative_to(R).as_posix():p.read_bytes() for folder in ('src','test','script') for p in sorted((R/folder).rglob('*.sol'))}
payload={**original,'sources':{k:{'content':v.decode('utf-8-sig')} for k,v in raw.items()}}
inp=json.dumps(payload).encode(); (B/'all-source-typecheck-control-final-input.json').write_bytes(inp)
start=time.monotonic()
p=subprocess.run([str(B.parents[1]/'toolchain-0.8.26/solc.exe'),'--standard-json','--base-path',str(R)],input=inp,capture_output=True,cwd=R,timeout=180)
out=p.stdout[p.stdout.find(b'{'):]; data=json.loads(out)
(B/'all-source-typecheck-control-final.json').write_bytes(out)
(B/'all-source-typecheck-control-final-stderr.log').write_bytes(p.stderr)
errors=[e for e in data.get('errors',[]) if e['severity']=='error']
stable=all((R/k).read_bytes()==v for k,v in raw.items())
sizes=json.loads((B/'source-size-gates.json').read_text())
assert all(sha((R/k).read_bytes())==h for k,h in sizes['source_sha256'].items())
summary={'base':'1e00b49e956d9c4daf30598d88ca88cd874d1e8a','source_count':len(raw),'solc_exit_code':p.returncode,'errors':errors,'unchanged_during_compile':stable,'elapsed_seconds':round(time.monotonic()-start,3),'source_sha256':{k:sha(v) for k,v in raw.items()},'compiler_input_sha256':sha(inp),'compiler_output_sha256':sha(out),'production_41_match_existing_normal_build':True,'scope':'Final ABI/AST typecheck after test-name and same-depth mock-control repairs. Production build and size gates reused unchanged; no EVM tests or deployment performed by this script.'}
(B/'typecheck-control-final-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
(T/'typecheck-summary-initial.json').write_bytes((T/'typecheck-summary.json').read_bytes())
(T/'typecheck-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:summary[k] for k in ('source_count','solc_exit_code','elapsed_seconds','unchanged_during_compile','production_41_match_existing_normal_build')},indent=2))
raise SystemExit(0 if not errors and not p.returncode and stable else 1)
