from pathlib import Path
import datetime,hashlib,importlib.util,json,subprocess,sys,time,unittest
R=Path.cwd();E=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
runner=load('whole_review_python_runner',R/'scripts/run_python_tests.py')
modules=('test_function_reference','test_operator_reference','test_slither_review','test_source_inventory')
before=runner.inputs();tests,classes=runner.select_tests(modules);started=time.monotonic()
with (E/'documentation-tests.log').open('x',encoding='utf-8') as log:
 result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=runner.Results).run(unittest.TestSuite(tests.values()))
after=runner.inputs()
record={'modules':modules,'selected_methods':list(tests),'executed_methods':result.methods,
 'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
 'seconds':time.monotonic()-started,'source_before':before,'source_after':after,
 'source_changes_during_run':[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)],
 'successful':result.wasSuccessful() and result.testsRun==len(tests) and result.methods==list(tests) and before==after}
with (E/'documentation-tests.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:record[k] for k in ('tests_run','failures','errors','skips','successful','seconds')}))
assert record['successful']
commands=[['scripts/generate-function-reference.py','--check'],['scripts/generate-operator-reference.py','--check'],
 ['scripts/sync-project-todo.py','--check'],['scripts/source_checks.py','--output',str(E/'source-consistency-final.json')]]
rows=[]
for args in commands:
 run=subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=R,capture_output=True,text=True)
 rows.append({'arguments':args,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
 assert run.returncode==0,rows[-1]
with (E/'document-gates.json').open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2);f.write('\n')
print('All four current generated/source gates pass.')
