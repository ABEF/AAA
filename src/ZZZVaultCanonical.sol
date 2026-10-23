// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZFees, IZZZMigration} from "./interfaces/IZZZ.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
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
    modifier onlyVault() { if (msg.sender != address(vault)) revert Unauthorized(); _; }
    modifier onlyHandoff() {
        if (msg.sender != IZZZCanonicalAccess(address(access)).canonicalHandoff()) revert Unauthorized();
        _;
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
        delete backingAssets; delete backingAmounts;
        imported = false;
        nftCount = vault.sequence(); groupCount = vault.bucketCount(); aliasCount = aliases.length;
        for (uint256 i; i < groupCount; ++i) {
            uint256 id = vault.bucketAt(i);
            Position memory p = vault.group(id);
            if (p.status == PositionStatus.None) {
                if (p.lpTokenId != 0 || p.idle0 != 0 || p.idle1 != 0 || vault.bucketTotalShares(id) != 0) revert InvalidState();
            } else if (p.status != PositionStatus.Parked || p.lpTokenId != 0 || p.homeChain != block.chainid ||
                p.homeVault != address(vault) || p.locationChain != block.chainid || p.locationVault != address(vault) ||
                !IZZZFees(access.module(Ids.FEES)).remoteSettled(id)) revert InvalidState();
            if (IZZZMigration(access.module(Ids.MIGRATION)).activePlan(id) != bytes32(0)) revert InvalidState();
        }
        ICanonicalVaultRewards rewards = ICanonicalVaultRewards(access.module(Ids.REWARDS));
        for (uint256 i; i < rewards.assetCount(); ++i) {
            address asset = rewards.assets(i);
            if (asset == address(0)) continue; // ETH reward credits are held by Rewards, never Vault principal.
            uint256 balance = IERC20(asset).balanceOf(address(vault));
            if (balance < vault.totalIdle(asset)) revert InvalidState();
            backingAssets.push(asset); backingAmounts.push(balance); released[i] = false;
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
            if (vault.sequence() != 0 || vault.bucketCount() != 0 || aliases.length != 0) revert InvalidState();
            uint256 assetCount;
            (originChain, originVault, nftCount, groupCount, aliasCount, assetCount) =
                abi.decode(record, (uint256,address,uint256,uint256,uint256,uint256));
            if (originChain == 0 || originVault == address(0) || nftCount > 1000 || groupCount > 4 || assetCount > 32) revert InvalidState();
            // Fixed length records make the complete domain independent of relay choices.
            backingAssets = new address[](assetCount); backingAmounts = new uint256[](assetCount);
            vault.canonicalWrite(0, abi.encode(nftCount));
            imported = true;
            return;
        }
        --row;
        if (row < groupCount) {
            (uint256 id, Position memory p, uint256 shares, bytes32 homePool, uint64 epoch) =
                abi.decode(record, (uint256,Position,uint256,bytes32,uint64));
            if (p.status != PositionStatus.None && p.status != PositionStatus.Parked) revert InvalidState();
            if (p.status == PositionStatus.Parked) {
                PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
                if ((epoch == 0 && (c.key.currency0 != p.homeToken0 || c.key.currency1 != p.homeToken1)) || p.lpTokenId != 0) revert InvalidState();
                p.homeChain = block.chainid; p.homeVault = address(vault); p.homeReceiver = access.module(Ids.RECEIVER);
                p.locationChain = block.chainid; p.locationVault = address(vault);
            }
            vault.canonicalWrite(2, abi.encode(id, p, shares, homePool));
            vault.migrationBudget().importComposition(id,epoch);
            return;
        }
        row -= groupCount;
        if (row < aliasCount) {
            (bytes32 pool, uint256 id) = abi.decode(record, (bytes32,uint256));
            if (pool == bytes32(0) || id == 0 || aliasBucket[pool] != 0) revert InvalidState();
            aliases.push(pool); aliasBucket[pool] = id;
            vault.canonicalWrite(3, record);
            return;
        }
        row -= aliasCount;
        if (row < nftCount) {
            (uint256 id, uint256 bucket, uint256 shares, uint256 contribution) = abi.decode(record, (uint256,uint256,uint256,uint256));
            if (id != uint256(keccak256(abi.encode(originChain, originVault, row + 1))) ||
                (bucket == 0 ? shares != 0 || contribution != 0 : shares == 0)) revert InvalidState();
            importedShares[bucket] += shares;
            vault.canonicalWrite(1, record);
            return;
        }
        row -= nftCount;
        if (row >= backingAssets.length) revert InvalidState();
        (address asset, uint256 amount, uint256 principal) = abi.decode(record, (address,uint256,uint256));
        if (asset == address(0) || principal != vault.totalIdle(asset) || amount < principal) revert InvalidState();
        for (uint256 i; i < row; ++i) if (backingAssets[i] == asset) revert InvalidState();
        backingAssets[row] = asset; backingAmounts[row] = amount;
    }
    function canonicalAssetCount() external view returns (uint256) { return backingAssets.length; }
    function canonicalBacking(uint256 index) external view returns (address asset, uint256 amount) {
        return (backingAssets[index], backingAmounts[index]);
    }
    function canonicalRelease(uint256 index, address destination) external onlyHandoff {
        uint8 state = IZZZCanonicalAccess(address(access)).canonicalState();
        if ((state != 1 && state != 4) || released[index]) revert InvalidState();
        released[index] = true;
        vault.canonicalSend(backingAssets[index], destination, backingAmounts[index]);
    }
    function canonicalAccept(uint256 index, address) external payable onlyHandoff {
        if (msg.value != 0 || IZZZCanonicalAccess(address(access)).canonicalState() != 2) revert InvalidState();
        ExactToken.push(backingAssets[index], address(vault), backingAmounts[index]);
    }
    function canonicalRestore(uint256 index, address) external payable onlyHandoff {
        if (msg.value != 0 || IZZZCanonicalAccess(address(access)).canonicalState() != 1 || !released[index]) revert InvalidState();
        ExactToken.push(backingAssets[index], address(vault), backingAmounts[index]);
        released[index] = false;
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
            if (IERC20(backingAssets[i]).balanceOf(address(vault)) < backingAmounts[i]) revert InvalidState();
        }
    }
    function canonicalActivate() external onlyHandoff {
        if (IZZZCanonicalAccess(address(access)).canonicalState() != 2) revert InvalidState();
    }
}
