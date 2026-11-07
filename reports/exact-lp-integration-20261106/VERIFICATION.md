# Verification, source scope and retained failures

**Not independent approval, full published CI or target-chain qualification.**
Campaign baseline main64f9bfb; actual final source inputs, tools, config, outputs
and failures are immutable packaged evidence, not substituted latest results.
See [review](REVIEW.md), [physical manifest](COPY_MANIFEST_PHYSICAL.json) and
[copy validation](COPY_VALIDATION_PHYSICAL.json).

## Real normal build and static review

Final normal stage `normal-final-5994e91eed` compiles87actual production/dependency
sources, passes46normal object gates and two actual Factory code-data carrier
gates under unchanged0.8.26/Cancun/via-IR settings. No fixture size exemption is
used as a production result.

| Contract | Runtime bytes | Runtime headroom |
| --- | ---: | ---: |
| Vault | 24,443 | 133 |
| Rewards | 24,218 | 358 |
| RewardsCanonical | 18,609 | 5,967 |
| CanonicalHandoff | 24,544 | 32 |
| LiquidityManager | 22,411 | 2,165 |
| MigrationBudget | 24,018 | 558 |

Rewards creation44,703bytes plus32constructor bytes fits the normal49,152limit.
Earlier inline Rewards31,068runtime and first extracted Rewards25,380runtime
FAILED normal gates; both are preserved under `contract/stages`. The successful
split moved the typed codec and canonical source validation, not financial guards,
compiler settings or allowed limits.

Final actual analyzer stage `static-4e89b2781d` reports532records:
**222individually reassessed current contexts /310unique exact referenced-source
reuse**. [Full strict record](static-review.json), [actual normalized detector
payload](static-detectors.json), [coverage](static-coverage.json). The strict
checker passes against the actual raw output; its CI default now selects this
record. The Windows analyzer process exit4294967295 remains recorded alongside
its JSON `success=true`; it is not silently changed into process exit0.
Exploratory224/308 classification is retained but superseded by final222/310,
without relaxing fingerprint/source matching.

Only two NatSpec lines changed between executable stage `7e38e0a291` and final
`5994e91eed`. [Comment equivalence](contract/provenance/COMMENT_ONLY_EQUIVALENCE.json)
proves all87executable ASTs (including declaration references/IDs) and ABIs equal,
excluding only comments/source-location spans. Earlier host tests retain their
actual raw pins and are not falsely described as having executed later bytes.
The unchanged primitive-engine17cases retain their prior report scope and were
not needlessly rerun for comments.

## Canonical host verification

[Canonical verification](canonical/CANONICAL_VERIFICATION.json) records
**34distinct final-stage EVM methods**:23final plus11justified closure reruns,
including two1000-run fuzz methods. Actual final5994source/config/tool/test
closures are frozen. Coverage includes exact pending/phase/direct round trips,
future-credit/growth/claim equivalence, tiny units, zero collection, fully funded
abort, prefunds, interrupted chunks/funding, canonical cutoffs and malformed
node/phase/leaf/unminted/spare-domain rejection. Parent hooks reject non-child
callers; source books remain unchanged through abort.

An initial empty test-selector attempt, callback-funding/native fixture errors,
one diagnostic timeout and a test-closure drift are retained under
`canonical/historical`. Corrected fixtures use actual Vault/native identity;
guards were not widened. The affected11methods were rerun against final closure;
earlier successes are not double counted.

## Backend and actual producer/consumer verification

[Backend package](backend/INDEX.json) records **619distinct corrected affected
Python methods**, with per-method/stage provenance rather than summed overlapping
runs. Actual production Vault emitted77literal logs and FOUR26-field getter snapshots
through mint, activation101e18raw shares,20raw units of each fee currency,
growth5/dormant NFT and18raw units claimed per currency with zero final reward liabilities. Independent replay matches whole
components and historical earnings; claims/conversions/import are not income.
The producer uses controlled venue/VRF/authorities and normalized feeds, not live
Robinhood dependency qualification.

Caught and corrected consumer faults include missed fresh7 dispatch and a pool
bool tuple-index replacement error (44failures/6errors retained). A manual
share-writer transcript without actual Vault events was rejected as producer
evidence and replaced by the real Vault transcript. Source7 keeper/API configuration rejection
occurs before RPC/journal access. The25listed historical files and F2 artifact
remain byte-identical. Neutral shared readers are intentionally adapted with
explicit historical branches; this is not a claim every old reader file is unchanged. New F3payload-spec3 uses unchanged code-storage format2 and
verified final constructor bytes; parent/child/data runtime pins are explicit.

Raw7 history works; checkpoint1 intentionally rejects7. Exact-unit checkpoint2
and actual lifetime workload/archival/restore remain unimplemented qualification
work. No existing database/service/checkpoint/journal was relabeled or migrated.

## Reference and publication checks

95focused static-review/function-reference/operator-reference Python methods
pass. Source consistency checks find56source classes and zero errors; they are
not a Solidity security analyzer. Source-bound reference and short tables check
38contracts,844functions,38constructors,13receive hooks and895example rows with
zero input/output/description gaps and `ready_for_submission=false`.

Final task generation, links, preservation, staged Python import closure and
local/remote publication proofs are recorded with the final publication checks.
Original report scopes/failures and all environment boundaries remain intact.

## Complete-host and gas evidence

[Accounting package](accounting/INDEX.json) and its
[final review](accounting/records/FINAL_ACCOUNTING_REVIEW.json) record54distinct
methods across16host, one actual-Vault producer,35native controls and two
actual-v4 accounting methods. Canonical34 is a separate explicitly listed scope;
do not add attempted, repeated or failed methods to either total.

14distinct exact-host methods cover tiny-unit conservation,1,000mint ordinals,
37wallets/900activated participants/four buckets, changing shares, dormant
eligibility, current-owner/router claims, rejecting payouts, same-component
conversion rollback and currency-deficit isolation. Eleven unchanged methods
and three corrected/new methods retain per-function provenance; the initial
router-prank and zero-entitlement fixture errors remain preserved, not counted.
The older-stage executable reuse is limited by the NatSpec/AST proof above.

| Controlled cold host call | Raw execution gas | Limit interpretation |
| --- | ---: | --- |
| Single native LP claim | 1,259,505 | Actual Rewards/NFT/Fees/Membership; authenticated synthetic share writer. Excludes intrinsic/calldata/refunds and actual target fees. |
| Post-write growth, both books | 1,213,300 | Synthetic authenticated share writer, not the complete activation transaction. |
| Router32entries /16NFTs /4buckets /ETH+ZZZ | 31,085,813 | Funded exact payouts pass, but this DOES NOT fit the unchanged12M service budget. Planner must simulate smaller prefixes; do not call it maximum-batch qualification. |
| Router8entries /4NFTs /4buckets /ETH+ZZZ | 8,819,431 | Same cold fixture; within12M raw call budget, not universal8-entry approval. Existing final simulation/estimate and transaction overhead still apply. |

35native Vault methods pass across explicit stages:33unchanged successful
methods plus two corrected cases, with exact per-function provenance. Corrected
tests now verify the unminted caller retains1ETH on an old-selector rejection,
and prove the unsealed rejection against a complete bound graph with exact
NotReady plus a positive sealed mint. Two selected actual-v4-core methods prove
entrant-generated fees belong to incumbents before new shares and both-leg entry
checkpointing/second-leg rollback. The final four-method stage passed4/4; it
reran only the corrected two native cases plus those two core controls.

Final complete src/test/script ABI closure covers315sources with zero errors
and exact before/after raw hashes. This is type checking, not EVM execution.

One broader45-class fixture compilation exhausted host memory before EVM
results. Only the owned Forge/compiler process tree was stopped; that attempt
is retained as a resource failure, not a passing or failed accounting assertion.
Priority smaller closures and source-bound test-construction improvements are
reported by their actual subsequent stages; no production guard/limit changed.

The accounting package records exact method/source stages, cold gas and affected
regression outcomes. Measurements distinguish single call gas from cumulative
rehearsal/deployment gas; no count ceiling or harness envelope qualifies the
actual provider, maximum populated batch, target-chain block gas or fees.
Use smaller freshly simulated router batches/individual claims as necessary.
Real operating and independent approval remain open.

[Test maintenance](TEST_MAINTENANCE.md) separates current/native porting from
historical retirement and exact unchanged-function reuse. Later changes to only
two unselected VaultAccounting test bodies leave imported declarations/helpers
byte-identical: native95closure has94other raw-exact imports; each canonical
105closure has104. Original frozen snapshots and the explicit reuse proof remain
preserved; these are not claims that every later test file has identical bytes.

Final publication formatting removed only one extra EOF newline from the new
CanonicalNativeVenue test helper. [Exact byte proof](root/TEST_EOF_PROOF.json)
retains its earlier raw hash and proves all declaration/body bytes unchanged;
all other314type inputs remain raw-exact. Earlier canonical snapshots/reuse
proofs retain their original hashes, not a claim of later raw-file identity.
