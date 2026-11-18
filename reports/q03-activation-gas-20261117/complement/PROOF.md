# Experimental complementary royalty allocation

This is an accounting-representation experiment, not a production promotion.
The new library is under `test/fixtures`; no production import uses it.

## Invariant and credit equivalence

Let M=2^256. Interpret every root-to-leaf lazy-tag sum modulo M. At each
completed operation it equals a nonnegative entitlement E[t], with E[t]≤B≤UINTMAX.
B is the checked `Book.outstanding` total of all outstanding ticket entitlements.
Only private tag/carry arithmetic wraps. Credits check B+A; positive range credits
check both delta×ticketCount and the addition to B. No negative economic range
operation is exposed.

The total bound alone does not prove ownership fairness. Exact allocation and
claim-path correctness still depend on this internal representation invariant;
the independent per-ticket model and fixed positive control test that property.

For eligible weight W, cursor c and A=qW+r, the current rule credits q to every
eligible ticket and one extra to the cyclic r-ticket interval after c. The next
cursor is (c+r) mod W. When r>W/2, the experiment instead credits q+1 to the
prefix and subtracts one from its complementary W−r cyclic interval, beginning
after the next cursor. These are identical integer entitlements ticket by ticket;
future tickets receive zero. UINTMAX is the coefficient minus one in the ring,
not a backed payment or economic credit.

The complementary branch implies W≥2, so q+1 cannot overflow. W=1,A=UINTMAX
stays on the original branch. The temporary full-prefix total may exceed UINTMAX:
W=4,A=UINTMAX temporarily represents UINTMAX+1 before excluding one unit. Check
the actual B+A once, never that temporary prefix as an economic range credit.
Validated endpoint/cursor arithmetic stays below6000; tree indices stay≤8191.

## Reads and claims

Ring path addition reconstructs E[t] modulo M. Because the complete mathematical
entitlement is in[0,UINTMAX], that residue is the unique correct payout value.
The final experiment's checked `B-=amount` enforces the selected payout bound.
It must not compare intermediate tags/carry with B: those may represent negative
values. A view-only comparison is unnecessary under the invariant. The initial
prototype also performed redundant explicit comparisons; omitting them does not
allow the final economic subtraction to wrap.

Claims propagate the selected path's coefficient to its unselected sibling,
retain it in memory for the selected child, then clear the selected leaf. All
coefficient/carry/leaf sums wrap consistently. Other path sums remain unchanged.
The final actual amount is checked against B and subtracted with checked
arithmetic. Zero-entitlement claims can traverse cancellation tags and must pay
zero. Complete drainage, later receipts and prefix growth must not resurrect
old income or overflow a lifetime accumulator.

## Compatibility boundary

Appending B inside the book keeps its mapping at the original struct offset;
it remains a storage-representation change needing fresh source/runtime review.
An old nonempty raw book must not be reinterpreted: its missing B invalidates the
new invariant. Immutable old deployments keep their original code.

Royalty canonical records flatten per-NFT claims into `accrued`, rather than
serializing lazy tags. Fresh imported books and B start at zero; imported accrued
rights stay separately backed. Later receipts populate only new books. Actual
host/canonical verification remains necessary before promotion. Exact-LP's
different allocation library remains untouched.

The final experiment reuses existing `InvalidAllocation`; the initial
`InvalidOutstanding` error is removed. The checked payout subtraction fails with
Solidity's arithmetic panic if its economic bound is violated. `weight==0` is
still rejected by `cursor>=weight` for every unsigned cursor, so the explicit
duplicate predicate is removed. Final leaf deletion is unconditional: clearing
an already-zero warmed slot can add100gas to that claim, with no payout change.

## Finite experimental evidence

`prototype02` executes four new methods: cold rotated1023/1499/3000 ticket credit
equivalence/drainage; growing prefixes with partial claims and recredit; UINTMAX
and repeated drainage; positive range-product budgets and invalid-input rollback.
The existing positive engine and a direct integer per-ticket model are controls.

`prototype01` selected zero methods because an unrelated in-progress host fixture
referenced a private getter. That compiler failure remains recorded. The second
attempt explicitly excludes only that host fixture. The cold-gas method then
adds retained numeric logs and executes alone in `prototype03`; the other three
unchanged methods are not rerun at that stage. `prototype04` then runs all four
affected methods after the representation's branches/checks are consolidated.
Its positive control is a frozen23be8c9 copy, not a moving production import.
All four pass with stable sources. These are four distinct methods, not nine
distinct features from summing the staged executions.

| W | Existing cold credit | Experimental cold credit | Saved | Nonzero tags |
| --- | ---: | ---: | ---: | --- |
|1023|650372|307934|342438|27→12|
|1499|628324|263354|364970|26→10|
|3000|629899|241476|388423|26→9|

These controlled harness CALL-body measurements include the new checked total
write. They are not fees, whole activation gas or production approval. Claim gas,
all-fault activation, first-opening allocation, homogeneous unit2/3→mixed unit1
phases, factory construction, canonical transfer and full nearly1000-NFT
activation remain integration obligations. Finite differential examples support
the invariant; they do not establish exhaustive formal verification.

Normal-settings `size-probe01` confirms identical four selected host ABIs but
rejects the first virtual candidate's Royalty runtime24789 (213bytes over the
unchanged24576 limit). Access creation48546 has606raw bytes before constructor
arguments. No gate is raised, and this candidate is not shippable.

`size-probe08` consolidates the complementary and positive interval branches,
uses bounded `addmod` for the rotation cursor, retains checked economic total
addition/subtraction, removes the duplicate zero-weight predicate and clears the
final leaf unconditionally. The production Royalty host and original checked
preview arithmetic are unchanged. The selected virtual normal build reports
Royalty runtime24545/31bytes margin, creation25543; Factory creation29004; Access
creation48302 plus96constructor bytes, leaving754bytes; NFT stays24234runtime.
All four selected ABIs are identical. This is a selected code-generation probe,
not all normal size gates or an adopted production runtime. The exact virtual
source is frozen externally as `FINAL_CANDIDATE.sol`, SHA256
`5733ebada4066f028c0c09e6a2d6603d2b1b28b5bdc3aeb16fcf787f4cbd9df8`.
