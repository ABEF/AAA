# Earnings longevity: implementation scope and review

Baseline main096fd2b. Preserve all existing contracts, economic rights, profiles,
services, journals, signing restrictions and unrelated dirty files. This is a
backend source improvement, not installation or production acceptance.

## Evidence and design

History.read validates deployment-to-target raw SQLite history and Earnings
replays seven emitters for each request. Streaming fixes memory materialization,
not lifetime replay CPU/event bounds. There is no trusted persistent earnings
checkpoint today. A plain cached total would lose fractions/cohorts/provenance.

Implement an explicit opt-in, source/configuration-bound immutable checkpoint
for the single-deployment earnings path. Its SHA-256 must be pinned in reviewed
API configuration; never automatically trust the file's own hash or advertise a
checksum as a log-completeness proof. Preserve raw history and the existing
operator/provider trust boundary. No pruning or mutable unsigned cache.

- Save exact ownership/claims/conversions plus full replay denominators/indexes,
  incumbent dust/cohorts and all NFT fractional earnings. No USD values stored.
- Build/advance with validated complete-block raw replay and pinned on-chain
  reconciliation, writing an exclusive candidate artifact only after success.
- Serve from the pinned checkpoint plus a bounded suffix, checking its canonical
  block and SQLite identity/ancestry, runtime bindings and current ledger state.
  Reorg across the checkpoint is unavailable until reviewed rebuild/re-pin.
- A served earnings checkpoint must be at least24hours old: the entire rolling
  day is replayed from raw suffix events. This avoids guessed day buckets and
  preserves exact boundary/fraction timing. Too-recent checkpoints fail explicitly.
- Existing request event/deadline/RPC budgets remain. Old checkpoints can become
  too expensive; the operator advances them. Do not truncate or raise limits.
- Initial profile rejects predecessor/canonical replacement use. Existing full
  lineage replay remains explicit; automatic lineage checkpoint continuation,
  unattended approval/rotation and raw-history pruning remain separate work.

## Critical review one: financial correctness

Carry exact per-NFT scaled earnings, not only rounded totals. Claims/conversions
are not income. Checkpoint at full block boundaries only; fee-credit pairs and
deferred royalty recovery cannot be left open. Preserve owner identity/current
ownership semantics, separate source currencies, all-time vs claimable totals,
collection80/10/5/5 allocations and quarantines. Enforce original source identity
and snapshot anchors; unrecognized versions/schemas fail closed.

## Critical review two: availability and verification

Pin external approval in config; use strict bounded JSON, no pickle/dynamic
objects. Preserve raw SQLite evidence, read-only snapshots and cross-prefix
transaction-identity checks through the existing primary-key index. No API
request creates/reviews a checkpoint. Independent stored-source reconciliation,
restart, changed-file/hash, suffix reorg, anchor reorg, stale/too-new checkpoint,
concurrent ingestion, partial publication and old source/profile tests are
required. Compare seeded output to full replay and independent accounting
assertions; do not repeat unchanged contract suites.

OpenSea research proceeds independently using official documentation and actual
interface/source. Record exact incompatibilities and a bounded implementation
boundary; do not invent Robinhood deployment/fee acceptance or add mint powers
before the marketplace caller/payment design is qualified.
