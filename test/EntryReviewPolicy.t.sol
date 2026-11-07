// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZProtocolPolicy} from "../src/interfaces/IZZZProtocolPolicy.sol";
import {DirectEntryFixture} from "./AtomicActivationIntegration.t.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";

/// @dev Direct Entry3 review-boundary checks; no pre-Vault route fixture.
contract EntryReviewPolicyTest is DirectEntryFixture {
    function _reviewed(uint256 id,uint16 maximum,bool reject) private {
        bytes32 policy=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
        vm.startPrank(alice);t1.approve(address(entry),100e18);
        if(reject)vm.expectRevert();entry.executeReviewed(_request(id,false),maximum,policy);
        vm.stopPrank();
    }
    function testDirectABIIsDistinctButCapturedPolicySemanticsRemainVersionTwo() public realIntegration {
        assertEq(entry.ENTRY_ROUTING_VERSION(),3);assertEq(entry.REVIEW_POLICY_VERSION(),2);
        assertEq(oracle.contributionPricing().ENTRY_REVIEW_VERSION(),2);
    }
    function testRaisedGovernedLossCannotExceedCallerReviewBeforePull() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        vault.migrationBudget().setLossLimits(200,300);_reviewed(id,100,true);_unspent(id,before);
        vault.migrationBudget().setLossLimits(100,300);_reviewed(id,100,false);
        assertEq(vault.contributionUSD(id),100e18);_clean();
    }
    function testWiderCallerMaximumNeverWeakensCapturedPhysicalFloor() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        venue.setSpendBps(9899);_reviewed(id,200,true);_unspent(id,before);
        venue.setSpendBps(9900);_reviewed(id,200,false);
        // All100 units remain attributed:99 deployed plus1 idle. Shares price
        // net added NAV; the separate physical-deployment guard still sees99.
        uint256 bucket=vault.nftBucket(id);assertEq(vault.sharesOf(id),100e18);
        assertEq(venue.a1(vault.group(bucket).lpTokenId),99e18);assertEq(vault.group(bucket).idle1,1e18);_clean();
    }
    function testZeroCallerMaximumRequiresZeroPolicyAndLosslessDeployedInput() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        _reviewed(id,0,true);_unspent(id,before);
        vault.migrationBudget().setLossLimits(0,300);venue.setSpendBps(9999);
        _reviewed(id,0,true);_unspent(id,before);
        venue.setSpendBps(10000);_reviewed(id,0,false);assertEq(vault.sharesOf(id),100e18);_clean();
    }
    function testCallerMaximumAboveTenPercentAndStaleFingerprintReject() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);_reviewed(id,1001,true);_unspent(id,before);
        bytes32 old=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
        IZZZProtocolPolicy.EntryPolicy memory terms=IZZZProtocolPolicy(ac.protocolPolicy()).entryPolicy();
        // Changing even to the same values creates a fresh scoped revision.
        (bool ok,)=ac.protocolPolicy().call(abi.encodeWithSignature("setEntryPolicy(uint128,uint128,uint16,bytes32)",
            terms.minActivationUSD,terms.minGrowthUSD,terms.maxIdleBps,REVIEW));
        assertTrue(ok);
        vm.startPrank(alice);t1.approve(address(entry),100e18);vm.expectRevert();
        entry.executeReviewed(_request(id,false),100,old);vm.stopPrank();_unspent(id,before);
    }
    function testLegacyAndMalformedReviewSelectorsCannotActivate() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        bytes memory input=abi.encodeCall(entry.executeReviewed,(_request(id,false),uint16(100),
            IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint()));
        // uint16 is word7 of the direct static tuple and its two review fields.
        assembly("memory-safe"){mstore(add(input,260),65536)}
        vm.prank(alice);(bool ok,)=address(entry).call(input);assertFalse(ok);_unspent(id,before);
        vm.prank(address(entry));(ok,)=address(oracle.contributionPricing()).call(
            abi.encodeWithSignature("beginEntry(uint256,bytes32,address,uint256)",id,poolId,address(t1),100e18));
        assertFalse(ok);_clean();
    }
}
