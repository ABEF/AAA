# Typed Uniswap v4 conversion routes

The undeployed candidate supports reviewed, static-fee, hookless, single-hop
exact-input conversion for already-earned LP ZZZ balances. Royalties are claimed
in their original currencies; the current release has no royalty converter. Fresh Entry3
has no pre-Vault conversion route or executor. Native ETH is currency zero, with explicit value handling and no WETH
dependency for v4. These routes are separate from the registry's principal LP
pools. Adding one does not admit another NFT contribution pool or reward currency.
No real route, RPC or oracle is qualified by the local tests.

## Contract boundary

`ZZZLPRewardConverter` inherits the fixed-ledger `ZZZRewardConverter` base and
creates one immutable `ZZZV4RouteExecutor`. Only that parent can record, enable
or execute a route; output always returns to the same parent. Historical
royalty-converter instances and receipts retain their original profiles and
are not part of the current graph.
The parent retains owner/ledger authentication, governance, lifecycle and loss
checks. There is no arbitrary calldata, router, output recipient, sweep, hook,
multihop path, exact-output swap or generic executor approval.

Existing `addRoute(RoutePolicy)` and v3 route identities are preserved. The new
`addV4Route(ZZZV4RouteExecutor.Policy)` records an append-only policy. Read
`routeKind(id)` (0 unknown, 1 v3, 2 v4), `routeExists`, `routeEnabled`, and use
`v4Route(id)` for v4. A v4 ID must never be decoded as the old v3 tuple.
`setRouteEnabled(id,false)` requires no external venue/token read; reopening
revalidates the exact policy. Each parent mutation uses existing immediate
governance, operating-state and reentrancy guards.

The v4 `Policy` has 14 ABI words, in this order:

| Words | Fields |
| --- | --- |
| 0-1 | source, output |
| 2-6 | PoolKey: currency0, currency1, fee, tickSpacing, hooks |
| 7-8 | poolManager, stateView |
| 9-12 | sourceCodeHash, outputCodeHash, poolManagerCodeHash, stateViewCodeHash |
| 13 | reviewHash |

ID is `keccak256(abi.encode(keccak256("ZZZ_TYPED_V4_ROUTE_V1"), chainId,
executor, parent, policy))`. Currencies must be sorted, distinct and match the
directed source/output. Native uses `keccak256("ZZZ_NATIVE_ETH_V1")`, not a
fabricated token code hash. The pool must be initialized, hook zero, static fee
below 1,000,000 pips and tick spacing 1-32,767. StateView's manager binding,
runtime pins and current stored LP fee are checked before and after execution.

The unsigned review also checks the existing pinned slot0 response with exact
integer v4 TickMath: canonical ABI fields, initialized sqrt/tick bounds,
`sqrtAtTick(tick) <= sqrtPriceX96 <= sqrtAtTick(tick + 1)`, both packed 12-bit
protocol-fee directions at most 1,000 pips, and the stored LP fee equal to the
reviewed static fee. It rejects contradictory state before preparing a route.
The inclusive upper endpoint is intentional: after a downward boundary crossing,
v4 can store the preceding tick at the exact boundary price. Preserve that tick;
do not replace it with a calculated floor tick for range membership. Observer
and offline inventory checks share the integer consistency validation; the offline
gate also requires the reviewed static fee. No new RPC reads or schema fields are
added. These off-chain checks do not replace the executor's own guards.

The helper authenticates one core unlock callback, consumes its pending context,
requires full exact input and a positive minimum output, explicitly syncs native
settlement, settles/takes exact deltas and forwards only measured output.
Prefunded assets and forced ETH cannot subsidize input or masquerade as output.
Partial fills, mismatched callbacks, short/extra credit or failed forwarding
revert the entire operation. Input/output are bounded by signed int128 settlement.

<a id="add-or-rotate-an-input-route"></a>
## Add or rotate an earned-conversion route

1. Select the LP-reward converter, its fixed Rewards ledger and exact
   parent-bound executor. Qualify source currency, independent prices, actual
   venue depth/directional fees and core/StateView runtime/behavior.
2. Governance calls that converter's `addV4Route(policy)` with the exact tuple
   above. Source is a nonzero admitted earned ERC20 and output is native ETH.
   This cannot admit a contribution currency or move principal.
3. Record the returned immutable ID and exact observed tuple/parent/runtime in
   the matching conversion worker configuration. Complete the ledger's guarded
   converter enablement, and simulate the full entitlement debit/output credit.
   The default conversion cap remains1%, gas separate; a cheap nominal fee is
   insufficient qualification.
4. Stop an obsolete route with that converter's
   `setRouteEnabled(id,false)`, reconcile saved pending work, then qualify any
   replacement. Do not edit old route IDs, runtime pins or journals to adopt it.

Fresh Entry3 does not expose `addRoute`, `addV4Route`, `setRouteEnabled` or
`v4Executor`; the above is exclusively earned conversion. Historical routed
Entry1/2 keeps its explicit old readers/runtime and cannot be relabelled.

## Settle earned balances into ETH

Ledger `convertBatch` still selects at most 32 sorted NFT IDs and only their
already-earned source balances. V4 converter policies require nonzero ERC20
source and native output zero. The ledger preserves exact NFT entitlements;
conversion is not new income and cannot spend principal, compound/buyback reserves
or another NFT's balance. Native LP income is indexed in ETH directly.

Governance adds the v4 policy and enables the LP converter after
bindings/prices/routes are qualified. The constructor accepts no wrapper for a
native-only deployment. If V3 or exact WETH unwrap is used, its explicit wrapper
still must exist and pass its own checks. Enabling the converter does not invent
a usable route. Failed conversion leaves original backed entitlements intact.

Conversion workers explicitly select `profile: "v4_native"` with the reviewed
`contracts.lp_v4_executor` / `code_hashes.lp_v4_executor` pins for LP conversion.
Helper/parent, route tuple, current cap, independent
native quote, balances and simulation are verified at the same hash. Existing
historical workers use `v3_wrapper`; new adjustable-cap v3 deployments use
`v3_wrapper_configurable`. Changing profiles changes durable worker identity:
stop, reconcile pending hashes/state, review and restart one worker. There is no
silent profile fallback or mixed-profile automatic scheduling in this slice.

Historical royalty-reporting schema2 converter records are inspection-only.
Current royalty4/reporting5 uses `converter:null` and original currencies.
LP conversion reports its current governed cap separately from the10% maximum;
a missing/mismatched getter is unavailable, not an assumed1%.

[Execution-loss policy](EXECUTION_LOSS_POLICY.md) defines 3% / 1% / 3% defaults,
immediate governance and 10% hard maxima. At default 1%, the selected ETH/ZZZ
pool's observed approximately 1.101% fee still does not qualify a full conversion
at reference prices. Qualify a cheaper route or deliberately review a policy
change; never silently raise the limit.

## Remaining release work

Actual assets/routes/feeds, RPC/trace compatibility, complete fees/gas and keeper
operation need qualification, alongside current-profile website/release inventory,
OpenSea mint support and independent audit. Atomic ETH/WETH principal moves and
cross-chain NFT/ledger transport are unsupported scope, not implied capabilities
or required bridge-provider configuration. External custody-address exits are
removed; terminal collective holder return and compatible pre-exit same-chain
replacement retain their separate procedures.
No public signing, deployment or existing local fixture change is enabled here. [Scoped evidence](../reports/typed-v4-routes/VERIFICATION.md)
and the [single Todo](../TODO.md) distinguish implementation from release approval.
