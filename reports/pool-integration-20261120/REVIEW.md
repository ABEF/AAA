# Supplied-pool production swaps and Entry/NFT integration

20 November 2026. Baseline `bb5ef4de5afc9dd8cebf4ee96d5b044477a52bf5`.
Trusted production build: `activation-final-six-20261118`, Factory6/allocation2.
**The new finite integration partitions pass. Production remains NOT APPROVED.**

## Improvement and scope

The [previous physical-LP proof](../pool-lifecycle-20261120/REVIEW.md) used a test
trader to generate fees and a typed custody fixture instead of the full NFT graph.
This work adds the missing production direct-swap path and actual Entry-to-Vault
contributions against the supplied real native Uniswap core/periphery/token.
It does not relabel that earlier evidence or rerun its unchanged suite.

The supplied hookless ETH/ZZZ test pool remains
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`, at pinned
Robinhood block119107223. Final production-pool selection remains deferred.
The original zero-active-liquidity observation is preserved. Test funding and
locally added depth are explicit fixtures, not sustainable external market depth.

## Direct production swap path

[Swap report](swap/REVIEW.md), [saved-wire verification](swap/VERIFICATION.json)
and [network accounting](swap/NETWORK_COUNTS.json).

Both `Manager.swap` directions pass through the real Balancer quote, Oracle
execution checks, core unlock/swap/settlement and exact recipient-delta checks.
An impossible caller output floor returns `Slippage()` in simulation with
unchanged balances, allowances and pool state. That negative is **not a mined
failed transaction**. Final Manager/LP-child balances and checked spending
allowances are zero; the temporary synthetic depth is closed.

There are two newly covered swap behaviors, six positive setup/action/cleanup
receipts, and a simulation-only refusal. The existing24M/full25% envelope is
retained. A typed caller bound through `MockAccess` exercises the allowed BUYBACK
caller path; this is not production Access or buyback-reserve qualification.
The direct function quotes its specified pool: it does not search a venue list.

## Actual Entry activation and growth

[Entry report](entry/REVIEW.md) and [saved-evidence verification](entry/VERIFICATION.json).
The fresh normal39-instance graph uses the real supplied core, POSM, StateView,
Permit2 and ZZZ, with112 binding checks. Construction is necessary setup for
this integration, not a new claim that the earlier constructor suite was rerun.
Only this newly owned disposable graph is configured and locally sealed so the
real Entry authorization can execute. No existing or production Access is sealed.

| Newly covered contribution | Estimate | Full20% transaction allowance | Actual gas |
| --- | ---: | ---: | ---: |
| ETH activation |10,587,724|12,705,269|10,255,624|
| ZZZ activation |10,975,926|13,171,112|10,335,526|
| ETH growth |9,418,190|11,301,828|9,007,090|
| ZZZ growth |9,883,458|11,860,150|9,288,458|

All four use the selected32M/full20% contribution profile and current3% loss
budget. Controlled inputs are110USD activation and20USD growth in each asset.
These two-NFT/no-ERC20-royalty cases are not the historical near1,000-NFT or
64-currency maximum-state workload. The remaining476,135-estimate shortfall in
the unsynchronized maximum-state case stays open.

Both NFTs belong to the same disposable local account. The journey verifies real
PoPL NFT ownership, activation/membership, main-position
custody and increasing L; exact share totals agree with the allocation tree.
Growth and the second activation preserve main ID4331098, ticks121400/132600,
the captured centre and rebalance clock. Other NFT share balances do not change
when one NFT grows. No residual is created. New activations receive no older LP
claim, and Entry balances and the checked contribution/LP spending allowances
return to zero.

Saved execution traces connect entrant-only balancing inputs to actual placement,
post-swap incumbent NAV and the whole-unit share result. The separate arithmetic
replay checks the issuance formula and captured financial floors. Its NAV inputs
come from the real trace; it is **not an independent physical valuation oracle**.
The configured one-venue catalog is exercised through `Manager.balance`; this
does not prove selection among multiple markets or qualify the best live pool.

## Confirmed corrections and evidence boundaries

- The restored swap clone initially kept an earlier pending-block clock, making
  correctly protected feed reads fail. The report driver now establishes a
  monotonic next block on that owned clone before sending setup transactions.
  Original failed artifacts remain. This is not a production clock workaround.
- The current findings and feature guidance are reconciled with the completed
  physical partition instead of still presenting its earlier interrupted attempt
  as current. Historical source-scoped reports remain unchanged.
- Cache hits, local relay rejections and actual upstream requests are reported
  separately; local admission refusals are not public-provider failures.

No confirmed production Solidity defect required changing the frozen F6 build.
All financial guards, exact entitlements, economic splits, caller permissions,
default gas budgets and selected profiles remain. The100 source files/four build
controls and48 earlier size gates retain their existing source scope; no unchanged
contract/browser/population suite or size build is rerun.

## Remaining acceptance and preservation

Correlated USD feed pairs, controlled VRF, exact archived SeaDrop code/guard
materialization, local balance substitution and synthetic depth are deliberate
test seams. This does not qualify independent valuation sources, actual OpenSea
or VRF operation, production liquidity/routes, the separate1% earned-LP conversion
route, complete Robinhood fees/provider capacity, hybrid/maximum workloads,
canonical/terminal recovery, running consumers or independent release approval.
There is no claim of every-market, continuous-concurrency or manipulation immunity.

The [plan](PLAN.md) and [baseline](BASELINE.json) retain scope and original-document
hashes. Each partition retains exact source stages, raw requests, receipts,
traces, state and cleanup in its own manifest-bound archive. All owned nodes are
stopped with no pending submission. Existing Anvil8902, NFTs/LP/balances, journals,
checkpoints, websites/services and the user-paused heartbeat are unchanged.
Source/evidence publication is not production deployment, sealing or adoption.
