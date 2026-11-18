"""Closed normal build of a proposed library; does not adopt or edit sources.

All100 actual source files must exactly match the trusted prior input. Only the
explicit library override enters this proposed build. Later filesystem adoption
requires separate evidence; preparation never claims the override was on disk.
"""
from pathlib import Path
import gzip,hashlib,json,os,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[3]
COMPILER_SHA='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
LIB='src/libraries/ExactRoyaltyAllocation.sol'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n')as handle:json.dump(value,handle,indent=2);handle.write('\n')

def semantic_type(layout,key,seen=()):
    row=layout['types'][key]
    result={k:row[k]for k in ('encoding','label','numberOfBytes')}
    if key in seen:return {**result,'recursive':True}
    seen=(*seen,key)
    for name in ('key','value','base'):
        if name in row:result[name]=semantic_type(layout,row[name],seen)
    if 'members'in row:result['members']=[{'label':x['label'],'slot':x['slot'],'offset':x['offset'],
        'type':semantic_type(layout,x['type'],seen)}for x in row['members']]
    return result

def semantic_storage(layout):
    return [{'contract':x['contract'],'label':x['label'],'slot':x['slot'],'offset':x['offset'],
        'type':semantic_type(layout,x['type'])}for x in layout['storage']]

def main():
    compiler,template_dir,virtual_input,destination=(Path(x).resolve()for x in sys.argv[1:])
    destination.mkdir(parents=True,exist_ok=False)
    if sha(compiler.read_bytes())!=COMPILER_SHA:raise ValueError('Pinned compiler identity differs')
    baseline_input=(template_dir/'compiler-input.json').read_bytes()
    baseline_output=(template_dir/'compiler-output.json').read_bytes()
    template=json.loads(baseline_input);prior=json.loads(baseline_output)
    previous=json.loads((template_dir/'normal-size-evidence.json').read_bytes())
    if len(template['sources'])!=100 or len(previous['gates'])!=48 or not previous['all_pass']:
        raise ValueError('Expected trusted closed100-source/48-gate baseline')
    paths=template['sources'];actual={};mismatches=[]
    for name,row in paths.items():
        raw=(ROOT/name).read_bytes();actual[name]=sha(raw)
        if raw.decode('utf-8')!=row['content']:mismatches.append(name)
    if mismatches:raise ValueError('Raw filesystem source differs from trusted input: '+repr(mismatches))
    if set(x.relative_to(ROOT).as_posix()for x in(ROOT/'src').rglob('*.sol'))!={x for x in paths if x.startswith('src/')}:
        raise ValueError('Actual project source inventory differs')
    proposed=json.loads(virtual_input.read_bytes())['sources'][LIB]['content']
    boundary=proposed.index('library ExactRoyaltyAllocation {')
    header='''// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Exact whole-unit royalty allocation to permanent rarity tickets.
/// @dev Lazy tags are coefficients modulo2^256, not cash balances. Only tags,
/// carry and validated indices wrap. Outstanding additions, range budgets and
/// payout subtraction stay checked. Canonical export flattens holder claims;
/// historical nonempty raw books must never be reinterpreted as this layout.
'''
    final_source=header+proposed[boundary:]
    if '\r'in final_source:raise ValueError('Final proposed source must be explicit UTF8 LF')
    (destination/'PROPOSED_LIBRARY.sol').write_bytes(final_source.encode('utf-8'))
    template['sources'][LIB]['content']=final_source
    expected={n:sha(v['content'].encode())for n,v in paths.items()}
    if [n for n in paths if expected[n]!=actual[n]]!=[LIB]:raise ValueError('Only the allocator may be proposed')
    payload=json.dumps(template,separators=(',',':'),ensure_ascii=True).encode()
    (destination/'compiler-input.json').write_bytes(payload)
    observed_build={n:sha((ROOT/n).read_bytes())for n in previous['build_input_sha256']}
    command=[str(compiler),'--standard-json']
    start={'kind':'proposed_closed_normal_build','candidate_build_id':'q03-allocation-20261117',
        'command':command,'compiler_sha256':COMPILER_SHA,'baseline_input_sha256':sha(baseline_input),
        'baseline_output_sha256':sha(baseline_output),'input_sha256':sha(payload),
        'settings':template['settings'],'codegen_and_output_settings_exactly_unchanged':True,
        'actual_source_sha256_at_start':actual,'proposed_compiler_content_sha256':expected,
        'only_proposed_override':LIB,'actual_filesystem_matches_proposed_at_compile_time':False,
        'actual_raw_filesystem_matches_all_trusted_sources_at_start':True,
        'actual_source_inventory':{'project':61,'dependency':39,'closed_total':100},
        'template_build_input_sha256':previous['build_input_sha256'],
        'observed_build_input_sha256_at_start':observed_build,
        'foundry_configuration_not_consumed_by_this_standard_json_compilation':True,
        'production_edited':False,'source_adopted':False,'production_approved':False}
    save(destination/'START.json',start)
    keep=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')
    env={k:os.environ[k]for k in keep if k in os.environ}
    env['PATH']=str(compiler.parent)+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32')
    began=time.monotonic()
    with(destination/'compiler-input.json').open('rb')as inp,(destination/'compiler-output.json').open('xb')as out,(destination/'stderr.txt').open('xb')as err:
        process=subprocess.Popen(command,stdin=inp,stdout=out,stderr=err,cwd=destination,env=env,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));save(destination/'PID.json',{'owned_pid':process.pid})
        try:status=process.wait(timeout=900)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10);raise
    after={n:sha((ROOT/n).read_bytes())for n in paths}
    if actual!=after:raise ValueError('Actual source files changed while preparing proposed build')
    if sha(compiler.read_bytes())!=COMPILER_SHA:raise ValueError('Compiler changed')
    raw=(destination/'compiler-output.json').read_bytes();compiled=json.loads(raw)
    errors=[x for x in compiled.get('errors',[])if x['severity']=='error']
    gates=[];abi=[];storage=[]
    if not errors:
        for gate in previous['gates']:
            obj=compiled['contracts'][gate['path']][gate['name']];old=prior['contracts'][gate['path']][gate['name']]
            runtime=len(obj['evm']['deployedBytecode']['object'])//2;creation=len(obj['evm']['bytecode']['object'])//2
            gates.append({**gate,'runtime':runtime,'creation':creation,'runtime_margin':24576-runtime,
                'maximum_total_argument_bytes':49152-creation,'runtime_ok':runtime<=24576,
                'creation_ok':creation+gate['minimum_args']<=49152})
            abi.append({'path':gate['path'],'name':gate['name'],'identical':obj['abi']==old['abi']})
            before_layout=semantic_storage(old['storageLayout']);new_layout=semantic_storage(obj['storageLayout'])
            if before_layout!=new_layout:
                storage.append({'path':gate['path'],'name':gate['name'],'old':before_layout,'proposed':new_layout})
    closure=set(compiled.get('sources',{}))==set(paths)
    layout_expected=False
    if len(storage)==1 and storage[0]['path']=='src/ZZZRoyaltyRewards.sol':
        old=storage[0]['old'];new=storage[0]['proposed']
        changed=[(x,y)for x,y in zip(old,new)if x!=y]
        if len(old)==len(new)and len(changed)==1:
            left,right=changed[0]
            book_old=left['type']['value']['value'];book_new=right['type']['value']['value']
            extra=book_new['members'][-1]
            layout_expected=(left['label']==right['label']=='allocationBooks'and left['slot']==right['slot']and
                left['offset']==right['offset']and book_old['members']==book_new['members'][:-1]and
                extra['label']=='outstanding'and extra['slot']=='1'and extra['offset']==0 and
                extra['type']['label']=='uint256'and extra['type']['numberOfBytes']=='32')
    result={'kind':'proposed_closed_normal_build','candidate_build_id':'q03-allocation-20261117',
        'exit_code':status,'seconds':time.monotonic()-began,'errors':errors,'gates':gates,
        'all_pass':status==0 and not errors and len(gates)==48 and all(g['runtime_ok']and g['creation_ok']for g in gates),
        'settings':template['settings'],'source_count':100,'compiled_source_count':len(compiled.get('sources',{})),
        'closed_input_inventory':closure,'unexpected_implicit_sources':sorted(set(compiled.get('sources',{}))-set(paths)),
        'missing_compiled_sources':sorted(set(paths)-set(compiled.get('sources',{}))),
        'compiler_input_sha256':sha(payload),'compiler_output_sha256':sha(raw),
        'solc_exit_code':status,'solc_executable_sha256':COMPILER_SHA,'solc_executable_unchanged':True,
        'source_sha256':{n:h for n,h in expected.items()if n.startswith('src/')},
        'dependency_source_sha256':{n:h for n,h in expected.items()if not n.startswith('src/')},
        'compiler_content_sha256':expected,'actual_source_sha256_before':actual,'actual_source_sha256_after':after,
        'actual_source_files_unchanged_during_build':True,'only_proposed_override':LIB,
        'actual_filesystem_matches_proposed_at_compile_time':False,'source_adopted':False,
        'abi_unchanged_all48':len(abi)==48 and all(x['identical']for x in abi),
        'semantic_storage_change_is_only_private_book_counter':layout_expected,
        'normal_limits':{'runtime_bytes':24576,'initcode_with_original_minimum_arguments_bytes':49152},
        'observed_build_input_sha256_at_start':observed_build,
        'observed_build_input_sha256_at_end':{n:sha((ROOT/n).read_bytes())for n in observed_build},
        'template_build_input_sha256':previous['build_input_sha256'],
        'old_test_methods_executed':0,'production_edited':False,'production_approved':False}
    save(destination/'ABI_STORAGE_COMPARISON.json',{'abi':abi,'storage_changes':storage,'expected_book_counter_only':layout_expected})
    if result['all_pass']and closure and result['abi_unchanged_all48']and layout_expected:
        sys.path.insert(0,str(ROOT));from zzz_ops.abi import keccak256
        code=bytes.fromhex(compiled['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
        parts=[code[:24573],code[24573:]]
        carrier={'scope':'actual compiled creation payload and constructor-defined code carriers; no deployment',
            'payload_length':len(code),'creation_code_hash':'0x'+keccak256(code).hex(),
            'royalty_initcode_including_nft_argument':len(code)+32,'royalty_initcode_ok':len(code)+32<=49152,
            'parts':[{'index':i,'payload_bytes':len(p),'runtime_bytes':len(p)+3,
                'runtime_code_hash':'0x'+keccak256(bytes.fromhex('5f5ffd')+p).hex(),'runtime_ok':len(p)+3<=24576}
                for i,p in enumerate(parts)],'source_adopted':False,'production_approved':False}
        carrier['all_pass']=carrier['royalty_initcode_ok']and len(code)<=2*24573 and all(x['runtime_ok']for x in carrier['parts'])
        save(destination/'ROYALTY_CARRIER_EVIDENCE.json',carrier)
    else:carrier={'all_pass':False}
    result['carrier_checks_pass']=carrier['all_pass'];save(destination/'normal-size-evidence.json',result)
    for name in('compiler-input.json','compiler-output.json'):
        (destination/(name+'.gz')).write_bytes(gzip.compress((destination/name).read_bytes(),mtime=0))
    print(json.dumps({k:result[k]for k in('exit_code','seconds','all_pass','compiled_source_count','closed_input_inventory','abi_unchanged_all48','semantic_storage_change_is_only_private_book_counter','carrier_checks_pass')}))
    print(json.dumps({'proposed_library_sha256':expected[LIB],'selected':[g for g in gates if g['name']in('ZZZRoyaltyRewards','ZZZAccessController','ZZZNFT','ZZZVault','ZZZOracle')]}))
    return 0 if result['all_pass']and closure and result['abi_unchanged_all48']and layout_expected and carrier['all_pass']else 1

if __name__=='__main__':raise SystemExit(main())
