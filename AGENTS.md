# AAA / ZZZ PoPL project instructions

Reviewed 2026-10-26. Read [current context](PROJECT_CONTEXT.md), [README](README.md),
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
- Browser signing remains **Anvil-only**; public `DEPLOYMENT` remains null.
  The staging heartbeat was paused by the user; do not restart it.
- Never print, log or commit keys, credentialed endpoints, keystores or passwords.
  Preserve unrelated work. Read Git status and the handoff before staging;
  archive original dirty documentation before consolidating it.
- Website product changes normally follow local edit/verification, website
  commit/push, then authorized server deployment. Contract/docs-only changes
  may update website memory; they do not change its source, build or server.

## Current architecture and rules

- Fresh candidate: accounting3, direct governance2, fee intake1, custody2,
  pricing2, routing2, reviewed Entry1 and local canonical V4. See
  [exact profile](docs/POSITION_V3.md) and [inventory](docs/PRODUCTION_PREFLIGHT.md).
  No automatic historical profile/journal migration or dummy module bindings.
- One fixed deployment ZZZ token and native ETH are the only contribution inputs.
  Buyback and normal exit use that same ZZZ. Token identity is not replaceable
  after seal; issuer migration uses custody exit and a fresh reviewed deployment.
  Marketplace royalty currencies and optional conversion routes are separate.
- Activation minimum $100; growth minimum $5, subject to stronger pool minima.
  Two independently reviewed USD sources per priced asset; agreement tolerance
  3%. Actual marginal deployed LP must satisfy captured contribution loss limits
  and a caller maximum. Defaults: contribution2%, conversion1%, maintenance3%;
  each governance ceiling10%, gas separate. Do not confuse source agreement,
  budget retention, idle ceilings or caller minima with each other.
- Fixed LP allocation80/10/5/5: individual shares / equal activated collective /
  compound / ZZZ buyback-burn. Rarity affects only actual received royalties at
  Commun1/Rare2/Legendary3. No Power score or configurable split.
- One contribution pool enabled at a time; historical custody buckets remain
  bounded for movement/history. Many NFTs share a physical LP with independent
  nonredeemable shares. The selected native ETH/ZZZ v4 pool is static/hookless;
  actual dependency/fee/route qualification remains required.
- No creator-payment inboxes, integrated bridges, remote-proof intake or remote
  ownership/reward ledgers in current contracts. Retain compatible same-chain
  handoff, same-pair pool moves, parking and governed external custody.
- Governance acts directly, with no timelock scheduler/executor. Normal custody
  exit converts to fixed ZZZ under approved limits; explicit raw exit sends actual
  ETH/ZZZ without swaps or an aggregate loss promise. External custody is trusted;
  the source cannot force return. Exit does not migrate canonical NFT/reward rights.
- Current owner holds unclaimed rights, including prior owners' accruals.
  NFT earnings are individual+collective LP plus royalties, excluding reserves
  and duplicate claims/conversions/imports. Earnings, claimable and claimed differ.
  Missing or inconsistent data must remain unavailable/error, never guessed zero.

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
- Current source/evidence references: [backend fee integrity](reports/backend-remediation-20261026/VERIFICATION.md),
  [full candidate audit](reports/full-audit-20261025/VERIFICATION.md),
  [cleanup compiler comparison](reports/deep-cleanup-20261025/compiler-comparison.md).
  Actual feeds/routes/VRF/authorities/OpenSea, current3 website/services, target
  gas/operations, metadata hosting and independent audit/remediation remain open.

Archived checkpoints and original dirty documentation are preserved outside
the checkout under the documentation-cleanup evidence directory recorded in
[work handoff](docs/WORK_HANDOFF.md). They are historical context, not overrides
of these current instructions. Durable repo context is not global personal memory.
