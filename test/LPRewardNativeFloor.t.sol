// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZLPRewardConverter} from "../src/ZZZLPRewardConverter.sol";
import {ZZZRewardConverter} from "../src/base/ZZZRewardConverter.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {IV3RouteRouter} from "../src/interfaces/IZZZV3Route.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

// TEST ONLY: independent fixture instances are controlled inputs, not qualified
// production feeds, venues, proxy dependencies, authority or liquidity.
contract NativeFloorGasPolicy {
    function sourceCallGas() external pure returns (uint32) { return 500000; }
}
contract NativeFloorAccess {
    address public immutable governance = msg.sender;
    address public immutable protocolPolicy = address(new NativeFloorGasPolicy());
    mapping(bytes32 => address) public module;
    bool public isSealed;
    bool public paused;
    bool public preparationActive;
    uint8 public canonicalState;
    function canConfigure(address caller) external view returns (bool) { return caller == governance; }
    function bind(bytes32 id, address target) external { module[id] = target; }
    function seal() external { isSealed = true; }
}
contract NativeFloorFeed {
    uint8 public constant decimals = 8;
    int256 public immutable answer;
    uint256 public immutable updated;
    constructor(int256 value, uint256 timestamp) { answer = value; updated = timestamp; }
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        return (1, answer, updated, updated, 1);
    }
}
contract NativeFloorToken is ERC20 {
    constructor() ERC20("Source fixture", "SOURCE") {}
    function decimals() public pure override returns (uint8) { return 6; }
    function mint(address receiver, uint256 amount) external { _mint(receiver, amount); }
}
contract NativeFloorWrapper is ERC20 {
    uint8 private digits = 18;
    uint256 public payoutBps = 10000;
    constructor() ERC20("Wrapper fixture", "WRAPPED") {}
    function initializeProxyFixture() external { digits = 18; payoutBps = 10000; }
    function decimals() public view override returns (uint8) { return digits; }
    function setDecimals(uint8 value) external { digits = value; }
    function setPayoutBps(uint256 value) external { payoutBps = value; }
    function mint(address receiver, uint256 amount) external { _mint(receiver, amount); }
    function withdraw(uint256 amount) external {
        _burn(msg.sender, amount);
        (bool ok,) = msg.sender.call{value: amount * payoutBps / 10000}("");
        require(ok, "fixture native transfer");
    }
    receive() external payable {}
}
contract NativeFloorWrapperReplacement is NativeFloorWrapper {
    function fixtureRevision() external pure returns (uint256) { return 2; }
}
contract NativeFloorProxy {
    bytes32 private constant IMPLEMENTATION_SLOT = bytes32(uint256(keccak256("eip1967.proxy.implementation")) - 1);
    bytes32 private constant ADMIN_SLOT = bytes32(uint256(keccak256("eip1967.proxy.admin")) - 1);
    constructor(address controller, address implementation_) {
        bytes32 a = ADMIN_SLOT; bytes32 i = IMPLEMENTATION_SLOT;
        assembly { sstore(a, controller) sstore(i, implementation_) }
    }
    function admin() public view returns (address value) {
        bytes32 slot = ADMIN_SLOT; assembly { value := sload(slot) }
    }
    function implementation() public view returns (address value) {
        bytes32 slot = IMPLEMENTATION_SLOT; assembly { value := sload(slot) }
    }
    function upgrade(address target) external {
        require(msg.sender == admin(), "fixture proxy admin");
        bytes32 slot = IMPLEMENTATION_SLOT; assembly { sstore(slot, target) }
    }
    fallback() external payable {
        address target = implementation();
        assembly {
            calldatacopy(0, 0, calldatasize())
            let ok := delegatecall(gas(), target, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch ok case 0 { revert(0, returndatasize()) } default { return(0, returndatasize()) }
        }
    }
}
contract NativeFloorProxyAdmin {
    address public immutable owner = msg.sender;
    function getProxyAdmin(address proxy) external view returns (address) {
        return NativeFloorProxy(payable(proxy)).admin();
    }
    function getProxyImplementation(address proxy) external view returns (address) {
        return NativeFloorProxy(payable(proxy)).implementation();
    }
    function upgrade(address proxy, address implementation_) external {
        require(msg.sender == owner, "fixture owner");
        NativeFloorProxy(payable(proxy)).upgrade(implementation_);
    }
}
contract NativeFloorVenue {
    address public immutable factory = address(this);
    address public immutable source;
    NativeFloorWrapper public immutable wrapper;
    address public immutable token0;
    address public immutable token1;
    uint24 public constant fee = 500;
    uint256 public output = 0.99 ether;
    bool public lie;
    constructor(address asset, NativeFloorWrapper wrapped) {
        source = asset; wrapper = wrapped;
        token0 = asset < address(wrapped) ? asset : address(wrapped);
        token1 = asset < address(wrapped) ? address(wrapped) : asset;
    }
    function getPool(address a, address b, uint24 f) external view returns (address) {
        return ((a == token0 && b == token1) || (a == token1 && b == token0)) && f == fee
            ? address(this) : address(0);
    }
    function setOutput(uint256 amount, bool returnLie) external { output = amount; lie = returnLie; }
    function exactInputSingle(IV3RouteRouter.ExactInputSingleParams calldata p) external payable returns (uint256) {
        require(p.tokenIn == source && p.tokenOut == address(wrapper) && p.fee == fee, "fixture route");
        require(IERC20(source).transferFrom(msg.sender, address(this), p.amountIn), "fixture source");
        // Deliberately ignores the supplied minimum: the converter must check it.
        wrapper.mint(p.recipient, output);
        return lie ? output + 1 : output;
    }
}
/// @dev Accounting seam only: actual converter/oracle, synthetic earned balance.
/// Full Rewards7 NFT/tree/canonical behavior belongs to its separate host tests.
contract NativeFloorLedger {
    IERC20 public immutable source;
    ZZZLPRewardConverter public converter;
    uint256 public earned;
    uint256 public sourceLiability;
    uint256 public nativeCredit;
    uint256 public nativeLiability;
    constructor(address asset) { source = IERC20(asset); }
    receive() external payable {}
    function bind(ZZZLPRewardConverter target) external { converter = target; }
    function credit(uint256 amount) external { earned += amount; sourceLiability += amount; }
    function convert(bytes32 route, uint256 minimum, uint256 deadline) external returns (uint256 output) {
        uint256 amount = earned; earned = 0; sourceLiability -= amount;
        require(source.approve(address(converter), amount), "fixture approve");
        output = converter.convert(address(source), amount, route, minimum, deadline);
        require(source.approve(address(converter), 0), "fixture clear");
        nativeCredit += output; nativeLiability += output;
    }
}

contract LPRewardNativeFloorTest is Test {
    NativeFloorAccess private access;
    NativeFloorToken private token;
    NativeFloorWrapper private wrapper;
    NativeFloorLedger private ledger;
    NativeFloorVenue private venue;
    ZZZLPRewardConverter private converter;
    ZZZOracle private oracle;
    bytes32 private routeId;
    uint256 private constant SOURCE = 2000e6;

    function setUp() public {
        vm.warp(100000);
        access = new NativeFloorAccess(); token = new NativeFloorToken(); wrapper = new NativeFloorWrapper();
        ledger = new NativeFloorLedger(address(token));
        oracle = new ZZZOracle(address(access), address(0)); access.bind(Ids.ORACLE, address(oracle));
        _price(address(token), 1e8, block.timestamp); _price(address(wrapper), 2000e8, block.timestamp);
        converter = new ZZZLPRewardConverter(address(access), address(ledger), address(wrapper));
        ledger.bind(converter); converter.configureWrapper(_wrapperPolicy(address(wrapper)));
        venue = new NativeFloorVenue(address(token), wrapper);
        routeId = converter.addRoute(ZZZRewardConverter.RoutePolicy(address(token), address(venue), address(venue),
            address(venue), 500, address(token).codehash, address(venue).codehash, address(venue).codehash,
            address(venue).codehash, keccak256("controlled native-floor venue")));
        converter.setEnabled(true); access.seal();
        token.mint(address(ledger), SOURCE); ledger.credit(SOURCE); vm.deal(address(wrapper), 10 ether);
    }
    function _price(address asset, int256 value, uint256 timestamp) private {
        NativeFloorFeed first = new NativeFloorFeed(value, timestamp);
        NativeFloorFeed second = new NativeFloorFeed(value, timestamp);
        oracle.setDualFeed(asset,
            ZZZOracle.SourcePolicy(address(first), address(first).codehash, keccak256(abi.encode("first", first)), 3600, 8),
            ZZZOracle.SourcePolicy(address(second), address(second).codehash, keccak256(abi.encode("second", second)), 3600, 8),
            0, keccak256("controlled feed pair; not production independence"));
    }
    function _wrapperPolicy(address target) private view returns (ZZZRewardConverter.WrapperPolicy memory) {
        return ZZZRewardConverter.WrapperPolicy(target.codehash, address(0), address(0), address(0), 0, 0,
            keccak256("controlled native-floor wrapper"));
    }
    function _convert(uint256 minimum) private returns (uint256) {
        return ledger.convert(routeId, minimum, block.timestamp + 60);
    }
    function _unchanged() private view {
        assertEq(ledger.earned(), SOURCE); assertEq(ledger.sourceLiability(), SOURCE);
        assertEq(token.balanceOf(address(ledger)), SOURCE); assertEq(token.balanceOf(address(converter)), 0);
        assertEq(token.balanceOf(address(venue)), 0); assertEq(ledger.nativeCredit(), 0);
        assertEq(ledger.nativeLiability(), 0); assertEq(address(ledger).balance, 0);
        assertEq(token.allowance(address(ledger), address(converter)), 0);
        assertEq(token.allowance(address(converter), address(venue)), 0);
        assertEq(wrapper.balanceOf(address(converter)), 0);
    }
    function testDivergentWrapperPriceCannotWeakenFinalNativeFloor() public {
        _price(address(0), 2000e8, block.timestamp); _price(address(wrapper), 2040e8, block.timestamp);
        venue.setOutput(0.98 ether, false);
        assertLt(oracle.quote(address(token), address(wrapper), SOURCE) * 99 / 100, 0.98 ether);
        assertEq(oracle.quote(address(token), address(0), SOURCE), 1 ether);
        vm.expectRevert(ZZZModule.Slippage.selector); _convert(1); _unchanged();
    }
    function testMissingNativePriceFailsClosedBeforeSpending() public {
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(0)));
        _convert(1); _unchanged();
    }
    function testAlignedPricesAcceptExactNinetyNinePercentAndPreserveCredits() public {
        _price(address(0), 2000e8, block.timestamp);
        assertEq(_convert(1), 0.99 ether);
        assertEq(ledger.earned(), 0); assertEq(ledger.sourceLiability(), 0);
        assertEq(ledger.nativeCredit(), 0.99 ether); assertEq(ledger.nativeLiability(), 0.99 ether);
        assertEq(address(ledger).balance, 0.99 ether); assertEq(token.balanceOf(address(venue)), SOURCE);
        assertEq(token.allowance(address(ledger), address(converter)), 0);
        assertEq(token.allowance(address(converter), address(venue)), 0);
    }
    function testExistingStrongerWrapperFloorRemainsRequired() public {
        _price(address(0), 2000e8, block.timestamp); _price(address(wrapper), 1960e8, block.timestamp);
        venue.setOutput(1 ether, false);
        vm.expectRevert(ZZZModule.Slippage.selector); _convert(1); _unchanged();
    }
    function testStrongerCallerMinimumAndLyingReturnRollback() public {
        _price(address(0), 2000e8, block.timestamp);
        vm.expectRevert(ZZZModule.Slippage.selector); _convert(0.99 ether + 1); _unchanged();
        venue.setOutput(0.99 ether, true);
        vm.expectRevert(ZZZModule.InvalidState.selector); _convert(1); _unchanged();
    }
    function testStaleNativeFeedStopsConversionWithoutChangingRights() public {
        _price(address(0), 2000e8, block.timestamp); vm.warp(block.timestamp + 3601);
        _price(address(token), 1e8, block.timestamp); _price(address(wrapper), 2000e8, block.timestamp);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(0)));
        _convert(1); _unchanged();
    }
    function testNonEighteenDecimalWrapperCannotBeAdmitted() public {
        wrapper.setDecimals(6);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); converter.configureWrapper(_wrapperPolicy(address(wrapper)));
        _unchanged();
    }
    function testFaultyUnwrapRollsBackSwapAndEarnedBalances() public {
        _price(address(0), 2000e8, block.timestamp); wrapper.setPayoutBps(9999);
        vm.expectRevert(ZZZModule.InvalidState.selector); _convert(1); _unchanged();
    }
    function testDirectWrapperUnwrapNeedsNoOracleAndKeepsOneToOne() public {
        NativeFloorLedger direct = new NativeFloorLedger(address(wrapper));
        ZZZLPRewardConverter directConverter = new ZZZLPRewardConverter(address(access), address(direct), address(wrapper));
        direct.bind(directConverter); directConverter.configureWrapper(_wrapperPolicy(address(wrapper)));
        directConverter.setEnabled(true); wrapper.mint(address(direct), 1 ether); direct.credit(1 ether);
        vm.warp(block.timestamp + 7200);
        assertEq(direct.convert(bytes32(0), 1 ether, block.timestamp + 60), 1 ether);
        assertEq(direct.nativeCredit(), 1 ether); assertEq(direct.sourceLiability(), 0);
        assertEq(wrapper.allowance(address(direct), address(directConverter)), 0);
    }
    function testDirectUnwrapRejectsChangedWrapperDecimals() public {
        NativeFloorLedger direct = new NativeFloorLedger(address(wrapper));
        ZZZLPRewardConverter directConverter = new ZZZLPRewardConverter(address(access), address(direct), address(wrapper));
        direct.bind(directConverter); directConverter.configureWrapper(_wrapperPolicy(address(wrapper)));
        directConverter.setEnabled(true); wrapper.mint(address(direct), 1 ether); direct.credit(1 ether);
        wrapper.setDecimals(6);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        direct.convert(bytes32(0), 1 ether, block.timestamp + 60);
        assertEq(direct.earned(), 1 ether); assertEq(direct.sourceLiability(), 1 ether);
        assertEq(direct.nativeCredit(), 0); assertEq(wrapper.balanceOf(address(direct)), 1 ether);
        assertEq(wrapper.allowance(address(direct), address(directConverter)), 0);
    }
    function testProxyImplementationDriftRequiresNewAuthenticatedReview() public {
        NativeFloorProxyAdmin admin = new NativeFloorProxyAdmin();
        NativeFloorWrapper implementation = new NativeFloorWrapper();
        NativeFloorProxy proxy = new NativeFloorProxy(address(admin), address(implementation));
        NativeFloorWrapper wrapped = NativeFloorWrapper(payable(address(proxy))); wrapped.initializeProxyFixture();
        NativeFloorLedger direct = new NativeFloorLedger(address(wrapped));
        ZZZLPRewardConverter directConverter = new ZZZLPRewardConverter(address(access), address(direct), address(wrapped));
        direct.bind(directConverter);
        ZZZRewardConverter.WrapperPolicy memory policy = ZZZRewardConverter.WrapperPolicy(address(proxy).codehash,
            address(admin), address(implementation), address(this), address(admin).codehash,
            address(implementation).codehash, keccak256("controlled proxy fixture"));
        directConverter.configureWrapper(policy); directConverter.setEnabled(true);
        wrapped.mint(address(direct), 1 ether); direct.credit(1 ether); vm.deal(address(proxy), 2 ether);
        NativeFloorWrapperReplacement replacement = new NativeFloorWrapperReplacement();
        admin.upgrade(address(proxy), address(replacement));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        direct.convert(bytes32(0), 1 ether, block.timestamp + 60);
        assertEq(direct.earned(), 1 ether); assertEq(direct.nativeCredit(), 0);
        policy.implementation = address(replacement); policy.implementationCodeHash = address(replacement).codehash;
        policy.reviewHash = keccak256("replacement controlled fixture review");
        directConverter.configureWrapper(policy);
        assertEq(direct.convert(bytes32(0), 1 ether, block.timestamp + 60), 1 ether);
    }
}
