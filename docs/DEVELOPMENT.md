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

## Focused keeper verification

```bash
python3 scripts/run-keeper-tests.py --output path/to/new-keeper-results.json
```

The maintained CI selection deduplicates defined test classes and covers keeper,
metadata, native/conversion and recovery helpers. Unix-only assertions remain
explicit on other hosts; Windows success does not qualify Linux operation.
[Latest evidence](../reports/keeper-lp-audit-20261026/VERIFICATION.md) records the
initial failures/repairs,359selected354pass5skips and9affected Solidity passes;
it is not a new full release regression or production qualification.

## Fork and operating qualification

The separate [current native-pool harness](../test/CurrentNativePoolFork.t.sol)
and [bounded read-only runner](../scripts/run-current-pool-fork.py) replace the
archived wrapped fixture for this campaign. [Verification](../reports/current-pool-fork-20261026/VERIFICATION.md)
records11distinct successful methods across source-bound affected runs, not a
fresh whole final11-case pass. Pinax served the fixed chain4663 block; mock
governance/VRF/correlated USD feeds and fork-funded balances are explicit.
ETH100 activation, ETH5 growth and ZZZ100 activation pass in the stated fixture;
an unfillable larger growth quote correctly reverts with atomic backing intact.

From the repository root, replace the executable/output placeholders:

```sh
python scripts/run-current-pool-fork.py --solc REVIEWED_SOLC_0_8_26_PATH --output NEW_EVIDENCE_DIRECTORY
```

Forge must be on PATH or supplied with `--forge`. The runner checks the pinned
Forge/solc versions, strips inherited compiler overrides, verifies the effective
normal Forge configuration and actual source inputs, creates an exclusive output, uses
the keyless Pinax endpoint by default, and permits only read RPC methods through
its bounded serialized relay. Optional `ROBINHOOD_FORK_RPC_URL` comes from outside
Git; do not paste credentials into commands or logs. It never broadcasts. A
future whole run must contain all11expected methods with no skips; the legacy
dirty runner and old fixture evidence were not repurposed.

Actual feeds/routes, real keeper/rebalance and target-gas qualification remain
open. Provider batching hit a documented429; serialized archive success is not
production SLA/provider approval. Do not copy old Pons/WETH fixtures as current
evidence or add overlapping attempts to the11-method count. Three layers remain: local adversarial tests,
selected Robinhood mainnet fork and Robinhood Testnet wallet/operator rehearsals.
See [release preflight](PRODUCTION_PREFLIGHT.md) and [sole Todo](../TODO.md).

Fresh source profile: accounting4/custody3/governance2/fee1/canonicalV5 with
maintenance2/compound3/LP1/quality1/confirmation1. Inventory uses schema6;
historical schema5/accounting3 is inspection-only. Preserve actual historical
Anvil profiles and immutable runtimes. The following local scaffolds remain
historical accounting3/governance2/fee1/localV4, ETH/fixedZZZ inputs,
$100activation/$5growth,2/1/3%defaults with10%ceilings, gas separate. Parked status
is4, not a historical code6. Local scaffold is unsealed/local-only; it does not
approve real addresses. The historical local-stack launcher rejects incompatible
current pricing/native artifacts before creating state/processes. Preserve
existing Anvil/journals; use their actual historical configuration.

Use [operations](OPERATIONS.md), [operator manual](OPERATOR_MANUAL.md),
[current context](../PROJECT_CONTEXT.md) and [feature evidence](IMPLEMENTATION_STATUS.md).
Keep keys outside Git. No command here authorizes public deployment or transactions.
No integrated bridge/creator-inbox services are required for this release.
