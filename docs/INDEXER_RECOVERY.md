# Indexer history and reorganization recovery

The SQLite indexer is an operator-maintained event cache, not custody or an
independent proof of complete blockchain history. Its cursor, exact deployment
contract list, creation/start block and original parent hash identify one history.
The [confirmed-history API](FRONTEND_HISTORY.md) must keep unavailable or
incomplete history distinct from zero balances and zero earnings.

Use exact emitter inventories for the selected deployment profile, not familiar
token names or an old Anvil manifest. Earnings needs all seven reviewed emitters
from creation. Accounting3/canonical V4 and historical codecs remain distinct;
adding emitters or changing profiles is not a cursor-only edit. Backfill and
verify a separate database before switching consumers.

The shared read-only RPC client refuses HTTP redirects, including redirects on
the same host. Endpoint rotation uses only the configured reviewed URL list and
rechecks the chain ID. If a provider changes its address, review and configure
the direct HTTPS endpoint explicitly; do not enable redirect following or an
insecure fallback to restore service.

## Routine operation

Use one writer under the existing process lock. Keep the reviewed chain ID,
contract inventory, confirmation count, start parent and maximum reorganization
depth fixed. A normal unchanged indexed tip needs one header lookup. A proved
one-block reorganization needs three: changed tip, common ancestor and a fresh
check of that ancestor before the database transaction.

An unavailable RPC header is **not evidence of a reorganization**. Header reads
must return the exact requested block number, canonical quantities, a nonzero
block hash and a valid parent hash. Reconciliation proves contiguous ancestry
without writing. Only then can one atomic transaction remove orphaned blocks
and their logs and rewind the cursor. A rollback reaching the configured start
also needs its original explicit parent anchor; a changed genesis or an
unproved ancestor requires operator review.

## Failure response

The process emits `indexer_error` with an exception type. Locally generated
safety failures additionally expose a fixed `reason`, without RPC URLs,
credentials or provider response bodies:

| Reason | Meaning and operator action |
| --- | --- |
| `invalid_log` | A confirmed log has malformed or inconsistent provenance, topics, data or bounds. The new batch and cursor are not committed. Preserve the response/range, deployment anchors and consistent database backup; compare a reviewed provider. |
| `duplicate_log` | A batch repeats a block/log position or a transaction hash crosses block identities in the batch or stored history. Preserve evidence; do not delete rows or advance the cursor manually. |
| `header_unavailable` | The provider cannot supply a required header. Retain the database and retry a reviewed endpoint with the required history. Check node synchronization, archive availability and provider limits. |
| `invalid_header` / `inconsistent_header` | A header is malformed, misnumbered or supplies different metadata for the same hash. Preserve evidence and compare an independently reviewed provider. |
| `unstable_ancestry` | Reads did not describe a stable contiguous chain. Retry after the reviewed confirmation boundary settles; persistent disagreement needs provider/finality review. |
| `reorg_depth` / `unproved_ancestor` | No common ancestor was proved inside the configured boundary. Preserve the original database, configuration and observations; investigate chain identity and finality before approving a separate rebuild. |
| `database_boundary` / `database_changed` | Stored blocks/cursor are inconsistent or another writer changed them. Stop competing writers and inspect a consistent backup. Do not edit rows or guess a cursor. |

Rejected log batches do not commit new logs or advance the cursor. A separately
proved bounded reorganization can already have been rolled back before batch
validation; that rollback retains its independent ancestry checks. Header and
ancestry safety failures preserve the existing logical blocks, logs and cursor. They do
not make stale history current: keep affected API/history responses unavailable
until complete confirmed coverage is verified. Generic RPC/transport failures
retain sanitized exception-type logging; consult restricted operator telemetry
without putting endpoint secrets into public logs.

## Backup, rebuild and restart

1. Preserve the original configuration and deployment anchors, code revision,
   sanitized failure reason, observation time and last indexed block/hash.
2. Take a consistent SQLite backup using its backup API, or stop the writer and
   preserve the database with its required WAL state. Copying a live `.sqlite`
   file alone is not a consistent backup procedure.
3. If retrying a healthy reviewed endpoint recovers the exact same chain and
   configuration, restart the one writer with the preserved database. A bounded
   proved shallow reorganization is handled automatically; downtime does not
   require resetting the cursor.
4. When a full rebuild is justified, use a **separate database** with reviewed
   creation/start/parent/emitter identity. Keep the original and its evidence.
   Do not weaken the confirmation or reorganization bound merely to suppress an
   unexplained error.
5. Before serving rebuilt history, verify complete contiguous coverage through
   the API's exact confirmed target, raw-event projections, ownership and
   LP/royalty accounting. Use the [independent-provider comparison](HISTORY_AUDIT.md)
   and [history limitations](FRONTEND_HISTORY.md). Switch service configuration
   only after that review.

This runbook authorizes no production service restart, database repair,
transaction, signer use or custody action. Actual provider behavior, Linux
operations, backups and production recovery rehearsals remain release work.
