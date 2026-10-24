// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZVault} from "./interfaces/IZZZ.sol";
import {ZZZFeeController, ICanonicalFeeAssets} from "./ZZZFeeController.sol";
import {ZZZRewardReceiver} from "./ZZZRewardReceiver.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";

/// @notice Seal-bound companion for complete fee/reserve state and exact
/// classified backing. FeeController retains custody and ordinary allocation.
contract ZZZFeesCanonical is ZZZModule {
    ZZZFeeController public immutable fees;
    address[] private assets;
    uint256[] private amounts;
    uint256[] private quarantine;
    uint256 private groups;
    uint256 private receivers;
    uint256 private lpAssets;
    uint256 private cursor;
    bool private captured;
    bool private imported;
    mapping(uint256 => bool) private released;
    mapping(uint256 => bool) private accepted;
    mapping(address => uint256) private prefunds;
    constructor(address controller, address feeController) ZZZModule(controller) {
        fees = ZZZFeeController(payable(feeController));
        if (feeController.code.length == 0 || address(fees.access()) != controller) revert InvalidConfiguration();
    }
    receive() external payable {}
    function _balance(address asset, address holder) private view returns (uint256) {
        return asset == address(0) ? holder.balance : IERC20(asset).balanceOf(holder);
    }
    function _requireLPAsset(address asset) private view {
        for (uint256 i; i < lpAssets; ++i) if (assets[i] == asset) return;
        revert InvalidState();
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
        imported = false;
        for (uint256 i; i < assets.length; ++i) delete accepted[i];
        delete assets; delete amounts; delete quarantine;
        groups = _vault().bucketCount(); receivers = fees.rewardReceiverCount();
        ICanonicalFeeAssets rewards = ICanonicalFeeAssets(access.module(Ids.REWARDS));
        for (uint256 i; i < rewards.assetCount(); ++i) {
            address asset = rewards.assets(i);
            uint256 raw = _balance(asset, address(fees));
            assets.push(asset); amounts.push(0);
            // Source restoration is authenticated by the handoff's exact
            // incoming delta. Do not snapshot arbitrary companion donations:
            // a nonzero prefund for every admitted asset must not inflate freeze.
            quarantine.push(raw - fees.accounted(asset) - fees.canonicalLateTotal(asset));
            released[assets.length - 1] = false;
        }
        lpAssets = assets.length;
        // The FeeController's barrier rejects capture inside ordinary ingress.
        // No external token mutation occurs until EVERY module has captured.
        fees.canonicalCaptureReceivers();
        for (uint256 i; i < receivers; ++i) {
            ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(fees.rewardReceivers(i)));
            assets.push(receiver.token0()); amounts.push(receiver.protected0());
            assets.push(receiver.token1()); amounts.push(receiver.protected1());
            assets.push(address(0)); amounts.push(receiver.protectedNative());
            for (uint256 j; j < 3; ++j) released[lpAssets + i * 3 + j] = false;
        }
        captured = true;
    }
    function canonicalSettle() external onlyHandoff {
        if (!captured) revert InvalidState();
        fees.canonicalSettleReceivers();
        for (uint256 i; i < groups; ++i) {
            uint256 id = _vault().bucketAt(i);
            for (uint256 j; j < lpAssets; ++j) fees.canonicalFlush(id, assets[j]);
        }
        for (uint256 i; i < lpAssets; ++i) {
            address asset = assets[i];
            amounts[i] = fees.accounted(asset) + quarantine[i];
            if (_balance(asset, address(fees)) < amounts[i] + fees.canonicalLateTotal(asset)) revert InvalidState();
        }
    }
    function canonicalCount() public view returns (uint256) { return 1 + lpAssets + groups * lpAssets + receivers; }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if (!captured || row >= canonicalCount()) revert InvalidState();
        if (row == 0) return abi.encode(lpAssets, groups, receivers);
        --row;
        if (row < lpAssets) {
            address asset = assets[row];
            return abi.encode(asset, fees.accounted(asset), fees.buybackBalance(asset), amounts[row], quarantine[row]);
        }
        row -= lpAssets;
        if (row < groups * lpAssets) return fees.canonicalBucketRecord(_vault().bucketAt(row / lpAssets), assets[row % lpAssets]);
        row -= groups * lpAssets;
        ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(fees.rewardReceivers(row)));
        uint256 base = lpAssets + row * 3;
        return abi.encode(receiver.bucketId(), receiver.token0(), receiver.token1(), receiver.wrappedNative(),
            amounts[base], amounts[base + 1], amounts[base + 2]);
    }
    function canonicalImport(uint256 row, bytes calldata record) external onlyHandoff {
        if (row != cursor++ || access.canonicalState() != 2) revert InvalidState();
        if (row == 0) {
            if (fees.rewardReceiverCount() != 0) revert InvalidState();
            (lpAssets, groups, receivers) = abi.decode(record, (uint256,uint256,uint256));
            if (lpAssets == 0 || lpAssets > 33 || groups > 4 || receivers > 16) revert InvalidState();
            imported = true; return;
        }
        --row;
        if (row < lpAssets) {
            (address asset, uint256 total,, uint256 backing, uint256 q) =
                abi.decode(record, (address,uint256,uint256,uint256,uint256));
            if ((row == 0 ? asset != address(0) : asset == address(0) || asset.code.length == 0) || backing != total + q) revert InvalidState();
            for (uint256 i; i < row; ++i) if (assets[i] == asset) revert InvalidState();
            assets.push(asset); amounts.push(backing); quarantine.push(q);
            prefunds[asset] = _balance(asset, address(this));
            fees.canonicalWrite(0, record); return;
        }
        row -= lpAssets;
        if (row < groups * lpAssets) {
            ZZZFeeController.CanonicalBucket memory r = abi.decode(record, (ZZZFeeController.CanonicalBucket));
            if (r.id != _vault().bucketAt(row / lpAssets) || r.asset != assets[row % lpAssets]) revert InvalidState();
            fees.canonicalWrite(1, record); return;
        }
        row -= groups * lpAssets;
        if (row >= receivers) revert InvalidState();
        (, address t0, address t1,, uint256 p0, uint256 p1, uint256 pn) =
            abi.decode(record, (uint256,address,address,address,uint256,uint256,uint256));
        fees.canonicalWrite(2, record);
        assets.push(t0); amounts.push(p0); assets.push(t1); amounts.push(p1); assets.push(address(0)); amounts.push(pn);
        if (t0 == address(0) && pn != 0) revert InvalidState();
        _requireLPAsset(t0); _requireLPAsset(t1);
    }
    function canonicalAssetCount() external view returns (uint256) { return assets.length; }
    function canonicalBacking(uint256 index) external view returns (address asset, uint256 amount) { return (assets[index], amounts[index]); }
    function canonicalRelease(uint256 index, address destination) external onlyHandoff {
        uint8 state = access.canonicalState();
        if ((state != 1 && state != 4) || index >= assets.length || released[index] ||
            (state == 4 && !accepted[index])) revert InvalidState();
        released[index] = true;
        if (index < lpAssets) fees.canonicalSend(assets[index], type(uint256).max, 0, destination, amounts[index]);
        else {
            uint256 offset = index - lpAssets;
            fees.canonicalSend(assets[index], offset / 3, uint8(offset % 3), destination, amounts[index]);
        }
    }
    function _accept(uint256 index, bool restore) private {
        if (msg.value != 0 || index >= assets.length || (!restore && accepted[index]) ||
            _balance(assets[index], address(this)) < (restore ? 0 : prefunds[assets[index]]) + amounts[index]) revert InvalidAmount();
        if (!restore) accepted[index] = true;
        if (index < lpAssets) { _push(assets[index], address(fees), amounts[index]); return; }
        uint256 offset = index - lpAssets;
        if (assets[index] != address(0)) _push(assets[index], fees.rewardReceivers(offset / 3), amounts[index]);
        fees.canonicalFundReceiver{value: assets[index] == address(0) ? amounts[index] : 0}(offset / 3, uint8(offset % 3), amounts[index], restore);
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
        if (imported && (cursor != canonicalCount() || fees.rewardReceiverCount() != receivers)) revert InvalidState();
        for (uint256 i; i < assets.length; ++i) {
            address holder = i < lpAssets ? address(fees) : fees.rewardReceivers((i - lpAssets) / 3);
            uint256 balance = assets[i] == address(0) ? holder.balance : IERC20(assets[i]).balanceOf(holder);
            if (balance < amounts[i]) revert InvalidState();
        }
    }
    function canonicalActivate() external onlyHandoff {
        if (access.canonicalState() != 2) revert InvalidState();
        fees.canonicalQuarantineReceivers();
    }
}
