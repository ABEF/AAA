// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";

/// @notice Shared price-ratio arithmetic. This performs no source reads or caching.
library ZZZPriceMath {
    error InvalidPrice(address token);

    function referenceX96(uint256 lower0, uint256 lower1, uint8 decimals0, uint8 decimals1, address token0)
        internal pure returns (uint160) {
        uint256 ratioX128 = Math.mulDiv(lower0, uint256(1) << 128, lower1);
        if (decimals1 >= decimals0) ratioX128 = Math.mulDiv(ratioX128, 10 ** (decimals1 - decimals0), 1);
        else ratioX128 /= 10 ** (decimals0 - decimals1);
        uint256 root = Math.sqrt(ratioX128);
        if (root == 0 || root > type(uint128).max) revert InvalidPrice(token0);
        return uint160(root << 32);
    }
}
