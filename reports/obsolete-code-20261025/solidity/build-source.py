"""Normal production object limits; no deployment, size waiver or test rerun."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[3]
E=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
B=E/'obsolete-code-audit-20261025'/'solidity'; B.mkdir(parents=True,exist_ok=True)
raw_sources={p.relative_to(R).as_posix():p.read_bytes() for p in (R/'src').rglob('*.sol')}
sources={name:{'content':raw.decode('utf-8-sig')} for name,raw in raw_sources.items()}
settings={'evmVersion':'cancun','viaIR':True,'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},
    'remappings':['@openzeppelin/contracts/=node_modules/@openzeppelin/contracts/','@uniswap/v4-core/=node_modules/@uniswap/v4-core/',
                  '@uniswap/v4-periphery/=node_modules/@uniswap/v4-periphery/','forge-std/=lib/forge-std/src/',
                  'solmate/=node_modules/@uniswap/v4-core/lib/solmate/'],
    'outputSelection':{'*':{'*':['abi','storageLayout','evm.bytecode.object','evm.deployedBytecode.object']}}}
payload={'language':'Solidity','sources':sources,'settings':settings}
(B/'source-build-input.json').write_text(json.dumps(payload),encoding='utf-8')
start=time.monotonic()
p=subprocess.run([str(E/'toolchain-0.8.26/solc.exe'),'--standard-json','--base-path',str(R)],
    input=json.dumps(payload).encode(),cwd=R,capture_output=True,timeout=1200)
(B/'source-build-stderr.log').write_bytes(p.stderr)
raw=p.stdout[p.stdout.find(b'{'):]; (B/'source-build.json').write_bytes(raw); data=json.loads(raw)
errors=[x for x in data.get('errors',[]) if x['severity']=='error']; gates=[]
for path,contracts in data.get('contracts',{}).items():
    if not path.startswith('src/'):continue
    for name,value in contracts.items():
        runtime=len(value['evm']['deployedBytecode']['object'])//2; creation=len(value['evm']['bytecode']['object'])//2
        if not creation:continue
        args=next((x['inputs'] for x in value['abi'] if x.get('type')=='constructor'),[])
        dynamic=any(x['type'] in ('string','bytes','tuple') or '[' in x['type'] for x in args)
        static=None if dynamic else len(args)*32
        entry={'path':path,'name':name,'runtime':runtime,'runtime_margin':24576-runtime,'creation':creation,
               'constructor_types':[x['type'] for x in args],'static_argument_bytes':static,
               'runtime_ok':runtime<=24576,'creation_ok':creation+(static or 0)<=49152,
               'maximum_total_argument_bytes':49152-creation,'dynamic_constructor_exact_argument_qualification_required':dynamic}
        if name == 'ZZZAccessController':
            # Five ABI head words, two array lengths and one address per role.
            # These nonempty arrays are required by this constructor. A multisig
            # can be one role address; its internal signers are not array items.
            minimal_args=32*(5+2+1+1)
            entry.update(minimal_role_argument_bytes=minimal_args,
                minimal_role_total_initcode=creation+minimal_args,
                minimal_role_initcode_margin=49152-creation-minimal_args,
                minimal_role_initcode_ok=creation+minimal_args<=49152)
            entry['creation_ok'] = entry['creation_ok'] and entry['minimal_role_initcode_ok']
        gates.append(entry)
stable_sources=set(raw_sources)=={p.relative_to(R).as_posix() for p in (R/'src').rglob('*.sol')} and all((R/path).read_bytes()==raw for path,raw in raw_sources.items())
report={'solc_exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-start,2),'errors':errors,'gates':gates,
        'all_pass':stable_sources and not errors and all(x['runtime_ok'] and x['creation_ok'] for x in gates),'settings':settings,
        'unchanged_during_build':stable_sources,
        'source_sha256':{path:hashlib.sha256(raw).hexdigest() for path,raw in raw_sources.items()},
        'compiler_content_sha256':{path:hashlib.sha256(value['content'].encode()).hexdigest() for path,value in sources.items()},
        'qualification':'Normal EIP-170/EIP-3860 object gates; dynamic release constructor arguments require exact ABI-encoded qualification. No deployment or live-service approval.'}
(B/'source-size-gates.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'elapsed':report['elapsed_seconds'],'source_count':len(sources),'gate_count':len(gates),'all_pass':report['all_pass'],
    'errors':errors,'new_reader':[x for x in gates if x['name']=='ZZZPythPriceFeed'],'vault':[x for x in gates if x['name']=='ZZZVault']},indent=2))
sys.exit(0 if report['all_pass'] else 1)
