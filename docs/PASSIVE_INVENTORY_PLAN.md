# Bounded passive inventory research and design rationale

This page preserves the earlier research/design discussion; its unresolved choices
and no-swap examples are historical alternatives, not current implementation.
The approved [implementation plan](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md),
[profile6](POSITION_V6.md) and [operator procedure](OPERATOR_MANUAL.md) own behavior.
The implemented hybrid permits a guarded partial swap to attain main>=60%, with
one residual<=40%; latest initial geometry is HALF corresponding side (5000bps),
not the earlier full-side choice. Threshold85%,600/240/300sampled window,
60–300jitter and hard initial12hours are explicit. No live qualification follows.
Read [review/evidence](../reports/optional-portfolio-20261030/REVIEW.md).

Requested30October2026. This is a researched proposal for a fresh candidate, not
an operating procedure, provider qualification or approval of a swap fallback.
Current accounting4/maintenance2/confirmation2 and all installed services remain
unchanged. [Research scope](../reports/passive-inventory-research-20261030/README.md).

## Requested policy and unresolved choices

The user requested85% of the actual centre-to-boundary distance, in ZZZ-price-in-ETH
space,10minutes sampled persistence and one durable random60-300second delay.
A return inside or side change invalidates both window and delay. Four-minute
sampling cannot prove every intervening price; source cadence and maximum gap
must remain distinct. Existing physical-range exit predicates cannot implement
this inside-range policy by relabelling keeper settings.

For actual centre C, lower price D and upper price U, the trigger thresholds are
C-0.85(C-D) and C+0.85(U-C). At ideal arithmetic+/-50% these are+/-42.5% from C;
at+/-25%,+/-21.25%. Actual tick rounding and inverse native pair orientation matter;
85% of ticks or square-root distance would be a different policy.

Funding choice, residual width/completion, pure no-swap versus recovery swaps and
the12hour minimum remain unresolved. The present12hour hard minimum is not
removed by this plan. No automatic volatility policy,20%/40%trigger, third leg,
new asset, external custodian or production transaction is implied.

## Evidence from other managers

The [DefiLlama category snapshot](https://defillama.com/protocols/liquidity-manager)
showed approximate protocol/product totals: Arrakis$56.5m, Kodiak Islands$35.0m,
Steer$15.6m, ICHI$6.0m, Gamma$2.8m and Charm$1.8m. The separate
[Beefy page](https://defillama.com/protocol/beefy) showed$98.8m across all its
products. These are retrieved/cached snapshots, not exact live balances or
strategy-specific TVL; high TVL is not security proof.

| Reference | Verified mechanism and useful lesson |
| --- | --- |
| [Beefy CLM](https://beefy.finance/articles/eth-clms/) | Documented main+one alt, without a rebalance sale. Historical pinned Uniswap source removes both legs, deploys paired main, then one residual; with one asset the main can be empty. Do not copy its harvest/deposit resetting into PoPL. |
| [Charm AlphaPro source](https://raw.githubusercontent.com/charmfinance/alpha-vaults-v2-contracts/main/contracts/AlphaProVault.sol) | Burns existing full/base/limit, then optional full-range allocation, maximum base and one residual limit. Bounded configured slots, not recursive residual positions. Inspected v2 rebalance contains no swap. |
| [Gamma strategies](https://docs.gamma.xyz/gamma/lp-vaults/strategies) | Classic dual base/limit; inspected v1.3 core consolidates both before replacement. Current v4 families separately support up to20positions. Do not infer all Gamma products use two legs or share one rebalance guard. |
| [Arrakis oracle checks](https://docs.arrakis.finance/text/arrakisModular/priceOracles.html) | Independent before/after valuation and module checks. Its general modules permit multiple ranges and optional swaps, rather than enforcing this specific passive policy. |
| [Kodiak rebalance controls](https://documentation.kodiak.finance/protocol/islands/island-mechanics/rebalancing) | Separates compounding from range management; reviewed external execution, output/TWAP controls and trade size/pace discipline. Not a universally swap-free strategy. |
| [Steer strategy interface](https://docs.steer.finance/flagship-apps/smart-pools/developing-with-smart-pools/strategy-side/) | Explicit multi-position targets and strategy-specific optional swap skipping. The engine's flexibility is not a two-leg or no-swap guarantee. |
| [ICHI YieldIQ](https://docs.ichi.org/home/yieldiq-strategy.md) | Inventory tolerances can reduce unnecessary changes; swaps may still occur. No universal live position cap was established in this research. |
| [Revert Auto-Range](https://docs.revert.finance/revert/auto-range.md) | Guarded one-position replacement with swap and owner-returned leftovers. That leftover payout is incompatible with PoPL's nonredeemable principal and is not copied. |

Source versions/deployed products differ. Historical inspected Solidity is an
architectural precedent, not a bytecode-verified current deployment. Research
records preserve source pins and confidence limits. Some published Charm guard
prose conflicts with code: increasing allowed TWAP deviation loosens that cap;
Gamma deposit-proxy TWAP controls do not prove classic rebalance-core protection.

## Critical economic result at85%

For one continuous Uniswap range with ZZZ price P in ETH, liquidity L and bounds
D/U, while D<P<U the principal is:

- ZZZ=L*(1/sqrt(P)-1/sqrt(U));
- ETH=L*(sqrt(P)-sqrt(D));
- NAV=ZZZ*P+ETH.

Outside the range, clamp sqrt(P) to the sqrt(D)/sqrt(U) endpoints in the token
amount formulas. The resulting principal is one-sided, never a negative amount.

An illustrative initial centre1/+/-50% range at upper85%threshold P=1.425 holds
about94.15% of value in ETH. A new same-width range centred at1.425 needs about
61.48%ETH/38.52%ZZZ value. The scarce ZZZ funds only about15.18% of portfolio NAV
in that new active main;84.82% becomes initially inactive ETH residual.

| Main width | Price trigger | New active main | Initially inactive residual |
| --- | --- | --- | --- |
| +/-50% | +42.5% |15.18% |84.82% ETH |
| +/-50% | -42.5% |24.49% |75.51% ZZZ |
| +/-25% | +21.25% |15.00% |85.00% ETH |
| +/-25% | -21.25% |18.70% |81.30% ZZZ |

These are independent continuous-range calculations, ignoring fees, gas,
tick spacing/rounding, compound, idle and execution. They are not a backtest or
market quote. Arithmetic percentage bands are not necessarily50/50 at centre.
An operation can preserve NAV yet materially reduce active capital/fee potential.
Current maintenance-loss guards do not measure future utilization or eliminate IL.

Consequently, do not promise simultaneously no swaps, centred symmetric ranges
and most capital active for arbitrary inventory. A minimum-active-capital guard
can also block every illustrated85%adjustment: it needs an explicit waiting or
recovery policy, not a hidden automatic swap or weakened cap.

## Recommended bounded lifecycle

1. Enforce at most two live positions per shared bucket: one main and one optional
   residual, in the same admitted ETH/ZZZ pool. These are not two positions per
   NFT or a tree of pools. All NFTs retain their existing independent shares.
2. At a genuinely eligible portfolio adjustment, harvest both legs into the
   existing fixed80/10/5/5 ledger, close both old positions, combine only attributed
   principal/idle/released compound, deploy the maximum useful new main, then at
   most one residual. Fee/royalty/buyback liabilities cannot fund it. All steps are
   atomic; any failed guard leaves the prior positions/accounting intact.
3. Determine residual direction from actual remaining tokens, not old trigger
   direction. Excess ZZZ is offered above the current ZZZ-in-ETH price; excess ETH
   bids below it. Tick alignment must make it one-sided at mint. Select a reviewed
   governed width; the old centre is not always on the correct side and must not
   be a universal placement anchor.
4. Do not rebuild just because the residual becomes mixed. That is normal market
   trading. Both positions may earn fees; allow them to work until an actual main
   trigger or explicit recovery rule justifies action. Never swap merely to make
   the residual label one-sided again.
5. A residual that crosses fully into the opposite asset can unfill on recross.
   Removing a completed leg prevents that future reversal but leaves attributed
   principal idle. The plan must choose between keeping the passive exposure until
   the next whole adjustment and an explicit completion/idle policy. Closing a
   large residual may breach the current5%idle ceiling and block contributions;
   do not solve this with a sweep, reserve mixing or silent cap relaxation.
6. If both legs hold the same asset, a no-swap main may be empty. Enter an explicit
   inventory-limited state; never advertise active liquidity or invent the other
   asset. Either wait under a strict passive mandate, or execute a separately
   approved, bounded recovery trade. Current claims/funded royalties remain
   independent. New contributions must not subsidize incumbent inventory repair.
7. The smallest first version should avoid third baseline/range legs, volatility
   prediction, staged10%replacement and perpetual secondary-only rebalancing.
   Keeping old main+new main+residual would require three legs. One deterministic
   aggregate portfolio cycle is easier to account/audit than separate managers.

## State cases

| Observed state | Proposed handling |
| --- | --- |
| Main active, residual one-sided | Keep both unless the main's real trigger passes; collect fees independently. |
| Price reverses and both become mixed | Normal. No forced swap/reset; next approved cycle combines actual amounts. |
| Residual fills fully | Conversion is reversible until removed. Apply the explicitly selected completion policy; never create a third leg. |
| Main and residual become the same asset | No two-sided centred main can be funded without reverse market movement, new counterpart inventory or a swap. Show inventory-limited; follow approved recovery policy. |
| Two one-sided legs hold opposite assets | Combine their actual assets at the next valid adjustment; this requires disjoint ranges with price in the gap, not the proposed overlapping geometry. |
| Target/reference disagreement, expired window or failed evidence | No ordinary adjustment. Preserve/reset evidence and independently due harvest/claims. |
| Secondary creation fails, price/policy changes during callbacks | Revert whole adjustment; no half-rebuilt portfolio or orphan leg. |
| Main absent but residual remains | Fresh explicit lifecycle/reader state, not current accounting4 Active/mainId0 contradiction; guard entries and ordinary scheduling accordingly. |

## Anti-manipulation, cost and IL

No-immediate-swap removes that particular balancing-order exposure, not ordinary
LP arbitrage, manipulated range placement or front-running of contributions,
conversions/buybacks. Retain independent-reference corroboration at the SAME85%
thresholds, fresh spot/reference bounds before/after execution, exact deltas,
receipt-backed context and unchanged financial controls. Do not substitute our
own pool spot for independent pricing. Reliable independent TWAP/market data can
corroborate, but actual Robinhood feed/transport qualification remains open.

A fresh random60-300second delay is drawn once per candidate, persisted and
rechecked. Avoid consecutive identical draws if that is the intended requirement;
forever-unique draws from241integer seconds are impossible. Jitter is schedule
obfuscation, not MEV immunity or control over a keeper key using other software.
Protected submission is useful only if the actual chain/provider supports it;
no Ethereum private-relay guarantee is assumed for Robinhood.

Keep hourly harvest independent; do not copy automatic full resets on every
harvest/deposit from another product. Preserve entrant-only swap/deployment,
separate compound timing, manual widths and current loss caps. Select economic
minimums for residual creation/changes and expose active/inactive NAV, inventory,
net fees, gas, spread and source quality. Additional legs are not automatically
more efficient. No-swap management retains IL/adverse-selection risk; moving
ranges alone does not restore historical token quantities or erase losses.

## Implementation and verification sequence

1. Settle recovery mandate, residual width/completion, funding and12hour policy.
   Recommend passive by default with an explicit bounded recovery option, not an
   unconditional claim of no swaps/continuous active liquidity. This is a
   recommendation, not approval to enable that fallback.
2. Use a fresh explicit portfolio/policy/accounting/canonical/read profile. Cover
   both physical NFTs in NAV, marginal LP/share pricing, custody contexts, metadata,
   harvest, compound, park/move/emergency, raw terminal return and pre-exit handoff.
   Do not silently reinterpret amounts(actualId) or old journals. Current Vault
   runtime59-byte and Manager initcode37-byte margins require a measured modular
   refactor before added behavior; no gate relaxation or delegatecall shortcut.
3. Authenticate both leg IDs/owners/keys/ticks/liquidity at one canonical snapshot;
   bind samples/jitter to the entire portfolio and policy revision. Store raw
   threshold evidence separately from execution cooldown. If12hours stays, observe
   during cooldown and require both conditions before drawing the delay.
4. Reuse unchanged evidence; add useful actual-core tests for both directions,
   gaps/trends/chop/reversals, residual fill/unfill, missing counterpart, callbacks,
   concurrent deposits/claims/transfers, mint/close rollback, share conservation and
   all-leg terminal return/canonical closure. Verify actual value, not summed raw
   liquidity units from different ranges. Compare strategy NAV/fees/gas/utilization
   with hold and existing-policy counterfactuals before calling it an improvement.
5. Update source-bound API/keeper/observer/function/operator documentation and
   qualify real dependencies/gas/services separately. Preserve existing services,
   websites, Anvil NFTs/balances/journals, null public config and Anvil-only signer.

This plan introduces no callable function, new operating command or implemented
feature. No contract/service/site/public transaction/test deployment changed.
