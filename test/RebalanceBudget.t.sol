// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {BudgetAdversarialVenue,BudgetAdversarialPolicy} from "./MigrationBudgetAdversarial.t.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {MockFeed} from "./mocks/Mocks.sol";
import {Ids,Position} from "../src/libraries/ZZZTypes.sol";

contract RebalanceBudgetPolicy is BudgetAdversarialPolicy {
    function needsRebalance(uint256) external pure returns(bool){return true;}
}
contract RebalanceBudgetTest is PooledVaultFixture {
    BudgetAdversarialVenue adverse; RebalanceBudgetPolicy rebalancePolicy;
    event MigrationValueChecked(uint256 indexed bucketId,uint256 beforeUSD,uint256 deployedUSD,uint256 idleUSD);
    function _start() private returns(uint256 id){
        adverse=new BudgetAdversarialVenue(address(t0),address(t1));rebalancePolicy=new RebalanceBudgetPolicy();
        ac.bind(Ids.LIQUIDITY,address(adverse));ac.bind(Ids.STRATEGY,address(rebalancePolicy));
        id=activatedPosition();
    }
    function _run() private {vault.rebalance(_bucket(),1,block.timestamp+100);}
    function _unchanged(uint256 id,Position memory p) private view {
        assertEq(_record(id).lpTokenId,p.lpTokenId);assertEq(adverse.ownerOf(p.lpTokenId),address(vault));
        assertEq(vault.sharesOf(id),2000e18);assertEq(vault.bucketTotalShares(_bucket()),2000e18);
        assertEq(adverse.amount0(p.lpTokenId),1000);assertEq(adverse.amount1(p.lpTokenId),1000);
        assertEq(t0.allowance(address(vault),address(adverse)),0);
    }
    function testStackedCloseSwapMintLossRejectedThenExactThreePercentAccepted() public {
        uint256 id=_start();Position memory p=_record(id);
        adverse.losses(20,20,5,5);rebalancePolicy.setSwapAmount(100);adverse.setSwapOutput(82);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector);_run();_unchanged(id,p);
        adverse.setSwapOutput(90);
        vm.expectEmit(true,false,false,true,address(vault.migrationBudget()));
        emit MigrationValueChecked(_bucket(),2000e18,1940e18,0);_run();
        assertEq(vault.sharesOf(id),2000e18);assertGt(_record(id).lpTokenId,p.lpTokenId);
    }
    function testCompoundCannotMaskLossAndFailedHarvestRollsBackRewards() public {
        uint256 id=_start();Position memory p=_record(id);
        adverse.setFees(1000,1000);adverse.losses(40,40,0,0);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector);_run();_unchanged(id,p);
        assertEq(adverse.fee0(),1000);assertEq(rewards.claimable(id,address(t0)),0);
        assertEq(fees.compoundBalance(_bucket(),address(t0)),0);
    }
    function testPriceChangesDuringHarvestCannotHideExecutionLoss() public {
        uint256 id=_start();Position memory p=_record(id);
        MockFeed feed=new MockFeed(8,1e8);oracle.setFeed(address(t0),address(feed),3600);
        oracle.setFeed(address(t1),address(feed),3600);
        adverse.harvestLosses(40,40);adverse.mutatePrice(feed,2e8,false);adverse.mutateAtHarvest(true);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector);_run();_unchanged(id,p);
        assertEq(feed.answer(),1e8);
    }
    function testDonationsAndClaimableFeesCannotPayRebalanceLoss() public {
        uint256 id=_start();adverse.setFees(1000,1000);vault.collectFees(_bucket(),block.timestamp+100);
        t0.mint(address(vault),10000);t1.mint(address(vault),10000);
        adverse.losses(40,40,0,0);uint256 owed=rewards.claimable(id,address(t0));
        Position memory p=_record(id);vm.expectRevert(ZZZMigrationBudget.Slippage.selector);_run();
        assertEq(_record(id).lpTokenId,p.lpTokenId);assertEq(rewards.claimable(id,address(t0)),owed);
        assertEq(t0.balanceOf(address(vault)),10000);
    }
    function testRepeatedSnapshotsClearAndExistingIdleCapStillApplies() public {
        uint256 id=_start();adverse.spending(9500,9500);_run();
        assertEq(_record(id).idle0,50);assertEq(_record(id).idle1,50);
        adverse.spending(10000,10000);_run();assertEq(_record(id).idle0,0);
        uint256 lp=_record(id).lpTokenId;adverse.spending(9400,9400);
        vm.expectRevert();_run();assertEq(_record(id).lpTokenId,lp);
        adverse.spending(10000,10000);_run();assertGt(_record(id).lpTokenId,lp);
    }
    function testRebalanceSnapshotCannotBeReenteredDuringClose() public {
        _start();adverse.reenter(address(vault),abi.encodeCall(vault.rebalance,(_bucket(),uint128(1),block.timestamp+100)));
        ac.setKeeper(address(adverse),true);_run();assertTrue(adverse.reentryAttempted());assertFalse(adverse.reentrySucceeded());
    }
    function testFuzzThreePercentCloseBoundary(uint16 basisPoints) public {
        uint256 id=_start();uint256 loss=bound(uint256(basisPoints),0,600);
        adverse.losses(loss,0,0,0);Position memory p=_record(id);
        if(loss>60){vm.expectRevert(ZZZMigrationBudget.Slippage.selector);_run();_unchanged(id,p);}
        else {_run();(bool available,uint256 value)=nft.currentLPValue(id);assertTrue(available);assertEq(value,(2000-loss)*1e18);}
    }
}
