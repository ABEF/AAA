# Work handoff

Reviewed 2026-10-26. Read [instructions](../AGENTS.md), [current context](../PROJECT_CONTEXT.md),
[README](../README.md), [Todo](../TODO.md) and the owning runbook before continuing.

## Latest functional state

[Market/input review](../reports/market-adversarial-20261026/REVIEW.md) and
[verification](../reports/market-adversarial-20261026/VERIFICATION.md) record exact
slot0 consistency/fee checks across unsigned reviews/routes/observed and manual
release inventory. Valid stored downward-boundary ticks remain unchanged.
223affected Python methods pass, zero skips/failures/errors/source drift;15actual-v4
composed methods pass after explicitly configuring the test fixed-ZZZ identity.
Both out-of-range directions preserve contributions/shares/claims and subsequent
rebalancing; actual pool donations are excluded from newcomer past income.
Original first fixture failures remain preserved. Production Solidity/ABI/economics
and existing services/Anvil/NFTs/LP/balances/journals/website/monitor are untouched.

Implementation [60bfb96](https://github.com/ABEF/AAA/commit/60bfb96a1cde47b84af926dc62d9ca9b692925ac) is
pushed on main, with exact local/remote equality verified in the
[publication receipt](../reports/market-adversarial-20261026/PUBLICATION.md). Earlier [resilience](../reports/reward-resilience-20261026/VERIFICATION.md),
[allocation](../reports/reward-allocation-20261026/VERIFICATION.md) and normal size/
static receipts retain their own exact scopes; actual qualification remains open.

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
