from pathlib import Path
import io,json,unittest,sys,time,datetime,hashlib
R=Path.cwd();sys.path.insert(0,str(R));E=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/review-policy-20261025');tag=sys.argv[1]
names=sys.argv[2:];suite=unittest.defaultTestLoader.loadTestsFromNames(names)
class Result(unittest.TextTestResult):
 def startTest(self,test):super().startTest(test);self.records.append({'test':test.id(),'status':'started'})
 def addSuccess(self,test):super().addSuccess(test);self.records[-1]['status']='passed'
 def addError(self,test,err):super().addError(test,err);self.records[-1]['status']='error'
 def addFailure(self,test,err):super().addFailure(test,err);self.records[-1]['status']='failed'
 def addSkip(self,test,reason):super().addSkip(test,reason);self.records[-1].update(status='skipped',reason=reason)
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self.records=[]
stream=io.StringIO();t=time.monotonic();result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
pins={p.as_posix():hashlib.sha256((R/p).read_bytes()).hexdigest() for p in [Path(x) for x in ('frontend_api/activation.py','frontend_api/activation_config.py','frontend_api/activation_trace.py','zzz_ops/production_observer.py','zzz_ops/production_v2.py','tests_python/test_entry_review_policy.py','tests_python/test_dual_price_integration.py','tests_python/test_frontend_activation.py','tests_python/test_typed_v4_activation.py','tests_python/dual_price_fixtures.py','tests_python/test_production_observer.py','tests_python/test_production_v2.py')]}
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-t,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'cases':result.records,'source_sha256':pins,'scope':'Focused Python mocked RPC/trace/profile cases, not Solidity execution or actual service qualification.'}
(E/(tag+'.log')).write_text(stream.getvalue(),encoding='utf-8',newline='\n');(E/(tag+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(stream.getvalue());print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','cases')},indent=2));sys.exit(not result.wasSuccessful())
