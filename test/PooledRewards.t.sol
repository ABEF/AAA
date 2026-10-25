// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {MockAccess, MockToken, MockPools} from "./mocks/Mocks.sol";
import {RewardsVaultFixture} from "./RewardsAndFees.t.sol";

contract PooledRewardsTest is Test {
    MockAccess ac; MockToken token0; MockToken token1; MockPools pools;
    RewardsVaultFixture vault; ZZZNFT nft; ZZZMembership membership; ZZZRewards rewards; ZZZFeeController fees;
    uint256 constant BUCKET = 11; uint256 constant SECOND = 12;
    bytes32 constant POOL = keccak256("pool-owner-index");
    address constant ALICE = address(0xA11CE); address constant BOB = address(0xB0B); address constant CAROL = address(0xCA201);
    address constant FOREIGN_VAULT = address(0xF001); address constant CANONICAL0 = address(0xC001); address constant CANONICAL1 = address(0xC002);
    function setUp() public {
        ac = new MockAccess(); token0 = new MockToken(18); token1 = new MockToken(18); pools = new MockPools();
        nft = new ZZZNFT(address(ac), "ipfs://"); membership = new ZZZMembership(address(ac)); rewards = new ZZZRewards(address(ac));
        fees = new ZZZFeeController(address(ac)); vault = new RewardsVaultFixture(rewards);
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.NFT, address(nft)); ac.bind(Ids.MEMBERSHIP, address(membership));
        ac.bind(Ids.REWARDS, address(rewards)); ac.bind(Ids.FEES, address(fees)); ac.bind(Ids.POOLS, address(pools));
        rewards.addAsset(address(token0)); rewards.addAsset(address(token1));
        nft.configureRandomness(address(new MockVRF()),bytes32(uint256(1)),1,3,500000,false); ac.seal();
        PoolConfig memory c; c.key.currency0 = address(token0); c.key.currency1 = address(token1); pools.set(POOL, c);
        Position memory p; p.poolId = POOL; p.homeChain = block.chainid; p.homeVault = address(vault);
        p.homeToken0 = address(token0); p.homeToken1 = address(token1); p.status = PositionStatus.Active;
        vault.set(BUCKET, p); vault.set(SECOND, p);
    }
    function _seed(uint256 id, address owner, uint256 bucket, uint256 shares, bool activated) private {
        vm.prank(address(vault)); nft.mint(owner, id); vault.join(id, bucket, shares);
        if (activated) { vm.prank(address(vault)); membership.activate(id); }
    }
    function _credit(uint256 bucket, uint256 personal, uint256 shared) private {
        token0.mint(address(fees), personal + shared); vm.startPrank(address(fees));
        token0.approve(address(rewards), personal + shared); rewards.creditPool(bucket, address(token0), personal, shared); vm.stopPrank();
    }
    function _allocate(uint256 amount) private {
        token0.mint(address(vault), amount); vm.startPrank(address(vault)); token0.approve(address(fees), amount);
        fees.allocate(BUCKET, address(token0), amount); vm.stopPrank();
    }
    function testOwnerFeesFollowSharesAndCollectiveIsEqualAcrossBuckets() public {
        _seed(1, ALICE, BUCKET, 100, true); _seed(2, BOB, BUCKET, 100, true); _seed(3, CAROL, SECOND, 200, true);
        _credit(BUCKET, 100, 60);
        assertEq(rewards.claimable(1, address(token0)), 70); assertEq(rewards.claimable(2, address(token0)), 70);
        assertEq(rewards.claimable(3, address(token0)), 20);
        _credit(SECOND, 80, 0); assertEq(rewards.claimable(3, address(token0)), 100);
        assertEq(rewards.claimable(1, address(token0)), 70);
    }
    function testNewOwnerSharesCannotReceiveHistoricalOwnerFees() public {
        _seed(1, ALICE, BUCKET, 100, false); _credit(BUCKET, 100, 0); _seed(2, BOB, BUCKET, 100, false);
        assertEq(rewards.claimable(1, address(token0)), 100); assertEq(rewards.claimable(2, address(token0)), 0);
        assertEq(rewards.paidOwnerIndex(2, address(token0)), rewards.ownerIndex(BUCKET, address(token0)));
        _credit(BUCKET, 100, 0); assertEq(rewards.claimable(1, address(token0)), 150); assertEq(rewards.claimable(2, address(token0)), 50);
    }
    function testTopUpCheckpointDoesNotRepriceOldOwnerFees() public {
        _seed(1, ALICE, BUCKET, 100, false); _seed(2, BOB, BUCKET, 100, false); _credit(BUCKET, 100, 0);
        vault.join(1, BUCKET, 200); assertEq(rewards.claimable(1, address(token0)), 50);
        _credit(BUCKET, 100, 0); assertEq(rewards.claimable(1, address(token0)), 125); assertEq(rewards.claimable(2, address(token0)), 75);
    }
    function testOwnerFractionSurvivesClaimsAndShareIncrease() public {
        _seed(1, ALICE, BUCKET, 1, false); _seed(2, BOB, BUCKET, 3, false);
        _credit(BUCKET, 1, 0); vm.prank(ALICE); assertEq(rewards.claim(1, address(token0)), 0);
        assertEq(rewards.ownerFraction(1, address(token0)), rewards.SCALE() / 4);
        vault.join(1, BUCKET, 3); _credit(BUCKET, 7, 0);
        vm.prank(ALICE); assertEq(rewards.claim(1, address(token0)), 4);
        vm.prank(BOB); assertEq(rewards.claim(2, address(token0)), 3);
        assertEq(token0.balanceOf(address(rewards)), 1); assertEq(rewards.liabilities(address(token0)), 1);
    }
    function testIndexDivisionRemainderCannotBeCapturedByNewShares() public {
        _seed(1, ALICE, BUCKET, 7, false); _seed(2, BOB, BUCKET, 11, false); _credit(BUCKET, 1, 0);
        _seed(3, CAROL, BUCKET, 100000, false);
        assertEq(rewards.claimable(3, address(token0)), 0);
        assertEq(rewards.claimable(1, address(token0)) + rewards.claimable(2, address(token0)), 0);
        assertEq(rewards.liabilities(address(token0)), 1);
    }
    function testDirectDonationDoesNotPublishOwnerIndex() public {
        _seed(1, ALICE, BUCKET, 100, false); token0.mint(address(rewards), 1000);
        assertEq(rewards.ownerIndex(BUCKET, address(token0)), 0); assertEq(rewards.claimable(1, address(token0)), 0);
        assertEq(rewards.liabilities(address(token0)), 0);
    }
    function testNoEligibleNFTCollectiveFundsRemainOrphanedForFutureParticipants() public {
        _seed(1, ALICE, BUCKET, 100, false); _credit(BUCKET, 50, 30);
        vm.prank(address(vault)); membership.activate(1);
        assertEq(rewards.claimable(1, address(token0)), 50); assertEq(rewards.orphaned(address(token0)), 30);
        assertEq(rewards.liabilities(address(token0)), 50);
    }
    function testFuzzOwnerClaimsNeverExceedFundedPoolFees(uint96 a, uint96 b, uint96 first, uint96 second) public {
        uint256 aShares = bound(uint256(a), 1, 1e24); uint256 bShares = bound(uint256(b), 1, 1e24);
        uint256 firstFees = bound(uint256(first), 1, 1e24); uint256 secondFees = bound(uint256(second), 1, 1e24);
        _seed(1, ALICE, BUCKET, aShares, false); _credit(BUCKET, firstFees, 0); _seed(2, BOB, BUCKET, bShares, false);
        assertEq(rewards.claimable(2, address(token0)), 0); _credit(BUCKET, secondFees, 0);
        vm.prank(ALICE); uint256 paidA = rewards.claim(1, address(token0)); vm.prank(BOB); uint256 paidB = rewards.claim(2, address(token0));
        assertLe(paidA + paidB, firstFees + secondFees);
        assertEq(token0.balanceOf(address(rewards)), rewards.liabilities(address(token0)));
        assertEq(firstFees + secondFees, paidA + paidB + rewards.liabilities(address(token0)));
    }
}
