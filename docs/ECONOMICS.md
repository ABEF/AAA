# Economic rights and allocation rules

**Current execution policy (2026-10-24):** governance may configure contribution, conversion and maintenance loss limits within hard10% ceilings; defaults remain1%/1%/3%, with gas separate. Captured operation policy, original approved custody floors, stronger caller/venue minima and backing remain. [Exact controls and risks](EXECUTION_LOSS_POLICY.md), [typed v4 routes](TYPED_V4_ROUTES.md). Earlier fixed-limit descriptions are default/historical scope. The candidate remains undeployed and production NOT APPROVED.


**Selected pool (2026-10-24):** Robinhood Uniswap v4 native ETH/ZZZ `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`, static 1.002% LP fee, no hook. The observed protocol fee makes the combined fee about 1.101%. Hookless native admission and atomic `moveFunds` are the current candidate; external `exit` remains separately approved and paused. [Selection and limits](POOL_SELECTION.md). Production remains NOT APPROVED.

Current accepted rules: $100 activation, 80/10/5/5 revenue, equal activated-NFT collective membership and separate rarity royalties. This is an undeployed candidate; publication is not approval to use real funds.

## Permanent capital

The 0.05 ETH mint charge is forwarded to the immutable mint recipient and never becomes LP or rewards. The accepted activation input minimum is **$100 in value**, with **at least 99% deployed as marginal LP** after execution; network gas is separate. The same 1% execution/undeployed limit applies to additions. Incumbent LP, idle and compound assets cannot subsidize the new contribution. Stricter pool execution bounds still apply. The immutable [atomic Entry](ACTIVATION_ENTRY.md) authenticates exact original-source ingress, current-owner intent and measured USD value through typed conversion into the Vault. Its short-lived context prevents using post-conversion value to reset the 1% budget. Actual production feeds/routes and selected hookless-pool execution still need qualification.

Shares are nonredeemable. They are priced against the pool's current principal NAV, including attributed idle and designated compounding reserves. Earlier owner fees are checkpointed before new shares. Swaps can reprice incumbent LP; this gain/loss belongs to incumbents, and execution losses are charged to the net new contribution. Compounding and market changes do not create collective memberships. Transfers preserve shares and unclaimed rewards for the current holder.

[Governed paused parking](CUSTODY_PARKING.md) closes LP into bucket-attributed Vault balances without holder redemption or a USD price read. Independently reviewed raw-token minimums bound only actual LP-close proceeds. NFT shares, equal membership, royalty eligibility and funded claims persist; no ongoing LP revenue is fabricated while closed. Resume restores ordinary valuation/deployment guards, and parked migration retains authenticated funding and remote-liability barriers.

## Collected LP fees and optional funding

| Purpose | Share | Weight or destination |
| --- | --- | --- |
| NFT owner | 80% | Pool-specific nonredeemable shares |
| Collective | 10% | One equal share per activated canonical NFT, across pools |
| Permanent compounding | 5% | Isolated attributed reinvestment reserve |
| ZZZ buyback/burn | 5% | Isolated approved execution reserve |

Twenty raw units split 16/2/1/1; smaller receipts carry forward. Before membership/share changes or migration, remaining dust goes to existing owner shares. The maximum exception is now **19 raw units**, which must be valued for each admitted currency, including ETH. Low-decimal/high-unit-value tokens can make this economically material. Global index dust stays reserved; per-NFT fractions carry. No administrator can sweep reward or orphan reserves.

All registered creator inboxes are processed and their old dust settled before a new membership or shares can be issued. Late receipts during entry are settled under old weights with a final pending-funds barrier. New members get no earlier published/pending income. Payments delivered later use processing-time membership and shares; no historical creator entitlement is reconstructed.

The selected hookless native ETH/ZZZ pool has a static 1.002% LP fee. Fees actually earned by PoPL's position fund the allocation above when harvested; the separate Uniswap protocol fee is not PoPL revenue. Historical Pons creator payments are optional funding, not a prerequisite for this selected pool. No creator percentage or TVL-derived entitlement is assumed.

The undeployed [native V2 candidate](NATIVE_ETH_ARCHITECTURE.md) keeps venue ETH as ETH throughout Vault, fee reserves and Rewards. Native holder fees accrue directly through individual/equal-collective indices; no wrapper or keeper conversion is needed for those receipts. Already-converted ETH remains an attributed balance and never becomes new indexed income. ZZZ rewards still need a cheaper qualified conversion route under the unchanged **1% loss cap, gas separate**; the selected pool's approximately 1.101% combined swap fee does not qualify that full conversion at reference prices. An explicitly configured v3/WETH conversion operation retains its wrapper dependency. Typed v4 conversion support and actual route/feed qualification remain open. The earlier WETH checkpoint reports retain their historical source scope; use the [native-port verification](../reports/native-eth-port/VERIFICATION.md) for the current candidate.

Historical already-allocated remote owner/collective liabilities are not split again or erased. Their token provenance, funding barriers and old evidence retain their original scope. The old bridge/pair execution stack is removed; current principal movement uses [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md). External inbox funding does not discharge remote liabilities, and new contributions remain blocked while principal custody is away or its plan remains outstanding.

## Equal collective membership

`ZZZMembership.activate` is vault-only, one-time and checkpoints all admitted LP reward assets before eligibility changes. A dormant NFT has zero membership; each activated NFT has one share regardless of rarity, LP size or number of top-ups. Membership persists through transfer, market losses, pauses and migration. No contribution-USD Power module or score exists. Contribution USD remains a separate historical contribution record, not a reward weight or current valuation.

## NFT-sale royalties

ERC-2981 requests **5% of a marketplace sale** payable to the immutable NFT-owned royalty receiver. Payment cannot be forced by this interface. **100% of actual receipts** is reserved for already-activated NFTs in weights Commun1/Rare2/Legendary3, independently of LP revenue allocations. LP size and evolution do not change royalty weight. Current owners claim all their NFT's accrued balances.

Native ETH is supported; up to16 reviewed exact-transfer, non-rebasing ERC20 assets may be admitted. All raw pending royalties are synced to incumbents before a newly activated NFT gains weight. Constructor/admission prefunds and receipts with zero eligible weight are quarantined permanently, excluding future entrants. Fractions carry; index dust stays reserved. There is no rescue, administrator withdrawal, weight replacement or redirected payout. An unreadable optional currency defers only its new eligibility: recovery allocates unseen receipts to its earlier cohort before newcomers join. Healthy currencies and LP activation continue. [Batch conversion](ROYALTY_SETTLEMENT.md) credits the same NFTs in ETH with a 1% execution limit and gas separate; source fractions remain backed.

## NFT supply and evolution

Mint supply is capped at1,000, with exact600/300/100 rarity quotas. Authenticated VRF words are bound to each NFT/request, and permissionless reveal proceeds strictly in mint order. Draws use remaining quotas; 60/30/10 describes initial odds only. Earlier unavailable randomness blocks later reveals; there is no reroll or administrator bypass.

Evolution follows current marked LP share NAV, including attributed idle and compounding reserves, excluding claimable rewards and donations. Enhanced starts at$1,000; Singularity at$10,000. A decline can lower evolution while activation, collective membership and rarity royalties remain. Stale/oracle/remote valuation is unavailable, not a zero-price observation. It does not block claims or migration.

## Strategy and migrations

Rebalancing uses configured range/deviation/cooldown, fresh valuation and bounded swaps. It does not eliminate impermanent loss or guarantee capital/returns. Buyback supports approved direct routes or direct ZZZ burn, not arbitrary multi-hop conversion. Atomic moves within the same actual currency pair preserve NFT shares and apply one fixed 3% aggregate loss floor. Native ETH and WETH are different assets: an atomic boundary conversion is not implemented and the pair guard rejects it.

Separately approved custody exits trust the external recipient: normal exit consolidates principal to ZZZ under the floor, while explicit raw exit bypasses swaps/USD valuation and sends actual ETH/ZZZ under raw minimums. Native close, fee classification, custody exit and exact funded recovery do not call WETH. A failed pool or token can still block recovery. Whole-collection handoff is separate and versioned; legacy V1 canonical import and future-chain transport are not supported by the native V2 candidate. Actual finality/backing, gas/MEV, operating rehearsals and independent economic/security review remain release gates.
