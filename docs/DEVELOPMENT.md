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

The first command executes the off-chain implementation and mathematical model suites and writes results under `reports/`. The original suite contained 66 implementation tests and 18 models; paid-mint/activation event decoding adds two implementation tests. The models do not execute Solidity. The second command performs narrow textual consistency checks rather than compilation or security analysis.

The original delivery records 84 passing Python tests. Publication verification on Windows ran all 84 and found 81 passing, one failing permission assertion, and two missing-`fcntl` errors. See [publication checks](../reports/PUBLICATION_CHECKS.json). Historical delivery reports are retained rather than rewritten as current passing evidence.

## Solidity verification

```bash
bash scripts/install-deps.sh
bash scripts/verify.sh
# Use a separate Python 3.12 environment for the security analyzer:
python3.12 -m venv .venv-slither
source .venv-slither/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r requirements-slither.lock
bash scripts/verify-slither.sh
# Explicit archive RPC access; no public-chain transactions are submitted:
ROBINHOOD_ARCHIVE_RPC_URL=https://robinhood.rpc.pinax.network \
  python3 scripts/run-fork-checks.py
# Longer stateful accounting run, when preparing review evidence:
FOUNDRY_PROFILE=audit forge test --match-contract ProductionAccountingInvariantTest -vv
forge test --match-contract ProductionGasTest -vv
```

Dependency installation suppresses npm lifecycle scripts and requires the committed lockfile. It pins OpenZeppelin 5.4.0, v4-core 1.0.2, v4-periphery 1.0.3, and forge-std v1.9.7 at `77041d2ce690e692d6e03cc812b57d1ddaa4d505`, rejecting a modified forge-std checkout. The original periphery 1.0.4 request was not published on npm and caused the first GitHub Actions installation failure. `package-lock.json` records npm tarball URLs and integrity hashes; installation uses `npm ci`. CI actions use immutable reviewed release revisions. Slither and all 48 resolved packages are pinned with artifact hashes in `requirements-slither.lock` (Python 3.12; one Windows-only package).

The verifier runs Python/source checks, then builds with size reporting and executes offline Foundry tests. The opt-in network suite reports one setup skip offline; an explicitly requested fork run fails if the RPC, block hash or dependency hashes do not match. CI has separate offline, static-analysis and real fork jobs. Public archive endpoints can rate limit or prune old blocks; an optional `ROBINHOOD_RPC_URL` Actions secret can provide a reviewed archive service. An RPC failure must be resolved, not converted into a passing mock test. See the latest [Ubuntu verification runs](https://github.com/ABEF/AAA/actions/workflows/verify.yml) for the exact commit.

The fork runner uses a temporary loopback read-only relay to serialize archive requests at least 1.25 seconds apart. HTTP 429 alone has three bounded attempts; other failures remain failures. It forwards the actual pinned-block data without caching, fabricated responses or a latest-block fallback, denies write/sign/admin RPC methods and runs Forge with storage caching disabled. The upstream is explicit; credentials stay outside source/logs. For a reviewed higher-capacity endpoint, the direct opt-in command remains available, but anonymous endpoints may reject Foundry bursts.

Solidity 0.8.26's default Yul optimizer triggered an internal bytecode-assembly error for this vault. The profile keeps `via_ir = true` and the EVM optimizer, with `optimizer_details = { yul = false }` as the tested workaround. `optimizer_runs = 1` favors deployment size. The shared-pool rewrite changes custody, rewards and migration ABIs and requires fresh size/security evidence. `group(bucketId)` is the maintenance/custody view; `nftStatus`, `nftBucket`, `sharesOf` and `contributionUSD` expose NFT rights; the old `position(nftId)` ABI is removed. Economic bridge messages are version 3. Do not reuse per-NFT keeper state or old manifests. Current measured sizes and test counts are in [shared-pool evidence](../reports/pooled/README.md); older 23,662-byte figures describe the preceding per-NFT Vault only. No standard deployment size limit is raised.

Foundry 1.4.4 also reserves the removed `testFail*` naming pattern. Revert tests use explicit `expectRevert` assertions with names that avoid this prefix. The earlier suite of 70 tests passed under the original repaired profile; paid dormant issuance, separate activation, repeated migrations and historical reward routing now have additional EVM tests. See [current implementation evidence](../reports/IMPLEMENTATION_UPDATE.md) separately from [CI repair evidence](../reports/CI_REPAIR.md).

## Local-only deployment and services

[DeployCore.s.sol](../script/DeployCore.s.sol) is a local-only template. It creates the fixed router with no provider policies. It does not seal module bindings or open deposits. No bridge endpoint environment variable is required; add reviewed provider policies and policy-bound routes separately when needed. [.env.example](../.env.example) contains placeholders, not deployment credentials.

`MINT_PROCEEDS_RECIPIENT` is a required constructor parameter. Select and verify a recipient that accepts native ETH; a rejected payment reverts the entire mint. It cannot be changed after deployment. Minting requires sealing and costs exactly `0.05 ether`; `activate` preserves the paid NFT and requires at least $500 of measured deployed LP. The template retains its local-chain guard; this work does not deploy public-chain contracts.

Retain dry-run mode while preparing service configuration:

```bash
python3 -m keeper.monitor --config keeper/config.example.json --once
python3 -m indexer.monitor --config indexer/config.example.json --once
```

Example addresses are placeholders. Live signing uses an encrypted external Foundry `cast` keystore, a private password file, reviewed-deployment consent, bytecode hashes, and spending limits. See [operations](OPERATIONS.md).

## Review and provenance

The initial documentation/publication pass preserved all implementation and test sources. The later CI repair changed dependency/build configuration and one test function name, without changing contract logic or test assertions. Subsequent paid-mint and future-migration work changes implementation, interfaces, event schemas and tests; it is separate evidence and requires fresh security review. [Original README](../reports/history/README.v0.2.md) and [original manifest](../reports/history/MANIFEST.v0.2.sha256) preserve the initial presentation and hashes. The root manifest describes the current Git snapshot.

Start implementation work from the [component status](COMPONENT_STATUS.md), [current internal review](../reports/PRODUCTION_READINESS.md), historical [source-level audit](AUDIT.md), and [release checklist](RELEASE_CHECKLIST.md). The internal review never closes the independent audit gate.
