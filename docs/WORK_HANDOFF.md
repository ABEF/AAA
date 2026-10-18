# Resume handoff - 2026-10-18

This is a continuation record, not another task list. Remaining work and acceptance
criteria live in the [central Todo](../TODO.md#task-security-chain-recovery).

## Current checkpoint

The October 19 continuation adds [the operator manual](OPERATOR_MANUAL.md) with
mandatory same-change maintenance in repository instructions/Todo workflow, API
request-wide work limits and supervised workers, plus confirmed mint readiness.
Read [scoped verification](../reports/api-work-limits/VERIFICATION.md) for results
and source bindings. Solidity is unchanged; do not repeat unchanged suites.
Randomness policy is qualified/funded service plus draining original requests
before replacement; no reroll/carry. Keep the 3% cap per operation only. Production,
provider/escrow/hosting qualification remain open; main publication is established
by Git. Website/server/paused monitor and unrelated drafts remain unchanged.


The [review of October 18 changes](../reports/daily-security-20261018/REVIEW.md)
was completed October 19 against 13 commits through `485a089`. No production
code changed. Existing build/source hashes matched; unchanged suites were not
rerun. A new synthetic expiry check reproduced continued API work before safe
rejection. Request-wide deadlines and RPC-work limits belong to host-services;
the unfulfilled-VRF/handoff dependency belongs to fair-draw and canonical recovery.
Successor escrow compatibility, immediate governance trust and cumulative
maintenance costs remain recorded risks. The central Todo contains acceptance
criteria. Release stays NOT APPROVED; preserved local drafts remain unpublished.

Governance now has **no mandatory waiting period**, including the additional LP
migration delay. The user explicitly superseded the earlier delayed policy and
proposed route-only exception. Read [authority semantics](GOVERNANCE.md) and
[scoped evidence](../reports/immediate-governance/VERIFICATION.md). Target safety
checks, sealing and finality remain; there is no advance warning window. Update
production authority/runtime records and operating procedures before approval.
No deployment or website/server change occurred; monitor stays paused. The
randomness provider decision remains open and unchanged. Use Git for publication.


The [read-only route campaign](INTEGRATION_CAMPAIGN.md) now records a successful
paced USDG/ETH feed and four-route conversion observation. This is not complete
activation, a public transaction or a new fork/test pass. See [its scope](../reports/activation-route-observation/VERIFICATION.md).
Actual PoPL deployment, qualified services and operator-run transactions remain
open; the private key was not accessed. Earlier HTTP failures remain preserved.

The [local $1 rehearsal](ONE_DOLLAR_REHEARSAL.md) is separately implemented and
verified (10 Solidity / four Python). Production $100 activation / 0.05 ETH mint rules
are unchanged; no public transaction or website/API deployment was made. Read
[its evidence](../reports/one-dollar-rehearsal/VERIFICATION.md) for the original
fixture failure and successful corrected run. Real defects found in later tests
must be fixed in production with targeted evidence; the $1 override stays isolated.

The latest [range-policy path](RANGE_POLICY_UPDATES.md) is implemented. After a
governance-approved range update, ordinary keeper rebalance becomes eligible once cooldown
passes even at a flat price. It compares current LP ticks at the recorded center,
preserves existing Vault guards and clears the mismatch on success. No forced
execution role/state was added. Backend context now reports the pending range
cause and checks both triggers. Read [current evidence](../reports/range-policy/VERIFICATION.md).
Only Strategy production Solidity changed; broad unchanged suites were not
repeated. Vault still has 19 runtime bytes of headroom. Runtime manifests, real
range/MEV/gas qualification, services and independent review remain open. The
website/server and paused monitoring are unchanged. Check Git for publication.

The [dynamic-liquidity review](DYNAMIC_LIQUIDITY.md) adds the user-approved
out-of-range warning with honest eligibility timing, the 3% aggregate ordinary
rebalance budget, guarded current NFT valuation and current-LP API context.
[Verification](../reports/dynamic-liquidity/VERIFICATION.md) binds affected
checks to these changes; the earlier full handoff regression below is historical
for its source snapshot and must not be presented as a new full regression.
Vault has 19 runtime bytes of headroom. Use the central Todo for live range/
strategy qualification, next-check telemetry, wallet integration and audit.
No website/server or monitoring service changes are included.

Complete activation/top-up preparation is implemented separately from the old
mint/claim and conversion-only drafts. Read [the integration contract](ACTIVATION_PREPARATION.md)
and [scoped evidence](../reports/activation-preparation/VERIFICATION.md): 38 focused
checks passed on the exact publication snapshot; 63 ABI getter layouts and local
Anvil trace/gas/budget mechanics were verified using source-matched artifacts.
The backend returns the current NFT on-chain marked value separately from the
new marginal LP contribution, an exact unsigned Entry call and separate gas.
Insufficient approval returns only an approval/reset step and requires re-quoting
after confirmation. Production manifests/routes/feeds/RPC fee semantics and the
wallet/hosted-service integration remain open; no website/server changes occurred.
Source/evidence/docs are published together on main; use Git for exact identity.


The latest [claim-lineage checkpoint](FRONTEND_LINEAGE.md) extends the schema-2
lifecycle API with complete explicitly configured same-chain predecessor replay.
It verifies both handoff directions, canonical retirement/activation receipts and
terminal source commitments, then includes all prior LP/royalty claims and owners.
Old indexes may stop at retirement; historical-only assets remain visible.
Missing configuration stays unavailable; invalid lineage fails closed.
[Scoped verification](../reports/frontend-lineage/VERIFICATION.md): 91 passing
API/lifecycle/history cases on the exact publication snapshot, plus two getter and
two event layouts checked against source-matching existing compiler artifacts.
Production Solidity is unchanged and its tests were not repeated. Live archive
services, independent peer review and website integration remain open.
The optional wallet POST drafts remain outside this scoped publication.

The earlier handoff's saved bridge-fixture fixes and final cold-gas checks were
verified. That regression passed **582 cases with zero failures and two intentional fork setup
skips** across 49 suites. The unchanged 34-case focused handoff run is reused after
checking all compiled dependencies, giving 616 successful cases in combined scope.
These are separate source-matched runs, not one new 616-case execution.

This checkpoint accompanies the scoped canonical-handoff publication on **main**.
Use Git HEAD/origin/main to verify the exact publication; the earlier
`79f205a7933107f61f26892109f14ee52821700e` checkpoint and its uncommitted wording
are historical. Unrelated wallet/API, quote/process-runner and artwork drafts
remain outside this publication. Do not use `git add .` to include them later.
No contract has been deployed and no website/server service was changed.
Release remains **NOT APPROVED**.

## Implementation and accepted trust

Read [the implemented handoff boundary](CANONICAL_HANDOFF.md). It supports only
same-chain replacement: all mints revealed, buckets Parked/None, no active plans
or historic legacy bridge activity. Freeze captures all six receipt cutoffs
atomically; phase 8 settles domains once in strict order before export. Complete
state/import and exact classified backing precede atomic source retirement and
single-successor activation. Restored abort and one-hop late forwarding exist.

The user accepts different reviewed replacement code approved through timelocked
governance, including the risk of a malicious approved successor diverting LP.
Do not impose identical-code admission. Future-chain activation still requires
verified source finality with no multisig/timeout override. Authenticated channel
closure, new lineage/message semantics and exact cross-chain transport/backing
remain pre-seal work. Sealed code cannot acquire absent capabilities later;
post-halt recovery is deferred.

## Evidence to reuse

The [verification record](../reports/canonical-handoff/VERIFICATION.md) separates:

- The new 582-case regression, including repaired bridge suites and ten cold-gas
  cases, with unchanged sources and explicit fork skips.
- The reused 34 focused passes, 30 normal object gates/39 production bindings,
  141 configuration checks and 88 keeper lifecycle checks.
- The current-source internal review of 374 Slither findings, coverage and ten
  mutation rejections. Internal review does not replace an independent audit.
- 123 additional successful keeper cases; one Unix permissions case awaits
  Ubuntu. The venue fixture and local deployment script compile/type-check,
  without implying deployment or operating rehearsal.

[Reuse verification](../reports/canonical-handoff/reuse-verification.json) binds
prior evidence to unchanged source dependencies. Do not repeat checks solely to
increase counts. Vault has 33 runtime bytes of headroom and Migration 58;
constructor arguments still need deployment allowance.

## Next work boundaries

Follow the owning tasks in the central Todo for exact-commit Ubuntu CI, keeper
operating qualification, live API/indexer and same-chain history integration,
marketplace/contract-owner cutover, qualified live services and independent audit.
The cross-chain requirements remain implementation work, not completed by the
same-chain tests. The initial release still requires migration disabled.

The chat health monitor was **paused at the user's request on 2026-10-17**.
Do not restart it without authorization. That action did not stop the isolated
server service; the period after pause has no chat-monitor observation coverage.

## Artifact and publication discipline

External artifacts and runner scripts remain under:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/handoff-20261017`.

Current broad receipt: `regression/attempt2/receipt.json`; reused focused receipt:
`focused/attempt5/receipt.json`; normal production build: fresh attempt9 and
successful cached attempt10. Fresh static analysis is in
`static-analysis-settlement/`. Continuation tooling is in `resume-20261018/`.
Original failed/stale diagnostic attempts remain preserved and are not merged
into passing results. Raw large logs stay external with hashes and full compact
case outcomes in the repository. Do not overwrite existing attempt directories.

Do not rerun `publish_local_evidence.py` blindly: its historical review assumption
is obsolete. Preserve strict reentrancy write-bundle comparison metadata when
updating the review. Keep compiler/profile and tested source unchanged during a
verification run. Current CI allows 60 minutes for local checks and includes
canonical/preparation keeper tests; that timeout does not relax gas assertions.

For every change, update `docs/project-todo.json`, regenerate `TODO.md`, run the
sync tool with `--check`, and reconcile affected evidence/release references.
This is durable repository context, not a claim of global personal memory.
