// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {Q03EnvelopeAllocation as Envelope} from "./fixtures/Q03EnvelopeAllocation.sol";
import {Q03GlobalBoundAllocation as Global} from "./fixtures/Q03GlobalBoundAllocation.sol";
import {Q03PositiveAllocationBaseline as Positive} from "./fixtures/Q03ComplementAllocation.sol";

/// @dev Isolated allocator caller. The liability always belongs to this book;
/// no externally supplied financial bound is used by this authenticating host.
contract Q03EnvelopeHost {
    using Envelope for Envelope.Book;
    Envelope.Book private book;
    uint256 public liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256 next) {
        uint256 afterL;(next,afterL)=book.credit(a,w,c,liability);liability=afterL;
    }
    function take(uint256 t) external returns(uint256 a){a=book.takeTicket(t,liability);liability-=a;}
    function ticket(uint256 t) external view returns(uint256){return book.viewTicket(t);}
    /// @dev Test-only raw path for zero-entitlement envelope leaves beyond the
    /// public ticket limit. Public credit/view/take limits remain3000.
    function rawPath(uint256 t) external view returns(uint256 a){
        require(t!=0&&t<=4096);
        unchecked{for(uint256 n=4095+t;n!=0;n>>=1)a+=book.pending[n];}
    }
}
contract Q03EnvelopePositiveHost {
    using Positive for Positive.Book;Positive.Book private book;uint256 private liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256){liability+=a;return book.credit(a,w,c);}
    function take(uint256 t) external returns(uint256 a){a=book.takeTicket(t);liability-=a;}
    function ticket(uint256 t) external view returns(uint256){return book.viewTicket(t);}
}
contract Q03EnvelopeGlobalHost {
    using Global for Global.Book;Global.Book private book;uint256 private liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256 next){
        uint256 afterL;(next,afterL)=book.credit(a,w,c,liability);liability=afterL;
    }
    function take(uint256 t) external returns(uint256 a){a=book.takeTicket(t,liability);liability-=a;}
    function ticket(uint256 t) external view returns(uint256){return book.viewTicket(t);}
}

/// @dev Separate actual-caller model for old homogeneous books plus new unit1,
/// with imported accrued liabilities and an independent positive-tree shadow.
/// This models internal royalty economics, not NFT/token/canonical execution.
contract Q03EnvelopeCoupledHost {
    using Envelope for Envelope.Book;using Positive for Positive.Book;
    mapping(uint256=>Envelope.Book) private books;
    mapping(uint256=>Positive.Book) private refs;
    mapping(uint256=>uint256) public weights;
    mapping(uint256=>uint256) public first;
    mapping(uint256=>uint256) public accrued;
    uint256 public liability;uint256 public weight;uint256 public cursor;uint256 private kinds;
    function activate(uint256 id,uint256 w) external {
        require(weights[id]==0&&w!=0&&w<=3);first[id]=weight+1;weights[id]=w;weight+=w;kinds|=1<<w;
    }
    function seedAccrued(uint256 id,uint256 a) external {require(weights[id]!=0);accrued[id]+=a;liability+=a;}
    function unit() public view returns(uint256){
        if((kinds&2)!=0||(kinds&12)==12)return 1;return (kinds&4)!=0?2:3;
    }
    function credit(uint256 a) external {
        uint256 u=unit();require(cursor%u==0);
        (uint256 next,uint256 afterL)=books[u].credit(a,weight/u,cursor/u,liability);
        require(next==refs[u].credit(a,weight/u,cursor/u));liability=afterL;cursor=next*u;
    }
    function claimable(uint256 id) public view returns(uint256 a){
        a=accrued[id];uint256 start=first[id];uint256 w=weights[id];
        for(uint256 i;i<w;++i){uint256 v=books[1].viewTicket(start+i);require(v==refs[1].viewTicket(start+i));a+=v;}
        if(w>1){uint256 key=(start-1)/w+1;uint256 v=books[w].viewTicket(key);require(v==refs[w].viewTicket(key));a+=v;}
    }
    function claim(uint256 id) external returns(uint256 a){
        uint256 beforeL=liability;a=accrued[id];uint256 start=first[id];uint256 w=weights[id];
        for(uint256 i;i<w;++i){uint256 v=books[1].takeTicket(start+i,beforeL-a);require(v==refs[1].takeTicket(start+i));a+=v;}
        if(w>1){uint256 key=(start-1)/w+1;uint256 v=books[w].takeTicket(key,beforeL-a);require(v==refs[w].takeTicket(key));a+=v;}
        accrued[id]=0;liability-=a;
    }
}

contract Q03EnvelopeAllocation20261117Test is Test {
    function _expected(uint256 a,uint256 w,uint256 c,uint256 t) private pure returns(uint256){
        return a/w+((t-1+w-c)%w<a%w?1:0);
    }
    function _measure(uint256 w,bool opening) private {
        uint256 a=opening?w:2*w-2;uint256 c=opening?0:513%w;
        Q03EnvelopePositiveHost p=new Q03EnvelopePositiveHost();
        Q03EnvelopeGlobalHost g=new Q03EnvelopeGlobalHost();Q03EnvelopeHost e=new Q03EnvelopeHost();
        vm.cool(address(p));vm.cool(address(g));vm.cool(address(e));
        uint256 s=gasleft();uint256 pc=p.credit(a,w,c);uint256 pg=s-gasleft();
        s=gasleft();uint256 gc=g.credit(a,w,c);uint256 gg=s-gasleft();
        s=gasleft();uint256 ec=e.credit(a,w,c);uint256 eg=s-gasleft();
        assertEq(pc,ec);assertEq(gc,ec);
        if(w==1023||w==1499||w==3000)assertLt(eg,gg);
        if(w==1025||w==1024)assertLt(eg,gg+12_000); // direct encoding retained
        vm.cool(address(p));vm.cool(address(g));vm.cool(address(e));
        s=gasleft();uint256 pv=p.ticket(w);uint256 pvg=s-gasleft();
        s=gasleft();uint256 gv=g.ticket(w);uint256 gvg=s-gasleft();
        s=gasleft();uint256 ev=e.ticket(w);uint256 evg=s-gasleft();
        assertEq(pv,ev);assertEq(gv,ev);assertEq(ev,_expected(a,w,c,w));
        vm.cool(address(p));vm.cool(address(g));vm.cool(address(e));
        s=gasleft();uint256 pt=p.take(w);uint256 ptg=s-gasleft();
        s=gasleft();uint256 gt=g.take(w);uint256 gtg=s-gasleft();
        s=gasleft();uint256 et=e.take(w);uint256 etg=s-gasleft();
        assertEq(pt,et);assertEq(gt,et);assertEq(et,ev);
        emit log_named_uint("envelope weight",w);emit log_named_uint("opening prefix",opening?1:0);
        emit log_named_uint("positive cold credit",pg);emit log_named_uint("global cold credit",gg);emit log_named_uint("envelope cold credit",eg);
        emit log_named_uint("positive cold view",pvg);emit log_named_uint("global cold view",gvg);emit log_named_uint("envelope cold view",evg);
        emit log_named_uint("positive cold take",ptg);emit log_named_uint("global cold take",gtg);emit log_named_uint("envelope cold take",etg);
        if(w<3000){
            vm.cool(address(e));s=gasleft();assertEq(e.ticket(w+1),0);emit log_named_uint("envelope future cold view",s-gasleft());
            vm.cool(address(e));s=gasleft();assertEq(e.take(w+1),0);emit log_named_uint("envelope future cold take",s-gasleft());
        }
        assertEq(e.rawPath(4096),0);assertEq(e.liability(),a-et);
    }
    function testQ03EnvelopeColdCreditViewAndTakeIncludeExistingLiability() public {
        vm.pauseGasMetering();uint256[5] memory ws=[uint256(1023),1499,1025,3000,1024];
        for(uint256 i;i<ws.length;++i){vm.resumeGasMetering();_measure(ws[i],true);_measure(ws[i],false);vm.pauseGasMetering();}
        vm.resumeGasMetering();
    }
    function testQ03EnvelopeGrowingPrefixZeroFutureClaimsDoNotLeakOrResurrect() public {
        Q03EnvelopeHost e=new Q03EnvelopeHost();uint256[] memory model=new uint256[](3001);
        uint256[7] memory ws=[uint256(1023),1024,1499,1500,2047,2048,3000];uint256 cursor;
        for(uint256 epoch;epoch<ws.length;++epoch){
            uint256 w=ws[epoch];uint256 a=epoch==0?w:2*w-2+epoch;
            for(uint256 t=1;t<=w;++t)model[t]+=_expected(a,w,cursor,t);
            cursor=e.credit(a,w,cursor);uint256 sum;
            for(uint256 t=1;t<=3000;++t){assertEq(e.ticket(t),model[t]);sum+=model[t];}
            assertEq(e.liability(),sum);assertEq(e.rawPath(4096),0);
            uint256 selectedTicket=epoch+1;assertEq(e.take(selectedTicket),model[selectedTicket]);model[selectedTicket]=0;
            if(w<3000){assertEq(e.take(w+1),0);assertEq(e.ticket(w+1),0);}
        }
        uint256 total;
        for(uint256 t=3000;t!=0;--t){assertEq(e.take(t),model[t]);total+=model[t];model[t]=0;}
        assertEq(e.liability(),0);assertGt(total,0);assertEq(e.rawPath(4096),0);
        e.credit(1499,1499,0);
        for(uint256 t=1;t<=3000;++t)assertEq(e.take(t),t<=1499?1:0);
        assertEq(e.liability(),0);assertEq(e.rawPath(4096),0);
    }
    function testQ03EnvelopeUintMaximumCancellationAndCheckedLiability() public {
        uint256[6] memory ws=[uint256(1),4,250,1023,1499,3000];
        for(uint256 i;i<ws.length;++i){
            Q03EnvelopeHost e=new Q03EnvelopeHost();uint256 w=ws[i];uint256 c=513%w;
            uint256 next=e.credit(type(uint256).max,w,c);
            vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));e.credit(1,w,next);
            uint256 sum;
            for(uint256 t=w;t!=0;--t){uint256 expected=_expected(type(uint256).max,w,c,t);assertEq(e.ticket(t),expected);assertEq(e.take(t),expected);sum+=expected;}
            assertEq(sum,type(uint256).max);assertEq(e.liability(),0);assertEq(e.rawPath(4096),0);
            if(w<3000)assertEq(e.take(w+1),0);
            e.credit(w,w,0);for(uint256 t=1;t<=w;++t)assertEq(e.take(t),1);assertEq(e.liability(),0);
        }
    }
    function testQ03EnvelopeHomogeneousBooksToMixedWithAccruedAndPartialClaims() public {
        for(uint256 unit=2;unit<=3;++unit){
            Q03EnvelopeCoupledHost h=new Q03EnvelopeCoupledHost();
            uint256 count=unit==2?511:499;
            for(uint256 id=1;id<=count;++id)h.activate(id,unit);
            h.seedAccrued(1,29);h.seedAccrued(count,31);h.credit(2*count-2);
            uint256 beforeLast=h.claimable(count);assertGt(beforeLast,31);
            uint256 beforeFirst=h.claimable(1);assertEq(h.claim(1),beforeFirst);
            uint256 newcomer=count+1;h.activate(newcomer,1);assertEq(h.unit(),1);assertEq(h.claimable(newcomer),0);
            for(uint256 epoch;epoch<3;++epoch){h.credit(2*h.weight()-2+epoch);if(epoch==1)h.claim(newcomer);}
            uint256 sum;for(uint256 id=1;id<=newcomer;++id)sum+=h.claimable(id);assertEq(h.liability(),sum);
            for(uint256 id=newcomer;id!=0;--id){uint256 expected=h.claimable(id);assertEq(h.claim(id),expected);}
            assertEq(h.liability(),0);assertEq(h.claim(newcomer),0);assertEq(h.claim(1),0);
        }
    }
}
