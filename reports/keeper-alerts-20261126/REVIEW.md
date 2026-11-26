# Ubuntu keeper alerts and stale-backup checks — 26 November 2026

**The unsigned one-shot observer is implemented, and all21 NEW Ubuntu methods pass.** The [saved result](evidence/fetch-001/RESULT.json) records4.072 seconds, zero failures/errors/skips, UID/GID65534 and a private network namespace. Each method ran once; no existing green body, contract/browser suite or financial journey was rerun. The [operator guide](../../docs/KEEPER_ALERTS.md) contains all inputs, units and recovery steps.

This is an actual Ubuntu/POSIX filesystem and localhost HTTP check of the new observer. It uses new temporary fixtures and published JSON vectors as data, retimed and bound to the new local source. It does **not** inspect, mutate or qualify the running legacy keeper. Keeper construction, subprocesses and non-receiver connections are denied inside the selection. No Anvil, Cast, signer, RPC request, transaction or seal is used by these methods.

## What changed

| Component | Result |
| --- | --- |
| [keeper/alerts.py](../../keeper/alerts.py) | Bounded health/current-journal reads, existing exact backup verification, explicitly supplied age thresholds, sanitized incidents and healthy recovery |
| [scripts/keeper-alerts.py](../../scripts/keeper-alerts.py) | Unsigned one-shot command; explicit configuration/working directory/backup/pin/original configuration/private state directory and age inputs |
| [keeper/ops.py](../../keeper/ops.py) | Optional explicit bounded-snapshot input, preserving the omitted-keyword reader and the original health verdict body |
| Separate private alert state | Atomic durable outbox, stable IDs, process lock, restart deduplication, first-observed pending timer and bounded delivery |

Only the observer's separate state/outbox/lock is written. Original journal bytes, configuration, health, source backup and signer files remain untouched. There is no scheduler installation, keeper repair, transaction recovery action, restart, public notification channel or automatic source adoption.

The adapter changes **one of thirteen daemon health-source identities**. The other twelve, including `keeper/monitor.py`, remain exact. [Source review](verification/SOURCE_REVIEW.json) and [preparation pins](preparation/PREP_REVIEW_PINS.json) bind the four reviewed files. AST comparison confirms that `health_check` after input selection retains its original body. This is a justified Python identity change, not a journal codec, contract, accounting, authority, fee/gas/RPC limit or readiness relaxation. Adopt matching writer/checker code and newly reviewed matching backup pins separately; preserve old health, bundles and journals under their original release.

## Alert behavior and draft corrections

- Ordinary known-hash pending may receive the explicitly configured grace only while unrelated health/source/runtime/profile checks and backup verification pass. The underlying readiness remains false. Hashless or inconsistent pending alerts immediately. The timer measures **time since first observation of the intent**, not transaction submission age; restarts, later hash publication and normal backup rotation preserve it.
- Backup selection and external manifest SHA-256 are explicit. Integrity, original configuration/profile/source binding and capture age reuse the existing backup verifier. A stale or corrupt backup cannot produce recovery, even when health is fresh. Capture age is not canonical freshness or off-host possession.
- Incidents are committed before HTTP; an exact positive ACK precedes removal/commit. Lost ACK retries the same event ID. This is at-least-once delivery, requiring sink deduplication; it is not exactly-once notification.
- Capacity is64 events and at most8 attempts per invocation. Already-durable entries drain before new transitions, preventing a full-queue deadlock when the receiver recovers. An insufficient queue refuses new transitions without dropping old events or resetting state.
- Only literal `http://127.0.0.1:PORT/alerts` is accepted. The restricted local HTTP exchange has a two-second absolute deadline,8,192 combined response bytes and exact `event_id`/`accepted:true` ACK fields. No redirects, proxies, DNS destination selection, credentials or arbitrary payload/error/configuration text are sent.

Pre-execution review corrected five draft issues: valid finite health-duration floats were initially refused; pending grace could mask unrelated source faults; the journal check was incomplete; a FIFO could block the observer's first read; and a full outbox could prevent delivery from ever resuming. The final code accepts only finite health floats, uses the existing exact journal validator, restricts grace, uses a nonblocking first file open and drains durable events before transitions. These were corrections to the new draft, not relabeled old-production findings. All21 methods ran against the final reviewed production/test files.

## New verification partitions

The [source manifest](preparation/SOURCE_MANIFEST.json) records35 Python source members from `fe2db714e0ef14252cf43f8afb7c1f0d772c1bbd`, with three explicit new files and the explicit `keeper/ops.py` worktree override. There are39 archive members including the runner, manifest and two static JSON vectors. It does not claim every packaged file is HEAD-identical.

| New methods | Covered behavior |
| --- | --- |
|3 | Actual health/backup validator composition, snapshot adapter without reread, explicit dry mode |
|3 | Known pending first-seen/grace/restart, hashless/mismatched/malformed fee/profile refusal, unrelated source/config faults |
|3 | Independent health/backup age and corruption, malformed health/FIFO, backup rotation with hash publication |
|6 | Durable incident deduplication, actual incident/recovery HTTP, wrong ACK, lost ACK/same ID, redirect/proxy refusal, recovery requiring both valid inputs |
|1 | Slow response headers against an actual absolute one-second remaining invocation budget |
|4 | Failed durable write/no send, competing lock, unsafe endpoints/resource/path bounds/redaction, input race/no false recovery |
|1 | Publicly generated64-event outbox drains its original ordered prefix and preserves every old ID while queuing a new incident |

These are21 distinct methods, not a claim of exhaustive state coverage. Existing producer and health logic are composed by new tests; their old test bodies were not executed. Synthetic secret markers verify no configured signer contents, credentialed URL or arbitrary exception appears in state/result/payload. The actual temporary journals and private fixture configurations are not published.

## Execution, cleanup and preservation

The [controller](preparation/remote_capsule.py) can operate only the fresh fixed lab `/opt/popl-keeper-alerts-20261126-c815` and its single named unit. Root-owned read-only source runs as `nobody:nogroup`, with private network/tmp, strict filesystem protection, no privileges,512MiB memory/no swap,64 tasks, no restart,180-second outer deadline and bounded diagnostics. The [parent receipt](evidence/ORCHESTRATION_RESULT.json) records10.140 seconds including installation, execution, stop and retrieval. The [final record](evidence/fetch-002/FINAL.json) proves source-before/after equality and an empty stopped cgroup.

The [host comparison](verification/HOST_PRESERVATION.json) verifies all five existing unit states, zero non-ambient differences and one disclosed periodic-observer invocation change. The older seven owned labs remain stopped. This observation does not resume the desktop heartbeat: it remains user-paused. Existing services, sites, Anvil8902, journals, signer/null public settings and financial/operating limits remain unchanged.

One **preparation-only drift** is retained in [the correction record](verification/PREPARATION_DRIFT.json): two timeout-handler lines in the client runner template changed during offline packaging. The independently pinned generated/executed runner retained its original `TimeoutError`; neither it, the capsule nor test bodies changed. The original mismatched template and pre-execution pins remain in preparation; [the restored template](preparation/REPRODUCIBLE_RUNNER_TEMPLATE.py) reproduces the exact executed runner. The outer unit deadline remained180 seconds; the selection completed in4.072 seconds. No successful method was repeated to correct this packaging inconsistency.

## Adoption and remaining limits

No production ages are selected: all three age thresholds are explicit operator inputs. Configuration/source/policy drift emits an identity-change incident while preserving old events. Updating the observation scope is a notification transition, not authorization; a later stable cycle can recover only with fresh matching health and a verified selected backup.

Protected local ancestors and the invoking user are trusted. The first observer read rejects nonregular files, but the reused backup/configuration producer can reopen a file; hostile same-UID replacement and kernel/filesystem stalls remain within its existing trust boundary. The processing budget is cooperative, not a kernel-I/O preemption guarantee. Use separately reviewed outer supervision for a hard overall timeout. The HTTP exchange does have its own absolute deadline. Source hashes describe local bytes, not remote-running-code attestation; checksums supplied with hostile files are not external authentication.

Still open: real notification channel/delivery acknowledgement, actual backup scheduling and off-host possession, host-down monitoring, alert-process supervision, cross-host fencing/restore, sustained outages and operation, actual-provider/market fees and independent release approval. Q06/P20/P21 remain open. Local-loopback delivery cannot notify anyone when this same host is down. Publication installs nothing.

The [current inventory](FUNCTION_INVENTORY.json) contains187 Python files,2,087 named definitions and279 lambdas; frozen F6 remains61 project/39 dependency sources,4 controls and1,021 ABI rows. The Todo retains all83 IDs/statuses, with this finite work attached to keeper monitoring/recovery. The normal inventory pointer, operator manual, specialist recovery/backup guides, feature reference, roadmap, findings and repository memory are updated together. Historical evidence retains its original pins and scope.

The first offline staged-artifact check refused Windows path separators in its generated manifest. The [original refusal](verification/STAGING_PATH_ATTEMPT1.json) is retained; manifest keys now use portable POSIX relative paths. Artifact/source bytes and successful test methods were not changed or rerun.
