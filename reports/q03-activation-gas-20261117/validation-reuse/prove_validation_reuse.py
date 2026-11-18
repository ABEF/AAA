"""Inspect the already recorded trace; no RPC, compilation or EVM execution."""
from pathlib import Path
import collections,gzip,hashlib,json
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
D=V/'q03-activation-gas-20261117/validation-reuse';D.mkdir(exist_ok=True)
P=R/'reports/launch-workload-20261117/rpc/initial/activation-eth-0-empty-steady/rpc-records.json.gz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=json.loads(gzip.decompress(P.read_bytes()));record=records[94]
assert record['request']['method']=='debug_traceCall'
root=record['response']['result']
def at(path):
 n=root
 for i in path:n=n['calls'][i]
 return n
def compact(n,i):return {'index':i,'type':n.get('type'),'from':n.get('from'),'to':n.get('to'),'selector':n.get('input','')[:10],'gasUsed':int(n.get('gasUsed','0x0'),16),'error':n.get('error')}
cases=[]
for title,path,start,end,removed,reason in [
 ('Pricing.endEntry redundant pre-final validation',[29],5,12,[5], 'The retained endExecution repeats the complete live proof; only STATIC basis/policy/price/decimal reads separate the duplicate from it.'),
 ('Manager.balance initial context after authenticated begin',[24,35],11,16,[14], 'Authenticated beginManagerExecution validates/captures the whole source scope. Only trusted local loan bookkeeping and STATIC reads precede the policy-only context.'),
 ('Manager.balance zero token pull duplicate context',[24,35],14,28,[24,25,26], 'ExactToken.pull(amount=0) returns before any token call. Intervening balance/LP identity reads are STATIC; nonzero token pulls still perform a full source and policy proof.'),
 ('Manager.balance final context before authenticated end',[24,35],56,65,[56], 'Only STATIC execution revision, policy fingerprint, target-price and module reads precede the retained full endManagerExecution proof.')]:
 n=at(path);children=n['calls'];rows=[compact(children[i],i)for i in range(start,end+1)]
 assert all(i<len(children)for i in removed)
 cases.append({'title':title,'parent_path':path,'parent_selector':n.get('input','')[:10],'child_range':[start,end],'removed_old_child_indices':removed,'reason':reason,'children':rows,'historical_removed_gas':sum(int(children[i]['gasUsed'],16)for i in removed)})
counts=collections.Counter()
def walk(n):
 counts[(n.get('to','').lower(),n.get('input','')[:10])]+=1
 for c in n.get('calls',[]):walk(c)
walk(root)
result={'schema':1,'scope':'Already-recorded historical empty-ETH call, not new measurement/current maximum-state or20M acceptance',
 'trace_path':P.relative_to(R).as_posix(),'trace_sha256':sha(P),'trace_record_index':94,'trace_wire_records':len(records),
 'root':compact(root,0),'oracle_validate_selector':'0x7ae3ab18','oracle_validation_calls':counts[('0x212224d2f2d262cd093ee13240ca4873fccbba3c','0x7ae3ab18')],
 'proofs':cases,'historical_removed_call_gas_sum':sum(c['historical_removed_gas']for c in cases),
 'limitations':['Gas attributed to removed historical calls is not net current gas saving; control-flow and warmness change.','No nested STATIC-chain duplicate is claimed.','All mutable callback, token transfer, venue and final proof boundaries retain validation.','Public getter behavior, captures, source freshness/agreement, source revision, own-swap expected output/full state, thresholds and caps remain.'],
 'source_edit_record_sha256':sha(D/'SOURCE_EDIT.json'),'source_diff_sha256':sha(D/'SOURCE.diff'),'production_approved':False}
(D/'TRACE_PROOF.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'wire_records':len(records),'oracle_validations':result['oracle_validation_calls'],'historical_removed_call_gas_sum':result['historical_removed_call_gas_sum'],'trace_sha256':result['trace_sha256']}))
