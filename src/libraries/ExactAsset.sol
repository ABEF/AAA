// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ExactToken} from "./ExactToken.sol";

/// @notice Native ETH is an asset identity, never an ERC20 alias. Payable ingress
/// must validate its entire declared budget before using these transfer helpers.
library ExactAsset {
    using SafeERC20 for IERC20;
    error NativeTransferFailed();

    function balance(address asset, address owner) internal view returns (uint256) {
        return asset == address(0) ? owner.balance : IERC20(asset).balanceOf(owner);
    }
    function approve(address asset, address spender, uint256 amount) internal {
        if (asset != address(0)) IERC20(asset).forceApprove(spender, amount);
    }
    function push(address asset, address to, uint256 amount) internal {
        if (asset != address(0)) ExactToken.push(asset, to, amount);
        else if (amount != 0) {
            uint256 beforeBalance = address(this).balance;
            (bool ok,) = payable(to).call{value: amount}("");
            if (!ok || address(this).balance != beforeBalance - amount) revert NativeTransferFailed();
        }
    }
}
