# Development setup and verification

Use Linux/Unix with Python3.11+ for full keeper/state-lock operation and tests:
`fcntl` and Unix0600 semantics are required. Windows editing/publication and
portable checks do not establish Unix operating acceptance. Solidity is pinned
to 0.8.26/Cancun with the committed via-IR/optimizer profile. Use the actual
[Foundry settings](../foundry.toml), [packages](../package.json), lockfile and
[dependency installer](../scripts/install-deps.sh), not an old report's sizes.

## Setup and change verification

Before publication, check the exact staged Python source closure with
`python3 scripts/check-python-publication.py --index`. After committing, use the
same command without `--index` to check HEAD. It parses Git blobs rather than
importing local packages, so untracked reader files cannot hide a missing
published dependency. The full verifier checks HEAD first. This is a static
repository-import check; dynamic imports, dependencies and runtime behavior still
need their own checks. An unstaged working file does not repair a failing commit.

From the repository root in the supported environment:

```bash
bash scripts/install-deps.sh
# Full verification when the change/release requires it:
bash scripts/verify.sh
# Documentation/reference consistency without repeating contract suites:
python3 scripts/generate-function-reference.py --check
python3 scripts/sync-project-todo.py --check
```

The full verifier first inspects the actual local Forge/default compiler profile,
normal size/optimizer settings, remappings, filesystem permissions and unfiltered
test/fuzz/invariant selection. It then runs Python/source checks, normal build/
size gates and offline Solidity tests. Source/tool settings are rechecked at
phase boundaries; this does not authenticate a compromised tool or host.

Each invocation creates an exclusive `reports/verification.XXXXXXXX` directory
and prints its path on completion. Optional `POPL_VERIFICATION_OUTPUT_DIR` must name a new
directory with an existing parent. Old reports are preserved; retry into a fresh
directory rather than overwriting a failed campaign. Raw Forge configuration may
contain credentials: the checker exports only reviewed fields and safe diagnostic
messages. Do not publish a raw `forge config --json` dump.

The full Python runner now uses canonical `tests_python.*` identities and locally
defined cases once; imported aliases do not rerun, while locally defined subclasses
retain inherited tests. Empty/duplicate/wrong-identity/custom-loader selections
fail closed. A custom loader requires an explicit reviewed selector, not silent
exclusion. Both source drift and executed-ID mismatches invalidate a result.
No-argument Python execution also creates unique evidence files. To inspect only:

```bash
python3 scripts/run_python_tests.py --list --output NEW_INVENTORY.json
python3 scripts/run_python_tests.py --output NEW_RESULTS.json
python3 scripts/verify-normal-profile.py
```

`--list` imports selected modules but executes no test bodies; its success and
counts are inventory metadata, not test passes. Existing JSON/log output paths
are refused. The default full verifier is intentionally the normal profile;
run separately scoped stronger audit/fuzz campaigns with explicit evidence.
[Verification-tooling scope](../reports/operational-reliability-20261029/VERIFICATION.md) and
[recent affected keeper/preflight evidence](../reports/keeper-coordination-20261029/VERIFICATION.md)
retain separate source and execution scopes; neither is a fresh full-suite run.

Python/keeper/source-check producers reserve fresh JSON (and execution logs)
exclusively before importing tests or scanning sources. An in-progress/failed
marker is nonpass evidence, not proof that no side effect occurred. Partial
diagnostics remain; a storage/fsync failure can leave partial unreadable evidence.
Do not replay real actions to recreate a report. Source checks now default to a
unique `reports/source-checks-<time>-<nonce>.json`; explicit existing outputs are
refused. Full Python `--list` retains no execution log; inventory is not testing.
Source hashes bracket selection/imports as well as execution; they are not
runtime attestation against a compromised host or preloaded altered module.

During development run the useful affected suites; preserve
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

Each static run reserves a new `reports/slither.XXXXXXXX/` directory before
invoking the analyzer. Optional `POPL_SLITHER_OUTPUT_DIR` must name a new
directory; an existing path is refused. Version/report/diagnostic/review files
remain there on failure, and the path prints on exit. Analyzer exit255 means
findings, not approval; analyzer/log-capture/checker failures still fail. The
checker strictly loads JSON objects and preserves source/finding coverage gates.
CI uploads only these new static directories. Older canonical analysis/review
files are not deleted or refreshed automatically.

The [historical full audit](../reports/full-audit-20261025/VERIFICATION.md) records
actual399-findings/47bindings internal static review coverage PASS, successful
solc output and a later Forge host-cache CLI failure. Those are separate facts,
not a current green workflow or independent approval. The [historical applicability
comparison](../reports/historical-reconciliation-completion-20261029/STATIC_APPLICABILITY.json)
records19of47then-changed source pins. The [source6 refresh](../reports/today-audit-20261031/VERIFICATION.md)
now records471 flags with exact-context reuse/current review and a new default
[review record](../reports/today-audit-20261031/static-review.json). Old records
remain untouched; the checker still requires exact source/finding coverage.
Refresh after relevant changes and check exact-revision CI.
Keep normal runtime/initcode/gas gates and exact constructor arguments.

## Focused keeper verification

```bash
python3 scripts/run-keeper-tests.py --list --output path/to/new-selection.json
python3 scripts/run-keeper-tests.py --output path/to/new-keeper-results.json
```

`--list` validates and writes the selected modules/classes/methods without running
test bodies; `execution_performed:false` and `tests_run:0` are not test passes.
The dedicated CI list now includes the newer confirmation/checkpoint, cadence,
principal-delivery, telemetry/watchdog/revert and conversion-header regressions.
Imported fixture classes are not executed twice; duplicate/empty/wrong-identity
selection fails. Full `verify.sh` separately discovers the wider Python suite.
Use the [whole-project verification](../reports/whole-project-audit-20261029/VERIFICATION.md)
for narrow selection checks; it does not claim all selected methods ran again.
Unix-only assertions remain explicit on other hosts; Windows success does not
qualify Linux operation.

## Fork and operating qualification

The separate [current native-pool harness](../test/CurrentNativePoolFork.t.sol)
and [bounded read-only runner](../scripts/run-current-pool-fork.py) replace the
archived wrapped fixture for this campaign. [Verification](../reports/current-pool-fork-20261026/VERIFICATION.md)
records 11distinct successful methods across source-bound affected runs, not a
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
future whole run must contain all 11expected methods with no skips; the legacy
dirty runner and old fixture evidence were not repurposed.

The committed fork CI job now invokes this current runner, with a checksum-pinned
official Linux solc0.8.26 download verified before execution. It retains the same
reviewed normal profile and read-only relay; the historical dirty runner is not
used or overwritten by that job. This wiring was checked statically, not run on
GitHub or against live RPC during the audit. Require actual exact-revision CI
artifacts before saying it passed. [Compiler/dependency scope](../reports/whole-project-audit-20261029/COMPILER_DEPENDENCIES.md).

Actual feeds/routes, real keeper/rebalance and target-gas qualification remain
open. Provider batching hit a documented429; serialized archive success is not
production SLA/provider approval. Do not copy old Pons/WETH fixtures as current
evidence or add overlapping attempts to the 11-method count. Three layers remain: local adversarial tests,
selected Robinhood mainnet fork and Robinhood Testnet wallet/operator rehearsals.
The concrete production Registry deliberately pins chain4663 and mainnet native
runtimes. A byte-identical full venue flow cannot simply be redeployed on a
different testnet. A testnet rehearsal needs an explicit reviewed test-only
binding/profile with mocks/limits declared; it qualifies only that scope. Keep
actual mainnet-venue qualification in the selected fork/approved rehearsal, never
weaken production pins or label test dependencies real.
See [release preflight](PRODUCTION_PREFLIGHT.md) and [sole Todo](../TODO.md).

Fresh source profile: accounting6/custody4/governance2/fee1/canonicalV6 with
portfolio2/maintenance3/compound4/LP2/quality1/confirmation3 and separate manual
emergency2. Inventory uses schema8/21 helpers; schema6/accounting4 and
schema5/accounting3 remain explicitly historical. Local actual-v4-core portfolio
checks are source-scoped with mock external dependencies, not live qualification. Preserve actual historical
Anvil profiles and immutable runtimes. The following local scaffolds remain
historical accounting3/governance2/fee1/localV4, ETH/fixedZZZ inputs,
$100activation/$5growth,2/1/3% defaults with 10% ceilings, gas separate. Parked status
is 4, not a historical code6. Local scaffold is unsealed/local-only; it does not
approve real addresses. The historical local-stack launcher rejects incompatible
current pricing/native artifacts before creating state/processes. Preserve
existing Anvil/journals; use their actual historical configuration.

Use [operations](OPERATIONS.md), [operator manual](OPERATOR_MANUAL.md),
[current context](../PROJECT_CONTEXT.md) and [feature evidence](IMPLEMENTATION_STATUS.md).
Keep keys outside Git. No command here authorizes public deployment or transactions.
No integrated bridge/creator-inbox services are required for this release.
