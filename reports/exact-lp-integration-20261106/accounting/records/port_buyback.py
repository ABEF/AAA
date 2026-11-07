from pathlib import Path
import re,json
p=Path('test/BuybackExecution.t.sol');s=p.read_bytes().decode()
# The only ERC20 is fixedZZZ. Destination-refusal remains a meaningful reserve
# transfer fault on that asset, rather than installing token behavior at ETH0.
s=s.replace('address public reentryTarget;\r\n    bool public reentrySucceeded;', 'address public blockedRecipient;\r\n    function blockRecipient(address value)external{blockedRecipient=value;}\r\n    function _update(address from,address to,uint256 amount)internal override{require(to==address(0)||to!=blockedRecipient,"fixture recipient blocked");super._update(from,to,amount);}\r\n    address public reentryTarget;\r\n    bool public reentrySucceeded;',1)
s=s.replace('input = new BuybackInputToken();','input=MockToken(address(0));')
s=s.replace('rewards.addAsset(address(input)); rewards.addAsset(address(zzz));','')
needle='pools.activationAssets().configureZZZ(address(zzz), address(zzz).codehash, keccak256("buyback fixture fixed ZZZ"));';s=s.replace(needle,needle+'rewards.addAsset(address(zzz));vm.deal(address(this),100_000 ether);')
s=s.replace('oracle.setTestFeed(address(third), address(inputFeed), 3600); rewards.addAsset(address(third));','oracle.setTestFeed(address(third),address(inputFeed),3600);')
s=s.replace('require(msg.value == 0 && synced == input, "fixture wrong input");\r\n        paid = IERC20(input).balanceOf(address(this)) - beforeSync;', 'if(input==address(0)){paid=msg.value;}else{require(msg.value==0&&synced==input,"fixture wrong input");paid=IERC20(input).balanceOf(address(this))-beforeSync;}')
s=s.replace('function sync(address token) external { synced = token; beforeSync = IERC20(token).balanceOf(address(this)); }','function sync(address token)external{synced=token;beforeSync=token==address(0)?address(this).balance:IERC20(token).balanceOf(address(this));}')
a=s.index('    function _fund(address token');b=s.index('    function _execute(',a)
s=s[:a]+'''    function _fund(address token,uint256 amount)private{
        if(token==address(zzz)){
            zzz.mint(address(vault),amount);vm.startPrank(address(vault));zzz.approve(address(fees),amount);fees.allocate(BUCKET,token,amount);vm.stopPrank();
        }else{require(token==address(0));vm.deal(address(vault),address(vault).balance+amount);vm.prank(address(vault));fees.allocate{value:amount}(BUCKET,address(0),amount);}
    }
    function _assetBalance(address asset,address account)private view returns(uint256){return asset==address(0)?account.balance:IERC20(asset).balanceOf(account);}
'''+s[b:]
s=re.sub(r'input\.balanceOf\((address\([^()]*\))\)',r'\1.balance',s)
s=s.replace('IERC20(token).balanceOf(address(fees))','_assetBalance(token,address(fees))').replace('IERC20(token).balanceOf(address(rewards))','_assetBalance(token,address(rewards))')
s=s.replace('input.balanceOf(address(core))','address(core).balance').replace('input.balanceOf(address(manager))','address(manager).balance')
s=s.replace('            address(buyback).balance, input.allowance(address(buyback), address(manager)),','            address(buyback).balance,')
s=re.sub(r'\s*assertEq\(input\.allowance\(address\(buyback\), address\(manager\)\), 0\);','',s)
s=s.replace('input.mint(address(buyback), 13 ether);','vm.deal(address(buyback),address(buyback).balance+13 ether);')
s=s.replace('_fund(address(input), GROSS); BuybackInputToken(address(input)).blockRecipient(address(buyback));','_fund(address(zzz),GROSS);zzz.blockRecipient(address(buyback));')
a=s.index('    function testReserveTransferFailure');b=s.index('    function testNoOpBurn',a);part=s[a:b].replace('address(input)','address(zzz)').replace('BuybackInputToken(address(zzz)).blockRecipient(address(0));','zzz.blockRecipient(address(0));');s=s[:a]+part+s[b:]
s=s.replace('// TEST ONLY ERC20 admission; production permits only native ETH/ZZZ LP.','// Synthetic registry fixture; the fresh pair here is native ETH/fixed ZZZ.')
# Obsolete token-specific helper no longer has any callers after native input port.
a=s.index('/// @dev TEST ONLY: simulate an admitted token refusing one transfer destination.');b=s.index('/// @dev TEST ONLY: deterministic v4 settlement',a);s=s[:a]+s[b:]
p.write_bytes(s.encode())
# Retire precisely the obsolete full-Vault WETH/ZZZ block; keep all primitive
# pinned fork methods and transport checks above it. Archive original already exists.
p=Path('test/UniswapV4Fork.t.sol');s=p.read_bytes().decode();a=s.index('    // TEST ONLY: an empty migration plan.');b=s.index('    function onERC721Received(',a);removed=s[a:b];s=s[:a]+'''    // Historical full-Vault WETH/ZZZ shared-entry/rebalance fixture retired from
    // fresh profile7. Original64f9bfb retained in audit maintenance evidence.
    // CurrentNativePoolFork and local native-v4 suites cover the fresh pair.

'''+s[b:];p.write_bytes(s.encode())
E=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/exact-lp-integration-20261106/accounting-agent');(E/'RETIRED_WETH_VAULT_FORK.sol.txt').write_text(removed);(E/'RETIRED_FORK.json').write_text(json.dumps({'original_commit':'64f9bfb1b0db28c9c8eafc42394afad2263637b6','file':'test/UniswapV4Fork.t.sol','retired_methods':['testRealSharedPoolEntryUsesOneLPAndPostSwapSharePricing','testRealSharedPoolRebalanceChangesOneLPAndPreservesAllShares'],'reason':'FullVaultWETH/ZZZ+twoERC20LPassets incompatiblewithfreshnativeETH/fixedZZZ exact7;alltypedManager/token/oracleforkprimitivesretained','archive':'baseline/test/UniswapV4Fork.t.sol','retired_block':'RETIRED_WETH_VAULT_FORK.sol.txt','not_a_fork_pass':True},indent=2))
print('Native buyback fixture and exact obsolete fork block retirement written')
