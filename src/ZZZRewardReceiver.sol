// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IZZZExternalFunding {
    function allocateExternal(uint256 bucket, address token, uint256 amount) external payable;
    function canonicalState() external view returns (uint8);
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
    uint256 public protected0;
    uint256 public protected1;
    uint256 public protectedNative;
    uint256 private cutoff0;
    uint256 private cutoff1;
    uint256 private cutoffNative;
    bool private cutoffSettled;
    error InvalidConfiguration();
    error InvalidFunding();
    event RewardPaymentProcessed(uint256 indexed bucketId, uint256 amount0, uint256 amount1);
    event NativeRewardWrapped(uint256 indexed bucketId, address indexed token, uint256 amount);

    constructor(uint256 bucket, address asset0, address asset1, address wrapper, address feeController) {
        if (bucket == 0 || feeController.code.length == 0 || (asset0 != address(0) && asset0.code.length == 0) ||
            asset1.code.length == 0 || asset0 == asset1 ||
            (wrapper != address(0) && (asset0 == address(0) || wrapper.code.length == 0 || (wrapper != asset0 && wrapper != asset1) ||
                IERC20Metadata(wrapper).decimals() != 18))) {
            revert InvalidConfiguration();
        }
        fees = feeController;
        bucketId = bucket;
        token0 = asset0;
        token1 = asset1;
        wrappedNative = wrapper;
        protected0 = _balance(asset0);
        protected1 = IERC20(asset1).balanceOf(address(this));
        // ETH belongs to slot 0 in a native pool. The legacy wrapper/donation
        // slot must never protect or export that same balance a second time.
        protectedNative = asset0 == address(0) ? 0 : address(this).balance;
    }
    /// @dev No external calls or storage writes: ordinary low-gas payments work.
    receive() external payable {
        if (token0 != address(0) && wrappedNative == address(0)) revert InvalidConfiguration();
    }
    function _balance(address token) private view returns (uint256) {
        return token == address(0) ? address(this).balance : IERC20(token).balanceOf(address(this));
    }
    function pending() external view returns (uint256 amount0, uint256 amount1) {
        amount0 = _balance(token0) - protected0;
        amount1 = IERC20(token1).balanceOf(address(this)) - protected1;
        if (wrappedNative != address(0)) {
            if (wrappedNative == token0) amount0 += address(this).balance - protectedNative;
            else if (wrappedNative == token1) amount1 += address(this).balance - protectedNative;
        }
    }
    function _forward(address token, uint256 amount) private {
        if (amount == 0) return;
        if (token == address(0)) {
            IZZZExternalFunding(fees).allocateExternal{value: amount}(bucketId, token, amount);
            return;
        }
        IERC20(token).forceApprove(fees, amount);
        IZZZExternalFunding(fees).allocateExternal(bucketId, token, amount);
        IERC20(token).forceApprove(fees, 0);
    }
    function sync() external nonReentrant returns (uint256 amount0, uint256 amount1) {
        uint8 state = IZZZExternalFunding(fees).canonicalState();
        if (state != 0 && state != 3) revert InvalidFunding();
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
        amount0 = _balance(token0) - protected0;
        amount1 = IERC20(token1).balanceOf(address(this)) - protected1;
        _forward(token0, amount0);
        _forward(token1, amount1);
        if (_balance(token0) != protected0 ||
            IERC20(token1).balanceOf(address(this)) != protected1) revert InvalidFunding();
        if (amount0 + amount1 != 0) emit RewardPaymentProcessed(bucketId, amount0, amount1);
    }
    modifier onlyFees() { if (msg.sender != fees) revert InvalidConfiguration(); _; }
    /// @dev Called for every receiver before any wrapping or token callback.
    function canonicalCapture() external onlyFees {
        cutoff0 = _balance(token0) - protected0;
        cutoff1 = IERC20(token1).balanceOf(address(this)) - protected1;
        cutoffNative = token0 == address(0) ? 0 : address(this).balance - protectedNative;
        if (token0 != address(0) && wrappedNative == address(0)) {
            // Forced native transfers are unsupported donations, not a way to
            // obstruct a migration of otherwise valid creator receipts.
            protectedNative += cutoffNative; cutoffNative = 0;
        }
        cutoffSettled = false;
    }
    function canonicalSettle() external onlyFees nonReentrant {
        if (cutoffSettled) revert InvalidFunding();
        cutoffSettled = true;
        uint256 a0 = cutoff0; uint256 a1 = cutoff1;
        if (cutoffNative != 0) {
            if (wrappedNative == address(0)) revert InvalidFunding();
            uint256 beforeWrapped = IERC20(wrappedNative).balanceOf(address(this));
            IWrappedNativeReward(wrappedNative).deposit{value: cutoffNative}();
            if (IERC20(wrappedNative).balanceOf(address(this)) != beforeWrapped + cutoffNative) revert InvalidFunding();
            if (wrappedNative == token0) a0 += cutoffNative; else a1 += cutoffNative;
        }
        _forward(token0, a0); _forward(token1, a1);
        if (_balance(token0) < protected0 || IERC20(token1).balanceOf(address(this)) < protected1 ||
            address(this).balance < protectedNative) revert InvalidFunding();
    }
    /// @notice Import quarantine, independently of constructor prefunding.
    function canonicalProtection(uint256 a0, uint256 a1, uint256 nativeAmount) external onlyFees {
        uint8 state = IZZZExternalFunding(fees).canonicalState();
        if ((state != 1 && state != 2) || (token0 == address(0) && nativeAmount != 0)) revert InvalidFunding();
        protected0 += a0; protected1 += a1; protectedNative += nativeAmount;
    }
    function canonicalRelease(uint8 slot, address destination, uint256 amount) external onlyFees nonReentrant {
        if (slot == 0) { protected0 -= amount; _push(token0, destination, amount); }
        else if (slot == 1) { protected1 -= amount; _push(token1, destination, amount); }
        else {
            if (slot != 2) revert InvalidFunding();
            if (token0 == address(0) && amount != 0) revert InvalidFunding();
            protectedNative -= amount;
            (bool ok,) = payable(destination).call{value: amount}("");
            if (!ok) revert InvalidFunding();
        }
    }
    function _push(address token, address destination, uint256 amount) private {
        if (amount == 0) return;
        if (token == address(0)) {
            uint256 beforeNative = address(this).balance;
            (bool ok,) = payable(destination).call{value: amount}("");
            if (!ok || address(this).balance != beforeNative - amount) revert InvalidFunding();
            return;
        }
        uint256 beforeSelf = IERC20(token).balanceOf(address(this));
        uint256 beforeTo = IERC20(token).balanceOf(destination);
        IERC20(token).safeTransfer(destination, amount);
        if (IERC20(token).balanceOf(address(this)) + amount != beforeSelf ||
            IERC20(token).balanceOf(destination) != beforeTo + amount) revert InvalidFunding();
    }
    /// @dev Allows native quarantine funding even when the receiver has no wrapper.
    function canonicalNative() external payable onlyFees {
        uint8 state = IZZZExternalFunding(fees).canonicalState();
        if (state != 1 && state != 2) revert InvalidFunding();
    }
    function canonicalQuarantinePending() external onlyFees {
        if (IZZZExternalFunding(fees).canonicalState() != 2) revert InvalidFunding();
        uint256 a0 = _balance(token0);
        uint256 a1 = IERC20(token1).balanceOf(address(this));
        if (a0 < protected0 || a1 < protected1 || address(this).balance < protectedNative) revert InvalidFunding();
        protected0 = a0; protected1 = a1; protectedNative = token0 == address(0) ? 0 : address(this).balance;
    }
    // Unsupported/constructor-prefunded assets stay quarantined. No rescue path.
}
