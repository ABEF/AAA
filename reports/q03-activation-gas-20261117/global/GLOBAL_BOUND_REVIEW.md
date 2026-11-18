# Global-bound royalty allocator: scoped analysis and experiment

This is an internal source/economic review. The experimental files and virtual
builds do not alter a deployed contract, authorize release or qualify 20M gas.
The campaign name retains 17 November; later execution timestamps are 18 November.

## Preserved economic invariant

For each admitted currency, checked `liabilities[asset]` is the sum of imported
or already materialized `accrued` plus outstanding tickets in its unit 1/2/3 books.
Each book and each individual ticket is bounded by that same currency's global
liability. Imported accrued makes the bound larger without invalidating it.
Different currency liabilities cannot substitute for one another.

The proposed caller pair centralizes all four monetary credits in private
`_distribute`: opening allocation, ordinary received funds, explicit unallocated
recovery and canonical cutoff settlement. The allocator checks and returns
`oldGlobalLiability + actualAmount`; the caller stores that returned value.
Neither operation contains an external call. The earlier ordinary sync's
post-distribution addition moves into that same internal pair. No credited
receipt, historical entitlement or orphan recovery rule changes.

The proposed claim captures the actual liability after synchronization. It
starts with the NFT's accrued balance, passes checked remaining liability to
each ticket take, accumulates amounts with checked addition, then preserves the
existing checked global-liability/accounted debits and exact current-owner
transfer. The library's bound is not supplied by the NFT holder. No new public
function, authority, asset, book field or storage slot is introduced.

## Why modular tags preserve exact units

For captured weight `W` and amount `A`, let `A = qW + r`. The previous representation adds `q`
to every eligible ticket, then 1 to the next cyclic `r` tickets. If `r > W/2`, the new
representation adds `q`+1 to that same prefix and subtracts 1 from the complementary
cyclic `W-r` tickets. Every leaf's mathematical entitlement is identical.

Tags, carry and path sums are coefficients modulo2^256. Credit's actual monetary
addition is checked before any tag write; takes are bounded by the checked
remaining global liability. Parent debits and final transfer/backing checks stay
checked. A coefficient may wrap while a payable claim cannot exceed actual
backed liabilities. The library's positive `addRange` seam also checks its actual
delta-times-count budget and caller total; it provides no unbounded overload.

Unchecked indices are bounded after validation:1≤W≤3000, cursor<W, leaves≤7095,
tree nodes≤8191. Complement q+1 is evaluated only when r>W/2, which impliesW≥2
and excludes quotient overflow. Weight0 is still rejected by cursor≥weight for
every unsigned cursor. The W=1 / UINT_MAX valid case does not calculate `q+1`.

This representation is coupled to an authenticated caller liability. It must not
be copied as an unbounded generic allocator. Canonical royalty export already
flattens exact per-NFT rights rather than serializing raw tags. Matching public
storage layout does not authorize a hot upgrade, relabel an old runtime or prove
arbitrary transplantation of partial internal state.

## New finite evidence

`EXPERIMENT_RESULT.json` and `EXPERIMENT_FORGE.json` record five distinct new
methods; all pass. The frozen positive-only library is the original source
control, and a separate per-NFT arithmetic model checks rights. Coverage includes
homogeneous unit2/unit3 histories transitioning to mixed unit1, imported accrued,
other-currency separation, partial/repeated claims, long recredits, UINT_MAX,
checked overcredit, insufficient claim bounds and rollback before healthy retry.
No unchanged old method runs. This is a controlled internal caller model;
actual NFT/token/canonical integration is separate parent-owned evidence.

The fair cold-credit comparison includes the authentic caller's existing
liability write in every implementation. For W=1499 / A=2996 / cursor=513, positive
cost 645262, duplicate-counter 284063 and global-bound 261721 gas. The duplicate
counter therefore costs 22342 extra gas per new currency in this measured case.
These are component calls, not whole activation estimates or capacity approval.

## Envelope alternative rejected for this candidate

Four further new envelope methods pass in the separate `envelope` evidence.
An exact dyadic envelope minus a cancelling tail reduces some prefix writes and
preserves future-ticket zero entitlement, growing prefixes, partial claims and
UINT_MAX. Its additional runtime fails the actual normal EIP170 gate:
Royalty 24800 bytes, 224 bytes over 24576. It also shifts work to claims: the measured
W=1499 cold edge-ticket take rises from 47382 to 220575 gas; cold views stay near 37k.
No limit was raised and that candidate was not ported. Its preflight and initial
test-only reserved-identifier compile failures remain recorded as zero executed
methods, not passing coverage.

The simpler global-only complementary representation was selected and ported.
The final actual02 normal build passes all48 size gates, unchanged public ABIs
and semantic storage layouts, exact100-source closure and the existing strict
reference importer. Royalty runtime leaves25 bytes. Actual integration and
whole-flow measurements retain their separately recorded source scope. It does not prove that every 20M activation can fit. Sixteen faulty
currencies may legitimately consume their individually bounded gas allowances;
no healthy entitlement is deferred to manufacture a smaller benchmark.
