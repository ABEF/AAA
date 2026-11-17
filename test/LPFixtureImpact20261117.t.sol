// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {DirectEntryFixture} from "./AtomicActivationIntegration.t.sol";
import {DirectEntryCallbackToken} from "./ContributionEntryPriceSecurity.t.sol";
import {IZZZProtocolPolicy} from "../src/interfaces/IZZZProtocolPolicy.sol";

interface IImpactFeedMutation {function mutateBothSources() external;}

/// @dev Explicit adversarial-runtime substitution, not the deployed ZZZ code.
contract ImpactFeedMutationToken is MockToken {
    address private callback;address private watched;
    constructor()MockToken(0){}
    function configure(address target,address receiver) external {callback=target;watched=receiver;}
    function _update(address from,address to,uint256 value)internal override{
        super._update(from,to,value);
        if(callback!=address(0) && to==watched && value!=0)IImpactFeedMutation(callback).mutateBothSources();
    }
}

/// @notice DirectEntry adds actual asset policy/caller-review/endEntry checks;
/// the liquidity geometry and controlled sources remain explicitly synthetic.
contract EntryFixtureImpact20261117Test is DirectEntryFixture {
    function testEntryPullApprovalAndFinalResetActuallyInvokeRejectedFeedChanges() public realIntegration {
        address source=oracle.policy(oracle.activePolicy(address(t1))).primary.source;
        int256 initial=MockFeed(source).answer();uint256 initialToken=t1.balanceOf(alice);
        DirectEntryCallbackToken implementation=new DirectEntryCallbackToken();
        vm.etch(address(t1),address(implementation).code);
        DirectEntryCallbackToken token=DirectEntryCallbackToken(address(t1));
        assets.setAsset(address(t1),true,address(t1).codehash,REVIEW);
        uint256 id;
        for(uint8 phase=1;phase<=3;++phase){
            id=_mint(alice);
            bytes memory mutation=abi.encodeCall(MockFeed.set,(initial+1,block.timestamp,block.timestamp));
            token.configure(address(entry),source,mutation,phase);
            bytes32 expectedPolicy=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
            vm.startPrank(alice);t1.approve(address(entry),100e18);
            vm.expectCall(source,mutation);vm.expectRevert(ZZZModule.InvalidState.selector);
            entry.executeReviewed(_request(id,false),100,expectedPolicy);
            vm.stopPrank();
            assertEq(MockFeed(source).answer(),initial);_unspent(id,initialToken);
            assertEq(vault.bucketCount(),0);assertEq(membership.totalEligible(),0);
            assertEq(venue.next(),1);assertEq(t1.allowance(address(entry),address(vault)),0);
        }
        token.configure(address(entry),source,bytes(""),0);
        _execute(alice,_request(id,false));
        assertEq(vault.contributionUSD(id),100e18);assertEq(vault.sharesOf(id),100e18);
        assertEq(venue.a1(vault.group(vault.nftBucket(id)).lpTokenId),100e18);
        assertEq(membership.totalEligible(),1);_clean();
    }
}

/// @notice Cross-action accounting/rollback checks for the repaired synthetic
/// native fixture. Real Vault/Budget/Pricing/Fees/Rewards/NFT/Membership execute;
/// LP geometry, exchange, governance, feeds and randomness remain test doubles.
/// These are not actual-v4 execution, market, gas or production qualification.
contract LPFixtureImpact20261117Test is PooledVaultFixture {
    MockFeed private changedPrimary;MockFeed private changedSecondary;

    function mutateBothSources() external {
        require(msg.sender==address(t1));
        changedPrimary.set(101_000_000,block.timestamp,block.timestamp);
        changedSecondary.set(101_000_000,block.timestamp,block.timestamp);
    }

    function testPullCallbackMustReachBothFeedMutationsAndRejectWithTypedStateError() public {
        changedPrimary=new MockFeed(8,1e8);changedSecondary=new MockFeed(8,1e8);
        oracle.setDualFeed(address(t1),
            ZZZOracle.SourcePolicy(address(changedPrimary),address(changedPrimary).codehash,keccak256("impact-first"),3600,8),
            ZZZOracle.SourcePolicy(address(changedSecondary),address(changedSecondary).codehash,keccak256("impact-second"),3600,8),
            0,keccak256("TEST ONLY deliberately controlled feeds"));
        uint256 first=activatedPosition();uint256 bucket=vault.nftBucket(first);
        uint256 entrant=_mint(bob);uint256 shares=vault.bucketTotalShares(bucket);
        Position memory p=vault.group(bucket);uint256 wallet=t1.balanceOf(bob);
        ImpactFeedMutationToken implementation=new ImpactFeedMutationToken();
        vm.etch(address(t1),address(implementation).code);
        ImpactFeedMutationToken(address(t1)).configure(address(this),address(vault));
        bytes memory mutation=abi.encodeCall(MockFeed.set,(int256(101_000_000),block.timestamp,block.timestamp));
        vm.expectCall(address(changedPrimary),mutation);vm.expectCall(address(changedSecondary),mutation);
        vm.prank(bob);vm.expectRevert(ZZZModule.InvalidState.selector);
        vault.activate(entrant,poolId,0,100,1,block.timestamp+100);
        assertEq(changedPrimary.answer(),1e8);assertEq(changedSecondary.answer(),1e8);
        assertEq(t1.balanceOf(bob),wallet);assertEq(vault.bucketTotalShares(bucket),shares);
        assertEq(vault.group(bucket).lpTokenId,p.lpTokenId);assertEq(venue.a1(p.lpTokenId),1000);
        assertEq(vault.nftBucket(entrant),0);assertEq(vault.sharesOf(entrant),0);
        assertEq(membership.totalEligible(),1);assertFalse(oracle.contributionPricing().active());
        ImpactFeedMutationToken(address(t1)).configure(address(0),address(vault));
        _activate(bob,entrant,0,100);
        assertEq(vault.group(bucket).lpTokenId,p.lpTokenId);assertEq(venue.a1(p.lpTokenId),1100);
        assertEq(vault.sharesOf(first),shares);assertEq(vault.sharesOf(entrant),100e18);
        assertEq(membership.totalEligible(),2);assertFalse(oracle.contributionPricing().active());
    }

    function testMarginal97BoundaryWithIncumbentIdleCompoundAndAtomicRetry() public {
        assertEq(vault.migrationBudget().contributionLossBps(),300);
        venue.setSpendBps(9800);
        uint256 first=activatedPosition();uint256 bucket=vault.nftBucket(first);
        Position memory beforePosition=vault.group(bucket);
        uint256 shares=vault.sharesOf(first);
        venue.setFees(100,100);vault.collectFees(bucket,block.timestamp+100);
        uint256 entrant=_mint(bob);
        _giftNative(address(vault),777);t1.mint(address(vault),888);
        uint256 walletETH=bob.balance;uint256 walletZZZ=t1.balanceOf(bob);
        uint256 venueETH=address(venue).balance;uint256 tokenSupply=t1.totalSupply();

        // A large aggregate LP and existing idle/compound cannot subsidize the
        // one missing marginal LP unit. Only the entrant's budget is deployed.
        venue.setSpendBps(9699);
        vm.prank(bob);vm.expectRevert(ZZZModule.Slippage.selector);
        vault.activate{value:10000}(entrant,poolId,10000,0,1,block.timestamp+100);
        assertEq(bob.balance,walletETH);assertEq(t1.balanceOf(bob),walletZZZ);
        assertEq(address(venue).balance,venueETH);assertEq(t1.totalSupply(),tokenSupply);
        assertEq(vault.sharesOf(first),shares);assertEq(vault.sharesOf(entrant),0);
        assertEq(vault.nftBucket(entrant),0);assertEq(membership.totalEligible(),1);
        assertFalse(membership.eligible(entrant));assertFalse(oracle.contributionPricing().active());
        assertEq(fees.compoundBalance(bucket,address(0)),5);
        assertEq(fees.compoundBalance(bucket,address(t1)),5);
        assertEq(rewards.claimable(first,address(0)),90);
        assertEq(venue.a0(beforePosition.lpTokenId),980);
        assertEq(vault.group(bucket).idle0,20);

        venue.setSpendBps(9700);_activate(bob,entrant,10000,0);
        Position memory afterPosition=vault.group(bucket);
        assertEq(afterPosition.lpTokenId,beforePosition.lpTokenId);
        assertEq(afterPosition.centerX96,beforePosition.centerX96);
        assertEq(afterPosition.lastRebalance,beforePosition.lastRebalance);
        assertEq(venue.balanceAmount0(),10000);assertEq(venue.balanceAmount1(),0);
        assertEq(venue.a0(afterPosition.lpTokenId),10680);
        assertEq(venue.a1(afterPosition.lpTokenId),980);
        assertEq(afterPosition.idle0,325);assertEq(afterPosition.idle1,25);
        assertEq(vault.sharesOf(first),shares);
        assertEq(vault.sharesOf(entrant),shares*10000e18/2010e18);
        assertEq(vault.bucketTotalShares(bucket),shares+vault.sharesOf(entrant));
        assertEq(rewards.claimable(entrant,address(0)),0);
        assertEq(rewards.claimable(first,address(t1)),90);
        assertEq(fees.compoundBalance(bucket,address(0)),0);
        assertEq(fees.buybackBalance(address(0)),5);
        assertEq(address(vault).balance-vault.totalIdle(address(0)),777);
        assertEq(t1.balanceOf(address(vault))-vault.totalIdle(address(t1)),888);
        assertEq(t1.allowance(address(vault),address(venue)),0);
        assertEq(membership.totalEligible(),2);assertFalse(oracle.contributionPricing().active());
    }

    function testPartialClaimsTransferGrowthAndNextHarvestKeepBothAssetsExact() public {
        uint256 first=activatedPosition();uint256 second=_mint(bob);_activate(bob,second,2000,2000);
        uint256 bucket=vault.nftBucket(first);Position memory initial=vault.group(bucket);
        uint256 secondShares=vault.sharesOf(second);
        venue.setFees(6000,6000);vault.collectFees(bucket,block.timestamp+100);
        assertEq(rewards.claimable(first,address(0)),1900);
        assertEq(rewards.claimable(second,address(0)),3500);
        uint256 aliceETH=alice.balance;
        vm.prank(alice);assertEq(rewards.claim(first,address(0)),1900);
        assertEq(alice.balance,aliceETH+1900);
        vm.prank(alice);nft.transferFrom(alice,bob,first);
        vm.prank(alice);vm.expectRevert(ZZZModule.Unauthorized.selector);
        rewards.claim(first,address(t1));
        uint256 sharesBefore=vault.sharesOf(first);uint256 fundingBefore=bob.balance;
        // Releasing the existing600 compound into attributed idle would leave
        // 600/8600 above the existing5% cap. Entrant-only placement must reject
        // atomically rather than using the entrant to deploy incumbent assets.
        vm.prank(bob);vm.expectRevert(ZZZModule.Slippage.selector);
        vault.increase{value:1000}(first,1000,1000,1,block.timestamp+100);
        assertEq(bob.balance,fundingBefore);assertEq(vault.sharesOf(first),sharesBefore);
        assertEq(vault.group(bucket).idle0,0);assertEq(vault.group(bucket).idle1,0);
        assertEq(fees.compoundBalance(bucket,address(0)),300);
        assertEq(fees.compoundBalance(bucket,address(t1)),300);
        assertEq(rewards.claimable(first,address(t1)),1900);
        assertFalse(oracle.contributionPricing().active());
        // Actual keeper compound at the independent interval recovers the
        // incumbent assets into the SAME LP; it issues no NFT shares and does
        // not recenter/reset the rebalance clock. No policy/cap is widened.
        policy.setNeed(false);vm.warp(block.timestamp+1 hours);
        compounder.compound(bucket,1,block.timestamp+100);
        assertEq(vault.sharesOf(first),sharesBefore);assertEq(vault.sharesOf(second),secondShares);
        assertEq(venue.a0(initial.lpTokenId),3300);assertEq(venue.a1(initial.lpTokenId),3300);
        assertEq(vault.group(bucket).lastRebalance,initial.lastRebalance);
        vm.prank(bob);vault.increase{value:1000}(first,1000,1000,1,block.timestamp+100);
        assertEq(vault.sharesOf(second),secondShares);
        assertEq(vault.group(bucket).lpTokenId,initial.lpTokenId);
        assertEq(vault.group(bucket).lastRebalance,initial.lastRebalance);
        assertEq(vault.group(bucket).idle0,0);assertEq(vault.group(bucket).idle1,0);
        assertEq(rewards.claimable(first,address(0)),0);
        assertEq(rewards.claimable(first,address(t1)),1900);
        uint256 dormant=_mint(alice);assertFalse(membership.eligible(dormant));
        assertEq(membership.totalEligible(),2);
        venue.setFees(20,20);vault.collectFees(bucket,block.timestamp+100);
        assertEq(rewards.claimable(first,address(0))+rewards.claimable(second,address(0)),3518);
        assertEq(rewards.claimable(first,address(t1))+rewards.claimable(second,address(t1)),5418);
        assertEq(rewards.claimable(dormant,address(0)),0);
        assertEq(rewards.claimable(dormant,address(t1)),0);
        uint256 bobETH=bob.balance;uint256 bobZZZ=t1.balanceOf(bob);
        vm.startPrank(bob);
        uint256 paidETH=rewards.claim(first,address(0))+rewards.claim(second,address(0));
        uint256 paidZZZ=rewards.claim(first,address(t1))+rewards.claim(second,address(t1));
        vm.stopPrank();
        assertEq(paidETH,3518);assertEq(paidZZZ,5418);
        assertEq(bob.balance,bobETH+paidETH);assertEq(t1.balanceOf(bob),bobZZZ+paidZZZ);
        assertEq(rewards.liabilities(address(0)),0);assertEq(rewards.liabilities(address(t1)),0);
        assertEq(fees.compoundBalance(bucket,address(0)),1);
        assertEq(fees.compoundBalance(bucket,address(t1)),1);
        assertEq(fees.buybackBalance(address(0)),301);assertEq(fees.buybackBalance(address(t1)),301);
        assertEq(fees.accounted(address(0)),302);assertEq(fees.accounted(address(t1)),302);
        assertEq(address(fees).balance,302);assertEq(t1.balanceOf(address(fees)),302);
        assertEq(venue.a0(initial.lpTokenId),4300);assertEq(venue.a1(initial.lpTokenId),4300);
        assertEq(vault.bucketCount(),1);assertEq(nft.ownerOf(first),bob);
        assertFalse(oracle.contributionPricing().active());
    }

    function testFullCapacityMoveMintFaultRollsBackThenMoveAndReturnRemainFunded() public {
        uint256 first=activatedPosition();uint256 second=_mint(bob);_activate(bob,second,1000,1000);
        uint256 bucket=vault.nftBucket(first);uint256 shares=vault.bucketTotalShares(bucket);
        Position memory initial=vault.group(bucket);
        for(uint256 i=1;i<4;++i){
            bytes32 reserved=_pool(uint24(500+i));
            vault.reservePool(reserved,vault.canonicalModule().bucketIdentity(reserved));
        }
        bytes32 destination=_pool(1000);
        ZZZMigration migration=new ZZZMigration(address(ac));ac.bind(Ids.MIGRATION,address(migration));
        venue.setFees(1000,1000);_giftNative(address(vault),777);t1.mint(address(vault),888);
        uint256 backing=address(venue).balance;uint256 tokenSupply=t1.totalSupply();
        uint256 deadline=block.timestamp+100;
        bytes memory mintCall=abi.encodeWithSelector(VaultLiquidityMock.mint.selector,destination,int24(-600),int24(600),uint256(2050),uint256(2050),uint128(1),deadline);
        bytes4 fault=bytes4(keccak256("ImpactPlannedMintFailure()"));
        vm.mockCallRevert(address(venue),mintCall,abi.encodeWithSelector(fault));
        vm.expectRevert(fault);migration.moveFunds(bucket,destination,1,deadline);
        assertEq(address(venue).balance,backing);assertEq(t1.totalSupply(),tokenSupply);
        assertEq(vault.group(bucket).lpTokenId,initial.lpTokenId);
        assertEq(venue.ownerOf(initial.lpTokenId),address(vault));
        assertEq(venue.fee0(),1000);assertEq(venue.fee1(),1000);
        assertEq(vault.poolBucket(destination),0);assertEq(vault.canonicalModule().aliasBucket(destination),0);
        assertEq(vault.bucketCount(),4);assertEq(vault.bucketTotalShares(bucket),shares);
        assertEq(rewards.liabilities(address(0)),0);assertEq(fees.accounted(address(0)),0);
        assertEq(address(vault).balance,777);assertEq(t1.balanceOf(address(vault)),888);
        vm.clearMockedCalls();migration.moveFunds(bucket,destination,1,deadline);
        assertEq(vault.poolBucket(destination),bucket);assertEq(vault.bucketCount(),4);
        assertEq(venue.a0(vault.group(bucket).lpTokenId),2050);
        assertEq(rewards.claimable(first,address(0)),450);
        assertEq(rewards.claimable(second,address(0)),450);
        migration.moveFunds(bucket,poolId,1,deadline);
        assertEq(vault.group(bucket).poolId,poolId);assertEq(vault.bucketCount(),4);
        assertEq(vault.bucketTotalShares(bucket),shares);assertEq(vault.homePoolId(bucket),poolId);
        assertEq(venue.a0(vault.group(bucket).lpTokenId),2050);
        assertEq(venue.a1(vault.group(bucket).lpTokenId),2050);
        assertEq(fees.buybackBalance(address(0)),50);assertEq(fees.buybackBalance(address(t1)),50);
        assertEq(address(vault).balance,777);assertEq(t1.balanceOf(address(vault)),888);
        assertEq(t1.allowance(address(vault),address(venue)),0);
        assertFalse(oracle.contributionPricing().active());
    }

    function _pool(uint24 fee) private returns(bytes32 id){
        PoolConfig memory c=pools.get(poolId);c.key.fee=fee;id=keccak256(abi.encode(c.key));pools.set(id,c);
    }
}
