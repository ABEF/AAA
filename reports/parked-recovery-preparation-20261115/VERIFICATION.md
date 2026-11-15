# Verification scope

Baseline: `fce0ac27952997d8501098a96743603d4ff2a236`.
The archived baseline manual module is mechanically byte-equal to Git. Current
source/test hashes and preserved boundaries are in [ROOT_REVIEW.json](ROOT_REVIEW.json).

| Stage | Actual result | Meaning |
| --- | --- | --- |
| Initial new-test baseline attempt | [Raw log](baseline-new-tests.log) retained | Earlier test shape, before fixture correction; not current source acceptance. |
| First post-edit fixture attempt | [Raw log](first-post-tests.log) retained | Failed injected-custody fixture/setup; corrected, never presented as a passing candidate. |
| Final17 methods against archived baseline | [JSON](baseline-final-tests.json), [log](baseline-final-tests.log):17 methods,47 failing subtest assertions and18 errors | Missing explicit Parked capability demonstrated; these are subtest failures/errors, not65 distinct methods or production bugs. |
| First accepted source stage | [JSON](post-fix.json), [log](post-fix.log):17 methods pass,0 skips | Source/test pins unchanged across run. |
| Two additional methods against baseline | [JSON](baseline-delta.json), [log](baseline-delta.log) | Both new cases reject before the capability exists. Not additional unique defects. |
| Delta only on accepted source | [JSON](post-fix-delta.json), [log](post-fix-delta.log):2 methods pass,0 skips | Both-direction exact inventory boundary and explicit execution1/LP3 controls. Earlier17 not rerun. |
| Final test-file equivalence | [AST comparison](post17-final19-method-reuse.json) | All17 previously executed methods and fixture helpers unchanged; final total19 unique new methods. |
| Active compatibility | [Full artifact byte comparison](active-artifact-comparison.json) | Three freshly compared B/C/D artifacts are byte-identical to baseline; no old test method executed. |

Coverage includes explicit opt-in/state, all32 masks (eight supported2/4/8
combinations and24 Active-only incompatibilities), exact nonzero zero-ID hashes,
other-bucket residual allowance, custody/alias/inventory/asset/runtime proof,
idle/compound-only backing, both swap directions, exact calldata/floors/deadline,
current execution1/LP3 source controls, late state/permission/price-simulation
failure, expiry/reorg/funding/gas limits, sanitized errors and exclusive CLI output.
Successful injected voids prove preparation handling, not retained on-chain
guard eligibility, token settlement, target gas or provider truth.

Root verification also checks generated Todo, unchanged contract/operator
references, new documentation links, Python publication closure and preserved
source pins. [Completion](COMPLETION.json) records the actual mechanical results;
an inventory-only run executes0 tests. Broad financial, Solidity, browser,
compiler and static suites are reused only in their unchanged source scope.

No public RPC, key, signer, transaction, service/site/chain reset or journal edit
is used. Original dirty docs are archived outside Git before updates. Preserved
raw logs keep their exact bytes, including whitespace; whitespace validation of
edited source/docs excludes those raw evidence logs only.
