"""Create two immutable authority-text errata; reuse existing analyzer evidence."""
from pathlib import Path
import hashlib,importlib.util,json
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent.parent
prior=R/'reports/reference-execution-20261111/static-review.json'
prior_bytes=prior.read_bytes();review=json.loads(prior_bytes.decode('utf-8'))
corrections=[]
for f in review['findings']:
 i=f.get('current_context_index')
 if i not in (98,142) or f.get('review_evidence')!='static/current-162.json':continue
 old=f['rationale']
 if i==98:
  new=old.replace('typed Vault/Fees operation','typed Vault/Buyback operation')
 else:
  new=old.replace('onlyVault/onlyFees/onlyPositionExecutor checks on economic operations',
      'fixed Vault or Buyback authorization on swap, onlyVault on typed custody operations, and onlyPositionExecutor on its parent callbacks')
 assert new!=old and 'onlyFees' not in new and 'Vault/Fees' not in new
 corrections.append({'current_context_index':i,'fingerprint':f['fingerprint'],
  'check':f['check'],'description':f['description'],'old_rationale':old,'corrected_rationale':new,
  'evidence':'src/ZZZLiquidityManager.sol:220-223; swap authenticates the sealed fixed Vault or Buyback. Typed custody operations retain their own fixed caller checks.',
  'source_sha256':hashlib.sha256((R/'src/ZZZLiquidityManager.sol').read_bytes()).hexdigest()})
 f['rationale']=new
assert len(corrections)==2
review['reviewer']='Internal correction of two authority-description errors only; original162current-context/405exact-reuse scopes retained. Remaining565records were not freshly analyzed or re-audited by this errata.'
review['scope']['errata']={'prior_review':'reports/reference-execution-20261111/static-review.json',
 'prior_sha256':hashlib.sha256(prior_bytes).hexdigest(),'corrected_context_indices':[98,142],
 'rationale_fields_only':True,'fresh_analyzer_run':False,'fresh_compilation':False,
 'unchanged_finding_identities':567,'remaining_records_not_freshly_reaudited':565,
 'evidence':'contracts/AUTHORITY_ERRATA.json',
 'inherited_evidence_base':'reports/reference-execution-20261111/'}
errata={'schema':1,'date':'2026-11-11','source_commit':'872a5a5','production_source_unchanged':True,
 'prior_review':'reports/reference-execution-20261111/static-review.json',
 'prior_sha256':hashlib.sha256(prior_bytes).hexdigest(),'corrections':corrections,
 'meaning':'Correct two authorizations in prose; no permission, source, detector identity or original finding disposition changes.'}
for path,value in [(P/'static-review.json',review),(P/'contracts/AUTHORITY_ERRATA.json',errata)]:
 with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=True);f.write('\n')
assert prior.read_bytes()==prior_bytes
print(json.dumps({'rationale_corrections':2,'finding_identities':567,'prior_unchanged':True}))
