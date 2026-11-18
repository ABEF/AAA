"""Publish only four artifact-dependent C08 rechecks and exact unchanged-consumer proof."""
from pathlib import Path
import gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/royalty-rounds-20261118')
OUT=Path(__file__).resolve().parent/'consumer'
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    previous=json.loads((V/'consumer-final04/RESULT.json').read_bytes())
    final=json.loads((V/'consumer-final05/RESULT.json').read_bytes())
    assert final['success'] and final['tests_run']==4 and final['source_stable']
    assert set(final['methods'])<set(previous['methods'])
    assert final['protected_sha256']==previous['protected_sha256']
    reused=['zzz_ops/royalty_read_policy.py','zzz_ops/production_v15.py','zzz_ops/production_observer_v15.py',
        'zzz_ops/preseal_plan.py','tests_python/test_factory_payload5.py','tests_python/test_factory_payload4.py']
    assert all(previous['source_sha256_after'][p]==final['source_sha256_before'][p] for p in reused)
    archive=OUT/'c07-pins'
    oldhelper=gzip.decompress((archive/'00-factory_code_v5.py.gz').read_bytes())
    prior=json.loads(gzip.decompress((archive/'03-FINAL_PAYLOAD5.json.gz').read_bytes()))
    current=json.loads((ROOT/'reports/royalty-rounds-20261118/FINAL_PAYLOAD5.json').read_bytes())
    newhelper=(ROOT/'zzz_ops/factory_code_v5.py').read_bytes()
    assert oldhelper.replace(prior['canonical_manifest_sha256'].encode(),current['canonical_manifest_sha256'].encode())==newhelper
    oldtemplate=json.loads(gzip.decompress((archive/'02-production.example.json.gz').read_bytes()))
    template=json.loads((ROOT/'config/production.example.json').read_bytes())
    for value in (oldtemplate,template):
        chain=value['chains'][0]
        del chain['factory_code']
        for key in ('royaltyCodeHash','creationCodeLength','part0CodeHash','part1CodeHash'):
            del chain['helpers']['royalty_factory']['bindings'][key]
    assert oldtemplate==template
    target=OUT/'final05';target.mkdir(exist_ok=False)
    for name in ('START.json','RESULT.json'):(target/(name+'.gz')).write_bytes(gzip.compress((V/'consumer-final05'/name).read_bytes(),mtime=0))
    shutil.copyfile(V/'consumer-final05/raw.log',target/'raw.log')
    current_files=['zzz_ops/factory_code_v5.py','config/factory-code-storage-v5.json','config/production.example.json',
        'reports/royalty-rounds-20261118/FINAL_PAYLOAD5.json','reports/royalty-rounds-20261118/refresh_payload5.py',
        'reports/royalty-rounds-20261118/run_consumer_checks.py']
    files=[]
    for i,path in enumerate(current_files):
        raw=(ROOT/path).read_bytes();name=f'{i:02d}-'+Path(path).name+'.gz';(target/name).write_bytes(gzip.compress(raw,mtime=0));files.append(dict(source=path,archive=name,sha256=sha(raw)))
    (target/'SOURCE_INDEX.json').write_text(json.dumps(files,indent=2)+'\n')
    report=dict(schema=1,kind='Final C08 exact factory pins and four affected methods; remaining eight controls not rerun',
        distinct_consumer_methods=12,actual_final05_passes=4,selected_methods=final['methods'],
        stages={'first_source':'final01/final02','C07_admission_error':'final03','C07_affected_passes':'final04','C08_artifact_passes':'final05'},
        previous_c07_methods_not_rerun=[p for p in previous['methods'] if p not in final['methods']],
        other_unchanged_prior_controls=5,unaffected_consumer_and_test_sources_exactly_unchanged={p:final['source_sha256_before'][p] for p in reused},
        factory_helper_byte_identical_after_only_manifest_pin_replacement=True,
        production_template_unchanged_except_actual_factory_code_parts_and_four_factory_binding_pins=True,
        c07_pin_archive='consumer/c07-pins',first_source_archive='consumer/first-source-pins',
        accepted_payload=current,source_stable=True,protected_sha256=final['protected_sha256'],
        no_unchanged_tests_compiler_evm_or_network=True,production_approved=False)
    (OUT/'C08_RECHECK.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(actual_final_passes=4,distinct_methods=12,unaffected_controls_reused=8)))

if __name__=='__main__':main()
