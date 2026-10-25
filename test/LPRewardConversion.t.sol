// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {MockFeed} from "./mocks/Mocks.sol";
import {ConversionAccess, ConversionToken, ConversionWrapper, ConversionVenue, ConversionReadProbe} from "./RoyaltyConversion.t.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZLPRewardConverter} from "../src/ZZZLPRewardConverter.sol";
import {ZZZRewardConverter} from "../src/base/ZZZRewardConverter.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

contract LPConversionNFT is ERC721 {
    uint256 public mintedCount;
    mapping(uint256=>uint256) public tokenAtOrdinal;
    constructor() ERC721("LP", "LP") {}
    function mint(address owner,uint256 id) external { _mint(owner,id); tokenAtOrdinal[++mintedCount]=id; }
}
contract LPConversionShares {
    mapping(uint256=>uint256) public sharesOf;
    mapping(uint256=>bool) public eligible;
    uint256 public totalEligible;
    uint256 public totalShares;
    function nftBucket(uint256) external pure returns(uint256) { return 1; }
    function bucketCount() external pure returns(uint256) { return 1; }
    function bucketAt(uint256 i) external pure returns(uint256) { require(i==0);return 1; }
    function bucketTotalShares(uint256) external view returns(uint256) { return totalShares; }
    function join(ZZZRewards r,uint256 id,uint256 shares) external {
        r.checkpointOwner(id); r.checkpointAll(id);
        if (!eligible[id]) { eligible[id]=true;totalEligible++; }
        sharesOf[id]+=shares;totalShares+=shares;
    }
}
contract RejectNative { receive() external payable { revert(); } function claim(ZZZRewards r,uint256 id) external {r.claim(id,address(0));} }

contract LPRewardConversionTest is Test {
    ConversionAccess a; LPConversionNFT nft; LPConversionShares shares;
    ZZZRewards r; ZZZLPRewardConverter c; ConversionWrapper w; ConversionToken t;
    ConversionVenue venue; ZZZOracle oracle; MockFeed sf; MockFeed ef; bytes32 routeId;
    address alice=address(0xa11ce); address bob=address(0xb0b); address carol=address(0xca701);
    function setUp() public {
        vm.warp(100000);a=new ConversionAccess();nft=new LPConversionNFT();shares=new LPConversionShares();
        r=new ZZZRewards(address(a));w=new ConversionWrapper();t=new ConversionToken();
        a.bind(Ids.NFT,address(nft));a.bind(Ids.VAULT,address(shares));a.bind(Ids.MEMBERSHIP,address(shares));
        a.bind(Ids.FEES,address(this));a.bind(Ids.REWARDS,address(r));a.bind(Ids.CANONICAL,address(this));a.setKeeper(address(this),true);
        r.addAsset(address(t));r.addAsset(address(w));
        oracle=new ZZZOracle(address(a),address(0));sf=new MockFeed(8,1e8);ef=new MockFeed(8,2000e8);
        oracle.setTestFeed(address(t),address(sf),3600);oracle.setTestFeed(address(w),address(ef),3600);a.bind(Ids.ORACLE,address(oracle));
        c=new ZZZLPRewardConverter(address(a),address(r),address(w));r.bindConverter(address(c));
        c.configureWrapper(ZZZRewardConverter.WrapperPolicy(address(w).codehash,address(0),address(0),address(0),0,0,bytes32(uint256(1))));
        c.setEnabled(true);venue=new ConversionVenue(address(t),w);
        routeId=c.addRoute(ZZZRewardConverter.RoutePolicy(address(t),address(venue),address(venue),address(venue),500,
            address(t).codehash,address(venue).codehash,address(venue).codehash,address(venue).codehash,bytes32(uint256(2))));
        a.seal();nft.mint(alice,1);nft.mint(bob,2);nft.mint(carol,3);
        shares.join(r,1,2e18);shares.join(r,2,1e18);vm.deal(address(w),1000 ether);vm.deal(address(this),100 ether);
    }
    function ids() internal pure returns(uint256[] memory list) {list=new uint256[](2);list[0]=1;list[1]=2;}
    function credit(uint256 personal,uint256 shared) internal {
        t.mint(address(this),personal+shared);t.approve(address(r),personal+shared);r.creditPool(1,address(t),personal,shared);
    }
    function convert(uint256 minimum) internal returns(uint256) {return r.convertBatch(address(t),ids(),routeId,minimum,block.timestamp+60);}
    function testEarnedOnlyConservationAndNoNewcomerRedistribution() public {
        credit(600e6,200e6);t.mint(address(r),77e6);vm.deal(address(r),9 ether);
        shares.join(r,3,100e18);assertEq(convert(1),0.4 ether);
        assertEq(r.claimable(1,address(0)),0.25 ether);assertEq(r.claimable(2,address(0)),0.15 ether);
        assertEq(r.individual(1,address(0)),0.2 ether);assertEq(r.collective(1,address(0)),0.05 ether);
        assertEq(r.claimable(3,address(0)),0);assertEq(r.claimable(3,address(t)),0);
        assertEq(r.liabilities(address(0)),0.4 ether);assertEq(t.balanceOf(address(r)),77e6);
        assertEq(address(r).balance,9.4 ether);assertEq(r.liabilities(address(t)),0);
        assertEq(t.allowance(address(r),address(c)),0);assertEq(t.allowance(address(c),address(venue)),0);
        vm.prank(alice);assertEq(r.claim(1,address(0)),0.25 ether);
        vm.prank(alice);assertEq(r.claim(1,address(0)),0);
    }
    function testTransferBeforeAndAfterConversionAndShareGrowth() public {
        credit(600e6,200e6);vm.prank(alice);nft.transferFrom(alice,carol,1);shares.join(r,2,20e18);convert(1);
        vm.prank(carol);nft.transferFrom(carol,bob,1);
        vm.prank(alice);vm.expectRevert();r.claim(1,address(0));
        vm.prank(bob);assertEq(r.claim(1,address(0)),0.25 ether);
    }
    function testOnePercentBoundaryAndAtomicRollback() public {
        credit(600e6,200e6);venue.settings(9899,false);vm.expectRevert();convert(1);
        assertEq(r.claimable(1,address(t)),500e6);assertEq(r.liabilities(address(t)),800e6);
        assertEq(t.balanceOf(address(r)),800e6);assertEq(t.allowance(address(r),address(c)),0);
        venue.settings(9900,false);assertEq(convert(1),0.396 ether);
    }
    function testStrongerMinimumAndLyingRouterRevert() public {
        credit(600e6,200e6);vm.expectRevert();convert(0.401 ether);
        venue.settings(10000,true);vm.expectRevert();convert(1);assertEq(r.claimable(1,address(t)),500e6);
    }
    function testSourceRecoveryDoesNotPayAgain() public {
        credit(600e6,200e6);c.setEnabled(false);vm.expectRevert();convert(1);
        vm.prank(alice);assertEq(r.claim(1,address(t)),500e6);c.setEnabled(true);
        assertEq(convert(1),0.15 ether);assertEq(r.claimable(1,address(0)),0);
    }
    function testExactUnwrapWithoutPriceAndFailureRecovery() public {
        w.mint(address(this),3 ether);w.approve(address(r),3 ether);r.creditPool(1,address(w),3 ether,0);
        vm.warp(block.timestamp+7200);w.setFail(true);vm.expectRevert();r.convertBatch(address(w),ids(),0,1,block.timestamp+60);
        assertEq(r.claimable(1,address(w)),2 ether);w.setFail(false);
        assertEq(r.convertBatch(address(w),ids(),0,3 ether,block.timestamp+60),3 ether);
        assertEq(r.claimable(1,address(0)),2 ether);
    }
    function testStaleOracleAndRouteDisableLeaveBalances() public {
        credit(600e6,200e6);c.setRouteEnabled(routeId,false);vm.expectRevert();convert(1);
        c.setRouteEnabled(routeId,true);vm.warp(block.timestamp+7200);vm.expectRevert();convert(1);
        assertEq(r.claimable(1,address(t)),500e6);
    }
    function testRolesLifecycleAndOriginalBinding() public {
        credit(600e6,200e6);vm.prank(alice);vm.expectRevert();convert(1);
        a.setPaused(true);vm.expectRevert();convert(1);a.setPaused(false);
        a.setPreparation(true);vm.expectRevert();convert(1);a.setPreparation(false);
        a.state(1);vm.expectRevert();convert(1);a.state(0);
        vm.expectRevert();r.bindConverter(address(c));
        a.bind(Ids.REWARDS,address(1));vm.expectRevert();convert(1);
    }
    function testCallbacksCannotPauseOrExposePartialBalances() public {
        credit(600e6,200e6);venue.setCallback(address(a),abi.encodeCall(a.setPaused,(true)));vm.expectRevert();convert(1);
        assertFalse(a.paused());ConversionReadProbe probe=new ConversionReadProbe();
        venue.setCallback(address(probe),abi.encodeCall(probe.query,(address(r))));convert(1);assertFalse(probe.readable());
    }
    function testInvalidBatchDeadlineAndNativeInput() public {
        credit(600e6,200e6);uint256[] memory list=ids();list[1]=1;vm.expectRevert();r.convertBatch(address(t),list,routeId,1,block.timestamp+60);
        list[1]=99;vm.expectRevert();r.convertBatch(address(t),list,routeId,1,block.timestamp+60);
        vm.expectRevert();r.convertBatch(address(t),ids(),routeId,1,block.timestamp-1);
        vm.expectRevert();r.convertBatch(address(0),ids(),0,1,block.timestamp+60);
        vm.expectRevert();r.creditPool(1,address(0),1,0);
    }
    function testNativeRecipientRevertRestoresLiabilityAndClaimsIgnorePause() public {
        credit(600e6,200e6);convert(1);RejectNative receiver=new RejectNative();vm.prank(alice);nft.transferFrom(alice,address(receiver),1);
        vm.expectRevert();receiver.claim(r,1);assertEq(r.claimable(1,address(0)),0.25 ether);
        a.setPaused(true);vm.prank(bob);assertEq(r.claim(2,address(0)),0.15 ether);
    }
    function testMaximumBatchConservesOutputWithinGasBudget() public {
        uint256[] memory list=new uint256[](32);
        for(uint256 i=1;i<=32;++i) {
            if(i>3)nft.mint(alice,i);
            if(i>2)shares.join(r,i,1e18);
            list[i-1]=i;
        }
        credit(600e6,200e6);
        uint256 beforeGas=gasleft();uint256 out=r.convertBatch(address(t),list,routeId,1,block.timestamp+60);
        assertLt(beforeGas-gasleft(),8_000_000);
        uint256 total;for(uint256 i=1;i<=32;++i)total+=r.claimable(i,address(0));
        assertEq(total,out);assertEq(r.liabilities(address(0)),out);
        uint256[] memory tooMany=new uint256[](33);
        vm.expectRevert();r.convertBatch(address(t),tooMany,routeId,1,block.timestamp+60);
    }
    function testFuzzOutputAndSourceFractionsConserved(uint96 personal,uint96 shared) public {
        vm.deal(address(w),1e12 ether); // Back the fuzz venue's largest synthetic output.
        uint256 p=bound(uint256(personal),1,1e16);uint256 s=bound(uint256(shared),1,1e16);credit(p,s);
        uint256 earned=r.claimable(1,address(t))+r.claimable(2,address(t));
        if (earned < 2000) return;
        uint256 out=convert(1);
        assertEq(r.claimable(1,address(0))+r.claimable(2,address(0)),out);
        assertEq(r.liabilities(address(t)),p+s-earned);assertEq(t.balanceOf(address(r)),p+s-earned);
        assertEq(r.claimable(1,address(t)),0);assertEq(r.claimable(2,address(t)),0);
        credit(6e6,2e6);assertGe(r.claimable(1,address(t)),5e6);
    }
    function imported() internal returns(ZZZRewards dest, ConversionAccess other) {
        credit(600e6,200e6);convert(1);credit(60e6,20e6);
        other=new ConversionAccess();other.bind(Ids.CANONICAL,address(this));other.bind(Ids.NFT,address(nft));
        other.bind(Ids.VAULT,address(shares));other.bind(Ids.MEMBERSHIP,address(shares));other.seal();
        dest=new ZZZRewards(address(other));vm.deal(address(dest),1 ether);
        a.state(1);r.canonicalCapture();other.state(2);
        for(uint256 row;row<r.canonicalCount();++row) dest.canonicalImport(row,r.canonicalExport(row));
    }
    function testCanonicalNativeBackingImportClaimsAndPrefunds() public {
        (ZZZRewards dest,ConversionAccess other)=imported();vm.expectRevert();dest.canonicalValidate();
        for(uint256 i;i<r.canonicalAssetCount();++i) {r.canonicalRelease(i,address(dest));dest.canonicalAccept(i,address(r));}
        dest.canonicalValidate();other.state(0);
        assertEq(address(dest).balance,1.4 ether);assertEq(dest.liabilities(address(0)),0.4 ether);
        assertEq(dest.claimable(1,address(t)),50e6);assertEq(dest.claimable(1,address(0)),0.25 ether);
        vm.prank(alice);assertEq(dest.claim(1,address(0)),0.25 ether);
    }
    function testCanonicalAbortReturnsETHAndSourceBacking() public {
        (ZZZRewards dest,ConversionAccess other)=imported();
        for(uint256 i;i<r.canonicalAssetCount();++i) {r.canonicalRelease(i,address(dest));dest.canonicalAccept(i,address(r));}
        other.state(4);
        for(uint256 i;i<r.canonicalAssetCount();++i) {dest.canonicalRelease(i,address(r));r.canonicalRestore(i,address(dest));}
        r.canonicalValidate();a.state(0);assertEq(r.claimable(1,address(0)),0.25 ether);assertEq(r.claimable(1,address(t)),50e6);
        assertEq(address(dest).balance,1 ether);
    }
}
