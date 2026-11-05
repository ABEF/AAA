// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZRoyaltyFactory} from "../src/ZZZRoyaltyFactory.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZRoyaltyCodeData} from "../src/ZZZRoyaltyCodeData.sol";

/// @notice Fixed code-data transport only; no public deployment/chain qualification.
contract RoyaltyFactoryCodeDataTest is Test {
    function _factory() private returns(ZZZRoyaltyFactory) { return new ZZZRoyaltyFactory(); }
    function _reject(ZZZRoyaltyFactory factory) private {
        vm.expectRevert(ZZZRoyaltyFactory.InvalidCreationCode.selector);factory.create();
    }
    function testPartsReconstructExactSourceBytesAndActualNormalRuntimeLimits() public {
        ZZZRoyaltyFactory factory=_factory();bytes memory original=type(ZZZRoyaltyRewards).creationCode;
        assertEq(factory.CODE_STORAGE_VERSION(),2);assertEq(factory.creationCodeLength(),original.length);
        assertEq(factory.royaltyCodeHash(),keccak256(original));assertTrue(factory.part0()!=factory.part1());
        bytes memory head=factory.part0().code;bytes memory tail=factory.part1().code;
        assertEq(head.length,24576);assertEq(tail.length,original.length-24573+3);
        assertLe(head.length,24576);assertLe(tail.length,24576);
        assertEq(head[0],hex"5f");assertEq(head[1],hex"5f");assertEq(head[2],hex"fd");
        assertEq(tail[0],hex"5f");assertEq(tail[1],hex"5f");assertEq(tail[2],hex"fd");
        assertEq(keccak256(head),factory.part0CodeHash());assertEq(keccak256(tail),factory.part1CodeHash());
        // Independent byte-by-byte reconstruction, not the factory's EXTCODECOPY.
        bytes memory rebuilt=new bytes(original.length);
        for(uint256 i;i<original.length;++i) rebuilt[i]=i<24573?head[i+3]:tail[i-24573+3];
        assertEq(rebuilt,original);
        ZZZRoyaltyRewards ledger=factory.create();
        assertEq(ledger.nft(),address(this));assertEq(ledger.canonicalController(),address(this));
        assertEq(ledger.ROYALTY_SETTLEMENT_VERSION(),4);
    }
    function testSameLengthPrefixReplacementCannotHideBehindUnchangedPayload() public {
        ZZZRoyaltyFactory factory=_factory();bytes memory code=factory.part0().code;
        code[0]=hex"00";vm.etch(factory.part0(),code);_reject(factory);
    }
    function testSameLengthTailPayloadReplacementRejects() public {
        ZZZRoyaltyFactory factory=_factory();bytes memory code=factory.part1().code;
        code[3]^=bytes1(uint8(1));vm.etch(factory.part1(),code);_reject(factory);
    }
    function testMissingEitherDataChildRejects() public {
        ZZZRoyaltyFactory factory=_factory();bytes memory head=factory.part0().code;
        vm.etch(factory.part0(),hex"");_reject(factory);
        vm.etch(factory.part0(),head);vm.etch(factory.part1(),hex"");_reject(factory);
    }
    function testTruncatedExtendedAndSwappedPartLengthsReject() public {
        ZZZRoyaltyFactory factory=_factory();bytes memory tail=factory.part1().code;
        bytes memory shortTail=new bytes(tail.length-1);
        for(uint256 i;i<shortTail.length;++i) shortTail[i]=tail[i];
        vm.etch(factory.part1(),shortTail);_reject(factory);
        vm.etch(factory.part1(),bytes.concat(tail,hex"00"));_reject(factory);
        vm.etch(factory.part1(),tail);vm.etch(factory.part0(),tail);_reject(factory);
    }
    function testCarrierRejectsOrdinaryCallsAndNativePayments() public {
        ZZZRoyaltyFactory factory=_factory();vm.deal(address(this),1 ether);
        address[2] memory parts=[factory.part0(),factory.part1()];
        for(uint256 i;i<2;++i) {
            (bool called,)=parts[i].call(hex"12345678");assertFalse(called);
            (bool paid,)=parts[i].call{value:1}(hex"");assertFalse(paid);assertEq(parts[i].balance,0);
        }
        (bool funded,)=address(factory).call{value:1}(abi.encodeCall(factory.create,()));assertFalse(funded);
    }
    function testCarrierEmptyAndMaximumBoundaryAreBoundedInertData() public {
        ZZZRoyaltyCodeData empty=new ZZZRoyaltyCodeData(hex"");assertEq(address(empty).code,hex"5f5ffd");
        ZZZRoyaltyCodeData maximum=new ZZZRoyaltyCodeData(new bytes(24573));assertEq(address(maximum).code.length,24576);
        vm.expectRevert(ZZZRoyaltyCodeData.DataTooLong.selector);new ZZZRoyaltyCodeData(new bytes(24574));
    }
    function testNoPointerMutatorArbitraryCodeOrRecipientEntryExists() public {
        ZZZRoyaltyFactory factory=_factory();address head=factory.part0();address tail=factory.part1();
        (bool a,)=address(factory).call(abi.encodeWithSignature("setParts(address,address)",address(1),address(2)));
        (bool b,)=address(factory).call(abi.encodeWithSignature("create(bytes)",hex"60006000f3"));
        (bool c,)=address(factory).call(abi.encodeWithSignature("create(address)",address(3)));
        assertFalse(a);assertFalse(b);assertFalse(c);assertEq(factory.part0(),head);assertEq(factory.part1(),tail);
        assertEq(factory.controller(),address(this));
    }
}
