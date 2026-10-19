// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZActivationAssets} from "./ZZZActivationAssets.sol";
import {IZZZNFT, IZZZPools} from "./interfaces/IZZZ.sol";
import {Ids, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";

interface IActivationVault {
    function activate(uint256, bytes32, uint256, uint256, uint128, uint256) external;
    function increase(uint256, uint256, uint256, uint128, uint256) external;
}
interface IActivationWrapper { function deposit() external payable; }
interface IActivationV3Factory { function getPool(address, address, uint24) external view returns (address); }
interface IActivationV3Pool {
    function factory() external view returns (address);
    function token0() external view returns (address);
    function token1() external view returns (address);
    function fee() external view returns (uint24);
}
/// @dev SwapRouter02's deadline-free single-hop tuple. Entry checks its own deadline.
interface IActivationV3Router {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    function factory() external view returns (address);
    function exactInputSingle(ExactInputSingleParams calldata) external payable returns (uint256);
}

/// @notice Atomic owner-funded source conversion into the permanent LP Vault.
/// The Registry creates this immutable child. No arbitrary executor, recipient,
/// user-supplied USD value, NFT custody, permit or token rescue path exists.
contract ZZZActivationEntry is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    address public immutable registry;
    ZZZActivationAssets public immutable activationAssets;

    struct Request {
        uint256 nftId;
        bytes32 poolId;
        address sourceAsset; // Zero means native ETH, normalized to this native pool's wrapper.
        uint256 amountIn;
        bytes32 routeId; // Zero means direct accounting currency or exact native wrapping.
        uint256 minimumOut;
        uint128 minimumLiquidity;
        uint256 deadline;
        bool increase;
    }
    struct RoutePolicy {
        address source;
        address output;
        address router;
        address factory;
        address pool;
        uint24 fee;
        bytes32 routerCodeHash;
        bytes32 factoryCodeHash;
        bytes32 poolCodeHash;
        bytes32 sourceCodeHash;
        bytes32 outputCodeHash;
        bytes32 reviewHash;
    }
    struct Context {
        address owner;
        uint256 nftId;
        bytes32 callHash;
        bytes32 poolId;
        uint256 amount0;
        uint256 amount1;
        uint256 grossUSD;
    }
    mapping(bytes32 => RoutePolicy) private routes;
    mapping(bytes32 => bool) public routeExists;
    mapping(bytes32 => bool) public routeEnabled;
    Context private context;
    event RouteRecorded(bytes32 indexed id, address indexed source, address indexed output,
        address router, address pool, uint24 fee, bytes32 reviewHash);
    event RouteEnabled(bytes32 indexed id, bool enabled);
    event SourceContributed(address indexed owner, uint256 indexed nftId, bytes32 indexed poolId,
        address sourceAsset, uint256 sourceAmount, uint256 grossUSD, address output, uint256 outputAmount, bool increase);

    constructor(address controller, address poolRegistry, address assets) ZZZModule(controller) {
        if (poolRegistry == address(0) || msg.sender != poolRegistry || assets.code.length == 0 ||
            ZZZActivationAssets(assets).registry() != poolRegistry ||
            address(ZZZActivationAssets(assets).access()) != controller) revert InvalidConfiguration();
        registry = poolRegistry;
        activationAssets = ZZZActivationAssets(assets);
    }

    /// @notice Policy identity and contents never change. Review hash is provenance,
    /// not a claim that an independent security audit has occurred.
    function addRoute(RoutePolicy calldata policy) external onlyGovernance returns (bytes32 id) {
        _checkRoute(policy);
        id = keccak256(abi.encode(policy));
        if (routeExists[id]) revert InvalidConfiguration();
        routes[id] = policy;
        routeExists[id] = true;
        routeEnabled[id] = true;
        emit RouteRecorded(id, policy.source, policy.output, policy.router, policy.pool, policy.fee, policy.reviewHash);
        emit RouteEnabled(id, true);
    }
    function route(bytes32 id) external view returns (RoutePolicy memory) {
        if (!routeExists[id]) revert InvalidConfiguration();
        return routes[id];
    }
    /// @notice Disabling requires no call to a failing token, router or pool.
    function setRouteEnabled(bytes32 id, bool enabled) external onlyGovernance {
        if (!routeExists[id]) revert InvalidConfiguration();
        if (enabled) _checkRoute(routes[id]);
        routeEnabled[id] = enabled;
        emit RouteEnabled(id, enabled);
    }
    function _pin(address target, bytes32 expected) private view {
        if (expected == bytes32(0) || target.code.length == 0 || target.codehash != expected) revert InvalidConfiguration();
    }
    function _checkRoute(RoutePolicy memory p) private view {
        if (p.source == address(0) || p.output == address(0) || p.source == p.output ||
            p.reviewHash == bytes32(0) || p.fee >= 1_000_000) revert InvalidConfiguration();
        _pin(p.source, p.sourceCodeHash); _pin(p.output, p.outputCodeHash);
        _pin(p.router, p.routerCodeHash); _pin(p.factory, p.factoryCodeHash); _pin(p.pool, p.poolCodeHash);
        address a = p.source < p.output ? p.source : p.output;
        address b = p.source < p.output ? p.output : p.source;
        if (IActivationV3Router(p.router).factory() != p.factory ||
            IActivationV3Factory(p.factory).getPool(p.source, p.output, p.fee) != p.pool ||
            IActivationV3Pool(p.pool).factory() != p.factory || IActivationV3Pool(p.pool).token0() != a ||
            IActivationV3Pool(p.pool).token1() != b || IActivationV3Pool(p.pool).fee() != p.fee) revert InvalidConfiguration();
    }
    function _owner(uint256 id) private view returns (address) {
        return IZZZNFT(access.module(Ids.NFT)).ownerOf(id);
    }
    function _vault() private view returns (address vault) {
        vault = access.module(Ids.VAULT);
        if (!access.isSealed() || access.module(Ids.POOLS) != registry || vault.code.length == 0) revert InvalidConfiguration();
    }

    /// @notice Only the canonical Vault may authorize this exact active call.
    /// ERC721 token/operator approval is never contribution authority.
    function validateOwner(uint256 id, bytes32 vaultCallHash) external view {
        Context memory c = context;
        if (msg.sender != _vault() || c.owner == address(0) || c.nftId != id ||
            c.callHash != vaultCallHash || _owner(id) != c.owner) revert Unauthorized();
    }
    /// @notice Only Registry valuation may replace pair-input value with the
    /// original, proven source value. An active mismatch MUST NOT fall back.
    function sourceValue(bytes32 poolId, uint256 amount0, uint256 amount1) external view returns (uint256) {
        if (msg.sender != registry) revert Unauthorized();
        Context memory c = context;
        if (c.owner == address(0)) return 0;
        if (c.poolId != poolId || c.amount0 != amount0 || c.amount1 != amount1 ||
            _owner(c.nftId) != c.owner) revert InvalidState();
        return c.grossUSD;
    }

    function execute(Request calldata request) external payable live operating nonReentrant {
        _deadline(request.deadline);
        address vault = _vault();
        if (request.amountIn == 0 || request.minimumLiquidity == 0 || _owner(request.nftId) != msg.sender) revert Unauthorized();
        PoolConfig memory pool = IZZZPools(registry).accounting(request.poolId);
        if (!pool.depositsEnabled || !pool.operationsEnabled || pool.key.currency0 == address(0) ||
            pool.key.currency0 == pool.key.currency1) revert InvalidConfiguration();
        address source = request.sourceAsset;
        address output;
        RoutePolicy memory policy;
        if (source == address(0)) {
            if (msg.value != request.amountIn || request.routeId != bytes32(0) || request.minimumOut != 0 ||
                IZZZPools(registry).get(request.poolId).key.currency0 != address(0)) revert InvalidAmount();
            source = pool.key.currency0;
            output = source;
        } else {
            if (msg.value != 0) revert InvalidAmount();
            if (request.routeId == bytes32(0)) {
                if (request.minimumOut != 0) revert InvalidAmount();
                output = source;
            } else {
                if (!routeEnabled[request.routeId]) revert InvalidConfiguration();
                policy = routes[request.routeId];
                if (policy.source != source || request.minimumOut == 0) revert InvalidConfiguration();
                _checkRoute(policy);
                output = policy.output;
            }
        }
        if (output != pool.key.currency0 && output != pool.key.currency1) revert InvalidConfiguration();
        uint256 nativeBaseline = address(this).balance - msg.value;
        uint256 sourceBaseline = IERC20(source).balanceOf(address(this));
        uint256 outputBaseline = IERC20(output).balanceOf(address(this));
        if (request.sourceAsset == address(0)) {
            IActivationWrapper(source).deposit{value: request.amountIn}();
            if (address(this).balance != nativeBaseline ||
                IERC20(source).balanceOf(address(this)) != sourceBaseline + request.amountIn) revert InvalidState();
        } else ExactToken.pull(source, msg.sender, request.amountIn);
        // Values the real original amount; an assumed stable peg or supplied USD
        // claim cannot relax the Vault's single 99% end-to-end execution budget.
        uint256 grossUSD = activationAssets.value(source, request.amountIn);
        if (grossUSD == 0 || (!request.increase && grossUSD < 100e18) ||
            (request.increase && grossUSD < 5e18)) revert InvalidAmount();
        uint256 acquired = request.amountIn;
        if (request.routeId != bytes32(0)) {
            IERC20(source).forceApprove(policy.router, request.amountIn);
            acquired = IActivationV3Router(policy.router).exactInputSingle(IActivationV3Router.ExactInputSingleParams(
                source, output, policy.fee, address(this), request.amountIn, request.minimumOut, 0));
            IERC20(source).forceApprove(policy.router, 0);
            if (acquired < request.minimumOut || IERC20(source).balanceOf(address(this)) != sourceBaseline ||
                IERC20(output).balanceOf(address(this)) != outputBaseline + acquired) revert InvalidState();
        }
        if (_owner(request.nftId) != msg.sender) revert Unauthorized();
        uint256 amount0 = output == pool.key.currency0 ? acquired : 0;
        uint256 amount1 = output == pool.key.currency1 ? acquired : 0;
        bytes memory payload = request.increase
            ? abi.encodeCall(IActivationVault.increase, (request.nftId, amount0, amount1, request.minimumLiquidity, request.deadline))
            : abi.encodeCall(IActivationVault.activate, (request.nftId, request.poolId, amount0, amount1, request.minimumLiquidity, request.deadline));
        // Token approval can call arbitrary token code. Context must remain
        // inactive until the immediate Vault call, whose own guard then protects
        // contribution valuation against unrelated callback-driven joins.
        IERC20(output).forceApprove(vault, acquired);
        if (_owner(request.nftId) != msg.sender) revert Unauthorized();
        context = Context(msg.sender, request.nftId, keccak256(payload), request.poolId, amount0, amount1, grossUSD);
        (bool success, bytes memory result) = vault.call(payload);
        if (!success) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
        delete context;
        IERC20(output).forceApprove(vault, 0);
        if (_owner(request.nftId) != msg.sender || IERC20(output).balanceOf(address(this)) != outputBaseline ||
            IERC20(source).balanceOf(address(this)) != sourceBaseline || address(this).balance != nativeBaseline) revert InvalidState();
        emit SourceContributed(msg.sender, request.nftId, request.poolId, request.sourceAsset,
            request.amountIn, grossUSD, output, acquired, request.increase);
    }
}
