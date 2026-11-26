"""Offline metadata/source/link checks; never imports tests or contacts a host."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[3]
REPORT=ROOT/'reports/ubuntu-backup-recovery-20261126'
PROTECTED={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
DOCS=['AGENTS.md','PROJECT_CONTEXT.md','README.md','TODO.md','docs/AUDIT_FINDINGS.md',
 'docs/IMPLEMENTATION_STATUS.md','docs/KEEPER_BACKUP.md','docs/KEEPER_RECOVERY.md',
 'docs/KEEPER_REHEARSALS.md','docs/OPERATOR_MANUAL.md','docs/README.md','docs/ROADMAP.md',
 'docs/WORK_HANDOFF.md','reports/README.md']
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 for name,digest in PROTECTED.items():assert sha((ROOT/name).read_bytes())==digest
 preserved={}
 for name in ('keeper-full-audit-20261126','ubuntu-daemon-storage-20261126','keeper-backup-20261126'):
  base=ROOT/'reports'/name;manifest=json.loads((base/'ARTIFACTS.json').read_bytes())
  for rel,row in manifest['files'].items():
   raw=(base/rel).read_bytes();assert len(raw)==row['bytes']and sha(raw)==row['sha256']
  preserved[name]=len(manifest['files'])
 assert preserved=={'keeper-full-audit-20261126':77,'ubuntu-daemon-storage-20261126':88,'keeper-backup-20261126':31}
 for label in ('C813','C814'):
  manifest=json.loads((REPORT/f'CURATION_{label}.json').read_bytes())
  for rel,row in manifest['copied_files'].items():
   raw=(REPORT/rel).read_bytes();assert len(raw)==row['bytes']and sha(raw)==row['sha256']
  host=json.loads((REPORT/f'verification/HOST_{label}.json').read_bytes())
  assert host['success']is True and host['non_ambient_difference_count']==0
  assert host['existing_units_checked']==5 and host['ignored_observer_invocation_count']==1
 old=json.loads((REPORT/'evidence/c813/model-RESULT.json').read_bytes())
 new=json.loads((REPORT/'evidence/c814/model-RESULT.json').read_bytes())
 assert old['success']is False and old['final_financial_error']['fixed_guard']=='Owned listener PID differs'
 assert new['success']is True and new['final_financial_capture_complete']is True
 assert not(REPORT/'evidence/c813/case-FINANCIAL_FINAL.json').exists()
 assert (REPORT/'evidence/c814/case-FINANCIAL_FINAL.json').is_file()
 outputs={}
 for name,cmd in (
  ('todo',[sys.executable,'-B','-X','utf8','scripts/sync-project-todo.py','--check']),
  ('inventory',[sys.executable,'-B','-X','utf8','scripts/build-workload-inventory.py','--check','reports/keeper-backup-20261126/FUNCTION_INVENTORY.json']),
  ('diff',['git','diff','--check','--','.gitattributes',*DOCS,'docs/project-todo.json'])):
  r=subprocess.run(cmd,cwd=ROOT,capture_output=True,check=True,timeout=30)
  assert len(r.stdout)+len(r.stderr)<32768
  outputs[name]={'exit_code':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()}
 j=json.loads((ROOT/'docs/project-todo.json').read_bytes());current={}
 def walk(value):
  if isinstance(value,dict):
   if 'id'in value and 'status'in value:current[value['id']]=value['status']
   for child in value.values():walk(child)
  elif isinstance(value,list):
   for child in value:walk(child)
 walk(j);assert len(current)==83
 baseline=json.loads(subprocess.run(['git','show','HEAD:docs/project-todo.json'],cwd=ROOT,capture_output=True,check=True).stdout)
 before=current.copy();current.clear();walk(baseline);assert current==before
 count=0
 for name in [*DOCS,'reports/ubuntu-backup-recovery-20261126/REVIEW.md']:
  path=ROOT/name
  for link in re.findall(r'\]\(([^\s)]+)(?:\s+[^)]*)?\)',path.read_text(encoding='utf8')):
   link=unquote(link.strip('<>')).split('#',1)[0]
   if not link or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',link):continue
   target=(path.parent/link).resolve();assert target.exists(),name+':'+link;count+=1
 result={'schema':1,'success':True,'prior_report_files_unchanged':preserved,
  'protected_dirty_files':PROTECTED,'stable_task_ids_and_statuses':83,'local_file_links_checked':count,
  'static_command_results':outputs,'original_c813_NONPASS_retained':True,'c814_final_vectors_present':True,
  'all_host_comparisons_pass':True,'test_bodies_run':0,'server_actions':0,'production_approved':False,
  'checker_sha256':sha(Path(__file__).read_bytes())}
 with a.output.open('x',encoding='utf8')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps({'success':True,'preserved_old_artifacts':sum(preserved.values()),'stable_tasks':83,'local_file_links':count,'tests_run':0}))


if __name__=='__main__':main()
