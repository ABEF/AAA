// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Ids, PoolConfig, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Real Vault/NFT/Membership/Fees/Rewards accounting with two distinct
/// pools and the existing local venue mock. No public pool/bridge is exercised.
contract GlobalMembershipDustTest is PooledVaultFixture {
    function _secondPool() private returns (bytes32 other) {
        PoolConfig memory config = pools.get(poolId);
        config.key.fee = 500;
        other = keccak256(abi.encode(config.key));
        pools.set(other, config);
    }

    function _activateSecond(uint256 id, bytes32 other) private {
        vm.prank(bob);
        vault.activate(id, other, 1000, 1000, 1, block.timestamp + 100);
    }

    function _selectSecondAndDisableOldContributions() private returns(bytes32 other) {
        other=_secondPool();
        PoolConfig memory old=pools.get(poolId);old.depositsEnabled=false;pools.set(poolId,old);
    }
    function _breakHistoricalAccounting() private returns(bytes memory failure) {
        failure=abi.encodeWithSignature("HistoricalVenueUnavailable()");
        vm.mockCallRevert(address(pools),abi.encodeWithSignature("accounting(bytes32)",poolId),failure);
        // The former dust barrier performed this exact live read even with no
        // dust. Its admitted local currency record remains available.
        (bool ok,bytes memory returned)=address(pools).staticcall(
            abi.encodeWithSignature("accounting(bytes32)",poolId));
        assertFalse(ok);assertEq(returned,failure);
        assertEq(pools.get(poolId).key.currency0,address(t0));
        assertEq(pools.get(poolId).key.currency1,address(t1));
    }

    function testBrokenHistoricalVenueWithNoDustDoesNotBlockHealthyNewEntry() public {
        uint256 first=activatedPosition();uint256 firstBucket=vault.nftBucket(first);
        uint256 shares=vault.sharesOf(first);uint256 lp=vault.group(firstBucket).lpTokenId;
        uint256 second=_mint(bob);bytes32 other=_selectSecondAndDisableOldContributions();
        assertEq(fees.dust(firstBucket,address(t0)),0);assertEq(fees.dust(firstBucket,address(t1)),0);
        _breakHistoricalAccounting();_activateSecond(second,other);
        assertEq(membership.totalEligible(),2);assertTrue(membership.eligible(second));
        assertEq(vault.sharesOf(first),shares);assertEq(vault.group(firstBucket).lpTokenId,lp);
        assertGt(vault.sharesOf(second),0);assertEq(vault.bucketCount(),2);
        assertEq(rewards.claimable(first,address(t0)),0);assertEq(rewards.claimable(second,address(t0)),0);
        assertEq(fees.accounted(address(t0)),0);assertEq(rewards.liabilities(address(t0)),0);
    }

    function testBrokenHistoricalVenueStillSettlesFundedDustOnlyToIncumbents() public {
        uint256 first=activatedPosition();uint256 firstBucket=vault.nftBucket(first);
        venue.setFees(19,19);vault.collectFees(firstBucket,block.timestamp+100);
        uint256 second=_mint(bob);bytes32 other=_selectSecondAndDisableOldContributions();
        _breakHistoricalAccounting();_activateSecond(second,other);
        assertEq(membership.totalEligible(),2);assertTrue(membership.eligible(second));
        assertEq(fees.dust(firstBucket,address(t0)),0);assertEq(fees.dust(firstBucket,address(t1)),0);
        assertEq(rewards.claimable(first,address(t0)),19);assertEq(rewards.claimable(first,address(t1)),19);
        assertEq(rewards.claimable(second,address(t0)),0);assertEq(rewards.claimable(second,address(t1)),0);
        assertEq(rewards.liabilities(address(t0)),19);assertEq(rewards.liabilities(address(t1)),19);
        assertEq(fees.accounted(address(t0)),0);assertEq(t0.balanceOf(address(rewards)),19);
        vm.prank(alice);assertEq(rewards.claim(first,address(t0)),19);
        vm.prank(alice);assertEq(rewards.claim(first,address(t1)),19);
        assertEq(rewards.liabilities(address(t0)),0);assertEq(rewards.liabilities(address(t1)),0);
    }

    function testCurrentVenueFaultStillRejectsEntryAndPreservesFundedDust() public {
        uint256 first=activatedPosition();uint256 firstBucket=vault.nftBucket(first);
        venue.setFees(19,19);vault.collectFees(firstBucket,block.timestamp+100);
        uint256 second=_mint(bob);bytes32 other=_selectSecondAndDisableOldContributions();
        bytes memory failure=abi.encodeWithSignature("CurrentVenueUnavailable()");
        vm.mockCallRevert(address(pools),abi.encodeWithSignature("accounting(bytes32)",other),failure);
        uint256 balance0=t0.balanceOf(bob);uint256 balance1=t1.balanceOf(bob);
        vm.prank(bob);vm.expectRevert(failure);vault.activate(second,other,1000,1000,1,block.timestamp+100);
        assertEq(vault.bucketCount(),1);assertEq(vault.nftBucket(second),0);assertEq(vault.sharesOf(second),0);
        assertFalse(membership.eligible(second));assertEq(membership.totalEligible(),1);
        assertEq(fees.dust(firstBucket,address(t0)),19);assertEq(fees.dust(firstBucket,address(t1)),19);
        assertEq(fees.accounted(address(t0)),19);assertEq(t0.balanceOf(address(fees)),19);
        assertEq(rewards.liabilities(address(t0)),0);assertEq(t0.balanceOf(bob),balance0);assertEq(t1.balanceOf(bob),balance1);
    }

    function testHistoricalDustPaymentFailureRejectsEntryWithoutLosingOldRights() public {
        uint256 first=activatedPosition();uint256 firstBucket=vault.nftBucket(first);
        venue.setFees(19,0);vault.collectFees(firstBucket,block.timestamp+100);
        uint256 second=_mint(bob);bytes32 other=_selectSecondAndDisableOldContributions();
        _breakHistoricalAccounting();
        bytes memory failure=abi.encodeWithSignature("HistoricalDustPaymentUnavailable()");
        vm.mockCallRevert(address(t0),abi.encodeWithSignature("transferFrom(address,address,uint256)",
            address(fees),address(rewards),uint256(19)),failure);
        vm.prank(bob);vm.expectRevert(failure);vault.activate(second,other,1000,1000,1,block.timestamp+100);
        assertEq(vault.nftBucket(second),0);assertFalse(membership.eligible(second));assertEq(membership.totalEligible(),1);
        assertEq(fees.dust(firstBucket,address(t0)),19);assertEq(fees.accounted(address(t0)),19);
        assertEq(t0.balanceOf(address(fees)),19);assertEq(rewards.liabilities(address(t0)),0);
    }

    function testFundedDustWithoutCreatorInboxCannotRewardNewMemberInOtherPool() public {
        uint256 first = activatedPosition(); uint256 firstBucket = vault.nftBucket(first);
        venue.setFees(19, 19); vault.collectFees(firstBucket, block.timestamp + 100);
        assertEq(fees.dust(firstBucket, address(t0)), 19);
        assertEq(fees.dust(firstBucket, address(t1)), 19); assertEq(rewards.claimable(first, address(t0)), 0);
        uint256 second = _mint(bob); _activateSecond(second, _secondPool());
        assertTrue(vault.nftBucket(second) != firstBucket); assertEq(vault.bucketCount(), 2);
        assertEq(membership.totalEligible(), 2);
        assertEq(fees.dust(firstBucket, address(t0)), 0); assertEq(fees.dust(firstBucket, address(t1)), 0);
        assertEq(rewards.claimable(first, address(t0)), 19); assertEq(rewards.claimable(first, address(t1)), 19);
        assertEq(rewards.claimable(second, address(t0)), 0); assertEq(rewards.claimable(second, address(t1)), 0);
        // Freshly collected revenue uses CURRENT equal collective membership.
        // It never combines the earlier funded nineteen units with a new entry.
        venue.setFees(20, 20); vault.collectFees(firstBucket, block.timestamp + 100);
        assertEq(rewards.claimable(first, address(t0)), 36); assertEq(rewards.claimable(first, address(t1)), 36);
        assertEq(rewards.claimable(second, address(t0)), 1); assertEq(rewards.claimable(second, address(t1)), 1);
        assertEq(fees.compoundBalance(firstBucket, address(t0)), 1); assertEq(fees.buybackBalance(address(t0)), 1);
        assertEq(fees.accounted(address(t0)), 2); assertEq(rewards.liabilities(address(t0)), 37);
    }

    function testRevertedEntryRollsBackGlobalDustSettlementAndMembershipAtomically() public {
        uint256 first = activatedPosition(); uint256 bucket = vault.nftBucket(first);
        venue.setFees(19, 19); vault.collectFees(bucket, block.timestamp + 100);
        uint256 second = _mint(bob); bytes32 other = _secondPool(); venue.setFail(true);
        vm.prank(bob); vm.expectRevert(); vault.activate(second, other, 1000, 1000, 1, block.timestamp + 100);
        assertEq(vault.bucketCount(), 1); assertEq(vault.nftBucket(second), 0); assertEq(vault.sharesOf(second), 0);
        assertFalse(membership.eligible(second)); assertEq(membership.totalEligible(), 1);
        assertEq(fees.dust(bucket, address(t0)), 19); assertEq(fees.accounted(address(t0)), 19);
        assertEq(rewards.liabilities(address(t0)), 0); assertEq(rewards.claimable(first, address(t0)), 0);
        assertEq(t0.balanceOf(address(fees)), 19); assertEq(t0.balanceOf(address(rewards)), 0);
        venue.setFail(false); _activateSecond(second, other);
        assertEq(fees.dust(bucket, address(t0)), 0); assertEq(rewards.claimable(first, address(t0)), 19);
        assertEq(rewards.claimable(second, address(t0)), 0);
    }

    function testGlobalSettlementOnlyVaultAndDustFlushOnlyAuthorizedModules() public {
        uint256 first = activatedPosition(); uint256 bucket = vault.nftBucket(first);
        vm.expectRevert(); membership.settleDust();
        vm.prank(bob); vm.expectRevert(); membership.settleDust();
        vm.prank(bob); vm.expectRevert(); fees.flushDust(bucket, address(t0));
        vm.prank(address(vault)); membership.settleDust();
    }

    function testMembershipCannotFlushForeignCustodyDust() public {
        uint256 first = activatedPosition(); uint256 bucket = vault.nftBucket(first);
        venue.setFees(19, 0); vault.collectFees(bucket, block.timestamp + 100);
        vm.chainId(block.chainid + 1);
        vm.prank(address(vault)); membership.settleDust();
        assertEq(fees.dust(bucket, address(t0)), 19);
        vm.prank(address(membership)); vm.expectRevert(); fees.flushDust(bucket, address(t0));
        assertEq(fees.dust(bucket, address(t0)), 19); assertEq(rewards.liabilities(address(t0)), 0);
    }
}
