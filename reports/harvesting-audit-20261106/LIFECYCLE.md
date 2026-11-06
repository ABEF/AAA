# Harvesting paths and classification

Read against baseline11e0157 production Solidity, unchanged in this audit.
The table is source tracing, not a claim that every row received a new EVM run.
[Verification scopes](VERIFICATION.md), [findings](REVIEW.md).

| Path | Order and allocation boundary | Verification / limit |
| --- | --- | --- |
| Standalone collect | Permissionless sealed/live/unpaused Active bucket; collect main then residual; allocate actual aggregate per currency. | New actual-core comparison and existing both-leg controls. No swap, L/share change or price read. Both-leg failure atomic. |
| First activation | No prior bucket supply/owned LP fees; deployment precedes first eligibility. | Source trace plus existing initial-entry evidence; no fabricated pre-activation LP revenue. |
| Activation in existing bucket | Settle already funded dust across bounded buckets; collect current bucket before shares/membership; collect entrant-swap fees under incumbent weights; checkpoint before issuance. | New nonzero actual-core entrant/claim case; current split/fraction policies retained. |
| Growth | Same incumbent harvest and share checkpoint; increases main only, leaves residual L/membership unchanged. | New actual-core checkpoint case; no entrant subsidy or recenter. |
| Standalone compound | Harvest both, release designated reserve, capture backing, balance existing idle; harvest own-swap fees before main increase. | Source trace and exact-scope prior composed controls. A successful Compounded amount can exclude already idle/reinvested funds. |
| Ordinary rebalance / mode merge | Harvest both, release compound, close both, guarded replacement. | Source trace/current moving-market evidence; FeesCollected proof coalesces only matching own paid receipt. |
| Same-pair move | Harvest current source, release compound and close both before destination deployment. | Source trace/prior destination tests; source pool identifies receipts, not the new alias. |
| Parking | Governance paused internal harvest/compound release/close, actual proceeds to attributed idle. | Source trace/prior raw recovery. Public collect is blocked by global pause. |
| Resume | Parked principal re-enters selected same-pair pool; no invented new historical fees. | Source trace/prior destination-mode tests; ordinary price/financial guards remain. |
| Close residual only | Harvest both, close only registered residual into attributed idle; no designated compound release or implicit mode change. | Source trace/prior residual tests; late compromised-dependency fees remain a documented boundary. |
| Same-main consolidation | Harvest both, close residual if present, balance attributed inventory, harvest main self-swap fees then increase same main. | Source trace/current same-main controls; phase4 reserves remain separate. |
| Full emergency replacement | Paused governance harvests/closes both before explicit swap/redeployment; optional financial checks are manifest-selected. | Source trace/prior manual-safeguard evidence; not ordinary keeper fallback. |
| Terminal holder return | Harvest both, flush fee carry, release compound, close actual ETH/ZZZ; classify principal separately. | Source trace/prior holder assurance; no later LP reopening. Old funded rewards/royalties survive. |
| Canonical preparation/cutoff | Standalone collection can remain available in announcement phase while canonicalState0/live; frozen/captured lifecycle uses dedicated cutoff settlement. | Source trace/prior canonical evidence, not blanket pause assumptions. Registered residuals must be closed before capture. |
| Canonical import/abort | Carry classified backing/indices/fractions and restore original records according to exact V8 lifecycle. Import is not new earnings. | Existing profile, unchanged source; exact-unit LP upgrade needs a NEW reviewed format. |
| Holder claim | Current owner checkpoints personal/equal balances and pays already funded rights; no venue collection or 5% jobs. | New finite-final-unit counterexample plus prior ownership/claim evidence. USD price not required. |
| LP conversion | Convert selected already-earned whole source balances to attributed ETH for the same NFTs/components. | Source trace/prior converter evidence; no new income or current-weight redistribution. |
| Buyback | Separate keeper release/execution/burn of its classified5%reserve. | Source trace/prior execution evidence; reserve funding alone is not a burn. |

## Accounting checks per asset

Reconcile actual receipt with holder funding, retained split carry, compound and
buyback. Then reconcile holder liabilities with paid whole units and retained
LP fractions/index dust. A claimable-only total does not equal all allocated
holder funding in the current fractional profile. Never sum ETH and ZZZ raw
units or main/residual raw liquidity; use independent per-currency balances.

For20unit blocks, no intervening flush gives16/2/1/1. With a barrier, carried
units go to existing personal rights; calculate each receipt and barrier in
order. Released compound moving to Vault idle changes its custody category, not
its economic owner or entrant floor. Zero-fee collection is a successful check,
not new income. Donations to core can create fees; raw prefunds cannot fabricate
a declared receipt.
