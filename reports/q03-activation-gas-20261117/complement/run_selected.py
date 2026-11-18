"""Bounded experimental-only allocator tests; no production source mutation."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True,type=Path);p.add_argument('--stage',required=True)
    p.add_argument('--method',default='^testQ03');p.add_argument('--expected',type=int,default=4)
    a=p.parse_args();stage=a.evidence/a.stage;stage.mkdir(parents=True,exist_ok=False)
    v=a.evidence.parents[1];forge=v/'foundry-v1.4.4/forge.exe';solc=v/'toolchain-0.8.26/solc.exe'
    names=sorted([x.relative_to(ROOT).as_posix()for x in(ROOT/'src').rglob('*.sol')]+
        ['test/Q03ComplementAllocation20261117.t.sol','test/fixtures/Q03ComplementAllocation.sol','foundry.toml'])
    before={n:sha(ROOT/n)for n in names}
    cmd=[str(forge),'test','--offline','--root',str(ROOT),'--use',str(solc),
        '--match-path','test/Q03ComplementAllocation20261117.t.sol',
        '--match-contract','Q03ComplementAllocation20261117Test','--match-test',a.method,
        '--skip','Q03ActivationCapacity20261117.t.sol',
        '--code-size-limit','1000000','--out',str(a.evidence/'out'),'--cache-path',str(a.evidence/'cache'),'--json','-vv']
    allow={'SYSTEMROOT','WINDIR','PATH','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','COMSPEC'}
    env={k:v for k,v in os.environ.items()if k.upper()in allow};env['FOUNDRY_PROFILE']='default'
    start={'command':cmd,'source_sha256':before,'forge_sha256':sha(forge),'solc_sha256':sha(solc),
        'scope':'new experimental library and four new methods; no production edit or gate qualification'}
    (stage/'START.json').write_text(json.dumps(start,indent=2)+'\n')
    for n in names:
        if n.startswith('test/'):
            dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/n).read_bytes())
    then=time.monotonic()
    with(stage/'forge.json').open('wb')as output,(stage/'stderr.log').open('wb')as error:
        r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=output,stderr=error,check=False)
    suites={}
    for line in(stage/'forge.json').read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('{"test/'):suites=json.loads(line)
    methods=[{'id':suite+'.'+method,'status':case['status'],'reason':case.get('reason'),'logs':case.get('decoded_logs',[])}
        for suite,data in suites.items()for method,case in data.get('test_results',{}).items()]
    after={n:sha(ROOT/n)for n in names}
    result={'returncode':r.returncode,'elapsed_seconds':time.monotonic()-then,'methods':methods,
        'actual_methods':len(methods),'nonzero_exact_selection':len(methods)==a.expected>0,
        'source_unchanged':before==after,'source_after_sha256':after,'raw_sha256':sha(stage/'forge.json')}
    result['pass']=r.returncode==0 and len(methods)==a.expected>0 and all(m['status']=='Success'for m in methods)and before==after
    (stage/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='source_after_sha256'}))
    return 0 if result['pass']else 1
if __name__=='__main__':raise SystemExit(main())
