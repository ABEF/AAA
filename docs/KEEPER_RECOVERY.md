# Keeper outage and server recovery

Hardened keeper candidate. See [the internal review](../reports/keeper-recovery/REVIEW.md). Staging and independent approval remain required before funded operation.

See [service qualification and rehearsal](KEEPER_REHEARSALS.md) for the isolated
process-crash suite and read-only health, preflight and recovery-snapshot commands.
Actual execution evidence is kept separately from the historical internal review.

## Restart and custody

LP stays on chain. The keeper discovers the Vault's shared buckets and reads current state. A restart reconciles a pending transaction before evaluating current maintenance with fresh prices, deadlines, simulations and budgets. It does not replay missed rebalances or restore missed earnings; LP may remain out of range while offline.

The state file preserves deployment identity, next nonce, pending intent/hash, daily costs, maintenance times, discovery cursor and metadata checkpoints. Live startup refuses missing/corrupt state, an absent nonce checkpoint or an unqualified network fee policy. Used signers require a canonical confirmed receipt anchor; a later deep reorganization blocks further signing until reviewed reconciliation. Submission refuses nonce drift, unknown pending transactions and insufficient native balance. Ambiguous broadcasts never trigger blind resubmission.

## Move to a new host

1. Stop the old signer and prevent simultaneous operation. File locking only protects one host. If key confidentiality is uncertain, revoke the old keeper and authorize a fresh signer through the reviewed governance/timelock process.
2. Preserve the exact release/configuration, durable state and journal logs. Back up state off-host after changes with hashes and timestamps, and monitor backup age/failures. Secure encrypted signer material separately. Never store secrets or runtime state in Git.
3. Restore on supported Linux with restrictive permissions and reviewed RPCs. Reconcile transactions since the backup, failed-transaction gas, actual L1/L2 costs, current UTC-day budgets and both confirmed/pending nonces. A stale backup is not automatically safe.
4. Run a dry cycle. Inspect recovery/health, discovered buckets, authorized signer and deployment pins. Then resume the reviewed live service and verify canonical receipts and state progression.
5. With total state loss, stop signing. Independently reconstruct recovery records or rotate to a fresh authorized signer after reconciling the old one. Automated full reconstruction from an arbitrary lost snapshot is not provided.

An unused signer can explicitly bootstrap using `python -m keeper.monitor --config REVIEWED_CONFIG --initialize-state`. This never signs; it requires reviewed deployment pins, a fresh head and zero latest/pending nonces, and refuses existing state. Legacy state without a nonce checkpoint requires reviewed migration, never deletion or a blind nonce insertion.

## Logs, health and fallback

- JSON logs identify action, bucket and transaction where available. Errors include type and source location; raw error bodies, signer output, credentials and full tracebacks are excluded.
- Separate `health_path` defaults to the state filename with `.health.json`. It reports heartbeat time, last success, pending flag, skipped buckets and failure count. `running`, `awaiting_receipt`, `recovery_required`, `degraded`, `error` and `halted` are not successful maintenance. Dry-run success is explicitly labelled.
- Configure `receipt_fee_policy` only after qualifying the actual chain: `included` requires all gas costs in effective receipt gas accounting; `separate_l1_fee` requires an explicit L1 fee field on every receipt and a positive reviewed allowance. The example is `unverified`, which blocks live startup. An allowance is a conservative estimate, not an enforceable cap on external L1 charges.
- Reverted actions retain their gas costs and receive a durable cooldown (default one hour). Other eligible work can proceed, while repeated failures remain visible. Gas/budget rejections mark the cycle degraded.
- RPC reads have bounded retries and chain-checked endpoint fallback. Failed cycles back off. A failing bucket is logged and marked degraded while independent buckets remain checkable. Never execute with stale prices or an unreviewed chain/route as a fallback.
- Storage failures and unexpected program errors stop the loop. A failed initial health write prevents signing. The systemd unit limits restart storms and stops the keeper plus signer child processes together. Shutdown detected before intent persistence prevents a new submission; a submission already underway must finish or be reconciled from durable state. Invalid state/configuration still needs intervention.
- Monitor stale/missing heartbeats, sustained errors, long-pending/ambiguous transactions, stale heads, low balance, backup age and role/code changes from a separate host. A dead server cannot alert about itself. Configure journal retention/rotation and alert routing before launch.

<a id="rehearsals-still-required"></a>

## Recovery rehearsal scenarios

Track qualification in the [keeper recovery task](../TODO.md#task-keeper-recovery) and [guardrail task](../TODO.md#task-keeper-guardrails). These scenarios define evidence to collect; they do not reset the scoped tests and isolated rehearsals already recorded.

- Several days offline, current-state restart and claims/metadata behavior.
- Crashes around intent persistence, broadcast, receipt confirmation and final state write, with no duplicate submission.
- RPC failover, wrong chain, stale heads, malformed receipts, reorgs and incomplete fee reporting.
- Disk full, permission errors, corrupt state, stale backup and total state loss.
- New-host restoration, old-host isolation, nonce/budget reconciliation and key rotation.
- Actual Linux systemd, locking, off-host backups, monitoring and operator alert delivery.

Local tests do not establish universal recovery or production readiness.
