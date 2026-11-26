# Keeper alerts: one-shot observation and local delivery

The [alert module](../keeper/alerts.py) and [command](../scripts/keeper-alerts.py) inspect keeper health, the current journal and one explicitly selected recovery backup. They write a **separate alert state/outbox**, and can send sanitized events to a local test receiver. They never sign, submit transactions, read configured signer-file contents, repair a journal or approve a keeper for live use.

This is an unsigned one-shot tool. It installs no scheduler, service or notification channel. Production ages, delivery destination, supervision and operating qualification still need review. The [qualification report](../reports/keeper-alerts-20261126/REVIEW.md) records21 NEW Ubuntu method passes with a real receiver inside a private network. This finite rehearsal is not live-channel or sustained-operation approval.

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

Local delivery accepts only the literal IPv4 loopback endpoint and exact `/alerts` path. Credentials, alternate hosts, proxies, redirects, query parameters and fragments are unsupported. The combined response header/body limit is 8,192 bytes. Delivery has an absolute **two-second deadline**, further bounded by the remaining invocation budget. A successful HTTP 2xx response must contain exactly:

```json
{"event_id":"<THE_SAME_64_CHARACTER_EVENT_ID>","accepted":true}
```

Wrong IDs, extra acknowledgement fields, malformed responses, redirects and timeout/connection failures do not acknowledge the event. Payloads contain only fixed event fields and reason codes; configuration, RPC URLs, pending calldata, arbitrary error text and signer material are excluded.

## Pending transactions and identity changes

Keeper journals contain no precise submission timestamp. The pending timer therefore starts when this sidecar **first observes the intent**. It survives restarts and publication of that intent's transaction hash. It cannot establish how long a transaction existed before monitoring began. Hashless or inconsistent pending records raise an immediate incident.

A known-hash `awaiting_receipt` record can receive the explicit observation grace only when all unrelated health, source, runtime, schema and identity checks remain valid and the backup verifies. Grace means normal waiting; **the underlying health verdict stays unready**. It never authorizes signing, resending or skipping receipt recovery. Prolonged observed waiting becomes an incident.

Configuration, source or observation-policy changes produce an identity-change incident while preserving queued events. Updating the stored observation scope is a notification transition, not approval to adopt software. A subsequent stable evaluation may queue recovery only when matching health is fresh and valid **and** the explicitly selected backup verifies. Missing, stale, changed or malformed inputs cannot generate a healthy recovery.

Backup rotation is explicit: supply each new reviewed directory and manifest pin with its matching original configuration. Changing that selection alone does not invalidate the observer scope, erase the outbox or restart the pending clock. The tool never selects the newest folder automatically.

## Release and supervision boundary

The bounded snapshot keyword added to `keeper.ops.health_check` preserves its existing readiness logic and omitted-keyword behavior. It changes one of the thirteen health-source identities. Matching writer/checker source and newly reviewed backups must be adopted together; retain older health files, backup pins and journals under their original release. No journal codec, financial right, authority or keeper limit changes.

Source hashes identify local files, not the binary running elsewhere. Protected local ancestors and the invoking user remain trusted; an advisory lock is not multi-host fencing. Backup verification reuses the existing producer reader, including its replacement-race boundary. Filesystem/kernel stalls are not preempted by cooperative budgets. Use external process supervision for a hard overall timeout; the local HTTP exchange has its own actual delivery deadline.

Off-host scheduling, remote delivery, real channel acknowledgement/alerts, sustained outages and production adoption remain separate qualification work. Source publication starts nothing and changes no existing service, journal, environment or paused heartbeat.
