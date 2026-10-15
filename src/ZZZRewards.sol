// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZMembership, IZZZNFT, IZZZVault} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";

contract ZZZRewards is ZZZModule, ReentrancyGuard {
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
    function checkpointAll(uint256 id) external onlyModule(Ids.MEMBERSHIP) {
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
    function checkpointOwner(uint256 id) external onlyModule(Ids.VAULT) {
        for (uint256 i; i < assets.length; ++i) _checkpointOwner(id, assets[i]);
    }
    function creditPool(uint256 bucketId, address token, uint256 personal, uint256 shared)
        external onlyModule(Ids.FEES) nonReentrant {
        if (!isAsset[token] || personal + shared == 0) revert InvalidAmount();
        uint256 supply = IZZZVault(access.module(Ids.VAULT)).bucketTotalShares(bucketId);
        if (supply == 0) revert InvalidState();
        ExactToken.pull(token, msg.sender, personal + shared);
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
    function claim(uint256 id, address token) external nonReentrant returns (uint256 amount) {
        // Claims are NOT paused when strategy operations are paused.
        if (!access.isSealed() || IZZZNFT(access.module(Ids.NFT)).ownerOf(id) != msg.sender) revert Unauthorized();
        if (!isAsset[token]) revert InvalidConfiguration();
        _checkpoint(id, token);
        _checkpointOwner(id, token);
        amount = individual[id][token] + collective[id][token];
        individual[id][token] = 0;
        collective[id][token] = 0;
        liabilities[token] -= amount;
        ExactToken.push(token, msg.sender, amount);
        emit Claimed(id, token, msg.sender, amount);
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
}
