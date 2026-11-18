"""Closed100-source normal compilation of explicit royalty/library overrides.

Proposal reads actual raw source and proves it matches the accepted two-source
validation build. --actual instead requires already-adopted source to match the
prepared exact compiler input/output. Neither mode writes production source.
"""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,os,subprocess,sys,time
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
COMPILER_SHA='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
OVERRIDES={'src/libraries/ExactRoyaltyAllocation.sol':'ExactRoyaltyAllocation.sol',
           'src/ZZZRoyaltyRewards.sol':'ZZZRoyaltyRewards.sol'}
sha=lambda b:hashlib.sha256(b).hexdigest()

def save(p,value):
    with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(value,f,indent=2);f.write('\n')

def semantic_type(layout,key,seen=()):
    row=layout['types'][key];r={k:row[k]for k in('encoding','label','numberOfBytes')}
    if key in seen:return {**r,'recursive':True}
    for k in('key','value','base'):
        if k in row:r[k]=semantic_type(layout,row[k],(*seen,key))
    if 'members'in row:r['members']=[{'label':x['label'],'slot':x['slot'],'offset':x['offset'],
        'type':semantic_type(layout,x['type'],(*seen,key))}for x in row['members']]
    return r

def semantic_storage(layout):
    return[{'contract':x['contract'],'label':x['label'],'slot':x['slot'],'offset':x['offset'],
        'type':semantic_type(layout,x['type'])}for x in layout['storage']]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('compiler','template','candidate','destination'):p.add_argument(name,type=Path)
    p.add_argument('--actual',action='store_true');p.add_argument('--proposal',type=Path)
    a=p.parse_args();dst=a.destination.resolve();dst.mkdir(parents=True,exist_ok=False)
    if sha(a.compiler.read_bytes())!=COMPILER_SHA:raise ValueError('Wrong compiler')
    old_input=a.template/'compiler-input.json';old_output=a.template/'compiler-output.json'
    template=json.loads(old_input.read_bytes());old=json.loads(old_output.read_bytes())
    prior=json.loads((a.template/'RESULT.json').read_bytes())
    if len(template['sources'])!=100 or len(prior['gates'])!=48 or not prior['all_pass']:raise ValueError('Invalid template')
    source=template['sources'];actual={n:sha((ROOT/n).read_bytes())for n in source}
    candidate={n:(a.candidate/f).read_bytes().decode('utf-8')for n,f in OVERRIDES.items()}
    if any('\r'in v for v in candidate.values()):raise ValueError('Candidate must be exact UTF8 LF')
    for n,row in source.items():
        expected=candidate[n]if a.actual and n in candidate else row['content']
        if (ROOT/n).read_bytes().decode('utf-8')!=expected:raise ValueError('Unexpected actual source: '+n)
    if {x.relative_to(ROOT).as_posix()for x in(ROOT/'src').rglob('*.sol')}!={n for n in source if n.startswith('src/')}:
        raise ValueError('Project source inventory differs')
    for n,body in candidate.items():source[n]['content']=body
    expected={n:sha(v['content'].encode())for n,v in source.items()}
    if a.actual and actual!=expected:raise ValueError('Actual source does not match compiler input')
    if not a.actual and {n for n in expected if expected[n]!=actual[n]}!=set(OVERRIDES):raise ValueError('Wrong proposed overrides')
    payload=json.dumps(template,separators=(',',':'),ensure_ascii=True).encode();(dst/'compiler-input.json').write_bytes(payload)
    if a.actual:
        if not a.proposal or payload!=(a.proposal/'compiler-input.json').read_bytes():raise ValueError('Actual input differs from prepared source')
    build_names=[n for n in('foundry.toml','package.json','package-lock.json','scripts/install-deps.sh')if(ROOT/n).is_file()]
    build_before={n:sha((ROOT/n).read_bytes())for n in build_names}
    cmd=[str(a.compiler.resolve()),'--standard-json']
    start={'kind':'actual_closed_normal_build'if a.actual else'proposed_closed_normal_build',
        'candidate_build_id':'q03-allocation-20261117','started_utc':datetime.now(timezone.utc).isoformat(),'command':cmd,'compiler_sha256':COMPILER_SHA,
        'baseline_input_sha256':sha(old_input.read_bytes()),'baseline_output_sha256':sha(old_output.read_bytes()),
        'input_sha256':sha(payload),'settings':template['settings'],'codegen_and_output_settings_exactly_unchanged':True,
        'actual_source_sha256_at_start':actual,'compiler_content_sha256':expected,
        'actual_filesystem_matches_compiler_input':a.actual,'actual_filesystem_matches_accepted_template':not a.actual,
        'proposed_overrides':[]if a.actual else list(OVERRIDES),'source_adopted':a.actual,
        'production_sources_written_by_this_compilation':False,
        'build_input_sha256':build_before,'production_approved':False}
    if a.actual:start.update(source_sha256=actual,unchanged_before_build=True)
    save(dst/'START.json',start)
    keep={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA'}
    env={k:v for k,v in os.environ.items()if k.upper()in keep};env['PATH']=str(a.compiler.resolve().parent)+os.pathsep+'C:/Windows/System32'
    if a.actual:
        spec=importlib.util.spec_from_file_location('_q03_global_normal_profile',ROOT/'scripts/verify-normal-profile.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        forge=a.compiler.resolve().parent.parent/'foundry-v1.4.4/forge.exe'
        save(dst/'EFFECTIVE_NORMAL_PROFILE.json',module.inspect_profile(str(forge),environment=env))
        # Prospective schema validation uses the already compiled prepared bytes;
        # it does not claim that this future compilation has happened.
        sys.path.insert(0,str(ROOT));from zzz_ops.function_reference import import_compiler
        prospective=json.loads((a.proposal/'normal-size-evidence.json').read_bytes())
        prospective.update(kind='schema_fixture_only_not_build_evidence',
            unchanged_before_build=True,unchanged_during_build=True,
            build_input_sha256=build_before,source_sha256={n:h for n,h in expected.items()if n.startswith('src/')},
            dependency_source_sha256={n:h for n,h in expected.items()if not n.startswith('src/')},
            compiler_content_sha256=expected,unexpected_implicit_sources=[],missing_compiled_sources=[],
            normal_limits={'runtime_bytes':24576,'initcode_bytes':49152})
        prospective_path=dst/'PROSPECTIVE_SCHEMA_ONLY.json';save(prospective_path,prospective)
        snapshot=import_compiler(ROOT,a.proposal/'compiler-input.json',a.proposal/'compiler-output.json',prospective_path)
        save(dst/'PREFLIGHT_RESULT.json',{'kind':'strict_importer_schema_preflight_of_prepared_artifacts',
            'pass':True,'future_compilation_has_happened':False,
            'schema_fixture_sha256':sha(prospective_path.read_bytes()),
            'source_objects':len(snapshot['abi_snapshot']),
            'closed_sources':len(snapshot['source_snapshot']['compiler_source_names']),
            'production_approved':False})
    then=time.monotonic()
    with(dst/'compiler-input.json').open('rb')as inp,(dst/'compiler-output.json').open('xb')as out,(dst/'stderr.txt').open('xb')as err:
        proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,cwd=dst,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(dst/'PID.json',{'owned_pid':proc.pid});rc=proc.wait(timeout=900)
    after={n:sha((ROOT/n).read_bytes())for n in source};build_after={n:sha((ROOT/n).read_bytes())for n in build_names}
    raw=(dst/'compiler-output.json').read_bytes();compiled=json.loads(raw);errors=[x for x in compiled.get('errors',[])if x['severity']=='error']
    gates=[];abis=[];layouts=[]
    if not errors:
        for g in prior['gates']:
            obj=compiled['contracts'][g['path']][g['name']];old_obj=old['contracts'][g['path']][g['name']]
            runtime=len(obj['evm']['deployedBytecode']['object'])//2;creation=len(obj['evm']['bytecode']['object'])//2
            gates.append({**g,'runtime':runtime,'creation':creation,'runtime_margin':24576-runtime,
                'maximum_total_argument_bytes':49152-creation,
                'runtime_delta':runtime-len(old_obj['evm']['deployedBytecode']['object'])//2,
                'creation_delta':creation-len(old_obj['evm']['bytecode']['object'])//2,
                'runtime_ok':runtime<=24576,
                'creation_ok':creation+g['minimum_args']<=49152})
            abis.append({'path':g['path'],'name':g['name'],'identical':obj['abi']==old_obj['abi']})
            layouts.append({'path':g['path'],'name':g['name'],'identical':semantic_storage(obj['storageLayout'])==semantic_storage(old_obj['storageLayout'])})
    result={**start,'completed_utc':datetime.now(timezone.utc).isoformat(),'solc_exit_code':rc,'exit_code':rc,'seconds':time.monotonic()-then,'errors':errors,
        'gates':gates,'all_pass':rc==0 and not errors and len(gates)==48 and all(g['runtime_ok']and g['creation_ok']for g in gates),
        'closed_input_inventory':set(compiled.get('sources',{}))==set(source),'source_count':100,
        'unexpected_implicit_sources':sorted(set(compiled.get('sources',{}))-set(source)),
        'missing_compiled_sources':sorted(set(source)-set(compiled.get('sources',{}))),
        'normal_limits':{'runtime_bytes':24576,'initcode_bytes':49152},
        'compiled_source_count':len(compiled.get('sources',{})),'source_sha256':{n:h for n,h in expected.items()if n.startswith('src/')},
        'dependency_source_sha256':{n:h for n,h in expected.items()if not n.startswith('src/')},
        'actual_source_sha256_after':after,'actual_source_files_unchanged_during_build':actual==after,
        'build_input_sha256_after':build_after,'build_inputs_unchanged_during_build':build_before==build_after,
        'abi_unchanged_all48':len(abis)==48 and all(x['identical']for x in abis),
        'semantic_storage_unchanged_all48':len(layouts)==48 and all(x['identical']for x in layouts),
        'solc_executable_sha256':sha(a.compiler.read_bytes()),'solc_executable_unchanged':sha(a.compiler.read_bytes())==COMPILER_SHA,
        'compiler_input_sha256':sha(payload),'compiler_output_sha256':sha(raw),'old_test_methods_executed':0}
    if a.actual:
        result.update(unchanged_before_build=True,unchanged_during_build=actual==after and build_before==build_after,
            source_unchanged=actual==after,actual_input_output_identical_to_prepared=raw==(a.proposal/'compiler-output.json').read_bytes())
    save(dst/'ABI_STORAGE_COMPARISON.json',{'abi':abis,'storage':layouts})
    if not errors:
        sys.path.insert(0,str(ROOT));from zzz_ops.abi import keccak256
        code=bytes.fromhex(compiled['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
        parts=[code[:24573],code[24573:]]
        carrier={'payload_length':len(code),'creation_code_hash':'0x'+keccak256(code).hex(),
            'parts':[{'index':i,'payload_bytes':len(x),'runtime_bytes':len(x)+3,'runtime_code_hash':'0x'+keccak256(b'\x5f\x5f\xfd'+x).hex(),
                'runtime_ok':len(x)+3<=24576}for i,x in enumerate(parts)],'source_adopted':a.actual,'production_approved':False}
        carrier['all_pass']=len(code)+32<=49152 and len(code)<=2*24573 and all(x['runtime_ok']for x in carrier['parts'])
        save(dst/'ROYALTY_CARRIER_EVIDENCE.json',carrier);result['carrier_checks_pass']=carrier['all_pass']
    save(dst/'normal-size-evidence.json',result)
    for n in('compiler-input.json','compiler-output.json'):(dst/(n+'.gz')).write_bytes(gzip.compress((dst/n).read_bytes(),mtime=0))
    required=['all_pass','closed_input_inventory','actual_source_files_unchanged_during_build','abi_unchanged_all48',
        'semantic_storage_unchanged_all48','solc_executable_unchanged','carrier_checks_pass']
    if a.actual:required+=['build_inputs_unchanged_during_build','unchanged_during_build','actual_input_output_identical_to_prepared']
    result['pass']=all(result.get(x)for x in required);save(dst/'RESULT.json',result)
    if a.actual and result['pass']:
        snapshot=import_compiler(ROOT,dst/'compiler-input.json',dst/'compiler-output.json',dst/'normal-size-evidence.json')
        save(dst/'ADMISSION_RESULT.json',{'strict_import_pass':True,
            'size_evidence_sha256':sha((dst/'normal-size-evidence.json').read_bytes()),
            'source_objects':len(snapshot['abi_snapshot']),
            'closed_sources':len(snapshot['source_snapshot']['compiler_source_names']),
            'actual_build_not_preflight':True,'production_approved':False})
    print(json.dumps({k:result[k]for k in('seconds','all_pass','abi_unchanged_all48','semantic_storage_unchanged_all48','pass')}))
    print(json.dumps([g for g in gates if g['name']in('ZZZRoyaltyRewards','ZZZAccessController','ZZZNFT','ZZZVault','ZZZOracle')]))
    return 0 if result['pass']else 1
if __name__=='__main__':raise SystemExit(main())
