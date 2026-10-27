# Component boundaries and current status

This map describes the undeployed [accounting4/custody3/canonical V5](POSITION_V4.md)
source, not installed contracts or service qualification. Production is **NOT
APPROVED**. Use [features/evidence](IMPLEMENTATION_STATUS.md) for scoped checks,
the [sole Todo](../TODO.md) for work and the [operator manual](OPERATOR_MANUAL.md)
for action procedures. Historical codecs and report bytes retain their scope.

## Ownership, entry and custody

| Component | Current job | Remaining qualification |
| --- | --- | --- |
| [AccessController](../src/ZZZAccessController.sol) | Direct governance2, keeper/guardian permissions,16 sealed module bindings, two-step wallet handover and irreversible `lpExitStarted`. | Actual authorities, recovery, configuration/code trust and operating acceptance. |
| [Vault](../src/ZZZVault.sol) | Direct0.05ETH dormant mint, source-bound$100 activation/$5 growth, shared LP/per-NFT shares and exact principal settlement to fixed Migration. New principal work ends permanently at exit. | Actual venue behavior, accounting/callback composition, maximal gas and independent review. |
| [ActivationAssets](../src/ZZZActivationAssets.sol) | One pre-seal fixed ZZZ plus native ETH, source-policy review and dependency-independent disabling. | Actual token/proxy/runtime/decimals and independent feed evidence. |
| [PoolRegistry](../src/ZZZPoolRegistry.sol) | One contribution pool, pinned static hookless native ETH/fixedZZZ LP admission and supported fee-tier replacements. Generic ERC20 LP admission is removed. | Actual initialized pools, venue bindings, execution depth and deposit/operation controls. |
| [ActivationEntry](../src/ZZZActivationEntry.sol) | Current owner, exact Vault call, captured source USD/caller loss maximum, typed routes, exact approvals and callback-safe context. | Actual input/conversion funding, browser wallet and target-chain execution. |
| [LiquidityManager](../src/ZZZLiquidityManager.sol) | Typed v4 mint/increase/collect/close/swap, actual key/ticks/liquidity and exact native settlement; isolates prefunds. | Actual dependencies, adverse composition, strategy costs and maximal gas. |
| [ContributionPricing](../src/ZZZContributionPricing.sol) | Captures dual-source prices/policy before funds move and measures actual marginal LP. | Actual independent source policies and real routes/depth. |
| [MigrationBudget](../src/ZZZMigrationBudget.sol) | Captured contribution/maintenance floors, physical placement, idle accounting and loss checks. Dead external-custody helpers are removed. | Independent economic review and installed-venue gas/behavior. |

Position4 has eight fields: poolId,lpTokenId,idle0,idle1,depositUSD,centerX96,
lastRebalance,status. Statuses None0/Active1/reservedOutbound2/Dormant3/Parked4/
Exited5 are explicit; old profiles keep old meanings. At most four historical/
reserved buckets are permanently admitted. Many NFTs share one physical LP;
maintenance is per bucket, not per1,000 NFTs.

## Income, claims and upkeep

| Component | Current job | Remaining qualification |
| --- | --- | --- |
| [FeeController](../src/ZZZFeeController.sol) | Actual LP receipts only, fixed80/10/5/5 and separate compound/buyback/dust classification. | Currency rounding, actual collection and independent accounting review. |
| [Rewards](../src/ZZZRewards.sol) | Share-weighted individual plus equal activated collective indices/fractions and current-owner claims. | Actual recipients, complete history and worst-case currency gas. |
| [Membership](../src/ZZZMembership.sol) | One equal collective share per activated NFT, preserved through transfer/LP exit so past entitlements survive. | Bounded dust/checkpoint costs and complete handoff composition. |
| [LPRewardConverter](../src/ZZZLPRewardConverter.sol) | Converts only earned balances into the same NFTs' ETH credits, without new-income double counting. | Cheaper qualified ZZZ route at default1%, latency, gas and operation. |
| [RoyaltyRewards](../src/ZZZRoyaltyRewards.sol) | Separate actual-receipt1/2/3 rarity ledger, optional-currency outage cohorts and current-owner claims; future royalties continue after LP exit. No custody drain. | Actual marketplace currencies/receipts and failure/recovery behavior. |
| [RoyaltyConverter](../src/ZZZRoyaltyConverter.sol) | Guarded batch conversion preserving original NFT entitlements; wrappers only in explicit routes. | Routes/feed/wrapper and keeper operating qualification. |
| [ClaimRouter](../src/ZZZClaimRouter.sol) | Up to32 mixed ledger claims, actual owner and atomic rollback. Principal return is a separate Migration payout. | Gas, frontend chunking and real receiver acceptance. |
| [Oracle](../src/ZZZOracle.sol) | Two-source USD bounds, freshness/fingerprint and3% disagreement; reviewed sequencer policy. | Independent sources, proxies/common-mode/uptime and provider support. |
| [Optional Pyth source](../src/ZZZPythPriceFeed.sol) | Immutable bounded price/time/confidence reader, no funds/updater. | Actual Core/source/provider and updater review. |
| [Strategy](../src/ZZZStrategy.sol),[Compounder](../src/ZZZCompounder.sol) | Trigger/cooldown/range and attributed reinvestment before exit; optional reviewed +/-25/50% width policy. | Volatility, MEV, gas and real strategy operations. |
| [Buyback](../src/ZZZBuyback.sol) | Spend only buyback reserve, acquire fixed ZZZ, verify actual supply burn; governed operating ceiling. | Actual conversion/burn, price policy and funded operation. |

Defaults contribution2%/conversion1%/maintenance3%, maxima10%, gas separate.
Stronger caller/venue guards remain. Raw holder principal return has no aggregate
USD-loss promise. Source currency stays source currency until actually converted.

## NFT, holder return and replacement

| Component | Current job | Remaining qualification |
| --- | --- | --- |
| [NFT](../src/ZZZNFT.sol) | ERC721/2981/4906,1,000 cap, exact quota/inventory draw, immutable traits and ownership. | Actual VRF and compatible OpenSea primary mint. |
| [NFTMetadata](../src/ZZZNFTMetadata.sol) | Current LP NAV selects four visual stages; unavailable data stays explicit. Exited LP has verifiedzero and terminal `LP exited` stage4 using existing artwork. | Permanent hosting, feed/cache refresh and current-profile display. |
| [Factories](../src/ZZZRoyaltyFactory.sol),[Assets factory](../src/ZZZActivationAssetsFactory.sol) | Fixed helper creation and parent/controller bindings. | Exact deployed release inventory and bytecode. |
| [Migration](../src/ZZZMigration.sol),[parking validation](../src/ZZZCustodyValidation.sol) | Before exit, same-pair moves/reversible parking. Governance then irrevocably closes LP, allocates every actual ETH/ZZZ unit by shares and pushes bounded payouts to current owners, with isolated failure/owner fallback. | Maximal allocation/receiver gas, accounting4 services/UI and actual operating/independent review. No custodian/bridge/return ingress. |
| [CanonicalHandoff](../src/ZZZCanonicalHandoff.sol) | Six-domain same-chain capture/import/backing, funded abort and atomic source retirement/replacement activation, only before LP exit. | Exact V5 compatible peers, escrow cutover, funding/interruption/gas and independent review. |
| [NFTCanonical](../src/ZZZNFTCanonical.sol),[VaultCanonical](../src/ZZZVaultCanonical.sol),[FeesCanonical](../src/ZZZFeesCanonical.sol) | Sealed typed codecs for ownership, shares, ledgers/fractions and classified backing. V5 group rows retain12words. | Actual source/successor manifest and complete operated rehearsal. |

Rarity affects royalties only; color/pattern affect neither ledger. Exited NFTs
retain transfers, earned rewards and future royalty rights; unpaid principal
follows current ownership until permanently marked paid. Current V5 canonical
replacement cannot run after exit starts because its importer does not carry
terminal payout accounting. No integrated bridge, remote ledger or post-halt
recovery is provided. [Exit details](HOLDER_COLLECTIVE_EXIT.md).

## Services and evidence

Keeper scheduling, simulation, nonce/receipt recovery and monitoring are off-chain;
contracts enforce principal rules. Indexer/API use confirmed state, explicit
profiles and complete pinned history. Missing pricing/history stays unavailable.
The new source profile requires explicit accounting4 readers; served accounting3 poplint
and old local deployments are not relabelled or upgraded. Public deployment stays
null, browser signing Anvil-only, popldemo unchanged.

Actual feeds/routes/VRF/authorities, OpenSea, artwork hosting, accounting4 wallet/
service acceptance, target gas/strategy/operations and independent audit remain
open. Earlier [reports](../reports/README.md) do not verify later source changes.
Maintain the [callable reference](CONTRACT_FUNCTIONS.md) for ABI/permission changes.
