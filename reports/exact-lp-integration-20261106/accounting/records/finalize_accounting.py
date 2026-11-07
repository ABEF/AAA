from pathlib import Path
import json,hashlib,re,subprocess,gzip,io
r=Path.cwd();e=Path(__file__).parent;v=e.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
# Lexical body extraction ignoring braces in comments/quoted strings.
def erase_noncode(t):
    out=list(t);i=0
    while i<len(t):
        if t.startswith('//',i):
            j=t.find('\n',i);j=len(t)if j<0 else j
            out[i:j]=' '*(j-i);i=j
        elif t.startswith('/*',i):
            j=t.find('*/',i+2);assert j>=0;j+=2;out[i:j]=' '*(j-i);i=j
        elif t[i]in"'\"":
            q=t[i];j=i+1
            while j<len(t):
                if t[j]=='\\':j+=2
                elif t[j]==q:j+=1;break
                else:j+=1
            out[i:j]=' '*(j-i);i=j
        else:i+=1
    return ''.join(out)
def funcs(b):
    t=b.decode();c=erase_noncode(t);out={}
    for m in re.finditer(r'\bfunction\s+([A-Za-z0-9_]+)\s*\(',c):
        start=m.start();j=c.find('{',m.end());semi=c.find(';',m.end())
        if j<0 or 0<=semi<j:continue
        dep=1;k=j+1
        while dep:
            dep+=(c[k]=='{')-(c[k]=='}');k+=1
        key=m.group(1);idx=1
        while key in out:idx+=1;key=m.group(1)+'#'+str(idx)
        out[key]={'sha256':sha(t[start:k].encode()),'start':start,'end':k}
    return out
def compare_body(before,after):
    b0=before.read_bytes();b1=after.read_bytes();f0=funcs(b0);f1=funcs(b1)
    changes=[k for k in f0 if k not in f1 or f0[k]['sha256']!=f1[k]['sha256']]
    return {'before':str(before),'after':str(after),'before_sha256':sha(b0),'after_sha256':sha(b1),
      'changed_functions':changes,'added_functions':sorted(set(f1)-set(f0)),
      'old_function_sha256':{k:x['sha256']for k,x in f0.items()},
      'final_function_sha256':{k:x['sha256']for k,x in f1.items()},
      'all_non_test_functions_exact':all(k.startswith('test')or k in f1 and x['sha256']==f1[k]['sha256']for k,x in f0.items())}
def without_tests(p):
    t=p.read_bytes().decode();f=funcs(t.encode())
    for k,x in sorted(f.items(),key=lambda x:x[1]['start'],reverse=True):
        if k.startswith('test'):t=t[:x['start']]+'/* TEST METHOD OMITTED */'+t[x['end']:]
    return t.encode()
native_old=e/'evm-native-vault-controls/test-source.sol'
assert native_old.exists()
native=compare_body(native_old,r/'test/VaultAccounting.t.sol')
assert set(native['changed_functions'])=={'testOldDepositSelectorCannotBypassPaidMint','testUnsealedSystemCannotMint'}
assert not native['added_functions'] and native['all_non_test_functions_exact']
native['non_test_declarations_and_helpers_byte_identical']=without_tests(native_old)==without_tests(r/'test/VaultAccounting.t.sol')
assert native['non_test_declarations_and_helpers_byte_identical']
oldstatus=load(e/'evm-native-vault-controls/status.json');newstatus=load(e/'evm-priority-native-core/status.json')
assert sum(x['status']=='Success'for x in oldstatus['methods'].values())==33
assert newstatus['successful'] and len(newstatus['methods'])==4
native.update({'initial_stage':'evm-native-vault-controls','initial_successes_reused':33,'corrected_selected_successes':2,'final_distinct_methods':35,'corrected_stage':'evm-priority-native-core','reason':'Only two unrelated test bodies changed; inherited PooledVaultFixture/VaultLiquidityMock and all imports/setup/helpers remain exact.'})
write(e/'NATIVE35_FINAL_REUSE_PROOF.json',native)
host=compare_body(e/'evm-host-corrected-matched/test-source.sol',r/'test/ExactLPRewards.t.sol')
assert not host['changed_functions'];assert len(host['added_functions'])==2
host['all_original14_method_and_helper_bodies_exact']=True
host['final_distinct_methods']=16
host['additional_methods_stages']={'evm-router32':1,'evm-router8':1}
write(e/'HOST16_FINAL_REUSE_PROOF.json',host)
# Independently compare canonical frozen fixture bodies/declarations, not claim current raw file equality.
canver=load(r/'reports/exact-lp-integration-20261106/canonical/CANONICAL_VERIFICATION.json')
canproof=[]
for s in canver['final_stages']:
    stage=Path(s['path']);candidates=[p for p in stage.rglob('VaultAccounting.t.sol')]
    if candidates:
        for p in candidates:
            x=compare_body(p,r/'test/VaultAccounting.t.sol')
            x['non_test_declarations_and_helpers_byte_identical']=without_tests(p)==without_tests(r/'test/VaultAccounting.t.sol')
            assert x['non_test_declarations_and_helpers_byte_identical']
            canproof.append(x)
    else:
        # Compiler input retains literal source, enough to reconstruct original fixture bytes.
        start=load(stage/'START.json');target='test/VaultAccounting.t.sol'
        matched=[]
        for ip in (e.parent/'canonical-agent').rglob('input.json'):
            try:
                inp=load(ip);text=inp.get('sources',{}).get(target,{}).get('content')
                if text is not None:
                    raw=text.encode()
                    expected=start.get('closed_before',start.get('test_source_before',{})).get(target)
                    # Expected closure format may differ; use known frozen helper pin if present.
                    expected=expected or load(e/'SHARED_HELPERS_FREEZE.json')[target]
                    if sha(raw)==expected:matched.append((ip,raw))
            except (ValueError,KeyError):pass
        assert matched, ('No source snapshot for canonical closure',stage)
        ip,raw=matched[0];sp=e/('canonical-fixture-'+stage.name+'.sol');sp.write_bytes(raw)
        x=compare_body(sp,r/target)
        x['canonical_original_stage']=str(stage);x['original_input']=str(ip)
        x['non_test_declarations_and_helpers_byte_identical']=without_tests(sp)==without_tests(r/target)
        assert x['non_test_declarations_and_helpers_byte_identical']
        canproof.append(x)
write(e/'CANONICAL_IMPORTED_FIXTURE_REUSE_PROOF.json',{'scope':'No canonical tests rerun. Original34 frozen105 closures remain original-source passes. Later two unselected VaultAccounting test-only bodies do not change imported fixture declarations/helpers.','comparisons':canproof})
normal=v/'exact-lp-integration-20261106-64f9/normal-final-5994e91eed/START.json'
normalpins=load(normal)['source_sha256']
assert all(sha((r/p).read_bytes())==h for p,h in normalpins.items())
protected={
'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
assert all(sha((r/p).read_bytes())==h for p,h in protected.items())
# Inventory actual final test maintenance; this is not a full runtime-pass claim.
baseline=load(e/'BASELINE_TESTS.json')
diff=subprocess.run(['git','diff','--name-only','--','test'],capture_output=True,text=True,check=True).stdout.splitlines()
physical={'test/CanonicalHandoff.t.sol','test/NativeCanonicalIntegration.t.sol','test/NativeFeeRewards.t.sol','test/ZeroAssetCanonical.t.sol'}
own=[p for p in diff if p not in physical]+['test/ExactLPRewards.t.sol','test/ExactLPVaultWire.t.sol']
write(e/'OWNED_FINAL_FILES.json',{'source_hooks':['src/ZZZVault.sol','src/ZZZMembership.sol','src/interfaces/IZZZ.sol'],'test_maintenance_final':{p:sha((r/p).read_bytes())for p in sorted(set(own))},'other_agent_canonical_files_excluded':sorted(physical),'note':'Changed test files are compile-maintained, not all runtime executed; stage-selection manifests identify exact runtime scope.'})
statuses={}
for p in e.glob('evm-*/status.json'):
    s=load(p);ms=s.get('methods',{});statuses[p.parent.name]={'exit_code':s.get('exit_code'),'method_count':len(ms),'successes':sum(i.get('status')=='Success'for i in ms.values()),'failures':{k:i.get('reason')for k,i in ms.items()if i.get('status')!='Success'},'successful':s.get('successful'),'status_sha256':sha(p.read_bytes())}
review={
'schema':1,'baseline_git':'64f9bfb1b0db28c9c8eafc42394afad2263637b6',
'final_normal_source_basis':str(normal),'final_normal_sources':len(normalpins),'production_raw_pins_unchanged':True,
'production_sha256':normalpins,'protected_files_sha256':protected,'protected_files_unchanged':True,
'distinct_successful_methods_by_nonoverlapping_scope':{'exact_host':16,'actual_vault_producer':1,'native_vault_controls':35,'actual_v4_accounting':2},
'no_claim_of_complete_project_suite':True,'priority_stage_successful':True,'stage_statuses':statuses,
'raw_cold_execution_gas':{'single_native_claim':1259505,'two_book_growth':1213300,'router32_entries':31085813,'router8_entries':8819431,'unchanged_service_budget':12000000},
'gas_scope':'Harness/callee cold execution only; no intrinsic/calldata/refund/targetprovider qualification.32-entry count maximum DOES NOT fit12M in measured fixture;8fit is not universal chunk approval; planner must freshly simulate/replan.',
'fixture_scope':['Native-default synthetic test venue prices normalize1USD perwei ETH and per0decimalZZZ; not production oracle qualification.','Host suite uses actualNFT/Rewards/Membership/Fees/router but authenticated synthetic sharewriter/converter and MockAccess.','Real-Vault wire uses actualVault+shares/events, normalized correlated mockfeeds, synthetic venue; independent backend actual77log replay.','Selected actual-v4 controls use actualPoolManager/PositionManager/typedManager; testfeeds and authority seams remain; minLiquidity1 fixture not production recommendation.'],
'original_failures_and_retirements_preserved':['initial host compile stopped','host13 two fixture failures','empty selector0methods','real-Vault wrong historical harness InvalidAmount','native35 two fixture assertions','affected45 compilerOOM zeroEVM','two full-VaultWETH fork tests explicitly retired','three third-LP-asset cases explicitly retired'],
'unexecuted_scope':'45class affected selection was typechecked244sources but compilerOOM ranZEROEVM. Many compile-maintained legacy dependent cases remain unexecuted; final bounded54method scopes do not substitute for fullsuite/productionqualification.',
'host_reuse':'HOST14_REUSE_PROOF.json + HOST16_FINAL_REUSE_PROOF.json',
'native_reuse':'NATIVE35_FINAL_REUSE_PROOF.json',
'canonical_fixture_reuse':'CANONICAL_IMPORTED_FIXTURE_REUSE_PROOF.json',
'actual_wire':'Backend packaged actual77logs/four26field snapshots and independent consumer checks; original partial sharefixture producer rejection retained.',
'environments_changed':False,'services_or_chains_reset':False,'signing_changed':False,'foundry_config_changed':False,
'limitations':['No target-chain provider/gas/uptime/OpenSea/externalprice/VRFqualification.','No fullsuite/publicCI/independentapproval.','Canonical/V9 large import gas and target operating envelopes remain qualification obligations.']}
write(e/'FINAL_ACCOUNTING_REVIEW.json',review)
print(json.dumps({'native35':True,'host16':True,'canonical_fixture_reuse_comparisons':len(canproof),'production_sources':len(normalpins),'owned_files':len(set(own)),'stages':statuses},indent=2))

