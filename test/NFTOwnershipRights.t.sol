// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockToken} from "./mocks/Mocks.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @dev TEST ONLY: proves ownership is already committed during a safe-transfer
/// receiver callback. A rejection must roll back both the NFT and its payouts.
contract ImmediateRightsReceiver is IERC721Receiver {
    ZZZNFT private immutable nft;
    address private immutable lpAsset;
    bool private immutable reject;
    bool public sawOwnership;
    constructor(ZZZNFT collection, address asset, bool rejectTransfer) {
        nft = collection; lpAsset = asset; reject = rejectTransfer;
    }
    function onERC721Received(address, address, uint256 id, bytes calldata) external returns (bytes4) {
        require(msg.sender == address(nft));
        sawOwnership = nft.ownerOf(id) == address(this);
        require(sawOwnership);
        ZZZClaimRouter.Claim[] memory requests = new ZZZClaimRouter.Claim[](3);
        requests[0] = ZZZClaimRouter.Claim(id, lpAsset, false);
        requests[1] = ZZZClaimRouter.Claim(id, lpAsset, true);
        requests[2] = ZZZClaimRouter.Claim(id, address(0), true);
        nft.claimRouter().claimBatch(requests);
        require(!reject, "reject after claims");
        return IERC721Receiver.onERC721Received.selector;
    }
    receive() external payable {}
}

contract UnavailableRoyaltyToken is MockToken {
    bool public unavailable;
    constructor() MockToken(6) {}
    function setUnavailable(bool value) external { unavailable = value; }
    function balanceOf(address owner) public view override returns (uint256) {
        require(!unavailable, "balance unavailable");
        return super.balanceOf(owner);
    }
}

/// @notice Real canonical Vault/NFT/Fees/Membership/LP and royalty ledgers.
/// The pool venue, tokens, price feed, authority and VRF are explicit local mocks.
contract NFTOwnershipRightsTest is PooledVaultFixture {
    ZZZRoyaltyRewards private royalties;
    ZZZClaimRouter private router;
    function _ledgers() private {
        assertTrue(OPERATOR != alice && OPERATOR != bob && OPERATOR != CAROL, "operator must be a separate actor");
        assertTrue(alice != bob && alice != CAROL && bob != CAROL, "holders must be separate actors");
        royalties = nft.royaltyRewards(); router = nft.claimRouter();
    }
    address private constant OPERATOR = address(0x0B0B00);
    address private constant CAROL = address(0xCA701);

    function _fundRights(uint256 id) private {
        _ledgers(); nft.addRoyaltyAsset(address(t0));
        venue.setFees(100, 200);
        vault.collectFees(vault.nftBucket(id), block.timestamp + 100);
        t0.mint(address(royalties), 70);
        (bool ok,) = address(royalties).call{value: 3 ether}("");
        require(ok);
    }

    function _claims(uint256 id) private view returns (ZZZClaimRouter.Claim[] memory requests) {
        requests = new ZZZClaimRouter.Claim[](3);
        requests[0] = ZZZClaimRouter.Claim(id, address(t0), false);
        requests[1] = ZZZClaimRouter.Claim(id, address(t0), true);
        requests[2] = ZZZClaimRouter.Claim(id, address(0), true);
    }

    function testApprovedOperatorCanTransferButCannotClaimAnyLedger() public {
        uint256 id = activatedPosition(); _fundRights(id);
        vm.prank(alice); nft.approve(OPERATOR, id);
        vm.startPrank(OPERATOR);
        vm.expectRevert(); rewards.claim(id, address(t0));
        vm.expectRevert(); royalties.claim(id, address(0));
        vm.expectRevert(); router.claimBatch(_claims(id));
        nft.transferFrom(alice, bob, id);
        vm.stopPrank();
        assertEq(nft.getApproved(id), address(0));
        uint256 beforeBalance = t0.balanceOf(bob); uint256 beforeETH = bob.balance;
        vm.prank(bob); uint256[] memory amounts = router.claimBatch(_claims(id));
        assertEq(amounts[0], 90); assertEq(amounts[1], 70); assertEq(amounts[2], 3 ether);
        assertEq(t0.balanceOf(bob) - beforeBalance, 160); assertEq(bob.balance - beforeETH, 3 ether);
        assertEq(vault.sharesOf(id), 2000e18); assertTrue(membership.eligible(id));
    }

    function testSafeTransferReceiverImmediatelyClaimsAsCurrentOwner() public {
        uint256 id = activatedPosition(); _fundRights(id);
        ImmediateRightsReceiver receiver = new ImmediateRightsReceiver(nft, address(t0), false);
        uint256 bucket = vault.nftBucket(id); uint256 shares = vault.sharesOf(id);
        uint8 rarity = nft.rarityOf(id); uint8 palette = nft.paletteOf(id); uint8 pattern = nft.patternOf(id);
        vm.prank(alice); nft.setApprovalForAll(OPERATOR, true);
        vm.prank(OPERATOR); nft.safeTransferFrom(alice, address(receiver), id);
        assertTrue(receiver.sawOwnership()); assertEq(nft.ownerOf(id), address(receiver));
        assertEq(t0.balanceOf(address(receiver)), 160); assertEq(address(receiver).balance, 3 ether);
        assertEq(rewards.claimable(id, address(t0)), 0); assertEq(rewards.claimable(id, address(t1)), 180);
        assertEq(royalties.claimable(id, address(0)), 0);
        assertEq(vault.nftBucket(id), bucket); assertEq(vault.sharesOf(id), shares);
        assertEq(nft.rarityOf(id), rarity); assertEq(nft.paletteOf(id), palette); assertEq(nft.patternOf(id), pattern);
        vm.startPrank(alice);
        vm.expectRevert(); rewards.claim(id, address(t1));
        vm.expectRevert(); royalties.claim(id, address(0));
        vm.stopPrank();
    }

    function testReceiverRejectAfterClaimsRollsBackAllRightsAndTransfer() public {
        uint256 id = activatedPosition(); _fundRights(id);
        ImmediateRightsReceiver receiver = new ImmediateRightsReceiver(nft, address(t0), true);
        vm.prank(alice); nft.approve(OPERATOR, id);
        vm.prank(OPERATOR); vm.expectRevert(bytes("reject after claims"));
        nft.safeTransferFrom(alice, address(receiver), id);
        assertEq(nft.ownerOf(id), alice); assertEq(nft.getApproved(id), OPERATOR);
        assertFalse(receiver.sawOwnership()); assertEq(t0.balanceOf(address(receiver)), 0);
        assertEq(address(receiver).balance, 0); assertEq(rewards.claimable(id, address(t0)), 90);
        assertEq(royalties.pending(address(t0)), 70);
        assertEq(royalties.pending(address(0)), 3 ether);
        vm.prank(alice); router.claimBatch(_claims(id));
        assertEq(rewards.claimable(id, address(t0)), 0);
    }

    function testSuccessiveTransfersCarryAccruedLPFeesAndPendingRoyalties() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        _ledgers(); nft.addRoyaltyAsset(address(t0));
        venue.setFees(200, 0); vault.collectFees(bucket, block.timestamp + 100);
        t0.mint(address(royalties), 50);
        (bool ok,) = address(royalties).call{value: 2 ether}(""); require(ok);
        assertEq(rewards.claimable(id, address(t0)), 180);
        vm.prank(alice); nft.approve(OPERATOR, id);
        vm.prank(OPERATOR); nft.transferFrom(alice, bob, id);
        vm.prank(bob); nft.setApprovalForAll(OPERATOR, true);
        vm.prank(OPERATOR); nft.transferFrom(bob, CAROL, id);
        vm.prank(CAROL); nft.transferFrom(CAROL, bob, id);
        vm.startPrank(alice);
        vm.expectRevert(); rewards.claim(id, address(t0));
        vm.expectRevert(); royalties.claim(id, address(t0));
        vm.stopPrank();
        vm.prank(CAROL); vm.expectRevert(); router.claimBatch(_claims(id));
        uint256 beforeBalance = t0.balanceOf(bob); uint256 beforeETH = bob.balance;
        vm.prank(bob); uint256[] memory paid = router.claimBatch(_claims(id));
        assertEq(paid[0], 180); assertEq(paid[1], 50); assertEq(paid[2], 2 ether);
        assertEq(t0.balanceOf(bob) - beforeBalance, 230); assertEq(bob.balance - beforeETH, 2 ether);
        assertEq(fees.compoundBalance(bucket, address(t0)), 10);
        assertEq(fees.buybackBalance(address(t0)), 10);
        assertEq(royalties.weightOf(id), 1);
    }

    function testClaimBeforeSaleTransfersOnlyRemainingUnclaimedRights() public {
        uint256 id = activatedPosition(); _fundRights(id);
        uint256 aliceBefore = t0.balanceOf(alice); uint256 aliceETH = alice.balance;
        vm.prank(alice); router.claimBatch(_claims(id));
        vm.prank(alice); nft.transferFrom(alice, bob, id);
        vm.prank(bob); uint256[] memory zero = router.claimBatch(_claims(id));
        assertEq(zero[0], 0); assertEq(zero[1], 0); assertEq(zero[2], 0);
        assertEq(t0.balanceOf(alice) - aliceBefore, 160); assertEq(alice.balance - aliceETH, 3 ether);
        // The seller left the second fee asset unclaimed; it follows the NFT.
        vm.prank(bob); assertEq(rewards.claim(id, address(t1)), 180);
        venue.setFees(200, 0); vault.collectFees(vault.nftBucket(id), block.timestamp + 100);
        t0.mint(address(royalties), 20);
        vm.prank(alice); vm.expectRevert(); rewards.claim(id, address(t0));
        vm.prank(bob); uint256[] memory next = router.claimBatch(_claims(id));
        assertEq(next[0], 180); assertEq(next[1], 20); assertEq(next[2], 0);
    }

    function testSaleBeforeClaimImmediatelyRevokesFormerOwner() public {
        uint256 id = activatedPosition(); _fundRights(id);
        vm.prank(alice); nft.transferFrom(alice, bob, id);
        vm.prank(alice); vm.expectRevert(); router.claimBatch(_claims(id));
        vm.prank(bob); uint256[] memory paid = router.claimBatch(_claims(id));
        assertEq(paid[0], 90); assertEq(paid[1], 70); assertEq(paid[2], 3 ether);
        vm.prank(bob); paid = router.claimBatch(_claims(id));
        assertEq(paid[0], 0); assertEq(paid[1], 0); assertEq(paid[2], 0);
    }

    function testUnavailableRoyaltyCurrencyDefersOnlyItsEligibilityWhileActualLPActivates() public {
        uint256 active = activatedPosition(); _fundRights(active);
        UnavailableRoyaltyToken unavailable = new UnavailableRoyaltyToken();
        nft.addRoyaltyAsset(address(unavailable));
        unavailable.mint(address(royalties), 100);
        uint256 next = _mint(bob);
        uint256 before0 = t0.balanceOf(bob); uint256 before1 = t1.balanceOf(bob);
        uint256 bucket = vault.nftBucket(active);
        uint256 oldShares = vault.sharesOf(active); uint256 totalShares = vault.bucketTotalShares(bucket);
        Position memory beforePosition = vault.group(bucket);
        uint256 beforeLP0 = venue.a0(beforePosition.lpTokenId);
        uint256 beforeLP1 = venue.a1(beforePosition.lpTokenId);
        unavailable.setUnavailable(true);
        _activate(bob, next, 1000, 1000);
        assertGt(vault.sharesOf(next), 0); assertEq(vault.nftBucket(next), bucket);
        assertEq(uint256(vault.nftStatus(next)), uint256(PositionStatus.Active));
        assertEq(vault.sharesOf(active), oldShares);
        assertEq(vault.bucketTotalShares(bucket), totalShares + vault.sharesOf(next));
        assertEq(t0.balanceOf(bob), before0 - 1000); assertEq(t1.balanceOf(bob), before1 - 1000);
        assertGe(venue.a0(beforePosition.lpTokenId), beforeLP0 + 1000);
        assertGe(venue.a1(beforePosition.lpTokenId), beforeLP1 + 1000);
        assertTrue(membership.eligible(next)); assertTrue(nft.traitsReady(next));
        assertEq(royalties.weightOf(next), uint256(nft.rarityOf(next)) + 1);
        assertTrue(royalties.eligibleFor(next, address(0)));
        assertTrue(royalties.eligibleFor(next, address(t0)));
        assertFalse(royalties.eligibleFor(next, address(unavailable)));
        assertEq(royalties.claimable(next, address(t0)), 0);
        assertEq(royalties.claimable(next, address(0)), 0);
        // Previously funded LP fees and healthy royalties remain entirely with
        // the incumbent despite the optional currency's isolated read failure.
        vm.prank(alice); uint256[] memory paid = router.claimBatch(_claims(active));
        assertEq(paid[0], 90); assertEq(paid[1], 70); assertEq(paid[2], 3 ether);
        unavailable.mint(address(royalties), 50);
        unavailable.setUnavailable(false); royalties.sync(address(unavailable));
        assertTrue(royalties.eligibleFor(next, address(unavailable)));
        assertEq(royalties.claimable(next, address(unavailable)), 0);
        assertEq(royalties.claimable(active, address(unavailable)), 150);
        vm.prank(alice); assertEq(royalties.claim(active, address(unavailable)), 150);
        // Both deterministic fixture draws are Commun. Future receipts join
        // their equal royalty weights only after the recovery boundary.
        assertEq(royalties.weightOf(active), 1); assertEq(royalties.weightOf(next), 1);
        unavailable.mint(address(royalties), 60);
        assertEq(royalties.claimable(active, address(unavailable)), 30);
        assertEq(royalties.claimable(next, address(unavailable)), 30);
    }
}
