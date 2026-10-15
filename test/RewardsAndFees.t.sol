// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZPower} from "../src/ZZZPower.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockPools} from "./mocks/Mocks.sol";

// TEST ONLY: isolated canonical share ledger. Fair share issuance and LP custody
// are exercised against the real Vault in separate suites.
contract RewardsVaultFixture {
    mapping(uint256 => uint256) public nftBucket;
    mapping(uint256 => uint256) public sharesOf;
    mapping(uint256 => uint256) public bucketTotalShares;
    mapping(uint256 => bytes32) public homePoolId;
    mapping(uint256 => Position) private groups;
    ZZZRewards private rewards;
    constructor(ZZZRewards rewardLedger) { rewards = rewardLedger; }
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
    ZZZNFT nft; ZZZPower power; ZZZRewards rewards; ZZZFeeController fees;
    address alice = address(0xA11CE); address bob = address(0xB0B);
    uint256 constant BUCKET = 7; bytes32 constant POOL = keccak256("shared-rewards-pool");
    function setUp() public {
        ac = new MockAccess(); token = new MockToken(18); token1 = new MockToken(18);
        nft = new ZZZNFT(address(ac), "ipfs://"); power = new ZZZPower(address(ac)); rewards = new ZZZRewards(address(ac));
        fees = new ZZZFeeController(address(ac)); pools = new MockPools(); vault = new RewardsVaultFixture(rewards);
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.NFT, address(nft)); ac.bind(Ids.POWER, address(power));
        ac.bind(Ids.REWARDS, address(rewards)); ac.bind(Ids.FEES, address(fees)); ac.bind(Ids.POOLS, address(pools));
        ac.bind(Ids.BUYBACK, address(this)); rewards.addAsset(address(token)); ac.seal();
        PoolConfig memory c; c.key.currency0 = address(token); c.key.currency1 = address(token1); pools.set(POOL, c);
        Position memory p; p.poolId = POOL; p.homeChain = block.chainid; p.homeVault = address(vault);
        p.homeToken0 = address(token); p.homeToken1 = address(token1); p.status = PositionStatus.Active; vault.set(BUCKET, p);
        vm.prank(address(vault)); nft.mint(alice, 1); vm.prank(address(vault)); nft.mint(bob, 2);
        vault.join(1, BUCKET, 100); _power(1, 100);
    }
    function _power(uint256 id, uint256 amount) internal { vm.prank(address(vault)); power.add(id, amount); }
    function _credit(uint256 personal, uint256 shared) internal {
        token.mint(address(fees), personal + shared);
        vm.startPrank(address(fees)); token.approve(address(rewards), personal + shared);
        rewards.creditPool(BUCKET, address(token), personal, shared); vm.stopPrank();
    }
    function _allocate(uint256 amount) internal {
        token.mint(address(vault), amount); vm.startPrank(address(vault)); token.approve(address(fees), amount);
        fees.allocate(BUCKET, address(token), amount); vm.stopPrank();
    }
    function testNewPowerCannotClaimPublishedPastReward() public {
        _credit(50, 30); vault.join(2, BUCKET, 100); _power(2, 100);
        assertEq(rewards.claimable(1, address(token)), 80); assertEq(rewards.claimable(2, address(token)), 0);
        _credit(0, 40); assertEq(rewards.claimable(1, address(token)), 100); assertEq(rewards.claimable(2, address(token)), 20);
    }
    function testIncreasePowerCheckpointsEarlierAllocation() public {
        vault.join(2, BUCKET, 100); _power(2, 100); _credit(0, 40); _power(1, 200);
        assertEq(rewards.claimable(1, address(token)), 20); _credit(0, 40);
        assertEq(rewards.claimable(1, address(token)), 50); assertEq(rewards.claimable(2, address(token)), 30);
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
    function testUnauthorizedPowerChange() public { vm.prank(alice); vm.expectRevert(); power.add(1, 100); }
    function testUnauthorizedOwnerCheckpoint() public { vm.expectRevert(); rewards.checkpointOwner(1); }
    function testUnknownBucketCannotReceiveFundedRewards() public {
        token.mint(address(fees), 80); vm.startPrank(address(fees)); token.approve(address(rewards), 80);
        vm.expectRevert(); rewards.creditPool(99, address(token), 50, 30); vm.stopPrank(); assertEq(token.balanceOf(address(fees)), 80);
    }
    function testFractionalClaimsRemainFunded() public {
        vault.join(2, BUCKET, 200); _power(2, 200);
        for (uint256 i; i < 30; ++i) { _credit(0, 1); vm.prank(alice); rewards.claim(1, address(token)); }
        vm.prank(bob); rewards.claim(2, address(token)); assertLe(token.balanceOf(alice) + token.balanceOf(bob), 30);
        assertGe(token.balanceOf(address(rewards)), rewards.liabilities(address(token)));
    }
    function testNFTSupportsStandardERC721() public { assertTrue(nft.supportsInterface(0x80ac58cd)); }
    function testUnsafeReceiverRejected() public {
        vm.prank(alice); vm.expectRevert(); nft.safeTransferFrom(alice, address(token), 1); assertEq(nft.ownerOf(1), alice);
    }
    function testFeeSplitIsExactAndBacked() public {
        _allocate(1000); assertEq(rewards.claimable(1, address(token)), 800); assertEq(fees.compoundBalance(BUCKET, address(token)), 100);
        assertEq(fees.buybackBalance(address(token)), 100); assertEq(token.balanceOf(address(fees)), 200); assertEq(fees.accounted(address(token)), 200);
    }
    function testTinyFeesCannotManipulateSplitWithoutMembershipBoundary() public {
        for (uint256 i; i < 10; ++i) _allocate(1);
        assertEq(rewards.claimable(1, address(token)), 8); assertEq(fees.compoundBalance(BUCKET, address(token)), 1);
        assertEq(fees.buybackBalance(address(token)), 1); assertEq(fees.dust(BUCKET, address(token)), 0);
    }
    function testDustOnMigrationGoesToIncumbentOwners() public {
        _allocate(9); Position memory p = vault.group(BUCKET); p.status = PositionStatus.Outbound; vault.set(BUCKET, p);
        vm.prank(address(vault)); fees.flushDust(BUCKET, address(token));
        assertEq(rewards.claimable(1, address(token)), 9); assertEq(fees.accounted(address(token)), 0);
    }
    function testDustBeforeJoinCannotBeClaimedByEntrant() public {
        _allocate(9); vm.prank(address(vault)); fees.flushDust(BUCKET, address(token)); vault.join(2, BUCKET, 100); _power(2, 100);
        assertEq(rewards.claimable(1, address(token)), 9); assertEq(rewards.claimable(2, address(token)), 0); _allocate(10);
        // Owner 2.5 and collective 1.5 retain separate half-unit fractions.
        assertEq(rewards.claimable(1, address(token)), 12); assertEq(rewards.claimable(2, address(token)), 3);
        assertEq(rewards.liabilities(address(token)),17);
        _allocate(10);
        assertEq(rewards.claimable(1, address(token)),17); assertEq(rewards.claimable(2, address(token)),8);
    }
    function testUnauthorizedReserveRelease() public {
        _allocate(100); vm.prank(alice); vm.expectRevert(); fees.releaseCompound(BUCKET, address(token));
        vm.prank(alice); vm.expectRevert(); fees.releaseBuyback(address(token), 10);
    }
    function testFuzzFeeConservation(uint96 amount) public {
        vm.assume(amount > 0); _allocate(amount); uint256 units = uint256(amount) / 10;
        assertEq(rewards.claimable(1, address(token)), units * 8);
        assertEq(fees.compoundBalance(BUCKET, address(token)) + fees.buybackBalance(address(token)) + fees.dust(BUCKET, address(token)), uint256(amount) - units * 8);
        assertEq(fees.accounted(address(token)), token.balanceOf(address(fees)));
    }
    function onERC721Received(address, address, uint256, bytes calldata) external pure override returns (bytes4) { return IERC721Receiver.onERC721Received.selector; }
}
