# Feature and evidence reference

Reviewed 2026-11-04. This records implemented source, not another task list.
[Todo](../TODO.md) owns work; [release approval](RELEASE_CHECKLIST.md) remains
**NOT APPROVED**. Existing contracts, services, websites and journals are unchanged.

## Current profile

Fresh **accounting6 / portfolio2 / maintenance3 / confirmation3 / compound4 /
custody5 / emergency2 / LP routing2**, with pricing2, Entry routing3, reviewed
policy2, direct governance2 and fee intake1. The eight-word Position and compatible
parked same-chain canonical V6 wire remain; they do not imply old runtime compatibility.
[Profile](POSITION_V6.md), [implementation plan](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md).
Production inventory is schema10 with20 helper pins. Historical schema9/custody4 retains direct Entry3 and20helpers; schema8 keeps
its routed Entry2 and21-helper profile; no conversion child remains on fresh Entry. Historical accounting5/4 and inventory7/6
profiles remain explicit and are never silently rewritten.

Use [consolidated findings](AUDIT_FINDINGS.md) for historical dispositions and
[the report map](../reports/README.md) for exact source-scoped evidence. A source
mechanism, test pass, configured service and approved production release are
separate milestones.

## Smart contracts

| Capability | Implemented behavior | Reference |
| --- | --- | --- |
| NFT identity | ERC-721, fixed artwork draw, exact1,000 rarity quotas; actual VRF provider still unqualified. | [Metadata](NFT_METADATA.md) |
| Contributions | ETH or the fixed ZZZ; future-governed minima(default$100 activation/$5 growth); checkpoint incumbents, use entrant-only budgets, verify marginal main LP, then issue shares from aggregate NAV. Residuals and rebalance centre/clock remain unchanged. | [Entry](ACTIVATION_ENTRY.md), [pricing](PRICE_SECURITY.md) |
| Shared LP portfolio | Single main by default, optional one residual in the same pool; both NFTs remain Vault-owned. Aggregate raw principal/valuation includes both actual ranges, not a sum of their liquidity units. | [Portfolio profile](POSITION_V6.md) |
| Ordinary replacement | Both single/hybrid reject inactive stored-tick quotes before ranking and verify the new main is physically active before/after callbacks; hybrid requires its configured6000–9999bps main floor(default60%) and complementary residual ceiling(default40%) at captured post-cost valuation. Natural placement meeting that floor needs no swap. Otherwise bounded approved-route sizing targets a rounding-safe floor. Failed sizing/mint/close reverts atomically. | [Execution policy](LP_EXECUTION_POLICY.md) |
| Residual geometry | Default half of the corresponding main side, a governed positive tick-spacing gap(default1) beyond spot. Width governed1–10000bps of that side. At most one residual; mixed/filled inventory remains valued until whole adjustment. | [Range controls](RANGE_POLICY_UPDATES.md) |
| Residual-only recovery | New paused governance-only Migration.closeResidual(ParkingRequest), explicit RESIDUAL_EXIT_VERSION1 across Migration/Vault/Manager/position child. Harvest both then burn only registered residual; exact raw proceeds to same bucket idle. Main/shares/clocks/configuration preserved; no swap/payout/compound release. | [Management controls](OPERATOR_MANUAL.md#portfolio-management-controls) |
| Enable/disable | Manual reviewed desired mode; enabling permits rather than forces a residual. Disabling retains both actual legs and NFT reward membership until a guarded single-position merge succeeds; no immediate deactivation or trade. | [Operator](OPERATOR_MANUAL.md) |
| Ordinary eligibility | 85% actual centre-to-edge human ZZZ-price distance; physical and independent reference on the same side.600-second sampled window/maxgap300, source240-second checks, fresh60–300-second service jitter, initial hard12hours. Manual geometry changes are a distinct cooldown-gated exception. | [Confirmation](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer) |
| Financial checks | Dual USD sources with3% agreement; captured default2% contribution/1% conversion/3% maintenance limits, governance ceilings10%, gas separate. Additional-loss default1% after known directional fees remains separate. | [Price security](PRICE_SECURITY.md), [execution quality](EXECUTION_QUALITY.md) |
| LP revenue | Combined actual fees from both legs allocated once per asset at80/10/5/5. Individual shares/equal active collective; no dormant dilution. Independent claims, compound and buyback reserves. | [Economics](ECONOMICS.md) |
| Royalties | Actual received funds; separate ×1/×2/×3 weights, outage isolation and guarded batch conversion. Unclaimed rights follow current ownership. | [Royalties](ROYALTY_SETTLEMENT.md) |
| Compounding | Existing range, both-leg NAV and separate interval after last compound/rebalance; keeper waits for in-range main below the adjustment threshold/no pending geometry. Entrants cannot spend incumbent idle/compound. | [Coordination](KEEPER_COORDINATION.md) |
| Recovery | Both-leg same-pair movement, raw paused parking and collective ETH+ZZZ holder return. Custody5 allocation/distribution is governance-only; holder LP/royalty/fallback claims remain. Pending compound follows shares; rewards/buyback backing remain separate. Pre-exit canonical export requires every residual closed. | [Parking](CUSTODY_PARKING.md), [holder return](HOLDER_COLLECTIVE_EXIT.md), [canonical](CANONICAL_HANDOFF.md) |
| Emergency | Paused governance-only reviewed manifest; both-leg liquidity-sensitive fingerprint. Financial bypass is explicit and can lose nearly all principal; structural rights/ownership/settlement remain. | [Emergency](EMERGENCY_REBALANCE.md) |

## Backend and operations

Confirmed-read and preparation boundaries remain explicit. RPC endpoints are a
validated immutable snapshot, budgeted convenience calls use the metered path,
and strict new-work validation does not discard a valid pending recovery intent.

| Capability | Implemented source boundary |
| --- | --- |
| Confirmed reads | Explicit accounting6 graph/runtime/version checks; both physical IDs/owners/keys/ticks/liquidity and aggregate principal authenticated at one confirmed block. Desired-disabled residuals remain included. Physical reads preserve owners/raw funded claims during price outages; valuations remain unavailable. No maintenance readiness inferred. Old profiles remain separate. |
| Unsigned activation/growth | Fresh graph including actual typed-executor verification, control and portfolio review binding; exact Manager→typed child→PosM trace and entrant marginal main liquidity; no public signing added. |
| Keeper | Fresh3 threshold/window semantics, durable jitter/reset/pending-first recovery, in-range compound wait, authenticated harvest coalescing and operation diagnostics. Raw checks during cooldown; paid observation enrollment near hard eligibility avoids waste. |
| Inventory | Schema10/custody5 validates20helpers, both physical legs and fresh capabilities. Schemas9/8/7/6 retain explicit historical inspection. Example is unqualified. |
| Manual operation preparation | Source-bound current callable reference plus exact operating procedures; the historical90-entry inventory retains its original scope. Ordered named inputs, actual caller/reversal and full tuple links. Offline reviewHash helper validates strict source-bound ABI shapes and preserves exact decimal strings; no live reads, simulation, signing, transaction or readiness claim. [Operator guide](OPERATOR_MANUAL.md#prepare-and-check-an-offline-reviewhash). |
| Earnings | Separate LP/collective/royalties, current-price USD, claimable versus earned/claimed, authenticated chronology and no duplicate income from claims/conversion/imports. Missing prices/data remain unavailable. |

Explicit fresh read/keeper configs set custody_version5 and check actual runtime.
Keeper principal_distribution is disabled/rejected on5; governance pays/submits
terminal batches. Owner earned-reward claims remain available.
[Full permissions](ACCESS_PERMISSIONS.md).

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

## Collective exit scale and mixed-wallet evidence

[Focused assurance](../reports/holder-exit-assurance-20261103/REVIEW.md) adds corrected
1000-NFT enumeration, distinct-address and37-wallet mixed-holdings checks plus
real NFT rarity/tier/growth/prior-claim/transfer composition and local real-v4
both-leg exit.10distinct selected methods span explicit stages, including one
1000-case fuzz method. Production source/policy/profile are unchanged; normal
size/static evidence is reused at matching pins. Failed stale-fixture attempts
remain recorded. This is not target-chain gas, full-suite or independent approval.

## Current whole-project supplement

[November4 review](../reports/comprehensive-audit-20261104/REVIEW.md) fixes the
indexer's borrowed configuration anchor and streams ownership replay.33affected
Python methods pass, including6new regressions. Negative-control failures are
retained. All production Solidity/dependency/build pins are unchanged; no EVM,
static or size result is presented as a fresh rerun. Website documentation is
aligned without changing its source behavior, signer, builds or served releases.
Storage/lifetime replay and actual operating qualification remain open.

## Market/lifecycle assurance

The [market/lifecycle campaign](../reports/market-lifecycle-20261104/REVIEW.md) adds7new actual-core journeys plus
one affected six-day control and7new current-profile API/keeper methods.
Separate receipt-derived reward fractions, fair shares, both-leg NAV, mode
transitions, outages, transfers and terminal royalties/payouts are reconciled.
Failed test-model/RPC-fixture attempts remain recorded; production code and
operating settings are unchanged. No profit, uptime or release approval.

The independent test ledger uses pre-operation participant snapshots and
actual credit events, not production reward-index getters. The operator
profile sentence now correctly requires custody5. No new management call,
policy, restart or economic right is introduced. See [coverage](../reports/market-lifecycle-20261104/COVERAGE.md).

## Confirmation scheduling and recovery

The [confirmation audit](../reports/confirmation-audit-20261104/REVIEW.md) fixes daemon sleep ignoring saved maturity/
jitter deadlines and queued incident clears depending on unrelated router
metadata.100focused Python methods pass, including14new regressions; causal
negative failures are retained. Contracts/settings/journals are unchanged.
A reviewed matching keeper source rollout remains required; no service was
changed.600/240/300 and the hard12hours remain, with sampled/live limits.

## Current evidence and limits

| Evidence | Source scope | What it does not establish |
| --- | --- | --- |
| [Authority change normal/static record](../reports/authority-audit-20261103/VERIFICATION.md) | Current52production/31dependency sources;43normal gates/471static records,19current contexts reviewed and452unchanged reused.14distinct selected EVM passes across explicit corrected stages;25corrected Python methods. Reference37/818/37/13 has0gaps; Migration39/Vault635/Budget237/Balancer360runtime headroom. | No full suite/CI, independent review, deployment gas, service or production approval. |
| [Direct Entry3 normal/static record](../reports/direct-entry-v3-20261103/VERIFICATION.md) | Prior custody4 source52production/31dependency sources;43normal gates,471triaged static records; reference37contracts/818functions/37constructors/13receivers without note gaps. Entry runtime9863; Vault635/Budget237/Migration20/Balancer360headroom. | Full regression, published CI, independent audit, deployment gas, future edit capacity or production approval. |
| [Entry/native regressions](../reports/direct-entry-v3-20261103/test-stages.json) |28distinct selected successes across recorded scopes;19unchanged successful bodies reused after one assertion correction. Failures and empty selection retained. |28fresh final-source tests in one run, actual target-chain feeds/venues or browser/keeper operating acceptance. |
| [Backend/profile tooling](../reports/direct-entry-v3-20261103/python-verification.json) |314selected Python successes across two scopes; explicit direct/historical tuple, config/helper/observer and operator/reference/publication boundaries. |Actual tracing-provider or matching website acceptance. |
| [LP lifecycle](../reports/lp-lifecycle-audit-20261102/REVIEW.md), [multi-day journeys](../reports/portfolio-long-horizon-20261102/VERIFICATION.md) | Ordinary active-main candidate selection and composed main/residual/entry/reward/recovery behavior at recorded source/test pins. Relevant unchanged code can support reuse. | All market paths, profitable60/40 strategy, maximum populated gas or live uptime. Geometry getter coherence is not independent source proof. |
| [Backend/action consolidation](../reports/consolidation-20261103/VERIFICATION.md), [fault boundaries](../reports/action-resilience-audit-20261102/ACTION_MATRIX.md) | Scoped endpoint, budget, validation, receipt and availability corrections. | Honest providers, hard DNS/header timeouts, Linux host/storage/off-host recovery or source rollout. |
| [Documentation/findings consolidation](../reports/project-consolidation-20261103/REVIEW.md) | Current procedures/navigation/finding provenance and exact unchanged-source/evidence checks. | New contract execution, new independent security opinion or closure of external release gates. |

Older source/ABI/size/static/test counts remain in immutable reports and are not
combined into a current pass. Refresh applicability after code/settings/dependency
changes. The [compiler assessment](../reports/direct-entry-v3-20261103/compiler-assessment.json)
uses an explicitly captured official snapshot with source graph/layout limitations;
refresh advisories for the frozen release.

## Current selected-pool fork scope

[Prior fork evidence](../reports/current-pool-fork-20261026/VERIFICATION.md) is historical.
The current harness is source preparation, not a newly executed fresh portfolio/
Entry3 fork. Qualify actual pool state/depth, feeds, original-input execution,
burn ABI, market cost and target gas before approval. Do not lower policy or
label mocked prices a production feed to turn an infeasible quote into a pass.

## Bounded post-seal flexibility

[ProtocolPolicy1](ADAPTABLE_POLICY.md) governs approved future terms within fixed
bounds; Entry3/review-policy2 binds scoped contribution terms before callbacks.
[Manual controls](OPERATOR_MANUAL.md#future-operating-settings) distinguish a chain
setter from a new runtime/worker/site rollout. Retired architecture and old
journals remain separate. Real providers/authorities/OpenSea, source8 services/
website, storage/operations, economics/gas and independent audit remain open.
