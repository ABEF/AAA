# Pool spot price multiplied by ETH/USD

[13November source and market review](../reports/predeployment-qualification-20261113/markets/REVIEW.md)
still qualifies no source pair. Shared-aggregator Chainlink proxies are one
ETH service; Pyth is stale/disagreeing and API3 ETH inactive. No two independent
ZZZ paths are established. Raw activeL cannot choose a truthful reference, and
the deeper known native markets currently conflict with selected-pool bands.
The optional reader, spot choice and every safeguard stay unchanged.

## Scope and economic decision

The user selected **spot for both placement and independent valuation** on
9 November 2026. Activation/growth placement already uses the current destination
pool price, the existing main's fixed bounds, actual-core swap quotes and the
post-swap token requirements. The incoming contribution increases only that main;
it does not recenter either position or reset the rebalance clock.

The optional [ZZZV4SpotPriceFeed](../src/ZZZV4SpotPriceFeed.sol) provides a separate
valuation source: **reference-pool ETH per ZZZ × ETH/USD = ZZZ/USD**, returned with
18 decimals through the existing `decimals()`/`latestRoundData()` source interface.
There is no TWAP, stored averaging history or persistence filter in this reader.
At the high-sqrt fixed-point boundary, ratio truncation can differ from the
exact rational by one USD18 raw unit; this is pricing precision, not a new fee,
claim reserve or permission to loosen a financial floor.
The reader owns no principal, accepts no payments and cannot swap or select a pool.
It does not change the Vault, Strategy, contribution/share accounting or an
existing deployment. Its existence is not live source admission.

This explicitly accepts greater exposure to temporary reference-price changes
than a time-averaged reference. A real liquidity increase and correct token ratio
do not independently establish fair economic value. Existing source agreement,
runtime/round checks, caller floors, swap/spot/additional-loss guards, the default
3% total contribution limit and actual 97% marginal deployed-LP requirement remain.
They constrain execution; they do not make an external spot unmanipulable.

## Choose the reference pool

Prefer the **largest qualifying external ETH/ZZZ pool**, not an automatically
changing TVL leaderboard. Governance reviews and pins one exact reference per
adapter. The LP destination, execution venue and valuation reference are separate
choices. Their identities and dependencies must be recorded independently.

1. Verify the chain, native ETH/fixed ZZZ identity, complete PoolKey/PoolId,
   static fee, zero hook, core and StateView runtime/control identities.
2. Establish liquidity independent of PoPL's main/residual and its attributed
   funds. Review both-direction usable external depth at the intended operation
   sizes. Raw active liquidity and gross/displayed TVL are not interchangeable
   across ranges; neither a TVL label nor the reader's active-liquidity floor
   authenticates ownership or proves executable bidirectional depth.
3. Review the ranking against other compatible candidates at the same block and
   record the prices/method used to value TVL. Short-lived added liquidity,
   inactive ranges, hooks, proxies and shared reporters require separate review.
   An unsupported higher-TVL venue is not made compatible by entering its ID.
4. Establish a **second independently reviewed ZZZ valuation path** for the
   existing two-source Oracle. Two copies of one pool multiplied by different
   ETH feeds still share the same manipulable ZZZ price. The contract's distinct
   `independenceId` values are review assertions, not proof of independence.

The standalone reader enforces its configured active-liquidity minimum but does
not subtract PoPL-owned LP or discover all pools on-chain. Independence/depth
qualification and monitoring are required operating controls. If PoPL later
moves principal into a reference venue, re-review that source before the move;
pool admission does not automatically rotate or repair the price reference.

**Fresh execution-price1 / LP-routing3:** the reference may also be a reviewed
swap venue. [The transaction-only execution context](REFERENCE_SWAP_EXECUTION.md)
keeps the original two-source valuation, verifies the exact quoted own-swap
transition before settlement and rechecks live freshness/agreement and callbacks.
It does not allow the reference to be the same-core PoPL principal destination.
Enable the explicit source proof after dual-feed admission, and adopt matching
LP3 consumers; public Oracle reads remain live. No cap is loosened.

**Historical LP-routing2 compatibility:** that implementation requires the
reference to remain untouched by the complete operation. Contribution finalization freezes source bounds/observations;
Manager's ordinary balance/swap/mint/increase paths also bind the Oracle
fingerprints through `LPBalancer.policyFingerprint`. Reference == LP destination
changes L; reference == executed swap venue can change spot/tick/L. These can
therefore reject activation/growth, rebalancing, compounding, governed LP movement
and Manager-routed buybacks. The earned-LP converter uses its separate output-floor
path; do not infer the identical context-freeze behavior for every conversion.
Explicit governance emergency uses its separately reviewed emergency context;
this ordinary-path incompatibility does not add a new force-operation gate.

For old LP2 deployments, choose references not modified by the operation and
simulate the complete route; they do not inherit the new capability. For the
fresh LP3 graph use the explicit source admission and full-operation procedure
in [reference execution](REFERENCE_SWAP_EXECUTION.md). Existing fingerprints and
financial guards are retained under that transaction-scoped design. The earlier
[decision list](../reports/whole-project-review-20261111/REVIEW.md#decisions-and-release-gates)
is historical evidence of the issue, not approval of a current configuration.

The [dated market review](../reports/market-followup-20261109/REVIEW.md) does not
qualify such a pair or select a production pool, source age or minimum liquidity.
The selected hookless v4 pool has no built-in oracle history; this implementation
deliberately reads spot and does not pretend otherwise. See the official
[Uniswap oracle documentation](https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles).

## Exact constructor settings

Deploy the optional reader with one `Config` tuple in the exact ABI order below.
All addresses, hashes, age and minimum-liquidity values require an actual review;
this document supplies no invented live defaults. The examples are templates,
not a transaction or source qualification.

| Input | Meaning |
| --- | --- |
| `core`, `expectedCoreCodeHash` | Correct-chain v4 PoolManager and exact outer runtime hash. |
| `stateView`, `expectedStateViewCodeHash` | Reviewed StateView and runtime; its `poolManager()` must equal `core`. |
| `key` | Full native-ETH/fixed-ZZZ static hookless PoolKey, including fee and tick spacing. |
| `expectedPoolId` | Exact hash of that complete PoolKey. |
| `zzz`, `expectedZZZCodeHash` | This deployment's fixed ZZZ identity and runtime. |
| `ethUsdFeed`, `expectedETHFeedCodeHash` | Compatible reviewed ETH/USD round source and runtime. Never point back to a dependent Oracle/reader cycle. |
| `maxETHAge` | Positive maximum original ETH observation age, at most one day. |
| `minimumLiquidity` | Positive raw active-liquidity floor for this exact reference pool; not a TVL/depth guarantee. |
| `reviewHash` | Nonzero commitment to the pool/source/control/depth/config review. |

Proxy implementations, administrators, market independence and native-ETH
denomination are not authenticated merely by an outer runtime hash. A correctly
encoded malicious source can lie; source/control review remains necessary.

## Operator procedure and later changes

| Step / call | Input | Expected result |
| --- | --- | --- |
| Deploy `ZZZV4SpotPriceFeed(config)` | Reviewed tuple above | Fixed read-only source |
| Read `config()` / `poolId()` | None | Verify exact reviewed identities |
| Read `latestRoundData()` | None | Positive composite observation |
| Call `Oracle.setDualFeed(...)` | Fixed ZZZ; both complete SourcePolicy tuples; reviewed agreement tolerance (currently 300bps); nonzero review hash | Validate and activate both sources |
| Read `activePolicy(ZZZ)` / `policy(id)` / `priceBounds(ZZZ)` | Exact ZZZ/policy | Verify bounds and fingerprint |
| Fresh execution1 only: `Oracle.setExecutionSource(reader,true,expectedCodeHash,reviewHash)` | Matching admitted fixed-ZZZ reader/runtime; nonzero review hash | Explicit market proof; verify policy/revision and LP3 consumers |

Each adapter SourcePolicy uses that adapter's runtime hash and `feedDecimals=18`,
plus its genuine reviewed independence identity and age bound. Preserve original
ETH timestamps: reading spot does not renew a stale ETH observation or prove a
recent pool trade. The returned round is a synthetic snapshot identity, not a
Chainlink round or proof of a time interval. No market last-swap age is available
from v4 slot0. Missing/malformed state, mismatched pins, inadequate current
liquidity and invalid/stale/future ETH observations fail closed.

Source changes remain immediate-governance operations **after sealing**. Changing
the pool, source, age or liquidity floor deploys a reviewed replacement immutable
reader, then uses the existing `setDualFeed` setter. There is no keeper source
selection, automatic TVL switch or new governance authority. An obsolete source
cannot force a switch to itself. Keep the core's two-source and freshness bounds.

Before adopting a source, stop affected automated price-dependent work, preserve
pending transaction/journal evidence, qualify the complete operation at actual
depth and budgets, review new policy/runtime fingerprints and update matching
consumer configuration. Invalidate/reprepare unsigned reviews against the new
policy. Restart only the services whose installed configuration requires it;
never reset an existing chain or relabel old runtime/journal profiles. Resume
after read-only verification and simulations. Raw funded claims, hourly fee-only
harvesting, raw custody recovery and terminal holder return retain their own
existing requirements; a pricing incident does not invent a new payout authority.

## Verification and open gates

The [scoped implementation record](../reports/composite-spot-price-20261109/REVIEW.md)
separates actual offline Solidity checks from external-market qualification.
Live reference selection/ranking, external depth, the second independent ZZZ
path, ETH feeds/publication/liveness, proxy controls, target-chain gas and
operating recovery remain release requirements. No source is deployed/admitted,
no provider funded, no public transaction submitted and no site/service or
existing Anvil state changed by adding this reader.
