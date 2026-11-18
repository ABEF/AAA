"""ONE new synced-prefund import regression, including baseline failure proof."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
SOURCE='test/RoyaltySyncedPrefundImport20261118.t.sol';NAME='RoyaltySyncedPrefundImport20261118Test'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dst=V/'royalty-rounds-20261118/synced-prefund'/sys.argv[1];dst.mkdir(parents=True,exist_ok=False)
    before={p.relative_to(R).as_posix():sha(p)for d in ('src','test','lib','node_modules')for p in(R/d).rglob('*.sol')if p.is_file()}
    cfg=sha(R/'foundry.toml');forge=V/'foundry-v1.4.4/forge.exe';solc=V/'toolchain-0.8.26/solc.exe'
    command=[str(forge),'test','--offline','--root',str(R),'--use',str(solc),'--out',str(dst/'out'),'--cache-path',str(dst/'cache'),
      '--code-size-limit','1000000','--match-path',SOURCE,'--match-contract','^'+NAME+'$','--match-test','testSyncedTargetPrefunds','--json']
    command += [x for p in(R/'test').rglob('*.t.sol')if p.relative_to(R).as_posix()!=SOURCE for x in ('--skip',p.name)]
    env={k:v for k,v in os.environ.items()if k.upper()in {'SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PATH'}}
    save=lambda name,value:(dst/name).write_text(json.dumps(value,indent=2)+'\n')
    save('START.json',{'command':command,'source_before':before,'foundry_before':cfg,'solc_sha256':sha(solc),'forge_sha256':sha(forge),'expected_methods':1,'expected_baseline_failure':sys.argv[1].startswith('baseline'),'old_methods_run':0})
    t=time.monotonic()
    with(dst/'raw.json').open('wb')as out,(dst/'stderr.log').open('wb')as err:done=subprocess.run(command,cwd=R,env=env,stdout=out,stderr=err,timeout=900)
    rows=[];error=None;deps={};artifact=dst/'out'/Path(SOURCE).name/(NAME+'.json')
    try:
        raw=json.loads((dst/'raw.json').read_bytes());assert set(raw)=={SOURCE+':'+NAME}
        rows=[{'signature':sig,'status':item['status'],'reason':item.get('reason'),'logs':item.get('decoded_logs',[])}for sig,item in raw[SOURCE+':'+NAME]['test_results'].items()]
        a=json.loads(artifact.read_bytes());m=a.get('metadata');m=m if isinstance(m,dict)else json.loads(a['rawMetadata'])
        for n,record in m['sources'].items():
            n=Path(n).as_posix();b=(R/n).read_bytes();wanted=record['keccak256'].lower();binding='raw'if'0x'+keccak256(b).hex()==wanted else'CRLF_to_LF_only'if'0x'+keccak256(b.replace(b'\r\n',b'\n')).hex()==wanted else None
            deps[n]={'before':before[n],'after':sha(R/n),'stable':before[n]==sha(R/n),'compiled_keccak256':wanted,'binding':binding}
    except Exception as exc:error=repr(exc)
    result={'seconds':time.monotonic()-t,'exit_code':done.returncode,'methods':rows,'error':error,'compiled_source_bracket':deps,
      'source_scope_valid':bool(deps)and all(x['stable']and x['binding']for x in deps.values()),'config_unchanged':cfg==sha(R/'foundry.toml'),
      'raw_sha256':sha(dst/'raw.json'),'artifact_sha256':sha(artifact)if artifact.exists()else None,'old_methods_run':0,'new_distinct_method_count':len(rows)}
    result['pass']=done.returncode==0 and len(rows)==1 and rows[0]['status']=='Success'and result['source_scope_valid']and result['config_unchanged']
    save('RESULT.json',result);print(json.dumps({k:result[k]for k in ('seconds','exit_code','methods','error','source_scope_valid','config_unchanged','pass')},indent=2))
    return 0 if result['pass']else 1
if __name__=='__main__':raise SystemExit(main())
