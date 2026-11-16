# Source-scoped verification

Baseline main: `3c180f2f5a0fe3743b87184250dd2d0f96d09881`.
Final producer/importer/CLI/test hashes and all46 new test method AST pins are in
[final pins](evidence/FINAL_SOURCE_PINS.json). Original stage files, including
failures, are enumerated by exact SHA-256 in [EVIDENCE.json](EVIDENCE.json).
Gzip files decode to the original byte hashes recorded there; compression changes
no log text and avoids publishing whitespace-modified failure evidence.

| Stage | New method evidence | Outcome / limitation |
| --- | --- | --- |
| Baseline capability | [Baseline admission record](evidence/prefix-import-baseline-capability.json.gz) | New producer/CLI absent at exact baseline; unchanged current lineage consumer rejects direct original2 installation. No old suite executed. |
| Original2 representative | [Stage1](evidence/prefix-import-representative-stage1.log.gz), [stage2](evidence/prefix-import-representative-stage2-fixture-shape.log.gz), [stage3](evidence/prefix-import-representative-stage3-fixture-patch.log.gz) | First two fail because the old reusable fixture simplified lifecycle origin and the first correction did not replace its already-bound method. Corrected NEW helper uses actual `{chain_id,vault}` shape; representative passes. Existing fixture/application unchanged. |
| Other initial import methods | [16-method log](evidence/prefix-import-remaining-stage1.log.gz), [pins](evidence/prefix-import-remaining-stage1-pins.json.gz) |16 new methods pass; representative was not repeated. |
| Pair and unapproved manifest | [Two-method log](evidence/prefix-import-review-pair-stage1.log.gz), [19-stage map](evidence/prefix-import-19-stage-final-pins.json.gz) |2 more new methods pass. Source-stage mapping retains a semantic-free test rename; not19 freshly repeated methods. |
| Later royalty descriptor | [Initial fixture-alias failure](evidence/prefix-import-late-descriptor-stage1.log.gz), [corrected new method](evidence/prefix-import-late-descriptor-stage2-fixture-alias.log.gz), [final pins](evidence/prefix-import-late-descriptor-final-pins.json.gz) |1 additional new method passes: later admission/11 actual raw units/import across retirement/full-replay equality, changed existing meaning rejects. Fixture config lists alias; duplicate append was corrected only in the new method. Prior19 not rerun. |
| CLI/publication representative | [JSON](evidence/cli-publication-representative-01.json), [log](evidence/cli-publication-representative-01.log.gz) |1 real prepared-pair publication method passes against final producer. |
| Other CLI/publication | [Initial25-method stage](evidence/cli-publication-adversarial-01.json), [log](evidence/cli-publication-adversarial-01.log.gz), [10 corrected harness cases](evidence/cli-publication-harness-repair-01.json), [log](evidence/cli-publication-harness-repair-01.log.gz) |15 new methods pass initially. Ten fail because tests expected ValueError for the correctly typed RpcError subclass or constructed an invalid WorkLimit reason. Only those10 repeat after fixing test expectations; all10 pass. No producer/CLI edit. |
| Canonical selected-case map | [26-case provenance](evidence/cli-selected-case-pins.json.gz) | Exact source stages/case AST pins prevent counting repeated10 as new cases. |
| Internal source review | [Initial publication gap](evidence/IMPORT_REVIEW_INITIAL.json), [post-fix review](evidence/DESIGN_REVIEW.json), [accounting review](evidence/prefix-import-independent-accounting-review.json.gz) | Sidecar gap fixed before final publication checks; no additional concrete accounting defect found. No tests or operating proof from these reviews. |
| Reuse and preservation | [Algorithm-body proof](evidence/algorithm-body-reuse.json), [preservation](evidence/PRESERVATION.json), [baseline manifest](evidence/BASELINE.json.gz) | Prior importer reconstructed only if its earlier independent/test-stage digest matches. Critical algorithm ASTs unchanged across publication-only hardening. All14 existing semantic sources and61 Solidity sources stay exact; no unchanged suite rerun. |

**Total:46 unique NEW test methods with passing composed evidence, not one fresh
all46 run.**20 exercise import/accounting and26 CLI/publication. Existing fixture
helpers are reused; their historical test bodies are not selected. Tests use
controlled getter/lifecycle/RPC observations plus actual SQLite/exact replay and
strict codecs/builders. They do not establish EVM/target gas, provider/archive
completeness, maximum-state/host or independent security qualification.

Final housekeeping checks (generated Todo consistency, changed-document links,
canonical two-module inventory without execution, diff whitespace, exact staged
Python import closure and committed closure) are recorded separately during
publication. They are not added to46 and do not execute unchanged test suites.
