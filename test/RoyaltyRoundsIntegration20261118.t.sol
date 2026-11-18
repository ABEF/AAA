// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {InKindNFT} from "./RoyaltyRecovery.t.sol";
import {MockAccess,MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @dev Faults affect only the receiver's read, not the independent test oracle.
contract RoundsMalformedCurrency is MockToken {
    address public reader;
    uint8 public mode;
    constructor() MockToken(6) {}
    function configure(address who,uint8 value) external {reader=who;mode=value;}
    function balanceOf(address who) public view override returns(uint256) {
        if(msg.sender==reader) {
            uint256 selected=mode;
            if(selected==1)assembly("memory-safe"){invalid()}
            if(selected==2)revert("read rejected");
            if(selected==3)assembly("memory-safe"){mstore(0,0)return(0,31)}
            if(selected==4)assembly("memory-safe"){mstore(0,0)return(0,64)}
            if(selected==5)assembly("memory-safe"){return(0,65536)}
            if(selected==6)return 0;
            if(selected==7 || selected==8) {
                uint256 actual=super.balanceOf(who);
                assembly("memory-safe") {
                    mstore(0,actual)
                    mstore(32,0xdeadbeef)
                    if eq(selected,7){return(0,64)}
                    return(0,65536)
                }
            }
        }
        return super.balanceOf(who);
    }
}

/// @notice NEW actual-ledger regressions, beyond the reused affected Q03 cases.
/// No physical LP or provider/gas qualification is inferred from this component.
contract RoyaltyRoundsIntegration20261118Test is Test {
    address private constant A=address(0xA11CE);
    address private constant B=address(0xB0B);
    address private constant C=address(0xCA701);
    address private constant D=address(0xDA1);
    address private constant E=address(0xE1E);
    MockAccess private control;
    InKindNFT private nft;
    ZZZRoyaltyRewards private ledger;
    MockToken private token;

    function setUp() public {
        vm.warp(1000);control=new MockAccess();nft=new InKindNFT(address(control));
        ledger=nft.royalties();control.bind(Ids.NFT,address(nft));control.seal();
        token=new MockToken(6);nft.add(address(token));
        vm.prank(address(nft));ledger.setMintEnd(1200);
    }
    function _mint(uint256 id,uint8 rarity,address owner) private {nft.mint(owner,id,rarity);nft.activate(id);}
    function _open() private {vm.warp(4800);ledger.syncAll();}
    function _credit(uint256 amount) private {token.mint(address(ledger),amount);ledger.sync(address(token));}
    function _claim(InKindNFT collection,ZZZRoyaltyRewards receiver,address asset,uint256 id,uint256 expected) private {
        address owner=collection.ownerOf(id);uint256 before=MockToken(asset).balanceOf(owner);
        vm.prank(owner);assertEq(receiver.claim(id,asset),expected);
        assertEq(MockToken(asset).balanceOf(owner)-before,expected);
    }
    function _empty(ZZZRoyaltyRewards receiver,address asset) private view {
        assertEq(receiver.liabilities(asset),0);assertEq(receiver.accounted(asset),0);
        assertEq(receiver.pending(asset),0);assertEq(receiver.orphaned(asset),0);
        assertEq(MockToken(asset).balanceOf(address(receiver)),0);
    }

    function testRoundsActualRawCursorConversionAndTransferRetainBothHistories() public {
        _mint(1,1,A);_mint(2,1,B);_open();_credit(1);
        assertEq(ledger.allocationCursor(address(token)),2);
        assertEq(ledger.claimable(1,address(token)),1);assertEq(ledger.claimable(2,address(token)),0);
        _mint(3,2,C);assertEq(ledger.claimable(3,address(token)),0);
        // The inherited cursor is RAW2, so the next unit belongs to rawticket3/B.
        _credit(1);assertEq(ledger.claimable(1,address(token)),1);
        assertEq(ledger.claimable(2,address(token)),1);assertEq(ledger.claimable(3,address(token)),0);
        _claim(nft,ledger,address(token),2,1);_credit(7);
        vm.prank(A);nft.transferFrom(A,D,1);
        vm.prank(A);vm.expectRevert();ledger.claim(1,address(token));
        _claim(nft,ledger,address(token),1,3);_claim(nft,ledger,address(token),2,2);
        _claim(nft,ledger,address(token),3,3);_claim(nft,ledger,address(token),1,0);
        assertEq(token.totalSupply(),9);_empty(ledger,address(token));
    }

    function testRoundsActualFaultCatchupSnapshotsNewPhaseInsteadOfOldElevenRounds() public {
        RoundsMalformedCurrency fault=new RoundsMalformedCurrency();nft.add(address(fault));
        _mint(1,1,A);_mint(2,1,B);_open();fault.mint(address(ledger),22);ledger.sync(address(fault));
        _claim(nft,ledger,address(fault),2,11);
        fault.configure(address(ledger),1);_mint(3,2,C);_mint(4,1,D);
        assertEq(ledger.eligibleCount(address(fault)),2);fault.mint(address(ledger),5);
        fault.configure(address(0),0);ledger.sync(address(fault));
        assertEq(ledger.eligibleCount(address(fault)),4);
        assertEq(ledger.claimable(1,address(fault)),14);assertEq(ledger.claimable(2,address(fault)),2);
        assertEq(ledger.claimable(3,address(fault)),0);assertEq(ledger.claimable(4,address(fault)),0);
        fault.mint(address(ledger),9);ledger.sync(address(fault));
        vm.prank(D);nft.transferFrom(D,E,4);
        _claim(nft,ledger,address(fault),1,16);_claim(nft,ledger,address(fault),2,4);
        _claim(nft,ledger,address(fault),3,3);_claim(nft,ledger,address(fault),4,2);
        assertEq(fault.balanceOf(B),15);_empty(ledger,address(fault));
    }

    function testRoundsActualImportedCursorSplitAndAccruedNeverBecomeCounterDebt() public {
        _mint(1,0,A);_mint(2,2,B);_open();_credit(3);
        _claim(nft,ledger,address(token),1,1);
        assertEq(ledger.allocationCursor(address(token)),3);assertEq(ledger.liabilities(address(token)),2);
        MockAccess destination=new MockAccess();InKindNFT nextNFT=new InKindNFT(address(destination));
        ZZZRoyaltyRewards next=nextNFT.royalties();nextNFT.mint(A,1,0);nextNFT.mint(B,2,2);
        destination.bind(Ids.NFT,address(nextNFT));destination.bind(Ids.CANONICAL,address(this));destination.seal();
        control.bind(Ids.CANONICAL,address(this));control.setCanonicalState(1);destination.setCanonicalState(2);
        ledger.canonicalCapture();ledger.canonicalSettle();
        for(uint256 row;row<ledger.canonicalCount();++row)next.canonicalImport(row,ledger.canonicalExport(row));
        vm.expectRevert();next.canonicalValidate();
        for(uint256 i;i<2;++i){ledger.canonicalRelease(i,address(next));next.canonicalAccept(i,address(ledger));}
        next.canonicalValidate();next.canonicalActivate();control.setCanonicalState(3);destination.setCanonicalState(0);
        assertEq(next.claimable(1,address(token)),0);assertEq(next.claimable(2,address(token)),2);
        _claim(nextNFT,next,address(token),2,2);_empty(next,address(token));
        token.mint(address(next),4);
        assertEq(next.claimable(1,address(token)),1);assertEq(next.claimable(2,address(token)),3);
        next.sync(address(token));_claim(nextNFT,next,address(token),1,1);_claim(nextNFT,next,address(token),2,3);
        _claim(nextNFT,next,address(token),2,0);_empty(next,address(token));
        assertEq(token.balanceOf(A),2);assertEq(token.balanceOf(B),5);
    }

    function testRoundsActualMalformedRevertingBombAndUnderBackingReadsStayIsolated() public {
        RoundsMalformedCurrency[6] memory faulty;
        for(uint256 i;i<6;++i){faulty[i]=new RoundsMalformedCurrency();nft.add(address(faulty[i]));}
        _mint(1,0,A);_open();
        for(uint256 i;i<6;++i){faulty[i].mint(address(ledger),5);ledger.sync(address(faulty[i]));
            faulty[i].mint(address(ledger),7);faulty[i].configure(address(ledger),uint8(i+1));}
        _mint(2,1,B);assertEq(ledger.activationCount(),2);
        for(uint256 i;i<6;++i){
            assertEq(ledger.eligibleCount(address(faulty[i])),1);
            faulty[i].configure(address(0),0);ledger.sync(address(faulty[i]));
            assertEq(ledger.claimable(1,address(faulty[i])),12);assertEq(ledger.claimable(2,address(faulty[i])),0);
            faulty[i].mint(address(ledger),3);ledger.sync(address(faulty[i]));
            _claim(nft,ledger,address(faulty[i]),1,13);_claim(nft,ledger,address(faulty[i]),2,2);
            _empty(ledger,address(faulty[i]));
        }
    }

    function testRoundsActualHighReadCeilingAllowsCheapTokenAndOuterUnderfundingRollsBack() public {
        _mint(1,0,A);_open();nft.mint(B,2,1);token.mint(address(ledger),7);
        ZZZProtocolPolicy(control.protocolPolicy()).setRoyaltyBalanceGas(1000000,keccak256("TEST ONLY upper read ceiling"));
        // A maximum is not a minimum that cheap conventional reads must burn.
        // The original full-frame guard must still prevent selective deferral.
        (bool ok,)=address(nft).call{gas:250000}(abi.encodeCall(InKindNFT.activate,(2)));
        assertFalse(ok);assertEq(ledger.activationCount(),1);assertEq(ledger.weightOf(2),0);
        assertEq(ledger.eligibleCount(address(token)),1);assertEq(ledger.pending(address(token)),7);
        nft.activate(2);assertEq(ledger.eligibleCount(address(token)),2);
        assertEq(ledger.claimable(1,address(token)),7);assertEq(ledger.claimable(2,address(token)),0);
        _claim(nft,ledger,address(token),1,7);_empty(ledger,address(token));
    }

    function testRoundsActualPaddedAndLargeValidABIReturnsKeepTheirOriginalEntitlements() public {
        RoundsMalformedCurrency[2] memory padded;
        for(uint256 i;i<2;++i){padded[i]=new RoundsMalformedCurrency();nft.add(address(padded[i]));}
        _mint(1,0,A);_open();
        for(uint256 i;i<2;++i){padded[i].mint(address(ledger),5);ledger.sync(address(padded[i]));
            padded[i].mint(address(ledger),7);padded[i].configure(address(ledger),uint8(7+i));}
        // Solidity's existing uint256 ABI decoder accepts trailing output.
        // Copy only32bytes, without inventing an exact-length entitlement fault.
        _mint(2,1,B);
        for(uint256 i;i<2;++i){
            assertEq(ledger.eligibleCount(address(padded[i])),2);
            assertEq(ledger.claimable(1,address(padded[i])),12);assertEq(ledger.claimable(2,address(padded[i])),0);
            padded[i].configure(address(0),0);padded[i].mint(address(ledger),3);ledger.sync(address(padded[i]));
            _claim(nft,ledger,address(padded[i]),1,13);_claim(nft,ledger,address(padded[i]),2,2);
            _empty(ledger,address(padded[i]));
        }
    }
}
