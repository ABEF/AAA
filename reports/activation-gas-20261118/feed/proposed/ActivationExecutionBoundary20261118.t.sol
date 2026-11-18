// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ReferenceExecutionContextTest,ContextExternalTrader} from "./ReferenceExecutionContext.t.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";

/// @notice One NEW composite actual-v4 regression for the changed Oracle/feed
/// source. It does not call old test methods or qualify maximum-state Entry gas.
/// MockAccess, MockFeed/Permit2 and the adversarial token are explicit seams.
contract ActivationExecutionBoundary20261118Test is ReferenceExecutionContextTest {
    ContextExternalTrader private primaryTrader;
    uint8 private attack;

    function mutateBoundary20261118() external {
        require(msg.sender==address(token));
        assertTrue(_execution().executionActive(),"callback reaches active source scope");
        ++callbackCount;
        if(attack==0) ethFirst.rounds(2,2);
        else if(attack==1) {
            // This fixture deliberately authorizes the governance actor. This
            // is not a claim that an unapproved wallet can change source kind.
            oracle.setExecutionSource(address(referenceFeed),false,address(referenceFeed).codehash,REVIEW);
            oracle.setExecutionSource(address(referenceFeed),true,address(referenceFeed).codehash,REVIEW);
        } else if(attack==2) callbackTrader.swapTokenForETH(1 ether);
        else if(attack==3) {
            ZZZProtocolPolicy policy=ZZZProtocolPolicy(access.protocolPolicy());
            policy.setGasPolicy(policy.payoutGas(),policy.sourceCallGas(),policy.royaltySyncGas(),REVIEW);
        } else primaryTrader.swapTokenForETH(1 ether);

        if(attack==1 || attack==3) {
            (bool ok,)=address(oracle).staticcall(abi.encodeCall(_execution().executionBounds,(address(token))));
            assertFalse(ok,"changed monotonic controls invalidate cheap reads too");
        } else {
            // A cheap captured read may remain readable after unapproved
            // market/round movement, but it cannot authorize a commit.
            (uint256 lo,uint256 hi,bytes32 fingerprint)=_execution().executionBounds(address(token));
            assertEq(lo,callbackExpectedPrice.lower);assertEq(hi,callbackExpectedPrice.upper);
            assertEq(fingerprint,callbackExpectedPrice.fingerprint);
        }
    }

    function _boundaryState20261118() private view returns(bytes32) {
        bytes32 markets=keccak256(abi.encode(_snapshot(state,target),_snapshot(state,referencePool),
            _snapshot(independentState,independentPool),core.protocolFeesAccrued(Currency.wrap(address(0))),
            core.protocolFeesAccrued(Currency.wrap(address(token))),
            independentCore.protocolFeesAccrued(Currency.wrap(address(0))),
            independentCore.protocolFeesAccrued(Currency.wrap(address(token)))));
        bytes32 balances=keccak256(abi.encode(address(this).balance,token.balanceOf(address(this)),
            token.allowance(address(this),address(manager)),address(manager).balance,token.balanceOf(address(manager)),
            address(core).balance,token.balanceOf(address(core)),address(independentCore).balance,
            token.balanceOf(address(independentCore)),address(primaryTrader).balance,token.balanceOf(address(primaryTrader)),
            address(callbackTrader).balance,token.balanceOf(address(callbackTrader))));
        return keccak256(abi.encode(markets,balances,ethFirst.round(),ethFirst.answeredRound(),
            ethSecond.round(),ethSecond.answeredRound(),oracle.executionSourceRevision(),
            ZZZProtocolPolicy(access.protocolPolicy()).gasFingerprint(),callbackCount));
    }

    function _healthyRetry20261118(bool direction) private {
        uint256 a0=direction?100 ether:1 ether;uint256 a1=direction?1 ether:100 ether;
        ZZZLPBalancer.Plan memory plan=_plan(a0,a1);
        assertEq(plan.poolId,referencePool);assertEq(plan.zeroForOne,direction);assertGt(plan.amountIn,0);
        (uint256 lo,uint256 hi,bytes32 fingerprint)=oracle.priceBounds(address(token));
        bytes32 independentBefore=_snapshot(independentState,independentPool);
        bytes32 mainBefore=_snapshot(state,target);
        uint256 ethBefore=address(this).balance;uint256 zzzBefore=token.balanceOf(address(this));
        token.arm(address(manager),3,address(this),abi.encodeCall(this.observeRefund,()));
        (uint256 out0,uint256 out1)=manager.balance{value:a0}(target,0,a0,a1,block.timestamp+100);
        assertEq(callbackCount,1);assertTrue(callbackSeen);assertFalse(token.armed());
        assertEq(callbackExecutionLower,lo);assertEq(callbackExecutionUpper,hi);
        assertEq(callbackExecutionFingerprint,fingerprint);assertTrue(callbackLiveFingerprint!=fingerprint);
        assertEq(_snapshot(state,target),mainBefore);assertEq(_snapshot(independentState,independentPool),independentBefore);
        assertEq(keccak256(abi.encode(_market(state,referencePool))),keccak256(abi.encode(plan.afterState)));
        if(direction) {
            assertEq(out0,a0-plan.amountIn);assertEq(out1,a1+plan.amountOut);
            assertEq(ethBefore-address(this).balance,plan.amountIn);assertEq(token.balanceOf(address(this))-zzzBefore,plan.amountOut);
        } else {
            assertEq(out0,a0+plan.amountOut);assertEq(out1,a1-plan.amountIn);
            assertEq(address(this).balance-ethBefore,plan.amountOut);assertEq(zzzBefore-token.balanceOf(address(this)),plan.amountIn);
        }
        assertFalse(_execution().executionActive());_assertPrefunds();
    }

    function testExecutionBoundaryRejectionsRollbackThenBothReferenceDirectionsRetry20261118() public {
        primaryTrader=new ContextExternalTrader(core,referenceKey);
        callbackTrader=new ContextExternalTrader(independentCore,independentKey);
        token.mint(address(primaryTrader),10 ether);token.mint(address(callbackTrader),10 ether);
        for(uint256 side;side<2;++side) {
            bool direction=side==0;uint256 a0=direction?100 ether:1 ether;uint256 a1=direction?1 ether:100 ether;
            callbackCount=0;callbackSeen=false;
            for(uint8 kind;kind<5;++kind) {
                attack=kind;callbackExpectedPrice=_priceCapture(address(token));
                token.arm(address(manager),3,address(this),abi.encodeCall(this.mutateBoundary20261118,()));
                bytes32 beforeState=_boundaryState20261118();
                vm.expectCall(address(this),abi.encodeCall(this.mutateBoundary20261118,()));
                vm.expectRevert(ZZZModule.InvalidState.selector);
                manager.balance{value:a0}(target,0,a0,a1,block.timestamp+100);
                assertEq(_boundaryState20261118(),beforeState,"all market/funding/policy/round writes roll back");
                assertTrue(token.armed(),"callback disarm rolls back with failed operation");
                assertFalse(_execution().executionActive(),"no failed frame leaves a borrowed/owned context");
                _assertPrefunds();
            }
            _healthyRetry20261118(direction);
        }
    }
}
