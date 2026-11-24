"""Offline artifact/source/documentation validation only; no test-suite execution."""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent;REPORT=ROOT/'reports/ubuntu-key-rotation-20261124'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def load(path):return json.loads(path.read_bytes())
protected={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4','scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b','tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9','tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
assert all(sha((ROOT/name).read_bytes())==pin for name,pin in protected.items())
for path in REPORT.rglob('*.json'):load(path)
for path in REPORT.rglob('*.py'):ast.parse(path.read_bytes())
source=load(REPORT/'evidence/c803/SOURCE_MANIFEST.json');verified=0
for name,pin in source['members'].items():
    if name=='scripts/run-fork-checks.py':continue
    raw=(ROOT/name).read_bytes();assert len(raw)==pin['bytes']and sha(raw)==pin['sha256'],name;verified+=1
assert verified==189
for tag in('c801','c802','c803'):
    build=load(REPORT/'evidence'/tag/'BUILD_RECEIPT.json')
    for name,pin in build['helpers'].items():
        raw=(REPORT/'verification'/tag/name).read_bytes();assert len(raw)==pin['bytes']and sha(raw)==pin['sha256']
    for name,key in [('remote_capsule.py','controller'),('host_control.py','host_wrapper')]:
        raw=(REPORT/'verification'/tag/name).read_bytes();assert len(raw)==build[key]['bytes']and sha(raw)==build[key]['sha256']
    stop=load(REPORT/'evidence'/tag/'control/STOP.json');assert stop['after']['owned_cgroup_pids']==[]and stop['after']['properties']['ActiveState']=='inactive'
def snapshots(value):
    if isinstance(value,dict):
        if set(('raw_utf8','bytes','sha256','state'))<=set(value):
            raw=value['raw_utf8'].encode();assert len(raw)==value['bytes']and sha(raw)==value['sha256']and json.loads(raw)==value['state']
        assert not(set(value)&{'private_key','password','password_file','keystore','mnemonic','rpc_urls'})
        for x in value.values():snapshots(x)
    elif isinstance(value,list):
        for x in value:snapshots(x)
for path in (REPORT/'evidence/c803').glob('*.json'):
    if path.name not in ('MANIFEST.json','SOURCE_MANIFEST.json'):snapshots(load(path))
original=load(REPORT/'evidence/c801/ORIGINAL_HASHLESS_JOURNAL.json');assert original['state']['pending']['hash']is None and sha(original['raw_utf8'].encode())==original['journal_sha256']
changed=('README.md','AGENTS.md','PROJECT_CONTEXT.md','docs/WORK_HANDOFF.md','docs/OPERATOR_MANUAL.md','docs/KEEPER_RECOVERY.md','docs/AUDIT_FINDINGS.md','docs/ROADMAP.md','docs/IMPLEMENTATION_STATUS.md','reports/README.md','reports/ubuntu-key-rotation-20261124/REVIEW.md');links=0
for rel in changed:
    path=ROOT/rel
    for target in re.findall(r'\]\(([^\n()]+)\)',path.read_text(encoding='utf-8')):
        if 'ubuntu-key-rotation-20261124/'not in target and rel!='reports/ubuntu-key-rotation-20261124/REVIEW.md':continue
        if target.startswith(('http://','https://')):continue
        file,_,fragment=target.partition('#');dest=(path.parent/file).resolve()if file else path
        assert dest.is_relative_to(ROOT)and(dest.is_file()or dest==REPORT/'verification/EVIDENCE_MANIFEST.json'),(rel,target)
        if fragment:
            headings=re.findall(r'^#+\s+(.+)$',dest.read_text(encoding='utf-8'),re.M);slug=lambda v:re.sub(r'[^\w\- ]','',v.lower()).replace(' ','-')
            assert fragment in map(slug,headings),(rel,fragment)
        links+=1
files=[]
for path in sorted(REPORT.rglob('*')):
    if path.is_file()and path!=REPORT/'verification/EVIDENCE_MANIFEST.json':
        raw=path.read_bytes();assert len(raw)<=16*1024*1024;assert b'PRIVATE '+b'KEY-----'not in raw
        files.append({'path':path.relative_to(REPORT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
(REPORT/'verification/EVIDENCE_MANIFEST.json').write_bytes((json.dumps({'schema':1,'source_commit':source['source_head'],'files':files,'manifest_self_excluded':True},indent=2,sort_keys=True)+'\n').encode())
path=ROOT/'reports/ubuntu-hybrid-20261124/verification/verify_saved_hybrid.py';spec=importlib.util.spec_from_file_location('public_artifact_closure',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);closure=module.public_closure(REPORT)
result={'schema':1,'evidence_closure':closure,'current_source_members_verified':verified,'four_protected_dirty_hashes_preserved':True,'all_three_new_labs_stopped':True,'journal_raw_snapshots_match_hashes_and_decoding':True,'changed_document_links_verified':links,'new_transactions':0,'old_test_bodies_run':0,'production_approved':False}
(BASE/'PUBLIC_VERIFICATION.json').write_bytes((json.dumps(result,indent=2,sort_keys=True)+'\n').encode());print(json.dumps(result))
