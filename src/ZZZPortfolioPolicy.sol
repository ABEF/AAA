// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "./libraries/ZZZTypes.sol";
import {IZZZPools, IZZZVault, IZZZLiquidity, IPositionManagerMinimal} from "./interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";

interface IPortfolioAssociation {
    function secondaryId(uint256 main) external view returns(uint256);
}
interface IPortfolioParent { function portfolioPolicy() external view returns(address); }

/// @notice Fixed, noncustodial policy for one main and at most one residual LP.
/// Desired mode never moves assets. Only an atomic guarded adjustment applies it.
contract ZZZPortfolioPolicy is ZZZModule {
    uint256 public constant PORTFOLIO_VERSION = 2;
    uint16 public constant HARD_MINIMUM_MAIN_BPS = 6000;
    uint16 public constant HARD_MAXIMUM_RESIDUAL_BPS = 4000;
    uint16 public constant DEFAULT_RESIDUAL_SIDE_BPS = 5000;
    uint16 public thresholdBps = 8500;
    uint64 public revision;
    uint64 public triggerRevision;
    mapping(bytes32 => uint64) public controlRevision;
    mapping(bytes32 => bool) public enabled;
    mapping(bytes32 => uint64) public geometryRevision;
    /// @dev Zero storage selects the explicitly approved half-side default.
    mapping(bytes32 => uint16) private configuredResidualSideBps;
    mapping(bytes32 => uint16) private configuredMinimumMainBps;
    mapping(bytes32 => uint24) private configuredResidualGap;
    mapping(bytes32 => bytes32) public residualReviewHash;
    mapping(uint256 => uint64) public appliedRevision;
    mapping(bytes32 => bytes32) public modeReviewHash;
    bytes32 public triggerReviewHash;
    uint256 private constant UNIT = 1e18;

    event PortfolioModeConfigured(bytes32 indexed pool,bool enabled,uint64 geometryRevision,uint64 revision,bytes32 indexed reviewHash);
    event PortfolioTriggerConfigured(uint16 previous,uint16 current,uint64 revision,bytes32 indexed reviewHash);
    event ResidualSideConfigured(bytes32 indexed pool,uint16 previous,uint16 current,uint64 geometryRevision,uint64 revision,bytes32 indexed reviewHash);
    event PortfolioApplied(uint256 indexed main,bytes32 indexed pool,uint64 geometryRevision);
    event MainAllocationConfigured(bytes32 indexed pool,uint16 minimumMainBps,uint64 geometryRevision,bytes32 indexed reviewHash);
    event ResidualGapConfigured(bytes32 indexed pool,uint24 spacings,uint64 geometryRevision,bytes32 indexed reviewHash);

    constructor(address controller) ZZZModule(controller) {}
    /// @notice The sealed controller fixes the sole Strategy parent. Standalone
    /// creation avoids embedding helper initcode; there is no parent setter.
    function strategy() public view returns(address) { return access.module(Ids.STRATEGY); }

    function setMode(bytes32 pool,bool next,bytes32 reviewed)
        external onlyGovernance operating principalOperating {
        if(reviewed == bytes32(0) || enabled[pool] == next) revert InvalidConfiguration();
        // Disabling an already enabled mode records a desired safe merge; it
        // must not depend on a currently failing external venue binding.
        if(next) _pool(pool);
        enabled[pool] = next;
        modeReviewHash[pool] = reviewed;
        ++geometryRevision[pool];
        ++controlRevision[pool];
        ++revision;
        emit PortfolioModeConfigured(pool,next,geometryRevision[pool],revision,reviewed);
    }

    function configureResidualSide(bytes32 pool,uint16 next,bytes32 reviewed)
        external onlyGovernance operating principalOperating {
        if(next == 0 || next > 10000 || reviewed == bytes32(0)) revert InvalidConfiguration();
        _pool(pool);
        uint16 previous = residualSideBps(pool);
        configuredResidualSideBps[pool] = next;
        residualReviewHash[pool] = reviewed;
        // An unused residual setting cannot force a single-position trade.
        // Relevant samples/reviews use this pool's control revision; unrelated
        // pools and cosmetic/read-only policies cannot reset its evidence.
        if(enabled[pool]) ++geometryRevision[pool];
        ++controlRevision[pool];
        ++revision;
        emit ResidualSideConfigured(pool,previous,next,geometryRevision[pool],revision,reviewed);
    }
    /// @notice 10000 uses the full corresponding main side; 5000 uses half that
    /// side's ZZZ-in-ETH price distance. Mode remains disabled by default.
    function residualSideBps(bytes32 pool) public view returns(uint16 configured) {
        configured = configuredResidualSideBps[pool];
        if(configured == 0) configured = DEFAULT_RESIDUAL_SIDE_BPS;
    }
    function minimumMainBps(bytes32 pool) public view returns(uint16 configured) {
        configured=configuredMinimumMainBps[pool];
        if(configured==0)configured=HARD_MINIMUM_MAIN_BPS;
    }
    function maximumResidualBps(bytes32 pool) external view returns(uint16){return 10000-minimumMainBps(pool);}
    function residualGapSpacings(bytes32 pool) public view returns(uint24 configured){
        configured=configuredResidualGap[pool];if(configured==0)configured=1;
    }
    /// @notice Raise the qualifying main allocation within the approved60/40
    /// envelope.100% is expressed by single mode, not an impossible zero-dust
    /// hybrid promise. Very strict floors can be unavailable until loosened.
    function configureMainAllocation(bytes32 pool,uint16 next,bytes32 reviewed)
        external onlyGovernance operating principalOperating {
        if(next<HARD_MINIMUM_MAIN_BPS || next>=10000 || reviewed==bytes32(0))revert InvalidConfiguration();
        _pool(pool);configuredMinimumMainBps[pool]=next;
        if(enabled[pool])++geometryRevision[pool];++controlRevision[pool];++revision;
        emit MainAllocationConfigured(pool,next,geometryRevision[pool],reviewed);
    }
    /// @notice The bound derives from the complete TickMath domain. Actual
    /// main-side width may be smaller and must still be feasible at execution.
    function configureResidualGap(bytes32 pool,uint24 next,bytes32 reviewed)
        external onlyGovernance operating principalOperating {
        PoolConfig memory c=_pool(pool);
        if(next==0 || reviewed==bytes32(0) || uint256(next)*uint256(uint24(c.key.tickSpacing))>=
            uint256(int256(TickMath.MAX_TICK)-int256(TickMath.MIN_TICK)))revert InvalidConfiguration();
        configuredResidualGap[pool]=next;
        if(enabled[pool])++geometryRevision[pool];++controlRevision[pool];++revision;
        emit ResidualGapConfigured(pool,next,geometryRevision[pool],reviewed);
    }

    /// @notice Percentage of actual centre-to-boundary PRICE distance, not ticks,
    /// square-root distance or percentage change from the centre itself.
    function setTriggerBps(uint16 next,bytes32 reviewed)
        external onlyGovernance operating principalOperating {
        if(next == 0 || next > 10000 || reviewed == bytes32(0)) revert InvalidConfiguration();
        uint16 previous = thresholdBps;
        thresholdBps = next;
        triggerReviewHash = reviewed;
        ++triggerRevision;
        ++revision;
        emit PortfolioTriggerConfigured(previous,next,revision,reviewed);
    }

    /// @notice Records only an actually minted, Vault-owned portfolio. The
    /// current fixed Manager is the sole writer; governance cannot mark a mode
    /// applied without the physical operation that the Manager authenticates.
    function recordApplied(uint256 main,bytes32 pool) external operating principalOperating {
        address manager = access.module(Ids.LIQUIDITY);
        if(!access.isSealed() || msg.sender != manager || manager == address(0) || main == 0 ||
            IPortfolioParent(strategy()).portfolioPolicy() != address(this)) revert Unauthorized();
        _pool(pool);
        IPositionManagerMinimal posm = IPositionManagerMinimal(IZZZLiquidity(manager).positionManager());
        _position(posm,main,pool);
        uint256 secondary = IPortfolioAssociation(manager).secondaryId(main);
        if(secondary != 0) {
            if(!enabled[pool] || secondary == main) revert InvalidState();
            _position(posm,secondary,pool);
        }
        appliedRevision[main] = geometryRevision[pool];
        emit PortfolioApplied(main,pool,geometryRevision[pool]);
    }

    function _position(IPositionManagerMinimal posm,uint256 id,bytes32 pool) private view {
        (PoolKey memory key,uint256 info) = posm.getPoolAndPositionInfo(id);
        int24 lower = int24(uint24(info >> 8));
        int24 upper = int24(uint24(info >> 32));
        if(posm.ownerOf(id) != access.module(Ids.VAULT) || keccak256(abi.encode(key)) != pool ||
            posm.getPositionLiquidity(id) == 0 || lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper)
            revert InvalidState();
    }

    /// @notice Explicit mode changes are pending independently of market price.
    /// Trigger-only changes invalidate evidence but do not create this exception.
    function configurationPending(uint256 bucket) external view returns(bool) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        return p.status == PositionStatus.Active && p.lpTokenId != 0 &&
            appliedRevision[p.lpTokenId] != geometryRevision[p.poolId];
    }

    function controlFingerprint(bytes32 pool) external view returns(bytes32) {
        return keccak256(abi.encode(address(this),strategy(),controlRevision[pool],triggerRevision,pool,enabled[pool],thresholdBps,
            geometryRevision[pool],residualSideBps(pool),minimumMainBps(pool),residualGapSpacings(pool),
            modeReviewHash[pool],residualReviewHash[pool],triggerReviewHash,
            IZZZProtocolPolicy(access.protocolPolicy()).maintenanceFingerprint()));
    }

    function _pool(bytes32 pool) private view returns(PoolConfig memory c) {
        c = IZZZPools(access.module(Ids.POOLS)).accounting(pool);
        if(pool == bytes32(0) || keccak256(abi.encode(c.key)) != pool || c.key.currency0 != address(0) ||
            c.key.currency1 == address(0) || c.key.hooks != address(0) || c.key.tickSpacing<=0) revert InvalidConfiguration();
    }

    /// @notice Raw side1=below sqrt range centre, side2=above. Interpolation is
    /// ALWAYS in ZZZ-in-ETH price (inverse pool price), using actual rounded bounds.
    /// Inward rounding is forbidden: floor the observed upper move and ceil its
    /// threshold; ceil the observed lower move and floor its threshold.
    function thresholdSide(uint160 center,int24 lower,int24 upper,uint160 price) external view returns(uint8) {
        if(lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper ||
            price < TickMath.MIN_SQRT_PRICE || price >= TickMath.MAX_SQRT_PRICE) revert InvalidState();
        uint160 a = TickMath.getSqrtPriceAtTick(lower);
        uint160 b = TickMath.getSqrtPriceAtTick(upper);
        if(center <= a || center >= b) revert InvalidState();
        if(price <= a) return 1;
        if(price >= b) return 2;
        if(price == center) return 0;
        if(price < center) {
            uint256 observedRise = _ratio(center,price,false);
            uint256 boundaryRise = _ratio(center,a,true);
            uint256 thresholdRise = UNIT + Math.mulDiv(boundaryRise-UNIT,thresholdBps,10000,Math.Rounding.Ceil);
            return observedRise >= thresholdRise ? 1 : 0;
        }
        uint256 observed = _ratio(center,price,true);
        uint256 boundary = _ratio(center,b,false);
        uint256 threshold = UNIT-Math.mulDiv(UNIT-boundary,thresholdBps,10000,Math.Rounding.Ceil);
        return observed <= threshold ? 2 : 0;
    }

    function _ratio(uint160 numerator,uint160 denominator,bool roundUp) private pure returns(uint256) {
        return _ratioScale(numerator,denominator,roundUp,UNIT);
    }
    function _ratioScale(uint160 numerator,uint160 denominator,bool roundUp,uint256 unit) private pure returns(uint256) {
        Math.Rounding rounding = roundUp ? Math.Rounding.Ceil : Math.Rounding.Floor;
        uint256 root = Math.mulDiv(numerator,unit,denominator,rounding);
        return Math.mulDiv(root,root,unit,rounding);
    }

    /// @notice A passive range within the corresponding side of the new main.
    /// The nearest edge leaves at least one full spacing beyond spot. The outer
    /// edge uses the configured fraction of spot-to-main-bound PRICE distance,
    /// rounded inward. Insufficient representable width fails closed.
    function residualRange(bytes32 pool,uint160 current,int24 mainLower,int24 mainUpper,bool residual0)
        external view returns(int24 lower,int24 upper) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(pool);
        uint16 fraction = residualSideBps(pool);
        int24 spacing = c.key.tickSpacing;
        if(!enabled[pool] || fraction == 0 || spacing <= 0 || mainLower < TickMath.MIN_TICK ||
            mainUpper > TickMath.MAX_TICK || mainLower >= mainUpper || mainLower % spacing != 0 || mainUpper % spacing != 0)
            revert InvalidConfiguration();
        uint160 a = TickMath.getSqrtPriceAtTick(mainLower);
        uint160 b = TickMath.getSqrtPriceAtTick(mainUpper);
        if(current <= a || current >= b) revert InvalidState();
        int24 tick = TickMath.getTickAtSqrtPrice(current);
        int256 aligned = _floor(tick,spacing);
        int256 gap=int256(uint256(residualGapSpacings(pool)))*spacing;
        if(residual0) {
            int256 near = aligned + spacing + gap;
            if(near >= mainUpper) revert InvalidState();
            lower = int24(near);
            upper = mainUpper;
            if(fraction != 10000) {
                uint256 boundary = _ratioScale(current,b,true,1e36);
                uint256 ratio = 1e36-Math.mulDiv(1e36-boundary,fraction,10000);
                uint256 root = Math.sqrt(ratio,Math.Rounding.Ceil);
                uint160 outer = uint160(Math.mulDiv(current,1e18,root));
                upper = _floor(TickMath.getTickAtSqrtPrice(outer),spacing);
            }
        } else {
            int256 near = aligned - gap;
            if(near <= mainLower) revert InvalidState();
            upper = int24(near);
            lower = mainLower;
            if(fraction != 10000) {
                uint256 boundary = _ratioScale(current,a,false,1e36);
                uint256 ratio = 1e36+Math.mulDiv(boundary-1e36,fraction,10000);
                uint256 root = Math.sqrt(ratio);
                uint160 outer = uint160(Math.mulDiv(current,1e18,root,Math.Rounding.Ceil));
                int256 inward = int256(_floor(TickMath.getTickAtSqrtPrice(outer),spacing))+spacing;
                if(inward > TickMath.MAX_TICK) revert InvalidState();
                lower = int24(inward);
            }
        }
        if(lower < mainLower || upper > mainUpper || lower >= upper) revert InvalidState();
    }
    function _floor(int24 tick,int24 spacing) private pure returns(int24) {
        int24 quotient = tick/spacing;
        if(tick < 0 && tick % spacing != 0) --quotient;
        return quotient*spacing;
    }
    /// @notice One exact range implementation shared by Strategy target and
    /// recorded-centre comparisons. This pure helper grants no trading rights.
    function range(PoolConfig memory c,uint160 referenceX96,uint8 orientation)
        external pure returns(int24 lower,int24 upper) {
        if(orientation > 1 || c.rangeBps >= 10000 || c.key.tickSpacing <= 0) revert InvalidConfiguration();
        uint256 below = Math.sqrt(uint256(10000-c.rangeBps)*1e28);
        uint256 above = Math.sqrt(uint256(10000+c.rangeBps)*1e28);
        uint256 lowerRoot = orientation == 1 ? Math.mulDiv(referenceX96,1e16,
            Math.sqrt(uint256(10000+c.rangeBps)*1e28,Math.Rounding.Ceil)) : Math.mulDiv(referenceX96,below,1e16);
        uint256 upperRoot = orientation == 1 ? Math.mulDiv(referenceX96,1e16,below,Math.Rounding.Ceil) :
            Math.mulDiv(referenceX96,above,1e16);
        if(lowerRoot <= TickMath.MIN_SQRT_PRICE || upperRoot >= TickMath.MAX_SQRT_PRICE) revert InvalidConfiguration();
        lower = _floor(TickMath.getTickAtSqrtPrice(uint160(lowerRoot)),c.key.tickSpacing);
        upper = _floor(TickMath.getTickAtSqrtPrice(uint160(upperRoot)),c.key.tickSpacing)+c.key.tickSpacing;
        if(lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper) revert InvalidConfiguration();
    }
}
