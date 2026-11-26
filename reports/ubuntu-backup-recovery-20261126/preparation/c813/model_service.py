"""NEW c813 stock known-pending backup/restore composition; preparation only.

Same-host isolated fixture. No old test body, constructor, activation, public
transaction, new sealing, original environment or installed journal adoption.
Raw configurations/journals/packages remain PRIVATE; public files are curated.
"""
from pathlib import Path
import argparse, copy, datetime as dt, importlib.util, json, os, re, signal, stat, sys, threading, time
import keeper_runtime as B
import keeper_jobs as J
import job_cases as C

LAB=Path('/opt/popl-ubuntu-backup-recovery-20261126-c813')
SOURCE=LAB/'source/contracts'; OUT=LAB/'runtime/run-001/model'; CONTROL=LAB/'control'
for module in (B,J,C):module.LAB,module.SOURCE,module.OUT=LAB,SOURCE,OUT
need,save,sha=B.need,B.save,B.sha
HEAD='5662a81ad9c9c5953d3578974e0c5840d626ba97'
PINS={'keeper/monitor.py':'90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f',
 'keeper/recovery_bundle.py':'fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268',
 'scripts/keeper-recovery.py':'450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'}
TX_FIELDS=('hash','from','to','input','nonce','value','gas','gasPrice','type','chainId',
 'maxFeePerGas','maxPriorityFeePerGas','blockHash','blockNumber','transactionIndex')

def raw_file(path):
 st=path.lstat();need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and not path.is_symlink()
  and 0<st.st_size<=2*1024*1024,'Private snapshot identity differs')
 with path.open('rb')as f:raw=f.read(2*1024*1024+1)
 need(len(raw)==st.st_size,'Private snapshot changed');return raw

def private_copy(path,raw):
 need(len(raw)<=2*1024*1024,'Private evidence bound differs')
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())

def root_marker(name):
 need(name in ('FENCED.json','RECOVERY_COMPLETE.json','DRY_COMPLETE.json'),'Closed marker name')
 path=CONTROL/name
 if not path.exists():return None
 st=path.lstat();need(stat.S_ISREG(st.st_mode)and st.st_uid==0 and st.st_nlink==1
  and stat.S_IMODE(st.st_mode)==0o644 and st.st_size<=65536,'Root marker differs')
 return B.json_file(path,65536)

class Model(J.Model):
 def start(self,env):
  need(sha(self.binary.read_bytes())==B.ANVIL_SHA,'Anvil differs')
  self.controlled_genesis_timestamp=int(time.time())
  self.child=B.Child([self.binary,'--host','127.0.0.1','--port','19591','--accounts','0',
   '--silent','--chain-id','4663','--hardfork','cancun','--gas-limit','32000000',
   '--gas-price','1000000000','--block-base-fee-per-gas','1','--timestamp',
   str(self.controlled_genesis_timestamp),'--load-state',LAB/'inputs/restore-state.json'],
   self.folder,env,self.folder/'anvil')
  end=time.monotonic()+20
  while True:
   need(self.child.process.poll()is None and not self.child.overflow,'Owned node stopped')
   if B.owns(self.child.process.pid,19591):
    try:
     if self.rpc('eth_chainId',[])=='0x1237':break
    except(ConnectionError,OSError):pass
   need(time.monotonic()<end,'Node startup deadline');time.sleep(.1)
  h=self.rpc('eth_getBlockByNumber',['latest',False]);need(h['hash'].lower()==B.IMPORTED_HASH
   and int(h['gasLimit'],16)==32000000,'Copied F6 anchor differs');return h
 def guard(self):
  need(self.raw_send_count==self.work.raw_attempts==1 and self.raw_forwarded==0,
   'Exactly one fresh harvest submission is admitted')
  super().guard();need(self.work.raw==1,'One guarded harvest only')

C.Model=Model

def financial(case):
 # Each vector retains raw integer units. Harvest can change fee accounting;
 # unsigned recovery must not change the post-inclusion vectors.
 result={'rights':case.rights(),'physical':case.physical(),'money':case.money()}
 result['vault_balances']={J.ZERO:int(case.model.rpc('eth_getBalance',[case.a['vault'],'latest']),16),
  J.ZZZ:case.uint(J.ZZZ,'balanceOf(address)',case.a['vault'])}
 return result

def tool(case,action,extra):
 from keeper.cast_process import run_cast
 argv=['/usr/bin/python3','-B',str(SOURCE/'scripts/keeper-recovery.py'),action,
  '--config',str(case.config_path),*extra]
 result=run_cast(argv,env=case.env,timeout=90)
 need(result.returncode==0,'Unsigned recovery tool refused')
 match=re.search(r'^(?:Manifest|Restore plan) SHA-256: ([0-9a-f]{64})$',result.stdout,re.M)
 need(match is not None,'Unsigned tool digest absent')
 return {'action':action,'returncode':result.returncode,'output_sha256':sha((result.stdout+result.stderr).encode()),
  'digest':match.group(1),'configuration_sha256':sha(raw_file(case.config_path)),
  'signing_enabled':False,'secret_contents_exported':False}

def main():
 p=argparse.ArgumentParser()
 for k in ('source-manifest','base','jobs','cases','independent'):p.add_argument('--'+k+'-sha256',required=True)
 a=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=
  os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New private unprivileged lab required')
 for m,h in ((B,a.base_sha256),(J,a.jobs_sha256),(C,a.cases_sha256)):
  need(sha(Path(m.__file__).read_bytes())==h,'Frozen setup helper differs')
 OUT.mkdir(mode=0o700,exist_ok=False);source=B.validate_source(a.source_manifest_sha256)
 need(source['source_head']==HEAD and all(sha((SOURCE/k).read_bytes())==v for k,v in PINS.items()),'Exact current source required')
 for n,(size,h)in B.INPUTS.items():
  raw=(LAB/'inputs'/n).read_bytes();need(len(raw)==size and sha(raw)==h,'Copied F6 input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Cast differs')
 sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE))
 rows=B.json_file(LAB/'inputs/instances.json');addresses={r['role']:r['address'].lower()for r in rows}
 pins={r['role']:r['runtime_keccak256'].lower()for r in rows}
 need(len(rows)==len(addresses)==len(set(addresses.values()))==39,'Exact F6 graph required')
 tmp=OUT/'tmp';tmp.mkdir(mode=0o700)
 env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8',
  'HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'}
 os.environ.update(env);work,events=J.Work(),J.Events()
 case=C.Case('supervisor',work,env,addresses,pins,rows,B.json_file(LAB/'inputs/bindings.json'),events)
 stop=threading.Event();signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
 result={'schema':1,'success':False,'source_head':HEAD,'scope':'same_host_isolated_known_hash_pending_backup_restore',
  'old_test_bodies_run':0,'public_transactions':0,'new_seals':0,'production_approved':False}
 initial=included=final=None;original_cfg=original_journal=None;target=None;intent=None;accepted=None
 try:
  case.start();case.configure(maintenance={'compound':False,'compound_idle':False,'harvest':True,
   'minimum_liquidity':1,'harvest_interval_seconds':3600})
  case.model.review['allowed']=[('harvest','vault','collectFees(uint256,uint256)')]
  case.lock_guard.__exit__(None,None,None);case.lock_guard,case.k=None,None
  original_cfg=raw_file(case.config_path);journal=Path(case.cfg['state_path'])
  private_copy(case.folder/'ORIGINAL_CONFIG.json',original_cfg)
  st=B.json_file(journal);need(st['pending']is None and st['next_nonce']==0 and not st['spent'],'Unused journal required')
  need(case.uint('strategy','needsRebalance(uint256)',J.BUCKET)==0 and
   case.uint('strategy','rangeUpdatePending(uint256)',J.BUCKET)==0,'Harvest-only partition required')
  initial=financial(case);save(case.folder/'FINANCIAL_INITIAL.json',initial)
  for _ in range(12):case.advance()
  save(OUT/'READY.json',{'schema':1,'source_head':HEAD,'namespace':os.readlink('/proc/self/ns/net'),
   'configuration_path':str(case.config_path),'configuration_sha256':sha(original_cfg),
   'semantic_configuration_sha256':sha(B.enc(case.cfg)),'state_path':str(journal),'health_path':case.cfg['health_path'],
   'sender':case.sender,'monitor_argv':['/usr/bin/python3','-m','keeper.monitor','--config',str(case.config_path),'--live'],
   'monitor_working_directory':str(SOURCE),'all_guard_limits_unchanged':True})
  case.stage='await_durable_known_hash'
  phases=set();backup_digest=None;restore_digest=None
  while not stop.wait(.2):
   need(time.monotonic()<work.deadline,'Shared900second bound exceeded')
   need(case.model.raw_send_count<=1 and work.raw_attempts<=1 and case.model.raw_forwarded<=1 and work.raw<=1,'Unexpected second send')
   need(raw_file(case.config_path)==original_cfg,'Original configuration changed')
   if 'pending'not in phases:
    raw=raw_file(journal);state=json.loads(raw);pending=state.get('pending')
    if type(pending)is not dict or type(pending.get('hash'))is not str:continue
    accepted=pending['hash'];intent=copy.deepcopy(pending)
    need(re.fullmatch('0x[0-9a-f]{64}',accepted)and int(accepted,16)>0 and pending['nonce']==state['next_nonce']==0
     and pending['key']=='harvest:'+str(J.BUCKET),'Known pending identity differs')
    tx=case.model.rpc('eth_getTransactionByHash',[accepted])
    from zzz_ops.ethereum_fees import fee_cap,transaction_chain_id
    need(tx['from'].lower()==case.sender and tx['to'].lower()==pending['to']and tx['input']==pending['data']
     and int(tx['nonce'],16)==0 and int(tx['value'],16)==0 and transaction_chain_id(tx)==4663
     and int(tx['gas'],16)==pending['fee_review']['gas_limit'] and fee_cap(tx)==pending['fee_review']['max_fee_per_gas']
     and tx.get('blockNumber')is None and case.model.rpc('eth_getTransactionReceipt',[accepted])is None,'Unmined actual transaction differs')
    original_journal=raw;private_copy(case.folder/'PENDING.json',raw)
    save(OUT/'PENDING_READY.json',{'schema':1,'accepted_hash':accepted,'journal_sha256':sha(raw),
     'configuration_sha256':sha(original_cfg),'unmined':True,'next_nonce':0,'pending_fee_review':pending['fee_review']})
    phases.add('pending');case.stage='await_root_source_fence'
   if 'restore'not in phases:
    marker=root_marker('FENCED.json')
    if marker is None:continue
    need(marker.get('schema')==1 and marker.get('keeper_fenced_empty')is True and marker.get('automatic_restart_inhibited')is True
     and marker.get('accepted_hash')==accepted and marker.get('journal_sha256')==sha(original_journal), 'Exact source fence marker absent')
    need(raw_file(journal)==original_journal and case.model.rpc('eth_getTransactionReceipt',[accepted])is None,'Source changed before backup')
    bundle=case.folder/'bundle-001';restore=case.folder/'restore-001'
    backup=tool(case,'backup',['--working-directory',str(SOURCE),'--output',str(bundle)])
    backup_digest=backup['digest'];common=['--bundle',str(bundle),'--manifest-sha256',backup_digest,
     '--max-age-seconds','900','--minimum-next-nonce','0']
    verification=tool(case,'verify',common);restoration=tool(case,'restore',common+['--output',str(restore)])
    restore_digest=restoration['digest'];restored=raw_file(restore/'keeper-state.json')
    need(restored==original_journal and raw_file(journal)==original_journal,'Restored journal must be byte exact')
    private_copy(case.folder/'RESTORED_BEFORE_LOAD.json',restored)
    target=copy.deepcopy(case.cfg);target.update(state_path=str(restore/'keeper-state.json'),
     health_path=str(restore/'health.json'),lock_path=str(restore/'keeper.lock'))
    changed=sorted(k for k in set(case.cfg)|set(target)if B.enc(case.cfg.get(k))!=B.enc(target.get(k)))
    need(changed==['health_path','lock_path','state_path'],'Only runtime paths may change')
    save(case.folder/'TARGET_CONFIG.json',target)
    evidence={'schema':1,'source_head':HEAD,'known_hash':accepted,'configuration_raw_sha256':sha(original_cfg),
     'configuration_semantic_sha256':sha(B.enc(case.cfg)),'target_configuration_raw_sha256':sha(raw_file(case.folder/'TARGET_CONFIG.json')),
     'target_configuration_semantic_sha256':sha(B.enc(target)),'changed_configuration_keys':changed,
     'pending_journal_sha256':sha(original_journal),'restored_journal_sha256':sha(restored),
     'backup_manifest_sha256':backup_digest,'restore_plan_sha256':restore_digest,
     'tool_runs':[backup,verification,restoration],'bundle_file_names':sorted(x.name for x in bundle.iterdir()),
     'restore_file_names':sorted(x.name for x in restore.iterdir()),'raw_configuration_exported':False,
     'signer_material_bundled':False,'same_host_only':True,'fence_marker':marker}
    save(case.folder/'EVIDENCE.json',evidence)
    save(OUT/'RESTORE_READY.json',{'schema':1,'accepted_hash':accepted,'journal_sha256':sha(restored),
     'target_configuration_sha256':sha(raw_file(case.folder/'TARGET_CONFIG.json')),
     'target_semantic_configuration_sha256':sha(B.enc(target)),'source_fenced_before_backup':True})
    for _ in range(12):case.advance()
    receipt=case.model.rpc('eth_getTransactionReceipt',[accepted]);head=case.model.rpc('eth_getBlockByNumber',['latest',False])
    block=case.model.rpc('eth_getBlockByHash',[receipt['blockHash'],False]);tx=case.model.rpc('eth_getTransactionByHash',[accepted])
    need(receipt['status']=='0x1' and int(head['number'],16)-int(receipt['blockNumber'],16)+1==12,'Exactly12 confirmations required')
    canonical={'schema':1,'accepted_hash':accepted,'receipt':receipt,'receipt_block':block,'head':head,
     'transaction_without_signature':{k:tx.get(k)for k in TX_FIELDS},'confirmations':12}
    save(case.folder/'CANONICAL.json',canonical);included=financial(case);save(case.folder/'FINANCIAL_INCLUDED.json',included)
    save(OUT/'INCLUDED.json',{'schema':1,'accepted_hash':accepted,'confirmations':12,'financial_included_sha256':sha(B.enc(included))})
    phases.add('restore');case.stage='await_unsigned_target_receipt_recovery'
   if 'settled'not in phases:
    marker=root_marker('RECOVERY_COMPLETE.json')
    if marker is None:continue
    need(marker.get('schema')==1 and marker.get('signing_enabled')is False and marker.get('accepted_hash')==accepted
     and marker.get('actual_exit_status')==1,'First unsigned stock recovery result differs')
    target_journal=Path(target['state_path']);raw=raw_file(target_journal);state=json.loads(raw)
    receipt=case.model.rpc('eth_getTransactionReceipt',[accepted]);block=case.model.rpc('eth_getBlockByHash',[receipt['blockHash'],False])
    from zzz_ops.ethereum_fees import execution_price
    tx=case.model.rpc('eth_getTransactionByHash',[accepted])
    # Preserve the current fee derivation: type-2 execution price comes from
    # signed caps and the canonical inclusion block, not Anvil's derived field.
    paid=int(receipt['gasUsed'],16)*execution_price(tx,block,receipt)
    day=dt.datetime.fromtimestamp(int(block['timestamp'],16),dt.timezone.utc).date().isoformat()
    need(state['pending']is None and state['next_nonce']==1 and sum(map(int,state['spent'].values()))==paid
     and int(state['spent'][day])==paid and state['last'][intent['key']]==int(block['timestamp'],16)
     and state['receipt_anchor']=={'number':int(block['number'],16),'hash':block['hash'],
      'timestamp':int(block['timestamp'],16),'nonce':0},'Canonical receipt accounting differs')
    health=B.json_file(Path(target['health_path']))
    need(health.get('status')=='degraded'and health.get('pending')is False and health.get('live')is False
     and health.get('configuration_sha256')==sha(B.enc(target))and health.get('rebalance_confirmation_health',{}).get('policy',{}).get('state')=='pending_recovery',
     'First cycle must be specifically metadata-degraded after confirmed recovery')
    private_copy(case.folder/'SETTLED_JOURNAL.json',raw)
    save(OUT/'SETTLED.json',{'schema':1,'accepted_hash':accepted,'journal_sha256':sha(raw),
     'recovery_fields':{k:state.get(k)for k in ('pending','next_nonce','spent','receipt_anchor','last_fee_observation','last')},
     'health':health,'paid_wei':paid,'actual_exit_status':1,'source_fenced':True})
    phases.add('settled');case.stage='await_unsigned_fresh_dry_cycle'
   if 'dry'not in phases:
    marker=root_marker('DRY_COMPLETE.json')
    if marker is None:continue
    need(marker.get('schema')==1 and marker.get('signing_enabled')is False and marker.get('accepted_hash')==accepted
     and marker.get('actual_exit_status')==0,'Fresh unsigned cycle exit differs')
    raw=raw_file(Path(target['state_path']));state=json.loads(raw);settled=B.json_file(case.folder/'SETTLED_JOURNAL.json')
    # Ordinary read-only scheduling intentionally advances its durable turn.
    # This fixture has one bucket and all optional workers disabled, so only
    # conversion_turn and bucket_cursor are admitted to change on the dry cycle.
    changed=sorted(k for k in set(state)|set(settled)if B.enc(state.get(k))!=B.enc(settled.get(k)))
    need(set(changed)<={'conversion_turn','bucket_cursor'} and
     state.get('conversion_turn')==(settled.get('conversion_turn',0)+1)%3 and state.get('bucket_cursor')==1,
     'Unexpected journal change in unsigned dry scheduling')
    need(all(B.enc(state.get(k))==B.enc(settled.get(k))for k in
     ('pending','next_nonce','spent','receipt_anchor','last_fee_observation','last')),
     'Fresh dry cycle changed financial recovery fields')
    health=B.json_file(Path(target['health_path']))
    need(health.get('status')=='dry_run_v2'and health.get('pending')is False and health.get('live')is False
     and health.get('configuration_sha256')==sha(B.enc(target)),'Fresh complete dry cycle absent')
    private_copy(case.folder/'DRY_JOURNAL.json',raw)
    save(OUT/'DRY.json',{'schema':1,'accepted_hash':accepted,'journal_sha256':sha(raw),'health':health,'actual_exit_status':0,
     'changed_scheduler_keys':changed,'conversion_turn_before':settled.get('conversion_turn',0),
     'conversion_turn_after':state.get('conversion_turn'),'bucket_cursor_after':state.get('bucket_cursor')})
    need(financial(case)==included,'Unsigned recovery changed physical financial state')
    node_nonces={t:int(case.model.rpc('eth_getTransactionCount',[case.sender,t]),16)for t in('latest','pending')}
    need(node_nonces=={'latest':1,'pending':1}
     and case.model.raw_send_count==case.model.raw_forwarded==work.raw_attempts==work.raw==1,'Duplicate transaction/nonce detected')
    need(raw_file(journal)==original_journal and raw_file(case.config_path)==original_cfg,'Source journal or configuration changed')
    save(case.folder/'SOURCE_PRESERVED.json',{'schema':1,'configuration_sha256':sha(original_cfg),
     'journal_sha256':sha(original_journal),'original_configuration_unchanged':True,'original_journal_unchanged':True,
     'node_nonces':node_nonces,'raw_attempts':work.raw_attempts,'raw_forwarded':case.model.raw_forwarded,
     'raw_validated':work.raw,'raw_gateway_attempts':case.model.raw_send_count})
    phases.add('dry');result.update(success=True,accepted_hash=accepted,confirmed_harvests=1,raw_attempts=1,
     once_only_canonical_receipt_accounting=True,source_fenced_before_backup=True,exact_restoration_before_load=True,
     target_signing_enabled=False,fresh_dry_run_v2=True,post_inclusion_financial_unchanged=True)
    save(OUT/'COMPLETE.json',result);case.stage='await_root_stop';break
  need(result['success'],'Complete backup recovery composition not observed')
  while not stop.wait(.2):need(time.monotonic()<work.deadline,'Root cleanup exceeded900seconds')
 except Exception as exc:result.update(success=False,failure_stage=case.stage,**B.safe_error(exc))
 finally:
  # Capture physical after-state even when a late assertion failed, before
  # closing the private node. Never repeat a successful old test body.
  try:
   if case.cfg is not None:
    final=financial(case);save(case.folder/'FINANCIAL_FINAL.json',final)
    result['final_financial_capture_complete']=True
    result['post_inclusion_financial_unchanged']=included is not None and included==final
  except Exception as exc:result.update(success=False,final_financial_error=B.safe_error(exc))
  try:
   # This NEW standalone checker reads exact private evidence and returns only
   # approved summaries. It never imports the keeper, reads keys or uses RPC.
   checker=LAB/'source/helpers/independent_private.py'
   meta=B.json_file(LAB/'MANIFEST.json');pin=meta['members']['source/helpers/independent_private.py']
   raw=raw_file(checker);need(len(raw)==pin['bytes']and sha(raw)==pin['sha256']==a.independent_sha256,'Independent checker differs')
   spec=importlib.util.spec_from_file_location('fixed_c813_independent',checker)
   mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
   checked=mod.verify();save(OUT/'INDEPENDENT.json',checked)
   need(checked.get('success')is True,'Independent private evidence refused')
   result['independent_private_review_passed']=True
  except Exception as exc:result.update(success=False,independent_review_error=B.safe_error(exc))
  try:
   B.validate_source(a.source_manifest_sha256)
   need(all(sha((LAB/'inputs'/n).read_bytes())==h for n,(_,h)in B.INPUTS.items()),'Original F6 inputs changed')
  except Exception as exc:result.update(success=False,source_final_error=B.safe_error(exc))
  try:case.outcome.update(status='passed'if result['success']else'failed');result['cleanup']=case.close()
  except Exception as exc:result.update(success=False,cleanup_error=B.safe_error(exc))
  result.update(shared_RPC_requests=work.count,raw_attempts=work.raw_attempts,raw_forwarded=case.model.raw_forwarded,
   secrets='retained only in new private lab; no secret contents or hashes exported')
  try:save(OUT/'EVENTS.json',{'fixture_setup_events':''.join(events.parts)});save(OUT/'RESULT.json',result)
  except Exception:return 1
 return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
