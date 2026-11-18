// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {BaselineFeed} from "../src/BaselineFeed.sol";
import {DeduplicatedFeed} from "../src/DeduplicatedFeed.sol";
import {BracketedFeed} from "../src/BracketedFeed.sol";
import {MarketState} from "../src/interfaces/IZZZExecutionOracle.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
interface Vm {function warp(uint256)external;function cool(address)external;function coolSlot(address,bytes32)external;}
contract Core {function marker()external pure returns(uint256){return 1;}}
contract Token {uint8 public immutable decimals;constructor(uint8 d){decimals=d;}}
contract USD {uint8 public constant decimals=8;function latestRoundData()external view returns(uint80,int256,uint256,uint256,uint80){return(1,2000e8,block.timestamp-10,block.timestamp-2,1);}}
contract State {
 address public poolManager;uint256 public sqrt;int256 public tick;uint256 public protocol;uint256 public fee;uint256 public liquidity;
 constructor(address core){poolManager=core;reset();}
 function reset()public{sqrt=uint160(1<<96);tick=0;protocol=0;fee=3000;liquidity=1000;}
 function raw(uint256 s,int256 t,uint256 p,uint256 f,uint256 l)external{sqrt=s;tick=t;protocol=p;fee=f;liquidity=l;}
 function getSlot0(bytes32)external view returns(uint256,int256,uint256,uint256){return(sqrt,tick,protocol,fee);}
 function getLiquidity(bytes32)external view returns(uint256){return liquidity;}
}
contract QuoteMath {
 function original(uint160 sqrt,uint256 usd,uint8 d)external pure returns(uint256 out){
  uint256 numerator=usd*(10**d);
  if(sqrt<=type(uint128).max){uint256 ratio=uint256(sqrt)*sqrt;out=Math.mulDiv(numerator,uint256(1)<<192,ratio)/1e18;}
  else{uint256 ratio=Math.mulDiv(sqrt,sqrt,uint256(1)<<64);out=Math.mulDiv(numerator,uint256(1)<<128,ratio)/1e18;}
  require(out!=0 && out<=1e36);
 }
 function proposed(uint160 sqrt,uint256 usd,uint8 d)external pure returns(uint256 out){
  uint256 divisor=10**(18-d);
  if(sqrt<=type(uint128).max){uint256 ratio=uint256(sqrt)*sqrt;out=Math.mulDiv(usd,uint256(1)<<192,ratio)/divisor;}
  else{uint256 ratio=Math.mulDiv(sqrt,sqrt,uint256(1)<<64);out=Math.mulDiv(usd,uint256(1)<<128,ratio)/divisor;}
  require(out!=0 && out<=1e36);
 }
}
contract FeedDifferential20261118Test {
 Vm private constant vm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
 BaselineFeed base;DeduplicatedFeed dedup;BracketedFeed bracket;Core core;Token token;USD usd;State state;QuoteMath math;
 event log_named_uint(string key,uint256 value);
 function setUp()public{
  vm.warp(10000000);core=new Core();token=new Token(18);usd=new USD();state=new State(address(core));math=new QuoteMath();
  PoolKey memory key=PoolKey(Currency.wrap(address(0)),Currency.wrap(address(token)),3000,60,IHooks(address(0)));
  bytes memory encoded=abi.encode(address(core),address(core).codehash,address(state),address(state).codehash,key,
    keccak256(abi.encode(key)),address(token),address(token).codehash,address(usd),address(usd).codehash,uint32(3600),uint128(1),bytes32(uint256(1)));
  base=new BaselineFeed(abi.decode(encoded,(BaselineFeed.Config)));
  dedup=new DeduplicatedFeed(abi.decode(encoded,(DeduplicatedFeed.Config)));
  bracket=new BracketedFeed(abi.decode(encoded,(BracketedFeed.Config)));
 }
 function _same(bytes memory data)private view{
  (bool a,bytes memory aa)=address(base).staticcall(data);(bool b,bytes memory bb)=address(dedup).staticcall(data);(bool c,bytes memory cc)=address(bracket).staticcall(data);
  require(a==b && a==c,"different acceptance");require(keccak256(aa)==keccak256(bb) && keccak256(aa)==keccak256(cc),"different output/error");
 }
 function testFuzzQuoteAlgebra(uint160 raw,uint128 amount,uint8 digit)public view{
  uint160 sqrt=uint160(uint256(raw)%(TickMath.MAX_SQRT_PRICE-TickMath.MIN_SQRT_PRICE)+TickMath.MIN_SQRT_PRICE);
  uint256 ethUSD=uint256(amount)%1e36+1;uint8 d=digit%19;
  (bool a,bytes memory aa)=address(math).staticcall(abi.encodeCall(math.original,(sqrt,ethUSD,d)));
  (bool b,bytes memory bb)=address(math).staticcall(abi.encodeCall(math.proposed,(sqrt,ethUSD,d)));
  require(a==b && (!a || keccak256(aa)==keccak256(bb)),"quote algebra acceptance/value mismatch");
  if(d==18)_sameQuote(abi.encodeCall(base.probeQuote,(sqrt,ethUSD)));
 }
 function testQuoteExtremesAllDecimals()public view{
  uint160[7]memory roots=[TickMath.MIN_SQRT_PRICE,uint160(TickMath.MIN_SQRT_PRICE+1),uint160(1<<96),type(uint128).max,uint160(uint256(type(uint128).max)+1),uint160(TickMath.MAX_SQRT_PRICE-2),uint160(TickMath.MAX_SQRT_PRICE-1)];
  uint256[5]memory values=[uint256(1),1e18,2000e18,uint256(1e36-1),1e36];
  for(uint8 d;d<=18;++d)for(uint256 i;i<roots.length;++i)for(uint256 j;j<values.length;++j){
   (bool a,bytes memory aa)=address(math).staticcall(abi.encodeCall(math.original,(roots[i],values[j],d)));
   (bool b,bytes memory bb)=address(math).staticcall(abi.encodeCall(math.proposed,(roots[i],values[j],d)));
   require(a==b && (!a || keccak256(aa)==keccak256(bb)),"extreme quote acceptance/value mismatch");
  }
 }
 function testFuzzTickBracket(uint160 raw,int24 tick)public view{
  MarketState memory s=MarketState(raw,tick,0,3000,1000);_same(abi.encodeCall(base.probeState,(s)));
 }
 function testCanonicalCrossingAndBounds()public view{
  int24[8]memory ticks=[TickMath.MIN_TICK,int24(TickMath.MIN_TICK+1),int24(-200000),int24(-1),int24(0),int24(1),int24(200000),int24(TickMath.MAX_TICK-1)];
  for(uint256 i;i<ticks.length;++i){
   uint160 sqrt=TickMath.getSqrtPriceAtTick(ticks[i]);
   _same(abi.encodeCall(base.probeState,(MarketState(sqrt,ticks[i],0,3000,1000))));
   if(ticks[i]>TickMath.MIN_TICK)_same(abi.encodeCall(base.probeState,(MarketState(sqrt,ticks[i]-1,0,3000,1000))));
   if(sqrt<TickMath.MAX_SQRT_PRICE-1)_same(abi.encodeCall(base.probeState,(MarketState(sqrt+1,ticks[i],0,3000,1000))));
   if(sqrt>TickMath.MIN_SQRT_PRICE)_same(abi.encodeCall(base.probeState,(MarketState(sqrt-1,ticks[i],0,3000,1000))));
  }
  _same(abi.encodeCall(base.probeState,(MarketState(TickMath.MIN_SQRT_PRICE-1,TickMath.MIN_TICK,0,3000,1000))));
  _same(abi.encodeCall(base.probeState,(MarketState(TickMath.MAX_SQRT_PRICE,TickMath.MAX_TICK,0,3000,1000))));
  _same(abi.encodeCall(base.probeState,(MarketState(uint160(1<<96),0,1001,3000,1000))));
  _same(abi.encodeCall(base.probeState,(MarketState(uint160(1<<96),0,0,3001,1000))));
  _same(abi.encodeCall(base.probeState,(MarketState(uint160(1<<96),0,0,3000,0))));
 }
 function _expectReadFailure()private view{
  bytes4 sel=BaselineFeed.latestRoundData.selector;
  (bool a,bytes memory aa)=address(base).staticcall(abi.encodeWithSelector(sel));(bool b,bytes memory bb)=address(dedup).staticcall(abi.encodeWithSelector(sel));(bool c,bytes memory cc)=address(bracket).staticcall(abi.encodeWithSelector(sel));
  require(!a && !b && !c,"malformed accepted");require(keccak256(aa)==keccak256(bb) && keccak256(aa)==keccak256(cc),"malformed error");
 }
 function testWideNoncanonicalStateRejected()public{
  state.raw(uint256(type(uint160).max)+1,0,0,3000,1000);_expectReadFailure();
  state.raw(1<<96,int256(type(int24).max)+1,0,3000,1000);_expectReadFailure();
  state.raw(1<<96,int256(type(int24).min)-1,0,3000,1000);_expectReadFailure();
  state.raw(1<<96,0,uint256(type(uint24).max)+1,3000,1000);_expectReadFailure();
  state.raw(1<<96,0,0,uint256(type(uint24).max)+1,1000);_expectReadFailure();
  state.raw(1<<96,0,0,3000,uint256(type(uint128).max)+1);_expectReadFailure();
  state.raw(1<<96,0,1001,3000,1000);_expectReadFailure();
  state.raw(1<<96,887272,0,3000,1000);_expectReadFailure();
 }
 function _cold(address target)private{
  address[5]memory aa=[target,address(core),address(token),address(usd),address(state)];
  for(uint256 a;a<aa.length;++a){vm.cool(aa[a]);for(uint256 s;s<30;++s)vm.coolSlot(aa[a],bytes32(s));}
 }
 function _proofGas(address target,MarketState memory s)private returns(uint256 used){
  _cold(target);bytes memory data=abi.encodeCall(base.executionProof,(s));uint256 beforeGas=gasleft();
  (bool ok,bytes memory result)=target.staticcall(data);used=beforeGas-gasleft();require(ok && result.length==320,"proof failed");
 }
 function testColdProofAndTickAlgorithmGas()public{
  int24[5]memory ticks=[int24(-200000),int24(-1),int24(0),int24(1),int24(200000)];
  for(uint256 i;i<ticks.length;++i){
   uint160 sqrt=TickMath.getSqrtPriceAtTick(ticks[i]);state.raw(sqrt,ticks[i],0,3000,1000);MarketState memory s=MarketState(sqrt,ticks[i],0,3000,1000);
   uint256 b=_proofGas(address(base),s);uint256 d=_proofGas(address(dedup),s);uint256 c=_proofGas(address(bracket),s);
   emit log_named_uint("tickIndex",i);emit log_named_uint("baseline",b);emit log_named_uint("dedupQuote",d);emit log_named_uint("bracket",c);
   require(d<b,"dedup not cheaper");
  }
 }

 function _sameQuote(bytes memory data)private view{
  (bool a,bytes memory aa)=address(base).staticcall(data);(bool b,bytes memory bb)=address(dedup).staticcall(data);(bool c,bytes memory cc)=address(bracket).staticcall(data);
  require(a==b && a==c,"different quote acceptance");if(a)require(keccak256(aa)==keccak256(bb) && keccak256(aa)==keccak256(cc),"different valid quote");
 }
 function testInvalidExtremeSelectorsRemainRejected()public view{
  bytes memory data=abi.encodeCall(base.probeQuote,(TickMath.MIN_SQRT_PRICE+2,uint256(1e35)));
  (bool a,bytes memory aa)=address(base).staticcall(data);(bool b,bytes memory bb)=address(dedup).staticcall(data);(bool c,bytes memory cc)=address(bracket).staticcall(data);
  require(!a && !b && !c && aa.length==36 && bb.length==4 && cc.length==4,"extreme rejection");
  require(bytes4(aa)==bytes4(0x4e487b71),"baseline overflow");
  require(bytes4(bb)==DeduplicatedFeed.InvalidObservation.selector && bytes4(cc)==BracketedFeed.InvalidObservation.selector,"candidate domain error");
 }
}
