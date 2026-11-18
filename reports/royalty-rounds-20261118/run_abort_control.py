"""Run one directly affected funded-abort control on final C08 source."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,time

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
FORGE=V/'foundry-v1.4.4/forge.exe';SOLC=V/'toolchain-0.8.26/solc.exe'
SOURCE='test/RoyaltyRoundsIntegration20261118.t.sol';CONTRACT='RoyaltyRoundsIntegration20261118Test'
AFFECTED='test/Q03RoyaltyIntegration20261117.t.sol';AFFECTED_CONTRACT='Q03RoyaltyIntegration20261117Test'
FUNDING='test/RoyaltyActivationFunding20261118.t.sol';FUNDING_CONTRACT='RoyaltyActivationFunding20261118Test'
PROTECTED={
 'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory():
    return {p.relative_to(R).as_posix():sha(p) for directory in ('src','test','lib','node_modules')
        for p in sorted((R/directory).rglob('*.sol')) if p.is_file()}
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def main():
    stage=sys.argv[1]
    if re.fullmatch(r'abort-final\d{2}',stage) is None:raise ValueError('New owned stage required')
    E=V/'royalty-rounds-20261118'/stage;E.mkdir()
    warm=None
    before=inventory();config_before=sha(R/'foundry.toml');producer_before=sha(Path(__file__))
    for f,h in PROTECTED.items():assert sha(R/f)==h
    expected={AFFECTED+':'+AFFECTED_CONTRACT:['testQ03FundedAbortRestoresSourceComplementaryCreditsAndFutureClaims']}
    command=[str(FORGE),'test','--offline','--use',str(SOLC),'--root',str(R),
        '--out',str(E/'out'),'--cache-path',str(E/'cache'),
        '--match-path',AFFECTED,
        '--match-contract',AFFECTED_CONTRACT,
        '--match-test','^testQ03FundedAbortRestoresSourceComplementaryCreditsAndFutureClaims','--json']
    command += [x for path in sorted((R/'test').rglob('*.t.sol'))
        if path.relative_to(R).as_posix() != AFFECTED for x in ('--skip',path.name)]
    env={k:v for k,v in os.environ.items() if not k.upper().startswith(
        ('POPL_','FOUNDRY_','DAPP_','CAST_','ANVIL_','ETH_'))}
    write(E/'START.json',dict(stage=stage,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
        production_diff_against_head=subprocess.check_output(['git','diff','--name-only','HEAD','--','src'],cwd=R,text=True).splitlines(),
        stage_notice='Exactly one funded-abort control affected by the C08 import category construction; no unchanged suite is selected.',
        command=command,forge_sha256=sha(FORGE),solc_sha256=sha(SOLC),foundry_toml_sha256=config_before,
        producer_sha256=producer_before,
        owned_warm_cache_copied_from=str(warm) if warm else None,
        expected_methods=expected,source_sha256=before,network_or_signing=False,shared_config_mutation=False))
    started=time.monotonic();exit_code=None;timeout=False
    try:
        with (E/'raw.json').open('wb') as out,(E/'stderr.log').open('wb') as err:
            exit_code=subprocess.run(command,cwd=R,env=env,stdout=out,stderr=err,timeout=900).returncode
    except subprocess.TimeoutExpired:timeout=True
    after=inventory();config_after=sha(R/'foundry.toml');rows=[];parse_error=None
    try:
        raw=json.loads((E/'raw.json').read_text(encoding='utf-8'));suites={name:raw[name]for name in expected}
        assert set(raw)==set(expected)
        for name,suite in suites.items():
            for signature,item in suite['test_results'].items():
                rows.append(dict(suite=name,signature=signature,status=item['status'],reason=item.get('reason'),
                    gas=item.get('kind',{}),decoded_logs=item.get('decoded_logs',[])))
    except Exception as exc:parse_error=type(exc).__name__
    artifacts={name:E/'out'/name.split(':')[0].split('/')[-1]/(name.split(':')[1]+'.json')for name in expected}
    deps={};metadata_error=None
    try:
        for identity,artifact in artifacts.items():
            obj=json.loads(artifact.read_text(encoding='utf-8'));metadata=obj.get('metadata')
            if not isinstance(metadata,dict):metadata=json.loads(obj['rawMetadata'])
            for f,record in metadata['sources'].items():
                name=Path(f).as_posix()
                if name not in before:raise ValueError('Dependency outside source-before inventory')
                compiled_hash=record['keccak256'].lower();source_bytes=(R/name).read_bytes()
                current_hash='0x'+keccak256(source_bytes).hex()
                lf_hash='0x'+keccak256(source_bytes.replace(b'\r\n',b'\n')).hex()
                binding='raw' if compiled_hash==current_hash else 'CRLF_to_LF_only' if compiled_hash==lf_hash else None
                record=dict(before=before[name],after=after.get(name),stable=before[name]==after.get(name),
                    compiled_keccak256=compiled_hash,current_keccak256=current_hash,
                    lf_keccak256=lf_hash,compiler_source_binding=binding,artifact_binds_current_source=binding is not None)
                assert name not in deps or deps[name]==record
                deps[name]=record
    except Exception as exc:metadata_error=type(exc).__name__
    protected_ok=all(sha(R/f)==h for f,h in PROTECTED.items())
    selected={(row['suite'],row['signature'].split('(')[0])for row in rows}
    expected_ids={(name,m)for name,methods in expected.items()for m in methods}
    success=bool(exit_code==0 and not timeout and len(rows)==1 and selected==expected_ids
        and all(row['status']=='Success' for row in rows) and deps and not metadata_error
        and all(item['stable'] and item['artifact_binds_current_source'] for item in deps.values())
        and config_before==config_after and protected_ok
        and producer_before==sha(Path(__file__)))
    summary=dict(stage=stage,success=success,exit_code=exit_code,timeout=timeout,seconds=time.monotonic()-started,
        expected_methods=expected,actual_count=len(rows),methods=rows,parse_error=parse_error,
        artifact_sha256={k:sha(v)if v.exists()else None for k,v in artifacts.items()},metadata_error=metadata_error,
        producer_sha256_before=producer_before,producer_sha256_after=sha(Path(__file__)),
        forge_suite_duration=suite.get('duration') if parse_error is None else None,
        dependency_count=len(deps),dependency_source_bracket=deps,foundry_toml_unchanged=config_before==config_after,
        protected_four_unchanged=protected_ok,
        source_changes_outside_dependency_closure=[f for f in before.keys()|after.keys()
            if before.get(f)!=after.get(f) and f not in deps],
        production_source_bracket={f:dict(before=h,after=after.get(f),stable=h==after.get(f))
            for f,h in before.items() if f.startswith('src/')},
        raw_sha256=sha(E/'raw.json'),stderr_sha256=sha(E/'stderr.log'),
        scope='Actual royalty ledger/allocator canonical component with typed InKindNFT/MockAccess. No Entry/LP/provider or deployment qualification.',
        unchanged_test_methods_executed=0,affected_prior_methods_executed=1,new_methods_executed=0)
    write(E/'RESULT.json',summary)
    print(json.dumps({k:summary[k] for k in ('stage','success','exit_code','actual_count','seconds','parse_error','metadata_error')},indent=2))
    return 0 if success else 1

if __name__=='__main__':raise SystemExit(main())
