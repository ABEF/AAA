# PoPL market, lifecycle and recovery execution plan

Baseline: main 44f5fa7; fresh accounting6/portfolio2/custody5. Isolated offline
Foundry execution only. Existing Anvil, services, sites, wallets and journals
remain untouched. Production authority and network admission are not qualified
by the test controller/registry/feeds/Permit2/VRF substitutes.

## First challenge of the requested prompt

- An infinite market cannot be exhaustively simulated. Enumerate reachable
  geometry, lifecycle, accounting and failure classes, identify uncovered gates,
  and distinguish model scenarios from actual operating acceptance.
- Main/residual are two positions in ONE pool. The residual begins within main
  geometry; residual-active/main-inactive is not an ordinary reachable state.
- 60/40 is a replacement-time bound, not a permanent ratio. Entry grows main
  only but buys aggregate NAV. Repricing must not be mistaken for share dilution.
- Permissionless transaction order is serialized. Local ordered EVM actions
  cannot establish browser/RPC capacity, private submission or MEV immunity.
- A feed that follows the simulated pool is useful for arithmetic composition,
  not independent oracle or manipulation qualification.
- Reuse existing source-matched authority, timing, royalty-outage, canonical,
  history and maximum-holder evidence. Do not rerun unchanged broad suites.

## Second challenge and verification design

- Test assertions must not only echo contract getters or observe successful
  calls. Maintain a separate receipt-derived LP entitlement model with raw-unit
  fractions and claims; reconcile actual wallet deltas, aggregate shares and NAV.
- Capture each incumbent's shares/eligibility BEFORE entry-generated receipts.
  Newly activated NFTs cannot earn those older receipts.
- Explicitly test ETH and fixed-ZZZ inputs at flat, trending, reversing, residual
  mixed, pending-disable and wholly outside geometry; preserve exact approval,
  main-only growth, old geometry/clock and actual marginal-deployment floors.
- Follow a rejected operation with snapshot equality and an explicit successful
  recovery under restored controls. Retain failures; never relax a guard merely
  to make a scenario pass.
- Add post-transition transfers, multiple NFTs per wallet, dormant members and
  separate royalty receipts. Principal return must not count as fee income.
- Preserve actual selected core fee/protocol fee and normal build profile.
  Large fixture code-size allowance is test-only; reuse production gates only
  after exact source/dependency/build-input hash comparison.

## Execution

1. Extend the actual local-v4 composed fixture with independent multi-holder
   share/NAV/receipt assertions and new bounded scenario journeys.
2. Compile/run only the new scenario methods. Fix fixture or implementation
   errors according to evidence, retaining all attempts and source pins.
3. Exercise affected backend/keeper failure and recovery paths only where a
   coverage gap or actual changed implementation justifies new execution.
4. Produce a coverage ledger: fresh execution / exact-source reuse / inspection /
   external or unverified. No unchanged historical test is counted as fresh.
5. Update findings, feature evidence, sole Todo, operator guidance and memory.
   Run consistency checks, preserve protected files, publish intended changes on
   main only. Publication is no deployment or operating approval.
