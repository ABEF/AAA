# Main/residual accounting and custody review

Source baseline main5d70b4b;6November2026. This review does not approve production,
live currencies/venues, target gas or any service/chain rollout. Production source
has not been edited by this agent. New execution evidence is recorded separately.

## Exact creation and closure contexts

| Path | Principal and fee flow | Residual behavior |
| --- | --- | --- |
| First activation | Entry/Vault capture prices; settle incumbent barriers; incoming assets only; factual marginal deployment precedes shares. | No Budget replacement snapshot, therefore initial main only even when modeON. |
| Activation/top-up with two legs | Both-leg pre-entry harvest; old compound becomes attributed idle/NAV; entrant-only balance/increase; repriced incumbent NAV; actual marginal main deployment. | Main L increases; residual ID/L/ticks and rebalance clock stay. Token mix/value can move with pool price. |
| Standalone compound | Budget phase3 snapshot replacement=false; both-leg harvest; designated compound release; existing idle rebalanced/deployed; final captured whole-operation floors. | Existing main increases; no independent residual creation. Existing residual stays valued. Service adds in-range/below-threshold/no-geometry wait. |
| Ordinary rebalance | Phase0 replacement=true; both-leg harvest/pull compound/include; close both; balance once; mint bounded portfolio; validate retained value/idle/main floor. | May create one residual if current pool modeON and useful. Both old IDs burn atomically. |
| Governance moveFunds | Same replacement snapshot; closes both source legs; source controls retained; target admission, same ordered pair and target controls checked. | Target modeON can create a NEW residual. This is not limited to Vault.rebalance. |
| Governance resume | Parked idle is the initial mark; pending compound is included once; destination same-pair admission and final physical value checked. | Target modeON can create a residual too. Source main/residual were already closed by parking. |
| Raw residual-only close | Validate exact custody/nonce/epoch; harvest both; close residual only; actual receipts to same-bucket idle; main/control fingerprint and raw minima after. | Clears residual association, preserves main/shares/deposit/clock/mode; does NOT release compound. Protocol stays paused. |
| Raw park | Harvest both then close both into attributed idle. No required USD/swap route; no arbitrary receiver. | Both physical positions close. Compound remains reserved until later resume/exit release. Parking is permitted while preparation drains, unlike new-work closeResidual. |
| Emergency replacement | Paused governance exact manifest; optional financial groups; immutable custody/accounting controls retained. | Always one new main in current pool, never silently changes desired hybrid mode. |
| Terminal holder return | Harvest active legs; flush fee dust; pull compound; close both; send exact classified ETH/ZZZ to Migration; cumulative NFT-share allocation. | Both gone; irreversibly no principal reopening. Earned fees/buyback/royalties stay separate. |
| Canonical replacement | Before terminal exit only; all source groups parked and activeSecondaryCount zero; exact classified backing/imported shares. | No live residual exported/imported; wire tuple shape is not runtime compatibility. |

## Conservation and entrant separation

- Physical principal is actual token amounts from each range; raw liquidity units
  are never summed as value. NAV includes both legs and attributed idle; NFT value
  also includes correctly classified pending compound.
- `_join` harvests before new membership, records pre-entry supply, reprices old
  physical principal after entrant swaps, deploys entrant budgets only, checkpoints
  old owner debt and prices new shares from net added NAV. Existing residual/idle/
  compound cannot satisfy the entrant's marginal-deployment requirement.
- `ZZZContributionPricing.finish` preserves lower-LP/upper-input marks, captured
  policy and post-callback spot; original fees/idle remain in incumbent NAV.
- Fees reach `_allocate` only on operation0 collect receipts. The combined actual
  main+residual receipt is allocated once by the FeeController's20-raw-unit rule:
  16owner/2collective/1compound/1buyback, with bounded carried dust and incumbent
  dust barriers. LP fractional accounting is distinct from exact-unit royalties.
- Compound's phase3 and replacement's phase0 are different. Snapshot phase1 adds
  only the exact designated compound idle delta once. Phase2 freezes source
  controls, target physical backing, retained value, idle and (hybrid replacement)
  configured main allocation. No share supply change is part of maintenance.
- Principal closure receipts never go to holder reward/buyback reserves; raw
  residual close deliberately leaves earned FeeController compound untouched.

## No ordinary accounting loss defect confirmed

The reviewed source does not establish an ordinary share-conservation, forgotten
residual, duplicate80/10/5/5 or lost-principal defect under its conventional exact-
transfer fixed-token/pinned-periphery model. This is a bounded internal review,
not proof of safety or all economic regimes. The new tests address a genuine
coverage gap: destination hybrid creation during move/resume and atomic failure.

## Dependency callback threat boundary

After the pre-close harvest, Vault treats actual BURN/TAKE returns as principal.
The typed executor does not separately split fees generated AFTER that harvest.
A malicious/upgraded ZZZ token or compromised PositionManager could introduce a
callback between harvest and burn, or between the two burns, and donate/trade so
the still-live residual acquires late fees. A roundtrip price mutation may leave
the final mark unchanged. Those late fees could then follow principal instead of
80/10/5/5. A conventional immutable ERC20 and reviewed hookless periphery do not
give an ordinary external trader a way to interleave within this transaction.

This is NOT presented as a current outsider exploit or fixed by prose. Actual
ZZZ callback/proxy/admin behavior and periphery provenance must be qualified.
Supporting mutable/reentrant token behavior would require a separately reviewed
close-receipt/accounting design; do not silently sweep, reclassify or relax guards.
The parent requested static retention of this threat, not a fabricated compromised-
dependency test or an unapproved economic redesign.

## Recoverability dependencies

| Condition | Supported next action | Dependency/limit |
| --- | --- | --- |
| Residual unused/mixed/filled | Keep, raw close, ordinary merge or whole emergency. | Same actual ID remains principal; composition alone is not a new entitlement. |
| ModeOFF but residual live | Keep authenticating both until successful merge/close. | A policy setter is not a custody transfer or final applied state. |
| Large idle after raw close | Eligible compound, guarded whole replacement, paused emergency, full parking or terminal return. | New entrants cannot subsidize it; default idle ceiling can intentionally block entry. |
| Failed/stale prices or no affordable swap | Raw residual close/full parking/terminal raw closure remain separate paths. | Core/token/fee ledgers and exact settlement must still work. |
| Preparing canonical migration | Drain with whole parking, then capture closed backing. | closeResidual is new work and preparation-blocked; park uses drain authority. |
| Token freeze/core failure/chain halt | No universal recovery guarantee. | A generic transfer/sweep cannot repair a frozen token or disappear a liability. |
| Recipient rejects terminal payout | Governance isolated retry; current owner fallback recipient. | Retain backing; do not drop failed claims or send principal to the operator. |

Normal principal is intentionally nonredeemable; attributed idle is not a lost or
claimable reward. Emergency can deliberately lose nearly all principal when its
optional guards are disabled. Governance movement/resume are explicit custody
operations, not keeper timing bypasses. The12-hour ordinary rebalance gate is not
an assertion that every governance custody operation uses that same clock.

## Prior evidence and focused verification

Existing OptionalPortfolioCore methods already cover mixed/outside residuals,
direct and Entry contributions, hourly allocation, current owner claims, raw close
and callback rollback, full parking, target single-mode movement, terminal return
and multiple1→2→1 cycles. Historical source scopes remain explicit; do not sum
old reports or claim their full current Royalty4/V8 code was rerun.

New methods are `testResidualAuditEnabledDestinationMoveCreatesTrackedPortfolioAndPreservesEarnedRights`,
`testResidualAuditEnabledResumeThenGrowthThenSingleMergeKeepsAllBacking`, and
`testResidualAuditInfeasibleDestinationRollsBackBothSourceLegsAndReservation`.
They use actual local v4 core/periphery and production PoPL code, with explicitly
mocked Access, Registry admission, correlated feeds, Permit2, VRF and test ZZZ.
The first ABI attempt mistakenly called the private reverse-association mapping;
the corrected test uses authenticated full-portfolio reads instead. Both attempts
are retained; no production visibility or guard was changed to make it pass.
