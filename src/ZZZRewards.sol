// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZMembership, IZZZNFT, IZZZVault} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ZZZCanonicalLedger} from "./base/ZZZCanonicalLedger.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";

interface IZZZRewardNFTOrdinals {
    function mintedCount() external view returns (uint256);
    function tokenAtOrdinal(uint256) external view returns (uint256);
}

contract ZZZRewards is ZZZModule, ReentrancyGuard, ZZZCanonicalLedger {
    uint256 public constant SCALE = 1e36;
    uint256 public constant MAX_ASSETS = 32;
    address[] public assets;
    mapping(address => bool) public isAsset;
    mapping(address => uint256) public index;
    mapping(address => uint256) public liabilities;
    mapping(address => uint256) public orphaned;
    mapping(uint256 => mapping(address => uint256)) public individual;
    mapping(uint256 => mapping(address => uint256)) public collective;
    mapping(uint256 => mapping(address => uint256)) public paidIndex;
    mapping(uint256 => mapping(address => uint256)) public fraction;
    // Owner rewards follow nonredeemable NFT shares in a shared LP bucket.
    // Collective rewards are shared equally by activated canonical NFTs.
    mapping(uint256 => mapping(address => uint256)) public ownerIndex;
    mapping(uint256 => mapping(address => uint256)) public paidOwnerIndex;
    mapping(uint256 => mapping(address => uint256)) public ownerFraction;
    event AssetAdded(address indexed token);
    event PoolRewardsCredited(uint256 indexed bucketId, address indexed token, uint256 individual, uint256 collective);
    event Claimed(uint256 indexed nftId, address indexed token, address indexed recipient, uint256 amount);
    constructor(address controller) ZZZModule(controller) {}
    function _canonicalAccess() internal view override returns (address) { return address(access); }
    function addAsset(address token) external onlyGovernance {
        if (token.code.length == 0 || isAsset[token] || assets.length == MAX_ASSETS) revert InvalidConfiguration();
        isAsset[token] = true;
        assets.push(token);
        emit AssetAdded(token);
    }
    function assetCount() external view returns (uint256) { return assets.length; }
    function _checkpoint(uint256 id, address token) private {
        uint256 delta = index[token] - paidIndex[id][token];
        uint256 weight = IZZZMembership(access.module(Ids.MEMBERSHIP)).eligible(id) ? 1 : 0;
        if (delta != 0 && weight != 0) {
            uint256 whole = Math.mulDiv(weight, delta, SCALE);
            uint256 remainder = mulmod(weight, delta, SCALE) + fraction[id][token];
            collective[id][token] += whole + remainder / SCALE;
            fraction[id][token] = remainder % SCALE;
        }
        paidIndex[id][token] = index[token];
    }
    function checkpointAll(uint256 id) external onlyModule(Ids.MEMBERSHIP) economic {
        for (uint256 i; i < assets.length; ++i) _checkpoint(id, assets[i]);
    }
    function _checkpointOwner(uint256 id, address token) private {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        uint256 current = ownerIndex[vault.nftBucket(id)][token];
        uint256 delta = current - paidOwnerIndex[id][token];
        uint256 shares = vault.sharesOf(id);
        if (delta != 0 && shares != 0) {
            uint256 whole = Math.mulDiv(shares, delta, SCALE);
            uint256 remainder = mulmod(shares, delta, SCALE) + ownerFraction[id][token];
            individual[id][token] += whole + remainder / SCALE;
            ownerFraction[id][token] = remainder % SCALE;
        }
        paidOwnerIndex[id][token] = current;
    }
    /// @dev The Vault associates a new NFT with its bucket while shares are zero,
    /// then calls this before every share increase. Membership never changes
    /// buckets; migration moves the whole bucket, not the canonical share ledger.
    function checkpointOwner(uint256 id) external onlyModule(Ids.VAULT) economic {
        for (uint256 i; i < assets.length; ++i) _checkpointOwner(id, assets[i]);
    }
    function creditPool(uint256 bucketId, address token, uint256 personal, uint256 shared)
        external onlyModule(Ids.FEES) nonReentrant economic {
        _creditPool(bucketId, token, personal, shared, false);
    }
    function creditCanonicalCutoff(uint256 bucketId, address token, uint256 personal, uint256 shared)
        external nonReentrant {
        if (msg.sender != access.module(Ids.FEES) || _state() != 1 || !canonicalCaptured ||
            !IZZZCanonicalAccess(address(access)).canonicalSettling()) revert CanonicalState();
        _creditPool(bucketId, token, personal, shared, true);
        if (_state() != 1 || !IZZZCanonicalAccess(address(access)).canonicalSettling()) revert CanonicalState();
    }
    function _creditPool(uint256 bucketId, address token, uint256 personal, uint256 shared, bool cutoff) private {
        if (!isAsset[token] || personal + shared == 0) revert InvalidAmount();
        uint256 supply = IZZZVault(access.module(Ids.VAULT)).bucketTotalShares(bucketId);
        if (supply == 0) revert InvalidState();
        ExactToken.pull(token, msg.sender, personal + shared);
        if (cutoff) {
            for (uint256 i; i < canonicalAssets.length; ++i) {
                if (canonicalAssets[i] == token) { canonicalAmounts[i] += personal + shared; break; }
            }
        }
        ownerIndex[bucketId][token] += Math.mulDiv(personal, SCALE, supply);
        uint256 weight = IZZZMembership(access.module(Ids.MEMBERSHIP)).totalEligible();
        if (weight == 0) {
            // Never give pre-participation revenue to a future entrant.
            orphaned[token] += shared;
            liabilities[token] += personal;
        } else {
            index[token] += Math.mulDiv(shared, SCALE, weight);
            liabilities[token] += personal + shared;
        }
        if (IERC20(token).balanceOf(address(this)) < liabilities[token] + orphaned[token]) revert InvalidState();
        emit PoolRewardsCredited(bucketId, token, personal, shared);
    }
    function claim(uint256 id, address token) external nonReentrant economic returns (uint256 amount) {
        return _claim(id, token, msg.sender);
    }
    /// @notice Only the NFT's immutable router can claim for its authenticated
    /// current owner. No approvals or arbitrary payout destinations are used.
    function claimFor(uint256 id, address token, address owner) external nonReentrant economic returns (uint256 amount) {
        if (msg.sender != IZZZNFT(access.module(Ids.NFT)).claimRouter()) revert Unauthorized();
        return _claim(id, token, owner);
    }
    function _claim(uint256 id, address token, address owner) private returns (uint256 amount) {
        // Claims are NOT paused when strategy operations are paused.
        if (!access.isSealed() || IZZZNFT(access.module(Ids.NFT)).ownerOf(id) != owner) revert Unauthorized();
        if (!isAsset[token]) revert InvalidConfiguration();
        _checkpoint(id, token);
        _checkpointOwner(id, token);
        amount = individual[id][token] + collective[id][token];
        individual[id][token] = 0;
        collective[id][token] = 0;
        liabilities[token] -= amount;
        ExactToken.push(token, owner, amount);
        emit Claimed(id, token, owner, amount);
    }
    function claimable(uint256 id, address token) external view returns (uint256) {
        uint256 weight = IZZZMembership(access.module(Ids.MEMBERSHIP)).eligible(id) ? 1 : 0;
        uint256 delta = index[token] - paidIndex[id][token];
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        uint256 shares = vault.sharesOf(id);
        uint256 ownerDelta = ownerIndex[vault.nftBucket(id)][token] - paidOwnerIndex[id][token];
        return individual[id][token] + collective[id][token] + Math.mulDiv(weight, delta, SCALE)
            + (mulmod(weight, delta, SCALE) + fraction[id][token]) / SCALE
            + Math.mulDiv(shares, ownerDelta, SCALE)
            + (mulmod(shares, ownerDelta, SCALE) + ownerFraction[id][token]) / SCALE;
    }
    // Global index-rounding dust remains reserved; no administrator sweep exists.

    uint256 private canonicalNFTs;
    uint256 private canonicalBuckets;
    uint256 private canonicalAssetTotal;
    function canonicalCapture() external canonicalOnly {
        _canonicalBeginCapture();
        canonicalNFTs = IZZZRewardNFTOrdinals(access.module(Ids.NFT)).mintedCount();
        canonicalBuckets = IZZZVault(access.module(Ids.VAULT)).bucketCount();
        canonicalAssetTotal = assets.length;
        for (uint256 i; i < assets.length; ++i) {
            address token = assets[i];
            uint256 amount = IERC20(token).balanceOf(address(this));
            if (amount < liabilities[token] + orphaned[token]) revert CanonicalState();
            _canonicalAdd(token, amount, 0);
        }
    }
    function canonicalSettle() external canonicalOnly {}
    function canonicalCount() public view returns (uint256) {
        return 1 + canonicalAssetTotal * (1 + canonicalBuckets + canonicalNFTs);
    }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if ((_state() != 1 && _state() != 3) || row >= canonicalCount()) revert CanonicalState();
        if (row == 0) return abi.encode(canonicalAssetTotal, canonicalBuckets, canonicalNFTs);
        --row;
        if (row < canonicalAssetTotal) {
            address token = assets[row];
            return abi.encode(token, index[token], liabilities[token], orphaned[token], canonicalAmounts[row]);
        }
        row -= canonicalAssetTotal;
        address asset = assets[row % canonicalAssetTotal];
        uint256 ordinal = row / canonicalAssetTotal;
        if (ordinal < canonicalBuckets) {
            uint256 bucket = IZZZVault(access.module(Ids.VAULT)).bucketAt(ordinal);
            return abi.encode(bucket, asset, ownerIndex[bucket][asset]);
        }
        uint256 id = IZZZRewardNFTOrdinals(access.module(Ids.NFT)).tokenAtOrdinal(ordinal - canonicalBuckets + 1);
        return abi.encode(id, asset, individual[id][asset], collective[id][asset], paidIndex[id][asset],
            fraction[id][asset], paidOwnerIndex[id][asset], ownerFraction[id][asset]);
    }
    function canonicalImport(uint256 row, bytes calldata record) external canonicalOnly {
        _canonicalNext(row);
        if (row == 0) {
            (canonicalAssetTotal, canonicalBuckets, canonicalNFTs) = abi.decode(record, (uint256,uint256,uint256));
            if (canonicalAssetTotal > MAX_ASSETS || canonicalBuckets > 4 || canonicalNFTs > 1000 ||
                (assets.length != 0 && assets.length != canonicalAssetTotal)) revert CanonicalState();
            return;
        }
        if (row >= canonicalCount()) revert CanonicalState();
        --row;
        if (row < canonicalAssetTotal) {
            (address token, uint256 ix, uint256 liability, uint256 orphan, uint256 backing) =
                abi.decode(record, (address,uint256,uint256,uint256,uint256));
            if (token.code.length == 0 || liabilities[token] != 0 || orphaned[token] != 0 || index[token] != 0 ||
                backing < liability + orphan) revert CanonicalState();
            if (assets.length == row) { if (isAsset[token]) revert CanonicalState(); assets.push(token); isAsset[token] = true; }
            if (assets[row] != token) revert CanonicalState();
            _canonicalAdd(token, backing, IERC20(token).balanceOf(address(this)));
            index[token] = ix; liabilities[token] = liability; orphaned[token] = orphan;
            return;
        }
        row -= canonicalAssetTotal;
        address expected = assets[row % canonicalAssetTotal];
        uint256 ordinal = row / canonicalAssetTotal;
        if (ordinal < canonicalBuckets) {
            (uint256 bucket, address token, uint256 ix) = abi.decode(record, (uint256,address,uint256));
            if (token != expected || bucket != IZZZVault(access.module(Ids.VAULT)).bucketAt(ordinal)) revert CanonicalState();
            ownerIndex[bucket][token] = ix; return;
        }
        (uint256 id, address asset, uint256 personal, uint256 shared, uint256 paid, uint256 frac,
            uint256 ownerPaid, uint256 ownerFrac) = abi.decode(record,(uint256,address,uint256,uint256,uint256,uint256,uint256,uint256));
        if (asset != expected || id != IZZZRewardNFTOrdinals(access.module(Ids.NFT)).tokenAtOrdinal(ordinal - canonicalBuckets + 1) ||
            frac >= SCALE || ownerFrac >= SCALE || paid > index[asset] ||
            ownerPaid > ownerIndex[IZZZVault(access.module(Ids.VAULT)).nftBucket(id)][asset]) revert CanonicalState();
        individual[id][asset] = personal; collective[id][asset] = shared; paidIndex[id][asset] = paid;
        fraction[id][asset] = frac; paidOwnerIndex[id][asset] = ownerPaid; ownerFraction[id][asset] = ownerFrac;
    }
    function canonicalValidate() external view {
        if (_state() == 2 && canonicalCursor != canonicalCount()) revert CanonicalState();
        _canonicalValidateBacking();
    }
}
