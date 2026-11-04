# Work handoff

Reviewed4November2026. Current contract-source base is main
`e237aa72ec7fa09382d857ffab1a3fd96b286299`; publication status must be verified
against actual local/remote Git heads. Read [instructions](../AGENTS.md),
[context](../PROJECT_CONTEXT.md), [README](../README.md), [sole Todo](../TODO.md),
[findings](AUDIT_FINDINGS.md) and the relevant [operator procedure](OPERATOR_MANUAL.md).

The [November4 audit supplement](../reports/comprehensive-audit-20261104/REVIEW.md) fixes indexer anchor
isolation and streams ownership replay;33affected Python methods pass with
negative controls retained. Production Solidity/dependencies/build profiles
remain unchanged; old EVM/static/size evidence is explicitly reused. Website
documentation alignment is source/docs-only, with no runtime/site/journal rollout.

## Current source and preserved environments

[Accounting6 profile](POSITION_V6.md), direct Entry3/review-policy2/pricing2,
ProtocolPolicy1/Portfolio2, maintenance3/confirmation3/compound4/custody5/emergency2/
LP-routing2; schema10 inventory17modules/20helpers. Same eight-word Position and
canonical V6 do not identify runtime compatibility. No Entry conversion child,
route catalogue or receiver remains. Separate earned-reward converters stay.

Default single main or optional one residual in the same ETH/fixed-ZZZ pool;
entrant-only main growth and both-leg accounting remain. Normal600/240/300
confirmation,85% threshold, initial12hours and60–300jitter remain. Hourly harvest
is separate from compound/burn/claim. See current context/manual for all defaults
and governed bounds; do not reconstruct settings from old audit prose.

No deployment, sealing, site/service/Anvil/journal/signing/heartbeat change.
Keep Anvil8902 and its NFTs/LP/balances/recovery records. Popldemo remains its
simulation; poplint remains separately served current3/read-and-prepare, not the
fresh source8 consumer. DEPLOYMENT null, browser signer Anvil-only, heartbeat paused.

## Evidence to reuse, with limits

Use [authority verification](../reports/authority-audit-20261103/VERIFICATION.md):
52production/31dependencies,43normal EIP170/EIP3860 gates,0.8.26/Cancun/viaIR/
optimizer1/Yulfalse.471static records:19current contexts and452exact unchanged
reuse;37contracts/818functions/37constructors/13receivers without gaps.
14distinct selected EVM successes span two recorded stages;25corrected Python
methods pass. Initial size/test/observer/reference failures remain preserved.
No full suite, published CI, target gas/uptime or independent approval is implied.

Migration now24537(39margin), unchanged Vault23941(635), Budget24339(237),
Balancer24216(360); Entry9863. Only production Migration changed: custody5 plus
governance-only allocation/distribution and authenticated owner-read reuse.
Holder LP/royalty/fallback claims remain. Fresh schema10/read/keeper versions
are explicit; disable keeper principal_distribution on5. Old custody4/schema9
and pending records retain their original behavior. See [permissions](ACCESS_PERMISSIONS.md).
Earlier Entry3/consolidation evidence retains its source scope.

## Collective exit assurance supplement

[Exit assurance](../reports/holder-exit-assurance-20261103/REVIEW.md) changes tests
and guidance only; production remains exact e26fc74.10distinct selected EVM
behaviors across explicit scopes, including1000fuzz cases, corrected1000-NFT
model,1000distinct owners,37mixed wallets and actual local v4 two-leg closure.
Initial missing-Manager model failures remain recorded; no production guard was
removed. Mixed real NFTs cover dormant/three tiers/three rarities, top-ups,
previous claims and transfer after allocation. Normal43gate/static471/callable
records still match source; no full repeat, live rehearsal or rollout. Existing
receiver/dependency/gas/authority/independent-audit limits remain. Operator guide
now explains grouped per-NFT reconciliation rather than per-wallet entitlement.
External assurance root preserves the original test/docs and all run stages.

## Continue next

Use the [roadmap](ROADMAP.md) and owning Todo tasks. Real feeds/routes/VRF,
authorities, OpenSea, fresh current-profile services/site, economics/target gas,
storage/recovery, long-lived history and independent audit remain open. Prior
recommendations now implemented include cooldown observation, harvest coalescing,
active-main candidate filtering, residual-only close and direct Entry removal.
Do not reopen retired creator/bridge/third-input/external-custody requirements.

Operator changes must update exact procedure, fields, authority, effect,
verification, stop/restart/reverse and irreversible limits in the same change.
Source publication never upgrades running services or reinterprets pending intents.

## Archives and unrelated work

External evidence root:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9`.
Current `authority-audit-20261103` holds111 original current files,
2634 baseline report hashes and485 code/config/test/build pins. Its BASELINE.json
also binds four unrelated dirty files; preserve/exclude them:
reports/source-checks.json, scripts/run-fork-checks.py,
tests_python/test_fork_runner.py, tests_python/test_frontend_history.py.
Do not stage unrelated untracked design/cache/old report drafts.

Prior `direct-entry-v3-20261103` retains585 original files,2678 prior report
hashes and raw compiler/analyzer/EVM/Python stages. Earlier archive roots are
linked from their immutable verification records. They are history, not another
current instruction set. Check exact archived and live hashes before evidence reuse.
