# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

PoPL connects transferable NFTs to vault-managed liquidity. Activating an NFT attaches an LP allocation and unlocks two income streams: funded LP revenue and a separate share of NFT-sale royalties.

**Status: undeployed contract candidate; not approved for real funds.** The [website demo](https://popldemo.0xwave.com) uses simulated balances and transactions.

**Development verification (2026-10-18):** the same-chain handoff candidate has 582 passing regression tests, plus 34 unchanged-source focused handoff passes. The two opt-in fork setup skips are recorded separately. This is an undeployed development candidate, not production approval. See the [resume handoff](docs/WORK_HANDOFF.md) and [scoped verification](reports/canonical-handoff/VERIFICATION.md).

## Project navigation

| Purpose | Start here |
| --- | --- |
| Progress and remaining work | **[Project Todo](TODO.md)** - the single task list, with expandable acceptance criteria |
| What is built and tested | [Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) - capabilities, boundaries and verification |
| System design | [Architecture](docs/ARCHITECTURE.md) for interactions; [evolution and trust boundaries](docs/ARCHITECTURE_EVOLUTION.md) for migration limits; [Component map](docs/COMPONENT_STATUS.md) for each module's responsibilities |
| Security and release | [Security audit plan](docs/SECURITY_AUDIT_PLAN.md) for review criteria; [Release approval record](docs/RELEASE_CHECKLIST.md) for the final go/no-go decision |

## Architecture overview

| Layer | Responsibility | Code and documentation |
| --- | --- | --- |
| **1. Smart contracts** | NFT ownership, shared LP custody, per-NFT shares, funded reward accounting and authorization. Entry routes contributions into the Vault; separate ledgers account for LP fees and royalties. | [Vault source](src/ZZZVault.sol), [Activation Entry](docs/ACTIVATION_ENTRY.md), [economics](docs/ECONOMICS.md) |
| **2. Backend and operations** | The keeper coordinates authorized LP maintenance. The schema-2 API checks canonical lifecycle before serving ownership/balances and can combine complete pinned same-chain predecessor LP/royalty claim history. Services still need hosting and operating qualification. | [Keeper](keeper/monitor.py), [indexer](indexer/monitor.py), [read API](docs/FRONTEND_API.md), [lifecycle boundary](docs/FRONTEND_LIFECYCLE.md), [lifetime claims](docs/FRONTEND_LINEAGE.md) |
| **3. Frontend** | The separate website presents minting, activation, portfolios and claims. Live wallet transactions and data integration remain pending. | [Website repository](https://github.com/ABEF/AAA-website), [integration tasks](TODO.md#frontend) |

Many NFTs share one physical Uniswap v4 LP position per supported pool/strategy, with independent NFT share accounts. Maintenance operates on that shared position, without looping through every holder. The initial collection is intended to use one pool. The Vault permits **four permanently admitted/historical custody buckets**, including unfunded reservations and imports; an existing bucket's migration or return reuses its slot. This bounds settlement work, not the number of NFTs. See the [architecture and capacity boundary](docs/ARCHITECTURE.md).

## NFT lifecycle

| Step | Rule |
| --- | --- |
| **Mint** | Pay exactly **0.05 ETH** to the immutable mint recipient for a dormant NFT. Minting adds supply, not liquidity or reward eligibility. |
| **Activate** | After traits are revealed, contribute at least **$100 in original gross input value**. At least **99% must become new LP**; conversion costs, slippage and undeployed input share one 1% limit. Network gas is separate. |
| **Add liquidity** | Further contributions grow the same NFT's LP allocation under the same execution limit. Existing holders' assets cannot subsidize that limit; a top-up creates no extra collective membership. |
| **Hold or transfer** | The current owner can claim its funded balances. Transfers carry the LP allocation, remaining unclaimed balances and future fee rights. A seller can claim before a transfer, so an earlier listing balance is not guaranteed to the buyer. |

**LP principal cannot be redeemed by holders.** It remains managed by the protocol for rebalancing, compounding and approved migration. A right to future funded fees has no expiry, but does not guarantee future revenue or capital value.

Target activation assets are **ETH, ZZZ, USDG and USDC**, admitted by reviewed address and route. Actual routes and feeds still require qualification; USDC has no qualified funded route. The [atomic Entry](docs/ACTIVATION_ENTRY.md) binds the original contribution value through conversion into LP; [route qualification](docs/ACTIVATION_ROUTING.md) covers the remaining integration work.

## Revenue and claims

### LP and creator revenue

The allocation is fixed in the current contracts:

| Use | Share | Basis |
| --- | --- | --- |
| Individual NFT holders | **80%** | Proportional to each NFT's shares in the earning LP bucket |
| Collective rewards | **10%** | Equal per activated NFT, across pools |
| LP compounding | **5%** | Reserved for reinvestment in the earning bucket |
| ZZZ buyback and burn | **5%** | Reserved for approved execution |

Rarity does not change LP or collective weights; there is no Power multiplier. Actual receipts allocate in batches of 20 raw token units, with a documented sub-20-unit incumbent-dust exception at membership/migration boundaries. Returned remote holder rewards are already allocated and are not split again. See [accounting and timing](docs/ECONOMICS.md).

The selected Robinhood ZZZ/native-ETH Pons pool has **0% conventional LP fees**. Creator/hook revenue is a separate funding path: the reported proportional-liquidity agreement still needs final payment and measurement terms. Adding LP does not by itself fund claims. See [current market qualification](TODO.md#task-pons-qualification) and [creator revenue-sharing proposals](docs/REVENUE_SHARE.md).

### NFT-sale royalties

ERC-2981 requests **5% of sale value** to the immutable royalty receiver. **100% of eligible receipts** are shared among activated NFTs at **Commun x1 / Rare x2 / Legendary x3**, independently of LP shares. Prefunds, pre-admission receipts and payments with no eligible members stay quarantined. ERC-2981 does not enforce marketplace payment. See the [separate royalty ledger](docs/NFT_METADATA.md#separate-marketplace-royalties).

Claims follow funding events, not a per-minute clock. LP claims use allocated balances; royalty claims also synchronize pending admitted receipts. Direct claims take one NFT and asset; the [claim router](docs/CLAIM_ROUTER.md) supports up to **32 mixed LP/royalty operations**, paid to the current owner. [Timing and keeper schedules](docs/OPERATIONS.md#reward-timing-and-maintenance-schedule) explain when processing occurs.

## Collection and artwork

- **Supply:** at most **1,000 NFTs**, with exact eventual quotas of **600 Commun / 300 Rare / 100 Legendary**.
- **Assignment:** an authenticated random draw selects fixed inventory entries without replacement, finalized in mint order. There is no administrator trait selection or reroll. A stalled earlier request can block later reveals; live VRF qualification remains open.
- **Fixed traits:** rarity, palette and pattern never change. Eight colors form 58 palettes across monochrome, bicolor and tricolor styles; four patterns produce **2,784 rendered evolution states**. Palette and pattern do not change rewards; rarity affects only royalty weight.
- **Evolution:** Dormant until activation; afterward, current marked LP value selects Activated, **Enhanced from $1,000**, or **Singularity from $10,000**. Falling value can downgrade art without removing activation or fee rights. Remote or stale valuation is explicitly unavailable.

The [metadata specification](docs/NFT_METADATA.md) and [artwork catalogue](design/nft-metadata/palette-system-v1/README.md) detail inventory quotas, duplicate limits, palettes and patterns. The [IPFS bundle](docs/ARTWORK_PUBLICATION.md) is prepared; provider selection, publication and marketplace refresh testing remain open.

## Governance, custody and recovery

Governance is a deployment-selected multisig acting through a timelock, with separate guardian and keeper roles. Production addresses are not yet selected; the [address inventory](docs/DEPLOYMENT_ADDRESSES.md) distinguishes wallets, deployed contracts and network dependencies. **Sealing fixes module implementations and local venue bindings.** Supported assets, routes, feeds, destinations and strategy parameters remain configurable within explicit controls. New algorithms or unsupported venues require separately reviewed compatible deployments. See the [change and recovery matrix](docs/CHANGE_AND_RECOVERY.md).

Timelocked governance can [park custody while globally paused](docs/CUSTODY_PARKING.md), closing into the Vault under an exact snapshot and raw output minimums without source prices or creator-inbox synchronization. Resume requires fresh deployment guards. Failed external tokens or venues can still prevent movement.

**LP migration is not collection migration.** The new [same-chain handoff candidate](docs/CANONICAL_HANDOFF.md) freezes and carries NFT ownership, both reward ledgers and exact classified backing to one replacement, with atomic retirement/activation and a fully funded abort path. Cross-chain canonical relocation still needs verified finality, authenticated channel closure, a new lineage/message boundary and reviewed transport before sealing. Post-halt recovery is deferred. Real bridging remains disabled pending independent destination-admission review, provider/backing review and multi-chain rehearsals. Local permanent capacity reservation is implemented; the source does not authenticate remote admission proof. These risks are tracked in the [security audit plan](docs/SECURITY_AUDIT_PLAN.md).

## Keeper and operating services

The keeper defaults to dry run. Its example ten-minute polling interval does not force rebalancing: price movement, cooldown and execution guards must pass. The optional metadata watcher is disabled by default and uses the same bounded transaction path. Full keeper/state-lock operation requires Linux/Unix and Python 3.11+.

| Need | Documentation |
| --- | --- |
| Configure maintenance and services | [Operations](docs/OPERATIONS.md) |
| Recover from outages or server loss | [Keeper recovery runbook](docs/KEEPER_RECOVERY.md) |
| Inspect staging and monitoring evidence | [Operating rehearsals](docs/KEEPER_REHEARSALS.md) |
| Review remaining keeper risks | [Internal keeper review](reports/keeper-recovery/REVIEW.md) |
| Choose randomness, pricing and other dependencies | [Production service decisions](docs/PRODUCTION_SERVICES.md) |

## Verification and release status

The [handoff verification record](reports/canonical-handoff/VERIFICATION.md) covers the current candidate and its limits. Earlier [architecture verification](reports/architecture-evolution/VERIFICATION.md) and [migration safety evidence](reports/migration-safety/VERIFICATION.md) retain their original source scope; they do not verify later handoff changes. Different-pair conversion and cross-chain canonical relocation remain open. Future cross-chain successor activation requires verified finality, with no multisig-only override.

The historical [NFT economic-rights verification](reports/nft-rights-audit/VERIFICATION.md) records **531 offline Solidity passes**, two expected fork-setup skips, **23 normal size gates** and an extended invariant run of **65,536 calls**. The report separates fresh checks from reused static/fork evidence and the broader local Python candidate. The [internal review](reports/nft-rights-audit/REVIEW.md) records findings and remaining risks; [historical reports](reports/README.md) retain their original source scope.

Production approval still requires qualified market/input routes, tokens and price feeds; supported VRF; authority addresses and creator terms; live frontend/backend integration; target-chain gas and operating rehearsals; and an independent audit with remediation. Track these in the [Project Todo](TODO.md); record final sign-off in the [release approval record](docs/RELEASE_CHECKLIST.md) with the [production inventory](config/production.example.json). Check [CI for the exact revision](https://github.com/ABEF/AAA/actions); local evidence does not imply a green published workflow.

## Development

From the repository root, in the [supported development environment](docs/DEVELOPMENT.md):

```sh
bash scripts/install-deps.sh
bash scripts/verify.sh
python3 scripts/sync-project-todo.py --check
```

The verifier runs the Python/source checks, normal build/size checks and offline Solidity tests. Solidity is pinned to **0.8.26/Cancun** with the existing via-IR optimizer profile. Explicit fork and static-analysis commands are in the development guide. Deployment scaffolding is local-only; these commands do not deploy public contracts.

When work progresses, update the [task ledger](docs/project-todo.json) and its linked evidence using the [Todo maintenance procedure](docs/TODO_WORKFLOW.md). Keep unfinished local candidates, published code, test evidence and deployment status distinct.
