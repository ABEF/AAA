import ast, hashlib, io, json, pathlib, sys, time, unittest
R=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=pathlib.Path(__file__).parent
sys.path.insert(0,str(R))
from frontend_api.earnings_checkpoint import source_identity
test='tests_python.test_earnings_checkpoint_v2.Checkpoint2APITests.test_reviewed_royalty_currency_append_preserves_exact_state_and_old_descriptors'
P=R/'tests_python/test_earnings_checkpoint_v2.py';old=(E/'test-final15.py.txt').read_bytes();new=P.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
before=source_identity(2);before_hash=sha(new)
tree=ast.parse(new)
for cls in tree.body:
    if isinstance(cls,ast.ClassDef) and cls.name=='Checkpoint2APITests':
        cls.body=[node for node in cls.body if not isinstance(node,ast.FunctionDef) or node.name!=test.split('.')[-1]]
same_ast=ast.dump(tree,include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
start=new.index(b'    def test_reviewed_royalty_currency_append_preserves_exact_state_and_old_descriptors(')
end=new.index(b"\n\nif __name__",start)
# Strip only this added final method; preserve the original two separator LFs.
same_raw=new[:start]+new[end+1:]==old
if not same_ast:raise AssertionError('Existing fifteen methods/helpers changed')
stream=io.StringIO();start_time=time.monotonic()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(test))
elapsed=time.monotonic()-start_time
with (E/'append1.log').open('x',encoding='utf-8',newline='\n') as f:f.write(stream.getvalue())
after=source_identity(2)
record=dict(status='PASS' if result.wasSuccessful() and before==after and before_hash==sha(P.read_bytes()) and same_ast else 'FAIL',
    tests_run=result.testsRun,distinct_test_ids=[test],failures=len(result.failures),errors=len(result.errors),skips=result.skipped,
    seconds=elapsed,source_identity_before=before,source_identity_after=after,semantic_sources_unchanged=before==after,
    old_test_sha256=sha(old),current_test_sha256=before_hash,old_test_declarations_identical=same_ast,
    old_test_bytes_after_removing_only_new_final_method_identical=same_raw,
    scope='One added synthetic fresh7 real SQLite/Projection/Earnings test: reviewed original-currency royalty append with exact13-unit allocation, current1/3 cohort rights4/9, actual History claim9, seeded/full all-time and day equality, old descriptor mutation rejection. No old15 rerun.',
    development_attempt={'runs':1,'errors':1,'cause':'Test invalid old symbol exceeded display-label length before reaching checkpoint identity','correction':'Use valid different OTHERETH symbol to test checkpoint identity itself'},
    log_sha256=sha((E/'append1.log').read_bytes()))
with (E/'APPEND1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:record[k] for k in ('status','tests_run','failures','errors','seconds','old_test_declarations_identical','old_test_bytes_after_removing_only_new_final_method_identical')}))
if record['status']!='PASS':print(stream.getvalue())
sys.exit(0 if record['status']=='PASS' else 1)
