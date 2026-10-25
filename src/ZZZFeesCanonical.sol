// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZVault} from "./interfaces/IZZZ.sol";
import {ZZZFeeController, ICanonicalFeeAssets} from "./ZZZFeeController.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";

/// @notice LP-only fee/reserve export with exact classified backing.
/// Local-position LP-only V4 handoff rows are incompatible with older position/inbox/bridge rows.
contract ZZZFeesCanonical is ZZZModule {
    ZZZFeeController public immutable fees;
    address[] private assets;
    uint256[] private amounts;
    uint256[] private quarantine;
    uint256 private groups;
    uint256 private lpAssets;
    uint256 private cursor;
    bool private captured;
    bool private imported;
    mapping(uint256 => bool) private released;
    mapping(uint256 => bool) private accepted;
    mapping(address => uint256) private prefunds;
    constructor(address controller, address feeController) ZZZModule(controller) {
        fees = ZZZFeeController(payable(feeController));
        if (feeController.code.length == 0 || address(fees.access()) != controller || fees.FEE_INTAKE_VERSION() != 1) revert InvalidConfiguration();
    }
    receive() external payable {}
    function _balance(address asset, address holder) private view returns (uint256) {
        return asset == address(0) ? holder.balance : IERC20(asset).balanceOf(holder);
    }
    function _push(address asset, address destination, uint256 amount) private {
        if (asset != address(0)) { ExactToken.push(asset, destination, amount); return; }
        if (amount == 0) return;
        uint256 beforeBalance = address(this).balance;
        (bool ok,) = payable(destination).call{value: amount}("");
        if (!ok || address(this).balance != beforeBalance - amount) revert InvalidState();
    }
    function _vault() private view returns (IZZZVault) { return IZZZVault(access.module(Ids.VAULT)); }
    function canonicalCapture() external onlyHandoff {
        // Reject snapshotting from an ordinary allocation/reserve-send callback.
        fees.canonicalBarrier();
        imported = false;
        for (uint256 i; i < assets.length; ++i) delete accepted[i];
        delete assets; delete amounts; delete quarantine;
        groups = _vault().bucketCount();
        ICanonicalFeeAssets rewards = ICanonicalFeeAssets(access.module(Ids.REWARDS));
        lpAssets = rewards.assetCount();
        if (lpAssets == 0 || lpAssets > 33 || groups > 4) revert InvalidState();
        for (uint256 i; i < lpAssets; ++i) {
            address asset = rewards.assets(i);
            uint256 raw = _balance(asset, address(fees));
            assets.push(asset); amounts.push(0);
            // Donations remain quarantined, never converted into new income.
            // Restores are authenticated by the handoff's exact incoming delta;
            // arbitrary companion prefunds do not inflate the source snapshot.
            quarantine.push(raw - fees.accounted(asset));
            released[i] = false;
        }
        captured = true;
    }
    function canonicalSettle() external onlyHandoff {
        if (!captured) revert InvalidState();
        for (uint256 i; i < groups; ++i) {
            uint256 id = _vault().bucketAt(i);
            for (uint256 j; j < lpAssets; ++j) fees.canonicalFlush(id, assets[j]);
        }
        for (uint256 i; i < lpAssets; ++i) {
            amounts[i] = fees.accounted(assets[i]) + quarantine[i];
            if (_balance(assets[i], address(fees)) < amounts[i]) revert InvalidState();
        }
    }
    function canonicalCount() public view returns (uint256) { return 1 + lpAssets + groups * lpAssets; }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if (!captured || row >= canonicalCount()) revert InvalidState();
        if (row == 0) return abi.encode(lpAssets, groups);
        --row;
        if (row < lpAssets) {
            address asset = assets[row];
            return abi.encode(asset, fees.accounted(asset), fees.buybackBalance(asset), amounts[row], quarantine[row]);
        }
        row -= lpAssets;
        return fees.canonicalBucketRecord(_vault().bucketAt(row / lpAssets), assets[row % lpAssets]);
    }
    function canonicalImport(uint256 row, bytes calldata record) external onlyHandoff {
        if (row != cursor++ || access.canonicalState() != 2) revert InvalidState();
        if (row == 0) {
            if (record.length != 64) revert InvalidState();
            (lpAssets, groups) = abi.decode(record, (uint256,uint256));
            if (lpAssets == 0 || lpAssets > 33 || groups > 4) revert InvalidState();
            imported = true; return;
        }
        --row;
        if (row < lpAssets) {
            if (record.length != 160) revert InvalidState();
            (address asset, uint256 total,, uint256 backing, uint256 q) =
                abi.decode(record, (address,uint256,uint256,uint256,uint256));
            if ((row == 0 ? asset != address(0) : asset == address(0) || asset.code.length == 0) || backing != total + q) revert InvalidState();
            for (uint256 i; i < row; ++i) if (assets[i] == asset) revert InvalidState();
            assets.push(asset); amounts.push(backing); quarantine.push(q);
            prefunds[asset] = _balance(asset, address(this));
            fees.canonicalWrite(0, record); return;
        }
        row -= lpAssets;
        if (row >= groups * lpAssets || record.length != 128) revert InvalidState();
        ZZZFeeController.CanonicalBucket memory r = abi.decode(record, (ZZZFeeController.CanonicalBucket));
        if (r.id != _vault().bucketAt(row / lpAssets) || r.asset != assets[row % lpAssets]) revert InvalidState();
        fees.canonicalWrite(1, record);
    }
    function canonicalAssetCount() external view returns (uint256) { return assets.length; }
    function canonicalBacking(uint256 index) external view returns (address asset, uint256 amount) { return (assets[index], amounts[index]); }
    function canonicalRelease(uint256 index, address destination) external onlyHandoff {
        uint8 state = access.canonicalState();
        if ((state != 1 && state != 4) || index >= assets.length || released[index] ||
            (state == 4 && !accepted[index])) revert InvalidState();
        released[index] = true;
        fees.canonicalSend(assets[index], destination, amounts[index]);
    }
    function _accept(uint256 index, bool restore) private {
        if (msg.value != 0 || index >= assets.length || (!restore && accepted[index]) ||
            _balance(assets[index], address(this)) < (restore ? 0 : prefunds[assets[index]]) + amounts[index]) revert InvalidAmount();
        if (!restore) accepted[index] = true;
        _push(assets[index], address(fees), amounts[index]);
    }
    function canonicalAccept(uint256 index, address) external payable onlyHandoff {
        if (access.canonicalState() != 2) revert InvalidState();
        _accept(index, false);
    }
    function canonicalRestore(uint256 index, address) external payable onlyHandoff {
        if (access.canonicalState() != 1 || !released[index]) revert InvalidState();
        _accept(index, true); released[index] = false;
    }
    function canonicalValidate() external view {
        if ((!captured && !imported) || (imported && cursor != canonicalCount())) revert InvalidState();
        for (uint256 i; i < assets.length; ++i) if (_balance(assets[i], address(fees)) < amounts[i]) revert InvalidState();
    }
    function canonicalActivate() external onlyHandoff {
        if (access.canonicalState() != 2 || !imported || cursor != canonicalCount()) revert InvalidState();
    }
}
