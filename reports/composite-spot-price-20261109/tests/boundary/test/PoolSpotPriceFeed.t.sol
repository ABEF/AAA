// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {ZZZV4SpotPriceFeed} from "../src/ZZZV4SpotPriceFeed.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {MockAccess,MockFeed} from "./mocks/Mocks.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

// Explicit synthetic ABI fixtures, not canonical runtime, TVL, provider or source
// independence qualification. No real market, wallet, funds or Anvil is used.
contract SpotCoreFixture { function marker() external pure returns(uint256) { return 1; } }
contract SpotTokenFixture {
    uint8 public decimals;
    constructor(uint8 d) { decimals = d; }
    function setDecimals(uint8 d) external { decimals = d; }
}
contract SpotStateFixture {
    address public poolManager;
    uint160 public sqrt;
    int24 public tick;
    uint24 public protocol;
    uint24 public lpFee = 3000;
    uint128 public liquidity = 1e18;
    bool public exhausted;
    constructor(address core) { poolManager=core; set(uint160(2**97)); }
    function set(uint160 s) public { sqrt=s; tick=TickMath.getTickAtSqrtPrice(s); }
    function setManager(address c) external {poolManager=c;}
    function setTick(int24 t) external {tick=t;}
    function setFees(uint24 p,uint24 f) external {protocol=p; lpFee=f;}
    function setLiquidity(uint128 l) external {liquidity=l;}
    function setExhausted(bool e) external {exhausted=e;}
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24) {
        while (exhausted) {}
        return(sqrt,tick,protocol,lpFee);
    }
    function getLiquidity(bytes32) external view returns(uint128) {return liquidity;}
}

contract PoolSpotPriceFeedTest is Test {
    bytes32 constant REVIEW=keccak256("unqualified synthetic composite source test");
    SpotCoreFixture core;
    SpotTokenFixture token;
    SpotStateFixture state;
    MockFeed eth;
    ZZZV4SpotPriceFeed reader;
    function setUp() public {
        vm.warp(1_000_000);
        core=new SpotCoreFixture(); token=new SpotTokenFixture(18);
        state=new SpotStateFixture(address(core)); eth=new MockFeed(8,2000e8);
        eth.set(2000e8,block.timestamp-40,block.timestamp-30);
        reader=new ZZZV4SpotPriceFeed(_config());
    }
    function _config() internal view returns(ZZZV4SpotPriceFeed.Config memory c) {
        c.core=address(core); c.expectedCoreCodeHash=address(core).codehash;
        c.stateView=address(state); c.expectedStateViewCodeHash=address(state).codehash;
        c.key=PoolKey(Currency.wrap(address(0)),Currency.wrap(address(token)),3000,60,IHooks(address(0)));
        c.expectedPoolId=keccak256(abi.encode(c.key)); c.zzz=address(token);
        c.expectedZZZCodeHash=address(token).codehash; c.ethUsdFeed=address(eth);
        c.expectedETHFeedCodeHash=address(eth).codehash; c.maxETHAge=60; c.minimumLiquidity=1e18;
        c.reviewHash=REVIEW;
    }
    function _reject() internal view {reader.latestRoundData();}
    function testExactInvertedSpotAndOriginalETHTimestamps() public view {
        (uint80 r,int256 value,uint256 started,uint256 updated,uint80 answered)=reader.latestRoundData();
        assertEq(value,500e18); assertEq(started,block.timestamp-40); assertEq(updated,block.timestamp-30);
        assertEq(r,answered); assertGt(r,0); assertEq(reader.decimals(),18);
        assertEq(reader.config().reviewHash,REVIEW); assertEq(reader.poolId(),_config().expectedPoolId);
    }
    function testSpotChangeNeedsNoTWAPAndDoesNotFreshenETH() public {
        (uint80 beforeRound,,,,)=reader.latestRoundData();
        state.set(uint160(2**96));
        (uint80 afterRound,int256 value,uint256 started,uint256 updated,)=reader.latestRoundData();
        assertEq(value,2000e18); assertTrue(beforeRound!=afterRound);
        assertEq(started,block.timestamp-40); assertEq(updated,block.timestamp-30);
    }
    function testLiquidityAndSamePriceETHRoundChangeFingerprint() public {
        (uint80 a,,,,)=reader.latestRoundData(); state.setLiquidity(2e18);
        (uint80 b,,,,)=reader.latestRoundData(); eth.rounds(2,2);
        (uint80 c,,,,)=reader.latestRoundData(); assertTrue(a!=b && b!=c);
    }
    function testSmallAndLargeSqrtBranchesHaveKnownExactValues() public {
        state.set(uint160(2**95)); (,int256 a,,,)=reader.latestRoundData(); assertEq(a,8000e18);
        state.set(uint160(2**129)); (,int256 b,,,)=reader.latestRoundData(); assertEq(b,27);
        state.set(uint160(2**130)); (,int256 c,,,)=reader.latestRoundData(); assertEq(c,6);
    }
    function testZeroAndEighteenDecimalsNormalizeCorrectly() public {
        token=new SpotTokenFixture(0); eth=new MockFeed(0,2000); reader=new ZZZV4SpotPriceFeed(_config());
        (,int256 a,,,)=reader.latestRoundData(); assertEq(a,500);
        token=new SpotTokenFixture(6); eth=new MockFeed(18,2000e18); reader=new ZZZV4SpotPriceFeed(_config());
        (,int256 b,,,)=reader.latestRoundData(); assertEq(b,500e6);
    }
    function testFuzzExactPowerOfTwoPricesAcrossDecimals(uint8 td,uint8 fd,uint8 exponent,uint32 dollars) public {
        td=uint8(bound(td,0,18)); fd=uint8(bound(fd,0,18));
        int256 k=int256(bound(exponent,0,60))-24;
        uint256 dollar=bound(dollars,1,1_000_000);
        token=new SpotTokenFixture(td); eth=new MockFeed(fd,int256(dollar*10**fd));
        uint160 s=k>=0 ? uint160(uint256(2**96)<<uint256(k)) : uint160(uint256(2**96)>>uint256(-k));
        state.set(s); reader=new ZZZV4SpotPriceFeed(_config());
        uint256 numerator=dollar*1e18*10**td;
        uint256 expected=k>=0 ? numerator/(uint256(1e18)<<uint256(2*k)) :
            (numerator<<uint256(-2*k))/1e18;
        if (expected==0 || expected>1e36) {vm.expectRevert(); reader.latestRoundData();}
        else {(,int256 actual,,,)=reader.latestRoundData(); assertEq(uint256(actual),expected);}
    }
    function testETHFreshnessBoundaryIsExactAndReadsCannotRefreshIt() public {
        eth.set(2000e8,block.timestamp-60,block.timestamp-60); reader.latestRoundData();
        vm.warp(block.timestamp+1); vm.expectRevert(ZZZV4SpotPriceFeed.InvalidObservation.selector); _reject();
    }
    function testBadETHRoundsPricesTimesAndWideABIReject() public {
        eth.set(0,1,1); vm.expectRevert(); _reject();
        eth.set(-1,1,1); vm.expectRevert(); _reject();
        eth.set(2000e8,block.timestamp+1,block.timestamp+1); vm.expectRevert(); _reject();
        eth.set(2000e8,block.timestamp,block.timestamp-1); vm.expectRevert(); _reject();
        eth.set(2000e8,0,block.timestamp); vm.expectRevert(); _reject();
        eth.set(2000e8,block.timestamp,block.timestamp); eth.rounds(2,1); vm.expectRevert(); _reject();
        eth.rounds(0,0); vm.expectRevert(); _reject();
        vm.mockCall(address(eth),abi.encodeWithSignature("latestRoundData()"),
            abi.encode(uint256(type(uint80).max)+1,int256(2000e8),block.timestamp,block.timestamp,uint256(type(uint80).max)+1));
        vm.expectRevert(); _reject();
    }
    function testZeroLiquidityAndOneUnitBelowFloorReject() public {
        state.setLiquidity(0); vm.expectRevert(); _reject();
        state.setLiquidity(1e18-1); vm.expectRevert(); _reject();
        state.setLiquidity(1e18); reader.latestRoundData();
    }
    function testUninitializedAndNoncanonicalSlot0Reject() public {
        bytes memory call=abi.encodeWithSignature("getSlot0(bytes32)",reader.poolId());
        vm.mockCall(address(state),call,abi.encode(uint256(0),int256(0),uint256(0),uint256(3000)));
        vm.expectRevert(); _reject();
        vm.mockCall(address(state),call,abi.encode(uint256(2**160),int256(0),uint256(0),uint256(3000)));
        vm.expectRevert(); _reject();
        vm.mockCall(address(state),call,abi.encode(uint256(2**96),int256(type(int24).max)+1,uint256(0),uint256(3000)));
        vm.expectRevert(); _reject();
    }
    function testDirectionalProtocolFeeBoundsAndStaticFeeMustMatch() public {
        state.setFees(uint24(1000|(1000<<12)),3000); reader.latestRoundData();
        state.setFees(1001,3000); vm.expectRevert(); _reject();
        state.setFees(uint24(1001<<12),3000); vm.expectRevert(); _reject();
        state.setFees(0,3001); vm.expectRevert(); _reject();
    }
    function testExactDownwardCrossingTickAllowedButFalseTickRejected() public {
        state.set(uint160(2**96)); state.setTick(-1); reader.latestRoundData();
        state.setTick(-2); vm.expectRevert(); _reject();
        state.set(uint160(2**97)); state.setTick(state.tick()-1); vm.expectRevert(); _reject();
    }
    function testPinnedRuntimesAndChangedDecimalsOrStateViewParentReject() public {
        token.setDecimals(17); vm.expectRevert(); _reject(); token.setDecimals(18);
        state.setManager(address(99)); vm.expectRevert(); _reject(); state.setManager(address(core));
        vm.etch(address(core),hex"00"); vm.expectRevert(); _reject();
    }
    function testEveryRuntimePinIsRechecked() public {
        bytes memory original=address(state).code; vm.etch(address(state),hex"00"); vm.expectRevert(); _reject();
        vm.etch(address(state),original); original=address(eth).code;
        vm.etch(address(eth),hex"00"); vm.expectRevert(); _reject(); vm.etch(address(eth),original);
        vm.etch(address(token),hex"00"); vm.expectRevert(); _reject();
    }
    function testMalformedAndOversizedResponsesAndGasExhaustionRejectBoundedly() public {
        bytes memory call=abi.encodeWithSignature("getSlot0(bytes32)",reader.poolId());
        vm.mockCall(address(state),call,new bytes(127)); vm.expectRevert(); _reject();
        vm.mockCall(address(state),call,new bytes(4096)); vm.expectRevert(); _reject();
        vm.clearMockedCalls(); state.setExhausted(true); vm.expectRevert(); _reject();
    }
    function testMalformedETHAndLiquidityRepliesCannotTruncate() public {
        vm.mockCall(address(state),abi.encodeWithSignature("getLiquidity(bytes32)",reader.poolId()),abi.encode(uint256(2**128)));
        vm.expectRevert(); _reject(); vm.clearMockedCalls();
        vm.mockCall(address(eth),abi.encodeWithSignature("latestRoundData()"),new bytes(161));
        vm.expectRevert(); _reject();
    }
    function testConstructorRejectsMissingPinsAndUnreviewedConfig() public {
        ZZZV4SpotPriceFeed.Config memory c=_config(); c.reviewHash=bytes32(0);
        vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.expectedCoreCodeHash=bytes32(0); vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.expectedStateViewCodeHash=bytes32(uint256(1)); vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.expectedETHFeedCodeHash=bytes32(0); vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.expectedZZZCodeHash=bytes32(0); vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
    }
    function testConstructorRejectsWrongPoolKeyHooksDynamicFeeAndAgeOrFloor() public {
        ZZZV4SpotPriceFeed.Config memory c=_config(); c.expectedPoolId=bytes32(uint256(1));
        vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.key.hooks=IHooks(address(1)); vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.key.fee=0x800000; vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.key.currency0=Currency.wrap(address(1)); vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.key.tickSpacing=0; vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.maxETHAge=86401; vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.maxETHAge=0; vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
        c=_config(); c.minimumLiquidity=0; vm.expectRevert(); new ZZZV4SpotPriceFeed(c);
    }
    function testConstructorRejectsWrongStateViewParentAndUnsupportedDecimals() public {
        state.setManager(address(1)); vm.expectRevert(); new ZZZV4SpotPriceFeed(_config());
        state.setManager(address(core)); token.setDecimals(19); vm.expectRevert(); new ZZZV4SpotPriceFeed(_config());
        token.setDecimals(18); eth=new MockFeed(19,1); vm.expectRevert(); new ZZZV4SpotPriceFeed(_config());
    }
    function testDefaultSourceGasEnvelopeAndOracleAdmissionDisagreementAndFingerprint() public {
        (bool ok,bytes memory result)=address(reader).staticcall{gas:500_000}(abi.encodeWithSignature("latestRoundData()"));
        assertTrue(ok); assertEq(result.length,160);
        MockAccess access=new MockAccess(); ProtocolPolicyFixture.bind(address(access));
        ZZZOracle oracle=new ZZZOracle(address(access),address(0)); MockFeed second=new MockFeed(18,500e18);
        ZZZOracle.SourcePolicy memory firstPolicy=ZZZOracle.SourcePolicy(address(reader),address(reader).codehash,keccak256("fixture relative A"),60,18);
        ZZZOracle.SourcePolicy memory secondPolicy=ZZZOracle.SourcePolicy(address(second),address(second).codehash,keccak256("fixture relative B"),60,18);
        access.seal(); oracle.setDualFeed(address(token),firstPolicy,secondPolicy,300,REVIEW);
        (uint256 lower,uint256 upper,bytes32 a)=oracle.priceBounds(address(token));
        assertEq(lower,500e18); assertEq(upper,500e18);
        state.setLiquidity(2e18); (,,bytes32 b)=oracle.priceBounds(address(token)); assertTrue(a!=b);
        second.set(515e18,block.timestamp,block.timestamp); oracle.priceBounds(address(token));
        second.set(515e18+1,block.timestamp,block.timestamp); vm.expectRevert(); oracle.priceBounds(address(token));
    }
    function testNoAdministratorMethodsValueReceptionOrMutatingPriceRead() public {
        bytes32 before=keccak256(abi.encode(reader.config()));
        reader.latestRoundData(); reader.latestRoundData(); assertEq(before,keccak256(abi.encode(reader.config())));
        (bool ok,)=address(reader).call(abi.encodeWithSignature("setPool(bytes32)",bytes32(uint256(1)))); assertFalse(ok);
        vm.deal(address(this),1); (ok,)=address(reader).call{value:1}(""); assertFalse(ok);
    }
    function testExtremeRepresentableMinimumSqrtAndMaximumSqrtRejection() public {
        token=new SpotTokenFixture(0); eth=new MockFeed(18,1);
        state.set(TickMath.MIN_SQRT_PRICE); reader=new ZZZV4SpotPriceFeed(_config());
        (,int256 actual,,,)=reader.latestRoundData();
        uint256 square=uint256(TickMath.MIN_SQRT_PRICE)*TickMath.MIN_SQRT_PRICE;
        assertEq(uint256(actual),(uint256(1)<<192)/square/1e18);
        assertGt(actual,0);
        state.set(TickMath.MAX_SQRT_PRICE-1); vm.expectRevert(); _reject();
    }
    function testExactMaximumOutputAndOneUnitAboveETHBound() public {
        eth=new MockFeed(18,1e36); state.set(uint160(2**96)); reader=new ZZZV4SpotPriceFeed(_config());
        (,int256 actual,,,)=reader.latestRoundData(); assertEq(actual,1e36);
        eth.set(1e36+1,block.timestamp,block.timestamp); vm.expectRevert(); _reject();
    }
}
