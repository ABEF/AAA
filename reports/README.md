# Verification evidence

[Paris28October day audit](day-audit-20261028/VERIFICATION.md): all five reachable
day commits throughb61aecb reviewed, exact raw evidence/source hashes revalidated,
profile/telemetry/gas guidance corrected and requested15-minute buffer recorded
as unimplemented pending method choice. No new test campaign or production approval.

[Fee-adjusted execution quality,2026-10-28](fee-impact-policy-20261028/VERIFICATION.md):
separate Strategy-owned extra1% oracle-relative deterioration after actual core
fees, retained gross/total/caller caps, callback policy binding and explicit
reader profiles. Failed compiler attempts remain recorded; actual market/depth/
service qualification and independent audit stay open. No strategy/site rollout.


[October27-28 change audit](two-day-audit-20261028/VERIFICATION.md): source review of the ten-commit window, principal retry/fairness correction and refreshed operator guidance. Comment-only Solidity fixes preserve ABI/storage/instructions with normal38size gates; prior execution evidence is reused explicitly, not rerun. No economic-attack immunity, service/site rollout or production approval.

[Atomic LP routing and entrant isolation,2026-10-28](atomic-routing-20261028/VERIFICATION.md):
immutable bounded reviewed venues, actual-core sizing/quote rollback, zero/one
swap, entrant-only execution and exact context/balance guards. Explicit API/keeper
capabilities preserve historical profiles. Actual market/depth/gas/ordering,
service rollout and independent audit remain open; no deployment or service change.

[Outside-only upkeep / independent compound,2026-10-27](maintenance-policy-20261027/VERIFICATION.md): Strategy2/Budget3, durable service jitter, matching API profile and explicit historical readers;100affected Solidity methods,396Python passes/2skips and37normal gates. No service/deployment or economic-profitability approval.

[Manipulation-related hardening, 2026-10-27](manipulation-hardening-20261027/VERIFICATION.md): paid-revert health correction, post-callback keeper/pause completion checks and explicitly open economic/ordering qualification. No service or deployment change.

[Coordinated compound cadence, 2026-10-27](maintenance-cadence-20261027/VERIFICATION.md):
fresh capability2, rebalance/range priority, independent harvesting, pinned keeper
eligibility and source-bound normal sizes. Keeper-originated and outside-actor
economic manipulation remain explicit [open work](../TODO.md#task-security-keeper-manipulation).

[Collective holder return, 2026-10-27](holder-collective-exit-20261027/VERIFICATION.md): fresh accounting4/custody3/V5, actual per-NFT ETH+ZZZ principal and retained royalty/reward rights;133affected Solidity passes,37normal object gates and separate backend/keeper scopes. Source-only; no deployment or production approval.


[Current3 website integration](current3-website-20261026/VERIFICATION.md) and
[separate poplint serving](current3-website-20261026/DEPLOYMENT.md) record451JS
passes, seven shell/build checks and three scoped browser cases. Live HTTPS
is unconfigured/read-unsigned; demo remains unchanged. These are separate scopes.
[Current-pool fork](current-pool-fork-20261026/VERIFICATION.md) records11distinct
successful methods across8+1+1+1scopes and11runner cases, with exact pinned
dependencies, explicit mock services and retained failures; not a fresh whole
final suite, independent audit or production qualification.

[Systematic adversarial review](system-adversarial-20261026/REVIEW.md),
[function/source coverage](system-adversarial-20261026/COVERAGE.md) and
[verification](system-adversarial-20261026/VERIFICATION.md) distinguish652 callable
source-review rows/1,987 scenario instances from244 unique affected Python methods:241 passes/3 explicit skips.
The read-RPC and holder CLI corrections preserve source-stage negative controls,
unchanged Solidity evidence, existing services and unrelated drafts. This is
internal audit preparation; real qualification and independent audit remain open.

[Market/input review](market-adversarial-20261026/REVIEW.md) and
[verification](market-adversarial-20261026/VERIFICATION.md) record exact integer
slot0 integrity and223affected Python passes.15actual-v4 composed cases cover
both out-of-range contribution directions, rebalance/claims and actual funded
donations; the first missing-identity fixture failures are retained. Production
Solidity/rights and installed services are unchanged; real qualification stays open.

[Adversarial rewards/keeper review](reward-resilience-20261026/REVIEW.md) and
[verification](reward-resilience-20261026/VERIFICATION.md) record maintenance
outage isolation, consistent pending-error stops and impossible inactive claim
draft rejection. Final 443methods yield 437 passes/6 explicit skips; one new actual-v4
outage/harvest/claim case passes. The first wider regression failure is preserved
and corrected without relaxing its assertion. No production Solidity/service change.

[Reward allocation review](reward-allocation-20261026/REVIEW.md) and
[verification](reward-allocation-20261026/VERIFICATION.md) distinguish harvest
allocation, NFT claims, compounding and actual burns. Two new accounting methods
pass, including 1,000 randomized claim schedules; the keeper fairness fix passes
370 affected Python methods/6 explicit skips. No production Solidity or service
change; exact source and negative-control evidence retain their stated limits.

[Keeper/LP audit](keeper-lp-audit-20261026/REVIEW.md) and
[verification](keeper-lp-audit-20261026/VERIFICATION.md) record config-bound health,
strict conversion controls and repaired verification.354affected Python passes,
5Unix skips and9range methods retain scope; earlier failures/subsets are preserved,
not added to fresh coverage. Production Solidity and running services unchanged.

Current instructions are organized in the [documentation map](../docs/README.md).
[Documentation consolidation](documentation-cleanup-20261026/README.md) replaces
obsolete guide prose without rewriting the historical reports below. Each report
still applies only to its recorded source, deployment and verification scope.
Some older reports contain relative links to now-retired source paths; inspect
the report at its recorded Git revision for that historical code. These are not
current implementation links.

## Backend fee-breakdown remediation - 2026-10-26

[Review](backend-remediation-20261026/REVIEW.md),
[verification](backend-remediation-20261026/VERIFICATION.md),
[history](backend-remediation-20261026/HISTORY.md),
[current profile](backend-remediation-20261026/PROFILE.md) and
[wallet summary](backend-remediation-20261026/OPERATIONS.md) record the five-module
reporting fixes. Final affected suite: 167 distinct Python methods, 31 new and
136 existing. Pre-fix counterexamples remain; earlier overlapping runs are not
summed as coverage. Solidity/economics and running services are unchanged.
Complete authentic logs, actual services and independent audit remain required.

## Full current-candidate audit - 2026-10-26

Started25October: [findings](full-audit-20261025/REVIEW.md),
[coverage](full-audit-20261025/COVERAGE.md),
[verification](full-audit-20261025/VERIFICATION.md),
[readiness](full-audit-20261025/READINESS.md),
[principal](full-audit-20261025/PRINCIPAL.md),
[rights](full-audit-20261025/RIGHTS.md) and
[services](full-audit-20261025/SERVICES.md).
Three current-profile preparation/audit bugs are fixed. Fresh399-flag manual
Slither triage refreshes the current source-review gate. No production Solidity
change, full release regression, independent or real-service approval. Older
stale-static failures retain their dated historical evidence scope.

## Day-change readiness audit - 2026-10-25

[Adapted prompt](day-readiness-20261025/ADAPTED_PROMPT.md),
[scope](day-readiness-20261025/SCOPE.md),
[findings](day-readiness-20261025/REVIEW.md),
[preservation matrix](day-readiness-20261025/PRESERVATION.md),
[verification](day-readiness-20261025/VERIFICATION.md) and
[release gates](day-readiness-20261025/READINESS.md).
Independent review of reference35007db and the full Paris-day ancestry found
reader/replay custody mismatches, contradictory-evidence acceptance and native
test-sensitivity gaps. Those are corrected without changing production Solidity
or deployed state. Fresh and exact reused evidence remain separate; no full
regression, live qualification or independent audit approval is implied.

## Deep cleanup review - 2026-10-25

[Adapted workflow](deep-cleanup-20261025/ADAPTED_PROMPT.md),
[review](deep-cleanup-20261025/REVIEW.md), [verification](deep-cleanup-20261025/VERIFICATION.md)
and [compiler comparison](deep-cleanup-20261025/compiler-comparison.md) record
role visibility, duplicate helper/error removal, repaired native/royalty fixtures,
closed dependency inputs and guarded evidence. No production deployment or
independent approval; older reports below retain their own source scopes.

Current source organization: [auditability refactor review](auditability-refactor-20261025/REVIEW.md),
[verification](auditability-refactor-20261025/VERIFICATION.md) and
[compiler comparison](auditability-refactor-20261025/compiler-comparison.md).
Shared settlement/venue guards, separate converters over a neutral base and
explicit financial identifiers/phases preserve the existing rights and controls.
The [preceding architecture pruning](architecture-pruning-20261025/VERIFICATION.md)
has its own source scope. Historical totals below are not a new full regression,
service qualification or production approval.


Latest residual cleanup: [review](obsolete-code-20261025/REVIEW.md),
[verification](obsolete-code-20261025/VERIFICATION.md). Unused Registry wrapper
metadata and creator-payment measurement are removed; current converter safety,
rights and historical recovery remain.10selected Solidity/6scoped Python cases,
122-input typecheck/36normal object gates; no full regression or deployment.
Earlier reports below keep their original source scope and defaults.

Current service work: [review](release-services-20261025/REVIEW.md) and
[verification](release-services-20261025/VERIFICATION.md) cover optional Pyth
reader, current mint/VRF qualification and frozen-review tooling.17 new Solidity,
87 distinct gate/package Python methods plus focused reference checks across recorded scopes and38 normal object gates;
actual services/marketplace/independent audit remain unapproved. Historical
reports below preserve their original defaults and source scope.

Latest internal audit: [pre-production review](preproduction-audit-20261025/REVIEW.md), [scoped verification](preproduction-audit-20261025/VERIFICATION.md). Keeper budget/preflight fixes, improved composed/invariant evidence and current operator guidance; production NOT APPROVED.

Current inventory tooling: [native preflight verification](native-preflight/VERIFICATION.md) and [internal review](native-preflight/REVIEW.md). These offline/mock checks qualify no real deployment, route, service or independent audit. Earlier contract evidence retains its source scope.

Current scoped candidate: [typed v4 conversion and governed loss policy](typed-v4-routes/VERIFICATION.md), [internal review](typed-v4-routes/REVIEW.md). Defaults1%/1%/3%, governance maximum10%; local evidence is not release approval. Earlier reports retain their source scope.


The historical [local pair-conversion review](pair-composition/VERIFICATION.md)
records a retired typed-pair implementation, reserve accounting and its original
ABI/size scope; governed custody superseded that execution path. Its incremental source scope and remaining qualification are
explicit; it does not replace an independent audit or earlier report bindings.


- [Browser-wallet integration](browser-wallet/VERIFICATION.md): local unsigned preparation, independent signing and canonical recovery; public signing remains disabled.
## User-reported local acceptance - 2026-10-20

[Manual acceptance and priority decision](local-wallet-concurrency/MANUAL_ACCEPTANCE.md)
records six local two-wallet scenarios reported passed by the user. It is not a
new automated run. The [nonce-bound two-mint rehearsal](local-wallet-concurrency/NONCE_VERIFICATION.md)
retains its own receipts and source scope. The large-scale load campaign is
deferred; production capacity remains unverified and release NOT APPROVED.

## Current development review

The [royalty reporting continuation](royalty-reporting/VERIFICATION.md) records
138 affected Python passes plus 20 supplemental cases, exact reuse of unchanged
contract bindings and compiler ABI checks. Currency eligibility and conversion
history are backend features; live services and full earned/USD history remain
open. Its [internal review](royalty-reporting/REVIEW.md) is not an independent audit.

The [review of October 18 changes](daily-security-20261018/REVIEW.md), completed
October 19, assesses all 13 published commits through `485a089` and separates
unpublished local drafts. It includes a new synthetic API availability
reproduction and source-hash checks, not a fresh broad regression or independent
audit. Material risks are linked to the central Todo.

Current handoff work is recorded in [canonical handoff verification](canonical-handoff/VERIFICATION.md), its [internal review](canonical-handoff/REVIEW.md) and [static-analysis scope](canonical-handoff/static/README.md). Each receipt identifies its exact source and whether checks have completed; this index is not a passing test or independent audit. See the [feature and evidence reference](../docs/IMPLEMENTATION_STATUS.md), [central Todo](../TODO.md) and exact-commit Ubuntu CI separately.

Earlier [migration safety](migration-safety/VERIFICATION.md), [architecture evolution](architecture-evolution/VERIFICATION.md), [release hardening](release-hardening/README.md), [artwork test/size verification](artwork-palettes/README.md) and [artwork static review](artwork-palette/README.md) retain their own source scope. Archived review bytes remain alongside those reports; replacing the canonical `production/slither-review.json` does not refresh historical execution evidence.

[Website alignment](website-alignment/README.md), [the future-bridge update](future-bridge/README.md) and [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) preserve earlier implementation/test/fork/gas evidence for their recorded source revisions. Older files in `production/` are not automatically fresh evidence because the review JSON was updated. The release remains blocked by real integrations, production qualification and independent audit. The records below describe earlier deliveries and are preserved in their original scope.

## Original delivery evidence

- `python-tests.json` and `python-tests.log`: the final executed Python test run.
- `verify-attempt.log`: the full verification command; it intentionally exits with failure when Foundry is unavailable.
- `source-checks.json`: narrow textual consistency checks only, not compilation or security analysis.
- `toolchain-install.log`: failed dependency installation evidence.
- `DELIVERY_STATUS.json`: machine-readable release limitations.
- `source-diff.patch`: custom-source changes against the original prototype, for review; not a build script.
- `package-checks.json`: actual packaging checks.
- `history/`: preserved intermediate development test logs, not the final result.

No successful Solidity compiler, EVM, real bridge or independent audit report exists for this delivery.

## Organization and publication pass

- `PUBLICATION_CHECKS.json`: current Windows verification, documentation-link checks, and source-preservation checks. This is separate from the original delivery evidence.
- `publication-python-tests.log`: current Windows test output, including Unix-specific state-test failures.
- `history/README.v0.2.md` and `history/MANIFEST.v0.2.sha256`: unchanged copies of the original package README and manifest.

The root `MANIFEST.sha256` inventories the organized Git snapshot. It excludes itself and Git metadata. Historical reports keep their original scope and are not certificates for this later snapshot.
