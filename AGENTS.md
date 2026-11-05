# AAA / ZZZ PoPL project instructions

Reviewed2026-11-05. Read [context](PROJECT_CONTEXT.md), [README](README.md),
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
  fresh canonicalV8 carries sale end/capacity and exact royalty tickets; rejects older peers; tuple shape is not runtime identity.
  Schema13 inventory has18helpers and exact original-currency royalty4 with canonicalV8. Historical schema12 royalty3/canonicalV7; historical schema10 royalty-converting/custody5, schema9/custody4/direct Entry3, schema8/routed Entry2 and older inventories are inspection-only; historical
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
- Confirmation deadline wake-ups use a recent head plus ephemeral monotonic
  elapsed time; never use that estimate as readiness or persist it in journals.
  Keep pending/global-error recovery polling intact. Known clear-only resets
  precede router metadata reads but retain all submission/authority checks.
  [Scoped audit](reports/confirmation-audit-20261104/REVIEW.md):100focused Python passes, no service rollout.
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
  Canonical V8 capture/import/activation requires zero registered live residuals.
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
entry and maintenance idle,180k payout/500k source/1m optional royalty sync gas,
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
Canonical V8 rejects old schemas early and binds helper/runtime/config commitment;
threshold VALUES must match during source/import lifecycle, not local revisions.
Current owner/rewards/quotas/ETH-ZZZ/fixed splits and terminal custody guarantees
are unchanged. No deployment/service/site/Anvil/journal/signing change authorized.

## Manual safeguards: current source follow-up

See [manual safeguard audit](reports/manual-safeguard-audit-20261104/VERIFICATION.md).
Emergency bit16 checks retained live sampled evidence independently of bit1
hard cooldown/raw eligibility. Ordinary ready still retains that clock. Bit4
needs USD data even when bit2 is off. Paused governance park/closeResidual may
explicitly use minimum0=minimum1=0; positive caller floors, current physical
principal proof, custody/receipt/share/reserve/nonce/epoch/lifecycle checks remain.
Raw emergency checks0 works from Active/Parked into the CURRENT pool, not an
unreviewed new destination. Force cannot fix broken tokens/core or reopen terminal
exit. Exact runtime pins changed with unchanged ABI/storage/capability versions;
never apply these semantics to old runtimes or relabel journals. Fresh43normal
gates/current callable/static evidence replaces only its changed source scope;
the November3 authority report below remains historical for those contexts.

## Historical obligation and static-default maintenance

- The [whole-history reconciliation](reports/full-history-reconciliation-20261104/REVIEW.md)
  maps310original finding rows, deleted guides,162ledger versions and398old
  unchecked lines. Use original pointers plus current decisions; never close a
  finding just by age/topic or revive creator/bridge paths from old reports.
- CI/check-slither-review selects the strict current [last24-hour review](reports/last24h-audit-20261105/static-review.json).
  Full detector/source coverage is source-bound; exact context reuse remains
  distinguished from current review. Earlier479/471 records stay historical.
  Update current default/full record together after relevant source changes.
- Checkpoint1 is an implemented first milestone; general lifetime history remains open.
  OpenSea/fresh consumer, providers/authorities/gas/hosting/metadata/recovery and
  independent approval remain open. Source publication changes no environment.

## Earnings checkpoint source boundary

- [Checkpoint1](docs/EARNINGS_CHECKPOINTS.md) is opt-in fresh accounting6/custody5/
  fee-intake1, without predecessors, for earnings endpoints only. Operator-pinned
  immutable bytes/source/config/anchor plus bounded suffix; never automatic cache
  approval or fabricated zero. The full24-hour window remains raw; preserve
  scaled NFT fractions, dust/cohorts, ownership/claims/conversions and today prices.
- Offline builder uses explicit bounded read-only work, all-NFT reconciliation
  and exclusive atomic candidate creation. API budgets remain unchanged. Retain
  raw/WAL backups and old artifacts; source/profile/reorg changes require reviewed
  rebuild/re-pin. No pruning, running config, signer or journal change is implied.
- Current evidence: final24new cases, broader147affected at its recorded earlier
  source stage. Do not sum overlaps. Lineage/other readers, actual workload/
  archive/rotation/restore and independent approval stay open. OpenSea research
  does not implement or approve its exact Robinhood drop caller/payment path.

## Royalty exact-unit source boundary

Fresh royalty4/recovery2/reporting5/schema13/canonicalV8 has18 deployed helpers;
ExactRoyaltyAllocation is internal code. Original currencies remain unchanged,
without royalty swaps/unwraps/converter. LP conversion/fractions stay separate.
The user explicitly authorized deterministic whole-unit rounding. GCD-normalize
the captured1/2/3 cohort, distribute quotient plus rotating remainder; preserve
earlier normalization books. Every ALLOCATED raw unit becomes one ticket's whole
claim, including the finite final unit. No royalty index/fraction reserve.
Ticket starts areONE-based(1first,0dormant); replay/checkpoint ticket_offsets are
ZERO-based. The currency rotation cursor is zero-based raw weight, divisible by
cohort GCD. Never compare source starts directly to internal offsets.

Strict actual producer/consumer EVM fixtures bind events/getters/V8 rows. Only
RoyaltiesAllocated credits income; positive receipt/opening/recovery telemetry
acknowledges it, zero canonical-settle telemetry is not an income credit.
V8 exports flattened whole rights without deleting source books, preserves
activation order independent of mint order, checks exact liabilities/backing,
and rejects V7. Rebuild/review checkpoints; never relabel old runtimes/journals.

Constructor/preadmission/zero-cohort funds stay reviewed unallocated until their
authorized decision. Default16ERC20+ETH may expand to64 after gas/service review;
source inventory13 permits97 total token records, older observer bounds stay
explicit. Unknown/frozen/taxed/rebasing/unreachable-owner cases cannot have a
universal automatic payout guarantee. All allocated rounding units are assignable,
not all imaginable tokens transferable. Current-owner rights and outage cohorts
remain. See [exact rules](docs/EXACT_ROYALTY_ALLOCATION.md).

Default optional royalty sync gas is1m(existing100k–1m bounds). Lowering it may
defer healthy currencies. Router32 is a count limit, not worst-case gas approval.
Factory stores only constructor-derived fixed creation bytes and immutable hash;
create accepts no code/recipient/salt, verifies hash, deploys typed NFT-bound ledger.
Its high one-time initialization gas requires actual target-chain qualification.

Mint review uses Vault's six-word fingerprint(domain,core Policy fingerprint,
NFT,receiver,mintEnd,mintEndRevision). Every end setter increments revision;
final Vault check follows payee callbacks. Core Policy hash alone is insufficient.
Cancelled importer royalty recovery waits for full abort restoration, follows
only authenticated retired V8 hops, and requires CURRENT verified target governance
with nonzero review hash, admitted asset, open window and stable active cohort.
Existing VaultCanonical validates hops read-only; only coordinator writes routes
or calls the cancelled ledger. No arbitrary recipient, principal movement or swap.

Use [current audit](reports/last24h-audit-20261105/REVIEW.md) for exact failures,
corrected source stages, verification/gas/size/static limits. Earlier royalty3
counts and bindings remain historical. No deployment/site/service/signing change.

## Operator documentation maintenance

The maintained manual's short four-column call tables cover every current ABI
function, constructor and receive hook. `docs/operator-call-examples.json` binds
its complete function reference. For function/input/permission/value changes,
review the notes, regenerate the ABI reference, update explicit examples/caller
classes and regenerate `scripts/generate-operator-reference.py`. Normal verification
runs both `--check` commands; no silent skipping/new default examples. Descriptions
are1–5words; tuples/arrays expand in ABI order. Keep reads, nominated callers,
keeper-only, governance, module/callback and deployment roles distinct. Templates
are unresolved documentation, never a simulation, live snapshot or transaction.
Historical source plans are exact-Git pointers; preserve source-scoped reports,
versioned codecs, old journals, original failures and actual environment boundaries.

## Verification and records

Current test maintenance must distinguish actual royalty4/V8 consumers from
explicit historical imports. Use the real1-hour opening; do not compare zero
claimables while claiming to preserve earned rights. Closed canonical imports
must not resume primary minting. Keep true initial-pool and zero-cohort cases
separate, require nonvacuous funded claims and exact healthy royalty conservation,
and verify rejected entry refunds/state rollback without relaxing idle guards.
Sixteen1M optional faults do not fit12M; larger local envelopes are not operating
qualification. See [test map](reports/last24h-audit-20261105/TEST_MAINTENANCE.md).
Unchanged normal/static source evidence needs no rerun for test-only corrections.

[Four-audit consolidation](reports/four-report-consolidation-20261104/REVIEW.md)
maps the latest manual/confirmation/market/indexer reports to current source;
original36files remain immutable. New indexer startup is transactionally admitted,
failed connections close and durable rollback/WAL are required. SQLite chain ID
<=2^63-1; start and max_reorg_depth<=2^63-2. Keep valid database identity/schema;
no rescan, runtime or journal migration is implied.93focused Python passes include
9new startup regressions; negatives retained. Current manual-safeguard normal/
static/callable pins are exact unchanged reuse, not a fresh contract audit.
No environment rollout or independent approval. See the single operator procedure.

- Current source/evidence: [profile identities](docs/POSITION_V6.md),
  [features](docs/IMPLEMENTATION_STATUS.md), [consolidated findings](docs/AUDIT_FINDINGS.md),
  [report map](reports/README.md) and [release approval](docs/RELEASE_CHECKLIST.md).
  Historical report bytes/source scopes remain immutable; do not sum overlapping
  tests or describe old analysis as current. The consolidation is not a new audit pass.
- [Historical authority evidence](reports/authority-audit-20261103/VERIFICATION.md)
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
  No deployment/journal/service is upgraded by publication. Current principal wire remains
  accounting6/custody4-format; current royalty header uses canonicalV8; see [permissions](docs/ACCESS_PERMISSIONS.md).
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

## Royalty launch and capacity source boundary

ONE-hour3600-second final grace, not24hours. Configure NFT.setMintEnd to final
OpenSea stage; governance can revise only while OLD end has not passed. Review
fingerprint/revision invalidates stale operations. Initial pool belongs to strict
pre-cutoff activations; late activations future-only. Zero cohort remains explicitly
unallocated. Lazy sync/claim materializes initial allocation; no keeper job required.
LP claims remain independent. V8 capture waits for open/finalized window and all
initial currencies synchronized. Emergency/terminal LP paths remain independent.
Use [launch rule](docs/ROYALTY_LAUNCH_WINDOW.md) and the [current audit](reports/last24h-audit-20261105/VERIFICATION.md).
No changes to served current3, public signing, services, Anvil or journals.

Do not display the royalty deadline on dormant NFT cards. The final grace is
3600seconds; prior24-hour task drafts are historical only.
