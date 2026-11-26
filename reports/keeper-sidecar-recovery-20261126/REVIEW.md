# Unsigned scheduler and alert-state recovery — 26 November 2026

An unsigned recovery package now preserves the scheduler's selected generation
and the observer's exact delivery/pending history together. Restoration prepares
a new private tree and an explicit mapping plan. It does not install files,
restart a service, sign, query RPC or change the keeper journal.

**Eight NEW focused Ubuntu methods pass once**, with zero failures, errors or
skips, followed by actual unsigned backup/verify/restore and resumed observation
against the restored folders. No old test body runs. This is finite same-host
synthetic evidence, not off-host possession, signer fencing or release approval.

## Implementation and review

Baseline: `aae84e64d7f7fa470e5767630608755df91e75c1`.

| Change | Scope |
| --- | --- |
| [keeper/sidecar_recovery.py](../../keeper/sidecar_recovery.py) | Twenty-five definitions: bounded exact capture, package verification and exclusive review-only restore |
| [scripts/keeper-sidecar-recovery.py](../../scripts/keeper-sidecar-recovery.py) | Three definitions: unsigned CLI with fixed sanitized refusals |
| [New focused tests](../../tests_python/test_keeper_sidecar_recovery.py) | Eight independent new bodies; existing fixture setup helpers only; POSIX-only class |
| [Future test selector](../../scripts/run-keeper-tests.py) | One new module literal; the full selector was not executed |
| [Operator procedure](../../docs/KEEPER_SIDECAR_RECOVERY.md) | Exact paths, digest/age/byte/time inputs, recovery boundaries and refusal handling |

The nineteen original scheduling identity files, including the thirteen daemon
health files, remain byte-identical. Existing backup/alert cores and CLIs, unit
templates, journal schemas, permissions, financial/resource defaults, F6 Solidity
and its source maps remain unchanged. The new producer identifies its two files
separately; it does not silently extend the old scheduling policy's source list.

The [core review](review/CORE_REVIEW.json), [independent design review](review/DESIGN_REVIEW.json)
and [dynamic dependency review](review/CLOSURE_REVIEW.json) record distinct static
scopes. The [current inventory](FUNCTION_INVENTORY.json) has191 Python files,
2,137 named definitions and279 lambdas; frozen F6 remains61 project sources,
39 dependencies,4 build controls and1,021 ABI rows. Inventory is not coverage.

## State and recovery rules

Four raw records are preserved: selected-backup record, alert state, selected
generation manifest and that generation's journal. The snapshot journal may be
older than the observer's pending history or the current keeper journal; the
tool never invents equality between these different histories.

Capture takes the **existing** schedule lock, then the **existing** alert lock,
nonblocking and without creating either. Private ownership, regular-file shape,
link count, inode identity, exact inventory and stable rereads are required.
Held-lock identities and output bytes are checked before final publication.
Unlock failures still close descriptors. Busy/missing/replaced locks refuse.

Historical selected-backup integrity is validated at its original capture time;
the nested time must match exactly. A newly captured outer package has a separate
capture-age check. It does not refresh the old journal or approve its present
operating freshness. The normal observer still reports actual incidents.

Restore preserves raw bytes and writes fresh empty0600 coordination files.
They are **new lock inodes**, not restored ownership. Local `flock` ownership
belongs to an open file description and cannot be recovered from file contents.
See the [Linux locking reference](https://man7.org/linux/man-pages/man2/flock.2.html).

All readiness, fencing, canonical-state, signer-inclusion, installation, restart,
mapping, lock-ownership and selected-freshness approval fields remain false.
Original policy/configuration/release and trusted digests must be secured
separately. Verification/restoration also require the original protected working
and parent layout; missing live selected/alert records are not required. New-host
layout preparation and path mapping need separate review. Normal scheduler
`rebind` still cannot authorize a source/configuration/path migration.

Byte budgets include payload and metadata together. Defaults remain16MiB/60s,
ceilings64MiB/120s, and a stricter original policy wins. There is no overwrite,
auto-delete, empty-state fallback, timestamp reset or automatic installation.
Partial/uncertain output is retained. Cooperative deadlines cannot preempt a
blocked kernel operation; hard external supervision remains necessary.

## Original attempt and targeted correction

The original **c820 remains NONPASS**. It stopped in fixture setup before any
focused method, CLI command or scenario started: one dynamically named existing
script, `scripts/keeper-schedule.py`, was absent from the upload package.
[Original result](evidence/c820/fetch-1/RESULT.json), [final capture](evidence/c820/fetch-2/FINAL.json)
and failed missing-progress fetch receipt are retained. All four owned groups
were stopped. This is a packaging failure, not a passing application check.

c821 adds exactly that HEAD dependency. All forty prior source rows, production
bytes and eight test ASTs remain identical. Runtime preparation differs only in
the new lab namespace. The builder now includes all declared source groups and
both actual subprocess entrypoints, alongside recursive imports and the two
pinned public fixture vectors. Its [closure proof](preparation/c821/STATIC_CLOSURE_REVIEW.json)
and [parent approval](preparation/c821/PARENT_PREEXECUTION_REVIEW.json) bind49 archive
members/41 source rows. Earlier offline package receipts are explicitly retained
as preparation, not executions. No previously passing body was rerun.

## New Ubuntu execution

c821 finishes in3.825290 seconds, including2.017733 seconds for the eight methods.
It uses three nobody/nogroup workers and one bounded root coordinator, a private
network namespace, distinct root-owned empty mode000 read-only signer masks,
empty worker capabilities and fixed limits. No real signer material is copied
or read. There is no Anvil, Cast, Ethereum RPC, transaction or financial journey.

| New focused method | Actual purpose |
| --- | --- |
| Historical round trip | Stale selected journal and newer pending/outbox history retain all raw bytes |
| Existing-lock behavior | Real busy/missing locks refuse; unlock error closes descriptors |
| Pin/inventory tampering | Wrong pins, modified payloads and unexpected entries refuse |
| Output/budget separation | Limits and overlap fail without changing source state |
| Identity/configuration | Unsupported policy/profile/source identities refuse |
| Missing/partial state | No implicit initialization or complete-marker publication |
| Exclusive restore/age | Existing output refuses; new package does not refresh old rights/history |
| Noncooperating changes | State replacement and held-lock races block complete capture |

[Focused result](evidence/c821/fetch-4/FOCUSED_RESULT.json) and
[per-method progress](evidence/c821/fetch-5/FOCUSED_PROGRESS.json) record exactly8
started/finished/passed methods, zero old bodies and zero skips. The POSIX label
was set before first execution; no Windows execution is claimed.

The additional actual native stages are:

1. Run the new backup, verify and restore commands. Compare four source/restored
   raw records, verify new empty private lock inodes, and retain all false
   adoption flags. Original policy/configuration and source state stay unchanged.
2. Fence the finished source worker, then bind the restored directories over the
   original logical paths in a separate target mount namespace. Run the existing
   scheduler's observer and acknowledge its **original** queued event ID through
   a local test receiver. Pending `first_seen`, sequence and active incident stay
   unchanged; outbox drains. Exit1 is expected because health remains an incident.
   Outside that namespace, original source folder hashes remain unchanged.
3. Stop the three workers; verify their groups empty and original fixture journal
   unchanged. Stop the root anchor and capture final source/mask/group evidence.

See [source commands](evidence/c821/fetch-6/SOURCE_RESULT.json),
[target observation](evidence/c821/fetch-7/TARGET_RESULT.json),
[campaign result](evidence/c821/fetch-1/RESULT.json) and
[final capture](evidence/c821/fetch-2/FINAL.json). Namespace binding is explicit,
not a policy rewrite or an automated adoption feature; see
[systemd BindPaths](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html#BindPaths=).

The native harness directly asserted raw-byte equality/readback. The independent
saved-evidence review reconciles recorded hashes/lengths, state, outcomes and
code assertions. The four physical payloads were not fetched for independent
raw-byte rehashing; do not describe that separate proof as completed.
The [saved verification](verification/UBUNTU_VERIFICATION.json) binds its exact
inputs and [report-only verifier](verification/verify_saved.py); it imports no
application code and executes no test, network request or server action.

## Preservation and remaining qualification

Both four-unit labs stop with empty owned groups and unchanged source/mask
files. The separately captured [host comparison](verification/HOST_PRESERVATION.json)
finds zero non-ambient differences across five pre-existing service states and
discloses one observer invocation. This is a finite state comparison, not proof
of every original host byte or power-loss durability.

Original journals, existing services/sites/Anvil8902 and the paused desktop
heartbeat are not adopted. Source publication authorizes no public transaction,
new sealing, rollout or change to signing/financial/resource limits.

Real off-host possession and authenticated transfer, host-loss restore and
single-signer/sidecar fencing, actual notification routing and external host-down
monitoring, physical durability, production providers, sustained operation and
independent release approval remain open. Q06/P20/P21 remain open. The earlier
[scheduling](../keeper-scheduling-20261126/REVIEW.md),
[journal backup](../keeper-backup-20261126/REVIEW.md) and
[receipt-recovery rehearsal](../ubuntu-backup-recovery-20261126/REVIEW.md) retain
their original source, fixture and verification scopes.
