// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {OperatorControlsTest} from "./OperatorControls.t.sol";
import {PoolConfig} from "../src/libraries/ZZZTypes.sol";

/// Real sealed controller and registry. Venue/feed tokens are local fixtures.
contract SingleContributionPoolTest is OperatorControlsTest {
    function _other(bool enabled) private view returns (PoolConfig memory c) {
        c = config; c.key.fee = 500; c.depositsEnabled = enabled;
    }
    function _configure(PoolConfig memory c) private {
        bytes memory data = abi.encodeCall(registry.configure, (c));
        bytes32 salt = bytes32(++nonce);
        ac.schedule(address(registry), 0, data, bytes32(0), salt, 0);
        ac.execute(address(registry), 0, data, bytes32(0), salt);
    }
    function _switch(PoolConfig memory c, bool shouldRevert) private {
        address[] memory targets = new address[](2);
        uint256[] memory values = new uint256[](2);
        bytes[] memory payloads = new bytes[](2);
        targets[0] = address(registry); targets[1] = address(registry);
        payloads[0] = abi.encodeCall(registry.disablePool, (pool, true, false));
        payloads[1] = abi.encodeCall(registry.configure, (c));
        bytes32 salt = bytes32(++nonce);
        ac.scheduleBatch(targets, values, payloads, bytes32(0), salt, 0);
        if (shouldRevert) vm.expectRevert();
        ac.executeBatch(targets, values, payloads, bytes32(0), salt);
    }
    function testSecondEnabledPoolRejectedWithoutAdmissionOrChangingFirst() public {
        assertEq(registry.contributionPool(), pool);
        PoolConfig memory c = _other(true);
        bytes32 second = keccak256(abi.encode(c.key));
        vm.prank(address(ac)); vm.expectRevert(); registry.configure(c);
        assertFalse(registry.exists(second)); assertTrue(registry.get(pool).depositsEnabled);
        assertEq(registry.contributionPool(), pool);
    }
    function testMaintenanceOnlyPoolAdmissionAndStopDoNotClearContributionPool() public {
        PoolConfig memory c = _other(false); _configure(c);
        bytes32 second = keccak256(abi.encode(c.key));
        assertTrue(registry.get(second).operationsEnabled);
        vm.prank(address(ac)); registry.disablePool(second, true, true);
        assertEq(registry.contributionPool(), pool);
        c.depositsEnabled = true;
        vm.prank(address(ac)); vm.expectRevert(); registry.configure(c);
    }
    function testCurrentPoolReconfigurationAndExplicitStopAndReopen() public {
        config.rangeBps = 1500; _configure(config);
        assertEq(registry.contributionPool(), pool);
        config.depositsEnabled = false; _configure(config);
        assertEq(registry.contributionPool(), bytes32(0));
        config.depositsEnabled = true; _configure(config);
        assertEq(registry.contributionPool(), pool);
    }
    function testOperationsStopAloneDoesNotReleaseContributionSelection() public {
        vm.prank(address(ac)); registry.disablePool(pool, false, true);
        assertEq(registry.contributionPool(), pool);
        vm.prank(address(ac)); vm.expectRevert(); registry.configure(_other(true));
    }
    function testAtomicGovernanceSwitchPreservesOldPoolMaintenanceAndIdentity() public {
        PoolConfig memory c = _other(true); _switch(c, false);
        bytes32 second = keccak256(abi.encode(c.key));
        assertEq(registry.contributionPool(), second);
        assertFalse(registry.get(pool).depositsEnabled);
        assertTrue(registry.get(pool).operationsEnabled);
        assertTrue(registry.get(second).depositsEnabled);
        assertTrue(registry.exists(pool));
        vm.prank(address(ac)); vm.expectRevert(); registry.configure(config);
        // Stopping an old historical pool again cannot unset the selected pool.
        vm.prank(address(ac)); registry.disablePool(pool, true, false);
        assertEq(registry.contributionPool(), second);
    }
    function testAtomicSwitchFailureRestoresFirstPool() public {
        PoolConfig memory c = _other(true); c.rangeBps = 0;
        _switch(c, true);
        assertEq(registry.contributionPool(), pool);
        assertTrue(registry.get(pool).depositsEnabled);
        assertFalse(registry.exists(keccak256(abi.encode(c.key))));
    }
    function testDependencyFailureStopClearsSelectionButFailedOpenDoesNotSelect() public {
        vm.mockCallRevert(address(oracle), bytes(""), bytes("unavailable"));
        vm.prank(address(ac)); registry.disablePool(pool, true, false);
        assertEq(registry.contributionPool(), bytes32(0));
        vm.prank(address(ac)); vm.expectRevert(); registry.configure(_other(true));
        assertEq(registry.contributionPool(), bytes32(0));
        vm.clearMockedCalls(); _configure(_other(true));
        assertFalse(registry.get(pool).depositsEnabled);
        assertTrue(registry.get(registry.contributionPool()).depositsEnabled);
    }
}
