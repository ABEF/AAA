// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, BoundDummy} from "./mocks/Mocks.sol";

contract PolicyImplementationOne { function version() external pure returns (uint256) { return 1; } }
contract PolicyImplementationTwo { function version() external pure returns (uint256) { return 2; } }

/// @dev Local policy-authentication fixture, not a real canonical-WETH dependency.
contract PolicyAdminFixture {
    address public owner;
    address public implementation;
    constructor(address i, address o) { implementation = i; owner = o; }
    function setImplementation(address i) external { implementation = i; }
    function setOwner(address next) external { owner = next; }
    function getProxyAdmin(address) external view returns (address) { return address(this); }
    function getProxyImplementation(address) external view returns (address) { return implementation; }
}

contract NativeWrapperPolicyTest is Test {
    MockAccess private access;
    ZZZPoolRegistry private registry;
    PolicyImplementationOne private first;
    PolicyImplementationTwo private second;
    PolicyAdminFixture private admin;
    function setUp() public {
        if (block.timestamp < 2) vm.warp(1000000);
        access = new MockAccess(); registry = new ZZZPoolRegistry(address(access));
        first = new PolicyImplementationOne(); second = new PolicyImplementationTwo();
        admin = new PolicyAdminFixture(address(first), address(this));
    }
    function _policy(address implementation) private view returns (ZZZPoolRegistry.WrapperPolicy memory p) {
        p = ZZZPoolRegistry.WrapperPolicy(address(admin), implementation, address(this), address(admin).codehash, implementation.codehash);
    }
    function testWrapperPolicyUnauthorizedApprovalAndActivationRejected() public {
        ZZZPoolRegistry.WrapperPolicy memory p = _policy(address(first));
        vm.prank(address(0xBAD)); vm.expectRevert(); registry.approveWrapperPolicy(p);
        bytes32 id = registry.approveWrapperPolicy(p);
        vm.prank(address(0xBAD)); vm.expectRevert(); registry.activateWrapperPolicy(id);
        assertTrue(registry.wrapperPolicyExists(id));
    }
    function testWrapperPolicyAppendOnlyAndHistoricalRecordSurvivesActivation() public {
        bytes32 bootstrap = registry.activeWrapperPolicy();
        ZZZPoolRegistry.WrapperPolicy memory p = _policy(address(first)); bytes32 id = registry.approveWrapperPolicy(p);
        vm.expectRevert(); registry.approveWrapperPolicy(p);
        registry.activateWrapperPolicy(id); assertEq(registry.activeWrapperPolicy(), id);
        admin.setImplementation(address(second)); bytes32 next = registry.approveWrapperPolicy(_policy(address(second)));
        registry.activateWrapperPolicy(next); assertTrue(registry.wrapperPolicyExists(id)); assertTrue(registry.wrapperPolicyExists(bootstrap));
        (address oldAdmin, address oldImplementation, address oldOwner, bytes32 oldAdminCode, bytes32 oldImplementationCode) = registry.wrapperPolicies(id);
        assertEq(oldAdmin, p.admin); assertEq(oldImplementation, address(first)); assertEq(oldOwner, p.adminOwner);
        assertEq(oldAdminCode, p.adminCodeHash); assertEq(oldImplementationCode, p.implementationCodeHash);
    }
    function testWrapperPolicyMustMatchCurrentCodeOwnerAndReportedImplementation() public {
        ZZZPoolRegistry.WrapperPolicy memory p = _policy(address(first)); p.implementationCodeHash = bytes32(uint256(1));
        vm.expectRevert(); registry.approveWrapperPolicy(p);
        p = _policy(address(first)); p.adminOwner = address(0xBAD); vm.expectRevert(); registry.approveWrapperPolicy(p);
        p = _policy(address(second)); vm.expectRevert(); registry.approveWrapperPolicy(p);
    }
    function testWrapperPolicyActivationRechecksCurrentObservation() public {
        bytes32 beforePolicy = registry.activeWrapperPolicy(); bytes32 id = registry.approveWrapperPolicy(_policy(address(first)));
        admin.setImplementation(address(second)); vm.expectRevert(); registry.activateWrapperPolicy(id);
        assertEq(registry.activeWrapperPolicy(), beforePolicy);
        vm.expectRevert(); registry.activateWrapperPolicy(bytes32(uint256(1)));
    }
    function testWrapperPolicyRejectsZeroOrEOAImplementationAndDoesNotAcceptNativeFunds() public {
        ZZZPoolRegistry.WrapperPolicy memory p = _policy(address(first)); p.implementation = address(0); vm.expectRevert(); registry.approveWrapperPolicy(p);
        p = _policy(address(first)); p.implementation = address(0xBAD); p.implementationCodeHash = address(0xBAD).codehash;
        vm.expectRevert(); registry.approveWrapperPolicy(p);
        vm.deal(address(this), 1); (bool ok,) = address(registry).call{value: 1}(""); assertFalse(ok);
    }
    function testWrapperPolicyAfterSealRequiresBothImmediateGovernanceActions() public {
        address[] memory authorities = new address[](1); authorities[0] = address(this);
        ZZZAccessController controller = new ZZZAccessController(0, authorities, authorities, address(0x123), address(0x456));
        ZZZPoolRegistry governed = new ZZZPoolRegistry(address(controller));
        bytes32[16] memory ids = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP, Ids.FEES,
            Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION, Ids.BRIDGE, Ids.RECEIVER,
            Ids.ORACLE, Ids.POOLS, Ids.ROUTES, Ids.TRANSPORT];
        for (uint256 i; i < ids.length; ++i) {
            if (ids[i] == Ids.BRIDGE || ids[i] == Ids.RECEIVER || ids[i] == Ids.ROUTES || ids[i] == Ids.TRANSPORT) continue;
            controller.bind(ids[i], ids[i] == Ids.POOLS ? address(governed) : address(new BoundDummy(address(controller))));
        }
        CanonicalFixture.bind(address(controller));
        controller.seal(); ZZZPoolRegistry.WrapperPolicy memory p = _policy(address(first));
        bytes32 id = keccak256(abi.encode(p)); bytes memory data = abi.encodeCall(governed.approveWrapperPolicy, (p));
        vm.expectRevert(); governed.approveWrapperPolicy(p);
        bytes32 salt = keccak256("review-wrapper-implementation");
        controller.schedule(address(governed), 0, data, bytes32(0), salt, 0);
        controller.execute(address(governed), 0, data, bytes32(0), salt);
        assertTrue(governed.wrapperPolicyExists(id)); assertTrue(governed.activeWrapperPolicy() != id);
        data = abi.encodeCall(governed.activateWrapperPolicy, (id)); salt = keccak256("activate-reviewed-wrapper");
        vm.expectRevert(); governed.activateWrapperPolicy(id);
        controller.schedule(address(governed), 0, data, bytes32(0), salt, 0);
        controller.execute(address(governed), 0, data, bytes32(0), salt);
        assertEq(governed.activeWrapperPolicy(), id); assertEq(controller.getMinDelay(), 0);
    }
    function testWrapperPolicyRenouncedOwnerCanBeReviewedThroughImmediateGovernance() public {
        address[] memory authorities = new address[](1); authorities[0] = address(this);
        ZZZAccessController controller = new ZZZAccessController(0, authorities, authorities, address(0x123), address(0x456));
        ZZZPoolRegistry governed = new ZZZPoolRegistry(address(controller));
        bytes32[16] memory ids = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP, Ids.FEES,
            Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION, Ids.BRIDGE, Ids.RECEIVER,
            Ids.ORACLE, Ids.POOLS, Ids.ROUTES, Ids.TRANSPORT];
        for (uint256 i; i < ids.length; ++i) {
            if (ids[i] == Ids.BRIDGE || ids[i] == Ids.RECEIVER || ids[i] == Ids.ROUTES || ids[i] == Ids.TRANSPORT) continue;
            controller.bind(ids[i], ids[i] == Ids.POOLS ? address(governed) : address(new BoundDummy(address(controller))));
        }
        ZZZPoolRegistry.WrapperPolicy memory previous = _policy(address(first));
        bytes32 previousId = governed.approveWrapperPolicy(previous); governed.activateWrapperPolicy(previousId);
        CanonicalFixture.bind(address(controller));
        controller.seal(); admin.setOwner(address(0));
        ZZZPoolRegistry.WrapperPolicy memory renounced = previous; renounced.adminOwner = address(0);
        bytes32 id = keccak256(abi.encode(renounced));
        vm.expectRevert(); governed.approveWrapperPolicy(renounced);
        bytes memory data = abi.encodeCall(governed.approveWrapperPolicy, (renounced)); bytes32 salt = keccak256("review-renounced-wrapper-admin");
        controller.schedule(address(governed), 0, data, bytes32(0), salt, 0);
        controller.execute(address(governed), 0, data, bytes32(0), salt);
        assertEq(governed.activeWrapperPolicy(), previousId); assertTrue(governed.wrapperPolicyExists(previousId));
        data = abi.encodeCall(governed.activateWrapperPolicy, (id)); salt = keccak256("activate-renounced-wrapper-admin");
        controller.schedule(address(governed), 0, data, bytes32(0), salt, 0);
        controller.execute(address(governed), 0, data, bytes32(0), salt);
        assertEq(governed.activeWrapperPolicy(), id);
        (,, address reviewedOwner,,) = governed.wrapperPolicies(id); assertEq(reviewedOwner, address(0));
        (,, address historicalOwner,,) = governed.wrapperPolicies(previousId); assertEq(historicalOwner, address(this));
    }
}
