// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/// @notice Strict transfers for conventional non-rebasing, non-taxed ERC20s.
/// Balance checks do not prove a token will remain non-malicious in the future.
library ExactToken {
    using SafeERC20 for IERC20;
    error UnsupportedToken(address token);
    function pull(address token, address from, uint256 amount) internal {
        if (amount == 0) return;
        uint256 beforeBalance = IERC20(token).balanceOf(address(this));
        uint256 beforeSender = IERC20(token).balanceOf(from);
        IERC20(token).safeTransferFrom(from, address(this), amount);
        if (IERC20(token).balanceOf(address(this)) != beforeBalance + amount ||
            IERC20(token).balanceOf(from) + amount != beforeSender) revert UnsupportedToken(token);
    }
    function push(address token, address to, uint256 amount) internal {
        if (amount == 0) return;
        uint256 beforeSender = IERC20(token).balanceOf(address(this));
        uint256 beforeRecipient = IERC20(token).balanceOf(to);
        IERC20(token).safeTransfer(to, amount);
        if (IERC20(token).balanceOf(address(this)) + amount != beforeSender ||
            IERC20(token).balanceOf(to) != beforeRecipient + amount) revert UnsupportedToken(token);
    }
}
