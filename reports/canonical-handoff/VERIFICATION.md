# Canonical handoff verification

**Local development evidence; NOT production approval.** The focused checks below
have completed. The 2026-10-18 offline regression also passes on unchanged source. Prior
migration/preparation reports do not verify this changed source.

| Check | Recorded result | Scope |
| --- | --- | --- |
| [Focused handoff execution](focused/verification.json) | 34 passed; no failures or skips | Complete 1,000-NFT inventory; maximum local asset/bucket domain; exact backing; import/abort/retirement; late receipts; interrupted settlement and repeated handoffs |
| [Normal production build](build/verification.json) and [size gates](build/size-gates.json) | 30 objects pass runtime/initcode-object limits; all 39 production sources bound | Solc 0.8.26, Cancun, normal repository optimizer/via-IR settings; constructor arguments are not included in initcode-object figures |
| [Static analysis and internal review](static/README.md) | 374 individually recorded dispositions; coverage passes; 10 mutations rejected | 153 false positives, 75 accepted risks, 146 informational; not an independent audit |
| [Production configuration validation](config-verification.json) | 141 tests passed | Lifecycle/origin, companion/factory ownership, manifests and admission gates; no actual production addresses approved |
| [Keeper lifecycle checks](keeper/verification.json) | 88 tests passed, unchanged source hashes confirmed | Reuses the completed targeted run for these same keeper sources; existing server staging is unchanged |
| [Current offline regression](regression/verification.json) | 582 passed; zero failures; two intentional fork setup skips; 49 bound suites | Includes repaired bridge mock interfaces and all three updated cold-gas suites; 1,764.125 seconds; sources unchanged |
| General cold-gas qualification | All ten cases pass within the current regression | CollectionScale, CombinedCapacityGas and ProductionGas include final helper cooling; no duplicate gas run was needed |
| [Additional keeper checks](keeper/resume-20261018/README.md) | 123 distinct supporting cases pass; one Unix permissions case remains for Ubuntu | 122 initial passes plus the previously skipped cast parser case; separate from the reused 88-case receipt |
| [Local deployment script](deployment-script-typecheck.json) | Type/ABI compilation passes | No local/public deployment, bytecode-size or operating rehearsal claim |

The [reuse receipt](reuse-verification.json) checks 87 focused-test dependencies,
78 normal-build dependencies, configuration/keeper sources and all 42 normalized
static-review source/configuration entries. The 582-case regression and earlier
34-case focused run cover **616 successful offline cases** across 50 suites;
this is combined source-matched coverage, not one newly executed 616-case run.
The selected-market fork suites remain opt-in and were not executed locally here.
Exact-commit Ubuntu CI, operating rehearsal and independent audit are separate.

The unchanged handoff call budget is 12,000,000 measured execution gas. The
maximum-domain fixture cools system storage for capture, domain settlement and
commit, and enforces the limit; it also checks each eight-row relay and funding
call. The scale fixture resets the test meter **between** export/import batches
to represent separate transactions, while measuring each call normally. These
are local EVM fixtures, not target-chain transaction quotes or operating rehearsals.

Current runtime/initcode-object bytes are Vault 24,543/41,255; Migration
24,518/25,044; NFT 23,265/42,786; Handoff 21,029/21,666. Vault has only 33 runtime
bytes of headroom and Migration 58. Deployment review must also account for
constructor arguments and exact chain limits.

The fresh production compilation produced all artifacts, then the restricted
Windows process failed to access Foundry's signature cache. Its
[original receipt](build/fresh-compilation.json) and stderr are preserved. The
subsequent authorized normal build reused those exact artifacts, exited zero and
passed all size gates. It is a successful cached build, not a second fresh compile.

The candidate implements only direct same-chain handoff. Cross-chain finalized
proofs, transport and channel closure remain unimplemented. No contracts have
been deployed; no website or existing staging service has been changed.

Development attempts and raw logs are retained outside Git under the task's
`handoff-20261017` artifact directory. Failed compilation/size/test attempts are
not merged into later passing results. The original maximum-domain atomic
freeze/settle call exceeded 12M; the fixed version captures cutoffs atomically and
settles domains separately. Test-harness corrections (a missing interface getter,
meter-reset scope and synchronizing pending royalty receipts before asserting
claimable amounts) preserve the original failed attempts.

Historical diagnostic results remain preserved: the earlier regression had
576 passes/six failures/two skips and stale source bindings; the earlier general
gas run had ten successes with stale fixture bindings. Neither is relabelled.
The current bridge fixes supply the real sealed companion lineage interface in
test mocks, preserving the production guard. Raw logs are retained externally
with hashes and compact outcomes in [current regression](regression/README.md)
and [historical diagnostic](diagnostic/regression/README.md).

See [internal review](REVIEW.md), [implementation boundary](../../docs/CANONICAL_HANDOFF.md)
and [evidence hashes](evidence-manifest.json). Nothing here authorizes public
transactions, sealing or use of real funds.
