// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Real Vault admission/custody regressions. Venue, feeds, governance
/// and authority are explicit fixtures, not live venue/market qualification.
contract ReservationCapacityTest is PooledVaultFixture {
    function _destination(uint256 index) private returns (bytes32 pool) {
        if (index == 0) return poolId;
        PoolConfig memory config = pools.get(poolId);
        config.key.fee = uint24(500 + index);
        pool = keccak256(abi.encode(config.key));
        pools.set(pool, config);
    }

    function _identity(uint256 index) private returns (uint256) {
        return vault.canonicalModule().bucketIdentity(_destination(index));
    }

    function _assertEmptyReservation(bytes32 pool, uint256 bucket) private view {
        Position memory p = vault.group(bucket);
        assertEq(vault.poolBucket(pool), bucket);
        assertEq(uint256(p.status), uint256(PositionStatus.None));
        assertEq(p.lpTokenId, 0); assertEq(p.idle0, 0); assertEq(p.idle1, 0);
        assertEq(vault.bucketTotalShares(bucket), 0); assertEq(vault.homePoolId(bucket), bytes32(0));
    }

    function testReservationImmediatelyOwnsPermanentCapacityWithoutCustodyOrShares() public {
        uint256 bucket = _identity(0);
        vault.reservePool(poolId, bucket);
        assertEq(vault.bucketCount(), 1); assertEq(vault.bucketAt(0), bucket);
        _assertEmptyReservation(poolId, bucket);
        assertEq(membership.totalEligible(), 0);
        assertEq(venue.next(), 1); assertEq(vault.totalIdle(address(t0)), 0);
        assertEq(vault.totalIdle(address(t1)), 0); assertEq(address(vault).balance, 0);
    }



    function testFullCapacityDuplicatesAndPoolAliasesReuseTheSameSlot() public {
        uint256 first;
        for (uint256 i; i < vault.MAX_BUCKETS(); ++i) {
            uint256 bucket = _identity(i); if (i == 0) first = bucket;
            vault.reservePool(_destination(i), bucket);
        }
        vault.reservePool(poolId, first);
        bytes32 aliasPool = _destination(20); vault.reservePool(aliasPool, first);
        vault.reservePool(aliasPool, first);
        bytes32 lastAlias=_destination(21);uint256 last=vault.bucketAt(3);
        vault.reservePool(lastAlias,last);assertEq(vault.canonicalModule().aliasBucket(lastAlias),last);
        assertEq(vault.bucketCount(), 4); assertEq(vault.bucketAt(0), first);
        _assertEmptyReservation(poolId, first); _assertEmptyReservation(aliasPool, first);
        for (uint256 i; i < vault.bucketCount(); ++i) {
            for (uint256 j = i + 1; j < vault.bucketCount(); ++j) assertTrue(vault.bucketAt(i) != vault.bucketAt(j));
        }
    }

    function testPoolReassignmentRejectsWithoutConsumingAnotherSlot() public {
        uint256 first = _identity(0); uint256 second = _identity(1);
        vault.reservePool(poolId, first);
        vm.expectRevert(bytes4(keccak256("InvalidState()"))); vault.reservePool(poolId, second);
        assertEq(vault.bucketCount(), 1); assertEq(vault.bucketAt(0), first);
        _assertEmptyReservation(poolId, first);
        assertEq(uint256(vault.group(second).status), uint256(PositionStatus.None));
    }

    function testInvalidIdentityAndFailedPoolValidationNeverConsumeCapacity() public {
        uint256 bucket = _identity(0);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); vault.reservePool(bytes32(0), bucket);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); vault.reservePool(poolId, 0);
        // The fixture registry is permissive, so explicitly reproduce a real
        // registry's missing-pool failure before any capacity can be committed.
        vm.mockCallRevert(address(pools), abi.encodeWithSignature("get(bytes32)", poolId), abi.encodePacked("missing pool"));
        vm.expectRevert(); vault.reservePool(poolId, bucket); vm.clearMockedCalls();
        assertEq(vault.bucketCount(), 0); assertEq(vault.poolBucket(poolId), 0);
    }





    function testNoncanonicalNewReservationRejectsBeforeActivationAndLeavesSlotUsable() public {
        uint256 canonical = _identity(0);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()")));vault.reservePool(poolId,canonical+1);
        assertEq(vault.bucketCount(),0);assertEq(vault.poolBucket(poolId),0);
        assertEq(vault.canonicalModule().aliasBucket(poolId),0);
        uint256 id = _mint(alice);_activate(alice,id,1000,1000);
        assertEq(vault.bucketCount(),1);assertEq(vault.nftBucket(id),canonical);
        assertGt(vault.sharesOf(id),0);assertTrue(membership.eligible(id));
        assertEq(vault.canonicalModule().aliasBucket(poolId),canonical);
    }

    function testCanonicalActivationUsesItsReservedSlotAtFullCapacity() public {
        uint256 canonical = _bucket(); vault.reservePool(poolId, canonical);
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) {
            uint256 reserved = _identity(i); vault.reservePool(_destination(i), reserved);
        }
        uint256 id = _mint(alice); _activate(alice, id, 1000, 1000);
        assertEq(vault.bucketCount(), 4); assertEq(vault.bucketAt(0), canonical);
        assertEq(vault.nftBucket(id), canonical); assertEq(vault.bucketTotalShares(canonical), vault.sharesOf(id));
        assertEq(membership.totalEligible(), 1); assertTrue(membership.eligible(id));
    }

    function testCanonicalReservationsThenLocalActivationShareOneCapacityLimit() public {
        // Reserving other admitted pools consumes the same finite capacity as
        // the initial local activation; each new identity is companion-derived.
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) {
            uint256 reserved = _identity(i); vault.reservePool(_destination(i), reserved);
        }
        uint256 id = activatedPosition(); assertEq(vault.bucketCount(), 4);
        assertEq(vault.nftBucket(id), _bucket()); assertEq(vault.bucketAt(3), _bucket());
        uint256 extra = _identity(9); bytes32 extraPool = _destination(9);
        vm.expectRevert(bytes4(keccak256("InvalidState()"))); vault.reservePool(extraPool, extra);
        assertEq(vault.poolBucket(extraPool), 0); assertEq(vault.bucketCount(), 4);
    }

    function testLocalActivationThenCanonicalReservationsShareOneCapacityLimit() public {
        uint256 id = activatedPosition(); uint256 lp = vault.group(_bucket()).lpTokenId;
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) {
            uint256 reserved = _identity(i); vault.reservePool(_destination(i), reserved);
        }
        uint256 extra = _identity(9); bytes32 extraPool = _destination(9);
        vm.expectRevert(bytes4(keccak256("InvalidState()"))); vault.reservePool(extraPool, extra);
        assertEq(vault.bucketCount(), 4); assertEq(vault.bucketAt(0), _bucket());
        assertEq(vault.group(_bucket()).lpTokenId, lp); assertEq(vault.nftBucket(id), _bucket());
        uint256 second = _mint(bob); _activate(bob, second, 1000, 1000);
        assertEq(vault.bucketCount(), 4); assertEq(vault.nftBucket(second), _bucket());
        assertEq(vault.group(_bucket()).lpTokenId, lp);
    }

    function testNoneReservationsAreSkippedBeforeMembershipPoolAndPriceReads() public {
        for (uint256 i; i < vault.MAX_BUCKETS(); ++i) {
            uint256 bucket = _identity(i); vault.reservePool(_destination(i), bucket);
        }
        vm.mockCallRevert(address(pools), abi.encodeWithSignature("accounting(bytes32)", bytes32(0)), abi.encodePacked("None has no pool"));
        vm.warp(block.timestamp + 3601); // Both fixture feeds are also stale.
        vm.prank(address(vault)); membership.settleDust();
        vm.clearMockedCalls();
        assertEq(vault.bucketCount(), 4); assertEq(membership.totalEligible(), 0);
        assertEq(rewards.liabilities(address(t0)), 0);
    }

    function testTimeoutAndDisabledPoolDoNotReleaseOrReassignReservation() public {
        uint256 first = _identity(0); vault.reservePool(poolId, first);
        PoolConfig memory disabled = pools.get(poolId); disabled.operationsEnabled = false;
        disabled.depositsEnabled = false; pools.set(poolId, disabled);
        vm.warp(block.timestamp + 365 days);
        vault.reservePool(poolId, first); bytes32 aliasPool = _destination(20); vault.reservePool(aliasPool, first);
        uint256 other = _identity(1); vm.expectRevert(); vault.reservePool(poolId, other);
        assertEq(vault.bucketCount(), 1); _assertEmptyReservation(poolId, first);
        _assertEmptyReservation(aliasPool, first);
    }
    function testReservationUsesImportedCompanionOriginAndRetainsExactExistingMapping() public {
        // Real companion imports its source origin; authority/phase transition
        // are explicit MockAccess seams, not a complete handoff rehearsal.
        address priorVault=address(0xC0FFEE);ZZZVaultCanonical companion=vault.canonicalModule();ac.setCanonicalState(2);
        vm.prank(ac.module(Ids.CANONICAL));
        companion.canonicalImport(0,abi.encode(block.chainid,priorVault,uint256(0),uint256(0),uint256(0),uint256(0)));
        ac.setCanonicalState(0);
        uint256 canonical=vault.canonicalModule().bucketIdentity(poolId);
        uint256 guessed=uint256(keccak256(abi.encode(block.chainid,address(vault),poolId)));
        assertNotEq(canonical,guessed);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()")));vault.reservePool(poolId,guessed);
        assertEq(vault.bucketCount(),0);assertEq(vault.canonicalModule().aliasBucket(poolId),0);
        vault.reservePool(poolId,canonical);
        // Existing exact mappings remain idempotent without an identity reread.
        vm.mockCallRevert(address(vault.canonicalModule()),abi.encodeWithSignature("bucketIdentity(bytes32)",poolId),bytes("origin reader unavailable"));
        vault.reservePool(poolId,canonical);
        vm.expectRevert(bytes4(keccak256("InvalidState()")));vault.reservePool(poolId,canonical+1);
        vm.clearMockedCalls();assertEq(vault.bucketCount(),1);assertEq(vault.poolBucket(poolId),canonical);
    }
    function testUnauthorizedReservationAndBudgetValidationCannotConsumeCapacity() public {
        uint256 bucket=_identity(0);ZZZMigrationBudget budget=vault.migrationBudget();
        vm.prank(alice);vm.expectRevert(bytes4(keccak256("Unauthorized()")));vault.reservePool(poolId,bucket);
        vm.prank(alice);vm.expectRevert(bytes4(keccak256("Unauthorized()")));budget.validateReservation(poolId,bucket);
        assertEq(vault.bucketCount(),0);assertEq(vault.poolBucket(poolId),0);
        assertEq(vault.canonicalModule().aliasBucket(poolId),0);
    }
}
