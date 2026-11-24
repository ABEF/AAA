"""NEW missing positive stock burn only; private ROOT REVIEW required; not executed."""
from job_cases import *

def buyback(c):
 from zzz_ops.abi import keccak256
 from zzz_ops.ethereum_fees import execution_price
 c.restore_historical_supply();c.stage='genuine_fee_setup';c.fees_setup();before=c.burn_money();rights=c.rights();physical=c.physical();supply=c.uint(ZZZ,'totalSupply()');zero_balance=c.uint(ZZZ,'balanceOf(address)',ZERO);c.burn_amount=before[ZZZ]['buyback'];need(0<c.burn_amount<=supply,'No actual classified ZZZ burn reserve')
 save(c.folder/'BURN_PRE_REVIEW.json',{'money':before,'rights':rights,'physical':physical,'total_supply':supply,'zero_address_balance':zero_balance,'burn_amount':c.burn_amount,'historical_supply_restore_writes':c.model.supply_restore_attempts,'actual_fee_reserve_funding':True,'copied_state_not_actual_market':True})
 c.stage='stock_direct_ZZZ_burn';c.configure(buybacks=[{'token':ZZZ,'amount':c.burn_amount,'pool_id':POOL}]);fee_readback=c.fee_readback();p=c.cycle()
 if p is None:raise FeatureBlocked('Stock direct ZZZ burn refused; inspect exact diagnostics')
 need(p['key']=='buyback:'+ZZZ,'Unexpected stock job before burn');receipt=c.settle(p);after=c.burn_money();after_rights=c.rights();after_physical=c.physical();after_supply=c.uint(ZZZ,'totalSupply()');after_zero_balance=c.uint(ZZZ,'balanceOf(address)',ZERO)
 tx=c.model.rpc('eth_getTransactionByHash',[p['hash']]);header=c.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);fields={k:tx.get(k)for k in('hash','from','to','input','value','nonce','gas','gasPrice','type','chainId','maxFeePerGas','maxPriorityFeePerGas','blockHash','blockNumber','transactionIndex')};charged_price=execution_price(tx,header,receipt);charged_cost=int(receipt['gasUsed'],16)*charged_price;observed=copy.deepcopy(c.k.state.get('last_fee_observation'));spent=copy.deepcopy(c.k.state['spent'])
 review={'scope':'NEW stock direct-ZZZ burn, exact historical supply scalar plus controlled copied state; not full global-state/provider acceptance','pre':{'money':before,'rights':rights,'physical':physical,'total_supply':supply,'zero_address_balance':zero_balance},'post':{'money':after,'rights':after_rights,'physical':after_physical,'total_supply':after_supply,'zero_address_balance':after_zero_balance},'requested_burn_amount':c.burn_amount,'actual_transaction_without_signature':fields,'canonical_inclusion_header':header,'receipt':receipt,'durable_review':p['fee_review'],'stock_last_fee_observation':observed,'stock_spent':spent,'independently_derived_execution_price_wei':charged_price,'independently_derived_cost_wei':charged_cost,'actual_reported_receipt_price_wei':int(receipt['effectiveGasPrice'],16),'fee_readback':fee_readback,'saved_before_terminal_assertions':True};save(c.folder/'BURN_REVIEW.json',review)
 need(after_supply+c.burn_amount==supply and after_zero_balance==zero_balance,'Supply did not genuinely burn or zero-address balance grew')
 need(after[ZZZ]['buyback']==0 and after[ZZZ]['fees_balance']+c.burn_amount==before[ZZZ]['fees_balance']and after[ZZZ]['accounted']+c.burn_amount==before[ZZZ]['accounted'],'Classified ZZZ reserve/physical backing did not debit exactly')
 need(after[ZERO]==before[ZERO]and after_rights==rights==c.before_rights and after_physical==physical,'Burn changed ETH reserves/NFT rights/LP principal')
 need(all(after[ZZZ][key]==before[ZZZ][key]for key in before[ZZZ]if key not in('buyback','fees_balance','accounted')),'Burn consumed compound/dust/reward claims or other balances')
 burn_topic='0x'+keccak256(b'Transfer(address,address,uint256)').hex();event_topic='0x'+keccak256(b'BoughtAndBurned(address,uint256,uint256)').hex();burns=[l for l in receipt['logs']if l['address'].lower()==ZZZ and l['topics'][0]==burn_topic and int(l['topics'][1],16)==int(c.a['buyback'],16)and int(l['topics'][2],16)==0];events=[l for l in receipt['logs']if l['address'].lower()==c.a['buyback']and l['topics'][0]==event_topic and int(l['topics'][1],16)==int(ZZZ,16)]
 need(len(burns)==1 and c.decode(burns[0]['data'])==[c.burn_amount]and len(events)==1 and c.decode(events[0]['data'])==[c.burn_amount,c.burn_amount],'Missing exact token burn and BoughtAndBurned events')
 need(sum(spent.values())==charged_cost==observed['cost_wei']and observed['execution_price_wei']==charged_price and charged_cost<=p['fee_review']['maximum_cost_wei']<=10**16,'Canonical fee accounting differs or exceeds unchanged cap')
 count=c.model.raw_send_count;need(c.cycle()is None and c.model.raw_send_count==count==1,'Drained reserve repeated a burn submission')
 c.outcome.update(status='passed',burned=str(c.burn_amount),supply_before=str(supply),supply_after=str(after_supply),saved_review='BURN_REVIEW.json',historical_supply_restore_writes=1,no_dead_address_transfer_fiction=True,reserves_rights_and_principal_preserved=True,no_resend_or_repeated_burn=True,canonical_cost_wei=charged_cost)

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--base-sha256',required=True);p.add_argument('--trader-sha256',required=True);args=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Unprivileged dedicated private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed private helper path required');need(sha(Path(B.__file__).read_bytes())==args.base_sha256,'Frozen base helper differs');need(sha((LAB/'inputs/TRADER.json').read_bytes())==args.trader_sha256,'Retained trader artifact differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256)
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied input differs')
 need(len((LAB/'inputs/BURN_STATE.json').read_bytes())==BURN_STATE_BYTES and sha((LAB/'inputs/BURN_STATE.json').read_bytes())==BURN_STATE_SHA,'Reviewed supply artifact differs');
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast binary differs');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);work=Work();events=Events();result={'schema':1,'scope':'NEW positive stock direct-ZZZ burn only; copied F6 plus authenticated historical supply-slot restore and synthetic local fees; no actual provider/market/global-state qualification','success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'production_approved':False,'features':[],'cleanup':[],'all_enabled_jobs_qualified':False,'unexecuted':['ordinary_confirmation_and_jitter','ordinary_rebalance','manual_geometry_exception','LP_native_conversion','different_key_rotation','continuous_long_duration_operation']}
 for name,fn in [('buyback',buyback)]:
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
 result.update(shared_RPC_requests=work.count,raw_submission_attempts=work.raw_attempts,reviewed_raw_forward_attempts=work.raw,shared_maximum_reviewed_cost_wei=work.maximum_cost,stock_events_bytes=events.size,tracked_children_stopped=bool(result['cleanup'])and all(r.get('stopped')is True and r.get('overflow')is False for r in result['cleanup']),whole_cgroup_cleanup_requires_external_readback=True,actual_signed_envelope_predecoded=False,postforward_exact_transaction_verification_required=True,unattempted_jobs=[n for n in('buyback',)if n not in{r['feature']for r in result['features']}],secret_disposition={'retained_only_in_new_owned_lab':True,'contents_or_content_hashes_exported':False})
 result['success']=len(result['features'])==1 and all(r['status']in('passed','expected_refusal')for r in result['features'])and result['tracked_children_stopped']and result.get('source_inputs_preserved')is True;save(OUT/'EVENTS.json',{'combined_stdout_stderr':''.join(events.parts)});save(OUT/'RESULT.json',result);print(json.dumps({'success':result['success'],'features':[(r['feature'],r['status'])for r in result['features']],'tracked_children_stopped':result['tracked_children_stopped']}));return 0 if result['success']else 1


if __name__=='__main__':raise SystemExit(main())
