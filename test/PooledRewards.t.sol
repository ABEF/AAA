// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZPower} from "../src/ZZZPower.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {Ids, Position, PositionStatus, PoolConfig, BridgeMessage, MessageKind} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockPools} from "./mocks/Mocks.sol";
import {RewardsVaultFixture} from "./RewardsAndFees.t.sol";

contract PooledRewardsTest is Test {
    MockAccess ac; MockToken token0; MockToken token1; MockPools pools;
    RewardsVaultFixture vault; ZZZNFT nft; ZZZPower power; ZZZRewards rewards; ZZZFeeController fees;
    uint256 constant BUCKET = 11; uint256 constant SECOND = 12;
    bytes32 constant POOL = keccak256("pool-owner-index");
    address constant ALICE = address(0xA11CE); address constant BOB = address(0xB0B); address constant CAROL = address(0xCA201);
    address constant FOREIGN_VAULT = address(0xF001); address constant CANONICAL0 = address(0xC001); address constant CANONICAL1 = address(0xC002);
    function setUp() public {
        ac = new MockAccess(); token0 = new MockToken(18); token1 = new MockToken(18); pools = new MockPools();
        nft = new ZZZNFT(address(ac), "ipfs://"); power = new ZZZPower(address(ac)); rewards = new ZZZRewards(address(ac));
        fees = new ZZZFeeController(address(ac)); vault = new RewardsVaultFixture(rewards);
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.NFT, address(nft)); ac.bind(Ids.POWER, address(power));
        ac.bind(Ids.REWARDS, address(rewards)); ac.bind(Ids.FEES, address(fees)); ac.bind(Ids.POOLS, address(pools));
        ac.bind(Ids.RECEIVER, address(this)); rewards.addAsset(address(token0)); rewards.addAsset(address(token1)); ac.seal();
        PoolConfig memory c; c.key.currency0 = address(token0); c.key.currency1 = address(token1); pools.set(POOL, c);
        Position memory p; p.poolId = POOL; p.homeChain = block.chainid; p.homeVault = address(vault);
        p.homeToken0 = address(token0); p.homeToken1 = address(token1); p.status = PositionStatus.Active;
        vault.set(BUCKET, p); vault.set(SECOND, p);
    }
    function _seed(uint256 id, address owner, uint256 bucket, uint256 shares, uint256 weight) private {
        vm.prank(address(vault)); nft.mint(owner, id); vault.join(id, bucket, shares);
        if (weight != 0) { vm.prank(address(vault)); power.add(id, weight); }
    }
    function _credit(uint256 bucket, uint256 personal, uint256 shared) private {
        token0.mint(address(fees), personal + shared); vm.startPrank(address(fees));
        token0.approve(address(rewards), personal + shared); rewards.creditPool(bucket, address(token0), personal, shared); vm.stopPrank();
    }
    function _remote() private {
        Position memory p = vault.group(BUCKET); p.homeChain = block.chainid + 1; p.homeVault = FOREIGN_VAULT;
        p.homeToken0 = CANONICAL0; p.homeToken1 = CANONICAL1; vault.set(BUCKET, p);
    }
    function _allocate(uint256 amount) private {
        token0.mint(address(vault), amount); vm.startPrank(address(vault)); token0.approve(address(fees), amount);
        fees.allocate(BUCKET, address(token0), amount); vm.stopPrank();
    }
    function _snapshot(uint256 personal0, uint256 shared0, uint256 personal1, uint256 shared1)
        private view returns (BridgeMessage memory m) {
        Position memory p = vault.group(BUCKET);
        m.version = 3; m.kind = MessageKind.Principal; m.bucketId = BUCKET; m.homeChain = p.homeChain; m.homeVault = p.homeVault;
        m.canonicalToken0 = p.homeToken0; m.canonicalToken1 = p.homeToken1; m.totalShares = vault.bucketTotalShares(BUCKET);
        m.allocatedIndividual0 = personal0; m.allocatedCollective0 = shared0;
        m.allocatedIndividual1 = personal1; m.allocatedCollective1 = shared1;
    }
    function _remoteCredit(MockToken token, uint256 personal, uint256 shared) private {
        token.mint(address(this), personal + shared); token.approve(address(fees), personal + shared);
        fees.creditRemote(BUCKET, address(token), personal, shared);
    }
    function testOwnerFeesFollowSharesAndCollectiveFollowsPowerAcrossBuckets() public {
        _seed(1, ALICE, BUCKET, 100, 100); _seed(2, BOB, BUCKET, 100, 100); _seed(3, CAROL, SECOND, 200, 200);
        _credit(BUCKET, 100, 80);
        assertEq(rewards.claimable(1, address(token0)), 70); assertEq(rewards.claimable(2, address(token0)), 70);
        assertEq(rewards.claimable(3, address(token0)), 40);
        _credit(SECOND, 80, 0); assertEq(rewards.claimable(3, address(token0)), 120);
        assertEq(rewards.claimable(1, address(token0)), 70);
    }
    function testNewOwnerSharesCannotReceiveHistoricalOwnerFees() public {
        _seed(1, ALICE, BUCKET, 100, 0); _credit(BUCKET, 100, 0); _seed(2, BOB, BUCKET, 100, 0);
        assertEq(rewards.claimable(1, address(token0)), 100); assertEq(rewards.claimable(2, address(token0)), 0);
        assertEq(rewards.paidOwnerIndex(2, address(token0)), rewards.ownerIndex(BUCKET, address(token0)));
        _credit(BUCKET, 100, 0); assertEq(rewards.claimable(1, address(token0)), 150); assertEq(rewards.claimable(2, address(token0)), 50);
    }
    function testTopUpCheckpointDoesNotRepriceOldOwnerFees() public {
        _seed(1, ALICE, BUCKET, 100, 0); _seed(2, BOB, BUCKET, 100, 0); _credit(BUCKET, 100, 0);
        vault.join(1, BUCKET, 200); assertEq(rewards.claimable(1, address(token0)), 50);
        _credit(BUCKET, 100, 0); assertEq(rewards.claimable(1, address(token0)), 125); assertEq(rewards.claimable(2, address(token0)), 75);
    }
    function testOwnerFractionSurvivesClaimsAndShareIncrease() public {
        _seed(1, ALICE, BUCKET, 1, 0); _seed(2, BOB, BUCKET, 3, 0);
        _credit(BUCKET, 1, 0); vm.prank(ALICE); assertEq(rewards.claim(1, address(token0)), 0);
        assertEq(rewards.ownerFraction(1, address(token0)), rewards.SCALE() / 4);
        vault.join(1, BUCKET, 3); _credit(BUCKET, 7, 0);
        vm.prank(ALICE); assertEq(rewards.claim(1, address(token0)), 4);
        vm.prank(BOB); assertEq(rewards.claim(2, address(token0)), 3);
        assertEq(token0.balanceOf(address(rewards)), 1); assertEq(rewards.liabilities(address(token0)), 1);
    }
    function testIndexDivisionRemainderCannotBeCapturedByNewShares() public {
        _seed(1, ALICE, BUCKET, 7, 0); _seed(2, BOB, BUCKET, 11, 0); _credit(BUCKET, 1, 0);
        _seed(3, CAROL, BUCKET, 100000, 0);
        assertEq(rewards.claimable(3, address(token0)), 0);
        assertEq(rewards.claimable(1, address(token0)) + rewards.claimable(2, address(token0)), 0);
        assertEq(rewards.liabilities(address(token0)), 1);
    }
    function testDirectDonationDoesNotPublishOwnerIndex() public {
        _seed(1, ALICE, BUCKET, 100, 0); token0.mint(address(rewards), 1000);
        assertEq(rewards.ownerIndex(BUCKET, address(token0)), 0); assertEq(rewards.claimable(1, address(token0)), 0);
        assertEq(rewards.liabilities(address(token0)), 0);
    }
    function testZeroPowerCollectiveFundsRemainOrphanedForFutureParticipants() public {
        _seed(1, ALICE, BUCKET, 100, 0); _credit(BUCKET, 50, 30);
        vm.prank(address(vault)); power.add(1, 100);
        assertEq(rewards.claimable(1, address(token0)), 50); assertEq(rewards.orphaned(address(token0)), 30);
        assertEq(rewards.liabilities(address(token0)), 50);
    }
    function testUnsentRemoteReservesAreIncludedInDepartureCounters() public {
        _seed(1, ALICE, BUCKET, 100, 100); _remote(); _allocate(100);
        (uint256 personal, uint256 shared) = fees.allocated(BUCKET, CANONICAL0);
        assertEq(personal, 50); assertEq(shared, 30); assertEq(fees.remoteIndividual(BUCKET, address(token0)), 50);
        assertEq(fees.remoteCollective(BUCKET, address(token0)), 30); assertEq(token0.balanceOf(address(fees)), 100);
        assertEq(rewards.claimable(1, address(token0)), 0);
    }
    function testRemoteDustAddsToLifetimeOwnerCounterBeforeDeparture() public {
        _seed(1, ALICE, BUCKET, 100, 100); _remote(); _allocate(9);
        vm.prank(address(vault)); fees.flushDust(BUCKET, address(token0));
        (uint256 personal, uint256 shared) = fees.allocated(BUCKET, CANONICAL0);
        assertEq(personal, 9); assertEq(shared, 0); assertEq(fees.remoteIndividual(BUCKET, address(token0)), 9);
        assertEq(fees.accounted(address(token0)), 9);
    }
    function testCumulativeRemoteBaselinePreservesPastHopsWithoutDoubleCounting() public {
        _seed(1, ALICE, BUCKET, 100, 100); _remote(); fees.importAccounting(_snapshot(1000, 600, 2000, 1200)); _allocate(100);
        (uint256 personal, uint256 shared) = fees.allocated(BUCKET, CANONICAL0);
        assertEq(personal, 1050); assertEq(shared, 630);
        (personal, shared) = fees.allocated(BUCKET, CANONICAL1); assertEq(personal, 2000); assertEq(shared, 1200);
    }
    function testRemoteSnapshotCannotEraseUnsentLiabilities() public {
        _seed(1, ALICE, BUCKET, 100, 100); _remote(); _allocate(100);
        BridgeMessage memory m = _snapshot(49, 30, 0, 0); vm.expectRevert(); fees.importAccounting(m);
        (uint256 personal, uint256 shared) = fees.allocated(BUCKET, CANONICAL0); assertEq(personal, 50); assertEq(shared, 30);
    }
    function testReturnedBucketBarrierRequiresBothOwnerAndCollectiveFunding() public {
        _seed(1, ALICE, BUCKET, 100, 100); fees.importAccounting(_snapshot(50, 30, 0, 0));
        assertFalse(fees.remoteSettled(BUCKET)); _remoteCredit(token0, 50, 0); assertFalse(fees.remoteSettled(BUCKET));
        _remoteCredit(token0, 0, 30); assertTrue(fees.remoteSettled(BUCKET)); assertEq(rewards.claimable(1, address(token0)), 80);
        (uint256 personal, uint256 shared) = fees.allocated(BUCKET, address(token0)); assertEq(personal, 50); assertEq(shared, 30);
    }
    function testBothCanonicalAssetsMustBeFundedBeforeBarrierClears() public {
        _seed(1, ALICE, BUCKET, 100, 100); fees.importAccounting(_snapshot(50, 30, 100, 60));
        _remoteCredit(token0, 50, 30); assertFalse(fees.remoteSettled(BUCKET)); _remoteCredit(token1, 100, 60);
        assertTrue(fees.remoteSettled(BUCKET)); assertEq(rewards.claimable(1, address(token1)), 160);
    }
    function testReversedSnapshotTokenOrderingPreservesCanonicalCounterIdentity() public {
        _seed(1, ALICE, BUCKET, 100, 100); BridgeMessage memory m = _snapshot(100, 60, 50, 30);
        m.canonicalToken0 = address(token1); m.canonicalToken1 = address(token0); fees.importAccounting(m);
        assertEq(fees.expectedIndividual(BUCKET, address(token0)), 50); assertEq(fees.expectedCollective(BUCKET, address(token0)), 30);
        assertEq(fees.expectedIndividual(BUCKET, address(token1)), 100); assertEq(fees.expectedCollective(BUCKET, address(token1)), 60);
    }
    function testHomeSnapshotCannotResetPreviousExpectedCounters() public {
        _seed(1, ALICE, BUCKET, 100, 100); fees.importAccounting(_snapshot(50, 30, 0, 0));
        BridgeMessage memory m = _snapshot(0, 0, 0, 0); vm.expectRevert(); fees.importAccounting(m); assertFalse(fees.remoteSettled(BUCKET));
    }
    function testImportedAccountingRejectsWrongSharesBeforeUpdatingCounters() public {
        _seed(1, ALICE, BUCKET, 100, 100); BridgeMessage memory m = _snapshot(50, 30, 0, 0); m.totalShares++;
        vm.expectRevert(); fees.importAccounting(m); assertEq(fees.expectedIndividual(BUCKET, address(token0)), 0);
    }
    function testAccountingImportRequiresAuthenticatedReceiver() public {
        _seed(1, ALICE, BUCKET, 100, 100); BridgeMessage memory m = _snapshot(50, 30, 0, 0);
        vm.prank(ALICE); vm.expectRevert(); fees.importAccounting(m);
    }
    function testFuzzOwnerClaimsNeverExceedFundedPoolFees(uint96 a, uint96 b, uint96 first, uint96 second) public {
        uint256 aShares = bound(uint256(a), 1, 1e24); uint256 bShares = bound(uint256(b), 1, 1e24);
        uint256 firstFees = bound(uint256(first), 1, 1e24); uint256 secondFees = bound(uint256(second), 1, 1e24);
        _seed(1, ALICE, BUCKET, aShares, 0); _credit(BUCKET, firstFees, 0); _seed(2, BOB, BUCKET, bShares, 0);
        assertEq(rewards.claimable(2, address(token0)), 0); _credit(BUCKET, secondFees, 0);
        vm.prank(ALICE); uint256 paidA = rewards.claim(1, address(token0)); vm.prank(BOB); uint256 paidB = rewards.claim(2, address(token0));
        assertLe(paidA + paidB, firstFees + secondFees);
        assertEq(token0.balanceOf(address(rewards)), rewards.liabilities(address(token0)));
        assertEq(firstFees + secondFees, paidA + paidB + rewards.liabilities(address(token0)));
    }
}
