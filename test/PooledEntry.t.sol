// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Position} from "../src/libraries/ZZZTypes.sol";
contract PooledEntryTest is PooledVaultFixture {
    function testEntrySwapRepricingBelongsToIncumbents() public {
        uint256 first=activatedPosition();uint256 bucket=vault.nftBucket(first);
        uint256 lp=vault.group(bucket).lpTokenId;
        policy.setSwapAmount(10);venue.setRepricing(lp,20);
        uint256 second=_mint(bob);_activate(bob,second,1000,1000);
        assertEq(vault.sharesOf(first),2000e18);
        assertEq(vault.sharesOf(second),uint256(2000e18)*2000/2020);
        assertEq(vault.group(bucket).lpTokenId,lp);assertEq(venue.next(),2);
    }
    function testCompoundedNAVDoesNotBuyNewEntrantExtraShares() public {
        uint256 first=activatedPosition();uint256 bucket=vault.nftBucket(first);
        venue.setFees(100,100);vault.collectFees(bucket,block.timestamp+100);
        uint256 second=_mint(bob);_activate(bob,second,1000,1000);
        assertEq(vault.sharesOf(second),uint256(2000e18)*2000/2020);
        assertEq(rewards.claimable(second,address(t0)),0);
        assertEq(rewards.claimable(first,address(t0)),80);
        assertEq(power.powerOf(second),2000e18);assertEq(vault.bucketCount(),1);
    }
    function testDonationDoesNotReduceSharesPurchased() public {
        uint256 first=activatedPosition();uint256 second=_mint(bob);
        t0.mint(address(vault),1_000_000);_activate(bob,second,1000,1000);
        assertEq(vault.sharesOf(first),vault.sharesOf(second));
        Position memory p=vault.group(vault.nftBucket(first));
        assertEq(t0.balanceOf(address(vault)),p.idle0+1_000_000);
    }
    function testFeeDustSettlesToPreviousMembershipBeforeJoin() public {
        uint256 first=activatedPosition();uint256 bucket=vault.nftBucket(first);
        venue.setFees(9,9);vault.collectFees(bucket,block.timestamp+100);
        uint256 second=_mint(bob);_activate(bob,second,1000,1000);
        assertEq(rewards.claimable(first,address(t0)),9);
        assertEq(rewards.claimable(second,address(t0)),0);
        assertEq(fees.dust(bucket,address(t0)),0);
    }
}
