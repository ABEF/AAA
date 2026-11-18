// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {RoyaltyRounds20261118 as Rounds} from "./fixtures/RoyaltyRounds20261118.sol";
import {Q03GlobalBoundAllocation as Old} from "./fixtures/Q03GlobalBoundAllocation.sol";
import {ExactRoyaltyAllocation as PreviewV4} from "./fixtures/ExactRoyaltyTreeV4.sol";

/// @dev Controlled arithmetic/eligibility model, not an actual NFT/token graph.
/// Opening, unreadable-currency cohort gaps and flat imported accrual are explicit
/// seams. No receiver, arbitrary caller or financial bound is supplied to claims.
contract RoyaltyRoundPrototypeHost {
    using Rounds for Rounds.Book;using Rounds for Rounds.Cohorts;
    address private immutable creator=msg.sender;
    mapping(uint256=>mapping(uint256=>Rounds.Book)) private books;
    mapping(uint256=>Rounds.Cohorts) private cohorts;
    mapping(uint256=>mapping(uint256=>uint256)) private paid;
    mapping(uint256=>mapping(uint256=>uint256)) public accrued;
    mapping(uint256=>uint256) public weight;
    mapping(uint256=>uint256) public first;
    mapping(uint256=>uint256) public prefix;
    uint256[3] private firstKind;
    mapping(uint256=>uint256) public eligible;
    mapping(uint256=>uint256) public cursor;
    mapping(uint256=>uint256) public liability;
    mapping(uint256=>uint256) public cash;
    mapping(uint256=>uint256) public pending;
    mapping(uint256=>uint256) public orphan;
    mapping(uint256=>bool) public initial;
    uint256 public count;bool public open;uint256 public cutoff;
    modifier controlled(){require(msg.sender==creator);_;}
    constructor(bool opening){open=!opening;initial[0]=!opening;initial[1]=!opening;}
    function unit(uint256 n) public view returns(uint256){
        bool rare=firstKind[1]!=0&&firstKind[1]<=n;bool legendary=firstKind[2]!=0&&firstKind[2]<=n;
        if((firstKind[0]!=0&&firstKind[0]<=n)||(rare&&legendary))return 1;
        return rare?2:legendary?3:0;
    }
    function fund(uint256 asset,uint256 a) external controlled{cash[asset]+=a;pending[asset]+=a;}
    function _enroll(uint256 asset,uint256 n) private {
        if(n!=0)cohorts[asset].enroll(n,books[asset][unit(n)].rounds);
        eligible[asset]=n;
    }
    function _sync(uint256 asset) private {
        if(!open)return;
        if(!initial[asset]){initial[asset]=true;_enroll(asset,cutoff);}
        uint256 n=eligible[asset];uint256 w=prefix[n];uint256 a=pending[asset];pending[asset]=0;
        if(w==0)orphan[asset]+=a;
        else if(a!=0){
            uint256 u=unit(n);(uint256 next,uint256 afterL)=books[asset][u].credit(a,w/u,cursor[asset]/u,liability[asset]);
            liability[asset]=afterL;cursor[asset]=next*u;
        }
        _enroll(asset,count);
    }
    function sync(uint256 asset) external controlled{_sync(asset);}
    function activate(uint256 w,bool healthy0,bool healthy1) external controlled {
        if(healthy0)_sync(0);if(healthy1)_sync(1);
        require(count<1000&&w>0&&w<=3);uint256 id=++count;
        first[id]=prefix[id-1]+1;weight[id]=w;prefix[id]=prefix[id-1]+w;
        if(firstKind[w-1]==0)firstKind[w-1]=id;
        if(healthy0)_enroll(0,id);if(healthy1)_enroll(1,id);
    }
    function finishWindow() external controlled{require(!open);open=true;cutoff=count;}
    function seedImportedCursor(uint256 asset,uint256 c) external controlled{
        require(initial[asset]&&liability[asset]==0&&cursor[asset]==0&&c<prefix[count]);
        require(c%unit(count)==0);cursor[asset]=c;
    }
    function seedAccrued(uint256 id,uint256 asset,uint256 a) external controlled {
        accrued[id][asset]+=a;liability[asset]+=a;cash[asset]+=a;
    }
    function _gross(uint256 id,uint256 asset) private view returns(uint256 gross,uint256 born){
        if(id==0||id>eligible[asset])return(0,0);
        (uint256 end,uint256 birthRound)=cohorts[asset].birth(id);uint256 birthUnit=unit(end);
        uint256 w=weight[id];uint256 start=first[id];
        unchecked {
            gross=books[asset][1].gross(start,start+w-1);
            if(birthUnit==1)born=birthRound*w;
            else {
                require(birthUnit==w);uint256 key=(start-1)/w+1;
                gross+=books[asset][w].gross(key,key);born=birthRound;
            }
        }
    }
    function claimable(uint256 id,uint256 asset) public view returns(uint256 a){
        (uint256 gross,uint256 born)=_gross(id,asset);uint256 remaining;
        unchecked{remaining=gross-born-paid[id][asset];}
        a=accrued[id][asset]+remaining;require(a<=liability[asset]);
    }
    function claim(uint256 id,uint256 asset) external controlled returns(uint256 a){
        _sync(asset);(uint256 gross,uint256 born)=_gross(id,asset);uint256 counter;
        unchecked{uint256 entitlement=gross-born;counter=entitlement-paid[id][asset];paid[id][asset]=entitlement;}
        a=accrued[id][asset]+counter;accrued[id][asset]=0;liability[asset]-=a;cash[asset]-=a;
    }
    function birth(uint256 asset,uint256 id) external view returns(uint256,uint256){return cohorts[asset].birth(id);}
}

contract RoyaltyRoundCreditGasHost {
    using Rounds for Rounds.Book;Rounds.Book private book;uint256 private liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256 next){
        uint256 afterL;(next,afterL)=book.credit(a,w,c,liability);liability=afterL;
    }
}
contract RoyaltyOldCreditGasHost {
    using Old for Old.Book;Old.Book private book;uint256 private liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256 next){
        uint256 afterL;(next,afterL)=book.credit(a,w,c,liability);liability=afterL;
    }
}
contract RoyaltyRoundCohortHost {
    using Rounds for Rounds.Cohorts;Rounds.Cohorts private cohorts;
    function enroll(uint256 n,uint256 q) external{cohorts.enroll(n,q);}
    function birth(uint256 n) external view returns(uint256,uint256){return cohorts.birth(n);}
}

contract RoyaltyRoundPrototype20261118Test is Test {
    RoyaltyRoundPrototypeHost private host;
    mapping(uint256=>mapping(uint256=>uint256)) private model;
    function _fresh(bool opening) private{host=new RoyaltyRoundPrototypeHost(opening);}
    function _modelSync(uint256 asset) private {
        if(!host.open())return;
        uint256 n=host.initial(asset)?host.eligible(asset):host.cutoff();
        uint256 a=host.pending(asset);if(n==0||a==0)return;
        // Independent normalized per-ticket quotient/remainder model. No round
        // counter, birth checkpoint, bitmap or paid-debt equation is used.
        uint256 u=host.weight(1);
        for(uint256 id=2;id<=n;++id)if(host.weight(id)!=u)u=1;
        uint256 w=host.prefix(n)/u;uint256 c=host.cursor(asset)/u;
        for(uint256 id=1;id<=n;++id){
            uint256 start=(host.first(id)-1)/u+1;uint256 tickets=host.weight(id)/u;
            for(uint256 t=start;t<start+tickets;++t)model[asset][id]+=a/w+((t-1+w-c)%w<a%w?1:0);
        }
    }
    function _check(uint256 asset) private view{
        uint256 sum;for(uint256 id=1;id<=host.count();++id){assertEq(host.claimable(id,asset),model[asset][id]);sum+=model[asset][id];}
        assertEq(host.liability(asset),sum);
        assertEq(host.cash(asset),sum+host.pending(asset)+host.orphan(asset));
    }
    function _activate(uint256 w,bool healthy0,bool healthy1) private {
        if(healthy0)_modelSync(0);if(healthy1)_modelSync(1);host.activate(w,healthy0,healthy1);_check(0);_check(1);
    }
    function _sync(uint256 asset) private{_modelSync(asset);host.sync(asset);_check(asset);}
    function _fund(uint256 asset,uint256 a) private{host.fund(asset,a);}
    function _claim(uint256 id,uint256 asset) private{
        _modelSync(asset);uint256 expected=model[asset][id];assertEq(host.claim(id,asset),expected);model[asset][id]=0;_check(asset);
    }
    function _import(uint256 id,uint256 asset,uint256 a) private{model[asset][id]+=a;host.seedAccrued(id,asset,a);_check(asset);}

    function testRoundVariablePrefixesAndPartialClaimsMatchEveryTicket() public {
        _fresh(false);_activate(1,true,true);_fund(0,1);_sync(0);
        for(uint256 step;step<40;++step){
            _fund(0,step*7+13);_fund(1,step*5+11);_activate(step%3+1,true,true);
            if(step%3==0)_claim(step/3+1,0);if(step%4==0)_claim(step/4+1,1);
        }
        for(uint256 id=host.count();id!=0;--id){_claim(id,0);_claim(id,1);}
        assertEq(host.liability(0),0);assertEq(host.liability(1),0);
    }
    function testRoundHomogeneousTransitionsFreezeOldBookAndSnapshotNewUnit() public {
        for(uint256 homogeneous=2;homogeneous<=3;++homogeneous){
            _fresh(false);for(uint256 i;i<5;++i)_activate(homogeneous,true,true);
            _fund(0,17);_sync(0);assertGt(host.cursor(0),0);_claim(2,0);
            _fund(0,19);_activate(1,true,true);assertEq(host.claimable(6,0),0);
            _fund(0,29);_sync(0);_fund(0,31);_activate(homogeneous,true,true);
            assertEq(host.claimable(7,0),0);_fund(0,53);_sync(0);
            for(uint256 id=7;id!=0;--id)_claim(id,0);
            assertEq(host.cash(0),0);
        }
    }
    function testRoundFaultGroupAndOpeningCutoffPreserveDifferentCohorts() public {
        _fresh(false);_activate(2,true,true);_activate(2,true,true);_fund(1,7);
        _activate(2,true,false);_activate(1,true,false);_activate(3,true,false);
        assertEq(host.eligible(1),2);_sync(1);
        for(uint256 id=3;id<=5;++id)assertEq(host.claimable(id,1),0);
        (uint256 end,)=host.birth(1,3);assertEq(end,5);
        _fund(1,17);_sync(1);for(uint256 id=1;id<=5;++id)_claim(id,1);
        _fresh(true);_activate(2,true,true);_fund(1,23);_activate(1,true,false);
        host.finishWindow();_activate(3,true,false);_sync(1);
        assertEq(host.claimable(3,1),0);assertGt(host.claimable(2,1),0);
        for(uint256 id=1;id<=3;++id)_claim(id,1);assertEq(host.cash(1),0);
    }
    function testRoundImportedCursorAccrualAndMaximumLifetimeWrapDrainExactly() public {
        _fresh(false);for(uint256 id=1;id<=4;++id)_activate(1,true,true);
        host.seedImportedCursor(0,3);_import(1,0,29);_import(4,0,31);
        _fund(0,7);_sync(0);_claim(3,0);_activate(2,true,true);_fund(0,17);_sync(0);
        for(uint256 id=1;id<=5;++id)_claim(id,0);assertEq(host.cash(0),0);
        _fresh(false);for(uint256 id=1;id<=4;++id)_activate(1,true,true);
        for(uint256 epoch;epoch<5;++epoch){
            _fund(0,type(uint256).max);_sync(0);
            vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));host.fund(0,1);
            for(uint256 id=4;id!=0;--id)_claim(id,0);assertEq(host.cash(0),0);
        }
        _import(1,0,type(uint256).max-999);_fund(0,999);_sync(0);
        for(uint256 id=1;id<=4;++id)_claim(id,0);assertEq(host.liability(0),0);
    }
    function testRoundColdCreditIsBoundedIndependentlyOfPrefixStorageGeometry() public {
        uint256[4] memory ws=[uint256(4),1023,1499,3000];uint256 minGas=type(uint256).max;uint256 maxGas;
        for(uint256 i;i<ws.length;++i){
            uint256 w=ws[i];uint256 a=2*w-2;uint256 c=513%w;
            RoyaltyRoundCreditGasHost fresh=new RoyaltyRoundCreditGasHost();RoyaltyOldCreditGasHost old=new RoyaltyOldCreditGasHost();
            vm.cool(address(fresh));vm.cool(address(old));uint256 start=gasleft();uint256 got=fresh.credit(a,w,c);uint256 used=start-gasleft();
            start=gasleft();uint256 previousNext=old.credit(a,w,c);uint256 prior=start-gasleft();assertEq(got,previousNext);
            minGas=used<minGas?used:minGas;maxGas=used>maxGas?used:maxGas;
            if(w>=1023)assertLt(used,prior);
            emit log_named_uint("round prefix",w);emit log_named_uint("round cold credit",used);emit log_named_uint("prior cold credit",prior);
        }
        assertLt(maxGas-minGas,3000);
    }
    function testRoundZeroWrapBirthAndPhaseChangeRetainHistoricalDebt() public {
        _fresh(false);for(uint256 id=1;id<=4;++id)_activate(2,true,true);
        for(uint256 epoch;epoch<4;++epoch){
            _fund(0,type(uint256).max);_sync(0);for(uint256 id=1;id<=4;++id)_claim(id,0);
        }
        // Q reaches UINT_MAX after four drained maximum receipts, then wraps
        // exactly to zero after four additional units. Zero is a real baseline.
        _fund(0,4);_sync(0);for(uint256 id=1;id<=4;++id)_claim(id,0);
        _activate(2,true,true);(uint256 end,uint256 q)=host.birth(0,5);assertEq(end,5);assertEq(q,0);
        _fund(0,9);_activate(1,true,true);assertGt(host.cursor(0),0);assertEq(host.claimable(6,0),0);
        _fund(0,13);_sync(0);_claim(3,0);_activate(2,true,true);assertEq(host.claimable(7,0),0);
        _fund(0,29);_sync(0);for(uint256 id=7;id!=0;--id)_claim(id,0);
        assertEq(host.liability(0),0);assertEq(host.cash(0),0);
    }
    function testRoundCohortBoundariesAndZeroSnapshotAreExact() public {
        RoyaltyRoundCohortHost c=new RoyaltyRoundCohortHost();
        uint256[10] memory ends=[uint256(1),255,256,511,512,767,768,999,1000,1000];
        for(uint256 i;i<9;++i)c.enroll(ends[i],i==7?0:i+1);
        vm.expectRevert(Rounds.InvalidAllocation.selector);c.enroll(999,777); // Cannot rewrite an earlier boundary.
        for(uint256 ordinal=1;ordinal<=1000;++ordinal){
            uint256 index;while(ends[index]<ordinal)++index;
            (uint256 end,uint256 q)=c.birth(ordinal);assertEq(end,ends[index]);assertEq(q,index==7?0:index+1);
        }
        vm.expectRevert(Rounds.InvalidAllocation.selector);c.birth(0);
        vm.expectRevert(Rounds.InvalidAllocation.selector);c.birth(1001);
        vm.expectRevert(Rounds.InvalidAllocation.selector);c.enroll(1001,0);
    }
    function testRoundPreviewMatchesFrozenV4AtMaximumAndFutureIntervals() public pure {
        uint256[6] memory ws=[uint256(1),4,250,1023,1499,3000];
        for(uint256 i;i<ws.length;++i){
            uint256 w=ws[i];uint256[4] memory amounts=[uint256(0),1,2*w-2,type(uint256).max];
            uint256[3] memory cursors=[uint256(0),w-1,513%w];
            for(uint256 j;j<amounts.length;++j)for(uint256 k;k<cursors.length;++k){
                uint256 a=amounts[j];uint256 c=cursors[k];
                assertEq(Rounds.previewShare(a,w,c,1,3000),PreviewV4.previewShare(a,w,c,1,3000));
                assertEq(Rounds.previewShare(a,w,c,1,1),PreviewV4.previewShare(a,w,c,1,1));
                assertEq(Rounds.previewShare(a,w,c,w,w),PreviewV4.previewShare(a,w,c,w,w));
                if(w<3000)assertEq(Rounds.previewShare(a,w,c,w+1,3000),0);
            }
        }
    }
}
