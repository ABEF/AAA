# Verification evidence

Use [consolidated findings](../docs/AUDIT_FINDINGS.md) to interpret historical
remarks against current code, [features/evidence](../docs/IMPLEMENTATION_STATUS.md)
for capabilities, [Operator manual](../docs/OPERATOR_MANUAL.md) for actions and
[the sole Todo](../TODO.md) for remaining work. **Production NOT APPROVED.**
Source publication and report reconciliation do not deploy or qualify a service.

## Current evidence map

| Question | Evidence | Boundary |
| --- | --- | --- |
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
