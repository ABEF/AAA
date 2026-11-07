from pathlib import Path
p=Path('test/ProductionGas.t.sol');s=p.read_bytes().decode()
s=s.replace('for (uint256 i; i < assetCount; ++i) tokens.push(new MockToken(0));','require(assetCount==2);tokens.push(MockToken(address(0)));tokens.push(new MockToken(0));')
s=s.replace('oracle.setTestFeed(address(tokens[0]), address(feed), 3600);','oracle.setTestFeed(address(0),address(new MockFeed(8,1e26)),3600);')
s=s.replace('for (uint256 i; i < assetCount; ++i) rewards.addAsset(address(tokens[i]));','pools.setFixedZZZ(address(tokens[1]));rewards.addAsset(address(tokens[1]));')
s=s.replace('tokens[0].mint(OWNER, 10_000_000);','').replace('tokens[0].approve(address(vault), type(uint256).max);','')
s=s.replace('vault.activate(previous,','vault.activate{value:1000}(previous,').replace('vault.activate(id,','vault.activate{value:1000}(id,').replace('vault.increase(id,','vault.increase{value:100}(id,')
s=s.replace('vm.prank(address(membership));','').replace('rewards.checkpointAll(id);','rewards.claimableComponents(id,address(0));').replace('"checkpointAll"','"claimableComponents"')
a=s.index('    function testGasMaximum32FundedRewardAssets()');s=s[:a]+'''    /// @notice Fresh profile7 has exactly native ETH and fixed ZZZ, not32 LP assets.
    function testGasMaximumTwoFundedLPBooks()public{
        uint256 id=_runCollectionWorkload(1000,2);uint256 bucket=vault.nftBucket(id);
        vm.deal(address(fees),address(fees).balance+900_000);
        vm.prank(address(fees));rewards.creditPool{value:900_000}(bucket,address(0),800_000,100_000);
        tokens[1].mint(address(fees),900_000);
        vm.startPrank(address(fees));tokens[1].approve(address(rewards),900_000);
        rewards.creditPool(bucket,address(tokens[1]),800_000,100_000);vm.stopPrank();
        _cool();uint256 start=gasleft();rewards.claimableComponents(id,address(0));
        _report("collection.1000.assets.2.funded","claimableComponents",start-gasleft());
        _cool();vm.startPrank(OWNER);start=gasleft();
        uint256 ethClaim=rewards.claim(id,address(0));uint256 zzzClaim=rewards.claim(id,address(tokens[1]));
        uint256 spent=start-gasleft();vm.stopPrank();
        assertGt(ethClaim,0);assertGt(zzzClaim,0);assertEq(rewards.assetCount(),2);
        _report("collection.1000.assets.2.funded","claimTwoBatchedCalls",spent);
    }
}
''';p.write_bytes(s.encode())
p=Path('test/CombinedCapacityGas.t.sol');s=p.read_bytes().decode()
s=s.replace('import {Test}', 'import {Vm} from "forge-std/Vm.sol";\nimport {Test}',1)
s=s.replace('    MockPools private immutable pools;','''    Vm private constant nativeVm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    MockPools private immutable pools;
    receive()external payable{}
    function _send(address to,uint256 value)private{if(value!=0){(bool ok,)=payable(to).call{value:value}("");require(ok);}}
''',1)
s=s.replace('function balance(bytes32,uint256,uint256 a0,uint256 a1,uint256) external pure returns(uint256,uint256) {','function balance(bytes32,uint256,uint256 a0,uint256 a1,uint256) external payable returns(uint256,uint256) {\n        require(msg.value==a0);_send(msg.sender,a0);')
s=s.replace('external returns (uint256 id, uint256 spent0, uint256 spent1)', 'external payable returns (uint256 id, uint256 spent0, uint256 spent1)',1)
s=s.replace('external returns (uint256, uint256)', 'external payable returns (uint256, uint256)',1)
s=s.replace('require(IERC20(config.key.currency0).transferFrom(msg.sender, address(this), a0));','require(config.key.currency0==address(0)&&msg.value==a0);')
s=s.replace('MockToken(config.key.currency0).mint(msg.sender, value);','nativeVm.deal(address(this),address(this).balance+value);_send(msg.sender,value);')
s=s.replace('and the default 16 ERC20 royalty assets plus native ETH.', 'and the default16 ERC20 royalty assets plus native ETH.')
s=s.replace('32 admitted LP reward assets','two fixed LP reward books')
s=s.replace('for (uint256 i; i < 32; ++i) {','for (uint256 i; i < 16; ++i) {',1)
s=s.replace('            rewards.addAsset(address(token));','')
s=s.replace('        CanonicalFixture.bind(address(access));','''        pools.setFixedZZZ(address(tokens[0]));rewards.addAsset(address(tokens[0]));
        oracle.setTestFeed(address(0),address(new MockFeed(8,1e26)),7200);
        CanonicalFixture.bind(address(access));''',1)
s=s.replace('address first = address(tokens[i * 2]);\r\n            address second = address(tokens[i * 2 + 1]);\r\n            if (first > second) (first, second) = (second, first);','address first=address(0);address second=address(tokens[0]);')
s=s.replace('PoolKey(first, second, 3000, 60','PoolKey(first, second, uint24(3000+i), 60')
s=s.replace('vault.activate(id, pool,','vault.activate{value:1000}(id, pool,')
s=s.replace('assertEq(rewards.assetCount(), 33);','assertEq(rewards.assetCount(), 2);')
a=s.index('    function _assertHistoricalFundingExcluded()');b=s.index('    function testColdActivationAtCombined',a)
s=s[:a]+'''    function _lpAsset(uint256 i)private view returns(address){return i==0?address(0):address(tokens[0]);}
    function _seedBooks(uint256 bucket)private{
        vm.deal(address(fees),address(fees).balance+900);
        vm.prank(address(fees));rewards.creditPool{value:900}(bucket,address(0),800,100);
        tokens[0].mint(address(fees),900);vm.startPrank(address(fees));
        tokens[0].approve(address(rewards),900);rewards.creditPool(bucket,address(tokens[0]),800,100);vm.stopPrank();
    }
    function _assertHistoricalFundingExcluded()private view{
        for(uint256 i;i<2;++i){address asset=_lpAsset(i);
            assertEq(rewards.liabilities(asset),3676);
            assertEq(rewards.claimable(entrant,asset),0);
            for(uint256 j;j<4;++j){assertEq(fees.dust(vault.nftBucket(incumbents[j]),asset),0);assertEq(rewards.claimable(incumbents[j],asset),919);}
        }
        for(uint256 i;i<16;++i){address asset=address(tokens[i]);assertEq(royalties.claimable(entrant,asset),0);assertEq(royalties.claimable(incumbents[0],asset),400);}
        assertEq(royalties.claimable(entrant,address(0)),0);assertEq(royalties.claimable(incumbents[0],address(0)),4 ether);
    }

'''+s[b:]
s=s.replace('vault.activate(entrant, poolIds[0],','vault.activate{value:1000}(entrant, poolIds[0],').replace('vault.increase(incumbents[0],','vault.increase{value:100}(incumbents[0],')
s=s.replace('32-assets','2-books').replace('32-indexed-assets','2-exact-books')
a=s.index('        for (uint256 i; i < 32; ++i)',s.index('    function _fullyIndexedOperation'));b=s.index('        vm.resumeGasMetering();',a)
s=s[:a]+'''        _seedBooks(bucket);
        for(uint256 i;i<2;++i){(uint256 personal,uint256 shared)=rewards.claimableComponents(incumbents[0],_lpAsset(i));assertGt(personal,0);assertGt(shared,0);}
'''+s[b:]
a=s.index('        for (uint256 i; i < 32; ++i)',s.index('    function _fullyIndexedOperation'));b=s.index('        assertEq(royalties.claimable(entrant, address(0)), 0);',a)
s=s[:a]+'''        for(uint256 i;i<2;++i){address asset=_lpAsset(i);assertEq(rewards.claimable(entrant,asset),0);
            assertEq(rewards.liabilities(asset),4576);assertEq(rewards.claimable(incumbents[0],asset),1744);
            for(uint256 j;j<4;++j)assertEq(fees.dust(vault.nftBucket(incumbents[j]),asset),0);
        }
        for(uint256 i;i<16;++i){assertEq(royalties.claimable(entrant,address(tokens[i])),0);assertEq(royalties.claimable(incumbents[0],address(tokens[i])),400);}
'''+s[b:]
s=s.replace('testColdActivationWithEveryHistoricalRewardIndexPopulated','testColdActivationWithBothExactRewardBooksFunded').replace('testColdIncumbentTopUpWithEveryHistoricalRewardIndexPopulated','testColdIncumbentTopUpWithBothExactRewardBooksFunded')
a=s.index('        for (uint256 i; i < 32; ++i)',s.index('function testSixteenOptionalFaults'));b=s.index('        for (uint256 i; i < 16; ++i) Capacity',a)
s=s[:a]+'        _seedBooks(bucket);\n'+s[b:]
s=s.replace('uint256 balance0 = IERC20(first).balanceOf(ENTRANT);','uint256 balance0=ENTRANT.balance;')
s=s.replace('IERC20(first).balanceOf(ENTRANT)','ENTRANT.balance')
s=s.replace('call{gas: LOCAL_GAS_BUDGET}(payload)','call{gas:LOCAL_GAS_BUDGET,value:1000}(payload)').replace('call{gas:localFaultBudget}(payload)','call{gas:localFaultBudget,value:1000}(payload)')
s=s.replace('for (uint256 i; i < 32; ++i) assertEq(rewards.claimable(entrant,address(tokens[i])),0,"No historical LP fee theft");','for(uint256 i;i<2;++i)assertEq(rewards.claimable(entrant,_lpAsset(i)),0,"No historical LP fee theft");')
s=s.replace('Every owner/global index','Both exact-unit books').replace('one venue earns 32 assets','the native/fixed-ZZZ pair earns any third asset').replace('Fully indexed capacity','Both-book capacity')
p.write_bytes(s.encode());print('Gas fixtures now fixed native+ZZZ books; sixteen separate royalty currencies preserved')
