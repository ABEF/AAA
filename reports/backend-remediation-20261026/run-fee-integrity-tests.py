"""Focused actual-Projection fee integrity checks; preserve original failures."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,io,json,sys,time,unittest

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
TARGET=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    phase=sys.argv[1]
    if phase not in ('before','after'):raise ValueError('Explicit phase required')
    paths=['frontend_api/service.py','tests_python/test_current_fee_integrity.py']
    before={p:sha(ROOT/p) for p in paths}
    suite=unittest.defaultTestLoader.loadTestsFromName('tests_python.test_current_fee_integrity.CurrentFeeIntegrityTests')
    stream=io.StringIO();start=time.monotonic()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'phase':phase,
      'scope':'New actual current/historical Projection methods; raw ABI fixtures, no real RPC or signing.',
      'source_sha256':before,'sources_unchanged':before=={p:sha(ROOT/p) for p in paths},
      'tests_run':result.testsRun,'failures':[(t.id(),str(e)) for t,e in result.failures],
      'errors':[(t.id(),str(e)) for t,e in result.errors],'skips':[(t.id(),reason) for t,reason in result.skipped],
      'successful':result.wasSuccessful(),'elapsed_seconds':round(time.monotonic()-start,3)}
    (TARGET/('fee-integrity-'+phase+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    (TARGET/('fee-integrity-'+phase+'.log')).write_text(stream.getvalue(),encoding='utf-8',newline='\n')
    print(json.dumps({k:report[k] for k in ('phase','tests_run','successful','elapsed_seconds')}))
    if phase=='after' and not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
