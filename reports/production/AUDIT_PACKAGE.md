# Current audit handoff package

This index accompanies the exact Git revision and root `MANIFEST.sha256`. It is an internal engineering package, not an audit certificate. Review current sources and dependency locks; historical reports apply only to their own revisions.

| Material | Location / purpose |
| --- | --- |
| Current verdict, threat boundaries, changes and blockers | `reports/PRODUCTION_READINESS.md`, `docs/RELEASE_CHECKLIST.md`, `SECURITY.md` |
| Architecture, economics and market scope | `docs/ARCHITECTURE.md`, `docs/ECONOMICS.md`, `docs/ROBINHOOD_POOL.md` |
| Custody/module source and minimal ABIs | `src/`, `src/interfaces/IZZZ.sol`, `src/libraries/ZZZTypes.sol` |
| Toolchain and locks | `foundry.toml`, `package-lock.json`, `requirements-slither.lock`, `scripts/install-deps.sh`, `.github/workflows/verify.yml` |
| Local unit/fuzz/stateful/gas coverage | `test/`, especially `ProductionInvariants.t.sol`, `ProductionGas.t.sol`; retained final logs and invariant evidence in this directory |
| Deployed dependency fork and market observations | `test/UniswapV4Fork.t.sol`, `current-pool.json`, `robinhood-fork-tests.log`, `bridge-capabilities.json` |
| Fresh uncached archive verification | `robinhood-fork-uncached.json` / `.log`, `scripts/run-fork-checks.py`, `tests_python/test_fork_runner.py`; read-only paced relay, actual upstream responses |
| Current router source, tests and internal secondary review | `../future-bridge/README.md`, `../future-bridge/secondary-security-review.json`, `../../docs/BRIDGE_ONBOARDING.md` |
| Current analyzer output and every recorded disposition | `../future-bridge/slither-final.json`, `../future-bridge/slither-final.log`, `slither-review.json`; `scripts/check-slither-review.py`. Earlier raw output stays in this directory, with its original review in `../history/slither-review-4924d0f.json`. |
| Foundry lint output and individual rationale | `final-build.log`, `forge-lint-review.json`; timestamp-range assumptions are identified explicitly |
| Operational code and regressions | `keeper/`, `indexer/`, `zzz_ops/`, `tests_python/`; `docs/OPERATIONS.md` |
| Unready inventory and fail-closed validation | `config/production.example.json`, `scripts/validate-production-config.py`, `tests_python/test_production_config.py` |
| Historical source/review provenance | `reports/history/`, `docs/AUDIT.md`, previous implementation and CI-repair reports |

Reproduce from a fresh clone using `docs/DEVELOPMENT.md`. Hashes in `slither-review.json` use LF-normalized source bytes for Windows/Linux portability. Runtime hashes in the real dependency inventory are Ethereum Keccak; deployment runtime hashes must be recomputed with actual immutable constructor values. The root manifest inventories Git file contents and excludes itself. Never include credentials, signer keystores, RPC secrets, private operator configuration or repository-local personal notes in an audit archive.

External review priorities: permanently non-redeemable custody and exact funds segregation; mint payout/receiver callbacks; lifetime Power timing/rounding and 32-asset costs; oracle denomination/manipulation/outages; authenticated swap callback/Permit2 settlement; ordered custody epochs and ACK recovery; immutable token provenance/legacy remote rewards; post-seal future-provider/route governance, immutable policy identities, pending old-provider settlement and malicious destinations; production bridge exact backing/finality/recovery; keeper ambiguous transaction recovery and RPC/signer isolation. Review the selected reward/settlement model after the user supplies it.

The package intentionally has no approved production deployment script, transport, payout agreement or ZZZ price source. Passing internal checks does not waive these missing components.
