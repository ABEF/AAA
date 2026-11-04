# Scenario coverage and evidence boundaries

November4,2026. [Review](REVIEW.md), [executed method/stage record](VERIFICATION.md).
Finite coverage is explicit; there is no100% market/function/recovery guarantee.

## Newly composed actual local-v4 scenarios

| Scenario | Actions and assertions |
| --- | --- |
| Bull then bear; bear then bull | Two four-adjustment paths, alternating desired hybrid/single modes. Each path has10NFTs,9activated and one dormant, with unequal principal and Commun/Rare/Legendary royalty weights across two wallets. ETH/ZZZ activation and growth before/after replacements; hourly-spaced donations/harvest; real Compounder; partial/final claims. Independent raw entitlement, fair shares, aggregate NAV and custody checks after phases. |
| Flat/near-centre activity | Contributions/harvest/compound use existing main geometry after replacement. No recentering or manufactured residual; no continuously enforced60/40 assumption. |
| Residual becomes mixed; disable pending | Actual swap into residual interior, new ETH activation and ZZZ growth while old residual remains registered. Partial claims and transfer to an existing holder, old-owner claim rejection, guarded merge, then growth under new ownership. |
| Both positions wholly outside | Cross each main boundary in turn. Correct one-sided ETH/ZZZ entries still increase main only, without clock/centre/residual-L changes; both legs stay valued until a guarded merge. This does not prove every opposite-side swap is affordable. |
| Ordinary sampled trigger | With no pending geometry exception, collect600seconds across the end of the hard12hours, inserting ZZZ activation and ETH growth. Stable identity/first sample/side and clock persist; authorized replacement then succeeds. Service jitter is separate evidence. |
| Independent-feed disagreement | Contradict one ETH USD source; activation rejects with identical wallet funds, supply and physical fingerprint. Current USD value becomes unavailable; actual harvest and raw claim still succeed. Restore feeds after a virtual minute; activation and reconciliation recover. |
| LP/royalties/terminal return | Fund pre-entry royalties to incumbent only, then rarity1:3 future receipts across hybrid replacement. Harvest/close both; governance allocate/direct payout; old LP rewards, transfer and future royalties continue. Principal wallet delta is distinct from fees. |

Contract scenario bodies/helpers: [OptionalPortfolioCore](../../test/OptionalPortfolioCore.t.sol),
`testMarketCampaign*`. The changed harvest helper's existing six-day caller is
also selected as a control. These are serialized EVM calls, not simultaneous
browser writes, real wall-clock service behavior or live market backtests.

## Newly composed backend/worker scenarios

| Scope | Fresh tests |
| --- | --- |
| Projection accounting6/portfolio2/custody5 | [Four methods](../../tests_python/test_market_lifecycle_projection.py): single→dual→pending-disabled→residual-closed canonical snapshots through one Projection; unavailable USD/recovery with unchanged raw claims; wrong residual owner after a healthy read; omitted residual with inconsistent count/amounts. |
| Worker accounting6/portfolio2/custody5 | [Three methods](../../tests_python/test_market_lifecycle_keeper.py): compound eligibility through modes/threshold/outside/restart; price-fault blocks compound while both-leg raw harvest review survives; pending recovery precedes broken fresh reads. Temporary journals and inert RPCs only; no signer invoked. |

## Broader requested areas and what remains

| Area | Evidence applied / limitation |
| --- | --- |
| Core/dependency/build safety | Exact52production/31dependency/4build-input comparison against current authority size evidence. Reuse43normal gates and their original limits; no new analyzer/full suite/CI claim. |
| Permissions, callback races, failure on second mint/burn, emergency and parking | Prior [authority](../authority-audit-20261103/VERIFICATION.md), [LP audit](../smart-contract-lp-audit-20261103/COVERAGE.md) and [manual controls](../manual-operations-20261031/REVIEW.md) retain original scopes. Existing implementations inspected; those whole campaigns were not rerun here. |
|1000 NFTs / mixed wallet terminal apportionment | [Prior focused assurance](../holder-exit-assurance-20261103/REVIEW.md) retains source/test scope. New campaign adds a small real-v4 royalty/exit composition, not a new1000-holder or target-gas result. |
| Burn and LP/royalty conversion | Separate implementations and earlier scoped [native/Entry evidence](../direct-entry-v3-20261103/VERIFICATION.md). The new campaigns reserve/check backing but do not qualify a real conversion route, actual ZZZ burn ABI or complete ETH-only claim service. |
| Canonical replacement | Parked same-chain V6 with zero live residuals; actual successor/runtime/funding/cutover remain qualification. No post-exit, cross-chain or post-halt recovery was added/tested. |
| Timing, jitter, observation faults | New EVM timing/worker-decision composition plus earlier [coordination](../../docs/KEEPER_COORDINATION.md) evidence. No new24/7 service run, inclusion guarantee or protected submission. |
| RPC outages, restart, disk/nonce/reorg/backup/history | New inert read/worker cases supplement [backend corrections](../comprehensive-audit-20261104/VERIFICATION.md) and [action matrix](../action-resilience-audit-20261102/ACTION_MATRIX.md). Unix filesystems/off-host restore, actual RPC behavior and long-lived financial history remain open. |
| Website/UI/browser recovery and concurrency | Backend outputs are exercised, not a fresh browser/server rollout. Popldemo simulation, served poplint current3 and fresh source8 remain separate. Browser signer Anvil-only; public DEPLOYMENT null. Real current-profile website acceptance remains open. |
| Market extremes/manipulation | Controlled trends/reversals/active/mixed/outside geometry. No flash-loan or sequencer/profitability/MEV campaign, thin-depth sweep, independent reference-market liquidity assessment or real-price profit/IL claim. Known per-operation losses can accumulate; no cumulative cap was approved. |
| Random draw/artwork/OpenSea/storage | No images regenerated, no rerolls. Mock VRF is not live verification. Actual provider/reveal/drop integration and permanent hosting remain open. |
| Governance/key/service longevity | Existing roles/recovery controls reviewed; no governance address selected, server migrated, credential accessed or heartbeat restarted. Key loss and failed dependencies remain genuine release risks. |

These rows describe evidence coverage, not a second task ledger. Remaining work
stays in the [sole Todo](../../TODO.md) and [release approval](../../docs/RELEASE_CHECKLIST.md).
