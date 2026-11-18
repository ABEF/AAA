// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReferenceExecutionContextTest} from "./ReferenceExecutionContext.t.sol";
import {FactualPermit,FactualToken} from "./LiquidityFactualChecks.t.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZExecutionOracle} from "../src/interfaces/IZZZExecutionOracle.sol";
import {IZZZOracle} from "../src/interfaces/IZZZ.sol";

/// @dev Same inherited storage/transfer behavior, deliberately different code.
contract PlacementDifferentRuntimeToken20261118 is FactualToken {
    function distinctRuntimeMarker() external pure returns(uint256){return 1;}
}

/// @dev Separately funded, explicitly owner-approved adversary. This is NOT a
/// claim that an unapproved trader can alter somebody else's position NFT.
contract PlacementLiquidityActor20261118 {
    PositionManager private immutable posm;
    FactualToken private immutable token;
    constructor(PositionManager p,FactualToken t,FactualPermit permit) {
        posm=p;token=t;t.approve(address(permit),type(uint256).max);
        permit.approve(address(t),address(p),type(uint160).max,type(uint48).max);
    }
    receive() external payable {}
    function increaseOne(uint256 id,uint256 nativeDebt) external {
        bytes[] memory params=new bytes[](2);
        params[0]=abi.encode(id,uint256(1),type(uint128).max,type(uint128).max,bytes(""));
        params[1]=abi.encode(address(0),address(token));
        posm.modifyLiquidities{value:nativeDebt}(abi.encode(hex"000d",params),block.timestamp+100);
    }
}

/// @notice NEW proof-boundary checks against actual installed v4 core/PosM.
/// MockAccess/admission, fixed ETH feeds, VRF and Permit2 are local seams.
/// These small funded transactions do not qualify maximum-state gas/markets.
contract ManagerPlacementProofReuse20261118Test is ReferenceExecutionContextTest {
    PlacementLiquidityActor20261118 private actor;
    uint256 private activePosition;
    uint256 private actorDebt;
    uint256 private rejectedPublicReads;

    function _newMain() private returns(uint256 id) {
        uint256 ethBefore=address(this).balance;uint256 zzzBefore=token.balanceOf(address(this));
        uint256 spent0;uint256 spent1;
        (id,spent0,spent1)=manager.mint{value:10 ether}(target,-2000,2000,10 ether,11 ether,1,block.timestamp+100);
        assertGt(spent0,0);assertGt(spent1,0);assertLt(spent1,11 ether,"actual refund is nonzero");
        assertEq(ethBefore-address(this).balance,spent0);assertEq(zzzBefore-token.balanceOf(address(this)),spent1);
        assertEq(positions.ownerOf(id),address(this));assertGt(positions.getPositionLiquidity(id),0);
        (int24 lo,int24 hi)=manager.ticks(id);assertEq(lo,-2000);assertEq(hi,2000);
        assertEq(manager.secondaryId(id),0);assertFalse(_execution().executionActive());_assertPrefunds();
        positions.approve(manager.positionOperator(),id);
    }
    function _positionState(uint256 id) private view returns(bytes32) {
        return keccak256(abi.encode(_snapshot(state,target),_snapshot(state,referencePool),
            _snapshot(independentState,independentPool),positions.getPositionLiquidity(id),positions.ownerOf(id),
            positions.getApproved(id),address(this).balance,token.balanceOf(address(this)),
            token.allowance(address(this),manager.positionOperator()),address(manager).balance,
            token.balanceOf(address(manager)),manager.positionOperator().balance,
            token.balanceOf(manager.positionOperator()),address(positions).balance));
    }
    function checkPublicRefundProof() external {
        require(msg.sender==address(token));++callbackCount;
        assertTrue(_execution().executionActive());
        ethFirst.rounds(2,2);
        (bool ok,bytes memory reason)=address(manager).staticcall(abi.encodeCall(manager.balanceContext,(target)));
        assertFalse(ok,"foreign public call must still authenticate current sources");
        assertEq(reason,abi.encodeWithSelector(ZZZModule.InvalidState.selector));++rejectedPublicReads;
        ethFirst.rounds(1,1);
    }
    function leaveFreshRoundInRefund() external {
        require(msg.sender==address(token));++callbackCount;
        assertTrue(_execution().executionActive());ethFirst.rounds(2,2);
    }
    function alterPhysicalLiquidityInRefund() external {
        require(msg.sender==address(token));++callbackCount;
        uint128 beforeL=positions.getPositionLiquidity(activePosition);
        actor.increaseOne(activePosition,actorDebt);
        assertEq(positions.getPositionLiquidity(activePosition),uint256(beforeL)+1,
            "separate owner-approved actor reached actual core mutation");
    }
    function testManagerMintKeepsFullProofBeforeMutablePortfolioWrite() public {
        vm.expectCall(address(oracle),abi.encodeCall(IZZZExecutionOracle.validateExecution,()),uint64(1));
        uint256 id=_newMain();assertGt(id,0);
    }
    function testManagerIncreasePublicRefundReadStillRejectsChangedSource() public {
        uint256 id=_newMain();uint128 oldL=positions.getPositionLiquidity(id);
        token.arm(manager.positionOperator(),3,address(this),abi.encodeCall(this.checkPublicRefundProof,()));
        vm.expectCall(address(oracle),abi.encodeCall(IZZZExecutionOracle.validateExecution,()),uint64(1));
        manager.increase{value:10 ether}(target,id,10 ether,11 ether,1,block.timestamp+100);
        assertEq(callbackCount,1);assertEq(rejectedPublicReads,1);assertEq(ethFirst.round(),1);
        assertGt(positions.getPositionLiquidity(id),oldL);assertFalse(token.armed());
        assertFalse(_execution().executionActive());_assertPrefunds();
    }
    function testManagerIncreaseRefundRoundMutationRollsBackAndHealthyRetryWorks() public {
        uint256 id=_newMain();bytes32 beforeState=_positionState(id);
        token.arm(manager.positionOperator(),3,address(this),abi.encodeCall(this.leaveFreshRoundInRefund,()));
        vm.expectCall(address(this),abi.encodeCall(this.leaveFreshRoundInRefund,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.increase{value:10 ether}(target,id,10 ether,11 ether,1,block.timestamp+100);
        assertEq(_positionState(id),beforeState);assertEq(ethFirst.round(),1);assertTrue(token.armed());
        assertFalse(_execution().executionActive());_assertPrefunds();
        token.arm(manager.positionOperator(),0,address(0),"");uint128 oldL=positions.getPositionLiquidity(id);
        manager.increase{value:10 ether}(target,id,10 ether,11 ether,1,block.timestamp+100);
        assertGt(positions.getPositionLiquidity(id),oldL);assertFalse(_execution().executionActive());_assertPrefunds();
    }
    function testManagerIncreaseLatePhysicalMutationRollsBackIndependentFunding() public {
        uint256 id=_newMain();activePosition=id;
        actor=new PlacementLiquidityActor20261118(positions,token,permit);
        vm.deal(address(actor),1 ether);token.mint(address(actor),1 ether);
        positions.setApprovalForAll(address(actor),true);
        (actorDebt,)=router.balanceMath().deploymentDebts(Q96,-2000,2000,1);
        assertGt(actorDebt,0);uint256 actorETH=address(actor).balance;uint256 actorZZZ=token.balanceOf(address(actor));
        bytes32 beforeState=_positionState(id);
        token.arm(manager.positionOperator(),3,address(this),abi.encodeCall(this.alterPhysicalLiquidityInRefund,()));
        vm.expectCall(address(this),abi.encodeCall(this.alterPhysicalLiquidityInRefund,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.increase{value:10 ether}(target,id,10 ether,11 ether,1,block.timestamp+100);
        assertEq(_positionState(id),beforeState);assertEq(address(actor).balance,actorETH);
        assertEq(token.balanceOf(address(actor)),actorZZZ);assertTrue(token.armed());
        assertFalse(_execution().executionActive());_assertPrefunds();
        token.arm(manager.positionOperator(),0,address(0),"");uint128 oldL=positions.getPositionLiquidity(id);
        manager.increase{value:10 ether}(target,id,10 ether,11 ether,1,block.timestamp+100);
        assertGt(positions.getPositionLiquidity(id),oldL);assertEq(address(actor).balance,actorETH);
        assertEq(token.balanceOf(address(actor)),actorZZZ);assertFalse(_execution().executionActive());
    }
    function testManagerEntrySourceFaultAndPricingPhaseGuardsRetainAtomicRights() public {
        _installProductionEntryGraph();address owner=address(0xB0B);
        ZZZContributionPricing pricing=oracle.contributionPricing();
        vm.expectRevert(ZZZContributionPricing.Unauthorized.selector);
        pricing.finish(1,100e18,0,0,0,100e18,0,uint32(300)|(uint32(300)<<16));
        vm.prank(address(vault.migrationBudget()));vm.expectRevert(ZZZContributionPricing.InvalidState.selector);
        pricing.finish(1,100e18,0,0,0,100e18,0,uint32(300)|(uint32(300)<<16));
        vm.deal(owner,1 ether);token.mint(owner,1000 ether);uint256 id=_mint(owner);
        vm.prank(owner);token.approve(address(entry),100 ether);
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(id,target,address(token),100 ether,1,block.timestamp+100,false);
        bytes32 policy=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();
        assertEq(entry.activationAssets().value(address(0xDEAD),0),0,"zero side never queries admission/price");
        entry.activationAssets().setAsset(address(token),false,address(token).codehash,REVIEW);
        bytes32 beforeAdmission=_entryAtomicState(owner,id);
        vm.prank(owner);vm.expectRevert(ZZZModule.InvalidConfiguration.selector);entry.executeReviewed(request,300,policy);
        assertEq(_entryAtomicState(owner,id),beforeAdmission);assertFalse(pricing.active());
        entry.activationAssets().setAsset(address(token),true,address(token).codehash,REVIEW);
        beforeAdmission=_entryAtomicState(owner,id);
        vm.mockCall(address(oracle),abi.encodeCall(IZZZOracle.tokenDecimals,(address(token))),abi.encode(uint8(6)));
        vm.prank(owner);vm.expectRevert(ZZZModule.InvalidConfiguration.selector);entry.executeReviewed(request,300,policy);
        assertEq(_entryAtomicState(owner,id),beforeAdmission);assertFalse(pricing.active());vm.clearMockedCalls();
        bytes memory originalCode=address(token).code;
        PlacementDifferentRuntimeToken20261118 changed=new PlacementDifferentRuntimeToken20261118();
        vm.etch(address(token),address(changed).code);
        beforeAdmission=_entryAtomicState(owner,id);
        vm.prank(owner);vm.expectRevert(ZZZModule.InvalidConfiguration.selector);entry.executeReviewed(request,300,policy);
        assertEq(_entryAtomicState(owner,id),beforeAdmission);assertFalse(pricing.active());vm.etch(address(token),originalCode);
        ZZZActivationEntry.Request memory tooSmall=ZZZActivationEntry.Request(
            id,target,address(token),1 ether,1,block.timestamp+100,false);
        beforeAdmission=_entryAtomicState(owner,id);
        vm.prank(owner);vm.expectRevert(ZZZModule.InvalidAmount.selector);entry.executeReviewed(tooSmall,300,policy);
        assertEq(_entryAtomicState(owner,id),beforeAdmission);assertFalse(pricing.active());
        bytes32 beforeState=_entryAtomicState(owner,id);
        // The exact approval reset is guaranteed even if the ratio leaves no
        // token refund; it follows actual PosM settlement inside the child.
        token.arm(manager.positionOperator(),2,address(this),abi.encodeCall(this.leaveFreshRoundInRefund,()));
        vm.expectCall(address(this),abi.encodeCall(this.leaveFreshRoundInRefund,()));
        vm.prank(owner);vm.expectRevert(ZZZModule.InvalidState.selector);entry.executeReviewed(request,300,policy);
        assertEq(_entryAtomicState(owner,id),beforeState);assertEq(ethFirst.round(),1);
        assertTrue(token.armed());assertFalse(pricing.active());assertFalse(_execution().executionActive());
        token.arm(manager.positionOperator(),0,address(0),"");
        vm.prank(owner);entry.executeReviewed(request,300,policy);
        assertEq(nft.ownerOf(id),owner);assertGt(vault.sharesOf(id),0);
        assertEq(membership.totalEligible(),1);assertEq(nft.royaltyRewards().totalWeight(),1);
        assertGt(positions.getPositionLiquidity(vault.group(vault.nftBucket(id)).lpTokenId),0);
        assertFalse(pricing.active());assertFalse(_execution().executionActive());_assertPrefunds();
    }
}
