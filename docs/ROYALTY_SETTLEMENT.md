# Marketplace royalty settlement

Decision and research record, 2026-10-19. Implementation and qualification status
belongs to the [central task](../TODO.md#task-royalty-eth-settlement).

## Accepted direction

Price PoPL secondary sales in ETH on OpenSea, and initially qualify native ETH
and the exact Robinhood WETH wrapper for royalties. Holders should be able to
receive royalties in ETH. Stablecoin conversion is conditional: if USDC/USDG
royalties cannot be excluded from the supported marketplace settlement flows,
implement guarded conversion to ETH. Do not admit arbitrary currencies or assume
a ticker identifies a reviewed token. Activation inputs remain a separate policy;
this decision does not remove USDC/USDG from the intended activation inputs.

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

## Current implementation boundary

[NFT.royaltyInfo](../src/ZZZNFT.sol) points at the fixed
[RoyaltyRewards ledger](../src/ZZZRoyaltyRewards.sol). Native ETH is admitted by
default; governance can append up to 16 ERC20 currencies with
`NFT.addRoyaltyAsset(token)`. Claims pay the admitted currency directly. There is
no automatic WETH unwrap or stablecoin-to-ETH converter. Admission does not
restrict the payment currency a marketplace or peer-to-peer seller can use.

The Vault issues LP shares before `NFT.notifyContribution` calls
`RoyaltyRewards.activate`. All are in one atomic transaction. Activation syncs
existing receipts before adding the new weight, so an admitted ERC20 balance-read
failure can roll back activation. Native ETH has no external ERC20 balance read.
Zero royalties are valid and do not prevent activation. Existing healthy-currency
claims are separate from `syncAll`.

The desired failure boundary remains: royalty processing must not undo successful
LP activation or award older royalties to a newcomer. Moving the check later in
the same transaction, catching an error without correct accounting, or adding a
converter does not by itself establish that boundary. Per-currency delayed
eligibility was discussed but not approved; do not implement it as a settled
product rule. Define and review receipt/eligibility cutoffs before changing the ledger.

## Operator procedure and implementation constraints

After an actual collection exists and the authorized marketplace account is
available, use OpenSea's collection-pricing operation:

```text
POST /api/v2/collections/{slug}/pricing_currency
{"use_stablecoin": false}
```

Verify the account, chain, collection contract and slug first. Follow the reported
repricing job to completion; a successful request alone is not settlement proof.
Inspect new listings, accepted item/collection offers, existing orders and
supported cross-chain checkouts. Record exact recipient/currency/amount from
transactions, including the 5% creator payment when included. Configure the
creator recipient from `NFT.royaltyInfo` / `NFT.royaltyRewards()`, never a manager's
wallet. API credentials remain outside the repository.

Do not assume this operation cancels old signatures or bans stablecoin transfers.
Changing pricing back is another authorized marketplace operation, not a reversal
of completed sales. Any proposed currency expansion requires fresh qualification.

The planned ETH payout path retains ETH, unwraps only a verified WETH deployment
with exact accounting, and swaps stablecoins only if required by the settlement
findings. Stablecoin conversion needs reviewed routes, price/minimum-output and
deadline protections, bounded approvals, measured received ETH and separate gas
accounting. No swap-loss parameter has been selected for royalties; the activation
1% and maintenance 3% limits are not automatically royalty-conversion budgets.

Automation must preserve which NFTs earned pending funds, NFT ownership changes,
all liabilities and fractional balances. Delayed conversion cannot distribute
old funds using a newer membership set. Failed conversion must retain the funds
and its accounting for retry, without a sweep, invented ETH credit or disruption
to unrelated activation/claims. Dust, retries, wrapper failures, callbacks and
canonical handoff/late receipts belong to the same design review. None of these
conversion operations is an available operator command in the current candidate.

For a current admitted-token failure, inspect the exact asset and its provider;
there is no supported removal/sweep or accounting bypass. Healthy single-currency
claims may still work. Preserve the failure evidence and resolve/review the
dependency before retrying affected calls. See the
[operator manual](OPERATOR_MANUAL.md#revenue-operations).
