"""Private, source-pinned c7ea stock-daemon rehearsal. ROOT REVIEW REQUIRED.

CONTROLLED COPIED-STATE MODEL: not Robinhood global state, archive, fees or
production approval. No new seal, public endpoint, old journal or old node use.
"""
from pathlib import Path, PurePosixPath
import argparse, copy, datetime as dt, hashlib, http.client, json, os, re
import signal, socket, stat, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LAB=Path('/opt/popl-ubuntu-features-20261124-c7ea')
SOURCE=LAB/'source/contracts'
OUT=LAB/'runtime/run-001/keeper'
OWNER='0x000000000000000000000000000000000000a0a0'
ANVIL_SHA='05ee0cf1758024ea5e23dae562d92955ace205ab299091a43d2fa5bdeb6933bd'
CAST_SHA='d55f540256f0dd8b940a125d435919948a5e8c140262e9923067cbfa95ef2970'
INPUTS={
 'restore-state.json':(13643211,'42ab11fd14bd02868359fb3fdd84e961f3f8050245f0cb370d1962be823d9b9a'),
 'instances.json':(4845414,'e94a9dc5d4f3f04211ad77e62612b2284301584c3e363203198311d34d128e56'),
 'bindings.json':(30645,'c79d30ae3bc56ed900646bc2d8ad7da81bc60867290f8d737ae37be9ac6e0dd5'),
 'entry-receipts.json':(696971,'425902fae92cdbb210f3a12afc80908b9bd186ec1ae80060c427d9f302f3c519')}
IMPORTED_HASH='0x6880a335003c0f15184918ca84724ed5c79c27f9115a86a1475eedc683bc2ddf'
CORE='0x8366a39cc670b4001a1121b8f6a443a643e40951'
STATE='0xf3334192d15450cdd385c8b70e03f9a6bd9e673b'
CORE_HASH='0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626'
STATE_HASH='0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6'
MAX_RESPONSE=16*1024*1024
MAX_REQUEST=128*1024
STATIC_BINDINGS={'module(bytes32)','protocolPolicy()','bootstrap()','governance()',
 'migrationBudget()','vault()','portfolioPolicy()','rebalanceConfirmation()',
 'positionManager()','poolManager()','stateView()','permit2()','balancingRouter()',
 'liquidityManager()','balancer()','oracle()','registry()','activationAssets()',
 'nft()','canonicalController()','royalties()','rewards()','migration()','ledger()',
 'parent()','seaDrop()','seaDropCodeHash()','royaltyCodeHash()','creationCodeLength()',
 'part0CodeHash()','part1CodeHash()','assetsOf(address)','access()','metadataRenderer()',
 'wrapper()','executionStrategy()','converter()','seaDropMint()','controller()'}
READ_METHODS={'web3_clientVersion','net_version','eth_chainId','eth_blockNumber',
 'eth_getBlockByNumber','eth_getBlockByHash','eth_getCode','eth_getStorageAt',
 'eth_getBalance','eth_getTransactionCount','eth_getTransactionReceipt',
 'eth_getTransactionByHash','eth_call','eth_estimateGas','eth_gasPrice',
 'eth_maxPriorityFeePerGas','eth_feeHistory','eth_getLogs'}
UTILITY_CONTROLS={'anvil_mine','anvil_setIntervalMining','evm_snapshot','evm_revert','evm_mine','evm_setNextBlockTimestamp'}
SETUP_METHODS={'anvil_setBalance','anvil_impersonateAccount','anvil_stopImpersonatingAccount',
 'evm_setNextBlockTimestamp','evm_mine','evm_setAutomine','evm_setIntervalMining','eth_sendTransaction'}


def sha(raw):return hashlib.sha256(raw).hexdigest()
class HarnessRefusal(ValueError):pass
def need(ok,message):
 if not ok:raise HarnessRefusal(message)
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def save(path,v):
 raw=json.dumps(v,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'
 need(len(raw)<=2*1024*1024,'Diagnostic artifact exceeds bound')
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def json_file(path,maximum=16*1024*1024):
 st=path.lstat();need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and st.st_size<=maximum,'Input identity or size differs')
 raw=path.read_bytes();need(len(raw)==st.st_size,'Input changed during read');return json.loads(raw)
def safe_error(exc):return {'error_class':type(exc).__name__,'fixed_guard':str(exc)if type(exc)is HarnessRefusal else None,'message_sha256':sha(str(exc).encode())}

def owns(pid,port):
 inodes=[]
 for table in ('/proc/net/tcp','/proc/net/tcp6'):
  for line in Path(table).read_text().splitlines()[1:]:
   row=line.split()
   if row[3]=='0A'and int(row[1].rsplit(':',1)[1],16)==port:inodes.append(row[9])
 if len(inodes)!=1:return False
 wanted='socket:['+inodes[0]+']'
 try:return any(os.readlink(path)==wanted for path in (Path('/proc')/str(pid)/'fd').iterdir())
 except (FileNotFoundError,PermissionError):return False


class Child:
 def __init__(self,argv,cwd,env,output,maximum=65536):
  self.output=output;self.maximum=maximum;self.total=0;self.chunks=[[],[]];self.overflow=False;self.lock=threading.Lock();self.threads=[]
  self.process=subprocess.Popen(list(map(str,argv)),cwd=cwd,env=env,stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True)
  for n,stream in enumerate((self.process.stdout,self.process.stderr)):
   t=threading.Thread(target=self._drain,args=(n,stream),daemon=True);t.start();self.threads.append(t)
 def _drain(self,n,stream):
  try:
   while True:
    part=stream.read(4096)
    if not part:break
    with self.lock:
     left=max(0,self.maximum-self.total);self.chunks[n].append(part[:left]);self.total+=min(left,len(part))
     if len(part)>left:self.overflow=True
  finally:stream.close()
 def stop(self):
  p=self.process
  if p.poll()is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
  for t in self.threads:t.join(2)
  need(not any(t.is_alive()for t in self.threads),'Owned child output did not close')
  for n,label in enumerate(('stdout','stderr')):
   with(self.output.with_suffix('.'+label)).open('xb')as f:f.write(b''.join(self.chunks[n]))
  return {'stopped':p.poll()is not None,'returncode':p.returncode,'output_bytes':self.total,'overflow':self.overflow}


class Model:
 def __init__(self,binary,folder):
  self.binary=binary;self.folder=folder;self.child=None;self.rpc_count=0;self.deadline=time.monotonic()+900;self.rpc_lock=threading.Lock();self.gateway=None;self.gateway_thread=None;self.raw_send_count=0;self.last_rpc_failure=None;self.submission_review=None;self.utility_phase=False;self.utility_control_attempts=0;self.utility_snapshots={};self.utility_receipts=[];self.utility_floor=None;self.gateway_refusals=[]
 def _identity(self):
  need(self.child is not None and self.child.process.poll()is None and not self.child.overflow,'Owned model unavailable')
  pid=self.child.process.pid
  need(os.readlink('/proc/self/ns/net')==os.readlink('/proc/'+str(pid)+'/ns/net'),'Owned namespace differs')
  need(Path('/proc/self/cgroup').read_bytes()==Path('/proc/'+str(pid)+'/cgroup').read_bytes(),'Owned cgroup differs')
  need(owns(pid,19591),'Owned listener PID differs')
 def start(self,env):
  need(sha(self.binary.read_bytes())==ANVIL_SHA,'Anvil bytes differ')
  self.child=Child([self.binary,'--host','127.0.0.1','--port','19591','--accounts','0','--silent',
   '--chain-id','4663','--hardfork','cancun','--gas-limit','32000000','--load-state',LAB/'inputs/restore-state.json'],self.folder,env,self.folder/'anvil')
  end=time.monotonic()+20
  while True:
   need(self.child.process.poll()is None and not self.child.overflow,'Owned model startup failed')
   if not owns(self.child.process.pid,19591):
    need(time.monotonic()<end,'Owned listener startup deadline');time.sleep(.1);continue
   try:
    if self.rpc('eth_chainId',[])=='0x1237':break
   except (ConnectionError,OSError):pass
   need(time.monotonic()<end,'Owned model startup deadline');time.sleep(.1)
  header=self.rpc('eth_getBlockByNumber',['latest',False]);need(header['hash'].lower()==IMPORTED_HASH and int(header['gasLimit'],16)==32000000,'Imported latest anchor differs')
  return header
 def request(self,q):
  self._identity()
  with self.rpc_lock:
   need(time.monotonic()<self.deadline and self.rpc_count<6000,'Owned work budget exceeded');self.rpc_count+=1
  body=enc(q);need(len(body)<=MAX_REQUEST,'RPC request exceeds bound');end=min(self.deadline,time.monotonic()+30)
  conn=http.client.HTTPConnection('127.0.0.1',19591,timeout=max(.001,end-time.monotonic()))
  try:
   conn.request('POST','/',body,{'Content-Type':'application/json'});response=conn.getresponse();need(response.status==200,'Owned HTTP status differs');parts=[];size=0
   while True:
    need(time.monotonic()<end,'Owned response deadline');part=response.read1(min(65536,MAX_RESPONSE+1-size));need(time.monotonic()<end,'Owned response deadline')
    if not part:break
    size+=len(part);need(size<=MAX_RESPONSE,'Owned response byte limit');parts.append(part)
   raw=b''.join(parts);answer=json.loads(raw)
   need(type(answer)is dict and answer.get('jsonrpc')=='2.0'and type(answer.get('id'))is type(q['id'])and answer['id']==q['id']and('result'in answer)!=('error'in answer),'Owned response identity differs')
   return answer
  finally:conn.close()
 def rpc(self,method,params):
  need(method in READ_METHODS|SETUP_METHODS,'Closed driver method set');q={'jsonrpc':'2.0','id':self.rpc_count+1,'method':method,'params':params};answer=self.request(q)
  if 'error'in answer:
   error=answer['error'];data=error.get('data')if type(error)is dict else None
   self.last_rpc_failure={'method':method,'request_id':q['id'],'error_code':error.get('code')if type(error)is dict and type(error.get('code'))is int else None,'revert_selector':data[:10]if type(data)is str and re.fullmatch(r'0x[0-9a-fA-F]{8,}',data)is not None else None}
   raise HarnessRefusal('Owned RPC refused; inspect bounded method/code/selector')
  return answer['result']
 def gateway_start(self):
  model=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*_):pass
   def do_POST(self):
    self.connection.settimeout(30);identifier=None;method=None;control_before=None
    try:
     length=int(self.headers.get('Content-Length','0'));need(0<length<=MAX_REQUEST,'Gateway request bound')
     q=json.loads(self.rfile.read(length));need(type(q)is dict and q.get('jsonrpc')=='2.0'and type(q.get('id'))is int,'Closed gateway envelope')
     if set(q)=={'jsonrpc','id','method'}and q['method']in {'web3_clientVersion','net_version','eth_chainId','eth_blockNumber','eth_gasPrice','eth_maxPriorityFeePerGas'}:q=dict(q,params=[])
     need(set(q)=={'jsonrpc','id','method','params'}and type(q['params'])is list,'Closed gateway parameter shape')
     identifier=q['id'];method=q['method'];need(type(method)is str,'Gateway method type differs');need(method in READ_METHODS|{'eth_sendRawTransaction'}|UTILITY_CONTROLS,'Closed gateway method set')
     if method in UTILITY_CONTROLS:
      need(model.utility_phase and model.utility_floor is not None,'Utility control phase is closed')
      with model.rpc_lock:
       model.utility_control_attempts+=1;need(model.utility_control_attempts<=16,'Utility control attempt ceiling')
      params=q['params']
      allowed=(method=='anvil_setIntervalMining'and len(params)==1 and type(params[0])is int and params[0]in(0,1)or
        method in('evm_snapshot','evm_mine')and params==[]or
        method=='anvil_mine'and params==['0xd']or
        method=='evm_revert'and len(params)==1 and type(params[0])is str and params[0]in model.utility_snapshots or
        method=='evm_setNextBlockTimestamp'and len(params)==1 and type(params[0])is int and 0<params[0]<1<<63 and abs(params[0]-time.time())<=60)
      need(allowed,'Utility control parameters differ')
      if method in('evm_mine','anvil_mine'):
       pending_head=model.rpc('eth_getBlockByNumber',['pending',False]);need(type(pending_head)is dict and type(pending_head.get('transactions'))is list and not pending_head['transactions'],'Utility empty mining found pending transactions')
      if method=='evm_snapshot':
       control_before=model.rpc('eth_getBlockByNumber',['latest',False]);need(int(control_before['number'],16)>=model.utility_floor,'Utility snapshot predates recovered actor anchors')
     if method=='eth_sendRawTransaction':
      with model.rpc_lock:
       model.raw_send_count+=1;need(model.raw_send_count==1,'One reviewed harvest broadcast only')
      need(len(q['params'])==1 and type(q['params'][0])is str and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',q['params'][0])is not None,'Signed envelope encoding differs')
      review=model.submission_review;need(type(review)is dict,'Explicit first-submission review absent')
      config_raw=review['configuration'].read_bytes();need(sha(config_raw)==review['configuration_sha256'],'Reviewed keeper configuration changed')
      configuration=json.loads(config_raw);need(configuration['sender']==review['sender'],'Reviewed sender changed')
      state=json_file(review['journal']);intent=state.get('pending');need(type(intent)is dict,'Durable pending intent absent')
      need(state.get('sender')==review['sender']and state.get('next_nonce')==0 and
           intent.get('key')=='harvest:'+review['bucket']and intent.get('nonce')==0 and
           intent.get('value')==0 and intent.get('to')==review['vault']and intent.get('hash')is None,'Unreviewed first action forbidden')
      data=intent.get('data');need(type(data)is str and len(data)==138 and data.startswith(review['selector'])and
           re.fullmatch(r'0x[0-9a-f]+',data)is not None and int(data[10:74],16)==int(review['bucket']),'First harvest calldata differs')
      head=model.rpc('eth_getBlockByNumber',['latest',False]);stamp=int(head['timestamp'],16);need(stamp<=int(data[74:138],16)<=stamp+600,'First harvest deadline differs')
      budget=intent.get('fee_review');need(type(budget)is dict and budget.get('schema')==1 and budget.get('receipt_fee_policy')=='included'and
           type(budget.get('gas_limit'))is int and 0<budget['gas_limit']<=24000000 and
           type(budget.get('max_fee_per_gas'))is int and 0<budget['max_fee_per_gas']<=5000000000 and
           budget.get('l1_fee_allowance_wei')==0 and type(budget.get('maximum_cost_wei'))is int and
           budget['maximum_cost_wei']==budget['gas_limit']*budget['max_fee_per_gas']<=10000000000000000,'First harvest gas/fee review differs')
      need(sum(int(value)for value in state.get('spent',{}).values())+budget['maximum_cost_wei']<=50000000000000000,'First harvest daily review differs')
      save(OUT/'BEFORE_RAW_SUBMISSION.json',{'durable_intent':intent,'sender':review['sender'],'configuration_sha256':review['configuration_sha256'],
           'raw_signature_logged':False,'actual_signed_envelope_predecoded':False,'postforward_exact_transaction_verification_required':True})
     answer=model.request(q)
     if method in UTILITY_CONTROLS:
      need('error'not in answer,'Actual utility control was refused')
      if method=='evm_snapshot':
       snapshot=answer['result'];need(type(snapshot)is str and re.fullmatch(r'0x[0-9a-fA-F]{1,64}',snapshot)is not None and snapshot not in model.utility_snapshots,'Actual utility snapshot ID differs');model.utility_snapshots[snapshot]=control_before
      if method=='evm_revert':
       need(answer['result']is True,'Actual utility revert failed');expected=model.utility_snapshots.pop(q['params'][0]);actual=model.rpc('eth_getBlockByNumber',['latest',False]);need(actual['hash']==expected['hash']and actual['number']==expected['number']and int(actual['number'],16)>=model.utility_floor,'Utility revert crossed recovered actor anchors')
      model.utility_receipts.append({'method':method,'attempt':model.utility_control_attempts,'result':answer['result']})
    except Exception as exc:
     if len(model.gateway_refusals)<8:model.gateway_refusals.append({'method':method if type(method)is str and method in READ_METHODS|{'eth_sendRawTransaction'}|UTILITY_CONTROLS else 'refused_method',**safe_error(exc)})
     answer={'jsonrpc':'2.0','id':identifier,'error':{'code':-32070,'message':'Owned bounded model gateway refused','data':type(exc).__name__}}
    payload=enc(answer);self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
  self.gateway=ThreadingHTTPServer(('127.0.0.1',19592),Handler);self.gateway.daemon_threads=True
  self.gateway_thread=threading.Thread(target=self.gateway.serve_forever,daemon=True);self.gateway_thread.start()
 def close(self):
  if self.gateway is not None:self.gateway.shutdown();self.gateway.server_close();self.gateway_thread.join(2)
  return None if self.child is None else self.child.stop()


def validate_source(expected):
 manifest=LAB/'inputs/SOURCE_MANIFEST.json';raw=manifest.read_bytes();need(len(raw)<=2*1024*1024 and sha(raw)==expected,'Source manifest differs');meta=json.loads(raw)
 need(meta.get('schema')==1 and re.fullmatch(r'[0-9a-f]{40}',meta.get('source_head',''))and type(meta.get('members'))is dict,'Source manifest shape differs')
 for relative,row in meta['members'].items():
  path=PurePosixPath(relative);need(not path.is_absolute()and'..'not in path.parts and'\\'not in relative,'Unsafe source path')
  p=SOURCE/relative;need(p.is_file()and not p.is_symlink(),'Source file identity differs');raw=p.read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'Published source bytes differ')
 need({'keeper/monitor.py','keeper/cast_process.py','keeper/ops.py','keeper/health.py','zzz_ops/abi.py','indexer/event_schema.json'}<=set(meta['members']),'Required source members absent')
 return meta


def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--utilities-sha256');args=p.parse_args()
 need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New unprivileged private namespace required')
 need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed reviewed helper path required');OUT.mkdir(mode=0o700,exist_ok=False)
 source_meta=validate_source(args.source_manifest_sha256);input_before={}
 for name,(size,digest)in INPUTS.items():
  path=LAB/'inputs'/name;raw=path.read_bytes();need(len(raw)==size and sha(raw)==digest,'Fixed fixture input differs');input_before[name]=digest
 sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE))
 from zzz_ops.abi import calldata,keccak256
 from keeper.cast_process import run_cast
 rows=json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal F6 instance count differs');addresses={r['role']:r['address'].lower()for r in rows};hashes={r['role']:r['runtime_keccak256'].lower()for r in rows}
 need(len(addresses)==len(set(addresses.values()))==39,'Normal F6 role identity differs')
 temporary=OUT/'tmp';temporary.mkdir(mode=0o700)
 env={'TMPDIR':str(temporary),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'secrets'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'}
 result={'schema':1,'scope':'NEW actual stock daemon/real Cast in controlled copied-state model; no original global-state/archive or production qualification','success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'production_approved':False,'cleanup':[]}
 model=None;daemon=None;stage='owned_model_start'
 try:
  folder=OUT/'model';folder.mkdir(mode=0o700);model=Model(LAB/'tools/anvil',folder);initial=model.start(env);save(OUT/'IMPORTED_HEAD.json',initial)
  def read(role,sig,*values):
   data=calldata(sig,*values);return model.rpc('eth_call',[{'to':addresses[role],'data':data},'latest'])
  stage='runtime_and_static_binding_proof';runtime=[]
  for row in rows:
   code=model.rpc('eth_getCode',[row['address'],'latest']);need('0x'+keccak256(bytes.fromhex(code[2:])).hex()==row['runtime_keccak256'].lower(),'F6 runtime pin differs');runtime.append(row['role'])
  bindings=[]
  for row in json_file(LAB/'inputs/bindings.json'):
   if (row['signature']not in STATIC_BINDINGS and not(row['role']=='buyback'and row['signature']=='zzz()'))or 'expected'not in row:continue
   actual=read(row['role'],row['signature'],*row.get('arguments',[]));need(actual.lower()==row['expected'].lower(),'Static controller or module binding differs');bindings.append({'role':row['role'],'signature':row['signature'],'actual':actual})
  need(len(bindings)==91,'Required static binding proof incomplete')
  need(int(read('access','isSealed()'),16)==1 and int(read('access','paused()'),16)==0 and int(read('access','canonicalState()'),16)==0 and int(read('access','preparationActive()'),16)==0 and int(read('access','lpExitStarted()'),16)==0,'Imported live lifecycle differs')
  need(int(read('nft','mintedCount()'),16)==2 and int(read('access','governance()'),16)==int(OWNER,16),'Imported mint/governance differs')
  for address,pin in ((CORE,CORE_HASH),(STATE,STATE_HASH)):
   code=model.rpc('eth_getCode',[address,'latest']);need('0x'+keccak256(bytes.fromhex(code[2:])).hex()==pin,'Copied native dependency runtime differs')
  save(OUT/'PREMUTATION_BINDINGS.json',{'runtimes':runtime,'static_bindings':bindings,'sealed':True,'minted':2,'new_seal':False})
  stage='new_private_disposable_signer';secrets=OUT/'secrets';secrets.mkdir(mode=0o700);password=secrets/'password';keystore=secrets/'keeper'
  with password.open('xb')as f:f.write(os.urandom(32).hex().encode()+b'\n')
  password.chmod(0o600);need(sha((LAB/'tools/cast').read_bytes())==CAST_SHA,'Cast bytes differ')
  key_env={**env,'CAST_PASSWORD':password.read_text().strip()}
  generated=run_cast([str(LAB/'tools/cast'),'wallet','new',str(secrets),'keeper'],env=key_env,timeout=30)
  need(generated.returncode==0 and keystore.is_file(),'Disposable encrypted key creation refused');del generated;del key_env;keystore.chmod(0o600)
  found=run_cast([str(LAB/'tools/cast'),'wallet','address','--keystore',str(keystore),'--password-file',str(password)],env=env,timeout=30)
  need(found.returncode==0,'Disposable signer address read refused');sender=found.stdout.strip().lower();need(re.fullmatch(r'0x[0-9a-f]{40}',sender)is not None and sender not in set(addresses.values())|{OWNER},'Disposable signer identity differs')
  stage='owned_fixture_bootstrap';model.rpc('evm_setIntervalMining',[0]);model.rpc('evm_setAutomine',[True])
  head=model.rpc('eth_getBlockByNumber',['latest',False]);now=int(time.time());need(int(head['timestamp'],16)<=now,'Copied fixture time is unexpectedly future');model.rpc('evm_setNextBlockTimestamp',[now]);model.rpc('evm_mine',[])
  model.rpc('anvil_setBalance',[sender,hex(10**18)]);need(int(model.rpc('eth_getTransactionCount',[sender,'latest']),16)==0 and int(model.rpc('eth_getTransactionCount',[sender,'pending']),16)==0,'Fresh model signer nonce differs')
  model.rpc('anvil_impersonateAccount',[OWNER]);setup=[]
  def setup_tx(target,data):
   nonce=model.rpc('eth_getTransactionCount',[OWNER,'latest']);need(nonce==model.rpc('eth_getTransactionCount',[OWNER,'pending']),'Fixture governance pending nonce differs')
   envelope={'from':OWNER,'to':target,'data':data,'value':'0x0','gas':hex(4000000),'nonce':nonce}
   h=model.rpc('eth_sendTransaction',[envelope]);end=time.monotonic()+20;receipt=None
   while time.monotonic()<end:
    receipt=model.rpc('eth_getTransactionReceipt',[h])
    if receipt:break
    time.sleep(.1)
   need(receipt is not None and receipt['status']=='0x1','Fixture governance setup receipt failed');setup.append({'hash':h,'receipt':receipt,'envelope':envelope})
  setup_tx(addresses['access'],calldata('setKeeper(address,bool)',sender,True))
  feeds=set()
  def visit(value):
   if isinstance(value,dict):
    label=str(value.get('label',value.get('name',value.get('key',''))))
    if any(role in label for role in ('eth_feed_a','eth_feed_b','zzz_feed_a','zzz_feed_b')):
     record=value.get('receipt',{})
     if isinstance(record,dict)and record.get('contractAddress'):feeds.add(record['contractAddress'].lower())
    for child in value.values():visit(child)
   elif isinstance(value,list):
    for child in value:visit(child)
  visit(json_file(LAB/'inputs/entry-receipts.json'));need(len(feeds)==4,'Expected controlled feed identities absent');feedproof=[]
  for feed in sorted(feeds):
   before=model.rpc('eth_call',[{'to':feed,'data':calldata('latestRoundData()')},'latest']);words=[int(before[i:i+64],16)for i in range(2,len(before),64)];need(len(words)==5 and 0<words[1]<1<<255,'Controlled feed answer differs')
   stamp=int(model.rpc('eth_getBlockByNumber',['latest',False])['timestamp'],16);setup_tx(feed,'0x'+keccak256(b'set(int256,uint256,uint256)').hex()[:8]+f'{words[1]:064x}{stamp:064x}{stamp:064x}');after=model.rpc('eth_call',[{'to':feed,'data':calldata('latestRoundData()')},'latest']);need(int(after[66:130],16)==words[1],'Controlled feed answer changed');feedproof.append({'address':feed,'answer_unchanged':True})
  model.rpc('anvil_stopImpersonatingAccount',[OWNER]);need(int(read('access','keepers(address)',sender),16)==1 and int(read('access','guardians(address)',sender),16)==0,'Fresh keeper-only role differs')
  save(OUT/'BOOTSTRAP.json',{'sender':sender,'setup':setup,'controlled_feed_timestamps_refreshed':feedproof,'global_market_qualified':False,'public_calls':0})
  stage='fresh_stock_configuration';live=OUT/'live';live.mkdir(mode=0o700)
  roles=('access','vault','strategy','fees','compounder','buyback','pools','rewards','liquidity','balancing_router','lp_balance_math','lp_position_executor','portfolio_policy','protocol_policy','rebalance_confirmation','oracle','contribution_pricing')
  contracts={name:addresses[name]for name in roles};pins={name:hashes[name]for name in roles}
  contracts.update(principal_exit=addresses['migration'],pool_manager=CORE,state_view=STATE);pins.update(principal_exit=hashes['migration'],pool_manager=CORE_HASH,state_view=STATE_HASH,idle_compounding_budget=hashes['migration_budget'])
  config={'chain_id':4663,'accounting_model':'shared-pools-v2','accounting_version':7,'custody_version':5,'protocol_policy_version':1,'portfolio_version':2,'maintenance_policy_version':3,'rebalance_confirmation_version':3,'fee_intake_version':1,'lp_routing_version':3,'execution_quality_version':1,'execution_price_version':1,'royalty_settlement_version':4,'rpc_urls':['http://127.0.0.1:19592'],'sender':sender,'contracts':contracts,'code_hashes':pins,'idle_compounding_budget':addresses['migration_budget'],'reviewed_for_live_use':True,'cast_binary':str(LAB/'tools/cast'),'keystore':str(keystore),'password_file':str(password),'interval_seconds':240,'confirmations':12,'max_gas_limit':24000000,'max_gas_price_wei':'5000000000','max_transaction_cost_wei':'10000000000000000','max_daily_cost_wei':'50000000000000000','l1_fee_allowance_wei':'0','receipt_fee_policy':'included','revert_cooldown_seconds':3600,'state_path':str(live/'state.json'),'health_path':str(live/'health.json'),'lock_path':str(live/'keeper.lock'),'bucket_discovery':{'maximum_count':4,'max_per_cycle':4},'maintenance':{'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600},'bucket_overrides':{},'adaptive_range':{'enabled':False},'royalty_conversion':{'enabled':False},'lp_conversion':{'enabled':False},'metadata_refresh':{'enabled':False},'principal_distribution':{'enabled':False},'buybacks':[]}
  save(live/'config.json',config)
  model.submission_review={'configuration':live/'config.json','configuration_sha256':sha((live/'config.json').read_bytes()),
      'journal':live/'state.json','sender':sender,'vault':addresses['vault'],
      'bucket':'47181787163762592248710325652087236475813397965818762058663276509558631703230',
      'selector':'0x'+keccak256(b'collectFees(uint256,uint256)').hex()[:8]}
  model.gateway_start();model.rpc('evm_mine',[]);model.rpc('evm_mine',[])
  def stock(label,args,timeout=40):
   child=Child(['/usr/bin/python3','-m','keeper.monitor','--config',live/'config.json',*args],SOURCE,env,OUT/label);end=time.monotonic()+timeout
   try:
    while child.process.poll()is None and time.monotonic()<end:need(not child.overflow,'Stock CLI output overflow');time.sleep(.1)
    need(child.process.poll()is not None,'Stock CLI deadline')
   finally:metadata=child.stop()
   need(not metadata['overflow'],'Stock CLI output overflow');return metadata
  stage='stock_initialize';initialization=stock('initialize',['--initialize-state']);need(initialization['returncode']==0,'Fresh stock journal initialization refused')
  state=json_file(live/'state.json');need(state['next_nonce']==0 and state['pending']is None,'Fresh journal identity differs');save(OUT/'INITIAL_JOURNAL.json',state)
  stage='stock_live_durable_pending';model.rpc('evm_setAutomine',[False]);model.rpc('evm_setIntervalMining',[0])
  daemon=Child(['/usr/bin/python3','-m','keeper.monitor','--config',live/'config.json','--live'],SOURCE,env,OUT/'stock-live-001')
  end=time.monotonic()+120;pending=None
  while time.monotonic()<end:
   need(daemon.process.poll()is None and not daemon.overflow,'Stock keeper exited before durable pending')
   if(live/'state.json').exists():
    state=json_file(live/'state.json');candidate=state.get('pending')
    if type(candidate)is dict and type(candidate.get('hash'))is str:pending=copy.deepcopy(candidate);break
   time.sleep(.1)
  need(pending is not None and pending['key'].startswith('harvest:')and pending['nonce']==0 and pending['to']==addresses['vault'],'Actual stock harvest intent unavailable')
  h=pending['hash'];transaction=model.rpc('eth_getTransactionByHash',[h]);need(transaction['from'].lower()==sender and transaction['to'].lower()==addresses['vault']and transaction['input']==pending['data']and int(transaction['nonce'],16)==0 and transaction.get('blockNumber')is None,'Actual included-model pending transaction differs')
  need(model.raw_send_count==1,'One actual Cast broadcast required');result['actual_Cast_broadcasts']=1;public_transaction={key:value for key,value in transaction.items()if key in {'hash','from','to','input','value','gas','nonce','blockHash','blockNumber','transactionIndex','gasPrice','type','chainId'}};save(OUT/'DURABLE_PENDING.json',{'pending':pending,'transaction_without_signature':public_transaction,'raw_submission_attempts':1})
  stage='stock_lock_contention';lock_before=(live/'keeper.lock').stat();journal_before_contender=(live/'state.json').read_bytes()
  nonce_before_contender=[model.rpc('eth_getTransactionCount',[sender,tag])for tag in ('latest','pending')]
  contender=stock('lock-contender',['--live','--once']);events=[]
  for line in (OUT/'lock-contender.stdout').read_text(encoding='utf-8').splitlines():
   event=json.loads(line)
   if type(event)is dict and event.get('event')=='keeper_halted':events.append(event)
  need(contender['returncode']==1 and len(events)==1 and events[0].get('error_type')=='RuntimeError'and
       str(events[0].get('error_site','')).startswith('state.py:process_lock:'),'Contender did not prove flock exclusion')
  lock_after=(live/'keeper.lock').stat();need((lock_before.st_dev,lock_before.st_ino,lock_before.st_mode)==(lock_after.st_dev,lock_after.st_ino,lock_after.st_mode),'Lock inode/mode changed')
  need((live/'state.json').read_bytes()==journal_before_contender and model.raw_send_count==1 and
       [model.rpc('eth_getTransactionCount',[sender,tag])for tag in ('latest','pending')]==nonce_before_contender,'Lock contender altered journal/submission/nonce')
  save(OUT/'LOCK_CONTENTION.json',{'event':events[0],'same_inode_and_mode':True,'journal_nonce_and_send_unchanged':True,'returncode':1})
  stage='stock_interruption';journal_before=(live/'state.json').read_bytes();result['cleanup'].append({'label':'first-stock-daemon',**daemon.stop()});daemon=None
  need((live/'state.json').read_bytes()==journal_before,'Interruption rewrote durable pending');save(OUT/'INTERRUPTED_PENDING.json',{'sha256':sha(journal_before),'pending_hash':h,'raw_submission_attempts':model.raw_send_count})
  stage='mining_saved_transaction';model.rpc('evm_mine',[]);receipt=model.rpc('eth_getTransactionReceipt',[h]);need(receipt is not None and receipt['status']=='0x1','Saved actual transaction receipt failed')
  confirmation_headers=[]
  for _ in range(12):
   model.rpc('evm_mine',[]);confirmation_headers.append(model.rpc('eth_getBlockByNumber',['latest',False]))
  need(int(confirmation_headers[-1]['number'],16)-int(receipt['blockNumber'],16)+1>=12,'Actual receipt confirmation depth insufficient')
  save(OUT/'CONFIRMATION_BLOCKS.json',{'headers':confirmation_headers,'configured_confirmations':12,'all_genuine_local_blocks':True})
  model.rpc('evm_setAutomine',[False]);model.rpc('evm_setIntervalMining',[1])
  save(OUT/'ACTUAL_RECEIPT.json',receipt)
  stage='stock_same_journal_recovery';daemon=Child(['/usr/bin/python3','-m','keeper.monitor','--config',live/'config.json','--live'],SOURCE,env,OUT/'stock-live-002')
  end=time.monotonic()+560;healthy=False
  while time.monotonic()<end:
   need(daemon.process.poll()is None and not daemon.overflow,'Stock recovery daemon exited')
   state=json_file(live/'state.json')
   if state.get('pending')is None and state.get('next_nonce')==1 and(live/'health.json').exists():
    health=json_file(live/'health.json');healthy=health.get('status')=='healthy_v2'
    if healthy:break
   time.sleep(.2)
  need(healthy,'Stock recovery did not complete a healthy normal cycle');need(model.raw_send_count==1 and int(model.rpc('eth_getTransactionCount',[sender,'latest']),16)==1,'Recovery resubmitted or nonce differs')
  block=model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);paid=int(receipt['gasUsed'],16)*int(receipt['effectiveGasPrice'],16);day=dt.datetime.fromtimestamp(int(block['timestamp'],16),dt.timezone.utc).date().isoformat()
  need(int(state['spent'][day])==paid and state['last'].get(pending['key'])==int(block['timestamp'],16),'Exact actual spend/harvest receipt clock differs')
  save(OUT/'RECOVERED_JOURNAL.json',state);save(OUT/'HEALTHY_NORMAL_CYCLE.json',health)
  result['cleanup'].append({'label':'recovered-stock-daemon',**daemon.stop()});daemon=None
  actor_journal=(live/'state.json').read_bytes()
  if args.utilities_sha256:
   stage='reviewed_readonly_utilities';helper=LAB/'source/helpers/utility_runtime.py';need(sha(helper.read_bytes())==args.utilities_sha256,'Reviewed utilities helper differs')
   model.utility_floor=int(model.rpc('eth_getBlockByNumber',['latest',False])['number'],16);model.utility_phase=True;utility=None
   try:
    utility=Child(['/usr/bin/python3',helper,'--source-root',SOURCE,'--output',LAB/'runtime/run-001/utilities','--keeper-config',live/'config.json','--rpc-url','http://127.0.0.1:19592','--bucket','47181787163762592248710325652087236475813397965818762058663276509558631703230'],SOURCE,env,OUT/'utilities-runner');end=time.monotonic()+300
    while utility.process.poll()is None and time.monotonic()<end:need(not utility.overflow,'Utilities output overflow');time.sleep(.1)
    need(utility.process.poll()is not None,'Utilities deadline')
   finally:
    if utility is not None:utility_result=utility.stop()
    model.utility_phase=False
    save(OUT/'UTILITY_CONTROLS.json',{'attempts':model.utility_control_attempts,'maximum_attempts':16,'phase_closed':True,'recovered_actor_floor':model.utility_floor,'receipts':model.utility_receipts,'shared_RPC_requests':model.rpc_count})
   need(utility_result['returncode']==0 and not utility_result['overflow'],'Reviewed utilities refused')
  need(model.raw_send_count==1 and (live/'state.json').read_bytes()==actor_journal,'Utilities altered signer action or recovered journal')
  validate_source(args.source_manifest_sha256)
  for name,digest in input_before.items():need(sha((LAB/'inputs'/name).read_bytes())==digest,'Original copied-state input changed')
  result.update(success=True,actual_Cast_broadcasts=1,actual_saved_hash_recovered=True,nonce_before=0,nonce_after=1,exact_receipt_spend=paid,authenticated_harvest_clock=True,same_journal=True,lock_contender_refused=True,normal_healthy_cycle=True,source_inputs_preserved=True,controlled_prices_unchanged=True,model_RPC_requests=model.rpc_count,all_enabled_jobs_qualified=False)
 except Exception as exc:result.update(failure_stage=stage,**safe_error(exc))
 finally:
  if daemon is not None:result['cleanup'].append({'label':'stock-daemon-final',**daemon.stop()})
  if model is not None:
   result['model_RPC_requests']=model.rpc_count;result['raw_submission_attempts']=model.raw_send_count;result['last_model_RPC_failure']=model.last_rpc_failure;result['gateway_refusals']=model.gateway_refusals;result['utility_control_attempts']=model.utility_control_attempts;metadata=model.close()
   if metadata is not None:result['cleanup'].append({'label':'owned-model',**metadata})
  result['tracked_children_stopped']=bool(result['cleanup'])and all(row.get('stopped')is True and row.get('overflow')is False for row in result['cleanup'])
  result['whole_cgroup_cleanup_requires_external_readback']=True
  if not result['tracked_children_stopped']:result['success']=False
  result['secret_disposition']={'created_files':sum((OUT/'secrets'/name).is_file()for name in ('keeper','password')),'retained_only_in_new_owned_lab':True,'contents_or_content_hashes_exported':False};save(OUT/'RESULT.json',result)
 print(json.dumps({'success':result['success'],'failure_stage':result.get('failure_stage'),'tracked_children_stopped':result['tracked_children_stopped']}));return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
