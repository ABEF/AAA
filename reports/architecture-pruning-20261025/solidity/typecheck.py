from pathlib import Path
import hashlib,json,subprocess,time,tomllib
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=Path(__file__).parent;B=E/'solidity';B.mkdir(exist_ok=True)
raw={p.relative_to(R).as_posix():p.read_bytes() for directory in ('src','test','script') for p in (R/directory).rglob('*.sol')}
settings=json.loads((B/'source-size-gates.json').read_text())['settings']
settings['remappings']=tomllib.loads((R/'foundry.toml').read_text())['profile']['default']['remappings']
settings['outputSelection']={'*':{'':['ast'],'*':['abi']}}
if (B/'typecheck-summary.json').exists():
    n=len(list(B.glob('typecheck-attempt*-summary.json')))+1
    for name in ('all-source-typecheck-input.json','all-source-typecheck.json','typecheck-summary.json'):
        (B/f'typecheck-attempt{n}-{name}').write_bytes((B/name).read_bytes())
inp=json.dumps({'language':'Solidity','sources':{k:{'content':v.decode('utf-8-sig')} for k,v in raw.items()},'settings':settings}).encode()
(B/'all-source-typecheck-input.json').write_bytes(inp)
start=time.monotonic();p=subprocess.run([str(E.parent/'toolchain-0.8.26/solc.exe'),'--standard-json','--base-path',str(R)],input=inp,capture_output=True,cwd=R,timeout=180)
out=p.stdout[p.stdout.find(b'{'):];(B/'all-source-typecheck.json').write_bytes(out);d=json.loads(out)
errors=[x for x in d.get('errors',[]) if x['severity']=='error']
result={'source_count':len(raw),'solc_exit_code':p.returncode,'errors':errors,'elapsed_seconds':round(time.monotonic()-start,2),'source_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},'unchanged_during_compile':all((R/k).read_bytes()==v for k,v in raw.items()),'compiler_input_sha256':hashlib.sha256(inp).hexdigest(),'compiler_output_sha256':hashlib.sha256(out).hexdigest()}
(B/'typecheck-summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:result[k] for k in ('source_count','solc_exit_code','errors','elapsed_seconds','unchanged_during_compile')},indent=2))
raise SystemExit(1 if errors or p.returncode else 0)
