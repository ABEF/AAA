// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {BalanceDelta, BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {ZZZV4RouteExecutor} from "../src/ZZZV4RouteExecutor.sol";
import {PoolKey} from "../src/libraries/ZZZTypes.sol";
import {IPoolManagerMinimal} from "../src/interfaces/IZZZ.sol";

contract V4RouteForcedETH { constructor(address payable recipient) payable { selfdestruct(recipient); } }
contract V4RouteToken is ERC20 {
    address private forceTarget;
    constructor() ERC20("V4 route fixture", "VRF") {}
    function mint(address recipient, uint256 amount) external { _mint(recipient, amount); }
    function forceOnTransferTo(address target) external { forceTarget = target; }
    function _update(address from, address to, uint256 amount) internal override {
        super._update(from, to, amount);
        if (from != address(0) && to == forceTarget) new V4RouteForcedETH{value: 1}(payable(to));
    }
}

/// @dev TEST ONLY. Deliberately adversarial settlement behavior, never a venue
/// qualification. Installed PoolManager is used separately for real swap math.
contract V4RouteFaultCore {
    uint8 public mode;
    address private input;
    address private output;
    uint256 private debt;
    uint256 private credit;
    address private synced;
    uint256 private syncedBalance;
    bytes private payload;
    bool public replaySucceeded;
    bytes public replayResult;
    receive() external payable {}
    function setMode(uint8 value) external { mode = value; }
    function unlock(bytes calldata data) external returns (bytes memory) {
        payload = data; synced = address(0xDEAD);
        if (mode == 8) return abi.encode(uint256(1));
        bytes memory result = ZZZV4RouteExecutor(payable(msg.sender)).unlockCallback(data);
        require(debt == 0 && credit == 0, "dirty remaining delta"); return result;
    }
    function swap(PoolKey calldata key, IPoolManagerMinimal.SwapParams calldata params, bytes calldata hookData)
        external returns (int256 delta) {
        require(hookData.length == 0); uint256 amount = uint256(-params.amountSpecified);
        if (mode == 1) --amount;
        input = params.zeroForOne ? key.currency0 : key.currency1;
        output = params.zeroForOne ? key.currency1 : key.currency0;
        debt = amount; credit = amount * 99 / 100;
        int128 inDelta = mode == 5 ? int128(uint128(amount)) : -int128(uint128(amount));
        int128 a = params.zeroForOne ? inDelta : int128(uint128(credit));
        int128 b = params.zeroForOne ? int128(uint128(credit)) : inDelta;
        if (mode == 6) (replaySucceeded, replayResult) = msg.sender.call(abi.encodeWithSignature("unlockCallback(bytes)", payload));
        return (int256(a) << 128) | int256(uint256(uint128(b)));
    }
    function sync(address asset) external {
        synced = asset; if (asset != address(0)) syncedBalance = IERC20(asset).balanceOf(address(this));
    }
    function settle() external payable returns (uint256 paid) {
        require(synced == input, "wrong synced currency");
        paid = input == address(0) ? msg.value : IERC20(input).balanceOf(address(this)) - syncedBalance;
        require(paid == debt); debt = 0; if (mode == 2) --paid;
    }
    function take(address asset, address recipient, uint256 amount) external {
        require(asset == output && amount == credit); credit = 0;
        uint256 actual = mode == 3 ? amount - 1 : mode == 7 ? amount + 1 : amount;
        if (asset == address(0)) {
            (bool ok,) = recipient.call{value: actual}(""); require(ok);
            if (mode == 4) new V4RouteForcedETH{value: 1}(payable(recipient));
        } else require(IERC20(asset).transfer(recipient, actual));
    }
}
contract V4RouteFaultState {
    address public immutable poolManager;
    constructor(address core) { poolManager = core; }
    function getSlot0(bytes32) external pure returns (uint160, int24, uint24, uint24) {
        return (uint160(1 << 96), 0, 0, 3000);
    }
}

/// @notice Actual installed v4 core/state-view settlement plus focused hostile
/// fixtures. No production provider, price feed, route or public funds are used.
contract TypedV4ExecutorTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    PoolManager private core;
    StateView private state;
    ZZZV4RouteExecutor private executor;
    V4RouteToken private tokenA;
    V4RouteToken private tokenB;
    PoolKey private nativeKey;
    PoolKey private tokenKey;
    bytes32 private activeRoute;
    bool private rejectNative;
    bool private reenter;
    bool private reentrySucceeded;
    bytes private reentryResult;
    address private constant OUTSIDER = address(0xBAD);

    receive() external payable {
        require(!rejectNative, "parent rejects ETH");
        if (reenter) (reentrySucceeded, reentryResult) = address(executor).call(
            abi.encodeCall(executor.setRouteEnabled, (activeRoute, false)));
    }
    function setUp() public {
        vm.warp(1_000_000); vm.deal(address(this), 100000 ether);
        core = new PoolManager(address(this)); state = new StateView(IPoolManager(address(core)));
        tokenA = new V4RouteToken(); tokenB = new V4RouteToken(); executor = new ZZZV4RouteExecutor();
        tokenA.mint(address(this), 100000 ether); tokenB.mint(address(this), 100000 ether);
        nativeKey = PoolKey(address(0), address(tokenA), 3000, 60, address(0));
        tokenKey = address(tokenA) < address(tokenB)
            ? PoolKey(address(tokenA), address(tokenB), 3000, 60, address(0))
            : PoolKey(address(tokenB), address(tokenA), 3000, 60, address(0));
        _initialize(nativeKey, -60000, 60000, 10000 ether);
        _initialize(tokenKey, -60000, 60000, 10000 ether);
    }
    function _coreKey(PoolKey memory key) private pure returns (CoreKey memory) {
        return CoreKey(Currency.wrap(key.currency0), Currency.wrap(key.currency1), key.fee, key.tickSpacing, IHooks(key.hooks));
    }
    function _initialize(PoolKey memory key, int24 lower, int24 upper, int256 liquidity) private {
        core.initialize(_coreKey(key), uint160(1 << 96));
        core.unlock(abi.encode(key, lower, upper, liquidity));
    }
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == address(core));
        (PoolKey memory key, int24 lower, int24 upper, int256 liquidity) = abi.decode(data, (PoolKey, int24, int24, int256));
        (BalanceDelta delta,) = core.modifyLiquidity(_coreKey(key), ModifyLiquidityParams(lower, upper, liquidity, bytes32(0)), "");
        _pay(key.currency0, delta.amount0()); _pay(key.currency1, delta.amount1()); return "";
    }
    function _pay(address asset, int128 delta) private {
        if (delta == 0) return; require(delta < 0); uint256 amount = uint256(-int256(delta));
        core.sync(Currency.wrap(asset));
        if (asset == address(0)) assertEq(core.settle{value: amount}(), amount);
        else { require(IERC20(asset).transfer(address(core), amount)); assertEq(core.settle(), amount); }
    }
    function _policy(PoolKey memory key, address source, address output) private view returns (ZZZV4RouteExecutor.Policy memory p) {
        p.source = source; p.output = output; p.key = key; p.poolManager = address(core); p.stateView = address(state);
        p.sourceCodeHash = source == address(0) ? executor.NATIVE_ASSET_CODE_HASH() : source.codehash;
        p.outputCodeHash = output == address(0) ? executor.NATIVE_ASSET_CODE_HASH() : output.codehash;
        p.poolManagerCodeHash = address(core).codehash; p.stateViewCodeHash = address(state).codehash;
        p.reviewHash = keccak256("explicit deterministic fixture review");
    }
    function _route(PoolKey memory key, address source, address output) private returns (bytes32) {
        return executor.addRoute(_policy(key, source, output));
    }
    function _price(PoolKey memory key) private view returns (uint160 p) {
        (p,,,) = state.getSlot0(PoolId.wrap(keccak256(abi.encode(key))));
    }
    function _prefund() private {
        new V4RouteForcedETH{value: 123}(payable(address(executor)));
        tokenA.mint(address(executor), 456); tokenB.mint(address(executor), 789);
    }
    function _assertPrefunds() private view {
        assertEq(address(executor).balance, 123); assertEq(tokenA.balanceOf(address(executor)), 456);
        assertEq(tokenB.balanceOf(address(executor)), 789);
        assertEq(tokenA.allowance(address(executor), address(core)), 0); assertEq(tokenB.allowance(address(executor), address(core)), 0);
    }

    function testActualCoreNativeBothDirectionsPreserveAllPrefundsAndExactTransfers() public {
        _prefund(); bytes32 toNative = _route(nativeKey, address(tokenA), address(0));
        uint256 beforeETH = address(this).balance; uint256 beforeToken = tokenA.balanceOf(address(this));
        tokenA.approve(address(executor), 1 ether);
        uint256 out = executor.execute(toNative, 1 ether, 0.99 ether, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH + out); assertEq(tokenA.balanceOf(address(this)), beforeToken - 1 ether);
        assertEq(tokenA.allowance(address(this), address(executor)), 0); _assertPrefunds();
        bytes32 fromNative = _route(nativeKey, address(0), address(tokenA));
        beforeETH = address(this).balance; beforeToken = tokenA.balanceOf(address(this));
        out = executor.execute{value: 1 ether}(fromNative, 1 ether, 0.99 ether, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH - 1 ether); assertEq(tokenA.balanceOf(address(this)), beforeToken + out);
        _assertPrefunds();
    }
    function testActualCoreERC20BothDirectionsAndDirtySyncBeforeNativeSettlement() public {
        _prefund(); bytes32 aToB = _route(tokenKey, address(tokenA), address(tokenB));
        tokenA.approve(address(executor), 1 ether); uint256 beforeB = tokenB.balanceOf(address(this));
        uint256 out = executor.execute(aToB, 1 ether, 0.99 ether, block.timestamp + 100);
        assertEq(tokenB.balanceOf(address(this)), beforeB + out); _assertPrefunds();
        bytes32 bToA = _route(tokenKey, address(tokenB), address(tokenA));
        tokenB.approve(address(executor), 1 ether); uint256 beforeA = tokenA.balanceOf(address(this));
        out = executor.execute(bToA, 1 ether, 0.99 ether, block.timestamp + 100);
        assertEq(tokenA.balanceOf(address(this)), beforeA + out); _assertPrefunds();
        core.sync(Currency.wrap(address(tokenB)));
        bytes32 fromNative = _route(nativeKey, address(0), address(tokenA));
        out = executor.execute{value: 1 ether}(fromNative, 1 ether, 0.99 ether, block.timestamp + 100);
        assertGt(out, 0); _assertPrefunds();
    }
    function testActualCorePartialFillRevertsAllMarketAndCallerState() public {
        PoolKey memory narrow = PoolKey(address(0), address(tokenA), 500, 10, address(0));
        _initialize(narrow, -60, 60, 10 ether); bytes32 id = _route(narrow, address(0), address(tokenA)); _prefund();
        uint256 beforeETH = address(this).balance; uint256 beforeCore = address(core).balance;
        uint256 beforeToken = tokenA.balanceOf(address(this)); uint256 beforeCoreToken = tokenA.balanceOf(address(core));
        vm.expectRevert(ZZZV4RouteExecutor.Slippage.selector);
        executor.execute{value: 1 ether}(id, 1 ether, 1, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH); assertEq(address(core).balance, beforeCore);
        assertEq(tokenA.balanceOf(address(this)), beforeToken); assertEq(tokenA.balanceOf(address(core)), beforeCoreToken);
        assertEq(_price(narrow), uint160(1 << 96)); _assertPrefunds();
    }
    function testPolicyAdmissionRejectsAmbiguousNativeHooksDynamicFeesAndWrongIdentities() public {
        ZZZV4RouteExecutor.Policy memory good = _policy(nativeKey, address(0), address(tokenA));
        for (uint256 i; i < 13; ++i) {
            ZZZV4RouteExecutor.Policy memory bad = _policy(nativeKey, address(0), address(tokenA));
            if (i == 0) bad.sourceCodeHash = bytes32(0);
            if (i == 1) bad.key.hooks = address(1);
            if (i == 2) bad.key.fee = 0x800000;
            if (i == 3) bad.key.fee = 1000000;
            if (i == 4) bad.key.tickSpacing = 0;
            if (i == 5) bad.key.tickSpacing = 32768;
            if (i == 6) bad.output = bad.source;
            if (i == 7) bad.source = address(tokenB);
            if (i == 8) bad.key.currency0 = bad.key.currency1;
            if (i == 9) bad.poolManagerCodeHash = bytes32(uint256(1));
            if (i == 10) bad.stateViewCodeHash = bytes32(0);
            if (i == 11) bad.reviewHash = bytes32(0);
            if (i == 12) bad.key.fee = 4000;
            vm.expectRevert(ZZZV4RouteExecutor.InvalidConfiguration.selector); executor.addRoute(bad);
        }
        StateView wrong = new StateView(IPoolManager(address(new PoolManager(address(this)))));
        good.stateView = address(wrong); good.stateViewCodeHash = address(wrong).codehash;
        vm.expectRevert(ZZZV4RouteExecutor.InvalidConfiguration.selector); executor.addRoute(good);
    }
    function testParentAuthorityRouteDomainAndNoUnauthenticatedNativeOrCallback() public {
        ZZZV4RouteExecutor.Policy memory p = _policy(nativeKey, address(0), address(tokenA));
        vm.prank(OUTSIDER); vm.expectRevert(ZZZV4RouteExecutor.Unauthorized.selector); executor.addRoute(p);
        bytes32 id = executor.addRoute(p);
        assertEq(id, keccak256(abi.encode(executor.ROUTE_DOMAIN(), block.chainid, address(executor), address(this), p)));
        assertEq(executor.parent(), address(this)); assertTrue(executor.routeExists(id)); assertTrue(executor.routeEnabled(id));
        assertEq(keccak256(abi.encode(executor.route(id))), keccak256(abi.encode(p)));
        ZZZV4RouteExecutor second = new ZZZV4RouteExecutor(); assertNotEq(second.addRoute(p), id);
        vm.prank(OUTSIDER); vm.expectRevert(ZZZV4RouteExecutor.Unauthorized.selector); executor.setRouteEnabled(id, false);
        vm.prank(OUTSIDER); vm.expectRevert(ZZZV4RouteExecutor.Unauthorized.selector); executor.execute(id, 1, 1, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.Unauthorized.selector); executor.unlockCallback("");
        vm.prank(address(core)); vm.expectRevert(ZZZV4RouteExecutor.Unauthorized.selector); executor.unlockCallback("");
        (bool ok,) = address(executor).call{value: 1}(""); assertFalse(ok);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidConfiguration.selector); executor.addRoute(p);
        vm.chainId(block.chainid + 1); vm.expectRevert(ZZZV4RouteExecutor.InvalidConfiguration.selector); executor.validate(id);
    }
    function testDisableWithoutDependenciesAndReenableRequiresFreshPins() public {
        bytes32 id = _route(nativeKey, address(0), address(tokenA)); bytes memory original = address(state).code;
        vm.etch(address(state), hex"00"); executor.setRouteEnabled(id, false); assertFalse(executor.routeEnabled(id));
        assertEq(executor.route(id).output, address(tokenA));
        vm.expectRevert(ZZZV4RouteExecutor.InvalidConfiguration.selector); executor.validate(id);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidConfiguration.selector); executor.setRouteEnabled(id, true);
        vm.etch(address(state), original); executor.setRouteEnabled(id, true); executor.validate(id);
        uint256 beforeETH = address(this).balance; vm.etch(address(core), hex"00");
        vm.expectRevert(ZZZV4RouteExecutor.InvalidConfiguration.selector);
        executor.execute{value: 1 ether}(id, 1 ether, 1, block.timestamp);
        assertEq(address(this).balance, beforeETH);
    }
    function testExactValueSignedBoundsAndDeadlinesCannotSpendPrefunds() public {
        _prefund(); bytes32 nativeId = _route(nativeKey, address(0), address(tokenA));
        bytes32 tokenId = _route(nativeKey, address(tokenA), address(0)); tokenA.approve(address(executor), 1 ether);
        uint256 beforeETH = address(this).balance; uint256 beforeA = tokenA.balanceOf(address(this));
        vm.expectRevert(ZZZV4RouteExecutor.InvalidAmount.selector); executor.execute(nativeId, 1 ether, 1, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidAmount.selector); executor.execute{value: 1 ether + 1}(nativeId, 1 ether, 1, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidAmount.selector); executor.execute{value: 1}(tokenId, 1 ether, 1, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidAmount.selector); executor.execute(tokenId, 0, 1, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidAmount.selector); executor.execute(tokenId, 1, 0, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidAmount.selector); executor.execute(tokenId, uint256(uint128(type(int128).max)) + 1, 1, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.InvalidAmount.selector); executor.execute(tokenId, 1, uint256(uint128(type(int128).max)) + 1, block.timestamp);
        vm.expectRevert(ZZZV4RouteExecutor.Expired.selector); executor.execute(tokenId, 1, 1, block.timestamp - 1);
        vm.expectRevert(ZZZV4RouteExecutor.Expired.selector); executor.execute(tokenId, 1, 1, block.timestamp + 601);
        assertEq(address(this).balance, beforeETH); assertEq(tokenA.balanceOf(address(this)), beforeA); _assertPrefunds();
    }
    function testRejectedNativeParentRollsBackActualSwapAndAllBalances() public {
        bytes32 id = _route(nativeKey, address(tokenA), address(0)); _prefund(); tokenA.approve(address(executor), 1 ether);
        uint256 beforeETH = address(this).balance; uint256 beforeA = tokenA.balanceOf(address(this));
        uint256 beforeCore = address(core).balance; rejectNative = true;
        vm.expectRevert(); executor.execute(id, 1 ether, 0.99 ether, block.timestamp);
        assertEq(address(this).balance, beforeETH); assertEq(tokenA.balanceOf(address(this)), beforeA);
        assertEq(address(core).balance, beforeCore); assertEq(_price(nativeKey), uint160(1 << 96)); _assertPrefunds();
    }
    function testParentCannotReenterRouteMutationWhileNativeOutputIsDelivered() public {
        activeRoute = _route(nativeKey, address(tokenA), address(0)); tokenA.approve(address(executor), 1 ether); reenter = true;
        assertGt(executor.execute(activeRoute, 1 ether, 0.99 ether, block.timestamp), 0);
        assertFalse(reentrySucceeded); assertTrue(executor.routeEnabled(activeRoute));
        assertEq(reentryResult, abi.encodeWithSelector(ReentrancyGuard.ReentrancyGuardReentrantCall.selector));
    }
    function testForcedETHDuringERC20PullOrActualCoreOutputCannotAlterAccounting() public {
        _prefund(); vm.deal(address(tokenA), 1); tokenA.forceOnTransferTo(address(executor));
        bytes32 fromToken = _route(nativeKey, address(tokenA), address(0));
        bytes32 toToken = _route(nativeKey, address(0), address(tokenA)); tokenA.approve(address(executor), 1 ether);
        uint256 beforeETH = address(this).balance; uint256 beforeA = tokenA.balanceOf(address(this));
        vm.expectRevert(ZZZV4RouteExecutor.InvalidState.selector); executor.execute(fromToken, 1 ether, 1, block.timestamp);
        assertEq(address(this).balance, beforeETH); assertEq(tokenA.balanceOf(address(this)), beforeA); _assertPrefunds();
        vm.expectRevert(ZZZV4RouteExecutor.InvalidState.selector);
        executor.execute{value: 1 ether}(toToken, 1 ether, 1, block.timestamp);
        assertEq(address(this).balance, beforeETH); assertEq(tokenA.balanceOf(address(this)), beforeA);
        assertEq(address(tokenA).balance, 1); assertEq(_price(nativeKey), uint160(1 << 96)); _assertPrefunds();
    }
    function _faultPolicy(V4RouteFaultCore fault, V4RouteFaultState view_, address source, address output)
        private view returns (ZZZV4RouteExecutor.Policy memory p) {
        p = _policy(nativeKey, source, output); p.poolManager = address(fault); p.stateView = address(view_);
        p.poolManagerCodeHash = address(fault).codehash; p.stateViewCodeHash = address(view_).codehash;
    }
    function testFaultCorePartialDirtyDeltaShortSettleAndFalseNativeCreditsRevertAtomically() public {
        V4RouteFaultCore fault = new V4RouteFaultCore(); V4RouteFaultState view_ = new V4RouteFaultState(address(fault));
        vm.deal(address(fault), 100 ether); tokenA.mint(address(fault), 100 ether); _prefund();
        bytes32 id = executor.addRoute(_faultPolicy(fault, view_, address(tokenA), address(0)));
        tokenA.approve(address(executor), 1 ether); uint256 beforeA = tokenA.balanceOf(address(this));
        uint256 beforeETH = address(this).balance;
        for (uint8 mode = 1; mode <= 8; ++mode) {
            if (mode == 6) continue;
            fault.setMode(mode); vm.expectRevert(); executor.execute(id, 1 ether, 0.99 ether, block.timestamp);
            assertEq(tokenA.balanceOf(address(this)), beforeA); assertEq(address(this).balance, beforeETH);
            assertEq(address(fault).balance, 100 ether); assertEq(tokenA.balanceOf(address(fault)), 100 ether); _assertPrefunds();
        }
        fault.setMode(6); assertEq(executor.execute(id, 1 ether, 0.99 ether, block.timestamp), 0.99 ether);
        assertFalse(fault.replaySucceeded()); assertEq(fault.replayResult(), abi.encodeWithSelector(ZZZV4RouteExecutor.Unauthorized.selector));
        _assertPrefunds();
    }
    function testFaultCoreDirtySyncStillSettlesNativeWithNoWrapperOrLPRegistry() public {
        V4RouteFaultCore fault = new V4RouteFaultCore(); V4RouteFaultState view_ = new V4RouteFaultState(address(fault));
        tokenA.mint(address(fault), 100 ether); _prefund();
        bytes32 id = executor.addRoute(_faultPolicy(fault, view_, address(0), address(tokenA)));
        uint256 beforeA = tokenA.balanceOf(address(this));
        assertEq(executor.execute{value: 1 ether}(id, 1 ether, 0.99 ether, block.timestamp), 0.99 ether);
        assertEq(tokenA.balanceOf(address(this)), beforeA + 0.99 ether); _assertPrefunds();
    }
}
