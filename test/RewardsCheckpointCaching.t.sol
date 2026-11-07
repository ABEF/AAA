// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {RewardsAndFeesTest} from "./RewardsAndFees.t.sol";
import {IZZZVault, IZZZMembership} from "../src/interfaces/IZZZ.sol";

/// @notice Fresh7 synchronization replaces obsolete33-LP-asset index loops.
/// Original source is archived before this explicit fixed-pair maintenance.
contract RewardsCheckpointCachingTest is RewardsAndFeesTest {
    function _creditBoth(uint256 personal,uint256 shared)private{
        _credit(personal,shared);uint256 amount=personal+shared;vm.deal(address(fees),amount);
        vm.prank(address(fees));rewards.creditPool{value:amount}(BUCKET,address(0),personal,shared);
    }
    function testBothBooksPreserveOldWholeRightsBeforeGrowth()public{
        vault.join(2,BUCKET,200);_activate(2);_creditBoth(7,5);
        uint256 eth=rewards.claimable(1,address(0));uint256 zzz=rewards.claimable(1,address(token));
        vault.join(1,BUCKET,100);assertEq(rewards.claimable(1,address(0)),eth);assertEq(rewards.claimable(1,address(token)),zzz);
    }
    function testDormantExcludesBothBooksPastRights()public{
        _creditBoth(7,5);vault.join(2,BUCKET,100);_activate(2);
        assertEq(rewards.claimable(2,address(0)),0);assertEq(rewards.claimable(2,address(token)),0);
    }
    function testShareSyncReadsEachCanonicalWriterValueOnce()public{
        vm.expectCall(address(vault),abi.encodeCall(IZZZVault.nftBucket,(1)),uint64(1));
        vm.expectCall(address(vault),abi.encodeCall(IZZZVault.sharesOf,(1)),uint64(1));
        vm.expectCall(address(vault),abi.encodeCall(IZZZVault.bucketTotalShares,(BUCKET)),uint64(1));
        vm.prank(address(vault));rewards.syncShares(1);
    }
    function testMembershipSyncReadsPostActivationStateOnce()public{
        vault.join(2,BUCKET,100);
        vm.expectCall(address(membership),abi.encodeCall(IZZZMembership.eligible,(2)),uint64(1));
        vm.expectCall(address(membership),abi.encodeCall(IZZZMembership.totalEligible,()),uint64(1));_activate(2);
    }
    function testBenchmarkActualOwnerGrowthSettlesBothBooks()public{
        _creditBoth(7,5);vm.cool(address(rewards));vm.cool(address(vault));vm.cool(address(nft));vm.cool(address(ac));
        uint256 beforeGas=gasleft();vault.join(1,BUCKET,100);emit log_named_uint("owner_sync_two_book_fixture_gas",beforeGas-gasleft());
    }
    function testBenchmarkMembershipActivationSettlesBothBooks()public{
        _creditBoth(7,5);vault.join(2,BUCKET,100);vm.cool(address(rewards));vm.cool(address(membership));vm.cool(address(nft));vm.cool(address(ac));
        uint256 beforeGas=gasleft();_activate(2);emit log_named_uint("collective_sync_two_book_fixture_gas",beforeGas-gasleft());
        assertEq(rewards.claimable(2,address(0)),0);assertEq(rewards.claimable(2,address(token)),0);
    }
}
