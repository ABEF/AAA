"""New offline evidence and documentation check, never test-suite execution."""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent;REPORT=ROOT/'reports/ubuntu-hybrid-20261124'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def save(path,data):path.write_bytes((json.dumps(data,indent=2,sort_keys=True)+'\n').encode())
protected={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4','scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b','tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9','tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
assert all(sha((ROOT/name).read_bytes())==pin for name,pin in protected.items())
for path in REPORT.rglob('*.json'):json.loads(path.read_bytes())
for path in REPORT.rglob('*.py'):ast.parse(path.read_bytes())
manifest=json.loads((REPORT/'evidence/c800/SOURCE_MANIFEST.json').read_bytes())
source=[]
for name,pin in manifest['members'].items():
    if name=='scripts/run-fork-checks.py':continue
    raw=(ROOT/name).read_bytes();assert len(raw)==pin['bytes']and sha(raw)==pin['sha256'],name;source.append(name)
assert len(source)==189
for stage in ('c7ff','c800'):
    build=json.loads((REPORT/'evidence'/stage/'BUILD_RECEIPT.json').read_bytes())
    for name,pin in build['helpers'].items():
        raw=(REPORT/'verification'/stage/name).read_bytes();assert len(raw)==pin['bytes']and sha(raw)==pin['sha256']
    for name,key in [('remote_capsule.py','controller'),('host_control.py','host_wrapper')]:
        raw=(REPORT/'verification'/stage/name).read_bytes();assert len(raw)==build[key]['bytes']and sha(raw)==build[key]['sha256']
    stop=json.loads((REPORT/'evidence'/stage/'control/STOP.json').read_bytes());assert stop['after']['owned_cgroup_pids']==[] and stop['after']['properties']['ActiveState']=='inactive'
# Check only new/changed Markdown destinations; historical links remain source-scoped.
changed=['README.md','AGENTS.md','PROJECT_CONTEXT.md','docs/WORK_HANDOFF.md','docs/OPERATOR_MANUAL.md','docs/AUDIT_FINDINGS.md','docs/ROADMAP.md','docs/IMPLEMENTATION_STATUS.md','docs/OPTIONAL_PORTFOLIO_IMPLEMENTATION.md','reports/README.md','reports/ubuntu-hybrid-20261124/REVIEW.md']
new_links=0
for rel in changed:
    path=ROOT/rel;text=path.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^\n()]+)\)',text):
        if 'ubuntu-hybrid-20261124/' not in target and not(rel.endswith('ubuntu-hybrid-20261124/REVIEW.md')):continue
        if target.startswith(('https://','http://')):continue
        file,_,fragment=target.partition('#');dest=(path.parent/file).resolve()if file else path
        assert dest.is_relative_to(ROOT) and (dest.is_file()or dest==REPORT/'verification/EVIDENCE_MANIFEST.json'),(rel,target)
        if fragment:
            headings=re.findall(r'^#+\s+(.+)$',dest.read_text(encoding='utf-8'),re.M)
            slug=lambda value:re.sub(r'[^\w\- ]','',value.lower()).replace(' ','-')
            assert fragment in [slug(h)for h in headings],(rel,fragment)
        new_links+=1
files=[]
for path in sorted(REPORT.rglob('*')):
    if path.is_file()and path!=REPORT/'verification/EVIDENCE_MANIFEST.json':
        raw=path.read_bytes();assert len(raw)<=16*1024*1024
        forbidden=[b'PRIVATE '+b'KEY-----',b'"private_'+b'key"',b'"password_'+b'contents"']
        assert all(word not in raw for word in forbidden),str(path)
        files.append({'path':path.relative_to(REPORT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
save(REPORT/'verification/EVIDENCE_MANIFEST.json',{'schema':1,'source_commit':'e20e5d602dd59226e3dfb2f03ee2d206d0b8f9e8','files':files,'manifest_self_excluded':True})
spec=importlib.util.spec_from_file_location('new_public_review',REPORT/'verification/verify_saved_hybrid.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
closure=module.public_closure(REPORT)
summary={'schema':1,'public_evidence_closure':closure,'new_markdown_links_checked':new_links,'unchanged_working_production_members':len(source),'published_protected_runfork_exclusion':True,'four_unrelated_dirty_hashes_preserved':True,'helper_controller_pins_match':True,'both_new_labs_stopped':True,'old_test_bodies_run':0,'new_transactions':0,'production_approved':False}
save(BASE/'PUBLIC_VERIFICATION.json',summary);print(json.dumps(summary))
