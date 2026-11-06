# Exact-unit LP rewards: approved upgrade design

6 November 2026. **Design/prototype only; current Rewards is NOT upgraded.**
The user selected exact-unit LP allocation during this audit. This is an accepted
requirement, not a new question to repeat next session. The earlier exact-unit
implementation was royalty4; its completion did not change the LP index ledger.
See [measured findings](REVIEW.md) and the [owning task](../../TODO.md#task-lp-exact-unit-allocation).

## Problem and invariant

Current LP indices can strand a finite last unit: a20raw-unit fee allocates18to
holders and1each to compound/buyback, but a sole holder with101share units can
claim17. The remaining1is backed; its almost-one-unit fractional right is not a
whole payout without later revenue. Solvency is not eventual claimability.

Every ALLOCATED holder unit must instead belong to a whole, recoverable NFT
right, even when no later fees arrive. Preserve actual-receipt80/10/5/5,
individual LP shares, one equal collective share per activated NFT, current-owner
claims, entrant checkpoints, asset separation and all principal/reserve barriers.
Sub20FeeController carry and its existing incumbent flush are a separate policy.
Core fee-growth truncation before PoPL receives money is also separate.

## Recommended bounded mechanism

Use a fixed-depth binary weighted allocation tree:1024leaves, at most1000NFT
mint-ordinal slots. NFT token IDs are not array indices. One individual tree per
logical bucket stores the NFT's actual shares; a collection tree stores one
weight per activated NFT for the collective component. Both components can use
one audited mechanism, with separate storage and currencies. Evaluate reuse of
the existing equal-ticket allocator for the collective component during the
implementation review; never copy rarity weights or raw-share ticket rotation.

Each tree node records subtree weight. Each currency has whole pending units and
a nonmonetary split carry at nodes. A harvest credits only the relevant roots;
no1000NFT materialization loop runs during either entry harvest.

When pushing amount A through a node with left weight L and total weight W:

```text
q = floor(A * L / W)       # full-precision mulDiv
r = (A * L) mod W         # mulmod, not an overflowing product
left = q + overflow_safe_carry(r, previousCarry, W)
right = A - left
nextCarry = (r + previousCarry) mod W
```

Implement the carry addition through `gap=W-previousCarry`: when `r>=gap`,
increment q and use `r-gap`; otherwise use `r+previousCarry`. Do not evaluate
the overflowing sum first. Check pending/weight totals with uint256 arithmetic.
Zero-weight branches receive nothing; a zero-total cohort cannot take a credit.
Every split conserves whole units exactly: left+right=A. Leaf rights therefore
sum to funded root credits, regardless of when materialization occurs.

Claims/views traverse at most10levels. A transfer changes the payout owner,
not the NFT leaf. Before adding shares or activating collective membership,
push ALL existing currency amounts on that path using OLD weights. Then update
the leaf and ancestors. Pending sibling amounts remain their old whole rights;
an entrant cannot acquire them. Reset affected split-fairness carries only after
old pending money is pushed. Carries are not monetary reserves to sweep.

The current pre-update `Rewards.checkpointOwner(id)` call is not a complete
integration: the new ledger must also atomically synchronize the NEW leaf weight
after Vault writes shares/total supply. Design a fixed typed share-change
integration with exact old/new identity and denominator checks; trace callbacks
and reverts across it. A post-write sync may settle pending against internally
stored OLD weights before verifying/updating to the new Vault values; a two-phase
stored preparation is not required without evidence. A ledger that keeps an old tree after growth is incorrect even
if the existing Vault getters report new shares. Do not add an arbitrary executor
or rely on off-chain events to update on-chain weights.

For fixed weights, saved carry makes batching/materialization order irrelevant
to cumulative entitlement under this hierarchical rounding rule. It is NOT a
claim of equivalence to flat largest-remainder allocation. Tree topology and
weight-change carry reset introduce a deterministic rounding policy which must
be stated, tested and included in the release review. Do not describe it as
optimal fairness or silently redistribute prior whole rights.

## Costs and alternatives

| Approach | Decision |
| --- | --- |
| Write every NFT balance at every harvest | Reject as the default: up to1000writes per asset/component and two entry harvests can make contributions uneconomic or unexecutable. |
| Keep fractional indices and sweep at exit | Does not meet ongoing exact-unit assignment; cannot confiscate old backing or invent a recipient. |
| Append allocation epochs and scan them on claim | Unbounded lifetime work unless a separately designed bounded continuation protocol is added. |
| Reuse1/2/3raw royalty tickets for LP shares | Unsafe shortcut: LP shares are large and mutable; raw ticket rotation can produce extreme allocation concentration. |
| Fixed-depth lazy weighted tree | Recommended implementation target: bounded history-independent paths, exact unit conservation; higher claim/growth storage cost must be measured. |

The prototype is an inert design check, not production Solidity, gas evidence or
an independent audit. The implementation must measure actual worst-case paths
for1000NFTs,4buckets, all retained assets, activation/growth, both components,
32-entry claims, conversion and canonical materialization. A32-entry count is
not approval under the existing12Mgas/work limits. No operating limit is raised.

## Required implementation and compatibility work

1. Build a typed bounded allocator; prove exact parent/child/leaf conservation,
   old-weight settlement, carry bounds, full-precision arithmetic, zero branches
   and state rollback before wiring it into the real Rewards ledger.
2. Preserve claim/conversion current-owner semantics, component classification,
   liabilities and exact actual backing. Only accepted exact units replace LP
   fractions; no reserve/principal sweep or new operator payment is introduced.
3. Introduce explicit fresh LP-allocation/accounting identity. A likely boundary
   is accounting7/new canonicalV9 and explicit API/replay/checkpoint selection;
   determine the exact inventory after tracing consumers, not by relabelling6/V8.
   Preserve legacy getters/readers/events/imports as historical where needed.
4. Design canonical capture/import/abort for whole pending rights and future
   fairness carries. Non-destructive views must reconcile every NFT and asset;
   do not drop sibling pending books or resume with changed future rounding.
5. Update authoritative event consumers, earnings checkpoints, claim preparation,
   exact runtime/helper graph pins, function notes and operator examples. Missing
   current identity remains unavailable, not legacy math used on a new runtime.
6. Existing old deployed state is not upgraded here. If legacy fractional rights
   ever need conversion, specify a fully backed apportionment/cutover first;
   never reinterpret old fractions, journals or zero-balance comparisons.
7. Run affected actual-core/accounting/consumer tests, normal size/initcode gates,
   static/source review and exact gas measurements. Independent approval and
   actual operating qualification remain separate.

## Completion criteria

Positive final-unit claims for both LP currencies; correct old/new cohort and
growth order; arbitrary claim order/batching; multiple NFTs per owner/transfers;
all mode/close/compound/exit paths; conversion and canonical round trips; exact
current earnings outputs; bounded maximum-state gas and unchanged custody/splits.
Only then may this implementation task be marked complete. The current audit's
keeper fixes or royalty4 evidence do not close it.
