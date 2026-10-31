// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZVault} from "../src/ZZZVault.sol";

contract MintTermsChangingRecipient {
    ZZZProtocolPolicy public policy;
    function configure(ZZZProtocolPolicy next) external { policy=next; }
    receive() external payable { policy.setMintPrice(uint128(0.09 ether),keccak256("TEST_ONLY callback terms mutation")); }
}

/// @notice Real policy/Vault/reward ledgers with the existing explicitly
/// synthetic two-ERC20 transport/LP fixture; not live venue/provider qualification.
contract AdaptableTermsTest is PooledVaultFixture {
    bytes32 private constant REVIEW=keccak256("TEST_ONLY future terms review");
    ZZZProtocolPolicy private terms;
    function setUp() public override { super.setUp(); terms=ZZZProtocolPolicy(ac.protocolPolicy()); }
    function _terms() private view returns(ZZZProtocolPolicy) { return terms; }
    function testChangedMintPriceRequiresFreshReviewAndOnlyChangesFuturePayment() public {
        uint256 first=_mint(alice); uint256 received=treasury.balance;
        bytes32 previous=vault.mintPolicyFingerprint(); _terms().setMintPrice(uint128(0.08 ether),REVIEW);
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.08 ether}(previous);
        assertEq(vault.sequence(),1);assertEq(treasury.balance,received);assertEq(nft.ownerOf(first),alice);
        bytes32 reviewedPolicy1 = vault.mintPolicyFingerprint(); vm.prank(alice);uint256 id=vault.mintDormant{value:0.08 ether}(reviewedPolicy1);
        assertEq(nft.ownerOf(id),alice);assertEq(treasury.balance,received+0.08 ether);
        assertEq(vault.sharesOf(first),0);assertEq(nft.royaltyRewards().weightOf(first),0);
    }
    function testFutureRecipientAcceptanceInvalidatesReviewWithoutMovingPastProceeds() public {
        _mint(alice);uint256 received=treasury.balance;uint256 beforeBob=bob.balance;
        bytes32 previous=vault.mintPolicyFingerprint();_terms().proposeMintRecipient(bob,REVIEW);
        assertEq(vault.mintProceedsRecipient(),treasury);
        vm.prank(bob);_terms().acceptMintRecipient();
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}(previous);
        bytes32 reviewedPolicy2 = vault.mintPolicyFingerprint(); vm.prank(alice);vault.mintDormant{value:0.05 ether}(reviewedPolicy2);
        assertEq(treasury.balance,received);assertEq(bob.balance,beforeBob+0.05 ether);
    }
    function testRecipientCallbackCannotChangeAndCommitReviewedMintTerms() public {
        MintTermsChangingRecipient recipient=new MintTermsChangingRecipient();recipient.configure(_terms());
        _terms().proposeMintRecipient(address(recipient),REVIEW);
        vm.prank(address(recipient));_terms().acceptMintRecipient();
        // Deliberately model a recipient that is ALSO an authorized governor.
        vm.mockCall(address(ac),abi.encodeWithSignature("canConfigure(address)",address(recipient)),abi.encode(true));
        bytes32 expected=vault.mintPolicyFingerprint();uint256 beforeBalance=alice.balance;
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}(expected);
        assertEq(vault.sequence(),0);assertEq(nft.mintedCount(),0);assertEq(alice.balance,beforeBalance);
        assertEq(address(recipient).balance,0);assertEq(vault.mintPolicyFingerprint(),expected);
        assertEq(vault.mintPrice(),0.05 ether);
    }
    function testFutureVrfRequestPolicyInvalidatesMintReviewBeforeRequest() public {
        bytes32 previous=vault.mintPolicyFingerprint();
        _terms().setRandomnessRequestSettings(4,600000,REVIEW);
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}(previous);
        assertEq(nft.mintedCount(),0);assertEq(vault.sequence(),0);
        bytes32 reviewedPolicy3 = vault.mintPolicyFingerprint(); vm.prank(alice);vault.mintDormant{value:0.05 ether}(reviewedPolicy3);
        assertEq(nft.mintedCount(),1);
    }
    function testActivationAndGrowthPolicyAreFutureOnlyAndPoolMinimumStillApplies() public {
        uint256 active=_mint(alice);_activate(alice,active,100,0);uint256 shares=vault.sharesOf(active);
        uint256 dormant=_mint(bob);_terms().setEntryPolicy(150e18,10e18,500,REVIEW);
        vm.prank(bob);vm.expectRevert();vault.activate(dormant,poolId,100,0,1,block.timestamp+100);
        vm.prank(alice);vm.expectRevert();vault.increase(active,5,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(active),shares);assertEq(vault.sharesOf(dormant),0);
        assertTrue(membership.eligible(active));assertEq(nft.royaltyRewards().weightOf(active),1);
        vm.prank(alice);vault.increase(active,10,0,1,block.timestamp+100);
        _activate(bob,dormant,150,0);
        assertGt(vault.sharesOf(active),shares);assertEq(vault.contributionUSD(dormant),150e18);
    }
    function testCosmeticAndGasPoliciesDoNotInvalidateReviewedMint() public {
        bytes32 expected=vault.mintPolicyFingerprint();_terms().setEvolutionThresholds(2000e18,20000e18,REVIEW);
        _terms().setGasPolicy(200000,600000,300000,REVIEW);
        assertEq(vault.mintPolicyFingerprint(),expected);
        vm.prank(alice);vault.mintDormant{value:0.05 ether}(expected);assertEq(nft.mintedCount(),1);
    }
}
