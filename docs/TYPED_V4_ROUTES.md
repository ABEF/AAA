# Typed Uniswap v4 conversion routes

The undeployed candidate supports reviewed, static-fee, hookless, single-hop
exact-input conversion for Entry contributions and earned LP/royalty ERC20
balances. Native ETH is currency zero, with explicit value handling and no WETH
dependency for v4. These routes are separate from the registry's principal LP
pools. Adding one does not admit another NFT contribution pool or reward currency.
No real route, RPC or oracle is qualified by the local tests.

## Contract boundary

Each `ZZZActivationEntry`, `ZZZRoyaltyConverter` and inherited
`ZZZLPRewardConverter` creates its own immutable `ZZZV4RouteExecutor`. Only that
parent can record, enable or execute a route; output always returns to the parent.
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

The helper authenticates one core unlock callback, consumes its pending context,
requires full exact input and a positive minimum output, explicitly syncs native
settlement, settles/takes exact deltas and forwards only measured output.
Prefunded assets and forced ETH cannot subsidize input or masquerade as output.
Partial fills, mismatched callbacks, short/extra credit or failed forwarding
revert the entire operation. Input/output are bounded by signed int128 settlement.

## Add or rotate an input route

1. Qualify the actual assets, independently priced feeds, pool liquidity,
   directional fees, manager and StateView runtime hashes/binding. A UI ticker or
   low nominal LP fee does not establish an executable route.
2. Verify native ETH or fixed ZZZ source admission through the existing policy;
   no third contribution currency can be added. Call
   `Entry.addV4Route(policy)` through governance with the exact immutable policy.
   The output must be one actual currency of the selected contribution pool.
   Direct pair input still uses route zero; token approvals remain exact amounts.
3. Add a reviewed activation configuration with accounting 3 / fee-intake 1 in
   its parent, explicit routing 2 / pricing 2 / review 1 and
   `contracts.v4_executor: {address,code_hash}` plus the fixed pricing companion. Every source entry declares
   `route_kind` (0 direct, 1 v3 or 2 v4). Include reviewed token/feed and conversion
   manager/StateView dependency pins. No automatic v3/native fallback exists.
4. Preparation verifies helper/parent, domain/policy, actual pool state and current
   governed contribution cap at one canonical hash. The complete trace must show
   the exact Entry-to-helper call/value/output, packed Budget result, share event
   and actual LP-unit increase. Internal probes are never wallet transactions.
5. Simulate approval if needed, then reprepare the full operation after it confirms.
   Caller output/liquidity minima remain additional protections. Wait for the
   confirmed Entry event and actual active LP before changing NFT values/artwork.
6. Disable an obsolete route explicitly and reconcile pending reviews; disabling
   does not rewrite route identity, refund prior approvals or resend transactions.

## Settle earned balances into ETH

Ledger `convertBatch` still selects at most 32 sorted NFT IDs and only their
already-earned source balances. V4 converter policies require nonzero ERC20
source and native output zero. The ledger preserves exact NFT entitlements;
conversion is not new income and cannot spend principal, compound/buyback reserves
or another NFT's balance. Native LP income is indexed in ETH directly.

For each converter, governance adds the v4 policy and enables the converter after
bindings/prices/routes are qualified. The constructor accepts no wrapper for a
native-only deployment. If V3 or exact WETH unwrap is used, its explicit wrapper
still must exist and pass its own checks. Enabling the converter does not invent
a usable route. Failed conversion leaves original backed entitlements intact.

Conversion workers explicitly select `profile: "v4_native"` with the reviewed
`contracts.lp_v4_executor` / `code_hashes.lp_v4_executor` pins for LP conversion,
or `contracts.royalty_v4_executor` / `code_hashes.royalty_v4_executor` for royalties;
helper/parent, route tuple, current cap, independent
native quote, balances and simulation are verified at the same hash. Existing
historical workers use `v3_wrapper`; new adjustable-cap v3 deployments use
`v3_wrapper_configurable`. Changing profiles changes durable worker identity:
stop, reconcile pending hashes/state, review and restart one worker. There is no
silent profile fallback or mixed-profile automatic scheduling in this slice.

Royalty reporting opts in with `royalty_reporting: {schema: 2,
converter: {address, code_hash}}`. It reports the current governed cap separately
from its 10% hard maximum; a missing/mismatched getter is unavailable, not 1%.

[Execution-loss policy](EXECUTION_LOSS_POLICY.md) defines 2% / 1% / 3% defaults,
immediate governance and 10% hard maxima. At default 1%, the selected ETH/ZZZ
pool's observed approximately 1.101% fee still does not qualify a full conversion
at reference prices. Qualify a cheaper route or deliberately review a policy
change; never silently raise the limit.

## Remaining release work

Actual assets/routes/feeds, RPC/trace compatibility, complete fees/gas and keeper
operation need qualification, alongside current-profile website/release inventory,
OpenSea mint support and independent audit. Atomic ETH/WETH principal moves and
cross-chain NFT/ledger transport are unsupported scope, not implied capabilities
or required bridge-provider configuration. External custody remains separate.
No public signing, deployment or existing local fixture change is enabled here. [Scoped evidence](../reports/typed-v4-routes/VERIFICATION.md)
and the [single Todo](../TODO.md) distinguish implementation from release approval.
