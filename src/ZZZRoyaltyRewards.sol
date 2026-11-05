// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ZZZCanonicalLedger} from "./base/ZZZCanonicalLedger.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
import {IZZZAccess} from "./interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
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
/// Current owners inherit unclaimed balances. No external-custodian exit,
/// administrator holder-claim or weight override exists.
contract ZZZRoyaltyRewards is ReentrancyGuard, ZZZCanonicalLedger {
    uint256 public constant SCALE = 1e36;
    uint256 public constant MAX_ERC20_ASSETS = 64;
    uint256 public constant MAX_ASSETS = MAX_ERC20_ASSETS + 1;
    uint8 public assetCapacity = 16;
    address public immutable nft;
    address private immutable creator;
    address public canonicalController;
    uint256 public constant ROYALTY_SETTLEMENT_VERSION = 3;
    uint256 public constant ROYALTY_RECOVERY_VERSION = 2;
    uint256 public constant ACTIVATION_WINDOW = 1 hours;
    uint64 public mintEnd;
    bool private openingFinalized;
    uint256 private openingCount;
    uint256 private openingWeight;
    mapping(address => bool) private initialAllocated;
    mapping(address => uint256) public openingPool;
    // Address zero denotes native ETH and is always the first admitted asset.
    address[] public assets;
    mapping(address => bool) public isAsset;
    mapping(uint256 => uint256) public weightOf;
    uint256 public totalWeight;
    mapping(address => uint256) public index;
    // Accounted = liabilities + orphaned + openingPool. Raw receipts are above it.
    mapping(address => uint256) public accounted;
    mapping(address => uint256) public liabilities;
    mapping(address => uint256) public orphaned;
    mapping(uint256 => mapping(address => uint256)) public accrued;
    mapping(uint256 => mapping(address => uint256)) public paidIndex;
    mapping(uint256 => mapping(address => uint256)) public fraction;
    uint256 public activationCount;
    mapping(uint256 => uint256) public activationOrdinal;
    mapping(address => uint256) public eligibleCount;
    mapping(address => uint256) public eligibleWeight;
    struct Join { uint256 first; uint256 last; uint256 baseline; }
    mapping(address => Join[]) private deferredJoins;

    error Unauthorized();
    error InvalidConfiguration();
    error InvalidState();
    error NativeTransferFailed();
    event AssetAdded(address indexed asset, uint256 quarantined);
    event Activated(uint256 indexed id, uint256 weight);
    event RoyaltiesReceived(address indexed asset, uint256 amount, bool eligible);
    event Claimed(uint256 indexed id, address indexed asset, address indexed owner, uint256 amount);
    event LateRoyaltiesForwarded(address indexed asset, address indexed receiver, uint256 amount);
    event RoyaltyAssetDeferred(uint256 indexed id, address indexed asset);
    event RoyaltyEligibilityRecovered(address indexed asset, uint256 firstOrdinal, uint256 lastOrdinal);
    event UnallocatedRoyaltiesAllocated(address indexed asset, uint256 amount,
        uint256 activeWeight, bytes32 reviewHash);
    event MintEndConfigured(uint64 mintEnd, uint256 royaltiesOpenAt);
    event RoyaltyOpeningFinalized(uint256 cutoff, uint256 count, uint256 weight);
    event InitialRoyaltiesAllocated(address indexed asset, uint256 amount, uint256 count, uint256 weight);
    event AssetCapacityIncreased(uint8 capacity, bytes32 reviewHash);

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

    /// @notice Expand reviewed capacity without dropping any admitted currency.
    /// A review hash records operator gas qualification; it is not a gas proof.
    function increaseAssetCapacity(uint8 capacity, bytes32 reviewHash) external onlyNFT nonReentrant economic {
        if (capacity <= assetCapacity || capacity > MAX_ERC20_ASSETS || reviewHash == bytes32(0))
            revert InvalidConfiguration();
        assetCapacity = capacity;
        emit AssetCapacityIncreased(capacity, reviewHash);
    }

    /// @notice Mirror the final marketplace sale end. Changes are allowed only
    /// while the old sale is still open; they never shorten the 1-hour window.
    function setMintEnd(uint64 end) external onlyNFT nonReentrant economic {
        if (end <= block.timestamp || (mintEnd != 0 && block.timestamp > mintEnd) || openingFinalized)
            revert InvalidState();
        mintEnd = end;
        emit MintEndConfigured(end, uint256(end) + ACTIVATION_WINDOW);
    }
    function royaltiesOpenAt() public view returns (uint256) {
        return mintEnd == 0 ? 0 : uint256(mintEnd) + ACTIVATION_WINDOW;
    }
    function royaltiesOpen() public view returns (bool) {
        return mintEnd != 0 && block.timestamp >= royaltiesOpenAt();
    }
    /// @dev Seal the cutoff before ANY post-deadline activation joins. A late
    /// first transaction cannot extend the eligible cohort or award late entrants.
    function _finalizeOpening() private {
        if (!openingFinalized && royaltiesOpen()) {
            openingFinalized = true;
            openingCount = activationCount;
            openingWeight = totalWeight;
            emit RoyaltyOpeningFinalized(royaltiesOpenAt(), openingCount, openingWeight);
        }
    }

    /// @notice Allocate reviewed unallocated receipts in their ORIGINAL currency.
    /// Existing earned/deferred/fraction liabilities never enter this amount.
    /// Admission is separate and bounded; no swap, approval or external recipient.
    function allocateUnallocated(address asset, uint256 amount, bytes32 reviewHash)
        external nonReentrant economic {
        _allocateUnallocated(asset,amount,reviewHash,false);
    }
    /// @notice Allocate every currently unallocated whole unit of ONE currency;
    /// existing earned/fraction backing is never included. No holder loop.
    function allocateAllUnallocated(address asset, bytes32 reviewHash)
        external nonReentrant economic returns (uint256 amount) {
        return _allocateUnallocated(asset,0,reviewHash,true);
    }
    function _allocateUnallocated(address asset,uint256 amount,bytes32 reviewHash,bool all)
        private returns(uint256) {
        _recoveryAuthority();
        if (!royaltiesOpen()) revert InvalidState();
        if (!isAsset[asset] || (!all && amount == 0) || reviewHash == bytes32(0) || totalWeight == 0)
            revert InvalidConfiguration();
        _sync(asset);
        if(all) amount=orphaned[asset];
        if (amount > orphaned[asset]) revert InvalidConfiguration();
        orphaned[asset] -= amount;
        liabilities[asset] += amount;
        index[asset] += Math.mulDiv(amount, SCALE, totalWeight);
        if(amount!=0)emit UnallocatedRoyaltiesAllocated(asset, amount, totalWeight, reviewHash);
        _recoveryAuthority();
        return amount;
    }

    function _recoveryAuthority() private view {
        IZZZAccess control = IZZZAccess(canonicalController);
        if (!control.canConfigure(msg.sender) || !control.isSealed() || control.paused() ||
            control.preparationActive() || control.module(Ids.NFT) != nft) revert Unauthorized();
    }

    /// @dev Called by NFT governance's authenticated asset-admission wrapper.
    /// Admission never awards previously unsupported/prefunded token balances.
    /// Governance must admit only conventional exact-transfer, non-rebasing
    /// tokens. Balance observation cannot distinguish a positive rebase from a
    /// donation; a negative rebase fails closed, and taxed claims revert.
    function addAsset(address token) external onlyNFT nonReentrant economic {
        if (token == address(0) || token.code.length == 0 || isAsset[token] || assets.length >= uint256(assetCapacity)+1) {
            revert InvalidConfiguration();
        }
        uint256 balance = IERC20(token).balanceOf(address(this));
        isAsset[token] = true;
        assets.push(token);
        accounted[token] = balance;
        orphaned[token] = balance;
        eligibleCount[token] = activationCount; eligibleWeight[token] = totalWeight;
        // Post-opening admission keeps the explicit current-weight recovery rule;
        // it cannot silently rewrite the original cutoff cohort.
        _finalizeOpening();
        initialAllocated[token] = openingFinalized;
        emit AssetAdded(token, balance);
    }

    /// @notice Permanently assign Commun/Rare/Legendary's royalty weight 1/2/3.
    /// @dev Healthy assets settle before joining. An unreadable optional currency
    /// retains its old cohort; later recovery assigns unseen receipts to that
    /// cohort before enrolling the waiting activations. ETH cannot fail via ERC20.
    function activate(uint256 id, uint256 weight) external onlyNFT nonReentrant economic {
        _finalizeOpening();
        if (weight == 0 || weight > 3 || weightOf[id] != 0) revert InvalidConfiguration();
        if (IZZZRoyaltyNFTOwner(nft).ownerOf(id) == address(0)) revert InvalidState();
        if (activationCount == 1000) revert InvalidConfiguration();
        uint256 syncGas;
        if(assets.length > 1) syncGas = IZZZProtocolPolicy(IZZZAccess(canonicalController).protocolPolicy()).royaltySyncGas();
        uint256 successful;
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i];
            bool ok = true;
            if (asset == address(0)) _sync(asset);
            else {
                // Reserve enough gas for the complete isolated call and tail.
                // Caller underfunding cannot deliberately defer a healthy read.
                if (gasleft() < syncGas + 120_000) revert InvalidState();
                bytes memory data = abi.encodeCall(this.syncForActivation, (asset));
                uint256 budget = syncGas;
                assembly ("memory-safe") { ok := call(budget, address(), 0, add(data, 32), mload(data), 0, 0) }
            }
            if (ok) { _checkpoint(id, asset); successful |= uint256(1) << i; }
            else emit RoyaltyAssetDeferred(id, asset);
        }
        weightOf[id] = weight;
        totalWeight += weight;
        activationOrdinal[id] = ++activationCount;
        for (uint256 i; i < assets.length; ++i) if ((successful & (uint256(1) << i)) != 0) {
            eligibleCount[assets[i]] = activationCount; eligibleWeight[assets[i]] = totalWeight;
        }
        emit Activated(id, weight);
    }

    /// @dev Self-call boundary isolates optional token reverts/OOG/oversized
    /// revert data. External callers must use sync, with the economic guard.
    function syncForActivation(address asset) external {
        if (msg.sender != address(this)) revert Unauthorized();
        _sync(asset);
    }
    function eligibleFor(uint256 id, address asset) public view returns (bool) {
        uint256 ordinal = activationOrdinal[id];
        return isAsset[asset] && ordinal != 0 && ordinal <= effectiveEligibleCount(asset);
    }
    /// @notice Include the sealed opening cohort even before a faulted currency
    /// can materialize its initial index. This does not enroll late activations.
    function effectiveEligibleCount(address asset) public view returns (uint256) {
        uint256 cutoff = openingFinalized ? openingCount : activationCount;
        return !initialAllocated[asset] && royaltiesOpen() ? Math.max(eligibleCount[asset], cutoff) : eligibleCount[asset];
    }
    function _enrollWaiting(address asset) private {
        uint256 old = eligibleCount[asset];
        if (old == activationCount) return;
        deferredJoins[asset].push(Join(old + 1, activationCount, index[asset]));
        eligibleCount[asset] = activationCount; eligibleWeight[asset] = totalWeight;
        emit RoyaltyEligibilityRecovered(asset, old + 1, activationCount);
    }
    function _paid(uint256 id, address asset) private view returns (uint256 paid) {
        paid = paidIndex[id][asset];
        uint256 ordinal = activationOrdinal[id];
        Join[] storage joins = deferredJoins[asset];
        uint256 low; uint256 high = joins.length;
        while (low < high) { uint256 mid = (low + high) / 2;
            if (joins[mid].last < ordinal) low = mid + 1; else high = mid;
        }
        if (low < joins.length && ordinal >= joins[low].first) paid = Math.max(paid, joins[low].baseline);
    }

    function pending(address asset) external view returns (uint256) {
        if (_reentrancyGuardEntered()) revert InvalidState();
        if (!isAsset[asset]) revert InvalidConfiguration();
        uint256 balance = _canonicalBalance(asset);
        if (balance < accounted[asset]) revert InvalidState();
        return balance - accounted[asset];
    }

    function _sync(address asset) private returns (uint256 amount) {
        _finalizeOpening();
        uint256 balance = _canonicalBalance(asset);
        if (balance < accounted[asset]) revert InvalidState();
        amount = balance - accounted[asset];
        if (!openingFinalized) {
            accounted[asset] = balance;
            openingPool[asset] += amount;
            if (amount != 0) emit RoyaltiesReceived(asset, amount, false);
            _enrollWaiting(asset);
            return amount;
        }
        if (!initialAllocated[asset]) {
            initialAllocated[asset] = true;
            // A currency fault during the grace window must not exclude NFTs
            // which DID activate before cutoff. Its initial index is still zero.
            uint256 old = eligibleCount[asset];
            if (old < openingCount) {
                deferredJoins[asset].push(Join(old + 1, openingCount, 0));
                emit RoyaltyEligibilityRecovered(asset, old + 1, openingCount);
            }
            eligibleCount[asset] = openingCount;
            eligibleWeight[asset] = openingWeight;
            accounted[asset] = balance;
            uint256 initial = openingPool[asset] + amount;
            openingPool[asset] = 0;
            if (amount != 0) emit RoyaltiesReceived(asset, amount, false);
            if (openingWeight != 0) {
                liabilities[asset] += initial;
                index[asset] += Math.mulDiv(initial, SCALE, openingWeight);
            } else orphaned[asset] += initial;
            emit InitialRoyaltiesAllocated(asset, openingWeight == 0 ? 0 : initial, openingCount, openingWeight);
            _enrollWaiting(asset);
            return amount;
        }
        if (amount == 0) { _enrollWaiting(asset); return 0; }
        accounted[asset] = balance;
        uint256 supply = eligibleWeight[asset];
        if (supply == 0) {
            orphaned[asset] += amount;
        } else {
            index[asset] += Math.mulDiv(amount, SCALE, supply);
            liabilities[asset] += amount;
        }
        emit RoyaltiesReceived(asset, amount, supply != 0);
        _enrollWaiting(asset);
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
        uint256 delta = index[asset] - _paid(id, asset);
        uint256 weight = eligibleFor(id, asset) ? weightOf[id] : 0;
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
        if (!royaltiesOpen()) revert InvalidState();
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
        if (_canonicalBalance(asset) < accounted[asset]) revert InvalidState();
        emit Claimed(id, asset, owner, amount);
    }

    /// @dev Includes actual pending receipts at the CURRENT membership weight.
    function claimable(uint256 id, address asset) external view returns (uint256) {
        // External consumers must not value an intermediate conversion/payment
        // balance during a token, router or recipient callback.
        if (_reentrancyGuardEntered()) revert InvalidState();
        if (!isAsset[asset]) revert InvalidConfiguration();
        if (!royaltiesOpen()) return 0;
        uint256 balance = _canonicalBalance(asset);
        if (balance < accounted[asset]) revert InvalidState();
        uint256 currentIndex = index[asset];
        if (!eligibleFor(id, asset)) return accrued[id][asset];
        uint256 supply = eligibleWeight[asset];
        if (!initialAllocated[asset]) {
            uint256 count = openingFinalized ? openingCount : activationCount;
            if (activationOrdinal[id] > count) return accrued[id][asset];
            supply = openingFinalized ? openingWeight : totalWeight;
            if (supply != 0 && _state() == 0)
                currentIndex += Math.mulDiv(openingPool[asset] + balance - accounted[asset], SCALE, supply);
        } else if (supply != 0 && _state() == 0)
            currentIndex += Math.mulDiv(balance - accounted[asset], SCALE, supply);
        uint256 delta = currentIndex - _paid(id, asset);
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
        // The unchanged per-NFT canonical rows flatten a completed opening only.
        // Do not discard a live initial cohort or silently reopen a grace window.
        if (!royaltiesOpen() || !openingFinalized) revert CanonicalState();
        _canonicalBeginCapture();
        delete canonicalPending;
        canonicalCutoffSettled = false;
        canonicalNFTs = IZZZRoyaltyOrdinals(nft).mintedCount();
        canonicalAssetTotal = assets.length;
        canonicalWeight = totalWeight;
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i];
            if (!initialAllocated[asset]) revert CanonicalState();
            uint256 balance = _canonicalBalance(asset);
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
            uint256 supply = eligibleWeight[asset];
            if (supply == 0) orphaned[asset] += amount;
            else { index[asset] += Math.mulDiv(amount, SCALE, supply); liabilities[asset] += amount; }
            _enrollWaiting(asset);
            emit RoyaltiesReceived(asset, amount, supply != 0);
        }
    }
    function canonicalCount() public view returns (uint256) {
        return 1 + canonicalAssetTotal + canonicalNFTs * (1 + canonicalAssetTotal);
    }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if ((_state() != 1 && _state() != 3) || !canonicalCutoffSettled || row >= canonicalCount()) revert CanonicalState();
        if (row == 0) return abi.encode(canonicalAssetTotal, canonicalNFTs, totalWeight, mintEnd,assetCapacity);
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
        // Flatten deferred-join baselines into the existing portable row format.
        return abi.encode(id, token, accrued[id][token], _paid(id, token), fraction[id][token]);
    }
    function canonicalImport(uint256 row, bytes calldata record) external canonicalOnly {
        _canonicalNext(row);
        if (row == 0) {
            if (totalWeight != 0) revert CanonicalState();
            if (record.length != 160) revert CanonicalState();
            (canonicalAssetTotal, canonicalNFTs, canonicalWeight, mintEnd,assetCapacity) = abi.decode(record, (uint256,uint256,uint256,uint64,uint8));
            if (!royaltiesOpen()) revert CanonicalState();
            openingFinalized = true;
            if (canonicalAssetTotal == 0 || canonicalAssetTotal > MAX_ASSETS || canonicalNFTs > 1000 ||
                assetCapacity<16 || assetCapacity>MAX_ERC20_ASSETS || canonicalAssetTotal>uint256(assetCapacity)+1 ||
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
            uint256 prefund = _canonicalBalance(asset);
            _canonicalAdd(asset, backing, prefund);
            index[asset] = ix; liabilities[asset] = liability;
            initialAllocated[asset] = true;
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
            weightOf[id] = weight; totalWeight += weight;
            if (weight != 0) activationOrdinal[id] = ++activationCount;
            return;
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
            uint256 extra = _canonicalBalance(asset) - accounted[asset];
            accounted[asset] += extra; orphaned[asset] += extra; canonicalPrefunds[i] += extra;
            eligibleCount[asset] = activationCount; eligibleWeight[asset] = totalWeight;
        }
    }
    /// @notice Retired marketplace addresses can still receive payments. Forward
    /// even unsupported currencies to the one authenticated immediate successor;
    /// admission or restricted recovery there determines their allocation.
    function forwardLate(address asset) external nonReentrant returns (uint256 amount) {
        if (_state() != 3) revert CanonicalState();
        address handoff = IZZZCanonicalAccess(canonicalController).canonicalHandoff();
        address destination = IZZZRoyaltySuccessor(handoff).destinationController();
        address receiver = IZZZRoyaltyOrdinals(IZZZAccess(destination).module(Ids.NFT)).royaltyRewards();
        if (receiver == address(0) || receiver == address(this)) revert CanonicalState();
        amount = _canonicalBalance(asset);
        if (asset == address(0)) {
            if (amount != 0) { (bool ok,) = payable(receiver).call{value: amount}(""); if (!ok) revert NativeTransferFailed(); }
        } else ExactToken.push(asset, receiver, amount);
        emit LateRoyaltiesForwarded(asset, receiver, amount);
    }
}
