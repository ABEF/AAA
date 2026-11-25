"""Offline public capture and source checks only; no tests, imports or network."""
from pathlib import Path
import ast,hashlib,json,re
REPORT=Path(__file__).resolve().parents[1];ROOT=REPORT.parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 evidence=REPORT/'evidence';case=evidence/'c808'
 review=json.loads((evidence/'INDEPENDENT_REVIEW.json').read_bytes());assert review['status']=='passed'and all(v['status']=='passed'for v in review['checks'].values())
 result=json.loads((case/'RESULT.json').read_bytes());assert result['success']and result['failures']==6 and result['raw_attempts']==result['raw_forwarded']==2 and result['raw_resends']==0 and result['shared_RPC_requests']==2265
 for capture in(case/'capture').glob('EXECUTION-*.json'):
  j=json.loads(capture.read_bytes());name=capture.name.removeprefix('EXECUTION-').removesuffix('.json');assert j['exit_code']==0 and sha((case/name).read_bytes())==j['artifact_sha256']
 stop=json.loads((case/'control/STOP.json').read_bytes())['after'];assert not stop['owned_cgroup']['pids']and int(stop['properties']['MainPID'])==0 and stop['properties']['ActiveState']in('inactive','failed')
 host=json.loads((evidence/'HOST_PRESERVATION.json').read_bytes());assert host['success']and host['existing_units_checked']==5 and host['non_ambient_difference_count']==0
 first=json.loads((evidence/'DIAGNOSTIC_EVIDENCE.json').read_bytes());second=json.loads((evidence/'HASH_DIAGNOSTIC_EVIDENCE.json').read_bytes());assert first['result']=='5passed'and second['result']=='2passed'and second['earlier_green_methods_rerun']==0
 for j in(first,second):assert sha((ROOT/j['new_test_file']).read_bytes())==j['new_test_sha256']
 assert sha((ROOT/'keeper/monitor.py').read_bytes())==second['final_monitor_sha256']=='5ab6bbb20eea21e301d81d2e829a827594079561e2f10770336ec8585b234631'
 protected={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4','scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b','tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9','tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
 for path,pin in protected.items():assert sha((ROOT/path).read_bytes())==pin,path
 paths=[]
 for p in REPORT.rglob('*'):
  if not p.is_file()or'__pycache__'in p.parts:continue
  raw=p.read_bytes()
  if p.suffix=='.py':ast.parse(raw,filename=str(p))
  if p.suffix=='.json':json.loads(raw)
  if p.suffix=='.md':
   for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',raw.decode()):
    if not target.startswith(('https:','http:','#')):paths.append(p.parent/target.split('#',1)[0])
  assert re.search(rb'(?m)^\s*-----BEGIN (?:OPENSSH )?PRIVATE KEY-----\s*$',raw)is None
 summary={'schema':1,'status':'passed','original_source_and_capture_hashes_verified':True,'independent_checks':8,'new_distinct_unit_methods':7,'unchanged_methods_rerun':0,'stopped_unit_empty_group':True,'five_original_service_states_preserved':True,'protected_dirty_files_unchanged':True,'report_relative_links':len(paths),'production_approved':False,'runtime_actions':0,'network_calls':0,'private_original_archives_required_for_full_source_replay':True}
 (REPORT/'verification/PUBLIC_VERIFICATION.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf8')
 files=sorted(p for p in REPORT.rglob('*')if p.is_file()and p.name!='EVIDENCE_MANIFEST.json'and'__pycache__'not in p.parts)
 manifest={'schema':1,'report':REPORT.name,'members':{str(p.relative_to(REPORT)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in files}}
 (REPORT/'verification/EVIDENCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf8')
 assert all(p.is_file()for p in paths),paths
 print(json.dumps({**summary,'manifest_members':len(files)},sort_keys=True))
if __name__=='__main__':main()
