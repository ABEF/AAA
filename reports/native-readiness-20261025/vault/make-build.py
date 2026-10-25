from pathlib import Path
R=Path.cwd()
B=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/vault-headroom-20261025')
s=(R/'reports/comprehensive-improvement-20261025/core/build-final.py').read_text(encoding='utf-8-sig')
s=s.replace("B=E/'comprehensive-improvement-20261025'", "B=E/'vault-headroom-20261025'")
s=s.replace("['abi','evm.bytecode.object','evm.deployedBytecode.object','metadata']", "['abi','storageLayout','evm.bytecode.object','evm.deployedBytecode.object','metadata']")
insert='''baseline=subprocess.run(['git','show','HEAD:src/ZZZVault.sol'],cwd=R,capture_output=True,check=True).stdout.decode('utf-8-sig')
(B/'published-baseline-vault.sol').write_text(baseline,encoding='utf-8',newline='\\n')
sources['variants/Vault_PublishedBaseline.sol']={'content':baseline.replace('contract ZZZVault is','contract Vault_PublishedBaseline is').replace('"./','"../src/')}
'''
s=s.replace("xin={'language'",insert+"xin={'language'")
s=s.replace("for path in sources}","for path in sources if path.startswith('src/')}")
append='''
def normalized_layout(value):
 types=value['storageLayout']['types']
 def typ(key):
  item=types[key]
  return {k:(typ(v) if k in ('key','value','base') else [dict(label=m['label'],slot=m['slot'],offset=m['offset'],type=typ(m['type'])) for m in v] if k=='members' else v) for k,v in item.items() if k not in ('astId','contract')}
 return [dict(label=i['label'],slot=i['slot'],offset=i['offset'],type=typ(i['type'])) for i in value['storageLayout']['storage']]
current=data['contracts']['src/ZZZVault.sol']['ZZZVault']
previous=data['contracts']['variants/Vault_PublishedBaseline.sol']['Vault_PublishedBaseline']
abi_equal=current['abi']==previous['abi'];storage_equal=normalized_layout(current)==normalized_layout(previous)
comparison={'abi_equal':abi_equal,'normalized_storage_equal':storage_equal,'baseline_runtime':len(previous['evm']['deployedBytecode']['object'])//2,'current_runtime':len(current['evm']['deployedBytecode']['object'])//2,'baseline_creation_with_args':len(previous['evm']['bytecode']['object'])//2+96,'current_creation_with_args':len(current['evm']['bytecode']['object'])//2+96,'baseline_source_sha256':hashlib.sha256(baseline.encode()).hexdigest(),'current_source_sha256':rawpins['src/ZZZVault.sol'],'baseline_normalized_storage':normalized_layout(previous),'current_normalized_storage':normalized_layout(current),'current_abi':current['abi'],'notice':'Published HEAD Vault baseline recompiled under the same normal profile with renamed contract/import path for comparison. Exact ABI and normalized storage layout, not a semantic-equivalence proof.'}
(B/'vault-abi-storage-comparison.json').write_text(json.dumps(comparison,indent=2)+'\\n',encoding='utf-8')
assert abi_equal and storage_equal and comparison['baseline_runtime']==24519
'''
needle="print(json.dumps({'elapsed':report['elapsed_seconds']"
s=s.replace(needle,append+"\n"+needle)
(B/'build-final.py').write_text(s,encoding='utf-8',newline='\n')
