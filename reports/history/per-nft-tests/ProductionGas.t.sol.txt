// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZPower} from "../src/ZZZPower.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockPools, MockFeed} from "./mocks/Mocks.sol";
import {VaultPolicyMock, VaultLiquidityMock} from "./VaultAccounting.t.sol";

/// @notice Reproducible cold-account/slot execution-gas scaling workloads.
/// Profile: solc 0.8.26, Cancun, via-IR, optimizer runs 1, Yul disabled.
/// Real Vault/NFT/Power/Rewards/FeeController/Oracle; mock access, tokens,
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
    ZZZPower private power;
    ZZZRewards private rewards;
    ZZZFeeController private fees;
    ZZZOracle private oracle;
    MockToken[] private tokens;
    bytes32 private poolId;
    address private constant OWNER = address(0xA11CE);
    address payable private constant TREASURY = payable(address(0x7EA5));

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
        power = new ZZZPower(address(access));
        rewards = new ZZZRewards(address(access));
        fees = new ZZZFeeController(address(access));
        oracle = new ZZZOracle(address(access), address(0));
        oracle.setFeed(address(tokens[0]), address(feed), 3600);
        oracle.setFeed(address(tokens[1]), address(feed), 3600);
        access.bind(Ids.VAULT, address(vault));
        access.bind(Ids.NFT, address(nft));
        access.bind(Ids.POWER, address(power));
        access.bind(Ids.REWARDS, address(rewards));
        access.bind(Ids.FEES, address(fees));
        access.bind(Ids.LIQUIDITY, address(venue));
        access.bind(Ids.STRATEGY, address(policy));
        access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.ORACLE, address(oracle));
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
        vm.cool(address(access));
        vm.cool(address(vault));
        vm.cool(address(nft));
        vm.cool(address(power));
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
        vault.collectFees(id, block.timestamp + 100);
        spent = start - gasleft();
        _report(prefix, "harvest", spent);

        _cool();
        // Isolate the real checkpoint implementation without changing contribution Power.
        vm.prank(address(power));
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

    function testGasMaximum32FundedRewardAssets() public {
        uint256 id = _runCollectionWorkload(1000, 32);
        // Model funded balances retained across historical pools/routes. Only the
        // bound fee module is impersonated to fund the real reward ledger for all
        // assets; this does not pretend one pool produces 32 different currencies.
        for (uint256 i; i < tokens.length; ++i) {
            tokens[i].mint(address(fees), 800_000);
            vm.startPrank(address(fees));
            tokens[i].approve(address(rewards), 800_000);
            rewards.credit(id, address(tokens[i]), 500_000, 300_000);
            vm.stopPrank();
        }
        _cool();
        vm.prank(address(power));
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
        // There is no production bulk-claim ABI. This is 32 calls in one local
        // transaction; shared warm accesses make it cheaper than 32 transactions.
        _report("collection.1000.assets.32.funded", "claim32BatchedCalls", spent);
        assertEq(rewards.assetCount(), 32);
    }
}
