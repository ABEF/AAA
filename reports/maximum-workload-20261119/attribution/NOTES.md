# Offline attribution:64 currencies, two LPs, opening ZZZ/all-slow

The retained producer06 call succeeds at32M and its financial verification is
complete, but its estimate27,142,801 becomes32,571,362 with full20% padding.
The admitted estimate ceiling is26,666,666: a476,135 estimate reduction is
needed. No operating cap, padding, source allowance or economic right changes.

Only the existing compressed RPC record and source/ABI files were read. No
node, compiler, application test, public request or contract call was run.
`TRACE_ATTRIBUTION.json` pins every input and the offline analysis helper.
The ABI helper is imported only for pure selector hashing.

## What the actual call shows

| Frame group | Frames | Immediate-child-exclusive gas |
| --- | ---: | ---: |
| Royalty.syncForActivation |64|5,166,400|
| Royalty.activate outer own work |1|4,074,958|
| Optional-currency balanceOf |64|3,079,424|
| Rewards.syncShares |1|1,030,623|
| Rewards.syncMembership |1|1,016,618|
| Independent executionProof |16|962,544|
| Reference executionProof |16|952,144|

These are observations of one trace, not separately benchmarked budget pieces.
The64 token reads each receive the unchanged50,000 gas cap and use about48,116;
that is deliberately expensive but legitimate successful token behavior. All64
isolated sync frames receive the existing1M allowance and succeed. Eliminating
that support or silently deferring a healthy read would change requirements.

The trace has2,383 frames and reports25,910,993 gas used, distinct from its
27,142,801 estimate. Subtracting immediate child gas produces one negative
root residual(-641,918). Non-root exclusive work sums26,552,911; including the
signed root residual telescopes to the reported trace total. Preserve that
negative accounting observation rather than clamping it to zero or calling it
negative opcode cost. Refunds/trace/forwarding/estimation behavior cannot be
isolated from callTracer alone. A476,135 exclusive-frame reduction is therefore
not itself proof of a476,135 estimator reduction.

No old16-currency trace is treated as a matched optimization comparison. That
case has one LP, common-first order, different price/input and reference depth,
and a20M cap. The current case has two LPs, Legendary→Rare→Commun enrollment,
64 ERC20s plus ETH, synthetic6M external reference liquidity and32M.

## Justified candidate: a bounded enrollment bitmap

The retained storage proof shows all64 ERC20 currencies have992 enrollment
ends and the next append opens an empty packed16-end word. Current source also
updates the dynamic-array length and writes the new full-width birth round.
Those are real additional workload obligations, not duplicated currency reads.

Consider replacing only private `Cohorts.ends` with four256-bit words covering
the maximum1,000 activation ordinals. A set bit records the same immutable
eligibility end; a bounded next-set-bit search finds the first end>=ordinal.
Retain `roundsAt[end]` as full uint256, exact modular coefficients, all monetary
liabilities, before-join sync, cutoff/fault cohorts and every caller guard.
For this final append, the bitmap would update an already nonzero word and
need no array-length update. This directly targets avoidable enrollment writes
and may also simplify bounded claims reads. Savings are symbolic candidates;
no opcode-level SSTORE count, bytecode size or gas saving is measured here.

A safe review would cover0/1/255/256/511/512/767/768/999/1000 boundaries, sparse
fault enrollments, duplicate/decreasing ends, missing ends, separate initial
unit2/unit3 cohorts transitioning to unit1, full-width modular rounds, claims
and canonical import/abort. Generic
library validation must remain intact. This is a fresh private codec: it needs
explicit new source/Factory/runtime/storage admission and normal size checks.
Royalty currently has only14 bytes runtime headroom, so do not assume it fits
or relabel F6/old deployed storage. No production implementation is proposed as
already verified or adopted.

Other large costs are existing exact LP books and execution/reference proofs.
Their repeated calls protect different mutable boundaries. Do not remove them
from frame counts alone. Current activate already reads sync/read caps once;
there is no new per-currency gas-policy-cache shortcut to claim.
