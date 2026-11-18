# Current-source compatibility and safeguards

The admitted normal build is `build/current`: 100 closed sources, 48 normal
runtime/initcode gates and strict function-reference import pass. The only
declared ABI/storage changes are ProtocolPolicy's independently reviewed read
policy and Royalty's fresh allocation state/getter. Compiler settings and gates
are unchanged. Actual source/dependencies, all four required build-input files
and the compiler are bound before/after the build.

## Royalty surface and storage

Existing public functions, event formats, settlement version 4, recovery version 2
and flattened canonical row formats remain. The new read-only
`ROYALTY_ALLOCATION_VERSION()` returns 2 and is required by the explicit Factory 5
consumer. Factory 3/4 and existing deployed runtimes keep their historical pins.

`STORAGE_COMPATIBILITY.json` compares the actual compiler layouts. All existing
Royalty top-level labels, slots and offsets remain. Only the private
`allocationBooks` value representation changes: each book now contains a full
round counter and one packed cursor/initial-cursor/initialized word. Two new
private mappings, enrollment and paid-counter debt, append at slots 55/56.
This is a fresh private accounting format, **not raw-storage upgrade compatibility**.

Enrollment uses sorted uint16 end ordinals, not the earlier experimental bitmap.
Strictly increasing ends bounded by 1000 imply at most 1000 cohorts per currency.
Binary search is bounded by 10 iterations. Payments alone append no cohorts.
An existing last boundary cannot be rewritten; a lower boundary is rejected.

The global monetary liability addition, actual balance accounting, aggregate
claim addition/debits, exact current-owner transfer and final backing check stay
checked. Unchecked arithmetic is confined to validated bounds and lifetime
coefficient/debt arithmetic with a checked actual payout bound. A Book's packed
initialized marker remains nonzero even when its round counter wraps to zero.

## Canonical compatibility

Export remains exact accrued plus unclaimed per-NFT units. Raw round state,
birth cohorts and paid debt do not cross the boundary. Import stores those flat
claims in accrued, enrolls the imported prefix at zero rounds and uses the
imported cursor as an initial offset when its first future credit occurs.
Imported accrued never increments paid-counter debt. Source state is retained
for abort. Existing prefund/late-receipt rules remain.

This supports the existing economic wire; it does not authorize relabeling old
runtime inventories, replaying old raw books, upgrading deployed contracts in
place or adopting a new environment. Actual graph/consumer/runtime matching is
still required.

## Activation read isolation

Only activation's optional-currency balance read receives the new governed
maximum. The original full-sync allowance and outer underfunding guard remain.
The decoder copies one word and accepts trailing ABI-compatible output. No new
inner minimum-gas gate makes a high maximum automatically reject a cheap token.
OOG/revert/short/under-backed reads roll back their isolated currency work and
retain the previous eligible cohort. This does not make arbitrary malicious,
rebasing, taxed or permanently broken tokens safe or always transferable.

## Evidence scope

The final current arithmetic prototype has eight methods. Earlier five-method,
two-boundary and bitmap stages are not additive. The renamed bitmap-boundary
case is an alias of the current search-boundary case, not a new economic feature.
Full actual-ledger and physical Entry/Vault workload evidence is recorded
separately; component gas cannot establish whole-operation qualification.

Royalty runtime leaves 5 bytes; Vault leaves 32 and Oracle 3. All gates pass, but
future source work must preserve those limits. Earlier oversize candidates and
the initial virtual-only Yul naming refusal remain separate historical attempts.
The final actual build contains four approved comment-only corrections relative
to the proposal and makes no false prepared-byte-equality claim.

No public signing, deployment, sealing, site/service operation, existing-chain
reset, journal rewrite or heartbeat restart is performed by this source work.
