"""Verify complete accepted unit bytes/callbacks and read-wire slices without extraction, RPC or execution."""
import argparse,collections,gzip,hashlib,io,json,stat,zipfile
from pathlib import Path,PurePosixPath
if not __debug__:raise RuntimeError('Verification requires assertions enabled')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,default=Path(__file__).with_name('unit-evidence.zip'));p.add_argument('--output',required=True,type=Path);args=p.parse_args()
assert args.evidence.is_file() and not args.output.exists();H=lambda raw:hashlib.sha256(raw).hexdigest()
archive=zipfile.ZipFile(args.evidence);entries=archive.infolist();names=[e.filename for e in entries];assert len(names)<=4096 and len(set(names))==len(names)
for entry in entries:
 name=entry.filename;path=PurePosixPath(name);assert not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name
 assert entry.file_size<=64*1024*1024 and not stat.S_ISLNK(entry.external_attr>>16)
read_total=0
def read(name):
 global read_total
 assert name in names
 with archive.open(name) as stream:raw=stream.read(64*1024*1024+1)
 read_total+=len(raw);assert len(raw)<=64*1024*1024 and read_total<=1024*1024*1024
 return raw
manifest=json.loads(read('MANIFEST.json'));tests=json.loads(read('FINAL_TESTS.json'));proof=json.loads(read('CALLBACK_TRACE_PROOFS.json'))
expected={row['path']+'/forge.json':row for row in tests['accepted_new']+tests['accepted_adapted']};assert len(expected)==28 and tests['new_unique_passed']==25 and tests['adapted_unique_passed']==3
callbacks={row['method']:row for row in proof['proofs']};assert len(callbacks)==9
verified=[];verified_callbacks=[];wire=[]
for name,entry in manifest['files'].items():
 raw=read(name);assert len(raw)==entry['bytes'] and H(raw)==entry['sha256']
 if name in expected:
  prior=expected[name];assert H(raw)==prior['forge_sha256'];data=json.loads(raw)
  rows=[(suite,method,row) for suite,group in data.items() for method,row in group.get('test_results',{}).items()]
  assert len(rows)==1;_,method,row=rows[0];assert method.split('(')[0]==prior['method'] and row['status']=='Success'
  verified.append(prior['method'])
  if prior['method'] in callbacks:
   cb=callbacks[prior['method']];arena=next(value['arena'] for kind,value in row['traces'] if kind=='Execution');node=arena[cb['callback_frame_index']];t=node['trace']
   assert t['success'] and t['output']=='0x' and t['data']==cb['callback_data'] and node['logs']==cb['confirmed_callback_logs'] and node['logs']
   assert int(t['data'][-64:],16)==1
   for outer in cb['failed_outer_ancestors_after_callback_return']:
    actual=arena[outer['index']]['trace'];assert not actual['success'] and actual['address']==outer['address'] and actual['output']==outer['reason']
   verified_callbacks.append(prior['method'])
 if name.endswith('rpc-records.read-calls.json.gz'):
  with gzip.GzipFile(fileobj=io.BytesIO(raw)) as compressed:decoded=compressed.read(64*1024*1024+1)
  assert len(decoded)<=64*1024*1024;records=json.loads(decoded);groups={}
  for record in records:
   if record['method']!='eth_call':continue
   tx=record['params'][0]
   if tx.get('from','').lower()!='0x000000000000000000000000000000000000a0a0' or not tx.get('gas'):continue
   key=(tx.get('to'),tx.get('data'))
   groups.setdefault(key,collections.Counter())[int(tx['gas'],16)]+=1
  wire.append({'path':name,'original_records':len(records),'governance_call_groups':[{'to':to,'selector':data[:10],'calldata_sha256':H(bytes.fromhex(data[2:])),'gas_counts':dict(counts)} for (to,data),counts in groups.items()]})
assert len(verified)==28 and len(set(verified))==28 and len(verified_callbacks)==9
stage1=read('NEW_HOST_STAGE1.sol');stage2=read('NEW_HOST_STAGE2.sol');final=read('source/test/ManualReferenceSwapQualification.t.sol')
d2=json.loads(read('NEW_HOST_STAGE2_DELTA.json'));d3=json.loads(read('NEW_HOST_STAGE3_DELTA.json'))
assert stage1.replace(d2['only_change']['before'].encode(),d2['only_change']['after'].encode())==stage2
assert stage2.replace(d3['before'].encode(),d3['after'].encode())==final
# Exact four simulation groups across three independent owned nodes: manual
# initial/final/full-cap plus one padded call; park has three of each.
counts=[list(map(int,group['gas_counts'].values())) for capture in wire for group in capture['governance_call_groups']]
assert len(counts)==4 and sum(sorted(group)==[1,3] for group in counts)==3 and sum(sorted(group)==[3,3] for group in counts)==1
result={'schema':1,'successful':True,'offline_only':True,'new_evm_or_cli_runs':0,'zip_sha256':H(args.evidence.read_bytes()),'manifest_sha256':H(read('MANIFEST.json')),'complete_original_unit_files_verified':28,'new_methods':25,'adapted_methods':3,'callback_actual_success_before_later_outer_failure_verified':verified_callbacks,'source_stage_equivalence_verified':True,'actual_governance_call_counts':wire,'fullsize_source_or_profile_adoption':False}
with args.output.open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,indent=2)+'\n')
print(json.dumps({'successful':True,'original_unit_files':28,'callback_proofs':9,'wire_groups':4,'new_evm_or_cli_runs':0}))
