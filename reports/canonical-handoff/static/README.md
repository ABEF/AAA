# Canonical handoff static analysis and internal review

Slither 0.11.6 analyzed the complete current normal production compilation:
39 Solidity source files, typed AST and artifact bytecode were checked before
execution. [Execution provenance](execution.json) records unchanged source hashes
and the raw analyzer hash. No compilation was delegated to the analyzer.

All 374 findings have [individual internal dispositions](slither-review.json):
153 false positives, 75 accepted risks and 146 informational. Coverage passes;
[10 mutations of the actual report/review](coverage-mutations.json) are rejected,
including a changed settlement finding, source drift and a missing disposition.
This is review coverage, not proof of exploit absence or independent audit approval.

Twenty supported reentrancy entries retain the existing strict write-bundle
comparison for platform-dependent Slither grouping. The [current-data check](regrouping-check.json)
accepts the same exact write multiset regrouped into 390 findings and rejects a
missing write. Call contexts, nested edges and multiplicities are preserved; the
matcher itself was not changed.

Review scope includes canonical lifecycle authority, exact record provenance,
backing transfers and abort restoration, inherited NFT inventory and reward
rights, prefunds, late receipts and onward migrations. Each reported finding
has a source-specific disposition, with accepted risks distinguished from false
positives. Those risks include admitted dependency liveness, governance-approved
replacement code, bounded-loop costs, oracle assumptions and operational/finality
qualification. The previous canonical review is preserved byte-for-byte at
[migration safety](../../migration-safety/static-analysis/slither-review.json).

The final settlement delta was reviewed against the earlier development analyzer
snapshot: 358 findings retained their detector bodies except source lines; the
remaining 16 entries were explicitly reviewed, including the new ordered
settlement entrypoint and source capture changes. Repeated expressions at distinct
locations retain distinct fingerprints. The unchanged matcher test suite was not
rerun merely to increase counts; current-data coverage and mutation checks were.

The raw analyzer JSON and full typed compiler output are retained in the external
`handoff-20261017/static-analysis-settlement` evidence directory; their hashes are
recorded here. Historical reports are unchanged. Release approval remains open.
