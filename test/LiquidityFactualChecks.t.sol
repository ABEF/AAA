// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta, BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {SwapParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {IPositionDescriptor} from "@uniswap/v4-periphery/src/interfaces/IPositionDescriptor.sol";
import {IWETH9} from "@uniswap/v4-periphery/src/interfaces/external/IWETH9.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockPools} from "./mocks/Mocks.sol";

/// @dev TEST ONLY: implements only the exact allowance path used by installed
/// PositionManager. Actual Permit2 is solc 0.8.17, outside this pinned compiler.
contract FactualPermit {
    struct Approval { uint160 amount; uint48 expiration; }
    mapping(address => mapping(address => mapping(address => Approval))) public allowances;
    function approve(address token, address spender, uint160 amount, uint48 expiration) external {
        allowances[msg.sender][token][spender] = Approval(amount, expiration);
    }
    function transferFrom(address from, address to, uint160 amount, address token) external {
        Approval storage a = allowances[from][token][msg.sender];
        require(a.expiration >= block.timestamp && a.amount >= amount);
        a.amount -= amount; require(IERC20(token).transferFrom(from, to, amount));
    }
}

/// @dev Exact transfers with one deliberately hostile external callback.
contract FactualToken is ERC20 {
    address public manager;
    address public contributor;
    address public callback;
    bytes public callbackData;
    uint8 public phase;
    bool public armed;
    constructor() ERC20("Factual callback token", "FACT") {}
    function mint(address owner, uint256 amount) external { _mint(owner, amount); }
    function arm(address manager_, uint8 phase_, address target, bytes calldata data) external {
        manager = manager_; contributor = msg.sender; phase = phase_; callback = target; callbackData = data; armed = true;
    }
    function _call(uint8 stage) private {
        if (!armed || phase != stage) return;
        armed = false; (bool ok, bytes memory reason) = callback.call(callbackData);
        if (!ok) assembly ("memory-safe") { revert(add(reason,32),mload(reason)) }
    }
    function approve(address spender, uint256 amount) public override returns (bool) {
        bool ok = super.approve(spender, amount);
        if (msg.sender == manager && amount == 0) _call(2);
        return ok;
    }
    function _update(address from, address to, uint256 amount) internal override {
        super._update(from,to,amount);
        if (to == manager && from == contributor) _call(1);
        if (from == manager && to == contributor) _call(3);
    }
}

contract FactualPools is MockPools {
    function isNativePool(bytes32 id) external view returns (bool) { return this.get(id).key.currency0 == address(0); }
}
contract FactualReference {
    function referenceX96(address, address) external pure returns(uint160) { return uint160(1 << 96); }
}

/// @dev A separately funded external trader. Its callback trade does not change
/// the contributor's balance and cannot be rejected merely as an inexact pull.
contract FactualTrader {
    using BalanceDeltaLibrary for BalanceDelta;
    PoolManager private immutable core;
    CoreKey private key;
    constructor(PoolManager core_, CoreKey memory key_) { core=core_; key=key_; }
    function movePrice() external { core.unlock(abi.encode(uint256(0.1 ether))); }
    function unlockCallback(bytes calldata data) external returns(bytes memory) {
        require(msg.sender==address(core)); uint256 amount=abi.decode(data,(uint256));
        BalanceDelta d=core.swap(key,SwapParams(false,-int256(amount),TickMath.MAX_SQRT_PRICE-1),"");
        core.sync(key.currency1); require(IERC20(Currency.unwrap(key.currency1)).transfer(address(core),uint256(-int256(d.amount1()))));
        require(core.settle()==uint256(-int256(d.amount1())));
        core.take(key.currency0,address(this),uint256(int256(d.amount0()))); return "";
    }
}

/// @notice Actual installed v4 core, StateView AND PositionManager. Token prices,
/// asset admission and Permit2 are local substitutes, not provider qualification.
contract LiquidityFactualChecksTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    MockAccess private access;
    FactualToken private token0;
    FactualToken private token1;
    FactualPools private pools;
    FactualPermit private permit;
    PoolManager private core;
    StateView private state;
    PositionManager private positions;
    ZZZLiquidityManager private manager;
    ZZZStrategy private strategy;
    FactualTrader private trader;
    PoolKey private key;
    bytes32 private poolId;
    uint256 private incumbent;

    receive() external payable {}
    function setUp() public {
        vm.warp(1_000_000); vm.deal(address(this), 10000 ether);
        access = new MockAccess(); pools = new FactualPools(); permit = new FactualPermit();
        FactualToken a = new FactualToken(); FactualToken b = new FactualToken();
        (token0,token1) = address(a)<address(b) ? (a,b) : (b,a);
        core = new PoolManager(address(this)); state = new StateView(IPoolManager(address(core)));
        // No descriptor/wrapper operation is used by these typed LP actions.
        positions = new PositionManager(IPoolManager(address(core)), IAllowanceTransfer(address(permit)),
            100000, IPositionDescriptor(address(0)), IWETH9(address(0)));
        manager = new ZZZLiquidityManager(address(access),address(positions),address(state),address(core),address(permit));
        strategy = new ZZZStrategy(address(access));
        access.bind(Ids.VAULT,address(this)); access.bind(Ids.LIQUIDITY,address(manager));
        access.bind(Ids.POOLS,address(pools)); access.bind(Ids.STRATEGY,address(strategy));
        access.bind(Ids.ORACLE,address(new FactualReference())); access.seal();
        key = PoolKey(address(token0),address(token1),3000,60,address(0));
        poolId = _admit(key); core.initialize(_coreKey(key),uint160(1 << 96));
        token0.mint(address(this),10000 ether); token1.mint(address(this),10000 ether);
        token0.approve(address(manager),type(uint256).max); token1.approve(address(manager),type(uint256).max);
        (incumbent,,) = manager.mint(poolId,-600,600,1000 ether,1000 ether,1,block.timestamp+100);
        positions.approve(address(manager),incumbent);
        trader=new FactualTrader(core,_coreKey(key));token1.mint(address(trader),10 ether);
    }
    function _admit(PoolKey memory k) private returns(bytes32 id) {
        PoolConfig memory c; c.key=k; c.operationsEnabled=true; c.depositsEnabled=true;
        c.maxSpotDeviationBps=100; c.maxSlippageBps=100; c.rangeBps=1000;
        id=keccak256(abi.encode(k)); pools.set(id,c);
    }
    function _coreKey(PoolKey memory k) private pure returns(CoreKey memory) {
        return CoreKey(Currency.wrap(k.currency0),Currency.wrap(k.currency1),k.fee,k.tickSpacing,IHooks(k.hooks));
    }
    function lateOwnerLoss() external { positions.transferFrom(address(this),address(0xBAD),incumbent); }
    function _arm(uint8 stage, bool ownerLoss) private {
        token1.arm(address(manager),stage,ownerLoss ? address(this) : address(trader),ownerLoss
            ? abi.encodeCall(this.lateOwnerLoss,()) : abi.encodeCall(trader.movePrice,()));
    }
    function _mint() private { manager.mint(poolId,-600,600,100 ether,150 ether,1,block.timestamp+100); }
    function _increase() private { manager.increase(poolId,incumbent,100 ether,150 ether,1,block.timestamp+100); }
    function _assertClean(uint128 initialLiquidity, uint256 b0, uint256 b1) private view {
        assertEq(positions.getPositionLiquidity(incumbent),initialLiquidity);
        assertEq(positions.ownerOf(incumbent),address(this)); assertEq(positions.nextTokenId(),2);
        assertEq(token0.balanceOf(address(this)),b0); assertEq(token1.balanceOf(address(this)),b1);
        assertEq(token0.balanceOf(address(manager)),0); assertEq(token1.balanceOf(address(manager)),0);
        assertEq(token0.allowance(address(manager),address(permit)),0);
        assertEq(token1.allowance(address(manager),address(permit)),0);
        (uint160 p,,,) = state.getSlot0(PoolId.wrap(poolId)); assertEq(p,uint160(1 << 96));
    }
    function _rejected(uint8 stage, bool increasing) private {
        uint128 l=positions.getPositionLiquidity(incumbent);
        uint256 b0=token0.balanceOf(address(this)); uint256 b1=token1.balanceOf(address(this));
        _arm(stage,false); vm.expectRevert(ZZZModule.Slippage.selector);
        if(increasing) _increase(); else _mint();
        _assertClean(l,b0,b1);
    }
    function testMintRejectsRealPriceChangeDuringTokenPullWithinOrdinaryDeviation() public { _rejected(1,false); }
    function testIncreaseRejectsRealPriceChangeDuringTokenPullWithinOrdinaryDeviation() public { _rejected(1,true); }
    function testMintRejectsRealPriceChangeDuringApprovalReset() public { _rejected(2,false); }
    function testIncreaseRejectsRealPriceChangeDuringApprovalReset() public { _rejected(2,true); }
    function testMintRejectsRealPriceChangeDuringFinalRefund() public { _rejected(3,false); }
    function testIncreaseRejectsRealPriceChangeDuringFinalRefund() public { _rejected(3,true); }
    function testFinalRefundCannotTransferLPBehindEarlierOwnerCheck() public {
        uint128 l=positions.getPositionLiquidity(incumbent);
        uint256 b0=token0.balanceOf(address(this));uint256 b1=token1.balanceOf(address(this));
        _arm(3,true);vm.expectRevert(ZZZModule.InvalidState.selector);_increase();_assertClean(l,b0,b1);
    }
    function testIncorrectPhysicalLiquidityCannotPassFactualCheck() public {
        uint128 l=positions.getPositionLiquidity(incumbent);
        uint256 b0=token0.balanceOf(address(this));uint256 b1=token1.balanceOf(address(this));
        vm.mockCall(address(positions),abi.encodeWithSignature("getPositionLiquidity(uint256)",incumbent),abi.encode(uint128(0)));
        vm.expectRevert(ZZZModule.InvalidState.selector);_increase();vm.clearMockedCalls();_assertClean(l,b0,b1);
    }
    function testCallbackTradeIsWithinOrdinaryPriceGuardYetChangesActualSpot() public {
        trader.movePrice();
        uint160 price=strategy.validatePrice(poolId);
        assertGt(price,uint160(1<<96));
        assertEq(price,manager.spot(poolId));
    }
    function testHonestInstalledV4IncreaseMatchesRawLiquidityAndExactPrincipal() public {
        uint128 beforeL=positions.getPositionLiquidity(incumbent);
        uint256 b0=token0.balanceOf(address(this));uint256 b1=token1.balanceOf(address(this));
        (uint256 spent0,uint256 spent1)=manager.increase(poolId,incumbent,100 ether,150 ether,1,block.timestamp+100);
        uint128 added=positions.getPositionLiquidity(incumbent)-beforeL;
        assertGt(added,0);assertEq(positions.ownerOf(incumbent),address(this));
        assertEq(b0-token0.balanceOf(address(this)),spent0);assertEq(b1-token1.balanceOf(address(this)),spent1);
        assertEq(spent0,SqrtPriceMath.getAmount0Delta(uint160(1<<96),TickMath.getSqrtPriceAtTick(600),added,true));
        assertEq(spent1,SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(-600),uint160(1<<96),added,true));
        assertEq(strategy.validatePrice(poolId),uint160(1<<96));assertEq(positions.nextTokenId(),2);
    }
    function testHonestInstalledV4NativeMintAndIncreaseUseNoWrapper() public {
        PoolKey memory nativeKey=PoolKey(address(0),address(token1),3000,60,address(0));
        bytes32 id=_admit(nativeKey);core.initialize(_coreKey(nativeKey),uint160(1<<96));
        uint256 nativeBefore=address(this).balance;
        (uint256 lp,uint256 spent0,uint256 spent1)=manager.mint{value:100 ether}(id,-600,600,100 ether,150 ether,1,block.timestamp+100);
        assertEq(nativeBefore-address(this).balance,spent0);assertGt(spent1,0);
        positions.approve(address(manager),lp);uint128 l=positions.getPositionLiquidity(lp);
        manager.increase{value:5 ether}(id,lp,5 ether,10 ether,1,block.timestamp+100);
        assertGt(positions.getPositionLiquidity(lp),l);assertEq(positions.ownerOf(lp),address(this));
        assertEq(address(manager).balance,0);assertEq(address(positions).balance,0);
        assertEq(strategy.validatePrice(id),uint160(1<<96));
    }
}
