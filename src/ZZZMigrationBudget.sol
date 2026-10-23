// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZOracle, IZZZLiquidity, IZZZStrategy, IZZZFees, IZZZMigration, IPositionManagerMinimal, IZZZNFT, IZZZActivationEntry} from "./interfaces/IZZZ.sol";
interface IPairAssets { function assetCount() external view returns(uint256); function assets(uint256) external view returns(address); }
interface IPairVault { function migrationBudget() external view returns(ZZZMigrationBudget); }
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";

interface IMigrationContribution { function contributionUSD(uint256 id) external view returns (uint256); }
interface IMigrationIdle { function totalIdle(address) external view returns(uint256); }

/// @notice Fixed execution budget for atomic rebalances and same-pair custody moves.
/// Created by its only caller, Vault. No token custody, configuration or executor.
contract ZZZMigrationBudget {
    address public immutable vault;
    IZZZAccess public immutable access;
    struct Snapshot {
        uint256 bucketId;
        uint256 value;
        uint256 price0;
        uint256 price1;
        uint256 scale0;
        uint256 scale1;
        uint256 idle0;
        uint256 idle1;
    }
    Snapshot private snapshot;
    bool private compoundIncluded;
    mapping(uint256 => uint64) public compositionEpoch;
    error Unauthorized();
    error InvalidState();
    error InvalidAmount();
    error InvalidConfiguration();
    error Slippage();
    event MigrationValueChecked(uint256 indexed bucketId, uint256 beforeUSD, uint256 deployedUSD, uint256 idleUSD);

    constructor(address controller) {
        vault = msg.sender;
        access = IZZZAccess(controller);
    }
    modifier onlyVault() {
        if (msg.sender != vault) revert Unauthorized();
        _;
    }
    function recordComposition(uint256 id) external onlyVault {
        ++compositionEpoch[id];
    }
    function validateOwner(uint256 id,address caller,bool minted,bool activation) external view onlyVault returns (address entry) {
        if (block.chainid != IZZZVault(vault).canonicalChainId() || !minted) revert Unauthorized();
        if (activation && (IZZZVault(vault).nftBucket(id) != 0 || !IZZZNFT(access.module(Ids.NFT)).traitsReady(id))) revert InvalidState();
        if (IZZZNFT(access.module(Ids.NFT)).ownerOf(id) == caller) return address(0);
        entry = IZZZPools(access.module(Ids.POOLS)).activationEntry();
        if (entry == address(0) || caller != entry) revert Unauthorized();
    }
    function importComposition(uint256 id, uint64 epoch) external {
        if (msg.sender != access.module(Ids.VAULT_CANONICAL) ||
            IZZZCanonicalAccess(address(access)).canonicalState() != 2 || compositionEpoch[id] != 0) revert Unauthorized();
        compositionEpoch[id] = epoch;
    }
    function assertIdle(uint256 id) external view onlyVault {
        (address a,address b) = poolTokens(IZZZVault(vault).group(id).poolId);
        if (IERC20(a).balanceOf(vault) < IMigrationIdle(vault).totalIdle(a) ||
            IERC20(b).balanceOf(vault) < IMigrationIdle(vault).totalIdle(b)) revert InvalidState();
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
        else revert InvalidState();
    }
    function _beforeMove(uint256 id) private {
        if (snapshot.value != 0) revert InvalidState();
        Position memory p = IZZZVault(vault).group(id);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        Snapshot memory s;
        s.bucketId = id;
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
        // ceil(97%): rounding never permits more than 3% aggregate loss. Gas is
        // outside these custody ledgers. Keep the existing 5% idle ceiling under
        // this same vector, including when an admitted feed changes mid-call.
        if (retained < s.value - Math.mulDiv(s.value, 300, 10000) || deployed == 0 ||
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
    function valueBucket(uint256 bucket, uint256 amount0, uint256 amount1) external view returns (uint256) {
        (address token0,address token1) = poolTokens(IZZZVault(vault).group(bucket).poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        return oracle.value(token0, amount0) + oracle.value(token1, amount1);
    }
    /// @dev Read-only validation extracted from custody; all writes and exact
    /// token movement remain in the immutable caller Vault.
    function nav(uint256 id) public view returns (uint256 deployed, uint256 idle) {
        Position memory p = IZZZVault(vault).group(id);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        if (p.lpTokenId != 0) {
            (uint256 a0, uint256 a1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(p.lpTokenId);
            deployed = oracle.value(c.key.currency0, a0) + oracle.value(c.key.currency1, a1);
        }
        idle = oracle.value(c.key.currency0, p.idle0) + oracle.value(c.key.currency1, p.idle1);
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
        if (spent0 > a0 || spent1 > a1 || IERC20(token0).balanceOf(vault) + spent0 != before0 ||
            IERC20(token1).balanceOf(vault) + spent1 != before1 ||
            IPositionManagerMinimal(manager).ownerOf(p.lpTokenId) != vault) revert InvalidState();
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
    function idleValue(uint256 id) public view returns (uint256) {
        Position memory p = IZZZVault(vault).group(id);
        (address token0, address token1) = poolTokens(p.poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        return oracle.value(token0, p.idle0) + oracle.value(token1, p.idle1);
    }
    function assertIdleLoss(uint256 id, uint256 beforeValue) external view onlyVault {
        uint16 slippage = IZZZPools(access.module(Ids.POOLS)).accounting(IZZZVault(vault).group(id).poolId).maxSlippageBps;
        if (idleValue(id) < Math.mulDiv(beforeValue, 10000 - slippage, 10000)) revert Slippage();
    }
    function validateContribution(uint256 id, uint256 bucket, uint256 inputUSD, uint256 inputTotal,
        uint128 minimumLiquidity, bool activation) external view onlyVault returns (address token0, address token1, uint16 maxSlippageBps) {
        Position memory p = IZZZVault(vault).group(bucket);
        if (p.status != PositionStatus.Active || p.homeChain != block.chainid || p.homeVault != vault ||
            !IZZZFees(access.module(Ids.FEES)).remoteSettled(bucket) ||
            IZZZMigration(access.module(Ids.MIGRATION)).activePlan(bucket) != bytes32(0)) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if (!c.depositsEnabled || inputTotal == 0 || minimumLiquidity == 0 ||
            (activation && inputUSD < 100e18) || (!activation && inputUSD < 5e18) || inputUSD < c.minDepositUSD ||
            IMigrationContribution(vault).contributionUSD(id) + inputUSD > c.maxPositionUSD) revert InvalidAmount();
        return (c.key.currency0, c.key.currency1, c.maxSlippageBps);
    }
    function contributionResult(uint256 bucket, uint256 inputUSD, uint256 supply, uint256 incumbentNAV,
        uint256 incumbentDeployed, uint256 deployed, uint256 idle, uint16 maxSlippageBps)
        external view returns (uint256 issued, uint256 netUSD) {
        if (IZZZFees(access.module(Ids.FEES)).hasPendingExternal()) revert InvalidState();
        if (deployed == 0 || idle > Math.mulDiv(deployed + idle, 500, 10000)) revert Slippage();
        if (deployed + idle <= incumbentNAV) revert InvalidAmount();
        netUSD = deployed + idle - incumbentNAV;
        if (netUSD < Math.mulDiv(inputUSD, 10000 - maxSlippageBps, 10000)) revert Slippage();
        uint256 minimumNet = inputUSD - inputUSD / 100;
        if (netUSD < minimumNet || deployed < incumbentDeployed + minimumNet) revert Slippage();
        issued = supply == 0 ? netUSD : Math.mulDiv(supply, netUSD, incumbentNAV + historicalCompoundValue(bucket));
        if (issued == 0 || supply + issued > 1e36) revert InvalidAmount();
    }
    /// @notice Late old-currency compounding remains part of incumbent backing.
    /// It is not the new contribution's deployed LP and cannot subsidize its 99% floor.
    function historicalCompoundValue(uint256 id) public view returns (uint256 value) {
        if (compositionEpoch[id] == 0) return 0;
        (address a,address b) = poolTokens(IZZZVault(vault).group(id).poolId);
        IPairAssets admitted = IPairAssets(access.module(Ids.REWARDS));
        if (admitted.assetCount() > 32) revert InvalidState();
        for (uint256 i; i < admitted.assetCount(); ++i) {
            address token = admitted.assets(i);
            if (token == address(0) || token == a || token == b) continue;
            uint256 amount = IZZZFees(access.module(Ids.FEES)).compoundBalance(id,token);
            if (amount != 0) value += IZZZOracle(access.module(Ids.ORACLE)).value(token,amount);
        }
    }
}
