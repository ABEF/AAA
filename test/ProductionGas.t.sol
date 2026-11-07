// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

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
        access = new MockAccess(); ProtocolPolicyFixture.bind(address(access));
        pools = new MockPools();
        policy = new VaultPolicyMock();
        feed = new MockFeed(8, 1e8);
        require(assetCount==2);tokens.push(MockToken(address(0)));tokens.push(new MockToken(0));
        venue = new VaultLiquidityMock(address(tokens[0]), address(tokens[1]));
        ProtocolPolicyFixture.recipient(address(access),TREASURY);vault=new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        nft = new ZZZNFT(address(access), ""); nft.setMintEnd(uint64(block.timestamp + 3650 days));
        vrf = new MockVRF();
        ProtocolPolicyFixture.randomness(address(nft.access()),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        membership = new ZZZMembership(address(access));
        rewards = new ZZZRewards(address(access));
        fees = new ZZZFeeController(address(access));
        oracle = new ZZZOracle(address(access), address(0));
        oracle.setTestFeed(address(0),address(new MockFeed(8,1e26)),3600);
        oracle.setTestFeed(address(tokens[1]), address(feed), 3600);
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
        access.bind(keccak256("ZZZMigrationReceiver"), address(0x987));
        pools.setFixedZZZ(address(tokens[1]));rewards.addAsset(address(tokens[1]));
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

        tokens[1].mint(OWNER, 10_000_000);
        vm.startPrank(OWNER);

        tokens[1].approve(address(vault), type(uint256).max);
        vm.stopPrank();
    }

    function _cool() private {
        // Include every account reached by the workload, not merely the entrypoint.
        vm.cool(address(oracle.contributionPricing()));
        for (uint256 i; i < tokens.length; ++i) {
            bytes32 id=oracle.activePolicy(address(tokens[i]));
            if(id!=bytes32(0)) {
                ZZZOracle.DualPolicy memory p=oracle.policy(id);
                vm.cool(p.primary.source);vm.cool(p.secondary.source);
            }
        }
        vm.cool(address(vault.migrationBudget()));
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
        // Policy/getter observations above must not warm the measured Oracle.
        vm.cool(address(oracle));
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
            bytes32 reviewedPolicy2 = vault.mintPolicyFingerprint(); uint256 previous = vault.mintDormant{value: 0.05 ether}(reviewedPolicy2);
            vm.stopPrank();
            _finalizeTraits(previous);
            vm.startPrank(OWNER);
            vault.activate{value:1000}(previous, poolId, 1000, 1000, 1, block.timestamp + 100);
            vm.stopPrank();
        }
        vm.resumeGasMetering();
        string memory prefix = string.concat("collection.", vm.toString(size), ".assets.", vm.toString(assetCount));
        _cool();
        vm.prank(OWNER);
        uint256 start = gasleft();
        bytes32 reviewedPolicy1 = vault.mintPolicyFingerprint(); id = vault.mintDormant{value: 0.05 ether}(reviewedPolicy1);
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
        vault.activate{value:1000}(id, poolId, 1000, 1000, 1, block.timestamp + 100);
        spent = start - gasleft();
        _report(prefix, "activate", spent);

        venue.setFees(1000, 1000);
        _cool();
        vm.prank(OWNER);
        start = gasleft();
        vault.increase{value:100}(id, 100, 100, 1, block.timestamp + 100);
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

        start = gasleft();
        rewards.claimableComponents(id,address(0));
        spent = start - gasleft();
        _report(prefix, "claimableComponents", spent);

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

    /// @notice Fresh profile7 has exactly native ETH and fixed ZZZ, not32 LP assets.
    function testGasMaximumTwoFundedLPBooks()public{
        uint256 id=_runCollectionWorkload(1000,2);uint256 bucket=vault.nftBucket(id);
        vm.deal(address(fees),address(fees).balance+900_000);
        vm.prank(address(fees));rewards.creditPool{value:900_000}(bucket,address(0),800_000,100_000);
        tokens[1].mint(address(fees),900_000);
        vm.startPrank(address(fees));tokens[1].approve(address(rewards),900_000);
        rewards.creditPool(bucket,address(tokens[1]),800_000,100_000);vm.stopPrank();
        _cool();uint256 start=gasleft();rewards.claimableComponents(id,address(0));
        _report("collection.1000.assets.2.funded","claimableComponents",start-gasleft());
        _cool();vm.startPrank(OWNER);start=gasleft();
        uint256 ethClaim=rewards.claim(id,address(0));uint256 zzzClaim=rewards.claim(id,address(tokens[1]));
        uint256 spent=start-gasleft();vm.stopPrank();
        assertGt(ethClaim,0);assertGt(zzzClaim,0);assertEq(rewards.assetCount(),2);
        _report("collection.1000.assets.2.funded","claimTwoBatchedCalls",spent);
    }
}
