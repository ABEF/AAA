"""Prepare exact source/docs paths without changing Git, services or tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parent
EXTERNAL=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/five-report-consolidation-20261117')


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().splitlines()


def main():
    scope=json.loads((OWN/'SCOPE.json').read_text(encoding='utf-8'))
    assert git('branch','--show-current')==['main'] and git('rev-parse','HEAD')==[scope['baseline']]
    assert not git('diff','--cached','--name-only')
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in scope['protected'].items())
    protected=set(scope['protected']);changed=set(git('diff','--name-only'))-protected
    assert not any(p.startswith('src/') for p in changed)
    assert {p for p in changed if p.startswith('zzz_ops/')}=={'zzz_ops/preseal_plan.py'}
    extra={'zzz_ops/focused_evidence.py','scripts/check-focused-evidence.py','config/focused-evidence-1c18379.json',
           'tests_python/test_focused_evidence.py','tests_python/test_preseal_operating_stops.py'}
    for path in OWN.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':extra.add(path.relative_to(ROOT).as_posix())
    manifest_path=OWN/'PUBLICATION_PREPARATION.json';extra.add(manifest_path.relative_to(ROOT).as_posix())
    paths=sorted(changed|extra);assert not(set(paths)&protected)
    archive=json.loads((OWN/'RETAINED_OBSERVATIONS.json').read_text())
    path=OWN/'retained-observations.zip';assert hashlib.sha256(path.read_bytes()).hexdigest()==archive['sha256']
    with zipfile.ZipFile(path) as z:
        assert set(z.namelist())=={r['path'] for r in archive['files']}
        for row in archive['files']:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    record={'baseline':scope['baseline'],'branch':'main','exact_expected_staged_paths':paths,
            'protected_excluded':sorted(protected),'unrelated_untracked_included':False,
            'original300report_files_preserved':True,'source_docs_only':True,'no_live_environment_actions':True}
    manifest_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    (EXTERNAL/'publication-paths.txt').write_text('\n'.join(paths)+'\n',encoding='utf-8')
    print(json.dumps({'publication_files':len(paths),'protected_excluded':len(protected),'archive_entries_checked':len(archive['files'])}))


if __name__=='__main__':main()
