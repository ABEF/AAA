# AAA / ZZZ PoPL project instructions

Reviewed2026-10-31. Read [context](PROJECT_CONTEXT.md), [README](README.md),
[sole Todo](TODO.md), [handoff](docs/WORK_HANDOFF.md) and the relevant
[operator procedure](docs/OPERATOR_MANUAL.md) before changing behavior.
This file is current instructions, not a report timeline.

## Authorization and preservation

- Contract repository ABEF/AAA is this checkout; website ABEF/AAA-website is sibling
  aaa-website. **Main only**, as requested. Read Git status before edits/staging;
  verify exact local/remote heads before claiming pushed. Production NOT APPROVED.
- Source/docs publication is not deployment. It authorizes no public transaction,
  sealing, operating-service change, website rollout or local-chain reset.
- Preserve existing Anvil8902, NFTs/LP/balances, journals and dist overlay. Never
  relabel old runtimes, codecs or pending records as a newer profile.
- Popldemo is the existing simulation; poplint is separately built read/unsigned
  integration. Follow [environment map](docs/SITE_ENVIRONMENTS.md). Missing actual
  integration config is unavailable data, not demo data. Do not use demo roots,
  installers or dist for poplint. Current source6 is not the served current3 site.
- Browser signing remains **Anvil-only**, public DEPLOYMENT null. Staging heartbeat
  was paused by the user; never restart it without explicit authorization.
- Never print/log/commit keys, passwords, credentialed RPC endpoints or keystores.
  Preserve unrelated work and archive original dirty docs before consolidation.
- Preserve four unrelated tracked dirty files byte-identically: reports/source-checks.json,
  scripts/run-fork-checks.py, tests_python/test_fork_runner.py and
  tests_python/test_frontend_history.py. Original hashes/evidence locations are in
  the [handoff](docs/WORK_HANDOFF.md). Do not stage unrelated untracked drafts.

## Fresh architecture and rules

- Fresh [profile6](docs/POSITION_V6.md): accounting6/portfolio2/maintenance3/
  confirmation3/compound4/custody4/emergency2/LP-routing2, pricing2/Entry-routing2/
  reviewedEntry2/directgovernance2/fee-intake1. Position remains eight words;
  compatible parked same-chain canonical V6 wire does not imply runtime compatibility.
  Schema8 inventory has21helpers. Historical schema6 is inspection-only; historical
  codecs/readers/receipts/journals remain separate and explicit.
- Only native ETH and one fixed deployment ZZZ are contribution/LP assets.
  Buyback/holder return use that same ZZZ. Token identity cannot change after
  seal; issuer/chain migration uses terminal holder exit and redeployment, with
  no external principal/royalty custody address or integrated bridge.
- Activation/growth minima default$100/$5; ProtocolPolicy governs future minima
  >=1USD, growth<=activation, subject to stronger admitted minima. Use two
  independently reviewed USD sources per priced asset, agreement tolerance3%.
  Prove actual marginal deployed LP and captured caller/operation floors. Default
  contribution2%, conversion1%, maintenance3%; governance ceilings10%, gas separate.
  Additional execution-loss default1% after actual directional core fees is distinct
  from gross budgets, oracle agreement, governed idle ceilings(default5%) and caller minimums.
- Fixed80/10/5/5 actual LP revenue allocation: individual / equal activated
  collective / compound / ZZZ buyback-burn. Rarity affects only actual received
  royalties at Commun1/Rare2/Legendary3. No configurable split or Power score.
- One contribution pool at a time. At most four admitted/historical custody
  buckets; each is one logical share account, with default one main physical LP
  or optional main plus ONE residual in that same native ETH/fixed-ZZZ pool.
  Both NFTs stay Vault-owned. Never add raw L across different ranges for value.
- User approved optional hybrid main>=60%/residual<=40% of post-cost attributed
  principal AT replacement; it is not a continuously maintained target. Initial
  residual width is HALF corresponding main side, default5000bps, governed1–10000.
  Use the configured positive full tick-spacing gap beyond spot(default1); default50–150 main yields
  approximately75–100 or100–125 residual before gap/rounding. Mode defaultsOFF.
  Filled/mixed/outside residuals remain valued/harvested. Disabling desired mode
  records a pending guarded whole merge, never drops backing or creates a third leg.
- Ordinary fresh threshold85%actual centre-to-boundary ZZZ-in-ETH price distance;
  both physical price and independent reference must corroborate the same side.
 600-second sampled window/strict maximum gap300; source checks240seconds;
  then durable freshly drawn60–300-second jitter. Initial hard12hours remains.
  Returning inside/fault/identity/control changes reset sampled evidence/jitter.
  Manual geometry changes apply after cooldown as an explicit exception.
  This is sampled evidence, not uninterrupted history or MEV immunity.
- Raw checks can occur during cooldown. Paid enrollment starts near eligibility
  (earliest-duration-maxgap), avoiding many redundant nonce/gas writes. Preserve
  pending-first recovery, reset acknowledgements and receipt provenance. Main
  contributions do not invalidate stable geometry identity or reset clocks.
- Manager's typed LP child has fixed parent/core/periphery and Vault recipients;
  no delegatecall/generic executor/sweep. Vault approves individual LP IDs, not
  collection-wide approval. Math child is read-only. Constructors now deploy
  standalone Budget/Policy/Confirmation/Balancer in reviewed order with frozen
  Access module parents; no dummy bindings or manual journal migration.
- Balancing uses a bounded list of reviewed venues independent of LP destination,
  actual-core quotes and captured valuation. Empty list disables swaps with no
  fallback. Hybrid natural>=configured main floor(default60%) needs no trade; otherwise bounded partial sizing
  targets rounding headroom. Every ordinary new main, single or hybrid, must be
  physically active before/after mint/refund callbacks; hybrid also proves its
  main-floor allocation. Initial/growth and explicit emergency remain separate. At most one balancing swap;
  no automatic unsafe fallback if liquidity/fees make placement impossible.
- Contributions checkpoint incumbents, swap/deploy entrant funds only, increase
  MAIN only, verify marginal deployed LP and issue shares from aggregate NAV.
  Existing idle/compound/residual cannot fund entrant execution floors. Never
  recenter, reset rebalance clocks or modify residual L during activation/growth.
- Hourly harvest collects both legs and applies80/10/5/5 once per actual asset
  receipt. Claims, conversions, compound and burn are separate. Compound uses
  independent governed interval after max(lastCompound,lastRebalance); service
  waits for in-range main below the adjustment threshold/no pending geometry. Preserve authenticated internal-
  harvest coalescing and raw need vs sampled readiness vs timing diagnostics.
- Both legs close for same-pair movement, parking and terminal holder return.
  Source controls compare captured sourcePool during movement. Stable geometry
  fingerprint excludes L; parking/emergency fingerprint includes both IDs/ticks/L.
  Canonical V6 capture/import/activation requires zero registered live residuals.
- Collective exit is paused-governance-triggered, terminal, no swaps required.
  Close actual ETH/ZZZ and designated compound; allocate by NFT shares, pay current
  owners through bounded isolated direct batches. Rewards/buyback backing stay
  separate; NFTs keep transfers/future royalties/old claims. No custody recipient,
  reopening or post-exit canonical replacement. Post-exit venue admission is
  reserve-only after Ready with deposits disabled; cannot reopen principal.
- One human operator/governance (the user), not two people or a committee.
  Automated keeper's limited key/capability remains distinct. Governance direct,
  no timelock. Sealing fixes implementation/module/venue parent/token identities;
  many reviewed policies/routes remain configurable within explicit bounds.
- Manual Vault.rebalance requires actual keeper permission and preserves on-chain
  guards; it bypasses only service scheduling. Paused governance-only emergency2
  uses a separate exact manifest with optional financial guards and can lose nearly
  all principal. It is never automated day-to-day fallback. Same-key out-of-band
  signing requires nonce/receipt/spend journal reconciliation, never guessed adoption.
- Current owner owns prior unclaimed rights. Earned/claimable/claimed differ;
  conversion/claim/import is not new income. Missing/inconsistent data remains
  unavailable/error, never guessed zero. Royalty currencies are separate from
  permitted contribution inputs and preserve outage/deferred-entry entitlements.

## Adaptable policy source boundary

ProtocolPolicy1 is separately predeployed and Access-bound once before consumers.
Current defaults remain100USD activation/5USD growth/0.05ETH direct mint,500bps
entry and maintenance idle,180k payout/500k source/250k optional royalty sync gas,
1000/10000USD cosmetic thresholds. Governed bounds and exact procedures are in
[policy](docs/ADAPTABLE_POLICY.md) and [operator](docs/OPERATOR_MANUAL.md#future-operating-settings).
Future minima>=1USD; lowering changes future participant economics. Mint payee
propose/accept changes future payments only. New mint binds sale+VRF fingerprint;
Entry2 binds exact entry fingerprint before callbacks. Scoped revisions prevent
restore-to-revive reviews and avoid cosmetic/gas/mint changes resetting LP samples.
Portfolio2 main floor6000–9999bps; hard6000 stays because lowering was not approved.
Gas bounds100k–1m are engineering limits, not provider/chain qualification.
Provider rotation requires all draws finalized, no pending reroll/retargeting.
Coordinator runtime is pinned for new requests; original-address callbacks may
drain before planned rotation. Codehash does not freeze proxy implementations.
Canonical V6 rejects old schemas early and binds helper/runtime/config commitment;
threshold VALUES must match during source/import lifecycle, not local revisions.
Current owner/rewards/quotas/ETH-ZZZ/fixed splits and terminal custody guarantees
are unchanged. No deployment/service/site/Anvil/journal/signing change authorized.

## Verification and records

- [Current change audit](reports/today-audit-20261031/REVIEW.md) repairs published
  portfolio-reader omissions and same-chain lineage admission of matching external
  dependencies, corrects recovery labels and restores current accounting fixtures.
  Before Python publication check exact staged Git blobs with
  `python scripts/check-python-publication.py --index`, then the committed revision.
  Local imports are insufficient. Keep protocol identities distinct, exact runtime
  pins/history proof and old deployment/journal profiles. No production Solidity
  or economic policy changed; use the audit's fresh/reused evidence boundaries.

- Current source-scoped [adaptable-policy evidence](reports/adaptable-policy-20261031/VERIFICATION.md)
  binds52 production sources/31 dependencies and43 normal gates at final0a.
  Vault635/Budget237/Migration20 runtime headroom is exact-source evidence, not
  future edit capacity or target-chain gas qualification. Current callable
  reference is37contracts/826functions/37constructors/14receivers, zero gaps.
- Scoped EVM/backend campaigns retain original failures, empty attempts, corrected
  retries and body-based reuse. They are not a current full suite, published CI,
  provider/operating acceptance or independent audit. Older42-gate/778-callable/
  463-static reports are historical; refresh analysis before release approval.
- Offline operator-review tooling only hashes a strict source-bound manifest and
  orders explorer inputs. No live authority/snapshot/simulation/signing is implied.
  Preserve false readiness flags, exact integer/hash inputs and saved journals.
- Matching source6 APIs authenticate both LP legs while retaining price-outage
  ownership/raw-claim availability. USD/NAV can remain unavailable. Never infer
  keeper readiness from physical-only data or relabel old services/journals.
- Actual dual feeds/routes/VRF/authorities/OpenSea, source6 site/services, target
  gas/economics, storage/recovery and independent audit/remediation remain open.
- Management has one maintained Operator manual; PORTFOLIO_OPERATIONS is only
  a compatibility pointer. Update exact procedure/input/permission/rollback and
  callable notes with behavior changes; no background synchronization is implied.
- One ledger docs/project-todo.json generates TODO.md. Preserve stable IDs/status
  evidence and Contract/Backend/Frontend ordering; follow docs/TODO_WORKFLOW.md.
  Check feature/evidence, roadmap, release, current context and operator guidance.
- Preserve historical report bytes/source scopes, unrelated dirty files and all
  services/sites/Anvil/journals/signing. Use exclusive evidence paths and exact
  source pins; do not rerun unchanged contract suites for documentation sync.
- Main only. Verify exact local/remote heads before reporting publication. Git
  publication is separate from deployment; source6 code does not update old sites.
- Current guides replace stale prose. Scoped history belongs in reports/Git;
  archive original dirty docs first. Repo memory is not global personal memory.

## Manual portfolio management follow-up

Additional RESIDUAL_EXIT_VERSION1 on Migration/Vault/Manager/position child,
same accounting6/custody4 wire and no new modules. Paused governance can call
Migration.closeResidual(ParkingRequest): harvest both, close only associated
residual into attributed Vault idle, preserve main/shares/clock/configuration.
Raw minima, physical/control fingerprint, current governance/pause and shared
parking nonce/custody epoch are enforced. No implicit setMode/recordApplied,
swap, external recipient, holder payout or compound release. To stay single,
setMode(false) first. Mode(true) enables future guarded adjustment; an alreadyON
geometry can be re-reviewed with same-value configureResidualSide after cooldown.
EmergencyRebalance already forces one main at its actual required token ratio,
not necessarily50/50USD. [Complete controls](docs/OPERATOR_MANUAL.md#portfolio-management-controls).
Large idle is intentional recovery state; do not bypass later entrant/deployment
guards. Existing both-leg park/holder-return remain fallbacks.
Behavior-preserving private terminal-check dedup and read-only holder-exit
validation extraction preserve normal limits. Current source6 gates are
43 at exact final0a pins, with Vault635/Budget237runtime margins; old905/286
margins remain historical.
Preserve exact pre/post checks and caller/error semantics. No existing deployment,
service/site/Anvil/journal/signer/heartbeat was changed; work remains local.
