// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed} from "./mocks/Mocks.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {IZZZStrategy} from "../src/interfaces/IZZZ.sol";

/// @dev Deliberately adversarial TEST ONLY venue. Exact transfers and honest
/// reported retained amounts isolate Vault's loss budget from venue minima.
/// Losses are removed from attributed LP amounts, never fabricated as backing.
contract BudgetAdversarialVenue is ERC721 {
    MockToken private immutable token0;
    MockToken private immutable token1;
    mapping(uint256 => uint256) public amount0;
    mapping(uint256 => uint256) public amount1;
    uint256 private nextId = 1;
    uint256 public closeLoss0;
    uint256 public closeLoss1;
    uint256 public mintLoss0;
    uint256 public mintLoss1;
    uint256 public spend0Bps = 10000;
    uint256 public spend1Bps = 10000;
    uint256 public swapOutput;
    uint256 public swapCount;
    uint256 public fee0;
    uint256 public fee1;
    uint256 private harvestLoss0;
    uint256 private harvestLoss1;
    MockFeed private mutateFeed;
    int256 private replacementPrice;
    bool private mutateOnMint;
    bool private mutateOnHarvest;
    address private reentryTarget;
    bytes private reentryData;
    bool public reentryAttempted;
    bool public reentrySucceeded;
    bytes4 public reentryError;
    bool private displaceMintOwner;

    constructor(address a, address b) ERC721("Adversarial budget venue", "ABV") {
        token0 = MockToken(a); token1 = MockToken(b);
    }
    function positionManager() external view returns (address) { return address(this); }
    function balanceContext(bytes32) external pure returns(bytes32){return bytes32(0);}
    function amounts(uint256 id) external view returns (uint256, uint256) { return (amount0[id], amount1[id]); }
    function losses(uint256 close0, uint256 close1, uint256 mint0, uint256 mint1) external {
        closeLoss0 = close0; closeLoss1 = close1; mintLoss0 = mint0; mintLoss1 = mint1;
    }
    function spending(uint256 a, uint256 b) external { spend0Bps = a; spend1Bps = b; }
    function setSwapOutput(uint256 value) external { swapOutput = value; }
    function setFees(uint256 a, uint256 b) external { fee0 = a; fee1 = b; }
    function harvestLosses(uint256 a, uint256 b) external { harvestLoss0 = a; harvestLoss1 = b; }
    function mutateAtHarvest(bool enabled) external { mutateOnHarvest = enabled; }
    function mutatePrice(MockFeed feed, int256 price, bool atMint) external {
        mutateFeed = feed; replacementPrice = price; mutateOnMint = atMint;
    }
    function reenter(address target, bytes calldata data) external { reentryTarget = target; reentryData = data; }
    function stealMintedLP(bool enabled) external { displaceMintOwner = enabled; }
    function _mutate() private {
        if (address(mutateFeed) != address(0)) mutateFeed.set(replacementPrice, block.timestamp, block.timestamp);
    }
    function mint(bytes32, int24, int24, uint256 a, uint256 b, uint128, uint256)
        external returns (uint256 id, uint256 used0, uint256 used1) {
        id = nextId++; _mint(msg.sender, id);
        used0 = a * spend0Bps / 10000; used1 = b * spend1Bps / 10000;
        require(token0.transferFrom(msg.sender, address(this), used0));
        require(token1.transferFrom(msg.sender, address(this), used1));
        amount0[id] = used0 - mintLoss0; amount1[id] = used1 - mintLoss1;
        // Burn modeled execution losses, ensuring final LP amounts are backed.
        token0.burn(mintLoss0); token1.burn(mintLoss1);
        if (mutateOnMint) _mutate();
        if (displaceMintOwner) _transfer(msg.sender, address(0xBAD), id);
    }
    function collect(bytes32, uint256 id, uint256) external {
        uint256 a = fee0; uint256 b = fee1; fee0 = 0; fee1 = 0;
        amount0[id] -= harvestLoss0; amount1[id] -= harvestLoss1;
        token0.burn(harvestLoss0); token1.burn(harvestLoss1);
        if (mutateOnHarvest) _mutate();
        token0.mint(msg.sender, a); token1.mint(msg.sender, b);
    }
    function close(bytes32, uint256 id, uint256) external {
        uint256 a = amount0[id] - closeLoss0; uint256 b = amount1[id] - closeLoss1;
        delete amount0[id]; delete amount1[id]; _burn(id);
        token0.burn(closeLoss0); token1.burn(closeLoss1);
        require(token0.transfer(msg.sender, a)); require(token1.transfer(msg.sender, b));
        if (!mutateOnMint) _mutate();
        if (reentryTarget != address(0)) {
            reentryAttempted = true;
            bytes memory result;
            (reentrySucceeded, result) = reentryTarget.call(reentryData);
            if (result.length >= 4) reentryError = bytes4(result);
        }
    }
    function balance(bytes32 pool,uint256,uint256 a,uint256 b,uint256 deadline)
        external returns(uint256 balanced0,uint256 balanced1) {
        IZZZStrategy strategy=IZZZStrategy(ZZZVault(payable(msg.sender)).access().module(Ids.STRATEGY));
        (bool direction,uint256 input,uint256 minimum)=strategy.swapPlan(pool,a,b);
        balanced0=a;balanced1=b;
        if(input!=0){
            require(direction&&input<=a);
            uint256 output=swap(pool,direction,input,minimum,deadline);
            balanced0-=input;balanced1+=output;
        }
    }
    function swap(bytes32, bool zeroForOne, uint256 input, uint256, uint256) public returns (uint256) {
        require(zeroForOne);
        ++swapCount;
        require(token0.transferFrom(msg.sender, address(this), input));
        token1.mint(msg.sender, swapOutput);
        return swapOutput;
    }
}

contract BudgetAdversarialPolicy {
    BudgetAdversarialVenue private venue;
    uint256 private amountIn;
    uint256 private plannedAtCount;
    // TEST ONLY: same-pair move/loss fixtures use no sampled timer. Keep
    // evidence/control stable; rebalance-specific subclasses supply readiness.
    function rebalanceReady(uint256) external pure virtual returns(bool){return false;}
    function rebalanceConfirmation() external view returns(address){return address(this);}
    function controlFingerprint(bytes32) external pure returns(bytes32){return keccak256("adversarial-budget fixture controls");}
    function observationFingerprint(uint256,bytes32) external pure returns(bytes32){
        return keccak256(abi.encode(keccak256("adversarial-budget fixture controls"),bytes32(0),uint64(0),uint64(0),uint8(0)));
    }
    function observations(uint256) external pure returns(bytes32,uint64,uint64,uint8){return(bytes32(0),0,0,0);}
    function observeVenue(BudgetAdversarialVenue observed) external { venue = observed; }
    function setSwapAmount(uint256 value) external { amountIn = value; plannedAtCount = venue.swapCount(); }
    function validatePrice(bytes32) external pure returns (uint160) { return uint160(1 << 96); }
    function validateExitPrice(bytes32) external pure returns (uint160) { return uint160(1 << 96); }
    function target(bytes32) external pure returns (int24, int24, uint160) { return (-600, 600, uint160(1 << 96)); }
    // The old synthetic plan prescribed one deliberate swap. Repeating its
    // fixed amount on a reconciliation pass would invent a second unrelated loss.
    function swapPlan(bytes32, uint256, uint256) external view returns (bool, uint256, uint256) {
        return (true, amountIn != 0 && venue.swapCount() == plannedAtCount ? amountIn : 0, 1);
    }
}

/// @notice Real Vault/rewards/accounting with fake authority, venue and feeds.
/// These tests establish local accounting behavior, not async bridge guarantees,
/// production dependency integrity, swap execution or target-chain gas costs.
contract MigrationBudgetAdversarialTest is PooledVaultFixture {
    BudgetAdversarialVenue private adversary;
    BudgetAdversarialPolicy private adversePolicy;

    function _setupAdversary() private {
        adversary = new BudgetAdversarialVenue(address(t0), address(t1));
        adversePolicy = new BudgetAdversarialPolicy(); adversePolicy.observeVenue(adversary);
        ac.bind(Ids.LIQUIDITY, address(adversary)); ac.bind(Ids.STRATEGY, address(adversePolicy));
    }
    function _destination() private returns (bytes32 nextPool) {
        PoolConfig memory c = pools.get(poolId); c.key.fee = 500;
        nextPool = keccak256(abi.encode(c.key)); pools.set(nextPool, c);
    }
    function _move(bytes32 nextPool) private { vault.movePool(_bucket(), nextPool, 1, block.timestamp + 100); }
    function _assertUnchanged(Position memory beforePosition, bytes32 nextPool, uint256 nftId, uint256 shares) private view {
        Position memory afterPosition = vault.group(_bucket());
        assertEq(afterPosition.poolId, beforePosition.poolId); assertEq(afterPosition.lpTokenId, beforePosition.lpTokenId);
        assertEq(afterPosition.idle0, beforePosition.idle0); assertEq(afterPosition.idle1, beforePosition.idle1);
        assertEq(uint8(afterPosition.status), uint8(beforePosition.status));
        assertEq(vault.poolBucket(nextPool), 0); assertEq(vault.bucketCount(), 1);
        assertEq(vault.sharesOf(nftId), shares); assertEq(adversary.ownerOf(beforePosition.lpTokenId), address(vault));
        assertEq(t0.allowance(address(vault), address(adversary)), 0);
        assertEq(t1.allowance(address(vault), address(adversary)), 0);
    }
    function testBudgetRejectsStackedCloseSwapAndMintLossAtomicallyThenAllowsRetry() public {
        _setupAdversary(); uint256 id = activatedPosition(); bytes32 nextPool = _destination();
        Position memory beforePosition = vault.group(_bucket()); uint256 shares = vault.sharesOf(id);
        adversary.losses(20, 20, 5, 5); adversePolicy.setSwapAmount(100); adversary.setSwapOutput(82);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool); // 40 + 18 + 10 > 60.
        _assertUnchanged(beforePosition, nextPool, id, shares);
        adversary.setSwapOutput(90); _move(nextPool); // 40 + 10 + 10 = 60, exactly 3%.
        Position memory moved = vault.group(_bucket());
        assertEq(adversary.amount0(moved.lpTokenId) + adversary.amount1(moved.lpTokenId), 1940);
        assertEq(vault.sharesOf(id), shares); assertEq(vault.poolBucket(nextPool), _bucket());
    }
    function testFreshHarvestCompoundEntersDenominatorInsteadOfMaskingCloseLoss() public {
        _setupAdversary(); uint256 id = activatedPosition(); bytes32 nextPool = _destination();
        Position memory beforePosition = vault.group(_bucket()); uint256 shares = vault.sharesOf(id);
        adversary.setFees(1000, 1000); adversary.losses(40, 40, 0, 0);
        // The designated 50 + 50 compound increases the starting value to 2100.
        // The retained 2020 exceeds old principal, but is below ceil(2100 * .97).
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool);
        _assertUnchanged(beforePosition, nextPool, id, shares);
        assertEq(adversary.fee0(), 1000); assertEq(fees.compoundBalance(_bucket(), address(t0)), 0);
        assertEq(rewards.claimable(id, address(t0)), 0);
    }
    function testFundedRewardBuybackAndPriorDonationsCannotSubsidizePrincipalLoss() public {
        _setupAdversary(); uint256 id = activatedPosition(); bytes32 nextPool = _destination();
        adversary.setFees(1000, 1000); vault.collectFees(_bucket(), block.timestamp + 100);
        t0.mint(address(vault), 777); t1.mint(address(vault), 888);
        uint256 rewardBefore = rewards.claimable(id, address(t0));
        uint256 reserveBefore = fees.buybackBalance(address(t0));
        uint256 vaultBefore0 = t0.balanceOf(address(vault)); uint256 vaultBefore1 = t1.balanceOf(address(vault));
        adversary.losses(40, 40, 0, 0);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool);
        assertEq(rewards.claimable(id, address(t0)), rewardBefore); assertEq(fees.buybackBalance(address(t0)), reserveBefore);
        assertEq(fees.compoundBalance(_bucket(), address(t0)), 50);
        assertEq(t0.balanceOf(address(vault)), vaultBefore0); assertEq(t1.balanceOf(address(vault)), vaultBefore1);
    }
    function testCloseCallbackDoublingOraclePricesCannotEraseFourPercentLoss() public {
        _setupAdversary(); activatedPosition(); bytes32 nextPool = _destination();
        MockFeed feed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(t0), address(feed), 3600); oracle.setTestFeed(address(t1), address(feed), 3600);
        adversary.mutatePrice(feed, 2e8, false); adversary.losses(40, 40, 0, 0);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool);
        assertEq(feed.answer(), 1e8); assertEq(vault.group(_bucket()).poolId, poolId);
    }
    function testHarvestCallbackPrincipalLossAndPriceChangeCannotPrecedeStartingSnapshot() public {
        _setupAdversary(); uint256 id = activatedPosition(); bytes32 nextPool = _destination();
        Position memory beforePosition = vault.group(_bucket()); uint256 shares = vault.sharesOf(id);
        MockFeed feed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(t0), address(feed), 3600); oracle.setTestFeed(address(t1), address(feed), 3600);
        // The initial implementation took its snapshot after this stateful call:
        // it would accept the already diminished 1920 as the starting principal.
        adversary.harvestLosses(40, 40); adversary.mutatePrice(feed, 2e8, false); adversary.mutateAtHarvest(true);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool);
        _assertUnchanged(beforePosition, nextPool, id, shares); assertEq(feed.answer(), 1e8);
        assertEq(adversary.amount0(beforePosition.lpTokenId), 1000);
        assertEq(adversary.amount1(beforePosition.lpTokenId), 1000);
    }
    function testMintCallbackPriceChangeCannotHideExcessAttributedIdle() public {
        _setupAdversary(); activatedPosition(); bytes32 nextPool = _destination();
        MockFeed feed = new MockFeed(8, 1e8); oracle.setTestFeed(address(t0), address(feed), 3600);
        adversePolicy.setSwapAmount(899); adversary.setSwapOutput(899); adversary.spending(0, 10000);
        adversary.mutatePrice(feed, 1e6, true);
        // Dynamic prices see 1.01 idle + 1899 LP; cached prices see 101/2000 idle.
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool);
        assertEq(feed.answer(), 1e8); assertEq(vault.group(_bucket()).idle0, 0);
    }
    function testBudgetCountsAttributedIdleAndAllowsExactFivePercentIdle() public {
        _setupAdversary(); uint256 id = activatedPosition(); bytes32 nextPool = _destination();
        adversePolicy.setSwapAmount(900); adversary.setSwapOutput(900); adversary.spending(0, 10000);
        _move(nextPool); Position memory p = vault.group(_bucket());
        assertEq(p.idle0, 100); assertEq(p.idle1, 0); assertEq(adversary.amount1(p.lpTokenId), 1900);
        assertEq(vault.totalIdle(address(t0)), 100); assertEq(vault.sharesOf(id), 2000e18);
    }
    function testBudgetRoundsRequiredRetentionUpAtOneWeiBoundary() public {
        _setupAdversary(); uint256 id = _mint(alice); _activate(alice, id, 100, 101); bytes32 nextPool = _destination();
        MockFeed feed = new MockFeed(18, 1);
        oracle.setTestFeed(address(t0), address(feed), 3600); oracle.setTestFeed(address(t1), address(feed), 3600);
        adversary.losses(4, 3, 0, 0);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool); // 194 < ceil(201 * .97) = 195.
        adversary.losses(3, 3, 0, 0); _move(nextPool);
        Position memory p = vault.group(_bucket()); assertEq(adversary.amount0(p.lpTokenId) + adversary.amount1(p.lpTokenId), 195);
    }
    function testBudgetWeightsLossByCachedAssetPricesRatherThanRawTokenTotals() public {
        _setupAdversary(); activatedPosition(); bytes32 nextPool = _destination();
        MockFeed dearer = new MockFeed(8, 10e8); oracle.setTestFeed(address(t0), address(dearer), 3600);
        // 34 raw units are only 1.7% of token counts, but $340 exceeds the $330 budget.
        adversary.losses(0, 0, 34, 0);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); _move(nextPool);
        adversary.losses(0, 0, 33, 0); _move(nextPool);
        Position memory p = vault.group(_bucket());
        assertEq(adversary.amount0(p.lpTokenId), 967); assertEq(adversary.amount1(p.lpTokenId), 1000);
    }
    function testBudgetResumeStartsFromParkedPrincipalAndRollsBackBadMint() public {
        _setupAdversary(); uint256 id = activatedPosition(); uint256 shares = vault.sharesOf(id);
        ac.setPaused(true); vault.park(_bucket(), block.timestamp + 100); ac.setPaused(false);
        adversary.losses(0, 0, 31, 30);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); vault.resume(_bucket(), poolId, 1, block.timestamp + 100);
        Position memory parked = vault.group(_bucket());
        assertEq(uint8(parked.status), uint8(PositionStatus.Parked)); assertEq(parked.lpTokenId, 0);
        assertEq(parked.idle0, 1000); assertEq(parked.idle1, 1000); assertEq(vault.sharesOf(id), shares);
        adversary.losses(0, 0, 30, 30); vault.resume(_bucket(), poolId, 1, block.timestamp + 100);
        assertEq(uint8(vault.group(_bucket()).status), uint8(PositionStatus.Active)); assertEq(vault.sharesOf(id), shares);
    }
    function testBudgetMigrationBlocksCloseCallbackReentry() public {
        _setupAdversary(); activatedPosition(); bytes32 nextPool = _destination();
        adversary.reenter(address(vault), abi.encodeCall(vault.collectFees, (_bucket(), block.timestamp + 100)));
        _move(nextPool);
        assertTrue(adversary.reentryAttempted()); assertFalse(adversary.reentrySucceeded());
        assertEq(adversary.reentryError(), bytes4(keccak256("ReentrancyGuardReentrantCall()")));
    }
    function testBudgetRetainsFinalLPCustodyCheck() public {
        _setupAdversary(); uint256 id = activatedPosition(); bytes32 nextPool = _destination();
        Position memory beforePosition = vault.group(_bucket()); uint256 shares = vault.sharesOf(id);
        adversary.stealMintedLP(true);
        vm.expectRevert(); _move(nextPool);
        _assertUnchanged(beforePosition, nextPool, id, shares);
    }
    function testBudgetCannotBeArmedOrFinalizedByAnotherCaller() public {
        _setupAdversary(); activatedPosition(); ZZZMigrationBudget budget = vault.migrationBudget();
        assertEq(budget.vault(), address(vault));
        for (uint8 phase; phase < 3; ++phase) {
            vm.expectRevert(ZZZMigrationBudget.Unauthorized.selector); budget.checkpoint(_bucket(), phase);
        }
        _move(_destination());
    }
}
