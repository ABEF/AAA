// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {BoundDummy} from "./mocks/Mocks.sol";
contract AccessControllerTest is Test {
    ZZZAccessController ac;address guardian=address(0x123);address keeper=address(0x456);
    function setUp() public {
        address[] memory a=new address[](1);a[0]=address(this);ac=new ZZZAccessController(1 days,a,a,keeper,guardian);
    }
    function fill() private {
        bytes32[16] memory ids=[Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,Ids.STRATEGY,
            Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.BRIDGE,Ids.RECEIVER,Ids.ORACLE,Ids.POOLS,Ids.ROUTES,Ids.TRANSPORT];
        for(uint256 i;i<ids.length;i++)ac.bind(ids[i],address(new BoundDummy(address(ac))));
    }
    function testIncompleteDeploymentCannotSeal() public {vm.expectRevert();ac.seal();}
    function testCanonicalRandomnessMustBeConfiguredBeforeSeal() public {
        fill();BoundDummy nft=BoundDummy(ac.module(Ids.NFT));nft.setRandomnessConfigured(false);
        vm.expectRevert();ac.seal();assertFalse(ac.isSealed());assertEq(ac.bootstrap(),address(this));
        nft.setRandomnessConfigured(true);ac.seal();assertTrue(ac.isSealed());
    }
    function testSealErasesBootstrap() public {fill();ac.seal();assertEq(ac.bootstrap(),address(0));assertTrue(ac.isSealed());}
    function testCannotReplaceModules() public {
        fill();ac.seal();BoundDummy other=new BoundDummy(address(ac));vm.expectRevert();ac.bind(Ids.VAULT,address(other));
    }
    function testGuardianCanPauseNotUnpause() public {
        fill();ac.seal();vm.prank(guardian);ac.setPaused(true);assertTrue(ac.paused());
        vm.prank(guardian);vm.expectRevert();ac.setPaused(false);
    }
    function testDelayCannotBeShortened() public {vm.expectRevert();ac.updateDelay(0);}
    function testTimelockedKeeperChange() public {
        fill();ac.seal();bytes memory data=abi.encodeCall(ac.setKeeper,(address(0xABC),true));bytes32 salt=keccak256("new-keeper");
        ac.schedule(address(ac),0,data,bytes32(0),salt,1 days);vm.expectRevert();ac.execute(address(ac),0,data,bytes32(0),salt);
        vm.warp(block.timestamp+1 days);ac.execute(address(ac),0,data,bytes32(0),salt);assertTrue(ac.keepers(address(0xABC)));
    }
    function testBootstrapCannotConfigureAfterSeal() public {fill();ac.seal();vm.expectRevert();ac.setKeeper(address(0xABC),true);}
    function testWrongControllerBindingRejected() public {
        BoundDummy wrong=new BoundDummy(address(0x123));vm.expectRevert();ac.bind(Ids.VAULT,address(wrong));
    }
}
