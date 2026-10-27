// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
// TEST ONLY ERC20 admission; production permits only native ETH/ZZZ LP.
import {SyntheticPoolRegistry as ZZZPoolRegistry} from "./helpers/SyntheticPoolRegistry.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {IPoolManagerMinimal} from "../src/interfaces/IZZZ.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {RewardsVaultFixture} from "./RewardsAndFees.t.sol";
import {FakePermit2, FakePositionManager} from "./LiquidityEncoding.t.sol";

/// @dev TEST ONLY: selectable broken burn and callback behavior. Never production token code.
contract BuybackBurnToken is ERC20 {
    enum Mode { Correct, NoOp, Partial, RevertBurn }
    Mode public mode;
    address public reentryTarget;
    bool public reentrySucceeded;
    bytes4 public reentryError;
    constructor() ERC20("Buyback fixture ZZZ", "BZZZ") {}
    function mint(address account, uint256 amount) external { _mint(account, amount); }
    function setMode(Mode value) external { mode = value; }
    function setReentry(address target) external { reentryTarget = target; }
    function burn(uint256 amount) external {
        require(mode != Mode.RevertBurn, "fixture burn unavailable");
        if (reentryTarget != address(0)) {
            bytes memory returned;
            (reentrySucceeded, returned) = reentryTarget.call(abi.encodeCall(
                ZZZBuyback.execute, (address(this), uint256(1), bytes32(0), block.timestamp)));
            if (returned.length >= 4) reentryError = bytes4(returned);
        }
        if (mode == Mode.Correct) _burn(msg.sender, amount);
        else if (mode == Mode.Partial) _burn(msg.sender, amount / 2);
    }
}

/// @dev TEST ONLY: simulate an admitted token refusing one transfer destination.
contract BuybackInputToken is MockToken {
    address public blockedRecipient;
    constructor() MockToken(18) {}
    function blockRecipient(address recipient) external { blockedRecipient = recipient; }
    function _update(address from, address to, uint256 amount) internal override {
        require(to == address(0) || to != blockedRecipient, "fixture recipient blocked");
        super._update(from, to, amount);
    }
}

/// @dev TEST ONLY: deterministic v4 settlement, not a real pool, market quote or hook.
/// Real LiquidityManager validates the input debt, output minimum and exact transfers.
contract BuybackCoreFixture {
    address public input;
    address public output;
    address private synced;
    uint256 private beforeSync;
    uint256 public debt;
    uint256 public credit;
    uint256 public swaps;
    uint256 public outputBps = 10000;
    bool public failSwap;
    address public reentryTarget;
    bool public reentrySucceeded;
    bytes4 public reentryError;
    address public postSwapState;
    uint160 public postSwapPrice;
    function setOutputBps(uint256 value) external { outputBps = value; }
    function setFail(bool value) external { failSwap = value; }
    function setReentry(address target) external { reentryTarget = target; }
    function setPostSwapPrice(address target, uint160 value) external { postSwapState = target; postSwapPrice = value; }
    function unlock(bytes calldata data) external returns (bytes memory result) {
        result = ZZZLiquidityManager(payable(msg.sender)).unlockCallback(data);
        require(debt == 0 && credit == 0, "fixture unsettled balances");
    }
    function swap(PoolKey calldata key, IPoolManagerMinimal.SwapParams calldata params, bytes calldata)
        external returns (int256 delta) {
        require(!failSwap, "fixture market unavailable");
        ++swaps;
        input = params.zeroForOne ? key.currency0 : key.currency1;
        output = params.zeroForOne ? key.currency1 : key.currency0;
        if (reentryTarget != address(0)) {
            bytes memory returned;
            (reentrySucceeded, returned) = reentryTarget.call(abi.encodeCall(
                ZZZBuyback.execute, (input, uint256(1), keccak256(abi.encode(key)), block.timestamp)));
            if (returned.length >= 4) reentryError = bytes4(returned);
        }
        debt = uint256(-params.amountSpecified);
        credit = debt * outputBps / 10000;
        int128 d0 = params.zeroForOne ? -int128(uint128(debt)) : int128(uint128(credit));
        int128 d1 = params.zeroForOne ? int128(uint128(credit)) : -int128(uint128(debt));
        delta = (int256(d0) << 128) | int256(uint256(uint128(d1)));
        if (postSwapState != address(0)) BuybackStateFixture(postSwapState).setPrice(postSwapPrice);
    }
    function sync(address token) external { synced = token; beforeSync = IERC20(token).balanceOf(address(this)); }
    function settle() external payable returns (uint256 paid) {
        require(msg.value == 0 && synced == input, "fixture wrong input");
        paid = IERC20(input).balanceOf(address(this)) - beforeSync;
        require(paid == debt, "fixture incorrect debt");
        debt = 0;
    }
    function take(address token, address recipient, uint256 amount) external {
        require(token == output && amount == credit, "fixture incorrect credit");
        credit = 0;
        require(IERC20(token).transfer(recipient, amount));
    }
}

contract BuybackStateFixture {
    address public immutable poolManager;
    uint160 public price = uint160(1 << 96);
    constructor(address core) { poolManager = core; }
    function setPrice(uint160 value) external { price = value; }
    function getSlot0(bytes32) external view returns (uint160, int24, uint24, uint24) { return (price, 0, 0, 3000); }
}

/// @notice Real fee/reward/buyback/price/registry/strategy/manager execution.
/// Synthetic tokens, price feeds, authority, share ledger, VRF and v4 settlement;
/// no real LP custody, venue price formation, mainnet MEV or live service claim.
contract BuybackExecutionTest is Test {
    MockAccess private access;
    MockToken private input;
    BuybackBurnToken private zzz;
    MockFeed private inputFeed;
    MockFeed private zzzFeed;
    ZZZOracle private oracle;
    ZZZPoolRegistry private pools;
    ZZZStrategy private strategy;
    ZZZLiquidityManager private manager;
    ZZZBuyback private buyback;
    ZZZFeeController private fees;
    ZZZRewards private rewards;
    ZZZMembership private membership;
    ZZZNFT private nft;
    RewardsVaultFixture private vault;
    BuybackCoreFixture private core;
    BuybackStateFixture private state;
    bytes32 private pool;
    uint256 private constant BUCKET = 7;
    uint256 private constant GROSS = 1000 ether;
    uint256 private constant RESERVE = 50 ether;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    bytes4 private constant INVALID_STATE = bytes4(keccak256("InvalidState()"));
    bytes4 private constant INVALID_CONFIGURATION = bytes4(keccak256("InvalidConfiguration()"));
    bytes4 private constant INVALID_AMOUNT = bytes4(keccak256("InvalidAmount()"));
    bytes4 private constant REENTRY = bytes4(keccak256("ReentrancyGuardReentrantCall()"));
    event BoughtAndBurned(address indexed input, uint256 inputAmount, uint256 zzzBurned);

    function setUp() public {
        vm.warp(1_000_000);
        access = new MockAccess(); input = new BuybackInputToken(); zzz = new BuybackBurnToken();
        inputFeed = new MockFeed(8, 1e8); zzzFeed = new MockFeed(8, 1e8);
        oracle = new ZZZOracle(address(access), address(0));
        oracle.setTestFeed(address(input), address(inputFeed), 3600);
        oracle.setTestFeed(address(zzz), address(zzzFeed), 3600);
        rewards = new ZZZRewards(address(access)); membership = new ZZZMembership(address(access));
        fees = new ZZZFeeController(address(access)); vault = new RewardsVaultFixture(rewards);
        nft = new ZZZNFT(address(access), "ipfs://test-only/");
        nft.configureRandomness(address(new MockVRF()), bytes32(uint256(1)), 1, 3, 500000, false);
        pools = new ZZZPoolRegistry(address(access)); strategy = new ZZZStrategy(address(access));
        core = new BuybackCoreFixture(); state = new BuybackStateFixture(address(core));
        FakePermit2 permit = new FakePermit2();
        FakePositionManager positions = new FakePositionManager(address(core), address(permit));
        manager = new ZZZLiquidityManager(address(access), address(positions), address(state), address(core), address(permit));
        buyback = new ZZZBuyback(address(access), address(zzz), 100 ether);
        access.bind(Ids.NFT, address(nft)); access.bind(Ids.VAULT, address(vault));
        access.bind(Ids.MEMBERSHIP, address(membership)); access.bind(Ids.REWARDS, address(rewards));
        access.bind(Ids.FEES, address(fees)); access.bind(Ids.BUYBACK, address(buyback));
        access.bind(Ids.ORACLE, address(oracle)); access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.STRATEGY, address(strategy)); access.bind(Ids.LIQUIDITY, address(manager));
        rewards.addAsset(address(input)); rewards.addAsset(address(zzz));
        pools.activationAssets().configureZZZ(address(zzz), address(zzz).codehash, keccak256("buyback fixture fixed ZZZ"));
        PoolConfig memory c = _configuration(address(input), address(zzz)); pool = pools.configure(c);
        Position memory p; p.poolId = pool; p.status = PositionStatus.Active;
        vault.set(BUCKET, p); access.setKeeper(address(this), true); access.seal();
        vm.prank(address(vault)); nft.mint(ALICE, 1); vault.join(1, BUCKET, 100);
        vm.prank(address(vault)); membership.activate(1);
        vm.prank(address(vault)); nft.mint(BOB, 2); vault.join(2, BUCKET, 100);
        vm.prank(address(vault)); membership.activate(2);
        zzz.mint(address(core), 1_000_000 ether);
    }
    function _configuration(address a, address b) private pure returns (PoolConfig memory c) {
        (address t0, address t1) = a < b ? (a, b) : (b, a);
        c.key = PoolKey(t0, t1, 3000, 60, address(0)); c.operationsEnabled = true; c.depositsEnabled = true;
        c.rangeBps = 1000; c.triggerBps = 500; c.maxSpotDeviationBps = 100; c.maxSlippageBps = 100;
        c.minRebalanceInterval = 600; c.minDepositUSD = 100 ether; c.maxPositionUSD = 1_000_000 ether;
    }
    function _fund(address token, uint256 amount) private {
        if (token == address(zzz)) zzz.mint(address(vault), amount);
        else input.mint(address(vault), amount);
        vm.startPrank(address(vault)); IERC20(token).approve(address(fees), amount);
        fees.allocate(BUCKET, token, amount); vm.stopPrank();
    }
    function _execute(address token, uint256 amount) private {
        buyback.execute(token, amount, pool, block.timestamp + 100);
    }
    function _ledger(address token) private view returns (bytes32) {
        bytes32 reserves = keccak256(abi.encode(fees.buybackBalance(token), fees.compoundBalance(BUCKET, token),
            fees.accounted(token), fees.dust(BUCKET, token), IERC20(token).balanceOf(address(fees))));
        bytes32 claims = keccak256(abi.encode(rewards.claimable(1, token), rewards.claimable(2, token),
            rewards.liabilities(token), IERC20(token).balanceOf(address(rewards))));
        bytes32 execution = keccak256(abi.encode(zzz.totalSupply(), zzz.balanceOf(address(buyback)),
            input.balanceOf(address(buyback)), input.allowance(address(buyback), address(manager)),
            zzz.allowance(address(buyback), address(manager)), core.swaps(), core.debt(), core.credit(), state.price()));
        return keccak256(abi.encode(reserves, claims, execution, input.balanceOf(address(core)), zzz.balanceOf(address(core)),
            input.balanceOf(address(manager)), zzz.balanceOf(address(manager))));
    }
    function _claimBoth(address token) private {
        vm.prank(ALICE); assertEq(rewards.claim(1, token), 450 ether);
        vm.prank(BOB); assertEq(rewards.claim(2, token), 450 ether);
        assertEq(rewards.liabilities(token), 0);
    }
    function _assertReserves(address token, uint256 remaining) private view {
        assertEq(fees.buybackBalance(token), remaining);
        assertEq(fees.compoundBalance(BUCKET, token), RESERVE);
        assertEq(fees.accounted(token), RESERVE + remaining);
        assertEq(IERC20(token).balanceOf(address(fees)), RESERVE + remaining);
        assertEq(input.allowance(address(buyback), address(manager)), 0);
        assertEq(zzz.allowance(address(buyback), address(manager)), 0);
        assertEq(input.balanceOf(address(manager)), 0); assertEq(zzz.balanceOf(address(manager)), 0);
    }

    function testDirectZZZBurnUsesOnlyBuybackReserveAndPreservesDonations() public {
        _fund(address(zzz), GROSS); zzz.mint(address(buyback), 17 ether);
        uint256 beforeSupply = zzz.totalSupply();
        vm.expectEmit(true, false, false, true, address(buyback));
        emit BoughtAndBurned(address(zzz), RESERVE, RESERVE);
        _execute(address(zzz), RESERVE);
        assertEq(zzz.totalSupply(), beforeSupply - RESERVE); assertEq(zzz.balanceOf(address(buyback)), 17 ether);
        assertEq(core.swaps(), 0); _assertReserves(address(zzz), 0); _claimBoth(address(zzz));
        vm.expectRevert(INVALID_AMOUNT); _execute(address(zzz), RESERVE);
    }
    function testApprovedDirectSwapBurnPreservesRewardAndCompoundBalances() public {
        _fund(address(input), GROSS); core.setOutputBps(9900); zzz.mint(address(buyback), 17 ether);
        input.mint(address(buyback), 13 ether); uint256 beforeSupply = zzz.totalSupply();
        uint256 acquired = RESERVE * 99 / 100;
        vm.expectEmit(true, false, false, true, address(buyback)); emit BoughtAndBurned(address(input), RESERVE, acquired);
        _execute(address(input), RESERVE);
        assertEq(zzz.totalSupply(), beforeSupply - acquired); assertEq(core.swaps(), 1);
        assertEq(input.balanceOf(address(core)), RESERVE); assertEq(zzz.balanceOf(address(buyback)), 17 ether);
        assertEq(input.balanceOf(address(buyback)), 13 ether); _assertReserves(address(input), 0); _claimBoth(address(input));
    }
    function testSwapFailureRollsBackThenClaimsAndRetryRemainAvailable() public {
        _fund(address(input), GROSS); core.setFail(true); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(bytes("fixture market unavailable")); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
        core.setFail(false); _execute(address(input), RESERVE); _assertReserves(address(input), 0);
    }
    function testBelowMinimumSwapRollsBackAndCanRetry() public {
        _fund(address(input), GROSS); core.setOutputBps(9899); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(bytes4(keccak256("Slippage()"))); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); core.setOutputBps(9900);
        _execute(address(input), RESERVE); _assertReserves(address(input), 0); _claimBoth(address(input));
    }
    function testReserveTransferFailureRestoresAccountingAndCanRetry() public {
        _fund(address(input), GROSS); BuybackInputToken(address(input)).blockRecipient(address(buyback));
        bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(bytes("fixture recipient blocked")); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
        BuybackInputToken(address(input)).blockRecipient(address(0));
        _execute(address(input), RESERVE); _assertReserves(address(input), 0);
    }
    function testNoOpBurnRejectsAndRestoresEverythingBeforeRetry() public {
        _fund(address(input), GROSS); zzz.setMode(BuybackBurnToken.Mode.NoOp); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(INVALID_STATE); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); zzz.setMode(BuybackBurnToken.Mode.Correct);
        _execute(address(input), RESERVE); _assertReserves(address(input), 0); _claimBoth(address(input));
    }
    function testPartialBurnRejectsAndRestoresEverythingBeforeRetry() public {
        _fund(address(zzz), GROSS); zzz.setMode(BuybackBurnToken.Mode.Partial); bytes32 beforeState = _ledger(address(zzz));
        vm.expectRevert(INVALID_STATE); _execute(address(zzz), RESERVE);
        assertEq(_ledger(address(zzz)), beforeState); zzz.setMode(BuybackBurnToken.Mode.Correct);
        _execute(address(zzz), RESERVE); _assertReserves(address(zzz), 0); _claimBoth(address(zzz));
    }
    function testRevertingBurnDoesNotBlockLPClaims() public {
        _fund(address(input), GROSS); zzz.setMode(BuybackBurnToken.Mode.RevertBurn); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(bytes("fixture burn unavailable")); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
        zzz.setMode(BuybackBurnToken.Mode.Correct); _execute(address(input), RESERVE); _assertReserves(address(input), 0);
    }
    function testStaleFeedRejectsWithoutReleasingFundsAndRecoversAfterRefresh() public {
        _fund(address(input), GROSS); vm.warp(block.timestamp + 3601); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(input))); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
        inputFeed.set(1e8, block.timestamp, block.timestamp); zzzFeed.set(1e8, block.timestamp, block.timestamp);
        _execute(address(input), RESERVE); _assertReserves(address(input), 0);
    }
    function testStaleOutputFeedRollsBackReleasedInputReserve() public {
        _fund(address(input), GROSS); vm.warp(block.timestamp + 3601);
        inputFeed.set(1e8, block.timestamp, block.timestamp); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(zzz))); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
    }
    function testUnapprovedRouteCannotReleaseReserve() public {
        _fund(address(input), GROSS); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(INVALID_CONFIGURATION); buyback.execute(address(input), RESERVE, keccak256("unapproved"), block.timestamp);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
    }
    function testWrongPairAdmissionCannotExpandBuybackAuthority() public {
        _fund(address(input), GROSS); MockToken third = new MockToken(18);
        oracle.setTestFeed(address(third), address(inputFeed), 3600); rewards.addAsset(address(third));
        PoolConfig memory wrongConfig = _configuration(address(input), address(third));
        // Even the synthetic ERC20 fixture requires the immutable ZZZ identity.
        // Do not bypass admission to manufacture an obsolete approved wrong pair.
        wrongConfig.depositsEnabled = false;
        bytes32 wrongPool = keccak256(abi.encode(wrongConfig.key));
        bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(INVALID_CONFIGURATION); pools.configure(wrongConfig);
        assertFalse(pools.exists(wrongPool));
        assertEq(_ledger(address(input)), beforeState);
    }
    function testDisabledPoolStopsSwapWithoutBlockingClaimsOrDirectBurn() public {
        _fund(address(input), GROSS); _fund(address(zzz), GROSS);
        PoolConfig memory c = pools.get(pool); c.operationsEnabled = false; pools.configure(c);
        bytes32 beforeState = _ledger(address(input)); vm.expectRevert(INVALID_STATE); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
        _execute(address(zzz), RESERVE); _assertReserves(address(zzz), 0); _claimBoth(address(zzz));
    }
    function testManipulatedSpotRejectedByRealStrategyGuard() public {
        _fund(address(input), GROSS); state.setPrice(uint160((uint256(1) << 96) * 11 / 10));
        bytes32 beforeState = _ledger(address(input)); vm.expectRevert(bytes4(keccak256("Slippage()")));
        _execute(address(input), RESERVE); assertEq(_ledger(address(input)), beforeState);
        state.setPrice(uint160(1 << 96)); _execute(address(input), RESERVE); _assertReserves(address(input), 0);
    }
    function testPostSwapPriceDeviationRollsBackSettledSwapAndReserve() public {
        _fund(address(input), GROSS);
        core.setPostSwapPrice(address(state), uint160((uint256(1) << 96) * 11 / 10));
        bytes32 beforeState = _ledger(address(input)); vm.expectRevert(bytes4(keccak256("Slippage()")));
        _execute(address(input), RESERVE); assertEq(_ledger(address(input)), beforeState);
        _claimBoth(address(input)); core.setPostSwapPrice(address(0), 0);
        _execute(address(input), RESERVE); _assertReserves(address(input), 0);
    }
    function testExpiredAndOverlongDeadlineCannotReleaseReserve() public {
        _fund(address(input), GROSS); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(bytes4(keccak256("Expired()")));
        buyback.execute(address(input), RESERVE, pool, block.timestamp - 1);
        assertEq(_ledger(address(input)), beforeState);
        vm.expectRevert(bytes4(keccak256("Expired()")));
        buyback.execute(address(input), RESERVE, pool, block.timestamp + 601);
        assertEq(_ledger(address(input)), beforeState);
    }
    function testUnauthorizedCallerAndDirectReserveReleaseRejected() public {
        _fund(address(input), GROSS); bytes32 beforeState = _ledger(address(input));
        vm.prank(ALICE); vm.expectRevert(bytes4(keccak256("Unauthorized()"))); _execute(address(input), RESERVE);
        vm.prank(ALICE); vm.expectRevert(bytes4(keccak256("Unauthorized()"))); fees.releaseBuyback(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState);
    }
    function testPausedBuybackLeavesFundedClaimsAvailable() public {
        _fund(address(input), GROSS); access.setPaused(true); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(bytes4(keccak256("Paused()"))); _execute(address(input), RESERVE);
        assertEq(_ledger(address(input)), beforeState); _claimBoth(address(input));
        access.setPaused(false); _execute(address(input), RESERVE); _assertReserves(address(input), 0);
    }
    function testZeroOverReserveAndOverTradeBudgetRejected() public {
        _fund(address(input), GROSS); bytes32 beforeState = _ledger(address(input));
        vm.expectRevert(INVALID_AMOUNT); _execute(address(input), 0);
        vm.expectRevert(INVALID_AMOUNT); _execute(address(input), RESERVE + 1);
        vm.expectRevert(INVALID_AMOUNT); _execute(address(input), 101 ether);
        assertEq(_ledger(address(input)), beforeState);
    }
    function testBurnReentryCannotSpendASecondBudgetEvenWithKeeperRole() public {
        _fund(address(zzz), GROSS); access.setKeeper(address(zzz), true); zzz.setReentry(address(buyback));
        uint256 beforeSupply = zzz.totalSupply(); _execute(address(zzz), RESERVE);
        assertFalse(zzz.reentrySucceeded()); assertEq(zzz.reentryError(), REENTRY);
        assertEq(zzz.totalSupply(), beforeSupply - RESERVE); _assertReserves(address(zzz), 0); _claimBoth(address(zzz));
    }
    function testVenueReentryCannotSpendASecondBudgetEvenWithKeeperRole() public {
        _fund(address(input), GROSS); access.setKeeper(address(core), true); core.setReentry(address(buyback));
        uint256 beforeSupply = zzz.totalSupply(); _execute(address(input), RESERVE);
        assertFalse(core.reentrySucceeded()); assertEq(core.reentryError(), REENTRY);
        assertEq(core.swaps(), 1); assertEq(zzz.totalSupply(), beforeSupply - RESERVE);
        _assertReserves(address(input), 0); _claimBoth(address(input));
    }
    function testFuzzSplitBurnCannotConsumeIndividualOrCompoundReserve(uint96 rawAmount) public {
        uint256 amount = bound(uint256(rawAmount), 1, 1e17) * 20;
        _fund(address(zzz), amount); uint256 reserve = amount / 20; uint256 beforeSupply = zzz.totalSupply();
        uint256 first = reserve / 2;
        if (first != 0) _execute(address(zzz), first);
        _execute(address(zzz), reserve - first);
        assertEq(zzz.totalSupply(), beforeSupply - reserve); assertEq(fees.buybackBalance(address(zzz)), 0);
        assertEq(fees.compoundBalance(BUCKET, address(zzz)), reserve); assertEq(fees.accounted(address(zzz)), reserve);
        assertEq(zzz.balanceOf(address(fees)), reserve); assertEq(rewards.liabilities(address(zzz)), reserve * 18);
        vm.prank(ALICE); uint256 a = rewards.claim(1, address(zzz));
        vm.prank(BOB); uint256 b = rewards.claim(2, address(zzz));
        assertEq(a + b + rewards.liabilities(address(zzz)) + fees.accounted(address(zzz)) + reserve, amount);
        assertEq(zzz.balanceOf(address(rewards)), rewards.liabilities(address(zzz)));
    }
}
