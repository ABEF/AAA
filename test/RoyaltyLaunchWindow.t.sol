// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {InKindNFT, InKindFaultToken} from "./RoyaltyRecovery.t.sol";
import {MockAccess, MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

contract RoyaltyLaunchWindowTest is Test {
    MockAccess a; InKindNFT nft; ZZZRoyaltyRewards r; MockToken token;
    address alice=address(0xa11ce); address bob=address(0xb0b); address carol=address(0xca701);
    uint64 end; uint256 opening;
    function setUp() public {
        vm.warp(1000);a=new MockAccess();nft=new InKindNFT(address(a));r=nft.royalties();
        a.bind(Ids.NFT,address(nft));a.seal();token=new MockToken(6);nft.add(address(token));
        nft.mint(alice,1,0);nft.mint(bob,2,1);nft.mint(carol,3,2);
        end=1200;opening=uint256(end)+1 hours;
        vm.prank(address(nft));r.setMintEnd(end);vm.deal(address(this),100 ether);
    }
    function pay(uint256 n) internal {(bool ok,)=address(r).call{value:n}("");assertTrue(ok);}
    function testUnconfiguredAndPrematureClaimsCannotSpendInitialPool() public {
        nft.activate(1);pay(6 ether);token.mint(address(r),600e6);r.sync(address(0));
        assertEq(r.openingPool(address(0)),6 ether);assertEq(r.orphaned(address(0)),0);assertEq(r.liabilities(address(0)),0);
        assertEq(r.claimable(1,address(0)),0);assertEq(r.claimable(1,address(token)),0);
        vm.prank(alice);vm.expectRevert();r.claim(1,address(0));
        vm.expectRevert();r.allocateUnallocated(address(0),6 ether,bytes32(uint256(1)));
    }
    function testAllGraceActivationsShareEarlierReceiptsAtDeadline() public {
        pay(6 ether);token.mint(address(r),600e6);nft.activate(1);
        vm.warp(opening-1);nft.activate(2);nft.activate(3);
        assertEq(r.claimable(1,address(0)),0);
        vm.warp(opening);assertTrue(r.royaltiesOpen());
        assertEq(r.claimable(1,address(0)),1 ether);assertEq(r.claimable(2,address(0)),2 ether);
        assertEq(r.claimable(3,address(token)),300e6);
        vm.prank(alice);assertEq(r.claim(1,address(0)),1 ether);
        vm.prank(bob);assertEq(r.claim(2,address(token)),200e6);
    }
    function testActivationExactlyAtCutoffCannotTakeInitialPool() public {
        nft.activate(1);pay(6 ether);token.mint(address(r),600e6);
        vm.warp(opening);nft.activate(2);
        assertEq(r.claimable(1,address(0)),6 ether);assertEq(r.claimable(2,address(0)),0);
        assertEq(r.claimable(2,address(token)),0);
        pay(3 ether);token.mint(address(r),300e6);
        assertEq(r.claimable(1,address(0)),7 ether);assertEq(r.claimable(2,address(0)),2 ether);
        assertEq(r.claimable(2,address(token)),200e6);
    }
    function testLateFirstInteractionStillUsesCutoffCohort() public {
        nft.activate(1);pay(6 ether);vm.warp(opening+30 days);nft.activate(2);
        assertEq(r.claimable(1,address(0)),6 ether);assertEq(r.claimable(2,address(0)),0);
    }
    function testZeroAtDeadlineRemainsUnallocatedUntilExplicitGovernance() public {
        pay(6 ether);vm.warp(opening);nft.activate(1);
        assertEq(r.claimable(1,address(0)),0);assertEq(r.orphaned(address(0)),6 ether);
        nft.activate(2);r.allocateUnallocated(address(0),6 ether,bytes32(uint256(1)));
        assertEq(r.claimable(1,address(0)),2 ether);assertEq(r.claimable(2,address(0)),4 ether);
    }
    function testTransferCarriesInitialEntitlementNotSnapshotWallet() public {
        nft.activate(1);pay(6 ether);vm.prank(alice);nft.transferFrom(alice,bob,1);
        vm.warp(opening);vm.prank(alice);vm.expectRevert();r.claim(1,address(0));
        vm.prank(bob);assertEq(r.claim(1,address(0)),6 ether);
    }
    function testRescheduleOnlyDuringMintAndAlwaysFullDay() public {
        vm.warp(end);vm.prank(address(nft));r.setMintEnd(end+300);
        assertEq(r.royaltiesOpenAt(),opening+300);
        vm.warp(end+301);vm.prank(address(nft));vm.expectRevert();r.setMintEnd(end+600);
        vm.prank(alice);vm.expectRevert();r.setMintEnd(end+600);
    }
    function testFaultedCurrencyIncludesGraceButExcludesLateActivations() public {
        InKindFaultToken bad=new InKindFaultToken();nft.add(address(bad));
        nft.activate(1);bad.mint(address(r),600e6);bad.setFailed(true);
        nft.activate(2);vm.warp(opening);nft.activate(3);
        bad.setFailed(false);r.sync(address(bad));
        assertEq(r.claimable(1,address(bad)),200e6);assertEq(r.claimable(2,address(bad)),400e6);
        assertEq(r.claimable(3,address(bad)),0);
        bad.mint(address(r),600e6);assertEq(r.claimable(3,address(bad)),300e6);
    }
    function testPostOpeningCurrencyKeepsExplicitRecoveryRule() public {
        nft.activate(1);vm.warp(opening);nft.activate(2);
        MockToken later=new MockToken(6);later.mint(address(r),300e6);nft.add(address(later));
        assertEq(r.claimable(1,address(later)),0);
        r.allocateUnallocated(address(later),300e6,bytes32(uint256(1)));
        assertEq(r.claimable(1,address(later)),100e6);assertEq(r.claimable(2,address(later)),200e6);
    }
    function testCanonicalCannotDiscardAnUnopenedWindow() public {
        a.bind(Ids.CANONICAL,address(this));a.setCanonicalState(1);
        vm.expectRevert();r.canonicalCapture();
    }
    function testCompletedOpeningCanonicalHeaderCarriesDeadlineAndRejectsOldHeader() public {
        nft.activate(1);vm.warp(opening);r.sync(address(0));r.sync(address(token));
        a.bind(Ids.CANONICAL,address(this));a.setCanonicalState(1);r.canonicalCapture();r.canonicalSettle();
        bytes memory header=r.canonicalExport(0);assertEq(header.length,160);
        (uint256 currencies,uint256 count,uint256 weight,uint64 close,uint8 capacity)=abi.decode(header,(uint256,uint256,uint256,uint64,uint8));
        assertEq(close,end);assertEq(count,3);assertEq(weight,1);assertEq(currencies,2);
        assertEq(capacity,16);
        MockAccess dest=new MockAccess();InKindNFT other=new InKindNFT(address(dest));
        dest.bind(Ids.CANONICAL,address(this));dest.setCanonicalState(2);
        ZZZRoyaltyRewards target=other.royalties();
        vm.expectRevert();target.canonicalImport(0,abi.encode(currencies,count,weight));
        target.canonicalImport(0,header);
        assertEq(target.mintEnd(),end);assertTrue(target.royaltiesOpen());
    }
    function testCapacityCanExpandAfterSealWithoutChangingExistingRights() public {
        nft.activate(1);
        for(uint256 i=1;i<16;++i)nft.add(address(new MockToken(6)));
        MockToken seventeenth=new MockToken(6);seventeenth.mint(address(r),300e6);
        vm.expectRevert();nft.add(address(seventeenth));
        vm.prank(alice);vm.expectRevert();r.increaseAssetCapacity(17,bytes32(uint256(1)));
        vm.prank(address(nft));r.increaseAssetCapacity(17,bytes32(uint256(1)));
        nft.add(address(seventeenth));assertEq(r.assetCount(),18);
        nft.activate(2);vm.warp(opening);
        assertEq(r.claimable(1,address(seventeenth)),0);
        r.allocateAllUnallocated(address(seventeenth),bytes32(uint256(1)));
        assertEq(r.claimable(1,address(seventeenth)),100e6);assertEq(r.claimable(2,address(seventeenth)),200e6);
        vm.prank(address(nft));vm.expectRevert();r.increaseAssetCapacity(16,bytes32(uint256(1)));
        vm.prank(address(nft));vm.expectRevert();r.increaseAssetCapacity(65,bytes32(uint256(1)));
    }
    function testAllocateAllLeavesNoUnallocatedWholeUnitsAndCannotSpendEarnedFunds() public {
        pay(6 ether);vm.warp(opening);nft.activate(1);nft.activate(2);
        assertEq(r.allocateAllUnallocated(address(0),bytes32(uint256(1))),6 ether);
        assertEq(r.orphaned(address(0)),0);assertEq(r.liabilities(address(0)),6 ether);
        assertEq(r.allocateAllUnallocated(address(0),bytes32(uint256(1))),0);
        assertEq(r.claimable(1,address(0)),2 ether);assertEq(r.claimable(2,address(0)),4 ether);
    }
    function testThousandNFTsOpeningWeightsAndDormantExclusion() public {
        // Distinct wallets, all three weights, 999 active and one dormant.
        for(uint256 i=4;i<=1000;++i)nft.mint(address(uint160(0x10000+i)),i,uint8(i%3));
        uint256 total;
        for(uint256 i=1;i<1000;++i){nft.activate(i);total+=uint256(nft.rarityOf(i))+1;}
        uint256 amount=total*1000;token.mint(address(r),amount);vm.warp(opening);
        for(uint256 i=1;i<1000;++i){
            address owner=nft.ownerOf(i);uint256 expected=(uint256(nft.rarityOf(i))+1)*1000;
            vm.prank(owner);assertEq(r.claim(i,address(token)),expected);assertEq(token.balanceOf(owner),expected);
        }
        assertEq(r.claimable(1000,address(token)),0);assertEq(token.balanceOf(address(r)),0);
        assertEq(r.liabilities(address(token)),0);
    }
    function testFuzzInitialPoolIsConservedAndCannotBeClaimedTwice(uint96 amount) public {
        amount=uint96(bound(amount,6,1e24));nft.activate(1);nft.activate(2);nft.activate(3);
        token.mint(address(r),amount);vm.warp(opening);
        vm.prank(alice);uint256 x=r.claim(1,address(token));
        vm.prank(bob);uint256 y=r.claim(2,address(token));
        vm.prank(carol);uint256 z=r.claim(3,address(token));
        assertLe(x+y+z,amount);assertEq(token.balanceOf(address(r)),uint256(amount)-x-y-z);
        assertEq(r.accounted(address(token)),token.balanceOf(address(r)));
        vm.prank(alice);assertEq(r.claim(1,address(token)),0);
    }
    receive() external payable {}
}

contract RoyaltySaleEndAuthorityTest is Test {
    MockAccess a; ZZZNFT n;MockVRF v;
    bool mutateEnd;
    function setUp() public {vm.warp(1000);a=new MockAccess();ProtocolPolicyFixture.bind(address(a));n=new ZZZNFT(address(a),"ipfs://royalty-window/");a.bind(Ids.NFT,address(n));a.bind(Ids.VAULT,address(this));v=new MockVRF();ProtocolPolicyFixture.randomness(address(a),address(v),bytes32(uint256(1)),1,3,500000,false);a.seal();}
    function testOnlyGovernanceCanSetOfficialMintEnd() public {
        vm.prank(address(123));vm.expectRevert();n.setMintEnd(1200);
        n.setMintEnd(1200);assertEq(n.royaltyRewards().royaltiesOpenAt(),4800);
    }
    function testUnconfiguredAndClosedSaleCannotMint() public {
        vm.expectRevert();n.mint(address(123),1);
        n.setMintEnd(1200);vm.warp(1201);vm.expectRevert();n.mint(address(123),1);
        assertEq(n.mintedCount(),0);
    }
    function mintProceedsRecipient() external pure returns(address){return address(0x7ea5);}
    function onERC721Received(address,address,uint256,bytes calldata) external returns(bytes4){
        if(mutateEnd)n.setMintEnd(1300);
        return 0x150b7a02;
    }
    function testMintCallbackCannotChangeReviewedSaleDeadline() public {
        n.setMintEnd(1200);mutateEnd=true;
        vm.expectRevert();n.mint(address(this),1);
        assertEq(n.mintedCount(),0);assertEq(n.royaltyRewards().mintEnd(),1200);assertEq(v.sequence(),0);
        mutateEnd=false;n.mint(address(this),1);assertEq(n.ownerOf(1),address(this));assertEq(n.mintedCount(),1);
    }
}
