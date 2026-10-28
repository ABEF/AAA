// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture,VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {Position} from "../src/libraries/ZZZTypes.sol";
import {MockToken} from "./mocks/Mocks.sol";

/// @dev TEST ONLY hostile token runtime retaining MockToken's storage prefix.
/// Model a changed execution policy on approval or its later zero-reset.
contract ContributionContextCallbackToken is MockToken {
    VaultLiquidityMock private venue;
    address private watched;
    bool private atReset;
    constructor() MockToken(0) {}
    function arm(VaultLiquidityMock target,address account,bool reset) external {
        venue=target;watched=account;atReset=reset;
    }
    function approve(address spender,uint256 amount) public override returns(bool) {
        bool ok=super.approve(spender,amount);
        if(msg.sender==watched && (atReset ? amount==0 : amount!=0))
            venue.setBalanceContext(bytes32(uint256(1)));
        return ok;
    }
}

/// @notice Focused share/floor fixtures. The venue is deliberately artificial;
/// actual tick depth, quote rollback and route selection have separate v4 tests.
contract ContributionBudgetIsolationTest is PooledVaultFixture {
    function testJoinLeavesIncumbentIdleAndCompoundForGuardedMaintenance() public {
        venue.setSpendBps(9800);
        uint256 first=activatedPosition();
        uint256 bucket=vault.nftBucket(first);
        Position memory before=vault.group(bucket);
        uint256 oldShares=vault.bucketTotalShares(bucket);
        venue.setFees(100,100);
        vault.collectFees(bucket,block.timestamp+100);
        venue.setSpendBps(10000);

        uint256 entrant=_mint(bob);
        _activate(bob,entrant,100,100);

        Position memory afterJoin=vault.group(bucket);
        assertEq(afterJoin.lpTokenId,before.lpTokenId,"increase the existing LP");
        assertEq(venue.balanceAmount0(),100,"only entrant token0 may be balanced");
        assertEq(venue.balanceAmount1(),100,"only entrant token1 may be balanced");
        assertEq(venue.a0(before.lpTokenId),1080);
        assertEq(venue.a1(before.lpTokenId),1080);
        assertEq(afterJoin.idle0,25,"old idle20 plus old compound5 stay attributed");
        assertEq(afterJoin.idle1,25);
        assertEq(vault.sharesOf(first),oldShares);
        assertEq(vault.sharesOf(entrant),oldShares*200/2010,"old compound stays in share price");
        assertEq(rewards.claimable(first,address(t0)),90);
        assertEq(rewards.claimable(entrant,address(t0)),0,"no past fee rights");
        assertEq(t0.allowance(address(vault),address(venue)),0);
        assertEq(t1.allowance(address(vault),address(venue)),0);

        // The retained assets are usable later; there is no sweep or new share
        // issuance. Standalone compounding keeps its independent cooldown.
        uint256 totalShares=vault.bucketTotalShares(bucket);
        policy.setNeed(false);
        vm.warp(block.timestamp+1 hours);
        compounder.compound(bucket,1,block.timestamp+100);
        assertEq(vault.group(bucket).idle0+vault.group(bucket).idle1,0);
        assertEq(venue.a0(before.lpTokenId),1105);
        assertEq(venue.a1(before.lpTokenId),1105);
        assertEq(vault.bucketTotalShares(bucket),totalShares);
    }

    function testIncumbentIdleCannotMaskAnUnderdeployedEntrant() public {
        venue.setSpendBps(9800);
        uint256 first=activatedPosition();
        uint256 bucket=vault.nftBucket(first);
        Position memory before=vault.group(bucket);
        uint256 oldShares=vault.bucketTotalShares(bucket);
        uint256 entrant=_mint(bob);
        venue.setSpendBps(9700);

        // Only96 of this100 becomes LP. Deploying the old40 idle as well
        // would incorrectly hide that failure behind a larger physical LP delta.
        vm.prank(bob);vm.expectRevert(bytes4(keccak256("Slippage()")));
        vault.activate(entrant,poolId,50,50,1,block.timestamp+100);

        assertEq(vault.nftBucket(entrant),0);
        assertEq(vault.sharesOf(entrant),0);
        assertEq(vault.bucketTotalShares(bucket),oldShares);
        assertEq(vault.group(bucket).idle0,before.idle0);
        assertEq(vault.group(bucket).idle1,before.idle1);
        assertEq(venue.a0(before.lpTokenId),980);
        assertEq(venue.a1(before.lpTokenId),980);
        assertEq(t0.balanceOf(bob),100000);
        assertEq(t1.balanceOf(bob),100000);
        assertFalse(membership.eligible(entrant));
    }

    function testIncumbentCompoundCannotMaskAnUnderdeployedEntrant() public {
        uint256 first=activatedPosition();
        uint256 bucket=vault.nftBucket(first);
        uint256 oldShares=vault.bucketTotalShares(bucket);
        venue.setFees(1000,1000);
        vault.collectFees(bucket,block.timestamp+100);
        assertEq(fees.compoundBalance(bucket,address(t0)),50);
        uint256 entrant=_mint(bob);
        venue.setSpendBps(9700);

        vm.prank(bob);vm.expectRevert(bytes4(keccak256("Slippage()")));
        vault.activate(entrant,poolId,50,50,1,block.timestamp+100);

        assertEq(vault.nftBucket(entrant),0);
        assertEq(vault.bucketTotalShares(bucket),oldShares);
        assertEq(fees.compoundBalance(bucket,address(t0)),50,"failed join rolls back reserve release");
        assertEq(fees.compoundBalance(bucket,address(t1)),50);
        assertEq(rewards.claimable(first,address(t0)),900);
        assertEq(rewards.claimable(entrant,address(t0)),0);
        assertFalse(membership.eligible(entrant));
    }

    function testOneContributionSwapCannotSpendIncumbentIdle() public {
        venue.setSpendBps(9800);
        uint256 first=activatedPosition();
        uint256 bucket=vault.nftBucket(first);
        uint256 entrant=_mint(bob);
        venue.setSpendBps(10000);
        policy.setSwapAmount(51);

        // The bucket has70 of token0 after the deposit; the entrant owns only50
        // of that execution budget. A plan for51 must not borrow old principal.
        vm.prank(bob);vm.expectRevert(bytes("entrant budget"));
        vault.activate(entrant,poolId,50,50,1,block.timestamp+100);
        assertEq(vault.group(bucket).idle0,20);

        policy.setSwapAmount(5);
        _activate(bob,entrant,50,50);
        assertEq(venue.balanceAmount0(),50);
        assertEq(venue.balanceAmount1(),50);
        assertEq(vault.group(bucket).idle0,20);
        assertEq(vault.group(bucket).idle1,20);
        assertEq(vault.contributionUSD(entrant),100e18);
    }

    function testRawPrefundCannotBackAnIncorrectBalancerReturn() public {
        uint256 entrant=_mint(bob);
        t0.mint(address(vault),777);
        venue.setBalanceReportExtra0(1);

        // The fake venue reports one extra unit without transferring it. A
        // backing-only check could incorrectly consume the pre-existing777.
        vm.prank(bob);vm.expectRevert(bytes4(keccak256("InvalidState()")));
        vault.activate(entrant,poolId,50,50,1,block.timestamp+100);

        assertEq(t0.balanceOf(address(vault)),777);
        assertEq(vault.totalIdle(address(t0)),0);
        assertEq(vault.nftBucket(entrant),0);
        assertEq(vault.sharesOf(entrant),0);
        assertFalse(membership.eligible(entrant));
    }

    function testCompleteBalancingContextCoversApprovalAndResetCallbacks() public {
        uint256 entrant=_mint(bob);
        ContributionContextCallbackToken implementation=new ContributionContextCallbackToken();
        vm.etch(address(t0),address(implementation).code);
        for(uint256 mode;mode<2;++mode){
            ContributionContextCallbackToken(address(t0)).arm(venue,address(vault),mode==1);
            vm.prank(bob);vm.expectRevert(bytes4(keccak256("InvalidState()")));
            vault.activate(entrant,poolId,50,50,1,block.timestamp+100);
            assertEq(venue.balanceContext(poolId),bytes32(0),"callback policy update rolled back");
            assertEq(vault.nftBucket(entrant),0);
            assertEq(vault.sharesOf(entrant),0);
            assertEq(t0.balanceOf(bob),100000);
            assertFalse(membership.eligible(entrant));
        }
    }
}
