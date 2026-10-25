"""Separate transaction-context measurements after the preserved combined control."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('role_gas_template',HERE/'run-role-gas.py')
template=importlib.util.module_from_spec(spec);spec.loader.exec_module(template)
OUT=template.EXTERNAL/'day-readiness-20261025/role-gas-isolated'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    if OUT.exists():raise ValueError('Preserve earlier isolated gas outputs')
    (OUT/'test').mkdir(parents=True)
    before=json.loads(template.BASELINE.read_text());after=json.loads(template.CURRENT.read_text())
    source='src/ZZZAccessController.sol';name='ZZZAccessController'
    old=before['contracts'][source][name];new=after['contracts'][source][name]
    (OUT/'bytecodes.json').write_text(json.dumps({'baseline':'0x'+old['evm']['bytecode']['object'],
        'candidate':'0x'+new['evm']['bytecode']['object']}),encoding='utf-8')
    harness=template.HARNESS.replace('BYTECODE_FILE',(OUT/'bytecodes.json').as_posix())
    harness=harness.replace('event log_named_uint(string key,uint256 value);',
        'address private oldAccess; address private newAccess; uint256 private oldCreate; uint256 private newCreate;\n    event log_named_uint(string key,uint256 value);')
    harness=harness.replace('bool enabled,string memory name) private {','bool enabled,string memory name,address account) private {')
    harness=harness.replace('(ACCOUNT,enabled)','(account,enabled)').replace('GUARDIAN_EVENT,ACCOUNT,enabled','GUARDIAN_EVENT,account,enabled').replace('guardians(ACCOUNT)','guardians(account)')
    harness=harness.replace('function testControlledRoleGasAndObservableAuthority() public {','function setUp() public {')
    harness=harness.replace('(address oldAccess,uint256 oldCreate)=_create(oldCode);','(oldAccess,oldCreate)=_create(oldCode);')
    harness=harness.replace('(address newAccess,uint256 newCreate)=_create(newCode);','(newAccess,newCreate)=_create(newCode);')
    previous='''        emit log_named_uint("constructor CREATE baseline",oldCreate);
        emit log_named_uint("constructor CREATE candidate",newCreate);
        _role(oldAccess,newAccess,true,"guardian grant");
        _role(oldAccess,newAccess,true,"guardian idempotent grant");
        _role(oldAccess,newAccess,false,"guardian revoke");
        _authorities(oldAccess);_authorities(newAccess);'''
    if previous not in harness:raise ValueError('Harness template changed; review adaptation')
    harness=harness.replace(previous,'')
    methods='''
    function testConstructorGasAndInitialAuthority() public {
        emit log_named_uint("constructor CREATE baseline",oldCreate);
        emit log_named_uint("constructor CREATE candidate",newCreate);
        _authorities(oldAccess);_authorities(newAccess);
    }
    function testGuardianGrantGasFromCommittedZero() public {
        require(!IAccess(oldAccess).guardians(ACCOUNT) && !IAccess(newAccess).guardians(ACCOUNT),"Expected zero role");
        _role(oldAccess,newAccess,true,"guardian grant",ACCOUNT);
        _authorities(oldAccess);_authorities(newAccess);
    }
    function testGuardianIdempotentGasFromCommittedOne() public {
        _authorities(oldAccess);_authorities(newAccess);
        _role(oldAccess,newAccess,true,"guardian idempotent grant",GUARDIAN);
        _authorities(oldAccess);_authorities(newAccess);
    }
    function testGuardianRevokeGasFromCommittedOne() public {
        _authorities(oldAccess);_authorities(newAccess);
        _role(oldAccess,newAccess,false,"guardian revoke",GUARDIAN);
        require(IAccess(oldAccess).governance()==address(this) && IAccess(newAccess).governance()==address(this),"Governance unchanged");
        require(IAccess(oldAccess).keepers(KEEPER) && IAccess(newAccess).keepers(KEEPER),"Keeper unchanged");
    }
'''
    harness=harness.rsplit('}',1)[0]+methods+'}\n'
    (OUT/'test/RoleGas.t.sol').write_text(harness,encoding='utf-8')
    config=(template.OUT/'foundry.toml').read_text().replace((template.OUT/'bytecodes.json').as_posix(),(OUT/'bytecodes.json').as_posix())
    (OUT/'foundry.toml').write_text(config,encoding='utf-8')
    command=[str(template.FORGE),'test','--root',str(OUT),'--use',str(template.SOLC),
        '--match-contract','RoleGasTest','-vv','--json']
    start=time.monotonic();result=subprocess.run(command,cwd=OUT,capture_output=True,timeout=300)
    elapsed=round(time.monotonic()-start,3)
    (OUT/'forge.stdout.json').write_bytes(result.stdout);(OUT/'forge.stderr.log').write_bytes(result.stderr)
    output=json.loads(result.stdout)
    cases=[];measurements={}
    for suite in output.values():
        for method,row in suite['test_results'].items():
            cases.append({'method':method,'status':row['status'],'reason':row['reason'],'unit_gas':row['kind']})
            for line in row['decoded_logs']:
                label,value=line.rsplit(': ',1);measurements[label]=int(value)
    metrics=[]
    for operation in ('constructor CREATE','guardian grant','guardian idempotent grant','guardian revoke'):
        a,b=measurements.get(operation+' baseline'),measurements.get(operation+' candidate')
        metrics.append({'operation':operation,'baseline_raw_gas':a,'candidate_raw_gas':b,
            'difference':None if a is None or b is None else b-a})
    inputs=[template.EXTERNAL/'day-readiness-20261025/solidity/controlled-baseline-input.json',
            template.EXTERNAL/'deep-cleanup-20261025/solidity/source-build-input.json']
    saved_inputs=[json.loads(path.read_text()) for path in inputs]
    dependencies={name:value for name,value in saved_inputs[1]['sources'].items() if not name.startswith('src/')}
    same_dependencies=all(saved_inputs[0]['sources'].get(name)==value for name,value in dependencies.items())
    report={'scope':'Four isolated Forge tests; setUp deployments precede separate test transaction contexts, with cooled target storage/account state.',
        'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'command':command,'exit_code':result.returncode,
        'elapsed_seconds':elapsed,'cases':cases,'measurements':metrics,'raw_results':output,
        'runtime_bytes':{'baseline':len(bytes.fromhex(old['evm']['deployedBytecode']['object'])),
                         'candidate':len(bytes.fromhex(new['evm']['deployedBytecode']['object']))},
        'creation_bytes':{'baseline':len(bytes.fromhex(old['evm']['bytecode']['object'])),
                          'candidate':len(bytes.fromhex(new['evm']['bytecode']['object']))},
        'constructor_wire_labels':{'baseline':[x for x in old['abi'] if x['type']=='constructor'],
                                   'candidate':[x for x in new['abi'] if x['type']=='constructor']},
        'controlled_settings_equal':saved_inputs[0]['settings']==saved_inputs[1]['settings'],
        'controlled_dependency_contents_equal':same_dependencies,'dependency_count':len(dependencies),
        'compiler_sha256':sha(template.SOLC.read_bytes()),'forge_sha256':sha(template.FORGE.read_bytes()),
        'harness_driver_sha256':sha(Path(__file__).read_bytes()),
        'artifact_sha256':{str(path):sha(path.read_bytes()) for path in [template.BASELINE,template.CURRENT,*inputs,OUT/'bytecodes.json',OUT/'test/RoleGas.t.sol',OUT/'foundry.toml',OUT/'forge.stdout.json']},
        'limits':['CREATE/call gasleft deltas exclude transaction intrinsic/calldata/L1/network costs and applied refunds.',
            'Targets are cooled before identical payloads; assembly CALL has no return-data allocation and payload memory is allocated before measurement.',
            'Initial combined-control revoke had dirty-slot semantics, so its absolute gas is not a standalone transaction estimate and is not used here.',
            'EOA-style initial keeper/guardian addresses and the same bootstrap/governance test caller are used; sealed-governance branch gas and target-chain fees are not measured.',
            'No persistent Anvil, public deployment, account key, signing, RPC or service operation occurs.']}
    report['passed']=result.returncode==0 and len(cases)==4 and all(row['status']=='Success' for row in cases) and all(
        row['difference'] is not None and row['difference']>0 for row in metrics) and same_dependencies and report['controlled_settings_equal']
    (HERE/'role-gas.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'elapsed_seconds':elapsed,'cases':cases,'measurements':metrics},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':sys.exit(main())
