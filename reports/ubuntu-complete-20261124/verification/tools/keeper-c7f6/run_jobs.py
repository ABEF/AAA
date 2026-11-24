"""ONLY remaining stock role/pause/reset and previously unexecuted RPC faults.

Two NEW independent sealed-state clones share6000RPC/900s and unchanged
maintenance24M/full25%, confirmations12,240s cadence/hourly harvest and fees.
No passed metadata/retired or blocked compound/buyback case is repeated.
"""
from job_cases import *


def reset_receipt(c,p,receipt):
 from zzz_ops.abi import keccak256
 topic='0x'+keccak256(b'ObservationReset(uint256,uint8)').hex()
 need(p['key']=='rebalance_reset:'+str(BUCKET)and p['to']==c.a['rebalance_confirmation']and p['data']==encode('resetObservation(uint256)',BUCKET),'Only exact clear-only reset expected')
 logs=receipt['logs'];need(len(logs)==1 and logs[0]['address'].lower()==c.a['rebalance_confirmation']and logs[0]['topics']==[topic,'0x'+f'{BUCKET:064x}']and logs[0]['data']=='0x'+f'{5:064x}','Exact on-chain keeper invalidation event differs')
 need(c.words('rebalance_confirmation','observations(uint256)',BUCKET)==[0,0,0,0],'On-chain sampled evidence was not cleared')


def next_non_reset(c,*,allow_harvest,maximum_resets=2):
 resets=[]
 for _ in range(maximum_resets+1):
  p=c.cycle()
  if p is None:need(c.last_cycle_success is True,'Unrelated stock cycle failure cannot count as a settled pause/recovery');return None,resets
  if p['key']=='harvest:'+str(BUCKET):need(allow_harvest,'Paused keeper attempted harvest');return p,resets
  need(p['key']=='rebalance_reset:'+str(BUCKET)and len(resets)<maximum_resets,'Unexpected/excessive stock action while draining evidence resets')
  receipt=c.settle(p);reset_receipt(c,p,receipt);resets.append(p['hash'])
 raise B.HarnessRefusal('Bounded reset handling did not converge')


def verify_harvest(c,p,receipt):
 from zzz_ops.abi import keccak256
 need(p['key']=='harvest:'+str(BUCKET)and p['to']==c.a['vault'],'Expected exact resumed ordinary harvest')
 topic='0x'+keccak256(b'FeesCollected(uint256,uint256,uint256)').hex()
 need(any(log['address'].lower()==c.a['vault']and log['topics']and log['topics'][0]==topic and int(log['topics'][1],16)==BUCKET for log in receipt['logs']),'Resumed harvest lacks authenticated same-bucket collection event')
 need(c.k.state['last'].get('harvest:'+str(BUCKET))==int(c.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False])['timestamp'],16),'Harvest clock lacks exact successful receipt timestamp')


def roles(c):
 from zzz_ops.abi import keccak256
 c.stage='pause';c.call_setup('pause','access','setPaused(bool)',True)
 before=c.physical();money=c.money()
 c.configure(maintenance={'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600})
 paused,paused_resets=next_non_reset(c,allow_harvest=False)
 need(paused is None and all(r['action']=='rebalance_reset:'+str(BUCKET)for r in c.receipts)and c.physical()==before and c.money()==money and c.rights()==c.before_rights,'Paused keeper changed principal/rewards/rights or left work pending')
 need(c.uint('access','paused()')==1 and c.k.state['pending']is None,'Paused reset recovery state differs')
 c.owner_on();c.call_setup('unpause','access','setPaused(bool)',False);c.call_setup('revoke_new_keeper','access','setKeeper(address,bool)',c.sender,False);c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);c.stage='revocation'
 attempts=c.model.raw_send_count;forwarded=c.model.raw_forwarded;nonce=c.model.rpc('eth_getTransactionCount',[c.sender,'latest'])
 need(c.cycle()is None and c.last_cycle_success is False and c.model.raw_send_count==attempts and c.model.raw_forwarded==forwarded and c.model.rpc('eth_getTransactionCount',[c.sender,'latest'])==nonce,'Revoked keeper broadcast or advanced nonce')
 health=B.json_file(Path(c.cfg['health_path']));need(health['consecutive_failures']>=1 and c.uint('access','keepers(address)',c.sender)==0,'Revocation was not reflected by stock authority admission')
 q={'jsonrpc':'2.0','id':c.model.rpc_count+1,'method':'eth_call','params':[{'from':c.sender,'to':c.a['vault'],'data':encode('collectFees(uint256,uint256)',BUCKET,c.now()+180)},'latest']}
 error=c.model.request(q).get('error',{});selector='0x'+keccak256(b'Unauthorized()').hex()[:8]
 need(type(error.get('data'))is str and error['data'][:10]==selector,'Revoked wallet lacks exact typed on-chain Unauthorized refusal')
 need(c.physical()==before and c.money()==money and c.rights()==c.before_rights,'Revocation check changed principal/rewards/rights')
 c.owner_on();c.call_setup('restore_keeper','access','setKeeper(address,bool)',c.sender,True);c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);c.stage='restored_authority'
 p,restored_resets=next_non_reset(c,allow_harvest=True)
 if p is None:raise FeatureBlocked('Restored keeper did not resume due ordinary harvest after bounded resets')
 receipt=c.settle(p);verify_harvest(c,p,receipt)
 need(c.rights()==c.before_rights and c.physical()==before and c.uint('access','keepers(address)',c.sender)==1 and c.uint('access','paused()')==0,'Restored role changed rights/geometry or remained paused')
 c.outcome.update(status='passed',paused_only_clear_resets=paused_resets,paused_no_principal_or_harvest=True,revoked_no_submission_or_nonce_change=True,revoked_onchain_selector=selector,restored_clear_resets=restored_resets,restored_same_key_harvest=p['hash'],different_key_rotation_qualified=False)


def rpc_fault(c):
 c.stage='pre_submission_read_fault';c.configure(maintenance={'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600})
 nonce=c.model.rpc('eth_getTransactionCount',[c.sender,'latest']);c.model.fault={'method':'eth_getBlockByNumber','params':None}
 try:need(c.cycle()is None and c.last_cycle_success is False and c.model.fault_attempts>0 and c.model.raw_send_count==0 and c.model.raw_forwarded==0,'Failed pre-submission reads broadcast')
 finally:c.model.fault=None
 need(c.model.rpc('eth_getTransactionCount',[c.sender,'latest'])==nonce and c.k.state['pending']is None,'Failed prereads advanced nonce or created pending submission')
 save(c.folder/'PREREAD_FAULT.json',{'nonce_before':nonce,'nonce_after':c.model.rpc('eth_getTransactionCount',[c.sender,'latest']),'raw_attempts':c.model.raw_send_count,'raw_forwarded':c.model.raw_forwarded,'pending':c.k.state['pending'],'stock_cycle_success':c.last_cycle_success,'fault_hits':c.model.fault_attempts})
 before_faults=c.model.fault_attempts;c.stage='saved_hash_receipt_fault';p,resets=next_non_reset(c,allow_harvest=True)
 if p is None:raise FeatureBlocked('Read recovery did not resume due harvest after bounded resets')
 attempts=c.model.raw_send_count;forwarded=c.model.raw_forwarded
 receipt=c.settle(p,fault=True);verify_harvest(c,p,receipt)
 need(c.model.raw_send_count==attempts and c.model.raw_forwarded==forwarded and c.model.fault_attempts>before_faults and c.rights()==c.before_rights,'Saved-hash fault recovery resent or lost rights')
 c.outcome.update(status='passed',pre_send_no_submission=True,pre_send_nonce_preserved=True,post_send_identical_hash_no_resend=True,clear_resets_after_fault=resets,confirmed_harvest=p['hash'],receipt_fault_exact_pending_bytes=True)


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source-manifest-sha256',required=True);parser.add_argument('--base-sha256',required=True);args=parser.parse_args()
 need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New unprivileged private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed reviewed helper path required');need(sha(Path(B.__file__).read_bytes())==args.base_sha256,'Frozen base helper differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256)
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied sealed input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast bytes differ');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);work=Work();events=Events()
 result={'schema':1,'scope':__doc__,'success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'production_approved':False,'features':[],'cleanup':[],'all_enabled_jobs_qualified':False,'passed_or_blocked_cases_not_repeated':['metadata','retired','compound','buyback'],'unexecuted':['ordinary_confirmation_and_jitter','ordinary_rebalance','manual_geometry_exception','LP_native_conversion','different_key_rotation','continuous_long_duration_operation']}
 for name,fn in(('roles',roles),('rpc_fault',rpc_fault)):
  case=None;common_start_failed=False
  try:
   need(time.monotonic()<work.deadline and work.count<5400,'Shared setup/cleanup budget reserve');case=Case(name,work,env,a,pins,rows,bindings,events);case.start();fn(case)
  except Exception as exc:
   common_start_failed=case is None or case.stage in('model_start','sealed_graph_identity');outcome={'feature':name,'status':'blocked'if type(exc)is FeatureBlocked else'failed','last_stage':None if case is None else case.stage,**B.safe_error(exc)}
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
    except Exception as exc:result['cleanup'].append({'feature':name,'stopped':False,**B.safe_error(exc)});result['features'].append({**case.outcome,'status':'failed','cleanup_failed':True});break
  if common_start_failed or time.monotonic()>=work.deadline or work.count>=5400:break
 try:
  B.validate_source(args.source_manifest_sha256)
  for name,(size,digest)in B.INPUTS.items():need(sha((LAB/'inputs'/name).read_bytes())==digest,'Original copied input changed')
  result['source_inputs_preserved']=True
 except Exception as exc:result['final_validation']=B.safe_error(exc)
 result.update(shared_RPC_requests=work.count,raw_submission_attempts=work.raw_attempts,reviewed_raw_forward_attempts=work.raw,shared_maximum_reviewed_cost_wei=work.maximum_cost,stock_events_bytes=events.size,tracked_children_stopped=bool(result['cleanup'])and all(r.get('stopped')is True and r.get('overflow')is False for r in result['cleanup']),whole_cgroup_cleanup_requires_external_readback=True,actual_signed_envelope_predecoded=False,postforward_exact_transaction_verification_required=True,unattempted_jobs=[n for n in('roles','rpc_fault')if n not in{r['feature']for r in result['features']}],secret_disposition={'retained_only_in_new_owned_lab':True,'contents_or_content_hashes_exported':False})
 result['success']=len(result['features'])==2 and all(r['status']=='passed'for r in result['features'])and result['tracked_children_stopped']and result.get('source_inputs_preserved')is True;save(OUT/'EVENTS.json',{'combined_stdout_stderr':''.join(events.parts)});save(OUT/'RESULT.json',result);print(json.dumps({'success':result['success'],'features':[(r['feature'],r['status'])for r in result['features']],'tracked_children_stopped':result['tracked_children_stopped']}));return 0 if result['success']else 1


if __name__=='__main__':raise SystemExit(main())
