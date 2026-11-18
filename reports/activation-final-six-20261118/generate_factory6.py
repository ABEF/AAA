"""Generate payload6 pins only from the explicit admitted final normal build.

No compilation, RPC, signing, deployment, sealing or observed/live values.
Historical payload3/4/5 helpers, artifacts and templates remain unchanged.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
OWN=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/activation-final-six-20261118')
BUILD='activation-final-six-20261118'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
HISTORICAL={
 'zzz_ops/factory_code_v5.py':'3e41c39666784e514d35a53e6ed7996b0bd3522126d22c55dcf63dfc943dfb46',
 'config/factory-code-storage-v5.json':'d3273a94c8ffa6347bedec98947d04644a9cc3e6a156ebeceafc3d2ad3c3fd20',
 'config/production.schema17.payload5.example.json':'3469640a7ec586dad0f1037620c2ce4c02441103024d2019cafd19b0adb4366d'}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('normal_build',type=Path);args=parser.parse_args();base=args.normal_build.resolve()
 assert base.is_relative_to((OWN/'build').resolve())and re.fullmatch(r'final[0-9]{2}',base.name),'Only explicitly owned final normal build'
 before={n:sha((R/n).read_bytes())for n in HISTORICAL};assert before==HISTORICAL
 inp_raw=(base/'compiler-input.json').read_bytes();out_raw=(base/'compiler-output.json').read_bytes();evidence_raw=(base/'normal-size-evidence.json').read_bytes()
 evidence=json.loads(evidence_raw);inp=json.loads(inp_raw);out=json.loads(out_raw)
 assert evidence['candidate_build_id']==BUILD and evidence['phase']=='admitted_without_recompilation'and evidence['pass']is True and evidence['all_pass']is True
 assert evidence['compiler_input_sha256']==sha(inp_raw)and evidence['compiler_output_sha256']==sha(out_raw)
 assert len(inp['sources'])==100 and len(evidence['gates'])==48 and all(g['runtime_ok']and g['creation_ok']for g in evidence['gates'])
 sources={n:sha(row['content'].encode('utf-8'))for n,row in inp['sources'].items()}
 assert sources==evidence['compiler_content_sha256']=={n:sha((R/n).read_bytes())for n in sources}
 assert set(out['sources'])==set(sources)
 settings=inp['settings'];assert settings['evmVersion']=='cancun'and settings['viaIR']is True and settings['optimizer']=={'enabled':True,'runs':1,'details':{'yul':False}}
 raw=out['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object']
 assert isinstance(raw,str)and re.fullmatch(r'(?:[0-9a-fA-F]{2})+',raw)
 code=bytes.fromhex(raw);assert 0<len(code)<=2*24573 and len(code)+32<=49152
 spec={'schema':1,'profile':'royalty_factory_code_storage_payload_v6','code_storage_version':2,'prefix':'0x5f5ffd','data_offset':3,'max_part_data_bytes':24573,
  'compiler':{'solidity_version':'0.8.26','evm_version':'cancun','via_ir':True,'optimizer_runs':1,'yul_optimizer':False},'source_sha256':sources,
  'creation_code_length':len(code),'creation_code_hash':'0x'+keccak256(code).hex(),'parts':[]}
 for i,payload in enumerate((code[:24573],code[24573:])):
  runtime=b'\x5f\x5f\xfd'+payload;assert len(runtime)<=24576
  spec['parts'].append({'index':i,'data_length':len(payload),'runtime_length':len(runtime),'runtime_hash':'0x'+keccak256(runtime).hex()})
 old=json.loads((R/'config/factory-code-storage-v5.json').read_bytes())
 assert spec['creation_code_hash']!=old['creation_code_hash'],'New private Royalty payload must not reuse historical5 identity'
 pin=sha(json.dumps(spec,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
 artifact=R/'config/factory-code-storage-v6.json';assert not artifact.exists(),'Do not replace an existing accepted payload artifact'
 helper=R/'zzz_ops/factory_code_v6.py';text=helper.read_text(encoding='utf-8');needle='ARTIFACT_CANONICAL_SHA256=None  # Generated only from the admitted final normal build.'
 assert text.count(needle)==1,'Helper already generated or differs from preparation'
 config_path=R/'config/production.example.json';config=json.loads(config_path.read_bytes())
 for chain in config['chains']:
  assert chain['factory_payload_version']==6
  section=chain['factory_code'];section.update(creation_code_length=spec['creation_code_length'],creation_code_hash=spec['creation_code_hash'])
  assert section['review_evidence']is None and section['observed_creation_code_length']is None and section['observed_creation_code_hash']is None
  for row,part in zip(section['parts'],spec['parts']):
   assert row['address']is None and all(v is None for k,v in row.items()if k.startswith('observed_'));row.update(part)
 assert all(row['address']is None and row['runtime_hash']is None and row['observed_runtime_hash']is None
  for chain in config['chains']for group in('modules','helpers')for row in chain[group].values())
 artifact.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')
 helper.write_text(text.replace(needle,"ARTIFACT_CANONICAL_SHA256='"+pin+"'  # Exact admitted final normal source payload."),encoding='utf-8',newline='\n')
 config['_notes'][0]=config['_notes'][0].replace('Source payload pins await the admitted final normal build; no hash is guessed.','Exact source payload pins derive from the admitted final normal build; they are not deployment observations.')
 config_path.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8',newline='\n')
 assert {n:sha((R/n).read_bytes())for n in HISTORICAL}==before
 proof={'schema':1,'build_id':BUILD,'normal_build':str(base),'normal_input_sha256':sha(inp_raw),'normal_output_sha256':sha(out_raw),'normal_size_evidence_sha256':sha(evidence_raw),
  'artifact_canonical_sha256':pin,'payload6_json_sha256':sha(artifact.read_bytes()),'payload6_helper_sha256':sha(helper.read_bytes()),'fresh_template_sha256':sha(config_path.read_bytes()),
  'historical_preserved':before,'creation_code_length':len(code),'creation_code_hash':spec['creation_code_hash'],'parts':spec['parts'],'addresses_observations_approvals_adopted':False,'production_approved':False}
 target=Path(__file__).resolve().parent/'consumer/GENERATED_PINS.json';assert not target.exists();target.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(proof,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
