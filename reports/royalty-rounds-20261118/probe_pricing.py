"""Current-graph Oracle size probe; not a full normal-build qualification."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    solc,template,dst=(Path(x).resolve() for x in sys.argv[1:]);dst.mkdir(parents=True,exist_ok=False)
    assert sha(solc.read_bytes())=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
    data=json.loads(template.read_bytes());before={n:sha((ROOT/n).read_bytes()) for n in data['sources']}
    allowed={'src/ZZZLiquidityManager.sol','src/ZZZContributionPricing.sol'}
    for n,row in data['sources'].items():
        actual=(ROOT/n).read_bytes().decode()
        if n not in allowed: assert row['content']==actual,n
        row['content']=actual
    data['settings']['outputSelection']={'src/ZZZOracle.sol':{'ZZZOracle':['evm.bytecode.object','evm.deployedBytecode.object']}}
    payload=json.dumps(data,separators=(',',':')).encode();(dst/'compiler-input.json').write_bytes(payload)
    (dst/'START.json').write_text(json.dumps({'scope':'one-object Oracle size probe, not48normal gates','source_before':before,'input_sha256':sha(payload)},indent=2)+'\n')
    env={k:v for k,v in os.environ.items()if k.upper()in{'SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA'}}
    env['PATH']=str(solc.parent)+os.pathsep+'C:/Windows/System32';start=time.monotonic()
    with(dst/'compiler-input.json').open('rb')as inp,(dst/'compiler-output.json').open('xb')as out,(dst/'stderr.log').open('xb')as err:
        done=subprocess.run([str(solc),'--standard-json'],stdin=inp,stdout=out,stderr=err,cwd=dst,env=env,check=False)
    compiled=json.loads((dst/'compiler-output.json').read_bytes());errors=[x for x in compiled.get('errors',[])if x['severity']=='error']
    result={'scope':'one-object size probe only','exit_code':done.returncode,'seconds':time.monotonic()-start,'errors':errors,
        'source_unchanged':before=={n:sha((ROOT/n).read_bytes())for n in before},'output_sha256':sha((dst/'compiler-output.json').read_bytes())}
    if not errors:
        obj=compiled['contracts']['src/ZZZOracle.sol']['ZZZOracle']['evm'];runtime=len(obj['deployedBytecode']['object'])//2;creation=len(obj['bytecode']['object'])//2
        result.update(runtime=runtime,creation=creation,constructor_bytes=creation+64,runtime_margin=24576-runtime,initcode_margin=49152-creation-64)
    (dst/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
