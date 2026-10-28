# LP execution and operator-selected maintenance

Reviewed2026-10-28. Fresh LP routing1 adds bounded reviewed-venue comparison,
depth-aware atomic sizing and entrant-only execution to maintenance policy2 /
Budget3. [Routing review](../reports/atomic-routing-20261028/REVIEW.md) and
[verification](../reports/atomic-routing-20261028/VERIFICATION.md) own the new
source scope; [earlier timing verification](../reports/maintenance-policy-20261027/VERIFICATION.md)
retains its original scope. Actual venue/gas/economic qualification and operating
rollout remain open. The separate [fee-aware execution-quality policy](EXECUTION_QUALITY.md)
adds a governed additional-loss floor without removing all-in limits; its
[review](../reports/fee-impact-policy-20261028/REVIEW.md) and
[verification](../reports/fee-impact-policy-20261028/VERIFICATION.md) own that
later source scope. [Todo](../TODO.md#task-lp-execution-routing) owns status.
Old deployments, journals and sites retain their actual historical code/profiles.

## Current behavior and requested direction

| Topic | Current source | Requested direction / boundary |
| --- | --- | --- |
| Swap venue | Immutable Manager-created LPBalancer compares up to four explicitly reviewed native ETH/fixed-ZZZ static hookless v4 pools and executes the same selected route/size. | Best valid sampled final LP value among this list, not global or exact mathematical optimality. Buyback/Entry/reward converters retain separate routing. |
| Range choice | Governance selects the desired width; a separate optional keeper policy can automatically select 25%/50%. | Operator selects +/-25% or +/-50% in ZZZ price in ETH. No automatic volatility analysis or range switching is requested for this operating policy. Keep optional automation disabled. |
| Rebalance trigger | Policy2 uses actual physical range exit or an explicit operator range change, after the governed hard pool cooldown. | Initial12-hour minimum even after early exit; matching service adds durable1-10minute jitter and hourly ordinary checks while eligible but inside. |
| Contributions | First activation creates shared LP; later activations/top-ups increase its actual ticks. Only the new contribution can be swapped/deployed. | Incumbent idle/compound remains in old share NAV and available for guarded maintenance; it cannot subsidize the new marginal LP floor. |
| Residual assets | Attributed idle can already be reinvested, including without new fees, and joins collective principal return. | Combine useful residuals later; no zero-dust target, arbitrary sweep or external recipient. |
| Per-NFT limit | Governance configures cumulative gross contributions through `maxPositionUSD`. | Intended configuration: $1,000,000 per NFT, not a guaranteed current NAV or a shared-market capacity allowance. |

Settled decisions: twelve hours is the initial hard rebalance minimum even after
an early range exit; deliberate operator width changes may apply after cooldown
while old LP is still in range; standalone compound has a separate configurable
interval and hourly harvesting remains independent. Defaults do not install a
production configuration. Jitter is service-only; outside/cooldown/value guards
are enforced on-chain.

## Execution venue selection

The target is **best valid execution among reviewed candidates at the observed
state**, not a guarantee of globally optimal execution when mined. Compare the
actual required swap amount, directional LP/protocol fees, depth across ticks,
resulting target-position ratio and useful final deployed value, using the same
captured independent price vector and reviewed target-range policy for every
candidate. Value retained idle separately; do not compare raw Uniswap liquidity
units across different ticks or let a route's own quoted USD choose the winner. Gas remains
separate; a lower headline fee or higher displayed TVL does not establish a
better result. Rebalance evaluation must include removing our own old LP first.
Any liquidity we just removed cannot supply that replacement swap.

Use a bounded governance-admitted set of native ETH/fixed-ZZZ static hookless v4
pools on the reviewed venue initially. Avoid generic executors, arbitrary calldata,
new contribution currencies or operator-selected token recipients. Quote and
simulate complete candidate operations at one pinned state. On-chain checks must
retain exact inputs/outputs/recipients, admitted route, actual balance deltas,
fresh prices, captured loss limits, caller minima and final LP/idle accounting.
Fresh inclusion-time guards remain necessary after an off-chain quote.

The comparison now runs on-chain inside `LiquidityManager.balance`, after any
old LP was closed. A keeper supplies no route, direction, swap size or recipient.
The immutable helper uses a fee-aware seed, safeguarded residual interpolation
with midpoint fallback and bounded search with reverted
actual-core quotes. It scores deployed USD at one independent price vector,
retains the no-swap candidate and skips unusable venues. A quote's price/fee/tick
changes are reverted; only the selected swap settles. Gas remains separate.
This deterministic bounded search is approximate; it cannot guarantee a global
optimum, organic pricing, profitability or protection against transaction ordering.

Governance can already admit another native ETH/ZZZ pool through
`PoolRegistry.configureNative(fullConfig)` after sealing, normally keeping its
`depositsEnabled=false` to preserve the one contribution pool. **Admission alone
does not redirect Vault balancing:** governance must also call
`LiquidityManager.balancingRouter().configureExecutionPools(ids,reviewHash)`.
The list has at most four unique admitted pools. An empty list disables swaps;
there is no implicit target-pool fallback. Already balanced budgets can still
proceed; unfillable contributions fail the final LP guard atomically. Removing
all venues needs no healthy prices or venue call. Entry/converter `addV4Route`
policies do not control this list. Future compatible admission/list updates work
after sealing without Solidity editing, redeployment or moving the LP destination.

`LP_ROUTING_VERSION()==1`, immutable helper/core/state/parent bindings and exact
runtime pins identify this new capability independently of Entry routing2.
The Registry's monotonic `configurationRevision`, the helper's catalog/solver
`executionRevision` and Strategy's `executionQualityRevision`, full policies,
source fingerprints and desired target ticks bind the atomic decision. The
quality revision detects changing and restoring the additional-loss setting;
it is separate from the helper revision. Pulls/refunds cannot silently change policy, ownership,
existing LP liquidity or outputs. Both layers verify exact raw balance changes;
manager prefunds are preserved. Historical contracts/readers/journals do not gain
this behavior by relabeling a configuration.

Fee-aware quality explicitly advertises `EXECUTION_QUALITY_VERSION()==1` on
Manager, helper and Strategy while retaining LP routing1. Fresh keeper/API
configs select `execution_quality_version:1`; historical absent/zero profiles
do not probe the new ABI. Same-block observations authenticate the real Strategy
and its forwarded cap, reporting policy owner and quality revision. An unsigned
review reports observed policy, not a frozen inclusion-time setting; the
caller's signed total contribution maximum remains binding.

## Deterministic execution and adjustable economics

Strategy's legacy view plans remain approximate previews. Execution now uses
the typed helper's actual-core depth-aware comparison; those view plans do not
authorize a route or promise the exact final amount.
Maintain deterministic on-chain limits while permitting explicit bounded
governance updates to economic policy after sealing.

Current defaults are 2% contribution, 1% conversion and 3% maintenance, each with
a governed 10% hard ceiling. The separately governed pool-slippage ceiling is
now also 10% (1-1000bps); its operating value is not automatically raised.
The tighter target/selected-venue slippage, pool/reference deviation, captured
operation limits and caller minima remain independent.
Strategy also governs a default1% additional-loss limit after known directional
LP/protocol fees, adjustable0–10% with a nonzero review hash. The output floor
uses conservative independent USD bounds and rounds up; the effective minimum
retains the stronger gross venue and caller floors. Fees still count under all-in
limits. This covers balancing and Manager direct/buyback swaps; separate reward
converters retain their existing all-in conversion controls. It is oracle-relative
loss, including spread/rounding/source uncertainty, not isolated price impact.
See [calculation and capability boundaries](EXECUTION_QUALITY.md).
Increasing one loss cap does not waive another guard. Parameter loosening is an
explicit acceptance of worse execution, never a retry fallback or guarantee that
a trade becomes possible. Preserve user-signed stronger limits. Empty liquidity,
failed tokens and invalid prices can still make execution impossible. Atomic
failure leaves the old LP intact; paused collective holder return is a separate
raw ETH/ZZZ recovery path, not an unrestricted swap bypass.

Governance can call `configureSolver(iterations,quoteGasLimit,reviewHash)`:
default8 iterations and200000gas per attempted quote; allowed4-12 iterations and
100000-300000gas. These are work bounds, not relaxed price/loss guarantees.
The search stops early once deployable value is within0.1% of retained value;
it performs zero or one actual swap, never a second fee-bearing correction.
More venues/iterations can cost more gas; qualify exact settings/depth before
enabling them. Out-of-gas/unfillable quotes cannot spend principal, but can make
an otherwise useful venue unavailable. No automatic widening occurs on failure.
An output/spot-infeasible quote reduces the input ceiling before ratio sizing,
so a large invalid seed cannot permanently hide smaller usable swaps. The work
bound/early stop is a precision/cost policy, not a guaranteed maximum dust amount.

## Implemented outside-only upkeep policy2

The new versioned source implements this scheduler/state policy:

1. Anchor the cycle to confirmed physical LP creation/replacement, not a process
   start, top-up, refresh, failed attempt or last hourly harvest.
2. Apply the configured hard interval, initially43,200seconds. Genuine early range
   exit does not bypass it. Exit after one hour can leave roughly eleven hours
   without conventional active-range fees. Governance may deliberately change
   the interval within supported bounds after observing actual economics.
3. At an eligible evaluation, use the authenticated actual pool tick and the
   physical LP's real ticks. Active range is `lower <= tick < upper`. Preserve
   legitimate downward-boundary slot0 tick semantics; do not infer it from a
   rounded display price or an assumed +/-percentage.
4. If still inside, persist another ordinary evaluation one hour later. Keep
   faster receipt/health observation independent; hourly decision checks can
   add nearly another hour after a later boundary crossing.
5. If outside or an explicit operator range change is pending, choose one
   OS-CSPRNG delay of60-600seconds and persist it with
   deployment, bucket, LP and policy identity. Do not block the event loop or
   redraw on every check/restart. Continue receipt handling and hourly harvest.
6. At the due time, re-read actual range, prices, routes and economics; simulate
   fresh exact calldata. If back inside with no operator range change, cancel
   the attempt. A new explicit width request bypasses the local hourly wait,
   never the hard contract cooldown. Submit only when
   the contract's actual outside/cooldown/authorization/execution rules pass.
7. Reset the anchor only after confirmed successful LP replacement. Preserve
   ambiguous hashes, normal nonce recovery and paid-revert backoff. Recovery
   after downtime evaluates current state, never replays missed rebalances.

Jitter is modest schedule obfuscation, not cryptographic protection against MEV
or a keeper that bypasses Python. The twelve-hour lower bound and market state
remain observable. No new VRF service, timestamp-derived secure randomness,
timelock, cumulative-loss breaker or protected-RPC guarantee is selected.

Historical policy1 used `triggerBps=100` as a1%reference-price movement trigger,
not a centring tolerance. Policy2 retains the ABI field/configuration bounds but
does not let that movement authorize ordinary replacement. Actual tick membership
or the deliberate operator width change decides eligibility after cooldown.
Approximate centring does not select a new oracle/spot tolerance.

## Direct manual execution

An authorized wallet can submit `Vault.rebalance(bucket,minimumLiquidity,deadline)`
at a chosen time. Governance alone does not imply keeper authorization; its
`setKeeper` grant enables the existing capability. The call skips local hourly
checking/jitter only. It retains all on-chain cooldown/range/lifecycle/execution
checks and can be mined later than submission. No force-rebalance bypass exists.
The submitter funds network gas. Reconcile automated pending work first. A manual
transaction from the service's own key outside its journal needs explicit nonce/
receipt/spend reconciliation before restart; new LP/timer discovery does not
adopt it automatically. [Exact procedure](OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time).

## Harvest, compound and contributions

Hourly harvesting collects actual LP fees and allocates 80/10/5/5 without swaps.
The 5% designated compound becomes a reserve. A later compound harvests first,
pulls that reserve and reinvests it with eligible attributed idle. Thus harvesting
funds compounding; it does not require compounding hourly. Claims run neither job.

Currency-specific `compound_thresholds` already exists. Idle compounding requires
the actual-currency map; reserve-only historical/common scheduling can still use
a shared raw-unit fallback. Do not describe the existing currency-aware feature
as missing. Review explicit ETH/ZZZ economic thresholds for the fresh service;
fresh keeper policy2 requires the map for enabled standalone compounding;
historical scheduling retains its old explicit fallback.

After the first activation creates a bucket's LP, contributions keep that existing
LP ID/ticks. ETH-only or ZZZ-only funding
may need a swap to match the actual range ratio, which is not necessarily50/50
and is single-sided outside the range. New contributions now balance and deploy
only their own exact budget, leaving incumbent idle/compound for maintenance.
Old fees/compound remain synchronized and valued for incumbent membership/share
pricing; they cannot mask an entrant's underdeployment. The final independent
LP floor, minimum contribution, caller maximum and all rollback guards still run.
An existing LP ID/range and rebalance clock do not change on a top-up. The wallet
transaction includes conversion and actual LP increase; display/artwork must
wait for its confirmed successful LP state, not an approval or prepared quote.

## One useful balancing swap before residual correction

The new helper replaces the old two-pass loop with one bounded route/size plan,
then zero or one actual swap and LP deployment. Quotes account for actual
directional fees, traversed liquidity and resulting target ratio, including
self-pool price movement. Both directions retain exact input/output guards.
If the bounded search cannot find a usable result, it cannot waive the final
contribution/maintenance floor. Preserve atomic failure and test thin markets;
do not add another swap just to chase rounding dust.

Attributed ETH/ZZZ idle is already recoverable through guarded
`Compounder.compound(bucket,minimumLiquidity,deadline)`, even without fresh fees;
collective exit includes it. Reward fractions, fee-allocation dust, buyback
reserves, royalty cohorts and unclassified prefunds have distinct purposes.
An arbitrary `clear()` would violate those boundaries. See [idle ownership](IDLE_AND_DUST.md).

## Price authority and dependency upgrades

Both the pool price and the configured oracle answers are read on-chain. Use
actual target-pool state to determine active range and actual execution; retain
independent sources for USD minima, NAV and output/value safety. A high-liquidity
pool is useful evidence of executable pricing, not automatically an independent
USD oracle. Same-pool spot as its own safety reference is circular. Source
agreement, spot deviation, execution loss and market loss remain different.

Runtime pins do not necessarily pin a proxy's downstream implementation or
aggregator. Qualify source-specific upstream/admin/upgrade semantics, monitor
changes, and use reviewed adapters with authenticated upstream identity checks
where practical. There is no universal external proxy-storage read available
to another Solidity contract. Off-chain monitoring is not an on-chain invariant.
Governance may rotate to reviewed feed policies/adapters after sealing; never
silently adopt an upstream upgrade or a same-pool/stale/single-source fallback.

## Timed 10% replacement versus a price TWAP

A TWAP oracle averages historical prices. Timed execution divides a trade or LP
replacement over time. Ten same-transaction slices provide no time averaging;
without intervening liquidity changes, they do not remove aggregate AMM impact.

Actual timed 10% replacement might benefit from liquidity replenishment, but
leaves inventory/old-range exposure during completion and creates predictable
repeated flow, more transactions and failure states. Current accounting has one
physical `lpTokenId` per bucket and atomic replacement. Staging would require
old/new positions or controlled idle, combined NAV/fees/shares, entry/claim/
transfer/exit handling, completion/abort/restart and exact partial-state recovery.
An operation cap must not be accidentally applied per slice to permit ten times
the intended aggregate loss. Defer implementation until actual full-size
execution evidence demonstrates that this complexity is worthwhile.

Prioritize atomic reviewed-route execution and a better sizing solver first.
Uniswap v4 has no built-in v3-style oracle history to enable by configuration.
See [Uniswap swaps](https://developers.uniswap.org/docs/get-started/concepts/traders/swaps),
[oracle versions](https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles)
and [Robinhood ordering](https://docs.robinhood.com/chain/).

## Operator configuration and verification

For current implemented calls, use the [operator procedure](OPERATOR_MANUAL.md#operator-selected-lp-policy).
`maxPositionUSD=1000000000000000000000000` is $1,000,000 in USD18; 1,000 fully
funded NFTs could admit $1bn of cumulative contributions. This is not promised
NAV, executable depth or release capacity. No production binding is configured
by this record. Shared exposure must still be supported by real execution depth.

Budget3 compound interval is independent: default3600seconds, governed
`setCompoundInterval(poolId,seconds)` within600seconds-7days, measured after
max(lastCompound,lastRebalance), with due rebalance priority and no clock reset.
On-chain range/cooldown/compound-interval/cap changes are read fresh and normally need no keeper
restart. Local JSON schedule/threshold/route-candidate changes require controlled
restart because there is no hot reload. Reconcile pending intents around either
kind of policy change; a mined transaction cannot be undone by editing config.
Current rebalance calldata does not bind a historical configuration hash.

This execution change adds an immutable helper/new versioned capability and
removes the obsolete Budget `balancePlan` ABI. It modifies keeper/API source;
actual deployments, services, journals, sites, signer policy and funds are unchanged.
Verification is scoped to the delivered execution slice, not economic profitability,
a globally optimal route, a live provider or the deferred timed-replacement design.
