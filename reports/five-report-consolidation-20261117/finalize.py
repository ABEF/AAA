"""Reconcile existing observations and preserve source/evidence; no tests run."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
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
EXTERNAL=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/five-report-consolidation-20261117')


def sha(raw):return hashlib.sha256(raw).hexdigest()
def obj(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def dump(name,value):(OWN/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    scope=obj(OWN/'SCOPE.json');docs=obj(OWN/'DOC_CHANGES.json')
    for name,row in docs.items():
        backup=EXTERNAL/'docs-before'/name
        if backup.exists():
            path=ROOT/name;a=backup.read_bytes().splitlines(keepends=True);b=path.read_bytes().splitlines(keepends=True)
            clean=lambda rows:[r.rstrip(b'\r\n') for r in rows];out=[]
            for kind,i,j,k,l in SequenceMatcher(a=clean(a),b=clean(b),autojunk=True).get_opcodes():
                out.extend(a[i:j] if kind=='equal' else b[k:l])
            assert clean(out)==clean(b);path.write_bytes(b''.join(out))
        raw=(ROOT/name).read_bytes();row['after_sha256']=sha(raw);row['after_lines']=len(raw.splitlines())
    dump('DOC_CHANGES.json',docs)
    historical={f['path']:f['sha256'] for family in scope['families'] for f in family['files']}
    assert len(historical)==300 and all(sha((ROOT/name).read_bytes())==pin for name,pin in historical.items())
    assert all(sha((ROOT/name).read_bytes())==pin for name,pin in scope['protected'].items())
    assert len(scope['all61_solidity_sha256'])==61
    assert all(sha((ROOT/name).read_bytes())==pin for name,pin in scope['all61_solidity_sha256'].items())
    normal=obj(ROOT/'reports/test-seal-deep-review-20261117/build/START.json')['source_sha256']
    assert len(normal)==100 and all(sha((ROOT/name).read_bytes())==pin for name,pin in normal.items())
    registry=obj(OWN/'RECONCILIATION.json');rows=registry['findings']
    assert len(rows)==len({r['id'] for r in rows})==registry['distinct_rows']==64
    assert dict(Counter(row['current_disposition'] for row in rows))==registry['counts']
    for row in rows:
        assert all((ROOT/x['path']).is_file() for x in row['origins'])
        assert all(sha((ROOT/x['path']).read_bytes())==x['sha256'] for x in row.get('current_source_proof',[])),row['id']
    # Count only observed new successes; do not rerun tests to fill raw-log gaps.
    evidence=obj(OWN/'EVIDENCE_CHECKS.json')
    initial=evidence['initial_observation'];assert initial['tests_run']==13 and initial['failures']==initial['errors']==initial['skips']==0
    ids=set(initial['methods'])
    for name in ('evidence-final-affected','evidence-deflate-final'):
        record=obj(OWN/(name+'.json'));assert record['exit_code']==0 and record['source_before']==record['source_after']
        raw=(OWN/(name+'.log')).read_bytes();assert sha(raw)==record['log_sha256']
        ids.update(re.findall(r'^test\w+ \(([^)]+)\) \.\.\. ok$',raw.decode('utf-8-sig').replace('\r',''),re.M))
    declared={'tests_python.test_focused_evidence.FocusedEvidenceTests.'+name for name in evidence['new_method_ast_sha256']}
    assert len(ids)==15 and ids==declared
    stops=obj(OWN/'TOOL_STOPS_AFTER.json');assert stops['success'] and not stops['failures'] and not stops['errors'] and not stops['skipped']
    assert stops['source_before']==stops['source_after'] and len(stops['selected'])==2
    groups={'new_evidence_admission':sorted(ids),'new_planner_stop_diagnostics':stops['selected']}
    assert len(set(groups['new_evidence_admission']+groups['new_planner_stop_diagnostics']))==17
    dump('SELECTED_CHECKS.json',{'distinct_new_methods_observed_passing':17,'groups':groups,
        'scope':'Recorded explicit source stages; initial13observation lacks rawterminal log as disclosed',
        'historical_suites_or_EVM_rerun':False})
    admission=obj(OWN/'DEFAULT_ADMISSION.json')
    assert admission['integrity_admitted'] and admission['new_test_executions']==admission['new_EVM_executions']==0
    assert admission['production_approved'] is False and len(admission['groups'])==7 and admission['historical_method_records']==78
    current=obj(ROOT/'docs/project-todo.json');previous=obj(EXTERNAL/'docs-before/docs/project-todo.json')
    statuses=lambda a:{t['id']:t['status'] for area in a['areas'] for t in area['tasks']}
    assert statuses(current)==statuses(previous)
    commands=[[sys.executable,'scripts/generate-function-reference.py','--check'],
              [sys.executable,'scripts/generate-operator-reference.py','--check'],
              [sys.executable,'scripts/sync-project-todo.py','--check'],
              ['git','-c','core.whitespace=cr-at-eol','diff','--check']]
    def run(command):
        r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        return {'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    with ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(run,commands))
    assert all(row['exit_code']==0 for row in checks),checks
    changed=set(subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines())-set(scope['protected'])
    assert not any(name.startswith('src/') for name in changed)
    assert {name for name in changed if name.startswith('reports/')}<= {'reports/README.md'}
    extra={'zzz_ops/focused_evidence.py','scripts/check-focused-evidence.py','config/focused-evidence-1c18379.json',
           'tests_python/test_focused_evidence.py','tests_python/test_preseal_operating_stops.py'}
    paths=sorted(changed|extra);pins={name:sha((ROOT/name).read_bytes()) for name in paths}
    markdown={ROOT/name for name in paths if name.endswith('.md')}|set(OWN.glob('*.md'));links=[]
    for path in markdown:
        for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
            target=raw.strip().strip('<>')
            if not target or target.startswith(('#','https:','http:','mailto:','codex:','plugin:')):continue
            target=re.sub(r':\d+$','',unquote(target.split('#',1)[0]))
            resolved=Path(target) if re.match(r'^[A-Za-z]:[/\\]',target) else path.parent/target
            links.append({'from':path.relative_to(ROOT).as_posix(),'target':raw,'exists':resolved.exists()})
    assert all(row['exists'] for row in links),[row for row in links if not row['exists']]
    archive=OWN/'retained-observations.zip';items=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(EXTERNAL.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.json','.log','.txt','.py','.gz'):continue
            relative=path.relative_to(EXTERNAL)
            if '__pycache__' in relative.parts or 'docs-before' in relative.parts:continue
            raw=path.read_bytes();items.append({'path':relative.as_posix(),'bytes':len(raw),'sha256':sha(raw)});z.writestr(relative.as_posix(),raw)
    dump('RETAINED_OBSERVATIONS.json',{'archive':archive.name,'sha256':sha(archive.read_bytes()),'bytes':archive.stat().st_size,'files':items,
        'scope':'New-task observations/drivers only; original reports are pinned and preserved separately'})
    dump('COMPLETION.json',{'baseline':scope['baseline'],'all300historical_files_unchanged':True,
        'all61solidity_and100normal_sources_unchanged':True,'protected4_unchanged':True,'task_statuses_unchanged':True,
        'current_registry_rows':64,'selected_new_methods':17,'maintenance_checks':checks,'local_file_links':links,
        'current_source_sha256':pins,'default_CLI_admission':{'groups':7,'historical_records':78,'new_executions':0},
        'source_only_no_deploy_sign_service_or_existing_chain_changes':True})
    print(json.dumps({'findings':64,'new_method_observations':17,'historical_files_preserved':300,'current_source_pins':len(pins),
                      'doc_file_links':len(links),'retained_task_files':len(items),'archive_bytes':archive.stat().st_size}))


if __name__=='__main__':main()
