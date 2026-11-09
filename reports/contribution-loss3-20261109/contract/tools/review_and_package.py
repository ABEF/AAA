from pathlib import Path
import collections,gzip,hashlib,importlib.util,json,re,shutil,sys
R=Path.cwd();E=Path(__file__).resolve().parent;D=R/'reports/contribution-loss3-20261109'
sys.path.insert(0,str(R))
spec=importlib.util.spec_from_file_location('review',R/'scripts/check-slither-review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fresh=json.loads((E/'static-current-contexts.json').read_text(encoding='utf-8'))
reuse=json.loads((E/'static-exact-reuse.json').read_text(encoding='utf-8'))
prior=json.loads((R/'reports/opensea-integration-20261109/static-review.json').read_text(encoding='utf-8'))
reviewed=[]
for row in fresh:
    desc=row['description'];check=row['check']
    if check=='reentrancy-eth' and desc.startswith('Reentrancy in ZZZLPPositionExecutor.collect('):
        disposition='false_positive'
        rationale='Individually reviewed both-leg collect context. Executor.collect is sealed fixed-Manager-only and nonReentrant; Manager.collect is fixed-Vault-only and nonReentrant. The fixed core/periphery pays only the typed executor, whose receive accepts only the armed core. _finishNativeCredit clears nativeSender and nativeReceived before forwarding ETH to the fixed Vault, with exact balance checks. The second leg deliberately rearms its own receipt counter; it is not an externally selected recipient or reusable payout balance. Token forwarding uses exact deltas. The approved constructor contribution default does not change this runtime/callback code. Actual upstream code and token behavior remain separately qualified dependencies.'
    elif check=='reentrancy-eth' and desc.startswith('Reentrancy in ZZZLPPositionExecutor.close('):
        disposition='false_positive'
        rationale='Individually reviewed both-leg close context. Only the sealed immutable Manager can enter the nonReentrant executor; Manager.close accepts only the fixed Vault under its own guard. Every physical NFT is checked Vault-owned and bound to the exact PoolKey. Core native credit is armed per leg, then disarmed and zeroed before ETH goes only to the fixed Vault with exact balance proof. Secondary associations are deleted only after the actual second burn succeeds, so a failed burn/transfer reverts the complete operation instead of abandoning backing. Read-only portfolio getters do not grant a write/custody capability. The approved contribution-default initializer changes neither this logic nor recipients; compromised upstream behavior remains an explicit dependency limit.'
    elif check=='uninitialized-local' and 'ZZZMigrationBudget._beforeMove' in desc:
        disposition='false_positive'
        rationale='Individually rechecked the zero-initialized Snapshot memory value and every later assignment. _beforeMove sets bucket/source pool, maintenanceLossBps, confirmation controls and captured price/value/scale/idle/policy fields before persistence; nonzero starting value is required. Ordinary replacement assigns portfolio revision/replacement; emergency deliberately retains replacement=false to forbid hybrid creation. Its cap remains the separate300bps maintenance policy. Changing the fresh contributionLossBps initializer from200 to300 does not leave any Snapshot field uninitialized or relax emergency/custody checks.'
    elif check=='unused-return' and 'ZZZMigrationBudget.validateUnwind' in desc:
        disposition='false_positive'
        rationale='Individually rechecked that validateExitPrice is invoked for its reverting spot/reference validity guard, not its return value. validateUnwind is fixed-Vault-only; only an already authenticated emergency context with explicit bit2 bypass may omit this check. Raw closure and captured principal accounting remain elsewhere. Contribution default300bps is separate from this unwinding check and the unchanged maintenance300bps policy; dropping the unused returned price does not skip price validation.'
    elif check=='unused-return' and 'ZZZMigrationBudget.validateReservation' in desc:
        disposition='false_positive'
        rationale='Individually rechecked that Registry.get is required to succeed before reading the permanent poolBucket alias. Its config return is intentionally unused because this function validates nonzero reservation inputs and collision-free bucket ownership rather than pricing/executing a swap. The sealed fixed Vault is the only caller. The authorized fresh contribution300bps default changes no registry admission, reservation, recipient or custody behavior.'
    elif check=='events-maths' and 'ZZZMigrationBudget.beginEmergency' in desc:
        disposition='false_positive'
        rationale='Individually rechecked that beginEmergency accepts only fixed Migration, rejects an existing emergency/snapshot and captures current governance before validating sealed, globally paused, canonical/current and nonterminal lifecycle. Emergency bucket/check bits are transaction-scoped context cleared by endEmergency after the guarded operation. Outer Migration completion events carry exact calldata/review provenance; this is not a persistent unlogged policy update. ContributionLossLimitChanged remains emitted by the unchanged governed setter; the fresh300bps constructor default is a separately documented deployment term.'
    elif check=='missing-inheritance' and desc.startswith('ZZZVaultCanonical '):
        disposition='informational'
        rationale='Individually rechecked the Budget-facing validation interface against VaultCanonical selectors and its fixed Budget caller authentication. These typed validations do not expose arbitrary storage or asset transfer. Explicit IBudgetVaultValidation inheritance adds no authority guarantee; actual controller/module/runtime binding remains required. Constructor contribution300bps is captured through the unchanged Budget/Pricing flow, not an alternate caller or interface layout.'
    elif check=='missing-inheritance' and 'IPortfolioBudget ' in desc:
        disposition='informational'
        rationale='Individually rechecked maintenanceBucket and maintenancePrices against Manager IPortfolioBudget. The Budget exposes only the captured ordinary replacement basis, while emergency and same-main paths retain their distinct context. Explicit inheritance would not authorize hybrid minting or validate a controller/module binding. The source default change affects only future contribution loss policy; portfolio and maintenance interfaces/storage/guards remain exact unchanged.'
    elif check=='missing-inheritance' and desc.startswith('ZZZMigration '):
        disposition='informational'
        rationale='Individually rechecked Migration IEmergencyManifest fingerprint/target selectors and exact fixed-Budget authentication for its fingerprint. The active request remains scoped to the paused governance operation; no generic caller obtains emergency manifest authority by structural interface matching. The fresh contribution300bps initializer changes no manifest selector, request layout, checks mask or automatic emergency policy.'
    elif check=='missing-inheritance' and 'IBudgetVaultValidation ' in desc:
        disposition='informational'
        rationale='Individually rechecked that IBudgetVaultValidation describes VaultCanonical, not a mandatory Budget base. Budget validateContribution intentionally returns captured uint32 packed venue/contribution limits, whereas the companion validation returns uint16 venue policy. Adding inheritance from a structural selector overlap would obscure that distinction. The authorized300bps initial cap is frozen into the existing high16bits before callbacks; ABI/storage and max1000bps governance ceiling remain unchanged.'
    elif check=='missing-inheritance' and 'IHistoricalCompound ' in desc:
        disposition='informational'
        rationale='Individually rechecked immutable metadata renderer IHistoricalCompound against Budget historicalCompoundValue. The exact read-only selector delegates to fixed ContributionPricing historicalValue; explicit inheritance adds no deployment/runtime or permission validation. The new contribution300bps initializer changes future contribution execution economics only, not historical compounding value, royalty accounting or current-owner rights.'
    else:raise ValueError('unreviewed current context '+desc)
    entry={k:v for k,v in row.items() if k not in ('prior','referenced_paths')}
    entry.update(disposition=disposition,rationale=rationale,review_scope='Individually reassessed exact current detector context and composition after the authorized constructor contribution200-to300bps default change; not independent approval.')
    if row['prior']:
        entry.update(prior_review='reports/opensea-integration-20261109/static-review.json',prior_fingerprint=row['prior']['fingerprint'])
    else:
        root=desc.splitlines()[0]
        entry['prior_related_contexts']=[x['fingerprint'] for x in prior['findings'] if x['check']==check and x.get('description','').splitlines()[0]==root]
        entry['presentation_difference_scope']='New actual reentrancy-eth fingerprint individually reviewed; no comparison/parser normalization expanded.'
    assert m.fingerprint(entry)==entry['fingerprint']
    reviewed.append(entry)
entries=list(reviewed)
for row in reuse:
    for path in row['referenced_paths']:
        assert m.source_hash(R/path)==prior['source_sha256_lf'][path]
    entry=dict(row['prior']);entry.update(prior_review='reports/opensea-integration-20261109/static-review.json',prior_fingerprint=row['fingerprint'],review_scope='Unique exact prior fingerprint and every description-referenced source LF-byte-identical; prior transitive/dependency limits retained. No inference from finding age or topic.')
    assert m.fingerprint(entry)==entry['fingerprint']
    entries.append(entry)
assert len(entries)==len({x['fingerprint']for x in entries})==558
assert len(reviewed)==11 and len(reuse)==547
entries.sort(key=lambda x:(x['check'],x['fingerprint']))
paths=sorted([p.relative_to(R).as_posix()for p in (R/'src').rglob('*.sol')]+['foundry.toml','package-lock.json','slither.config.json'])
review={'analyzer':'Slither0.11.6/crytic-compile0.4.2','date':'2026-11-09','independent_audit':False,'reviewer':'Internal11 current contexts (9 changed-Budget references and2 actual reordered reentrancy-eth descriptions),547 unique exact referenced-source reuse; not independent approval.','source_sha256_lf':{p:m.source_hash(R/p)for p in paths},'normal_build':'normal-final-a864bb33d5','actual_analyzer':'static-417c118f1d','current_contexts':11,'unique_unchanged_referenced_source_reuse':547,'findings':entries}
raw=json.loads((E/'static-417c118f1d/detectors-only.json').read_text(encoding='utf-8'))
errors=m.check(raw,review,R);assert not errors,errors
D.mkdir(parents=True,exist_ok=True)
with (D/'static-review.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(review,f,indent=2);f.write('\n')
N=D/'contract'/'normal-final-a864bb33d5';N.mkdir(parents=True,exist_ok=False)
for name in ['START.json','compiler-input.json','production-size-gates.json','solc-stderr.txt']:shutil.copyfile(E/'normal-final-a864bb33d5'/name,N/name)
normal_out=(E/'normal-final-a864bb33d5/compiler-output.json').read_bytes();(N/'compiler-output.json.gz').write_bytes(gzip.compress(normal_out,mtime=0));assert gzip.decompress((N/'compiler-output.json.gz').read_bytes())==normal_out
for name in ['CONSTRUCTOR_DEFAULT_EQUIVALENCE.json']:shutil.copyfile(E/name,D/'contract'/name)
S=D/'static';S.mkdir(exist_ok=False)
for name in ['START.json','EXECUTION.json','slither.log']:shutil.copyfile(E/'static-417c118f1d'/name,S/name)
for name in ['slither.json','detectors-only.json']:
    content=(E/'static-417c118f1d'/name).read_bytes();(S/(name+'.gz')).write_bytes(gzip.compress(content,mtime=0));assert gzip.decompress((S/(name+'.gz')).read_bytes())==content
for name,obj in [('static-current-reviewed.json',reviewed),('static-exact-reuse.json',reuse),('review-coverage.json',{'review_coverage_pass':True,'findings':558,'current_contexts':11,'unique_exact_reused':547,'errors':errors,'independent_audit':False})]:
    with (S/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
T=D/'contract'/'tools';T.mkdir()
for name in ['build-closed.py','run-static.py','equivalence.py','equivalence-attempt1.py','equivalence-attempt2.py','equivalence-attempt3.py','prepare_review.py','review_and_package.py']:shutil.copyfile(E/name,T/name)
attempts={'scope':'Tool-observed comparison-utility diagnostics, not compiler or product test failures. Original scripts retained; existing strict Slither comparison rules unchanged.','attempts':[{'tool_chunk':'09cd2a','script':'equivalence-attempt1.py','failure':'New utility mis-sized the exact solc CBOR key suffix as11bytes instead of9; assertion rejected before producing a pass.'},{'tool_chunk':'dc31da','script':'equivalence-attempt2.py','failure':'Constructor-returned ZZZRoyaltyCodeData creation has no CBOR trailer; utility now compares every raw byte for this exact artifact.'},{'tool_chunk':'79e6ca','script':'equivalence-attempt3.py','failure':'Initial utility assumed only Budget creation body could differ and all creation sizes equal. Actual compile shows Budget+1byte and Migration/NFT embedded own-runtime CBOR changes. Final proof explicitly explains these known objects via exact unique-runtime substitution; never strips arbitrary embedded data.'},{'tool_chunk':'6afc82','script':'equivalence.py','result':'PASS64runtime bodies,0ABI/storage differences, fullAST identical except initializer literal; constructor and metadata effects separated.'}]}
with (D/'contract/EQUIVALENCE_ATTEMPTS.json').open('x',encoding='utf-8',newline='\n')as f:json.dump(attempts,f,indent=2);f.write('\n')
records=[]
for p in sorted(list((D/'contract').rglob('*'))+list(S.rglob('*'))+[D/'static-review.json']):
    if p.is_file():records.append({'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with (D/'contract-static-manifest.json').open('x',encoding='utf-8',newline='\n')as f:json.dump({'kind':'Contract and static evidence only; excludes parent-owned prose/tests','files':records},f,indent=2);f.write('\n')
print(json.dumps({'findings':558,'current':11,'exact_reused':547,'coverage_errors':errors,'packaged_files':len(records),'packaged_bytes':sum(x['bytes']for x in records),'manifest_sha256':hashlib.sha256((D/'contract-static-manifest.json').read_bytes()).hexdigest()}))
