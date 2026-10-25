// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockPools, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {VaultPolicyMock} from "./VaultAccounting.t.sol";

/// @dev TEST ONLY: mutable balance-query fault confined to the royalty ledger.
/// Transfers, LP/price reads and historical backing remain conventional. INVALID
/// consumes the forwarded token-read gas, exercising the isolated self-call cap.
contract CapacityRoyaltyFaultToken is MockToken {
    address private failingReader;
    constructor() MockToken(0) {}
    function setFailingReader(address reader) external { failingReader = reader; }
    function balanceOf(address owner) public view override returns (uint256) {
        if (msg.sender == failingReader) assembly ("memory-safe") { invalid() }
        return super.balanceOf(owner);
    }
}

/// @dev TEST ONLY: multi-pair venue that deploys every contributed token unit.
/// It models custody and fee separation, not Uniswap execution or production gas.
contract CombinedCapacityVenue is ERC721 {
    MockPools private immutable pools;
    mapping(uint256 => uint256) private amount0;
    mapping(uint256 => uint256) private amount1;
    mapping(bytes32 => uint256) private fee;
    uint256 private next = 1;

    constructor(MockPools registry) ERC721("Combined-capacity mock", "CCM") { pools = registry; }
    function positionManager() external view returns (address) { return address(this); }
    function amounts(uint256 id) external view returns (uint256, uint256) { return (amount0[id], amount1[id]); }
    function setFees(bytes32 pool, uint256 value) external { fee[pool] = value; }
    function mint(bytes32 pool, int24, int24, uint256 a0, uint256 a1, uint128, uint256)
        external returns (uint256 id, uint256 spent0, uint256 spent1) {
        id = next++;
        _mint(msg.sender, id);
        (spent0, spent1) = _fund(pool, id, a0, a1);
    }
    function increase(bytes32 pool, uint256 id, uint256 a0, uint256 a1, uint128, uint256)
        external returns (uint256, uint256) {
        require(ownerOf(id) == msg.sender);
        return _fund(pool, id, a0, a1);
    }
    function _fund(bytes32 pool, uint256 id, uint256 a0, uint256 a1) private returns (uint256, uint256) {
        PoolConfig memory config = pools.get(pool);
        require(IERC20(config.key.currency0).transferFrom(msg.sender, address(this), a0));
        require(IERC20(config.key.currency1).transferFrom(msg.sender, address(this), a1));
        amount0[id] += a0;
        amount1[id] += a1;
        return (a0, a1);
    }
    function collect(bytes32 pool, uint256, uint256) external {
        uint256 value = fee[pool];
        fee[pool] = 0;
        if (value == 0) return;
        PoolConfig memory config = pools.get(pool);
        MockToken(config.key.currency0).mint(msg.sender, value);
        MockToken(config.key.currency1).mint(msg.sender, value);
    }
}

/// @notice Combined permitted limits, rather than independent one-axis tests:
/// Four historical buckets with actual LP fee receipts, 32 admitted LP reward assets,
/// and the maximum 16 ERC20 royalty assets plus native ETH. Real core accounting;
/// mocked access, tokens, oracle feeds, randomness, strategy and liquidity venue.
/// Cold gasleft deltas exclude construction, intrinsic/calldata gas and refunds.
contract CombinedCapacityGasTest is Test {
    uint256 private constant LOCAL_GAS_BUDGET = 12_000_000;
    uint256 private constant SUPPORTED_BUCKETS = 4;
    address private constant OWNER = address(0xA11CE);
    address private constant ENTRANT = address(0xB0B);
    address payable private constant TREASURY = payable(address(0x7EA5));
    MockAccess private access;
    MockPools private pools;
    MockFeed private feed;
    MockVRF private vrf;
    VaultPolicyMock private policy;
    CombinedCapacityVenue private venue;
    ZZZVault private vault;
    ZZZNFT private nft;
    ZZZMembership private membership;
    ZZZRewards private rewards;
    ZZZFeeController private fees;
    ZZZOracle private oracle;
    ZZZRoyaltyRewards private royalties;
    MockToken[] private tokens;
    bytes32[] private poolIds;
    uint256[] private incumbents;
    uint256 private entrant;
    bool private faultCurrencyFixture;

    function activePlan(uint256) external pure returns (bytes32) { return bytes32(0); }

    function _mint(address owner) private returns (uint256 id) {
        vm.prank(owner);
        id = vault.mintDormant{value: 0.05 ether}();
        vrf.fulfill(nft.requestOf(id), 0, 0);
        nft.finalizeTraits(id);
    }

    function _fixture() private {
        vm.pauseGasMetering();
        vm.warp(1_000_000);
        access = new MockAccess();
        pools = new MockPools();
        feed = new MockFeed(8, 1e8);
        policy = new VaultPolicyMock();
        venue = new CombinedCapacityVenue(pools);
        vault = new ZZZVault(address(access), block.chainid, TREASURY);
        assertEq(vault.MAX_BUCKETS(), SUPPORTED_BUCKETS, "Requalify combined gas before changing capacity");
        nft = new ZZZNFT(address(access), "");
        vrf = new MockVRF();
        nft.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        membership = new ZZZMembership(address(access));
        rewards = new ZZZRewards(address(access));
        fees = new ZZZFeeController(address(access));
        oracle = new ZZZOracle(address(access), address(0));
        royalties = nft.royaltyRewards();
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
        access.bind(keccak256("ZZZMigrationReceiver"), address(0x987));
        for (uint256 i; i < 32; ++i) {
            MockToken token = faultCurrencyFixture && i < 16 ? new CapacityRoyaltyFaultToken() : new MockToken(0);
            tokens.push(token);
            oracle.setTestFeed(address(token), address(feed), 3600);
            rewards.addAsset(address(token));
            if (i < 16) nft.addRoyaltyAsset(address(token));
            token.mint(OWNER, 100_000);
            token.mint(ENTRANT, 100_000);
            vm.prank(OWNER); token.approve(address(vault), type(uint256).max);
            vm.prank(ENTRANT); token.approve(address(vault), type(uint256).max);
        }
        CanonicalFixture.bind(address(access));
        access.seal();
        vm.deal(OWNER, 10 ether);
        vm.deal(ENTRANT, 1 ether);
        for (uint256 i; i < SUPPORTED_BUCKETS; ++i) {
            address first = address(tokens[i * 2]);
            address second = address(tokens[i * 2 + 1]);
            if (first > second) (first, second) = (second, first);
            PoolConfig memory config;
            config.key = PoolKey(first, second, 3000, 60, address(0));
            config.operationsEnabled = true;
            config.depositsEnabled = true;
            config.minDepositUSD = 1e18;
            config.maxPositionUSD = 1e30;
            config.maxSlippageBps = 100;
            bytes32 pool = keccak256(abi.encode(config.key));
            pools.set(pool, config);
            poolIds.push(pool);
            uint256 id = _mint(OWNER);
            incumbents.push(id);
            vm.prank(OWNER); vault.activate(id, pool, 1000, 1000, 1, block.timestamp + 100);
        }
        entrant = _mint(ENTRANT);
        // Actual LP fees and sub-twenty dust belong to the incumbent cohort
        // before either measured operation; no creator-inbox intake exists.
        for (uint256 i; i < SUPPORTED_BUCKETS; ++i) {
            venue.setFees(poolIds[i], 19);
            vault.collectFees(vault.nftBucket(incumbents[i]), block.timestamp + 100);
            venue.setFees(poolIds[i], 1000);
            vault.collectFees(vault.nftBucket(incumbents[i]), block.timestamp + 100);
        }
        for (uint256 i; i < 16; ++i) tokens[i].mint(address(royalties), 1600);
        vm.deal(address(royalties), 16 ether);
        assertEq(vault.bucketCount(), SUPPORTED_BUCKETS);
        assertEq(rewards.assetCount(), 33);
        assertEq(royalties.assetCount(), 17);
        assertEq(membership.totalEligible(), SUPPORTED_BUCKETS);
        vm.resumeGasMetering();
    }

    function _cool() private {
        vm.cool(address(oracle.contributionPricing()));
        for (uint256 i; i < tokens.length; ++i) {
            ZZZOracle.DualPolicy memory p=oracle.policy(oracle.activePolicy(address(tokens[i])));
            vm.cool(p.primary.source);vm.cool(p.secondary.source);
        }
        vm.cool(address(vault.migrationBudget()));
        vm.cool(address(access)); vm.cool(address(pools)); vm.cool(address(feed));
        vm.cool(address(vrf)); vm.cool(address(policy)); vm.cool(address(venue));
        vm.cool(address(vault)); vm.cool(address(royalties));
        vm.cool(address(nft.metadataRenderer())); vm.cool(address(nft.claimRouter()));
        vm.cool(address(membership)); vm.cool(address(rewards)); vm.cool(address(fees));
        vm.cool(address(oracle)); vm.cool(OWNER); vm.cool(ENTRANT); vm.cool(TREASURY);
        for (uint256 i; i < tokens.length; ++i) vm.cool(address(tokens[i]));
        // Helper getters above touch the NFT; cool it after those reads.
        vm.cool(address(nft));
        vm.cool(access.module(Ids.CANONICAL)); vm.cool(access.module(Ids.NFT_CANONICAL));
        vm.cool(access.module(Ids.VAULT_CANONICAL)); vm.cool(access.module(Ids.FEES_CANONICAL));
        // Reading companion bindings warms the controller; cool it last.
        vm.cool(address(access));
        vm.cool(address(oracle));
    }

    function _assertHistoricalFundingExcluded() private view {
        for (uint256 i; i < 32; ++i) {
            address token = address(tokens[i]);
            if (i < incumbents.length * 2) {
                uint256 bucket = vault.nftBucket(incumbents[i / 2]);
                assertEq(fees.dust(bucket, token), 0);
                assertEq(rewards.liabilities(token), 919);
                assertEq(rewards.claimable(incumbents[i / 2], token), 819 + 100 / incumbents.length);
            } else assertEq(rewards.liabilities(token), 0);
            assertEq(rewards.claimable(entrant, token), 0, "Entrant received historical LP fees");
            if (i < 16) {
                assertEq(royalties.claimable(entrant, token), 0, "Entrant received historical royalties");
                assertEq(royalties.claimable(incumbents[0], token), 1600 / SUPPORTED_BUCKETS);
            }
        }
        assertEq(royalties.claimable(entrant, address(0)), 0);
        assertEq(royalties.claimable(incumbents[0], address(0)), 16 ether / SUPPORTED_BUCKETS);
    }

    function testColdActivationAtCombinedBucketAndAssetCaps() public {
        _fixture();
        _cool();
        vm.prank(ENTRANT);
        uint256 beforeGas = gasleft();
        vault.activate(entrant, poolIds[0], 1000, 1000, 1, block.timestamp + 100);
        uint256 used = beforeGas - gasleft();
        emit log_named_uint("combined.4-buckets.32-assets.17-royalties.activation", used);
        assertEq(membership.totalEligible(), SUPPORTED_BUCKETS + 1);
        assertGt(vault.sharesOf(entrant), 0);
        _assertHistoricalFundingExcluded();
        assertLt(used, LOCAL_GAS_BUDGET, "Combined-capacity activation exceeds unchanged local budget");
    }

    function testColdIncumbentTopUpAtCombinedBucketAndAssetCaps() public {
        _fixture();
        uint256 previousShares = vault.sharesOf(incumbents[0]);
        uint256 previousWeight = royalties.weightOf(incumbents[0]);
        _cool();
        vm.prank(OWNER);
        uint256 beforeGas = gasleft();
        vault.increase(incumbents[0], 100, 100, 1, block.timestamp + 100);
        uint256 used = beforeGas - gasleft();
        emit log_named_uint("combined.4-buckets.32-assets.17-royalties.top-up", used);
        assertEq(membership.totalEligible(), SUPPORTED_BUCKETS);
        assertEq(royalties.weightOf(incumbents[0]), previousWeight);
        assertGt(vault.sharesOf(incumbents[0]), previousShares);
        _assertHistoricalFundingExcluded();
        assertLt(used, LOCAL_GAS_BUDGET, "Combined-capacity top-up exceeds unchanged local budget");
    }

    /// @dev Conservatively populate every owner/global index, even though local
    /// pool moves preserve the accounting pair. Mock Fee authority seeds real
    /// backed Rewards state; this does not claim that one venue earns 32 assets.
    function _fullyIndexedOperation(bool activation) private {
        _fixture();
        vm.pauseGasMetering();
        uint256 bucket = vault.nftBucket(incumbents[0]);
        for (uint256 i; i < 32; ++i) {
            tokens[i].mint(address(fees), 900);
            vm.startPrank(address(fees));
            tokens[i].approve(address(rewards), 900);
            rewards.creditPool(bucket, address(tokens[i]), 800, 100);
            vm.stopPrank();
            assertGt(rewards.ownerIndex(bucket, address(tokens[i])), 0);
            assertGt(rewards.index(address(tokens[i])), 0);
        }
        vm.resumeGasMetering();
        uint256 previousShares = vault.sharesOf(incumbents[0]);
        uint256 previousWeight = royalties.weightOf(incumbents[0]);
        _cool();
        vm.prank(activation ? ENTRANT : OWNER);
        uint256 beforeGas = gasleft();
        if (activation) vault.activate(entrant, poolIds[0], 1000, 1000, 1, block.timestamp + 100);
        else vault.increase(incumbents[0], 100, 100, 1, block.timestamp + 100);
        uint256 used = beforeGas - gasleft();
        emit log_named_uint(activation ? "combined.4-buckets.32-indexed-assets.activation" :
            "combined.4-buckets.32-indexed-assets.top-up", used);
        assertEq(membership.totalEligible(), SUPPORTED_BUCKETS + (activation ? 1 : 0));
        assertEq(royalties.weightOf(incumbents[0]), previousWeight);
        if (activation) {
            assertGt(vault.sharesOf(entrant), 0);
            assertEq(vault.sharesOf(incumbents[0]), previousShares);
        } else assertGt(vault.sharesOf(incumbents[0]), previousShares);
        for (uint256 i; i < 32; ++i) {
            address token = address(tokens[i]);
            assertEq(rewards.claimable(entrant, token), 0, "Entrant received historical indexed rewards");
            assertEq(rewards.paidOwnerIndex(activation ? entrant : incumbents[0], token), rewards.ownerIndex(bucket, token));
            if (activation) assertEq(rewards.paidIndex(entrant, token), rewards.index(token));
            bool currentAsset = i < SUPPORTED_BUCKETS * 2;
            assertEq(rewards.liabilities(token), 900 + (currentAsset ? 919 : 0));
            assertEq(rewards.claimable(incumbents[0], token),
                800 + 100 / SUPPORTED_BUCKETS + (currentAsset ? 100 / SUPPORTED_BUCKETS : 0) + (i < 2 ? 819 : 0));
            if (currentAsset) {
                uint256 earningBucket = vault.nftBucket(incumbents[i / 2]);
                assertEq(fees.dust(earningBucket, token), 0);
            }
            if (i < 16) {
                assertEq(royalties.claimable(entrant, token), 0);
                assertEq(royalties.claimable(incumbents[0], token), 1600 / SUPPORTED_BUCKETS);
            }
        }
        assertEq(royalties.claimable(entrant, address(0)), 0);
        assertEq(royalties.claimable(incumbents[0], address(0)), 16 ether / SUPPORTED_BUCKETS);
        assertLt(used, LOCAL_GAS_BUDGET, "Fully indexed capacity exceeds unchanged local budget");
    }

    function testColdActivationWithEveryHistoricalRewardIndexPopulated() public { _fullyIndexedOperation(true); }
    function testColdIncumbentTopUpWithEveryHistoricalRewardIndexPopulated() public { _fullyIndexedOperation(false); }

    /// @notice Bounded optional-currency isolation still has a finite total gas
    /// cost. This scenario fits the unchanged 12M call budget while preserving
    /// earlier earnings; it does not qualify actual venue or worst-case native gas.
    function testMaximumOptionalRoyaltyGasFaultsFitReviewedActivationBudget() public {
        faultCurrencyFixture = true;
        _fixture();
        vm.pauseGasMetering();
        uint256 bucket = vault.nftBucket(incumbents[0]);
        for (uint256 i; i < 32; ++i) {
            tokens[i].mint(address(fees), 900);
            vm.startPrank(address(fees));
            tokens[i].approve(address(rewards), 900);
            rewards.creditPool(bucket, address(tokens[i]), 800, 100);
            vm.stopPrank();
        }
        for (uint256 i; i < 16; ++i) CapacityRoyaltyFaultToken(address(tokens[i])).setFailingReader(address(royalties));
        address first = pools.get(poolIds[0]).key.currency0;
        address second = pools.get(poolIds[0]).key.currency1;
        uint256 balance0 = IERC20(first).balanceOf(ENTRANT);
        uint256 balance1 = IERC20(second).balanceOf(ENTRANT);
        uint256 previousShares = vault.bucketTotalShares(bucket);
        uint256 previousLP = vault.group(bucket).lpTokenId;
        bytes memory payload = abi.encodeCall(vault.activate, (entrant,poolIds[0],1000,1000,1,block.timestamp+100));
        vm.resumeGasMetering();
        _cool();
        vm.prank(ENTRANT);
        uint256 start = gasleft();
        (bool executed, bytes memory result) = address(vault).call{gas: LOCAL_GAS_BUDGET}(payload);
        uint256 completedGas = start-gasleft();
        emit log_named_uint("maximum-royalty-faults.12M-attempt.gas", completedGas);
        if (!executed) assembly ("memory-safe") { revert(add(result,32),mload(result)) }
        assertLt(completedGas,LOCAL_GAS_BUDGET,"Requalify optional-currency gas before changing the review");
        assertEq(vault.nftBucket(entrant),bucket);
        assertGt(vault.sharesOf(entrant),0);
        assertEq(vault.bucketTotalShares(bucket),previousShares+vault.sharesOf(entrant));
        assertEq(membership.totalEligible(),SUPPORTED_BUCKETS+1);
        assertEq(royalties.activationCount(),SUPPORTED_BUCKETS+1);
        assertEq(royalties.eligibleCount(address(0)),SUPPORTED_BUCKETS+1);
        assertEq(IERC20(first).balanceOf(ENTRANT),balance0-1000);
        assertEq(IERC20(second).balanceOf(ENTRANT),balance1-1000);
        for (uint256 i; i < 16; ++i) {
            address token=address(tokens[i]);
            assertFalse(royalties.eligibleFor(entrant,token));
            assertEq(royalties.eligibleCount(token),SUPPORTED_BUCKETS);
            CapacityRoyaltyFaultToken(token).setFailingReader(address(0));
            royalties.sync(token);
            assertTrue(royalties.eligibleFor(entrant,token));
            assertEq(royalties.claimable(entrant,token),0,"No pre-activation royalty theft");
            assertEq(royalties.claimable(incumbents[0],token),1600/SUPPORTED_BUCKETS);
        }
        for (uint256 i; i < 32; ++i) assertEq(rewards.claimable(entrant,address(tokens[i])),0,"No historical LP fee theft");
        assertEq(royalties.claimable(entrant,address(0)),0);
    }
}
