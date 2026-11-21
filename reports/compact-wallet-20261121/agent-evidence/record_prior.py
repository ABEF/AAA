"""Preserve prior visible tool results; never executes any test or runtime.

These are faithful result transcriptions, not raw stdout/stderr captures.
Contemporaneous source hashes and stream separation were not captured.
"""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WEBSITE=ROOT.parent.parent/'aaa-website'
def write(name,data):
    with (HERE/name).open('xb') as output:output.write(data)
def digest(data):return hashlib.sha256(data).hexdigest()
def snapshot(name,path):
    data=path.read_bytes();write(name,data)
    return {'source':str(path),'recovered_snapshot':name,'sha256':digest(data),
        'capture_timing':'post-run recovery, not contemporaneous test-time hashing'}

sources={}
for label,path in {
    'canonical_cache.py':ROOT/'frontend_api/canonical_cache.py',
    'test_canonical_cache.py':ROOT/'tests_python/test_canonical_cache.py',
    'compact-wallet-view.test.mjs':WEBSITE/'tests/compact-wallet-view.test.mjs',
    'deployment-wallet-view.js':WEBSITE/'deployment-wallet-view.js',
    'deployment-api.js':WEBSITE/'deployment-api.js',
    'deployment-view.js':WEBSITE/'deployment-view.js',
    'build.mjs':WEBSITE/'build.mjs',
}.items():sources[label]=snapshot('recovered-'+label,path)

current=(ROOT/'frontend_api/canonical_cache.py').read_bytes()
capture=b'''        # The lookup must use the same captured containers as a possible miss.
        # Never bind a later captured query to an earlier caller-owned key.
        captured = deepcopy(params)
        key = _key(self.inner, method, captured)
        if key is None:
            return self.inner.call(method, captured)
'''
assert current.count(capture)==1
old=current.replace(capture,b'').replace(b'        result = self.inner.call(method, captured)\n',
    b'        captured = deepcopy(params)\n        result = self.inner.call(method, captured)\n')
write('reconstructed-cache-before-capture-fix.py',old)
tests=(ROOT/'tests_python/test_canonical_cache.py').read_text(encoding='utf-8')
begin=tests.index('    def test_key_is_derived_from_captured_params_even_if_source_changes_during_capture')
end=tests.index("\n\nif __name__ == '__main__':",begin)
old_tests=(tests[:begin]+tests[end:]).replace('from unittest.mock import patch\n','').encode()
write('reconstructed-cache-stage21-tests.py',old_tests)

module=(WEBSITE/'deployment-wallet-view.js').read_bytes()
new=b'.sort((a,b)=>a.address<b.address?-1:a.address>b.address?1:0)'
prior=b'.sort((a,b)=>a.address.localeCompare(b.address))'
assert module.count(new)==1
pre_ascii=module.replace(new,prior)
write('reconstructed-wallet-module-before-ascii.js',pre_ascii)

names=sorted(node.name for node in ast.walk(ast.parse(tests)) if isinstance(node,ast.FunctionDef) and node.name.startswith('test_') and node.name!='test_key_is_derived_from_captured_params_even_if_source_changes_during_capture')
assert len(names)==21
stage21=''.join(f'{name} (tests_python.test_canonical_cache.CanonicalCacheTests.{name}) ... ok\n' for name in names)
stage21+='\n----------------------------------------------------------------------\nRan 21 tests in 0.009s\n\nOK\n'
write('python-stage21.tool-output.transcript.txt',stage21.encode())
failure='''test_key_is_derived_from_captured_params_even_if_source_changes_during_capture (tests_python.test_canonical_cache.CanonicalCacheTests.test_key_is_derived_from_captured_params_even_if_source_changes_during_capture) ... FAIL

======================================================================
FAIL: test_key_is_derived_from_captured_params_even_if_source_changes_during_capture (tests_python.test_canonical_cache.CanonicalCacheTests.test_key_is_derived_from_captured_params_even_if_source_changes_during_capture)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\\Users\\Ali\\Desktop\\2.x holas\\Oto\\zzz-protocol-v2-reviewed\\zzz-protocol-v2\\tests_python\\test_canonical_cache.py", line 310, in test_key_is_derived_from_captured_params_even_if_source_changes_during_capture
    self.assertEqual([row[1][0]['data'] for row in transport.calls], ['0x87654321', '0x12345678'])
AssertionError: Lists differ: ['0x87654321'] != ['0x87654321', '0x12345678']

Second list contains 1 additional elements.
First extra element 1:
'0x12345678'

- ['0x87654321']
+ ['0x87654321', '0x12345678']

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
'''
write('python-capture-red.tool-output.transcript.txt',failure.encode())
green='''test_key_is_derived_from_captured_params_even_if_source_changes_during_capture (tests_python.test_canonical_cache.CanonicalCacheTests.test_key_is_derived_from_captured_params_even_if_source_changes_during_capture) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
'''
write('python-capture-green.tool-output.transcript.txt',green.encode())
metadata={'schema':1,'kind':'post-run faithful tool-result transcription',
    'raw_stdout_stderr_files_existed':False,'original_stream_separation_captured':False,
    'test_time_source_hashes_captured':False,'no_test_rerun_for_transcription':True,
    'transcript_newlines':'normalized LF; verbose passing method names recovered from unchanged test source and visible tool results',
    'source_recovery':sources,
    'reconstructed_sources':{
        'reconstructed-cache-before-capture-fix.py':{'sha256':digest(old),'basis':'exact owned capture-fix patch reversed; no contemporaneous hash claim'},
        'reconstructed-cache-stage21-tests.py':{'sha256':digest(old_tests),'basis':'exact owned added mutation regression/import reversed; no contemporaneous hash claim'},
        'reconstructed-wallet-module-before-ascii.js':{'sha256':digest(pre_ascii),'basis':'only the root-reported explicit ASCII comparator change reversed in current bytes; no contemporaneous byte pin claim'},
    },
    'stages':[
        {'name':'python-stage21','command':['python','-m','unittest','tests_python.test_canonical_cache','-v'],
         'cwd':str(ROOT),'tool_chunk_id':'e1839e','exit_code':0,'tests':21,'passed':21,'failed':0,'unittest_seconds':0.009,
         'transcript':'python-stage21.tool-output.transcript.txt','source_scope':'pre-capture-fix helper and 21-method test source; recovered/reconstructed above'},
        {'name':'python-capture-red','command':['python','-m','unittest','tests_python.test_canonical_cache.CanonicalCacheTests.test_key_is_derived_from_captured_params_even_if_source_changes_during_capture','-v'],
         'cwd':str(ROOT),'tool_chunk_id':'c9ada4','exit_code':1,'tests':1,'passed':0,'failed':1,'unittest_seconds':0.002,
         'transcript':'python-capture-red.tool-output.transcript.txt','source_scope':'pre-capture-fix helper, final 22-method test source'},
        {'name':'python-capture-green','command':['python','-m','unittest','tests_python.test_canonical_cache.CanonicalCacheTests.test_key_is_derived_from_captured_params_even_if_source_changes_during_capture','-v'],
         'cwd':str(ROOT),'tool_chunk_id':'a9d955','exit_code':0,'tests':1,'passed':1,'failed':0,'unittest_seconds':0.001,
         'transcript':'python-capture-green.tool-output.transcript.txt','source_scope':'final recovered helper and final 22-method test source; earlier 21 methods not rerun'},
        {'name':'node-stage80','command':['node','--test','tests/compact-wallet-view.test.mjs'],
         'cwd':str(WEBSITE),'tool_chunk_id':'2e3a35','exit_code':0,'tests':80,'passed':80,'failed':0,'skipped':0,'cancelled':0,'node_duration_ms':841.4013,
         'transcript':'node-stage80.tool-output.transcript.txt','source_scope':'earlier localeCompare module; later API/view/build newline normalization and ASCII comparator change are not mislabeled as the exact tested bytes'},
    ]}
write('PRIOR_TEST_METADATA.json',(json.dumps(metadata,indent=2)+'\n').encode())
print(json.dumps({'directory':str(HERE),'stages':4,'test_time_pins_captured':False,'files_written':len(list(HERE.iterdir()))}))
