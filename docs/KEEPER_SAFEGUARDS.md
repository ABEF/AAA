# Keeper safeguards

Reviewed 2026-10-28 against the [two-day reviewed candidate](../reports/two-day-audit-20261028/VERIFICATION.md) (LP implementation `1cabb85`): accounting4, Strategy maintenance2,
Budget compound3 and LP routing1. The later [execution-quality1 review](../reports/fee-impact-policy-20261028/REVIEW.md)
adds an independent fee-aware floor; it does not relabel earlier evidence or
deployments. Entry source-routing2 is a separate capability.
**Undeployed candidate; production NOT APPROVED.** This inventory describes
implemented protections, not installed service settings or an independent audit.

**Contract guards constrain direct keeper calls. Service controls such as jitter,
simulation and local gas budgets can be bypassed by a malicious keeper key.**
Governance retains immediate configuration authority within supported bounds.
The twelve-hour interval is the selected initial setting, not an immutable limit.

Use the [operator manual](OPERATOR_MANUAL.md) for exact calls and stop/recovery,
[execution policy](LP_EXECUTION_POLICY.md) for current semantics and
[sole Todo](../TODO.md#task-security-keeper-manipulation) for unfinished qualification.
This file is explanatory documentation, not another task ledger.

## 1. Architecture and keeper authority

- **Limited keeper permissions.** The keeper cannot change price feeds, loss limits, approved pools, routing policy or governance settings.
- **Fixed execution paths.** No arbitrary contract calls, arbitrary calldata or keeper-selected payment recipient.
- **Funds stay in protocol contracts.** Principal does not pass through the keeper’s wallet or compounding coordinator.
- **Sealed module bindings.** The keeper cannot substitute another implementation or executor.
- **Fixed assets.** Principal uses native ETH and the deployment’s fixed ZZZ token; the keeper cannot substitute another token or burn target.
- **Restricted venues.** LP execution supports admitted, static-fee, hookless ETH/ZZZ v4 pools with checked contract identities and wiring.
- **Shared LP management.** Maintenance operates per shared bucket, avoiding 1,000 separate NFT rebalances.
- **No principal sweep or external custody recipient.** Routine maintenance cannot send everyone’s liquidity to an arbitrary address.

## 2. Deterministic routing and swap execution

- **On-chain route comparison.** LP balancing compares up to four governance-reviewed execution pools. These are swap venues, not four separate NFT liquidity positions.
- **Separate swap venue and LP destination.** A better execution pool can supply the swap while liquidity returns to the intended LP pool.
- **Post-removal depth.** Rebalance quotes happen after closing our old LP, so the calculation cannot rely on liquidity we just removed.
- **Actual-size quotes.** Quotes account for directional fees, liquidity across ticks, price impact and the resulting LP ratio.
- **Independent valuation.** Candidates are compared by useful deployed value using the same independent price vector—not headline fees, displayed TVL or raw liquidity units.
- **Contract-calculated direction and amount.** For LP balancing, the keeper cannot simply choose an unfavorable swap size, direction or route.
- **Quote/execution matching.** Actual output and post-swap price must match the selected quote.
- **Zero or one actual balancing swap.** The former second fee-bearing correction is removed.
- **Safeguarded sizing.** Interpolation improves precision; bounded fallback search handles difficult cases. An oversized invalid quote cannot hide smaller valid trades.
- **Bounded work.** Venue count, search iterations and quote gas are capped.
- **No hidden fallback.** An empty execution catalog disables swaps; execution does not silently switch to an unapproved pool.
- **Reverted quote effects.** Simulated quotes do not leave behind price changes, fees or token movements.

These controls provide the best sampled valid result among the reviewed candidates, not a guarantee of globally optimal execution. [Routing implementation and review](../reports/atomic-routing-20261028/REVIEW.md).

## 3. Price-manipulation protections

- **Two USD sources per priced asset.** ETH and ZZZ each require their own reviewed source pair.
- **Source-disagreement rejection.** The selected policy is 3%; excessive disagreement stops the operation.
- **No automatic price fallback.** The system does not silently substitute a single feed, assumed dollar peg or the pool’s own spot price.
- **Feed validation.** Checks include approved code, decimals, positive answers, valid rounds, freshness and nonfuture timestamps.
- **Bounded feed calls.** Gas and response sizes are bounded.
- **Sequencer checks where configured.** The sequencer must be healthy, followed by a one-hour recovery grace period.
- **Independent spot/reference checks.** Pool execution prices must remain within their configured deviation from the independent reference.
- **Actual pool-state validation.** Price, tick, fee and physical-range observations must be consistent, including legitimate boundary ticks.
- **Conservative valuation.** Upper input prices and lower output/LP prices make execution floors harder to satisfy.
- **Captured valuations.** Maintenance measures retained value against its starting price vector; repricing cannot simply conceal execution loss.
- **Fee-aware additional-loss floor.** Current directional LP/protocol fees are separated from a default1% additional oracle-relative allowance. Conservative output bounds supplement existing gross/aggregate/caller limits; known fees remain costs under those limits. Spread, source uncertainty and rounding also consume the allowance, so it is not isolated AMM impact.

Two different feed addresses or matching answers alone do not prove independence. [Price-security rules](PRICE_SECURITY.md).

## 4. Implemented settings and limits

These are distinct protections; increasing one does not remove the others.

| Control | Current candidate policy |
| --- | --- |
| Contribution execution loss | 2% default; actual marginal deployed LP must satisfy the floor |
| LP/royalty conversion loss | 1% default, plus any stronger submitted output minimum |
| Maintenance loss | 3% default, covering retained LP plus attributed idle |
| Governance ceilings | The three loss categories can be configured up to 10% |
| Venue slippage | Governed 1–1,000 bps; balancing uses the tighter target/selected-venue value |
| Additional execution loss after known fees | 1% default; Strategy governs 0–1,000 bps with a nonzero review hash; existing all-in limits remain |
| Spot/reference deviation | Governed 1–500 bps, separate from source agreement |
| Final idle ceiling | 5%, with positive deployed LP required |
| Caller protection | Minimum LP/output amounts remain enforced |
| Contract deadline | No more than 10 minutes ahead |
| Solver | Default 8 iterations, governed 4–12 |
| Quote gas | Default 200,000, governed 100,000–300,000 per attempt |
| Contribution minimums | $100 activation / $5 growth, subject to stronger pool minimums |
| NFT contribution ceiling | Governed cumulative per-NFT maximum; intended setting $1 million |

Network gas is separate. Operating limits are not automatically increased after failure.
[Loss-policy explanation](EXECUTION_LOSS_POLICY.md) and [fee-aware calculation](EXECUTION_QUALITY.md).

## 5. Rebalance timing and unnecessary-turnover prevention

- **Outside-only ordinary rebalancing.** A 1% price movement or imperfect centring no longer authorizes replacement.
- **Hard configured cooldown.** The selected initial interval is 12 hours, even if liquidity leaves range earlier.
- **Governance-controlled interval.** Supported bounds remain 10 minutes–7 days.
- **Operator-directed range changes.** Your deliberate width change can apply after cooldown while the old LP remains in range; the keeper cannot invent that request.
- **Manual range selection.** The chosen operating policy uses your ±25%/±50% selection, with automatic selection disabled.
- **Separate compound clock.** Default one hour after the later of the last compound or LP replacement.
- **Rebalance priority.** Compounding yields to eligible rebalancing and cannot reset or postpone the rebalance clock.
- **Persistent 1–10-minute jitter.** The service draws and saves one random delay; restarting, harvesting or topping up does not redraw it.
- **Five-minute eligible checks with confirmation1.** After cooldown, the fresh worker samples every300seconds inside/outside; historical policy2 keeps hourly inside checks. Receipt handling and independent harvest remain separate.
- **Fresh eligibility rechecks.** Ordinary scheduled work is cancelled if liquidity returns inside before submission.
- **Independent hourly harvesting.** Harvesting performs no swaps. `Vault.collectFees` is permissionless, but cannot initiate rebalancing or spend principal.
- Claims trigger neither compounding nor buybacks.
- **Currency-specific compound thresholds.** ETH and ZZZ are checked separately rather than adding incompatible raw units or continually chasing tiny dust.

[Current timing policy](LP_EXECUTION_POLICY.md).

Fresh confirmation1 enforces15-minute sampled confirmation with selected strict
maximum gap300seconds, restarting on observed failure, side/LP/policy change or
staleness. Constructor gap0 blocks ordinary readiness until reviewed configuration.
Budget gates execution and rechecks stable controls across the whole operation.
Matching worker records/clears observations with canonical receipts and keeps
samples fresh during post-ready jitter. Hidden moves between observations and
publicly visible pending upkeep remain limitations; strict300-second cadence/gap
can repeatedly restart with receipt delays. No uninterrupted-price or MEV guarantee.
[Exact policy](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer).

## 6. Deposit, accounting and callback protections

- **Entrant-only execution.** Activation and growth cannot force existing holders’ idle funds or compound reserves through a swap.
- **Existing range preserved.** Contributions increase the current physical LP rather than forcing a new range.
- **Actual marginal LP measurement.** Old principal, idle, compound and donations cannot disguise an underdeployed contribution.
- **Incumbent repricing retained.** Existing LP is valued correctly before issuing new shares.
- **Old fees settled before membership changes.** New activations cannot capture earlier funded income.
- **Self-swap fees separated.** Fees generated during entry belong to the existing membership, not to newly contributed principal.
- **Exact approvals, transfers and refunds.** Spending and receipts must match measured balances; approvals are cleared.
- **Prefund isolation.** Accidental balances cannot subsidize an operation or another holder.
- **Physical LP verification.** The actual owner, pool, ticks and liquidity increase are checked.
- **Reentrancy and authenticated callbacks.** Unexpected callers or altered callback payloads reject.
- **Configuration-change detection.** Registry/helper revisions and Strategy's separate quality-policy revision detect settings changed and then restored during callbacks.
- **Complete execution context.** Source fingerprints, pool policies and target-range settings are checked across approvals, balancing and resets.
- **Completion authorization checks.** Rebalance, compound and buyback recheck keeper authorization and pause state after external work.
- **Atomic failure.** A failed final guard reverts the swaps, LP changes and accounting together. Spent gas remains spent.
- **Separated liabilities.** Holder rewards, compound reserves, buyback reserves, royalties and principal cannot be treated as interchangeable funds.

## 7. Buyback and conversion safeguards

- **Designated reserves only.** Buybacks cannot consume principal or holder claim backing.
- **Fixed ZZZ target.** The keeper cannot buy and burn another token.
- **Per-trade USD ceiling.** Uses the upper source price, rounded upward; governance’s operating ceiling cannot exceed the deployment maximum.
- **Immediate buyback stop.** Setting its operating limit to zero stops new buys.
- **Actual burn verification.** Checks both the ZZZ balance decrease and total-supply reduction.
- **Fixed-ledger conversions.** Approved routes convert only authorized earned balances and return ETH to the same accounting domain.
- **Exact receipts and minimum outputs.** Conversion cannot replace missing proceeds with another reserve.
- **Manager buyback floor.** Direct Manager swaps also enforce the fee-aware quality minimum and retain a positive caller minimum. Separate V3/V4 LP-reward/royalty converters retain their existing all-in conversion limit (default1%); the new additional-loss cap does not apply to them.

Buyback routing remains separate: the keeper chooses a permitted amount,
admitted pool and execution time, subject to the output guards above. LP venue
comparison does not automatically choose routes for buybacks or reward conversion.

## 8. Keeper software and infrastructure safeguards

These protect the automated service; they are not substitutes for contract guards.

- Dry-run default and explicit reviewed live configuration.
- Chain, signer, contract-code, module-binding and capability checks.
- Canonical-block observations and fresh-head validation.
- Explicit quality1 capability checks on Manager, Balancer and actual Strategy, including same-block policy-owner/quality-revision validation and forwarded-cap agreement. API reviews expose the metadata; current keeper health/logs do not. Historical absent/zero configurations retain their old ABI reads. Reviews do not freeze quality policy until inclusion; signed caller loss limits remain binding.
- Exact transaction simulation before signing.
- Gas-limit, gas-price, per-transaction and daily spending ceilings.
- Reviewed fee accounting, including applicable L1 costs.
- One pending transaction lane with nonce reconciliation.
- Durable intent saved before the signer can broadcast.
- No automatic resend after a timeout or ambiguous submission.
- Pending recovery before new work, including during router outages.
- Canonical receipt, confirmation, reorg and checkpoint checks.
- Actual spending recorded, including reverted-transaction gas.
- Persistent failed-action cooldowns and bounded retry/backoff.
- Failed transactions remain visible in health reporting.
- Local process locking, private runtime files and protected keystore access.
- Strict RPC responses, chain checks, rejected redirects and bounded responses.
- Sanitized logs and configuration-bound health records.
- Optional progress watchdog for stalled execution.
- Failure isolation: unavailable swap maintenance does not automatically block independently guarded harvesting.
- Durable job rotation prevents principal-return attempts from taking every serial submission slot. Confirmed batches use a persisted retry interval even if every receiver rejected payment; actual paid flags remain on-chain. See the [recovery procedure](KEEPER_RECOVERY.md#optional-automatic-principal-delivery).

## 9. Emergency containment

- Governance can revoke a compromised keeper.
- Guardian/governance can pause relevant activity.
- Individual pool deposits/operations can be disabled without healthy prices.
- The swap catalog can be cleared without querying failed venues.
- Governed parking or collective holder return provides recovery without forcing an unacceptable swap.
- Emergency recovery retains authorization, actual backing, raw minima and protected destinations.

## What remains exposed

- A malicious keeper key can bypass Python jitter, simulations and software gas budgets; it still faces the contract guards.
- Per-operation limits do not impose a cumulative-loss budget.
- Front-running, back-running or profitable execution inside allowed tolerances is not ruled out. A malicious keeper can trade personally around its chosen eligible submission time; deterministic sizing and cooldown constrain that opportunity but do not prove it unprofitable. Outside traders may attempt the same surrounding trades.
- Governance can immediately loosen permitted settings or approve unsafe dependencies.
- Feed independence, real depth/fees, transaction ordering, operating deployment and independent audit remain qualification work.

No immutable 24-hour rule, cumulative-loss breaker, qualified private-ordering
service or MEV-immunity guarantee is implemented. Local process locking is not
distributed old-host fencing; runtime pins do not universally freeze proxy or
upstream behavior. A failed atomic operation still spends network gas, and a
separately confirmed approval is not reverted by a later failed contribution.

## Code and evidence

- [Strategy](../src/ZZZStrategy.sol), [LPBalancer](../src/ZZZLPBalancer.sol),
  [LiquidityManager](../src/ZZZLiquidityManager.sol), [Vault](../src/ZZZVault.sol),
  [Budget](../src/ZZZMigrationBudget.sol) and [Oracle](../src/ZZZOracle.sol).
- [Buyback](../src/ZZZBuyback.sol), [conversion guards](../src/base/ZZZRewardConverter.sol),
  [keeper](../keeper/monitor.py), [RPC](../zzz_ops/rpc.py) and [journal](../zzz_ops/state.py).
- [Atomic routing review/verification](../reports/atomic-routing-20261028/VERIFICATION.md),
  [fee-aware execution verification](../reports/fee-impact-policy-20261028/VERIFICATION.md),
  [timing verification](../reports/maintenance-policy-20261027/VERIFICATION.md),
  [completion/health review](../reports/manipulation-hardening-20261027/REVIEW.md).
- [Keeper recovery](KEEPER_RECOVERY.md), [operating rehearsals](KEEPER_REHEARSALS.md)
  and [remaining outside-actor qualification](../TODO.md#task-security-external-manipulation).
- [Execution-quality policy](EXECUTION_QUALITY.md) and [governance setting procedure](OPERATOR_MANUAL.md#set-additional-execution-loss).

Update this inventory when authority, execution, accounting, pricing, limits,
scheduling or recovery behavior changes; update the owning procedure and evidence
in the same change under [documentation maintenance](TODO_WORKFLOW.md).
