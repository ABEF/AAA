"""Index existing observations and verify publication inputs; executes no tests."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parent
EXTERNAL=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-impact-followup-20261117')


def read(name):return json.loads((OWN/name).read_text(encoding='utf-8-sig'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().splitlines()


def main():
    tool=[]
    for name in ('tool-tool-followup-after-01.json','tool-tool-followup-after-02.json'):
        row=read(name);assert not row['failures'] and not row['errors'] and not row['skips']
        assert row['source_unchanged'];tool+=row['executed']
    rights=read('RIGHTS_VERIFICATION.json')['selected_methods']
    physical=read('PHYSICAL_VERIFICATION.json')['selected_methods']
    assert all(row['status']=='Success' for row in rights+physical)
    groups={'tools':tool,'physical':[row['id'] for row in physical],
            'rights':[row['id'] for row in rights],'lp':read('LP_EXECUTION_RESULT.json')['passed_method_ids']}
    assert [len(rows) for rows in groups.values()]==[11,3,2,13]
    methods=[method for rows in groups.values() for method in rows]
    assert len(methods)==len(set(methods))==29
    (OWN/'SELECTED_CHECKS.json').write_text(json.dumps({'schema':1,'distinct_selected_passes':29,'groups':groups,
        'scope':'Finite observations at explicit source stages; not full branch/suite/market qualification',
        'unchanged_full_suites_rerun':False,'rename_only_not_counted':True},indent=2)+'\n',encoding='utf-8')
    # Preserve raw failures, compiler-only attempts, drivers and observation pins.
    archived=[];target=OWN/'retained-observations.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(EXTERNAL.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.json','.log','.txt','.py','.sol','.gz','.raw'):continue
            rel=path.relative_to(EXTERNAL)
            if any(p in ('out','cache','__pycache__','docs-before') or p.startswith(('out-','cache-')) or p.endswith(('-out','-cache')) for p in rel.parts[:-1]):continue
            raw=path.read_bytes();archived.append({'path':rel.as_posix(),'bytes':len(raw),'sha256':sha(raw)})
            z.writestr(rel.as_posix(),raw)
    (OWN/'RETAINED_OBSERVATIONS.json').write_text(json.dumps({'archive':target.name,'archive_bytes':target.stat().st_size,
        'archive_sha256':sha(target.read_bytes()),'files':archived,
        'scope':'Raw finite success/failure/compiler diagnostics and drivers; excluded output/cache trees are not extra evidence'},indent=2)+'\n',encoding='utf-8')
    baseline=read('BASELINE.json')
    assert all(sha((ROOT/name).read_bytes())==pin for name,pin in baseline['protected'].items())
    assert all(sha((ROOT/name).read_bytes())==pin for name,pin in baseline['production_solidity_sha256'].items())
    normal=json.loads((ROOT/'reports/test-seal-deep-review-20261117/build/START.json').read_text())
    assert len(normal['source_sha256'])==100
    assert all(sha((ROOT/name).read_bytes())==pin for name,pin in normal['source_sha256'].items())
    previous=json.loads((EXTERNAL/'docs-before/docs/project-todo.json').read_text(encoding='utf-8'))
    current=json.loads((ROOT/'docs/project-todo.json').read_text(encoding='utf-8'))
    statuses=lambda obj:{t['id']:t['status'] for area in obj['areas'] for t in area['tasks']}
    assert statuses(previous)==statuses(current)
    commands=[[sys.executable,'scripts/generate-function-reference.py','--check'],
              [sys.executable,'scripts/generate-operator-reference.py','--check'],
              [sys.executable,'scripts/sync-project-todo.py','--check'],
              ['git','-c','core.whitespace=cr-at-eol','diff','--check']]
    def run(command):
        value=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        return {'command':command,'exit_code':value.returncode,'stdout':value.stdout,'stderr':value.stderr}
    with ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(run,commands))
    assert all(row['exit_code']==0 for row in checks),checks
    changed=set(git('diff','--name-only'))-set(baseline['protected'])
    assert not any(name.startswith('src/') for name in changed)
    assert {name for name in changed if name.startswith('reports/')}<= {'reports/README.md'}
    extra=['test/LPFixtureImpact20261117.t.sol','test/RightsImpactFollowup20261117.t.sol','tests_python/test_manual_final_anchor.py']
    paths=sorted(changed|set(extra));pins={name:sha((ROOT/name).read_bytes()) for name in paths}
    markdown={ROOT/name for name in paths if name.endswith('.md')}|set(OWN.glob('*.md'))
    links=[]
    for path in sorted(markdown):
        for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
            link=raw.strip().strip('<>')
            if not link or link.startswith(('#','http:','https:','mailto:','codex:','plugin:')):continue
            link=unquote(link.split('#',1)[0]);link=re.sub(r':\d+$','',link)
            dest=Path(link) if re.match(r'^[A-Za-z]:[/\\]',link) else path.parent/link
            links.append({'from':path.relative_to(ROOT).as_posix(),'target':raw,'exists':dest.exists()})
    assert all(row['exists'] for row in links),[row for row in links if not row['exists']]
    record={'schema':1,'baseline':baseline['baseline_commit'],'source_sha256':pins,
        'all61_solidity_unchanged':True,'accepted100source_build_unchanged':True,'protected4_unchanged':True,
        'task_statuses_unchanged':True,'maintenance_checks':checks,'local_links':links,
        'new_tests_or_compiler_or_network_or_environment_actions_by_this_check':False}
    (OWN/'COMPLETION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'distinct_selected_passes':29,'archived_records':len(archived),'archive_bytes':target.stat().st_size,
                      'production_unchanged':61,'normal_sources_unchanged':100,'local_links':len(links)}))


if __name__=='__main__':main()
