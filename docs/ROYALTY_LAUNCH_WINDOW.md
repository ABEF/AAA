# Mint close and the royalty activation window

Fresh royalty settlement3/recovery2, inventory12, reporting4 and canonicalV7.
Source candidate only: no contract, website, service or existing journal updated.

## What changes

The operator sets `NFT.setMintEnd(end)`, where `end` is the Unix timestamp of
OpenSea's FINAL sale-stage end. Minting is accepted through that timestamp and
rejected afterward. An unset end rejects minting and royalty claims. Selling all
1,000 NFTs early does not change the official clock; an undersubscribed sale can
still end normally. This call does not configure OpenSea: its reviewed drop
integration and exact matching stage configuration remain release requirements.

Governance may revise the end to another future timestamp while the OLD end has
not passed. It cannot change it after closing or shorten the fixed1-hour grace
duration. Coordinate every change with all marketplace mint stages and announce
the new deadline. Future production integration must enforce the same end across
all mint paths; a marketplace interface alone cannot enforce our contract state.

Royalty claims open at `mintEnd + 3600`. Activation before this timestamp joins
the initial cohort. Activation at the timestamp or afterward does not. Later
activation remains possible for future royalties. LP rewards, harvesting,
contributions, compounding and principal accounting keep their separate rules.

## Received funds and first allocation

During minting and the grace period, each ADMITTED currency's newly received
units accumulate in `openingPool(asset)`. No NFT can claim them yet. At opening,
the pool belongs to the NFTs activated strictly before the cutoff, weighted
Commun1/Rare2/Legendary3. Current ownership, rather than an old wallet snapshot,
determines who claims. A delayed first transaction cannot admit late activations
to that initial pool. A healthy sync, claim or first later activation materializes
the initial allocation; no keeper, swap or manual opening transaction is required.

ERC20 receipts have no universal receiver callback. Reads/claims and activation
checkpoint balances, rather than reconstructing an exact payment timestamp.
With no intervening activation, later receipts have the same eligible cohort.
A faulted currency conservatively retains its prior cohort until recovery;
pre-cutoff activations join its initial pool, late activations do not.

If no NFT activated before cutoff, the initial pool becomes unallocated. Later
activation does not automatically capture it. Governance can then use the
explicit current-active-weight allocation policy. If no NFTs exist, there is no
holder beneficiary to pay; do not invent one or promise automatic recovery.

Constructor prefunds and tokens received before admission remain SEPARATE from
the initial pool. They retain the approved review/admit/current-weight allocation
rule. The contract cannot reconstruct which NFTs were active when an unregistered
token arrived. Register reviewed marketplace currencies before the sale to avoid
this ambiguity. Never reclassify earned or fractional backing as unallocated.

## Exact operator calls

| Action | Call and inputs | Verify / reverse boundary |
| --- | --- | --- |
| Set/revise sale end | Governance `NFT.setMintEnd(uint64 end)`; end in Unix seconds, strictly in the future | Read `RoyaltyRewards.mintEnd()`, `royaltiesOpenAt()` and `MintEndConfigured`. Match the final OpenSea stage. Revisable only before the OLD end passes. |
| Inspect lock | `royaltiesOpen()`, `openingPool(asset)`, `claimable(id,asset)` | Claims return no spendable amount before opening. Actual claim attempts revert. LP claims are independent. |
| Materialize allocation | Anyone `RoyaltyRewards.sync(asset)` | `RoyaltyOpeningFinalized` records the cutoff/count/weight once; `InitialRoyaltiesAllocated` allocates one currency once. Currency faults revert only its selected sync. |
| Allocate all reviewed unallocated units | Governance `RoyaltyRewards.allocateAllUnallocated(asset,reviewHash)` | Requires open window, sealed current lifecycle, unpaused/no preparation, nonzero active weight and review hash. Returns raw amount;0 if none remain. Verify orphaned decreases, liabilities increase and balance stays unchanged. Irreversible allocation; no payout/swap. |
| Allocate selected unallocated units | Governance `allocateUnallocated(asset,amount,reviewHash)` | Same guards; exact positive raw amount. Can intentionally leave a remainder. Use the all variant when no remainder is intended. |
| Claim royalties | Current owner `claim(id,asset)` or bounded router batch | Original currencies; transfer of the NFT carries unpaid entitlement. A failed selected payout reverts the batch. Review healthy currencies separately. |

No timer runs a transaction by itself. The timestamp gates eligibility; an owner
claim can do the bookkeeping and payout in the same transaction. No operator or
keeper must first claim royalties from OpenSea.

## Expandable currency capacity

Operating capacity starts16ERC20 currencies plus ETH. Governance may call
`NFT.increaseRoyaltyAssetCapacity(capacity,reviewHash)` after gas/service review.
Capacity must strictly increase and cannot exceed64ERC20 currencies plus ETH.
Then admit a currency with `NFT.addRoyaltyAsset(token)`. Capacity changes do not
admit a token, remove a token, reweight holders or move funds.

The review hash is an operation fingerprint, NOT an on-chain proof of gas safety.
Before increasing, rehearse cold/faulted maximum activation, source-policy gas,
RPC/history/checkpoint/claim workloads, canonical export/import and recovery on
the target chain. Preserve headroom and the existing service work limits. The
fresh inventory requires capacity observations and expansion evidence; a64 ceiling
is not64-currency production qualification. Review descriptors/clients and pin
configuration together. Older17-currency readers must not be relabeled.

There is no unlimited-token guarantee. Beyond64 needs another reviewed compatible
implementation. Malicious/frozen/blacklisted/taxed/rebasing tokens can still make
their own payouts impossible. Normal active currencies remain independent. Tiny
fractional entitlements stay backed/carry forward; allocation never sweeps them.

## Incidents and canonical replacement

Time keeps passing during an outage or pause. If VRF, RPC or activation is failing
before the sale closes, review whether to extend BOTH sale schedules while that
is still allowed. After closing, no automatic pause/extension changes the cutoff.
Late activation earns future royalties only. Terminal LP exit also stops new LP
activation: do not initiate it during grace except as a deliberate emergency.

CanonicalV7 deliberately requires the window to have opened/finalized and every
admitted currency's initial allocation to have synchronized before capture.
This temporary restriction avoids dropping a live initial cohort. Exact token
read failures can still block that handoff. The five-word royalty header carries
currency count, NFT count, weight, mint end and configured capacity; V6 peers are
rejected early. LP emergency/parking/terminal-return paths remain independent.
An importing replacement retains the closed sale and never reopens the grace
window. Prefunds remain classified separately.

Reporting4 exposes the lock/deadline and preserves exact original amounts.
Initial allocation is credited once in event history; conversion, claims and
imports are not new income. Source/checkpoint identity changes require a reviewed
rebuild/re-pin; never rewrite an old checkpoint or transaction journal.

The activation transaction must finish on-chain before the cutoff; an approval
or pending transaction does not count. Per user preference, dormant NFT cards
do not display this deadline. The sale schedule still needs clear operator and
marketplace coordination. Native mint/activation pause controls do not pause the
clock; resuming mint cannot bypass a sale end which has already passed.

Official references: [OpenSea drop schedule](https://support.opensea.io/en/articles/8867049-prepare-your-drop-schedule)
and [SeaDrop active-stage checks](https://github.com/ProjectOpenSea/seadrop/blob/main/src/SeaDrop.sol).
Their integration is a release gate, not something this source-only change deploys.
