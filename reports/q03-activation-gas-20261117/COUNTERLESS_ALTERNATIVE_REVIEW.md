# Analysis only: authenticated currency liability instead of a per-book counter

This is a conditional design/proof review. It does not implement, adopt, compile,
test or qualify the alternative, and changes no current payload identity.

## Mathematical condition

Let L be one currency's existing checked `liabilities[asset]`, and let e(b,i) be
the nonnegative exact entitlement of ticketi in unit bookb. Let a(n) be imported
accrued rights, which remain separate from the allocation trees. The important
economic invariant in an active or fully settled state is:

`L = sum(e(b,i), all unit1/unit2/unit3 tickets) + sum(a(n), all NFTs) <= 2^256-1`.

This implies every individual leaf and each NFT's combined payout is at mostL.
Consequently a modular ancestor-tag sum recovers each true integer entitlement
uniquely. A separate per-book counter is sufficient but not mathematically
necessary: the already-authenticated global liability can supply the bound.

For a positive creditA, check/reserve `L+A` before modifying tags. The ordinary
and complementary interval decompositions add exactlyA nonnegative leaf units.
Their internal coefficients/carries may wrap, but actual global liability must
not. For a take, check its final modular result against the captured currentL;
the parent's final checked debit of imported accrued plus all selected ticket
takes enforces the aggregate bound before any asset transfer. Multiple takes
must not each debit or resetL independently while the parent also debits their
sum. Returning an imported accrued amount must not debit a nonexistent tree
counter.

The proof fails if callers can supply an unauthenticated/arbitrary bound, a new
positive-credit path forgets the actual liability reservation, an external call
can change this currency's books between bound capture and final debit, a
representation subtraction is exposed as a positive economic credit, or raw
unvalidated tree tags can enter the active ledger. Those are API/precondition
requirements, not assumptions that an arbitrary reusable allocator is safe.

## Current source paths

The inspected `ZZZRoyaltyRewards` has exactly four `_distribute` call sites:

| Path | Existing liability update | Necessary invariant |
| --- | --- | --- |
| Reviewed allocation from orphaned units | AddsA before `_distribute` | RemoveA from orphaned and add exactlyA to funded rights; never spend old liabilities. |
| First opening allocation | Addsinitial before `_distribute` | Preserve the captured opening cohort, all openingPool/raw units and zero-cohort orphaning. |
| Normal successful `_sync` | AddsA after `_distribute` | Must reserve before a counterless tree credit; keep old cohort settlement before waiting enrollment. |
| `canonicalSettle` | AddsA before `_distribute` | Settle the captured source pending amount once, before backing is transported; preserve abort state. |

The least error-prone structure would have the ONE private `_distribute` own
the checked reservation: read oldL for that exactasset, reserve oldL+A, then
credit the corresponding book with that authenticated oldL. Remove the four
caller-side increments rather than maintaining a future convention at every
caller. The helper already receives asset/amount/cohort and makes no external
call, so reservation and tree work can remain atomic. Zero-amount behavior and
event ordering must retain their current definitions.

The library's funded-bound parameter should be mandatory and explicitly named;
do not leave an old overload that accepts unbounded credits. For generic
positive `addRange`, check `delta*inclusiveCount` and the actual liability plus
that amount. Its private complementary negative-tag writes are representation
operations, not separately funded ranges. The production ledger currently does
not call `addRange`; its generic test harness needs its own checked economic
total if the stored Book counter is removed.

After `_sync`, `_claim` currently performs only internal tree/accrued operations
until it debits global liabilities/accounted and calls `_sendRaw`. Capturing
that currency's currentL once for all its ticket takes is therefore coherent.
Keep the checked per-NFT additions and aggregate debit; individual result≤L
alone would not authorize their unchecked sum. Current reentrancy and post-send
backing checks remain binding, including a receiver returning fresh ETH.

## Opening, faults, imports and recovery

- A failed isolated optional-currency sync must roll back its reservation and
  every tag/cursor change together. Its old cohort remains unchanged. A cheaper
  implementation must not skip healthy allocation or shrink the1M allowance.
- Before opening or with zero eligible weight, receipts go to openingPool or
  orphaned; they do not enterL or any tree. A later reviewed allocation reserves
  exactly the newly assigned amount. A zero-amount recovery changes no bound.
- Canonical import stages authenticated per-NFT accrued records under an inert
  state and validates their sum against imported liability before activation.
  It does not import raw books. The active successor's imported accrued plus
  later new tree credits therefore satisfies the same global invariant.
- Source canonical transport can move backing while economic calls are frozen;
  its book/L mirror remains intact for funded abort. The bound is the liability,
  not the temporarily moved source balance. Retired/cancelled ledgers cannot
  use it to reopen ordinary economic work.
- Negative rebases, failed exact transfers, malformed balance replies and
  unsupported tokens retain their existing failures. Donations/positive rebases
  do not authorize fabricated liability or a different cohort.
- Unit2/unit3 outstanding credits coexist with later unit1 allocations. The
  global bound must cover ALL those books plus accrued rights, not just the
  current allocation unit. Assets and raw decimal units must never be mixed.

Restoring the original mapping-only Book shape avoids the experimental extra
slot; original positive tags are also valid modular coefficients. This does
not authorize changing immutable deployed code, reusing old source/runtime
reviews or transplanting arbitrary raw storage. Existing deployments remain
historical, and the actual release's exact implementation/payload pins still
need a fresh accepted source stage.

## Evidence required if the measured counter candidate remains over budget

No shortcut is accepted merely because it removes storage writes. Measure the
same complete cold Entry states and exact full20% padded20M calls. Keep known
failures and source stages; do not add component savings to a previous total.

In addition to the prepared four integration methods, check actual currency
liability against an independent per-NFT/book model across every credit/take,
partial claim, compressed-unit transition, opening/deferred recovery, canonical
import and abort. Test imported accrued nearUINT_MAX followed by a new credit:
an empty tree does not make that currency's global capacity empty. Check caller
underfunding/isolated OOG restores both liability and coefficients atomically.

The newly requested production-ledger UINT_MAX case should use real token
supply, Commun1 plus Legendary3 (width4), exact independent expected shares,
all payouts drained, and the same units transferred back for three cycles.
It tests complementary decomposition at a real maximum-funded bound without
inventing token mint capacity or treating lifetime income as outstanding debt.
Also preserve W1's valid UINT_MAX/zero-remainder case and checked overflow
rejection without mutation of existing rights.

No counterless implementation or additional test was run by this review. The
currently prepared counter-candidate consumer/payload files remain unchanged.
