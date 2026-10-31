// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZCustodyValidation} from "./ZZZCustodyValidation.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZVault, IZZZPools, IZZZRewards, IZZZNFT, IZZZLiquidity} from "./interfaces/IZZZ.sol";
import {EmergencyRebalance, IZZZEmergencyVault} from "./interfaces/IZZZEmergency.sol";
import {ZZZMigrationBudget} from "./ZZZMigrationBudget.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";

interface IHolderExitVault is IZZZVault {
    function beginLPExit() external;
    function exitBucketToHolders(uint256,uint256,uint256,uint256) external returns(uint256,uint256);
    function closeResidual(uint256,uint256) external;
}
interface IHolderExitNFT is IZZZNFT {
    function mintedCount() external view returns(uint256);
    function tokenAtOrdinal(uint256) external view returns(uint256);
    function refreshMetadata(uint256) external;
}
interface IExitTokenRegistry { function activationAssets() external view returns(address); }
interface IExitTokenIdentity { function zzz() external view returns(address); }

/// @notice Live same-pair movement/parking, or irreversible collective principal
/// return to NFT owners. No external custody address, conversion exit or sweep.
/// Reward ledgers and future royalty rights remain independent of principal.
contract ZZZMigration is ZZZModule, ReentrancyGuard {
    uint8 public constant CUSTODY_VERSION = 4;
    uint256 public constant EMERGENCY_REBALANCE_VERSION = 2;
    uint256 public constant RESIDUAL_EXIT_VERSION = 1;
    uint256 public constant MAX_BATCH = 32;
    enum ExitPhase { Operating, Closing, Allocating, Ready }
    struct ParkingRequest {
        uint256 bucketId; bytes32 poolId; uint256 lpTokenId; uint256 totalShares; uint256 depositUSD;
        uint64 custodyEpoch; uint64 nonce; address token0; address token1;
        uint128 minimum0; uint128 minimum1; uint256 deadline; bytes32 reviewHash; bytes32 portfolioHash;
    }
    struct BucketSettlement {
        uint256 totalShares;
        uint256 ethAmount;
        uint256 zzzAmount;
        uint256 allocatedShares;
        uint256 allocatedETH;
        uint256 allocatedZZZ;
        bool closed;
    }
    struct Principal {
        uint256 ethAmount;
        uint256 zzzAmount;
        bool allocated;
        bool paid;
    }
    address public currentZZZ;
    bytes32 public zzzCodeHash;
    ExitPhase public exitPhase;
    bytes32 public exitReviewHash;
    uint256 public exitMintedCount;
    uint256 public allocationCursor;
    uint256 public remainingBuckets;
    uint256 public remainingETH;
    uint256 public remainingZZZ;
    uint256[] private settlementBuckets;
    mapping(uint256 => BucketSettlement) public bucketSettlement;
    mapping(uint256 => Principal) public principalOf;
    mapping(uint256 => uint64) public custodyEpoch;
    mapping(uint256 => uint64) public parkingNonce;
    ZZZCustodyValidation public immutable validation;
    EmergencyRebalance private emergency;
    event ZZZConfigured(address indexed token,bytes32 codeHash,bytes32 reviewHash);
    event CollectiveExitStarted(bytes32 indexed reviewHash,uint256 mintedCount,uint256 bucketCount);
    event BucketClosed(uint256 indexed bucketId,uint256 totalShares,uint256 ethAmount,uint256 zzzAmount);
    event PrincipalAllocated(uint256 indexed nftId,uint256 indexed bucketId,uint256 ethAmount,uint256 zzzAmount);
    event PrincipalDistributionReady(uint256 totalETH,uint256 totalZZZ);
    event PrincipalPaid(uint256 indexed nftId,address indexed owner,address indexed recipient,uint256 ethAmount,uint256 zzzAmount);
    event PrincipalDeferred(uint256 indexed nftId);
    event ParkingExecuted(bytes32 indexed requestHash,uint256 indexed bucketId,uint64 nonce,uint256 principal0,uint256 principal1);
    event ParkingInvalidated(uint256 indexed bucketId,uint64 nextNonce);
    event ResidualClosed(bytes32 indexed requestHash,uint256 indexed bucketId,uint256 indexed secondaryId,
        uint64 nonce,uint256 principal0,uint256 principal1);
    event EmergencyRebalanced(uint256 indexed bucket,uint8 retainedChecks,bytes32 indexed requestHash,bytes32 indexed reviewHash);

    constructor(address controller) ZZZModule(controller) {
        validation = new ZZZCustodyValidation(controller);
    }
    receive() external payable {
        if(msg.sender != access.module(Ids.VAULT)) revert Unauthorized();
    }
    function _vault() private view returns(IHolderExitVault) {
        return IHolderExitVault(access.module(Ids.VAULT));
    }
    function _nft() private view returns(IHolderExitNFT) {
        return IHolderExitNFT(access.module(Ids.NFT));
    }
    /// @notice Manual governance-only emergency, while paused. Never a keeper
    /// fallback. Disabled economic checks accept the explicitly reviewed risk;
    /// native ETH/fixed ZZZ, exact accounting and all lifecycle locks remain.
    function emergencyRebalance(EmergencyRebalance calldata request)
        external onlyGovernance operating principalOperating nonReentrant {
        _deadline(request.deadline);
        if(!access.isSealed() || !access.paused() || request.checks > 31 || request.bucket == 0 ||
            request.custodyHash != emergencyCustodyHash(request.bucket) ||
            request.amountIn > uint128(type(int128).max) || request.minimumOut > uint128(type(int128).max) ||
            request.minimumLiquidity == 0 || request.lower < TickMath.MIN_TICK || request.upper > TickMath.MAX_TICK ||
            request.lower >= request.upper || request.reviewHash == bytes32(0) ||
            (request.amountIn == 0 ? request.swapPool != bytes32(0) || request.minimumOut != 0 :
                request.swapPool == bytes32(0) || request.minimumOut == 0)) revert InvalidConfiguration();
        ZZZMigrationBudget budget = ZZZMigrationBudget(IZZZEmergencyVault(address(_vault())).migrationBudget());
        emergency = request;
        budget.beginEmergency(request.bucket,request.checks);
        bytes32 context = budget.emergencyFingerprint();
        IZZZEmergencyVault(address(_vault())).emergencyRebalance(request.bucket,request.minimumLiquidity,request.deadline);
        if(budget.emergencyFingerprint() != context) revert InvalidState();
        budget.endEmergency();
        delete emergency;
        emit EmergencyRebalanced(request.bucket,request.checks,
            keccak256(abi.encode(block.chainid,address(this),address(_vault()),request)),request.reviewHash);
    }
    function emergencyFingerprint() external view returns(bytes32 result) {
        ZZZMigrationBudget budget = ZZZMigrationBudget(IZZZEmergencyVault(address(_vault())).migrationBudget());
        if(msg.sender != address(budget)) revert Unauthorized();
        EmergencyRebalance memory request = emergency;
        budget.validateEmergency(request.bucket);
        return validation.emergencyFingerprint(request);
    }
    function emergencyRequest() external view returns(EmergencyRebalance memory) { return emergency; }
    function emergencyTarget() external view returns(int24,int24) { return(emergency.lower,emergency.upper); }
    /// @notice Review-time physical/accounting identity. Price changes alone do
    /// not replace the LP, but a top-up, park, move or share change invalidates it.
    function emergencyCustodyHash(uint256 bucket) public view returns(bytes32) {
        return validation.emergencyCustodyHash(bucket);
    }
    /// @notice Compatibility read for ordinary same-chain canonical snapshots.
    /// No external-custody plans exist in this implementation.
    function activePlan(uint256) external pure returns(bytes32) { return bytes32(0); }
    function outstandingCount() external pure returns(uint256) { return 0; }
    function settlementBucketCount() external view returns(uint256) { return settlementBuckets.length; }
    function settlementBucketAt(uint256 index) external view returns(uint256) { return settlementBuckets[index]; }

    /// @notice Bootstrap-only binding of the same fixed ZZZ used by contributions
    /// and buybacks. This is not an external recipient or a replaceable token.
    function configureZZZ(address token,bytes32 codeHash,bytes32 reviewHash) external onlyGovernance nonReentrant {
        if(access.isSealed() || currentZZZ != address(0) || token.code.length == 0 || token.codehash != codeHash ||
            reviewHash == bytes32(0) || !IZZZRewards(access.module(Ids.REWARDS)).isAsset(token)) revert InvalidConfiguration();
        address buyback = access.module(Ids.BUYBACK);
        address source = IExitTokenRegistry(access.module(Ids.POOLS)).activationAssets();
        if(buyback.code.length == 0 || IExitTokenIdentity(buyback).zzz() != token ||
            IExitTokenIdentity(source).zzz() != token) revert InvalidConfiguration();
        currentZZZ = token;
        zzzCodeHash = codeHash;
        emit ZZZConfigured(token,codeHash,reviewHash);
    }

    /// @notice Governance commits an irreversible LP shutdown while paused.
    /// Validate EVERY funded bucket before locking; no oracle or swap is needed.
    /// No mint, activation, growth, rebalance, resume or canonical replacement may
    /// subsequently reopen LP. NFT transfers and reward/royalty claims continue.
    function beginCollectiveExit(bytes32 reviewHash) external onlyGovernance operating nonReentrant {
        if(!access.isSealed() || !access.paused() || access.lpExitStarted() || exitPhase != ExitPhase.Operating ||
            reviewHash == bytes32(0) || currentZZZ == address(0)) revert InvalidState();
        IHolderExitVault vault = _vault();
        uint256 count = vault.bucketCount();
        if(count > vault.MAX_BUCKETS()) revert InvalidState();
        for(uint256 i; i<count; ++i) {
            uint256 bucket = vault.bucketAt(i);
            Position memory p = vault.group(bucket);
            uint256 shares = vault.bucketTotalShares(bucket);
            if(shares == 0) {
                if(p.lpTokenId != 0 || p.idle0 != 0 || p.idle1 != 0 || p.status != PositionStatus.None) revert InvalidState();
                continue;
            }
            if((p.status != PositionStatus.Active && p.status != PositionStatus.Parked) ||
                (p.status == PositionStatus.Active && p.lpTokenId == 0) ||
                (p.status == PositionStatus.Parked && p.lpTokenId != 0)) revert InvalidState();
            PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
            if(c.key.currency0 != address(0) || c.key.currency1 != currentZZZ) revert InvalidConfiguration();
            bucketSettlement[bucket].totalShares = shares;
            settlementBuckets.push(bucket);
        }
        remainingBuckets = settlementBuckets.length;
        exitMintedCount = _nft().mintedCount();
        if(remainingBuckets == 0 || exitMintedCount == 0 || exitMintedCount > 1000) revert InvalidState();
        exitReviewHash = reviewHash;
        exitPhase = ExitPhase.Closing;
        // The nonreentrant Vault barrier rejects a start during any in-flight
        // contribution, LP execution or principal callback before setting Access.
        vault.beginLPExit();
        if(!access.lpExitStarted()) revert InvalidState();
        emit CollectiveExitStarted(reviewHash,exitMintedCount,remainingBuckets);
    }

    /// @notice Close one snapshotted bucket without swaps. Raw minima cover all
    /// returned principal: LP proceeds + attributed idle + pending compounding.
    /// Only exact operation deltas enter settlement; prefunds are never assigned.
    function closeBucket(uint256 bucket,uint256 minimumETH,uint256 minimumZZZ,uint256 deadline)
        external onlyGovernance operating nonReentrant {
        _deadline(deadline);
        BucketSettlement storage s = bucketSettlement[bucket];
        if(exitPhase != ExitPhase.Closing || !access.lpExitStarted() || !access.paused() ||
            s.totalShares == 0 || s.closed || _vault().bucketTotalShares(bucket) != s.totalShares) revert InvalidState();
        uint256 beforeETH = address(this).balance;
        uint256 beforeZZZ = ExactAsset.balance(currentZZZ,address(this));
        (uint256 ethAmount,uint256 zzzAmount) = _vault().exitBucketToHolders(bucket,minimumETH,minimumZZZ,deadline);
        if(address(this).balance != beforeETH+ethAmount ||
            ExactAsset.balance(currentZZZ,address(this)) != beforeZZZ+zzzAmount ||
            _vault().group(bucket).status != PositionStatus.Exited ||
            _vault().bucketTotalShares(bucket) != s.totalShares) revert InvalidState();
        s.ethAmount = ethAmount; s.zzzAmount = zzzAmount; s.closed = true;
        remainingETH += ethAmount; remainingZZZ += zzzAmount;
        ++custodyEpoch[bucket];
        if(--remainingBuckets == 0) {
            if (IZZZLiquidity(access.module(Ids.LIQUIDITY)).activeSecondaryCount() != 0) revert InvalidState();
            exitPhase = ExitPhase.Allocating;
            allocationCursor = 1;
        }
        emit BucketClosed(bucket,s.totalShares,ethAmount,zzzAmount);
    }

    /// @notice Permissionless bounded deterministic apportionment. Cumulative
    /// floors in immutable mint order allocate every raw unit without a sweep.
    /// Transfers do not change shares; unclaimed principal follows the NFT.
    function allocatePrincipal(uint256 maximum) external operating nonReentrant {
        if(exitPhase != ExitPhase.Allocating || maximum == 0 || maximum > MAX_BATCH) revert InvalidState();
        IHolderExitNFT nft = _nft(); IHolderExitVault vault = _vault();
        uint256 end = Math.min(allocationCursor+maximum,exitMintedCount+1);
        for(uint256 ordinal=allocationCursor; ordinal<end; ++ordinal) {
            uint256 id = nft.tokenAtOrdinal(ordinal);
            if(id == 0 || principalOf[id].allocated) revert InvalidState();
            uint256 shares = vault.sharesOf(id); uint256 bucket = vault.nftBucket(id);
            Principal storage p = principalOf[id]; p.allocated = true;
            if(shares == 0) {
                if(bucket != 0) revert InvalidState();
                continue;
            }
            BucketSettlement storage s = bucketSettlement[bucket];
            if(!s.closed || s.totalShares == 0) revert InvalidState();
            uint256 cumulative = s.allocatedShares+shares;
            if(cumulative > s.totalShares) revert InvalidState();
            uint256 ethTotal = Math.mulDiv(s.ethAmount,cumulative,s.totalShares);
            uint256 zzzTotal = Math.mulDiv(s.zzzAmount,cumulative,s.totalShares);
            p.ethAmount = ethTotal-s.allocatedETH; p.zzzAmount = zzzTotal-s.allocatedZZZ;
            s.allocatedShares = cumulative; s.allocatedETH = ethTotal; s.allocatedZZZ = zzzTotal;
            emit PrincipalAllocated(id,bucket,p.ethAmount,p.zzzAmount);
            // Bounded ERC-4906 event only: no receiver callback or price read.
            nft.refreshMetadata(id);
        }
        allocationCursor = end;
        if(end == exitMintedCount+1) {
            for(uint256 i; i<settlementBuckets.length; ++i) {
                BucketSettlement memory s = bucketSettlement[settlementBuckets[i]];
                if(s.allocatedShares != s.totalShares || s.allocatedETH != s.ethAmount || s.allocatedZZZ != s.zzzAmount)
                    revert InvalidState();
            }
            _backed(); exitPhase = ExitPhase.Ready;
            emit PrincipalDistributionReady(remainingETH,remainingZZZ);
        }
    }
    function claimablePrincipal(uint256 id) external view returns(uint256 ethAmount,uint256 zzzAmount) {
        Principal memory p = principalOf[id];
        if(exitPhase != ExitPhase.Ready || !p.allocated) revert NotReady();
        return p.paid ? (uint256(0),uint256(0)) : (p.ethAmount,p.zzzAmount);
    }
    /// @notice Anyone may pay the CURRENT NFT owner. Each bounded inner call is
    /// isolated: a rejecting or gas-consuming owner cannot block other owners.
    /// A deferred NFT remains fully backed and can retry or use owner fallback.
    function distributePrincipal(uint256[] calldata ids) external operating nonReentrant returns(uint256 paid) {
        if(exitPhase != ExitPhase.Ready || ids.length == 0 || ids.length > MAX_BATCH) revert InvalidState();
        uint256 payoutGas = IZZZProtocolPolicy(access.protocolPolicy()).payoutGas();
        for(uint256 i; i<ids.length; ++i) {
            if(gasleft() < payoutGas+60000) break;
            Principal memory p = principalOf[ids[i]];
            if(!p.allocated || p.paid || (p.ethAmount == 0 && p.zzzAmount == 0)) continue;
            try this.payCurrentOwner{gas:payoutGas}(ids[i]) { ++paid; }
            catch { emit PrincipalDeferred(ids[i]); }
        }
    }
    /// @dev Self-only isolation boundary, never a caller-selected beneficiary.
    function payCurrentOwner(uint256 id) external {
        if(msg.sender != address(this)) revert Unauthorized();
        _pay(id,_nft().ownerOf(id));
    }
    /// @notice Optional recovery for a receiver that rejects an automatic push.
    /// Only the actual current owner (not an ERC721 approval) chooses recipient.
    function claimPrincipal(uint256 id,address recipient) external operating nonReentrant {
        if(_nft().ownerOf(id) != msg.sender) revert Unauthorized();
        _pay(id,recipient);
    }
    function _pay(uint256 id,address recipient) private {
        Principal storage p = principalOf[id];
        if(exitPhase != ExitPhase.Ready || !p.allocated || p.paid || (p.ethAmount == 0 && p.zzzAmount == 0) ||
            recipient == address(0) || recipient == address(this))
            revert InvalidState();
        address owner = _nft().ownerOf(id);
        _backed();
        p.paid = true;
        remainingETH -= p.ethAmount; remainingZZZ -= p.zzzAmount;
        ExactAsset.push(currentZZZ,recipient,p.zzzAmount);
        ExactAsset.push(address(0),recipient,p.ethAmount);
        _backed();
        emit PrincipalPaid(id,owner,recipient,p.ethAmount,p.zzzAmount);
    }
    function _backed() private view {
        if(address(this).balance < remainingETH || ExactAsset.balance(currentZZZ,address(this)) < remainingZZZ) revert InvalidState();
    }

    /// @notice Atomic pool-to-pool move while LP is operating. No holder payout
    /// or external recipient is involved; actual ordered currencies must match.
    function moveFunds(uint256 id,bytes32 pool,uint128 minimum,uint256 deadline)
        external onlyGovernance live principalOperating nonReentrant {
        _vault().movePool(id,pool,minimum,deadline);
    }
    function resume(uint256 id,bytes32 pool,uint128 minimum,uint256 deadline)
        external onlyGovernance live principalOperating nonReentrant {
        _vault().resume(id,pool,minimum,deadline);
    }
    function park(ParkingRequest calldata r) external onlyDrainGovernance principalOperating nonReentrant {
        _deadline(r.deadline); IHolderExitVault vault = _vault(); Position memory p = vault.group(r.bucketId);
        validation.validateParking(abi.encode(r)); ++parkingNonce[r.bucketId];
        vault.park(r.bucketId,r.deadline); Position memory afterPosition = vault.group(r.bucketId);
        uint256 a0 = afterPosition.idle0-p.idle0; uint256 a1 = afterPosition.idle1-p.idle1;
        if(afterPosition.status != PositionStatus.Parked || afterPosition.lpTokenId != 0 ||
            IZZZLiquidity(access.module(Ids.LIQUIDITY)).secondaryId(r.lpTokenId) != 0 ||
            a0 < r.minimum0 || a1 < r.minimum1) revert Slippage();
        emit ParkingExecuted(keccak256(abi.encode(block.chainid,address(this),address(vault),r)),r.bucketId,r.nonce,a0,a1);
    }
    /// @notice Manually close only the associated residual into Vault-attributed
    /// idle, without a swap, external payout or replacement of the main LP.
    /// The reviewed desired mode is unchanged; disable it separately to prevent
    /// a future whole adjustment from creating another residual.
    function closeResidual(ParkingRequest calldata r)
        external onlyGovernance operating principalOperating nonReentrant {
        _deadline(r.deadline);
        validation.validateParking(abi.encode(r));
        IHolderExitVault vault=_vault();
        IZZZLiquidity manager=IZZZLiquidity(access.module(Ids.LIQUIDITY));
        uint256 secondary=manager.secondaryId(r.lpTokenId);
        if(secondary==0)revert InvalidState();
        Position memory beforePosition=vault.group(r.bucketId);
        bytes32 mainState=validation.residualMainFingerprint(r.bucketId);
        ++parkingNonce[r.bucketId];
        vault.closeResidual(r.bucketId,r.deadline);
        Position memory afterPosition=vault.group(r.bucketId);
        uint256 a0=afterPosition.idle0-beforePosition.idle0;
        uint256 a1=afterPosition.idle1-beforePosition.idle1;
        if(!access.isSealed() || !access.paused() ||
            validation.residualMainFingerprint(r.bucketId)!=mainState ||
            parkingNonce[r.bucketId]!=r.nonce+1 || custodyEpoch[r.bucketId]!=r.custodyEpoch ||
            manager.secondaryId(r.lpTokenId)!=0 || a0<r.minimum0 || a1<r.minimum1)revert Slippage();
        ++custodyEpoch[r.bucketId];
        emit ResidualClosed(keccak256(abi.encode(block.chainid,address(this),address(vault),r)),
            r.bucketId,secondary,r.nonce,a0,a1);
    }
    function invalidateParking(uint256 id) external onlyDrainGovernance principalOperating {
        ++parkingNonce[id]; emit ParkingInvalidated(id,parkingNonce[id]);
    }
}

