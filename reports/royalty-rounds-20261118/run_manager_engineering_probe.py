"""UNQUALIFIED engineering probe: only one Manager runtime is transplanted.
No new full-graph qualification, deployment, signer, existing chain or storage graft.
"""
from pathlib import Path
from contextlib import contextmanager
import copy,gzip,hashlib,importlib.util,json,os,socket,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
D=V/'royalty-rounds-20261118/manager/engineering01';F=V/'royalty-rounds-20261118/full02'
sys.path.insert(0,str(R));from zzz_ops.abi import keccak256,decode_words
sha=lambda raw:hashlib.sha256(raw).hexdigest()
GETTERS={'access':'access()','balancingRouter':'balancingRouter()','positionExecutor':'positionOperator()',
 'posm':'positionManager()','stateView':'stateView()','poolManager':'poolManager()','permit2':'permit2()'}

def main():
 compile_result=json.loads((D/'RESULT.json').read_bytes());assert compile_result['exit_code']==0 and compile_result['runtime_object_byte_identical']
 assert sha((D/'compiler-output.json').read_bytes())==compile_result['output_sha256']
 actual=json.loads((D/'compiler-output.json').read_bytes());obj=actual['contracts']['src/ZZZLiquidityManager.sol']['ZZZLiquidityManager']['evm']['deployedBytecode']
 # This recorded engineering stage belongs to full02, never the final13 checker.
 spec=importlib.util.spec_from_file_location('owned_rounds_verifier',R/'reports/royalty-rounds-20261118/full-flow-baseline/source-helpers/verify_full_flow.py');helper=importlib.util.module_from_spec(spec)
 saved=sys.argv;sys.argv=[str(spec.origin),'full02']
 try:
  spec.loader.exec_module(helper)
  helper.R=R  # Rebase only the project path after archiving exact helper bytes.
 finally:sys.argv=saved
 folder=F/'local-rpc02/rounds-999-rotated-zzz-allslow';original=json.loads((folder/'VERIFICATION.json').read_bytes())
 assert original['verification_complete']and original['royalty_trace_verification']['verified']
 case=original['profile'];alloc,omitted,merge=helper.source_state(case);genesis=json.loads((folder/'genesis.json').read_bytes());assert genesis['alloc']==alloc
 manager=case['pins']['liquidity'];old_runtime=helper.code_bytes(alloc[manager]['code'])
 assert helper.keccak256(old_runtime).hex()==case['runtime_hashes']['liquidity'][2:]
 evidence={'schema':1,'scope':'UNQUALIFIED Manager-only runtime transplant engineering probe; not fresh constructor/full graph/source profile/deployment evidence',
  'old_verified_case':str(folder),'old_verification_sha256':sha((folder/'VERIFICATION.json').read_bytes()),'original_authenticated_state_merge':merge,
  'new_compiler_input_sha256':sha((D/'compiler-input.json').read_bytes()),'new_compiler_output_sha256':compile_result['output_sha256'],
  'old_runtime_sha256':sha(old_runtime),'old_runtime_keccak256':'0x'+helper.keccak256(old_runtime).hex(),
  'production_approved':False,'meets_reviewed_execution_profile':False,'profile_qualification':False,'public_transactions':0}
 (D/'PROBE_START.json').write_text(json.dumps(evidence,indent=2)+'\n')

 @contextmanager
 def node(name,state):
  target=D/name;target.mkdir(exist_ok=False);material=copy.deepcopy(genesis);material['alloc']=state
  raw=json.dumps(material,separators=(',',':')).encode();(target/'genesis.json').write_bytes(raw)
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  env={key:os.environ[key]for key in('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')if key in os.environ};env['PATH']=str(helper.ANVIL.parent)+os.pathsep+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32')
  assert sha(helper.ANVIL.read_bytes())==helper.ANVIL_SHA256
  command=[str(helper.ANVIL),'--host','127.0.0.1','--port',str(port),'--accounts','0','--silent','--init',str(target/'genesis.json'),
   '--gas-limit','32000000','--chain-id',str(case['block']['chain_id']),'--hardfork','cancun','--no-mining']
  proc=None;rpc=None;stateproof={'command':command,'genesis_sha256':sha(raw),'owned_node_stopped':False,'public_transactions':0}
  try:
   with(target/'anvil.log').open('xb')as log:proc=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   stateproof.update(owned_pid=proc.pid,listener_ownership=helper.listener_identity(proc,port));rpc=helper.RPC(port)
   assert helper.quantity(rpc.call('eth_chainId'))==case['block']['chain_id'];head=rpc.call('eth_getBlockByNumber',['latest',False])
   assert helper.quantity(head['number'])==case['block']['number']and helper.quantity(head['timestamp'])==case['block']['timestamp']
   anchor={'blockHash':head['hash'],'requireCanonical':True};stateproof['anchor']=head
   def read(address,signature,*args,count=1):
    data=helper.selector(signature)+''.join(value[2:].rjust(64,'0')if isinstance(value,str)else f'{value:064x}'for value in args)
    words=decode_words(rpc.call('eth_call',[{'from':case['sender'],'to':address,'data':data},anchor]));assert len(words)==count,(signature,'unexpected output size');return words
   yield rpc,anchor,read,stateproof
  finally:
   if proc is not None:
    proc.terminate()
    try:proc.wait(timeout=10)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
    stateproof['owned_node_stopped']=proc.poll()is not None
   if rpc is not None:
    (target/'rpc-records.json.gz').write_bytes(gzip.compress(json.dumps(rpc.records,separators=(',',':')).encode(),mtime=0));stateproof['rpc_records_sha256']=sha((target/'rpc-records.json.gz').read_bytes());stateproof['rpc_requests']=len(rpc.records)
   (target/'NODE.json').write_text(json.dumps(stateproof,indent=2)+'\n')

 def read_immutables(read):return {name:'0x'+read(manager,getter)[0][-40:]for name,getter in GETTERS.items()}
 def crosscheck(read,values):
  pins=case['pins'];assert values['posm']==pins['position_manager']and values['stateView']==pins['state_view']and values['poolManager']==pins['pool_manager']
  assert values['positionExecutor']==pins['lp_position_executor']and values['balancingRouter']==pins['balancing_router']
  assert '0x'+read(values['posm'],'permit2()')[0][-40:]==values['permit2']
  assert '0x'+read(values['posm'],'poolManager()')[0][-40:]==values['poolManager']
  assert '0x'+read(values['stateView'],'poolManager()')[0][-40:]==values['poolManager']
  assert '0x'+read(values['balancingRouter'],'access()')[0][-40:]==values['access']
  assert '0x'+read(values['balancingRouter'],'poolManager()')[0][-40:]==values['poolManager']
  assert '0x'+read(values['positionExecutor'],'liquidityManager()')[0][-40:]==manager
  assert '0x'+read(values['positionExecutor'],'access()')[0][-40:]==values['access']
  assert '0x'+read(values['access'],'module(bytes32)','0x'+keccak256(b'ZZZLiquidityManager').hex())[0][-40:]==manager
 with node('old-getters',alloc)as(rpc,anchor,read,stateproof):
  values=read_immutables(read);crosscheck(read,values)
  for address in values.values():assert helper.code_bytes(rpc.call('eth_getCode',[address,anchor]))
 evidence['old_getters_and_controls']=values
 new_runtime=bytearray.fromhex(obj['object']);fills=[];seen={}
 for identifier,spots in obj['immutableReferences'].items():
  name=compile_result['immutable_names'][identifier];value=bytes.fromhex(values[name][2:]).rjust(32,b'\0')
  for spot in spots:
   start=spot['start'];length=spot['length'];assert length==32 and new_runtime[start:start+length]==bytes(32)
   assert start not in seen;seen[start]=name;new_runtime[start:start+length]=value;fills.append({'ast_id':identifier,'name':name,'start':start,'length':length,'value':values[name]})
 changed=copy.deepcopy(alloc);changed[manager]['code']='0x'+new_runtime.hex()
 assert {key for key in changed if changed[key]!=alloc[key]}=={manager}
 assert {key for key in changed[manager]if changed[manager][key]!=alloc[manager].get(key)}=={'code'}
 evidence.update(immutable_fills=fills,new_runtime_sha256=sha(new_runtime),new_runtime_keccak256='0x'+helper.keccak256(bytes(new_runtime)).hex(),
  new_runtime_size=len(new_runtime),only_allocation_change=[manager+'.code'],all_storage_and_other_code_byte_identical=True)
 candidate=copy.deepcopy(case);candidate['runtime_hashes']['liquidity']=evidence['new_runtime_keccak256'];candidate['materialized'][manager]={'hash':evidence['new_runtime_keccak256'],'length':len(new_runtime)}
 with node('new-runtime',changed)as(rpc,anchor,read,stateproof):
  assert read_immutables(read)==values;crosscheck(read,values)
  assert helper.code_bytes(rpc.call('eth_getCode',[manager,anchor]))==bytes(new_runtime)
  tx={'from':case['sender'],'to':case['destination'],'value':hex(case['value']),'data':case['data'],'gas':hex(helper.CAP)}
  call=rpc.attempt('eth_call',[tx,anchor]);estimate=rpc.attempt('eth_estimateGas',[tx,anchor]);trace=helper.checked_trace(rpc,tx,anchor,omitted)
  gas=helper.quantity(estimate['result'])if estimate['ok']else None;padded=(gas*120+99)//100 if gas is not None else None
  exact=rpc.attempt('eth_call',[{**tx,'gas':hex(padded)},anchor])if call['ok']and padded is not None and padded<=helper.CAP else None
  evidence.update(actual20m_call=call,estimate20m=estimate,estimated_gas=gas,padded_gas=padded,exact_padded_call=exact,
   original_estimated_gas=original['estimated_gas'],estimated_saving=original['estimated_gas']-gas if gas is not None else None)
  if call['ok']:assert call['result']=='0x'
  if trace['ok']and not trace['result'].get('error'):
   evidence['financial_trace']=helper.measure_trace(trace['result'],tx,candidate,read)
   evidence['royalty_trace']=helper.royalty_trace(trace['result'],candidate,original['workload']['royalty_ledger'],original['workload']['royalty_assets'],original['workload']['verified_rounds2_workload'])
   evidence['trace_gas_used']=helper.quantity(trace['result']['gasUsed']);evidence['functional_checks_pass']=True
  else:evidence['functional_checks_pass']=False;evidence['trace_error']=trace
  evidence['engineering_candidate_within20m_and_full20pct']=bool(call['ok']and gas is not None and padded<=helper.CAP and exact and exact['ok']and evidence['functional_checks_pass'])
 evidence['both_owned_nodes_stopped']=all(json.loads((D/name/'NODE.json').read_text())['owned_node_stopped']for name in('old-getters','new-runtime'))
 (D/'PROBE_RESULT.json').write_text(json.dumps(evidence,indent=2)+'\n')
 print(json.dumps({key:evidence.get(key)for key in ['scope','estimated_gas','padded_gas','estimated_saving','trace_gas_used','functional_checks_pass','engineering_candidate_within20m_and_full20pct','both_owned_nodes_stopped','profile_qualification','production_approved']}),flush=True)
 return 0 if evidence.get('functional_checks_pass')and evidence['both_owned_nodes_stopped']else 1
if __name__=='__main__':raise SystemExit(main())
