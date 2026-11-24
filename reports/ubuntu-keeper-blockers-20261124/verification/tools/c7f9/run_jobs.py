"""NEW missing ordinary-rebalance completion, directed copied-state model.

DRAFT: not executed. Actual stock run_cycle/submit/Cast/recovery are unchanged.
Existing sampled/disagreement proofs are cited, not separate cases rerun.
"""
from job_cases import *
import math

class LPCase(Case):
 def configure(self,**updates):
  super().configure(**updates)
  self.model.review['allowed']=[('rebalance_observation','rebalance_confirmation','observe(uint256)'),('rebalance_reset','rebalance_confirmation','resetObservation(uint256)'),('rebalance','vault','rebalance(uint256,uint128,uint256)')]
 def fee_readback(self):
  quote=self.model.rpc('eth_gasPrice',[]);tip=self.model.rpc('eth_maxPriorityFeePerGas',[]);head=self.model.rpc('eth_getBlockByNumber',['latest',False]);pending=self.model.rpc('eth_getBlockByNumber',['pending',False])
  def q(value):
   need(type(value)is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})',value)is not None,'Canonical controlled fee quantity');return int(value,16)
  gas=q(quote);priority=q(tip);base=q(head.get('baseFeePerGas'));pending_base=q(pending.get('baseFeePerGas'))
  need(0<gas<=100 and 0<base<=100 and 0<pending_base<=100,'Controlled fixture fee policy readback differs')
  save(self.folder/'CONTROLLED_FEES.json',{'gas_price_wei':gas,'node_suggested_priority_fee_wei':priority,'priority_suggestion_is_not_signed_cap':True,'latest_base_fee_wei':base,'pending_base_fee_wei':pending_base,'latest_head':head,'pending_head':pending,'flags':['--gas-price','1','--block-base-fee-per-gas','1','--disable-min-priority-fee'],'synthetic_model_economics_not_Robinhood_fee_qualification':True,'gas_fee_cost_caps_unchanged':True})
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
 from zzz_ops.abi import keccak256
 c.stage='controlled_fee_readback';c.fee_readback();c.stage='stock_configuration';c.configure()
 c.stage='actual_market_move';before,spot,_unused_inside=c.move_to_trigger();need(before['secondary']==0 and c.uint('portfolio_policy','enabled(bytes32)',POOL)==0,'This missing partition starts with single-main mode')
 c.stage='controlled_reference_refresh';c.refresh_reference(spot)
 # The reference-inside disagreement case already passed in c7f0 and is NOT
 # rerun. Actual new stock checks still corroborate both references on every
 # ordinary decision and before each possible submission.
 if c.now()<int(time.time())-560:c.advance(int(time.time())-560)
 c.stage='stock_sample_window_and_jitter';scheduled=None;first=None;observations=[];rebalance_topic='0x'+keccak256(b'Rebalanced(uint256,uint256,uint256,uint160)').hex();principal_before=c.uint('vault','bucketTotalShares(uint256)',BUCKET)
 for index in range(8):
  count_before=c.model.rpc_count;sender_before=int(c.model.rpc('eth_getBalance',[c.sender,'latest']),16);p=c.cycle();stock=copy.deepcopy(c.k.rebalance_confirmation.last_observation)
  if p is not None:
   if p['key'].startswith('rebalance:'):
    need(scheduled is not None and c.now()>=scheduled['execute_after'],'Ordinary adjustment preceded durable jitter')
    c.stage='ordinary_rebalance_recovery';receipt=c.settle(p);head=c.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);stamp=int(head['timestamp'],16);after=c.physical()
    need(after['main']!=before['main']and after['secondary']==0 and after['liquidity']>0 and after['owner']=='0x'+f"{int(c.a['vault'],16):064x}"and c.rights()==c.before_rights,'Ordinary replacement/custody/NFT rights differ')
    need(first is not None and stamp-first>=600 and after['group'][6]==stamp and after['group'][0]==before['group'][0]and c.uint('vault','bucketTotalShares(uint256)',BUCKET)==principal_before,'Ordinary sample timing/checkpoint/share total differs')
    slot=c.words(B.STATE,'getSlot0(bytes32)',POOL);signed=lambda value:value-(1<<256)if value>>255 else value;lower,upper=map(signed,after['ticks']);tick=signed(slot[1]);need(lower<=tick<upper,'New main is not physically active')
    rows=[r for r in receipt.get('logs',[])if r.get('address','').lower()==c.a['vault']and r.get('topics',[None])[0]==rebalance_topic]
    need(len(rows)==1 and rows[0]['topics']==[rebalance_topic,'0x'+f'{BUCKET:064x}']and c.decode(rows[0]['data'])==[before['main'],after['main'],after['group'][5]],'Exact Rebalanced event differs')
    cost=c.k.state['last_fee_observation'];sender_after=int(c.model.rpc('eth_getBalance',[c.sender,'latest']),16);need(cost['transaction']==p['hash']and sender_before-sender_after==cost['cost_wei'],'Keeper received funds besides exact gas spend')
    c.stage='final_rights_reserve_checks';save(c.folder/'FINAL_ACCOUNTING_VIEWS.json',{'money':c.money(),'rights':c.rights(),'total_shares':str(principal_before),'slot0':slot,'scope':'classification readback; no independent all-fee accounting claim'})
    c.outcome.update(status='passed',before=before,after=after,observations=observations,schedule=scheduled,unavoidable_new_confirmation_prerequisites=len(observations),prior_disagreement_proof_reused='c7f0 LP_KEEPER_RECONCILIATION scoped_pass',controlled_logical_clock=True,wallclock_soak=False,fees_synthetic=True,ordinary_rebalance_hash=p['hash'],rebalance_event_exact=True,sender_only_pays_gas=True)
    return
   need(p['key'].startswith('rebalance_observation:'),'Unexpected confirmation reset or unrelated normal adjustment action');receipt=c.settle(p)
   # Four raw words are a NEW receipt/post-state assertion. Do not perform a
   # redundant full driver confirmation audit: stock has just done its own
   # fresh candidate/runtime/source/control checks before actual submission.
   identity,observed_first,last,side=c.words('rebalance_confirmation','observations(uint256)',BUCKET);header=c.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);included=int(header['timestamp'],16)
   need(type(stock)is dict and identity==int(stock['identity'],16)and side==stock['side']and side in(1,2)and observed_first>0 and last==included,'Actual observation differs from the fresh stock reviewed condition')
   if first is None:first=observed_first
   need(first==observed_first and(not observations or 0<last-observations[-1]['last_seen']<=300),'Strict same-window observation identity/gap differs')
   observations.append({'identity':'0x'+f'{identity:064x}','side':side,'first_seen':first,'last_seen':last,'receipt_hash':p['hash'],'receipt_number':receipt['blockNumber'],'RPC_requests_this_step':c.model.rpc_count-count_before,'source':'actual four-word on-chain receipt state; full reviewed condition stays stock-owned'})
  s=c.k.state.get('observed_adjustment_v3',{}).get(str(BUCKET));need(s is not None,'Stock sampled schedule absent')
  if s['execute_after']:
   scheduled=copy.deepcopy(s);need(60<=s['execute_after']-s['observed_at']<=300,'Fresh jitter outside60to300');target=min(s['execute_after'],s['next_check_at'])
  else:target=s['next_check_at']
  if first and c.now()<first+600:target=min(target,first+600)
  if target<=c.now():target=c.now()+1
  c.advance(target)
 raise FeatureBlocked('Missing ordinary adjustment did not complete within8directed stock cycles')

JOBS=[('confirmation',confirmation)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--base-sha256',required=True);p.add_argument('--trader-sha256',required=True);args=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed private LP helper path');need(sha(Path(B.__file__).read_bytes())==args.base_sha256 and sha((LAB/'inputs/TRADER.json').read_bytes())==args.trader_sha256,'Frozen helper/input differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256)
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast bytes differ');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);work=Work();events=Events();result={'schema':1,'scope':'NEW missing ordinary single-main replacement only;600s sampled/240s checks/strict300gap/fresh60-300jitter/12h cooldown; copied sealed state with actual synthetic low-fee node','success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'features':[],'cleanup':[],'production_approved':False,'all_enabled_jobs_qualified':False,'unexecuted':['continuous_daemon_timing','sample_reset_job_after_new_market_recovery','different_key_rotation']}
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
