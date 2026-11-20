"""NEW owned native/F6 claim fixture; no public RPC, compiler or protocol slot writes.

Exact archived external runtime materialization, constructor-default reproduction,
correlated prices, controlled VRF and local token balances are explicit seams.
Every PoPL instance is created by its trusted normal creation object. All PoPL
configuration, sealing, minting, activation and allocation use actual entrypoints.
"""
from __future__ import annotations
import argparse, copy, gzip, hashlib, http.client, importlib.util, json, math
import os, re, socket, subprocess, sys, time, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from zzz_ops import deployment_plan as P
from zzz_ops.abi import keccak256
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
WORK=V/'full-claim-admission-20261120'
ANVIL=V/'foundry-v1.4.4/anvil.exe'
ANVIL_PIN='d438383b871c726407ecc5829279bea44ceac63a712be9e010813ca0a15434b6'
CACHE=Path('C:/Users/Ali/.foundry/cache/rpc/4663/88544093')
OLD_ZIP=ROOT/'reports/source9-actual-entry-20261109/campaign-evidence.zip'
FIXTURES=V/'fresh-entry3-rehearsal-fixture-compile-subagent1'
TOKENS=V/'maximum-workload-20261119/test-out/Mocks.sol'
ZERO=P.ZERO; SENDER='0x000000000000000000000000000000000000a0a0'
FEE='0x000000000000000000000000000000000000feed'
POOL='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
UNIT=10**18; CAP=32_000_000
REVIEW='0x'+keccak256(b'NEW FULL F6 CLAIM ADMISSION OWNED LOCAL FIXTURE 20261120').hex()
NATIVE_HASHES=dict(zip(P.NATIVE,(
 '0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626',
 '0xc873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2',
 '0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6',
 '0x5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca',
 '0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597')))

def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def save(path,value):
 raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 require(len(raw)<=64*1024*1024,'Evidence bound')
 with Path(path).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 return sha(raw)
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
M=module(ROOT/'scripts/rehearse-local-deployment.py','full_claim_construction_20261120')
def word(value):
 if isinstance(value,str):value=int(value,16) if value.startswith('0x') else int(value)
 return f'{int(value)%(2**256):064x}'
def encode(signature,*values):return '0x'+keccak256(signature.encode())[:4].hex()+''.join(word(v)for v in values)
def words(raw):
 require(isinstance(raw,str) and re.fullmatch(r'0x(?:[0-9a-fA-F]{64})*',raw),'Canonical static ABI')
 return [int(raw[i:i+64],16) for i in range(2,len(raw),64)]
def addr(value):return '0x'+f'{int(value):040x}'
def bytes_hash(raw):return '0x'+keccak256(raw).hex()
def short_string(value):
 raw=value.encode();require(len(raw)<32,'Short native constructor string')
 return '0x'+(raw+b'\0'*(31-len(raw))+bytes([len(raw)*2])).hex()

class LocalRPCError(RuntimeError):
 def __init__(self,method,error):self.method=method;self.error=error;super().__init__(method+' refused: '+str(error))

class OwnedNode(M.Node):
 """Same owned PID/genesis checks; expanded exact reviewed setup envelope only."""
 READS=M.READS|frozenset(('eth_blockNumber','eth_getBlockByHash','eth_getStorageAt','debug_traceCall','anvil_dumpState'))
 ADMIN=frozenset(('anvil_impersonateAccount','eth_sendTransaction','evm_mine',
   'evm_setNextBlockTimestamp','evm_snapshot','evm_revert'))
 def __init__(self,*args):
  super().__init__(*args);self.deadline=time.monotonic()+3600;self.phase='construction';self.reviewed=None
 def wire(self,method,params=None,mutation=False):
  require(self.proc is not None and self.proc.poll()is None,'Owned child not alive')
  require(method in self.READS or mutation and method in self.ADMIN,'Closed local RPC allowlist')
  require(time.monotonic()<self.deadline and len(self.records)<100000,'Owned fixture work bound')
  request={'jsonrpc':'2.0','id':len(self.records)+1,'method':method,'params':params or []}
  raw=json.dumps(request).encode();request=json.loads(raw)
  if self.connection is None:self.connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=30)
  self.connection.request('POST','/',raw,{'Content-Type':'application/json'})
  response=self.connection.getresponse();body=response.read(64*1024*1024+1)
  require(response.status==200 and len(body)<=64*1024*1024,'Local bounded response')
  value=json.loads(body);self.records.append({'request':request,'response':value})
  require(value.get('id')==request['id'],'RPC identity')
  if 'error'in value:raise LocalRPCError(method,value['error'])
  require('result'in value,'RPC result missing');return value['result']
 def call(self,method,params=None):return self.wire(method,params)
 def batch(self,calls):return [self.call(method,params)for method,params in calls]
 def mutate(self,method,params):
  self.guard()
  if method=='anvil_impersonateAccount':require(params==[SENDER],'Single disposable account')
  elif method=='eth_sendTransaction':
   require(len(params)==1 and params[0]['from']==SENDER,'Single disposable sender')
   if self.phase=='construction':require(params[0].get('value')=='0x0','Construction zero value')
   else:
    require(self.reviewed==params[0],'Exact reviewed owned setup/scenario envelope required')
    self.reviewed=None
  elif method=='evm_setNextBlockTimestamp':require(self.phase=='setup' and len(params)==1 and type(params[0])is int,'Setup-only explicit timestamp')
  elif method=='evm_mine':require(params==[],'Empty owned mine')
  else:require(method in ('evm_snapshot','evm_revert'),'Owned snapshots only')
  return self.wire(method,params,True)

class NativeF6Fixture:
 def __init__(self,output):
  self.output=Path(output).resolve();require(self.output.is_relative_to(WORK.resolve()),'Exclusive new external fixture directory required')
  self.node=None;self.rpc=None;self.receipts=[];self.ids=[];self.contracts={};self.runtime_pins={};self.owner=SENDER
  self.assets=[];self.helpers={};self.created=False
 def prepare(self):
  require(not self.output.exists(),'Preserve previous attempts; new directory required')
  self.output.mkdir(parents=True);self.created=True
  require(sha(ANVIL.read_bytes())==ANVIL_PIN,'Anvil binary pin')
  self.artifacts=P.Artifacts(build_profile=P.DEFAULT_BUILD_PROFILE)
  raw=CACHE.read_bytes();cached=json.loads(raw);self.native={};native=[]
  for role,target in P.NATIVE.items():
   row=cached['accounts'][target];analyzed=row['code']['LegacyAnalyzed'];code=bytes.fromhex(analyzed['bytecode'][2:])[:analyzed['original_len']]
   require(bytes_hash(code)==row['code_hash']==NATIVE_HASHES[role],'Exact native external code hash')
   self.native[role]=code;native.append({'role':role,'address':target,'runtime_hex':'0x'+code.hex(),'original_len':len(code),'runtime_keccak256':bytes_hash(code),'runtime_sha256':sha(code),'inherited_storage_rows':0})
  # Independent retained source9 balance probe proves mapping slot0 for this exact runtime.
  with zipfile.ZipFile(OLD_ZIP)as archive:
   funding=[n for n in archive.namelist()if n.startswith('explicit-external-depth-2/gov-local-funding/')and n.endswith('.json')and 'intent'not in n]
   require(len(funding)==1,'Single native balance source');funding_raw=archive.read(funding[0]);fund=json.loads(funding_raw)
   require(fund['mapping_slot']==0 and fund['token']==P.NATIVE['zzz']and fund['state']=='verified','Exact native funding mapping evidence')
   depth_raw=archive.read('source9-depth-seeder-compile-attempt1/Source9DepthSeeder.object.json');depth=json.loads(depth_raw)
   inp_raw=archive.read('source9-depth-seeder-compile-attempt1/compiler-input.json');inp=json.loads(inp_raw)
   depth_source='test/local/Source9DepthSeeder.sol';current=(ROOT/depth_source).read_bytes()
   require(sha(current)==depth['source_sha256']and inp['sources'][depth_source]['content'].replace('\r\n','\n')==current.decode().replace('\r\n','\n'),'Depth helper exact current source')
   self.helpers['Source9DepthSeeder']=depth['artifact']
   depth_pin={'archive_sha256':sha(OLD_ZIP.read_bytes()),'member':'source9-depth-seeder-compile-attempt1/Source9DepthSeeder.object.json','member_sha256':sha(depth_raw),'compiler_input_sha256':sha(inp_raw),'source':depth_source,'source_sha256':sha(current),'source_content':current.decode()}
  fixture_input_raw=(FIXTURES/'fixture-compiler-input.json').read_bytes();fixture_input=json.loads(fixture_input_raw)
  fixture_output_raw=(FIXTURES/'fixture-compiler-stdout.json').read_bytes();fixture_output=json.loads(fixture_output_raw)
  source='test/local/Source9RehearsalFixtures.sol';current=(ROOT/source).read_bytes()
  require(fixture_input['sources'][source]['content'].replace('\r\n','\n')==current.decode().replace('\r\n','\n'),'Fixture exact current source')
  require(not any(e.get('severity')=='error'for e in fixture_output.get('errors',[])),'Retained helper compiler success')
  self.helpers.update(fixture_output['contracts'][source])
  self.token_artifacts={};token_pins=[]
  for name in ('MockToken','TaxToken'):
   raw_art=(TOKENS/(name+'.json')).read_bytes();artifact=json.loads(raw_art);metadata=artifact['metadata']
   for rel,source_pin in metadata['sources'].items():
    source_path=ROOT/rel
    require(source_path.is_file(),'Token source closure exists: '+rel)
    require(bytes_hash(source_path.read_text(encoding='utf-8').encode())==source_pin['keccak256'],'Token exact current source closure: '+rel)
   self.token_artifacts[name]=artifact
   token_pins.append({'contract':name,'artifact_path':str(TOKENS/(name+'.json')),'artifact_sha256':sha(raw_art),'metadata_sources':metadata['sources']})
  initial,_=M.genesis()
  for role,target in P.NATIVE.items():initial['alloc'][target]={'balance':'0x0','nonce':'0x1','code':'0x'+self.native[role].hex(),'storage':{}}
  initial['alloc'][P.NATIVE['pool_manager']]['storage']['0x'+word(0)]='0x'+word(SENDER)
  # Source-established external constructor fields only. No PoPL storage is seeded.
  pos=initial['alloc'][P.NATIVE['position_manager']]['storage']
  pos.update({'0x'+word(0):short_string('Uniswap v4 Positions NFT'),'0x'+word(1):short_string('UNI-V4-POSM'),'0x'+word(8):'0x'+word(1)})
  bal_slot='0x'+keccak256(bytes.fromhex(word(SENDER)+word(0))).hex()
  initial['alloc'][P.NATIVE['zzz']]['storage'][bal_slot]='0x'+word(100_000_000*UNIT)
  self.initial=initial
  save(self.output/'native-source.json',{'cache_path':str(CACHE),'cache_sha256':sha(CACHE.read_bytes()),'native':native,'no_cached_storage_inherited':True,'external_constructor_defaults':{'core_owner_slot0':SENDER,'position_name_slot0':'Uniswap v4 Positions NFT','position_symbol_slot1':'UNI-V4-POSM','position_next_id_slot8':1,'seadrop_guard_slot0':1},'native_zzz_funding':{'mapping_slot':0,'owner':SENDER,'amount':str(100_000_000*UNIT),'balance_key':bal_slot,'archive_member':funding[0],'archive_member_sha256':sha(funding_raw),'original_verified_evidence':fund,'supply_proof':False}})
  save(self.output/'helper-source.json',{'depth':depth_pin,'fixtures':{'directory':str(FIXTURES),'input_sha256':sha(fixture_input_raw),'output_sha256':sha(fixture_output_raw),'source':source,'source_sha256':sha(current),'source_content':current.decode()},'tokens':token_pins})
  prep={'status':'offline_preparation_only','normal_build':self.artifacts.profile,'normal_artifacts':self.artifacts.file_pins,'normal_source_pins':self.artifacts.source_pins,'construction_runner_sha256':sha((ROOT/'scripts/rehearse-local-deployment.py').read_bytes()),'fixture_sha256':sha(Path(__file__).read_bytes()),'node_started':False,'compiler_run':False,'public_requests':0,'protocol_storage_seeded':False,'expected_nfts':32,'expected_royalty_erc20':64,'tax_currency_explicit_negative_only':True}
  (self.output/'native_fixture.py').write_bytes(Path(__file__).read_bytes())
  save(self.output/'PREPARATION.json',prep);return prep
 def __enter__(self):
  require(self.created,'Call prepare and review before starting node')
  try:
   self.node=OwnedNode(ANVIL,self.output/'node',self.initial);self.node.__enter__();self.rpc=self.node
   self._construct();self._configure();self._populate();self._income();self._manifest();return self
  except BaseException:
   if self.node and self.node.proc and self.node.proc.poll()is None:
    try:self.export_state('FAILURE_STATE_EXPORT.json')
    except BaseException:pass
   self.__exit__(*sys.exc_info());raise
 def _construct(self):
  folder=self.output/'construction';folder.mkdir()
  self.construction=M.Rehearsal(self.node,self.artifacts,folder);result=self.construction.run();save(folder/'RESULT.json',result)
  with gzip.open(folder/'construction-rpc-records.json.gz','wt',encoding='utf-8')as stream:json.dump(self.node.records,stream,separators=(',',':'))
  save(folder/'source-stage.json',{'accepted_build_profile':self.artifacts.profile,'accepted_build_files_sha256':self.artifacts.file_pins,'source_sha256':self.artifacts.source_pins,'tool_sources_sha256':{name:sha((ROOT/name).read_bytes())for name in('scripts/rehearse-local-deployment.py','zzz_ops/deployment_plan.py','zzz_ops/abi.py')},'transport_source':'reports/full-claim-admission-20261120/tools/native_fixture.py','transport_sha256':sha(Path(__file__).read_bytes()),'constructor_mutations_unchanged':True,'native_dependencies_explicit_fresh_genesis':True})
  instances=json.loads((folder/'instances.json').read_text());self.contracts={row['role']:row['address']for row in instances}
  self.runtime_pins={row['role']:row['runtime_keccak256']for row in instances}
  self.contracts.update(P.NATIVE);self.runtime_pins.update(NATIVE_HASHES)
  self.contracts['seadrop']=P.SEADROP;self.runtime_pins['seadrop']=P.SEADROP_HASH
  for alias,role in {'royalties':'royalty_rewards','handoff':'canonical','budget':'migration_budget','principal_exit':'migration','entry':'activation_entry'}.items():
   self.contracts[alias]=self.contracts[role];self.runtime_pins[alias]=self.runtime_pins[role]
  self.deployment_block=int(self.construction.receipts[0]['receipt']['blockNumber'],16)
  self.deployment_block_hash=self.construction.receipts[0]['receipt']['blockHash'];self.node.phase='setup'
  require(self.read(P.NATIVE['position_manager'],'nextTokenId()')[0]==1,'Fresh native PositionManager constructor default')
  require(self.read(P.NATIVE['pool_manager'],'owner()')==[int(SENDER,16)],'Fresh native core owner constructor default')
  require(self.read(P.NATIVE['zzz'],'balanceOf(address)',SENDER)[0]==100_000_000*UNIT,'Explicit native ZZZ balance funding')
 def read(self,target,signature,*args,block='latest'):
  return words(self.rpc.call('eth_call',[{'to':self.contracts.get(target,target),'data':encode(signature,*args)},block]))
 def codehash(self,target):return bytes_hash(bytes.fromhex(self.rpc.call('eth_getCode',[target,'latest'])[2:]))
 def send(self,label,target,payload,*,value=0,cap=24_000_000,padding=2500,creation=False):
  to=self.contracts.get(target,target)if target else None
  tx={'from':SENDER,'data':payload,'value':hex(value),'gas':hex(cap)}
  if to:tx['to']=to
  require(not creation or len(bytes.fromhex(payload[2:]))<=49152,'Creation init size limit')
  self.node.guard();before=self.rpc.call('eth_getTransactionCount',[SENDER,'latest'])
  simulated=self.rpc.call('eth_call',[tx,'latest']);estimate=int(self.rpc.call('eth_estimateGas',[tx]),16)
  padded=(estimate*(10000+padding)+9999)//10000;require(padded<=cap,'Full padded transaction exceeds unchanged cap: '+label)
  tx['gas']=hex(padded);require(self.rpc.call('eth_call',[tx,'latest'])==simulated,'Padded exact simulation differs')
  require(self.rpc.call('eth_getTransactionCount',[SENDER,'latest'])==before,'Simulated nonce changed')
  tx['nonce']=before;tx['gasPrice']=self.rpc.call('eth_gasPrice');self.node.reviewed=copy.deepcopy(tx)
  save(self.output/f'intent-{len(self.receipts)+1:04d}.json',{'label':label,'submitted':tx,'estimate':estimate,'padded':padded,'padding_bps':padding,'cap':cap})
  self.node.pending='submission_uncertain_do_not_resend';txhash=self.node.mutate('eth_sendTransaction',[tx]);self.node.pending=txhash
  receipt=None;until=time.monotonic()+20
  while time.monotonic()<until:
   receipt=self.rpc.call('eth_getTransactionReceipt',[txhash])
   if receipt is not None:break
   time.sleep(.05)
  require(receipt is not None and int(receipt['status'],16)==1,'Included successful receipt required; no resend')
  included=self.rpc.call('eth_getTransactionByHash',[txhash]);require(included['input']==payload and included['nonce']==before and int(included['value'],16)==value and int(included['gas'],16)==padded,'Exact included envelope')
  self.node.pending=None
  row={'label':label,'submitted':tx,'transaction':included,'receipt':receipt,'estimate':estimate,'estimated_gas':estimate,'padded_gas':padded,'padding_bps':padding,'cap':cap,'simulation_return':simulated}
  if creation:
   actual=receipt['contractAddress'].lower();runtime=self.rpc.call('eth_getCode',[actual,'latest']);require(runtime==simulated,'Constructor return runtime differs')
   row['create_trace']=self.rpc.call('debug_traceTransaction',[txhash,{'tracer':'callTracer'}]);self.node.code_pins[actual]=runtime
  self.receipts.append(row);save(self.output/f'tx-{len(self.receipts):04d}.json',row);return row
 def configure(self,role,signature,*args,value=0,cap=24_000_000,padding=2500):return self.send('configure:'+role+':'+signature,role,encode(signature,*args),value=value,cap=cap,padding=padding)
 def deploy(self,role,name,*args,token=False):
  artifact=self.token_artifacts[name]if token else self.helpers[name]
  creation=artifact['bytecode']['object']if token else artifact['evm']['bytecode']['object']
  creation=creation.removeprefix('0x');row=self.send('helper:'+role,None,'0x'+creation+''.join(word(v)for v in args),creation=True)
  target=row['receipt']['contractAddress'].lower();self.contracts[role]=target;self.runtime_pins[role]=self.codehash(target);return target
 def _configure(self):
  key=[ZERO,P.NATIVE['zzz'],10020,200,ZERO];sqrt=math.isqrt(2000*(1<<192))
  self.configure('pool_manager','initialize((address,address,uint24,int24,address),uint160)',*key,sqrt)
  for index in range(3):
   role='external_depth_'+str(index);seeder=self.deploy(role,'Source9DepthSeeder');self.configure('zzz','approve(address,uint256)',seeder,10_000_000*UNIT)
   self.configure(role,'seed(uint128,uint256)',4_000*UNIT,10_000_000*UNIT,value=100*UNIT)
  for role,asset,price in (('eth',ZERO,2000*UNIT),('zzz',P.NATIVE['zzz'],UNIT)):
   pair=[]
   for suffix in ('a','b'):
    target=self.deploy(role+'_feed_'+suffix,'Source9RehearsalFeed',price)
    pair.extend((target,self.codehash(target),bytes_hash(('CORRELATED FIXTURE '+role+suffix).encode()),86400,18))
   self.configure('oracle','setDualFeed(address,(address,bytes32,bytes32,uint32,uint8),(address,bytes32,bytes32,uint32,uint8),uint16,bytes32)',asset,*pair,300,REVIEW)
  self.configure('activation_assets','configureZZZ(address,bytes32,bytes32)',P.NATIVE['zzz'],NATIVE_HASHES['zzz'],REVIEW)
  self.configure('activation_assets','setAsset(address,bool,bytes32,bytes32)',ZERO,1,bytes_hash(b'ZZZ_NATIVE_ETH_V1'),REVIEW)
  self.configure('rewards','addAsset(address)',P.NATIVE['zzz'])
  self.configure('migration','configureZZZ(address,bytes32,bytes32)',P.NATIVE['zzz'],NATIVE_HASHES['zzz'],REVIEW)
  vrf=self.deploy('vrf','Source9RehearsalVRF')
  self.configure('protocol_policy','configureRandomness(address,bytes32,bytes32,uint256,uint16,uint32,bool,bytes32)',vrf,self.codehash(vrf),1,1,3,500000,0,REVIEW)
  now=int(self.rpc.call('eth_getBlockByNumber',['latest',False])['timestamp'],16)
  self.sale_end=now+1800
  config=[0,0,1000,1000,10,1,2,3,4,5,self.sale_end,1,0,FEE,bytes_hash(bytes.fromhex(word(32)+word(0)))]
  self.configure('seadrop_mint','configure((uint16,uint16,uint16,uint16,uint8,uint48,uint48,uint48,uint48,uint48,uint48,bool,bytes32,address,bytes32),uint128,bytes32)',*config,5*10**16,REVIEW)
  self.configure('nft','setMintEnd(uint64)',self.sale_end)
  self.configure('nft','updatePublicDrop(address,(uint80,uint48,uint48,uint16,uint16,bool))',P.SEADROP,5*10**16,5,self.sale_end,1000,1000,1)
  # Dynamic AllowListData: top-level implementation + tuple offset; tuple bytes32/string[]/string.
  body=word(P.SEADROP)+word(64)+word(0)+word(96)+word(128)+word(0)+word(0)
  self.send('configure:nft:updateAllowList','nft','0x'+keccak256(b'updateAllowList(address,(bytes32,string[],string))')[:4].hex()+body)
  self.configure('nft','updateCreatorPayoutAddress(address,address)',P.SEADROP,M.PAYEE)
  self.configure('nft','updateAllowedFeeRecipient(address,address,bool)',P.SEADROP,FEE,1)
  config=[*key,1,1,5000,500,100,200,43200,5*UNIT,1_000_000*UNIT]
  self.configure('pools','configureNative(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))',*config)
  dynamic=encode('configureExecutionPools(bytes32[],bytes32)',64,REVIEW,1,POOL)
  self.send('configure:balancer:executionPools','balancing_router',dynamic)
  self.configure('strategy','setRangeOrientation(bytes32,uint8)',POOL,1)
  self.configure('rebalance_confirmation','configure(uint32,uint32,bytes32)',600,300,REVIEW)
  self.configure('access','setKeeper(address,bool)',SENDER,1)
  # 63 conventional exact-transfer currencies and one explicit tax-failure currency.
  self.configure('nft','increaseRoyaltyAssetCapacity(uint8,bytes32)',64,REVIEW)
  self.royalty_tokens=[]
  for index in range(64):
   target=self.deploy('currency_'+str(index),'TaxToken'if index==63 else'MockToken',*(()if index==63 else(6,)),token=True)
   self.configure('nft','addRoyaltyAsset(address)',target);self.royalty_tokens.append(target)
  self.configure('access','seal()')
  require(self.read('access','isSealed()')==[1]and self.read('access','bootstrap()')==[0],'Actual normal Access seal')
 def _populate(self):
  for quantity in (10,10,10,2):self.configure('seadrop','mintPublic(address,address,address,uint256)',self.contracts['nft'],FEE,ZERO,quantity,value=quantity*5*10**16,cap=CAP)
  for ordinal in range(1,33):
   identifier=self.read('nft','tokenAtOrdinal(uint256)',ordinal)[0];self.ids.append(identifier)
   request=self.read('nft','requestOf(uint256)',identifier)[0]
   self.configure('vrf','fulfill(uint256,uint256,uint256)',request,0,ordinal)
   self.configure('nft','finalizeTraits(uint256)',identifier)
   timestamp=int(self.rpc.call('eth_getBlockByNumber',['latest',False])['timestamp'],16)
   fingerprint=self.read('protocol_policy','entryFingerprint()')[0]
   self.configure('activation_entry','executeReviewed((uint256,bytes32,address,uint256,uint128,uint256,bool),uint16,bytes32)',identifier,POOL,ZERO,55*10**15,1,timestamp+600,0,300,fingerprint,value=55*10**15,cap=CAP,padding=2000)
  self.bucket=self.read('vault','nftBucket(uint256)',self.ids[0])[0]
  require(self.read('nft','mintedCount()')==[32]and self.read('membership','totalEligible()')==[32]and self.read('royalties','activationCount()')==[32],'Actual finite32 population')
 def _income(self):
  self.deploy('external_trader','Source9RehearsalTrader')
  # Native-input actual trade creates ETH-denominated trading fees for the PoPL LP.
  self.configure('external_trader','execute(bool,uint256,uint256,uint160)',1,UNIT//2,1,4295128740,value=UNIT//2)
  timestamp=int(self.rpc.call('eth_getBlockByNumber',['latest',False])['timestamp'],16)
  self.configure('vault','collectFees(uint256,uint256)',self.bucket,timestamp+600)
  require(self.read('rewards','claimable(uint256,address)',self.ids[0],ZERO)[0]>0,'Actual LP ETH fee claim must be funded')
  self.node.mutate('evm_setNextBlockTimestamp',[self.sale_end+3601]);self.node.mutate('evm_mine',[])
  timestamp=int(self.rpc.call('eth_getBlockByNumber',['latest',False])['timestamp'],16)
  for role in ('eth_feed_a','eth_feed_b','zzz_feed_a','zzz_feed_b'):
   price=2000*UNIT if role.startswith('eth')else UNIT
   self.configure(role,'set(int256,uint256,uint256)',price,timestamp,timestamp)
  # Actual marketplace-style ETH receipt; ledger sync allocates whole units.
  self.send('royalty:actual_native_receipt','royalties','0x',value=32*UNIT//10)
  self.configure('royalties','sync(address)',ZERO)
  for index,target in enumerate(self.royalty_tokens):
   self.configure(target,'mint(address,uint256)',self.contracts['royalties'],32*(10**18 if index==63 else 10**6))
   self.configure('royalties','sync(address)',target)
  require(self.read('royalties','assetCount()')==[65]and self.read('royalties','claimable(uint256,address)',self.ids[0],ZERO)[0]>0,'Actual65currency royalty inventory and rights')
 def _manifest(self):
  header=self.rpc.call('eth_getBlockByNumber',['latest',False]);self.assets=[{'address':ZERO,'decimals':18,'symbol':'ETH','code_hash':None},{'address':P.NATIVE['zzz'],'decimals':18,'symbol':'ZZZ','code_hash':NATIVE_HASHES['zzz']}]
  for index,target in enumerate(self.royalty_tokens):self.assets.append({'address':target,'decimals':18 if index==63 else 6,'symbol':'TAX'if index==63 else'R'+str(index),'code_hash':self.runtime_pins['currency_'+str(index)]})
  self.manifest={'schema':1,'chain_id':4663,'normal_build':P.DEFAULT_BUILD_PROFILE,'contracts':self.contracts,'expected_runtime_pins':self.runtime_pins,'owner':self.owner,'ids':[str(i)for i in self.ids],'bucket':str(self.bucket),'assets':self.assets,'deployment_block':self.deployment_block,'deployment_block_hash':self.deployment_block_hash,'configured_block':int(header['number'],16),'configured_block_hash':header['hash'],'clock_timestamp':int(header['timestamp'],16),'active_nfts':32,'royalty_currencies':65,'actual_entry_activations':32,'actual_normal_access_sealed':True,'no_protocol_storage_seeded':True,'no_prior_population_rerun':True,'seams':['exact external native runtime genesis materialization','fresh external constructor defaults','native ZZZ balance substitute, not total supply proof','four correlated controlled price publications','controlled VRF, no proof','synthetic external depth','63 exact-transfer royalty mocks and one taxed currency negative fixture'],'production_approved':False,'public_requests':0,'compiler_run':False}
  save(self.output/'FIXTURE_MANIFEST.json',self.manifest);save(self.output/'setup-transactions.json',self.receipts)
 def export_state(self,name='STATE_EXPORT.json'):
  raw=self.rpc.call('anvil_dumpState',[])
  require(isinstance(raw,str)and re.fullmatch(r'0x[0-9a-fA-F]+',raw),'Actual complete same-source Anvil state export')
  save(self.output/name,{'state_hex':raw,'state_sha256':sha(bytes.fromhex(raw[2:])),'anchor':self.rpc.call('eth_getBlockByNumber',['latest',False]),'normal_build':P.DEFAULT_BUILD_PROFILE,'exact_source_only':True,'no_slot_reinterpretation':True})
  return raw
 def __exit__(self,kind,error,traceback):
  if self.node:self.node.__exit__(kind,error,traceback)
  if self.created and not(self.output/'setup-transactions.json').exists():save(self.output/'setup-transactions.json',self.receipts)
  if error and not(self.output/'FAILURE.json').exists():save(self.output/'FAILURE.json',{'error_type':type(error).__name__,'message':str(error),'completed_setup_transactions':len(self.receipts),'no_automatic_retry':True})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--run',action='store_true');args=parser.parse_args()
 fixture=NativeF6Fixture(args.output);prep=fixture.prepare();print(json.dumps({'status':prep['status'],'path':str(fixture.output)}),flush=True)
 if args.run:
  with fixture:
   fixture.export_state();print(json.dumps({'status':'populated_native_f6_fixture','manifest':str(fixture.output/'FIXTURE_MANIFEST.json')}),flush=True)
if __name__=='__main__':main()
