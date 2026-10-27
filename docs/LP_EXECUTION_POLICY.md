# LP execution and operator-selected maintenance

Reviewed 2026-10-27 against source main `9c8a43d`. This is a **design and decision
record**, not an implemented strategy, configured deployment or operating
rehearsal. [Todo](../TODO.md#task-lp-execution-routing) owns implementation status.
Current source, old deployments, journals and sites retain their existing rules.

## Current behavior and requested direction

| Topic | Current source | Requested direction / boundary |
| --- | --- | --- |
| Swap venue | Vault balancing always uses its LP bucket's pool. Buyback accepts an admitted pool; Entry/reward converters have separate typed routes. None discovers a globally best execution. | Select the best executable full-operation result among a bounded set of reviewed ETH/fixed-ZZZ venues, independently of the LP destination. |
| Range choice | Governance selects the desired width; a separate optional keeper policy can automatically select 25%/50%. | Operator selects +/-25% or +/-50% in ZZZ price in ETH. No automatic volatility analysis or range switching is requested for this operating policy. Keep optional automation disabled. |
| Rebalance trigger | Reference displacement from the recorded centre or a pending range change, after the pool cooldown. | Ordinary automatic replacement only outside the actual physical range; requested 12-hour interval, then 1-10-minute service jitter and hourly checks while still in range. Exceptions below need decisions. |
| Contributions | The first activation creates the shared LP; later activations/top-ups increase it at its actual ticks. Balancing can swap attributed idle and released compound. | Keep an existing LP/range; improve marginal-input execution without making contributions an indirect full-bucket maintenance trigger. |
| Residual assets | Attributed idle can already be reinvested, including without new fees, and joins collective principal return. | Combine useful residuals later; no zero-dust target, arbitrary sweep or external recipient. |
| Per-NFT limit | Governance configures cumulative gross contributions through `maxPositionUSD`. | Intended configuration: $1,000,000 per NFT, not a guaranteed current NAV or a shared-market capacity allowance. |

Three consequential decisions were asked and remain pending unless an answer is
recorded here: whether 12 hours is hard even after an earlier range exit; whether
an explicit governance width change may replace still-in-range LP after cooldown;
and whether standalone compounding should receive a separate interval. The current
compound helper uses the pool rebalance interval, so simply setting 12 hours also
delays standalone compound. Do not select these answers by implementation default.

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

An honest keeper can select the best candidate off-chain. A malicious authorized
keeper can ignore that selection. Existing floors must therefore protect every
allowed route. A claim that optimality itself is enforced on-chain would need a
separately reviewed bounded comparison or authentic witness mechanism, with its
gas, quote-manipulation and availability costs. Do not advertise that as existing.

Governance can already admit another native ETH/ZZZ pool through
`PoolRegistry.configureNative(fullConfig)` after sealing, normally keeping its
`depositsEnabled=false` to preserve the one contribution pool. **Admission alone
does not redirect Vault balancing:** `_swap` still uses `p.poolId`. Implement the
new balancing-route boundary before sealing. Thereafter, qualifying/admitting a
compatible future pool should be configuration, not a Solidity edit or LP move.
Existing Entry/converter `addV4Route` policies do not currently control this path.

## Deterministic execution and adjustable economics

The current Strategy already deterministically computes direction, amount and
minimum output from balances, target ticks, prices and directional fees. It does
not optimize across execution pools or fully solve market-depth price impact.
Maintain deterministic on-chain limits while permitting explicit bounded
governance updates to economic policy after sealing.

Current defaults are 2% contribution, 1% conversion and 3% maintenance, each with
a governed 10% hard ceiling. Pool slippage is a **separate** current 2% hard
ceiling; pool/reference deviation and caller minima also remain independent.
Increasing one loss cap does not waive another guard. Parameter loosening is an
explicit acceptance of worse execution, never a retry fallback or guarantee that
a trade becomes possible. Preserve user-signed stronger limits. Empty liquidity,
failed tokens and invalid prices can still make execution impossible. Atomic
failure leaves the old LP intact; paused collective holder return is a separate
raw ETH/ZZZ recovery path, not an unrestricted swap bypass.

The new route design must enumerate each governed setter, default and separate
hard ceiling, including route-level slippage, so a hidden immutable venue gate
does not contradict the promised economic configurability. Its final ceilings
remain a design decision; this record does not silently raise the current 2%
venue ceiling or weaken any caller's signed protection.

## Requested outside-only schedule

This is a proposed scheduler/state policy, **not current source behavior**:

1. Anchor the cycle to confirmed physical LP creation/replacement, not a process
   start, top-up, refresh, failed attempt or last hourly harvest.
2. Apply the requested 43,200-second interval. Explicitly settle whether genuine
   early range exit can bypass that wait. With a hard interval, exit after one
   hour can leave roughly eleven hours without conventional active-range fees.
3. At an eligible evaluation, use the authenticated actual pool tick and the
   physical LP's real ticks. Active range is `lower <= tick < upper`. Preserve
   legitimate downward-boundary slot0 tick semantics; do not infer it from a
   rounded display price or an assumed +/-percentage.
4. If still inside, persist another ordinary evaluation one hour later. Keep
   faster receipt/health observation independent; hourly decision checks can
   add nearly another hour after a later boundary crossing.
5. If outside, choose one OS-CSPRNG delay of 60-600 seconds and persist it with
   deployment, bucket, LP and policy identity. Do not block the event loop or
   redraw on every check/restart. Continue receipt handling and hourly harvest.
6. At the due time, re-read actual range, prices, routes and economics; simulate
   fresh exact calldata. If back inside, cancel the attempt. Submit only when
   the contract's actual outside/cooldown/authorization/execution rules pass.
7. Reset the anchor only after confirmed successful LP replacement. Preserve
   ambiguous hashes, normal nonce recovery and paid-revert backoff. Recovery
   after downtime evaluates current state, never replays missed rebalances.

Jitter is modest schedule obfuscation, not cryptographic protection against MEV
or a keeper that bypasses Python. The twelve-hour lower bound and market state
remain observable. No new VRF service, timestamp-derived secure randomness,
timelock, cumulative-loss breaker or protected-RPC guarantee is selected.

`triggerBps=100` currently means a 1% reference-price movement can permit a
replacement even deep inside a wide range. It is **not** a 1% tolerance for an
imperfect centre. The outside-only design must not accidentally retain that
automatic trading trigger. The user's approximate-centre remark does not select
a new oracle/spot tolerance. Deliberate operator range changes need an explicit
exception decision because they can otherwise remain unapplied indefinitely.

## Harvest, compound and contributions

Hourly harvesting collects actual LP fees and allocates 80/10/5/5 without swaps.
The 5% designated compound becomes a reserve. A later compound harvests first,
pulls that reserve and reinvests it with eligible attributed idle. Thus harvesting
funds compounding; it does not require compounding hourly. Claims run neither job.

Currency-specific `compound_thresholds` already exists. Idle compounding requires
the actual-currency map; reserve-only historical/common scheduling can still use
a shared raw-unit fallback. Do not describe the existing currency-aware feature
as missing. Review explicit ETH/ZZZ economic thresholds for the fresh service;
requiring them in profile4 would be a separate small implementation change.

After the first activation creates a bucket's LP, contributions keep that existing
LP ID/ticks. ETH-only or ZZZ-only funding
may need a swap to match the actual range ratio, which is not necessarily 50/50
and is single-sided outside the range. Review whether entrant-only execution can
leave unrelated incumbent idle/compound for scheduled work. Do not simply remove
compound synchronization: old compound, fees and idle must remain in incumbent
NAV before issuing new shares. Preserve pre-entry harvest/membership checkpoints,
actual marginal deployed floors and failure rollback. Repeated small top-ups must
not become an economical way to force undesirable incumbent turnover.

## One useful balancing swap before residual correction

Prefer a bounded, full-size quote/ratio solver that normally makes one useful
swap and then deposits. Compare final deployable liquidity and residual value,
including fees/impact, rather than solving a fee-free 50/50 split. Current source
permits at most two passes and skips corrections at or below one basis point of
available input. That cutoff is not a USD/gas-aware economic test.

Retain a second correction only if it materially improves the deployed result
after its costs and all existing guards. Do not blindly remove it: historical
thin-market placement motivated it. Record both directions and outputs, including
an opposite-direction correction. Never iterate toward zero dust.

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

On-chain range/cooldown/cap changes are read fresh and normally need no keeper
restart. Local JSON schedule/threshold/route-candidate changes require controlled
restart because there is no hot reload. Reconcile pending intents around either
kind of policy change; a mined transaction cannot be undone by editing config.
Current rebalance calldata does not bind a historical configuration hash.

This review changed documentation only. No ABI, contract, keeper code/config,
deployment, service, journal, site, signer or funds changed. No unchanged Solidity
or keeper regression suite was rerun or relabelled as verification of this design.
