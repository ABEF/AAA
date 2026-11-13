"""Offline integrity/compatibility reconciliation; sends no network request."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256

def require(ok,message):
 if not ok:raise ValueError(message)

def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def sanitize(row,sequence):
 out={k:row[k]for k in ('provider','label','observed_at_utc','request','http_status','transport_error_class','body_truncated')if k in row}
 out.setdefault('provider','https://api.blockvectra.com/v1/robinhood_mainnet/public');out.setdefault('label','blockvectra-canonical-capability');out['sequence']=sequence
 if 'response_text'in row:
  out['response_text_sha256']=hashlib.sha256(row['response_text'].encode()).hexdigest();body=json.loads(row['response_text'])
  out['rpc_response']={k:body[k]for k in ('jsonrpc','id','error')if k in body}
  if 'result'in body:
   result=body['result'];method=row['request']['method']
   if method in('eth_getBlockByNumber','eth_getBlockByHash'):out['rpc_response']['result_header']={k:result[k]for k in('number','hash','parentHash','timestamp','gasLimit','gasUsed','baseFeePerGas')if k in result}
   elif method=='eth_getCode':
    code=bytes.fromhex(result[2:]);out['rpc_response']['result_code']={'bytes':len(code),'keccak256':'0x'+keccak256(code).hex()}
   else:out['rpc_response']['result']=result
 return out

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--external-root',type=Path);args=ap.parse_args();manifest=read(HERE/'ARTIFACTS.json')
 for row in manifest['public_files']:
  p=(HERE/row['path']).resolve();require(p.parent==HERE,'Public path escapes');require(sha(p)==row['sha256'],'Public hash mismatch '+row['path'])
 results=read(HERE/'RESULTS.json');obs=read(HERE/'OBSERVATIONS.json');methods=read(HERE/'METHODS.json');rows=obs['rows']
 require(len(rows)==33,'RPC scope drift');counts={'attempts':len(rows),'valid_rpc_results':0,'rpc_errors':0,'transport_failures':0,'http_denials':0};phases={};codes={}
 for i,row in enumerate(rows,1):
  require(row['sequence']==i,'Sequence drift');q=row['request'];require(q['method']in methods['allowed'],'Non-read method');phase=row['label'];provider=row['provider'];phases.setdefault(phase,{'requests':0,'chain':False,'provider':provider});state=phases[phase];state['requests']+=1
  require(state['provider']==provider,'Provider switched within phase')
  if q['method']!='eth_chainId':require(state['chain'],'Missing valid chain handshake')
  if 'transport_error_class'in row:
   counts['transport_failures']+=1;require(q['method']=='eth_chainId'and provider=='https://rpc.ordofi.network','Unexpected transport failure scope');continue
  require(row['http_status']==200 and row['body_truncated']is False,'Invalid/truncated HTTP response');body=row['rpc_response'];require(body['jsonrpc']=='2.0'and body['id']==q['id'],'RPC envelope drift')
  if 'error'in body:counts['rpc_errors']+=1;code=str(body['error']['code']);codes[code]=codes.get(code,0)+1
  else:counts['valid_rpc_results']+=1
  if q['method']=='eth_chainId':require(int(body['result'],16)==4663,'Wrong chain');state['chain']=True
  if q['method']in('eth_call','eth_estimateGas','debug_traceCall'):
   tx=q['params'][0];require(set(tx)=={'to','data','gas'},'Unexpected transaction fields');require(tx['to']==methods['gas_info_address']and tx['data']in methods['allowed_selectors'],'Non-reviewed target/data');require(int(tx['gas'],16)in methods['gas_fields'],'Unexpected gas field')
   require(len(q['params'])==(3 if q['method']=='debug_traceCall'else 2),'State override or extra argument')
   if q['method']=='debug_traceCall':require(q['params'][2]==methods['trace_options']and int(tx['gas'],16)==24000000,'Trace controls changed')
  elif q['method']=='eth_getCode':require(q['params'][0]==methods['selected_core_read'],'Unexpected code target')
 require(counts==obs['counts']==results['counts']=={'attempts':33,'valid_rpc_results':24,'rpc_errors':8,'transport_failures':1,'http_denials':0},'Count drift')
 require(codes=={'-32011':5,'-32601':2,'-32000':1},'Failure evidence changed')
 require({k:x['requests']for k,x in phases.items()}=={'blockvectra-canonical-capability':13,'blockvectra-numbered-diagnostic':7,'ordofi-capability':1,'daybreak-capability':12},'Phase bound changed')
 require(results['chain_parameters']['max_tx_execution']==results['chain_parameters']['max_block_execution']==32000000,'Wrong real execution parameters')
 require(results['chain_parameters']['anchor']['header_gas_limit']==1<<50,'Synthetic header changed')
 q=results['qualification']
 for name in('actual_full_popl_operation_executed','effective_provider_execution_ceiling_proven','required_trace_provider_qualified','archive_or_sustained_service_qualified','complete_popl_fee_quote_obtained','fee_policy_review_hash_attested','operator_spending_caps_selected','provider_adopted','keys_or_accounts_used'):require(q[name]is False,'Unproven qualification '+name)
 require(q['public_transactions']==q['configuration_changes']==q['signatures']==0,'Unauthorized action claim')
 day=next(x for x in results['provider_results']if x['provider']=='https://robinhood.daybreak-rpc.network');expected='0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626'
 require(day['selected_core_bytes']==24009 and day['selected_core_keccak256']==expected and day['matches_registry_pin']is True,'Core identity drift');require(day['own_header_by_hash_matches']and day['same_prior_blockvectra_anchor_matches']and day['same_header_rechecked'],'Anchor proof missing')
 require(day['canonical_hash_calls_gas_fields']==day['canonical_hash_estimates_gas_fields']==[20000000,24000000]and day['canonical_hash_cheap_view_estimate_gas']==23182,'Cap compatibility drift')
 if args.external_root:
  root=args.external_root.resolve()
  for row in manifest['external_files']:
   p=(root/row['path']).resolve();require(p.parent==root,'External path escapes');require(sha(p)==row['sha256'],'External hash mismatch '+row['path'])
  raw=read(root/'blockvectra-rpc-raw.json')['requests']+read(root/'phase2-raw.json');require([sanitize(x,i+1)for i,x in enumerate(raw)]==rows,'Raw/public summaries differ')
  require(sha(root/'blockvectra-catalog.raw')==read(HERE/'SOURCES.json')['primary_research'][1]['sha256'],'Catalog changed')
  data=read(root/'PHASE2_RESULT.json');d=next(x for x in data if x['label']=='daybreak-capability');b=read(root/'BLOCKVECTRA_RESULT.json');require(d['own_header_by_hash']['result']['hash']==d['anchor']['hash'],'Own hash mismatch');require(d['prior_blockvectra_header']['result']['hash']==b['anchor']['hash'],'Cross-endpoint header mismatch')
 print(json.dumps({'status':'PASS','rpc_attempts':len(rows),'public_files':len(manifest['public_files']),'external_files_checked':len(manifest['external_files'])if args.external_root else 0,'new_network_calls':0,'new_evm_tests_or_compiles':0,'provider_qualified':False}))
if __name__=='__main__':
 try:main()
 except (OSError,ValueError,KeyError,TypeError)as ex:print('ERROR: '+str(ex),file=sys.stderr);sys.exit(1)
