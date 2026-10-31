// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {IZZZProtocolPolicy as P} from "../src/interfaces/IZZZProtocolPolicy.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess} from "./mocks/Mocks.sol";

/// @dev TEST ONLY lifecycle/metadata callbacks; no provider acceptance asserted.
contract PolicyNFTContext {
    uint256 public mintedCount;uint256 public nextToFinalize=1;
    address public constant royaltyRewards=address(0xBEEF);
    uint256 public refreshes;
    address public policy;
    function bind(address p)external{policy=p;}
    function history(uint256 count,uint256 next)external{mintedCount=count;nextToFinalize=next;}
    function policyMetadataChanged()external{require(msg.sender==policy);++refreshes;}
}
contract PolicyProviderIdentity {}
contract ProtocolPolicyTest is Test {
    MockAccess private access;ZZZProtocolPolicy private policy;PolicyNFTContext private nft;
    PolicyProviderIdentity private provider;
    address private constant RECIPIENT=address(0xCAFE);
    bytes32 private constant REVIEW=keccak256("TEST ONLY POLICY REVIEW");
    function setUp()public{
        access=new MockAccess();policy=new ZZZProtocolPolicy(address(access),RECIPIENT);
        access.setProtocolPolicy(address(policy));nft=new PolicyNFTContext();nft.bind(address(policy));
        access.bind(Ids.NFT,address(nft));provider=new PolicyProviderIdentity();
    }
    function _vrf()private{
        policy.configureRandomness(address(provider),address(provider).codehash,bytes32(uint256(1)),1,3,500000,false,REVIEW);
    }
    function testDefaultsAreCompleteWithoutGuessedUnconfiguredValues()public view{
        P.EntryPolicy memory e=policy.entryPolicy();assertEq(e.minActivationUSD,100e18);assertEq(e.minGrowthUSD,5e18);assertEq(e.maxIdleBps,500);
        assertEq(policy.maintenancePolicy().maxIdleBps,500);
        P.GasPolicy memory g=policy.gasPolicy();assertEq(g.payoutGas,180000);assertEq(g.sourceCallGas,500000);assertEq(g.royaltySyncGas,250000);
        assertEq(policy.payoutGas(),g.payoutGas);assertEq(policy.sourceCallGas(),g.sourceCallGas);assertEq(policy.royaltySyncGas(),g.royaltySyncGas);
        assertEq(policy.salePolicy().recipient,RECIPIENT);assertEq(policy.salePolicy().mintPrice,0.05 ether);
        assertEq(policy.metadataPolicy().enhancedUSD,1000e18);assertEq(policy.metadataPolicy().singularityUSD,10000e18);
        assertFalse(policy.vrfPolicy().configured);
    }
    function testCosmeticGasAndSaleChangesDoNotInvalidateFinancialDomains()public{
        bytes32 entry=policy.entryFingerprint();bytes32 maintenance=policy.maintenanceFingerprint();bytes32 mint=policy.mintFingerprint();
        bytes32 full=policy.configurationHash();
        policy.setEvolutionThresholds(2000e18,20000e18,REVIEW);assertEq(nft.refreshes(),1);
        assertEq(policy.entryFingerprint(),entry);assertEq(policy.maintenanceFingerprint(),maintenance);assertEq(policy.mintFingerprint(),mint);
        policy.setGasPolicy(200000,600000,300000,REVIEW);
        assertEq(policy.entryFingerprint(),entry);assertEq(policy.maintenanceFingerprint(),maintenance);assertEq(policy.mintFingerprint(),mint);
        policy.setMintPrice(uint128(0.04 ether),REVIEW);assertTrue(policy.mintFingerprint()!=mint);
        assertEq(policy.entryFingerprint(),entry);assertEq(policy.maintenanceFingerprint(),maintenance);assertTrue(policy.configurationHash()!=full);
    }
    function testFinancialDomainsAreIndependentAndRestoreCannotReviveOldReview()public{
        bytes32 entry=policy.entryFingerprint();bytes32 maintenance=policy.maintenanceFingerprint();
        policy.setMaintenancePolicy(4000,REVIEW);assertEq(policy.entryFingerprint(),entry);assertTrue(policy.maintenanceFingerprint()!=maintenance);
        maintenance=policy.maintenanceFingerprint();policy.setEntryPolicy(150e18,10e18,1000,REVIEW);
        assertEq(policy.maintenanceFingerprint(),maintenance);assertTrue(policy.entryFingerprint()!=entry);
        policy.setEntryPolicy(100e18,5e18,500,REVIEW);assertTrue(policy.entryFingerprint()!=entry);
    }
    function testEntryAndIdleBoundsCannotCreateFreeOrUnboundedContributions()public{
        policy.setEntryPolicy(1e18,1e18,4000,REVIEW);assertEq(policy.entryPolicy().maxIdleBps,4000);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setEntryPolicy(1e18-1,1e18-1,500,REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setEntryPolicy(100e18,101e18,500,REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setEntryPolicy(100e18,5e18,4001,REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setMaintenancePolicy(4001,REVIEW);
        policy.setMaintenancePolicy(0,REVIEW);assertEq(policy.maintenancePolicy().maxIdleBps,0);
    }
    function testGasBudgetsStayBoundedAndUnauthorizedChangesRevert()public{
        policy.setGasPolicy(100000,1000000,1000000,REVIEW);
        assertEq(policy.payoutGas(),100000);assertEq(policy.sourceCallGas(),1000000);assertEq(policy.royaltySyncGas(),1000000);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setGasPolicy(99999,500000,250000,REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setGasPolicy(180000,1000001,250000,REVIEW);
        vm.prank(address(0xBAD));vm.expectRevert(ZZZModule.Unauthorized.selector);policy.setMaintenancePolicy(4000,REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setMintPrice(0,REVIEW);
    }
    function testRecipientRotationRequiresNewRecipientAcceptanceAndPreservesOtherTerms()public{
        address next=address(0xA11CE);bytes32 entry=policy.entryFingerprint();
        policy.proposeMintRecipient(next,REVIEW);assertEq(policy.salePolicy().recipient,RECIPIENT);
        vm.prank(address(0xBAD));vm.expectRevert(ZZZModule.Unauthorized.selector);policy.acceptMintRecipient();
        vm.prank(next);policy.acceptMintRecipient();assertEq(policy.salePolicy().recipient,next);
        assertEq(policy.salePolicy().pendingRecipient,address(0));assertEq(policy.entryFingerprint(),entry);
        policy.proposeMintRecipient(RECIPIENT,REVIEW);policy.proposeMintRecipient(address(0),REVIEW);
        assertEq(policy.salePolicy().pendingRecipient,address(0));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.proposeMintRecipient(address(nft),REVIEW);
        address royalty=nft.royaltyRewards();
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.proposeMintRecipient(royalty,REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.proposeMintRecipient(address(policy),REVIEW);
    }
    function testFrozenUnsealedImporterCannotMutatePolicyOrAcceptRecipient()public{
        policy.proposeMintRecipient(address(0xA11CE),REVIEW);access.setCanonicalState(2);
        vm.expectRevert(ZZZModule.CanonicalLocked.selector);policy.setMaintenancePolicy(1000,REVIEW);
        vm.expectRevert(ZZZModule.CanonicalLocked.selector);policy.setEvolutionThresholds(2000e18,20000e18,REVIEW);
        vm.expectRevert(ZZZModule.CanonicalLocked.selector);policy.configureRandomness(address(provider),address(provider).codehash,bytes32(uint256(1)),1,3,500000,false,REVIEW);
        vm.prank(address(0xA11CE));vm.expectRevert(ZZZModule.CanonicalLocked.selector);policy.acceptMintRecipient();
        assertEq(policy.salePolicy().recipient,RECIPIENT);assertFalse(policy.vrfPolicy().configured);
    }
    function testFutureRequestSettingsChangeMintReviewButDoNotRetargetPendingDraws()public{
        _vrf();bytes32 beforeMint=policy.mintFingerprint();bytes32 beforeSale=policy.saleFingerprint();
        nft.history(1,1);policy.setRandomnessRequestSettings(4,600000,REVIEW);
        assertEq(policy.vrfPolicy().generation,0);assertEq(policy.vrfPolicy().coordinator,address(provider));
        assertTrue(policy.mintFingerprint()!=beforeMint);assertEq(policy.saleFingerprint(),beforeSale);
        access.seal();vm.expectRevert(ZZZModule.InvalidState.selector);
        policy.rotateRandomness(address(provider),address(provider).codehash,bytes32(uint256(2)),2,4,600000,true,REVIEW);
        nft.history(1,2);policy.rotateRandomness(address(provider),address(provider).codehash,bytes32(uint256(2)),2,4,600000,true,REVIEW);
        assertEq(policy.vrfPolicy().generation,1);assertEq(policy.vrfPolicy().subscriptionId,2);
    }
}
