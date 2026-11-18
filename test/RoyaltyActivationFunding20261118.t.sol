// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {InKindNFT} from "./RoyaltyRecovery.t.sol";
import {MockAccess,MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @dev A clipped read could lie with a valid ABI word rather than revert.
/// The reviewed 50k call always reaches the real balance branch.
contract FundingGasSensitiveCurrency is MockToken {
    address public reader;
    constructor() MockToken(6) {}
    function configure(address value) external {reader=value;}
    function balanceOf(address owner) public view override returns(uint256) {
        if(msg.sender==reader && gasleft()<40000)return 0;
        return super.balanceOf(owner);
    }
}

/// @notice NEW funding-witness tests; original units and old cohort stay exact.
contract RoyaltyActivationFunding20261118Test is Test {
    MockAccess private control;
    InKindNFT private nft;
    ZZZRoyaltyRewards private ledger;
    FundingGasSensitiveCurrency private asset;
    address private constant A=address(0xA11CE);
    address private constant B=address(0xB0B);

    function setUp() public {
        vm.warp(1000);control=new MockAccess();nft=new InKindNFT(address(control));
        ledger=nft.royalties();control.bind(Ids.NFT,address(nft));control.seal();
        asset=new FundingGasSensitiveCurrency();nft.add(address(asset));
        vm.prank(address(nft));ledger.setMintEnd(1200);
        nft.mint(A,1,0);nft.activate(1);nft.mint(B,2,0);
        vm.warp(4800);ledger.syncAll();asset.mint(address(ledger),5);ledger.sync(address(asset));
        asset.mint(address(ledger),7);asset.configure(address(ledger));
    }
    function _newActivation(uint256 gasLimit) private returns(bool ok) {
        vm.cool(address(nft));vm.cool(address(ledger));vm.cool(address(asset));
        (ok,)=address(nft).call{gas:gasLimit}(abi.encodeCall(InKindNFT.activate,(2)));
    }
    function _rightsAndDrain() private {
        assertEq(ledger.claimable(1,address(asset)),12);assertEq(ledger.claimable(2,address(asset)),0);
        asset.mint(address(ledger),2);ledger.sync(address(asset));
        vm.prank(A);assertEq(ledger.claim(1,address(asset)),13);
        vm.prank(B);assertEq(ledger.claim(2,address(asset)),1);
        assertEq(asset.balanceOf(A),13);assertEq(asset.balanceOf(B),1);
        assertEq(ledger.liabilities(address(asset)),0);assertEq(ledger.accounted(address(asset)),0);
        assertEq(asset.balanceOf(address(ledger)),0);vm.prank(B);assertEq(ledger.claim(2,address(asset)),0);
    }
    function testFundingHealthyPartialFrameStillForwardsFullReviewedReadAndSettles() public {
        // Below the old complete-frame preallocation, but enough for actual work.
        assertTrue(_newActivation(850000));assertEq(ledger.eligibleCount(address(asset)),2);
        assertEq(ledger.weightOf(2),1);_rightsAndDrain();
    }
    function testFundingStarvedReadCannotChooseDeferralOrSkipEarlierReceipts() public {
        bytes32 beforeState=keccak256(abi.encode(ledger.activationCount(),ledger.totalWeight(),
            ledger.accounted(address(asset)),ledger.liabilities(address(asset)),ledger.eligibleCount(address(asset))));
        assertFalse(_newActivation(170000));assertEq(ledger.weightOf(2),0);
        assertEq(keccak256(abi.encode(ledger.activationCount(),ledger.totalWeight(),
            ledger.accounted(address(asset)),ledger.liabilities(address(asset)),ledger.eligibleCount(address(asset)))),beforeState);
        assertTrue(_newActivation(850000));_rightsAndDrain();
    }
    function testFundingAuthenticatedReadFailureDefersWithoutWholeFrameReservation() public {
        // Reuse the adversarial token in the existing malformed-reader fixture
        // by a separate exact receiver context; no source or ledger state graft.
        FundingRevertingCurrency faulty=new FundingRevertingCurrency();nft.add(address(faulty));
        faulty.mint(address(ledger),5);ledger.sync(address(faulty));faulty.mint(address(ledger),7);
        faulty.configure(address(ledger));assertTrue(_newActivation(950000));
        assertEq(ledger.eligibleCount(address(faulty)),1);assertEq(ledger.weightOf(2),1);
        faulty.configure(address(0));ledger.sync(address(faulty));
        assertEq(ledger.claimable(1,address(faulty)),12);assertEq(ledger.claimable(2,address(faulty)),0);
        faulty.mint(address(ledger),2);ledger.sync(address(faulty));
        vm.prank(A);assertEq(ledger.claim(1,address(faulty)),13);
        vm.prank(B);assertEq(ledger.claim(2,address(faulty)),1);
        assertEq(faulty.balanceOf(A),13);assertEq(faulty.balanceOf(B),1);
        assertEq(ledger.liabilities(address(faulty)),0);assertEq(ledger.accounted(address(faulty)),0);
        _rightsAndDrain();
    }
}

contract FundingRevertingCurrency is MockToken {
    address private reader;
    constructor() MockToken(6) {}
    function configure(address value) external {reader=value;}
    function balanceOf(address owner) public view override returns(uint256) {
        if(msg.sender==reader)assembly("memory-safe"){invalid()}
        return super.balanceOf(owner);
    }
}
