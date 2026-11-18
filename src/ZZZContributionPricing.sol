// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {IZZZAccess, IZZZOracle, IZZZVault, IZZZPools, IZZZLiquidity, IZZZStrategy} from "./interfaces/IZZZ.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {IZZZExecutionOracle, IZZZExecutionStrategy} from "./interfaces/IZZZExecutionOracle.sol";

interface IPricingVault { function migrationBudget() external view returns (address); }
interface IPricingExecutionManager {function executionStrategy()external view returns(address);}
interface IPricingEntry {
    function pricingContext(uint256,bytes32,uint256,uint256) external view returns (bool);
}
interface IPricingBudget {
    function emergencyActive() external view returns(bool);
    function contributionLossBps() external view returns(uint16);
    function lastCompound(uint256) external view returns(uint64);
    function compoundInterval(bytes32) external view returns(uint32);
}
interface IPricingMaintenanceMath {
    function compoundReady(uint256,address)external view returns(bool);
    function validateRebalance(uint256,uint128,bool,uint8)external view;
    function validateResidualClose(uint256,bool)external view;
    function maintenanceValues(uint256,uint256,uint256,uint256,uint256)external view returns(uint256,uint256);
    function checkMaintenance(uint256,uint256,uint256,uint256,uint256,uint256,uint16,uint16,bytes32)external view returns(uint256,uint256,bytes32);
    function assertPortfolioUtilization(uint256,uint256,uint256,uint256,uint256)external view;
}

/// @notice Fixed Oracle-created accounting companion. No funds, approvals, user
/// setter, arbitrary call or sweep. A whole contribution uses one price vector.
contract ZZZContributionPricing {
    uint256 public constant ENTRY_REVIEW_VERSION = 2;
    uint256 public constant RESIDUAL_REINVEST_VERSION = 1;
    uint256 public constant EXECUTION_PRICE_VERSION = 1;
    IZZZAccess public immutable access;
    IZZZOracle public immutable oracle;
    uint256 private maintenanceBucket;
    // Oracle USD18 prices are at most 1e36, below uint128.max. Packing the
    // bounds saves one transient word per marked asset. ABI field order and
    // padded values stay identical, including the final basis fingerprint.
    struct Mark { uint128 lower; uint128 upper; uint256 scale; bytes32 fingerprint; }
    struct MaintenanceMark {
        uint256 value; uint256 price0; uint256 price1; uint256 scale0; uint256 scale1;
        uint256 idle0; uint256 idle1;
        uint16 maxIdleBps;bytes32 maintenancePolicy;
    }
    // One atomic operation shares Oracle's transaction-only execution scope.
    // Individual typed writes preserve visibility at every existing callback.
    bytes32 private constant BASIS_WORDS=keccak256("PoPL.ContributionPricing.basis.v1");
    uint256 private constant B_POOL=0;
    uint256 private constant B_NFT=1;
    uint256 private constant B_BUCKET=2;
    uint256 private constant B_LOWER_INPUT=3;
    uint256 private constant B_UPPER_INPUT=4;
    uint256 private constant B_PUT_SPOT=5;
    uint256 private constant B_PHASE=6;
    uint256 private constant B_ENTRY=7;
    uint256 private constant B_TOKEN0=8;
    uint256 private constant B_TOKEN1=9;
    uint256 private constant B_LIMITS=10;
    uint256 private constant B_MAX_IDLE_BPS=11;
    uint256 private constant B_ENTRY_POLICY_FINGERPRINT=12;
    // Exact captured marks are transaction-scoped, just like Oracle execution.
    // Every operation still explicitly clears them, including within one tx.
    bytes32 private constant MARK_DOMAIN = keccak256("PoPL.ContributionPricing.mark.v1");
    bytes32 private constant ASSET_LIST = keccak256("PoPL.ContributionPricing.assets.v1");
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
    function active() external view returns(bool) { return uint8(_basisWord(B_PHASE)) != 0; }
    /// @notice Read-only timing extraction. Budget still authenticates Vault
    /// and any active emergency; no caller receives execution authority here.
    function validateRebalance(uint256 bucket,uint128 minimumLiquidity,bool emergency,uint8 checks)
        external view onlyBudget {
        IPricingMaintenanceMath(address(_executionStrategy())).validateRebalance(bucket,minimumLiquidity,emergency,checks);
    }
    /// @notice Read-only raw-close checks, with Budget's local busy state.
    /// All dependency reads are public; caller-specific authority stays Budget.
    function validateResidualClose(uint256 bucket,bool busy) external view onlyBudget {
        IPricingMaintenanceMath(address(_executionStrategy())).validateResidualClose(bucket,busy);
    }
    function _protocolPolicy() private view returns(IZZZProtocolPolicy){return IZZZProtocolPolicy(access.protocolPolicy());}
    /// @notice The fixed Budget may only use the contribution cap captured
    /// before external input movement, never a guessed current/default value.
    function entryIdleLimit(uint256 bucket) external view onlyBudget returns(uint16){
        if(uint8(_basisWord(B_PHASE))==0 || uint8(_basisWord(B_PHASE))>4 || _basisWord(B_BUCKET)!=bucket)revert InvalidState();
        return uint16(_basisWord(B_MAX_IDLE_BPS));
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
        return IPricingMaintenanceMath(address(_executionStrategy())).checkMaintenance(bucket,beforeValue,
            price0,price1,scale0,scale1,lossBps,maxIdleBps,expectedMaintenancePolicy);
    }
    function compoundReady(uint256 bucket) external view onlyBudget returns(bool) {
        return IPricingMaintenanceMath(address(_executionStrategy())).compoundReady(bucket,msg.sender);
    }
    /// @notice Stateless exact valuation for the fixed Budget's captured vector.
    /// This shares accounting math; it creates no new authority or price fallback.
    function markMaintenance(uint256 bucket) external onlyBudget returns(MaintenanceMark memory mark) {
        IZZZProtocolPolicy policy=_protocolPolicy();
        IZZZProtocolPolicy.MaintenancePolicy memory limits=policy.maintenancePolicy();
        mark.maxIdleBps=limits.maxIdleBps;
        mark.maintenancePolicy=keccak256(abi.encode(address(policy),limits));
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(bucket);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if(!IPricingBudget(msg.sender).emergencyActive()) {
            _beginMaintenanceExecution(bucket,c.key.currency1);
        }
        (mark.price0,,)=IZZZExecutionOracle(address(oracle)).executionBounds(c.key.currency0);
        (mark.price1,,)=IZZZExecutionOracle(address(oracle)).executionBounds(c.key.currency1);
        mark.scale0 = 10 ** oracle.tokenDecimals(c.key.currency0); mark.scale1 = 10 ** oracle.tokenDecimals(c.key.currency1);
        mark.idle0 = p.idle0; mark.idle1 = p.idle1;
        (uint256 deployed,uint256 idle) = IPricingMaintenanceMath(address(_executionStrategy())).maintenanceValues(bucket,
            mark.price0,mark.price1,mark.scale0,mark.scale1);
        mark.value = deployed+idle;
    }
    /// @notice Complete the normal maintenance scope only after every custody,
    /// portfolio and loss proof. Explicit emergency masks keep their own path.
    function endMaintenance(uint256 bucket) external onlyBudget {
        if(IPricingBudget(msg.sender).emergencyActive())return;
        _endMaintenanceExecution(bucket);
    }
    /// @notice Fixed Budget opens before any priced manual movement and closes
    /// after Vault settlement/final manifest, before disarming its context.
    /// Budget validates its active context immediately before either call.
    /// Only that sealed, nonreentrant caller can reach this entry; intervening
    /// source/configuration reads are STATIC, so no duplicate status read is needed.
    function emergencyExecution(uint256 bucket,bool opening) external onlyBudget {
        if(opening) {
            Position memory p=IZZZVault(access.module(Ids.VAULT)).group(bucket);
            _beginMaintenanceExecution(bucket,IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId).key.currency1);
        } else _endMaintenanceExecution(bucket);
    }
    function _beginMaintenanceExecution(uint256 bucket,address zzz) private {
        if(bucket==0 || maintenanceBucket!=0 || uint8(_basisWord(B_PHASE))!=0)revert InvalidState();
        maintenanceBucket=bucket;
        IZZZExecutionOracle(address(oracle)).beginExecution(zzz);
    }
    function _endMaintenanceExecution(uint256 bucket) private {
        if(maintenanceBucket!=bucket || bucket==0)revert InvalidState();
        IZZZExecutionOracle(address(oracle)).endExecution();
        delete maintenanceBucket;
    }
    /// @notice Post-replacement utilization uses actual physical principal and
    /// the Budget's starting USD vector. The main floor, residual ceiling and
    /// idle ceiling are independent of the operation's execution-loss budget.
    function assertPortfolioUtilization(uint256 bucket,uint256 price0,uint256 price1,uint256 scale0,uint256 scale1)
        external view onlyBudget {
        IPricingMaintenanceMath(address(_executionStrategy())).assertPortfolioUtilization(bucket,price0,price1,scale0,scale1);
    }

    /// @dev Only the typed fixed-operation writes below address these13words.
    function _basisWord(uint256 index) private view returns(uint256 value) {
        bytes32 base=BASIS_WORDS;
        assembly("memory-safe") {value:=tload(add(base,index))}
    }
    function _basisSet(uint256 index,uint256 value) private {
        bytes32 base=BASIS_WORDS;
        assembly("memory-safe") {tstore(add(base,index),value)}
    }
    function _clearBasis() private {
        bytes32 base=BASIS_WORDS;
        assembly("memory-safe") {
            for{let i:=0}lt(i,13){i:=add(i,1)}{tstore(add(base,i),0)}
        }
    }
    /// @dev Domain-separated slots; only bounded typed _mark can create records.
    function _markSlot(address token) private pure returns(bytes32 slot) {
        bytes32 domain=MARK_DOMAIN;
        assembly ("memory-safe") {
            mstore(0,and(token,0xffffffffffffffffffffffffffffffffffffffff))
            mstore(32,domain)
            slot:=keccak256(0,64)
        }
    }
    function _readMark(address token) private view returns(Mark memory m) {
        bytes32 slot=_markSlot(token);
        assembly ("memory-safe") {
            let value:=tload(slot)
            mstore(m,and(value,0xffffffffffffffffffffffffffffffff))
            mstore(add(m,32),shr(128,value))
            mstore(add(m,64),tload(add(slot,1)))
            mstore(add(m,96),tload(add(slot,2)))
        }
    }
    function _writeMark(address token,Mark memory m) private {
        bytes32 slot=_markSlot(token);
        assembly ("memory-safe") {
            tstore(slot,or(and(mload(m),0xffffffffffffffffffffffffffffffff),shl(128,mload(add(m,32)))))
            tstore(add(slot,1),mload(add(m,64)))
            tstore(add(slot,2),mload(add(m,96)))
        }
    }
    function _assetCount() private view returns(uint256 count) {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") { count:=tload(slot) }
    }
    function _assetAt(uint256 index) private view returns(address token) {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") { token:=and(tload(add(add(slot,1),index)),0xffffffffffffffffffffffffffffffffffffffff) }
    }
    function _appendAsset(address token) private {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") {
            let count:=tload(slot)
            tstore(add(add(slot,1),count),and(token,0xffffffffffffffffffffffffffffffffffffffff))
            tstore(slot,add(count,1))
        }
    }
    function _clearAssets() private {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") {
            let count:=tload(slot)
            for {let i:=0} lt(i,count) {i:=add(i,1)} {tstore(add(add(slot,1),i),0)}
            tstore(slot,0)
        }
    }

    function _mark(address token) private {
        if (_readMark(token).lower != 0) return;
        if (_assetCount() == 34) revert InvalidState();
        (uint256 lower,uint256 upper,bytes32 fingerprint) = IZZZExecutionOracle(address(oracle)).executionBounds(token);
        if (lower == 0 || upper < lower || upper > type(uint128).max) revert InvalidState();
        _writeMark(token,Mark(uint128(lower),uint128(upper),10 ** oracle.tokenDecimals(token),fingerprint));
        _appendAsset(token);
    }
    function _pair(bytes32 pool) private {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(pool);
        _basisSet(B_POOL,uint256(pool)); _basisSet(B_TOKEN0,uint256(uint160(c.key.currency0))); _basisSet(B_TOKEN1,uint256(uint160(c.key.currency1)));
        if(maintenanceBucket!=0)revert InvalidState();
        IZZZExecutionOracle(address(oracle)).beginExecution(c.key.currency1);
        IZZZProtocolPolicy policy=_protocolPolicy();
        IZZZProtocolPolicy.EntryPolicy memory entry=policy.entryPolicy();
        _basisSet(B_MAX_IDLE_BPS,uint256(entry.maxIdleBps));
        _basisSet(B_ENTRY_POLICY_FINGERPRINT,uint256(keccak256(abi.encode(address(policy),entry))));
        // Entry freezes operating limits before the original-source transfer
        // and conversion, not only when it eventually enters the Vault.
        uint16 cap = IPricingBudget(IPricingVault(access.module(Ids.VAULT)).migrationBudget()).contributionLossBps();
        if (cap > 1000 || c.maxSlippageBps > 1000) revert InvalidState();
        _basisSet(B_LIMITS,uint256(uint32(c.maxSlippageBps) | (uint32(cap) << 16)));
        _mark(c.key.currency0); _mark(c.key.currency1);
    }
    /// @dev Entry calls BEFORE token pulls, approvals or conversion. No later
    /// quote can replace this original-source value or LP-pair price basis.
    /// @notice Freeze the reviewed Entry basis and enforce the caller's maximum loss.
    function beginEntryReviewed(uint256 nft,bytes32 pool,address source,uint256 amount,uint16 maximumLossBps,
        bytes32 expectedContributionPolicy)
        external returns(uint256 lowerUSD) {
        if (msg.sender != _entry()) revert Unauthorized();
        _live(); if (uint8(_basisWord(B_PHASE)) != 0 || amount == 0) revert InvalidState();
        if (maximumLossBps > 1000) revert InvalidAmount();
        _basisSet(B_PHASE,uint256(1)); _basisSet(B_ENTRY,(true?1:0)); _basisSet(B_NFT,uint256(nft));
        _pair(pool);
        if(expectedContributionPolicy==bytes32(0) || bytes32(_basisWord(B_ENTRY_POLICY_FINGERPRINT))!=expectedContributionPolicy)revert InvalidState();
        if (uint16(uint32(_basisWord(B_LIMITS)) >> 16) > maximumLossBps) revert Slippage();
        _mark(source);
        Mark memory m = _readMark(source);
        lowerUSD = Math.mulDiv(amount,m.lower,m.scale);
        _basisSet(B_LOWER_INPUT,uint256(lowerUSD));
        _basisSet(B_UPPER_INPUT,uint256(Math.mulDiv(amount,m.upper,m.scale,Math.Rounding.Ceil)));
    }
    /// @dev Existing Vault ABI carries both bounded raw amounts in one word:
    /// low128=amount0, high128=amount1. This is not a supplied USD claim.
    function begin(uint256 nft,uint256 bucket,uint256 packed,uint256 inputUSD,uint32 limits) external onlyBudget {
        _live();
        bytes32 pool = IZZZVault(access.module(Ids.VAULT)).group(bucket).poolId;
        if (uint8(_basisWord(B_PHASE)) != 0) {
            if (!(_basisWord(B_ENTRY)!=0) || uint8(_basisWord(B_PHASE)) != 1 || bytes32(_basisWord(B_POOL)) != pool || _basisWord(B_NFT) != nft ||
                _basisWord(B_LOWER_INPUT) != inputUSD || !IPricingEntry(_entry()).pricingContext(nft,pool,packed,inputUSD)) revert InvalidState();
        } else {
            _basisSet(B_PHASE,uint256(1)); _basisSet(B_NFT,uint256(nft)); _pair(pool);
            uint256 a0 = uint128(packed); uint256 a1 = packed >> 128;
            _basisSet(B_LOWER_INPUT,uint256(_pairValue(a0,a1)));
            _basisSet(B_UPPER_INPUT,uint256(_upper(address(uint160(_basisWord(B_TOKEN0))),a0) + _upper(address(uint160(_basisWord(B_TOKEN1))),a1)));
            if (inputUSD != _basisWord(B_LOWER_INPUT)) revert InvalidAmount();
        }
        // A callback cannot adopt a later, wider governance/venue policy.
        // Even a tightening during this operation requires a fresh review.
        if (uint32(_basisWord(B_LIMITS)) != limits) revert InvalidState();
        _basisSet(B_BUCKET,uint256(bucket));
        // Conversion/pull callbacks may not replace policies or round data.
        _unchanged(true);
    }
    function _lower(address token,uint256 amount) private view returns(uint256) {
        if (amount == 0) return 0;
        if (uint8(_basisWord(B_PHASE)) == 0) return oracle.value(token,amount);
        Mark memory m = _readMark(token);
        if (m.lower == 0) revert InvalidState();
        return Math.mulDiv(amount,m.lower,m.scale);
    }
    function _upper(address token,uint256 amount) private view returns(uint256) {
        if (amount == 0) return 0;
        Mark memory m = _readMark(token);
        if (m.upper == 0) revert InvalidState();
        return Math.mulDiv(amount,m.upper,m.scale,Math.Rounding.Ceil);
    }
    function _pairValue(uint256 amount0,uint256 amount1) private view returns(uint256) {
        return _lower(address(uint160(_basisWord(B_TOKEN0))),amount0) + _lower(address(uint160(_basisWord(B_TOKEN1))),amount1);
    }
    function valueBucket(uint256 bucket,uint256 amount0,uint256 amount1) public view returns(uint256) {
        if (uint8(_basisWord(B_PHASE)) != 0 && _basisWord(B_BUCKET) == bucket) return _pairValue(amount0,amount1);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(access.module(Ids.VAULT)).group(bucket).poolId);
        if(maintenanceBucket==bucket && bucket!=0)return _executionValue(c.key.currency0,amount0)+_executionValue(c.key.currency1,amount1);
        return oracle.value(c.key.currency0,amount0) + oracle.value(c.key.currency1,amount1);
    }
    function _executionValue(address token,uint256 amount) private view returns(uint256) {
        (uint256 lower,,)=IZZZExecutionOracle(address(oracle)).executionBounds(token);
        return Math.mulDiv(amount,lower,10**oracle.tokenDecimals(token));
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
        if(uint8(_basisWord(B_PHASE))!=0 && _basisWord(B_BUCKET)==bucket)return _pairValue(p.idle0,p.idle1);
        if(maintenanceBucket==bucket && bucket!=0)return _executionValue(c.key.currency0,p.idle0)+_executionValue(c.key.currency1,p.idle1);
        return oracle.value(c.key.currency0,p.idle0)+oracle.value(c.key.currency1,p.idle1);
    }
    /// @dev The Vault already performs these three marks in fixed order: before
    /// its deliberate balancing swap, before _put, and after every _put callback.
    function contributionNav(uint256 bucket) external onlyBudget returns(uint256 deployed,uint256 idle) {
        if (uint8(_basisWord(B_PHASE)) == 0 || uint8(_basisWord(B_PHASE)) > 3 || _basisWord(B_BUCKET) != bucket) revert InvalidState();
        IZZZExecutionOracle(address(oracle)).validateExecution();
        if (uint8(_basisWord(B_PHASE)) == 2) _basisSet(B_PUT_SPOT,uint256(_executionStrategy().executionValidatePrice(bytes32(_basisWord(B_POOL)))));
        if (uint8(_basisWord(B_PHASE)) == 3) _putUnchanged();
        _basisSet(B_PHASE,uint256(uint8(_basisWord(B_PHASE))+1));
        return nav(bucket);
    }
    /// @notice Compatibility read: fresh principal and LP reserves use only
    /// native ETH/fixed ZZZ, so there is no foreign-currency compound add-on.
    /// Current pair compound is already included by its actual release/mark.
    function historicalValue(uint256 bucket) public view returns(uint256 value) {
        return 0;
    }
    function _putUnchanged() private view {
        if (_executionStrategy().executionValidatePrice(bytes32(_basisWord(B_POOL))) != uint160(_basisWord(B_PUT_SPOT))) revert Slippage();
    }
    function _executionStrategy()private view returns(IZZZExecutionStrategy){
        return IZZZExecutionStrategy(IPricingExecutionManager(access.module(Ids.LIQUIDITY)).executionStrategy());
    }
    function _unchanged(bool checkSources) private view returns(bytes32 hash) {
        if(checkSources)IZZZExecutionOracle(address(oracle)).validateExecution();
        if(_protocolPolicy().entryFingerprint()!=bytes32(_basisWord(B_ENTRY_POLICY_FINGERPRINT)))revert InvalidState();
        hash = keccak256(abi.encode(bytes32(_basisWord(B_POOL)),_basisWord(B_NFT),_basisWord(B_LOWER_INPUT),_basisWord(B_UPPER_INPUT),
            uint16(_basisWord(B_MAX_IDLE_BPS)),bytes32(_basisWord(B_ENTRY_POLICY_FINGERPRINT))));
        for (uint256 i; i < _assetCount(); ++i) {
            address token = _assetAt(i); Mark memory m = _readMark(token);
            (uint256 low,uint256 high,bytes32 fingerprint) = IZZZExecutionOracle(address(oracle)).executionBounds(token);
            if (low != m.lower || high != m.upper || fingerprint != m.fingerprint ||
                10 ** oracle.tokenDecimals(token) != m.scale) revert InvalidState();
            hash = keccak256(abi.encode(hash,token,m));
        }
    }
    function finish(uint256 bucket,uint256 inputUSD,uint256 supply,uint256 incumbentNAV,
        uint256 incumbentDeployed,uint256 deployed,uint256 idle,uint32 limits)
        external onlyBudget returns(uint256 issued,uint256 netUSD) {
        if (uint8(_basisWord(B_PHASE)) != 4 || _basisWord(B_BUCKET) != bucket || _basisWord(B_LOWER_INPUT) != inputUSD || uint32(_basisWord(B_LIMITS)) != limits ||
            uint16(limits) > 1000 || uint16(limits >> 16) > 1000) revert InvalidState();
        // Phase-three NAV has just completed the full source proof. Only
        // STATIC reads and local Vault/Budget arithmetic precede this fixed
        // phase-four call; retain every captured mark and policy comparison.
        _putUnchanged(); bytes32 hash = _unchanged(false);
        if (deployed == 0 || idle > Math.mulDiv(deployed+idle,uint16(_basisWord(B_MAX_IDLE_BPS)),10000) ||
            deployed+idle <= incumbentNAV || deployed < incumbentDeployed) revert Slippage();
        netUSD = deployed+idle-incumbentNAV;
        uint256 required = _basisWord(B_UPPER_INPUT) - Math.mulDiv(_basisWord(B_UPPER_INPUT),uint16(limits >> 16),10000);
        // Vault caps both balancing and deployment to the entrant's budget;
        // this baseline is the repriced incumbent physical LP only. Existing
        // idle/compound belongs in NAV, never in the marginal deployment test.
        if (netUSD < Math.mulDiv(_basisWord(B_UPPER_INPUT),10000-uint16(limits),10000) ||
            netUSD < required || deployed-incumbentDeployed < required) revert Slippage();
        issued = supply == 0 ? netUSD : Math.mulDiv(supply,netUSD,incumbentNAV);
        if (issued == 0 || supply+issued > 1e36) revert InvalidAmount();
        emit ContributionVerified(_basisWord(B_NFT),bucket,_basisWord(B_LOWER_INPUT),_basisWord(B_UPPER_INPUT),
            deployed-incumbentDeployed,netUSD,uint160(_basisWord(B_PUT_SPOT)),hash);
        if ((_basisWord(B_ENTRY)!=0)) _basisSet(B_PHASE,uint256(5));
        else _clear();
    }
    /// @dev Entry's approval reset and final balance/owner checks happen after
    /// Vault returns. Keep the frozen basis until that complete operation ends.
    function endEntry() external {
        if (msg.sender != _entry()) revert Unauthorized();
        if (!(_basisWord(B_ENTRY)!=0) || uint8(_basisWord(B_PHASE)) != 5) revert InvalidState();
        // _clear starts with Oracle.endExecution's full final proof. Only
        // STATIC mark/policy reads separate it from these exact-basis checks.
        _putUnchanged(); _unchanged(false); _clear();
    }
    function _clear() private {
        IZZZExecutionOracle(address(oracle)).endExecution();
        for (uint256 i; i < _assetCount(); ++i) _writeMark(_assetAt(i),Mark(0,0,0,bytes32(0)));
        _clearAssets(); _clearBasis();
    }
}
