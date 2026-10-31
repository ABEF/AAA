# Feature and evidence reference

Reviewed 2026-10-31. This records implemented source, not another task list.
[Todo](../TODO.md) owns work; [release approval](RELEASE_CHECKLIST.md) remains
**NOT APPROVED**. Existing contracts, services, websites and journals are unchanged.

## Current profile

Fresh **accounting6 / portfolio2 / maintenance3 / confirmation3 / compound4 /
custody4 / emergency2 / LP routing2**, with pricing2, Entry routing2, reviewed
Entry2, direct governance2 and fee intake1. The eight-word Position and compatible
parked same-chain canonical V6 wire remain; they do not imply old runtime compatibility.
[Profile](POSITION_V6.md), [implementation plan](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md).
Production inventory is schema8 with21 helper pins. Historical accounting5/4 and inventory7/6
profiles remain explicit and are never silently rewritten.

## Smart contracts

| Capability | Implemented behavior | Reference |
| --- | --- | --- |
| NFT identity | ERC-721, fixed artwork draw, exact1,000 rarity quotas; actual VRF provider still unqualified. | [Metadata](NFT_METADATA.md) |
| Contributions | ETH or the fixed ZZZ; future-governed minima(default$100 activation/$5 growth); checkpoint incumbents, use entrant-only budgets, verify marginal main LP, then issue shares from aggregate NAV. Residuals and rebalance centre/clock remain unchanged. | [Entry](ACTIVATION_ENTRY.md), [pricing](PRICE_SECURITY.md) |
| Shared LP portfolio | Single main by default, optional one residual in the same pool; both NFTs remain Vault-owned. Aggregate raw principal/valuation includes both actual ranges, not a sum of their liquidity units. | [Portfolio profile](POSITION_V6.md) |
| Ordinary replacement | Both single/hybrid verify the new main is physically active before/after callbacks; hybrid requires its configured6000–9999bps main floor(default60%) and complementary residual ceiling(default40%) at captured post-cost valuation. Natural placement meeting that floor needs no swap. Otherwise bounded approved-route sizing targets a rounding-safe floor. Failed sizing/mint/close reverts atomically. | [Execution policy](LP_EXECUTION_POLICY.md) |
| Residual geometry | Default half of the corresponding main side, a governed positive tick-spacing gap(default1) beyond spot. Width governed1–10000bps of that side. At most one residual; mixed/filled inventory remains valued until whole adjustment. | [Range controls](RANGE_POLICY_UPDATES.md) |
| Residual-only recovery | New paused governance-only Migration.closeResidual(ParkingRequest), explicit RESIDUAL_EXIT_VERSION1 across Migration/Vault/Manager/position child. Harvest both then burn only registered residual; exact raw proceeds to same bucket idle. Main/shares/clocks/configuration preserved; no swap/payout/compound release. | [Management controls](OPERATOR_MANUAL.md#portfolio-management-controls) |
| Enable/disable | Manual reviewed desired mode. Disabling does not discard live residuals; both remain valued/harvested until an atomic single-position merge succeeds after cooldown. | [Operator](OPERATOR_MANUAL.md) |
| Ordinary eligibility | 85% actual centre-to-edge human ZZZ-price distance; physical and independent reference on the same side.600-second sampled window/maxgap300, source240-second checks, fresh60–300-second service jitter, initial hard12hours. Manual geometry changes are a distinct cooldown-gated exception. | [Confirmation](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer) |
| Financial checks | Dual USD sources with3% agreement; captured default2% contribution/1% conversion/3% maintenance limits, governance ceilings10%, gas separate. Additional-loss default1% after known directional fees remains separate. | [Price security](PRICE_SECURITY.md), [execution quality](EXECUTION_QUALITY.md) |
| LP revenue | Combined actual fees from both legs allocated once per asset at80/10/5/5. Individual shares/equal active collective; no dormant dilution. Independent claims, compound and buyback reserves. | [Economics](ECONOMICS.md) |
| Royalties | Actual received funds; separate ×1/×2/×3 weights, outage isolation and guarded batch conversion. Unclaimed rights follow current ownership. | [Royalties](ROYALTY_SETTLEMENT.md) |
| Compounding | Existing range, both-leg NAV and separate interval after last compound/rebalance; keeper waits for in-range main below the adjustment threshold/no pending geometry. Entrants cannot spend incumbent idle/compound. | [Coordination](KEEPER_COORDINATION.md) |
| Recovery | Both-leg same-pair movement, raw paused parking and collective ETH+ZZZ holder return. Pending compound follows shares; rewards/buyback backing remain separate. Pre-exit canonical export requires every residual closed. | [Parking](CUSTODY_PARKING.md), [holder return](HOLDER_COLLECTIVE_EXIT.md), [canonical](CANONICAL_HANDOFF.md) |
| Emergency | Paused governance-only reviewed manifest; both-leg liquidity-sensitive fingerprint. Financial bypass is explicit and can lose nearly all principal; structural rights/ownership/settlement remain. | [Emergency](EMERGENCY_REBALANCE.md) |

## Backend and operations

| Capability | Implemented source boundary |
| --- | --- |
| Confirmed reads | Explicit accounting6 graph/runtime/version checks; both physical IDs/owners/keys/ticks/liquidity and aggregate principal authenticated at one confirmed block. Desired-disabled residuals remain included. Physical reads preserve owners/raw funded claims during price outages; valuations remain unavailable. No maintenance readiness inferred. Old profiles remain separate. |
| Unsigned activation/growth | Fresh graph including actual typed-executor verification, control and portfolio review binding; exact Manager→typed child→PosM trace and entrant marginal main liquidity; no public signing added. |
| Keeper | Fresh3 threshold/window semantics, durable jitter/reset/pending-first recovery, in-range compound wait, authenticated harvest coalescing and operation diagnostics. Raw checks during cooldown; paid observation enrollment near hard eligibility avoids waste. |
| Inventory | Schema8 validates21helpers, both physical legs and fresh capabilities. Schemas7/6 retain explicit historical inspection. Example is unqualified. |
| Manual operation preparation | Source-bound current callable reference plus exact operating procedures; the historical90-entry inventory retains its original scope. Ordered named inputs, actual caller/reversal and full tuple links. Offline reviewHash helper validates strict source-bound ABI shapes and preserves exact decimal strings; no live reads, simulation, signing, transaction or readiness claim. [Operator guide](OPERATOR_MANUAL.md#prepare-and-check-an-offline-reviewhash). |
| Earnings | Separate LP/collective/royalties, current-price USD, claimable versus earned/claimed, authenticated chronology and no duplicate income from claims/conversion/imports. Missing prices/data remain unavailable. |

See [API](FRONTEND_API.md), [unsigned preparation](ACTIVATION_PREPARATION.md),
[operation report](KEEPER_COORDINATION.md) and [preflight](PRODUCTION_PREFLIGHT.md).
Implementing source does not qualify a host, provider, maximum gas or operating latency.

## Frontend boundary

Popldemo remains simulation. Poplint's separately served current3 read/unsigned
build is not an accounting6 website consumer. The new backend projections and
preparation are local source; actual website acceptance remains open. Browser
signing stays Anvil-only; public DEPLOYMENT stays null. No source/build/server
change to the website is part of this contract implementation.
[Environment map](SITE_ENVIRONMENTS.md), [website profile](CURRENT_WEBSITE_PROFILE.md).

## Current evidence and limits

[Current adaptable-policy verification](../reports/adaptable-policy-20261031/VERIFICATION.md)
binds52production sources/31dependencies and43normal object gates at the unchanged
compiler settings. The reference explains37contracts/826function rows,37constructors
and14receivers, with zero recorded explanation gaps. Scoped EVM/backend methods,
intermediate failures/empty attempts and exact staged reuse remain separate; this
is not a fresh whole-suite/CI or independent approval.

The [earlier manual-operation audit](../reports/manual-operations-20261031/REVIEW.md),
[earlier source audit](../reports/day-audit-20261031/REVIEW.md) and
[residual management follow-up](../reports/residual-operations-20261031/REVIEW.md)
retain their original source scopes, failures and metrics. Their50-source/42-gate/
778-function/463-static records do not audit the later policy implementation.
The old internal static triage must be refreshed against a frozen current release;
independent review, target gas and economic/market/operating qualification remain open.

The [historical reconciliation](../reports/historical-reconciliation-completion-20261029/REVIEW.md)
maps earlier findings to mechanisms or remaining tasks without rewriting old
reports. Candidate-ranking liveness, maximum populated gas/dynamic URI and actual
provider behavior remain qualification work.

## Current selected-pool fork scope

The [selected-pool fork record](../reports/current-pool-fork-20261026/VERIFICATION.md)
is historical to its source/fixture/block. It verifies real-venue paths at those
pins using explicit mock services; it does not verify the new two-position
portfolio, live feeds/VRF, target gas, actual market depth or sustainable revenue.
Retain that evidence and qualify the exact fresh profile before release.

## Bounded post-seal flexibility

[ProtocolPolicy1](ADAPTABLE_POLICY.md) is implemented for future mint price/payee,
activation/growth minima, scoped entry/maintenance idle and bounded read/payout/
optional-sync gas, display tiers and fully drained VRF rotation. Portfolio2 adds
per-pool6000–9999bps main floor and positive tick-spacing gap; manual geometry can
extend below100% subject to Registry/tick bounds. Buyback maximum is reviewed and
changeable. Defaults remain0.05ETH/100USD/5USD,60/40,5%idle and original gas/stages.
New mint/Entry2 reviews bind scoped fingerprints; callback policy changes revert.
Source6/schema8/canonicalV6 are explicit, old deployed profiles remain unchanged.
[Current evidence](../reports/adaptable-policy-20261031/VERIFICATION.md) records fresh
normal gates, actual selected executions and limitations; it is not deployment,
whole-suite/CI/live qualification or independent audit approval.
