"""NEW direct stock Keeper storage boundaries; not a daemon or power-loss proof."""
from pathlib import Path
import argparse,contextlib,copy,datetime as dt,errno,json,os,re,stat,sys,time
import keeper_runtime as B
import keeper_jobs as J
import job_cases as C
LAB=Path('/opt/popl-ubuntu-storage-20261125-c807');SOURCE=LAB/'source/contracts';OUT=LAB/'runtime/run-001/storage-run';VOLUME=LAB/'runtime/storage'
for module in(B,J,C):module.LAB,module.SOURCE,module.OUT=LAB,SOURCE,OUT
need,save,sha=B.need,B.save,B.sha

class StorageFault:
 def __init__(self):
  s=VOLUME.lstat();need(stat.S_ISDIR(s.st_mode)and s.st_uid==65534 and stat.S_IMODE(s.st_mode)==0o700,'Private storage root differs')
  matches=[]
  for line in Path('/proc/self/mountinfo').read_text().splitlines():
   left,right=line.split(' - ',1);fields=left.split()
   if fields[4]==str(VOLUME):matches.append((fields,right.split()))
  fs=os.statvfs(VOLUME)
  need(len(matches)==1 and matches[0][1][0]=='tmpfs'and fs.f_blocks*fs.f_frsize==1048576 and s.st_dev!=VOLUME.parent.stat().st_dev,'Exact new private1MiBtmpfs required BEFORE filling')
  self.parent=VOLUME/'journal';self.parent.mkdir(mode=0o700);self.path=self.parent/'state.json';self.filler=VOLUME/'owned-full.tmp';self.mode=None;self.identity=None
  save(OUT/'FILESYSTEM.json',{'mount':str(VOLUME),'fstype':'tmpfs','bytes':fs.f_blocks*fs.f_frsize,'block_bytes':fs.f_frsize,'uid':s.st_uid,'mode':oct(stat.S_IMODE(s.st_mode)),'mount_namespace':os.readlink('/proc/self/ns/mnt'),'network_namespace':os.readlink('/proc/self/ns/net'),'host_physical_filesystem_never_filled':True,'power_loss_or_ext4_durability_qualified':False})
 def arm(self,mode):
  need(self.mode is None and mode in('EACCES','ENOSPC'),'One closed storage fault required');self.mode=mode;fs=os.statvfs(VOLUME);record={'mode':mode,'free_before':fs.f_bavail*fs.f_frsize}
  if mode=='EACCES':self.parent.chmod(0o500);record['parent_mode']='0o500'
  else:
   fd=os.open(self.filler,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);total=0;caught=None
   try:
    s=os.fstat(fd);self.identity=(s.st_dev,s.st_ino)
    while total<=1048576:
     try:total+=os.write(fd,b'\0'*4096)
     except OSError as exc:caught=exc.errno;break
    need(caught==errno.ENOSPC,'Bounded filler did not receive actual ENOSPC')
   finally:os.close(fd)
   need(os.statvfs(VOLUME).f_bavail==0,'Owned tmpfs not full');record.update(filler_bytes=total,filler_errno=caught,filler_errno_name=errno.errorcode[caught],free_after=0)
  return record
 def repair(self):
  need(self.mode in('EACCES','ENOSPC'),'No storage fault to repair')
  if self.mode=='EACCES':self.parent.chmod(0o700)
  else:
   s=self.filler.lstat();need(stat.S_ISREG(s.st_mode)and s.st_uid==65534 and(s.st_dev,s.st_ino)==self.identity,'Only exact owned filler may be unlinked');self.filler.unlink();self.identity=None
  self.mode=None;need(stat.S_IMODE(self.parent.stat().st_mode)==0o700 and os.statvfs(VOLUME).f_bavail>0,'Exact storage repair failed')

class Model(J.Model):
 def start(self,env):
  need(sha(self.binary.read_bytes())==B.ANVIL_SHA,'Anvil differs');self.controlled_genesis_timestamp=int(time.time());self.accept_hook=None
  self.child=B.Child([self.binary,'--host','127.0.0.1','--port','19591','--accounts','0','--silent','--chain-id','4663','--hardfork','cancun','--gas-limit','32000000','--gas-price','1000000000','--block-base-fee-per-gas','1','--timestamp',str(self.controlled_genesis_timestamp),'--load-state',LAB/'inputs/restore-state.json'],self.folder,env,self.folder/'anvil');end=time.monotonic()+20
  while True:
   need(self.child.process.poll()is None and not self.child.overflow,'Owned model startup failed')
   if B.owns(self.child.process.pid,19591):
    try:
     if self.rpc('eth_chainId',[])=='0x1237':break
    except(ConnectionError,OSError):pass
   need(time.monotonic()<end,'Owned model startup deadline');time.sleep(.1)
  head=self.rpc('eth_getBlockByNumber',['latest',False]);need(head['hash'].lower()==B.IMPORTED_HASH and int(head['gasLimit'],16)==32000000,'Copied anchor differs');return head
 def request(self,q):
  answer=super().request(q)
  if q['method']=='eth_sendRawTransaction'and self.accept_hook is not None:
   value=answer.get('result');need(type(value)is str and re.fullmatch(r'0x[0-9a-fA-F]{64}',value)and int(value,16),'Actual node acceptance hash absent');callback,self.accept_hook=self.accept_hook,None;callback(value.lower())
  return answer
 def guard(self):
  need(self.work.raw<2 and self.raw_forwarded<2,'Exactly two original stock sends admitted');super().guard()
C.Model=Model

def snapshot(path):
 raw=path.read_bytes();return{'sha256':sha(raw),'raw_utf8':raw.decode('utf8'),'state':json.loads(raw)}

def main():
 p=argparse.ArgumentParser()
 for name in('source-manifest','base','jobs','cases'):p.add_argument('--'+name+'-sha256',required=True)
 a=p.parse_args();need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Private unprivileged lab required')
 for module,digest in((B,a.base_sha256),(J,a.jobs_sha256),(C,a.cases_sha256)):need(sha(Path(module.__file__).read_bytes())==digest,'Frozen helper differs')
 OUT.mkdir(mode=0o700,exist_ok=False);source=B.validate_source(a.source_manifest_sha256);need(source['source_head']=='352ebe0aa479a10f2220857edadbf049720616c5'and len(source['members'])==190,'Exact reviewed production scope differs');save(OUT/'SOURCE.json',source)
 for name,(size,digest)in B.INPUTS.items():
  raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==digest,'Copied input differs')
 need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Cast differs');sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE))
 rows=B.json_file(LAB/'inputs/instances.json');addresses={r['role']:r['address'].lower()for r in rows};pins={r['role']:r['runtime_keccak256'].lower()for r in rows};need(len(rows)==len(addresses)==len(set(addresses.values()))==39,'Exact F6 graph required')
 tmp=OUT/'tmp';tmp.mkdir(mode=0o700);env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'};os.environ.update(env)
 work,events=J.Work(),J.Events();case=C.Case('storage',work,env,addresses,pins,rows,B.json_file(LAB/'inputs/bindings.json'),events);fault=None;branches=[];transactions=[]
 result={'schema':1,'success':False,'direct_stock_calls_not_normal_daemon':True,'old_passed_tests_or_worker_journeys_run':0,'public_transactions':0,'new_seals':0,'production_approved':False,'host_physical_disk_filled':False,'power_loss_or_ext4_durability_qualified':False}
 def reload():
  from keeper.monitor import Keeper
  before=fault.path.read_bytes()
  with contextlib.redirect_stdout(events),contextlib.redirect_stderr(events):case.k=Keeper(case.cfg,live=True)
  need(fault.path.read_bytes()==before,'Constructor rewrote preserved journal')
 def submit():return case.k.submit('vault','collectFees(uint256,uint256)',(J.BUCKET,case.now()+180),'harvest:'+str(J.BUCKET))
 def capture(name,mode,function,sends,known=None):
  case.stage=name;before=snapshot(fault.path);memory=copy.deepcopy(case.k.state);row={'stage':name,'mode':mode,'before':before,'raw_sends_before':case.model.raw_send_count}
  if known is None:row['fault']=fault.arm(mode)
  try:
   with contextlib.redirect_stdout(events),contextlib.redirect_stderr(events):function()
  except OSError as exc:
   need(exc.errno==getattr(errno,mode),'Different actual storage refusal');row.update(actual_errno=exc.errno,actual_errno_name=errno.errorcode[exc.errno])
  else:raise B.HarnessRefusal('Expected OS storage failure absent')
  row['after']=snapshot(fault.path);row['memory_after']=copy.deepcopy(case.k.state);row['raw_sends_after']=case.model.raw_send_count
  expected=before if known is None else known['durable_hashless'];row['expected_unchanged_checkpoint']=expected
  if known is not None:row['accepted_boundary']=copy.deepcopy(known)
  need(row['after']['raw_utf8']==expected['raw_utf8']and row['raw_sends_after']==sends,'Failed storage lost checkpoint or sent unexpectedly')
  if name.startswith('receipt'):need(case.k.state==memory,'Receipt failure did not restore in-memory pending')
  branches.append(row);save(OUT/'BRANCHES.json',branches);fault.repair()
 try:
  fault=StorageFault();case.start();case.configure(state_path=str(fault.path));case.model.review['allowed']=[('harvest','vault','collectFees(uint256,uint256)')];save(OUT/'INITIAL_JOURNAL.json',snapshot(fault.path));before={'rights':case.rights(),'physical':case.physical(),'money':case.money()};save(OUT/'BEFORE.json',before)
  for mode in('EACCES','ENOSPC'):
   capture('intent_'+mode,mode,submit,0);reload();need(case.k.state['pending']is None and case.k.state['next_nonce']==0,'Never-broadcast intent damaged durable nonce')
  for ordinal,hash_mode,receipt_mode in((0,'EACCES','ENOSPC'),(1,'ENOSPC','EACCES')):
   known={}
   def accepted(value):
    known['hash']=value;known['durable_hashless']=snapshot(fault.path);need(known['durable_hashless']['state']['pending']['hash']is None,'Accepted boundary requires durable hashless intent');save(OUT/('ACCEPTED_'+str(ordinal)+'.json'),known);known['fault']=fault.arm(hash_mode);save(OUT/('ACCEPTED_'+str(ordinal)+'.json'),known)
   case.model.accept_hook=accepted;capture('accepted_hash_'+hash_mode,hash_mode,submit,ordinal+1,known=known);need('hash'in known and fault.mode is None,'Actual accepted hash/repair absent');reload();need(case.k.state['pending']['hash']is None and case.k.state['next_nonce']==ordinal,'Hash-save failure lost original ambiguous intent')
   with contextlib.redirect_stdout(events),contextlib.redirect_stderr(events):need(case.k.poll_pending()is True,'Hashless restart did not block')
   need(case.model.raw_send_count==ordinal+1,'Hashless recovery resent');actual=case.model.rpc('eth_getTransactionByHash',[known['hash']]);need(actual.get('blockNumber')is None,'Actual hash mined before adoption')
   with contextlib.redirect_stdout(events),contextlib.redirect_stderr(events):case.k.resolve_pending(known['hash'])
   pending=copy.deepcopy(case.k.state['pending']);need(pending['hash']==known['hash'],'Stock resolver lost original hash');published=snapshot(fault.path);case.advance();receipt=case.model.rpc('eth_getTransactionReceipt',[known['hash']]);need(type(receipt)is dict and receipt['status']=='0x1','Actual paid receipt failed')
   for _ in range(12):case.advance()
   capture('receipt_'+receipt_mode,receipt_mode,case.k.poll_pending,ordinal+1);reload()
   with contextlib.redirect_stdout(events),contextlib.redirect_stderr(events):need(case.k.poll_pending()is False,'Repaired stock recovery incomplete')
   recovered=snapshot(fault.path);need(recovered['state']['pending']is None and recovered['state']['next_nonce']==ordinal+1,'Recovered exact nonce differs');raw=fault.path.read_bytes()
   with contextlib.redirect_stdout(events),contextlib.redirect_stderr(events):need(case.k.poll_pending()is False,'Repeated empty recovery differs')
   need(fault.path.read_bytes()==raw and case.model.raw_send_count==ordinal+1,'Recovery repeated charge/send');header=case.model.rpc('eth_getBlockByNumber',[receipt['blockNumber'],False]);head=case.model.rpc('eth_getBlockByNumber',['latest',False]);actual=case.model.rpc('eth_getTransactionByHash',[known['hash']])
   from zzz_ops.ethereum_fees import execution_price
   price=execution_price(actual,header,receipt);cost=int(receipt['gasUsed'],16)*price
   transactions.append({'accepted_hash':known['hash'],'known_at_acceptance':known,'published_hash':published,'original_pending':pending,'transaction_without_signature':{k:v for k,v in actual.items()if k not in('r','s','v','yParity')},'receipt':receipt,'receipt_header':header,'confirmed_head':head,'canonical_execution_price_wei':price,'paid_wei':cost,'recovered':recovered,'raw_sends':case.model.raw_send_count});case.receipts.append({'action':pending['key'],'hash':known['hash'],'receipt':receipt,'intent':pending,'actual_transaction_checked':True,'confirmations':12,'fault_recovery':True});save(OUT/'TRANSACTIONS.json',transactions)
  need(len(branches)==6 and len(transactions)==2 and case.model.raw_send_count==case.model.raw_forwarded==work.raw_attempts==2,'Exact six/two counts differ');final=snapshot(fault.path);costs={}
  for row in transactions:
   day=dt.datetime.fromtimestamp(int(row['receipt_header']['timestamp'],16),dt.timezone.utc).date().isoformat();costs[day]=costs.get(day,0)+row['paid_wei']
  need(final['state']['spent']==costs,'Exact canonical-day spending differs');need(all(int(case.model.rpc('eth_getTransactionCount',[case.sender,t]),16)==2 for t in('latest','pending')),'Actual node nonce differs');after={'rights':case.rights(),'physical':case.physical(),'money':case.money()};need(before==after,'Zero-fee storage harvest changed rights/backing');save(OUT/'FINAL_JOURNAL.json',final);save(OUT/'AFTER.json',after);case.outcome.update(status='passed',storage_boundaries=6,actual_paid_transactions=2);result.update(success=True,failures=6,actual_paid_transactions=2,final_nonce=2,actual_costs_wei=costs,raw_resends=0,exact_old_checkpoints_preserved=True,current_rights_backing_preserved=True)
 except BaseException as exc:result.update(error=B.safe_error(exc),failed_stage=getattr(case,'stage','worker'))
 finally:
  if fault is not None and fault.mode is not None:
   try:fault.repair()
   except BaseException as exc:result['success']=False;result['fault_repair_error']=B.safe_error(exc)
  if fault is not None and fault.path.is_file():
   try:
    raw=fault.path.read_bytes();need(len(raw)<=2*1024*1024,'Final journal capture bound');record={'sha256':sha(raw),'raw_utf8':raw.decode('utf8')}
    try:record['state']=json.loads(raw)
    except ValueError:record['parse_error']='invalid_json_retained_exactly'
    save(OUT/'JOURNAL_AT_STOP.json',record)
   except BaseException as exc:result['success']=False;result['journal_capture_error']=B.safe_error(exc)
  save(OUT/'BRANCHES.json',branches);save(OUT/'TRANSACTIONS.json',transactions);save(OUT/'EVENTS.json',events.parts)
  try:result['cleanup']=case.close()
  except BaseException as exc:result['success']=False;result['cleanup_error']=B.safe_error(exc)
  result.update(shared_RPC_requests=work.count,raw_attempts=work.raw_attempts,raw_forwarded=case.model.raw_forwarded,real_seconds_remaining=max(0,work.deadline-time.monotonic()));save(OUT/'RESULT.json',result)
 return 0 if result['success']else 1
if __name__=='__main__':raise SystemExit(main())
