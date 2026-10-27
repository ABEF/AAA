# AAA / ZZZ PoPL project instructions

Reviewed 2026-10-28. Read [current context](PROJECT_CONTEXT.md), [README](README.md),
[sole Todo](TODO.md) and the relevant [operator procedure](docs/OPERATOR_MANUAL.md)
before changing behavior. This file contains current instructions, not a timeline.

## Repository and authorization boundaries

- Contract repository: `ABEF/AAA`, this checkout. Website: `ABEF/AAA-website`,
  sibling `aaa-website`. Use **main only**, as explicitly requested by the user.
- Git publication is not deployment. No public contract transaction, deployment,
  sealing, operating-service change or website rollout is authorized by a docs
  or source publication request. Verify exact local/remote heads before saying
  pushed. Current production status is **NOT APPROVED**.
- Preserve existing local Anvil services, port8902, NFTs, LP, balances, transaction
  journals and website dist overlay. Do not reset/relabel old deployments to
  match newer source profiles. Historical codecs and receipt recovery remain.
- Public sites are distinct: `popldemo.0xwave.com` keeps the existing simulation;
  `poplint.0xwave.com` is the separately built current-contract read/unsigned-review
  site. See [environment map](docs/SITE_ENVIRONMENTS.md); never use the demo
  installer/root/dist for poplint. Missing integration configuration is not demo data.
- Browser signing remains **Anvil-only**; public `DEPLOYMENT` remains null.
  The staging heartbeat was paused by the user; do not restart it.
- Never print, log or commit keys, credentialed endpoints, keystores or passwords.
  Preserve unrelated work. Read Git status and the handoff before staging;
  archive original dirty documentation before consolidating it.
- Website product changes normally follow local edit/verification, website
  commit/push, then authorized server deployment. Contract/docs-only changes
  may update website memory; they do not change its source, build or server.

## Current architecture and rules

- Fresh candidate: accounting4, direct governance2, fee intake1, custody3,
  pricing2, routing2, reviewed Entry1 and local canonical V5. See
  [exact profile](docs/POSITION_V4.md) and [inventory](docs/PRODUCTION_PREFLIGHT.md).
  No automatic historical profile/journal migration or dummy module bindings.
- One fixed deployment ZZZ token and native ETH are the only contribution inputs.
  Buyback and collective holder return use that same ZZZ. Token identity is not
  replaceable after seal. Issuer/chain migration has no external custody executor.
  Marketplace royalty currencies and optional conversion routes are separate.
- Activation minimum $100; growth minimum $5, subject to stronger pool minima.
  Two independently reviewed USD sources per priced asset; agreement tolerance
  3%. Actual marginal deployed LP must satisfy captured contribution loss limits
  and a caller maximum. Defaults: contribution2%, conversion1%, maintenance3%;
  each governance ceiling10%, gas separate. Do not confuse source agreement,
  budget retention, idle ceilings or caller minima with each other.
- Fresh Strategy maintenance policy2 uses actual physical tick range exit or deliberate operator range change after the configured hard interval (initial12hours), never the old movement trigger. Matching keeper policy2 adds durable60-600second service jitter/hourly ordinary inside checks; preserve manual widths and fast independent receipt/harvest work. Budget capability3 uses max(lastCompound,lastRebalance) plus its independent per-pool compoundInterval (default3600seconds, governed600seconds-7days), yields to due rebalance and never changes its clock. Fresh API configs declare policy2; explicit historical policy1/helper2 and older readers/journals remain separate. See [current evidence](reports/maintenance-policy-20261027/VERIFICATION.md).
- Fixed LP allocation80/10/5/5: individual shares / equal activated collective /
  compound / ZZZ buyback-burn. Rarity affects only actual received royalties at
  Commun1/Rare2/Legendary3. No Power score or configurable split.
- One contribution pool enabled at a time; historical custody buckets remain
  bounded for movement/history. Many NFTs share a physical LP with independent
  nonredeemable shares. The selected native ETH/ZZZ v4 pool is static/hookless;
  actual dependency/fee/route qualification remains required.
- No creator-payment inboxes, integrated bridges, remote-proof intake or remote
  ownership/reward ledgers in current contracts. Retain compatible same-chain
  handoff before LP exit, same-native-pair pool moves and parking. No external
  principal or royalty custody-address exit remains. All production LP pools are ETH/ZZZ.
- Governance acts directly, without timelock machinery. A paused collective exit
  permanently stops new principal/mint activity, closes all ETH/ZZZ buckets and
  allocates actual principal plus pending compound by NFT shares. Bounded direct
  payouts go only to current owners, with owner fallback for rejecting receivers.
  NFTs retain transfers/future royalties/old reward claims. Buyback and reward
  liabilities stay separate; no external recipient, swap exit or sweep exists.
  Post-exit canonical replacement is blocked; see the holder-exit runbook.
- One human operator (the user) controls governance and operates the services;
  operator and governance are not separate people or approval roles. Keep the
  automated keeper's limited key/capability distinct from governance. No extra
  operator role, mandatory multi-person committee or new wallet is implied.
- Current owner holds unclaimed rights, including prior owners' accruals.
  NFT earnings are individual+collective LP plus royalties, excluding reserves
  and duplicate claims/conversions/imports. Earnings, claimable and claimed differ.
  Missing or inconsistent data must remain unavailable/error, never guessed zero.

- Requested next LP operating policy is recorded in [execution decisions](docs/LP_EXECUTION_POLICY.md): manual +/-25/50% selection, twelve-hour outside-only upkeep with hourly eligible checks and durable 1-10-minute service jitter, best reviewed execution venues independent of the LP target and $1m cumulative contributions per NFT. The approved timing slice is implemented in policy2/Budget3; best-route balancing and new solver remain pending. Twelve hours is a hard initial minimum, explicit range changes may apply inside after cooldown, and compounding has its own interval. Do not silently interpret 1% centring tolerance as the old movement trigger or replace independent pricing with pool spot.

- Direct manual `Vault.rebalance` uses an actual keeper grant (governance alone is not enough), bypasses only service jitter/hourly checking and preserves all on-chain guards. Follow [manual procedure](docs/OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time). Same-service-key signing outside its journal requires reviewed nonce/receipt/spend reconciliation; restart or new LP/timer discovery alone cannot adopt it. No manual transaction/service change is authorized by updating these instructions.

## Verification and documentation workflow

- Maintain one task ledger: `docs/project-todo.json` -> generated `TODO.md`.
  Preserve stable task IDs, clickable source links and Contract / Backend /
  Frontend ordering. Follow [maintenance procedure](docs/TODO_WORKFLOW.md).
- Keep the feature/evidence reference, roadmap, release record, operator guide
  and repository context consistent with actual implementation. Update the
  source-bound callable reference for ABI, behavior, permission/input changes.
- Keep current guides concise. Replace superseded guidance; do not prepend
  another dated checkpoint to every file. Store scoped history in reports/Git,
  linked from the documentation index. Historical reports retain original bytes,
  source identities, failures, skips and limitations; never relabel them current.
- Run useful affected checks; reuse unchanged Solidity/dependency/build evidence
  only with exact source pins. Do not inflate counts by adding overlapping runs.
  No gate relaxation, invented provider qualification or global audit guarantee.
- Reconcile current Todo acceptance text as well as its summary: old inputs, loss
  policies, governance and codecs belong to explicitly historical evidence. Do not
  turn deferred work or deliberately disabled public signing into an approval.
  Documentation-only synchronization does not close implementation/release tasks.
- Current integration/source operations are documented in [site boundaries](docs/SITE_ENVIRONMENTS.md)
  and [serving evidence](reports/current3-website-20261026/DEPLOYMENT.md). Current
  contract work targets poplint; leave the existing popldemo release untouched.
  Poplint remains unconfigured/read-unsigned, never an Anvil/public-signing bridge.
- [Current fork verification](reports/current-pool-fork-20261026/VERIFICATION.md)
  records11distinct successful methods across scoped runs, not a fresh whole
  suite; retain mock-price/VRF/authority and real swap-floor limitations. New
  runner is read-only and independent of the preserved old dirty runner/tests.
- [Documentation cleanup/publication](reports/documentation-cleanup-20261026/PUBLICATION.md)
  records the consolidated current guides and original-draft preservation.
- Current manipulation-related hardening: [review](reports/manipulation-hardening-20261027/REVIEW.md) and [verification](reports/manipulation-hardening-20261027/VERIFICATION.md). Paid-revert health markers require matching writer/checker rollout; do not alter journals to pass. Rebalance/compound/buyback recheck keeper/pause at completion. Economic profitability/ordering work remains open; no new24-hour or cumulative limit.
- Earlier keeper/LP source-scoped review: [audit](reports/keeper-lp-audit-20261026/REVIEW.md)
  and [verification](reports/keeper-lp-audit-20261026/VERIFICATION.md). Health binds
  loaded config; deploy checker/writer together, never alter journals to pass.
- [Reward allocation review](reports/reward-allocation-20261026/REVIEW.md) verifies
  claim-order conservation and fixes off-chain buyback scheduling fairness.
  Allocation is at harvest; LP claims never run compound/buyback. Rollout and
  actual schedule/route/burn/gas qualification remain separate; preserve journals.
- [Reward resilience review](reports/reward-resilience-20261026/REVIEW.md) isolates
  maintenance RPC failures from independently guarded due harvests; malformed
  configuration/ABI still fails closed. Pending intents stop all scheduling.
  Current3 unsigned claims reject contradictory inactive rewards; preserve legacy,
  parked/outbound and deferred-currency rights. No installed service was changed.
- [Market/input review](reports/market-adversarial-20261026/REVIEW.md) adds shared
  exact TickMath/slot0 checks to unsigned reviews and observed/manual inventory.
  Preserve real downward-boundary ticks; never repair an inconsistent observation
  by guessing. Actual PoolManager donations are funded fees, unlike raw Vault
  prefunds; neither consistency nor funded earnings proves provider authenticity
  or organic trading volume. Production Solidity/services remain unchanged.
- [Systematic adversarial review](reports/system-adversarial-20261026/REVIEW.md)
  maps608 functions plus31 constructors/13 receivers to multiple static cases; rows
  and1,987 scenario instances are not execution tests. Strict RPC identity/JSON/
  envelope/decoder failure and bounded/sanitized holder CLI inputs and systemd progress watchdog have244affected
  methods:241 passes/3 explicit skips; production Solidity/services remain unchanged. Owner callbacks
  can legitimately change later batch claim amounts; do not add unconditional
  preview equality or skip liabilities to overcome dependency failure.
- Current source/evidence references: [backend fee integrity](reports/backend-remediation-20261026/VERIFICATION.md),
  [full candidate audit](reports/full-audit-20261025/VERIFICATION.md),
  [cleanup compiler comparison](reports/deep-cleanup-20261025/compiler-comparison.md).
  Actual feeds/routes/VRF/authorities/OpenSea, current3 website/services, target
  gas/operations, metadata hosting and independent audit/remediation remain open.

Archived checkpoints and original dirty documentation are preserved outside
the checkout under the documentation-cleanup evidence directory recorded in
[work handoff](docs/WORK_HANDOFF.md). They are historical context, not overrides
of these current instructions. Durable repo context is not global personal memory.
