// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IZZZExternalFunding {
    function allocateExternal(uint256 bucket, address token, uint256 amount) external;
}
interface IWrappedNativeReward {
    function deposit() external payable;
}

/// @notice Permanent plain-transfer inbox for one canonical shared LP bucket.
/// Anyone may process payments; nobody may withdraw or change their destination.
/// Raw transfers are pending until sync. Constructor-time prefunding is quarantined.
contract ZZZRewardReceiver is ReentrancyGuard {
    using SafeERC20 for IERC20;
    address public immutable fees;
    uint256 public immutable bucketId;
    address public immutable token0;
    address public immutable token1;
    address public immutable wrappedNative;
    uint256 public immutable protected0;
    uint256 public immutable protected1;
    uint256 public immutable protectedNative;
    error InvalidConfiguration();
    error InvalidFunding();
    event RewardPaymentProcessed(uint256 indexed bucketId, uint256 amount0, uint256 amount1);
    event NativeRewardWrapped(uint256 indexed bucketId, address indexed token, uint256 amount);

    constructor(uint256 bucket, address asset0, address asset1, address wrapper) {
        if (bucket == 0 || msg.sender.code.length == 0 || asset0.code.length == 0 ||
            asset1.code.length == 0 || asset0 == asset1 ||
            (wrapper != address(0) && (wrapper.code.length == 0 || (wrapper != asset0 && wrapper != asset1) ||
                IERC20Metadata(wrapper).decimals() != 18))) {
            revert InvalidConfiguration();
        }
        fees = msg.sender;
        bucketId = bucket;
        token0 = asset0;
        token1 = asset1;
        wrappedNative = wrapper;
        protected0 = IERC20(asset0).balanceOf(address(this));
        protected1 = IERC20(asset1).balanceOf(address(this));
        protectedNative = address(this).balance;
    }
    /// @dev No external calls or storage writes: ordinary low-gas payments work.
    receive() external payable {
        if (wrappedNative == address(0)) revert InvalidConfiguration();
    }
    function pending() external view returns (uint256 amount0, uint256 amount1) {
        amount0 = IERC20(token0).balanceOf(address(this)) - protected0;
        amount1 = IERC20(token1).balanceOf(address(this)) - protected1;
        if (wrappedNative == token0) amount0 += address(this).balance - protectedNative;
        else if (wrappedNative == token1) amount1 += address(this).balance - protectedNative;
    }
    function _forward(address token, uint256 amount) private {
        if (amount == 0) return;
        IERC20(token).forceApprove(fees, amount);
        IZZZExternalFunding(fees).allocateExternal(bucketId, token, amount);
        IERC20(token).forceApprove(fees, 0);
    }
    function sync() external nonReentrant returns (uint256 amount0, uint256 amount1) {
        if (wrappedNative != address(0)) {
            uint256 nativeAmount = address(this).balance - protectedNative;
            if (nativeAmount != 0) {
                uint256 beforeWrapped = IERC20(wrappedNative).balanceOf(address(this));
                IWrappedNativeReward(wrappedNative).deposit{value: nativeAmount}();
                if (IERC20(wrappedNative).balanceOf(address(this)) != beforeWrapped + nativeAmount ||
                    address(this).balance != protectedNative) revert InvalidFunding();
                emit NativeRewardWrapped(bucketId, wrappedNative, nativeAmount);
            }
        }
        amount0 = IERC20(token0).balanceOf(address(this)) - protected0;
        amount1 = IERC20(token1).balanceOf(address(this)) - protected1;
        _forward(token0, amount0);
        _forward(token1, amount1);
        if (IERC20(token0).balanceOf(address(this)) != protected0 ||
            IERC20(token1).balanceOf(address(this)) != protected1) revert InvalidFunding();
        if (amount0 + amount1 != 0) emit RewardPaymentProcessed(bucketId, amount0, amount1);
    }
    // Unsupported/constructor-prefunded assets stay quarantined. No rescue path.
}
