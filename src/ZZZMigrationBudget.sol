// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZContributionPricing} from "./ZZZContributionPricing.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZOracle, IZZZLiquidity, IZZZStrategy, IZZZFees, IZZZMigration, IPositionManagerMinimal, IZZZNFT, IZZZActivationEntry} from "./interfaces/IZZZ.sol";
interface IPairAssets { function assetCount() external view returns(uint256); function assets(uint256) external view returns(address); }
interface IPairVault { function migrationBudget() external view returns(ZZZMigrationBudget); }
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";

interface IMigrationContribution { function contributionUSD(uint256 id) external view returns (uint256); }
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
    uint256 public constant IDLE_COMPOUNDING_VERSION = 1;
    uint16 public contributionLossBps = 200;
    uint16 public maintenanceLossBps = 300;
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
    }
    Snapshot private snapshot;
    bool private compoundIncluded;
    /// @notice Local operating cooldown, not an NFT entitlement or imported ledger.
    mapping(uint256 => uint64) public lastCompound;
    mapping(uint256 => uint64) public compositionEpoch;
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

    constructor(address controller) {
        vault = msg.sender;
        access = IZZZAccess(controller);
    }
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
    /// @dev Called before fee settlement, token callbacks or closing the old LP.
    /// Only attributed assets enter the starting denominator.
    function checkpoint(uint256 id, uint8 phase) external onlyVault {
        if (phase == 0) _beforeMove(id);
        else if (phase == 1) _includeCompound(id);
        else if (phase == 2) _afterMove(id);
        else if (phase == 3) {
            Position memory p = IZZZVault(vault).group(id);
            if (p.lpTokenId == 0) revert InvalidState();
            uint256 previous = lastCompound[id];
            if (previous != 0 && block.timestamp < previous +
                IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId).minRebalanceInterval) revert InvalidState();
            _beforeMove(id);
            lastCompound[id] = uint64(block.timestamp);
        }
        else revert InvalidState();
    }
    function _beforeMove(uint256 id) private {
        if (snapshot.value != 0) revert InvalidState();
        Position memory p = IZZZVault(vault).group(id);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        Snapshot memory s;
        s.bucketId = id;
        s.lossBps = maintenanceLossBps;
        // Price validates feed/sequencer freshness. Reuse this exact vector after
        // close, swap and mint; callbacks cannot reprice away execution loss.
        s.price0 = oracle.price(c.key.currency0);
        s.price1 = oracle.price(c.key.currency1);
        s.scale0 = 10 ** oracle.tokenDecimals(c.key.currency0);
        s.scale1 = 10 ** oracle.tokenDecimals(c.key.currency1);
        s.idle0 = p.idle0;
        s.idle1 = p.idle1;
        (uint256 deployed, uint256 idle) = _values(p, s);
        s.value = deployed + idle;
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
        (uint256 deployed, uint256 idle) = _values(IZZZVault(vault).group(id), s);
        uint256 retained = deployed + idle;
        // Round the captured retained-value floor up. Later policy changes cannot
        // weaken this operation's aggregate budget. Gas is
        // outside these custody ledgers. Keep the existing 5% idle ceiling under
        // this same vector, including when an admitted feed changes mid-call.
        if (retained < s.value - Math.mulDiv(s.value, s.lossBps, 10000) || deployed == 0 ||
            idle > Math.mulDiv(retained, 500, 10000)) revert Slippage();
        delete snapshot;
        delete compoundIncluded;
        emit MigrationValueChecked(id, s.value, deployed, idle);
    }
    function _values(Position memory p, Snapshot memory s) private view returns (uint256 deployed, uint256 idle) {
        if (p.lpTokenId != 0) {
            (uint256 amount0, uint256 amount1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(p.lpTokenId);
            deployed = _value(amount0, amount1, s);
        }
        idle = _value(p.idle0, p.idle1, s);
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
        return IZZZStrategy(access.module(Ids.STRATEGY)).target(IZZZVault(vault).group(id).poolId);
    }
    function balancePlan(uint256 id, bool existingRange)
        external view returns (bool zeroForOne, uint256 amountIn, uint256 minimumOut, address input) {
        Position memory p = IZZZVault(vault).group(id);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        IZZZStrategy strategy = IZZZStrategy(access.module(Ids.STRATEGY));
        if (existingRange) (zeroForOne, amountIn, minimumOut) = strategy.compoundPlan(id, p.idle0, p.idle1);
        else (zeroForOne, amountIn, minimumOut) = strategy.swapPlan(p.poolId, p.idle0, p.idle1);
        // Ignore corrections no greater than one basis point of this bucket's
        // available input. Precision dust does not justify another fee-bearing swap.
        if (amountIn <= (zeroForOne ? p.idle0 : p.idle1) / 10000) amountIn = 0;
        input = zeroForOne ? c.key.currency0 : c.key.currency1;
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
        IZZZStrategy(access.module(Ids.STRATEGY)).validateExitPrice(IZZZVault(vault).group(id).poolId);
    }
    function validateRelease(uint256 id) external view onlyVault {
        Position memory p = IZZZVault(vault).group(id);
        if (p.status != PositionStatus.Parked || p.lpTokenId != 0 ||
            p.homeChain != block.chainid || p.homeVault != vault) revert InvalidState();
    }
    function validateHandoff(uint256 id) external view onlyVault {
        Position memory p = IZZZVault(vault).group(id);
        if (p.status != PositionStatus.Outbound || p.lpTokenId != 0 || p.idle0 != 0 || p.idle1 != 0) revert InvalidState();
    }
    function validateRebalance(uint256 id, uint128 minimumLiquidity) external view onlyVault {
        if (minimumLiquidity == 0 || !IZZZStrategy(access.module(Ids.STRATEGY)).needsRebalance(id)) revert InvalidState();
    }
    function idleValue(uint256 id) public view returns (uint256) {
        Position memory p = IZZZVault(vault).group(id);
        (address token0, address token1) = poolTokens(p.poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        return oracle.value(token0, p.idle0) + oracle.value(token1, p.idle1);
    }
    function assertIdleLoss(uint256 id, uint256 beforeValue) external view onlyVault {
        uint16 slippage = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(vault).group(id).poolId).maxSlippageBps;
        if (beforeValue == 0 || idleValue(id) < Math.mulDiv(beforeValue, 10000 - slippage, 10000)) revert Slippage();
    }
    /// @notice The end-to-end custody minimum cannot weaken a swap's own floor.
    /// A looser overall request is tightened here, not passed to an adapter that
    /// must reject it. This never relaxes the original approved Migration budget.
    function handoffMinimum(uint256 id,address input,address output,uint256 amount,uint256 requested)
        public view onlyVault returns(uint256) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(vault).group(id).poolId);
        uint256 floor = Math.mulDiv(IZZZOracle(access.module(Ids.ORACLE)).quote(input,output,amount),
            10000-c.maxSlippageBps,10000);
        return Math.max(requested,floor);
    }
    struct HandoffSwap { bool direction; address input; uint256 amount; uint256 held; uint256 minimum; }
    /// @dev Read-only extraction; custody, approval and exact sends stay in Vault.
    function handoffPlan(uint256 id,address zzz,uint256 minimumZZZ) external view onlyVault returns(HandoffSwap memory plan) {
        Position memory p = IZZZVault(vault).group(id);
        if (!access.paused() || p.status != PositionStatus.Parked || p.lpTokenId != 0) revert InvalidState();
        (address t0,address t1) = poolTokens(p.poolId);
        if (zzz == address(0) || (zzz != t0 && zzz != t1)) revert InvalidConfiguration();
        plan.direction = zzz == t1;
        plan.input = plan.direction ? t0 : t1;
        plan.amount = plan.direction ? p.idle0 : p.idle1;
        plan.held = plan.direction ? p.idle1 : p.idle0;
        if (plan.amount != 0) plan.minimum = handoffMinimum(id,plan.input,zzz,plan.amount,
            minimumZZZ > plan.held ? minimumZZZ-plan.held : 1);
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
