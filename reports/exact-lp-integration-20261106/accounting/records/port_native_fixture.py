from pathlib import Path
r=Path.cwd();p=r/'test/VaultAccounting.t.sol';s=p.read_text()
start=s.index('contract VaultLiquidityMock is ERC721');end=s.index('contract RejectingMintReceiver',start)
venue=r'''/// @dev TEST ONLY normalized native-ETH/fixed-ZZZ venue. Fee minting and
/// repricing use local cheatcodes; this is neither real v4 nor market gas proof.
contract VaultLiquidityMock is ERC721, SinglePositionFixture {
    Vm private constant nativeVm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    MockToken public t0;MockToken public t1;uint256 public next=1;bool public failMint;uint256 public spendBps=10000;
    uint256 public fee0;uint256 public fee1;uint256 public repricingLP;uint256 public repricingGain;uint256 public closeLossBps;
    uint256 public balanceAmount0;uint256 public balanceAmount1;uint256 public balanceReportExtra0;bytes32 private balancingContext;
    mapping(uint256=>uint256)public a0;mapping(uint256=>uint256)public a1;
    constructor(address x,address y)ERC721("Mock venue","MV"){t0=MockToken(x);t1=MockToken(y);}
    receive()external payable{}
    function positionManager()external view returns(address){return address(this);}
    function balanceContext(bytes32)external view returns(bytes32){return balancingContext;}
    function setCloseLossBps(uint256 v)external{require(v<=10000);closeLossBps=v;}
    function setFees(uint256 x,uint256 y)external{fee0=x;fee1=y;}
    function setSpendBps(uint256 x)external{spendBps=x;}
    function setRepricing(uint256 id,uint256 gain)external{repricingLP=id;repricingGain=gain;}
    function setBalanceReportExtra0(uint256 x)external{balanceReportExtra0=x;}
    function setBalanceContext(bytes32 context)external{balancingContext=context;}
    function _native()private view returns(bool){return address(t0)==address(0);}
    function _send(address receiver,uint256 amount)private{if(amount==0)return;(bool ok,)=payable(receiver).call{value:amount}("");require(ok);}
    function _createNative(uint256 amount)private{nativeVm.deal(address(this),address(this).balance+amount);}
    function swap(bytes32,bool direction,uint256 amount,uint256,uint256)external payable returns(uint256){
        require(msg.value==(_native()&&direction?amount:0));return _swap(direction,amount,false);
    }
    function balance(bytes32 pool,uint256 lp,uint256 amount0,uint256 amount1,uint256)external payable returns(uint256 balanced0,uint256 balanced1){
        require(msg.value==(_native()?amount0:0));balanceAmount0=amount0;balanceAmount1=amount1;
        IZZZStrategy policy=IZZZStrategy(ZZZVault(payable(msg.sender)).access().module(Ids.STRATEGY));bool direction;uint256 input;
        if(lp==0)(direction,input,)=policy.swapPlan(pool,amount0,amount1);else(direction,input,)=policy.compoundPlan(ZZZVault(payable(msg.sender)).poolBucket(pool),amount0,amount1);
        balanced0=amount0+balanceReportExtra0;balanced1=amount1;
        if(input!=0){require(input<=(direction?amount0:amount1),"entrant budget");uint256 out=_swap(direction,input,true);if(direction){balanced0-=input;balanced1+=out;}else{balanced0+=out;balanced1-=input;}}
        if(_native())_send(msg.sender,balanced0-balanceReportExtra0);
    }
    function _swap(bool direction,uint256 amount,bool escrowed)private returns(uint256){
        if(direction){if(!_native())require(t0.transferFrom(msg.sender,address(this),amount));t1.mint(msg.sender,amount);}
        else{require(t1.transferFrom(msg.sender,address(this),amount));if(_native()){_createNative(amount);if(!escrowed)_send(msg.sender,amount);}else t0.mint(msg.sender,amount);}
        if(repricingLP!=0){a0[repricingLP]+=repricingGain;if(_native())_createNative(repricingGain);else t0.mint(address(this),repricingGain);}
        return amount;
    }
    function amounts(uint256 id)external view returns(uint256,uint256){return(a0[id],a1[id]);}
    function setFail(bool x)external{failMint=x;}
    function mint(bytes32,int24,int24,uint256 x,uint256 y,uint128,uint256)external payable returns(uint256 id,uint256 s0,uint256 s1){require(!failMint);id=next++;_mint(msg.sender,id);(s0,s1)=_fund(id,x,y);}
    function increase(bytes32,uint256 id,uint256 x,uint256 y,uint128,uint256)external payable returns(uint256,uint256){return _fund(id,x,y);}
    function _fund(uint256 id,uint256 x,uint256 y)private returns(uint256 s0,uint256 s1){
        require(msg.value==(_native()?x:0));s0=x*spendBps/10000;s1=y*spendBps/10000;
        if(!_native())require(t0.transferFrom(msg.sender,address(this),s0));require(t1.transferFrom(msg.sender,address(this),s1));a0[id]+=s0;a1[id]+=s1;
        if(_native())_send(msg.sender,x-s0);
    }
    function collect(bytes32,uint256,uint256)external{uint256 x=fee0;uint256 y=fee1;fee0=0;fee1=0;if(_native()){_createNative(x);_send(msg.sender,x);}else t0.mint(msg.sender,x);t1.mint(msg.sender,y);}
    function close(bytes32,uint256 id,uint256)external{uint256 x=a0[id]*(10000-closeLossBps)/10000;uint256 y=a1[id]*(10000-closeLossBps)/10000;delete a0[id];delete a1[id];_burn(id);if(_native())_send(msg.sender,x);else require(t0.transfer(msg.sender,x));require(t1.transfer(msg.sender,y));}
}
'''
s=s[:start]+venue+s[end:]
if 'import {Vm}' not in s:s=s.replace('pragma solidity 0.8.26;','pragma solidity 0.8.26;\nimport {Vm} from "forge-std/Vm.sol";',1)
s=s.replace('t0=new MockToken(0);t1=new MockToken(0);','t0=MockToken(address(0));t1=new MockToken(0);',1)
s=s.replace('rewards.addAsset(address(t0));rewards.addAsset(address(t1));','pools.setFixedZZZ(address(t1));rewards.addAsset(address(t1));',1)
s=s.replace('oracle.setTestFeed(address(t0),address(feed),3600);','oracle.setTestFeed(address(0),address(new MockFeed(8,1e26)),3600);',1)
s=s.replace('vm.deal(owner,1 ether);t0.mint(owner,100000);t1.mint(owner,100000);','vm.deal(owner,1 ether);t1.mint(owner,100000);',1)
s=s.replace('t0.approve(address(vault),type(uint256).max);','',1)
s=s.replace('vm.prank(owner);vault.activate(id,poolId,amount0,amount1,1,block.timestamp+100);','vm.prank(owner);vault.activate{value:amount0}(id,poolId,amount0,amount1,1,block.timestamp+100);',1)
s=s.replace('assertEq(rewards.paidIndex(dormantId,address(t0)),rewards.index(address(t0)));','assertEq(rewards.claimable(dormantId,address(0)),0);')
s=s.replace('contract VaultAccountingTest is PooledVaultFixture {','// Native fixture prices deliberately normalize1wei and1zero-decimal ZZZ to$1.\n// This preserves historical unit arithmetic, not production prices or gas.\ncontract VaultAccountingTest is PooledVaultFixture {')
p.write_bytes(s.encode())
print('Native-capable venue and native default fixture written; dependent body ports still pending')
