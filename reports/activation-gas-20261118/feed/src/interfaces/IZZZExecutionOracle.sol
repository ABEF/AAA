// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Exact hookless-v4 observation. Field order also matches the quote
/// proof; stored tick is not recomputed at a downward tick boundary.
struct MarketState {
    uint160 sqrtPriceX96;
    int24 tick;
    uint24 protocolFee;
    uint24 lpFee;
    uint128 liquidity;
}

/// @notice Optional immutable composite reader's execution proof surface.
/// roundAt is a hypothetical captured-state proof, never the live price feed.
interface IZZZExecutionSpotSource {
    function EXECUTION_SOURCE_VERSION() external view returns(uint256);
    function executionAsset() external view returns(address);
    function executionMarket() external view returns(address core,address stateView,bytes32 poolId,MarketState memory state);
    function roundAt(MarketState calldata state) external view returns(uint80,int256,uint256,uint256,uint80);
    function executionProof(MarketState calldata captured) external view returns
        (address core,address stateView,bytes32 poolId,bytes32 currentStateHash,bytes32 capturedRoundHash,
         uint80 roundId,int256 answer,uint256 startedAt,uint256 updatedAt,uint80 answeredInRound);
}

/// @notice Explicit transaction-only price basis. Observational Oracle methods
/// remain live. Fixed Pricing owns whole operations; Manager borrows only for
/// an explicitly authenticated Vault call, or owns its standalone operation.
interface IZZZExecutionOracle {
    function EXECUTION_PRICE_VERSION() external view returns(uint256);
    function executionActive() external view returns(bool);
    function validateExecution() external view;
    function beginExecution(address zzz) external;
    function endExecution() external;
    function beginManagerExecution(address zzz,bytes32 destination,bool borrowVault) external returns(bool owned);
    function endManagerExecution(bool owned) external;
    function executionBounds(address token) external view returns(uint256 lower,uint256 upper,bytes32 fingerprint);
    function executionReferenceX96(address token0,address token1) external view returns(uint160);
    function beforeSwap(address core,address stateView,bytes32 poolId,MarketState calldata expectedAfter) external;
    function afterSwap() external;
}

/// @notice Explicit execution variants; the ordinary Strategy views remain live.
interface IZZZExecutionStrategy {
    function executionTarget(bytes32 poolId) external view returns(int24 lower,int24 upper,uint160 referenceX96);
    function executionValidatePrice(bytes32 poolId) external view returns(uint160);
    function executionMinimumOutput(bytes32 poolId,bool zeroForOne,uint256 amountIn) external view returns(uint256);
}
