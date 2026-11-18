// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {PoolKey} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {IPoolManagerMinimal, IStateViewMinimal} from "./interfaces/IZZZ.sol";

/// @notice One parent's fixed-recipient, single-hop v4 conversion executor.
/// The immutable parent enforces governance, lifecycle and economic floors.
/// Conversion markets are separate from the Registry's NFT principal pools.
/// There is no arbitrary calldata, hook, recipient, approval or rescue surface.
contract ZZZV4RouteExecutor is ReentrancyGuard {
    struct Policy {
        address source;
        address output;
        PoolKey key;
        address poolManager;
        address stateView;
        bytes32 sourceCodeHash;
        bytes32 outputCodeHash;
        bytes32 poolManagerCodeHash;
        bytes32 stateViewCodeHash;
        bytes32 reviewHash;
    }
    address public immutable parent;
    bytes32 public constant NATIVE_ASSET_CODE_HASH = keccak256("ZZZ_NATIVE_ETH_V1");
    bytes32 public constant ROUTE_DOMAIN = keccak256("ZZZ_TYPED_V4_ROUTE_V1");
    mapping(bytes32 => Policy) private policies;
    mapping(bytes32 => bool) public routeExists;
    mapping(bytes32 => bool) public routeEnabled;
    bytes32 private pendingHash;
    address private pendingManager;
    address private nativeSender;
    uint256 private nativeReceived;
    error Unauthorized();
    error InvalidConfiguration();
    error InvalidAmount();
    error InvalidState();
    error Slippage();
    error Expired();
    event RouteRecorded(bytes32 indexed id, address indexed source, address indexed output, bytes32 reviewHash);
    event RouteEnabled(bytes32 indexed id, bool enabled);
    event Executed(bytes32 indexed id, uint256 input, uint256 output);

    constructor() { parent = msg.sender; }
    modifier onlyParent() { if (msg.sender != parent) revert Unauthorized(); _; }
    receive() external payable {
        if (msg.sender != nativeSender || nativeSender == address(0)) revert Unauthorized();
        nativeReceived += msg.value;
    }

    function addRoute(Policy calldata policy) external onlyParent nonReentrant returns (bytes32 id) {
        _check(policy); id = _id(policy);
        if (routeExists[id]) revert InvalidConfiguration();
        policies[id] = policy; routeExists[id] = true; routeEnabled[id] = true;
        emit RouteRecorded(id, policy.source, policy.output, policy.reviewHash); emit RouteEnabled(id, true);
    }
    /// @notice Stopping a route does not query its external dependencies.
    function setRouteEnabled(bytes32 id, bool enabled) external onlyParent nonReentrant {
        if (!routeExists[id]) revert InvalidConfiguration();
        if (enabled) { if (_id(policies[id]) != id) revert InvalidConfiguration(); _check(policies[id]); }
        routeEnabled[id] = enabled; emit RouteEnabled(id, enabled);
    }
    function route(bytes32 id) external view returns (Policy memory) {
        if (!routeExists[id]) revert InvalidConfiguration(); return policies[id];
    }
    function validate(bytes32 id) external view returns (Policy memory) { return _validated(id); }
    function _validated(bytes32 id) private view returns (Policy memory p) {
        if (!routeExists[id] || !routeEnabled[id]) revert InvalidConfiguration();
        p = policies[id];
        if (_id(p) != id) revert InvalidConfiguration();
        _check(p);
    }
    function _id(Policy memory p) private view returns (bytes32) {
        return keccak256(abi.encode(ROUTE_DOMAIN, block.chainid, address(this), parent, p));
    }
    function _pin(address target, bytes32 codeHash) private view {
        if (target == address(0) || codeHash == bytes32(0) || target.code.length == 0 || target.codehash != codeHash)
            revert InvalidConfiguration();
    }
    function _asset(address asset, bytes32 codeHash) private view {
        if (asset == address(0)) { if (codeHash != NATIVE_ASSET_CODE_HASH) revert InvalidConfiguration(); }
        else _pin(asset, codeHash);
    }
    function _check(Policy memory p) private view {
        PoolKey memory k = p.key;
        if (p.source == p.output || k.currency0 >= k.currency1 || k.hooks != address(0) ||
            k.fee >= 1000000 || k.tickSpacing < 1 || k.tickSpacing > 32767 || p.reviewHash == bytes32(0) ||
            !((p.source == k.currency0 && p.output == k.currency1) ||
                (p.source == k.currency1 && p.output == k.currency0))) revert InvalidConfiguration();
        _asset(p.source, p.sourceCodeHash); _asset(p.output, p.outputCodeHash);
        _pin(p.poolManager, p.poolManagerCodeHash); _pin(p.stateView, p.stateViewCodeHash);
        IStateViewMinimal view_ = IStateViewMinimal(p.stateView);
        if (view_.poolManager() != p.poolManager) revert InvalidConfiguration();
        (uint160 price,,, uint24 lpFee) = view_.getSlot0(keccak256(abi.encode(k)));
        if (price < TickMath.MIN_SQRT_PRICE || price >= TickMath.MAX_SQRT_PRICE || lpFee != k.fee)
            revert InvalidConfiguration();
    }

    function execute(bytes32 id, uint256 amountIn, uint256 minimumOut, uint256 deadline)
        external payable onlyParent nonReentrant returns (uint256 amountOut) {
        if (deadline < block.timestamp || deadline > block.timestamp + 10 minutes) revert Expired();
        if (amountIn == 0 || amountIn > uint256(uint128(type(int128).max)) || minimumOut == 0 ||
            minimumOut > uint256(uint128(type(int128).max))) revert InvalidAmount();
        Policy memory p = _validated(id);
        if (msg.value != (p.source == address(0) ? amountIn : 0)) revert InvalidAmount();
        uint256 nativeBefore = address(this).balance - msg.value;
        uint256 sourceBefore = ExactAsset.balance(p.source, address(this)) - msg.value;
        uint256 outputBefore = ExactAsset.balance(p.output, address(this));
        if (p.source != address(0)) ExactToken.pull(p.source, parent, amountIn);
        // An ERC20 callback cannot inject ETH and disguise it as swap output,
        // or let prefunded ETH subsidize the exact declared native budget.
        if (address(this).balance != nativeBefore + msg.value) revert InvalidState();
        bytes memory payload = abi.encode(p.key, p.source, p.output, amountIn, minimumOut);
        pendingHash = keccak256(payload); pendingManager = p.poolManager;
        amountOut = abi.decode(IPoolManagerMinimal(p.poolManager).unlock(payload), (uint256));
        if (pendingHash != bytes32(0) || pendingManager != address(0) || nativeSender != address(0) ||
            nativeReceived != 0 || amountOut < minimumOut ||
            ExactAsset.balance(p.source, address(this)) != sourceBefore ||
            ExactAsset.balance(p.output, address(this)) != outputBefore + amountOut ||
            address(this).balance != nativeBefore + (p.output == address(0) ? amountOut : 0)) revert InvalidState();
        _check(p);
        uint256 parentBefore = ExactAsset.balance(p.output, parent);
        ExactAsset.push(p.output, parent, amountOut);
        if (ExactAsset.balance(p.source, address(this)) != sourceBefore ||
            ExactAsset.balance(p.output, address(this)) != outputBefore || address(this).balance != nativeBefore ||
            ExactAsset.balance(p.output, parent) != parentBefore + amountOut) revert InvalidState();
        _check(p);
        emit Executed(id, amountIn, amountOut);
    }

    function unlockCallback(bytes calldata payload) external returns (bytes memory) {
        if (msg.sender != pendingManager || pendingHash == bytes32(0) || pendingHash != keccak256(payload))
            revert Unauthorized();
        pendingHash = bytes32(0); pendingManager = address(0);
        (PoolKey memory key, address source, address output, uint256 amountIn, uint256 minimumOut) =
            abi.decode(payload, (PoolKey, address, address, uint256, uint256));
        IPoolManagerMinimal manager = IPoolManagerMinimal(msg.sender);
        bool zeroForOne = source == key.currency0;
        int256 delta = manager.swap(key, IPoolManagerMinimal.SwapParams(zeroForOne, -int256(amountIn),
            zeroForOne ? TickMath.MIN_SQRT_PRICE + 1 : TickMath.MAX_SQRT_PRICE - 1), bytes(""));
        int128 delta0 = int128(delta >> 128); int128 delta1 = int128(uint128(uint256(delta)));
        int128 inputDelta = zeroForOne ? delta0 : delta1;
        int128 outputDelta = zeroForOne ? delta1 : delta0;
        if (inputDelta >= 0 || outputDelta <= 0 || uint256(-int256(inputDelta)) != amountIn ||
            uint256(int256(outputDelta)) < minimumOut) revert Slippage();
        manager.sync(source);
        if (source == address(0)) {
            if (manager.settle{value: amountIn}() != amountIn) revert InvalidState();
        } else {
            ExactToken.push(source, msg.sender, amountIn);
            if (manager.settle() != amountIn) revert InvalidState();
        }
        uint256 amountOut = uint256(int256(outputDelta));
        uint256 beforeOutput = ExactAsset.balance(output, address(this));
        if (output == address(0)) { nativeSender = msg.sender; nativeReceived = 0; }
        manager.take(output, address(this), amountOut);
        if (output == address(0)) {
            if (nativeReceived != amountOut) revert InvalidState();
            nativeSender = address(0); nativeReceived = 0;
        }
        if (ExactAsset.balance(output, address(this)) != beforeOutput + amountOut) revert InvalidState();
        return abi.encode(amountOut);
    }
}
