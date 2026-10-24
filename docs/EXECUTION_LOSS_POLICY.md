# Governed execution-loss limits

Decision updated 2026-10-24: governance may change all three execution-loss
categories immediately after sealing, with an immutable **10% hard maximum**.
Current defaults remain **2% contribution, 1% reward conversion, 3% maintenance**.
These are per-operation ceilings, not targets or protection against market losses.
Network gas is separate. The candidate is undeployed and not production approved.

| Category | Policy owner and getters | Measurement |
| --- | --- | --- |
| Activation and top-ups | Vault's immutable `migrationBudget()`: `contributionLossBps()` | At least `grossUSD - floor(grossUSD * cap / 10,000)` must be added as marginal deployed LP. Incumbent principal, idle, compound and donations cannot subsidize it. |
| LP-fee / royalty conversion | Each fixed-ledger converter: `conversionLossBps()` | Native ETH output must meet `ceil(independentOracleQuote * (10,000 - cap) / 10,000)` and the stronger caller minimum. Each converter has its own setting. Exact WETH unwrap remains 1:1. |
| Rebalance, atomic pool move/resume and normal external custody | Budget: `maintenanceLossBps()`; custody plan: `minimumRetainedUSD(id)` | Atomic maintenance retains the capped starting principal plus released compound, measured at one starting price vector. Normal external custody preserves the absolute floor captured at approval. |

`MAX_LOSS_BPS()` is 1,000 basis points (10%) in these current modules. One basis
point is 0.01%. A setting of 100 means 1%, 300 means 3%, and zero requires no
execution loss under the applicable measurement. Zero can deliberately make
swaps unavailable; it is not a stop flag or a fee waiver.

## Operator procedure

1. Read the exact sealed deployment, controller, Budget/converter bindings and
   current settings at a confirmed block. Inspect pending transactions and custody
   approvals before changing policy. Never use a default as an on-chain observation.
2. Choose a justified ceiling, retaining cheaper routes, meaningful minima and
   independent prices. Raising a ceiling authorizes more possible economic loss.
   It does not repair a failed dependency or prove execution is reasonable.
3. Through the existing immediate governance controller, call the Budget's
   `setLossLimits(uint16 contribution,uint16 maintenance)`, or the
   relevant converter's `setConversionLossBps(uint16)`. Values must be 0-1,000.
   Read and preserve the other Budget limit when changing only one. LP and royalty
   converters must be configured separately when both should change.
4. Verify the getter and previous/new-value event. Ordinary global pause permits
   these settings; preparation/terminal canonical locks and reentrancy do not.
   Budget rejects configuration during an active maintenance checkpoint.
5. Reprepare and simulate current quotes and keeper work. Do not resend a known
   pending transaction. Caller-specified output/liquidity minimums never relax
   automatically; stop or reconcile stale pending work deliberately.

The Budget snapshots contribution policy before stateful Vault work, carrying it
with venue slippage in a typed `uint32`: low 16 bits venue slippage, high 16 bits
contribution loss. The final Budget check uses that captured policy. Maintenance
captures its ceiling at the initial checkpoint. A later callback cannot silently
weaken the in-progress check. A quote is not a lock on future governance: policy
may change before inclusion; user calldata minimums remain unchanged.

For normal external custody, approval stores an absolute minimum retained value.
Raising the global limit later does **not** weaken that plan's exit/completion or
proof commitment. Cancel and separately review a new unsent approval if a different
budget is intended. Exact outgoing raw/ZZZ and destination minimums still apply.
Raw emergency exit remains explicit and separately approved, with raw-asset
minimums and no USD-loss guarantee. Normal failure never selects raw mode.

## Independent safeguards and version boundaries

Venue slippage/deviation checks, caller minima, exact balances, actual LP,
available reserves and the existing 5% idle ceiling still apply. A 10% aggregate
setting does not override a stricter venue check. Per-operation limits do not
bound cumulative turnover, impermanent loss, depegs or future price changes.
Governance remains trusted and has no advance-warning delay.

Current activation preparation uses explicit `routing_version: 2` and reviewed
native accounting V2/runtime pins. It reads the current contribution cap and
cross-checks the packed `contributionResult(...,uint32)` trace. Legacy profiles
retain their old `uint16`/fixed-1% interpretation; no missing-getter fallback.
Current conversion workers explicitly use `v4_native` or
`v3_wrapper_configurable`; historical `v3_wrapper` remains fixed 1%.
Royalty reporting schema 2 reads the governed current limit and hard maximum;
schema 1 remains a historical fixed-limit profile.

No already-deployed immutable contract acquires these controls from a config edit.
Existing Anvil state, saved reviews and public simulation are unchanged. See
[typed routes](TYPED_V4_ROUTES.md), the [operator manual](OPERATOR_MANUAL.md),
[feature evidence](IMPLEMENTATION_STATUS.md) and [central Todo](../TODO.md).

The public website is not switched to this policy. Its native-V2/live profile and
review of current limits remain explicit release work; the existing local
deployment and its journals keep their original contract/configuration semantics.

### Review-time policy binding remains open

The current Entry captures the **execution-time** loss policy before transfers,
not the policy previously displayed in a wallet review. Its Request has amount,
route, minimum output/liquidity and deadline, but no caller maximum-loss field.
If governance raises the cap before inclusion, the new value can apply. Raw
caller minima still constrain the result, but do not prove the earlier USD loss
percentage, particularly after range/price changes. A pinned preparation trace
only proves its observation block; it cannot control later inclusion.

Before public activation/growth signing, implement a versioned reviewed Entry
path binding the caller's maximum contribution-loss BPS (or equivalently rigorous
minimum-value expectation). Compare it to the actual captured execution policy
before any transfer; preserve final callback/price/policy checks. Update exact
calldata/trace/API/inventory/wallet handling together, with no silent legacy or
direct-Vault fallback claiming the stronger guarantee. A lower configured cap
may be stricter; raising governance's maximum must not override the caller limit.
Preserve old Anvil deployments/journals under their explicit historical profile.

This is an [open release task](../TODO.md#task-reviewed-contribution-policy), not
an implemented guard. Immediate governance remains deliberately trusted, and no
new delay is proposed. Pausing/reviewing new work does not cancel transactions
already signed and broadcast by users. Current public signing remains disabled.
