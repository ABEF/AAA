"""Fixed c813 native controls. Import performs no service or signer action."""
from pathlib import Path
import json, os, re, stat
import native_base as N

LAB=Path('/opt/popl-ubuntu-backup-recovery-20261126-c813')
MODEL_UNIT=LAB.name+'-model.service'; KEEPER_UNIT=LAB.name+'-keeper.service'; RESOLVE_UNIT=LAB.name+'-resolve.service'
for k,v in {'LAB':LAB,'MODEL_UNIT':MODEL_UNIT,'KEEPER_UNIT':KEEPER_UNIT,'RESOLVE_UNIT':RESOLVE_UNIT,
 'UNITS':(MODEL_UNIT,KEEPER_UNIT,RESOLVE_UNIT),'SOURCE':LAB/'source/contracts','HELPERS':LAB/'source/helpers',
 'RUN':LAB/'runtime/run-001','MODEL':LAB/'runtime/run-001/model',
 'LIVE':LAB/'runtime/run-001/model/supervisor/actor','CONFIG':LAB/'runtime/run-001/model/supervisor/actor/config.json',
 'READY':LAB/'runtime/run-001/model/READY.json'}.items():setattr(N,k,v)
CONTROL=LAB/'control'; CASE=N.MODEL/'supervisor'; TARGET=CASE/'TARGET_CONFIG.json'; need=N.need

def read(path,maximum=2*1024*1024):return json.loads(N._read(path,maximum,owners=(0,N.UID)))
def source_identity():
 N._ownership();ready=read(N.READY,65536);raw=N._read(N.CONFIG,256*1024,owners=(0,N.UID));cfg=json.loads(raw)
 need(ready.get('configuration_sha256')==N.digest(raw)and ready.get('configuration_path')==str(N.CONFIG)
  and ready.get('state_path')==str(N.LIVE/'state.json'),'Original ready configuration differs')
 exact={'chain_id':4663,'rpc_urls':['http://127.0.0.1:19592'],'cast_binary':str(LAB/'tools/cast'),
  'keystore':str(N.LIVE/'secrets/keeper'),'password_file':str(N.LIVE/'secrets/password'),
  'state_path':str(N.LIVE/'state.json'),'health_path':str(N.LIVE/'health.json'),'lock_path':str(N.LIVE/'keeper.lock'),
  'interval_seconds':240,'confirmations':12,'max_gas_limit':24000000,'max_gas_price_wei':'5000000000',
  'max_transaction_cost_wei':'10000000000000000','max_daily_cost_wei':'50000000000000000',
  'l1_fee_allowance_wei':'0','receipt_fee_policy':'included',
  'maintenance':{'compound':False,'compound_idle':False,'harvest':True,'minimum_liquidity':1,'harvest_interval_seconds':3600},
  'bucket_overrides':{},'adaptive_range':{'enabled':False},'royalty_conversion':{'enabled':False},
  'lp_conversion':{'enabled':False},'metadata_refresh':{'enabled':False},'principal_distribution':{'enabled':False},'buybacks':[]}
 need(all(cfg.get(k)==v for k,v in exact.items()),'Keeper guards/jobs differ');return ready,cfg,raw

def private_record(name,value):
 need(name in ('RECOVER_STARTED.json','DRY_STARTED.json','TARGET_POLICY.json','SOURCE_STOP_REQUEST.json'),'Closed private control record')
 if not CONTROL.exists():CONTROL.mkdir(mode=0o755);os.chmod(CONTROL,0o755,follow_symlinks=False)
 need(CONTROL.is_dir()and CONTROL.lstat().st_uid==0,'Root control directory required')
 path=CONTROL/name;raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
 need(len(raw)<=65536 and not os.path.lexists(path),'Control record already exists or exceeds bound')
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())

def start_model(pins):
 N._ownership();expected={'source_manifest_sha256','base_sha256','jobs_sha256','cases_sha256','model_sha256','independent_sha256'}
 need(type(pins)is dict and set(pins)==expected and all(type(v)is str and re.fullmatch('[0-9a-f]{64}',v)for v in pins.values()),'Model source pins differ')
 for path,key in ((LAB/'inputs/SOURCE_MANIFEST.json','source_manifest_sha256'),
  (N.HELPERS/'keeper_runtime.py','base_sha256'),(N.HELPERS/'keeper_jobs.py','jobs_sha256'),
  (N.HELPERS/'job_cases.py','cases_sha256'),(N.HELPERS/'model_service.py','model_sha256'),
  (N.HELPERS/'independent_private.py','independent_sha256')):N._read(path,2*1024*1024,expected=pins[key])
 for name,pin in (('cast',N.CAST_SHA),('anvil',N.ANVIL_SHA)):N._read(LAB/'tools'/name,128*1024*1024,expected=pin)
 need(all(N._properties(u).get('LoadState')=='not-found'for u in N.UNITS),'New native names must be unused')
 for path in (LAB/'runtime',N.RUN,N.RUN/'native-tmp'):N._runtime_directory(path)
 need(not os.path.lexists(N.MODEL),'Model output already exists')
 policy=N._common_policy('model');policy.update(Restart='no',TimeoutStopSec='120s')
 env={'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(N.HELPERS),
  'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONNOUSERSITE':'1',
  'POPL_LAB_HOST_NETWORK_NAMESPACE':os.readlink('/proc/self/ns/net'),'TMPDIR':str(N.RUN/'native-tmp')}
 argv=['/usr/bin/python3','-B',str(N.HELPERS/'model_service.py')]
 for k in ('source_manifest_sha256','base_sha256','jobs_sha256','cases_sha256','independent_sha256'):argv+=['--'+k.replace('_','-'),pins[k]]
 return N._start(MODEL_UNIT,argv,policy,env)

def start_keeper():
 ready,cfg,raw=source_identity();model=N._properties(MODEL_UNIT)
 need(model.get('ActiveState')=='active'and int(model.get('MainPID','0'))>1,'Private model is inactive')
 proc=N._proc(int(model['MainPID']));need(proc is not None and proc['uid']==N.UID
  and proc['network_namespace']==ready['namespace']and proc['network_namespace']!=os.readlink('/proc/self/ns/net'),'Model namespace differs')
 argv,policy,env=N._keeper_launch_parts()
 need(argv==ready['monitor_argv']and str(N.SOURCE)==ready['monitor_working_directory'],'Stock source argv differs')
 result=N._start(KEEPER_UNIT,argv,policy,env);N._keeper_policy_checks(result['properties']);return result

def stopkeeper():
 result=N.native_request_stop(KEEPER_UNIT)
 if not(CONTROL/'SOURCE_STOP_REQUEST.json').exists():private_record('SOURCE_STOP_REQUEST.json',result)
 return result

def fence():
 ready,cfg,raw=source_identity();N._inactive_empty(KEEPER_UNIT)
 pending=read(N.MODEL/'PENDING_READY.json',65536);state_raw=N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID));state=json.loads(state_raw)
 need(pending.get('unmined')is True and pending.get('journal_sha256')==N.digest(state_raw)
  and state['next_nonce']==0 and type(state['pending'])is dict and state['pending']['hash']==pending['accepted_hash'],
  'Known pending source journal differs')
 values=N._properties(KEEPER_UNIT)
 request=json.loads(N._read(CONTROL/'SOURCE_STOP_REQUEST.json',65536))
 need(request.get('unit')==KEEPER_UNIT and request.get('stop_requested')is True
  and request.get('before',{}).get('ActiveState')=='active','Recorded explicit source stop request absent')
 need(values.get('ActiveState')=='inactive'and values.get('SubState')=='dead'and
  (values.get('Result')=='success'or values.get('LoadState')=='not-found'),
  'An explicit completed source stop is required')
 # systemctl stop cancels this transient unit's restart job. No timer/path/socket
 # activation is created in this closed capsule; PID disappearance alone is not proof.
 jobs=N._run(['/usr/bin/systemctl','list-jobs','--no-legend','--no-pager'])
 need(jobs['returncode']==0 and KEEPER_UNIT.encode()not in jobs['stdout'],'Source unit still has a manager job')
 return {'schema':1,'keeper_fenced_empty':True,'automatic_restart_inhibited':True,
  'accepted_hash':pending['accepted_hash'],'journal_sha256':N.digest(state_raw),
  'configuration_sha256':N.digest(raw),'explicit_systemctl_stop_completed':True,
  'no_source_activation_units_created':True,'native_snapshot':N.native_status()}

def target_identity():
 ready,cfg,raw=source_identity();N._inactive_empty(KEEPER_UNIT)
 marker=read(CONTROL/'FENCED.json',65536)
 need(marker.get('keeper_fenced_empty')is True and marker.get('automatic_restart_inhibited')is True,'Source fence marker absent')
 need(N.digest(N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID)))==marker['journal_sha256'],'Source journal changed after fence')
 target_raw=N._read(TARGET,256*1024,owners=(0,N.UID));target=json.loads(target_raw)
 expected=dict(cfg,state_path=str(CASE/'restore-001/keeper-state.json'),
  health_path=str(CASE/'restore-001/health.json'),lock_path=str(CASE/'restore-001/keeper.lock'))
 need(json.dumps(target,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':')),
  'Only the three reviewed runtime paths may change')
 included=read(N.MODEL/'INCLUDED.json',65536);need(included['accepted_hash']==marker['accepted_hash']and included['confirmations']==12,'Inclusion barrier absent')
 return marker,target,target_raw

def _unsigned(kind):
 need(kind in ('recover','dry'),'Closed unsigned stage');marker,target,target_raw=target_identity()
 N._inactive_empty(RESOLVE_UNIT)
 if kind=='recover':
  need(not(CONTROL/'RECOVER_STARTED.json').exists(),'Recovery already started')
  need(N._read(Path(target['state_path']),2*1024*1024,owners=(0,N.UID))==
   N._read(CASE/'RESTORED_BEFORE_LOAD.json',2*1024*1024,owners=(0,N.UID)),'Exact restored bytes changed before stock load')
  secret=N.LIVE/'secrets';st=secret.lstat();need(stat.S_ISDIR(st.st_mode)and st.st_uid==N.UID and stat.S_IMODE(st.st_mode)==0o700,'Only private lab secrets may be restricted')
  os.chmod(secret,0o000,follow_symlinks=False)
  policy=N._common_policy('resolve');policy.update(Restart='no',RemainAfterExit='yes',TimeoutStopSec='120s',
   JoinsNamespaceOf=MODEL_UNIT,Requires=MODEL_UNIT,After=MODEL_UNIT)
  private_record('TARGET_POLICY.json',policy)
 else:
  need((CONTROL/'RECOVERY_COMPLETE.json').exists()and(N.MODEL/'SETTLED.json').exists()
   and not(CONTROL/'DRY_STARTED.json').exists(),'Confirmed settled first cycle required')
  need(stat.S_IMODE((N.LIVE/'secrets').lstat().st_mode)==0,'Signer paths must stay inaccessible')
  policy=json.loads(N._read(CONTROL/'TARGET_POLICY.json',65536))
  for s in ('stdout','stderr'):
   path=N.RUN/('native-resolve.'+s+'.log');N._read(path,N.MAX_OUTPUT,owners=(0,N.UID))
 if N._properties(RESOLVE_UNIT).get('LoadState')!='not-found':
  done=N._run(['/usr/bin/systemctl','reset-failed',RESOLVE_UNIT]);need(done['returncode']==0,'Owned failed unit reset refused')
 env={'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(N.SOURCE),
  'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONNOUSERSITE':'1',
  'TMPDIR':str(N.MODEL/'tmp'),'HOME':str(N.MODEL/'unsigned-home')}
 argv=['/usr/bin/python3','-m','keeper.monitor','--config',str(TARGET),'--once']
 need('--live'not in argv and '--initialize-state'not in argv,'Unsigned argv differs')
 if N._properties(RESOLVE_UNIT).get('LoadState')=='not-found':launch=N._start(RESOLVE_UNIT,argv,policy,env)
 else:
  need(kind=='dry','Unexpected previously loaded unsigned unit')
  launched=N._run(['/usr/bin/systemctl','start','--no-block',RESOLVE_UNIT]);need(launched['returncode']==0,'Owned target start refused')
  launch={'unit':RESOLVE_UNIT,'requested_policy':policy,'direct_exec_argv':argv,'properties':N._properties(RESOLVE_UNIT),'same_loaded_unit':True}
 record={'schema':1,'kind':kind,'accepted_hash':marker['accepted_hash'],'target_configuration_sha256':N.digest(target_raw),
  'signing_enabled':False,'signer_directory_mode':'0000','launch':launch}
 private_record('RECOVER_STARTED.json'if kind=='recover'else'DRY_STARTED.json',record)
 return record

def recover():return _unsigned('recover')
def dry():return _unsigned('dry')

def status():
 snapshot=N.native_status();value=snapshot['units'][RESOLVE_UNIT];props=value['properties']
 kind='dry'if(CONTROL/'DRY_STARTED.json').exists()else'recover'if(CONTROL/'RECOVER_STARTED.json').exists()else None
 complete_name='DRY_COMPLETE.json'if kind=='dry'else'RECOVERY_COMPLETE.json'
 terminal=(props.get('ActiveState')in ('inactive','failed')or
  props.get('ActiveState')=='active'and props.get('SubState')=='exited')
 if kind and not(CONTROL/complete_name).exists()and terminal and props.get('MainPID','0')=='0'and not value['cgroup']['pids']:
  start=json.loads(N._read(CONTROL/('DRY_STARTED.json'if kind=='dry'else'RECOVER_STARTED.json'),65536))
  status=int(props.get('ExecMainStatus','-1'));need(props.get('ExecMainCode')=='1'and status==(0 if kind=='dry'else 1),'Unsigned cycle exit differs')
  health=read(CASE/'restore-001/health.json')
  need(health.get('live')is False and health.get('pending')is False and health.get('status')==('dry_run_v2'if kind=='dry'else'degraded'),
   'Unsigned health differs')
  marker={'schema':1,'signing_enabled':False,'accepted_hash':start['accepted_hash'],'actual_exit_status':status,
   'direct_exec_argv':start['launch']['direct_exec_argv']}
  receipt={'schema':1,'kind':kind,'marker':marker,'native':value,'launch':start['launch'],
   'target_configuration_sha256':start['target_configuration_sha256'],'signer_directory_mode':'0000',
   'stock_health':health,'target_journal_sha256':N.digest(N._read(CASE/'restore-001/keeper-state.json',2*1024*1024,owners=(0,N.UID)))}
  snapshot['unsigned_completion']={'kind':kind,'receipt':receipt,'marker':marker}
 return snapshot

def stop_owned():return N.native_stop_owned()
