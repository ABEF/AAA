# ZZZ Collection — Proof of Permanent Liquidity

PoPL connects transferable ERC-721 NFTs to shared, Vault-managed ETH/ZZZ liquidity.
Activating an NFT attaches independently accounted LP shares. Active NFTs receive
funded LP rewards and rarity-weighted NFT-sale royalties. Principal is not
holder-redeemable during normal operation; governance can permanently end LP
activity and return the actual ETH+ZZZ to NFT owners.

**Undeployed production candidate. Production is NOT APPROVED.**

Start with the [current review](reports/CURRENT_REVIEW.md),
[consolidated findings](docs/AUDIT_FINDINGS.md), [sole Todo](TODO.md) and
[qualification roadmap](docs/ROADMAP.md). They distinguish implementation,
source-scoped verification, operating adoption and launch approval.

## Architecture

| Layer | Responsibility | Main components |
| --- | --- | --- |
| Ownership, mint and metadata | ERC-721 ownership, dormant minting, fixed artwork draw and confirmed LP evolution. OpenSea integration and randomness still need live qualification. | [NFT](src/ZZZNFT.sol), [SeaDrop mint](src/ZZZSeaDropMint.sol), [metadata](src/ZZZNFTMetadata.sol), [mint guide](docs/OPENSEA_MINT.md) |
| Principal and LP execution | Authenticate ETH/fixed-ZZZ contributions, checkpoint incumbents, deploy actual marginal LP and issue shares. Manage one main and optionally one residual in the same pool. | [Entry](src/ZZZActivationEntry.sol), [Vault](src/ZZZVault.sol), [LiquidityManager](src/ZZZLiquidityManager.sol), [Balancer](src/ZZZLPBalancer.sol), [portfolio profile](docs/POSITION_V7.md) |
| Funded income | Allocate collected LP receipts, maintain exact-unit NFT claims, reinvest designated compound and buy/burn ZZZ. Keep royalty receipts and entitlements separate. | [FeeController](src/ZZZFeeController.sol), [Rewards](src/ZZZRewards.sol), [Membership](src/ZZZMembership.sol), [Compounder](src/ZZZCompounder.sol), [Buyback](src/ZZZBuyback.sol), [RoyaltyRewards](src/ZZZRoyaltyRewards.sol) |
| Policy and safeguards | Direct governance permissions, bounded pool/route/source configuration, independent valuation, strategy, confirmation and execution controls. | [Access](src/ZZZAccessController.sol), [Registry](src/ZZZPoolRegistry.sol), [ProtocolPolicy](src/ZZZProtocolPolicy.sol), [PortfolioPolicy](src/ZZZPortfolioPolicy.sol), [Oracle](src/ZZZOracle.sol), [Strategy](src/ZZZStrategy.sol) |
| Recovery and replacement | Governed same-pair LP movement, parking, residual consolidation, irreversible holder return and compatible pre-exit same-chain replacement. | [Migration](src/ZZZMigration.sol), [budget](src/ZZZMigrationBudget.sol), [canonical coordinator](src/ZZZCanonicalHandoff.sol), [recovery matrix](docs/CHANGE_AND_RECOVERY.md) |
| Backend and operations | Read confirmed state, index history, prepare exact unsigned transactions, and run authorized maintenance with durable recovery. | [Keeper](keeper/monitor.py), [indexer](indexer/monitor.py), [read API](docs/FRONTEND_API.md), [history](docs/EARNINGS_HISTORY.md), [operations](docs/OPERATIONS.md) |
| Website consumer | Present confirmed holdings, value, rewards and unsigned reviews. Demo and versioned integration environments remain separate; public signing is disabled. | [Website repository](https://github.com/ABEF/AAA-website), [environment map](docs/SITE_ENVIRONMENTS.md), [source10 consumer](docs/SOURCE10_WEBSITE_PROFILE.md) |

The [architecture guide](docs/ARCHITECTURE.md) explains module boundaries and data
flows. The [capability catalog](docs/IMPLEMENTATION_STATUS.md) records implemented
behavior. The [function reference](docs/CONTRACT_FUNCTIONS.md) and
[operator manual](docs/OPERATOR_MANUAL.md#operator-call-tables) cover callable
inputs, outputs, permissions and management procedures.

## Liquidity and economic rights

- Contributions use **native ETH or one fixed ZZZ**, with default activation/growth
  minima of $100/$5. Placement follows the existing range's current ratio; independent
  prices verify value and actual marginal deployed LP. New funds do not recenter
  the shared LP or reset its rebalance clock.
- Actual harvested LP revenue is **80% individual / 10% equal activated collective /
  5% permanent compounding / 5% ZZZ buyback-burn**. Claims do not execute compound
  or buyback. Funded reserves, principal, royalties and mint proceeds stay separate.
- Royalties distribute actual received admitted currencies with Commun×1, Rare×2
  and Legendary×3 weights. They remain original-currency rights. The initial
  royalty cohort opens one hour after the configured mint end; LP rewards are separate.
- One contribution pool is active at a time. A logical bucket can hold one main
  and optionally one residual, both Vault-owned. The default60%/40% bounds apply
  when replacing a portfolio; they are not a continuously maintained allocation.
- Governance-triggered collective exit returns actual ETH+ZZZ by NFT shares in
  bounded owner payouts. NFTs remain transferable with old rewards and future
  royalties; LP cannot reopen after terminal exit begins.

See [economics](docs/ECONOMICS.md), [exact LP allocation](docs/EXACT_LP_ALLOCATION.md),
[royalties](docs/ROYALTY_SETTLEMENT.md) and [holder return](docs/HOLDER_COLLECTIVE_EXIT.md).

## Governance and maintenance

One human operator controls the selected governance wallet. Governance acts
directly without a timelock; the keeper and pause-only guardian have separate,
revocable permissions. Sealing fixes implementations and token/parent identities;
supported configuration remains adaptable within its controls. An explicitly
paused governance emergency may waive selected financial checks and accept severe
loss. It is separate from normal keeper automation.

Ordinary upkeep uses the configured85%-of-centre-to-boundary trigger,
independent same-side confirmation, a10-minute sampled window with a strict
five-minute maximum gap, four-minute source checks and a fresh1–5-minute jitter
after the hard12-hour minimum. Hourly harvesting remains independent. Compounding
has its own interval and the selected software waiting policy.

The keeper defaults to dry run, recovers saved transactions before new work and
never automatically resends an uncertain transaction. Use the
[operator manual](docs/OPERATOR_MANUAL.md), [keeper safeguards](docs/KEEPER_SAFEGUARDS.md),
[recovery guide](docs/KEEPER_RECOVERY.md) and [backup procedure](docs/KEEPER_BACKUP.md).

## Release and operating boundaries

The trusted normal Solidity build remains `activation-final-six-20261118`
(payload6/allocation2, accounting7, custody5, mint2/canonicalV10). Older profiles,
codecs, journals, checkpoints and served websites retain their original identities.

Final production-pool selection is deferred. The supplied native ETH/ZZZ pool
remains an isolated test target, including explicitly synthetic liquidity;
it is not a production selection or independent-depth proof.

An optional [complete-wallet read profile2](docs/OPERATOR_MANUAL.md#optional-profile2-separate-complete-wallet-earnings)
separates ownership/LP pages from whole-wallet earnings slices:80 core reads
instead of1,071 for1,000 NFTs and65–66 descriptors. Exact per-NFT rights, the full
24-hour history and existing limits remain; actual provider/F6/site adoption is
still unqualified. No public signing or running-site change is implied.

The selected non-live contribution profile is32M gas/full20% padding;
maintenance is24M/full25%, and claims12M/full20%. Qualification is workload-specific.
Real prices/routes, complete provider fees/capacity, maximum states, authorities,
custom OpenSea/VRF/content, current consumers, operating recovery and independent
audit/remediation remain open. See [current findings](docs/AUDIT_FINDINGS.md) and
the [release checklist](docs/RELEASE_CHECKLIST.md).

Source publication does not deploy, seal, update services/sites or reset chains.
Recorded popldemo simulation, poplint integration and local Anvil environments are
distinct. Browser signing remains Anvil-only; the desktop monitor stays paused.

## Development and records

Use the [supported development environment](docs/DEVELOPMENT.md):

```bash
bash scripts/install-deps.sh
bash scripts/verify.sh
python3 scripts/sync-project-todo.py --check
```

Solidity is pinned to0.8.26/Cancun and the reviewed normal optimizer profile.
Run meaningful affected checks; do not relax size, gas, resource or financial
guards to obtain a pass. Historical test counts do not qualify later source.

[Documentation map](docs/README.md) · [Todo maintenance](docs/TODO_WORKFLOW.md) ·
[current report](reports/CURRENT_REVIEW.md) · [findings](docs/AUDIT_FINDINGS.md)

Retired narratives are preserved at the
[pre-consolidation revision](https://github.com/ABEF/AAA/tree/fdd599c7698d0e1c0709a4a8b50130e5557ba508).
Required structured evidence remains source-bound; the current report explains
how to retrieve complete historical packages without treating them as current guidance.
