from pathlib import Path
import datetime,hashlib,importlib.util,json,sys
E=Path(__file__).resolve().parent;R=Path.cwd();sys.path.insert(0,str(R))
def read(name):return json.loads((E/(name+'.json')).read_text())
stages={name:read(name) for name in ('keeper-existing-first','keeper-fixtures-recheck',
    'simulation-negative-corrected-fixture','final-submit-consumers',
    'confirmation-affected-baseline','confirmation-fixture-final','inventory-final')}
final={}
for name in ('final-submit-consumers','confirmation-affected-baseline','confirmation-fixture-final','inventory-final'):
    record=stages[name]
    assert not record['source_changes_during_run']
    rejected={row[0] for key in ('failures','errors','skips') for row in record[key]}
    for identifier in record['executed_methods']:
        if identifier not in rejected:final[identifier]=name
spec=importlib.util.spec_from_file_location('keeper_summary_runner',R/'scripts/run-keeper-tests.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
inventory,_=runner.select_tests()
assert set(final)<=set(inventory)
skips={row[0]:row[1] for name in ('final-submit-consumers','confirmation-affected-baseline','inventory-final')
       for row in stages[name]['skips']}
assert len(final)==370 and len(skips)==2
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'keeper_monitor_sha256':hashlib.sha256((R/'keeper/monitor.py').read_bytes()).hexdigest(),
 'new_simulation_test_sha256':hashlib.sha256((R/'tests_python/test_keeper_simulation_outputs.py').read_bytes()).hexdigest(),
 'runner_inventory_methods':len(inventory),'final_monitor_affected_methods_passed':len(final),
 'final_monitor_affected_methods_skipped':skips,'final_method_evidence':dict(sorted(final.items())),
 'before_stage':{'selected':stages['keeper-existing-first']['tests_run'],
   'failures':len(stages['keeper-existing-first']['failures']),
   'errors':len(stages['keeper-existing-first']['errors']),
   'skips':len(stages['keeper-existing-first']['skips'])},
 'negative_simulation_stage':{'methods':stages['simulation-negative-corrected-fixture']['tests_run'],
   'failing_subcases':len(stages['simulation-negative-corrected-fixture']['failures']),
   'errors':len(stages['simulation-negative-corrected-fixture']['errors'])},
 'source_changed_stage':'inventory-previously-omitted ran69 with0failures/errors but keeper/monitor.py changed; not a final pass; repeated as inventory-final69/stable.',
 'scope':'Defined-class offline/unit/injected-RPC fixtures only. No installed service, public transaction, operating acceptance or all927 final-source rerun claim. Five late-job and three strict-output methods overlap root stages and must not be summed twice.',
 'fixture_maintenance':'Only new transport submissions get future deadlines; historical pending/receipt calldata unchanged. Two incident signer fixtures now return canonical bool for observe; reset stays void.',
 'runner_coverage_fix':'Four existing keeper regression modules were absent and are now explicitly selected, alongside two new modules; no broad discovery or duplicate imported classes.'}
with (E/'final-summary.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({key:record[key] for key in ('keeper_monitor_sha256','runner_inventory_methods','final_monitor_affected_methods_passed','final_monitor_affected_methods_skipped')}))
