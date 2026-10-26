# Current ETH/ZZZ contribution routing

The current candidate accepts only **native ETH or one fixed ZZZ**. Its profile
is accounting 3 / fee-intake 1 / routing 2 / pricing 2 / review 1, with direct
governance 2 and local canonical V4. A route is a reviewed conversion path,
not the NFT's liquidity ownership or a new accepted currency.

## Three distinct routing jobs

| Stage | Purpose | Current boundary |
| --- | --- | --- |
| Original contribution through Entry | Convert ETH or fixed ZZZ into one actual pool accounting currency when necessary | For the selected native ETH/ZZZ pool, both inputs can be direct (`routeId=0`, `route_kind=0`). No external input swap is required merely to enter. |
| Vault ratio balancing and LP placement | Acquire the amounts appropriate to the actual concentrated range and add real LP | Guarded swaps may still be needed for a direct one-sided contribution. Full operation must meet the captured original-source deployed-LP floor. |
| Later reward conversion | Convert already-earned ZZZ or an admitted royalty currency into ETH | Separate ledger/converter/routes and default 1% conversion cap. This never adds a contribution input or uses principal. |

A direct contribution is not a promise of a literal half-and-half split. Actual
range and pool price determine token requirements. Balancing, unused input and
execution costs are included in the contribution checks; NFT values/artwork
change only after confirmed actual LP addition.

## Admission and route identities

`ActivationAssets` binds the fixed ZZZ once before seal and admits only that
source or native ETH. Source-policy disable/re-enable, approved routes and the
sole contribution-pool selection remain separately controlled. There is no
post-seal token replacement, USDC/USDG/WETH input option or symbol-based fallback.

The selected [hookless native ETH/ZZZ pool](POOL_SELECTION.md) is one contribution
pool at a time. Historical buckets, owed currencies and local pool migrations
retain their accounting identities. Admitting another supported pool does not
move principal, select a route or reopen contributions automatically.

When a pre-Vault route is needed, Entry supports these explicit kinds:

| `route_kind` | Identity and requirements |
| --- | --- |
| `0` | Zero route ID, source already equals one actual accounting currency; `minimumOut=0`. |
| `1` | Reviewed typed single-hop v3 policy, ERC20 source/output and exact SwapRouter02/factory/pool bindings. |
| `2` | Reviewed typed hookless static-fee v4 policy and immutable parent executor; native source/output use explicit ETH settlement. |

Policy IDs are append-only. Direct governance can add/disable routes after
sealing; no protocol timelock applies. Disabling avoids failing dependencies;
re-enabling validates them. Route changes do not change fixed input identity,
sealed algorithms, owner authorization or current signed caller maxima. A new
unsupported venue/algorithm requires compatible reviewed code, not a new URL.

## Value, execution and wallet review

Two independent reviewed USD observations are required for each priced asset;
the selected disagreement tolerance is **3%**. Contribution loss defaults to
**2%**, governed up to 10%, with gas separate and stronger caller/venue minima
retained. At default, conservative upper source value must produce at least 98%
as actual marginal LP valued at frozen lower pair prices. Price disagreement
and conversion/placement costs share the available margin; they do not create
extra allowances per stage.

The backend validates source policy, route identity, real dependencies, balances,
exact allowance, canonical state and the complete operation. It returns only an
unsigned approval or exact Entry transaction, never a conversion-only wallet
shortcut that loses original-source provenance. After approval confirms, prepare
again. See [Entry tuple/guards](ACTIVATION_ENTRY.md), [preparation configuration](ACTIVATION_PREPARATION.md)
and [typed v4 routes](TYPED_V4_ROUTES.md).

Qualification must examine actual depth, directional LP/protocol fees, token
behavior, independent prices, full trace/gas and pending-state handling. A cheap
quoted source swap alone cannot qualify the complete activation. Native ETH and
WETH stay distinct; an optional wrapper-dependent reward route does not make
native principal depend on WETH.

## Historical research and release boundary

USDC/USDG activation research, old addresses/quotes, the standalone route reader
and its CLI commands are retired. They are not supported contribution options
or present-day price/liquidity evidence. Their committed source and unpublished
draft identities remain in the [retirement record](../reports/architecture-pruning-20261025/retired-tools/stable-research-retirement.json).
Optional admitted stablecoin/WETH royalties remain a separate [settlement duty](ROYALTY_SETTLEMENT.md).

Actual ETH/ZZZ feeds, swaps, API/provider traces, wallet services and target-chain
operations still require qualification in the [sole Todo](../TODO.md#task-activation-assets).
Source edits do not update running contracts, journals, the website server or its
null public deployment. Signing remains Anvil-only; production is NOT APPROVED.
