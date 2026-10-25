// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockToken} from "./mocks/Mocks.sol";
import {PoolConfig} from "../src/libraries/ZZZTypes.sol";

interface ILPOnlyEntryCallback { function contributionCallback() external; }

/// @dev TEST ONLY callback-capable runtime substitution with the same ERC20
/// storage layout. It does not represent the current public ZZZ implementation.
contract LPOnlyCallbackToken is MockToken {
    address private target;
    address private watched;
    bool private fired;
    constructor() MockToken(0) {}
    function configure(address callback,address recipient) external {
        target=callback;watched=recipient;fired=false;
    }
    function _update(address from,address to,uint256 amount) internal override {
        super._update(from,to,amount);
        if (!fired && target!=address(0) && to==watched && amount!=0) {
            fired=true;
            ILPOnlyEntryCallback(target).contributionCallback();
        }
    }
}

/// @notice Real Vault/price/LP-reward/membership state machines with a local
/// liquidity mock. Tests the one pre-entry global dust barrier after removal of
/// creator-receipt ingress; it is not actual venue or token qualification.
contract LPOnlyEntryBoundaryTest is PooledVaultFixture {
    uint256 private incumbentBucket;
    bool private callbackObserved;
    bool private collectionAccepted;
    bool private membershipAccepted;
    bool private allocationAccepted;

    function contributionCallback() external {
        require(msg.sender==address(t0));
        callbackObserved=true;
        // Raw gifts cannot manufacture LP-fee accounting or change membership.
        t0.mint(address(fees),211);
        t0.mint(address(rewards),223);
        (bool received,) = address(fees).call{value:17}("");require(received);
        (received,) = address(rewards).call{value:29}("");require(received);
        // Even during callbacks no public path can collect another bucket's
        // fees under the Vault lock or invoke the fixed-Vault dust authority.
        (collectionAccepted,) = address(vault).call(abi.encodeWithSignature(
            "collectFees(uint256,uint256)",incumbentBucket,block.timestamp+100));
        (membershipAccepted,) = address(membership).call(abi.encodeWithSignature("settleDust()"));
        (allocationAccepted,) = address(fees).call(abi.encodeWithSignature(
            "allocate(uint256,address,uint256)",incumbentBucket,address(t0),uint256(20)));
    }

    function _donationDuringEntry(address watched) private {
        uint256 incumbent=activatedPosition();incumbentBucket=vault.nftBucket(incumbent);
        venue.setFees(19,19);vault.collectFees(incumbentBucket,block.timestamp+100);
        assertEq(fees.dust(incumbentBucket,address(t0)),19);
        assertEq(rewards.claimable(incumbent,address(t0)),0);
        uint256 entrant=_mint(bob);
        PoolConfig memory config=pools.get(poolId);config.key.fee=500;
        bytes32 other=keccak256(abi.encode(config.key));pools.set(other,config);
        LPOnlyCallbackToken implementation=new LPOnlyCallbackToken();
        vm.etch(address(t0),address(implementation).code);
        LPOnlyCallbackToken(address(t0)).configure(address(this),watched);
        vm.prank(bob);vault.activate(entrant,other,1000,1000,1,block.timestamp+100);

        assertTrue(callbackObserved);
        assertFalse(collectionAccepted);assertFalse(membershipAccepted);assertFalse(allocationAccepted);
        assertEq(membership.totalEligible(),2);
        assertEq(fees.dust(incumbentBucket,address(t0)),0);
        assertEq(fees.dust(incumbentBucket,address(t1)),0);
        assertEq(rewards.claimable(incumbent,address(t0)),19);
        assertEq(rewards.claimable(incumbent,address(t1)),19);
        assertEq(rewards.claimable(entrant,address(t0)),0);
        assertEq(rewards.claimable(entrant,address(t1)),0);
        assertEq(rewards.claimable(entrant,address(0)),0);
        assertEq(fees.accounted(address(t0)),0);
        assertEq(fees.accounted(address(0)),0);
        assertEq(rewards.liabilities(address(t0)),19);
        assertEq(rewards.liabilities(address(0)),0);
        assertEq(rewards.index(address(t0)),0);
        assertEq(rewards.orphaned(address(t0)),0);
        assertEq(t0.balanceOf(address(fees)),211);
        assertEq(t0.balanceOf(address(rewards)),242);
        assertEq(address(fees).balance,17);assertEq(address(rewards).balance,29);
        assertGt(vault.sharesOf(entrant),0);
        assertFalse(oracle.contributionPricing().active());
    }

    function testTokenPullDonationAndCallbackCannotCreateCrossBucketRevenue() public {
        _donationDuringEntry(address(vault));
    }
    function testLPPlacementDonationAndCallbackCannotCreateCrossBucketRevenue() public {
        _donationDuringEntry(address(venue));
    }
}
