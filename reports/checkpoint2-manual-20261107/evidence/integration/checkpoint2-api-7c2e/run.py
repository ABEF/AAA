import hashlib, io, json, pathlib, sys, time, unittest
R=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=pathlib.Path(__file__).parent
sys.path.insert(0,str(R))
from frontend_api.earnings_checkpoint import source_identity
PROTECTED=('reports/source-checks.json','scripts/run-fork-checks.py','tests_python/test_fork_runner.py','tests_python/test_frontend_history.py')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(names): return {n:sha(R/n) for n in names}
suite=unittest.defaultTestLoader.loadTestsFromName('tests_python.test_earnings_checkpoint_v2')
def ids(s):
    for t in s:
        if isinstance(t,unittest.TestSuite):yield from ids(t)
        else:yield t.id()
test_ids=list(ids(suite)); before=source_identity(2); protect=hashes(PROTECTED)
testhash=sha(R/'tests_python/test_earnings_checkpoint_v2.py')
stream=io.StringIO();start=time.monotonic()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
elapsed=time.monotonic()-start;after=source_identity(2);protect_after=hashes(PROTECTED)
with (E/'final15.log').open('x',encoding='utf-8',newline='\n') as f:f.write(stream.getvalue())
record=dict(status='PASS' if result.wasSuccessful() and before==after and protect==protect_after else 'FAIL',
    tests_run=result.testsRun,distinct_test_ids=test_ids,failures=len(result.failures),errors=len(result.errors),
    skips=result.skipped,seconds=elapsed,source_identity_before=before,source_identity_after=after,
    semantic_sources_unchanged=before==after,protected_before=protect,protected_after=protect_after,
    test_sha256=testhash,test_unchanged=testhash==sha(R/'tests_python/test_earnings_checkpoint_v2.py'),
    actual_fixture_sha256=sha(R/'tests_python/fixtures/exact-lp-source7-wire.json'),
    scope='One unchanged actual 77-log producer transcript replay/Seed differential with original 26-word getter witnesses and synthetic block/time/hash embedding; fourteen explicitly synthetic fresh7 RPC tests through real SQLite/History/Projection/Earnings/checkpoint builder. No provider/runtime deployment qualification.',
    log_sha256=sha(E/'final15.log'))
with (E/'FINAL15.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:record[k] for k in ('status','tests_run','failures','errors','seconds','semantic_sources_unchanged','test_sha256')}))
if record['status']!='PASS':print(stream.getvalue())
sys.exit(0 if record['status']=='PASS' else 1)
