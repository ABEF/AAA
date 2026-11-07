from pathlib import Path
import re,json
R=Path.cwd(); E=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/exact-lp-integration-20261106/accounting-agent')
def read(p):return p.read_bytes().decode()
def write(p,s):p.write_bytes(s.encode())
def args(s,start):
 depth=1;i=start+1;parts=[];prev=i
 while depth:
  if s[i]=='(':depth+=1
  elif s[i]==')':depth-=1
  elif s[i]==',' and depth==1:parts.append(s[prev:i].strip());prev=i+1
  i+=1
 parts.append(s[prev:i-1].strip());return parts,i

def replace_calls(s,needle,fn):
 at=0
 while (at:=s.find(needle+'(',at))>=0:
  a,end=args(s,at+len(needle));rep=fn(a);s=s[:at]+rep+s[end:];at+=len(rep)
 return s
# Explicitly swapped test-domain currency references so the originally ERC20
# royalty/burn scenarios continue to exercise ERC20 ZZZ, not native ETH.
for name in ['NFTOwnershipRights.t.sol','CollectionScale.t.sol','NFTRightsInvariants.t.sol','ContributionPriceSecurity.t.sol']:
 p=R/'test'/name;s=read(p);s=re.sub(r'\bt0\b','TOKEN_SWAP',s);s=re.sub(r'\bt1\b','t0',s);s=s.replace('TOKEN_SWAP','t1');write(p,s)
p=R/'test/RoyaltyNoCustodian.t.sol';s=read(p);s=re.sub(r'\bt0\b','t1',s);write(p,s)
files=[]
for p in (R/'test').glob('*.sol'):
 if p.name in ['CanonicalPreparation.t.sol','AtomicActivationIntegration.t.sol']:continue
 s=read(p)
 # Only change actual inherited fixture scopes, not unrelated contracts above/below.
 spans=[]
 for m in re.finditer(r'contract\s+\w+\s+is\s+PooledVaultFixture\s*\{',s):
  start=m.start();brace=s.index('{',start);depth=1;i=brace+1
  while depth:
   if s[i]=='{':depth+=1
   elif s[i]=='}':depth-=1
   i+=1
  spans.append((start,i))
 if p.name=='VaultAccounting.t.sol':
  # Include helper base methods but exclude venue's legacy token branch.
  start=s.index('abstract contract PooledVaultFixture');spans=[(start,len(s))]
 for start,end in reversed(spans):
  part=s[start:end]
  part=replace_calls(part,'t0.balanceOf',lambda a:'address('+a[0]+').balance')
  part=replace_calls(part,'t0.mint',lambda a:'_giftNative('+', '.join(a)+')')
  # ETH has no ERC20 approval; do not turn this into a vacuous zero assertion.
  part=re.sub(r'assertEq\(t0\.allowance\([^;]+;','',part)
  part=re.sub(r'(?:vm\.prank\([^;]+;\s*)?t0\.approve\([^;]+;','',part)
  part=part.replace('oracle.setTestFeed(','_setFixtureFeed(')
  for op,idx in [('activate',2),('increase',1)]:
   part=replace_calls(part,'vault.'+op,lambda a,op=op,idx=idx:'vault.'+op+'{value:'+a[idx]+'}('+', '.join(a)+')')
  for who in ['alice','bob']:
   part=re.sub(r'assertEq\(address\('+who+r'\)\.balance,\s*100000\)',f'assertEq({who}.balance,1 ether-0.05 ether)',part)
  s=s[:start]+part+s[end:]
 if spans:write(p,s);files.append(p.name)
# Native fixture feed adapter is local to the synthetic mock-price environment.
p=R/'test/VaultAccounting.t.sol';s=read(p)
where=s.index('abstract contract PooledVaultFixture')
adapter='''/// @dev TEST ONLY adapter: $1/zero-decimal fixture unit -> $1/wei native unit.
contract NormalizedNativeFixtureFeed {
    MockFeed public immutable source;
    constructor(address feed){source=MockFeed(feed);}
    function decimals()external pure returns(uint8){return 8;}
    function latestRoundData()external view returns(uint80,int256,uint256,uint256,uint80){
        (uint80 id,int256 value,uint256 started,uint256 updated,uint80 answered)=source.latestRoundData();
        return(id,value*1e18,started,updated,answered);
    }
}
'''
s=s[:where]+adapter+s[where:]
s=s.replace('MockFeed private _royaltyFixtureFeed;','''MockFeed private _royaltyFixtureFeed;
    function _giftNative(address owner,uint256 amount)internal{vm.deal(owner,owner.balance+amount);}
    function _setFixtureFeed(address asset,address feed,uint64 age)internal{
        oracle.setTestFeed(asset,asset==address(0)?address(new NormalizedNativeFixtureFeed(feed)):feed,age);
    }''')
s=s.replace('_setFixtureFeed(address(0),address(new MockFeed(8,1e26)),3600);','_setFixtureFeed(address(0),address(feed),3600);')
s=s.replace('assertEq(alice.balance,etherBalance);','assertEq(alice.balance,etherBalance-1000);')
s=s.replace('assertEq(address(alice).balance,99000);','assertEq(alice.balance,1 ether-0.05 ether-1000);')
# Exact-unit remainder now belongs to one holder rather than stranded fraction.
s=s.replace('assertEq(rewards.claimable(dormantId,address(t0)),44);','assertEq(rewards.claimable(dormantId,address(t0)),45);').replace('assertEq(rewards.claim(dormantId,address(t0)),44);','assertEq(rewards.claim(dormantId,address(t0)),45);')
write(p,s)
(E/'NATIVE_PORT_FILES.json').write_text(json.dumps(files,indent=2))
print('Ported native currency calls in inherited fixture scopes:',len(files))
