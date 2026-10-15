# Development setup and verification

> Current undeployed candidate uses $100 net deployed-LP activation, 80/10/5/5 LP fees, equal activated membership, exact 600/300/100 rarities across at most 1,000 NFTs, VRF reveal and separate 5% royalties. Bounded metadata notifications and an optional keeper watcher are now implemented. See the [implemented and todo checklist](IMPLEMENTATION_STATUS.md), [current verification](../reports/release-hardening/README.md) and [static review](../reports/release-hardening/static-analysis/README.md). Historical reports retain their source scope; live integration and independent audit remain open.

## Supported environment

Use Linux/Unix with Python 3.11+ for the full off-chain test suite and keeper. `zzz_ops.state.process_lock` uses `fcntl`, and state-file tests require Unix `0600` permissions. Native Windows does not satisfy those assumptions. A Windows checkout can be edited and published; keeper operation and complete verification require a supported Linux environment such as WSL with a Linux distribution.

Solidity tooling requires reviewed Foundry, Node/npm, Git, Solidity 0.8.26, and the configured Cancun EVM target. Direct package versions are specified in [package.json](../package.json); Foundry settings and remappings are in [foundry.toml](../foundry.toml).

## Off-chain tests

From the repository root:

```bash
python3 scripts/run_python_tests.py
python3 scripts/source_checks.py
```

The first command executes off-chain implementation and mathematical model suites and writes results under `reports/`. Models do not execute Solidity. The second performs narrow textual consistency checks rather than compilation or security analysis. Discover and report the current test inventory from the actual run; do not reuse a preceding revision's count as current evidence.

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

Solidity 0.8.26's default Yul optimizer triggered an internal bytecode-assembly error for this vault. The profile keeps `via_ir = true` and the EVM optimizer, with `optimizer_details = { yul = false }` as the tested workaround. `optimizer_runs = 1` favors deployment size. `group(bucketId)` is the maintenance/custody view; `nftStatus`, `nftBucket`, `sharesOf` and `contributionUSD` expose NFT rights; the old `position(nftId)` ABI is removed. Economic bridge messages are version 3. Do not reuse per-NFT keeper state or old manifests. Earlier shared-pool, reward-funding and artwork reports retain their source scope. Current [release verification](../reports/release-hardening/README.md) supplies the complete offline run and all 20 module/helper size measurements; its [static review](../reports/release-hardening/static-analysis/README.md) is source-bound. Vault runtime is 24,407 bytes, leaving 169 bytes below EIP-170; NFT runtime/initcode objects are 18,822/42,307 bytes. Constructor arguments still need deployment-time initcode allowance. No standard deployment size limit is raised.

Foundry 1.4.4 also reserves the removed `testFail*` naming pattern. Revert tests use explicit `expectRevert` assertions with names that avoid this prefix. The earlier suite of 70 tests passed under the original repaired profile; paid dormant issuance, separate activation, repeated migrations and historical reward routing now have additional EVM tests. See the historical [implementation evidence](../reports/IMPLEMENTATION_UPDATE.md) separately from [CI repair evidence](../reports/CI_REPAIR.md); neither verifies the current alignment revision.

## Current alignment coverage

The metadata-notification candidate passed 342 offline Solidity tests with one expected fork setup skip and all 20 normal module/helper size gates. See the [source-bound summary](../reports/release-hardening/verification-summary.json) for actual Python/static-analysis results and limitations. Earlier [Ubuntu CI for `5febe70`](https://github.com/ABEF/AAA/actions/runs/38793910449) passed all three jobs; check the new published revision separately. This local offline pass does not rerun actual dependency forks or the extended accounting stress profile. Targeted development commands include:

```bash
forge test --match-contract NFTMetadataTest -vv
forge test --match-contract NFTRoyaltiesTest -vv
forge test --match-contract PooledSecurityTest -vv
forge test --match-contract ExternalRewardsTest -vv
```

The NFT tests use an explicitly non-proof-verifying `MockVRF`: they cover request binding/authentication, strict mint-order finalization, exact quota exhaustion, cap rejection, immutable traits, separate royalties, current-value evolution/downgrades and unavailable valuation. Complete 1,000-mint inventory tests cover 58 palettes, four patterns, fixed style/rarity quotas, at most four identical finishes and unique Legendary looks. Generated catalogue checks bind the 2,784 supported artwork paths to the immutable inventory. These tests do not establish live VRF, subscription backing or Robinhood support. Test-only venue/feed fixtures are not actual selected-market evidence. Preserve equal-member timing, all-bucket funded-dust barriers and token-callback regression coverage when changing entry accounting.

## Local-only deployment and services

[DeployCore.s.sol](../script/DeployCore.s.sol) is a local-only template. It creates the fixed router with no provider policies. It does not seal module bindings or open deposits. No bridge endpoint environment variable is required; add reviewed provider policies and policy-bound routes separately when needed. [.env.example](../.env.example) contains placeholders, not deployment credentials.

The canonical NFT must be configured with a reviewed VRF-v2.5-compatible coordinator before `seal()`; canonical sealing rejects missing randomness configuration. Mint requests two words once and activation waits for authenticated, mint-order `finalizeTraits(id)`. A missing earlier fulfillment blocks later reveals without a fallback. The immutable artwork root must be reviewed content-addressed assets, and the separate royalty/metadata helper bindings must be included in deployment observations. Actual coordinator/network review remains open.

`MINT_PROCEEDS_RECIPIENT` is a required constructor parameter. Select and verify a recipient that accepts native ETH; a rejected payment reverts the entire mint. It cannot be changed after deployment. Minting requires sealing and costs exactly `0.05 ether`; `activate` preserves the paid NFT and requires at least $100 of net measured deployed LP after execution, not merely $100 gross input. Current activation accepts configured pool tokens; arbitrary USDC/ZZZ-to-pair routing is absent. The template retains its local-chain guard; this work does not deploy public-chain contracts.

Retain dry-run mode while preparing service configuration:

```bash
python3 -m keeper.monitor --config keeper/config.example.json --once
python3 -m indexer.monitor --config indexer/config.example.json --once
```

Example addresses are placeholders. Live signing uses an encrypted external Foundry `cast` keystore, a private password file, reviewed-deployment consent, bytecode hashes, and spending limits. See [operations](OPERATIONS.md).

## Review and provenance

The initial documentation/publication pass preserved all implementation and test sources. The later CI repair changed dependency/build configuration and one test function name, without changing contract logic or test assertions. Subsequent paid-mint and future-migration work changes implementation, interfaces, event schemas and tests; it is separate evidence and requires fresh security review. [Original README](../reports/history/README.v0.2.md) and [original manifest](../reports/history/MANIFEST.v0.2.sha256) preserve the initial presentation and hashes. The root manifest describes its committed Git snapshot; regenerate it for a completed release rather than presenting an earlier manifest as a hash inventory for uncommitted edits.

Start implementation work from the [implemented and todo checklist](IMPLEMENTATION_STATUS.md), [component status](COMPONENT_STATUS.md), [current local verification](../reports/release-hardening/README.md), [earlier internal review](../reports/PRODUCTION_READINESS.md), historical [source-level audit](AUDIT.md), and [release checklist](RELEASE_CHECKLIST.md). Internal review never closes the independent audit gate.
