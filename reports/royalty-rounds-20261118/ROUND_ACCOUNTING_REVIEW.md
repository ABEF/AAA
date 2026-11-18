# Exact royalties without receipt-history allocation work

This is an internal implementation review, not independent release approval.
The selected fresh profile uses Factory payload 5 and
`ROYALTY_ALLOCATION_VERSION=2`. Original-currency settlement remains version 4;
recovery version 2, public settlement events and flattened canonical rows retain
their meanings. Historical raw tree storage must not be loaded into round books.

## Accounting identity

For eligible normalized prefix W, cursor C and actual received amount A, credit
advances full rounds by `A/W + (C+A%W >= W)` and cursor to `(C+A%W)%W`.
For any eligible ticket t, the allocation is exactly
`deltaRounds + [t <= newCursor] - [t <= oldCursor]`.
This equals the prior quotient plus cyclic-remainder allocation for every unit.

Eligible prefixes only grow. New tickets append after the old prefix and
therefore after its cursor. Capturing their birth-round baseline after old-cohort
credit excludes all past income. Ordinary payments update constant-size state;
they do not create receipt records, append work queues or scan holders.

Lifetime rounds, interval gross amounts and paid counter debt use modulo2^256
coefficients. Actual same-currency liability additions remain checked before
credit. A counter claim is bounded by the actual liability; imported accrued
is added separately with checked arithmetic. Existing checked liability and
accounted debits, exact current-owner transfer and final backing checks remain.
The modulo representation does not authorize spending an unbacked coefficient.

## Eligibility and unit phases

Each eligibility expansion records one immutable end ordinal and its round
snapshot. Ends are strictly increasing uint16 values bounded by 1000, giving at
most 1000 records per currency for its entire lifetime. A binary search needs at
most10 iterations. Repeated payments after the last activation add no records.

The unit at that immutable end is derived from the existing rarity-prefix data.
A homogeneous Rare/Legendary prefix uses unit2/unit3; it can only transition to
unit1. The old book then stays frozen. Its members retain those old earnings,
while their future unit1 income starts at the preserved raw cursor. A new book
subtracts its initial cursor indicator so starting midway through a round creates
no income. Later unit1 entrants do not inherit a frozen homogeneous book.

Claims subtract both the birth baseline and previously paid counter units.
Imported `accrued` is never inserted into counter debt. Transfers keep all rights
and debt attached to the NFT. Dormant ordinal0 returns no counter entitlement.

Healthy activation captures receipts and credits the previous cohort before
enrolling the entrant. The enrollment snapshot uses the **post-enrollment unit**.
Fault recovery first credits unseen receipts to the previous eligible cohort,
then enrolls all waiting activations with one checkpoint. No waiting-holder loop
is introduced. These preserve the previously accepted fault-entitlement rule.

## Opening and canonical lifecycle

During minting and the following one-hour window, funds remain in the opening
pool. Opening eligibility is checkpointed before initial allocation, including
pre-cutoff activations whose currency was temporarily unreadable. Later
activations receive the post-allocation baseline. An empty opening cohort still
uses the existing explicit unallocated-recovery rule.

Canonical export flattens exact per-NFT claims; round counters, cohorts and paid
debt are not serialized. The destination starts with empty books and zero debt,
stores imported accrued independently, and enrolls its imported prefix at zero
rounds. The first new credit initializes the imported cursor as an offset. Source
round state stays intact for abort. Existing inert-destination prefund and late
receipt treatment is unchanged.

## Bounded activation reads

The following paragraphs describe the initial phase1 source, not the final C08 funding path. The original complete-sync allowance and caller-underfunding check remain. Only
the token's activation-time `balanceOf` STATICCALL gets the separately governed
read maximum, initially 50000 gas. The caller copies one word and accepts at least
32 return bytes, preserving ABI-compatible padded responses without copying
arbitrary return data. Short/reverting/OOG reads defer atomically to the existing
old-cohort recovery path. Ordinary sync and claims retain their existing reads.

The cap is a maximum, not a promise that every high setting can be fully forwarded
inside the existing whole-sync frame. The newly proposed inner minimum-gas guard
was removed because a 1M read maximum must not reject a cheap token automatically.
The original outer full-sync guard still prevents caller-selected underfunding.
Higher caps, increased currency capacity and unusual token implementations need
renewed whole-workload qualification.

## Evidence and limits

The final arithmetic prototype has eight focused current methods, with an
independent per-ticket model and a frozen v4 preview reference. It covers growing
prefixes; partial/repeated claims; homogeneous-to-mixed phases; fault groups;
opening cutoff; imported accrued and nonzero cursor; maximum values and repeated
lifetime wraps; a newborn at exactly zero wrapped rounds; cohort search through
ordinal1000; and full-width/future-interval preview equivalence.

Earlier bitmap prototypes and oversize source candidates remain separate
historical stages. The sorted-array implementation replaces that unadopted
bitmap. No unchanged historical test method is rerun. Actual Royalty/NFT/token
integration and near 1000-NFT 20M workload evidence are separately recorded by the
parent campaign; component gas must not be summed into a whole-flow guarantee.

The selected source passed the proposed 48 normal size gates. Royalty runtime is
24571 bytes, leaving5; Vault leaves 32 and Oracle 3. No gate, compiler setting,
financial cap or gas default is raised. Actual-source normal compilation and
strict admission are recorded separately. Four current-architecture comment
lines change after the proposal; no prepared byte-equality claim is made for
that explicitly recorded comment-only difference.


## Final C08 funding and source boundary

The complete-sync maximum remains1M. A captured full-frame witness preserves its original120k funding margin; a partial frame must independently fund the configured balance read plus120k before STATICCALL. Only the child's exact4-byte unavailable signal permits cheap deferral after a fully funded failed read. Other failed partial frames revert activation. See [final source review](FINAL_SOURCE_CHANGE_REVIEW.md) and [funding regressions](ledger-c07/RESULT.json). The initial paragraph about removing the proposed inner guard is historical; the final funded-read guard avoids caller clipping while cheap reads under a high configured maximum retain the full-frame path.

Final actual normal compilation passes48 gates, with Royalty24,572runtime bytes/4bytes headroom. Private accounted is now a checked derived identity; pre-import synchronized target prefunds are classified once. Actual launch-scale verification is separate from this arithmetic proof.
