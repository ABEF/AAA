# PoPL operator manual

Management procedures for the **undeployed candidate; production NOT APPROVED**.
The [sole Todo](../TODO.md) owns remaining work; the [release approval record](RELEASE_CHECKLIST.md)
records one frozen release. A procedure, local pass or GitHub publication does
not authorize public transactions, deployment, sealing or a service restart.

**Keep this manual current.** Changes to operator-facing functions, permissions,
defaults, parameters, lifecycles, services or failures must update the affected
procedure in the same change, or explain why there is no operator impact. Keep
[features/evidence](IMPLEMENTATION_STATUS.md) and the [task ledger](TODO_WORKFLOW.md)
aligned. This is a review obligation, not automatic synchronization.

## One operator and governance wallet

You are the project's single human operator and control its governance wallet.
Governance actions in this manual are actions you authorize from that wallet;
they do not require a separate operator, committee or second project manager.
The contracts have no additional "operator" role. The keeper is your automated
service, using a limited keeper key rather than loading the governance key onto
the server. You can also control the guardian/deployment/treasury accounts;
their permissions and rotation procedures remain distinct.

The governance wallet can be a directly controlled account or a compatible
single-owner Safe. Production wallet addresses/type remain unselected. For a
Safe, use its own signing flow so the Safe is the target caller; for a direct
account, that account itself submits the call. See [governance](GOVERNANCE.md).

Keeper `Vault.rebalance`, `Compounder.compound` and `Buyback.execute` require
the original keeper to remain authorized and the protocol unpaused through
completion, including after external callbacks. A failed completion reverts
the operation and the callback's state changes together. This is not a way to
interrupt another transaction: send normal pause/revocation from the appropriate
guardian/governance wallet, preserve any pending hash, then reconcile its receipt
and gas. It adds no withdrawal power or economic-parameter change. See the
[scoped review](../reports/manipulation-hardening-20261027/REVIEW.md).

## Pool, positions and pause: what each control means

The main LP and optional one-sided residual are **two positions in the same
ETH/ZZZ pool**, not two independently pausable Uniswap pools. A residual can
become mixed as price moves; its current actual tokens always remain accounted.

- **Change policy:** `PortfolioPolicy.setMode(pool,false,reviewHash)` stops future
  residual creation and requests a guarded merge. It does not immediately close
  either position. No global pause is needed for this setter or the later normal
  unpaused rebalance. Read `enabled(pool)` first; same-value calls revert.
- **Close only the residual:** governance uses the paused `Migration.closeResidual`
  workflow. The main stays deployed, with unchanged ticks/liquidity. Its actual
  in-range Uniswap trading fees continue; residual proceeds become attributed
  Vault idle. This operation neither puts those proceeds into the main nor pays
  them to a wallet. Later guarded deployment is a separate operation.
- **PoPL global pause:** `Access.setPaused(true)` temporarily blocks ordinary
  PoPL live mint/contribution/harvest/maintenance work. It does not pause the
  external Uniswap pool, remove either LP or erase fees. Funded claims and NFT
  transfers retain their separate lifecycle permissions.
- **Unpause:** current governance calls `Access.setPaused(false)`. It does not
  change residual mode, restore stopped pool/asset/route flags, resume a parked
  bucket, cancel preparation or reopen terminal holder exit. Restore only the
  particular controls actually intended after fresh validation.
- **Stop all our deployed LP:** parking closes both actual positions into the
  Vault, preserving share ownership. Unpause alone does not redeploy them;
  `Migration.resume` does that under fresh deployment guards. External traders
  may still use other liquidity in the permissionless pool.

Normal return to one main is: **set mode false → wait for eligible successful
ordinary rebalance → verify one active main**. Immediate exceptional return is:
**set mode false → pause → reviewed emergency consolidation → inspect → unpause**.
There is no holder-facing principal withdrawal in either sequence.

## Find the right procedure

Production minting is intended for OpenSea; the website Mint page is a demo.
Qualify the exact mint product, chain, contract integration and collection URL
before sealing, following [mint integration qualification](MINT_INTEGRATION_QUALIFICATION.md).
Existing mint pause/reveal controls still govern external mint callers.

For full-wallet earnings and collection holder allocations, use the existing
reviewed read API with [current-holdings totals](EARNINGS_HISTORY.md#current-holdings-totals).
Match API/frontend versions, verify a complete same-block inventory, and retain
unavailable states on missing chunks/prices. No authority or transaction is added;
stop/rollback these reports through the read-service profile, not a chain reset.

| I want to... | Procedure |
| --- | --- |
| View the confirmed collection, LP totals, and recover failed reads | [Confirmed collection data](COLLECTION_READS.md) |
| Change +/-50% LP range to +/-20%, trigger, cooldown or execution settings | [Range and strategy](#range-and-strategy) |
| Enable/disable ETH or fixed ZZZ, or change an approved route | [Activation assets and routes](#activation-assets-and-routes) |
| Stop minting independently | [Mint-only pause](#mint-and-metadata) |
| Stop new LP entering a pool, stop maintenance, or open another pool | [Pool admission and retirement](#pool-admission-and-retirement) |
| Enable/disable a residual, close only it, or force consolidation into one main | [Portfolio management controls and recovery procedure](#portfolio-management-controls) |
| Stop everything possible, recover and restart safely | [Stop controls](#stop-controls) and [incident recovery](#incident-recovery) |
| Move existing LP, close it temporarily, or change chains | [Custody and LP migration](#custody-and-lp-migration) |
| Change prices, sequencer checks or wrapper policy | [Dependencies and pricing](#dependencies-and-pricing) |
| Collect LP fees, compound, burn or process royalties | [Revenue operations](#revenue-operations) |
| Change the automatic fee-harvest interval | [Standalone harvesting schedule](#change-the-standalone-harvesting-interval) |
| Inspect LP job waits, known blockers and simulation without changing state | [Read-only operation review](KEEPER_COORDINATION.md#read-only-operation-review) |
| Resolve pending artwork reveals or replace all contracts; recover failed holder-file/CLI input | [Mint and metadata](#mint-and-metadata), [whole-collection replacement](#whole-collection-replacement) |
| Change managers/keys, replace a server, update software or contain stalled RPC | [Authorities](#authorities), [services](#services-and-server-recovery) |
| Use a browser wallet locally, recover pending transactions or inspect exact approvals | [Browser-wallet signing and recovery](BROWSER_WALLET.md) |
| Run the current selected-pool read-only fork harness | [Development and fork qualification](DEVELOPMENT.md#fork-and-operating-qualification) |
| Publish poplint without changing the demo | [Demo/integration environment map](SITE_ENVIRONMENTS.md) |
| Configure reviewed API holdings; rehearse wallet sends on local Anvil only | [Reviewed website API profile](DEPLOYMENT_WEBSITE.md) |
| Prepare a reviewHash and exact ordered explorer inputs without signing | [Offline review preparation](#prepare-and-check-an-offline-reviewhash) |
| Find every manual write's caller, ordered inputs and reversal limits | [Manual write input catalog](#manual-write-input-catalog) |
| Know what cannot be changed after sealing | [Fixed boundaries](#fixed-boundaries) |

## Current accounting6 deployment boundary

Fresh source uses Vault.ACCOUNTING_VERSION6, ProtocolPolicy1, Migration.CUSTODY_VERSION4,
Strategy maintenance3 / confirmation3 / portfolio2, Budget compound4, LP routing2,
emergency2, Access.GOVERNANCE_VERSION2 and
`SCHEMA()==keccak256("ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6")`.
Verify exact chain/runtime/module/helper pins and the [fresh profile](POSITION_V6.md).
Normal size/runtime gates, scoped offline checks and local actual-v4-core
integration pass within their [recorded source scope](../reports/adaptable-policy-20261031/VERIFICATION.md).
Live dependency/operating qualification and independent review remain open.
Eight Position words remain; statuses are None0/Active1/Outbound2/Dormant3/
Parked4/Exited5. Historical profiles/Anvil/journals keep their own meanings.

- Contribution inputs remain native ETH and one fixed ZZZ. Entry binds exact
  value/approval, current owner, original source value, caller maximum and
  actual marginal LP. Activation/growth minima default100/5USD and are governed for future contributions;
  exact policy fingerprints and the2% default loss cap remain separate.
- Production LP admission is native ETH/fixedZZZ only through configureNative.
  Another reviewed fee tier is possible; ERC20-only LP admission is removed.
  Separate reward-conversion venues/currencies do not expand principal assets.
- Native LP fees retain80/10/5/5; claims and royalty weights are independent.
  Pending 5% compound belongs to principal on collective exit; designated buyback
  and already earned reward/royalty backing stay separate.
- Governance may pause and permanently start collective exit, close every bucket
  without swaps/USD price reads, allocate shares and deliver ETH+ZZZ to current
  owners in batches. No external custody recipient, recovery ingress, all-ZZZ
  conversion exit or royalty drain exists. [Exact procedure](HOLDER_COLLECTIVE_EXIT.md).
- Access.lpExitStarted is irreversible. Unpause cannot restart mint, activation,
  growth, LP maintenance or canonical replacement. Old claims/transfers and future
  royalties remain available; new LP earnings end after all buckets close.
- Default single main; governance may enable at most one residual in the same
  pool. Both actual LP NFTs belong to Vault and back the same independent NFT
  shares. Disabling desired mode does not hide a live residual before safe merge.
- Use explicit accounting6 API/keeper configuration, ProtocolPolicy1 pins and new state paths. API
  requires principal_exit runtime/address pins; keeper also binds access/fees/
  vault. Existing accounting3 poplint stays unconfigured and is not a profile6
  frontend. Public signing stays Anvil-only; no deployment is authorized here.

### Fixed ZZZ setup order

For a fresh deployment, bootstrap first deploys Access and the separately
predeployed `ProtocolPolicy(controller,initialMintRecipient)`, then calls
`Access.bindProtocolPolicy(policyAddress)` before constructing its consumers.
Verify exact controller/version/runtime and the initial valid mint recipient;
there is no dummy binding or post-seal helper replacement. Only then construct
and bind Oracle/other consumers and configure the two-source USD policies.
This documents setup order, not permission to deploy or seal.

Review and configure the two-source USD policies before source/pool admission. Bind
`ActivationAssets.configureZZZ(token,codeHash,reviewHash)` once before
`PoolRegistry.configureNative`; deploy/bind Buyback with that same immutable ZZZ,
then call the one-time `Migration.configureZZZ`. Verify matching nonzero source,
buyback and holder-return identities before sealing. A wrong immutable identity
requires a fresh reviewed deployment, not a post-seal repair setter. Raw emergency
exit does not gain a conversion/buyback dependency.

### Deployment and integration qualification

| Need | Procedure and boundary |
| --- | --- |
| Exact version, modules, helper runtimes and addresses | [Address inventory](DEPLOYMENT_ADDRESSES.md) and [schema8 preflight](PRODUCTION_PREFLIGHT.md), which observes17 modules/21 helpers; schema6 and older profiles are inspection-only. Observed code cannot approve its own runtime pin; retain creation-to-anchor policy history. |
| OpenSea primary mint and VRF | [Mint qualification](MINT_INTEGRATION_QUALIFICATION.md). Buyer gross 0.05 ETH, recipient net of actual platform fee, gas separate. Current direct mint still pays all 0.05 ETH; supported OpenSea/VRF integration is unfinished. |
| USD providers, proxy controls and update services | [Price security](PRICE_SECURITY.md), [service decisions](PRODUCTION_SERVICES.md) and optional [Pyth reader](PYTH_PRICE_SOURCE.md). Review upstream independence, update costs, funding and recovery; a matching ABI is not provider qualification. |
| Website read/unsigned review | [Served current3/fresh4 boundary](CURRENT_WEBSITE_PROFILE.md). Fresh profile6 readers are separate from the served accounting3 browser reader; source support is not a rollout. Neither accepts a historical accounting2 reader by relabeling. Actual consumer/service acceptance remains open; public DEPLOYMENT is null and signing Anvil-only. |
| RPC and exact frozen audit inputs | [Bounded RPC qualification](RPC_PREPARATION_QUALIFICATION.md) and [frozen review bundle](FROZEN_REVIEW_BUNDLE.md). A timeout is not proof of rejecting missing blocks; package export is not audit approval. |

Source-scoped audit results belong to [reports](../reports/README.md), not to a
second release history in this manual. The [current October31 analysis](../reports/day-audit-20261031/VERIFICATION.md)
has463 contextually dispositioned findings at the unchanged final source closure;
this manual-operation review reuses those exact production pins. Older analyzer
and handwritten body reports retain their original scopes. Refresh analysis
after source changes and qualify actual dependencies, target-chain gas/operations
and independent audit before release; internal triage is not release approval.


## Liquidity placement and keeper policy

For post-exit automatic payouts, configure the [principal worker and retry interval](KEEPER_RECOVERY.md#optional-automatic-principal-delivery). Repeated rejected batches default to hourly retry; serial-job priority alternates durably. Apply JSON changes through controlled restart, preserve the journal and refresh config-bound health; no contract update/resealing or new authority is required.

Read [keeper safeguards](KEEPER_SAFEGUARDS.md) for the full protection inventory
and the distinction between on-chain enforcement and bypassable service policy.

Use [idle and dust ownership](IDLE_AND_DUST.md) before any cleanup. Contributions
default to 2% (98% marginal deployed LP), conversion 1%, maintenance 3%, gas separate.
Fresh LP routing2 selects one bounded route/size using actual-core quotes and
executes zero or one balancing swap. Contributions can swap/deploy only their
own amounts; old idle/compound stays attributed for guarded maintenance and in
incumbent share NAV. Retained idle still backs the same bucket. There is no
general clear/sweep or operator dust recipient.

### Restore a buyback venue after collective exit

Use this only once `Migration.exitPhase()==3` (`Ready`). Every LP bucket is
closed and principal allocated then; holder payout batches may still be pending.
During Closing/Allocating, pool admission/reopening remains blocked.

1. From the governance wallet, read the exact admitted/new ETH/fixed-ZZZ PoolKey,
   actual initialized fee/tick spacing, pinned native runtimes and fresh reviewed
   feeds. Copy/review the entire `PoolConfig`; set `depositsEnabled=false` and
   `operationsEnabled=true`, retaining supported parameter limits. Prefer stopping
   obsolete contribution/operation flags explicitly with `disablePool` where needed.
2. Simulate and call `PoolRegistry.configureNative(fullConfig)`. Inspect the
   returned PoolKey-derived ID, `PoolConfigured`, `get(id)`, `configurationRevision`
   and the unchanged irreversible exit flag. Full validation failure reverts all
   writes. This call cannot reopen principal or move funds.
3. Separately review the keeper buyback task's `pool_id` and ETH input/budget.
   Pool admission does not auto-select a job route. Stop/reconcile pending work,
   preserve journal/nonce/spend history, apply a controlled source/config reload
   and verify matching fresh health before enabling the changed job.
4. Actual `Buyback.execute` still requires the keeper grant and ordinary unpause,
   fresh prices, execution floors, reserve/operating ceilings and verified fixed-ZZZ
   supply burn. Governance may unpause these remaining ordinary operations; no
   principal path restarts. Migration-held holder funds are separate and cannot
   be spent by this venue configuration or buyback.

This source behavior requires the reviewed new Registry deployment. Existing
Anvil/old releases are not upgraded by changing configuration or this runbook.
[Scope and evidence](../reports/comprehensive-popl-20261029/VERIFICATION.md).

### Add or remove an execution pool after sealing

This changes the swap venue, not the LP contribution destination. Use the fresh
Manager `LP_ROUTING_VERSION()==2`, fixed `balancingRouter()` and typed
position/arithmetic children;
Entry routing2 is a separate capability. Historical deployments are unchanged.

1. Review the future pool's full native ETH/fixed-ZZZ static hookless key,
   initialized state, pinned dependencies, actual fees/depth, independent prices
   and full-operation costs. Governance admits it through
   `PoolRegistry.configureNative(fullConfig)`, normally with
   `depositsEnabled=false, operationsEnabled=true`. One contribution pool remains.
2. Read the helper's current `executionPoolCount()`/`executionPoolAt(index)`.
   Governance submits the complete replacement list to
   `configureExecutionPools(ids,reviewHash)`: at most four unique admitted pools,
   nonzero reviewed evidence hash. Include the old venue only if still approved.
   Simulate actual post-close replacement and both contribution directions.
3. Verify the event, `executionRevision`, exact list, runtime/parent/core/state
   bindings and current execution-policy pins. Future balances compare valid
   candidates automatically on-chain; the keeper does not pick an arbitrary route.
   No LP move or Solidity edit is necessary for a compatible new pool.
4. To stop a bad route, remove it from the list, or use the existing dependency-
   free `disablePool(id,false,true)` stop. `configureExecutionPools([],reviewHash)`
   removes all swaps without price/core reads. There is no implicit target fallback.
   Balanced operations may continue; operations needing a swap must still pass
   final LP/value guards and otherwise revert. Re-admission requires full validation.
5. Reconcile pending work around changes. On-chain settings are read afresh; they
   normally require no keeper restart. Local version/runtime/endpoint/config
   changes need controlled restart with the same intact journal. A changed list
   does not cancel a broadcast transaction or waive caller limits.

A saved pending transaction is recovered before new LP-router metadata checks;
an unavailable router never permits a new balance operation. Runtime, signer,
accounting and nonce/receipt guards remain; due fee harvesting stays independent.

Governance can tune `configureSolver(iterations,gasLimit,reviewHash)` within 4-12
iterations and 100000-300000 gas per attempted quote; defaults8/200000. More search
can cost more gas; inadequate quote gas may skip a usable venue. Keep actual
measured operating values and simulate the whole call. The helper stops early
near a useful ratio and never performs a second real correction. Runtime pins
and this method do not qualify proxy controls, liquidity or market execution.

Idle-only reinvestment uses the existing `Compounder.compound(bucket,minLP,deadline)`
with current prices, actual LP, captured maintenance budget and its separate compound interval.
`Budget.lastCompound(bucket)` changes only on success. Configure keeper opt-in,
both actual currency thresholds and reviewed Budget pins using the specialist
[keeper/range guide](RANGE_POLICY_UPDATES.md). Stop scheduling and reconcile pending
hashes before changing services; do not reset journals or count principal as income.

### Explicit ZZZ-price orientation and two-range selection

For the selected operating policy, choose the width manually in steps1-2 and keep
automatic selection disabled. Steps3-6 describe the existing optional capability,
not a required service or newly added volatility analysis.

1. Read exact Strategy/Registry versions, runtimes, full pool config and physical
   ticks. New `RANGE_POLICY_VERSION()==1` profiles are explicit. Mode0 preserves
   historical raw `token1/token0`; mode1 means `token0/token1`, ETH per ZZZ for
   this native ETH/ZZZ key. Governance calls `setRangeOrientation(pool,1)` only
   if not already1. The change disables an enabled automatic policy and creates
   a desired tick mismatch; it does not move funds or instantly change artwork/NAV.
2. Choose initial `rangeBps`2500 or5000 through full pool configuration. In mode1,
   ZZZ price `P` in ETH has endpoints `[0.75P,1.25P]` or `[0.50P,1.50P]` before
   outward ticks. Normal oracle/spot checks still use the actual raw pool ratio.
3. Review drift thresholds and cadence economically, including MEV/turnover and
   both widening and narrowing. Governance explicitly calls
   `setKeeperRangePolicy(pool,true,narrowBps,widenBps,interval,reviewHash)` with
   `0<=narrowBps<widenBps<2500`,600 seconds<=interval<=7 days, and interval at
   least the pool cooldown. Trigger/deviation must fit the narrower width.
   No default production thresholds or continuous-volatility claim is supplied.
   This optional automatic policy cannot be enabled while confirmation3's
   `requireReferenceExit` protection is enabled. Preserve the selected manual
   policy; relaxing reference protection would be a separate explicit governance
   decision, not an automatic workaround for a rejected setter.
4. Verify orientation, complete `keeperRangePolicy(pool)` and configuration/review
   hashes. The fingerprint binds all PoolConfig fields except desired width plus
   orientation. A changed non-width config makes selection unavailable until
   governance re-reviews it. `keeperRangeTarget(pool)` returns0 unless all policy,
   lifecycle, actual-position, cooldown and unapplied-tick checks pass. Malformed or
   failed dependency reads can revert; report unavailable, never coerce them to 0.
5. Enable reviewed keeper `adaptive_range` only on this matching version/runtime.
   It calls `Strategy.applyKeeperRange(pool)` with no width argument. The on-chain
   rule chooses2500 or5000; the fixed Strategy's Registry callback can change
   only width, never assets, recipient, feeds, pool flags or loss limits.
6. Selection and LP movement are separate confirmed transactions. The normal
   `Vault.rebalance` then applies ticks under its cooldown, price/close/swap/deploy
   and captured maintenance floor. Verify actual LP/ticks/center, retained value,
   unchanged shares and claims. Failed execution leaves the old physical LP and
   desired width pending; no automatic raw exit or repeated width selection follows.

To stop automatic selection, governance calls
`setKeeperRangePolicy(pool,false,0,0,0,bytes32(0))`; disabling needs no healthy
Oracle/venue. Disable off-chain scheduling too and recover any saved hash before
restarting. This does not cancel a broadcast selection/rebalance or restore a
previous physical range. To restore manually, disable policy, review full pool
config/orientation and use ordinary guarded rebalance. Pause maintenance/disable
pool operations for containment; funded claims retain their existing rules.

The rule measures current oracle displacement from the last applied center;
it does not observe every intervening price or prove sustained low volatility.
The keeper cannot choose arbitrary widths, bypass prices or guarantee always-in-
range LP. Polling and a target width are not a promised execution time.

<a id="configure-stop-and-recover-usd-pricing---2026-10-24"></a>

## Configure, stop and recover USD pricing

The [pricing-V2 guard](PRICE_SECURITY.md) requires two independently reviewed USD
sources per priced asset. The old single-feed `setFeed` entry point is removed;
its instructions and deployed profiles are historical. Do not use one ETH/USD source plus one
ZZZ/USD source as redundant coverage for both assets.

1. Disable affected pool contributions with `disablePool(poolId,true,false)`;
   pause broader maintenance if necessary. Stopping does not require a working
   price source. Preserve pending hashes, holders' ledgers and all raw balances.
2. Review both exact chain/source addresses, runtime and proxy/implementation
   authorities, underlying markets/reporters, USD denomination, decimals, ages,
   disagreement bounds, outages and depegs. Independence IDs and review hashes
   record reviewed assertions; they do not prove independence by themselves.
3. Simulate the exact governance call `Oracle.setDualFeed(token,primary,secondary,
   maxDeviationBps,reviewHash)`. Each source tuple contains `source`,
   `expectedCodeHash`, `independenceId`, `maxAge`, `feedDecimals`. Source age must
   be 1-86,400 seconds; spread is 0-500 bps, with zero requiring exact agreement.
   Those are hard code bounds. The user selected **300 bps (3%)** for the
   intended configuration. Both current rounds must already pass admission.
   Actual source pairs and freshness settings remain unqualified.
4. Execute through existing immediate governance, then verify `DualPolicyRecorded`,
   `DualPolicyActivated`, `activePolicy`, `policyAt`, the full immutable policy and
   `priceBounds`. Confirm lower/upper values, both rounds and fingerprint. The old
   policy remains in history. Never promote observed hashes to approved pins
   automatically or remove a safety check to make a price appear available.
5. Refresh the schema8 release inventory with explicit `pricing_version: 2` and
   all21 helpers, including `Oracle.contributionPricing()` and its `oracle()`/
   `access()` bindings. Update reviewed API/preparation/earnings configurations,
   source proxy pins and service alerts at one confirmed block. Keep old deployed
   epochs and wallet journals on their original profiles.
6. Qualify the current governed activation/growth minima (default100/5USD) in actual token units through the full
   route and LP operation, including callback/round changes, depegs, divergence,
   outages/recovery and worst-case gas. Reopen only with complete validated pool
   configuration and qualified dependencies. Retain actual receipts/evidence.

Entry freezes prices and both contribution/venue limits before the original
source transfer and conversion. Callback changes, even a later tighter limit,
require a fresh review. Existing nonzero historical compound keeps its starting
mark; newly discovered historical compound is first marked at the final
checkpoint only for incumbent backing, never the new LP floor. Source uncertainty
uses some of the captured execution budget: even agreement inside 3% can fail
the separate default 2% contribution execution floor. A failed quote does not authorize an
automatic cap increase, stablecoin peg, spot price or single-source fallback.

If either source fails, retain unavailable status and disable affected work until
both sources recover or governance independently reviews a new pair. Raw-unit
funded claims need no USD feed; the paused collective holder close
keeps its separate exact minima and no USD guarantee. Failed pools/tokens can
still prevent movement. See [preflight](PRODUCTION_PREFLIGHT.md) and
[raw recovery controls](GOVERNED_CUSTODY_HANDOFF.md).

Source, asset-decimals and sequencer reads use ProtocolPolicy.sourceCallGas(),
default500,000 and governed100,000–1,000,000, with exact ABI checks. Qualify actual
proxy gas before changing it; the optional Pyth reader has its own immutable
300,000 upstream cap and may require a newly reviewed adapter. Strategy
read snapshots last one planning call only; execution/final checks re-read. Raw
funded claims do not need USD prices. Public push-feed reads need no per-read
LINK transfer, but adapters, updates, RPCs and VRF can cost money; review each
actual product and upstream authority. [Price operating requirements](PRICE_SECURITY.md).


<a id="pending-15-minute-rebalance-confirmation"></a>

The [whole-operation assessment](../reports/normal-operation-design-20261029/REVIEW.md) explains the different
contribution, reserve, idle, harvest and maintenance paths. The implemented
[read-only keeper review](KEEPER_COORDINATION.md#read-only-operation-review) covers
rebalance, compound and harvest; broader operation adapters remain unfinished.
It reports known blockers and explicitly unavailable evidence, not a universal
execution approval. Do not infer a specific cause from stale health or a generic
simulation error, or replace raw need with sampled readiness.

### Configure rebalance confirmation

For fresh confirmation3, resolve `Strategy.rebalanceConfirmation()` from the
sealed Access Strategy. Verify Strategy/helper/Budget capability3, Budget
compound4 and exact parent/runtime bindings. The standalone helper resolves its
fixed parent through the sealed controller; it has no mutable parent setter.
Old deployments and journals retain their explicit historical profiles.

1. Governance calls helper
   `configure(uint32 secondsRequired,uint32 maximumGap,bytes32 reviewed)` with
   intended values `600,300,<nonzero review hash>`: ten minutes of sampled
   evidence and a strict five-minute maximum confirmed gap. Supported duration
   is 60 seconds–7 days; maximumGap0 stops sampled market-trigger readiness, otherwise at most half
   the duration. Construction starts gap 0, not a fabricated operating approval.
2. Verify `ConfirmationConfigured`, duration/gap/review and increased
   `policyRevision`. Every reconfiguration, including change-and-restore,
   invalidates old samples. Ordinary pause permits configuration; preparation,
   canonical lifecycle and principal exit retain their locks.
3. Use explicit accounting6/ProtocolPolicy1/portfolio2/maintenance3/confirmation3/LP2/quality1
   keeper/API configuration, Budget4 and the complete fixed helper graph.
   Match runtime pins and source, preserve pending/nonce/spend truth, and use
   controlled restart for local config/release changes. An on-chain setter alone
   normally needs no host restart. Preflight/health can validate policy during
   cooldown without relying on a bucket price or readiness read.
4. The source checks ordinary physical/reference 85% threshold conditions every
   240 seconds even during the hard12-hour cooldown. Paid ordinary observations
   enroll near `earliestCooldown - duration - maximumGap`: initially 15 minutes
   before eligibility, or immediately if already due. Earlier off-chain checks
   and fault/identity resets continue; no twelve-hour price history is inferred.
   Existing foreign/reset/acknowledged records and pending recovery retain
   priority. A deliberately deferred old window is not deleted; a stale sample
   restarts when an authorized observation is later confirmed.
5. Read helper `condition(bucket)`, `observations(bucket)` and `ready(bucket)` at
   one canonical block. Physical/reference same-side samples must persist for
   the configured duration with no recorded gap above300 seconds. A known maturity
   boundary may cause an earlier read. `needsRebalance` additionally enforces
   cooldown; a candidate during cooldown is not execution permission. Main-loop
   `interval_seconds` must be explicitly60–240; actual latency may still miss
   the strict gap. Qualify inclusion and gas; do not add grace to hide an outage.
6. A deliberate width/mode/active residual-geometry change has its manual sample
   exception after cooldown. Threshold-side diagnostics are unavailable for this
   repair; price/tick, custody and ordinary execution guards remain. Raw side1/2
   are pool-ratio directions: side1 means higher ZZZ-in-ETH price, side2 lower.
7. After readiness, the service saves one OS-random60–300 second delay, excluding
   the preceding chosen delay for that bucket. Continue checks/samples through
   the wait and recheck before submission. Routine top-ups/harvest do not redraw
   it; it is not a promise of forever-unique delays, secrecy or MEV protection.
8. Return inside the threshold, side reversal, changed physical/policy identity,
   stale gaps or relevant observed faults invalidate evidence/jitter. The worker
   persists a clear-only reset and confirms `resetObservation(bucket)` before
   renewal. Startup, observed pause and interrupted recovery preserve these
   requirements. A reverted reset or maintenance transaction cannot persist a
   deletion; recover the same hash and do not repeat an ambiguous action.

Known confirmation renewal/reset deadlines follow pending recovery and precede
optional nonce users. Unrelated job failures remain isolated; global authority,
head or canonical-checkpoint faults invalidate known relevant windows. A canonical
clear acknowledgement prevents repeated paid no-op resets while awaiting a fresh
healthy read. Foreign nonempty evidence requires another clear; only the worker's
own new observation intent removes the acknowledgement atomically with pending
persistence. Never edit a journal, move its nonce or erase a saved intent to pass.

Sampled confirmation does not prove every price, fault or pause between checks.
It adds neither privacy nor profitable-execution guarantees. Hourly harvest,
funded claims and original pending recovery remain independent. To deliberately
stop new market-triggered sampled readiness, configure reviewed gap0. This is
**not a universal rebalance stop**: a deliberate mode/range geometry change has
its own cooldown-gated exception. To stop ordinary execution entirely, use the
appropriate global pause, keeper revocation or pool-operation stop and reconcile
pending transactions. Follow [the policy](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer)
and [keeper coordination](KEEPER_COORDINATION.md); exact operating latency/gas
qualification and matching worker/checker rollout remain open.


### Set additional execution loss

For fresh `EXECUTION_QUALITY_VERSION()==1`, governance calls
`Strategy.setAdditionalLossBps(uint16 limit,bytes32 reviewHash)`. The initial limit
is 100bps (1%) beyond actual directional LP/protocol fees; allowed0-1000bps.
Zero is a strict economic limit, not a disable switch. Use a nonzero review hash.
This is separate from venue gross slippage, total contribution/maintenance loss,
converter policy and caller minimums; the strongest relevant floor always wins.

1. Resolve the sealed Strategy from Access, verify its runtime/Access binding and
   capability, read current limit/MAX/revision and actual directional pool fees.
   Reconcile pending keeper work before changing policy. Qualify fee/depth/price
   assumptions; raising the setting accepts more possible loss.
2. Simulate and call the setter from governance (or valid pre-seal bootstrap).
   Ordinary global pause and post-LP-exit buyback configuration are supported;
   preparation/canonical locks reject. No keeper authorization permits this setter.
3. Confirm `AdditionalLossLimitChanged`, getter and incremented
   `executionQualityRevision`. Reprepare unsigned reviews. Changing and restoring
   policy mid-operation fails its captured fingerprint; later transactions use
   current inclusion-time settings. Reviewed Entry maximum binds the contribution
   cap, not a frozen copy of this quality setting.
4. Fresh keeper/API configurations declare `execution_quality_version:1` with
   reviewed Strategy/Manager/helper runtimes and bindings. Historical absent/0
   profiles stay separate. For an off-chain config/release change, stop/reconcile,
   preserve the journal, verify pins/dry run and restart the actual reviewed
   service; an on-chain setter alone needs no process restart. Never relabel an
   existing immutable deployment or delete pending state to pass a capability check.

No installed service was changed. Direct Manager swaps/buybacks additionally
require a constructible configured target range through the full context check;
near TickMath bounds that can stop execution. Inspect configuration and simulated
failure instead of bypassing prices/floors. Separate LP/royalty converters retain
their own all-in conversion limits. See [fee-adjusted quality](EXECUTION_QUALITY.md)
for exact fee/rounding scope, 2% gross-floor interaction and recovery boundaries.

### Qualify current routing gas and telemetry

The blocked holder-exit keeper example's `max_gas_limit:2500000` is not a qualified
current-maintenance budget. Earlier cold routing fixtures measured balance alone
at 2,590,680 gas (one venue) and 5,963,090 gas (four), before full maintenance and the
keeper's 25% estimate padding. These are historical fixture observations, not
current Robinhood limits or safe launch values. The keeper must refuse work above
its configured ceiling; **never widen caps automatically**. Qualify exact current
catalog/search/depth and complete operations, including network fee accounting,
then deliberately set limits and daily budgets, simulate and dry-run. Reconcile
pending work and preserve the journal before any config/release restart.

Fresh keeper health schema2 separates confirmed execution/quality metadata from
`rebalance_confirmation_health.policy`: a fresh latest canonical policy-only
block/hash/time, config/source/runtime pins, helper/Budget versions and bindings.
Confirmation1 requires this record independently of quality1, even during
cooldown with compounding off. It proves neither sampled readiness nor continuous
history. `stopped` means gap 0; `incompatible_cadence` means a nonzero gap below 240;
`unavailable` retains any old observation explicitly as stale. These states
degrade active-principal health without cancelling independent harvest. After
explicit terminal `lp_exit_started:true`, health treats stop/cadence as
informational; real bindings and freshness remain required. Saved pending work is recovered before
any new policy/quality reads. Metadata failure cannot refresh `last_success_at`
and increments failures. Local source hashes identify files, not the running
binary or provider authenticity. Fresh
healthy_v2/dry_run_v2 statuses require the matching checker; an old checker must
fail closed. Roll out writer/checker together only after authorized operating
qualification, with original journals intact. Discovery/health may reuse reads
only at the identical block hash/config within one cycle; pre-signing validation
stays fresh. Gas refusals report estimate,25%-padded requirement and configured
ceiling/reason, without widening any budget. [Telemetry/recovery](KEEPER_RECOVERY.md)
and [verification](../reports/practical-improvements-20261028/VERIFICATION.md).
No installed service changed.

## Typed conversion and loss-limit operations

[Typed v4 route setup](TYPED_V4_ROUTES.md) covers new pools/routes, exact policy
fields, activation `routing_version: 2`, converter workers and failure/restart.
[Execution-loss controls](EXECUTION_LOSS_POLICY.md) supersede earlier fixed-cap
wording in this manual: default **2% / 1% / 3%**, immediate governance **0-10%**,
network gas separate. Never assume an old default is the current on-chain value.

| Change | Exact current control | Preserve / recover |
| --- | --- | --- |
| Contribution or maintenance limit | Budget `setLossLimits(uint16 contribution,uint16 maintenance)` | Read both current values; preserve the other when changing one. Captured per-operation policy and caller-reviewed maxima never relax automatically. The retired custody-approval floor is not a current control. |
| LP or royalty conversion limit | Respective converter `setConversionLossBps(uint16)` | Each converter is independent. Keep stronger caller minima, fresh independent quotes and exact source/native backing. |
| Add v4 conversion pool | Parent `addV4Route(Policy)` | Static hookless exact-input, pinned manager/StateView/assets, immutable parent output; separate from principal pool admission. |
| Stop/reopen conversion route | Parent `setRouteEnabled(id,bool)` | Stop has no dependency reads. Reopen requires exact dependency validation. Reconcile submitted transactions before replacing worker config. |
| Read current conversion limit | Royalty reporting schema 2 and reviewed converter pin | Reports current cap and hard maximum separately. Legacy schema 1 stays fixed-1%; no missing-getter fallback. |

Verify previous/new events and getters, then regenerate current reviews. An
ordinary pause allows policy changes; preparation/canonical locks and reentry do
not. Caps are per operation, not cumulative. Other venue guards can still be
stricter than 10%; raising a cap does not bypass those guards or guarantee a swap.
The public site remains simulated and signing remains Anvil-only.

## Before every management operation

1. **Identify the deployment:** chain ID, controller, canonical lifecycle, sealed module addresses and code hashes from the reviewed [inventory](DEPLOYMENT_ADDRESSES.md). Read `canonicalState()`, `preparationActive()` and `paused()`. An old retired deployment is not a valid target merely because its explorer page still exists.
2. **Identify the object:** PoPL NFT token ID, mint ordinal, bucket ID, pool ID and physical Uniswap position ID are different. Read `Vault.nftBucket(tokenId)`, `group(bucketId)`, `bucketTotalShares(bucketId)` and the registry. The keeper operates on shared buckets, not 1,000 independent NFTs.
3. **Read before changing:** preserve the complete current struct, asset units/decimals, balances, shares, current parameters and pending work. Use a confirmed block and record its hash. Do not copy example addresses or raw-token thresholds into production.
4. **Prepare exact calldata with the ABI for that release.** Simulate from the actual authorized caller, including value, bounds and dependent operations. Use fresh deadlines and meaningful minimum output/liquidity. If state/configuration changes, simulate again. Simulation does not guarantee later execution or prevent MEV.
5. **Execute through the proper authority**, wait for the configured confirmations/finality, then check receipts, events, getters and economic balances. A submitted hash or successful multisig proposal is not a successful target operation.
6. **Update off-chain configuration and the operation record:** runtime pins, asset/route inventories, API/indexer/keeper configuration, frontend supported actions, review evidence and rollback plan. Never put keys, RPC secrets or runtime state in Git. Record failures and failed-transaction gas too.

### Use an explorer or a smart-wallet transaction builder

After an actual compatible deployment is verified, open its exact address on
the **deployment chain's** explorer, choose Write Contract and connect the
authorized wallet. The source candidate currently has no approved production
address. Obtain targets from the reviewed address inventory/module getters, not
search results or an example. A pool ID is32bytes; it is not a contract address.

For a governance EOA, the EOA submits directly. For a Safe, prepare the target
call in its Transaction Builder so the **Safe** is `msg.sender`; one Safe owner
calling the explorer from a personal account has no inherited authority. A
reviewed batch is possible only when that wallet preserves the authorized
caller for every call. The controller supplies no generic multicall executor.

1. Read the exact deployed versions/runtimes/controller, roles, canonical state,
   pool/bucket and physical IDs at one recorded confirmed block.
2. Use the [named-input catalog](#manual-write-input-catalog) and full ABI. Expand
   tuple fields in their ABI order. Token amounts, USD18, BPS, ticks, IDs and
   timestamps are different units. Keep large integers as decimal strings in
   JSON tooling; JavaScript numbers can silently round wei/USD18/liquidity.
3. Build a fresh review record, then simulate the **complete** intended target
   call from its real authority, with exact value and current state. A prior
   setter/pause may invalidate fingerprints; reread after it. Simulation cannot
   guarantee inclusion, later prices or protection against public ordering.
4. Check transaction value separately: the management setters, residual close,
   park, emergency, move and resume are nonpayable and send0ETH. Gas is separate.
   Funding operations have their own documented value/approval rules; they do
   not grant permission to spend principal.
5. Submit once, retain the hash, reconcile final receipt/state/events, then take
   the documented next or reverse step. An approved wallet proposal is not an
   executed call. Expired/changed requests require fresh inputs, simulation and
   wallet approval; never reuse an ambiguous broadcast as a new operation.

These interfaces do not calculate a ParkingRequest/EmergencyRebalance or choose
safe economic minimums for you. The [offline review helper](#prepare-and-check-an-offline-reviewhash)
supplies provenance and exact input ordering only, not a live transaction planner.

### How governance calls work

After sealing, the wallet returned by `Access.governance()` calls the governed
module **directly**. The module authenticates it through `Access.canConfigure`.
Before seal, that predicate admits **only the bootstrap** while preparation is
inactive; an unrelated governance wallet is not an additional setup authority.
After seal it admits current governance only in operating canonical state and
outside preparation. Read `isSealed()`, `bootstrap()`, `governance()` and
`canConfigure(caller)` rather than assuming two wallet addresses are the same.
Special functions such as propose/accept governance and pause have their own
explicit permissions, as shown in the input catalog.
The controller has `GOVERNANCE_VERSION=2`; it has no scheduling, generic forwarding
executor or Timelock roles. If governance is a Safe, its owner uses the Safe's
transaction flow so the Safe itself is the target caller; that owner's personal
account does not inherit the Safe's authority. A governance EOA calls directly.
Review exact target, value, calldata and wallet nonce, simulate from that wallet,
then verify the finalized receipt and resulting getters. **There is no governance
waiting period.** A wallet proposal is not an executed target call. Cancel or
replace an unexecuted proposal using that wallet's own supported process; do not
retry a confirmed successful call. Lifecycle/preparation guards still apply.

To change the governance wallet, the current wallet calls
`Access.proposeGovernance(candidate)` and the candidate calls
`Access.acceptGovernance()`, with no cooldown. Verify `GovernanceAccepted`, the
new getter and zero `pendingGovernance()`. Proposing zero cancels a pending
handover; the current authority remains until acceptance. Both calls require
operating canonical state and inactive preparation. Keeper/guardian grants and
the separately governed future mint recipient do not change. See [governance semantics](GOVERNANCE.md)
and [controller source](../src/ZZZAccessController.sol).

## Authorities

| Authority | Management action | Rotation/recovery |
| --- | --- | --- |
| Governance wallet | Direct governed configuration, custody changes and replacement admission | Verify `governance()` and the wallet's own signers/threshold. Rotate via `proposeGovernance` then candidate `acceptGovernance`; zero proposal cancels. Changing owners/threshold of the same Safe uses that Safe's own process. No controller-admin recovery exists if governance is lost. |
| Guardian | Direct `AccessController.setPaused(true)` | Governance uses `setGuardian(address,bool)`. A guardian cannot unpause, choose a new pool, withdraw LP or repair lost governance. |
| Keeper | Eligible bounded maintenance; cannot approve or execute discretionary custody exits or same-pair pool moves | Governance uses `setKeeper(address,bool)`. Isolate/revoke a compromised signer, reconcile its pending transactions, then qualify a new signer and state. No salary, gas reimbursement or bounty is automatic. |
| Bootstrap | Initial bindings and sealing | `bind` and `seal` only before sealing; bootstrap is erased. Do not retain deployment keys as a supposed recovery backdoor. |
| Mint recipient | Receives future direct-mint proceeds at the reviewed current price (default0.05 ETH); OpenSea primary integration remains open | Governance proposes through ProtocolPolicy, candidate accepts; zero cancels. Old payments and protocol rights never move. |

Roles can technically share an address, but this combines their compromise and availability risks. Immediate governance can approve unsafe dependencies or harmful replacement code; role separation and independent transaction review are operational defenses, not an on-chain delay. If every required governance authority/key is lost, there is no hidden admin recovery. Preserve reviewed multisig recovery arrangements before launch.

<a id="deep-cleanup-review---2026-10-25"></a>

Monitor `GuardianChanged` and `KeeperChanged` from the controller's deployment
receipt, including initial grants, then reconcile their stored mappings with
canonical complete history. Older controllers without initial events require
constructor/call evidence. These events add visibility, not authority.


## Range and strategy

**You can change the supported strategy's parameters after sealing**, without replacing contracts. You cannot replace the algorithm itself by updating a number.

### Example: change the width

`rangeBps` is the approximate half-width around the independent oracle reference, with outward tick rounding. Its units follow explicit Strategy orientation: mode0 raw token1/token0 (historical); mode1 token0/token1 (ETH per ZZZ here). Read the configured mode, not the token label alone. It is not half the capital or an unchecked spot-centered range.

| Intended interval at reference price P | `rangeBps` | Example at P = 1 |
| --- | --- | --- |
| +/-50% | `5000` | 0.50 to 1.50 |
| +/-25% | `2500` | 0.75 to 1.25 |
| +/-20% | `2000` | 0.80 to 1.20 |
| Total width 20%, meaning +/-10% | `1000` | 0.90 to 1.10 |

1. Read `PoolRegistry.get(poolId)` and copy the **entire** `PoolConfig`, including its real venue key. Change only intended settings. Use `configureNative(config)` for supported native ETH/fixedZZZ fee tiers; generic ERC20 LP admission is removed. Current accounting6 retains the real zero ETH currency; do not substitute WETH or change slot ordering.
2. Check the dependent bounds below, oracle freshness, current price/spot difference, target ticks, actual swap costs and expected gas. Review narrower-range out-of-range exposure and turnover. Simulate the new configuration and maintenance on a fork at the same state before approval.
3. Governance executes the configuration. This **does not immediately close/reopen LP**. Inspect `Strategy.rangeUpdatePending(bucketId)` and `needsRebalance(bucketId)`.
4. The authorized keeper submits `Vault.rebalance(bucketId,minimumLiquidity,deadline)` when cooldown and guards permit. A width mismatch can trigger it even at a flat price. Fresh confirmation3 uses 240-second condition checks; historical ten-minute polling is not its operating schedule or a guaranteed rebalance deadline.
5. Verify the new physical LP ID/ticks/center, retained value, attributed idle, unchanged NFT shares and continued claims. A successful replacement clears the width mismatch. A revert preserves the old position and leaves the desired change pending.

Before execution, restoring the actual main's old width may clear that width
mismatch, only if no portfolio geometry revision remains pending. An ordinary
85% threshold candidate may still qualify after its sampled window and cooldown.
Mode/active geometry revisions are monotonic: changing and restoring the mode
does not cancel their pending replacement. After execution, reverting the width
requires another valid configuration/replacement, with new costs and cooldown.
Stop/reconcile in-flight keeper work around changes: a transaction is not bound
to an earlier off-chain review hash. See [range application](RANGE_POLICY_UPDATES.md).

The fresh [optional portfolio source](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md)
implements a main plus at most one residual. Scoped local actual-core integration
passes; live production qualification remains open. Historical deployments keep their own behavior;
never set legacy `triggerBps` to 8500 or use emergency as a routine substitute.

### Operator-selected LP policy

Fresh Strategy maintenance3, PortfolioPolicy1, Confirmation3 and Budget compound4
implement the [current source policy](LP_EXECUTION_POLICY.md). Choose main width
manually; disable on-chain automatic policies and local `adaptive_range.enabled`.
For the intended initial settings, use orientation1, `rangeBps=2500` or `5000`,
`minRebalanceInterval=43200` and
`maxPositionUSD=1000000000000000000000000` ($1m cumulative contributions per NFT,
USD18). Review/copy the entire actual native PoolConfig and preserve other guards.
These values are intended configuration, not an installed release or depth proof.

Ordinary market adjustment begins at 85% of actual centre-to-main-boundary
ZZZ-in-ETH price distance on the same physical/reference side, with the sampled
window and hard cooldown. A deliberate width/mode/active geometry request may
apply after cooldown while the old main is still active. `triggerBps` is a retained
legacy field, not this threshold or a 1% centring tolerance. Contributions keep the
actual main/residual portfolio and do not recenter it or reset the clock.

The source keeps four-minute condition checks during cooldown, enrolling paid
ordinary samples only near `earliestCooldown-duration-maximumGap` (initially the
last 15 minutes). Once ready, it saves one 60–300 second jitter while continuing
samples. A failed/ambiguous operation retains normal recovery/backoff; downtime
never replays missed rebalances. [Configure observations](#configure-rebalance-confirmation).

On-chain settings are read fresh and normally need no host restart/reseal.
Lowering a cooldown can make existing custody due sooner; it does not reset its
clock. Local source/config/version/runtime changes need a controlled matching
restart with original journal/pending/nonce/spend state preserved. Never relabel
an accounting4 service or deployment as profile6. Publication does not perform
an operating rollout or change the existing Anvil chain.

### Optional main and residual mode

Resolve `Strategy.portfolioPolicy()` and verify the exact policy/runtime/Access
binding, its Strategy parent, `PORTFOLIO_VERSION()==2`, trigger/revisions and the
actual `Manager.secondaryId(main)`. `ZZZLPPositionExecutor` is a fixed typed
contract child, not another human operator or a general executor. Validate its
immutable Manager/core/state/PosM/Permit2/router graph and the Balancer math child.

| Governance call on PortfolioPolicy | Inputs and result |
| --- | --- |
| `setMode(bytes32 pool,bool enabled,bytes32 reviewed)` | Reviewed admitted native ETH/fixed-ZZZ pool; true requests main+optional residual, false requests single main. Nonzero review hash. Updates desired mode and geometry/global revisions, emits `PortfolioModeConfigured`; does not move funds. Same-value mode requests revert. |
| `setTriggerBps(uint16 next,bytes32 reviewed)` |1–10000, initial 8500. Percentage of actual centre-to-edge ZZZ-in-ETH price distance. Emits `PortfolioTriggerConfigured`, advances global revision and invalidates samples/reviews; it does not create a manual geometry exception. |
| `configureResidualSide(bytes32 pool,uint16 next,bytes32 reviewed)` |1–10000, default 5000 uses half the corresponding main side in price distance;10000 remains the reviewed full-side option. With main50–150 around100, ideal residual75–100 or100–125 before spot gap/rounding. Emits `ResidualSideConfigured`; geometry advances when mode is enabled, global revision always advances. An unused setting while mode is off does not force a single-mode trade. |

1. Inspect current main and residual IDs/owners/ticks/liquidity/amounts, complete
   NAV, fees/reserves, desired mode and `geometryRevision(pool)`/
   `appliedRevision(main)`. Simulate the exact setter from governance and record
   the nonzero evidence commitment. No principal is sent to the policy helper.
2. Verify getter/event/revision, then `configurationPending(bucket)` and the
   aggregate `Strategy.rangeUpdatePending(bucket)`. A deliberate geometry change
   awaits the hard cooldown and guarded `Vault.rebalance`; it is not immediate.
3. In hybrid mode that operation closes the old one/two legs and rebuilds a main
   plus at most one useful one-sided residual. It seeks only the swap needed to
   meet the main floor among bounded reviewed samples. At the final captured
   price vector, actual main must meet minimumMainBps(pool), default60%, and the residual
   stays below its complementary ceiling, including attributed idle in the denominator.
   Governance can raise that main floor to9999bps; use single mode for100%.
   The captured maintenance idle cap (default5%) and loss guards remain separate.
   No residual allocation or continuous60/40ratio is promised.
4. The residual starts beyond spot by at least residualGapSpacings(pool) full tick-spacings on its main side;
   rounded geometry, useful size and actual inventory may leave no residual.
   It can later fill, unfill or become mixed. It remains accounted until the next
   whole adjustment; no unbounded additional positions are created.
5. Disabling mode leaves every live residual valued and harvested until a safe
   atomic merge succeeds after cooldown, or governance performs the separate
   [residual-only close](#close-only-the-second-position). Failure leaves old
   custody/rights intact. Do not hide an auxiliary ID in configuration.
   Mode/active geometry revisions are monotonic: flip-and-restore does not cancel
   pending replacement even if visible values match again. A pure width restored
   to matching ticks can cancel only its own mismatch, not a pending portfolio revision.
6. Confirm the successful operation's actual one/two Vault-owned IDs, applied
   revision, token amounts, unchanged NFT shares/rewards, retained backing, idle
   and new clock. On-chain settings need no service restart; matching fresh local
   source/config needs controlled rollout. Preserve submitted transaction truth.

`portfolioAmounts(main)` is the sum of actual token amounts; never add raw
liquidity across ranges. Stable `portfolioFingerprint` excludes liquidity so
normal contributions do not reset samples. Custody reviews use the separate
liquidity-sensitive `executionPortfolioFingerprint`. Parking/move/holder return
must close both legs; canonical export requires no live residual. [Profile](POSITION_V6.md),
[range guide](RANGE_POLICY_UPDATES.md), [current source qualification](../reports/optional-portfolio-20261030/VERIFICATION.md).

Every ordinary replacement, including single mode, checks that the new main
is physically active before and after mint/refund callbacks. Narrow inverse-price
bands and admitted reference deviation can otherwise create an inactive main
despite good USD retention. A rejection rolls back both legs. Simulate the exact
configuration and candidate; review width/venue/reference validity rather than
automatically widening loss caps. The explicit paused-governance emergency is a
separate manual procedure, never a keeper fallback. Initial/growth outside-range
policy is unchanged. [Audit and remaining route-ranking limit](../reports/day-audit-20261031/REVIEW.md).

### Portfolio management controls

This is the single operator procedure for the main and optional residual.
Both physical positions use the **same ETH/ZZZ pool** and remain Vault-owned,
attributed to the same NFT shares. A single concentrated position uses the
ratio required by its current price and ticks, **not necessarily50/50 USD**.
The hybrid60/40 limits describe allocation between positions at replacement,
not the token ratio or a continuously maintained allocation.

The [configuration section above](#optional-main-and-residual-mode) owns exact
PortfolioPolicy inputs, geometry and revision semantics. Inspect both actual
positions and desired settings before choosing an operation below. A matching
accounting label does not add a new write capability to historical deployments.

| Intent | Wallet and exact function | Effect |
| --- | --- | --- |
| Allow a residual | Governance → `PortfolioPolicy.setMode(pool,true,reviewHash)`. | Enables future guarded whole adjustment; creates no LP immediately and does not force a40%residual. |
| Stop future residual creation | Governance → `PortfolioPolicy.setMode(pool,false,reviewHash)`. | Immediately changes desired policy. Existing residual remains accounted until explicitly closed or consolidated. |
| Close only the residual now | Pause; governance → `Migration.closeResidual(ParkingRequest)`. | Harvests both legs, burns only the registered residual and attributes its actual ETH/ZZZ to the same bucket's idle. Main ID/ticks/liquidity/centre/clock and NFT shares remain unchanged. No swap or external payout. |
| Consolidate through ordinary upkeep | Set desired modefalse; a keeper-granted wallet → `Vault.rebalance(bucket,minimumLiquidity,deadline)` when ready. | Closes both, balances inventory and opens one main. Retains cooldown, price, execution and liquidity guards. A governance wallet needs a keeper grant for this ordinary function. |
| Consolidate urgently before cooldown | Pause; governance → `Migration.emergencyRebalance(request)`. | Always closes the whole current portfolio and creates one explicit emergency main. Select retained checks in the reviewed manifest. Does not automatically change desired mode. |
| Stay single after emergency consolidation | Governance sets modefalse **before** preparing/signing the emergency review. | Prevents a later ordinary adjustment from creating another residual. |
| Re-enable after closing it | Governance sets modetrue; use the next eligible guarded whole adjustment. | Existing unused principal remains included; a new residual can be created with actual inventory and approved geometry. |
| Reapply geometry when mode is already enabled | Governance → `configureResidualSide(pool,currentSideBps,reviewHash)`. | Same-value width review intentionally advances enabled geometry so the next guarded whole adjustment after cooldown can rebuild it. No artificial mode toggle or cooldown bypass. |
| Stop all LP without a swap | Governance → paused [parking](CUSTODY_PARKING.md). | Closes both legs into Vault-attributed idle. Resume requires separate guarded deployment. |
| Permanently end LP and return principal | Governance → [collective holder exit](HOLDER_COLLECTIVE_EXIT.md). | Irreversible; closes both legs and returns actual ETH/ZZZ to NFT holders, while old rewards, future royalties and transfers remain. |

Every governance write requires a fresh nonzero review commitment where specified.
Governance is the user's authority, not the automated keeper. The sending wallet
or Safe execution pays network gas; principal does not pay an operator bounty.

#### Close only the second position

Use this when its inventory/range is no longer wanted but the main should remain
untouched. A residual that has filled or become mixed is still closable: the
receipt may include **both** ETH and ZZZ. Its historical one-sided label does not
restrict the returned assets.

1. Reconcile existing pending keeper/manual transactions and stop conflicting
   scheduling through the authorized operating procedure. A host stop or pause
   does not cancel a transaction already broadcast. Preserve journals and recover
   the same transaction hash rather than submitting a duplicate.
2. Governance calls `Access.setPaused(true)`. Verify sealed/current canonical
   operation, no preparation/import/retirement and no terminal LP exit. Claims and
   transfers retain their own existing permissions.
3. Read `PortfolioPolicy.enabled(pool)`. If it is true and the desired long-term
   policy is one position, call `PortfolioPolicy.setMode(pool,false,reviewHash)`
   first. The setter is available while paused; do not repeat it when the value
   is already false because same-value mode requests revert. If left enabled,
   closing the residual does **not** disable its future recreation at a later
   eligible whole adjustment.
4. Check `RESIDUAL_EXIT_VERSION()==1` on the exact reviewed Migration, Vault,
   Manager and typed position executor. Verify their code hashes, reciprocal
   bindings and the actual nonzero residual ID. A matching accounting version
   alone does not prove this new write is supported.
5. Prepare the same typed `Migration.ParkingRequest` shape used by raw parking:

| Field | Reviewed input |
| --- | --- |
| `bucketId`, `poolId`, `lpTokenId` | Exact current shared bucket, same ETH/ZZZ pool and actual main LP ID; not the individual NFT ID or residual ID. |
| `totalShares`, `depositUSD` | Exact current bucket shares and recorded contribution value. These are identity checks, not a request to rewrite either. |
| `custodyEpoch`, `nonce` | Current `Migration.custodyEpoch(bucket)` and shared `parkingNonce(bucket)`. |
| `token0`, `token1` | Native ETH zero address and the deployment's fixed ZZZ, matching the actual admitted ordered pair. |
| `minimum0`, `minimum1` | Raw minimum principal receipts from closing **only the residual**, excluding existing idle and harvested fees. ETH uses wei; ZZZ uses its reviewed decimals. At least one minimum must be positive; a genuinely absent side can be zero. |
| `deadline` | Unix seconds; inclusion must satisfy `now <= deadline <= now+600`. |
| `reviewHash` | Nonzero hash of the reviewed exact operation and supporting evidence. A hash records review intent, not review quality. |
| `portfolioHash` | Current `Manager.executionPortfolioFingerprint(main)`, including both physical IDs/ticks/liquidity. |

6. Simulate the exact governance sender and full Migration call at fresh confirmed
   state. Check both-leg fee collection, exact residual burn, raw minimums,
   main preservation and reserve backing. The transaction is nonpayable; no ETH
   contribution or approval is required. Use the real post-close receipt
   estimates, not total portfolio value, for `minimum0/1`.
7. Governance calls `Migration.closeResidual(request)` once. No keeper grant is
   required, no address can be chosen to receive principal and no swap occurs.
   A failed harvest, token call, burn, minimum or postcondition reverts the whole
   transaction, including fee allocation and nonce/association updates. Gas remains
   spent on a reverted transaction.
8. Confirm the successful canonical receipt and `ResidualClosed` event. Verify:
   residual association0 and burned old auxiliary ID; unchanged main owner/key/
   ticks/liquidity, centre, rebalance clock, shares and deposit; exact attributed
   idle increases; no reserve or unclaimed-reward diversion; incremented shared
   parking nonce and custody epoch. The protocol stays paused until separately
   reviewed unpause. Refresh policy/sample evidence and reconcile service state.

No healthy USD feed or swap route is required for this raw close. Operations can
be disabled for the pool while accounting/withdrawal remains readable. Fee
ledgers, the underlying pool, token transfers and raw receipt checks must still
work. A permanently broken token or venue can block it; this is not a universal
rescue or permission to bypass custody.

Market movement can change the residual's token mix without changing its LP
identity. A raw minimum for a side that has since fully converted can therefore
reject the request. Re-read and simulate the actual mix; never substitute guessed
zero minimums simply to get an old request through.

#### Returned idle and restarting deployment

The returned principal becomes **attributed idle**, still owned economically by
the same NFT shares. It is neither claimable reward nor a payout to governance.
The main continues to be the only physical position; its principal is not reopened
or recentered by the residual-only close.

A large idle balance is intentional recovery state. Ordinary activation/growth
still enforce their actual marginal deployment and total-idle guards; new users
cannot subsidize recovery. They may be blocked until existing funds are deployed.
Do not disable those checks or sweep the idle to an arbitrary wallet.

To reinvest, use a complete guarded adjustment, the separately eligible compound
path, or a reviewed paused emergency. Compounding still waits for a healthy,
in-range main below the adjustment threshold with no pending geometry. A pending
mode/width change, cooldown or price disagreement can require ordinary waiting
or the explicit emergency procedure. Raw close does not reset the rebalance clock
or silently mark a pending desired configuration applied.

Fresh confirmation/jitter must reflect the changed physical association. A new
residual must never inherit a previous position's readiness. Existing claim,
royalty and direct holder-return accounting continue independently.

#### Forced consolidation and exceptional markets

The existing [emergency procedure](EMERGENCY_REBALANCE.md) accepts explicit ticks,
one reviewed swap venue/input/output floor, minimum deployed liquidity, custody
hash, deadline, review hash and retained-check mask. It always creates **one**
position, even if optional mode remains enabled.

For timing-only override, retaining bits `2+4+8` preserves fresh independent prices,
financial floors and venue-operation checks while bypassing ordinary trigger/
cooldown/sample requirements. The exact manifest must be simulated; this is an
example selection, not a blanket recommendation. Some financial checks depend
on healthy prices even if another price bit is disabled.

Evaluate required inventory at the actual target ticks/current price and swap
against liquidity remaining after withdrawing our LP. Literal50/50 USD may leave
unused capital and does not prove correct concentrated-LP placement. Read the
actual post-execution range, liquidity, deployment and accounted idle.

Disabling financial guards can lose nearly all principal. A timer override cannot
manufacture initialized liquidity, repair a broken token or authorize an unsupported
venue. Emergency uses its separately reviewed exact swap manifest; its admitted
`swapPool` is not selected from the ordinary Balancer list, which may be empty.
If a safe swap is unavailable, raw residual close or full parking can preserve
attributed inventory without forcing a bad trade. They cannot guarantee USD value
or future fee income.

#### Repeated management, stale reviews and future changes

- A successful residual close consumes the shared parking nonce and increments
  custody epoch. An old raw parking/residual request cannot be replayed. Governance
  may call `invalidateParking(bucket)` to invalidate unsigned requests using that
  shared nonce; despite its historical name, it also invalidates residual reviews.
- A main top-up, portfolio change or other physical/custody mutation can invalidate
  the exact request. Prepare and simulate again rather than updating hash fields
  blindly. Submitted-transaction recovery remains tied to the original hash.
- Setting mode off and back on is a new reviewed geometry revision; it does not
  erase pending work or act as a cancellation shortcut. Mode changes may be
  configured after sealing; new algorithms require reviewed replacement contracts.
- If mode is already on but the residual was closed, a same-value
  `configureResidualSide` review can explicitly request reapplication. The setter
  permits it and increments enabled geometry, unlike same-value `setMode`, which
  rejects. The next whole adjustment still respects cooldown and financial guards.
- Existing mixed/fully converted residuals remain in NAV and fee collection until
  actually burned. At most one residual exists; whole adjustments close prior
  legs before creating a replacement pair.
- Before changing residual width, simulate `PortfolioPolicy.residualRange` with
  the actual proposed ticks/price and excess side. Tick rounding and the full
  spacing gap can make a narrow configured width unmintable. Configuration
  acceptance is not execution readiness; review a feasible width or disable
  optional mode rather than removing the geometry guard.
- Changing pool or fee tier uses [same-pair movement](GOVERNED_CUSTODY_HANDOFF.md),
  including both legs. Destination desired policy is separately reviewed; do not
  assume source mode or geometry automatically applies to another pool.
- Never use canonical import/write entrypoints, raw token transfers, a generic
  executor or an invented custody recipient as a residual recovery shortcut.
  Terminal holder exit cannot be undone or followed by reopening LP.
- On-chain setting changes do not require a keeper restart by themselves; source,
  runtime/configuration and journal-profile changes require the reviewed stop,
  reconcile, dry-run and controlled rollout. No operating rollout is performed
  by editing these guides.

Actual route/feed/token/gas/host qualification and independent audit remain open.
Current local tests establish their recorded source scope, not uninterrupted
operation, manipulation immunity, maximum-holder gas or production approval.
See the [residual-operation verification](../reports/residual-operations-20261031/VERIFICATION.md)
for actual executed cases and exact source boundaries.

### Independent-reference and manual emergency controls

Confirmation3 normally requires our LP pool and the configured independent
reference to cross the same 85% price-distance threshold on the same side.
Target-only, reference-only and opposite-side conditions cannot authorize ordinary
adjustment. Read `marketSides`, `condition` and `ready` at one canonical block;
a failed read is unavailable, never a zero or a force instruction. Raw side1
means higher ZZZ-in-ETH price; side2 lower. Manual geometry repair deliberately
reports threshold sides unavailable while retaining price/tick checks.

Governance may call helper `setRequireReferenceExit(bool required,bytes32 reviewed)`
with a nonzero review commitment. Verify event/revision and expect old samples to
restart. Default true requires every automatic keeper-width policy disabled;
manual governance widths/modes retain their post-cooldown exception. On-chain
setters normally need no host restart; new runtime/capability profiles require a
fresh reviewed deployment/configuration, not relabeled old journals.

For an actual emergency, use [manual paused recovery](EMERGENCY_REBALANCE.md):
governance calls Migration `emergencyRebalance(request)` with capability2 and a
fresh custody hash binding both physical legs and liquidity. The five-bit mask
explicitly retains or bypasses timing, prices, financial floors, operation flags
and sampled confirmation. This is never a keeper fallback. It closes both old
legs and mints one emergency target, without independently creating a residual.
No principal goes to governance; financial bypass can still destroy nearly all
value. Simulate the whole operation, reconcile pending hashes and verify cleared
emergency state before separately authorized unpause/service restart.

### Manual rebalance at a chosen time

A keeper-authorized wallet can call the existing nonpayable function:

`Vault.rebalance(bucketId,minimumLiquidity,deadline)`

This is the same guarded LP replacement as automated upkeep. It bypasses only
Python's evaluation schedule and random waiting; it cannot bypass sampled
confirmation3, hard on-chain cooldown, 85%-threshold/operator-geometry eligibility, pause/lifecycle, prices or
execution/minimum/backing checks. Submission time is your choice; inclusion at
an exact second is not guaranteed. No contract self-schedules a future call.

| Input or caller | Required value |
| --- | --- |
| Caller | `Access.keeperAuthorized(wallet)` must be true. Governance status alone is insufficient. Governance may call `Access.setKeeper(wallet,true)` first. This grants the existing general keeper capability, not just one rebalance; revoke a temporary grant only after its work is reconciled. No new human role or mandatory new wallet is implied. |
| `bucketId` | Read the real `Vault.poolBucket(poolId)` and `Vault.group(bucketId)`. It identifies the shared physical LP, not an individual NFT or its physical LP NFT ID. One call handles that bucket's NFT shares. Zero/missing/inactive custody is not eligible. |
| `minimumLiquidity` | Positive raw Uniswap liquidity units, with a meaningful minimum derived from a fresh complete simulation. It is neither token units nor USD; do not copy the fixture value1 as production protection. |
| `deadline` | Unix seconds; at execution `block.timestamp <= deadline <= block.timestamp+600`. Use a short fresh expiry, not a calendar schedule. |
| Native transaction value | Zero: `rebalance` is nonpayable. The external transaction submitter funds network gas separately; wallet/Safe execution follows that wallet's normal gas workflow. |

1. Verify exact chain/deployment/ABI/runtimes, selected pool, active LP/ticks,
   current interval, raw `Strategy.needsRebalance(bucketId)` and final
   `Strategy.rebalanceReady(bucketId)`. For ordinary confirmation3, authorized
   receipt-backed `observe(bucketId)` calls must establish the reviewed window
   first; a raw true alone is insufficient. See the confirmation procedure.
   A failed price/read
   is unavailable, not false or permission to force execution. Initial12 hours is
   the intended governed hard interval, not an immutable override of every config.
2. Coordinate the automated signer and reconcile any pending hash before manual
   submission. Use the controlled service stop/recovery procedure if needed;
   **do not globally pause to make this call**, because rebalance requires live,
   unpaused operation. A broadcast transaction is not cancelled by stopping a host.
3. Prefer an already available operator/governance wallet with its own reviewed
   keeper grant when keeping the service signer's nonce lane separate. Do not
   import the governance key into the keeper host. If the manual transaction uses
   the automated keeper's same address outside its journal, its saved nonce/spend/
   receipt checkpoint will become stale: restart alone cannot adopt that call.
   Stop signing and use reviewed reconciliation before resuming; never patch a
   nonce or delete state to silence the error. No automatic out-of-band importer
   is promised. [Nonce recovery](KEEPER_RECOVERY.md#deployment-and-journal-identity).
4. Simulate exact caller/target/value/calldata against fresh confirmed state and
   review output LP, loss/idle minima, fees and separate gas. Then sign once from
   the authorized wallet. The contract rechecks its guards at execution.
5. Verify the canonical successful receipt, `Rebalanced`, actual new LP ID/ticks,
   updated `lastRebalance`, retained backing and unchanged NFT shares/earned rights.
   Failure reverts LP/accounting changes but spends gas. An unresolved result is
   recovery of the same hash, not permission to submit another call.
6. Before resuming automated work, reconcile any original pending intent and
   same-key nonce/spend changes. With a separate manual signer, normal rediscovery
   recognizes the new physical LP/clock and invalidates only its obsolete jitter
   record. That timer update is not same-key nonce reconciliation. Resume through
   the matching configuration/health procedure; no journal reset or reseal.

[Current LP policy](LP_EXECUTION_POLICY.md), [range application](RANGE_POLICY_UPDATES.md),
[callable function](CONTRACT_FUNCTIONS.md#zzzvault), [service recovery](KEEPER_RECOVERY.md).
This procedure submits nothing by itself; current source is undeployed.

### Editable pool parameters and coupled limits

| Field | Current contract boundary | Practical meaning |
| --- | --- | --- |
| `rangeBps` | 100-9999, also greater than trigger and spot tolerance | Because `triggerBps >= 100` and must be smaller, 100 itself cannot form a valid complete configuration. Wider/narrower ranges still require representable ticks. |
| `triggerBps` | At least 100 and less than range | Retained ABI/config field; historical policy1 movement trigger. Fresh policy3 uses PortfolioPolicy.thresholdBps and explicit geometry, never this legacy movement field. |
| `minRebalanceInterval` | 600 seconds-7 days | Minimum time between rebalances; a safety cooldown, not a governance delay. |
| `maxSpotDeviationBps` | 1-500 and less than range | Spot/reference discrepancy permitted by guarded execution. Do not widen it simply to accept a manipulated market. |
| `maxSlippageBps` | 1-1000 in fresh LP routing2; pool fee must be strictly below it in equivalent units | Operating values are not raised automatically. Selected LP fee10020 pips requires at least 101bps before other costs. Routing uses the tighter target/venue guard, plus actual protocol fee, impact, captured loss and caller floors. Historical profiles retain their original ceiling. |
| `minDepositUSD`, `maxPositionUSD` | Positive minimum; maximum at least minimum | Minimum for each contribution and maximum cumulative gross contribution per NFT, in 18-decimal USD units; not a live market-value ceiling or total pool cap. Lowering them cannot remove the current helper action floors(default$100 activation/$5 growth). The effective minimum is the larger of the action floor and configured minimum. Check existing NFT contributions/top-ups. |
| `depositsEnabled`, `operationsEnabled` | Full `configureNative` for enabling; `disablePool` can only clear flags | Different controls; see below. |

Read Budget `maintenanceLossBps()` as `L` before ordinary rebalance or supported
local move/resume. Its captured floor is `V - floor(V * L / 10000)`, equal to
`ceil(V * (10000 - L) / 10000)`, for starting principal plus released compound
`V` at one starting price vector. Retained LP plus attributed idle must meet that
floor; idle has its separate 5% ceiling. The default `L=300` means 97% retention,
not an immutable percentage. Contributions similarly capture
`contributionLossBps()` as `C`: both net added backing and marginal deployed LP,
valued at lower source bounds, must reach
`U - floor(U * C / 10000)` for upper-bound original input value `U`. The default
`C=200` means 98%; stronger venue/caller guards remain. Network gas is separate.
The user retained **per-operation limits only**: repeated permitted operations
can accumulate losses. Monitor turnover/costs and stop harmful activity; no
rolling loss breaker or guarantee against impermanent loss exists.

### PoolConfig form for Write Contract

`PoolRegistry.configureNative(config)` takes **one complete tuple**, not only the
changed value. Read `PoolRegistry.get(poolId)`, preserve all unrelated settings,
then change only reviewed fields. The exact field order is:

| Ordered field | ABI type | Input/source |
| --- | --- | --- |
| `key.currency0` | address | Native ETH: zero address. |
| `key.currency1` | address | This deployment's fixed ZZZ. |
| `key.fee` | uint24 | Actual initialized static LP fee in pips;1%=10000pips. |
| `key.tickSpacing` | int24 | Actual positive spacing of that initialized key. |
| `key.hooks` | address | Zero; custom hooks are unsupported. |
| `depositsEnabled` | bool | Whether this is the sole selected contribution pool; enabling another while one is selected reverts. |
| `operationsEnabled` | bool | Approved normal deployment/swap/maintenance capability; not a switch for external Uniswap trades or every raw recovery path. |
| `rangeBps` | uint16 | Main half-width;2500=±25%,5000=±50%, subject to the coupled bounds above. |
| `triggerBps` | uint16 | Preserve the valid legacy compatibility field; it is not the fresh85% threshold. |
| `maxSpotDeviationBps` | uint16 | Reviewed spot/reference allowance; independent from USD-source agreement. |
| `maxSlippageBps` | uint16 | Venue execution allowance, within hard bounds and stronger operation/caller floors. |
| `minRebalanceInterval` | uint32 | Seconds; initial43200. Changing it does not reset lastRebalance. |
| `minDepositUSD` | uint256 | Positive USD18 contribution minimum; may strengthen the current ProtocolPolicy activation/growth floors (default100/5USD). |
| `maxPositionUSD` | uint256 | Maximum cumulative contributed USD18 per NFT, not current NAV/collection total; intended1mUSD=10^24. |

The first five fields form the nested `key` tuple, followed by the nine remaining
fields. Changing a key field selects a different pool ID; it cannot edit the
existing pool's fee or spacing. Admit/qualify the new key and follow the reservation
and move sequence. Narrowing a width may require lowering its dependent trigger/
spot limits in the **same full config**. Restoring a previous config is a new
governance transaction and does not undo already executed swaps or range costs.

### Contribution minimums

For normal $5 increases, governance configures `minDepositUSD=5e18` through the
appropriate full `configureNative` call. After terminal exit, reserve-venue configuration requires Ready and deposits
disabled; activation/growth remain permanently stopped. Activation still requires
$100; each action must meet the captured contribution-loss floor above (98% at
the default 200 bps), gas separate. No per-user
override or new role exists. A higher pool minimum intentionally blocks smaller
increases. Follow [the exact procedure](CONTRIBUTION_MINIMUMS.md#operator-procedure)
for authority, simulation, verified getters/receipts, dependency-free stop,
validated restart and rollback. The floors are implementation changes, not a way
to modify sealed deployed bytecode. This candidate is undeployed publicly.

Local launcher source now uses the $5 pool minimum. Existing running fixtures
remain unchanged: build source-matched artifacts and launch a separate fresh
disposable session; do not silently erase holdings or reuse stale ABI/runtime pins.
Optional history failures now retain core confirmed balances with unavailable
history and a sanitized `local_earnings_unavailable` event. Inspect indexer/RPC
coverage before retrying a refresh; work-budget failures are terminal, core reads
still fail closed and refresh never repeats financial operations. Dormant NFTs
skip irrelevant history replay. See [local setup](LOCAL_TEST_STACK.md).

### Read-only selected-pool evidence

Use `scripts/verify-hookless-pool.py --block <confirmed-number> --expected-hash <reviewed-hash> --output <report.json>` with a reviewed RPC. It uses bounded read-only batches, EIP-1898 canonical-hash state selectors and reviewed dependency runtime pins. An incompatible provider fails; there is no latest-block or number-tag fallback. A failed observation/output replacement preserves the previous complete report, which remains old evidence and must not be mistaken for a fresh success. Check exit status and observation block/time. The report never authorizes deployment or financial actions and does not prove immutable proxy administrators, safe feeds or adequate liquidity. See [audit scope](../reports/daily-security-20261024/REVIEW.md).

## Activation assets and routes

An **activation route** converts a user's contribution into the LP pair. It is distinct from moving the Vault's already-held LP to another pool. Changing an ETH/ZZZ source conversion route does not migrate attached LP or change its owners.

### Add or re-enable an input token

1. Only ETH and the reviewed ZZZ identity are contribution inputs. Do not add USDC, USDG or WETH as user sources. Marketplace royalty currencies are a separate policy.
2. Bind the initial ZZZ identity once before sealing using `ActivationAssets.configureZZZ(token,codeHash,reviewHash)` after reviewing its exact runtime, decimals, transfer behavior and two independent USD sources. The deployed identity cannot be replaced. An issuer migration uses custody exit and a fresh deployment; old ownership/reward records are not erased.
3. To stop either input, append its disabled `setAsset` policy; this stop requires no healthy token/feed. Re-enabling requires full review/validation. The helper cannot enable a third contribution currency.
4. Current principal destinations remain native ETH/fixedZZZ only. A new execution venue does not admit another input or target pair. Pin its exact venue/code/prices, simulate the complete direct/native operation and verify captured contribution floors before admission. Optional royalty conversions have their separate routes and permissions. Pool/route reconfiguration does not reopen a disabled source.

Current native accounting uses explicitly admitted ETH at `address(0)`, with an independent feed and exact call value. It is never an ERC20 approval target. Accepting a new **input** does not automatically admit an LP or royalty payout currency. Only native ETH and the explicitly reviewed ZZZ identity may be user inputs. Actual ETH/ZZZ routes and services remain subject to [qualification](ACTIVATION_PREPARATION.md).

### Replace a swap route when market liquidity moves

Read/review the new route, append it with `addRoute`, qualify it, switch the backend's selected route, and use `setRouteEnabled(oldId,false)` to stop the old route. Route contents/identities are immutable; do not overwrite one in a manifest under the old hash. There is no time delay. Concurrent user quotes may revert after disablement and must be rebuilt. Already mined operations cannot be undone.

To stop an input immediately, use `ActivationAssets.setAsset(token,false,expectedCodeHash,reviewHash)` with the exact ETH-zero or fixed-ZZZ token and nonzero review hash, and disable affected Entry routes. Disable paths deliberately avoid dependency calls needed for enabling; they can help when a token/feed is broken. Previously attached LP, shares and claims are not erased. Re-enabling requires valid current token/feed/code checks and new quotes. Pool configuration cannot silently re-enable an explicitly disabled source. See [Entry and source policy](ACTIVATION_ENTRY.md) and [routing](ACTIVATION_ROUTING.md).

## Pool admission and retirement

For a supported new LP venue, first qualify tokens, feeds, reward-asset admission (`Rewards.addAsset(token)`), the exact venue key/manager and strategy. Then governance calls `configureNative`; the removed generic pool `configure` entrypoint is unavailable. Not every Uniswap v4 hook/native pair is supported. Native admission permits only supported static, hookless ETH/ZZZ keys on the pinned Robinhood dependencies; immutable bindings are not arbitrary venue plug-ins.

### One contribution pool at a time

`PoolRegistry.contributionPool()` is the only pool whose `depositsEnabled` flag
can be true; zero means new activations/top-ups are stopped. Initial production
configuration must select the reviewed Robinhood hookless native ETH/ZZZ pool
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`.
Selection may change among compatible fee tiers; it cannot change this
deployment's fixed native ETH/ZZZ pair, chain or pinned core bindings. A second
enabled pool is rejected even through governance; comments/UI restrictions are
not the enforcement boundary. Disabling only operations retains its selection.

To switch contributions after sealing:

1. Review the supported destination and full config. It may be admitted with
   `depositsEnabled=false` for preparation/maintenance; this does not select it.
   Read `Vault.poolBucket(target)` and the existing bucket identity. If unreserved,
   call `Vault.reservePool(target,existingBucket)` **before** enabling destination
   deposits. If already reserved, require the same intended bucket. Never guess a
   new bucket ID: alias reservations and four registered bucket slots are permanent;
   an incorrectly selected bucket is not later reassigned/merged by moveFunds.
2. Governance disables the current pool with `disablePool(oldId,true,false)`,
   then fully validates/enables the new config through `configureNative`. When moving an existing shared bucket, **move it before
   enabling destination deposits**: admit the target with deposits=false and
   operations=true, disable source deposits, execute the guarded same-pair
   `Migration.moveFunds(bucket,target,minLiquidity,deadline)`, then enable target
   deposits. The existing move guard requires target operations, not deposits.
   If the governance wallet supports a reviewed atomic batch that preserves it
   as each target's caller, it can include this ordered sequence; target failure
   must revert the whole batch. Access does not supply a batch executor. Enabling first lets another activation
   occupy the destination bucket and block the intended move. If intentionally
   stopping first in a separate transaction, a failed enable leaves deposits
   stopped; retry only after resolving validation failures.
3. Verify `ContributionPoolChanged`, the getter, old flag=false and new flag=true
   at a confirmed block. Update the API's reviewed target/runtime pins and UI;
   discard old quotes and simulate fresh ones. Cancel obsolete wallet proposals.
4. A selection-only switch does not move LP. Existing NFTs in the old pool cannot top up until their shared bucket is moved
   to the selected destination, or governance switches contributions back. The
   selection alone does not move liquidity. Use the guarded migration/parking
   procedure; old claims, historical accounting and permitted maintenance remain.

For incidents, dependency-free `disablePool` clears the selection only when
stopping that pool's deposits. Repeated stops of a historical pool cannot clear
the new selection. Full `configureNative` with deposits=false also clears selection,
but still requires healthy dependencies. Roll back a selection using the same
validated switch; mined contributions cannot be undone. A canonical replacement
must explicitly configure its own selection; this is not imported economic state.
No new role or governance delay is introduced, and an already sealed old registry
cannot gain this rule through a configuration call.

The Vault has **four historical local bucket slots**, including permanent reservations/imports. Before a permanent reservation, read
`Vault.poolBucket(poolId)`, `VaultCanonical.bucketIdentity(poolId)`,
`VaultCanonical.aliasBucket(poolId)` and `Vault.bucketCount()/MAX_BUCKETS()`
from the same confirmed state. Enumerate `Vault.bucketAt(index)` for indexes
0 through count minus one to determine registration. There is no public
`registeredBucket` getter; registration is derived from the complete actual
bucket list, not a guessed mapping call or a supplied JSON flag. For a new
uninitialized first-activation target, use its exact canonical bucket ID if
reserving; arbitrary nonzero placeholders can permanently prevent activation.
Unreserved first activation can create its canonical slot only if capacity is
available. An already initialized bucket moved from another pool keeps its
original ID; do not force it to the destination pool's newly derived ID.

Do not execute destination reservations before canonical header import: the
importer requires empty local sequence/buckets/aliases and later imports the
authenticated source aliases. A planned inherited mapping is not permission to
pre-populate the replacement. The current schema8 observer checks these facts;
its narrow reservation status is not full transaction approval. A bad permanent
reservation has no delete/relabel fix: assess remaining capacity/another reviewed
pool or a fresh pre-deployment candidate, rather than rewriting off-chain state.

`Vault.reservePool(poolId,bucketId)` is governance-controlled and consumes permanent identity/capacity; repeated matching reservation is idempotent. An unfunded reservation cannot simply be deleted to recover capacity. Check occupancy/history before admitting or reserving a new bucket. Existing bucket moves/returns reuse their identity, subject to pool occupancy; NFTs cannot be arbitrarily split/merged by an admin operation.

| Desired effect | Action | What remains |
| --- | --- | --- |
| Stop fresh activation/top-up into one pool | Governance calls `PoolRegistry.disablePool(poolId,true,false)` | Existing custody and claims remain; it does not withdraw LP or stop every maintenance operation. |
| Stop ordinary price-guarded maintenance in one pool | Governance calls `PoolRegistry.disablePool(poolId,false,true)` | Existing LP remains at the venue; fresh contributions also fail execution guards. Governed exit paths can still exit a disabled source with their own checks. |
| Retire a pool but preserve users' rights | Disable new contributions, cancel conflicting plans, move or park the bucket using the next section | Retain pool/history/receipts; do not delete indexer history or reward assets. |
| Resume use | Review dependencies, configure intended flags, verify live/pause/preparation state, re-quote and simulate | Enabling a flag does not relocate parked LP or restart a stopped server. |

**Disable without healthy dependencies.** `PoolRegistry.disablePool(poolId,disableDeposits,disableOperations)` only clears the selected flags of an already admitted pool. Use `(poolId,true,true)` to clear both. A `false` argument leaves that flag unchanged; it never enables anything. At least one argument must be `true`; repeated stops are safe. The function does not call tokens, prices, wrapper, hook or venue, and does not change the PoolKey, range or limits. Read `get(poolId)` and the resulting flags in `PoolDisabled` after execution.

**Reopen only after validation.** Read the complete current config, set the intended enabled flags and call `configureNative`. After terminal exit only Ready-phase, deposits-disabled reserve venues may be restored. Full fresh token/price/admission/venue checks still apply; a failed attempt leaves the stopped config unchanged. A previously approved operation can still be executable: cancel obsolete approvals and coordinate keeper/user transactions before reopening. A stop cannot undo a mined transaction.

Both stop and re-enable are exact immediate governance operations; there is no new guardian or keeper permission. Global pause does not block these configuration controls. Preparation, frozen/importing/retired lifecycle states do block them: cancel reversible preparation first if configuration is needed, or use permitted drains. The existing guardian global pause remains available for incidents. `operationsEnabled=false` is not a universal freeze: claims, transfers and some receipt/harvest/exit paths are separate. For a protocol-wide incident use the stop matrix.

## Custody and LP migration

There is **no external handoff custody address** in accounting6/custody4.
[Collective holder exit](HOLDER_COLLECTIVE_EXIT.md) replaces both principal and
royalty-custody drains. Normal moves and parking remain reversible before exit.

| Need | Exact control and verification |
| --- | --- |
| Switch to another same-pair pool | Admit the reviewed native ETH/fixedZZZ fee tier. Simulate governance Migration.moveFunds(bucket,pool,minLP,deadline); verify actual LP/ticks, unchanged shares, retained value and deliberate sole contribution-pool cutover. No external recipient. |
| Temporarily park LP | Pause; use exact Migration.park(ParkingRequest), current nonce/epoch/LP/shares/currencies and raw minima. Principal remains attributed in the Vault. No USD oracle required; venue/token checks remain. |
| Restart parked LP | Before collective exit, revalidate feeds/venue/limits, unpause and call Migration.resume(bucket,pool,minLP,deadline). Verify actual LP and unchanged shares. |
| End collection LP | Pause and review irreversible shutdown. Governance beginCollectiveExit(reviewHash), then closeBucket for each bucket with raw ETH/ZZZ minima. No conversion or custody recipient. Pending compound joins principal; earned rewards and buyback backing remain separate. |
| Deliver principal without holder action | Anyone runs allocatePrincipal(max32) to completion, then distributePrincipal(max32 IDs). Current owners receive exact allocated ETH+ZZZ. Inspect paid/deferred markers; low gas can leave later IDs unprocessed. |
| Rejected owner payment | Other payouts continue. Retry unpaid IDs, or actual owner claimPrincipal(id,recipient). ERC721 approval/operator authority cannot redirect funds. Both assets stay backed on failure. |
| Token/chain migration | Exit returns assets to holders; no protocol bridge, issuer exchange or external treasury custody remains. A fresh project/deployment does not inherit these principal rights automatically. |

The exit is permanent: unpause cannot reopen minting, activation, growth,
rebalancing or resume. Current ownership carries unpaid principal and previous
unclaimed rewards. After payout there is no second principal payment on sale.
NFTs remain transferable/royalty-eligible; all LP earnings end after final close.
Whole-collection handoff after exit is blocked because its importer does not
carry terminal principal settlement. Follow the complete runbook for exact
phases, minima, rounding, failure recovery and receipt reconciliation.

## Dependencies and pricing

| Change/problem | Control and checks | Fallback/limit |
| --- | --- | --- |
| USD source pair / freshness / disagreement | Governance `Oracle.setDualFeed(token,primary,secondary,maxDeviationBps,reviewHash)`; verify two independent reviewed sources, exact runtimes/decimals, valid current rounds, append-only identity and `priceBounds` fingerprint | Both sources are mandatory. No single-source, stale/spot or $1 fallback. Disable affected work and follow the [pricing recovery procedure](#configure-stop-and-recover-usd-pricing---2026-10-24); raw funded claims and explicitly approved raw custody retain separate rules. |
| Sequencer feed replacement | `setSequencerFeed(source,expectedCodeHash,reviewHash)` after reviewing the new nonzero source | Replacement does not require the failed old feed to work. Existing recovery grace remains. No setter removes the protection by setting zero. |
| Pool manager, token, router or optional historical hook change | Compare actual code/config/authorities to the deployment pins; stop affected work | Some source/route policies can be replaced, but immutable venue bindings cannot be patched by changing a manifest. New unsupported implementations require compatible reviewed replacement work. |
| Contradictory pool sqrt/tick/fee observation | Unsigned contribution/route reviews and observed/manual inventory gates reject inconsistent integer slot0, malformed directional protocol fees or reviewed static-fee mismatch. Valid downward-crossing boundary ticks are preserved. | Stop the affected preparation/release review; retain sanitized block/hash/error evidence. Compare the same canonical block using a reviewed independent provider and check runtime/key pins. Do not edit the tick, relax checks or substitute latest state. Consistent fabrication still requires provider review; this validator is not authentication. [Market/input review](../reports/market-adversarial-20261026/REVIEW.md). |
| Malformed RPC identity/JSON or ambiguous success/error | Shared read transport rejects noncanonical chain quantities, duplicate fields, nonfinite values and invalid envelopes; decoder limits become bounded sanitized failures | Preserve pending intent/index evidence, compare the same canonical block at a reviewed alternate endpoint and inspect fixed error diagnostics. Do not relax parsing, guess zero, reset a journal or resend a saved transaction. A malformed result+error is not qualified missing-block rejection. [Exact scope](../reports/system-adversarial-20261026/VERIFICATION.md). |
| Stalled DNS or continuously trickled RPC data | Qualify the source120s systemd main-progress watchdog with matching code/unit, systemd>=240, main notification and full cgroup SIGKILL/no-core settings | A socket timeout alone is not total elapsed time; standalone commands remain unsupervised. Rehearse all-descendant kill/lock release and exact pending-journal recovery, with no automatic resend. Do not change a running unit without authorization. [Watchdog procedure](KEEPER_RECOVERY.md#stalled-rpc-and-progress-watchdog). |
| RPC/trace/archive outage | Use chain-checked reviewed endpoints with required hash-pinned reads and trace/receipt semantics | Never fall back to latest/unconfirmed state or a wrong chain. Serve unavailable status; retain indexes/state. |

Changing off-chain code hashes to whatever is currently deployed is not a review. Verify proxy implementation and external control as well as runtime bytecode. Governance configuration during canonical preparation is blocked; cancel preparation only if reopening is intended, not to bypass a migration freeze.

## Revenue operations

A real `PoolManager.donate` becomes funded fee growth and is allocated at harvest
like other actual LP receipts. An unsolicited raw Vault balance remains a prefund,
not NFT income or new shares. Do not describe funded earnings alone as organic
trading volume or a sustainable yield; donation/wash-flow intent is not classified.

Hourly harvesting funds the 5% compound reserve; it does not require a compound
transaction at the same time. Compound itself harvests first before releasing
and reinvesting the reserve. Claims run neither job. Currency-specific
`compound_thresholds` already exists; use reviewed raw thresholds for both
actual ETH/ZZZ currencies. Idle compounding requires that map; the reserve-only
legacy/common fallback is not a qualified production economic threshold.

Revenue is receipt-based, not a per-minute promise. **80/10/5/5 is fixed**: individual LP shares / equal activated-NFT collective membership / compound reserve / buyback reserve. Rarity only weights the separate royalty ledger at x1/x2/x3. Allocation occurs at actual harvest. The 10% denominator is activated membership at that allocation, not remaining unclaimed NFTs; a claim never redistributes funds or runs the 5% jobs. Source: [timing and arithmetic](ECONOMICS.md#allocation-reinvestment-and-claim-timing).

| Operation | Entry point / owner of action | Verify and recover |
| --- | --- | --- |
| Harvest selected pool LP fees | Permissionless `Vault.collectFees(bucketId,deadline)` while live and locally active | Verify actual venue fees collected and funded 80/10/5/5 allocation. The selected hookless pool has a static 1.002% LP fee; PoPL earns its eligible position's share, not Uniswap's separate protocol fee. No creator payment is required for this LP income. |
| Compound | Keeper `Compounder.compound(bucketId,minimumLiquidity,deadline)`; contributions/rebalances also pull the bucket's compound reserve | Current Budget4 / policy3 compound waits after both the last compound and LP replacement, and yields to eligible rebalance/range selection. Uses attributed backing and guards; funds never pass through keeper. Holder claim balances are separate. |
| Buy back and burn | Keeper `Buyback.execute(token,amount,poolId,deadline)` | Check reserve, oracle value ≤ current `operatingTradeUSD` ≤ reviewed `maxTradeUSD`, swap minima, actual ZZZ acquired and total-supply reduction. Governance tunes the operating ceiling with `setOperatingTradeUSD`; zero stops buys. The buyback target is immutable and must be the same ZZZ as contribution and collective holder return. There is no retargeting setter. Bind Buyback before `Migration.configureZZZ`; mismatched or unbound targets cannot complete setup. Token migration requires collective holder return and a fresh reviewed deployment. |
| Admit LP payout asset | Governance `Rewards.addAsset(token)` | Permanent bounded history, maximum 32; do not fill slots with speculative assets. Admission is distinct from input routing. |
| Receive marketplace royalties | `NFT.royaltyInfo(tokenId,salePrice)` returns the NFT's royalty receiver and requested 5% | Configure marketplaces with the **returned contract receiver**, never a manager wallet. ERC2981 is a request, not universal enforcement on every marketplace. |
| Admit royalty currency | Governance `NFT.addRoyaltyAsset(token)` | Initial scope is native ETH plus the independently verified Robinhood WETH wrapper; stablecoin conversion depends on marketplace qualification. Admission does not restrict sales or convert payouts. Separate bounded ledger (17 total including native); no arbitrary removal/sweep. Pre-admission/no-eligible-holder funds stay quarantined. |
| Synchronize/claim royalties | Permissionless `RoyaltyRewards.sync(asset)`/`syncAll`; actual owner calls ledger `claim` or bounded ClaimRouter | Direct royalty claim synchronizes pending admitted receipts. LP claim does not harvest new venue fees. Use current owner and actual funded amounts. |

A holder can claim both streams in a **1-32 operation atomic ClaimRouter batch**, or claim individually. One failed operation reverts the whole batch; simulate and split by asset/NFT if needed. No operator can choose a different beneficiary or claim just because it holds ERC721 approval. All unclaimed rights follow the current NFT owner; already paid funds do not travel with it. An escrow that owns the NFT is the contract-level holder. Lifetime claimed display requires complete confirmed index history, including predecessors after replacement.

Pause generally preserves claims and transfers while canonical state is operating. A frozen/retired deployment has different rules; follow lifecycle status rather than presenting a failing claim button. Failed payout tokens, blacklists or recipient callbacks may still block their claims. There is no generic admin seizure/sweep/rewrite to clear a liability. Keep actual funded balances distinct from unharvested fees and UI estimates.

Stop scheduled compounding/buybacks using reviewed keeper configuration or by stopping/revoking the keeper. Accumulated reserves remain classified on-chain; no automatic transfer to the operator is allowed. LP/royalty conversion uses its separately bound guarded converter; LP payouts and the fixed 80/10/5/5 allocation are unchanged. Creator-payment inboxes and measurement jobs are retired. See [royalty/claim behavior](CLAIM_ROUTER.md).

Before enabling automated revenue operations, review the actual
[schedule and reserve checks](OPERATIONS.md#reward-timing-and-maintenance-schedule).
The historical accounting4 example polls every 60 seconds, evaluates eligible
confirmation every 240 seconds and schedules standalone
harvests every 3600 seconds (one hour), independently from rebalancing;
standalone compounding is off and `buybacks` is empty. These are blocked sample
settings, not an enabled production promise. Do not put swaps/compounding inside
the holder claim: a failed strategy or buyback should not block funded LP claims.

For a manual independent harvest, governance can call
`Vault.collectFees(bucketId,deadline)` directly; the deadline must be no more
than ten minutes ahead. The same transaction collects actual shared-position
fees and allocates80/10/5/5 to indices/reserves. The function is permissionless:
a caller pays gas but cannot choose the split or recipients, move principal or
initiate collective exit. The keeper normally submits it automatically. Native
ETH receipts fund ETH claims immediately; ZZZ portions still use their separate
reviewed conversion path for ETH settlement. Reserving the 5% allocations does
not execute compounding or buybacks. Sealed/live active custody and other guards
remain; no harvesting after terminal LP exit.

### Coordinate compounding with rebalancing

Fresh Budget `IDLE_COMPOUNDING_VERSION()==4` exposes
`compoundInterval(poolId)` and `compoundReady(bucketId)`. Default compound
interval is 3600 seconds (one hour), independently from the 12-hour rebalance
configuration. This is earliest eligibility, not a promise to compound hourly.

Governance calls `Budget.setCompoundInterval(poolId,intervalSeconds)` on the
exact address returned by `Vault.migrationBudget()`. Allowed600 seconds-7 days;
verify admitted pool identity and `CompoundIntervalChanged`, then getter/readiness.
This changes no clock, shares or backing. It may be configured during ordinary
pause, but rejects preparation, non-operating canonical state and an active
captured operation. It needs no keeper restart; local scheduling intervals remain
additional delays and their JSON changes do require controlled restart.

Every standalone compound, including idle-only/no-swap, waits until
`max(lastCompound(bucket), Position.lastRebalance) + compoundInterval(poolId)`.
It yields to eligible rebalance or available optional adaptive selection. Rebalance
never reads lastCompound: compound cannot postpone the hard rebalance clock.
Keep automatic width selection disabled for the chosen manual operating policy.
Initial LP creation/replacement starts the compound wait; ordinary contributions
and harvesting do not reset it. A failed compound rolls back clocks and funds.

Current keeper policy3 verifies exact Budget runtime, mutual Vault binding and
capability4 before readiness. Enabled compound requires explicit positive
`compound_thresholds` for both actual ETH/ZZZ currencies; use raw units per asset.
Historical policy1/helper2 and older helper1 readers remain versioned separately.
No automatic journal or runtime migration is provided. Readiness does not replace
keeper authority, lifecycle, prices, gas, deadline or execution/backing checks.

Fresh accounting6/policy3 keeper source additionally waits while the main crosses
the 85% physical threshold, is outside its range, or operator width/mode/active
residual geometry is pending, including before
the 12-hour rebalance cooldown expires. This is service policy, not a new
contract restriction. Missing authenticated physical reader pins/data make
compound unavailable; due harvest remains independent. This also applies when
upgrading an LP-routing0 worker to the new source: qualify the reader bindings,
never invent a fallback or rewrite its journal. See
[coordination and read-only review](KEEPER_COORDINATION.md).

Harvest first creates the designated 5% reserve; standalone compound also harvests
before pulling/reinvesting it. Hourly harvesting and holder claims remain independent;
claims never run compounding/buybacks. Stop new compounds through local scheduling
or keeper revocation, reconcile pending hashes, and reopen only after fresh checks.
[Idle ownership](IDLE_AND_DUST.md), [policy/evidence](LP_EXECUTION_POLICY.md).

### Change the standalone harvesting interval

The fresh worker coalesces this clock with its own successful compound/rebalance
only when canonical receipt logs prove a matching Vault `FeesCollected` event.
A zero-fee collection counts; submission, reverts, ambiguous work, NAV changes
and unjournaled manual transactions do not. Missing optional proof preserves
paid recovery but leaves the clock unchanged. The next hourly collection is
measured from the verified receipt block time, not the wall-clock hour. Read
[proof and recovery rules](KEEPER_COORDINATION.md#harvest-clocks-follow-proved-collection).

As the sole operator, edit the **actual keeper service configuration**. The
setting is `maintenance.harvest_interval_seconds`, in seconds. The current
[historical accounting4 example](../keeper/config.holder-exit.example.json) uses **3600 = 1 hour**.
The historical accounting3 example retains 14400 seconds. This is an
off-chain scheduling change: no governance contract call, redeployment or
unsealing is required, and the 80/10/5/5 split does not change.

To use the current **one-hour** schedule, merge these fields into the existing `maintenance`
object, keeping its other settings intact:

```json
{
  "harvest": true,
  "harvest_interval_seconds": 3600
}
```

1. Identify the real service's config and unit/supervisor. Review its current
   pending intent, preserve the private config/journal/receipt evidence and
   follow [planned stop/recovery](KEEPER_RECOVERY.md). Stop only that authorized
   service cleanly and confirm it cannot keep signing from another host.
2. Set a positive whole-number interval: `1800` means 30 minutes, `3600` one hour,
   `14400` four hours. Review gas budgets before increasing frequency. Check
   `bucket_overrides["<actual bucket ID>"].harvest_interval_seconds` and `.harvest`:
   these override the global maintenance values. A bucket ID is not an NFT ID
   or a Uniswap pool ID. Change/remove only the intended override.
3. Keep chain, sender, runtime/authority pins, state/lock paths and original
   pending records intact. Run read-only preflight with the exact reviewed config:
   `python3 -m keeper.ops --config /path/to/reviewed-keeper.json preflight`.
   Reconcile pending work using its original evidence, not new assumed limits.
4. Under the authorized service rollout, restart the actual service with the
   reviewed config. The keeper loads config at startup; editing JSON alone does
   not reload it. Do not run another monitor against its journal alongside it.
5. Require a fresh healthy cycle with the matching `configuration_sha256`, then
   verify the canonical `FeesCollected` receipt when eligible and funded
   allocation when fees are nonzero. A valid 0/0 collection need not emit
   `FeesAllocated`. Health or dry run alone does not prove a harvest occurred.

The threshold uses the receipt block time of the last confirmed successful
`harvest:<bucket>` action or a proved own compound/rebalance harvest coalesced
into that clock. The latter requires matching canonical Vault event proof;
zero-fee collection is valid. Missing optional proof leaves the clock unchanged
while preserving paid recovery. Contributions, unjournaled manual activity,
submission, reverts and ambiguous work are not silently adopted. A shorter
interval or no prior worker success record can make harvesting due at the next
eligible cycle. Restart does not reset the clock. Polling uses the
separate `interval_seconds` setting. Historical examples use 600 seconds; fresh
confirmation3 requires 60-240, with 60 in its example and 240-second eligible
observations. A harvest interval shorter than polling cannot make checks run
more often. Pending
receipts, other eligible jobs, pause/lifecycle and execution/gas guards can delay
execution; this is not an exact wall-clock promise.

If a price-dependent maintenance read/simulation fails, the keeper logs
`maintenance_deferred`; a due harvest can still pass its own normal checks for
the authenticated active bucket. This does not permit rebalancing with stale
prices. Invalid configuration/ABI, bad bucket identity, global pause and canonical
locks still fail closed. Treat degraded health as an issue to repair even when
fees were successfully collected. If any pending intent was saved, reconcile it
first; no fallback job may continue after an ambiguous submission.

Set `maintenance.harvest=false` to stop only scheduled standalone harvests;
implicit/manual harvesting and funded claims retain their existing behavior.
To roll back a schedule change, restore the prior reviewed config and repeat
the controlled restart/health checks. Never reset `last`, pending state, nonce,
budgets or health hashes to force a harvest or make a check pass. Review the
config change explicitly when using a backup bound to the old configuration.

### Tune or stop buyback trading

Read `Buyback.maxTradeUSD()` (reviewed maximum) and `operatingTradeUSD()`
(current limit), both USD18. The deployment default is the hard ceiling. Through
the current governance wallet, call the target directly:
`Buyback.setOperatingTradeUSD(limit)`, with `0 <= limit <= maxTradeUSD`.
Confirm `OperatingTradeLimitChanged(previous,current)` and the getter. Zero stops
new execution without querying the oracle or releasing reserves; it does not stop
LP maintenance, claims or royalty processing, and does not move accumulated funds.
Reopen by selecting a positive reviewed limit within the hard ceiling.
This is a per-trade USD limit, not a token quantity or daily/cumulative budget.
Current pricingV2 checks the upper admitted input price, rounded upward at token
precision. Reduce the raw task amount if disagreement makes it exceed the ceiling;
never switch to the lower mark just to make a batch pass.
Zero also stops direct ZZZ burns; it leaves the 5% buyback reserve backed in Fees.

Remove or resize the keeper's fixed `buybacks[].amount` tasks after lowering or
stopping the ceiling. The keeper still simulates exact execution; an oversized
task intentionally reverts and can cause error/backoff until its configuration is
adjusted. Do not clear pending journals or resend confirmed transactions. An old
review above the new limit fails at execution; inspect any already-submitted hash
before preparing another action. Pause allows configuration, while preparation,
canonical locks and reentry prevent it. A replacement reviews its own limit;
handoff does not copy the source's operating policy. Governance separately calls
`Buyback.setMaximumTradeUSD(limit,reviewHash)` to change the positive uint128
USD18 maximum. It must not be below operatingTradeUSD; lower the operating limit
first when shrinking. Verify MaximumTradeLimitChanged and both getters. This
changes no ZZZ identity, revenue allocation, holder entitlement or reserve. [Evidence and limits](../reports/post-seal-controls/VERIFICATION.md).

### Coordinate token and market dependencies

Use [Creator tasks / ZZZ team](../TODO.md#creator-tasks--zzz-team) to record public
ZZZ token controls, independent price sources and market continuity evidence.
Record each answer's date, authorized contact and supporting identifiers. Request
proof of control where relevant; never request a signing key. Creator-payment
terms, per-bucket funding receivers and measurement invoices no longer form part
of the selected hookless-pool operation. Marketplace royalties remain separate.

### Start a current keeper configuration

The shipped `keeper/config.example.json` is a historical accounting3 template;
`keeper/config.holder-exit.example.json` is historical accounting4. Neither is a
ready-made profile6 operating configuration. Do not merely relabel their version.

Prepare a separately reviewed configuration with accounting6, protocol_policy_version1, maintenance3,
confirmation3, portfolio2, LP routing2 and quality1; exact module/Budget/helper
runtime pins and reciprocal parents; the complete new policy/math/physical
executor graph; explicit 60–240 second main loop and new private state paths.
Schema8 production observation is separate from keeper live configuration.
Leave live review/runtime pins unset and dry run enabled until real deployment
bindings, gas/spend limits, providers and schedules are qualified. Enable
compounding/conversions only with reviewed per-currency thresholds/routes, and
keep automatic width selection off for manual range policy.
Do not apply the fresh profile to an existing legacy journal or reuse its state path.
Preserve old hashes/nonces and follow [keeper recovery](KEEPER_RECOVERY.md).
Changing the example does not alter any installed service or saved journal.

### Marketplace currency and ETH payouts

The [settlement and conversion runbook](ROYALTY_SETTLEMENT.md) specifies the exact
OpenSea pricing procedure, pre-seal converter binding, reviewed wrapper/routes,
post-seal governance stop/reopen controls, keeper configuration, gas budgets,
outage recovery and event/accounting checks. Native ETH requires no conversion;
WETH unwrap is exact and stablecoin conversion enforces the converter's current
`conversionLossBps()` ceiling (1% by default, maximum 10%), plus stronger caller
and venue minima.
Network gas is separate and paid by the keeper. Batches convert earned balances
for at most 32 NFTs and credit ETH to those same NFTs; they are not claims.

`RoyaltyRewards.bindConverter` is one-time **before sealing**; converter
`configureWrapper`, `addRoute`, `setRouteEnabled` and `setEnabled` are immediate
governance operations within lifecycle controls. The optional keeper job is off
by default. Do not reset pending/nonce/budget state when adding its contract pins.
Stop a failed route without querying it, then review fresh policies before restart.

Activation survives optional-currency balance failures. On recovery, unseen funds
belong to the earlier eligible cohort; waiting NFTs join future receipts only.
Check `eligibleFor(id,asset)` and the deferred/recovered events. Healthy claims
continue; exact unreadable backing can still block canonical handoff. Original
currency claims remain a fallback. No LP principal, orphaned funds or other NFT's
entitlement is swept into a conversion. Local implementation is not live-service
approval; use the [central settlement task](../TODO.md#task-royalty-eth-settlement).

### Read royalty status and conversion history

The [reporting guide](ROYALTY_REPORTING.md) gives exact configuration and field
semantics. In a reviewed schema-2 API configuration, opt in with
`"royalty_reporting": {"schema": 1, "converter": null}`; supply the exact bound
converter address/runtime hash only after reviewing them. This changes read
behavior, not contracts, keeper scheduling or transaction permissions.

Verify dormant/eligible/deferred cases at a confirmed block. A currency failure
must show an unavailable amount, while healthy balances remain visible. Unknown
core state, stale snapshots and work limits reject the request. Disabled or
unverified converter status is not an ETH execution promise. Original-currency
claims and synchronization retain their separate on-chain controls.

Use actual lifetime `previously_claimed` payouts for the NFT, including past
owners. Keep `royalty_conversions` separate: current ETH claimable already includes
unclaimed converted amounts. After an API/indexer outage, restore/backfill complete
history and retirement cutoffs; never reset them to show zero totals. Roll back
to a compatible reviewed configuration/release and disable unsupported UI fields
if needed. Runtime drift requires review, not automatic acceptance of new pins.
Actual hosting/consumer qualification remains open; no service is started by this
code change. See the [scoped verification](../reports/royalty-reporting/VERIFICATION.md).

### Serve processed earnings and current-price values

Enable the optional `earnings_history` profile only after reviewing the
[exact configuration and backfill procedure](EARNINGS_HISTORY.md). It requires
all seven financial emitters from creation for each predecessor/current epoch;
changing an indexer address list without rebuilding complete coverage is invalid.
Use `/v1/earnings` and `/v1/nfts/<decimal-token-id>/earnings` for processed
all-time/24h earnings. NFT history follows the NFT across owners.

The accepted USD policy marks originally earned currencies at **today's confirmed
prices**. Show this label and snapshot time; do not add conversion credits as
income or confuse earned amounts with current claimable or lifetime paid amounts.
Missing prices are null, not zero. Pending/unprocessed revenue is excluded.

Before live cutover, use [independent-provider history comparison](HISTORY_AUDIT.md) over contiguous windows for every configured epoch, with the exact retirement/current cutoffs. Preserve both providers' evidence on mismatch; backfill a separate database and rerun economic reconciliation before reopening. The audit never repairs data or signs. The indexer's new ordered block/log index is created on restart, requiring disk space, a WAL-consistent backup and a reviewed maintenance window for large databases. No live restart is performed by this change.

Remove the optional profile and restart the read service to stop these views;
no contract action, keeper stop or claim restriction is needed. Preserve/backfill
history into a separate database after an outage. Reconcile against pinned
indexes/denominators and known NFT claims before reopening. Review changed
runtimes/feed policies instead of automatically accepting them. Real provider,
large-history/load and UI qualification remain open; source changes do not start
a service. The strict earnings endpoint may be unavailable during ledger/currency
faults even when the separate healthy-currency balance view still works.

## Mint and metadata

For accounting6, write randomness policy through **ProtocolPolicy**, not the NFT.
Configure before sealing/import preparation with the reviewed coordinator,
expected runtime codehash, lane, subscription ID, confirmations, callback gas,
payment mode and reviewHash. Initial defaults remain unconfigured. After all
minted draws finalize, governance may perform a planned provider/subscription/
lane/payment rotation. Pending original draws can never be retargeted or rerolled.
See [future controls](#future-operating-settings) and [VRF recovery limits](ADAPTABLE_POLICY.md#planned-vrf-rotation).

`ProtocolPolicy.setRandomnessRequestSettings(confirmations,callbackGas,reviewHash)`
changes future requests only, within3–200 confirmations and200,000–10,000,000 gas.
Qualify narrower actual provider bounds, simulate, then verify policy/revision
and `RandomnessSettingsConfigured`. Stop new mints during an outage with
`NFT.setMintPaused(true)`, recover original requests and finalize in order.
Raising the future callback budget cannot repair an already-created request.
New source controls do not add them to existing sealed code or select a provider.

Evolution thresholds are now governed display settings; positive enhanced and
strictly higher singularity USD18 values retain defaults1000/10000. They emit
ERC4906 invalidation and never rewrite traits, balances, rarity or eligibility.
Activated stage1 comes from real activation, not a permanent100USD valuation floor.

The read API offers `GET /v1/mint-readiness`: confirmed minted/revealed counts, unfinished draws, earliest request/epoch, whether it awaits randomness or finalization, and the separate on-chain `mint_paused` flag. `new_minting_stopped` combines this flag with lifecycle controls; it is not a provider or gas-availability check. It checks inventory consistency and canonical deployment. It does **not** verify subscription funds, provider liveness, elapsed pending time, escrow compatibility or full handoff readiness; those fields are explicitly unverified. Correlate request/fulfillment events for latency and alert thresholds. The endpoint does not deploy a monitoring service or resume the paused chat monitor.

For a provider outage, governance calls `NFT.setMintPaused(true)` directly, with no waiting period. Verify `NFT.mintPaused()` and `MintPauseChanged(true)`. This blocks new NFT mint/randomness requests, including direct Vault callers; the complete transaction reverts without spending the mint payment. Pending original fulfillment and ordered finalization continue. Existing revealed NFTs can still activate/top up, transfer, claim and undergo LP maintenance when their independent guards permit. Pausing during the NFT receiver callback also rolls back that mint atomically.

To restart, qualify provider funding/liveness and reconcile pending requests; governance calls `NFT.setMintPaused(false)`, verifies the event/getter and simulates the complete mint. It does not clear global pause, preparation, canonical locks, exhausted supply or broken provider conditions. The mint switch is an operational setting, not an exported economic entitlement: for a replacement explicitly set/review the successor's desired state before locking it for import (fresh deployment default is `false`). It is not copied from the source and is not automatically cleared by handoff/abort. Existing sealed deployments without this function cannot acquire it by configuration.

There is **no pending-request coordinator retarget, reroll, administrator-selected trait or pending-request transfer**. Ordinary LP pool migration/rebalance has no reveal-completion requirement. Global pause remains the wider incident control; hiding the Mint button alone does not stop callers. A permanently unanswered draw still blocks whole-collection replacement.

The current artwork revision replaces Vertical ribs with **Twin circuit routes**
in the existing `ribs` filename/slot 3. Do not rename or reorder the packed inventory.
Before first production deployment, regenerate and verify the complete content
bundle from the matching website revision, review the new root and metadata
renderer bytecode, and qualify marketplace retrieval. A previously prepared bundle
has the old appearance. Roll back the complete website release if needed, keeping
its matching manifest; do not mix old metadata/renderer labels with a new root.
This pre-deployment visual change adds no operator function or authority and does
not make sealed artwork mutable. See [verification](../reports/twin-circuits/VERIFICATION.md).

Artwork URI is fixed once configured: `setBaseURI` can populate an initially empty base only once before sealing. Keep the same IPFS/Arweave content available with redundant pinning; a gateway UI change does not change canonical metadata. Permissionless `refreshMetadata(tokenId)` or `refreshMetadataRange(firstOrdinal,lastOrdinal)` (maximum 50 inclusive ordinals) emits ERC4906 notifications. The optional keeper watcher can request refreshes, but marketplace caches choose when to refetch. Current LP valuation drives evolution and can fall; activation eligibility does not disappear just because artwork downgrades. Never replace unavailable prices with zero or lifetime deposits.

## Whole-collection replacement

This is a separately reviewed operation, not routine LP maintenance. Current implementation supports **same-chain** replacement only, with every minted draw finalized, buckets parked/None, no outstanding principal or royalty custody plans. Read [the exact handoff sequence](CANONICAL_HANDOFF.md) before any attempt.

Run the [read-only holder inventory and escrow cutover procedure](HOLDER_PREFLIGHT.md) before preparation and again after freeze. Every code-bearing owner requires a review of its ability to release and claim for the exact replacement; a complete inventory is not approval.

1. Independently review the proposed different-code successor, its economic compatibility and deployment commitment. Governance is trusted to approve it; there is no identical-code safeguard. Inventory every contract/escrow NFT holder: same owners at a new NFT contract address does not prove their escrow can operate it. Rehearse withdrawals/cutover while the old system is still usable; never rewrite owners to work around an incompatible escrow.
2. Require Access.lpExitStarted()==false; terminal principal settlement cannot be imported by this successor. Prepare the compatible V6 destination as an inert importer with CanonicalHandoff.prepareImport(sourceController) before its seal, qualify actual dependencies/randomness and verify its source binding. Governance starts the exact reviewed preparation notice. New mint/contribution/maintenance/config work stops; reveal, transfers, claims and permitted local parking remain available.
3. Finish existing provider responses and ordered `finalizeTraits` calls; confirm `unfinished_draws=0`. This is the selected simple policy: reliable funded provider plus draining before replacement. Do not remove the fully-revealed check if a request is stuck. Cancel the exact notice via `cancelPreparation(noticeHash)` if postponing, then restore ordinary controls deliberately.
4. Park each live bucket locally with its exact reviewed request; do not start collective holder exit. Governance freeze() stops ownership/accounting before capture. Complete six ordered settle(slot) domains, export/import batches of at most eight and completeImport(), then exact classified fund(slot,index) legs. Recover from on-chain cursors/roots rather than an assumed last successful command.
5. Verify every root, owner, trait, share, liability, reserve and exact backing. Governance `commit()` atomically retires the source and activates one successor. Finality remains required before service/marketplace cutover. Update canonical address/runtime and complete predecessor-history configuration, payout routing and marketplace collection records; old ERC721 approvals are not imported.
6. Before commit, `abort()` cancels the importer; return every funded leg via `returnFunds`, then `finishAbort()` only after full restoration. This is not immediate unlock. After successful commit the source cannot be revived by unpausing or cancelling preparation. Late royalty receipts forward one successor at a time through the supported royalty forwarding function. There is no creator-inbox forwarding path.

Budget the complete workflow before preparation, using the [domain row/call
calculation](CANONICAL_HANDOFF.md#workflow-size-and-relay-budget). Four custody
slots do not bound lifetime aliases. Recover exact next cursors/roots after an
interruption; never skip rows or relax backing to fit a transaction budget.
This sizing review needs no service restart or on-chain configuration change.

A successful same-chain handoff does not qualify cross-chain finality, transport or post-halt recovery. Do not promise these are solved by external principal custody. The retired v3 principal bridge stack is not bound in new deployments. Collective exit must not have started; canonical V6 rejects terminal principal settlement. Imported local buckets retain their reviewed shares/backing. Track the remaining design in the [canonical recovery task](../TODO.md#task-security-chain-recovery).

## Stop controls

**These controls are not interchangeable.** First reconcile already-broadcast transactions; stopping a service or disabling a route cannot undo a mined operation.

| Control | Stops | Preserves / restart |
| --- | --- | --- |
| Hide a frontend action | That UI path only | Direct contract calls continue. Restore UI only after real backend/on-chain readiness. |
| Stop an API/indexer/keeper process | That service's new work | On-chain custody/rights persist; another authorized keeper/direct caller may operate. Recover durable state before restart. |
| Revoke keeper | New authorized keeper actions from that address | Permissionless claims, transfers and allowed fee synchronization remain. Governance must authorize a reviewed replacement. |
| Disable source asset / Entry route | Affected contributions | Existing LP/funded claims remain. Reward/royalty conversion routes are separate controls; this stop does not disable them. Re-enable only after validation and fresh quotes. |
| Converter `setEnabled(false)` / `setRouteEnabled(id,false)` | New conversion through that converter/route | Existing earned currencies/credits stay backed; receipts and source claims keep their separate permissions. Review routes/runtime/prices and full simulation before re-enabling; an enabled getter alone is no qualification. |
| `NFT.setMintPaused(true)` | New NFT mints and new randomness requests | Governance only. Original fulfillment/finalize, existing NFT rights and LP work retain their own guards. Resume with `false`; global/lifecycle controls remain. |
| `Buyback.setOperatingTradeUSD(0)` | New buyback executions only | Immediate governance; no price/reserve query. Resize/remove keeper buyback tasks to avoid deliberate simulation failures. Accrued reserves stay classified; reopen with a reviewed positive limit no higher than `maxTradeUSD`. Preparation/canonical locks still apply. |
| `PoolRegistry.disablePool(id,stopDeposits,stopOperations)` | Pool-specific new contributions / ordinary guarded operations; no token/price/venue reads on disable | Governance only; flags only clear. Not universal pause. Reopen with full validated config; parked LP still needs resume. |
| `AccessController.setPaused(true)` | Ordinary mint, contributions, standalone harvest, rebalance/compound/buyback and moves/resume | Existing Uniswap LP stays deployed and can accrue actual in-range fees. Transfers/funded claims/royalty receipts retain separate guards. Governance unpauses with `setPaused(false)`; no other stopped flag is changed and terminal lpExitStarted is not reversed. |
| Canonical preparation | New economic work and normal protocol configuration | Existing claims/transfers/reveal/permitted drains; exact notice can be cancelled before freeze. Not a generic pause toggle. |
| Canonical freeze | Ownership and ordinary reward/accounting operations | Only handoff settlement/export/funding/abort path. Fully restore abort or complete one successor; no guardian unlock. |
| `Migration.invalidateParking(bucket)` | An unused parking authorization at its current nonce | No funds move. Collective exit has no cancel/recover/reopen path; failed individual payments stay backed for retry or owner fallback. |

There is no independent pause for every individual feature/asset payout. Do not invent one in an incident. Source: [module guards](../src/base/ZZZModule.sol), [controller](../src/ZZZAccessController.sol), [recovery matrix](CHANGE_AND_RECOVERY.md).

### Common stop and restart sequences

| Intended outcome | Ordered calls and caller | Restart and failed-step handling |
| --- | --- | --- |
| Keep main, stop using a residual at the next safe adjustment | Governance reads `enabled(pool)`; if true calls `PortfolioPolicy.setMode(pool,false,reviewHash)`. An authorized keeper later calls `Vault.rebalance(bucket,minimumLiquidity,deadline)` after cooldown and execution guards. | No global pause. Both old legs close atomically and one active main is created. A failed replacement preserves both old legs; desired mode stays false/pending. Normal price/caller/retention/idle checks remain; small attributed idle may remain. |
| Close only residual immediately; main keeps trading | Reconcile pending work; pause; optionally set modefalse first; rebuild snapshot; governance calls `Migration.closeResidual(ParkingRequest)`. Verify main unchanged/residual0 and exact attributed idle, then governance `Access.setPaused(false)`. | Main was never removed. In-range underlying fees can accrue during the temporary PoPL pause. Unpause restores live PoPL actions, not deployment of returned idle. Large idle can block fresh contributions under the5%guard; perform separately guarded maintenance rather than bypassing it. |
| Urgently consolidate both into one main | Set modefalse if necessary; pause; read new custody hash; governance simulates/submits `Migration.emergencyRebalance(request)` with explicitly chosen retained checks; inspect one main/no residual; unpause when safe. | Emergency does not change desired mode. Failed trade/deployment reverts that operation but leaves earlier separately mined pause/policy calls in effect. Repair/resimulate; choose deliberately whether to remain paused. Never retry by silently dropping safeguards. |
| Stop all our deployed LP temporarily | Pause; governance explicitly disables intended deposits with `disablePool(pool,true,false)`, reads fresh snapshots, then parks each active shared bucket using its own `ParkingRequest`; verify both legs closed and classified idle. | Parking/pause do not clear deposit flags themselves. After fixing actual dependencies, unpause before normal `Migration.resume(bucket,pool,minimumLiquidity,deadline)`; inspect successful deployment before full validated re-enable of intended deposits. A failed resume leaves that bucket Parked; unpause alone cannot restart it. |
| Stop deposits only / stop one execution venue | `disablePool(pool,true,false)` for input stop; separately remove the unwanted swap venue through the reviewed Balancer catalog if swaps are the concern. | Copy/full-validate the intended pool config to re-enable. Pool flags and execution venue lists are different; disabling one must not be treated as disabling both. Empty execution list blocks swaps but a valid no-swap operation can remain possible. |
| Permanently return principal to holders | Paused governance `beginCollectiveExit(reviewHash)`; close every captured bucket, then advance bounded allocation/delivery with exact phase/cursors. | **No restart/unpause reversal.** Do not use terminal exit for a temporary pause, a residual merge or a routine fee-tier change. NFTs retain their separate transfer/royalty/old-reward rights. |

On-chain setters are read fresh; changing an on-chain value alone does not require
a host restart or resealing. Local keeper/API/indexer source or configuration
changes require the controlled restart procedure below. If multiple calls are
separate transactions, only each individual transaction is atomic: failed step3
does not undo successful steps1–2. Record the last confirmed state and use the
documented compensating control, never a guessed rollback or journal deletion.

## Services and server recovery

Before adopting a source release, run
`python3 scripts/check-python-publication.py --revision <exact-commit>` in its Git
checkout. It checks published static imports rather than allowing untracked local
readers to hide an incomplete release. Runtime/config/dependency checks and the
stop/reconcile/restart procedure below remain separate; this command starts no
service and changes no journal. [Publication/lineage repair](../reports/today-audit-20261031/REVIEW.md).

The read/activation service CLIs and indexer now reject duplicate JSON fields,
nonfinite numbers and nonobject configuration before starting resources. The
activation CLI also loads its request before RPC/projection construction. Keep
private original files for review and correct ambiguity explicitly; no file,
database, pending intent or chain state is automatically repaired. Frontend files
retain UTF-8; existing journal/indexer default encoding is unchanged. Roll out
matching source through this runbook with pending work preserved; changed local
source hashes are not a reason to edit a journal or claim a running deployment
has updated. [Scoped verification](../reports/historical-reconciliation-completion-20261029/VERIFICATION.md).

The heartbeat now includes `configuration_sha256`, a hash of the exact loaded
configuration. `keeper.ops health` requires the same hash, not merely chain and
sender. Old/missing/malformed or mismatched artifacts return `configuration_mismatch`.
Deploy matching writer/checker together only through an authorized rollout and
require a fresh matching cycle after a reviewed config change. Never patch the
hash, edit/reset a journal or assume this digest authenticates the host/provider.
There is no in-process config reload: finalize config before constructing Keeper.


Use the reviewed Linux/Unix release and separate service users. Fresh confirmation3 source requires an explicit60–240 second main loop; condition checks target240 seconds during cooldown too, paid sample enrollment starts near eligibility, and standalone harvesting defaults hourly. A main-loop wake is not an on-chain observation transaction. Historical ten-minute/four-hour examples retain their own scope. None guarantees inclusion. Change reviewed config for interval, thresholds, per-bucket overrides, minimum liquidity, gas/daily budgets, RPC providers and metadata scans; restart through the deployment's service manager after checking pending work. Do not guess a production unit name or reuse the isolated staging signer/config.

Read-only checks from the repository (replace paths with the actual reviewed configuration):

```sh
python3 -m keeper.ops --config /etc/zzz/keeper.json preflight
python3 -m keeper.ops --config /etc/zzz/keeper.json health --max-age 1800
python3 -m keeper.ops --config /etc/zzz/keeper.json snapshot --output /backup/keeper-UNIQUE-TIMESTAMP.json
python3 -m keeper.ops --config /etc/zzz/keeper.json verify-snapshot --input /backup/keeper-UNIQUE-TIMESTAMP.json --max-age 3600
```

For a planned stop, inspect pending intent, stop the exact reviewed unit, confirm signer children are stopped, snapshot state/logs and prevent a second host from signing. **Never delete state to clear an error.** A restart reads current buckets and reconciles receipts/nonces/budgets before new work; it does not replay every missed ten-minute interval or recover missed income.

For host loss, fence the old host, restore exact release/config/state from authenticated off-host backups, reconcile transactions/costs since backup and both pending/confirmed nonces, run preflight/dry cycle, then resume one live signer. Total state loss needs reviewed reconstruction or key rotation after reconciliation; chain discovery alone does not restore pending intent or daily expenditure. A fresh unused signer can use explicit `--initialize-state`; do not use it to reset a used signer's history. See [recovery runbook](KEEPER_RECOVERY.md) and [rehearsal commands](KEEPER_REHEARSALS.md).

The indexer needs complete confirmed logs, persistent SQLite/WAL handling and reorg recovery. Back up consistently, preserve deployment anchors and predecessor indexes, and rebuild into a separate validated database if required. Never substitute incomplete history for a zero balance or zero lifetime claims. After code/event-schema/canonical-address changes, update exact pins/config and qualify replay before serving results.

The API has a shared 25-second work budget, finite RPC counts and expiry checks; command-line HTTP servers use a separate request process with a 30-second supervisor deadline and bounded termination cleanup. A blocked request must not leave abandoned work running. Keep it behind authenticated/reviewed ingress as appropriate, TLS, request-size/rate/connection limits and monitoring; the loopback example is not public hosting approval. A timeout/stale quote means **retry from a new snapshot**, not increase slippage or return an old transaction. No API worker holds a signer. See [API](FRONTEND_API.md) and [activation preparation](ACTIVATION_PREPARATION.md).

Watch independent heartbeat/backup age, stale heads, long-pending transactions, nonce drift, RPC failures, disk/permissions, gas balance, budget exhaustion, feed freshness, keeper authorization, range exposure, cumulative execution cost, randomness funding/latency and unexpected dependency changes. Record observation gaps honestly. The desktop chat monitor remains paused; finishing this manual does not restart it.

### Client admission and public API ingress

The infrastructure operator sets `--per-client-active` (default 2, range 1-4)
below the worker count and, only behind the reviewed local proxy, supplies
`--proxy-origin https://EXACT-WEBSITE-HOST` to both CLI services. Read and unsigned
preparation budgets are separate; 429/503 admission errors start no upstream work.
The proxy must overwrite `X-PoPL-Client-IP` from its TCP peer, strip other forwarding
and credential headers, and preserve the exact loopback Host. POST Origin must
match. Shared NAT users share the IP budget; no wallet authentication is inferred.

Follow [the complete procedure](API_INGRESS.md) for the Nginx includes, exact
commands/defaults, TLS/host prerequisites, log rotation, status/retry behavior and
local rehearsal. Validate the full configuration before reload; verify fresh
protocol state and unsigned preparation through the edge. For overload or a bad
release, disable public ingress, drain bounded work, stop the reviewed process
group, inspect provider/worker/limit evidence, then restart and reopen only after
verification. Restart resets in-memory client quotas; it cannot undo a transaction
or recover a failed claim. Roll back proxy and service policy together, never
bypass origin/identity checks to restore availability. No contract authority,
website deployment or paused-monitor restart is part of this procedure update.

## Incident recovery

| Symptom | First response | Safe return to service |
| --- | --- | --- |
| Compromised keeper / excessive rebalance cost | Pause or revoke signer, fence host, retain receipts/state | Reconcile pending transactions and losses, rotate key, review strategy/budgets; one tested signer only. |
| Suspected governance compromise | Guardian pause, secure the governance wallet/signers, cancel unauthorized wallet proposals where supported | Pause alone cannot defeat malicious governance, which can unpause/reconfigure immediately. Use the current wallet's legitimate recovery/rotation process and independent review; there is no controller-admin override or guaranteed rescue. |
| Oracle stale/depegged/wrong or sequencer down | Stop affected contribution/maintenance; preserve claims; consider parking if exact close can succeed | Reviewed new feed/policy, healthy rounds/grace and fresh full simulations; never blind unpause. |
| Out of range | Warn that conventional swap fees may be absent; show observed eligibility/next-check telemetry only if real | Eligible keeper rebalance with guards. Wide range/ten-minute polling cannot guarantee always in range; no fabricated ETA. |
| Repeated slippage/loss/minimum failure | Retain old position; inspect actual conversion, venue costs, liquidity and oracle | Inspect route/timing and accounting first. Governance may deliberately review loss limits within the 10% hard bound; exact approved custody/caller minima remain. A higher limit authorizes more loss and does not repair a failed dependency. |
| Gas spike/low keeper funds/daily budget reached | Stop new submissions; continue receipt reconciliation/alerts | Refill reviewed signer or revise operating budget after analysis; gas is not taken from arbitrary holder balances. |
| Unknown broadcast/nonce drift/reorg | Stop new signing, retain exact intent/hash and canonical anchors | Reconcile confirmed/pending transactions through recovery path; no blind resend or nonce reset. |
| Token blacklist/pause, optional wrapper upgrade or venue unusable | Stop the affected exposure, preserve ledger, review the actual dependency and exact exit | Policy update only where implemented and safe; venue/token/runtime failure can block parking/claim/abort. A wrapper failure affects an explicitly wrapped operation, not native ETH custody. No blanket rescue function. |
| Marketplace royalties missing | Check sale consideration, the exact royalty helper and confirmed transfers | Only payments actually received fund holder claims. Marketplace payment is not universally enforced; do not invent accrual or treat an API outage as a missing payment. |
| VRF unfulfilled / ordered reveals blocked | Verify subscription/provider/request; stop new minting if needed | Use the mint-only governance pause, then original authenticated fulfillment and ordered finalize. Resume deliberately after service checks. No reroll; postpone whole-collection replacement if unresolved. |
| Server/disk/backup failure | Stop unsafe signing; alert off-host, preserve damaged evidence | Restore/reconcile state, permissions and storage; qualify health before new work. |
| Venue/token fails during holder exit | Preserve exact phase, outputs, minima, receipts and liabilities; do not mark paid or erase pending | Governance must finish all bucket closes before payouts become ready. No administrator custody bypass exists. Repair the dependency if possible; lost governance or permanently broken venue/token can block progress. |
| Bad UI/API release | Roll back the service to a compatible verified build, disable affected UI actions | Verify code/ABI/config/chain/history compatibility before reopening. This does not roll back mined transactions or sealed contracts. |

For contract reverts, decode using the exact release ABI. `Unauthorized` means inspect caller/controller/roles, `Preparing` or `CanonicalLocked` means respect lifecycle, `InvalidConfiguration` may mean invalid bounds or pins, `InvalidPrice` means inspect feed/round/sequencer state, `Slippage` means execution bounds failed, and `Expired` means prepare fresh calldata. A retry is appropriate only after identifying the cause and simulating current state. Save sanitized errors and operation identity; do not log credentials or private signer output.

### Restart checklist for an actual incident

Record the cause, affected block/time/object, containment and exact state; verify recovered authority and dependencies; reconcile every in-flight transaction and classified balance; resimulate fresh intended work; restore the narrowest controls in order; execute a monitored bounded operation; verify finalized receipts, user claims and off-host health. Only then reopen normal UI/keeper work. Do not treat a green process status as economic/accounting recovery. Update the incident evidence, task ledger and this procedure if the incident revealed a missing case.

### Unsigned mint and claim service

**Authority:** the service operator enables an unhosted read-only adapter; no
governance permission or private key is needed. Wallet signatures and contracts
authorize eventual payments/claims. Review the exact chain, anchor, base module
pins plus the full accounting6 ProtocolPolicy1/Portfolio2 graph (historical profiles
retain their declared sets), helper pins and admitted assets first. The schema8
release inventory separately observes21 helpers. Bind the separate fee policy to
`Projection.identity`; document full network-fee semantics, gas-price ceiling
and maximum suggested-limit cost. Placeholder reviews are not qualification.

Run `python -m frontend_api.server --config /operator/path/frontend-read.json
--transaction-config /operator/path/wallet-policy.json --port 8787` as one command.
The [configuration and response guide](FRONTEND_TRANSACTIONS.md) defines every
field. The flag enables only typed `POST /v1/transactions/prepare`; GET-only is
the default. Use a separate listener for activation preparation. Keep TLS,
ingress/rate limits and logs under review. No arbitrary calls/signing are added.

Verify independently decoded target/value/calldata, snapshot and policy hashes,
separate estimated gas and draft expiry. The wallet must refresh gas/state and
confirm account/chain before signing. Mint checks the global/mint switches and
preparation; claims retain their independent availability. Selected currency
faults reject a batch; unselected faults do not excuse missing core/inventory
checks. Choose smaller claim batches when necessary. Claims do not fund their
own upfront gas. Missing canonical estimation or omitted fee components means
unavailable, never a latest-state or zero-cost fallback.

**Stop/recover:** stop the listener or restart without `--transaction-config` to
return to GET-only. Inspect sanitized error/deadline/cleanup outcomes and review
runtime/configuration/provider/control changes. Reconcile already submitted
wallet transactions; do not resend payments automatically. Re-enable only after
fresh validation with a compatible reviewed policy. A configuration/code change
requires old drafts to be discarded; mined transactions cannot be rolled back.
This service is not installed on the server by this change.

## Financial reporting and recovery

This [backend correction](../reports/backend-remediation-20261026/REVIEW.md)
adds no on-chain function, permission, config key, write action or service rollout.

| Check / symptom | Operator procedure |
| --- | --- |
| Current LP-only fee history | Keep explicit fee intake 1. Verify actual `FeeController.FEE_INTAKE_VERSION()`, sealed module/runtime pins, all seven emitters and the same confirmed cutoff. Replay requires exact funded-credit/allocation pairs and actual `dust(bucket,asset)` for observed keys. Native address zero is permitted only in that getter's currency argument. |
| Fee/dust mismatch or malformed core value | Stop serving the affected report; preserve raw logs, database, request/config hash, cutoff and error. Compare a separate replay copy with authentic independent-provider windows. Do not edit/delete history, guess zero, relabel a profile or trigger a financial transaction to hide an error. |
| Malformed stored JSON or event envelope | Duplicate fields, nonfinite numbers, missing `removed:false`, malformed hex data and parser-resource failures make history unavailable. Preserve the original DB/WAL; restore/replay a consistent separate copy. Do not normalize corrupt evidence into apparently clean claims or earnings. |
| Optional royalty-currency outage and wallet inventory | Ownership inventory retains exact admitted addresses, lifecycle/history, balance and owner checks even if optional token runtime/decimals fail. It reports no token balances; affected financial metrics remain unavailable. Required module, asset-list, history, budget or canonical faults still reject. Roll out/rollback only a compatible reviewed API release when authorized. |
| Accounting3/4/5/6 balances | Rewards inventory must actually start with native ETH. An NFT that never activated cannot have positive available LP/royalty entitlement. Optional unavailable currencies remain null. Activated parked NFTs and accounting4/5/6 Exited NFTs retain eligible funded rewards; historical outbound semantics remain profile-specific. |
| Wallet read budget | Accounting3/4 checks pinned `weightOf(id)` and `nftStatus(id)` per NFT. This follow-up adds one custody read to profile3; profile4 strengthens its existing status read. Historical1/2 read shapes remain. Keep16-item chunks, finite request limits and complete same-block chunk verification. Requalify actual latency/budgets before rollout; no unbounded retry or limit relaxation. |
| Display totals | Ready to claim = funded LP plus royalty balances now. Earnings 24h/all time includes earlier claims and past owners; claims/conversions are not new income. Compound/buyback/gross receipts are not additional NFT claimable funds. |

Recover by correcting provider/history/configuration evidence and rerunning the
bounded read on a separate copy. Upgrade/rollback only matching API releases
under the existing service runbook when separately authorized; never reset chain
or journals. Genuine view outages may null only their metric; malformed Boolean,
ABI, or contradictory available/value data now rejects the request. See
[earnings operations](EARNINGS_HISTORY.md) and [167-method evidence](../reports/backend-remediation-20261026/VERIFICATION.md).
Production feeds/history capacity and service acceptance remain open.

In accounting4/5/6, native royalty eligibility cannot be delayed by an external
custody transfer because that drain is removed. Optional ERC20 royalty currency
faults still defer only that currency's new eligibility; recovery synchronization
protects the older cohort. Historical profile3 custody events remain readable,
but there is no current returnCustody operator action.

Retired `forwardLate(asset)` accepts only previously admitted currencies and sends
them to the fixed immediate successor. Unknown new ERC20 receipts at a retired
receiver have no admission/rescue path. Before handoff inventory cached royalty
receivers, payment currencies and orders; do not promise universal recovery or
introduce an undocumented sweep. [Royalty recovery](ROYALTY_SETTLEMENT.md#late-receipts-after-retirement).


## Disposable local testing

Use the [local stack](LOCAL_TEST_STACK.md), [website harness](LOCAL_WEBSITE.md)
and [isolated API rehearsal](LOCAL_API_REHEARSAL.md) for disposable Anvil flows.
Verify the exact fixture profile/build/runtime and preserve existing NFT/LP,
balances, receipts and journals. A launcher restart may create a new fixture;
it is not chain recovery. Do not restart/reset an existing lab to clear a wallet
error. Historical named USDC/USDG/WETH fixtures are test-only and are not current
ETH/fixed-ZZZ production inputs.

A token approval is separate from activation/growth. Confirm at most the exact
required ERC20 approval then the reviewed Entry call; sufficient allowance skips
approval. Native ETH uses exact call value, no approval. Before showing new LP or
evolution, verify successful confirmed execution and increased actual deployed LP.
Reverts preserve Entry input/conversion/LP changes, but gas and an earlier
approval remain separate. A failed post-confirmation read requires recovery,
not another contribution.

<a id="local-contribution-form-troubleshooting"></a>
<a id="local-activation-review-during-a-busy-refresh"></a>
<a id="two-transaction-contribution-operation"></a>
<a id="two-browsers-using-local-wallets"></a>
<a id="local-submission-lock-recovery---2026-10-20"></a>
<a id="independent-local-wallet-confirmations---2026-10-20"></a>

Local busy/review/nonce handling belongs to the matching fixture's
[runbook](LOCAL_WEBSITE.md) and [concurrency evidence](../reports/local-wallet-concurrency/VERIFICATION.md).
Keep the serialized local signer/mutation lock. Retry only a documented rejection
that occurred before work began, using the identical saved operation identity;
never retry an ambiguous broadcast as a new action. Two browsers have independent
accounts/sessions; do not erase recovery storage to work around a conflict.

## Main website pending-action and storage recovery

Use [browser-wallet signing and recovery](BROWSER_WALLET.md) for the opt-in local
extension profile; demo storage and launcher-owned signing are different modes.
Reads use the exact deployment-pinned RPC; the extension authorizes/signs.
Reverify exposed account, chain/genesis, runtime pins and original reviewed limits.
A selected wallet label alone proves none of these. Public signing stays disabled;
production must use an independently reviewed Robinhood manifest, never an Anvil
fallback or a guessed network name.

Preserve the hash, exact review, nonce/account/chain and saved operation before
recovering pending, missing, changed or mismatched receipts. Close/refresh does
not cancel a transaction. Recovery checks the same hash, never sends it again.
Check the [nonce-queue procedure](BROWSER_WALLET.md#queued-or-changed-transaction-numbers)
before any separately authorized reconciliation; do not fill gaps or reset state.
A confirmed approval is not Entry execution. A confirmed Entry remains effective
when the UI read fails. Mask stale amounts and disable conflicting actions; only
the target NFT's confirmed LP/tier change may update its artwork.

The known local nonce 35 incident retains its separate
[reconciliation evidence](../reports/browser-wallet/local-mint-reconciliation/RECONCILIATION.md);
it is not a general authorization to clean pending state. Local two-wallet manual
acceptance is [recorded](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md).
The 10/25/100-user campaign is deferred, not passed or implicitly scheduled.

## Concurrent read and preparation services

Follow [bounded workers and cleanup](CONCURRENT_SERVICES.md) and
[public ingress](API_INGRESS.md) for exact flags, limits and start/stop procedures.
Services are read-only or prepare unsigned transactions; they hold no wallet key.
Busy429/503 responses permit finite read backoff, not another financial intent.
A failed cleanup quarantines its worker slot: drain ingress, stop the reviewed
process group, preserve evidence, correct the cause and verify fresh state before
reopening. Never raise budgets or return stale financial data to hide failure.
One-host browser/demo locks do not establish production wallet authorization or
100-user capacity; actual Linux/provider/monitoring qualification remains open.

## Holder payout currencies

LP and royalty converters remain separate, bound to their exact immutable ledgers.
Follow [LP settlement](LP_ETH_SETTLEMENT.md) and [royalty settlement](ROYALTY_SETTLEMENT.md).
Native ETH needs no conversion. Non-native earned balances remain their actual
currency until a successful guarded conversion credits ETH to those same NFTs.
Keep unavailable/pending amounts explicit; never display source token units as ETH.
No converter has principal custody or a generic approval/sweep permission.

## Convert LP holder fees to ETH

Before sealing, bind the reviewed LP converter and any explicitly used wrapper;
qualify actual typed routes, independent feeds, recipient behavior and keeper gas.
Default conversion loss is 1%, governance maximum 10%, gas separate. Follow the
[operator procedure](LP_ETH_SETTLEMENT.md#operator-procedure) and
[bounded scheduling](LP_ETH_SETTLEMENT.md#keeper-configuration-and-scheduling)
for stop/reopen, route rotation, source claims and pending-intent recovery.
Existing sealed deployments/journals cannot acquire new bindings through a config
edit. Service changes need separate rollout authorization.

<a id="capacity-decision-and-manual-acceptance---2026-10-20"></a>
<a id="queued-wallet-transaction-recovery"></a>
<a id="real-local-api-rehearsal-and-complete-wallet-totals"></a>
<a id="collection-data-operations---2026-10-23"></a>

[Confirmed collection reads](COLLECTION_READS.md) and
[current-holdings totals](EARNINGS_HISTORY.md#current-holdings-totals) require
complete same-block inventory/chunks and authentic history. Retain nulls on missing
prices/history. No local manual acceptance or sample reward funds qualify the
current production integration.

## Fixed boundaries

| Desired future change | Current boundary |
| --- | --- |
| Enable/disable ETH or fixed ZZZ; reviewed routes, prices, pool parameters, operators | Governed configuration after sealing, within code constraints; immediate authorization, no delay. |
| Future direct mint price/recipient, entry minima, gas/idle/display policy | Governed through the bounded ProtocolPolicy helper; exact inputs and economic effects are in [future settings](#future-operating-settings). Existing payments/rights never move. |
| Supply/rarity quotas, final traits/art root,80/10/5/5, requested5% royalty rate/weights | No ordinary post-seal setter; protected rights/identity remain. |
| Randomness provider/lane/subscription/payment | Planned ProtocolPolicy rotation requires every draw finalized; pending requests cannot change or reroll. |
| Canonical artwork base, module/helper implementations, core strategy/adapter identity | Fixed after sealing. Bounded policy/geometry changes are not a replacement algorithm or arbitrary proxy upgrade. |
| Future activation/growth minima | ProtocolPolicy allows reviewed USD18 minima>=1USD, growth<=activation; defaults100/5USD. Stronger pool minima and marginal LP floors remain. A smaller minimum changes future participation economics; no deployment/test action is implied. |
| Exceed normal10% loss ceilings or lower hybrid main below60% | No such configured path. Defaults2%/1%/3% loss; main floor may rise6000–9999bps or choose single mode. |
| Redeem principal, reroll rarity, overwrite owners/reward balances, sweep liabilities | Not supported. Governance configuration is not permission to manufacture those operations. |
| Add arbitrary pair conversion, hooks, chains, cross-chain canonical replacement or post-halt recovery | Not made functional just by adding an address. Complete missing design, source support, independent review and rehearsals before relying on it. |

Future changes must preserve this distinction: what can be configured now, what requires new compatible code, what has actually been qualified, and what cannot be recovered. Do not describe a possible new deployment as a repair guaranteed to work with every already sealed predecessor.

<a id="callable-contract-reference"></a>

## Callable contract reference: reads, writes, inputs and outputs

Open the [complete callable-function reference](CONTRACT_FUNCTIONS.md). It is
grouped by contract, with a navigation index and separate read/write tables.
Each entry records the concise purpose, required caller, exact argument and
return types, tuple fields and relevant safety limitations. Constructors and
native-ETH receive hooks are included separately; internal-only libraries are
not callable deployed contracts.

- **Read:** `view`/`pure` does not submit a transaction. A read can still fail on
  stale prices, missing history, retired lifecycle or dependency faults.
- **Write:** a successful transaction changes state. Many writes return nothing;
  their result is confirmed state/events, not an invented output value. A return
  value from a simulated write does not prove the transaction later succeeded.
- **Inputs:** token/native amounts are raw integer units unless explicitly USD,
  BPS, ticks or timestamps. Native ETH sent with a payable call is a separate
  transaction `value`, not an ABI argument. Gas is always separate.
- **Permission:** external/public ABI visibility does not grant operator access.
  Holder, governance, keeper, parent-module and authenticated-callback roles
  remain distinct. Use the linked procedure before signing a consequential call.
- **Addresses:** this is a source reference, not the production address book.
  Verify chain, deployed version, runtime, bindings and [address inventory](DEPLOYMENT_ADDRESSES.md)
  first. Do not call current ABIs against historical local deployments.

The source-bound [generation/check procedure](CONTRACT_FUNCTIONS.md#maintenance)
must accompany future function, permission, parameter, output or behavior changes.
No read or write is executed by generating this reference.


## Prepare and check an offline reviewHash

The [local helper](../scripts/prepare-operator-review.py) now generates a
reproducible review reference and **ordered explorer inputs**. It is not a live
state reader, fee/range planner, simulation service, signer, raw calldata builder
or Safe transaction JSON. It creates no network transaction and never loads a
private key. `ready_for_submission` and all live qualification flags stayfalse.

Start from a deliberately non-submittable example: [mode off](../config/operator-review.mode.example.json),
[close residual](../config/operator-review.residual-close.example.json) or
[emergency consolidation](../config/operator-review.emergency.example.json).
Replace every placeholder using the actual reviewed deployment and current
`profile` output. The examples contain no valid deployment addresses or chosen
execution minimums; they are rejected until completed. Runtime hashes and
contract custody/portfolio fingerprints use their documented Ethereum hashing,
not this helper's SHA256 review convention.

From the repository root, with the supported Python environment:

```sh
python scripts/prepare-operator-review.py profile --output operator-profile.json
python scripts/prepare-operator-review.py prepare reviewed-request.json --output operator-review.json
python scripts/prepare-operator-review.py check operator-review.json --output operator-check.json
```

Each output path must be **new**. Files are written as UTF-8; existing files are
never overwritten. Avoid a shell redirection whose encoding may vary. On failed
write, retain evidence and do not use a partial artifact. Validation/source
refusal creates no output. A successful `check` proves only local consistency,
not authority, current chain state, freshness, execution quality or simulation.

Prepare the request as a strict JSON object with exactly these fields:

| Field | Required value and where it comes from |
| --- | --- |
| `schema` | JSON integer1. |
| `profile`, `reference_sha256`, `source_snapshot_sha256` | Copy exact values from `profile` for the reviewed local release. It checks local source/dependency/build pins; this does not authenticate a downloaded release or deployed address. |
| `chain` | Object: `id` (decimal string), `controller`, `governance`, `target` (lowercase nonzero addresses), `target_runtime_keccak256` (lowercase nonzero32-byte0x hash). Read/verify from the real deployment independently; these supplied values are not verified by this offline tool. |
| `snapshot` | Object: `block_number` and `timestamp` as decimal strings, `block_hash` as lowercase nonzero32-byte0x hash. Supply one actual confirmed snapshot; the tool does not determine finality or current age. |
| `contract` | Exact source name, e.g. `ZZZPortfolioPolicy` or `ZZZMigration`. |
| `signature` | Exact full canonical signature, not only its name. For example `setMode(bytes32,bool,bytes32)`. Overloads/tuples use the complete ABI signature in the callable reference. |
| `arguments` | Object with every named input and no extra fields. A struct is another named object. Use **decimal strings for every ABI integer**, JSONtrue/false for bools, canonical lowercase hex for addresses/bytes and source names/order from the reference. No approximate USD numbers or scientific notation. |
| `review_notes_sha256` |64 lowercase hex characters without0x, hashing the retained human review record. Keep the record separately. No secret, password, endpoint or arbitrary narrative belongs in this field. |
| `evidence_sha256` |1–16 unique64-character lowercase SHA256 digests without0x for the retained reads/simulation/supporting evidence. Supplying a digest does not prove its content or quality. |

For a mode change the `arguments` object has `pool`, `next`, `reviewed`; set the
last field to the literal string **`$REVIEW_HASH`**. For residual close it has
one `r` object with every ParkingRequest field. Emergency uses one `request`
object with every EmergencyRebalance field. Copy actual ABI labels, not a guessed
`request` name for every struct. All exact `bytes32` fields called `reviewHash`
or `reviewed` use that marker. Never use it for the independently read
`portfolioHash`, `custodyHash`, a runtime hash or a pool ID.

The helper replaces markers only in the ordered explorer output; the retained
manifest still contains them, avoiding a self-referential hash. Its convention is
SHA256 of ASCII domain `ZZZ_POPL_OPERATOR_REVIEW_V1` followed by LF, then canonical
ASCII JSON with sorted keys, comma/colon separators and no floats/trailing LF.
The result is `0x` plus64hex digits. **The contract does not mandate this scheme**:
it checks a nonzero provenance value and records it, not the review preimage.
This is not the transaction hash or a contract-produced custody fingerprint.

Review `explorer.argument_order`, recursively ordered `explorer.arguments` and
the actual catalog access description, then perform the separate complete live
simulation/authority/deployment checks. An ABI-visible fixed-module/callback
function is still not human-callable. Do not import this artifact as a ready Safe
transaction or send it to a public wallet API. Any source/catalog/argument/evidence
change requires a new artifact. Never update pins blindly merely to make it pass.

The helper has strict size/depth/array/byte limits, so it is not intended to
prepare an arbitrarily large handoff batch. Split only along actual contract
cursor/batch rules. It checks Solidity types and precision, **not** contextual
limits such as same-value mode, minimum receipts, tick spacing, supported route,
actual owner, sufficient balances, deadline freshness or lifecycle readiness.

Use a private local directory for operation records, evidence, receipt and final
state verification; never commit keys, credentialed endpoints or journal state.
Publishing a review hash does not attest the keeper host or eliminate governance
trust. No particular operator wallet type, extra person or timelock is required.

## Manual write input catalog

This index is for the reviewed fresh candidate; **production is not approved**. Resolve exact chain, controller, contract/runtime and ABI first. Each signature preserves argument order. Named structs use their source type; follow the function-reference link for every nested field in canonical ABI order. The detailed task procedure and actual function guards remain mandatory.

**Configuration authority:** `G` means Access.canConfigure: before seal **only bootstrap**, not a distinct governance wallet; after seal **only current governance**, canonicalState0/no preparation. Additional lifecycle/body guards still apply. `B` means pre-seal bootstrap only. A global pause alone does not block normal configuration. Other permissions are stated per row; a public function is not automatically operator-callable.

All amounts are raw currency units unless explicitly USD18/BPS/ticks/seconds; ETH uses wei, token uses reviewed decimals, liquidity minimum is raw Uniswap L. A deadline is Unix seconds, execution time through at most600seconds ahead. All transactions pay gas separately. Where required, `reviewHash` is a nonzero commitment to a review, not permission, timestamp, signature or proof of safety; the documented automatic-range disable explicitly accepts zero unused fields.

Only ordinary on-chain configuration generally needs no keeper restart. Local source/config/runtime/API pins need controlled matching restart, original journals retained. Stop/reconcile the automated signer before manual same-key nonce use. Preserve hashes, receipts, spent gas and pending intents; never reset history or resend an ambiguous action.

### Permission boundary and completeness

The historical manual-operation audit classified231 mutable ABI functions and90 manual endpoints. Current additions are documented in the [future operating settings](#future-operating-settings) section and the regenerated source-bound callable reference; those historical counts are not current coverage totals. Fixed module-only methods/callbacks are not manual alternatives to the listed parents. Holder NFT transfers/approvals, activation, growth and reward claims remain owner/payer flows described in the callable reference. Constructors/sealing choose immutable identities; no current method grants a generic sweep, arbitrary recipient, new principal token or bridge.

### ZZZAccessController

[Procedure](#authorities) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzaccesscontroller)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `acceptGovernance()` | Pending nonzero governance wallet only, operating canonical state and no preparation. | The exact proposed wallet accepts authority atomically and clears the proposal. Not a rollback. The newly accepted wallet must propose/complete a later handover. |
| `bind(bytes32 id, address implementation)` | Bootstrap only, before seal. | Bind one of the16 supported core module slots exactly once before seal, verifying deployed code and matching controller. One-time module binding; no replacement/unbind. Wrong binding requires a fresh deployment. |
| `cancelPreparation(bytes32 noticeHash)` | Current governance directly while the exact preparation is active and canonical state is operating. | Cancel the exact active preparation notice while the source is still operating. Ends only the exact notice before freeze. New preparation is a new reviewed nonce. |
| `proposeGovernance(address candidate)` | Current governance only, canonical operating state and no preparation. Controller-self/current-wallet candidates reject. | Propose a governance-wallet replacement without a delay; zero cancels a proposal. Zero candidate cancels a pending proposal; candidate must accept to gain authority. |
| `seal()` | Bootstrap only, once. | Irreversibly close bootstrap after complete unique module/companion, randomness and matching nonzero fixed contribution/exit ZZZ bindings are validated. Irreversible. Clears bootstrap; no unseal/upgrade or deployment reset. |
| `setGuardian(address who, bool enabled)` | G. | Grant or revoke guardian pause authority and emit GuardianChanged for the resulting state. Apply the opposite grant after reconciling incidents; guardian grants pause-only power. |
| `setKeeper(address who, bool enabled)` | G. | Grant or revoke bounded keeper maintenance authority and emit KeeperChanged. Apply the opposite grant; preserve pending signer/nonces/spend state before key rotation. |
| `setPaused(bool state)` | Current governance, bootstrap before seal, or an enabled guardian for state=true only. Canonical lifecycle guards remain independent. | Set or clear ordinary global pause. Governance may unpause; guardians cannot. Does not undo preparation, freeze or LP exit. |
| `startPreparation(ZZZAccessController.PreparationNotice notice)` | Current governance directly, sealed canonical operating state. | Announce a cancellable same-chain replacement/draining window; no custody or rights leave. Use cancelPreparation(exact preparationHash) before freeze; no funds or rights move here. |

### ZZZActivationAssets

[Procedure](#activation-assets-and-routes) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzactivationassets)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `configureZZZ(address token, bytes32 expectedCodeHash, bytes32 reviewHash)` | B; unavailable after seal. Additional guards: unset fixed ZZZ identity and valid current code/decimals/dual pricing. | Configure the fixed ZZZ ERC20 once before sealing and record its validated source policy. One-time fixed token. No replacement; issuer migration uses holder exit and a fresh deployment. |
| `setAsset(address token, bool enabled, bytes32 expectedCodeHash, bytes32 reviewHash)` | G. | Append and activate same-identity source enablement/runtime policy. Append disabled policy to stop; re-enable only through validated new policy. No third input. |

### ZZZActivationEntry

[Procedure](#activation-assets-and-routes) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzactivationentry)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `addRoute(ZZZActivationEntry.RoutePolicy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Append and enable an immutable typed-v3 route whose original source is the fixed reviewed ZZZ. Append-only identity. Disable the route; do not overwrite it under the old ID. |
| `addV4Route(ZZZV4RouteExecutor.Policy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Append and enable a reviewed hookless typed-v4 route for an original ETH/ZZZ source. Append-only typed route. Disable it to stop; no generic callback/recipient authority. |
| `setRouteEnabled(bytes32 id, bool enabled)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Enable a reviewed route only for an allowed ETH/ZZZ source, or disable it without calling a failing token/router/pool. False stops without upstream checks; true fully revalidates. Mined executions stay final. |

### ZZZBuyback

[Procedure](#tune-or-stop-buyback-trading) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzbuyback)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `execute(address token, uint256 amount, bytes32 poolId, uint256 deadline)` | Authorized keeper; live/operating. Original keeper authorization and unpaused state are rechecked after external work. | Release classified buyback reserves, acquire ZZZ if necessary, then verify an actual supply-reducing burn. No undo of a completed burn. Change reviewed task/operating limit before the next trade. |
| `setOperatingTradeUSD(uint256 limit)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Adjust the future per-trade buyback budget within the reviewed governance maximum. Zero stops all new burns; restore a reviewed positive value no higher than reviewed maxTradeUSD. |

### ZZZCanonicalHandoff

[Procedure](#whole-collection-replacement) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `abort()` | Selected source governance wallet directly, with the function's exact sealed/canonical phase and backing guards. | Begin pre-commit cancellation of a frozen handoff and permanently cancel the importer. Begin abort, return every funded leg and finishAbort only after full restoration. |
| `commit()` | Selected source governance wallet directly, with the function's exact sealed/canonical phase and backing guards. | Atomically retire the source and activate its one fully funded compatible successor. Irreversibly retires source and activates successor; no post-commit abort/revival. |
| `completeImport()` | Permissionless after complete source-authenticated import. | Verify every imported count/root and mark the successor ready for backing. Does not activate successor. Complete exact funding, then source governance commit. |
| `exportRows(uint8 slot, uint256 count)` | Permissionless in the export phase. | Commit a bounded ordered batch of source records into the canonical snapshot root. Continue on-chain exported cursor; rows/root remain authenticated, not editable relay input. |
| `finishAbort()` | Selected source governance wallet directly, with the function's exact sealed/canonical phase and backing guards. | Reactivate the original source only after every sent leg is fully restored and validated. Source resumes only after verified backing restoration; deliberate pause/service state still needs review. |
| `freeze()` | Selected source governance wallet directly, with the function's exact sealed/canonical phase and backing guards. | Freeze ownership/accounting and atomically capture six source-domain cutoffs for the reviewed sealed importer. Use abort/complete exact restoration before finishAbort, or complete commit; unpause alone cannot undo it. |
| `fund(uint8 slot, uint256 index)` | Permissionless in funding phase after completed import. | Transfer one exact classified source backing leg to the matching successor module. Return the exact funded leg only through an authenticated source abort; no free recipient. |
| `importRows(uint8 slot, bytes[] records)` | Permissionless relay in importer phase. | Import source-authenticated ordered records into the inert successor. Continue exact imported cursor with authentic exported bytes; do not infer or renumber rows. |
| `prepareImport(address sourceController)` | That deployment’s bootstrap before sealing. | Mark an unused unsealed successor as an inert same-chain importer for one source controller. One-time importer binding before seal; cancelled importer is not ordinary live recovery. |
| `returnFunds(uint8 slot, uint256 index)` | Permissionless during source abort, exact funded/unreturned leg. | Recover one previously funded leg from a cancelled importer and restore source classification. Continue until every funded leg is returned; no private/manual transfer substitutes for acknowledgment. |
| `settle(uint8 slot)` | Permissionless with the exact phase/cursor. | Settle exactly the next captured canonical domain before export/funding. Continue exact slot order. Do not repeat/skip acknowledged domain settlement. |

### ZZZCompounder

[Procedure](#coordinate-compounding-with-rebalancing) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzcompounder)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `compound(uint256 id, uint128 minimumLiquidity, uint256 deadline)` | Authorized keeper; live/operating. Original keeper authorization and unpaused state are rechecked after external work. | Ask Vault to reinvest one bucket’s designated compound reserve and attributed idle. No undo. Failed compound reverts; stop scheduling/revoke keeper for containment, not interval=0. |

### ZZZLPBalancer

[Procedure](#add-or-remove-an-execution-pool-after-sealing) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzlpbalancer)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `configureExecutionPools(bytes32[] pools, bytes32 reviewHash)` | G. Additional guards: operating canonical lifecycle and no preparation, no terminal LP exit. | Replace the complete bounded list of reviewed admitted execution pools. Replace entire reviewed list; empty list disables swaps without price reads, with no implicit fallback. |
| `configureSolver(uint8 iterations, uint32 gasLimit, bytes32 reviewHash)` | G. Additional guards: operating canonical lifecycle and no preparation, no terminal LP exit. | Change bounded quote search/gas policy, advancing executionRevision. Reconfigure within fixed bounds after complete-operation gas/sizing review; old work must be reconciled. |

### ZZZLPRewardConverter

[Procedure](LP_ETH_SETTLEMENT.md#operator-procedure) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzlprewardconverter)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `addRoute(ZZZRewardConverter.RoutePolicy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Append a reviewed immutable single-hop v3 exact-input route into native ETH via the fixed wrapper. Append-only identity. Disable the route; do not overwrite it under the old ID. |
| `addV4Route(ZZZV4RouteExecutor.Policy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Append a reviewed typed hookless static v4 route into actual native ETH. Append-only typed route. Disable it to stop; no generic callback/recipient authority. |
| `configureWrapper(ZZZRewardConverter.WrapperPolicy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Review the existing immutable WETH wrapper’s runtime/proxy policy for exact unwrap paths. Wrapper identity is constructor-fixed. Policy can be re-reviewed, not repointed to another asset. |
| `setConversionLossBps(uint16 value)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Set the permitted future conversion loss beneath the hard 10% ceiling. Reconfigure within0–1000bps; cannot relax stronger caller minimum or repair a failed route. |
| `setEnabled(bool value)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Stop or reopen this converter without querying dependencies. False is a dependency-independent converter stop. True does not qualify routes or clear pending work. |
| `setRouteEnabled(bytes32 id, bool value)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Disable or re-enable one admitted conversion route. False stops without upstream checks; true fully revalidates. Mined executions stay final. |

### ZZZMigration

[Procedure](#custody-and-lp-migration) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzmigration)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `allocatePrincipal(uint256 maximum)` | Anyone in canonical operating state, not preparing; requires Allocating phase. | Advance deterministic proportional principal apportionment over bounded captured mint ordinals. Continue bounded cursor. Allocation is irreversible; complete every bucket before Ready. |
| `beginCollectiveExit(bytes32 reviewHash)` | Current governance through controller; sealed, paused, canonical operating and not preparing. | Validate every funded bucket and captured mint inventory, then irreversibly start collective principal return. Irreversible global principal retirement. Does not close or pay all holders in this first call. |
| `closeBucket(uint256 bucket, uint256 minimumETH, uint256 minimumZZZ, uint256 deadline)` | Current governance; terminal exit in Closing, paused and canonical operating. | Final-harvest and close one captured bucket into exact ETH+ZZZ settlement backing. Continue remaining buckets. No swaps; preserve raw minima/phase/backing on failure. |
| `closeResidual(ZZZMigration.ParkingRequest r)` | Selected governance only; sealed/globally paused, operating canonical lifecycle without preparation or terminal LP exit; nonreentrant. | Manually remove only the reviewed residual LP into Vault idle while preserving the main and all NFT rights. No reverse transfer to a recipient. Main remains; idle can be redeployed by guarded ordinary/emergency maintenance. |
| `configureZZZ(address token, bytes32 codeHash, bytes32 reviewHash)` | B; unavailable after seal. Additional guards: nonReentrant, unset fixed ZZZ identity matching source admission, Rewards and immutable Buyback. | Bind the fixed ZZZ token once before sealing, matching source admission, Rewards admission and immutable Buyback. One-time fixed token. No replacement; issuer migration uses holder exit and a fresh deployment. |
| `distributePrincipal(uint256[] ids)` | Anyone; Ready phase and canonical operating lifecycle, not preparing. Ordinary pause does not block payouts. | Attempt automatic principal pushes to current NFT owners in isolated bounded subcalls. Retry unpaid/deferred IDs only. Successful payment is never due again; ownership follows NFT until paid. |
| `emergencyRebalance(EmergencyRebalance request)` | Current governance only; sealed/paused, operating, no canonical preparation/import/retirement or terminal LP exit. Nonreentrant; not a keeper fallback. | Manually close/optionally swap/redeploy one shared LP while globally paused, under an exact custody-bound manifest. No automatic retry/fallback. Paused governance explicitly reviews every retained financial check and final backing. |
| `invalidateParking(uint256 id)` | Drain-authorized governance before irreversible LP exit. | Advance the shared bucket nonce to invalidate unused parking and residual-close reviews. Advances shared nonce; rebuild fresh park/residual review. Does not move funds or cancel mined custody. |
| `moveFunds(uint256 id, bytes32 pool, uint128 minimum, uint256 deadline)` | Current governance; live and before irreversible LP exit. | Atomically move a live shared LP to an admitted native ETH/fixed-ZZZ pool with identical actual currencies. A later guarded move/park may reverse direction if occupancy/capacity permit; not an undo. |
| `park(ZZZMigration.ParkingRequest r)` | Drain-authorized governance while globally paused,before terminal exit; nonreentrant. | Harvest/close both exactly reviewed LP legs into Vault idle without releasing custody. Unpause and guarded resume after review; principal stays in Vault. Parking does not withdraw to governance. |
| `resume(uint256 id, bytes32 pool, uint128 minimum, uint256 deadline)` | Current governance; live and before irreversible LP exit. | Deploy a locally parked bucket into an admitted same-actual-pair LP. A later paused park may close again; verify destination reservation/deposit ordering first. |

### ZZZMigrationBudget

[Procedure](#typed-conversion-and-loss-limit-operations) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzmigrationbudget)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `setCompoundInterval(bytes32 poolId, uint32 interval)` | G. Additional guards: nonReentrant, no preparation/canonical lock or active captured snapshot. | Configure a pool standalone-compound interval without changing backing or recorded clocks. Minimum600seconds, never zero. Stop automation separately; change does not reset recorded clocks. |
| `setLossLimits(uint16 contribution, uint16 maintenance)` | G. Additional guards: nonReentrant, no preparation/canonical lock or active captured snapshot. | Set contribution and maintenance caps for future operations within hard 10% maxima. Read/preserve the other value. Future operation only; captured caller and operation floors remain. |

### ZZZNFT

[Procedure](#mint-and-metadata) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzznft)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `addRoyaltyAsset(address token)` | G. | Append an admitted ERC20 royalty payment currency to the NFT-bound ledger. Permanent at-most16ERC20+ETH list. No remove/sweep or arbitrary conversion of quarantined funds. |
| `finalizeTraits(uint256 id)` | Anyone; canonical accounting must be operating. | Finalize the next mint-ordered revealed rarity/palette/pattern from its verified stored words. Original fulfilled draws only, in mint order. Missing provider response cannot be fabricated. |
| `refreshMetadata(uint256 id)` | Anyone; no NFT ownership required. | Emit an ERC4906 notification for an existing NFT. Notification only; no trait/root change and no promise marketplace cache refreshes immediately. |
| `refreshMetadataRange(uint256 firstOrdinal, uint256 lastOrdinal)` | Anyone. | Emit one ERC4906 notification per actual NFT in a bounded ordinal interval. At most50 inclusive mint ordinals, not token IDs. Notification only. |
| `setBaseURI(string baseURI)` | B; unavailable after seal. Additional guards: empty/unconfigured base and valid nonempty IPFS/Arweave root. | Populate an initially empty immutable artwork root once before sealing. One nonempty IPFS/Arweave root before seal; no URI replacement afterward. |
| `setMintPaused(bool state)` | G. | Stop or resume new NFT issuance/randomness requests independently. False reopens only new mints when all other guards pass. Pending fulfillment/finalize remains separate. |

### ZZZOracle

[Procedure](#configure-stop-and-recover-usd-pricing) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzoracle)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `setDualFeed(address token, ZZZOracle.SourcePolicy primary, ZZZOracle.SourcePolicy secondary, uint16 maxDeviationBps, bytes32 reviewHash)` | G. | Append and immediately activate a fully reviewed independent two-source USD policy for an asset. Append/review a healthy independent pair; old policy is immutable history, not overwritten. |
| `setSequencerFeed(address source, bytes32 expectedCodeHash, bytes32 reviewHash)` | G. | Replace the uptime dependency with a newly reviewed nonzero source without reading the broken old source. Nonzero reviewed replacement only; cannot remove uptime protection or waive grace. |

### ZZZPoolRegistry

[Procedure](#pool-admission-and-retirement) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzpoolregistry)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `configureNative(PoolConfig config)` | G. Additional guards: exact nativeConfiguration admission/terminal-exit guards and full venue validation. | Admit or reconfigure a reviewed static hookless native ETH/fixed-ZZZ pool, including compatible future fee tiers. Reconfigure complete reviewed config; no token/core change. Post-exit admission is Ready/reserve-only. |
| `disablePool(bytes32 poolId, bool disableDeposits, bool disableOperations)` | G. | Stop new deposits and/or ordinary operations on an admitted pool without querying external tokens, venue or prices. True only clears flags; false preserves. Reopen with full configureNative validation. |

### ZZZPortfolioPolicy

[Procedure](#portfolio-management-controls) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `configureResidualSide(bytes32 pool, uint16 next, bytes32 reviewed)` | G. Additional guards: operating canonical lifecycle and no preparation, no terminal LP exit. | Choose residual extent toward the corresponding new-main boundary. Per-pool desired geometry. Enabled same-value review advances revision; no immediate placement/rollback. |
| `setMode(bytes32 pool, bool next, bytes32 reviewed)` | G. Additional guards: operating canonical lifecycle and no preparation, no terminal LP exit. | Select desired single/hybrid mode; disabling requests a guarded merge instead of deleting a live residual. Desired mode only; false requests ordinary guarded merge. No per-residual pause, arbitrary withdrawal or immediate exit. |
| `setTriggerBps(uint16 next, bytes32 reviewed)` | G. Additional guards: operating canonical lifecycle and no preparation, no terminal LP exit. | Change ordinary edge-threshold fraction in single and optional hybrid mode. Global threshold1–10000bps of centre-to-edge distance. Reconfiguration resets samples, not geometry exemption. |

### ZZZRebalanceConfirmation

[Procedure](#configure-rebalance-confirmation) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `configure(uint32 secondsRequired, uint32 maximumGap, bytes32 reviewed)` | G. Additional guards: operating canonical lifecycle and no preparation, no terminal LP exit, nonReentrant. | Configure the sampled window and maximum gap, advancing policy revision so earlier samples cannot authorize the new policy. Duration60seconds–7days; gap0 stops the sampled market path, not the deliberate geometry exception; otherwise <=duration/2. Old samples reset. |
| `observe(uint256 bucket)` | Authorized keeper; sealed/unpaused, operating canonical lifecycle and no principal exit; nonreentrant. | Record threshold sample during/after cooldown; reset for changed side/identity,excessive gap,no candidate or caught fault. Recorded sample, not swap or rebalance. On observed failure reset succeeds; preserve pending/hash provenance. |
| `resetObservation(uint256 bucket)` | Authorized keeper; operating canonical lifecycle and no principal exit. Ordinary global pause is allowed; nonreentrant. | Delete recorded bucket evidence after an observed incident so it cannot be extended on recovery. Clear-only keeper operation, allowed during ordinary pause; not an eligibility/budget override. |
| `setRequireReferenceExit(bool required, bytes32 reviewed)` | G. Additional guards: operating canonical lifecycle and no preparation, no terminal LP exit, nonReentrant. | Set reviewed independent-reference corroboration policy and monotonically invalidate old samples. Weakening independent corroboration is explicit governance risk. Re-enable only after automatic range policies disabled. |

### ZZZRewards

[Procedure](#revenue-operations) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzrewards)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `addAsset(address token)` | G. | Append a reviewed LP reward currency within the bounded admission inventory. Permanent at-most32ERC20+ETH LP payout history; cannot remove liabilities or admit new principal inputs. |
| `bindConverter(address candidate)` | B; unavailable after seal. Additional guards: economic canonical state0, nonReentrant, one-time unused converter slot and exact ledger/controller bindings. | Bind the one fixed LP-reward-to-ETH executor before sealing. One-time before seal; routes/policy remain governed but bound implementation cannot be replaced. |
| `convertBatch(address token, uint256[] ids, bytes32 routeId, uint256 minimumETH, uint256 deadline)` | Authorized keeper; live/operating economic state. | Swap selected NFTs’ already allocated ERC20 LP rewards into ETH and credit the same NFTs. Keeper only, sorted unique at most32NFT IDs. The same NFTs retain exact converted credit; current owners hold the rights; this is not income or claim. |

### ZZZRoyaltyConverter

[Procedure](ROYALTY_SETTLEMENT.md) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzroyaltyconverter)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `addRoute(ZZZRewardConverter.RoutePolicy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Append a reviewed immutable single-hop v3 exact-input route into native ETH via the fixed wrapper. Append-only identity. Disable the route; do not overwrite it under the old ID. |
| `addV4Route(ZZZV4RouteExecutor.Policy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Append a reviewed typed hookless static v4 route into actual native ETH. Append-only typed route. Disable it to stop; no generic callback/recipient authority. |
| `configureWrapper(ZZZRewardConverter.WrapperPolicy policy)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Review the existing immutable WETH wrapper’s runtime/proxy policy for exact unwrap paths. Wrapper identity is constructor-fixed. Policy can be re-reviewed, not repointed to another asset. |
| `setConversionLossBps(uint16 value)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Set the permitted future conversion loss beneath the hard 10% ceiling. Reconfigure within0–1000bps; cannot relax stronger caller minimum or repair a failed route. |
| `setEnabled(bool value)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Stop or reopen this converter without querying dependencies. False is a dependency-independent converter stop. True does not qualify routes or clear pending work. |
| `setRouteEnabled(bytes32 id, bool value)` | G. Additional guards: operating canonical lifecycle and no preparation, nonReentrant. | Disable or re-enable one admitted conversion route. False stops without upstream checks; true fully revalidates. Mined executions stay final. |

### ZZZRoyaltyRewards

[Procedure](#marketplace-currency-and-eth-payouts) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `bindConverter(address candidate)` | B; unavailable after seal. Additional guards: economic canonical state0, nonReentrant, one-time unused converter slot and exact ledger/controller bindings. | Bind one reviewed royalty-only ETH conversion executor before sealing. One-time before seal; routes/policy remain governed but bound implementation cannot be replaced. |
| `convertBatch(address asset, uint256[] ids, bytes32 routeId, uint256 minimumETH, uint256 deadline)` | Authorized keeper, sealed canonical NFT and live economic/operation state. | Convert selected earned royalty balances in one swap and credit ETH to those same NFTs. Keeper only, sorted unique at most32NFT IDs. The same NFTs retain exact converted credit; current owners hold the rights; this is not income or claim. |
| `forwardLate(address asset)` | Permissionless after authenticated canonical retirement. | Forward post-cutoff royalties from a retired receiver to its one immutable immediate successor. Retired source only; forward current receipts to its authenticated immediate successor, no chosen recipient. |
| `fund(address asset, uint256 amount)` | Permissionless funder in active economic state. | Pull an exact ERC20 royalty donation and synchronize its actual receipt. Transfers actual admitted royalty currency as revenue; no fabricated balance or principal/activation authority. |
| `sync(address asset)` | Permissionless in active economic state. | Recognize actual newly arrived royalty funds and advance that currency’s eligible-weight index. Assign actual newly received currency to existing eligible cohort; no LP harvesting or swaps. |
| `syncAll()` | Permissionless in active economic state. | Synchronize every admitted royalty currency using normal accounting checks. Reads every admitted royalty currency. One failing sync may revert; use source-specific sync/recovery, not guessed zero. |

### ZZZStrategy

[Procedure](#range-and-strategy) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzstrategy)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `applyKeeperRange(bytes32 poolId)` | Enabled keeper; sealed, unpaused normal canonical operation with no preparation. | Apply the currently eligible preapproved width selected by keeperRangeTarget. Disabled in selected manual policy. Separate opt-in chooses only approved2500/5000, never arbitrary width. |
| `setAdditionalLossBps(uint16 limit, bytes32 reviewHash)` | G. Additional guards: operating canonical lifecycle and no preparation. | Set the extra oracle-relative loss limit after actual directional core fees. Separate additional-after-directional-fee guard; keep gross loss/caller/spot/oracle floors distinct. |
| `setKeeperRangePolicy(bytes32 poolId, bool enabled, uint16 narrowTriggerBps, uint16 widenTriggerBps, uint32 minInterval, bytes32 reviewHash)` | G. Additional guards: operating canonical lifecycle and no preparation. | Enable/disable reviewed on-chain switching between ±25% and ±50% in the approved price orientation. Selected operating policy keeps disabled. Disabling does not restore old physical ticks or erase pending hashes. |
| `setRangeOrientation(bytes32 poolId, uint8 orientation)` | G. Additional guards: operating canonical lifecycle and no preparation. | Select explicit raw or inverse price orientation for future target range calculations. Physical ticks are not reinterpreted. New orientation disables automatic policy and requests guarded new geometry. |

### ZZZVault

[Procedure](#manual-rebalance-at-a-chosen-time) · [Exact ABI, tuple fields, inputs and outputs](CONTRACT_FUNCTIONS.md#zzzvault)

| Function and ordered inputs | Authorized caller / lifecycle | Result and reversal boundary |
| --- | --- | --- |
| `collectFees(uint256 id, uint256 deadline)` | Permissionless while live and canonical accounting is active. | Collect actual main/residual venue fees and fund one bucket80/10/5/5 allocation. Permissionless single shared-bucket harvest; no fixed split override, swap, compounding, burn or claim. |
| `rebalance(uint256 id, uint128 minimumLiquidity, uint256 deadline)` | Wallet must be keeper-authorized, including governance if it calls directly; live/operating and on-chain eligibility/cooldown required. Original keeper authorization and unpaused state are rechecked after external work. | Replace complete shared portfolio after guarded edge-threshold/sample readiness and fee settlement. Keeper capability required even for governance. Ordinary eligibility/confirmation/cooldown/budgets remain. |
| `reservePool(bytes32 pool, uint256 bucket)` | G. Additional guards: no terminal LP exit. | Permanently associate an admitted pool with a reviewed bucket identity, including a valid first-activation reservation. An empty initial bucket must equal `VaultCanonical.bucketIdentity(pool)`; a move uses the intended already-active bucket. Matching repeat is idempotent; no unreserve/delete repair. |

### Out-of-catalog manual operations

Provider subscription funding/consumer registration, OpenSea product/receiver setup, DNS/TLS/service users/monitoring, RPC credentials, wallet/Safe owner recovery, metadata pinning and software/backup operations are external operational procedures, not extra contract endpoints. Follow the linked service, mint and recovery procedures; no actual production addresses/service names are invented here. No public signing, deployed service change or restart is authorized by this catalog.


## Future operating settings

Accounting6 uses the separately predeployed **ProtocolPolicy1** helper and
PortfolioPolicy2. [Exact semantics, defaults and limitations](ADAPTABLE_POLICY.md).
The module address is fixed after seal; bounded values remain configurable.
Use the governance wallet (bootstrap before sealing), confirmed state, matching
ABI/runtime pins, meaningful nonzero reviewHash and exact unsigned simulation.
Configuration is blocked during preparation/canonical locks, including an
unsealed importer. Configure the successor **before** prepareImport.

| Target and function | Ordered inputs / units | Verify and recovery |
| --- | --- | --- |
| Access.bindProtocolPolicy | implementation address; deployed helper.access must match controller, version1 | Bootstrap only, once before consumers/seal. Verify ProtocolPolicyBound and getter. No later replacement/unbind; wrong binding needs fresh deployment. |
| ProtocolPolicy.setEntryPolicy | uint128 activationUSD, uint128 growthUSD, uint16 maxIdleBps, bytes32 reviewHash | Minima USD18, each>=10^18, growth<=activation; idle0–4000bps. Default100/5USD and500bps. Verify tuple/revision/EntryPolicyConfigured. Restore reviewed values with a new revision; old reviews stay stale. Stronger pool minimum and captured marginal LP floors remain. |
| ProtocolPolicy.setMaintenancePolicy | uint16 maxIdleBps, bytes32 reviewHash |0–4000bps, default500. Verify MaintenancePolicyConfigured/fingerprint. Relevant confirmation samples restart; does not transfer or reinvest idle itself. |
| ProtocolPolicy.setGasPolicy | uint32 payoutGas, uint32 sourceCallGas, uint32 royaltySyncGas, bytes32 reviewHash | Each100000–1000000; defaults180000/500000/250000. Verify GasPolicyConfigured/tuple and lean getters. Simulate actual owner/currency/provider and total transaction gas; reduce batch size if needed. No automatic widening and no change to earned backing. |
| ProtocolPolicy.setMintPrice | uint128 price, bytes32 reviewHash | Positive native wei; default50000000000000000. Verify MintPriceConfigured, Vault.mintPrice and fresh mint fingerprint. Future direct mints only; OpenSea drop gross/net integration still unqualified. |
| ProtocolPolicy.proposeMintRecipient | address candidate, bytes32 reviewHash | Candidate must be valid external payee, not accounting/custody module. Zero cancels. Verify pendingRecipient/revision/event. Proposal invalidates older mint reviews but moves no funds. |
| ProtocolPolicy.acceptMintRecipient | No inputs; candidate itself sends | Verify MintRecipientAccepted/current recipient/pending zero. No governance rights granted. To reverse, propose/accept a later payee; never rewrite past payments. |
| ProtocolPolicy.setEvolutionThresholds | uint128 enhancedUSD, uint128 singularityUSD, bytes32 reviewHash | USD18, 0<enhanced<singularity; defaults1000e18/10000e18. Verify metadata tuple and ERC4906 batch event; market caches may refresh later. Restore reviewed thresholds with new revision; no economic-right changes. |
| ProtocolPolicy.configureRandomness | address coordinator, bytes32 expectedCodeHash, bytes32 keyHash, uint256 subscriptionId, uint16 confirmations, uint32 callbackGas, bool nativePayment, bytes32 reviewHash | Initial setup only before seal and before importing, code/key/sub nonzero; provider runtime must match;3–200confirmations and200000–10000000callback gas. Qualify consumer/funding/provider proof/upgrade risk; verify configured tuple, generation0 and RandomnessConfigured. No invented live provider. |
| ProtocolPolicy.rotateRandomness | Same8 ordered inputs as configureRandomness | Post-seal planned rotation only; all draws finalized, principal activity not terminal. Stop minting, drain original requests, verify nextToFinalize=mintedCount+1, qualify/fund new subscription, simulate, execute, inspect generation/revision; then fresh request rehearsal and intentional mint resume. Failed original provider must recover before rotation; no reroll workaround. |
| ProtocolPolicy.setRandomnessRequestSettings | uint16 confirmations, uint32 callbackGas, bytes32 reviewHash | Configured provider, future requests only. Verify RandomnessSettingsConfigured and policy revision. Existing request payload/callback words remain unchanged. |
| PortfolioPolicy.configureMainAllocation | bytes32 pool, uint16 next, bytes32 reviewed |6000–9999bps, default6000. Verify minimumMainBps(pool), maximumResidualBps(pool), geometry/control revision and MainAllocationConfigured. Use setMode(false) for a one-position100% main. Pending geometry applies at the next guarded adjustment; existing residual remains accounted. |
| PortfolioPolicy.configureResidualGap | bytes32 pool, uint24 next, bytes32 reviewed | Positive number of full tick-spacings, default1; mathematical TickMath bound plus actual side feasibility. Verify ResidualGapConfigured/gap getter. Excessive gaps can block placement; lower deliberately or disable mode, never discard a live residual. |
| Buyback.setMaximumTradeUSD | uint256 limit, bytes32 reviewHash | Positive, <=uint128.max USD18, >=operatingTradeUSD. Verify event/current maximum. setOperatingTradeUSD(0) stops buys; lower operating first when lowering maximum. Fixed reserve ownership and ZZZ remain. |

Read all tuple fields with ProtocolPolicy.entryPolicy/maintenancePolicy/gasPolicy/
salePolicy/metadataPolicy/vrfPolicy. Their scoped fingerprints and configurationHash
are separate: sale+VRF bind mint reviews; entry binds contributions; maintenance
binds its execution; cosmetic/gas/sale changes do not reset unrelated LP evidence.
A reviewHash is provenance, not an execution fingerprint or on-chain permission.

Fresh direct mint calls `Vault.mintDormant(expectedMintPolicy)` with the exact
current price; read Vault.mintPolicyFingerprint **before** the wallet review.
Entry2 calls `executeReviewed(request,maximumLossBps,expectedContributionPolicy)`
using ProtocolPolicy.entryFingerprint. Stale reviews or mid-call policy changes
revert atomically. No local/public signer extension is included. Old Anvil selectors,
services, transaction hashes and recovery codecs remain historical and unchanged.

For a manual main width beyond±25/50, use the existing **complete**
PoolRegistry.configureNative tuple and preserve unrelated fields. rangeBps is the
human-price half-width, strictly<10000, with trigger/deviation below it, positive
aligned geometry and actual TickMath/execution feasibility. Width must exceed
100bps under the coupled admission rules. The old optional automatic two-width
policy remains distinct. Changed geometry applies only on the next guarded full
adjustment; it does not immediately remove LP or waive cooldown/confirmation.

On-chain policy changes need no service restart only for a **matching** source6
worker that reads them dynamically. Adopting accounting6/schema8/new runtime pins
requires separate reviewed installation/configuration and controlled restart;
editing this manual does not authorize one. Preserve pending hashes/journals and
reconcile nonce/receipts/spend before any operating change. Requalify gas/load,
minimum economics, wallet review and provider behavior after material tuning.

Fixed after seal: core/helper implementations, ETH/fixed-ZZZ identities, supply/
quotas/final traits/art root,80/10/5/5, royalty weights/5% request, exact shares/
backing/current-owner rights, terminal holder return, no external custody sweep/
bridge and normal10% loss ceilings. These are not operational knobs.
