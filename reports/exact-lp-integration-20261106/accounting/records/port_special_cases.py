from pathlib import Path
import re
R=Path.cwd();E=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/exact-lp-integration-20261106/accounting-agent')
def rd(n):return (R/'test'/n).read_bytes().decode()
def wr(n,s):(R/'test'/n).write_bytes(s.encode())
def swap(s):return re.sub(r'\bt1\b','t0',re.sub(r'\bt0\b','SWAP_TOKEN',s)).replace('SWAP_TOKEN','t1')
p='VaultAccounting.t.sol';s=rd(p).replace('address feed,uint64 age','address feed,uint32 age');wr(p,s)
p='LPOnlyEntryBoundary.t.sol';s=(E/'baseline/test'/p).read_bytes().decode();s=swap(s)
s=s.replace('vault.activate(entrant,other,1000,1000,1,block.timestamp+100)','vault.activate{value:1000}(entrant,other,1000,1000,1,block.timestamp+100)')
s=s.replace('assertEq(rewards.index(address(t1)),0);','(uint256 treeWeight,,)=rewards.allocationTree(0);assertEq(treeWeight,2);')
wr(p,s)
p='ContributionBudgetIsolation.t.sol';s=rd(p).replace('vm.etch(address(t0)','vm.etch(address(t1)').replace('ContributionContextCallbackToken(address(t0))','ContributionContextCallbackToken(address(t1))');wr(p,s)
p='GlobalMembershipDust.t.sol';s=rd(p);start=s.index('    function testHistoricalDustPaymentFailure');end=s.index('    function testFundedDust',start)
part=s[start:end].replace('setFees(19,0)','setFees(0,19)').replace('address(t0)','address(t1)').replace('address(address(fees)).balance','t1.balanceOf(address(fees))');s=s[:start]+part+s[end:];wr(p,s)
p='KeeperCompletion.t.sol';s=rd(p).replace('uint256 supply0 = t0.totalSupply();','uint256 nativeBacking = address(adversary).balance;').replace('assertEq(t0.totalSupply(), supply0);','assertEq(address(adversary).balance, nativeBacking);');wr(p,s)
p='GovernedExecutionLoss.t.sol';s=rd(p).replace('vm.etch(address(t0)','vm.etch(address(t1)').replace('LossPolicyCallbackToken(address(t0))','LossPolicyCallbackToken(address(t1))')
start=s.index('    function test',s.index('vm.etch')) if False else 0
# Only the callback test must pull the callback-capable ZZZ rather than native ETH.
at=s.index('vm.etch');a=s.rfind('    function ',0,at);b=s.index('    function ',at);part=s[a:b].replace('activate{value:1000}(id, poolId, 1000, 0','activate{value:0}(id, poolId, 0, 1000').replace('uint256 before=address(alice).balance','uint256 before=t1.balanceOf(alice)').replace('assertEq(address(alice).balance,before)','assertEq(t1.balanceOf(alice),before)');s=s[:a]+part+s[b:];wr(p,s)
# Native-capable adversarial venue: real escrow/refund and explicit fixture-only
# synthetic fee/loss units. No ERC20 behavior is installed at native address0.
p='MigrationBudgetAdversarial.t.sol';s=rd(p)
s=s.replace('import {ERC721}', 'import {Vm} from "forge-std/Vm.sol";\nimport {ERC721}',1)
s=s.replace('MockToken private immutable token0;','''Vm private constant nativeVm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    MockToken private immutable token0;''',1)
pos=s.index('    function positionManager()')
s=s[:pos]+'''    receive()external payable{}
    function _native()private view returns(bool){return address(token0)==address(0);}
    function _send0(address recipient,uint256 value)private{if(value!=0){(bool ok,)=payable(recipient).call{value:value}("");require(ok);}}
    function _burn0(uint256 value)private{if(_native())nativeVm.deal(address(this),address(this).balance-value);else token0.burn(value);}
    function _mint0(address recipient,uint256 value)private{if(_native())nativeVm.deal(recipient,recipient.balance+value);else token0.mint(recipient,value);}
'''+s[pos:]
s=s.replace('external returns (uint256 id, uint256 used0, uint256 used1)', 'external payable returns (uint256 id, uint256 used0, uint256 used1)',1)
s=s.replace('require(token0.transferFrom(msg.sender, address(this), used0));','if(_native()){require(msg.value==a);_send0(msg.sender,a-used0);}else require(token0.transferFrom(msg.sender, address(this), used0));',1)
s=s.replace('token0.burn(mintLoss0);','_burn0(mintLoss0);').replace('token0.burn(harvestLoss0);','_burn0(harvestLoss0);').replace('token0.burn(closeLoss0);','_burn0(closeLoss0);')
s=s.replace('token0.mint(msg.sender, a);','_mint0(msg.sender,a);')
s=s.replace('require(token0.transfer(msg.sender, a));','if(_native())_send0(msg.sender,a);else require(token0.transfer(msg.sender, a));')
a=s.index('    function balance(bytes32 pool');b=s.index('\n}\n\ncontract BudgetAdversarialPolicy',a)
s=s[:a]+'''    function balance(bytes32 pool,uint256,uint256 a,uint256 b,uint256)
        external payable returns(uint256 balanced0,uint256 balanced1) {
        require(msg.value==(_native()?a:0));
        IZZZStrategy strategy=IZZZStrategy(ZZZVault(payable(msg.sender)).access().module(Ids.STRATEGY));
        (bool direction,uint256 input,)=strategy.swapPlan(pool,a,b);
        balanced0=a;balanced1=b;
        if(input!=0){require(direction&&input<=a);uint256 output=_swap(input);balanced0-=input;balanced1+=output;}
        if(_native())_send0(msg.sender,balanced0);
    }
    function swap(bytes32,bool zeroForOne,uint256 input,uint256,uint256)external payable returns(uint256){
        require(zeroForOne&&msg.value==(_native()?input:0));return _swap(input);
    }
    function _swap(uint256 input)private returns(uint256){
        ++swapCount;if(!_native())require(token0.transferFrom(msg.sender,address(this),input));
        token1.mint(msg.sender,swapOutput);return swapOutput;
    }
'''+s[b:];wr(p,s)
# Derived growth mock must escrow native ETH and remove explicit simulated loss.
p='GovernedExecutionLoss.t.sol';s=rd(p)
s=s.replace('external returns(uint256 used0,uint256 used1)', 'external payable returns(uint256 used0,uint256 used1)',1)
s=s.replace('require(first.transferFrom(msg.sender,address(this),a));','if(address(first)==address(0))require(msg.value==a);else require(first.transferFrom(msg.sender,address(this),a));',1)
s=s.replace('first.burn(mintLoss0);','if(address(first)==address(0))vmBurn(mintLoss0);else first.burn(mintLoss0);',1)
s=s.replace('contract GovernedGrowthLossVenue is BudgetAdversarialVenue {','''contract GovernedGrowthLossVenue is BudgetAdversarialVenue {
    function vmBurn(uint256 amount)private{Vm(address(uint160(uint256(keccak256("hevm cheat code"))))).deal(address(this),address(this).balance-amount);}''')
s=s.replace('pragma solidity 0.8.26;','pragma solidity 0.8.26;\nimport {Vm} from "forge-std/Vm.sol";',1);wr(p,s)
print('Corrected callback domains, native adversarial venue, zero-asset fault cases')
