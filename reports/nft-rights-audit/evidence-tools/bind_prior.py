from pathlib import Path
import hashlib, json

repo = Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
dest = repo/'reports/nft-rights-audit'
def sha(path, lf=False):
    data=path.read_bytes()
    return hashlib.sha256(data.replace(b'\r\n',b'\n') if lf else data).hexdigest()
prior=repo/'reports/operations-hardening/static-analysis/coverage.json'
coverage=json.loads(prior.read_text())
expected=coverage['all_current_source_sha256_lf']
assert len(expected)==32
assert all(sha(repo/name,True)==digest for name,digest in expected.items())
assert sha(repo/'reports/production/slither-review.json')==coverage['current_review_sha256']
front=repo/'reports/frontend-transactions/verification-summary.json'
summary=json.loads(front.read_text())
binding=json.loads((front.parent/'unchanged-production-binding.json').read_text())
production={k:v for k,v in binding['production_source_sha256'].items() if k.startswith('src/')}
assert len(production)==29
assert all(sha(repo/name)==digest for name,digest in binding['production_source_sha256'].items())
fork=front.parent/'fork-summary.json'
fork_data=json.loads(fork.read_text())
print('Fork receipt keys:',list(fork_data))
assert fork_data['status']=='passed' and fork_data['source_unchanged']
drift=[name for name,digest in fork_data['source_sha256_after'].items() if sha(repo/name)!=digest]
fork_closure={}
for bound in fork_data['compiler_bindings_after'].values():
    for name,record in bound['current_metadata_source_bindings'].items():
        assert sha(repo/name)==record['sha256'], name
        fork_closure[name]=record['sha256']
assert not set(drift).intersection(fork_closure)
value={
 'scope':'Historical evidence revalidated against unchanged production source; no fresh Slither or live fork run claimed.',
 'independent_audit':False,'production_approved':False,
 'current_production_sources_sha256':production,
 'static':{'prior_coverage':prior.relative_to(repo).as_posix(),'prior_coverage_sha256':sha(prior),
   'source_and_configuration_sha256_lf':expected,'all_match':True,
   'findings':coverage['findings'],'dispositions':coverage['dispositions'],
   'unresolved_detector_entries':coverage['unresolved_detector_entries'],
   'known_open_capacity_reservation_issue':True},
 'fork':{'prior_summary':front.relative_to(repo).as_posix(),'prior_summary_sha256':sha(front),
   'prior_receipt':fork.relative_to(repo).as_posix(),'prior_receipt_sha256':sha(fork),
   'counts':summary['fork']['counts_by_suite'],'compiled_dependency_closure_matches':True,
   'dependency_sha256':fork_closure,'changed_files_outside_fork_closure':drift,
   'block_pins':fork_data['block_pins'],'sources_outside_fork_closure':fork_data['production_sources_outside_fork_closure'],
   'limitations':'Actual venue fork with mocked authorities/VRF and synthetic USD calibration. No public transactions or production service qualification.'}}
(dest/'unchanged-production-evidence.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print('Bound unchanged production source to prior internal Slither and fork evidence.')
