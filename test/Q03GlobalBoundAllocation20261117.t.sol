// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {Q03GlobalBoundAllocation as Global} from "./fixtures/Q03GlobalBoundAllocation.sol";
import {Q03PositiveAllocationBaseline as Positive,Q03ComplementAllocation as Counter}
    from "./fixtures/Q03ComplementAllocation.sol";

/// @dev Controlled caller-model, not an NFT/token/canonical deployment. Only
/// this creator can supply funding or activation/import seeds. Every engine
/// credit captures its own same-asset liability; no caller-supplied bound exists.
contract Q03CoupledGlobalHost {
    using Global for Global.Book;
    using Positive for Positive.Book;
    address private immutable controller=msg.sender;
    mapping(address=>mapping(uint256=>Global.Book)) private books;
    mapping(address=>mapping(uint256=>Positive.Book)) private referenceBooks;
    mapping(uint256=>uint256) public weightOf;
    mapping(uint256=>uint256) public first;
    mapping(uint256=>mapping(address=>uint256)) public accrued;
    mapping(address=>uint256) public liabilities;
    mapping(address=>uint256) public cash;
    mapping(address=>uint256) public cursor;
    uint256 public totalWeight;
    uint256 private kinds;
    modifier onlyController(){require(msg.sender==controller,"controlled seed/funding only");_;}
    function activate(uint256 id,uint256 weight) external onlyController{
        require(weight!=0&&weight<=3&&weightOf[id]==0);
        first[id]=totalWeight+1;weightOf[id]=weight;totalWeight+=weight;kinds|=1<<weight;
    }
    function unit() public view returns(uint256){
        if((kinds&2)!=0||(kinds&12)==12)return 1;
        if((kinds&4)!=0)return 2;
        return (kinds&8)!=0?3:0;
    }
    function importAccrued(uint256 id,address asset,uint256 amount) external onlyController{
        require(weightOf[id]!=0);accrued[id][asset]+=amount;liabilities[asset]+=amount;cash[asset]+=amount;
    }
    function distribute(address asset,uint256 amount) external onlyController{
        uint256 u=unit();uint256 beforeCursor=cursor[asset];
        require(u!=0&&beforeCursor%u==0);
        (uint256 next,uint256 liability)=books[asset][u].credit(amount,totalWeight/u,beforeCursor/u,liabilities[asset]);
        require(next==referenceBooks[asset][u].credit(amount,totalWeight/u,beforeCursor/u));
        liabilities[asset]=liability;cash[asset]+=amount;cursor[asset]=next*u;
    }
    function claimable(uint256 id,address asset) public view returns(uint256 amount){
        amount=accrued[id][asset];uint256 start=first[id];uint256 weight=weightOf[id];
        for(uint256 i;i<weight;++i){
            uint256 value=books[asset][1].viewTicket(start+i);
            require(value==referenceBooks[asset][1].viewTicket(start+i));amount+=value;
        }
        if(weight>1){
            uint256 value=books[asset][weight].viewTicket((start-1)/weight+1);
            require(value==referenceBooks[asset][weight].viewTicket((start-1)/weight+1));amount+=value;
        }
    }
    function claim(uint256 id,address asset) external returns(uint256 amount){
        uint256 liability=liabilities[asset];amount=accrued[id][asset];
        uint256 start=first[id];uint256 weight=weightOf[id];
        for(uint256 i;i<weight;++i){
            uint256 value=books[asset][1].takeTicket(start+i,liability-amount);
            require(value==referenceBooks[asset][1].takeTicket(start+i));amount+=value;
        }
        if(weight>1){
            uint256 key=(start-1)/weight+1;
            uint256 value=books[asset][weight].takeTicket(key,liability-amount);
            require(value==referenceBooks[asset][weight].takeTicket(key));amount+=value;
        }
        accrued[id][asset]=0;liabilities[asset]-=amount;cash[asset]-=amount;
    }
}

/// @dev Raw library seam for invalid caller-budget checks. This is not the
/// production API; an authentic caller must derive its own liability argument.
contract Q03RawGlobalHost {
    using Global for Global.Book;
    Global.Book private book;
    function credit(uint256 a,uint256 w,uint256 c,uint256 l) external returns(uint256,uint256){return book.credit(a,w,c,l);}
    function range(uint256 l,uint256 h,uint256 d,uint256 beforeL) external returns(uint256){return book.addRange(l,h,d,beforeL);}
    function take(uint256 t,uint256 available) external returns(uint256){return book.takeTicket(t,available);}
    function ticket(uint256 t) external view returns(uint256){return book.viewTicket(t);}
}

contract Q03PositiveGasHost {
    using Positive for Positive.Book;Positive.Book private book;uint256 private liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256){liability+=a;return book.credit(a,w,c);}
}
contract Q03CounterGasHost {
    using Counter for Counter.Book;Counter.Book private book;uint256 private liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256){liability+=a;return book.credit(a,w,c);}
}
contract Q03GlobalGasHost {
    using Global for Global.Book;Global.Book private book;uint256 private liability;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256 next){
        uint256 newLiability;(next,newLiability)=book.credit(a,w,c,liability);liability=newLiability;
    }
}

contract Q03GlobalBoundAllocation20261117Test is Test {
    address private constant ETH=address(0);
    address private constant OTHER=address(0xC012);
    Q03CoupledGlobalHost private host;
    mapping(address=>mapping(uint256=>uint256)) private expected;
    function _fresh() private{host=new Q03CoupledGlobalHost();}
    function _credit(address asset,uint256 amount) private{
        uint256 u=host.unit();uint256 w=host.totalWeight()/u;uint256 c=host.cursor(asset)/u;
        for(uint256 id=1;id<=4;++id){
            uint256 weight=host.weightOf(id);if(weight==0)continue;
            uint256 start=(host.first(id)-1)/u+1;uint256 count=weight/u;
            for(uint256 t=start;t<start+count;++t){
                uint256 distance=(t-1+w-c)%w;
                expected[asset][id]+=amount/w+(distance<amount%w?1:0);
            }
        }
        host.distribute(asset,amount);_check(asset);
    }
    function _import(uint256 id,address asset,uint256 amount) private{
        expected[asset][id]+=amount;host.importAccrued(id,asset,amount);_check(asset);
    }
    function _check(address asset) private view{
        uint256 sum;
        for(uint256 id=1;id<=4;++id){assertEq(host.claimable(id,asset),expected[asset][id]);sum+=expected[asset][id];}
        assertEq(host.liabilities(asset),sum);assertEq(host.cash(asset),sum);
    }
    function _claim(uint256 id,address asset) private returns(uint256 amount){
        amount=expected[asset][id];assertEq(host.claim(id,asset),amount);expected[asset][id]=0;_check(asset);
    }

    function testQ03GlobalRareUnitToMixedKeepsImportedAndOtherCurrencyRights() public{
        _fresh();host.activate(1,2);host.activate(2,2);
        _import(1,ETH,13);_import(2,ETH,17);_import(2,OTHER,23);
        _credit(ETH,101);_credit(OTHER,19);_claim(1,ETH);
        host.activate(3,1);assertEq(host.unit(),1);
        _credit(ETH,99);_credit(OTHER,103);
        _claim(3,OTHER);_claim(2,ETH);_claim(1,OTHER);_claim(1,ETH);_claim(3,ETH);_claim(2,OTHER);
        assertEq(host.liabilities(ETH),0);assertEq(host.liabilities(OTHER),0);
        assertEq(host.claim(1,ETH),0);assertEq(host.claim(2,OTHER),0);
    }

    function testQ03GlobalLegendaryUnitToMixedPartialClaimsAndLongRecredit() public{
        _fresh();host.activate(1,3);host.activate(2,3);
        _import(1,ETH,11);_import(2,ETH,17);_credit(ETH,9);_claim(2,ETH);
        host.activate(3,2);assertEq(host.unit(),1);
        for(uint256 epoch;epoch<16;++epoch){
            _credit(ETH,2*host.totalWeight()-2+epoch);
            if(epoch%3==0)_claim(1,ETH);
            if(epoch%4==0)_claim(3,ETH);
        }
        _claim(3,ETH);_claim(1,ETH);_claim(2,ETH);
        assertEq(host.liabilities(ETH),0);_credit(ETH,1);_claim(2,ETH);_claim(1,ETH);_claim(3,ETH);
        assertEq(host.cash(ETH),0);
    }

    function testQ03GlobalUintMaximumAcrossAccruedAndBooksCannotOvercredit() public{
        _fresh();for(uint256 id=1;id<=4;++id)host.activate(id,1);
        _import(1,ETH,type(uint256).max-999);_credit(ETH,999);
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));host.distribute(ETH,1);_check(ETH);
        _claim(2,ETH);_claim(4,ETH);_claim(1,ETH);_claim(3,ETH);assertEq(host.liabilities(ETH),0);
        _credit(ETH,type(uint256).max);_claim(4,ETH);_claim(1,ETH);_claim(3,ETH);_claim(2,ETH);
        assertEq(host.liabilities(ETH),0);assertEq(host.cash(ETH),0);
    }

    function testQ03GlobalUnderfundedBoundAndInvalidCreditRollbackBeforeRetry() public{
        Q03RawGlobalHost raw=new Q03RawGlobalHost();
        (uint256 c,uint256 l)=raw.credit(7,4,3,0);assertEq(c,2);assertEq(l,7);
        uint256[4] memory beforeValues;
        for(uint256 t=1;t<=4;++t)beforeValues[t-1]=raw.ticket(t);
        vm.expectRevert(Global.InvalidAllocation.selector);raw.take(4,1);
        for(uint256 t=1;t<=4;++t)assertEq(raw.ticket(t),beforeValues[t-1]);
        assertEq(raw.take(4,2),2);assertEq(raw.take(4,0),0);
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));raw.credit(1,4,c,type(uint256).max);
        vm.expectRevert(Global.InvalidAllocation.selector);raw.credit(0,0,0,0);
        vm.expectRevert(Global.InvalidAllocation.selector);raw.credit(0,3001,0,0);
        vm.expectRevert(Global.InvalidAllocation.selector);raw.credit(0,4,4,0);
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));raw.range(1,250,type(uint256).max,0);
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));raw.range(1,1,1,type(uint256).max);
        assertEq(raw.ticket(1),beforeValues[0]);assertEq(raw.ticket(2),beforeValues[1]);assertEq(raw.ticket(3),beforeValues[2]);
        uint256 paid=2;for(uint256 t=1;t<=3;++t)paid+=raw.take(t,7-paid);assertEq(paid,7);
        assertEq(raw.ticket(5),0);
    }

    function testQ03GlobalCoupledColdCreditIncludesSameAssetLiabilityOnAllControls() public{
        vm.pauseGasMetering();uint256[2] memory weights=[uint256(1023),1499];
        for(uint256 i;i<weights.length;++i){
            uint256 w=weights[i];uint256 a=2*w-2;
            Q03PositiveGasHost positive=new Q03PositiveGasHost();Q03CounterGasHost counter=new Q03CounterGasHost();Q03GlobalGasHost global=new Q03GlobalGasHost();
            vm.cool(address(positive));vm.cool(address(counter));vm.cool(address(global));
            vm.resumeGasMetering();uint256 start=gasleft();uint256 p=positive.credit(a,w,513);uint256 pg=start-gasleft();
            start=gasleft();uint256 b=counter.credit(a,w,513);uint256 bg=start-gasleft();
            start=gasleft();uint256 g=global.credit(a,w,513);uint256 gg=start-gasleft();vm.pauseGasMetering();
            assertEq(p,b);assertEq(p,g);assertLt(gg,bg);assertLt(gg,pg);assertGt(bg-gg,20_000);
            emit log_named_uint("global experiment weight",w);
            emit log_named_uint("positive plus existing liability cold gas",pg);
            emit log_named_uint("counter plus existing liability cold gas",bg);
            emit log_named_uint("global plus existing liability cold gas",gg);
            emit log_named_uint("additional saved versus duplicate counter",bg-gg);
        }
        vm.resumeGasMetering();
    }
}
