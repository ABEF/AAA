# Verify earnings-history ingestion

The read-only `frontend_api.history_audit` command compares a local index with a
separately reviewed RPC provider. It checks all configured emitters, including
the seven required by [earnings replay](EARNINGS_HISTORY.md). It detects omitted,
extra or conflicting raw logs and block/cursor inconsistencies. It does not
change a database, publish financial totals, start a service or move funds.

The owning task is [financial history](../TODO.md#task-financial-history).
[Scoped evidence](../reports/history-audit/VERIFICATION.md) covers local fixtures;
actual provider/backfill qualification remains open. An agreeing RPC is another
observation, not a cryptographic proof that no event was omitted.

## Configure and run

Use the reviewed schema-2 API configuration with `history`, `earnings_history`
and every required same-chain predecessor. Fresh deployments explicitly select
accounting4/fee-intake1/canonical V5; each predecessor must use the same profile.
Explicit historical accounting3/V4 remains separate and similarly requires its
own compatible predecessors. A config version does not upgrade old deployments.
The constructor verifies that each earnings profile has all seven emitters.
The audit checks that the SQLite cursor has the
exact configured chain/start/parent/contract identity and has fully ingested the
requested window. It uses raw log fields, not cached event names or decoded data.

Create a private operator-owned audit configuration:

```json
{
  "schema": 1,
  "rpc_urls": ["https://<independently-reviewed-archive-provider>"],
  "provider_id": "second-operator",
  "independence_review_sha256": "<64 lowercase hex characters hashing your review record>"
}
```

These are deliberately unusable placeholders. Review archive support, provider
ownership/upstreams and log limits; record that evidence before supplying its
SHA-256. URLs on a primary provider's hostname are rejected, but different
hostnames and a supplied hash alone cannot prove independent infrastructure.
All configured fallback URLs must meet the same review. Keep credentials out of
Git and reports. Public output contains the provider label and review hash only.

Run from the repository root, replacing the paths, public controller and block
numbers with reviewed values:

```sh
python -m frontend_api.history_audit --config /operator/frontend-read.json --audit-rpc-config /operator/history-audit-rpc.json --controller 0xREPLACE_WITH_EPOCH_CONTROLLER --from-block 100000 --to-block 100127 --output /evidence/epoch-100000-100127.json
```

The controller selects one configured current or predecessor deployment and its
own database; it never discovers arbitrary peers. The output must be a new file
in an existing directory. Configurations, databases, SQLite sidecars and existing
receipts cannot be overwritten. Invalid configuration/output paths may produce
only a sanitized stdout error. The command requires no signer or governance role.

| Result | Meaning and operator action |
| --- | --- |
| `matched`, exit 0 | All stored headers and normalized raw logs in this window agree with the selected RPC. Preserve the receipt and proceed to the next contiguous window. |
| `mismatch`, exit 2 | Missing-from-index, absent-from-RPC or conflicting records were found. Counts and up to 20 coordinates per category are included. Neither provider is automatically declared correct. Preserve evidence and investigate. |
| `unavailable`, exit 2 | Identity, ancestry, confirmations, limits, malformed data or transport/database failure prevented comparison. Never record this as an empty or successful window. |

Each receipt binds the API configuration hash, epoch/controller, exact block
range and boundary hashes, confirmation observations, emitters, header digest
and both normalized log digests. It does not expose RPC URLs, database paths or
raw exception contents. Unknown extra RPC fields are ignored; amounts, topics,
emitter, transaction/block identity, transaction index and log index are compared.

## Coverage, limits and release use

One run handles at most **128 blocks**, **10,000 logs** and **8 MiB of normalized
log data per source**. Stored raw JSON text is capped at 65,536 characters per log
before decoding. RPC log fetches use chunks of at most 32 blocks and the existing
transport response limit.
The standard 25-second request deadline, RPC/post budgets and SQLite cancellation
remain active. Reducing the window can resolve volume/latency limits; a single
block beyond the limits requires engineering review. No truncation or ignored
window is accepted as coverage.

Before serving live history, record contiguous, non-overlapping matched windows
from each reviewed history start through that epoch's canonical retirement
cutoff or the current confirmed target. Reconcile the coverage externally; this
command does **not** aggregate receipts into a full-history certificate or verify
retirement/activation proofs. Recheck overlapping tails after a reorg, and retain
invalidated receipts as superseded evidence. The ordinary earnings endpoint still
verifies lifecycle, complete predecessor lineage, on-chain indexes and NFT
entitlement/claim/conversion reconciliation. This audit never bypasses it.

A report for a historical window is not a current balance or price quote. No USD
price is inferred, and an audit pass does not qualify a feed. Preserve the user's
current-price earnings policy: missing prices stay unavailable, conversions and
claims are not new income, and transfers preserve the NFT's earnings history.
The current release has no remote fee intake or bridge history. A custody transfer
to an external address is not a same-chain canonical handoff or proof of a later
chain's NFT/reward history.

## Database performance and recovery

The indexer now creates `block_log_lookup(chain,block_number,log_index)` on
startup. This supports ordered range comparisons without scanning unrelated log
history; it changes neither cursor identity nor stored event/accounting data.
The audit is read-only and never creates that index itself.

For an existing service, preserve the configuration and take a WAL-consistent
backup. Allow disk space and a maintenance window for the first index build,
then restart the indexer under the existing process lock with the reviewed code.
Verify its cursor and event counts are unchanged, the index exists, and normal
ingestion resumes. Large-database creation cost is not qualified by the local
fixture. Concurrent reads can be unavailable while SQLite schema work completes.

On mismatch, stop publishing the affected earnings/history data. Keep wallet
claims governed by the existing on-chain checks; do not rewrite claims or raw
logs to make reports agree. Preserve the original database, report and provider
observations, diagnose the discrepancy with reviewed independent evidence, and
backfill a separate database from the known deployment anchor. Recheck lineage,
all affected windows and earnings reconciliation before switching service traffic.
An extra database index is compatible with the prior reader; rollback of the
application does not require deleting financial history. Stop an audit with
normal process termination and rerun the unfinished window to a new report file.

This work does not deploy or restart any service, qualify a live RPC provider,
prove consensus finality, authenticate unreviewed successor economics or provide
independent production approval.
