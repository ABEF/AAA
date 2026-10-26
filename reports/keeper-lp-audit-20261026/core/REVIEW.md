# Core LP management: source-bound review

This slice reviewed the current eight core LP modules, their financial call
order and the installed Uniswap/OZ implementations used by those calls. Exact
source/dependency/build pins are recorded in [bindings](core-bindings.json).
Production Solidity, authority, allocation, supported inputs, custody rights,
policies and public ABI remain unchanged. This is an internal source review,
not proof that no exploit exists or production/independent approval.

## Confirmed correction

**C-01: stale enum domain in the range-policy regression (verification defect).**
`testInactiveAndMissingIdentityCannotAuthorizeRebalance` still iterated statuses
0 through 6 from the removed architecture. Current `PositionStatus` is
None/Active/Outbound/Dormant/Parked, values 0 through 4. Casting 5 or 6 panicked
before the intended strategy checks could finish. This did not expose a
production principal-withdrawal or authorization bypass.

The exact existing method was executed before editing: one selected/executed
case failed with enum-conversion panic `0x21`, not a setup failure. The original
[test bytes](RangePolicy-before.sol.txt), [result](before-results.json) and
[selection/summary](before-summary.json) are preserved.

The single-line test repair uses `uint8(PositionStatus.Parked)` as the actual
domain end. It keeps all four supported inactive cases and the separate missing
physical LP/center checks for Active. No assertion, production guard, minimum,
compiler setting or EVM limit was relaxed.

Afterward, the affected nine-method `RangePolicyTest` fixture passes, including
the 1,000-run applied-width property and actual sealed governance/keeper-role
control. [Final summary](after-summary.json), [results](after-results.json) and
[runner](run-range-regression.py) record that scope. The initial failing run is
not added to the nine distinct final passes. Full-test gas includes fixture
deployments and is not target-chain operation gas qualification.

## Financial and operational paths traced

| Boundary | Source behavior checked | Result / remaining limitation |
| --- | --- | --- |
| Contribution and share order | `Vault._join` settles all already-funded dust, harvests current LP, flushes current dust and releases incumbent compound before adding new money. It harvests entry-swap fees again under incumbent weights, revalues incumbent LP after deliberate balancing, excludes old LP/idle/compound from marginal deployment, checkpoints owner before share writes, then adds one-time membership. | No new old-fee capture, duplicate collective membership or incumbent-value subsidy was identified. Fee-ledger callback guards were independently traced by the accounting subtask. |
| Captured contribution basis | Entry authenticates owner/source/exact Vault calldata; ContributionPricing freezes source/pair bounds, caller maximum and policies before pulls. Three ordered NAV marks bracket swaps and physical placement; final spot/fingerprints remain bound through Entry approval resets and owner checks. | Failed transactions roll back the transient basis. No public cleanup/reset is needed or added. Honest independent sources and token/venue qualification remain assumptions. |
| Maintenance checkpoint lifecycle | Budget snapshots only attributed starting principal/idle and one starting price vector, then includes only actually released designated compound. Rebalance/move/compound finish with physical deployed+idle retention, nonzero deployed LP and the 5% idle ceiling. Compound cooldown and transient snapshot roll back on failure. | The 3% default is per operation, not capital insurance or a cumulative allowance. Existing stricter venue minima remain. No new policy was introduced. |
| Shared upkeep and settlement | Rebalance harvests before closing; compound preserves existing ticks and harvests any balancing-swap fees before increasing. At most two balance passes re-plan from actual state; corrections no greater than one basis point of available raw input are skipped. | Maintenance is per shared bucket, without a 1,000-holder loop. Bounded loops and economical execution still need actual maximum-state/gas/strategy qualification. |
| Physical v4 LP | Manager verifies Vault owner, complete PoolKey, tick range and exact liquidity delta after pulls, approvals, settlement, resets and refunds. Native debt is rounded up and exactly funded; previous Manager/PositionManager balances cannot pay principal. | Installed PositionManager `_mint`, `_increase`, `_decrease`, `_burn`, `_settlePair` and `_takePair` were traced. Its zero-liquidity decrease really collects accrued fees; principal slippage excludes fees. No arbitrary action or recipient surface was found. |
| Swap/native callbacks | One pending hash authenticates the Core callback and is consumed once. Exact input and positive output are required; native sync/settle/take uses expected sender windows. Actual output/deltas and prefunds are checked, approvals reset and price deviation is rechecked. | Partial fills, changed output or unauthorized callback revert. These checks cannot make a frozen/malicious admitted dependency available. |
| Range direction and scheduling | Raw and inverse price directions, outward tick spacing, recorded-center mismatch detection, cooldown/price trigger and default-disabled 25/50 keeper selection were traced. Selection changes only width under a reviewed fingerprint; ordinary guarded rebalance changes physical LP separately. | No new range-authority bypass confirmed. Displacement/hysteresis is not a volatility model, and polling or wide ranges do not guarantee continuous fee earning. |
| Directional fee sizing | Strategy uses the correct low/high 12-bit directional protocol fee and combined `pf + lp - floor(pf*lp/1e6)` formula, matching the installed `ProtocolFeeLibrary`. Actual static LP fee must match the admitted key. | Wrong/unavailable state fails closed. Price movement/depth and repeated turnover remain real-market economics, not a constant-price sizing guarantee. |
| Prices and admission | Oracle bounds both reviewed rounds, age, precision, positive answer, runtime, optional sequencer and exact 3%-configured disagreement. Registry permits one contribution pool, fixed ZZZ pairs and pinned hookless native venue bindings; disabling does not need the failed dependencies. | Two addresses/IDs cannot prove independence. Immediate governance can admit unsafe policies and external inputs can fail; no fallback/peg/spot oracle or automatic token replacement was added. |
| Persistent identities and capacity | Alias/reservation reuses stable buckets; four historical/reserved slots and current eight-word statuses remain explicit. Same-pair move and parked resume preserve shares; contribution reopening is a separate deliberate setting. | Old aliases cannot silently activate against a bucket now in another pool. External custody and whole-collection lifecycle are separate reviewed slices, not a bridge guarantee from this review. |

## Source/dependency evidence and exclusions

The review read Vault, LiquidityManager, Strategy, PoolRegistry, Oracle,
MigrationBudget, Compounder and ContributionPricing, plus the named Entry,
Assets, Canonical validation, exact-asset and price-math caller boundaries.
Installed PositionInfo tick offsets, v4 settlement/fee behavior and OZ exact
approval/reentrancy semantics were inspected locally; dependency versions were
not replaced or inferred from generic documentation.

All 44 production Solidity files, 31 normal dependency inputs and four build
inputs match the reused normal 37-object evidence. Both executions bind all
265 closed AST inputs before and after. Only `test/RangePolicy.t.sol` changes
for the final AST; fresh typechecking succeeds. Normal production objects,
unaffected suites and fresh static analysis were not rerun without a source
change. Earlier full-audit principal/static evidence remains historical and
source-bound, not inflated into new runtime coverage.

No production financial defect was confirmed in this slice, and no speculative
Solidity optimization was introduced to manufacture a code-change outcome.
Removing an approval, final callback check, physical-LP assertion, backing guard
or read freshness check solely for cheaper gas was not justified. Actual
feed independence, routes/depth/fees, token/proxy behavior, target gas/MEV and
strategy economics, keeper operating recovery, authority wallets and independent
audit/remediation remain release work. Production is NOT APPROVED.

No public RPC, financial transaction, deployment, sealing, existing Anvil reset,
service action, website change, signer change or journal mutation occurred.
