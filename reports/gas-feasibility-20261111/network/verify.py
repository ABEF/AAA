"""Offline integrity verification; never accesses RPC or alters configuration."""
import argparse,hashlib,json,pathlib,re,sys
P=pathlib.Path(__file__).resolve().parent

def check(condition,message):
 if not condition:raise ValueError(message)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--external-root',type=pathlib.Path);args=a.parse_args()
 manifest=read(P/'ARTIFACTS.json')
 for item in manifest['public_files']:
  target=P/item['path'];check(target.is_file(),'Missing public file '+item['path']);check(sha(target)==item['sha256'],'Public hash mismatch '+item['path'])
 obs=read(P/'OBSERVATIONS.json');limits=read(P/'LIMITS.json');methods=read(P/'METHODS.json');sources=read(P/'SOURCES.json')
 rows=[r for probe in obs['probes']for r in probe['requests']]
 counts={'attempted_rpc_requests':len(rows),'successful_rpc_results':sum('result'in r or 'result_summary'in r for r in rows),'rpc_errors_http200':sum('rpc_error'in r for r in rows),'http_access_denials':sum(r.get('http_status')==403 for r in rows),'environment_failures':sum(r.get('http_status')is None for r in rows)}
 check(counts==obs['counts'],'Observation counts mismatch');check(counts=={'attempted_rpc_requests':31,'successful_rpc_results':23,'rpc_errors_http200':3,'http_access_denials':4,'environment_failures':1},'Unexpected scope/count')
 allowed=set(methods['allowed_rpc_methods']);views={r['selector']:r['address']for r in methods['precompile_views']}
 for r in rows:
  q=r['request'];check(q['method']in allowed,'Non-read method');check(not r.get('body_truncated'),'Truncated RPC body')
  if q['method']=='eth_call':
   call=q['params'][0];check(set(call)=={'to','data','gas'},'Unexpected call fields');check(views.get(call['data'])==call['to'],'Non-reviewed view');check(call['gas']=='0x30d40','Call exceeds gas bound')
  if r.get('http_status')==403:check(r['access_response']['retryable']is False,'Denial unexpectedly retryable')
 live=limits['live_observed'];check(limits['anchor']['chain_id']==4663,'Wrong chain');check(limits['anchor']['same_header_rechecked']is True,'Missing anchor recheck')
 check(live['max_transaction_execution_gas_parameter']==32000000 and live['max_block_execution_gas_parameter']==32000000,'Wrong live limits');check(live['header_gas_limit']==1<<50,'Wrong synthetic header');check(live['arb_sys_version_raw']==116 and live['arbos_version_decoded_with_documented_nitro_offset']==61,'Version decoding error')
 check(limits['provider_catalog_observed']['public_history_blocks']==900,'Wrong public retention');check(limits['identity_corroboration']['code_keccak256']=='0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626','Wrong core hash');check(limits['unresolved']['public_transactions_submitted']==0 and limits['unresolved']['defaults_or_caps_changed']is False,'Unauthorized state scope')
 for name in ('actual_full_popl_operation_estimate','actual_full_popl_total_fee_eth','numeric_provider_call_or_estimate_gas_cap'):check(limits['unresolved'][name]is None,'Unverified qualification '+name)
 if args.external_root:
  root=args.external_root.resolve()
  for item in manifest['external_files']:
   path=(root/item['path']).resolve();check(path.parent==root,'External path escapes');check(path.is_file(),'Missing external '+item['path']);check(sha(path)==item['sha256'],'External hash mismatch '+item['path'])
  for probe in obs['probes']:
   raw=read(root/probe['external_file']);rs=raw.get('requests',[raw]);check(len(rs)==len(probe['requests']),'Raw row count mismatch')
   for r,t in zip(rs,probe['requests']):
    check(r['request']==t['request'],'Raw request mismatch');check(hashlib.sha256(r.get('response_text','').encode()).hexdigest()==t['response_body_sha256'],'Raw response mismatch')
    if r.get('http_status')==200:
     v=json.loads(r['response_text']);check(v.get('jsonrpc')=='2.0'and v.get('id')==r['request']['id'],'RPC envelope mismatch');check(('result'in v)!=('error'in v),'RPC result/error ambiguity')
     if 'rpc_error'in t:check(v.get('error')==t['rpc_error'],'RPC error lost')
     elif 'result'in t and r['request']['method']!='eth_getBlockByNumber':check(v.get('result')==t['result'],'RPC result changed')
  for c in sources['captures']:
   check(sha(root/c['external_capture'])==c['capture_sha256'],'Source metadata mismatch')
   if c['external_body']:check(sha(root/c['external_body'])==c['body_sha256'],'Source body mismatch')
 print(json.dumps({'status':'pass','rpc_attempts':len(rows),'valid_rpc_results':counts['successful_rpc_results'],'public_files':len(manifest['public_files']),'external_files_checked':len(manifest['external_files'])if args.external_root else 0,'network_calls':0,'signature_or_configuration_changes':0}))
if __name__=='__main__':
 try:main()
 except (OSError,ValueError,KeyError,TypeError)as e:print('ERROR: '+str(e),file=sys.stderr);sys.exit(1)
