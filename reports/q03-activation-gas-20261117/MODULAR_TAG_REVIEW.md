# Independent critique: complementary exact-unit royalty allocation

This is a mathematical/source review of the proposed algorithm, before adoption.
No production change or test execution is performed by this review. It does not
approve a particular implementation that has not yet been inspected.

## Conditional mathematical result

Complementary dyadic tags are valid **if** their only unchecked arithmetic is
explicit modular representation arithmetic and the economic total remains
checked. Let Q=2^256, U=Q−1, and B be a book's outstanding economic units.

Maintain these invariants:

1. Each ticket's exact integer entitlement e(i) is nonnegative, their sum is B,
   and B≤U. For every supported ticket, summing its ancestor tags moduloQ returns
   e(i). Thus the final modular result has a unique correct uint256 value.
2. An economic credit of A checks B+A≤U once. For widthW, quotientq and remainderR,
   the ordinary increment is `q + indicator(remainder arc)`. IfR>W/2, this equals
   `q+1 − indicator(complementary gap)` for every ticket in1..W. Tickets beyondW
   are unchanged. Updating the corresponding dyadic intervals moduloQ therefore
   preserves exactly the same integer leaf rights.
3. Taking a ticket pushes its ancestor carry into the unselected siblings and
   clears the selected path. This preserves all other path sums moduloQ and
   makes the selected leaf zero. All tag, carry, sibling and final leaf/carry
   additions on this representation path must wrap explicitly. The FINAL paid
   amount must be≤B and B must subtract it checked. Intermediate negative tags
   or carries must not be mistaken for economic amounts and compared againstB.
4. A positive public/internal-API `addRange(low,high,delta)` request checks
   `delta*(high-low+1)` and B+that amount. The private complementary subtract is
   a representation operation, never an exposed arbitrary negative credit.

These invariants hold under prefix growth: the new credit changes only its
captured eligible prefix, and a previously unused ticket has zero net path sum
until actually credited. A zero-value take may normalize cancellation tags, but
must return0, preserveB and leave every other ticket's rights unchanged.

## Concrete implementation traps

- **Temporary full-prefix overflow:** W=4,A=U gives R=3 and q=(U−3)/4. The
  complementary full-prefix temporary amount `(q+1)*4` is U+1, although the
  actual requested credit U is valid. Do not route the temporary full-prefix
  write through a separately checked/accounted positive `addRange`, and do not
  increment outstanding for the full prefix then subtract the gap. Check the
  actualA once and manipulate only tags for its decomposition.
- **Eager q+1 overflow:** W=1,A=U,R=0 is valid. Calculatingq+1 unconditionally
  would revert before reaching the ordinary branch. Compute it only when the
  complementary branch is actually selected; in that branch W≥2 makes it fit.
- **Partially checked take:** leaving the final `leaf+carry`, a sibling's
  `oldTag+carry`, or the carry accumulator as a checked addition can revert for
  perfectly valid cancellation tags. Conversely, economic B updates, payout
  totals and actual input products must not become unchecked.
- **False raw-layout equivalence:** equivalent leaf rights do not imply the
  same raw dyadic tags as the earlier positive-only algorithm. Adapt the
  affected raw-node differential assertion to prove intended economic and
  canonical equivalence; do not retain or report a false raw-tag identity.
- **Outstanding is not lifetime earnings:** draining all units must restoreB=0
  and allow another U-unit credit. Claims and failed transfers must update or
  roll backB with the same atomicity as the tree and asset liabilities.

## Royalty-specific interactions

The production royalty book is a value in nested mappings. Appending
`uint256 outstanding` after its existing pending mapping leaves that mapping's
base slot unchanged; the new field occupies the Book base+1. It does change the
internal value layout. Raw-copying an older nonempty book into a new code image
with outstanding0 is invalid and must not be advertised as compatible. A dense
standalone test struct followed by other state can have different layout impacts
from this production nested-mapping value; inspect actual compiler layout.

Unit1, unit2 and unit3 books can coexist. A homogeneous Rare or Legendary cohort
can have outstanding compressed-book credits when another rarity changes future
allocation to unit1. Their separate B values bound their own ticket entitlements;
do not reset a historical book, sum unrelated ticket indexes or apply the new
cohort width to an old credit. The current permanent-first-ticket indexing must
continue to exclude future NFTs from the older compressed books.

For a settled asset, the stronger whole-ledger check is:

`liabilities = B(unit1)+B(unit2)+B(unit3)+sum(imported accrued per NFT)`.

Opening pools, orphaned units and unsynchronized raw receipts are separate. A
book's outstanding need not equal the asset's entire liability after canonical
import. Existing checked ledger additions and actual backing still constrain
the combined units across books. A failure after an earlier book mutation must
revert the whole transaction, rather than leaving a new B or cursor behind.

The royalty canonical path exports per-NFT flattened claim amounts, not raw
dyadic tags. A successor can import those units into accrued balances with empty
books/B0, then account only new receipts in its new books. The source tree and
B must remain intact through a funded abort. Test capture/settle/export/import,
partial claims, a transfer and future receipts; do not assume output equality
merely because node tags are mathematically equivalent. The separate LP exact-
unit engine does not use this library and must not be changed by analogy.

This internal algorithm makes no external call. Existing reentrancy, exact-token
transfer checks, balance-deficit rejection, optional-currency isolation, opening
cutoff and old-cohort recovery must remain untouched. A positive token rebase is
still indistinguishable from a donation, and a negative rebase or failed token
transfer still fails closed; modular internal tags do not repair token behavior.

## Required new evidence before adoption

Use an independent integer per-ticket model across direct/complementary
branches, wrapped/unwrapped arcs, prefix growth, arbitrary claim order, zero
claims, all units drained and recredited, and an overflow refusal preserving
all previous rights. Include U credits atW1 andW4 explicitly; existing U tests
only iterate widths1..3 and miss the complementary temporary-overflow example.
Check B against the model's sum after every operation, not only returned totals.

Run the new complete811/999 Entry cases in TEST_PLAN.md, including a full-budget
currency fault, opening cutoff and compressed-book transition. Reuse old
unchanged evidence only at its exact source scope. A lower unique-node count
alone does not prove an entire activation fits20M with full20% margin.

The accepted prior normal build records RoyaltyRewards runtime24,524/24,576
(52 bytes headroom), Factory creation28,983, and Access creation48,281+96
(775 bytes initcode headroom). The royalty creation payload and both immutable
data-child pins change; Factory and transitive Access construction must be
remeasured. Appending a bookkeeping field and checks is not automatically a
size improvement. No compiler gate or safeguard may be relaxed to make it fit.

Retain historical payload3, normal/static records and observed runtimes. Prepare
the exact new factory payload/build and compatible consumer selection separately.
An unchanged external ABI does not make changed deployed bytecode identical.

## Actual proposed01 implementation check

The complete proposed normal build's purpose-header library is SHA256
`22f42cbfd5220aa2605c048ea8809ad96c18c2f896e258293e9116af22f37b02`.
Its complementary gap starts at the computed nextCursor and its quotient
increment occurs only inside that branch. Thus the two concrete U-value traps
above are avoided. Its checked economic amount/product additions and final
checked `outstanding -= amount` preserve the proof's economic boundary; every
internal coefficient/carry/final leaf addition wraps explicitly.

**Precision:** this final candidate does not perform an explicit per-view
`amount <= outstanding` comparison. `viewTicket` derives that bound from the
nonnegative-leaf/sumB invariant established by the validated write/take paths.
The checked final take subtraction enforces the actual payout bound. This is
not evidence that corrupted or transplanted historical raw trees are safe;
those remain unsupported, and canonical import continues to use flattened
accrued claims. The source review found no counterexample under the stated
invariant. It is separate from the still-required executed financial/complete
gas evidence and does not count as an additional test pass.
