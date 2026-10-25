# Manual triage of the rights-domain static findings

This reviews all **165** assigned findings from the parent's fresh Slither0.11.6
capture:35High,27Medium and103Low analyzer labels. Labels are not confirmed bug
severities. Every input fingerprint/check/impact has an individual disposition
and concrete function/call rationale in [the decision list](static-rights-review.json).
The decisions reflect manual reading of the complete descriptions and actual
callers/guards, not an automatic baseline whitelist or a clean-analysis claim.

Disposition totals:71false_positive,91accepted_risk,3informational,0unresolved
in this assigned slice. The91accepted items are90bounded external-call loop
sites plus the explicitly trusted royalty custody recipient. These do not mean
dependencies or target-chain gas have been qualified. Actual source/market/
provider/operating and independent-audit release requirements remain open.

## Exact native sends

Rewards and RoyaltyRewards claims pay only the current `ownerOf(id)`; their
public paths fix owner to caller or immutable authenticated ClaimRouter. CEI,
per-ledger nonReentrant and canonical post-checks prevent a repeated withdrawal
or a successful lifecycle switch mid-claim. The router repeats ownership before
each selected payout, so callback transfer cannot let the old owner claim the
next operation. Converter ETH goes only to its immutable ledger. FeeController
private sends are reached by authenticated reserve/canonical callers; public
users cannot choose a recipient.

Royalty custody is deliberately different: paused selected governance may move
the exact full admitted balance to the approved recipient/codehash/nonce/review.
It suspends that currency until full backing returns. This is an accepted
privileged-withdrawal/custodian risk, not a false assertion that no one can ever
move capital. The static warning is retained as `accepted_risk`.

## Reentrancy and balance snapshots

The27balance warnings concern deliberately retained **pre-operation baselines**:
Migration exit/funding, Converter swap/unwrap/payout, Rewards/Royalty conversion,
Buyback acquisition/burn, and CanonicalHandoff fund/abort return. The later
equalities are conservation checks against original prefunds, not cached current
spend authorization. Updating those baselines after callbacks would remove their
protection against old funds subsidizing missing input/output or returned backing.

Migration principal/plan mutation is nonReentrant, exact-status and snapshot
gated. `_receive` subtracts only declared `msg.value` from the relevant native
baseline, uses exact pulls and resets allowances, then requires original
prefunds restored. A privileged parking-nonce invalidation is not an alternate
plan/principal mutation and cannot fund, close or recover the active plan.

Converters are immutable-ledger-only under nonReentrant; the nativeSender flag
permits only the expected wrapper or fixed v4 helper during its native return.
The flag never grants another financial entry. Exact source/native/wrapped
amounts, route/wrapper pins and stronger submitted minima apply. Ledger batch
conversion debits/checkpoints first, then credits exactly the actual received
output to the same selected NFT components. Public claimable/pending views reject
intermediate reentrant state; public mapping getters are not payout authority.

FeesCanonical restore has no independent nonReentrant modifier, but only the
fixed Handoff can invoke it. Handoff's complete return sequence is locked and
checks an actual incoming delta before restoration. Its native destination is
the fixed FeeController with an empty receive; token callbacks cannot impersonate
Handoff. Clearing the source delivery flag after this transfer does not create
another authenticated restore/release route.

Handoff transitions themselves use phase, peer, root and cursor guards plus
nonReentrant. The unguarded `bindFrozen` requires the exact source peer, importer
phase and unset handoffId; it cannot be used as a second source freeze/import/
activation/abort mutation. All asset-domain hooks accept only fixed Handoff.
Operating/economic post-checks make a nested canonical transition roll back the
outer financial operation. New role/event emissions do not bypass those guards.

Membership deliberately checkpoints the zero-weight entrant before marking it
eligible; its only mutable caller is fixed Vault, and the fixed Rewards
checkpoint only reads eligibility/shares and writes its own indexes. No token
callback occurs there. NFT.mint rejects a synchronous randomness response because
the requested result is not registered until after coordinator request returns;
nonReentrant/fixed-Vault authorization prevents a second mint.

## Medium arithmetic, local initialization and ignored values

The three divide-before-multiply findings are intentional20-raw-unit grouping:
16individual,2collective,1compound,1buyback, with `%20` dust retained. Documented
incumbent dust settlement is separate; integer truncation does not silently drop
funds or promise exact percentages at every tiny receipt.

The two strict equalities test either zero new royalty receipt (while still
enrolling waiting NFTs) or the captured `Active` versus `Parked` enum. Neither
uses a forced external balance as a required magic sentinel.

All10uninitialized-local flags are ordinary Solidity zero defaults: conversion
accumulators, binary-search low, supported-module known flag and metadata color
counter. The converter's memory route policy is populated and validated on the
only branch where its fields are used; direct wrapper withdrawal never reads
those route fields. No uninitialized storage pointer was found.

The ignored returns are intentional validation-only uses: setup price liveness,
exit-price validation before actual amount/NAV valuation, unused lower/fingerprint
when the buyback ceiling explicitly needs upper USD, and preparation reviewHash
already included in Access's exact notice commitment. No validation call is
skipped merely because its numeric result is not stored.

The apparent double write to conversion `assigned` is necessary. The first
updated value is read immediately when allocating collective output, and the
second carries combined allocation to the next NFT. Removing the first would
over-credit output, so it is not dead code.

## The90external-call loop sites

Each decision preserves its exact flagged call and stack. Important bounds and
availability effects were reviewed, not inferred from a generic loop warning:

- Handoff resolves16fixed module IDs/six domains; import/export batches cap8rows.
  Captured asset counts cap256; actual current reward/royalty domains cap33/17.
  Activation/abort completion still depend on the full composed maximum fitting
  and every admitted backing asset being observable.
- Membership residual settlement caps4buckets and33LP assets. Positive unpaid
  incumbent dust intentionally blocks entry rather than being lost/redistributed;
  broken live venue reads were removed from that identity-only path earlier.
- Fee canonical settlement can do4x33dust flushes; currency capture/validation
  can fail on an admitted token. That failure cannot be waived to invent backing.
- ClaimRouter caps32selected operations with ownership rechecks and atomic
  rollback. Users can chunk/select healthy currencies, but a selected failing
  payout or recipient can revert that transaction.
- Conversion batches cap32sorted NFTs. Repeated owner/share/eligibility reads
  are fixed static dependencies; maximum gas is still a real qualification.
- Royalty activation caps17currencies with a250,000gas optional-token isolation
  boundary; `syncAll` and canonical backing checks intentionally fail as whole
  convenience/export operations if an admitted currency is unreadable.

These sites are `accepted_risk`, with concrete current bounds and outstanding
token/gas qualifications. They are not individually unresolved security bugs,
nor evidence that all maximum-state operating scenarios already passed.

No new confirmed exploit or production code correction emerged from this
assigned static triage. No EVM tests, public RPC, financial transaction, service
action, dependency upgrade or source mutation was performed by this slice.
The parent's independent cross-check and complete399-finding merge are required
before updating the checked-in static-review gate. Production remains NOT APPROVED.
