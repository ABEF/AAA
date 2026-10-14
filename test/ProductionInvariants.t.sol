// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZPower} from "../src/ZZZPower.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockPools, MockFeed} from "./mocks/Mocks.sol";
import {VaultLiquidityMock, VaultPolicyMock} from "./VaultAccounting.t.sol";

/// @dev Internal accounting review only. These are real custody/reward modules
/// behind a FAKE liquidity venue, policy, token and access fixture. This does not
/// test real Uniswap, hostile dependencies, governance or cross-chain providers.
contract ProductionAccountingHandler is Test {
    uint256 private constant SCALE = 1e36;
    uint256 private constant MAX_NFTS = 8;
    address payable private constant TREASURY = payable(address(0x7EA5));

    MockAccess public access;
    MockToken[2] public tokens;
    MockPools public pools;
    VaultLiquidityMock public venue;
    ZZZVault public vault;
    ZZZNFT public nft;
    ZZZPower public power;
    ZZZRewards public rewards;
    ZZZFeeController public fees;
    ZZZCompounder public compounder;
    address[4] public actors;
    uint256[] public ids;
    bytes32 public poolId;

    mapping(uint256 => address) public expectedOwner;
    mapping(uint256 => uint256[2]) private contributed;
    mapping(uint256 => uint256[2]) private collected;
    mapping(uint256 => uint256[2]) private compounded;
    uint256[2] private totalCollected;
    uint256[2] private totalClaimed;
    uint256[2] private totalBuybackReleased;
    uint256[2][4] private donations; // Vault, venue, fees, rewards.

    // A separate, bounded integer reference model uses direct multiplication
    // and one quotient/remainder instead of the production mulDiv/mulmod paths.
    uint256 public modelTotalPower;
    uint256[2] private modelIndex;
    mapping(uint256 => uint256) private modelPower;
    mapping(uint256 => uint256[2]) private modelPaid;
    mapping(uint256 => uint256[2]) private modelFraction;
    mapping(uint256 => uint256[2]) private modelPersonal;
    mapping(uint256 => uint256[2]) private modelCollective;

    constructor() {
        vm.warp(1_000_000);
        access = new MockAccess();
        tokens[0] = new MockToken(0);
        tokens[1] = new MockToken(0);
        pools = new MockPools();
        VaultPolicyMock policy = new VaultPolicyMock();
        venue = new VaultLiquidityMock(address(tokens[0]), address(tokens[1]));
        vault = new ZZZVault(address(access), block.chainid, TREASURY);
        nft = new ZZZNFT(address(access), "");
        power = new ZZZPower(address(access));
        rewards = new ZZZRewards(address(access));
        fees = new ZZZFeeController(address(access));
        compounder = new ZZZCompounder(address(access));
        ZZZOracle oracle = new ZZZOracle(address(access), address(0));
        MockFeed feed = new MockFeed(8, 1e8);
        oracle.setFeed(address(tokens[0]), address(feed), 3600);
        oracle.setFeed(address(tokens[1]), address(feed), 3600);
        access.bind(Ids.VAULT, address(vault));
        access.bind(Ids.NFT, address(nft));
        access.bind(Ids.POWER, address(power));
        access.bind(Ids.REWARDS, address(rewards));
        access.bind(Ids.FEES, address(fees));
        access.bind(Ids.COMPOUNDER, address(compounder));
        access.bind(Ids.LIQUIDITY, address(venue));
        access.bind(Ids.STRATEGY, address(policy));
        access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.ORACLE, address(oracle));
        access.bind(Ids.BUYBACK, address(this));
        access.bind(Ids.RECEIVER, address(0x987));
        access.setKeeper(address(this), true);
        rewards.addAsset(address(tokens[0]));
        rewards.addAsset(address(tokens[1]));
        PoolConfig memory config;
        config.key = PoolKey(address(tokens[0]), address(tokens[1]), 3000, 60, address(0));
        config.operationsEnabled = true;
        config.depositsEnabled = true;
        config.minDepositUSD = 1e18;
        config.maxPositionUSD = 1e30;
        config.maxSlippageBps = 100;
        poolId = keccak256(abi.encode(config.key));
        pools.set(poolId, config);
        access.seal();
        actors = [address(0xA11CE), address(0xB0B), address(0xCA401), address(0xDA7E)];
        for (uint256 i; i < actors.length; ++i) {
            vm.deal(actors[i], 100 ether);
            tokens[0].mint(actors[i], 1e20);
            tokens[1].mint(actors[i], 1e20);
            vm.startPrank(actors[i]);
            tokens[0].approve(address(vault), type(uint256).max);
            tokens[1].approve(address(vault), type(uint256).max);
            vm.stopPrank();
        }
        mint(0);
        mint(1);
        activate(0, 1000, 1000);
    }

    function mint(uint256 ownerSeed) public {
        if (access.paused() || ids.length == MAX_NFTS) return;
        address owner = actors[ownerSeed % actors.length];
        vm.prank(owner);
        uint256 id = vault.mintDormant{value: 0.05 ether}();
        ids.push(id);
        expectedOwner[id] = owner;
        assertEq(power.powerOf(id), 0, "mint created Power");
        assertEq(vault.position(id).lpTokenId, 0, "mint created LP");
    }

    function _checkpoint(uint256 id) private {
        for (uint256 t; t < 2; ++t) {
            uint256 numerator = modelPower[id] * (modelIndex[t] - modelPaid[id][t]) + modelFraction[id][t];
            modelCollective[id][t] += numerator / SCALE;
            modelFraction[id][t] = numerator % SCALE;
            modelPaid[id][t] = modelIndex[t];
        }
    }

    function _contribute(uint256 id, uint256 amount0, uint256 amount1) private {
        contributed[id][0] += amount0;
        contributed[id][1] += amount1;
        uint256 increment = (amount0 + amount1) * 1e18;
        modelPower[id] += increment;
        modelTotalPower += increment;
    }

    function activate(uint256 idSeed, uint256 amount0, uint256 amount1) public {
        uint256 id = ids[idSeed % ids.length];
        if (access.paused() || vault.position(id).status != PositionStatus.Dormant) return;
        amount0 = bound(amount0, 500, 10000);
        amount1 = bound(amount1, 500, 10000);
        _checkpoint(id);
        vm.prank(expectedOwner[id]);
        vault.activate(id, poolId, amount0, amount1, 1, block.timestamp + 100);
        _contribute(id, amount0, amount1);
        for (uint256 t; t < 2; ++t) {
            assertEq(rewards.claimable(id, address(tokens[t])), 0, "activation gained historical fees");
        }
    }

    function topUp(uint256 idSeed, uint256 amount0, uint256 amount1) external {
        uint256 id = ids[idSeed % ids.length];
        if (access.paused() || vault.position(id).status != PositionStatus.Active) return;
        amount0 = bound(amount0, 1, 1000);
        amount1 = bound(amount1, 1, 1000);
        uint256[2] memory beforeClaims;
        for (uint256 t; t < 2; ++t) beforeClaims[t] = rewards.claimable(id, address(tokens[t]));
        _checkpoint(id);
        vm.prank(expectedOwner[id]);
        vault.increase(id, amount0, amount1, 1, block.timestamp + 100);
        _contribute(id, amount0, amount1);
        for (uint256 t; t < 2; ++t) {
            assertEq(rewards.claimable(id, address(tokens[t])), beforeClaims[t], "top-up repriced history");
        }
    }

    function harvest(uint256 idSeed, uint256 amount0, uint256 amount1) public {
        uint256 id = ids[idSeed % ids.length];
        if (access.paused() || vault.position(id).status != PositionStatus.Active) return;
        uint256[2] memory amounts = [bound(amount0, 0, 10000), bound(amount1, 0, 10000)];
        venue.setFees(amounts[0], amounts[1]);
        vault.collectFees(id, block.timestamp + 100);
        for (uint256 t; t < 2; ++t) {
            uint256 oldUnits = collected[id][t] / 10;
            collected[id][t] += amounts[t];
            totalCollected[t] += amounts[t];
            uint256 units = collected[id][t] / 10 - oldUnits;
            modelPersonal[id][t] += units * 5;
            modelIndex[t] += units * 3 * SCALE / modelTotalPower;
        }
    }

    function claim(uint256 idSeed, uint256 tokenSeed) public {
        uint256 id = ids[idSeed % ids.length];
        uint256 t = tokenSeed % 2;
        _checkpoint(id);
        uint256 expected = modelPersonal[id][t] + modelCollective[id][t];
        modelPersonal[id][t] = 0;
        modelCollective[id][t] = 0;
        address owner = expectedOwner[id];
        uint256 beforeBalance = tokens[t].balanceOf(owner);
        vm.prank(owner);
        uint256 paid = rewards.claim(id, address(tokens[t]));
        assertEq(paid, expected, "claim differs from independent integer model");
        assertEq(tokens[t].balanceOf(owner), beforeBalance + paid, "owner did not receive funded claim");
        totalClaimed[t] += paid;
    }

    function transfer(uint256 idSeed, uint256 ownerSeed) external {
        uint256 id = ids[idSeed % ids.length];
        address next = actors[ownerSeed % actors.length];
        vm.prank(expectedOwner[id]);
        nft.transferFrom(expectedOwner[id], next, id);
        expectedOwner[id] = next;
    }

    function setPaused(bool state) public { access.setPaused(state); }

    function donate(uint256 recipientSeed, uint256 tokenSeed, uint256 amount) external {
        uint256 r = recipientSeed % 4;
        uint256 t = tokenSeed % 2;
        amount = bound(amount, 1, 10000);
        address[4] memory recipients = [address(vault), address(venue), address(fees), address(rewards)];
        tokens[t].mint(recipients[r], amount);
        donations[r][t] += amount;
    }

    function compound(uint256 idSeed) external {
        uint256 id = ids[idSeed % ids.length];
        if (access.paused() || vault.position(id).status != PositionStatus.Active) return;
        uint256[2] memory budget;
        for (uint256 t; t < 2; ++t) budget[t] = fees.compoundBalance(id, address(tokens[t]));
        if (budget[0] + budget[1] == 0) return;
        compounder.compound(id, 1, block.timestamp + 100);
        for (uint256 t; t < 2; ++t) compounded[id][t] += budget[t];
    }

    function rebalance(uint256 idSeed) external {
        uint256 id = ids[idSeed % ids.length];
        if (access.paused() || vault.position(id).status != PositionStatus.Active) return;
        uint256[2] memory budget;
        for (uint256 t; t < 2; ++t) budget[t] = fees.compoundBalance(id, address(tokens[t]));
        uint256 oldLp = vault.position(id).lpTokenId;
        vault.rebalance(id, 1, block.timestamp + 100);
        assertTrue(vault.position(id).lpTokenId != oldLp, "rebalance retained burned LP");
        for (uint256 t; t < 2; ++t) compounded[id][t] += budget[t];
    }

    function releaseBuyback(uint256 tokenSeed, uint256 amount) external {
        if (access.paused()) return;
        uint256 t = tokenSeed % 2;
        uint256 budget = fees.buybackBalance(address(tokens[t]));
        if (budget == 0) return;
        amount = bound(amount, 1, budget);
        // This fixture is the designated buyback module. Verify reserve release;
        // real swapping/burning is covered separately, never assumed here.
        fees.releaseBuyback(address(tokens[t]), amount);
        totalBuybackReleased[t] += amount;
    }

    function assertConservation() public view {
        uint256[2] memory idle;
        uint256[2] memory lp;
        uint256[2] memory dust;
        uint256[2] memory compoundReserve;
        uint256[2] memory totalCompounded;
        uint256[2] memory grossBuyback;
        uint256[2] memory allClaims;
        for (uint256 i; i < ids.length; ++i) {
            uint256 id = ids[i];
            Position memory p = vault.position(id);
            assertEq(nft.ownerOf(id), expectedOwner[id], "ownership drift");
            assertEq(p.depositUSD, modelPower[id], "contribution attribution drift");
            assertEq(power.powerOf(id), modelPower[id], "Power drift");
            if (p.status == PositionStatus.Dormant) {
                assertEq(p.idle0 + p.idle1 + p.lpTokenId + p.depositUSD, 0, "dormant has principal");
            } else {
                assertEq(uint256(p.status), uint256(PositionStatus.Active), "unexpected local custody state");
                assertEq(venue.ownerOf(p.lpTokenId), address(vault), "LP custody drift");
            }
            for (uint256 t; t < 2; ++t) {
                uint256 positionIdle = t == 0 ? p.idle0 : p.idle1;
                uint256 positionLp = t == 0 ? venue.a0(p.lpTokenId) : venue.a1(p.lpTokenId);
                assertEq(positionIdle + positionLp, contributed[id][t] + compounded[id][t], "principal not conserved");
                idle[t] += positionIdle;
                lp[t] += positionLp;
                totalCompounded[t] += compounded[id][t];
                uint256 units = collected[id][t] / 10;
                uint256 expectedDust = collected[id][t] % 10;
                uint256 expectedCompound = units - compounded[id][t];
                assertEq(fees.dust(id, address(tokens[t])), expectedDust, "partition-dependent dust");
                assertEq(fees.compoundBalance(id, address(tokens[t])), expectedCompound, "compound reserve drift");
                dust[t] += expectedDust;
                compoundReserve[t] += expectedCompound;
                grossBuyback[t] += units;
                uint256 pendingNumerator = modelPower[id] * (modelIndex[t] - modelPaid[id][t]) + modelFraction[id][t];
                uint256 expectedClaim = modelPersonal[id][t] + modelCollective[id][t] + pendingNumerator / SCALE;
                assertEq(rewards.claimable(id, address(tokens[t])), expectedClaim, "reward index/model drift");
                allClaims[t] += expectedClaim;
            }
        }
        assertEq(vault.sequence(), ids.length, "issuance count drift");
        assertEq(TREASURY.balance, ids.length * 0.05 ether, "mint proceeds mixed with token funds");
        assertEq(address(vault).balance, 0, "mint payment retained as custody");
        assertEq(power.totalPower(), modelTotalPower, "total Power drift");
        for (uint256 t; t < 2; ++t) {
            address token = address(tokens[t]);
            uint256 buyback = grossBuyback[t] - totalBuybackReleased[t];
            assertEq(vault.totalIdle(token), idle[t], "idle aggregate not attributed");
            assertEq(tokens[t].balanceOf(address(vault)), idle[t] + donations[0][t], "vault donation contamination");
            assertEq(tokens[t].balanceOf(address(venue)), lp[t] + donations[1][t], "venue custody drift");
            assertEq(fees.buybackBalance(token), buyback, "buyback reserve drift");
            uint256 feeAccounted = dust[t] + compoundReserve[t] + buyback;
            assertEq(fees.accounted(token), feeAccounted, "fee ledger drift");
            assertEq(tokens[t].balanceOf(address(fees)), feeAccounted + donations[2][t], "fee donations became reserves");
            uint256 liabilities = rewards.liabilities(token);
            assertLe(allClaims[t], liabilities, "entitlements exceed funding");
            assertEq(rewards.orphaned(token), 0, "unexpected zero-Power allocation");
            assertEq(tokens[t].balanceOf(address(rewards)), liabilities + donations[3][t], "reward backing drift");
            assertEq(tokens[t].balanceOf(address(this)), totalBuybackReleased[t], "reserve release recipient drift");
            assertEq(totalCollected[t], feeAccounted + liabilities + totalClaimed[t] + totalCompounded[t]
                + totalBuybackReleased[t], "collected fees not conserved");
        }
    }
}

contract ProductionAccountingInvariantTest is Test {
    ProductionAccountingHandler private handler;

    function setUp() public {
        handler = new ProductionAccountingHandler();
        bytes4[] memory selectors = new bytes4[](11);
        selectors[0] = handler.mint.selector;
        selectors[1] = handler.activate.selector;
        selectors[2] = handler.topUp.selector;
        selectors[3] = handler.harvest.selector;
        selectors[4] = handler.claim.selector;
        selectors[5] = handler.transfer.selector;
        selectors[6] = handler.setPaused.selector;
        selectors[7] = handler.donate.selector;
        selectors[8] = handler.compound.selector;
        selectors[9] = handler.rebalance.selector;
        selectors[10] = handler.releaseBuyback.selector;
        targetContract(address(handler));
        targetSelector(FuzzSelector(address(handler), selectors));
    }

    function invariant_custodyFeesAndClaimsRemainConserved() public view { handler.assertConservation(); }

    function testPausedClaimAndDormantTransferKeepPublishedHistory() public {
        handler.harvest(0, 109, 217);
        handler.setPaused(true);
        handler.transfer(0, 3);
        handler.claim(0, 0);
        handler.claim(0, 1);
        handler.assertConservation();
        handler.setPaused(false);
        handler.transfer(1, 2);
        handler.activate(1, 1000, 1500);
        handler.topUp(0, 300, 400);
        handler.harvest(1, 211, 307);
        handler.compound(1);
        handler.rebalance(0);
        handler.claim(1, 1);
        handler.assertConservation();
    }
}
