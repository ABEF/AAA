// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {IZZZAccess, IZZZOracle, IZZZVault, IZZZPools, IZZZFees, IZZZLiquidity, IZZZStrategy} from "./interfaces/IZZZ.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";

interface IPricingVault { function migrationBudget() external view returns (address); }
interface IPricingEntry {
    function pricingContext(uint256,bytes32,uint256,uint256) external view returns (bool);
}
interface IPricingAssets { function assetCount() external view returns(uint256); function assets(uint256) external view returns(address); }
interface IPricingBudget {
    function compositionEpoch(uint256) external view returns(uint64);
    function contributionLossBps() external view returns(uint16);
    function lastCompound(uint256) external view returns(uint64);
    function compoundInterval(bytes32) external view returns(uint32);
}
interface IPricingPortfolio {function minimumMainBps(bytes32) external view returns(uint16);}

/// @notice Fixed Oracle-created accounting companion. No funds, approvals, user
/// setter, arbitrary call or sweep. A whole contribution uses one price vector.
contract ZZZContributionPricing {
    uint256 public constant ENTRY_REVIEW_VERSION = 2;
    IZZZAccess public immutable access;
    IZZZOracle public immutable oracle;
    // Oracle USD18 prices are at most 1e36, below uint128.max. Packing the
    // bounds saves one persistent slot per marked asset. ABI field order and
    // padded values stay identical, including the final basis fingerprint.
    struct Mark { uint128 lower; uint128 upper; uint256 scale; bytes32 fingerprint; }
    struct Basis {
        bytes32 pool;
        uint256 nft;
        uint256 bucket;
        uint256 lowerInput;
        uint256 upperInput;
        uint160 putSpot;
        uint8 phase;
        bool entry;
        address token0;
        address token1;
        uint32 limits;
        uint16 maxIdleBps;
        bytes32 entryPolicyFingerprint;
    }
    struct MaintenanceMark {
        uint256 value; uint256 price0; uint256 price1; uint256 scale0; uint256 scale1;
        uint256 idle0; uint256 idle1;
        uint16 maxIdleBps;bytes32 maintenancePolicy;
    }
    Basis private basis;
    mapping(address => Mark) private marks;
    address[] private assets;
    error Unauthorized();
    error InvalidState();
    error InvalidAmount();
    error Slippage();
    event ContributionVerified(uint256 indexed nftId,uint256 indexed bucketId,uint256 inputLowerUSD,
        uint256 inputUpperUSD,uint256 marginalDeployedUSD,uint256 netUSD,uint160 spotX96,bytes32 basisHash);

    constructor(address controller,address priceOracle) {
        if (msg.sender != priceOracle || controller.code.length == 0) revert Unauthorized();
        access = IZZZAccess(controller); oracle = IZZZOracle(priceOracle);
    }
    modifier onlyBudget() {
        if (msg.sender != IPricingVault(access.module(Ids.VAULT)).migrationBudget()) revert Unauthorized();
        _;
    }
    function _entry() private view returns(address) { return IZZZPools(access.module(Ids.POOLS)).activationEntry(); }
    function _live() private view {
        if (!access.isSealed() || access.paused() || access.preparationActive() || access.canonicalState() != 0) revert InvalidState();
    }
    function active() external view returns(bool) { return basis.phase != 0; }
    function _protocolPolicy() private view returns(IZZZProtocolPolicy){return IZZZProtocolPolicy(access.protocolPolicy());}
    /// @notice The fixed Budget may only use the contribution cap captured
    /// before external input movement, never a guessed current/default value.
    function entryIdleLimit(uint256 bucket) external view onlyBudget returns(uint16){
        if(basis.phase==0 || basis.phase>4 || basis.bucket!=bucket)revert InvalidState();
        return basis.maxIdleBps;
    }
    function assertDeployed(uint256 bucket,uint16 maxIdleBps) external view onlyBudget {
        if(maxIdleBps>4000)revert InvalidState();
        (uint256 deployed,uint256 idle)=nav(bucket);
        if(deployed==0 || idle>Math.mulDiv(deployed+idle,maxIdleBps,10000))revert Slippage();
    }
    /// @notice Typed read-only extraction of the Budget's post-maintenance
    /// value proof. The starting vector/caps remain captured by its fixed caller;
    /// source scope cannot be repriced or relaxed by a later governance callback.
    function checkMaintenance(uint256 bucket,uint256 beforeValue,uint256 price0,uint256 price1,
        uint256 scale0,uint256 scale1,uint16 lossBps,uint16 maxIdleBps,bytes32 expectedMaintenancePolicy)
        external view onlyBudget returns(uint256 deployed,uint256 idle,bytes32 poolId) {
        if(beforeValue==0 || lossBps>1000 || maxIdleBps>4000 ||
            _protocolPolicy().maintenanceFingerprint()!=expectedMaintenancePolicy)revert InvalidState();
        Position memory p=IZZZVault(access.module(Ids.VAULT)).group(bucket);poolId=p.poolId;
        (deployed,idle)=_maintenanceValues(p,price0,price1,scale0,scale1);
        uint256 retained=deployed+idle;
        if(retained<beforeValue-Math.mulDiv(beforeValue,lossBps,10000) || deployed==0 ||
            idle>Math.mulDiv(retained,maxIdleBps,10000))revert Slippage();
    }
    function compoundReady(uint256 bucket) external view onlyBudget returns(bool) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        if(p.status != PositionStatus.Active || p.lpTokenId == 0) return false;
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if(!c.operationsEnabled) return false;
        IPricingBudget budget = IPricingBudget(msg.sender);
        uint256 previous = budget.lastCompound(bucket);
        if(p.lastRebalance > previous) previous = p.lastRebalance;
        if(block.timestamp < previous+budget.compoundInterval(p.poolId)) return false;
        IZZZStrategy strategy = IZZZStrategy(access.module(Ids.STRATEGY));
        return !strategy.needsRebalance(bucket) && strategy.keeperRangeTarget(p.poolId) == 0;
    }
    /// @notice Stateless exact valuation for the fixed Budget's captured vector.
    /// This shares accounting math; it creates no new authority or price fallback.
    function markMaintenance(uint256 bucket) external view onlyBudget returns(MaintenanceMark memory mark) {
        IZZZProtocolPolicy policy=_protocolPolicy();
        IZZZProtocolPolicy.MaintenancePolicy memory limits=policy.maintenancePolicy();
        mark.maxIdleBps=limits.maxIdleBps;
        mark.maintenancePolicy=keccak256(abi.encode(address(policy),limits));
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        mark.price0 = oracle.price(c.key.currency0); mark.price1 = oracle.price(c.key.currency1);
        mark.scale0 = 10 ** oracle.tokenDecimals(c.key.currency0); mark.scale1 = 10 ** oracle.tokenDecimals(c.key.currency1);
        mark.idle0 = p.idle0; mark.idle1 = p.idle1;
        (uint256 deployed,uint256 idle) = _maintenanceValues(p,mark.price0,mark.price1,mark.scale0,mark.scale1);
        mark.value = deployed+idle;
    }
    /// @notice Post-replacement utilization uses actual physical principal and
    /// the Budget's starting USD vector. The main floor, residual ceiling and
    /// idle ceiling are independent of the operation's execution-loss budget.
    function assertPortfolioUtilization(uint256 bucket,uint256 price0,uint256 price1,uint256 scale0,uint256 scale1)
        external view onlyBudget {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        IZZZLiquidity manager = IZZZLiquidity(access.module(Ids.LIQUIDITY));
        (uint256 a0,uint256 a1) = manager.amounts(p.lpTokenId);
        uint256 main = Math.mulDiv(a0,price0,scale0)+Math.mulDiv(a1,price1,scale1);
        uint256 secondary = manager.secondaryId(p.lpTokenId);
        uint256 residual;
        if (secondary != 0) {
            (a0,a1) = manager.amounts(secondary);
            residual = Math.mulDiv(a0,price0,scale0)+Math.mulDiv(a1,price1,scale1);
        }
        uint256 retained = main+residual+Math.mulDiv(p.idle0,price0,scale0)+Math.mulDiv(p.idle1,price1,scale1);
        uint16 floor=IPricingPortfolio(IZZZStrategy(access.module(Ids.STRATEGY)).portfolioPolicy()).minimumMainBps(p.poolId);
        if (main < Math.mulDiv(retained,floor,10000,Math.Rounding.Ceil) ||
            residual > Math.mulDiv(retained,10000-floor,10000)) revert Slippage();
    }
    function _maintenanceValues(Position memory p,uint256 price0,uint256 price1,uint256 scale0,uint256 scale1)
        private view returns(uint256 deployed,uint256 idle) {
        if(p.lpTokenId != 0) {
            (uint256 a0,uint256 a1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).portfolioAmounts(p.lpTokenId);
            deployed = Math.mulDiv(a0,price0,scale0)+Math.mulDiv(a1,price1,scale1);
        }
        idle = Math.mulDiv(p.idle0,price0,scale0)+Math.mulDiv(p.idle1,price1,scale1);
    }
    function _mark(address token) private {
        if (marks[token].lower != 0) return;
        if (assets.length == 34) revert InvalidState();
        (uint256 lower,uint256 upper,bytes32 fingerprint) = oracle.priceBounds(token);
        if (lower == 0 || upper < lower || upper > type(uint128).max) revert InvalidState();
        marks[token] = Mark(uint128(lower),uint128(upper),10 ** oracle.tokenDecimals(token),fingerprint);
        assets.push(token);
    }
    function _pair(bytes32 pool) private {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(pool);
        basis.pool = pool; basis.token0 = c.key.currency0; basis.token1 = c.key.currency1;
        IZZZProtocolPolicy policy=_protocolPolicy();
        IZZZProtocolPolicy.EntryPolicy memory entry=policy.entryPolicy();
        basis.maxIdleBps=entry.maxIdleBps;
        basis.entryPolicyFingerprint=keccak256(abi.encode(address(policy),entry));
        // Entry freezes operating limits before the original-source transfer
        // and conversion, not only when it eventually enters the Vault.
        uint16 cap = IPricingBudget(IPricingVault(access.module(Ids.VAULT)).migrationBudget()).contributionLossBps();
        if (cap > 1000 || c.maxSlippageBps > 1000) revert InvalidState();
        basis.limits = uint32(c.maxSlippageBps) | (uint32(cap) << 16);
        _mark(c.key.currency0); _mark(c.key.currency1);
    }
    function _historicalMarks(uint256 bucket) private {
        if (bucket == 0) return;
        // Before the first custody composition, compound belongs only to the
        // already marked current pair. Unrelated global reward assets cannot
        // be this bucket's historical principal backing.
        IPricingBudget budget = IPricingBudget(IPricingVault(access.module(Ids.VAULT)).migrationBudget());
        if (budget.compositionEpoch(bucket) == 0) return;
        IPricingAssets admitted = IPricingAssets(access.module(Ids.REWARDS));
        uint256 count = admitted.assetCount();
        if (count > 33) revert InvalidState();
        for (uint256 i; i < count; ++i) {
            address token = admitted.assets(i);
            if (token == basis.token0 || token == basis.token1) continue;
            if (IZZZFees(access.module(Ids.FEES)).compoundBalance(bucket,token) != 0) _mark(token);
        }
    }
    /// @dev Entry calls BEFORE token pulls, approvals or conversion. No later
    /// quote can replace this original-source value or LP-pair price basis.
    /// @notice Freeze the reviewed Entry basis and enforce the caller's maximum loss.
    function beginEntryReviewed(uint256 nft,bytes32 pool,address source,uint256 amount,uint16 maximumLossBps,
        bytes32 expectedContributionPolicy)
        external returns(uint256 lowerUSD) {
        if (msg.sender != _entry()) revert Unauthorized();
        _live(); if (basis.phase != 0 || amount == 0) revert InvalidState();
        if (maximumLossBps > 1000) revert InvalidAmount();
        basis.phase = 1; basis.entry = true; basis.nft = nft;
        _pair(pool);
        if(expectedContributionPolicy==bytes32(0) || basis.entryPolicyFingerprint!=expectedContributionPolicy)revert InvalidState();
        if (uint16(basis.limits >> 16) > maximumLossBps) revert Slippage();
        _mark(source);
        Mark memory m = marks[source];
        lowerUSD = Math.mulDiv(amount,m.lower,m.scale);
        basis.lowerInput = lowerUSD;
        basis.upperInput = Math.mulDiv(amount,m.upper,m.scale,Math.Rounding.Ceil);
        _historicalMarks(IZZZVault(access.module(Ids.VAULT)).poolBucket(pool));
    }
    /// @dev Existing Vault ABI carries both bounded raw amounts in one word:
    /// low128=amount0, high128=amount1. This is not a supplied USD claim.
    function begin(uint256 nft,uint256 bucket,uint256 packed,uint256 inputUSD,uint32 limits) external onlyBudget {
        _live();
        bytes32 pool = IZZZVault(access.module(Ids.VAULT)).group(bucket).poolId;
        if (basis.phase != 0) {
            if (!basis.entry || basis.phase != 1 || basis.pool != pool || basis.nft != nft ||
                basis.lowerInput != inputUSD || !IPricingEntry(_entry()).pricingContext(nft,pool,packed,inputUSD)) revert InvalidState();
        } else {
            basis.phase = 1; basis.nft = nft; _pair(pool);
            uint256 a0 = uint128(packed); uint256 a1 = packed >> 128;
            basis.lowerInput = _pairValue(a0,a1);
            basis.upperInput = _upper(basis.token0,a0) + _upper(basis.token1,a1);
            if (inputUSD != basis.lowerInput) revert InvalidAmount();
            _historicalMarks(bucket);
        }
        // A callback cannot adopt a later, wider governance/venue policy.
        // Even a tightening during this operation requires a fresh review.
        if (basis.limits != limits) revert InvalidState();
        basis.bucket = bucket;
        // Conversion/pull callbacks may not replace policies or round data.
        _unchanged();
    }
    function _lower(address token,uint256 amount) private view returns(uint256) {
        if (amount == 0) return 0;
        if (basis.phase == 0) return oracle.value(token,amount);
        Mark memory m = marks[token];
        if (m.lower == 0) revert InvalidState();
        return Math.mulDiv(amount,m.lower,m.scale);
    }
    function _upper(address token,uint256 amount) private view returns(uint256) {
        if (amount == 0) return 0;
        Mark memory m = marks[token];
        if (m.upper == 0) revert InvalidState();
        return Math.mulDiv(amount,m.upper,m.scale,Math.Rounding.Ceil);
    }
    function _pairValue(uint256 amount0,uint256 amount1) private view returns(uint256) {
        return _lower(basis.token0,amount0) + _lower(basis.token1,amount1);
    }
    function valueBucket(uint256 bucket,uint256 amount0,uint256 amount1) public view returns(uint256) {
        if (basis.phase != 0 && basis.bucket == bucket) return _pairValue(amount0,amount1);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(access.module(Ids.VAULT)).group(bucket).poolId);
        return oracle.value(c.key.currency0,amount0) + oracle.value(c.key.currency1,amount1);
    }
    function nav(uint256 bucket) public view returns(uint256 deployed,uint256 idle) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        if (p.lpTokenId != 0) {
            (uint256 a0,uint256 a1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).portfolioAmounts(p.lpTokenId);
            deployed = valueBucket(bucket,a0,a1);
        }
        idle = valueBucket(bucket,p.idle0,p.idle1);
    }
    /// @notice Exact attributed idle only; deliberately independent of physical
    /// LP reads, principal activity and terminal valuation availability.
    function idleValue(uint256 bucket) external view onlyBudget returns(uint256) {
        Position memory p=IZZZVault(access.module(Ids.VAULT)).group(bucket);
        PoolConfig memory c=IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        return oracle.value(c.key.currency0,p.idle0)+oracle.value(c.key.currency1,p.idle1);
    }
    /// @dev The Vault already performs these three marks in fixed order: before
    /// its deliberate balancing swap, before _put, and after every _put callback.
    function contributionNav(uint256 bucket) external onlyBudget returns(uint256 deployed,uint256 idle) {
        if (basis.phase == 0 || basis.phase > 3 || basis.bucket != bucket) revert InvalidState();
        if (basis.phase == 2) basis.putSpot = IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(basis.pool);
        if (basis.phase == 3) _putUnchanged();
        ++basis.phase;
        return nav(bucket);
    }
    function historicalValue(uint256 bucket) public view returns(uint256 value) {
        IPricingBudget budget = IPricingBudget(IPricingVault(access.module(Ids.VAULT)).migrationBudget());
        if (budget.compositionEpoch(bucket) == 0) return 0;
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(access.module(Ids.VAULT)).group(bucket).poolId);
        IPricingAssets admitted = IPricingAssets(access.module(Ids.REWARDS));
        uint256 count = admitted.assetCount(); if (count > 33) revert InvalidState();
        for (uint256 i; i < count; ++i) {
            address token = admitted.assets(i);
            if (token == c.key.currency0 || token == c.key.currency1) continue;
            uint256 amount = IZZZFees(access.module(Ids.FEES)).compoundBalance(bucket,token);
            if (amount != 0) value += basis.phase != 0 && basis.bucket == bucket ? _lower(token,amount) : oracle.value(token,amount);
        }
    }
    function _putUnchanged() private view {
        if (IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(basis.pool) != basis.putSpot) revert Slippage();
    }
    function _unchanged() private view returns(bytes32 hash) {
        if(_protocolPolicy().entryFingerprint()!=basis.entryPolicyFingerprint)revert InvalidState();
        hash = keccak256(abi.encode(basis.pool,basis.nft,basis.lowerInput,basis.upperInput,
            basis.maxIdleBps,basis.entryPolicyFingerprint));
        for (uint256 i; i < assets.length; ++i) {
            address token = assets[i]; Mark memory m = marks[token];
            (uint256 low,uint256 high,bytes32 fingerprint) = oracle.priceBounds(token);
            if (low != m.lower || high != m.upper || fingerprint != m.fingerprint ||
                10 ** oracle.tokenDecimals(token) != m.scale) revert InvalidState();
            hash = keccak256(abi.encode(hash,token,m));
        }
    }
    function finish(uint256 bucket,uint256 inputUSD,uint256 supply,uint256 incumbentNAV,
        uint256 incumbentDeployed,uint256 deployed,uint256 idle,uint32 limits)
        external onlyBudget returns(uint256 issued,uint256 netUSD) {
        if (basis.phase != 4 || basis.bucket != bucket || basis.lowerInput != inputUSD || basis.limits != limits ||
            uint16(limits) > 1000 || uint16(limits >> 16) > 1000) revert InvalidState();
        // Previously zero old-currency compound can first arrive during fee
        // synchronization. Mark it only for incumbent historical backing now;
        // never overwrite a starting mark or count it as newly deployed LP.
        _historicalMarks(bucket);
        _putUnchanged(); bytes32 hash = _unchanged();
        if (deployed == 0 || idle > Math.mulDiv(deployed+idle,basis.maxIdleBps,10000) ||
            deployed+idle <= incumbentNAV || deployed < incumbentDeployed) revert Slippage();
        netUSD = deployed+idle-incumbentNAV;
        uint256 required = basis.upperInput - Math.mulDiv(basis.upperInput,uint16(limits >> 16),10000);
        // Vault caps both balancing and deployment to the entrant's budget;
        // this baseline is the repriced incumbent physical LP only. Existing
        // idle/compound belongs in NAV, never in the marginal deployment test.
        if (netUSD < Math.mulDiv(basis.upperInput,10000-uint16(limits),10000) ||
            netUSD < required || deployed-incumbentDeployed < required) revert Slippage();
        issued = supply == 0 ? netUSD : Math.mulDiv(supply,netUSD,incumbentNAV+historicalValue(bucket));
        if (issued == 0 || supply+issued > 1e36) revert InvalidAmount();
        emit ContributionVerified(basis.nft,bucket,basis.lowerInput,basis.upperInput,
            deployed-incumbentDeployed,netUSD,basis.putSpot,hash);
        if (basis.entry) basis.phase = 5;
        else _clear();
    }
    /// @dev Entry's approval reset and final balance/owner checks happen after
    /// Vault returns. Keep the frozen basis until that complete operation ends.
    function endEntry() external {
        if (msg.sender != _entry()) revert Unauthorized();
        if (!basis.entry || basis.phase != 5) revert InvalidState();
        _putUnchanged(); _unchanged(); _clear();
    }
    function _clear() private {
        for (uint256 i; i < assets.length; ++i) delete marks[assets[i]];
        delete assets; delete basis;
    }
}
