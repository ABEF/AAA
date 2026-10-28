# October 27-28 change audit

Internal source review, completed 2026-10-28. **Undeployed; production NOT APPROVED.**
The [verification record](VERIFICATION.md) distinguishes fresh checks, reused
execution evidence and unqualified real dependencies. This is not an independent
audit, an economic-profitability campaign or a deployment authorization.

## Scope and method

The Paris-time window covers ten main commits from `85ba8b6` (before the window)
through `1cabb85`, with 270 changed paths including reports and documentation.
[Exact revisions and paths](scope.json) are preserved. A pre-edit external snapshot
recorded all tracked hashes and the four unrelated dirty files. Those drafts,
historical evidence, Anvil services, journals, sites and paused monitoring remain
untouched. Website main was read locally as `e5bb216`; its changes in the window
are operating/resumption documentation, not another website rollout.

The review followed the actual paths: contribution -> harvest/incumbent
settlement -> entrant balancing/deployment -> shares; maintenance -> close ->
post-close quote -> one swap -> LP/idle retained-value checks; and irreversible
exit -> frozen allocations -> current-owner payout -> future reward/royalty rights.
Separate reviewers examined custody/accounting, routing/dependencies and keeper/API
behavior. Existing tests were read before selecting affected new verification.

| Partition | Source reviewed and questions resolved |
| --- | --- |
| LP execution | Full new LPBalancer and current LiquidityManager/Registry, Strategy/ContributionPricing changes; Vault/Budget/Oracle boundaries. Quote rollback, feasibility bracket, post-close depth, callback/config revisions, exact output/postspot, entrant isolation and independent price vector. |
| Installed v4 dependencies | PoolManager unlock/callback/deltas; Pool directional fee/progress/downward-boundary behavior; ProtocolFeeLibrary composition; TickMath/SqrtPriceMath/LiquidityAmounts rounding call sites. No dependency implementation changed. |
| Custody and rights | Changed Access/Module, Vault/Budget, Migration/CustodyValidation, NFT/metadata/royalty/canonical, Compounder/Buyback and types. Irreversibility, frozen denominators, exact backing, current owner, isolated receiver failure, reward/reserve separation and maintenance clocks. |
| Services and integration | Changed keeper monitor/ops/principal, profile4 API/lifecycle/lineage/portfolio/activation/trace/principal reporting, LP context/profile helpers and fork/preflight tools. Pending/nonce recovery, canonical reads, unknown-profile refusal, job scheduling and degraded dependencies. |
| Current guides | Safeguards inventory, operator/recovery/operations, Todo acceptance text, features, roadmap, release and repository context. Preserve current3 poplint versus accounting4 source and exact historical scopes. |

This is review coverage, not a claim that all 270 paths or every possible market
state received an execution test.

## Findings and corrections

### P2: deferred principal recipients could monopolize the keeper

Previously `Keeper.cycle` always attempted principal distribution before all
post-exit jobs. The on-chain batch correctly permits individual receiver failure
without failing healthy recipients, including a successful transaction paying
nobody. The rotating worker reread those unpaid entries immediately. A rejecting
owner, or rejection in every remaining batch, could therefore cause repeated paid
zero-payout transactions and delay LP/royalty conversions, buybacks and metadata.

Corrected in [principal worker](../../keeper/principal.py) and
[scheduler](../../keeper/monitor.py):

- Ready-phase batches use their existing canonical successful-receipt clock,
  keyed by starting ordinal. Default retry interval is 3,600 seconds, configurable
  from 60 to 86,400. A missing clock never delays the first attempt.
- Durable first/last job priority alternates delivery with other jobs, even at
  minimum retry spacing. Allocation remains prompt and ordinary one-pending-action
  nonce/gas limits are unchanged.
- Actual paid flags and amounts are always read from the contract. A successful
  receipt does not prove every holder was paid; no local paid cache was added.
- Existing paid-revert cooldowns remain independent. Saved pending recovery
  precedes new configuration/priority validation. State-save failures roll back
  the attempted in-memory cursor/priority update.

The new tests detect both archived defects and preserve restart, malformed
clock/configuration, 1,000-ordinal rotation and independent-job behavior. Actual
supervised service rollout, receiver backlog alerts and gas qualification remain
open. See the [operator retry procedure](../../docs/KEEPER_RECOVERY.md#optional-automatic-principal-delivery).

### Low: stale source comments and current operating instructions

Two comments referred to removed `configure()` and native-to-WETH/ERC20 LP moves.
They now describe `configureNative()` and native ETH/fixed ZZZ admission. There is
no Solidity behavior, permission, ABI or storage change. The normal compiler
comparison verifies equal instructions except compiler metadata; fresh source
pins replace the old metadata identities.

Operations still said best-venue sizing was unimplemented, that contribution
could reinvest incumbent compound, and that a historical accounting3 inventory
qualified the fresh release. These are corrected. Todo text no longer points to
a removed external-custody workflow or metadata status. The project profile now
names Entry routing2 and separate LP execution1 explicitly. The
[Keeper safeguards inventory](../../docs/KEEPER_SAFEGUARDS.md) is linked from the
README, operator guide and documentation map and is part of future maintenance.

## Examined hypotheses without a confirmed new defect

- Reverted actual-core quotes unwind pool changes and transient deltas; they do
  not create fees or settle funds. A failed reviewed venue does not remove healthy
  candidates or the no-swap baseline.
- Replacement planning occurs after closing old LP. Entrant-only budgets constrain
  both balancing and deployment; old idle/compound stays in incumbent NAV. Old and
  self-swap fees settle under incumbent membership before new shares.
- Captured source/target policies, monotonic revisions, exact raw deltas and
  physical LP checks prevent a callback from silently substituting execution
  context. Keeper/pause completion checks remain after external maintenance.
- Policy2 requires actual physical range exit or deliberate operator width change
  after cooldown; 1% movement alone is insufficient. Separate compound timing
  yields to due rebalance and cannot reset its clock. Hourly harvest is independent.
- Collective exit freezes share denominators and uses cumulative-floor allocation
  to conserve actual ETH/ZZZ. Current-owner resolution, paid markers before
  isolated transfer and owner-only fallback prevent duplicate/redirected payouts.
  Earned rewards/buyback reserves remain separate; future royalties continue.
- Profile4 projections and explicit historical codecs remain separate. Current
  read/trace bindings reject inconsistent profiles rather than fabricating data.

No new high/critical or monetary-accounting flaw was confirmed in these inspected
partitions. That conclusion is bounded by static review and the scoped evidence;
it is not proof of absence of defects.

## Remaining risks and qualification

- **Keeper personal trades / outside ordering:** a keeper can trade ZZZ around
  its chosen eligible submission time. Deterministic amount/route, independent
  references, cooldown and per-operation limits constrain the transaction but
  do not prove every surrounding trade unprofitable. Profit and holder loss are
  not inevitable either. Jitter and simulation are bypassable software controls.
  No economic attack campaign was performed or previously blocked campaign retried.
- **Repeated losses and governance:** per-operation caps are not a cumulative
  loss budget. Governance can immediately loosen approved bounds or choose unsafe
  dependencies. These accepted authorities were not silently changed.
- **Maximum quote work:** four venues x twelve attempts x 300,000 requested call
  gas is 14.4 million for quote calls alone, before other work. This is a bound on
  requested work, not a measured transaction cost. Deep tick crossing, maximum
  settings and Robinhood gas limits require actual qualification. The solver picks
  the best valid sampled useful-LP result, not a global or gas-adjusted optimum.
- **Exit availability:** all buckets must close before allocation. A permanently
  failed venue/token or lost governance can stall closure. Contract owners can
  reject or trap payouts; no operator confiscation/recipient override was added.
- **Real release inputs:** independent feeds, routes, VRF, authorities, OpenSea
  mint/royalty behavior, permanent artwork, exact accounting4 integration/services,
  target gas/operating rehearsals and independent audit/remediation remain open.

Track unfinished work only in the [sole Todo](../../TODO.md). No operating service,
public signing, website artifact, contract deployment or sealing changed here.
