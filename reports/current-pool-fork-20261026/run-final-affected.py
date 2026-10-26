"""One actual unfillable-growth and atomic-rollback case only; not a complete-suite approval runner.

Eight unchanged passed methods retain attempt2 source scope; the swaps-only method passed attempt4. The maintained
scripts/run-current-pool-fork.py still requires every current method and rejects
partial/skipped results. This native-host evidence driver never sends a public
transaction or contacts an existing local test service.
"""
from pathlib import Path
import importlib.util,json,os,threading,time
from datetime import datetime,timezone

R=Path(__file__).resolve().parents[2]
E=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OUT=E/'current-pool-fork-20261026/attempt6-growth-rollback'
spec=importlib.util.spec_from_file_location('current_fork',R/'scripts/run-current-pool-fork.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SELECTED={'testCurrentVaultUnfillableGrowthRevertsFundsAndAccounting'}
before=m.source_pins();OUT.mkdir(parents=True,exist_ok=False)

relay=m.Relay('https://robinhood.rpc.pinax.network');server=m.RelayServer(relay)
env=dict(os.environ)
for key in list(env):
    if any(v in key.upper() for v in ('PRIVATE_KEY','MNEMONIC','RPC_URL','RPC_HEADERS','JWT_SECRET')):env.pop(key,None)
env.update(RUN_CURRENT_POOL_FORK='true',ROBINHOOD_RPC_URL=server.url)
forge=E/'foundry-v1.4.4/forge.exe';solc=E/'toolchain-0.8.26/solc.exe'
assert m.FORGE_COMMIT in m.run_process_tree([str(forge),'--version'],timeout=30).stdout
assert '0.8.26+commit.8a97fa7a' in m.run_process_tree([str(solc),'--version'],timeout=30).stdout
command=[str(forge),'test','--root',str(R),'--use',str(solc),
    '--match-path','test/CurrentNativePoolFork.t.sol','--match-contract','^CurrentNativePoolForkTest$',
    '--match-test','^('+'|'.join(sorted(SELECTED))+')','--threads','1','--no-storage-caching','--json','-vvv',
    '--out',str(OUT/'out'),'--cache-path',str(OUT/'cache')]
start=time.monotonic();stop=threading.Event()
def progress():
    while not stop.wait(30):print(json.dumps({'affected_fork_seconds':int(time.monotonic()-start),'archive_attempts':relay.archive_attempts}),flush=True)
thread=threading.Thread(target=progress,daemon=True);server.start();thread.start()
report={'campaign_review_date':'2026-10-26','observed_start_utc':datetime.now(timezone.utc).isoformat(),'suite':m.SUITE,'selected_methods':sorted(SELECTED),
    'whole_current_suite_run':False,'chain_id':4663,'block':96427989,
    'block_hash':'0x0ba14c22200dfc717bbd2c8b5b8842329775374d06f46e30c65e273f067ecbc3',
    'public_transactions':False,'source_sha256_before':before,'successful':False}
try:
    process=m.run_process_tree(command,env=env,timeout=1500)
    (OUT/'forge-results.json').write_text(process.stdout,encoding='utf-8')
    (OUT/'forge-stderr.log').write_text(process.stderr,encoding='utf-8')
    report['process_exit_code']=process.returncode
    if process.returncode==0:
        j=json.loads(process.stdout);assert set(j)=={m.SUITE}
        tests=j[m.SUITE]['test_results'];assert set(tests)=={n+'()' for n in SELECTED}
        assert all(t['status']=='Success' for t in tests.values())
        report['passed_tests']=len(tests);report['successful']=True
finally:
    stop.set();server.close();thread.join(timeout=5)
    report.update(elapsed_seconds=round(time.monotonic()-start,3),archive_attempts=relay.archive_attempts,observed_end_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256_after=m.source_pins())
    report['source_inputs_unchanged']=report['source_sha256_after']==before
    if not report['source_inputs_unchanged']:report['successful']=False
    (OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('successful','whole_current_suite_run','elapsed_seconds','archive_attempts','source_inputs_unchanged')}))
raise SystemExit(0 if report['successful'] else 1)
