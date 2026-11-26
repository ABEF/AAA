# Unsigned keeper backup and alert scheduling

The [desktop/Ubuntu return](../reports/keeper-offhost-20261126/REVIEW.md) preserves selected generation, outbox IDs and pending clock through exact off-host package transfer. It prepares new review folders only; no scheduler initialization or live adoption occurs. Prior [combined native scheduling](../reports/ubuntu-keeper-composition-20261126/REVIEW.md) keeps its separate actual-daemon scope.

The scheduler coordinates the existing exact-journal backup and alert tools.
It never starts the keeper, signs, calls RPC, restores a journal or grants live
readiness. The maintained systemd examples are not installed by publication.
The desktop monitor remains paused.

## Review the policy before first use

`scripts/keeper-schedule.py` accepts one action, `--policy` and
`--policy-sha256`; only `rebind` also requires the previous policy and digest.
Each digest is the independently reviewed SHA-256 of the
**exact policy file bytes**, 64 lowercase hex characters without `0x`.
The policy is a strict JSON object; all fields are required:

| Field | Input / units |
| --- | --- |
| `schema`, `kind` | Integer `1`, string `popl-keeper-schedule` |
| `configuration`, `configuration_sha256` | Absolute original keeper config path and SHA-256 of its exact bytes |
| `working_directory` | Actual absolute keeper working directory |
| `scheduler_directory` | Fresh private directory for selection and persistent lock |
| `backup_directory` | Fresh private directory for exclusive backup generations |
| `alert_directory` | Fresh private directory for observer state/outbox |
| `source_files_sha256` | Exact 19-file map: daemon13, observer/tool4, scheduler core/CLI2; see `keeper.scheduling.SOURCE_FILES` |
| `max_backups` | Integer `1..1024`; partial generation attempts count |
| `max_health_age_seconds` | Reviewed integer `1..31536000` seconds |
| `max_backup_age_seconds` | Reviewed integer `1..31536000` seconds |
| `pending_max_age_seconds` | Reviewed integer `1..31536000` seconds since first observation |
| `receiver` | `null` or literal `http://127.0.0.1:PORT/alerts` |
| `allow_dry_run` | Explicit boolean matching the reviewed health profile |
| `max_bytes` | Integer `1..67108864`; existing tool ceiling, normally `16777216` |
| `max_seconds` | Total cooperative invocation budget, integer `1..120`; normally `60` |

Start from the deliberately blocked [policy template](../config/keeper-scheduling.example.json).
Its unknown ages, capacity, dry-run choice, configuration digest and source map
must be reviewed and filled; it is not runnable production configuration.
Take the 19 source hashes from the independently reviewed release artifacts,
not from an unreviewed machine merely to make a refusal disappear.

Production ages and schedules are deliberately not selected. Calculate them
against the real keeper cadence, confirmations, expected outages and backup
frequency. Estimate storage before choosing capacity: retained copies can each
approach the explicit byte ceiling. Capacity is not a retention period.

Keep the policy/source release read-only. Secure its reviewed digest separately;
do not compute a replacement digest merely because a check refused. Original
configuration bytes, signer material and source releases remain separate from
the backup generations. Source/configuration changes require a new reviewed
policy and adoption procedure; do not edit old manifests or journals.

All three output directories must be distinct, private mode0700 and outside
the keeper journal's parent, policy/configuration and runtime/signer paths.
Their existing parents must be protected. No symlink, hardlink alias, arbitrary
newest-folder selection, automatic deletion or in-place restore is supported.
The invoking account and local ancestors remain trusted; this is not host fencing.

## Commands and outputs

Substitute separately reviewed absolute paths and the exact digest:

```text
python3 -B /opt/zzz-protocol/scripts/keeper-schedule.py init --policy /etc/zzz/schedule.json --policy-sha256 REVIEWED_64_LOWERCASE_HEX_DIGEST
python3 -B /opt/zzz-protocol/scripts/keeper-schedule.py backup --policy /etc/zzz/schedule.json --policy-sha256 REVIEWED_64_LOWERCASE_HEX_DIGEST
python3 -B /opt/zzz-protocol/scripts/keeper-schedule.py observe --policy /etc/zzz/schedule.json --policy-sha256 REVIEWED_64_LOWERCASE_HEX_DIGEST
```

| Action | Required state | Result |
| --- | --- | --- |
| `init` | All three output directories absent | Creates first exact backup, verifies it, commits selection and initializes observer state; call once only |
| `backup` | Committed scheduler state and backup root | Creates a fresh generation, verifies its exact pin, atomically changes selected backup |
| `observe` | Committed scheduler and observer state | Checks only the selected generation and current health; preserves original event IDs and pending age |
| `rebind` | Exact previous policy/path/digest and committed selection | Adopts reviewed operational settings without replacing backup or alert history |

An initialization that records an incident can return nonzero even though its
state was created. Inspect the sanitized result and files; never retry `init`
over partial or committed output. Timers call only `backup` and `observe`.

Both jobs take the same nonblocking persistent schedule lock. Contention
refuses that invocation; it never replaces the lock, queues a duplicate task
or retries recursively. The next scheduled activation can try again. Direct
one-shot observer calls have their own outbox lock; do not run competing
unreviewed schedulers against the same state.

A slow backup can therefore defer observation until a later timer activation.
Review alert-age and delivery expectations against the full cooperative/hard
timeout, not just the nominal interval. This lock does not acquire the keeper's
own lock or delay its transaction recovery. Repeated contention is a failed
sidecar operation to supervise, not a healthy observation.

Capture or verification failure leaves the previous selection unchanged.
A failure after atomic rename but before successful directory sync has an
**uncertain old/new commit**: stop, preserve and inspect; never roll back blindly.
Incomplete generation folders stay preserved and count against capacity.
The observer does not choose an alternate backup because one folder looks newer.

Local automatic selection trusts the reviewed local producer and private
publication directory. It is not an externally authenticated or off-host copy.
Retain each selected manifest pin independently before claiming off-host recovery.

To change ages, receiver, dry-run observation, capacity or tool budgets, stop
both timers and services first. Preserve the old policy unchanged, prepare a
new file with its separately reviewed digest, then call:

```text
python3 -B /opt/zzz-protocol/scripts/keeper-schedule.py rebind --policy /etc/zzz/schedule-next.json --policy-sha256 REVIEWED_NEW_DIGEST --previous-policy /etc/zzz/schedule.json --previous-policy-sha256 REVIEWED_OLD_DIGEST
```

The old selection must match the exact previous policy. Configuration, working
and output paths, deployment identity and all19 source hashes must stay equal.
Only the selection's policy digest changes; generation, original manifest pin,
capture time and alert-state bytes stay intact. Refresh the service environment
to the newly reviewed path/digest before resuming. Editing the old policy in
place loses the previous proof and is refused. Lowering capacity can block
later captures until reviewed archival; it does not stop observation. Rebinding
does not make an old backup fresh or approve a source/configuration migration.

Changing just the timer interval does not change the JSON policy. Stop the
reviewed units, update their installation copies, review/reload only that
installation and resume with the existing state. No keeper restart or on-chain
transaction is needed for these sidecar-only timing changes.

## systemd supervision and schedule

Review the four maintained examples under `keeper/zzz-keeper-backup.*` and
`keeper/zzz-keeper-observer.*`. Timer intervals contain deliberately invalid
placeholders; replace them only in separately reviewed installation copies.
Prepare a protected environment file with just the policy path and digest:

```text
POPL_SCHEDULE_POLICY=/etc/zzz/schedule.json
POPL_SCHEDULE_POLICY_SHA256=REVIEWED_64_LOWERCASE_HEX_DIGEST
```

Review account ownership, source/working/output paths and **both actual signer
paths** in `BindReadOnlyPaths`. Use two distinct, new root-owned empty regular
mask files under a protected root-owned directory outside all writable paths.
Require mode000, size0, link count1, no symlink and different device/inode pairs;
bind them read-only over the two original signer paths in the sidecar namespace.
The real files stay unchanged. Do not use two file-level `InaccessiblePaths`:
systemd can map both to one inaccessible inode, correctly rejected by the
existing alias-separation guard. Keep that guard intact. Review effective binds
and confirm both paths are unreadable and distinct inside the service.
Give sidecars no new signer permissions. The
backup service uses a private network; observation permits only host loopback.
A future real notification relay and independent host-down monitor are separate.

The examples use `Type=oneshot`, `Restart=no`, `RemainAfterExit=no`, explicit
180-second startup timeout, two-second stop timeout and whole-cgroup termination.
Sidecar start-rate limiting is explicitly disabled (`StartLimitIntervalSec=0`)
so inherited host defaults cannot latch off a recurring check after failures.
There is no automatic service restart: the reviewed timer interval controls
retry frequency. Review that interval against work duration and operating cost;
these sidecars do not change the signing keeper's existing restart/start limits.
Check the effective `TimeoutStartUSec`, `TimeoutStopUSec`, `KillMode`, account,
write paths and signer exclusions before enabling anything. `RuntimeMaxSec`
alone does not cap oneshot startup. Cooperative Python budgets cannot preempt
kernel I/O or fsync stalls; supervisor/kernel boundaries remain.

The monotonic timers use `OnActiveSec` and `OnUnitInactiveSec`: the next period
is measured from completion, not a promise of exact wall-clock intervals. A
still-active matching service is not started twice. Missed downtime periods
are not replayed as a queue of historical backups. See the official
[timer semantics](https://www.freedesktop.org/software/systemd/man/255/systemd.timer.html)
and [oneshot timeout rules](https://www.freedesktop.org/software/systemd/man/255/systemd.service.html).

After separately authorized installation, start the two reviewed timers; inspect
their effective next/last trigger and service results. To pause this scheduling,
stop **both timers and both services**. Stopping a timer alone does not cancel
an already running invocation. Resume the same reviewed timers with original
state retained. Do not run `init`, reset event IDs or replace lock files.

For exact selected-record, pending-clock and queued-event recovery, use the
separate [sidecar recovery package](KEEPER_SIDECAR_RECOVERY.md). It captures the
committed scheduler/observer records and selected generation together, without
copying signer material or installing restored state. Keeper journal backup
remains separate; an outer package capture does not make its old selected
journal fresh.

## Failure and recovery

| Condition | Operator response |
| --- | --- |
| Capture/verification refusal | Preserve failed generation and old selection; repair the cause and let a later invocation create a new copy |
| Backup capacity reached | Stop backup timer; independently archive/verify older generations, preserve the selected one and external pins, review resulting inventory before resuming; no automatic pruning |
| Missing selected record or temporary scheduler file | Stop both jobs, preserve files and review committed state; no auto-init or temporary-file promotion |
| Missing/damaged observer state | Stop observer, preserve outbox evidence and prepare fresh [sidecar recovery](KEEPER_SIDECAR_RECOVERY.md) from an independently retained package; never reset its pending clock |
| Missing health/journal | Observation records the supported incident; it never invents empty state or repairs keeper data |
| Configuration/source/policy pin mismatch | Fixed scheduler refusal before observation; preserve state and inspect failed service. This invocation cannot emit a new HTTP alert |
| Receiver outage | Preserve queued IDs; repair the relay and retry through the same observer state; delivery remains at least once |
| Hard timeout or interrupted publication | Fence the affected job, preserve partials and inspect original state before resuming; no automatic deletion or rollback |

A same-host scheduler cannot report complete host failure by itself. Production
still needs external receipt/host-down monitoring, off-host backup possession,
single-signer fencing and sustained operating qualification. These commands
change no on-chain safeguards, gas/fee limits or NFT rights.
