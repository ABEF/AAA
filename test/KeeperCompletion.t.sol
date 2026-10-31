// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {Ids, Position} from "../src/libraries/ZZZTypes.sol";
import {MockAccess} from "./mocks/Mocks.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {BudgetAdversarialVenue} from "./MigrationBudgetAdversarial.t.sol";

/// @dev TEST ONLY. Unauthenticated MockAccess setters model an already authorized
/// governance/guardian callback. This is dependency/privileged-callback hardening,
/// not an ordinary external actor's authority or a market-profit simulation.
contract KeeperCompletionCallback {
    MockAccess public immutable control;
    address public immutable keeper;
    uint8 public action; // 0: unchanged; 1: pause; 2: revoke original keeper.
    uint256 public calls;

    constructor(MockAccess access_, address keeper_) { control = access_; keeper = keeper_; }
    function configure(uint8 value) external { require(value <= 2); action = value; }
    function run() external {
        ++calls;
        if (action == 1) control.setPaused(true);
        else if (action == 2) control.setKeeper(keeper, false);
    }
}

/// @notice Real Vault/accounting/rewards with the existing synthetic venue and
/// authority fixture. Only the close callback changes pause/keeper state.
contract KeeperRebalanceCompletionTest is PooledVaultFixture {
    BudgetAdversarialVenue private adversary;
    KeeperCompletionCallback private callback;
    bytes4 private constant UNAUTHORIZED = bytes4(keccak256("Unauthorized()"));

    function _prepare(uint8 action) private returns (uint256 id) {
        adversary = new BudgetAdversarialVenue(address(t0), address(t1));
        ac.bind(Ids.LIQUIDITY, address(adversary));
        id = activatedPosition();
        callback = new KeeperCompletionCallback(ac, address(this));
        callback.configure(action);
        adversary.reenter(address(callback), abi.encodeCall(KeeperCompletionCallback.run, ()));
        adversary.setFees(100, 100);
        vm.warp(block.timestamp + 600);
    }

    function _rejectAndAssertRollback(uint8 action) private {
        uint256 id = _prepare(action);
        Position memory beforePosition = vault.group(_bucket());
        uint256 shares = vault.sharesOf(id);
        uint256 supply0 = t0.totalSupply();
        uint256 supply1 = t1.totalSupply();
        vm.expectRevert(UNAUTHORIZED);
        vault.rebalance(_bucket(), 1, block.timestamp + 100);
        assertEq(keccak256(abi.encode(vault.group(_bucket()))), keccak256(abi.encode(beforePosition)));
        assertEq(adversary.ownerOf(beforePosition.lpTokenId), address(vault));
        assertEq(adversary.amount0(beforePosition.lpTokenId), 1000);
        assertEq(adversary.amount1(beforePosition.lpTokenId), 1000);
        assertEq(t0.balanceOf(address(adversary)), 1000);
        assertEq(t1.balanceOf(address(adversary)), 1000);
        assertEq(t0.totalSupply(), supply0);
        assertEq(t1.totalSupply(), supply1);
        assertEq(t0.balanceOf(address(vault)), 0);
        assertEq(t1.balanceOf(address(vault)), 0);
        assertEq(t0.allowance(address(vault), address(adversary)), 0);
        assertEq(t1.allowance(address(vault), address(adversary)), 0);
        assertEq(vault.totalIdle(address(t0)), 0);
        assertEq(vault.totalIdle(address(t1)), 0);
        assertEq(vault.sharesOf(id), shares);
        assertEq(vault.migrationBudget().lastCompound(_bucket()), 0);
        assertEq(adversary.fee0(), 100);
        assertEq(adversary.fee1(), 100);
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(rewards.claimable(id, address(t1)), 0);
        assertEq(fees.compoundBalance(_bucket(), address(t0)), 0);
        assertEq(fees.compoundBalance(_bucket(), address(t1)), 0);
        assertEq(fees.buybackBalance(address(t0)), 0);
        assertEq(fees.buybackBalance(address(t1)), 0);
        assertFalse(adversary.reentryAttempted());
        assertEq(callback.calls(), 0);
        // The callback's pause/revocation also rolls back with the transaction.
        assertTrue(ac.keeperAuthorized(address(this)));
        assertFalse(ac.paused());
        // Failed completion also rolls back the budget snapshot and permits a
        // fresh retry after removing the deliberately adversarial callback.
        adversary.reenter(address(0), bytes(""));
        vault.rebalance(_bucket(), 1, block.timestamp + 100);
        assertTrue(vault.group(_bucket()).lpTokenId != beforePosition.lpTokenId);
        assertEq(rewards.claimable(id, address(t0)), 90);
    }

    function testRebalanceRejectsPauseDuringCloseAndRollsBack() public { _rejectAndAssertRollback(1); }
    function testRebalanceRejectsKeeperRevocationDuringCloseAndRollsBack() public { _rejectAndAssertRollback(2); }
    function testRebalanceUnchangedAuthorityCallbackStillSucceeds() public {
        uint256 id = _prepare(0);
        uint256 oldLP = vault.group(_bucket()).lpTokenId;
        vault.rebalance(_bucket(), 1, block.timestamp + 100);
        Position memory p = vault.group(_bucket());
        assertTrue(p.lpTokenId != oldLP);
        assertEq(p.lastRebalance, block.timestamp);
        assertEq(adversary.amount0(p.lpTokenId), 1005);
        assertEq(adversary.amount1(p.lpTokenId), 1005);
        assertEq(callback.calls(), 1);
        assertTrue(adversary.reentrySucceeded());
        assertEq(rewards.claimable(id, address(t0)), 90);
        assertEq(fees.buybackBalance(address(t0)), 5);
    }
}

/// @dev TEST ONLY: isolate the coordinator's original caller from the Vault
/// module caller. The stub admits only the bound Compounder and records work.
contract KeeperCompletionVaultStub {
    KeeperCompletionCallback public immutable callback;
    address public compounder;
    uint256 public calls;
    uint256 public lastId;
    uint128 public lastMinimum;
    uint256 public lastDeadline;
    constructor(KeeperCompletionCallback callback_) { callback = callback_; }
    function bind(address candidate) external { require(compounder == address(0)); compounder = candidate; }
    function compound(uint256 id, uint128 minimum, uint256 deadline) external {
        require(msg.sender == compounder);
        ++calls; lastId = id; lastMinimum = minimum; lastDeadline = deadline;
        callback.run();
    }
}

contract KeeperCompoundCompletionTest is Test {
    MockAccess private control;
    KeeperCompletionCallback private callback;
    KeeperCompletionVaultStub private vault;
    ZZZCompounder private compounder;
    bytes4 private constant UNAUTHORIZED = bytes4(keccak256("Unauthorized()"));

    function setUp() public {
        vm.warp(1_000_000);
        control = new MockAccess(); ProtocolPolicyFixture.bind(address(control));
        callback = new KeeperCompletionCallback(control, address(this));
        vault = new KeeperCompletionVaultStub(callback);
        compounder = new ZZZCompounder(address(control));
        vault.bind(address(compounder));
        control.bind(Ids.VAULT, address(vault));
        control.bind(Ids.COMPOUNDER, address(compounder));
        control.setKeeper(address(this), true);
        control.seal();
    }

    function _rejectAndAssertRollback(uint8 action) private {
        callback.configure(action);
        vm.expectRevert(UNAUTHORIZED);
        compounder.compound(7, 19, block.timestamp + 100);
        assertEq(vault.calls(), 0);
        assertEq(vault.lastId(), 0);
        assertEq(vault.lastMinimum(), 0);
        assertEq(vault.lastDeadline(), 0);
        assertEq(callback.calls(), 0);
        assertTrue(control.keeperAuthorized(address(this)));
        assertFalse(control.paused());
        callback.configure(0);
        compounder.compound(7, 19, block.timestamp + 100);
        assertEq(vault.calls(), 1);
    }

    function testCompoundRejectsPauseDuringVaultCallAndRollsBack() public { _rejectAndAssertRollback(1); }
    function testCompoundRejectsOriginalKeeperRevocationAndRollsBack() public { _rejectAndAssertRollback(2); }
    function testCompoundChecksOriginalKeeperAndAllowsUnchangedAuthority() public {
        assertFalse(control.keeperAuthorized(address(compounder)));
        compounder.compound(7, 19, block.timestamp + 100);
        assertEq(vault.calls(), 1);
        assertEq(vault.lastId(), 7);
        assertEq(vault.lastMinimum(), 19);
        assertEq(vault.lastDeadline(), block.timestamp + 100);
        assertEq(callback.calls(), 1);
    }
}

/// @dev TEST ONLY exact burn with a callback after the balance/supply change.
contract KeeperCompletionBurnToken is ERC20 {
    KeeperCompletionCallback public immutable callback;
    constructor(KeeperCompletionCallback callback_) ERC20("Keeper completion fixture", "KCF") { callback = callback_; }
    function mint(address account, uint256 amount) external { _mint(account, amount); }
    function burn(uint256 amount) external { _burn(msg.sender, amount); callback.run(); }
}

/// @dev TEST ONLY funded direct-ZZZ reserve; no market quote or fee allocation
/// behavior is asserted by the coordinator completion cases.
contract KeeperCompletionReserve {
    KeeperCompletionBurnToken public immutable token;
    address public buyback;
    uint256 public reserve;
    uint256 public releases;
    constructor(KeeperCompletionBurnToken token_) { token = token_; }
    function bind(address candidate) external { require(buyback == address(0)); buyback = candidate; }
    function fund(uint256 amount) external { token.mint(address(this), amount); reserve += amount; }
    function releaseBuyback(address asset, uint256 amount) external {
        require(msg.sender == buyback && asset == address(token) && amount <= reserve);
        reserve -= amount; ++releases;
        require(token.transfer(msg.sender, amount));
    }
}

contract KeeperCompletionOracle {
    function priceBounds(address) external pure returns (uint256, uint256, bytes32) {
        return (1 ether, 1 ether, keccak256("TEST_ONLY_EQUAL_BOUNDS"));
    }
    function tokenDecimals(address) external pure returns (uint8) { return 18; }
}

contract KeeperBuybackCompletionTest is Test {
    MockAccess private control;
    KeeperCompletionCallback private callback;
    KeeperCompletionBurnToken private token;
    KeeperCompletionReserve private reserve;
    ZZZBuyback private buyback;
    bytes4 private constant UNAUTHORIZED = bytes4(keccak256("Unauthorized()"));

    function setUp() public {
        vm.warp(1_000_000);
        control = new MockAccess(); ProtocolPolicyFixture.bind(address(control));
        callback = new KeeperCompletionCallback(control, address(this));
        token = new KeeperCompletionBurnToken(callback);
        reserve = new KeeperCompletionReserve(token);
        buyback = new ZZZBuyback(address(control), address(token), 100 ether);
        reserve.bind(address(buyback));
        control.bind(Ids.BUYBACK, address(buyback));
        control.bind(Ids.FEES, address(reserve));
        control.bind(Ids.ORACLE, address(new KeeperCompletionOracle()));
        control.setKeeper(address(this), true);
        control.seal();
        reserve.fund(100 ether);
        token.mint(address(buyback), 7 ether); // Unclassified prefund stays untouched.
    }

    function _execute() private { buyback.execute(address(token), 10 ether, bytes32(0), block.timestamp + 100); }
    function _rejectAndAssertRollback(uint8 action) private {
        callback.configure(action);
        uint256 supply = token.totalSupply();
        vm.expectRevert(UNAUTHORIZED);
        _execute();
        assertEq(reserve.reserve(), 100 ether);
        assertEq(reserve.releases(), 0);
        assertEq(token.balanceOf(address(reserve)), 100 ether);
        assertEq(token.balanceOf(address(buyback)), 7 ether);
        assertEq(token.totalSupply(), supply);
        assertEq(buyback.operatingTradeUSD(), 100 ether);
        assertEq(callback.calls(), 0);
        assertTrue(control.keeperAuthorized(address(this)));
        assertFalse(control.paused());
        callback.configure(0);
        _execute();
        assertEq(reserve.reserve(), 90 ether);
        assertEq(token.totalSupply(), supply - 10 ether);
    }

    function testBuybackRejectsPauseDuringBurnAndRollsBack() public { _rejectAndAssertRollback(1); }
    function testBuybackRejectsKeeperRevocationDuringBurnAndRollsBack() public { _rejectAndAssertRollback(2); }
    function testBuybackUnchangedAuthorityCallbackStillBurnsOnlyReserve() public {
        uint256 supply = token.totalSupply();
        _execute();
        assertEq(reserve.reserve(), 90 ether);
        assertEq(reserve.releases(), 1);
        assertEq(token.balanceOf(address(reserve)), 90 ether);
        assertEq(token.balanceOf(address(buyback)), 7 ether);
        assertEq(token.totalSupply(), supply - 10 ether);
        assertEq(callback.calls(), 1);
    }
}
