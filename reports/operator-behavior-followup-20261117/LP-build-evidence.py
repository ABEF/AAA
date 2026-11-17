"""Freeze evidence from the finite new LP/key-recovery checks, offline only."""
import hashlib,json,re,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256

V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
REPORT=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()

stages=[
    ('actual-core-signature-filter.log','operator-behavior-followup-20261117-lp-out1',
     'test/OptionalPortfolioCore.t.sol','OptionalPortfolioCoreTest',[
         'testKeeperSoftwareBoundaryActualCompoundAndRevokeRotatePauseRecovery']),
    ('actual-access-role.log','operator-behavior-followup-20261117-role-out1',
     'test/AccessController.t.sol','AccessControllerTest',[
         'testKeeperRecoveryGovernanceRevokesAndReplacesWhilePausedWithoutRestoringOldGrant',
         'testSealErasesBootstrap']),
]
result={'schema':1,'starting_commit':'6945eeeba24304b8ddf27ac4c08fe55dc553554e',
    'scope':'Two new methods plus one affected seal-fixture method; no unchanged suite, external RPC or chain run.',
    'accepted_policy':'In-range/below-threshold compound wait remains keeper-software-only by explicit user decision.',
    'production_LP_changes':False,'production_Access_changed_by_separate_artwork_fix':True,
    'new_methods':2,'affected_existing_methods':1,'stages':[],
    'zero_test_attempts':[],'test_files_sha256':{},'limitations':[
        'Actual-core case uses mock Access/admission/Permit2/VRF and correlated controlled prices.',
        'Actual AccessController authorization is checked separately with unused economic roles as BoundDummy.',
        'Combined source scopes are not a full live-controller/market/provider/wallet rehearsal.',
        'Test-method gas includes many operations and is not an operation deployment/target-chain gas quote.',
        'Revocation/pause protect later inclusion; they cannot undo a valid transaction included first.',
        'Existing Anvil, databases, services, signing, pending journals and public deployment remain untouched.',
    ]}
for name,out,source,contract,methods in stages:
    log_path=REPORT/'LP-checks-attempt1'/name;raw=log_path.read_bytes();log=raw.decode('utf-8-sig')
    passed=re.findall(r'\[PASS\] ([A-Za-z0-9_]+)\(\)',log)
    if sorted(passed)!=sorted(methods) or '[FAIL' in log or '0 failed; 0 skipped' not in log:
        raise SystemExit('Expected finite successful method list differs: '+name)
    artifact_path=V/out/Path(source).name/(contract+'.json')
    artifact_raw=artifact_path.read_bytes();artifact=json.loads(artifact_raw);metadata=artifact['metadata']
    settings=metadata['settings']
    # Solc metadata emits explicit optimizer components and can omit 'enabled'.
    # Require the actual EVM optimizer flags, not an absent summary alias.
    details=settings['optimizer']['details']
    if (metadata['compiler']['version']!='0.8.26+commit.8a97fa7a' or settings['evmVersion']!='cancun' or
        settings['optimizer']['runs']!=1 or any(details.get(key) is not True for key in
            ('peephole','inliner','jumpdestRemover','orderLiterals','deduplicate','cse','constantOptimizer')) or
        settings.get('viaIR') is not True or settings['optimizer']['details'].get('yul') is not False):
        raise SystemExit('Compiler profile differs: '+name)
    sources={};normalized=[]
    for rel,record in metadata['sources'].items():
        actual=(ROOT/rel).read_bytes()
        if '0x'+keccak256(actual).hex()!=record['keccak256']:
            # Foundry supplies LF-normalized source text to Solc. Accept ONLY
            # that exact transport normalization and retain both identities.
            lf=actual.replace(b'\r\n',b'\n')
            if lf==actual or '0x'+keccak256(lf).hex()!=record['keccak256']:
                raise SystemExit('Compiled/current source differs: '+rel)
            normalized.append(rel)
        sources[rel]=sha(actual)
    result['stages'].append({'log':str(log_path.relative_to(ROOT)).replace('\\','/'),
        'log_sha256':sha(raw),'methods_passed':passed,'compiled_artifact':str(artifact_path),
        'artifact_sha256':sha(artifact_raw),'compiler':metadata['compiler'],'settings':settings,
        'compiled_sources_sha256':sources,'compiler_CRLF_to_LF_sources':normalized,
        'compiler_source_keccak256':{k:v['keccak256'] for k,v in metadata['sources'].items()}})
for name in ('actual-core.log','actual-core-explicit-root.log','actual-core-glob.log'):
    p=REPORT/'LP-checks-attempt1'/name;raw=p.read_bytes()
    if 'No tests found in project' not in raw.decode('utf-8-sig'):raise SystemExit('Unclassified initial attempt')
    result['zero_test_attempts'].append({'log':str(p.relative_to(ROOT)).replace('\\','/'),
        'sha256':sha(raw),'tests_executed':0,'qualification':False})
for rel in ('test/OptionalPortfolioCore.t.sol','test/AccessController.t.sol','test/mocks/Mocks.sol'):
    result['test_files_sha256'][rel]=sha((ROOT/rel).read_bytes())
with (REPORT/'LP-evidence.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'passed':3,'new':2,'affected_existing':1,'source_scopes':[len(s['compiled_sources_sha256']) for s in result['stages']]}))
