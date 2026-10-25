// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {MockAccess, MockToken, MockPools} from "./mocks/Mocks.sol";

// TEST ONLY: isolated canonical share ledger. Fair share issuance and LP custody
// are exercised against the real Vault in separate suites.
contract RewardsVaultFixture {
    function migrationBudget() external view returns(address){return address(this);}
    function compositionEpoch(uint256) external pure returns(uint64){return 0;}
    mapping(uint256 => uint256) public nftBucket;
    mapping(uint256 => uint256) public sharesOf;
    mapping(uint256 => uint256) public bucketTotalShares;
    mapping(uint256 => bytes32) public homePoolId;
    mapping(uint256 => Position) private groups;
    ZZZRewards private rewards;
    constructor(ZZZRewards rewardLedger) { rewards = rewardLedger; }
    function mintProceedsRecipient() external pure returns(address payable) {return payable(address(0x7EA5));}
    function set(uint256 bucketId, Position memory p) external { groups[bucketId] = p; homePoolId[bucketId] = p.poolId; }
    function group(uint256 bucketId) external view returns (Position memory) { return groups[bucketId]; }
    function join(uint256 id, uint256 bucketId, uint256 increment) external {
        require(nftBucket[id] == 0 || nftBucket[id] == bucketId, "immutable membership");
        nftBucket[id] = bucketId;
        rewards.checkpointOwner(id);
        sharesOf[id] += increment;
        bucketTotalShares[bucketId] += increment;
    }
}
contract RewardsAndFeesTest is Test, IERC721Receiver {
    MockAccess ac; MockToken token; MockToken token1; MockPools pools; RewardsVaultFixture vault;
    ZZZNFT nft; ZZZMembership membership; ZZZRewards rewards; ZZZFeeController fees;
    address alice = address(0xA11CE); address bob = address(0xB0B);
    uint256 constant BUCKET = 7; bytes32 constant POOL = keccak256("shared-rewards-pool");
    function setUp() public {
        ac = new MockAccess(); token = new MockToken(18); token1 = new MockToken(18);
        nft = new ZZZNFT(address(ac), "ipfs://"); membership = new ZZZMembership(address(ac)); rewards = new ZZZRewards(address(ac));
        fees = new ZZZFeeController(address(ac)); pools = new MockPools(); vault = new RewardsVaultFixture(rewards);
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.NFT, address(nft)); ac.bind(Ids.MEMBERSHIP, address(membership));
        ac.bind(Ids.REWARDS, address(rewards)); ac.bind(Ids.FEES, address(fees)); ac.bind(Ids.POOLS, address(pools));
        ac.bind(Ids.BUYBACK, address(this)); rewards.addAsset(address(token));
        nft.configureRandomness(address(new MockVRF()),bytes32(uint256(1)),1,3,500000,false); ac.seal();
        PoolConfig memory c; c.key.currency0 = address(token); c.key.currency1 = address(token1); pools.set(POOL, c);
        Position memory p; p.poolId = POOL; p.status = PositionStatus.Active; vault.set(BUCKET, p);
        vm.prank(address(vault)); nft.mint(alice, 1); vm.prank(address(vault)); nft.mint(bob, 2);
        vault.join(1, BUCKET, 100); _activate(1);
    }
    function _activate(uint256 id) internal { vm.prank(address(vault)); membership.activate(id); }
    function _credit(uint256 personal, uint256 shared) internal {
        token.mint(address(fees), personal + shared);
        vm.startPrank(address(fees)); token.approve(address(rewards), personal + shared);
        rewards.creditPool(BUCKET, address(token), personal, shared); vm.stopPrank();
    }
    function _allocate(uint256 amount) internal {
        token.mint(address(vault), amount); vm.startPrank(address(vault)); token.approve(address(fees), amount);
        fees.allocate(BUCKET, address(token), amount); vm.stopPrank();
    }
    function testNewActivatedNFTCannotClaimPublishedPastReward() public {
        _credit(50, 30); vault.join(2, BUCKET, 100); _activate(2);
        assertEq(rewards.claimable(1, address(token)), 80); assertEq(rewards.claimable(2, address(token)), 0);
        _credit(0, 40); assertEq(rewards.claimable(1, address(token)), 100); assertEq(rewards.claimable(2, address(token)), 20);
    }
    function testTopUpDoesNotIncreaseEqualCollectiveShare() public {
        vault.join(2, BUCKET, 100); _activate(2); _credit(0, 40); vault.join(1, BUCKET, 200);
        assertEq(rewards.claimable(1, address(token)), 20); _credit(0, 40);
        assertEq(rewards.claimable(1, address(token)), 40); assertEq(rewards.claimable(2, address(token)), 40);
        assertEq(membership.totalEligible(), 2);
    }
    function testNFTTransferCarriesUnclaimedRewards() public {
        _credit(50, 30); vm.prank(alice); nft.transferFrom(alice, bob, 1);
        vm.prank(alice); vm.expectRevert(); rewards.claim(1, address(token));
        vm.prank(bob); assertEq(rewards.claim(1, address(token)), 80); assertEq(token.balanceOf(bob), 80);
    }
    function testClaimWorksWhilePaused() public {
        _credit(50, 30); ac.setPaused(true); vm.prank(alice); rewards.claim(1, address(token)); assertEq(token.balanceOf(alice), 80);
    }
    function testClaimsCannotRepeat() public {
        _credit(50, 30); vm.startPrank(alice); rewards.claim(1, address(token));
        assertEq(rewards.claim(1, address(token)), 0); vm.stopPrank(); assertEq(token.balanceOf(alice), 80);
    }
    function testUnauthorizedCredit() public { vm.expectRevert(); rewards.creditPool(BUCKET, address(token), 1, 1); }
    function testUnauthorizedMembershipActivation() public { vm.prank(alice); vm.expectRevert(); membership.activate(2); }
    function testMembershipCannotBeActivatedTwice() public {
        vm.prank(address(vault)); vm.expectRevert(); membership.activate(1); assertEq(membership.totalEligible(), 1);
    }
    function testMissingNFTCannotBecomeEligible() public {
        vm.prank(address(vault)); vm.expectRevert(); membership.activate(999); assertEq(membership.totalEligible(), 1);
    }
    function testUnauthorizedCollectiveCheckpoint() public { vm.expectRevert(); rewards.checkpointAll(1); }
    function testUnauthorizedOwnerCheckpoint() public { vm.expectRevert(); rewards.checkpointOwner(1); }
    function testUnknownBucketCannotReceiveFundedRewards() public {
        token.mint(address(fees), 80); vm.startPrank(address(fees)); token.approve(address(rewards), 80);
        vm.expectRevert(); rewards.creditPool(99, address(token), 50, 30); vm.stopPrank(); assertEq(token.balanceOf(address(fees)), 80);
    }
    function testFractionalClaimsRemainFunded() public {
        vault.join(2, BUCKET, 200); _activate(2);
        // Three equal participants exercise persistent thirds rather than exact halves.
        vm.prank(address(vault)); nft.mint(alice, 3); vault.join(3, BUCKET, 100); _activate(3);
        for (uint256 i; i < 30; ++i) { _credit(0, 1); vm.prank(alice); rewards.claim(1, address(token)); }
        vm.prank(bob); rewards.claim(2, address(token)); vm.prank(alice); rewards.claim(3, address(token));
        assertLe(token.balanceOf(alice) + token.balanceOf(bob), 30);
        assertGe(token.balanceOf(address(rewards)), rewards.liabilities(address(token)));
    }
    function testNFTSupportsStandardERC721() public { assertTrue(nft.supportsInterface(0x80ac58cd)); }
    function testUnsafeReceiverRejected() public {
        vm.prank(alice); vm.expectRevert(); nft.safeTransferFrom(alice, address(token), 1); assertEq(nft.ownerOf(1), alice);
    }
    function testFeeSplitIsExactAndBacked() public {
        _allocate(1000);
        assertEq(rewards.ownerIndex(BUCKET, address(token)), 800 * rewards.SCALE() / 100);
        assertEq(rewards.index(address(token)), 100 * rewards.SCALE());
        assertEq(rewards.claimable(1, address(token)), 900); assertEq(rewards.liabilities(address(token)), 900);
        assertEq(fees.compoundBalance(BUCKET, address(token)), 50); assertEq(fees.buybackBalance(address(token)), 50);
        assertEq(token.balanceOf(address(fees)), 100); assertEq(fees.accounted(address(token)), 100);
    }
    function testTinyFeesCannotManipulateSplitWithoutMembershipBoundary() public {
        for (uint256 i; i < 19; ++i) _allocate(1);
        assertEq(rewards.claimable(1, address(token)), 0); assertEq(rewards.liabilities(address(token)), 0);
        assertEq(fees.dust(BUCKET, address(token)), 19); assertEq(fees.accounted(address(token)), 19);
        assertEq(fees.compoundBalance(BUCKET, address(token)), 0); assertEq(fees.buybackBalance(address(token)), 0);
        _allocate(1);
        assertEq(rewards.claimable(1, address(token)), 18); assertEq(fees.compoundBalance(BUCKET, address(token)), 1);
        assertEq(fees.buybackBalance(address(token)), 1); assertEq(fees.dust(BUCKET, address(token)), 0);
    }
    function testDustOnMigrationGoesToIncumbentOwners() public {
        _allocate(19); Position memory p = vault.group(BUCKET); p.status = PositionStatus.Outbound; vault.set(BUCKET, p);
        vm.prank(address(vault)); fees.flushDust(BUCKET, address(token));
        assertEq(rewards.claimable(1, address(token)), 19); assertEq(fees.accounted(address(token)), 0);
    }
    function testDustBeforeJoinCannotBeClaimedByEntrant() public {
        _allocate(19); vm.prank(address(vault)); fees.flushDust(BUCKET, address(token)); vault.join(2, BUCKET, 100); _activate(2);
        assertEq(rewards.claimable(1, address(token)), 19); assertEq(rewards.claimable(2, address(token)), 0); _allocate(20);
        // Each new basket funds 8 owner and 1 collective unit for each participant.
        assertEq(rewards.claimable(1, address(token)), 28); assertEq(rewards.claimable(2, address(token)), 9);
        assertEq(rewards.liabilities(address(token)),37);
        _allocate(20);
        assertEq(rewards.claimable(1, address(token)),37); assertEq(rewards.claimable(2, address(token)),18);
    }
    function testUnauthorizedReserveRelease() public {
        _allocate(100); vm.prank(alice); vm.expectRevert(); fees.releaseCompound(BUCKET, address(token));
        vm.prank(alice); vm.expectRevert(); fees.releaseBuyback(address(token), 10);
    }
    function testFuzzFeeConservation(uint96 amount) public {
        vm.assume(amount > 0); _allocate(amount); uint256 units = uint256(amount) / 20;
        assertEq(rewards.claimable(1, address(token)), units * 18);
        assertEq(fees.compoundBalance(BUCKET, address(token)) + fees.buybackBalance(address(token)) + fees.dust(BUCKET, address(token)), uint256(amount) - units * 18);
        assertEq(fees.accounted(address(token)), token.balanceOf(address(fees)));
    }
    function testFuzzFeeChunkingPreservesTwentyUnitBaskets(uint96 first, uint96 second) public {
        vm.assume(first > 0 && second > 0); _allocate(first); _allocate(second);
        uint256 total = uint256(first) + second; uint256 units = total / 20;
        assertEq(rewards.claimable(1, address(token)), units * 18);
        assertEq(fees.compoundBalance(BUCKET, address(token)), units); assertEq(fees.buybackBalance(address(token)), units);
        assertEq(fees.dust(BUCKET, address(token)), total % 20);
        assertEq(fees.accounted(address(token)), units * 2 + total % 20);
        assertEq(fees.accounted(address(token)), token.balanceOf(address(fees)));
    }
    function onERC721Received(address, address, uint256, bytes calldata) external pure override returns (bytes4) { return IERC721Receiver.onERC721Received.selector; }
}
