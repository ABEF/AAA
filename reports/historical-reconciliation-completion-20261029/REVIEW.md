# Historical findings reconciled with the current project

Reviewed 2026-10-29 against `main` at `b266ef74e69bdf58264d53cbb2d4dcee28cc1b84`
plus the explicitly pinned Python/documentation corrections in this completion.
**Internal reconciliation complete for the defined inventory; production NOT APPROVED.**
This completes the [published partial checkpoint](../historical-reconciliation-20261029/REVIEW.md)
without rewriting that checkpoint or any original finding, failure, skip or test result.

## Scope and interpretation

All **352 original report Markdown narratives** were read and reconciled, with
**91 current guides** checked for relevant architecture, procedures and evidence
claims. The two subsequently published checkpoint reports were also read. The
[reading inventory](READING_INVENTORY.json) preserves hashes, tracked/local-only
status, reading scope and finding links. Generated tables/matrices and their
linked machine artifacts were not individually re-executed merely because their
narrative reports were read; the callable reference is source-checked rather
than counted as another 696 function-body reviews.

The [finding ledger](FINDINGS.json) contains **235 overlapping material groups**:
53 contract groups, 28 read-service groups, 40 operations groups, 94 supplemental
operations/read-service dispositions and 20 release/evidence groups. These are
neither 235 independent bugs nor 235 tests. Repeated recommendations share
current mechanisms and retain their original source sections and limitations.

The requested workflow was adapted in three material ways:

- A past recommendation is evaluated against current code and decisions before
  implementation. Reintroducing removed bridges, external custody drains,
  creator-payment inboxes, Power or stablecoin contribution inputs would conflict
  with the current release. Their original reports remain valid history.
- "Solved" is separated into implemented, superseded, adapted, accepted risk,
  deferred proposal and unqualified dependency. A source mechanism or a historic
  pass does not close a live operating or independent-review requirement.
- Verification targets confirmed gaps. Existing source-matched Solidity/build
  evidence is reused; unchanged suites, real transactions and financial journeys
  are not repeated to produce a larger count.

## Implemented improvements

| Finding | Correction and effect | Evidence boundary |
| --- | --- | --- |
| HR-C-01: ambiguous frontend startup input | Read API, activation server and unsigned activation CLI now strictly parse all required configuration/request files as objects before constructing workers, Projection, RPC or listeners. Duplicate fields, nested ambiguity, nonfinite/overflowing floating-point values and nonobject roots fail through fixed diagnostics. Finite integers retain existing field validation. | Four new CLI methods plus three existing shared-reader compatibility methods pass. Resource construction is mocked; no live listener or RPC. |
| HR-C-02: ambiguous indexer configuration | The actual indexer CLI uses the shared strict reader before signals, process locking, Indexer, database or RPC. Missing-file classification and valid values/defaults remain. Parser failures use a fixed diagnostic rather than echoing input. | Eight new methods pass; the negative pre-fix experiment reproduced eight assertions failing across three methods. No real database or service. |
| HR-C-03: stale operating and assurance guidance | Current runbooks distinguish the 240-second service cadence from the selected 300-second on-chain maximum; they document strict CLI rejection and matching reviewed rollout. Claim preparation describes its actual never-activated reward invariant without pretending it repeats all NFT/LP validation. | Current code/guide comparison, generated-reference/Todo/link checks; no cadence, signer, ABI or financial policy change. |
| HR-C-04: historical evidence provenance and closure | Completed the contract/operations dispositions; replaced synthetic read-service section labels and nonexistent function names with exact original sections and actual symbols. Preserved the incomplete checkpoint instead of relabeling it complete. | Hash/locator QA and final preservation record; no historical execution reclassified. |
| HR-C-05: overstated static-analysis currency | The October 25 Slither review has 19 changed pins among its 47 LF-normalized source bindings. Current operator/release/Todo guidance now requires refreshed analysis/triage rather than calling it a current pass. | [Applicability comparison](STATIC_APPLICABILITY.json), not a fresh analyzer run or evidence of an exploit. |

The shared reader adds only an optional keyword-only encoding argument: frontend
files retain explicit UTF-8; existing/default indexer locale behavior remains.
Existing HTTP schemas/body bounds, financial math, transaction preparation and
signing restrictions are unchanged. Required configs are not silently repaired.

The earlier checkpoint already repaired both historical local verification tools
to reserve a new evidence output **before** lab HTTP/activity, preserve incomplete
or failed reports and refuse overwrites. Its 13-method scope (12 passes and one
Windows symlink skip) was **not rerun**. Its current-profile/custody guide fixes
remain part of this reconciliation; their original receipts are retained.

## What the historical recommendations mean now

| Area | Current disposition |
| --- | --- |
| Shares, revenue and claims | Current mechanisms preserve per-NFT share NAV, entrant-only contributions, incumbent checkpointing, funded 80/10/5/5 allocation, equal activated collective membership and separate rarity-weighted royalties. Transfers carry unclaimed rights. Old reviews do not establish all current compositions or actual token/provider behavior; their source scopes remain explicit. |
| Maintenance and recovery | Deadline-first scheduling, independent harvest, in-range/no-pending-width compound waits, receipt-backed harvest coalescing, metadata fairness, bounded holder-return retry fairness and actual-ABI reservation observation are already implemented. They are not resold as unfinished features. Rollout, gas and operating acceptance remain separate. |
| Rebalance manipulation | Same-side physical/reference sampled confirmation, reviewed routes, atomic sizing, additional-loss and gross limits are implemented safeguards. They do not prove continuous price persistence, provider independence, protected ordering or attacker unprofitability. Governance-only paused emergency bypass remains an accepted, potentially near-total-loss trust risk. |
| Retired architecture | No current integrated bridge, remote ledgers, creator inbox or external principal/royalty custody exit. Fixed ETH/ZZZ contributions, direct governance and holder collective return replace those old requirements. Historical codecs/recovery for existing Anvil deployments remain required. |
| Proposed enhancements | Observation during cooldown, an outside-range no-swap compound exception, enabling idle-only scheduling, wider diagnostic adapters and fresh Entry-v3 simplification remain explicitly separate design/qualification work. Removing valid royalty-v3 conversion or relaxing financial gates is not justified by those proposals. |
| Marketplace and service availability | Ordered original-request randomness and primary OpenSea mint support are different requirements. Provider failures, stale prices, unknown settlement currencies and missing history are not converted into invented readiness or zero balances. |

Each group's detailed disposition and remaining acceptance link back to the
existing stable [sole Todo](../../TODO.md). Completing this reconciliation closes
only its task, not the owning engineering/release tasks.

## Remaining release work and accepted limits

1. **Actual independent feeds, routes and VRF:** authenticate exact providers,
   source/upstream controls, freshness, token behavior and usable depth. The
   selected pool's recorded fee exceeds the default 1% conversion cap; a cheaper
   qualified conversion route remains necessary unless deliberately governed
   within existing limits. See [pricing](../../TODO.md#task-dual-price-qualification),
   [routing](../../TODO.md#task-lp-execution-routing) and [draw](../../TODO.md#task-fair-draw).
2. **OpenSea and current-profile integration:** qualify/implement the actual
   primary-drop path and 0.05 ETH gross buyer price. Fresh accounting4 services,
   poplint reads/unsigned reviews, wallet acceptance and live history still need
   exact-profile operation. Public signing stays disabled; popldemo stays a demo.
3. **Gas, economics and operational recovery:** measure real maximum-state
   execution, confirmation inclusion/reset cadence, conversion/harvest latency,
   outages, backups, source rollout and current-owner terminal distributions.
   Near-limit code size is not a gas/capacity proof.
4. **Current static and independent security review:** refresh the mismatched
   Slither source scope, freeze the actual release, audit/remediate and sign off
   independently. Reviewed source bodies, receipt models and historic tests are
   useful evidence, not a universal absence-of-bug guarantee.
5. **Deployment size:** exact unchanged build comparison retains 39 normal gates,
   but Manager initcode has only **37 bytes** of margin and Vault runtime **59**.
   Full constructor/dynamic metadata arguments and the exact deployment artifact
   still require release qualification. Do not widen gates to hide the limits.

No unresolved product decision was silently chosen. Optional enhancements remain
under their existing tasks, with reasons and dependencies; no new economic right,
custody authority or daily keeper privilege was added.

## Preservation and publication boundary

Historical report bytes remain unchanged, except the navigational `reports/README.md`.
Two inventoried local-only draft reports are not published as original reports.
The four pre-existing dirty code/evidence files remain unchanged and excluded
from this publication. Original dirty documentation and raw verification outputs
are retained in the external reconciliation directories recorded by the
[handoff](../../docs/WORK_HANDOFF.md).

Only current Python source/tests, affected guides, the sole task/evidence/context
records and this new report are in scope. No Solidity, financial policy, installed
worker, Anvil state, transaction journal, website source/build/server, protected
signer, public transaction, deployment, sealing or paused heartbeat changed.

See [verification](VERIFICATION.md), [provenance QA](PROVENANCE_CHECK.json) and
[preservation](PRESERVATION.json) for the final checks. Git publication remains
separate from operating rollout and production approval.
