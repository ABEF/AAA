// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

// TEST ONLY: this provider accepts supplied authentication arguments deliberately.
// It models the router boundary, never a live bridge's authentication or backing.
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IZZZAccess} from "../../src/interfaces/IZZZ.sol";
import {PoolConfig, BridgeMessage, Route} from "../../src/libraries/ZZZTypes.sol";

interface IRouterCallbackFixture {
    function onProviderMessage(uint256 sourceChain, address sourceRouter,
        address[] calldata tokens, uint256[] calldata amounts, bytes calldata envelope) external;
}

contract RouterProviderMock {
    address public immutable router;
    bytes32 private configuration;
    uint256 public consumeBps = 10000;
    bool public zeroReceipt;
    bool public attemptReentry;
    bool public reentrySucceeded;
    bool public mutateDuringSend;
    uint256 public sends;
    bytes public lastEnvelope;
    address public lastDestinationRouter;
    address public lastDestinationProvider;

    constructor(address target, bytes32 configHash) { router = target; configuration = configHash; }
    function configurationHash(bytes32) external view returns (bytes32) { return configuration; }
    function setConfigurationHash(bytes32 value) external { configuration = value; }
    function setConsumeBps(uint256 value) external { consumeBps = value; }
    function setZeroReceipt(bool value) external { zeroReceipt = value; }
    function setAttemptReentry(bool value) external { attemptReentry = value; }
    function setMutateDuringSend(bool value) external { mutateDuringSend = value; }

    function send(bytes32, uint256 destinationChain, address destinationProvider, address destinationRouter,
        address[] calldata tokens, uint256[] calldata amounts, bytes calldata envelope)
        external payable returns (bytes32) {
        require(msg.sender == router, "only fixture router");
        if (attemptReentry) {
            (reentrySucceeded,) = router.call(abi.encodeWithSignature(
                "onProviderMessage(uint256,address,address[],uint256[],bytes)",
                destinationChain, destinationRouter, tokens, amounts, envelope));
        }
        for (uint256 i; i < tokens.length; ++i) {
            require(IERC20(tokens[i]).transferFrom(msg.sender, address(this), amounts[i] * consumeBps / 10000));
        }
        if (mutateDuringSend) configuration = keccak256("mutation inside provider send");
        lastEnvelope = envelope;
        lastDestinationRouter = destinationRouter;
        lastDestinationProvider = destinationProvider;
        sends++;
        return zeroReceipt ? bytes32(0) : bytes32(sends);
    }

    function deliver(uint256 sourceChain, address sourceRouter, address[] calldata tokens,
        uint256[] calldata amounts, bytes calldata envelope) external {
        for (uint256 i; i < tokens.length; ++i) require(IERC20(tokens[i]).approve(router, amounts[i]));
        IRouterCallbackFixture(router).onProviderMessage(sourceChain, sourceRouter, tokens, amounts, envelope);
        for (uint256 i; i < tokens.length; ++i) require(IERC20(tokens[i]).approve(router, 0));
    }
}

contract RouterVaultStub {
    IZZZAccess public immutable access;
    uint256 public immutable canonicalChainId;
    constructor(address controller, uint256 canonicalChain) {
        access = IZZZAccess(controller); canonicalChainId = canonicalChain;
    }
}

contract RouterPoolsStub {
    IZZZAccess public immutable access;
    PoolConfig private config;
    constructor(address controller, PoolConfig memory value) { access = IZZZAccess(controller); config = value; }
    function get(bytes32) external view returns (PoolConfig memory) { return config; }
}

interface IRouterRoutesFixture { function get(bytes32) external view returns (Route memory, bool); }

contract RouterReceiverStub {
    IZZZAccess public immutable access;
    IRouterRoutesFixture public registry;
    bool public reject;
    address public mutationProvider;
    uint256 public receipts;
    constructor(address controller) { access = IZZZAccess(controller); }
    function setRegistry(address target) external { registry = IRouterRoutesFixture(target); }
    function setReject(bool value) external { reject = value; }
    function setMutationProvider(address value) external { mutationProvider = value; }
    function receiveMessage(uint256, address, BridgeMessage calldata message) external {
        require(!reject, "fixture receipt failure");
        (Route memory route,) = registry.get(message.routeId);
        if (message.amount0 != 0) require(IERC20(route.destinationToken0).transferFrom(msg.sender, address(this), message.amount0));
        if (message.amount1 != 0) require(IERC20(route.destinationToken1).transferFrom(msg.sender, address(this), message.amount1));
        if (mutationProvider != address(0)) {
            RouterProviderMock(mutationProvider).setConfigurationHash(keccak256("mutation during destination handoff"));
        }
        receipts++;
    }
}
