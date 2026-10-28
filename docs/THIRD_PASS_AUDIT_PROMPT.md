# Third-pass audit brief

## Objective and frozen scope

Perform a third evidence-driven audit and implement justified repairs across
PoPL's contracts, accounting, backend, keeper, unsigned user flows, operational
controls and documentation. Seek incorrect behavior, financial misaccounting,
unsafe permissions, failure amplification, avoidable cost and gaps between
components. Do not equate another review, test count or internal report with
absence of vulnerabilities or production approval.

Baseline: `cb0aadfe61b0bdcebab1838adbcf1b5835215510`, ABEF/AAA main.
Audit the reachable main changes for **October26,27,28 2026 in Europe/Paris**,
using committer timestamps and recording author timestamps separately. Freeze
this calendar window even if execution crosses midnight. Inspect every commit
in that interval, its parent and changed-file inventory; distinguish code,
configuration, tests, documentation and publication-only commits. Trace changed
components into earlier unchanged callers/callees, deployed dependencies and
historical compatibility readers rather than restricting review to diff lines.
Separately identify pre-existing dirty files; never attribute them to these
commits or publish them as part of this task.

## Establish facts before proposing changes

1. Read AGENTS, PROJECT_CONTEXT, README, sole Todo, handoff, operator manual,
   architecture, profile definitions, security plan and relevant prior review
   receipts. Inventory actual code, callable ABI, deployment examples, dependency
   implementations and source-bound build/test evidence. Confirm statements
   against source, not a previous assistant answer or a Todo status alone.
2. Record Git heads, the exact date-window commit list, changed paths and current
   source hashes. Preserve original dirty documents before editing. Keep prior
   reports, negative controls and failed attempts immutable.
3. Mark each review area as inspected, verified by fresh evidence, covered by
   exact unchanged evidence, externally blocked, or outside this release with
   justification. A checklist/scenario inventory is not an execution test.
4. Distinguish a confirmed exploitable defect, reproducible incorrect behavior,
   defense-in-depth improvement, accepted trust/liveness tradeoff, and missing
   production qualification. Do not manufacture a bug or redesign merely to
   make a third pass appear productive.

## Requirements and authority boundaries to preserve

- Fresh accounting4, governance2, fee intake1, custody3, pricing2, Entry routing2,
  reviewed Entry1, LP routing1, quality1, confirmation1 and same-chain canonicalV5;
  historical profiles/Anvil/journals retain original identities.
- One immutable deployment ZZZ and native ETH inputs; minimum100USD activation,
  5USD growth; one contribution pool at a time, four historical buckets. No
  restored stablecoin inputs, configurable token identity, bridge, arbitrary
  custody exit, generic sweep or Power weighting.
- Contribution/conversion/maintenance default loss limits2%/1%/3%, governed at
  most10%; additional loss excluding actual core trading fees defaults1%,
  separately governed0-10%. Stronger caller/venue/captured limits and gas separate.
  Two reviewed independent USD sources per priced asset,3% agreement tolerance.
- Fixed80/10/5/5 on actual harvested LP fees; collective weight equal per activated
  NFT; separate100% actual eligible NFT royalties at rarity1/2/3. Current owners
  inherit all unclaimed entitlements/fractions. Claims, conversions and imports
  are not new earnings; protocol reserves and returned principal are not rewards.
- Hard initial12-hour rebalance interval; actual physical range exit or deliberate
  approved width change, not centre chasing. Manual +/-25/50% selection, separate
  compound clock, hourly independent harvest. No passive/40%/TWAP strategy.
- Sampled confirmation duration900sec, check300sec and maximum gap exactly300sec,
  reset on a greater gap; gap0 constructor stopped pending reviewed config.
  Jitter60-600sec after readiness while sampling continues. Preserve explicit
  manual width exception/cooldown and raw need versus buffered readiness.
  Samples do not prove uninterrupted persistence; do not silently add grace.
- Direct governance controlled by the single human operator, limited service
  keeper and separate guardian capabilities; no timelock or invented committee.
  Normal holders cannot redeem principal. Paused governance-triggered collective
  exit closes actual ETH/ZZZ liquidity, allocates by NFT shares and pays current
  owners in bounded batches; failed receivers retain backed owner fallback.
  Future royalties, transfers and prior rewards survive; LP activity cannot reopen.
- Same-native-pair movement/parking and compatible pre-exit same-chain replacement
  remain; canonical handoff after collective exit is blocked.
- No public deployment, transaction, sealing, service restart/rollout, website
  deployment, Anvil reset, journal repair, funded-wallet use or monitor restart.
  Preserve port8902 and all existing NFTs/LP/balances/dist. Browser signer remains
  Anvil-only and public DEPLOYMENT null. Popldemo simulation and poplint unconfigured
  read/unsigned site stay distinct. Main only; Git publication is not deployment.
  Never print or commit secrets or credentialed endpoints.

## Review workstreams and adversarial cases

For every applicable area, trace normal entry, boundary values, adversarial
ordering, callback effects, partial/outage failure, recovery/retry and lifecycle
transition. Identify inputs, caller authority, preconditions, state writes,
external calls, emitted evidence, backing and consumers. Include interactions
that individually correct modules can mishandle together.

### A. Contract permissions, callbacks and lifecycle

Verify sealing/setup order and immutable identities, role grant/revocation,
post-callback pause/keeper checks, reentrancy and unsafe receiver behavior.
Trace preparation/freeze/import/abort/retire, parked/active/exited states and late
receipts. Check whether any route can bypass the confirmation, custody, pricing
or accounting controls. Test governance changes within an operation and stale
signed reviews without granting new authority or removing accepted flexibility.

### B. Contributions, NAV and shared-share accounting

Reconcile gross source input, conversion, exact approvals/native deltas, entrant
budget, marginal deployed LP, incumbent NAV, idle and compound at the same price
basis. Examine first/last shares, zero NAV, rounding, maximum cumulative per-NFT
contribution, changing pool ratio, deposits while outside, donations, fees from
entry swaps, failed placement and all rollback paths. Prevent entrant subsidy,
cross-bucket spending, double-counted principal and price-source substitution.

### C. Harvest, allocation, rewards, royalties and history

Independently derive conservation equations for harvested receipts,20-unit split,
remainders/index fractions, individual/collective entitlements, compound and
buyback reserves. Trace activation versus old receipts, transfers, claims in
different orders, optional currency faults, conversion credits, tiny repeated
receipts, terminal exit and pre-exit handoff. Verify source-to-ETH conversion and
burn spend only classified funds. Reconcile per-NFT versus collection totals,
claimable versus generated versus previously claimed,24h/all-time and today's
USD valuations. Missing data must be unavailable, not guessed zero. A legitimate
owner callback may change later batch claims; do not demand false preview equality.

### D. Price, routing, maintenance and manipulation

Verify oracle rounds/age/decimals/identity, actual source independence limits,
frozen lower/upper bounds and price/control revisions. Review on-chain tick/spot
consistency, physical LP ownership/PoolKey/range identity and actual-core quotes
after withdrawal. Check bounded venue catalog/search, rollback-only quote state,
zero/one swap, deterministic sizing, fee-adjusted versus all-in floors, idle
attribution and empty-catalog behavior. Distinguish accounting safety from IL,
market losses, sandwiches, repeated permitted loss and keeper personal trading.
Audit the recent buffer, quality and routing changes together, not individually.

### E. Keeper timing, persistence, recovery and observability

Trace pending-first scheduling, nonce/hashless intent reconciliation, canonical
receipt anchors/reorgs, save failures, crashes between each durable transition,
lost server/key rotation and same-key manual calls. Verify cooldown/compound/
harvest/jitter/sample clocks, clock retreat, strict gap boundaries, stale/foreign
evidence and clear acknowledgements. Check fairness/starvation, paid-revert
cooldowns, distribution retry clocks and receiver backlog. Review RPC outage
isolation, budgets, signer boundaries, watchdog behavior, file/config hashes and
health freshness/bindings versus actual cycle success. Local hashes are not
runtime attestation; a health file is not consensus proof.

### F. API, inventory, indexer and unsigned wallet flows

Audit typed ABI/JSON/RPC envelopes, canonical block pinning, caching, malformed
and contradictory data, coherent-but-untrusted provider limits, identity versus
eligibility, profile downgrades and historical recovery. Verify pagination,
bounded complete holdings, per-client concurrency/budgets, deadlines, isolation,
database reorg/backfill atomicity and consistent aggregate/individual results.
Trace unsigned approvals/transactions, exact amount/spender/value, review expiry,
simulated complete operation and interrupted/rejected wallet recovery. Read the
separate website only to verify compatibility/boundaries; source changes there
require a justified independent scope, never activation of public signing.

### G. Deployment, dependencies, operations and documentation

Inspect selected Uniswap/package implementations and code-hash/proxy limits,
native settlement, authority/config examples and error handling. Verify normal
EIP-170/EIP-3860 sizes with exact constructor arguments and existing guardrails;
do not relax compiler/gas/security gates. Identify unqualified feed/route/VRF,
OpenSea, hosting, gas and operator procedures explicitly. Match callable inputs,
permissions and outputs to current docs; remove obsolete *current* instructions,
preserving historical receipts. Review operator stop/restart, recovery and
readiness wording for actions that are impossible or unsafe in current source.

## Evidence and implementation discipline

Start with changed-code analysis, source/dependency reads, concrete financial
equations and minimal counterexamples. For each confirmed finding, record the
trigger, expected/actual result, affected version, impact, source lines and a
bounded reproduction. Where useful, prove the regression fails before the fix
and passes after; retain failures. Correct defective test fixtures or vacuous
assertions before treating a green run as evidence.

Prioritize real financial/authority/recovery defects, then fail-closed admission,
availability, reporting and efficiency. Make the smallest justified repair and
review its new failure modes. Separate behavior-preserving refactor, bug fix,
defense-in-depth, policy change and feature removal. Do not weaken gates or
change economic/custody rights to make tests pass. Ask only when a consequential
decision remains unresolved; continue independent work meanwhile.

Run focused new/affected checks after changes. Reuse unchanged prior evidence
only with exact production/test/dependency/build/config pins and stated source
scope. Do not rerun broad unchanged suites to inflate counts. Count distinct
methods once; identify skips, intermediate failures, mocks and actual dependency
execution separately. Static coverage rows are not test passes. No live provider,
Linux/systemd rehearsal, deployed website or production qualification may be
invented from local synthetic results.

## Deliverables and completion criteria

1. Save this reviewed prompt and a source-bound three-day commit/coverage inventory.
2. Execute the review across the workstreams, implement supported fixes and
   verify affected behavior. Record inspected areas with no confirmed finding
   and blocked/remaining risks as carefully as confirmed defects.
3. Update the sole task ledger/generated Todo, feature/evidence reference,
   roadmap/release limits, operator/runbooks and repository context where affected;
   regenerate/check callable reference only when applicable. Preserve stable IDs.
4. Keep original dirty work, prior reports, services/sites and local chain intact.
   Publish only the exact reviewed allowlist on main under the repository workflow,
   verify local/remote heads and distinguish publication from deployment.
5. Report material prompt adaptations, repaired defects, actual fresh/reused
   verification and unresolved decisions/qualification. Do not claim exhaustive
   proof, eliminated manipulation risk or production approval.
