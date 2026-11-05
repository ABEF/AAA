# Verification evidence

Use [consolidated findings](../docs/AUDIT_FINDINGS.md) to interpret historical
remarks against current code, [features/evidence](../docs/IMPLEMENTATION_STATUS.md)
for capabilities, [Operator manual](../docs/OPERATOR_MANUAL.md) for actions and
[the sole Todo](../TODO.md) for remaining work. **Production NOT APPROVED.**
Source publication and report reconciliation do not deploy or qualify a service.

## Current evidence map

| Question | Evidence | Boundary |
| --- | --- | --- |
| How are royalties claimed without swaps? | [Original-currency change](royalties-in-kind-20261105/REVIEW.md), [verification](royalties-in-kind-20261105/VERIFICATION.md) | Fresh settlement2/recovery2, schema11/18helpers; same-currency weighted claims/allocation. Old conversion reports retain their original scope; no rollout or production approval. |
| Where are current operator inputs and consolidated guides? | [Documentation consolidation](operator-docs-20261105/REVIEW.md), [verification](operator-docs-20261105/VERIFICATION.md), [document inventory](operator-docs-20261105/DOCUMENT_MAP.json) | All820functions,37constructors and13receivers have short source-bound example rows. Templates require real reviewed inputs; no Solidity or operating change and no new contract-audit claim. |
| Are royalty receipt/recovery/conversion/claims consistent? | [Royalty audit](royalty-audit-20261105/REVIEW.md), [verification](royalty-audit-20261105/VERIFICATION.md), [strict static review](royalty-audit-20261105/static-review.json) | Recovery1 credits only unallocated value at current active weights, excludes earned/deferred liabilities, preserves unsupported late forwarding, and documents ERC2981 non-enforcement. No live deployment/provider/marketplace or independent approval. |
| What earnings-longevity code now exists? | [Checkpoint milestone](earnings-checkpoints-20261104/REVIEW.md), [scope/verification](earnings-checkpoints-20261104/VERIFICATION.md), [OpenSea research](earnings-checkpoints-20261104/OPENSEA_RESEARCH.md) | Opt-in fresh6/5/1immutable checkpoints plus bounded raw suffix, final24new cases and earlier147affected checks; original/historical consumers and operating approval remain separate. |
| How do all historical reports, removed guides and old task lists apply now? | [Whole-history reconciliation](full-history-reconciliation-20261104/REVIEW.md), [original findings](full-history-reconciliation-20261104/FINDINGS.json), [full catalogue](full-history-reconciliation-20261104/REPORT_CATALOG.md), [verification](full-history-reconciliation-20261104/VERIFICATION.md) |310original finding rows,162ledger versions,398pre-ledger lines and explicit superseded decisions; fixes the recurring strict static-default gap.44focused Python methods pass; no new contract/analyzer execution or operating approval. |
| How do the latest four audits apply now, and what improved next? | [Consolidated review](four-report-consolidation-20261104/REVIEW.md), [finding map](four-report-consolidation-20261104/RECONCILIATION.md), [verification](four-report-consolidation-20261104/VERIFICATION.md) | Preserves36input files, implements transactional/durable indexer startup and keeps external release gates open.93focused Python passes; unchanged Solidity evidence reused. |
| Can manual recovery bypass optional guards without weakening normal upkeep? | [Manual safeguard audit](manual-safeguard-audit-20261104/REVIEW.md), [full matrix](manual-safeguard-audit-20261104/SAFEGUARD_MATRIX.md), [verification](manual-safeguard-audit-20261104/VERIFICATION.md) | Two view fixes; fresh normal/reference/static scope and selected EVM/Python checks. No rollout or production approval. |
| Does the confirmation daemon honor its deadlines? | [Confirmation audit](confirmation-audit-20261104/REVIEW.md), [verification](confirmation-audit-20261104/VERIFICATION.md) | Corrects outer-loop deadline/work overhead and queued-clear router-metadata coupling.100focused Python passes with negative controls retained; no contract/settings/journal/service rollout. |
| What did the market/lifecycle campaign verify? | [Review](market-lifecycle-20261104/REVIEW.md), [coverage](market-lifecycle-20261104/COVERAGE.md), [verification](market-lifecycle-20261104/VERIFICATION.md) |7new real local-v4 journeys plus one affected six-day control;7new API/worker methods. Independent receipt/fraction and NAV/cohort assertions, retained model/fixture failures; no production-code or operating change. |
| What did the whole-project supplement improve? | [November4 review](comprehensive-audit-20261104/REVIEW.md), [coverage](comprehensive-audit-20261104/COVERAGE.md), [verification](comprehensive-audit-20261104/VERIFICATION.md) | Indexer anchor snapshot/validation and streaming replay;33affected Python checks. Solidity/build/static evidence reused at exact unchanged pins; source/docs publication only. |
| Does terminal return handle1000NFTs and mixed wallets? | [Focused assurance](holder-exit-assurance-20261103/REVIEW.md), [campaign pins](holder-exit-assurance-20261103/campaigns.json) | Test-only fixture repair and perNFT/grouped-wallet/actual local v4 checks; production e26fc74 unchanged. Maximum target gas, receiver/dependency liveness and independent audit remain open. |
| Which calls are governance-only and can holders still claim? | [Authority review](authority-audit-20261103/REVIEW.md), [verification](authority-audit-20261103/VERIFICATION.md), [permission guide](../docs/ACCESS_PERMISSIONS.md) | Current custody5/schema10/Entry3:43normal gates,471static records, scoped EVM/Python checks. Holder rewards remain claimable; terminal principal batches governance-only. |
| What did the prior direct-Entry change implement? | [Direct Entry3 change](direct-entry-v3-20261103/REVIEW.md), [exact verification](direct-entry-v3-20261103/VERIFICATION.md), [current profile](../docs/POSITION_V6.md) | Historical custody4/accounting6/Entry3/schema9;52production/31dependency sources,43normal gates,471internal static records. No full-suite/CI/independent approval. |
| How do earlier reports apply now? | [Current consolidation](project-consolidation-20261103/REVIEW.md), [finding provenance](project-consolidation-20261103/FINDINGS.json), [baseline catalogue](project-consolidation-20261103/REPORT_CATALOG.md) |310overlapping historical rows,22current topics and5later explicit findings. Not310bugs/tests or a new code audit. |
| What LP behavior was examined? | [LP lifecycle](lp-lifecycle-audit-20261102/REVIEW.md), [multi-day cases](portfolio-long-horizon-20261102/CASE_MATRIX.md), [contract/LP audit](smart-contract-lp-audit-20261103/COVERAGE.md) | Source/test scopes remain distinct. Virtual days/serialized execution and AST inventories do not prove all markets, live uptime or maximum gas. |
| What backend faults were corrected? | [Shared-client consolidation](consolidation-20261103/REVIEW.md), [action/output matrix](action-resilience-audit-20261102/ACTION_MATRIX.md), [fee/history integrity](backend-remediation-20261026/HISTORY.md) | Current source mechanisms versus old execution scope and actual provider/host acceptance stay separate. |
| What management controls exist? | [Manual operations](manual-operations-20261031/REVIEW.md), [residual close](residual-operations-20261031/REVIEW.md), [adaptable policy](adaptable-policy-20261031/REVIEW.md) | The maintained Operator manual/current callable reference governs exact current inputs. Original reports can contain superseded profiles and older uncommitted-state labels. |
| What history was already reconciled? | [Historical completion](historical-reconciliation-completion-20261029/REVIEW.md), [ten-report reconciliation](ten-audit-consolidation-20261102/REVIEW.md) | Prior matrices overlap; the41-row five-report matrix is subsumed by the later75-row matrix, not another41findings. |
| What is still needed for release? | [Remaining findings](../docs/AUDIT_FINDINGS.md), [approval record](../docs/RELEASE_CHECKLIST.md), [roadmap](../docs/ROADMAP.md) | Real feeds/routes/VRF/authorities/OpenSea, matching services/site, metadata, economics/target gas, recovery and independent audit remain open. |

## Read historical reports correctly

The [catalogue](project-consolidation-20261103/REPORT_CATALOG.md) links all400
baseline immutable narrative paths. The mutable index makes401baseline report
Markdown files.351 prior reading records are reused at exact unchanged hashes;
49later narratives have a separate corpus/findings extract inventory. The new
consolidation's own records are outside that baseline, avoiding circular counts.

Original reports, source pins, failures, empty selections, skips and corrected
retries remain byte-preserved. A heading such as “current”, “complete” or “not
pushed” refers to that report's revision/date. Use the current profile and exact
source hashes rather than its wording as an operating instruction. Retired
Power/bridge/creator/third-input/custody-recipient proposals are history, not
unfinished launch requirements. Valid historical deployment codecs remain needed.

Normal build evidence, static triage, source reading, executed tests, installed
services, actual provider qualification and independent audit are different
forms of evidence. Never sum overlapping counts or relabel old sources as a fresh
pass. Frozen-release compiler advisories/analysis must be refreshed when needed.
No report grants public signing, deployment, sealing, site/service changes or
permission to discard an existing pending transaction journal.

[Royalty window/capacity](royalty-launch-window-20261105/REVIEW.md) — current royalty3/canonicalV7 source; earlier royalty2 reports retain their exact historical scope.
