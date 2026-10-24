// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZRoyaltyConverter} from "../src/ZZZRoyaltyConverter.sol";
import {IActivationV3Router} from "../src/ZZZActivationEntry.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

contract ConversionAccess is MockAccess { function state(uint8 s) external { canonicalState = s; } }
contract ConversionNFT is ERC721 {
    ZZZRoyaltyRewards public royalties;
    uint256 public mintedCount;
    mapping(uint256 => uint256) public tokenAtOrdinal;
    mapping(uint256 => uint8) public rarityOf;
    constructor(address control) ERC721("Test", "T") {
        royalties = new ZZZRoyaltyRewards(address(this)); royalties.bindCanonicalController(control);
    }
    function mint(address owner, uint256 id, uint8 rarity) external {
        _mint(owner,id); tokenAtOrdinal[++mintedCount] = id; rarityOf[id] = rarity;
    }
    function activate(uint256 id) external { royalties.activate(id, uint256(rarityOf[id])+1); }
    function add(address token) external { royalties.addAsset(token); }
}
contract ConversionWrapper is MockToken {
    bool public fail;
    constructor() MockToken(18) {}
    function setFail(bool v) external { fail = v; }
    function withdraw(uint256 n) external {
        require(!fail); _burn(msg.sender,n); (bool ok,) = msg.sender.call{value:n}(""); require(ok);
    }
    receive() external payable {}
}
contract ConversionToken is MockToken {
    uint8 public fault;
    constructor() MockToken(6) {}
    function setFault(uint8 v) external { fault = v; }
    function balanceOf(address a) public view override returns(uint256) {
        if (fault == 1) revert("unavailable");
        if (fault == 2) { assembly { invalid() } }
        return super.balanceOf(a);
    }
}
contract ConversionVenue {
    address public immutable factory = address(this);
    address public immutable token0;
    address public immutable token1;
    address public immutable source;
    ConversionWrapper public immutable wrapped;
    uint24 public constant fee = 500;
    uint256 public bps = 10000;
    bool public lie;
    address public callback; bytes public callbackData;
    constructor(address token, ConversionWrapper w) {
        source=token; wrapped=w; token0=token<address(w)?token:address(w); token1=token<address(w)?address(w):token;
    }
    function getPool(address a,address b,uint24 f) external view returns(address) {
        return ((a==token0&&b==token1)||(a==token1&&b==token0))&&f==fee ? address(this):address(0);
    }
    function settings(uint256 b,bool l) external { bps=b; lie=l; }
    function setCallback(address a,bytes calldata d) external {callback=a;callbackData=d;}
    function exactInputSingle(IActivationV3Router.ExactInputSingleParams calldata p) external payable returns(uint256 out) {
        require(p.tokenIn==source&&p.tokenOut==address(wrapped)&&p.fee==fee);
        IERC20(source).transferFrom(msg.sender,address(this),p.amountIn);
        out = p.amountIn * 1e12 / 2000 * bps / 10000;
        // Deliberately ignores minOut: the converter must enforce it independently.
        wrapped.mint(p.recipient,out);
        if(callback!=address(0)){(bool ok,)=callback.call(callbackData);require(ok);}
        return lie ? out+1 : out;
    }
}
contract ConversionReadProbe {
    bool public readable;
    function query(address ledger) external {
        (readable,) = ledger.staticcall(abi.encodeCall(ZZZRoyaltyRewards.claimable,(1,address(0))));
    }
}

contract RoyaltyConversionTest is Test {
    ConversionAccess a; ConversionNFT nft; ZZZRoyaltyRewards r; ZZZRoyaltyConverter c;
    ConversionWrapper w; ConversionToken t; ConversionVenue venue; ZZZOracle oracle;
    MockFeed sf; MockFeed ef; bytes32 routeId;
    address alice=address(0xa11ce); address bob=address(0xb0b); address carol=address(0xca701);
    function setUp() public {
        vm.warp(100000); a=new ConversionAccess(); nft=new ConversionNFT(address(a)); r=nft.royalties();
        w=new ConversionWrapper();t=new ConversionToken();nft.add(address(w));nft.add(address(t));
        oracle=new ZZZOracle(address(a),address(0)); sf=new MockFeed(8,1e8);ef=new MockFeed(8,2000e8);
        oracle.setTestFeed(address(t),address(sf),3600);oracle.setTestFeed(address(w),address(ef),3600);
        a.bind(Ids.ORACLE,address(oracle));a.bind(Ids.NFT,address(nft));a.bind(Ids.CANONICAL,address(this));
        a.setKeeper(address(this),true);
        c=new ZZZRoyaltyConverter(address(a),address(r),address(w)); r.bindConverter(address(c));
        c.configureWrapper(ZZZRoyaltyConverter.WrapperPolicy(address(w).codehash,address(0),address(0),address(0),0,0,bytes32(uint256(1))));
        c.setEnabled(true);venue=new ConversionVenue(address(t),w);
        routeId=c.addRoute(ZZZRoyaltyConverter.RoutePolicy(address(t),address(venue),address(venue),address(venue),500,
            address(t).codehash,address(venue).codehash,address(venue).codehash,address(venue).codehash,bytes32(uint256(2))));
        a.seal();nft.mint(alice,1,0);nft.mint(bob,2,1);nft.mint(carol,3,2);
        nft.activate(1);nft.activate(2);vm.deal(address(w),1000 ether);vm.deal(address(this),100 ether);
    }
    function ids() internal pure returns(uint256[] memory list){list=new uint256[](2);list[0]=1;list[1]=2;}
    function convert(uint256 minimum) internal returns(uint256){return r.convertBatch(address(t),ids(),routeId,minimum,block.timestamp+60);}
    function pay(uint256 n) internal {(bool ok,)=address(r).call{value:n}("");assertTrue(ok);}

    function testBatchConvertsOnlyEarnedBalancesAndKeepsNativeEntitlement() public {
        pay(3 ether); t.mint(address(r),600e6); nft.activate(3);
        assertEq(convert(0.297 ether),0.3 ether);
        assertEq(r.claimable(1,address(0)),1.1 ether);assertEq(r.claimable(2,address(0)),2.2 ether);
        assertEq(r.claimable(3,address(0)),0);assertEq(r.claimable(3,address(t)),0);
        assertEq(r.liabilities(address(t)),0);assertEq(r.accounted(address(0)),3.3 ether);
        assertEq(t.allowance(address(r),address(c)),0);assertEq(t.allowance(address(c),address(venue)),0);
        vm.prank(alice);assertEq(r.claim(1,address(0)),1.1 ether);
        vm.prank(bob);assertEq(r.claim(2,address(0)),2.2 ether);
    }
    function testTransferBeforeAndAfterConversionPreservesRights() public {
        t.mint(address(r),600e6);vm.prank(alice);nft.transferFrom(alice,carol,1);
        convert(1);vm.prank(carol);nft.transferFrom(carol,bob,1);
        vm.prank(alice);vm.expectRevert();r.claim(1,address(0));
        vm.prank(bob);assertEq(r.claim(1,address(0)),0.1 ether);
    }
    function testLossOverOnePercentRollsBackEverythingAndRetryWorks() public {
        t.mint(address(r),600e6);venue.settings(9899,false);
        vm.expectRevert();convert(1);
        assertEq(r.claimable(1,address(t)),200e6);assertEq(t.balanceOf(address(r)),600e6);
        assertEq(t.allowance(address(r),address(c)),0);assertEq(r.claimable(1,address(0)),0);
        venue.settings(9900,false);assertEq(convert(1),0.297 ether);
    }
    function testUserMinimumCannotBeRelaxedAndRouterReturnIsMeasured() public {
        t.mint(address(r),600e6);vm.expectRevert();convert(0.31 ether);
        venue.settings(10000,true);vm.expectRevert();convert(1);
        assertEq(t.balanceOf(address(r)),600e6);
    }
    function testExactUnwrapNoSwapOrOracle() public {
        w.mint(address(r),3 ether);vm.warp(block.timestamp+7200);
        assertEq(r.convertBatch(address(w),ids(),0,3 ether,block.timestamp+60),3 ether);
        assertEq(r.claimable(1,address(0)),1 ether);assertEq(r.claimable(2,address(0)),2 ether);
    }
    function testWrapperFailureDoesNotBlockActivationOrNativeClaims() public {
        w.mint(address(r),3 ether);w.setFail(true);vm.expectRevert();r.convertBatch(address(w),ids(),0,1,block.timestamp+60);
        nft.activate(3);pay(6 ether);vm.prank(carol);assertEq(r.claim(3,address(0)),3 ether);
        w.setFail(false);r.convertBatch(address(w),ids(),0,1,block.timestamp+60);assertEq(r.claimable(3,address(0)),0);
    }
    function testBadTokenActivationRecoveryExcludesOlderReceipts() public {
        t.mint(address(r),600e6);t.setFault(1);nft.activate(3);
        assertEq(r.weightOf(3),3);assertFalse(r.eligibleFor(3,address(t)));assertTrue(r.eligibleFor(3,address(0)));
        pay(6 ether);assertEq(r.claimable(3,address(0)),3 ether);
        t.mint(address(r),300e6);t.setFault(0);r.sync(address(t));
        assertTrue(r.eligibleFor(3,address(t)));assertEq(r.claimable(3,address(t)),0);
        assertEq(r.claimable(1,address(t)),300e6);assertEq(r.claimable(2,address(t)),600e6);
        t.mint(address(r),600e6);assertEq(r.claimable(3,address(t)),300e6);
        convert(1);assertEq(r.claimable(3,address(t)),300e6);
    }
    function testGasBurningOptionalTokenCannotBlockActivation() public {
        t.setFault(2);nft.activate(3);assertEq(r.weightOf(3),3);assertFalse(r.eligibleFor(3,address(t)));
        vm.expectRevert();r.syncForActivation(address(t));
    }
    function testRepeatedOutagesJoinAtDifferentBaselines() public {
        t.setFault(1);nft.activate(3);t.mint(address(r),300e6);t.setFault(0);r.sync(address(t));
        nft.mint(alice,4,0);t.setFault(1);nft.activate(4);t.mint(address(r),600e6);t.setFault(0);r.sync(address(t));
        assertEq(r.claimable(1,address(t)),200e6);assertEq(r.claimable(2,address(t)),400e6);
        assertEq(r.claimable(3,address(t)),300e6);assertEq(r.claimable(4,address(t)),0);
        t.mint(address(r),700e6);assertEq(r.claimable(4,address(t)),100e6);
    }
    function testNoOldEligibleMembersRecoveryQuarantinesReceipts() public {
        ConversionNFT other=new ConversionNFT(address(a));ZZZRoyaltyRewards rr=other.royalties();other.add(address(t));
        t.setFault(1);other.mint(alice,9,0);other.activate(9);t.mint(address(rr),100e6);t.setFault(0);rr.sync(address(t));
        assertEq(rr.orphaned(address(t)),100e6);assertEq(rr.claimable(9,address(t)),0);
        t.mint(address(rr),10e6);assertEq(rr.claimable(9,address(t)),10e6);
    }
    function testDisabledRouteAndConverterStopWithoutDependencyReads() public {
        t.mint(address(r),300e6);vm.etch(address(venue),hex"00");
        c.setRouteEnabled(routeId,false);c.setEnabled(false);vm.expectRevert();convert(1);
        vm.expectRevert();c.setRouteEnabled(routeId,true);
    }
    function testStaleOracleRejectsWithoutConsumingRights() public {
        t.mint(address(r),300e6);vm.warp(block.timestamp+3601);vm.expectRevert();convert(1);
        assertEq(r.claimable(1,address(t)),100e6);
    }
    function testDeadlineRoleBindingAndDuplicateGuards() public {
        t.mint(address(r),300e6);vm.prank(bob);vm.expectRevert();convert(1);
        vm.expectRevert();r.convertBatch(address(t),ids(),routeId,1,block.timestamp-1);
        uint256[] memory dup=ids();dup[1]=1;vm.expectRevert();r.convertBatch(address(t),dup,routeId,1,block.timestamp+60);
        vm.expectRevert();r.bindConverter(address(c));vm.expectRevert();c.convert(address(t),1,routeId,1,block.timestamp+60);
    }
    function testPausePreparationAndCanonicalStopConversionsButNotNativeClaims() public {
        t.mint(address(r),300e6);pay(3 ether);
        a.setPaused(true);vm.expectRevert();convert(1);vm.prank(alice);assertEq(r.claim(1,address(0)),1 ether);
        a.setPaused(false);a.setPreparation(true);vm.expectRevert();convert(1);a.setPreparation(false);
        a.state(1);vm.expectRevert();convert(1);
    }
    function testCallbackPauseRollsBackConversion() public {
        t.mint(address(r),300e6);venue.setCallback(address(a),abi.encodeCall(a.setPaused,(true)));
        vm.expectRevert();convert(1);assertFalse(a.paused());assertEq(t.balanceOf(address(r)),300e6);
    }
    function testCanonicalExportFlattensRecoveryBaseline() public {
        t.mint(address(r),300e6);t.setFault(1);nft.activate(3);t.setFault(0);
        a.state(1);r.canonicalCapture();r.canonicalSettle();
        // header + three assets + two NFT records of four rows + weight/native/WETH/token
        (uint256 id,address token,uint256 amount,uint256 paid,uint256 frac)=abi.decode(r.canonicalExport(15),(uint256,address,uint256,uint256,uint256));
        assertEq(id,3);assertEq(token,address(t));assertEq(amount,0);assertEq(paid,r.index(address(t)));assertEq(frac,0);
        a.state(0);assertEq(r.claimable(3,address(t)),0);
    }
    function testPartialBatchDoesNotConvertOtherNFTOrQuarantinedBalance() public {
        t.mint(address(r),600e6);uint256[] memory one=new uint256[](1);one[0]=1;
        r.convertBatch(address(t),one,routeId,1,block.timestamp+60);
        assertEq(r.claimable(1,address(0)),0.1 ether);assertEq(r.claimable(2,address(0)),0);
        assertEq(r.claimable(2,address(t)),400e6);assertEq(t.balanceOf(address(r)),400e6);
        vm.prank(bob);assertEq(r.claim(2,address(t)),400e6);
        vm.expectRevert();convert(1);
    }
    function testCallbackReentryCannotClaimOrDuplicateConversion() public {
        t.mint(address(r),300e6);venue.setCallback(address(r),abi.encodeCall(r.convertBatch,(address(t),ids(),routeId,1,block.timestamp+60)));
        vm.expectRevert();convert(1);assertEq(r.claimable(1,address(t)),100e6);
    }
    function testReadOnlyCallbacksCannotObserveIntermediateClaimableBalances() public {
        ConversionReadProbe probe=new ConversionReadProbe();t.mint(address(r),300e6);
        venue.setCallback(address(probe),abi.encodeCall(probe.query,(address(r))));
        convert(1);assertFalse(probe.readable());assertEq(r.claimable(1,address(0)),0.05 ether);
    }
    function testBoundedBatchAndFullNativeAllocation() public {
        uint256[] memory list=new uint256[](32);
        for(uint256 i=0;i<32;++i){uint256 id=i+10;nft.mint(alice,id,0);nft.activate(id);list[i]=id;}
        t.mint(address(r),350e6);uint256 output=r.convertBatch(address(t),list,routeId,1,block.timestamp+60);
        uint256 sum;for(uint256 i=0;i<32;++i)sum+=r.accrued(list[i],address(0));assertEq(sum,output);
        uint256[] memory tooMany=new uint256[](33);vm.expectRevert();r.convertBatch(address(t),tooMany,routeId,1,block.timestamp+60);
    }
    function testConvertedAndDeferredRightsSurviveCanonicalImport() public {
        t.mint(address(r),600e6);t.setFault(1);nft.activate(3);t.setFault(0);convert(1);
        t.mint(address(r),600e6);a.state(1);r.canonicalCapture();r.canonicalSettle();
        ConversionAccess destination=new ConversionAccess();destination.bind(Ids.CANONICAL,address(this));
        ConversionNFT successor=new ConversionNFT(address(destination));ZZZRoyaltyRewards rr=successor.royalties();
        successor.mint(alice,1,0);successor.mint(bob,2,1);successor.mint(carol,3,2);
        destination.state(2);
        for(uint256 row;row<r.canonicalCount();++row)rr.canonicalImport(row,r.canonicalExport(row));
        for(uint256 slot;slot<r.canonicalAssetCount();++slot){r.canonicalRelease(slot,address(rr));rr.canonicalAccept(slot,address(r));}
        rr.canonicalValidate();rr.canonicalActivate();destination.state(0);a.state(3);
        assertEq(rr.claimable(1,address(0)),0.1 ether);assertEq(rr.claimable(2,address(0)),0.2 ether);
        assertEq(rr.claimable(3,address(t)),300e6);assertTrue(rr.eligibleFor(3,address(t)));
        vm.prank(carol);assertEq(rr.claim(3,address(t)),300e6);
    }
    function testFuzzBatchConservation(uint96 units) public {
        uint256 n=bound(uint256(units),3,1e12);t.mint(address(r),n);
        uint256 first=r.claimable(1,address(t));uint256 second=r.claimable(2,address(t));
        uint256 out=convert(1);assertEq(r.accrued(1,address(0))+r.accrued(2,address(0)),out);
        assertEq(t.balanceOf(address(r)),n-first-second);assertEq(r.liabilities(address(0)),out);
    }
}
