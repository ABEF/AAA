from pathlib import Path
import subprocess,json,time,hashlib,sys
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
B=E/'comprehensive-improvement-20261025'
sources={p.relative_to(R).as_posix():{'content':p.read_bytes().decode('utf-8-sig')} for p in (R/'src').rglob('*.sol')}
settings={'evmVersion':'cancun','viaIR':True,'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},'remappings':['@openzeppelin/contracts/=node_modules/@openzeppelin/contracts/','@uniswap/v4-core/=node_modules/@uniswap/v4-core/','@uniswap/v4-periphery/=node_modules/@uniswap/v4-periphery/','forge-std/=lib/forge-std/src/','solmate/=node_modules/@uniswap/v4-core/lib/solmate/'],'outputSelection':{'*':{'*':['abi','evm.bytecode.object','evm.deployedBytecode.object','metadata']}}}
xin={'language':'Solidity','sources':sources,'settings':settings}
(B/'production-final-input.json').write_text(json.dumps(xin),encoding='utf-8')
start=time.monotonic();p=subprocess.run([str(E/'toolchain-0.8.26/solc.exe'),'--standard-json','--base-path',str(R)],input=json.dumps(xin).encode(),cwd=R,capture_output=True,timeout=1500)
(B/'production-final-stderr.log').write_bytes(p.stderr)
raw=p.stdout[p.stdout.find(b'{'):];(B/'production-final-compile.json').write_bytes(raw);data=json.loads(raw)
errors=[z for z in data.get('errors',[]) if z['severity']=='error'];gates=[]
for path,contracts in data.get('contracts',{}).items():
 if not path.startswith('src/'):continue
 for name,value in contracts.items():
  runtime=len(value['evm']['deployedBytecode']['object'])//2;creation=len(value['evm']['bytecode']['object'])//2
  if not creation:continue
  args=next((z['inputs'] for z in value['abi'] if z.get('type')=='constructor'),[])
  dynamic=any(z['type'] in ('string','bytes','tuple') or '[' in z['type'] for z in args)
  static=None if dynamic else len(args)*32
  entry={'path':path,'name':name,'runtime':runtime,'runtime_margin':24576-runtime,'creation':creation,'constructor_types':[z['type'] for z in args],'static_argument_bytes':static,'runtime_ok':runtime<=24576,'creation_ok':creation+(static or 0)<=49152,'maximum_total_argument_bytes':49152-creation,'dynamic_constructor_exact_argument_qualification_required':dynamic}
  if name=='ZZZNFT':
   illustrative_uri='ipfs://'+'b'+'a'*58+'/'
   encoded=96+32*((len(illustrative_uri.encode())+31)//32)
   entry.update(illustrative_uri_bytes=len(illustrative_uri.encode()),illustrative_argument_bytes=encoded,illustrative_creation_total=creation+encoded,illustrative_creation_ok=creation+encoded<=49152,uri_qualification='Illustrative syntax only; no real published root selected. Exact release URI must be ABI-encoded and size checked.')
  if name=='ZZZAccessController':
   encoded=5*32+2*64
   entry.update(illustrative_single_proposer_executor_argument_bytes=encoded,illustrative_creation_total=creation+encoded,illustrative_creation_ok=creation+encoded<=49152)
  gates.append(entry)
rawpins={path:hashlib.sha256((R/path).read_bytes()).hexdigest() for path in sources}
report={'solc_exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-start,2),'errors':errors,'gates':gates,'all_pass':not errors and all(z['runtime_ok'] and z['creation_ok'] and z.get('illustrative_creation_ok',True) for z in gates),'settings':settings,'source_sha256':rawpins,'compiler_content_sha256':{path:hashlib.sha256(value['content'].encode()).hexdigest() for path,value in sources.items()},'qualification':'Normal EIP-170/EIP-3860 gates; dynamic constructor release addresses/arrays/base URI require exact encoded-argument qualification. No deployment or real-service qualification.'}
(B/'production-final-size-gates.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'elapsed':report['elapsed_seconds'],'errors':errors,'gate_count':len(gates),'all_pass':report['all_pass'],'critical':[z for z in gates if z['name'] in ('ZZZBuyback','ZZZNFT','ZZZNFTMetadata','ZZZPoolRegistry','ZZZVault','ZZZContributionPricing','ZZZActivationEntry','ZZZAccessController')]},indent=2));sys.exit(0 if report['all_pass'] else 1)
