"""Private bounded NEW job partitions; no old tests and no production adoption."""
from job_cases import *

def compound(c):
 c.stage='genuine_fee_setup';c.fees_setup();before=c.physical();funds=c.money();c.stage='stock_compound'
 c.configure(maintenance={'compound':True,'compound_idle':True,'harvest':False,'minimum_liquidity':1,'compound_interval_seconds':3600,'compound_thresholds':{ZERO:1000,ZZZ:1000},'harvest_interval_seconds':3600})
 need(c.uint('migration_budget','compoundReady(uint256)',BUCKET)==1,'Imported compound clock not due');p=c.cycle()
 if p is None:raise FeatureBlocked('Stock compound refused; inspect exact diagnostics')
 need(p['key']=='compound:'+str(BUCKET),'Unexpected compound job');c.settle(p);after=c.physical();after_funds=c.money();need(after['main']==before['main']and after['ticks']==before['ticks']and after['liquidity']>before['liquidity']and c.rights()==c.before_rights,'Compound failed physical increase or changed rights/geometry');need(c.uint('migration_budget','compoundReady(uint256)',BUCKET)==0,'Compound did not commit interval');need(c.cycle()is None,'Immediate repeated compound submitted');c.outcome.update(status='passed',before=before,after=after,funds_before=funds,funds_after=after_funds,clock_suppressed_repeat=True)

def buyback(c):
 c.stage='genuine_fee_setup';c.fees_setup();before=c.money();c.burn_amount=before[ZZZ]['buyback'];need(c.burn_amount>0,'No actual ZZZ burn reserve');supply=c.uint(ZZZ,'totalSupply()');c.outcome['copied_token_supply_read']=str(supply)
 if supply<c.burn_amount:raise FeatureBlocked('Copied model lacks adequate ZZZ supply state; burn support remains unqualified')
 c.stage='stock_direct_ZZZ_burn';c.configure(buybacks=[{'token':ZZZ,'amount':c.burn_amount,'pool_id':POOL}]);p=c.cycle()
 if p is None:raise FeatureBlocked('Stock direct burn refused; inspect diagnostics/token support')
 c.settle(p);after=c.money();need(c.uint(ZZZ,'totalSupply()')+c.burn_amount==supply and after[ZZZ]['buyback']==0 and c.rights()==c.before_rights,'Direct burn supply/reserve/rights differs');need(all(after[t]['liabilities']==before[t]['liabilities']and after[t]['claims']==before[t]['claims']for t in(ZERO,ZZZ)),'Burn touched NFT claims');c.outcome.update(status='passed',burned=str(c.burn_amount),supply_before=str(supply),supply_after=str(supply-c.burn_amount))

def metadata(c):
 from zzz_ops.abi import keccak256
 c.stage='stock_metadata2';c.configure(metadata_refresh={'enabled':True,'lifecycle_version':2,'nft':c.a['nft'],'renderer':c.a['metadata_renderer'],'renderer_code_hash':c.pins['metadata_renderer'],'maximum_count':1000,'max_per_cycle':2,'max_refresh_batch':2,'maximum_observation_age_blocks':256});p=c.cycle()
 if p is None:raise FeatureBlocked('Stock metadata refused; inspect diagnostics')
 receipt=c.settle(p);topic='0x'+keccak256(b'MetadataUpdate(uint256)').hex();ids=[int(log['topics'][1],16)if len(log['topics'])>1 else int(log['data'],16)for log in receipt['logs']if log['address'].lower()==c.a['nft']and log['topics'][0]==topic];need(ids==c.ids,'Metadata events use wrong NFT IDs');need(c.cycle()is None and c.rights()==c.before_rights,'Metadata repeated unchanged state or changed rights');c.outcome.update(status='passed',notified_ids=list(map(str,ids)),notified=copy.deepcopy(c.k.state['metadata_refresh']['notified']))

def retired(c):
 from keeper.monitor import Keeper
 c.stage='retired_worker_admission';c.configure();before=Path(c.cfg['state_path']).read_bytes();refusals=[]
 for field,value,expected in [('royalty_conversion',{'enabled':True},'Original-currency royalties prohibit conversion settings'),('principal_distribution',{'enabled':True},'Custody5 principal allocation/distribution is governance-only; disable keeper principal_distribution'),('adaptive_range',{'enabled':True},'Threshold-based rebalancing requires operator-selected ranges')]:
  cfg=copy.deepcopy(c.cfg);cfg[field]=value
  try:
   with contextlib.redirect_stdout(c.events),contextlib.redirect_stderr(c.events):Keeper(cfg,live=False)
  except ValueError as exc:need(str(exc)==expected,'Refusal came from an unexpected prerequisite');refusals.append({'setting':field,'type':'ValueError','fixed_reason':expected})
  else:raise B.HarnessRefusal('Retired/incompatible job admitted')
 need(c.model.raw_send_count==0 and Path(c.cfg['state_path']).read_bytes()==before,'Admission checks changed journal/broadcast');c.outcome.update(status='expected_refusal',refusals=refusals)

def roles(c):
 from zzz_ops.abi import keccak256
 c.stage='pause';c.call_setup('pause','access','setPaused(bool)',True);c.configure(maintenance={'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600});need(c.cycle()is None and c.model.raw_send_count==0,'Paused keeper submitted');c.owner_on();c.call_setup('unpause','access','setPaused(bool)',False);c.call_setup('revoke_new_keeper','access','setKeeper(address,bool)',c.sender,False);c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);c.stage='revocation';need(c.cycle()is None and c.model.raw_send_count==0,'Revoked keeper submitted')
 q={'jsonrpc':'2.0','id':c.model.rpc_count+1,'method':'eth_call','params':[{'from':c.sender,'to':c.a['vault'],'data':encode('collectFees(uint256,uint256)',BUCKET,c.now()+180)},'latest']};error=c.model.request(q).get('error',{});need(type(error.get('data'))is str and error['data'][:10]=='0x'+keccak256(b'Unauthorized()').hex()[:8],'Revoked wallet lacks typed on-chain refusal');c.owner_on();c.call_setup('restore_keeper','access','setKeeper(address,bool)',c.sender,True);c.model.rpc('anvil_stopImpersonatingAccount',[OWNER]);c.stage='restored_authority';p=c.cycle()
 if p is None:raise FeatureBlocked('Restored keeper did not resume due work')
 c.settle(p);c.outcome.update(status='passed',paused_no_broadcast=True,revoked_typed_refusal=True,reenabled_key_resumed=True,replacement_key_not_qualified=True)

def rpc_fault(c):
 c.stage='pre_submission_read_fault';c.configure(maintenance={'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600});c.model.fault={'method':'eth_getBlockByNumber','params':None};need(c.cycle()is None and c.model.raw_send_count==0,'Failed prereads broadcast');c.model.fault=None;c.stage='saved_hash_receipt_fault';p=c.cycle()
 if p is None:raise FeatureBlocked('Read recovery did not resume due work')
 c.settle(p,fault=True);need(c.model.raw_send_count==1 and c.model.fault_attempts>0,'Saved-hash fault recovery resent/missed fault');c.outcome.update(status='passed',pre_send_no_submission=True,post_send_identical_hash_no_resend=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--base-sha256',required=True);p.add_argument('--trader-sha256',required=True);args=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Unprivileged dedicated private namespace required');need(Path(__file__).resolve().is_relative_to(LAB/'source/helpers'),'Fixed private helper path required');need(sha(Path(B.__file__).read_bytes())==args.base_sha256,'Frozen base helper differs');need(sha((LAB/'inputs/TRADER.json').read_bytes())==args.trader_sha256,'Retained trader artifact differs');OUT.mkdir(mode=0o700,exist_ok=False);B.validate_source(args.source_manifest_sha256)
 for name,(size,digest)in B.INPUTS.items():raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Copied Cast binary differs');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));rows=B.json_file(LAB/'inputs/instances.json');need(len(rows)==39,'Normal graph count differs');a={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};bindings=B.json_file(LAB/'inputs/bindings.json');tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env);work=Work();events=Events();result={'schema':1,'scope':'NEW directed stock job methods/real Cast; copied sealed F6; not a daemon soak or global fork','success':False,'public_transactions':0,'new_seals':0,'old_test_bodies_run':0,'production_approved':False,'features':[],'cleanup':[],'all_enabled_jobs_qualified':False,'unexecuted':['ordinary_confirmation_and_jitter','ordinary_rebalance','manual_geometry_exception','LP_native_conversion','different_key_rotation','continuous_long_duration_operation']}
 for name,fn in [('compound',compound),('buyback',buyback),('metadata',metadata),('retired',retired),('roles',roles),('rpc_fault',rpc_fault)]:
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
 result.update(shared_RPC_requests=work.count,raw_submission_attempts=work.raw_attempts,reviewed_raw_forward_attempts=work.raw,shared_maximum_reviewed_cost_wei=work.maximum_cost,stock_events_bytes=events.size,tracked_children_stopped=bool(result['cleanup'])and all(r.get('stopped')is True and r.get('overflow')is False for r in result['cleanup']),whole_cgroup_cleanup_requires_external_readback=True,actual_signed_envelope_predecoded=False,postforward_exact_transaction_verification_required=True,unattempted_jobs=[n for n in('compound','buyback','metadata','retired','roles','rpc_fault')if n not in{r['feature']for r in result['features']}],secret_disposition={'retained_only_in_new_owned_lab':True,'contents_or_content_hashes_exported':False})
 result['success']=len(result['features'])==6 and all(r['status']in('passed','expected_refusal')for r in result['features'])and result['tracked_children_stopped']and result.get('source_inputs_preserved')is True;save(OUT/'EVENTS.json',{'combined_stdout_stderr':''.join(events.parts)});save(OUT/'RESULT.json',result);print(json.dumps({'success':result['success'],'features':[(r['feature'],r['status'])for r in result['features']],'tracked_children_stopped':result['tracked_children_stopped']}));return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
