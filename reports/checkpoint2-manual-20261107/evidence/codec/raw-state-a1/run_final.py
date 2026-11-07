from pathlib import Path
import hashlib,json,unittest,sys,time
sys.path.insert(0,str(Path.cwd()))
from tests_python import test_earnings_checkpoint_v2_codec as module
from frontend_api.earnings_checkpoint import SOURCE_FILES,EXACT_SOURCE_FILES
r=Path.cwd();e=Path(__file__).parent
names=sorted(set(SOURCE_FILES+EXACT_SOURCE_FILES+('tests_python/test_earnings_checkpoint_v2_codec.py','tests_python/test_exact_lp_backend.py','zzz_ops/work_budget.py','zzz_ops/exact_lp.py')))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={n:sha(r/n) for n in names};started=time.perf_counter()
with (e/'final17.log').open('w',encoding='utf-8',newline='\n') as log:
 result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
after={n:sha(r/n) for n in names}
for n in ('frontend_api/earnings_checkpoint_v2.py','tests_python/test_earnings_checkpoint_v2_codec.py'):
 dest=e/'final-sources'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((r/n).read_bytes())
data=dict(success=result.wasSuccessful(),tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),elapsed_seconds=time.perf_counter()-started,measurement=module.COLLECTION_MEASUREMENT,source_before=before,source_after=after,source_unchanged=before==after,
 stage_scope='17distinct codec methods; earlier16/17methods and separatecollectionmeasurement overlap, not additionalsuccesses. No contract/provider/service/site/journal changes.',
 retained_setup_failure='MEASUREMENT_IMPORT_FAILURE.json: externalhelperinitialsys.path omittedcheckout; correctedhelperonly; no codec/testassertionfailure',
 files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in e.iterdir() if p.is_file()})
(e/'FINAL.json').write_bytes((json.dumps(data,indent=2)+'\n').encode())
print(json.dumps({k:data[k] for k in ('success','tests_run','failures','errors','elapsed_seconds','measurement','source_unchanged')},indent=2))
assert result.wasSuccessful() and before==after
