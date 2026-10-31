// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";

/// @dev Minimal terminal-flag/callback fixture. It does not grant production
/// Access authority or replace the separate complete collective-exit tests.
contract PrincipalFlagFixture {
    bool public lpExitStarted;
    uint256 public callbacks;
    function endLP() external { lpExitStarted=true; }
    function callback(bool end) external { ++callbacks;if(end)lpExitStarted=true; }
}
contract PrincipalGuardFixture is ZZZModule {
    uint256 public writes;
    constructor(address controller)ZZZModule(controller){}
    function run(bool end)external principalOperating {
        ++writes;
        PrincipalFlagFixture(address(access)).callback(end);
    }
}
contract PrincipalOperatingGuardTest is Test {
    PrincipalFlagFixture private flag;
    PrincipalGuardFixture private guard;
    function setUp()public {flag=new PrincipalFlagFixture();guard=new PrincipalGuardFixture(address(flag));}
    function testNormalOperationCompletesWithBothWrites()public {
        guard.run(false);assertEq(guard.writes(),1);assertEq(flag.callbacks(),1);assertFalse(flag.lpExitStarted());
    }
    function testAlreadyTerminalRejectsBeforeBodyOrCallback()public {
        flag.endLP();vm.expectRevert(ZZZModule.LPExitLocked.selector);guard.run(false);
        assertEq(guard.writes(),0);assertEq(flag.callbacks(),0);assertTrue(flag.lpExitStarted());
    }
    function testTerminalCallbackRejectsAtEndAndRollsBackAllWrites()public {
        vm.expectRevert(ZZZModule.LPExitLocked.selector);guard.run(true);
        assertEq(guard.writes(),0);assertEq(flag.callbacks(),0);assertFalse(flag.lpExitStarted());
        guard.run(false);assertEq(guard.writes(),1);assertEq(flag.callbacks(),1);
    }
}
