"""Run one NEW actual-v4 Oracle/feed boundary regression; no RPC or signer."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
FORGE=V/'foundry-v1.4.4/forge.exe';SOLC=V/'toolchain-0.8.26/solc.exe'
SOURCE='test/ActivationExecutionBoundary20261118.t.sol';CONTRACT='ActivationExecutionBoundary20261118Test'
PROTECTED={
 'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
    return {p.relative_to(R).as_posix():sha(p) for directory in ('src','test','lib','node_modules')
        for p in sorted((R/directory).rglob('*.sol')) if p.is_file()}
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def main():
    stage=sys.argv[1]
    if not re.fullmatch(r'boundary\d{2}',stage):raise ValueError('Fresh owned stage required')
    dst=V/'activation-gas-20261118'/stage;dst.mkdir(exist_ok=False)
    before=inventory();config=sha(R/'foundry.toml');producer=sha(Path(__file__))
    available=re.findall(r'function (testExecutionBoundary\w+)\(', (R/SOURCE).read_bytes().decode());assert len(available)==1
    expected=sys.argv[2].split(',') if len(sys.argv)>2 else available
    assert expected and len(set(expected))==len(expected) and set(expected)<=set(available)
    assert sha(SOLC)=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
    assert all(sha(R/p)==h for p,h in PROTECTED.items())
    command=[str(FORGE),'test','--offline','--root',str(R),'--use',str(SOLC),
        '--out',str(dst/'out'),'--cache-path',str(dst/'cache'),'--code-size-limit','1000000',
        '--match-path',SOURCE,'--match-contract','^'+CONTRACT+'$','--match-test','('+'|'.join(expected)+')','--json']
    command += [arg for p in sorted((R/'test').rglob('*.t.sol')) if p.relative_to(R).as_posix()!=SOURCE
        for arg in ('--skip',p.name)]
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA'}}
    env['PATH']=str(SOLC.parent)+';C:/Windows/System32'
    write(dst/'START.json',{'stage':stage,'command':command,'expected_methods':expected,'source_before':before,
        'config_before':config,'producer_before':producer,'forge_sha256':sha(FORGE),'solc_sha256':sha(SOLC),
        'scope':'NEW actual-v4 proof-boundary tests; test-host size limit only, no production-gate change'})
    start=time.monotonic()
    with(dst/'raw.json').open('wb')as out,(dst/'stderr.log').open('wb')as err:
        done=subprocess.run(command,cwd=R,env=env,stdout=out,stderr=err,timeout=900)
    after=inventory();rows=[];parse_error=None;deps={};metadata_error=None
    try:
        raw=json.loads((dst/'raw.json').read_bytes());suite=raw[SOURCE+':'+CONTRACT]
        assert set(raw)=={SOURCE+':'+CONTRACT}
        for sig,t in suite['test_results'].items():rows.append({'signature':sig,'status':t['status'],'reason':t.get('reason'),'decoded_logs':t.get('decoded_logs',[])})
    except Exception as exc:parse_error=repr(exc)
    artifact=dst/'out'/Path(SOURCE).name/(CONTRACT+'.json')
    try:
        a=json.loads(artifact.read_bytes());m=a.get('metadata');m=m if isinstance(m,dict)else json.loads(a['rawMetadata'])
        for n,record in m['sources'].items():
            n=Path(n).as_posix();b=(R/n).read_bytes();wanted=record['keccak256'].lower()
            binding='raw' if '0x'+keccak256(b).hex()==wanted else 'CRLF_to_LF_only' if '0x'+keccak256(b.replace(b'\r\n',b'\n')).hex()==wanted else None
            deps[n]={'before':before[n],'after':after.get(n),'stable':before[n]==after.get(n),'compiled_keccak256':wanted,'binding':binding}
    except Exception as exc:metadata_error=repr(exc)
    pass_=done.returncode==0 and len(rows)==len(expected) and {x['signature'].split('(')[0]for x in rows}==set(expected) and all(x['status']=='Success'for x in rows)
    pass_=bool(pass_ and deps and not metadata_error and all(x['stable']and x['binding']for x in deps.values()) and config==sha(R/'foundry.toml') and all(sha(R/p)==h for p,h in PROTECTED.items()))
    result={'pass':pass_,'stage':stage,'seconds':time.monotonic()-start,'exit_code':done.returncode,'methods':rows,
        'parse_error':parse_error,'metadata_error':metadata_error,'dependency_source_bracket':deps,
        'config_unchanged':config==sha(R/'foundry.toml'),'protected_unchanged':all(sha(R/p)==h for p,h in PROTECTED.items()),
        'all_production_source_stable':all(before[n]==after.get(n)for n in before if n.startswith('src/')),
        'producer_unchanged':producer==sha(Path(__file__)),'raw_sha256':sha(dst/'raw.json'),'stderr_sha256':sha(dst/'stderr.log'),
        'artifact_sha256':sha(artifact)if artifact.exists()else None,'new_method_count':len(rows),'old_methods_run':0,'gas_qualification':False}
    write(dst/'RESULT.json',result);print(json.dumps({k:result[k]for k in ('pass','stage','seconds','exit_code','methods','parse_error','metadata_error')},indent=2))
    return 0 if pass_ else 1
if __name__=='__main__':raise SystemExit(main())
