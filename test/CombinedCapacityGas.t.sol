// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {SinglePositionFixture} from "./helpers/PortfolioFixture.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Vm} from "forge-std/Vm.sol";
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
contract CombinedCapacityVenue is ERC721 , SinglePositionFixture {
    Vm private constant nativeVm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    MockPools private immutable pools;
    receive()external payable{}
    function _send(address to,uint256 value)private{if(value!=0){(bool ok,)=payable(to).call{value:value}("");require(ok);}}

    mapping(uint256 => uint256) private amount0;
    mapping(uint256 => uint256) private amount1;
    mapping(bytes32 => uint256) private fee;
    uint256 private next = 1;

    constructor(MockPools registry) ERC721("Combined-capacity mock", "CCM") { pools = registry; }
    function positionManager() external view returns (address) { return address(this); }
    function balanceContext(bytes32) external pure returns(bytes32){return bytes32(0);}
    function balance(bytes32,uint256,uint256 a0,uint256 a1,uint256) external payable returns(uint256,uint256) {
        require(msg.value==a0);_send(msg.sender,a0);
        return(a0,a1); // Deterministic custody fixture; no market execution is modeled.
    }
    function amounts(uint256 id) external view returns (uint256, uint256) { return (amount0[id], amount1[id]); }
    function setFees(bytes32 pool, uint256 value) external { fee[pool] = value; }
    function mint(bytes32 pool, int24, int24, uint256 a0, uint256 a1, uint128, uint256)
        external payable returns (uint256 id, uint256 spent0, uint256 spent1) {
        id = next++;
        _mint(msg.sender, id);
        (spent0, spent1) = _fund(pool, id, a0, a1);
    }
    function increase(bytes32 pool, uint256 id, uint256 a0, uint256 a1, uint128, uint256)
        external payable returns (uint256, uint256) {
        require(ownerOf(id) == msg.sender);
        return _fund(pool, id, a0, a1);
    }
    function _fund(bytes32 pool, uint256 id, uint256 a0, uint256 a1) private returns (uint256, uint256) {
        PoolConfig memory config = pools.get(pool);
        require(config.key.currency0==address(0)&&msg.value==a0);
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
        nativeVm.deal(address(this),address(this).balance+value);_send(msg.sender,value);
        MockToken(config.key.currency1).mint(msg.sender, value);
    }
}

/// @notice Combined permitted limits, rather than independent one-axis tests:
/// Four historical buckets with actual LP fee receipts, two fixed LP reward books,
/// and the default16 ERC20 royalty assets plus native ETH. Real core accounting;
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
        bytes32 reviewedPolicy1 = vault.mintPolicyFingerprint(); vm.prank(owner);
        id = vault.mintDormant{value: 0.05 ether}(reviewedPolicy1);
        vrf.fulfill(nft.requestOf(id), 0, 0);
        nft.finalizeTraits(id);
    }

    function _fixture() private {
        vm.pauseGasMetering();
        vm.warp(1_000_000);
        access = new MockAccess(); ProtocolPolicyFixture.bind(address(access));
        pools = new MockPools();
        feed = new MockFeed(8, 1e8);
        policy = new VaultPolicyMock();
        venue = new CombinedCapacityVenue(pools);
        ProtocolPolicyFixture.recipient(address(access),TREASURY);vault=new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        assertEq(vault.MAX_BUCKETS(), SUPPORTED_BUCKETS, "Requalify combined gas before changing capacity");
        nft = new ZZZNFT(address(access), "", address(new ZZZNFTMetadata(address(access)))); nft.setMintEnd(uint64(block.timestamp + 3650 days));
        vrf = new MockVRF();
        ProtocolPolicyFixture.randomness(address(nft.access()),address(vrf),bytes32(uint256(1)),1,3,500000,false);
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
        for (uint256 i; i < 16; ++i) {
            MockToken token = faultCurrencyFixture && i < 16 ? new CapacityRoyaltyFaultToken() : new MockToken(0);
            tokens.push(token);
            oracle.setTestFeed(address(token), address(feed), 3600);

            if (i < 16) nft.addRoyaltyAsset(address(token));
            token.mint(OWNER, 100_000);
            token.mint(ENTRANT, 100_000);
            vm.prank(OWNER); token.approve(address(vault), type(uint256).max);
            vm.prank(ENTRANT); token.approve(address(vault), type(uint256).max);
        }
        pools.setFixedZZZ(address(tokens[0]));rewards.addAsset(address(tokens[0]));
        oracle.setTestFeed(address(0),address(new MockFeed(8,1e26)),7200);
        CanonicalFixture.bind(address(access));
        access.seal();
        vm.deal(OWNER, 10 ether);
        vm.deal(ENTRANT, 1 ether);
        for (uint256 i; i < SUPPORTED_BUCKETS; ++i) {
            address first=address(0);address second=address(tokens[0]);
            PoolConfig memory config;
            config.key = PoolKey(first, second, uint24(3000+i), 60, address(0));
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
            vm.prank(OWNER); vault.activate{value:1000}(id, pool, 1000, 1000, 1, block.timestamp + 100);
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
        // All fixture NFTs are already minted. Close the actual sale and wait
        // its real 1-hour grace with four incumbents and a dormant entrant.
        nft.setMintEnd(uint64(block.timestamp+1));
        vm.warp(block.timestamp+3601);
        feed.set(1e8,block.timestamp,block.timestamp);
        royalties.syncAll();
        assertTrue(royalties.royaltiesOpen());
        // Leave receipts PENDING for the measured operation: healthy activation
        // must allocate to incumbents, and fault recovery must exclude entrant.
        for (uint256 i; i < 16; ++i) tokens[i].mint(address(royalties), 1600);
        vm.deal(address(royalties), 16 ether);
        assertEq(royalties.pending(address(0)),16 ether);
        assertEq(vault.bucketCount(), SUPPORTED_BUCKETS);
        assertEq(rewards.assetCount(), 2);
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
        // The strategy mock and actual gas/terms policy are different contracts.
        vm.cool(access.protocolPolicy());
        // Reading companion/policy bindings warms the controller; cool it last.
        vm.cool(address(access));
        vm.cool(address(oracle));
    }

    function _lpAsset(uint256 i)private view returns(address){return i==0?address(0):address(tokens[0]);}
    function _seedBooks(uint256 bucket)private{
        vm.deal(address(fees),address(fees).balance+900);
        vm.prank(address(fees));rewards.creditPool{value:900}(bucket,address(0),800,100);
        tokens[0].mint(address(fees),900);vm.startPrank(address(fees));
        tokens[0].approve(address(rewards),900);rewards.creditPool(bucket,address(tokens[0]),800,100);vm.stopPrank();
    }
    function _assertHistoricalFundingExcluded()private view{
        for(uint256 i;i<2;++i){address asset=_lpAsset(i);
            assertEq(rewards.liabilities(asset),3676);
            assertEq(rewards.claimable(entrant,asset),0);
            for(uint256 j;j<4;++j){assertEq(fees.dust(vault.nftBucket(incumbents[j]),asset),0);assertEq(rewards.claimable(incumbents[j],asset),919);}
        }
        for(uint256 i;i<16;++i){address asset=address(tokens[i]);assertEq(royalties.claimable(entrant,asset),0);assertEq(royalties.claimable(incumbents[0],asset),400);}
        assertEq(royalties.claimable(entrant,address(0)),0);assertEq(royalties.claimable(incumbents[0],address(0)),4 ether);
    }

    function testColdActivationAtCombinedBucketAndAssetCaps() public {
        _fixture();
        _cool();
        vm.prank(ENTRANT);
        uint256 beforeGas = gasleft();
        vault.activate{value:1000}(entrant, poolIds[0], 1000, 1000, 1, block.timestamp + 100);
        uint256 used = beforeGas - gasleft();
        emit log_named_uint("combined.4-buckets.2-books.17-royalties.activation", used);
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
        vault.increase{value:100}(incumbents[0], 100, 100, 1, block.timestamp + 100);
        uint256 used = beforeGas - gasleft();
        emit log_named_uint("combined.4-buckets.2-books.17-royalties.top-up", used);
        assertEq(membership.totalEligible(), SUPPORTED_BUCKETS);
        assertEq(royalties.weightOf(incumbents[0]), previousWeight);
        assertGt(vault.sharesOf(incumbents[0]), previousShares);
        _assertHistoricalFundingExcluded();
        assertLt(used, LOCAL_GAS_BUDGET, "Combined-capacity top-up exceeds unchanged local budget");
    }

    /// @dev Conservatively populate every owner/global index, even though local
    /// pool moves preserve the accounting pair. Mock Fee authority seeds real
    /// backed Rewards state; this does not claim that the native/fixed-ZZZ pair earns any third asset.
    function _fullyIndexedOperation(bool activation) private {
        _fixture();
        vm.pauseGasMetering();
        uint256 bucket = vault.nftBucket(incumbents[0]);
        _seedBooks(bucket);
        for(uint256 i;i<2;++i){(uint256 personal,uint256 shared)=rewards.claimableComponents(incumbents[0],_lpAsset(i));assertGt(personal,0);assertGt(shared,0);}
        vm.resumeGasMetering();
        uint256 previousShares = vault.sharesOf(incumbents[0]);
        uint256 previousWeight = royalties.weightOf(incumbents[0]);
        _cool();
        vm.prank(activation ? ENTRANT : OWNER);
        uint256 beforeGas = gasleft();
        if (activation) vault.activate{value:1000}(entrant, poolIds[0], 1000, 1000, 1, block.timestamp + 100);
        else vault.increase{value:100}(incumbents[0], 100, 100, 1, block.timestamp + 100);
        uint256 used = beforeGas - gasleft();
        emit log_named_uint(activation ? "combined.4-buckets.2-exact-books.activation" :
            "combined.4-buckets.2-exact-books.top-up", used);
        assertEq(membership.totalEligible(), SUPPORTED_BUCKETS + (activation ? 1 : 0));
        assertEq(royalties.weightOf(incumbents[0]), previousWeight);
        if (activation) {
            assertGt(vault.sharesOf(entrant), 0);
            assertEq(vault.sharesOf(incumbents[0]), previousShares);
        } else assertGt(vault.sharesOf(incumbents[0]), previousShares);
        for(uint256 i;i<2;++i){address asset=_lpAsset(i);assertEq(rewards.claimable(entrant,asset),0);
            assertEq(rewards.liabilities(asset),4576);assertEq(rewards.claimable(incumbents[0],asset),1744);
            for(uint256 j;j<4;++j)assertEq(fees.dust(vault.nftBucket(incumbents[j]),asset),0);
        }
        for(uint256 i;i<16;++i){assertEq(royalties.claimable(entrant,address(tokens[i])),0);assertEq(royalties.claimable(incumbents[0],address(tokens[i])),400);}
        assertEq(royalties.claimable(entrant, address(0)), 0);
        assertEq(royalties.claimable(incumbents[0], address(0)), 16 ether / SUPPORTED_BUCKETS);
        assertLt(used, LOCAL_GAS_BUDGET, "Both-book capacity exceeds unchanged local budget");
    }

    function testColdActivationWithBothExactRewardBooksFunded() public { _fullyIndexedOperation(true); }
    function testColdIncumbentTopUpWithBothExactRewardBooksFunded() public { _fullyIndexedOperation(false); }

    /// @notice Sixteen full-budget faults at the current 1M per-currency default
    /// exceed 12M. Underfunded execution must roll back; a larger LOCAL fixture
    /// call verifies isolation without qualifying live API/provider/chain budgets.
    function testSixteenOptionalFaultsRejectTwelveMillionAndIsolateWithLargerLocalBudget() public {
        faultCurrencyFixture = true;
        _fixture();
        vm.pauseGasMetering();
        uint256 bucket = vault.nftBucket(incumbents[0]);
        _seedBooks(bucket);
        for (uint256 i; i < 16; ++i) CapacityRoyaltyFaultToken(address(tokens[i])).setFailingReader(address(royalties));
        address first = pools.get(poolIds[0]).key.currency0;
        address second = pools.get(poolIds[0]).key.currency1;
        uint256 balance0=ENTRANT.balance;
        uint256 balance1 = IERC20(second).balanceOf(ENTRANT);
        uint256 previousShares = vault.bucketTotalShares(bucket);
        uint256 previousLP = vault.group(bucket).lpTokenId;
        bytes memory payload = abi.encodeCall(vault.activate, (entrant,poolIds[0],1000,1000,1,block.timestamp+100));
        vm.resumeGasMetering();
        _cool();
        vm.prank(ENTRANT);
        uint256 start = gasleft();
        (bool executed,) = address(vault).call{gas:LOCAL_GAS_BUDGET,value:1000}(payload);
        emit log_named_uint("maximum-royalty-faults.12M-rejected.gas", start-gasleft());
        assertFalse(executed,"Sixteen 1M faults must not be labeled 12M-qualified");
        assertEq(vault.nftBucket(entrant),0);
        assertEq(vault.sharesOf(entrant),0);
        assertEq(vault.bucketTotalShares(bucket),previousShares);
        assertEq(vault.group(bucket).lpTokenId,previousLP);
        assertEq(membership.totalEligible(),SUPPORTED_BUCKETS);
        assertEq(royalties.activationCount(),SUPPORTED_BUCKETS);
        assertEq(royalties.weightOf(entrant),0);
        assertEq(ENTRANT.balance,balance0);
        assertEq(IERC20(second).balanceOf(ENTRANT),balance1);
        for(uint256 i;i<16;++i) assertEq(royalties.eligibleCount(address(tokens[i])),SUPPORTED_BUCKETS);
        // 24M is a test-local envelope, not a changed service limit or target
        // qualification. Production must simulate and review aggregate capacity.
        uint256 localFaultBudget=24_000_000;
        _cool();
        vm.prank(ENTRANT);
        start=gasleft();
        bytes memory result;
        (executed,result)=address(vault).call{gas:localFaultBudget,value:1000}(payload);
        uint256 completedGas=start-gasleft();
        emit log_named_uint("maximum-royalty-faults.24M-local-attempt.gas",completedGas);
        if (!executed) assembly ("memory-safe") { revert(add(result,32),mload(result)) }
        assertLt(completedGas,localFaultBudget,"Local fault-envelope regression");
        assertEq(vault.nftBucket(entrant),bucket);
        assertGt(vault.sharesOf(entrant),0);
        assertEq(vault.bucketTotalShares(bucket),previousShares+vault.sharesOf(entrant));
        assertEq(membership.totalEligible(),SUPPORTED_BUCKETS+1);
        assertEq(royalties.activationCount(),SUPPORTED_BUCKETS+1);
        assertEq(royalties.eligibleCount(address(0)),SUPPORTED_BUCKETS+1);
        assertEq(ENTRANT.balance,balance0-1000);
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
        for(uint256 i;i<2;++i)assertEq(rewards.claimable(entrant,_lpAsset(i)),0,"No historical LP fee theft");
        assertEq(royalties.claimable(entrant,address(0)),0);
    }
}
