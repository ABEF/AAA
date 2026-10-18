# Dynamic liquidity: internal review - 2026-10-18

**Release remains NOT APPROVED.** This is an internal source/economic review,
not an independent audit, proof of profitability or production qualification.
The [revised brief](PROMPT.md) challenges the supplied prompt; the
[accounting reference](../../docs/DYNAMIC_LIQUIDITY.md) describes the final design.

## Decisions and alternatives

The user approved allowing outside-range activation/top-ups with an explicit
warning, including honest next-rebalance eligibility information. Existing
minimum-input, 99% marginal-deployment, route, custody and price checks remain.
Waiting/queuing deposits would add custody, ordering and cancellation complexity;
forcing rebalance on every contribution would burden entrants and expose a new
maintenance trigger. Neither was introduced. Rebalancing being due does not by
itself invalidate a correctly priced contribution to the current range.

The user separately approved the fixed 3% overall cap for ordinary rebalances,
gas separate. This adds protection across close, swap and mint; it does not relax
the existing per-step minima, price checks or 5% idle ceiling. The existing
immutable helper is reused, preserving Vault size and avoiding parallel formulas.

## Findings and dispositions

| Finding | Disposition and evidence |
| --- | --- |
| **DL-01: fresh USD feeds could coexist with a manipulated LP spot in metadata** | Fixed. `currentValue` now calls the existing exit-price validation before marking actual position amounts. The pre-fix real strategy/manager/metadata test failed exactly at the missing revert. The final test passes; unavailable state preserves ownership, transferability and royalty eligibility. |
| **DL-02: ordinary rebalance lacked one aggregate starting-price execution check** | Fixed under the explicit user decision. Checkpoint 0 precedes harvesting/callbacks, checkpoint 1 includes exact designated compound and checkpoint 2 checks retained LP/idle against the initial vector. Stacked losses, fresh fees hiding loss, callback price changes, donations, reentry and rollback are tested. |
| **DL-03: prepared contributions omitted current-range/maintenance context** | Fixed in backend output. Existing physical LP ticks and current StateView tick determine range activity; strategy eligibility, cooldown and price trigger determine status. Outside-range entry is permitted with a warning and no bypass of normal guards. |
| **DL-04: a 10-minute polling setting could be mistaken for the next execution time** | Avoided explicitly. The warning includes cooldown end/eligible-now/waiting status. Next check and expected execution remain null without qualified fresh keeper telemetry. Hosting/UI telemetry integration remains a central task. |
| **DL-05: a read consumer could retain an old physical LP or mistake contributions for current value** | Backend now exposes current local custody pool/LP ID, share numerator/denominator and cumulative gross contribution separately from `NFT.currentLPValue`. Active/parked local identity and share consistency are checked. Nonlocal states cannot report an available mark. |
| **DL-06: stale physical-position expectations after a signed quote** | Explicit boundary, not claimed solved on-chain. Reprepare on position/range/policy changes before signing. Existing Entry calldata constrains costs, amounts and deadline but has no physical-LP version lock; a signed call can execute after rebalance if all current safeguards pass. |

No accounting dilution defect was reproduced in the inspected current-share
path. This is a scoped result, not proof against every dependency/economic attack.
Share issuance uses the incumbent NAV after entry-induced repricing and settles
old rewards/compound before changing weights. The tests retain the existing
no-retroactive-fees, donation, callback, compound and original-source budget guards.

## Numeric evidence and boundaries

The independent Decimal generator produces 36 price/order/decimal vectors. Actual
manager amount reads and actual strategy plans are compared against those vectors,
including single-token and proportional two-token $100/$10,000 plans. The range
matrix is a read-only synthetic venue with honest test prices; it is not a full
live swap or a stable-input production route qualification. Initial target ranges
recenter at current prices; existing entries use the old physical LP's ticks.

Real Vault/NFT accounting with an explicitly synthetic settlement venue verifies:

- A 500-share-value allocation in $10,000 has 5%: marked value **$500**.
- After an injected 2% total close loss and physical LP replacement: **$490**
  of **$9,800**, with unchanged NFT shares and historical $500 contribution.
- A subsequent 20% price increase gives **$588** of **$11,760**; repeated
  lossless replacement keeps that mark and the same NFT/share identity.
- A $1,000 receipt produces $800 individual/$100 collective/$50 compound/$50
  buyback. The 5% NFT receives **$90** claimable ($40 individual + $50 collective)
  while its NAV becomes **$502.50** from its share of compound. Claim balances
  and buyback are excluded from NAV.
- A later $1,000 entrant buys `floor(oldShares * 1000 / 10050)` and no earlier
  funded fees. Compounding itself changes no share counts.
- Repeated rebalances and an ownership transfer preserve accrued LP/royalty
  rights; the old owner cannot claim. Failed replacement restores old LP custody,
  balances and rights atomically.

The 3% cap is tested at the exact boundary: $2,000 must retain $1,940. A stacked
$68 loss rejects; a stacked $60 loss passes. Fresh compound increases the
denominator and cannot subsidize that limit. Initial oracle/venue honesty and
real execution behavior remain required. Simulated loss injection is not a
measurement of normal Uniswap fees or market performance.

## Static and manual review

Fresh Slither analysis covers all 39 production sources: **376 findings**,
internally reviewed as 155 false positives, 75 accepted risks and 146 informational.
373 detector expression/call-tree reviews remain applicable after explicit delta
inspection and source-location normalization. Two changed rebalance reentrancy
records and the new validation-only ignored return were reviewed separately.
The [current review](../production/slither-review.json) retains exact fingerprints;
the [summary](static-review-summary.json) records coverage and five rejected review
mutations. No matcher was weakened. Earlier canonical review remains archived.

The new helper calls preserve nonReentrant/onlyKeeper/lifecycle guards and expose
no new recipient, spender, upgrade, withdrawal or keeper power. Helper snapshot
state is single-operation, Vault-only and cleared on success; transaction rollback
restores it on failure. Metadata uses static reads and does not affect reward
eligibility. API reads remain pinned to one confirmed hash, with final freshness
and canonicality validation; malformed timing/ranges fail closed.

## Remaining qualification

The [central Todo](../../TODO.md) owns live route/feed/VRF and creator terms,
strategy backtesting, gas/MEV and full configuration stress, independent review,
keeper operating/telemetry rehearsals, live frontend integration and future-chain
portability. The 3% per-operation cap cannot prevent cumulative erosion or
impermanent loss. Wide ranges and polling do not guarantee continuous in-range
liquidity. The selected Pons pool's external revenue is not conventional LP fees.

The website remains a labelled simulation. No website/server change, public
deployment, transaction or monitoring restart occurred. See
[verification](VERIFICATION.md) for actual results and historical evidence limits.
