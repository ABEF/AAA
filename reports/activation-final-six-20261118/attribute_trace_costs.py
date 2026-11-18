"""Read retained call traces; no requests, execution or synthetic gas sums."""
from pathlib import Path
import gzip,hashlib,json

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
label='rounds-999-opening-zzz-allslow'
rows={}
for family in ('activation-gas-20261118','activation-final-six-20261118'):
    base=V/family/'full01/local-rpc'
    result=next(x for x in json.loads((base/'SUMMARY.json').read_bytes())['results']if x['profile']['label']==label)
    path=base/label/'rpc-records.json.gz';raw=path.read_bytes();records=json.loads(gzip.decompress(raw))
    traces=[x for x in records if x['request']['method']=='debug_traceCall'and'result'in x['response']
            and not x['response']['result'].get('error')]
    assert traces
    chosen_trace=min(traces,key=lambda x:int(x['request']['params'][0]['gas'],16))
    trace=chosen_trace['response']['result']
    pins=result['profile']['pins'];royalty=result['workload']['royalty_ledger']
    chosen={'royalty':royalty,'pricing':pins['contribution_pricing'],'oracle':pins['oracle'],'rewards':pins['rewards']}
    totals={role:{'frames':0,'exclusive_gas':0}for role in chosen}
    def walk(frame):
        used=int(frame.get('gasUsed','0x0'),16)
        children=sum(int(c.get('gasUsed','0x0'),16)for c in frame.get('calls',[]))
        for role,address in chosen.items():
            if frame.get('to','').lower()==address.lower():
                totals[role]['frames']+=1;totals[role]['exclusive_gas']+=used-children
        for child in frame.get('calls',[]):walk(child)
    walk(trace)
    rows[family]={'trace_records_sha256':hashlib.sha256(raw).hexdigest(),
        'trace_call_gas_limit':int(chosen_trace['request']['params'][0]['gas'],16),'exclusive_frame_totals':totals}
result={'schema':1,'case':label,'scope':'Offline exclusive frame gas attribution in retained matching diagnostic traces. This is not an estimate, fee quote or sum of component benchmarks.',
 'records':rows,'execution_performed':False,'requests':0,'production_approved':False}
(P/'TRACE_ATTRIBUTION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,indent=2))
