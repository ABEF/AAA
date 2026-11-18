"""Break down already-recorded calls only; no RPC or EVM replay."""
from pathlib import Path
import collections,gzip,hashlib,json
R=Path(__file__).resolve().parents[2]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
D=V/'royalty-rounds-20261118/full02/local-rpc02'
normal=json.loads(gzip.decompress((R/'reports/royalty-rounds-20261118/build/current/compiler-output.json.gz').read_bytes()))
import sys
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
def canonical_type(row):
 kind=row['type']
 return '('+','.join(canonical_type(x)for x in row['components'])+')'+kind[5:]if kind.startswith('tuple')else kind
selectors=collections.defaultdict(set)
for path,contracts in normal['contracts'].items():
 for name,body in contracts.items():
  for signature,selector in body.get('evm',{}).get('methodIdentifiers',{}).items():selectors['0x'+selector].add(signature)
  for row in body.get('abi',[]):
   if row['type']=='function':
    signature=row['name']+'('+','.join(canonical_type(x)for x in row['inputs'])+')';selectors['0x'+keccak256(signature.encode()).hex()[:8]].add(signature)
report=[]
for label in ['rounds-999-opening-eth','rounds-999-rotated-eth','rounds-999-rotated-zzz-allslow','rounds-999-rotated-eth-allfault','rounds-1000-grow-eth']:
 folder=D/label;verification=json.loads((folder/'VERIFICATION.json').read_bytes());records=json.loads(gzip.decompress((folder/'rpc-records.json.gz').read_bytes()))
 traces=[(i,row['response']['result'])for i,row in enumerate(records)if row['request']['method']=='debug_traceCall'and'response'in row and'result'in row['response']and not row['response']['result'].get('error')]
 index,root=traces[0];roles={address:role for role,address in verification['profile']['pins'].items()};roles[verification['workload']['royalty_ledger']]='royalties'
 rows=[]
 def walk(node,path=()):
  children=node.get('calls',[]);used=int(node.get('gasUsed','0x0'),16);selector=node.get('input','')[:10]
  own=used-sum(int(child.get('gasUsed','0x0'),16)for child in children)
  rows.append({'path':list(path),'type':node.get('type'),'role':roles.get(node.get('to','').lower(),'other'),
   'from':node.get('from'),'to':node.get('to'),'selector':selector,'known_signatures':sorted(selectors.get(selector,[])),
   'gas':used,'exclusive_gas':own,'error':node.get('error')})
  for i,child in enumerate(children):walk(child,path+(i,))
 walk(root);rolecost=collections.Counter();methodcost=collections.Counter();methodcount=collections.Counter()
 for row in rows:
  rolecost[row['role']]+=row['exclusive_gas'];methodcost[(row['role'],row['selector'])]+=row['exclusive_gas'];methodcount[(row['role'],row['selector'])]+=1
 item={'case':label,'rpc_records_sha256':hashlib.sha256((folder/'rpc-records.json.gz').read_bytes()).hexdigest(),'record_index':index,
  'root_trace_gas':int(root['gasUsed'],16),'estimated_gas':verification['estimated_gas'],'padded_gas':verification['padded_gas'],
  'exclusive_by_role':dict(rolecost.most_common()),'largest_exclusive_methods':[{'role':role,'selector':sel,'known_signatures':sorted(selectors.get(sel,[])),
   'exclusive_gas':cost,'calls':methodcount[(role,sel)]}for(role,sel),cost in methodcost.most_common(25)],
  'largest_inclusive_royalty_calls':[row for row in rows if row['role']=='royalties'and row['type']=='CALL'],'frames':rows,
  'scope':'Read-only analysis of already-recorded20M actual successful call, not a fresh test. Exclusive=framegas minus immediate children; may include call overhead/refunds. Frame totals across nesting must not be summed.'}
 (folder/'CALL_COSTS.json').write_text(json.dumps(item,indent=2)+'\n');report.append({key:item[key]for key in ['case','root_trace_gas','estimated_gas','padded_gas','exclusive_by_role','largest_exclusive_methods']})
 print(json.dumps({'case':label,'trace':item['root_trace_gas'],'roles':item['exclusive_by_role'],'top_methods':item['largest_exclusive_methods'][:7]}),flush=True)
(D/'CALL_COST_SUMMARY.json').write_text(json.dumps({'cases':report,'execution_replays':0},indent=2)+'\n')
