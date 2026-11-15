"""Offline reconciliation only: reads immutable owned-chain captures; no RPC/process/transaction is created."""
from pathlib import Path
import gzip,importlib.util,io,json,sys
import argparse,hashlib,stat,zipfile
if not __debug__:raise RuntimeError("Evidence verification requires Python assertions enabled")
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
ART=E/'focused-fixed/out/ManualRecoveryQualification.t.sol/ManualRecoveryQualificationTest.json'
ROWS=[('C14','adapted-testActualManualC14ConsolidatesExistingMain','active-c14','rpc/c14-2/active-c14','manual','C',True),
 ('D14','adapted-testActualManualD14ReplacesBothLegs','active-d14','rpc/d14-1/active-d14','manual','D',True),
 ('park-current-journey','adapted-testActualParkedD14RetainsFinancialGuards','parked14-before-park','rpc/parked14-1/parked-d14','park','park',True),
 ('ParkedD14','adapted-testActualParkedD14RetainsFinancialGuards','parked-d14','rpc/parked14-1/parked-d14','manual','D',True)]
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
 if action!='park':
  accepted=json.loads((parent.parent/'REFERENCE_ACCEPTANCE.json').read_bytes())
  assert accepted['reference_swap_accepted'] and accepted['quoted_output_equals_actual_output'] and accepted['quoted_full_state_armed_and_after_swap_validated']
  assert accepted['actual_receipt_sha256']==hashlib.sha256((p/'receipt.json').read_bytes()).hexdigest()
  pins=case['bindings'];trace=captured['receipt-trace']
  def flat(frame):
   yield frame
   for child in frame.get('calls',[]):yield from flat(child)
  frames=list(flat(trace));selector=lambda text:'0x'+m.keccak256(text.encode()).hex()[:8]
  quotes=[frame for frame in frames if frame.get('to')==pins['balancing_router']['address'] and frame.get('input','').startswith(selector('quoteSwap(bytes32,bool,uint256)')) and not frame.get('error')]
  assert len(quotes)==1
  quote=quotes[0];qi=m.decode_words('0x'+quote['input'][10:]);qo=m.decode_words(quote['output']);args_=review['arguments']
  assert len(qi)==3 and len(qo)==6 and int(qi[0],16)==int(args_['swapPool'],16) and bool(int(qi[1],16))==args_['zeroForOne'] and int(qi[2],16)==int(args_['amountIn'])
  swaps=[frame for frame in frames if frame.get('from')==pins['liquidity']['address'] and frame.get('to')==pins['pool_manager']['address'] and frame.get('input','').startswith(selector('swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)')) and not frame.get('error')]
  assert len(swaps)==1
  call=m.decode_words('0x'+swaps[0]['input'][10:]);key=[int(word,16) for word in call[:5]]
  assert '0x'+m.keccak256(bytes.fromhex(''.join(call[:5]))).hex()==args_['swapPool']
  assert key==[0,int(case['asset']['address'],16),500,10,0]
  delta=int(m.decode_words(swaps[0]['output'])[0],16);signed=lambda x:x-(1<<128) if x>=1<<127 else x
  d0=signed((delta>>128)&((1<<128)-1));d1=signed(delta&((1<<128)-1));spent,out=(d0,d1) if args_['zeroForOne'] else (d1,d0)
  assert -spent==int(args_['amountIn']) and out==int(qo[0],16) and out>=int(args_['minimumOut'])
  armed=[frame for frame in frames if frame.get('to')==pins['oracle']['address'] and frame.get('input','').startswith(selector('beforeSwap(address,address,bytes32,(uint160,int24,uint24,uint24,uint128))')) and not frame.get('error')]
  assert len(armed)==1 and m.decode_words('0x'+armed[0]['input'][10:])[-5:]==qo[1:]
  assert any(frame.get('to')==pins['oracle']['address'] and frame.get('input','').startswith(selector('afterSwap()')) and not frame.get('error') for frame in frames)
  original=json.loads((p/'selection.json').read_bytes())
  assert all(original[field]==args_[field] for field in ('amountIn','minimumOut','minimumLiquidity','deadline','lower','upper','swapPool','zeroForOne'))
  assert args_['checks']=='14' and int(args_['minimumLiquidity'])>1
  result['same_reference_exact_quote_and_full_state_proof']=True
 results.append(result)
out={'schema':1,'successful':True,'offline_only':True,'new_evm_executions':0,'new_cli_executions':0,'rows':results,
 'unique_transactions':len(set(row['transaction_hash'] for row in results)),'accepted_manual_rows':3,'accepted_park_journey_rows':1,'earlier_confirmed_park_preserved':0,
 'new_unit_methods':25,'adapted_unit_methods':3,'unchanged_old_methods_rerun':0,'rehearsal_source_sha256':m.sha((ROOT/'scripts/rehearse-manual-recovery.py').read_bytes()),
 'archive_scope':manifest['scope'],'external_full_archive':manifest.get('external_full_archive'),
 'evidence_archive_sha256':hashlib.sha256(store.path.read_bytes()).hexdigest() if store.archive else None}
m.save(args.output,out)
print(json.dumps({'successful':True,'rows':len(results),'manual_rows':3,'transactions':out['unique_transactions'],'gas':[{k:row[k] for k in ('name','final_estimate','exact_25_percent_padding','receipt_gas_used')} for row in results]},indent=2))
