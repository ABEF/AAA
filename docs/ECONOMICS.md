# Economic rights and allocation rules

Fresh accounting4 supports [governance-triggered collective holder return](HOLDER_COLLECTIVE_EXIT.md).
After LP closes, each NFT retains unpaid proportional ETH+ZZZ principal, old
rewards and future royalty eligibility. Direct payouts are separate from income;
no holder principal withdrawal exists during normal operation. LP cannot reopen
after exit starts. Historical deployments keep their original rules.


**Undeployed candidate; production NOT APPROVED.** Accounting4, custody3,
direct governance2 and `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5` retain
the economic rights below. Historical profiles retain their own layouts and
evidence; no existing local deployment is upgraded. See [profile boundaries](POSITION_V3.md)
and [pruning review](../reports/architecture-pruning-20261025/REVIEW.md).

Governance configures contribution/conversion/maintenance loss limits within
hard 10% ceilings; defaults are 2%/1%/3%, gas separate. Captured operations,
stronger caller/venue minima and exact classified backing remain.
[Exact controls](EXECUTION_LOSS_POLICY.md), [typed routes](TYPED_V4_ROUTES.md).

The [selected pool](POOL_SELECTION.md) is Robinhood v4 native ETH/ZZZ
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`,
static 1.002% LP fee, no hook; recorded combined fee about 1.101%. Only actual
earned LP fees fund PoPL, not Uniswap's separate protocol fee.

## One fixed ZZZ token

Contributions, buyback burns and collective principal return use the same ZZZ contract.
Before sealing, configure the reviewed source ZZZ once, deploy and bind Buyback
with that immutable token, then configure Migration once to the matching source
and Buyback identity. The source and exit pins are separate records for one ZZZ,
not two economic assets. Sealing requires matching nonzero source/exit identities;
native pool admission also checks the pinned Robinhood ZZZ. LP admission accepts
native ETH/fixed ZZZ only; a reviewed fee tier of that same pair remains possible.
WETH or another accounting pair is not an admitted LP destination. Separate
reward-conversion routes do not expand principal-pool admission.
No post-seal token
replacement or buyback-retargeting setter exists. An issuer migration is not
executed by this deployment. Governance may close the collection LP and return
actual ETH/ZZZ to NFT owners; any subsequent holder token exchange or new project
deployment is separate and must not claim automatic NFT/accounting continuity.

Collective exit performs no swap into ZZZ and has no external custody recipient.
Actual returned principal is bounded by reviewed raw ETH/ZZZ output minima;
there is no USD-loss promise when closing without price feeds.

## Permanent capital

Current direct mint forwards its full 0.05 ETH charge to the immutable mint recipient; none becomes LP or rewards. The intended OpenSea path must keep the buyer total at 0.05 ETH, deduct the actual platform fee and pay that recipient the remainder, with gas separate. That compatible mint integration is not implemented; no platform percentage is assumed. See [mint qualification](MINT_INTEGRATION_QUALIFICATION.md). Contributions accept native ETH or fixed ZZZ only. Activation starts at **$100 conservative original-source value** and growth at **$5**, subject to a higher pool minimum. The **captured marginal-LP floor is 98% at the default 2% limit**, with gas separate. Conversion and deployment share that budget; Entry V1 also binds the caller maximum. Incumbent LP, idle and compound cannot subsidize a newcomer. Stricter venue bounds remain. The immutable [Entry](ACTIVATION_ENTRY.md) authenticates exact source ingress, owner intent and measured USD through the actual Vault call. Its context prevents resetting the budget after conversion. Actual feeds/routes and selected-pool execution remain unqualified.

Shares are nonredeemable during normal operation. They are priced against the pool's current principal NAV, including attributed idle and designated compounding reserves. Earlier owner fees are checkpointed before new shares. Swaps can reprice incumbent LP; this gain/loss belongs to incumbents, and execution losses are charged to the net new contribution. Compounding and market changes do not create collective memberships. Transfers preserve shares and unclaimed rights for the current holder.

[Governed paused parking](CUSTODY_PARKING.md) closes LP into bucket-attributed Vault balances without holder redemption or a USD price read. Independently reviewed raw-token minimums bound only actual LP-close proceeds. NFT shares, equal membership, royalty eligibility and funded claims persist; no ongoing LP revenue is fabricated while closed. Resume restores ordinary valuation/deployment guards, and parked migration retains authenticated funding and classified-liability barriers.

## Collected local LP fees

| Purpose | Share | Weight or destination |
| --- | --- | --- |
| NFT owner | 80% | Pool-specific nonredeemable shares |
| Collective | 10% | One equal share per activated canonical NFT, across pools |
| Permanent compounding | 5% | Isolated attributed reinvestment reserve |
| ZZZ buyback/burn | 5% | Isolated approved execution reserve |

### Allocation, reinvestment and claim timing

Pool swaps earn fees while the LP is eligible/in range; they do not run a PoPL
distribution transaction every minute. `Vault.collectFees` collects actual fees,
then FeeController funds the four allocations in that same transaction. Joining,
growing, rebalancing and standalone compounding also harvest fees along their
guarded paths. Uncollected venue fees are not yet a holder's funded claim balance.

| Event | What changes | What does not happen |
| --- | --- | --- |
| Harvest | 80% advances the bucket's per-share owner index; 10% advances the equal activated-membership index. The other 5%/5% become separately backed reserves. | No loop pays every NFT, and no burn is inferred merely from reserving funds. |
| NFT claim | Checkpoint that NFT's individual and collective balances, pay its current owner, and reduce the corresponding liability by the actual payout. Fractions remain. | No second allocation, membership change, compounding or buyback. Other NFTs' earned balances and both reserves are unchanged. |
| Reinvestment | Keeper `Compounder.compound`, or a guarded contribution/rebalance, puts the bucket's compound funds into backing/LP for its existing shares. | It does not consume holder claim balances or mint another collective membership. Retained attributed idle remains backing, not completed LP deployment. |
| Buyback | A separate keeper `Buyback.execute` spends only the designated reserve, swaps ETH to ZZZ when required, then verifies the actual ZZZ burn and supply reduction. | It does not depend on a holder claiming. Failed execution reverts reserve release; an allocated 5% is not an executed burn. |

The collective denominator is the eligible count **when receipts are allocated**,
not the number who have claimed and not a reconstructed count at each swap.
Dormant NFTs do not participate; activation grants one membership regardless of
LP size/rarity, and a top-up grants none. Published indices are checkpointed before
entry, excluding past allocated fees. Unharvested fees in another historical
bucket retain receipt-time policy; the current bucket is harvested before joining.

For an exact arithmetic example, 6,000 raw fee units with three activated NFTs
holding 10%/20%/70% of LP shares allocate owner amounts 480/960/3,360, collective
200 each, compound 300 and buyback 300. The claim totals are 680/1,160/3,560.
After any subset claims, each remaining NFT retains its amount and the two
300-unit reserves remain. A fourth dormant NFT receives zero. Currency units and
rounding matter; this example is not a USD valuation or a return forecast.

Keep harvesting, reinvestment, buybacks and claims separate. Use reviewed keeper
intervals, per-currency minimum economic batches, gas budgets and backlog alerts;
see [operating schedule](OPERATIONS.md#reward-timing-and-maintenance-schedule).
An off/failed keeper leaves funded rights and purpose reserves on-chain, but does
not promise timely reinvestment, conversion or burn.

Twenty raw units split 16/2/1/1; smaller receipts carry forward. Before membership/share changes or migration, remaining dust goes to existing owner shares. The maximum exception is now **19 raw units**, which must be valued for each admitted currency, including ETH. Low-decimal/high-unit-value tokens can make this economically material. Global index dust stays reserved; per-NFT fractions carry. No administrator can sweep reward or orphan reserves. Collection allocation
accumulators may include carried/index rounding amounts; they are not the exact
sum of all NFT claimable balances.

Already-funded dust across local buckets is settled once before entry. Fees earned by the current contribution swap are harvested under incumbent weights before issuing new shares. Only the bound Vault allocates actual local LP proceeds; an arbitrary callback or unsolicited raw Vault prefund cannot fabricate such proceeds. Actual PoolManager donations do change fee growth and fund the normal allocation at harvest; they do not prove organic trading volume. Creator inboxes and remote intake are removed.

The selected hookless native ETH/ZZZ pool has a static 1.002% LP fee. Fees actually earned by PoPL's position fund the allocation above when harvested; the separate Uniswap protocol fee is not PoPL revenue. The current candidate has no Pons creator-payment intake. No creator percentage or TVL-derived entitlement is assumed.

Current [native accounting](NATIVE_ETH_ARCHITECTURE.md) keeps venue ETH as ETH throughout Vault, fee reserves and Rewards. Native holder fees accrue directly through individual/equal-collective indices; no wrapper or keeper conversion is needed for those receipts. Already-converted ETH remains an attributed balance and never becomes new indexed income. ZZZ rewards still need a cheaper qualified route under the **default 1% loss cap, governed up to 10%, gas separate**; the selected pool's recorded approximately 1.101% combined fee does not qualify that full conversion at reference prices. An explicitly configured v3/WETH conversion retains its wrapper dependency. Typed hookless static-fee v4 conversion is implemented; actual route/feed qualification remains open. Earlier [native-port evidence](../reports/native-eth-port/VERIFICATION.md) retains its source scope and does not verify later accounting V3 changes.

The old bridge/pair execution stack, external-custodian exits and remote-fee
intake are removed. Historical profiles retain their original ledgers and
decoding. Before retirement, same-pair pool moves and compatible canonicalV5
handoff remain separate operations. Once collective exit starts, minting and all
new principal work stop permanently; canonical replacement cannot bypass it.

## Claimable, earned and paid amounts

These are separate measurements, never interchangeable:

| Measurement | Included | Excluded |
| --- | --- | --- |
| NFT rewards to claim | Its exact funded LP balance (individual plus collective) and separately recorded royalty balance | Compounding, buyback, other NFTs' shares and unswapped source balances presented as ETH |
| NFT fees generated, 24 hours / all time | Processed individual LP, equal collective rewards and royalties attributed to that NFT | Gross pool/collection revenue, repeated claims, conversion output and returned principal |
| Previously claimed | Verified lifetime LP and royalty payouts, including earlier owners | Unclaimed balances and a second recognition of earned income |

Pending admitted royalty receipts may appear in contract claimable views before
synchronization enters processed earnings history. Collection gross LP intake
is displayed separately from the NFT's net rewards. Missing history or prices
remain unavailable. These reporting distinctions do not change on-chain rights;
see [history semantics](FRONTEND_HISTORY.md).

## Equal collective membership

`ZZZMembership.activate` is vault-only, one-time and checkpoints all admitted LP reward assets before eligibility changes. A dormant NFT has zero membership; each activated NFT has one share regardless of rarity, LP size or number of top-ups. Membership persists through transfer, market losses, pauses and migration. No contribution-USD Power module or score exists. Contribution USD remains a separate historical contribution record, not a reward weight or current valuation.

## NFT-sale royalties

ERC-2981 requests **5% of a marketplace sale** payable to the immutable NFT-owned royalty receiver. Payment cannot be forced by this interface. **100% of distributable receipts** is reserved for eligible activated NFTs in weights Commun x1 / Rare x2 / Legendary x3, independently of LP revenue allocations. LP size and evolution do not change royalty weight. Current owners claim all their NFT's accrued balances.

Native ETH and up to 16 reviewed exact-transfer, non-rebasing ERC20s are supported;
stablecoins admitted here do not become contribution inputs. Pending royalties
sync to incumbents before a newly activated NFT gains weight. Constructor/admission
prefunds and zero-eligibility receipts stay quarantined. Fractions carry; index
dust stays reserved. There is no generic sweep, weight replacement or redirected
holder payout. Royalty backing has no external-custodian exit or return function.
An unreadable optional currency defers only new eligibility:
recovery protects its earlier cohort before newcomers join. Healthy currencies
and activation continue. [Batch conversion](ROYALTY_SETTLEMENT.md) credits the same
NFTs in ETH under the captured limit (default 1%, maximum 10%), gas separate.

Revealed metadata reports the fixed Commun x1 / Rare x2 / Legendary x3 trait even while
Dormant. Unrevealed weight is `Unrevealed`, not an invented rarity. The economic
ledger stays weight 0 until activation; `royalty_activated` reports that registration,
not per-currency readiness or a payment promise. No older royalties accrue to
newly eligible NFTs.

## NFT supply and evolution

Mint supply is capped at 1,000, with exact 600/300/100 rarity quotas. Authenticated VRF words are bound to each NFT/request, and permissionless reveal proceeds strictly in mint order. Draws use remaining quotas; 60/30/10 describes initial odds only. Earlier unavailable randomness blocks later reveals; there is no reroll or administrator bypass.

Evolution follows current marked LP share NAV, including attributed idle and compounding reserves, excluding claimable rewards and donations. Enhanced starts at $1,000; Singularity at $10,000. A decline can lower evolution while activation, collective membership and rarity royalties remain. Stale/oracle or parked-custody valuation is unavailable, not a zero-price observation. After confirmed collective closure, Exited5 has verified zero remaining LP and the terminal `LP exited` label using existing Activated artwork. This does not remove royalties or earned rewards.

## Strategy and migrations

Rebalancing uses configured range/deviation/cooldown, fresh valuation and bounded swaps. It does not eliminate impermanent loss or guarantee capital/returns. Buyback supports approved direct routes or direct ZZZ burn, not arbitrary multi-hop conversion. Atomic moves between admitted native ETH/fixed ZZZ pools preserve NFT shares and apply one captured aggregate maintenance floor (default 3% loss, governance maximum 10%). WETH is not native ETH and is not an admitted principal destination.

Governance may irreversibly start [collective holder return](HOLDER_COLLECTIVE_EXIT.md) while paused. Final harvested fees keep the fixed allocation; pending5%compound joins that bucket's principal. Each NFT receives its frozen share of actual ETH/ZZZ, including idle and reinvested compound, by deterministic raw-unit apportionment. Earned LP/royalty liabilities, buyback reserves, donations and quarantines are excluded. The operator closes and allocates bounded batches, then sends direct payouts to current owners; normal recipients take no action. A rejecting or unusually expensive receiver is deferred without blocking others, with retry or owner-selected fallback as exceptional recovery. Receipt cannot be forced for every address. Unpaid rights follow NFT transfer; a paid NFT cannot be paid twice. LP earnings end after all LP closes, while NFTs and future royalty shares remain.

Whole-collection handoff is separate and requires compatible accounting4/canonicalV5 while LP is still operating; it is blocked permanently once collective exit starts. No issuer exchange, bridge or post-exit canonical import is implemented. Failed venues/tokens, gas and recipient behavior can prevent or delay settlement. Actual operating rehearsals and independent review remain release gates.

Governance is immediate: the selected wallet/Safe calls modules directly, with
its own signature/nonce policy. There is no protocol timelock, queued executor
or role-grant API. Proposal/acceptance protects governance handover; it does not
change ownership, economic allocation, keeper/guardian roles or the immutable
mint recipient. Sealing does not remove governance or reviewed-replacement trust.
