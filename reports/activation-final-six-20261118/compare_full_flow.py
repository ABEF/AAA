"""Compare captured complete calls with the exact previous thirteen cases."""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
old_path=V/'activation-gas-20261118/full01/local-rpc/SUMMARY.json'
new_path=V/'activation-final-six-20261118/full01/local-rpc/SUMMARY.json'
old=json.loads(old_path.read_bytes());new=json.loads(new_path.read_bytes())
assert old['verification_complete']and new['verification_complete']
aa={r['profile']['label']:r for r in old['results']}
bb={r['profile']['label']:r for r in new['results']}
assert set(aa)==set(bb) and len(aa)==13
fields=('label','sender','destination','value','data','cap','padding_bps','nft_id','shared_bucket','block')
rows=[]
for name,a in aa.items():
    b=bb[name]
    assert {k:a['profile'][k]for k in fields}=={k:b['profile'][k]for k in fields},name
    assert b['verification_complete']and b['production_trace_measurement_verified']and b['royalty_trace_verification']['verified']
    assert b['actual_20m_call']['ok']and b['owned_node_stopped']
    rows.append({'label':name,'baseline_raw':a['estimated_gas'],'current_raw':b['estimated_gas'],
        'raw_saved':a['estimated_gas']-b['estimated_gas'],'baseline_padded':a['padded_gas'],'current_padded':b['padded_gas'],
        'baseline_admitted':a['meets_reviewed_execution_profile'],'current_admitted':b['meets_reviewed_execution_profile'],
        'matched_call_fields':list(fields)})
assert all(r['raw_saved']>0 and r['current_admitted']for r in rows)
assert sum(not r['baseline_admitted']for r in rows)==6
result={'schema':1,'baseline_sha256':hashlib.sha256(old_path.read_bytes()).hexdigest(),
 'current_sha256':hashlib.sha256(new_path.read_bytes()).hexdigest(),'matched_cases':13,
 'previous_refusals_now_admitted':6,'current_refusals':0,'all_raw_estimates_lower':True,
 'worst':max(rows,key=lambda r:r['current_padded']),
 'minimum_raw_saving':min(r['raw_saved']for r in rows),'maximum_raw_saving':max(r['raw_saved']for r in rows),
 'scope':'Same controlled full calls, market anchor, sender, amount and calldata. Source/runtime/private representations differ explicitly; this is not real-market qualification.',
 'rows':rows,'production_approved':False}
(P/'BASELINE_COMPARISON.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
table=['| Case | Previous padded | Current raw | Current padded | Margin under20M |','|---|---:|---:|---:|---:|']
for r in rows:
    table.append(f"| {r['label'].replace('rounds-','')} | {r['baseline_padded']:,} | {r['current_raw']:,} | {r['current_padded']:,} | {20_000_000-r['current_padded']:,} |")
(P/'GAS_TABLE.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items()if k not in ('rows','worst')},indent=2))
