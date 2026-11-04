# AAA / ZZZ PoPL project instructions

Reviewed2026-11-04. Read [context](PROJECT_CONTEXT.md), [README](README.md),
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
  installers or dist for poplint. Fresh source8/direct Entry3 is not the served current3 site.
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
  confirmation3/compound4/custody5/emergency2/LP-routing2, pricing2/Entry-routing3/
  reviewedEntry2/directgovernance2/fee-intake1. Position remains eight words;
  compatible parked same-chain canonical V6 wire does not imply runtime compatibility.
  Schema10 inventory has20helpers. Historical schema9/custody4/direct Entry3, schema8/routed Entry2 and older inventories are inspection-only; historical
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
Direct Entry3/review-policy2 binds exact entry fingerprint before callbacks. Scoped revisions prevent
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

[Whole-project supplement](reports/comprehensive-audit-20261104/REVIEW.md) fixes indexer anchor snapshot/early
validation and streaming ownership replay;33affected Python methods pass.
Production Solidity/dependencies/build settings stay exact; normal/static/EVM
evidence is reused, not rerun. Current website documents are aligned without
source/build/service/journal/signing changes. Lifetime storage/provider/operating
and independent-audit gates stay open.


- [Market/lifecycle evidence](reports/market-lifecycle-20261104/REVIEW.md) adds7new actual-v4 journeys plus one
  affected six-day control and7new API/worker methods. Receipt-derived owner
  and collective fractions remain separate; sum principal tokens before USD
  rounding. Initial model/transcript failures are retained. Production sources,
  settings, services and sites are unchanged; this is not market qualification.
- Current source/evidence: [profile identities](docs/POSITION_V6.md),
  [features](docs/IMPLEMENTATION_STATUS.md), [consolidated findings](docs/AUDIT_FINDINGS.md),
  [report map](reports/README.md) and [release approval](docs/RELEASE_CHECKLIST.md).
  Historical report bytes/source scopes remain immutable; do not sum overlapping
  tests or describe old analysis as current. The consolidation is not a new audit pass.
- [Current authority evidence](reports/authority-audit-20261103/VERIFICATION.md)
  binds52production/31dependencies and43normal gates.471static records:19current
  contexts reviewed/452exact unchanged reuse.14distinct selected EVM successes
  span explicit corrected stages;25corrected Python methods pass. No full suite,
  public CI, actual gas/uptime or independent approval. Reference37/818/37/13 has
  zero gaps; runtime headroom Vault635/Budget237/Migration39/Balancer360.
- Custody5 makes terminal allocatePrincipal/distributePrincipal governance-only
  with pre/post authority checks. Owner LP/royalty/fallback claims remain. Fresh
  API/keeper configs explicitly select custody_version5; omission retains old4
  and rejects actual5. Each fresh lineage peer states its own version. Schema10
  observer/validator8 preserves old schema9/custody4 behind historical inspection.
  Disable keeper principal_distribution on5; never put governance key on its host.
  No deployment/journal/service is upgraded by publication. Current wire remains
  accounting6/custody4-format/canonicalV6; see [permissions](docs/ACCESS_PERMISSIONS.md).
- [Exit assurance supplement](reports/holder-exit-assurance-20261103/REVIEW.md)
  changes tests/guidance only; production pins remain e26fc74.10distinct selected
  successes across explicit stages include1000fuzz inputs,1000distinct holders,
  37mixed wallets, actual NFT tiers/rarities/claims/transfers and local real-v4
  both-leg closure. Retain missing-Manager model failures; guard was not relaxed.
  No target gas/actual-wallet/independent approval or runtime/site/journal rollout.
- Before Python publication run `python scripts/check-python-publication.py --index`
  against exact staged blobs, then the committed revision. Local untracked imports
  never establish published closure. Main only; verify exact local/remote heads.
- Offline operator-review tooling only hashes a strict source-bound manifest and
  orders explorer inputs. No live authority/snapshot/simulation/signing is implied.
  Preserve false readiness flags, exact integers/hashes and saved journals.
- Matching current APIs authenticate both LP legs while preserving ownership/raw
  funded claims through price outages. USD/NAV can remain unavailable. Never infer
  keeper readiness from physical-only data or relabel an old service/journal.
- Actual dual feeds/routes/VRF/authorities/OpenSea, matching source8 services/site,
  target gas/economics, storage/recovery, long-lived history and independent
  audit/remediation remain open. Source publication is not operating acceptance.
- One maintained [Operator manual](docs/OPERATOR_MANUAL.md); PORTFOLIO_OPERATIONS
  is only a compatibility pointer. Update procedure/input/permission/reverse steps,
  restart/irreversible boundaries and callable notes with behavior changes.
- One ledger docs/project-todo.json generates TODO.md. Preserve stable IDs/statuses,
  evidence and Contract/Backend/Frontend order; follow docs/TODO_WORKFLOW.md. Review
  feature/evidence, roadmap, release, context and operator guidance together.
- Archive original dirty documentation before consolidation. Replace stale current
  prose rather than append another timeline. History belongs in reports/Git;
  repository memory is not global personal memory or a background sync service.
- Use exclusive evidence paths; retain failures/skips/empty attempts. Do not rerun
  unchanged contract suites for a documentation change. Preserve unrelated dirty
  files and every existing service/site/Anvil/journal/signer/heartbeat boundary.

<a id="manual-portfolio-management-follow-up"></a>

## Manual portfolio control invariants

RESIDUAL_EXIT_VERSION1 on Migration/Vault/Manager/position child retains
accounting6 and the unchanged custody4-format wire under custody5. Paused governance `Migration.closeResidual(ParkingRequest)`
harvests both then closes only the registered residual into attributed Vault idle;
main/shares/clock/configuration remain. Raw minima, physical/control fingerprint,
current governance/pause and shared parking nonce/custody epoch remain enforced.
No implicit mode change, swap, payout, external recipient or compound release.
Set modefalse first to remain single; modetrue permits the next guarded adjustment.
Already-ON geometry can be re-reviewed with same-value configureResidualSide after
cooldown. Emergency consolidation creates one main at its required ratio, not
necessarily50/50USD. Large idle can be intentional recovery state; never bypass
later entrant/deployment floors. Both-leg park/holder return remain fallbacks.
Preserve exact pre/post checks and caller/error semantics. See the [complete
controls](docs/OPERATOR_MANUAL.md#portfolio-management-controls).
