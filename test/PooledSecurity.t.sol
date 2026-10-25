// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {PooledVaultFixture, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {MockFeed} from "./mocks/Mocks.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @dev Deliberately impaired accounting venue, not a deployed Uniswap dependency.
contract ImpairedPooledVenue is VaultLiquidityMock {
    constructor(address token0,address token1) VaultLiquidityMock(token0,token1) {}
    function impair(uint256 tokenId) external { a0[tokenId]=0; a1[tokenId]=0; }
    function markPrincipal(uint256 tokenId,uint256 amount0,uint256 amount1) external { a0[tokenId]=amount0; a1[tokenId]=amount1; }
}

/// @notice Real Vault/Fees/Rewards/NFT/Membership security integration with a mock LP venue.
contract PooledSecurityTest is PooledVaultFixture {
    function testCorrectCanonicalPreReservationCanActivateAndEnumeratesOnce() public {
        uint256 bucket=uint256(keccak256(abi.encode(block.chainid,address(vault),poolId)));
        vault.reservePool(poolId,bucket);
        assertEq(vault.bucketCount(),1); // Reservation already owns its permanent capacity slot.
        uint256 first=activatedPosition();uint256 second=_mint(bob);_activate(bob,second,1000,1000);
        assertEq(vault.nftBucket(first),bucket);assertEq(vault.nftBucket(second),bucket);
        assertEq(vault.bucketCount(),1);assertEq(vault.bucketAt(0),bucket);assertEq(venue.next(),2);
    }

    function testReservationCannotReassignOccupiedPool() public {
        uint256 id=activatedPosition();uint256 bucket=vault.nftBucket(id);
        uint256 lp=vault.group(bucket).lpTokenId;
        vm.expectRevert();vault.reservePool(poolId,bucket+1);
        assertEq(vault.poolBucket(poolId),bucket);assertEq(vault.group(bucket).lpTokenId,lp);
        assertEq(vault.bucketCount(),1);
    }

    function testMismatchedReservationCannotCreateAnotherCanonicalGroup() public {
        uint256 bucket=uint256(keccak256(abi.encode(block.chainid,address(vault),poolId)));
        vault.reservePool(poolId,bucket+1);
        uint256 id=_mint(alice);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        assertEq(t0.balanceOf(alice),100000);assertEq(vault.bucketCount(),1); // Failed activation cannot release the reservation.
        assertEq(vault.sharesOf(id),0);assertEq(vault.nftBucket(id),0);
        assertEq(uint256(vault.nftStatus(id)),uint256(PositionStatus.Dormant));
    }

    function testOrdinaryHolderCannotReserveOrReassignPools() public {
        vm.prank(alice);vm.expectRevert();vault.reservePool(poolId,123);
        assertEq(vault.poolBucket(poolId),0);
    }

    function testSubTwentyHistoricalFeeDustBelongsOnlyToIncumbents() public {
        uint256 first=activatedPosition();uint256 second=_mint(bob);
        uint256 bucket=vault.nftBucket(first);
        venue.setFees(19,0);
        _activate(bob,second,1000,1000);
        assertEq(rewards.claimable(first,address(t0)),19);
        assertEq(rewards.claimable(second,address(t0)),0);
        assertEq(fees.dust(bucket,address(t0)),0);
        venue.setFees(100,0);vault.collectFees(bucket,block.timestamp+100);
        assertEq(rewards.claimable(first,address(t0)),64);
        assertEq(rewards.claimable(second,address(t0)),45);
        vm.prank(bob);assertEq(rewards.claim(second,address(t0)),45);
        vm.prank(alice);assertEq(rewards.claim(first,address(t0)),64);
        assertEq(rewards.liabilities(address(t0)),0);
    }

    function testNFTTransferPreservesEarnedOwnerFeesAndPermitsOnlyNewOwnerTopUp() public {
        uint256 id=activatedPosition();uint256 bucket=vault.nftBucket(id);uint256 oldShares=vault.sharesOf(id);
        venue.setFees(100,100);vault.collectFees(bucket,block.timestamp+100);
        vm.prank(alice);nft.transferFrom(alice,bob,id);
        vm.prank(alice);vm.expectRevert();rewards.claim(id,address(t0));
        vm.prank(alice);vm.expectRevert();vault.increase(id,100,100,1,block.timestamp+100);
        vm.prank(bob);vault.increase(id,100,100,1,block.timestamp+100);
        assertGt(vault.sharesOf(id),oldShares);assertEq(vault.nftBucket(id),bucket);
        assertEq(vault.bucketCount(),1);assertEq(venue.next(),2);
        vm.prank(bob);assertEq(rewards.claim(id,address(t0)),90);
        assertEq(vault.contributionUSD(id),2200e18);assertTrue(membership.eligible(id));
        assertEq(membership.totalEligible(),1);assertEq(nft.ownerOf(id),bob);
    }

    function testFuzzTopUpCannotRewriteEitherOwnersPreviouslyEarnedFees(uint64 rawFees,uint16 rawTopUp,uint16 rawOther) public {
        uint256 first=activatedPosition();uint256 second=_mint(bob);
        uint256 other=bound(uint256(rawOther),100,20000);_activate(bob,second,other,other);
        uint256 bucket=vault.nftBucket(first);uint256 oldLp=vault.group(bucket).lpTokenId;
        uint256 gross=bound(uint256(rawFees),1,1e6)*20;
        venue.setFees(gross,0);vault.collectFees(bucket,block.timestamp+100);
        uint256 earnedFirst=rewards.claimable(first,address(t0));uint256 earnedSecond=rewards.claimable(second,address(t0));
        // Each zero-decimal fixture token is $1; both sides together must meet
        // the existing $5 growth floor. $5 itself is covered by native Entry.
        uint256 secondShares=vault.sharesOf(second);uint256 topUp=bound(uint256(rawTopUp),3,30000);
        vm.prank(alice);vault.increase(first,topUp,topUp,1,block.timestamp+100);
        assertEq(rewards.claimable(first,address(t0)),earnedFirst);
        assertEq(rewards.claimable(second,address(t0)),earnedSecond);
        assertEq(vault.sharesOf(second),secondShares);assertEq(vault.group(bucket).lpTokenId,oldLp);
        assertEq(vault.bucketCount(),1);assertEq(venue.next(),2);
        vm.prank(alice);assertEq(rewards.claim(first,address(t0)),earnedFirst);
        vm.prank(bob);assertEq(rewards.claim(second,address(t0)),earnedSecond);
        assertGe(t0.balanceOf(address(rewards)),rewards.liabilities(address(t0)));
    }

    function testIncumbentIdleCannotSatisfyNewNFTDeployedMinimum() public {
        venue.setSpendBps(9900);
        uint256 first=activatedPosition();uint256 second=_mint(bob);uint256 bucket=vault.nftBucket(first);
        Position memory beforeState=vault.group(bucket);uint256 oldShares=vault.bucketTotalShares(bucket);
        assertEq(beforeState.idle0+beforeState.idle1,20);
        // $100 supplied, but the 99% venue deploys less than $99 of marginal
        // entrant LP even though it also deploys some incumbents' idle assets.
        vm.prank(bob);vm.expectRevert();vault.activate(second,poolId,50,50,1,block.timestamp+100);
        assertEq(vault.nftBucket(second),0);assertEq(vault.sharesOf(second),0);
        assertEq(vault.bucketTotalShares(bucket),oldShares);assertEq(t0.balanceOf(bob),100000);
        assertEq(vault.group(bucket).idle0,beforeState.idle0);assertEq(vault.group(bucket).lpTokenId,beforeState.lpTokenId);
    }

    function testUnattributedDonationsCannotDiluteIncumbentsOrInflateEntryPrice() public {
        uint256 first=activatedPosition();uint256 second=_mint(bob);
        uint256 incumbentShares=vault.sharesOf(first);
        t0.mint(address(vault),1e12);t1.mint(address(vault),1e12);
        _activate(bob,second,1000,1000);
        assertEq(vault.sharesOf(first),incumbentShares);assertEq(vault.sharesOf(second),incumbentShares);
        uint256 bucket=vault.nftBucket(first);Position memory p=vault.group(bucket);
        assertEq(venue.a0(p.lpTokenId)+p.idle0,2000);
        assertEq(t0.balanceOf(address(vault))-vault.totalIdle(address(t0)),1e12);
    }

    function testOutstandingSharesWithZeroNAVCannotBeRecapitalizedByStealingNewDeposit() public {
        ImpairedPooledVenue impaired=new ImpairedPooledVenue(address(t0),address(t1));
        venue=impaired;ac.bind(Ids.LIQUIDITY,address(impaired));impaired.setSpendBps(10000);
        uint256 first=activatedPosition();uint256 second=_mint(bob);uint256 bucket=vault.nftBucket(first);
        impaired.impair(vault.group(bucket).lpTokenId);
        vm.prank(bob);vm.expectRevert();vault.activate(second,poolId,1000,1000,1,block.timestamp+100);
        assertEq(t0.balanceOf(bob),100000);assertEq(vault.sharesOf(second),0);
        assertGt(vault.bucketTotalShares(bucket),0);assertEq(vault.bucketCount(),1);
    }

    function testEntryAfterDrawdownUsesCurrentNAVRatherThanHistoricalContribution() public {
        ImpairedPooledVenue impaired=new ImpairedPooledVenue(address(t0),address(t1));
        venue=impaired;ac.bind(Ids.LIQUIDITY,address(impaired));impaired.setSpendBps(10000);
        uint256 first=activatedPosition();uint256 bucket=vault.nftBucket(first);
        uint256 incumbent=vault.sharesOf(first);uint256 second=_mint(bob);
        impaired.markPrincipal(vault.group(bucket).lpTokenId,500,500);
        // Incumbents now own $1,000 of measured principal. A new $2,000
        // contribution receives twice their shares, while collective membership stays equal.
        _activate(bob,second,1000,1000);
        assertEq(vault.sharesOf(first),incumbent);assertEq(vault.sharesOf(second),incumbent*2);
        assertEq(vault.contributionUSD(first),2000e18);assertEq(vault.contributionUSD(second),2000e18);
        assertTrue(membership.eligible(first));assertTrue(membership.eligible(second));assertEq(membership.totalEligible(),2);
        venue.setFees(1000,0);vault.collectFees(bucket,block.timestamp+100);
        assertEq(rewards.claimable(first,address(t0)),316);
        assertEq(rewards.claimable(second,address(t0)),583);
    }

    function testUnequalLPSharesKeepEqualCollectiveMembership() public {
        uint256 first=activatedPosition();uint256 second=_mint(bob);_activate(bob,second,2000,2000);
        uint256 bucket=vault.nftBucket(first);
        assertEq(vault.sharesOf(second),vault.sharesOf(first)*2);
        assertEq(membership.totalEligible(),2);
        venue.setFees(6000,0);vault.collectFees(bucket,block.timestamp+100);
        // Owner allocation is 1,600/3,200 by LP shares; collective is 300 each.
        assertEq(rewards.claimable(first,address(t0)),1900);
        assertEq(rewards.claimable(second,address(t0)),3500);
        vm.prank(alice);assertEq(rewards.claim(first,address(t0)),1900);
        vm.prank(bob);assertEq(rewards.claim(second,address(t0)),3500);
        vm.prank(alice);vault.increase(first,1000,1000,1,block.timestamp+100);
        assertEq(membership.totalEligible(),2);
        uint256 dormant=_mint(alice);assertFalse(membership.eligible(dormant));
        assertEq(membership.totalEligible(),2);
    }

    function testShareCapFailureRollsBackCustodyAndLeavesPaidNFTDormant() public {
        PoolConfig memory c=pools.get(poolId);c.maxPositionUSD=type(uint256).max;pools.set(poolId,c);
        MockFeed veryHigh=new MockFeed(8,1e26);
        oracle.setTestFeed(address(t0),address(veryHigh),3600);oracle.setTestFeed(address(t1),address(veryHigh),3600);
        uint256 id=_mint(alice);uint256 paid=treasury.balance;
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        assertEq(vault.sharesOf(id),0);assertEq(vault.bucketCount(),0);assertEq(vault.poolBucket(poolId),0);
        assertEq(t0.balanceOf(alice),100000);assertEq(venue.next(),1);assertEq(treasury.balance,paid);
        assertEq(uint256(vault.nftStatus(id)),uint256(PositionStatus.Dormant));assertEq(membership.totalEligible(),0);
    }
}
