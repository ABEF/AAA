# Work handoff

Reviewed4November2026. Current contract-source base is main
`0b14acaf5df696c7a32243b8ea7c315a8cd191ab`; publication status must be verified
against actual local/remote Git heads. Read [instructions](../AGENTS.md),
[context](../PROJECT_CONTEXT.md), [README](../README.md), [sole Todo](../TODO.md),
[findings](AUDIT_FINDINGS.md) and the relevant [operator procedure](OPERATOR_MANUAL.md).

The [November4 audit supplement](../reports/comprehensive-audit-20261104/REVIEW.md) fixes indexer anchor
isolation and streams ownership replay;33affected Python methods pass with
negative controls retained. Production Solidity/dependencies/build profiles
remain unchanged; old EVM/static/size evidence is explicitly reused. Website
documentation alignment is source/docs-only, with no runtime/site/journal rollout.

The [market/lifecycle campaign](../reports/market-lifecycle-20261104/REVIEW.md) adds7new actual-core journeys plus
one affected six-day control and7new current-profile API/keeper methods.
Separate receipt-derived reward fractions, fair shares, both-leg NAV, mode
transitions, outages, transfers and terminal royalties/payouts are reconciled.
Failed test-model/RPC-fixture attempts remain recorded; production code and
operating settings are unchanged. No profit, uptime or release approval.

The [confirmation audit](../reports/confirmation-audit-20261104/REVIEW.md) fixes daemon sleep ignoring saved maturity/
jitter deadlines and queued incident clears depending on unrelated router
metadata.100focused Python methods pass, including14new regressions; causal
negative failures are retained. Contracts/settings/journals are unchanged.
A reviewed matching keeper source rollout remains required; no service was
changed.600/240/300 and the hard12hours remain, with sampled/live limits.

The [manual safeguard audit](../reports/manual-safeguard-audit-20261104/REVIEW.md) changes ONLY the Confirmation view
and read-only custody validator: emergency bit16 no longer implicitly retains
hard-cooldown bit1; paused parking/residual close can explicitly use both raw
floors0. Positive floors, exact ownership/receipt/share/reserve/callback/lifecycle
guards remain. Ordinary readiness and emergency authority are unchanged. Normal
compiler/reference/static and focused regression evidence belongs to that report;
old e26fc74 authority evidence is historical for these two changed contexts.
No ABI/storage layout or advertised capability version changed; exact current
runtime pins are required. Installed services/sites/Anvil/journals remain untouched.

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

## Earlier authority evidence to reuse, with limits

Use [authority verification](../reports/authority-audit-20261103/VERIFICATION.md):
52production/31dependencies,43normal EIP170/EIP3860 gates at that historical revision,0.8.26/Cancun/viaIR/
optimizer1/Yulfalse.471static records:19current contexts and452exact unchanged
reuse;37contracts/818functions/37constructors/13receivers without gaps.
14distinct selected EVM successes span two recorded stages;25corrected Python
methods pass. Initial size/test/observer/reference failures remain preserved.
No full suite, published CI, target gas/uptime or independent approval is implied.

That authority revision: Migration24537(39margin), Vault23941(635), Budget24339(237),
Balancer24216(360); Entry9863. Only production Migration changed: custody5 plus
governance-only allocation/distribution and authenticated owner-read reuse.
Holder LP/royalty/fallback claims remain. Fresh schema10/read/keeper versions
are explicit; disable keeper principal_distribution on5. Old custody4/schema9
and pending records retain their original behavior. See [permissions](ACCESS_PERMISSIONS.md).
Earlier Entry3/consolidation evidence retains its source scope.

## Collective exit assurance supplement

[Exit assurance](../reports/holder-exit-assurance-20261103/REVIEW.md) changes tests
and guidance only at historical e26fc74.10distinct selected EVM
behaviors across explicit scopes, including1000fuzz cases, corrected1000-NFT
model,1000distinct owners,37mixed wallets and actual local v4 two-leg closure.
Initial missing-Manager model failures remain recorded; no production guard was
removed. Mixed real NFTs cover dormant/three tiers/three rarities, top-ups,
previous claims and transfer after allocation. Those normal43gate/static471/callable
records retain their historical source scope; no full repeat, live rehearsal or rollout. Existing
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
