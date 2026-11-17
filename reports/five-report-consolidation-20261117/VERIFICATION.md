# Verification and preservation

Baseline main `1c18379b03b067de722d250cee1cc173acc4d635`.

## New work only

- Two new actual pre-seal planner methods pass after the missing stop warning is
  corrected. The baseline had one meaningful warning failure and one healthy
  control pass. No calldata/settings/readiness semantics changed.
- Fifteen distinct new evidence-admission methods were observed passing at their
  explicitly recorded development stages. The initial13pass observation lacks a
  raw terminal capture; it is not fabricated. Later malformed-log/DEFLATE
  failures, corrected affected selections and raw source hashes are retained in
  [EVIDENCE_CHECKS.json](EVIDENCE_CHECKS.json).
- The actual default checker CLI admits its seven pinned historical groups,
  preserving each evidence tier and reporting zero new historical tests/EVM
  executions and `production_approved:false`.
  [Observed output](DEFAULT_ADMISSION.json).

These are17distinct new unit methods across recorded stages, not17current EVM
transactions, not78new historical executions and not a replay of prior29/80/45
suites. No unchanged full test, compiler, static, browser, fork, public-RPC or
operating campaign was rerun. [Tool stages](TOOLS_RECONCILIATION.md) and
[checker scope](EVIDENCE_ADMISSION.md) give exact limits.

## Reconciliation is not execution

[SCOPE.json](SCOPE.json) pins300old files in five families; the
[Markdown ingestion record](MARKDOWN_INGESTION.json) accounts for all37Markdown
files. Large generated method/corpus matrices are ingested as source/evidence
inventory, not claimed manual branch verification. Detailed current assessments
live in [64registry rows](RECONCILIATION.json), including both corrections made
in this consolidation. Topic-slice counts overlap and are not summed.

Current source proofs are checked against the working tree. Historical
compiler/ABI/runtime/receipt/source-stage labels remain historical. Missing raw
logs remain missing; artifact integrity is not proof that an original run
actually occurred. The maintained manifest needs explicit source review before
a new baseline can be admitted. Its Git attribute preserves exact raw manifest
bytes across checkout line-ending settings; no checksum is silently recomputed.

## Final checks

The completion record separately checks original300report hashes, protected4
dirty files, unchanged61Solidity/100normal-build sources, task-status retention,
generated function/operator/Todo references and local documentation file links.
No new normal build or Slither result is claimed for unchanged Solidity.

Exact staged and committed Python imports and publication bytes are checked
before claiming pushed. No public deployment/sealing/signing, existing Anvil or
database/journal mutation, site/service change or monitoring restart occurs.
