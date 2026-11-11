"""Compare exact normal compiler artifacts; ignore AST identifiers, not storage types."""
from pathlib import Path
import hashlib,json,sys
B=Path(__file__).resolve().parent
V=B.parents[1]
BEFORE=V/'composite-price-20261109-0acb123/normal-final-4f5c9bf7d1'
AFTER=Path(sys.argv[1])
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
old_input=load(BEFORE/'compiler-input.json');new_input=load(AFTER/'compiler-input.json')
old=load(BEFORE/'compiler-output.json');new=load(AFTER/'compiler-output.json')
assert not [e for e in old.get('errors',[]) if e['severity']=='error']
assert not [e for e in new.get('errors',[]) if e['severity']=='error']
def storage(layout):
    types=layout['types'] or {}
    def typ(key):
        value=types[key]
        result={k:value[k] for k in ('encoding','label','numberOfBytes') if k in value}
        for k in ('base','key','value'):
            if k in value:result[k]=typ(value[k])
        if 'members' in value:
            result['members']=[field(m) for m in value['members']]
        return result
    def field(item):return {'label':item['label'],'slot':item['slot'],'offset':item['offset'],'type':typ(item['type'])}
    return [field(item) for item in layout['storage']]
def executable(obj):
    if not obj:return ''
    raw=bytes.fromhex(obj);length=int.from_bytes(raw[-2:],'big')
    assert length+2<=len(raw)
    return raw[:-length-2].hex()
rows=[];removed=[]
for source,contracts in old['contracts'].items():
    if not source.startswith('src/'):continue
    for name,obj in contracts.items():
        if name not in new.get('contracts',{}).get(source,{}):
            assert not obj['evm']['deployedBytecode']['object'],(source,name)
            removed.append({'source':source,'name':name,'no_executable_runtime':True});continue
        fresh=new['contracts'][source][name]
        raw_old=obj['evm']['deployedBytecode']['object'];raw_new=fresh['evm']['deployedBytecode']['object']
        row={'source':source,'name':name,'abi_identical':obj['abi']==fresh['abi'],
            'semantic_storage_identical':storage(obj['storageLayout'])==storage(fresh['storageLayout']),
            'runtime_before_bytes':len(raw_old)//2,'runtime_after_bytes':len(raw_new)//2,
            'executable_runtime_identical':executable(raw_old)==executable(raw_new)}
        rows.append(row)
changed_sources=[source for source in old_input['sources'] if old_input['sources'][source]!=new_input['sources'].get(source)]
new_sources=sorted(set(new_input['sources'])-set(old_input['sources']))
gates=load(AFTER/'production-size-gates.json')
result={'before':str(BEFORE),'after':str(AFTER),'baseline_input_sha256':digest(BEFORE/'compiler-input.json'),
    'final_input_sha256':digest(AFTER/'compiler-input.json'),'final_output_sha256':digest(AFTER/'compiler-output.json'),
    'changed_sources':changed_sources,'new_sources':new_sources,'removed_interface_artifacts':removed,
    'all_shared_abis_identical':all(r['abi_identical'] for r in rows),
    'all_concrete_abis_identical':all(r['abi_identical'] for r in rows if r['runtime_before_bytes']),
    'interface_only_abi_changes':[r for r in rows if not r['abi_identical'] and not r['runtime_before_bytes']],
    'all_shared_semantic_storage_identical':all(r['semantic_storage_identical'] for r in rows),
    'objects':rows,'normal_gates_pass':gates['all_pass'],
    'scope':'ABI/storage and compiler object comparison; no claim of full behavioral equivalence from bytecode size alone'}
out=B/'normal-comparison-final.json';out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('all_shared_abis_identical','all_concrete_abis_identical','all_shared_semantic_storage_identical','interface_only_abi_changes','normal_gates_pass','changed_sources','new_sources','removed_interface_artifacts')},indent=2))
print(json.dumps([r for r in rows if r['runtime_before_bytes']!=r['runtime_after_bytes']],indent=2))
assert result['all_concrete_abis_identical'] and result['all_shared_semantic_storage_identical'] and result['normal_gates_pass']
