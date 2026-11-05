// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {MockAccess, MockToken} from "./mocks/Mocks.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

contract InKindFaultToken is MockToken {
    bool public failed;
    constructor() MockToken(6) {}
    function setFailed(bool value) external { failed = value; }
    function balanceOf(address who) public view override returns (uint256) {
        require(!failed,"read unavailable"); return super.balanceOf(who);
    }
}
contract InKindNFT is ERC721 {
    ZZZRoyaltyRewards public royalties;
    ZZZClaimRouter public claimRouter;
    uint256 public mintedCount;
    mapping(uint256=>uint256) public tokenAtOrdinal;
    mapping(uint256=>uint8) public rarityOf;
    constructor(address control) ERC721("In-kind fixture","IK") {
        ProtocolPolicyFixture.bind(control);
        royalties = new ZZZRoyaltyRewards(address(this));
        royalties.bindCanonicalController(control);
        claimRouter = new ZZZClaimRouter(control,address(this),address(royalties));
    }
    function mint(address owner,uint256 id,uint8 rarity) external {
        _mint(owner,id); tokenAtOrdinal[++mintedCount]=id; rarityOf[id]=rarity;
    }
    function activate(uint256 id) external { royalties.activate(id,uint256(rarityOf[id])+1); }
    function add(address token) external { royalties.addAsset(token); }
}

contract OriginalCurrencyRoyaltyTest is Test {
    MockAccess a; InKindNFT nft; ZZZRoyaltyRewards r; MockToken usdc; MockToken other;
    address alice=address(0xa11ce); address bob=address(0xb0b); address carol=address(0xca701);
    bytes32 constant REVIEW=keccak256("reviewed original-currency allocation");
    function setUp() public {
        a=new MockAccess(); nft=new InKindNFT(address(a)); r=nft.royalties();
        usdc=new MockToken(6);other=new MockToken(18);nft.add(address(usdc));nft.add(address(other));
        a.bind(Ids.NFT,address(nft));a.seal();
        nft.mint(alice,1,0);nft.mint(bob,2,1);nft.mint(carol,3,2);
        vm.deal(address(this),10 ether);
        vm.prank(address(nft));r.setMintEnd(uint64(block.timestamp+1));
        vm.warp(block.timestamp+3601);r.syncAll();
    }
    function pay(uint256 n) internal {(bool ok,)=address(r).call{value:n}("");assertTrue(ok);}
    function activateAll() internal {nft.activate(1);nft.activate(2);nft.activate(3);}
    function testFreshRoyaltyProfileHasNoSwapOrApprovalEntrypoint() public {
        assertEq(r.ROYALTY_SETTLEMENT_VERSION(),4);assertEq(r.ROYALTY_RECOVERY_VERSION(),2);
        bytes[4] memory calls=[abi.encodeWithSignature("converter()"),
            abi.encodeWithSignature("bindConverter(address)",alice),
            abi.encodeWithSignature("convertBatch(address,uint256[],bytes32,uint256,uint256)",address(usdc),new uint256[](1),REVIEW,1,block.timestamp),
            abi.encodeWithSignature("recoverUnallocated(address,uint256,bytes32,uint256,uint256,bytes32)",address(usdc),1,REVIEW,1,block.timestamp,REVIEW)];
        for(uint256 i;i<calls.length;++i){(bool ok,)=address(r).call(calls[i]);assertFalse(ok);}
        assertEq(usdc.allowance(address(r),alice),0);
    }
    function testThreeCurrenciesWeightsClaimsAndTransferStaySeparate() public {
        activateAll();pay(0.6 ether);usdc.mint(address(r),600e6);other.mint(address(r),1200e18);
        vm.prank(alice);assertEq(r.claim(1,address(usdc)),100e6);
        assertEq(r.claimable(1,address(0)),0.1 ether);assertEq(r.claimable(1,address(other)),200e18);
        vm.prank(alice);nft.transferFrom(alice,bob,1);
        vm.prank(alice);vm.expectRevert();r.claim(1,address(other));
        vm.prank(bob);assertEq(r.claim(1,address(other)),200e18);
        vm.prank(bob);assertEq(r.claim(2,address(usdc)),200e6);
        vm.prank(carol);assertEq(r.claim(3,address(usdc)),300e6);
        assertEq(r.liabilities(address(usdc)),0);
    }
    function testSingleTransactionClaimsAllOriginalRoyaltyCurrencies() public {
        activateAll();pay(0.6 ether);usdc.mint(address(r),600e6);other.mint(address(r),1200e18);
        ZZZClaimRouter.Claim[] memory c=new ZZZClaimRouter.Claim[](3);
        c[0]=ZZZClaimRouter.Claim(1,address(0),true);c[1]=ZZZClaimRouter.Claim(1,address(usdc),true);
        c[2]=ZZZClaimRouter.Claim(1,address(other),true);
        ZZZClaimRouter router=nft.claimRouter();
        vm.prank(alice);uint256[] memory out=router.claimBatch(c);
        assertEq(out[0],0.1 ether);assertEq(out[1],100e6);assertEq(out[2],200e18);
        assertEq(alice.balance,0.1 ether);assertEq(usdc.balanceOf(alice),100e6);
    }
    function testReviewedOriginalCurrencyRecoveryExcludesOlderEarnedReceipts() public {
        usdc.mint(address(r),300e6);nft.activate(1);usdc.mint(address(r),100e6);nft.activate(2);
        assertEq(r.orphaned(address(usdc)),300e6);
        r.allocateUnallocated(address(usdc),300e6,REVIEW);
        assertEq(r.claimable(1,address(usdc)),200e6);assertEq(r.claimable(2,address(usdc)),200e6);
        assertEq(r.claimable(3,address(usdc)),0);assertEq(r.orphaned(address(usdc)),0);
        assertEq(address(r).balance,0);assertEq(r.accounted(address(usdc)),400e6);
        vm.expectRevert();r.allocateUnallocated(address(usdc),1,REVIEW);
    }
    function testUnknownCurrencyNeedsReviewAdmissionThenRecoveryInSameToken() public {
        nft.activate(1);MockToken unknown=new MockToken(8);unknown.mint(address(r),77);
        vm.expectRevert();r.allocateUnallocated(address(unknown),77,REVIEW);
        nft.add(address(unknown));assertEq(r.claimable(1,address(unknown)),0);
        r.allocateUnallocated(address(unknown),77,REVIEW);
        vm.prank(alice);assertEq(r.claim(1,address(unknown)),77);
        assertEq(unknown.balanceOf(alice),77);
    }
    function testRecoveryAuthorityPausePreparationAndNoBeneficiaryFailClosed() public {
        usdc.mint(address(r),300);r.sync(address(usdc));
        vm.expectRevert();r.allocateUnallocated(address(usdc),300,REVIEW);
        nft.activate(1);a.setKeeper(bob,true);
        vm.prank(bob);vm.expectRevert();r.allocateUnallocated(address(usdc),300,REVIEW);
        a.setPaused(true);vm.expectRevert();r.allocateUnallocated(address(usdc),300,REVIEW);
        a.setPaused(false);a.setPreparation(true);vm.expectRevert();r.allocateUnallocated(address(usdc),300,REVIEW);
        a.setPreparation(false);vm.expectRevert();r.allocateUnallocated(address(usdc),300,bytes32(0));
        vm.expectRevert();r.allocateUnallocated(address(usdc),0,REVIEW);
        r.allocateUnallocated(address(usdc),300,REVIEW);assertEq(r.liabilities(address(usdc)),300);
    }
    function testUnreadableCurrencyDefersOnlyItsNewCohortAndOldFundsCannotBeRecovered() public {
        InKindFaultToken t=new InKindFaultToken();nft.add(address(t));nft.activate(1);
        t.mint(address(r),100);t.setFailed(true);nft.activate(2);
        assertFalse(r.eligibleFor(2,address(t)));pay(3 ether);
        vm.prank(bob);assertEq(r.claim(2,address(0)),2 ether);
        t.setFailed(false);vm.expectRevert();r.allocateUnallocated(address(t),100,REVIEW);
        r.sync(address(t));assertEq(r.claimable(1,address(t)),100);assertEq(r.claimable(2,address(t)),0);
        t.mint(address(r),300);vm.prank(bob);assertEq(r.claim(2,address(t)),200);
    }
    function testNativeRecoveryAndTerminalLPExitKeepFutureRoyalties() public {
        pay(0.3 ether);nft.activate(1);r.allocateUnallocated(address(0),0.3 ether,REVIEW);
        a.bind(Ids.VAULT,address(this));a.setPaused(true);a.startLPExit();a.setPaused(false);
        other.mint(address(r),7);vm.prank(alice);assertEq(r.claim(1,address(other)),7);
        vm.prank(alice);assertEq(r.claim(1,address(0)),0.3 ether);
    }
    function testFuzzRecoveredSourceClaimsNeverExceedFundedUnits(uint96 raw) public {
        uint256 n=uint256(raw)+1;usdc.mint(address(r),n);activateAll();
        r.allocateUnallocated(address(usdc),n,REVIEW);
        vm.prank(alice);uint256 x=r.claim(1,address(usdc));vm.prank(bob);uint256 y=r.claim(2,address(usdc));
        vm.prank(carol);uint256 z=r.claim(3,address(usdc));
        assertLe(x+y+z,n);assertEq(usdc.balanceOf(address(r))+x+y+z,n);
        assertEq(r.liabilities(address(usdc)),n-x-y-z);assertEq(r.orphaned(address(usdc)),0);
    }
    function testThousandNFTsMultipleWalletsRaritiesAndDormantKeepExactSourcePayouts() public {
        uint256 totalWeight=1998;
        usdc.mint(address(r),totalWeight*1e6);
        for(uint256 i=1;i<=1000;++i){
            if(i>3)nft.mint(address(uint160(0x10000+i%37)),i,uint8((i-1)%3));
            if(i<1000)nft.activate(i);
        }
        assertEq(nft.mintedCount(),1000);assertEq(r.activationCount(),999);
        assertEq(r.totalWeight(),totalWeight);
        r.allocateUnallocated(address(usdc),totalWeight*1e6,REVIEW);
        uint256 paid;
        for(uint256 i=1;i<1000;++i){
            address owner=nft.ownerOf(i);uint256 before=usdc.balanceOf(owner);
            uint256 expected=(((i-1)%3)+1)*1e6;
            vm.prank(owner);assertEq(r.claim(i,address(usdc)),expected);
            assertEq(usdc.balanceOf(owner)-before,expected);paid+=expected;
        }
        assertEq(paid,totalWeight*1e6);assertEq(r.claimable(1000,address(usdc)),0);
        assertEq(r.liabilities(address(usdc)),0);assertEq(usdc.balanceOf(address(r)),0);
    }
}
