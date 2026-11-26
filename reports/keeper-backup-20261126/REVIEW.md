# Keeper backup and restore preparation — 26 November 2026

The unsigned tool preserves **exact journal bytes** and prepares restoration into a **fresh directory**. Configuration and signer material stay separate; no daemon, signing, network, installation or existing-journal replacement is involved.

**Thirty-three distinct NEW methods pass** in separate Windows and Ubuntu stages. No previously green body or financial journey repeats. Off-host adoption, canonical recovery and release approval remain open.

## Implemented behavior

The [core module](../../keeper/recovery_bundle.py) and [CLI](../../scripts/keeper-recovery.py) provide three operations:

| Operation | Result | Boundary |
| --- | --- | --- |
| `backup` | Exact `journal.json`, followed by completion `manifest.json` | Requires explicit daemon working directory; never resolves relative state paths from the configuration's folder |
| `verify` | Integrity, identity, capture-age and reviewed-floor checks | Requires an externally reviewed manifest digest and the separately secured original configuration |
| `restore` | Exact `keeper-state.json`, followed by `RESTORE_PLAN.json` | Fresh directory only; no installed configuration, signer, lock, health record or live-ready approval |

The manifest binds both raw-file and canonical semantic configuration digests, the deployment/profile identity and the existing thirteen-file keeper health source identity. Producer hashes record provenance only. These are local file identities, **not running-code attestation**.

Original pending hash or hashless intent, captured fee-review schema, nonces, spending, receipt anchors, metadata records, worker cursors, confirmation evidence and jitter history retain their original bytes. Missing legacy fee reviews remain missing and explicitly require manual review; the tool neither invents them nor reprices saved transactions using today's limits.

Known journal shapes and types are checked without constructing `Keeper`. Unknown fields, obvious secret-bearing fields and journal HTTP URLs are refused rather than stripped. Configured signer files are checked for path/inode aliases where applicable but their contents are not read or copied. Arbitrary attacker-controlled bytes cannot be certified universally secret-free; the configured-file boundary and reviewed journal envelope define the supported scope.

Stable descriptor/path identity checks and repeated journal/configuration/source reads refuse a changing snapshot without rolling it back. Publication uses exclusive files and writes its completion marker last. POSIX parents must be protected, and output directory identities are pinned around descriptor-relative writes. Failed publication may leave incomplete, unapproved output; originals are never deleted or overwritten.

The new tool's default package budget is 16 MiB, configurable up to 64 MiB. Its 60-second default is a **cooperative** filesystem/processing budget, configurable within the tool's bounds; it cannot interrupt a kernel or filesystem hang. These new sidecar limits change no keeper gas, RPC, transaction, daily-spend or financial safeguards. Ten fixed refusal codes give operator diagnostics without echoing private values or paths. Procedure and inputs are documented in the [operator manual](../../docs/OPERATOR_MANUAL.md) and [recovery guide](../../docs/KEEPER_RECOVERY.md).

## Verification actually executed

| Stage | Actual result | Scope |
| --- | --- | --- |
| [Windows selection](evidence/windows/RESULT.json) | 31 invocations: 30 passes, one symlink skip; 8.453 seconds | New temporary fixtures, static published c811 journal vectors and guarded offline CLI composition |
| [Ubuntu c812](evidence/ubuntu/RESULT.json) | Three first successful completions; zero skips | Two POSIX-only methods plus the symlink method skipped on Windows; UID/GID 65534, no supplementary groups |

The [selection record](evidence/TEST_SELECTION.json), [pre-execution record](evidence/windows/PREEXECUTION.json) and [Ubuntu source manifest](evidence/ubuntu/SOURCE_MANIFEST.json) retain exact source and method identities. Core SHA-256 is `fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268`; CLI is `450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf`; test source is `e7ba697edee57e08dcf4e40e55633a2cb82b76ae592a8ebea2489c66aea016d9`.

Checks cover whole-byte round trips, hashless/known-hash pending transactions, captured zero-tip fees, settled anchors and large spend values, retained worker/timer state, type substitutions, duplicate/nonfinite JSON, trusted-pin/configuration/source changes, age/floor refusals, aliases, source replacement during reading, incomplete publication and safe CLI diagnostics. The fsync refusal is an injected failure, not a physical-disk or power-loss experiment.

The Ubuntu capsule creates only its new fixed source/runtime tree. Sources and static data are root-owned and read-only; only private temporary test files are writable by the child. Ninety-second work, 64 KiB combined output and bounded group cleanup retain complete child-wait evidence. Source maps match before and after, and the child group is empty. No Anvil, Cast, service unit, real signer or operating journal is used.

The separate [saved-result review](verification/POST_REVIEW.json) binds the original logs, exact source maps, raw Ubuntu capture and disjoint method selections. The [publication checks](verification/PUBLICATION_CHECKS.json) cover current inventory/Todo, links, preserved historical evidence and source hashes without executing test bodies. The final [artifact manifest](ARTIFACTS.json) pins the published report files.

## Host preservation: original comparison retained

The [original host comparison](verification/HOST_COMPARISON.json) remains **NONPASS**, with five observer lifecycle differences and one disclosed invocation change. It is not rewritten as “five states identical.”

Separate [read-only reconciliation](verification/HOST_RECONCILIATION.json) identifies the existing observer as a successful `Type=oneshot` service: an in-progress invocation finishes, its process/group disappears and its active timer returns from running to waiting. The captured window includes the corresponding `UNIT_SUCCESS` and `UNIT_STARTED` records, using the [systemd v255 message definitions](https://github.com/systemd/systemd/blob/v255/src/systemd/sd-messages.h). The observed transition follows [oneshot service semantics](https://www.freedesktop.org/software/systemd/man/255/systemd.service.html#Type=). Other compared properties remain unchanged. The isolated capsule performs no service or configuration writes.

## Remaining boundaries

Capture age and optional nonce/time floors do not establish latest chain state. An ordinary backup is a coherent point-in-time snapshot, not proof of signer fencing. Real adoption still requires stopping/fencing the old writer and restart paths, separately securing configuration and signer material, reviewing new runtime paths, reconciling canonical transactions/nonces/fees and running the reviewed stock recovery. A same-host lock does not fence another host.

Windows ACL enforcement, hostile same-UID/ancestor changes, physical durability, actual off-host transfer/restore, alert delivery and sustained operation are not qualified here. Existing environments, Anvil8902, journals, websites, signer restrictions and the paused heartbeat remain unchanged. The previous c811 NONPASS and missing physical after-reads retain their original scope.

The new [production inventory](FUNCTION_INVENTORY.json) records **185 Python files/2,057 named definitions/278 lambdas**. Frozen F6 maps remain 61/39/4 with 1,021 ABI rows. Daemon/health source identity, existing journal/checkpoint semantics, permissions and financial limits are unchanged; publication is not operating-source adoption or production approval.
