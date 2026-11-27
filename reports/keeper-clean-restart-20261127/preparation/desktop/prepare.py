"""Archive current documents and retain private trust; no network/application work."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
HEAD='d6e8a909fd2b2a12eb1bee15173e92d526178cdb'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,check=True,timeout=30).stdout
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert git('branch','--show-current').decode().strip()=='main'
names=['.gitattributes','AGENTS.md','PROJECT_CONTEXT.md','README.md','TODO.md',
 'docs/WORK_HANDOFF.md','docs/AUDIT_FINDINGS.md','docs/OPERATOR_MANUAL.md','docs/KEEPER_ALERTS.md',
 'docs/KEEPER_BACKUP.md','docs/KEEPER_RECOVERY.md','docs/KEEPER_REHEARSALS.md',
 'docs/KEEPER_SCHEDULING.md','docs/KEEPER_SIDECAR_RECOVERY.md','docs/IMPLEMENTATION_STATUS.md',
 'docs/ROADMAP.md','docs/project-todo.json','docs/WORKLOAD_PLAN.json','docs/WORKLOAD_COVERAGE.md',
 'docs/RELEASE_CHECKLIST.md','docs/README.md','reports/README.md','scripts/verify.sh','scripts/run-keeper-tests.py']
files={}
for name in names:
    raw=(ROOT/name).read_bytes();target=BASE/'before'/name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb')as stream:stream.write(raw)
    files[name]=sha(raw)
private=V/'keeper-clean-restart-20261127';private.mkdir(mode=0o700)
with(private/'.gitignore').open('xb')as stream:stream.write(b'*\n')
for name in('private','trust'):(private/name).mkdir()
trust={}
for name,source in (
 ('C822_SOURCE_MANIFEST.json','reports/ubuntu-keeper-composition-20261126/preparation/c822/SOURCE_MANIFEST.json'),
 ('C825_RUNTIME_REVIEW.json','reports/keeper-reconstruction-20261127/evidence/campaign-002/export/RUNTIME_REVIEW.json')):
    raw=git('show',HEAD+':'+source)
    with(private/'trust'/name).open('xb')as stream:stream.write(raw)
    trust[name]={'source_commit':HEAD,'source_path':source,'bytes':len(raw),'sha256':sha(raw),'incoming_derived':False}
protected={name:sha((ROOT/name).read_bytes())for name in('reports/source-checks.json','scripts/run-fork-checks.py',
 'tests_python/test_fork_runner.py','tests_python/test_frontend_history.py')}
with(BASE/'ARCHIVE.json').open('x',encoding='utf8')as stream:
    json.dump({'head':HEAD,'files':files,'protected':protected,'private_root':str(private),'trust':trust},stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({'archived_files':len(files),'protected_files':4,'private_storage_outside_checkout':True,
 'independent_trust_records':len(trust),'remote_actions':0}))
