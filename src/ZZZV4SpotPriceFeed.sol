// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {MarketState} from "./interfaces/IZZZExecutionOracle.sol";

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
    uint256 public constant EXECUTION_SOURCE_VERSION = 1;
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
    function executionAsset() external view returns(address) { return settings.zzz; }
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
    function _state(Config memory c) private view returns(MarketState memory s) {
        bytes32 id = poolId;
        bytes memory data = _read(c.stateView,abi.encodeWithSelector(SLOT0,id),128);
        (uint256 raw,int256 tick,uint256 protocol,uint256 lpFee) = abi.decode(data,(uint256,int256,uint256,uint256));
        if (raw < TickMath.MIN_SQRT_PRICE || raw >= TickMath.MAX_SQRT_PRICE ||
            tick < TickMath.MIN_TICK || tick > TickMath.MAX_TICK || protocol > type(uint24).max ||
            (protocol & 0xfff) > 1000 || (protocol >> 12) > 1000 || lpFee != c.key.fee)
            revert InvalidObservation();
        uint256 liquidity = _word(c.stateView,abi.encodeWithSelector(LIQUIDITY,id));
        if (liquidity > type(uint128).max) revert InvalidObservation();
        s = MarketState(uint160(raw),int24(tick),uint24(protocol),uint24(lpFee),uint128(liquidity));
        _validateState(c,s);
    }
    function _validateState(Config memory c,MarketState memory s) private pure {
        uint160 sqrt=s.sqrtPriceX96;
        if(sqrt < TickMath.MIN_SQRT_PRICE || sqrt >= TickMath.MAX_SQRT_PRICE ||
            s.tick < TickMath.MIN_TICK || s.tick > TickMath.MAX_TICK ||
            (s.protocolFee & 0xfff)>1000 || s.protocolFee >> 12>1000 || s.lpFee!=c.key.fee ||
            s.liquidity<c.minimumLiquidity)revert InvalidObservation();
        // At an exact downward tick crossing core stores tick=tickAtSqrt-1.
        int24 canonical = TickMath.getTickAtSqrtPrice(sqrt);
        if (s.tick != canonical && !(canonical > TickMath.MIN_TICK && s.tick == int256(canonical)-1 &&
            sqrt == TickMath.getSqrtPriceAtTick(canonical))) revert InvalidObservation();
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
    function _configuration() private view returns(Config memory c) {
        c=settings; _pins(c);
        if (_word(c.zzz,abi.encodeWithSelector(DECIMALS)) != zzzDecimals ||
            _word(c.ethUsdFeed,abi.encodeWithSelector(DECIMALS)) != ethFeedDecimals ||
            _word(c.stateView,abi.encodeWithSelector(MANAGER)) != uint160(c.core)) revert InvalidObservation();
    }
    /// @notice Actual current pool observation for a bounded execution proof.
    function executionMarket() external view returns(address core,address stateView,bytes32 id,MarketState memory state) {
        Config memory c=_configuration();
        return(c.core,c.stateView,poolId,_state(c));
    }
    /// @notice Reconstruct the feed at a previously captured pool state using
    /// CURRENT pinned ETH data. This is a hypothetical proof, not a live price.
    function roundAt(MarketState calldata state) external view returns
        (uint80,int256,uint256,uint256,uint80) {
        Config memory c=_configuration();_validateState(c,state);
        return _roundAt(c,state);
    }
    /// @notice Bounded proof combines current market identity with the original
    /// captured-state round AND live round under ONE current pinned ETH read.
    /// No state is adopted, and no timestamp or independent ETH datum is cached.
    function executionProof(MarketState calldata captured) external view returns
        (address core,address stateView,bytes32 id,bytes32 currentStateHash,bytes32 capturedRoundHash,
         uint80 roundId,int256 answer,uint256 startedAt,uint256 updatedAt,uint80 answeredInRound) {
        Config memory c=_configuration();_validateState(c,captured);
        MarketState memory current=_state(c);
        uint256 usd;bytes32 ethIdentity;
        (usd,startedAt,updatedAt,ethIdentity)=_eth(c);
        uint80 originalId=_roundId(c,captured,ethIdentity);
        capturedRoundHash=keccak256(abi.encode(originalId,int256(_quote(captured.sqrtPriceX96,usd)),
            startedAt,updatedAt,originalId));
        roundId=_roundId(c,current,ethIdentity);answer=int256(_quote(current.sqrtPriceX96,usd));answeredInRound=roundId;
        return(c.core,c.stateView,poolId,keccak256(abi.encode(current)),
            capturedRoundHash,roundId,answer,startedAt,updatedAt,answeredInRound);
    }
    function latestRoundData() external view returns(uint80,int256,uint256,uint256,uint80) {
        Config memory c=_configuration();return _roundAt(c,_state(c));
    }
    function _roundAt(Config memory c,MarketState memory state) private view returns
        (uint80 roundId,int256 answer,uint256 startedAt,uint256 updatedAt,uint80 answeredInRound) {
        uint256 ethUSD; bytes32 ethIdentity;
        (ethUSD,startedAt,updatedAt,ethIdentity) = _eth(c);
        answer = int256(_quote(state.sqrtPriceX96,ethUSD));
        roundId=_roundId(c,state,ethIdentity);
        answeredInRound = roundId;
    }
    function _roundId(Config memory c,MarketState memory state,bytes32 ethIdentity) private view returns(uint80 roundId) {
        bytes32 poolIdentity=keccak256(abi.encode(
            abi.encode(state.sqrtPriceX96,state.tick,state.protocolFee,state.lpFee),uint256(state.liquidity)));
        roundId=uint80(uint256(keccak256(abi.encode(address(this),block.chainid,poolId,c.reviewHash,poolIdentity,ethIdentity))));
        if(roundId==0)roundId=1;
    }
}
