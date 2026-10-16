// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Ids, Position, PositionStatus, PoolConfig, Route, BridgeMessage} from "../src/libraries/ZZZTypes.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {MockAccess, MockToken, MockPools, MockRoutes} from "./mocks/Mocks.sol";
import {RewardsVaultFixture} from "./RewardsAndFees.t.sol";
import {ReceiverVaultFixture, CapturingBridgeFixture} from "./ReceiverAndRemoteFees.t.sol";

/// @dev TEST ONLY: isolate parked reward policy from physical LP removal, which
/// is exercised by the actual Vault's separate recovery tests. No mock parking
/// operation is evidence that a real LP was closed safely.
contract ParkedRewardVaultFixture is RewardsVaultFixture {
    constructor(ZZZRewards rewards) RewardsVaultFixture(rewards) {}
    function MAX_BUCKETS() external pure returns (uint256) { return 4; }
    function bucketCount() external pure returns (uint256) { return 1; }
    function bucketAt(uint256 ordinal) external pure returns (uint256) { require(ordinal == 0); return 7; }
}

contract ParkedRewardsTest is Test {
    MockAccess access;
    MockToken token;
    MockToken other;
    MockPools pools;
    ParkedRewardVaultFixture vault;
    ZZZNFT nft;
    ZZZMembership membership;
    ZZZRewards rewards;
    ZZZFeeController fees;
    ZZZRoyaltyRewards royalties;
    address alice = address(0xA11CE);
    address bob = address(0xB0B);
    uint256 constant BUCKET = 7;
    bytes32 constant POOL = keccak256("parked-rewards-pool");

    function setUp() public {
        access = new MockAccess(); token = new MockToken(18); other = new MockToken(18);
        rewards = new ZZZRewards(address(access)); vault = new ParkedRewardVaultFixture(rewards);
        nft = new ZZZNFT(address(access), "ipfs://"); royalties = nft.royaltyRewards();
        membership = new ZZZMembership(address(access)); fees = new ZZZFeeController(address(access));
        pools = new MockPools();
        access.bind(Ids.VAULT, address(vault)); access.bind(Ids.NFT, address(nft));
        access.bind(Ids.MEMBERSHIP, address(membership)); access.bind(Ids.REWARDS, address(rewards));
        access.bind(Ids.FEES, address(fees)); access.bind(Ids.POOLS, address(pools));
        rewards.addAsset(address(token)); rewards.addAsset(address(other)); nft.addRoyaltyAsset(address(token));
        MockVRF vrf = new MockVRF();
        nft.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        access.seal();
        PoolConfig memory config; config.key.currency0 = address(token); config.key.currency1 = address(other);
        pools.set(POOL, config);
        Position memory p; p.poolId = POOL; p.lpTokenId = 99; p.status = PositionStatus.Active;
        p.homeChain = block.chainid; p.homeVault = address(vault); p.homeReceiver = address(0x123);
        p.homeToken0 = address(token); p.homeToken1 = address(other);
        p.locationChain = block.chainid; p.locationVault = address(vault);
        p.idle0 = 11; p.idle1 = 13; vault.set(BUCKET, p);
        token.mint(address(vault), 11); other.mint(address(vault), 13);
        vm.prank(address(vault)); nft.mint(alice, 1);
        vrf.fulfill(nft.requestOf(1), 0, 0); nft.finalizeTraits(1);
        vm.prank(address(vault)); nft.mint(bob, 2);
        vrf.fulfill(nft.requestOf(2), 0, 0); nft.finalizeTraits(2);
        _activate(1);
    }
    function _activate(uint256 id) private {
        vault.join(id, BUCKET, 100);
        vm.prank(address(vault)); membership.activate(id);
        vm.prank(address(vault)); nft.notifyContribution(id);
    }
    function _allocate(uint256 amount) private {
        token.mint(address(vault), amount);
        vm.startPrank(address(vault)); token.approve(address(fees), amount);
        fees.allocate(BUCKET, address(token), amount); vm.stopPrank();
    }
    function _park() private {
        Position memory p = vault.group(BUCKET); p.status = PositionStatus.Parked; p.lpTokenId = 0;
        vault.set(BUCKET, p);
    }
    function testParkedReceiverCreationFundingAndClaimsWorkWhilePaused() public {
        _park(); access.setPaused(true);
        address inbox = fees.createRewardReceiver(BUCKET, address(0));
        token.mint(inbox, 1000); fees.syncExternal(BUCKET);
        assertEq(fees.totalExternalFunded(BUCKET, address(token)), 1000);
        assertEq(rewards.claimable(1, address(token)), 900);
        assertEq(fees.compoundBalance(BUCKET, address(token)), 50);
        assertEq(fees.buybackBalance(address(token)), 50);
        vm.prank(alice); assertEq(rewards.claim(1, address(token)), 900);
        assertEq(vault.sharesOf(1), 100); assertEq(vault.bucketTotalShares(BUCKET), 100);
        assertEq(vault.group(BUCKET).idle0, 11); assertEq(token.balanceOf(address(vault)), 11);
        assertTrue(membership.eligible(1)); assertEq(membership.totalEligible(), 1);
    }
    function testParkedGlobalDustSettlesBeforeAnotherNFTJoins() public {
        _allocate(19); assertEq(fees.dust(BUCKET, address(token)), 19); _park();
        vm.prank(address(vault)); fees.syncAllExternal();
        assertEq(fees.dust(BUCKET, address(token)), 0);
        assertEq(rewards.claimable(1, address(token)), 19);
        // Isolated membership fixture: an actual parked Vault forbids LP joins.
        // This exercises the global pre-entry barrier before another member.
        _activate(2);
        assertEq(rewards.claimable(2, address(token)), 0);
        assertEq(rewards.claimable(1, address(token)), 19);
    }
    function testParkedDustStillRequiresAuthorizedSettler() public {
        _allocate(19); _park();
        vm.prank(bob); vm.expectRevert(); fees.flushDust(BUCKET, address(token));
        assertEq(fees.dust(BUCKET, address(token)), 19);
        vm.prank(address(vault)); fees.flushDust(BUCKET, address(token));
        assertEq(rewards.claimable(1, address(token)), 19);
    }
    function testParkedTransferCarriesLPAndRoyaltyClaimsWithUnavailableMark() public {
        _allocate(1000); token.mint(address(royalties), 200); _park(); access.setPaused(true);
        (bool available, uint256 value) = nft.currentLPValue(1); assertFalse(available); assertEq(value, 0);
        uint256 weight = royalties.weightOf(1);
        vm.prank(alice); nft.transferFrom(alice, bob, 1);
        vm.prank(alice); vm.expectRevert(); rewards.claim(1, address(token));
        vm.prank(alice); vm.expectRevert(); royalties.claim(1, address(token));
        vm.prank(bob); assertEq(rewards.claim(1, address(token)), 900);
        vm.prank(bob); assertEq(royalties.claim(1, address(token)), 200);
        assertEq(token.balanceOf(bob), 1100); assertEq(royalties.weightOf(1), weight);
        assertTrue(membership.eligible(1)); assertEq(vault.sharesOf(1), 100);
    }
    function testParkedDoesNotAdmitOrdinaryVenueFeeAllocation() public {
        _park(); token.mint(address(vault), 100); uint256 before = token.balanceOf(address(vault));
        vm.startPrank(address(vault)); token.approve(address(fees), 100);
        vm.expectRevert(); fees.allocate(BUCKET, address(token), 100); vm.stopPrank();
        assertEq(token.balanceOf(address(vault)), before); assertEq(fees.accounted(address(token)), 0);
    }
    function testParkedReceiverCreationStillRequiresGovernance() public {
        _park(); vm.prank(bob); vm.expectRevert(); fees.createRewardReceiver(BUCKET, address(0));
        assertEq(fees.rewardReceiver(BUCKET), address(0));
    }
}

contract ParkedSatelliteRewardsTest is Test {
    function testParkedSatelliteDustAndLegacyRewardsCanBridgeWithoutReopeningLP() public {
        vm.chainId(31337); MockAccess access = new MockAccess();
        MockToken token = new MockToken(18); MockToken other = new MockToken(18);
        MockPools pools = new MockPools(); MockRoutes routes = new MockRoutes();
        ReceiverVaultFixture vault = new ReceiverVaultFixture(1, pools);
        CapturingBridgeFixture bridge = new CapturingBridgeFixture(routes);
        ZZZFeeController fees = new ZZZFeeController(address(access));
        access.bind(Ids.VAULT, address(vault)); access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.ROUTES, address(routes)); access.bind(Ids.BRIDGE, address(bridge)); access.seal();
        bytes32 pool = keccak256("parked-satellite"); bytes32 route = keccak256("parked-home-reward");
        PoolConfig memory config; config.key.currency0 = address(token); config.key.currency1 = address(other);
        pools.set(pool, config);
        Position memory p; p.poolId = pool; p.status = PositionStatus.Active; p.homeChain = 1;
        p.homeVault = address(0x1002); p.homeReceiver = address(0x1003);
        p.homeToken0 = address(0x1001); p.homeToken1 = address(0x1004); vault.set(42, p);
        Route memory r; r.sourceChain = block.chainid; r.sourceVault = address(vault); r.sourceToken0 = address(token);
        r.destinationChain = 1; r.destinationVault = p.homeVault; r.destinationReceiver = p.homeReceiver;
        r.destinationToken0 = p.homeToken0; routes.set(route, r);
        token.mint(address(vault), 1009); vm.startPrank(address(vault)); token.approve(address(fees), 1009);
        fees.allocate(42, address(token), 1009); vm.stopPrank();
        p.status = PositionStatus.Parked; vault.set(42, p);
        vm.prank(address(vault)); fees.flushDust(42, address(token));
        fees.bridgeRewards(42, address(token), route);
        BridgeMessage memory message = bridge.message();
        assertEq(message.individual, 809); assertEq(message.collective, 100);
        assertEq(token.balanceOf(address(bridge)), 909); assertEq(fees.accounted(address(token)), 100);
        assertEq(vault.group(42).lpTokenId, 0);
        assertEq(uint256(vault.group(42).status), uint256(PositionStatus.Parked));
    }
}
