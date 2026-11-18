"""Preserve failed admission stage and publish seven affected final-pin rechecks."""
from pathlib import Path
import ast,gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/royalty-rounds-20261118')
OUT=Path(__file__).resolve().parent/'consumer'
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    prior=json.loads((V/'consumer-final02/RESULT.json').read_bytes())
    failed=json.loads((V/'consumer-final03/RESULT.json').read_bytes())
    final=json.loads((V/'consumer-final04/RESULT.json').read_bytes())
    assert failed['tests_run']==7 and len(failed['errors'])==4 and not failed['failures'] and failed['source_stable']
    assert all('source_closure' in row['error'] for row in failed['errors'])
    assert final['tests_run']==7 and final['success'] and final['source_stable']
    assert final['methods']==failed['methods'] and final['protected_sha256']==prior['protected_sha256']
    old_test=gzip.decompress((OUT/'final02/CURRENT_TEST_SOURCE.py.gz').read_bytes())
    test=(ROOT/'tests_python/test_factory_payload5.py').read_bytes()
    assert old_test==test
    untouched=['test_exact_historical3_and4_templates_retain_separate_identity_and_no_read_policy',
        'test_computed_fingerprint_has_explicit_scope_bounds_revision_and_independent_encoding',
        'test_failed_or_out_of_bounds_cap_clears_stale_observation_and_never_adopts_declared_cap',
        'test_unknown_optional_cap_blocks_calldata_and_bounds_fail_before_artifact_reads',
        'test_bool_unknown_and_mixed_payloads_reject_before_any_observer_read']
    # Reused failure branches and historical selectors are code-identical; F5 byte
    # admission and the real part reader are checked again on the final actual bytes.
    reused_sources=['zzz_ops/royalty_read_policy.py','zzz_ops/production_v15.py',
        'zzz_ops/production_observer_v15.py','zzz_ops/preseal_plan.py',
        'tests_python/test_factory_payload5.py','tests_python/test_factory_payload4.py']
    assert all(prior['source_sha256_after'][p]==final['source_sha256_before'][p] for p in reused_sources)
    for stage in ('03','04'):
        directory=OUT/('final'+stage);directory.mkdir(exist_ok=False)
        external=V/('consumer-final'+stage)
        for name in ('START.json','RESULT.json'):(directory/(name+'.gz')).write_bytes(gzip.compress((external/name).read_bytes(),mtime=0))
        shutil.copyfile(external/'raw.log',directory/'raw.log')
        if (external/'RUNNER_SOURCE.py.gz').exists():shutil.copyfile(external/'RUNNER_SOURCE.py.gz',directory/'RUNNER_SOURCE.py.gz')
    selected=final['methods']
    sources={p:final['source_sha256_after'][p] for p in reused_sources}
    snapshot=OUT/'final04'/'source';snapshot.mkdir()
    owned=['zzz_ops/factory_code_v5.py','config/factory-code-storage-v5.json','config/production.example.json',
        'reports/royalty-rounds-20261118/refresh_payload5.py','reports/royalty-rounds-20261118/run_consumer_checks.py',
        'reports/royalty-rounds-20261118/FINAL_PAYLOAD5.json']+reused_sources
    archived=[]
    for i,name in enumerate(owned):
        raw=(ROOT/name).read_bytes();file=f'{i:02d}-'+Path(name).name+'.gz';(snapshot/file).write_bytes(gzip.compress(raw,mtime=0))
        archived.append(dict(source=name,archive=file,sha256=sha(raw)))
    (snapshot/'INDEX.json').write_text(json.dumps(archived,indent=2)+'\n')
    record=dict(schema=1,kind='Final fresh payload5 pins; seven affected methods rechecked, five unchanged controls retained at explicit prior scope',
        distinct_methods=12,new_methods=11,changed_historical_methods=1,
        executions_by_stage={'final01':12,'final02':1,'final03':7,'final04':7},
        final04_actual_passes=7,failed_final03=dict(passes=3,errors=4,cause='Final registry selected the61-source root map instead of existing100-source compiler-content map; strict closure rejected before pin publication',
            corrected_by='Registry-only new final profile source_key=compiler_content_sha256; old stage records unchanged'),
        current_selected=selected,unchanged_controls_reused=untouched,
        same_test_source_bytes_as_final02=True,exact_reused_source_sha256=sources,
        final_source_stable=True,protected_sha256=final['protected_sha256'],
        accepted_payload=json.loads((ROOT/'reports/royalty-rounds-20261118/FINAL_PAYLOAD5.json').read_bytes()),
        historical_initial_pin_archive='consumer/first-source-pins',
        no_unchanged_suite_rerun=True,no_compiler_evm_or_network_execution=True,production_approved=False)
    (OUT/'FINAL_RECHECK.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(actual_final_passes=7,distinct_methods=12,initial_error_stage_preserved=True)))

if __name__=='__main__':main()
