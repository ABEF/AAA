"""Private fresh-copy setup and exact stock-job recovery; not executed."""
from keeper_jobs import *
BURN_STATE_BYTES=3125
BURN_STATE_SHA='1d662fc392b6ec588fe107b58a80db23b4ac2588f43308e05f4bdeb562784f86'

class Case:
 def __init__(self,name,work,env,addresses,pins,rows,bindings,events):
  self.name=name;self.folder=OUT/name;self.folder.mkdir(mode=0o700);self.model=Model(self.folder,work);self.model.case=self;self.env=env;self.a=addresses;self.pins=pins;self.rows=rows;self.bindings=bindings;self.events=events;self.setup_records=[];self.receipts=[];self.k=None;self.cfg=None;self.lock_guard=None;self.stage='model_start';self.outcome={'feature':name,'status':'incomplete','controlled_copied_state_only':True,'new_seal':False};self.cycles=0
 def target(self,role):return self.a.get(role,role)
 @staticmethod
 def decode(raw):need(type(raw)is str and raw.startswith('0x')and(len(raw)-2)%64==0,'Static job result shape differs');return[int(raw[i:i+64],16)for i in range(2,len(raw),64)]
 def read(self,role,sig,*args):return self.model.rpc('eth_call',[{'to':self.target(role),'data':encode(sig,*args)},'latest'])
 def words(self,role,sig,*args):return self.decode(self.read(role,sig,*args))
 def uint(self,role,sig,*args):v=self.words(role,sig,*args);need(len(v)==1,'Expected one job result');return v[0]
 def now(self):return int(self.model.rpc('eth_getBlockByNumber',['latest',False])['timestamp'],16)
 def advance(self,stamp=None):
  current=self.now();stamp=current+1 if stamp is None else stamp;need(type(stamp)is int and stamp>current and abs(stamp-time.time())<=600,'Controlled timestamp is not fresh/increasing');self.model.rpc('evm_setNextBlockTimestamp',[stamp]);self.model.rpc('evm_mine',[]);need(self.now()==stamp,'Controlled block time differs')
 def start(self):
  from zzz_ops.abi import keccak256
  self.model.start(self.env);self.stage='sealed_graph_identity'
  for row in self.rows:
   code=self.model.rpc('eth_getCode',[row['address'],'latest']);need('0x'+keccak256(bytes.fromhex(code[2:])).hex()==row['runtime_keccak256'].lower(),'New clone runtime differs')
  proofs=[]
  for row in self.bindings:
   if(row['signature']not in B.STATIC_BINDINGS and not(row['role']=='buyback'and row['signature']=='zzz()'))or'expected'not in row:continue
   expected=row['expected'];adapted=row['role']=='access'and row['signature']=='bootstrap()'
   if adapted:expected='0x'+'0'*64
   actual=self.read(row['role'],row['signature'],*row.get('arguments',[]))
   if actual.lower()!=expected.lower():
    save(self.folder/'BINDING_REFUSAL.json',{'role':row['role'],'signature':row['signature'],'constructor_expected':row['expected'],'sealed_expected':expected,'actual':actual});raise B.HarnessRefusal('Sealed binding differs; inspect exact row')
   proofs.append({'role':row['role'],'signature':row['signature'],'actual':actual,'constructor_expected':row['expected'],'sealed_bootstrap_adjustment':adapted})
  need(len(proofs)==91,'All91sealed static probes required');save(self.folder/'BINDINGS.json',proofs)
  need(all(self.uint('access',s)==v for s,v in [('isSealed()',1),('paused()',0),('canonicalState()',0),('lpExitStarted()',0),('preparationActive()',0)])and self.uint('nft','mintedCount()')==2,'Clone lifecycle differs')
  self.ids=[self.uint('nft','tokenAtOrdinal(uint256)',i)for i in(1,2)];self.before_rights=self.rights();self.model.rpc('evm_setIntervalMining',[0]);self.model.rpc('evm_setAutomine',[False]);latest=self.model.rpc('eth_getBlockByNumber',['latest',False]);pending=self.model.rpc('eth_getBlockByNumber',['pending',False]);wall=int(time.time());stamp=max(wall-570 if self.name=='confirmation'else wall+2,int(latest['timestamp'],16)+1,int(pending['timestamp'],16)+1);self.advance(stamp);save(self.folder/'CLOCK_REPAIR.json',{'latest':latest,'pending':pending,'wall':wall,'selected':stamp,'controlled_genesis_timestamp':getattr(self.model,'controlled_genesis_timestamp',None),'freshness_limit_unchanged':True});self.owner_on();self.model.rpc('anvil_setBalance',[OWNER,hex(10**18)])
  self.feeds={r['label'].split(':')[1]:r['receipt']['contractAddress'].lower()for r in B.json_file(LAB/'inputs/entry-receipts.json')if r['label'].startswith('helper:')and'feed_'in r['label']};need(set(self.feeds)=={'eth_feed_a','eth_feed_b','zzz_feed_a','zzz_feed_b'},'Controlled feed identities differ')
  for label,target in sorted(self.feeds.items()):
   values=self.words(target,'latestRoundData()');need(len(values)==5 and 0<values[1]<1<<255,'Controlled feed round differs');stamp=self.now();self.call_setup('refresh_timestamp:'+label,target,'set(int256,uint256,uint256)',values[1],stamp,stamp)
 def owner_on(self):self.model.rpc('anvil_impersonateAccount',[OWNER])
 def setup(self,label,role,data,value=0,creation=False):
  target=None if creation else self.target(role);nonce=self.model.rpc('eth_getTransactionCount',[OWNER,'latest']);need(nonce==self.model.rpc('eth_getTransactionCount',[OWNER,'pending']),'Setup has pending nonce');tx={'from':OWNER,'data':data,'value':hex(value),'gas':hex(24000000),'nonce':nonce}
  if target:tx['to']=target
  sim=self.model.rpc('eth_call',[tx,'latest']);estimate=int(self.model.rpc('eth_estimateGas',[tx]),16);padded=(estimate*125+99)//100;need(padded<=24000000,'Setup exceeds24M/full25%');tx['gas']=hex(padded);h=self.model.rpc('eth_sendTransaction',[tx]);self.advance();receipt=self.model.rpc('eth_getTransactionReceipt',[h]);need(type(receipt)is dict and receipt['status']=='0x1'and receipt['transactionHash']==h,'Setup receipt failed');actual=self.model.rpc('eth_getTransactionByHash',[h]);need(actual['from'].lower()==OWNER and actual['input']==data and actual['nonce']==nonce and int(actual['value'],16)==value,'Setup transaction differs');self.setup_records.append({'label':label,'hash':h,'receipt':receipt,'estimate':estimate,'padded':padded,'envelope':tx});return receipt,sim
 def call_setup(self,label,role,sig,*args,value=0):return self.setup(label,role,encode(sig,*args),value)
 def rights(self):return[{'id':str(i),'owner':self.read('nft','ownerOf(uint256)',i),'shares':self.uint('vault','sharesOf(uint256)',i),'eligible':self.uint('membership','eligible(uint256)',i),'royalty_weight':self.uint('royalty_rewards','weightOf(uint256)',i)}for i in self.ids]
 def physical(self):
  g=self.words('vault','group(uint256)',BUCKET);need(len(g)==8 and g[7]==1,'Active eight-word position required');return{'group':g,'main':g[1],'secondary':self.uint('liquidity','secondaryId(uint256)',g[1]),'ticks':self.words('liquidity','ticks(uint256)',g[1]),'liquidity':self.uint(POSM,'getPositionLiquidity(uint256)',g[1]),'owner':self.read(POSM,'ownerOf(uint256)',g[1])}
 def money(self):return{t:{'compound':self.uint('fees','compoundBalance(uint256,address)',BUCKET,t),'buyback':self.uint('fees','buybackBalance(address)',t),'liabilities':self.uint('rewards','liabilities(address)',t),'claims':[self.words('rewards','claimableComponents(uint256,address)',i,t)for i in self.ids]}for t in(ZERO,ZZZ)}
 def restore_historical_supply(self):
  from zzz_ops.abi import keccak256
  raw=(LAB/'inputs/BURN_STATE.json').read_bytes();need(len(raw)==BURN_STATE_BYTES and sha(raw)==BURN_STATE_SHA,'Reviewed historical supply artifact differs');meta=json.loads(raw)
  need(meta['schema']==1 and meta['chain_id']==4663 and meta['token']==ZZZ and meta['slot']=='0x2'and meta['maximum_state_restore_writes']==1 and meta['restore_only_target_and_slot']is True,'Historical supply restore scope differs')
  need(meta['block_number']==119107223 and meta['block_hash']=='0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335'and int(meta['word'],16)==int(meta['total_supply_decimal'])==840000000000000000000000000,'Historical supply proof identity differs')
  code=self.model.rpc('eth_getCode',[ZZZ,'latest']);actual_runtime='0x'+keccak256(bytes.fromhex(code[2:])).hex();slot=self.model.rpc('eth_getStorageAt',[ZZZ,'0x2','latest']);supply=self.uint(ZZZ,'totalSupply()')
  need(actual_runtime==meta['runtime_keccak256']==meta['new_clone_precondition']['same_runtime_keccak256']and slot==meta['new_clone_precondition']['copied_slot2']and supply==int(meta['new_clone_precondition']['copied_totalSupply'])==0,'Fresh copied token runtime/zero missing-slot precondition differs')
  self.stage='restore_historical_token_supply';self.model.supply_restore_auth=meta['word'];answer=self.model.request({'jsonrpc':'2.0','id':self.model.rpc_count+1,'method':'anvil_setStorageAt','params':[ZZZ,'0x2',meta['word']]});need(answer.get('result')is True and'error'not in answer,'Exact historical supply restore refused')
  restored=self.model.rpc('eth_getStorageAt',[ZZZ,'0x2','latest']);actual_supply=self.uint(ZZZ,'totalSupply()');save(self.folder/'SUPPLY_RESTORE.json',{'scope':'One omitted historical global scalar restored; not complete account/global/fork state','metadata_sha256':sha(raw),'historical_block_number':meta['block_number'],'historical_block_hash':meta['block_hash'],'token':ZZZ,'slot':'0x2','runtime_keccak256':actual_runtime,'before_word':slot,'before_supply':supply,'after_word':restored,'after_supply':actual_supply,'writes':self.model.supply_restore_attempts,'new_clone_only':True,'public_state_unchanged':True})
  need(restored==meta['word']and actual_supply==int(meta['total_supply_decimal'])and self.model.supply_restore_attempts==1,'Restored historical total supply differs')
  self.model.supply_restore_auth=None
 def fee_readback(self):
  quote=int(self.model.rpc('eth_gasPrice',[]),16);tip=int(self.model.rpc('eth_maxPriorityFeePerGas',[]),16);latest=self.model.rpc('eth_getBlockByNumber',['latest',False]);pending=self.model.rpc('eth_getBlockByNumber',['pending',False]);bases=[int(h['baseFeePerGas'],16)for h in(latest,pending)]
  proof={'scope':'Synthetic local fee model, no actual Robinhood fee/provider qualification','gas_price_wei':quote,'suggested_priority_fee_wei':tip,'latest':latest,'pending':pending,'tip_suggestion_not_signed_priority':True,'fixture_quote_and_base_screen_wei':1000};save(self.folder/'FEE_READBACK.json',proof)
  need(0<quote<=1000 and all(0<b<=1000 for b in bases)and tip>=0,'Local fixture fee quote/base not in reviewed1-to1000wei screen')
  return proof
 def burn_money(self):
  result=self.money()
  for asset,row in result.items():
   row.update(dust=self.uint('fees','dust(uint256,address)',BUCKET,asset),accounted=self.uint('fees','accounted(address)',asset),orphaned=self.uint('rewards','orphaned(address)',asset),total_idle=self.uint('vault','totalIdle(address)',asset))
   for name in('fees','rewards','vault','buyback'):
    row[name+'_balance']=int(self.model.rpc('eth_getBalance',[self.a[name],'latest']),16)if asset==ZERO else self.uint(asset,'balanceOf(address)',self.a[name])
  return result
 def configure(self,**updates):
  from keeper.cast_process import run_cast
  folder=self.folder/'actor';folder.mkdir(mode=0o700);secrets=folder/'secrets';secrets.mkdir(mode=0o700);password=secrets/'password';key=secrets/'keeper'
  with password.open('xb')as f:f.write(os.urandom(32).hex().encode()+b'\n')
  password.chmod(0o600);generated=run_cast([str(LAB/'tools/cast'),'wallet','new',str(secrets),'keeper'],env={**self.env,'CAST_PASSWORD':password.read_text().strip()},timeout=30);need(generated.returncode==0 and key.is_file(),'New encrypted signer creation refused');del generated;key.chmod(0o600);found=run_cast([str(LAB/'tools/cast'),'wallet','address','--keystore',str(key),'--password-file',str(password)],env=self.env,timeout=30);need(found.returncode==0,'New signer address refused');self.sender=found.stdout.strip().lower();need(re.fullmatch(r'0x[0-9a-f]{40}',self.sender)is not None and self.sender not in set(self.a.values())|{OWNER},'New signer identity differs');self.model.rpc('anvil_setBalance',[self.sender,hex(10**18)]);self.call_setup('enable_new_keeper','access','setKeeper(address,bool)',self.sender,True)
  roles=('access','vault','strategy','fees','compounder','buyback','pools','rewards','liquidity','balancing_router','lp_balance_math','lp_position_executor','portfolio_policy','protocol_policy','rebalance_confirmation','oracle','contribution_pricing','nft');contracts={r:self.a[r]for r in roles};pins={r:self.pins[r]for r in roles};contracts.update(principal_exit=self.a['migration'],pool_manager=B.CORE,state_view=B.STATE);pins.update(principal_exit=self.pins['migration'],pool_manager=B.CORE_HASH,state_view=B.STATE_HASH,idle_compounding_budget=self.pins['migration_budget'])
  cfg={'chain_id':4663,'accounting_model':'shared-pools-v2','accounting_version':7,'custody_version':5,'protocol_policy_version':1,'portfolio_version':2,'maintenance_policy_version':3,'rebalance_confirmation_version':3,'fee_intake_version':1,'lp_routing_version':3,'execution_quality_version':1,'execution_price_version':1,'royalty_settlement_version':4,'rpc_urls':['http://127.0.0.1:19592'],'sender':self.sender,'contracts':contracts,'code_hashes':pins,'idle_compounding_budget':self.a['migration_budget'],'reviewed_for_live_use':True,'cast_binary':str(LAB/'tools/cast'),'keystore':str(key),'password_file':str(password),'interval_seconds':240,'confirmations':12,'max_gas_limit':24000000,'max_gas_price_wei':'5000000000','max_transaction_cost_wei':'10000000000000000','max_daily_cost_wei':'50000000000000000','l1_fee_allowance_wei':'0','receipt_fee_policy':'included','revert_cooldown_seconds':3600,'state_path':str(folder/'state.json'),'health_path':str(folder/'health.json'),'lock_path':str(folder/'keeper.lock'),'bucket_discovery':{'maximum_count':4,'max_per_cycle':4},'maintenance':{'compound':False,'compound_idle':False,'harvest':False,'minimum_liquidity':1,'harvest_interval_seconds':3600},'bucket_overrides':{},'adaptive_range':{'enabled':False},'royalty_conversion':{'enabled':False},'lp_conversion':{'enabled':False},'metadata_refresh':{'enabled':False},'principal_distribution':{'enabled':False},'buybacks':[]};cfg.update(updates);self.cfg=cfg;self.config_path=folder/'config.json';save(self.config_path,cfg)
  allowed={'compound':[('compound','compounder','compound(uint256,uint128,uint256)')],'buyback':[('buyback','buyback','execute(address,uint256,bytes32,uint256)')],'metadata':[('metadata','nft','refreshMetadataRange(uint256,uint256)')],'roles':[('harvest','vault','collectFees(uint256,uint256)')],'rpc_fault':[('harvest','vault','collectFees(uint256,uint256)')]}.get(self.name,[])
  if self.name in('metadata','conversion'):
   floor=self.model.rpc('eth_getBlockByNumber',['latest',False])
   for _ in range(12):self.advance()
   tip=self.model.rpc('eth_getBlockByNumber',['latest',False]);confirmed=self.model.rpc('eth_getBlockByNumber',[hex(int(tip['number'],16)-11),False]);need(type(confirmed)is dict and int(confirmed['number'],16)>=int(floor['number'],16),'Confirmed metadata anchor predates fresh setup');save(self.folder/'CONFIRMED_ANCHOR.json',{'setup_floor':floor,'confirmed':confirmed,'tip':tip,'confirmations':12,'new_genuine_blocks':12,'old_missing_history_not_adopted':True})
  self.model.review={'config':self.config_path,'config_sha':sha(self.config_path.read_bytes()),'journal':Path(cfg['state_path']),'sender':self.sender,'allowed':allowed,'burn_amount':getattr(self,'burn_amount',None)};self.model.gateway_start();from keeper.monitor import Keeper
  from zzz_ops.state import process_lock
  self.lock_guard=process_lock(cfg['lock_path']);self.lock_guard.__enter__()
  with contextlib.redirect_stdout(self.events),contextlib.redirect_stderr(self.events):initial=Keeper(cfg,live=False);initial.initialize_state();self.k=Keeper(cfg,live=True)
  self.model.rpc('anvil_stopImpersonatingAccount',[OWNER])
 def cycle(self):
  with contextlib.redirect_stdout(self.events),contextlib.redirect_stderr(self.events):success=self.k.run_cycle()
  state=B.json_file(Path(self.cfg['state_path']));health=B.json_file(Path(self.cfg['health_path']));self.cycles+=1;save(self.folder/f'CYCLE-{self.cycles:02d}.json',{'success':success,'health':health,'state':state});return state.get('pending')
 def settle(self,p,*,fault=False):
  need(type(p)is dict and type(p.get('hash'))is str,'Expected durable stock transaction hash');h=p['hash'];tx=self.model.rpc('eth_getTransactionByHash',[h]);need(tx['from'].lower()==self.sender and tx['to'].lower()==p['to']and tx['input']==p['data']and int(tx['nonce'],16)==p['nonce']and int(tx['value'],16)==0,'Actual signed stock transaction differs')
  if fault:
   before=Path(self.cfg['state_path']).read_bytes();self.model.fault={'method':'eth_getTransactionReceipt','params':[h]}
   with contextlib.redirect_stdout(self.events),contextlib.redirect_stderr(self.events):failed=self.k.run_cycle()
   self.model.fault=None;need(not failed and Path(self.cfg['state_path']).read_bytes()==before,'Receipt read fault altered pending intent')
  self.advance();receipt=self.model.rpc('eth_getTransactionReceipt',[h]);save(self.folder/f'RAW_RECEIPT-{len(self.receipts)+1:02d}.json',receipt);need(type(receipt)is dict and receipt['status']=='0x1','Actual stock job reverted; inspect retained receipt')
  mining=self.model.mine_empty_descendants(receipt)
  count=self.model.raw_send_count
  with contextlib.redirect_stdout(self.events),contextlib.redirect_stderr(self.events):pending=self.k.poll_pending()
  need(pending is False and self.k.state['pending']is None and self.k.state['next_nonce']==p['nonce']+1 and self.model.raw_send_count==count,'Stock receipt recovery resent/lost nonce');self.receipts.append({'action':p['key'],'hash':h,'receipt':receipt,'intent':p,'actual_transaction_checked':True,'confirmations':12,'fault_recovery':fault,'descendant_mining':mining});return receipt
 def fees_setup(self):
  meta=B.json_file(LAB/'inputs/TRADER.json');need(meta['operator']==OWNER,'Retained actual trader operator differs');receipt,_=self.setup('new_external_trader',None,meta['creation'],creation=True);trader=receipt['contractAddress'].lower();runtime=self.model.rpc('eth_getCode',[trader,'latest']);need(runtime.lower()==meta['expected_runtime'].lower(),'Authenticated actual trader runtime differs');r,out=self.call_setup('genuine_native_trade',trader,'execute(bool,uint256,uint256,uint160)',True,10**15,1,4295128740,value=10**15);amount=int(out,16)//2;need(amount>0,'Actual trader returned no ZZZ');self.call_setup('exact_reverse_approval',ZZZ,'approve(address,uint256)',trader,amount);self.call_setup('genuine_ZZZ_trade',trader,'execute(bool,uint256,uint256,uint160)',False,amount,1,1461446703485210103287273052203988822378723970341)
  need(self.uint(ZZZ,'allowance(address,address)',OWNER,trader)==0 and self.uint(ZZZ,'balanceOf(address)',trader)==0 and int(self.model.rpc('eth_getBalance',[trader,'latest']),16)==0,'Controlled trader did not settle exactly');self.call_setup('fund_actual_fee_reserves','vault','collectFees(uint256,uint256)',BUCKET,self.now()+180)
 def close(self):
  try:
   self.outcome.update(last_stage=self.stage,setup_transactions=len(self.setup_records),stock_transactions=len(self.receipts),RPC_requests=self.model.rpc_count,raw_attempts=self.model.raw_send_count,raw_forwarded=self.model.raw_forwarded,fault_attempts=self.model.fault_attempts,gateway_refusals=self.model.gateway_refusals,last_model_RPC_failure=self.model.last_rpc_failure,RPC_method_counts=self.model.method_counts,RPC_phase_counts=self.model.phase_counts,actual_signed_envelope_predecoded=False,postforward_exact_transaction_verification_required=True);save(self.folder/'SETUP.json',self.setup_records);save(self.folder/'RECEIPTS.json',self.receipts);save(self.folder/'RAW_REVIEWS.json',self.model.raw_records);save(self.folder/'RESULT.json',self.outcome)
  finally:
   try:cleanup=self.model.close()
   finally:
    if self.lock_guard is not None:self.lock_guard.__exit__(None,None,None);self.lock_guard=None
  return cleanup
