"""Independent saved-evidence review only: never imports or runs test bodies."""
from pathlib import Path
import argparse,ast,hashlib,json,re

PINS={'keeper/recovery_bundle.py':'fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268',
 'scripts/keeper-recovery.py':'450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf',
 'tests_python/test_keeper_recovery_bundle.py':'e7ba697edee57e08dcf4e40e55633a2cb82b76ae592a8ebea2489c66aea016d9'}
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=a.root.resolve();report=root/'reports/keeper-backup-20261126';artifacts={};checks=[]
 def read(rel):
  path=root/rel;assert path.is_file()and not path.is_symlink();raw=path.read_bytes();assert 0<len(raw)<=1024*1024
  artifacts[rel]={'bytes':len(raw),'sha256':sha(raw)};return raw
 def load(rel):return json.loads(read(rel))
 def ok(name):checks.append({'check':name,'passed':True})
 for name,digest in PINS.items():assert sha(read(name))==digest
 test_tree=ast.parse(read('tests_python/test_keeper_recovery_bundle.py'))
 methods={c.name+'.'+n.name:n for c in test_tree.body if isinstance(c,ast.ClassDef)
  for n in c.body if isinstance(n,ast.FunctionDef)and n.name.startswith('test_')}
 assert len(methods)==33
 ok('exact_reviewed_module_CLI_and_33_method_source_identity')
 prefix='reports/keeper-backup-20261126/'
 win=load(prefix+'evidence/windows/RESULT.json');pre=load(prefix+'evidence/windows/PREEXECUTION.json')
 plan=load(prefix+'evidence/TEST_SELECTION.json');log=read(prefix+'evidence/windows/RUN.log').decode('utf8')
 selected=win['selected_NEW_methods'];assert len(selected)==len(set(selected))==31
 assert selected==pre['selected_NEW_methods']==plan['portable_methods']
 assert pre['source_pins']==PINS and plan['source_sha256']==PINS['tests_python/test_keeper_recovery_bundle.py']
 assert win['success']is True and win['tests_run']==31 and win['skipped']==1
 assert win['errors']==win['failures']==[]and win['interrupted']is None
 assert win['unchanged_test_bodies_rerun']==win['server_actions']==0 and win['original_operating_journals_accessed']is False
 assert win['source_before']==win['source_after']and len(win['source_before'])==18
 for name,digest in win['source_before'].items():assert sha(read(name))==digest
 runner=read(prefix+'preparation/run_new_windows.py');assert sha(runner)==win['runner_sha256']
 rows=re.findall(r'^([A-Za-z_][A-Za-z0-9_]*) \(([^)]+)\) \.\.\. (ok|skipped)(?:[^\n]*)$',log,re.M)
 assert len(rows)==31 and [r[1]for r in rows]==selected
 assert all(r[0]==r[1].rsplit('.',1)[-1]for r in rows)
 passed={'.'.join(r[1].split('.')[-2:])for r in rows if r[2]=='ok'}
 skipped={'.'.join(r[1].split('.')[-2:])for r in rows if r[2]=='skipped'}
 assert len(passed)==30 and len(skipped)==1 and 'Ran 31 tests'in log and 'OK (skipped=1)'in log
 ok('Windows_31_exact_NEW_selections_RUN_log_30_pass_one_skip_source_stable')
 lin=load(prefix+'evidence/ubuntu/RESULT.json');raw_stdout=read(prefix+'evidence/ubuntu/RAW_STDOUT.json')
 execution=load(prefix+'evidence/ubuntu/EXECUTION.json');build=load(prefix+'evidence/ubuntu/BUILD_RECEIPT.json')
 manifest_raw=read(prefix+'evidence/ubuntu/SOURCE_MANIFEST.json');manifest=json.loads(manifest_raw)
 approval=load(prefix+'evidence/ubuntu/EXECUTION_APPROVAL.json')
 assert json.loads(raw_stdout)==lin and sha(raw_stdout)==execution['stdout_sha256']and len(raw_stdout)==execution['stdout_bytes']
 assert execution['exit_code']==0 and execution['capture_reason']is None and execution['capture_errors']==[]
 assert execution['selection_success']is True and execution['stderr_bytes']==0 and execution['stderr_sha256']==sha(b'')
 assert execution['combined_output_limit']==65536 and execution['service_actions']==0
 assert execution['Ethereum_signer_files_read_or_copied']is False and execution['credential_contents_exported']is False
 for name,key in [('remote_capsule.py','controller'),('run_selected.py','runner')]:
  raw=read(prefix+'preparation/ubuntu/'+name);assert build[key]=={'bytes':len(raw),'sha256':sha(raw)}
 assert approval=={'bundle_sha256':build['bundle']['sha256'],'controller_sha256':build['controller']['sha256'],
  'runner_sha256':build['runner']['sha256']}
 assert execution['bundle_sha256']==approval['bundle_sha256']and execution['controller_sha256']==approval['controller_sha256']
 assert build['source_manifest']=={'bytes':len(manifest_raw),'sha256':sha(manifest_raw)}
 assert build['source_members']==20 and build['archive_members']==21 and manifest['source_head']=='f36b848278479ca1cb9499d5fa831757b1e34c45'
 assert len(manifest['members'])==20
 assert lin['source_before']==lin['source_after']and lin['source_files_unchanged']is True and len(lin['source_before'])==21
 assert lin['source_before']['SOURCE_MANIFEST.json']==sha(manifest_raw)==lin['source_manifest_sha256']
 for name,pin in manifest['members'].items():
  assert lin['source_before'][name]==pin['sha256']
  rel=name.removeprefix('source/')
  raw=read(prefix+'preparation/ubuntu/run_selected.py')if rel=='run_selected.py'else read(rel)
  assert pin=={'bytes':len(raw),'sha256':sha(raw)}
 ok('Ubuntu_exact_raw_capture_build_approval_and_20_payloads_plus_manifest_unchanged')
 selected_linux=lin['selected_result']['selected_methods'];assert selected_linux==manifest['selected_methods']==build['selected_new_methods']
 assert len(selected_linux)==len(set(selected_linux))==3
 for name in selected_linux:
  node=methods['KeeperRecoveryBundleTests.'+name]
  assert sha(ast.dump(node,include_attributes=False).encode())==manifest['selected_method_AST_sha256'][name]
 inner=lin['selected_result'];assert inner['success']is True and inner['tests_run']==3 and inner['skipped']==inner['errors']==inner['failures']==0
 assert inner['method_outcomes']=={n:'passed'for n in selected_linux}and inner['error_digests_only']=={}
 assert inner['uid']==inner['gid']==65534 and inner['supplementary_groups']==[]and inner['network_and_Popen_guards']is True
 assert inner['old_test_bodies_run']==inner['previously_green_portable_methods_run']==inner['signing_attempts']==0
 assert inner['services_changed']is False and lin['services_changed']is False and lin['existing_environments_changed']is False
 assert lin['old_test_bodies_run']==lin['public_transactions']==lin['signing_attempts']==0
 assert lin['success']is True and lin['returncode']==0 and lin['child_wait_complete']is True and lin['capture_failure']is None
 assert lin['group_before_wait']==[lin['child_pid']]and lin['group_after_wait']==[]
 summary=(json.dumps({'selected_new_methods':3,'success':True,'test_errors_or_failures':0})+'\n').encode()
 assert sha(summary)==lin['stdout_sha256']and sha(b'')==lin['stderr_sha256']and len(summary)==lin['combined_output_bytes']<=65536
 inner_raw=(json.dumps(inner,sort_keys=True,allow_nan=False)+'\n').encode()
 assert sha(inner_raw)==lin['result_sha256']and build['child_work_seconds']==90 and build['failure_cleanup_seconds']==2
 ok('three_exact_new_Linux_bodies_UID65534_no_signing_services_descendants_or_capture_overflow')
 linux_passed={'KeeperRecoveryBundleTests.'+n for n in selected_linux}
 assert not passed&linux_passed and skipped<=linux_passed
 assert {'.'.join(n.split('.')[-2:])for n in pre['POSIX_methods_not_executed_here']}|skipped==linux_passed
 assert passed|linux_passed==set(methods)and len(passed|linux_passed)==33
 ok('33_distinct_passes_from_30_Windows_plus_three_Linux_no_prior_green_reexecution')
 out={'schema':1,'success':True,'checks':checks,'artifacts':artifacts,'source_pins':PINS,
  'Windows_method_invocations':31,'Windows_passes':30,'Windows_skips_retained':1,'Linux_NEW_method_invocations':3,
  'Linux_passes':3,'Linux_skips':0,'total_invocations_including_original_skip':34,'distinct_NEW_methods_passed':33,
  'previously_green_methods_reexecuted':0,'postreview_test_or_server_actions':0,'external_host_preservation_review_required':True,
  'limitations':['Saved code/results and capture integrity only; original private source-copy provenance is separately recorded',
   'No canonical freshness, signing, off-host fencing, production rollout or independent release approval'],
  'reviewer_source_sha256':sha(Path(__file__).read_bytes())}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x',encoding='utf8')as f:json.dump(out,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
 a.output.chmod(0o644)
 print(json.dumps({'success':True,'checks':len(checks),'distinct_NEW_passes':33,'original_Windows_skip_retained':1}))


if __name__=='__main__':main()
