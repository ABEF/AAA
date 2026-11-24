"""Private bounded NEW job partitions; no old tests and no production adoption."""
from job_cases import *

def compound(c):
 from zzz_ops.abi import keccak256
 c.stage='genuine_fee_setup';c.fees_setup();before=c.physical();funds=c.accounting()
 need(c.uint('vault','bucketCount()')==1 and funds['total_shares']==sum(r['shares']for r in funds['rights']),'Fixture is not the complete single-bucket/two-holder model')
 need(before['secondary']==0 and funds['eligible']==len(c.ids)==2 and any(r['compound']>0 for r in funds['assets'].values()),'Missing actual compound reserve/single-main active model')
 c.stage='stock_compound'
 c.configure(maintenance={'compound':True,'compound_idle':True,'harvest':False,'minimum_liquidity':1,'compound_interval_seconds':3600,'compound_thresholds':{ZERO:1000,ZZZ:1000},'harvest_interval_seconds':3600})
 c.fee_readback('BEFORE_JOB');need(c.uint('migration_budget','compoundReady(uint256)',BUCKET)==1,'Imported compound clock not due');p=c.cycle()
 if p is None:raise FeatureBlocked('Stock compound refused; inspect exact diagnostics')
 need(p['key']=='compound:'+str(BUCKET),'Unexpected compound job');receipt=c.settle(p);after=c.physical();after_funds=c.accounting()
 need(after['main']==before['main']and after['secondary']==before['secondary']==0 and after['ticks']==before['ticks']and after['owner']==before['owner']and after['liquidity']>before['liquidity'],'Compound did not increase same main liquidity/ownership')
 need(after['group'][0]==before['group'][0]and after['group'][4:]==before['group'][4:],'Compound changed deposit/centre/rebalance/lifecycle fields')
 need(after_funds['rights']==funds['rights']==c.before_rights and after_funds['total_shares']==funds['total_shares']and after_funds['eligible']==funds['eligible'],'Compound changed NFT rights/shares/membership')
 topics={s:'0x'+keccak256(s.encode()).hex()for s in('FeesCollected(uint256,uint256,uint256)','Compounded(uint256,uint256,uint256)','PoolRewardsCredited(uint256,address,uint256,uint256)','MigrationValueChecked(uint256,uint256,uint256,uint256)')}
 vault_logs=[l for l in receipt['logs']if l['address'].lower()==c.a['vault']]
 collections=[c.decode(l['data'])for l in vault_logs if l['topics'][0]==topics['FeesCollected(uint256,uint256,uint256)']and int(l['topics'][1],16)==BUCKET]
 compounded=[c.decode(l['data'])for l in vault_logs if l['topics'][0]==topics['Compounded(uint256,uint256,uint256)']and int(l['topics'][1],16)==BUCKET]
 need(len(compounded)==1 and len(compounded[0])==2 and len(collections)>=2 and all(len(r)==2 for r in collections),'Missing exact actual compound/internal-harvest receipt events')
 reconciled={}
 for index,asset in enumerate((ZERO,ZZZ)):
  old=funds['assets'][asset];new=after_funds['assets'][asset];dust=old['dust'];units=0
  for row in collections:total=dust+row[index];units+=total//20;dust=total%20
  harvested=sum(row[index]for row in collections);released=compounded[0][index]
  reward_events=[c.decode(l['data'])for l in receipt['logs']if l['address'].lower()==c.a['rewards']and l['topics'][0]==topics['PoolRewardsCredited(uint256,address,uint256,uint256)']and int(l['topics'][1],16)==BUCKET and int(l['topics'][2],16)==int(asset,16)]
  need(all(len(v)==2 for v in reward_events)and sum(v[0]for v in reward_events)==16*units and sum(v[1]for v in reward_events)==2*units,'Authenticated individual/collective credit events differ')
  need(new['compound']==old['compound']+units-released and new['buyback']==old['buyback']+units and new['dust']==dust,'Actual80/10/5/5 reserve/dust/release arithmetic differs')
  need(new['accounted']==old['accounted']+harvested-18*units-released and new['fees_balance']==old['fees_balance']+harvested-18*units-released,'Fee reserve physical/accounted deltas differ')
  need(new['liabilities']==old['liabilities']+18*units and new['rewards_balance']==old['rewards_balance']+18*units and new['orphaned']==old['orphaned']and new['direct_liabilities']==old['direct_liabilities'],'Compound consumed or miscredited reward backing')
  need(sum(sum(r)for r in new['claims'])==sum(sum(r)for r in old['claims'])+18*units,'Exact whole-unit holder claims do not reconcile')
  need(released>=old['compound'],'Existing designated compound was not released')
  need(new['total_idle']==after['group'][2+index]and old['total_idle']==before['group'][2+index],'Whole-model idle attribution differs')
  reconciled[asset]={'actual_harvested':harvested,'allocation_units':units,'compound_released':released,'remaining_dust':dust,'new_holder_credit':18*units,'new_buyback':units}
 actual=c.model.rpc('eth_getTransactionByHash',[p['hash']]);header=c.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);actual_fields={k:actual.get(k)for k in('hash','from','to','input','nonce','value','gas','gasPrice','type','chainId','maxFeePerGas','maxPriorityFeePerGas','blockHash','blockNumber')}
 need(int(actual['gas'],16)==p['fee_review']['gas_limit']and int(actual.get('maxFeePerGas',actual['gasPrice']),16)==p['fee_review']['max_fee_per_gas'],'Actual signed gas fields differ from durable review')
 if actual['type']=='0x2':need(0<=int(actual['maxPriorityFeePerGas'],16)<=int(actual['maxFeePerGas'],16),'Actual priority exceeds captured max fee')
 need(after_funds['last_compound']==int(header['timestamp'],16)and c.uint('migration_budget','compoundReady(uint256)',BUCKET)==0,'Compound interval did not commit to actual receipt time')
 count=c.model.raw_send_count;need(c.cycle()is None and c.model.raw_send_count==count==1,'Immediate repeated compound submitted')
 need(sum(int(v)for v in c.k.state['spent'].values())==int(receipt['gasUsed'],16)*int(receipt['effectiveGasPrice'],16)<=p['fee_review']['maximum_cost_wei']<=10**16,'Actual charged spend differs/exceeds reviewed unchanged fee cap')
 c.outcome.update(status='passed',before=before,after=after,funds_before=funds,funds_after=after_funds,exact_allocation=reconciled,actual_transaction_without_signature=actual_fields,receipt_header=header,clock_suppressed_repeat=True,synthetic_fee_model_not_provider_qualification=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--base-sha256',required=True);p.add_argument('--trader-sha256',required=True);args=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Unprivileged dedicated private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed private helper path required');need(sha(Path(B.__file__).read_bytes())==args.base_sha256,'Frozen base helper differs');need(sha((LAB/'inputs/TRADER.json').read_bytes())==args.trader_sha256,'Retained trader artifact differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256)
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast binary differs');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);work=Work();events=Events();result={'schema':1,'scope':'NEW positive stock compound only; copied sealed F6 and genuine local quotes in explicit synthetic fee model; not Robinhood/provider/global-state qualification','success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'production_approved':False,'features':[],'cleanup':[],'all_enabled_jobs_qualified':False,'unexecuted':['ordinary_confirmation_and_jitter','ordinary_rebalance','manual_geometry_exception','LP_native_conversion','different_key_rotation','continuous_long_duration_operation']}
 for name,fn in [('compound',compound)]:
  case=None;common_start_failed=False
  try:
   need(time.monotonic()<work.deadline and work.count<5400,'Shared setup/cleanup budget reserve');case=Case(name,work,env,a,pins,rows,bindings,events);case.start();fn(case)
  except Exception as exc:
   common_start_failed=case is None or case.stage in('model_start','sealed_graph_identity')
   outcome={'feature':name,'status':'blocked'if type(exc)is FeatureBlocked else'failed','last_stage':None if case is None else case.stage,**B.safe_error(exc)}
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
    try:cleanup=case.close();result['cleanup'].append({'feature':name,**cleanup});result['features'].append(case.outcome)
    except Exception as exc:
     result['cleanup'].append({'feature':name,'stopped':False,**B.safe_error(exc)});result['features'].append({**case.outcome,'status':'failed','cleanup_failed':True});break
  if common_start_failed or time.monotonic()>=work.deadline or work.count>=5400:break
 try:
  B.validate_source(args.source_manifest_sha256)
  for name,(size,digest)in B.INPUTS.items():need(sha((LAB/'inputs'/name).read_bytes())==digest,'Original copied input changed')
  result['source_inputs_preserved']=True
 except Exception as exc:result['final_validation']=B.safe_error(exc)
 result.update(shared_RPC_requests=work.count,raw_submission_attempts=work.raw_attempts,reviewed_raw_forward_attempts=work.raw,shared_maximum_reviewed_cost_wei=work.maximum_cost,stock_events_bytes=events.size,tracked_children_stopped=bool(result['cleanup'])and all(r.get('stopped')is True and r.get('overflow')is False for r in result['cleanup']),whole_cgroup_cleanup_requires_external_readback=True,actual_signed_envelope_predecoded=False,postforward_exact_transaction_verification_required=True,unattempted_jobs=[n for n in('compound',)if n not in{r['feature']for r in result['features']}],secret_disposition={'retained_only_in_new_owned_lab':True,'contents_or_content_hashes_exported':False})
 result['success']=len(result['features'])==1 and all(r['status']in('passed','expected_refusal')for r in result['features'])and result['tracked_children_stopped']and result.get('source_inputs_preserved')is True;save(OUT/'EVENTS.json',{'combined_stdout_stderr':''.join(events.parts)});save(OUT/'RESULT.json',result);print(json.dumps({'success':result['success'],'features':[(r['feature'],r['status'])for r in result['features']],'tracked_children_stopped':result['tracked_children_stopped']}));return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
