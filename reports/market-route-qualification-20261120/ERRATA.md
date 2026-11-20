# Qualification-scope correction — 20 November 2026

This supplements the original REVIEW/RESULTS/CANDIDATE/VERIFICATION and raw
capture without modifying their bytes or re-running their observations.

The original statement that a WETH/v3 "price or swap path needs separately
reviewed adapters" is too broad for **already-earned LP reward conversion**.

| Capability | Correct current boundary |
| --- | --- |
| Principal LP placement/movement/balancing | Current Manager/Registry routing supports native ETH/fixed-ZZZ hookless v4. A v3 pool address is not an admitted principal destination. |
| `ZZZV4SpotPriceFeed` | Reads its fixed native-v4 reference. Reading a WETH/v3 reference requires separate source adaptation and review. |
| Solidity earned-LP converter | `ZZZRewardConverter` already implements typed v3 `addRoute`, exact source-to-wrapper swap and unwrap to native ETH, with original ledger rights, wrapper/venue/code checks and independent output floors. A new swap algorithm is not inherently required. |
| Wrapper choice | The wrapper ADDRESS is immutable **at converter construction**. Governance may configure reviewed wrapper policy/routes after sealing, but a zero-wrapper instance cannot become v3-capable through a setter. |
| Current F6 construction plan | `zzz_ops/deployment_plan.py` constructs the LP converter with zero wrapper. The example binding also records zero. A v3-capable fresh graph needs separately reviewed construction and matching pins/consumer qualification; no such graph is adopted. |
| Accounting7 keeper | Rejects LP settlement profiles other than `v4_native`. Generic/historical v3 worker code does not establish current accounting7 v3 automation. Manual contract capability is distinct from that service restriction. |

The original statement that the discovered v3 pools are unusable through the
**current prepared graph and worker configuration** still holds. Their positive
outputs remain finite unqualified diagnostics; full input consumption, actual
independent prices, gross1% conversion and complete fees/operation acceptance
are not established. No route, wrapper, source, financial cap, role or operating
configuration changes. Native ETH/fixed ZZZ remain the only contribution assets;
original-currency royalties remain separate.

The operator subsequently deferred final production-pool selection. Existing
`0x501122…afe1b` references describe the integration target and dated captures,
not a requirement to choose it for launch. No historical runtime, configuration
example or report is relabeled as a different deployment or newly qualified pool.

See [documentation reconciliation](../documentation-sync-20261120/REVIEW.md),
[LP settlement](../../docs/LP_ETH_SETTLEMENT.md) and
[pool selection](../../docs/POOL_SELECTION.md). Production remains NOT APPROVED.
