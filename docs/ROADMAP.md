# Engineering roadmap

Reviewed5November2026. [The sole Todo](../TODO.md) owns statuses; this page orders
work and dependencies. [Findings](AUDIT_FINDINGS.md) explain current mechanisms
and unresolved risks. Production **NOT APPROVED**. Source publication is separate
from deployment, services, websites and public transactions.

## 1. Freeze the correct source and integration boundary

Use [accounting6/Entry3/schema13](POSITION_V6.md) and exact runtime/helper/dependency
pins. Direct Entry removal, residual management, active-main candidate filtering,
cooldown observation and authenticated harvest coalescing are implemented; do not
reopen them as proposals or revive retired bridges/creator inboxes/third inputs.
The [current 24-hour audit](../reports/last24h-audit-20261105/REVIEW.md) and
[source-scoped manual review](../reports/manual-safeguard-audit-20261104/VERIFICATION.md) have exact
source scope, retained failed attempts and explicit reuse. Normal Migration has
39bytes runtime headroom; further code changes need new exact-source gates.

Owning work: [release freeze/audit](../TODO.md#task-audit-release),
[deployment size/gas](../TODO.md#task-deployment-initcode),
[reviewed contributions](../TODO.md#task-reviewed-contribution-policy).

## 2. Qualify real dependencies and market execution

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

Build reviewed schema13/source8 configs for API/indexer/keeper/health writer-checker
and a matching accounting6/direct Entry3 website consumer on poplint. Popldemo
remains simulation; served current3 and historical Anvil/journals remain their
original profiles. Public DEPLOYMENT stays null and signing Anvil-only.

Qualify actual preparation/trace/approval/claims and truthful complete holdings/
history, unavailable states, account changes and pending recovery. Qualify the opt-in
checkpoint1 implementation, then extend lineage/other full-history consumers and
review long-lived archival/rotation/source-codec evolution.
Fresh royalty4/reporting5/canonicalV8 needs exact-unit cursor/cohort history and
+reviewed checkpoint rebuilds. No converter or new deployed allocator is added.
+A new service/config rollout needs stop/reconcile/dry-run/restart, not a version edit.

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
+1,000,000-gas optional royalty-sync ceiling under cold/faulted actual currencies;
+the ceiling is not a fixed charge or proof that every32-entry claim fits.
+Reconcile all allocated raw units after final claims, with temporary opening,
+prefund, zero-cohort and unsupported balances classified separately.

Review manipulation and residual inventory economics.60/40 is an approved
placement tradeoff, not an optimum; unused or unsafe execution remains blocked.
Independent audit/remediation, exact accepted risks and named release sign-off
complete the [approval record](RELEASE_CHECKLIST.md). Terminal holder return is
irreversible; pre-exit same-chain replacement and post-halt recovery are distinct.

Owning work: [fork](../TODO.md#task-mainnet-fork),
[testnet rehearsal](../TODO.md#task-testnet-rehearsal),
[keeper safeguards](../TODO.md#task-keeper-guardrails),
[independent approval](../TODO.md#task-audit-release).
