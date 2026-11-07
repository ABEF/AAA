from pathlib import Path
import hashlib,json,re,subprocess
root=Path.cwd()
evidence=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/fee-flow-audit-20261107/keeper/capacity-20261107-013629-8744')
snapshot=evidence/'source-final'
snapshot.mkdir(exist_ok=False)
files=['keeper/monitor.py','keeper/royalties.py','tests_python/test_exact_lp_conversion_capacity.py']
pins={}
for name in files:
    data=(root/name).read_bytes();target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    pins[name]=hashlib.sha256(data).hexdigest()
expected={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4','scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b','tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9','tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
preserved={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in expected}
assert preserved==expected
union={}
for name in ('attempt6-final-affected.log','attempt7-final-pending-and-focused.log'):
    for test,status in re.findall(r'^test_\w+ \((tests_python\.[^)]+)\) \.\.\. (ok|skipped [^\n]*)',(evidence/name).read_text(encoding='utf-8-sig'),re.M):
        union[test]=status.strip()
summary={'baseline_head':'c055684a558519eab308a24b81746bf1b9842d96','owned_files':pins,'protected_files':preserved,
'corrected_stage_union':{'distinct_cases':len(union),'passed':sum(s=='ok' for s in union.values()),'skipped':{t:s for t,s in union.items() if s!='ok'},'not_sum_of_overlapping_runs':True},
'stages':[
{'log':'attempt1.log','result':'Python not on PATH; no tests executed'},
{'log':'attempt2.log','result':'14 tests:13 passes,1 fixture error because included-fee mock admission missing; actual fee guard correctly blocked'},
{'log':'attempt3-affected.log','result':'69 pass at initial capacity-only scope'},
{'log':'attempt4-negative-late-send.log','result':'2 intended regressions failed before late-stop fix: expired candidate and UTC-rollover budget both signed through mocked sender'},
{'log':'attempt5-final-focused.log','result':'20 pass before additional malformed-output and pending-config regressions'},
{'log':'attempt6-final-affected.log','result':'339 distinct cases;337 pass,2 environment skips; all substantive sizing/probe/late-stop/output checks, before new pending-count guard'},
{'log':'attempt7-final-pending-and-focused.log','result':'22 focused passes at final source pins'},
{'log':'baseline-negative.log','result':'Original c055 worker: exactly one32-ID estimate, cursor1,0 signer calls; affordable-subset regression fails as expected'}],
'limits':['Injected byte-level RPC and mocked signer; no target-chain gas/provider/production qualification','Bounded6 candidate preparations max; unknown source reads and transport/work/malformed faults are deferred, never diagnosed as zero or bad NFT','Opaque pre-send prefix probes only for sanitized RemoteRPCError on exact eth_call/eth_estimateGas step,code3/-32000,reason unclassified; no saved intent/signer invocation','After final head or durable I/O/inclusion, market/deadline/day/authority can still change; on-chain guards remain and no inclusion guarantee is claimed'],
'publication':'No staging,commit,push,environment,service,site,chain,signing or journal migration performed by keeper agent'}
(evidence/'final-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'corrected_stage_union':summary['corrected_stage_union'],'owned_files':pins},indent=2))
