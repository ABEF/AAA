// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZBridgeAdapter} from "../src/ZZZBridgeAdapter.sol";
import {Ids,Route,BridgeMessage,MessageKind} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockToken,MockRoutes,MockMessageReceiver,MockTransport} from "./mocks/Mocks.sol";
contract BridgeSecurityTest is Test {
    MockAccess ac;MockToken token;MockRoutes routes;MockMessageReceiver receiver;MockTransport transport;ZZZBridgeAdapter bridge;
    address source=address(0x5150);uint256 remote=54321;bytes32 routeId=keccak256("test-route");
    function setUp() public {
        vm.chainId(31337);ac=new MockAccess();token=new MockToken(18);routes=new MockRoutes();receiver=new MockMessageReceiver();
        transport=new MockTransport();bridge=new ZZZBridgeAdapter(address(ac),address(transport));
        ac.bind(Ids.BRIDGE,address(bridge));ac.bind(Ids.RECEIVER,address(receiver));ac.bind(Ids.ROUTES,address(routes));ac.bind(Ids.VAULT,address(this));
        receiver.configure(address(token),false);
        Route memory r;r.sourceChain=remote;r.sourceAdapter=source;r.sourceVault=address(0x51);r.sourceReceiver=address(0x52);
        r.destinationChain=block.chainid;r.destinationAdapter=address(bridge);r.destinationVault=address(this);r.destinationReceiver=address(receiver);
        r.sourceToken0=address(0x77);r.destinationToken0=address(token);routes.set(routeId,r);ac.seal();
    }
    function message() private view returns(BridgeMessage memory m){
        m.version=3;m.kind=MessageKind.Reward;m.routeId=routeId;m.nonce=1;m.bucketId=42;m.amount0=80;m.individual=50;m.collective=30;
    }
    function deliver(BridgeMessage memory m) private {transport.deliver(address(bridge),remote,source,abi.encode(m),address(token),m.amount0);}
    function testAuthenticatedFundedDelivery() public {
        token.mint(address(transport),80);deliver(message());assertEq(token.balanceOf(address(receiver)),80);
        assertEq(receiver.received(),1);assertEq(token.allowance(address(bridge),address(receiver)),0);
    }
    function testReplayRejected() public {
        token.mint(address(transport),160);BridgeMessage memory m=message();deliver(m);vm.expectRevert();deliver(m);assertEq(receiver.received(),1);
    }
    function testUnfundedMessageRevertsAndNonceNotConsumed() public {
        BridgeMessage memory m=message();vm.expectRevert();deliver(m);
        assertFalse(bridge.processed(keccak256(abi.encode(remote,source,m.nonce))));
        token.mint(address(transport),80);deliver(m);assertEq(receiver.received(),1);
    }
    function testDirectCallerCannotDeliver() public {vm.expectRevert();bridge.onMessage(remote,source,abi.encode(message()));}
    function testWrongSourceRejected() public {
        token.mint(address(transport),80);vm.expectRevert();transport.deliver(address(bridge),remote,address(0xBAD),abi.encode(message()),address(token),80);
    }
    function testReceiverFailureIsRetryable() public {
        token.mint(address(transport),80);receiver.configure(address(token),true);BridgeMessage memory m=message();vm.expectRevert();deliver(m);
        assertEq(token.balanceOf(address(transport)),80);receiver.configure(address(token),false);deliver(m);assertEq(receiver.received(),1);
    }
    function testInboundAllowedDuringPause() public {ac.setPaused(true);token.mint(address(transport),80);deliver(message());assertEq(receiver.received(),1);}
    function testIncorrectAllocationRejected() public {
        token.mint(address(transport),80);BridgeMessage memory m=message();m.collective=31;vm.expectRevert();deliver(m);
    }
    function testVersionMismatchRejected() public {
        token.mint(address(transport),80);BridgeMessage memory m=message();m.version=1;vm.expectRevert();deliver(m);
    }
    function testOutboundUnauthorized() public {vm.expectRevert();bridge.send(message());}
}
