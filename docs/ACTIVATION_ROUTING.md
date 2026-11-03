# ETH/ZZZ routing boundaries

Fresh **Entry-routing3 / pricing2 / review2 / accounting6**, schema10 inventory,
accepts only native ETH and the one fixed ZZZ. Both already are LP currencies.
The optional whole-input conversion before Vault balancing has been removed.

| Operation | Actual responsibility |
| --- | --- |
| Entry input | Authenticate the current owner and exact admitted ETH/ZZZ amount; freeze pricing/review terms; forward directly to the fixed Vault. No Entry route/executor. |
| Vault balancing | Use only entrant funds to acquire the ratio required by the existing concentrated range, then prove actual marginal MAIN LP and issue aggregate-NAV shares. |
| Maintenance balancing | After closing the existing portfolio, compare bounded actual-core quotes from reviewed ETH/ZZZ execution venues independently of the LP destination. |
| Earned reward conversion | Separate LP/royalty ledgers/converters settle funded ERC20 entitlement into ETH. Their reviewed v3/v4 routes remain. |

A direct contribution is not a promise of no swap or a literal50/50 ratio. The
actual range and pool price determine token requirements. Entry no longer adds
a redundant preliminary round trip. Vault uses at most one reviewed balancing
swap; an unsafe/unfillable placement reverts without an automatic weaker fallback.

## Operator controls

`ActivationAssets.configureZZZ` fixes the one ZZZ before sealing.
`setAsset(token,false,codeHash,reviewHash)` stops future contributions in that
currency without querying a failed token/feed. Re-enable with validated code,
decimals and dual pricing; pool configuration cannot silently reopen it.
There is no `Entry.addRoute`, `addV4Route`, `setRouteEnabled`, or `v4Executor`.
Do not call these old interfaces against a fresh Entry3.

Governance can still update the bounded reviewed swap-venue list through
`LPBalancer.configureExecutionPools(ids,reviewHash)` after qualification. This
changes Vault balancing choices, not the one contribution destination, token
identity, existing liquidity or earned-conversion routes. An empty list stops
swaps with no fallback; an already suitable inventory may need no swap.

Contributions default100USD activation/5USD growth and a2% total execution budget,
with policy bounds/caller maxima/stronger venue limits and gas separate. Dual
source agreement3%, additional execution-loss1%, idle ceilings and known trading
fees remain different controls. At default, marginal deployed LP must cover98%
of conservative source value. Incumbent LP/idle/compound cannot subsidize it.

## Profiles and wallet review

Fresh activation configuration explicitly selects routing_version3, pricing2,
review_policy_version2 and matching accounting6/Portfolio2 read bindings. Source
rows contain only pool_id,source_asset,asset_policy_id; old route fields and
contracts.v4_executor are rejected. The shorter seven-field Entry request has a
new selector. Exact ZZZ approval remains a separate transaction; reprepare after
it confirms. ETH needs one Entry transaction. Values/artwork update after actual
confirmed LP execution, not approval or submission.

Historical routing1/2 API readers retain their exact old tuples and runtime pins;
they cannot reinterpret or upgrade a deployment by changing a version number.
The public website remains simulated and signing Anvil-only. Matching fresh
site/services, actual feeds/venues/token/gas/operating qualification and independent
audit remain open. [Entry inputs](ACTIVATION_ENTRY.md), [preparation](ACTIVATION_PREPARATION.md),
[earned conversions](TYPED_V4_ROUTES.md), [execution policy](LP_EXECUTION_POLICY.md).
