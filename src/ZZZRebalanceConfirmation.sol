// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZVault, IZZZPools, IZZZLiquidity, IZZZOracle, IStateViewMinimal} from "./interfaces/IZZZ.sol";
import {IZZZEmergencyVault, IZZZEmergencyBudget} from "./interfaces/IZZZEmergency.sol";

interface IConfirmationStrategy {
    function needsRebalance(uint256) external view returns(bool);
    function rangeUpdatePending(uint256) external view returns(bool);
    function rangeOrientation(bytes32) external view returns(uint8);
    function executionQualityRevision() external view returns(uint64);
    function activeKeeperRangePolicies() external view returns(uint256);
}
interface IConfirmationRegistry { function configurationRevision() external view returns(uint64); }
interface IConfirmationOracle {
    function activePolicy(address) external view returns(bytes32);
    function activeSequencerPolicy() external view returns(bytes32);
}
interface IConfirmationLiquidity { function stateView() external view returns(IStateViewMinimal); }

/// @notice Receipt-backed sampled confirmation, not proof of uninterrupted price.
/// Created by the fixed Strategy. No funds, approvals, execution or custody rights.
contract ZZZRebalanceConfirmation is ZZZModule, ReentrancyGuard {
    uint256 public constant REBALANCE_CONFIRMATION_VERSION = 2;
    uint32 public constant MAX_DURATION = 7 days;
    address public immutable strategy;
    uint32 public duration = 15 minutes;
    /// @notice Zero is unconfigured/stopped; it never disables the safeguard.
    uint32 public maxObservationGap;
    uint64 public policyRevision;
    bytes32 public reviewHash;
    /// @notice Ordinary samples require physical AND independent reference exit.
    /// Governance may explicitly relax this rule; changing/restoring it always
    /// invalidates previous samples. This never disables execution loss guards.
    bool public requireReferenceExit = true;
    bytes32 public referenceReviewHash;
    struct Observation { bytes32 identity; uint64 firstSeen; uint64 lastSeen; uint8 side; }
    mapping(uint256 => Observation) public observations;
    event ConfirmationConfigured(uint32 duration,uint32 maxObservationGap,uint64 revision,bytes32 indexed reviewHash);
    event ConfirmationInvalidated(uint64 revision);
    event ReferenceExitConfigured(bool required,uint64 revision,bytes32 indexed reviewHash);
    event Observed(uint256 indexed bucket,uint8 side,bytes32 indexed identity,uint64 firstSeen,uint64 lastSeen);
    /// @dev 1=no ordinary trigger, 2=read fault, 3=unconfigured/stopped,
    /// 4=manual exception, 5=keeper invalidation after an observed incident.
    event ObservationReset(uint256 indexed bucket,uint8 reason);

    constructor(address controller) ZZZModule(controller) { strategy = msg.sender; }

    /// @notice Review the actual cadence/receipt latency before setting a gap.
    /// Reconfiguration always invalidates prior samples, including change/restore.
    function configure(uint32 secondsRequired,uint32 maximumGap,bytes32 reviewed)
        external onlyGovernance operating principalOperating nonReentrant {
        if(secondsRequired < 60 || secondsRequired > MAX_DURATION || maximumGap > secondsRequired/2 ||
            reviewed == bytes32(0)) revert InvalidConfiguration();
        duration = secondsRequired; maxObservationGap = maximumGap; reviewHash = reviewed;
        ++policyRevision;
        emit ConfirmationConfigured(secondsRequired,maximumGap,policyRevision,reviewed);
    }
    function setRequireReferenceExit(bool required,bytes32 reviewed)
        external onlyGovernance operating principalOperating nonReentrant {
        if(reviewed == bytes32(0)) revert InvalidConfiguration();
        if(required && IConfirmationStrategy(strategy).activeKeeperRangePolicies() != 0) revert InvalidConfiguration();
        requireReferenceExit = required;
        referenceReviewHash = reviewed;
        ++policyRevision;
        emit ReferenceExitConfigured(required,policyRevision,reviewed);
    }
    /// @dev Only the fixed Strategy can invalidate. Its governed orientation
    /// setting remains configurable after LP exit for post-exit buyback context;
    /// invalidation grants no principal readiness or execution capability.
    function invalidatePolicy() external operating {
        if(msg.sender != strategy) revert Unauthorized();
        ++policyRevision;
        emit ConfirmationInvalidated(policyRevision);
    }
    /// @notice Side0=no ordinary candidate, 1=below, 2=above; manual is the
    /// existing deliberate range-change exception, still subject to raw guards.
    function condition(uint256 bucket) public view returns(uint8 side,bytes32 identity,bool manual) {
        return _condition(bucket,false);
    }
    function _condition(uint256 bucket,bool pausedEmergency) private view returns(uint8 side,bytes32 identity,bool manual) {
        if(access.module(Ids.STRATEGY) != strategy || !access.isSealed() || (access.paused() && !pausedEmergency) ||
            access.preparationActive() || access.canonicalState() != 0 || access.lpExitStarted()) return(0,bytes32(0),false);
        IConfirmationStrategy policy = IConfirmationStrategy(strategy);
        if(!policy.needsRebalance(bucket)) return(0,bytes32(0),false);
        if(policy.rangeUpdatePending(bucket)) return(0,bytes32(0),true);
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        address registry = access.module(Ids.POOLS);
        PoolConfig memory c = IZZZPools(registry).accounting(p.poolId);
        address manager = access.module(Ids.LIQUIDITY);
        (int24 lower,int24 upper) = IZZZLiquidity(manager).ticks(p.lpTokenId);
        (,int24 tick,,) = IConfirmationLiquidity(manager).stateView().getSlot0(p.poolId);
        side = tick < lower ? 1 : tick >= upper ? 2 : 0;
        if(side == 0) revert InvalidState(); // Raw and current physical observations must agree.
        if(requireReferenceExit) {
            // Compare the identical physical boundaries in raw token1/token0
            // orientation. No inverted display price, rounded tick or target
            // range can turn disagreement into same-side confirmation.
            if(_referenceSide(c,lower,upper) != side) return(0,bytes32(0),false);
        }
        // Normal feed rounds and fresh token balances do not reset the window.
        // Policy IDs/revisions, physical LP identity and both boundaries do.
        bytes32 physical = keccak256(abi.encode(block.chainid,address(this),bucket,p.poolId,p.lpTokenId,
            p.lastRebalance,lower,upper,manager));
        identity = keccak256(abi.encode(physical,keccak256(abi.encode(c)),
            policy.rangeOrientation(p.poolId),_controlFingerprint(c)));
    }
    /// @notice Pinned-reader explanation, not readiness or permission to trade.
    /// Side0=inside, 1=below, 2=above, in the same raw pool-key orientation.
    function marketSides(uint256 bucket) external view returns(uint8 physical,uint8 referenceSide) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        if(p.lpTokenId == 0) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        address manager = access.module(Ids.LIQUIDITY);
        (int24 lower,int24 upper) = IZZZLiquidity(manager).ticks(p.lpTokenId);
        if(lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper) revert InvalidState();
        (,int24 tick,,) = IConfirmationLiquidity(manager).stateView().getSlot0(p.poolId);
        physical = tick < lower ? 1 : tick >= upper ? 2 : 0;
        referenceSide = _referenceSide(c,lower,upper);
    }
    function _referenceSide(PoolConfig memory c,int24 lower,int24 upper) private view returns(uint8) {
        uint160 price = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0,c.key.currency1);
        if(price < TickMath.MIN_SQRT_PRICE || price >= TickMath.MAX_SQRT_PRICE) revert InvalidState();
        return price < TickMath.getSqrtPriceAtTick(lower) ? 1 : price >= TickMath.getSqrtPriceAtTick(upper) ? 2 : 0;
    }
    /// @notice Stable controls for the complete close/swap/deploy operation.
    /// Same-native-pair moves may change pool ID, but not this asset policy.
    /// Physical LP state and healthy round updates are deliberately excluded.
    function controlFingerprint(bytes32 poolId) external view returns(bytes32) {
        return _controlFingerprint(IZZZPools(access.module(Ids.POOLS)).accounting(poolId));
    }
    /// @notice Stable controls plus the raw record, not readiness of a new LP.
    /// Budget captures this across callbacks and deliberate LP replacement.
    function observationFingerprint(uint256 bucket,bytes32 poolId) external view returns(bytes32) {
        Observation memory o=observations[bucket];
        return keccak256(abi.encode(_controlFingerprint(IZZZPools(access.module(Ids.POOLS)).accounting(poolId)),
            o.identity,o.firstSeen,o.lastSeen,o.side));
    }
    function _controlFingerprint(PoolConfig memory c) private view returns(bytes32) {
        if(c.key.currency0 != address(0) || c.key.currency1 == address(0)) revert InvalidConfiguration();
        address registry = access.module(Ids.POOLS);
        IConfirmationOracle oracle = IConfirmationOracle(access.module(Ids.ORACLE));
        bytes32 first = oracle.activePolicy(c.key.currency0);
        bytes32 second = oracle.activePolicy(c.key.currency1);
        if(first == bytes32(0) || second == bytes32(0)) revert InvalidState();
        bytes32 sources = keccak256(abi.encode(address(oracle),first,second,oracle.activeSequencerPolicy()));
        return keccak256(abi.encode(registry,IConfirmationRegistry(registry).configurationRevision(),sources,
            IConfirmationStrategy(strategy).executionQualityRevision(),policyRevision));
    }
    /// @notice A fresh read never writes/reset samples and fails closed on faults.
    function ready(uint256 bucket) external view returns(bool) {
        (uint8 side,bytes32 identity,bool manual) = condition(bucket);
        if(manual) return true;
        return _ready(observations[bucket],side,identity);
    }
    /// @notice Optional manual-emergency check of still-fresh existing evidence.
    /// Does not record observations while paused or authorize ordinary execution.
    function emergencyReady(uint256 bucket) external view returns(bool) {
        address budget = IZZZEmergencyVault(access.module(Ids.VAULT)).migrationBudget();
        if(msg.sender != budget || !access.paused()) revert Unauthorized();
        IZZZEmergencyBudget(budget).validateEmergency(bucket);
        (uint8 side,bytes32 identity,bool manual) = _condition(bucket,true);
        return manual || _ready(observations[bucket],side,identity);
    }
    function _ready(Observation memory old,uint8 side,bytes32 identity) private view returns(bool) {
        return maxObservationGap != 0 && side != 0 && old.identity == identity && old.side == side &&
            old.firstSeen != 0 && old.firstSeen <= old.lastSeen && old.lastSeen <= block.timestamp &&
            block.timestamp-old.lastSeen <= maxObservationGap && block.timestamp-old.firstSeen >= duration;
    }
    /// @notice Clear only, including during ordinary pause. A worker which saw
    /// an off-chain fault must confirm this reset before extending old evidence.
    function resetObservation(uint256 bucket) external onlyKeeper operating principalOperating nonReentrant {
        delete observations[bucket];
        emit ObservationReset(bucket,5);
    }
    /// @notice A failed observed read clears evidence in a successful transaction;
    /// reverting after deletion would incorrectly restore the previous samples.
    function observe(uint256 bucket) external onlyKeeper live operating principalOperating nonReentrant returns(bool) {
        try this.condition(bucket) returns(uint8 side,bytes32 identity,bool manual) {
            if(manual || side == 0 || maxObservationGap == 0) {
                delete observations[bucket];
                emit ObservationReset(bucket,manual ? 4 : side == 0 ? 1 : 3);
                return manual;
            }
            if(block.timestamp == 0 || block.timestamp > type(uint64).max) revert InvalidState();
            Observation memory old = observations[bucket];
            bool restart = old.identity != identity || old.side != side || old.lastSeen > block.timestamp ||
                old.firstSeen == 0 || block.timestamp-old.lastSeen > maxObservationGap;
            Observation memory next = Observation(identity,restart ? uint64(block.timestamp) : old.firstSeen,
                uint64(block.timestamp),side);
            observations[bucket] = next;
            emit Observed(bucket,side,identity,next.firstSeen,next.lastSeen);
            return _ready(next,side,identity);
        } catch {
            delete observations[bucket];
            emit ObservationReset(bucket,2);
            return false;
        }
    }
}
