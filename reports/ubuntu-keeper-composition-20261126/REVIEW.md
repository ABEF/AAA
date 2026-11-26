# Combined Ubuntu keeper, backups and observation — 26 November 2026

**The four-stage c822 composition passes**, with one actual local keeper harvest,
concurrent native backup/observer timers, exact receipt recovery and accepted
fresh health. It finishes in308.218726 seconds using2,942/6,000 local RPC requests.
All seven owned service groups and two timers stop. No component test body,
constructor build or previous financial scenario body is rerun.

No confirmed production defect required a code change. The production Python,
Solidity, source13/source19 identities, journal/ABI profiles and financial limits
remain unchanged. The [operator manual](../../docs/OPERATOR_MANUAL.md) now explains
the concurrent failure/recovery states explicitly. New preparation improvements
are confined to this isolated rehearsal's synchronization and evidence handling.

## Purpose and source scope

Baseline: `7436933c153246f57eaa01cf42c5f3ec90363dad`.
The [plan](PLAN.md) targets a missing composition, rather than repeating the
separate [timer](../keeper-scheduling-20261126/REVIEW.md),
[exact restore](../keeper-sidecar-recovery-20261126/REVIEW.md) or
[receipt recovery](../ubuntu-backup-recovery-20261126/REVIEW.md) checks.

The new [package](preparation/c822/SOURCE_MANIFEST.json) has36 exact current
production members/45 archive members, including its required JSON resource.
It reuses four pinned immutable F6 inputs and existing Anvil/Cast binaries from
the earlier isolated fixture. It adopts no old runtime, journal, signer,
configuration or service. Frozen setup helpers are reused for setup only;
their old scenario bodies are not invoked. No contract is deployed or sealed.

The [source interaction review](review/SOURCE_INTERACTION_REVIEW.json),
[final package review](review/FINAL_PACKAGE_REVIEW.json) and
[resource closure](preparation/c822/RESOURCE_CLOSURE_REVIEW.json) retain their
static scopes. The existing [191-file/2,137-definition inventory](../keeper-sidecar-recovery-20261126/FUNCTION_INVENTORY.json)
is reused because production sources and the workload plan are unchanged.
F6 remains61 project sources/39 dependencies/4 controls and1,021 ABI rows.
Inventory presence is not runtime coverage.

## Actual new interactions

| Stage | Observed behavior |
| --- | --- |
| Capture overlaps real intent publication | A new lab-only reader barrier holds the schedule lock while the real daemon signs and publishes its pending hash. The changed journal causes `backup_capture` / `source_snapshot_changed`; the old selected backup remains exact |
| Timer lock contention | Ordinary timer invocations refuse the held shared lock. Selected-record and observer bytes, queued IDs, sequence and pending `first_seen` remain exact; delivery later acknowledges the original IDs |
| Normal pending-first recovery | The original hash settles once while ordinary timer jobs continue. Receipt recovery stays metadata-degraded; a subsequent normal evaluation produces authenticated fresh health |
| Fenced final capture | Stop writers/timers, read actual final rights/principal/reserves/balances and canonical booking, then publish completion. Stop the model and require its final source/input revalidation and cleanup success too |

The RACE and HOLD scopes differ: RACE directly witnesses transaction progress
while the schedule lock is held. HOLD occurs **before inclusion** and proves
sidecar-history preservation. Receipt clearing itself is not claimed to have
occurred during that explicit HOLD; it occurs with ordinary timers running.

The [result](evidence/c822/fetch-1/RESULT.json) contains bounded compressed stage
details. [Race](evidence/c822/fetch-15/RACE_RESULT.json),
[held-state](evidence/c822/fetch-17/HOLD_RESULT.json) and
[sidecar records](evidence/c822/fetch-4/SIDECAR_RESULT.json) retain actual evidence.
Forty wrapper invocations comprise8 backups,30 observations, one initialization
and one barrier. Six ordinary backups succeed; three observations are healthy;
four invocations report expected scheduler-lock refusal. These are operating
outcomes, **not forty tests**. Incident observations must not be counted as
healthy, and delivery remains at least once.

## Canonical accounting and physical state

Keeper transaction:
`0x6b93f5b978baa03066f0ec02b656b8e5b19088b48aa3de79a1bde29bad772957`.
This is a disposable local Anvil transaction, not a public Robinhood transaction.

The [pending record](evidence/c822/early-1/PENDING.json),
[initial inclusion](evidence/c822/early-2/INCLUDED.json) and
[settlement](evidence/c822/early-3/SETTLED.json) bind the same sender, destination,
calldata, value, nonce and reviewed fee envelope. There is one raw attempt,
one forward and one accepted transaction; latest/pending node nonces both end1.
The actual Vault receipt authenticates `FeesCollected` for the selected bucket.

Canonical gas is300,814 at32 wei: **9,626,048 wei booked once** under the receipt's
UTC day. Pending clears, next nonce becomes1, and the canonical anchor/last
harvest are retained through the healthy cycle and final capture. This validates
local execution-cost booking; it does not qualify real Robinhood complete fees.

[MODEL_EVIDENCE](evidence/c822/fetch-13/MODEL_EVIDENCE.json) exports nine named raw
records with byte counts/hashes: initial/pending/settled/healthy/final journals,
three financial vectors and final canonical transaction/receipt/headers. Its
bounded compressed envelope also carries source pins and exact counters. No raw
configuration, signer material or signed envelope is included. Final physical
captures precede completion/node shutdown; saved independent reconciliation
must pass before the overall result is accepted or published.

The [independent saved verification](verification/UBUNTU_VERIFICATION.json) passes:
it rehashes all nine raw records and reconciles canonical type2 fee arithmetic,
exact booking, physical vectors, queued IDs and native/host preservation. Its
[report-only verifier](verification/verify_saved.py) runs no application, test,
RPC or server action. The tar bytes were verified before execution; the later
saved review checks embedded member/final pins, not a second fetched tar copy.

NFT rights and physical principal remain equal to the initial vector. Final
money/reserves/balances equal the post-inclusion vector. The imported fixture has
no funded fee increment in this harvest: this adds no new dynamic80/10/5/5 proof,
maximum-wallet proof or concurrent-holder-operation qualification.

## Measured timing and operating settings

Normal keeper configuration remains240-second outer polling,12 confirmations,
hourly harvest and24M/full25% maintenance admission. No keeper sleep, pending
record, financial guard or on-chain clock policy is reset to pass this check.

Settlement is observed252.528747 seconds after model readiness, with expected
metadata degradation. Fresh accepted health follows at264.219904 seconds,
11.691162 seconds later. The saved ordinary adjustment-check schedule already
has a nearer deadline: last check1795727030, next check1795727270, no execution
jitter. `poll_delay` prioritizes that known deadline; the healthy cycle advances
the last check to1795727275. The observed gap is245 seconds, within300 seconds.

This is **not two complete240-second sleeps**. The configuration sets an outer
interval, not a minimum after every recovery. The exact internal `_poll_clock`
sample was not exported; observed timestamps and source-branch reasoning do not
prove an unrecorded exact sleep calculation. See the [saved timing review](verification/TIMING_REVIEW.json).

The new lab uses45-second backup and10-second observer timers, capacity32,
300-second health age,900-second backup age and a deliberately short1-second
pending-alert threshold. These are explicit test settings, not launch cadence
or changes to existing services. Local5-second empty-block mining keeps headers
fresh; directed inclusion/confirmation mining is disclosed synthetic chain
control, not wall-clock or real-provider qualification. There are no public RPC
calls or transactions. The900-second/6,000-RPC and capture limits are unchanged.

## Preparation improvements and remaining limits

Before any runtime execution, review corrected rehearsal-only issues: atomic
complete marker publication, narrow retries for two known live-read races,
selection pins taken under the acquired lock, complete JSON resource closure,
accurate signer scope, bounded evidence export and final-stop semantic gating.
The [preflight](preparation/c822/OFFLINE_PREFLIGHT.json) checks source-map/output
sizes without raising caps. Original pre-export model/review bytes remain
separately identified; none is mislabeled as a runtime attempt or pass.

The [final capture](evidence/c822/fetch-2/FINAL.json) verifies unchanged source,
copied inputs/tools and signer masks, with all owned groups empty. The separate
[host comparison](verification/HOST_PRESERVATION.json) records five existing
service states, zero non-ambient differences and one disclosed observer
invocation-ID change. This is a finite comparison, not every host byte or an
uninterrupted-uptime guarantee. Existing services/sites/Anvil8902, journals,
signer configuration and the user-paused desktop heartbeat remain untouched.

Q06/P20/P21 remain open. Real off-host possession/restore and signer fencing,
notification routing/host-down monitoring, physical/power-loss durability,
provider/market operation, maximum/concurrent workloads, multi-day sustained
operation and independent release approval remain separate. No production
rollout, public transaction, deployment or sealing is authorized by publication.
