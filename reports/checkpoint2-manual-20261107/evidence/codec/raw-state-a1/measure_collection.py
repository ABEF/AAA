from pathlib import Path
import hashlib,json,unittest,sys
sys.path.insert(0,str(Path.cwd()))
from tests_python import test_earnings_checkpoint_v2_codec as module
r=Path.cwd();e=Path(__file__).parent
names=['frontend_api/earnings_checkpoint_v2.py','tests_python/test_earnings_checkpoint_v2_codec.py','frontend_api/earnings_exact_lp.py','frontend_api/earnings_replay.py','frontend_api/earnings_checkpoint.py','zzz_ops/exact_lp.py','zzz_ops/work_budget.py','tests_python/test_exact_lp_backend.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={n:sha(r/n) for n in names}
suite=unittest.TestSuite([module.EarningsCheckpointV2CodecTests('test_full_collection_four_buckets_preserve_raw_phase_pending_and_direct')])
with (e/'collection-measurement.log').open('w',encoding='utf-8',newline='\n') as log:
 result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
after={n:sha(r/n) for n in names}
data=dict(success=result.wasSuccessful(),tests_run=result.testsRun,measurement=module.COLLECTION_MEASUREMENT,source_before=before,source_after=after,source_unchanged=before==after)
(e/'collection-measurement.json').write_bytes((json.dumps(data,indent=2)+'\n').encode())
print(json.dumps(data,indent=2))
assert result.wasSuccessful() and before==after
