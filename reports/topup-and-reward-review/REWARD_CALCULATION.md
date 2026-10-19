# NFT displayed reward calculation audit

2026-10-19. Internal review of source and scoped fixtures, not live funding proof.

## What each number means

`Rewards to claim` is current unpaid LP (individual plus collective) and royalties.
`Fees generated` for 24h/all-time is **earned history**, including income already
claimed by any holder. It is not another claimable balance. LP principal and the
5% compound / 5% buyback reserves are excluded from holder income.

For a processed LP fee receipt, the 80% individual allocation follows the NFT's
LP shares. Its portion of the 10% collective allocation follows equal eligible
membership. Royalties follow the NFT's eligible rarity weight. Thus the total is
not simply 90% of the gross fees attributed to that NFT's LP.

Example: $100 LP fees, two active NFTs holding 90% / 10% of LP, and $40 royalties
with weights 1 / 3 yield $72 + $5 + $10 = **$87** for the first NFT, and
$8 + $5 + $30 = **$43** for the second, before raw-unit rounding. The remaining
$10 of LP revenue belongs to compounding/buyback. This example checks display
component selection, not a new on-chain fee-processor test.

## Traced implementations

- The static demo's `rewardHistory` sums `individualCents + collectiveCents +
  royaltiesCents + claimedCents + royaltiesClaimedCents`. Claims move balances to
  cumulative paid counters and preserve the earned total. Top-ups only change LP.
  Gross `feesAllTimeCents` / `fees24hCents` never enter this calculation.
- PoPL #444's fixed example credits are $142.32 individual LP, $41.68 collective,
  and $12.50 royalties: **$196.50**. After a combined claim, all-time remains
  $196.50 and available is $0. These are seeded illustrative balances, not a
  reconstruction of 70 days of actual trading or an assumed proportional split.
- The contract-backed client sums only `lp_individual`, `lp_collective` and
  `royalties` current-price USD fields, using exact integers before display
  rounding. NFT/chain/block identity and all nonzero-component prices must match.
  Gross receipts, reserves, conversions, principal and previous payouts are not
  additional inputs. Oversized/invalid aggregate integers now return unavailable
  instead of throwing during rendering.
- The backend replays actual processed ledger allocations with shares, equal
  membership, per-currency royalty cohorts, 1e36 indexes and carried fractions.
  Reconciliation checks LP earned minus paid against current entitlement, and
  royalty earned minus paid/source-converted plus ETH-credited and pending amounts
  against the royalty ledger. Claims/conversions/transfers/imports are not new
  income. Relevant unchanged backend/ledger files match the earlier source-bound
  earnings review; see [bindings](reward-source-review.json).

## Time, pricing and availability

The on-chain history window is `(confirmed timestamp - 86400, confirmed timestamp]`
using processing/allocation time, not necessarily underlying trade time. Both
periods use today's reviewed prices as requested. Converted royalties retain
their original earned currency in history; current claimable reflects actual
remaining denomination. Therefore historical USD earnings minus historical USD
claims is not generally today's claimable USD after price changes/conversion costs.

The saved static demo has no dated net-reward series for its original NFTs.
Its 24h field is **Unavailable**, not gross fees divided by 70, not gross times90%,
and not today's entire claimable balance. New zero-income activations can show0.
The local fixture has no ETH/USD feed, so a nonzero ETH royalty also makes a
combined USD total unavailable while exact raw claimable balances remain usable.

## Checks and remaining boundary

[Six additional display regressions](website-calculation-audit.log) pass:
the exact #444 three-part sum before/after partial/combined claims, no new income
from top-ups/gross fields, equal collective membership example, exclusion of
conversion/principal/reserves/paid totals, rounding only after exact addition,
and missing-price/overflow handling. The [37 affected client cases](website-calculation-client.log)
also pass after the small aggregate-guard change. No unchanged full contract or
backend history suite was rerun for this presentation audit.

Actual receipt ingestion, reviewed prices, production wallets and complete
same-chain predecessor configuration remain essential. See the existing
[history task](../../TODO.md#task-financial-history),
[earnings guide](../../docs/EARNINGS_HISTORY.md) and
[verification](VERIFICATION.md). No new revenue, deployment or real claim occurs
because a number is shown on a card.
