# Residual-management verification

Local source checks,31October2026. Production **NOT APPROVED**. No public RPC,
real funds, existing Anvil state, service/site, signer, journal or heartbeat change.

## Executed checks and exact scope

| Group | Result and limits |
| --- | --- |
| Actual local v4 composition |33distinct successful methods across two stages. Stage2 has29passes/one fixture expectation failure; stage3 has the corrected exact-target growth guard plus3new callback cases, all4pass. Not one fresh33-method run. Old14core methods are included once, not added. [Final test ledger](actual-core-verification.json), [stage2](core-stage2.json), [stage3](core-stage3.json). |
| Terminal-lock extraction |3methods pass: normal work, rejection before body when already terminal, and callback terminal detection with all writes rolled back. Minimal fixture; no actual Access authority qualification. [Receipt](terminal-guard-verification.json). |
| Normal compiler |81closed inputs/42normal gates pass, no source/build/compiler drift. Original0.8.26/Cancun/viaIR/optimizer1/Yul-disabled profile and normal EIP170/3860 limits. [Exact gates](normal-size-gates.json). |
| ABI and storage |Existing semantic ABI and storage preserved across141compiler contract/interface entries; only explicitly added selectors/event. This is compiler comparison, not execution or141deployable contracts. [Comparison](interface-storage-comparison.json). |
| Callable documentation |36concrete contracts/777functions/36constructors/14receivers, zero purpose/input/output gaps; strict final source-bound check passes. [Receipt](callable-reference-verification.json). |

Actual-core coverage includes fee-before-principal separation, exact raw receipts,
main/custody/share/clock preservation, mixed residual with failed USD sources and
disabled pool operations, authority/lifecycle/replay/minimum guards, failed-burn
rollback, transfers/claims/future royalties, mode disable/re-enable, ordinary
re-creation and forced single-position consolidation with retained financial
checks. A genuine late governance callback changes policy, invalidates nonce or
unpauses; each is reached and the complete transaction rolls back.

The corrected growth test sets quote/approval before expectRevert, expects the
exact Slippage selector and witnesses Budget.assertDeployed. Its cached trace
shows deployed766.8177 versus idle434.584 before the actual guard reverts. The
trace rerun overlaps an existing method and is not additional coverage.

Real local PoolManager/PositionManager/StateView execute with explicitly mocked
Access, correlated USD feeds, VRF, Permit2 and Registry admission. PositionManager
has explicit test-only burn/failure/callback seams; injected callbacks test guards,
not a demonstrated attack against the actual ZZZ or Uniswap deployment.

## Retained failures and size comparison

The first30-method test build hit a test-fixture Yul stack-depth error and
executed no tests. Named snapshot helpers fixed the fixture without relaxing
compiler settings. Stage2's one expected-revert assertion was incorrectly placed
before setup view calls; the exact failed case was corrected and rerun with the
three new callback methods. [Stage1](core-stage1.json) and other receipts retain
original failures; no failed attempt is overwritten or counted as a pass.

The first residual implementation measured Vault24903/Budget24586runtime bytes
and failed normal limits. Behavior-preserving terminal-check dedup and read-only
holder-exit validation extraction restore normal limits:

| Component | Runtime bytes | Runtime margin |
| --- | ---: | ---: |
| Vault |23671|905|
| Budget |24290|286|
| Manager |21591|2985|
| Position child |20169|4407|

Static constructor argument bounds are included in the normal initcode gates;
exact target deployment arguments/gas, maximum-holder economics and operating
qualification remain open. All previous optional-portfolio report bytes and four
unrelated dirty tracked files remain unchanged. [Source pins](source-pins.json).

## Source and release boundary

Code remains uncommitted local source, not deployed/pushed or a completed full
regression/CI/independent audit. Existing private-key signing restrictions,
popldemo/poplint and old Anvil profiles are unchanged. Real token/upstream
behavior, feeds/routes/VRF/authority/OpenSea, gas/market/host recovery and
independent review remain in the [sole Todo](../../TODO.md).

The management guide and current Todo/features/context are synchronized with the
actual control surface. Per-operation financial bypass remains explicit in
paused emergency rebalancing; raw residual close never adds an arbitrary payout,
swap, principal redemption or custody-recipient path.
