# Economic rights and allocation rules

**Undeployed candidate; production NOT APPROVED.** Accounting V3 removes unused
remote Position copies; direct governance V2 and same-chain canonical V4 retain
the economic rights below. Historical profiles retain their own layouts and
evidence; no existing local deployment is upgraded. See [profile boundaries](POSITION_V3.md)
and [pruning review](../reports/architecture-pruning-20261025/REVIEW.md).

Governance configures contribution/conversion/maintenance loss limits within
hard 10% ceilings; defaults are 2%/1%/3%, gas separate. Captured operations,
original approved custody floors, stronger caller/venue minima and backing remain.
[Exact controls](EXECUTION_LOSS_POLICY.md), [typed routes](TYPED_V4_ROUTES.md).

The [selected pool](POOL_SELECTION.md) is Robinhood v4 native ETH/ZZZ
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`,
static 1.002% LP fee, no hook; recorded combined fee about 1.101%. Only actual
earned LP fees fund PoPL, not Uniswap's separate protocol fee.

## One fixed ZZZ token

Contributions, buyback burns and normal all-ZZZ exit use the same token contract.
Before sealing, configure the reviewed source ZZZ once, deploy and bind Buyback
with that immutable token, then configure Migration once to the matching source
and Buyback identity. The source and exit pins are separate records for one ZZZ,
not two economic assets. Sealing requires matching nonzero source/exit identities;
native pool admission also checks the pinned Robinhood ZZZ, and generic ERC20
pool admission requires the same fixed ZZZ as one currency. A reviewed future
WETH/ZZZ pool or fee tier remains possible; a pair without ZZZ is rejected.
No post-seal token
replacement or buyback-retargeting setter exists. An issuer token migration uses
custody exit and a fresh reviewed deployment; it does not erase NFT ownership,
earned balances or purpose-bound reserves.

This setup check does not add a Buyback or source-policy call to raw exit.
Explicit raw exit still transfers actual pair assets without conversion under
its own custody and raw-minimum checks.

## Permanent capital

Current direct mint forwards its full 0.05 ETH charge to the immutable mint recipient; none becomes LP or rewards. The intended OpenSea path must keep the buyer total at 0.05 ETH, deduct the actual platform fee and pay that recipient the remainder, with gas separate. That compatible mint integration is not implemented; no platform percentage is assumed. See [mint qualification](MINT_INTEGRATION_QUALIFICATION.md). Contributions accept native ETH or fixed ZZZ only. Activation starts at **$100 conservative original-source value** and growth at **$5**, subject to a higher pool minimum. The **captured marginal-LP floor is 98% at the default 2% limit**, with gas separate. Conversion and deployment share that budget; Entry V1 also binds the caller maximum. Incumbent LP, idle and compound cannot subsidize a newcomer. Stricter venue bounds remain. The immutable [Entry](ACTIVATION_ENTRY.md) authenticates exact source ingress, owner intent and measured USD through the actual Vault call. Its context prevents resetting the budget after conversion. Actual feeds/routes and selected-pool execution remain unqualified.

Shares are nonredeemable. They are priced against the pool's current principal NAV, including attributed idle and designated compounding reserves. Earlier owner fees are checkpointed before new shares. Swaps can reprice incumbent LP; this gain/loss belongs to incumbents, and execution losses are charged to the net new contribution. Compounding and market changes do not create collective memberships. Transfers preserve shares and unclaimed rewards for the current holder.

[Governed paused parking](CUSTODY_PARKING.md) closes LP into bucket-attributed Vault balances without holder redemption or a USD price read. Independently reviewed raw-token minimums bound only actual LP-close proceeds. NFT shares, equal membership, royalty eligibility and funded claims persist; no ongoing LP revenue is fabricated while closed. Resume restores ordinary valuation/deployment guards, and parked migration retains authenticated funding and classified-liability barriers.

## Collected local LP fees

| Purpose | Share | Weight or destination |
| --- | --- | --- |
| NFT owner | 80% | Pool-specific nonredeemable shares |
| Collective | 10% | One equal share per activated canonical NFT, across pools |
| Permanent compounding | 5% | Isolated attributed reinvestment reserve |
| ZZZ buyback/burn | 5% | Isolated approved execution reserve |

Twenty raw units split 16/2/1/1; smaller receipts carry forward. Before membership/share changes or migration, remaining dust goes to existing owner shares. The maximum exception is now **19 raw units**, which must be valued for each admitted currency, including ETH. Low-decimal/high-unit-value tokens can make this economically material. Global index dust stays reserved; per-NFT fractions carry. No administrator can sweep reward or orphan reserves.

Already-funded dust across local buckets is settled once before entry. Fees earned by the current contribution swap are harvested under incumbent weights before issuing new shares. Only the bound Vault allocates actual local LP proceeds; callbacks and raw donations cannot create fee income. Creator inboxes and remote intake are removed.

The selected hookless native ETH/ZZZ pool has a static 1.002% LP fee. Fees actually earned by PoPL's position fund the allocation above when harvested; the separate Uniswap protocol fee is not PoPL revenue. The current candidate has no Pons creator-payment intake. No creator percentage or TVL-derived entitlement is assumed.

Current [native accounting](NATIVE_ETH_ARCHITECTURE.md) keeps venue ETH as ETH throughout Vault, fee reserves and Rewards. Native holder fees accrue directly through individual/equal-collective indices; no wrapper or keeper conversion is needed for those receipts. Already-converted ETH remains an attributed balance and never becomes new indexed income. ZZZ rewards still need a cheaper qualified route under the **default 1% loss cap, governed up to 10%, gas separate**; the selected pool's recorded approximately1.101% combined fee does not qualify that full conversion at reference prices. An explicitly configured v3/WETH conversion retains its wrapper dependency. Typed hookless static-fee v4 conversion is implemented; actual route/feed qualification remains open. Earlier [native-port evidence](../reports/native-eth-port/VERIFICATION.md) retains its source scope and does not verify later accounting V3 changes.

The old bridge/pair execution stack and remote-fee intake are removed. Historical
remote/inbox profiles retain their own ledgers and decoding; no automatic import,
erasure or reinterpretation is provided. Current movement uses [governed custody](GOVERNED_CUSTODY_HANDOFF.md)
and compatible LP-only canonical V4. Contributions remain blocked while principal
is away or its plan is outstanding.

## Equal collective membership

`ZZZMembership.activate` is vault-only, one-time and checkpoints all admitted LP reward assets before eligibility changes. A dormant NFT has zero membership; each activated NFT has one share regardless of rarity, LP size or number of top-ups. Membership persists through transfer, market losses, pauses and migration. No contribution-USD Power module or score exists. Contribution USD remains a separate historical contribution record, not a reward weight or current valuation.

## NFT-sale royalties

ERC-2981 requests **5% of a marketplace sale** payable to the immutable NFT-owned royalty receiver. Payment cannot be forced by this interface. **100% of actual receipts** is reserved for already-activated NFTs in weights Commun x1 / Rare x2 / Legendary x3, independently of LP revenue allocations. LP size and evolution do not change royalty weight. Current owners claim all their NFT's accrued balances.

Native ETH and up to 16 reviewed exact-transfer, non-rebasing ERC20s are supported;
stablecoins admitted here do not become contribution inputs. Pending royalties
sync to incumbents before a newly activated NFT gains weight. Constructor/admission
prefunds and zero-eligibility receipts stay quarantined. Fractions carry; index
dust stays reserved. There is no generic sweep, weight replacement or redirected
holder payout. Explicit governed paused currency custody may move backing to a
trusted recipient, retaining liabilities and suspending that currency until full
original-asset return. An unreadable optional currency defers only new eligibility:
recovery protects its earlier cohort before newcomers join. Healthy currencies
and activation continue. [Batch conversion](ROYALTY_SETTLEMENT.md) credits the same
NFTs in ETH under the captured limit (default 1%, maximum 10%), gas separate.

Revealed metadata reports the fixed Commun x1 / Rare x2 / Legendary x3 trait even while
Dormant. Unrevealed weight is `Unrevealed`, not an invented rarity. The economic
ledger stays weight 0 until activation; `royalty_activated` reports that registration,
not per-currency readiness or a payment promise. No older royalties accrue to
newly eligible NFTs.

## NFT supply and evolution

Mint supply is capped at1,000, with exact 600/300/100 rarity quotas. Authenticated VRF words are bound to each NFT/request, and permissionless reveal proceeds strictly in mint order. Draws use remaining quotas; 60/30/10 describes initial odds only. Earlier unavailable randomness blocks later reveals; there is no reroll or administrator bypass.

Evolution follows current marked LP share NAV, including attributed idle and compounding reserves, excluding claimable rewards and donations. Enhanced starts at $1,000; Singularity at$10,000. A decline can lower evolution while activation, collective membership and rarity royalties remain. Stale/oracle or external/parked-custody valuation is unavailable, not a zero-price observation. It does not block claims or recovery.

## Strategy and migrations

Rebalancing uses configured range/deviation/cooldown, fresh valuation and bounded swaps. It does not eliminate impermanent loss or guarantee capital/returns. Buyback supports approved direct routes or direct ZZZ burn, not arbitrary multi-hop conversion. Atomic moves within the same actual currency pair preserve NFT shares and apply one captured aggregate maintenance floor (default 3% loss, governance maximum 10%). A pre-existing approved normal custody floor cannot be weakened by a later cap change. Native ETH and WETH are different assets: an atomic boundary conversion is not implemented and the pair guard rejects it.

Separately approved custody exits trust the external recipient: normal exit consolidates principal to ZZZ under the floor, while explicit raw exit bypasses swaps/USD valuation and sends actual ETH/ZZZ under raw minimums. Native close, fee classification, exit and exact funded recovery do not call WETH. A failed pool or token can still block recovery. Whole-collection handoff is separate and uses compatible LP-only canonical V4; legacy schemas and future-chain transport are unsupported. Actual backing, gas/MEV, operating rehearsals and independent economic/security review remain release gates.

Governance is immediate: the selected wallet/Safe calls modules directly, with
its own signature/nonce policy. There is no protocol timelock, queued executor
or role-grant API. Proposal/acceptance protects governance handover; it does not
change ownership, economic allocation, keeper/guardian roles or the immutable
mint recipient. Sealing does not remove governance or external-custodian trust.
