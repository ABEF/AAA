// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ExactRoyaltyAllocation} from "./libraries/ExactRoyaltyAllocation.sol";
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
    using ExactRoyaltyAllocation for ExactRoyaltyAllocation.Book;
    mapping(address => mapping(uint256 => ExactRoyaltyAllocation.Book)) private allocationBooks;
    uint256[3] private firstWeightOrdinal;
    uint256 public constant MAX_ERC20_ASSETS = 64;
    uint256 public constant MAX_ASSETS = MAX_ERC20_ASSETS + 1;
    uint8 public assetCapacity = 16;
    address public immutable nft;
    address private immutable creator;
    uint256 public constant ROYALTY_SETTLEMENT_VERSION = 4;
    uint256 public constant ROYALTY_ALLOCATION_VERSION = 2;
    uint256 public constant ROYALTY_RECOVERY_VERSION = 2;
    uint256 public constant ACTIVATION_WINDOW = 1 hours;
    uint64 public mintEnd;
    uint64 public mintEndRevision;
    bool private openingFinalized;
    address public canonicalController;
    uint256 private openingCount;
    uint256 private openingWeight;
    // Fresh private packed state: count10, weight12, cursor12, initial1.
    // Original validated write origins remain within1000NFTs/3000tickets.
    mapping(address => uint256) private assetStatus;
    function eligibleCount(address asset) public view returns(uint256) { return _readStatus(asset)&65535; }
    function eligibleWeight(address asset) public view returns(uint256) { return (_readStatus(asset)>>16)&65535; }
    function allocationCursor(address asset) public view returns(uint256) { return (_readStatus(asset)>>32)&65535; }
    function _initialAllocated(address asset) private view returns(bool) {
        return _readStatus(asset)&(uint256(1)<<48)!=0;
    }
    function _readStatus(address asset) private view returns(uint256 value) {
        assembly ("memory-safe") {
            mstore(0,and(asset,0xffffffffffffffffffffffffffffffffffffffff))
            mstore(32,assetStatus.slot)
            value:=sload(keccak256(0,64))
        }
    }
    function _writeStatus(address asset,uint256 mask,uint256 value) private {
        assembly ("memory-safe") {
            mstore(0,and(asset,0xffffffffffffffffffffffffffffffffffffffff))
            mstore(32,assetStatus.slot)
            let location:=keccak256(0,64)
            sstore(location,or(and(sload(location),not(mask)),value))
        }
    }
    mapping(address => uint256) public openingPool;
    // Address zero denotes native ETH and is always the first admitted asset.
    address[] public assets;
    mapping(address => bool) public isAsset;
    mapping(uint256 => uint256) public weightOf;
    uint256 public totalWeight;
    mapping(uint256 => uint256) public ticketStart;
    // Accounted = liabilities + orphaned + openingPool. Raw receipts are above it.
    /// @notice Exact accounted categories; pending raw donations remain above this sum.
    function accounted(address asset) public view returns(uint256) {
        return liabilities[asset]+orphaned[asset]+openingPool[asset];
    }
    mapping(address => uint256) public liabilities;
    mapping(address => uint256) public orphaned;
    mapping(uint256 => mapping(address => uint256)) public accrued;
    uint256 public activationCount;
    mapping(uint256 => uint256) public activationOrdinal;

    error Unauthorized();
    error InvalidConfiguration();
    error InvalidState();
    error ActivationReadUnavailable();
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
    event RoyaltiesAllocated(address indexed asset, uint256 amount, uint256 eligibleCount,
        uint256 eligibleWeight, uint256 cursorBefore, uint256 cursorAfter);

    constructor(address nftController) {
        // The NFT may deploy this receiver from its own constructor.
        if (nftController == address(0)) revert InvalidConfiguration();
        nft = nftController;
        creator = msg.sender;
        isAsset[address(0)] = true;
        assets.push(address(0));
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
        ++mintEndRevision;
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
    /// Existing earned and deferred ticket liabilities never enter this amount.
    /// Admission is separate and bounded; no swap, approval or external recipient.
    function allocateUnallocated(address asset, uint256 amount, bytes32 reviewHash)
        external nonReentrant economic {
        _allocateUnallocated(asset,amount,reviewHash,false);
    }
    /// @notice Allocate every currently unallocated whole unit of ONE currency;
    /// existing earned ticket backing is never included. No holder loop.
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
        _distribute(asset,amount,activationCount,totalWeight);
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
        orphaned[token] = balance;
        _enrollTo(token,activationCount,totalWeight);
        // Post-opening admission keeps the explicit current-weight recovery rule;
        // it cannot silently rewrite the original cutoff cohort.
        _finalizeOpening();
        _writeStatus(token,uint256(1)<<48,openingFinalized?uint256(1)<<48:0);
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
        uint256 syncGas; uint256 balanceCap;
        if(assets.length > 1) {
            IZZZProtocolPolicy policy=IZZZProtocolPolicy(IZZZAccess(canonicalController).protocolPolicy());
            syncGas=policy.royaltySyncGas(); balanceCap=policy.royaltyBalanceGas();
        }
        uint256 successful;
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i];
            bool ok = true;
            if (asset == address(0)) _sync(asset);
            else ok=_syncActivationAsset(asset,syncGas,balanceCap);
            if (ok) successful |= uint256(1) << i;
            else emit RoyaltyAssetDeferred(id, asset);
        }
        weightOf[id] = weight;
        ticketStart[id] = totalWeight + 1;
        totalWeight += weight;
        activationOrdinal[id] = ++activationCount;
        if (firstWeightOrdinal[weight-1] == 0) firstWeightOrdinal[weight-1] = activationCount;
        for (uint256 i; i < assets.length; ++i) if ((successful & (uint256(1) << i)) != 0) {
            _enrollTo(assets[i],activationCount,totalWeight);
        }
        emit Activated(id, weight);
    }

    function _syncActivationAsset(address asset,uint256 syncGas,uint256 balanceCap) private returns(bool ok) {
        // Reserve enough gas for the complete isolated call and tail.
        // Caller underfunding cannot deliberately defer a healthy read.
        // AUTHONLYSELF codec: cap in low32 bits, full-frame witness at bit32.
        uint256 readLimits=balanceCap;
        if(gasleft() >= syncGas + 120_000) readLimits|=uint256(1)<<32;
        bytes memory data = abi.encodeCall(this.syncForActivation,(asset,readLimits));
        uint256 budget = syncGas; uint256 failure; uint256 size;
        assembly ("memory-safe") {
            mstore(0,0)
            ok := call(budget,address(),0,add(data,32),mload(data),0,4)
            failure := shr(224,mload(0))
            size := returndatasize()
        }
        if(!ok && readLimits>>32 == 0 && (size != 4 || failure != uint32(ActivationReadUnavailable.selector)))
            revert InvalidState();
    }

    /// @dev Self-call boundary isolates optional token reverts/OOG/oversized
    /// revert data. External callers must use sync, with the economic guard.
    function syncForActivation(address asset,uint256 readLimits) external {
        if (msg.sender != address(this)) revert Unauthorized();
        _syncBalance(asset,_activationBalance(asset,readLimits));
    }
    /// @dev This read alone is capped; ordinary settlement keeps its full budget.
    /// Copying only the first word preserves ABI-compatible padded returns.
    function _activationBalance(address asset,uint256 readLimits)
        private view returns(uint256 observedBalance) {
        uint256 cap=uint32(readLimits); bool ok;
        // Partial frames must fully fund even a successful gas-sensitive read.
        // Full frames retain the original complete-sync allowance and behavior.
        if(readLimits>>32 == 0 && gasleft() < cap + 120_000) revert InvalidState();
        assembly ("memory-safe") {
            let ptr:=mload(0x40)
            mstore(ptr,shl(224,0x70a08231))
            mstore(add(ptr,4),address())
            ok:=staticcall(cap,asset,ptr,36,ptr,32)
            if lt(returndatasize(),32){ok:=0}
            observedBalance:=mload(ptr)
        }
        if(!ok || observedBalance < accounted(asset)) revert ActivationReadUnavailable();
    }
    function eligibleFor(uint256 id, address asset) public view returns (bool) {
        uint256 ordinal = activationOrdinal[id];
        return isAsset[asset] && ordinal != 0 && ordinal <= effectiveEligibleCount(asset);
    }
    /// @notice Include the sealed opening cohort even before a faulted currency
    /// can materialize its opening allocation. This does not enroll late activations.
    function effectiveEligibleCount(address asset) public view returns (uint256) {
        uint256 cutoff = openingFinalized ? openingCount : activationCount;
        return !_initialAllocated(asset) && royaltiesOpen() && cutoff > eligibleCount(asset) ? cutoff : eligibleCount(asset);
    }
    function _enrollTo(address asset,uint256 count,uint256 weight) private {
        uint256 old=eligibleCount(asset);
        if(count<old)revert InvalidState();
        if(count==old)return;
        uint256 unit=_allocationUnit(count);
        if(unit==0)revert InvalidState();
        ExactRoyaltyAllocation.enrollValidated(enrollment[asset],count,allocationBooks[asset][unit].rounds());
        _writeStatus(asset,4294967295,count|(weight<<16));
    }
    function _enrollWaiting(address asset) private {
        uint256 old = eligibleCount(asset);
        if (old == activationCount) return;
        _enrollTo(asset,activationCount,totalWeight);
        emit RoyaltyEligibilityRecovered(asset, old + 1, activationCount);
    }
    /// @dev Every raw unit becomes one ticket's whole-unit entitlement. Existing
    /// tickets retain their allocation across future activations and claims.
    function _allocationUnit(uint256 count) private view returns(uint256 unit) {
        uint256 firstCommon=firstWeightOrdinal[0];
        uint256 firstRare=firstWeightOrdinal[1];
        uint256 firstLegendary=firstWeightOrdinal[2];
        // Each active bit is exactly (first!=0 && first<=count).
        // A common ticket or both other rarities fixes the unit at one.
        assembly ("memory-safe") {
            let common:=and(iszero(iszero(firstCommon)),iszero(gt(firstCommon,count)))
            let rare:=and(iszero(iszero(firstRare)),iszero(gt(firstRare,count)))
            let legendary:=and(iszero(iszero(firstLegendary)),iszero(gt(firstLegendary,count)))
            unit:=add(mul(rare,2),mul(legendary,3))
            if or(common,and(rare,legendary)){unit:=1}
        }
    }

    function _distribute(address asset,uint256 amount,uint256 count,uint256 weight) private {
        if (amount == 0) return;
        uint256 unit = _allocationUnit(count);
        uint256 beforeCursor = allocationCursor(asset);
        if (unit == 0 || weight%unit != 0 || beforeCursor%unit != 0) revert InvalidState();
        // Reserve actual same-currency backing before modular coefficient writes.
        (uint256 nextCursor,uint256 afterLiability) = allocationBooks[asset][unit].credit(
            amount,weight/unit,beforeCursor/unit,liabilities[asset]);
        liabilities[asset] = afterLiability;
        uint256 afterCursor = nextCursor*unit;
        _writeStatus(asset,uint256(65535)<<32,afterCursor<<32);
        emit RoyaltiesAllocated(asset,amount,count,weight,beforeCursor,afterCursor);
    }

    function _ticketShare(uint256 id,address asset) private view returns(uint256 amount) {
        uint256 ordinal=activationOrdinal[id];
        if(ordinal==0||ordinal>eligibleCount(asset))return 0;
        (uint256 end,uint256 birthRound)=ExactRoyaltyAllocation.birthActivated(enrollment[asset],ordinal);
        uint256 unit=_allocationUnit(end);
        uint256 first=ticketStart[id];uint256 weight=weightOf[id];
        uint256 gross=ExactRoyaltyAllocation.gross(allocationBooks[asset][1],first,first+weight-1);
        unchecked {
            if(unit==1)gross-=birthRound*weight;
            else {
                if(unit!=weight)revert InvalidState();
                uint256 key=(first-1)/weight+1;
                gross+=ExactRoyaltyAllocation.gross(allocationBooks[asset][weight],key,key)-birthRound;
            }
            amount=gross-counterPaid[id][asset];
        }
        if(amount>liabilities[asset])revert InvalidState();
    }

    function pending(address asset) external view returns (uint256) {
        if (_reentrancyGuardEntered()) revert InvalidState();
        if (!isAsset[asset]) revert InvalidConfiguration();
        uint256 balance = _canonicalBalance(asset);
        uint256 prior=accounted(asset);
        if (balance < prior) revert InvalidState();
        return balance - prior;
    }

    function _sync(address asset) private returns (uint256 amount) {
        _finalizeOpening();
        return _syncBalance(asset,_canonicalBalance(asset));
    }
    function _syncBalance(address asset,uint256 balance) private returns(uint256 amount) {
        uint256 prior=accounted(asset);
        if (balance < prior) revert InvalidState();
        amount = balance - prior;
        if (!openingFinalized) {
            openingPool[asset] += amount;
            if (amount != 0) emit RoyaltiesReceived(asset, amount, false);
        } else if (!_initialAllocated(asset)) {
            _writeStatus(asset,uint256(1)<<48,uint256(1)<<48);
            // A currency fault during the grace window must not exclude NFTs
            // which DID activate before cutoff. Its ticket allocation is still empty.
            uint256 old = eligibleCount(asset);
            if (old < openingCount)
                emit RoyaltyEligibilityRecovered(asset, old + 1, openingCount);
            _enrollTo(asset,openingCount,openingWeight);
            uint256 initial = openingPool[asset] + amount;
            openingPool[asset] = 0;
            if (amount != 0) emit RoyaltiesReceived(asset, amount, false);
            if (openingWeight != 0) {
                _distribute(asset,initial,openingCount,openingWeight);
            } else orphaned[asset] += initial;
            emit InitialRoyaltiesAllocated(asset, openingWeight == 0 ? 0 : initial, openingCount, openingWeight);
        } else if (amount != 0) {
            uint256 supply = eligibleWeight(asset);
            if (supply == 0) {
                orphaned[asset] += amount;
            } else {
                _distribute(asset,amount,eligibleCount(asset),supply);
            }
            emit RoyaltiesReceived(asset, amount, supply != 0);
        }
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
        uint256 counter=_ticketShare(id,asset);
        amount=accrued[id][asset]+counter;
        // Imported accrued is paid separately; it must never become round debt.
        unchecked {counterPaid[id][asset]+=counter;}
        accrued[id][asset] = 0;
        liabilities[asset] -= amount;
        _sendRaw(asset,owner,amount);
        // A receiver can return native ETH during its callback; that new inbox
        // payment remains pending. Existing backing must never decrease further.
        if (_canonicalBalance(asset) < accounted(asset)) revert InvalidState();
        emit Claimed(id, asset, owner, amount);
    }

    /// @notice Exact stored units plus the selected pending allocation, without
    /// mutating allocation state or projecting late receipts into a frozen snapshot.
    function claimable(uint256 id, address asset) external view returns (uint256 amount) {
        if (_reentrancyGuardEntered()) revert InvalidState();
        if (!isAsset[asset]) revert InvalidConfiguration();
        if (!royaltiesOpen()) return 0;
        uint256 balance = _canonicalBalance(asset);
        if (balance < accounted(asset)) revert InvalidState();
        amount = accrued[id][asset] + _ticketShare(id,asset);
        if (weightOf[id] == 0 || _state() != 0) return amount;
        uint256 count = eligibleCount(asset);
        uint256 weight = eligibleWeight(asset);
        uint256 receipt = balance - accounted(asset);
        if (!_initialAllocated(asset)) {
            count = openingFinalized ? openingCount : activationCount;
            weight = openingFinalized ? openingWeight : totalWeight;
            receipt += openingPool[asset];
        }
        if (activationOrdinal[id] <= count && weight != 0) {
            uint256 unit = _allocationUnit(count);
            uint256 cursor = allocationCursor(asset);
            if (unit == 0 || weight%unit != 0 || cursor%unit != 0) revert InvalidState();
            uint256 first = (ticketStart[id]-1)/unit+1;
            amount += ExactRoyaltyAllocation.previewShare(receipt,weight/unit,cursor/unit,
                first,first+weightOf[id]/unit-1);
        }
    }

    uint256 private canonicalNFTs;
    uint256 private canonicalAssetTotal;
    uint256 private canonicalWeight;
    uint256[] private canonicalPending;
    bool private canonicalCutoffSettled;
    // Ordinal keys1..1000 and ticket keys1025..4024 are disjoint within
    // the same16-word bitmap; decoded bounds remain checked before marking.
    uint256[16] private canonicalSeen;
    uint256 private canonicalMaxOrdinal;
    mapping(address => uint256) private canonicalImportedClaims;
    // Fresh allocation2 state. Historical raw books are never imported here.
    mapping(address => ExactRoyaltyAllocation.Cohorts) private enrollment;
    mapping(uint256 => mapping(address => uint256)) private counterPaid;
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
            if (!_initialAllocated(asset)) revert CanonicalState();
            uint256 balance = _canonicalBalance(asset);
            if (balance < accounted(asset)) revert CanonicalState();
            canonicalPending.push(balance - accounted(asset));
            _canonicalAdd(asset, balance, 0);
        }
    }
    function canonicalSettle() external canonicalOnly {
        if (_state() != 1 || canonicalCutoffSettled) revert CanonicalState();
        canonicalCutoffSettled = true;
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i]; uint256 amount = canonicalPending[i];
            uint256 supply = eligibleWeight(asset);
            if (supply == 0) orphaned[asset] += amount;
            else { _distribute(asset,amount,eligibleCount(asset),supply); }
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
            return abi.encode(asset, allocationCursor(asset), accounted(asset), liabilities[asset], orphaned[asset], canonicalAmounts[row]);
        }
        row -= canonicalAssetTotal;
        uint256 id = IZZZRoyaltyOrdinals(nft).tokenAtOrdinal(row / (1 + canonicalAssetTotal) + 1);
        uint256 subrow = row % (1 + canonicalAssetTotal);
        if (subrow == 0) return abi.encode(id, weightOf[id], activationOrdinal[id], ticketStart[id]);
        address token = assets[subrow - 1];
        // Frozen royalty rights flatten in bounded VIEW rows. The source round state
        // remains intact for abort; the successor starts with fresh round books.
        return abi.encode(id, token, accrued[id][token] + _ticketShare(id,token));
    }
    function canonicalImport(uint256 row, bytes calldata record) external canonicalOnly {
        _canonicalNext(row);
        if (row == 0) {
            if (totalWeight != 0 || activationCount != 0) revert CanonicalState();
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
            if (record.length != 192) revert CanonicalState();
            (address asset,uint256 cursor,uint256 acc,uint256 liability,uint256 orphan,uint256 backing) =
                abi.decode(record,(address,uint256,uint256,uint256,uint256,uint256));
            if ((row == 0) != (asset == address(0)) || (asset != address(0) && asset.code.length == 0) ||
                liabilities[asset] != 0 || allocationCursor(asset) != 0 || acc != liability + orphan || backing != acc ||
                (canonicalWeight == 0 ? cursor != 0 : cursor >= canonicalWeight)) revert CanonicalState();
            if (assets.length == row) { if (isAsset[asset]) revert CanonicalState(); assets.push(asset); isAsset[asset] = true; }
            if (assets[row] != asset) revert CanonicalState();
            uint256 prefund = _canonicalBalance(asset);
            _canonicalAdd(asset, backing, prefund);
            _writeStatus(asset,(uint256(65535)<<32)|(uint256(1)<<48),(cursor<<32)|(uint256(1)<<48)); liabilities[asset] = liability;
            // Every actual target receipt is an inert prefund, including money
            // synchronized before preparation. Do not retain its old opening category.
            delete openingPool[asset];
            // Header proves acc=liability+orphan. Checked total/subtraction retain
            // the original aggregate-prefund overflow bound by construction.
            orphaned[asset] = (acc + prefund) - liability;
            return;
        }
        row -= canonicalAssetTotal;
        uint256 expected = IZZZRoyaltyOrdinals(nft).tokenAtOrdinal(row / (1 + canonicalAssetTotal) + 1);
        uint256 subrow = row % (1 + canonicalAssetTotal);
        if (subrow == 0) {
            if (record.length != 128) revert CanonicalState();
            (uint256 id,uint256 weight,uint256 ordinal,uint256 first) = abi.decode(record,(uint256,uint256,uint256,uint256));
            if (id != expected || weightOf[id] != 0 || weight > 3 ||
                (weight != 0 && weight != uint256(IZZZRoyaltyOrdinals(nft).rarityOf(id)) + 1)) revert CanonicalState();
            if (weight == 0) { if (ordinal != 0 || first != 0) revert CanonicalState(); }
            else {
                if (ordinal == 0 || ordinal > canonicalNFTs || first == 0 || first+weight-1 > canonicalWeight)
                    revert CanonicalState();
                _markCanonical(ordinal);
                for (uint256 i; i < weight; ++i) _markCanonical(1024+first+i);
                if (ordinal > canonicalMaxOrdinal) canonicalMaxOrdinal = ordinal;
                activationOrdinal[id] = ordinal; ticketStart[id] = first; ++activationCount;
                uint256 earliest = firstWeightOrdinal[weight-1];
                if (earliest == 0 || ordinal < earliest) firstWeightOrdinal[weight-1] = ordinal;
            }
            weightOf[id] = weight; totalWeight += weight;
            return;
        }
        if (record.length != 96) revert CanonicalState();
        (uint256 nftId,address token,uint256 amount) = abi.decode(record,(uint256,address,uint256));
        if (nftId != expected || token != assets[subrow - 1] || (weightOf[nftId] == 0 && amount != 0)) revert CanonicalState();
        accrued[nftId][token] = amount;
        canonicalImportedClaims[token] += amount;
    }
    function _markCanonical(uint256 value) private {
        uint256 bit = uint256(1) << (value & 255);
        if ((canonicalSeen[value >> 8] & bit) != 0) revert CanonicalState();
        canonicalSeen[value >> 8] |= bit;
    }
    function canonicalValidate() external view {
        if (_state() == 2) {
            if (canonicalCursor != canonicalCount() || totalWeight != canonicalWeight || canonicalMaxOrdinal != activationCount)
                revert CanonicalState();
            uint256 unit = _allocationUnit(activationCount);
            for (uint256 i; i < assets.length; ++i) {
                address asset = assets[i];
                if (canonicalImportedClaims[asset] != liabilities[asset] ||
                    (unit != 0 && allocationCursor(asset)%unit != 0)) revert CanonicalState();
            }
        }
        _canonicalValidateBacking();
    }
    /// @dev Every receipt arriving at the inert successor before activation is
    /// quarantined. It cannot become the imported holders' imported entitlement.
    function canonicalActivate() external override canonicalOnly {
        if (_state() != 2) revert CanonicalState();
        for (uint256 i; i < assets.length; ++i) {
            address asset = assets[i];
            uint256 extra = _canonicalBalance(asset) - accounted(asset);
            orphaned[asset] += extra; canonicalPrefunds[i] += extra;
            _enrollTo(asset,activationCount,totalWeight);
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
        amount = _forwardRaw(asset,receiver);
        emit LateRoyaltiesForwarded(asset, receiver, amount);
    }
    /// @notice Only the fixed coordinator may recover a cancelled importer's
    /// remaining receipts after complete backing restoration and reviewed routing.
    /// It supplies the authenticated active canonical royalty receiver, never an
    /// operator-selected wallet. Original imported accounting stays inert.
    function canonicalRecoverCancelled(address asset,address receiver)
        external canonicalOnly nonReentrant returns(uint256 amount) {
        if (_state() != 4) revert CanonicalState();
        return _forwardRaw(asset,receiver);
    }
    function _forwardRaw(address asset,address receiver) private returns(uint256 amount) {
        if (receiver == address(0) || receiver == address(this)) revert CanonicalState();
        amount = _canonicalBalance(asset);
        _sendRaw(asset,receiver,amount);
    }
    function _sendRaw(address asset,address receiver,uint256 amount) private {
        if (amount == 0) return;
        if (asset == address(0)) {
            (bool ok,) = payable(receiver).call{value: amount}("");
            if (!ok) revert NativeTransferFailed();
        } else ExactToken.push(asset,receiver,amount);
    }
}
