# Creator-funded LP rewards

The creator can send payments directly to an immutable per-bucket `ZZZRewardReceiver`. This is an undeployed intake candidate, not a deployed receiver or guaranteed payment agreement. NFT-sale royalties use a different receiver and allocation; see [NFT metadata](NFT_METADATA.md).

## Payment and allocation

After sealing and activating a canonical bucket, governance creates its receiver through the timelock. One receiver permanently binds each bucket and its original admitted pair; at most16are registered. No redirection/replacement/admin sweep exists.

Plain pair-ERC20 payments are accepted. Optionally, nativeETH is wrapped exactly one-for-one using a reviewed admitted18decimal pair wrapper. Anyone or the constrained keeper may sync receipts. Only actual processed funds enter80/10/5/5:80%pool-share owner,10%equal activated-NFT collective,5%permanent compounding,5%buyback/burn.

Twenty raw units split16/2/1/1; smaller receipts carry. Before membership changes or departure, remaining dust goes to incumbent owners. A$1,000 illustration allocates$800/$100/$50/$50. An NFT with20%of its bucket shares receives$160of the owner portion; the$100collective part is divided equally among all activated canonical NFTs, independent of rarity/LP size.

The current NFT owner claims funded ERC20 rewards, including WETH for wrappednative receipts. Unclaimed balances follow transfers. Dormant NFTs have no LP shares or collective membership. No Power score exists. `totalExternalFunded` measures actual processed external funds, not all Pons revenue, a creator promise or the website's hypothetical TVL-share calculation.

## Entry timing and remote custody

Funding uses processing-time shares/membership. A payment delivered after entry may benefit the entrant even if the creator earned it earlier. The protocol does not reconstruct historical swap entitlement or promise a creator percentage.

Before activation or top-up, the vault syncs all registered inboxes and settles old dust. It repeats settlement after entry balancing and final LP updates. Late compounding belongs to incumbent NAV. A95%deployed check, final pending/dust barrier and old-owner checkpoint precede new shares and first collective/royalty membership. Failed guards roll back atomically. Old idle/compound funds cannot meet an entrant's$100marginal deployed minimum.

Canonical processing/claims continue during pause or while LP custody is away. Home receipts do not discharge authenticated remote counters; their compounding reserve awaits compatible maintenance after return. Strategy pauses still stop maintenance, bridging and buybacks.

## Admission and production limits

Only admitted exact-transfer, non-rebasing tokens and exactwrappers are supported. Constructor prefunds/unsupportedassets cannot be rescued. Without a wrapper ordinaryETHreceipt reverts, while forcedETH is excluded. Anyone may donate accepted funds; receipt does not authenticate creator identity.

The19raw-unit dust exception must be economically valued for every token. An admitted token/wrapper outage can block global synchronization and new entries. The16receiver bound limits loops but does not eliminate availability risk. Inventory receiver code, immutable getters, currencies, wrapper behavior and actual staging in schema4production configuration.

The selected Robinhood native-ETH/Pons-hook LP remains unsupported by the LP adapter. Its0%corefee does not imply hook revenue entitlement. Payment intake never supplies native/hook custody support, production transport, approved valuation or an independent audit.
