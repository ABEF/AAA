# NFT traits, royalties and live artwork

The development candidate caps minting at **1,000 NFTs** with **600 Commun / 300 Rare / 100 Legendary**. Eight base colors form 58 palettes and four circuit patterns. The renderer supports 2,784 SVG artwork states (58×4×3×4), separate from minted identities. The earlier six-color/72-PNG library remains historical artwork.

## Fixed visual inventory

The base colors are Cyan, Blue, Violet, Emerald, Amber (yellow), Crimson (red), Ivory and Onyx. Bicolor palettes require at least one Ivory, Amber, Crimson or Onyx. A tricolor palette is an allowed pair plus a distinct Amber, Crimson or Onyx. Palette ordering is canonical; swapping color order does not create another palette. This produces eight monochrome, 22 bicolor and 28 tricolor palettes.

The immutable 1,000-entry inventory contains 200 monochrome, 500 bicolor and 300 tricolor entries. Each style separately has 60% Commun / 30% Rare / 10% Legendary. Remainders are balanced across its palettes. Four purely visual circuit patterns are flowing arcs, segmented panels, orbital rings and vertical ribs. An identical palette/pattern/rarity appears at most four times; Legendary finished looks have no duplicates. The 1,000 entries use 542 distinct finished base looks. Evolution is a state of that same artwork, not an additional minted NFT. Every palette and every pattern is represented across all three rarities.

`design/nft-metadata/palette-system-v1/inventory.json` defines the finite entries. `packed-catalog.json` filters those entries by rarity and packs each as palette-index×4 + pattern-index. `scripts/generate-artwork-library.py --check` verifies the generated immutable `ZZZArtwork` source. The preview's deterministic seed fixes catalogue contents and illustrative token order; it never supplies production mint randomness or lets an owner choose a mint's traits.

## Random reveal

Before sealing, governance configures a VRF-v2.5-compatible coordinator, key, funded subscription, confirmations, callback gas and payment currency exactly once. There is no coordinator replacement or trait setter. Production must verify actual proof-verifying code and availability on the selected chain; the matching ABI and mock tests are not proof of a working oracle.

Mint records its ordinal and one request for two words. The authenticated callback only stores words. Anyone may finalize the next mint ordinal. The first word draws a rarity from the remaining quotas; the second independently selects one remaining entry from that rarity's fixed visual inventory, using a sparse Fisher-Yates draw without replacement. Consuming an entry swaps the final remaining index into its place. Neither callback ordering nor token ownership selects an entry. The first rarity odds are 60/30/10; later odds depend on remaining quotas. Color-style and palette odds likewise follow their remaining finite inventories, rather than promising fixed independent odds throughout a sellout. No reroll or cancellation exists. An unavailable earlier request blocks later finalization, so subscription backing, callback gas and fulfillment recovery need explicit operational review. Activation requires revealed traits.

Traits remain bound to the NFT through transfers, additions and migration. `paletteOf` and `patternOf` identify the immutable visual entry; the compatibility getter `colorOf` reports its first canonical color. Metadata publishes Color style, Palette, Color 1/2/3 as applicable, Circuit pattern, Rarity, Evolution and current NFT-sale royalty weight. Unrevealed NFTs return an embedded placeholder. Revealed SVG filenames are `palette-pattern-rarity-evolution.svg`, such as `cyan-amber-onyx-arcs-rare-enhanced.svg`. The root can only be populated once before sealing; it is not a post-seal governance image switch. Production admission requires the entire supported 2,784-path publication with independent content-root/manifest review. No SVG publication, website preview or local VRF mock establishes deployment readiness.

## Current LP value and ERC-4906

`currentLPValue` returns availability and current 18-decimal oracle-USD marked principal/idle/compound NAV proportional to NFT shares. It does not include unclaimed rewards, arbitrary donations or historical contribution USD. Enhanced starts at$1,000 and Singularity at$10,000; losses may downgrade artwork. An activated NFT below$100 remains activated.

Remote/in-flight custody, stale feeds or unavailable dependencies return valuation unavailable and explicitly labelled Activated fallback art. They never fabricate live remote prices. Claims and migration do not require metadata/oracle evaluation. ERC-4906 events accompany reveal/contribution. Anyone can notify one token with `refreshMetadata(id)` or up to 50 inclusive mint ordinals with `refreshMetadataRange(firstOrdinal,lastOrdinal)`. Ordinals are not token IDs: the bounded call emits one `MetadataUpdate` per actual hashed ID, without reading prices or modifying custody.

The optional keeper watcher observes confirmed-block evolution, valuation availability and reveal state and uses the existing simulated/budgeted serial transaction path. It defaults to disabled, validates the canonical deployment and live runtime pins, and separates observations from confirmed notifications. This is a separate NFT scan; LP rebalancing still operates once per shared pool. See [operating details](OPERATIONS.md#optional-metadata-notifications) and [current verification](../reports/release-hardening/README.md). Immutable artwork publication and actual marketplace cache integration remain release gates: a changed view or emitted event does not guarantee an instant external refresh.

## Separate marketplace royalties

`royaltyInfo` requests5% of sale value, payable entirely to the immutable `ZZZRoyaltyRewards` helper. ERC-2981 reports a royalty request; it does not enforce payment. All actually received eligible funds are distributed to activated Commun/Rare/Legendary at1/2/3, regardless of LP size/evolution. Dormant NFTs get zero weight. LP owner/collective rewards remain a separate ledger.

Native ETH is admitted automatically. Reviewed ERC20 assets can be appended through NFT governance; prefunds at admission are quarantined. Pending receipts are checkpointed before a new NFT joins, preserving incumbent rights. Zero-eligibility and constructor prefunds stay orphaned. Current owners claim, and unclaimed funds follow transfers. No admin rescue or redirected claim exists. Read [economic rules](ECONOMICS.md) for dust, token admission and liveness boundaries.

Primary references: [ERC-2981](https://eips.ethereum.org/EIPS/eip-2981), [ERC-4906](https://eips.ethereum.org/EIPS/eip-4906), [Chainlink VRF security](https://docs.chain.link/vrf/v2-5/security), [VRF request ABI](https://docs.chain.link/vrf/v2-5/subscription/get-a-random-number). Actual coordinator/network review remains open.

## Current marked value guard

The renderer now checks the strategy's exit-price freshness/deviation guard before
marking actual current LP amounts. Operations-disabled pools may retain honest
valuation. Divergent spot/stale or unavailable dependencies return an unavailable
mark; ownership, activated royalty eligibility and claims persist. See
[dynamic liquidity](DYNAMIC_LIQUIDITY.md) and its scoped verification.

## Operator reveal-drain policy

See [the operator manual](OPERATOR_MANUAL.md#mint-and-metadata). Qualify/fund and
monitor the original randomness service; for planned collection replacement stop
new mints through the supported lifecycle control and finalize all existing draws.
No request carry, reroll, admin trait choice or post-seal coordinator switch exists.
The confirmed mint-readiness endpoint is an observation, not provider/recovery
qualification. A permanently unanswered request remains a replacement blocker.

Governance can pause new draws with `NFT.setMintPaused(true)` while the original
coordinator fulfills existing requests and ordered finalization continues.
Resume with `false` after provider checks; other lifecycle/global controls still
apply. The switch does not select, cancel or reroll traits. See the
[operator procedure](OPERATOR_MANUAL.md#mint-and-metadata) and
[scoped control verification](../reports/operator-controls/VERIFICATION.md).
