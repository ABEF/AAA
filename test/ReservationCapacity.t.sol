// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Regression documenting an OPEN migration release limitation, not
/// evidence that destination capacity is safely reserved. The Vault is real;
/// venue, feeds, access and authenticated receiver authority are test fixtures.
/// Pool identity reservation does not allocate a historical registration slot.
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

    function testPoolReservationDoesNotReserveCapacityAndCannotGuaranteeLaterImport() public {
        vm.chainId(block.chainid + 1);
        uint256 limit = vault.MAX_BUCKETS();
        address receiver = ac.module(Ids.RECEIVER);
        (uint256 reservedBucket, Position memory reservedOrigin) = _origin(limit);
        bytes32 reservedPool = _destination(limit);

        // Governance reserves the intended destination while it has no custody.
        // This succeeds but does not earmark one of the registration slots.
        vault.reservePool(reservedPool, reservedBucket);
        assertEq(vault.bucketCount(), 0);
        assertEq(vault.poolBucket(reservedPool), reservedBucket);

        // Other independently authorized arrivals consume every historical slot
        // before the earlier reservation's principal arrives.
        for (uint256 i; i < limit; ++i) {
            (uint256 bucket, Position memory origin) = _origin(i);
            bytes32 destination = _destination(i);
            vault.reservePool(destination, bucket);
            _fundReceiver(receiver);
            vm.prank(receiver);
            vault.importPending(bucket, destination, origin, 2000e18, poolId, 1000, 1000);
            assertEq(uint256(vault.group(bucket).status), uint256(PositionStatus.Inbound));
        }
        assertEq(vault.bucketCount(), limit);
        assertEq(vault.totalIdle(address(t0)), limit * 1000);
        assertEq(vault.totalIdle(address(t1)), limit * 1000);

        _fundReceiver(receiver);
        vm.prank(receiver);
        vm.expectRevert(bytes4(keccak256("InvalidState()")));
        vault.importPending(reservedBucket, reservedPool, reservedOrigin, 2000e18, poolId, 1000, 1000);

        // Failure is atomic: this Vault accepts none of the arriving principal,
        // while the old pool reservation still exists and cannot create room.
        // This fixture says nothing about an external bridge's recovery ability.
        assertEq(vault.poolBucket(reservedPool), reservedBucket);
        assertEq(vault.bucketCount(), limit);
        assertEq(uint256(vault.group(reservedBucket).status), uint256(PositionStatus.None));
        assertEq(vault.bucketTotalShares(reservedBucket), 0);
        assertEq(vault.homePoolId(reservedBucket), bytes32(0));
        assertEq(t0.balanceOf(receiver), 1000); assertEq(t1.balanceOf(receiver), 1000);
        assertEq(t0.allowance(receiver, address(vault)), 1000);
        assertEq(t1.allowance(receiver, address(vault)), 1000);
        assertEq(t0.balanceOf(address(vault)), limit * 1000);
        assertEq(t1.balanceOf(address(vault)), limit * 1000);
        assertEq(vault.totalIdle(address(t0)), limit * 1000);
        assertEq(vault.totalIdle(address(t1)), limit * 1000);
    }
}
