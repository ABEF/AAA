// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {Test} from "forge-std/Test.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {ModifyLiquidityParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {ZZZRoyaltyConverter} from "../src/ZZZRoyaltyConverter.sol";
import {ZZZLPRewardConverter} from "../src/ZZZLPRewardConverter.sol";
import {ZZZV4RouteExecutor} from "../src/ZZZV4RouteExecutor.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {PoolKey,Ids} from "../src/libraries/ZZZTypes.sol";
import {ConversionAccess,ConversionNFT,ConversionWrapper,ConversionToken,ConversionVenue} from "./RoyaltyConversion.t.sol";
import {LPConversionShares} from "./LPRewardConversion.t.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";

/// @dev Real local Uniswap v4 core/state view and real conversion/ledger code.
/// Synthetic tokens, USD feeds, access, NFT issuance and LP-share fixtures do not
/// qualify a Robinhood venue, dependency address, oracle or marketplace flow.
contract TypedV4RewardsTest is Test {
    ConversionAccess private access;
    ConversionNFT private nft;
    ZZZRoyaltyRewards private royalties;
    ZZZRewards private rewards;
    ZZZRoyaltyConverter private converter;
    ZZZLPRewardConverter private lpConverter;
    LPConversionShares private shares;
    ZZZOracle private oracle;
    MockFeed private feed;
    MockToken private token;
    PoolManager private core;
    StateView private state;
    CoreKey private key;
    bytes32 private royaltyRoute;
    bytes32 private lpRoute;
    address private constant ALICE=address(0xA11CE);
    address private constant BOB=address(0xB0B);
    address private constant CAROL=address(0xCA701);
    ZZZRoyaltyConverter private callbackTarget;
    bool private callbackSucceeded;
    bytes4 private callbackError;
    event ConversionLossLimitChanged(uint16 previous,uint16 current);
    receive() external payable {
        if(address(callbackTarget)!=address(0)) {
            bytes memory returned;
            (callbackSucceeded,returned)=address(callbackTarget).call(
                abi.encodeCall(ZZZRoyaltyConverter.setConversionLossBps,(uint16(1000))));
            if(returned.length>=4)callbackError=bytes4(returned);
        }
    }

    function setUp() public {
        vm.warp(100000);vm.deal(address(this),1e30);
        access=new ConversionAccess();nft=new ConversionNFT(address(access));royalties=nft.royalties();
        token=new MockToken(18);nft.add(address(token));
        oracle=new ZZZOracle(address(access),address(0));feed=new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(feed),3600);oracle.setTestFeed(address(token),address(feed),3600);
        access.bind(Ids.NFT,address(nft));access.bind(Ids.ORACLE,address(oracle));access.setKeeper(address(this),true);
        shares=new LPConversionShares();rewards=new ZZZRewards(address(access));rewards.addAsset(address(token));
        access.bind(Ids.REWARDS,address(rewards));access.bind(Ids.VAULT,address(shares));
        access.bind(Ids.MEMBERSHIP,address(shares));access.bind(Ids.FEES,address(this));
        converter=new ZZZRoyaltyConverter(address(access),address(royalties),address(0));royalties.bindConverter(address(converter));
        lpConverter=new ZZZLPRewardConverter(address(access),address(rewards),address(0));rewards.bindConverter(address(lpConverter));
        converter.setEnabled(true);lpConverter.setEnabled(true);
        core=new PoolManager(address(this));state=new StateView(IPoolManager(address(core)));
        key=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),500,60,IHooks(address(0)));
        core.initialize(key,uint160(1<<96));core.unlock(abi.encode(uint256(1)));
        royaltyRoute=converter.addV4Route(_policy());lpRoute=lpConverter.addV4Route(_policy());
        access.seal();nft.mint(ALICE,1,0);nft.mint(BOB,2,1);nft.mint(CAROL,3,2);
        nft.activate(1);nft.activate(2);shares.join(rewards,1,2e18);shares.join(rewards,2,1e18);
    }
    function unlockCallback(bytes calldata) external returns(bytes memory) {
        require(msg.sender==address(core));
        (BalanceDelta delta,)=core.modifyLiquidity(key,ModifyLiquidityParams(-120,120,int256(1e28),bytes32(0)),bytes(""));
        uint256 nativeDebt=uint256(-int256(delta.amount0()));
        uint256 tokenDebt=uint256(-int256(delta.amount1()));
        core.settle{value:nativeDebt}();core.sync(key.currency1);
        token.mint(address(core),tokenDebt);core.settle();return bytes("");
    }
    function _policy() private view returns(ZZZV4RouteExecutor.Policy memory) {
        return ZZZV4RouteExecutor.Policy(address(token),address(0),
            PoolKey(address(0),address(token),500,60,address(0)),address(core),address(state),
            address(token).codehash,keccak256("ZZZ_NATIVE_ETH_V1"),address(core).codehash,address(state).codehash,keccak256("local actual v4 test"));
    }
    function _ids() private pure returns(uint256[] memory result) {result=new uint256[](2);result[0]=1;result[1]=2;}
    function _fundRoyalty(uint256 amount) private {token.mint(address(royalties),amount);}
    function _creditLP(uint256 personal,uint256 collective) private {
        token.mint(address(this),personal+collective);token.approve(address(rewards),personal+collective);
        rewards.creditPool(1,address(token),personal,collective);
    }
    function _royalty(uint256 minimum) private returns(uint256) {
        return royalties.convertBatch(address(token),_ids(),royaltyRoute,minimum,block.timestamp+60);
    }

    function testActualV4RoyaltyConversionPreservesNFTWeightsAndEveryPrefund() public {
        _fundRoyalty(600e18);nft.activate(3);
        token.mint(address(converter),7);token.mint(address(converter.v4Executor()),11);
        vm.deal(address(converter),13);vm.deal(address(converter.v4Executor()),17);
        uint256 output=_royalty(1);
        assertGe(output,594e18);assertEq(royalties.accrued(1,address(0)),output/3);
        assertEq(royalties.accrued(1,address(0))+royalties.accrued(2,address(0)),output);
        assertEq(royalties.claimable(3,address(0)),0);assertEq(royalties.liabilities(address(token)),0);
        assertEq(royalties.liabilities(address(0)),output);assertEq(royalties.accounted(address(0)),output);
        assertEq(address(royalties).balance,output);assertEq(token.balanceOf(address(converter)),7);
        assertEq(token.balanceOf(address(converter.v4Executor())),11);assertEq(address(converter).balance,13);
        assertEq(address(converter.v4Executor()).balance,17);
        assertEq(token.allowance(address(royalties),address(converter)),0);
        assertEq(token.allowance(address(converter),address(converter.v4Executor())),0);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,1);
        vm.prank(ALICE);vm.expectRevert();royalties.claim(1,address(0));
        uint256 beforeETH=BOB.balance;vm.prank(BOB);uint256 paid=royalties.claim(1,address(0));
        assertEq(BOB.balance,beforeETH+paid);assertEq(royalties.claimable(1,address(0)),0);
    }
    function testActualV4LPConversionPreservesIndividualCollectiveAndExistingETH() public {
        _creditLP(600e18,200e18);shares.join(rewards,3,100e18);
        rewards.creditPool{value:9e18}(1,address(0),6e18,3e18);
        uint256 before1=rewards.claimable(1,address(0));uint256 before2=rewards.claimable(2,address(0));
        uint256 before3=rewards.claimable(3,address(0));
        uint256 output=rewards.convertBatch(address(token),_ids(),lpRoute,1,block.timestamp+60);
        assertGe(output,792e18);assertEq(rewards.individual(1,address(0)),output/2);
        assertEq(rewards.collective(1,address(0)),output*5/8-output/2);
        assertEq(rewards.claimable(1,address(0))-before1+rewards.claimable(2,address(0))-before2,output);
        assertEq(rewards.claimable(3,address(0)),before3);
        assertEq(rewards.liabilities(address(0)),9e18+output);assertEq(rewards.liabilities(address(token)),0);
        assertEq(address(rewards).balance,9e18+output);assertEq(token.allowance(address(rewards),address(lpConverter)),0);
    }
    function testV4DoesNotRequireAnAvailableWrapperOrItsFeed() public {
        ConversionWrapper wrapper=new ConversionWrapper();wrapper.setFail(true);
        ZZZRoyaltyConverter separate=new ZZZRoyaltyConverter(address(access),address(this),address(wrapper));
        separate.setEnabled(true);bytes32 id=separate.addV4Route(_policy());
        token.mint(address(this),100e18);token.approve(address(separate),100e18);
        uint256 beforeETH=address(this).balance;
        assertGe(separate.convert(address(token),100e18,id,1,block.timestamp+60),99e18);
        assertGt(address(this).balance,beforeETH);assertEq(wrapper.totalSupply(),0);
        vm.expectRevert();separate.convert(address(wrapper),1,bytes32(0),1,block.timestamp+60);
    }
    function testNativeOnlyConverterRejectsV3AndUnexpectedETH() public {
        assertEq(converter.wrapper(),address(0));assertEq(converter.routeKind(royaltyRoute),2);
        assertTrue(converter.routeExists(royaltyRoute));assertTrue(converter.routeEnabled(royaltyRoute));
        vm.expectRevert();converter.route(royaltyRoute);
        (bool ok,)=address(converter).call{value:1}("");assertFalse(ok);
        vm.prank(address(converter.v4Executor()));(ok,)=address(converter).call{value:1}("");assertFalse(ok);
        _fundRoyalty(100e18);vm.expectRevert();royalties.convertBatch(address(token),_ids(),bytes32(0),1,block.timestamp+60);
    }
    function testStrongerMinimumAndStalePricesRevertWithAllRightsBacked() public {
        _fundRoyalty(600e18);royalties.sync(address(token));
        vm.expectRevert();_royalty(601e18);
        assertEq(token.balanceOf(address(royalties)),600e18);assertEq(royalties.claimable(1,address(token)),200e18);
        assertEq(royalties.claimable(2,address(token)),400e18);assertEq(royalties.liabilities(address(0)),0);
        vm.warp(block.timestamp+3601);vm.expectRevert();_royalty(1);
        assertEq(token.balanceOf(address(royalties)),600e18);assertEq(token.allowance(address(royalties),address(converter)),0);
    }
    function testOnePercentRoundedUpFloorCannotBeWeakenedByCaller() public {
        _fundRoyalty(600e18);uint256 snapshot=vm.snapshot();uint256 actual=_royalty(1);assertTrue(vm.revertTo(snapshot));
        uint256 expected=((actual+1)*10000+9899)/9900;
        vm.mockCall(address(oracle),abi.encodeCall(ZZZOracle.quote,(address(token),address(0),600e18)),abi.encode(expected));
        vm.expectRevert();_royalty(1);
        assertEq(token.balanceOf(address(royalties)),600e18);assertEq(royalties.liabilities(address(0)),0);
    }
    function testV4RoutesRejectWrongCurrencyAndGovernanceLifecycleChanges() public {
        ZZZV4RouteExecutor.Policy memory p=_policy();p.source=address(0);vm.expectRevert();converter.addV4Route(p);
        p=_policy();p.output=address(token);vm.expectRevert();converter.addV4Route(p);
        vm.prank(ALICE);vm.expectRevert();converter.setRouteEnabled(royaltyRoute,false);
        access.state(1);vm.expectRevert();converter.setEnabled(false);
        vm.expectRevert();converter.setRouteEnabled(royaltyRoute,false);access.state(0);
        access.setPaused(true);converter.setRouteEnabled(royaltyRoute,false);assertFalse(converter.routeEnabled(royaltyRoute));
        access.setPaused(false);_fundRoyalty(600e18);vm.expectRevert();_royalty(1);
        converter.setRouteEnabled(royaltyRoute,true);assertGt(_royalty(1),0);
    }
    function testConversionLossPolicyDefaultsBoundsAndImmediateEvents() public {
        assertEq(converter.conversionLossBps(),100);assertEq(converter.MAX_LOSS_BPS(),1000);
        vm.expectEmit(false,false,false,true,address(converter));emit ConversionLossLimitChanged(100,250);
        converter.setConversionLossBps(250);assertEq(converter.conversionLossBps(),250);
        vm.expectRevert();converter.setConversionLossBps(1001);assertEq(converter.conversionLossBps(),250);
        converter.setConversionLossBps(1000);assertEq(converter.conversionLossBps(),1000);
    }
    function testConversionLossPolicyAuthorityPauseAndCanonicalBoundaries() public {
        vm.prank(ALICE);vm.expectRevert();converter.setConversionLossBps(500);
        access.setPaused(true);converter.setConversionLossBps(0);assertEq(converter.conversionLossBps(),0);
        access.setPaused(false);access.setPreparation(true);vm.expectRevert();converter.setConversionLossBps(500);
        access.setPreparation(false);
        for(uint8 s=1;s<=4;++s){access.state(s);vm.expectRevert();converter.setConversionLossBps(500);}
        access.state(0);converter.setConversionLossBps(100);assertEq(converter.conversionLossBps(),100);
    }
    function testChangedCapEnforcesCurrentCeilFloorAndStillHonorsStrongerMinimum() public {
        _fundRoyalty(600e18);uint256 snapshot=vm.snapshot();uint256 actual=_royalty(1);assertTrue(vm.revertTo(snapshot));
        vm.mockCall(address(oracle),abi.encodeCall(ZZZOracle.quote,(address(token),address(0),600e18)),abi.encode(actual*102/100));
        vm.expectRevert();_royalty(1);assertEq(token.balanceOf(address(royalties)),600e18);
        converter.setConversionLossBps(300);vm.expectRevert();_royalty(actual+1);
        assertEq(token.balanceOf(address(royalties)),600e18);assertEq(_royalty(1),actual);
    }
    function testZeroLossPolicyRequiresFullReferenceValue() public {
        _fundRoyalty(600e18);converter.setConversionLossBps(0);vm.expectRevert();_royalty(1);
        assertEq(token.balanceOf(address(royalties)),600e18);
        converter.setConversionLossBps(1000);assertGt(_royalty(1),0);
    }
    function testAuthorizedGovernanceCallbackCannotChangeCapDuringNativePayout() public {
        ZZZRoyaltyConverter separate=new ZZZRoyaltyConverter(address(access),address(this),address(0));
        separate.setEnabled(true);bytes32 routeId=separate.addV4Route(_policy());
        token.mint(address(this),100e18);token.approve(address(separate),100e18);callbackTarget=separate;
        assertGt(separate.convert(address(token),100e18,routeId,1,block.timestamp+60),0);
        assertFalse(callbackSucceeded);assertEq(callbackError,bytes4(keccak256("ReentrancyGuardReentrantCall()")));
        assertEq(separate.conversionLossBps(),100);
    }
    function testLegacyV3RouteUsesCurrentCapAndExactUnwrapWhilePreservingABI() public {
        ConversionToken stable=new ConversionToken();ConversionWrapper wrapper=new ConversionWrapper();
        oracle.setTestFeed(address(stable),address(new MockFeed(8,1e8)),3600);
        oracle.setTestFeed(address(wrapper),address(new MockFeed(8,2000e8)),3600);
        ZZZRoyaltyConverter separate=new ZZZRoyaltyConverter(address(access),address(this),address(wrapper));
        separate.configureWrapper(ZZZRoyaltyConverter.WrapperPolicy(address(wrapper).codehash,address(0),address(0),address(0),0,0,keccak256("wrapper fixture")));
        separate.setEnabled(true);ConversionVenue venue=new ConversionVenue(address(stable),wrapper);
        bytes32 id=separate.addRoute(ZZZRoyaltyConverter.RoutePolicy(address(stable),address(venue),address(venue),address(venue),500,
            address(stable).codehash,address(venue).codehash,address(venue).codehash,address(venue).codehash,keccak256("v3 fixture")));
        assertEq(separate.routeKind(id),1);assertEq(separate.route(id).source,address(stable));
        stable.mint(address(this),300e6);stable.approve(address(separate),300e6);vm.deal(address(wrapper),1 ether);
        venue.settings(9800,false);vm.expectRevert();separate.convert(address(stable),300e6,id,1,block.timestamp+60);
        assertEq(stable.balanceOf(address(this)),300e6);separate.setConversionLossBps(300);
        vm.expectRevert();separate.convert(address(stable),300e6,id,0.147 ether+1,block.timestamp+60);
        assertEq(separate.convert(address(stable),300e6,id,1,block.timestamp+60),0.147 ether);
        assertEq(stable.allowance(address(separate),address(venue)),0);assertEq(wrapper.balanceOf(address(separate)),0);
    }
}
