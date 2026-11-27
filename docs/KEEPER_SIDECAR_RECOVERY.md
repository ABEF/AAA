# Scheduler and alert-state recovery

Use `scripts/keeper-sidecar-recovery.py` to prepare an unsigned recovery package
for the [backup/observer scheduler](KEEPER_SCHEDULING.md). This is separate from
the [keeper journal backup](KEEPER_BACKUP.md). It never signs, queries RPC,
installs restored files, starts a service or changes a keeper journal.

## What is preserved

| Payload | Meaning |
| --- | --- |
| Selected-backup record | Exact generation name, original manifest pin, capture time, policy/configuration binding and identity |
| Alert state | Exact outbox/event IDs, sequence, active incidents, observation scope and pending `first_seen` clock |
| Selected generation manifest | Exact original backup metadata; not a newly dated journal |
| Selected generation journal | Exact bytes of that selected snapshot; it need not equal the keeper's latest journal |

The package stores raw `selection.json`, `alert-state.json` and
`selected/manifest.json` / `selected/journal.json`. Fresh restoration maps them
to `scheduler/selected.json`, `alerts/state.json` and
`backups/<original-generation>/manifest.json` / `backups/<original-generation>/journal.json`; the original
generation name and all four records stay byte-identical.

Keep the original policy, original configuration and matching reviewed release
separately. Signer material, passwords and the keeper's current journal are not
copied. The package cannot reconstruct missing original configuration, unknown
canonical transactions or lost history. The selected backup can legitimately
be older than the alert state's last observation; those histories are preserved
independently rather than forced into a false equality.

The package's manifest SHA-256 must be retained through an independently trusted
channel. A digest stored only alongside the package is not independent
authentication or off-host possession.

## Inputs and commands

Use absolute protected paths. Digests are 64 lowercase hexadecimal characters
without `0x`. Example placeholders must be replaced with reviewed values:

```text
python3 -B /opt/zzz-protocol/scripts/keeper-sidecar-recovery.py backup --policy /etc/zzz/schedule.json --policy-sha256 REVIEWED_POLICY_DIGEST --output /archive/sidecars-NEW
python3 -B /opt/zzz-protocol/scripts/keeper-sidecar-recovery.py verify --policy /etc/zzz/schedule.json --policy-sha256 REVIEWED_POLICY_DIGEST --bundle /archive/sidecars-NEW --manifest-sha256 TRUSTED_PACKAGE_DIGEST --max-age-seconds REVIEWED_CAPTURE_AGE
python3 -B /opt/zzz-protocol/scripts/keeper-sidecar-recovery.py restore --policy /etc/zzz/schedule.json --policy-sha256 REVIEWED_POLICY_DIGEST --bundle /archive/sidecars-NEW --manifest-sha256 TRUSTED_PACKAGE_DIGEST --max-age-seconds REVIEWED_CAPTURE_AGE --output /recovery/sidecars-REVIEW-NEW
```

| Input | Applies to | Meaning |
| --- | --- | --- |
| `--policy` | All | Separately secured exact original scheduling policy |
| `--policy-sha256` | All | Externally reviewed digest of its raw bytes |
| `--output` | Backup/restore | Fresh private destination under an existing protected parent |
| `--bundle` | Verify/restore | Complete exact package directory |
| `--manifest-sha256` | Verify/restore | Independently retained package manifest digest |
| `--max-age-seconds` | Verify/restore | Required positive maximum package capture age, in seconds |
| `--minimum-created-at` | Verify/restore | Optional trusted earliest package capture, UTC Unix seconds |
| `--max-bytes` | All | Total byte budget; default16777216, ceiling67108864 |
| `--max-seconds` | All | Cooperative work budget; default60, ceiling120 seconds |

The total budget includes metadata and payload, not a separate allowance for
each file. Restore also checks its prepared plan against its output budget.
A stricter byte/time budget in the original scheduling policy remains in force.
Oversized, malformed, duplicate, missing, linked or unexpected files are refused;
there is no truncation or automatic budget increase. POSIX ownership/locking is
required. Windows ACLs, network filesystems and physical durability are separate
qualification work.

Verify and restore still need the exact separately supplied policy, its
referenced original configuration and matching source release. The declared
working directory and output parents must exist in the reviewed protected
layout. Live scheduler selection, alert state and their lock files are not
required for those two operations: their captured records come from the
package. Other configured runtime-path metadata remains subject to validation.
If host loss removed the layout, use the [complete private kit procedure](OPERATOR_MANUAL.md#unsigned-recovery-kit-and-clean-filesystem-reconstruction)
to reconstruct exact application inputs at reviewed logical paths. The
[clean-root evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/keeper-reconstruction-20261127/REVIEW.md) verifies
this without old application folders, but still supplies the existing OS runtime.
Do not invent configuration or rewrite captured hashes; physical-host/OS/signer
recovery and live adoption remain separate reviews.
The [later stock keeper restart](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/keeper-clean-restart-20261127/REVIEW.md)
uses a separate fresh journal/configuration/release kit and real local receipt;
it does not recapture or rerun this synthetic sidecar queue proof. Its
[unsigned restart recipe](OPERATOR_MANUAL.md#unsigned-keeper-restart-from-a-reconstructed-kit)
keeps actual signer/OS/chain adoption and unchanged sidecar policy separate.

## Capture and verification

Capture acquires the **existing** schedule lock, then the **existing** alert
lock, without creating either. This matches the scheduler's lock order. A busy
or missing lock refuses capture; never create a replacement lock to force it.
The tool checks original identities and rereads raw state before publication.
New package and restored payload bytes are also read back under the same
budget before their final manifest/plan is committed; no byte repair is made.
Cooperating scheduled jobs pause on their shared lock; this does not acquire the
keeper's own lock or establish multi-host fencing.

The original policy binds configuration and nineteen source files. Producer
provenance separately identifies the recovery tool. Exact schemas, identities,
source controls, selected manifest/journal hashes and alert-state rules remain
enforced. No directory scan selects a newer backup.

A stale selected generation may still be captured for recovery. Its integrity
is checked **as of its original capture time**, with the exact original time
cross-checked; its operational freshness is never approved. Package capture age
is checked separately during verify/restore. Creating a new package does not
make the old journal fresh, reset pending age or override the normal observer's
freshness/incident checks.

## Restore preparation and adoption boundary

Restore writes a new private tree containing scheduler state, alert state, the
selected generation and an unsigned `RESTORE_PLAN.json`. All captured records
retain their original bytes. Two new empty private lock files are coordination
inodes for the proposed destination; they do not restore or prove old lock
ownership. No original lock or existing destination is replaced.

The plan maps original logical paths to the proposed output tree. It does not
rewrite policy hashes, selected-record paths or observation history. The normal
scheduler's `rebind` permits operational settings only; it cannot authorize a
path/configuration/source migration. Review that mapping explicitly before any
future adoption. A private mount namespace can exercise the original logical
paths against disposable restored directories without replacing source data.

Before adoption, fence the old sidecar jobs and their restart paths; preserve
original files, policies, configuration, release and logs. Review both signer
mask paths and all effective read/write bindings. Keep the keeper's own pending
recovery and single-signer fencing procedures separate. A new host needs the
same original policy/configuration identities and an explicitly reviewed path
mapping, never hand-edited raw records or a fresh scheduler initialization.

Readiness, fencing, installation and restart approval remain false in the
prepared plan. A valid package is not approval to run a live keeper. The fields
`lock_ownership_restored` and `selected_generation_freshness_approved` are also
explicitly false: restored files cannot establish either fact. Restored
observation must retain queued IDs and pending history, then evaluate actual
current health/journal/backup freshness normally. Receivers must deduplicate
event IDs because delivery remains at least once.

## Refusal and interruption

Preserve incomplete output and use a new reviewed destination after diagnosing
the cause. Never automatically delete partial packages, promote temporary
state, roll back an uncertain commit or rerun `init` over lost observer history.
Missing source state requires recovery from independently retained data, not an
invented empty queue. A cooperative work budget cannot preempt blocked kernel
I/O/fsync; separately reviewed supervision remains required.

Earlier same-host isolated recovery proves neither off-host possession nor cross-host
fencing. The [desktop round-trip](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/keeper-offhost-20261126/REVIEW.md) now
proves possession of the exact synthetic package and its return to fresh review
folders on the same Ubuntu host. It uses actual clock86400-second historical
review, leaving the original900-second operating freshness policy unchanged and
unapproved. Original release/configuration/layout remain server-only dependencies.
Independent second-host execution, cross-host fencing, real notification delivery,
host-loss handling, provider operation,
sustained qualification and independent release approval remain open. Existing
services, journals and the user-paused desktop monitor are not adopted by this
source publication.
