# Development setup and verification

## Supported environment

Use Linux/Unix with Python 3.11+ for the full off-chain test suite and keeper. `zzz_ops.state.process_lock` uses `fcntl`, and state-file tests require Unix `0600` permissions. Native Windows does not satisfy those assumptions. A Windows checkout can be edited and published; keeper operation and complete verification require a supported Linux environment such as WSL with a Linux distribution.

Solidity tooling requires reviewed Foundry, Node/npm, Git, Solidity 0.8.26, and the configured Cancun EVM target. Direct package versions are specified in [package.json](../package.json); Foundry settings and remappings are in [foundry.toml](../foundry.toml).

## Off-chain tests

From the repository root:

```bash
python3 scripts/run_python_tests.py
python3 scripts/source_checks.py
```

The first command executes 66 off-chain implementation tests and 18 mathematical model tests and writes results under `reports/`. The models do not execute Solidity. The second command performs narrow textual consistency checks rather than compilation or security analysis.

The original delivery records 84 passing Python tests. Publication verification on Windows ran all 84 and found 81 passing, one failing permission assertion, and two missing-`fcntl` errors. See [publication checks](../reports/PUBLICATION_CHECKS.json). Historical delivery reports are retained rather than rewritten as current passing evidence.

## Solidity verification

```bash
bash scripts/install-deps.sh
bash scripts/verify.sh
# After installing a reviewed, pinned Slither release:
slither . --config-file slither.config.json
```

Dependency installation suppresses npm lifecycle scripts. It pins OpenZeppelin 5.4.0, v4-core 1.0.2, v4-periphery 1.0.3, and forge-std v1.9.7. The original periphery 1.0.4 request was not published on npm and caused the first GitHub Actions installation failure. The committed `package-lock.json` records the resolved npm versions, tarball URLs, and integrity hashes; subsequent installs use `npm ci`. Upstream Git revisions and workflow actions still need immutable release pins and review before production use.

The verifier runs Python/source checks, then builds with size reporting and executes Foundry tests. Tests use mocks; actual Uniswap fork tests and provider-specific bridge tests remain separate release requirements. See the latest [Ubuntu verification runs](https://github.com/ABEF/AAA/actions/workflows/verify.yml) for the status of the exact commit being reviewed.

Solidity 0.8.26's default Yul optimizer triggers an internal bytecode-assembly error for this vault. The current profile keeps `via_ir = true`, the EVM optimizer, and 200 runs, with `optimizer_details = { yul = false }` as the tested workaround. All 16 module artifacts fit the standard runtime/initcode limits; the vault runtime is 23,451 bytes, leaving 1,125 bytes below EIP-170. This profile needs gas benchmarking and independent review before a funded release.

Foundry 1.4.4 also reserves the removed `testFail*` naming pattern. The ordinary rollback test is named `testMintFailureRollsBackWholeDeposit`, retaining its explicit revert and state assertions. All 70 provided Solidity tests passed locally, including two fuzz tests with 1,000 runs each. See [CI repair evidence](../reports/CI_REPAIR.md).

## Local-only deployment and services

[DeployCore.s.sol](../script/DeployCore.s.sol) is a local-only template. It does not seal module bindings or open deposits. [.env.example](../.env.example) contains placeholders, not deployment credentials.

Retain dry-run mode while preparing service configuration:

```bash
python3 -m keeper.monitor --config keeper/config.example.json --once
python3 -m indexer.monitor --config indexer/config.example.json --once
```

Example addresses are placeholders. Live signing uses an encrypted external Foundry `cast` keystore, a private password file, reviewed-deployment consent, bytecode hashes, and spending limits. See [operations](OPERATIONS.md).

## Review and provenance

The initial documentation/publication pass preserved all implementation and test sources. The later CI repair changes dependency/build configuration and one test function name, without changing contract logic or test assertions. [Original README](../reports/history/README.v0.2.md) and [original manifest](../reports/history/MANIFEST.v0.2.sha256) preserve the initial presentation and hashes. The root manifest describes the current Git snapshot.

Start implementation work from the [component status](COMPONENT_STATUS.md), [source-level audit](AUDIT.md), and [release checklist](RELEASE_CHECKLIST.md). Every funded deployment gate remains open until evidence closes it.
