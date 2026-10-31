// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";
import {ZZZFeesCanonical} from "../src/ZZZFeesCanonical.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {BoundDummy} from "./mocks/Mocks.sol";
contract AccessControllerTest is Test {
    ZZZAccessController ac;address guardian=address(0x123);address keeper=address(0x456);
    function setUp() public {
        vm.warp(1000000);
        ac=new ZZZAccessController(address(0xA0A0), keeper, guardian); ProtocolPolicyFixture.bind(address(ac));
    }
    function fill() private {
        fillCore();
        CanonicalFixture.bind(address(ac));
    }
    function fillCore() private {
        bytes32[12] memory ids=[Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,Ids.STRATEGY,
            Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.ORACLE,Ids.POOLS];
        for(uint256 i;i<ids.length;i++)ac.bind(ids[i],address(new BoundDummy(address(ac))));
    }
    function testIncompleteDeploymentCannotSeal() public {vm.expectRevert();ac.seal();}
    function testAllCoreModulesWithoutCanonicalCompanionsCannotSeal() public {
        fillCore(); vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.seal();
        assertFalse(ac.isSealed()); assertEq(ac.bootstrap(), address(this));
    }
    function testNFTCompanionMustBelongToBoundCollection() public {
        fillCore(); address other = address(new BoundDummy(address(ac)));
        ac.bind(Ids.NFT_CANONICAL, address(new ZZZNFTCanonical(address(ac), other)));
        CanonicalFixture.bind(address(ac));
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.seal();
        assertFalse(ac.isSealed());
    }
    function testFeeCompanionMustBelongToBoundFeeController() public {
        fillCore(); address other = address(new BoundDummy(address(ac)));
        ac.bind(Ids.FEES_CANONICAL, address(new ZZZFeesCanonical(address(ac), other)));
        CanonicalFixture.bind(address(ac));
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.seal();
        assertFalse(ac.isSealed());
    }
    function testCanonicalRandomnessMustBeConfiguredBeforeSeal() public {
        fill();BoundDummy nft=BoundDummy(ac.module(Ids.NFT));nft.setRandomnessConfigured(false);
        vm.expectRevert();ac.seal();assertFalse(ac.isSealed());assertEq(ac.bootstrap(),address(this));
        nft.setRandomnessConfigured(true);ac.seal();assertTrue(ac.isSealed());
    }
    function testCanonicalZZZIdentityMustBeBoundBeforeSeal() public {
        fill(); BoundDummy identity=BoundDummy(ac.module(Ids.POOLS));
        identity.setTestZZZIdentity(address(0));
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);ac.seal();
        assertFalse(ac.isSealed());assertEq(ac.bootstrap(),address(this));
        identity.setTestZZZIdentity(address(identity));ac.seal();assertTrue(ac.isSealed());
    }
    function testMissingOrMismatchedExitZZZCannotPermanentlySeal() public {
        fill();address exit=ac.module(Ids.MIGRATION);
        vm.mockCall(exit,abi.encodeWithSignature("currentZZZ()"),abi.encode(address(0)));
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);ac.seal();
        assertFalse(ac.isSealed());assertEq(ac.bootstrap(),address(this));
        vm.clearMockedCalls();
        vm.mockCall(exit,abi.encodeWithSignature("currentZZZ()"),abi.encode(address(0xBAD)));
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);ac.seal();
        vm.clearMockedCalls();ac.seal();assertTrue(ac.isSealed());
    }
    function testHolderExitRequiresPausedVaultAndPermanentlyBlocksCanonicalReplacement() public {
        fill();ac.seal();address boundVault=ac.module(Ids.VAULT);address handoff=ac.canonicalHandoff();
        vm.expectRevert(ZZZAccessController.Unauthorized.selector);ac.startLPExit();
        vm.prank(boundVault);vm.expectRevert(ZZZAccessController.Unauthorized.selector);ac.startLPExit();
        vm.prank(guardian);ac.setPaused(true);vm.prank(boundVault);ac.startLPExit();assertTrue(ac.lpExitStarted());
        vm.prank(address(0xA0A0));ac.setPaused(false);assertTrue(ac.lpExitStarted());assertFalse(ac.paused());
        vm.prank(boundVault);vm.expectRevert(ZZZAccessController.Unauthorized.selector);ac.startLPExit();
        ZZZAccessController.PreparationNotice memory notice;
        vm.prank(address(0xA0A0));vm.expectRevert(ZZZAccessController.Unauthorized.selector);ac.startPreparation(notice);
        vm.prank(handoff);vm.expectRevert(ZZZAccessController.Unauthorized.selector);ac.canonicalTransition(1,false,false);
        assertEq(ac.canonicalState(),0);assertFalse(ac.preparationActive());
    }
    function testSealErasesBootstrap() public {fill();ac.seal();assertEq(ac.bootstrap(),address(0));assertTrue(ac.isSealed());}
    function testFuzzTerminalCanonicalStateCannotReopen(uint8 seed) public {
        fill();ac.seal();address handoff=ac.canonicalHandoff();uint8 terminal=uint8(3+(seed%2));
        vm.prank(handoff);ac.canonicalTransition(terminal,false,false);
        for(uint8 next;next<5;++next){
            vm.prank(handoff);vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
            ac.canonicalTransition(next,false,true);
            assertEq(ac.canonicalState(),terminal);
        }
    }
    function testCannotReplaceModules() public {
        fill();ac.seal();BoundDummy other=new BoundDummy(address(ac));vm.expectRevert();ac.bind(Ids.VAULT,address(other));
    }
    function testGuardianCanPauseNotUnpause() public {
        fill();ac.seal();vm.prank(guardian);ac.setPaused(true);assertTrue(ac.paused());
        vm.prank(guardian);vm.expectRevert();ac.setPaused(false);
    }
    function testBootstrapCannotConfigureAfterSeal() public {fill();ac.seal();vm.expectRevert();ac.setKeeper(address(0xABC),true);}
    function testWrongControllerBindingRejected() public {
        BoundDummy wrong=new BoundDummy(address(0x123));vm.expectRevert();ac.bind(Ids.VAULT,address(wrong));
    }
    function testRetiredBridgeModulesCannotBeBoundEvenBeforeSeal() public {
        bytes32[4] memory ids=[keccak256("ZZZBridgeAdapter"),keccak256("ZZZMigrationReceiver"),keccak256("ZZZMigrationRegistry"),keccak256("ZZZBridgeRouter")];
        address candidate=address(new BoundDummy(address(ac)));
        for(uint256 n;n<ids.length;++n){vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);ac.bind(ids[n],candidate);assertEq(ac.module(ids[n]),address(0));}
    }
}
