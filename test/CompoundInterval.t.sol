// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {PoolConfig,PoolKey} from "../src/libraries/ZZZTypes.sol";

/// Real accounting/Budget with the explicit synthetic venue/strategy fixture.
contract CompoundIntervalTest is PooledVaultFixture {
    function setUp() public override {
        super.setUp();policy.setNeed(false);
        PoolConfig memory c=pools.get(poolId);c.minRebalanceInterval=12 hours;pools.set(poolId,c);
    }
    function testDefaultCompoundHourIsIndependentOfTwelveHourRebalance() public {
        activatedPosition();uint256 bucket=_bucket();uint256 created=vault.group(bucket).lastRebalance;
        assertEq(vault.migrationBudget().IDLE_COMPOUNDING_VERSION(),4);
        assertEq(vault.migrationBudget().compoundInterval(poolId),3600);
        venue.setFees(100,100);
        vm.warp(created+3599);assertFalse(vault.migrationBudget().compoundReady(bucket));
        vm.warp(created+3600);assertTrue(vault.migrationBudget().compoundReady(bucket));
        compounder.compound(bucket,1,block.timestamp+100);
        assertEq(vault.group(bucket).lastRebalance,created);
        assertEq(vault.migrationBudget().lastCompound(bucket),created+3600);
        assertFalse(vault.migrationBudget().compoundReady(bucket));
    }
    function testIntervalChangesNeverResetPhysicalOrCompoundClocks() public {
        activatedPosition();uint256 bucket=_bucket();uint256 created=vault.group(bucket).lastRebalance;
        vault.migrationBudget().setCompoundInterval(poolId,7200);
        vm.warp(created+3600);assertFalse(vault.migrationBudget().compoundReady(bucket));
        vault.migrationBudget().setCompoundInterval(poolId,600);
        assertTrue(vault.migrationBudget().compoundReady(bucket));
        assertEq(vault.group(bucket).lastRebalance,created);
        assertEq(vault.migrationBudget().lastCompound(bucket),0);
        PoolConfig memory c=pools.get(poolId);c.minRebalanceInterval=7 days;pools.set(poolId,c);
        assertTrue(vault.migrationBudget().compoundReady(bucket));
    }
    function testCompoundPoliciesArePerAdmittedPool() public {
        PoolConfig memory c=pools.get(poolId);c.key.fee=500;bytes32 other=keccak256(abi.encode(c.key));pools.set(other,c);
        vault.migrationBudget().setCompoundInterval(poolId,7200);
        assertEq(vault.migrationBudget().compoundInterval(other),3600);
        vault.migrationBudget().setCompoundInterval(other,1200);
        assertEq(vault.migrationBudget().compoundInterval(poolId),7200);
        assertEq(vault.migrationBudget().compoundInterval(other),1200);
    }
    function testUnknownPoolBoundsAndUnprivilegedSetterFailClosed() public {
        ZZZMigrationBudget budget=vault.migrationBudget();
        vm.expectRevert(ZZZMigrationBudget.InvalidConfiguration.selector);budget.setCompoundInterval(poolId,599);
        vm.expectRevert(ZZZMigrationBudget.InvalidConfiguration.selector);budget.setCompoundInterval(poolId,7 days+1);
        vm.expectRevert(ZZZMigrationBudget.InvalidConfiguration.selector);budget.setCompoundInterval(bytes32(uint256(1)),3600);
        vm.expectRevert(ZZZMigrationBudget.InvalidConfiguration.selector);budget.compoundInterval(bytes32(0));
        vm.prank(alice);vm.expectRevert(ZZZMigrationBudget.Unauthorized.selector);budget.setCompoundInterval(poolId,3600);
    }
    function testPreparationCanonicalAndActiveSnapshotRejectPolicyChanges() public {
        ZZZMigrationBudget budget=vault.migrationBudget();
        ac.setPreparation(true);vm.expectRevert();budget.setCompoundInterval(poolId,3600);ac.setPreparation(false);
        ac.setCanonicalState(1);vm.expectRevert(ZZZMigrationBudget.CanonicalLocked.selector);
        budget.setCompoundInterval(poolId,3600);ac.setCanonicalState(0);
        activatedPosition();
        // Privileged Vault checkpoint models an already-running operation.
        vm.prank(address(vault));budget.checkpoint(_bucket(),0);
        vm.expectRevert(ZZZMigrationBudget.InvalidConfiguration.selector);budget.setCompoundInterval(poolId,600);
        assertEq(budget.compoundInterval(poolId),3600);
    }
    function testOrdinaryPauseAllowsReviewedIntervalConfiguration() public {
        ac.setPaused(true);vault.migrationBudget().setCompoundInterval(poolId,600);
        assertEq(vault.migrationBudget().compoundInterval(poolId),600);
        assertTrue(ac.paused());
    }
}
