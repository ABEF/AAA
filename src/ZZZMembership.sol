// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZRewards, IZZZNFT, IZZZVault, IZZZFees, IZZZPools} from "./interfaces/IZZZ.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IPairVault, IPairAssets} from "./ZZZMigrationBudget.sol";
interface IZZZMembershipOrdinals {
    function mintedCount() external view returns (uint256);
    function tokenAtOrdinal(uint256) external view returns (uint256);
}

/// @notice Each activated canonical NFT has one equal collective-reward share.
/// Eligibility belongs to the NFT, persists through transfers and LP migration,
/// and never increases when its attached LP receives an additional contribution.
contract ZZZMembership is ZZZModule {
    mapping(uint256 => bool) public eligible;
    uint256 public totalEligible;
    event MembershipActivated(uint256 indexed nftId);
    error CanonicalState();
    constructor(address controller) ZZZModule(controller) {}
    // Membership exports eligibility records, not assets. Keep its lifecycle
    // checks without inheriting custody storage or asset-transfer entrypoints.
    modifier canonicalOnly() {
        if (msg.sender != access.canonicalHandoff()) revert CanonicalState();
        _;
    }
    modifier economic() { _economic(); _; _economic(); }
    function _state() private view returns (uint8) { return access.canonicalState(); }
    function _economic() private view { if (_state() != 0) revert CanonicalState(); }
    function _canonicalNext(uint256 row) private {
        if (_state() != 2 || canonicalCursor != row) revert CanonicalState();
        ++canonicalCursor;
    }
    /// @notice Settle funded fee dust in every canonical bucket before an entry.
    /// The Vault caps all historical local buckets, including imported custody.
    /// Unharvested venue fees retain receipt-time policy.
    function settleDust() external onlyModule(Ids.VAULT) economic {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        IZZZFees fees = IZZZFees(access.module(Ids.FEES));
        IZZZPools pools = IZZZPools(access.module(Ids.POOLS));
        uint256 count = vault.bucketCount();
        if (count > vault.MAX_BUCKETS()) revert InvalidState();
        for (uint256 i; i < count; ++i) {
            uint256 bucket = vault.bucketAt(i);
            Position memory position = vault.group(bucket);
            if (position.status != PositionStatus.Active && position.status != PositionStatus.Outbound &&
                position.status != PositionStatus.Parked) continue;
            // Dust uses immutable admitted currency identities, not a live venue
            // observation. A broken historical venue must not block healthy new
            // entry when its funded dust can still settle exactly. Current-pool
            // execution independently validates accounting and real LP backing.
            PoolConfig memory config = pools.get(position.poolId);
            fees.flushDust(bucket, config.key.currency0);
            fees.flushDust(bucket, config.key.currency1);
            if (IPairVault(address(vault)).migrationBudget().compositionEpoch(bucket) != 0) {
                IPairAssets assets = IPairAssets(access.module(Ids.REWARDS));
                if (assets.assetCount() > 33) revert InvalidState();
                for (uint256 j; j < assets.assetCount(); ++j) {
                    address token = assets.assets(j);
                    if (token != config.key.currency0 && token != config.key.currency1) fees.flushDust(bucket,token);
                }
            }
        }
    }
    function activate(uint256 id) external onlyModule(Ids.VAULT) economic {
        if (eligible[id] || IZZZNFT(access.module(Ids.NFT)).ownerOf(id) == address(0)) revert InvalidState();
        // The inactive NFT checkpoints at the current index before its one
        // collective share exists, excluding every previously published reward.
        IZZZRewards(access.module(Ids.REWARDS)).checkpointAll(id);
        eligible[id] = true;
        ++totalEligible;
        emit MembershipActivated(id);
    }
    uint256 private canonicalNFTs;
    uint256 private canonicalEligible;
    uint256 private canonicalCursor;
    function canonicalCapture() external canonicalOnly {
        if (_state() != 1) revert CanonicalState();
        canonicalNFTs = IZZZMembershipOrdinals(access.module(Ids.NFT)).mintedCount();
        canonicalEligible = totalEligible;
    }
    function canonicalSettle() external canonicalOnly {}
    function canonicalCount() public view returns (uint256) { return canonicalNFTs + 1; }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if ((_state() != 1 && _state() != 3) || row > canonicalNFTs) revert CanonicalState();
        if (row == 0) return abi.encode(canonicalNFTs, totalEligible);
        uint256 id = IZZZMembershipOrdinals(access.module(Ids.NFT)).tokenAtOrdinal(row);
        return abi.encode(id, eligible[id]);
    }
    function canonicalImport(uint256 row, bytes calldata record) external canonicalOnly {
        _canonicalNext(row);
        if (row == 0) {
            if (totalEligible != 0) revert CanonicalState();
            (canonicalNFTs, canonicalEligible) = abi.decode(record, (uint256,uint256));
            if (canonicalNFTs > 1000 || canonicalEligible > canonicalNFTs) revert CanonicalState();
            return;
        }
        (uint256 id, bool active) = abi.decode(record, (uint256,bool));
        if (row > canonicalNFTs || id != IZZZMembershipOrdinals(access.module(Ids.NFT)).tokenAtOrdinal(row)) revert CanonicalState();
        eligible[id] = active;
        if (active) ++totalEligible;
    }
    function canonicalValidate() external view {
        if (_state() == 2 && (canonicalCursor != canonicalCount() || totalEligible != canonicalEligible)) revert CanonicalState();
    }
    function canonicalAssetCount() external view returns (uint256) { return 0; }
    function canonicalActivate() external canonicalOnly {
        if (_state() != 2) revert CanonicalState();
    }
}
