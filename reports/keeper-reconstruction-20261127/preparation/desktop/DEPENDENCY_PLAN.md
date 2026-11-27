# Unsigned reconstruction kit: fixed c821 fixture scope

The five native package files alone cannot reconstruct a lost host. The fixed
kit adds the exact original fixture configuration, original scheduling policy,
matching reviewed release and independently retained trust. It preserves the
native journal and sidecar formats. It contains no signer file or password.

This campaign uses a clean filesystem on the existing Ubuntu machine; it does
not prove a physical second host, separate disaster domain, durability, old-host
fencing, current canonical transactions or permission to start a keeper.

## Exact private inventory

The kit directory has exactly49 regular files and no extra tree entries:

| Private relative path | Required bytes / meaning |
| --- | --- |
| `SOURCE_MANIFEST.json` | Original24910-byte c821 manifest, pinned below |
| `source/<original41 source_files names>` | Exact41 original release members;772088bytes total |
| `references/keeper-config.json` | Exact5254-byte original fixture configuration |
| `references/policy.json` | Exact original fixture policy, including unchanged900-second operating freshness |
| `package/manifest.json` | Original outer sidecar manifest |
| `package/selection.json` | Original selected generation and nested manifest identity |
| `package/alert-state.json` | Original outbox IDs, sequence, pending `first_seen` and observations |
| `package/selected/manifest.json` | Original journal backup manifest |
| `package/selected/journal.json` | Original exact journal, including pending, nonce and accounting |

The original41-member reviewed release inventory is retained in full; its four
test-source members remain inert. No fixture builder, test method, keeper,
scheduler or observer is executed by kit assembly/preflight. This is a finite
reproducible release set, not a claim that every member is required by the two
native recovery entrypoints. OS interpreter/stdlib and shared-library inputs are
separate recorded dependencies and are not operational package contents.

Source bytes can be copied locally from the exact trusted Git blobs after every
length/hash check against the independently pinned source manifest. The server
exports only the two already reviewed fixture configuration/policy files; it
does not export source41, signer files or its current journal. Both reference
files and the native package remain private outside the checkout and Git.

## Independent trust

Retain these values before receiving incoming bytes. An incoming manifest is
not its own trust anchor. Source trust is retained in the historical c821/c823
published build receipts; package/reference trust is retained in the published
c821 `SOURCE_RESULT.json`, raw SHA-256
`9bec125bedd73b6f80cb3f316a7822aa09aeb9198927ca8d901c476f3798c371`.

| Exact object | Independently retained SHA-256 |
| --- | --- |
| Original source manifest | `c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08` |
| Original configuration raw bytes | `1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8` |
| Original policy raw bytes | `7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba` |
| Outer sidecar manifest | `a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b` |
| Nested journal manifest | `911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1` |

The fixed report helper `reconstruction_kit.py verify --kit PRIVATE_KIT
--proof NEW_PRIVATE_PROOF` performs closed-inventory, exact length/hash and
source13/source19 binding checks. It reads actual saved files twice under a
60-second budget, with1MiB per-file and2MiB total raw bounds. The separate proof
is capped at16KiB and writes exclusively outside the kit. It contains hashes,
lengths, actual time and false readiness/adoption flags. It neither replaces
native validation nor attests loaded interpreter code, Windows ACLs or live
single-writer ownership.

## Reconstruct original logical paths, preserve exact bytes

Native sidecar verify/restore checks the original policy's absolute
`configuration`, `working_directory`, `scheduler_directory`, `backup_directory`
and `alert_directory` paths. The package also binds those exact three sidecar
logical paths. Native `rebind` permits selected operational settings, not a
configuration/source/path migration. Do not rewrite or reserialize the policy,
configuration, manifest, selection or alert state to make a new path pass.

Create a disposable clean root and recreate only the required logical directory
layout inside it. Supply copied original configuration and policy at the original
logical names. Copy the41 reviewed source files into the original release path
inside that root. These paths then resolve entirely inside the reconstructed
root; the old host release/runtime must not be visible to the worker. The new
unsigned review outputs belong to separate new protected directories.

`scheduling._load` requires the declared working directory and protected parents
for scheduler/backup/alert directories. It validates configured journal/health/
lock/keystore/password paths for aliases and existing-file metadata. For native
verify/restore, the original journal, health, scheduler/alert state and original
lock files may be absent: captured state comes from the package. Do not invent
an empty current journal or reset observer state. Exclude both signer contents;
if signer-path masks are used, make two distinct root-owned unreadable empty
regular files and prove the unsigned worker cannot read them.

Keep the system interpreter and allowlisted runtime dependencies read-only,
record versions and hashes, drop worker privilege/capabilities, deny external
network families, and separately bound output, elapsed work and service life.
The host's existing runtime is an explicit dependency; recording its allowlist
does not turn this into a complete OS recovery image.

## Four existing native operations only

Run these from the reconstructed matching release with exact reviewed logical
paths. `CONFIG`, `POLICY`, `BUNDLE` and outputs are path placeholders, not data to
invent. The nested journal bundle is `BUNDLE/selected`.

```text
python3 -B scripts/keeper-recovery.py verify --config CONFIG --bundle BUNDLE/selected --manifest-sha256 911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1 --max-age-seconds 86400 --minimum-created-at 1795723324
python3 -B scripts/keeper-recovery.py restore --config CONFIG --bundle BUNDLE/selected --manifest-sha256 911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1 --max-age-seconds 86400 --minimum-created-at 1795723324 --output NEW_JOURNAL_REVIEW
python3 -B scripts/keeper-sidecar-recovery.py verify --policy POLICY --policy-sha256 7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba --bundle BUNDLE --manifest-sha256 a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b --max-age-seconds 86400 --minimum-created-at 1795723324
python3 -B scripts/keeper-sidecar-recovery.py restore --policy POLICY --policy-sha256 7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba --bundle BUNDLE --manifest-sha256 a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b --max-age-seconds 86400 --minimum-created-at 1795723324 --output NEW_SIDECAR_REVIEW
```

Default native16MiB/60-second budgets and any stricter original policy budgets
remain. Use actual wall-clock time and original capture1795723324. At desktop
planning time1795781857 the age was58533seconds, leaving27867seconds under86400;
this is not execution evidence. Abort if the real clock exceeds the reviewed
age. Do not extend that allowance, recapture or change a timestamp silently.
The unchanged900-second operating freshness is exceeded; its approval remains
false. The c821 pending hash/accounting/outbox is synthetic, not chain truth.

Record one separate missing-dependency refusal in a fresh negative root, without
repairing/promoting it. Preserve any failure/partial output, then run the planned
successful composition only in its separate complete root. No old test bodies
or previous application compositions are rerun.

Compare exact journal bytes, pending intent/hash/nonce/cost/anchors, selected
generation, queue IDs/sequence/first_seen, both plan hashes and every false flag.
Check that restored lock files are new empty distinct coordination inodes, not
recovered ownership. Stop the new unit and verify its group is empty. Preserve
all old source/reference/package/runtime metadata and unrelated host states.

No keeper cycle, scheduler initialization, observation/delivery, RPC, signing,
transaction, public deployment, website/service adoption, old journal install,
Anvil8902 change or desktop-heartbeat restart belongs to this rehearsal.
