// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {OperatorControlsTest} from "./OperatorControls.t.sol";
import {PoolConfig} from "../src/libraries/ZZZTypes.sol";

/// Real sealed controller and registry. Venue/feed tokens are local fixtures.
contract SingleContributionPoolTest is OperatorControlsTest {
    function _other(bool enabled) private view returns (PoolConfig memory c) {
        c = config; c.key.fee = 500; c.depositsEnabled = enabled;
    }
    function _configure(PoolConfig memory c) private { registry.configure(c); }
    /// Test-only contract-governance batch: both writes originate from the actual
    /// governance address and rollback atomically if admission fails.
    function governanceSwitch(PoolConfig calldata c) external {
        require(msg.sender == address(this), "self only");
        registry.disablePool(pool, true, false); registry.configure(c);
    }
    function _switch(PoolConfig memory c, bool shouldRevert) private {
        if (shouldRevert) vm.expectRevert();
        this.governanceSwitch(c);
    }
    function testSecondEnabledPoolRejectedWithoutAdmissionOrChangingFirst() public {
        assertEq(registry.contributionPool(), pool);
        PoolConfig memory c = _other(true);
        bytes32 second = keccak256(abi.encode(c.key));
        vm.prank(ac.governance()); vm.expectRevert(); registry.configure(c);
        assertFalse(registry.exists(second)); assertTrue(registry.get(pool).depositsEnabled);
        assertEq(registry.contributionPool(), pool);
    }
    function testMaintenanceOnlyPoolAdmissionAndStopDoNotClearContributionPool() public {
        PoolConfig memory c = _other(false); _configure(c);
        bytes32 second = keccak256(abi.encode(c.key));
        assertTrue(registry.get(second).operationsEnabled);
        vm.prank(ac.governance()); registry.disablePool(second, true, true);
        assertEq(registry.contributionPool(), pool);
        c.depositsEnabled = true;
        vm.prank(ac.governance()); vm.expectRevert(); registry.configure(c);
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
        vm.prank(ac.governance()); registry.disablePool(pool, false, true);
        assertEq(registry.contributionPool(), pool);
        vm.prank(ac.governance()); vm.expectRevert(); registry.configure(_other(true));
    }
    function testAtomicGovernanceSwitchPreservesOldPoolMaintenanceAndIdentity() public {
        PoolConfig memory c = _other(true); _switch(c, false);
        bytes32 second = keccak256(abi.encode(c.key));
        assertEq(registry.contributionPool(), second);
        assertFalse(registry.get(pool).depositsEnabled);
        assertTrue(registry.get(pool).operationsEnabled);
        assertTrue(registry.get(second).depositsEnabled);
        assertTrue(registry.exists(pool));
        vm.prank(ac.governance()); vm.expectRevert(); registry.configure(config);
        // Stopping an old historical pool again cannot unset the selected pool.
        vm.prank(ac.governance()); registry.disablePool(pool, true, false);
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
        vm.prank(ac.governance()); registry.disablePool(pool, true, false);
        assertEq(registry.contributionPool(), bytes32(0));
        vm.prank(ac.governance()); vm.expectRevert(); registry.configure(_other(true));
        assertEq(registry.contributionPool(), bytes32(0));
        vm.clearMockedCalls(); _configure(_other(true));
        assertFalse(registry.get(pool).depositsEnabled);
        assertTrue(registry.get(registry.contributionPool()).depositsEnabled);
    }
}
