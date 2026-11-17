"""Package only the two already executed rights sequences; executes no tests."""
import gzip,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OWN=Path(__file__).resolve().parent
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
DEST=V/'test-impact-followup-20261117/rights-refactored'
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 execution=json.loads((DEST/'EXECUTION.json').read_text());assert execution['exit_code']==0
 raw_results=(DEST/'RESULT.json').read_bytes();result=json.loads(raw_results)
 methods=[{'id':c+'.'+n,'status':x['status'],'reason':x['reason'],'aggregate_method_gas_not_one_transaction_budget':x['kind']['Unit']['gas']} for c,s in result.items() for n,x in s['test_results'].items()]
 assert len(methods)==2 and all(x['status']=='Success' for x in methods)
 artifact=(DEST/'out/RightsImpactFollowup20261117.t.sol/RightsImpactFollowup20261117Test.json').read_bytes();meta=json.loads(artifact)['metadata']
 cache_path=V/'test-seal-deep-review-20261117/corpus-source-keccak-cache.json';cache=json.loads(cache_path.read_text())
 def kh(data):
  key=sha(data)
  if key not in cache:cache[key]='0x'+keccak256(data).hex()
  return cache[key]
 sources={}
 for name,row in meta['sources'].items():
  data=(ROOT/name).read_bytes();expected=row['keccak256'];assert expected in (kh(data),kh(data.replace(b'\r\n',b'\n'))),name
  bracketed=name in execution['source_before']
  if bracketed:assert execution['source_before'][name]==execution['source_after'][name]==sha(data),name
  sources[name]={'raw_sha256':sha(data),'compiler_keccak256':expected,'before_after_bracketed':bracketed}
 differences=[n for n in execution['source_before'] if execution['source_before'][n]!=execution['source_after'].get(n)]
 additions=sorted(set(execution['source_after'])-set(execution['source_before']))
 assert not(set(differences+additions)&set(sources))
 baseline=json.loads((OWN/'BASELINE.json').read_text());protected={n:sha((ROOT/n).read_bytes()) for n in baseline['protected']}
 assert protected==baseline['protected']
 production={n:sha((ROOT/n).read_bytes()) for n in baseline['production_solidity_sha256']}
 assert production==baseline['production_solidity_sha256']
 # Authenticate the rename only: no changed body and no dependent selector rewrite.
 name='test/RoyaltyLaunchWindow.t.sol';old=subprocess.check_output(['git','show','fdb7562:'+name],cwd=ROOT);new=(ROOT/name).read_bytes()
 assert old.replace(b'testRescheduleOnlyDuringMintAndAlwaysFullDay',b'testRescheduleOnlyDuringMintAndAlwaysFullHour').replace(b'\r\n',b'\n')==new.replace(b'\r\n',b'\n')
 initial=V/'test-impact-followup-20261117/rights-initial';initial_record=json.loads((initial/'EXECUTION.json').read_text())
 assert initial_record['exit_code']!=0 and b'Yul exception' in (initial/'stderr.log').read_bytes()
 assert sha((OWN/'RIGHTS_INITIAL_TEST.sol.txt').read_bytes())==initial_record['source_before']['test/RightsImpactFollowup20261117.t.sol']
 (OWN/'RIGHTS_INITIAL_COMPILER_STDERR.log').write_bytes((initial/'stderr.log').read_bytes())
 (OWN/'RIGHTS_RAW.json').write_bytes(raw_results)
 compressed=gzip.compress(artifact,mtime=0);(OWN/'RIGHTS_ARTIFACT.json.gz').write_bytes(compressed)
 record={'schema':1,'baseline':baseline['baseline_commit'],'selected_methods':methods,'distinct_selected_passes':2,'skips':0,'compiler':meta['compiler'],'settings':meta['settings'],'compiler_source_dependencies':sources,'selected_graph_unchanged':True,'global_test_tree_unchanged':execution['source_before']==execution['source_after'],'unrelated_modified_sources':differences,'unrelated_added_sources':additions,'production_sources_unchanged':production==baseline['production_solidity_sha256'],'protected_files':protected,'execution':execution,'raw_results_sha256':sha(raw_results),'artifact_sha256':sha(artifact),'compressed_artifact_sha256':sha(compressed),'initial_test_harness_compile_failure':{'executed_EVM_methods':0,'classification':'test-only Yul stack-depth compiler failure; compiler settings unchanged; memory struct/helper correction','stderr_sha256':sha((initial/'stderr.log').read_bytes()),'retained_test_source':'RIGHTS_INITIAL_TEST.sol.txt','retained_test_source_sha256':sha((OWN/'RIGHTS_INITIAL_TEST.sol.txt').read_bytes()),'source_before':initial_record['source_before'],'raw_result_sha256':sha((initial/'RESULT.json').read_bytes())},'rename_only':{'path':name,'baseline_raw_sha256':sha(old),'current_raw_sha256':sha(new),'body_normalized_unchanged':True,'unchanged_test_rerun':False},'scope_limits':['Real current economic modules with synthetic constant-geometry venue/authority/prices/VRF; not actual v4 placement or market qualification','One bucket, at most4minted/3activated NFTs and selected sequences; not all state combinations or maximum64currency gas','Large test-harness code-size exemption is not production runtime/initcode admission; aggregate method gas is not a deployed single-operation cost','No provider/route/VRF/OpenSea/hosting/operating/independent approval or existing-chain/signing/service work']}
 (OWN/'RIGHTS_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n')
 (V/'test-impact-followup-20261117/rights-keccak-cache.json').write_text(json.dumps(cache))
 print(json.dumps({'passes':2,'selected_compiler_sources':len(sources),'unrelated_modified_sources':differences,'unrelated_added_sources':additions,'protected_unchanged':True,'production_unchanged':True}))
if __name__=='__main__':main()
