from pathlib import Path
import hashlib,json,sys
R=Path.cwd();E=Path(__file__).resolve().parent;N=Path(sys.argv[1])
P=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/moving-market-flows-20261106-e1e736/contract-agent/normal-final-7db12e78d6')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((P/'production-size-gates.json').read_text());b=json.loads((N/'production-size-gates.json').read_text());assert a['all_pass'] and b['all_pass']
ap={**a['source_sha256'],**a['dependency_source_sha256']};bp={**b['source_sha256'],**b['dependency_source_sha256']}
assert set(ap).issubset(bp)
assert all(ap[k]==bp[k] for k in ap)
new_sources=sorted(set(bp)-set(ap));assert len(new_sources)==1 and new_sources[0].startswith('src/libraries/')
ao=json.loads((P/'compiler-output.json').read_text());bo=json.loads((N/'compiler-output.json').read_text());records=[]
for g in a['gates']:
    source,name=g['path'],g['name'];before=ao['contracts'][source][name];after=bo['contracts'][source][name]
    row={'source':source,'name':name,'abi_identical':before['abi']==after['abi'],'creation_template_identical':before['evm']['bytecode']['object']==after['evm']['bytecode']['object'],'runtime_template_identical':before['evm']['deployedBytecode']['object']==after['evm']['deployedBytecode']['object']}
    assert row['abi_identical'] and row['creation_template_identical'] and row['runtime_template_identical'],row
    records.append(row)
assert len(records)==44
new_gates=[g for g in b['gates'] if g['path'] in new_sources];assert len(new_gates)==1
assert a['factory_data_gates']==b['factory_data_gates'] and a['royalty_creation_code_hash']==b['royalty_creation_code_hash']
record={'old_closed_source_count':len(ap),'new_closed_source_count':len(bp),'old_sources_raw_byte_identical':True,'new_sources':new_sources,'previous_normal':str(P),'new_normal':str(N),'old44_normal_objects':records,'new_internal_library_shell_gate':new_gates,'new_library_unwired':True,'library_shell_does_not_prove_future_integrated_consumer_size_or_gas':True,'actual_factory_carrier_gates_unchanged':True,'royalty_payload_identical':True,'no_module_profile_or_runtime_upgrade':True,'no_deployment':True,'no_rpc':True,'normal_input_sha256':sha(N/'compiler-input.json'),'normal_output_sha256':sha(N/'compiler-output.json')}
with (E/'NORMAL_COMPARISON.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'sources':len(bp),'old_objects_identical':len(records),'new_library_gate':new_gates,'factory_carriers_unchanged':True}))
