# Actual LP fees, exact NFT entitlements and current-owner claims

21 November 2026. Baseline `33af0ab927d6724b724df99e926fedf78e4febcf`.
**The new finite fee-flow partition passes. Production remains NOT APPROVED.**

## What improved

The [previous composed integration](../pool-integration-20261120/REVIEW.md) proved
production swaps and four Entry contributions, but deliberately did not requalify
the complete80/10/5/5 reserve/claim relationship. This work closes that missing
finite connection against the supplied real native Uniswap core, using the
saved normal39-instance F6 graph rather than repeating construction, minting,
activation or growth.

The supplied pool is still a testing target at block119107223, not an approved
launch market. Two NFTs, one main position and controlled funding/prices/depth
remain explicit. No production Solidity, financial policy, gas profile, authority,
consumer or operating configuration changes.

## Independent starting-state proof

The [independent baseline replay](review/REVIEW.md) authenticates the original
Entry archive and replays six reward credits plus every share/membership change.
All four captured after-states match. It starts from zero expected money and
uses an eager rational allocation model; it does not initialize expected claims
from observed claimables or read production pending/phase storage.

The maintained engine preserves the high fairness phase and rebases only its
low remainder after real weight changes. The historical Python phase-reset
design helper is unsuitable for this history and is not run or adopted. A new
[counterexample control](run/ORACLE_CONTROL.json) distinguishes these behaviors:
weights1/1, credit1, change to2/1, credit1 gives cumulative1/1 rather than0/2.
No-op weights and zero credits preserve phase.

The extension uses a separately reviewed two-adjacent-ordinal specialization.
The full baseline replay confirms only that joint branch has nonzero individual
phase; mint count, ordinals and zero other memberships are authenticated. This
is not a general1,000-NFT/all-order workload qualification.

## New actual-core journey

[Detailed run and evidence](run/REVIEW.md).

The passing clone executes17local transactions: an external test trader and
exact reverse allowance, three actual trades, three collections, one NFT transfer,
one controlled feed fault and seven claims. These are a composed journey, not
17new independent test methods. Two negative read-only checks are separate.

| Collection | Actual ETH received, wei | Actual ZZZ received, raw units |
| --- | ---: | ---: |
| After both swap directions |44,297,574,637|6,240,265,720,857,220|
| Without another trade |0|0|
| After transfer/new trade, with invalid feed |22,148,787,318|0|

For each asset, the independent checks apply `u=(oldDust+receipt)//20`:
`16u` individual, `2u` collective, `u` compound and `u` buyback, with remainder
`<20` retained as classified fee dust. Earlier entry barriers correctly credited
their tails to incumbent personal rewards, and previously released compound
remains attributed Vault idle. Do not count either reserve as holder income.

Actual receipt deltas, allocation/credit events, individual and collective books,
claimable totals, liabilities and contract cash reconcile. The no-trade repeat
produces no new fee income. Harvest does not swap, compound or burn.

### Transfer and payout rights

The first owner claims one NFT's ETH while retaining its ZZZ rights, then
transfers that NFT. Further fees accrue to the NFT. The former owner's ZZZ claim
is rejected with `Unauthorized()` in simulation; no failed payout transaction
is sent. The new owner receives that NFT's remaining ETH and ZZZ, while the
original owner claims the other NFT. Repeat claims pay zero.

All **allocated** ETH/ZZZ LP reward liabilities, corresponding tree outstanding
balances and Rewards cash reach zero. Payouts include the earlier prefix's
funded rewards as well as new income. Recipient deltas match payouts; native
comparisons account separately for the sender's actual network gas. Shares,
membership, main ID4331098, L142316833039121843140, ticks121400/132600, centre and
rebalance clock remain unchanged. Market trades can reprice principal amounts;
this is not a promise of constant USD principal value.

Direct fixed-ZZZ claims are an existing current-owner contract capability. This
does not change the normal consumer's ETH-only flow, perform a conversion, or
qualify the separate1% conversion route. NFT-sale royalties are separate and
are not qualified by this LP-only journey.

### Feed outage isolation and classified reserves

One existing owned fixture feed is deliberately set to zero. The public Oracle
read correctly fails with `InvalidPrice(ETH)`. Normal collection and claims
continue without waiving a price guard: these operations use actual funded
assets and have no USD-price dependency. The maintained keeper already has a
separate due-harvest fallback after an ordinary maintenance RPC failure; that
existing source behavior is not a new code fix or full-daemon acceptance.

Final FeeController balances remain exactly classified and backed:

| Asset | Compound | Buyback | Dust | Accounted and actual cash |
| --- | ---: | ---: | ---: | ---: |
| ETH, wei |3,322,318,097|10,708,322,192|15|14,030,640,304|
| ZZZ, raw units |312,013,286,042,861|12,880,570,335,965,477|0|13,192,583,622,008,338|

These balances include earlier receipts. They are intentional reserves/carry,
not unpaid allocated holder liabilities. Vault-attributed idle remains unchanged. Claims do
not spend principal, compound reserves, buyback reserves or fee dust.

## Gas and confirmed tool correction

The three collection allowances, with full25% padding, are `1,175,429`, `414,065`
and `758,172` gas, within the unchanged24M envelope. The largest of seven direct claim
allowances is534,490gas with full20% padding, within12M. These finite local
measurements do not qualify cold claim batches, target execution capacity,
complete Robinhood fees or economic profitability of tiny payouts.

The first restore attempt stops before any transaction: the authenticated full
graph snapshot exceeds Anvil's default2MB HTTP request limit. The new report
driver uses the installed `--load-state` file interface with an exclusive,
hash-verified derived JSON file, bounded to16MiB. Its actual size is13,643,211bytes.
Default HTTP limits, strict RPC IDs, code-size/gas limits and financial guards
remain. This corrects the rehearsal tool, not production contracts. The original
failed attempt and cleanup are retained; it is not presented as a contract failure.

## Preservation and remaining acceptance

Both owned nodes stop with no pending submission. Original Entry evidence,
existing Anvil8902/NFTs/LP/balances, journals/checkpoints, websites/services and
the paused heartbeat remain unchanged. No new production deployment or sealing
occurs. Frozen F6 source/Factory6/allocation2 and earlier size/static evidence
retain their exact scope; no unchanged contract/browser/population suite is run.

Real independent feeds, sustainable market depth/routes, ETH conversion,
buyback/compound execution, optional residuals, larger cohorts/currencies,
faulty recipients/tokens, matching backend/wallet operation, actual normal keeper
operation, complete fees and independent release approval remain separate.
This proof is finite and does not establish every-market or adversarial immunity.
The [plan](PLAN.md) and [baseline](BASELINE.json) preserve scope and original
document hashes; child reports retain exact sources, state, wire and manifests.
