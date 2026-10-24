// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ProtocolFeeLibrary} from "@uniswap/v4-core/src/libraries/ProtocolFeeLibrary.sol";
import {LiquidityAmounts} from "@uniswap/v4-periphery/src/libraries/LiquidityAmounts.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {IStateViewMinimal} from "../src/interfaces/IZZZ.sol";
import {MockAccess, MockPools} from "./mocks/Mocks.sol";

/// @dev Isolated constant-price planner regression, not a live venue/depth test.
contract FeeSizingOracle {
    function value(address, uint256 amount) external pure returns (uint256) { return amount; }
    function quote(address, address, uint256 amount) external pure returns (uint256) { return amount; }
    function price(address) external pure returns (uint256) { return 1 ether; }
    function tokenDecimals(address) external pure returns (uint8) { return 18; }
    function referenceX96(address, address) external pure returns (uint160) { return uint160(1 << 96); }
}

contract FeeSizingVenue {
    uint24 public protocolFee;
    uint24 public lpFee = 10020;
    function setFees(uint24 protocol, uint24 lp) external { protocolFee = protocol; lpFee = lp; }
    function stateView() external view returns (IStateViewMinimal) { return IStateViewMinimal(address(this)); }
    function spot(bytes32) external pure returns (uint160) { return uint160(1 << 96); }
    function getSlot0(bytes32) external view returns (uint160, int24, uint24, uint24) {
        return (uint160(1 << 96), 0, protocolFee, lpFee);
    }
}

contract StrategyFeeSizingTest is Test {
    ZZZStrategy private strategy;
    FeeSizingVenue private venue;
    bytes32 private poolId;
    uint160 private constant SPOT = uint160(1 << 96);

    function setUp() public {
        MockAccess access = new MockAccess();
        MockPools pools = new MockPools();
        FeeSizingOracle oracle = new FeeSizingOracle();
        venue = new FeeSizingVenue();
        PoolConfig memory config;
        // Both currencies are ERC20 identities; this is the branch the native-
        // only adjustment previously skipped. Their equal prices isolate fees.
        config.key = PoolKey(address(0x100), address(0x200), 10020, 200, address(0));
        config.operationsEnabled = true;
        config.rangeBps = 1000;
        config.maxSpotDeviationBps = 100;
        config.maxSlippageBps = 200;
        poolId = keccak256(abi.encode(config.key));
        pools.set(poolId, config);
        access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.ORACLE, address(oracle));
        access.bind(Ids.LIQUIDITY, address(venue));
        strategy = new ZZZStrategy(address(access));
    }

    function _deployed(bool zeroForOne, uint256 amountIn, uint24 swapFee) private view returns (uint256) {
        (int24 lower, int24 upper,) = strategy.target(poolId);
        uint160 a = TickMath.getSqrtPriceAtTick(lower);
        uint160 b = TickMath.getSqrtPriceAtTick(upper);
        uint256 output = Math.mulDiv(amountIn, 1_000_000 - swapFee, 1_000_000);
        uint256 amount0 = zeroForOne ? 100 ether - amountIn : output;
        uint256 amount1 = zeroForOne ? output : 100 ether - amountIn;
        uint128 liquidity = LiquidityAmounts.getLiquidityForAmounts(SPOT, a, b, amount0, amount1);
        return SqrtPriceMath.getAmount0Delta(SPOT, b, liquidity, false) +
            SqrtPriceMath.getAmount1Delta(a, SPOT, liquidity, false);
    }

    function _unadjustedInput(bool zeroForOne) private view returns (uint256) {
        (int24 lower, int24 upper,) = strategy.target(poolId);
        uint256 unit0 = SqrtPriceMath.getAmount0Delta(SPOT, TickMath.getSqrtPriceAtTick(upper), 1e18, false);
        uint256 unit1 = SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower), SPOT, 1e18, false);
        uint256 desired0 = Math.mulDiv(100 ether, unit0, unit0 + unit1);
        return zeroForOne ? 100 ether - desired0 : desired0;
    }

    function testERC20OneSidedInputsDeployNinetyNinePercentWithActualFees() public {
        venue.setFees(uint24(1000 | (1000 << 12)), 10020);
        uint24 combined = ProtocolFeeLibrary.calculateSwapFee(1000, 10020);
        assertEq(combined, 11010);
        for (uint256 i; i < 2; ++i) {
            bool zeroForOne = i == 0;
            (bool direction, uint256 input, uint256 minimum) = strategy.swapPlan(
                poolId, zeroForOne ? 100 ether : 0, zeroForOne ? 0 : 100 ether);
            assertEq(direction, zeroForOne);
            assertGe(_deployed(direction, input, combined), 99 ether);
            // The former no-fee sizing fails the actual 99% deployment floor.
            assertLt(_deployed(direction, _unadjustedInput(direction), combined), 99 ether);
            assertEq(minimum, Math.mulDiv(input, 9800, 10000));
        }
    }

    function testERC20ProtocolFeeSizingUsesOnlyTheSwapDirection() public {
        (, uint256 base0,) = strategy.swapPlan(poolId, 100 ether, 0);
        (, uint256 base1,) = strategy.swapPlan(poolId, 0, 100 ether);
        venue.setFees(1000, 10020);
        (, uint256 direction0,) = strategy.swapPlan(poolId, 100 ether, 0);
        (, uint256 unchanged1,) = strategy.swapPlan(poolId, 0, 100 ether);
        assertGt(direction0, base0);
        assertEq(unchanged1, base1);
        venue.setFees(uint24(1000 << 12), 10020);
        (, uint256 unchanged0,) = strategy.swapPlan(poolId, 100 ether, 0);
        (, uint256 direction1,) = strategy.swapPlan(poolId, 0, 100 ether);
        assertEq(unchanged0, base0);
        assertGt(direction1, base1);
    }

    function testERC20MismatchedStaticFeeAndInvalidDirectionalProtocolFailClosed() public {
        venue.setFees(0, 3000);
        vm.expectRevert(); strategy.swapPlan(poolId, 100 ether, 0);
        venue.setFees(1001, 10020);
        vm.expectRevert(); strategy.swapPlan(poolId, 100 ether, 0);
        // A fault in the unused direction is not misread as this swap's fee.
        strategy.swapPlan(poolId, 0, 100 ether);
    }

    function testERC20UnavailableFeeStateCannotFallBackToAnUnpricedSwap() public {
        vm.mockCallRevert(address(venue), abi.encodeWithSignature("getSlot0(bytes32)", poolId), hex"deadbeef");
        vm.expectRevert(); strategy.swapPlan(poolId, 100 ether, 0);
    }
}
