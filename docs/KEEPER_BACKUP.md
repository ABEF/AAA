# Keeper journal backup and restore preparation

Use the [alert observer](KEEPER_ALERTS.md) to check one explicitly selected
bundle's age and integrity against its externally retained manifest pin and
separate original configuration. Rotation never selects the newest folder
automatically. The [day audit](../reports/keeper-day-audit-20261126/REVIEW.md)
reviews the combined backup, recovery and alert paths. Current producer and
daemon-source changes require separate reviewed adoption; preserve older
bundles, original configurations and release pins rather than rewriting them.

Use `scripts/keeper-recovery.py` to capture exact keeper journal bytes, verify a
reviewed backup and prepare an unsigned restore folder. Existing journals,
configuration, health files and locks remain untouched. The tool performs no
RPC requests, signing, installation or service actions. For recurring unsigned
invocations, use the separate [scheduling procedure](KEEPER_SCHEDULING.md);
the original backup/verify/restore CLI remains one-shot and installs nothing.

The journal carries pending intent/hash, original fee reviews, nonce, spending,
receipt anchors and scheduling/worker state. Ownership, LP and reward balances
remain in the contracts. Use the separate [history recovery procedure](HISTORY_RECOVERY.md)
for API history databases.

The older `keeper.ops snapshot` / `verify-snapshot` commands provide diagnostic
normalized-state integrity/age evidence. They are **not** this exact-byte backup
and restore package. Use `keeper-recovery.py backup/verify/restore` for current
review-only restoration preparation; neither interface authorizes adoption.

## Scheduled capture and local selection

A reviewed, explicitly pinned scheduler policy may create and verify a fresh
generation before atomically selecting its exact path/manifest pin. It never
chooses the newest directory, edits an old bundle or copies signer material.
Automatic local selection does not replace independent retention of the
manifest pin, original configuration, matching release or off-host backup.

Capacity counts retained generations, including partial attempts. There is
no automatic deletion: fence the relevant scheduled jobs, preserve/review
evidence and archive approved generations outside the capture directory.
Never remove the selected generation as an unreviewed cleanup step. Capacity
refusal or broken observer state does not reset a journal or observer clock.
Backup jobs do not initialize/repair the observer; observation of the selected
backup can continue while new capture is refused.

Capture/verification failures leave the earlier selection unchanged. A
selection rename followed by failed directory synchronization has an uncertain
old/new commit; preserve both generations and inspect the committed record.
Do not blindly roll back, promote temporary files or repeat initialization.
See [scheduler recovery and policy rebinding](KEEPER_SCHEDULING.md).

## What to keep separately

- Keep the **exact original configuration file** in a separately secured backup.
  Its raw bytes and canonical configuration digest are bound into the manifest;
  its contents and credentialed RPC URLs are not copied into the package.
- Keep encrypted signer material and its password/secret separately. The tool
  never opens configured keystore or password files; backup checks only their
  path/file metadata for dangerous aliases.
- Store the manifest SHA-256 printed by backup in a separately trusted record.
  Supply that digest explicitly for verification/restore. A checksum checks
  selected bytes; it does not authenticate whoever supplied both file and hash.
- Treat actual journal packages as private operational data. Do not commit them
  or configuration/credentials to Git.

## Commands

These paths are examples. Use real, reviewed paths without symlink/junction
aliases, a protected local output parent and a new output name each time.
`--working-directory` must be the keeper's actual working directory: relative
runtime paths are interpreted from there, independently of the config location.
Run the tool from the matching reviewed release. Source hashes come from that
tool's own release directory; `--working-directory` selects runtime paths only
and does not attest which release the running service loaded.

```bash
python3 scripts/keeper-recovery.py backup \
  --config /secure/popl/keeper-original.json \
  --working-directory /opt/popl/releases/release-001 \
  --output /srv/popl-backups/snapshot-001
```

The new private directory contains only `journal.json` and `manifest.json`.
The completion manifest is written last. No lock, health file, config or signer
material is bundled. Drift detected during the repeated journal/configuration/
release checks refuses capture; no automatic retry or rewrite occurs. A stable capture is a point-in-time
snapshot, not a guarantee that no later transaction was submitted.

Set the digest from your separately reviewed backup record before these calls;
the placeholder below is intentionally invalid until replaced.

```bash
MANIFEST_SHA256="paste-the-reviewed-64-character-lowercase-digest"

python3 scripts/keeper-recovery.py verify \
  --bundle /srv/popl-backups/snapshot-001 \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --config /secure/popl/keeper-original.json \
  --max-age-seconds 86400

python3 scripts/keeper-recovery.py restore \
  --bundle /srv/popl-backups/snapshot-001 \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --config /secure/popl/keeper-original.json \
  --max-age-seconds 86400 \
  --output /srv/popl-recovery/review-001
```

`86400` is an example capture-age policy in seconds; choose it explicitly.
Verification needs the same original configuration bytes, even when formatting
changes preserve their JSON meaning. It does not resolve old runtime paths or
open signer files. The selected thirteen local daemon source-file identities
must match; producer tool hashes retain provenance without silently relabelling
older packages as produced by a newer tool.

Restore creates only `keeper-state.json` and `RESTORE_PLAN.json` in a fresh
private directory. The journal remains byte-identical, including hashless
intent, previous fee envelopes, UTC spending days, confirmation/jitter timers
and worker cursors. Missing legacy fee reviews remain missing and require
manual reconciliation. Restore never invents fees, resets a nonce or prunes data.

## Inputs and units

| Input | Used by | Meaning / example |
| --- | --- | --- |
| `--config` | All | Separately secured original JSON file |
| `--working-directory` | Backup | Actual keeper working directory; required |
| `--output` | Backup/restore | New directory under an existing protected parent |
| `--bundle` | Verify/restore | Complete two-file backup directory |
| `--manifest-sha256` | Verify/restore | Independently retained 64 lowercase hex characters, without `0x` |
| `--max-age-seconds` | Verify/restore | Required positive integer; capture age only |
| `--minimum-created-at` | Verify/restore | Optional trusted earliest capture; UTC Unix seconds, default `0` |
| `--minimum-next-nonce` | Verify/restore | Optional independently reviewed nonce floor; never guessed |
| `--max-bytes` | All | Journal plus manifest/plan ceiling: default `16777216`, at most `67108864` |
| `--max-seconds` | All | Cooperative work budget: default `60`, range `1..300` |

Configuration and manifest/plan JSON have separate 1MiB ceilings. Oversized or
unsupported input is refused without truncation. These are new tool resource
bounds; keeper gas, fee, financial, history and snapshot operating limits stay
unchanged. The work budget checks between bounded operations; it cannot interrupt
a blocked kernel read/fsync or guarantee a hard process deadline. Use reviewed
local storage and existing host supervision. Windows supports offline file
preparation; live atomic-journal capture and Unix permissions need Ubuntu checks.
Linux outputs request directory/file modes0700/0600. Windows NTFS ACLs are not
qualified by these checks and require separate review.

The current reader also opens nonblocking and checks the descriptor type,
preventing a FIFO substituted after `lstat` from blocking before validation.
Regular-file snapshot checks and source identities remain. This is not a hard
kernel-I/O deadline, protection from a hostile same-user process or host fencing.

The Cast interruption correction changes one of the thirteen daemon source
identities; reader hardening changes the backup producer's provenance hash.
Verify old packages using their separately preserved matching release and exact
original configuration. Do not rewrite bundles, source hashes or captured fee
reviews to fit new software. A new writer/checker release needs separately
reviewed adoption and canonical reconciliation, with original pending journals
retained. Producer hashes record which tool created a package; they do not
silently relabel it or introduce a current-producer equality requirement.

## Before adopting a restored journal

1. Fence the old keeper, Cast descendants and automatic restart paths. Local
   file locking and this unsigned tool do not establish cross-host fencing.
2. Preserve the original package, digest, configuration, release and logs.
3. Review the new host's paths, permissions, provider and separately secured
   signer material. The old config may still point at the old journal; prepare
   and review a separate new runtime configuration rather than launching it
   unchanged or overwriting the original.
4. Reconcile canonical receipts, both nonce getters, original fee reviews and
   spending since capture using the [stock recovery procedure](KEEPER_RECOVERY.md).
   A fresh capture time or nonce floor cannot prove newest chain state.
5. Run one unsigned stock cycle using
   `python3 -m keeper.monitor --config NEW_REVIEWED_CONFIG --once`, without
   `--live`. Inspect state/health and authorize live operation separately.
   Hashless intent remains blocked until the existing explicit original-hash
   reconciliation procedure completes. Never initialize a used sender or
   blindly resend.

With a confirmed saved receipt, the first unsigned `--once` cycle can clear
pending and book the original nonce/cost correctly, then exit `1` with health
`degraded`: it deliberately leaves fresh execution/reference metadata for a
later cycle. Check the exact journal, receipt and health reason. This exit code
alone is not permission to clear state or resend. A further unsigned `--once`
cycle must obtain fresh metadata before reporting `dry_run_v2`; errors remain
blocked. The health configuration digest belongs to the separately reviewed new
configuration, while bundle verification still requires the original bytes.

Every restore plan keeps live readiness, canonical verification, old-signer
fencing, installation and restart flags false. The tool supports its explicit
accounting7/custody5 profile; unsupported versions/unknown journal fields require
reviewed reader support, not edits to saved profile labels. Launch royalty policy
and existing economic rights remain unchanged.

Backup verification checks the supported envelope and file integrity; the
daemon's full configuration, runtime and canonical admission remain separate.

## Actual Ubuntu adoption evidence

The [26 November rehearsal](../reports/ubuntu-backup-recovery-20261126/REVIEW.md)
uses a new isolated Ubuntu runtime and real locally signed known-hash pending
transaction. Backup/restore preserve exact bytes; the target runs only unsigned
`--once`, with signer files inaccessible, then reaches `dry_run_v2`. Canonical
nonce, fee/day/anchor accounting is applied once; initial/included/final NFT,
LP and reserve vectors match. This fee-empty harvest is not a new allocation
or conversion qualification. All existing environments stay unchanged.

Capture evidence while dependencies are still alive. Stopping a systemd cgroup
can terminate its child node before the main process's `finally` block runs.
The failed c813 record stays intact; c814 captures the final vectors and
independent review before it permits teardown. Real off-host restore, signer
fencing, provider robustness and sustained operation remain separate.

## Refusals and partial output

| Fixed code | Review |
| --- | --- |
| `trusted_pin` | Exact trusted manifest digest and original bytes |
| `config_identity` | Original configuration formatting, identity and profile |
| `release_identity` | Matching reviewed local daemon source files |
| `backup_age_or_floor` | Capture age, trusted time/nonce floors and host UTC clocks |
| `source_snapshot_changed` | Source changed during capture/review; preserve it and use a new attempt |
| `package_inventory` | Exactly two expected regular files and their hashes |
| `journal_envelope` | Supported state shape and preserved original recovery records |
| `output_publication` | New output path, protected permissions and storage health |
| `resource_budget` | Explicit tool byte/time bounds; no automatic increase |
| `invalid_input` | Required values, safe paths, supported types and the guide above |

Errors contain fixed codes only. Do not loosen financial guards, reset state or
edit timestamps/hashes to make verification pass. A future capture timestamp
requires correct host clocks or waiting, not modifying the manifest. Failed
publication can leave partial or complete unapproved files; inspect and preserve
them, then use a new destination. Existing outputs are never overwritten or
automatically deleted.
