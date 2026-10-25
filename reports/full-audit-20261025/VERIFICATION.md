# Full candidate audit verification

Initial source main `e32e966`; current production Solidity44sources still equals
35007db. This campaign changes three backend Python modules, two new Python
regression modules, one Solidity test fixture, current static triage and docs.
It changes no production contract, dependency, compiler, signing or deployed state.
The final publication manifest binds exact owned files; older reports keep
their earlier source scope and are not added to fresh counts.

## Fresh backend regressions

| Campaign | Before / after | Evidence |
| --- | --- | --- |
| Current activation profile composition | Five new methods initially expose six subcase errors; historical profile2 positive already passes. Same fixture after two fixes5/5pass in4.391s. | [Before](activation-profile-before.json), [after](activation-profile-after.json). Existing/new pool ETH activation, growth, exact ZZZ approval, native-zero negatives and profile status boundaries. |
| Actual Rpc→history-audit composition | Four new methods: one real-adapter integer-chain-ID failure, three valid/negative controls already pass. After narrow fix4/4pass in0.672s; same test bytes. | [Before](history-transport-before.json), [after](history-transport-after.json). Actual Rpc with only offline HTTP transport seam, actual temporary SQLite; read-only evidence. |
| Affected legacy/typed-zero compatibility | Two existing directly affected methods pass once at final source. | [Compatibility](services-compatibility.json),0.938s. No duplicate imported suite counted. |

Total **11distinct final passing Python methods**:9new,2existing, across three
explicit selections. Old83day-audit methods are reused only where their source
is unchanged; they are not rerun or counted in this fresh11. No new assertion
was weakened or fixture changed between the recorded before/after captures.

## Fresh composed EVM gas/accounting scenario

Exactly one final selected method,
`testMaximumOptionalRoyaltyGasFaultsFitReviewedActivationBudget`, passes in
108.329s including focused compilation. Test-source SHA and unchanged four old
public methods are recorded in [the manifest](principal-gas-verification.json).
The first exploratory test expected12Mfailure; the actual operation succeeded,
so only that hypothesis assertion failed. Its source/result remain archived.
The unnecessary20Mdiagnostic was removed; no production gas floor/cap changed.

Measured activation CALL raw gas9,591,082<12,000,000; full test14,347,040includes
later recovery/assertions. The cold-account/storage helper is the existing
documented Vm.cool behavior. Four buckets/33LPassets/16optional token faults and
native eligibility, fair shares/exact debits/earlier rewards are checked. This
fixture mocks venue/access/prices/VRF: actual native Entry/v4/target-chain gas is
still NOT VERIFIED. Other old gas methods were not rerun.

One changed test input is refreshed in the closed265-input AST at12.25s. All44
production/31normal dependency/four build bindings remain unchanged. Normal37
gates are reused by that focused test driver; the separate fresh static-build
output comparison below checks all37object lengths again without another compile.

## Fresh static analysis and compilation evidence

- One isolated Forge compilation runs pinned solc0.8.26/Cancun/viaIR/optimizer1/
  Yul disabled; complete input/output sources86, including44production,32dependency
  and10test helper units. Solc reports zero errors and emits ABI/AST/bytecode.
  The extra test helpers are compiled by Foundry despite test-root skipping;
  analyzer filtering excludes test/script/dependency findings.
- Forge then exits1 because the Windows host local-signature cache directory is
  unavailable. This failed overall CLI is preserved, not called a successful
  normal verifier. The complete compiler artifacts are explicitly passed to
  Slither with compile disabled; no production rebuild was repeated to hide it.
- The first analyzer bootstrap lacks Forge in subprocess PATH and produces no
  detector JSON. Its log is preserved; adding only the task-local Foundry PATH
  allows the completed analyzer run in19.25s. No global PATH/cache/install or
  operating service changes.
- Slither0.11.6 succeeds with no analyzer error. Windows finding exit status
  is4294967295; the valid success JSON is inspected, not mistaken for tool failure
  or a clean zero-findings result. All48installed Python package versions match
  the committed lock; original wheel integrity is not retroactively proven.
- Full raw JSON with compilation archive79,349,338bytes stays external with SHA.
  The tracked detector-only projection preserves all399actual detector records.
  [Execution](static-execution.json), [versions](static-tool-versions.json).
- All399fingerprints are manually reviewed:165false_positive,152accepted_risk,
  82informational. Every47required source/build LF binding matches. The actual
  checker CLI returns `review_coverage_pass:true`/`independent_audit:false` against
  the updated current triage. [Coverage result](static-review-verification.json).
  Accepted loop/custody risks remain unqualified release dependencies.
- [Fresh size comparison](static-size-comparison.json): all37production object
  creation/runtime lengths equal the saved normal75-input capture and pass normal
  static size limits. Actual dynamic release arguments remain unqualified.
  Vault runtime22,852; RoyaltyFactory69-byte runtime margin remains. Production
  code, function ABI and storage are unchanged; no new code-size allowance.

## Final validation and reuse

Before publication, the source-bound callable reference, sole generated Todo,
static-review checker and local Markdown targets are checked. Final source/
dependency/build/test/evidence hashes and all14original dirty-file bytes are
verified; partial document prefixes are staged separately. Python syntax for
owned sources is parsed. Source-consistency output is written to this campaign,
not over the unrelated dirty reports/source-checks.json.

These are source/document bookkeeping checks, not additional financial tests.
No full final-release regression, actual RPC/fork/route/feed/VRF/OpenSea/wallet,
service operation or independent audit was run. No published CI green result is
claimed. Normal unchanged build/reference/economic evidence retains its exact
capture; this campaign does not relabel it as new broad testing.

Real authority addresses and deployment configuration, current website3
compatibility, fixed-ZZZ burn behavior, actual feeds/routes, whole-collection
liveness, known admitted-only late-currency recovery and trusted custody remain
as described in [findings](REVIEW.md) and [release gates](READINESS.md).
Production remains **NOT APPROVED**; nothing is deployed by Git publication.
