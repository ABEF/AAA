// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZNFT, IZZZPower, IZZZFees, IZZZPools, IZZZOracle, IZZZStrategy, IZZZLiquidity,
    IPositionManagerMinimal} from "./interfaces/IZZZ.sol";

/// @notice Non-upgradeable custody. Principal has no owner/admin redemption path.
/// Deposits, idle assets, compound reserves and earned fees are separate ledgers.
contract ZZZVault is ZZZModule, ReentrancyGuard, IERC721Receiver {
    using SafeERC20 for IERC20;
    mapping(uint256 => Position) private positions;
    mapping(address => uint256) public totalIdle;
    uint256 public sequence;
    uint256 public immutable canonicalChainId;
    uint256 public constant MAX_IDLE_BPS = 500; // At least 95% deployed by oracle value after LP updates.
    event Deposited(uint256 indexed nftId, address indexed owner, bytes32 indexed poolId, uint256 amount0, uint256 amount1);
    event LiquidityAdded(uint256 indexed nftId, uint256 amount0, uint256 amount1);
    event FeesCollected(uint256 indexed nftId, uint256 amount0, uint256 amount1);
    event Rebalanced(uint256 indexed nftId, uint256 oldLpTokenId, uint256 newLpTokenId, uint160 centerX96);
    event Compounded(uint256 indexed nftId, uint256 amount0, uint256 amount1);
    event PrincipalBridged(uint256 indexed nftId, bytes32 indexed migrationId, uint256 amount0, uint256 amount1);
    event ImportPending(uint256 indexed nftId, uint256 indexed homeChain, address indexed homeVault);
    event ImportFinalized(uint256 indexed nftId, uint256 lpTokenId);
    event LocationConfirmed(uint256 indexed nftId, uint256 chainId, address destinationVault);
    constructor(address controller, uint256 nftHomeChain) ZZZModule(controller) {
        if (nftHomeChain == 0) revert InvalidConfiguration();
        canonicalChainId = nftHomeChain;
    }
    function position(uint256 id) external view returns (Position memory) { return positions[id]; }
    function _pool(uint256 id) private view returns (PoolConfig memory) {
        return IZZZPools(access.module(Ids.POOLS)).get(positions[id].poolId);
    }
    function _isHome(Position storage p) private view returns (bool) {
        return p.homeChain == block.chainid && p.homeVault == address(this);
    }
    function _active(uint256 id) private view {
        if (positions[id].status != PositionStatus.Active) revert InvalidState();
    }
    function _idle(uint256 id, uint256 new0, uint256 new1) private {
        if (new0 > type(uint128).max || new1 > type(uint128).max) revert InvalidAmount();
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        totalIdle[c.key.currency0] = totalIdle[c.key.currency0] - p.idle0 + new0;
        totalIdle[c.key.currency1] = totalIdle[c.key.currency1] - p.idle1 + new1;
        p.idle0 = new0;
        p.idle1 = new1;
        if (IERC20(c.key.currency0).balanceOf(address(this)) < totalIdle[c.key.currency0] ||
            IERC20(c.key.currency1).balanceOf(address(this)) < totalIdle[c.key.currency1]) revert InvalidState();
    }
    function _put(uint256 id, bool create, uint128 minimumLiquidity, uint256 deadline) private {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        IZZZLiquidity manager = IZZZLiquidity(access.module(Ids.LIQUIDITY));
        uint256 a0 = p.idle0;
        uint256 a1 = p.idle1;
        uint256 before0 = IERC20(c.key.currency0).balanceOf(address(this));
        uint256 before1 = IERC20(c.key.currency1).balanceOf(address(this));
        IERC20(c.key.currency0).forceApprove(address(manager), a0);
        IERC20(c.key.currency1).forceApprove(address(manager), a1);
        uint256 spent0;
        uint256 spent1;
        if (create) {
            (int24 lower, int24 upper, uint160 ref) = IZZZStrategy(access.module(Ids.STRATEGY)).target(p.poolId);
            (p.lpTokenId, spent0, spent1) = manager.mint(p.poolId, lower, upper, a0, a1, minimumLiquidity, deadline);
            IPositionManagerMinimal(manager.positionManager()).approve(address(manager), p.lpTokenId);
            p.centerX96 = ref;
            p.lastRebalance = uint64(block.timestamp);
        } else {
            (spent0, spent1) = manager.increase(p.poolId, p.lpTokenId, a0, a1, minimumLiquidity, deadline);
        }
        IERC20(c.key.currency0).forceApprove(address(manager), 0);
        IERC20(c.key.currency1).forceApprove(address(manager), 0);
        if (spent0 > a0 || spent1 > a1 ||
            IERC20(c.key.currency0).balanceOf(address(this)) + spent0 != before0 ||
            IERC20(c.key.currency1).balanceOf(address(this)) + spent1 != before1 ||
            IPositionManagerMinimal(manager.positionManager()).ownerOf(p.lpTokenId) != address(this)) revert InvalidState();
        _idle(id, a0 - spent0, a1 - spent1);
        (uint256 deployed0, uint256 deployed1) = manager.amounts(p.lpTokenId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        uint256 deployedValue = oracle.value(c.key.currency0, deployed0) + oracle.value(c.key.currency1, deployed1);
        uint256 idleValue = _idleValue(id);
        if (deployedValue == 0 || idleValue > Math.mulDiv(deployedValue + idleValue, MAX_IDLE_BPS, 10000)) revert Slippage();
    }
    function deposit(bytes32 poolId, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline)
        external live nonReentrant returns (uint256 id) {
        // Satellite vaults can receive migrated positions, but never issue a second collection.
        if (block.chainid != canonicalChainId) revert InvalidState();
        _deadline(deadline);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        if (!c.depositsEnabled || amount0 + amount1 == 0 || minimumLiquidity == 0) revert InvalidAmount();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        uint256 valueUSD = oracle.value(c.key.currency0, amount0) + oracle.value(c.key.currency1, amount1);
        if (valueUSD < c.minDepositUSD || valueUSD > c.maxPositionUSD) revert InvalidAmount();
        id = uint256(keccak256(abi.encode(block.chainid, address(this), ++sequence)));
        if (positions[id].status != PositionStatus.None) revert InvalidState();
        Position storage p = positions[id];
        p.poolId = poolId;
        p.depositUSD = valueUSD;
        p.status = PositionStatus.Active;
        p.homeChain = block.chainid;
        p.homeVault = address(this);
        p.homeReceiver = access.module(Ids.RECEIVER);
        p.homeToken0 = c.key.currency0;
        p.homeToken1 = c.key.currency1;
        p.locationChain = block.chainid;
        p.locationVault = address(this);
        ExactToken.pull(c.key.currency0, msg.sender, amount0);
        ExactToken.pull(c.key.currency1, msg.sender, amount1);
        _idle(id, amount0, amount1);
        _balance(id, deadline);
        if (_idleValue(id) < Math.mulDiv(valueUSD, 10000 - c.maxSlippageBps, 10000)) revert Slippage();
        _put(id, true, minimumLiquidity, deadline);
        IZZZNFT(access.module(Ids.NFT)).mint(msg.sender, id);
        IZZZPower(access.module(Ids.POWER)).add(id, valueUSD);
        emit Deposited(id, msg.sender, poolId, amount0, amount1);
    }
    function increase(uint256 id, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline)
        external live nonReentrant {
        _deadline(deadline);
        _active(id);
        Position storage p = positions[id];
        if (!_isHome(p) || IZZZNFT(access.module(Ids.NFT)).ownerOf(id) != msg.sender) revert Unauthorized();
        PoolConfig memory c = _pool(id);
        if (!c.depositsEnabled || amount0 + amount1 == 0 || minimumLiquidity == 0) revert InvalidAmount();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        uint256 valueUSD = oracle.value(c.key.currency0, amount0) + oracle.value(c.key.currency1, amount1);
        if (valueUSD < c.minDepositUSD || p.depositUSD + valueUSD > c.maxPositionUSD) revert InvalidAmount();
        _harvest(id, deadline); // Old LP fees cannot be silently reinvested by v4.
        ExactToken.pull(c.key.currency0, msg.sender, amount0);
        ExactToken.pull(c.key.currency1, msg.sender, amount1);
        _idle(id, p.idle0 + amount0, p.idle1 + amount1);
        uint256 beforeValue = _idleValue(id);
        _balanceUsing(id, deadline, true);
        // A balancing swap can earn additional fees for the pre-existing LP.
        _harvest(id, deadline);
        if (_idleValue(id) < Math.mulDiv(beforeValue, 10000 - c.maxSlippageBps, 10000)) revert Slippage();
        _put(id, false, minimumLiquidity, deadline);
        p.depositUSD += valueUSD;
        IZZZPower(access.module(Ids.POWER)).add(id, valueUSD);
        emit LiquidityAdded(id, amount0, amount1);
    }
    function _allocate(uint256 id, address token, uint256 amount) private {
        if (amount == 0) return;
        address fees = access.module(Ids.FEES);
        IERC20(token).forceApprove(fees, amount);
        IZZZFees(fees).allocate(id, token, amount);
        IERC20(token).forceApprove(fees, 0);
    }
    function _harvest(uint256 id, uint256 deadline) private {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        uint256 before0 = IERC20(c.key.currency0).balanceOf(address(this));
        uint256 before1 = IERC20(c.key.currency1).balanceOf(address(this));
        IZZZLiquidity(access.module(Ids.LIQUIDITY)).collect(p.poolId, p.lpTokenId, deadline);
        uint256 fee0 = IERC20(c.key.currency0).balanceOf(address(this)) - before0;
        uint256 fee1 = IERC20(c.key.currency1).balanceOf(address(this)) - before1;
        _allocate(id, c.key.currency0, fee0);
        _allocate(id, c.key.currency1, fee1);
        emit FeesCollected(id, fee0, fee1);
    }
    function collectFees(uint256 id, uint256 deadline) external live nonReentrant {
        _deadline(deadline);
        _active(id);
        _harvest(id, deadline);
    }
    function _pullCompound(uint256 id) private returns (uint256 amount0, uint256 amount1) {
        PoolConfig memory c = _pool(id);
        Position storage p = positions[id];
        IZZZFees fees = IZZZFees(access.module(Ids.FEES));
        amount0 = fees.releaseCompound(id, c.key.currency0);
        amount1 = fees.releaseCompound(id, c.key.currency1);
        _idle(id, p.idle0 + amount0, p.idle1 + amount1);
    }
    function compound(uint256 id, uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.COMPOUNDER) live nonReentrant {
        _deadline(deadline);
        _active(id);
        _harvest(id, deadline);
        (uint256 amount0, uint256 amount1) = _pullCompound(id);
        if (amount0 + amount1 == 0 || minimumLiquidity == 0) revert InvalidAmount();
        uint256 beforeValue = _idleValue(id);
        _balanceUsing(id, deadline, true);
        // A same-pool swap can itself generate fees for this still-active LP.
        // Settle them separately before INCREASE so they cannot become principal.
        _harvest(id, deadline);
        if (_idleValue(id) < Math.mulDiv(beforeValue, 10000 - _pool(id).maxSlippageBps, 10000)) revert Slippage();
        _put(id, false, minimumLiquidity, deadline);
        emit Compounded(id, amount0, amount1);
    }
    function _close(uint256 id, uint256 deadline) private {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        uint256 before0 = IERC20(c.key.currency0).balanceOf(address(this));
        uint256 before1 = IERC20(c.key.currency1).balanceOf(address(this));
        IZZZLiquidity(access.module(Ids.LIQUIDITY)).close(p.poolId, p.lpTokenId, deadline);
        p.lpTokenId = 0;
        _idle(id, p.idle0 + IERC20(c.key.currency0).balanceOf(address(this)) - before0,
            p.idle1 + IERC20(c.key.currency1).balanceOf(address(this)) - before1);
    }
    function _balance(uint256 id, uint256 deadline) private { _balanceUsing(id, deadline, false); }
    function _balanceUsing(uint256 id, uint256 deadline, bool existingRange) private {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        IZZZStrategy strategy = IZZZStrategy(access.module(Ids.STRATEGY));
        bool zeroForOne;
        uint256 amountIn;
        uint256 minimumOut;
        if (existingRange) (zeroForOne, amountIn, minimumOut) = strategy.compoundPlan(id, p.idle0, p.idle1);
        else (zeroForOne, amountIn, minimumOut) = strategy.swapPlan(p.poolId, p.idle0, p.idle1);
        if (amountIn == 0) return;
        address input = zeroForOne ? c.key.currency0 : c.key.currency1;
        address manager = access.module(Ids.LIQUIDITY);
        IERC20(input).forceApprove(manager, amountIn);
        uint256 amountOut = IZZZLiquidity(manager).swap(p.poolId, zeroForOne, amountIn, minimumOut, deadline);
        IERC20(input).forceApprove(manager, 0);
        if (zeroForOne) _idle(id, p.idle0 - amountIn, p.idle1 + amountOut);
        else _idle(id, p.idle0 + amountOut, p.idle1 - amountIn);
    }
    function _idleValue(uint256 id) private view returns (uint256) {
        PoolConfig memory c = _pool(id);
        Position storage p = positions[id];
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        return oracle.value(c.key.currency0, p.idle0) + oracle.value(c.key.currency1, p.idle1);
    }
    function rebalance(uint256 id, uint128 minimumLiquidity, uint256 deadline) external onlyKeeper live nonReentrant {
        _deadline(deadline);
        _active(id);
        if (minimumLiquidity == 0 || !IZZZStrategy(access.module(Ids.STRATEGY)).needsRebalance(id)) revert InvalidState();
        Position storage p = positions[id];
        IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(p.poolId);
        uint256 oldId = p.lpTokenId;
        _harvest(id, deadline);
        _pullCompound(id);
        _close(id, deadline);
        uint256 beforeValue = _idleValue(id);
        _balance(id, deadline);
        if (_idleValue(id) < Math.mulDiv(beforeValue, 10000 - _pool(id).maxSlippageBps, 10000)) revert Slippage();
        _put(id, true, minimumLiquidity, deadline);
        emit Rebalanced(id, oldId, p.lpTokenId, p.centerX96);
    }
    function releaseForMigration(uint256 id, bytes32 migrationId, uint256 deadline)
        external onlyModule(Ids.MIGRATION) live nonReentrant returns (uint256 amount0, uint256 amount1) {
        _deadline(deadline);
        _active(id);
        Position storage p = positions[id];
        // v2 supports canonical -> satellite only; no silent onward migration.
        if (!_isHome(p)) revert InvalidState();
        IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(p.poolId);
        _harvest(id, deadline);
        _pullCompound(id);
        _close(id, deadline);
        PoolConfig memory c = _pool(id);
        amount0 = p.idle0;
        amount1 = p.idle1;
        _idle(id, 0, 0);
        p.status = PositionStatus.Outbound;
        IZZZFees(access.module(Ids.FEES)).flushDust(id, c.key.currency0);
        IZZZFees(access.module(Ids.FEES)).flushDust(id, c.key.currency1);
        ExactToken.push(c.key.currency0, msg.sender, amount0);
        ExactToken.push(c.key.currency1, msg.sender, amount1);
        emit PrincipalBridged(id, migrationId, amount0, amount1);
    }
    function importPending(uint256 id, bytes32 poolId, Position calldata origin, uint256 amount0, uint256 amount1)
        external onlyModule(Ids.RECEIVER) nonReentrant {
        if (positions[id].status != PositionStatus.None || origin.homeChain != canonicalChainId || origin.homeChain == block.chainid ||
            origin.homeVault == address(0) || origin.homeReceiver == address(0)) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        Position storage p = positions[id];
        p.poolId = poolId;
        p.homeChain = origin.homeChain;
        p.homeVault = origin.homeVault;
        p.homeReceiver = origin.homeReceiver;
        p.homeToken0 = origin.homeToken0;
        p.homeToken1 = origin.homeToken1;
        p.depositUSD = origin.depositUSD;
        p.locationChain = block.chainid;
        p.locationVault = address(this);
        p.status = PositionStatus.Inbound;
        ExactToken.pull(c.key.currency0, msg.sender, amount0);
        ExactToken.pull(c.key.currency1, msg.sender, amount1);
        _idle(id, amount0, amount1);
        emit ImportPending(id, p.homeChain, p.homeVault);
    }
    function finalizeImport(uint256 id, uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.RECEIVER) live nonReentrant {
        _deadline(deadline);
        if (positions[id].status != PositionStatus.Inbound || minimumLiquidity == 0) revert InvalidState();
        uint256 beforeValue = _idleValue(id);
        _balance(id, deadline);
        if (_idleValue(id) < Math.mulDiv(beforeValue, 10000 - _pool(id).maxSlippageBps, 10000)) revert Slippage();
        _put(id, true, minimumLiquidity, deadline);
        positions[id].status = PositionStatus.Active;
        emit ImportFinalized(id, positions[id].lpTokenId);
    }
    function confirmMigration(uint256 id, uint256 destinationChain, address destinationVault)
        external onlyModule(Ids.MIGRATION) {
        Position storage p = positions[id];
        if (p.status != PositionStatus.Outbound) revert InvalidState();
        p.status = PositionStatus.Remote;
        p.locationChain = destinationChain;
        p.locationVault = destinationVault;
        emit LocationConfirmed(id, destinationChain, destinationVault);
    }

    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.MIGRATION) live nonReentrant {
        _deadline(deadline);
        _active(id);
        Position storage p = positions[id];
        PoolConfig memory oldConfig = _pool(id);
        PoolConfig memory nextConfig = IZZZPools(access.module(Ids.POOLS)).get(newPool);
        if (p.poolId == newPool || minimumLiquidity == 0 || oldConfig.key.currency0 != nextConfig.key.currency0 ||
            oldConfig.key.currency1 != nextConfig.key.currency1 || !nextConfig.operationsEnabled) revert InvalidConfiguration();
        IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(p.poolId);
        uint256 oldId = p.lpTokenId;
        _harvest(id, deadline);
        _pullCompound(id);
        _close(id, deadline);
        uint256 beforeValue = _idleValue(id);
        p.poolId = newPool;
        _balance(id, deadline);
        if (_idleValue(id) < Math.mulDiv(beforeValue, 10000 - nextConfig.maxSlippageBps, 10000)) revert Slippage();
        _put(id, true, minimumLiquidity, deadline);
        emit Rebalanced(id, oldId, p.lpTokenId, p.centerX96);
    }
    function onERC721Received(address, address, uint256, bytes calldata) external view override returns (bytes4) {
        address manager = access.module(Ids.LIQUIDITY);
        if (manager == address(0) || msg.sender != IZZZLiquidity(manager).positionManager()) revert Unauthorized();
        return IERC721Receiver.onERC721Received.selector;
    }
    // No withdraw, rescue-token, arbitrary execution, proxy upgrade or admin NFT transfer.
}
