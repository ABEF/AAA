// SPDX-License-Identifier: MIT

pragma solidity 0.8.26;

import {TestBaselineHost,TestPackedHost} from "./PackedTestHosts.sol";

interface Vm {function expectRevert(bytes4)external;function expectRevert(bytes calldata)external;function store(address,bytes32,bytes32)external;function readFileBinary(string calldata)external view returns(bytes memory);function record()external;function accesses(address)external returns(bytes32[] memory,bytes32[] memory);function coolSlot(address,bytes32)external;function cool(address)external;}

contract LPPackedEngineeringTest {

 Vm constant vm=Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

 TestBaselineHost a; TestPackedHost b;

 event EngineeringGas(string tree,uint256 baseline,uint256 fused,uint256 saving);

 uint256[8] ids=[uint256(1),2,17,128,513,700,999,1000];

 function setUp()public{a=new TestBaselineHost();b=new TestPackedHost();}

 function _set(uint256 o,uint256 w)internal{require(a.setWeight(o,w)==b.setWeight(o,w),"weight total");}

 function _credit(uint8 z,uint256 n)internal{a.credit(z,n);b.credit(z,n);}

 function _take(uint8 z,uint256 o)internal{require(a.take(z,o)==b.take(z,o),"take");}

 function _equal()internal view{require(a.digest()==b.digest(),"raw digest");for(uint8 z;z<2;++z){require(a.outstanding(z)==b.outstanding(z),"liability");for(uint256 i;i<ids.length;++i)require(a.claimable(z,ids[i])==b.claimable(z,ids[i]),"claimable");}}

 function testPackedMutableStateAndClaims()public{for(uint256 i;i<ids.length;++i)_set(ids[i],17+i*i);_credit(0,791);_credit(1,4999);for(uint256 i;i<24;++i){uint256 o=ids[i%8];_set(o,i%5==0?0:11+i*3);if(i%3==0)_take(uint8(i%2),ids[(i+5)%8]);_credit(uint8(i%2),i+1);_equal();}for(uint8 z;z<2;++z)for(uint256 i;i<ids.length;++i)_take(z,ids[i]);_equal();require(a.outstanding(0)==0&&a.outstanding(1)==0,"drain");}

 function testPackedMaximumZeroNoopOverflow()public{_set(1,type(uint256).max-3);_set(1000,3);_credit(0,type(uint256).max);_credit(1,type(uint256).max);_set(1,type(uint256).max-3);_equal();vm.expectRevert(abi.encodeWithSelector(bytes4(0x4e487b71),uint256(0x11)));a.setWeight(1,type(uint256).max);vm.expectRevert(abi.encodeWithSelector(bytes4(0x4e487b71),uint256(0x11)));b.setWeight(1,type(uint256).max);_equal();_set(1,type(uint256).max-4);_equal();_set(1000,0);_equal();_set(1,0);_equal();vm.expectRevert(bytes4(keccak256("EmptyCohort()")));a.credit(0,1);vm.expectRevert(bytes4(keccak256("EmptyCohort()")));b.credit(0,1);_equal();for(uint8 z;z<2;++z){_take(z,1);_take(z,1000);}require(a.outstanding(0)==0&&a.outstanding(1)==0,"max drain");_set(1000,type(uint256).max);_credit(0,type(uint256).max);_take(0,1000);_equal();}

 function testPackedPhasesRemovalAndInvalidOrdinal()public{for(uint256 i;i<ids.length;++i)_set(ids[i],(uint256(1)<<128)+i*17+1);for(uint256 i;i<37;++i){_credit(uint8(i%2),1+i%3);if(i%4==0)_take(uint8(i%2),ids[i%8]);}_equal();for(uint256 i;i<ids.length;++i){_set(ids[i],0);_equal();}_set(513,7);_set(1,3);_credit(0,1009);_credit(1,999);_equal();vm.expectRevert(bytes4(keccak256("InvalidOrdinal()")));a.setWeight(0,1);vm.expectRevert(bytes4(keccak256("InvalidOrdinal()")));b.setWeight(0,1);vm.expectRevert(bytes4(keccak256("InvalidOrdinal()")));a.setWeight(1001,1);vm.expectRevert(bytes4(keccak256("InvalidOrdinal()")));b.setWeight(1001,1);_equal();}

 function testPackedDeterministicAdversarialSequence()public{uint256 seed=672187;for(uint256 i;i<ids.length;++i)_set(ids[i],1+i);for(uint256 i;i<128;++i){seed=uint256(keccak256(abi.encode(seed,i)));uint256 o=ids[seed%8];uint8 z=uint8(seed>>16)%2;uint256 op=(seed>>32)%4;if(op==0)_set(o,(seed>>64)%1e30);else if(op==1)_credit(z,(seed>>80)%1e22);else if(op==2)_take(z,o);else{uint256 w=a.weightOf(o);_set(o,w);}if(i%8==0)_equal();}_equal();for(uint8 z;z<2;++z)for(uint256 i;i<ids.length;++i)_take(z,ids[i]);_equal();require(a.outstanding(0)==0&&a.outstanding(1)==0,"sequence drain");}

 function _load(address host,string memory label)internal{bytes memory data=vm.readFileBinary(string.concat("fixtures/",label,".bin"));require(data.length%64==0,"fixture");for(uint256 i;i<data.length;i+=64){bytes32 slot;bytes32 value;assembly{slot:=mload(add(add(data,32),i)) value:=mload(add(add(data,64),i))}vm.store(host,slot,value);}}

 function _cool(address host)internal{vm.record();(bool ok,)=host.staticcall(abi.encodeWithSignature("digest()"));require(ok,"digest read");(bytes32[] memory reads,bytes32[] memory writes)=vm.accesses(host);for(uint256 i;i<reads.length;++i)vm.coolSlot(host,reads[i]);for(uint256 i;i<writes.length;++i)vm.coolSlot(host,writes[i]);vm.cool(host);}

 function testPackedColdExtractedOwnerAndCollective()public{_load(address(a),"owner-baseline");_load(address(b),"owner-packed");_equal();_cool(address(a));uint256 g=gasleft();a.setWeight(1000,99909134925785758152);uint256 oldGas=g-gasleft();_cool(address(b));g=gasleft();b.setWeight(1000,99909134925785758152);uint256 newGas=g-gasleft();emit EngineeringGas("actual999owner",oldGas,newGas,oldGas-newGas);_equal();TestBaselineHost c=new TestBaselineHost();TestPackedHost d=new TestPackedHost();_load(address(c),"collective-baseline");_load(address(d),"collective-packed");require(c.digest()==d.digest(),"collective import");_cool(address(c));g=gasleft();c.setWeight(1000,1);oldGas=g-gasleft();_cool(address(d));g=gasleft();d.setWeight(1000,1);newGas=g-gasleft();emit EngineeringGas("actual999collective",oldGas,newGas,oldGas-newGas);require(c.digest()==d.digest(),"collective final");}

 function _seed(uint8 z,uint128 h,uint256 l)internal{a.seedPhase(z,1,h,l);b.seedPhase(z,1,h,l);}
 function testPackedFullWidthSpillCompactAndBack()public{
   uint256 W=(uint256(1)<<200)+123;uint256 L=(uint256(1)<<199)+7;
   _set(1,L);_set(1000,W-L);_credit(0,1);_credit(1,19);_take(0,1);_take(1,1000);_equal();
   (,uint256 spill)=b.physicalCarry(0,1);require(spill>type(uint128).max,"reachable wide");
   _set(1,7);_set(1000,11);_equal();(,spill)=b.physicalCarry(0,1);require(spill==0,"clear spill");
   _set(1,L);_set(1000,W-L);_credit(0,1003);_take(0,1);_equal();(,spill)=b.physicalCarry(0,1);require(spill>type(uint128).max,"spill again");
   _seed(0,type(uint128).max,type(uint128).max);_equal();(uint256 packed,uint256 wide)=b.physicalCarry(0,1);require(wide==0&&packed==type(uint256).max,"compact edge");
   _seed(0,type(uint128).max,uint256(1)<<128);_equal();(packed,wide)=b.physicalCarry(0,1);require(wide==(uint256(1)<<128)&&packed==type(uint128).max,"wide edge");
   _seed(0,0,0);_equal();(packed,wide)=b.physicalCarry(0,1);require(packed==0&&wide==0,"zero clear");
   // Encoding preserves MAX too; this artificial low is invalid for any W, so do not split it.
   _seed(0,type(uint128).max,type(uint256).max);(uint256 wa,uint256 pa,uint128 ha,uint256 la)=a.node(0,1);(uint256 wb,uint256 pb,uint128 hb,uint256 lb)=b.node(0,1);require(wa==wb&&pa==pb&&ha==hb&&la==lb&&lb==type(uint256).max,"full low domain");
   _seed(0,0,0);_equal();
 }

}

