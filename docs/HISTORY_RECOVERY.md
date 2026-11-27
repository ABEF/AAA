# Offline history backup and restore

This tool snapshots and verifies current **accounting7** earnings/indexer history,
including all configured same-chain predecessors. It writes only to a brand-new
output directory. Existing databases, private configuration, checkpoints, journals,
services, contracts and NFT economic rights are not replaced or adopted.

Use the maintained [operator procedure](OPERATOR_MANUAL.md#back-up-verify-and-restore-history).
The [financial-history](../TODO.md#task-financial-history) and [hosting](../TODO.md#task-host-services)
tasks still own actual archive, storage, off-host and operating qualification.
Source capability is not production approval.

## Contents and trust

The bundle contains:

- A standalone SQLite snapshot for **every** configured epoch, retaining every
  stored block and log, including optional decoded labels. Those labels remain
  nonauthoritative; no row is filtered by an event label or settlement currency.
- A portable `profile.json` derived from the strictly validated API configuration.
  RPC URLs become `https://offline.invalid`; original database/checkpoint paths
  become generated relative paths. Private configuration is not packaged.
- The exact reviewed checkpoint2 or3 bytes, when configured. Raw LP trees,
  pending/high/low phase/direct credits, royalty tickets and local payout books
  are not flattened or reallocated. A supplied, separately pinned prefix-import
  review is preserved byte-for-byte and checked against that checkpoint.
- `manifest.json`, written last, with payload hashes/sizes, public graph and
  per-database anchors/counts, semantic/producer pins, runtime versions and false
  approval/install/readiness flags. Its original configuration SHA is the API's
  identity hash (excluding RPC URLs), **not** the raw configuration-file hash.

The supplied review's original producer hashes are provenance, not adoption of
older code. Its complete graph/anchor/cursor/time claims are bound using the
source-pinned import validator. A changed pinned semantic source still rejects;
there is no source-hash override. Retain the matching reviewed tool release and
prior approval/raw-history evidence separately.

SQLite's backup mechanism includes committed WAL data and excludes uncommitted
transactions. Each source connection is read-only with an explicit snapshot;
the tool performs no source SQL writes, schema setup, journal-mode change,
WAL checkpoint or WAL deletion. Normal SQLite shared-memory/lock bookkeeping can
occur. Legitimate concurrent writers can continue changing their own databases;
the captured snapshot remains separate. Long readers can temporarily retain WAL
pages, so use bounded jobs on qualified storage.

Each database is captured independently: **the graph is not one atomic snapshot**.
The tool rejects contradictory overlapping stored headers and checks every stored
checkpoint anchor in its corresponding snapshot. These checks do not establish
RPC authenticity, consensus/finality or complete ingestion. An empty initialized
database is backed up as empty; it is never represented as complete live history.
Missing required deployment/checkpoint coverage fails.

## Full 24-hour window and limits

All retained raw history is copied, including the checkpoint prefix and recent
suffix. Nothing is pruned to a rolling-day boundary. The ordinary earnings
consumer still requires a checkpoint at least **86,400 chain-timestamp seconds**
before the requested snapshot and replays the entire raw day. The tool neither
declares serving eligibility nor substitutes cached day totals. This is unrelated
to the separate one-hour royalty-launch window.

Existing API/RPC/replay/event/graph/currency/codec/accounting limits stay unchanged.
The replay `max_events` limit is not a lifetime backup-storage cap: a checkpointed
database may retain more historical rows, and the backup copies them all.

All three subcommands use a shared offline deadline, default60 seconds, existing
offline range1–3600 via `--max-seconds`. Nested work cannot reset an outer budget.
`--max-bytes` defaults to1,073,741,824 bytes (1GiB), with a1TiB engineering maximum.
It bounds package writes, including the manifest and a new restore receipt.
Restoring a package near its original cap can require a larger explicit restore
allowance for that receipt. It does not change an API/on-chain limit or approve
large workloads. Config/profile/manifest/review/receipt JSON is bounded to1MiB
each; the existing checkpoint limit remains32MiB. Busy SQLite, disk/permission
errors and expired work fail; filesystem calls are not guaranteed instantly
interruptible.

## Prepare a backup

Prerequisites: a reviewed current API configuration with complete earnings/history
profiles, owner-controlled existing input/output-parent directories, consistent
source identities and a qualified local SQLite/filesystem runtime. No wallet or
RPC key is needed by the operation. The private API configuration may contain RPC
credentials, but they are validated locally, never contacted or copied.

From the repository root, replace every path placeholder:

```sh
python scripts/history-recovery.py backup --config /secure/reviewed-api.json --output /archive/history-NEW
```

If the configured checkpoint came from prefix import, include its reviewed
sidecar and the externally reviewed digest:

```sh
python scripts/history-recovery.py backup --config /secure/reviewed-api.json --review /archive/import-review.json --review-sha256 REVIEWED_64_LOWERCASE_HEX_DIGEST --output /archive/history-NEW
```

The two review arguments must appear together. SHA-256 values have64 lowercase
hex characters without `0x`; they are file pins, not on-chain `reviewHash` values.
The output directory must not exist, even if empty. Parents must already exist;
linked/reparse paths, database aliases and unexpected schema objects reject.
The tool validates exact current table/index/FK layout, database identity,
contiguous ancestry/timestamps, raw-log provenance and payload integrity. It
does not recompute or modify claims on-chain.

Store the printed **manifest SHA-256 independently** after reviewing the bundle
and original evidence. A digest supplied by an untrusted bundle does not approve
that bundle. Keep private configuration/credentials, any signing material and
earlier artifacts in separately secured backups; do not put them in Git or infer
they are included here.

## Verify and restore

Verify a copied/off-host-returned sealed bundle without network calls:

```sh
python scripts/history-recovery.py verify --bundle /archive/history-REVIEWED --manifest-sha256 REVIEWED_MANIFEST_SHA256
```

The externally supplied digest is required. Verification rejects missing/changed
payloads, source/profile/graph mismatches, path traversal, aliases, unexpected
WAL/SHM or other entries and malformed restore receipts. It is integrity and
profile verification, not approval of historical completeness or current prices.

Restore into another brand-new directory:

```sh
python scripts/history-recovery.py restore --bundle /archive/history-REVIEWED --manifest-sha256 REVIEWED_MANIFEST_SHA256 --output /recovery/history-NEW
```

Restore first verifies the source, copies into separate new files (never hardlinks),
checks streamed hashes and verifies the restored package. It preserves the original
manifest and writes a false-approval `restore.json` receipt last. The printed
restore-receipt SHA differs from the original manifest SHA; use the **original
manifest SHA** for `verify` on the fresh restored package. Restoring inside the
source bundle, overwriting an existing directory or deleting/reusing partial
outputs is forbidden. Once a writer legitimately advances a restored database,
it is a working database rather than an unchanged sealed backup.

No API config is installed, indexer started, service restarted or heartbeat
resumed. The generated relative profile is deliberately offline. Independently
review absolute database/checkpoint paths and actual private RPC configuration,
then use a separately authorized matching-service rollout. Path remapping changes
the API configuration identity; it does not authorize relabeling checkpoint
deployment/history identity, runtimes, semantic source pins or old journals.
Before hosting, run the unchanged canonical RPC/history admission and verify
complete raw coverage, earnings/ownership/claim reporting and the full24-hour day.

## Interruption and recovery

| Condition | Required action |
| --- | --- |
| Backup interrupted, bound exceeded or source replaced | Preserve originals and partial directory. A missing manifest is incomplete. Inspect evidence; retry with a new path and deliberately reviewed allowance if needed. |
| Restore interrupted or receipt missing | Preserve both source and partial copy. Do not install it automatically. Verify provenance/contents and repeat into a fresh directory after resolving the cause. |
| Manifest present after a late error | Presence alone is insufficient. Verify the independently reviewed digest and every payload; approval/adoption remain separate. |
| Source databases disagree after reorg/backfill | Preserve the contradictory histories; reconcile through the established indexer/canonical procedure. Do not edit hashes, drop rows or mix arbitrary backups to force success. |
| Semantic/tool version changed | Use the matching independently reviewed release, or perform a separately reviewed compatibility/rebuild process. Never replace saved source hashes to pass. |
| Busy source, permission or storage fault | Resolve the qualified filesystem/runtime condition. No force checkpoint, unsafe main-file-only copy, schema repair or raised public limit is used as fallback. |

Files are created exclusively and synchronized; POSIX parent directories are
synchronized at publication. Windows ACL/power-loss behavior, actual Unix storage,
off-host transfer/encryption, loss of a host, maximal history and restore/operating
acceptance remain separate qualification. SQLite version is recorded; assess the
vendor's current WAL fixes before choosing another host runtime. The local source
evidence uses SQLite3.53.1 and does not approve an older runtime by analogy.

The design follows the official [SQLite backup API](https://www.sqlite.org/backup.html),
[WAL behavior](https://www.sqlite.org/wal.html) and [Python backup interface](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).
The [source-scoped report](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/history-recovery-20261116/REVIEW.md) separates
new focused checks from reused semantic code and remaining operating obligations.

## Controlled collection-scale evidence

The [1,000-NFT rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/history-scale-rehearsal-20261116/REVIEW.md)
passes exact checkpoint2-to-3 prefix import, backup/verification/new-file restore,
independent whole-unit accounting and complete per-copy wallet coverage. It spans
three controlled deployments, 900 active/100 dormant NFTs, 7,757 raw logs and
346,800 chain seconds, including receipts before/at/after the day's exclusive
lower boundary. Nonzero high/low LP allocation phase is retained.

The original default 4,096-read refusal is retained; positive offline build/import
uses explicit existing 65,536-call settings under the unchanged 60-second deadline.
HTTP defaults, 16-NFT chunks, 32MiB checkpoint, codec/event/graph/currency bounds
and recovery defaults remain unchanged. The rehearsal uses synthetic chain,
getter and lifecycle observations; local timing excludes real-provider posts,
network latency and complete admission cost. It does not qualify maximum lifetime
history, all currencies/buckets/epochs, Unix/off-host restore or deployment.
See the [operator procedure](OPERATOR_MANUAL.md#collection-scale-history-rehearsal).
