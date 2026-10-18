// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ZZZCanonicalLedger} from "./base/ZZZCanonicalLedger.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
import {IZZZAccess} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
interface IZZZRoyaltySuccessor {
    function destinationController() external view returns (address);
}
interface IZZZRoyaltyOrdinals {
    function mintedCount() external view returns (uint256);
    function tokenAtOrdinal(uint256) external view returns (uint256);
    function rarityOf(uint256) external view returns (uint8);
    function royaltyRewards() external view returns (address);
}

interface IZZZRoyaltyNFTOwner {
    function ownerOf(uint256 id) external view returns (address);
    function claimRouter() external view returns (address);
}

/// @notice Separate, funded NFT-sale royalty ledger. LP trading fees never enter
/// this allocation. The immutable NFT admits assets and activates each NFT once.
/// Current owners inherit unclaimed balances on transfer; there is no rescue,
/// withdrawal, weight-change, or administrator claim path.
contract ZZZRoyaltyRewards is ReentrancyGuard, ZZZCanonicalLedger {
    uint256 public constant SCALE = 1e36;
    uint256 public constant MAX_ERC20_ASSETS = 16;
    uint256 public constant MAX_ASSETS = MAX_ERC20_ASSETS + 1;
    address public immutable nft;
    address private immutable creator;
    address public canonicalController;
    // Address zero denotes native ETH and is always the first admitted asset.
    address[] public assets;
    mapping(address => bool) public isAsset;
    mapping(uint256 => uint256) public weightOf;
    uint256 public totalWeight;
    mapping(address => uint256) public index;
    // Accounted = liabilities + orphaned. Raw, unprocessed receipts are above it.
    mapping(address => uint256) public accounted;
    mapping(address => uint256) public liabilities;
    mapping(address => uint256) public orphaned;
    mapping(uint256 => mapping(address => uint256)) public accrued;
    mapping(uint256 => mapping(address => uint256)) public paidIndex;
    mapping(uint256 => mapping(address => uint256)) public fraction;

    error Unauthorized();
    error InvalidConfiguration();
    error InvalidState();
    error NativeTransferFailed();
    event AssetAdded(address indexed asset, uint256 quarantined);
    event Activated(uint256 indexed id, uint256 weight);
    event RoyaltiesReceived(address indexed asset, uint256 amount, bool eligible);
    event Claimed(uint256 indexed id, address indexed asset, address indexed owner, uint256 amount);
    event LateRoyaltiesForwarded(address indexed asset, address indexed receiver, uint256 amount);

    constructor(address nftController) {
        // The NFT may deploy this receiver from its own constructor.
        if (nftController == address(0)) revert InvalidConfiguration();
        nft = nftController;
        creator = msg.sender;
        isAsset[address(0)] = true;
        assets.push(address(0));
        accounted[address(0)] = address(this).balance;
        orphaned[address(0)] = address(this).balance;
        emit AssetAdded(address(0), address(this).balance);
    }

    /// @dev Intentionally no storage writes/calls: ordinary 2,300-gas marketplace
    /// transfers work. A later sync/activation/claim assigns the actual balance.
    receive() external payable {}
    /// @dev Production factory binds its immutable controller atomically before
    /// returning this receiver. Standalone ledgers have no migration authority.
    function bindCanonicalController(address controller) external {
        if (msg.sender != creator || canonicalController != address(0) || controller.code.length == 0) revert Unauthorized();
        canonicalController = controller;
    }
    function _canonicalAccess() internal view override returns (address) { return canonicalController; }

    modifier onlyNFT() {
        if (msg.sender != nft) revert Unauthorized();
        _;
    }

    function assetCount() external view returns (uint256) { return assets.length; }

    /// @dev Called by NFT governance's authenticated asset-admission wrapper.
    /// Admission never awards previously unsupported/prefunded token balances.
    /// Governance must admit only conventional exact-transfer, non-rebasing
    /// tokens. Balance observation cannot distinguish a positive rebase from a
    /// donation; a negative rebase fails closed, and taxed claims revert.
    function addAsset(address token) external onlyNFT nonReentrant economic {
        if (token == address(0) || token.code.length == 0 || isAsset[token] || assets.length == MAX_ASSETS) {
            revert InvalidConfiguration();
        }
        uint256 balance = IERC20(token).balanceOf(address(this));
        isAsset[token] = true;
        assets.push(token);
        accounted[token] = balance;
        orphaned[token] = balance;
        emit AssetAdded(token, balance);
    }

    /// @notice Permanently assign Commun/Rare/Legendary's royalty weight 1/2/3.
    /// @dev Sync every admitted asset BEFORE this member joins. Pending inbox
    /// receipts belong only to already eligible members, even if nobody synced.
    function activate(uint256 id, uint256 weight) external onlyNFT nonReentrant economic {
        if (weight == 0 || weight > 3 || weightOf[id] != 0) revert InvalidConfiguration();
        if (IZZZRoyaltyNFTOwner(nft).ownerOf(id) == address(0)) revert InvalidState();
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i];
            _sync(asset);
            _checkpoint(id, asset);
        }
        weightOf[id] = weight;
        totalWeight += weight;
        emit Activated(id, weight);
    }

    function _balance(address asset) private view returns (uint256) {
        return asset == address(0) ? address(this).balance : IERC20(asset).balanceOf(address(this));
    }

    function pending(address asset) external view returns (uint256) {
        if (!isAsset[asset]) revert InvalidConfiguration();
        uint256 balance = _balance(asset);
        if (balance < accounted[asset]) revert InvalidState();
        return balance - accounted[asset];
    }

    function _sync(address asset) private returns (uint256 amount) {
        uint256 balance = _balance(asset);
        if (balance < accounted[asset]) revert InvalidState();
        amount = balance - accounted[asset];
        if (amount == 0) return 0;
        accounted[asset] = balance;
        uint256 supply = totalWeight;
        if (supply == 0) {
            orphaned[asset] += amount;
        } else {
            index[asset] += Math.mulDiv(amount, SCALE, supply);
            liabilities[asset] += amount;
        }
        emit RoyaltiesReceived(asset, amount, supply != 0);
    }

    function sync(address asset) external nonReentrant economic returns (uint256 amount) {
        if (!isAsset[asset]) revert InvalidConfiguration();
        return _sync(asset);
    }

    function syncAll() external nonReentrant economic {
        for (uint256 i; i < assets.length; ++i) _sync(assets[i]);
    }

    /// @notice Optional exact ERC20 funding entrypoint. Plain transfers also
    /// work, but only the amount actually received can become a liability.
    function fund(address asset, uint256 amount) external nonReentrant economic {
        if (asset == address(0) || !isAsset[asset] || amount == 0) revert InvalidConfiguration();
        _sync(asset);
        ExactToken.pull(asset, msg.sender, amount);
        _sync(asset);
    }

    function _checkpoint(uint256 id, address asset) private {
        uint256 delta = index[asset] - paidIndex[id][asset];
        uint256 weight = weightOf[id];
        if (delta != 0 && weight != 0) {
            uint256 remainder = mulmod(weight, delta, SCALE) + fraction[id][asset];
            accrued[id][asset] += Math.mulDiv(weight, delta, SCALE) + remainder / SCALE;
            fraction[id][asset] = remainder % SCALE;
        }
        paidIndex[id][asset] = index[asset];
    }

    /// @notice Claims remain available independently of operational pauses.
    function claim(uint256 id, address asset) external nonReentrant economic returns (uint256 amount) {
        return _claim(id, asset, msg.sender);
    }

    /// @notice Router-only forwarding, always paid directly to the current owner.
    function claimFor(uint256 id, address asset, address owner) external nonReentrant economic returns (uint256 amount) {
        if (msg.sender != IZZZRoyaltyNFTOwner(nft).claimRouter()) revert Unauthorized();
        return _claim(id, asset, owner);
    }

    function _claim(uint256 id, address asset, address owner) private returns (uint256 amount) {
        if (IZZZRoyaltyNFTOwner(nft).ownerOf(id) != owner) revert Unauthorized();
        if (!isAsset[asset]) revert InvalidConfiguration();
        _sync(asset);
        _checkpoint(id, asset);
        amount = accrued[id][asset];
        accrued[id][asset] = 0;
        liabilities[asset] -= amount;
        accounted[asset] -= amount;
        if (asset == address(0)) {
            if (amount != 0) {
                (bool success,) = payable(owner).call{value: amount}("");
                if (!success) revert NativeTransferFailed();
            }
        } else {
            ExactToken.push(asset, owner, amount);
        }
        // A receiver can return native ETH during its callback; that new inbox
        // payment remains pending. Existing backing must never decrease further.
        if (_balance(asset) < accounted[asset]) revert InvalidState();
        emit Claimed(id, asset, owner, amount);
    }

    /// @dev Includes actual pending receipts at the CURRENT membership weight.
    function claimable(uint256 id, address asset) external view returns (uint256) {
        if (!isAsset[asset]) revert InvalidConfiguration();
        uint256 balance = _balance(asset);
        if (balance < accounted[asset]) revert InvalidState();
        uint256 currentIndex = index[asset];
        if (totalWeight != 0 && _state() == 0) currentIndex += Math.mulDiv(balance - accounted[asset], SCALE, totalWeight);
        uint256 delta = currentIndex - paidIndex[id][asset];
        uint256 weight = weightOf[id];
        return accrued[id][asset] + Math.mulDiv(weight, delta, SCALE)
            + (mulmod(weight, delta, SCALE) + fraction[id][asset]) / SCALE;
    }
    // Per-NFT fractional entitlements carry across checkpoints and claims.
    // Global index division dust stays reserved in liabilities, without a sweep
    // or redistribution to future entrants. Orphaned funds never join an index.

    uint256 private canonicalNFTs;
    uint256 private canonicalAssetTotal;
    uint256 private canonicalWeight;
    uint256[] private canonicalPending;
    bool private canonicalCutoffSettled;
    function canonicalCapture() external canonicalOnly {
        _canonicalBeginCapture();
        delete canonicalPending;
        canonicalCutoffSettled = false;
        canonicalNFTs = IZZZRoyaltyOrdinals(nft).mintedCount();
        canonicalAssetTotal = assets.length;
        canonicalWeight = totalWeight;
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i];
            uint256 balance = _balance(asset);
            if (balance < accounted[asset]) revert CanonicalState();
            canonicalPending.push(balance - accounted[asset]);
            _canonicalAdd(asset, balance, 0);
        }
    }
    function canonicalSettle() external canonicalOnly {
        if (_state() != 1 || canonicalCutoffSettled) revert CanonicalState();
        canonicalCutoffSettled = true;
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i]; uint256 amount = canonicalPending[i];
            accounted[asset] += amount;
            if (totalWeight == 0) orphaned[asset] += amount;
            else { index[asset] += Math.mulDiv(amount, SCALE, totalWeight); liabilities[asset] += amount; }
            emit RoyaltiesReceived(asset, amount, totalWeight != 0);
        }
    }
    function canonicalCount() public view returns (uint256) {
        return 1 + canonicalAssetTotal + canonicalNFTs * (1 + canonicalAssetTotal);
    }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if ((_state() != 1 && _state() != 3) || !canonicalCutoffSettled || row >= canonicalCount()) revert CanonicalState();
        if (row == 0) return abi.encode(canonicalAssetTotal, canonicalNFTs, totalWeight);
        --row;
        if (row < canonicalAssetTotal) {
            address asset = assets[row];
            return abi.encode(asset, index[asset], accounted[asset], liabilities[asset], orphaned[asset], canonicalAmounts[row]);
        }
        row -= canonicalAssetTotal;
        uint256 id = IZZZRoyaltyOrdinals(nft).tokenAtOrdinal(row / (1 + canonicalAssetTotal) + 1);
        uint256 subrow = row % (1 + canonicalAssetTotal);
        if (subrow == 0) return abi.encode(id, weightOf[id]);
        address token = assets[subrow - 1];
        return abi.encode(id, token, accrued[id][token], paidIndex[id][token], fraction[id][token]);
    }
    function canonicalImport(uint256 row, bytes calldata record) external canonicalOnly {
        _canonicalNext(row);
        if (row == 0) {
            if (totalWeight != 0) revert CanonicalState();
            (canonicalAssetTotal, canonicalNFTs, canonicalWeight) = abi.decode(record, (uint256,uint256,uint256));
            if (canonicalAssetTotal == 0 || canonicalAssetTotal > MAX_ASSETS || canonicalNFTs > 1000 ||
                canonicalWeight > 3 * canonicalNFTs || (assets.length != 1 && assets.length != canonicalAssetTotal)) revert CanonicalState();
            return;
        }
        if (row >= canonicalCount()) revert CanonicalState();
        --row;
        if (row < canonicalAssetTotal) {
            (address asset,uint256 ix,uint256 acc,uint256 liability,uint256 orphan,uint256 backing) =
                abi.decode(record,(address,uint256,uint256,uint256,uint256,uint256));
            if ((row == 0) != (asset == address(0)) || (asset != address(0) && asset.code.length == 0) ||
                liabilities[asset] != 0 || index[asset] != 0 || acc != liability + orphan || backing != acc) revert CanonicalState();
            if (assets.length == row) { if (isAsset[asset]) revert CanonicalState(); assets.push(asset); isAsset[asset] = true; }
            if (assets[row] != asset) revert CanonicalState();
            uint256 prefund = _balance(asset);
            _canonicalAdd(asset, backing, prefund);
            index[asset] = ix; liabilities[asset] = liability;
            accounted[asset] = acc + prefund; orphaned[asset] = orphan + prefund;
            return;
        }
        row -= canonicalAssetTotal;
        uint256 expected = IZZZRoyaltyOrdinals(nft).tokenAtOrdinal(row / (1 + canonicalAssetTotal) + 1);
        uint256 subrow = row % (1 + canonicalAssetTotal);
        if (subrow == 0) {
            (uint256 id,uint256 weight) = abi.decode(record,(uint256,uint256));
            if (id != expected || weightOf[id] != 0 || weight > 3 ||
                (weight != 0 && weight != uint256(IZZZRoyaltyOrdinals(nft).rarityOf(id)) + 1)) revert CanonicalState();
            weightOf[id] = weight; totalWeight += weight; return;
        }
        (uint256 nftId,address token,uint256 amount,uint256 paid,uint256 frac) = abi.decode(record,(uint256,address,uint256,uint256,uint256));
        if (nftId != expected || token != assets[subrow - 1] || frac >= SCALE || paid > index[token]) revert CanonicalState();
        accrued[nftId][token] = amount; paidIndex[nftId][token] = paid; fraction[nftId][token] = frac;
    }
    function canonicalValidate() external view {
        if (_state() == 2 && (canonicalCursor != canonicalCount() || totalWeight != canonicalWeight)) revert CanonicalState();
        _canonicalValidateBacking();
    }
    /// @dev Every receipt arriving at the inert successor before activation is
    /// quarantined. It cannot become the imported holders' initial reward index.
    function canonicalActivate() external override canonicalOnly {
        if (_state() != 2) revert CanonicalState();
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i];
            uint256 extra = _balance(asset) - accounted[asset];
            accounted[asset] += extra; orphaned[asset] += extra; canonicalPrefunds[i] += extra;
        }
    }
    /// @notice Retired marketplace addresses can still receive payments. Only
    /// post-cutoff balances are forwarded to the one immutable immediate successor.
    function forwardLate(address asset) external nonReentrant returns (uint256 amount) {
        if (_state() != 3 || !isAsset[asset]) revert CanonicalState();
        address handoff = IZZZCanonicalAccess(canonicalController).canonicalHandoff();
        address destination = IZZZRoyaltySuccessor(handoff).destinationController();
        address receiver = IZZZRoyaltyOrdinals(IZZZAccess(destination).module(Ids.NFT)).royaltyRewards();
        if (receiver == address(0) || receiver == address(this)) revert CanonicalState();
        amount = _balance(asset);
        if (asset == address(0)) {
            if (amount != 0) { (bool ok,) = payable(receiver).call{value: amount}(""); if (!ok) revert NativeTransferFailed(); }
        } else ExactToken.push(asset, receiver, amount);
        emit LateRoyaltiesForwarded(asset, receiver, amount);
    }
}
