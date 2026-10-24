# Price security and factual LP verification

## Status and security boundary

The undeployed pricing-V2 candidate combines two-source USD checks with factual
Uniswap position and asset-movement checks. This is implemented protection, not
qualification of live price services. The user-selected disagreement tolerance is **3% (300 bps)**. No production
ETH, ZZZ or USDG source pair, heartbeat, proxy policy or conversion route is
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

## Two sources for every priced asset

[ZZZOracle](../src/ZZZOracle.sol) exposes `PRICING_VERSION() == 2` and
`priceBounds(asset)`. ETH, ZZZ and USDG each need their own approved source pair;
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
separate default 1% execution-loss test described below. Governance can configure
maximum disagreement from 0 to 500 basis points. Zero requires
exact agreement. The 500-basis-point hard ceiling is consistent with the existing
maximum pool/reference-price guard; it is not a recommended production setting or
a claim that 5% uncertainty is safe for an operation with a 1% loss budget.

`priceBounds` returns the minimum, maximum and an observation fingerprint. The
fingerprint binds the chain, Oracle, active asset and sequencer policies and both
complete source rounds. `price` and ordinary `value` use the lower bound.
`quote(input, output, amount)` uses the upper input price and lower output price
to form a strict minimum-output reference. USDG is priced at its actual observed
USD value; no stablecoin is assumed to remain at $1.

There is no automatic single-source, stale-price, last-good-price, target-pool
spot or presumed-peg fallback. The old `setFeed` ABI explicitly reverts. Its
historical `feeds` getter exposes primary metadata only and does not establish
pricing-V2 readiness.

Chainlink's documentation distinguishes source quality, liquidity, stablecoin
and market-integrity risks and places source assessment on the consuming
application. Its API documents round timestamps and precision, which must be
interpreted for the selected feed rather than treated as proof of independence.
[Source selection](https://docs.chain.link/data-feeds/selecting-data-feeds),
[feed API](https://docs.chain.link/data-feeds/api-reference).

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
`ZZZContributionPricing.beginEntry` before pulling tokens, approving routers or
converting assets. The fixed [pricing companion](../src/ZZZContributionPricing.sol)
is created by the Oracle and authenticated to the actual Entry and Vault Budget.
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
it. The default contribution loss limit is 1%; existing governance can configure
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

## Availability, recovery and release qualification

An unhealthy price dependency stops new activation/growth, price-dependent
conversion, maintenance or USD reporting rather than presenting a guessed value.
Already funded raw-unit claims do not require an Oracle price. The separately
approved paused raw custody exit retains its own exact raw minima and explicitly
does not promise a USD loss floor; it cannot automatically replace a failed
normal exit. Pool, token or recipient failure may still prevent movement.

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

The contract companion permits at most 34 marked currencies: the bounded reward
inventory can contain 33 currencies including native ETH, plus an original input
that is not already in that inventory. Current activation/preflight token
inventories remain bounded to 33 total currencies. This work does not widen
those backend limits. A configuration requiring 34 distinct reviewed currencies
cannot be presented as supported by the current preparation profile: it must fail
closed or receive a separately reviewed capacity change and worst-case gas/RPC
qualification. Never omit a required historical asset to fit the inventory.
