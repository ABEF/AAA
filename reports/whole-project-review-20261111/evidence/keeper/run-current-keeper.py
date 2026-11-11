from pathlib import Path
import contextlib,datetime,hashlib,importlib.util,json,sys,time,unittest
R=Path.cwd();E=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
spec=importlib.util.spec_from_file_location('whole_keeper_runner',R/'scripts/run-keeper-tests.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
stage=sys.argv[1]
extra=['test_keeper_late_job_budget']
if (R/'tests_python/test_keeper_simulation_outputs.py').is_file():extra.append('test_keeper_simulation_outputs')
modules=tuple(dict.fromkeys(tuple(runner.MODULES)+tuple(extra)))
before=runner.inputs();tests,classes=runner.select_tests(modules)
if len(sys.argv)>2 and sys.argv[2].startswith('modules:'):
 names=sys.argv[2].split(':',1)[1].split(',')
 assert len(names)==len(set(names)) and set(names)<=set(modules)
 tests={k:v for k,v in tests.items() if any(k.startswith('tests_python.'+name+'.') for name in names)}
 assert tests
elif len(sys.argv)>2 and sys.argv[2]=='simulation-only':
 tests={k:v for k,v in tests.items() if k.startswith('tests_python.test_keeper_simulation_outputs.')}
 assert len(tests)==3
elif len(sys.argv)>2:
 prior=json.loads((E/sys.argv[2]).read_text())
 wanted={row[0] for key in ('failures','errors') for row in prior[key]}
 tests={k:v for k,v in tests.items() if k in wanted}
 assert set(tests)==wanted
start=time.monotonic()
with (E/(stage+'.log')).open('x',encoding='utf-8') as stream:
 with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
  result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=runner.Results).run(unittest.TestSuite(tests.values()))
after=runner.inputs();changed={n for n in before|after if before.get(n)!=after.get(n)}
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'modules':list(modules),'classes':classes,
 'selected_methods':list(tests),'executed_methods':result.methods,'tests_run':result.testsRun,
 'failures':[(x.id(),s) for x,s in result.failures],'errors':[(x.id(),s) for x,s in result.errors],
 'skips':[(x.id(),reason) for x,reason in result.skipped],
 'source_sha256_before':before,'source_sha256_after':after,'source_changes_during_run':sorted(changed),
 'successful':not changed and result.wasSuccessful() and result.methods==list(tests),
 'seconds':round(time.monotonic()-start,3),'scope':'Existing defined-class keeper selection plus explicit new late-job/simulation cases. Offline/unit/loopback; no service/Anvil/signing rollout.'}
with (E/(stage+'.json')).open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:record[k] if k not in ('failures','errors','skips') else len(record[k]) for k in ('tests_run','failures','errors','skips','successful','source_changes_during_run','seconds')}))
raise SystemExit(0 if record['successful'] else 1)
