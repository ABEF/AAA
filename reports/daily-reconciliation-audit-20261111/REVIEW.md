# Daily changes and historical findings — 11 November 2026

The improved [prompt](PROMPT.md) has been executed as three linked workstreams:
review today's changes, reconcile historical obligations, and correct current
source/guidance. The material implementation change is a narrowly scoped claim-
planner efficiency fix. No production Solidity, economic rule, risk setting or
operating environment changed. Production remains **NOT APPROVED**.

## Scope and adaptations

The day is Europe/Paris, not an inferred report date. Contract changes are
`0acb123..872a5a5`, including cleanup `8785728` and reference execution `872a5a5`.
Website changes are `2c6f0c8..3f68fb7`. The initial published heads were
`872a5a50f5b5cffd47e8fd101c44f61b46d06849` and
`3f68fb7e878c17e4aaca4403214575f4f9c9b918` respectively.

The prompt adds exact source/profile boundaries, individual historical finding
provenance, mixed source-complete/live-open dispositions, evidence reuse and
explicit preservation checks. It removes any implication that old royalty swaps,
bridge/custody-address workflows, obsolete codecs or earlier defaults should be
restored. Two critical scope reviews challenge accounting, callback, recovery,
timing, gas and document assumptions before implementation. Missing actual
market qualification is not replaced with synthetic data or relaxed guards.

## Implemented corrections

| Finding | Correction and evidence |
| --- | --- |
| Claim planning repeatedly reads immutable execution capabilities/binding | Add only `EXECUTION_PRICE_VERSION()` and `executionStrategy()` to the existing pinned-target, exact-block, request-local identity cache. A measured selection/trial/final plan drops these reads from18 to6 with the same18-unit payout. Ownership, balances, source revision, active scope, prices, simulations and fees are not cached; healthy claims require no new live Oracle reads. [Backend review](backend/REVIEW.md), [28-method verification](backend/claim-cache-final.json). |
| Two static-review rationales name the wrong allowed module | Correct Fees→Buyback in a new complete strict record. Actual `Manager.swap` remains sealed Vault/Buyback-only; custody has separate fixed callers. Original report bytes,567detector identities and dispositions remain. Only two rationales/provenance change; original162current/405reuse scope is retained. [Errata](contracts/AUTHORITY_ERRATA.md), [strict record](static-review.json). |
| Current guides/task summaries mix historical and current profiles/counts | Correct current callable counts to40contracts/956functions/1009examples; schema17/mint2/V10 and20callable-helper guidance; original-currency royalty4/reporting5; exact LP7 versus historical fractions; source9 LP2 versus source10 optional execution1/LP3; direct mint1 versus OpenSea mint2. Historical reports retain their original labels. |
| Maintained audit prompts still point to profile6/old royalty semantics | Update the maintained whole-project brief and historical entrypoint's current-profile link to profile7, explicitly covering exact-unit ledgers, mint2/V10 and execution1/LP3. The frozen historical checklist remains a research input. |
| Old coupling statement and counts misstate remaining work | Mark explicit execution1/LP3 own-swap/reference overlap as implemented, retaining same-core principal exclusion, actual gas/source/route qualification and service-only compound-policy exposure. Source9/10 unsigned consumers exist; rollout/signing acceptance remains open. |

Current README, sole task ledger/generated Todo, feature reference, findings,
roadmap, release record, operator manual, development/static guidance, context,
handoff and relevant royalty/claim guides now link the corrected source boundary.
Website changes are documentation and inactive-manifest comments only; both
configuration exports remain null. Existing function/input/permission tables
are unchanged and verified, rather than regenerated as a fictitious new ABI.

## Today's contract and consumer review

The [contract review](contracts/REVIEW.md) considers14changed Solidity files and
their invoked dependencies: fixed-pair cleanup, captured-price ownership and
49-word transient codec, actual-core quote/state proofs, settlement callbacks,
both physical LPs, entrant-only NAV/share issuance, ordinary maintenance,
manual emergency masks and context cleanup. All61production sources still
match the prior normal a846 source record. No new exploitable contract defect
was established; this is not a proof of defect absence.

The [backend review](backend/REVIEW.md) traces explicit execution versions,
immutable graph admission, healthy read/claim independence, pending records and
the already implemented late deadline/day/simulation checks. The website's
versioned demo replay, source9/10 separation, immutable manifest/runtime proofs
and unchanged signing/null-config boundaries were inspected. Earlier browser,
actual-core, trace, size and gas evidence is reused only in its exact scope.
There is no new wallet, market, provider, hosting or operating acceptance.

## Historical reconciliation

The [history review](history/REVIEW.md) indexes653current report/guide/root
narratives,3,948main-history blobs and25named structured finding files. It
preserves all310original finding records with their exact original text,
pointers and hashes, and retains every prior inventory blob ID. Bulk extracted
prose/structured contexts are held externally; public indexes retain their
hashes and Git source identities instead of duplicating those texts in Git.

The [individual map](history/CURRENT_REASSESSMENTS.json) contains25split
reassessments covering39distinct inherited rows plus9newer prose obligations.
The remaining271rows are explicitly **not newly source-reviewed or closed**.
Full-text extraction and prior review retention are not a new line-by-line
semantic audit of every historical recommendation. The [follow-up matrix](history/FOLLOWUP_MATRIX.json)
maps current obligations to the sole Todo, not another competing task list.

Material distinctions recovered from old reports:

- Royalty conversion requirements are superseded by original-currency royalty4;
  outage cohorts, admission, capacity and actual token behavior remain relevant.
- Fresh exact-unit LP allocation resolves the old final allocated-unit problem.
  It does not resolve upstream fees never received, sub20raw-unit FeeController
  split carry, the incumbent-individual dust exception or zero-cohort funds.
- OpenSea mint2/V10, source10 unsigned consumption, exact LP integration and
  checkpoints have implemented milestones. Actual onboarding, rollout, workload,
  archive/restore and provider acceptance remain open.
- Dedicated same-main consolidation supersedes the old instruction to close
  main before reinvesting residual. Raw residual-only close intentionally keeps
  principal as attributed idle; it is not an automatic consolidation.
- The keeper's in-range/below-threshold compound wait remains service policy
  selected by the user. It is not a new on-chain restriction on a compromised
  authorized keeper.

All5,517original report artifacts checked by the history verifier remain byte-
identical, excluding the explicitly maintained reports index and protected
pre-existing dirty source-checks record. No original failure or report was erased.

## Unresolved work and limits

| Item | Current conclusion / next action |
| --- | --- |
| Full-operation gas | Controlled cold Entry remains above the unchanged12M default. Earlier actual owned-node reviewed envelopes were17,180,808–18,929,126; Foundry gross-call figures are a different metric. Qualify optional policy2 against real transaction/block/provider bounds, full20%headroom and actual fees. No budget was raised. Vault/Oracle/Manager runtime margins remain32/88/190bytes at the retained normal build. |
| Initial keeper provider work | Initial `eth_call`/estimate omit an explicit gas envelope; the configured ceiling is checked after provider execution work and before signing. Final ordinary-LP simulation is bounded. This is a resource/availability follow-up, not a demonstrated spending or authority bypass. Qualify a shared bounded envelope against supported providers/legacy paths without widening spending. |
| Late fee credit during LP increase | Whether a reachable admitted mutable callback can create fees after the last harvest and net them against an increase debit remains **unverified**. Ordinary transactions cannot interleave atomically. Review actual token/Permit2/periphery powers and establish the accounting effect before deciding on a principal-debit guard. No speculative guard or share-loss claim is added. [Exact prerequisites](contracts/REVIEW.md). |
| Compound policy, idle and maintenance economics | Service-only compound waiting, economic idle-only thresholds, repeated permitted losses, receipt rounding/carry and actual strategy depth/cost remain qualification/decision boundaries. Do not silently change the chosen policy or economic rights. |
| Actual release | Two genuine ZZZ price paths, ETH publication/liveness, useful external depth/routes, VRF, authorities, OpenSea stages/fees/payers, metadata, matching service/site rollout, sustained recovery and independent audit/remediation remain open. Spot/no-TWAP and explicit governance emergency trust remain accepted design choices, not manipulation-immunity claims. |

See [verification](VERIFICATION.md) for fresh versus reused evidence. Main-only
publication changes no deployed contract, public transaction/signing, site,
service, existing Anvil/NFT/LP/balance/journal or user-paused heartbeat. The four
unrelated dirty tracked files and unrelated untracked drafts are preserved.
