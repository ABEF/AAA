// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Real Vault admission/custody regressions. Venue, feeds, governance
/// and authenticated receiver authority are fixtures, not live bridge evidence.
contract ReservationCapacityTest is PooledVaultFixture {
    function _destination(uint256 index) private returns (bytes32 pool) {
        if (index == 0) return poolId;
        PoolConfig memory config = pools.get(poolId);
        config.key.fee = uint24(500 + index);
        pool = keccak256(abi.encode(config.key));
        pools.set(pool, config);
    }

    function _origin(uint256 index) private view returns (uint256 bucket, Position memory origin) {
        origin.homeChain = vault.canonicalChainId();
        origin.homeVault = address(uint160(0x10000 + index));
        origin.homeReceiver = address(0xABCD);
        origin.homeToken0 = address(t0);
        origin.homeToken1 = address(t1);
        origin.depositUSD = 2000e18;
        bucket = uint256(keccak256(abi.encode(origin.homeChain, origin.homeVault, poolId)));
    }

    function _fundReceiver(address receiver) private {
        t0.mint(receiver, 1000); t1.mint(receiver, 1000);
        vm.startPrank(receiver);
        t0.approve(address(vault), 1000); t1.approve(address(vault), 1000);
        vm.stopPrank();
    }

    function _assertEmptyReservation(bytes32 pool, uint256 bucket) private view {
        Position memory p = vault.group(bucket);
        assertEq(vault.poolBucket(pool), bucket);
        assertEq(uint256(p.status), uint256(PositionStatus.None));
        assertEq(p.lpTokenId, 0); assertEq(p.idle0, 0); assertEq(p.idle1, 0);
        assertEq(p.homeChain, 0); assertEq(p.homeVault, address(0));
        assertEq(vault.bucketTotalShares(bucket), 0); assertEq(vault.homePoolId(bucket), bytes32(0));
    }

    function _assertReceiverUnchanged(address receiver) private view {
        assertEq(t0.balanceOf(receiver), 1000); assertEq(t1.balanceOf(receiver), 1000);
        assertEq(t0.allowance(receiver, address(vault)), 1000);
        assertEq(t1.allowance(receiver, address(vault)), 1000);
        assertEq(vault.totalIdle(address(t0)), 0); assertEq(vault.totalIdle(address(t1)), 0);
        assertEq(t0.balanceOf(address(vault)), 0); assertEq(t1.balanceOf(address(vault)), 0);
    }

    function testReservationImmediatelyOwnsPermanentCapacityWithoutCustodyOrShares() public {
        (uint256 bucket,) = _origin(0);
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
            (uint256 bucket,) = _origin(i); if (i == 0) first = bucket;
            vault.reservePool(_destination(i), bucket);
        }
        vault.reservePool(poolId, first);
        bytes32 aliasPool = _destination(20); vault.reservePool(aliasPool, first);
        vault.reservePool(aliasPool, first);
        assertEq(vault.bucketCount(), 4); assertEq(vault.bucketAt(0), first);
        _assertEmptyReservation(poolId, first); _assertEmptyReservation(aliasPool, first);
        for (uint256 i; i < vault.bucketCount(); ++i) {
            for (uint256 j = i + 1; j < vault.bucketCount(); ++j) assertTrue(vault.bucketAt(i) != vault.bucketAt(j));
        }
    }

    function testPoolReassignmentRejectsWithoutConsumingAnotherSlot() public {
        (uint256 first,) = _origin(0); (uint256 second,) = _origin(1);
        vault.reservePool(poolId, first);
        vm.expectRevert(bytes4(keccak256("InvalidState()"))); vault.reservePool(poolId, second);
        assertEq(vault.bucketCount(), 1); assertEq(vault.bucketAt(0), first);
        _assertEmptyReservation(poolId, first);
        assertEq(uint256(vault.group(second).status), uint256(PositionStatus.None));
    }

    function testInvalidIdentityAndFailedPoolValidationNeverConsumeCapacity() public {
        (uint256 bucket,) = _origin(0);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); vault.reservePool(bytes32(0), bucket);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); vault.reservePool(poolId, 0);
        // The fixture registry is permissive, so explicitly reproduce a real
        // registry's missing-pool failure before any capacity can be committed.
        vm.mockCallRevert(address(pools), abi.encodeWithSignature("get(bytes32)", poolId), abi.encodePacked("missing pool"));
        vm.expectRevert(); vault.reservePool(poolId, bucket); vm.clearMockedCalls();
        assertEq(vault.bucketCount(), 0); assertEq(vault.poolBucket(poolId), 0);
    }





    function testForeignReservationCannotBeHijackedByLocalActivation() public {
        (uint256 bucket,) = _origin(0); vault.reservePool(poolId, bucket); uint256 id = _mint(alice);
        vm.prank(alice); vm.expectRevert(); vault.activate(id, poolId, 1000, 1000, 1, block.timestamp + 100);
        assertEq(vault.bucketCount(), 1); _assertEmptyReservation(poolId, bucket);
        assertEq(vault.nftBucket(id), 0); assertEq(vault.sharesOf(id), 0);
        assertFalse(membership.eligible(id)); assertEq(t0.balanceOf(alice), 100000);
    }

    function testCanonicalActivationUsesItsReservedSlotAtFullCapacity() public {
        uint256 canonical = _bucket(); vault.reservePool(poolId, canonical);
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) {
            (uint256 remote,) = _origin(i); vault.reservePool(_destination(i), remote);
        }
        uint256 id = _mint(alice); _activate(alice, id, 1000, 1000);
        assertEq(vault.bucketCount(), 4); assertEq(vault.bucketAt(0), canonical);
        assertEq(vault.nftBucket(id), canonical); assertEq(vault.bucketTotalShares(canonical), vault.sharesOf(id));
        assertEq(membership.totalEligible(), 1); assertTrue(membership.eligible(id));
    }

    function testForeignReservationsThenLocalActivationShareOneCapacityLimit() public {
        // Reservation admission is common to local and remote identities. A real
        // first foreign import is satellite-only; do not bypass that invariant.
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) {
            (uint256 remote,) = _origin(i); vault.reservePool(_destination(i), remote);
        }
        uint256 id = activatedPosition(); assertEq(vault.bucketCount(), 4);
        assertEq(vault.nftBucket(id), _bucket()); assertEq(vault.bucketAt(3), _bucket());
        (uint256 extra,) = _origin(9); bytes32 extraPool = _destination(9);
        vm.expectRevert(); vault.reservePool(extraPool, extra);
        assertEq(vault.poolBucket(extraPool), 0); assertEq(vault.bucketCount(), 4);
    }

    function testLocalActivationThenForeignReservationsShareOneCapacityLimit() public {
        uint256 id = activatedPosition(); uint256 lp = vault.group(_bucket()).lpTokenId;
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) {
            (uint256 remote,) = _origin(i); vault.reservePool(_destination(i), remote);
        }
        (uint256 extra,) = _origin(9); bytes32 extraPool = _destination(9);
        vm.expectRevert(); vault.reservePool(extraPool, extra);
        assertEq(vault.bucketCount(), 4); assertEq(vault.bucketAt(0), _bucket());
        assertEq(vault.group(_bucket()).lpTokenId, lp); assertEq(vault.nftBucket(id), _bucket());
        uint256 second = _mint(bob); _activate(bob, second, 1000, 1000);
        assertEq(vault.bucketCount(), 4); assertEq(vault.nftBucket(second), _bucket());
        assertEq(vault.group(_bucket()).lpTokenId, lp);
    }

    function testNoneReservationsAreSkippedBeforeMembershipPoolAndPriceReads() public {
        for (uint256 i; i < vault.MAX_BUCKETS(); ++i) {
            (uint256 bucket,) = _origin(i); vault.reservePool(_destination(i), bucket);
        }
        vm.mockCallRevert(address(pools), abi.encodeWithSignature("accounting(bytes32)", bytes32(0)), abi.encodePacked("None has no pool"));
        vm.warp(block.timestamp + 3601); // Both fixture feeds are also stale.
        vm.prank(address(vault)); membership.settleDust();
        vm.clearMockedCalls();
        assertEq(vault.bucketCount(), 4); assertEq(membership.totalEligible(), 0);
        assertEq(rewards.liabilities(address(t0)), 0);
    }

    function testTimeoutAndDisabledPoolDoNotReleaseOrReassignReservation() public {
        (uint256 first,) = _origin(0); vault.reservePool(poolId, first);
        PoolConfig memory disabled = pools.get(poolId); disabled.operationsEnabled = false;
        disabled.depositsEnabled = false; pools.set(poolId, disabled);
        vm.warp(block.timestamp + 365 days);
        vault.reservePool(poolId, first); bytes32 aliasPool = _destination(20); vault.reservePool(aliasPool, first);
        (uint256 other,) = _origin(1); vm.expectRevert(); vault.reservePool(poolId, other);
        assertEq(vault.bucketCount(), 1); _assertEmptyReservation(poolId, first);
        _assertEmptyReservation(aliasPool, first);
    }
}
