// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {MockToken, TaxToken} from "./mocks/Mocks.sol";
import {ExactToken} from "../src/libraries/ExactToken.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";

/// @dev Isolated royalty-ledger fixture. This intentionally does not substitute
/// for the real NFT's authenticated admission, activation, or mint integration.
contract RoyaltyNFTFixture is ERC721 {
    ZZZRoyaltyRewards public immutable royalties;
    bool public paused;
    constructor() ERC721("Royalty fixture", "RF") { royalties = new ZZZRoyaltyRewards(address(this)); }
    function mint(address owner, uint256 id) external { _mint(owner, id); }
    function activate(uint256 id, uint256 weight) external { royalties.activate(id, weight); }
    function addAsset(address token) external { royalties.addAsset(token); }
    function setPaused(bool value) external { paused = value; }
}

contract RoyaltyRebaseToken is MockToken {
    constructor() MockToken(18) {}
    function slash(address account, uint256 amount) external { _burn(account, amount); }
}

contract RoyaltyLowGasPayer {
    function pay(address payable to) external payable { to.transfer(msg.value); }
}

contract RoyaltyNativeOwner {
    ZZZRoyaltyRewards public immutable royalties;
    uint256 public immutable id;
    bool public attempted;
    bool public reentered;
    bool public rejectPayment;
    bool public refundOne;
    constructor(ZZZRoyaltyRewards receiver, uint256 nftId) { royalties = receiver; id = nftId; }
    function configure(bool reject, bool refund) external { rejectPayment = reject; refundOne = refund; }
    function claim() external { royalties.claim(id, address(0)); }
    receive() external payable {
        require(!rejectPayment, "payment refused");
        attempted = true;
        (reentered,) = address(royalties).call(abi.encodeCall(ZZZRoyaltyRewards.claim, (id, address(0))));
        if (refundOne && msg.value != 0) {
            (bool success,) = address(royalties).call{value: 1}("");
            require(success);
        }
    }
}

contract NFTRoyaltiesTest is Test {
    RoyaltyNFTFixture private nft;
    ZZZRoyaltyRewards private royalties;
    MockToken private token;
    address private alice = address(0xA11CE);
    address private bob = address(0xB0B);
    address private carol = address(0xCA701);
    address private constant ETH = address(0);

    function setUp() public {
        nft = new RoyaltyNFTFixture();
        royalties = nft.royalties();
        token = new MockToken(18);
        nft.addAsset(address(token));
        nft.mint(alice, 1);
        nft.mint(bob, 2);
        nft.mint(carol, 3);
        vm.deal(address(this), 100 ether);
    }

    function _pay(uint256 amount) private {
        (bool success,) = address(royalties).call{value: amount}("");
        assertTrue(success);
    }

    function _claim(address owner, uint256 id, address asset) private returns (uint256) {
        vm.prank(owner);
        return royalties.claim(id, asset);
    }

    function testImmutableNFTOnlyAndOneTimeBoundedWeights() public {
        assertEq(royalties.nft(), address(nft));
        vm.expectRevert(ZZZRoyaltyRewards.Unauthorized.selector);
        royalties.activate(1, 3);
        MockToken another = new MockToken(18);
        vm.expectRevert(ZZZRoyaltyRewards.Unauthorized.selector);
        royalties.addAsset(address(another));
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        nft.activate(1, 0);
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        nft.activate(1, 4);
        nft.activate(1, 1);
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        nft.activate(1, 3);
        assertEq(royalties.weightOf(1), 1);
        assertEq(royalties.totalWeight(), 1);
    }

    function testDormantNFTCannotReceiveRoyalties() public {
        nft.activate(1, 1);
        _pay(6 ether);
        assertEq(royalties.claimable(2, ETH), 0);
        assertEq(_claim(bob, 2, ETH), 0);
        assertEq(_claim(alice, 1, ETH), 6 ether);
    }

    function testInvalidControllerAndMissingNFTCannotCreateWeights() public {
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        new ZZZRoyaltyRewards(address(0));
        vm.expectRevert();
        nft.activate(999, 1);
        assertEq(royalties.totalWeight(), 0);
        assertEq(royalties.weightOf(999), 0);
    }

    function testNativeRoyaltyWeightsOneTwoThreeAllocateAllActualReceipts() public {
        nft.activate(1, 1);
        nft.activate(2, 2);
        nft.activate(3, 3);
        _pay(6 ether);
        assertEq(royalties.claimable(1, ETH), 1 ether);
        assertEq(royalties.claimable(2, ETH), 2 ether);
        assertEq(royalties.claimable(3, ETH), 3 ether);
        assertEq(_claim(alice, 1, ETH), 1 ether);
        assertEq(_claim(bob, 2, ETH), 2 ether);
        assertEq(_claim(carol, 3, ETH), 3 ether);
        assertEq(address(royalties).balance, 0);
        assertEq(royalties.liabilities(ETH), 0);
    }

    function testERC20RoyaltyWeightsAndExactFunding() public {
        nft.activate(1, 1);
        nft.activate(2, 2);
        nft.activate(3, 3);
        token.mint(address(this), 600);
        token.approve(address(royalties), 600);
        royalties.fund(address(token), 600);
        assertEq(_claim(alice, 1, address(token)), 100);
        assertEq(_claim(bob, 2, address(token)), 200);
        assertEq(_claim(carol, 3, address(token)), 300);
        assertEq(token.balanceOf(address(royalties)), 0);
    }

    function testNativePlainTransferWorksWith2300Gas() public {
        nft.activate(1, 1);
        RoyaltyLowGasPayer payer = new RoyaltyLowGasPayer();
        payer.pay{value: 1 ether}(payable(address(royalties)));
        assertEq(royalties.pending(ETH), 1 ether);
        assertEq(_claim(alice, 1, ETH), 1 ether);
    }

    function testNoEligibleReceiptQuarantinedWithoutExplicitSync() public {
        _pay(2 ether);
        token.mint(address(royalties), 400);
        nft.activate(1, 1);
        assertEq(royalties.orphaned(ETH), 2 ether);
        assertEq(royalties.orphaned(address(token)), 400);
        assertEq(royalties.claimable(1, ETH), 0);
        assertEq(royalties.claimable(1, address(token)), 0);
        _pay(1 ether);
        token.mint(address(royalties), 100);
        assertEq(_claim(alice, 1, ETH), 1 ether);
        assertEq(_claim(alice, 1, address(token)), 100);
        assertEq(address(royalties).balance, 2 ether);
        assertEq(token.balanceOf(address(royalties)), 400);
    }

    function testExplicitEmptyMembershipSyncAlsoQuarantines() public {
        _pay(5);
        royalties.sync(ETH);
        nft.activate(1, 3);
        royalties.syncAll();
        assertEq(royalties.orphaned(ETH), 5);
        assertEq(_claim(alice, 1, ETH), 0);
    }

    function testPendingBothAssetsBelongToExistingMembersBeforeActivation() public {
        nft.activate(1, 1);
        _pay(3 ether);
        token.mint(address(royalties), 300);
        nft.activate(2, 2);
        assertEq(royalties.claimable(1, ETH), 3 ether);
        assertEq(royalties.claimable(2, ETH), 0);
        assertEq(royalties.claimable(1, address(token)), 300);
        assertEq(royalties.claimable(2, address(token)), 0);
        _pay(3 ether);
        token.mint(address(royalties), 300);
        assertEq(_claim(alice, 1, ETH), 4 ether);
        assertEq(_claim(bob, 2, ETH), 2 ether);
        assertEq(_claim(alice, 1, address(token)), 400);
        assertEq(_claim(bob, 2, address(token)), 200);
    }

    function testNFTTransferCarriesAllUnclaimedRightsAndFractions() public {
        nft.activate(1, 1);
        nft.activate(2, 1);
        _pay(1);
        assertEq(_claim(alice, 1, ETH), 0);
        assertEq(royalties.fraction(1, ETH), royalties.SCALE() / 2);
        vm.prank(alice);
        nft.transferFrom(alice, carol, 1);
        _pay(3);
        vm.prank(alice);
        vm.expectRevert(ZZZRoyaltyRewards.Unauthorized.selector);
        royalties.claim(1, ETH);
        assertEq(_claim(carol, 1, ETH), 2);
        assertEq(_claim(bob, 2, ETH), 2);
        assertEq(royalties.weightOf(1), 1);
    }

    function testOperatorsCannotClaimAndClaimsRemainAvailableWhilePaused() public {
        nft.activate(1, 1);
        _pay(1 ether);
        vm.prank(alice);
        nft.approve(bob, 1);
        vm.prank(bob);
        vm.expectRevert(ZZZRoyaltyRewards.Unauthorized.selector);
        royalties.claim(1, ETH);
        nft.setPaused(true);
        assertEq(_claim(alice, 1, ETH), 1 ether);
    }

    function testNativeClaimRejectsReentryWithoutLosingEntitlement() public {
        RoyaltyNativeOwner owner = new RoyaltyNativeOwner(royalties, 4);
        nft.mint(address(owner), 4);
        nft.activate(4, 3);
        _pay(2 ether);
        owner.claim();
        assertTrue(owner.attempted());
        assertFalse(owner.reentered());
        assertEq(address(owner).balance, 2 ether - 1);
        assertEq(royalties.liabilities(ETH), 1);
        assertEq(royalties.accounted(ETH), 1);
        assertEq(address(royalties).balance, 1);
        assertEq(royalties.fraction(4, ETH), royalties.SCALE() - 2);
        owner.claim();
        assertEq(address(owner).balance, 2 ether - 1);
        assertEq(royalties.liabilities(ETH), 1);
        assertEq(address(royalties).balance, 1);
    }

    function testRevertedNativeClaimRollsBackAccounting() public {
        RoyaltyNativeOwner owner = new RoyaltyNativeOwner(royalties, 4);
        nft.mint(address(owner), 4);
        nft.activate(4, 1);
        _pay(1 ether);
        owner.configure(true, false);
        vm.expectRevert(ZZZRoyaltyRewards.NativeTransferFailed.selector);
        owner.claim();
        assertEq(royalties.claimable(4, ETH), 1 ether);
        assertEq(address(royalties).balance, 1 ether);
        owner.configure(false, false);
        owner.claim();
        assertEq(address(owner).balance, 1 ether);
    }

    function testNativeCallbackDonationRemainsPendingAndBacked() public {
        RoyaltyNativeOwner owner = new RoyaltyNativeOwner(royalties, 4);
        nft.mint(address(owner), 4);
        nft.activate(4, 1);
        _pay(10);
        owner.configure(false, true);
        owner.claim();
        assertEq(royalties.accounted(ETH), 0);
        assertEq(royalties.pending(ETH), 1);
        assertEq(royalties.claimable(4, ETH), 1);
        owner.configure(false, false);
        owner.claim();
        assertEq(address(owner).balance, 10);
    }

    function testFractionsSurviveFrequentNativeAndTokenClaims() public {
        nft.activate(1, 1);
        nft.activate(2, 1);
        _pay(1);
        token.mint(address(royalties), 1);
        assertEq(_claim(alice, 1, ETH), 0);
        assertEq(_claim(bob, 2, ETH), 0);
        assertEq(_claim(alice, 1, address(token)), 0);
        assertEq(_claim(bob, 2, address(token)), 0);
        _pay(1);
        token.mint(address(royalties), 1);
        assertEq(_claim(alice, 1, ETH), 1);
        assertEq(_claim(bob, 2, ETH), 1);
        assertEq(_claim(alice, 1, address(token)), 1);
        assertEq(_claim(bob, 2, address(token)), 1);
        assertEq(royalties.liabilities(ETH), 0);
        assertEq(royalties.liabilities(address(token)), 0);
    }

    function testGlobalRoundingDustDoesNotBecomeNewEntrantWindfall() public {
        nft.activate(1, 1);
        nft.activate(2, 2);
        token.mint(address(royalties), 1);
        royalties.sync(address(token));
        nft.activate(3, 3);
        assertEq(royalties.claimable(3, address(token)), 0);
        token.mint(address(royalties), 6);
        assertEq(_claim(alice, 1, address(token)), 1);
        assertEq(_claim(bob, 2, address(token)), 2);
        assertEq(_claim(carol, 3, address(token)), 3);
        assertEq(token.balanceOf(address(royalties)), 1);
        assertEq(royalties.liabilities(address(token)), 1);
        assertEq(royalties.claimable(3, address(token)), 0);
    }

    function testUnsupportedPrefundedTokenQuarantinedOnAdmission() public {
        MockToken later = new MockToken(18);
        later.mint(address(royalties), 100);
        nft.activate(1, 1);
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        royalties.sync(address(later));
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        royalties.claimable(1, address(later));
        nft.addAsset(address(later));
        assertEq(royalties.orphaned(address(later)), 100);
        later.mint(address(royalties), 50);
        assertEq(_claim(alice, 1, address(later)), 50);
        assertEq(later.balanceOf(address(royalties)), 100);
    }

    function testPredictedConstructorNativePrefundNeverBecomesRewards() public {
        address predicted = vm.computeCreateAddress(address(this), vm.getNonce(address(this)));
        vm.deal(predicted, 4 ether);
        ZZZRoyaltyRewards receiver = new ZZZRoyaltyRewards(address(nft));
        assertEq(address(receiver), predicted);
        assertEq(receiver.orphaned(ETH), 4 ether);
        vm.prank(address(nft));
        receiver.activate(1, 1);
        assertEq(receiver.claimable(1, ETH), 0);
        vm.prank(alice);
        assertEq(receiver.claim(1, ETH), 0);
    }

    function testAssetAdmissionBoundAndDuplicates() public {
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        nft.addAsset(address(token));
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        nft.addAsset(ETH);
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        nft.addAsset(alice);
        for (uint256 i = 1; i < royalties.MAX_ERC20_ASSETS(); ++i) nft.addAsset(address(new MockToken(18)));
        assertEq(royalties.assetCount(), royalties.MAX_ASSETS());
        MockToken last = new MockToken(18);
        vm.expectRevert(ZZZRoyaltyRewards.InvalidConfiguration.selector);
        nft.addAsset(address(last));
    }

    function testTaxedTokenFundingAndClaimsRevertAtomically() public {
        TaxToken taxed = new TaxToken();
        nft.addAsset(address(taxed));
        nft.activate(1, 1);
        taxed.mint(address(this), 100);
        taxed.approve(address(royalties), 100);
        vm.expectRevert(abi.encodeWithSelector(ExactToken.UnsupportedToken.selector, address(taxed)));
        royalties.fund(address(taxed), 100);
        assertEq(taxed.balanceOf(address(this)), 100);
        taxed.mint(address(royalties), 100);
        vm.prank(alice);
        vm.expectRevert(abi.encodeWithSelector(ExactToken.UnsupportedToken.selector, address(taxed)));
        royalties.claim(1, address(taxed));
        assertEq(taxed.balanceOf(address(royalties)), 100);
        assertEq(royalties.claimable(1, address(taxed)), 100);
    }

    function testNegativeRebaseFailsClosedAndCannotSpendOtherAssetBacking() public {
        RoyaltyRebaseToken rebasing = new RoyaltyRebaseToken();
        nft.addAsset(address(rebasing));
        nft.activate(1, 1);
        rebasing.mint(address(royalties), 100);
        royalties.sync(address(rebasing));
        rebasing.slash(address(royalties), 1);
        vm.expectRevert(ZZZRoyaltyRewards.InvalidState.selector);
        royalties.sync(address(rebasing));
        vm.prank(alice);
        vm.expectRevert(ZZZRoyaltyRewards.InvalidState.selector);
        royalties.claim(1, address(rebasing));
        _pay(5);
        assertEq(_claim(alice, 1, ETH), 5);
        assertEq(royalties.liabilities(address(rebasing)), 100);
    }

    function testFuzzClaimsNeverExceedActualFunding(uint128 first, uint128 second, uint128 third) public {
        uint256 a = bound(uint256(first), 1, 1e24);
        uint256 b = bound(uint256(second), 1, 1e24);
        uint256 c = bound(uint256(third), 1, 1e24);
        nft.activate(1, 1);
        token.mint(address(royalties), a);
        nft.activate(2, 2);
        token.mint(address(royalties), b);
        nft.activate(3, 3);
        token.mint(address(royalties), c);
        uint256 sum = _claim(alice, 1, address(token)) + _claim(bob, 2, address(token))
            + _claim(carol, 3, address(token));
        assertLe(sum, a + b + c);
        assertEq(token.balanceOf(address(royalties)), a + b + c - sum);
        assertEq(royalties.liabilities(address(token)), a + b + c - sum);
        assertEq(royalties.accounted(address(token)), token.balanceOf(address(royalties)));
        assertEq(_claim(alice, 1, address(token)), 0);
        assertEq(_claim(bob, 2, address(token)), 0);
        assertEq(_claim(carol, 3, address(token)), 0);
    }
}
