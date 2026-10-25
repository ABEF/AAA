**Current policy, 2026-10-25:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and

## Late receipts after retirement

`RoyaltyRewards.forwardLate(asset)` forwards only an asset already admitted by
the retired source ledger, to its fixed immediate successor. Once retired,
governance cannot add a previously unknown currency there. An arbitrary new
ERC20 sent to an old receiver is therefore outside the implemented recovery
support. Existing admitted ETH/ERC20 late receipts retain their original path.

Before a handoff, inventory actual marketplace currencies/old signed orders and
cached receiver addresses; admit/qualify intended currencies before receipt or
retirement, and update supported marketplace configuration. Do not infer a
universal settlement-currency ban from collection pricing preferences.
An extension for bounded forwarding of genuinely unadmitted currencies to the
fixed successor would require explicit policy, quarantine/backing/security and
size review before sealing; an arbitrary operator sweep is not equivalent.
The current release retains its admitted-only behavior. See [rights audit](../reports/full-audit-20261025/RIGHTS.md).
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Marketplace royalty settlement

Decision and research record, 2026-10-19. Implementation and qualification status
belongs to the [central task](../TODO.md#task-royalty-eth-settlement).

## Accepted direction

Price PoPL secondary sales in ETH on OpenSea, and initially qualify native ETH
and the exact Robinhood WETH wrapper for royalties. Holders should be able to
receive royalties in ETH. Stablecoin conversion is conditional: if USDC/USDG
royalties cannot be excluded from the supported marketplace settlement flows,
enable the implemented guarded conversion after qualification. Do not admit arbitrary currencies or assume
a ticker identifies a reviewed token. Activation inputs remain a separate policy;
current activation/growth accepts only native ETH or the fixed deployment ZZZ.
USDC/USDG/WETH remain separately reviewed royalty/conversion currencies, not user contribution inputs.

Rarity and its multiplier are fixed at reveal before activation. Activation adds
LP and enables the existing Commun/Rare/Legendary royalty weight of 1/2/3. The
holder makes no separate royalty payment or registration transaction. Royalties
come from marketplace sales when paid, not from the activation contribution.
The 5% creator-royalty request, 100% eligible royalty distribution and separate
80/10/5/5 LP allocation are unchanged. OpenSea's own platform fee is not PoPL revenue.

## What OpenSea documents

[Collection pricing](https://docs.opensea.io/reference/set_collection_pricing_currency)
allows an owner or authorized editor to select ETH instead of the Robinhood USDG
default. Repricing is asynchronous. This documents a pricing choice; it does not
prove a universal stablecoin ban across offers, old signed orders, other venues
or direct transfers. No collection-specific setting or transaction was tested.

[Checkout](https://support.opensea.io/en/articles/10827963-how-can-i-purchase-on-a-different-blockchain-using-opensea)
can use other currencies and chains. The buyer's source currency is not proof of
the currency reaching the royalty receiver. Check the actual settlement order
and on-chain transfers. A stablecoin-funded checkout that settles royalties in
ETH needs no additional stablecoin conversion inside PoPL.

[OpenSea's offer documentation](https://docs.opensea.io/docs/collection-offers-and-advanced-trading)
uses WETH and documents unwrapping. Qualify the actual Robinhood flows and wrapper;
an Ethereum example does not identify a Robinhood deployment. Under
[ERC-2981](https://eips.ethereum.org/EIPS/eip-2981), royalties use the sale-price
currency. There is no verified OpenSea setting here that automatically converts
every creator royalty into ETH. All sources above were read on 2026-10-19.

## Implemented conversion and outage boundary

[RoyaltyRewards](../src/ZZZRoyaltyRewards.sol) preserves each NFT's original-currency
balance. An authorized keeper selects **1-32 distinct, sorted NFT IDs** and calls
`convertBatch(asset,ids,routeId,minimumETH,deadline)`. The ledger synchronizes
pending receipts, checkpoints those NFTs and aggregates only their earned whole
units. One swap/unwrap returns ETH to the ledger. That ETH is credited directly
to the same NFTs in proportion to the exact amounts converted, not today's
rarity-membership denominator. Cumulative rounding assigns every received wei;
source fractions and index dust stay backed in the source currency. Quarantined
prefunds and other NFTs' balances are never included. Larger inventories use
multiple bounded batches rather than a transaction iterating all 1,000 holders.

The separately deployed [RoyaltyConverter](../src/ZZZRoyaltyConverter.sol) is bound
once through `RoyaltyRewards.bindConverter(address)` **before sealing**. It has
fixed controller, ledger and WETH addresses, no arbitrary recipient/call/rescue,
and no access to LP principal. Governance can update reviewed wrapper policies,
append routes, and disable/re-enable conversion or routes after sealing. Existing
immediate-governance trust applies; there is no new timelock or override role.
The converter is optional to the generic core seal check; a release promising
ETH conversion must independently verify its pre-seal binding and configuration.
An imported successor needs its own reviewed converter binding.

Native ETH needs no conversion. WETH unwrapping must return exactly 1:1 in ETH.
An admitted stablecoin uses a pinned, typed, single-hop SwapRouter02 route to
WETH, followed by exact unwrap. At execution, the current protocol Oracle quote
sets a **99% minimum**, rounded up, and the caller's stronger minimum also applies.
Zero prices, stale feeds, bad routes, expired deadlines, transfer taxes, mismatched
outputs or changed pins reject atomically. The deadline may be at most ten minutes
away. Router approvals are exact and reset. **The 1% execution-loss cap is separate
from network gas**, which the keeper pays; no gas is deducted from holder balances.

`RoyaltyConverted` records source and ETH amounts per NFT; it is not a payout and
must not increment lifetime claimed totals. Actual native `Claimed` events do.
Direct original-currency claims remain available as a fallback, and the existing
mixed ClaimRouter can claim credited ETH alongside LP fees. A raw claim racing
conversion either consumes that NFT's balance first or causes the prepared batch
minimum to reject; no double claim is possible through the same ledger guard.
NFT transfers carry both unconverted and converted balances. No claim is paid to
the keeper or the former owner merely because they prepared a batch.

### Optional currency outage

The user approved this recovery rule on 2026-10-19. Healthy currencies settle
before activation joins. Each optional ERC20 synchronization runs behind a
250,000-gas self-call boundary with bounded failure-data handling. Failed balance
reads, negative-balance accounting or token execution do not undo LP activation;
the NFT's fixed rarity weight becomes active globally and for healthy currencies.
`eligibleFor(id,asset)` reports eligibility for the particular currency.

The failed currency retains its earlier eligible cohort. On the first successful
sync, **all previously unseen receipts go to that earlier cohort** (or quarantine
if it was empty). Waiting NFTs join only subsequent receipts. This deliberately
excludes newcomers from receipts arriving during the outage as well as before it:
without readable receipts the contract cannot distinguish the arrival times.
There is no retroactive catch-up or operator-selected allocation. Bounded cohort
intervals and lazy index checkpoints avoid looping over all waiting NFTs.

`RoyaltyAssetDeferred` and `RoyaltyEligibilityRecovered` expose the transition.
Native ETH uses no external token balance read. Genuine overall transaction gas
shortage still reverts; the caller must fund enough gas to run each isolated check.
Broken payout tokens can still prevent their own claims or canonical handoff,
which requires exact readable backing. Healthy single-currency claims continue.

Canonical settlement enrolls all recovered cohorts and exports flattened per-NFT
index baselines in the existing row format. Converted ETH and remaining source
currency are separate classified backing. Import/abort/late-forwarding keep the
existing lifecycle rules; converter configuration is not economic state imported
from the source. Future-chain transport remains a separate unimplemented gate.

## Operator procedure

For collection pricing, the authorized marketplace owner/editor can request:

```text
POST /api/v2/collections/{slug}/pricing_currency
{"use_stablecoin": false}
```

Verify account/chain/collection/slug, follow asynchronous completion, and inspect
actual royalty transfers for listings, offers, old orders and checkouts. Set the
creator recipient to `NFT.royaltyInfo` / `NFT.royaltyRewards()`, not a manager wallet.
This request does not cancel signatures or enforce a universal currency ban.

Before sealing:

1. Independently review exact WETH/token/router/factory/pool/feed addresses and
   runtime pins. Do not use an Ethereum address on Robinhood by analogy.
2. Deploy the converter with the current controller, royalty ledger and wrapper;
   governance calls `RoyaltyRewards.bindConverter(converter)` once. Verify both
   directions and record code hashes. This guide does not execute a deployment.
3. `configureWrapper(WrapperPolicy)` pins wrapper runtime and, for the Robinhood
   proxy, its reviewed admin, implementation, owner and code hashes. Direct-code
   mode (zero admin) is only for a reviewed non-proxy wrapper; it cannot prove that
   a supplied token is not an upgradeable proxy. Review remains essential.
4. Admit required currencies through `NFT.addRoyaltyAsset(token)`, then append
   stablecoin `addRoute(RoutePolicy)` records. Identity commits to all route data;
   mutable source/router implementations still need independent review/monitoring.
5. Call converter `setEnabled(true)` after policy validation. A WETH batch uses
   zero route ID; stablecoin batches use a reviewed enabled route. ETH is excluded.

### Automatic processing

The existing [keeper](../keeper/monitor.py) has an opt-in
[royalty worker](../keeper/royalties.py). It is disabled in the example config.
Add reviewed `royalties`, `royalty_converter`, `royalty_nft`, `royalty_wrapper`
and `oracle` addresses to `contracts` with their `code_hashes`, then configure:

```json
"royalty_conversion": {
  "enabled": true,
  "max_nfts_per_cycle": 32,
  "max_gas_to_output_bps": 100,
  "assets": [{
    "asset": "<reviewed ERC20 address>",
    "route_id": "<reviewed route ID; zero bytes32 for WETH>",
    "minimum_source_units": "<positive raw-unit batch threshold>",
    "minimum_output_wei": "<positive ETH-value threshold>"
  }]
}
```

These are placeholders, not a live configuration. Thresholds are operator choices;
avoid uneconomic tiny swaps. `max_gas_to_output_bps` limits estimated operator gas
relative to ETH output (default 1%); it is additional to the on-chain 1% execution
cap. Existing absolute transaction/daily gas budgets also apply. The worker checks
bindings/runtime hashes at a confirmed canonical hash, scans at most 32 NFTs and
one currency per cycle, alternates priority with other work, estimates gas and
simulates exact calldata through the existing serial pending/nonce path. Currency
rotation and per-NFT on-chain balances make retry/restart idempotent. No server is
started or upgraded by enabling source support.

Changing the configured contract inventory requires the existing reviewed keeper
state reconciliation and backup procedure; **never reset nonce/spending/pending
state**. First use dry run, then qualify signer/RPC/fee policy and logs on the target
network. No new private-key storage, external notification or monitor is added.

### Stop, recover and verify

- Governance `converter.setEnabled(false)` or `setRouteEnabled(id,false)` reads no
  failing venue/token and stops new conversions. Global pause or migration
  preparation also stops conversion; claims retain their own lifecycle rules.
- Correct/review the dependency, configure a new reviewed policy/route if needed,
  and re-enable with full validation. Already converted amounts cannot be reversed.
- Failed conversions atomically retain original balances. Retry from fresh state,
  not an old assumed balance/price. `sync(asset)` recovers currency eligibility;
  the worker can submit this when a waiting cohort has no convertible batch.
- Check per-NFT conversion events, native claimable balances, source liabilities,
  native liabilities, zero approvals, receipts and separately charged keeper gas.
  `royalty_conversion_deferred`, `royalty_conversion_uneconomic`, the existing
  cooldown and pending-recovery logs distinguish a skipped batch from a payment.
- Unsupported currency receipts are not rescued, admitted or converted silently.
  Direct currency claims remain available when their token is healthy. If ETH
  payment to an owning smart contract fails, ownership/payout compatibility still
  needs resolution; operators cannot redirect another holder's funds.

## Qualification boundary

Read [scoped verification and internal review](../reports/royalty-conversion/VERIFICATION.md).
The [backend reporting extension](ROYALTY_REPORTING.md) now exposes per-currency
eligibility, explicit unavailable balances and separately indexed conversion
credits, including complete configured same-chain predecessors. Only actual
claims increase lifetime paid totals. Its local checks do not qualify a live API
or consumer. No real route, wrapper, OpenSea settlement, live keeper, website
integration or public transaction has been qualified by local mocks. Final runtime
inventory, outage/recovery UI, target gas and independent audit remain in the
[central task](../TODO.md#task-royalty-eth-settlement).
