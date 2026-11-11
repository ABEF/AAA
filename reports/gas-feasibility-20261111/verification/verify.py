"""Verify published result/source integrity offline; runs no compiler or tests."""
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda name:json.loads((HERE/name).read_bytes())
execution=load('EXECUTION.json');gas=load('GAS.json');snapshot=load('SOURCE_SNAPSHOT.json')
scope=load('TEST_SCOPE.json');reuse=load('ARTIFACT_REUSE.json')
raw=gzip.decompress((HERE/'forge-results.json.gz').read_bytes())
assert sha(raw)==execution['raw_forge_json_sha256']
result=json.loads(raw)
cases={name:t for b in result.values() for name,t in b.get('test_results',{}).items()}
assert len(cases)==23 and all(t['status']=='Success' and t.get('reason') is None for t in cases.values())
assert {t['test'] for t in execution['cases']}==set(cases)
assert execution['existing_changed_methods']==18 and execution['new_maintenance_methods']==5
assert execution['original_runner']['exit_code']==1 and not execution['original_runner']['tests_rerun_for_receipt']
assert len(snapshot['source_sha256'])==200 and len(snapshot['compiler_source_id_to_path'])==197
source_checks=0
for name,expected in snapshot['source_sha256'].items():
 if name.startswith('src/') or name=='test/ReferenceExecutionContext.t.sol':
  assert sha((ROOT/name).read_bytes())==expected,name
  source_checks+=1
assert source_checks==62
assert scope['landed_raw_sha256']==execution['test_raw_sha256']
assert scope['compiled_copy_byte_identical'] and scope['original_test_method_count']==30
assert scope['changed_existing_functions']==['unlockCallback[1]','_policy2DiagnosticContribution[0]']
assert len(gas['entry_like_for_like'])==6 and len(gas['maintenance_separate_new_cohort'])==6
for row in gas['entry_like_for_like']:
 amount=row['candidate_raw_call_gas']
 assert row['candidate_full20pct']==amount+(amount+4)//5
 assert row['raw_call_saving']==row['baseline_raw_call_gas']-amount
 assert row['raw_call_saving']>0 and not row['candidate_default12M_call_succeeded']
for row in gas['maintenance_separate_new_cohort']:
 amount=row['raw_call_gas']
 assert row['frontend_full20pct']==amount+(amount+4)//5
 assert row['keeper_full25pct']==amount+(amount+3)//4
 assert not row['before_after_saving_established']
for row in reuse['existing_rpc_cases']:
 assert sha((ROOT/'tests_python/fixtures'/row['case']).read_bytes())==row['sha256']
manifest=load('ARTIFACTS.json')
for name,expected in manifest['sha256'].items():
 assert sha((HERE/name).read_bytes())==expected,name
print(json.dumps({'status':'PASS','kind':'Offline artifact/source reconciliation, not new testing',
 'published_artifacts':len(manifest['sha256']),'current_project_sources':source_checks,
 'original_actual_rpc_fixtures_unchanged':4,'actual_evm_methods_reconciled':23},indent=2))
