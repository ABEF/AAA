# Engineering roadmap

Current [whole-project execution](../reports/whole-project-execution-20261029/REVIEW.md) completes the internal
source/body review and implements keeper deadline priority, strict durable/log
provenance, final-depth/fee/pool observation and artifact-tooling repairs.
All122previously missing callable outputs are explained. Static review is not
exhaustive execution or independent release approval. Website reference metadata
is corrected locally without changing images/signing/configs or deploying sites.
Actual providers, economics, gas/host/marketplace qualification and audit remain open.

Current fresh source: **accounting4 / custody3 / canonical holder-exit V5**.
[Collective holder return](HOLDER_COLLECTIVE_EXIT.md) replaces external principal
and royalty custody exits. Governance permanently ends LP and pays actual
ETH+ZZZ by shares; NFTs retain transfers, future royalties and earned rewards.
No external recipient/bridge/return ingress remains. Whole-collection handoff
is available only before exit. Earlier source-scoped evidence and accounting3
service/inventory/website qualification remain historical to their original pins.
See [profile4](POSITION_V4.md); new release qualification remains open.


Reviewed 2026-10-29. This page explains dependencies and sequence; [TODO.md](../TODO.md)
is the only status list. [Feature reference](IMPLEMENTATION_STATUS.md) records what
exists, while [release approval](RELEASE_CHECKLIST.md) remains NOT APPROVED.

Current [keeper coordination](KEEPER_COORDINATION.md) implements service-only
in-range/no-pending-width waits, canonical internal-harvest coalescing and
bounded read-only LP reports. Qualify the extra pinned RPC reads and matching
worker/checker rollout; remaining action adapters retain their own Todo.

Current maintenance candidate: [compound cadence V3 / upkeep policy2](OPERATOR_MANUAL.md#coordinate-compounding-with-rebalancing) is coordinated on-chain with LP replacement and rebalance/range priority. Match keeper/helper versions and qualify actual economics/services; no24-hour default or new cumulative-loss breaker is assumed.

Current source has completion/health safeguards ([scope](../reports/manipulation-hardening-20261027/VERIFICATION.md)). Continue economic review of [keeper-originated manipulation](../TODO.md#task-security-keeper-manipulation)
and [outside-actor manipulation](../TODO.md#task-security-external-manipulation).
Use actual Robinhood ordering, independent prices and attacker/protocol profit
witnesses; protected submission and economic safety are not already qualified.

Manual upkeep is documented in [the operator procedure](OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time):
existing keeper authority and on-chain guards remain; same-key out-of-band signing
requires journal reconciliation. This is a documentation clarification, not a
new implementation or release qualification.

The [two-day audit](../reports/two-day-audit-20261028/REVIEW.md) adds bounded principal-return retries and serial-job fairness. Qualify the actual optional delivery worker with persisted retries, pending recovery, receiver deferral/backlog alerts and other post-exit work before enabling it. Keep [the safeguards inventory](KEEPER_SAFEGUARDS.md) current; publication is not service rollout.

The [implemented fee-quality slice](EXECUTION_QUALITY.md) separates known core
trading fees from a1% default additional oracle-relative loss floor, retaining
gross/caller/total limits. Qualify real depth/prices/gas and matching runtime/config
before rollout; defensive local checks do not establish attacker-profit immunity.
Passive inventory and40% triggers remain discussion only. Current confirmation2
implements independent same-side exit and a15-minute sampled window with four-minute eligible checks and strict
300-second maximum confirmed gap. Qualify actual observation/reset/jitter timing;
delays restart and no uninterrupted-price proof is claimed. [Owning task](../TODO.md#task-rebalance-confirmation-buffer).

The [day audit](../reports/day-audit-20261028/REVIEW.md) records current gaps rather
than reopening unchanged test campaigns. Later [practical improvements](../reports/practical-improvements-20261028/VERIFICATION.md)
implement schema6/accounting4 preflight and anchored quality telemetry. Real
addresses/services, matching health writer/checker rollout and complete-operation
target gas budgets remain unqualified.

The deeper buffer audit also fixes unrelated-job resets, repeated paid clears,
old-window jitter reuse, failed-related-receipt recovery, incompatible outer
polling, clock retreat and contradictory lifecycle/ABI observations. Budget now
captures raw observation state across maintenance; callback invalidation reverts
the complete LP operation. Post-exit governance orientation remains available
without reopening principal. Final evidence:217affected Solidity passes,
272distinct source-scoped Python methods (271pass/1missing-cast skip),39normal
object gates. Counts are scoped, not a global security or production approval.

[Review and evidence](../reports/practical-improvements-20261028/VERIFICATION.md).

The [follow-up repairs](../reports/confirmation-followup-20261028/VERIFICATION.md)
close local reset/admission/reporting inconsistencies without changing Solidity.
Before rollout, recollect schema6 physical ticks/PoolKey/PositionInfo, deploy a
matching health writer/checker, and qualify the extra pinned RPC reads, strict
300-second receipt cadence and preserved pending recovery on actual services.
These remain operating gates;398scoped Python passes do not close them.

The [third-pass repairs](../reports/third-pass-20261028/REVIEW.md) also require
operating qualification of used-signer checkpoint outages and malformed/future
conversion/indexer observations. Preserve pending-first recovery, strict sampled
cadence and separately guarded harvest; no new strategy decision or gate relaxation.

Current source additionally implements [confirmation2 and manual emergency1](EMERGENCY_REBALANCE.md).
Ordinary samples require physical/reference same-side exit; automatic width
policies cannot bypass that guard. Governance can review policy relaxation or
manually perform a paused emergency with optional financial checks. Exact
accounting/custody/lifecycle remain; nearly all principal may be lost if financial
guards are disabled. [Source-scoped review/evidence](../reports/independent-rebalance-20261029/VERIFICATION.md)
does not qualify feeds, economic profitability, actual gas/services or an
independent audit. No installed service/site/Anvil/deployment changed. The wider
current handwritten-body review is recorded in the [whole-project execution](../reports/whole-project-execution-20261029/COVERAGE.md); historical reports retain their pins.

## LP execution next steps

The [whole-project repairs](../reports/whole-project-audit-20261029/REVIEW.md)
need controlled API/keeper source rollout and actual confirmation latency,
metadata-stall recovery and health compatibility qualification. Four-minute
source checks are implemented; the separate proposed improvement to observe
during cooldown needs a reviewed contract change and gas/reset assessment while
preserving the hard12-hour execution minimum. Keep that proposal separate from
release approval, current3/fresh4 browser integration and live provider work.

The three timing decisions are settled: hard initial12-hour minimum even outside,
operator width application inside after cooldown, and independent compound interval.
The [implemented source slice](../reports/maintenance-policy-20261027/VERIFICATION.md)
includes Strategy2/Budget3, durable keeper jitter and matching API profile; qualify
actual rollout/runtime/config/operations separately. Keep operator-selected widths,
independent hourly harvest and fixed rights. Continue [execution routing](../TODO.md#task-lp-execution-routing):
LP routing1 bounded approved venues, actual-core post-close sizing and zero/one
swap are now implemented with entrant-only budgets and retained idle. Qualify
actual catalog/depth/gas, exact service pins and economic ordering next; see
[new evidence](../reports/atomic-routing-20261028/VERIFICATION.md). Global optimality
and timed10% replacement are not implemented or release claims. [Policy record](LP_EXECUTION_POLICY.md).

## 1. Close immutable integration boundaries

Qualify and finish [OpenSea primary mint](../TODO.md#task-opensea-mint), preserving
canonical NFT recipient,0.05ETH gross buyer price and net recipient proceeds,
fixed inventory, original randomness, mint pause and atomic failure. Select and
qualify the actual proof-verifying randomness provider. Direct mint/mock VRF
tests do not establish that integration.

Approve artwork root, fixed ZZZ identity, authority/module bindings, conversion
and collective holder-return behavior before sealing. Governance shutdown returns
actual ETH+ZZZ to holders, with no external custodian or issuer-exchange executor. Same-chain collection handoff and its real backing must retain all
ownership/reward rights. See [current boundaries](SIMPLIFIED_RELEASE.md).

## 2. Qualify real dependencies alongside integration

Select independently reviewed ETH/ZZZ feed pairs, source freshness/updater/RPC
policies, actual contribution/conversion routes and fixed-ZZZ burn semantics.
The selected pool's recorded fee exceeds the default1% conversion cap, so qualify
a cheaper route or make an explicit governed policy decision; never silently
widen caller limits. Complete [creator questions](../TODO.md#creator-tasks--zzz-team)
about token/source controls; creator-payment funding is no longer a launch feature.

Authentic complete event history, archive access and same-block observations are
required for earnings. Current credit/dust/head reconciliation does not prove
every receipt/timestamp. Verify original source-currency history at today's prices
without conflating earned, claimable and claimed amounts.

## 3. Integrate the exact current deployment profile

Use the separate [poplint integration target](SITE_ENVIRONMENTS.md) for the
explicit current3 website/API reader and unsigned reviews. Preserve the existing
popldemo simulation, root, configuration and content; do not roll integration
changes into that live demo. Public signing remains disabled. Existing native2 or legacy Anvil profiles
are not upgraded by relabeling. Rehearse approval/contribution/claim/recovery and
account/network changes against the exact reviewed configuration. See
[website boundary](NATIVE_WEBSITE_PROFILE.md) and [wallet task](../TODO.md#task-wallet).

Use the corrected config-bound health/strict conversion controls and explicit
current3 rehearsal source, then qualify hosted services, concurrent request budgets, index recovery, keeper
restart/nonce/fee-review recovery, backups, monitoring and operator rotation.
Validate real target-chain maximum-state gas and range/maintenance economics;
local synthetic tests do not establish capacity or uninterrupted uptime.
Qualify the [separate revenue jobs](OPERATIONS.md#reward-timing-and-maintenance-schedule)
with actual batch sizes, gas, harvest/conversion/compound/burn latency and backlog
alerts. The local claim-conservation and buyback-fairness checks do not enable
the placeholder service or turn allocated reserves into executed trades.
Exercise [maintenance-outage harvest isolation and claim-integrity checks](../reports/reward-resilience-20261026/REVIEW.md)
under actual provider/service conditions, including degraded health and saved
pending recovery. Local fault fixtures do not close those operating gates.

For market/input acceptance, retain the [exact slot0 consistency checks](../reports/market-adversarial-20261026/REVIEW.md)
and exercise both out-of-range directions, valid tick boundaries and actual
funded donations against the qualified deployment. Consistent observations do
not authenticate an RPC, and funded fee history does not prove organic volume.
The [current selected-pool fork](../reports/current-pool-fork-20261026/VERIFICATION.md)
adds11distinct successful real-venue methods with explicit mock services and
retained failed/repaired attempts; it is not a fresh whole final suite. Native
and fixed-ZZZ entry, small growth, actual fee harvest/transfer rights and
unfillable-growth rollback are covered at one pinned block. These cases do not
close actual independent pricing, cheaper conversion routes, keeper economics,
provider/service or operating gates.

The [per-callable adversarial matrix](../reports/system-adversarial-20261026/COVERAGE.md)
provides an exact source-review starting point for the independent auditor, not
proof of execution for every scenario. Retain the stricter RPC/holder-input
boundary behavior and main-progress systemd watchdog in actual provider/recovery
rehearsals, including stalled DNS/header/body, killed signer descendants and
no-resend pending recovery. A valid provider
identity, inventory checksum or local pass is not authentic-history or release
approval.

## 4. Freeze and approve a complete release

Select exact source/configuration/authorities. Run the relevant final release
checks, independent audit and remediation, then named reviewer sign-off in the
release record. Reuse unchanged evidence with exact hashes; avoid repeating
unaffected suites during routine documentation or backend fixes.

Deployment, public signing and real-fund rehearsal require separate authorization.
The three verification layers remain local adversarial tests, selected Robinhood
mainnet fork and Robinhood Testnet/operator rehearsals. Qualify holder-exit batch
gas, failure isolation, current-owner rights and separate principal reporting.
Future-chain canonical relocation, post-exit successor import and post-halt
recovery are outside this release.
