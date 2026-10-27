# Work handoff

Reviewed 2026-10-27. Read [instructions](../AGENTS.md), [current context](../PROJECT_CONTEXT.md),
[README](../README.md), [Todo](../TODO.md) and the owning runbook before continuing.

## Latest functional state

Published contract source/evidence checkpoint:
[8be0f89](https://github.com/ABEF/AAA/commit/8be0f89fd982253ddae7bef2ebfc36b497d836b1).
Website main77501ce and served artifactf23c559 are different identifiers;
the unchanged demo serves9be6d1. Documentation commits after these checkpoints
do not deploy contracts, websites or services.

The separate [poplint current3 integration](../reports/current3-website-20261026/DEPLOYMENT.md)
is served over HTTPS from website sourcef23c559; website main77501ce adds operating
docs and its verified certificate-renewal hook without redeploying the artifact.
The existing demo stays on9be6d1 with unchanged content/configuration/root hashes.
Poplint's deployment/API config is null: no fabricated balances, public signing
or public contract deployment. Its source checks include451JS passes (46new),
seven separate shell/build methods, three browser cases and compiler-bound ABI
checks; these are not a combined full-release count.

[Current-pool fork evidence](../reports/current-pool-fork-20261026/VERIFICATION.md)
has11distinct successful real-venue methods across8+1+1+1scoped runs, not a fresh
whole final suite. Native100 activation/5growth and ZZZ100activation, fee/ownership
backing and expected swap-floor failure/atomic rollback are recorded. Mock
governance/VRF/correlated prices and actual route/provider/keeper/gas limitations
remain explicit. The old four dirty files are preserved; the new runner is
independent. The user declined extra sale-rights UI (Not planned, not implemented).

The previous source-scoped backend/security state remains:

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

Implementation [2a9c65b](https://github.com/ABEF/AAA/commit/2a9c65bf2d4dc27cc4eb16a8ba8b629f07f2f22b) is
pushed on main with exact local/remote equality verified in its
[publication receipt](../reports/system-adversarial-20261026/PUBLICATION.md). That
earlier campaign left services/Anvil/NFTs/LP/balances/journals/website/monitor
untouched; the separately authorized poplint rollout above changes only its
new static hosting/TLS, never the demo or keeper/Anvil/monitor state. Earlier [market](../reports/market-adversarial-20261026/VERIFICATION.md),
[resilience](../reports/reward-resilience-20261026/VERIFICATION.md) and normal
build/static receipts retain scope; actual qualification remains open.

## Continue here

The user replaced external custody exits with irreversible collective return to
NFT holders. Fresh source is accounting4/custody3/canonicalV5. Read
[holder exit](HOLDER_COLLECTIVE_EXIT.md) and [profile](POSITION_V4.md): current
owners receive proportional actual ETH+ZZZ, automatic bounded pushes have owner
fallback, pending compound joins principal, and old rewards/future royalties
remain. LP earnings end at final close. No external principal/royalty recipient,
bridge or recovery-to-pool ingress remains. New LP admission is native ETH/ZZZ
only; old deployment/schema/journal meanings stay intact.

The earlier accounting3 fork and poplint evidence above remains historical to
its exact source. Poplint/demo/services/Anvil are not changed by this source task.
Affected source verification is recorded in [holder-return evidence](../reports/holder-collective-exit-20261027/VERIFICATION.md):133Solidity methods,37normal object gates and scoped backend/keeper checks pass. Complete actual profile4 release inventory/UI/service acceptance before production. Actual feeds/routes/VRF/OpenSea/authorities,
metadata hosting, gas/strategy/operating rehearsals and independent review remain
open. Never infer deployment approval from source/docs or local fixture success.

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
- Current integration workspace/evidence: `C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/poplint-integration-20261026/`.
  It preserves original contract/website docs, source snapshots, serving/desktop
  checks and safe deployment helpers. Fork evidence uses sibling
  `current-pool-fork-20261026/`. Campaign began26; final review is27October.
- A user-authorized deployment key exists outside Git in sibling
  `poplint-ops-credentials/`; user-owned ACL/OpenSSH and existing host pin were
  verified. Reuse that authorized connection for scoped website operations;
  do not probe old chat credentials, print the private key, install another
  privileged key or use the read-only staging monitor key for deployment.
  Key availability does not authorize contract signing or unrelated server changes.
- Four pre-existing drafts remain local and deliberately excluded from these
  publications: reports/source-checks.json, scripts/run-fork-checks.py,
  tests_python/test_fork_runner.py and tests_python/test_frontend_history.py.
  Their original hashes match the saved baseline. The new current fork runner
  is separate; do not reset, overwrite or publish these unrelated drafts blindly.
- Update Todo/features/operator/roadmap/release/context together. Keep current
  guides current rather than adding another dated preamble. Verify remote heads
  and distinguish publication from deployment.
