// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture}from "./VaultAccounting.t.sol";
import {Vm}from "forge-std/Vm.sol";

/// @notice Actual Vault/NFT/Membership/Fees/Rewards producer, with an explicitly
/// synthetic native venue, correlated feeds and $1/wei+$1/ZZZ test units.
/// This proves event/getter/replay wiring, not market or provider qualification.
contract ExactLPVaultWireTest is PooledVaultFixture {
    event ExactLPWire(uint8 indexed stage,bytes logs,bytes snapshot);
    struct WireSnapshot {
        address nft;address vault;address membership;address rewards;address fees;address zzz;
        uint256 id;uint256 bucket;uint256 shares;uint256 eligible;address owner;uint256 ordinal;
        uint256 individualETH;uint256 collectiveETH;uint256 individualZZZ;uint256 collectiveZZZ;
        uint256 bucketWeight;uint256 bucketETH;uint256 bucketZZZ;
        uint256 globalWeight;uint256 globalETH;uint256 globalZZZ;
        uint256 directETH;uint256 directZZZ;uint256 liabilityETH;uint256 liabilityZZZ;
    }
    function _snapshot(uint256 id)private view returns(bytes memory){
        WireSnapshot memory w;w.nft=address(nft);w.vault=address(vault);w.membership=address(membership);
        w.rewards=address(rewards);w.fees=address(fees);w.zzz=address(t1);w.id=id;w.bucket=vault.nftBucket(id);w.shares=vault.sharesOf(id);w.eligible=membership.totalEligible();w.owner=nft.ownerOf(id);w.ordinal=nft.mintOrdinalOf(id);
        (w.individualETH,w.collectiveETH)=rewards.claimableComponents(id,address(0));(w.individualZZZ,w.collectiveZZZ)=rewards.claimableComponents(id,address(t1));
        (w.bucketWeight,w.bucketETH,w.bucketZZZ)=rewards.allocationTree(w.bucket);(w.globalWeight,w.globalETH,w.globalZZZ)=rewards.allocationTree(0);
        w.directETH=rewards.directLiabilities(address(0));w.directZZZ=rewards.directLiabilities(address(t1));w.liabilityETH=rewards.liabilities(address(0));w.liabilityZZZ=rewards.liabilities(address(t1));return abi.encode(w);
    }
    function testExactLPRealVaultWireEnrollmentHarvestGrowthAndClaim()public{
        vm.recordLogs();uint256 id=_mint(alice);_activate(alice,id,101,0);Vm.Log[] memory records=vm.getRecordedLogs();emit ExactLPWire(0,abi.encode(records),_snapshot(id));
        uint256 bucket=vault.nftBucket(id);assertEq(vault.sharesOf(id),101e18);
        vm.recordLogs();venue.setFees(20,20);vault.collectFees(bucket,block.timestamp+100);records=vm.getRecordedLogs();emit ExactLPWire(1,abi.encode(records),_snapshot(id));
        (uint256 personal,uint256 shared)=rewards.claimableComponents(id,address(0));assertEq(personal,16);assertEq(shared,2);
        vm.recordLogs();uint256 dormant=_mint(bob);vm.prank(alice);vault.increase{value:5}(id,5,0,1,block.timestamp+100);records=vm.getRecordedLogs();emit ExactLPWire(2,abi.encode(records),_snapshot(id));
        assertEq(rewards.claimable(dormant,address(0)),0);assertEq(rewards.claimable(dormant,address(t1)),0);assertEq(vault.sharesOf(dormant),0);assertFalse(membership.eligible(dormant));
        assertEq(rewards.claimable(id,address(0)),18);assertEq(rewards.claimable(id,address(t1)),18);
        vm.recordLogs();vm.prank(alice);assertEq(rewards.claim(id,address(0)),18);vm.prank(alice);assertEq(rewards.claim(id,address(t1)),18);records=vm.getRecordedLogs();emit ExactLPWire(3,abi.encode(records),_snapshot(id));
        assertEq(rewards.liabilities(address(0)),0);assertEq(rewards.liabilities(address(t1)),0);assertEq(rewards.claimable(dormant,address(0)),0);
    }
}
