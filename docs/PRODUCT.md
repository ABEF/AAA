# PoPL product specification

This undeployed contract candidate implements the product rules accepted on 2026-10-15. The separate website remains a simulation rather than evidence of deployment.

## Lifecycle and rights

The collection has a hard cap of **1,000 NFTs**. A dormant mint costs **0.05 ETH**, forwarded to an immutable deployment-selected recipient independently of LP principal and rewards. Minting creates no liquidity or reward membership.

The NFT's current owner can activate it with at least **$100 in gross contribution value**, deploying **at least 99% as marginal new LP**. Conversion fees, slippage and undeployed input share one 1% execution budget; network gas is separate. Existing idle capital, pre-existing LP and compounding budgets cannot subsidize a new entrant. Later additions use the same execution limit and buy shares at current NAV. Principal has no holder or administrator redemption path.

One physical LP bucket serves NFTs in each approved pool/strategy. Owner LP fees follow that NFT's nonredeemable bucket shares. Collective rewards are equal per activated canonical NFT, including while its custody is remote or in flight. Top-ups do not create extra collective memberships. No Power score exists.

The current NFT owner claims funded rewards, including unclaimed balances from before transfer. Transfers carry economic rights and never withdraw principal. Approved ERC-721 operators do not acquire direct reward-claim rights.

## Revenue and rarity

Measured collected LP fees and processed creator funding split **80% owner / 10% collective / 5% compounding / 5% buyback-burn**. Only actual funding creates reward liabilities. No external creator percentage or guaranteed return is assumed.

NFT-sale royalties use an independent ledger. Marketplaces are asked for **5%** through ERC-2981; **100% of received eligible royalties** is reserved for holders. Activated Commun/Rare/Legendary have weights **1/2/3**. Dormant NFTs have zero weight; rarity has no effect on LP fees or equal collective membership. Funds received before anyone is eligible are quarantined, not awarded retroactively.

Verifiable random draws without replacement allocate exactly **600 Commun, 300 Rare and 100 Legendary** after the full 1,000 reveals. The initial 60/30/10 odds change with remaining quotas. Callbacks store words, and finalization follows mint order. No reroll, cancellation or owner-selected traits exists. A pending earlier fulfillment blocks later reveal and activation.

Rarity, palette and circuit pattern remain fixed. Eight base colors form 58 monochrome/bicolor/tricolor palettes, combined with four circuit patterns and four evolution states. The finite 1,000-entry visual inventory contains 200 monochrome, 500 bicolor and 300 tricolor NFTs, each style maintaining the 60/30/10 rarity composition. An identical palette/pattern/rarity appears at most four times; Legendary finished artwork has no duplicates. These visual traits have no economic weight. Evolution follows current attached LP market value: Activated after initial activation, Enhanced from $1,000, Singularity from $10,000; market losses can lower the visual state. Activation and royalty membership remain permanent. Unavailable remote/oracle valuation is explicitly labelled rather than invented. [Metadata details](NFT_METADATA.md).

## Custody and integration boundary

Timelocked governance may approve new immutable routes/provider policies after sealing. Whole-bucket LP can close, cross an approved transport, reopen and migrate again while canonical NFT shares/membership stay unchanged. Routes support reviewed equivalent assets, not arbitrary conversion or moving the NFT to another chain. Satellite holder top-ups remain unsupported.

The selected Robinhood ZZZ/native-ETH Pons market has a strictly pinned native-settlement development adapter, with WETH accounting while the actual native PoolKey is preserved. It requires production qualification. Target inputs are **USDC, USDG, ETH and ZZZ**. The immutable [Entry](ACTIVATION_ENTRY.md) now binds original-source value through exact native wrapping or an admitted typed single-hop conversion into the Vault; all legs share the 1% budget. Actual routes/feeds remain unqualified, and USDC has no verified usable route yet. Website buttons do not establish these live integrations.

[Paused custody parking](CUSTODY_PARKING.md) lets timelocked governance close LP into the Vault under an exact snapshot and raw-token minimums, independently of price feeds or the creator inbox. It preserves shares and reward rights without a withdrawal or redemption. Resume requires ordinary fresh-price deployment checks; parked migration keeps approved-route and historical-funding barriers. Actual external asset/venue/bridge failure can still prevent movement. A reviewed VRF service, safe pricing, authorities, staging, audit/remediation and later real bridge transport remain required.
