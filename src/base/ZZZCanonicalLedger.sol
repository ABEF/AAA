// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IZZZCanonicalAccess} from "../interfaces/IZZZCanonical.sol";
import {ExactAsset} from "../libraries/ExactAsset.sol";

/// @dev Shared exact-backing mechanics; only the fixed controller-created handoff
/// can call these hooks. Destination prefunds are never counted as migrated backing.
abstract contract ZZZCanonicalLedger {
    address[] internal canonicalAssets;
    uint256[] internal canonicalAmounts;
    uint256[] internal canonicalPrefunds;
    mapping(uint256 => bool) internal canonicalDelivered;
    mapping(uint256 => bool) internal canonicalAccepted;
    uint256 internal canonicalCursor;
    bool internal canonicalCaptured;
    error CanonicalState();
    function _canonicalAccess() internal view virtual returns (address);
    function _state() internal view returns (uint8) {
        address controller = _canonicalAccess();
        return controller == address(0) ? 0 : IZZZCanonicalAccess(controller).canonicalState();
    }
    modifier canonicalOnly() {
        if (msg.sender != IZZZCanonicalAccess(_canonicalAccess()).canonicalHandoff()) revert CanonicalState();
        _;
    }
    modifier economic() { _economic(); _; _economic(); }
    function _economic() internal view { if (_state() != 0) revert CanonicalState(); }
    function _canonicalBeginCapture() internal {
        if (_state() != 1) revert CanonicalState();
        for (uint256 i; i < canonicalAssets.length; ++i) { delete canonicalDelivered[i]; delete canonicalAccepted[i]; }
        delete canonicalAssets; delete canonicalAmounts; delete canonicalPrefunds;
        canonicalCaptured = true;
    }
    function _canonicalBeginImport() internal {
        if (_state() != 2 || canonicalCursor != 0) revert CanonicalState();
    }
    function _canonicalNext(uint256 row) internal {
        if (_state() != 2 || canonicalCursor != row) revert CanonicalState();
        ++canonicalCursor;
    }
    function _canonicalBalance(address asset) internal view returns (uint256) {
        return asset == address(0) ? address(this).balance : IERC20(asset).balanceOf(address(this));
    }
    function _canonicalAdd(address asset, uint256 amount, uint256 prefund) internal {
        for (uint256 i; i < canonicalAssets.length; ++i) if (canonicalAssets[i] == asset) revert CanonicalState();
        canonicalAssets.push(asset); canonicalAmounts.push(amount); canonicalPrefunds.push(prefund);
    }
    function canonicalAssetCount() external view returns (uint256) { return canonicalAssets.length; }
    function canonicalBacking(uint256 i) external view returns (address, uint256) {
        return (canonicalAssets[i], canonicalAmounts[i]);
    }
    function canonicalRelease(uint256 i, address destination) external canonicalOnly {
        uint8 state = _state();
        if ((state != 1 && state != 2 && state != 4) || canonicalDelivered[i] || destination == address(0) ||
            (state != 1 && !canonicalAccepted[i])) revert CanonicalState();
        canonicalDelivered[i] = true;
        uint256 amount = canonicalAmounts[i];
        address asset = canonicalAssets[i];
        ExactAsset.push(asset,destination,amount);
    }
    function canonicalAccept(uint256 i, address) external payable canonicalOnly {
        if (_state() != 2 || canonicalAccepted[i] || msg.value != 0 ||
            _canonicalBalance(canonicalAssets[i]) < canonicalPrefunds[i] + canonicalAmounts[i]) revert CanonicalState();
        canonicalAccepted[i] = true;
    }
    function canonicalRestore(uint256 i, address) external payable canonicalOnly {
        if (_state() != 1 || !canonicalDelivered[i] || msg.value != 0 ||
            _canonicalBalance(canonicalAssets[i]) < canonicalAmounts[i]) revert CanonicalState();
        canonicalDelivered[i] = false;
    }
    function _canonicalValidateBacking() internal view {
        for (uint256 i; i < canonicalAssets.length; ++i) {
            if (_canonicalBalance(canonicalAssets[i]) < canonicalAmounts[i] + canonicalPrefunds[i]) revert CanonicalState();
        }
    }
    function canonicalActivate() external virtual canonicalOnly {
        if (_state() != 2) revert CanonicalState();
    }
}
