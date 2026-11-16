# Verification record

Baseline main: `06e5af2640827e6b212c8b135899f4709ea9e1ee`.
All evidence files are losslessly gzip-compressed; [EVIDENCE.json](EVIDENCE.json)
binds both compressed and original byte hashes/lengths. Original failures, logs,
driver/source snapshots and corrected stages are retained. Source/AST pins and
scope are explicit, rather than retroactively relabelled.

| Stage | Evidence | Result / scope |
| --- | --- | --- |
| Capability baseline | [Record](evidence/recovery-baseline-capability.json.gz) | New module/CLI absent at exact baseline. No old tests executed. |
| Initial real round trip | [Initial JSON](evidence/history-recovery-representative-01.json.gz), [log](evidence/history-recovery-representative-01.log.gz), [corrected helper run](evidence/history-recovery-representative-02.json.gz), [log](evidence/history-recovery-representative-02.log.gz) | Backup/restore/reporting reached success, but a NEW test helper's connection context did not close its SQLite handle before Windows temporary cleanup. Corrected helper only; source1 representative passes. It is historical, not added to final31. |
| HR1 byte-bound baseline | [JSON](evidence/history-recovery-payload-bound-baseline-01.json.gz), [log](evidence/history-recovery-payload-bound-baseline-01.log.gz) | Expected failed regression proves excess ancillary allocation before source correction. |
| HR2 review baseline | [JSON](evidence/history-recovery-review-binding-baseline-01.json.gz), [log](evidence/history-recovery-review-binding-baseline-01.log.gz) | Expected failed method has three detached sidecar subcases. Actual checkpoint accounting/full-day gate stayed intact; provenance binding needed correction. |
| Source2 targeted checks | [JSON](evidence/history-recovery-fixed-source2-01.json.gz), [log](evidence/history-recovery-fixed-source2-01.log.gz) |3 methods pass: changed-backup representative plus both corrected source regressions. |
| Other core checks | [JSON](evidence/history-recovery-remaining27-source2-01.json.gz), [log](evidence/history-recovery-remaining27-source2-01.log.gz) |27 other NEW methods pass once; the preceding3 are excluded. |
| Original2 and initialized-empty branch | [JSON](evidence/history-recovery-original2-empty-source2-01.json.gz), [log](evidence/history-recovery-original2-empty-source2-01.log.gz), [31-method pin/union proof](evidence/history-recovery-31-final-pins.json.gz) |1 additional NEW method passes. Reuses an owned fixture's original-prefix config; unsupported count1 helper was identified without a test run. No old fixture edit. Final core union3+27+1 is31 distinct. |
| CLI first18 | [Representative](evidence/history-cli-representative-01.json.gz), [remaining stage](evidence/history-cli-remaining-01.json.gz), [harness repair](evidence/history-cli-harness-repair-01.json.gz), [case pins](evidence/history-cli-case-pins.json.gz) |1 representative +16 remaining initial successes +1 corrected method =18 unique. Initial one-method/24-subcase failure was a wording-only assertion (`not approved` versus `unapproved`), not24 application defects. Only that failed method repeated. |
| HR3 argument privacy | [Baseline](evidence/history-cli-credential-baseline-01.json.gz), [log](evidence/history-cli-credential-baseline-01.log.gz), [fixed](evidence/history-cli-credential-fixed-01.json.gz), [log](evidence/history-cli-credential-fixed-01.log.gz) |1 NEW method passes after SafeArgumentParser. Four fake-only bad-parse subcases plus valid command control. The previous18 do not repeat. |
| Independent internal reviews | [Initial core review](evidence/HISTORY_RECOVERY_REVIEW_INITIAL.json.gz), [postfix](evidence/HISTORY_RECOVERY_REVIEW_POSTFIX.json.gz), [CLI review](evidence/HISTORY_CLI_REVIEW.json.gz), [final parser/source proof](evidence/HISTORY_CLI_FINAL_REVIEW.json.gz) | Source review identifies/corrects bounded-output, durability/inode and review/parser gaps; no further concrete accounting defect found. Not an independent release audit or operating rehearsal. |
| Final source and preservation | [Final pins](evidence/FINAL_SOURCE_PINS.json.gz), [preservation](evidence/PRESERVATION.json.gz), [baseline](evidence/BASELINE.json.gz) | All50 new method ASTs and final producer/semantic pins; unchanged core at source2, final parser-only CLI delta and exact preservation. No additional test execution. |

**50 unique NEW methods with passing composed evidence; no fresh whole50 rerun.**
The core and CLI categories are disjoint. Repeated failed/newly affected stages
are not extra coverage. Zero selected final-method skips are recorded. Existing
historical suites, Solidity/compiler/static/browser/provider checks are not run.

Real SQLite/WAL/snapshot/file behavior and unchanged exact replay are exercised.
Lifecycle/getter/canonical-provider truths remain controlled; this is not an EVM,
real-market/provider,1000-NFT/maximum-state, Unix host/off-host or independent
approval claim. Exact rows and report amounts/windows match; intentionally
remapped configuration-provenance hashes are not treated as unchanged identities.

The final publication also checks generated Todo consistency, changed-document
links/operation anchors, new canonical test inventory without execution, exact
staged/committed Python import closure and whitespace/preservation. These are
mechanical checks, not additional methods or a full regression/CI-green result.

[Publication source pins](PUBLICATION_SOURCES.json) record the final raw blobs. An extra test-file EOF blank line was removed for the unchanged whitespace gate; the complete module AST matches the tested file, which is retained losslessly. No test was rerun for this formatting-only change.
