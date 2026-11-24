"""NEW directed normal adjustment and native LP conversion partitions."""
from job_cases import *
import math

class LPCase(Case):
 def configure(self,**updates):
  if self.name=='conversion':
   roles=('access','vault','strategy','fees','compounder','buyback','pools','rewards','liquidity','balancing_router','lp_balance_math','lp_position_executor','portfolio_policy','protocol_policy','rebalance_confirmation','oracle','contribution_pricing','nft','lp_converter','lp_v4_executor');contracts={r:self.a[r]for r in roles};pins={r:self.pins[r]for r in roles};contracts.update(principal_exit=self.a['migration'],pool_manager=B.CORE,state_view=B.STATE,lp_nft=self.a['nft']);pins.update(principal_exit=self.pins['migration'],pool_manager=B.CORE_HASH,state_view=B.STATE_HASH,idle_compounding_budget=self.pins['migration_budget'],lp_nft=self.pins['nft']);updates.update(contracts=contracts,code_hashes=pins)
  super().configure(**updates)
  self.model.review['allowed']={'confirmation':[('rebalance_observation','rebalance_confirmation','observe(uint256)'),('rebalance_reset','rebalance_confirmation','resetObservation(uint256)'),('rebalance','vault','rebalance(uint256,uint128,uint256)')],'geometry':[('rebalance','vault','rebalance(uint256,uint128,uint256)')],'conversion':[('lp_conversion','rewards','convertBatch(address,uint256[],bytes32,uint256,uint256)')]}[self.name]
  if self.name=='conversion':self.model.review.update(conversion_route=self.route,conversion_ids=self.ids)
 def refresh_reference(self,root):
  eth=self.words(self.feeds['eth_feed_a'],'latestRoundData()')[1];answer=eth*(1<<192)//(root*root);need(0<answer<1<<255,'Controlled reference magnitude differs');self.owner_on()
  for label in('zzz_feed_a','zzz_feed_b'):
   stamp=self.now();self.call_setup('controlled_reference:'+label,self.feeds[label],'set(int256,uint256,uint256)',answer,stamp,stamp)
  self.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);return answer
 def new_trader(self):
  self.owner_on();meta=B.json_file(LAB/'inputs/TRADER.json');r,_=self.setup('new_genuine_market_trader',None,meta['creation'],creation=True);self.trader=r['contractAddress'].lower();need(self.model.rpc('eth_getCode',[self.trader,'latest']).lower()==meta['expected_runtime'].lower(),'Retained actual trader runtime differs')
 def quote(self,amount):
  before=self.read(B.STATE,'getSlot0(bytes32)',POOL);q={'from':self.a['liquidity'],'to':self.a['balancing_router'],'data':encode('quoteSwap(bytes32,bool,uint256)',POOL,True,amount),'gas':hex(24000000)};value=self.model.rpc('eth_call',[q,'latest']);words=self.decode(value);need(len(words)==6 and words[0]>0 and words[1]>0,'Actual core quote shape differs');need(self.read(B.STATE,'getSlot0(bytes32)',POOL)==before,'Read-only quote persisted core state');return words
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

def confirmation(c):
 c.stage='stock_configuration';c.configure();c.stage='actual_market_move';before,spot,inside=c.move_to_trigger();c.refresh_reference(inside);c.stage='independent_reference_disagreement';status=c.k._confirmation_status(BUCKET);need(status['side']==0 and not status['ready']and status['first_seen']==0,'Independent inside reference did not block trigger');save(c.folder/'REFERENCE_DISAGREEMENT.json',status);c.refresh_reference(spot)
 if c.now()<int(time.time())-560:c.advance(int(time.time())-560)
 c.stage='stock_sample_window_and_jitter';scheduled=None;first=None;observations=[]
 for index in range(14):
  p=c.cycle()
  if p is not None:
   if p['key'].startswith('rebalance:'):
    need(scheduled is not None and c.now()>=scheduled['execute_after'],'Ordinary adjustment preceded durable jitter');receipt=c.settle(p);after=c.physical();need(after['main']!=before['main']and c.rights()==c.before_rights,'Ordinary rebalance failed replacement/rights');need(first is not None and int(c.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False])['timestamp'],16)-first>=600,'Ordinary adjustment preceded600second sample window');c.outcome.update(status='passed',before=before,after=after,observations=observations,schedule=scheduled,independent_inside_reference_blocked=True,controlled_logical_clock=True,wallclock_soak=False);return
   need(p['key'].startswith(('rebalance_observation:','rebalance_reset:')),'Unexpected normal adjustment action');c.settle(p)
  status=c.k._confirmation_status(BUCKET);observations.append(status);first=status['first_seen']or first;s=c.k.state.get('observed_adjustment_v3',{}).get(str(BUCKET));need(s is not None,'Stock sampled schedule absent')
  if s['execute_after']:
   scheduled=copy.deepcopy(s);need(60<=s['execute_after']-s['observed_at']<=300,'Fresh jitter outside60to300');target=min(s['execute_after'],s['next_check_at'])
  else:target=s['next_check_at']
  if first and c.now()<first+600:target=min(target,first+600)
  if target<=c.now():target=c.now()+1
  c.advance(target)
 raise FeatureBlocked('Normal sampled adjustment did not finish within14directed stock cycles')

def geometry(c):
 from zzz_ops.abi import keccak256
 c.stage='explicit_width_configuration';before=c.physical();config=c.words('pools','get(bytes32)',POOL);need(len(config)==14 and config[7]==5000,'Expected original5000width');config[7]=2500;sig='configureNative(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))';c.setup('only_governed_width_changed','pools','0x'+keccak256(sig.encode()).hex()[:8]+''.join(f'{x:064x}'for x in config));need(c.uint('strategy','rangeUpdatePending(uint256)',BUCKET)==1,'Width change did not mark pending');c.configure();status=c.k._confirmation_status(BUCKET);need(status['manual']and status['ready'],'Geometry exception not ready after old12h clock');c.stage='stock_geometry_exception';need(c.cycle()is None,'Geometry skipped initial durable jitter');schedule=c.k.state['observed_adjustment_v3'][str(BUCKET)];need(60<=schedule['execute_after']-schedule['observed_at']<=300,'Geometry jitter differs');c.advance(schedule['execute_after']);p=c.cycle()
 if p is None:raise FeatureBlocked('Manual geometry stock replacement refused; inspect diagnostics')
 c.settle(p);after=c.physical();need(after['main']!=before['main']and after['ticks']!=before['ticks']and c.uint('strategy','rangeUpdatePending(uint256)',BUCKET)==0 and c.rights()==c.before_rights,'Geometry replacement/rights differs');c.outcome.update(status='passed',before=before,after=after,unchanged_other_pool_fields=True,financial_guards_preserved=True)

def conversion(c):
 from zzz_ops.abi import keccak256
 from keeper.royalties import encode_batch
 c.stage='typed_native_route_setup';native='0x'+keccak256(b'ZZZ_NATIVE_ETH_V1').hex();code=c.model.rpc('eth_getCode',[ZZZ,'latest']);source_pin='0x'+keccak256(bytes.fromhex(code[2:])).hex();need(source_pin=='0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597','Copied ZZZ runtime differs');review='0x'+keccak256(b'c7f0 isolated selected-pool native LP conversion review').hex();words=[int(ZZZ,16),0,0,int(ZZZ,16),10020,200,0,int(B.CORE,16),int(B.STATE,16),int(source_pin,16),int(native,16),int(B.CORE_HASH,16),int(B.STATE_HASH,16),int(review,16)];sig='addV4Route((address,address,(address,address,uint24,int24,address),address,address,bytes32,bytes32,bytes32,bytes32,bytes32))';receipt,route=c.setup('register_reviewed_native_route','lp_converter','0x'+keccak256(sig.encode()).hex()[:8]+''.join(f'{x:064x}'for x in words));need(len(route)==66 and int(route,16)>0,'Typed route ID absent');c.route=route;c.call_setup('enable_native_converter','lp_converter','setEnabled(bool)',True);need(c.uint('lp_converter','conversionLossBps()')==100,'Existing1% cap changed');c.stage='stock_native_LP_conversion';c.configure(lp_conversion={'enabled':True,'profile':'v4_native','max_nfts_per_cycle':2,'max_gas_to_output_bps':100,'assets':[{'asset':ZZZ,'route_id':route,'minimum_source_units':1,'minimum_output_wei':1}]});before=c.money();ids=sorted(i for i in c.ids if c.uint('rewards','claimable(uint256,address)',i,ZZZ)>0);total=sum(c.uint('rewards','claimable(uint256,address)',i,ZZZ)for i in ids);need(total>0,'No funded ZZZ LP rights in copied state');expected=c.uint('oracle','quote(address,address,uint256)',ZZZ,ZERO,total);minimum=(expected*9900+9999)//10000;data=encode_batch(ZZZ,ids,route,minimum,c.now()+180);q={'jsonrpc':'2.0','id':c.model.rpc_count+1,'method':'eth_call','params':[{'from':c.sender,'to':c.a['rewards'],'data':data,'gas':hex(24000000)},'latest']};simulation=c.model.request(q);slot=c.words(B.STATE,'getSlot0(bytes32)',POOL);protocol=slot[2]>>12;fee=protocol+slot[3]-protocol*slot[3]//1000000;diag={'source_units':str(total),'oracle_output_wei':str(expected),'minimum_ETH_wei':str(minimum),'actual_directional_fee_ppm':fee,'conversion_loss_bps':100,'simulation_succeeded':'result'in simulation,'stock_gas_to_output_bps':100}
 if'error'in simulation:
  e=simulation['error'];raw=e.get('data')if type(e)is dict else None;diag.update(error_code=e.get('code')if type(e)is dict else None,revert_selector=raw[:10]if type(raw)is str else None)
 save(c.folder/'CONVERSION_REVIEW.json',diag);p=c.cycle()
 if p is not None:
  c.settle(p);after=c.money();need(after[ZZZ]['liabilities']<before[ZZZ]['liabilities']and after[ZERO]['liabilities']>before[ZERO]['liabilities']and c.rights()==c.before_rights,'Native conversion did not preserve NFT rights/funded credit');c.outcome.update(status='passed',conversion=diag,funded_ETH_credit=True)
 else:
  need(c.money()==before and c.rights()==c.before_rights and c.model.raw_send_count==0,'Refused conversion changed earned balances');selector='0x'+keccak256(b'Slippage()').hex()[:8]
  if diag.get('revert_selector')==selector:c.outcome.update(status='expected_refusal',conversion=diag,exact_original_rights_preserved=True,qualified_positive_conversion=False)
  else:raise FeatureBlocked('Native conversion did not submit; exact simulation/economic blocker retained')

JOBS=[('conversion',conversion),('geometry',geometry)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--base-sha256',required=True);p.add_argument('--trader-sha256',required=True);args=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed private LP helper path');need(sha(Path(B.__file__).read_bytes())==args.base_sha256 and sha((LAB/'inputs/TRADER.json').read_bytes())==args.trader_sha256,'Frozen helper/input differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256)
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast bytes differ');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);work=Work();events=Events();result={'schema':1,'scope':'NEW directed stock confirmation/rebalance/geometry/native LP conversion; copied sealed state; not global market or wallclock soak','success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'features':[],'cleanup':[],'production_approved':False,'all_enabled_jobs_qualified':False,'unexecuted':['continuous_daemon_timing','sample_reset_job_after_new_market_recovery','different_key_rotation']}
 for name,fn in JOBS:
  case=None;common_failed=False
  try:
   need(work.count<5400 and time.monotonic()<work.deadline,'Shared setup/cleanup budget reserve');case=LPCase(name,work,env,a,pins,rows,bindings,events);case.start();fn(case)
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
