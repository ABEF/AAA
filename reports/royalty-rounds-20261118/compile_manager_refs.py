"""Supplement one accepted engineering object with AST/immutable references.
No test, node, source/config mutation, signing or deployment.
"""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
S=V/'royalty-rounds-20261118/manager/probe02';D=V/'royalty-rounds-20261118/manager/engineering01'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def main():
 D.mkdir(parents=True,exist_ok=False)
 original=(S/'compiler-input.json').read_bytes();given=json.loads(original);prior=json.loads((S/'compiler-output.json').read_bytes())
 assert len(given['sources'])==100
 assert sha(given['sources']['src/ZZZLiquidityManager.sol']['content'].encode())=='43aa1d36777f3ab0b9c13c0fde91f47ffca2f38ec94a19df980606c04c015330'
 given['settings']['outputSelection']={'*':{'':['ast']},'src/ZZZLiquidityManager.sol':{'ZZZLiquidityManager':['evm.bytecode.object','evm.deployedBytecode.object','evm.deployedBytecode.immutableReferences']}}
 raw=json.dumps(given,separators=(',',':')).encode();(D/'compiler-input.json').write_bytes(raw)
 solc=V/'toolchain-0.8.26/solc.exe';assert sha(solc.read_bytes())=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
 cmd=[str(solc),'--standard-json'];start={'command':cmd,'input_sha256':sha(raw),'original_probe_input_sha256':sha(original),
  'original_probe_output_sha256':sha((S/'compiler-output.json').read_bytes()),'compiler_sha256':sha(solc.read_bytes()),
  'source_sha256':{name:sha(row['content'].encode())for name,row in given['sources'].items()},
  'only_compiler_output_selection_changed':True,'scope':'UNQUALIFIED one-object engineering metadata supplement; not new full normal build or profile qualification'}
 (D/'START.json').write_text(json.dumps(start,indent=2)+'\n');env={key:os.environ[key]for key in('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')if key in os.environ}
 then=time.monotonic()
 with(D/'compiler-input.json').open('rb')as inp,(D/'compiler-output.json').open('xb')as out,(D/'stderr.log').open('xb')as err:
  proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,env=env);(D/'PID.json').write_text(json.dumps({'pid':proc.pid})+'\n');code=proc.wait(timeout=600)
 current=json.loads((D/'compiler-output.json').read_bytes());errors=[row for row in current.get('errors',[])if row['severity']=='error']
 name='ZZZLiquidityManager';path='src/ZZZLiquidityManager.sol'
 result={'exit_code':code,'elapsed_seconds':time.monotonic()-then,'errors':errors,'compiled_source_count':len(current.get('sources',{})),
  'production_approved':False,'full_normal_build':False,'public_deployment':False,'new_tests_executed':0}
 if not errors:
  obj=current['contracts'][path][name]['evm']['deployedBytecode'];old=prior['contracts'][path][name]['evm']['deployedBytecode']
  result.update(runtime_object_byte_identical=obj['object']==old['object'],runtime_size=len(bytes.fromhex(obj['object'])),immutable_references=obj['immutableReferences'],output_sha256=sha((D/'compiler-output.json').read_bytes()))
  ids={}
  def scan(node):
   if isinstance(node,dict):
    if node.get('nodeType')=='VariableDeclaration'and node.get('mutability')=='immutable':ids[str(node['id'])]=node['name']
    for value in node.values():scan(value)
   elif isinstance(node,list):
    for value in node:scan(value)
  for row in current['sources'].values():scan(row.get('ast'))
  result['immutable_names']={key:ids[key]for key in obj['immutableReferences']}
  assert set(result['immutable_names'].values())=={'access','balancingRouter','positionExecutor','posm','stateView','poolManager','permit2'}
  assert result['runtime_object_byte_identical']
 (D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 return 0 if code==0 and not errors and result.get('runtime_object_byte_identical')else 1
if __name__=='__main__':raise SystemExit(main())
