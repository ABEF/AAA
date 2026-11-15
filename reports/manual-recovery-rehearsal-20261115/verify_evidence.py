"""Offline reconciliation only: reads immutable owned-chain captures; no RPC/process/transaction is created."""
from pathlib import Path
import gzip,importlib.util,io,json,sys
import argparse,hashlib,stat,zipfile
from pathlib import PurePosixPath
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repository',required=True,type=Path,help='Checkout containing the source-pinned rehearsal module; never a node URL')
parser.add_argument('--evidence',type=Path,default=Path(__file__).with_name('public-evidence.zip'))
parser.add_argument('--output',required=True,type=Path,help='New local reconciliation file; existing files are never replaced')
args=parser.parse_args();ROOT=args.repository.resolve()
class Evidence:
 def __init__(self,path):
  self.path=path.resolve();self.total=0;self.archive=None
  if self.path.is_file():
   self.archive=zipfile.ZipFile(self.path);entries=self.archive.infolist();names=[entry.filename for entry in entries]
   assert len(names)<=4096 and len(set(names))==len(names)
   for entry in entries:
    name=entry.filename;part=PurePosixPath(name)
    assert not part.is_absolute() and '..' not in part.parts and '\\' not in name and ':' not in name
    assert entry.file_size<=64*1024*1024 and not stat.S_ISLNK(entry.external_attr>>16)
   self.names=set(names)
  else:assert self.path.is_dir()
 def exists(self,name):
  return name in self.names if self.archive else (self.path/name).is_file()
 def read(self,name):
  part=PurePosixPath(name);assert not part.is_absolute() and '..' not in part.parts
  if self.archive:
   with self.archive.open(name) as member:raw=member.read(64*1024*1024+1)
  else:
   target=(self.path/name).resolve();assert target.is_relative_to(self.path);assert target.stat().st_size<=64*1024*1024
   raw=target.read_bytes()
  self.total+=len(raw);assert len(raw)<=64*1024*1024 and self.total<=1024*1024*1024
  return raw
class VirtualPath:
 def __init__(self,store,name=''):self.store=store;self.name=name
 def __truediv__(self,name):return VirtualPath(self.store,str(PurePosixPath(self.name)/name))
 @property
 def parent(self):return VirtualPath(self.store,str(PurePosixPath(self.name).parent))
 def read_bytes(self):return self.store.read(self.name)
 def exists(self):return self.store.exists(self.name)
 def relative_to(self,other):assert self.store is other.store;return PurePosixPath(self.name).relative_to(other.name or '.')
store=Evidence(args.evidence);E=VirtualPath(store)
manifest=json.loads((E/'MANIFEST.json').read_bytes())
for name,entry in manifest['files'].items():
 raw=store.read(name);assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
source=ROOT/'scripts/rehearse-manual-recovery.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['files']['source/scripts/rehearse-manual-recovery.py']['sha256']
spec=importlib.util.spec_from_file_location('manual_rehearsal',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ART=E/'current-host/out/ManualRecoveryQualification.t.sol/ManualRecoveryQualificationTest.json'
ROWS=[('C14','0-attempt3','active-c14','rpc/c14-attempt3/active-c14','manual','C',True),
 ('D14','1','active-d14','rpc/d14-1/active-d14','manual','D',True),
 ('park-first-confirmed-not-resent','2','parked14-before-park','rpc/parked14-1/parked-d14','park','park',False),
 ('park-accepted-journey','2','parked14-before-park','rpc/parked14-2/parked-d14','park','park',True),
 ('ParkedD14','2','parked-d14','rpc/parked14-2/parked-d14','manual','D',True),
 ('ParkedD0','3','parked-d0','rpc/parked0-1/parked-d0','manual','D',True)]
results=[]
for name,export,label,folder,operation,action,accepted in ROWS:
 parent=E/folder;p=parent/operation
 captured={key:json.loads((p/(key+'.json')).read_bytes()) for key in ('before','after','receipt','transaction','review','call-trace','receipt-trace','cli-execution')}
 record_path=parent/'rpc-records.json.gz' if (parent/'rpc-records.json.gz').exists() else parent/'rpc-records.post-receipt.json.gz'
 with gzip.GzipFile(fileobj=io.BytesIO(record_path.read_bytes())) as compressed:decoded=compressed.read(64*1024*1024+1)
 assert len(decoded)<=64*1024*1024
 records=json.loads(decoded)
 receipt=captured['receipt'];tx=captured['transaction'];review=captured['review']
 first=next(index for index,row in enumerate(records) if row['method']=='eth_getTransactionReceipt' and row['params']==[receipt['transactionHash']] and (row['response'].get('result') or {}).get('status')=='0x1')
 class Replay:
  queries=[]
  def call(self,method,params):
   assert method in ('eth_call','eth_getBlockByHash')
   matches=[row['response']['result'] for row in records[first+1:] if row['method']==method and row['params']==params and 'result' in row['response']]
   assert matches and all(item==matches[0] for item in matches)
   self.queries.append({'method':method,'params':params,'matches':len(matches)})
   return matches[0]
 cases=(m.parse_export(E/'exports'/export,ART) if (E/'exports'/export/'forge.json').exists() else
  json.loads((E/'CAPTURE_CASES.json').read_bytes())[export])
 case=next(case for case in cases if case['label']==label)
 replay=Replay();replay.queries=[]
 assertions=m.verify_post(replay,case,captured['before'],captured['after'],receipt,action=action,
  minimum_liquidity=None if action=='park' else int(review['arguments']['minimumLiquidity']),closed_by_receipt=True)
 initial,final=(review['simulation'][key] for key in ('initial','final'));estimate=int(final['estimated_gas'])
 padded=int(final.get('padded_gas',final.get('transaction_gas')))
 assert padded==(estimate*125+99)//100 and padded<=24_000_000 and int(final['gas_limit_cap'])==24_000_000
 assert int(final['block_gas_limit'])==32_000_000 and tx['input']==review['transaction']['data'] and int(tx['gas'],16)==padded
 assert tx['from']==case['governance'] and tx['to']==case['bindings']['principal_exit']['address'] and int(tx['value'],16)==0
 assert int(receipt['status'],16)==1 and int(receipt['gasUsed'],16)<=padded
 assert int(captured['call-trace']['gasUsed'],16)==int(captured['receipt-trace']['gasUsed'],16)==int(receipt['gasUsed'],16)
 assert captured['cli-execution']['exit_code']==0 and captured['cli-execution']['source_unchanged'] and captured['cli-execution']['default_time_time_clock']
 included=replay.call('eth_getBlockByHash',[receipt['blockHash'],False]);assert int(included['timestamp'],16)<=review['expires_at']
 result={'name':name,'accepted_flow':accepted,'path':str(p.relative_to(E)).replace('\\','/'),'transaction_hash':receipt['transactionHash'],
  'action':action,'selected_checks':None if action=='park' else review['arguments']['checks'],
  'initial_estimate':int(initial['estimated_gas']),'final_estimate':estimate,'exact_25_percent_padding':padded,'receipt_gas_used':int(receipt['gasUsed'],16),
  'headroom_to_24M':24_000_000-padded,'effective_gas_price_wei':int(receipt['effectiveGasPrice'],16),'assertions':assertions,
  'cli_seconds':captured['cli-execution']['seconds'],'cli_posts':captured['cli-execution']['recorded_rpc_requests'],
  'captured_evidence_sha256':{key:m.sha((p/(key+'.json')).read_bytes()) for key in captured},'recorded_post_receipt_queries':replay.queries,
  'owned_node_stopped':json.loads((parent/'cleanup.json').read_bytes())['owned_node_stopped']}
 assert result['owned_node_stopped']
 if (p/'reference-negative-trace.json').exists():
  trace=json.loads((p/'reference-negative-trace.json').read_bytes());summary=json.loads((p/'reference-negative.json').read_bytes())
  def flatten(frame):
   yield frame
   for child in frame.get('calls',[]):yield from flatten(child)
  flat=list(flatten(trace));fp=case['bindings']['custody_validation']['address']
  selectors=tuple('0x'+m.keccak256((name+'('+m.manual.TUPLE+')').encode()).hex()[:8] for name in ('emergencyFingerprint','consolidationEmergencyFingerprint'))
  swap='0x'+m.keccak256(b'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)').hex()[:8]
  swaps=[index for index,frame in enumerate(flat) if frame.get('to')==case['bindings']['pool_manager']['address'] and frame.get('input','').startswith(swap) and not frame.get('error')]
  fingerprints=[(index,frame['output']) for index,frame in enumerate(flat) if frame.get('to')==fp and frame.get('input','').startswith(selectors) and not frame.get('error')]
  assert trace.get('error') and swaps and len(set(value for _,value in fingerprints))>1
  assert any(index>max(swaps) and value!=fingerprints[0][1] for index,value in fingerprints)
  assert summary['host_atomic_before']==summary['host_atomic_after'] and summary['actual_state_unchanged'] and summary['host_quote']['swap_and_lp_floors_feasible']
  result['reference_as_execution_negative']={'actual_successful_core_swaps':len(swaps),'fingerprint_outputs':fingerprints,
   'changed_successful_fingerprint_after_core_swap':True,'failed_balance_frame_present':any(frame.get('to')==case['bindings']['liquidity']['address'] and frame.get('input','').startswith('0xdcd87610') and frame.get('error') for frame in flat),
   'actual_atomic_rejection':True,'scope':'Actual trace facts plus unchanged source semantics, not guessed from generic revert text.'}
 results.append(result)
out={'schema':1,'successful':True,'offline_only':True,'new_evm_executions':0,'new_cli_executions':0,'rows':results,
 'unique_transactions':len(set(row['transaction_hash'] for row in results)),'accepted_manual_rows':4,'accepted_park_journey_rows':1,'earlier_confirmed_park_preserved':1,
 'new_producer_methods':4,'unchanged_old_methods_rerun':0,'rehearsal_source_sha256':m.sha((ROOT/'scripts/rehearse-manual-recovery.py').read_bytes()),
 'archive_scope':manifest['scope'],'external_full_archive':manifest.get('external_full_archive'),
 'evidence_archive_sha256':hashlib.sha256(store.path.read_bytes()).hexdigest() if store.archive else None}
m.save(args.output,out)
print(json.dumps({'successful':True,'rows':len(results),'manual_rows':4,'transactions':out['unique_transactions'],'gas':[{k:row[k] for k in ('name','final_estimate','exact_25_percent_padding','receipt_gas_used')} for row in results]},indent=2))
