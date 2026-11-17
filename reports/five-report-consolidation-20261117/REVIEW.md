# Latest five reports: current findings and improvements

Baseline main `1c18379b03b067de722d250cee1cc173acc4d635`.

**Five report families are reconciled against current code, not merged into a
claim that every old test or release requirement is complete.** Their300tracked
files, including37Markdown files, remain unchanged. Repeated mentions point to
one issue/obligation; later fixes and explicit operator decisions supersede
earlier uncertainty.

## Selection and current disposition

[SCOPE.json](SCOPE.json) records first publication on main, exact file pins and
original documentation backups. Selection uses Git history, not modification
dates:

| Report family | First publication | Current significance |
| --- | --- | --- |
| [Repaired-test impact](../test-impact-followup-20261117/REVIEW.md) | `1c18379` | Late manual anchor race and stale test expectations corrected; finite economic/physical checks keep source stages. |
| [Test/seal review](../test-seal-deep-review-20261117/REVIEW.md) | `fdb7562` | Chain, URI and reservation safeguards; individually assessed earlier30/later29 and scoped fixture repairs. |
| [Operator behavior](../operator-behavior-followup-20261117/REVIEW.md) | `003c8d8` | Empty-artwork sealing and slow due-clock decisions corrected; service-only compound policy explicitly retained. |
| [Operator input audit](../operator-input-audit-20261116/REVIEW.md) | `6945eee` | Frozen gas, output handling and nested input/units/example corrections; documentation counts are not execution. |
| [Pre-seal planner](../preseal-planner-20261116/REVIEW.md) | `72e5197` | Twelve conditional unsigned setup families; unknown live identities/readiness remain unverified. |

[RECONCILIATION.json](RECONCILIATION.json) contains64distinct rows with origins,
current source proofs, disposition and next action:

| Classification | Rows | Meaning |
| --- | ---: | --- |
| Resolved prior findings/gaps |37|Already corrected source, tools, documentation, test fixtures or selected verification. Those fixes are checked against current code, not redone.|
| Retained policy choices |9|Preserve the selected economics/authority and approved operational model.|
| Structural limits |7|Immutable/recovery/dependency/engineering constraints; passing a local gate does not remove them.|
| Historical evidence limits |2|Missing/weak original evidence or explicitly historical cases; no invented artifacts or new pass claims.|
| Release qualification buckets |7|Actual inputs, providers, markets, maximum workloads, hosting and independent approval still required.|
| Corrections made in this consolidation |2|Missing per-pool stop disclosure and count-only historical evidence admission.|

These are issue/obligation categories, not vulnerabilities, test totals or
independent approval. The [sole Todo](../../TODO.md) retains all existing task
statuses. The [contract/LP review](CONTRACT_LP_RECONCILIATION.md),
[tool review](TOOLS_RECONCILIATION.md) and
[readable index](RECONCILIATION.md) provide the detailed slices without adding
their overlapping topic counts together.

## Implemented improvement1: disclose stopped ordinary LP operation

A complete pre-seal input could set `operationsEnabled=false` while leaving
`depositsEnabled=true`, but output could report no explicit operating stop.
Ordinary placement/compounding/rebalance still reject that pool. The new
regression reproduces the missing warning; its healthy control passes.

The planner now names each affected pool and the stopped ordinary paths. It
does not alter configuration, ordering/calldata, defaults, unknown-input blocking
or any readiness flag. Pool-flag-only harvesting and earned claims are kept
separate from ordinary deployment/maintenance. No automatic bypass, enable,
route change or financial relaxation is added.

Two new actual-planner checks pass; the original failure is preserved in
[TOOL_STOPS_BEFORE.json](TOOL_STOPS_BEFORE.json) and the correction in
[TOOL_STOPS_AFTER.json](TOOL_STOPS_AFTER.json).

## Implemented improvement2: admit exact evidence identities

The historical physical/rights collectors checked successful3/2method counts,
without independently demanding the advertised exact identities before
summarizing. Original records contain the right methods; **no substituted
historical execution was found**. The weakness is in future evidence admission,
not a reproduced contract exploit.

The new [fixed checker](../../scripts/check-focused-evidence.py) has a
code-pinned manifest, bounded duplicate-safe JSON/gzip decoding, exact IDs and
statuses, and cross-checks raw hashes, compiled selectors/targets/source metadata
where those artifacts exist. It offers no caller-supplied positive manifest,
network, compiler, execution, signing or adoption option. A malformed-log and
corrupt-DEFLATE edge found while developing the checker were corrected with
their own retained regression evidence.

Seven selected groups span all five report families. The78historical records
have **different evidence tiers**: the old input-audit tool list has no independent
raw terminal log, and one earlier seal group lacks a separately extracted
artifact. Those omissions stay visible. A passing integrity check does not
prove original execution, assertion strength, current behavior or release.
[Full scope and new checks](EVIDENCE_ADMISSION.md).

## Current documentation is consolidated too

README now starts with the project and its architecture; the architecture/body
itself is preserved. Context and handoff retain the operating/economic rules,
preservation requirements and exact next steps without repeated report
chronology. The current finding index no longer points at the superseded
16November index as latest. Feature evidence distinguishes current consolidation
from historical source-scoped results; pre-seal/operator/development procedures
explain the new diagnostic/checker and its limits.

Original current-doc bytes are archived outside the repository before edits;
[DOC_CHANGES.json](DOC_CHANGES.json) records before/after hashes. Original reports
are never rewritten or deleted. Nothing in this cleanup changes an NFT right,
permission, principal guarantee or operating service.

## What stays open

Extra compound waiting remains a keeper-software rule, cumulative loss caps
remain declined, emergency governance retains explicitly optional financial
protections, and royalty recovery retains current active-weight allocation.
Do not reopen these decisions as unapproved audit fixes.

Pending randomness, failed tokens/receivers, coupled terminal payouts and wrong
immutable graph/content remain real limits with documented recovery/approval
boundaries. Tight bytecode headroom is an engineering constraint—current normal
gates pass—not evidence that deployment is currently impossible.

Actual independent sources/routes and bidirectional depth, full fees/provider
capacity, maximum-state gas, authority/contract-wallet inputs, OpenSea/VRF/content,
matching site/services/operations and independent audit remain release work.
The checker cannot manufacture these inputs or repair a failed external asset.

[Verification](VERIFICATION.md) records only new/affected checks. All61 production
Solidity files, the accepted100-source build, financial defaults, existing
chains/journals, websites/services and signer remain unchanged. The staging
heartbeat stays user-paused; source publication is not rollout or production
approval.
