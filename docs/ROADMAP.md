# Engineering roadmap

The [current review](../reports/whole-project-review-20261111/REVIEW.md) closes
proven cleanup/encoding/indexer/keeper/UI defects. Next resolve the spot-reference
versus execution-venue coupling and qualify actual dependencies/operations.
Do not delete historical readers or reinterpret stored demo events.


The [read-only feed/route follow-up](../reports/market-followup-20261109/REVIEW.md)
is complete at its documented anchors. Next obtain two defensible ZZZ USD
provider proposals, resolve funded ETH publication and Robinhood liveness,
then qualify useful route depth and complete operations with those real prices.
API3 is a concrete inactive option requiring separate initialization/funding/ABI
review. Dedicated archive/trace service remains necessary. The sole Todo owns
status; do not repeat unchanged mock suites to close external dependencies.


The local [source10/mint2/V10 website consumer](SOURCE10_WEBSITE_PROFILE.md) now
implements current read/unsigned flows alongside source9/V9. Next review the
actual deployed graph, independent feeds/routes, OpenSea/VRF/provider and gas
configuration, then wallet/hosting/operating acceptance before separately
authorizing a rollout. Existing current3 poplint, popldemo and Anvil8902 stay
unchanged. The sole Todo retains qualification and release statuses.

The [OpenSea source integration](OPENSEA_MINT.md) adds mint2/helper1,
canonicalV10 and schema17 with20 callable helpers plus2 inert data children.
Initial20free-team/500paid-allowlist/480public allocations are configurable;
AL is one NFT per distinct listed address, unused AL rolls public and
unused team stays reserved. Original-recipient lifetime mint counts,
dormancy and original two-word VRF requests are preserved. Normal size
limits remain unchanged; see the [source-scoped verification](../reports/opensea-integration-20261109/VERIFICATION.md).
Backend read/claim and lineage support is implemented with explicit mint2/V10
pins; default1 remains V9 and direct mint2 preparation returns Use OpenSea.
Actual OpenSea custom-drop onboarding, exact fee/payers, live VRF/gas, matching
website rollout/installed-consumer and operating/independent acceptance remain open.
Earlier V9/schema16 evidence below retains its original scope; it does
not verify the mint extension or upgrade a served site/runtime.


The local [source9 browser consumer](SOURCE9_WEBSITE_PROFILE.md) now implements
fresh reads and unsigned reviews, including policy2 claim planning and optional
activation gas2. The [actual fork follow-up](../reports/source9-actual-entry-20261109/REVIEW.md)
executes ETH/ZZZ activation/growth but needs explicitly seeded external depth.
Next qualify actual market depth/routes, independent feeds, provider/fee manifests,
wallet and operating loads, then separately authorize API/poplint rollout.

The [fee-flow audit](../reports/fee-flow-audit-20261107/REVIEW.md) closes source
defects in final-ETH floors, keeper conversion capacity/deadline/day handling and
zero-noop replay. Optional gas policy2 is implemented without rollout; next qualify
actual cheap1% routes/native feeds and matching schema2 consumers/providers/fees,
then actual gas/recovery and independent audit. The soleTodo owns statuses.

Reviewed9November2026. [The sole Todo](../TODO.md) owns statuses; this page orders
work and dependencies. [Findings](AUDIT_FINDINGS.md) explain current mechanisms
and unresolved risks. Production **NOT APPROVED**. Source publication is separate
from deployment, services, websites and public transactions.

[Exact-unit LP integration](../reports/exact-lp-integration-20261106/REVIEW.md) connects the actual host, claims, lossless raw-tree handoff and explicit consumers. That earlier source had runtime headroom133bytes for Vault,358 for Rewards and32 for CanonicalHandoff; the current mint2 record is32/358/176 respectively, normal compiler limits are unchanged. Earlier moving-market source/evidence remains historical.

## 1. Freeze the correct source and integration boundary

The earlier [accounting7/LP-allocation1/V9/schema16](POSITION_V7.md) milestone wires authenticated shares/membership, current-owner whole claims and same-NFT conversion. The fixed RewardsCanonical child preserves exact pending/phase state, complete funding and abort without flattening rights. That milestone's source/size/static/consumer evidence is in the [original integration verification](../reports/exact-lp-integration-20261106/VERIFICATION.md); use the [report map](../reports/README.md) for later mint2/V10 and current3% source records. Historical6/V8, old checkpoints and journals remain distinct. This is an accounting upgrade, not a behavior-preserving cleanup or deployed upgrade.

Preserve completed direct Entry, residual management, active-main routing, cooldown observation and authenticated harvest coalescing. Do not revive removed bridges, creator inboxes or third LP inputs. Target deployment arguments, maximum-workload gas/economics and independent review still require the exact final candidate.

Owning work: [release freeze/audit](../TODO.md#task-audit-release),
[deployment size/gas](../TODO.md#task-deployment-initcode),
[reviewed contributions](../TODO.md#task-reviewed-contribution-policy).

The [residual lifecycle follow-up](../reports/residual-lifecycle-20261106/REVIEW.md)
added historical6 physical read admission and missing destination-hybrid composition
evidence. Production Solidity/normal/static pins remain unchanged. Actual token/
periphery callbacks, maximum workload and source rollout remain qualification.

## 2. Qualify real dependencies and market execution

The [actual market review](../reports/market-qualification-20261109/REVIEW.md)
establishes concrete blockers: no usable dual ETH/fixedZZZ pair, stale Pyth
updates, unqualified liveness/provider policy and direction-specific execution
constraints. Qualify independent ZZZ sources with the team, an operating ETH
updater/alternative, actual bidirectional depth and a default1%-eligible route.
Quote/slot/source observations are not admission approval or future guarantees.

Select and authenticate independent ETH/ZZZ USD sources, feed/proxy/update controls,
actual fixed token/burn behavior, reviewed balancing/conversion venues, RPC tracing,
VRF and authorities. Test usable depth/cost without substituting demo values or
widening captured user limits. Actual cheap ETH conversion remains necessary at
the default1% budget; bounded routing is not a universal best-route guarantee.
Qualify OpenSea primary mint/drop, gross buyer price and actual platform fee.

Owning work: [dual feeds](../TODO.md#task-dual-price-qualification),
[ZZZ-team questions](../TODO.md#creator-tasks--zzz-team),
[routing](../TODO.md#task-lp-execution-routing),
[draw](../TODO.md#task-fair-draw), [OpenSea](../TODO.md#task-opensea-mint).

## 3. Integrate matching services and site without changing old profiles

Qualify reviewed schema17/mint2/V10 configs and the implemented opt-in2
API read/claim/lineage path. Update remaining indexer/keeper/health/website
consumers explicitly, preserving source9/schema16 as a prior profile. Build and
qualify the matching accounting7/direct Entry3 website consumer on poplint. Popldemo
remains simulation; served current3 and historical Anvil/journals remain their
original profiles. Public DEPLOYMENT stays null and signing Anvil-only.

The [unsigned operator extension](../reports/operator-management-20261109/REVIEW.md)
adds reversible parking/resume/residual closure and all terminal holder-return
steps, alongside existing Active B/C/D. Qualify actual operator-selected floors,
provider/hash/complete-fee support, target gas and wallet execution. Parked
forced-D and contract-wallet envelopes remain separate manual procedures.
Preparation adds no signing, queue, force/recenter fallback or execution approval.

Qualify the new explicit claim planner with actual worst-case currencies/fees,
confirmation/replanning and no silent omission; bounded local planning is not a
maximum-batch or live-wallet gas guarantee.
Qualify actual preparation/trace/approval/claims and truthful complete holdings/
history, unavailable states, account changes and pending recovery. Fresh7 supports complete raw exact-tree replay or explicit reviewed checkpoint2 for earnings. Qualify actual suffix workloads, archival/rotation/restore and operator approval before claiming bounded lifetime operation. Checkpoint1 remains6-only. Extend lineage/other full-history consumers and review archival/rotation/source-codec evolution.
Fresh royalty4/reporting5/canonicalV10 retains the exact-unit cursor/cohort history and
reviewed checkpoint rebuilds. No converter or new deployed allocator is added.
A new service/config rollout needs stop/reconcile/dry-run/restart, not a version edit.

Owning work: [preflight](../TODO.md#task-native-production-preflight),
[hosting](../TODO.md#task-host-services), [wallet](../TODO.md#task-wallet),
[history](../TODO.md#task-financial-history),
[operating recovery](../TODO.md#task-keeper-recovery),
[metadata](../TODO.md#task-metadata-ops).

## 4. Rehearse operations and qualify the frozen release

Use three layers: meaningful local checks, actual Robinhood mainnet fork, then
Robinhood Testnet wallet/keeper/deployment rehearsal with explicit supported chain
bindings. A mainnet-pinned admission cannot be qualified by relabelling mocks.
Measure maximum-state/two-leg harvest/entry/close/holder batches and constructor
arguments, inclusion/reset/jitter, outages, Unix storage/watchdog, backups and
same-key receipt recovery. Virtual time and two local wallets are not a live load
or uptime result. The broader capacity campaign remains deferred, not passed. Measure the fresh
1,000,000-gas optional royalty-sync ceiling under cold/faulted actual currencies;
the ceiling is not a fixed charge or proof that every32-entry claim fits.
Reconcile all allocated raw units after final claims, with temporary opening,
prefund, zero-cohort and unsupported balances classified separately.

Review manipulation and residual inventory economics.60/40 is an approved
placement tradeoff, not an optimum; unused or unsafe execution remains blocked.
Independent audit/remediation, exact accepted risks and named release sign-off
complete the [approval record](RELEASE_CHECKLIST.md). Terminal holder return is
irreversible; pre-exit same-chain replacement and post-halt recovery are distinct.

Owning work: [fork](../TODO.md#task-mainnet-fork),
[testnet rehearsal](../TODO.md#task-testnet-rehearsal),
[keeper safeguards](../TODO.md#task-keeper-guardrails),
[independent approval](../TODO.md#task-audit-release).
