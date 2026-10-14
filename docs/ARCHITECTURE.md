# Accounting, lifecycle and contract boundaries

## Identity

The NFT identifier is derived from the canonical chain ID, vault address and a monotonic mint sequence. `mintDormant()` creates the canonical vault record and NFT before any LP is supplied. Activation and later LP replacements preserve that identifier. The canonical-chain guard prevents satellite issuance. A satellite vault holds the same economic identifier but never mints another ZZZ NFT for it.

A dormant economic NFT has no Uniswap LP NFT. An active economic NFT has one active Uniswap LP NFT. This preserves direct fee attribution for supported pools but is not gas-optimal for a large collection. An aggregated-share vault would be a different accounting design, not a drop-in optimization.

## Paid dormant mint, activation and increases

`mintDormant()` is payable and canonical-chain-only. `msg.value` must equal the constant `MINT_PRICE = 0.05 ether`; overpayment and underpayment revert. It records `Dormant`, issues the NFT, and forwards the payment to `mintProceedsRecipient`, an immutable constructor argument that must be nonzero and different from the vault. There is no LP creation, token contribution, or Power update. Mint proceeds never enter attributed idle principal, compounding, or collected-fee accounting. Issuance and payout form one atomic transaction: a failure reverts the NFT, record, sequence increment, and payment.

`activate(id, ...)` is available only to the current owner of a home-chain dormant NFT. Approved operators cannot activate for that owner. It uses the existing identifier, changes the position to `Active` only as part of an atomic successful placement, and does not issue a second NFT. A failed activation leaves the already paid dormant NFT intact.

For activation and increases, the vault validates a registered conventional ERC20 pair, oracle-valued contribution limits, a positive minimum-liquidity bound and a short deadline. Exact token transfers are recorded as idle principal. The strategy balances the composition, price/value-loss checks apply, and the liquidity manager supplies the position. Unused funds remain attributed and non-redeemable; they are not refunded to holders.

Activation requires both an eligible gross contribution and at least `MIN_ACTIVATION_LP_USD = 500e18` in measured, oracle-valued deployed LP after balancing and placement. Attributed idle assets do not satisfy this $500 LP minimum. The pool's configured contribution minimum and position maximum still apply. The threshold is checked at activation; it is not a promise that later market value stays above $500.

After each LP placement, measured position principal plus attributed idle value must satisfy the 95% deployment threshold. This prevents a mostly idle deposit from receiving a large contribution-based Power score. It does not guarantee the price range stays active.

Activation/top-up transactions revert atomically if any step fails. A top-up harvests the existing position's fees before Power changes and after any balancing swap. Initial gross contribution USD value is the explicit Power basis; the 0.05 ETH mint payment is excluded, and fees/market movement do not continually rebase Power. Neither activation nor a top-up adds a redemption path for principal.

## Requested Robinhood pool boundary

The requested pool contains native ETH, ZZZ, and `PonsV2MemeHook`; its core LP fee is zero. The current registry and adapter accept only conventional ERC20/ERC20, hookless static-fee pools, so this target cannot be registered as a supported pool merely by entering its ID. Native settlement and hook behavior require a separately designed integration.

The hook's trading fee goes to the launch's configured recipients rather than to external LP positions pro rata. The source of rewards for the PoPL project is undecided, and the current fee-collection path must not be described as a working integration with this pool. See [on-chain PoolKey and fee policy](ROBINHOOD_POOL.md).

## Fee accounting

Collection uses a dedicated zero-liquidity decrease and a fixed vault recipient. The vault measures its token balance increments, then allocates only those increments. Rebalancing principal is a separate flow.

For each fee asset, pending dust is added to newly received fees. Each ten raw units allocate five individual units, three collective units, one compounding unit and one buyback unit. Remainder below ten is retained. On source migration, final canonical dust is credited to the originating NFT. At a satellite, it joins that NFT's funded remote-individual reserve until delivery home; it is not silently bridged as principal or credited to satellite rewards.

On the canonical chain, the 80% NFT portion is transferred into funded rewards accounting. On a satellite, it is reserved by NFT/token until an authenticated reward message is sent home. It is not split again on arrival. The satellite retains its 10% compound and 10% buyback reserves.

The fee controller binds each remote NFT/local-token pair to an immutable canonical token identity. Imports establish this mapping in principal-route order; first remote allocation can bind an unbound asset. Conflicting mappings revert. Existing remote budgets use the persisted mapping rather than recomputing it from a later pool, and can be delivered while the old position is `Active`, `Outbound`, `Remote`, or `Inbound`. Canonical historical reward paths remain authorized after custody leaves a satellite, so funded old reserves can drain independently of later principal hops.

Global collective indexes use fixed-point arithmetic with retained per-NFT fractions. Before adding Power, the old weight checkpoints every registered reward asset. Index rounding dust and zero-Power orphan reserves are not administrator-withdrawable.

**Settlement timing:** Power at collection/delivery governs the collective allocation. This is not a reconstruction of historical per-swap weights. Delayed harvesting, delayed bridging, temporary capital increases and permanent historical Power can affect economic fairness. That policy is an open product/economic review item.

## Rebalancing and compounding

The keeper polls off chain. The contracts require eligible state, a cooldown, an oracle-relative trigger, valid tick spacing and price limits. The new target is an outward-rounded range around a validated reference, not blindly around a manipulable spot.

A rebalance harvests fees, consumes only the designated compounding reserve, closes the old LP, balances assets, enforces an oracle-value loss bound, creates the new LP and updates its reference atomically. Compounding instead targets the existing range and retains its LP ID.

Swaps only use registered pools and fixed caller recipients. Exact-input settlement must consume the expected input and deliver at least the on-chain minimum output. A same-pool swap can itself earn fees on an existing position, so a second harvest precedes an increase.

The initial deposit range defaults only through configuration; choose `rangeBps=1000`, `triggerBps=300`, `minRebalanceInterval=600` as an illustrative policy, not universally optimal settings. All execution/gas costs, market impact and MEV exposure require empirical validation.

## Migration state machine

Source: `Active -> Outbound -> Remote`.

First destination visit: `None -> Inbound -> Active`.

Revisit or canonical return: fully drained `Remote -> Inbound -> Active`.

Governance proposes an approved append-only route, freezing the position, canonical identity, asset mappings, and next custody epoch into the plan. After the additional **two-day migration delay**, a keeper requests source release. Changed position identity invalidates the proposal. The source harvests, collects its compound reserves, closes the LP and releases only attributed principal to the migration coordinator. The coordinator sends a version-2, nonce-bearing message through the bound transport adapter.

Version 2 carries the migration epoch, principal route ID, previous chain/vault/receiver, canonical home identity, contribution value, and canonical tokens in principal-route source order. The authenticated incoming route must match the previous custodian. The receiver records migration provenance before vault import and atomically retains the full accepted message. Destination-pool ordering may reverse the token pair; canonical mappings are reordered with it. Imports preserve the economic NFT and contribution value, with no NFT issuance or Power addition.

Destination receipt and LP activation remain separate. A failed/reverting pool deployment does not authorize an admin refund; accepted tokens remain attributed in vault custody for retry. A previously visited satellite accepts only a strictly newer custody epoch and a fully drained old record. It can skip global epochs for hops that did not visit it.

### Source completion and canonical location

After activation, `acknowledge(migrationId, reverseRouteId)` sends a `SourceCompletion` ACK to the immediately previous custodian. It completes that source plan and releases the source's migration state to `Remote`. If that source is the canonical home, the ACK also records the home location; a separate first-hop home notification is unnecessary.

For an onward satellite hop, `acknowledgeHome(migrationId, homeRouteId)` sends a separate `CanonicalLocation` ACK to the canonical vault/receiver. Both ACKs use the immutable accepted snapshot, not the NFT's potentially newer vault position. Canonical location updates require exactly the next global epoch and the recorded previous location. An out-of-order notification reverts until earlier hops have been recorded and must be retried. An exact historical ACK is idempotent and cannot regress location.

A return to the canonical vault records the next home location atomically during principal import, using canonical NFT identity and ordered location history. It does not require a fake self-chain bridge ACK. The destination still sends source completion to the satellite it left. Existing legacy remote reward paths remain available for funded old budgets.

### Future route onboarding and its trust boundary

Module bindings and the adapter's transport endpoint remain fixed after sealing. The registry can add new route identities through timelocked governance after sealing, and can disable/re-enable existing routes without editing their contents. The canonical registry may also approve remote-only graph edges, such as satellite B to C, so it can authenticate onward location updates. A route ID is the hash of the full route; onboarding a new route is not modification of an old route or a general proxy upgrade.

Principal, source-completion ACK, canonical-location ACK, and reward routes must be reviewed and present on the participating chains before using a new hop. Supported assets must be economically equivalent, with identical decimals and nominal units. Migration does not convert unrelated assets or move the NFT to another chain. Satellite user deposits and cross-chain holder top-ups are still unsupported.

Review destination runtime code and its custody authorities, token/proxy behavior, provider token equivalence, finality, funding, and retry semantics for every added route. The timelock gives governance notice; it cannot prove that arbitrary future destination code or a bridge preserves principal forever. A separately reviewed production `IZZZTransport` is not bundled. No arbitrary timeout recovery is safe without provider-authenticated cancellation evidence. Current validation evidence is recorded in [the implementation update](../reports/IMPLEMENTATION_UPDATE.md); it is not funded-deployment approval.

## Buybacks

Only the 10% buyback reserve can be consumed. The executor swaps an approved direct pair into the configured ZZZ token, or directly burns already-collected ZZZ. It verifies its exact acquired balance and a corresponding token-supply decrease.

This does not establish cross-chain/global supply reduction for arbitrary wrapped ZZZ implementations. Multi-hop routing and fee-token conversion for assets without a direct ZZZ market remain out of scope. Those assets must not be promised working automated buybacks until a reviewed route exists.
