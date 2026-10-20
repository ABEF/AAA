// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockPools, MockFeed} from "./mocks/Mocks.sol";
import {VaultPolicyMock, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

/// @notice Reproducible cold-account/slot execution-gas scaling workloads.
/// Profile: solc 0.8.26, Cancun, via-IR, optimizer runs 1, Yul disabled.
/// Real Vault/NFT/Membership/Rewards/FeeController/Oracle; mock access, tokens,
/// feeds, strategy and liquidity venue. No live valuation or network execution.
/// gasleft deltas exclude fixture construction, transaction intrinsic/calldata
/// gas and post-transaction refunds. Mock venue costs are not Uniswap gas costs.
contract ProductionGasTest is Test {
    MockAccess private access;
    MockPools private pools;
    MockFeed private feed;
    VaultPolicyMock private policy;
    VaultLiquidityMock private venue;
    ZZZVault private vault;
    ZZZNFT private nft;
    MockVRF private vrf;
    ZZZMembership private membership;
    ZZZRewards private rewards;
    ZZZFeeController private fees;
    ZZZOracle private oracle;
    MockToken[] private tokens;
    bytes32 private poolId;
    address private constant OWNER = address(0xA11CE);
    address payable private constant TREASURY = payable(address(0x7EA5));

    function activePlan(uint256) external pure returns(bytes32) {return bytes32(0);}
    function _fixture(uint256 assetCount) private {
        vm.warp(1_000_000);
        access = new MockAccess();
        pools = new MockPools();
        policy = new VaultPolicyMock();
        feed = new MockFeed(8, 1e8);
        for (uint256 i; i < assetCount; ++i) tokens.push(new MockToken(0));
        venue = new VaultLiquidityMock(address(tokens[0]), address(tokens[1]));
        vault = new ZZZVault(address(access), block.chainid, TREASURY);
        nft = new ZZZNFT(address(access), "");
        vrf = new MockVRF();
        nft.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        membership = new ZZZMembership(address(access));
        rewards = new ZZZRewards(address(access));
        fees = new ZZZFeeController(address(access));
        oracle = new ZZZOracle(address(access), address(0));
        oracle.setFeed(address(tokens[0]), address(feed), 3600);
        oracle.setFeed(address(tokens[1]), address(feed), 3600);
        access.bind(Ids.VAULT, address(vault));
        access.bind(Ids.NFT, address(nft));
        access.bind(Ids.MEMBERSHIP, address(membership));
        access.bind(Ids.REWARDS, address(rewards));
        access.bind(Ids.FEES, address(fees));
        access.bind(Ids.LIQUIDITY, address(venue));
        access.bind(Ids.STRATEGY, address(policy));
        access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.ORACLE, address(oracle));
        access.bind(Ids.MIGRATION, address(this));
        access.setKeeper(address(this),true);
        access.bind(Ids.RECEIVER, address(0x987));
        for (uint256 i; i < assetCount; ++i) rewards.addAsset(address(tokens[i]));
        PoolConfig memory c;
        c.key = PoolKey(address(tokens[0]), address(tokens[1]), 3000, 60, address(0));
        c.depositsEnabled = true;
        c.operationsEnabled = true;
        c.minDepositUSD = 1 ether;
        c.maxPositionUSD = 1e30;
        c.maxSlippageBps = 100;
        poolId = keccak256(abi.encode(c.key));
        pools.set(poolId, c);
        CanonicalFixture.bind(address(access));
        access.seal();
        vm.deal(OWNER, 100 ether);
        tokens[0].mint(OWNER, 10_000_000);
        tokens[1].mint(OWNER, 10_000_000);
        vm.startPrank(OWNER);
        tokens[0].approve(address(vault), type(uint256).max);
        tokens[1].approve(address(vault), type(uint256).max);
        vm.stopPrank();
    }

    function _cool() private {
        // Include every account reached by the workload, not merely the entrypoint.
        vm.cool(address(vault.migrationBudget())); vm.cool(address(fees.receiverFactory()));
        vm.cool(address(access));
        vm.cool(address(vault));
        vm.cool(address(nft.royaltyRewards()));
        vm.cool(address(nft.metadataRenderer()));
        vm.cool(address(vrf));
        vm.cool(address(membership));
        vm.cool(address(rewards));
        vm.cool(address(fees));
        vm.cool(address(oracle));
        vm.cool(address(pools));
        vm.cool(address(policy));
        vm.cool(address(venue));
        vm.cool(address(feed));
        vm.cool(TREASURY);
        vm.cool(OWNER);
        for (uint256 i; i < tokens.length; ++i) vm.cool(address(tokens[i]));
        // Helper getters above touch the NFT; cool it after those reads.
        vm.cool(address(nft));
        vm.cool(access.module(Ids.CANONICAL)); vm.cool(access.module(Ids.NFT_CANONICAL));
        vm.cool(access.module(Ids.VAULT_CANONICAL)); vm.cool(access.module(Ids.FEES_CANONICAL));
        // Reading companion bindings warms the controller; cool it last.
        vm.cool(address(access));
    }

    function _report(string memory prefix, string memory operation, uint256 spent) private {
        emit log_named_uint(string.concat(prefix, ".", operation), spent);
    }

    function _runCollectionWorkload(uint256 size, uint256 assetCount) private returns (uint256 id) {
        // Seed existing active positions outside measured execution and outside the
        // test transaction's gas budget. No production gas limit is changed.
        vm.pauseGasMetering();
        _fixture(assetCount);
        for (uint256 i = 1; i < size; ++i) {
            vm.startPrank(OWNER);
            uint256 previous = vault.mintDormant{value: 0.05 ether}();
            vm.stopPrank();
            _finalizeTraits(previous);
            vm.startPrank(OWNER);
            vault.activate(previous, poolId, 1000, 1000, 1, block.timestamp + 100);
            vm.stopPrank();
        }
        vm.resumeGasMetering();
        string memory prefix = string.concat("collection.", vm.toString(size), ".assets.", vm.toString(assetCount));
        _cool();
        vm.prank(OWNER);
        uint256 start = gasleft();
        id = vault.mintDormant{value: 0.05 ether}();
        uint256 spent = start - gasleft();
        _report(prefix, "mintDormant", spent);
        assertEq(nft.balanceOf(OWNER), size);

        // Coordinator fulfillment and trait finalization are separate execution,
        // excluded from dormant-mint and activation measurements alike.
        vm.pauseGasMetering();
        _finalizeTraits(id);
        vm.resumeGasMetering();

        _cool();
        vm.prank(OWNER);
        start = gasleft();
        vault.activate(id, poolId, 1000, 1000, 1, block.timestamp + 100);
        spent = start - gasleft();
        _report(prefix, "activate", spent);

        venue.setFees(1000, 1000);
        _cool();
        vm.prank(OWNER);
        start = gasleft();
        vault.increase(id, 100, 100, 1, block.timestamp + 100);
        spent = start - gasleft();
        _report(prefix, "topUpWithFeeCheckpoint", spent);

        venue.setFees(1000, 1000);
        _cool();
        start = gasleft();
        vault.collectFees(vault.nftBucket(id), block.timestamp + 100);
        spent = start - gasleft();
        _report(prefix, "harvest", spent);

        _cool();
        start = gasleft();
        vault.rebalance(vault.nftBucket(id), 1, block.timestamp + 100);
        spent = start - gasleft();
        _report(prefix, "sharedPoolRebalance", spent);
        assertEq(vault.bucketCount(), 1);
        assertEq(venue.next(), 3); // One initial mint, one replacement, regardless of NFT count.

        _cool();
        // Isolate checkpoint execution without changing equal NFT membership.
        vm.prank(address(membership));
        start = gasleft();
        rewards.checkpointAll(id);
        spent = start - gasleft();
        _report(prefix, "checkpointAll", spent);

        _cool();
        vm.prank(OWNER);
        start = gasleft();
        uint256 claimed = rewards.claim(id, address(tokens[0]));
        spent = start - gasleft();
        _report(prefix, "claimOneAsset", spent);
        assertGt(claimed, 0, "Benchmark must exercise a funded claim");
    }

    function testGasCollection1() public { _runCollectionWorkload(1, 2); }
    function testGasCollection100() public { _runCollectionWorkload(100, 2); }
    function testGasCollection1000() public { _runCollectionWorkload(1000, 2); }

    function _finalizeTraits(uint256 id) private {
        vrf.fulfill(nft.requestOf(id), 1, 1);
        nft.finalizeTraits(id);
    }

    function testGasMaximum32FundedRewardAssets() public {
        uint256 id = _runCollectionWorkload(1000, 32);
        // Model funded balances retained across historical pools/routes. Only the
        // bound fee module is impersonated to fund the real reward ledger for all
        // assets; this does not pretend one pool produces 32 different currencies.
        for (uint256 i; i < tokens.length; ++i) {
            tokens[i].mint(address(fees), 900_000);
            vm.startPrank(address(fees));
            tokens[i].approve(address(rewards), 900_000);
            rewards.creditPool(vault.nftBucket(id), address(tokens[i]), 800_000, 100_000);
            vm.stopPrank();
        }
        _cool();
        vm.prank(address(membership));
        uint256 start = gasleft();
        rewards.checkpointAll(id);
        uint256 spent = start - gasleft();
        _report("collection.1000.assets.32.funded", "checkpointAll", spent);

        _cool();
        vm.startPrank(OWNER);
        start = gasleft();
        for (uint256 i; i < tokens.length; ++i) rewards.claim(id, address(tokens[i]));
        spent = start - gasleft();
        vm.stopPrank();
        // This benchmark performs 32 raw calls, not the production claim router.
        // Shared warm accesses make it cheaper than 32 separate transactions;
        // ClaimRouter.t.sol independently measures its bounded 32-operation ABI.
        _report("collection.1000.assets.32.funded", "claim32BatchedCalls", spent);
        assertEq(rewards.assetCount(), 33);
    }
}
