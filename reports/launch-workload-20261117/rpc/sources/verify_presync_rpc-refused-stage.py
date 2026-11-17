"""Two NEW local pre-sync -> same-entry workflows, never sends transactions.

Exact prestateTracer diffMode storage is used to initialize a SECOND owned node.
No old node, signing, send, impersonation, arbitrary endpoint, state override or
budget increase. This is a controlled sequential simulation, not two mined
transactions, a fee/nonce adoption or real market/intervening-block qualification.
"""
from pathlib import Path
from contextlib import contextmanager
import copy,datetime,gzip,hashlib,importlib.util,json,os,socket,subprocess,sys,time
P=Path(__file__).resolve().with_name('verify_local_rpc.py')
S=importlib.util.spec_from_file_location('launch_local_rpc_subject',P);B=importlib.util.module_from_spec(S);S.loader.exec_module(B)
ROOT=B.F/'presync-rpc';LABELS=('activation-zzz-0-pending-steady','activation-eth-0-pending-opening')
SYNC_CAP=12_000_000

@contextmanager
def node(alloc,case,folder):
 folder.mkdir(parents=True,exist_ok=False);proc=None;rpc=None;meta={'owned_node_stopped':False,'new_transactions_sent':0}
 block=case['block'];genesis={'config':{'chainId':block['chain_id'],'homesteadBlock':0,'eip150Block':0,'eip155Block':0,'eip158Block':0,'byzantiumBlock':0,'constantinopleBlock':0,'petersburgBlock':0,'istanbulBlock':0,'berlinBlock':0,'londonBlock':0,'terminalTotalDifficulty':0,'shanghaiTime':0,'cancunTime':0},'number':hex(block['number']),'nonce':'0x0','timestamp':hex(block['timestamp']),'extraData':'0x','gasLimit':hex(B.DIAGNOSTIC),'difficulty':'0x0','mixHash':'0x'+'0'*64,'coinbase':B.ZERO,'baseFeePerGas':'0x0','alloc':alloc}
 raw=json.dumps(genesis,separators=(',',':')).encode();(folder/'genesis.json').write_bytes(raw);meta['genesis_sha256']=B.sha(raw)
 try:
  assert B.sha(B.ANVIL.read_bytes())==B.ANVIL_SHA256
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  env={key:os.environ[key]for key in('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')if key in os.environ};env['PATH']=str(B.ANVIL.parent)+os.pathsep+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32')
  command=[str(B.ANVIL),'--host','127.0.0.1','--port',str(port),'--accounts','0','--silent','--init',str(folder/'genesis.json'),'--gas-limit',str(B.DIAGNOSTIC),'--chain-id',str(block['chain_id']),'--hardfork','cancun','--no-mining']
  with(folder/'anvil.log').open('xb')as log:proc=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  meta.update(owned_pid=proc.pid,command=command,anvil_sha256=B.ANVIL_SHA256);rpc=B.RPC(port)
  for _ in range(60):
   try:chain=B.quantity(rpc.call('eth_chainId'));break
   except Exception:
    if proc.poll()is not None:raise RuntimeError('Owned node exited during startup')
    time.sleep(.1)
  else:raise RuntimeError('Owned node startup deadline')
  assert chain==block['chain_id'];head=rpc.call('eth_getBlockByNumber',['latest',False]);assert B.quantity(head['number'])==block['number']and B.quantity(head['timestamp'])==block['timestamp']and B.quantity(head['gasLimit'])==B.DIAGNOSTIC
  anchor={'blockHash':head['hash'],'requireCanonical':True}
  assert rpc.call('eth_getCode',[case['sender'],anchor])=='0x'
  meta.update(block=head,local_chain_id=chain,robinhood_network_qualification=False)
  def read(address,signature,*args,count=1):
   data=B.selector(signature)+''.join(value[2:].rjust(64,'0')if isinstance(value,str)else f'{value:064x}'for value in args)
   words=B.decode_words(rpc.call('eth_call',[{'to':address,'data':data},anchor]));assert len(words)==count,(signature,'unexpected output shape');return words
  yield rpc,anchor,read,meta
  final=rpc.call('eth_getBlockByHash',[head['hash'],False]);assert all(final[key]==head[key]for key in('hash','number','timestamp','gasLimit'))
 finally:
  if proc is not None:
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
   meta['owned_node_stopped']=proc.poll()is not None
  if rpc is not None:
   with gzip.open(folder/'rpc-records.json.gz','wt',encoding='utf-8')as stream:json.dump(rpc.records,stream,separators=(',',':'))
   meta.update(rpc_requests=len(rpc.records),rpc_records_sha256=B.sha((folder/'rpc-records.json.gz').read_bytes()))
  (folder/'NODE.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')

def read_shape(read,case):
 pins=case['pins'];new_id=case['nft_id'];old_id=int(read(pins['nft'],'tokenAtOrdinal(uint256)',1)[0],16)
 assert new_id!=old_id
 words=B.decode_words('0x'+case['data'][10:]);pool='0x'+words[1];bucket=int(read(pins['vault'],'poolBucket(bytes32)',pool)[0],16)
 group=read(pins['vault'],'group(uint256)',bucket,count=8);royalty='0x'+read(pins['nft'],'royaltyRewards()')[0][-40:]
 count=int(read(royalty,'assetCount()')[0],16);assert count==17;assets=['0x'+read(royalty,'assets(uint256)',i)[0][-40:]for i in range(count)]
 assert assets[0]==B.ZERO and len(set(assets))==17
 rights={asset:{'incumbent':str(int(read(royalty,'claimable(uint256,address)',old_id,asset)[0],16)),'newcomer':str(int(read(royalty,'claimable(uint256,address)',new_id,asset)[0],16))}for asset in assets}
 assert all(row=={'incumbent':'1601','newcomer':'0'}for row in rights.values())
 fixed='0x'+read(pins['activation_assets'],'zzz()')[0][-40:];protected={'bucket':str(bucket),'group':group,'minted_count':read(pins['nft'],'mintedCount()'),'activation_count':read(royalty,'activationCount()'),'activation_weight':read(royalty,'totalWeight()')}
 for label,identifier in(('incumbent',old_id),('newcomer',new_id)):
  protected[label]={'id':str(identifier),'owner':read(pins['nft'],'ownerOf(uint256)',identifier),'shares':read(pins['vault'],'sharesOf(uint256)',identifier),'royalty_weight':read(royalty,'weightOf(uint256)',identifier)}
 for asset in(B.ZERO,fixed):
  protected[asset]={'compound':read(pins['fees'],'compoundBalance(uint256,address)',bucket,asset),'buyback':read(pins['fees'],'buybackBalance(address)',asset),'fee_accounted':read(pins['fees'],'accounted(address)',asset),'lp_liability':read(pins['rewards'],'liabilities(address)',asset)}
 return {'royalty':royalty,'assets':assets,'rights':rights,'protected':protected,'source_old_id':str(old_id)}

def value(number):
 assert type(number)is int and number>=0 or type(number)is str and number.startswith('0x')
 return number if type(number)is int else int(number,16)

def word(raw):
 assert type(raw)is str and raw.startswith('0x')and 0<=int(raw,16)<1<<256
 return'0x'+f'{int(raw,16):064x}'

def apply_diff(alloc,diff,royalty):
 assert type(diff)is dict and set(diff)=={'pre','post'}and type(diff['pre'])is dict and type(diff['post'])is dict,'Unsupported prestateTracer diff result'
 after=copy.deepcopy(alloc);changed=[];cleared=[]
 assert set(diff['pre'])<=set(diff['post']),'syncAll cannot delete an account'
 for address in set(diff['pre'])|set(diff['post']):
  assert address==address.lower();before=after.get(address,{'balance':'0x0','nonce':'0x0','code':'0x','storage':{}});pre=diff['pre'].get(address,{});post=diff['post'].get(address,{})
  assert set(pre)<=set(('balance','nonce','code','storage'))and set(post)<=set(('balance','nonce','code','storage')),'Unknown state-diff account fields'
  for field in('balance','nonce','code'):
   if field in pre:assert (pre[field]==before.get(field,'0x')if field=='code'else value(pre[field])==value(before.get(field,'0x0'))),'State-diff pre-account mismatch'
   if field in post:
    assert(post[field]==before.get(field,'0x')if field=='code'else value(post[field])==value(before.get(field,'0x0'))),'syncAll unexpectedly changes code/balance/nonce'
  storage={word(k):word(v)for k,v in before.get('storage',{}).items()};pre_slots={word(k):word(v)for k,v in pre.get('storage',{}).items()};post_slots={word(k):word(v)for k,v in post.get('storage',{}).items()}
  for slot,raw in pre_slots.items():assert storage.get(slot,word('0x0'))==raw,'State-diff pre-storage mismatch'
  for slot in set(pre_slots)|set(post_slots):
   new=post_slots.get(slot,word('0x0'));old=storage.get(slot,word('0x0'))
   if old!=new:
    assert address==royalty,'syncAll unexpectedly mutates non-royalty storage'
    changed.append({'account':address,'slot':slot,'before':old,'after':new})
    if int(old,16)!=0 and int(new,16)==0:cleared.append(slot)
   storage[slot]=new
  after[address]={**before,'storage':storage}
 assert changed,'No actual royalty-storage transition was captured'
 return after,{'changed_storage_slots':len(changed),'cleared_storage_slots':len(cleared),'changed_accounts':sorted({row['account']for row in changed}),'changes':changed,'geth_diff_semantics':'https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers#prestatetracer','no_nonroyalty_storage_or_code_balance_nonce_change':True}

def workflow(case):
 folder=ROOT/case['label'];folder.mkdir(parents=True,exist_ok=False);result={'schema':1,'label':case['label'],'verification_complete':False,'sync12m_full20pct':False,'entry20m_full20pct':False,'production_approved':False,'new_transactions_sent':0,'new_workflow_only':True,'scope':'Optional separate public syncAll then SAME activation calldata, reconstructed from actual prestateTracer diff on two NEW isolated nodes at the same exported timestamp. Not two mined transactions, nonce/fee/market adoption, automatic worker or a required extra holder transaction.'}
 try:
  alloc,omitted,merge=B.source_state(case);result['source_state_merge']=merge;post_alloc=None;before_shape=None
  with node(alloc,case,folder/'before-sync')as(rpc,anchor,read,meta):
   result['before_node']=meta;before_shape=read_shape(read,case);royalty=before_shape['royalty'];tx={'from':case['sender'],'to':royalty,'value':'0x0','data':B.selector('syncAll()'),'gas':hex(SYNC_CAP)}
   call=rpc.attempt('eth_call',[tx,anchor]);estimate_reply=rpc.attempt('eth_estimateGas',[tx,anchor]);estimate=B.quantity(estimate_reply['result'])if estimate_reply['ok']else None;padded=(estimate*120+99)//100 if estimate is not None else None;exact=None
   if call['ok']and estimate is not None and 21000<=estimate<=padded<=SYNC_CAP:exact=rpc.attempt('eth_call',[{**tx,'gas':hex(padded)},anchor])
   trace=B.checked_trace(rpc,tx,anchor,omitted)
   result['sync']={'cap':SYNC_CAP,'call':call,'estimate':estimate_reply,'raw_estimate':estimate,'full20pct_padded':padded,'exact_padded_call':exact,'trace_success':trace['ok']and not trace['result'].get('error')}
   admitted=bool(call['ok']and call['result']=='0x'and exact and exact['ok']and exact['result']=='0x'and trace['ok']and not trace['result'].get('error'))
   result['sync12m_full20pct']=admitted
   if not admitted:result['specific_limit']='Separate syncAll did not fit12M with full20%; no larger fallback attempted.'
   else:
    transition=rpc.attempt('debug_traceCall',[tx,anchor,{'tracer':'prestateTracer','tracerConfig':{'diffMode':True},'timeout':'45s'}]);result['prestate_tracer_supported']=transition['ok']
    if not transition['ok']:result['specific_limit']='Owned client refuses prestateTracer diffMode; no poststate guessed.';result['tracer_error']=transition['error']
    else:
     diff=transition['result'];post_alloc,changed=apply_diff(alloc,diff,royalty);result['state_transition']=changed;result['sync']['trace_gas_used']=B.quantity(trace['result']['gasUsed'])
     diffraw=json.dumps(diff,separators=(',',':')).encode();(folder/'sync-state-diff.json').write_bytes(diffraw);result['state_diff_sha256']=B.sha(diffraw)
  if post_alloc is not None:
   with node(post_alloc,case,folder/'after-sync')as(rpc,anchor,read,meta):
    result['after_node']=meta;after_shape=read_shape(read,case);assert before_shape==after_shape,'Pre-sync must preserve all old/new NFT rights, LP and reserves';result['before_after_shape']=before_shape
    tx={'from':case['sender'],'to':case['destination'],'value':hex(case['value']),'data':case['data'],'gas':hex(B.CAP)};call=rpc.attempt('eth_call',[tx,anchor]);estimated=rpc.attempt('eth_estimateGas',[tx,anchor]);estimate=B.quantity(estimated['result'])if estimated['ok']else None;padded=(estimate*120+99)//100 if estimate is not None else None;exact=None
    if call['ok']and estimate is not None and 21000<=estimate<=padded<=B.CAP:exact=rpc.attempt('eth_call',[{**tx,'gas':hex(padded)},anchor])
    trace=B.checked_trace(rpc,tx,anchor,omitted);passed=bool(call['ok']and call['result']=='0x'and exact and exact['ok']and exact['result']=='0x'and trace['ok']and not trace['result'].get('error'));result['entry20m_full20pct']=passed
    result['entry']={'cap':B.CAP,'same_original_calldata_sha256':B.sha(bytes.fromhex(case['data'][2:])),'same_original_value':case['value'],'same_exported_timestamp':case['block']['timestamp'],'call':call,'estimate':estimated,'raw_estimate':estimate,'full20pct_padded':padded,'exact_padded_call':exact,'trace_success':trace['ok']and not trace['result'].get('error'),'scope':'No32M fallback for this post-sync profile review.'}
    if trace['ok']and not trace['result'].get('error'):
     result['entry']['trace_gas_used']=B.quantity(trace['result']['gasUsed']);result['production_measurement']=B.measure_trace(trace['result'],tx,case,read)
   result['rights_and_principal_preserved_across_sync']=True
  result['verification_complete']=True
 except Exception as error:result['verification_error']=type(error).__name__+': '+str(error)
 finally:
  result['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['verifier_source_sha256']=B.sha(Path(__file__).read_bytes());result['base_verifier_source_sha256']=B.sha(P.read_bytes())
  (folder/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 return result

def main():
 assert not sys.argv[1:],'No arbitrary path or endpoint input is accepted'
 _,summary=B.load(B.OUT/'SUMMARY.json');assert summary['source_forge_sha256']==B.RAW_SHA256;selected=[row['profile']for row in summary['results']if row['profile']['label']in LABELS];assert {row['label']for row in selected}==set(LABELS)
 ROOT.mkdir(parents=True,exist_ok=False);results=[]
 for case in selected:
  assert case['label']in LABELS and '-0-pending-'in case['label'];result=workflow(case);results.append(result);print(json.dumps({'case':case['label'],'verification_complete':result['verification_complete'],'sync12m_full20pct':result['sync12m_full20pct'],'entry20m_full20pct':result['entry20m_full20pct'],'verification_error':result.get('verification_error'),'specific_limit':result.get('specific_limit')}),flush=True)
  if not result['verification_complete']:break
 output={'schema':1,'scope':'Two NEW optional pre-sync sequential simulation workflows only. Original9 profiles unchanged; all limits/defaults preserved.','source_forge_sha256':B.RAW_SHA256,'results':results,'all_workflows_evaluated':len(results)==2 and all(row['verification_complete']for row in results),'production_approved':False,'geth_prestate_diff_reference':'https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers#prestatetracer'}
 (ROOT/'SUMMARY.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8');return 0 if output['all_workflows_evaluated']else 1

if __name__=='__main__':raise SystemExit(main())
