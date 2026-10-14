# ZZZ Protocol v0.2 — source-level security review

**Review date: October 14, 2026**  
**Disposition: NOT APPROVED FOR REAL-FUND DEPLOYMENT**  
**Reviewer: the same assistant that rewrote the code; this is a self-review, not an independent third-party audit.**

## 1. Executive conclusion

The original archive was a non-deployable architectural prototype. This delivery materially improves all 16 requested modules, adds typed liquidity operations and constrained migration/reward flows, replaces the incomplete NFT implementation, and supplies working off-chain code plus executable tests.

The strongest evidence obtained is **84 passing Python tests** for off-chain logic and separate mathematical specifications. **No Solidity source was compiled, no Foundry test was executed, no live Uniswap/bridge transaction was performed, no Slither analysis ran, and no independent audit occurred.** The environment lacked `forge`/`solc`; package installation failed with DNS/network errors. Narrow textual/source checks do not compensate for that gap.

Consequently, this report does not assert that any contract is exploitable or unexploitable based on runtime evidence, and it does not certify any listed source mitigation as complete. The immutable principal design makes those unresolved validation gaps particularly serious.

## 2. Scope and provenance

Input: `zzz-protocol-prototype.zip`.

```text
SHA-256 f1dad3b06517c58d8b044604e53bf60b60a1fb53d14256e68b1627bd34d8619e
```

Reviewed/rewritten custom scope: all 16 named modules under `src/`, shared interfaces/types/token helper, keeper, RPC/state/codec utilities, indexer and associated configuration. The original source was retained separately during review and is not overwritten by the delivered archive.

External scope limitations: official interfaces and selected implementation sections were consulted, but OpenZeppelin, Uniswap, a production bridge, oracle providers, chain deployments and token contracts were **not** independently audited here. No actual ZZZ token or production destination addresses were supplied/verified. Third-party dependencies were not vendored or successfully installed.

Tests authored cover real module source behind mocks, not just interfaces; those Solidity tests remain **uncompiled/unexecuted**. `test/LiquidityEncoding.t.sol` uses fake settlement and must not be confused with a real v4 fork test.

## 3. Work and validation actually performed

| Activity | Evidence / result |
|---|---|
| Initial prototype inspection | Original source/README explicitly had disabled Uniswap and bridge adapters, partial accounting and no complete tests |
| Contract source review and rewrite | All 16 requested modules and four supporting Solidity files |
| Official interface cross-check | Selected PosM actions/encoding, NFT approval/getter surfaces, Permit2 integration, ERC-721 and timelock APIs |
| Python execution | 84 tests passed; zero failures/errors/skips |
| Python implementation versus model split | 66 implementation tests and 18 independent specification/model tests |
| Foundry test source | 70 test functions across 6 files; not run |
| Source consistency check | Balanced delimiters, required modules, local imports, pinned pragmas and narrow dangerous-primitive checks; no errors found |
| CLI and shell checks | Python bytecode compilation, CLI help and shell syntax checks passed |
| Solidity/EVM/static analyzer verification | BLOCKED / NOT RUN |
| Production deployment / real funds | None |

The mathematical specifications include randomized fee-partition tests, reward-index solvency sequences, contribution/idle conservation and tick-range calculations. They implement reference models; they do **not** execute the Solidity implementation or prove matching compiled behavior.

## 4. Findings and changes implemented in source

Severity describes the risk if the issue exists in a live design. “Implemented in source” is not equivalent to “fixed and independently verified.” Findings R-12 through R-14 have applicable passing Python regression tests; Solidity findings require the listed EVM release gates.

| ID | Risk level | Finding | Mitigation implemented in this candidate | Source anchors |
|---|---|---|---|---|
| R-01 | High | Unrestricted or unproven custody adapters | Frozen module bindings, typed fixed-recipient operations, per-position NFT custody checks and temporary allowances. | `src/ZZZAccessController.sol:44`; `src/ZZZLiquidityManager.sol:51` |
| R-02 | High | Incomplete ERC-721 semantics | OpenZeppelin ERC-721 safe mint/transfer replaces the custom ERC721-like prototype. | `src/ZZZNFT.sol:9`; `test/RewardsAndFees.t.sol` |
| R-03 | High | Previously published rewards could be repriced after Power changes | Checkpoint every registered asset before either local or total weight changes; retain fractional entitlements. | `src/ZZZPower.sol:16`; `src/ZZZRewards.sol:34` |
| R-04 | High | Idle deposits and fee/principal flows were insufficiently separated | Per-position/aggregate idle ledgers, measured dedicated fee collection and separate fee reserve accounting. | `src/ZZZVault.sol:46`; `src/ZZZFeeController.sol:31` |
| R-05 | High | A same-pool balancing swap can generate new LP fees before an increase | Collect again after balancing an existing range, before increasing liquidity, so the v4 modification cannot silently compound those fees. | `src/ZZZVault.sol:181`; `src/ZZZVault.sol:124` |
| R-06 | High | A receiver-only transfer check misses additive sender taxes | Verify exact sender decrease and exact recipient increase on both pull and push paths. | `src/libraries/ExactToken.sol:11`; `test/OracleAndTransfers.t.sol` |
| R-07 | High | Satellite deployments could otherwise issue a separate collection | Immutable canonical NFT chain gate on deposits and accepted origins; imported positions do not mint another NFT. | `src/ZZZVault.sol:21`; `src/ZZZVault.sol:270` |
| R-08 | High / economic | Mostly idle contributions could receive large Power | Balance deposits/top-ups and require at least 95% oracle-valued deployment after LP placement. | `src/ZZZVault.sol:22`; `src/ZZZVault.sol:87` |
| R-09 | High | Migration identity, replay and asset backing were only placeholders | Fixed routes, domain-separated origin nonces, exact funding and retryable destination custody replace unconditional stubs. | `src/ZZZBridgeAdapter.sol:69`; `src/ZZZMigrationReceiver.sol:19` |
| R-10 | Medium | Tiny fee harvests could bias allocations through rounding | Accumulate ten-raw-unit fee batches and carry the remainder; explicitly resolve final migration dust. | `src/ZZZFeeController.sol:40`; `src/ZZZFeeController.sol:56` |
| R-11 | High | Spot-only or operator-supplied prices are unsafe execution authorities | External USD feed checks, reference/spot deviation, valid tick ranges, deadlines and on-chain minimum outputs. | `src/ZZZOracle.sol:34`; `src/ZZZStrategy.sol:30` |
| R-12 | High / operational | Ambiguous broadcasts and incomplete transaction identity checks | Persist intent before signing; no blind retry; validate sender/nonce/to/data/value and canonical receipt before clearing pending state. | `keeper/monitor.py:126`; `keeper/monitor.py:86` |
| R-13 | Medium / operational | Indexer lacked durable reorg-correct records | Atomic block/log/cursor storage, bounded common-ancestor rollback, replay-safe indexing and corrected burned-NFT projection. | `indexer/monitor.py:50`; `indexer/monitor.py:68` |
| R-14 | Medium / operational | Read client relied on a write-method blacklist | Use an explicit read-only JSON-RPC method allowlist; fail on unknown/bundler/write methods. | `zzz_ops/rpc.py:15`; `tests_python/test_rpc.py` |

### Important source review observations

The vault has no general `withdraw`, principal rescue, arbitrary selector execution or proxy upgrade entrypoint. That reduces obvious redemption paths, but is not a proof that principal cannot be lost through an approved strategy, external dependency or economic manipulation.

The liquidity manager uses explicit-liquidity PosM actions, not the deprecated FROM_DELTAS helpers. Fees are collected separately before changes. The second post-swap harvest was added during this review because a compounding/top-up swap may itself accrue fees to the pre-existing position.

Exact-token checks were strengthened after recognizing that a recipient-only check misses a token charging extra to the sender. This still does not prove that an approved token is non-malicious, non-upgradeable or permanently transferable.

The keeper transaction-value regression initially failed and was fixed before the final passing run. A timeout test was also corrected to expect the intentional fail-closed exception while verifying that pending state survives; the implementation must halt rather than pretend submission failed harmlessly.

## 5. Open blockers and residual risks

### O-01 — Verification blocker: no Solidity compilation/EVM execution

There may be syntax/type/import/ABI mismatches, stack/code-size issues, test errors, arithmetic edge cases or runtime failures that a compiler and EVM test run would reveal immediately. All Solidity behavior in this report is a source-level assessment. Successful textual checks are not a substitute. Resolve packages, compile and execute the full unit/fuzz suite before considering even a funded test deployment.

### O-02 — Integration blocker: no production transport implementation

`IZZZTransport` is a contract boundary, not an implementation of an actual bridge network. An additional reviewed provider-specific implementation is required. Exact token units, custody, finality, authentication, retries, fees, cancellation/refund evidence and upgrades must be established for the selected provider. A bound upgradeable provider can undermine supposedly immutable routing guarantees.

### O-03 — High trust/economic risk: governance, oracles and approved tokens

Governance retains timelocked oracle/eligibility/operator configuration. A bad oracle or malicious governance-approved configuration can cause unfavorable swaps and economic extraction without calling a principal withdrawal function. Thin/manipulable markets, token upgrades, blacklisting, transfer restrictions, rebases and chain failures can strand or destroy value. Neither spot checks nor a timelock guarantee honest external data.

### O-04 — Economic policy requires explicit approval

Power is lifetime contribution USD, not current productive LP value. Compounding does not increase it and market losses do not reduce it. Remote/in-flight positions remain eligible. Collective rewards use collection/delivery-time weights; uncollected historical fees are not retrospectively apportioned by swap-time weights. Deposit/harvest/bridge timing and persistently depreciated positions can change the incentive outcome. Checkpointing fixes published-index repricing only.

The new utilization threshold limits mostly idle deposits, but does not prove that the chosen Power formula is economically fair or resistant to oracle-driven inflation. The exact formula and timing policy require adversarial simulation and product approval.

### O-05 — Explicit migration scope and liveness limits

This design supports only canonical-to-satellite migration over routes fixed before sealing. It does not support arbitrary new future chains, return migration, onward migration or remote top-ups. Destination activation failures retain assets for retry; provider custody failures need provider-specific recovery that is not implemented here. Permanent locking plus immutable modules can make recovery impossible.

### O-06 — Operational scalability is unproven

The design uses separate LP NFTs and at most 32 reward assets. Many individual NFT rebalances can be expensive. Checkpoint loops, transaction size, repeated fee collection, transfer count, reorg backfills and all gas-dependent limits need real measurement. A keeper polls, but the contracts cannot guarantee execution every ten minutes or prevent all unfavorable MEV.

### O-07 — Buyback/burn limitations

Only direct approved token/ZZZ swaps and direct ZZZ burns are implemented. No general multi-hop route exists. The configured ZZZ token must have a working burn that decreases supply. Burning a wrapped ZZZ token on another chain does not automatically prove a reduction in canonical/global supply. Resolve those semantics and supported fee-token routes before marketing universal buyback support.

### O-08 — Dependencies and reproducibility are unresolved

Direct versions are specified, but dependency installation, published-package availability, lockfile integrity and immutable Git/action pins were not resolved in this environment. Official current source snippets may differ from installed release contents. Compare all minimal ABIs against the actual deployed/pinned contract versions. Do not treat the CI file as a completed CI run.

### O-09 — Off-chain runtime/provider assumptions remain

Tests use mocked RPC/signing processes. Live `cast` invocation, keystore handling, provider-specific receipts/L2 fees and real chain reorganizations were not exercised. RPC chain-ID and receipt checks assume honest-enough node data; they are not light-client proofs. A dedicated minimally funded keeper is necessary. The small public-data Keccak implementation passes known short vectors; a full independent long-message differential test should be added against the reviewed runtime toolchain before using it for deployment hash approval.

### O-10 — No independent adversarial audit or formal verification

This is not a certification and there is no claim of exhaustive vulnerability discovery. Stateful EVM invariant testing, malicious counterpart simulations, actual two-chain tests, formal reasoning about custody transitions and independent remediation review are outstanding. Test-only mocks intentionally bypass real venue/provider semantics and must never be used as live integrations.

## 6. Release decision

**Do not send real funds to this candidate.** Complete `docs/RELEASE_CHECKLIST.md`, settle the explicit economic/scope decisions, implement the production transport, and obtain an independent contract plus deployment-configuration review.

The deliverable is an improved, inspectable implementation candidate with useful evidence and an honest blocker list. It is not a claim that the permanently locked liquidity promise has already been proven safe.

## 7. Test source inventory

- `AccessController.t.sol`: 8 test functions, not executed.
- `BridgeSecurity.t.sol`: 10 test functions, not executed.
- `LiquidityEncoding.t.sol`: 10 test functions, not executed.
- `OracleAndTransfers.t.sol`: 13 test functions, not executed.
- `RewardsAndFees.t.sol`: 15 test functions, not executed.
- `VaultAccounting.t.sol`: 14 test functions, not executed.

The archive's per-file SHA-256 manifest binds this review package to the delivered source snapshot. Any subsequent source, dependency, configuration or compiler change requires renewed verification.
