// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, TaxToken} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

/// @dev TEST ONLY: canonical shares without LP custody. Claims use the real
/// NFT, LP ledger, equal membership, royalty ledger and immutable claim router.
contract ClaimVaultFixture {
    ZZZNFT private nft;
    ZZZRewards private rewards;
    ZZZMembership private membership;
    mapping(uint256 => uint256) public nftBucket;
    mapping(uint256 => uint256) public sharesOf;
    mapping(uint256 => uint256) public bucketTotalShares;
    constructor(ZZZNFT collection, ZZZRewards ledger, ZZZMembership members) {
        nft = collection; rewards = ledger; membership = members;
    }
    function mintProceedsRecipient() external pure returns (address payable) { return payable(address(0x7EA5)); }
    function mint(address owner, uint256 id) external { nft.mint(owner, id); }
    function activate(uint256 id, uint256 shares) external {
        nftBucket[id] = 1;
        rewards.checkpointOwner(id);
        sharesOf[id] = shares;
        bucketTotalShares[1] += shares;
        membership.activate(id);
        nft.notifyContribution(id);
    }
}

contract ClaimRouterOwner is IERC721Receiver {
    ZZZClaimRouter public immutable router;
    ZZZNFT public immutable nft;
    uint256 public callbackId;
    uint256 public transferId;
    address public transferTo;
    bool public rejectPayment;
    bool public attempted;
    bool public reentered;
    uint256 public refund;

    constructor(ZZZClaimRouter helper, ZZZNFT collection) { router = helper; nft = collection; }
    function configure(uint256 id, bool reject, uint256 moveId, address recipient, uint256 sendBack) external {
        callbackId = id; rejectPayment = reject; transferId = moveId; transferTo = recipient; refund = sendBack;
    }
    function claim(ZZZClaimRouter.Claim[] calldata requests) external returns (uint256[] memory) {
        return router.claimBatch(requests);
    }
    function onERC721Received(address, address, uint256, bytes calldata) external pure returns (bytes4) {
        return IERC721Receiver.onERC721Received.selector;
    }
    receive() external payable {
        require(!rejectPayment, "owner rejects ETH");
        attempted = true;
        ZZZClaimRouter.Claim[] memory requests = new ZZZClaimRouter.Claim[](1);
        requests[0] = ZZZClaimRouter.Claim(callbackId, address(0), true);
        (reentered,) = address(router).call(abi.encodeCall(ZZZClaimRouter.claimBatch, (requests)));
        if (transferId != 0) nft.transferFrom(address(this), transferTo, transferId);
        if (refund != 0) {
            (bool ok,) = address(nft.royaltyRewards()).call{value: refund}("");
            require(ok);
        }
    }
}

contract ClaimRouterTest is Test {
    MockAccess private access;
    ZZZNFT private nft;
    ZZZRewards private rewards;
    ZZZRoyaltyRewards private royalties;
    ZZZMembership private membership;
    ZZZClaimRouter private router;
    ClaimVaultFixture private vault;
    MockVRF private vrf;
    MockToken private token;
    MockToken private other;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address private constant ATTACKER = address(0xBAD);

    function setUp() public {
        access = new MockAccess(); ProtocolPolicyFixture.bind(address(access)); vrf = new MockVRF(); token = new MockToken(18); other = new MockToken(6);
        nft = new ZZZNFT(address(access), "ipfs://example/"); rewards = new ZZZRewards(address(access));
        royalties = nft.royaltyRewards(); router = nft.claimRouter(); membership = new ZZZMembership(address(access));
        vault = new ClaimVaultFixture(nft, rewards, membership);
        access.bind(Ids.NFT, address(nft)); access.bind(Ids.REWARDS, address(rewards));
        access.bind(Ids.MEMBERSHIP, address(membership)); access.bind(Ids.VAULT, address(vault));
        access.bind(Ids.FEES, address(this));
        rewards.addAsset(address(token)); rewards.addAsset(address(other));
        nft.addRoyaltyAsset(address(token)); nft.addRoyaltyAsset(address(other));
        ProtocolPolicyFixture.randomness(address(nft.access()),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        access.seal();
        _mint(ALICE, 1, 100); _mint(ALICE, 2, 300); _mint(BOB, 3, 100); _mint(ALICE, 4, 0);
        vm.deal(address(this), 100 ether);
    }

    function _mint(address owner, uint256 id, uint256 shares) private {
        vault.mint(owner, id); vrf.fulfill(nft.requestOf(id), 0, 0); nft.finalizeTraits(id);
        if (shares != 0) vault.activate(id, shares);
    }
    function _credit(MockToken asset, uint256 personal, uint256 collective) private {
        asset.mint(address(this), personal + collective); asset.approve(address(rewards), personal + collective);
        rewards.creditPool(1, address(asset), personal, collective);
    }
    function _fund() private {
        _credit(token, 1500, 1500); _credit(other, 3000, 3000);
        token.mint(address(royalties), 900); other.mint(address(royalties), 1800);
        (bool ok,) = address(royalties).call{value: 3 ether}(""); require(ok);
    }
    function _one(uint256 id, address asset, bool royalty) private pure returns (ZZZClaimRouter.Claim[] memory list) {
        list = new ZZZClaimRouter.Claim[](1); list[0] = ZZZClaimRouter.Claim(id, asset, royalty);
    }
    function _both(uint256 id) private view returns (ZZZClaimRouter.Claim[] memory list) {
        list = new ZZZClaimRouter.Claim[](3);
        list[0] = ZZZClaimRouter.Claim(id, address(token), false);
        list[1] = ZZZClaimRouter.Claim(id, address(token), true);
        list[2] = ZZZClaimRouter.Claim(id, address(0), true);
    }

    function testImmutableEndpointsAndNoApprovalsOrCustody() public {
        assertEq(address(router.access()), address(access)); assertEq(router.nft(), address(nft));
        assertEq(router.royalties(), address(royalties)); assertEq(nft.getApproved(1), address(0));
        assertFalse(nft.isApprovedForAll(ALICE, address(router))); _fund();
        vm.prank(ALICE); router.claimBatch(_both(1));
        assertEq(token.balanceOf(ALICE), 1100); assertEq(ALICE.balance, 1 ether);
        assertEq(token.balanceOf(address(router)), 0); assertEq(address(router).balance, 0);
        assertEq(token.allowance(address(router), address(rewards)), 0);
    }

    function testMultipleNFTsAssetsAndLedgersReturnSeparateRawAmounts() public {
        _fund(); ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](6);
        list[0] = ZZZClaimRouter.Claim(1, address(token), false);
        list[1] = ZZZClaimRouter.Claim(2, address(other), false);
        list[2] = ZZZClaimRouter.Claim(1, address(token), true);
        list[3] = ZZZClaimRouter.Claim(2, address(other), true);
        list[4] = ZZZClaimRouter.Claim(1, address(0), true);
        list[5] = ZZZClaimRouter.Claim(2, address(0), true);
        vm.prank(ALICE); uint256[] memory amounts = router.claimBatch(list);
        assertEq(amounts.length, 6); assertEq(amounts[0], 800); assertEq(amounts[1], 2800);
        assertEq(amounts[2], 300); assertEq(amounts[3], 600); assertEq(amounts[4], 1 ether); assertEq(amounts[5], 1 ether);
        assertEq(token.balanceOf(ALICE), 1100); assertEq(other.balanceOf(ALICE), 3400); assertEq(ALICE.balance, 2 ether);
        assertEq(rewards.claimable(3, address(token)), 800); assertEq(royalties.claimable(3, address(0)), 1 ether);
    }

    function testAttackerAndNFTApprovalDoNotAuthorizeClaims() public {
        _fund(); vm.prank(ALICE); nft.setApprovalForAll(ATTACKER, true);
        vm.prank(ATTACKER); vm.expectRevert(ZZZClaimRouter.Unauthorized.selector); router.claimBatch(_both(1));
        vm.prank(ATTACKER); vm.expectRevert(); rewards.claimFor(1, address(token), ALICE);
        vm.prank(ATTACKER); vm.expectRevert(); royalties.claimFor(1, address(0), ALICE);
        assertEq(rewards.claimable(1, address(token)), 800); assertEq(royalties.pending(address(0)), 3 ether);
    }

    function testRouterCannotRedirectToWrongOwnerAtLedger() public {
        _fund(); vm.prank(address(router)); vm.expectRevert(); rewards.claimFor(1, address(token), ATTACKER);
        vm.prank(address(router)); vm.expectRevert(); royalties.claimFor(1, address(0), ATTACKER);
    }

    function testTransferredNFTClaimsBelongOnlyToNewOwner() public {
        _fund(); vm.prank(ALICE); nft.transferFrom(ALICE, BOB, 1);
        vm.prank(ALICE); vm.expectRevert(ZZZClaimRouter.Unauthorized.selector); router.claimBatch(_both(1));
        vm.prank(BOB); router.claimBatch(_both(1));
        assertEq(token.balanceOf(BOB), 1100); assertEq(BOB.balance, 1 ether); assertEq(token.balanceOf(ALICE), 0);
    }

    function testPauseAndUnavailableValuationDoNotBlockClaims() public {
        _fund(); access.setPaused(true); (bool available,) = nft.currentLPValue(1); assertFalse(available);
        vm.prank(ALICE); router.claimBatch(_both(1));
        assertEq(token.balanceOf(ALICE), 1100); assertEq(ALICE.balance, 1 ether);
    }

    function testEmptyOversizedAndDuplicateBatchesRejected() public {
        vm.prank(ALICE); vm.expectRevert(ZZZClaimRouter.InvalidBatch.selector);
        router.claimBatch(new ZZZClaimRouter.Claim[](0));
        vm.prank(ALICE); vm.expectRevert(ZZZClaimRouter.InvalidBatch.selector);
        router.claimBatch(new ZZZClaimRouter.Claim[](33));
        ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](2);
        list[0] = ZZZClaimRouter.Claim(1, address(token), false); list[1] = list[0];
        vm.prank(ALICE); vm.expectRevert(ZZZClaimRouter.DuplicateClaim.selector); router.claimBatch(list);
    }

    function testMixedOwnerAndNonexistentNFTFailBeforePayouts() public {
        _fund(); ZZZClaimRouter.Claim[] memory list = _both(1); list[1].nftId = 3;
        vm.prank(ALICE); vm.expectRevert(ZZZClaimRouter.Unauthorized.selector); router.claimBatch(list);
        assertEq(token.balanceOf(ALICE), 0); assertEq(royalties.pending(address(0)), 3 ether);
        vm.prank(ALICE); vm.expectRevert(); router.claimBatch(_one(999, address(0), true));
    }

    function testUnsupportedAssetAtomicallyRollsBackEarlierLPAndRoyaltyClaims() public {
        _fund(); ZZZClaimRouter.Claim[] memory list = _both(1); list[2].asset = address(0xBAD);
        vm.prank(ALICE); vm.expectRevert(); router.claimBatch(list);
        assertEq(token.balanceOf(ALICE), 0); assertEq(rewards.claimable(1, address(token)), 800);
        assertEq(royalties.pending(address(token)), 900); assertEq(royalties.claimable(1, address(token)), 300);
        vm.prank(ALICE); vm.expectRevert(); router.claimBatch(_one(1, address(0xBAD), false));
    }

    function testUnsealedOrNoncanonicalBindingRejected() public {
        MockAccess unsealed = new MockAccess(); ProtocolPolicyFixture.bind(address(unsealed)); ZZZNFT otherNFT = new ZZZNFT(address(unsealed), "");
        ZZZClaimRouter unsealedRouter = otherNFT.claimRouter();
        vm.expectRevert(ZZZClaimRouter.InvalidConfiguration.selector); unsealedRouter.claimBatch(_both(1));
        access.bind(Ids.NFT, address(otherNFT));
        vm.prank(ALICE); vm.expectRevert(ZZZClaimRouter.InvalidConfiguration.selector); router.claimBatch(_both(1));
    }

    function testMissingLPDependencyDoesNotBlockRoyaltyOnlyBatch() public {
        _fund(); access.bind(Ids.REWARDS, address(0));
        vm.prank(ALICE); router.claimBatch(_one(1, address(0), true)); assertEq(ALICE.balance, 1 ether);
        vm.prank(ALICE); vm.expectRevert(ZZZClaimRouter.InvalidConfiguration.selector);
        router.claimBatch(_one(1, address(token), false));
    }

    function testNativeCallbackCannotReenterBatchAndNeverReceivesThroughRouter() public {
        ClaimRouterOwner owner = new ClaimRouterOwner(router, nft);
        vm.prank(ALICE); nft.transferFrom(ALICE, address(owner), 1); owner.configure(1, false, 0, address(0), 0);
        _fund(); uint256[] memory amounts = owner.claim(_both(1));
        assertEq(amounts[2], 1 ether); assertTrue(owner.attempted()); assertFalse(owner.reentered());
        assertEq(address(owner).balance, 1 ether); assertEq(token.balanceOf(address(owner)), 1100);
        assertEq(address(router).balance, 0);
    }

    function testNativeReceiverRevertRollsBackWholeBatchThenERC20CanClaimSeparately() public {
        ClaimRouterOwner owner = new ClaimRouterOwner(router, nft);
        vm.prank(ALICE); nft.transferFrom(ALICE, address(owner), 1); owner.configure(1, true, 0, address(0), 0);
        _fund(); vm.expectRevert(ZZZRoyaltyRewards.NativeTransferFailed.selector); owner.claim(_both(1));
        assertEq(rewards.claimable(1, address(token)), 800); assertEq(token.balanceOf(address(owner)), 0);
        assertEq(royalties.pending(address(token)), 900); owner.claim(_one(1, address(token), false));
        assertEq(token.balanceOf(address(owner)), 800);
    }

    function testCallbackTransferBeforeLaterEntryRollsBackClaimsAndNFTTransfer() public {
        ClaimRouterOwner owner = new ClaimRouterOwner(router, nft);
        vm.startPrank(ALICE); nft.transferFrom(ALICE, address(owner), 1); nft.transferFrom(ALICE, address(owner), 2);
        vm.stopPrank(); owner.configure(1, false, 2, BOB, 0); _fund();
        ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](2);
        list[0] = ZZZClaimRouter.Claim(1, address(0), true); list[1] = ZZZClaimRouter.Claim(2, address(token), false);
        vm.expectRevert(ZZZClaimRouter.Unauthorized.selector); owner.claim(list);
        assertEq(nft.ownerOf(2), address(owner)); assertEq(address(owner).balance, 0);
        assertEq(royalties.pending(address(0)), 3 ether); assertEq(rewards.claimable(2, address(token)), 1400);
    }

    function testCallbackNativeRefundStaysPendingAndBackingRemainsIntact() public {
        ClaimRouterOwner owner = new ClaimRouterOwner(router, nft);
        vm.prank(ALICE); nft.transferFrom(ALICE, address(owner), 1); owner.configure(1, false, 0, address(0), 3);
        _fund(); owner.claim(_one(1, address(0), true));
        assertEq(address(owner).balance, 1 ether - 3); assertEq(royalties.pending(address(0)), 3);
        assertEq(royalties.liabilities(address(0)), 2 ether); assertEq(address(router).balance, 0);
    }

    function testZeroBalancesAndDormantNFTCannotClaimAnotherNFTRewards() public {
        _fund(); vm.prank(ALICE); uint256[] memory zero = router.claimBatch(_both(4));
        assertEq(zero[0], 0); assertEq(zero[1], 0); assertEq(zero[2], 0);
        vm.startPrank(ALICE); router.claimBatch(_both(1)); zero = router.claimBatch(_both(1)); vm.stopPrank();
        assertEq(zero[0], 0); assertEq(zero[1], 0); assertEq(zero[2], 0);
        assertEq(rewards.claimable(2, address(token)), 1400); assertEq(royalties.claimable(2, address(0)), 1 ether);
    }

    function testDirectOwnerClaimsRemainAvailable() public {
        _fund(); vm.startPrank(ALICE); assertEq(rewards.claim(1, address(token)), 800);
        assertEq(royalties.claim(1, address(0)), 1 ether); vm.stopPrank();
        vm.prank(BOB); vm.expectRevert(); rewards.claim(1, address(token));
        vm.prank(BOB); vm.expectRevert(); royalties.claim(1, address(token));
    }

    function testRouterRejectsETHAndArbitraryCalls() public {
        (bool ok,) = address(router).call{value: 1}(""); assertFalse(ok);
        (ok,) = address(router).call(hex"deadbeef"); assertFalse(ok);
    }

    function testRouterCannotBeRedeployedByThirdPartyForCanonicalNFT() public {
        vm.expectRevert(ZZZClaimRouter.InvalidConfiguration.selector);
        new ZZZClaimRouter(address(access), address(nft), address(royalties));
    }

    function testTaxedRoyaltyAssetAtomicallyRevertsOtherAssetPayouts() public {
        TaxToken taxed = new TaxToken(); nft.addRoyaltyAsset(address(taxed));
        taxed.mint(address(royalties), 900); _credit(token, 1500, 1500);
        ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](2);
        list[0] = ZZZClaimRouter.Claim(1, address(token), false);
        list[1] = ZZZClaimRouter.Claim(1, address(taxed), true);
        vm.prank(ALICE); vm.expectRevert(); router.claimBatch(list);
        assertEq(token.balanceOf(ALICE), 0); assertEq(taxed.balanceOf(ALICE), 0);
        assertEq(rewards.claimable(1, address(token)), 800); assertEq(taxed.balanceOf(address(royalties)), 900);
        assertEq(royalties.pending(address(taxed)), 900);
    }

    function testMaximum32ColdOperationsAcross16NFTsUnder12MGas() public {
        uint256[] memory ids = new uint256[](16); ids[0] = 1; ids[1] = 2;
        for (uint256 i = 2; i < 16; ++i) { ids[i] = i + 10; _mint(ALICE, ids[i], 100); }
        _credit(token, 1900, 0);
        (bool ok,) = address(royalties).call{value: 17 ether}(""); require(ok);
        ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](32);
        for (uint256 i; i < ids.length; ++i) {
            list[i * 2] = ZZZClaimRouter.Claim(ids[i], address(token), false);
            list[i * 2 + 1] = ZZZClaimRouter.Claim(ids[i], address(0), true);
        }
        // Warmth from setup must not make this regression artificially cheap.
        vm.cool(address(nft)); vm.cool(address(router)); vm.cool(address(royalties)); vm.cool(address(rewards));
        vm.cool(address(vault)); vm.cool(address(membership)); vm.cool(address(access)); vm.cool(address(token));
        vm.prank(ALICE); uint256 beforeGas = gasleft(); uint256[] memory amounts = router.claimBatch(list);
        uint256 used = beforeGas - gasleft(); emit log_named_uint("32 mixed claim operations gas", used);
        assertLt(used, 12_000_000); assertEq(amounts.length, 32);
        assertEq(token.balanceOf(ALICE), 1800); assertEq(ALICE.balance, 16 ether);
        assertEq(address(router).balance, 0); assertEq(token.balanceOf(address(router)), 0);
    }

    function testFuzzBatchAndDirectClaimsConserveFundedBalances(uint96 personal, uint96 shared, uint96 royalty) public {
        personal = uint96(bound(personal, 1, 1e24)); shared = uint96(bound(shared, 1, 1e24));
        royalty = uint96(bound(royalty, 1, 1e24)); _credit(token, personal, shared);
        token.mint(address(royalties), royalty);
        uint256 lpExpected = rewards.claimable(1, address(token)); uint256 royaltyExpected = royalties.claimable(1, address(token));
        ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](2);
        list[0] = ZZZClaimRouter.Claim(1, address(token), false); list[1] = ZZZClaimRouter.Claim(1, address(token), true);
        vm.prank(ALICE); uint256[] memory amounts = router.claimBatch(list);
        assertEq(amounts[0], lpExpected); assertEq(amounts[1], royaltyExpected);
        assertEq(token.balanceOf(ALICE), lpExpected + royaltyExpected);
        assertGe(token.balanceOf(address(rewards)), rewards.liabilities(address(token)));
        assertGe(token.balanceOf(address(royalties)), royalties.accounted(address(token)));
        assertEq(token.balanceOf(address(router)), 0);
    }
}
