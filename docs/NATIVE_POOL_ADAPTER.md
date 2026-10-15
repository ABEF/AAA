# Selected native-ETH/Pons pool adapter candidate

Updated 2026-10-15. This describes undeployed development code. It is not an independent audit, a production deployment approval, a creator-payment agreement or evidence of supported production USD/VRF services. No public-chain transaction is needed to run the fork tests.

## Venue identity and accounting assets

The selected Robinhood mainnet pool is `0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f`: native ETH / ZZZ, static core LP fee zero, spacing 200 and the reviewed Pons hook. `ZZZPoolRegistry.configure()` still rejects native currencies and hooks. The separate `configureNative(PoolConfig)` accepts only that exact PoolKey on chain 4663, with pinned deployed dependencies, bindings, hook permissions and frozen per-pool fee terms. This is candidate capability, not production approval.

- `get(poolId)` returns the **real** native/Pons key. Only this key identifies the actual Uniswap venue or may be hashed to reproduce its pool ID.
- `accounting(poolId)` returns a copy with native slot zero normalized to canonical WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`. Venue slot orientation is retained; do not sort or hash this accounting key as a new pool.
- `nativeAsset(poolId)` returns that WETH for the admitted native pool and zero for a supported ordinary ERC20 pair.

Vault principal/idle balances, reward currencies, price reads, fee allocation, metadata valuation and migration principal vectors use canonical ERC20 accounting assets. The adapter retains the real native key. LP NFT ownership stays in the Vault; principal remains nonredeemable. Native ETH is not added to the general LP/reward/bridge ledger.

## Typed settlement and the contribution budget

Mint/increase pulls authorized WETH/ZZZ budgets and unwraps only the exact rounded-up native principal debt. With this admitted static-fee key and no liquidity callbacks, the debt follows the actual spot, ticks and liquidity. The adapter passes exactly that native value to PositionManager and verifies that its prefunded native balance is unchanged afterward. It never sweeps the PositionManager's whole balance. An unexpected fee offset/remainder fails atomically; the Vault harvests before increasing an existing position.

Collect/close take native credits to the adapter, admit receive callbacks only from the expected PoolManager, wrap only the actual callback amount, and return canonical ERC20 credits to the Vault. Existing forced ETH and token donations are excluded. Unexpected forced ETH during settlement fails the balance checks. Per-operation ERC20 and Permit2 approvals are cleared.

Disabling pool deposits/strategy operations blocks mint, increase and swaps, while typed collect/close remain available to the Vault under the same real-key, custody and wrapper-policy checks. The adapter computes closing principal from the venue's actual spot and ticks without a USD oracle read. The higher-level Vault still calls `Strategy.validateExitPrice`: it ignores the disabled-source flag but retains the same fresh-oracle and spot-deviation checks as ordinary strategy validation. A stale feed blocks Vault migration until governance admits a reviewed working replacement through the existing oracle configuration. Pause, migration authorization and destination-admission checks also apply. There is no implicit oracle or wrapper-policy bypass.

Exact-input swaps use the actual returned **post-hook** delta, require the whole input to be consumed and check the recipient's exact net output. Native debt calls `sync(address(0))` before payable `settle`, so another synced ERC20 cannot poison native settlement. Native output is taken to the adapter and wrapped before delivery.

The reviewed Pons hook charges 100 basis points of exact-input output. Strategy balancing compensates for this fee when choosing how much to swap: `swap value = excess / (1 - target input weight × 1%)`. This balances the net pair rather than leaving the output fee as undeployed input. It is not an execution guarantee; oracle deviation, protocol fees and price impact remain subject to actual slippage and Vault contribution-budget checks. Network gas is separate. No budget check is reduced to make a quote succeed.

Core protocol-fee observations and mutable Pons creator recipient/buyback settings do not freeze normalization or custody. Those settings do not add liquidity callbacks. Swaps enforce net execution output. Pons buyback/vesting is separate from PoPL's own 5% buyback-and-burn allocation. Ordinary LP ownership still creates no automatic entitlement to Pons revenue; only actual separately funded receipts can be allocated to NFTs.

## Canonical wrapper upgrades and governance

The canonical WETH is a proxy. At pinned block 88,544,093, the implementation is `0xC6B81b429797E0f555440b70cD99e032D7AE947e`, its ProxyAdmin is `0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF`, and the observed ProxyAdmin owner is `0x2A153c6A1B66DBc930a8d7017230ab0253005C09`. These are third-party authorities, not selected PoPL governance wallets. The bootstrap policy records their observed code hashes and addresses; actual matching is required before native admission.

`WrapperPolicy` commits to `admin`, `implementation`, `adminOwner`, `adminCodeHash` and `implementationCodeHash`. Its ID is `keccak256(abi.encode(policy))`.

1. Governance reviews the actual upgrade, code, proxy storage, authority and exact-transfer/1:1 wrapping behavior off-chain.
2. `approveWrapperPolicy(policy)` records a new immutable policy only when current code and public ProxyAdmin observations match it. A duplicate policy cannot overwrite history.
3. `activateWrapperPolicy(id)` rechecks the observations and selects that recorded policy. Approval alone does not change the active policy.

After sealing, both calls require the existing governance timelock. Its configured delay is unchanged; reviewed calls can be scheduled using the normal timelock workflow. All historical policy records remain available. No wrapper-address replacement, arbitrary transaction, LP-recipient change, principal withdrawal or rescue is introduced.

A normal implementation/admin/owner change fails native normalization closed until a matching reviewed policy is approved and activated. This allows reviewed infrastructure maintenance without a contract-code upgrade. Operations may be unavailable between the third-party upgrade and governance activation, so advance coordination and a rehearsed recovery procedure remain production requirements.

An explicitly reviewed zero `adminOwner` is permitted for a ProxyAdmin whose ownership has been renounced. The nonzero administrator and implementation addresses, code hashes and current reported bindings still have to match. Renunciation does not silently change the active policy: governance must approve and activate the zero-owner policy through the same timelock, retaining the historical owner record.

**Trust limitation:** public ProxyAdmin getters are not an on-chain proof against every hostile admin handoff. A malicious replacement implementation could answer fallback getters deceptively after the old ProxyAdmin loses its administrative position. Runtime hashes, reported identities and exact per-operation wrap checks do not eliminate that third-party upgrade authority. Governance must independently review actual proxy storage, source and ownership; admitting a policy is an explicit security decision. The canonical WETH proxy address and real PoolKey remain fixed.

## Verification scope and remaining qualification

The native unit suites cover dirty native sync, partial fills, post-hook minimum output, forced ETH/prefund isolation, incorrect wrapper behavior, reentry rejection, amount bounds and typed custody. Wrapper-policy tests cover immutable records, failed observation checks, unauthorized calls and real delayed governance approval/activation after sealing.

The opt-in `test/NativePoolFork.t.sol` targets the **actual selected native/Pons pool** at block 88,544,093 and checks its pinned block hash. It covers mint/increase/collect/close, both swap directions, range reopening, prefunds, changed dependencies, mutable payout settings, a local simulated EIP1967 implementation upgrade followed by reviewed policy activation, two NFTs sharing one physical LP, creator-funded claims and a single bucket rebalance preserving both NFTs' shares.

The existing CI fork job runs both exact contracts through the same runner:

```text
python scripts/run-fork-checks.py --upstream https://YOUR_ARCHIVE_RPC --forge PATH_TO_PINNED_FORGE
```

Use the pinned Forge 1.4.4 build recorded by the script and an explicitly selected HTTPS archive RPC (loopback HTTP is also accepted for a local service). The runner enables `RUN_ROBINHOOD_FORK_TESTS=true`, routes Forge through its local read-only relay, uses one test thread, disables storage caching and preserves the 1.25-second minimum serial RPC cadence. It never signs or broadcasts. The anchored class filter selects `UniswapV4ForkTest` and `NativePoolForkTest`; CI records Forge JSON output and diagnostics in its existing fork log. A zero Forge exit code is insufficient: both exact suites must contain every test declared in their current source files, and every result must be successful with zero skips. Missing suites, setup skips, inherited test filters and partial inventories fail the runner. At this source snapshot the required inventory is nine original tests plus 20 native/Pons tests, including paused parking, close-only principal minimums and guarded resumption. This runner integration has targeted Python regression coverage; an actual CI result still belongs to the exact revision on which it runs.

Mock authority, mocked VRF and synthetic USD reference calibration remain explicit test scaffolding. The bucket-rebalance test forces only the policy decision and tests custody/accounting, not production trigger economics. These tests do not establish reliable production price feeds, real randomness, creator-payment terms, bridge backing, operating gas safety for every asset combination, testnet rehearsals or an independent audit. The original alternative hookless-pool fork suite remains distinct coverage; including it in the same command does not make it evidence of actual Pons custody. The release checklist remains NOT APPROVED until the outstanding production gates are satisfied.

Future work: design and independently review an explicit governance-bounded oracle-independent custody exit if the production outage model requires it. Such a path would need concrete per-asset minimum amounts, delayed authorization and destination/backing review; the current candidate does not silently skip the oracle when a service fails.
