"""ONLY unexecuted correct authorization probe and restored same-key harvest.

Permissionless collectFees stays unchanged. Reuse c7f6 pause/reset, software
revocation and RPC-fault proofs; do not rerun their case bodies. One NEW sealed
clone uses the same6000RPC/900s/24M+25%/12confirmation/240s/hourly/fee bounds.
"""
from job_cases import *


def verify_harvest(c,p,receipt):
 from zzz_ops.abi import keccak256
 need(p['key']=='harvest:'+str(BUCKET)and p['to']==c.a['vault'],'Expected exact resumed ordinary harvest')
 topic='0x'+keccak256(b'FeesCollected(uint256,uint256,uint256)').hex()
 need(any(log['address'].lower()==c.a['vault']and log['topics']and log['topics'][0]==topic and int(log['topics'][1],16)==BUCKET for log in receipt['logs']),'Resumed harvest lacks authenticated same-bucket collection event')
 need(c.k.state['last'].get('harvest:'+str(BUCKET))==int(c.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False])['timestamp'],16),'Harvest clock lacks exact successful receipt timestamp')


def auth_completion(c):
 from zzz_ops.abi import keccak256
 c.stage='new_actor_prerequisites';c.configure(maintenance={'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600})
 c.owner_on();c.call_setup('revoke_for_onchain_probe','access','setKeeper(address,bool)',c.sender,False);c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);c.stage='proper_onchain_authorization_probe'
 need(c.uint('access','keepers(address)',c.sender)==0 and c.uint('access','keeperAuthorized(address)',c.sender)==0 and c.uint('access','paused()')==0,'Expected unpaused revoked caller')
 def snapshot():
  head=c.model.rpc('eth_getBlockByNumber',['latest',False]);return{'head_number':head['number'],'head_hash':head['hash'],'owner_nonce':c.model.rpc('eth_getTransactionCount',[OWNER,'latest']),'actor_nonce':c.model.rpc('eth_getTransactionCount',[c.sender,'latest']),'physical':c.physical(),'rewards':c.money(),'NFT_rights':c.rights()}
 before=snapshot();deadline=c.now()+180;data=encode('rebalance(uint256,uint128,uint256)',BUCKET,1,deadline)
 q={'jsonrpc':'2.0','id':c.model.rpc_count+1,'method':'eth_call','params':[{'from':c.sender,'to':c.a['vault'],'data':data},'latest']};answer=c.model.request(q);error=answer.get('error',{});unauthorized='0x'+keccak256(b'Unauthorized()').hex()[:8]
 need('result'not in answer and error.get('data')==unauthorized,'Keeper-only rebalance lacks exact first-modifier Unauthorized refusal')
 # This successful call is intentionally PERMISSIONLESS and SIMULATED ONLY.
 c.stage='permissionless_collect_simulation';collect_data=encode('collectFees(uint256,uint256)',BUCKET,c.now()+180);collected=c.model.rpc('eth_call',[{'from':c.sender,'to':c.a['vault'],'data':collect_data},'latest'])
 need(collected=='0x'and snapshot()==before and c.model.raw_send_count==c.model.raw_forwarded==0 and c.k.state['pending']is None,'Read-only authorization probes changed state or submitted a transaction')
 save(c.folder/'AUTHORIZATION_PROBES.json',{'caller':c.sender,'role_revoked':True,'private_unpaused_clone':True,'keeper_only_function':'rebalance(uint256,uint128,uint256)','keeper_only_selector':data[:10],'observed_error_selector':unauthorized,'permissionless_function':'collectFees(uint256,uint256)','permissionless_selector':collect_data[:10],'permissionless_eth_call_result':collected,'all_checked_state_and_nonces_unchanged':True,'no_transaction_submitted':True,'source_basis':'inputs/PERMISSION_BASIS.json','no_permission_or_financial_policy_changed':True})
 c.owner_on();c.call_setup('restore_same_keeper_identity','access','setKeeper(address,bool)',c.sender,True);c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);c.stage='restored_same_key_due_harvest'
 need(c.uint('access','keepers(address)',c.sender)==1 and c.uint('access','keeperAuthorized(address)',c.sender)==1,'Expected restored same actor authority')
 p=c.cycle()
 if p is None:raise FeatureBlocked('Restored same-key keeper did not prepare its due ordinary harvest')
 need(p['key']=='harvest:'+str(BUCKET),'Only remaining ordinary harvest may submit; prior reset cases are not repeated')
 receipt=c.settle(p);verify_harvest(c,p,receipt)
 need(c.model.raw_send_count==c.model.raw_forwarded==1 and len(c.receipts)==1 and c.physical()==before['physical']and c.rights()==c.before_rights,'Restored harvest changed principal/rights, resent or failed exact receipt recovery')
 c.outcome.update(status='passed',proper_keeper_only_rebalance_Unauthorized=True,permissionless_harvest_eth_call_expected=True,eth_call_state_and_nonces_unchanged=True,permission_change=False,restored_same_key_harvest=p['hash'],confirmed_harvest_clock=True,prior_case_bodies_repeated=False,different_key_rotation_qualified=False)



def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source-manifest-sha256',required=True);parser.add_argument('--base-sha256',required=True);parser.add_argument('--permission-basis-sha256',required=True);args=parser.parse_args()
 need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New unprivileged private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed reviewed helper path required');need(sha(Path(B.__file__).read_bytes())==args.base_sha256,'Frozen base helper differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256);basis_raw=(LAB/'inputs/PERMISSION_BASIS.json').read_bytes();need(sha(basis_raw)==args.permission_basis_sha256,'Reviewed permission basis differs');basis=B.json_file(LAB/'inputs/PERMISSION_BASIS.json');need(basis['permission_change']is False and basis['keeper_only_probe']['function']=='rebalance(uint256,uint128,uint256)'and basis['permissionless_collect']['function']=='collectFees(uint256,uint256)','Permission basis boundary differs')
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied sealed input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast bytes differ');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);work=Work();events=Events()
 result={'schema':1,'scope':__doc__,'success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'production_approved':False,'features':[],'cleanup':[],'all_enabled_jobs_qualified':False,'passed_or_blocked_cases_not_repeated':['metadata','retired','compound','buyback','pause_resets','software_revocation','RPC_fault'],'unexecuted':['ordinary_confirmation_and_jitter','ordinary_rebalance','manual_geometry_exception','LP_native_conversion','different_key_rotation','continuous_long_duration_operation']}
 for name,fn in(('auth_completion',auth_completion),):
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
 result.update(shared_RPC_requests=work.count,raw_submission_attempts=work.raw_attempts,reviewed_raw_forward_attempts=work.raw,shared_maximum_reviewed_cost_wei=work.maximum_cost,stock_events_bytes=events.size,tracked_children_stopped=bool(result['cleanup'])and all(r.get('stopped')is True and r.get('overflow')is False for r in result['cleanup']),whole_cgroup_cleanup_requires_external_readback=True,actual_signed_envelope_predecoded=False,postforward_exact_transaction_verification_required=True,unattempted_jobs=[n for n in('auth_completion',)if n not in{r['feature']for r in result['features']}],secret_disposition={'retained_only_in_new_owned_lab':True,'contents_or_content_hashes_exported':False})
 result['success']=len(result['features'])==1 and all(r['status']=='passed'for r in result['features'])and result['tracked_children_stopped']and result.get('source_inputs_preserved')is True;save(OUT/'EVENTS.json',{'combined_stdout_stderr':''.join(events.parts)});save(OUT/'RESULT.json',result);print(json.dumps({'success':result['success'],'features':[(r['feature'],r['status'])for r in result['features']],'tracked_children_stopped':result['tracked_children_stopped']}));return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
