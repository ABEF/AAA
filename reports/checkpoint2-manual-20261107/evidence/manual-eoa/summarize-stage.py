from pathlib import Path
import hashlib,json,re
root=Path.cwd();stage=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/checkpoint2-manual-20261107-bf2/manual/typed-bcd-20261107-025056-4529/governance-eoa-20261107')
sha=lambda b:hashlib.sha256(b).hexdigest()
owned=['zzz_ops/manual_lp_review.py','scripts/prepare-manual-lp.py','tests_python/test_manual_lp_review.py','docs/MANUAL_LP_PREPARATION.md']
snapshot=stage/'source-final';snapshot.mkdir(exist_ok=False);pins={}
for path in owned:
    raw=(root/path).read_bytes();target=snapshot/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);pins[path]=sha(raw)
    assert not any(line.rstrip(b' \t')!=line for line in raw.splitlines())
protected={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4','scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b','tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9','tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
actual={path:sha((root/path).read_bytes()) for path in protected};assert actual==protected
pattern=re.compile(r'^test_\w+ \((tests_python\.[^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$')
methods={}
for name in ('final29.log','final-cli-assertion.log'):
    for number,line in enumerate((stage/name).read_text(encoding='utf-8-sig').splitlines(),1):
        match=pattern.fullmatch(line)
        if match:methods.setdefault(match[1],[]).append({'log':name,'line':number,'outcome':match[2]})
assert len(methods)==29 and all(row['outcome']=='ok' for rows in methods.values() for row in rows)
summary={'schema':1,'stage':'direct_empty_code_governance_eoa_only','owned_files':pins,'protected_files':actual,
'final_results':{'distinct_methods':29,'passed':29,'skipped':0,'full_manual_log':'final29.log','additional_cli_assertions':'final-cli-assertion.log','not_summed_to_30':True},
'historical_stage':{'summary_relative_path':'../final-summary.json','summary_sha256':sha((stage.parent/'final-summary.json').read_bytes()),'scope':'Original89-method success source remains historical before this narrow client-wallet boundary. Files/logs/snapshots were not overwritten. Other61 existing methods were not rerun here; root owns exact unchanged-source reuse qualification.'},
'scope':['Direct empty-code governance EOA only; getCode strictly validated at each pinned snapshot. Nonempty contract or delegated code yields typed UnsupportedGovernanceEnvelope before network-funding review.','CLI maps only that local typed error to safe constant unsupported_contract_wallet_envelope. No arbitrary RPC message parsing or message echo.','Unsigned transaction still contains actual governance from, fixed Migration to, zero value, exact calldata and chainId; no outer contract-wallet envelope, gas payer guess, nonce, signing or gas fields.','Existing on-chain governance permissions and manual Explorer/Safe procedures unchanged. Direct EOA gas funding checks unchanged.'],
'publication':'No staging, commit, push or running changes by agent. Root must restage modified source/tests/guide against this stage before publication.',
'per_method_provenance':[{'id':method,'observations':rows} for method,rows in sorted(methods.items())]}
(stage/'final-stage-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'owned_files':pins,'final_results':summary['final_results'],'protected_preserved':True},indent=2))
