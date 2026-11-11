// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";

/// @notice Optional read-only ZZZ/USD source: native-v4 ETH/ZZZ spot times a
/// reviewed ETH/USD feed. Configuration has no setter; replace the reader through
/// Oracle.setDualFeed. No funds, approvals, administrative or execution methods.
/// @dev NOT a TWAP. A v4 pool has no last-swap timestamp here. Only the original
/// ETH observation timestamps are returned. A liquidity floor is not proof of
/// bidirectional depth, highest TVL, independence or exclusion of PoPL's own LP.
/// Two readers of the same ZZZ pool remain correlated ZZZ sources.
contract ZZZV4SpotPriceFeed {
    struct Config {
        address core; bytes32 expectedCoreCodeHash;
        address stateView; bytes32 expectedStateViewCodeHash;
        PoolKey key; bytes32 expectedPoolId;
        address zzz; bytes32 expectedZZZCodeHash;
        address ethUsdFeed; bytes32 expectedETHFeedCodeHash;
        uint32 maxETHAge; uint128 minimumLiquidity; bytes32 reviewHash;
    }
    Config private settings;
    bytes32 public immutable poolId;
    uint8 public immutable zzzDecimals;
    uint8 public immutable ethFeedDecimals;
    uint8 public constant decimals = 18;
    uint256 public constant SOURCE_CALL_GAS = 150_000;
    bytes4 private constant DECIMALS = bytes4(keccak256("decimals()"));
    bytes4 private constant ROUND = bytes4(keccak256("latestRoundData()"));
    bytes4 private constant SLOT0 = bytes4(keccak256("getSlot0(bytes32)"));
    bytes4 private constant LIQUIDITY = bytes4(keccak256("getLiquidity(bytes32)"));
    bytes4 private constant MANAGER = bytes4(keccak256("poolManager()"));
    error InvalidConfiguration();
    error InvalidObservation();

    constructor(Config memory c) {
        if (c.reviewHash == bytes32(0) || c.zzz == address(0) ||
            Currency.unwrap(c.key.currency0) != address(0) || Currency.unwrap(c.key.currency1) != c.zzz ||
            address(c.key.hooks) != address(0) || c.key.fee >= 1_000_000 ||
            c.key.tickSpacing < TickMath.MIN_TICK_SPACING || c.key.tickSpacing > TickMath.MAX_TICK_SPACING ||
            c.maxETHAge == 0 || c.maxETHAge > 1 days || c.minimumLiquidity == 0 ||
            c.ethUsdFeed == c.stateView || c.ethUsdFeed == c.core) revert InvalidConfiguration();
        bytes32 id = keccak256(abi.encode(c.key));
        if (id != c.expectedPoolId) revert InvalidConfiguration();
        _pins(c);
        uint256 d = _word(c.zzz,abi.encodeWithSelector(DECIMALS));
        uint256 e = _word(c.ethUsdFeed,abi.encodeWithSelector(DECIMALS));
        if (d > 18 || e > 18 || _word(c.stateView,abi.encodeWithSelector(MANAGER)) != uint160(c.core))
            revert InvalidConfiguration();
        zzzDecimals = uint8(d); ethFeedDecimals = uint8(e); poolId = id; settings = c;
    }
    /// @notice Exact immutable-by-interface configuration, including reference key.
    function config() external view returns(Config memory) { return settings; }
    function _pin(address target,bytes32 expected) private view {
        if (target.code.length == 0 || expected == bytes32(0) || target.codehash != expected)
            revert InvalidConfiguration();
    }
    function _pins(Config memory c) private view {
        _pin(c.core,c.expectedCoreCodeHash); _pin(c.stateView,c.expectedStateViewCodeHash);
        _pin(c.zzz,c.expectedZZZCodeHash); _pin(c.ethUsdFeed,c.expectedETHFeedCodeHash);
    }
    function _read(address target,bytes memory input,uint256 size) private view returns(bytes memory data) {
        bool ok; uint256 returned; uint256 limit = SOURCE_CALL_GAS;
        assembly ("memory-safe") {
            ok := staticcall(limit,target,add(input,32),mload(input),0,0)
            returned := returndatasize()
        }
        if (!ok || returned != size) revert InvalidObservation();
        data = new bytes(size);
        assembly ("memory-safe") { returndatacopy(add(data,32),0,size) }
    }
    function _word(address target,bytes memory input) private view returns(uint256) {
        return abi.decode(_read(target,input,32),(uint256));
    }
    function _spot(Config memory c) private view returns(uint160 sqrt,bytes32 identity) {
        bytes32 id = poolId;
        bytes memory data = _read(c.stateView,abi.encodeWithSelector(SLOT0,id),128);
        (uint256 raw,int256 tick,uint256 protocol,uint256 lpFee) = abi.decode(data,(uint256,int256,uint256,uint256));
        if (raw < TickMath.MIN_SQRT_PRICE || raw >= TickMath.MAX_SQRT_PRICE ||
            tick < TickMath.MIN_TICK || tick > TickMath.MAX_TICK || protocol > type(uint24).max ||
            (protocol & 0xfff) > 1000 || (protocol >> 12) > 1000 || lpFee != c.key.fee)
            revert InvalidObservation();
        sqrt = uint160(raw);
        // At an exact downward tick crossing core stores tick=tickAtSqrt-1.
        int24 canonical = TickMath.getTickAtSqrtPrice(sqrt);
        if (tick != canonical && !(canonical > TickMath.MIN_TICK && tick == int256(canonical)-1 &&
            sqrt == TickMath.getSqrtPriceAtTick(canonical))) revert InvalidObservation();
        uint256 liquidity = _word(c.stateView,abi.encodeWithSelector(LIQUIDITY,id));
        if (liquidity > type(uint128).max || liquidity < c.minimumLiquidity) revert InvalidObservation();
        identity = keccak256(abi.encode(data,liquidity));
    }
    function _eth(Config memory c) private view returns(uint256 usd,uint256 started,uint256 updated,bytes32 identity) {
        bytes memory data = _read(c.ethUsdFeed,abi.encodeWithSelector(ROUND),160);
        (uint256 round,int256 answer,uint256 s,uint256 u,uint256 answered) =
            abi.decode(data,(uint256,int256,uint256,uint256,uint256));
        if (round == 0 || round > type(uint80).max || answered > type(uint80).max || answered < round ||
            answer <= 0 || s == 0 || s > u || u > block.timestamp || block.timestamp-u > c.maxETHAge)
            revert InvalidObservation();
        uint256 factor = 10**(18-ethFeedDecimals);
        if (uint256(answer) > 1e36/factor) revert InvalidObservation();
        usd = uint256(answer)*factor; started = s; updated = u; identity = keccak256(data);
    }
    function _quote(uint160 sqrt,uint256 ethUSD) private view returns(uint256 usd) {
        // sqrt describes raw ZZZ/ETH; invert it. Fold the token-decimal factor
        // into the numerator before division to avoid first rounding ETH to wei.
        uint256 numerator = ethUSD*(10**zzzDecimals);
        if (sqrt <= type(uint128).max) {
            uint256 ratio = uint256(sqrt)*sqrt;
            usd = Math.mulDiv(numerator,uint256(1)<<192,ratio)/1e18;
        } else {
            uint256 ratio = Math.mulDiv(sqrt,sqrt,uint256(1)<<64);
            usd = Math.mulDiv(numerator,uint256(1)<<128,ratio)/1e18;
        }
        if (usd == 0 || usd > 1e36) revert InvalidObservation();
    }
    /// @notice Spot-derived USD18 per whole ZZZ, with original ETH timestamps.
    /// Synthetic round IDs bind both observations but are not monotonic provider
    /// rounds. Reading does not freshen ETH or establish a v4 last-trade time.
    function latestRoundData() external view returns
        (uint80 roundId,int256 answer,uint256 startedAt,uint256 updatedAt,uint80 answeredInRound) {
        Config memory c = settings; _pins(c);
        if (_word(c.zzz,abi.encodeWithSelector(DECIMALS)) != zzzDecimals ||
            _word(c.ethUsdFeed,abi.encodeWithSelector(DECIMALS)) != ethFeedDecimals ||
            _word(c.stateView,abi.encodeWithSelector(MANAGER)) != uint160(c.core)) revert InvalidObservation();
        (uint160 sqrt,bytes32 poolIdentity) = _spot(c);
        uint256 ethUSD; bytes32 ethIdentity;
        (ethUSD,startedAt,updatedAt,ethIdentity) = _eth(c);
        answer = int256(_quote(sqrt,ethUSD));
        roundId = uint80(uint256(keccak256(abi.encode(address(this),block.chainid,poolId,c.reviewHash,poolIdentity,ethIdentity))));
        if (roundId == 0) roundId = 1;
        answeredInRound = roundId;
    }
}
