# LP holder rewards settled in ETH

The [latest market follow-up](../reports/market-followup-20261109/REVIEW.md)
does not establish a practical default1% conversion route. Favorable tiny reverse
quotes are retained, but their observed output is below intrinsic-only gas cost
and no independent USD pair/full converter operation is qualified. This is not a
blanket claim that every numeric1% quote fails. A v3 pool's existence does not make
it a principal balancing venue. For future v3 earned conversion,
the converter must be constructed with the reviewed nonzero wrapper before
seal, then receive its exact wrapper/route policies and independently priced
ETH/ZZZ/WETH. Zero immutable wrapper cannot be changed after seal. Current
fresh7 automation accepts native-v4 only; manual existing contract capability
is not an implemented v3 worker. No asset/route is enabled by this note.

The current undeployed candidate uses native accounting7, custody5, fee-intake 1, direct
governance 2 and local canonical V10. Native ETH fees accrue directly as whole ETH units;
only already-earned fixed-ZZZ LP balances need conversion. The default
conversion loss cap is **1%**, governed up to **10%**, with gas paid separately by
the keeper. See [execution policy](EXECUTION_LOSS_POLICY.md) and the
[sole task](../TODO.md#task-lp-eth-settlement).

## Accounting and claims

The fixed 80/10/5/5 fee allocation happens first. Only whole units earned in the
80% individual and 10% equal-collective ledgers may be converted. Principal,
compound/buyback reserves, quarantined funds, unallocated receipts, nonmonetary phase and
unselected NFTs' balances are not conversion input. Whole-unit path settlement preserves
historical shares and equal membership before spending balances.

`Rewards.convertBatch(address token,uint256[] ids,bytes32 routeId,uint256 minimumETH,uint256 deadline)`
accepts 1-32 sorted, distinct minted NFT IDs and one admitted non-native source.
An authorized keeper converts the selected NFTs' earned whole balances once.
Output ETH is cumulatively allocated back to the same NFTs and their original
individual/collective components, conserving every received wei. Today's shares,
rarity or other holders do not reweight it. Transfers carry both unconverted
balances and ETH credits to the current owner.

The existing cumulative whole-wei apportionment conserves total measured output;
a tiny positive source component can round to zero ETH wei. The conversion floor
is a batch execution check, not a separate per-component USD guarantee. Retain
economic minimum amounts; holders can claim source ZZZ before it is converted.
Exact LP unit allocation does not eliminate currency-conversion rounding.

`ZZZLPRewardConverter` uses the neutral [ZZZRewardConverter base](../src/base/ZZZRewardConverter.sol). The fresh royalty converter is removed; original-currency royalties are separate. LP conversion cannot spend royalty or principal backing. It supports:

| Path | Required checks |
| --- | --- |
| Typed static hookless v4 source-to-native swap | Reviewed immutable executor policy, current independent source/ETH quote, exact full input, measured native output and no wrapper dependency. |
| Typed v3 source-to-WETH swap followed by unwrap | Reviewed router/factory/pool; authenticated18-decimal wrapper/proxy; BOTH wrapper-reference and final-native-ETH floors; exact output/unwrap deltas. |
| Admitted WETH directly unwrapped | Exact 1:1 native output and reviewed wrapper behavior; no price-based swap is implied. |

Swapped output must meet the greater of the caller's positive minimum and
`ceil(oracleQuote * (10000 - conversionLossBps) / 10000)`. For non-wrapper v3 swaps, oracleQuote is the GREATER of source→wrapper and source→nativeETH quotes; both must be positive/fresh. A wrapper feed cannot weaken the promised final ETH floor. At the 1% default this
is 99%; it is not a permanently fixed floor. Deadline is current and at most ten
minutes ahead. Exact approvals clear after use; prefunds cannot provide missing
input/output. A failed swap, quote, delta, wrapper, callback or minimum reverts
the whole batch and restores balances/liabilities. Native ETH itself is not a
conversion input.

Fresh7 Rewards admits exactly native ETH and the deployment-fixed ZZZ, bound before seal. Source identity must match `Pools.activationAssets().zzz`; no third LP currency or post-seal LP admission exists. Converted ETH credits the SAME NFTs/components directly rather than funding the trees again. Donations are not earned LP income. The generic converter may support a reviewed WETH route internally; this does not admit WETH to the LP ledger.

The standard claim selects ETH from both LP and royalty ledgers. Backed but
unconverted ZZZ remains **awaiting ETH conversion**, never relabelled as ETH.
An explicit `Rewards.claim(id,sourceToken)` can instead pay its current owner in
the original currency, including through ClaimRouter when selected. A claim
consumes that balance before any later conversion, preventing duplicate payout.
Ordinary pause preserves funded claims; canonical locks and recipient acceptance
retain their own guards. A broken source token can also block a source claim.


The shared optional conversion worker validates canonical latest/confirmed
header numbers, nonzero hashes and timestamps before scanning. A confirmed
timestamp cannot exceed either checked head; stale or reduced-depth
snapshots defer that worker through its existing error boundary. A quote-eligible
conversion adds one final head read after pricing and refreshes its deadline;
disabled and low-amount paths retain their existing work. No price, gas,
slippage or loss limit is widened.
Retain the source balances and recorded pending intent; do not force a
conversion, edit cursors or resend to hide an inconsistent provider.

## Operator procedure

| Step | Operation and required verification |
| --- | --- |
| Bind before sealing | Deploy `ZZZLPRewardConverter(controller,rewards,wrappedETH)` and bind it once through `Rewards.bindConverter(candidate)`. `wrappedETH` may be zero for v4-native-only use. Verify ledger/controller/runtime and the immutable wrapper choice. Generic seal does not certify this optional binding: the product inventory must. |
| Admit a native v4 route | Call `addV4Route(Policy)` with the exact [14-word policy](TYPED_V4_ROUTES.md), non-native source and native output. Review actual prices/depth/fees and executor-parent/runtime bindings. No wrapper is needed for this path. |
| Configure an actual wrapper path | `configureWrapper((bytes32,address,address,address,bytes32,bytes32,bytes32))` uses runtime, admin, implementation, admin owner, admin-runtime, implementation-runtime and review-hash fields in that order. Use only a genuinely reviewed wrapper; runtime alone cannot prove proxy safety. |
| Admit v3 conversion | `addRoute((address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32))` fields are source, router, factory, pool, fee, source hash, router hash, factory hash, pool hash, review hash. Output is the converter's immutable wrapper. |
| Enable/change policy | Direct governance sets `setEnabled(true)` and may call `setConversionLossBps(value)` within 0-1000 bps. Enabling alone proves no route is usable; execution checks its required dependencies. Existing stronger minimums remain. |
| Stop/rotate | `setEnabled(false)` or `setRouteEnabled(id,false)` needs no failing dependency read. New routes are append-only; route re-enable validates them. Review/reconcile pending transactions before replacing worker configuration. |
| Run and confirm | Select sorted IDs, actual whole balances, positive minimum ETH and fresh deadline. Simulate, submit once through the serial sender, confirm receipt and `LPRewardsConverted`, exact liabilities/output, cleared approvals and unchanged principal/shares. It is not a claim. |
| Failure/restart | Inspect sanitized error and saved hash/nonce first. Repair/review dependencies, then re-simulate current balances. Preserve journals, gas budgets, cursors and backing; never reset state to force a retry. |

The fixed converter algorithm, ledger and wrapper identity cannot be replaced
after binding. Supported new routes remain configurable; unsupported algorithms
or a different immutable wrapper need compatible reviewed replacement code.
A harmful governance-approved dependency remains an accepted trust risk.

## Keeper configuration and scheduling

`lp_conversion` is opt-in and disabled by default. Settings are `enabled`,
`profile`, `max_nfts_per_cycle` (1-32), `max_gas_to_output_bps`, and `assets`
entries with `asset`, `route_id`, `minimum_source_units`, `minimum_output_wei`.
Choose the actual reviewed profile explicitly:

- `v4_native`: pins `rewards`, `lp_converter`, `lp_nft`, `oracle` and
  `lp_v4_executor`; no `lp_wrapper` dependency is implied.
- `v3_wrapper_configurable`: pins the corresponding `lp_wrapper` and current
  governed-cap converter. WETH unwrap uses zero route ID.
- `v3_wrapper`: historical fixed-cap worker semantics only; never relabel a saved
  journal or silently use it for the current configurable deployment.

The worker validates bindings, route, policy, balances and simulation at one
confirmed canonical hash. It scans bounded windows and rotates currencies even
on an individual failure. Historical conversion scheduling and maintenance share
a serial sender and persistent three-way `conversion_turn` priority (0-2), with
separate cursors. Old `next_first` fields remain for state compatibility, not
priority selection. All existing absolute/daily gas and pending recovery limits
apply; relative gas-to-output is a separate operator economy guard.

A complete 1,000-NFT scan can take many cycles. Polling is not an immediately
claimable-ETH promise. Logs distinguish `lp_conversion_deferred` from
`lp_conversion_uneconomic` without secrets. Disable scheduling and reconcile any
pending hash before moving hosts; restore from actual chain/journal state, not a
new nonce counter.

## Exact-LP7 capacity and recovery

Fresh7 uses one fixed-ZZZ source and the explicitly supported native-v4 worker.
It performs at most six bounded preparations (32→16→8→4→2→1), recalculating each
subset's actual balances/quote/floor/deadline. Verified gas/per-transaction-cost
blocks or sanitized pre-send EVM refusals can permit smaller independent probes.
An opaque refusal diagnoses no token fault. Rate/transport/internal/work-limit,
price/economic/daily-budget, retry and uncertain-submission failures never justify
widening limits or retrying a signed operation. Successful subsets persist their
ordinal continuation, so the remaining suffix is visited instead of repeatedly
losing to an oversized prefix. Pending recovery precedes fresh configuration
admission. Singleton failures rotate without erasing balances.

Before durable intent/signing, a final head/deadline/UTC-day-budget check rejects
an expired or newly unaffordable review. It never rewrites approved calldata,
minimums, deadline, nonce or journals to revive it. Existing gas/economic ceilings
and captured source policies remain. The service still cannot promise an
affordable route, successful inclusion, permanently healthy tokens or instant
conversion; healthy source-token claims and independent ETH claims remain.

The contract's strengthened v3 manual route needs native ETH pricing IN ADDITION
to source/wrapper policies; the fresh7 automated worker remains native-v4 only.
Do not relabel a historical v3 worker or journal as fresh7. Source publication
does not enable or restart any worker. [Audit/evidence](../reports/fee-flow-audit-20261107/VERIFICATION.md).

## History, replacements and qualification

`LPRewardsConverted` records both source and native component amounts. API
`lp_conversions`, separate royalties and actual lifetime claims must remain
separate. Earnings are the original processed LP allocations plus royalties,
valued at today's reviewed prices. Conversion, claim and imported/returned
backing are not new income. Missing complete predecessor history is unavailable.

Compatible pre-exit same-chain canonical V10 carries native/source balances,
whole-unit pending/phase/direct component books and exact backing, with checked funding and funded
abort. Destination prefunds cannot replace source backing. Old profiles retain
their own schemas; they are not accounting4 imports. No external custody exit
remains. Terminal holder return preserves these reward liabilities but permanently
blocks canonical replacement; see [the lifecycle boundary](HOLDER_COLLECTIVE_EXIT.md).

The selected pool's recorded approximately 1.101% combined fee does not qualify
a full ZZZ conversion at the default 1% cap. Qualify a cheaper funded route or
explicitly review changed policy; never widen a signed review or invent output.
Typed v4 support exists, but actual routes/feeds, wallet/API and keeper services,
target gas, recovery rehearsals and independent audit remain open. Earlier
[settlement evidence](../reports/lp-eth-settlement/VERIFICATION.md) and
[native-port evidence](../reports/native-eth-port/VERIFICATION.md) retain their
original source scopes. No existing fixture, service or public signer is changed.
