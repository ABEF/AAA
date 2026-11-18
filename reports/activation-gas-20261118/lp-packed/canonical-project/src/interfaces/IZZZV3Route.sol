// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

interface IV3RouteFactory { function getPool(address, address, uint24) external view returns (address); }
interface IV3RoutePool {
    function factory() external view returns (address);
    function token0() external view returns (address);
    function token1() external view returns (address);
    function fee() external view returns (uint24);
}
/// @dev SwapRouter02's deadline-free single-hop tuple. Entry checks its own deadline.
interface IV3RouteRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    function factory() external view returns (address);
    function exactInputSingle(ExactInputSingleParams calldata) external payable returns (uint256);
}

