from pathlib import Path
import gzip,hashlib,io,json,re,subprocess
ROOT=Path.cwd()
SOURCE=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/fee-flow-audit-20261107/keeper/capacity-20261107-013629-8744')
DEST=ROOT/'reports/fee-flow-audit-20261107/keeper'
BASE='c055684a558519eab308a24b81746bf1b9842d96'
THRESHOLD=16384
sha=lambda data:hashlib.sha256(data).hexdigest()
def encoded_json(value):return (json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
def compress(data):
    stream=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',fileobj=stream,compresslevel=9,mtime=0) as archive:archive.write(data)
    return stream.getvalue()
assert not DEST.exists(),'Exclusive package destination already exists'
summary=json.loads((SOURCE/'final-summary.json').read_text(encoding='utf-8'))
source_files=sorted(p for p in SOURCE.rglob('*') if p.is_file())
for relative,expected in summary['owned_files'].items():
    assert sha((SOURCE/'source-final'/relative).read_bytes())==expected
    assert sha((ROOT/relative).read_bytes())==expected,'Source changed after freeze: '+relative
protected=[]
for relative,expected in summary['protected_files'].items():
    actual=sha((ROOT/relative).read_bytes());assert actual==expected
    protected.append({'path':relative,'expected_sha256':expected,'observed_sha256':actual,'byte_identical':True})
stages={
'attempt2.log':{'kind':'initial_fixture_failure','source_scope':'Initial capacity-only implementation; missing explicit included-fee policy in mocked live sender fixture. Not final-source verification.'},
'attempt3-affected.log':{'kind':'corrected_initial_scope','source_scope':'Initial capacity-only source before opaque-prefix, late-send and output-validation additions. Not final-source verification.'},
'attempt4-negative-late-send.log':{'kind':'intended_negative_control','source_scope':'Before fresh7 late head/deadline/day stop. Mocked sender accepted expired/new-day-over-budget candidates; expected assertion failures.'},
'attempt5-final-focused.log':{'kind':'corrected_intermediate_scope','source_scope':'Capacity, opaque-prefix and late-send fixes; before malformed-result and saved-pending-count regressions. Not final-source verification.'},
'attempt6-final-affected.log':{'kind':'corrected_broad_scope','source_scope':'All substantive sizing, opaque-prefix, late-send and output checks. Before the final pending-source-count admission guard and its new regression. Exact run-start source was not separately copied; do not label final snapshot as the run-start snapshot.'},
'attempt7-final-pending-and-focused.log':{'kind':'final_focused_scope','source_scope':'22 methods against the exact source-final snapshots and final-summary owned-file hashes.'},
'baseline-negative.log':{'kind':'original_worker_negative_control','source_scope':'Only RoyaltyAutomation loaded from original c055684 keeper/royalties.py; composed with the corrected monitor/test fixture of that stage. Not a whole-baseline test run.'}}
method_pattern=re.compile(r'^test_\w+ \((tests_python\.[^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$')
observations={}
for log,stage in stages.items():
    rows=[]
    for line_no,line in enumerate((SOURCE/log).read_text(encoding='utf-8-sig').splitlines(),1):
        match=method_pattern.fullmatch(line)
        if match:
            method,status=match.groups();status=status.strip()
            row={'log':log,'line':line_no,'outcome':status,'stage':stage['kind']}
            observations.setdefault(method,[]).append(row);rows.append(row)
    stage['observed_methods']=len(rows)
    stage['outcomes']={status:sum(row['outcome']==status for row in rows) for status in sorted({row['outcome'] for row in rows})}
selected={}
for log in ('attempt6-final-affected.log','attempt7-final-pending-and-focused.log'):
    for method,rows in observations.items():
        for row in rows:
            if row['log']==log:selected[method]=row
assert len(selected)==340
assert sum(row['outcome']=='ok' for row in selected.values())==338
assert sum(row['outcome'].startswith('skipped') for row in selected.values())==2
assert stages['attempt6-final-affected.log']['observed_methods']==339
assert stages['attempt7-final-pending-and-focused.log']['observed_methods']==22
provenance={'schema':1,'counting_rule':'Union of fully qualified method IDs from corrected broad attempt6 and final focused attempt7; latest selected observation per ID. Earlier passes/failures/negative controls are retained but add no counts.','distinct_selected_cases':340,'passed':338,'skipped':2,'final_focused_methods':22,'broad_before_pending_guard_methods':339,'stages':stages,'methods':[{'id':method,'selected_evidence':selected[method],'all_observations':rows,'final_focused':any(row['log']=='attempt7-final-pending-and-focused.log' for row in rows)} for method,rows in sorted(observations.items()) if method in selected]}
entries=[]
DEST.mkdir(parents=True,exist_ok=False)
def put(relative,data,origin,force_raw=False):
    raw_hash=sha(data);compression='gzip-mtime0-filename-empty-level9' if len(data)>=THRESHOLD and not force_raw else 'none'
    stored=compress(data) if compression!='none' else data
    archived=relative+'.gz' if compression!='none' else relative
    target=DEST/archived;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as file:file.write(stored)
    recovered=gzip.decompress(stored) if compression!='none' else stored
    assert recovered==data
    if compression!='none':assert compress(data)==stored
    entries.append({'path':archived,'logical_path':relative,'raw_size':len(data),'raw_sha256':raw_hash,'stored_size':len(stored),'stored_sha256':sha(stored),'compression':compression,'origin':origin})
for source in source_files:
    relative=source.relative_to(SOURCE).as_posix()
    put(relative,source.read_bytes(),{'kind':'exact_external_copy','source_path':str(source),'source_relative_path':relative},force_raw=relative=='final-summary.json')
for relative in ('keeper/monitor.py','keeper/royalties.py'):
    data=subprocess.check_output(['git','cat-file','blob',BASE+':'+relative])
    blob=subprocess.check_output(['git','rev-parse',BASE+':'+relative],text=True).strip()
    put('baseline/'+BASE+'/'+relative,data,{'kind':'exact_git_blob','commit':BASE,'repository_path':relative,'git_blob':blob})
put('per-method-provenance.json',encoded_json(provenance),{'kind':'derived_from_preserved_logs','inputs':list(stages)})
put('protected-proof.json',encoded_json({'schema':1,'observed_after_packaging_preflight':True,'files':protected}),{'kind':'read_only_sha256_observation','no_protected_bytes_modified':True})
notes={'schema':1,'source_evidence_root':str(SOURCE),'compression_threshold_bytes':THRESHOLD,'compression':'Gzip level9,mtime0,emptyfilename; regenerated bytes verified equal and decompressed bytes verified equal to original.','missing_original_artifacts':[{'referenced_by':'final-summary.json stages[0]','path':'attempt1.log','observation':'No file exists in original evidence directory. Initial python command was not found by PowerShell; no Python tests ran. Do not treat this absent log as an empty successful run.','record_basis':'Observed original command result in the agent conversation; this note is generated packaging metadata, not a recreated raw log.'}],'stage_source_boundary':'Exact source-final files bind final22 focused methods. Broad339-method run precedes final pending-count guard; original logs and per-method stage scope preserve that boundary. Counts340/338/2 are a deduplicated corrected-stage union, not one full final-source suite.','no_work_reexecuted':'Packaging reads/copies/hashes/compresses evidence and reads two original Git blobs only. No tests, compilation, signer, service or chain operations executed.','summary_preservation':'final-summary.json is copied byte-for-byte; its original missing attempt1.log reference is explained here rather than edited.'}
put('packaging-notes.json',encoded_json(notes),{'kind':'generated_packaging_metadata'})
manifest={'schema':1,'package':'reports/fee-flow-audit-20261107/keeper','baseline_commit':BASE,'original_evidence_root':str(SOURCE),'payload_count':len(entries),'compression_threshold_bytes':THRESHOLD,'entries':entries,'manifest_exclusions':['artifact-manifest.json','package-verification.json'],'verification_contract':'Every entry authenticates stored and decompressed raw bytes. Exact external copies must match the source file SHA256; Git baselines must match the named blob. Metadata manifest and verification are generated once, without rewriting source evidence.'}
manifest_bytes=encoded_json(manifest)
with (DEST/'artifact-manifest.json').open('xb') as file:file.write(manifest_bytes)
validated=[]
for entry in entries:
    stored=(DEST/entry['path']).read_bytes();assert sha(stored)==entry['stored_sha256'];assert len(stored)==entry['stored_size']
    raw=gzip.decompress(stored) if entry['compression']!='none' else stored
    assert sha(raw)==entry['raw_sha256'];assert len(raw)==entry['raw_size']
    if entry['compression']!='none':assert stored==compress(raw)
    origin=entry['origin']
    if origin['kind']=='exact_external_copy':assert raw==Path(origin['source_path']).read_bytes()
    elif origin['kind']=='exact_git_blob':assert raw==subprocess.check_output(['git','cat-file','blob',origin['commit']+':'+origin['repository_path']])
    validated.append(entry['path'])
verification={'schema':1,'result':'verified','artifact_manifest_sha256':sha(manifest_bytes),'payload_files_verified':len(validated),'exact_external_copies':sum(e['origin']['kind']=='exact_external_copy' for e in entries),'git_baseline_blobs':sum(e['origin']['kind']=='exact_git_blob' for e in entries),'compressed_files':sum(e['compression']!='none' for e in entries),'all_stored_hashes_sizes_raw_roundtrips_and_deterministic_gzip_checked':True,'protected_files_byte_identical':True,'source_final_matches_declared_hashes_and_current_workspace':True,'distinct_corrected_methods':340,'passed':338,'skipped':2,'final_focused':22,'test_reruns_during_packaging':0,'verified_payload_paths':validated}
with (DEST/'package-verification.json').open('xb') as file:file.write(encoded_json(verification))
print(json.dumps(verification,indent=2))
