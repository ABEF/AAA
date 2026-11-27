# Keeper output and storage review — 27 November 2026

**Implemented smaller diagnostic output and fixed publication/storage bounds.**
The review starts at `1605dac2b2fd30e3b23e0adfc2c09ab8a913e2b7`.
Both preceding 27 November commits changed rehearsal evidence/documentation,
not production keeper code. Their original report files remain unchanged.
This change updates production source locally; it adopts no running service.

| Improvement | Behavior and preserved boundary |
| --- | --- |
| Compact logs | Remove JSON whitespace, retain every event, field, duplicate, full calldata and flush. Nonfinite numbers refuse before emitting invalid JSON. No suppression, debounce or persistent log cache. |
| Compact health | Only health opts into the atomic writer's compact format. Default journal/sidecar formatting and private temporary-file, file-sync, replacement, directory-sync and cleanup order remain. Both health writes remain. |
| Bounded health inventories | Each confirmation ID list shows the first32 numeric-sorted IDs, with explicit full `count`, `complete` and `all_ids_sha256`. Every original ID remains in the journal. This is a diagnostic preview, not dropped work or a permission change. |
| Scheduler selection | Bound the actual pretty JSON/ASCII escaping/platform newline at64KiB before replacement. The former compact-size check could admit a file its reader would then reject. Existing selection, lock and generations survive refusal. |
| Staging export | Bound the actual persisted export at the existing1MiB forced-reader limit before replacing it. Refusal preserves the earlier export and captured snapshots; the earlier export can become stale and must not be called fresh. |
| Desktop snapshots | Bound new files at1MiB and serial archive enumeration at10,000 entries. Verify existing files with exact-length-plus-one stable reads and regular/single-link/reparse checks. Reject different/oversized/aliased files; preserve originals and exclusive0600/file-sync creation. Identical files remain verifiable at capacity. |

The full-list digest is SHA-256 of the complete numeric-sorted ID list encoded as
compact ASCII JSON, **without a newline**. Consumers must inspect `complete`;
an absent preview ID is not evidence that its journal work disappeared.
The preview ceiling changes no bucket admission, health schema, alert1MiB limit,
confirmation timing, financial limit, authority or transaction accounting.

## Verification actually performed

**29 distinct NEW methods pass across the recorded stages. No old test body ran.**

| Partition | Exact result and limits |
| --- | --- |
| [Publication bounds](verification/storage-bounds-001/RESULT.json) | Four new temporary-file methods pass: compact-fit/pretty-overflow selection and export refusal preserve prior files; exact1MiB escaped export passes, +1byte refuses. Scheduler identity guards are narrowly mocked; actual atomic writer is used. |
| [Output and health](verification/output-001/RESULT.json) | Eleven new methods pass: default-byte equivalence, compact logical equality, serialization/replacement failures, write order, all critical log fields/events, stock unsigned pending cycle and initial health refusal before cycle/RPC/signing.0/32/33 and real validator-admitted10,000+10,000 ID inventories are covered. |
| [Desktop archive](verification/desktop/DESKTOP_STORAGE_TESTS.json) | Fourteen distinct new methods pass across stages. The initial12-method run retains11 passes/one error; a single affected-method diagnostic also errors. Only that affected method and two new portability methods then run and pass. No whole-module rerun. |

The output check uses actual stock `run_cycle` with inert `FakeRpc` data and an
unmined saved hash. It neither submits a transaction nor replays the earlier
Ubuntu/F6 scenario. Its large synthetic case produces **6,591 health bytes**.
Reconstructing the previous full-list serialization of the same object gives
1,781,385 pretty bytes, or1,621,101 compact bytes. The **3,841,414-byte journal**,
its inode, full in-memory state and pending hash remain exact. These are byte
measurements, not CPU, network-latency or production workload qualification.

The desktop failure exposed an actual Windows interoperability edge: path and
descriptor stat calls reported different ctime values for the same fresh file.
The correction retains cross-API device/inode/mode/link/size/mtime equality and
requires ctime stability separately within each API before/after the read.
New checks accept that legitimate cross-API difference and reject same-API
ctime mutation. Original failures, their source pins and the diagnostic remain
in the staged receipt; the initial test-source copy is explicitly reconstructed
to its previously captured exact hash, not represented as an original capture.

Two existing health-writer mock adapters now accept/forward the new optional
keyword. [AST equivalence](review/WRITER_ADAPTER_AST_EQUIVALENCE.json) preserves
their assertions/body semantics; those old test bodies were not run.
The normal keeper selector includes all three new modules for future review.

## Code review and historical evidence

The [source review](review/SOURCE_REVIEW.json) identifies every changed named
production definition and checks exact unchanged AST/Git reuse. Default atomic
writer normalization is independently equivalent to the baseline; pending,
receipt/fee/day/nonce/spend, signing and keeper transaction scheduling remain unchanged.
The [peer review](review/CORE_PEER_REVIEW.json) and
[changed-preview supplement](review/CORE_PREVIEW_SUPPLEMENT.json) keep their
different source stages. Every new branch and its callers were reviewed before
its focused execution. Source inventory is not a guarantee of all numeric or
operating states.

The two earlier report families contain336 files/2,359,514 bytes.37 extra exact
copies account for447,208 bytes and already share Git blob IDs. Deleting or
editing those historical snapshots would damage provenance for little benefit;
none is removed. New evidence links current source instead of copying complete
source trees or operational packages.

Three finite-harness reuse caveats remain recorded: some unexpected exits omit
captured tool output; some wrappers publish execution metadata only after result
parsing; a read-only budget context commits unchanged metadata twice. These are
inert historical helpers, not current keeper daemon paths. Review a new driver
before reusing them; do not alter frozen successful/failed records.

Long-lived identity caching, cross-cycle log suppression and automatic backup
deletion were deliberately excluded. Repeated source checks detect changed
inputs; suppressing an unchanged message can hide a new recurrence after recovery.
The archive bound assumes **one serial collector per archive**, not a cross-process
lock or global quota. Actual host journald retention, off-host archival and
capacity alerts still need operating review. No existing backup is pruned.

## Source and operator adoption

The [current inventory](FUNCTION_INVENTORY.json) has191 Python files/2,140 named
definitions; the [anonymous supplement](ANONYMOUS_CODE_INVENTORY.json) records280
lambdas. F6 source/dependency/control maps remain61/39/4 and1,021 ABI rows.
The normal inventory check points to this new source scope. Historical inventories
retain their original source; the changed writer is not relabelled as the old one.

Source13/19 membership stays unchanged, but changed file hashes require matching
keeper/checker/tools and separately reviewed policy pins. Verify older packages
with their matching original release/configuration/policy. A source migration
is not an ordinary policy `rebind`; do not rewrite an old manifest or journal.
Follow [the operator procedure](../../docs/OPERATOR_MANUAL.md#keeper-output-storage-and-source-adoption).

Existing services/sites, Anvil8902, original journals, signer/public-submission
restrictions, financial/resource limits and the paused desktop heartbeat remain.
No application RPC/SSH/server actions, public transactions, deployment, sealing or service
restart were performed. Actual matching Ubuntu adoption, providers/channels,
cross-host/signer fencing, physical durability, sustained operation and independent
approval remain open under the existing Todo tasks and Q06/P20/P21 boundaries.

Implementation references: Python's [JSON encoding documentation](https://docs.python.org/3.11/library/json.html)
describes compact separators, ASCII escaping and strict nonfinite-number refusal;
the [OS interface documentation](https://docs.python.org/3.11/library/os.html)
describes platform-dependent file metadata and replacement interfaces. Saved
Windows observations and project-specific durability checks remain separate
from those API definitions.
