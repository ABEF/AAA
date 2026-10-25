// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {AtomicActivationIntegrationTest} from "./AtomicActivationIntegration.t.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";

/// @notice Real Entry/Pricing/Registry/Vault ledgers, deterministic local LP and
/// conversion fixtures. Not live venue, oracle or production qualification.
contract EntryReviewPolicyTest is AtomicActivationIntegrationTest {
    function _review(uint256 id, bool grow) private view returns (ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id,poolId,address(stable),grow ? 5e6 : 100e6,
            routeId,1,1,block.timestamp+100,grow);
    }
    function _assertNotSpent(uint256 id,uint256 sourceBefore) private view {
        assertEq(stable.balanceOf(alice),sourceBefore);
        assertEq(stable.balanceOf(address(router)),0);
        assertEq(stable.balanceOf(address(entry)),0);
        assertEq(t0.balanceOf(address(entry)),0);
        assertEq(stable.allowance(address(entry),address(router)),0);
        assertEq(t0.allowance(address(entry),address(vault)),0);
        assertEq(vault.sharesOf(id),0);assertEq(vault.nftBucket(id),0);
        assertEq(vault.contributionUSD(id),0);assertEq(vault.bucketCount(),0);
        assertFalse(membership.eligible(id));assertEq(nft.royaltyRewards().weightOf(id),0);
        assertFalse(oracle.contributionPricing().active());assertEq(nft.ownerOf(id),alice);
    }
    function testReviewVersionsAreExplicit() public realIntegration {
        assertEq(entry.REVIEW_POLICY_VERSION(),1);
        assertEq(oracle.contributionPricing().ENTRY_REVIEW_VERSION(),1);
    }
    function testReviewedMaximumRejectsRaisedGovernedCapBeforeSourcePullAndSwap() public realIntegration {
        uint256 id=_mint(alice);uint256 balance=stable.balanceOf(alice);
        uint256 allowance=stable.allowance(alice,address(entry));
        ZZZActivationEntry.Request memory request=_review(id,false);
        // Simulate a signed 1% review waiting while governance selects 2%.
        vault.migrationBudget().setLossLimits(200,300);
        vm.mockCallRevert(address(stable),abi.encodeWithSignature("transferFrom(address,address,uint256)",
            alice,address(entry),100e6),abi.encodeWithSignature("PullWasReached()"));
        vm.prank(alice);vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        entry.executeReviewed(request,100);
        assertEq(stable.allowance(alice,address(entry)),allowance);_assertNotSpent(id,balance);
        vm.clearMockedCalls();
        // The exact old signed transaction can work after policy tightens back.
        vault.migrationBudget().setLossLimits(100,300);
        vm.prank(alice);entry.executeReviewed(request,100);
        assertEq(vault.sharesOf(id),99e18);assertTrue(membership.eligible(id));
    }
    function testSignedMaximumAllowsTighterGovernedPolicyButNeverWidensActualFloor() public realIntegration {
        uint256 id=_mint(alice);uint256 balance=stable.balanceOf(alice);
        router.setOutputBps(9899); // 1.01%, below the captured 1% floor.
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(_review(id,false),200);
        _assertNotSpent(id,balance);
        router.setOutputBps(9900);
        vm.prank(alice);entry.executeReviewed(_review(id,false),200);
        assertEq(vault.sharesOf(id),99e18);assertEq(vault.contributionUSD(id),100e18);
    }
    function testZeroMaximumRequiresZeroGovernedCapAndLosslessActualDeployment() public realIntegration {
        uint256 id=_mint(alice);uint256 balance=stable.balanceOf(alice);
        vm.prank(alice);vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        entry.executeReviewed(_review(id,false),0);_assertNotSpent(id,balance);
        vault.migrationBudget().setLossLimits(0,300);
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(_review(id,false),0);
        _assertNotSpent(id,balance);
        router.setOutputBps(10000);
        vm.prank(alice);entry.executeReviewed(_review(id,false),0);
        assertEq(vault.sharesOf(id),100e18);assertFalse(oracle.contributionPricing().active());
    }
    function testMaximumAboveTenPercentAndLegacySelectorsFailClosed() public realIntegration {
        uint256 id=_mint(alice);uint256 balance=stable.balanceOf(alice);
        ZZZContributionPricing pricing=oracle.contributionPricing();
        vm.prank(alice);vm.expectRevert(ZZZContributionPricing.InvalidAmount.selector);
        entry.executeReviewed(_review(id,false),1001);_assertNotSpent(id,balance);
        // Removed historical selectors must fail with their exact old calldata,
        // including for the formerly authorized Entry caller. No ABI shim needed.
        bytes memory retired=abi.encodeWithSignature(
            "execute((uint256,bytes32,address,uint256,bytes32,uint256,uint128,uint256,bool))",_review(id,false));
        vm.prank(alice);(bool accepted,) = address(entry).call(retired);
        assertFalse(accepted);_assertNotSpent(id,balance);
        vm.prank(address(entry));(accepted,) = address(pricing).call(abi.encodeWithSignature(
            "beginEntry(uint256,bytes32,address,uint256)",id,poolId,address(stable),uint256(100e6)));
        assertFalse(accepted);
        _assertNotSpent(id,balance);
    }
    function testMalformedMaximumABIRevertsWithoutSpendingPrefundsOrUserAllowance() public realIntegration {
        uint256 id=_mint(alice);uint256 balance=stable.balanceOf(alice);
        uint256 allowance=stable.allowance(alice,address(entry));
        stable.mint(address(entry),17e6);t0.mint(address(entry),23e18);
        bytes memory data=abi.encodeWithSelector(entry.executeReviewed.selector,_review(id,false),uint256(65536+100));
        vm.prank(alice);(bool ok,)=address(entry).call(data);assertFalse(ok);
        assertEq(stable.balanceOf(alice),balance);assertEq(stable.allowance(alice,address(entry)),allowance);
        assertEq(stable.balanceOf(address(entry)),17e6);assertEq(t0.balanceOf(address(entry)),23e18);
        assertEq(vault.sharesOf(id),0);assertFalse(membership.eligible(id));
        assertFalse(oracle.contributionPricing().active());assertEq(vault.bucketCount(),0);
    }
    function testTenPercentMaximumCannotOverrideStrongerPhysicalVenueMinimum() public realIntegration {
        uint256 id=_mint(alice);uint256 balance=stable.balanceOf(alice);
        vault.migrationBudget().setLossLimits(1000,300);
        router.setOutputBps(9800);
        // The LP venue remains at 1%; a signed 10% maximum cannot relax it.
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(_review(id,false),1000);
        _assertNotSpent(id,balance);
        router.setOutputBps(9900);
        vm.prank(alice);entry.executeReviewed(_review(id,false),1000);
        assertEq(vault.sharesOf(id),99e18);
    }
    function testGrowthReviewRejectsWideningAndPreservesExistingSharesAndClaims() public realIntegration {
        uint256 id=_mint(alice);
        vm.prank(alice);entry.executeReviewed(_review(id,false),100);
        uint256 shares=vault.sharesOf(id);uint256 bucket=vault.nftBucket(id);
        uint256 lp=vault.group(bucket).lpTokenId;uint256 deployed=venue.a0(lp);
        uint256 balance=stable.balanceOf(alice);uint256 receiverBalance=t0.balanceOf(address(vault));
        vault.migrationBudget().setLossLimits(200,300);
        vm.prank(alice);vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        entry.executeReviewed(_review(id,true),100);
        assertEq(vault.sharesOf(id),shares);assertEq(venue.a0(lp),deployed);
        assertEq(stable.balanceOf(alice),balance);assertEq(t0.balanceOf(address(vault)),receiverBalance);
        assertEq(vault.contributionUSD(id),100e18);assertTrue(membership.eligible(id));
        assertEq(nft.royaltyRewards().weightOf(id),1);assertFalse(oracle.contributionPricing().active());
        vault.migrationBudget().setLossLimits(100,300);
        vm.prank(alice);entry.executeReviewed(_review(id,true),100);
        assertGt(vault.sharesOf(id),shares);assertEq(vault.contributionUSD(id),105e18);
        assertEq(venue.a0(lp)-deployed,4.95e18);
    }
}
