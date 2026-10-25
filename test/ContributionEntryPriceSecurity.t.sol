// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {AtomicActivationIntegrationTest} from "./AtomicActivationIntegration.t.sol";
import {IActivationV3Router,ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";
import {PoolConfig,PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @dev TEST ONLY typed conversion with exact transfers and a hostile callback.
/// This is not actual market execution or source/provider qualification.
contract EntryPriceCallbackRouter is IActivationV3Router {
    address public immutable factory;
    address public target;
    bytes public data;
    uint256 public outputBps=9900;
    constructor(address factory_) { factory=factory_; }
    function configure(address target_,bytes calldata data_,uint256 bps) external {
        target=target_;data=data_;outputBps=bps;
    }
    function exactInputSingle(ExactInputSingleParams calldata p) external payable returns(uint256 out) {
        require(msg.value==0 && p.fee==500 && p.sqrtPriceLimitX96==0);
        require(IERC20(p.tokenIn).transferFrom(msg.sender,address(this),p.amountIn));
        out=p.amountIn*1e12*outputBps/10000;
        require(out>=p.amountOutMinimum);require(IERC20(p.tokenOut).transfer(p.recipient,out));
        if(target!=address(0)) {
            (bool ok,bytes memory reason)=target.call(data);
            if(!ok) assembly("memory-safe") { revert(add(reason,32),mload(reason)) }
        }
    }
}

/// @dev TEST ONLY replacement runtime preserves inherited ERC20 storage. It
/// changes a feed specifically at the Entry's final approval-reset boundary.
contract EntryFinalResetToken is MockToken {
    address private watched;
    address private target;
    bytes private data;
    bool private entered;
    constructor() MockToken(18) {}
    function configure(address account,address target_,bytes calldata data_) external {
        watched=account;target=target_;data=data_;
    }
    function approve(address spender,uint256 amount) public override returns(bool) {
        bool ok=super.approve(spender,amount);
        if(!entered && msg.sender==watched && amount==0 && target!=address(0)) {
            entered=true;(bool success,bytes memory reason)=target.call(data);
            if(!success) assembly("memory-safe") { revert(add(reason,32),mload(reason)) }
            entered=false;
        }
        return ok;
    }
}

/// @notice Real Registry/Entry/Oracle/price companion/Vault/reward ledgers.
/// Exact-token runtime callbacks, authority, feeds, LP venue and swap math are
/// explicit local security fixtures; no live ZZZ exploit/provider is asserted.
contract ContributionEntryPriceSecurityTest is AtomicActivationIntegrationTest {
    function _callbackRoute() private returns(EntryPriceCallbackRouter selected,bytes32 id) {
        selected=new EntryPriceCallbackRouter(address(factory));
        id=entry.addRoute(ZZZActivationEntry.RoutePolicy(address(stable),address(t0),address(selected),
            address(factory),address(conversionPool),500,address(selected).codehash,address(factory).codehash,
            address(conversionPool).codehash,address(stable).codehash,address(t0).codehash,REVIEW));
        t0.mint(address(selected),100000e18);
    }
    function _request(uint256 id,bytes32 route) private view returns(ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id,poolId,address(stable),100e6,route,99e18,1,block.timestamp+100,false);
    }
    function _assertRollback(uint256 id,EntryPriceCallbackRouter selected,uint256 sourceBefore,uint256 outputBefore) private {
        assertEq(stable.balanceOf(alice),sourceBefore);assertEq(stable.balanceOf(address(selected)),0);
        assertEq(t0.balanceOf(address(selected)),outputBefore);assertEq(vault.sharesOf(id),0);
        assertEq(vault.nftBucket(id),0);assertEq(vault.contributionUSD(id),0);
        assertEq(uint256(vault.nftStatus(id)),uint256(PositionStatus.Dormant));
        assertFalse(membership.eligible(id));assertEq(nft.royaltyRewards().weightOf(id),0);
        assertEq(vault.bucketCount(),0);assertFalse(oracle.contributionPricing().active());
        assertEq(stable.balanceOf(address(entry)),0);assertEq(t0.balanceOf(address(entry)),0);
        assertEq(stable.allowance(address(entry),address(selected)),0);
        assertEq(t0.allowance(address(entry),address(vault)),0);
    }
    function _policyMutation(uint16 contribution,uint256 outputBps) private {
        (EntryPriceCallbackRouter selected,bytes32 route)=_callbackRoute();
        ZZZMigrationBudget budget=vault.migrationBudget();
        selected.configure(address(budget),abi.encodeCall(budget.setLossLimits,(contribution,300)),outputBps);
        vm.mockCall(address(ac),abi.encodeCall(ac.canConfigure,(address(selected))),abi.encode(true));
        uint256 id=_mint(alice);uint256 beforeSource=stable.balanceOf(alice);uint256 beforeOutput=t0.balanceOf(address(selected));
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(_request(id,route), 100);
        assertEq(budget.contributionLossBps(),100);_assertRollback(id,selected,beforeSource,beforeOutput);
    }
    function testEntryPriceCaptureRejectsWiderLossPolicyDuringSourceConversion() public realIntegration {
        _policyMutation(1000,9900);
    }
    function testEntryPriceCaptureRejectsTighterLossPolicyDuringSourceConversion() public realIntegration {
        _policyMutation(0,10000);
    }
    function testEntryPriceCaptureRejectsVenueFloorChangeDuringConversion() public realIntegration {
        (EntryPriceCallbackRouter selected,bytes32 route)=_callbackRoute();
        PoolConfig memory c=registry.get(poolId);c.maxSlippageBps=200;
        selected.configure(address(registry),abi.encodeCall(registry.configure,(c)),9900);
        vm.mockCall(address(ac),abi.encodeCall(ac.canConfigure,(address(selected))),abi.encode(true));
        uint256 id=_mint(alice);uint256 beforeSource=stable.balanceOf(alice);uint256 beforeOutput=t0.balanceOf(address(selected));
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(_request(id,route), 100);
        assertEq(registry.get(poolId).maxSlippageBps,100);_assertRollback(id,selected,beforeSource,beforeOutput);
    }
    function testEntryPriceCaptureRejectsSourceRoundChangeDuringConversion() public realIntegration {
        (EntryPriceCallbackRouter selected,bytes32 route)=_callbackRoute();
        selected.configure(address(stableFeed),abi.encodeCall(stableFeed.set,(101e6,block.timestamp,block.timestamp)),9900);
        uint256 id=_mint(alice);uint256 beforeSource=stable.balanceOf(alice);uint256 beforeOutput=t0.balanceOf(address(selected));
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(_request(id,route), 100);
        assertEq(stableFeed.answer(),1e8);_assertRollback(id,selected,beforeSource,beforeOutput);
    }
    function testEntryPriceCaptureSurvivesUntilFinalApprovalReset() public realIntegration {
        EntryFinalResetToken replacement=new EntryFinalResetToken();vm.etch(address(t0),address(replacement).code);
        (address source,,,)=oracle.feeds(address(t0));MockFeed feed=MockFeed(source);
        EntryFinalResetToken(address(t0)).configure(address(entry),source,
            abi.encodeCall(feed.set,(101e6,block.timestamp,block.timestamp)));
        (EntryPriceCallbackRouter selected,bytes32 route)=_callbackRoute();
        uint256 id=_mint(alice);uint256 beforeSource=stable.balanceOf(alice);uint256 beforeOutput=t0.balanceOf(address(selected));
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(_request(id,route), 100);
        assertEq(feed.answer(),1e8);_assertRollback(id,selected,beforeSource,beforeOutput);
    }
    function testEntryPriceCaptureHonestReviewedRouteCommitsAndClearsBasis() public realIntegration {
        (EntryPriceCallbackRouter selected,bytes32 route)=_callbackRoute();uint256 id=_mint(alice);
        vm.prank(alice);entry.executeReviewed(_request(id,route), 100);
        assertEq(vault.contributionUSD(id),100e18);assertEq(vault.sharesOf(id),99e18);
        assertTrue(membership.eligible(id));assertEq(nft.royaltyRewards().weightOf(id),1);
        assertFalse(oracle.contributionPricing().active());assertEq(stable.balanceOf(address(selected)),100e6);
        assertEq(t0.allowance(address(entry),address(vault)),0);
    }
}
