// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ExactToken} from "../src/libraries/ExactToken.sol";
import {MockAccess,MockToken,MockFeed,TaxToken,ExtraTaxToken} from "./mocks/Mocks.sol";
contract TransferHarness {
    function pull(address t,uint256 n) external {ExactToken.pull(t,msg.sender,n);}
}
contract OracleAndTransfersTest is Test {
    MockAccess ac;MockToken t0;MockToken t1;MockFeed f0;MockFeed f1;ZZZOracle oracle;
    function setUp() public {
        vm.warp(1_000_000);ac=new MockAccess();t0=new MockToken(18);t1=new MockToken(6);
        f0=new MockFeed(8,2000e8);f1=new MockFeed(8,1e8);oracle=new ZZZOracle(address(ac),address(0));
        oracle.setFeed(address(t0),address(f0),3600);oracle.setFeed(address(t1),address(f1),3600);
    }
    function testDecimalNormalization() public {
        assertEq(oracle.price(address(t0)),2000e18);assertEq(oracle.value(address(t1),1e6),1e18);
        assertEq(oracle.quote(address(t0),address(t1),1e18),2000e6);
    }
    function testStaleRejected() public {vm.warp(block.timestamp+3601);vm.expectRevert();oracle.price(address(t0));}
    function testZeroRejected() public {f0.set(0,block.timestamp,block.timestamp);vm.expectRevert();oracle.price(address(t0));}
    function testNegativeRejected() public {f0.set(-1,block.timestamp,block.timestamp);vm.expectRevert();oracle.price(address(t0));}
    function testFutureTimestampRejected() public {f0.set(1,block.timestamp,block.timestamp+1);vm.expectRevert();oracle.price(address(t0));}
    function testIncompleteRoundRejected() public {f0.rounds(10,9);vm.expectRevert();oracle.price(address(t0));}
    function testUnknownFeedRejected() public {vm.expectRevert();oracle.price(address(0x123));}
    function testSequencerDownRejected() public {
        MockFeed seq=new MockFeed(0,1);ZZZOracle l2=new ZZZOracle(address(ac),address(seq));
        l2.setFeed(address(t0),address(f0),3600);vm.expectRevert();l2.price(address(t0));
    }
    function testSequencerGraceThenRecovery() public {
        MockFeed seq=new MockFeed(0,0);ZZZOracle l2=new ZZZOracle(address(ac),address(seq));
        l2.setFeed(address(t0),address(f0),3600);vm.expectRevert();l2.price(address(t0));
        vm.warp(block.timestamp+3601);f0.set(2000e8,block.timestamp,block.timestamp);assertEq(l2.price(address(t0)),2000e18);
    }
    function testTaxedTokenRejectedAtomically() public {
        TaxToken tax=new TaxToken();TransferHarness target=new TransferHarness();tax.mint(address(this),100);tax.approve(address(target),100);
        vm.expectRevert();target.pull(address(tax),100);assertEq(tax.balanceOf(address(this)),100);
    }
    function testExtraSenderTaxRejectedAtomically() public {
        ExtraTaxToken tax=new ExtraTaxToken();TransferHarness target=new TransferHarness();tax.mint(address(this),110);tax.approve(address(target),100);
        vm.expectRevert();target.pull(address(tax),100);assertEq(tax.balanceOf(address(this)),110);
    }
    function testConventionalTokenAccepted() public {
        TransferHarness target=new TransferHarness();t0.mint(address(this),100);t0.approve(address(target),100);
        target.pull(address(t0),100);assertEq(t0.balanceOf(address(target)),100);
    }
    function testFuzzQuoteMonotonic(uint96 a,uint96 b) public {
        if(a>b)(a,b)=(b,a);assertLe(oracle.quote(address(t0),address(t1),a),oracle.quote(address(t0),address(t1),b));
    }
}
