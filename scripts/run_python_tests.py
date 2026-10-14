"""Run real off-chain tests and mathematical specifications; not EVM execution."""
import datetime,io,json,platform,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def count(suite):
    out={}
    for item in suite:
        if isinstance(item,unittest.TestSuite):
            for k,v in count(item).items():out[k]=out.get(k,0)+v
        else:
            k=item.__class__.__module__;out[k]=out.get(k,0)+1
    return out
if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests_python'));breakdown=count(suite)
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),
       'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
       'successful':result.wasSuccessful(),'by_module':breakdown,'solidity_tests_executed':0,
       'notice':'Python model tests do not execute or verify the Solidity implementation.'}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/python-tests.log').write_text(stream.getvalue())
    (ROOT/'reports/python-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(stream.getvalue());print(json.dumps(report,indent=2));sys.exit(not result.wasSuccessful())
