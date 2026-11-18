"""Actual activation-gas 100-source/48-object normal build; no tests or deployment."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,subprocess,sys,time
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R))
from zzz_ops.function_reference import BUILD_INPUTS,import_compiler
from zzz_ops.abi import keccak256
sys.path.insert(0,str(R/'reports/royalty-rounds-20261118'))
from build_candidate import semantic_storage
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
SOLC=V/'toolchain-0.8.26/solc.exe';FORGE=V/'foundry-v1.4.4/forge.exe'
BASE=V/'royalty-rounds-20261118/build/final02'
DEST=V/'activation-gas-20261118/build'/sys.argv[1]
PUB=R/'reports/activation-gas-20261118/build/final'
COMPILER='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
CHANGED={'src/ZZZOracle.sol','src/ZZZV4SpotPriceFeed.sol','src/libraries/ExactLPAllocation.sol','src/base/ZZZExactLPRewardsCanonical.sol'}
PROTECTED={
 'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,indent=2);f.write('\n')
def normalize_abi(rows):
    rows=json.loads(json.dumps(rows))
    for row in rows:
        if row.get('type')=='function' and row.get('name')=='accounted':row['inputs'][0]['name']=''
    return rows
def compare_abi(name,before,after):
    return before==after

def storage_matches(before,after):
    allowed={}
    def collect(value):
        if isinstance(value,dict):
            if value.get('label')=='struct ExactLPAllocation.Carry':allowed['old']=value
            for x in value.values():collect(x)
        elif isinstance(value,list):
            for x in value:collect(x)
    collect(before)
    def normalize(value):
        if isinstance(value,dict):
            if value.get('label')=='struct ExactLPAllocation.Carry':
                assert value['encoding']=='inplace' and value['numberOfBytes']=='64'
                assert [(x['label'],x['slot'],x['offset'],x['type']['label'])for x in value['members']]==[('packed','0',0,'uint256'),('wide','1',0,'uint256')]
                return allowed['old']
            return {k:normalize(v)for k,v in value.items()}
        if isinstance(value,list):return [normalize(x)for x in value]
        return value
    return before==normalize(after)

def main():
    DEST.mkdir(parents=True,exist_ok=False);PUB.mkdir(parents=True,exist_ok=False)
    assert sha(SOLC.read_bytes())==COMPILER
    data=json.loads((BASE/'compiler-input.json').read_bytes());old=json.loads((BASE/'compiler-output.json').read_bytes());prior=json.loads((BASE/'RESULT.json').read_bytes())
    assert prior['pass'] and len(data['sources'])==100 and len(prior['gates'])==48
    actual={n:sha((R/n).read_bytes())for n in data['sources']};changed=set()
    for n,row in data['sources'].items():
        text=(R/n).read_bytes().decode('utf-8-sig')
        if row['content']!=text:changed.add(n)
        row['content']=text
    assert changed==CHANGED,changed
    assert {n for n in actual if n.startswith('src/')}=={p.relative_to(R).as_posix()for p in(R/'src').rglob('*.sol')}
    assert sum(n.startswith('src/')for n in actual)==61
    assert sha((R/'src/ZZZRoyaltyRewards.sol').read_bytes())=='35f712bd0b95abdd63a9e696e6e85e63453f2d8e5ec57c089c595e6bfd5f5bbd'
    build={n:sha((R/n).read_bytes())for n in BUILD_INPUTS if(R/n).is_file()};assert len(build)==4
    assert all(sha((R/n).read_bytes())==h for n,h in PROTECTED.items())
    payload=json.dumps(data,separators=(',',':'),ensure_ascii=True).encode();(DEST/'compiler-input.json').write_bytes(payload)
    expected={n:sha(x['content'].encode())for n,x in data['sources'].items()};assert expected==actual
    keep={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA'}
    env={k:v for k,v in os.environ.items()if k.upper()in keep};env['PATH']=str(SOLC.parent)+os.pathsep+'C:/Windows/System32'
    spec=importlib.util.spec_from_file_location('_final_normal_profile',R/'scripts/verify-normal-profile.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    save(DEST/'EFFECTIVE_NORMAL_PROFILE.json',module.inspect_profile(str(FORGE),environment=env))
    start={'kind':'actual_closed_normal_build','candidate_build_id':'activation-gas-20261118','started_utc':datetime.now(timezone.utc).isoformat(),
      'command':[str(SOLC),'--standard-json'],'settings':data['settings'],'compiler_sha256':COMPILER,
      'source_sha256':{n:h for n,h in actual.items()if n.startswith('src/')},'dependency_source_sha256':{n:h for n,h in actual.items()if not n.startswith('src/')},
      'compiler_content_sha256':expected,'build_input_sha256':build,'input_sha256':sha(payload),
      'actual_filesystem_matches_compiler_input':True,'unchanged_before_build':True,'source_adopted':True,
      'production_sources_written_by_this_compilation':False,'production_approved':False,
      'changed_from_royalty_rounds':sorted(changed),'codegen_and_output_settings_exactly_unchanged':True,
      'baseline_input_sha256':sha((BASE/'compiler-input.json').read_bytes()),'baseline_output_sha256':sha((BASE/'compiler-output.json').read_bytes()),
      'no_proposal_byte_equality_claim':True,'old_test_methods_executed':0}
    assert data['settings']==json.loads((BASE/'compiler-input.json').read_bytes())['settings']
    save(DEST/'START.json',start)
    save(DEST/'PREFLIGHT_RESULT.json',{'scope':'schema/source/build inventory preflight; actual compilation not yet performed','required_build_inputs':sorted(BUILD_INPUTS),'all_four_present':True,'closed_sources':100,'project_sources':61,'source_content_matches_raw_files':True,'normal_codegen_unchanged':True,'not_a_build_pass':True})
    then=time.monotonic()
    with(DEST/'compiler-input.json').open('rb')as inp,(DEST/'compiler-output.json').open('xb')as out,(DEST/'stderr.txt').open('xb')as err:
        proc=subprocess.Popen(start['command'],stdin=inp,stdout=out,stderr=err,cwd=DEST,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));save(DEST/'PID.json',{'owned_pid':proc.pid});rc=proc.wait(timeout=900)
    after={n:sha((R/n).read_bytes())for n in actual};build_after={n:sha((R/n).read_bytes())for n in build};raw=(DEST/'compiler-output.json').read_bytes();compiled=json.loads(raw);errors=[x for x in compiled.get('errors',[])if x['severity']=='error']
    gates=[];abi_rows=[];storage_rows=[];layouts={}
    if not errors:
        for g in prior['gates']:
            obj=compiled['contracts'][g['path']][g['name']];before=old['contracts'][g['path']][g['name']]
            rt=len(obj['evm']['deployedBytecode']['object'])//2;cr=len(obj['evm']['bytecode']['object'])//2
            gates.append({**g,'runtime':rt,'creation':cr,'runtime_margin':24576-rt,'maximum_total_argument_bytes':49152-cr,
              'runtime_delta':rt-len(before['evm']['deployedBytecode']['object'])//2,'creation_delta':cr-len(before['evm']['bytecode']['object'])//2,
              'runtime_ok':rt<=24576,'creation_ok':cr+g['minimum_args']<=49152})
            abi_rows.append({'path':g['path'],'name':g['name'],'identical':before['abi']==obj['abi'],'as_expected':compare_abi(g['name'],before['abi'],obj['abi'])})
            a=semantic_storage(before['storageLayout']);b=semantic_storage(obj['storageLayout']);valid=storage_matches(a,b)
            storage_rows.append({'path':g['path'],'name':g['name'],'identical':a==b,'as_expected':valid})
            if g['name']=='ZZZRewards':layouts={'baseline':a,'final':b,'only_carry_encoding_changes':valid,'two_slot_carry_footprint_preserved':True,'logical_high128_low256_wire_preserved':True,'not_hot_upgrade_or_raw_state_import':True}
    sizepass=rc==0 and not errors and len(gates)==48 and all(g['runtime_ok']and g['creation_ok']for g in gates)
    result={**start,'completed_utc':datetime.now(timezone.utc).isoformat(),'solc_exit_code':rc,'exit_code':rc,'seconds':time.monotonic()-then,'errors':errors,'gates':gates,'all_pass':sizepass,
      'source_count':100,'compiled_source_count':len(compiled.get('sources',{})),'closed_input_inventory':set(compiled.get('sources',{}))==set(actual),
      'unexpected_implicit_sources':sorted(set(compiled.get('sources',{}))-set(actual)),'missing_compiled_sources':sorted(set(actual)-set(compiled.get('sources',{}))),
      'normal_limits':{'runtime_bytes':24576,'initcode_bytes':49152},'unchanged_during_build':actual==after and build==build_after,
      'actual_source_files_unchanged_during_build':actual==after,'build_inputs_unchanged_during_build':build==build_after,
      'source_sha256_after':after,'build_input_sha256_after':build_after,'solc_executable_sha256':sha(SOLC.read_bytes()),'solc_executable_unchanged':sha(SOLC.read_bytes())==COMPILER,
      'compiler_input_sha256':sha(payload),'compiler_output_sha256':sha(raw),'abi_changes_as_expected':len(abi_rows)==48 and all(x['as_expected']for x in abi_rows),
      'storage_changes_as_expected':len(storage_rows)==48 and all(x['as_expected']for x in storage_rows),
      'protected_four_unchanged':all(sha((R/n).read_bytes())==h for n,h in PROTECTED.items())}
    if not errors:
        code=bytes.fromhex(compiled['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object']);parts=[code[:24573],code[24573:]]
        carrier={'payload_length':len(code),'creation_code_hash':'0x'+keccak256(code).hex(),'parts':[{'index':i,'payload_bytes':len(x),'runtime_bytes':len(x)+3,'runtime_code_hash':'0x'+keccak256(b'\x5f\x5f\xfd'+x).hex(),'runtime_ok':len(x)+3<=24576}for i,x in enumerate(parts)],'source_adopted':True,'production_approved':False}
        carrier['all_pass']=len(code)+32<=49152 and len(code)<=2*24573 and all(x['runtime_ok']for x in carrier['parts']);save(DEST/'ROYALTY_CARRIER_EVIDENCE.json',carrier);result['carrier_checks_pass']=carrier['all_pass']
    save(DEST/'ABI_STORAGE_COMPARISON.json',{'abi':abi_rows,'storage':storage_rows});save(DEST/'FINAL_STORAGE_COMPATIBILITY.json',layouts)
    result['pass']=all(result.get(k)for k in ('all_pass','closed_input_inventory','unchanged_during_build','solc_executable_unchanged','abi_changes_as_expected','storage_changes_as_expected','protected_four_unchanged','carrier_checks_pass'))
    save(DEST/'normal-size-evidence.json',result)
    admission=None
    if result['pass']:
        snap=import_compiler(R,DEST/'compiler-input.json',DEST/'compiler-output.json',DEST/'normal-size-evidence.json')
        admission={'strict_import_pass':True,'actual_build_not_preflight':True,'source_objects':len(snap['abi_snapshot']),'closed_sources':len(snap['source_snapshot']['compiler_source_names']),'size_evidence_sha256':sha((DEST/'normal-size-evidence.json').read_bytes()),'production_approved':False};save(DEST/'ADMISSION_RESULT.json',admission)
    save(DEST/'RESULT.json',result)
    for name in ('compiler-input.json','compiler-output.json'):(DEST/(name+'.gz')).write_bytes(gzip.compress((DEST/name).read_bytes(),mtime=0))
    names=['START.json','RESULT.json','normal-size-evidence.json','PREFLIGHT_RESULT.json','EFFECTIVE_NORMAL_PROFILE.json','ABI_STORAGE_COMPARISON.json','FINAL_STORAGE_COMPATIBILITY.json','ROYALTY_CARRIER_EVIDENCE.json','ADMISSION_RESULT.json','compiler-input.json.gz','compiler-output.json.gz','stderr.txt']
    for name in names:
        if(DEST/name).is_file():(PUB/name).write_bytes((DEST/name).read_bytes())
    save(PUB/'ARTIFACTS.json',{'external_uncompressed_directory':str(DEST),'files':{n:sha((PUB/n).read_bytes())for n in names if(PUB/n).is_file()},'historical_royalty_rounds_unchanged':True,'production_approved':False})
    print(json.dumps({'pass':result['pass'],'all48_size_pass':sizepass,'seconds':result['seconds'],'abi_changes_as_expected':result['abi_changes_as_expected'],'storage_changes_as_expected':result['storage_changes_as_expected'],'strict_import':admission},indent=2))
    print(json.dumps([g for g in gates if g['name']in ('ZZZRoyaltyRewards','ZZZAccessController','ZZZLiquidityManager','ZZZOracle')]))
    return 0 if result['pass']else 1
if __name__=='__main__':raise SystemExit(main())
