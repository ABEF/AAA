// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZRewardsCanonical} from "../src/ZZZRewardsCanonical.sol";
import {ZZZExactLPRewardsCanonical as Records} from "../src/base/ZZZExactLPRewardsCanonical.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
interface Vm {function deal(address,uint256)external;function prank(address)external;function expectRevert()external;function load(address,bytes32)external view returns(bytes32);}
contract TypedAccess {
 mapping(bytes32=>address)public module;uint8 public canonicalState;bool public isSealed;bool public paused;bool public preparationActive;bool public lpExitStarted;bool public canonicalSettling;address public governor;
 constructor(){governor=msg.sender;}function bind(bytes32 k,address v)external{module[k]=v;}function setState(uint8 n)external{canonicalState=n;}function seal()external{isSealed=true;}function governance()external view returns(address){return governor;}function canonicalHandoff()external view returns(address){return module[Ids.CANONICAL];}function canConfigure(address a)external view returns(bool){return a==governor&&!preparationActive;}function moduleAuthorized(bytes32 k,address a)external view returns(bool){return isSealed&&canonicalState==0&&module[k]==a;}function keeperAuthorized(address a)external view returns(bool){return a==governor&&canonicalState==0&&isSealed;}
}
contract TypedToken {
 mapping(address=>uint256)public balanceOf;mapping(address=>mapping(address=>uint256))public allowance;
 function mint(address a,uint256 n)external{balanceOf[a]+=n;}function approve(address s,uint256 n)external returns(bool){allowance[msg.sender][s]=n;return true;}function transfer(address to,uint256 n)external returns(bool){balanceOf[msg.sender]-=n;balanceOf[to]+=n;return true;}function transferFrom(address f,address t,uint256 n)external returns(bool){allowance[f][msg.sender]-=n;balanceOf[f]-=n;balanceOf[t]+=n;return true;}function decimals()external pure returns(uint8){return 18;}
}
contract TypedNFT {
 mapping(uint256=>address)private owners;function mintedCount()external pure returns(uint256){return 3;}function mintOrdinalOf(uint256 id)external pure returns(uint256){return id>=1&&id<=3?id:0;}function tokenAtOrdinal(uint256 n)external pure returns(uint256){require(n>=1&&n<=3);return n;}function ownerOf(uint256 id)external view returns(address){return owners[id];}function claimRouter()external pure returns(address){return address(0);}function setOwner(uint256 id,address who)external{owners[id]=who;}
}
contract TypedMembers {
 ZZZRewards r;mapping(uint256=>bool)public eligible;uint256 public totalEligible;
 constructor(ZZZRewards x){r=x;}function activate(uint256 id)external{require(!eligible[id]);eligible[id]=true;++totalEligible;r.syncMembership(id);}function importEligibility(uint256 id)external{require(!eligible[id]);eligible[id]=true;++totalEligible;}
}
contract TypedVault {
 ZZZRewards r;TypedMembers m;mapping(uint256=>uint256)public nftBucket;mapping(uint256=>uint256)public sharesOf;mapping(uint256=>uint256)public bucketTotalShares;
 constructor(ZZZRewards x,TypedMembers y){r=x;m=y;}function ACCOUNTING_VERSION()external pure returns(uint256){return 7;}function bucketCount()external pure returns(uint256){return 1;}function bucketAt(uint256 i)external pure returns(uint256){require(i==0);return 11;}function join(uint256 id,uint256 w)external{nftBucket[id]=11;sharesOf[id]+=w;bucketTotalShares[11]+=w;r.syncShares(id);m.activate(id);}function seed(uint256 id,uint256 w)external{nftBucket[id]=11;sharesOf[id]=w;bucketTotalShares[11]+=w;m.importEligibility(id);}
}
contract TypedPoolIdentity {address public zzz;constructor(address a){zzz=a;}function activationAssets()external view returns(address){return address(this);}}
/// TEST ONLY: real final Rewards+immutable canonical child; typed authenticated-dependency seams.
/// This is not a whole-coordinator, real ERC721/market/venue or release qualification.
contract PackedCanonicalActualHostTest {
 Vm constant vm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
 address constant A=address(0xA11CE);address constant B=address(0xB0B);address constant C=address(0xCA11);
 struct D {TypedAccess ac;TypedNFT nft;TypedMembers m;TypedVault v;ZZZRewards r;ZZZRewardsCanonical codec;}
 TypedToken token;
 receive()external payable{}
 function _new(bool preseed)private returns(D memory d){d.ac=new TypedAccess();d.nft=new TypedNFT();d.r=new ZZZRewards(address(d.ac));d.codec=ZZZRewardsCanonical(payable(d.r.canonicalModule()));d.m=new TypedMembers(d.r);d.v=new TypedVault(d.r,d.m);d.ac.bind(Ids.VAULT,address(d.v));d.ac.bind(Ids.NFT,address(d.nft));d.ac.bind(Ids.MEMBERSHIP,address(d.m));d.ac.bind(Ids.REWARDS,address(d.r));d.ac.bind(Ids.FEES,address(this));d.ac.bind(Ids.POOLS,address(new TypedPoolIdentity(address(token))));d.ac.bind(Ids.CANONICAL,address(this));d.nft.setOwner(1,A);d.nft.setOwner(2,C);d.nft.setOwner(3,A);if(preseed)d.r.addAsset(address(token));d.ac.seal();}
 function _credit(D memory d,uint256 pe,uint256 se,uint256 pz,uint256 sz)private{d.r.creditPool{value:pe+se}(11,address(0),pe,se);token.mint(address(this),pz+sz);token.approve(address(d.r),pz+sz);d.r.creditPool(11,address(token),pz,sz);require(token.allowance(address(this),address(d.r))==0,"exact allowance");}
 function _claim(D memory d,address owner,uint256 id,address asset)private returns(uint256 n){n=d.r.claimable(id,asset);uint256 before=asset==address(0)?owner.balance:token.balanceOf(owner);vm.prank(owner);require(d.r.claim(id,asset)==n,"payout");require((asset==address(0)?owner.balance:token.balanceOf(owner))-before==n,"received");}
 function _setup()private returns(D memory s,D memory t,D memory c){vm.deal(address(this),1_000_000 ether);token=new TypedToken();s=_new(true);t=_new(false);c=_new(true);uint256 w=(uint256(1)<<200)+123;uint256 l=(uint256(1)<<199)+7;s.nft.setOwner(2,B);c.nft.setOwner(2,B);s.v.join(1,l);s.v.join(2,w-l);c.v.join(1,l);c.v.join(2,w-l);t.v.seed(1,l);t.v.seed(2,w-l);_credit(s,1,37,19,101);_credit(c,1,37,19,101);require(_claim(s,A,1,address(0))==_claim(c,A,1,address(0)),"prior eth");require(_claim(s,A,1,address(token))==_claim(c,A,1,address(token)),"prior zzz");s.nft.setOwner(2,C);c.nft.setOwner(2,C);require(this.logicalDigest(s.r)==this.logicalDigest(c.r),"setup exact");}
 function _key(uint256 n,uint256 base)private pure returns(bytes32){return keccak256(abi.encode(n,base));}
 function logicalDigest(ZZZRewards r)external view returns(bytes32 hash){
  uint256[2]memory p;uint128[2]memory h;uint256[2]memory l;
  for(uint256 t;t<2;++t){(,uint256 oe,uint256 oz)=r.allocationTree(t==0?11:0);hash=keccak256(abi.encode(hash,oe,oz));uint256 base=t==0?uint256(keccak256(abi.encode(uint256(11),uint256(5)))):6;
   for(uint256 n=1;n<=2023;++n){uint256 weight=uint256(vm.load(address(r),_key(n,base)));
    for(uint256 a;a<2;++a){uint256 b=base+1+3*a;p[a]=uint256(vm.load(address(r),_key(n,b)));bytes32 at=_key(n,b+1);uint256 packed=uint256(vm.load(address(r),at));uint256 wide=uint256(vm.load(address(r),bytes32(uint256(at)+1)));h[a]=uint128(packed);l[a]=wide==0?packed>>128:wide;}
    hash=keccak256(abi.encode(hash,weight,p[0],h[0],l[0],p[1],h[1],l[1]));
   }
  }
 }
 function _import(D memory s,D memory t)private{
  s.ac.setState(1);t.ac.setState(2);s.codec.canonicalCapture();s.codec.canonicalSettle();require(s.codec.canonicalCount()==2029,"row count");
  bool[2]memory wide;bool[2]memory compact;
  for(uint256 row;row<s.codec.canonicalCount();++row){bytes memory data=s.codec.canonicalExport(row);if(row>=6){Records.CanonicalNode memory n=abi.decode(data,(Records.CanonicalNode));for(uint256 a;a<2;++a){if(n.low[2+a]>type(uint128).max)wide[a]=true;if((n.high[a]!=0||n.low[a]!=0)&&n.low[a]<=type(uint128).max)compact[a]=true;}}t.codec.canonicalImport(row,data);}
  require(wide[0]&&wide[1]&&compact[0]&&compact[1],"wide and compact phase rows");require(this.logicalDigest(s.r)==this.logicalDigest(t.r),"import complete logical nodes");
  for(uint256 a;a<2;++a){(address asset,uint256 amount)=s.codec.canonicalBacking(a);uint256 before=asset==address(0)?address(t.r).balance:token.balanceOf(address(t.r));s.codec.canonicalRelease(a,address(t.codec));t.codec.canonicalAccept(a,address(s.codec));require((asset==address(0)?address(t.r).balance:token.balanceOf(address(t.r)))-before==amount,"funded acceptance");}
  t.codec.canonicalValidate();require(this.logicalDigest(s.r)==this.logicalDigest(t.r),"funding leaves phases");
 }
 function _compareAndDrain(D memory d,D memory c)private{
  vm.prank(B);vm.expectRevert();d.r.claim(2,address(0));
  for(uint256 a;a<2;++a){address asset=a==0?address(0):address(token);require(d.r.claimable(3,asset)==0,"dormant");require(_claim(d,C,2,asset)==_claim(c,C,2,asset),"owner rights");require(_claim(d,A,1,asset)==_claim(c,A,1,asset),"prior paid debt");require(d.r.liabilities(asset)==0,"complete drain");}
  _credit(d,3,11,7,13);_credit(c,3,11,7,13);
  for(uint256 a;a<2;++a){address asset=a==0?address(0):address(token);require(_claim(d,A,1,asset)==_claim(c,A,1,asset),"future first");require(_claim(d,C,2,asset)==_claim(c,C,2,asset),"future second");require(d.r.liabilities(asset)==0&&d.r.orphaned(asset)==0,"future no reserve");}
  require(address(d.r).balance==0&&token.balanceOf(address(d.r))==0,"backing fully paid");require(this.logicalDigest(d.r)==this.logicalDigest(c.r),"future exact phases");
 }
 function testPackedActualCanonicalBothBooksImportCurrentOwnerAndFutureIncome()public{(D memory s,D memory t,D memory c)=_setup();_import(s,t);t.codec.canonicalActivate();s.ac.setState(3);t.ac.setState(0);vm.prank(C);vm.expectRevert();s.r.claim(2,address(0));_compareAndDrain(t,c);require(address(s.r).balance==0&&token.balanceOf(address(s.r))==0,"source backing moved");}
 function testPackedActualFundedAbortRestoresSourcePhasesOwnerAndFutureIncome()public{(D memory s,D memory t,D memory c)=_setup();bytes32 before=this.logicalDigest(s.r);_import(s,t);t.ac.setState(4);for(uint256 a;a<2;++a){(address asset,uint256 amount)=s.codec.canonicalBacking(a);t.codec.canonicalRelease(a,address(s.codec));s.codec.canonicalRestore(a,address(t.codec));require((asset==address(0)?address(s.r).balance:token.balanceOf(address(s.r)))==amount,"full restore");}s.codec.canonicalValidate();require(this.logicalDigest(s.r)==before,"source book untouched");s.ac.setState(0);vm.prank(C);vm.expectRevert();t.r.claim(2,address(token));_compareAndDrain(s,c);require(address(t.r).balance==0&&token.balanceOf(address(t.r))==0,"target no backing");}
}
