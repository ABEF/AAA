"""Run only explicitly named NEW stage methods and retain exact streams/pins."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WEBSITE=ROOT.parent.parent/'aaa-website'
mode=sys.argv[1]
if mode=='cache':
    stage=HERE/'cache-retention'
    methods=['oversized_malformed_reply_bypasses_cache_without_copying_it',
        'total_includes_keys_stops_at_eight_mib_and_clears_on_exit',
        'nonserializable_result_is_returned_without_memoization',
        'oversized_key_bypasses_cache_and_keeps_ordinary_budget_charges']
    command=['python','-m','unittest',*[f'tests_python.test_canonical_cache.CanonicalCacheTests.test_retention_{name}' for name in methods],'-v']
    cwd=ROOT
    paths=[*sorted((ROOT/'frontend_api').glob('*.py')),*sorted((ROOT/'zzz_ops').glob('*.py')),ROOT/'tests_python/test_canonical_cache.py']
    snapshots=[ROOT/'frontend_api/canonical_cache.py',ROOT/'tests_python/test_canonical_cache.py']
elif mode=='node':
    stage=HERE/'node-producer'
    command=['node','--test','--test-name-pattern','^NEW producer','tests/compact-wallet-view.test.mjs']
    cwd=WEBSITE
    paths=[*sorted(WEBSITE.glob('*.js')),*sorted((WEBSITE/'tests/helpers').glob('*.mjs')),
        *sorted((WEBSITE/'tests/fixtures/compact-wallet-20261121').glob('*.json')),
        WEBSITE/'tests/fixtures/source10-api.json',WEBSITE/'tests/compact-wallet-view.test.mjs',WEBSITE/'package.json']
    snapshots=[WEBSITE/'deployment-wallet-view.js',WEBSITE/'deployment-api.js',WEBSITE/'deployment-view.js',WEBSITE/'tests/compact-wallet-view.test.mjs']
elif mode=='node-followup':
    stage=HERE/'node-followup'
    selection='^NEW producer (portfolio capability|exact service_busy|generic confirmed|portfolio final identity)|^NEW compact later currency HTTP 503'
    command=['node','--test','--test-name-pattern',selection,'tests/compact-wallet-view.test.mjs']
    cwd=WEBSITE
    paths=[*sorted(WEBSITE.glob('*.js')),*sorted((WEBSITE/'tests/helpers').glob('*.mjs')),
        *sorted((WEBSITE/'tests/fixtures/compact-wallet-20261121').glob('*.json')),
        WEBSITE/'tests/fixtures/source10-api.json',WEBSITE/'tests/compact-wallet-view.test.mjs',WEBSITE/'package.json']
    snapshots=[WEBSITE/'deployment-wallet-view.js',WEBSITE/'deployment-api.js',WEBSITE/'deployment-view.js',WEBSITE/'tests/compact-wallet-view.test.mjs']
else:raise ValueError('Unknown NEW stage')
stage.mkdir(exist_ok=False)
def hashes():return {str(path.relative_to(cwd)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
before=hashes()
for path in snapshots:
    with (stage/('before-'+path.name)).open('xb') as output:output.write(path.read_bytes())
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
begin=time.monotonic()
result=subprocess.run(command,cwd=cwd,capture_output=True,check=False)
after=hashes()
for name,data in [('stdout',result.stdout),('stderr',result.stderr)]:
    with (stage/(name+'.log')).open('xb') as output:output.write(data)
record={'schema':1,'command':command,'cwd':str(cwd),'started_utc':started,'elapsed_seconds':time.monotonic()-begin,
    'exit_code':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),
    'stderr_sha256':hashlib.sha256(result.stderr).hexdigest(),'source_hashes_before':before,'source_hashes_after':after,
    'source_bytes_unchanged_during_stage':before==after,'selection':'Only explicitly NEW methods; earlier passing bodies not rerun'}
with (stage/'RESULT.json').open('x',encoding='utf-8') as output:json.dump(record,output,indent=2)
print(json.dumps({'stage':str(stage),'exit_code':result.returncode,'source_bytes_unchanged':before==after}))
sys.stdout.buffer.write(result.stdout)
sys.stdout.buffer.write(result.stderr)
raise SystemExit(result.returncode)
