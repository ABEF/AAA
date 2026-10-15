# Verification evidence

## Current development review

Current source evidence is [release hardening](release-hardening/README.md), including [fresh internal static analysis](release-hardening/static-analysis/README.md), bounded metadata notifications and optional keeper monitoring. That review corresponds to the current `production/slither-review.json`; its prior bytes are preserved in `history/slither-review-pre-release-hardening.json`. It is not an independent audit. Earlier [artwork test/size verification](artwork-palettes/README.md) and [artwork static review](artwork-palette/README.md) retain their source scope. See the [Implemented / Todo checklist](../docs/IMPLEMENTATION_STATUS.md) and exact-commit Ubuntu CI separately.

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
