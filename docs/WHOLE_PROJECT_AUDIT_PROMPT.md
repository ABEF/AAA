# Whole-project audit and improvement brief

This is the maintained audit entrypoint. Earlier [third-pass material](THIRD_PASS_AUDIT_PROMPT.md)
and [passive-inventory research](PASSIVE_INVENTORY_PLAN.md) preserve their exact
historical Git text. They are research/checklist inputs, not current settings or
approval. Maintaining this brief does not itself execute an audit or deploy anything.

## Objective and authorization

Understand the complete current PoPL project, challenge decisions and implement
justified improvements in correctness, security, economics, operations, recovery,
usability, performance and maintainability. Do not stop at recommendations.
Preserve unrelated work and established economic rights. Read applicable AGENTS
instructions and the user's current authorization before acting. Publication is
not deployment, sealing, public transactions, service/site rollout, signer
expansion, chain reset, journal conversion or a heartbeat restart.

## Understand before changing

1. Capture Git branch/head/status and original dirty files. Inventory code,
   dependencies/compiler/settings, services, configurations, scripts, generated
   artifacts, actual deployments and journals. Distinguish implemented source,
   published code, running environments, historical evidence and qualification.
2. Read both applicable repository READMEs, [context](../PROJECT_CONTEXT.md),
   [profile](POSITION_V7.md), [architecture](ARCHITECTURE.md), [sole Todo](../TODO.md),
   [features](IMPLEMENTATION_STATUS.md), [findings](AUDIT_FINDINGS.md),
   [operator procedures](OPERATOR_MANUAL.md) and relevant original reports.
   Inspect implementations and actual dependencies; do not trust a diagram/title.
3. Trace every function, callback and cross-module interaction. The
   [source-bound reference](CONTRACT_FUNCTIONS.md) and
   [short operator examples](OPERATOR_MANUAL.md#operator-call-tables) inventory
   inputs/outputs/callers, but do not prove valid live inputs or human authority.
   Build an action/state/permission/backing/event matrix first.
4. Resolve knowledge gaps through version-matched primary documentation and
   dependency implementations: Solidity/compiler disclosures, OpenZeppelin,
   Uniswap, tokens/feeds/VRF/wrappers, marketplaces, Python/SQLite, RPC and wallets.
   Date and pin external observations. Do not assume a deployment, ticker/peg,
   provider support, price independence, hosting or production readiness.
5. Separate facts, user decisions, accepted trust, hypotheses, conflicts and
   unknowns. Critically review scope twice for omitted components/interactions,
   then continue useful authorized work while asking only material questions.

## Preserve current requirements

Read current owners for exact settings; never copy obsolete report defaults.

- Transferable ERC721 ownership, capped supply and fixed quota/artwork draw;
  no reroll. Reveal/metadata traits differ from activation and earned eligibility.
- Native ETH and one fixed ZZZ; one contribution pool, bounded historical buckets,
  one main and at most one optional same-pool residual, both Vault-owned.
  Value actual token amounts, not sums of liquidity across different ranges.
- Contributions checkpoint incumbents, spend entrant funds on MAIN only, prove
  actual marginal LP and issue NAV-priced shares. No recentering, clock reset,
  residual increase or subsidy from previous principal/idle/compound.
- Actual LP receipts split80/10/5/5; royalty rarity weights are separate. Harvest,
  conversion, compounding, burn and claims are distinct. Current ownership carries
  unpaid rights; earned, claimable and claimed amounts differ.
- Current royalty4/recovery2 pays original currencies, with exact whole-unit
  rarity tickets, a one-hour post-sale opening cohort and reviewed capacity.
  Admitted currency outages protect earlier cohorts. Recovery of genuinely
  unallocated value is a separate current-weight allocation and cannot consume
  earned/deferred/import backing. Fresh accounting7 LP allocation is exact-unit
  too; historical fractional ledgers keep their own codecs and liabilities.
  ERC2981 requests payment; it does not universally enforce it.
- Mint2/canonicalV10 uses the pinned SeaDrop helper with phased TEAM/allowlist/
  public quotas and original-recipient lifetime counts. Source9/V9 and source10/
  V10 browser consumers are distinct unsigned profiles; implementation is not
  live onboarding, deployment, provider or operating acceptance.
- Optional execution-price1/LP-routing3 captures both independent ETH/ZZZ bounds,
  proves actual-core output/full post-state before settlement and validates live
  sources and callbacks. Public pricing2 remains live. Distinguish swap/reference
  overlap from prohibited same-core principal/reference identity. Omission/0
  retains LP2, not an implicit upgrade. Qualify full-operation gas separately;
  controlled expensive Entry execution does not fit the default12M budget.
- Ordinary sampled trigger/readiness, cooldown/jitter and explicit geometry
  changes differ from manual keeper calls and paused governance emergencies.
  Optional financial bypass never bypasses custody/authentication/accounting or
  terminal lifecycle locks. No automatic unsafe fallback.
- One human governance/operator, direct authority, separate keeper/guardian and
  bootstrap capabilities. No timelock, generic executor, bridge or chosen
  principal/royalty custody recipient. Sealed identities remain protected.
- Residual closure, parking/resume, same-pair movement, terminal holder return
  and pre-exit same-chain replacement are different workflows. Terminal return
  cannot reopen; NFTs keep transfers, past rewards and future royalties. Token/
  chain replacement and post-halt recovery are not automatically implemented.

## Full workstream coverage

For every feature/function cover caller, inputs, preconditions, reads/writes,
external calls, outputs/events, actual backing, rollback, restart and irreversible
limits during normal, concurrent, adversarial and long-lived operation.

| Workstream | Required coverage |
| --- | --- |
| Architecture/authority | Constructors/module graph, immutable parents, permissions/sealing/rotation, replacements, approvals/recipients, runtime/ABI identity, proxy/upstream powers and governance trust. |
| Contributions | ETH/value and exact allowances, captured source prices/caller floors, callbacks, stale reviews, incumbent fees/idle/compound/residual, marginal LP/NAV/share dilution and rounding. |
| LP lifecycle | Main/residual mint/increase/harvest/close; bull/bear/reversal/gap markets; one→two→one transitions; active-main/main-floor guards; mixed/outside residuals; idle/dust, gas and range geometry. |
| Maintenance/execution | Sample/reset timing, cooldown enrollment/inclusion delays/jitter, pending-first priorities, compound scheduling, harvest coalescing/buyback; post-withdrawal depth, swap sizing/fees/impact, MEV and repeated permitted losses. |
| Prices/dependencies | Dual freshness/independence/agreement, spot/reference disagreement, decimals/rounding, sequencer faults, mutable token/wrapper/router behavior, exact transfers and unavailable-state handling. |
| Rewards/royalties | Actual funding,80/10/5/5, individual shares vs equal active membership vs rarity; exact-unit LP/royalty trees, split carry vs upstream receipt rounding, old fractional codecs, cohorts vs unallocated recovery, LP conversion/claim replay, original royalty currencies, ownership changes and rejecting receivers. |
| Recovery/migration | Pause vs flags, residual-only close, park/resume/move, manifests/nonces/epochs, optional emergency checks, terminal close/allocation/delivery/defer/fallback,1000-NFT mixed-wallet scenarios, export/import/backing/abort/retirement and late receipts. |
| Keeper/operations | Nonces/replacement/receipt provenance, outages/restarts/lost server, retries/budgets, stale config, manual same-key signing, Linux locks/users, minimal keys, monitoring and off-host recovery. |
| API/indexer/history | Canonical hashes/reorgs/complete ingestion, transactional SQLite/WAL, identities/codecs, transfers/history/current-price USD, checkpoints/fractions/cohorts/lineage, bounded work/concurrency/caches and unavailable-vs-zero. |
| Frontend/wallet | Demo vs integration and exact profiles, local-only/public-disabled signing, account/network changes, reviews/allowances/expiry, malformed provider responses, pending/replaced/reverted receipts, refresh/recovery and per-NFT confirmed updates. |
| NFT/marketplace/content | Fixed inventory/quotas, authentic randomness/provider rotation/funding, ordered reveal, metadata/hosting/cache refresh, marketplace mint/payment/recipient compatibility, enforcement choices and contract-holder compatibility. |
| Longevity/maintenance | Key/person/provider/chain/token loss, unsupported venues, operating economics, backups/archive/restore, manual control coverage, obsolete-code cleanup, size/gas/toolchain limits and source/task/document/publication consistency. |

Include boundary/zero/empty/duplicate/unsorted inputs, malicious callbacks,
changed authority/dependencies, price outages, failed transfers, delayed or
reordered confirmations, stale snapshots and partial off-chain work. Review
interactions between individually sound components. Do not claim exhaustive
proof of every market, token or future dependency.

## Implement, verify and report

Prioritize impact, reachability, evidence and recovery consequences. Distinguish
refactors from fixes, removals and behavioral/economic/architectural changes.
Justify consequential changes; ask where inspection cannot resolve a material
decision, while continuing independent work. Do not silently change rights,
custody, future-entry economics or risk tolerance.

Improve inadequate fixtures/assertions before testing. Use checks able to detect
the suspected fault, independent raw-asset/accounting witnesses, negative controls
and rollback/retry cases. Use actual local dependencies when necessary and label
models/synthetic feeds. Reuse exact unchanged evidence with scope limits; do not
rerun unrelated suites, sum overlapping passes, hide failures/skips or weaken a
guard to pass. Compiler/static/normal-size checks follow changed source scope.

Review fixes again across callers, backing/events, consumers and recovery. Update
owning docs/operator examples, feature/evidence, sole Todo/roadmap/release and
context together. Preserve original reports and source/commands/results/failures
in exclusive evidence paths. Finish with actual improvements/verification,
accepted risks, unknowns and remaining gates. Local/mock passes are not operating
qualification or independent production approval.
