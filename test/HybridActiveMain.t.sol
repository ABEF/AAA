// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {ZZZLPPositionExecutor} from "../src/ZZZLPPositionExecutor.sol";
import {ZZZLPBalanceMath} from "../src/ZZZLPBalanceMath.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids,PoolKey,PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockToken} from "./mocks/Mocks.sol";

/// @dev TEST ONLY arithmetic/venue sentinels isolate guard ordering. No actual
/// Uniswap mint, feed, route, funds, market or operating qualification is implied.
contract ActiveMainPermitFixture { function approve(address,address,uint160,uint48) external {} }
contract ActiveMainMintSentinel {
    error MintWasReached();
    bool public enabled;
    bool public changeTick;
    bool public minted;
    address public parent;
    address public vault;
    PoolKey private key;
    function configure(address p,address owner,address token) external {
        parent=p;vault=owner;key=PoolKey(address(0),token,10020,200,address(0));
    }
    function allowMint(bool flip) external { enabled=true;changeTick=flip; }
    function nextTokenId() external view returns(uint256) {
        if(!enabled)revert MintWasReached();return 1;
    }
    function getPositionLiquidity(uint256) external view returns(uint128) { return minted?1:0; }
    function ownerOf(uint256) external view returns(address) { return vault; }
    function getPoolAndPositionInfo(uint256) external view returns(PoolKey memory,uint256) {
        return(key,uint256(uint24(int24(-400)))<<8|uint256(uint24(int24(600)))<<32);
    }
    function modifyLiquidities(bytes calldata,uint256) external payable {
        minted=true;
        if(changeTick)ActiveMainParentFixture(payable(parent)).setMarket(-401,-400);
        (bool ok,)=parent.call{value:msg.value}("");require(ok,"test fixed mint sink");
    }
}
contract ActiveMainArithmeticFixture {
    ZZZLPBalanceMath public immutable balanceMath=new ZZZLPBalanceMath();
    function deploymentAmounts(uint160,int24,int24,uint256 amount0,uint256)
        external pure returns(uint128,uint256) { return(1,amount0); }
}
contract ActiveMainParentFixture {
    ZZZLPPositionExecutor public immutable executor;
    PoolConfig private config;
    uint160 public price;
    uint160 public statePrice;
    int24 public tick;
    bool public hybrid=true;
    bool public ordinary=true;
    bytes32 public immutable pool;
    receive() external payable {}
    constructor(address controller,address token,address posm,address permit,address arithmetic) {
        config=PoolConfig(PoolKey(address(0),token,10020,200,address(0)),true,true,400,100,399,200,
            12 hours,100 ether,1_000_000 ether);
        pool=keccak256(abi.encode(config.key));
        executor=new ZZZLPPositionExecutor(controller,posm,address(this),address(this),permit,arithmetic);
    }
    function setMarket(int24 value,int24 rootTick) external {
        tick=value;price=TickMath.getSqrtPriceAtTick(rootTick);statePrice=price;
    }
    function setStatePrice(uint160 value) external { statePrice=value; }
    function setHybrid(bool value) external { hybrid=value; }
    function setOrdinary(bool value) external { ordinary=value; }
    function executionConfig(bytes32,bool) external view returns(PoolConfig memory) { return config; }
    function executionSpot(bytes32) external view returns(uint160) { return price; }
    function executionOrdinaryReplacement() external view returns(bool) { return ordinary; }
    function executionHybridReplacement(bytes32) external view returns(bool) { return hybrid; }
    function balanceContext(bytes32) external pure returns(bytes32) { return keccak256("test fixed context"); }
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24) { return(statePrice,tick,0,10020); }
    function attemptMint() external payable {
        executor.mint{value:msg.value}(pool,-400,600,msg.value,0,1,block.timestamp+100);
    }
}

contract HybridActiveMainTest is Test {
    ActiveMainParentFixture private parent;
    ActiveMainMintSentinel private posm;
    function setUp() public {
        MockAccess access=new MockAccess(); ProtocolPolicyFixture.bind(address(access));MockToken zzz=new MockToken(18);
        posm=new ActiveMainMintSentinel();
        ActiveMainPermitFixture permit=new ActiveMainPermitFixture();
        ActiveMainArithmeticFixture arithmetic=new ActiveMainArithmeticFixture();
        parent=new ActiveMainParentFixture(address(access),address(zzz),address(posm),address(permit),address(arithmetic));
        posm.configure(address(parent),address(this),address(zzz));
        access.bind(Ids.LIQUIDITY,address(parent));access.bind(Ids.VAULT,address(this));access.seal();
        vm.deal(address(this),1 ether);
    }
    function testInverseReferenceDeviationCanPassWhileRoundedMainIsInactive() public {
        // reference rawprice1, human ZZZ/ETH+/-4%: lower rounds to tick-400.
        // rawspot at-407 differs by~3.988%(<399bps) but is already below it.
        parent.setMarket(-407,-407);
        uint256 root=parent.price();
        uint256 fixedRoot=root*1e18/(uint256(1)<<96);
        uint256 fixedRatio=fixedRoot*fixedRoot/1e18;
        assertGe(fixedRatio,9601*1e14);
        assertLt(root,TickMath.getSqrtPriceAtTick(-400));
        vm.expectRevert(ZZZModule.Slippage.selector);parent.attemptMint{value:10000}();
    }
    function testActualLowerTickIsActiveAndReachesMintBoundary() public {
        parent.setMarket(-400,-400);
        vm.expectRevert(ActiveMainMintSentinel.MintWasReached.selector);parent.attemptMint{value:10000}();
    }
    function testExactDownwardCrossingUsesStoredTickRatherThanSqrtAlone() public {
        parent.setMarket(-401,-400);
        vm.expectRevert(ZZZModule.Slippage.selector);parent.attemptMint{value:10000}();
    }
    function testUpperTickIsInactiveAndCannotSatisfyHybridActiveFloor() public {
        parent.setMarket(600,600);
        vm.expectRevert(ZZZModule.Slippage.selector);parent.attemptMint{value:10000}();
    }
    function testDifferentPhysicalMarkCannotMasqueradeAsActiveMain() public {
        parent.setMarket(-400,-400);parent.setStatePrice(TickMath.getSqrtPriceAtTick(-399));
        vm.expectRevert(ZZZModule.Slippage.selector);parent.attemptMint{value:10000}();
    }
    function testInitialOperationRetainsItsSeparateExistingPolicy() public {
        parent.setMarket(-407,-407);parent.setHybrid(false);parent.setOrdinary(false);
        vm.expectRevert(ActiveMainMintSentinel.MintWasReached.selector);parent.attemptMint{value:10000}();
    }
    function testSuccessfulFixtureMintPreservesActiveTickAndExactNativeBudget() public {
        parent.setMarket(-400,-400);posm.allowMint(false);
        parent.attemptMint{value:10000}();
        assertTrue(posm.minted());assertEq(parent.tick(),-400);
        assertEq(address(parent).balance,10000);assertEq(address(parent.executor()).balance,0);
        assertEq(address(posm).balance,0);
    }
    function testLateTickFlipAtIdenticalSqrtRevertsMintAndAllNativeMovement() public {
        parent.setMarket(-400,-400);posm.allowMint(true);
        uint160 original=parent.price();uint256 beforeBalance=address(this).balance;
        vm.expectRevert(ZZZModule.Slippage.selector);parent.attemptMint{value:10000}();
        assertFalse(posm.minted());assertEq(parent.tick(),-400);assertEq(parent.price(),original);
        assertEq(address(this).balance,beforeBalance);assertEq(address(parent).balance,0);
        assertEq(address(parent.executor()).balance,0);assertEq(address(posm).balance,0);
    }
    function testOrdinarySingleCannotMintInactiveMainDespiteFullValueRetention() public {
        parent.setMarket(-407,-407);parent.setHybrid(false);
        vm.expectRevert(ZZZModule.Slippage.selector);parent.attemptMint{value:10000}();
        assertFalse(posm.minted());assertEq(address(parent).balance,0);
    }
    function testOrdinarySingleCompletesWithActiveMainAndExactNativeBudget() public {
        parent.setMarket(-400,-400);parent.setHybrid(false);posm.allowMint(false);
        parent.attemptMint{value:10000}();
        assertTrue(posm.minted());assertEq(parent.tick(),-400);
        assertEq(address(parent).balance,10000);assertEq(address(parent.executor()).balance,0);
    }
    function testOrdinarySingleLateTickFlipRollsBackMintAndNativeBudget() public {
        parent.setMarket(-400,-400);parent.setHybrid(false);posm.allowMint(true);
        uint256 beforeBalance=address(this).balance;
        vm.expectCall(address(parent),abi.encodeCall(parent.setMarket,(-401,-400)));
        vm.expectRevert(ZZZModule.Slippage.selector);parent.attemptMint{value:10000}();
        assertFalse(posm.minted());assertEq(parent.tick(),-400);
        assertEq(address(this).balance,beforeBalance);assertEq(address(parent).balance,0);
    }
    function testInitialOutsideMintRemainsAllowedWithoutOrdinaryReplacementContext() public {
        parent.setMarket(-407,-407);parent.setHybrid(false);parent.setOrdinary(false);posm.allowMint(false);
        parent.attemptMint{value:10000}();
        assertTrue(posm.minted());assertEq(parent.tick(),-407);
        assertEq(address(parent).balance,10000);assertEq(address(parent.executor()).balance,0);
    }
}
