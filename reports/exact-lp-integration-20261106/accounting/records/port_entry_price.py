from pathlib import Path
import re
p=Path('test/AtomicActivationIntegration.t.sol');s=p.read_bytes().decode()
s=s.replace('import {MockToken,MockFeed}', 'import {ZZZRewards} from "../src/ZZZRewards.sol";\nimport {MockToken,MockFeed}',1)
a=s.index('        // The inherited accounting fixture');b=s.index('        poolId=registry.configure(config);ac.seal();',a)
s=s[:a]+'''        // Explicit native ETH/fixed18-decimal ZZZ. This venue does not model
        // actual-v4 ratio/routing; actual core suites cover that separately.
        t0=MockToken(address(0));t1=new MockToken(18);
        venue=new VaultLiquidityMock(address(0),address(t1));ac.bind(Ids.LIQUIDITY,address(venue));
        MockFeed feed=new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(feed),3600);oracle.setTestFeed(address(t1),address(feed),3600);
        t1.mint(alice,10000e18);t1.mint(bob,10000e18);
        registry=new ZZZPoolRegistry(address(ac));ac.bind(Ids.POOLS,address(registry));
        assets=registry.activationAssets();entry=registry.activationEntry();
        assets.configureZZZ(address(t1),address(t1).codehash,REVIEW);
        rewards=new ZZZRewards(address(ac));ac.bind(Ids.REWARDS,address(rewards));rewards.addAsset(address(t1));
        PoolConfig memory config=PoolConfig(PoolKey(address(0),address(t1),3000,60,address(0)),
            true,true,1000,300,100,100,600,1e18,1e30);
'''+s[b:]
# Entry's tested input is fixed ZZZ, so preserve exact approval/refund scenarios.
a=s.index('    function _request');s=s[:a]+re.sub(r'\bt0\b','t1',s[a:])
s=s.replace('assertEq(t1.balanceOf(address(entry)),0);assertEq(t1.balanceOf(address(entry)),0);','assertEq(address(entry).balance,0);assertEq(t1.balanceOf(address(entry)),0);')
s=s.replace('venue.a0(lp),100e18','venue.a1(lp),100e18').replace('venue.a1(lp),0','venue.a0(lp),0').replace('venue.a0(lp),105e18','venue.a1(lp),105e18').replace('venue.a0(lp),99e18','venue.a1(lp),99e18').replace('group(bucket).idle0,1e18','group(bucket).idle1,1e18')
s=s.replace('r.sourceAsset=address(t1);','r.sourceAsset=address(new MockToken(18));')
s=s.replace('This synthetic ERC20 pair isolates share,','This synthetic native-ETH/fixed-ZZZ pair isolates share,')
p.write_bytes(s.encode())
# Specific price/callback suite now prices fixedZZZ; native earlier compound
# is the second existing book, not an arbitrary admitted third currency.
p=Path('test/ContributionPriceSecurity.t.sol');s=p.read_bytes().decode()
s=s.replace('historical=new MockToken(0); historicalPrimary=new MockFeed(8,1e8);','historical=MockToken(address(0)); historicalPrimary=new MockFeed(8,1e26);')
s=s.replace('MockFeed second=new MockFeed(8,1e8);','MockFeed second=new MockFeed(8,1e26);')
s=s.replace('        rewards.addAsset(address(historical));','        // Native ETH is already the second and final admitted LP book.')
s=s.replace('historical.mint(address(fees),100);','_giftNative(address(fees),100);')
s=s.replace('historical.balanceOf(address(fees))','address(fees).balance')
# All one-currency execution inputs must actually pull the callback-capable ZZZ.
s=re.sub(r'activate\{value:100\}\(([^,]+), poolId, 100, 0,',r'activate{value:0}(\1, poolId, 0, 100,',s)
s=re.sub(r'increase\{value:5\}\(([^,]+), 5, 0,',r'increase{value:0}(\1, 0, 5,',s)
s=s.replace('_activate(bob,entrant,100,0)','_activate(bob,entrant,0,100)').replace('_activate(alice,id,100,0)','_activate(alice,id,0,100)')
p.write_bytes(s.encode())
print('Direct Entry native/fixed18decimal fixture and two-book price callback ported')
