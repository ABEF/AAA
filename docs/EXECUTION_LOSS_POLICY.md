# Governed execution-loss limits

Governance may change all three execution-loss
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
3. From the current governance wallet/Safe, directly call the Budget's
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
weaken the in-progress check. The reviewed Entry path additionally rejects inclusion-time policy above
the caller maximum; other governance configuration is not frozen by a quote.

For normal external custody, approval stores an absolute minimum retained value.
Raising the global limit later does **not** weaken that plan's exit/completion. Cancel and separately review a new unsent approval if a different
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
current accounting3/runtime pins. It reads the current contribution cap and
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

The public website remains simulated. Historical native2 source/read profiles
do not match current accounting3 merely through a configuration edit. Current
website/service qualification and public signing remain open; existing local
deployments/journals keep their original semantics.

<a id="review-time-policy-binding-remains-open"></a>

### Review-time policy binding

The undeployed candidate adds `REVIEW_POLICY_VERSION()==1` on Entry and
`ENTRY_REVIEW_VERSION()==1` on its fixed Pricing helper. The owner calls
`executeReviewed(Request,uint16 maximumLossBps)`; the original nine-field Request
is retained. The maximum is 0..1,000 bps and is encoded in signed calldata.

Before pulling tokens or converting funds, Pricing captures the current governed
contribution cap and rejects it if greater than the caller maximum. A lower
governed cap can tighten the operation. Existing final checks enforce the captured
actual policy; callbacks cannot weaken it mid-operation. The legacy `execute(Request)` and unreviewed Entry basis initializer are not
provided by this new code; unknown old selectors revert, with no fallback.

This binds a maximum loss policy, not a future USD price, range, strategy setting,
venue configuration or assured execution. Exact output/liquidity minima, deadline,
fresh independent prices and all physical/balance checks remain. Immediate
governance can still approve dangerous dependencies; this guard does not remove
that accepted trust. Direct owner-to-Vault calls do not acquire a reviewed-Entry
guarantee, and the preparer never silently falls back to them.

Current pricing-V2 activation preparation and schema-5 release inventory require
explicit `review_policy_version: 1`, matching getters, runtime pins and exact new
selector/trace. The response carries `reviewed_maximum_loss_bps` separately from
the captured `execution_limit_bps`; provenance includes the policy version.
Historical pricing-V1/local profiles keep their old semantics. Old native2
activation configurations require an explicit source-matched replacement profile; missing getters/RPC errors
never mean legacy support. Read-only historical profiles remain separate.

The historical Anvil profile retains its original policy and runtime; never
reinterpret saved journals. The current read/unsigned integration must explicitly require accounting3, the
reviewed selector and current limit checks; actual wallet/provider
acceptance and public signing remain [open](../TODO.md#task-reviewed-contribution-policy). [Source-scoped evidence](../reports/comprehensive-improvement-20261025/VERIFICATION.md).
