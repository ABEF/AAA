# NFT traits, royalties and live artwork

The development candidate caps minting at**1,000 NFTs** with **600 Commun / 300 Rare / 100 Legendary**. The six existing colors produce72 artwork states (6×3×4), not72 minted identities. Expanded solid/bicolor/tricolor art remains design work; token supply and artwork count are separate.

## Random reveal

Before sealing, governance configures a VRF-v2.5-compatible coordinator, key, funded subscription, confirmations, callback gas and payment currency exactly once. There is no coordinator replacement or trait setter. Production must verify actual proof-verifying code and availability on the selected chain; the matching ABI and mock tests are not proof of a working oracle.

Mint records its ordinal and one request for two words. The authenticated callback only stores words. Anyone may finalize the next mint ordinal, drawing a rarity from the remaining quotas and a color from six palettes. This prevents fulfillment ordering from changing allocation. The first rarity odds are60/30/10; later odds depend on remaining quotas. No reroll or cancellation exists. An unavailable earlier request blocks later finalization, so subscription backing, callback gas and fulfillment recovery need explicit operational review. Activation requires revealed traits.

Traits remain bound to the NFT through transfers, additions and migration. Unrevealed NFTs return an embedded placeholder. Metadata uses the preconfigured artwork root and current rarity/color/evolution. The root can only be populated once before sealing; it is not a post-seal governance image switch.

## Current LP value and ERC-4906

`currentLPValue` returns availability and current 18-decimal oracle-USD marked principal/idle/compound NAV proportional to NFT shares. It does not include unclaimed rewards, arbitrary donations or historical contribution USD. Enhanced starts at$1,000 and Singularity at$10,000; losses may downgrade artwork. An activated NFT below$100 remains activated.

Remote/in-flight custody, stale feeds or unavailable dependencies return valuation unavailable and explicitly labelled Activated fallback art. They never fabricate live remote prices. Claims and migration do not require metadata/oracle evaluation. ERC-4906 events accompany reveal/contribution, and anyone can emit a refresh notification after market moves. Indexer/marketplace refresh is still required; a view change alone does not push updates to external caches.

## Separate marketplace royalties

`royaltyInfo` requests5% of sale value, payable entirely to the immutable `ZZZRoyaltyRewards` helper. ERC-2981 reports a royalty request; it does not enforce payment. All actually received eligible funds are distributed to activated Commun/Rare/Legendary at1/2/3, regardless of LP size/evolution. Dormant NFTs get zero weight. LP owner/collective rewards remain a separate ledger.

Native ETH is admitted automatically. Reviewed ERC20 assets can be appended through NFT governance; prefunds at admission are quarantined. Pending receipts are checkpointed before a new NFT joins, preserving incumbent rights. Zero-eligibility and constructor prefunds stay orphaned. Current owners claim, and unclaimed funds follow transfers. No admin rescue or redirected claim exists. Read [economic rules](ECONOMICS.md) for dust, token admission and liveness boundaries.

Primary references: [ERC-2981](https://eips.ethereum.org/EIPS/eip-2981), [ERC-4906](https://eips.ethereum.org/EIPS/eip-4906), [Chainlink VRF security](https://docs.chain.link/vrf/v2-5/security), [VRF request ABI](https://docs.chain.link/vrf/v2-5/subscription/get-a-random-number). Actual coordinator/network review remains open.
