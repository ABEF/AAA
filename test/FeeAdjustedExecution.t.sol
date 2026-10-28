// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

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
import {MockAccess, MockFeed, MockToken} from "./mocks/Mocks.sol";
import {FactualPools, FactualPermit, FactualToken} from "./LiquidityFactualChecks.t.sol";

/// @dev TEST ONLY native admission. All swaps and fee rounding use installed v4.
contract QualityPools is FactualPools {
    uint64 public configurationRevision;
    function configure(bytes32 id, PoolConfig memory c) external { this.set(id,c); ++configurationRevision; }
}

/// @notice Defensive fee/quality checks, not attacker profitability or live feeds.
contract FeeAdjustedExecutionTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    bytes32 private constant REVIEW = keccak256("local fee-adjusted execution review");
    uint256 private constant PREFUND = 17;
    MockAccess private access;
    FactualToken private token;
    MockFeed private first;
    MockFeed private second;
    ZZZOracle private oracle;
    ZZZStrategy private strategy;
    QualityPools private registry;
    PoolManager private core;
    StateView private state;
    ZZZLiquidityManager private manager;
    ZZZLPBalancer private router;
    CoreKey private key;
    bytes32 private pool;
    receive() external payable {}

    function setUp() public {
        vm.warp(1_000_000); vm.deal(address(this),10_000_000 ether);
        access = new MockAccess(); token = new FactualToken(); token.mint(address(this),10_000_000 ether);
        core = new PoolManager(address(this)); state = new StateView(IPoolManager(address(core)));
        FactualPermit permit = new FactualPermit();
        PositionManager positions = new PositionManager(IPoolManager(address(core)),IAllowanceTransfer(address(permit)),100000,
            IPositionDescriptor(address(0)),IWETH9(address(0)));
        manager = new ZZZLiquidityManager(address(access),address(positions),address(state),address(core),address(permit));
        router = manager.balancingRouter();
        oracle = new ZZZOracle(address(access),address(0)); strategy = new ZZZStrategy(address(access));
        registry = new QualityPools(); first = new MockFeed(8,1e8); second = new MockFeed(8,1e8);
        access.bind(Ids.VAULT,address(this)); access.bind(Ids.BUYBACK,address(this));
        access.bind(Ids.LIQUIDITY,address(manager)); access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.STRATEGY,address(strategy)); access.bind(Ids.POOLS,address(registry));
        _feeds(address(0)); _feeds(address(token));
        key = CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),500,10,IHooks(address(0)));
        pool = _admit(key,1000); core.initialize(key,uint160(1<<96));
        core.setProtocolFeeController(address(this)); core.setProtocolFee(key,uint24(137|(997<<12)));
        _external(1_000_000 ether); access.seal();
        bytes32[] memory ids = new bytes32[](1); ids[0]=pool; router.configureExecutionPools(ids,REVIEW);
        token.approve(address(manager),type(uint128).max);
        vm.deal(address(manager),PREFUND); token.mint(address(manager),PREFUND);
    }
    function _feeds(address asset) private {
        oracle.setDualFeed(asset,
            ZZZOracle.SourcePolicy(address(first),address(first).codehash,keccak256("quality-source-a"),3600,8),
            ZZZOracle.SourcePolicy(address(second),address(second).codehash,keccak256("quality-source-b"),3600,8),300,REVIEW);
    }
    function _admit(CoreKey memory k,uint16 slippage) private returns(bytes32 id) {
        PoolKey memory configured = PoolKey(Currency.unwrap(k.currency0),Currency.unwrap(k.currency1),k.fee,k.tickSpacing,address(k.hooks));
        id = keccak256(abi.encode(configured));
        registry.configure(id,PoolConfig(configured,false,true,2500,100,500,slippage,600,1e18,1e30));
    }
    function _external(int256 liquidity) private { core.unlock(abi.encode(liquidity)); }
    function unlockCallback(bytes calldata data) external returns(bytes memory) {
        require(msg.sender==address(core));
        (BalanceDelta delta,) = core.modifyLiquidity(key,ModifyLiquidityParams(-60000,60000,abi.decode(data,(int256)),bytes32(0)),"");
        _settle(Currency.unwrap(key.currency0),delta.amount0()); _settle(Currency.unwrap(key.currency1),delta.amount1()); return "";
    }
    function _settle(address asset,int128 delta) private {
        if(delta==0)return;
        if(delta>0){core.take(Currency.wrap(asset),address(this),uint256(int256(delta)));return;}
        uint256 amount=uint256(-int256(delta)); core.sync(Currency.wrap(asset));
        if(asset==address(0)) assertEq(core.settle{value:amount}(),amount);
        else {token.transfer(address(core),amount);assertEq(core.settle(),amount);}
    }
    function _assertPrefunds() private view {
        assertEq(address(manager).balance,PREFUND); assertEq(token.balanceOf(address(manager)),PREFUND);
    }
    function _poolState() private view returns(bytes32) {
        (uint160 price,int24 tick,uint24 protocol,uint24 fee)=state.getSlot0(PoolId.wrap(pool));
        (uint256 growth0,uint256 growth1)=state.getFeeGrowthGlobals(PoolId.wrap(pool));
        return keccak256(abi.encode(price,tick,protocol,fee,growth0,growth1,state.getLiquidity(PoolId.wrap(pool))));
    }
    function _changeGross(uint16 limit) private {
        PoolConfig memory c=registry.get(pool);c.maxSlippageBps=limit;registry.configure(pool,c);
    }

    function test_DefaultAndSeparateCapabilityAreExplicit() public view {
        assertEq(router.LP_ROUTING_VERSION(),1);assertEq(manager.LP_ROUTING_VERSION(),1);
        assertEq(router.EXECUTION_QUALITY_VERSION(),1);assertEq(manager.EXECUTION_QUALITY_VERSION(),1);
        assertEq(router.additionalLossBps(),100);assertEq(router.MAX_ADDITIONAL_LOSS_BPS(),1000);
    }
    function test_DirectionalProtocolFeeAndCeilHaveExactRawBoundaries() public view {
        // 10,000 input, 500ppm LP; directional p=137/997 => F=637/1497.
        // Raw net inputs9,993/9,985; 99% output rounded UP gives9,894/9,886.
        assertEq(strategy.minimumOutput(pool,true,10000),9894);
        assertEq(strategy.minimumOutput(pool,false,10000),9886);
        // One net raw output cannot be rounded down to zero by the1%budget.
        assertEq(strategy.minimumOutput(pool,true,1),0);
        assertEq(strategy.minimumOutput(pool,true,2),1);
    }
    function test_ObservedProtocolFeeChangeUpdatesTheFloorWithoutReconfiguration() public {
        uint256 before=strategy.minimumOutput(pool,true,10000);
        core.setProtocolFee(key,uint24(997|(137<<12)));
        assertEq(strategy.minimumOutput(pool,true,10000),9886);
        assertEq(strategy.minimumOutput(pool,false,10000),before);
    }
    function test_SelectedHighFeeKeepsStricterGrossVenueLimit() public {
        CoreKey memory expensive=CoreKey(key.currency0,key.currency1,10020,200,IHooks(address(0)));
        bytes32 id=_admit(expensive,200);core.initialize(expensive,uint160(1<<96));
        core.setProtocolFee(expensive,uint24(1000|(1000<<12)));
        // 1.101% fee +1% extra permits2.08999%total; existing2%floor still wins.
        assertEq(strategy.minimumOutput(id,true,100 ether),98 ether);
    }
    function test_NetFeeQuoteUsesIndependentSourceBoundsRatherThanPoolSpot() public {
        second.set(101e6,block.timestamp,block.timestamp);
        // Input's upper mark1.01 and output's lower mark1, not the pool's1:1 spot.
        assertEq(strategy.minimumOutput(pool,true,10000),9992);
    }
    function test_TokenDecimalsDoNotChangeTheFeeAdjustedValueRule() public {
        MockToken six=new MockToken(6);_feeds(address(six));
        CoreKey memory decimalKey=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(six)),500,10,IHooks(address(0)));
        bytes32 id=_admit(decimalKey,1000);core.initialize(decimalKey,uint160((uint256(1)<<96)/1e6));
        assertEq(strategy.minimumOutput(id,true,1 ether),989505);
        assertEq(strategy.minimumOutput(id,false,1_000_000),989505000000000000);
    }
    function test_ZeroAndMaximumExtraCapsNeverEraseTheGrossFloor() public {
        strategy.setAdditionalLossBps(0,REVIEW);
        assertEq(strategy.minimumOutput(pool,true,10000),9993);
        strategy.setAdditionalLossBps(1000,REVIEW);
        assertEq(strategy.minimumOutput(pool,true,10000),9000);
        _changeGross(50);
        assertEq(strategy.minimumOutput(pool,true,10000),9950);
    }
    function test_ZeroFeeIsNotMistakenForMissingPolicy() public {
        CoreKey memory free=CoreKey(key.currency0,key.currency1,0,10,IHooks(address(0)));
        bytes32 id=_admit(free,1000);core.initialize(free,uint160(1<<96));
        assertEq(strategy.minimumOutput(id,true,10000),9900);
        strategy.setAdditionalLossBps(0,REVIEW);assertEq(strategy.minimumOutput(id,true,10000),10000);
    }
    function test_QualityUpdatesIncrementRevisionEvenWhenRestored() public {
        uint64 revision=strategy.executionQualityRevision();strategy.setAdditionalLossBps(101,REVIEW);
        strategy.setAdditionalLossBps(100,REVIEW);assertEq(router.additionalLossBps(),100);
        assertEq(strategy.executionQualityRevision(),revision+2);
    }
    function test_BadCapOrMissingReviewRejectsWithoutMutation() public {
        uint64 revision=strategy.executionQualityRevision();
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);strategy.setAdditionalLossBps(1001,REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);strategy.setAdditionalLossBps(100,bytes32(0));
        assertEq(router.additionalLossBps(),100);assertEq(strategy.executionQualityRevision(),revision);
    }
    function test_NonGovernanceCannotChangeQualityPolicy() public {
        vm.prank(address(0xBEEF));vm.expectRevert(ZZZModule.Unauthorized.selector);
        strategy.setAdditionalLossBps(1000,REVIEW);assertEq(router.additionalLossBps(),100);
    }
    function test_OrdinaryPauseAndPostExitRetainBuybackPolicyConfiguration() public {
        access.setPaused(true);strategy.setAdditionalLossBps(50,REVIEW);
        access.startLPExit();strategy.setAdditionalLossBps(75,REVIEW);
        assertEq(router.additionalLossBps(),75);
    }
    function test_PreparationAndCanonicalLockStillBlockConfiguration() public {
        access.setPreparation(true);vm.expectRevert();strategy.setAdditionalLossBps(50,REVIEW);
        access.setPreparation(false);access.setCanonicalState(1);
        vm.expectRevert(ZZZModule.CanonicalLocked.selector);strategy.setAdditionalLossBps(50,REVIEW);
        assertEq(router.additionalLossBps(),100);
    }
    function test_InvalidObservedStaticOrProtocolFeeFailsClosed() public {
        bytes memory query=abi.encodeCall(StateView.getSlot0,(PoolId.wrap(pool)));
        vm.mockCall(address(state),query,abi.encode(uint160(1<<96),int24(0),uint24(0),uint24(501)));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);strategy.minimumOutput(pool,true,10000);
        vm.mockCall(address(state),query,abi.encode(uint160(1<<96),int24(0),uint24(1001<<12),uint24(500)));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);strategy.minimumOutput(pool,true,10000);
        vm.clearMockedCalls();
    }
    function test_EmptyOrOverflowingQuoteInputFailsClosed() public {
        vm.expectRevert(ZZZModule.InvalidAmount.selector);strategy.minimumOutput(pool,true,0);
        vm.expectRevert(ZZZModule.InvalidAmount.selector);strategy.minimumOutput(pool,true,uint256(type(uint128).max)+1);
    }
    function test_DirectManagerSwapCannotBypassQualityWithWeakCallerMinimum() public {
        uint256 amount=15_000 ether;uint256 oldGross=amount*9/10;
        uint256 nativeBefore=address(this).balance;uint256 tokenBefore=token.balanceOf(address(this));bytes32 before=_poolState();
        vm.expectRevert(ZZZModule.Slippage.selector);
        manager.swap{value:amount}(pool,true,amount,oldGross,block.timestamp+100);
        assertEq(_poolState(),before);assertEq(address(this).balance,nativeBefore);
        assertEq(token.balanceOf(address(this)),tokenBefore);_assertPrefunds();
        strategy.setAdditionalLossBps(200,REVIEW);
        uint256 floor=strategy.minimumOutput(pool,true,amount);
        uint256 output=manager.swap{value:amount}(pool,true,amount,oldGross,block.timestamp+100);
        assertGe(output,floor);assertLt(output,amount);_assertPrefunds();
    }
    function test_StrongerCallerOutputMinimumRemainsEnforced() public {
        bytes32 before=_poolState();vm.expectRevert(ZZZModule.Slippage.selector);
        manager.swap{value:100 ether}(pool,true,100 ether,100 ether,block.timestamp+100);
        assertEq(_poolState(),before);_assertPrefunds();
    }
    function changeAndRestoreQuality() external {
        require(msg.sender==address(token));strategy.setAdditionalLossBps(101,REVIEW);strategy.setAdditionalLossBps(100,REVIEW);
    }
    function test_DirectSwapRejectsChangedRestoredQualityDuringInputPull() public {
        uint64 revision=strategy.executionQualityRevision();bytes32 before=_poolState();
        token.arm(address(manager),1,address(this),abi.encodeCall(this.changeAndRestoreQuality,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.swap(pool,false,100 ether,90 ether,block.timestamp+100);
        assertEq(strategy.executionQualityRevision(),revision);assertEq(_poolState(),before);_assertPrefunds();
    }
    function loosenAndRestoreGross() external {
        require(msg.sender==address(token));PoolConfig memory c=registry.get(pool);
        uint16 previous=c.maxSlippageBps;c.maxSlippageBps=1000;registry.configure(pool,c);
        c.maxSlippageBps=previous;registry.configure(pool,c);
    }
    function test_DirectSwapRejectsChangedRestoredVenueLimitDuringInputPull() public {
        _changeGross(200);uint64 revision=registry.configurationRevision();bytes32 before=_poolState();
        uint256 tokensBefore=token.balanceOf(address(this));uint256 nativeBefore=address(this).balance;
        token.arm(address(manager),1,address(this),abi.encodeCall(this.loosenAndRestoreGross,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.swap(pool,false,100 ether,90 ether,block.timestamp+100);
        assertEq(registry.configurationRevision(),revision);assertEq(registry.get(pool).maxSlippageBps,200);
        assertEq(token.balanceOf(address(this)),tokensBefore);assertEq(address(this).balance,nativeBefore);
        assertEq(_poolState(),before);_assertPrefunds();
    }
    function test_LPBalanceRejectsChangedRestoredQualityDuringRefund() public {
        uint64 revision=strategy.executionQualityRevision();bytes32 before=_poolState();
        token.arm(address(manager),3,address(this),abi.encodeCall(this.changeAndRestoreQuality,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.balance{value:100 ether}(pool,0,100 ether,1 ether,block.timestamp+100);
        assertEq(strategy.executionQualityRevision(),revision);assertEq(_poolState(),before);_assertPrefunds();
    }
    function test_NoSwapBalancedBudgetStillWorksAtZeroExtraCap() public {
        strategy.setAdditionalLossBps(0,REVIEW);bytes32[] memory empty=new bytes32[](0);router.configureExecutionPools(empty,REVIEW);
        (int24 lower,int24 upper,)=strategy.target(pool);uint160 q=manager.spot(pool);
        uint256 amount0=SqrtPriceMath.getAmount0Delta(q,TickMath.getSqrtPriceAtTick(upper),1e20,true);
        uint256 amount1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),q,1e20,true);
        bytes32 before=_poolState();(uint256 out0,uint256 out1)=manager.balance{value:amount0}(pool,0,amount0,amount1,block.timestamp+100);
        assertEq(out0,amount0);assertEq(out1,amount1);assertEq(_poolState(),before);_assertPrefunds();
    }
    function test_SelectedPlanCarriesAtLeastTheCurrentQualityFloor() public {
        (int24 lower,int24 upper,)=strategy.target(pool);vm.prank(address(manager));
        ZZZLPBalancer.Plan memory p=router.plan(pool,lower,upper,100 ether,0);
        assertGt(p.amountIn,0);assertGe(p.minimumOut,strategy.minimumOutput(p.poolId,p.zeroForOne,p.amountIn));
        assertGe(p.amountOut,p.minimumOut);_assertPrefunds();
    }
}
