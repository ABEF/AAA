// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {LiquidityAmounts} from "@uniswap/v4-periphery/src/libraries/LiquidityAmounts.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {IPoolManagerMinimal} from "../src/interfaces/IZZZ.sol";
import {MockAccess, MockToken} from "./mocks/Mocks.sol";
import {FakePermit2, FakeState, FakePolicy} from "./LiquidityEncoding.t.sol";

/// @dev Fake settlement tests only. Actual selected-market tests are in NativePoolFork.t.sol.
contract BoundaryWETH is ERC20 {
    bool public brokenWithdraw;
    bool public brokenDeposit;
    bool public reenter;
    address public target;
    constructor() ERC20("Boundary wrapped ETH", "BWETH") {}
    function failures(bool withdraw_, bool deposit_) external { brokenWithdraw = withdraw_; brokenDeposit = deposit_; }
    function reentry(address target_) external { target = target_; reenter = true; }
    function deposit() external payable {
        if (!brokenDeposit) _mint(msg.sender, msg.value);
        if (reenter) {
            (bool ok,) = target.call(abi.encodeWithSignature("collect(bytes32,uint256,uint256)", bytes32(0), 1, block.timestamp));
            require(!ok, "reentry succeeded");
        }
    }
    function withdraw(uint256 amount) external {
        _burn(msg.sender, amount);
        uint256 sent = brokenWithdraw ? amount - 1 : amount;
        (bool ok,) = msg.sender.call{value: sent}(""); require(ok);
    }
}

contract BoundaryPools {
    PoolConfig private config;
    address public wrapper;
    constructor(PoolConfig memory c, address w) { config = c; wrapper = w; }
    function get(bytes32) external view returns (PoolConfig memory) { return config; }
    function accounting(bytes32) external view returns (PoolConfig memory c) { c = config; c.key.currency0 = wrapper; }
    function nativeAsset(bytes32) external view returns (address) { return wrapper; }
    function setWrapper(address w) external { wrapper = w; }
    function setKey(PoolKey memory key) external { config.key = key; }
    function setStrategyPolicy() external { config.rangeBps = 1000; config.maxSpotDeviationBps = 100; }
    function disableOperations() external { config.operationsEnabled = false; config.depositsEnabled = false; }
}

contract BoundaryOracle {
    function quote(address, address, uint256 amount) external pure returns (uint256) { return amount; }
    function value(address, uint256 amount) external pure returns (uint256) { return amount; }
    function price(address) external pure returns (uint256) { return 1e18; }
    function tokenDecimals(address) external pure returns (uint8) { return 18; }
    function referenceX96(address, address) external pure returns (uint160) { return uint160(1 << 96); }
}
contract BoundaryUnavailableOracle { fallback() external { revert("oracle unavailable"); } }

contract BoundaryCore {
    address public synced;
    address public input;
    address public output;
    address public positions;
    uint256 public debt;
    uint256 public credit;
    uint256 private balanceAtSync;
    bool public partialFill;
    bool public forceDuringTake;
    function setPositions(address p) external { require(positions == address(0)); positions = p; }
    function setPartial(bool on) external { partialFill = on; }
    function forceTake(bool on) external { forceDuringTake = on; }
    receive() external payable {}
    function unlock(bytes calldata data) external returns (bytes memory result) {
        // Deliberately leave a dirty ERC20 sync before native debt is settled.
        synced = address(0xDEAD);
        result = ZZZLiquidityManager(payable(msg.sender)).unlockCallback(data);
        require(debt == 0 && credit == 0, "unsettled delta");
    }
    function swap(PoolKey calldata key, IPoolManagerMinimal.SwapParams calldata params, bytes calldata)
        external returns (int256 delta) {
        uint256 n = uint256(-params.amountSpecified);
        if (partialFill) n -= 1;
        input = params.zeroForOne ? key.currency0 : key.currency1;
        output = params.zeroForOne ? key.currency1 : key.currency0;
        debt = n;
        credit = n * 99 / 100; // Fake net execution output, not actual selected-pool math.
        int128 d0 = params.zeroForOne ? -int128(uint128(n)) : int128(uint128(credit));
        int128 d1 = params.zeroForOne ? int128(uint128(credit)) : -int128(uint128(n));
        delta = (int256(d0) << 128) | int256(uint256(uint128(d1)));
    }
    function sync(address token) external {
        synced = token;
        if (token != address(0)) balanceAtSync = IERC20(token).balanceOf(address(this));
    }
    function settle() external payable returns (uint256 paid) {
        require(synced == input, "dirty synced currency");
        if (input == address(0)) paid = msg.value;
        else { require(msg.value == 0); paid = IERC20(input).balanceOf(address(this)) - balanceAtSync; }
        require(paid == debt); debt = 0;
    }
    function take(address currency, address recipient, uint256 amount) external {
        require(currency == output && amount == credit); credit = 0;
        _pay(currency, recipient, amount);
    }
    function positionCredit(address currency, address recipient, uint256 amount) external {
        require(msg.sender == positions); _pay(currency, recipient, amount);
    }
    function _pay(address currency, address recipient, uint256 amount) private {
        if (currency == address(0)) {
            (bool ok,) = recipient.call{value: amount}(""); require(ok);
            if (forceDuringTake) new BoundaryForce{value: 1}(payable(recipient));
        } else require(IERC20(currency).transfer(recipient, amount));
    }
}

contract BoundaryForce { constructor(address payable recipient) payable { selfdestruct(recipient); } }

contract BoundaryPositions is ERC721 {
    address public immutable poolManager;
    FakePermit2 public immutable permit2;
    address public immutable WETH9;
    uint256 public nextTokenId = 1;
    bool public retainNative;
    mapping(uint256 => uint128) public getPositionLiquidity;
    mapping(uint256 => PoolKey) private keys;
    mapping(uint256 => uint256) private info;
    mapping(uint256 => uint256) public nativeFees;
    mapping(uint256 => uint256) public tokenFees;
    constructor(address core, address permit, address wrapped) ERC721("Native fake", "NF") {
        poolManager = core; permit2 = FakePermit2(permit); WETH9 = wrapped;
    }
    function retain(bool on) external { retainNative = on; }
    function fees(uint256 id, uint256 n, uint256 t) external { nativeFees[id] += n; tokenFees[id] += t; }
    function getPoolAndPositionInfo(uint256 id) external view returns (PoolKey memory, uint256) { return (keys[id], info[id]); }
    function modifyLiquidities(bytes calldata encoded, uint256) external payable {
        (bytes memory actions, bytes[] memory args) = abi.decode(encoded, (bytes, bytes[]));
        require(actions.length == 2 && args.length == 2);
        uint256 id; uint256 liquidity; uint128 max0; uint128 max1; int24 lower; int24 upper; PoolKey memory key;
        if (uint8(actions[0]) == 2) {
            address recipient; bytes memory hookData;
            (key, lower, upper, liquidity, max0, max1, recipient, hookData) =
                abi.decode(args[0], (PoolKey, int24, int24, uint256, uint128, uint128, address, bytes));
            require(hookData.length == 0); id = nextTokenId++; keys[id] = key;
            info[id] = (uint256(uint24(lower)) << 8) | (uint256(uint24(upper)) << 32); _mint(recipient, id);
        } else if (uint8(actions[0]) == 0) {
            bytes memory hookData; (id, liquidity, max0, max1, hookData) = abi.decode(args[0], (uint256, uint256, uint128, uint128, bytes));
            require(getApproved(id) == msg.sender && hookData.length == 0); key = keys[id];
            lower = int24(uint24(info[id] >> 8)); upper = int24(uint24(info[id] >> 32));
        } else {
            if (uint8(actions[0]) == 1) {
                bytes memory hd; (id, liquidity,,, hd) = abi.decode(args[0], (uint256, uint256, uint128, uint128, bytes));
                require(liquidity == 0 && hd.length == 0);
            } else { bytes memory hd; (id,,, hd) = abi.decode(args[0], (uint256, uint128, uint128, bytes)); require(hd.length == 0); }
            require(getApproved(id) == msg.sender && uint8(actions[1]) == 0x11);
            (address c0, address c1, address recipient) = abi.decode(args[1], (address, address, address));
            require(c0 == address(0) && c1 == keys[id].currency1);
            uint256 amount0 = nativeFees[id]; uint256 amount1 = tokenFees[id]; nativeFees[id] = 0; tokenFees[id] = 0;
            if (uint8(actions[0]) == 3) {
                int24 a = int24(uint24(info[id] >> 8)); int24 b = int24(uint24(info[id] >> 32));
                amount0 += SqrtPriceMath.getAmount0Delta(uint160(1 << 96), TickMath.getSqrtPriceAtTick(b), getPositionLiquidity[id], false);
                amount1 += SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(a), uint160(1 << 96), getPositionLiquidity[id], false);
                getPositionLiquidity[id] = 0; _burn(id);
            }
            BoundaryCore(payable(poolManager)).positionCredit(c0, recipient, amount0);
            BoundaryCore(payable(poolManager)).positionCredit(c1, recipient, amount1); return;
        }
        require(uint8(actions[1]) == 0x0d && key.currency0 == address(0));
        uint256 required0 = SqrtPriceMath.getAmount0Delta(uint160(1 << 96), TickMath.getSqrtPriceAtTick(upper), uint128(liquidity), true);
        uint256 required1 = SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower), uint160(1 << 96), uint128(liquidity), true);
        require(required0 <= max0 && required1 <= max1 && msg.value == required0);
        uint256 paid = retainNative ? required0 - 1 : required0;
        (bool ok,) = poolManager.call{value: paid}(""); require(ok);
        permit2.pay(msg.sender, key.currency1, required1);
        getPositionLiquidity[id] += uint128(liquidity);
    }
}

contract NativeLiquidityTest is Test {
    MockAccess private access;
    BoundaryWETH private wrapped;
    MockToken private token;
    BoundaryPools private pools;
    FakePermit2 private permit;
    BoundaryCore private core;
    BoundaryPositions private positions;
    ZZZLiquidityManager private manager;
    bytes32 private poolId;
    function setUp() public {
        access = new MockAccess(); wrapped = new BoundaryWETH(); token = new MockToken(18); permit = new FakePermit2();
        core = new BoundaryCore(); positions = new BoundaryPositions(address(core), address(permit), address(wrapped));
        core.setPositions(address(positions));
        FakeState state = new FakeState(address(core));
        manager = new ZZZLiquidityManager(address(access), address(positions), address(state), address(core), address(permit));
        PoolConfig memory c; c.key = PoolKey(address(0), address(token), 10020, 60, address(0));
        c.operationsEnabled = true; c.maxSlippageBps = 200; poolId = keccak256(abi.encode(c.key));
        vm.mockCall(address(state), abi.encodeWithSignature("getSlot0(bytes32)", poolId),
            abi.encode(uint160(1 << 96), int24(0), uint24(0), uint24(10020)));
        pools = new BoundaryPools(c, address(wrapped));
        access.bind(Ids.VAULT, address(this)); access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.LIQUIDITY, address(manager));
        access.bind(Ids.STRATEGY, address(new FakePolicy())); access.bind(Ids.ORACLE, address(new BoundaryOracle())); access.seal();
        vm.deal(address(this), 100 ether); wrapped.deposit{value: 50 ether}();
        vm.deal(address(core), 100 ether); token.mint(address(core), 100 ether); token.mint(address(this), 50 ether);
        wrapped.approve(address(manager), type(uint256).max); token.approve(address(manager), type(uint256).max);
    }
    function _mint() private returns (uint256 id) {
        (id,,) = manager.mint(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        positions.approve(address(manager), id);
    }
    function _clearApprovals() private view {
        assertEq(token.allowance(address(manager), address(permit)), 0);
        assertEq(permit.amount(address(manager), address(token), address(positions)), 0);
        assertEq(wrapped.allowance(address(manager), address(permit)), 0);
    }
    function testNativeMintSpendsOnlyExactDebtAndPreservesPrefunds() public {
        new BoundaryForce{value: 123}(payable(address(manager)));
        new BoundaryForce{value: 456}(payable(address(positions)));
        token.mint(address(manager), 789); wrapped.transfer(address(manager), 321);
        (uint256 id, uint256 spent0, uint256 spent1) = manager.mint(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(positions.ownerOf(id), address(this)); assertGt(spent0, 0); assertGt(spent1, 0);
        assertEq(address(manager).balance, 123); assertEq(address(positions).balance, 456);
        assertEq(token.balanceOf(address(manager)), 789); assertEq(wrapped.balanceOf(address(manager)), 321); _clearApprovals();
    }
    function testNativeIncreaseReusesPositionAndClearsApprovals() public {
        uint256 id = _mint(); uint128 beforeLiquidity = positions.getPositionLiquidity(id);
        manager.increase(poolId, id, 3 ether, 3 ether, 1, block.timestamp + 100);
        assertGt(positions.getPositionLiquidity(id), beforeLiquidity); assertEq(positions.nextTokenId(), 2); _clearApprovals();
    }
    function testNativeCollectWrapsOnlyActualCreditsIncludingDonationFees() public {
        uint256 id = _mint(); positions.fees(id, 17, 29);
        new BoundaryForce{value: 123}(payable(address(manager))); token.mint(address(manager), 40);
        uint256 w = wrapped.balanceOf(address(this)); uint256 t = token.balanceOf(address(this));
        manager.collect(poolId, id, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), w + 17); assertEq(token.balanceOf(address(this)), t + 29);
        assertEq(address(manager).balance, 123); assertEq(token.balanceOf(address(manager)), 40);
    }
    function testNativeCloseReturnsWrappedPrincipalWithoutExposingNativeToVault() public {
        uint256 id = _mint(); uint256 beforeWrapped = wrapped.balanceOf(address(this)); uint256 beforeNative = address(this).balance;
        (uint256 amount0, uint256 amount1) = manager.amounts(id); uint256 beforeToken = token.balanceOf(address(this));
        manager.close(poolId, id, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), beforeWrapped + amount0); assertEq(token.balanceOf(address(this)), beforeToken + amount1);
        assertEq(address(this).balance, beforeNative); vm.expectRevert(); positions.ownerOf(id);
    }
    function testNativeInputSwapResetsDirtySyncAndUsesNetDelta() public {
        uint256 beforeToken = token.balanceOf(address(this)); uint256 beforeWrapped = wrapped.balanceOf(address(this));
        uint256 out = manager.swap(poolId, true, 1 ether, 0.98 ether, block.timestamp + 100);
        assertEq(out, 0.99 ether); assertEq(token.balanceOf(address(this)), beforeToken + out);
        assertEq(wrapped.balanceOf(address(this)), beforeWrapped - 1 ether); assertEq(address(manager).balance, 0);
    }
    function testNativeOutputSwapWrapsNetDeltaAndPreservesForcedETH() public {
        new BoundaryForce{value: 123}(payable(address(manager)));
        uint256 beforeWrapped = wrapped.balanceOf(address(this));
        assertEq(manager.swap(poolId, false, 1 ether, 0.98 ether, block.timestamp + 100), 0.99 ether);
        assertEq(wrapped.balanceOf(address(this)), beforeWrapped + 0.99 ether); assertEq(address(manager).balance, 123);
    }
    function testNativePartialInputRejectedAtomically() public {
        core.setPartial(true); uint256 w = wrapped.balanceOf(address(this));
        vm.expectRevert(); manager.swap(poolId, true, 1 ether, 0.98 ether, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), w); assertEq(core.debt(), 0);
    }
    function testNativeMinOutIncludesExecutionFees() public {
        vm.expectRevert(); manager.swap(poolId, true, 1 ether, 0.995 ether, block.timestamp + 100);
        assertEq(address(manager).balance, 0);
    }
    function testNativeUnexpectedSenderAndCallbackRejected() public {
        (bool ok,) = address(manager).call{value: 1}(""); assertFalse(ok);
        vm.expectRevert(); manager.unlockCallback(bytes("fake"));
    }
    function testNativeIncorrectWrapperRejectedBeforePull() public {
        pools.setWrapper(address(token)); uint256 w = wrapped.balanceOf(address(this));
        vm.expectRevert(); manager.mint(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), w);
    }
    function testNativeAmountsRemainUint128BoundedWithoutPermitApproval() public {
        vm.expectRevert(); manager.mint(poolId, -600, 600, uint256(type(uint128).max) + 1, 1 ether, 1, block.timestamp + 100);
        assertEq(positions.nextTokenId(), 1); assertEq(address(manager).balance, 0);
    }
    function testNativeLiquidityCallbackHookMaskRejected() public {
        PoolConfig memory c = pools.get(poolId); c.key.hooks = address(0x2444); pools.setKey(c.key);
        bytes32 unsupported = keccak256(abi.encode(c.key));
        vm.expectRevert(); manager.mint(unsupported, -600, 600, 1 ether, 1 ether, 1, block.timestamp + 100);
        assertEq(positions.nextTokenId(), 1);
    }
    function testNativeDynamicFeeRejected() public {
        PoolConfig memory c = pools.get(poolId); c.key.fee = 0x800000; pools.setKey(c.key);
        bytes32 unsupported = keccak256(abi.encode(c.key));
        vm.expectRevert(); manager.mint(unsupported, -600, 600, 1 ether, 1 ether, 1, block.timestamp + 100);
        assertEq(positions.nextTokenId(), 1);
    }
    function testNativeBrokenWithdrawRollsBack() public {
        wrapped.failures(true, false); uint256 w = wrapped.balanceOf(address(this));
        vm.expectRevert(); manager.mint(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), w); assertEq(positions.nextTokenId(), 1);
    }
    function testNativeBrokenDepositRollsBackCredits() public {
        uint256 id = _mint(); positions.fees(id, 17, 29); wrapped.failures(false, true);
        vm.expectRevert(); manager.collect(poolId, id, block.timestamp + 100); assertEq(positions.nativeFees(id), 17);
    }
    function testNativeUnconsumedPosmValueRollsBackInsteadOfSweeping() public {
        positions.retain(true); uint256 w = wrapped.balanceOf(address(this));
        vm.expectRevert(); manager.mint(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), w); assertEq(positions.nextTokenId(), 1);
    }
    function testNativeForcedETHDuringTakeCannotBeClaimed() public {
        core.forceTake(true); uint256 w = wrapped.balanceOf(address(this));
        vm.expectRevert(); manager.swap(poolId, false, 1 ether, 0.98 ether, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), w); assertEq(address(manager).balance, 0);
    }
    function testNativeWrapperReentryFailsWhileCreditStillSucceeds() public {
        wrapped.reentry(address(manager));
        assertEq(manager.swap(poolId, false, 1 ether, 0.98 ether, block.timestamp + 100), 0.99 ether);
    }
    function testNativeRegistryAdmissionRejectsUnreviewedDependencies() public {
        ZZZPoolRegistry registry = new ZZZPoolRegistry(address(access));
        PoolConfig memory c = pools.get(poolId);
        vm.expectRevert(); registry.configure(c);
        vm.expectRevert(); registry.configureNative(c);
    }
    function testNativePlanBalancesNetAmountsWithinOnePercentBudget() public {
        pools.setStrategyPolicy(); ZZZStrategy policy = new ZZZStrategy(address(access)); access.bind(Ids.STRATEGY, address(policy));
        (int24 lower, int24 upper,) = policy.target(poolId);
        (bool direction, uint256 amountIn,) = policy.swapPlan(poolId, 0, 200 ether); assertFalse(direction);
        uint256 amount0 = amountIn * 99 / 100; uint256 amount1 = 200 ether - amountIn;
        uint160 a = TickMath.getSqrtPriceAtTick(lower); uint160 b = TickMath.getSqrtPriceAtTick(upper);
        uint128 liq = LiquidityAmounts.getLiquidityForAmounts(uint160(1 << 96), a, b, amount0, amount1);
        uint256 deployed = SqrtPriceMath.getAmount0Delta(uint160(1 << 96), b, liq, false) +
            SqrtPriceMath.getAmount1Delta(a, uint160(1 << 96), liq, false);
        assertGe(deployed, 198 ether); assertGt(deployed, 198.5 ether);
    }
    function testNativePlanUsesDirectionalProtocolFeesAndRejectsChangedLPFee() public {
        pools.setStrategyPolicy(); ZZZStrategy policy = new ZZZStrategy(address(access));
        access.bind(Ids.STRATEGY, address(policy));
        bytes memory callData = abi.encodeWithSignature("getSlot0(bytes32)", poolId);
        address state = address(manager.stateView());
        (bool direction,uint256 beforeInput,) = policy.swapPlan(poolId, 0, 200 ether); assertFalse(direction);
        vm.mockCall(state,callData,abi.encode(uint160(1<<96),int24(0),uint24(1000),uint24(10020)));
        (,uint256 unchangedInput,) = policy.swapPlan(poolId, 0, 200 ether); assertEq(unchangedInput,beforeInput);
        vm.mockCall(state,callData,abi.encode(uint160(1<<96),int24(0),uint24(1000<<12),uint24(10020)));
        (,uint256 higherInput,) = policy.swapPlan(poolId, 0, 200 ether); assertGt(higherInput,beforeInput);
        vm.mockCall(state,callData,abi.encode(uint160(1<<96),int24(0),uint24(0),uint24(3000)));
        vm.expectRevert(); policy.swapPlan(poolId,0,200 ether);
    }
    function testNativeDisabledPoolStillCollectsAndClosesButCannotEnterOrSwap() public {
        uint256 id = _mint(); pools.disableOperations(); positions.fees(id, 17, 29);
        vm.expectRevert(); manager.mint(poolId, -600, 600, 1 ether, 1 ether, 1, block.timestamp + 100);
        vm.expectRevert(); manager.increase(poolId, id, 1 ether, 1 ether, 1, block.timestamp + 100);
        vm.expectRevert(); manager.swap(poolId, true, 1 ether, 0.98 ether, block.timestamp + 100);
        uint256 beforeWrapped = wrapped.balanceOf(address(this)); manager.collect(poolId, id, block.timestamp + 100);
        assertEq(wrapped.balanceOf(address(this)), beforeWrapped + 17);
        manager.close(poolId, id, block.timestamp + 100); vm.expectRevert(); positions.ownerOf(id);
    }
    function testNativeDisabledPoolExitDoesNotReadUnavailableOracle() public {
        uint256 id = _mint(); pools.disableOperations();
        access.bind(Ids.ORACLE, address(new BoundaryUnavailableOracle()));
        manager.collect(poolId, id, block.timestamp + 100); manager.close(poolId, id, block.timestamp + 100);
        assertEq(address(manager).balance, 0); vm.expectRevert(); positions.ownerOf(id);
    }
    function testNativeExitPolicyIgnoresDisabledFlagButRequiresValidOracle() public {
        pools.setStrategyPolicy(); ZZZStrategy policy = new ZZZStrategy(address(access)); access.bind(Ids.STRATEGY, address(policy));
        pools.disableOperations(); vm.expectRevert(); policy.validatePrice(poolId);
        assertEq(policy.validateExitPrice(poolId), uint160(1 << 96));
        access.bind(Ids.ORACLE, address(new BoundaryUnavailableOracle())); vm.expectRevert(); policy.validateExitPrice(poolId);
    }
}
