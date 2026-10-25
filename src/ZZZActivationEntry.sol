// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZActivationAssets} from "./ZZZActivationAssets.sol";
import {IZZZNFT, IZZZPools, IZZZOracle} from "./interfaces/IZZZ.sol";
import {Ids, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {ZZZContributionPricing} from "./ZZZContributionPricing.sol";
import {ZZZV4RouteExecutor} from "./ZZZV4RouteExecutor.sol";

interface IActivationVault {
    function activate(uint256, bytes32, uint256, uint256, uint128, uint256) external payable;
    function increase(uint256, uint256, uint256, uint128, uint256) external payable;
}
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
    /// @notice Signed contribution policy: no legacy unbounded entry fallback.
    uint256 public constant REVIEW_POLICY_VERSION = 1;
    address public immutable registry;
    ZZZActivationAssets public immutable activationAssets;
    ZZZV4RouteExecutor public immutable v4Executor;
    address private nativeSender;
    uint256 private nativeReceived;

    struct Request {
        uint256 nftId;
        bytes32 poolId;
        address sourceAsset; // Zero is native ETH, distinct from every ERC20.
        uint256 amountIn;
        bytes32 routeId; // Zero means a direct accounting currency.
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
    mapping(bytes32 => bool) private v3RouteExists;
    mapping(bytes32 => bool) private v3RouteEnabled;
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
        v4Executor = new ZZZV4RouteExecutor();
    }
    receive() external payable {
        if (nativeSender == address(0) || msg.sender != nativeSender) revert Unauthorized();
        nativeReceived += msg.value;
    }

    /// @notice Policy identity and contents never change. Review hash is provenance,
    /// not a claim that an independent security audit has occurred.
    function addRoute(RoutePolicy calldata policy) external onlyGovernance operating nonReentrant returns (bytes32 id) {
        _checkRoute(policy);
        id = keccak256(abi.encode(policy));
        if (routeExists(id)) revert InvalidConfiguration();
        routes[id] = policy;
        v3RouteExists[id] = true;
        v3RouteEnabled[id] = true;
        emit RouteRecorded(id, policy.source, policy.output, policy.router, policy.pool, policy.fee, policy.reviewHash);
        emit RouteEnabled(id, true);
    }
    function route(bytes32 id) external view returns (RoutePolicy memory) {
        if (!v3RouteExists[id]) revert InvalidConfiguration();
        return routes[id];
    }
    /// @notice 0 unknown, 1 legacy typed v3, 2 typed hookless v4. Never reinterpret a v3 policy.
    function routeKind(bytes32 id) public view returns (uint8) {
        if (v3RouteExists[id]) return 1;
        return v4Executor.routeExists(id) ? 2 : 0;
    }
    function routeExists(bytes32 id) public view returns (bool) { return routeKind(id) != 0; }
    function routeEnabled(bytes32 id) public view returns (bool) {
        return v3RouteExists[id] ? v3RouteEnabled[id] : v4Executor.routeEnabled(id);
    }
    function addV4Route(ZZZV4RouteExecutor.Policy calldata policy)
        external onlyGovernance operating nonReentrant returns (bytes32 id) {
        id = v4Executor.addRoute(policy);
        if (v3RouteExists[id]) revert InvalidConfiguration();
        emit RouteEnabled(id, true);
    }
    function v4Route(bytes32 id) external view returns (ZZZV4RouteExecutor.Policy memory) {
        return v4Executor.route(id);
    }
    /// @notice Disabling requires no call to a failing token, router or pool.
    function setRouteEnabled(bytes32 id, bool enabled) external onlyGovernance operating nonReentrant {
        if (v3RouteExists[id]) {
            if (enabled) _checkRoute(routes[id]);
            v3RouteEnabled[id] = enabled;
        } else {
            v4Executor.setRouteEnabled(id, enabled);
        }
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

    function _pricing() private view returns(ZZZContributionPricing) {
        return ZZZContributionPricing(IZZZOracle(access.module(Ids.ORACLE)).contributionPricing());
    }
    /// @notice The fixed pricing companion may adopt only this exact live Vault context.
    function pricingContext(uint256 id,bytes32 pool,uint256 packed,uint256 gross) external view returns(bool) {
        if (msg.sender != address(_pricing())) revert Unauthorized();
        Context memory c = context;
        return c.owner != address(0) && c.nftId == id && c.poolId == pool && c.grossUSD == gross &&
            c.amount0 <= type(uint128).max && c.amount1 <= type(uint128).max &&
            packed == (c.amount0 | (c.amount1 << 128)) && _owner(id) == c.owner;
    }

    function _convertV4(Request calldata r, address output, uint256 sourceBaseline, uint256 outputBaseline)
        private returns (uint256 acquired) {
        ExactAsset.approve(r.sourceAsset,address(v4Executor),r.amountIn);
        nativeReceived = 0;
        nativeSender = output == address(0) ? address(v4Executor) : address(0);
        acquired = v4Executor.execute{value:r.sourceAsset == address(0) ? r.amountIn : 0}(
            r.routeId,r.amountIn,r.minimumOut,r.deadline);
        nativeSender = address(0);
        ExactAsset.approve(r.sourceAsset,address(v4Executor),0);
        if (acquired < r.minimumOut || (output == address(0) && nativeReceived != acquired) ||
            ExactAsset.balance(r.sourceAsset,address(this)) != sourceBaseline ||
            ExactAsset.balance(output,address(this)) != outputBaseline+acquired) revert InvalidState();
        nativeReceived = 0;
    }

    /// @notice Retired selector. Old reviews cannot silently use a newer governed cap.
    function execute(Request calldata) external payable { revert InvalidState(); }

    /// @notice The signed maximum includes conversion and placement loss; gas is separate.
    /// A tighter execution-time policy is allowed, but never a wider one than reviewed.
    function executeReviewed(Request calldata request, uint16 maximumLossBps)
        external payable live operating nonReentrant {
        _deadline(request.deadline);
        address vault = _vault();
        if (request.amountIn == 0 || request.minimumLiquidity == 0 || _owner(request.nftId) != msg.sender) revert Unauthorized();
        PoolConfig memory pool = IZZZPools(registry).accounting(request.poolId);
        if (!pool.depositsEnabled || !pool.operationsEnabled ||
            pool.key.currency0 == pool.key.currency1) revert InvalidConfiguration();
        address source = request.sourceAsset;
        address output;
        RoutePolicy memory policy;
        uint8 kind;
        if (msg.value != (source == address(0) ? request.amountIn : 0)) revert InvalidAmount();
        if (request.routeId == bytes32(0)) {
            if (request.minimumOut != 0) revert InvalidAmount();
            output = source;
        } else {
            kind = routeKind(request.routeId);
            if (!routeEnabled(request.routeId) || request.minimumOut == 0) revert InvalidConfiguration();
            if (kind == 2) {
                ZZZV4RouteExecutor.Policy memory v4 = v4Executor.validate(request.routeId);
                if (v4.source != source) revert InvalidConfiguration();
                output = v4.output;
            } else {
                if (kind != 1 || source == address(0)) revert InvalidConfiguration();
                policy = routes[request.routeId];
                if (policy.source != source) revert InvalidConfiguration();
                _checkRoute(policy);
                output = policy.output;
            }
        }
        if (output != pool.key.currency0 && output != pool.key.currency1) revert InvalidConfiguration();
        uint256 nativeBaseline = address(this).balance - msg.value;
        uint256 sourceBaseline = ExactAsset.balance(source,address(this)) - (source == address(0) ? msg.value : 0);
        uint256 outputBaseline = ExactAsset.balance(output,address(this)) - (output == address(0) ? msg.value : 0);
        // Admit and freeze source + LP-pair prices BEFORE a token pull, approval
        // or conversion can call external code. Both bounds come from two sources.
        uint256 grossUSD = activationAssets.value(source, request.amountIn);
        if (_pricing().beginEntryReviewed(request.nftId,request.poolId,source,request.amountIn,maximumLossBps) != grossUSD) revert InvalidState();
        if (source != address(0)) ExactToken.pull(source, msg.sender, request.amountIn);
        if (grossUSD == 0 || (!request.increase && grossUSD < 100e18) ||
            (request.increase && grossUSD < 5e18)) revert InvalidAmount();
        uint256 acquired = request.amountIn;
        if (kind == 2) {
            acquired = _convertV4(request,output,sourceBaseline,outputBaseline);
        } else if (kind == 1) {
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
        ExactAsset.approve(output,vault, acquired);
        if (_owner(request.nftId) != msg.sender) revert Unauthorized();
        context = Context(msg.sender, request.nftId, keccak256(payload), request.poolId, amount0, amount1, grossUSD);
        (bool success, bytes memory result) = vault.call{value: output == address(0) ? acquired : 0}(payload);
        if (!success) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
        delete context;
        ExactAsset.approve(output,vault, 0);
        if (_owner(request.nftId) != msg.sender || ExactAsset.balance(output,address(this)) != outputBaseline ||
            ExactAsset.balance(source,address(this)) != sourceBaseline || address(this).balance != nativeBaseline) revert InvalidState();
        _pricing().endEntry();
        emit SourceContributed(msg.sender, request.nftId, request.poolId, request.sourceAsset,
            request.amountIn, grossUSD, output, acquired, request.increase);
    }
}
