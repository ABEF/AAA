# Project documentation and historical-findings consolidation

Reviewed3November2026 against main source `3f879da74a3573ffde4578482835b24a73192930`.
**Production NOT APPROVED.** This is a documentation/provenance/current-source
applicability review, not a new whole-code security audit or deployment campaign.
[Verification](VERIFICATION.md), [current findings](../../docs/AUDIT_FINDINGS.md).

## Scope and evidence hierarchy

The baseline contains401tracked report Markdown files, including the mutable
index, and97guides.351exact unchanged prior narrative-reading records are reused
from the historical completion;49later narratives have a separate full-text
corpus and774finding/boundary extracts. Indexing and reading-scope reuse do not
mean every machine artifact was semantically re-audited or every test rerun.
The [inventory](READING_INVENTORY.json) hashes all baseline narrative paths and
2626immutable report artifacts. The [catalogue](REPORT_CATALOG.md) links the400
immutable narrative paths; this consolidation's own records are outside the baseline.

The [finding map](FINDINGS.json) preserves235historical and75later overlapping
rows with original matrix hashes, IDs and exact JSON pointers. All310pointers are
validated. The41-row five-report matrix is subsumed by the later75, not counted
again. Five subsequent shared-client/Entry findings are linked separately.
22current topics connect current mechanisms, limits, source references and
existing Todo ownership. Original dispositions remain visible; a topic-level
assessment or unchanged file hash is not a fresh exploit reproduction or blanket
closure of every old claim. No new independent-audit opinion is manufactured.

Current documentation now has these distinct owners:

| Question | Maintained owner |
| --- | --- |
| What is the current version/compatibility boundary? | [Profile identities](../../docs/POSITION_V6.md) |
| What is implemented and what evidence supports it? | [Feature/evidence reference](../../docs/IMPLEMENTATION_STATUS.md) |
| How do historical findings apply now? | [Consolidated findings](../../docs/AUDIT_FINDINGS.md), original immutable reports |
| What work remains? | [The sole Todo](../../TODO.md), generated from its one ledger |
| How does the operator perform an action? | [Operator manual](../../docs/OPERATOR_MANUAL.md), current source-bound callable reference |
| What is the work sequence or release decision? | [Roadmap](../../docs/ROADMAP.md), [approval record](../../docs/RELEASE_CHECKLIST.md) |

## Material corrections

| Finding | Correction | Consequence |
| --- | --- | --- |
| DC-01: Operator still described Entry input conversion and `addRoute` | Entry3 is direct input. The manual distinguishes `ActivationAssets.setAsset`, `Balancer.configureExecutionPools` and each earned-reward converter's route methods. | Removes a nonexistent Entry call and prevents configuring the wrong economic path. No Solidity/API change. |
| DC-02: Fresh activation setup table contradicted the actual API | Corrected versions2/2/2→3/2/2,18→17activation-config role pins, removed `v4_executor` and replaced5source fields with `{pool_id,source_asset,asset_policy_id}`. This is distinct from17production modules/20helpers and23parent-read bindings. | The documented shape now passes the actual ActivationConfig constructor with an offline dummy graph and no RPC. [QA](DOCUMENTATION_QA.json). |
| DC-03: Active simplified release and labels mixed old/current versions | Fresh owner guides use accounting6/custody4/direct Entry3/schema9. Review-policy2, Entry routing3, LP routing2 and API/inventory/site schemas are explicitly distinct. Older versioned references/rehearsals/research have scope banners. | Avoids relabelling old runtimes, websites or pending records. Historical procedures remain available under their declared profiles. |
| DC-04: Generic fixed-boundary wording conflicted with emergency/terminal operations | Normal10%ceilings are distinguished from explicit paused-governance optional financial bypass; no ordinary holder withdrawal is distinguished from irreversible collective holder return. | Clarifies existing permissions and risk; grants no new bypass or custody authority. |
| DC-05: Current summaries pointed to older gates/static counts and repeated timelines | Features, release, roadmap, README, report map, instructions, context and handoff now point to one current evidence hierarchy and separate historical source scopes. | Current Entry3 pins43normal gates/471static/reference818 remain exact-source; current task descriptions now use schema9/20helpers and earned-conversion-only scope. Earlier report counts are neither summed nor silently reclassified. |
| DC-06: Historical proposals remained described as missing | Current findings explicitly update direct Entry removal, cooldown observations/near-eligibility enrollment, harvest coalescing, residual close and active-main candidate filtering. The geometry-getter independence claim is explicitly corrected. | Prevents repeating finished work or treating source coherence as independent proof; real operating/economic gates remain open. |
| DC-07: Duplicated history and inaccurate latest labels obscured actual operator work | Replaced report chronology with a topical index plus complete stable catalogue; reduced repository-memory chronology and repeated unrelated boilerplate. Kept the one Operator manual and its full exact-input catalogue. | Unique procedures, task IDs/status/order and original reports are preserved. No extra Todo or automatic synchronization service. |

The source-bound callable reference/notes remain byte-identical. No new public or
internal function, parameter, permission, default, policy or economic right changes.
Operator procedures were corrected to the already implemented source; they were
not executed. Every existing code/config/test/build file remains at its baseline
bytes, including the four unrelated dirty files, which remain excluded from publication.

## Current conclusions that must not be lost

- Source7 is accounting6/direct Entry3/schema9, not accounting7; old current3
  poplint and Anvil profiles remain separate. No website/server rollout occurred.
- One logical bucket may have one main plus one residual in the same pool. Both
  physical holdings, fees and custody remain accounted through modes and recovery.
  Main>=60% is a replacement floor, not a continuous target or economic optimum.
- Contributions spend entrant-only funds; harvest/split, conversion, compound,
  buyback and claim are separate. Current owners own past unclaimed rights.
- 85%threshold/600-second samples/300maxgap/240source cadence/60–300jitter and
  initial12hours describe normal policy, not persistent-history or MEV guarantees.
- Raw cooldown checks, near-eligibility paid observation, receipt-backed harvest
  coalescing and active-main candidate filtering are implemented mechanisms.
- Broken assets/venues, immediate governance, explicit emergency bypass, proxy
  behavior, sampled evidence, bounded search/history and absent post-halt recovery
  remain actual boundaries. Retired architecture is superseded, not qualified.

## Remaining work

Actual independent feeds/routes/depth/VRF/authorities/OpenSea, matching source7
services/site, metadata publication, target gas/economics, host/storage/recovery,
long-lived history and independent audit/remediation remain under existing tasks.
No task status or priority is silently changed. The historical-findings task stays
complete for reconciliation; owning engineering/release tasks stay open.

No public transaction, deployment, sealing, service/site/Anvil/journal/signer change
or paused-heartbeat restart. [Verification](VERIFICATION.md) records unchanged-source
reuse and documentary checks. Source publication is separate from all operating
and production approvals.
