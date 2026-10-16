# Architecture capacity delta: current-source static analysis

2026-10-17. Pinned Slither 0.11.6 consumed the completed normal-profile production
build without invoking another compilation. Its typed AST, complete compiler
input/output and artifact bytecode bind all **29 current production sources**;
the review additionally binds `foundry.toml`, `package-lock.json` and
`slither.config.json`. Source hashes remained unchanged during analysis.
This is internal source/delta review, **not an independent audit or approval**.

There are **221 findings**: 40 High, 73 Medium, 69 Low, 33 Informational and
six Optimization. Compared with the previous 220 findings, 171 keep identical
fingerprints and 49 have identical semantics with shifted source line ranges.
The sole new finding recommends caching the four-slot registration array length;
its disposition is informational. The idempotent loop is bounded and contains no
external calls. Capacity-related rationales and current test references were
rechecked and updated; historical decisions are not relabelled as a fresh
comprehensive audit.

Current dispositions are **130 false positives / 46 accepted risks /
45 informational / zero unresolved detector entries**. The previous canonical
review is preserved byte-exact in [history](../../history/slither-review-pre-architecture-evolution.json).
The [current review](slither-review.json) also supplies the sole
[canonical review](../../production/slither-review.json).

| Evidence | Scope |
| --- | --- |
| [Run summary](run-summary.json) | Current source, compiler-input, artifact and tool bindings; actual analyzer completion; external raw report reference. |
| [Triage delta](triage-delta.json) | Exact versus source-range-only matches, new loop finding and revised capacity explanations. |
| [Coverage](coverage.json) | Fresh report/review hashes, complete finding coverage and old-review preservation. |
| [Matcher reuse](matcher-reuse.json) | The prior 43 matcher tests are reused only after exact current checker/test hashes match their recorded source closure. They were not rerun. |
| [Mutation checks](mutation-tests.json) | Nine fresh changes to expressions, severity, confidence, inventory, dispositions, rationale and source bindings are rejected by the unchanged checker. |

The local destination capacity race is repaired by permanent reserve-first
registration. This does not authenticate a remote reservation proof or qualify
an actual provider, backing, finality, recovery process or future destination.
The [approved-provider demonstration](../provider/receipt.json) proves that
correctly pinned source consumption can still be theft by an explicitly admitted
malicious provider. It uses real router/adapter/timelock contracts with custody
and remote-identity fixtures, not a full real migration or bridge SDK.

The review-publication preflight initially caught old references to the replaced
capacity regression. Those references and their obsolete capacity explanations
were corrected before publication; no production code or analyzer result changed.
Large raw analyzer/compiler outputs remain in the exact external directory
recorded by the run summary. Old reports keep their original source scope.

The proposed 3% aggregate migration execution-loss budget, actual conversion,
canonical ownership portability, production services/routes/gas, provider
qualification, authority choices and independent audit remain separate release
work. Zero unresolved detector entries does not establish their completion.
