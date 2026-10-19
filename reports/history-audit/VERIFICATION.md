# History ingestion audit - scoped verification, 2026-10-19

**Internal development evidence; release remains NOT APPROVED.** Baseline main:
`f0932365b64d0051a27dee052877e3bacce5e921`. Git establishes publication.
No Solidity, website, server, monitor or public-chain state changed.

Implemented [read-only independent-provider comparison](../../docs/HISTORY_AUDIT.md)
for a bounded window of a configured earnings epoch. Added one SQLite index to
the existing indexer for ordered block/log queries; no accounting/event decoder,
balance, price or earnings calculation changed.

## Evidence and reuse

- [Initial run record](initial.json): 21 focused local cases passed, no failures
  or skips, in 3.555 seconds. The record preserves the source snapshot after that
  observed run and before the final CLI protection change; it is not a second run.
  The publication copy normalizes Windows line endings to LF; the original
  external record is retained and source-file hashes are unchanged.
- [Final scoped run](scoped.json), [log](scoped.log): 21 cases passed, no failures,
  errors or skips, in an isolated published-HEAD tree plus the intended delta.
  These are 18 affected existing indexer cases and three CLI cases, including the
  original error/redaction case rerun after the CLI change.
- [Source and reuse mapping](source-and-reuse.json): 20 non-CLI audit cases retain
  initial passing evidence. Every original test/helper AST body matches; the only
  changed audit function was CLI `main`. The indexer and fixture helper stayed
  byte-identical to that initial run. Together the evidence covers **41 distinct
  affected tests**, not a newly rerun 41-case suite.
- Solidity and financial replay code are unchanged. Prior earnings and wallet
  evidence retain their existing scopes; unchanged contract/earnings suites were
  not rerun. No new build/ABI or public-provider qualification is claimed.

Cases cover actual SQLite/WAL reads, omitted fee events, RPC-side omissions,
conflicting amounts/topics, malformed/removed/duplicate logs, wrong emitters,
headers/cursors/ancestry/confirmation changes, shared work limits, empty windows,
separate predecessor selection and exact 10,000-log / 128-block limits. Query-plan
inspection confirms the added index supports the ordered range scan. Reopening
an existing database adds the index without changing its cursor or stored rows.

## Internal review and limits

The tool is an operator CLI, not a public HTTP endpoint or automatic repair job.
Database reads use `mode=ro`, query-only mode, a snapshot transaction and bounded
SQLite work. RPCs use the existing read-only transport. Reports are exclusive
new-file writes; a review improvement additionally blocks database sidecar and
configuration output paths before any audit RPC. Errors do not echo credentials,
URLs or raw input. Current windows retain confirmation depth at completion;
historical observations intentionally have no live-price freshness claim.

Comparison is over raw logs and canonicalized identities, not cached decoded
labels. Every configured emitter is compared, and the constructor requires the
seven earnings emitters. Missing or conflicting records produce nonzero exit;
resource/transport/identity errors cannot produce a matched window. Mismatches
do not establish which provider is correct and never repair data automatically.

Two agreeing data sources can still share an upstream or omit the same events.
Operator review of provider independence, exact source/epoch coverage and live
archive/backfill/reorg behavior remains necessary. A window report is not a
whole-history, on-chain receipt inclusion, consensus finality, lifecycle or price
proof. Full cutover and accounting reconciliation remain with the existing
earnings API. Production-scale index-build cost and actual provider/load behavior
are still open under the [central task](../../TODO.md#task-financial-history).
