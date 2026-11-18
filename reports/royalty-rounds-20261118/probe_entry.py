"""Virtual Entry/admission split size probe. No source adoption or approval."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
TARGETS={'src/ZZZActivationAssets.sol':('ZZZActivationAssets',64),
    'src/ZZZActivationEntry.sol':('ZZZActivationEntry',96),
    'src/ZZZActivationAssetsFactory.sol':('ZZZActivationAssetsFactory',0),
    'src/ZZZAccessController.sol':('ZZZAccessController',96)}
def main():
    solc,template,candidates,royalty,dst=(Path(x).resolve()for x in sys.argv[1:]);dst.mkdir(parents=True,exist_ok=False)
    assert sha(solc.read_bytes())=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
    data=json.loads(template.read_bytes());before={n:sha((ROOT/n).read_bytes())for n in data['sources']}
    overrides={n:(candidates/Path(n).name).read_bytes().decode()for n in ('src/ZZZActivationAssets.sol','src/ZZZActivationEntry.sol')}
    overrides['src/ZZZRoyaltyRewards.sol']=royalty.read_bytes().decode()
    actual_overlays={'src/ZZZLiquidityManager.sol','src/ZZZContributionPricing.sol'}
    for n,row in data['sources'].items():
        actual=(ROOT/n).read_bytes().decode()
        if n not in overrides and n not in actual_overlays:assert actual==row['content'],n
        row['content']=overrides.get(n,actual)
    data['settings']['outputSelection']={n:{name:['abi','evm.bytecode.object','evm.deployedBytecode.object','evm.deployedBytecode.immutableReferences']}for n,(name,args)in TARGETS.items()}
    payload=json.dumps(data,separators=(',',':')).encode();(dst/'compiler-input.json').write_bytes(payload)
    write=lambda p,obj:p.write_text(json.dumps(obj,indent=2)+'\n')
    write(dst/'START.json',{'scope':'virtual four-object size probe, not48normal gates','source_before':before,'input_sha256':sha(payload),'proposed_overrides':{n:sha(s.encode())for n,s in overrides.items()},'royalty_variant':str(royalty),'no_source_adoption':True})
    env={k:v for k,v in os.environ.items()if k.upper()in{'SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA'}}
    env['PATH']=str(solc.parent)+os.pathsep+'C:/Windows/System32';start=time.monotonic()
    with(dst/'compiler-input.json').open('rb')as inp,(dst/'compiler-output.json').open('xb')as out,(dst/'stderr.log').open('xb')as err:
        done=subprocess.run([str(solc),'--standard-json'],stdin=inp,stdout=out,stderr=err,cwd=dst,env=env,check=False)
    compiled=json.loads((dst/'compiler-output.json').read_bytes());errors=[x for x in compiled.get('errors',[])if x['severity']=='error'];objects=[]
    if not errors:
        for n,(name,args)in TARGETS.items():
            obj=compiled['contracts'][n][name]['evm'];runtime=len(obj['deployedBytecode']['object'])//2;creation=len(obj['bytecode']['object'])//2
            objects.append({'source':n,'name':name,'runtime':runtime,'creation':creation,'constructor_bytes':args,'runtime_margin':24576-runtime,'initcode_margin':49152-creation-args,'size_pass':runtime<=24576 and creation+args<=49152})
    result={'scope':'virtual four-object size probe only','exit_code':done.returncode,'seconds':time.monotonic()-start,'errors':errors,'objects':objects,'all_selected_size_gates_pass':bool(len(objects)==4 and all(o['size_pass']for o in objects)),'source_unchanged':before=={n:sha((ROOT/n).read_bytes())for n in before},'output_sha256':sha((dst/'compiler-output.json').read_bytes()),'production_adopted':False}
    write(dst/'RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
