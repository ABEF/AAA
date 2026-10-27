// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockFeed} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Position} from "../src/libraries/ZZZTypes.sol";

/// Real Vault/NFT/reward accounting with explicitly synthetic venue economics.
/// DynamicRange.t.sol separately verifies concentrated-liquidity amount math.
contract DynamicAccountingTest is PooledVaultFixture {
    function _value(uint256 id) private view returns(uint256 value){
        (bool available,uint256 marked)=nft.currentLPValue(id);assertTrue(available);return marked;
    }
    function _fivePercent() private returns(uint256 id,uint256 other){
        id=_mint(alice);_activate(alice,id,250,250);
        other=_mint(bob);_activate(bob,other,4750,4750);
        assertEq(vault.sharesOf(id)*20,vault.bucketTotalShares(_bucket()));
    }
    function testFivePercentTracksLossNewPhysicalLpAndAppreciation() public {
        (uint256 id,uint256 other)=_fivePercent();uint256 shares=vault.sharesOf(id);
        uint256 old=_record(id).lpTokenId;assertEq(_value(id),500e18);
        venue.setCloseLossBps(200);vault.rebalance(_bucket(),1,block.timestamp+100);
        assertEq(_value(id),490e18);assertEq(_value(other),9310e18);
        assertGt(_record(id).lpTokenId,old);assertEq(venue.a0(old)+venue.a1(old),0);
        assertEq(vault.sharesOf(id),shares);assertEq(vault.contributionUSD(id),500e18);
        // No rebalance: market marks alone change the NFT value.
        MockFeed higher=new MockFeed(8,120000000);
        oracle.setTestFeed(address(t0),address(higher),3600);oracle.setTestFeed(address(t1),address(higher),3600);
        assertEq(_value(id),588e18);assertEq(_value(other),11172e18);
        venue.setCloseLossBps(0);old=_record(id).lpTokenId;
        vault.rebalance(_bucket(),1,block.timestamp+100);
        assertGt(_record(id).lpTokenId,old);assertEq(_value(id),588e18);assertEq(vault.sharesOf(id),shares);
    }
    function testCompoundAndLaterContributionKeepIncumbentValueAndEarnedRights() public {
        (uint256 id,uint256 other)=_fivePercent();uint256 oldShare=vault.sharesOf(id);
        venue.setFees(1000,0);vault.collectFees(_bucket(),block.timestamp+100);
        // 80% follows 5%/95% LP; 10% splits equally. 5% compound is NAV,
        // while individual/collective claims and buyback are excluded from NAV.
        assertEq(rewards.claimable(id,address(t0)),90);assertEq(rewards.claimable(other,address(t0)),810);
        assertEq(_value(id),5025e17);uint256 valueBefore=_value(id);
        policy.setNeed(false); // Eligible rebalances have priority over compound.
        vm.warp(block.timestamp+1 hours); // Independent default compound cadence.
        compounder.compound(_bucket(),1,block.timestamp+100);
        assertEq(vault.sharesOf(id),oldShare);assertEq(_value(id),valueBefore);
        uint256 supply=vault.bucketTotalShares(_bucket());
        uint256 entrant=_mint(alice);_activate(alice,entrant,500,500);
        uint256 expected=supply*1000e18/10050e18;
        assertEq(vault.sharesOf(entrant),expected);assertEq(rewards.claimable(entrant,address(t0)),0);
        assertApproxEqAbs(_value(id),valueBefore,1);assertEq(rewards.claimable(id,address(t0)),90);
        // A top-up similarly buys current NAV shares, never past receipts.
        supply=vault.bucketTotalShares(_bucket());uint256 beforeShares=vault.sharesOf(id);
        vm.prank(alice);vault.increase(id,500,500,1,block.timestamp+100);
        assertEq(vault.sharesOf(id)-beforeShares,supply*1000e18/11050e18);
        assertEq(rewards.claimable(id,address(t0)),90);
    }
    function testRepeatedReplacementTransferRoyaltiesAndFailedRebalanceRollback() public {
        (uint256 id,)=_fivePercent();venue.setFees(1000,0);vault.collectFees(_bucket(),block.timestamp+100);
        (bool ok,)=address(nft.royaltyRewards()).call{value:1 ether}("");require(ok);
        uint256 royalty=nft.royaltyRewards().claimable(id,address(0));uint256 share=vault.sharesOf(id);
        for(uint256 i;i<4;++i){
            uint256 old=_record(id).lpTokenId;vault.rebalance(_bucket(),1,block.timestamp+100);
            assertGt(_record(id).lpTokenId,old);assertEq(vault.sharesOf(id),share);
            assertEq(rewards.claimable(id,address(t0)),90);assertEq(nft.royaltyRewards().claimable(id,address(0)),royalty);
        }
        vm.prank(alice);nft.transferFrom(alice,bob,id);
        assertEq(nft.ownerOf(id),bob);assertEq(rewards.claimable(id,address(t0)),90);
        Position memory before=_record(id);uint256 value=_value(id);
        venue.setFail(true);vm.expectRevert();vault.rebalance(_bucket(),1,block.timestamp+100);
        assertEq(_record(id).lpTokenId,before.lpTokenId);assertEq(venue.ownerOf(before.lpTokenId),address(vault));
        assertEq(_value(id),value);assertEq(vault.sharesOf(id),share);
        vm.prank(alice);vm.expectRevert();rewards.claim(id,address(t0));
        uint256 balance=t0.balanceOf(bob);vm.prank(bob);rewards.claim(id,address(t0));assertEq(t0.balanceOf(bob)-balance,90);
        ZZZRoyaltyRewards royaltyLedger=nft.royaltyRewards();
        uint256 ethBalance=bob.balance;vm.prank(bob);royaltyLedger.claim(id,address(0));assertEq(bob.balance-ethBalance,royalty);
    }
    function testFuzzShareRoundingAndRepeatedRebalancePreserveValue(uint96 input,uint8 repeats) public {
        (uint256 id,)=_fivePercent();uint256 added=bound(uint256(input),100,10000);
        uint256 entrant=_mint(bob);uint256 valueBefore=_value(id);uint256 beforeShare=vault.sharesOf(id);
        _activate(bob,entrant,added,0);
        assertEq(vault.sharesOf(entrant),added*1e18);assertEq(_value(id),valueBefore);
        uint256 count=bound(uint256(repeats),1,4);
        for(uint256 i;i<count;++i){vault.rebalance(_bucket(),1,block.timestamp+100);assertEq(vault.sharesOf(id),beforeShare);assertEq(_value(id),valueBefore);}
        assertEq(vault.bucketTotalShares(_bucket()),(10000+added)*1e18);
    }
}
