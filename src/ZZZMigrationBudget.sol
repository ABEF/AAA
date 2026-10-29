// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZContributionPricing} from "./ZZZContributionPricing.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZOracle, IZZZLiquidity, IZZZStrategy, IPositionManagerMinimal} from "./interfaces/IZZZ.sol";
interface IPairAssets { function assetCount() external view returns(uint256); function assets(uint256) external view returns(address); }
interface IPairVault { function migrationBudget() external view returns(ZZZMigrationBudget); }
interface IConfirmationControl {
    function controlFingerprint(bytes32) external view returns(bytes32);
    function observationFingerprint(uint256,bytes32) external view returns(bytes32);
    function observations(uint256) external view returns(bytes32,uint64,uint64,uint8);
    function emergencyReady(uint256) external view returns(bool);
}
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
interface IEmergencyManifest {
    function emergencyFingerprint() external view returns(bytes32);
    function emergencyTarget() external view returns(int24,int24);
}

interface IMigrationIdle { function totalIdle(address) external view returns(uint256); }
interface IBudgetVaultValidation {
    function validateOwner(uint256,address,bool,bool) external view returns(address);
    function validateContribution(uint256,uint256,uint256,uint256,uint128,bool)
        external view returns(address,address,uint16);
}

/// @notice Bounded execution policy for contributions and principal maintenance.
/// Created by Vault; governance can change future loss limits, never custody or recipients.
contract ZZZMigrationBudget is ReentrancyGuard {
    address public immutable vault;
    IZZZAccess public immutable access;
    uint16 public constant MAX_LOSS_BPS = 1000;
    uint256 public constant IDLE_COMPOUNDING_VERSION = 3;
    uint256 public constant REBALANCE_CONFIRMATION_VERSION = 2;
    uint32 public constant DEFAULT_COMPOUND_INTERVAL = 1 hours;
    uint16 public contributionLossBps = 200;
    uint16 public maintenanceLossBps = 300;
    uint256 public constant EMERGENCY_REBALANCE_VERSION = 1;
    bool public emergencyActive;
    uint256 public emergencyBucket;
    uint8 public emergencyChecks;
    address private emergencyGovernor;
    struct Snapshot {
        uint256 bucketId;
        uint256 value;
        uint256 price0;
        uint256 price1;
        uint256 scale0;
        uint256 scale1;
        uint256 idle0;
        uint256 idle1;
        uint16 lossBps;
        bytes32 confirmationControl;
    }
    Snapshot private snapshot;
    bool private compoundIncluded;
    /// @notice Last successful standalone compound. Local operating state, not
    /// an NFT entitlement/imported ledger; LP replacement time is kept by Vault.
    mapping(uint256 => uint64) public lastCompound;
    mapping(uint256 => uint64) public compositionEpoch;
    mapping(bytes32 => uint32) private compoundIntervals;
    error Unauthorized();
    error InvalidState();
    error InvalidAmount();
    error InvalidConfiguration();
    error Slippage();
    error Preparing();
    error CanonicalLocked();
    event MigrationValueChecked(uint256 indexed bucketId, uint256 beforeUSD, uint256 deployedUSD, uint256 idleUSD);
    event ContributionLossLimitChanged(uint16 previous, uint16 current);
    event MaintenanceLossLimitChanged(uint16 previous, uint16 current);
    event CompoundIntervalChanged(bytes32 indexed poolId,uint32 previous,uint32 current);

    constructor(address controller) {
        vault = msg.sender;
        access = IZZZAccess(controller);
    }
    /// @dev Only Migration's paused governance entry may arm the atomic context.
    function beginEmergency(uint256 bucket,uint8 checks) external nonReentrant {
        if(msg.sender != access.module(Ids.MIGRATION) || emergencyActive || snapshot.value != 0) revert Unauthorized();
        emergencyBucket = bucket; emergencyChecks = checks; emergencyGovernor = access.governance(); emergencyActive = true;
        validateEmergency(bucket);
    }
    function endEmergency() external nonReentrant {
        if(msg.sender != access.module(Ids.MIGRATION) || snapshot.value != 0) revert Unauthorized();
        validateEmergency(emergencyBucket);
        delete emergencyBucket; delete emergencyChecks; delete emergencyGovernor; emergencyActive = false;
    }
    function validateEmergency(uint256 bucket) public view {
        if(!emergencyActive || emergencyBucket != bucket || access.governance() != emergencyGovernor ||
            !access.isSealed() || !access.paused() || access.preparationActive() ||
            access.canonicalState() != 0 || access.lpExitStarted()) revert InvalidState();
    }
    function emergencyFingerprint() external view returns(bytes32 result) {
        validateEmergency(emergencyBucket);
        result = IEmergencyManifest(access.module(Ids.MIGRATION)).emergencyFingerprint();
        // A retained sample requirement must survive callbacks even when the
        // value guard is deliberately disabled. Compare the stable policy/raw
        // record, not readiness against the deliberately replaced LP identity.
        if((emergencyChecks & 16) != 0) result = keccak256(abi.encode(result,
            _confirmationControl(emergencyBucket,IZZZVault(vault).group(emergencyBucket).poolId)));
    }
    function _skip(uint8 bit) private view returns(bool) { return emergencyActive && (emergencyChecks & bit) == 0; }
    /// @notice One bounded immediate governance update. After the static access
    /// checks, only local writes/events occur: no callback can alter authority.
    function setLossLimits(uint16 contribution, uint16 maintenance) external nonReentrant {
        if (!access.canConfigure(msg.sender)) revert Unauthorized();
        if (access.preparationActive()) revert Preparing();
        if (access.canonicalState() != 0) revert CanonicalLocked();
        if (contribution > MAX_LOSS_BPS || maintenance > MAX_LOSS_BPS || snapshot.value != 0) revert InvalidConfiguration();
        emit ContributionLossLimitChanged(contributionLossBps, contribution);
        emit MaintenanceLossLimitChanged(maintenanceLossBps, maintenance);
        contributionLossBps = contribution;
        maintenanceLossBps = maintenance;
    }
    /// @notice Configure standalone compounding separately from rebalance.
    /// This changes future eligibility, never a recorded clock or NFT backing.
    function setCompoundInterval(bytes32 poolId,uint32 interval) external nonReentrant {
        if (!access.canConfigure(msg.sender)) revert Unauthorized();
        if (access.preparationActive()) revert Preparing();
        if (access.canonicalState() != 0) revert CanonicalLocked();
        if (interval < 600 || interval > 7 days || snapshot.value != 0) revert InvalidConfiguration();
        _knownPool(poolId);
        uint32 previous = _compoundInterval(poolId);
        compoundIntervals[poolId] = interval;
        emit CompoundIntervalChanged(poolId,previous,interval);
    }
    /// @notice Admitted pool policy, in seconds; one hour before its first setter.
    function compoundInterval(bytes32 poolId) external view returns(uint32) {
        _knownPool(poolId);
        return _compoundInterval(poolId);
    }
    function _compoundInterval(bytes32 poolId) private view returns(uint32 interval) {
        interval = compoundIntervals[poolId];
        if (interval == 0) interval = DEFAULT_COMPOUND_INTERVAL;
    }
    function _knownPool(bytes32 poolId) private view {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        if (poolId == bytes32(0) || c.key.tickSpacing <= 0 || keccak256(abi.encode(c.key)) != poolId) revert InvalidConfiguration();
    }
    modifier onlyVault() {
        if (msg.sender != vault) revert Unauthorized();
        _;
    }
    function recordComposition(uint256 id) external onlyVault {
        ++compositionEpoch[id];
    }
    function validateOwner(uint256 id,address caller,bool minted,bool activation) external view onlyVault returns (address entry) {
        return IBudgetVaultValidation(access.module(Ids.VAULT_CANONICAL)).validateOwner(id,caller,minted,activation);
    }
    function importComposition(uint256 id, uint64 epoch) external {
        if (msg.sender != access.module(Ids.VAULT_CANONICAL) ||
            IZZZCanonicalAccess(address(access)).canonicalState() != 2 || compositionEpoch[id] != 0) revert Unauthorized();
        compositionEpoch[id] = epoch;
    }
    function _balance(address asset) private view returns(uint256) {
        return asset==address(0)?vault.balance:IERC20(asset).balanceOf(vault);
    }
    function assertIdle(uint256 id) external view onlyVault {
        (address a,address b) = poolTokens(IZZZVault(vault).group(id).poolId);
        if (_balance(a) < IMigrationIdle(vault).totalIdle(a) ||
            _balance(b) < IMigrationIdle(vault).totalIdle(b)) revert InvalidState();
    }
    function validateCanonicalWriter(address caller) external view onlyVault {
        if (caller != access.module(Ids.VAULT_CANONICAL) || IZZZCanonicalAccess(address(access)).canonicalState() != 2) revert Unauthorized();
    }
    /// @notice Compound waits after either LP creation/replacement or compound,
    /// and yields to an eligible rebalance or preapproved range selection.
    /// Rebalance never reads lastCompound:
    /// a keeper cannot compound first to postpone needed range maintenance.
    /// Applies to all standalone compound calls, including ones needing no swap.
    function compoundReady(uint256 id) public view returns (bool) {
        return _pricing().compoundReady(id);
    }
    /// @dev Called before fee settlement, token callbacks or closing the old LP.
    /// Only attributed assets enter the starting denominator.
    function checkpoint(uint256 id, uint8 phase) external onlyVault {
        if(emergencyActive) {
            validateEmergency(id);
            if(_skip(4)) return;
        }
        if (phase == 0) _beforeMove(id);
        else if (phase == 1) _includeCompound(id);
        else if (phase == 2) _afterMove(id);
        else if (phase == 3) {
            if (!compoundReady(id)) revert InvalidState();
            _beforeMove(id);
            lastCompound[id] = uint64(block.timestamp);
        }
        else revert InvalidState();
    }
    function _beforeMove(uint256 id) private {
        if (snapshot.value != 0) revert InvalidState();
        Position memory p = IZZZVault(vault).group(id);
        Snapshot memory s;
        s.bucketId = id;
        s.lossBps = maintenanceLossBps;
        s.confirmationControl = _confirmationControl(id,p.poolId);
        // Price validates feed/sequencer freshness. Reuse this exact vector after
        // close, swap and mint; callbacks cannot reprice away execution loss.
        ZZZContributionPricing.MaintenanceMark memory mark = _pricing().markMaintenance(id);
        s.price0 = mark.price0; s.price1 = mark.price1; s.scale0 = mark.scale0; s.scale1 = mark.scale1;
        s.idle0 = mark.idle0; s.idle1 = mark.idle1; s.value = mark.value;
        if (s.value == 0) revert InvalidState();
        snapshot = s;
    }
    /// @dev Between checkpoints the guarded Vault only harvests and releases
    /// compound; harvest does not modify attributed idle. Its exact idle increase
    /// is therefore the designated compound, never donated/raw token balances.
    function _includeCompound(uint256 id) private {
        Snapshot memory s = snapshot;
        if (s.value == 0 || s.bucketId != id || compoundIncluded) revert InvalidState();
        Position memory p = IZZZVault(vault).group(id);
        snapshot.value = s.value + _value(p.idle0 - s.idle0, p.idle1 - s.idle1, s);
        compoundIncluded = true;
    }
    function _afterMove(uint256 id) private {
        Snapshot memory s = snapshot;
        if (s.value == 0 || s.bucketId != id || !compoundIncluded) revert InvalidState();
        Position memory afterPosition = IZZZVault(vault).group(id);
        (uint256 deployed, uint256 idle) = _pricing().maintenanceValues(id,s.price0,s.price1,s.scale0,s.scale1);
        uint256 retained = deployed + idle;
        // Round the captured retained-value floor up. Later policy changes cannot
        // weaken this operation's aggregate budget. Gas is
        // outside these custody ledgers. Keep the existing 5% idle ceiling under
        // this same vector, including when an admitted feed changes mid-call.
        if (s.confirmationControl != _confirmationControl(id,afterPosition.poolId) ||
            retained < s.value - Math.mulDiv(s.value, s.lossBps, 10000) || deployed == 0 ||
            idle > Math.mulDiv(retained, 500, 10000)) revert Slippage();
        delete snapshot;
        delete compoundIncluded;
        emit MigrationValueChecked(id, s.value, deployed, idle);
    }
    function _value(uint256 amount0, uint256 amount1, Snapshot memory s) private pure returns (uint256) {
        return Math.mulDiv(amount0, s.price0, s.scale0) + Math.mulDiv(amount1, s.price1, s.scale1);
    }
    /// @dev Shared current valuation keeps Vault within the standard code limit;
    /// migration checkpoints above deliberately use their cached price vector.
    function _pricing() private view returns(ZZZContributionPricing) {
        return ZZZContributionPricing(IZZZOracle(access.module(Ids.ORACLE)).contributionPricing());
    }
    function valueBucket(uint256 bucket,uint256 amount0,uint256 amount1) external view returns(uint256) {
        return _pricing().valueBucket(bucket,amount0,amount1);
    }
    function nav(uint256 id) public view returns(uint256 deployed,uint256 idle) {
        return _pricing().nav(id);
    }
    function contributionNav(uint256 id) external onlyVault returns(uint256 deployed,uint256 idle) {
        return _pricing().contributionNav(id);
    }
    function assertDeployed(uint256 id) external view {
        if(msg.sender == vault && _skip(4)) return;
        (uint256 deployed, uint256 idle) = nav(id);
        if (deployed == 0 || idle > Math.mulDiv(deployed + idle, 500, 10000)) revert Slippage();
    }
    function assertPut(uint256 id, uint256 a0, uint256 a1, uint256 spent0, uint256 spent1,
        uint256 before0, uint256 before1) external view onlyVault {
        Position memory p = IZZZVault(vault).group(id);
        (address token0, address token1) = poolTokens(p.poolId);
        address manager = IZZZLiquidity(access.module(Ids.LIQUIDITY)).positionManager();
        if (spent0 > a0 || spent1 > a1 || _balance(token0) + spent0 != before0 ||
            _balance(token1) + spent1 != before1 ||
            IPositionManagerMinimal(manager).ownerOf(p.lpTokenId) != vault) revert InvalidState();
    }
    function validateNativeSender(address sender) external view onlyVault returns (bool liquidityCredit) {
        liquidityCredit = sender == access.module(Ids.LIQUIDITY);
        if (!liquidityCredit && sender != access.module(Ids.FEES) &&
            sender != access.module(Ids.VAULT_CANONICAL)) revert Unauthorized();
    }
    function validateLPReceiver(address sender) external view onlyVault {
        address manager = access.module(Ids.LIQUIDITY);
        if (manager == address(0) || sender != IZZZLiquidity(manager).positionManager()) revert Unauthorized();
    }
    function mintTarget(uint256 id) external view onlyVault returns (int24,int24,uint160) {
        if(emergencyActive) {
            validateEmergency(id);
            (int24 lower,int24 upper) = IEmergencyManifest(access.module(Ids.MIGRATION)).emergencyTarget();
            return(lower,upper,
                IZZZLiquidity(access.module(Ids.LIQUIDITY)).spot(IZZZVault(vault).group(id).poolId));
        }
        return IZZZStrategy(access.module(Ids.STRATEGY)).target(IZZZVault(vault).group(id).poolId);
    }
    /// @notice Bind prices, target policy and admitted execution controls across
    /// the Vault's complete approval/balance/reset sequence, not only the router.
    function balanceContext(uint256 id) external view onlyVault returns(bytes32) {
        if(emergencyActive) { validateEmergency(id); return this.emergencyFingerprint(); }
        return IZZZLiquidity(access.module(Ids.LIQUIDITY)).balanceContext(IZZZVault(vault).group(id).poolId);
    }
    function poolTokens(bytes32 poolId) public view returns (address token0, address token1) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        return (c.key.currency0, c.key.currency1);
    }
    function validateReservation(bytes32 poolId,uint256 bucket) external view onlyVault {
        if (poolId == bytes32(0) || bucket == 0) revert InvalidConfiguration();
        IZZZPools(access.module(Ids.POOLS)).get(poolId);
        uint256 old = IZZZVault(vault).poolBucket(poolId);
        if (old != 0 && old != bucket) revert InvalidState();
    }
    function validateMove(uint256 id, bytes32 nextPool, uint128 minimumLiquidity) external view onlyVault {
        PoolConfig memory oldConfig = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(vault).group(id).poolId);
        PoolConfig memory nextConfig = IZZZPools(access.module(Ids.POOLS)).accounting(nextPool);
        if (minimumLiquidity == 0 || oldConfig.key.currency0 != nextConfig.key.currency0 ||
            oldConfig.key.currency1 != nextConfig.key.currency1 || !nextConfig.operationsEnabled) revert InvalidConfiguration();
    }
    function validateUnwind(uint256 id) external view onlyVault {
        if(_skip(2)) return;
        IZZZStrategy(access.module(Ids.STRATEGY)).validateExitPrice(IZZZVault(vault).group(id).poolId);
    }
    function validateRebalance(uint256 id, uint128 minimumLiquidity) external view onlyVault {
        if(emergencyActive) {
            validateEmergency(id);
            if(!_skip(1) && !IZZZStrategy(access.module(Ids.STRATEGY)).needsRebalance(id)) revert InvalidState();
            if(!_skip(16) && !IConfirmationControl(IZZZStrategy(access.module(Ids.STRATEGY)).rebalanceConfirmation())
                .emergencyReady(id)) revert InvalidState();
            return;
        }
        if (minimumLiquidity == 0 || !IZZZStrategy(access.module(Ids.STRATEGY)).rebalanceReady(id)) revert InvalidState();
    }
    function _confirmationControl(uint256 id,bytes32 poolId) private view returns(bytes32) {
        IConfirmationControl confirmation = IConfirmationControl(
            IZZZStrategy(access.module(Ids.STRATEGY)).rebalanceConfirmation());
        // Compare raw evidence, not post-replacement readiness (the new LP
        // deliberately has a different identity). A callback reset must abort.
        return confirmation.observationFingerprint(id,poolId);
    }
    function idleValue(uint256 id) public view returns (uint256) {
        if(msg.sender == vault && _skip(4)) return 0; // Internal sentinel, never an external zero USD valuation.
        Position memory p = IZZZVault(vault).group(id);
        (address token0, address token1) = poolTokens(p.poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        return oracle.value(token0, p.idle0) + oracle.value(token1, p.idle1);
    }
    function assertIdleLoss(uint256 id, uint256 beforeValue) external view onlyVault {
        if(_skip(4)) return;
        uint16 slippage = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(vault).group(id).poolId).maxSlippageBps;
        if (beforeValue == 0 || idleValue(id) < Math.mulDiv(beforeValue, 10000 - slippage, 10000)) revert Slippage();
    }
    function validateContribution(uint256 id, uint256 bucket, uint256 inputUSD, uint256 inputTotal,
        uint128 minimumLiquidity, bool activation) external onlyVault returns (address token0, address token1, uint32 limits) {
        uint16 captured = contributionLossBps;
        uint16 venue;
        (token0,token1,venue) = IBudgetVaultValidation(access.module(Ids.VAULT_CANONICAL)).validateContribution(
            id,bucket,inputUSD,inputTotal,minimumLiquidity,activation);
        // Carry both limits in the existing third ABI word: low 16 bits are the
        // venue limit; high 16 bits freeze the contribution policy before callbacks.
        limits = uint32(venue) | (uint32(captured) << 16);
        _pricing().begin(id,bucket,inputTotal,inputUSD,limits);
    }
    function contributionResult(uint256 bucket,uint256 inputUSD,uint256 supply,uint256 incumbentNAV,
        uint256 incumbentDeployed,uint256 deployed,uint256 idle,uint32 limits)
        external onlyVault returns(uint256 issued,uint256 netUSD) {
        return _pricing().finish(bucket,inputUSD,supply,incumbentNAV,incumbentDeployed,deployed,idle,limits);
    }
    function historicalCompoundValue(uint256 id) public view returns(uint256) {
        return _pricing().historicalValue(id);
    }
}
