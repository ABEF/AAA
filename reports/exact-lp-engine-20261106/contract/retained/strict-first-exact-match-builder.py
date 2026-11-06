from pathlib import Path
import collections,hashlib,importlib.util,json,re
R=Path.cwd();E=Path(__file__).resolve().parent;S=E/'static-ff6eb88a00';D=E/'candidate-static';D.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('checker',R/'scripts/check-slither-review.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
oldpath='reports/moving-market-flows-20261106/static-review.json';old=json.loads((R/oldpath).read_text());raw=json.loads((S/'detectors-only.json').read_text());execution=json.loads((S/'EXECUTION.json').read_text());impl=json.loads((E/'IMPLEMENTATION_REVIEW.json').read_text())
assert raw['success'] and not raw['error'] and execution['source_unchanged'] and execution['analyzer_success']
prior=collections.defaultdict(list)
for f in old['findings']:prior[f['fingerprint']].append(f)
rows=[];findings=[];compact=[]
for i,f in enumerate(raw['results']['detectors']):
    fp=M.fingerprint(f);matches=prior[fp]
    sources=sorted(set(re.findall(r'src/[^\s()#]+\.sol',f['description'].replace('\\','/'))))
    assert len(matches)==1 and sources,(i,f['check'])
    assert all(old['source_sha256_lf'].get(p)==M.source_hash(R/p) for p in sources),(i,sources)
    priorrow=matches[0]
    body={k:f[k] for k in ('check','impact','confidence','description')};compact.append(body.copy());body['fingerprint']=fp
    body.update(disposition=priorrow['disposition'],rationale=priorrow['rationale'],review_scope='Unique exact prior fingerprint; every description-referenced source LF-byte-identical',prior_review=oldpath,prior_fingerprint=fp)
    findings.append(body);rows.append({'index':i,'check':f['check'],'sources':sources,'current':False,'prior_fingerprint':fp,'exact_unique_fingerprint':True,'description_referenced_sources_unchanged':True})
assert len(findings)==497
review={'analyzer':'Slither0.11.6/crytic-compile0.4.2','date':'2026-11-06','independent_audit':False,'reviewer':'Independent new internal-engine source review plus unique exact unchanged-context reuse; no production approval','source_sha256_lf':{n:M.source_hash(R/n) for n in sorted([p.relative_to(R).as_posix() for p in (R/'src').rglob('*.sol')]+['foundry.toml','package-lock.json','slither.config.json'])},'normal_build':'normal-final-f73ef50a44','actual_analyzer':'static-ff6eb88a00','current_contexts':0,'unique_unchanged_referenced_source_reuse':497,'additional_unflagged_source_review':{'source':impl['source'],'sha256':impl['source_sha256'],'functions_reviewed':11,'record':'contract/IMPLEMENTATION_REVIEW.json','scope':'Unwired internal allocation engine; no actual funding/owner/host/canonical integration guarantee'},'findings':findings}
assert not M.check(raw,review),M.check(raw,review)
report={'success':True,'error':None,'results':{'detectors':compact},'scope':'Lossless strict-check descriptions/impact/confidence/check; full actual detector elements retained externally','original_detectors_sha256':hashlib.sha256((S/'detectors-only.json').read_bytes()).hexdigest()}
assert not M.check(report,review),M.check(report,review)
for name,value in [('static-review.json',review),('static-detectors.json',report)]:
    with (D/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
summary={'strict_records':497,'current_detector_contexts':0,'exact_unique_fingerprint_and_referenced_source_reused':497,'new_source_analyzed':'src/libraries/ExactLPAllocation.sol','new_source_detector_contexts':0,'new_internal_engine_functions_independently_source_reviewed':11,'analyzed_contracts_reported':189,'review_coverage_pass':True,'independent_audit':False,'raw_analyzer_exit':execution['analyzer_exit_code'],'analyzer_json_success':True,'source_unchanged':True,'no_default_record_changed_by_agent':True,'no_deployment':True,'no_rpc':True,'limits':['No detector flags is not proof of correctness or future host integration.','New library is internal and unwired; actual consumer harness functional/gas evidence remains separate.']}
with (D/'static-coverage.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(summary,f,indent=2);f.write('\n')
(E/'static-inventory-exact.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
