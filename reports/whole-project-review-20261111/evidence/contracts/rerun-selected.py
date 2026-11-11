"""Correct only the test-signature regex and reuse the unchanged closed compile/cache."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path.cwd();B=Path(__file__).resolve().parent;P=B/'focused-6cdccb71d2'
original=json.loads((P/'START.json').read_bytes())
command=original['command'];assert command[-1].endswith(')$')
command[-1]=command[-1][:-1]+r'\(\)$'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
before={name:sha(R/name) for name in original['sources']}
assert before==original['sources']
assert before=={name:sha(P/name) for name in original['sources']}
record={'command':command,'sources':before,'reason':'Original anchored names omitted function-signature parentheses, so zero tests matched. Original non-pass retained; only selection corrected, unchanged compiled project/cache reused.'}
(P/'SELECTED_START.json').write_text(json.dumps(record,indent=2)+'\n')
env=os.environ.copy();env['RAYON_NUM_THREADS']='2';start=time.monotonic()
with (P/'forge-selected.json').open('xb') as out,(P/'forge-selected.stderr.log').open('xb') as err:
 proc=subprocess.run(command,cwd=P,env=env,stdout=out,stderr=err,timeout=1200)
output=json.loads((P/'forge-selected.json').read_bytes())
cases=[{'suite':suite,'test':name,'status':value.get('status'),'reason':value.get('reason'),'gas':value.get('gas')} for suite,body in output.items() for name,value in body.get('test_results',{}).items()]
after={name:sha(R/name)for name in original['sources']}
report={'exit_code':proc.returncode,'seconds':round(time.monotonic()-start,2),'command':command,'tests':cases,'source_unchanged':before==after,'snapshot_exact':before=={name:sha(P/name)for name in before},'sources':before,'original_selection_nonpass_retained':True}
(P/'SELECTED_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'exit_code':proc.returncode,'tests':cases,'source_unchanged':report['source_unchanged'],'snapshot_exact':report['snapshot_exact']}),flush=True)
assert proc.returncode==0 and len(cases)==38 and all(c['status']=='Success'for c in cases)and report['source_unchanged']and report['snapshot_exact']
