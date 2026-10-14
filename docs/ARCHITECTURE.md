# Accounting, lifecycle and contract boundaries

## Identity

The NFT identifier is derived from the canonical chain ID, vault address and a monotonic deposit sequence. Vault records persist while underlying LP token IDs change. The canonical-chain constructor guard prevents satellite issuance. A satellite vault holds the same economic identifier but never mints another ZZZ NFT for it.

One economic NFT has one active Uniswap LP NFT. This preserves direct fee attribution but is not gas-optimal for a large collection. An aggregated-share vault would be a different accounting design, not a drop-in optimization.

## Deposits and increases

The vault validates a registered conventional ERC20 pair, oracle-valued contribution limits, a positive minimum-liquidity bound and a short deadline. Exact token transfers are recorded as idle principal. The strategy balances the composition, price/value-loss checks apply, and the liquidity manager supplies the position. Unused funds remain attributed and non-redeemable; they are not refunded to holders.

After each LP placement, measured position principal plus attributed idle value must satisfy the 95% deployment threshold. This prevents a mostly idle deposit from receiving a large contribution-based Power score. It does not guarantee the price range stays active.

Mint/top-up transactions revert atomically if any step fails. A top-up harvests the existing position's fees before Power changes and after any balancing swap. Initial gross contribution USD value is the explicit Power basis; fees/market movement do not continually rebase Power.

## Fee accounting

Collection uses a dedicated zero-liquidity decrease and a fixed vault recipient. The vault measures its token balance increments, then allocates only those increments. Rebalancing principal is a separate flow.

For each fee asset, pending dust is added to newly received fees. Each ten raw units allocate five individual units, three collective units, one compounding unit and one buyback unit. Remainder below ten is retained. On source migration, final dust is paid to the originating NFT rather than silently bridged as principal.

On the canonical chain, the 80% NFT portion is transferred into funded rewards accounting. On a satellite, it is reserved by NFT/token until an authenticated reward message is sent home. It is not split again on arrival. The satellite retains its 10% compound and 10% buyback reserves.

Global collective indexes use fixed-point arithmetic with retained per-NFT fractions. Before adding Power, the old weight checkpoints every registered reward asset. Index rounding dust and zero-Power orphan reserves are not administrator-withdrawable.

**Settlement timing:** Power at collection/delivery governs the collective allocation. This is not a reconstruction of historical per-swap weights. Delayed harvesting, delayed bridging, temporary capital increases and permanent historical Power can affect economic fairness. That policy is an open product/economic review item.

## Rebalancing and compounding

The keeper polls off chain. The contracts require eligible state, a cooldown, an oracle-relative trigger, valid tick spacing and price limits. The new target is an outward-rounded range around a validated reference, not blindly around a manipulable spot.

A rebalance harvests fees, consumes only the designated compounding reserve, closes the old LP, balances assets, enforces an oracle-value loss bound, creates the new LP and updates its reference atomically. Compounding instead targets the existing range and retains its LP ID.

Swaps only use registered pools and fixed caller recipients. Exact-input settlement must consume the expected input and deliver at least the on-chain minimum output. A same-pool swap can itself earn fees on an existing position, so a second harvest precedes an increase.

The initial deposit range defaults only through configuration; choose `rangeBps=1000`, `triggerBps=300`, `minRebalanceInterval=600` as an illustrative policy, not universally optimal settings. All execution/gas costs, market impact and MEV exposure require empirical validation.

## Migration state machine

Source: `Active -> Outbound -> Remote`.

Destination: `None -> Inbound -> Active`.

Governance first proposes a frozen route. After the additional migration delay, a keeper requests source release. The source harvests, collects its compound reserves, closes the LP and releases only attributed principal to the migration coordinator. The coordinator sends a typed, nonce-bearing message through the bound transport adapter.

Destination receipt and LP activation are separate. A failed/reverting pool deployment does not authorize an admin refund; already accepted tokens remain in destination vault custody. After activation, an acknowledgement updates the canonical location. Repeated acknowledgements are idempotent; replayed bridge delivery nonces are rejected.

Remote reward routes, reverse acknowledgements and the two token identities must be configured before sealing on both chains. Amounts use identical token decimals and nominal units; a real transport must implement the actual token equivalence, finality and retry semantics. No arbitrary timeout recovery is safe without provider-authenticated cancellation evidence.

No onward migration, return migration, satellite user deposits or cross-chain top-ups are implemented. The permanently fixed route design is intentionally narrower than a general multichain asset manager.

## Buybacks

Only the 10% buyback reserve can be consumed. The executor swaps an approved direct pair into the configured ZZZ token, or directly burns already-collected ZZZ. It verifies its exact acquired balance and a corresponding token-supply decrease.

This does not establish cross-chain/global supply reduction for arbitrary wrapped ZZZ implementations. Multi-hop routing and fee-token conversion for assets without a direct ZZZ market remain out of scope. Those assets must not be promised working automated buybacks until a reviewed route exists.
