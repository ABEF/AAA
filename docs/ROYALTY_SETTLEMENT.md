# Marketplace royalty settlement: original currencies

Fresh **royalty settlement4/recovery2**, accounting7/LP-allocation1/custody5/Entry3,
canonicalV10 and schema17. Historical accounting6/V8/schema15 remains separately pinned.
User decision5November2026: holders claim each royalty currency as received.
**No royalty swap, unwrap, converter binding, price-feed dependency or keeper
conversion job remains in this fresh ledger.** LP reward conversion is separate.
Existing runtimes/journals retain their original profiles. Production NOT APPROVED.

## Initial activation window

The [sale-close/window procedure](ROYALTY_LAUNCH_WINDOW.md) is part of this fresh
release: governance configures the final OpenSea sale end; royalties stay locked
through the next1hour. Admitted receipts accumulate separately in openingPool,
then allocate automatically to NFTs activated strictly before the deadline.
Late activations earn future receipts only. Zero initial participants leaves
funds unallocated for explicit governance allocation. LP claims are independent.
Unconfigured mint end rejects minting/royalty claims. No keeper is required.

`allocateAllUnallocated(asset,reviewHash)` distributes every eligible unallocated
whole unit of one admitted currency at current active weights. It cannot spend
the locked initial pool, earned backing, LP funds or another currency.
Constructor/preadmission prefunds retain their separate review/allocation rule.

Governance can increase operating ERC20 capacity from16 up to64 using the NFT
wrapper after a measured gas/service review. Exact entitlements remain; no
unlimited external-call loop or deferred-by-default enrollment is introduced.
The hard ceiling is not target-chain qualification or a universal-token promise.

## Accepted direction

Configure OpenSea creator earnings to `NFT.royaltyRewards()`, not a personal
wallet. Paid royalties arrive at that contract through marketplace settlement;
there is no separate OpenSea claim. ERC2981 requests5%, it does not enforce payment.
Verify actual Robinhood listing/offer/checkout transfers before release.
[OpenSea settings](https://support.opensea.io/en/articles/8867026-how-do-i-set-creator-earnings-on-opensea),
[ERC2981](https://eips.ethereum.org/EIPS/eip-2981).

Native ETH remains ETH. WETH remains WETH, USDC remains USDC, and each other
reviewed admitted currency remains itself. Only ETH/fixedZZZ are contribution
inputs; royalty admission does not change that pair. All distributable royalties
use activated Commun1/Rare2/Legendary3 weights, independent of LP size/evolution.
The LP80/10/5/5 allocation does not apply to royalties.

## Per-currency accounting and outage boundary

Each currency has independent accounted backing, liabilities, unallocated units,
eligible cohort, GCD-normalized ticket books and per-NFT whole-unit rights.
Use [exact allocation](EXACT_ROYALTY_ALLOCATION.md); prices and token tickers are
not accounting inputs. The current owner inherits all unpaid rights on transfer.
New activations settle readable currencies to incumbents before joining. A
growth contribution does not add another royalty weight.

An optional currency failure does not undo activation or healthy-currency claims.
Its earlier eligible cohort remains entitled to unseen receipts. Once readable,
`sync(asset)` settles those receipts first, then enrolls waiting NFTs for future
receipts. This is sampled balance accounting, not reconstruction of every payment
time during an outage. Review `eligibleFor`, `eligibleCount`, pending/accounted
balances and the deferred/recovered events. Anyone may call healthy `sync`;
operators can do so after a currency recovers. No conversion worker is required.

Fresh royalties have no scaled fraction/index reserve: all allocated raw units
are assigned to eligible tickets. Fresh7 LP rewards use separate exact-unit
trees; historical royalty/LP fractions retain their old rules. Taxed/rebasing/blacklisted/unreadable tokens are
not universally supported. Review conventional exact-transfer token behavior.

## Operator procedure

| Action | Exact call/config | Verify |
| --- | --- | --- |
| Admit currency, including after seal | Governance `NFT.addRoyaltyAsset(TOKEN_ADDRESS)` | Exact token/behavior/code/metadata, current capacity and AssetAdded. Native ETH is already admitted. No route/oracle is needed merely to claim. |
| Inspect entitlement | `RoyaltyRewards.claimable(NFT_ID,ASSET)` | Raw units, current NFT owner and currency-specific eligibility; ETH uses address zero. |
| Synchronize a healthy currency | `RoyaltyRewards.sync(ASSET)` | Real receipts and waiting-cohort enrollment, without payout or swap. Faults revert that currency's call. |
| Claim one currency | Current owner `RoyaltyRewards.claim(NFT_ID,ASSET)` | Owner receives the same asset; only its selected liability decreases. No token approval is needed. |
| Claim LP plus several royalty currencies | Owner `ClaimRouter.claimBatch([(NFT_ID,ASSET,false/true),...])` | At most32 NFT/asset/ledger entries, no duplicates. `false` LP, `true` royalties. Every NFT must belong to caller. |
| Recover unallocated receipts | Governance `allocateUnallocated(ASSET,RAW_AMOUNT,REVIEW_HASH)` | See restricted allocation below; no conversion, recipient or price arguments. |
| Configure API | `royalty_reporting: {schema:5, converter:null}` | Exact runtime and ROYALTY_SETTLEMENT_VERSION4, separate raw balances, unavailable prices never guessed zero. |
| Configure fresh keeper | `royalty_settlement_version:4`, omit royalty_conversion or set only `{enabled:false}` | No royalty swaps/unwraps. LP conversion remains separately opt-in. Preserve legacy pending recovery under its original runtime/config. |

One failed selected payout reverts the entire router batch. The opt-in
[claim planner](CLAIM_PLANNING.md) prepares one bounded executable batch and
reports every blocked/unresolved selection; it never silently discards one.
Simulate exact claims;
review healthy currencies separately if another is broken. No automatic skipping,
swapping or sending to an operator wallet occurs. Claims retain their own pause/
canonical/current-owner guards. Terminal LP exit does not end royalty eligibility.

Before admitting a new currency, prepare its reviewed API asset descriptor and
website reward_assets entry, then qualify that coordinated configuration rollout.
An on-chain admission does not reload a server or populate client metadata.
No USD feed is required for the raw claim; missing USD prices stay unavailable.
In schema17, declare an admitted non-ETH royalty currency's strategy as
`claim_original`. A royalty-only token may explicitly have `price_policy:null`;
token identity/decimals/transfer-behavior/admission checks still apply. ETH, ZZZ,
LP reward assets, contribution assets and conversion sources retain required
independent price policies. The observer uses the same narrow distinction.

## Unexpected currencies and unallocated recovery

`ROYALTY_RECOVERY_VERSION()==2` identifies original-currency allocation, not the
old six-argument recovery1 swap. Review the receipt's provenance and classification.
For an unsupported token, review/admit it first; its existing balance is recorded
as unallocated. Admission is append-only: operating capacity starts16, governance can increase it up to64ERC20 currencies plus
ETH. Do not fill slots with spam. No unlimited-token guarantee or arbitrary sweep
is introduced; full capacity/unconventional tokens remain explicit release risks.

Governance calls `allocateUnallocated(asset,amount,reviewHash)` only when sealed,
current canonical state0, unpaused/no preparation, with active rarity weight.
The asset must be admitted, amount positive and no greater than `orphaned(asset)`
after synchronizing pending receipts; reviewHash is a nonzero reviewed-operation
fingerprint. Exact inputs are in the Operator call tables. Earned/deferred ticket rights are excluded; no earned unit is reclassified as
unallocated. Historical fractional reserves and fresh7 exact LP books keep
their separate rules. No price, approval, route, deadline,
converter or external beneficiary is involved.

The amount moves from unallocated backing to liabilities in the SAME currency;
accounted backing stays unchanged. It joins the current GCD-normalized rarity-ticket book under
the user's separately approved recovery rule. Verify
`UnallocatedRoyaltiesAllocated(asset,amount,activeWeight,reviewHash)`, unchanged
token balance and correct orphan/liability/ticket-cursor changes. Holders later claim
normally. Success is irreversible; failure reverts, leaving backing intact.

<a id="late-receipts-after-retirement"></a>

## Late receipts and historical profiles

Authenticated retirement can still `forwardLate(asset)` only to the fixed immediate
successor, never a selected custody wallet. That successor separately reviews
admission/allocation. Exact unreadable backing can still block handoff.

Legacy conversion/recovery1 events, readers and tests remain explicitly historical;
they do not enable swaps on settlement4. Current canonicalV10 retains the
royalty4 sale/capacity and whole-ticket records, while separately preserving
the new raw exact LP trees in Rewards' fixed canonical child. It requires the
initial royalty window complete. HistoricalV8 and older record shapes are not
runtime/storage compatibility. Authenticate current hashes/capabilities;
never relabel a deployed contract or rewrite an old transaction journal.

## Qualification boundary

[Current change/evidence](../reports/last24h-audit-20261105/REVIEW.md),
[mixed claims](CLAIM_ROUTER.md), [reporting](ROYALTY_REPORTING.md).
Actual token behavior, marketplace payment, API/site configuration, gas and
independent audit remain open in the [sole task](../TODO.md#task-royalty-eth-settlement).
Source publication does not deploy, seal, change a server or enable public signing.
