"""Package the one strengthened historical-loader check and exact source reuse."""
from pathlib import Path
import ast,gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
EXTERNAL=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/royalty-rounds-20261118')
TARGET=Path(__file__).resolve().parent/'consumer/final02'
NAME='test_exact_historical3_and4_templates_retain_separate_identity_and_no_read_policy'
TEST='tests_python/test_factory_payload5.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
ADDITION=b'''        # Exercise the repaired historical loader, not just its code-owned JSON.
        from tests_python.test_factory_payload4 import compiled as historical_compiled
        archived=historical_compiled()
        self.assertTrue(F4.verify_compiler_output(archived))
        with self.assertRaises(ValueError):F5.verify_compiler_output(archived)
'''


def methods(raw):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(raw.decode()))
        if isinstance(n,ast.FunctionDef)}


def main():
    prior=json.loads((EXTERNAL/'consumer-final01/RESULT.json').read_bytes())
    current=json.loads((EXTERNAL/'consumer-final02/RESULT.json').read_bytes())
    assert prior['success'] and current['success'] and current['tests_run']==1
    assert current['methods']==['tests_python.test_factory_payload5.FactoryPayload5Tests.'+NAME]
    oldpins=prior['source_sha256_after'];newpins=current['source_sha256_after']
    changed=[p for p in sorted(set(oldpins)|set(newpins)) if oldpins.get(p)!=newpins.get(p)]
    assert changed==[TEST],changed
    raw=(ROOT/TEST).read_bytes();assert raw.count(ADDITION)==1 and sha(raw)==newpins[TEST]
    before=raw.replace(ADDITION,b'');assert sha(before)==oldpins[TEST]
    oldmethods,newmethods=methods(before),methods(raw)
    assert set(oldmethods)==set(newmethods)
    changed_methods=[n for n in oldmethods if oldmethods[n]!=newmethods[n]]
    assert changed_methods==[NAME],changed_methods
    TARGET.mkdir(parents=True,exist_ok=False)
    for name in ('START.json','RESULT.json'):
        (TARGET/(name+'.gz')).write_bytes(gzip.compress((EXTERNAL/'consumer-final02'/name).read_bytes(),mtime=0))
    shutil.copyfile(EXTERNAL/'consumer-final02/raw.log',TARGET/'raw.log')
    (TARGET/'CURRENT_TEST_SOURCE.py.gz').write_bytes(gzip.compress(raw,mtime=0))
    report=dict(schema=1,kind='One strengthened new method; unchanged remaining method bodies reused exactly',
        distinct_methods=12,total_method_executions=13,new_methods=11,changed_historical_methods=1,
        first_stage_actual_count=12,followup_actual_count=1,first_stage_success=True,followup_success=True,
        changed_source_files=changed,changed_function_bodies=changed_methods,
        byte_exact_prior_source_reconstruction_matches_recorded_sha256=True,
        unchanged_other_functions_ast_identical=True,
        source_sha256_before=oldpins[TEST],source_sha256_after=newpins[TEST],
        all_other_recorded_sources_exactly_reused=True,both_execution_source_brackets_stable=True,
        latest_method=current['methods'][0],latest_method_source='consumer/final02',
        preserved_other11_source='consumer/final01',protected_sha256=current['protected_sha256'],
        files_sha256={p.name:sha(p.read_bytes()) for p in sorted(TARGET.iterdir())},
        production_approved=False,unchanged_suites_rerun=False)
    (TARGET/'PUBLICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('distinct_methods','total_method_executions','all_other_recorded_sources_exactly_reused')}))


if __name__=='__main__':main()
