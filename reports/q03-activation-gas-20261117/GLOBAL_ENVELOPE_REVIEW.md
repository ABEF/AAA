# Internal source review: global bound and dyadic envelope experiments

Reviewed read-only: `test/fixtures/Q03GlobalBoundAllocation.sol`, its coupled
host in `test/Q03GlobalBoundAllocation20261117.t.sol`, and
`test/fixtures/Q03EnvelopeAllocation.sol`. This is not review of an actual
production adapter patch that has not yet been supplied, nor a new test run.

## Global bound implementation

The experiment validates width/cursor first, computes the USED returned
`globalAfter=globalBefore+amount` outside unchecked arithmetic, then updates
only internal coefficients/cursors unchecked. This avoids a discarded economic
check and preserves the W1/UINT_MAX zero-remainder and W4/UINT_MAX complementary
cases. `addRange` similarly checks its positive `delta*count` and global sum.

`takeTicket` performs modular carry/leaf transformations, then explicitly
rejects a final amount above available. A rejection rolls back those writes.
The coupled host derives the bound from its own same-asset liability, never an
EOA input; its claim passes `liability-accrued-alreadySelected` to each take and
retains checked combined liability/cash subtraction. The raw harness deliberately
exposes arbitrary bounds to test this internal precondition, and is not the
production permission model or real token backing.

The source implementation matches COUNTERLESS_ALTERNATIVE_REVIEW.md's proof.
It still depends on the actual Royalty adapter centralizing all four liability
credit paths and using the checked returned value. Its runtime event order,
failure isolation, exact accounting and private call-site bindings must be
reviewed again when that final patch exists. No caller-supplied public numeric
bound is approved by this internal library signature.

## Envelope correctness

For validated W in1..3000, the smallest power-of-two envelope E is at most4096.
The exact prefix update is either a direct dyadic cover of1..W or:

`+delta on1..E, -delta on W+1..E`.

Every current ticket receives precisely the original delta. Every future ticket
up to E receives zero net change; tickets beyond E also receive zero. Negative
coefficients are internal modular representation, not negative cash. The same
global nonnegative entitlement/liability invariant therefore proves view/take
correctness, including subsequent prefix growth and zero-value future-ticket
takes. Imported accrued and older unit2/unit3 books remain separate.

The code's count comparison is correct for aligned prefixes: direct coverage
uses popcount(W) tags; the tail uses popcount(E-W), plus one envelope tag. A
power-of-two W produces equal counts and takes the direct branch, so the tail
branch never receives the invalid empty interval W+1..W. Private tag indexes
remain within the4096-leaf tree; public intervals/tickets retain their3000 limit.

Examples: W1499 changes the full-prefix encoding8→5 tags; W1023 changes10→2;
W1025 and W1024 remain direct. Combined with the same remainder/gap encoding,
these are algebraic node-count changes, not full-operation gas measurements.

## Required efficiency and evidence limits

Fewer credit tags do NOT prove every operation becomes cheaper. A high ancestor
envelope tag can make a later take materialize/clear more sibling carry than a
direct prefix. View depth remains fixed, but claim writes may increase. Record
cold credit AND claim effects; do not assume old12M claim-batch qualification
survives unchanged. Smaller exact selected batches remain a recovery mechanism,
not evidence that arbitrary large batches fit. Raw node representation differs
and cannot be reported identical to the old positive-only tree.

No mathematical counterexample was found in these inspected code paths under
their authenticated-liability precondition. This does not substitute for the
new production-ledger integration methods, complete cold Entry/RPC/padding
measurements, final normal size/storage/ABI gates or the actual source adapter
review. Experimental host cash is numeric state, not a real asset transfer.

The five actual Royalty integration methods separately pass on the PRE-
allocation/reuse2-source baseline; their compact source-scoped evidence is in
`integration/baseline03`. They have not been rerun on an adopted new engine.
Prepared counter-candidate payload4 files remain unchanged and explicitly
unadopted; this review does not rebind them to the global/envelope experiment.
