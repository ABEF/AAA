# Development setup and verification

Use Linux/Unix with Python3.11+ for full keeper/state-lock operation and tests:
`fcntl` and Unix0600 semantics are required. Windows editing/publication and
portable checks do not establish Unix operating acceptance. Solidity is pinned
to0.8.26/Cancun with the committed via-IR/optimizer profile. Use the actual
[Foundry settings](../foundry.toml), [packages](../package.json), lockfile and
[dependency installer](../scripts/install-deps.sh), not an old report's sizes.

## Setup and change verification

From the repository root in the supported environment:

```bash
bash scripts/install-deps.sh
# Full verification when the change/release requires it:
bash scripts/verify.sh
# Documentation/reference consistency without repeating contract suites:
python3 scripts/generate-function-reference.py --check
python3 scripts/sync-project-todo.py --check
```

The full verifier runs Python/source checks, normal build/size gates and offline
Solidity tests. During development run the useful affected suites; preserve
source/command/results/failure evidence. Reuse unchanged-source evidence only
with exact production/dependency/build pins. Source-text checks are not compilation
or security analysis; models are not Solidity execution. Never add overlapping
test counts as new coverage or waive a test by changing the production safeguard.

Dependencies use the committed lockfile and no npm lifecycle scripts. Review
resolved versions and integrity; custom code does not inherit upstream audits.
For the separate Python3.12 static-analysis environment:

```bash
python3.12 -m venv .venv-slither
source .venv-slither/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r requirements-slither.lock
bash scripts/verify-slither.sh
```

The [last full audit](../reports/full-audit-20261025/VERIFICATION.md) records
actual399-findings/47bindings internal static review coverage PASS, successful
solc output and a later Forge host-cache CLI failure. Those are separate facts,
not a current green workflow or independent approval. Check exact-revision CI.
Keep normal runtime/initcode/gas gates and exact constructor arguments.

## Fork and operating qualification

Current fork qualification is blocked until an actual native accounting3 fixture
replaces the archived wrapped fixture; the runner rejects it before RPC/Forge.
Do not copy old Pons/WETH fork commands or fixtures as current selected-pool
qualification. Actual fork/service evidence must name its real chain, block,
dependencies and substitutes. Three layers remain: local adversarial tests,
selected Robinhood mainnet fork and Robinhood Testnet wallet/operator rehearsals.
See [release preflight](PRODUCTION_PREFLIGHT.md) and [sole Todo](../TODO.md).

Current profile: accounting3/governance2/fee1/localV4, ETH/fixedZZZ inputs,
$100activation/$5growth,2/1/3%defaults with10%ceilings, gas separate. Parked status
is4, not a historical code6. Local scaffold is unsealed/local-only; it does not
approve real addresses. The historical local-stack launcher rejects incompatible
current pricing/native artifacts before creating state/processes. Preserve
existing Anvil/journals; use their actual historical configuration.

Use [operations](OPERATIONS.md), [operator manual](OPERATOR_MANUAL.md),
[current context](../PROJECT_CONTEXT.md) and [feature evidence](IMPLEMENTATION_STATUS.md).
Keep keys outside Git. No command here authorizes public deployment or transactions.
No integrated bridge/creator-inbox services are required for this release.
