"""Offline reconciliation of independent genesis and the recorded full profile."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256

def require(ok,message):
 if not ok:raise ValueError(message)
def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def hashed(value):return'0x'+keccak256(value).hex()
def unpack(data):
 require(isinstance(data,str)and data.startswith('0x')and(len(data)-2)%64==0,'Malformed event ABI')
 return[data[i:i+64]for i in range(2,len(data),64)]
def result(row):return row['rpc_response']['result']

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--external-root',type=Path)
 args=parser.parse_args();manifest=read(HERE/'ARTIFACTS.json')
 for item in manifest['public_files']:
  path=(HERE/item['path']).resolve()
  require(path.parent==HERE and sha(path)==item['sha256'],'Public artifact changed '+item['path'])
 proof=read(HERE/'IDENTITY_PROOF.json');review=read(HERE/'GENESIS_REVIEW.json')
 require(sha(HERE/'IDENTITY_PROOF.json')==review['identity_proof_sha256'],'Root review does not bind proof')
 info=read(HERE/'OFFICIAL_NETWORK.json');require(len(info)==1,'Ambiguous official network')
 info=info[0]
 require(info['chain-id']==4663 and info['parent-chain-id']==1 and info['chain-config']['arbitrum']['GenesisBlockNum']==0,
  'Official identity changed')
 require(info['rollup']['rollup'].lower()==proof['official_rollup']and info['rollup']['deployed-at']==24994238,'Official rollup changed')
 l1=read(HERE/'L1_RPC.json');rows=l1['rows']
 require(len(rows)==l1['http_attempts']==9 and l1['http_denials']==2 and l1['null_receipt_results']==1,'L1 scope changed')
 phases={}
 for row in rows:phases.setdefault(row['phase'],[]).append(row)
 require({k:len(v)for k,v in phases.items()}=={'ethereum-publicnode':1,'ethereum-flashbots':5,
  'ethereum-flashbots-recheck':2,'ethereum-llama':1},'L1 phase scope changed')
 for name,phase in phases.items():
  require(phase[0]['request']['method']=='eth_chainId','Missing Ethereum handshake')
  if name in('ethereum-publicnode','ethereum-llama'):
   require(phase[0]['http_status']==403,'Denied provider retried/changed')
  else:require(result(phase[0])=='0x1','Not Ethereum mainnet')
 f=phases['ethereum-flashbots'];header=result(f[1]);events=result(f[2]);tx=result(f[3])
 require(int(header['number'],16)==24994238 and result(phases['ethereum-flashbots-recheck'][1])['hash']==header['hash'],
  'Ethereum canonical recheck differs')
 require(f[2]['request']['params']==[{'address':proof['official_rollup'],'fromBlock':header['number'],'toBlock':header['number']}],
  'Deployment event filter widened')
 before='(bytes32,bytes32,(bytes32,uint256,address,uint64,uint64))';state='((bytes32[2],uint64[2]),uint8,bytes32)'
 signature='AssertionCreated(bytes32,bytes32,('+before+','+state+','+state+'),bytes32,uint256,bytes32,uint256,address,uint64)'
 require(signature==proof['assertion_event_signature'],'ABI signature changed')
 topic=hashed(signature.encode())
 found=[e for e in events if e['topics'][0]==topic and len(e['topics'])==3 and int(e['topics'][2],16)==0]
 require(len(found)==1,'Unique initial assertion absent')
 event=found[0];words=unpack(event['data'])
 require(len(words)==25 and all(int(w,16)==0 for w in words[:13]),'Incorrect initial event layout')
 after=words[13:19];state_hash=hashed(bytes.fromhex(''.join(after)))
 commitment=hashed(bytes(32)+bytes.fromhex(state_hash[2:])+bytes(32))
 require(commitment==event['topics'][1]==proof['recomputed_assertion_hash']==proof['observed_assertion_hash'],
  'Initial assertion does not authenticate state')
 genesis='0x'+after[0]
 require(genesis==proof['genesis_block_hash']==review['genesis_pin_for_bounded_probe'],'Genesis pin differs')
 require(after==proof['after_state_words']and state_hash==proof['after_state_abi_keccak256'],'After-state proof differs')
 require(event['address'].lower()==proof['official_rollup']and event['blockHash']==header['hash']and
  int(event['blockNumber'],16)==24994238 and event.get('removed',False)is False,'Assertion inclusion differs')
 initial=[e for e in events if e['topics'][0]==hashed(b'RollupInitialized(bytes32,uint256)')]
 require(len(initial)==1 and int(unpack(initial[0]['data'])[1],16)==4663 and unpack(initial[0]['data'])[0]==words[21],
  'Rollup initialization identity differs')
 require(tx['hash']==event['transactionHash']and tx['blockHash']==header['hash']and genesis[2:]in tx['input'][2:],
  'Deployment transaction commitment differs')
 require(result(f[4])is None and proof['l1_receipt_result']is None,'Null receipt limitation changed')
 report=read(HERE/'PROFILE.json');wire=read(HERE/'PROFILE_RPC.json')['rows'];summary=read(HERE/'RESULTS.json')
 require(report['profile']==summary['full_existing_profile']=='activation_api_v1','Wrong profile')
 require(report['compatibility_checks_passed']is summary['compatibility_checks_passed']is True,'Full profile failed')
 require(report['reviewed_pins']['genesis_hash']==genesis and report['production_approved']is False,'Unreviewed/adopted profile')
 checks=report['endpoints'][0]['checks']
 expected=['genesis_identity','fresh_head','common_block_hash','canonical_hash_eth_call','canonical_hash_code',
  'canonical_hash_storage','unknown_hash_rejected','actual_call_tracer_with_log','gas_price_wei','safe_tag','finalized_tag',
  'ordinary_receipt_samples','reference_still_canonical']
 require([c['name']for c in checks]==expected and all(c['ok']is True for c in checks),'Profile checklist changed')
 require(len(wire)==report['actual_http_attempts']==summary['actual_pinax_http_attempts']==48,'Actual HTTP scope changed')
 require(len(report['endpoints'][0]['receipts'])==3 and report['configured_monotonic_spacing_seconds']==1.5,'Profile operating scope changed')
 source=read(HERE/'SOURCES.json')
 require(sha(HERE/'profile-runner.py.txt')==source['campaign_source_sha256']['run_full_probe.py']==
  '1b02160771ab4e6dbe68cd923c0b5d806f567723d56181c9f8c365551d9595f2',
  'Inert captured producer differs from actual source')
 for path,digest in source['local_source_sha256'].items():require(sha(ROOT/path)==digest,'Source drift '+path)
 require(report['probe_source_sha256']==source['local_source_sha256']['keeper/probe.py']and
  report['rpc_source_sha256']==source['local_source_sha256']['zzz_ops/rpc.py'],'Profile source mismatch')
 require(report['independent_genesis_evidence_sha256']==sha(HERE/'IDENTITY_PROOF.json')and
  report['root_genesis_review_sha256']==sha(HERE/'GENESIS_REVIEW.json'),'Profile provenance changed')
 methods={};errors=[]
 for index,row in enumerate(wire,1):
  request=row['request'];body=row['rpc_response'];method=request['method'];methods[method]=methods.get(method,0)+1
  require(row['sequence']==request['id']==body['id']==index and body['jsonrpc']=='2.0'and row['http_status']==200,
   'Actual RPC identity/envelope changed')
  require(method in('eth_chainId','eth_getBlockByNumber','eth_call','eth_getCode','eth_getStorageAt',
   'debug_traceCall','eth_gasPrice','eth_getTransactionByHash','eth_getTransactionReceipt'),'Unreviewed RPC method')
  if method=='eth_chainId':require(result(row)=='0x1237','Wrong Robinhood chain')
  if 'error'in body:errors.append(row)
 require(methods=={'eth_chainId':24,'eth_getBlockByNumber':9,'eth_call':3,'eth_getCode':1,'eth_getStorageAt':1,
  'debug_traceCall':1,'eth_gasPrice':1,'eth_getTransactionByHash':5,'eth_getTransactionReceipt':3},'Method count changed')
 require(len(errors)==1 and errors[0]['rpc_response']['error']=={'code':-32000,'message':'header not found'}and
  errors[0]['request']['params'][1]=={'blockHash':'0x'+'00'*32,'requireCanonical':True},'Missing-hash control differs')
 genesis_rows=[r for r in wire if r['request']['method']=='eth_getBlockByNumber'and r['request']['params'][0]=='0x0']
 require(len(genesis_rows)==1 and result(genesis_rows[0])['hash']==genesis,'Candidate genesis differs from independent pin')
 reference=report['reference_block']
 rechecks=[r for r in wire if r['request']['method']=='eth_getBlockByNumber'and r['request']['params'][0]==hex(reference['number'])]
 require(len(rechecks)>=3 and all(result(r)['hash']==reference['hash']for r in rechecks),'Canonical reference mismatch')
 for key in('full_20m_24m_capacity_proven','archive_uptime_recovery_qualified','provider_approved_or_adopted','full_popl_operation_fees_approved'):
  require(summary[key]is False,'Unproven release approval '+key)
 require(summary['public_transactions']==summary['signatures']==summary['service_site_anvil_journal_heartbeat_changes']==0,'Unauthorized mutation claim')
 external_count=0
 if args.external_root:
  external=args.external_root.resolve()
  for item in manifest['external_files']:
   path=(external/item['path']).resolve();require(path.is_relative_to(external)and sha(path)==item['sha256'],'External artifact changed '+item['path'])
   external_count+=1
  for row in rows+wire:
   if 'raw_relative_path'not in row:continue
   raw=(external/row['raw_relative_path']).read_bytes()
   require(hashlib.sha256(raw).hexdigest()==row['response_sha256'],'Original response hash differs')
   if 'rpc_response'in row:require(json.loads(raw)==row['rpc_response'],'Original and parsed responses differ')
  require(sha(external/'official-chain-info.raw')==sha(HERE/'OFFICIAL_NETWORK.json'),'Official metadata bytes differ')
  for relative,digest in proof['source_sha256'].items():require(sha(external/relative)==digest,'Independent source snapshot changed')
 print(json.dumps({'status':'PASS','independent_genesis_recomputed':True,'existing_profile_checks':13,
  'pinax_actual_http_attempts':48,'l1_actual_http_attempts':9,'external_files_checked':external_count,
  'new_network_calls':0,'new_evm_or_tests_or_compilers':0,'provider_or_release_approved':False}))

if __name__=='__main__':
 try:main()
 except(OSError,ValueError,KeyError,TypeError)as exc:print('ERROR: '+str(exc),file=sys.stderr);sys.exit(1)
