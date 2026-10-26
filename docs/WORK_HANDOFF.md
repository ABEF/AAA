# Work handoff

Reviewed 2026-10-26. Read [instructions](../AGENTS.md), [current context](../PROJECT_CONTEXT.md),
[README](../README.md), [Todo](../TODO.md) and the owning runbook before continuing.

## Latest functional state

[Systematic adversarial review](../reports/system-adversarial-20261026/REVIEW.md),
[coverage](../reports/system-adversarial-20261026/COVERAGE.md) and
[verification](../reports/system-adversarial-20261026/VERIFICATION.md) map652 callable
rows (608 functions/31 constructors/13 receivers) and1987static scenario instances.
No new on-chain exploit was confirmed in the inspected partitions. Production
Solidity/ABI/rights remain unchanged. New RPC identity/JSON/envelope/failover and
holder bounded-input/sanitized-argument corrections and watchdog integration have
244 distinct affected methods:241 passes/3 explicit skips,42 new methods included
once and zero failures/errors/source drift. Source-stage failures
and exploratory parser-threshold mistakes are preserved rather than relabeled.
Source-only keeper main-progress watchdog/unit support contains stalled RPC
when the reviewed systemd supervisor is actually enabled; standalone I/O still
has no absolute deadline. Financial/recovery Keeper methods are unchanged.
Actual Linux group cleanup/restart remains open; no installed unit changed.
Owner callbacks can legitimately change later claim payouts; no unconditional
view/simulation equality or skipped-liability workaround was added.

This work follows verified mainc3289a8 and is prepared for scoped main publication.
Verify the final exact local/remote head and campaign receipt before reporting
pushed. Existing services/Anvil/NFTs/LP/balances/journals/website/monitor remain
untouched. Earlier [market](../reports/market-adversarial-20261026/VERIFICATION.md),
[resilience](../reports/reward-resilience-20261026/VERIFICATION.md) and normal
build/static receipts retain scope; actual qualification remains open.

## Continue here

The user is the sole human operator and controls governance. Use that model in
the [operator manual](OPERATOR_MANUAL.md#one-operator-and-governance-wallet);
separate account capabilities do not require extra people or an operator role.
The [harvest schedule procedure](OPERATOR_MANUAL.md#change-the-standalone-harvesting-interval)
explains the four-hour example, exact JSON setting, overrides, receipt-based timer
and controlled restart/health/rollback. It changes no live config or contract;
do not infer that a production harvesting service has been enabled.

1. Use the [single task ledger](../TODO.md): actual feeds/routes/RPC/VRF/authorities,
   OpenSea primary-mint path, current3 website and service acceptance remain open.
2. Keep the current accounting3/governance2/fee1/localV4 profile explicit. Existing
   local deployments retain their own code/profile; never relabel or reset them.
3. Qualify current target-chain depth/gas/strategy economics and Linux operating
   rehearsals, then freeze exact source/configuration for independent review and
   remediation. Production remains NOT APPROVED.

## Preservation and publication

- Main only. No public transactions, deployment/seal, service/monitor restart or
  website source/build/server update is authorized by documentation work.
- Existing8902/Anvil/NFT/LP/balances/journals/dist overlay are unchanged; signing
  Anvil-only, public DEPLOYMENT null, monitoring paused.
- Original14dirty paths and all348tracked Markdown snapshots are backed up at
  `C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/documentation-cleanup-20261026/`.
  `baseline.json` records hashes and initial maina5fad3e. Original dirty docs are
  under `original-drafts/`; old checkpoint files under `baseline/`. Do not publish
  unrelated code drafts just to clean docs. Required historical reports stay
  source-scoped in the repository; Git preserves removed redundant pages.
- Update Todo/features/operator/roadmap/release/context together. Keep current
  guides current rather than adding another dated preamble. Verify remote heads
  and distinguish publication from deployment.
