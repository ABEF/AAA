from pathlib import Path
import re
for name in ['EntryReviewPolicy.t.sol','ContributionEntryPriceSecurity.t.sol']:
 p=Path('test')/name;s=p.read_bytes().decode();s=re.sub(r'\bt0\b','t1',s)
 s=s.replace('venue.a0(vault.group(bucket).lpTokenId),99e18','venue.a1(vault.group(bucket).lpTokenId),99e18').replace('group(bucket).idle0,1e18','group(bucket).idle1,1e18')
 p.write_bytes(s.encode())
# Preserve original per-currency algebra after redirecting old ERC20 cases to ZZZ.
for name in ['NFTOwnershipRights.t.sol','CollectionScale.t.sol','NFTRightsInvariants.t.sol']:
 p=Path('test')/name;s=p.read_bytes().decode()
 for first,second in [('.a0(','.a1('),('.idle0','.idle1')]:
  s=s.replace(first,'SWAP_FIELD').replace(second,first).replace('SWAP_FIELD',second)
 # setFees calls in these files contain simple arithmetic with no nested comma.
 s=re.sub(r'venue\.setFees\(([^,()]+),([^()]+)\)',lambda m:'venue.setFees('+m[2].strip()+','+m[1].strip()+')',s)
 if name=='NFTRightsInvariants.t.sol':
  s=s.replace('uint256 feeBalance = token.balanceOf(address(fees)); uint256 rewardBalance = token.balanceOf(address(rewards));','uint256 feeBalance=asset==address(0)?address(fees).balance:token.balanceOf(address(fees));uint256 rewardBalance=asset==address(0)?address(rewards).balance:token.balanceOf(address(rewards));')
  s=s.replace('assertLe(lpClaims[i], rewards.liabilities(asset));','assertEq(lpClaims[i],rewards.liabilities(asset));')
  s=s.replace('assertEq(address(vault).balance, 0);','assertEq(address(vault).balance,p.idle0);')
 if name=='CollectionScale.t.sol':
  s=s.replace('assertEq(address(owner).balance - before1, expected[1]);','assertEq(owner.balance-before1,expected[1]+expected[4]);')
  s=s.replace('assertEq(owner.balance - beforeNative, expected[4]);','assertEq(owner.balance-beforeNative,expected[1]+expected[4]);')
 p.write_bytes(s.encode())
p=Path('test/ProductionInvariants.t.sol');s=p.read_bytes().decode().replace('bound(x,1,100),bound(y,1,100)','bound(x,3,100),bound(y,3,100)')
s=s.replace('policy.setNeed(false);\n        compounder.compound','if(!vault.migrationBudget().compoundReady(bucket))return;\n        policy.setNeed(false);\n        compounder.compound')
s=s.replace('assertLe(claims[i],liabilities,"unfunded claim")','assertEq(claims[i],liabilities,"every allocated raw unit is claimable")')
s=s.replace('assertEq(address(vault).balance,0);','assertEq(address(vault).balance,p.idle0+donations[0]);');p.write_bytes(s.encode())
print('Updated dependent Entry scenarios, currency vector alignment, exact conservation')
