// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {StdStorage,stdStorage} from "forge-std/StdStorage.sol";
import {SeaDropPoPLFixture} from "./SeaDropPoPLIntegration.t.sol";
import {ZZZSeaDropMint} from "../src/ZZZSeaDropMint.sol";

/// @notice Helper-only quota boundary model. Past aggregate counts are seeded
/// through getter-verified StdStorage locations, and NFT.mintedCount is mocked
/// to the same synthetic count. No old NFT, VRF, ownership, principal or payout
/// history is fabricated or claimed as verified. The separate actual integration
/// suite proves real NFT/Vault/VRF callback coupling; this model avoids 1,000
/// repeated mints merely to exercise the final numerical quota boundaries.
contract SeaDropQuotaBoundaryTest is SeaDropPoPLFixture {
    using stdStorage for StdStorage;

    function _seed(uint256 team,uint256 allowlist,uint256 publicCount,address buyer,uint256 personal) private {
        uint256 total=team+allowlist+publicCount;
        require(total<=1000 && team<=20 && allowlist<=500 && personal<=total,"unit history bounds");
        stdstore.target(address(helper)).sig("totalMinted()").checked_write(total);
        stdstore.target(address(helper)).sig("phaseMinted(uint8)").with_key(uint256(1)).checked_write(team);
        stdstore.target(address(helper)).sig("phaseMinted(uint8)").with_key(uint256(2)).checked_write(allowlist);
        stdstore.target(address(helper)).sig("phaseMinted(uint8)").with_key(uint256(3)).checked_write(publicCount);
        stdstore.target(address(helper)).sig("lifetimeMinted(address)").with_key(buyer).checked_write(personal);
        vm.mockCall(address(nft),abi.encodeWithSignature("mintedCount()"),abi.encode(total));
        assertEq(helper.totalMinted(),total);assertEq(nft.mintedCount(),total);
        assertEq(helper.phaseMinted(1),team);assertEq(helper.phaseMinted(2),allowlist);
        assertEq(helper.phaseMinted(3),publicCount);assertEq(helper.lifetimeMinted(buyer),personal);
    }
    function _begin(address buyer,uint256 quantity) private returns(uint256 first,bytes32 fingerprint,uint8 stage) {
        vm.prank(address(nft));return helper.beginMint(address(seaDrop),buyer,quantity);
    }
    function _finish(bytes32 fingerprint) private {
        vm.mockCall(address(nft),abi.encodeWithSignature("mintedCount()"),abi.encode(helper.totalMinted()));
        vm.prank(address(nft));helper.finishMint(fingerprint);
    }

    function testAllowlistHard500CannotConsumeUnmintedTeamReserve() public {
        _seed(0,499,0,ALICE,0);vm.warp(config.allowlistStart);
        (uint256 first,bytes32 fingerprint,uint8 phase)=_begin(ALICE,1);
        assertEq(first,500);assertEq(phase,2);assertEq(helper.phaseMinted(2),500);_finish(fingerprint);
        vm.expectRevert();_begin(BOB,1);
        assertEq(helper.totalMinted(),500);assertEq(helper.phaseMinted(1),0);assertEq(helper.phaseMinted(2),500);
        assertEq(helper.originalMintRecipient(501),address(0));assertFalse(helper.minting());
    }
    function testUnmintedTeamStaysReservedAfterUnusedAllowlistRollsToPublic() public {
        assertFalse(config.releaseUnusedTeamToPublic);
        _seed(0,0,979,ALICE,0);vm.warp(config.publicStart);
        (uint256 first,bytes32 fingerprint,)=_begin(ALICE,1);assertEq(first,980);_finish(fingerprint);
        vm.expectRevert();_begin(BOB,1);
        assertEq(helper.totalMinted(),980);assertEq(helper.phaseMinted(3),980);
        assertEq(helper.originalMintRecipient(981),address(0));
    }
    function testAllFiveHundredUnusedAllowlistSlotsCanRollIntoPublic() public {
        _seed(20,0,979,ALICE,0);vm.warp(config.publicStart);
        (uint256 first,bytes32 fingerprint,)=_begin(ALICE,1);assertEq(first,1000);_finish(fingerprint);
        assertEq(helper.totalMinted(),1000);assertEq(helper.phaseMinted(1),20);
        assertEq(helper.phaseMinted(2),0);assertEq(helper.phaseMinted(3),980);
    }
    function testFinalAvailableOneRejectsTwoWithoutPartialReservation() public {
        _seed(20,500,479,ALICE,0);vm.warp(config.publicStart);
        vm.expectRevert();_begin(ALICE,2);
        assertEq(helper.totalMinted(),999);assertEq(helper.lifetimeMinted(ALICE),0);
        assertEq(helper.originalMintRecipient(1000),address(0));assertEq(helper.mintStage(1000),0);
        assertFalse(helper.minting());assertEq(helper.activeRecipient(),address(0));
        (,bytes32 fingerprint,)=_begin(ALICE,1);_finish(fingerprint);assertEq(helper.totalMinted(),1000);
    }
    function testTotalOneThousandIsHardCeilingForEveryRemainingBuyer() public {
        _seed(20,500,480,ALICE,0);vm.warp(config.publicStart);
        vm.expectRevert();_begin(ALICE,1);vm.expectRevert();_begin(BOB,1);
        assertEq(helper.totalMinted(),1000);assertEq(helper.phaseMinted(3),480);assertFalse(helper.minting());
    }
    function testPublicWalletLimitUsesLifetimeMintCount() public {
        config.publicWalletLimit=2;helper.configure(config,uint128(PRICE),REVIEW);
        nft.updatePublicDrop(address(seaDrop),helper.expectedPublicDrop());
        _seed(2,0,0,ALICE,2);vm.warp(config.publicStart);
        vm.expectRevert();_begin(ALICE,1);assertEq(helper.totalMinted(),2);
        (,bytes32 fingerprint,)=_begin(BOB,1);_finish(fingerprint);
        assertEq(helper.lifetimeMinted(ALICE),2);assertEq(helper.lifetimeMinted(BOB),1);
    }
    function testPhaseEdgesAreInclusiveAndOutsideWindowsNotEligible() public {
        vm.warp(uint256(config.teamStart)-1);assertEq(helper.currentPhase(),0);
        vm.warp(config.teamStart);assertEq(helper.currentPhase(),1);
        vm.warp(config.teamEnd);assertEq(helper.currentPhase(),1);
        vm.warp(config.allowlistStart);assertEq(helper.currentPhase(),2);
        vm.warp(config.allowlistEnd);assertEq(helper.currentPhase(),2);
        vm.warp(config.publicStart);assertEq(helper.currentPhase(),3);
        vm.warp(config.publicEnd);assertEq(helper.currentPhase(),3);
        vm.warp(uint256(config.publicEnd)+1);assertEq(helper.currentPhase(),0);
        vm.expectRevert();_begin(ALICE,1);assertEq(helper.totalMinted(),0);
    }
    function testOverlappingWindowsCannotBeConfigured() public {
        bytes32 beforeHash=helper.configurationHash();
        ZZZSeaDropMint.MintConfig memory next=config;next.teamEnd=next.allowlistStart;
        vm.expectRevert();helper.configure(next,uint128(PRICE),REVIEW);
        next=config;next.allowlistEnd=next.publicStart;
        vm.expectRevert();helper.configure(next,uint128(PRICE),REVIEW);
        assertEq(helper.configurationHash(),beforeHash);
    }
    function testQuotasCannotShrinkBelowIssuedOrCreateAlreadySoldReserve() public {
        _seed(7,11,0,ALICE,0);
        ZZZSeaDropMint.MintConfig memory next=config;next.teamAllocation=6;
        vm.expectRevert();helper.configure(next,uint128(PRICE),REVIEW);
        next=config;next.allowlistAllocation=10;
        vm.expectRevert();helper.configure(next,uint128(PRICE),REVIEW);
        _seed(0,500,480,ALICE,0);next=config;next.teamAllocation=21;
        // Deliberately different root isolates the reserve guard from the
        // same-root leaf-terms guard. No proof or mint is approved by this model.
        next.merkleRoot=keccak256("TEST ONLY different quota review root");
        vm.expectRevert();helper.configure(next,uint128(PRICE),REVIEW);
        assertEq(helper.totalMinted(),980);assertEq(helper.mintConfig().teamAllocation,20);
    }
    function testZeroRootAllPublicModeIsAvailableWithoutFreeOrAllowlistQuota() public {
        config.teamAllocation=0;config.allowlistAllocation=0;config.merkleRoot=bytes32(0);
        helper.configure(config,uint128(PRICE),REVIEW);_syncDrop();vm.warp(config.publicStart);
        (uint256 first,bytes32 fingerprint,uint8 phase)=_begin(ALICE,1);
        assertEq(first,1);assertEq(phase,3);_finish(fingerprint);
        assertEq(helper.totalMinted(),1);assertEq(helper.phaseMinted(1),0);assertEq(helper.phaseMinted(2),0);
    }
    function testWholeBatchStatsAreReservedBeforeCallbackAndCannotBeReentered() public {
        vm.warp(config.publicStart);(uint256 first,bytes32 fingerprint,)=_begin(ALICE,3);
        (uint256 personal,uint256 total,uint256 maximum)=nft.getMintStats(ALICE);
        assertEq(first,1);assertEq(personal,3);assertEq(total,3);assertEq(maximum,1000);
        assertEq(nft.mintedCount(),0);assertTrue(helper.minting());
        for(uint256 ordinal=1;ordinal<=3;++ordinal){assertEq(helper.originalMintRecipient(ordinal),ALICE);assertEq(helper.mintStage(ordinal),3);}
        vm.expectRevert();_begin(BOB,1);assertEq(helper.totalMinted(),3);
        _finish(fingerprint);assertFalse(helper.minting());
    }
    function testFuzzPublicLastSupplyBoundary(uint16 rawTotal,uint8 rawQuantity) public {
        uint256 total=bound(uint256(rawTotal),20,1000);uint256 quantity=bound(uint256(rawQuantity),1,10);
        _seed(20,0,total-20,ALICE,0);vm.warp(config.publicStart);
        if(total+quantity>1000){
            vm.expectRevert();_begin(ALICE,quantity);assertEq(helper.totalMinted(),total);assertFalse(helper.minting());
        }else{
            (uint256 first,bytes32 fingerprint,)=_begin(ALICE,quantity);
            assertEq(first,total+1);assertEq(helper.totalMinted(),total+quantity);_finish(fingerprint);
        }
    }
}
