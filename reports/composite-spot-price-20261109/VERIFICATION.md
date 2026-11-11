# Pool-spot source verification

Scope: new optional [spot reader](../../src/ZZZV4SpotPriceFeed.sol), its
[focused tests](../../test/PoolSpotPriceFeed.t.sol), required-class registration,
reference navigation/default static review and current documentation. No
existing production Solidity is changed. No broad unchanged contract suite was
rerun and no source pair, provider or market is approved.

| Evidence | Actual result |
| --- | --- |
| [Normal compiler input](contract/compiler-input.json.gz), [output](contract/compiler-output.json.gz), [size gates](contract/production-size-gates.json) | Solc0.8.26/Cancun, original via-IR/Yul=false/optimizer profile;99closed sources,48normal gates pass. Reader runtime8242bytes; creation11644+544constructor bytes. Actual Factory child gates remain. |
| [Core equivalence](CORE_EQUIVALENCE.json) | All59previous source hashes unchanged; every preexisting ABI and raw creation/runtime object byte-identical. Existing profile/runtime pins remain valid; no metadata relabeling. |
| [EVM stages](TEST_VERIFICATION.json) | 23distinct methods pass:21initial including1000property inputs, then only2additional boundary methods. Both arithmetic branches, token/feed decimals0..18, original timestamps, malformed/bounded calls, runtime/parent/slot0/fee/L integrity, exact disagreement, snapshot changes, post-seal Oracle admission and500k source-call envelope. Synthetic ABI fixtures do not qualify actual dependencies. |
| [Initial harness failure](tests/harness-failure/forge.stderr.log) | Remapping setup failed before Solidity compilation/tests; retained as zero verification. Corrected only in the external owned harness. |
| [Actual analyzer execution](static/EXECUTION.json), [raw output](static/slither.json.gz), [strict review](static-review.json), [coverage](static/review-coverage.json) | Successful offlineSlither over final normal output;560records,558unique exact referenced-source reuses and2new individual reviews. Existing transitive review limits retained. Nonzero analyzer findings exit is not an execution failure or audit approval. |
| Affected Python checks | 95reference/operator/static-review methods pass at initial stage. Final documentation links expose a constructor-only tuple omitted from expansion; new regression reproduces it, then corrected generator passes21operator methods including the new regression. These overlap the95stage. Source inventory: one initial pass, one stale SeaDrop-helper assertion failure; corrected required-class list and rechecked only that failed method successfully. Two distinct inventory methods ultimately pass; no overlapping pass counts added. |
| Generated and source checks | Full40contract/913function/40constructor/13receive reference: no explanation/input/output gaps;966explicit operator rows. Todo/reference/operator consistency, source inventory and local-document links checked. |

The high-sqrt branch's truncated X128 denominator can differ from the exact
rational by at most one USD18 raw unit at an integer boundary. This limit is
explicit; the existing conservative financial budgets are not widened.

The stage1 test source is retained at its original hash; stage2 appends only two
methods and tests only those additions. Production source is identical across
both stages. Current static findings concern timestamp use and bounded assembly;
the [individual rationales](static/static-current-reviewed.json) disclose spot,
proxy, chain-time and gas limits rather than marking these dependencies safe.

Actual pool/TVL ranking, own-L exclusion, external bidirectional depth, independent
second ZZZ path, ETH publication/liveness, target-chain gas and operating
qualification remain open. The reference must not be mutated by the complete
contribution: source fingerprint freeze can reject using it as destination or
executed swap venue. No core check is bypassed to make that configuration pass.

The [task-start record](START.json), [copy hashes](evidence-copy.json) and final
verification records preserve original evidence and protected-file boundaries.
The final link regression and all expanded constructor fields are reconciled in
[final closure](final-closure.json); the earlier failed link check is retained.
No deployment, source admission, public transaction, service/site/signer/Anvil/
journal change or paused-heartbeat restart was performed.
