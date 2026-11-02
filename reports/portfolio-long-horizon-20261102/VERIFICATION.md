# Multi-day portfolio evidence

Reviewed2November2026. [Findings and operating conclusions](REVIEW.md),
[case matrix](CASE_MATRIX.md), [exact stage/method ledger](tests.json).

## Fresh execution and retained failures

- First campaign: four new methods; the mixed/residual/both-outside/pricing-outage/
  recovery journey passes. Three other journeys fail with `InvalidAmount`.
- A cached diagnostic trace of one failed ordering identifies the actual rejection
  in `VaultCanonical.validateContribution`:25USD growth is below the fixture's
  100USD pool minimum. Quote callbacks' intentional reverts appear in the Forge
  summary backtrace; the innermost actual failure is the contribution minimum.
  The full trace is retained externally. No production defect is inferred merely
  from the top-level error or misleading quote backtrace.
- Corrected campaign: all three affected methods pass. They explicitly admit the
  fresh example's5USD pool floor and exercise5USD growth. The ordering methods
  also assert that the previous100USD floor rejects25USD atomically, preserving
  balances, shares, main/residual association and empty Entry balances.
- Total: **four distinct successful new methods across these stages**. The
  unchanged first successful method and its transitive fixture/helper bodies are
  reused; their LF hashes are recorded. No fresh final full-suite or one-shot
  four-method result is claimed. Compiler metadata authenticates both exact test
  source stages after Forge LF normalization.

New methods are `testLongHorizonSixDayModesEntryGrowthHarvestCompoundAndClaims`,
`testLongHorizonSameBlockUsersBeforeRebalance`,
`testLongHorizonSameBlockRebalanceBeforeUsers`, and
`testLongHorizonResidualMixedAndBothLegsOutsideStayBackedThenMerge` in
[the actual-core fixture](../../test/OptionalPortfolioCore.t.sol).

The assertions include bounded live IDs/custody, exact per-asset main+residual
aggregation, NAV/idle reconciliation, sum of NFT shares, eligible count, funded
liabilities/reserves, exact80/10/5/5 allocation and split dust, old-ID burns,
main-only incoming funds and compound, preserved clocks/residual L, exact ERC20
approval cleanup, saved observation continuity and partial claims. Both ETH and
fixed-ZZZ Entry execute against actual v4 core/periphery.

## Scope and substitutes

Real local PoolManager/PositionManager/StateView and production PoPL contracts
execute together. Synthetic Access/registry/admission, correlated USD feeds,
VRF, Permit2, test token/funding and deliberate periphery failure seams remain
explicit substitutes. New fixture minimum setter is not proof of the production
Registry governance/configuration procedure. Compounder is bound only through
explicit test bootstrap before user state; production has no unseal/rebind.

Six macro-cycles and18 spaced harvests use virtual time, manual authorized
contract calls and controlled swaps/donations. No live market data, profit/IL
forecast, uninterrupted keeper uptime, service jitter, signed mempool competition,
100-user browser load or1000-holder target-gas qualification is implied. A generous
fixture code-size allowance is separate from normal production gates.

## Unchanged production and verification reuse

All52 production sources and31 build dependencies match the prior
[43 normal gates](../lp-lifecycle-audit-20261102/production-size-gates.json)
at `normal-final-a8e7dc7cc5`. Compiler/settings, production ABI, bytecode, constructor
pins and37-contract/826-function callable reference are unchanged. No recompilation
or rerun of unchanged production suites was needed for this test/doc extension.
Prior475-record internal static disposition retains that exact source scope;
it is not a fresh static campaign or independent audit.

[Preservation](source-preservation.json) binds52 raw source hashes, four unrelated
dirty files and2580 original report artifacts. Existing deployments, Anvil8902,
NFTs/LP/balances, services/sites, journals, signing and paused heartbeat remain
unchanged. Raw attempts/compiler artifacts/trace and original guides are retained
externally at
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/portfolio-long-horizon-20261102`.

[Final checks](FINAL_CHECKS.json) cover generated Todo/reference, current links,
exact-source static-review reuse, preservation and staged Python publication.
Committed revision and remote main are verified separately in external publication
evidence. Source publication is not deployment or production approval.
