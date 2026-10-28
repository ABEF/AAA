// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZOracle, IZZZRewards, IZZZLiquidity, IStateViewMinimal} from "./interfaces/IZZZ.sol";
import {ZZZActivationAssets} from "./ZZZActivationAssets.sol";
import {ZZZActivationEntry} from "./ZZZActivationEntry.sol";
import {ZZZActivationAssetsFactory} from "./ZZZActivationAssetsFactory.sol";

interface INativeVenueBindings {
    function poolManager() external view returns (address);
    function stateView() external view returns (address);
    function permit2() external view returns (address);
}

/// @notice Append-only pool identities; bounded strategy parameters are governed.
/// Native support is restricted to static, hookless ETH/ZZZ on pinned Robinhood v4.
/// Both get() and accounting() preserve the real native ETH identity at slot zero.
contract ZZZPoolRegistry is ZZZModule {
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    bytes32 public constant SELECTED_NATIVE_POOL = 0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b;
    address private constant CORE = 0x8366a39CC670B4001A1121B8F6A443A643e40951;
    address private constant POSM = 0x58daec3116aae6D93017bAAea7749052E8a04fA7;
    address private constant STATE = 0xF3334192D15450CdD385c8B70e03f9A6bD9E673b;
    address private constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;
    address private constant ZZZ = 0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    mapping(bytes32 => PoolConfig) private pools;
    mapping(bytes32 => bool) public exists;
    /// @notice Zero means contributions are stopped. Historical/maintenance
    /// pools remain admitted, but at most one pool can enable new contributions.
    bytes32 public contributionPool;
    /// @notice Invalidates atomic execution reviews even if a callback restores
    /// the old values. Append-only storage; no change to historical deployments.
    uint64 public configurationRevision;
    event PoolConfigured(bytes32 indexed poolId, address indexed token0, address indexed token1);
    event PoolDisabled(bytes32 indexed poolId, bool depositsEnabled, bool operationsEnabled);
    event ContributionPoolChanged(bytes32 indexed previousPool, bytes32 indexed currentPool);
    constructor(address controller) ZZZModule(controller) {
        activationAssets = ZZZActivationAssets(ZZZActivationAssetsFactory(access.activationAssetsFactory()).create());
        activationEntry = new ZZZActivationEntry(controller, address(this), address(activationAssets));
    }
    /// @notice Admit a static hookless ETH/ZZZ pool, including future fee tiers.
    /// The selected launch identity does not prevent governed moves after sealing.
    /// Only native ETH/fixed ZZZ LP is admitted: every funded bucket must remain
    /// settleable to holders as ETH + ZZZ. ERC20 conversion venues are separate.
    /// Runtime/wiring are rechecked on every accounting/isNativePool read.
    function configureNative(PoolConfig calldata config) external onlyGovernance principalOperating returns (bytes32 poolId) {
        PoolKey memory key = config.key;
        if (key.currency0 != address(0) || key.currency1 != ZZZ || key.hooks != address(0) || key.fee > 100000 ||
            activationAssets.zzz() != ZZZ) {
            revert InvalidConfiguration();
        }
        _nativeBindings();
        poolId = keccak256(abi.encode(key));
        // Core protocol fees can change independently of the immutable static LP fee.
        // Swaps enforce actual net output; a fee-policy change must not freeze custody.
        (uint160 price,,, uint24 lpFee) = IStateViewMinimal(STATE).getSlot0(poolId);
        if (price == 0 || lpFee != key.fee) revert InvalidConfiguration();
        return _configure(config, address(0), ZZZ);
    }
    /// @notice Restrict an admitted pool without reading tokens, prices or venue
    /// dependencies. True flags DISABLE the respective capability; false keeps
    /// its current state. Re-enabling requires full configureNative validation.
    function disablePool(bytes32 poolId, bool disableDeposits, bool disableOperations) external onlyGovernance {
        if (!exists[poolId] || (!disableDeposits && !disableOperations)) revert InvalidConfiguration();
        PoolConfig storage config = pools[poolId];
        if (disableDeposits) {
            config.depositsEnabled = false;
            if (contributionPool == poolId) _setContributionPool(bytes32(0));
        }
        if (disableOperations) config.operationsEnabled = false;
        ++configurationRevision;
        emit PoolDisabled(poolId, config.depositsEnabled, config.operationsEnabled);
    }
    /// @notice Fixed Strategy may apply only its reviewed two-width policy.
    /// No keeper can call this directly or change assets, flags or other limits.
    function applyKeeperRange(bytes32 poolId,uint16 width) external onlyModule(Ids.STRATEGY) {
        // The fixed controller's moduleAuthorized already enforces sealed and
        // canonical-operating identity. All remaining calls are static and all
        // writes below are local: there is no callback requiring a second read.
        if (access.paused()) revert Paused();
        if (access.preparationActive()) revert Preparing();
        if (access.lpExitStarted()) revert LPExitLocked();
        PoolConfig storage c = pools[poolId];
        if (!exists[poolId] || !c.operationsEnabled || (width != 2500 && width != 5000) ||
            c.triggerBps >= width || c.maxSpotDeviationBps >= width) revert InvalidConfiguration();
        c.rangeBps = width; // Strategy emits the successful old/new width and review hash.
        ++configurationRevision;
    }
    function _configure(PoolConfig calldata config, address token0, address token1) internal returns (bytes32 poolId) {
        PoolKey memory k = config.key;
        poolId = keccak256(abi.encode(k));
        if (poolId == bytes32(0) || (config.depositsEnabled && contributionPool != bytes32(0) &&
            contributionPool != poolId)) revert InvalidConfiguration();
        if (k.tickSpacing <= 0 || k.tickSpacing > 32767 || k.fee > 100000 ||
            config.rangeBps < 100 || config.rangeBps > 5000 || config.triggerBps < 100 ||
            config.triggerBps >= config.rangeBps || config.maxSpotDeviationBps == 0 ||
            config.maxSpotDeviationBps > 500 || config.maxSpotDeviationBps >= config.rangeBps || config.maxSlippageBps == 0 || config.maxSlippageBps > 1000 || k.fee >= uint24(config.maxSlippageBps) * 100 ||
            config.minRebalanceInterval < 600 || config.minRebalanceInterval > 7 days ||
            config.minDepositUSD == 0 || config.maxPositionUSD < config.minDepositUSD) revert InvalidConfiguration();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        oracle.price(token0);
        oracle.price(token1);
        IZZZRewards rewards = IZZZRewards(access.module(Ids.REWARDS));
        if (!rewards.isAsset(token0) || !rewards.isAsset(token1)) revert InvalidConfiguration();
        activationAssets.admitPoolAsset(token0);
        activationAssets.admitPoolAsset(token1);
        pools[poolId] = config;
        exists[poolId] = true;
        if (config.depositsEnabled) _setContributionPool(poolId);
        else if (contributionPool == poolId) _setContributionPool(bytes32(0));
        ++configurationRevision;
        emit PoolConfigured(poolId, k.currency0, k.currency1);
    }
    function _setContributionPool(bytes32 poolId) private {
        bytes32 previous = contributionPool;
        if (previous == poolId) return;
        contributionPool = poolId;
        emit ContributionPoolChanged(previous, poolId);
    }
    function get(bytes32 poolId) external view returns (PoolConfig memory) {
        if (!exists[poolId]) revert InvalidConfiguration();
        return pools[poolId];
    }
    function accounting(bytes32 poolId) public view returns (PoolConfig memory c) {
        if (!exists[poolId]) revert InvalidConfiguration();
        c = pools[poolId];
        if (c.key.currency0 == address(0)) {
            _nativeBindings();
        }
    }
    /// @notice Source eligibility affects new contributions only, never existing LP/reward ledgers.
    function contributionValue(bytes32 poolId, uint256 amount0, uint256 amount1) external view returns (uint256) {
        if (msg.sender == access.module(Ids.VAULT)) {
            // Only the immutable child's actual fixed Vault call can carry an
            // original-source valuation. An armed mismatched context reverts.
            uint256 sourceUSD = activationEntry.sourceValue(poolId, amount0, amount1);
            if (sourceUSD != 0) return sourceUSD;
        }
        PoolConfig memory c = accounting(poolId);
        return activationAssets.value(c.key.currency0, amount0) + activationAssets.value(c.key.currency1, amount1);
    }
    /// @notice Whether an admitted pool settles its first currency as native ETH.
    function isNativePool(bytes32 poolId) public view returns (bool) {
        if (!exists[poolId]) revert InvalidConfiguration();
        if (pools[poolId].key.currency0 != address(0)) return false;
        _nativeBindings();
        return true;
    }
    function _nativeBindings() private view {
        if (block.chainid != 4663 ||
            CORE.codehash != 0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626 ||
            POSM.codehash != 0xc873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2 ||
            STATE.codehash != 0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6 ||
            PERMIT2.codehash != 0x5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca ||
            ZZZ.codehash != 0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597) {
            revert InvalidConfiguration();
        }
        // Native settlement and custody do not call or rely on WETH, its
        // implementation, its admin, or the periphery's optional wrapper getter.
        address manager = access.module(Ids.LIQUIDITY);
        if (IZZZLiquidity(manager).positionManager() != POSM ||
            INativeVenueBindings(manager).poolManager() != CORE || INativeVenueBindings(manager).stateView() != STATE ||
            INativeVenueBindings(manager).permit2() != PERMIT2) {
            revert InvalidConfiguration();
        }
    }
}
