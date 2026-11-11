# A price reference may also execute our swap

## Scope

The fresh `execution_price_version:1` / `LP_ROUTING_VERSION()==3` candidate permits
an independently reviewed external native-v4 ETH/fixed-ZZZ reference pool to be a
reviewed swap venue. It does not require a different swap venue merely because
the reference price changes during our own trade. Public Oracle price reads stay
live; no public Oracle cache or keeper-supplied price replaces them.

The reference remains separate from PoPL's principal LP destination on the same
core. Own LP additions/removals would also alter its liquidity and undermine the
external-depth assumption; authenticating those transitions is outside this
capability. Becoming the highest-TVL pool does not automatically rotate a feed.
Governance still reviews the largest qualifying external pool and pins its reader.

Existing ownership, ETH/ZZZ identities, accounting7, exact-unit rewards,
80/10/5/5, original-currency royalties, canonicalV10 and custody5 are unchanged.
No integrated bridge, custody recipient or new signing capability is introduced.

## One operation, one valuation, one verified transition

1. Pricing starts a transaction-only scope before Entry pulls tokens, or before
   maintenance harvests/closes the old LP. Direct Vault contribution captures its
   scope before incoming asset pulls too. The Oracle validates and captures both
   ETH and ZZZ source observations, bounds, decimals, policy/sequencer IDs, gas
   policy and monotonic source-kind revision.
2. Explicit execution reads use those starting bounds. Contribution minima,
   incumbent repricing, issued shares, idle loss, swap output floors, aggregate
   maintenance loss and main/residual utilization cannot adopt a favorable later
   price. Public `priceBounds`, `value`, `quote` and `referenceX96` remain live.
3. The bounded router compares its reviewed venues using actual-core simulations
   at current depth, after any principal withdrawal. A selected quote includes
   output and the full post-swap sqrt price, stored tick, directional protocol
   fee, LP fee and active liquidity. All simulated state changes revert.
4. Manager authenticates the current observation, arms exactly one selected
   transition, and calls the real core. Immediately after `core.swap`, before
   settlement/output callbacks, it proves the exact output and quoted full state.
   No keeper can supply or override this proof.
5. The immutable composite reader reconstructs its original observation using
   the captured pool state and **current** pinned ETH-feed data. This must still
   match the original observation commitment. Only the recorded own-swap market
   state may change; ETH publications, other sources, controls and policy changes
   cannot hide behind that exception. Pool identity includes core and PoolId;
   identical keys on different cores are distinct markets.
6. Live freshness, sequencer protection, source agreement and liquidity floors
   are checked separately. A swap that leaves the two live sources more than the
   configured tolerance apart still fails. Current defaults remain source3%,
   contribution3%, conversion1%, maintenance3%, additional execution1%, gas separate.
7. Settlement, approval resets, refunds, LP writes and final Entry cleanup remain
   inside the appropriate proofs. Full selected-venue state is checked through
   balancing. Subsequent legitimate LP minting may change active liquidity in a
   **non-reference destination** only; price/tick/fees and the existing exact
   position-L/ownership checks remain. Reference/external-venue liquidity is not
   relaxed. Placement uses actual destination geometry and token requirements.

Captured execution getters are **data reads, not readiness or price-validation
authorization**. Full validation occurs at capture, Manager entry/exit,
before/after the core swap, after settlement, the balance-context approval/refund
boundaries, all three contribution NAV phases, Pricing finalization and final
Entry/maintenance closure. Within a read-only calculation chain, getters share
the captured data without repeatedly fetching every source. Static calls cannot
mutate market state between those calculations. Each registered reader supplies
one bounded proof containing original-state commitment and current live round,
so both are checked against the same current ETH publication rather than fetched
twice. This reduces duplicate work; it does not remove the mutable-boundary checks.

The private V1 transient codec is exactly49 static ABI words (1568bytes), written
only by the compiler's typed encoder. Captured quote getters load named ABI words;
full validators decode the complete structure. No caller supplies these words.
Transient words are bounded and explicitly cleared at the successful owner-end;
transaction rollback also rolls back the scope and all assets/ledgers. Two
sequential operations recapture current prices. Unrelated/nested operations
cannot adopt or replace an active scope. This is not an across-block price cache,
TWAP, uninterrupted price history or MEV guarantee.

## Components and authority

| Component | Responsibility |
| --- | --- |
| [Oracle](../src/ZZZOracle.sol) | Owns bounded transient scope, original commitments, live validation and exact market transitions. |
| [Composite reader](../src/ZZZV4SpotPriceFeed.sol) | Immutable market/ETH pins and read-only captured-state proofs. `roundAt`/`executionProof` are hypothetical proof reads, not live price feeds. |
| [Pricing](../src/ZZZContributionPricing.sol) | Starts/ends whole contribution and maintenance scopes; keeps captured values through final Entry callbacks. |
| [Manager](../src/ZZZLiquidityManager.sol) | Authenticates the actual core transition; only typed authorized operations can advance it. Standalone swapping owns its scope; Vault calls can borrow the expected Pricing scope. |
| [Balancer](../src/ZZZLPBalancer.sol) | Routing3 uses a14-word Plan, including full post-state; compares bounded reviewed venues, not a global highest-TVL promise. |
| [Fixed Math child](../src/ZZZLPBalanceMath.sol) | Read-only captured geometry, price/maintenance/admission calculations. Its immutable parent and Manager getter bind the same existing helper. No funds, approvals, setter or arbitrary execution. |
| [Backend and keeper](../zzz_ops/execution_price.py) | Explicit capability/runtime/configuration authentication, complete fresh trace validation and preserved pending-first recovery. |

Pricing is the only whole-operation scope owner. Manager can borrow only through
its explicit authenticated Vault branch; a separate buyback cannot borrow that
scope. Operator/keeper keys cannot call scope-control methods directly. Public
hypothetical arithmetic/proof reads grant no management authority.

Unpriced harvesting, raw parking/closure, terminal holder return and funded
original-asset claims retain their separate existing paths. Explicit governance
emergency uses its existing manifest/mask and does not enter the normal context;
this capability is not an automatic force fallback. Earned-LP conversion remains
its separate output-floor route, not a Manager context or royalty swap.

## Operator setup and rotation

These are exact call patterns, not deployed addresses or approved live values.

| Operation | Caller and inputs | Verify |
| --- | --- | --- |
| Review source pool | Operator: exact chain/core/StateView/PoolKey/ZZZ, external bidirectional depth, ETH publication and second independent ZZZ path | Reference differs from same-core LP destination; actual independence is not a TVL label. |
| Deploy reader | Bootstrap/operator: reviewed `ZZZV4SpotPriceFeed(Config)` | `config`, code hash, `executionAsset`, `executionMarket`, live round. |
| Admit dual feeds | Governance: `Oracle.setDualFeed(ZZZ,primary,secondary,300,reviewHash)` | Both SourcePolicy addresses/runtime hashes/decimals/ages and genuine independence. |
| Enable market-aware proof | Governance: `Oracle.setExecutionSource(reader,true,expectedReaderCodeHash,reviewHash)` for each reviewed composite source | `executionSourcePolicies(reader)`, monotonic `executionSourceRevision`; enable requires matching active fixed-ZZZ feed. |
| Review swap venue | Governance: admit compatible pool, then `Balancer.configureExecutionPools(poolIds,reviewHash)` | Same fixed assets/core, fee/spot/slippage limits, complete current-depth quote and operation simulation. |
| Adopt consumers | Operator: matching exact runtimes and explicit `execution_price_version:1`, LP routing3 | All capabilities and fixed Math parent/getter; context inactive before preparation. Old omission/0 remains LP routing2. |
| Disable normalization | Governance: `Oracle.setExecutionSource(reader,false,expectedReaderCodeHash,reviewHash)` | Revision advances without reading the failed source. This does not waive Oracle freshness or make a bad feed usable. |
| Rotate reference | Governance: review replacement immutable reader and both feeds, activate policy, explicitly register the new reader and re-review consumers | Old observations/reviews do not revive after disable/restore. No automatic ranking switch. |

For actual operation, use the [operator manual](OPERATOR_MANUAL.md) and source-bound
call examples. Stop affected new scheduling and recover saved pending hashes
before configuration/service adoption; preserve journals, raw history/checkpoints
and backups. Reprepare unsigned reviews against the new configuration. Do not
relabel LP2 deployments/journals as LP3, reset a chain or rotate a signer silently.
Publishing source performs none of these operating steps.

The inventory's retained `services.keeper.profile` family identifier contains
`lp2`; do not rename that code-owned evidence identifier alone. Explicit version1/
LP3 configuration, runtime/capability proofs, health metadata and journal identity
select the new behavior. A family label or local source hash does not prove the
installed process runs those bytes; actual operating qualification remains open.

## Verification and remaining release gates

### Gas admission

The focused final cold Entry fixture uses15,317,541gas for ETH and15,644,361gas
for ZZZ. Required full20% headroom makes those18,381,050 and18,773,234 respectively,
before treating them as a production provider estimate. They **fail the unchanged
12M default**. Initial and intermediate failures remain evidence, not passes.
These are controlled market/authority fixtures, not qualified live gas prices.

Use the already-existing optional activation policy2 only after reviewing the
complete route/consumer configuration, confirmed-block gas bound, full20%
headroom and independent fee ceiling. The source supports that policy; this
change does not enable it or raise any running/default budget. Route count,
input size, callbacks and current state affect cost;18.8M is not a universal
budget recommendation. Do not remove financial proofs to fit12M or silently
retry under a higher limit. Actual Robinhood operation/cost remains unqualified.

Operator qualification must also establish the chain's transaction ceiling and
RPC limits, beyond the existing confirmed-block guard. The anonymous official-RPC
probe returned403 before a valid chain response; no target limit or fee is
claimed. [Gas qualification boundary](../reports/reference-execution-20261111/GAS_QUALIFICATION.md).

Use the [source-scoped verification](../reports/reference-execution-20261111/VERIFICATION.md).
Actual markets, independent references, meaningful route depth, target-chain gas,
supported VRF/OpenSea, operating recovery and independent audit remain separate
release requirements. Price impact, fees or source disagreement may correctly
block a trade; this design does not promise every contribution or rebalance can
execute at every depth.

The design follows the pinned v4 core's actual unlock/settlement behavior rather
than a frontend quote; see [Uniswap callback/delta documentation](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas).
Scope cleanup follows the [Solidity transient-storage composability guidance](https://docs.soliditylang.org/en/latest/contracts.html#transient-storage).
