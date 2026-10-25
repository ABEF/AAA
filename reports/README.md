# Verification evidence

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
