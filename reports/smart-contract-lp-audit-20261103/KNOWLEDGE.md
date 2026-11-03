# Primary-source knowledge and project applicability

Reviewed3November2026. Research informs the [audit brief](AUDIT_PROMPT.md);
guidance is checked against installed source rather than copied as a guarantee.

| Primary material | Application to PoPL |
| --- | --- |
| [Uniswap v4 liquidity overview](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/overview), [collection](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees) | Typed PositionManager actions; zero-liquidity decrease plus TAKE_PAIR collects real fees without a balancing swap. Review both registered legs and output classification. |
| [Unlock callback/deltas](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas), [flash accounting](https://developers.uniswap.org/docs/protocols/v4/guides/flash-accounting) | Authenticate callback caller/context, use actual deltas, fully settle debts/credits and enforce execution floors. Estimated LiquidityAmounts are not rounded actual principal debt. |
| [Native liquidity modification](https://developers.uniswap.org/docs/sdks/v4/guides/managing-liquidity/modifying-position) | v4 supports native ETH; this release must not revive WETH principal accounting or generic sweeps. |
| [Solidity0.8.26 security](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html) | Cross-contract reentrancy, effects/interaction ordering, callbacks, gas-bounded loops and fail-safe modes apply. CEI alone does not replace post-call identity/policy/backing checks. |
| [Current known compiler bugs](https://docs.solidity.org/en/latest/bugs.html), [versioned list](https://docs.soliditylang.org/en/v0.8.26/bugs.html) | Later disclosures can affect a pinned older compiler. Check actual conditions/patterns against viaIR/Yul-disabled0.8.26; do not silently upgrade compiler or infer that version-tagged docs contain later discoveries. |

Pinned installed implementations: Uniswap core1.0.2/periphery1.0.3 and OpenZeppelin5.4.0
from package/lockfile. The review reads PositionManager `_increase`, `_decrease`,
`_mint`, `_burn`, pair settlement/collection, actual PoolManager swap/modify logic,
SqrtPriceMath/LiquidityAmounts and exact token/Permit2 interactions. On increase
and decrease the installed periphery checks principal deltas separately from
fees; PoPL must still harvest and classify its own actual receipts correctly.

The current official compiler-list snapshot contains six records associated with
0.8.26. [Applicability](compiler-assessment.json) records the actual settings,
source graph, remaining layout assumptions and snapshot hashes. No applicable
trigger was established; neither source AST analysis nor source-code review is
proof of correct compiler lowering. The compiler was not upgraded.

The separate website README was inspected read-only: its prior source checkpoint
and served current3 build are not the accounting6 source reviewed here. Matching
current API/site/runtime rollout remains a distinct task. No website file,
deployment configuration, local wallet profile or served build was changed.

Live feeds/routes/marketplace/native dependencies and host qualification are not
created by these documents. More controls can trade liveness for safety; any new
restriction needs a demonstrated failure and compatibility review.
