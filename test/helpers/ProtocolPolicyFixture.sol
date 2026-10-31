// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZProtocolPolicy} from "../../src/ZZZProtocolPolicy.sol";
import {IZZZAccess} from "../../src/interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "../../src/interfaces/IZZZProtocolPolicy.sol";
import {Vm} from "forge-std/Vm.sol";

/// @dev TEST ONLY: explicit new-profile policy setup; never changes installed contracts.
library ProtocolPolicyFixture {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    function bind(address controller) internal returns(ZZZProtocolPolicy policy) {
        return bind(controller,address(0x7EA5));
    }
    function bind(address controller,address recipient) internal returns(ZZZProtocolPolicy policy) {
        address existing = IZZZAccess(controller).protocolPolicy();
        if(existing != address(0)) return ZZZProtocolPolicy(existing);
        policy = new ZZZProtocolPolicy(controller,recipient);
        (bool ok,) = controller.call(abi.encodeWithSignature("bindProtocolPolicy(address)",address(policy)));
        if(!ok) {
            (ok,) = controller.call(abi.encodeWithSignature("setProtocolPolicy(address)",address(policy)));
            require(ok,"TEST_ONLY policy binding failed");
        }
    }
    function recipient(address controller,address next) internal {
        ZZZProtocolPolicy policy = ZZZProtocolPolicy(IZZZAccess(controller).protocolPolicy());
        if(IZZZProtocolPolicy(address(policy)).salePolicy().recipient == next) return;
        policy.proposeMintRecipient(next,keccak256("TEST_ONLY reviewed mint recipient"));
        vm.prank(next); policy.acceptMintRecipient();
    }
    function randomness(address controller,address coordinator,bytes32 key,uint256 sub,uint16 confirmations,uint32 gasLimit,bool nativePayment) internal {
        ZZZProtocolPolicy(IZZZAccess(controller).protocolPolicy()).configureRandomness(coordinator,coordinator.codehash,
            key,sub,confirmations,gasLimit,nativePayment,keccak256("TEST_ONLY reviewed randomness provider"));
    }
}
