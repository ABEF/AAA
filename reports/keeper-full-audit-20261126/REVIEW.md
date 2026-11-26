# Full keeper audit and operating follow-through — 26 November 2026

Baseline: `5331d3a5d051aad3da61d85aa43fafb870487f35`. This review covers the
maintained keeper, its contract call paths, configuration, transaction recovery,
read-only diagnostics, process boundaries and Ubuntu operating procedures.
Source inspection, new execution and reused historical evidence are distinguished
below. Production is **not approved**. Publication is not service adoption.

## Confirmed corrections

| Finding | Correction | Boundary retained |
| --- | --- | --- |
| K26-01: a booked cost anchor could change during later receipt, metadata or transaction-review reads | Revalidate the previous canonical spending checkpoint immediately before the final successor/header proof, and before the final head in each new-submission branch | Exact original transaction, cost/day/nonce accounting, fee review, final inclusion proof and no-resend rules remain. A contradiction stops recovery/signing; no journal reset or guessed replacement |
| K26-02: staging wallet utilities captured unlimited output | Use the existing 64 KiB combined Cast capture for wallet creation/address reads | Original commands, environment and 60/30-second work deadlines; no signer output disclosure or operating installation |
| K26-03: desktop SSH monitor checked output size only after unlimited capture | Bound complete stdout + stderr to 1 MiB during capture, with the existing 30-second work deadline and 2-second failure cleanup | Exact forced command/account, host-key checks, backup validation and paused monitoring. The helper cannot sign or start monitoring |
| K26-04: recovery prose treated an older failed attempt as the latest outcome | Separate the failed 21 November attempt from finite successful 24–25 November partitions; document anchor and start-limit recovery | Full-feature, actual-provider, off-host and sustained operation remain open |

The late anchor check adds two logical header reads at each affected boundary
when a prior receipt exists, plus the transport's own chain validation. A first
nonce with no anchor adds no reads. Limits were not increased. This closes the
identified honest-reorg/failover window; it is not cryptographic ancestry proof
against a provider returning inconsistent forks on successive calls, nor a
promise about later transaction inclusion.

## Scope and critical workflow review

The three source ledgers are [scheduling](coverage/SCHEDULE.json),
[recovery/transport](coverage/RECOVERY.json) and
[operations/diagnostics](coverage/OPERATIONS.json). Overlapping definitions are
not additive coverage. Scheduling and recovery record body identities and inputs;
operations records file hashes, function locations and static review notes at its
recorded source stage. The final inventory and source comparison cover subsequent
runner-list additions. Inventory is not execution or proof of complete state-space
coverage. The [source comparison](verification/SOURCE_REVIEW.json) distinguishes
changed bodies from unchanged test files without executing old test bodies.

| Area | Reviewed behavior and retained boundary |
| --- | --- |
| Authority and lifecycle | Only admitted keeper/governance calls; exact deployment/runtime/reciprocal bindings; lifecycle and pause admission. Automated keeper never invokes governance emergency bypasses |
| Price and LP execution | Physical and independent reference corroboration; current spot policy, bounded reviewed routing after withdrawal, own-reference transition proofs, captured gross/additional-loss/idle/utilization/caller limits |
| Scheduling | Hard 12-hour ordinary cooldown, 85% boundary-distance trigger, sampled 600-second window, strict 300-second gap, source cadence 240 seconds, durable fresh 60–300-second jitter and reset acknowledgements |
| Contributions and LP geometry | Entrant-only placement/accounting remains on-chain; keeper never recenters for a contribution. Main + optional single residual stay one logical bucket. Mode/width updates remain pending until a valid adjustment |
| Compounding | Separate interval/actual-currency thresholds; software-only wait near/outside adjustment threshold or pending geometry is an explicitly accepted operator trust boundary |
| Harvesting | Independent hourly collection from both physical legs, fixed 80/10/5/5 and classified raw-unit dust. Only authenticated own successful harvest events coalesce the collection clock |
| Buyback and conversion | Only designated buyback reserves; fixed ZZZ and actual burn. LP earned conversion preserves the same NFTs' rights. Original-currency royalty4 disables the historical royalty-conversion worker |
| Holder return and canonical recovery | Current custody5 distribution remains governance-only; legacy keeper worker is rejected. Parking, terminal return and canonical replacement keep their distinct lifecycle/accounting permissions |
| Sender and recovery | Durable intent before Cast; strict reported hash; exact nonce/target/calldata/value/fee envelope; canonical receipt depth and final header; paid cost recorded once; unresolved sends never automatically resend |
| Time and budgets | Fresh deadline/day/funding/nonce after slow review; bounded RPC/response/failover; separate complete fee, daily spend and full padded gas limits |
| Persistence | Strict JSON, private atomic publication, same-inode locking, fail-stop write errors and actual surviving complete journal. File replacement followed by failed directory fsync does not imply the old file survived |
| Metadata and diagnostics | Canonical confirmed ordinal paging, bounded fair scans, exact source/configuration observations and typed failure stages. A source digest is not loaded-code attestation or proof of marketplace refresh |
| Host and operations | Root-owned reviewed tools/source, unprivileged keeper, no core dumps, complete cgroup stop, watchdog progress, retry/start limits, preserved journals and separately authorized adoption |

Full related source reads and the cross-layer call trace are recorded in
[the scheduling review](coverage/SCHEDULE.md). Shared contract arithmetic was
traced where the keeper depends on it; no fresh whole-contract audit or Solidity
test run is claimed. The frozen F6 contract/dependency/build maps and all 1,021
ABI rows remain unchanged.

## New verification and evidence integrity

Implementation and each proposed test partition were independently reviewed
before execution. No existing test method or unchanged contract/browser suite
was rerun.
The publication commit uses a CI skip marker because the existing push workflows
run broad unchanged suites. This follows the requested focused-only scope;
no green published workflow or release approval is claimed.

- **12 new anchor methods passed** in one recorded stage. They cover success and
  reverted receipts, metadata-time invalidation, all submission branches,
  first-nonce/no-anchor behavior, final successor-header checks and exact healthy
  transaction/fee/state ordering. [Manifest](verification/anchor/MANIFEST.json),
  [execution log](verification/anchor/stderr.txt). RPC, lifecycle and signer seams
  are explicit; these are not real-provider or full deployment-admission proofs.
- **10 new utility methods have retained passing log records**: six actual
  disposable Windows process cases and four structural/inert monitor cases.
  Exact combined limit, both-stream overflow, open/closed pipe deadlines, cleanup,
  nonzero exits and fixed monitor connection parameters are covered.
  The producer incorrectly raised `SystemExit(0)` inside its evidence context
  after finalization. Its durable result is correctly **interrupted/nonpass**;
  the overwritten pre/post source maps are unavailable. The original
  [marker](verification/utility-original/RESULT.json) and
  [log](verification/utility-original/RESULT.log) remain unchanged.
  [Separate log reconciliation](verification/utility-original/LOG_FOLLOWTHROUGH.json)
  records only what survives. No green body was rerun to hide this failure.
  The private future wrapper now exits after context closure; production evidence
  semantics were not weakened.

Windows capture is deliberately a single-threaded fixed SSH utility. It reaps
the direct child; descendant-tree containment, process creation and kernel stalls
remain host duties. Unix failure cleanup retains an unreaped group leader before
killing the group. Captured-byte bounds are not a process-RAM qualification.

## Installed Ubuntu inspection

The [read-only observation](server/BEFORE.json) checks Ubuntu's Python 3.12.3 /
systemd 255.4, effective service settings, public numeric configuration, source
digests and original journal metadata. No installed application or tool binary
was executed by this probe; no secrets or credentialed endpoints were exported.

This is an older local Anvil staging installation, not the current F6 candidate:
the original staging node was already failed, keeper inactive, and its saved
healthy observation dated 23 October. Its older 60-second/2-confirmation/4-hour
harvest/500,000-gas configuration must not be mistaken for the current reviewed
240-second/12-confirmation/hourly/24M profile. Several current modules are absent.
Its existing tool files have non-root ownership; the already corrected future
installer does not repair an existing installation automatically. Preserve that
installation and journal. Any adoption needs a separate fenced, matching-source,
tool-ownership and pending-reconciliation review.

## Isolated Ubuntu partition

The new **c810 partition passes** in219.610 seconds /1,652 of6,000 allowed RPC.
Actual stock keeper processes fail five times on an intentionally invalid interval;
the manager refuses the sixth start within600 seconds. Five unique invocation
start/exit pairs, at least30-second restart gaps, the exact PID1/unit refusal and
an empty failed cgroup are captured before any repair. The original journal and
bad configuration remain byte-identical through those failures.

The only repair restores the archived interval0→240 configuration; no journal,
nonce, funding, permissions or financial parameter is edited. One deliberate
reset/restart reaches a fresh `healthy_v2` idle cycle with nonce0, no pending work,
empty spending, zero raw submission attempts and unchanged NFT rights, physical
LP, reserves and claimable backing. All financial jobs are disabled, so this is
not another financial-worker or gas qualification. Existing24M/full25%,12
confirmations,5gwei,0.01ETH transaction/0.05ETH daily limits remain configured.
Numeric fee caps are bound by the pinned driver/configuration checks; the
published idle-health vectors do not independently expose every numeric cap.

The original **c809 campaign remains nonpass**. It safely exercised the same
start limit, but its verifier expected `Service.Result=start-limit-hit`. Actual
systemd255 preserves the earlier `exit-code` while the manager records the start
refusal. Official source and saved native records establish that distinction.
The harness now requires the manager refusal plus the full start/exit/timing and
cgroup proof, rather than relying on the result string. Only the affected
operating flow is repeated in c810.

One **new Linux inherited-pipe method passed once in c809**. C810 authenticates
that exact result and unchanged utility/test source pins without importing or
executing the method again. The original failure, one-method pass and its
zero-reexecution reuse remain separate. Neither campaign changes production
keeper behavior, services or limits.

Evidence: [c810 outcome](ubuntu/c810/ORCHESTRATION_RESULT.json),
[native refusal proof](ubuntu/c810/native-RATE_LIMIT_PROOF.json),
[repair](ubuntu/c810/native-REPAIR.json),
[fresh health](ubuntu/c810/case-HEALTHY_IDLE_CYCLE.json),
[independent saved-vector review](verification/UBUNTU_SAVED_VECTOR_REVIEW.json),
[c809 original outcome](ubuntu/c809/ORCHESTRATION_RESULT.json) and
[original Linux result](ubuntu/c809/model-SELECTED_LINUX_TEST.json).
The [inspection-only preparation manifest](ubuntu/preparation/MANIFEST.json)
binds exact harness/controller/setup source copies. These fixed private-lab
programs are evidence, not an installation or production deployment workflow;
no credential, runtime key or state snapshot is included in those source copies.

Both pairs of owned model/keeper units stop with all four recursive cgroups empty.
The [original-host comparison](server/PRESERVATION_REVIEW.json) preserves five
existing service states and seven older stopped labs: zero nonambient differences,
one expected observer invocation change. Separate
[before/after identity checks](server/IDENTITY_REVIEW.json) preserve installed
files, public configuration and the original staging journal metadata exactly.
No original service/site/chain/journal, Anvil8902 or heartbeat is adopted/restarted.

## Reused evidence, remaining decisions and qualification

Unchanged finite proofs are linked rather than rerun:
[stock daemon/history recovery](../ubuntu-complete-20261124/REVIEW.md),
[positive maintenance workers](../ubuntu-keeper-blockers-20261124/REVIEW.md),
[one–two–one LP lifecycle](../ubuntu-hybrid-20261124/REVIEW.md),
[key replacement](../ubuntu-key-rotation-20261124/REVIEW.md),
[watchdog and active-Cast interruption](../ubuntu-supervisor-20261125/REVIEW.md),
[six actual storage failures](../ubuntu-storage-20261125/REVIEW.md) and
[bounded Cast](../bounded-cast-20261121/REVIEW.md). Each keeps its original source,
fixture, failure and accounting scope; this review does not relabel them as a
fresh all-feature run.

Remaining material work:

1. Qualify actual-provider latency and serial transaction confirmation against
   the strict five-minute observation gap; first discovery has finite scheduling
   fairness, not a guaranteed elapsed-time SLA. Do not silently loosen the gap.
2. Complete fenced off-host restore, external stale/error alerts, full-feature
   normal operation, physical storage/power-loss and sustained faults. A responsive
   failure loop can pulse the progress watchdog without successful maintenance.
3. Review long-lived local JSON/backup growth against measured workloads before
   proposing new byte caps. Trusted root/same-UID files, host/kernel behavior and
   coherent provider responses remain explicit trust boundaries.
4. Metadata recovery may need historical pinned getters until its observation
   expires. Preserve pending work on archive failure; never infer a resend.
5. The legacy accounting3 rehearsal and fixed trusted systemctl observer still
   have capture/retention limits outside the newly bounded monitor path. They are
   not qualification tools for the current financial graph. Production monitoring
   and deliberate source adoption remain open; the desktop heartbeat stays paused.
6. Actual feeds/routes/depth, complete fees, authorities, custom OpenSea/VRF,
   matching consumer/runtime adoption and independent release review remain open.
   The operator still chooses the final production pool.

No ownership, reward split, exact entitlement, lifecycle, gas/fee/financial limit,
permission or journal/checkpoint schema changes. Q06/P20/P21 remain qualification
work; a bounded rehearsal cannot close the whole acceptance packages.

## Primary references used

- [Python 3.12 subprocess](https://docs.python.org/3.12/library/subprocess.html):
  buffered capture and process-creation timeout limits informed bounded reads,
  failure cleanup and explicit host-supervision caveats.
- [Microsoft PeekNamedPipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-peeknamedpipe):
  typed anonymous-pipe availability reads avoid stranded blocking reader threads
  in the fixed Windows monitor utility.
- [systemd 255 unit limits](https://www.freedesktop.org/software/systemd/man/255/systemd.unit.html#StartLimitIntervalSec=interval):
  start-rate limits and deliberate `reset-failed` after fault repair, rather than
  repeatedly resetting the manager or keeper journal.
- [systemd255 service state](https://github.com/systemd/systemd/blob/v255/src/core/service.c)
  and [unit start limits](https://github.com/systemd/systemd/blob/v255/src/core/unit.c):
  prior service failures can survive a later refused start. Native manager
  refusal/history must corroborate the operating condition.
- [EIP-1898](https://eips.ethereum.org/EIPS/eip-1898): canonical block identity
  remains provider-relative; a set of header rechecks is not independent consensus
  verification. No speculative block-selector or provider-policy change was made.
