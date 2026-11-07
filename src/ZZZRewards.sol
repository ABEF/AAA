// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {IZZZMembership, IZZZNFT, IZZZVault} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ExactLPAllocation} from "./libraries/ExactLPAllocation.sol";
import {ZZZExactLPRewardsCanonical} from "./base/ZZZExactLPRewardsCanonical.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
import {ZZZLPRewardConverter} from "./ZZZLPRewardConverter.sol";
import {ZZZRewardsCanonical} from "./ZZZRewardsCanonical.sol";

/// @notice Funded whole-unit LP rights follow the NFT's current owner.
/// @dev Accounting7 only. Individual trees use shared bucket shares; one global
/// tree uses equal activated membership. Royalties and principal are separate.
contract ZZZRewards is ZZZExactLPRewardsCanonical {
    using SafeERC20 for IERC20;
    using ExactLPAllocation for ExactLPAllocation.Tree;

    address public converter;
    address public immutable canonicalModule;
    event PoolRewardsCredited(uint256 indexed bucketId, address indexed token, uint256 individual, uint256 collective);
    event Claimed(uint256 indexed nftId, address indexed token, address indexed recipient, uint256 amount);
    event ConverterBound(address indexed converter);
    event LPRewardsConverted(uint256 indexed nftId, address indexed source,
        uint256 sourceIndividual, uint256 sourceCollective, uint256 nativeIndividual, uint256 nativeCollective);
    event ShareWeightSynchronized(uint256 indexed nftId, uint256 indexed bucketId,
        uint256 ordinal, uint256 previousWeight, uint256 weight, uint256 totalWeight);
    event CollectiveWeightSynchronized(uint256 indexed nftId,
        uint256 ordinal, uint256 previousWeight, uint256 weight, uint256 totalWeight);

    constructor(address controller) ZZZExactLPRewardsCanonical(controller) {
        canonicalModule = address(new ZZZRewardsCanonical(controller));
    }
    function _canonicalModule() internal view override returns (address) { return canonicalModule; }
    receive() external payable {}

    function bindConverter(address candidate) external onlyGovernance nonReentrant economic {
        if (access.isSealed() || converter != address(0) || candidate.code.length == 0 ||
            ZZZLPRewardConverter(payable(candidate)).ledger() != address(this) ||
            address(ZZZLPRewardConverter(payable(candidate)).access()) != address(access)) revert InvalidConfiguration();
        converter = candidate;
        emit ConverterBound(candidate);
    }

    /// @notice Bind only the deployment's fixed ZZZ, before sealing.
    function addAsset(address token) external onlyGovernance economic {
        if (access.isSealed() || assets.length != 1 || isAsset[token]) revert InvalidConfiguration();
        _validateZZZ(token);
        assets.push(token);
        isAsset[token] = true;
        emit AssetAdded(token);
    }
    function assetCount() external view returns (uint256) { return assets.length; }

    /// @notice Install authenticated new shares after the Vault's atomic write.
    /// @dev Stored old weights settle both old books first. No mutable dependency
    /// callback exists between the Vault write and this typed synchronization.
    function syncShares(uint256 id) external onlyModule(Ids.VAULT) nonReentrant economic {
        IZZZVault vault = IZZZVault(msg.sender);
        uint256 bucket = vault.nftBucket(id);
        uint256 weight = vault.sharesOf(id);
        uint256 ordinal = _ordinal(id);
        if (bucket == 0 || weight == 0 || (rewardBucket[id] != 0 && rewardBucket[id] != bucket)) revert InvalidState();
        ExactLPAllocation.Tree storage tree = ownerBooks[bucket];
        uint256 previous = tree.weightOf(ordinal);
        if (weight < previous) revert InvalidState();
        rewardBucket[id] = bucket;
        uint256 total = tree.setWeight(ordinal, weight);
        if (total != vault.bucketTotalShares(bucket)) revert InvalidState();
        emit ShareWeightSynchronized(id, bucket, ordinal, previous, weight, total);
    }

    /// @notice Add exactly one collective share after activation is recorded.
    function syncMembership(uint256 id) external onlyModule(Ids.MEMBERSHIP) nonReentrant economic {
        IZZZMembership membership = IZZZMembership(msg.sender);
        uint256 ordinal = _ordinal(id);
        uint256 previous = collectiveBook.weightOf(ordinal);
        if (!membership.eligible(id) || rewardBucket[id] == 0 || previous != 0) revert InvalidState();
        uint256 total = collectiveBook.setWeight(ordinal, 1);
        if (total != membership.totalEligible()) revert InvalidState();
        emit CollectiveWeightSynchronized(id, ordinal, previous, 1, total);
    }

    function creditPool(uint256 bucketId, address token, uint256 personal, uint256 shared)
        external payable onlyModule(Ids.FEES) nonReentrant economic {
        _creditPool(bucketId, token, personal, shared, false);
    }
    function creditCanonicalCutoff(uint256 bucketId, address token, uint256 personal, uint256 shared)
        external payable nonReentrant {
        if (msg.sender != access.module(Ids.FEES) || _state() != 1 ||
            !IZZZCanonicalAccess(address(access)).canonicalSettling()) revert CanonicalState();
        _creditPool(bucketId, token, personal, shared, true);
        if (_state() != 1 || !IZZZCanonicalAccess(address(access)).canonicalSettling()) revert CanonicalState();
    }

    function _creditPool(uint256 bucket, address token, uint256 personal, uint256 shared, bool cutoff) private {
        ExactLPAllocation.Asset book = _asset(token);
        uint256 amount = personal + shared;
        uint256 supply = IZZZVault(access.module(Ids.VAULT)).bucketTotalShares(bucket);
        uint256 eligible = IZZZMembership(access.module(Ids.MEMBERSHIP)).totalEligible();
        if (amount == 0) revert InvalidAmount();
        if (supply == 0 || ownerBooks[bucket].totalWeight() != supply ||
            collectiveBook.totalWeight() != eligible) revert InvalidState();
        if (msg.value != (token == address(0) ? amount : 0)) revert InvalidAmount();
        if (token != address(0)) ExactToken.pull(token, msg.sender, amount);
        if (cutoff) ZZZRewardsCanonical(payable(canonicalModule)).creditCutoff(token, amount);
        ownerBooks[bucket].credit(book, personal);
        liabilities[token] += personal;
        if (eligible == 0) orphaned[token] += shared;
        else {
            collectiveBook.credit(book, shared);
            liabilities[token] += shared;
        }
        _solvent(token);
        emit PoolRewardsCredited(bucket, token, personal, shared);
    }

    /// @notice Whole individual and collective rights, including direct credits.
    function claimableComponents(uint256 id, address token) public view returns (uint256 personal, uint256 shared) {
        if (_reentrancyGuardEntered()) revert InvalidState();
        ExactLPAllocation.Asset book = _asset(token);
        uint256 ordinal = _ordinal(id);
        uint256 bucket = rewardBucket[id];
        personal = directIndividual[id][token];
        if (bucket != 0) personal += ownerBooks[bucket].claimable(book, ordinal);
        shared = directCollective[id][token] + collectiveBook.claimable(book, ordinal);
    }
    function claimable(uint256 id, address token) external view returns (uint256) {
        (uint256 personal, uint256 shared) = claimableComponents(id, token);
        return personal + shared;
    }
    /// @notice Bucket zero selects the global equal-membership tree.
    function allocationTree(uint256 bucket) external view returns (uint256 weight, uint256 ethOutstanding, uint256 zzzOutstanding) {
        if (_reentrancyGuardEntered()) revert InvalidState();
        ExactLPAllocation.Tree storage tree = bucket == 0 ? collectiveBook : ownerBooks[bucket];
        return (tree.totalWeight(), tree.outstanding(ExactLPAllocation.Asset.ETH), tree.outstanding(ExactLPAllocation.Asset.ZZZ));
    }

    function _takeComponents(uint256 id, address token) private returns (uint256 personal, uint256 shared) {
        ExactLPAllocation.Asset book = _asset(token);
        uint256 ordinal = _ordinal(id);
        personal = directIndividual[id][token];
        shared = directCollective[id][token];
        if (personal != 0) delete directIndividual[id][token];
        if (shared != 0) delete directCollective[id][token];
        directLiabilities[token] -= personal + shared;
        uint256 bucket = rewardBucket[id];
        if (bucket != 0) personal += ownerBooks[bucket].take(book, ordinal);
        shared += collectiveBook.take(book, ordinal);
    }
    function _solvent(address token) private view {
        if (_canonicalBalance(token) < liabilities[token] + orphaned[token]) revert InvalidState();
    }

    function claim(uint256 id, address token) external nonReentrant economic returns (uint256) {
        return _claim(id, token, msg.sender);
    }
    /// @notice Only the NFT's fixed router may claim for its current owner.
    function claimFor(uint256 id, address token, address owner) external nonReentrant economic returns (uint256) {
        if (msg.sender != IZZZNFT(access.module(Ids.NFT)).claimRouter()) revert Unauthorized();
        return _claim(id, token, owner);
    }
    function _claim(uint256 id, address token, address owner) private returns (uint256 amount) {
        if (!access.isSealed() || IZZZNFT(access.module(Ids.NFT)).ownerOf(id) != owner) revert Unauthorized();
        (uint256 personal, uint256 shared) = _takeComponents(id, token);
        amount = personal + shared;
        liabilities[token] -= amount;
        if (token == address(0)) {
            if (amount != 0) { (bool ok,) = owner.call{value: amount}(""); if (!ok) revert InvalidState(); }
        } else ExactToken.push(token, owner, amount);
        _solvent(token);
        emit Claimed(id, token, owner, amount);
    }

    /// @notice Convert already allocated ZZZ rights into same-NFT ETH credits.
    function convertBatch(address token, uint256[] calldata ids, bytes32 routeId, uint256 minimumETH, uint256 deadline)
        external onlyKeeper live operating nonReentrant economic returns (uint256 output) {
        if (access.module(Ids.REWARDS) != address(this) || converter == address(0) || token == address(0) ||
            !isAsset[token] || ids.length == 0 || ids.length > MAX_CONVERSION_NFTS) revert InvalidConfiguration();
        uint256[] memory personal = new uint256[](ids.length);
        uint256[] memory shared = new uint256[](ids.length);
        uint256 total;
        for (uint256 i; i < ids.length; ++i) {
            if ((i != 0 && ids[i] <= ids[i-1]) || IZZZNFT(access.module(Ids.NFT)).ownerOf(ids[i]) == address(0))
                revert InvalidConfiguration();
            (personal[i], shared[i]) = _takeComponents(ids[i], token);
            total += personal[i] + shared[i];
        }
        if (total == 0) revert InvalidAmount();
        uint256 sourceBefore = IERC20(token).balanceOf(address(this));
        uint256 nativeBefore = address(this).balance;
        liabilities[token] -= total;
        IERC20(token).forceApprove(converter, total);
        output = ZZZLPRewardConverter(payable(converter)).convert(token,total,routeId,minimumETH,deadline);
        IERC20(token).forceApprove(converter, 0);
        if (IERC20(token).balanceOf(address(this)) != sourceBefore - total ||
            address(this).balance != nativeBefore + output) revert InvalidState();
        liabilities[address(0)] += output;
        directLiabilities[address(0)] += output;
        uint256 cumulative;
        uint256 assigned;
        for (uint256 i; i < ids.length; ++i) {
            cumulative += personal[i];
            uint256 next = Math.mulDiv(output,cumulative,total);
            uint256 ownETH = next - assigned;
            assigned = next;
            cumulative += shared[i];
            next = Math.mulDiv(output,cumulative,total);
            uint256 sharedETH = next - assigned;
            assigned = next;
            directIndividual[ids[i]][address(0)] += ownETH;
            directCollective[ids[i]][address(0)] += sharedETH;
            emit LPRewardsConverted(ids[i],token,personal[i],shared[i],ownETH,sharedETH);
        }
        _solvent(token);
        _solvent(address(0));
        if (!access.keeperAuthorized(msg.sender) || access.paused()) revert Unauthorized();
    }
}
