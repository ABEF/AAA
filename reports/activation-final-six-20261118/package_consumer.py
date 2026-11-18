"""Snapshot adopted affected consumer files; no tests, RPC or artifact adoption."""
from pathlib import Path
import gzip,hashlib,json
R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent/'consumer'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
 generated=json.loads((P/'GENERATED_PINS.json').read_bytes());passed=json.loads((P/'final02/RESULT.json').read_bytes())
 assert passed['pass']and passed['source_bracket_stable']
 current={n:sha((R/n).read_bytes())for n in passed['source_after']}
 assert current==passed['source_after'],'Adopted consumer sources differ from passing final02'
 for name,pin in generated['historical_preserved'].items():assert sha((R/name).read_bytes())==pin
 assert sha((R/'tests_python/test_factory_payload6.py').read_bytes())=='8e5a7205925784cb22123b0390f310dbaaffeba39f2724438dc1dd34a8a5a8ab'
 dest=P/'source-final';dest.mkdir(exist_ok=False)
 paths=[*current,'zzz_ops/factory_code_v5.py','config/factory-code-storage-v5.json','zzz_ops/abi.py',
  'reports/activation-final-six-20261118/generate_factory6.py','reports/activation-final-six-20261118/run_consumer_checks.py']
 rows=[]
 for i,name in enumerate(dict.fromkeys(paths)):
  raw=(R/name).read_bytes();file=f'{i:02d}-'+Path(name).name+'.gz';stored=gzip.compress(raw,mtime=0);(dest/file).write_bytes(stored)
  rows.append({'source':name,'snapshot':'source-final/'+file,'source_bytes':len(raw),'source_sha256':sha(raw),'stored_bytes':len(stored),'stored_sha256':sha(stored)})
 record={'schema':1,'kind':'adopted_affected_consumer_source_snapshot','scope':'Affected/new files and selected direct dependencies; not a claim to snapshot every Python/standard-library import.',
  'passing_current_source_stage':'final02','test_source_restored_byte_identically':True,'discarded_extra_test_adopted':False,
  'new_distinct_methods':7,'affected_distinct_methods':5,'distinct_passing_controls':12,
  'normal_build':generated['normal_build'],'normal_input_sha256':generated['normal_input_sha256'],'normal_output_sha256':generated['normal_output_sha256'],
  'historical_payload5_preserved':generated['historical_preserved'],'files':rows,'additional_test_executions':0,'production_approved':False}
 (P/'SOURCE_MANIFEST.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(rows),'new_distinct_methods':7,'affected_distinct_methods':5,'source_manifest':str(P/'SOURCE_MANIFEST.json'),'additional_tests':0},indent=2))

if __name__=='__main__':main()
