"""Private c7ec directed stock jobs. ROOT REVIEW REQUIRED; not executed.

Fresh copies of already-sealed state, no new seal/public fork/old journals.
Stock run_cycle and real Cast, not a continuous daemon/provider/market soak.
"""
from pathlib import Path
import argparse,contextlib,copy,json,os,re,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import keeper_runtime as B

LAB=Path('/opt/popl-ubuntu-key-rotation-20261124-c801');SOURCE=LAB/'source/contracts';OUT=LAB/'runtime/run-001/jobs'
B.LAB=LAB;B.SOURCE=SOURCE;B.OUT=OUT
OWNER=B.OWNER;ZERO='0x'+'0'*40;ZZZ='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
POOL='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
BUCKET=47181787163762592248710325652087236475813397965818762058663276509558631703230
POSM='0x58daec3116aae6d93017baaea7749052e8a04fa7'
need=B.need;save=B.save;sha=B.sha
class FeatureBlocked(ValueError):pass

class Work:
 def __init__(self):self.count=0;self.raw=0;self.raw_attempts=0;self.maximum_cost=0;self.deadline=time.monotonic()+900;self.lock=threading.Lock()
 def consume(self):
  with self.lock:
   need(time.monotonic()<self.deadline and self.count<6000,'Shared feature work budget exceeded');self.count+=1

class Events:
 def __init__(self):self.parts=[];self.size=0
 def write(self,value):
  raw=value.encode('utf8','strict');need(self.size+len(raw)<=65536,'Combined stock events exceed64KiB');self.size+=len(raw);self.parts.append(value);return len(value)
 def flush(self):pass

def encode(signature,*args):
 from zzz_ops.abi import keccak256
 types=signature[signature.index('(')+1:-1].split(',')if args else[];need(len(types)==len(args),'Flat typed argument count differs');words=[]
 for kind,value in zip(types,args):
  number=int(value,16)if type(value)is str and value.startswith('0x')else int(value)
  if kind=='address':need(0<=number<1<<160,'Typed asset/address bound')
  elif kind=='bool':need(type(value)is bool,'Typed boolean differs')
  elif kind=='bytes32':need(0<=number<1<<256,'Typed bytes32 differs')
  elif kind.startswith('uint'):need(0<=number<1<<int(kind[4:]or'256'),'Typed unsigned bound')
  elif kind.startswith('int'):bits=int(kind[3:]or'256');need(-(1<<(bits-1))<=number<1<<(bits-1),'Typed signed bound')
  else:raise B.HarnessRefusal('Only flat reviewed static types')
  words.append(f'{number%(1<<256):064x}')
 return'0x'+keccak256(signature.encode()).hex()[:8]+''.join(words)

class Model(B.Model):
 def __init__(self,folder,work):
  super().__init__(LAB/'tools/anvil',folder);self.work=work;self.deadline=work.deadline;self.review=None;self.raw_records=[];self.raw_forwarded=0;self.fault=None;self.fault_attempts=0;self.method_counts={};self.phase_counts={};self.case=None;self.submission_enabled=False;self.allowed_sender=None
 def start(self,env):
  need(sha(self.binary.read_bytes())==B.ANVIL_SHA,'Anvil bytes differ');self.controlled_genesis_timestamp=int(time.time())
  self.child=B.Child([self.binary,'--host','127.0.0.1','--port','19591','--accounts','0','--silent','--chain-id','4663','--hardfork','cancun','--gas-limit','32000000','--gas-price','1','--block-base-fee-per-gas','1','--disable-min-priority-fee','--timestamp',str(self.controlled_genesis_timestamp),'--load-state',LAB/'inputs/restore-state.json'],self.folder,env,self.folder/'anvil');end=time.monotonic()+20
  while True:
   need(self.child.process.poll()is None and not self.child.overflow,'Owned window model startup failed')
   if not B.owns(self.child.process.pid,19591):need(time.monotonic()<end,'Owned window listener deadline');time.sleep(.1);continue
   try:
    if self.rpc('eth_chainId',[])=='0x1237':break
   except(ConnectionError,OSError):pass
   need(time.monotonic()<end,'Owned window startup deadline');time.sleep(.1)
  header=self.rpc('eth_getBlockByNumber',['latest',False]);need(header['hash'].lower()==B.IMPORTED_HASH and int(header['gasLimit'],16)==32000000,'Loaded window anchor differs');return header
 def request(self,q):
  self.work.consume();method=q.get('method');need(method in B.READ_METHODS|B.SETUP_METHODS|{'eth_sendRawTransaction','anvil_mine'},'Closed counted RPC method')
  phase=getattr(self.case,'stage','model_start');need(type(phase)is str and 0<len(phase)<=64,'Bounded phase identity')
  with self.work.lock:
   self.method_counts[method]=self.method_counts.get(method,0)+1;self.phase_counts[phase]=self.phase_counts.get(phase,0)+1
  return super().request(q)
 def mine_empty_descendants(self,receipt):
  # Driver-only fixed operation. The stock gateway STILL accepts reads/raw-send
  # only; it gains no time/mining/state-control capability.
  need(type(receipt)is dict and receipt.get('status')=='0x1','Successful inclusion required before descendant mining')
  pending=self.rpc('eth_getBlockByNumber',['pending',False]);need(type(pending)is dict and pending.get('transactions')==[],'Receipt descendants require empty pending block')
  before=self.rpc('eth_getBlockByNumber',['latest',False]);need(before['number']==receipt['blockNumber']and before['hash']==receipt['blockHash'],'Receipt is not the current canonical head')
  q={'jsonrpc':'2.0','id':self.rpc_count+1,'method':'anvil_mine','params':['0xc']};answer=self.request(q);need('error'not in answer,'Fixed12empty-descendant mining refused')
  after=self.rpc('eth_getBlockByNumber',['latest',False]);need(int(after['number'],16)==int(before['number'],16)+12 and int(after['timestamp'],16)>=int(before['timestamp'],16) and abs(int(after['timestamp'],16)-time.time())<=600 and after.get('transactions')==[],'Actual12-descendant head/depth/time differs')
  canonical=self.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);need(canonical==before,'Receipt anchor changed during descendant mining')
  return {'before':before,'after':after,'genuine_empty_descendants':12,'configured_confirmations':12,'controlled_chain_only':True}

 def guard(self):
  from zzz_ops.abi import keccak256
  r=self.review;need(self.submission_enabled and type(r)is dict and r['sender']==self.allowed_sender,'Closed actor signing phase');need(type(r)is dict,'Reviewed job intent is absent');raw=r['config'].read_bytes();need(sha(raw)==r['config_sha'],'Reviewed configuration changed');cfg=json.loads(raw);st=B.json_file(r['journal']);p=st.get('pending')
  need(type(p)is dict and p.get('hash')is None and p.get('value')==0 and st['sender']==cfg['sender']==r['sender']and p.get('nonce')==st['next_nonce'],'Durable job identity differs')
  data=p.get('data');key=p.get('key');need(type(data)is str and re.fullmatch(r'0x[0-9a-f]+',data)is not None and(len(data)-10)%64==0 and type(key)is str,'Job calldata encoding differs');matched=False
  for kind,role,signature in r['allowed']:
   if key.startswith(kind+':')and p['to']==cfg['contracts'][role]and data[:10]=='0x'+keccak256(signature.encode()).hex()[:8]:
    values=[int(data[i:i+64],16)for i in range(10,len(data),64)];deadline=None
    if kind in('compound','rebalance'):need(len(values)==3 and values[:2]==[BUCKET,1],'Exact LP operation arguments differ');deadline=values[2]
    elif kind in('rebalance_observation','rebalance_reset'):need(values==[BUCKET],'Exact confirmation bucket differs')
    elif kind=='lp_conversion':
     need(len(values)>=7 and values[0]==int(ZZZ,16)and values[1]==160 and values[2]==int(r['conversion_route'],16)and values[3]>0 and 1<=values[5]<=2 and len(values)==6+values[5]and values[6:]==sorted(set(values[6:]))and set(values[6:])<=set(r['conversion_ids']),'Exact native LP conversion arguments differ');deadline=values[4]
    elif kind=='harvest':need(len(values)==2 and values[0]==BUCKET,'Exact harvest arguments differ');deadline=values[1]
    elif kind=='buyback':need(len(values)==4 and values[:3]==[int(ZZZ,16),r['burn_amount'],int(POOL,16)],'Exact direct ZZZ burn arguments differ');deadline=values[3]
    elif kind=='metadata':need(values==[1,2],'Exact notification ordinals differ')
    else:raise B.HarnessRefusal('Unreviewed job kind')
    matched=True;break
  need(matched,'Only explicitly reviewed stock jobs may broadcast')
  stamp=int(self.rpc('eth_getBlockByNumber',['latest',False])['timestamp'],16)
  if deadline is not None:need(stamp<=deadline<=stamp+600,'Job deadline differs')
  need(all(int(self.rpc('eth_getTransactionCount',[r['sender'],tag]),16)==p['nonce']for tag in('latest','pending')),'Job nonce is not free')
  f=p.get('fee_review');need(type(f)is dict and f.get('schema')==1 and f.get('receipt_fee_policy')=='included'and 0<f.get('gas_limit',0)<=24000000 and 0<f.get('max_fee_per_gas',0)<=5000000000 and f.get('l1_fee_allowance_wei')==0 and f.get('maximum_cost_wei')==f['gas_limit']*f['max_fee_per_gas']<=10**16,'Job gas/fee bounds differ');need(sum(int(v)for v in st['spent'].values())+f['maximum_cost_wei']<=5*10**16,'Job daily budget differs')
  with self.work.lock:
   need(self.work.raw<2 and self.work.maximum_cost+f['maximum_cost_wei']<=5*10**16,'Shared feature broadcast/spend bound');self.work.raw+=1;self.work.maximum_cost+=f['maximum_cost_wei']
  self.raw_records.append({'intent':copy.deepcopy(p),'config_sha256':r['config_sha'],'raw_signature_retained':False})
 def gateway_start(self):
  model=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    identifier=None;method=None
    try:
     self.connection.settimeout(30);size=int(self.headers.get('Content-Length','0'));need(0<size<=B.MAX_REQUEST,'Job gateway request bound');q=json.loads(self.rfile.read(size));need(type(q)is dict and q.get('jsonrpc')=='2.0'and type(q.get('id'))is int,'Job gateway envelope');identifier=q['id'];method=q.get('method')
     if set(q)=={'jsonrpc','id','method'}and method in {'web3_clientVersion','net_version','eth_chainId','eth_blockNumber','eth_gasPrice','eth_maxPriorityFeePerGas'}:q=dict(q,params=[])
     need(set(q)=={'jsonrpc','id','method','params'}and type(q['params'])is list and type(method)is str and method in B.READ_METHODS|{'eth_sendRawTransaction'},'Job gateway method/shape')
     if model.fault is not None and method==model.fault['method']and(model.fault.get('params')is None or q['params']==model.fault['params']):
      model.work.consume();model.fault_attempts+=1;need(model.fault_attempts<=12,'Injected fault attempt bound');answer={'jsonrpc':'2.0','id':identifier,'error':{'code':-32098,'message':'Controlled isolated read fault'}}
     else:
      if method=='eth_sendRawTransaction':
       model.raw_send_count+=1
       with model.work.lock:model.work.raw_attempts+=1;need(model.work.raw_attempts<=12,'Shared raw submission attempt bound')
       need(len(q['params'])==1 and type(q['params'][0])is str and len(q['params'][0])<=262144 and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',q['params'][0])is not None,'Signed envelope encoding differs');model.guard();model.raw_forwarded+=1
      answer=model.request(q)
    except Exception as exc:
     if len(model.gateway_refusals)<16:model.gateway_refusals.append({'method':method if type(method)is str and method in B.READ_METHODS|{'eth_sendRawTransaction'}else'refused_method',**B.safe_error(exc)})
     answer={'jsonrpc':'2.0','id':identifier,'error':{'code':-32070,'message':'Owned feature gateway refused'}}
    raw=B.enc(answer);self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  self.gateway=ThreadingHTTPServer(('127.0.0.1',19592),Handler);self.gateway.daemon_threads=True;self.gateway_thread=threading.Thread(target=self.gateway.serve_forever,daemon=True);self.gateway_thread.start()
