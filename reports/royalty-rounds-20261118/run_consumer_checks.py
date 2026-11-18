"""Run only NEW11 payload5 controls and the changed historical selector control."""
from pathlib import Path
import argparse,datetime,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
EXTERNAL=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/royalty-rounds-20261118')
PROTECTED=('reports/source-checks.json','scripts/run-fork-checks.py',
    'tests_python/test_fork_runner.py','tests_python/test_frontend_history.py')
PROTECTED_PINS=dict(zip(PROTECTED,(
    '049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
    '875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
    '6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
    '361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb')))
sha=lambda b:hashlib.sha256(b).hexdigest()


def sources():
    paths={Path(__file__).resolve()}
    for folder,pattern in (('src','*.sol'),('zzz_ops','*.py'),('config','*.json')):
        paths.update((ROOT/folder).rglob(pattern))
    paths.update(ROOT/p for p in PROTECTED)
    paths.update(ROOT/'tests_python'/name for name in ('test_factory_payload5.py','test_factory_payload4.py','preseal_fixture.py'))
    return {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(paths)}


class Results(unittest.TextTestResult):
    def startTest(self,test):
        super().startTest(test);self.methods.append(test.id())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',required=True)
    parser.add_argument('--only',action='append',help='Exact method ID; later stages require an affected subset.')
    args=parser.parse_args()
    if args.stage not in ('consumer-final01','consumer-final02','consumer-final03','consumer-final04','consumer-final05'):
        raise ValueError('Use an explicit bounded new source stage')
    directory=EXTERNAL/args.stage;directory.mkdir(parents=True,exist_ok=False)
    before=sources();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    if {p:before[p] for p in PROTECTED}!=PROTECTED_PINS:raise ValueError('Protected original dirty files changed')
    (directory/'START.json').write_text(json.dumps(dict(started=started,source_sha256=before),indent=2)+'\n')
    from tests_python.test_factory_payload5 import FactoryPayload5Tests
    from tests_python.test_factory_payload4 import FactoryPayload4Tests
    names=unittest.defaultTestLoader.getTestCaseNames(FactoryPayload5Tests)
    if len(names)!=11:raise ValueError('New selection count changed')
    available={t.id():t for t in [FactoryPayload5Tests(n) for n in names]+[FactoryPayload4Tests(
        'test_bool_unknown_and_mixed_payloads_reject_before_any_observer_read')]}
    if args.stage!='consumer-final01' and not args.only:raise ValueError('Select only affected follow-up methods')
    selected=list(available) if not args.only else args.only
    if len(selected)!=len(set(selected)) or any(n not in available for n in selected):
        raise ValueError('Unknown or repeated selected method')
    suite=unittest.TestSuite([available[n] for n in selected])
    class Result(Results):methods=[]
    with (directory/'raw.log').open('w',encoding='utf-8') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
    after=sources();record=dict(schema=1,kind='NEW11 F5 plus changed1 historical selector Python methods',
        started=started,ended=datetime.datetime.now(datetime.timezone.utc).isoformat(),tests_run=result.testsRun,
        methods=result.methods,failures=[dict(method=t.id(),error=s) for t,s in result.failures],
        errors=[dict(method=t.id(),error=s) for t,s in result.errors],skips=[dict(method=t.id(),reason=s) for t,s in result.skipped],
        selected_methods=selected,source_stable=before==after,source_sha256_before=before,source_sha256_after=after,
        protected_sha256={p:before[p] for p in PROTECTED},success=result.wasSuccessful() and result.testsRun==len(selected) and before==after,
        unchanged_suites_rerun=False,evm_execution=False,rpc_performed=False,production_approved=False)
    (directory/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:record[k] for k in ('tests_run','success','source_stable')}))
    return 0 if record['success'] else 1


if __name__=='__main__':raise SystemExit(main())
