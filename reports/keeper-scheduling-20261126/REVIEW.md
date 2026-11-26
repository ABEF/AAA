# Unsigned Ubuntu backup and alert scheduling — 26 November 2026

**Implemented and verified in isolation:** ten NEW focused methods and eight
additional native operating stages pass. Existing keeper services, journals,
financial limits and the paused desktop monitor are not adopted or changed.
Production scheduling, off-host possession and real notification channels remain
separate. The original c818 setup failure remains NONPASS.

## Implementation and review

The new [coordinator](../../keeper/scheduling.py) and
[CLI](../../scripts/keeper-schedule.py) reuse the existing exact backup/verify and
alert APIs. Those implementations, their original CLIs and all thirteen daemon
health-source files remain byte-identical to baseline
`03d6caddbe88b552d7edab102cfae0a32847cf37`. No keeper construction, RPC, Cast,
transaction submission, journal restore or signing is added.

| Operation | Implemented boundary |
| --- | --- |
| Explicit initialization | Requires three fresh private output directories; creates the first verified backup, selected record and observer state. Timers never call init. |
| Recurring backup | Captures exact bytes into a new exclusive generation, verifies its manifest pin and atomically selects it. Existing copies remain. |
| Recurring observation | Checks the explicit selected generation, current health and original observer history; it never scans for a newer candidate. |
| Reviewed rebind | Requires both old and new exact policy digests. Only operational settings can change; source/configuration, identities and paths stay fixed. Backup identity and alert-state bytes are preserved. |

The externally reviewed policy binds exact configuration bytes and nineteen
source files: daemon13, observer/tool4 and the new coordinator/CLI2. Strict
schemas, protected local paths, separate output directories, one persistent
nonblocking scheduling lock and original tool validators remain. New budgets
are explicit, within the existing tools' byte/time ceilings; no financial or
keeper limit changes. The [policy template](../../config/keeper-scheduling.example.json)
deliberately blocks unknown values.

The [function review](review/CORE_REVIEW.json) and
[independent design review](review/DESIGN_REVIEW.json) record the pre-execution
corrections. In particular:

- Backup failure does not prevent observation of the last selected backup.
  Damaged alert state does not prevent an independent backup.
- Unrelated generations/capacity do not gate observation. Partial capture
  attempts count toward bounded capacity; no automatic pruning is added.
- Missing committed scheduler/observer state cannot silently initialize a new
  history. Unexpected temporary files are preserved and refused.
- A late policy/source change refuses success without rolling back committed
  outbox state. A rename followed by failed directory sync has an uncertain
  old/new selection, requiring inspection rather than blind rollback.
- Policy changes have an explicit state-preserving operation, rather than
  requiring hand-edited selection or lost event/pending history.

The source service/timer examples remain uninstalled, with deliberately invalid
production cadence placeholders. Services are oneshot, have no automatic restart,
180-second startup/two-second stop bounds and whole-cgroup termination. Explicit
sidecar start-limit disabling prevents inherited host failure latches; reviewed
timer periods control retries. This does not change the signing keeper's limits.

Two file-level `InaccessiblePaths` can share systemd's inaccessible inode and
conflict with the existing alias guard. The examples instead require **two
distinct root-owned empty mode000 files bound read-only over the actual signer
paths**. The reader/alias guard remains unchanged. The native check verifies
distinct regular inodes and denied reads inside an unprivileged service.

## Actual verification

The new [ten-method selection](evidence/c819/fetch-003/FOCUSED_RESULT.json)
passes once in **1.469322 seconds**, zero errors/failures/skips. Its
[durable method progress](evidence/c819/fetch-004/FOCUSED_PROGRESS.json) reconciles
each start, finish and outcome. Historical alert fixture setup is reused as data
and helper composition; no old test body is selected or rerun.

The [native composition](evidence/c819/fetch-001/RESULT.json) completes in
**40.287877 seconds**, including the methods and eight further stages:

| Stage | Actual evidence |
| --- | --- |
| Explicit bootstrap | Actual unsigned CLI initializes verified selection and healthy observer state. |
| Repeated native timers | Backup6s/observe3s timers actually invoke separate unprivileged services; verified generations rotate and observations succeed. |
| Lock and hard timeout | Both busy calls return exact `scheduler_lock`; an inert eight-second oneshot timeout kills parent and child, releases the lock, and subsequent calls succeed. |
| Failed capture | A disposable malformed journal produces exact `backup_capture`/`journal_envelope`; prior selected bytes remain unchanged. |
| Missed backup | Stopping only backup scheduling produces a delivered `backup_stale` incident; fresh backup/health produce actual recovery delivery. |
| Receiver outage/restart | Queued IDs and first-observed pending time survive timer restart; the same IDs deliver when the local receiver returns. Only explicit valid no-pending state clears the clock. |
| Policy rebind | Actual CLI changes only selection policy digest; backup identity and observer bytes remain exact. |
| Final preservation | Disposable journal/configuration return to their original bytes; signer masks remain protected and all jobs/timers stop. |

These stage labels and method passes are different evidence levels; they are not
summed as eighteen independent tests. [Saved-evidence verification](verification/UBUNTU_VERIFICATION.json)
independently checks source/pins, bounded wire/artifact hashes, compressed blocks,
method progress, actual properties and outcomes without executing tests again.

The lab uses explicit **synthetic public historical journal/health vectors**, fresh
wall-clock observations and current source identities. It has no chain or real
provider. Lab cadence6s/3s, backup age8s, initial1s and accuracy100ms are not
production defaults. Maintained shared unit controls and all four example files
are hash-bound, with explicit path/account/network/resource overrides. Workers
run as65534 with empty capabilities. The fixed root coordinator has only the
three fixture privileges CHOWN/DAC_OVERRIDE/FOWNER, a private network and writable
lab runtime. A local receiver shares that private namespace.

## Preserved failed setup and cleanup

[c818](evidence/c818/fetch-001/RESULT.json) stops after0.189236 seconds before any
test body starts. Its namespace anchor was oneshot while dependent workers had
to wait for its startup; an initial inactive worker was incorrectly treated as
finished. The [independent original-evidence review](review/C818_SETUP_REVIEW.json)
confirms PID0, no start timestamp, empty logs and absent method progress.

The separately pinned c819 correction changes **lab orchestration only**: an
executable anchor has a180-second runtime bound, and completion requires actual
start/exit evidence. Production workers remain oneshot. All38 source-closure
rows and all10 method ASTs are identical. The original failure and both offline
preparation stages remain intact; no passing body is replayed to fix setup.

[c818](evidence/c818/fetch-004/FINAL.json) and
[c819](evidence/c819/fetch-002/FINAL.json) each prove all nine owned units stopped
with empty groups, unchanged48-member source maps and unchanged mask sources.
Results are captured before teardown. The [host comparison](verification/HOST_PRESERVATION.json)
checks five existing service states: zero non-ambient differences and one
disclosed observer invocation change. This is a finite comparison, not continuous
uptime or a physical-durability proof.

## Operator procedure and remaining work

The [operator manual](../../docs/OPERATOR_MANUAL.md),
[scheduling guide](../../docs/KEEPER_SCHEDULING.md), backup/alert/recovery guides,
Todo and workload map now describe inputs, source pins, initialization versus
resume, effective-unit review, policy rebind, uncertain publication, capacity,
stop/restart and failure independence. The current [inventory](FUNCTION_INVENTORY.json)
has189 Python files/2,109 named definitions/279 lambdas; frozen F6 remains61 project
sources/39 dependencies/4 controls and1,021 ABI rows. One module name was added
to future test selection; the broad selector and unchanged suites were not run.

Remaining boundaries are explicit: local automatic pin publication trusts its
reviewed producer/private host and is **not independent off-host authentication**.
A shared lock can defer an observer behind slow backup work. A source/config/policy
pin refusal happens before a new HTTP incident can be emitted; the scheduler
itself needs supervision. Missing observer history, temporary residue and
uncertain commits require review. No-delete capacity eventually needs independently
verified archival. Monotonic timers do not replay every missed downtime period.

Real schedules/age thresholds, notification relay and host-down detection,
off-host possession/fencing/restore, kernel/filesystem stalls and power-loss
durability, provider operation, sustained qualification and independent release
approval remain open. No service adoption, public transaction, sealing, site or
existing Anvil/journal change occurred. The desktop monitor stays paused.
