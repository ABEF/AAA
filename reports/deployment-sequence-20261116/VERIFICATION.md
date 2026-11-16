# Source-scoped verification

Baseline main: `4a3b30dd8d85d923d97d1892568280eec8328ce1`.
[EVIDENCE.json](EVIDENCE.json) binds each losslessly compressed file and its original
SHA/length. The old constructor reviewer/builds remain exact; new source stages,
failed cases and reuse boundaries are retained rather than relabelled.

| Stage | Evidence | Result / scope |
| --- | --- | --- |
| Capability baseline | [Record](evidence/sequence-core-baseline-capability.json.gz), [baseline](evidence/BASELINE.json.gz) | New module/CLI absent at exact baseline. No old tests executed. |
| Offline reference vectors | [Cast vectors](evidence/cast-create-vectors.json.gz), [driver](evidence/generate-vectors.py.gz) | Recorded public-address computations with exact executable/version/hash and minimal environment. No key/RPC/node/EVM. These are reference calculations, not extra method passes. |
| Core math representative | [JSON](evidence/sequence-core-representative-math-01.json.gz), [log](evidence/sequence-core-representative-math-01.log.gz) |1 new method passes first try at frozen module/CLI. |
| Current constructor composition | [JSON](evidence/sequence-core-representative-prepare-01.json.gz), [log](evidence/sequence-core-representative-prepare-01.log.gz) |1 new method passes: actual current strict preparation with derived25addresses. No constructor execution, compiler or old suite. |
| Remaining core | [JSON](evidence/sequence-core-remaining-01.json.gz), [log](evidence/sequence-core-remaining-01.log.gz), [18-method union](evidence/sequence-core-18-final-pins.json.gz) |16 other NEW methods pass once; preceding2 excluded. All18 disjoint. Accepted44receipt/transaction members and public archive hashes check25addresses/19binding offsets offline; old source/runtime/gas scope stays historical. |
| CLI representative | [JSON](evidence/sequence-cli-representative-01.json.gz), [log](evidence/sequence-cli-representative-01.log.gz) |1 new method passes. Preparation injected; real argument/dispatch contracts checked. |
| Other CLI/publication | [Initial19-method stage](evidence/sequence-cli-remaining-01.json.gz), [log](evidence/sequence-cli-remaining-01.log.gz) |18 methods pass; one fails on real abbreviated-option ambiguity. No deployment/signing path existed. |
| Exact-option correction | [Fixed affected method](evidence/sequence-cli-abbreviation-fixed-01.json.gz), [log](evidence/sequence-cli-abbreviation-fixed-01.log.gz), [20-case proof](evidence/sequence-cli-final-pins.json.gz) |Only the failed method repeats after `allow_abbrev=False`. Other19 successful CLI methods are not rerun. Complete CLI AST differs only by this constructor keyword; original bytes are preserved. |
| Internal independent source review | [Core](evidence/INDEPENDENT_SEQUENCE_REVIEW.json.gz), [CLI](evidence/SEQUENCE_CLI_REVIEW.json.gz) | Confirms nonce/RLP/44-step/collision/composition/conditional-authority/publication controls and remaining assumptions. No additional tests or independent release approval. |
| Final source/preservation | [Pins](evidence/FINAL_SOURCE_PINS.json.gz), [preservation](evidence/PRESERVATION.json.gz) | Final new source/test/producer hashes and38method ASTs; all prior Solidity, constructor planner/builds, semantic sources, existing Python/report and protected dirty files preserved. Hash checks are not new static/EVM runs. |

**38 unique NEW methods with passing composed evidence, not one fresh all38 run.**
18core+20CLI selections are disjoint; repeated failed stages and Cast/receipt
reference calculations are not added as more methods. Final selected cases have
no skips. Accepted normal source/ABI/size and historical receipt evidence is reused
only for its stated scope. No unchanged suite, compiler/static/browser/EVM,
provider probe, public transaction, seal or existing-chain action was performed.

The final publication additionally checks generated Todo consistency, current
document links/operation anchor, canonical new-test inventory without execution,
whitespace, and exact staged/committed Python import closure. These are mechanical
checks, not extra test passes or CI-green/production claims.
