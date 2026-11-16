# Offline history backup and restore — 16 November 2026

Implemented the authorized history-recovery tool on baseline main
`06e5af2640827e6b212c8b135899f4709ea9e1ee`. It creates WAL-consistent SQLite
snapshots, verifies an externally reviewed manifest and restores into separate
new files. **Exact accounting, all retained raw history, the full24-hour window
and existing safeguards/limits remain. No operating deployment is approved.**

The new [module](../../frontend_api/history_recovery.py) and [CLI](../../scripts/history-recovery.py)
are separate from existing readers/builders. All14 checkpoint semantic sources,
the prior prefix importer and all61 Solidity files remain byte-identical.
The [single operator manual](../../docs/OPERATOR_MANUAL.md#back-up-verify-and-restore-history)
and [detailed recovery procedure](../../docs/HISTORY_RECOVERY.md) give exact inputs,
commands, verification, interruption and separately authorized adoption steps.

## Implemented behavior

| Operation | Actual behavior |
| --- | --- |
| Backup | Strict current7 API configuration is parsed with a transport that rejects every network call. Each configured epoch uses a read-only explicit SQLite snapshot and backup API. Every retained row is preserved; source Indexer startup, source SQL writes/checkpoints/journal-mode changes are never used. |
| Contents | Independent standalone databases, portable offline profile, exact optional checkpoint2/3/import-review bytes and a manifest written last. Private RPC URLs/original paths are removed from the profile; original private configuration stays external. |
| Verification | External manifest SHA is mandatory. Exact source/profile/schema/index/FK, chain/cursor, contiguous headers/times, raw-log provenance, overlapping epoch headers, stored checkpoint anchors and file hashes/inventory are checked. No data is repaired or missing income guessed zero. |
| Restore | Verify first; copy into a brand-new directory with separate inodes, streamed hashes and post-copy verification. Preserve the original manifest and publish a false-approval restore receipt last. No old directory/database/configuration/journal is replaced or service started. |
| Failure | Existing paths, aliases/reparse entries, unsupported schema, corrupt/inconsistent data, work/byte exhaustion and ambiguous inputs reject. Partial directories are retained for inspection and a fresh-path retry. A file's presence does not approve it. |

The public graph is the reviewed configuration's deployment/history identity,
not a new on-chain attestation. Per-database snapshots are not one globally atomic
graph; overlapping-header checks detect contradictions but cannot prove finality
or complete ingestion. All returned approval/install/readiness flags stay false.
Actual canonical RPC/history admission and separately approved service adoption
remain necessary. A valid empty initialized database remains empty/unverified;
it does not become zero earnings or complete history.

Existing checkpoint age admission still requires86,400 chain-timestamp seconds
before a requested snapshot and a complete raw suffix. Exact checkpoint bytes
retain whole-unit LP trees, pending/high-low phase/direct credits, royalty tickets
and local payout histories. No financial replay source, share, reward allocation,
currency, principal or claim permission changes. The tool retains older raw prefix
rows as well; replay `max_events` is not repurposed as a lifetime-storage cap.

Offline defaults remain the existing60-second build budget; explicit time remains
1–3600seconds and nested work cannot reset an outer bound. The new total package
byte allowance defaults1GiB, engineering ceiling1TiB, enforced before writes.
JSON metadata has1MiB bounds; the existing checkpoint bound stays32MiB.
API/RPC/event/graph/currency/codec limits are not increased. A near-cap restored
package can require a larger deliberate allowance for its added receipt.

## Findings corrected during implementation

| ID | Finding and correction | Evidence |
| --- | --- | --- |
| HR1 | Initial database-only budgeting could write checkpoint/profile/review bytes beyond the allowance before rejecting. Reserve artifact lengths before copying; check manifest and restore receipt totals before publication. | New baseline regression observed341,017bytes versus323,915limit, then passes after correction. |
| HR2 | Initial optional import-review admission checked only selected fields; edited deadlines/counts/producer grammar could accompany the exact checkpoint. Reuse the unchanged source-pinned importer's full binding validator and validate original producer key/hash shape. | Three detached-field subcases reproduce acceptance, then reject correctly. Original reviewed producer hashes remain provenance, not adopted executable code. |
| HR3 | Standard argument parsing echoed mistakenly supplied credential-like values before normal error handling. Add a fixed-message parser, fixed program label and inherited safe subparsers. | Fake-only unknown argument/action and invalid integer values reproduce disclosure; all four reject without echo after correction, with a valid command control. |
| HR4 | Crash/source-rotation hardening needed parent-directory synchronization and source inode checks. Synchronize POSIX output parents/directories and detect source replacement around copying, while permitting legitimate concurrent writes. | Independent source review and existing concurrent-writer/alias/partial-output checks; actual POSIX power-loss/host behavior remains unqualified. |
| HR5 | Mutable caller configuration and ordinary Boolean/numeric equality were avoidable provenance ambiguity. Freeze the input object and use tagged exact cursor identity comparison. | Source-reviewed hardening; standard immutable graph/source and corruption checks remain. No pinned reader was edited. |

Database files are opened read-only, but ordinary SQLite WAL/SHM lock bookkeeping
can occur, and legitimate writers can advance their own database. Do not infer
byte-identical sidecars or that a long read has no operational resource cost.
Only fresh destination copies are normalized to standalone DELETE-journal mode;
logical rows are preserved while their physical header can differ from a WAL source.

## Verification and preservation

**50 distinct new methods have passing composed evidence:31 recovery methods and
19 CLI methods.** No unchanged suite/test body, compiler/static/EVM/browser run,
public RPC probe, signing or existing-chain rehearsal was executed. New fixture
helpers reuse earlier controlled sources without selecting their test methods.

The31 recovery methods exercise real SQLite/WAL and unchanged readers/replay,
with controlled lifecycle/getter/RPC observations. Coverage includes committed
versus uncommitted writes, a concurrent second writer after snapshot pinning,
all epochs/full rows, exact checkpoint2/3/import-review bytes, exact NFT/collection/
wallet all-time and full24h reporting, empty coverage, source preservation,
corruption, schema/identity mismatches, aliases, bounds and partial outputs.
Actual NTFS hardlinks are checked; symlink/reparse refusal uses portable injected
metadata, not a claim of privileged Windows symlink or actual Unix qualification.

CLI tests inject operations and verify the real parser, strict inputs, shared
budgets, dispatch and sanitized error contracts. The final parser change is
isolated from the unchanged core module; earlier18 method/helper bodies remain
AST-bound, and only the new parser method is executed after that change. This is
not a fresh all50 run. Initial test-harness failures and real source defects are
preserved with exact stage/source/case pins in [verification](VERIFICATION.md).

Hash-only preservation verifies all14 semantic files,61 Solidity sources,
6230 earlier report files and738 existing Python files (excluding the protected
dirty files). All four unrelated dirty files remain exact and unpublished.
Original documentation was archived outside Git before editing. No original
database, journal, Anvil state, NFT/LP/balance, website/signer/public null config,
service or user-paused heartbeat was acted on.

## Remaining obligations

The [financial-history](../../TODO.md#task-financial-history) and
[hosting](../../TODO.md#task-host-services) tasks remain In progress for actual
archive completeness, canonical provider behavior, maximum-state/lifetime
workloads, storage/off-host/host recovery and approved integration. Independent
audit and release approval remain separate.

This tool requires owner-controlled filesystem paths and a qualified SQLite/host
runtime. It does not defeat a hostile OS administrator or manufacture history
missing before capture. Current evidence uses SQLite3.53.1; another runtime and
its vendor's WAL fixes require review. Runtime versions are recorded in each bundle.

The design uses official [SQLite backup guidance](https://www.sqlite.org/backup.html),
[WAL documentation](https://www.sqlite.org/wal.html) and
[Python's backup interface](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).
The complete [evidence inventory](EVIDENCE.json) retains all source stages and
failures losslessly; tool source publication is neither live adoption nor deployment.
