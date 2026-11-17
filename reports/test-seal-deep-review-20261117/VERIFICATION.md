# Verification: tests, irreversible boundaries and source stages

Baseline main `003c8d8dc88b60cbfbcc8caf61fa864c6487b40f`.

## Source review versus execution

The earlier30 and later29 method lists are individually assessed, not added to
new passing-test totals. Matrices describe actual assertions, dependencies,
remaining gaps and whether a method was changed or only inspected. Broader
Python/Solidity corpus counts are static inventories, not executed tests.

| Workstream | Distinct selected methods | Meaning |
| --- | ---: | --- |
| Earlier30 improvements | 10 | Strengthened actual assertions and honest two-anchor mutation timing;20 unchanged methods inspected, not rerun. |
| Latest29 improvements | 9 | Eight strengthened methods plus one new tiny-unit/transfer case; source stages precede the later approved reservation change. |
| Chain/root/canonical guards | 6 | Five new cases including actual historical-bytecode controls, plus one adapted constructor case; explicit test/config stages. |
| Reservation behavior | 16 | Four new/twelve adapted; current native-v4 execution and bounded capacity/origin/authority cases. Staged helper corrections remain explicit. |
| Current build/pre-seal review | 7 | Three adapted artifact tests, three new readiness/boundary checks and one new early URI-input rejection check. |
| Critical read ABI validity | 1 | New check against actual trusted target ABIs; private finalization storage is not presented as callable. |
| SeaDrop artwork path | 1 | New exact-runtime mint/reveal/metadata case, controlled platform/provider conditions. |
| Normal-profile permission gate | 4 | Two new and two adapted cases; pre-fix actual-config rejection retained. |
| Corpus corrective cases | 8 | Two new nonvacuous invariant setup smokes and six affected ledger/buyback methods. |
| Current execution fixtures | 18 | One new and17 adapted/affected methods, including the four handoff checks exactly once. |

[SELECTED_CHECKS.json](SELECTED_CHECKS.json) records **80 distinct selected
methods with successful observations at their explicit source stages**. This
is not80 tests against one final tree and is not whole-suite qualification.
Counts exclude fuzz inputs, compiler gates, static detector records, skipped
forks, inventories and repeated executions of a corrected case.

## Original records and current corrections

- [Earlier30 method matrix](EARLIER30_METHOD_MATRIX.json) and
  [execution stages](EARLIER30_VERIFICATION.json).
- [Latest29 method matrix](LATEST29_METHOD_MATRIX.json) and
  [execution stages](LATEST29_VERIFICATION.json).
- [Immutable guard checks](SEAL_GUARD_VERIFICATION.json),
  [all-source inventory](SEAL_INVENTORY.json) and
  [test-only permission proof](SEAL_TEST_CONFIG_DELTA.json).
- [Reservation execution/source proof](RESERVATION_VERIFICATION.json).
- [SeaDrop result](OPENSEA_ARTWORK.json) and
  [safe execution command/scope](OPENSEA_ARTWORK_EXECUTION.json).
- [Normal-profile corrective cases](profile-corpus-after.json) and actual
  [effective-profile CLI](EFFECTIVE_PROFILE.json), which builds/runs no tests.
- [Critical read ABI check](PLANNER_ABI_READ_CHECK.json),
  [corpus corrective stages](TEST_CORPUS_VERIFICATION.json) and
  [execution-fixture stages](CURRENT_EXECUTION_RESULT.json).

One strengthened annotation assertion initially tested the wrong operation's
phrase; only that correction reran. The root build-admission case initially kept
one stale family literal; five other selected cases passed, then only that
corrected case reran. These are test-oracle mistakes, not production defects.
Permission rejection, a superseded large-literal compiler stack failure and the
canonical expectRevert argument-evaluation mistake are classified separately.
No failed attempt is hidden or counted as a behavior pass.

Six reservation fixtures needed the real child binding; the shared deterministic
native accounting venue also lacked the current execution interface. Its adapter
keeps declared toy geometry/prices and forwards actual production math/identity
checks. It does not qualify real markets. Independent actual-v4 cases supply
current physical activation/movement evidence. Eight capacity passes retain an
earlier test-helper stage; their old compiler artifact was not retained and is
not invented. Their raw pass log and exact helper-stage reconstruction are
separate from final current compiler proofs.

The real canonical constructor case has current production sources but one
transitive test-file revision differs; the relevant imported policy body is
unchanged and the difference is recorded. Earlier29 raw planner logs were absent
in the original report; this review does not manufacture them or relabel those
old observations.

## Normal compiler and storage/ABI checks

[BUILD_PINS.json](build/BUILD_PINS.json) authenticates the exact accepted closed
100-source input/output,61 production sources and48 normal object gates under
Solidity0.8.26/Cancun/viaIR/optimizer1/Yulfalse. Semantic storage comparison removes
only AST identifiers and compares slots, offsets and recursive types. All48
layouts match. Existing concrete ABI entries are unchanged; one public read is
added to CustodyValidation.

| Component | Runtime bytes | Margin to24,576 |
| --- | ---: | ---: |
| Oracle | 24,573 | 3 |
| Vault | 24,544 | 32 |
| Budget | 24,507 | 69 |
| NFT renderer | 24,119 | 457 |
| CustodyValidation | 18,868 | 5,708 |

Migration creation44,334+32argument bytes fits49,152 with4,786bytes margin.
No new constructor receipt/full target gas or actual fee qualification is claimed.
The final normal producer authenticates the exact read-only fixture permission
delta; compiler, size, gas and FFI policy are not relaxed.

The two-source first build and oversized Budget/companion probes retain their
original source scopes and failures. Only the final accepted family is admitted
as `seal-boundaries-20261117`; previous operator-seal/metadata2/manual pins remain
historical. Source drift never falls back to old artifacts.

## Actual static analysis

The intermediate571-record analysis keeps its two-source scope. Final analysis
uses accepted four-source compiler output with no additional compilation:
[FINAL_STATIC_REVIEW.md](FINAL_STATIC_REVIEW.md),
[FINAL_STATIC_RESULT.json](FINAL_STATIC_RESULT.json) and
[FINAL_STATIC_CLI_CHECK.json](FINAL_STATIC_CLI_CHECK.json).

All573 records are covered:22 current assessments and551 unique exact-source
reuses. Windows detector-present exit4294967295 is preserved; analyzer JSON
success and the strict check's exit0 are separate facts. Neither detector count
nor accepted disposition proves absence of vulnerabilities or independent audit.

## Final maintenance and limits

Current generated function/operator references and Todo, local link targets,
source/build hashes, exact staged/committed Python imports and protected files
are checked separately in the [completion record](COMPLETION.json) and publication
record. [Retained observations](RETAINED_OBSERVATIONS.json) authenticate the
compressed raw success/failure/intermediate records and drivers. No unchanged full
suite, old long fuzz/invariant campaign or public fork was executed for a new
aggregate count. Whole-project dynamic/market/maximum-state/operating acceptance
remains distinct from these finite checks.
