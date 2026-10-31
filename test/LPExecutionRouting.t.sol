// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";

import {Test} from "forge-std/Test.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta, BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {IPositionDescriptor} from "@uniswap/v4-periphery/src/interfaces/IPositionDescriptor.sol";
import {IWETH9} from "@uniswap/v4-periphery/src/interfaces/external/IWETH9.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockFeed} from "./mocks/Mocks.sol";
import {FactualPools, FactualPermit, FactualToken} from "./LiquidityFactualChecks.t.sol";

/// @dev TEST ONLY native admission seam; installed v4 execution remains real.
contract ExecutionPools is FactualPools {
    uint64 public configurationRevision;
    function configure(bytes32 id, PoolConfig memory c) external { this.set(id,c); ++configurationRevision; }
}

contract LPExecutionRoutingTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    MockAccess private access;
    FactualToken private token;
    MockFeed private first;
    MockFeed private second;
    ZZZOracle private oracle;
    ZZZStrategy private strategy;
    ExecutionPools private registry;
    PoolManager private core;
    StateView private state;
    PositionManager private positions;
    ZZZLiquidityManager private manager;
    ZZZLPBalancer private router;
    CoreKey private targetKey;
    CoreKey private alternateKey;
    bytes32 private target;
    bytes32 private alternate;
    uint256 private constant PREFUND = 17;
    receive() external payable {}

    function setUp() public {
        vm.warp(1_000_000); vm.deal(address(this),10_000_000 ether);
        access = new MockAccess(); ProtocolPolicyFixture.bind(address(access)); token = new FactualToken(); token.mint(address(this),10_000_000 ether);
        core = new PoolManager(address(this)); state = new StateView(IPoolManager(address(core)));
        FactualPermit permit = new FactualPermit();
        positions = new PositionManager(IPoolManager(address(core)),IAllowanceTransfer(address(permit)),100000,
            IPositionDescriptor(address(0)),IWETH9(address(0)));
        manager = new ZZZLiquidityManager(address(access),address(positions),address(state),address(core),address(permit), address(new ZZZLPBalancer(address(access), address(core), address(state))));
        router = manager.balancingRouter();
        oracle = new ZZZOracle(address(access),address(0)); strategy = new ZZZStrategy(address(access), address(new ZZZPortfolioPolicy(address(access))), address(new ZZZRebalanceConfirmation(address(access))));
        registry = new ExecutionPools(); first = new MockFeed(8,1e8); second = new MockFeed(8,1e8);
        access.bind(Ids.VAULT,address(this)); access.bind(Ids.LIQUIDITY,address(manager));
        access.bind(Ids.ORACLE,address(oracle)); access.bind(Ids.STRATEGY,address(strategy)); access.bind(Ids.POOLS,address(registry));
        _feeds(address(0)); _feeds(address(token));
        targetKey = CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),10020,200,IHooks(address(0)));
        alternateKey = CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),500,10,IHooks(address(0)));
        target = _admit(targetKey); alternate = _admit(alternateKey);
        core.initialize(targetKey,uint160(1<<96)); core.initialize(alternateKey,uint160(1<<96));
        core.setProtocolFeeController(address(this));
        core.setProtocolFee(targetKey,uint24(1000|(1000<<12)));
        core.setProtocolFee(alternateKey,uint24(1000|(1000<<12)));
        _external(targetKey,1_000_000 ether); _external(alternateKey,1_000_000 ether);
        access.seal(); _catalog(true,true);
        vm.deal(address(manager),PREFUND); token.mint(address(manager),PREFUND);
        token.approve(address(manager),type(uint128).max); token.approve(manager.positionOperator(), type(uint128).max);
    }
    function _feeds(address asset) private {
        oracle.setDualFeed(asset,
            ZZZOracle.SourcePolicy(address(first),address(first).codehash,keccak256("test-a"),3600,8),
            ZZZOracle.SourcePolicy(address(second),address(second).codehash,keccak256("test-b"),3600,8),300,keccak256("local test sources"));
    }
    function _admit(CoreKey memory key) private returns (bytes32 id) {
        PoolKey memory k = PoolKey(Currency.unwrap(key.currency0),Currency.unwrap(key.currency1),key.fee,key.tickSpacing,address(key.hooks));
        id = keccak256(abi.encode(k));
        registry.configure(id,PoolConfig(k,false,true,2500,100,500,200,600,1e18,1e30));
    }
    function _catalog(bool useTarget,bool useAlternate) private {
        bytes32[] memory ids = new bytes32[]((useTarget?1:0)+(useAlternate?1:0));
        uint256 i; if(useTarget) ids[i++]=target; if(useAlternate) ids[i]=alternate;
        router.configureExecutionPools(ids,keccak256("reviewed local native test venues"));
    }
    function _external(CoreKey memory key,int256 liquidity) private {
        core.unlock(abi.encode(key,liquidity));
    }
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender==address(core)); (CoreKey memory key,int256 liquidity)=abi.decode(data,(CoreKey,int256));
        (BalanceDelta delta,) = core.modifyLiquidity(key,ModifyLiquidityParams(-60000,60000,liquidity,bytes32(0)),"");
        _settle(Currency.unwrap(key.currency0),delta.amount0()); _settle(Currency.unwrap(key.currency1),delta.amount1()); return "";
    }
    function _settle(address asset,int128 delta) private {
        if(delta==0) return;
        if(delta>0) { core.take(Currency.wrap(asset),address(this),uint256(int256(delta))); return; }
        uint256 amount=uint256(-int256(delta)); core.sync(Currency.wrap(asset));
        if(asset==address(0)) assertEq(core.settle{value:amount}(),amount);
        else { token.transfer(address(core),amount); assertEq(core.settle(),amount); }
    }
    function _snapshot(bytes32 poolId) private view returns(bytes32) {
        (uint160 p,int24 tick,uint24 protocol,uint24 fee)=state.getSlot0(PoolId.wrap(poolId));
        (uint256 g0,uint256 g1)=state.getFeeGrowthGlobals(PoolId.wrap(poolId));
        return keccak256(abi.encode(p,tick,protocol,fee,g0,g1,state.getLiquidity(PoolId.wrap(poolId))));
    }
    function _plan(uint256 amount0,uint256 amount1) private returns(ZZZLPBalancer.Plan memory p) {
        (int24 lower,int24 upper,)=strategy.target(target);
        vm.prank(address(manager)); return router.plan(target,lower,upper,amount0,amount1);
    }
    function _assertPrefunds() private view {
        assertEq(address(manager).balance,PREFUND); assertEq(token.balanceOf(address(manager)),PREFUND);
    }
    function _cold() private {
        vm.cool(address(manager)); vm.cool(address(router)); vm.cool(address(core)); vm.cool(address(state));
        vm.cool(address(positions)); vm.cool(address(registry)); vm.cool(address(access)); vm.cool(address(oracle));
        vm.cool(address(strategy)); vm.cool(address(first)); vm.cool(address(second)); vm.cool(address(token));
    }

    function test_ActualSizeRoutingSelectsCheaperVenueAndPreservesQuotes() public {
        bytes32 a=_snapshot(target); bytes32 b=_snapshot(alternate);
        uint256 nativeFees=core.protocolFeesAccrued(Currency.wrap(address(0)));
        uint256 tokenFees=core.protocolFeesAccrued(Currency.wrap(address(token)));
        ZZZLPBalancer.Plan memory p=_plan(100 ether,0);
        assertEq(p.poolId,alternate); assertGt(p.amountIn,0);
        assertEq(_snapshot(target),a,"target quote rolls back"); assertEq(_snapshot(alternate),b,"venue quote rolls back");
        assertEq(core.protocolFeesAccrued(Currency.wrap(address(0))),nativeFees);
        assertEq(core.protocolFeesAccrued(Currency.wrap(address(token))),tokenFees);
        uint256 nativeBefore=address(this).balance; uint256 tokenBefore=token.balanceOf(address(this));
        uint256 start=gasleft(); (uint256 a0,uint256 a1)=manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        assertLt(start-gasleft(),12_000_000,"ordinary routing remains under existing operation gas gate");
        assertEq(a0,100 ether-p.amountIn); assertEq(a1,p.amountOut);
        assertEq(address(this).balance,nativeBefore-p.amountIn); assertEq(token.balanceOf(address(this)),tokenBefore+p.amountOut);
        assertEq(_snapshot(target),a,"independent LP destination stays unchanged"); _assertPrefunds();
    }
    function test_RoutesCanBeAdmittedAfterSealWithoutMovingLP() public {
        _catalog(true,false); ZZZLPBalancer.Plan memory old=_plan(100 ether,0); assertEq(old.poolId,target);
        uint64 previous=router.executionRevision(); _catalog(true,true);
        assertGt(router.executionRevision(),previous); assertEq(_plan(100 ether,0).poolId,alternate);
    }
    function test_PartialInputEmptyVenueDoesNotBlockHealthyAlternative() public {
        _external(targetKey,-int256(1_000_000 ether));
        assertEq(state.getLiquidity(PoolId.wrap(target)),0);
        assertEq(_plan(100 ether,0).poolId,alternate);
        (uint256 a0,uint256 a1)=manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        assertGt(a0,0); assertGt(a1,0); _assertPrefunds();
    }
    function test_QuoteUsesExternalDepthAfterActualOwnedLPClose() public {
        _external(targetKey,-int256(1_000_000 ether));
        (int24 lower,int24 upper,)=strategy.target(target); uint160 q=manager.spot(target);
        uint256 a0=SqrtPriceMath.getAmount0Delta(q,TickMath.getSqrtPriceAtTick(upper),1e20,true);
        uint256 a1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),q,1e20,true);
        (uint256 id,,)=manager.mint{value:a0}(target,lower,upper,a0,a1,1,block.timestamp+100);
        assertGt(state.getLiquidity(PoolId.wrap(target)),0); positions.approve(manager.positionOperator(),id);
        manager.close(target,id,block.timestamp+100);
        assertEq(state.getLiquidity(PoolId.wrap(target)),0,"removed own LP cannot fund replacement swap");
        assertEq(_plan(100 ether,0).poolId,alternate); _assertPrefunds();
    }
    function test_ThinCheaperVenueCannotBeatDeepSafeVenue() public {
        _external(alternateKey,-int256(1_000_000 ether)); _external(alternateKey,1 ether);
        assertEq(_plan(100 ether,0).poolId,target);
    }
    function test_PlannerFindsSmallerFeasibleSwapWhenSeedViolatesSpotLimit() public {
        _external(alternateKey,-int256(1_000_000 ether)); _external(alternateKey,1000 ether);
        PoolConfig memory c=registry.get(alternate); c.maxSpotDeviationBps=100; registry.configure(alternate,c);
        _catalog(false,true); bytes32 beforePool=_snapshot(alternate);
        // The fee-aware approximately56ETH seed is too large for a1% final
        // spot band. A smaller useful trade exists; its ratio still has excess
        // ETH, so using that ratio to increase an infeasible seed missed it.
        ZZZLPBalancer.Plan memory p=_plan(100 ether,0);
        assertEq(p.poolId,alternate); assertGt(p.amountIn,0); assertLt(p.amountIn,10 ether);
        assertGe(p.amountOut,p.minimumOut); assertGe(uint256(p.sqrtAfter)*uint256(p.sqrtAfter)/(1<<96),
            uint256(1<<96)*9900/10000,"predicted postspot stays within one percent");
        assertEq(_snapshot(alternate),beforePool,"planning still rolls back core changes");
        // This proves planner availability, not that a partial balance meets
        // the complete contribution deployment floor. Vault retains that gate.
    }
    function test_EmptyCatalogNeverImplicitlySwapsInDestination() public {
        _catalog(false,false); bytes32 beforePool=_snapshot(target);
        (uint256 a0,uint256 a1)=manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        assertEq(a0,100 ether); assertEq(a1,0); assertEq(_snapshot(target),beforePool); _assertPrefunds();
    }
    function test_BalancedBudgetDoesNotChaseDust() public {
        (int24 lower,int24 upper,)=strategy.target(target); uint160 q=manager.spot(target);
        uint256 a0=SqrtPriceMath.getAmount0Delta(q,TickMath.getSqrtPriceAtTick(upper),1e20,true);
        uint256 a1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),q,1e20,true);
        assertEq(_plan(a0,a1).amountIn,0);
        bytes32 beforePool=_snapshot(target);
        (uint256 b0,uint256 b1)=manager.balance{value:a0}(target,0,a0,a1,block.timestamp+100);
        assertEq(b0,a0); assertEq(b1,a1); assertEq(_snapshot(target),beforePool); _assertPrefunds();
    }
    function test_UnknownDuplicateAndOverlongCatalogRejected() public {
        bytes32[] memory ids=new bytes32[](2); ids[0]=target; ids[1]=target;
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); router.configureExecutionPools(ids,bytes32(uint256(1)));
        ids[1]=bytes32(uint256(3)); vm.expectRevert(); router.configureExecutionPools(ids,bytes32(uint256(1)));
        ids=new bytes32[](5); vm.expectRevert(ZZZModule.InvalidConfiguration.selector); router.configureExecutionPools(ids,bytes32(uint256(1)));
    }
    function test_SolverBoundsAndQuoteAuthentication() public {
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); router.configureSolver(3,200000,bytes32(uint256(1)));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); router.configureSolver(13,200000,bytes32(uint256(1)));
        router.configureSolver(4,100000,bytes32(uint256(1))); assertEq(router.searchIterations(),4);
        PoolKey memory key=registry.get(target).key;
        vm.expectRevert(ZZZModule.Unauthorized.selector); router.quoteCandidate(key,true,1 ether);
        vm.expectRevert(ZZZModule.Unauthorized.selector); router.unlockCallback("");
    }
    function changeCatalogDuringRefund() external { require(msg.sender==address(token)); _catalog(false,false); }
    function test_RefundCallbackCannotChangeRoutingPolicy() public {
        uint256 nativeBefore=address(this).balance; uint256 tokenBefore=token.balanceOf(address(this));
        bytes32 beforePool=_snapshot(alternate); uint64 revision=router.executionRevision();
        token.arm(address(manager),3,address(this),abi.encodeCall(this.changeCatalogDuringRefund,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.balance{value:100 ether}(target,0,100 ether,1 ether,block.timestamp+100);
        assertEq(address(this).balance,nativeBefore); assertEq(token.balanceOf(address(this)),tokenBefore);
        assertEq(_snapshot(alternate),beforePool); assertEq(router.executionRevision(),revision); _assertPrefunds();
    }
    function test_DisabledCandidateDoesNotFreezeHealthyRouting() public {
        PoolConfig memory c=registry.get(alternate); c.operationsEnabled=false; registry.configure(alternate,c);
        assertEq(_plan(100 ether,0).poolId,target);
    }
    function test_ColdDeepSingleVenueFastPathWithinExistingGasGate() public {
        _catalog(false,true); _cold(); uint256 start=gasleft();
        (uint256 a0,uint256 a1)=manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        uint256 used=start-gasleft(); emit log_named_uint("lp-routing.cold.deep.single-venue.balance-gas",used);
        assertLt(used,12_000_000); assertGt(a0,0); assertGt(a1,0); _assertPrefunds();
    }
    function test_ColdFourVenueSearchWithinExistingGasGate() public {
        CoreKey memory third=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),2000,20,IHooks(address(0)));
        CoreKey memory fourth=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),3000,60,IHooks(address(0)));
        bytes32 id3=_admit(third); bytes32 id4=_admit(fourth);
        core.initialize(third,uint160(1<<96)); core.initialize(fourth,uint160(1<<96));
        _external(third,1 ether); _external(fourth,1 ether);
        bytes32[] memory ids=new bytes32[](4); ids[0]=target; ids[1]=id3; ids[2]=id4; ids[3]=alternate;
        router.configureExecutionPools(ids,keccak256("four bounded test venues")); _cold(); uint256 start=gasleft();
        (uint256 a0,uint256 a1)=manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        uint256 used=start-gasleft(); emit log_named_uint("lp-routing.cold.four-venue.balance-gas",used);
        assertLt(used,12_000_000); assertGt(a0,0); assertGt(a1,0); _assertPrefunds();
    }
    function changeOrientationDuringRefund() external { require(msg.sender==address(token)); strategy.setRangeOrientation(target,1); }
    function test_RefundCallbackCannotChangeTargetOrientation() public {
        token.arm(address(manager),3,address(this),abi.encodeCall(this.changeOrientationDuringRefund,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.balance{value:100 ether}(target,0,100 ether,1 ether,block.timestamp+100);
        assertEq(strategy.rangeOrientation(target),0); _assertPrefunds();
    }
    function changeAndRestoreRegistryDuringRefund() external {
        require(msg.sender==address(token)); PoolConfig memory c=registry.get(target);
        uint16 previous=c.maxSlippageBps; c.maxSlippageBps=199; registry.configure(target,c);
        c.maxSlippageBps=previous; registry.configure(target,c);
    }
    function test_RefundCallbackCannotChangeAndRestoreRegistryPolicy() public {
        uint64 revision=registry.configurationRevision();
        token.arm(address(manager),3,address(this),abi.encodeCall(this.changeAndRestoreRegistryDuringRefund,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.balance{value:100 ether}(target,0,100 ether,1 ether,block.timestamp+100);
        assertEq(registry.configurationRevision(),revision); _assertPrefunds();
    }
    function changePricesDuringRefund() external {
        require(msg.sender==address(token)); first.set(100001000,block.timestamp,block.timestamp);
        second.set(100001000,block.timestamp,block.timestamp);
    }
    function test_RefundCallbackCannotChangeCapturedPriceVector() public {
        token.arm(address(manager),3,address(this),abi.encodeCall(this.changePricesDuringRefund,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.balance{value:100 ether}(target,0,100 ether,1 ether,block.timestamp+100);
        assertEq(first.answer(),1e8); assertEq(second.answer(),1e8); _assertPrefunds();
    }
    function test_ManagerRejectsERC20PairBeforeAssetPull() public {
        PoolKey memory invalid = PoolKey(address(token),address(0xBEEF),500,10,address(0));
        bytes32 id = keccak256(abi.encode(invalid));
        registry.configure(id,PoolConfig(invalid,false,true,2500,100,500,200,600,1e18,1e30));
        uint256 beforeBalance = token.balanceOf(address(this));
        uint256 beforeAllowance = token.allowance(address(this),address(manager));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.swap(id,true,100 ether,1,block.timestamp+100);
        assertEq(token.balanceOf(address(this)),beforeBalance);
        assertEq(token.allowance(address(this),address(manager)),beforeAllowance);
        _assertPrefunds();
    }
    function test_ManagerRejectsNonNativeMintEvenIfRegistryClaimsNative() public {
        PoolKey memory invalid = PoolKey(address(token),address(0xBEEF),500,10,address(0));
        bytes32 id = keccak256(abi.encode(invalid));
        registry.configure(id,PoolConfig(invalid,false,true,2500,100,500,200,600,1e18,1e30));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.mint(id,-100,100,0,100 ether,1,block.timestamp+100);
        _assertPrefunds();
    }
}
