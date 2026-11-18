# Derived from the historical fixed launch verifier, SHA256: f7d1ee4de3fda6da50b336ab2d53d359f86be7d77e2af4adf40bde32ef138b70
# Changed producer identity/population/shared-bucket semantics are explicit;
# historical input pins and results remain unchanged.
"""Verify NEW closed Q03 near-capacity exports on owned loopback Anvil using read-only RPC.

Fixed source/export paths only. No key, unlocked account, send, impersonation,
public RPC, fork, existing node, service or default-budget adoption. A completed
verification can explicitly FAIL the20M profile.32M is diagnostic execution only.
Only a source-pinned owned producer stage is accepted; no endpoint/key input.
"""
from pathlib import Path
import copy,datetime,gzip,hashlib,json,os,re,socket,subprocess,sys,time,urllib.request

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256,decode_words
from frontend_api.activation_trace import selector,measure,SHARES,EXECUTE_DIRECT_V3
from zzz_ops.execution_price import observe
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
E=V/'q03-activation-gas-20261117'
assert len(sys.argv)==2 and re.fullmatch(r'[a-z0-9-]+',sys.argv[1]),'Use one owned producer stage'
STAGE=sys.argv[1];F=E/STAGE;EXPORTS=F/'exports';OUT=F/'local-rpc'
PRODUCER=json.loads((F/'PRODUCER.json').read_bytes());assert PRODUCER['schema']==1
EXPECTED_METHOD='test/Q03ActivationCapacity20261117.t.sol:Q03ActivationCapacity20261117Test:testQ03FullEntry999ActualMixedNFTsSixteenCurrencyCapacity()'
EXPECTED_SOURCE_SHA256='1806c0404caeafe30b7568901cac7a60711b4f466d0729763d4e199dbfa48460'
EXPECTED_METHODS=[EXPECTED_METHOD,'test/Q03ActivationCapacity20261117.t.sol:Q03ActivationCapacity20261117Test:testQ03PreSynchronized999HealthyFaultAndZZZGrowth()']
EXPECTED_CASES={'q03-999-opening-eth','q03-999-rotated-zzz','q03-999-rotated-onefault-eth','q03-999-rotated-eth','q03-1000-grow-eth','q03-999-presynced-eth','q03-1000-presynced-grow-zzz','q03-999-presynced-onefault-eth'}
assert sorted(PRODUCER['method_ids'])==sorted(EXPECTED_METHODS)and set(PRODUCER['case_labels'])==EXPECTED_CASES
assert hashlib.sha256((F/'SOURCE_TEST.sol.txt').read_bytes()).hexdigest()==EXPECTED_SOURCE_SHA256
ANVIL=V/'foundry-v1.4.4/anvil.exe';ANVIL_SHA256='d438383b871c726407ecc5829279bea44ceac63a712be9e010813ca0a15434b6'
ARTIFACT=F/'producer-artifact.json'
RAW_SHA256=PRODUCER['raw_sha256'];START_SHA256=PRODUCER['start_sha256'];ARTIFACT_SHA256=PRODUCER['artifact_sha256']
ZERO='0x'+'0'*40;CAP=20_000_000;DIAGNOSTIC=32_000_000;MAX_FILE=256*1024*1024;MAX_REPLY=64*1024*1024
ROLES=('entry','vault','budget','contribution_pricing','oracle','liquidity','lp_position_executor','position_manager','fees','protocol_policy','pools','nft','rewards','membership','principal_exit','pool_manager','state_view','balancing_router','reference','independent_reference','independent_core','independent_state','activation_assets','vrf')
ALLOWED=frozenset(('eth_chainId','eth_getBlockByNumber','eth_getBlockByHash','eth_getCode','eth_getBalance','eth_call','eth_estimateGas','eth_gasPrice','debug_traceCall'))
sha=lambda raw:hashlib.sha256(raw).hexdigest()
topic=lambda signature:'0x'+keccak256(signature.encode()).hex()
EVENTS={topic(signature):name for name,signature in (
 ('bindings','ReferenceExecutionBindings(address[],bytes32[])'),
 ('call','ProfileUnsignedCall(string,address,address,uint256,bytes,uint256,uint16,uint256,uint256,bytes32)'),
 ('baseline','ReferenceExportBaseline(string,bytes32)'),('block','ReferenceExportBlock(uint256,uint256,uint256)'),
 ('code','ReferenceExportCodeMaterialized(address,bytes32,uint256)'),('state','ProfileStateExport(string,string,bytes32)'))}

def load(path):
 with Path(path).open('rb')as stream:raw=stream.read(MAX_FILE+1)
 assert len(raw)<=MAX_FILE,'Input file bound exceeded'
 return raw,json.loads(raw)

def quantity(value):
 assert type(value)is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)',value),'Invalid RPC quantity'
 return int(value,16)

def code_bytes(value):
 assert type(value)is str and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',value),'Invalid code bytes'
 return bytes.fromhex(value[2:])

def dyn(words,index,text=True):
 offset=int(words[index],16);assert offset%32==0 and offset//32<len(words)
 start=offset//32;length=int(words[start],16);raw=bytes.fromhex(''.join(words[start+1:]));assert length<=len(raw)
 return raw[:length].decode('utf-8')if text else '0x'+raw[:length].hex()

def parse_logs(logs):
 materialized={};bindings=None;current=None;cases=[]
 for log in logs:
  topics=log.get('topics',[])
  if not topics or topics[0]not in EVENTS:continue
  kind=EVENTS[topics[0]];words=decode_words(log['data'])
  if kind=='bindings':
   assert current is None
   a,h=(int(words[i],16)//32 for i in(0,1));assert int(words[a],16)==int(words[h],16)==len(ROLES)
   pins={role:'0x'+words[a+1+i][-40:]for i,role in enumerate(ROLES)}
   hashes={role:'0x'+words[h+1+i]for i,role in enumerate(ROLES)}
   assert len(set(pins.values()))==len(ROLES)and ZERO not in pins.values()
   bindings=(pins,hashes)
  elif kind=='code':
   assert len(topics)==2 and len(words)==2
   address='0x'+topics[1][-40:];pin={'hash':'0x'+words[0],'length':int(words[1],16)}
   materialized[address]=pin
   if current is not None:
    assert address not in current['materialized']or current['materialized'][address]==pin,'Conflicting within-case runtime'
    current['materialized'][address]=pin
  elif kind=='call':
   assert bindings is not None and current is None
   label=dyn(words,0);assert re.fullmatch(r'[a-z0-9-]{1,120}',label)
   current={'label':label,'sender':'0x'+words[1][-40:],'destination':'0x'+words[2][-40:],'value':int(words[3],16),
    'data':dyn(words,4,False),'cap':int(words[5],16),'padding_bps':int(words[6],16),'nft_id':int(words[7],16),
    'shared_bucket':int(words[8],16),'pre_state':'0x'+words[9],'harness':log['address'].lower(),
    'pins':copy.deepcopy(bindings[0]),'runtime_hashes':copy.deepcopy(bindings[1]),'materialized':copy.deepcopy(materialized)}
   assert current['cap']==CAP and current['padding_bps']==2000
  elif current is not None and kind=='baseline':current.update(baseline_path=dyn(words,0),baseline_hash='0x'+words[1])
  elif current is not None and kind=='block':current['block']={'number':int(words[0],16),'timestamp':int(words[1],16),'chain_id':int(words[2],16)}
  elif current is not None and kind=='state':
   assert current['label']==dyn(words,0)
   current.update(delta_path=dyn(words,1),delta_hash='0x'+words[2]);assert all(k in current for k in('block','baseline_path','baseline_hash'))
   assert current['block']['chain_id']in(31337,4663);cases.append(current);current=None
 assert current is None,'Incomplete exported case'
 return cases

def exports():
 raw,parsed=load(F/'raw.json');start_raw,started=load(F/'START.json');assert sha(raw)==RAW_SHA256 and sha(start_raw)==START_SHA256,'Selected producer input pin changed';methods=[];by_label={}
 for host,body in parsed.items():
  for name,test in body.get('test_results',{}).items():
   assert test['status']=='Success','Export producer method did not pass'
   methods.append(host+':'+name)
   for case in parse_logs(test.get('logs',[])):
    method=host+':'+name
    if case['label']in by_label:
     old=by_label[case['label']];assert {k:v for k,v in old.items()if k!='source_methods'}==case,'Conflicting duplicate export label'
     old['source_methods'].append(method)
    else:case['source_methods']=[method];by_label[case['label']]=case
 assert methods and by_label,'No successful actual export cases'
 source=started.get('source_before',{});assert sum(n.startswith('src/')for n in source)==61;assert methods==PRODUCER['method_ids'];assert set(by_label)==set(PRODUCER['case_labels'])
 for name,pin in source.items():
  if name.startswith('src/'):assert sha((R/name).read_bytes())==pin,'Production source changed since export start'
 return list(by_label.values()),sha(raw),source,methods

def merge_alloc(baseline,delta):
 alloc=copy.deepcopy(baseline);zeroes=0
 for address,row in delta.items():
  old=alloc.get(address,{})
  if old.get('code')and row.get('code'):assert old['code']==row['code'],'Runtime changed across exported baseline/delta'
  prior=old.get('storage',{});now=row.get('storage',{})
  zeroes+=sum(int(v,16)==0 and int(prior.get(k,'0x0'),16)!=0 for k,v in now.items())
  alloc[address]={**old,**row,'storage':{**prior,**now}}
 return alloc,zeroes

def source_state(case):
 paths=[Path(case[key]).resolve()for key in('baseline_path','delta_path')]
 assert all(path.is_relative_to(EXPORTS.resolve())for path in paths),'Only the NEW fixed export folder is accepted'
 base_raw,base=load(paths[0]);delta_raw,delta=load(paths[1])
 assert '0x'+keccak256(base_raw).hex()==case['baseline_hash'],'Baseline export hash mismatch'
 assert '0x'+keccak256(delta_raw).hex()==case['delta_hash'],'Delta export hash mismatch'
 alloc,zeroes=merge_alloc(base,delta);artifact_raw,artifact=load(ARTIFACT);assert sha(artifact_raw)==ARTIFACT_SHA256,'Selected producer artifact changed'
 assert artifact['metadata']['settings']['compilationTarget']=={'test/Q03ActivationCapacity20261117.t.sol':'Q03ActivationCapacity20261117Test'}
 assert artifact['metadata']['sources']['test/Q03ActivationCapacity20261117.t.sol']['keccak256']=='0x'+keccak256((F/'SOURCE_TEST.sol.txt').read_bytes()).hex(),'Compiled fixture differs from exact approved source'
 runtime=artifact['deployedBytecode']['object'];runtime=runtime if runtime.startswith('0x')else '0x'+runtime
 harness_pin={'hash':'0x'+keccak256(code_bytes(runtime)).hex(),'length':len(code_bytes(runtime))}
 omitted={}
 for address,pin in case['materialized'].items():
  if address==case['harness']:
   assert pin==harness_pin,'Harness runtime differs from compiled producer'
   if address in alloc:assert '0x'+keccak256(code_bytes(alloc[address].get('code','0x'))).hex()==pin['hash'];del alloc[address]
   omitted[address]=pin
  else:
   assert address in alloc,'Materialized account missing from authenticated complete allocation'
   code=code_bytes(alloc[address].get('code','0x'));assert len(code)==pin['length']and'0x'+keccak256(code).hex()==pin['hash'],'Materialized runtime mismatch'
 assert set(omitted)=={case['harness']},'Exactly the compiled test harness may be omitted'
 for role,address in case['pins'].items():assert '0x'+keccak256(code_bytes(alloc[address]['code'])).hex()==case['runtime_hashes'][role],role
 return alloc,omitted,{'baseline_sha256':sha(base_raw),'delta_sha256':sha(delta_raw),'baseline_keccak256':case['baseline_hash'],'delta_keccak256':case['delta_hash'],'nonzero_to_zero_overrides':zeroes,'baseline_accounts':len(base),'delta_accounts':len(delta),'merged_accounts':len(alloc),'harness_artifact_sha256':sha(artifact_raw)}

class RPCFailure(Exception):
 def __init__(self,method,error):self.method=method;self.error=error;super().__init__('Owned local RPC refusal: '+method)

class RPC:
 def __init__(self,port):
  self.port=port;self.records=[];self.start=time.monotonic();self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 def call(self,method,params=None):
  assert method in ALLOWED,'Non-read-only RPC denied'
  assert len(self.records)<256 and time.monotonic()-self.start<600,'Bounded owned RPC review exhausted'
  request={'jsonrpc':'2.0','id':len(self.records)+1,'method':method,'params':params or []};raw=json.dumps(request,separators=(',',':')).encode();record={'request':request,'serialized_request_sha256':sha(raw)}
  self.records.append(record)
  try:
   with self.opener.open(urllib.request.Request('http://127.0.0.1:'+str(self.port),raw,{'Content-Type':'application/json'}),timeout=60)as response:body=response.read(MAX_REPLY+1)
   assert len(body)<=MAX_REPLY,'Reply size bound exceeded';value=json.loads(body);record.update(response=value,serialized_response_sha256=sha(body))
  except Exception as error:record['transport_exception']=type(error).__name__;raise
  assert value.get('id')==request['id']and value.get('jsonrpc')=='2.0','RPC response identity differs'
  if 'error'in value:raise RPCFailure(method,value['error'])
  assert 'result'in value;return value['result']
 def attempt(self,method,params):
  try:return {'ok':True,'result':self.call(method,params)}
  except RPCFailure as error:return {'ok':False,'error':error.error}

def frames(trace):
 todo=[trace];count=0
 while todo:
  frame=todo.pop();count+=1;assert isinstance(frame,dict)and count<=16384,'Trace shape/work bound'
  yield frame;children=frame.get('calls',[]);assert isinstance(children,list);todo.extend(children)

def checked_trace(rpc,tx,block,omitted):
 reply=rpc.attempt('debug_traceCall',[tx,block,{'tracer':'callTracer','tracerConfig':{'withLog':True},'timeout':'45s'}])
 if not reply['ok']:return reply
 root=reply['result'];assert root['from'].lower()==tx['from']and root['to'].lower()==tx['to'],'Trace sender/target mismatch'
 assert not any(frame.get('to','').lower()in omitted for frame in frames(root)),'Production simulation called omitted harness'
 return reply

def measure_trace(trace,tx,case,read,*,captured_shared=None):
 pins=copy.deepcopy(case['pins']);words=decode_words('0x'+case['data'][10:]);assert case['data'].startswith(selector(EXECUTE_DIRECT_V3))and len(words)==9
 nft_id=int(words[0],16);pool='0x'+words[1];source='0x'+words[2][-40:];amount=int(words[3],16);minimum=int(words[4],16);deadline=int(words[5],16);growth=int(words[6],16);maximum=int(words[7],16);policy='0x'+words[8]
 assert nft_id==case['nft_id']and maximum==300 and growth in(0,1)
 assert int(read(pins['nft'],'ownerOf(uint256)',nft_id)[0],16)==int(case['sender'],16)
 old_bucket=int(read(pins['vault'],'nftBucket(uint256)',nft_id)[0],16);assert old_bucket==(case['shared_bucket']if growth else 0)
 # A dormant entrant has nftBucket0 while the pool can already have an
 # incumbent main. Its placement context is the shared pool, not group0.
 if captured_shared is None:
  shared_bucket=int(read(pins['vault'],'poolBucket(bytes32)',pool)[0],16)
  shared_words=read(pins['vault'],'group(uint256)',shared_bucket,count=8)
 else:shared_bucket,shared_words=captured_shared
 assert shared_bucket==case['shared_bucket'];old_lp=int(shared_words[1],16)
 zzz='0x'+read(pins['activation_assets'],'zzz()')[0][-40:]
 pins['lp_balance_math']='0x'+read(pins['liquidity'],'executionStrategy()')[0][-40:];pins['access']='0x'+read(pins['liquidity'],'access()')[0][-40:]
 pins['strategy']='0x'+read(pins['access'],'module(bytes32)','0x'+keccak256(b'ZZZStrategy').hex())[0][-40:];context=observe(read,pins);assert not context['context_active']
 bounds={}
 for asset in(ZERO,zzz):
  values=read(pins['oracle'],'priceBounds(address)',asset,count=3);bounds[asset]={'lower':int(values[0],16),'upper':int(values[1],16),'fingerprint':'0x'+values[2]}
 digits=int(read(pins['oracle'],'tokenDecimals(address)',source)[0],16);gross=amount*bounds[source]['lower']//10**digits;upper=(amount*bounds[source]['upper']+10**digits-1)//10**digits
 config=[int(value,16)for value in read(pins['pools'],'get(bytes32)',pool,count=14)];idle=int(read(pins['protocol_policy'],'entryPolicy()',count=4)[2],16)
 shares=[log for frame in frames(trace)for log in frame.get('logs',[])if log['address'].lower()==pins['vault']and log['topics'][0]==SHARES];assert len(shares)==1;bucket=int(shares[0]['topics'][2],16);assert shared_bucket in(0,bucket)
 request={'id':nft_id,'pool':pool,'source':source,'amount':amount,'minimum_lp':minimum,'deadline':deadline,'increase':bool(growth),'maximum_loss_bps':maximum,'expected_contribution_policy':policy,'bucket':bucket,'old_lp_id':old_lp,'output':source,'token0':ZERO,'token1':zzz,'route':'0x'+'0'*64,'minimum_out':0,'route_kind':0,'accounting_version':7,'routing_version':3,'review_policy_version':2,'pricing_version':2,'lp_routing_version':3,'execution_price_version':1,'portfolio_version':2,'execution_quality_version':1,'execution_loss_bps':300,'maximum_idle_bps':idle,'upper_input_usd':upper,'reviewed_price_bounds':bounds}
 return {'measurement':measure(trace,tx,pins,request,gross,config[10]),'request':request,'gross_usd18':gross,'context':context,'controlled_pool_minimum_usd18':config[12]}

def execute(case,forge_hash,source):
 folder=OUT/case['label'];folder.mkdir(parents=True,exist_ok=False);proc=None;rpc=None
 outcome={'schema':1,'profile':case,'source_forge_sha256':forge_hash,'source_start_sha256':START_SHA256,'source_harness_artifact_sha256':ARTIFACT_SHA256,'source_pre_state_hash_scope':'Harness-defined entry atomic-state fingerprint, not a commitment to all exported VM state; raw baseline/delta have their own authenticated hashes.','verification_complete':False,'meets_reviewed_execution_profile':False,'production_approved':False,'public_transactions':0,'owned_node_stopped':False,'scope':'NEW isolated loopback chain, captured controlled near1000 mint2 state, actual v4/financial code with controlled authority, admission, feeds, VRF and Permit2.Only exported31337/4663 local chain IDs are allowed, neither proves Robinhood network behavior.20M failure is retained.32M is diagnostic only; no service/default adoption or real market/provider/fee qualification.'}
 try:
  assert sha(ANVIL.read_bytes())==ANVIL_SHA256,'Pinned Anvil binary changed'
  for name,pin in source.items():
   if name.startswith('src/'):assert sha((R/name).read_bytes())==pin,'Production source changed before verification'
  alloc,omitted,merge=source_state(case);outcome.update(state_merge=merge,omitted_harness=omitted,anvil_sha256=ANVIL_SHA256)
  block=case['block'];genesis={'config':{'chainId':block['chain_id'],'homesteadBlock':0,'eip150Block':0,'eip155Block':0,'eip158Block':0,'byzantiumBlock':0,'constantinopleBlock':0,'petersburgBlock':0,'istanbulBlock':0,'berlinBlock':0,'londonBlock':0,'terminalTotalDifficulty':0,'shanghaiTime':0,'cancunTime':0},'number':hex(block['number']),'nonce':'0x0','timestamp':hex(block['timestamp']),'extraData':'0x','gasLimit':hex(DIAGNOSTIC),'difficulty':'0x0','mixHash':'0x'+'0'*64,'coinbase':ZERO,'baseFeePerGas':'0x0','alloc':alloc}
  (folder/'genesis.json').write_text(json.dumps(genesis,separators=(',',':')),encoding='utf-8')
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  env={key:os.environ[key]for key in('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')if key in os.environ};env['PATH']=str(ANVIL.parent)+os.pathsep+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32')
  cmd=[str(ANVIL),'--host','127.0.0.1','--port',str(port),'--accounts','0','--silent','--init',str(folder/'genesis.json'),'--gas-limit',str(DIAGNOSTIC),'--chain-id',str(block['chain_id']),'--hardfork','cancun','--no-mining']
  with(folder/'anvil.log').open('xb')as log:proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  outcome.update(owned_pid=proc.pid,owned_command=cmd,node_environment='Allowlisted OS variables only; no wallet/RPC settings. No proxy inheritance.')
  rpc=RPC(port)
  for _ in range(60):
   try:chain=quantity(rpc.call('eth_chainId'));break
   except(Exception):
    if proc.poll()is not None:raise RuntimeError('Owned node exited during startup')
    time.sleep(.1)
  else:raise RuntimeError('Owned node startup bound exceeded')
  assert chain==block['chain_id'];outcome.update(local_chain_id=chain,robinhood_network_qualification=False);head=rpc.call('eth_getBlockByNumber',['latest',False]);assert quantity(head['number'])==block['number']and quantity(head['timestamp'])==block['timestamp']and quantity(head['gasLimit'])==DIAGNOSTIC
  anchor={'blockHash':head['hash'],'requireCanonical':True};outcome['confirmed_block']=head
  assert rpc.call('eth_getCode',[case['sender'],anchor])=='0x','Actual outer sender must be empty-code EOA'
  for address,pin in case['materialized'].items():
   if address not in omitted:assert'0x'+keccak256(code_bytes(rpc.call('eth_getCode',[address,anchor]))).hex()==pin['hash'],'Materialized runtime not installed'
  def read(address,signature,*args,count=1):
   data=selector(signature)+''.join(value[2:].rjust(64,'0')if isinstance(value,str)else f'{value:064x}'for value in args)
   words=decode_words(rpc.call('eth_call',[{'to':address,'data':data},anchor]));assert len(words)==count,(signature,'unexpected output size');return words
  pins=case['pins'];royalty='0x'+read(pins['nft'],'royaltyRewards()')[0][-40:];helper='0x'+read(pins['nft'],'seaDropMint()')[0][-40:];drop='0x'+read(helper,'seaDrop()')[0][-40:]
  assert int(read(royalty,'assetCount()')[0],16)==17
  assets=['0x'+read(royalty,'assets(uint256)',i)[0][-40:]for i in range(17)];assert assets[0]==ZERO and len(set(assets))==17
  assert int(read(royalty,'assetCapacity()')[0],16)==16 and int(read(pins['protocol_policy'],'royaltySyncGas()')[0],16)==1_000_000
  assert helper!=ZERO and drop!=ZERO and int(read(helper,'nft()')[0],16)==int(pins['nft'],16)
  assert all(address in case['materialized']for address in assets[1:]+[helper,drop,royalty]),'New currency/helper code was not independently materialized'
  assert int(read(pins['oracle'],'executionActive()')[0],16)==0
  count=int(read(royalty,'activationCount()')[0],16);weight=int(read(royalty,'totalWeight()')[0],16)
  minted=int(read(pins['nft'],'mintedCount()')[0],16);eligible=int(read(pins['membership'],'totalEligible()')[0],16)
  growth=bool(int(decode_words('0x'+case['data'][10:])[6],16));expected=1000 if growth else 999
  assert minted==1000 and count==eligible==expected and weight==(1500 if growth else 1499),'Full population differs'
  outcome['population']={'minted':minted,'royalty_active':count,'membership_active':eligible,'royalty_weight':weight,'source_setup':'999 actual prior Entries in captured producer; no typed/raw accounting seeds'}
  outcome['workload']={'royalty_erc20_currencies':16,'royalty_assets_total':17,'royalty_asset_capacity':16,'royalty_assets':assets,'royalty_sync_gas':1_000_000,'royalty_ledger':royalty,'mint_helper':helper,'seadrop':drop,'actual_empty_code_sender':case['sender']}
  tx={'from':case['sender'],'to':case['destination'],'value':hex(case['value']),'data':case['data'],'gas':hex(CAP)}
  call20=rpc.attempt('eth_call',[tx,anchor]);estimate20=rpc.attempt('eth_estimateGas',[tx,anchor]);trace20=checked_trace(rpc,tx,anchor,omitted)
  estimate=quantity(estimate20['result'])if estimate20['ok']else None;padded=(estimate*120+99)//100 if estimate is not None else None
  exact=None
  if call20['ok']:assert call20['result']=='0x'
  if call20['ok']and estimate is not None and 21000<=estimate<=padded<=CAP:exact=rpc.attempt('eth_call',[{**tx,'gas':hex(padded)},anchor])
  if exact is not None and exact['ok']:assert exact['result']=='0x'
  trace20_ok=trace20['ok']and not trace20['result'].get('error')
  admitted=bool(call20['ok']and estimate is not None and 21000<=estimate<=padded<=CAP and exact and exact['ok']and trace20_ok)
  outcome.update(actual_20m_call=call20,estimate_20m=estimate20,estimated_gas=estimate,padded_gas=padded,exact_padded_call=exact,trace20_succeeded=trace20_ok,meets_reviewed_execution_profile=admitted)
  trace=trace20['result']if trace20_ok else None;trace_tx=tx
  if not admitted:
   tx32={**tx,'gas':hex(DIAGNOSTIC)};diagnostic=rpc.attempt('eth_call',[tx32,anchor]);trace32=checked_trace(rpc,tx32,anchor,omitted)
   outcome['diagnostic32']={'execution_only_no_adoption':True,'cap':DIAGNOSTIC,'call':diagnostic,'trace_succeeded':trace32['ok']and not trace32['result'].get('error')}
   if diagnostic['ok']:assert diagnostic['result']=='0x'
   if trace32['ok']and not trace32['result'].get('error'):trace=trace32['result'];trace_tx=tx32
  price=quantity(rpc.call('eth_gasPrice'));balance=quantity(rpc.call('eth_getBalance',[case['sender'],anchor]));outcome.update(local_gas_price_wei=price,sender_balance_wei=balance,fee_qualification='Local execution-only gas price; complete target L1/L2/network fees remain unqualified.')
  if admitted:assert balance>=case['value']+padded*price,'Sender cannot fund reviewed envelope'
  if trace is not None:
   outcome.update(trace_gas_used=quantity(trace['gasUsed']),measurement_scope='20M actual call'if trace_tx['gas']==hex(CAP)else'32M diagnostic call only')
   try:outcome['production_trace_measurement']=measure_trace(trace,trace_tx,case,read);outcome['production_trace_measurement_verified']=True
   except Exception as error:outcome.update(production_trace_measurement_verified=False,measurement_error=type(error).__name__+': '+str(error))
  final=rpc.call('eth_getBlockByHash',[head['hash'],False]);assert final['hash']==head['hash']and final['number']==head['number']and final['timestamp']==head['timestamp']and quantity(final['gasLimit'])==DIAGNOSTIC
  # Financial trace verification is required for profile admission too.
  # A completed RPC sequence alone must never certify an unmeasured entry.
  financial=outcome.get('production_trace_measurement_verified') is True
  outcome['meets_reviewed_execution_profile']=admitted and financial
  assert financial,'Complete financial trace measurement unavailable'
  outcome['verification_complete']=True
 except Exception as error:outcome.update(verification_error=type(error).__name__+': '+str(error),verification_complete=False,meets_reviewed_execution_profile=False)
 finally:
  if proc is not None:
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
   outcome['owned_node_stopped']=proc.poll()is not None
  outcome['rpc_requests']=len(rpc.records)if rpc else 0
  if rpc is not None:
   with gzip.open(folder/'rpc-records.json.gz','wt',encoding='utf-8')as stream:json.dump(rpc.records,stream,separators=(',',':'))
   outcome['rpc_records_sha256']=sha((folder/'rpc-records.json.gz').read_bytes())
  outcome['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  (folder/'VERIFICATION.json').write_text(json.dumps(outcome,indent=2)+'\n',encoding='utf-8')
 return outcome

def main():
 try:cases,forge_hash,source,methods=exports()
 except Exception as error:
  failure={'verification_complete':False,'node_started':False,'parser_error':type(error).__name__+': '+str(error),'selected_raw_sha256':RAW_SHA256,'selected_start_sha256':START_SHA256,'selected_artifact_sha256':ARTIFACT_SHA256}
  with(F/'LOCAL_RPC_PARSE_FAILURE.json').open('x',encoding='utf-8')as stream:json.dump(failure,stream,indent=2);stream.write('\n')
  print(json.dumps(failure));return 1
 OUT.mkdir(parents=True,exist_ok=False);results=[]
 for case in cases:
  result=execute(case,forge_hash,source);results.append(result)
  print(json.dumps({'case':case['label'],'verification_complete':result['verification_complete'],'meets_20m_with_full20pct':result['meets_reviewed_execution_profile'],'owned_node_stopped':result['owned_node_stopped'],'verification_error':result.get('verification_error')}),flush=True)
  if not result['verification_complete']:break
 summary={'schema':1,'source_forge_sha256':forge_hash,'source_methods':methods,'export_cases':len(cases),'completed_cases':len(results),'verification_complete':len(results)==len(cases)and all(row['verification_complete']and row['owned_node_stopped']for row in results),'meets_20m_cases':[row['profile']['label']for row in results if row['meets_reviewed_execution_profile']],'fails_20m_cases':[row['profile']['label']for row in results if not row['meets_reviewed_execution_profile']],'results':results,'production_approved':False,'diagnostic32_never_adopted':True}
 (OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 return 0 if summary['verification_complete']else 1

if __name__=='__main__':raise SystemExit(main())
