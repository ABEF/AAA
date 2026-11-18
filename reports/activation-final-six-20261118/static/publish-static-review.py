"""Publish complete source-bound actual analysis, without mutating old evidence."""
from pathlib import Path
import sys,importlib.util,hashlib,json,gzip,copy,re,collections
sys.dont_write_bytecode=True
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2');E=Path(__file__).resolve().parent;D=E/'static-fb34dc578e';P=R/'reports/activation-final-six-20261118';S=P/'static'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def enc(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as f:f.write(enc(obj))
def save_raw(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as f:f.write(raw)
spec=importlib.util.spec_from_file_location('checker',R/'scripts/check-slither-review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
prior_path=R/'reports/test-seal-deep-review-20261117/static-final-review.json';prior_raw=prior_path.read_bytes();prior=json.loads(prior_raw);old={f['fingerprint']:f for f in prior['findings']}
data=json.loads((D/'slither.json').read_bytes());run=json.loads((D/'EXECUTION.json').read_bytes());current=json.loads((E/'CURRENT_CONTEXTS.json').read_bytes());reuse=json.loads((E/'EXACT_REUSE.json').read_bytes())['reuse']
assert data['success'] is True and not data.get('error') and run['analyzer_success'] is True and run['source_unchanged'] is True
assert run['raw_report_sha256']==sha((D/'slither.json').read_bytes()) and run['compiler_invoked'] is False
normal=Path(run['normal_directory']);input_raw=(normal/'compiler-input.json').read_bytes();inp=json.loads(input_raw)
assert run['compiler_input_sha256']==sha(input_raw) and len(inp['sources'])==100
assert all((R/k).read_bytes()==v['content'].encode('utf-8') for k,v in inp['sources'].items())
compiled_after={k:sha((R/k).read_bytes()) for k in inp['sources']}
source={p.relative_to(R).as_posix():m.source_hash(p) for p in sorted((R/'src').rglob('*.sol'))};source.update({p:m.source_hash(R/p) for p in ['foundry.toml','package-lock.json','slither.config.json']})
assert len(source)==64 and all(run['source_before'][k]==run['source_after'][k]==sha((R/k).read_bytes()) for k in source)
fresh={};assessment_files={}
for name in ['ROYALTY_ASSESSMENTS.json','PRICING_ASSESSMENTS.json','OTHER_ASSESSMENTS.json']:
    raw=(E/name).read_bytes();ass=json.loads(raw);rows=ass.get('findings',ass.get('assessments'))
    assert len(rows)==ass['count'] and not ass.get('unresolved_confirmed_defects',ass.get('confirmed_unresolved_defects',[]))
    for row in rows:
        assert row['fingerprint'] not in fresh;fresh[row['fingerprint']]=copy.deepcopy(row)
    assessment_files[name]=sha(raw)
assert len(fresh)==current['current_count']==147
reuse_allowed={f['fingerprint']:f for f in reuse};assert len(reuse_allowed)==454
all_rows=[];comparison_count=0
for finding in data['results']['detectors']:
    fp=m.fingerprint(finding);desc=m.normalized_description(finding);paths=sorted(set(re.findall(r'src/[A-Za-z0-9_./-]+\.sol',desc)))
    if fp in fresh:
        row=fresh[fp];assert row['description']==desc
        assert all(row[k]==finding[k] for k in ('check','impact','confidence'))
        assert row['referenced_paths']==paths and row['referenced_source_sha256_lf']=={p:source[p] for p in paths}
        row.pop('prior_exact_fingerprint_rationale',None)
    else:
        assert fp in reuse_allowed and fp in old and paths
        assert all(source[p]==prior['source_sha256_lf'][p] for p in paths)
        row=copy.deepcopy(old[fp]);row.update(description=desc,referenced_paths=paths,referenced_source_sha256_lf={p:source[p] for p in paths},prior_review='reports/test-seal-deep-review-20261117/static-final-review.json',prior_fingerprint=fp,review_scope='Exact prior fingerprint and every description-referenced LF source unchanged. Prior rationale, authority and transitive-context limits retained; not a new full-transitive review.')
    assert row['disposition'] in ('false_positive','informational','accepted_risk') and row['rationale'].strip()
    assert row['fingerprint']==m.fingerprint(row)
    if finding['check']=='reentrancy-no-eth':
        try:m.write_bundle_atoms(row)
        except ValueError:pass
        else:row['comparison']=m.WRITE_BUNDLES;comparison_count+=1
    all_rows.append(row)
assert len(all_rows)==len({r['fingerprint'] for r in all_rows})==601
projection={'success':data['success'],'error':data.get('error'),'results':{'detectors':[{k:f[k] for k in ('check','impact','confidence','description')} for f in data['results']['detectors']]},'projection':{'kind':'Complete actual analyzer detector input projection; no findings removed','detector_count':601,'raw_analyzer_report_sha256':run['raw_report_sha256'],'compiler_input_sha256':run['compiler_input_sha256'],'compiler_output_sha256':run['compiler_output_sha256'],'additional_analyzer_run':False,'additional_compiler_run':False,'omitted_metadata':['supporting AST/element metadata','compilation objects'],'retained_fields_per_detector':['check','impact','confidence','description']}}
assert [m.fingerprint(r) for r in projection['results']['detectors']]==[m.fingerprint(r) for r in data['results']['detectors']]
proj_raw=enc(projection);proj_gz=gzip.compress(proj_raw,mtime=0)
review={'analyzer':'Slither0.11.6/crytic-compile0.4.2','date':'2026-11-18','independent_audit':False,'reviewer':'Internal source-specific review:147 individually current contexts and454 unique exact description/referenced-source reuses; not independent audit or exploit absence.','source_sha256_lf':dict(sorted(source.items())),'findings':all_rows,'scope':{'build':'activation-final-six-20261118','factory_payload_version':6,'royalty_allocation_version':2,'solidity_sources':61,'compiler_input_sources':100,'normal_gates':48,'actual_analyzer':True,'compiler_invoked_by_analyzer':False,'compiler_input_sha256':run['compiler_input_sha256'],'compiler_output_sha256':run['compiler_output_sha256'],'build_info_sha256':run['build_info_sha256'],'source_bracket_unchanged':True,'compiled100_sources_rechecked_after_analysis':True,'compiled_source_sha256_after':compiled_after,'changed_since_prior_review':sorted(current['changed_sources']),'individually_current_records':147,'unique_exact_reused':454,'total':601,'assessment_files_sha256':assessment_files,'prior_review':'reports/test-seal-deep-review-20261117/static-final-review.json','prior_review_sha256_raw':sha(prior_raw),'reuse_limit':'Only unique exact fingerprints with every description-referenced LF source unchanged. Prior transitive/context limits remain; unchanged source is not proof every upstream behavior is unchanged.','analyzer_exit_code':run['analyzer_exit_code'],'analyzer_exit_note':'Windows findings-present4294967295 is preserved, not relabelled0. Analyzer JSON success/no error and full review coverage are checked separately. CI Linux findings-present255 remains its existing accepted analyzer exit.','raw_analyzer_report_sha256':run['raw_report_sha256'],'raw_analyzer_log_sha256':run['raw_log_sha256'],'strict_input_projection':{'path':'reports/activation-final-six-20261118/static-input.json.gz','gzip_sha256':sha(proj_gz),'decompressed_sha256':sha(proj_raw),'gzip_bytes':len(proj_gz),'decompressed_bytes':len(proj_raw),'retains_all_detector_records':True,'retains_exact_detector_text_and_classification':True,'fingerprints_equal_raw_analyzer_in_order':True},'existing_narrow_write_bundle_comparison_records':comparison_count,'matcher_policy_changed':False,'no_unreviewed_findings_ignored':True,'not_qualified':['Independent audit or exploit absence','real markets/routes/currencies/providers/complete fees','64-currency/two-LP maximum workloads and all activation orders','actual wallet/host/constructor/operating adoption','public deployment/sealing/signing/services/sites'],'assembly_scope':'Explicit typed slot/memory/domain/width proofs were inspected; analyzer cannot infer all assembly effects. More/fewer detector records are not claims of more/fewer vulnerabilities.','new_test_methods_run_here':0}}
assert not m.check(data,review),m.check(data,review)
assert not m.check(projection,review),m.check(projection,review)
save(P/'static-review.json',review);save_raw(P/'static-input.json.gz',proj_gz)
save(S/'CURRENT_CONTEXTS.json',current);save(S/'EXACT_REUSE_PROOF.json',{'count':454,'prior_review_sha256':sha(prior_raw),'reuse':reuse})
for name in assessment_files:save_raw(S/name,(E/name).read_bytes())
save(S/'EXECUTION.json',run)
for name in ['slither.json','slither.log']:
    raw=(D/name).read_bytes();save_raw(S/(name+'.gz'),gzip.compress(raw,mtime=0))
save_raw(S/'versions.txt',(D/'versions.txt').read_bytes())
save_raw(S/'run-static.py',(E/'run-static.py').read_bytes());save_raw(S/'publish-static-review.py',Path(__file__).read_bytes())
result={'actual_analyzer_success':True,'analyzer_exit_code':run['analyzer_exit_code'],'total':601,'individually_current':147,'exact_referenced_source_reuse':454,'dispositions':dict(collections.Counter(r['disposition'] for r in all_rows)),'raw_strict_check_pass':True,'complete_projection_strict_check_pass':True,'all100_compiler_sources_stable':True,'compiler_reinvoked':False,'matcher_policy_changed':False,'independent_audit':False,'production_approved':False,'new_test_methods':0,'default_adoption_pending':True,'review_sha256':sha((P/'static-review.json').read_bytes()),'projection_gzip_sha256':sha(proj_gz)}
save(S/'REVIEW_COVERAGE.json',result);save(E/'PUBLISHED_REVIEW.json',result)
print(json.dumps(result,indent=2))
