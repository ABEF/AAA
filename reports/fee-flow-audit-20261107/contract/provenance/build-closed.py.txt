"""Source-only closed normal solc evidence; no Forge cache, RPC or deployment."""
from pathlib import Path
import datetime, hashlib, json, os, posixpath, re, subprocess, sys, time, tomllib, uuid

ROOT=Path.cwd()
sys.path.insert(0,str(ROOT))
from zzz_ops.function_reference import _constructor_bounds
BASE=Path(__file__).resolve().parent
OUT=BASE/('normal-final-'+uuid.uuid4().hex[:10])
OUT.mkdir()
SOLC=BASE.parents[1]/'toolchain-0.8.26/solc.exe'
# BASE is nested under range85; toolchain is under the shared visualization root.
SOLC=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/toolchain-0.8.26/solc.exe')
def sha(raw):return hashlib.sha256(raw).hexdigest()
normal=tomllib.loads((ROOT/'foundry.toml').read_text())['profile']['default']
assert normal['solc_version']=='0.8.26' and normal['evm_version']=='cancun'
assert normal['via_ir'] is True and normal['optimizer'] is True and normal['optimizer_runs']==1
assert normal['optimizer_details']=={'yul':False}
binary_before=sha(SOLC.read_bytes())
assert binary_before=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
remaps=[x.split('=',1) for x in normal['remappings']]
remaps.sort(key=lambda x:len(x[0]),reverse=True)
pattern=re.compile(r'''\bimport\s+(?:\{[^}]*\}\s*from\s*|(?:\*\s*as\s+\w+|\w+)\s*from\s*)?["']([^"']+)["']\s*;''',re.S)
project={p.relative_to(ROOT).as_posix() for p in (ROOT/'src').rglob('*.sol')}
sources={};raw_hash={}
def collect(name):
    if name in sources:return
    path=(ROOT/name).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not name.startswith(('src/','node_modules/','lib/')):
        raise ValueError('Source escaped closed project/dependency scope')
    raw=path.read_bytes();text=raw.decode('utf-8-sig')
    sources[name]={'content':text};raw_hash[name]=sha(raw)
    for imported in pattern.findall(text):
        if imported.startswith('.'):
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),imported))
        else:
            matches=[(prefix,target) for prefix,target in remaps if imported.startswith(prefix)]
            if not matches:raise ValueError('Unresolved import '+imported)
            prefix,target=matches[0];resolved=target+imported[len(prefix):]
        collect(resolved)
for name in sorted(project):collect(name)
settings={'evmVersion':'cancun','viaIR':True,'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},
 'remappings':normal['remappings'],'outputSelection':{'*':{'*':['abi','storageLayout','evm.bytecode.object','evm.bytecode.sourceMap','evm.deployedBytecode.object','evm.deployedBytecode.sourceMap','metadata'],'':['ast']}}}
payload={'language':'Solidity','sources':dict(sorted(sources.items())),'settings':settings}
input_path=OUT/'compiler-input.json';input_raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
with input_path.open('xb') as f:f.write(input_raw)
build_names=['foundry.toml','package.json','package-lock.json','scripts/install-deps.sh']
build_before={name:sha((ROOT/name).read_bytes()) for name in build_names if (ROOT/name).is_file()}
pre={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':raw_hash,'build_sha256':build_before,
 'solc_sha256':binary_before,'scope':'normal source-only production compile; no tests/RPC/deployment/approval'}
(OUT/'START.json').write_bytes(json.dumps(pre,indent=2).encode())
command=[str(SOLC),'--standard-json']
start=time.monotonic()
with input_path.open('rb') as stdin,(OUT/'compiler-output.json').open('xb') as stdout,(OUT/'solc-stderr.txt').open('xb') as stderr:
    proc=subprocess.Popen(command,cwd=ROOT,stdin=stdin,stdout=stdout,stderr=stderr)
    try:exit_code=proc.wait(timeout=240)
    except subprocess.TimeoutExpired:
        proc.kill();proc.wait()
        (OUT/'TIMEOUT.json').write_bytes(json.dumps({'timeout_seconds':240,'pid':proc.pid,'process_killed':True,'not_a_pass':True}).encode())
        print(str(OUT),flush=True);raise
output_raw=(OUT/'compiler-output.json').read_bytes()
output=json.loads(output_raw)
errors=[x.get('formattedMessage',x.get('message','compiler error')) for x in output.get('errors',[]) if x.get('severity')=='error']
actual_sources=set(output.get('sources',{}));expected=set(sources)
after={name:sha((ROOT/name).read_bytes()) for name in expected}
build_after={name:sha((ROOT/name).read_bytes()) for name in build_before}
gates=[]
if errors or not output.get('contracts'):
    failure={'all_pass':False,'exit_code':1,'solc_exit_code':exit_code,
        'errors':errors or ['Compiler produced no contract objects'],
        'elapsed_seconds':round(time.monotonic()-start,2),'source_sha256':raw_hash,
        'source_unchanged_during_build':raw_hash==after,'no_deployment':True,'no_rpc':True,
        'compiler_input_sha256':sha(input_raw),'compiler_output_sha256':sha(output_raw)}
    (OUT/'production-size-gates.json').write_text(json.dumps(failure,indent=2)+'\n')
    print(str(OUT),flush=True);print(json.dumps({'all_pass':False,'errors':failure['errors']}),flush=True)
    raise SystemExit(1)
if not errors:
    for source,contracts in sorted(output.get('contracts',{}).items()):
        if not source.startswith('src/'):continue
        for name,obj in sorted(contracts.items()):
            creation=obj.get('evm',{}).get('bytecode',{}).get('object','')
            if not creation:continue
            runtime=obj['evm']['deployedBytecode']['object']
            if not re.fullmatch('[0-9a-fA-F]*',creation+runtime):raise ValueError('Unlinked bytecode')
            bounds=_constructor_bounds(obj['abi']);clen=len(creation)//2;rlen=len(runtime)//2
            gates.append({'name':name,'runtime':rlen,'creation':clen,'minimum_args':bounds['minimum_argument_bytes'],
             'runtime_margin':24576-rlen,'path':source,'static_argument_bytes':bounds['static_argument_bytes'],
             'constructor_types':bounds['types'],'maximum_total_argument_bytes':49152-clen,
             'dynamic_constructor_exact_argument_qualification_required':bounds['requires_exact_arguments'],
             'runtime_ok':rlen<=24576,'creation_ok':clen+bounds['minimum_argument_bytes']<=49152})
if expected!=actual_sources:errors.append('Compiler source closure differs')
if raw_hash!=after or build_before!=build_after:errors.append('Source/build drift during compile')
if binary_before!=sha(SOLC.read_bytes()):errors.append('Compiler binary drift')
if any(not g['runtime_ok'] or not g['creation_ok'] for g in gates):errors.append('Normal object size gate failed')
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
royalty=bytes.fromhex(output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
carrier=output['contracts']['src/ZZZRoyaltyCodeData.sol']['ZZZRoyaltyCodeData']
carrier_creation=len(carrier['evm']['bytecode']['object'])//2
parts=[royalty[:24573],royalty[24573:]]
actual_data_gates=[]
for i,part in enumerate(parts):
    runtime=b'\x5f\x5f\xfd'+part
    arglen=64+((len(part)+31)//32)*32
    actual_data_gates.append({'index':i,'data_length':len(part),'runtime':len(runtime),
      'runtime_hash':'0x'+keccak256(runtime).hex(),'creation':carrier_creation,'exact_argument_bytes':arglen,
      'exact_initcode':carrier_creation+arglen,'runtime_ok':len(runtime)<=24576,
      'creation_ok':carrier_creation+arglen<=49152,
      'constructor_returned_runtime':True,'generic_deployed_bytecode_is_not_actual_runtime':True})
if not royalty or len(royalty)>49146 or any(not g['runtime_ok'] or not g['creation_ok'] for g in actual_data_gates):
    errors.append('Actual constructor-returned data runtime/initcode gate failed')
report={'exit_code':0 if exit_code==0 and not errors else 1,'elapsed_seconds':round(time.monotonic()-start,2),
 'errors':errors,'gates':gates,'input_sha256':sha(input_raw),'no_deployment':True,'no_rpc':True,
 'solc_exit_code':exit_code,'source_count':len(expected),'compiled_source_count':len(actual_sources),
 'closed_input_inventory':True,'unexpected_implicit_sources':sorted(actual_sources-expected),'missing_compiled_sources':sorted(expected-actual_sources),
 'unchanged_before_build':True,'unchanged_during_build':raw_hash==after and build_before==build_after,
 'solc_executable_unchanged':binary_before==sha(SOLC.read_bytes()),'solc_executable_sha256':binary_before,
 'settings':settings,'build_input_sha256':build_before,'compiler_input_sha256':sha(input_raw),'compiler_output_sha256':sha(output_raw),
 'source_sha256':{k:raw_hash[k] for k in sorted(project)},'compiler_content_sha256':{k:sha(v['content'].encode()) for k,v in sources.items()},
 'dependency_source_sha256':{k:raw_hash[k] for k in sorted(expected-project)},
 'factory_data_gates':actual_data_gates,'royalty_creation_code_hash':'0x'+keccak256(royalty).hex(),
 'all_pass':exit_code==0 and not errors}
(OUT/'production-size-gates.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
print(str(OUT),flush=True)
print(json.dumps({'all_pass':report['all_pass'],'sources':len(expected),'gates':len(gates),'errors':errors}),flush=True)
for g in gates:
    if g['name'] in ['ZZZVault','ZZZMigrationBudget','ZZZLiquidityManager','ZZZStrategy','ZZZPortfolioPolicy','ZZZLPBalancer','ZZZLPPositionExecutor']:
        print(g['name'],g['runtime'],g['creation'],g['runtime_margin'],flush=True)
raise SystemExit(0 if report['all_pass'] else 1)
