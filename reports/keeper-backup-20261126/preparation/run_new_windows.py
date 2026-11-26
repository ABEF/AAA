"""Run only the explicitly reviewed NEW portable methods; never discover suites."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,io,json,sys,time,unittest
sys.dont_write_bytecode=True
ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
OUT=BASE/'windows-001'
PINS={'keeper/recovery_bundle.py':'fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268',
    'scripts/keeper-recovery.py':'450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf',
    'tests_python/test_keeper_recovery_bundle.py':'e7ba697edee57e08dcf4e40e55633a2cb82b76ae592a8ebea2489c66aea016d9'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def write(name,value):
    with (OUT/name).open('x',encoding='utf8')as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')


def main():
    assert not OUT.exists();OUT.mkdir(mode=0o700)
    for name,pin in PINS.items():assert sha((ROOT/name).read_bytes())==pin
    plan=json.loads((BASE/'TEST_SELECTION.json').read_bytes());names=plan['portable_methods'];assert len(names)==31
    tree=ast.parse((ROOT/'keeper/health.py').read_bytes())
    sources=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SOURCE_FILES'for t in n.targets))
    paths=sorted(set([*PINS,*sources,'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json',
        'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-FINAL_JOURNAL.json']))
    before={n:sha((ROOT/n).read_bytes())for n in paths}
    write('PREEXECUTION.json',{'source_pins':PINS,'selected_NEW_methods':names,'unchanged_methods_selected':0,
        'POSIX_methods_not_executed_here':plan['posix_methods'],'UTC':dt.datetime.now(dt.timezone.utc).isoformat()})
    started=time.monotonic();log=io.StringIO();result=None;interrupted=None
    try:
        sys.path.insert(0,str(ROOT));spec=importlib.util.spec_from_file_location('tests_python.test_keeper_recovery_bundle',ROOT/'tests_python/test_keeper_recovery_bundle.py')
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        suite=unittest.TestSuite()
        for name in names:
            prefix,cls,method=name.rsplit('.',2);assert prefix=='tests_python.test_keeper_recovery_bundle'and method.startswith('test_')and not method.startswith('test_posix_')
            suite.addTest(getattr(module,cls)(method))
        result=unittest.TextTestRunner(stream=log,verbosity=2,buffer=True).run(suite)
    except BaseException as exc:interrupted=type(exc).__name__
    after={n:sha((ROOT/n).read_bytes())for n in paths}
    (OUT/'RUN.log').write_text(log.getvalue(),encoding='utf8')
    evidence={'success':result is not None and result.wasSuccessful()and interrupted is None and before==after,
        'tests_run':None if result is None else result.testsRun,'skipped':None if result is None else len(result.skipped),
        'failures':[]if result is None else[t.id()for t,_ in result.failures],
        'errors':[]if result is None else[t.id()for t,_ in result.errors],
        'interrupted':interrupted,'elapsed_seconds':time.monotonic()-started,'selected_NEW_methods':names,
        'source_before':before,'source_after':after,'unchanged_test_bodies_rerun':0,
        'server_actions':0,'original_operating_journals_accessed':False,'runner_sha256':sha(Path(__file__).read_bytes())}
    write('RESULT.json',evidence);print(json.dumps({k:evidence[k]for k in('success','tests_run','skipped','failures','errors','elapsed_seconds','interrupted')}))
    return 0 if evidence['success']else 1


if __name__=='__main__':raise SystemExit(main())
