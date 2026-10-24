# Scoped audit verification - 2026-10-25

This is internal, source-scoped evidence. **Production NOT APPROVED.** Exact
commands, input hashes, diagnostics and final reuse boundaries accompany the
receipts below. No actual wallet, public transaction, provider, service or chain
was changed. [Findings and remaining gates](REVIEW.md).

## Keeper and read-only preflight

[Service review](services/REVIEW.md) and [final bindings](services/final-bindings.json):
**199 distinct scoped Python passes, one explicit Unix-only skip**. Eighteen new
regressions cover fees and preflight. The independent harness reproduced failures
before the implementation fix. A stale mocked-live fixture's fee policy was
repaired and only that case rerun; the final sanitized legacy diagnostic branch
also has its own final-source rerun. Repeated cases are counted once.

The complete final-source suite was not rerun. The only final production delta
from the broad receipt is a fixed sanitized event inside the already tested
legacy-refusal branch; mechanical equivalence and its focused rerun are recorded.
The actual pinned `cast --help` parser ran, not transaction signing. Windows
cannot qualify Linux ownership/locking; Ubuntu CI and real operating evidence
remain separate requirements. No existing journal was rewritten.

## Composed economic and invariant checks

The new `test/IntegratedEconomicConservation.t.sol` executes installed v4 Core,
StateView and PositionManager with actual protocol accounting. Mock governance,
admission, USD prices, token, VRF and Permit2 are explicit substitutes. Actual
swaps/LP fees, independent ingress/claim totals and meaningful successful actions
are required, rather than only asserting copied index formulas or generic reverts.

The original four generic-fee scenarios passed. A deliberately more faithful
selected-fee fixture exposed the thin-market rejection recorded in A-07; it was
not discarded or treated as a production exploit. The final harness distinguishes
that full-rollback case from deeper-liquidity lifetime success and requires the
specific final source callback/error. Its final receipts and reuse boundaries
are recorded in the economic evidence in this directory.

[Economic verification](ECONOMICS.md) records **five distinct actual-v4 scenarios**:
three changed/new cases pass on final source and two unchanged selected-fee cases
retain their exact earlier scope with pinned shared function/helper text. There
is no blanket final-file rerun claim. The final 50 source/test bindings and 133
compiler/dependency bindings match; package/toolchain identities and retained
failure/compile-only diagnostics are explicit.

The existing `NFTRightsInvariants` handler now generates valid equal-sided growth
amounts under the $5 production minimum and asserts completed share growth.
Its repaired invariant passed **32 runs x 128 depth = 4,096 calls, zero reverts,
zero discards and zero failed corpus replays**, with all 11 selectors exercised.
Selector counts include intentional pause/eligibility early returns; they are
not a count of successful top-ups. A separate minimum-bound test proves a top-up
actually completes and preserves rights. This invariant uses the earlier mock
venue fixture and is not selected-chain evidence.

## Unchanged evidence and tooling

Production Solidity source is byte-identical to the preceding
[on-chain safety snapshot](../onchain-safety/final-solidity-bindings.json).
Its **37 normal source-object gates** and prior scoped gas/semantic evidence are
reused for that exact unchanged source, not rerun or added to today's pass count.
No compiler size/gas limit was relaxed. Vault's previous measured runtime remains
24,551 bytes, only 25 bytes below EIP-170; any future code change needs fresh gates.

The [scope/consistency receipt](scope-consistency.json) checks source/service
bindings, current document targets and preservation of the old local source-check
draft. Todo is generated from its sole JSON ledger. Documentation corrections
were checked against actual callable functions, guards and rounded-up formulas;
they do not require another unrelated contract suite.

The improved test fixtures compile under pinned solc0.8.26/Cancun, Foundry1.4.4,
via-IR/optimizer1 with the existing Yul profile; no code-size override was added
to the isolated profiles. Execution of test fixtures does not replace the
unchanged normal production object gates. No fresh
full final-source regression, new fork campaign, independent static analysis,
live RPC/VRF/route/feed qualification, website build or service rehearsal is claimed.

## Publication and old drafts

Only the owned audit fixes, tests and aligned records are intended for publication
on main. Older routing/fork/history/design drafts are excluded and remain local;
they are not implicitly approved by this review. For overlapping current operator
documentation, source-verified corrections are staged selectively over committed
HEAD. Consult the separate publication receipt and exact Git status for what
was actually pushed. Memory updates do not publish a website build or enable
production transactions.
