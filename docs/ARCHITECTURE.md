# Shared permanent-liquidity architecture

The initial collection is intended to use one shared pool, not one pool per NFT. Optional additional strategies use separate buckets. `ZZZVault.MAX_BUCKETS = 4` limits all historical bucket registrations on a vault, including imports; returning an existing bucket or migrating it to another reviewed pool does not allocate a new bucket. This bounds combined funded-dust and inbox settlement before new membership. The prior 16-bucket limit failed the combined distinct-asset/inbox workload; four retains local headroom without changing reward accounting or the 1,000-NFT cap. Actual Entry, venue, token and target-chain gas still require staging verification.

Pool reservations now permanently admit a bucket into the same four-slot set.
Aliases and returns reuse their slot; reserved None-state entries have no
principal or shares and are skipped by maintenance. Local admission does not
prove remote capacity or provider backing. See [evolution and trust boundaries](ARCHITECTURE_EVOLUTION.md)
and [current targeted evidence](../reports/architecture-evolution/VERIFICATION.md).

Current undeployed candidate: 1,000 NFTs; exact 600/300/100 random rarities; 0.05 ETH dormant mint; $100 original gross source activation with at least 99% marginal LP and gas separate; 80/10/5/5 LP allocation; equal activated collective membership; separate 5% marketplace royalties. See the [feature and evidence reference](IMPLEMENTATION_STATUS.md).

Earlier [release-hardening evidence](../reports/release-hardening/README.md) records bounded metadata notifications and the source-specific metadata checks; it predates native custody, atomic Entry and parking. [Historical integration receipts](../reports/gap-hardening/README.md) retain their own source, compiler, test and review scope. The current capacity change has separate [targeted evidence](../reports/architecture-evolution/VERIFICATION.md). Historical CI remains scoped to its exact published revision. These checks do not establish production integration or an independent audit.

## Identity and custody

Only the canonical chain issues NFTs. Minting forwards the charge separately, requests verifiable randomness and creates a dormant ERC-721 with no LP or rewards. Mint and payment/request failures roll back atomically. The NFT enforces the1,000cap and excludes royalty/mint-receiver collisions. Before canonical sealing, the randomness configuration must exist; actual provider availability remains a deployment gate.

Each approved pool/strategy has one bucket and one physical LP NFT. Bucket identity is keccak(homeChain,homeVault,initialPoolId); each economic NFT has its own canonical identity, bucket association and nonredeemable shares. `group(bucketId)` exposes custody; `nftBucket`, `sharesOf`, `contributionUSD` expose NFT rights/history. Never sum one physical LP once per NFT. `contributionUSD` is not a current valuation or reward weight.

`poolBucket` permanently reserves venues for their buckets. New destinations must be reserved through governance before route approval. Distinct buckets do not merge. NFT transfers change the current claimant without changing shares, membership, rarity or accrued balances. Operators cannot claim as owners; there is no principal redemption.

## Entry and membership

Activation requires revealed traits and at least $100 original gross source value, with at least 99% actually deployed as marginal oracle-valued LP, excluding incumbent idle/compound value. The immutable Registry-created [Entry](ACTIVATION_ENTRY.md) accepts admitted direct pair assets, exact native wrapping for the selected native pool, or reviewed typed single-hop V3 conversion into one accounting currency. It binds current ownership, exact Vault calldata and original measured source USD through a callback-safe context. Separate conversion and LP legs cannot each consume a new 1% allowance. Actual routes, liquidity and feeds need qualification; arbitrary calldata/conversion is not supported. The same NFT may receive permanent additions at current share NAV, with the same aggregate bound. After placement no more than 5% measured principal NAV may remain idle. Pool limits, fresh valuation, minimum liquidity and deadline guards remain.

Before share/membership changes, the vault harvests earlier fees and synchronizes all bounded registered creator inboxes. Sub-twenty-unit dust settles to existing owner shares. Entry swaps are followed by settlement so their fees belong to incumbents; old LP is revalued after balancing. Fresh5%compounding belongs to incumbent NAV. Final LP updates, late receipts,95%deployment and pending/dust guards precede owner checkpoint and share issuance.

First shares equal measured net principal USD; later shares round down as `supply * netNewUSD / incumbentNAV`. Zero-NAV/zero-share/cap violations revert. Donations, unclaimed rewards and buyback reserves do not buy shares. After successful issuance the vault activates one `ZZZMembership` share for an initially dormant NFT and notifies the fixed NFT, which joins its separate rarity royalty ledger. All failures roll back entry atomically. A top-up never adds collective/royalty weight.

## Funded LP rewards

Twenty raw units split16owner/2collective/1compound/1buyback. Owner indexes are pool/token-specific and use nonredeemable shares. Collective indexes are token-wide and give each activated canonical NFT one equal share. Eligibility persists through price declines, transfers and migration. Before the one-time membership is enabled, all published indexes are checkpointed. No Power module or USD reward weighting remains.

At most32 admitted LP reward assets bound checkpoint loops. Fractions carry per NFT; global division dust stays reserved. Smaller receipts carry and the maximum19raw-unit membership dust exception requires asset-specific economic review. No administrator can withdraw reward, orphan, compound or principal balances outside their constrained purpose. Claims remain available during operational pause.

Creator payments enter dedicated immutable per-bucket receivers. Actual processed funding uses the same allocation. At most four receivers are reachable under the current Vault capacity, and they are globally settled before entry; the factory retains a separate defensive ceiling of 16. Receipt timing uses processing-time weights, without a promised creator percentage or retrospective entitlement. Home external funding never pays authenticated remote obligations. [External rewards](EXTERNAL_REWARDS.md).

## NFT royalties and metadata

The NFT owns immutable royalty/metadata helpers. ERC-2981 requests5%sale royalties payable directly to the separate receiver;100%of eligible receipts is reserved for activated rarity weights1/2/3. NativeETH and up to16reviewed ERC20assets use funded indexes, pre-join pending synchronization and current-owner claims. There is no LP split or admin withdrawal in this ledger. Pre-admission/constructor/zero-eligibility funds are quarantined.

VRF callbacks only store request-bound words. Permissionless reveal follows mint order, drawing without replacement to exact 600/300/100 quotas. A separate word draws a fixed artwork entry without replacement within that rarity. Eight base colors form 58 palettes, combined with four patterns: Flowing arcs, Segmented panels, Orbital rings and Vertical ribs. Rarity, palette and pattern remain immutable, and visual traits never change reward weights. The 1,000-entry inventory has 200 monochrome, 500 bicolor and 300 tricolor slots, each with the 60/30/10 rarity mix; identical palette/pattern/rarity finishes occur at most four times and all 100 Legendary looks are unique. Missing earlier fulfillment blocks later reveal; no reroll/cancellation bypass exists. [NFT details](NFT_METADATA.md).

The renderer selects among 2,784 supported palette/pattern/rarity/evolution SVG states, separate from the NFT supply. It values current home-chain LP amounts, attributed idle and compound budgets using approved oracles, multiplied by shares/supply. Enhanced starts at $1,000 and Singularity at $10,000; market losses can downgrade artwork. Remote/in-flight/stale valuation is explicitly unavailable, with labelled fallback art. Metadata never gates claims/migration. Reveal/contributions emit ERC-4906 notifications. Permissionless per-token and bounded ordinal-range calls notify actual hashed IDs without price reads. An optional confirmed-block watcher uses the existing keeper's serial budgeted transaction path; permanent content publication, staged watcher operation and marketplace cache integration remain production work.

## Maintenance and migration

Keeper collect/rebalance/compound operations run once per bucket, with no NFT-holder loop. They retain trigger, cooldown, oracle/spot, range, swap, minimum-liquidity and deadline guards. Pooling does not remove impermanent loss, swap costs or MEV; real strategy/gas economics remain unapproved.

Source custody follows Active -> Outbound -> Remote and destination custody None/Remote -> Inbound -> Active. Canonical NFT shares and memberships stay home. Governance approves immutable equivalent-asset routes through a timelock; principal movement adds a two-day delay. New membership/share entry freezes while scheduled/away. No timeout principal refund exists.

Version3messages preserve bucket identity, provenance, share supply and cumulative owner/collective counters. Frozen source-completion and canonical-location acknowledgements authenticate ordered custody epochs. Repeated hops/returns never remint NFTs or add membership. Satellites deliver their already allocated90%reward portion without a second split. Historical paths and asset bindings remain usable after principal leaves.

After return, new shares and another outbound principal release remain blocked until all authenticated earlier owner/collective allocations are funded home. Transfers, claims and permitted maintenance remain available. A delayed/failed transport can delay contributions; there is no authority bypass discarding liabilities.

[Parking](CUSTODY_PARKING.md) appends custody status 6 without changing old enum values. While globally paused, a timelocked Migration request binds exact custody/shares/LP, nonce, epoch, ordered currencies and raw principal-close minimums. Vault harvests venue fees separately, closes into attributed idle and keeps all principal. This path omits source USD and creator-inbox reads; ordinary active exits retain their checks. Keeper maintenance stops while Parked, but funded LP/royalty claims, NFT transfers and eligibility persist. Resume uses the same ordered pair and fresh ordinary deployment guards. Parked migration can depart without restoring the old source price, while route readiness, exact transfers, delays, legacy funding and destination checks remain mandatory.

## Release and trust boundaries

The17sealed modules include Membership replacing Power; NFT royalty/metadata and per-bucket creator inboxes are helpers. Sealing fixes core bindings. Governance retains constrained timelocked route/provider/configuration powers, guardians pause operations and keepers execute bounded upkeep. Timelock notice cannot prove arbitrary future destinations preserve principal.

The LP adapter supports conventional hookless static-fee ERC20 Uniswap v4 pools and the strictly pinned selected Robinhood native/Pons market, using WETH accounting with the real native PoolKey preserved. Other native/hooks remain rejected. Production native admission, actual routes, real bridge SDK/backing, supported proof-verifying VRF, pricing and authorities remain unqualified. Creator intake is separate from hook revenue entitlement. An independent audit, live staging, bytecode/gas review and remediation are required before real funds.
