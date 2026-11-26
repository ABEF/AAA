# Ubuntu keeper: accepted-hash storage failure and recovery

Reviewed 26 November 2026. **Core recovery is verified; the original full campaign remains NONPASS.** Seven independent saved-vector checks establish a genuine accepted-transaction/EACCES failure, safe hashless restart, explicit resolution, one-time receipt accounting and a subsequent healthy stock-daemon cycle. The original harness then refused an incorrect timing expectation. Its result and missing final financial reads are preserved; they are not relabelled as a complete pass.

## Scope and source

This was one new isolated Ubuntu composition using the actual normal keeper daemon, real Cast, an unprivileged actor and a private local Anvil node. The authenticated copied F6 fixture has two NFTs and one main LP. The harvest generates zero additional LP fees; this is a persistence/recovery proof, not another fee-allocation or market rehearsal.

The [source manifest](evidence/SOURCE_MANIFEST.json) binds 191 exact HEAD members at `c07d5b153149f7c072ee5ff785c1cabac60197f6`, without working-tree overrides. Production monitor SHA-256 is `90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f`; the executed [model](preparation/c811/model_service.py) remains `a02747cd750363b04280d0f01438338bfbbc4df73065d1d5a74b6825a1924eb4`. Frozen tools, helpers, copied inputs and reviewed preparation are retained in the [build receipt](evidence/BUILD_RECEIPT.json), [review pins](evidence/CANDIDATE_REVIEW_PINS.json) and [independent semantic review](independent/SEMANTIC_REVIEW.md).

No production source, financial policy, permission or limit changed. The production inventory remains 183 Python files/2,007 named definitions/278 lambdas; frozen F6 maps remain 61 project sources/39 dependencies/four controls and 1,021 ABI rows. No unchanged test body or prior financial journey was rerun.

## Actual recovery sequence

1. The stock keeper durably published its exact hashless harvest intent before real Cast submitted it. The private node accepted one transaction. Before returning that original hash, the gateway matched the actual sender, nonce, target, calldata, value, gas and fee bounds, then changed **only the new actor directory** from `0700` to `0500`. [Accepted boundary](evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json).
2. The actual atomic hash save failed with EACCES. Sanitized `submission_requires_reconciliation` retained the validated reported hash; `cycle_failed` appeared before the subsequent health-write failure. The normal CLI logged `keeper_halted` and naturally exited 1. Native process evidence establishes the exit and fencing. [Fault proof](evidence/fetched/native-FAULT_PROOF.json).
3. After the owned keeper group was empty, the controller repaired that directory to `0700`, preserving the original journal and lock identity. A restarted stock daemon reported `recovery_required` with the byte-identical hashless intent and made no second submission. [Repair](evidence/fetched/native-REPAIR.json), [blocked restart](evidence/fetched/case-HASHLESS_RESTART_BLOCKED.json).
4. The controller fenced that writer before invoking the stock resolver **without `--live`**. Resolution authenticated the original transaction and changed only its pending hash while it was still unmined. Twelve actual confirmation blocks followed; only afterward was one-second empty-block mining enabled on the owned node for the remaining service check. [Resolver receipt](evidence/fetched/native-RESOLUTION_RECEIPT.json), [confirmation barrier](evidence/fetched/case-RESOLUTION_READY.json).
5. The restarted normal daemon recovered the original receipt, booked it once and completed a separate healthy metadata cycle. The [recovered journal](evidence/fetched/case-RECOVERED_JOURNAL.json), [stopped health capture](postrun/STOPPED_HEALTH.json) and [event projection](postrun/STOCK_EVENTS_PROJECTION.json) retain those distinct observations.

The new campaign used **2,765/6,000 RPC requests in about 311.3 seconds**, within its 900-second budget. There was one keeper raw attempt, one forwarding, one paid harvest and zero resends. Actual gas was **300,814**, canonical execution price **32 wei**, and the sole booked charge **9,626,048 wei**. Inclusion-day spending, receipt anchor, harvest clock, nonce `0 → 1` and final settled journal independently reconcile. These are isolated-node values, not Robinhood fee estimates.

The configured 24M/full-25% gas profile, 12 confirmations, 5-gwei ceiling, 0.01-ETH transaction/0.05-ETH daily caps, 240-second outer polling interval and hourly harvest all stayed unchanged.

## Original refusal and separate reconciliation

The [original model result](evidence/fetched/model-RESULT.json) and [orchestration result](evidence/ORCHESTRATION_RESULT.json) remain false. The harness incorrectly required at least 239 wall-clock seconds from recovery to the next healthy cycle.

Current `Keeper.poll_delay` prioritizes a known confirmation-check deadline before the recovery-refresh interval. Thus **240 seconds is the outer polling interval, not a mandatory minimum sleep**. The saved schedule was last checked at `1795697384`, due at `1795697624`; its subsequent metadata check records `1795697626`, with no paid observation. The actual healthy cycle completed **228.258214 seconds after the degraded recovery cycle**, with configuration unchanged. This is expected earlier-deadline scheduling, not a production defect or weakened setting. The exact internal poll-clock value/returned sleep was not captured. [Source diagnosis](verification/TIMING_SOURCE_ANALYSIS.json).

A separately reviewed, read-only post-stop capture and [independent reconciliation](independent/RECONCILED_C811.json) verify seven supported partitions from the original artifacts. They do not replace the original result. No financial scenario was replayed to obtain a green campaign.

## Preservation and remaining limits

All three owned keeper/resolver/model groups stopped and were recursively empty. [Final stop](evidence/fetched/native-FINAL_STOP.json). The original installed environments were not adopted or upgraded. [Host preservation](verification/HOST_PRESERVATION.json) records five matching service states, no non-ambient invocation change and one disclosed observer invocation change; [installed preservation](verification/INSTALLED_PRESERVATION.json) records equal source/journal digests and public configuration metadata. Keys, passwords and raw signed transactions were not exported. The desktop heartbeat remains paused.

**The model refused before `FINANCIAL_AFTER` and its planned final NFT/LP/backing reads.** This campaign therefore supplies no fresh physical after-state equality proof. Its genuine receipt/accounting/health evidence must not be presented as those missing reads. The earlier [c808 storage proof](../ubuntu-storage-20261125/REVIEW.md) retains its own six-boundary and direct-reconstruction financial-comparison scope; it is not rerun or relabelled here.

This is not physical disk exhaustion, directory-fsync/power-loss durability, multi-host fencing, off-host restore, sustained service operation, maximum-state or actual-provider qualification. Q06/P20/P21, remaining operating/provider work and independent release approval remain open. No public transaction, new sealing, site rollout, journal adoption or production approval occurred.

## Documentation and publication checks

The Todo, roadmap, findings, operator/recovery/rehearsal guides and project memory now distinguish this verified core from the original NONPASS. Operator instructions explain the earlier-deadline wake-up and conditional return to healthy. Future relevant journeys must capture final physical vectors even when a late assertion fails; the completed financial sequence is not replayed merely to replace this marker.

[Static checks](verification/STATIC_CHECKS.json) find no missing file targets among 3,789 local links in 126 current/new-report Markdown files. All 83 task IDs/statuses, 77 earlier audit artifacts, 82 original curated payloads and four unrelated dirty files remain unchanged. Todo generation and the existing production-function inventory check pass; these are static checks, not another test-suite run. Exact report/evidence files are pinned by the [artifact manifest](ARTIFACTS.json).
