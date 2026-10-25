"""Isolated old/new Access CREATE and guardian-call gas; no RPC or deployment."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
EXTERNAL=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OUT=EXTERNAL/'day-readiness-20261025/role-gas'
TRACKED=Path(__file__).resolve().parent
SOLC=EXTERNAL/'toolchain-0.8.26/solc.exe'
FORGE=EXTERNAL/'foundry-v1.4.4/forge.exe'
BASELINE=EXTERNAL/'day-readiness-20261025/solidity/controlled-baseline-output.json'
CURRENT=EXTERNAL/'deep-cleanup-20261025/solidity/source-build.json'

HARNESS=r'''// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function readFile(string calldata path) external view returns(string memory);
    function parseJsonBytes(string calldata json,string calldata key) external pure returns(bytes memory);
    function recordLogs() external;
    function getRecordedLogs() external returns(Log[] memory);
    function cool(address target) external;
}
interface IAccess {
    function governance() external view returns(address);
    function bootstrap() external view returns(address);
    function keepers(address) external view returns(bool);
    function guardians(address) external view returns(bool);
    function isSealed() external view returns(bool);
    function setGuardian(address,bool) external;
}
contract RoleGasTest {
    Vm private constant vm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address private constant KEEPER=address(0xBEEF);
    address private constant GUARDIAN=address(0x600D);
    address private constant ACCOUNT=address(0xC0FFEE);
    bytes32 private constant KEEPER_EVENT=keccak256("KeeperChanged(address,bool)");
    bytes32 private constant GUARDIAN_EVENT=keccak256("GuardianChanged(address,bool)");
    event log_named_uint(string key,uint256 value);
    function _create(bytes memory code) private returns(address result,uint256 spent) {
        assembly {
            let pointer := add(code,32)
            let length := mload(code)
            let before := gas()
            result := create(0,pointer,length)
            spent := sub(before,gas())
        }
        require(result!=address(0),"CREATE failed");
    }
    function _call(address target,bytes memory payload) private returns(uint256 spent) {
        bool ok;
        assembly {
            let pointer := add(payload,32)
            let length := mload(payload)
            let before := gas()
            ok := call(gas(),target,0,pointer,length,0,0)
            spent := sub(before,gas())
        }
        require(ok,"Role update failed");
    }
    function _log(Vm.Log memory item,address emitter,bytes32 signature,address account,bool enabled) private pure {
        require(item.emitter==emitter && item.topics.length==2,"Log identity");
        require(item.topics[0]==signature && item.topics[1]==bytes32(uint256(uint160(account))),"Log topics");
        require(keccak256(item.data)==keccak256(abi.encode(enabled)),"Log enabled payload");
    }
    function _authorities(address target) private view {
        IAccess access=IAccess(target);
        require(access.governance()==address(this) && access.bootstrap()==address(this),"Initial authority");
        require(access.keepers(KEEPER) && access.guardians(GUARDIAN) && !access.isSealed(),"Initial role state");
    }
    function _role(address oldAccess,address newAccess,bool enabled,string memory name) private {
        bytes memory payload=abi.encodeCall(IAccess.setGuardian,(ACCOUNT,enabled));
        vm.cool(oldAccess);vm.cool(newAccess);
        vm.recordLogs();uint256 oldGas=_call(oldAccess,payload);Vm.Log[] memory oldLogs=vm.getRecordedLogs();
        vm.recordLogs();uint256 newGas=_call(newAccess,payload);Vm.Log[] memory newLogs=vm.getRecordedLogs();
        require(oldLogs.length==0 && newLogs.length==1,"Setter event counts");
        _log(newLogs[0],newAccess,GUARDIAN_EVENT,ACCOUNT,enabled);
        require(IAccess(oldAccess).guardians(ACCOUNT)==enabled && IAccess(newAccess).guardians(ACCOUNT)==enabled,"Role state differs");
        emit log_named_uint(string.concat(name," baseline"),oldGas);
        emit log_named_uint(string.concat(name," candidate"),newGas);
        require(newGas>oldGas,"Expected extra event execution cost");
    }
    function testControlledRoleGasAndObservableAuthority() public {
        string memory json=vm.readFile("BYTECODE_FILE");
        bytes memory arguments=abi.encode(address(this),KEEPER,GUARDIAN);
        bytes memory oldCode=bytes.concat(vm.parseJsonBytes(json,".baseline"),arguments);
        bytes memory newCode=bytes.concat(vm.parseJsonBytes(json,".candidate"),arguments);
        // Both complete initcode arrays and payload memory exist before measurement.
        vm.recordLogs();(address oldAccess,uint256 oldCreate)=_create(oldCode);Vm.Log[] memory oldLogs=vm.getRecordedLogs();
        vm.recordLogs();(address newAccess,uint256 newCreate)=_create(newCode);Vm.Log[] memory newLogs=vm.getRecordedLogs();
        require(oldLogs.length==0 && newLogs.length==2,"Constructor event counts");
        _log(newLogs[0],newAccess,KEEPER_EVENT,KEEPER,true);
        _log(newLogs[1],newAccess,GUARDIAN_EVENT,GUARDIAN,true);
        _authorities(oldAccess);_authorities(newAccess);
        emit log_named_uint("constructor CREATE baseline",oldCreate);
        emit log_named_uint("constructor CREATE candidate",newCreate);
        _role(oldAccess,newAccess,true,"guardian grant");
        _role(oldAccess,newAccess,true,"guardian idempotent grant");
        _role(oldAccess,newAccess,false,"guardian revoke");
        _authorities(oldAccess);_authorities(newAccess);
    }
}
'''

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    if OUT.exists():raise ValueError('Use a new gas campaign; preserve earlier outputs')
    (OUT/'test').mkdir(parents=True)
    before=json.loads(BASELINE.read_text());after=json.loads(CURRENT.read_text())
    key='src/ZZZAccessController.sol'
    old=before['contracts'][key]['ZZZAccessController'];new=after['contracts'][key]['ZZZAccessController']
    bytecodes={'baseline':'0x'+old['evm']['bytecode']['object'],'candidate':'0x'+new['evm']['bytecode']['object']}
    (OUT/'bytecodes.json').write_text(json.dumps(bytecodes),encoding='utf-8')
    source=HARNESS.replace('BYTECODE_FILE',(OUT/'bytecodes.json').as_posix())
    (OUT/'test/RoleGas.t.sol').write_text(source,encoding='utf-8')
    settings=json.loads((EXTERNAL/'deep-cleanup-20261025/solidity/source-build-input.json').read_text())['settings']
    remappings=json.dumps(settings['remappings'])
    config=f'''[profile.default]
src = "src"
test = "test"
out = "out"
cache_path = "cache"
evm_version = "cancun"
via_ir = true
optimizer = true
optimizer_runs = 1
optimizer_details = {{ yul = false }}
remappings = {remappings}
fs_permissions = [{{ access = "read", path = "{(OUT/'bytecodes.json').as_posix()}" }}]
'''
    (OUT/'foundry.toml').write_text(config,encoding='utf-8')
    command=[str(FORGE),'test','--root',str(OUT),'--use',str(SOLC),'--match-contract','RoleGasTest','--json']
    start=time.monotonic();completed=subprocess.run(command,cwd=OUT,capture_output=True,timeout=300)
    (OUT/'forge.stdout.json').write_bytes(completed.stdout);(OUT/'forge.stderr.log').write_bytes(completed.stderr)
    elapsed=round(time.monotonic()-start,3)
    try:results=json.loads(completed.stdout)
    except ValueError:results=None
    report={'scope':'Disposable Forge CREATE/call execution gas, not persistent/public deployment or target-chain cost.',
        'command':command,'exit_code':completed.returncode,'elapsed_seconds':elapsed,'results':results,
        'compiler_sha256':sha(SOLC.read_bytes()),'forge_sha256':sha(FORGE.read_bytes()),
        'artifact_sha256':{str(path):sha(path.read_bytes()) for path in (BASELINE,CURRENT,OUT/'bytecodes.json',OUT/'test/RoleGas.t.sol',OUT/'foundry.toml')},
        'baseline_runtime_bytes':len(bytes.fromhex(old['evm']['deployedBytecode']['object'])),
        'candidate_runtime_bytes':len(bytes.fromhex(new['evm']['deployedBytecode']['object'])),
        'baseline_creation_bytes':len(bytes.fromhex(old['evm']['bytecode']['object'])),
        'candidate_creation_bytes':len(bytes.fromhex(new['evm']['bytecode']['object'])),
        'constructor_wire_labels':{'baseline':[x for x in old['abi'] if x['type']=='constructor'],
                                   'candidate':[x for x in new['abi'] if x['type']=='constructor']},
        'limits':['Raw gasleft deltas include CREATE/code-deposit or CALL execution, not transaction intrinsic/calldata/L1/network overhead.',
            'Raw deltas do not apply transaction refunds; revoke net billed gas is not inferred.',
            'Role calls use the same bootstrap/governance test caller, same payload and preallocated memory; target state is cooled before each pair.',
            'This is local isolated EVM code with reviewed compiled bytecodes, not target-chain deployment/rehearsal or production approval.']}
    (TRACKED/'role-gas-initial.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'exit_code':completed.returncode,'elapsed_seconds':elapsed,'results':results},indent=2))
    return completed.returncode

if __name__=='__main__':sys.exit(main())
