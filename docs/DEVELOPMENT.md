## Current static review refreshed - 2026-10-26

The [full audit](../reports/full-audit-20261025/VERIFICATION.md) performs fresh
Slither0.11.6 analysis and manually reviews all399flags against47current source/
build bindings. The actual current coverage checker passes. The older stale-
review statement below is historical, not the latest gate. This is internal
triage only: actual dependencies/operations, frozen full suite and independent
audit remain unqualified. Preserve the recorded successful solc output versus
later host-signature-cache Forge CLI failure; no green CI claim is implied.
Reference snapshot3 and unchanged31contracts/608functions remain current.

## Evidence snapshot 3 and day audit - 2026-10-25

The current reference uses snapshot3 with closed compiler names, normal limits,
compiler/status/freeze/hash coherence and independently derived constructor
sizes. Schema2 must be regenerated from the original matching normal compiler
input/output and size report; do not relabel old snapshots. Use the existing
generator flags below, then --check. Actual dynamic constructor arguments still
need release-specific qualification. See [audit](../reports/day-readiness-20261025/evidence-review.md).
The current saved Slither triage is stale and fails the release gate; obtain
and review a fresh frozen-source analysis. No old hash-only refresh qualifies it.

## Closed dependency evidence - 2026-10-25

Current callable-reference snapshot2 binds project and imported Solidity plus
the exact existing foundry.toml/package.json/package-lock.json/install-deps.sh.
Install locked dependencies before --check. Regeneration requires complete
explicit compiler contents, output/source inventory and normal size evidence;
implicit imports, missing build pins, malformed/truthy gate flags and escaping
source roots fail closed. Never hand-edit hashes to suppress a mismatch.
This is evidence-format versioning, not a deployed accounting upgrade.

The [current cleanup verification](../reports/deep-cleanup-20261025/VERIFICATION.md)
records 32 targeted Solidity / 41 Python methods, 37 normal gates and 75 production /
265 all-source explicit inputs. It does not claim a new full verify.sh run,
current Slither triage, real provider/operating acceptance or independent audit.
Run the complete frozen-release pipeline before approval. Keep old dated notes
below in their original source scope; current contribution default is 2%,
conversion 1%, maintenance 3%, each governed up to 10%, gas separate.

## Current fork qualification boundary - 2026-10-25

The wrapped-accounting NativePoolFork fixture is retired. Current fork
qualification is blocked explicitly before RPC/Forge until a reviewed native
replacement is available; historical source/status fixtures in unit tests do not
qualify a real venue. Current release accepts ETH/fixed ZZZ inputs only, has no
creator inbox/integrated bridge, and uses explicit LP-only profiles. Existing
local deployments and journals keep their old source version. Read the
[simplification evidence](../reports/simplification-20261025/VERIFICATION.md).

## Focused verification selection - 2026-10-25

The Linux keeper workflow now explicitly includes
`tests_python.test_keeper_maintenance_policy` and
`tests_python.test_keeper_range_policy`. A workflow edit is not a completed CI
run. Preserve normal runtime/initcode and gas gates; run only changed-surface
checks during development, then qualify a frozen release comprehensively.
[Current evidence and limits](../reports/comprehensive-improvement-20261025/VERIFICATION.md)
retain failed attempts, fixture repairs and exact reused-source boundaries;
do not overwrite historical evidence with an unsupported full-regression claim.

In Foundry fixtures, cache external helper/receiver getters before arming
one-shot `vm.prank` or `vm.expectRevert`: the next external getter can consume the
cheatcode instead of the intended action. Keep test preparation distinct from
the action/assertion, and retain original failed diagnostics when repairing a
harness. Do not change production guards to satisfy a stale mock.

## Current-source local rehearsal compatibility - 2026-10-24

The historical local-stack bootstrap is not a qualified pricing-V2 deployment
tool. It now rejects incompatible current artifacts before creating state or
starting Anvil. Existing8902 and its saved state remain untouched. Use scoped
offline tests and [current inventory instructions](PRODUCTION_PREFLIGHT.md);
a separate fresh native/routing/pricing2 operating rehearsal remains open.
[Price-security evidence](../reports/price-security/VERIFICATION.md).

## Native V2 inventory and preflight - 2026-10-24

[Current schema-5 preflight](PRODUCTION_PREFLIGHT.md) validates native/V4 bindings,
actual versus approved runtime pins and current governed limits. A separate
bounded read-only observer captures a canonical snapshot without upgrading review
status. Legacy schema 4 stays historical; missing actual public addresses,
prices/routes/VRF/services and audit evidence remain release blockers. No signer,
Solidity, website/service, existing Anvil/journal or monitor change follows.

## Native V2 verification boundary - 2026-10-24

Actual ETH funding/accounting is implemented in the undeployed [native V2 candidate](../reports/native-eth-port/VERIFICATION.md). Use explicit version2 API/keeper profiles and fresh runtime pins; preserve old WETH deployments and journals. Exact payable values, separate backing and current-owner claims remain mandatory. Atomic ETH/WETH conversion, V1 schema import, actual native services/market qualification and independent approval remain open. The website source/build/server, Anvil state and shared Anvil-only signer are unchanged. Earlier dated entries retain their original source scope.

# Development setup and verification

> Updated 2026-10-16: undeployed candidate; $100 original gross source value with at least 99% marginal deployed LP, gas separate; atomic source entry and paused custody parking. Accepted 80/10/5/5, equal membership, 1,000-NFT quotas, VRF and separate royalties remain unchanged. See the [feature and evidence reference](IMPLEMENTATION_STATUS.md). Earlier receipts retain their source scope; actual routes/services, staging and independent audit remain open.

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

The verifier runs Python/source checks, then builds with size reporting and executes offline Foundry tests. Opt-in fork suites skip their setup offline; report the actual skip count rather than reusing the earlier single-suite count. Explicit fork runs fail on RPC/block/dependency mismatches. Run both `UniswapV4ForkTest` and the new actual selected-market `NativePoolForkTest`; the earlier hookless suite alone does not qualify native custody. CI has separate offline, static-analysis and fork jobs; check that the exact revision runs the intended suites. Public archive rate limits/pruning remain real failures, not permission to substitute mocks. See the [Ubuntu runs](https://github.com/ABEF/AAA/actions/workflows/verify.yml).

The fork runner uses a temporary loopback read-only relay to serialize archive requests at least 1.25 seconds apart. HTTP 429 alone has three bounded attempts; other failures remain failures. It forwards the actual pinned-block data without caching, fabricated responses or a latest-block fallback, denies write/sign/admin RPC methods and runs Forge with storage caching disabled. The upstream is explicit; credentials stay outside source/logs. For a reviewed higher-capacity endpoint, the direct opt-in command remains available, but anonymous endpoints may reject Foundry bursts.

Solidity 0.8.26's default Yul optimizer triggered an internal bytecode-assembly error for this vault. The profile keeps `via_ir = true`, the EVM optimizer and `optimizer_details = { yul = false }`; `optimizer_runs = 1` favors size. `group(bucketId)` is the physical custody view; `nftStatus`, `nftBucket`, `sharesOf` and `contributionUSD` expose NFT rights. Bridge messages are version 3; do not reuse per-NFT keeper state or old manifests. The earlier [release verification](../reports/release-hardening/README.md) recorded Vault runtime 24,407 and NFT runtime/initcode 18,822/42,307 bytes. Those sizes predate native support, the 1% policy and the constructor-created claim router. Recheck every current module/helper plus complete constructor arguments against unchanged runtime/initcode limits; historical margins are not current deployability evidence. Refresh source-bound static analysis for the changed sources.

Foundry 1.4.4 also reserves the removed `testFail*` naming pattern. Revert tests use explicit `expectRevert` assertions with names that avoid this prefix. The earlier suite of 70 tests passed under the original repaired profile; paid dormant issuance, separate activation, repeated migrations and historical reward routing now have additional EVM tests. See the historical [implementation evidence](../reports/IMPLEMENTATION_UPDATE.md) separately from [CI repair evidence](../reports/CI_REPAIR.md); neither verifies the current alignment revision.

## Current alignment coverage

The earlier metadata-notification candidate passed 342 offline Solidity tests, one fork setup skip and 20 size gates. Its [source-bound summary](../reports/release-hardening/verification-summary.json) and [CI for `5febe70`](https://github.com/ABEF/AAA/actions/runs/38793910449) remain historical. They do not verify the new native/claim/entry changes. Reproduce complete current-source tests, sizes, static analysis, actual selected-pool forks and extended stress; record exact hashes. Targeted commands include:

```bash
forge test --match-contract NFTMetadataTest -vv
forge test --match-contract NFTRoyaltiesTest -vv
forge test --match-contract PooledSecurityTest -vv
forge test --match-contract ClaimRouterTest -vv
forge test --match-contract NativeAssetFoundationTest -vv
python3 -m unittest tests_python.test_frontend_api tests_python.test_frontend_history -v
```

The NFT tests use an explicitly non-proof-verifying `MockVRF`: they cover request binding/authentication, strict mint-order finalization, exact quota exhaustion, cap rejection, immutable traits, separate royalties, current-value evolution/downgrades and unavailable valuation. Complete 1,000-mint inventory tests cover 58 palettes, four patterns, fixed style/rarity quotas, at most four identical finishes and unique Legendary looks. Generated catalogue checks bind the 2,784 supported artwork paths to the immutable inventory. These tests do not establish live VRF, subscription backing or Robinhood support. Test-only venue/feed fixtures are not actual selected-market evidence. Preserve equal-member timing, all-bucket funded-dust barriers and token-callback regression coverage when changing entry accounting.

## Local-only deployment and services

[DeployCore.s.sol](../script/DeployCore.s.sol) is a local-only template. It does not seal module bindings, open deposits or configure a production venue. No integrated bridge is part of this release. Existing V1 local fixtures must retain their original artifacts and journals; they do not become native V2 by recompiling current source. [.env.example](../.env.example) contains placeholders, not deployment credentials.

The canonical NFT requires a reviewed VRF-v2.5-compatible coordinator before `seal()`; actual selected-chain provider support is still unverified. Mint requests two words once; activation waits for authenticated mint-order finalization, without fallback/reroll. Record immutable royalty, metadata and new `claimRouter()` helper bindings/runtime hashes. `scripts/prepare_ipfs_bundle.py` now prepares and independently verifies a reproducible artwork upload archive; the bundle is prepared but not uploaded/pinned, and no production CID is approved.

`MINT_PROCEEDS_RECIPIENT` is immutable and must accept native ETH. The current direct-mint contract costs exactly `0.05 ether`; compatible OpenSea primary mint remains unfinished. Native V2 contributions accept only ETH/fixed ZZZ: $100 activation and $5 growth minima, with a captured 2% default marginal deployed-LP limit (governed maximum10%, tighter caller/venue minima retained). Gas is separate. Entry binds the original source to actual ETH/ZZZ accounting; stablecoin or WETH inputs are not user options. See [current source policy](SIMPLIFIED_RELEASE.md), [Entry](ACTIVATION_ENTRY.md) and [execution guards](EXECUTION_LOSS_POLICY.md). No public transaction is authorized by these commands.

[Paused parking](CUSTODY_PARKING.md) adds `PositionStatus.Parked = 6` without renumbering old statuses. Tests must preserve exact raw close minimums, governance/pause/nonce checks, source-oracle/inbox independence, ordinary resume price checks and funded claims/legacy migration barriers. Keeper and API validate local custody/zero physical LP while Parked; they must not treat it as an Active position or invent current LP value.

Retain dry-run mode while preparing service configuration:

```bash
python3 -m keeper.monitor --config keeper/config.example.json --once
python3 -m indexer.monitor --config indexer/config.example.json --once
```

Example addresses are placeholders. Live signing uses an encrypted external Foundry `cast` keystore, a private password file, reviewed-deployment consent, bytecode hashes, and spending limits. See [operations](OPERATIONS.md).

The unhosted [frontend API](FRONTEND_API.md) serves confirmed holdings, current LP and funded claims. Optional complete [history](FRONTEND_HISTORY.md) and [earnings](EARNINGS_HISTORY.md) supply lifetime/24h LP-plus-royalty earnings and reviewed current-price values. Missing history/prices stay unavailable. The former creator-payment measurement CLI and tests are [retired](REVENUE_SHARE.md), not executable current tooling. Public website transactions remain simulated; the isolated existing local-wallet profile remains Anvil-only.

Complete the three required release layers: local mint/activation/reward/royalty/transfer/security tests; a Robinhood mainnet fork using the actual selected pool/hook/dependencies; and Robinhood Testnet wallet/website/keeper/deployment rehearsals. Sepolia is supplementary. These local commands do not deploy to a public testnet or close those gates.

## Review and provenance

The initial documentation/publication pass preserved all implementation and test sources. The later CI repair changed dependency/build configuration and one test function name, without changing contract logic or test assertions. Subsequent paid-mint and future-migration work changes implementation, interfaces, event schemas and tests; it is separate evidence and requires fresh security review. [Original README](../reports/history/README.v0.2.md) and [original manifest](../reports/history/MANIFEST.v0.2.sha256) preserve the initial presentation and hashes. The root manifest describes its committed Git snapshot; regenerate it for a completed release rather than presenting an earlier manifest as a hash inventory for uncommitted edits.

Start implementation work from the [central Todo](../TODO.md), [feature and evidence reference](IMPLEMENTATION_STATUS.md), [component status](COMPONENT_STATUS.md), [current local verification](../reports/release-hardening/README.md), [earlier internal review](../reports/PRODUCTION_READINESS.md), historical [source-level audit](AUDIT.md), and [release approval record](RELEASE_CHECKLIST.md). Internal review never closes the independent audit gate.
