# Work handoff

Reviewed 2026-10-26. Read [instructions](../AGENTS.md), [current context](../PROJECT_CONTEXT.md),
[README](../README.md), [Todo](../TODO.md) and the owning runbook before continuing.

## Latest functional state

[Reward review](../reports/reward-allocation-20261026/REVIEW.md) and
[verification](../reports/reward-allocation-20261026/VERIFICATION.md) record fixed
allocation timing, two new claim-conservation methods (1,000 fuzz runs), and keeper
buyback priority/currency fairness. Final376 affected Python methods:370 pass / 6skips,
no failures/errors or source drift. Production contracts/economics unchanged;
running services/journals untouched. Implementation [0ee9650](https://github.com/ABEF/AAA/commit/0ee9650904603f27b2f663b45d3f5534bef5ba4f)
is pushed on main, exact remote head verified. See the
[publication receipt](../reports/reward-allocation-20261026/PUBLICATION.md).

[Keeper/LP audit](../reports/keeper-lp-audit-20261026/REVIEW.md) and
[verification](../reports/keeper-lp-audit-20261026/VERIFICATION.md) record config-bound
health, strict conversion flags, current3native rehearsal source and range enum
test repair.354affected Python passes/5Unix skips;9range passes incl1000fuzz.
Production Solidity/ABI/economics unchanged. Implementation885af8e and website
memoryfd8c3e8 are pushed on main; exact remote heads verified in
[receipt](../reports/keeper-lp-audit-20261026/PUBLICATION.md). Old journals and
installed services are not upgraded. Fresh Linux/actual-provider qualification
remains open; use Git for the later docs-only receipt checkpoint.

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
