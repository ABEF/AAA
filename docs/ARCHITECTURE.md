# Shared permanent-liquidity architecture

## Identity and custody

`mintDormant()` costs exactly 0.05 ETH and issues a canonical ERC-721 without LP, shares, Power or fee entitlement. Payment goes immediately to the immutable constructor-selected recipient. A failed safe mint or payment rolls back issuance. Only the canonical chain can mint; current owners alone can activate or add permanently locked liquidity.

Each pool/strategy has one **bucket** and one physical Uniswap LP NFT, regardless of the number of economic NFTs. Bucket identity is `uint256(keccak256(abi.encode(homeChain,homeVault,initialPoolId)))`; NFT identity separately uses the mint sequence. The association `nftBucket(nftId)` and internal `sharesOf(nftId)` remain on the canonical chain. Shares are nonredeemable, cannot be detached from the NFT, and have no ERC-20 representation. `bucketTotalShares`, `homePoolId`, `group(bucketId)`, `bucketCount` and `bucketAt` expose custody. `nftStatus(nftId)` exposes NFT lifecycle independently. The former `position(nftId)` ABI is removed: physical LP fields must be read once from `group(bucketId)`. Read `nftBucket`, `sharesOf` and `contributionUSD` for NFT rights, and compute associated NAV from the bucket share fraction. Never sum a shared LP once per NFT.

`poolBucket(poolId)` permanently reserves a venue for its bucket, including while custody is remote. Governance must timelock `reservePool(poolId,bucketId)` on a new destination before route use. First canonical activation can initialize an unreserved or correctly pre-reserved canonical pool. Different buckets cannot merge or occupy the same venue; one pool cannot silently acquire multiple physical positions. A same-chain pool move preserves bucket identity and reserves the new venue, while old reservations remain. Activate against the bucket's current local pool. Satellite holder deposits and partial per-NFT migrations are unsupported.

## Activation, top-ups and share pricing

Activation requires at least $500 of **new marginal deployed LP**, with a conservative subtraction of all incumbent idle assets and freshly harvested compounding value. A large existing position cannot meet a small entrant's minimum. Pool contribution minimums and maximum lifetime contribution per NFT still apply. Top-ups add to the same bucket. After placement no more than 5% of measured principal NAV may remain attributed idle. This is an execution-time check, not an assurance that a concentrated range stays productive.

Before membership increases, the vault harvests prior fees, settles sub-ten-unit fee dust to existing owners, and pulls the old designated compounding reserves into attributed principal. It balances the deposit against the existing LP range, then harvests entry-swap fees before increasing liquidity. These fees belong to incumbent shares. Fresh 10% compounding value joins incumbent NAV. The old LP is revalued **after** the balancing swap so existing concentrated-LP quantity/price changes stay with incumbents. Net new principal is post-placement NAV minus that incumbent NAV; execution losses charged to entry must satisfy the configured input-value slippage bound.

First shares equal 18-decimal net principal USD. Later issuance is `floor(totalShares * netNewUSD / incumbentNAV)`. Positive existing supply with zero NAV, zero new shares, total supply above 1e36 and invalid minimum-liquidity/deadline values revert atomically. Donations to token balances are not attributed principal. Unclaimed rewards and buyback reserves never enter NAV. Shares checkpoint before increase; Power separately checkpoints before lifetime oracle-valued user contributions increase. Compounding and appreciation add NAV but never Power.

## Funded fees and NFT ownership

Only separately measured collection deltas enter fees. Each ten raw token units allocate 50% to the pool owner index, 30% to the global Power index, 10% to bucket compounding and 10% to buyback/burn. Less than ten units carry until the next collection; before membership changes or departure they settle to incumbent owner rewards. This documented bounded rounding exception prevents future members receiving old dust.

Owner indexes are keyed by bucket/token; individual checkpoints and retained fractions are keyed by NFT/token. Collective indexes remain token-wide and use lifetime contribution Power. At most 32 append-only reward assets bound every checkpoint loop. Funded liabilities reserve rounding remnants; neither those remnants nor zero-Power orphan funds have an admin sweep. Transferring an NFT changes its current claimant without changing shares, Power or earned rights. Claims remain available when maintenance is paused.

The 30% collective policy uses Power at collection or remote funding time, rather than historical per-swap weights. Contributions to other buckets and delayed settlement can affect that allocation. These economic choices still require external review and production approval.

## Pool-level maintenance

`collectFees(bucketId,deadline)`, keeper `rebalance(bucketId,minLiquidity,deadline)` and the compounder operate once per pool. There is no loop through NFT holders. Rebalancing validates trigger, cooldown, oracle/spot deviation, ticks, short deadline, slippage and minimum minted liquidity. It harvests, pulls designated compounding, closes the shared LP, balances and recreates one LP atomically. Compounding increases the existing range and preserves its LP ID, with a second collection after a same-pool balancing swap.

The keeper discovers bounded pages through `bucketCount/bucketAt`, checks actual local pool currencies and custody, and persists a fair scan cursor together with pending-transaction state. Operation count depends on pools/strategies and scheduled work, not NFT count. Batching does not remove swap costs, market impact, impermanent loss or MEV. Backtesting and actual operating costs remain release work.

## Whole-bucket migration and remote fees

Source custody is `Active -> Outbound -> Remote`; destination is `None/Remote -> Inbound -> Active`. NFT ownership, shares and Power remain home. Governance approves immutable equivalent-asset routes through its timelock and schedules a whole-bucket plan with an additional two-day delay. Scheduling freezes new membership; cancellation restores it. The source validates readiness before releasing attributed principal, and incoming exact-funded messages authenticate provenance and strictly newer custody epochs. No timeout unlock or principal refund exists.

Version-3 economic messages replace per-NFT identity with bucket identity, homePoolId, totalShares and four cumulative remote allocation counters. Version-2 messages are rejected. Final departure snapshots include fees collected during release. Source-completion and canonical-location ACKs retain that immutable snapshot, require the correct source/destination and ordered canonical history, and cannot regress location. Repeated A->B->C->A->B hops preserve one canonical share ledger without NFT reminting or Power inflation. Foreign revisits can carry larger canonical membership after a completed return and new contributions.

Remote owner/collective allocations remain segregated funded reserves, including unsent amounts and final dust. Lifetime counters are propagated with principal in canonical-token order across every hop. Home tracks exactly funded received counters. On return, **new shares and a new outbound release remain blocked until all authenticated prior allocations are funded home**. Transfers, funded claims and maintenance still work. Lost or delayed reward transport can therefore delay new contributions; no authority bypass discards liabilities. Historical reward routes and old provider policies can settle after principal leaves or outbound sending is disabled. Collective rewards retain funding-time Power semantics.

Before source approval, review and reserve every destination, token equivalence, decimals, code/upgrade authorities, physical bridge wrapper, finality, funding and all ACK/reward return paths. Cross-chain source contracts cannot independently inspect remote reservation or code. Timelock notice is a governance trust boundary, not proof of safe arbitrary future code. See [bridge onboarding](BRIDGE_ONBOARDING.md).

## Market and release boundaries

The fixed adapter supports conventional ERC-20 pairs, hookless Uniswap v4 static-fee pools and WETH instead of native ETH. The selected Robinhood native-ETH/ZZZ Pons pool has zero core LP fees; liquidity ownership does not establish hook-revenue rights. Its native/hook settlement and the deferred revenue agreement/new-pool choice remain unsupported. See [verified market](ROBINHOOD_POOL.md).

The 17-module graph is non-upgradeable after sealing. Governance retains bounded timelocked configuration and route/provider onboarding; guardian pauses maintenance; keepers execute constrained upkeep. There is no owner/admin principal redemption, arbitrary execution, token rescue or proxy upgrade. Independent audit, staged real provider/keeper operation, valuation policy, production authorities and reward-market integration are still required before funded deployment. Historical per-NFT architecture and test sources remain under reports/history; their passing logs do not validate this shared rewrite.
