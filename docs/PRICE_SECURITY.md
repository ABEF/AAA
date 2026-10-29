# Price security and factual LP verification

Current fresh LP protection uses confirmation2 and separate emergency capability1.
Ordinary readiness requires physical/reference same-side range exit (unless a
reviewed policy relaxation or deliberate governance width exception applies).
Reference prices remain the configured dual USD sources, not a newly qualified
market feed. A separate paused governance emergency may explicitly bypass
financial guards; it preserves exact accounting/custody but can cause near-total
economic loss. It is not a user transaction, keeper fallback or API signing
feature. [Policy](LP_EXECUTION_POLICY.md#independent-reference-in-confirmation2),
[emergency procedure](EMERGENCY_REBALANCE.md).

## Status and security boundary

The [reference-market improvement](../TODO.md#task-rebalance-confirmation-buffer)
is proposed separately from the implemented safeguards below.

## Physical pool and independent reference

Our physical pool's tick determines whether the actual LP is in range; another
pool's tick cannot substitute for it. Current `Strategy.needsRebalance` requires
cooldown/operation eligibility, reads the configured Oracle reference and checks
the managed pool spot against `maxSpotDeviationBps` before testing actual ticks.
Fresh confirmation2 `condition` additionally requires both actual physical and
independent-reference exit on the same side of the identical LP bounds. Target-
only, reference-only and opposite-side exits cannot qualify ordinary upkeep.
Governance may explicitly relax the reference rule with a review hash and sample
invalidation; automatic keeper widths cannot coexist with enabled protection.

On2026-10-29 the user requested corroboration from a reviewed higher-liquidity
market because the managed pool can be manipulated. Selecting that market,
averaging window, real depth, independence and failure/reset behavior remains
unqualified; no deeper-pool/TWAP adapter was added. The new reference-range trigger
uses the existing configured dual USD sources, whose actual independence and
market averaging still require qualification.
Deeper instantaneous spot alone is not manipulation proof, and the greatest
reported liquidity need not mean the best manipulation resistance.

The selected and implemented confirmation2 rule requires independent-reference
and physical exit on the same side through the sampled window. It can deliberately
leave the physical LP inactive during disagreement; governance may explicitly
change the reviewed reference requirement, invalidating samples. Actual deeper-
market/provider/window selection remains unqualified. Preserve actual ticks,
dual-source USD valuation, identity/policy resets and ordinary execution floors.
No automatic reference rotation or use of our own LP as an independent source is
implied. Concrete market/window selection requires source/operating qualification.

## Implemented valuation boundary

The undeployed pricing-V2 candidate combines two-source USD checks with factual
Uniswap position and asset-movement checks. This is implemented protection, not
qualification of live price services. The user-selected disagreement tolerance is **3% (300 bps)**. No production
ETH or ZZZ source pair, heartbeat, proxy policy or conversion route is
selected or qualified by this document. Production remains unapproved.

Two different questions must be answered:

| Question | Evidence |
| --- | --- |
| Did the stated assets enter the authorized operation and actually increase the Vault's LP? | Exact transfers, native settlement, pool/range/owner binding and PositionManager liquidity changes. |
| What is that input and LP inventory worth in USD? | Two independently qualified USD price sources per economic asset, with freshness and disagreement checks. |

The first is an on-chain accounting fact. The second remains a market valuation
with provider, market, governance and common-mode risks. Correct token amounts
cannot prove that an oracle's dollar price is true. Conversely, matching oracle
prices cannot prove that liquidity was deployed.

## Feed fees and recorded reference prices

The Oracle adds no separate percentage or LINK payment for price reads. Ordinary
public Chainlink push-feed getters have no per-read LINK charge. On-chain reads
consume transaction gas; off-chain eth_call has no transaction gas fee but RPC,
custom data/provider and hosting bills may apply. The 500,000-gas source-call
limit is a ceiling, not a flat charge. Actual provider terms and full-operation
gas are release work; VRF/data-reporting products are separate services.

[The dated25October observation](../reports/price-reference-20261025/OBSERVATION.md)
is candidate research, not configured PoPL output. Its ETH round was last updated
the previous evening; ZZZ was calculated from instantaneous pool spot. The
catalog's second Shared-SVR proxy does not supply independent coverage. Record
current quote block/time, source update time and provenance separately; never
copy these values into a live policy or presume future freshness/free service.

## Two sources for every priced asset

[ZZZOracle](../src/ZZZOracle.sol) exposes `PRICING_VERSION() == 2` and
`priceBounds(asset)`. ETH and fixed ZZZ each need their own approved source pair;
one ETH/USD feed plus one ZZZ/USD feed is not redundant pricing for either asset.
Native ETH is address zero with 18 decimals, without a token runtime or wrapper.

Governance calls `setDualFeed` with two source addresses, their runtime hashes,
distinct nonzero independence IDs, each source's decimals and maximum age,
maximum disagreement and a review hash. Each replacement is a new immutable
policy record; `activePolicy`, `policy`, `policyCount` and `policyAt` expose its
current selection and append-only history. Configuration uses existing immediate
governance authority. This introduces no new timelock.

Every price read requires both sources to:

- Match their approved source runtime and declared precision.
- Return bounded, correctly encoded round data with a positive answer, complete
  round identity and correctly ordered, nonzero timestamps.
- Be fresh at the current block, with no future update timestamp.
- Normalize to a positive USD18 value no greater than `1e36`.
- Agree within the asset's configured tolerance, measured against the lower
  answer. Rounding cannot admit a spread just outside that tolerance.

Price-source, asset-decimals and configured sequencer calls have a 500,000-gas
ceiling and exact 32-byte decimals / 160-byte round responses. Oversized replies,
noncanonical round widths and revert data cannot bypass those boundaries. These
are implementation limits to qualify against actual providers,
not measured live-service requirements. Maximum source age is bounded to one day;
the approved operational age must reflect the asset and feed heartbeat.

The intended configuration uses **300 basis points (3%)**. An observation at
exactly 3% is within that band; anything above it fails. This does not relax the
separate default 2% contribution execution-loss test described below. Governance can configure
maximum disagreement from 0 to 500 basis points. Zero requires
exact agreement. The 500-basis-point hard ceiling is consistent with the existing
maximum pool/reference-price guard; it is not a recommended production setting or
a claim that 5% uncertainty is safe for an operation with a 1% loss budget.

`priceBounds` returns the minimum, maximum and an observation fingerprint. The
fingerprint binds the chain, Oracle, active asset and sequencer policies and both
complete source rounds. `price` and ordinary `value` use the lower bound.
`quote(input, output, amount)` uses the upper input price and lower output price
to form a strict minimum-output reference. An optional admitted royalty or
conversion currency needs its own reviewed source pair whenever an operation
values it; no stablecoin is assumed to remain at $1. Those currencies are not
activation inputs.

There is no automatic single-source, stale-price, last-good-price, target-pool
spot or presumed-peg fallback. The obsolete `setFeed` setter and single-feed shadow getters are absent from
the current contract. Historical reader profiles retain their original semantics
and do not establish pricing-V2 readiness.

Chainlink's documentation distinguishes source quality, liquidity, stablecoin
and market-integrity risks and places source assessment on the consuming
application. Its API documents round timestamps and precision, which must be
interpreted for the selected feed rather than treated as proof of independence.
[Source selection](https://docs.chain.link/data-feeds/selecting-data-feeds),
[feed API](https://docs.chain.link/data-feeds/api-reference).

## Compatible source readers

The optional [Pyth Core reader](PYTH_PRICE_SOURCE.md) supplies the compatible
round interface with precision, confidence, publish-time and runtime checks.
It does not update feeds, select a source or prove independence. Confidence
screens a midpoint rather than widening the Oracle bounds. Source proxy and
updater qualification remain separate. ZZZ still requires two independent
qualified observations even when ETH is the activation input.

## Independence and governance still require review

Different addresses, runtime hashes or independence IDs do not prove independent
prices. Two adapters can share one underlying reporter, exchange, pool, bridge,
USD reference or administrator. A source derived from the contribution pool's
own instantaneous spot price is not independent confirmation of that pool.
Two providers covering the same sole thin market can also share its manipulation
risk. A website API quote is not an on-chain feed without a separately reviewed
authenticated adapter and its explicit trust model.

The review must identify underlying markets and reporters, shared dependencies,
market depth, manipulation cost, depeg behavior, heartbeat and deviation
settings, and source upgrade/administration authority. Runtime pins detect
runtime changes; a proxy may keep the same runtime while its implementation,
configuration or upstream data changes. Review those mechanisms and retain the
required additional getter/storage pins and operating monitoring.

Both sources must agree, so either source's outage can stop a contribution. If
both sources fail together or agree on the same wrong value, two-of-two pricing
cannot identify that error. Governance can also admit unsafe sources despite
their labels. Independent qualification, restricted operating procedures and
reviewed deployment pins remain necessary.

The selected pool is hookless. Uniswap v4 separates optional oracle functionality
from its core concentrated-liquidity mechanism; reading its current `slot0` is
not an independent historical TWAP. A TWAP needs an actual reviewed history
mechanism and manipulation assessment.
[Uniswap v4 whitepaper](https://app.uniswap.org/whitepaper-v4.pdf).

## One contribution, one frozen price basis

[Activation Entry](../src/ZZZActivationEntry.sol) calls
`ZZZContributionPricing.beginEntryReviewed` before pulling tokens, approving routers or
converting assets. The caller supplies `maximumLossBps` through
`Entry.executeReviewed(Request,maximumLossBps)`. The captured governed cap must
not exceed that signed maximum before funds move. Release/preparation profiles
require `review_policy_version: 1`; old execute is not a current alternative.
The fixed [pricing companion](../src/ZZZContributionPricing.sol) is created by the Oracle and authenticated to the actual Entry and Vault Budget.
It holds no user funds, approves no assets and supplies no arbitrary executor or
sweep path.

The original source and both LP currencies receive cached lower/upper prices,
decimal scales and fingerprints. Contribution and venue limits are captured before
the original source transfer/conversion as well. Budget adoption must match those
exact limits; a callback cannot substitute a later wider or tighter setting. Source admission remains governed through
[Activation Assets](../src/ZZZActivationAssets.sol). A direct Vault contribution
captures the corresponding basis before receiving assets. The Budget authenticates
the exact NFT, pool, original value and packed raw pair amounts; it cannot adopt
another caller's pending contribution.

[Vault](../src/ZZZVault.sol) and [Budget](../src/ZZZMigrationBudget.sol) value
incumbent LP, attributed idle, fresh compounding and final LP using that same
lower-price vector. The intentional balancing swap can reprice incumbent LP;
the incumbent mark is recomputed after that swap before measuring new deployment.
It is not counted as newly contributed value. The final check requires unchanged
source policies and full observation fingerprints, not merely matching final
numeric answers.

The contribution's lower input valuation must meet the on-chain activation or
growth threshold, currently $100 or $5 respectively. Its **upper** input value is
used for the captured execution floor, while incremental LP is valued with the
frozen **lower** pair prices. Both net new backing and marginal deployed LP must
meet the floor; incumbent idle, old LP and historical compound cannot subsidize
it. The default contribution loss limit is 2%; existing governance can configure
future limits up to the 10% hard maximum. Stronger venue/caller minima remain.
See [execution-loss policy](EXECUTION_LOSS_POLICY.md).

Price disagreement consumes some of the available execution margin. A quote can
therefore fail despite a cheap swap if the approved price bounds are too wide.
The safe response is to reject or obtain a new qualified quote, not silently
widen the loss cap or substitute one source. Network gas is separate.

### Historical compound discovered during settlement

Previously nonzero old-currency compound is marked at the starting checkpoint.
An asset with zero recorded compound may first receive historical funding during
fee synchronization. The final checkpoint marks that newly discovered backing
before its fingerprint check, without overwriting any existing mark. It affects
only incumbent historical backing in the share-issuance denominator. It never
counts as new LP, pays the entrant's execution loss or gives the entrant old
rewards. Unavailable prices for nonzero historical backing fail closed; an unused
zero-balance asset need not become a new price dependency.

## Verify the actual LP, not a quoted dollar figure

[Liquidity Manager](../src/ZZZLiquidityManager.sol) verifies the actual
PositionManager pool key, tick range and Vault ownership and requires the exact
expected increase in on-chain liquidity units. It checks raw asset spending,
unused refunds, native settlement and previous balances, excluding unrelated
prefunds and donations.

A static hookless mint/increase does not itself change the pool price. The
manager requires the same exact spot before and after token pulls, approvals,
settlement and refunds. The pricing companion also captures spot before Vault's
deployment approvals and verifies it after deployment and at final accounting,
covering callbacks outside the manager. Entry keeps the basis until approval
resets and final owner/balance checks finish. A changed spot, round, policy,
unexpected debit or insufficient LP reverts the entire contribution.

The contribution's LP USD value is calculated from actual liquidity units, ticks
and current pool inventory using the frozen price basis. Ordinary current-value
reporting obtains fresh bounds; the contribution snapshot does not fix an NFT's
USD value forever. A pool's instantaneous spot remains
subject to the independent-reference deviation guard. These checks bound
execution; they do not eliminate market risk, impermanent loss or every possible
MEV cost within an explicitly allowed execution budget.

Fresh LP routing1 additionally binds source fingerprints, full Registry policy
and monotonic revision, reviewed execution revision and derived target ticks
across Vault approvals/balancing/resets. Actual-core quotes revert simulated
state; the selected exact-input swap must match quoted output/post-price.
Only the entrant budget can be swapped and deployed. Old idle/compound remains
in incumbent NAV, but only repriced old physical LP is subtracted from the final
physical LP to measure new deployment. Exact raw deltas exclude prefund subsidy.
See [routing review](../reports/atomic-routing-20261028/REVIEW.md). These are
execution protections, not new Oracle providers or independence qualification.

## Availability, recovery and release qualification

An unhealthy price dependency stops new activation/growth, price-dependent
conversion, maintenance or USD reporting rather than presenting a guessed value.
Already funded raw-unit claims do not require an Oracle price. Governed paused parking and terminal collective holder close instead use their
own reviewed raw minima without a USD-loss promise or external custody address.
A separate [manual emergency manifest](EMERGENCY_REBALANCE.md) may explicitly
bypass selected price/financial checks, accepting potentially near-total loss;
it is never an automatic fallback. Venue/token/receiver failure can still prevent
closure or delivery.

The [backend policy codec](../zzz_ops/price_policy.py),
[activation configuration](../frontend_api/activation_config.py),
[trace verifier](../frontend_api/activation_trace.py) and
[earnings pricing](../frontend_api/earnings_prices.py) use explicit pricing
profiles, confirmed-block timestamps, reviewed policy identities and exact source
observations. Historical single-feed profiles retain their original meanings;
they are not silently promoted to V2. Unknown values remain unavailable.

The [production preflight](PRODUCTION_PREFLIGHT.md) separates approved policy,
actual observation and independent qualification. Release still needs actual
source addresses and adapters for every required asset, source/proxy review,
the selected 3% tolerance and qualified heartbeats, funded conversion routes, target-chain
gas and outage rehearsals, and independent audit/remediation. In particular, do
not enable ZZZ contributions if two defensible independent sources cannot be
qualified. No real provider or public deployment is established by mock tests.

## Execution cost without stale-price caching

One Strategy swap/compound plan reads each asset's complete dual-source bounds
once into memory. It computes the same lower-price inventory, reference ratio,
directional venue fees and upper-input/lower-output quote with the original
rounding order. The snapshot ends when that read-only call returns; there is no
persistent, cross-transaction or last-good-price cache. Actual execution and the
final contribution checkpoints still independently validate prices, fingerprints,
spot and physical LP. Shared reference arithmetic lives in an internal library;
it is not another deployed authority or configurable dependency.

Contribution marks pack the two bounds into one slot, with an explicit range
check before narrowing. The Oracle's `1e36` maximum fits in each `uint128` field.
Event/basis encoding keeps the same padded values and field order. Reward
checkpoint loops read eligibility or bucket/shares once before their local
arithmetic; no mutable dependency call occurs inside those loops.

Admission no longer repeats source validation that is already performed by its
round read. A same-currency quote validates its source pair once before returning
the unchanged amount; an unhealthy source still fails. The [security and cost
review](../reports/onchain-safety/REVIEW.md) and [scoped measurements](../reports/onchain-safety/VERIFICATION.md)
describe failure reproductions, accounting parity and local gas limits. No loss
floor, approval, owner check, runtime pin or source-independence requirement is
relaxed to save gas.

### Bounded inventory capacity

The pricing companion has a defensive ceiling of 34 marked currencies. The
current release accepts only ETH and fixed ZZZ as original inputs; both already
belong to its admitted LP-reward inventory. Backend inventories remain bounded
to 33 currencies, including native ETH. That bound is not permission to add a
third activation asset or omit required historical backing. Any future expansion
would require explicit compatible code, inventory and worst-case gas/RPC review.
