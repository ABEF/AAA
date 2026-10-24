// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {MockAccess, MockPools} from "./mocks/Mocks.sol";
import {Ids, PoolConfig} from "../src/libraries/ZZZTypes.sol";

// TEST ONLY: deterministic authority, price, funded reserve and native swap
// fixtures. The existing BuybackExecution suite uses the real accounting and
// venue modules; these cases isolate the new operating policy and callbacks.
contract OperatingLimitAccess is MockAccess {
    function setGovernor(address account) external { governor = account; }
}
contract OperatingLimitOracle {
    bool public unavailable;
    function setUnavailable(bool value) external { unavailable = value; }
    function value(address, uint256 amount) external view returns (uint256) {
        require(!unavailable, "fixture price unavailable"); return amount;
    }
    function quote(address, address, uint256 amount) external view returns (uint256) {
        require(!unavailable, "fixture price unavailable"); return amount;
    }
}
contract OperatingLimitToken is ERC20 {
    ZZZBuyback public callback;
    bool public callbackSucceeded;
    bytes4 public callbackError;
    constructor() ERC20("Operating limit fixture", "OLF") {}
    function mint(address owner, uint256 amount) external { _mint(owner, amount); }
    function setCallback(ZZZBuyback target) external { callback = target; }
    function burn(uint256 amount) external {
        if (address(callback) != address(0)) {
            bytes memory returned;
            (callbackSucceeded, returned) = address(callback).call(abi.encodeCall(ZZZBuyback.setOperatingTradeUSD, (0)));
            if (returned.length >= 4) callbackError = bytes4(returned);
        }
        _burn(msg.sender, amount);
    }
}
contract OperatingLimitFees {
    ZZZBuyback public buyback;
    OperatingLimitToken public token;
    uint256 public nativeReserve;
    uint256 public tokenReserve;
    uint256 public releases;
    constructor(OperatingLimitToken asset) { token = asset; }
    function bind(ZZZBuyback candidate) external { require(address(buyback) == address(0)); buyback = candidate; }
    function fundNative() external payable { nativeReserve += msg.value; }
    function fundToken(uint256 amount) external { token.mint(address(this), amount); tokenReserve += amount; }
    function releaseBuyback(address asset, uint256 amount) external {
        require(msg.sender == address(buyback)); ++releases;
        if (asset == address(0)) {
            require(amount <= nativeReserve); nativeReserve -= amount;
            (bool ok,) = payable(msg.sender).call{value: amount}(""); require(ok);
        } else {
            require(asset == address(token) && amount <= tokenReserve); tokenReserve -= amount;
            require(token.transfer(msg.sender, amount));
        }
    }
}
contract OperatingLimitManager {
    OperatingLimitToken public immutable token;
    uint256 public nativeSpent;
    constructor(OperatingLimitToken asset) { token = asset; }
    function swap(bytes32, bool zeroForOne, uint256 amount, uint256 minimum, uint256)
        external payable returns (uint256) {
        require(zeroForOne && msg.value == amount && amount >= minimum);
        nativeSpent += amount; require(token.transfer(msg.sender, amount)); return amount;
    }
}

contract BuybackOperatingLimitTest is Test {
    OperatingLimitAccess private access;
    OperatingLimitToken private token;
    OperatingLimitOracle private oracle;
    OperatingLimitFees private fees;
    OperatingLimitManager private manager;
    MockPools private pools;
    ZZZBuyback private buyback;
    address private constant KEEPER = address(0xBEE1);
    address private constant HOLDER = address(0xA11CE);
    uint256 private constant HARD = 100 ether;
    bytes32 private constant POOL = keccak256("operating-limit-native");
    event OperatingTradeLimitChanged(uint256 previous, uint256 current);

    function setUp() public {
        vm.warp(1_000_000); vm.deal(address(this), 1000 ether);
        access = new OperatingLimitAccess(); token = new OperatingLimitToken(); oracle = new OperatingLimitOracle();
        fees = new OperatingLimitFees(token); manager = new OperatingLimitManager(token); pools = new MockPools();
        buyback = new ZZZBuyback(address(access), address(token), HARD); fees.bind(buyback);
        access.bind(Ids.BUYBACK, address(buyback)); access.bind(Ids.FEES, address(fees));
        access.bind(Ids.LIQUIDITY, address(manager)); access.bind(Ids.ORACLE, address(oracle)); access.bind(Ids.POOLS, address(pools));
        access.setKeeper(KEEPER, true);
        PoolConfig memory config; config.key.currency1 = address(token); config.maxSlippageBps = 100;
        pools.set(POOL, config); token.mint(address(manager), 1000 ether);
        fees.fundNative{value: 200 ether}(); fees.fundToken(200 ether);
    }
    function _execute(address asset, uint256 amount) private {
        vm.prank(KEEPER); buyback.execute(asset, amount, POOL, block.timestamp + 100);
    }
    function testInitialOperatingLimitMatchesImmutableHardCeiling() public view {
        assertEq(buyback.maxTradeUSD(), HARD); assertEq(buyback.operatingTradeUSD(), HARD);
    }
    function testBootstrapAndPostSealGovernanceCanAdjustImmediatelyWithExactEvents() public {
        vm.expectEmit(false, false, false, true, address(buyback)); emit OperatingTradeLimitChanged(HARD, 20 ether);
        buyback.setOperatingTradeUSD(20 ether); access.seal();
        vm.expectEmit(false, false, false, true, address(buyback)); emit OperatingTradeLimitChanged(20 ether, 60 ether);
        buyback.setOperatingTradeUSD(60 ether);
        assertEq(buyback.operatingTradeUSD(), 60 ether); assertEq(buyback.maxTradeUSD(), HARD);
    }
    function testHolderAndKeeperCannotChangeOperatingPolicy() public {
        access.seal();
        vm.prank(HOLDER); vm.expectRevert(bytes4(keccak256("Unauthorized()"))); buyback.setOperatingTradeUSD(0);
        vm.prank(KEEPER); vm.expectRevert(bytes4(keccak256("Unauthorized()"))); buyback.setOperatingTradeUSD(HARD);
        assertEq(buyback.operatingTradeUSD(), HARD);
    }
    function testCannotRaiseOperatingLimitBeyondHardCeiling() public {
        access.seal(); buyback.setOperatingTradeUSD(20 ether);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); buyback.setOperatingTradeUSD(HARD + 1);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); buyback.setOperatingTradeUSD(type(uint256).max);
        assertEq(buyback.operatingTradeUSD(), 20 ether); assertEq(buyback.maxTradeUSD(), HARD);
    }
    function testZeroStopsWithoutPriceOrReserveCallsAndCanBeReopened() public {
        access.seal(); oracle.setUnavailable(true); buyback.setOperatingTradeUSD(0);
        vm.expectRevert(bytes4(keccak256("InvalidAmount()"))); _execute(address(0), 1);
        vm.expectRevert(bytes4(keccak256("InvalidAmount()"))); _execute(address(token), 1);
        assertEq(fees.releases(), 0); assertEq(fees.nativeReserve(), 200 ether); assertEq(fees.tokenReserve(), 200 ether);
        buyback.setOperatingTradeUSD(20 ether); // Reopening policy never bypasses execution's fresh-price checks.
        vm.expectRevert(bytes("fixture price unavailable")); _execute(address(token), 1 ether);
        oracle.setUnavailable(false); _execute(address(token), 20 ether);
        assertEq(fees.tokenReserve(), 180 ether);
    }
    function testNativeExactLimitWorksAndOverLimitPreservesReservesAndDonations() public {
        access.seal(); buyback.setOperatingTradeUSD(20 ether); vm.deal(address(buyback), 7 ether);
        uint256 supply = token.totalSupply();
        vm.expectRevert(bytes4(keccak256("InvalidAmount()"))); _execute(address(0), 20 ether + 1);
        assertEq(fees.releases(), 0); assertEq(fees.nativeReserve(), 200 ether);
        assertEq(manager.nativeSpent(), 0); assertEq(token.totalSupply(), supply);
        _execute(address(0), 20 ether);
        assertEq(fees.nativeReserve(), 180 ether); assertEq(manager.nativeSpent(), 20 ether);
        assertEq(address(buyback).balance, 7 ether); assertEq(token.totalSupply(), supply - 20 ether);
    }
    function testLoweredPolicyRejectsPreviouslyReviewedTradeAtExecution() public {
        access.seal(); uint256 reviewedAmount = 50 ether; buyback.setOperatingTradeUSD(40 ether);
        vm.expectRevert(bytes4(keccak256("InvalidAmount()"))); _execute(address(token), reviewedAmount);
        assertEq(fees.releases(), 0); assertEq(fees.tokenReserve(), 200 ether);
        buyback.setOperatingTradeUSD(HARD); _execute(address(token), reviewedAmount);
        assertEq(fees.tokenReserve(), 150 ether);
    }
    function testOrdinaryPauseAllowsPolicyChangeButNotExecution() public {
        access.seal(); access.setPaused(true); buyback.setOperatingTradeUSD(0); buyback.setOperatingTradeUSD(20 ether);
        vm.expectRevert(bytes4(keccak256("Paused()"))); _execute(address(token), 1 ether);
        access.setPaused(false); _execute(address(token), 20 ether);
        assertEq(fees.tokenReserve(), 180 ether);
    }
    function testPreparationAndEveryCanonicalLockBlockPolicyChanges() public {
        access.seal(); access.setPreparation(true);
        vm.expectRevert(); buyback.setOperatingTradeUSD(0); access.setPreparation(false);
        for (uint8 state = 1; state <= 4; ++state) {
            access.setCanonicalState(state);
            vm.expectRevert(bytes4(keccak256("CanonicalLocked()"))); buyback.setOperatingTradeUSD(0);
            assertEq(buyback.operatingTradeUSD(), HARD);
        }
        access.setCanonicalState(0); buyback.setOperatingTradeUSD(20 ether);
    }
    function testAuthorizedGovernanceCallbackCannotChangePolicyDuringBurn() public {
        access.seal(); token.setCallback(buyback); access.setGovernor(address(token));
        _execute(address(token), 20 ether);
        assertFalse(token.callbackSucceeded());
        assertEq(token.callbackError(), bytes4(keccak256("ReentrancyGuardReentrantCall()")));
        assertEq(buyback.operatingTradeUSD(), HARD); assertEq(fees.tokenReserve(), 180 ether);
    }
    function testOperatingLimitIsPerTradeNotAnInventedCumulativeBudget() public {
        access.seal(); buyback.setOperatingTradeUSD(20 ether);
        _execute(address(token), 20 ether); _execute(address(token), 20 ether);
        assertEq(fees.tokenReserve(), 160 ether); assertEq(buyback.operatingTradeUSD(), 20 ether);
    }
    function testFuzzGovernanceOperatingLimitAlwaysWithinHardCeiling(uint256 candidate) public {
        uint256 limit = bound(candidate, 1, HARD); access.seal(); buyback.setOperatingTradeUSD(limit);
        uint256 supply = token.totalSupply();
        vm.expectRevert(bytes4(keccak256("InvalidAmount()"))); _execute(address(token), limit + 1);
        assertEq(fees.tokenReserve(), 200 ether); assertEq(fees.releases(), 0);
        _execute(address(token), limit);
        assertEq(fees.tokenReserve(), 200 ether - limit); assertEq(token.totalSupply(), supply - limit);
        assertEq(token.balanceOf(address(buyback)), 0); assertEq(buyback.maxTradeUSD(), HARD);
    }
}
