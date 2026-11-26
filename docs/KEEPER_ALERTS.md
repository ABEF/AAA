# Keeper alerts: one-shot observation and local delivery

[Concurrent normal-keeper evidence](../reports/ubuntu-keeper-composition-20261126/REVIEW.md) preserves actual pending first_seen and queued IDs through timer contention, then reconciles delivery and genuine healthy recovery. Incident/lock-refusal outcomes are not healthy readiness; delivery ACK alone is not recovery. Short lab timings are not launch choices.

The [alert module](../keeper/alerts.py) and [command](../scripts/keeper-alerts.py) inspect keeper health, the current journal and one explicitly selected recovery backup. They write a **separate alert state/outbox**, and can send sanitized events to a local test receiver. They never sign, submit transactions, read configured signer-file contents, repair a journal or approve a keeper for live use.

The original command is an unsigned one-shot tool; it installs no scheduler, service or notification channel. The separate [scheduling wrapper](KEEPER_SCHEDULING.md) coordinates reviewed timer invocations without changing that interface. Production ages, delivery destination, supervision and operating qualification still need review. The [day audit](../reports/keeper-day-audit-20261126/REVIEW.md) describes the current corrections and focused verification. The earlier [21-method receiver proof](../reports/keeper-alerts-20261126/REVIEW.md) retains its original source scope; neither record approves live-channel or sustained operation.

## Inputs and units

Use the original keeper configuration unchanged. Relative configuration/runtime paths resolve against `--working-directory`, matching the daemon's actual working directory; they are not resolved against the configuration file's folder. The configuration's original bytes and semantic digest remain unchanged.

| CLI input | Required value | Meaning |
| --- | --- | --- |
| `--config` | Current keeper configuration path | Health and current-journal identity |
| `--working-directory` | Absolute existing directory | Resolve relative input/runtime paths |
| `--backup-bundle` | Exact reviewed bundle directory | Select one backup explicitly |
| `--backup-manifest-sha256` | Reviewed 64-character SHA-256 | External manifest integrity pin |
| `--backup-config` | Original configuration used by that backup | Preserve its exact raw/semantic bindings |
| `--directory` | Separate protected alert directory | Persistent alert state and lock |
| `--max-health-age-seconds` | Integer, 1–31,536,000 seconds | Maximum health-file age |
| `--max-backup-age-seconds` | Integer, 1–31,536,000 seconds | Maximum backup capture age |
| `--pending-max-age-seconds` | Integer, 1–31,536,000 seconds | Grace since first sidecar observation |
| `--receiver` | Optional `http://127.0.0.1:PORT/alerts` | Local test delivery only |
| `--allow-dry-run` | Optional flag | Assess the matching dry-run health profile |
| `--max-seconds` | Optional integer, 1–120; default 60 | Cooperative processing budget |
| `--max-bytes` | Optional integer, up to 64 MiB; default 16 MiB | Journal/backup byte bound |

The three age inputs have **no selected production defaults**. Choose and review them for the real polling interval, confirmations, backup frequency and response expectations. Stronger existing metadata/freshness checks remain in force. Backup age measures capture age; it does not establish latest canonical chain state or a complete backup schedule. Execution is POSIX-only; Windows permissions are not qualified here.

For a restored keeper, `--config` may identify its reviewed new runtime paths while `--backup-config` remains the separate original configuration that created the selected bundle. Deployment/profile identity must still agree. Do not edit the original configuration to make a backup pass.

The Python API is `keeper.alerts.run_once(config_path, *, working_directory, backup_bundle, backup_manifest_sha256, backup_config_path, directory, max_health_age_seconds, max_backup_age_seconds, pending_max_age_seconds, receiver=None, allow_dry_run=False, now=None, max_seconds=60, max_bytes=16777216)`. `now` supports controlled verification; normal operators omit it. Results contain fixed reason codes, counters and event IDs, with `readiness_approved: false` throughout. The CLI returns nonzero for incidents, undelivered events or refusal; inspect its sanitized JSON rather than interpreting an HTTP acknowledgement as keeper readiness.

Example template; replace every placeholder with separately reviewed inputs:

```text
python3 -B scripts/keeper-alerts.py \
  --config <CURRENT_CONFIG> \
  --working-directory <ABSOLUTE_DAEMON_WORKING_DIRECTORY> \
  --backup-bundle <REVIEWED_BUNDLE_DIRECTORY> \
  --backup-manifest-sha256 <REVIEWED_MANIFEST_SHA256> \
  --backup-config <ORIGINAL_BACKUP_CONFIG> \
  --directory <SEPARATE_PRIVATE_ALERT_DIRECTORY> \
  --max-health-age-seconds <REVIEWED_HEALTH_AGE_SECONDS> \
  --max-backup-age-seconds <REVIEWED_BACKUP_AGE_SECONDS> \
  --pending-max-age-seconds <REVIEWED_PENDING_OBSERVATION_SECONDS> \
  --receiver http://127.0.0.1:<LOCAL_TEST_PORT>/alerts
```

## State, delivery and recovery

The alert directory must be owned by the invoking user with mode `0700`, under a protected parent. Its only supported files are `state.json` and the persistent `alert.lock`, both private. The outbox is stored inside the atomic state document. Keep this directory outside the keeper journal's parent and separate from configuration, health, lock, backup and signer paths. Linked/aliased files and unexpected directory entries are refused. Never replace the keeper's own lock or journal with alert files.

Input regular files and their direct parents must be owned by root or the invoking user and must not be group/world-writable. The account also needs read access; this change grants none. Use the existing reviewed ownership model rather than broadening journal or signer permissions to accommodate monitoring. Configuration and health capture are each limited to 1 MiB; alert state is limited to 1 MiB.

An incident receives a stable event ID and is durably queued **before** delivery. Repeated observations and process restarts retain that ID. Successful delivery removes the event only after an exact positive acknowledgement and a subsequent state commit. If the receiver accepted an event but its reply was lost, the next invocation sends the **same ID** again. This is **at-least-once delivery**: the receiver must deduplicate by `event_id`.

Each invocation attempts at most **eight** deliveries in total. Capacity is **64 queued events**. Already-durable events drain before new transitions are queued, so a full outbox can make progress when delivery recovers. If insufficient room remains, `outbox_full` refuses the new transition without discarding existing events. Retain the directory and resolve delivery/backpressure; deleting it loses deduplication and pending-observation history.

An interrupted atomic write can leave a `.state.json.*.tmp` file. The next invocation deliberately refuses unexpected entries. Stop/fence the **observer**, preserve the committed state, lock, temporary files and metadata, then have the matching-schema state reviewed. Only after review, archive the identified orphaned temporary file outside the alert directory with private permissions. Keep the committed state and lock inode; never automatically delete files or promote temporary data into committed state. Rerun with the same reviewed inputs.

If `state.json` is missing, the tool initializes a fresh observer even when a lock file remains. That cannot reconstruct previous events or the pending clock. Preserve the directory and recover separately secured observer state under review; do not invoke blindly or describe a new baseline as uninterrupted history. The keeper-journal backup tool does not back up this separate alert state. Use the [sidecar recovery tool](KEEPER_SIDECAR_RECOVERY.md) to capture the committed alert bytes, selected-backup record and selected generation together. Its fresh restore plan preserves event IDs, sequence and pending time; it neither reconstructs already lost history nor initializes or installs a live observer.

Local delivery accepts only the literal IPv4 loopback endpoint and exact `/alerts` path. Credentials, alternate hosts, proxies, redirects, query parameters and fragments are unsupported. The combined response header/body limit is 8,192 bytes. Delivery has an absolute **two-second deadline**, further bounded by the remaining invocation budget. A successful HTTP 2xx response must contain exactly:

```json
{"event_id":"<THE_SAME_64_CHARACTER_EVENT_ID>","accepted":true}
```

Wrong IDs, extra acknowledgement fields, malformed responses, redirects and timeout/connection failures do not acknowledge the event. Payloads contain only fixed event fields and reason codes; configuration, RPC URLs, pending calldata, arbitrary error text and signer material are excluded.

## Pending transactions and identity changes

Keeper journals contain no precise submission timestamp. The pending timer starts when this sidecar **first observes the intent**. It survives restarts, hash publication, unavailable inputs and a snapshot invalidated by its final consistency check. Repair an unavailable input and rerun with the same directory; do not reset the clock. A validated different intent starts a new clock; only a validated current journal explicitly reporting no pending intent clears it. Hashless or inconsistent records still alert immediately. The timer cannot establish how long a transaction existed before monitoring began.

A known-hash `awaiting_receipt` record can receive finite grace while waiting normally, with a verified backup and no disallowed health reasons. A first pending cycle may lack earlier execution/confirmation observations or a successful cycle. Missing observations are not runtime assurance: any **present** invalid, stale or mismatched proof still alerts. **The underlying health verdict stays unready.** Grace never authorizes signing, resending or skipping receipt recovery; prolonged observed waiting alerts. Existing incidents are not cleared or given recovery events merely because the current classification becomes `pending_grace`.

Current and backup deployment identities use the same validated normalization. An omitted `accounting_model` means `shared-pools-v2`; writing that same explicit default does not invent a different intent or incompatible backup. An earlier observer's `None`-model fingerprint is normalized one way to that canonical identity without changing `first_seen`. Other genuinely different validated intents do not inherit its clock.

Configuration, source or observation-policy changes produce an identity-change incident while preserving queued events. Source scope includes the thirteen daemon files plus four observer/tool files: `keeper/alerts.py`, `scripts/keeper-alerts.py`, `keeper/recovery_bundle.py` and `scripts/keeper-recovery.py`. Both maps are checked again before publishing an observation. These are local file hashes, not loaded-code attestation. Scope changes are notification transitions, not adoption approval. Recovery requires a subsequent stable evaluation with fresh valid health **and** the selected verified backup; missing, stale, changed or malformed inputs cannot produce it.

Backup rotation is explicit: supply each new reviewed directory and manifest pin with its matching original configuration. Changing that selection alone does not invalidate the observer scope, erase the outbox or restart the pending clock. The tool never selects the newest folder automatically.

## Scheduled observation

Under the [pinned scheduling policy](KEEPER_SCHEDULING.md), automatic backup jobs create distinct generations, verify their exact bytes and publish one explicit `selected.json` path/pin record. Scheduled observation uses only that record; it never scans for the newest folder. This local producer handoff is not independent authentication or an off-host backup. The original CLI still requires its explicit bundle and manifest pin.

Only explicit scheduler `init` creates its initial directories and observer state. Later scheduled observation refuses a missing/corrupt committed selection or observer state, unexpected temporary residue or a changed policy/configuration/source pin; it never silently initializes a new pending clock or outbox. Preserve the exact files and follow the recovery procedure. A scheduler pin/state refusal is supervisor-visible; it cannot itself guarantee an HTTP incident.

Backup capture remains independent of observer-state failure, and observation remains independent of backup capacity or unrelated generations. A failed capture/verification keeps the selected backup available for normal stale/integrity checks. Operational `rebind` requires both exact old/new policies and the same configuration, runtime/output paths and source identities; it preserves the selected generation/pin and every observer-state byte. Next observation still applies its normal incident/recovery rules.

## Release and supervision boundary

The earlier bounded snapshot keyword in `keeper.ops.health_check` preserves the original readiness logic and omitted-keyword behavior. That change affected `ops.py`; the day audit's Cast interruption correction also changes a daemon source identity. Matching writer/checker adoption is separate. Retain old health files, bundles and journals under their original release. Verify old bundles with their preserved matching release and original configuration; never rewrite hashes to satisfy a new release. Producer hashes retain provenance and are not automatically required to equal the current producer. No journal codec, financial right, authority or keeper limit changes.

Protected local ancestors and the invoking user remain trusted; an advisory lock is not multi-host fencing. The backup reader now opens nonblocking so a substituted FIFO is refused before its type check can hang. This does not interrupt kernel/filesystem reads or fsync stalls, or eliminate every same-user race. The work budget remains cooperative; use separately reviewed external supervision for a hard overall timeout. The local HTTP exchange has its own actual delivery deadline.

Off-host scheduling, remote delivery, real channel acknowledgement/alerts, sustained outages and production adoption remain separate qualification work. Source publication starts nothing and changes no existing service, journal, environment or paused heartbeat.
