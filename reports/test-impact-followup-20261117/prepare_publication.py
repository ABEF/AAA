"""Exact allowlist for source/docs publication; no Git mutation or test execution."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parent
EXTERNAL=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-impact-followup-20261117')


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().splitlines()


def main():
    baseline=json.loads((OWN/'BASELINE.json').read_text(encoding='utf-8'))
    assert git('branch','--show-current')==['main']
    assert git('rev-parse','HEAD')==[baseline['baseline_commit']]
    assert not git('diff','--cached','--name-only')
    protected=set(baseline['protected'])
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==pin for name,pin in baseline['protected'].items())
    changed=set(git('diff','--name-only'))-protected
    assert not any(name.startswith('src/') for name in changed)
    assert {name for name in changed if name.startswith('zzz_ops/')}=={'zzz_ops/manual_lp_review.py'}
    extra={'test/LPFixtureImpact20261117.t.sol','test/RightsImpactFollowup20261117.t.sol','tests_python/test_manual_final_anchor.py'}
    for path in OWN.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':extra.add(path.relative_to(ROOT).as_posix())
    record_path=OWN/'PUBLICATION_PREPARATION.json';extra.add(record_path.relative_to(ROOT).as_posix())
    paths=sorted(changed|extra);assert not(set(paths)&protected)
    for name in paths:
        if name!=record_path.relative_to(ROOT).as_posix():assert (ROOT/name).is_file(),name
    record={'baseline':baseline['baseline_commit'],'branch':'main','exact_expected_staged_paths':paths,
            'protected_excluded':sorted(protected),'unrelated_untracked_included':False,
            'source_docs_only':True,'public_deployment_signing_service_existing_chain_actions':[]}
    record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    (EXTERNAL/'publication-paths.txt').write_text('\n'.join(paths)+'\n',encoding='utf-8')
    print(json.dumps({'publication_files':len(paths),'protected_excluded':len(protected)}))


if __name__=='__main__':main()
