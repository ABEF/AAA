from pathlib import Path
import hashlib,json,re,subprocess
root=Path.cwd();evidence=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/checkpoint2-manual-20261107-bf2/manual/typed-bcd-20261107-025056-4529')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
owned=['zzz_ops/manual_lp_review.py','scripts/prepare-manual-lp.py','tests_python/test_manual_lp_review.py','docs/MANUAL_LP_PREPARATION.md']
snapshot=evidence/'source-final';snapshot.mkdir(exist_ok=False)
pins={}
for name in owned:
    data=(root/name).read_bytes();target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);pins[name]=sha(data)
    assert not any(line.rstrip(b' \t')!=line for line in data.splitlines()),'Trailing whitespace: '+name
protected={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4','scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b','tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9','tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
proof={name:sha((root/name).read_bytes()) for name in protected};assert proof==protected
pattern=re.compile(r'^test_\w+ \((tests_python\.[^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$')
observed={}
for log in ('attempt1-initial.log','attempt2-moving-market.log','attempt3-current.log','attempt4-final-affected.log'):
    for line_no,line in enumerate((evidence/log).read_text(encoding='utf-8-sig').splitlines(),1):
        match=pattern.fullmatch(line)
        if match:
            method,outcome=match.groups();observed.setdefault(method,[]).append({'log':log,'line':line_no,'outcome':outcome})
final={method:[row for row in rows if row['log']=='attempt4-final-affected.log'][0] for method,rows in observed.items() if any(row['log']=='attempt4-final-affected.log' for row in rows)}
assert len(final)==89 and all(row['outcome']=='ok' for row in final.values())
new=[method for method in final if method.startswith('tests_python.test_manual_lp_review.')];assert len(new)==28
provenance={'schema':1,'counting_rule':'Only final affected log supplies success counts; prior attempts and deliberately mutated negative controls add zero passes. Fully qualified test IDs are unique.','distinct_final_methods':89,'new_manual_methods':28,'passed':89,'skipped':0,'methods':[{'id':method,'selected_evidence':final[method],'observations':observed[method]} for method in sorted(final)]}
(evidence/'per-method-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
base='bf2cc72adbed74e12e64b6b987cdd669eb30ce90'
listing=subprocess.check_output(['git','ls-tree',base,'--',*owned])
assert listing==b''
summary={'schema':1,'baseline_head':base,'source_scope':'Only four new files; no edits to shared existing files. All owned source bytes frozen for final affected run.','owned_files':pins,'baseline_paths_absent':True,'baseline_git_ls_tree_output_sha256':sha(listing),'protected_files':proof,'verification':{'final_log':'attempt4-final-affected.log','distinct_methods':89,'passed':89,'skipped':0,'new_manual_methods':28,'not_sum_of_overlapping_runs':True,'final_wall_seconds':191.431},'attempts':[{'log':'attempt1-initial.log','result':'19 methods;18 pass,1 final-head/reorg assertion failed. Initial source before moving-market/final-head revision; retained as failure, not counted as final evidence.'},{'log':'attempt2-moving-market.log','result':'24 methods pass at corrected moving-market/two-simulation/headroom scope, before final chain/labels/publication/D-lower-bound polish; not added to final counts.'},{'log':'attempt3-current.log','result':'27 methods pass before final D-preharvest-lower-bound and CLI/public pins polish; not added to final counts.'},{'log':'attempt4-final-affected.log','result':'89 distinct methods pass, including28 new manual methods, at the final owned source pins.'},{'log':'causal-negative-controls.log','result':'Intentional ephemeral monkeypatches only, source unchanged: disabled final control comparison causes5 assertion failures; reinstated false D preharvest ceiling causes1 expected error. expected_red=true. Not counted as passes.'}],'boundaries':{'read_only':True,'signing':False,'broadcasting':False,'arbitrary_call_targets':False,'nonce_or_journal_work':False,'running_config_changes':False,'service_site_chain_changes':False,'actual_target_gas_or_provider_qualification':False,'source_runtime_build_provenance_approved':False,'operator_wallet_rehearsal_performed':False,'supported_actions':'Explicit Active-state B/C/D only; Parked emergency unsupported.'},'methodological_limits':['Initial confirmation-depth snapshot plus separately labeled later canonical-tip control snapshot; latter is not claimed confirmed.','Exactly two full void simulations and estimates at pinned hashes, original calldata/floors/deadline/reviewHash unchanged; last head/deadline check, no loop or inclusion guarantee.','Healthy composition/price rounds may move, but custody/L/shares/nonces/config/policy identities remain committed. Forced0 skips price/policy/operations-readiness/automatic-route dependencies.','D captured availability excludes future harvest and is informative lower bound; unchanged complete source-call simulations decide spendability. B/C cannot spend main or designated compound.','Tests use real Projection/physical/Catalog implementations with injected RPC. No actual chain gas execution, independent source-build/runtime approval or provider-honesty proof.']}
(evidence/'final-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'owned_files':pins,'final_verification':summary['verification'],'protected_preserved':proof==protected},indent=2))
