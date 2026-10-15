# ZZZ Collection — Proof of Permanent Liquidity (PoPL)

## Project overview

The concept is to turn NFTs from speculative collectibles with little real utility into productive assets backed by permanent liquidity.

Instead of burning a made-up token to activate an NFT, users must permanently lock ZZZ/ETH or ZZZ/USDC liquidity. The current implementation uses **WETH** for the ETH pair because its liquidity adapter accepts ERC20 assets.

Minting through `ZZZVault.mintDormant()` costs exactly **0.05 ETH** and creates a dormant NFT with no LP, Power, or earned fees. The payment is forwarded to an immutable deployment-selected recipient, separately from locked principal. The current NFT owner later calls `activate(...)`, which must deploy at least **$500 of oracle-valued LP** for that same NFT. Minting alone never increases the collection's liquidity.

NFTs in the same approved pool share **one underlying LP position**. Each activated NFT holds nonredeemable internal shares and its own funded fee balance. The keeper collects, compounds and rebalances once per pool, independent of how many NFTs participate. The 50% owner allocation follows pool shares; the 30% collective allocation follows lifetime contribution Power.

New shares are priced against the shared position's current oracle-valued principal and designated compounding reserves. Joining or topping up checkpoints earlier fees before shares change; donations and unclaimed rewards do not buy shares. Whole-pool migrations preserve the canonical NFT/share ledger. See [shared-pool accounting](docs/ARCHITECTURE.md).

The underlying capital remains permanently locked but can be automatically rebalanced and compounded to maximize its productivity. Permanent locking means holders cannot redeem principal; it does not guarantee capital value, returns, or successful execution.

The NFT can be freely traded, transferring its economic rights to a new owner without ever withdrawing the underlying liquidity. Unclaimed rewards follow the NFT's current owner.

The goal is simple: replace speculative NFT utility with real, revenue-generating rights while permanently strengthening ZZZ's liquidity.

**The key innovation is separating capital permanence from economic ownership.**

## Revenue distribution

Trading fees collected from permanent liquidity positions are allocated as follows:

| Share | Destination | Purpose |
|---|---|---|
| **50%** | NFT owner | Pool owner-fee index, proportional to each NFT's nonredeemable shares |
| **30%** | Collective reward pool | Distributed among participating NFTs according to their weighted Power scores |
| **10%** | Permanent LP compounding | Reinvested into liquidity, permanently increasing its underlying capital |
| **10%** | ZZZ buyback and burn | Used to purchase and burn ZZZ, linking trading activity to token supply reduction |

The candidate allocates fees in ten-raw-unit batches and carries smaller remainders. Its Power score measures lifetime user contributions valued at deposit time. Collective allocation uses Power at collection or delivery time. See [economic rules](docs/ECONOMICS.md) for timing, rounding, and scope.

## Example: PoPL NFT #444

| Attribute | Illustrative value |
|---|---|
| Pool | ZZZ/ETH, represented by ZZZ/WETH in this implementation |
| Associated permanent LP | $4,270 |
| Unclaimed fees | $184 |
| Status | Enhanced — proposed product attribute |

When sold, the buyer inherits the NFT, its shares in the shared liquidity position, unclaimed rewards, and future revenue rights. Liquidity remains permanently locked while its economic ownership is transferable.

These figures are illustrative. NFT levels and the "Enhanced" status are product concepts, not implemented mechanics or live position data.

Current verification: [creator-payment implementation and internal review](reports/reward-funding/README.md). The [earlier shared-pool review](reports/pooled/README.md) records its own 2026-10-15 revision. Production remains undeployed and requires the selected native/hooked market integration, payment-policy review, staged operations and an independent audit.

## Technical architecture

| Main component | Role | Current implementation |
|---|---|---|
| **Permanent vault / locker** | Holds liquidity and attributed idle principal, allowing authorized rebalancing and compounding without principal redemption | `ZZZVault` and its custody modules |
| **Liquidity and revenue engine** | Manages Uniswap positions, collects and allocates fees, compounds, and executes buybacks | Hookless Uniswap v4 PositionManager integration plus strategy and fee modules |
| **NFT ownership layer** | Represents transferable economic rights and links each NFT to its position and Power | ERC-721 `ZZZNFT`, vault records, rewards, and Power modules |

The proposed product architecture includes a Uniswap v4 hook. **This candidate does not implement a custom hook**: it supports static-fee pools without hooks. A custom hook and NFT attribute/level mechanics remain future work.

The selected Robinhood Chain ZZZ/native-ETH pool has **0% conventional LP fees** and a separate Pons hook fee. Its native-ETH liquidity settlement is not implemented by this adapter. The creator intends to send payments to a dedicated immutable receiver, which processes funded revenue into the existing 50/30/10/10 allocation. See [creator-funded rewards](docs/EXTERNAL_REWARDS.md) and the verified [Robinhood pool record](docs/ROBINHOOD_POOL.md).

```text
User -> Permanent vault -> Liquidity manager -> Uniswap v4 position
            |
            +-> Transferable PoPL NFT
            +-> Fee controller -> 50% individual + 30% collective rewards
                              -> 10% permanent compounding
                              -> 10% ZZZ buyback and burn

Keeper -> authorized maintenance operations
Indexer -> confirmed events, ownership, and position history
```

See [technical architecture](docs/ARCHITECTURE.md) for custody, reward accounting, and migration lifecycles.

## Contracts

The 16 original modules and the fixed bridge router are present (17 sealed modules), plus a standalone receiver helper created by the fee controller. Their inclusion does not establish safe runtime behavior.

| Contract | Responsibility |
|---|---|
| [ZZZVault.sol](src/ZZZVault.sol) | Paid dormant minting, owner activation, shared LP custody, nonredeemable NFT shares and attributed idle balances |
| [ZZZNFT.sol](src/ZZZNFT.sol) | Transferable NFTs representing permanent LP economic rights |
| [ZZZLiquidityManager.sol](src/ZZZLiquidityManager.sol) | Creates, increases, collects, closes, and redeploys Uniswap positions for authorized custody operations |
| [ZZZRewards.sol](src/ZZZRewards.sol) | Funded individual and Power-weighted collective rewards |
| [ZZZRewardReceiver.sol](src/ZZZRewardReceiver.sol) | Immutable per-bucket creator-payment inbox; optional native wrapping and permissionless funded processing |
| [ZZZPower.sol](src/ZZZPower.sol) | Contribution-based Power and reward checkpoints |
| [ZZZFeeController.sol](src/ZZZFeeController.sol) | 50/30/10/10 fee allocation and isolated reserves |
| [ZZZStrategy.sol](src/ZZZStrategy.sol) | Oracle-relative ranges, rebalance triggers, cooldowns, and swap bounds |
| [ZZZCompounder.sol](src/ZZZCompounder.sol) | Reinvests the compounding reserve through the vault |
| [ZZZBuyback.sol](src/ZZZBuyback.sol) | Direct-route buybacks and supply-checked ZZZ burns |
| [ZZZMigration.sol](src/ZZZMigration.sol) | Coordinates approved source-to-destination migration and remote rewards |
| [ZZZBridgeAdapter.sol](src/ZZZBridgeAdapter.sol) | Fixed economic-message boundary and replay protection |
| [ZZZBridgeRouter.sol](src/ZZZBridgeRouter.sol) | Immutable provider policies, exact funding and timelocked future bridge onboarding |
| [ZZZMigrationReceiver.sol](src/ZZZMigrationReceiver.sol) | Incoming asset custody, destination activation, retries, and acknowledgements |
| [ZZZAccessController.sol](src/ZZZAccessController.sol) | Timelocked governance, fixed module bindings, operators, and pauses |
| [ZZZOracle.sol](src/ZZZOracle.sol) | Feed validation and value/price checks |
| [ZZZPoolRegistry.sol](src/ZZZPoolRegistry.sol) | Approved tokens, pools, and bounded strategy parameters |
| [ZZZMigrationRegistry.sol](src/ZZZMigrationRegistry.sol) | Append-only destinations, adapters and token mappings; new routes require timelocked governance after sealing |

New bridge policies and migration routes can be approved after sealing, so liquidity can move to a later-selected EVM chain or pool and migrate again. The canonical registry also approves remote-to-remote paths; authenticated custody epochs and acknowledgements track each move. Assets remain attributed to the same canonical NFT without adding Power or minting replacement NFTs. Each route permanently binds its provider policy; switching bridge providers requires a new policy and route ID. Outbound policies begin disabled, and old authenticated receipts remain valid after disabling sends. The vault and adapter never change. Each destination, asset mapping and production provider wrapper still requires review; no live bridge SDK is bundled. See [future bridge onboarding](docs/BRIDGE_ONBOARDING.md). See [architecture](docs/ARCHITECTURE.md).

Governance is the deployment-selected `GOVERNANCE_MULTISIG`, not an automatic vote of NFT holders. The local deployment template uses a two-day timelock and a further two-day migration execution delay. Sealing removes bootstrap authority and fixes core module addresses; it does not disable timelocked approval of new routes. These destination-selection powers create governance trust even though the current vault has no principal-redemption function.

## Off-chain components

| Component | Role |
|---|---|
| [ZZZKeeper](keeper/monitor.py) | Polls every 600 seconds by default; simulates and submits eligible operations with spending and pending-transaction safeguards |
| [ZZZIndexer](indexer/monitor.py) | Persists confirmed events in SQLite, handles bounded reorganizations, and projects NFT ownership |

Both use Python 3.11+ and shared utilities in `zzz_ops/`. Keeper state locking requires Linux/Unix. The indexer provides event data rather than a complete hosted dashboard/API. See [operations](docs/OPERATIONS.md).

## Development status

**Development candidate. Do not deploy with real funds.** The [current reward-funding review](reports/reward-funding/README.md) records the external payment and entry-ordering checks. Local targeted verification passed 45 tests: 43 security cases and two invariant-suite tests. Python inventory is 255 tests; 251 portable Windows tests passed, with four Unix-only cases retained for Ubuntu. Slither produced 160 reviewed findings, with a second internal review of all 91 High/Medium findings. This is not an independent audit. The full offline Solidity run passed 279 cases with zero failures and one intentional offline fork-setup skip; exact-commit CI completion must be checked in the current report.

The unchanged compiler profile produces Vault runtime **24,212 bytes** (364 below EIP-170) and FeeController runtime **24,203 bytes** (373 below). Both margins are small and require review. These checks do not supply selected Pons-market support, a live bridge, production configuration or funded-deployment approval.

The following table preserves earlier evidence, principally from the 2026-10-14 readiness pass. Its counts do not verify the new external funding code. Historical [future-bridge](reports/future-bridge/README.md) and [production-readiness](reports/PRODUCTION_READINESS.md) reports remain scoped to their own revisions.

| Evidence | Status |
|---|---|
| Original Python verification | 84 passed: 66 implementation tests and 18 mathematical model tests |
| Publication check on Windows | 81 passed, 1 failed, 2 errors; three state tests require Unix permissions/`fcntl` |
| Solidity unit/fuzz verification | Paid-mint and repeated-migration tests execute the development contracts with mocked LP venues/transport; see current [implementation evidence](reports/IMPLEMENTATION_UPDATE.md) |
| Solidity compilation and module bytecode sizes | All contracts/tests/scripts compile; all 17 modules fit standard EVM size limits |
| Stateful EVM accounting | Independent integer-ledger handler model; default 32 runs × 128 calls, with a larger audit profile |
| Slither | Pinned 0.11.6 analysis with individual review coverage; CI rejects source drift and unreviewed findings; see dated evidence |
| Real Uniswap fork tests | Six tests passed at a fixed Robinhood block/hash with deployed dependencies; the requested Pons pool is checked and rejected, adapter flows use a separate local hookless test pool |
| Gas benchmarks | 1/100/1,000 NFTs and 32 funded reward assets; mock venue costs are explicitly separated from real network costs |
| Production bridge transport and real cross-chain tests | Not completed |
| Independent security audit | Not performed |

Python model tests do not execute Solidity. The Windows Python result does not supersede the historical Linux-environment evidence; both are retained. The earlier repaired Ubuntu run passed 84 Python and 70 Solidity tests. Publication findings remain in [publication verification](reports/PUBLICATION_CHECKS.json), and historical build results remain in [CI repair evidence](reports/CI_REPAIR.md). New implementation evidence is recorded separately. Check the latest [GitHub Actions run](https://github.com/ABEF/AAA/actions/workflows/verify.yml) for the exact commit's complete CI status.

Current limits include contribution-based Power, at most 32 reward assets, direct-route buybacks, equivalent-asset migration rather than arbitrary asset conversion, and no satellite user top-ups. Native-ETH/hook integration for the selected Robinhood pool and a reviewed production bridge are still pending. See [economic rules](docs/ECONOMICS.md), [security entry point](SECURITY.md), and the [release checklist](docs/RELEASE_CHECKLIST.md).

The intended external source is **creator payments sent directly to a bucket's receiver**. Only actually funded and processed receipts are distributed; no creator percentage, guaranteed payout or 34% liquidity-based entitlement is assumed. The 50% owner allocation follows bucket shares; the 30% collective allocation follows lifetime contribution Power. The [blocked production inventory template](config/production.example.json) and read-only validator require reviewed payment policy, receiver/wrapper inventory, authentic release evidence and separately authorized deployment. External intake does not enable the selected Pons pool's native/hooked LP custody.

## Repository guide

| Path | Contents |
|---|---|
| `src/` | Solidity modules, interfaces, shared types, and token-transfer helper |
| `test/` | Foundry tests and test-only mocks |
| `keeper/`, `indexer/`, `zzz_ops/` | Off-chain services and shared utilities |
| `tests_python/` | Off-chain regression tests and mathematical models |
| `script/DeployCore.s.sol` | Local-only deployment template |
| `scripts/` | Dependency setup, verification, schema generation, and source checks |
| `docs/` | Product, economics, architecture, development, operations, and security documents |
| `reports/` | Historical test evidence and current publication checks |
| `MANIFEST.sha256` | SHA-256 inventory for the organized Git snapshot, excluding itself |

Start with the [product specification](docs/PRODUCT.md), [development setup](docs/DEVELOPMENT.md), or [roadmap](docs/ROADMAP.md). Original package documentation and hashes are preserved under [reports/history](reports/history/README.md).

On Linux/Unix with Python 3.11+:

```bash
python3 scripts/run_python_tests.py
python3 scripts/source_checks.py
```

Then install and verify the Solidity dependencies using the steps in [development setup](docs/DEVELOPMENT.md). Source consistency checks are not a compiler or a security audit.
