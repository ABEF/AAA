# Keeper outage and server recovery

Operating runbook for an **undeployed candidate; production NOT APPROVED**.
Use the [rehearsal guide](KEEPER_REHEARSALS.md) for commands and evidence, the
[keeper internal review](../reports/keeper-recovery/REVIEW.md) for its original
scope, and the [central Todo](../TODO.md#task-keeper-recovery) for remaining work.

## Deployment and journal identity

Current configuration explicitly selects `accounting_version: 4` and
`fee_intake_version: 1`, the exact chain/deployment identity, real Vault/Fees
addresses and independently reviewed deployed runtimes in `code_hashes`.
A compiler template is not a deployed runtime pin. Verify actual version getters
before new work; pending receipt recovery always runs first.

Current Positions have eight local words and terminal Exited5 in addition to
Dormant3/Parked4; only Active1 before collective exit runs ordinary LP upkeep.
Accounting1/2 retain their
original fifteen-word rows/status meanings (historical Remote3 is not Dormant3).
A missing version in an old journal means legacy1, not current support. A mismatch
stops without rewriting pending hashes, nonces, costs or receipts. Restore the
original matching release/profile; never upgrade a journal by editing its version.
Accounting3 retains its original local codec and journal, without terminal
holder-exit interpretation. The new blocked
[holder-exit example](../keeper/config.holder-exit.example.json) uses distinct
`keeper-holder-exit-v4-lp-only` paths. It requires `contracts.principal_exit` and
independently reviewed `code_hashes.access` / `code_hashes.principal_exit`, in
addition to Vault/Fees pins. No example upgrades an installed service.

For accounting4, verify `CUSTODY_VERSION()==3`, the fixed Migration/module/access
binding, and consistent `Access.lpExitStarted()` / `Migration.exitPhase()`.
Recovery of an already-saved transaction remains first. Once exit starts, the
keeper schedules no range change, rebalance, compound or standalone harvest,
even after ordinary unpause. It may still process previously earned LP/royalty
conversion and separately configured buyback reserves while ordinary controls
permit. Governance alone starts exit and closes every funded bucket. The optional
`principal_distribution` worker then allocates and directly delivers principal
in bounded batches, including while paused; it never initiates or closes LP.
It is disabled by default and is not enabled on any installed service here.
Never restart LP as a recovery shortcut: retirement is irreversible. Metadata
profile4 accepts terminal stage4; old metadata journals cannot be relabeled.

### Optional automatic principal delivery

For a reviewed accounting4 deployment, replace the disabled object in the keeper
configuration with the following complete object, using the actual NFT runtime:

```json
{
  "principal_distribution": {
    "enabled": true,
    "batch_size": 32,
    "nft": {"address": "0x<reviewed NFT address>", "code_hash": "0x<runtime keccak256>"}
  }
}
```

The worker checks NFT runtime, Access owner/module binding, frozen minted count
(at most1000), allocation cursor and ordinal identity. Phase2 submits only
`allocatePrincipal(batch_size)`; Ready3 scans at most32 ordinals and submits
`distributePrincipal(ids)` for unpaid nonzero allocations. Recipients and amounts
are fixed on-chain by current NFT ownership, not supplied by keeper configuration.
The ordinary signer, simulation, nonce/receipt journal and transaction/day/gas
budgets apply; no new key or signing path exists. Normal holders need no action
or payout gas. A rejecting receiver is retried on a later rotation and retains
exceptional owner fallback; payment cannot be forced into every contract.

The saved `principal_distribution_cursor` is scan progress, never a paid marker.
It is persisted before submission; every rotation rereads actual ledger paid
flags, including deferred recipients. Recovery of pending hashes precedes job
configuration/scheduling. A bad newly added job cannot bypass or erase an old
pending transaction. Do not delete a journal or reset its cursor to manufacture
completion. Actual source/unit rollout, gas economics, backlog/deferral alerts,
outage/restart and full1000-NFT delivery remain production qualification tasks.

The ordinary configured poll interval and confirmation depth apply: allocation
and payout use multiple transactions, with only one saved pending action at a
time. At32NFTs per batch,1000NFTs need many cycles; do not promise immediate or
same-block distribution. Review `interval_seconds`, confirmations and gas/tx/day
budgets for a deliberate service rollout/restart without silently changing an
existing schedule. Once the pinned module reports both `remainingETH()` and
`remainingZZZ()` zero, the worker stops rescanning the paid inventory. NFT pins,
a funded limited keeper wallet and actual service/operating qualification are
required before enabling this source-only job.

Native compound/buyback jobs use currency zero and zero user call value: Fees
funds its classified reserve. Native venue fees need no conversion; a separate
explicit non-native conversion worker retains its own binding/routes/cap.

The desktop chat monitor is **paused by the user's 2026-10-17 instruction**.
Historical observations provide no coverage after that pause and no proof of
continuous server uptime. Pausing it did not itself stop the staging services.
Do not resume monitoring or administer those services without authorization.

## Restart and custody

LP stays on chain. The keeper discovers the Vault's shared buckets and reads current state. A restart reconciles a pending transaction before evaluating current maintenance with fresh prices, deadlines, simulations and budgets. It does not replay missed rebalances or restore missed earnings; LP may remain out of range while offline.

The state file preserves deployment identity, next nonce, pending intent/hash, daily costs, maintenance times, discovery cursor and metadata checkpoints. Live startup refuses missing/corrupt state, an absent nonce checkpoint or an unqualified network fee policy. Used signers require a canonical confirmed receipt anchor; a later deep reorganization blocks further signing until reviewed reconciliation. Submission refuses nonce drift, unknown pending transactions and insufficient native balance. Ambiguous broadcasts never trigger blind resubmission.

## Stalled RPC and progress watchdog

A peer can trickle HTTP headers/body, or DNS can stall, beyond urllib's socket
inactivity timeout. Without an outer supervisor, retries cannot begin until
that call returns. API workers have a separate killable30second deadline; a
standalone keeper command does not. A stale health alert alone cannot interrupt
blocked I/O.

The reviewed source [unit](../keeper/zzz-keeper.service) sets
`WatchdogSec=120s`, `NotifyAccess=main`, `WatchdogSignal=SIGKILL`,
`KillMode=control-group`, `SendSIGKILL=yes`, `FinalKillSignal=SIGKILL` and
`LimitCORE=0`. Main progress notifications bracket startup/cycles, follow
completed RPC and cover intentional polling sleep; there is no timer thread.
A stuck read/signer cannot keep reporting progress. Default notification cadence
is at most10seconds, leaving margin for the existing90second signer timeout.
A progressing cycle may legitimately exceed120seconds.

Before a separately authorized rollout:

1. Stop/fence the old service/signer and preserve exact source/configuration,
   pending journal, backups and loaded unit/drop-ins. Never edit a saved nonce,
   pending hash, fee review or cost record to make restart pass.
2. Review matching source/unit, systemd>=240 and all effective overrides. The
   following are read-only inspection commands for the target host:

   ```sh
   systemd --version
   systemd-analyze verify /etc/systemd/system/zzz-keeper.service
   systemctl show zzz-keeper.service -p WatchdogUSec -p WatchdogSignal -p NotifyAccess -p KillMode -p SendSIGKILL -p FinalKillSignal -p LimitCORE -p WatchdogTimestampMonotonic
   ```

   Require the reviewed120second timeout, main-process notification, group
   termination, SIGKILL (signal9), no core dumps and advancing accepted timestamps.
   Older managers can ignore unsupported options; warnings or ignored settings
   block qualification. Review manual timeout changes against maximum legitimate
   uninterrupted work plus notification gap; do not blindly shorten the value.
3. Rehearse with isolated inert operations on that exact Linux host: stalled DNS,
   continuously trickled headers/body and interrupted signer. Verify systemd
   terminates every service/signer descendant before restart, releases the old
   lock and never overlaps another keeper. Local Python mocks/unit text do not
   prove actual cgroup cleanup or manager behavior.
4. Verify restart reads the intact journal. A saved hash is checked at that hash;
   a hashless intent remains ambiguous and blocks new submissions. The old signer
   may have broadcast just before termination: use exact reviewed transaction
   identity/nonce evidence and `--resolve-pending` as appropriate. Never resend,
   replace, delete pending state or reset budgets automatically. Repeated failure
   may hit the existing service start limit and require operator review.
5. Keep independent off-host stale/degraded/pending alerts. The desktop staging
   monitor remains paused; source watchdog support neither resumes it nor proves
   uninterrupted uptime. For rollback, stop/fence, restore the reviewed matching
   source/unit pair and inspect effective settings with the same journal intact.

Notifications carry only fixed bytes; systemd environment fields are consumed
before signer children start. This adds no financial capability or journal
migration. With no configured watchdog, existing one-shot/init/resolve/standalone
behavior remains. Live code/unit deployment and real kill/recovery qualification
are separate approvals. [Internal evidence](../reports/system-adversarial-20261026/WATCHDOG.md).

## Fee-review upgrades and legacy pending intents

The current keeper writes `pending.fee_review` schema 1 before invoking its signer.
It captures exact gas limit, maximum fee per gas, L1 allowance, maximum total
cost and `included`/`separate_l1_fee` semantics. Signed transaction gas/cap/chain
must match. For type 2, use signed fee caps plus canonical inclusion-block base
fee to derive spend; the provider's reported effective price is separate evidence.
The signer selects priority within the maximum, not a separately reviewed fixed
priority. Failed transactions consume gas; reverted native value is not spent.

Before upgrading a keeper that may have pending work:

1. Stop and fence the old signer. Preserve release/configuration, state, private
   backups and sanitized logs. Do not alter existing chain/NFT/LP state.
2. Inspect the exact pending hash/nonce and canonical receipt using reviewed
   nodes. An old journal without `fee_review` is loaded unchanged, but automatic
   reconciliation cannot invent the missing review from current configuration.
   Once receipt/candidate verification reaches that check it emits the sanitized
   `pending_fee_review_required` event; absent hashes/receipts can first report
   ordinary ambiguous/pending status. All pending states block new submissions.
3. Recover original transaction-review evidence, signed gas/cap fields and the
   chain's complete fee semantics. Reconcile inclusion-day spend and reverted
   transactions. A larger actual L1 charge is already paid: refusal prevents
   further automated work, not that historical fee. Archive the discrepancy.
4. If the original review cannot be established, use independently reviewed
   manual reconciliation or signer rotation. There is no automatic legacy-budget
   migration. Never guess a review, delete a journal, reset budgets, drop/replace
   a transaction or resend to make readiness pass.
5. Verify the matching accounting-version getter, runtime/role/chain pins and
   both nonces, then dry-run before resuming a separately authorized live service.
   A preflight result is supplied-evidence consistency, not release approval.

Current configuration changes apply to new work. They do not reinterpret pending
review limits. The [internal audit and scoped checks](../reports/preproduction-audit-20261025/services/REVIEW.md)
do not upgrade any running service or journal. Stage this procedure on Linux and
the actual chain fee model before production.

## Move to a new host

1. Stop the old signer and prevent simultaneous operation. File locking only protects one host. If key confidentiality is uncertain, revoke the old keeper and authorize a fresh signer through the reviewed immediate governance process.
2. Preserve the exact release/configuration, durable state and journal logs. Back up state off-host after changes with hashes and timestamps, and monitor backup age/failures. Secure encrypted signer material separately. Never store secrets or runtime state in Git.
3. Restore on supported Linux with restrictive permissions and reviewed RPCs. Reconcile transactions since the backup, failed-transaction gas, actual L1/L2 costs, current UTC-day budgets and both confirmed/pending nonces. A stale backup is not automatically safe.
4. Run a dry cycle. Inspect recovery/health, discovered buckets, authorized signer and deployment pins. Then resume the reviewed live service and verify canonical receipts and state progression.
5. With total state loss, stop signing. Independently reconstruct recovery records or rotate to a fresh authorized signer after reconciling the old one. Automated full reconstruction from an arbitrary lost snapshot is not provided.

An unused signer can explicitly bootstrap using `python -m keeper.monitor --config REVIEWED_CONFIG --initialize-state`. This never signs; it requires reviewed deployment pins, a fresh head and zero latest/pending nonces, and refuses existing state. Legacy state without a nonce checkpoint requires reviewed migration, never deletion or a blind nonce insertion.

## Logs, health and fallback

The heartbeat now includes `configuration_sha256`, a hash of the exact loaded
configuration. `keeper.ops health` requires the same hash, not merely chain and
sender. Old/missing/malformed or mismatched artifacts return `configuration_mismatch`.
Deploy matching writer/checker together only through an authorized rollout and
require a fresh matching cycle after a reviewed config change. Never patch the
hash, edit/reset a journal or assume this digest authenticates the host/provider.
There is no in-process config reload: finalize config before constructing Keeper.


The current keeper requires both `preparationActive()` and `canonicalState()` on
the exact controller. Missing, malformed or unknown states fail closed. State0
can operate under ordinary preparation/pause rules; Frozen1, Importing2, Retired3
and Cancelled4 stop **all new** keeper submissions, including drains and metadata.
Receipt recovery runs first and remains available. State is checked before
simulation, after gas estimation and before recording a new intent. Health reports
`canonical_locked` for an intentional lifecycle stop. Do not interpret it as
successful maintenance or delete pending state to bypass it. The existing staging
deployment has not been upgraded; qualify controller, fixture and keeper together.

`maintenance_deferred` means a price-dependent upkeep dependency failed. The
keeper may still independently simulate a due fee-only harvest after authenticating
the active bucket; no principal movement or maintenance price check is bypassed.
Malformed configuration/ABI remains fail-closed. Do not treat a successful harvest
as repaired prices or healthy maintenance. Caught conversion/maintenance/harvest
errors with a saved pending intent now stop all further scheduling; use the
original hash/review and normal reconciliation, never reset the journal to resume.

- JSON logs identify action, bucket and transaction where available. Errors include type and source location; raw error bodies, signer output, credentials and full tracebacks are excluded.
- Separate `health_path` defaults to the state filename with `.health.json`. It reports heartbeat time, last success, pending flag, skipped buckets and failure count. `running`, `awaiting_receipt`, `recovery_required`, `revert_cooldown`, `degraded`, `error` and `halted` are not successful maintenance. Dry-run success is explicitly labelled.
- Configure `receipt_fee_policy` only after qualifying the actual chain: `included` requires all network costs in the chain's qualified gas accounting; `separate_l1_fee` requires an explicit L1 fee field on every receipt and a positive reviewed allowance. The example is `unverified`, which blocks live startup. An allowance is a conservative estimate, not an enforceable cap on external L1 charges.
- Reverted actions retain their gas costs and receive a durable cooldown (default one hour). Other eligible work can proceed, while repeated failures remain visible. Gas/budget rejections mark the cycle degraded.
- Current health writer/checker additionally require `confirmed_reverts`,
  `active_revert_cooldowns` and `next_revert_retry_after`. A durably reconciled
  paid revert cannot immediately assert health; `revert_cooldown` reports active
  existing per-action restrictions, including after restart/unrelated success.
  Counts use fresh chain time. Expiry means retry eligibility, not a successful
  transaction or repaired market. No journal schema, fee/nonce accounting,
  retry limit, independent job or loop backoff is changed. Unknown/malformed
  markers or unavailable clock fail health. Roll out the matching writer/checker
  together only under separate authorization; never patch health/journal data.
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
