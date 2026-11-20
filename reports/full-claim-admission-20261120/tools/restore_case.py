"""Exact same-source full-state restore for the NEW late-tax32 resource case.

No constructors/population rerun, protocol slot interpretation, state edit,
public endpoint or key. The original native/F6 node remains stopped.
"""
from __future__ import annotations
import argparse, copy, gzip, importlib.util, json, os, subprocess, time
from pathlib import Path
from native_fixture import (NativeF6Fixture,OwnedNode,ROOT,WORK,ANVIL,ANVIL_PIN,
 M,P,SENDER,NATIVE_HASHES,sha,bytes_hash,require,save)

class RestoredNode(OwnedNode):
 def __init__(self,binary,folder,initial,state_file,source_anchor):
  super().__init__(binary,folder,initial);self.state_file=state_file;self.source_anchor=source_anchor
 def __enter__(self):
  try:
   self.folder.mkdir(parents=True,exist_ok=False);self.created=True;save(self.folder/'genesis.json',self.genesis)
   require(sha(self.binary.read_bytes())==ANVIL_PIN,'Exact reviewed Anvil')
   command=[str(self.binary),'--host','127.0.0.1','--port',str(self.port),'--accounts','0','--silent',
    '--load-state',str(self.state_file),
    '--gas-limit','32000000','--chain-id','4663','--hardfork','cancun']
   with (self.folder/'startup-stderr.log').open('xb')as errors:
    self.proc=subprocess.Popen(command,cwd=self.folder,env=M.env(self.binary),stdout=subprocess.DEVNULL,
     stderr=errors,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   until=time.monotonic()+30
   while time.monotonic()<until:
    require(self.proc.poll()is None,'Owned restored Anvil exited')
    if self.owner()=={self.proc.pid}:break
    time.sleep(.1)
   else:raise ValueError('Owned restored listener unavailable')
   require(int(self.wire('eth_chainId'),16)==4663,'Restored chain identity')
   genesis=self.wire('eth_getBlockByNumber',['0x0',False]);self.anchor=genesis['hash']
   require(self.anchor==self.source_anchor,'Exact original genesis ancestry')
   self.guard();save(self.folder/'process.json',{'pid':self.proc.pid,'port':self.port,'genesis_hash':self.anchor,
    'chain_id':4663,'command':command,'binary_sha256':ANVIL_PIN,'minimal_environment':True,
    'size_limit_override':False,'public_rpc':False,'exact_same_source_state_restore':True})
   self.mutate('anvil_impersonateAccount',[SENDER]);self.phase='setup';return self
  except BaseException:self.__exit__(*__import__('sys').exc_info());raise
 def __exit__(self,kind,error,traceback):
  if(self.folder/'cleanup.json').exists():return
  return super().__exit__(kind,error,traceback)

class RestoredFixture(NativeF6Fixture):
 def __init__(self,source,output):
  super().__init__(output);self.source=Path(source).resolve()
 def prepare(self):
  require(self.source.is_relative_to(WORK.resolve())and self.source.is_dir(),'Exact local campaign source')
  require(not self.output.exists(),'Exclusive new restored run')
  cleanup=json.loads((self.source/'node/cleanup.json').read_text())
  require(cleanup['owned_node_stopped']is True and cleanup['pending_submission']is None,'Original node closed without pending work')
  raw=(self.source/'STATE_EXPORT.json').read_bytes();export=json.loads(raw);encoded=bytes.fromhex(export['state_hex'][2:])
  require(sha(encoded)==export['state_sha256']and export['exact_source_only']and export['no_slot_reinterpretation'],'Exact source-export bytes')
  state_raw=gzip.decompress(encoded);require(len(state_raw)<=128*1024*1024,'Bounded complete state')
  state=json.loads(state_raw);manifest_raw=(self.source/'FIXTURE_MANIFEST.json').read_bytes();self.manifest=json.loads(manifest_raw)
  require(self.manifest['normal_build']==export['normal_build']==P.DEFAULT_BUILD_PROFILE,'Same exact normal F6 profile')
  self.artifacts=P.Artifacts(build_profile=P.DEFAULT_BUILD_PROFILE)
  self.contracts=dict(self.manifest['contracts']);self.runtime_pins=dict(self.manifest['expected_runtime_pins'])
  for role,target in self.contracts.items():
   code=bytes.fromhex(state['accounts'][target]['code'][2:])
   require(bytes_hash(code)==self.runtime_pins[role],'Source-state runtime matches actual constructor/native proof: '+role)
  for role,pin in NATIVE_HASHES.items():require(self.runtime_pins[role]==pin,'Same exact native external identity')
  self.ids=list(map(int,self.manifest['ids']));self.assets=self.manifest['assets'];self.bucket=int(self.manifest['bucket'])
  self.royalty_tokens=[self.contracts['currency_'+str(i)]for i in range(64)];self.owner=self.manifest['owner']
  require(self.owner==SENDER and len(set(self.ids))==32,'Exact finite source population')
  self.receipts=[];self.output.mkdir(parents=True);self.created=True
  self.state_file=self.output/'exact-anvil-state.json';self.state_file.write_bytes(state_raw)
  self.initial=json.loads((self.source/'node/genesis.json').read_text());self.source_anchor=json.loads((self.source/'node/process.json').read_text())['genesis_hash']
  self.source_export=export;self.source_state=state
  save(self.output/'RESTORE_PROVENANCE.json',{'source_campaign':str(self.source),'source_manifest_sha256':sha(manifest_raw),
   'source_export_file_sha256':sha(raw),'source_export_encoded_sha256':sha(encoded),'unpacked_state_sha256':sha(state_raw),
   'source_anchor':export['anchor'],'source_genesis':self.source_anchor,'source_best_block_number':state['best_block_number'],
   'source_headers':len(state['blocks']),'source_transactions':len(state['transactions']),
   'source_sender_nonce':state['accounts'][SENDER]['nonce'],'protocol_storage_edited':False,
   'protocol_runtime_relabelled':False,'constructors_or_population_rerun':False,
   'accepted_build_files':self.artifacts.file_pins,'accepted_current_source_pins':self.artifacts.source_pins,
   'restorer_source_sha256':sha(Path(__file__).read_bytes()),'native_fixture_source_sha256':sha(Path(__file__).with_name('native_fixture.py').read_bytes())})
  (self.output/'restore_case.py').write_bytes(Path(__file__).read_bytes());save(self.output/'FIXTURE_MANIFEST.json',self.manifest)
  return self.manifest
 def __enter__(self):
  try:
   self.node=RestoredNode(ANVIL,self.output/'node',self.initial,self.state_file,self.source_anchor)
   self.node.__enter__();self.rpc=self.node
   latest=self.rpc.call('eth_getBlockByNumber',['latest',False]);expected=self.source_export['anchor']
   require(latest['hash']==expected['hash']and latest['number']==expected['number']and latest['stateRoot']==expected['stateRoot'],'Exact restored current block/hash/state root')
   genesis=self.rpc.call('eth_getBlockByNumber',['0x0',False]);require(genesis['hash']==self.source_anchor,'Exact restored original genesis')
   deployment=self.rpc.call('eth_getBlockByNumber',[hex(self.manifest['deployment_block']),False])
   require(deployment['hash']==self.manifest['deployment_block_hash'],'Exact restored deployment-header ancestry')
   require(int(self.rpc.call('eth_getTransactionCount',[SENDER,'latest']),16)==self.source_state['accounts'][SENDER]['nonce'],'Exact restored transaction nonce')
   require(self.read('access','isSealed()')==[1]and self.read('nft','mintedCount()')==[32]and self.read('membership','totalEligible()')==[32],'Exact actual sealed source population')
   for role,target in self.contracts.items():require(self.codehash(target)==self.runtime_pins[role],'Restored exact runtime: '+role)
   require(self.read('royalties','assetCount()')==[65],'Exact source65 royalty inventory')
   save(self.output/'RESTORE_VERIFIED.json',{'exact_anchor':latest,'exact_genesis':genesis['hash'],
    'exact_deployment_header':deployment['hash'],'source_nonce':self.source_state['accounts'][SENDER]['nonce'],
    'actual_nfts':32,'actual_active':32,'actual_currencies':65,'full_runtime_pins_verified':True,
    'normal_access_sealed':True,'normal_deployment_admission_override':False})
   return self
  except BaseException:self.__exit__(*__import__('sys').exc_info());raise
 def align_pending_clock(self):
  """Capture Anvil restore clock behavior, then advance one explicit empty block."""
  latest=self.rpc.call('eth_getBlockByNumber',['latest',False]);pending=self.rpc.call('eth_getBlockByNumber',['pending',False])
  latest_open=self.read('royalties','royaltiesOpen()',block='latest')[0]
  pending_open=self.read('royalties','royaltiesOpen()',block='pending')[0]
  require(latest_open==1,'Captured source royalty opening remains valid')
  self.node.mutate('evm_setNextBlockTimestamp',[int(latest['timestamp'],16)+1]);self.node.mutate('evm_mine',[])
  after=self.rpc.call('eth_getBlockByNumber',['latest',False]);after_pending=self.rpc.call('eth_getBlockByNumber',['pending',False])
  after_open=self.read('royalties','royaltiesOpen()',block='pending')[0]
  require(after['parentHash']==latest['hash']and int(after['timestamp'],16)==int(latest['timestamp'],16)+1 and after_open==1 and int(after_pending['timestamp'],16)>=int(after['timestamp'],16),'Single coherent empty local clock block')
  require(after['stateRoot']==latest['stateRoot'],'Explicit empty clock block changes no account state')
  require(int(self.rpc.call('eth_getTransactionCount',[SENDER,'latest']),16)==self.source_state['accounts'][SENDER]['nonce'],'Clock block changes no sender nonce')
  save(self.output/'RESTORE_CLOCK.json',{'before_latest':latest,'before_pending':pending,'before_latest_royalties_open':latest_open,
   'before_pending_royalties_open':pending_open,'after_latest':after,'after_pending':after_pending,
   'after_pending_royalties_open':after_open,'explicit_empty_clock_block':True,'protocol_call_or_storage_edit':False})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--clock-followup',action='store_true');args=parser.parse_args()
 fixture=RestoredFixture(args.source,args.output);fixture.prepare()
 print(json.dumps({'phase':'prepared_exact_restore','output':str(fixture.output)}),flush=True)
 with fixture:
  if args.clock_followup:fixture.align_pending_clock()
  path=Path(__file__).with_name('late_tax_followup.py'if args.clock_followup else'late_tax_case.py');spec=importlib.util.spec_from_file_location('full_native_late_tax',path)
  checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
  result=(checks.run_late_followup if args.clock_followup else checks.run_late_tax)(fixture,fixture.output/'qualification');save(fixture.output/'LATE_TAX_RESULT.json',result)
  print(json.dumps({'phase':'late_tax32_complete','result_file':str(fixture.output/'LATE_TAX_RESULT.json')}),flush=True)
if __name__=='__main__':main()
