// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ExactLPAllocation} from "../src/libraries/ExactLPAllocation.sol";
import {ExactLPAllocationBaseline} from "./helpers/ExactLPAllocationBaseline.sol";

/// @dev TEST ONLY, unfunded and unauthenticated. This is not a Rewards ledger,
/// token receiver, NFT registry, canonical importer or deployment component.
contract ExactLPAllocationHarness {
    using ExactLPAllocation for ExactLPAllocation.Tree;
    ExactLPAllocation.Tree private tree;
    function setWeight(uint256 ordinal,uint256 weight) external returns(uint256){return tree.setWeight(ordinal,weight);}
    function credit(uint8 asset,uint256 amount)external{tree.credit(_asset(asset),amount);}
    function take(uint8 asset,uint256 ordinal)external returns(uint256){return tree.take(_asset(asset),ordinal);}
    function claimable(uint8 asset,uint256 ordinal)external view returns(uint256){return tree.claimable(_asset(asset),ordinal);}
    function outstanding(uint8 asset)external view returns(uint256){return tree.outstanding(_asset(asset));}
    function totalWeight()external view returns(uint256){return tree.totalWeight();}
    function weightOf(uint256 ordinal)external view returns(uint256){return tree.weightOf(ordinal);}
    function split(uint256 amount,uint256 left,uint256 total,uint128 high,uint256 low)
        external pure returns(uint256,uint256,uint128,uint256){return ExactLPAllocation.split(amount,left,total,high,low);}
    function node(uint8 asset,uint256 index)external view returns(uint256 weight,uint256 pending,uint128 high,uint256 low){
        require(index!=0&&index<2048);ExactLPAllocation.Book storage b=tree.books[uint256(_asset(asset))];
        return(tree.weights[index],b.pending[index],b.carry[index].high,b.carry[index].low);
    }
    // Complete bounded state digest is test-only. No production operation walks
    // every NFT/node to credit fees, claim one leaf or change one weight.
    function digest()external view returns(bytes32 value){
        value=keccak256(abi.encode(tree.books[0].outstanding,tree.books[1].outstanding));
        for(uint256 i=1;i<2048;++i)value=keccak256(abi.encode(value,tree.weights[i],
            tree.books[0].pending[i],tree.books[0].carry[i].high,tree.books[0].carry[i].low,
            tree.books[1].pending[i],tree.books[1].carry[i].high,tree.books[1].carry[i].low));
    }
    function _asset(uint8 asset)private pure returns(ExactLPAllocation.Asset){require(asset<2,"TEST ONLY unknown asset");return ExactLPAllocation.Asset(asset);}
}

/// @dev TEST ONLY frozen baseline adapter for exact complete-state comparison.
contract ExactLPBaselineHarness {
    using ExactLPAllocationBaseline for ExactLPAllocationBaseline.Tree;
    ExactLPAllocationBaseline.Tree private tree;
    function setWeight(uint256 id,uint256 w)external returns(uint256){return tree.setWeight(id,w);}
    function credit(uint8 a,uint256 n)external{tree.credit(ExactLPAllocationBaseline.Asset(a),n);}
    function take(uint8 a,uint256 id)external returns(uint256){return tree.take(ExactLPAllocationBaseline.Asset(a),id);}
    function claimable(uint8 a,uint256 id)external view returns(uint256){return tree.claimable(ExactLPAllocationBaseline.Asset(a),id);}
    function digest()external view returns(bytes32 value){
        value=keccak256(abi.encode(tree.books[0].outstanding,tree.books[1].outstanding));
        for(uint256 i=1;i<2048;++i)value=keccak256(abi.encode(value,tree.weights[i],
            tree.books[0].pending[i],tree.books[0].carry[i].high,tree.books[0].carry[i].low,
            tree.books[1].pending[i],tree.books[1].carry[i].high,tree.books[1].carry[i].low));
    }
}

contract ExactLPAllocationTest is Test {
    uint256 private constant Q=uint256(1)<<128;
    ExactLPAllocationHarness private h;
    uint256[2048] private rw;
    uint256[2048][2] private rh;
    uint256[2048][2] private rl;
    uint256[1001][2] private rb;
    uint256[8] private ordinals=[uint256(1),2,17,128,513,700,999,1000];
    event ColdEngineGas(uint256 ordinals,uint256 credit,uint256 take,uint256 weightChange,uint256 batch32);
    function setUp()public{h=new ExactLPAllocationHarness();}

    function _refWeight(uint256 ordinal,uint256 weight)private{
        uint256 leaf=1024+ordinal-1;if(rw[leaf]==weight)return;rw[leaf]=weight;
        for(uint256 node=leaf>>1;node!=0;node>>=1){uint256 old=rw[node];uint256 next=rw[node<<1]+rw[(node<<1)|1];rw[node]=next;
            for(uint8 a;a<2;++a)rl[a][node]=old==0||next==0?0:rl[a][node]*next/old;
        }
    }
    function _weight(uint256 ordinal,uint256 weight)private{h.setWeight(ordinal,weight);_refWeight(ordinal,weight);}
    function _refCredit(uint8 asset,uint256 amount,uint256 node)private{
        if(amount==0)return;
        if(node>=1024){uint256 ordinal=node-1024+1;assertLe(ordinal,1000);rb[asset][ordinal]+=amount;return;}
        uint256 total=rw[node];assertGt(total,0);
        // Independent EAGER rational oracle. Test ranges guarantee this single
        // expression fits256bits; the engine instead uses full-width mulDiv,
        // mulmod, gap folds and lazy paths. No engine split is reused here.
        uint256 rational=amount*rw[node<<1]*Q+rh[asset][node]*total+rl[asset][node];
        uint256 denominator=total*Q;uint256 left=rational/denominator;uint256 rest=rational%denominator;
        rh[asset][node]=rest/total;rl[asset][node]=rest%total;
        _refCredit(asset,left,node<<1);_refCredit(asset,amount-left,(node<<1)|1);
    }
    function _credit(uint8 asset,uint256 amount)private{h.credit(asset,amount);_refCredit(asset,amount,1);}
    function _take(uint8 asset,uint256 ordinal)private returns(uint256 amount){amount=h.take(asset,ordinal);assertEq(amount,rb[asset][ordinal]);rb[asset][ordinal]=0;}
    function _reference()private view{
        assertEq(h.totalWeight(),rw[1]);
        for(uint8 a;a<2;++a){uint256 pending;
            for(uint256 i;i<8;++i){uint256 id=ordinals[i];assertEq(h.weightOf(id),rw[1024+id-1]);assertEq(h.claimable(a,id),rb[a][id]);pending+=rb[a][id];}
            assertEq(h.outstanding(a),pending);
        }
    }
    function _treeInvariant()private view{
        for(uint8 a;a<2;++a){uint256 pending;
            for(uint256 n=1;n<2048;++n){(uint256 w,uint256 p,,uint256 low)=h.node(a,n);pending+=p;
                if(n<1024){(uint256 l,,,)=h.node(a,n<<1);(uint256 r,,,)=h.node(a,(n<<1)|1);assertEq(w,l+r);if(w==0)assertEq(low,0);else assertLt(low,w);}
                if(n>=2024){assertEq(w,0);assertEq(p,0);}
            }
            assertEq(pending,h.outstanding(a));
        }
    }

    function testExactLPFinalUnitsForBothBooks101Shares()public{
        h.setWeight(1,101);
        for(uint8 a;a<2;++a){h.credit(a,1);assertEq(h.claimable(a,1),1);assertEq(h.take(a,1),1);assertEq(h.outstanding(a),0);assertEq(h.take(a,1),0);}
        _treeInvariant();
    }
    function testExactLPSplitFullWidthAndInvalidBounds()public{
        uint256 m=type(uint256).max;
        // Independent big-integer vector: f is almost1, product is512bits.
        (uint256 l,uint256 r,uint128 high,uint256 low)=h.split(m-1,m/2,m,type(uint128).max,m-1);
        assertEq(l,m/2);assertEq(r,m/2);assertEq(uint256(high),Q/2);assertEq(low,Q/2-1);
        (l,r,high,low)=h.split(m,m,m,type(uint128).max,m-1);assertEq(l,m);assertEq(r,0);assertEq(uint256(high),Q-1);assertEq(low,m-1);
        (l,r,,)=h.split(m,0,m,type(uint128).max,m-1);assertEq(l,0);assertEq(r,m);
        vm.expectRevert(ExactLPAllocation.InvalidSplit.selector);h.split(1,0,0,0,0);
        vm.expectRevert(ExactLPAllocation.InvalidSplit.selector);h.split(1,2,1,0,0);
        vm.expectRevert(ExactLPAllocation.InvalidSplit.selector);h.split(1,1,2,0,2);
    }
    function testExactLPWideRebasePreservesBothBookRightsAndHighPhase()public{
        uint256 m=type(uint256).max;uint256 left=m/2;uint256 right=m-left;
        h.setWeight(1,left);h.setWeight(1000,right);h.credit(0,1);h.credit(1,3);
        assertEq(h.take(0,1),0);assertEq(h.take(1,1),1);
        uint128[2] memory highBefore;uint256[2] memory lowBefore;uint256[2] memory oldRight;
        for(uint8 a;a<2;++a){(,,highBefore[a],lowBefore[a])=h.node(a,1);assertGt(lowBefore[a],m/2);oldRight[a]=h.claimable(a,1000);}
        // Both low*(MAX-1) products exceed256bits. Independent golden identity:
        // floor(low*(MAX-1)/MAX)=low-1 for0<low<MAX. No engine split is reused.
        h.setWeight(1000,right-1);assertEq(h.totalWeight(),m-1);
        for(uint8 a;a<2;++a){(,,uint128 high,uint256 low)=h.node(a,1);assertEq(uint256(high),uint256(highBefore[a]));assertEq(low,lowBefore[a]-1);
            assertEq(h.claimable(a,1000),oldRight[a]);h.credit(a,17);assertEq(h.take(a,1)+h.take(a,1000),oldRight[a]+17);assertEq(h.outstanding(a),0);
        }
    }
    function testFuzzExactLPSplitMatchesIndependentRationalExpression(uint64 amount,uint48 rawWeight,uint48 rawLeft,uint128 high,uint48 rawLow)public view{
        uint256 w=uint256(rawWeight)+1;uint256 left=uint256(rawLeft)%(w+1);uint256 low=uint256(rawLow)%w;
        uint256 rational=uint256(amount)*left*Q+uint256(high)*w+low;uint256 denominator=w*Q;
        uint256 expectedLeft=rational/denominator;uint256 rest=rational%denominator;
        (uint256 actualLeft,uint256 right,uint128 nextHigh,uint256 nextLow)=h.split(amount,left,w,high,low);
        assertEq(actualLeft,expectedLeft);assertEq(right,uint256(amount)-expectedLeft);assertEq(uint256(nextHigh),rest/w);assertEq(nextLow,rest%w);
    }
    function testExactLPFixedWeightsBatchingAndClaimOrder()public{
        ExactLPAllocationHarness bulk=new ExactLPAllocationHarness();uint256[5] memory ids=[uint256(1),2,17,513,1000];uint256[5] memory weights=[uint256(101),7,9,31,2];
        for(uint256 i;i<5;++i){_weight(ids[i],weights[i]);bulk.setWeight(ids[i],weights[i]);}
        uint256[8] memory receipts=[uint256(1),1,2,17,23,101,1,1001];uint256[2] memory paid;
        for(uint256 i;i<8;++i)for(uint8 a;a<2;++a){_credit(a,receipts[i]*(a+1));if(i%2==0)paid[a]+=_take(a,2);}
        for(uint8 a;a<2;++a){bulk.credit(a,1147*(a+1));for(uint256 i=5;i>0;--i){uint256 id=ids[i-1];uint256 expected=rb[a][id]+(id==2?paid[a]:0);assertEq(bulk.claimable(a,id),expected);assertEq(bulk.take(a,id),expected);_take(a,id);}assertEq(h.outstanding(a),0);assertEq(bulk.outstanding(a),0);}
        _reference();
    }
    function testExactLPActivationGrowthSettlesBothOldAssetPaths()public{
        _weight(1,1);_weight(2,1);_weight(1000,3);_credit(0,103);_credit(1,107);
        uint256 ethSibling=rb[0][2];uint256 zzzSibling=rb[1][2];_weight(513,300);
        assertEq(h.claimable(0,513),0);assertEq(h.claimable(1,513),0);_weight(1,1001);
        assertEq(h.claimable(0,2),ethSibling);assertEq(h.claimable(1,2),zzzSibling);_reference();
        _credit(0,109);_credit(1,113);_reference();for(uint8 a;a<2;++a)for(uint256 i;i<8;++i)_take(a,ordinals[i]);_treeInvariant();
    }
    function testExactLPNoopLeavesPendingAndPhaseIdentical()public{
        h.setWeight(1,1);h.setWeight(2,2);h.credit(0,1);h.take(0,2);h.credit(1,11);
        (,,uint128 high,)=h.node(0,512);assertGt(uint256(high),0);bytes32 before=h.digest();
        assertEq(h.setWeight(2,2),3);assertEq(h.digest(),before);assertEq(h.take(0,1),0);assertEq(h.take(1,1)+h.take(1,2),11);
    }
    function testExactLPPreservesPhaseAcrossGenuineGrowthInsteadOfResetStarvation()public{
        _weight(1,1);_weight(2,2);_credit(0,1);_credit(1,1);
        for(uint256 right=3;right<=20;++right){_weight(2,right);_credit(0,1);_credit(1,1);_reference();}
        // Resetting a whole fractional phase each time would pay the minority0
        // forever in this tiny-credit/genuine-growth schedule. Preserve it.
        for(uint8 a;a<2;++a){uint256 minority=_take(a,1);assertGt(minority,0);uint256 majority=_take(a,2);assertEq(minority+majority,19);assertEq(h.outstanding(a),0);}
    }
    function testExactLPPhaseApproximationCanDelayOneUnitAtIntegerBoundary()public{
        h.setWeight(1,1);h.setWeight(2,2);h.credit(0,1);h.setWeight(2,3);h.setWeight(2,5);h.credit(0,4);
        // Exact unbounded rational phase1/3+4/6 would hit1. Bounded low-phase
        // rebases leave it just below1: ALL5whole units belong to the right NFT.
        assertEq(h.claimable(0,1),0);assertEq(h.claimable(0,2),5);assertEq(h.take(0,2),5);
        h.credit(0,1);assertEq(h.take(0,1),1);assertEq(h.outstanding(0),0);
    }
    function testExactLPZeroWeightsPreserveOldWholeRightsAndHighPhase()public{
        h.setWeight(1,1);h.setWeight(2,2);h.credit(0,1);h.setWeight(1,0);
        (,,uint128 before,)=h.node(0,512);assertGt(uint256(before),0);h.setWeight(2,0);
        (,,uint128 afterHigh,uint256 low)=h.node(0,512);assertEq(uint256(afterHigh),uint256(before));assertEq(low,0);
        assertEq(h.claimable(0,1),0);assertEq(h.claimable(0,2),1);assertEq(h.take(0,2),1);
        vm.expectRevert(ExactLPAllocation.EmptyCohort.selector);h.credit(0,1);
        h.setWeight(1,1);h.setWeight(2,2);(,,afterHigh,)=h.node(0,512);assertEq(uint256(afterHigh),uint256(before));
        h.credit(0,3);assertEq(h.take(0,1)+h.take(0,2),3);_treeInvariant();
        ExactLPAllocationHarness sole=new ExactLPAllocationHarness();sole.setWeight(1000,10);sole.credit(1,7);sole.setWeight(1000,0);
        assertEq(sole.claimable(1,1000),7);assertEq(sole.take(1,1000),7);assertEq(sole.outstanding(1),0);
    }
    function testExactLPLifetimeCanExceedUint256WithBoundedOutstanding()public{
        h.setWeight(1000,101);for(uint256 cycle;cycle<2;++cycle)for(uint8 a;a<2;++a){h.credit(a,type(uint256).max);assertEq(h.claimable(a,1000),type(uint256).max);assertEq(h.take(a,1000),type(uint256).max);assertEq(h.outstanding(a),0);}
    }
    function testExactLPInvalidAndOverflowOperationsRollBack()public{
        h.setWeight(1,type(uint256).max);bytes32 before=h.digest();vm.expectRevert();h.setWeight(2,1);assertEq(h.digest(),before);
        vm.expectRevert(ExactLPAllocation.InvalidOrdinal.selector);h.setWeight(0,1);vm.expectRevert(ExactLPAllocation.InvalidOrdinal.selector);h.setWeight(1001,1);
        vm.expectRevert(ExactLPAllocation.InvalidOrdinal.selector);h.claimable(0,1024);vm.expectRevert(ExactLPAllocation.InvalidOrdinal.selector);h.take(0,0);assertEq(h.digest(),before);
        h.credit(0,type(uint256).max);before=h.digest();vm.expectRevert();h.credit(0,1);assertEq(h.digest(),before);assertEq(h.take(0,1),type(uint256).max);
        vm.expectRevert();h.credit(2,1);h.setWeight(1,0);before=h.digest();vm.expectRevert(ExactLPAllocation.EmptyCohort.selector);h.credit(1,1);assertEq(h.digest(),before);
    }
    function testExactLP1000OrdinalsConserveBothBooksWithoutPadding()public{
        for(uint256 id=1;id<=1000;++id)h.setWeight(id,id%13+1);h.credit(0,1234567);h.credit(1,9876543);
        uint256[2] memory preview;uint256[2] memory paid;
        for(uint256 id=1;id<=1000;++id)for(uint8 a;a<2;++a)preview[a]+=h.claimable(a,id);
        for(uint256 id=1000;id!=0;--id)for(uint8 a;a<2;++a)paid[a]+=h.take(a,id);
        assertEq(preview[0],1234567);assertEq(preview[1],9876543);assertEq(paid[0],preview[0]);assertEq(paid[1],preview[1]);assertEq(h.outstanding(0),0);assertEq(h.outstanding(1),0);_treeInvariant();
    }
    function testExactLPCold1000OrdinalEngineGasSamples()public{
        for(uint256 id=1;id<=1000;++id)h.setWeight(id,id%13+1);h.credit(0,1 ether);h.credit(1,1 ether);
        vm.cool(address(h));uint256 start=gasleft();h.credit(0,10000);uint256 creditGas=start-gasleft();
        vm.cool(address(h));start=gasleft();uint256 paid=h.take(0,1);uint256 takeGas=start-gasleft();assertGt(paid,0);
        h.credit(0,1 ether);vm.cool(address(h));start=gasleft();h.setWeight(500,500%13+18);uint256 weightGas=start-gasleft();
        h.credit(0,1 ether);h.credit(1,1 ether);vm.cool(address(h));start=gasleft();
        for(uint256 id=1;id<=16;++id){h.take(0,id);h.take(1,id);}uint256 batchGas=start-gasleft();
        // Internal-engine + external harness-call gas only; excludes transfer,
        // host owner/funding checks, second component, intrinsic fees and router.
        emit ColdEngineGas(1000,creditGas,takeGas,weightGas,batchGas);
    }
    function testFuzzExactLPMixedSequenceMatchesIndependentEagerOracle(uint256 seed)public{
        _weight(1,7);_weight(1000,11);
        for(uint256 step;step<12;++step){seed=uint256(keccak256(abi.encode(seed,step)));uint256 ordinal=ordinals[seed%8];uint8 asset=uint8((seed>>32)%2);uint256 action=(seed>>64)%4;
            if(action==0)_weight(ordinal,(seed>>96)%1001);
            else if(action==1){uint256 amount=(seed>>128)%10000;if(rw[1]==0&&amount!=0){vm.expectRevert(ExactLPAllocation.EmptyCohort.selector);h.credit(asset,amount);}else _credit(asset,amount);}
            else if(action==2)_take(asset,ordinal);else _weight(ordinal,rw[1024+ordinal-1]);_reference();
        }
        for(uint8 a;a<2;++a)for(uint256 i;i<8;++i)_take(a,ordinals[i]);_reference();
    }
    function _baselineSame(ExactLPBaselineHarness baseline)private view{assertEq(h.digest(),baseline.digest());}
    function _baselineWeight(ExactLPBaselineHarness baseline,uint256 id,uint256 weight)private{
        assertEq(h.setWeight(id,weight),baseline.setWeight(id,weight));_baselineSame(baseline);
    }
    function _baselineCredit(ExactLPBaselineHarness baseline,uint8 asset,uint256 amount)private{
        h.credit(asset,amount);baseline.credit(asset,amount);_baselineSame(baseline);
    }
    function _baselineTake(ExactLPBaselineHarness baseline,uint8 asset,uint256 id)private{
        assertEq(h.claimable(asset,id),baseline.claimable(asset,id));_baselineSame(baseline);
        assertEq(h.take(asset,id),baseline.take(asset,id));_baselineSame(baseline);
    }
    function testExactLPOptimizedMatchesFrozenBaselineOrdinaryLifecycleCompleteStorage()public{
        ExactLPBaselineHarness baseline=new ExactLPBaselineHarness();_baselineSame(baseline);
        _baselineWeight(baseline,1,7);_baselineWeight(baseline,1000,11);
        _baselineCredit(baseline,0,103);_baselineCredit(baseline,1,107);_baselineTake(baseline,0,1);
        _baselineWeight(baseline,2,17);assertEq(h.claimable(0,2),0);assertEq(h.claimable(1,2),0);
        _baselineCredit(baseline,0,19);_baselineCredit(baseline,1,23);_baselineTake(baseline,1,1000);
        _baselineWeight(baseline,1,900);_baselineWeight(baseline,1,900);_baselineWeight(baseline,1000,0);
        for(uint8 a;a<2;++a){_baselineTake(baseline,a,1);_baselineTake(baseline,a,2);_baselineTake(baseline,a,1000);}
        _baselineWeight(baseline,1,0);_baselineWeight(baseline,2,0);_baselineCredit(baseline,0,0);
        _baselineWeight(baseline,513,101);_baselineCredit(baseline,0,1);_baselineCredit(baseline,1,2);
        _baselineTake(baseline,0,513);_baselineTake(baseline,1,513);
    }
    function testExactLPOptimizedMatchesFrozenBaselineFullWidthCompleteStorage()public{
        // A second fresh pair covers the full-width low-phase rebase, preserving
        // every node/leaf/phase, not merely equality of the final claim totals.
        h=new ExactLPAllocationHarness();ExactLPBaselineHarness baseline=new ExactLPBaselineHarness();_baselineSame(baseline);
        uint256 m=type(uint256).max;_baselineWeight(baseline,1,m/2);_baselineWeight(baseline,1000,m-m/2);
        _baselineCredit(baseline,0,1);_baselineCredit(baseline,1,3);_baselineTake(baseline,0,1);_baselineTake(baseline,1,1);
        _baselineWeight(baseline,1000,m-m/2-1);_baselineCredit(baseline,0,17);_baselineCredit(baseline,1,29);
        for(uint8 a;a<2;++a){_baselineTake(baseline,a,1);_baselineTake(baseline,a,1000);}
    }
}
