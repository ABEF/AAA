# Resume handoff - 2026-10-18

This is a continuation record, not another task list. Remaining work and acceptance
criteria live in the [central Todo](../TODO.md#task-security-chain-recovery).

## Current checkpoint

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

The saved bridge-fixture fixes and final cold-gas checks are verified. The current
regression passes **582 cases with zero failures and two intentional fork setup
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
