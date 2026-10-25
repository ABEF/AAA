// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IZZZAccess, IZZZVault, IZZZPools, IZZZMigration, IZZZNFT} from "./interfaces/IZZZ.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {ZZZMigrationBudget} from "./ZZZMigrationBudget.sol";

interface ICanonicalVaultState is IZZZVault {
    function migrationBudget() external view returns (ZZZMigrationBudget);
    function MINT_PRICE() external view returns (uint256);
    function sequence() external view returns (uint256);
    function contributionUSD(uint256 id) external view returns (uint256);
    function totalIdle(address asset) external view returns (uint256);
    function canonicalWrite(uint8 kind, bytes calldata row) external;
    function canonicalSend(address asset, address destination, uint256 amount) external;
    function canonicalBarrier() external;
}
interface ICanonicalVaultNFT { function tokenAtOrdinal(uint256 ordinal) external view returns (uint256); }
interface ICanonicalVaultRewards {
    function assetCount() external view returns (uint256);
    function assets(uint256 index) external view returns (address);
}

/// @notice Immutable Vault companion. No configurable executor or delegatecall.
/// It records the finite export domain and moves only source-captured backing.
contract ZZZVaultCanonical {
    IZZZAccess public immutable access;
    ICanonicalVaultState public immutable vault;
    uint256 public originChain;
    address public originVault;
    bytes32[] public aliases;
    mapping(bytes32 => uint256) public aliasBucket;
    uint256 private nftCount;
    uint256 private groupCount;
    uint256 private aliasCount;
    address[] private backingAssets;
    uint256[] private backingAmounts;
    mapping(uint256 => bool) private released;
    mapping(uint256 => bool) private accepted;
    mapping(uint256 => uint256) private companionPrefund;
    mapping(uint256 => uint256) private importedShares;
    uint256 private cursor;
    bool private captured;
    bool private imported;
    error Unauthorized();
    error InvalidState();
    error InvalidAmount();

    constructor(address controller, address vaultController, uint256 chain) {
        access = IZZZAccess(controller);
        if (vaultController.code.length == 0 || IZZZAccess(controller).module(Ids.VAULT) != vaultController ||
            chain == 0 || IZZZVault(vaultController).canonicalChainId() != chain) revert InvalidState();
        vault = ICanonicalVaultState(vaultController);
        originChain = chain;
        originVault = vaultController;
    }
    receive() external payable {}
    modifier onlyVault() { if (msg.sender != address(vault)) revert Unauthorized(); _; }
    modifier onlyBudget() {
        if (msg.sender != address(vault.migrationBudget())) revert Unauthorized();
        _;
    }
    modifier onlyHandoff() {
        if (msg.sender != IZZZCanonicalAccess(address(access)).canonicalHandoff()) revert Unauthorized();
        _;
    }
    /// @notice Read-only custody checks delegated by this fixed Vault's Budget.
    /// These views cannot write ownership, approve tokens or move backing.
    function validateOwner(uint256 id,address caller,bool minted,bool activation)
        external view onlyBudget returns(address entry) {
        if (block.chainid != vault.canonicalChainId() || !minted) revert Unauthorized();
        if (activation && (vault.nftBucket(id) != 0 || !IZZZNFT(access.module(Ids.NFT)).traitsReady(id))) revert InvalidState();
        if (IZZZNFT(access.module(Ids.NFT)).ownerOf(id) == caller) return address(0);
        entry = IZZZPools(access.module(Ids.POOLS)).activationEntry();
        if (entry == address(0) || caller != entry) revert Unauthorized();
    }
    function validateContribution(uint256 id,uint256 bucket,uint256 inputUSD,uint256 inputTotal,
        uint128 minimumLiquidity,bool activation) external view onlyBudget returns(address,address,uint16) {
        Position memory p = vault.group(bucket);
        if (p.status != PositionStatus.Active ||
            IZZZMigration(access.module(Ids.MIGRATION)).activePlan(bucket) != bytes32(0)) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if (!c.depositsEnabled || inputTotal == 0 || minimumLiquidity == 0 ||
            (activation && inputUSD < 100e18) || (!activation && inputUSD < 5e18) || inputUSD < c.minDepositUSD ||
            vault.contributionUSD(id) + inputUSD > c.maxPositionUSD) revert InvalidAmount();
        return(c.key.currency0,c.key.currency1,c.maxSlippageBps);
    }
    function mintIdentity(uint256 ordinal) external view returns (uint256) {
        return uint256(keccak256(abi.encode(originChain, originVault, ordinal)));
    }
    function validateMint(uint256 value,uint256 ordinal) external view onlyVault returns (uint256) {
        if (block.chainid != vault.canonicalChainId()) revert InvalidState();
        if (value != vault.MINT_PRICE()) revert InvalidAmount();
        return uint256(keccak256(abi.encode(originChain,originVault,ordinal)));
    }
    function bucketIdentity(bytes32 pool) external view returns (uint256) {
        return uint256(keccak256(abi.encode(originChain, originVault, pool)));
    }
    function registerAlias(bytes32 pool, uint256 bucket) external onlyVault {
        uint256 old = aliasBucket[pool];
        if (old != 0 && old != bucket) revert InvalidState();
        if (old == 0) { aliases.push(pool); aliasBucket[pool] = bucket; }
    }
    function canonicalCapture() external onlyHandoff {
        if (IZZZCanonicalAccess(address(access)).canonicalState() != 1) revert InvalidState();
        vault.canonicalBarrier();
        // A proved abort may be followed by a fresh freeze. Only snapshot caches
        // reset; ordinary shares, reservations and principal remain untouched.
        bool reset = captured || imported;
        delete backingAssets; delete backingAmounts;
        imported = false;
        nftCount = vault.sequence(); groupCount = vault.bucketCount(); aliasCount = aliases.length;
        for (uint256 i; i < groupCount; ++i) {
            uint256 id = vault.bucketAt(i);
            Position memory p = vault.group(id);
            if (p.status == PositionStatus.None) {
                if (p.lpTokenId != 0 || p.idle0 != 0 || p.idle1 != 0 || vault.bucketTotalShares(id) != 0) revert InvalidState();
            } else if (p.status != PositionStatus.Parked || p.lpTokenId != 0) revert InvalidState();
            if (IZZZMigration(access.module(Ids.MIGRATION)).activePlan(id) != bytes32(0)) revert InvalidState();
        }
        ICanonicalVaultRewards rewards = ICanonicalVaultRewards(access.module(Ids.REWARDS));
        if (rewards.assetCount() > 33) revert InvalidState();
        for (uint256 i; i < rewards.assetCount(); ++i) {
            address asset = rewards.assets(i);
            for (uint256 j; j < i; ++j) if (backingAssets[j] == asset) revert InvalidState();
            uint256 balance = ExactAsset.balance(asset,address(vault));
            if (balance < vault.totalIdle(asset)) revert InvalidState();
            backingAssets.push(asset); backingAmounts.push(balance);
            // A fresh source has zero flags; recapture/successor capture
            // clears old delivery flags without snapshotting unrelated prefunds.
            if (reset) { released[i] = false; accepted[i] = false; }
        }
        captured = true;
    }
    function canonicalSettle() external onlyHandoff { if (!captured) revert InvalidState(); }
    function canonicalCount() public view returns (uint256) {
        return 1 + groupCount + aliasCount + nftCount + backingAssets.length;
    }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if (!captured || row >= canonicalCount()) revert InvalidState();
        if (row == 0) return abi.encode(originChain, originVault, nftCount, groupCount, aliasCount, backingAssets.length);
        --row;
        if (row < groupCount) {
            uint256 id = vault.bucketAt(row);
            return abi.encode(id, vault.group(id), vault.bucketTotalShares(id), vault.homePoolId(id),
                vault.migrationBudget().compositionEpoch(id));
        }
        row -= groupCount;
        if (row < aliasCount) return abi.encode(aliases[row], aliasBucket[aliases[row]]);
        row -= aliasCount;
        if (row < nftCount) {
            uint256 id = ICanonicalVaultNFT(access.module(Ids.NFT)).tokenAtOrdinal(row + 1);
            return abi.encode(id, vault.nftBucket(id), vault.sharesOf(id), vault.contributionUSD(id));
        }
        row -= nftCount;
        address asset = backingAssets[row];
        // Retain the exact principal/quarantine classification even when raw
        // balances subsequently increase through unsolicited transfers.
        return abi.encode(asset, backingAmounts[row], vault.totalIdle(asset));
    }
    function canonicalImport(uint256 row, bytes calldata record) external onlyHandoff {
        if (IZZZCanonicalAccess(address(access)).canonicalState() != 2 || row != cursor++) revert InvalidState();
        if (row == 0) {
            if (record.length != 192) revert InvalidState();
            if (vault.sequence() != 0 || vault.bucketCount() != 0 || aliases.length != 0) revert InvalidState();
            uint256 assetCount;
            (originChain, originVault, nftCount, groupCount, aliasCount, assetCount) =
                abi.decode(record, (uint256,address,uint256,uint256,uint256,uint256));
            if (originChain == 0 || originVault == address(0) || nftCount > 1000 || groupCount > 4 || assetCount > 33) revert InvalidState();
            // Fixed length records make the complete domain independent of relay choices.
            backingAssets = new address[](assetCount); backingAmounts = new uint256[](assetCount);
            vault.canonicalWrite(0, abi.encode(nftCount));
            imported = true;
            return;
        }
        --row;
        if (row < groupCount) {
            if (record.length != 384) revert InvalidState();
            (uint256 id, Position memory p, uint256 shares, bytes32 homePool, uint64 epoch) =
                abi.decode(record, (uint256,Position,uint256,bytes32,uint64));
            if (p.status != PositionStatus.None && p.status != PositionStatus.Parked) revert InvalidState();
            if (p.status == PositionStatus.Parked) {
                // The admitted pool key supplies the actual local currencies.
                // Exact backing rows below must fund their attributed idle;
                // there is no remote/home token identity to reinterpret.
                IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
                if (p.lpTokenId != 0) revert InvalidState();
            }
            vault.canonicalWrite(2, abi.encode(id, p, shares, homePool));
            vault.migrationBudget().importComposition(id,epoch);
            return;
        }
        row -= groupCount;
        if (row < aliasCount) {
            if (record.length != 64) revert InvalidState();
            (bytes32 pool, uint256 id) = abi.decode(record, (bytes32,uint256));
            if (pool == bytes32(0) || id == 0 || aliasBucket[pool] != 0) revert InvalidState();
            aliases.push(pool); aliasBucket[pool] = id;
            vault.canonicalWrite(3, record);
            return;
        }
        row -= aliasCount;
        if (row < nftCount) {
            if (record.length != 128) revert InvalidState();
            (uint256 id, uint256 bucket, uint256 shares, uint256 contribution) = abi.decode(record, (uint256,uint256,uint256,uint256));
            if (id != uint256(keccak256(abi.encode(originChain, originVault, row + 1))) ||
                (bucket == 0 ? shares != 0 || contribution != 0 : shares == 0)) revert InvalidState();
            importedShares[bucket] += shares;
            vault.canonicalWrite(1, record);
            return;
        }
        row -= nftCount;
        if (row >= backingAssets.length) revert InvalidState();
        if (record.length != 96) revert InvalidState();
        (address asset, uint256 amount, uint256 principal) = abi.decode(record, (address,uint256,uint256));
        if (principal != vault.totalIdle(asset) || amount < principal) revert InvalidState();
        for (uint256 i; i < row; ++i) if (backingAssets[i] == asset) revert InvalidState();
        backingAssets[row] = asset; backingAmounts[row] = amount;
        companionPrefund[row] = ExactAsset.balance(asset,address(this));
    }
    function canonicalAssetCount() external view returns (uint256) { return backingAssets.length; }
    function canonicalBacking(uint256 index) external view returns (address asset, uint256 amount) {
        return (backingAssets[index], backingAmounts[index]);
    }
    function canonicalRelease(uint256 index, address destination) external onlyHandoff {
        uint8 state = IZZZCanonicalAccess(address(access)).canonicalState();
        if ((state != 1 && state != 4) || released[index] || (state == 4 && !accepted[index])) revert InvalidState();
        released[index] = true;
        vault.canonicalSend(backingAssets[index], destination, backingAmounts[index]);
    }
    function canonicalAccept(uint256 index, address) external payable onlyHandoff {
        if (msg.value != 0 || IZZZCanonicalAccess(address(access)).canonicalState() != 2 || accepted[index]) revert InvalidState();
        accepted[index] = true;
        _forward(index,false);
    }
    function canonicalRestore(uint256 index, address) external payable onlyHandoff {
        if (msg.value != 0 || IZZZCanonicalAccess(address(access)).canonicalState() != 1 || !released[index]) revert InvalidState();
        _forward(index,true);
        released[index] = false;
    }
    // Funding was transferred into this companion by canonicalRelease before
    // this zero-value acknowledgment. Prefunds cannot substitute for that row.
    function _forward(uint256 index,bool restore) private {
        address asset=backingAssets[index]; uint256 amount=backingAmounts[index];
        // Source restore follows Handoff.returnFunds' exact balance-delta check.
        // Capturing source prefunds would permit 33 dust donations to impose
        // cold storage costs on freeze. Imported successors must not reuse an
        // old importer baseline when they later become a source.
        uint256 prefund=restore?0:companionPrefund[index];
        if (ExactAsset.balance(asset,address(this)) < prefund+amount) revert InvalidState();
        ExactAsset.push(asset,address(vault),amount);
    }
    function canonicalValidate() external view {
        if (imported) {
            if (cursor != canonicalCount() || vault.bucketCount() != groupCount || aliases.length != aliasCount) revert InvalidState();
            for (uint256 i; i < groupCount; ++i) {
                uint256 id = vault.bucketAt(i);
                if (importedShares[id] != vault.bucketTotalShares(id)) revert InvalidState();
            }
        } else if (!captured) revert InvalidState();
        for (uint256 i; i < backingAssets.length; ++i) {
            if (ExactAsset.balance(backingAssets[i],address(vault)) < backingAmounts[i]) revert InvalidState();
        }
    }
    function canonicalActivate() external onlyHandoff {
        if (IZZZCanonicalAccess(address(access)).canonicalState() != 2) revert InvalidState();
    }
}
