from pathlib import Path
import subprocess,json,time,hashlib
R=Path.cwd();E=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9');B=E/'review-policy-20261025';sources={p.relative_to(R).as_posix():{'content':p.read_bytes().decode('utf-8-sig')} for p in (R/'src').rglob('*.sol')}
settings={'evmVersion':'cancun','viaIR':True,'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},'remappings':['@openzeppelin/contracts/=node_modules/@openzeppelin/contracts/','@uniswap/v4-core/=node_modules/@uniswap/v4-core/','@uniswap/v4-periphery/=node_modules/@uniswap/v4-periphery/','forge-std/=lib/forge-std/src/','solmate/=node_modules/@uniswap/v4-core/lib/solmate/'],'outputSelection':{'*':{'*':['abi','evm.bytecode.object','evm.deployedBytecode.object','metadata']}}}
t=time.monotonic();p=subprocess.run([str(E/'toolchain-0.8.26/solc.exe'),'--standard-json','--base-path',str(R)],input=json.dumps({'language':'Solidity','sources':sources,'settings':settings}).encode(),cwd=R,capture_output=True,timeout=1200)
(B/'production-compile.json').write_bytes(p.stdout[p.stdout.find(b'{'):]);x=json.loads((B/'production-compile.json').read_text());errors=[a for a in x.get('errors',[]) if a['severity']=='error'];gates=[]
for path,contracts in x.get('contracts',{}).items():
 if not path.startswith('src/'):continue
 for name,v in contracts.items():
  runtime=len(v['evm']['deployedBytecode']['object'])//2;creation=len(v['evm']['bytecode']['object'])//2
  if not creation:continue
  args=next((z['inputs'] for z in v['abi'] if z.get('type')=='constructor'),[]);dynamic=any(z['type'] in ('string','bytes','tuple') or '[' in z['type'] for z in args);arglen=None if dynamic else len(args)*32
  gates.append({'path':path,'name':name,'runtime':runtime,'creation':creation,'args':arglen,'runtime_ok':runtime<=24576,'creation_ok':creation+(arglen or 0)<=49152,'dynamic_constructor_qualification_required':dynamic})
report={'elapsed':time.monotonic()-t,'errors':errors,'gates':gates,'all_pass':not errors and all(g['runtime_ok'] and g['creation_ok'] for g in gates),'settings':settings,'source_sha256':{p:hashlib.sha256(v['content'].encode()).hexdigest() for p,v in sources.items()}}
(B/'production-size-gates.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'elapsed':report['elapsed'],'errors':errors,'gates':len(gates),'all_pass':report['all_pass'],'critical':[g for g in gates if g['name'] in ('ZZZVault','ZZZOracle','ZZZMigrationBudget','ZZZContributionPricing','ZZZPoolRegistry')]}));assert report['all_pass']


