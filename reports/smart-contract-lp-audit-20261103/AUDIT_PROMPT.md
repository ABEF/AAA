# Current-contract audit: LP management, accounting and recovery

Prepared3November2026 against main `e0ea4dcd4762c1c4016b7861bbacc42c2c1d72dd`.
This executable brief follows initial architecture/operating/source inspection
and primary-source research. Continue resolving evidence gaps during execution;
do not treat the brief or an inventory as proof that every function is correct.

## Objective and authorization

Audit the complete current smart-contract system, with detailed function/body
and cross-contract review of LP management. Establish intended versus actual
behavior, implement justified fixes within existing requirements, verify them
and update operator guidance, feature evidence, Todo and repository context.
Classify security defects, accounting errors, liveness limits, policy tradeoffs
and verification gaps separately. No claim of eliminating every possible risk.

Main only. Preserve unrelated dirty files, historical report bytes, current
Anvil/NFT/LP/balances, sites/services, journals, public-signing restrictions and
the user-paused heartbeat. Source publication authorizes no public transaction,
deployment, sealing, service restart or reinterpretation of an old profile.
Archive originals and pin sources/dependencies/tool settings before editing.

## 1. Complete the source and operation map

Use actual instructions, context, both relevant architecture/operating guides,
the sole Todo, source-bound callable reference, all current production sources,
constructors, libraries, inherited implementations and exact installed dependency
bodies. Reconcile the latest reports; do not inherit their conclusions blindly.
The current normal closure has52 production sources/31 dependencies, with pinned
Solidity0.8.26/Cancun/viaIR/optimizer1/Yul-disabled settings.

Build a per-function inventory covering public/external/internal/private bodies,
modifiers, constructors and payable/receiver callbacks. Distinguish interfaces,
automatic getters and inherited duplicate ABI rows from independently implemented
bodies. For each function establish purpose, caller, input units/bounds, lifecycle,
dependencies, reads/writes, external calls, output/event meaning, economic owner,
pre/postconditions, failure rollback, resource limits and recovery. Record review
depth and evidence honestly; do not label AST enumeration as manual review.

Follow each daily operation across all components: mint/reveal; Entry/direct
activation and growth; share/NAV checkpoints; harvest; individual/collective
claims and conversions; royalties; compound; buyback; sampled observation and
rebalance; desired mode/range changes; residual close; same-pair move; parking/
resume; paused emergency; terminal direct holder payouts; canonical same-chain
replacement/abort. Include read/API/keeper consumers only where contract outputs
or permissions affect them; this is not a website rollout campaign.

## 2. Research and interpret applicable guidance

Consult official Uniswap v4 liquidity actions, flash accounting, fee collection,
stored tick semantics, settlement/Permit2, and installed core/periphery code;
Solidity security/known-compiler-bug guidance and actual OpenZeppelin dependency
implementations. Verify known bugs against the pinned compiler/settings/source
patterns, including later disclosures; do not rely only on version-tagged docs.
Record sources and applicability. Examples are not production guarantees.

Do not import v3 assumptions: native ETH is supported, collection uses zero-delta
liquidity modification, LP amount math rounds differently from actual mint debt,
and stored tick can differ at an exact downward crossing. A precomputed quote is
not an inclusion guarantee. Code-hash pins do not freeze an upgradeable upstream.
Do not change compiler/dependencies automatically; demonstrate applicability and
tradeoffs before changing the reviewed build/deployment boundary.

## 3. Required invariant and threat review

### Principal, shares and entry

- Native ETH and one fixed ZZZ; one contribution destination; at most four
  permanent custody buckets. One logical share account has at most two Vault-owned
  LP NFTs in the same pool. Never sum raw liquidity across ranges as value.
- Activation/growth checkpoint incumbents, spend only entrant funds, balance into
  the existing main ratio, harvest swap-generated incumbent fees, prove marginal
  physical LP and issue aggregate-NAV shares. They must not alter the residual,
  recenter, reset the rebalance clock or use incumbent idle/reserves as subsidy.
- Test first/last/minimal/large entrants; mint/activate/transfer/claim orderings;
  live/empty/parked buckets; stale review after other users' actions; manipulated
  balances, donations, fake returns, approval/reset callbacks, zero/overflow and
  decimal/rounding boundaries. Check actual effective action/pool minima and
  per-NFT maximum semantics, not a remembered UI promise.

### Physical v4 execution and routing

- Read installed PositionManager mint/increase/decrease/burn and delta settlement.
  Authenticate exact core/periphery/parent/recipient, pool key, ticks, owner, IDs
  and liquidity; preserve per-ID approvals and zero residual allowances. Separate
  real native receipts from forced ETH and pre-existing token/PosM funds.
- Analyze all callbacks and reentrancy between modules, ERC20/ETH/LP operations,
  configuration changes, governance/keeper revocation, pause, preparation, terminal
  exit and source replacement. Pre/post checks protect different moments.
- Quotes must revert all trial effects; exact error shape/caller/context/directional
  spend/tick must be verified. Routing is bounded over reviewed venues and measured
  after our withdrawal. Analyze quote failure/gas starvation, partial fills,
  competing venues, changing fees, pool exhaustion, stale target and no-route state.
- Separate destination from swap venue, gross/extra loss, known directional fees,
  feed agreement, main allocation, idle and user floors. Verify arithmetic and
  captured policy/price vectors through close/swap/mint/refund. No unsafe fallback.

### Portfolio, compound and rebalance

- Default one main; optional qualifying main>=60% and one residual<=40% at ordinary
  replacement, not a continuously maintained allocation. Governed main floor may
  rise; residual initially half the corresponding side with positive spacing gap.
- Check enabled/disabled/pending/applied states, change/restore revisions, mixed/
  filled/outside residuals, both outside, trend/reversal/gaps, tiny inventories,
  high/low ticks and narrow/wide ranges. Closing only residual creates attributed
  idle; disabling must not drop backing. Repeated adjustments never create a third
  leg or confuse main growth with a new portfolio.
- Entry and compound increase main only. Rebalance closes/replaces both. Both-leg
  collection/valuation/closure and old-ID association cleanup must be atomic.
  Verify final actual active-main and allocation/utilization checks independently
  of quote ranking and captured maintenance retained-value floors.
- Initial ordinary policy:85% centre-to-boundary ZZZ-in-ETH price distance,
  same physical/reference side,600-second samples/maxgap300, service checks240,
  durable service jitter60–300 and hard12-hour minimum. Manual geometry exception
  is deliberate; do not silently add persistence/jitter to chain or remove clocks.
  Distinguish contract safeguards from keeper-only waits, including compound's
  pre-cooldown behavior. Evaluate liveness under disagreement, rapid markets and
  outages without rewriting accepted policy as a bug.

### Revenue, royalties and ownership

- Actual fees only; exact80/10/5/5, carried dust/fractions and pre-entry membership
  checkpoints. Dormant NFTs do not dilute collective rewards. Shares, collective
  eligibility, compound ownership and buyback reserves have distinct ledgers.
- Harvest is independent from claim, conversion, compound and burn. Repeated
  zero/small/large harvests, partial claims and all users' orderings must conserve
  every raw unit and preserve others' entitlements. Verify event meanings against
  actual outputs; reservation is not executed burn, conversion/import is not income.
- Current NFT owner inherits past unclaimed rights. Royalties are separately
  funded/weighted1/2/3 and maintain outage/deferred-entry cohorts. Check failures,
  double claims, callbacks, unsupported currencies, stale owners and conversions.

### Authorities, lifecycle and long-term recovery

- Direct governance, distinct limited keeper/guardian, immutable sealed bindings,
  bounded future policies and no generic executor/sweep. Verify setters and complete
  pre/post authorization, events, effective policy and pending-review invalidation.
- Audit every pause/unpause/disable/re-enable, preparation/cancel, raw residual
  close, park/resume and same-pair move. Inspect retained raw minima, nonces,
  source/destination controls and exact custody fingerprints. Tokens/pool failure
  can remain unrecoverable; never add arbitrary withdrawal to hide that limit.
- Emergency is paused governance-only with reviewed optional financial bypass,
  potentially near-total loss, and structural ownership/settlement retained. It
  must not become an automated ordinary fallback or leak bypass state afterward.
- Terminal collective exit closes both legs without swaps, pays proportional
  actual ETH/ZZZ to current holders in isolated bounded batches, preserves earned
  rewards/future royalties and cannot reopen LP or canonical replacement. Check
  partially completed closure/allocation/delivery, rejecting recipients, transfers,
  token faults, duplicate calls, gas budgets and reserve-only post-exit operations.
- Canonical same-chain capture/import/backing/activation/abort requires parked
  zero-residual state and exact semantic/runtime/config admission. No integrated
  bridge, external custody recipient, token-identity replacement or post-halt
  recovery exists. Do not reintroduce retired architecture.
- Analyze multiple days/years: quotas below1000, dust accumulation, stale feeds,
  provider rotation, decimals, pause duration, policy extremes, counters/time casts,
  repeated permitted losses, capacity/gas ceilings and stranded classified funds.

## 4. Verification and implementation discipline

Prioritize exploitability, economic impact and liveness; trace each claim to code
and a counterexample. Improve targeted fixtures/properties before tests. Reproduce
new defects against original source where practical, then implement the smallest
justified correction and verify positive/adversarial/rollback cases using actual
v4 core/periphery where relevant. Do not weaken a safeguard or fabricate prices/
routes/provider approval to obtain a pass. Mock assumptions must remain explicit.

Use exact-source existing evidence for unchanged behaviors; do not rerun unchanged
whole suites merely to increase counts. Changed Solidity requires normal object
runtime/initcode/constructor gates, source-bound callable updates, affected execution
and refreshed relevant static contexts. Existing Migration20-byte headroom is not
spare space to assume. Preserve all failed/empty attempts and source changes.
Fuzz/invariant and deterministic boundary tests have different evidence meanings.

Update operator inputs/permission/preconditions/post-state/rollback/remaining
recovery, the central ledger/generated Todo, feature evidence and handoff/context.
Verify links, exact staged/committed publication and remote main before claiming
publication. No report or local count establishes production readiness.

## 5. Completion report

Deliver the final prompt, primary-source knowledge/applicability record,
function/operation coverage with explicit depth/limits, prioritized findings and
fixes, exact fresh/reused verification, and unresolved decisions/release gates.
Continue all independently safe work if external evidence is missing; ask only
for consequential unresolvable decisions. Do not manufacture a code change where
the correct outcome is a documented accepted policy or unqualified dependency.

## Two pre-execution challenges

**Challenge1 — scope:** a generic LP audit misses entrant-generated fee harvesting,
two physical legs under one share account, exact downward ticks, classified idle,
desired/applied modes, terminal owner payouts and a parked canonical handoff.
These are explicit above. Uniswap examples alone do not verify this integration.

**Challenge2 — feasibility and evidence:** prevent false completion by enumerating
ABI rows, counting inventory as tests, silently changing12-hour policy, assuming
reference independence, treating cached quote/rounds as execution, waiving normal
size gates, or relabeling old profiles. Review depth, fresh/reused proof, irreversible
trust and missing real services must be explicit. Prompt review cannot certify
absence of unknown bugs; independent production review remains separate.
