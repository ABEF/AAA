"""Offline, exact affected retry-report set; no real RPC, signer or journal."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
names=['tests_python.test_keeper_review_retry','tests_python.test_keeper_operation_review',
       'tests_python.test_keeper_harvest_identity.KeeperHarvestIdentityTests.test_source6_report_preserves_harvest_through_price_fault']
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
def flatten(item):
    if isinstance(item,unittest.TestSuite):
        for child in item:yield from flatten(child)
    else:yield item
tests=list(flatten(suite));ids=[t.id() for t in tests]
assert len(ids)==len(set(ids))
hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in
    ('keeper/operation_review.py','tests_python/test_keeper_review_retry.py')}
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(tests))
assert hashes=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in hashes}
(E/'final-review-focused.log').write_text(stream.getvalue(),encoding='utf8')
report={'baseline':'b76dfcc5d1a2513ce6b277e43a6254eb63a74640','unique_methods':len(ids),
    'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
    'skipped':len(result.skipped),'successful':result.wasSuccessful(),'ids':ids,
    'owned_whitelist':hashes,'failures_detail':[{'id':test.id(),'trace':trace} for test,trace in result.failures+result.errors]}
(E/'final-review-focused.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({key:report[key] for key in ('unique_methods','tests_run','failures','errors','skipped','successful')}))
sys.exit(0 if result.wasSuccessful() else 1)
