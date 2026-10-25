// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
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
        address[] memory a=new address[](1);a[0]=address(this);ac=new ZZZAccessController(0,a,a,keeper,guardian);
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
    function testZeroDelayCannotBeChanged() public {vm.expectRevert();ac.updateDelay(0);}
    function testImmediateGovernanceKeeperChange() public {
        fill();ac.seal();bytes memory data=abi.encodeCall(ac.setKeeper,(address(0xABC),true));bytes32 salt=keccak256("new-keeper");
        ac.schedule(address(ac),0,data,bytes32(0),salt,0);
        ac.execute(address(ac),0,data,bytes32(0),salt);assertTrue(ac.keepers(address(0xABC)));
    }
    function testBootstrapCannotConfigureAfterSeal() public {fill();ac.seal();vm.expectRevert();ac.setKeeper(address(0xABC),true);}
    function testWrongControllerBindingRejected() public {
        BoundDummy wrong=new BoundDummy(address(0x123));vm.expectRevert();ac.bind(Ids.VAULT,address(wrong));
    }
    function testFuzzNonzeroConstructorAndOperationDelayRejected(uint32 delay) public {
        vm.assume(delay != 0);
        address[] memory roles=new address[](1);roles[0]=address(this);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        new ZZZAccessController(delay,roles,roles,keeper,guardian);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        ac.schedule(address(ac),0,bytes(""),bytes32(0),bytes32(0),delay);
        address[] memory targets=new address[](0);uint256[] memory values=new uint256[](0);bytes[] memory calls=new bytes[](0);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        ac.scheduleBatch(targets,values,calls,bytes32(0),bytes32(0),delay);
        assertEq(ac.getMinDelay(),0);
    }
    function testAuthorizedGovernanceCannotIntroduceDelay() public {
        fill();ac.seal();bytes memory data=abi.encodeCall(ac.updateDelay,(1 days));bytes32 salt=keccak256("no delay");
        ac.schedule(address(ac),0,data,bytes32(0),salt,0);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);ac.execute(address(ac),0,data,bytes32(0),salt);
        assertEq(ac.getMinDelay(),0);
    }
    function testNoUnscheduledAlteredCancelledOrRepeatedExecution() public {
        fill();ac.seal();bytes memory data=abi.encodeCall(ac.setKeeper,(address(0xABC),true));bytes32 salt=keccak256("exact operation");
        vm.expectRevert();ac.execute(address(ac),0,data,bytes32(0),salt);
        ac.schedule(address(ac),0,data,bytes32(0),salt,0);
        bytes32 id=ac.hashOperation(address(ac),0,data,bytes32(0),salt);assertTrue(ac.isOperationReady(id));
        vm.expectRevert();ac.execute(address(ac),0,abi.encodeCall(ac.setKeeper,(guardian,true)),bytes32(0),salt);
        ac.cancel(id);vm.expectRevert();ac.execute(address(ac),0,data,bytes32(0),salt);
        ac.schedule(address(ac),0,data,bytes32(0),salt,0);ac.execute(address(ac),0,data,bytes32(0),salt);
        assertTrue(ac.keepers(address(0xABC)));assertTrue(ac.isOperationDone(id));
        vm.expectRevert();ac.execute(address(ac),0,data,bytes32(0),salt);
        vm.expectRevert();ac.schedule(address(ac),0,data,bytes32(0),salt,0);
    }
    function testProposerAndExecutorPermissionsRemainSeparate() public {
        address[] memory proposers=new address[](1);proposers[0]=address(this);
        address[] memory executors=new address[](1);executors[0]=guardian;
        ZZZAccessController separate=new ZZZAccessController(0,proposers,executors,keeper,guardian);
        bytes memory data=abi.encodeCall(separate.setKeeper,(address(0xABC),true));bytes32 salt=keccak256("roles");
        vm.prank(keeper);vm.expectRevert();separate.schedule(address(separate),0,data,bytes32(0),salt,0);
        vm.prank(guardian);vm.expectRevert();separate.schedule(address(separate),0,data,bytes32(0),salt,0);
        separate.schedule(address(separate),0,data,bytes32(0),salt,0);
        vm.expectRevert();separate.execute(address(separate),0,data,bytes32(0),salt);
        vm.prank(keeper);vm.expectRevert();separate.execute(address(separate),0,data,bytes32(0),salt);
        vm.prank(guardian);separate.execute(address(separate),0,data,bytes32(0),salt);
        assertTrue(separate.keepers(address(0xABC)));
    }
    function testImmediateBatchIsAtomicAndRoleGated() public {
        fill();ac.seal();address[] memory targets=new address[](2);targets[0]=address(ac);targets[1]=address(ac);
        uint256[] memory values=new uint256[](2);bytes[] memory calls=new bytes[](2);
        calls[0]=abi.encodeCall(ac.setKeeper,(address(0xABC),true));calls[1]=abi.encodeCall(ac.setGuardian,(address(0xDEF),true));
        bytes32 salt=keccak256("atomic batch");uint256 beforeTime=block.timestamp;
        vm.prank(keeper);vm.expectRevert();ac.scheduleBatch(targets,values,calls,bytes32(0),salt,0);
        ac.scheduleBatch(targets,values,calls,bytes32(0),salt,0);
        vm.prank(guardian);vm.expectRevert();ac.executeBatch(targets,values,calls,bytes32(0),salt);
        ac.executeBatch(targets,values,calls,bytes32(0),salt);
        assertEq(block.timestamp,beforeTime);assertTrue(ac.keepers(address(0xABC)));assertTrue(ac.guardians(address(0xDEF)));
        calls[0]=abi.encodeCall(ac.setKeeper,(address(0xABC),false));calls[1]=abi.encodeCall(ac.setGuardian,(address(0),true));
        salt=keccak256("batch rollback");ac.scheduleBatch(targets,values,calls,bytes32(0),salt,0);
        vm.expectRevert();ac.executeBatch(targets,values,calls,bytes32(0),salt);
        assertTrue(ac.keepers(address(0xABC)));assertTrue(ac.isOperationReady(ac.hashOperationBatch(targets,values,calls,bytes32(0),salt)));
    }
    function testPredecessorStillRequiresCompletionNotElapsedTime() public {
        fill();ac.seal();bytes memory first=abi.encodeCall(ac.setKeeper,(address(0xABC),true));
        bytes memory second=abi.encodeCall(ac.setKeeper,(address(0xDEF),true));bytes32 salt=keccak256("ordered");
        bytes32 predecessor=ac.hashOperation(address(ac),0,first,bytes32(0),salt);
        ac.schedule(address(ac),0,second,predecessor,salt,0);
        vm.expectRevert();ac.execute(address(ac),0,second,predecessor,salt);
        ac.schedule(address(ac),0,first,bytes32(0),salt,0);ac.execute(address(ac),0,first,bytes32(0),salt);
        ac.execute(address(ac),0,second,predecessor,salt);assertTrue(ac.keepers(address(0xDEF)));
    }
    function testReservedTimestampCannotMislabelZeroDelayOperation() public {
        vm.warp(1);vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        ac.schedule(address(ac),0,bytes(""),bytes32(0),bytes32(0),0);
    }
    function testRetiredBridgeModulesCannotBeBoundEvenBeforeSeal() public {
        bytes32[4] memory ids=[Ids.BRIDGE,Ids.RECEIVER,Ids.ROUTES,Ids.TRANSPORT];
        address candidate=address(new BoundDummy(address(ac)));
        for(uint256 n;n<ids.length;++n){vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);ac.bind(ids[n],candidate);assertEq(ac.module(ids[n]),address(0));}
    }
}
