# Unsigned recovery kit and clean-filesystem Ubuntu reconstruction

Baseline `a418a567abbc3c0b7c6dd8425ef31306e8e48f17`,27 November2026.
Production is **not approved**. No production source, financial limit, native
backup format or existing environment was changed.

## What is now proved

The retained journal/sidecar package can be verified and restored using a
separately assembled private kit, without access to the original application
folders. Two fresh Ubuntu filesystem roots recreate the original logical paths
from desktop-held inputs. The successful workers cannot see the old host's
release, configuration, operating journals, selection, outbox, locks or signer
files as recovery inputs. OS runtime dependencies remain explicitly supplied
read-only from the existing Ubuntu host.

| Partition | Actual result |
| --- | --- |
| Complete private kit |49 files,820,029 bytes, independently pinned and reread |
| Desktop proof | `8411480086dfe7586308dd33edd5823b7500ccffc5a9e07e8dbfd2beb69fb39c` |
| Missing configuration | One native `verify` returns the expected fixed `invalid_input`; no restore output; worker0.162s |
| Complete reconstructed root | Four native journal/sidecar verify/restore operations return0; worker0.561s |
| Preserved records | Exact journal plus four sidecar payloads; pending/nonce/spending/anchor and queued event/sequence/first_seen history unchanged |
| Coordination | Two new empty private locks, distinct from each other and original lock inodes |
| Source and isolation |41 source files checked, source13/source19 unchanged, distinct physical source-manifest inode, no original host `/opt` bind |
| Runtime |18 explicit read-only mounts, including six diagnosed loader-name mappings;1192 regular stdlib files plus3 exact link-metadata entries |
| Signers and network | Both signer paths absent; nobody/empty capabilities; private network andAF_UNIX only; no RPC or transaction |
| Cleanup | Both c824 and c825 groups stopped/empty; original source/configuration/policy/eight retained files/locks unchanged |
| Existing services | Five states match,0 nonambient differences,1 disclosed periodic observer invocation-ID change |

These are **five native CLI invocations**, not five test methods. No unchanged
test bodies or earlier passing application compositions were rerun. The passed
missing-configuration case was reused when continuing the complete root.

## Kit contents and trust

The private kit contains the original source manifest,41 exact release files,
the exact original fixture configuration and policy, and the five original
package files. Source bodies came from pinned Git blobs after checks against
the original manifest. Only the two already pinned fixture references were
exported read-only from Ubuntu. No signer material, current journal or unrelated
source bodies were exported.

The independently retained source manifest pin is
`c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08`.
Reference/package trust comes from the previously published
[c821 source result](../keeper-sidecar-recovery-20261126/evidence/c821/fetch-6/SOURCE_RESULT.json),
raw digest `9bec125bedd73b6f80cb3f316a7822aa09aeb9198927ca8d901c476f3798c371`.
[Provenance](verification/TRUST_PROVENANCE.json) is separate from incoming data.
The finite41-member release includes four inert test-source files; none was run.

Raw kit/configuration/policy/package files and transport captures remain in a
new ignored private desktop store outside Git. The Linux lab's root-owned outer
directory is0700. Only explicitly allowlisted sanitized metadata and preparation
source are published. Windows storage access was checked for the two execution
accounts and retained system/administrator/owner rights; this is not general
Windows security or off-site encryption qualification.

The [report-bound preflight](preparation/desktop/reconstruction_kit.py) is fixed
to this fixture and its reviewed pins. It is not a new production backup format,
universal host installer or live adoption command. Native tool validation remains
required after the separate hash/inventory preflight.

## Actual isolation, runtime and time

Fresh `RootDirectory` trees contain copies reconstructed at the original logical
paths. The old application tree is not mounted. Native reads resolve inside the
new root; the witness verifies source bytes, distinct physical inodes, actual
mount information, absent original operating state and absent signers. The
reconstructed release, configuration and package files are read-only; new
review output has a separate writable subtree.

The interpreter, stdlib and individually enumerated ELF files are separate
read-only OS dependencies. The stdlib inventory includes cache bytes and exactly
three reviewed link records without following their targets; other selected
code-file links refuse. `-I -S -B` prevents site initialization and bytecode
writes. The actual runtime receipt and six precise library-name mappings are
hash-bound. No broad host `/lib`, `/etc`, `/home` or original `/opt` tree was added.
This is not a complete OS image, loaded-code attestation or second physical host.

The original capture1795723324 is unchanged. Actual ages were60,933seconds for
the missing-configuration case and61,340seconds for complete restoration.
Both exceed the unchanged900-second operating freshness policy. The explicit
86,400-second allowance applies only to this historical unsigned recovery
review. No clock override, new capture, timestamp rewrite or freshness approval
was used. Every native adoption/readiness/fencing/canonical flag remains false.

Existing native16MiB/60s budgets,2MiB compressed/expanded transfer bounds and
64KiB combined capture remain. The new OS inventory is separately bounded by
20s/8192 visited entries/128MiB; each worker retains180s hard life/256MiB memory.
These laboratory bounds do not qualify production cadence or maximum workloads.

## Corrections and original outcomes retained

1. The first OS inventory refused three ordinary Python symlinks. A bounded
   metadata-only inspection identified their exact names and targets. The
   corrected inventory records only those three as link metadata; application
   path/link protections were not relaxed.
2. Windows `DirEntry.stat()` supplied zero link/inode values. The new desktop
   checker now uses fresh `Path.lstat()` while retaining its single-link and
   reparse guards. One subsequent direct-helper refusal had no captured cause;
   it is **not retrospectively explained or relabelled**. A distinct traced
   invocation passed. Final safe stage/type diagnostics and a structured-argument
   CLI invocation passed with the authoritative proof above. Prior sources and
   outcomes are retained.
3. The first c824 root failed before worker execution: the dynamic loader lacked
   `libz.so.1` although its canonical file existed. Actual stderr and three
   bounded OS `ldd` inspections established six needed logical names. The fresh
   c825 root adds only those six file mounts with exact canonical hashes and
   host-resolution/inode checks. c824 remains **NONPASS**, with zero native calls;
   its incomplete/complete roots were not repaired or promoted.
4. After the c825 negative case passed, the original coordinator rejected its
   decimal timing fields. The separately pinned complete-only continuation
   embeds the original controller byte-for-byte and accepts timing decimals
   only in the exact3714-byte/SHA-bound saved negative result. Both durations
   must be finite/nonnegative; every other decode remains strict. The original
   ownership, source, runtime, empty-group, unit-absence and no-restart checks
   still execute. No installer, worker/input rewrite, `LAB_ID` relabelling or
   negative rerun occurred. Original refusal and continuation provenance remain.

See [original outcomes](review/ORIGINAL_OUTCOMES.json),
[loader diagnosis](verification/ELF_DIAGNOSTIC_SUMMARY.json),
[negative result](evidence/campaign-002/fetch-negative/RESULT-negative.json),
[complete result](evidence/campaign-002/fetch-complete/RESULT-complete.json) and
[independent saved reconciliation](verification/RECONSTRUCTION_VERIFICATION.json).
The witness directly compares restored raw bytes; saved independent review
rehashes private desktop inputs and reconciles recorded native/output hashes.
It does not independently fetch physical restored output bytes or re-execute
the native operations.

## Preservation and remaining qualification

All production Python/Solidity, source13/source19, workload plan, native formats,
financial/resource operating defaults and83 Todo IDs/statuses remain unchanged.
Reuse the [191-file/2,137-definition/279-lambda inventory](../keeper-sidecar-recovery-20261126/FUNCTION_INVENTORY.json):
F6 remains61/39/4 source/dependency/control maps and1,021ABI rows. No unchanged
inventory is regenerated. The four unrelated dirty files and earlier reports
remain byte-identical.

This closes a bounded **unsigned application-input reconstruction** partition.
The fixture's pending/hash/accounting/outbox is synthetic, not current chain
truth. No keeper, scheduler or observer was adopted; no key was installed;
Anvil8902, sites, services, journals and the paused desktop heartbeat are preserved.

Q06/P20/P21 remain open for actual independent-host/disaster-domain and OS setup,
signer recovery/old-host fencing/restart paths, current canonical reconciliation,
database/checkpoint adoption, durability/encryption, real channels/providers,
sustained operation and independent release approval. Use the
[operator recipe](../../docs/OPERATOR_MANUAL.md#unsigned-recovery-kit-and-clean-filesystem-reconstruction)
before any separately approved live recovery.
