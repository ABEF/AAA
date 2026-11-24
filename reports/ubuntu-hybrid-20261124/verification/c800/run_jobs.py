"""NEW one->two->one stock-keeper functional roundtrip only.
A declared fixed-offset lab clock models12h, not wall-clock daemon qualification.
No production edit/financial safeguard/time-limit or on-chain clock bypass.
"""
from job_cases import *
import math

class HybridCase(Case):
 def configure(self,**updates):
  super().configure(**updates);self.model.review['allowed']=[('rebalance','vault','rebalance(uint256,uint128,uint256)')]
 def fee_readback(self):
  quote=self.model.rpc('eth_gasPrice',[]);tip=self.model.rpc('eth_maxPriorityFeePerGas',[]);head=self.model.rpc('eth_getBlockByNumber',['latest',False]);pending=self.model.rpc('eth_getBlockByNumber',['pending',False])
  # Preserve actual node responses BEFORE any input-range/shape assumption.
  # The original loaded header can override CLI fee defaults; c7f9 observed
  #329wei latest/312wei pending in its captured CLOCK_REPAIR, not <=100wei.
  save(self.folder/'CONTROLLED_FEES.json',{'raw_gas_price':quote,'raw_node_suggested_priority_fee':tip,'priority_suggestion_is_not_signed_cap':True,'latest_head':head,'pending_head':pending,'flags':['--gas-price','1','--block-base-fee-per-gas','1','--disable-min-priority-fee'],'synthetic_model_economics_not_Robinhood_fee_qualification':True,'gas_fee_cost_caps_unchanged':True,'test_input_screen_maximum_wei':1000,'maximum_24M_gas_cost_at_screen_wei':24000000*1000,'prior_refusals_preserved':True})
  def q(value):
   need(type(value)is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})',value)is not None,'Canonical controlled fee quantity');return int(value,16)
  gas=q(quote);priority=q(tip);base=q(head.get('baseFeePerGas'));pending_base=q(pending.get('baseFeePerGas'))
  need(0<gas<=1000 and 0<base<=1000 and 0<pending_base<=1000,'Controlled fixture fee input screen differs; actual values retained')
 def refresh_reference(self,root):
  eth=self.words(self.feeds['eth_feed_a'],'latestRoundData()')[1];answer=eth*(1<<192)//(root*root);need(0<answer<1<<255,'Controlled reference magnitude differs');self.owner_on()
  for label in('zzz_feed_a','zzz_feed_b'):
   stamp=self.now();self.call_setup('controlled_reference:'+label,self.feeds[label],'set(int256,uint256,uint256)',answer,stamp,stamp)
  self.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);return answer
 def new_trader(self):
  self.owner_on();meta=B.json_file(LAB/'inputs/TRADER.json');r,_=self.setup('new_genuine_market_trader',None,meta['creation'],creation=True);self.trader=r['contractAddress'].lower();need(self.model.rpc('eth_getCode',[self.trader,'latest']).lower()==meta['expected_runtime'].lower(),'Retained actual trader runtime differs')
 def quote(self,amount,direction=True):
  before=self.read(B.STATE,'getSlot0(bytes32)',POOL);q={'from':self.a['liquidity'],'to':self.a['balancing_router'],'data':encode('quoteSwap(bytes32,bool,uint256)',POOL,direction,amount),'gas':hex(24000000)};value=self.model.rpc('eth_call',[q,'latest']);words=self.decode(value);need(len(words)==6 and words[0]>0 and words[1]>0,'Actual core quote shape differs');need(self.read(B.STATE,'getSlot0(bytes32)',POOL)==before,'Read-only quote persisted core state');return words
 def move_to_trigger(self):
  from zzz_ops.tick_math import sqrt_price_at_tick
  before=self.physical();center=before['group'][5];low,high=before['ticks'];a=sqrt_price_at_tick(low);unit=10**18;root=(center*unit+a-1)//a;boundary=(root*root+unit-1)//unit;limit=unit+((boundary-unit)*self.uint('portfolio_policy','thresholdBps()')+9999)//10000;edge=math.isqrt(center*center*unit//limit);target=edge*9995//10000;inside=edge*10005//10000
  need(self.uint('portfolio_policy','thresholdSide(uint160,int24,int24,uint160)',center,low,high,target)==1 and self.uint('portfolio_policy','thresholdSide(uint160,int24,int24,uint160)',center,low,high,inside)==0,'Exact price-space trigger projections differ');self.new_trader();self.model.rpc('anvil_setBalance',[OWNER,hex(512*10**18)]);lo=0;hi=10**18;quotes=[]
  for _ in range(10):
   quoted=self.quote(hi);quotes.append({'input':str(hi),'output':str(quoted[0]),'after_sqrt':str(quoted[1])})
   if quoted[1]<=target:break
   lo=hi;hi*=2
  else:raise FeatureBlocked('Retained synthetic depth did not reach trigger within512ETH')
  for _ in range(32):
   mid=(lo+hi)//2
   if mid<=lo:break
   got=self.quote(mid);quotes.append({'input':str(mid),'output':str(got[0]),'after_sqrt':str(got[1])})
   if got[1]<=target:hi=mid;quoted=got
   else:lo=mid
  quoted=self.quote(hi);r,output=self.call_setup('actual_market_move_to_trigger',self.trader,'execute(bool,uint256,uint256,uint160)',True,hi,1,4295128740,value=hi);slot=self.words(B.STATE,'getSlot0(bytes32)',POOL);need(int(output,16)==quoted[0]and slot[0]==quoted[1],'Actual trade differs from exact core quote');need(self.uint('portfolio_policy','thresholdSide(uint160,int24,int24,uint160)',center,low,high,slot[0])==1,'Actual market did not reach trigger');save(self.folder/'MARKET_MOVE.json',{'before':before,'quotes':quotes,'actual_input':str(hi),'actual_after_slot0':slot,'target_sqrt':str(target),'inside_reference_sqrt':str(inside),'read_only_quote_caller':self.a['liquidity'],'privileged_caller_probe_not_a_transaction':True,'real_core_swap':r['transactionHash'],'controlled_depth_not_external_market_qualification':True});return before,slot[0],inside
 def make_residual_mixed(self,two):
  from zzz_ops.tick_math import sqrt_price_at_tick
  residual=two['legs'][1];target=sqrt_price_at_tick(sum(residual['ticks'])//2);current=self.words(B.STATE,'getSlot0(bytes32)',POOL)[0];direction=target<current;self.owner_on();maximum=256*10**18 if direction else min(self.uint(ZZZ,'balanceOf(address)',OWNER),100000000*10**18);lo=0;hi=min(10**15 if direction else 100*10**18,maximum);need(hi>0,'No external caller inventory for residual trade');quotes=[]
  reached=lambda root:root<=target if direction else root>=target
  for _ in range(24):
   quoted=self.quote(hi,direction);quotes.append({'input':str(hi),'after_sqrt':str(quoted[1])})
   if reached(quoted[1]):break
   lo=hi;hi=min(hi*2,maximum)
   if hi==lo:raise FeatureBlocked('Explicit external trader budget cannot reach residual interior')
  else:raise FeatureBlocked('Residual interior quote did not converge within24bounded expansions')
  for _ in range(24):
   mid=(lo+hi)//2
   if mid<=lo:break
   quoted=self.quote(mid,direction);quotes.append({'input':str(mid),'after_sqrt':str(quoted[1])})
   if reached(quoted[1]):hi=mid
   else:lo=mid
  quoted=self.quote(hi,direction)
  if not direction:self.call_setup('exact_external_mixed_residual_approval',ZZZ,'approve(address,uint256)',self.trader,hi)
  receipt,output=self.call_setup('actual_external_trade_into_residual',self.trader,'execute(bool,uint256,uint256,uint160)',direction,hi,1,4295128740 if direction else 1461446703485210103287273052203988822378723970341,value=hi if direction else 0);slot=self.words(B.STATE,'getSlot0(bytes32)',POOL);tick=slot[1]-(1<<256)if slot[1]>>255 else slot[1];need(int(output,16)==quoted[0]and slot[0]==quoted[1]and residual['ticks'][0]<tick<residual['ticks'][1],'Real trade did not reach residual interior as quoted');need(self.uint(ZZZ,'balanceOf(address)',self.trader)==0 and int(self.model.rpc('eth_getBalance',[self.trader,'latest']),16)==0 and self.uint(ZZZ,'allowance(address,address)',OWNER,self.trader)==0,'External trader retained funds or approval')
  eth=self.words(self.feeds['eth_feed_a'],'latestRoundData()')[1];zzz=eth*(1<<192)//(slot[0]*slot[0])
  for label,feed in sorted(self.feeds.items()):values=self.words(feed,'latestRoundData()');stamp=self.now();self.call_setup('refresh_after_mixed_trade:'+label,feed,'set(int256,uint256,uint256)',zzz if label.startswith('zzz_')else values[1],stamp,stamp)
  self.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);mixed=self.snapshot();save(self.folder/'MIXED_RESIDUAL.json',{'before':two,'after':mixed,'real_core_trade':receipt,'native_input':direction,'input':str(hi),'target_sqrt':str(target),'quotes':quotes,'controlled_correlated_feeds_not_real_sources':True});need(mixed['group']==two['group']and [leg['id']for leg in mixed['legs']]==[leg['id']for leg in two['legs']]and all(a['liquidity']==b['liquidity']for a,b in zip(mixed['legs'],two['legs']))and all(v>0 for v in mixed['legs'][1]['amounts']),'Market trade did not leave same two live legs with a mixed residual');return mixed

 def snapshot(self):
  from zzz_ops.abi import keccak256
  from zzz_ops.physical_portfolio import physical_amounts,portfolio_fingerprints
  group=self.words('vault','group(uint256)',BUCKET);main=group[1];secondary=self.uint('liquidity','secondaryId(uint256)',main);slot=self.words(B.STATE,'getSlot0(bytes32)',POOL);signed24=lambda v:(v&((1<<24)-1))-(1<<24)if v&(1<<23)else v&((1<<24)-1);legs=[]
  for token in [main]+([secondary]if secondary else[]):
   owner=self.read(POSM,'ownerOf(uint256)',token);info=self.words(POSM,'getPoolAndPositionInfo(uint256)',token);liq=self.uint(POSM,'getPositionLiquidity(uint256)',token);need(len(info)==6 and '0x'+keccak256(bytes.fromhex(''.join(f'{v:064x}'for v in info[:5]))).hex()==POOL,'Captured full LP key differs');ticks=[signed24(info[5]>>8),signed24(info[5]>>32)];amounts=self.words('liquidity','amounts(uint256)',token);need(amounts==physical_amounts(slot[0],ticks,liq),'Physical rounded amounts differ from independent LP geometry');legs.append({'id':token,'owner':owner,'full_key':info[:5],'position_info':info[5],'ticks':ticks,'liquidity':liq,'amounts':amounts})
  amounts=self.words('liquidity','portfolioAmounts(uint256)',main);need(amounts==[sum(x['amounts'][i]for x in legs)for i in(0,1)],'Portfolio does not sum both legs assetwise');fingerprints=portfolio_fingerprints(executor=self.a['lp_position_executor'],position_manager=POSM,vault=self.a['vault'],pool=POOL,main=(main,legs[0]['position_info'],legs[0]['liquidity']),secondary=None if not secondary else(secondary,legs[1]['position_info'],legs[1]['liquidity']));need([self.read('liquidity',s,main)for s in('portfolioFingerprint(uint256)','executionPortfolioFingerprint(uint256)')]==list(fingerprints),'Stable/execution fingerprint differs')
  funds={};prices={}
  for index,asset in enumerate((ZERO,ZZZ)):
   row={'dust':self.uint('fees','dust(uint256,address)',BUCKET,asset),'compound':self.uint('fees','compoundBalance(uint256,address)',BUCKET,asset),'buyback':self.uint('fees','buybackBalance(address)',asset),'accounted':self.uint('fees','accounted(address)',asset),'liabilities':self.uint('rewards','liabilities(address)',asset),'orphaned':self.uint('rewards','orphaned(address)',asset),'direct_liabilities':self.uint('rewards','directLiabilities(address)',asset),'total_idle':self.uint('vault','totalIdle(address)',asset),'claims':[self.words('rewards','claimableComponents(uint256,address)',n,asset)for n in self.ids]}
   for role in('fees','rewards','vault'):row[role+'_balance']=int(self.model.rpc('eth_getBalance',[self.a[role],'latest']),16)if asset==ZERO else self.uint(ZZZ,'balanceOf(address)',self.a[role])
   need(row['accounted']==row['dust']+row['compound']+row['buyback']and row['fees_balance']>=row['accounted']and row['rewards_balance']>=row['liabilities']+row['orphaned']and row['vault_balance']>=row['total_idle']and row['total_idle']==group[2+index],'Classified physical backing/idle differs');funds[asset]=row;prices[asset]={'bounds':self.words('oracle','priceBounds(address)',asset),'scale':10**self.uint('oracle','tokenDecimals(address)',asset)}
  return {'group':group,'legs':legs,'slot0':slot,'portfolio_amounts':amounts,'fingerprints':list(fingerprints),'active_secondary_count':self.uint('liquidity','activeSecondaryCount()'),'rights':self.rights(),'total_shares':str(self.uint('vault','bucketTotalShares(uint256)',BUCKET)),'funds':funds,'prices':prices,'policy':{'enabled':self.uint('portfolio_policy','enabled(bytes32)',POOL),'geometry':self.uint('portfolio_policy','geometryRevision(bytes32)',POOL),'applied':self.uint('portfolio_policy','appliedRevision(uint256)',main),'pending':self.uint('portfolio_policy','configurationPending(uint256)',BUCKET),'main_floor':self.uint('portfolio_policy','minimumMainBps(bytes32)',POOL),'residual_side':self.uint('portfolio_policy','residualSideBps(bytes32)',POOL),'residual_gap':self.uint('portfolio_policy','residualGapSpacings(bytes32)',POOL)}}
 def toggle(self,next_,tag,before=None):
  from zzz_ops.abi import keccak256
  before=self.snapshot()if before is None else before;self.owner_on();review='0x'+keccak256(('c7ff new isolated hybrid '+tag).encode()).hex();self.call_setup('governance_desired_mode_'+tag,'portfolio_policy','setMode(bytes32,bool,bytes32)',POOL,next_,review);self.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);after=self.snapshot();save(self.folder/('TOGGLE_'+tag+'.json'),{'before':before,'after':after,'review_hash':review,'setting_only_not_execution':True})
  need(after['group']==before['group']and after['legs']==before['legs']and after['funds']==before['funds']and after['rights']==before['rights']and after['policy']['enabled']==int(next_)and after['policy']['pending']==1,'Mode toggle moved assets or failed to mark desired geometry');return after
 def apply_mode(self,tag,before=None):
  before=self.snapshot()if before is None else before;sender_before=int(self.model.rpc('eth_getBalance',[self.sender,'latest']),16);spent_before=sum(int(v)for v in self.k.state['spent'].values());start_count=self.model.raw_send_count;save(self.folder/('BEFORE_'+tag+'.json'),{'snapshot':before,'sender_balance':str(sender_before),'spent':str(spent_before)})
  need(self.cycle()is None and self.model.raw_send_count==start_count,'Mode adjustment skipped fresh jitter');schedule=copy.deepcopy(self.k.state['observed_adjustment_v3'][str(BUCKET)]);delay=schedule['execute_after']-schedule['observed_at'];need(60<=delay<=300,'Fresh geometry jitter missing');self.advance(schedule['execute_after']);pending=self.cycle()
  if pending is None:raise FeatureBlocked('Mode adjustment not submitted; actual unchanged stock diagnostics retained')
  need(pending['key']=='rebalance:'+str(BUCKET),'Non-rebalance job selected');receipt=self.settle(pending);after=self.snapshot();actual=self.model.rpc('eth_getTransactionByHash',[pending['hash']]);header=self.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);sender_after=int(self.model.rpc('eth_getBalance',[self.sender,'latest']),16);fee=copy.deepcopy(self.k.state['last_fee_observation']);fields={k:actual.get(k)for k in('hash','from','to','input','nonce','value','gas','gasPrice','type','chainId','maxFeePerGas','maxPriorityFeePerGas','blockHash','blockNumber')};save(self.folder/('AFTER_'+tag+'.json'),{'snapshot':after,'receipt':receipt,'actual_transaction_without_signature':fields,'header':header,'sender_balance':str(sender_after),'spent':str(sum(int(v)for v in self.k.state['spent'].values())),'canonical_fee':fee,'schedule':schedule})
  self.reconcile(before,after,receipt,actual,header,pending,sender_before,sender_after,spent_before,tag);return after,schedule
 def reconcile(self,before,after,receipt,actual,header,pending,sender_before,sender_after,spent_before,tag):
  from zzz_ops.abi import keccak256
  from zzz_ops.ethereum_fees import execution_price
  topic=lambda name:'0x'+keccak256(name.encode()).hex();vault=self.a['vault'];fee_events=[self.decode(x['data'])for x in receipt['logs']if x['address'].lower()==vault and x['topics'][0]==topic('FeesCollected(uint256,uint256,uint256)')and int(x['topics'][1],16)==BUCKET];need(fee_events and all(len(x)==2 for x in fee_events),'Rebalance did not record actual fee collection');alloc={}
  for index,asset in enumerate((ZERO,ZZZ)):
   old=before['funds'][asset];new=after['funds'][asset];dust=old['dust'];units=0
   for event in fee_events:total=dust+event[index];units+=total//20;dust=total%20
   harvested=sum(x[index]for x in fee_events);released=old['compound']+units-new['compound'];credited=[self.decode(x['data'])for x in receipt['logs']if x['address'].lower()==self.a['rewards']and x['topics'][0]==topic('PoolRewardsCredited(uint256,address,uint256,uint256)')and int(x['topics'][1],16)==BUCKET and int(x['topics'][2],16)==int(asset,16)];need(all(len(x)==2 for x in credited)and sum(x[0]for x in credited)==16*units and sum(x[1]for x in credited)==2*units,'Exact80percent individual/10percent collective credit events differ');need(new['compound']==0 and released==old['compound']+units and new['buyback']==old['buyback']+units and new['dust']==dust and new['accounted']==old['accounted']+harvested-18*units-released and new['fees_balance']==old['fees_balance']+harvested-18*units-released,'Actual fee80/10/5/5/dust/reserve debit differs');need(new['liabilities']==old['liabilities']+18*units and new['rewards_balance']==old['rewards_balance']+18*units and new['orphaned']==old['orphaned']and new['direct_liabilities']==old['direct_liabilities']and sum(sum(x)for x in new['claims'])==sum(sum(x)for x in old['claims'])+18*units,'Funded aggregate whole-unit holder rewards differ');alloc[asset]={'harvested':harvested,'allocation_units':units,'compound_released':released,'dust_after':dust,'holder_credit':18*units,'scope':'aggregate independent conservation, not fresh per-NFT phase oracle'}
  need(after['rights']==before['rights']==self.before_rights and after['total_shares']==before['total_shares']and after['group'][0]==before['group'][0]and after['group'][6]==int(header['timestamp'],16)and after['policy']['pending']==0 and after['policy']['applied']==after['policy']['geometry'],'Replacement changed NFT rights or failed actual geometry commit')
  rebalanced=[x for x in receipt['logs']if x['address'].lower()==vault and x['topics'][0]==topic('Rebalanced(uint256,uint256,uint256,uint160)')and int(x['topics'][1],16)==BUCKET];need(len(rebalanced)==1 and self.decode(rebalanced[0]['data'])==[before['legs'][0]['id'],after['legs'][0]['id'],after['group'][5]]and not(set(leg['id']for leg in before['legs'])&set(leg['id']for leg in after['legs'])),'Exact old/new main replacement event or fresh IDs differ')
  active_tick=after['slot0'][1];active_tick=active_tick-(1<<256)if active_tick>>255 else active_tick;need(after['legs'][0]['ticks'][0]<=active_tick<after['legs'][0]['ticks'][1]and all(leg['owner']=='0x'+f"{int(vault,16):064x}"for leg in after['legs']),'Active main/custody differs')
  burned={int(x['topics'][3],16)for x in receipt['logs']if x['address'].lower()==POSM and x['topics'][0]==topic('Transfer(address,address,uint256)')and int(x['topics'][1],16)==int(vault,16)and int(x['topics'][2],16)==0};need({leg['id']for leg in before['legs']}<=burned and self.uint('liquidity','secondaryId(uint256)',before['legs'][0]['id'])==0,'Old portfolio was not completely burned/association cleared')
  price=before['prices'];value=lambda amounts:sum(amounts[i]*price[asset]['bounds'][0]//price[asset]['scale']for i,asset in enumerate((ZERO,ZZZ)));main=value(after['legs'][0]['amounts']);residual=0 if len(after['legs'])==1 else value(after['legs'][1]['amounts']);idle=value(after['group'][2:4]);total=main+residual+idle;floor=after['policy']['main_floor'];need(main>0 and total>0,'New principal value absent')
  if tag=='ON':need(len(after['legs'])==2 and after['legs'][1]['id']!=after['legs'][0]['id']and after['active_secondary_count']==before['active_secondary_count']+1 and main>=(total*floor+9999)//10000 and residual<=total*(10000-floor)//10000 and sum(v>0 for v in after['legs'][1]['amounts'])==1,'Actual nonzero one-sided residual/60-40 allocation absent')
  else:need(len(before['legs'])==2 and len(after['legs'])==1 and after['active_secondary_count']==0,'OFF merge failed to remove both-leg association')
  if tag=='ON':
   residual_leg=after['legs'][1];main_leg=after['legs'][0];gap=after['policy']['residual_gap']*main_leg['full_key'][3];need(main_leg['ticks'][0]<=residual_leg['ticks'][0]<residual_leg['ticks'][1]<=main_leg['ticks'][1]and after['policy']['residual_side']==5000 and((residual_leg['amounts'][0]>0 and residual_leg['ticks'][0]-active_tick>=gap)or(residual_leg['amounts'][1]>0 and active_tick-residual_leg['ticks'][1]>=gap)),'Residual is not half-side policy/contained/atleast configured positive tick gap')
  canonical=execution_price(actual,header,receipt);charge=int(receipt['gasUsed'],16)*canonical;need(charge==sender_before-sender_after==self.k.state['last_fee_observation']['cost_wei']==sum(int(v)for v in self.k.state['spent'].values())-spent_before<=pending['fee_review']['maximum_cost_wei']and int(actual['gas'],16)==pending['fee_review']['gas_limit']<=24000000,'Canonical charged fee/spend/cap mismatch');save(self.folder/('REVIEW_'+tag+'.json'),{'fee_allocation':alloc,'main_value':str(main),'residual_value':str(residual),'idle_value':str(idle),'total_postcost_principal':str(total),'main_floor_bps':floor,'canonical_price_wei':canonical,'provider_reported_price_wei':int(receipt['effectiveGasPrice'],16),'canonical_charge_wei':str(charge),'burned_old_ids':sorted(burned),'exact_NFT_rights_unchanged':True})

def roundtrip(c,clock):
 from zzz_ops.rpc import RpcError
 c.stage='controlled_fee_readback';c.fee_readback();c.stage='actual_market_move';_,spot,_=c.move_to_trigger();c.refresh_reference(spot);c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);c.stage='stock_configuration';c.owner_on();c.configure();need(c.uint('vault','bucketCount()')==1 and c.uint('liquidity','activeSecondaryCount()')==0,'Fixture must start with exactlyone bucket/no global secondary');c.stage='governance_mode_ON';on=c.toggle(True,'ON');c.stage='stock_guarded_mode_ON';two,first=c.apply_mode('ON',on)
 c.stage='actual_market_into_residual';mixed=c.make_residual_mixed(two);c.stage='governance_mode_OFF';c.toggle(False,'OFF',mixed);c.stage='hard_cooldown_negative';count=c.model.raw_send_count;need(c.uint('strategy','needsRebalance(uint256)',BUCKET)==0 and c.cycle()is None and c.model.raw_send_count==count==1,'New modeOFF bypassed hard12h cooldown');old_head=c.model.rpc('eth_getBlockByNumber',['latest',False]);need(int(old_head['timestamp'],16)<two['group'][6]+43200,'Unexpected elapsed12h before logical transition')
 c.stage='fixed_logical_clock_transition';transition=clock.shift_once(c);globals()['time']=clock;stale_rejected=False
 try:c.k._head()
 except RpcError:stale_rejected=True
 need(stale_rejected,'Changing model UTC must not make old chain head fresh');transition['old_chain_head_rejected_by_unchanged_stock_head']=True;c.advance(int(old_head['timestamp'],16)+43200);c.owner_on()
 for label,target in sorted(c.feeds.items()):values=c.words(target,'latestRoundData()');stamp=c.now();c.call_setup('fresh_after12h:'+label,target,'set(int256,uint256,uint256)',values[1],stamp,stamp)
 c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);transition['new_chain_head']=c.model.rpc('eth_getBlockByNumber',['latest',False]);transition['unchanged_hard_cooldown_seconds']=43200;save(c.folder/'LOGICAL_CLOCK_TRANSITION.json',transition);need(c.uint('strategy','needsRebalance(uint256)',BUCKET)==1,'Actual12h pending geometry did not become ready');c.stage='stock_guarded_mode_OFF';one,second=c.apply_mode('OFF');need(first['identity']!=second['identity']and first['observed_at']<second['observed_at']and c.model.raw_send_count==c.model.raw_forwarded==2,'Second application reused old schedule identity or unexpected broadcasts');c.outcome.update(status='passed',first_schedule=first,second_schedule=second,main_and_residual_ids=[x['id']for x in two['legs']],final_main=one['legs'][0]['id'],logical_clock_offset=43200,source_guards_and_onchain_timers_unchanged=True,wallclock_qualification=False,independent_per_NFT_phase_oracle_requalified=False)

JOBS=[('hybrid',roundtrip)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--base-sha256',required=True);p.add_argument('--trader-sha256',required=True);args=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed private LP helper path');need(sha(Path(B.__file__).read_bytes())==args.base_sha256 and sha((LAB/'inputs/TRADER.json').read_bytes())==args.trader_sha256,'Frozen helper/input differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256)
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast bytes differ');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);clock=LogicalClock();seams=clock.install();globals()['time']=clock;work=Work();events=Events();result={'schema':1,'scope':'NEW one-to-two-to-one actual stock keeper roundtrip; explicit fixed12h logical UTC facade, not wall-clock daemon/soak; copied sealed F6, real core and synthetic low fees','success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'features':[],'cleanup':[],'production_approved':False,'all_enabled_jobs_qualified':False,'unexecuted':['continuous_daemon_timing','sample_reset_job_after_new_market_recovery','different_key_rotation']}
 for name,fn in JOBS:
  case=None;common_failed=False
  try:
   need(work.count<5400 and time.monotonic()<work.deadline,'Shared setup/cleanup budget reserve');case=HybridCase(name,work,env,a,pins,rows,bindings,events);case.start();save(case.folder/'CLOCK_SEAM.json',seams);fn(case,clock)
  except Exception as exc:
   common_failed=case is None or case.stage in('model_start','sealed_graph_identity');outcome={'feature':name,'status':'blocked'if type(exc)is FeatureBlocked else'failed',**B.safe_error(exc)}
   if type(exc)is FeatureBlocked:outcome['fixed_guard']=str(exc)
   trace=exc.__traceback__;site=None
   while trace is not None:
    if Path(trace.tb_frame.f_code.co_filename).name in('keeper_jobs.py','job_cases.py','run_jobs.py'):site={'file':Path(trace.tb_frame.f_code.co_filename).name,'function':trace.tb_frame.f_code.co_name,'line':trace.tb_lineno}
    trace=trace.tb_next
   outcome['site']=site
   if case is not None:case.outcome.update(outcome)
   else:result['features'].append(outcome)
  finally:
   if case is not None:
    try:clean=case.close();result['cleanup'].append({'feature':name,**clean});result['features'].append(case.outcome)
    except Exception as exc:result['cleanup'].append({'feature':name,'stopped':False,**B.safe_error(exc)});result['features'].append({**case.outcome,'status':'failed','cleanup_failed':True});break
  if common_failed or work.count>=5400 or time.monotonic()>=work.deadline:break
 try:
  B.validate_source(args.source_manifest_sha256);result['source_inputs_preserved']=all(sha((LAB/'inputs'/n).read_bytes())==digest for n,(size,digest)in B.INPUTS.items())
 except Exception as exc:result['source_inputs_preserved']=False;result['final_validation']=B.safe_error(exc)
 result.update(planned_jobs=[n for n,f in JOBS],unattempted_jobs=[n for n,f in JOBS if n not in{r['feature']for r in result['features']}],shared_RPC_requests=work.count,raw_submission_attempts=work.raw_attempts,reviewed_raw_forward_attempts=work.raw,stock_events_bytes=events.size,tracked_children_stopped=bool(result['cleanup'])and all(r.get('stopped')is True and r.get('overflow')is False for r in result['cleanup']),whole_cgroup_cleanup_requires_external_readback=True,actual_signed_envelope_predecoded=False,postforward_exact_transaction_verification_required=True,secret_disposition={'retained_only_in_new_owned_lab':True,'contents_or_content_hashes_exported':False});result['success']=len(result['features'])==len(JOBS)and all(r['status']in('passed','expected_refusal')for r in result['features'])and result['tracked_children_stopped']and result['source_inputs_preserved'];save(OUT/'EVENTS.json',{'combined_stdout_stderr':''.join(events.parts)});save(OUT/'RESULT.json',result);print(json.dumps({'success':result['success'],'features':[(r['feature'],r['status'])for r in result['features']]}));return 0 if result['success']else 1
if __name__=='__main__':raise SystemExit(main())
