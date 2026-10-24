// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZOracle} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ZZZV4RouteExecutor} from "./ZZZV4RouteExecutor.sol";
import {IActivationV3Router, IActivationV3Factory, IActivationV3Pool} from "./ZZZActivationEntry.sol";

interface IRoyaltyWrapper { function withdraw(uint256 amount) external; }
interface IRoyaltyProxyAdmin {
    function owner() external view returns (address);
    function getProxyAdmin(address proxy) external view returns (address);
    function getProxyImplementation(address proxy) external view returns (address);
}

/// @notice Fixed royalty-only executor. Exact input from one bound ledger, exact
/// native output to that same ledger; no arbitrary calls, recipient or rescue.
/// Governance admits reviewed dependencies, not tickers. Runtime pins alone do
/// not detect all proxy upgrades: token/router admission still requires review.
contract ZZZRoyaltyConverter is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    uint256 public constant MAX_LOSS_BPS = 1000;
    uint16 public conversionLossBps = 100;
    address public immutable ledger;
    address public immutable wrapper;
    ZZZV4RouteExecutor public immutable v4Executor;
    address private nativeSender;
    struct WrapperPolicy {
        bytes32 codeHash;
        address admin;
        address implementation;
        address adminOwner;
        bytes32 adminCodeHash;
        bytes32 implementationCodeHash;
        bytes32 reviewHash;
    }
    struct RoutePolicy {
        address source;
        address router;
        address factory;
        address pool;
        uint24 fee;
        bytes32 sourceCodeHash;
        bytes32 routerCodeHash;
        bytes32 factoryCodeHash;
        bytes32 poolCodeHash;
        bytes32 reviewHash;
    }
    WrapperPolicy public wrapperPolicy;
    bool public enabled;
    mapping(bytes32 => RoutePolicy) private routes;
    mapping(bytes32 => bool) private v3RouteExists;
    mapping(bytes32 => bool) private v3RouteEnabled;
    event WrapperConfigured(bytes32 indexed policyHash, bytes32 reviewHash);
    event Enabled(bool enabled);
    event RouteRecorded(bytes32 indexed routeId, address indexed source, bytes32 reviewHash);
    event RouteEnabled(bytes32 indexed routeId, bool enabled);
    event V4RouteRecorded(bytes32 indexed routeId, address indexed source, bytes32 reviewHash);
    event Converted(address indexed source, bytes32 indexed routeId, uint256 input, uint256 nativeOutput);
    event ConversionLossLimitChanged(uint16 previous, uint16 current);

    constructor(address controller, address receiver, address wrappedETH) ZZZModule(controller) {
        if (receiver.code.length == 0 || (wrappedETH != address(0) && wrappedETH.code.length == 0)) revert InvalidConfiguration();
        ledger = receiver; wrapper = wrappedETH;
        v4Executor = new ZZZV4RouteExecutor();
    }
    receive() external payable {
        if (nativeSender == address(0) || msg.sender != nativeSender) revert Unauthorized();
    }

    function configureWrapper(WrapperPolicy calldata policy) external onlyGovernance operating nonReentrant {
        _checkWrapper(policy);
        wrapperPolicy = policy;
        emit WrapperConfigured(keccak256(abi.encode(policy)), policy.reviewHash);
    }
    /// @notice Dependency-independent global stop/reopen. Each operation validates
    /// its own dependencies; an unused wrapper cannot stop native v4 conversion.
    function setEnabled(bool value) external onlyGovernance operating nonReentrant {
        enabled = value; emit Enabled(value);
    }
    /// @notice Immediate bounded execution policy; never changes earned balances
    /// or permits the caller to weaken a stronger submitted minimum.
    function setConversionLossBps(uint16 value) external onlyGovernance operating nonReentrant {
        if (value > MAX_LOSS_BPS) revert InvalidConfiguration();
        uint16 previous = conversionLossBps;
        conversionLossBps = value;
        emit ConversionLossLimitChanged(previous, value);
    }
    function addRoute(RoutePolicy calldata policy) external onlyGovernance operating nonReentrant returns (bytes32 id) {
        _checkRoute(policy);
        id = keccak256(abi.encode(policy));
        if (routeExists(id)) revert InvalidConfiguration();
        routes[id] = policy; v3RouteExists[id] = true; v3RouteEnabled[id] = true;
        emit RouteRecorded(id, policy.source, policy.reviewHash); emit RouteEnabled(id, true);
    }
    function route(bytes32 id) external view returns (RoutePolicy memory) {
        if (!v3RouteExists[id]) revert InvalidConfiguration(); return routes[id];
    }
    function addV4Route(ZZZV4RouteExecutor.Policy calldata policy)
        external onlyGovernance operating nonReentrant returns (bytes32 id) {
        if (policy.source == address(0) || policy.output != address(0)) revert InvalidConfiguration();
        id = v4Executor.addRoute(policy);
        if (v3RouteExists[id]) revert InvalidConfiguration();
        emit V4RouteRecorded(id, policy.source, policy.reviewHash);
        emit RouteEnabled(id, true);
    }
    function v4Route(bytes32 id) external view returns (ZZZV4RouteExecutor.Policy memory) {
        return v4Executor.route(id);
    }
    function routeKind(bytes32 id) public view returns (uint8) {
        return v3RouteExists[id] ? 1 : v4Executor.routeExists(id) ? 2 : 0;
    }
    function routeExists(bytes32 id) public view returns (bool) { return routeKind(id) != 0; }
    function routeEnabled(bytes32 id) public view returns (bool) {
        return v3RouteExists[id] ? v3RouteEnabled[id] : v4Executor.routeEnabled(id);
    }
    function setRouteEnabled(bytes32 id, bool value) external onlyGovernance operating nonReentrant {
        uint8 kind = routeKind(id);
        if (kind == 0) revert InvalidConfiguration();
        if (kind == 1) {
            if (value) _checkRoute(routes[id]);
            v3RouteEnabled[id] = value;
        } else v4Executor.setRouteEnabled(id, value);
        emit RouteEnabled(id, value);
    }
    function _pin(address target, bytes32 hash) private view {
        if (hash == bytes32(0) || target.code.length == 0 || target.codehash != hash) revert InvalidConfiguration();
    }
    function _checkWrapper(WrapperPolicy memory p) private view {
        _pin(wrapper, p.codeHash);
        if (p.reviewHash == bytes32(0)) revert InvalidConfiguration();
        if (p.admin == address(0)) {
            if (p.implementation != address(0) || p.adminOwner != address(0) ||
                p.adminCodeHash != bytes32(0) || p.implementationCodeHash != bytes32(0)) revert InvalidConfiguration();
        } else {
            _pin(p.admin, p.adminCodeHash); _pin(p.implementation, p.implementationCodeHash);
            IRoyaltyProxyAdmin admin = IRoyaltyProxyAdmin(p.admin);
            if (admin.owner() != p.adminOwner || admin.getProxyAdmin(wrapper) != p.admin ||
                admin.getProxyImplementation(wrapper) != p.implementation) revert InvalidConfiguration();
        }
    }
    function _checkRoute(RoutePolicy memory p) private view {
        if (wrapper == address(0) || p.source == wrapper || p.reviewHash == bytes32(0) || p.fee >= 1_000_000) revert InvalidConfiguration();
        _pin(p.source, p.sourceCodeHash); _pin(p.router, p.routerCodeHash);
        _pin(p.factory, p.factoryCodeHash); _pin(p.pool, p.poolCodeHash);
        address a = p.source < wrapper ? p.source : wrapper;
        address b = p.source < wrapper ? wrapper : p.source;
        if (IActivationV3Router(p.router).factory() != p.factory ||
            IActivationV3Factory(p.factory).getPool(p.source, wrapper, p.fee) != p.pool ||
            IActivationV3Pool(p.pool).factory() != p.factory || IActivationV3Pool(p.pool).token0() != a ||
            IActivationV3Pool(p.pool).token1() != b || IActivationV3Pool(p.pool).fee() != p.fee) revert InvalidConfiguration();
    }

    function convert(address source, uint256 amount, bytes32 routeId, uint256 minimumETH, uint256 deadline)
        external live operating nonReentrant returns (uint256 output) {
        if (msg.sender != ledger || !enabled) revert Unauthorized();
        _deadline(deadline);
        if (source == address(0) || amount == 0 || minimumETH == 0) revert InvalidAmount();
        if (routeKind(routeId) == 2) return _convertV4(source, amount, routeId, minimumETH, deadline);
        if (wrapper == address(0)) revert InvalidConfiguration();
        _checkWrapper(wrapperPolicy);
        RoutePolicy memory p;
        uint256 floor = amount;
        if (source == wrapper) {
            if (routeId != bytes32(0)) revert InvalidConfiguration();
        } else {
            if (!v3RouteEnabled[routeId]) revert InvalidConfiguration();
            p = routes[routeId];
            if (p.source != source) revert InvalidConfiguration();
            _checkRoute(p);
            uint256 expected = IZZZOracle(access.module(Ids.ORACLE)).quote(source, wrapper, amount);
            if (expected == 0) revert InvalidAmount();
            floor = Math.mulDiv(expected, 10_000 - conversionLossBps, 10_000, Math.Rounding.Ceil);
        }
        uint256 minimum = Math.max(floor, minimumETH);
        uint256 sourceBefore = IERC20(source).balanceOf(address(this));
        uint256 wrappedBefore = IERC20(wrapper).balanceOf(address(this));
        uint256 nativeBefore = address(this).balance;
        ExactToken.pull(source, ledger, amount);
        output = amount;
        if (source != wrapper) {
            IERC20(source).forceApprove(p.router, amount);
            output = IActivationV3Router(p.router).exactInputSingle(IActivationV3Router.ExactInputSingleParams(
                source, wrapper, p.fee, address(this), amount, minimum, 0));
            IERC20(source).forceApprove(p.router, 0);
            if (IERC20(source).balanceOf(address(this)) != sourceBefore ||
                IERC20(wrapper).balanceOf(address(this)) != wrappedBefore + output) revert InvalidState();
            _checkRoute(p);
        }
        if (output < minimum) revert Slippage();
        nativeSender = wrapper;
        IRoyaltyWrapper(wrapper).withdraw(output);
        nativeSender = address(0);
        _checkWrapper(wrapperPolicy);
        if (IERC20(wrapper).balanceOf(address(this)) != wrappedBefore ||
            address(this).balance != nativeBefore + output) revert InvalidState();
        (bool ok,) = payable(ledger).call{value: output}("");
        if (!ok || address(this).balance != nativeBefore) revert InvalidState();
        emit Converted(source, routeId, amount, output);
    }

    function _convertV4(address source, uint256 amount, bytes32 routeId, uint256 minimumETH, uint256 deadline)
        private returns (uint256 output) {
        ZZZV4RouteExecutor.Policy memory p = v4Executor.validate(routeId);
        if (p.source != source || p.output != address(0)) revert InvalidConfiguration();
        uint256 expected = IZZZOracle(access.module(Ids.ORACLE)).quote(source, address(0), amount);
        if (expected == 0) revert InvalidAmount();
        uint256 minimum = Math.max(minimumETH,
            Math.mulDiv(expected, 10_000 - conversionLossBps, 10_000, Math.Rounding.Ceil));
        uint256 sourceBefore = IERC20(source).balanceOf(address(this));
        uint256 nativeBefore = address(this).balance;
        ExactToken.pull(source, ledger, amount);
        IERC20(source).forceApprove(address(v4Executor), amount);
        nativeSender = address(v4Executor);
        output = v4Executor.execute(routeId, amount, minimum, deadline);
        nativeSender = address(0);
        IERC20(source).forceApprove(address(v4Executor), 0);
        if (output < minimum || IERC20(source).balanceOf(address(this)) != sourceBefore ||
            address(this).balance != nativeBefore + output) revert InvalidState();
        (bool ok,) = payable(ledger).call{value: output}("");
        if (!ok || address(this).balance != nativeBefore ||
            IERC20(source).balanceOf(address(this)) != sourceBefore) revert InvalidState();
        emit Converted(source, routeId, amount, output);
    }
}
