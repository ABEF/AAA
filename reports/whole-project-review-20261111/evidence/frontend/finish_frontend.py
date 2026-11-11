from pathlib import Path
import hashlib,json,subprocess
W=Path('C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website');E=Path(__file__).resolve().parent
p=W/'AGENTS.md';old=p.read_bytes();target=E/'before-demo-alignment/AGENTS.md';assert not target.exists();target.write_bytes(old)
s=old.decode();s=s.replace('Reviewed 2026-11-09.','Reviewed 2026-11-11.',1)
needle='remain unqualified. Existing example source copy still requires alignment.'
assert needle in s
s=s.replace(needle,'remain unqualified. Current demo writes now use explicit demo_policy2, ETH/ZZZ\n  and one native pair; historical v7 replay/local runtimes remain separate.')
p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n' if b'\r\n' in old else '\n').encode())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((E/'START.json').read_text())
unchanged={n:sha(W/n)==base['original'][n] for n in ['browser-wallet.js','deployment-config.js','integration-config.js']}
assert all(unchanged.values())
changed=subprocess.check_output(['git','-c','safe.directory='+str(W),'-C',str(W),'diff','--name-only'],text=True).splitlines()
expected=['AGENTS.md','FRONTEND_STATE.md','PROJECT_CONTEXT.md','README.md','app.js','build.mjs','domain.js','index.html','package.json','preview-store.js','server.mjs','styles.css','tests/contribution-flow.test.mjs']
assert sorted(changed)==sorted(expected),changed
new=['tests/deployment-bundle.test.mjs','tests/current-demo-policy.test.mjs']
check=subprocess.run(['git','-c','safe.directory='+str(W),'-c','core.whitespace=cr-at-eol','-C',str(W),'diff','--check'],capture_output=True,text=True)
assert check.returncode==0,check.stdout+check.stderr
record={'website_head':base['head'],'working_branch':subprocess.check_output(['git','-c','safe.directory='+str(W),'-C',str(W),'branch','--show-current'],text=True).strip(),
 'changed_files':changed,'new_files':new,'sha256':{n:sha(W/n) for n in changed+new},
 'preserved_sha256':{n:sha(W/n) for n in unchanged},'preserved':unchanged,
 'bundle_methods_passed':2,'demo_adjacent_methods_passed':86,'new_methods_in_demo_scope':6,'bundle_new_methods':2,
 'syntax_only_checks':8,'no_overlapping_stage_counts_added':True,
 'new_demo_policy':'explicit demo_policy:2; ETH/ZZZ; one ZZZ/ETH pool;3percent illustrative limit',
 'legacy_seed_sha256':'52ead56bd450875c0195d341c66b3c35065afd109199e985fe7868f65509c96a',
 'legacy_replay_sha256':'217d865c092f742578e1e1301dec66ed56bba7cbf4023336ab1c56060a010cb4',
 'current_demo_negative_before_fix_tool_observed':{'methods':6,'passed':1,'failed':5,'producer_log_not_saved':True},
 'compiled_or_deployed':False,'existing_dist_journal_anvil_service_state_changed':False,'public_configs_null':True,
 'full_website_suite_rerun':False,'browser_or_market_acceptance':False,'whitespace_check_pass':True,'committed_or_pushed':False}
with (E/'VERIFICATION.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'changed_tracked':len(changed),'new':len(new),'preserved':unchanged,'branch':record['working_branch'],'methods':{'bundle':2,'demo_including_new':86},'no_rollout':True}))
