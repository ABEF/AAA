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

For the complete permission map, see [who can call each class of function](ACCESS_PERMISSIONS.md).
Holder reward claims stay owner-controlled. Fresh custody5 restricts terminal
principal allocation and direct distribution to your governance wallet, which
pays each batch's gas. Keep keeper principal_distribution disabled; do not put
the governance key on its server. Old custody4 jobs/journals remain historical.

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

## Reconcile principal and reward rounding

For each NFT, value its shares of the actual main+residual holdings plus
attributed idle/designated compound. Sum each token amount before applying
its USD price; independently rounded subtotals may differ by a raw USD unit.
Never add liquidity units from different ranges or use historical deposits
as current LP value. Both legs remain counted while mode-off awaits merge.

LP rewards keep separate individual and collective sub-unit fractions. Do
not combine those fractions into a spendable unit or sweep the difference
between total liabilities and current claims. Claim only the exact funded
contract amount; failed USD reads do not prove a zero reward balance. Claims
and terminal principal payouts are not additional fee generation. See the
[receipt-model campaign](../reports/market-lifecycle-20261104/REVIEW.md). No new call or restart is required;
fresh custody5 still keeps terminal batches governance-only and holder reward
claims owner-controlled.

## Find the right procedure

Use [current profile identities](POSITION_V6.md) and [consolidated findings](AUDIT_FINDINGS.md)
when an older report conflicts with a procedure. Source publication does not
upgrade old services/sites or make an offline reviewHash a simulated transaction.

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
| Find every read/write, caller and example input | [Complete short call tables](#operator-call-tables) |
| Know what cannot be changed after sealing | [Fixed boundaries](#fixed-boundaries) |

## Current accounting6 deployment boundary

Fresh source uses Vault.ACCOUNTING_VERSION6, ProtocolPolicy1, Migration.CUSTODY_VERSION5,
Strategy maintenance3 / confirmation3 / portfolio2, Budget compound4, LP routing2,
emergency2, Access.GOVERNANCE_VERSION2 and
`SCHEMA()==keccak256("ZZZ_CANONICAL_SAME_CHAIN_ROYALTY_OPENING_V7")`.
Verify exact chain/runtime/module/helper pins and the [fresh profile](POSITION_V6.md).
Normal size/runtime gates, scoped offline checks and local actual-v4-core
integration pass within their [current Entry3 source scope](../reports/direct-entry-v3-20261103/VERIFICATION.md).
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
| Exact version, modules, helper runtimes and addresses | [Address inventory](DEPLOYMENT_ADDRESSES.md) and [schema12 preflight](PRODUCTION_PREFLIGHT.md), which observes17 modules/18 helpers; schema9/custody4, schema8/7/6 and older profiles are explicit historical inspection only. Observed code cannot approve its own runtime pin; retain creation-to-anchor policy history. |
| OpenSea primary mint and VRF | [Mint qualification](MINT_INTEGRATION_QUALIFICATION.md). Buyer gross 0.05 ETH, recipient net of actual platform fee, gas separate. Current direct mint still pays all 0.05 ETH; supported OpenSea/VRF integration is unfinished. |
| USD providers, proxy controls and update services | [Price security](PRICE_SECURITY.md), [service decisions](PRODUCTION_SERVICES.md) and optional [Pyth reader](PYTH_PRICE_SOURCE.md). Review upstream independence, update costs, funding and recovery; a matching ABI is not provider qualification. |
| Website read/unsigned review | [Served current3/fresh Entry3/accounting6 boundary](CURRENT_WEBSITE_PROFILE.md). Fresh profile6 readers are separate from the served accounting3 browser reader; source support is not a rollout. Neither accepts a historical accounting2 reader by relabeling. Matching Entry3 website consumer/service acceptance remains open; public DEPLOYMENT is null and signing Anvil-only. |
| RPC and exact frozen audit inputs | [Bounded RPC qualification](RPC_PREPARATION_QUALIFICATION.md) and [frozen review bundle](FROZEN_REVIEW_BUNDLE.md). A timeout is not proof of rejecting missing blocks; package export is not audit approval. |

Source-scoped audit results belong to [reports](../reports/README.md), not to a
second release history in this manual. The historical [October31 analysis](../reports/day-audit-20261031/VERIFICATION.md)
has463 contextually dispositioned findings at the unchanged final source closure;
its source scope does not verify later window/capacity code. Current source evidence is the [royalty-window review](../reports/royalty-launch-window-20261105/VERIFICATION.md). Older analyzer
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
Entry routing3 is direct ETH/ZZZ input with no pre-Vault conversion child; LP routing2 remains separate. Historical deployments are unchanged.

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

**If a reviewed replacement still fails:** do not loosen the final active-main
guard or repeat a known failing transaction. Fresh ordinary single/hybrid planning
now filters actual stored-tick activity before ranking, including initialized
downward crossings. Residual gap/rounding, bounded search, fees, depth, quote gas
and other financial/context checks can still block placement. Inspect the whole
post-close simulation, exact ticks, candidate list and each margin. Governance
may review and replace the complete execution list above with qualified compatible
alternatives, then re-simulate and reconcile pending work before a new submission.
This changes the swap list, not the LP destination, original ETH/ZZZ input or explicit
conversion/buyback requests. No global optimum or automatic fallback is promised.
An empty list disables swaps; no viable admitted venue leaves the operation
blocked. [Implemented repair and remaining qualification](../reports/lp-lifecycle-audit-20261102/REVIEW.md).

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
5. Refresh the schema10 release inventory with explicit `pricing_version: 2` and
   all20 helpers, including `Oracle.contributionPricing()` and its `oracle()`/
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

For `harvest_custody_unavailable`, compare the pinned Manager `ticks(lpId)` and
PosM `getPoolAndPositionInfo(lpId)`/owner for both actual legs. Stored geometry
must agree; Manager/child ticks forward to the same packed PosM record, so
`geometry_sources_independent:false` is deliberate. This is custody/geometry
coherence, not an independent stored ledger. No price feed or active-range
condition is required merely to harvest.
The report exposes validated main/per-leg ticks and its ProtocolPolicy version.
Keep the journal and current profiles intact; a report is not a transaction or an
instruction to alter geometry. [Exact diagnostic scope](KEEPER_COORDINATION.md#read-only-operation-review).

### Configure rebalance confirmation

The daemon now honors saved maturity/cooldown/jitter deadlines instead of
always adding the full outer interval. A recent validated head plus
monotonic elapsed time estimates local wake-up only; actual chain reads
still decide eligibility. Unknown/expired local anchors use normal polling;
overdue blocked candidates retry reads at most60seconds later without a
one-second busy loop. Pending recovery/global-error backoff remain unchanged.
Known incident clears precede unrelated router metadata checks; submission
still validates reviewed runtimes/authority/lifecycle/simulation/cost/nonce.
The15-minute initial enrollment lead is600+300seconds, not a15-minute window.
This source change needs a reviewed matching stop/reconcile/install/restart
through the existing recovery procedure. Keep deployment/profile/config and
pending/nonce/spend journal; no journal migration, reseal or setter is needed.
No running service was updated. [Audit](../reports/confirmation-audit-20261104/REVIEW.md).

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

Fresh Strategy maintenance3, PortfolioPolicy2, Confirmation3 and Budget compound4
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
| Stop all LP without a swap | Governance → paused [parking](CUSTODY_PARKING.md). | Closes both legs into Vault-attributed idle; both optional raw floors may be zero. Later ordinary resume is guarded; paused emergency redeployment can bypass optional guards. |
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
| `minimum0`, `minimum1` | Raw minimum principal receipts from closing **only the residual**, excluding existing idle and harvested fees. ETH uses wei; ZZZ uses its reviewed decimals. Both may deliberately be zero for a raw governance close. Any positive floor remains binding; use fresh simulation when retaining output protection. |
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
reject the request. Re-read and simulate the actual mix. Governance may instead
review a NEW request explicitly accepting both zero floors; this gives up
review-time token-output protection, not custody or exact settlement checks.

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
  The same applies to an excessive configured gap: setter admission alone does
  not prove either side can be placed. Reverting adjustment preserves the old
  portfolio. To return to one main, call `setMode(pool,false,reviewHash)` from
  governance and simulate the later guarded whole rebalance; it still needs
  cooldown, healthy prices/routes and execution floors. Changing policy does
  not move liquidity or restart the clock.
- During a USD-feed outage, do not invent NAV or force an ordinary swap. If the
  native pool/core/fixed token remain usable, permissionless
  `Vault.collectFees(bucketId,deadline)` can collect both legs while live, and
  current owners can claim funded raw currencies. This is not available through
  a global pause. Paused governance can instead use the reviewed raw
  `Migration.closeResidual(request)` path, which harvests internally and retains
  proceeds as attributed idle. Restore valid feeds and independently verify
  valuation before guarded deployment; unpause does not skip cooldown or merge
  automatically. A failed core or token may still block raw movement.
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
The [November3 journeys](../reports/smart-contract-lp-audit-20261103/VERIFICATION.md)
exercise infeasible-gap rollback/single-mode recovery and minute-long synthetic
USD outage with harvest/partial claims/raw close/later merge. They do not qualify
the actual operator wallet, provider, token, market depth or recovery host.

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

### Force, close and redeploy: choose the correct call

An ordinary manual call is not a force call. Use the following recovery sequence
when deliberately bypassing optional policy; do not weaken the automated keeper.
The [audited safeguard matrix](../reports/manual-safeguard-audit-20261104/SAFEGUARD_MATRIX.md)
maps every operation and dependency.

| Intent | Governance transaction / inputs | Timing and financial policy |
| --- | --- | --- |
| Rebalance now, including before cooldown | Pause via `Access.setPaused(true)`; fresh `Migration.emergencyRebalance(request)` with explicit ticks, current custody hash, chosen swap and `checks=0`. | No sampled window, hard cooldown, service jitter, independent-price, USD-loss, idle-ceiling or enabled-operation policy. Positive explicit swap-output/LP floors still bind. |
| Close all LP temporarily | Paused `Migration.park(ParkingRequest)`; exact current main/both-leg fingerprint, shares/epoch/nonce, fresh deadline/reviewHash. | No trigger, timer, USD source or swap. `minimum0=minimum1=0` is an explicit raw-close choice; positive floors remain binding. Principal remains attributed in Vault. |
| LP again after parking, despite optional policy failure | Stay paused; recompute `emergencyCustodyHash(bucket)` from PARKED state; new `emergencyRebalance` with `checks=0`. | Uses current pool, explicit raw ticks/optional one swap, and attributed idle/designated compound. No stale Active review or old sample can be reused. |
| Close residual only | Paused `Migration.closeResidual(ParkingRequest)`; same exact review fields, minima apply ONLY to residual. | No timing, USD or swap dependency; both raw floors may be zero. Main/shares/clock remain; desired mode does not change. |
| Consolidate and remain single | Set desired modefalse BEFORE reviewing; paused emergency replacement into one main. | Same selectable emergency mask; emergency never creates a second position. |
| Deploy normally or select a different reviewed ETH/ZZZ pool | Unpaused `Migration.resume` or `moveFunds`, positive LP floor and deadline. | Ordinary pricing/admission/execution guards remain. Emergency targets the bucket's CURRENT pool; it does not admit arbitrary new pools. |
| Permanently return LP to holders | Paused collective-exit procedure and governed bounded batches. | Terminal. No emergency can reopen LP or bypass NFT-owner allocations. |

Emergency bits are RETAINED checks, not bypass bits. Bit1 retains raw trigger/
cooldown; bit16 retains existing samples independently of that clock. Selecting
16 without1 still needs fresh matching samples and their live price/control
dependencies. Bit4 still needs USD valuation even without2. Select zero only
after reviewing the loss of all optional economic protections. Review hashes
are audit references, not attestations that the trade is safe.

All these calls retain current authority/pause/lifecycle, exact fixed assets,
Vault ownership, actual receipts/shares/reserves, typed callbacks, bounded
deadline and structurally valid ticks/liquidity. The core's current-transaction
principal proof remains even when review-time output floors are zero. Broken
tokens/core, unavailable liquidity, invalid raw amounts/ticks or insufficient gas
can still prevent execution. Never invent a recipient, relabel a runtime or
automatically retry with weaker protection.

After successful emergency/parking/close, the protocol REMAINS PAUSED. Check
receipt, both LP IDs, attributed idle, shares, old rewards/reserves and cleared
emergency state. Restore healthy normal settings and separately unpause when
ready. New LP replacement starts a new rebalance clock; unpause alone does not
deploy parked assets. On-chain policy changes alone need no keeper restart;
new source/runtime adoption and out-of-band signer activity require the existing
stop, reconcile, dry-run and reviewed rollout procedure. No rollout is performed
by this documentation or source publication.

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

Fresh Entry3 accepts only native ETH or fixed ZZZ and forwards the exact input to
Vault balancing; it has **no input conversion route, route toggle or executor
child**. Three separate controls must not be confused:

| What changes | Correct target | Effect |
| --- | --- | --- |
| Accept/stop ETH or fixed ZZZ as new contribution input | `ActivationAssets.setAsset` | Changes source admission; no swap or movement of existing principal. |
| Where Vault balances ETH/ZZZ for entry or maintenance | `Balancer.configureExecutionPools` | Changes the bounded reviewed venue list; LP destination/ownership remain separate. See [execution venue admission](#add-or-remove-an-execution-pool-after-sealing). |
| How already-earned LP rewards or royalties convert to ETH | The specific LP or royalty converter's route functions | Converts that ledger's existing funded credits; does not add an Entry route or new principal input. |

The exact fresh Request and policy inputs are in [direct Entry](ACTIVATION_ENTRY.md).
Changing one control never implicitly re-enables another stopped source/pool/route.

### Add or re-enable an input token

1. Only ETH and the reviewed ZZZ identity are contribution inputs. Do not add USDC, USDG or WETH as user sources. Marketplace royalty currencies are a separate policy.
2. Bind the initial ZZZ identity once before sealing using `ActivationAssets.configureZZZ(token,codeHash,reviewHash)` after reviewing its exact runtime, decimals, transfer behavior and two independent USD sources. The deployed identity cannot be replaced. An issuer migration uses terminal collective holder return and a fresh deployment; old ownership/reward records are not erased.
3. To stop either input, append its disabled `setAsset` policy; this stop requires no healthy token/feed. Re-enabling requires full review/validation. The helper cannot enable a third contribution currency.
4. Current principal destinations remain native ETH/fixedZZZ only. A new execution venue does not admit another input or target pair. Pin its exact venue/code/prices, simulate the complete direct/native operation and verify captured contribution floors before admission. Optional royalty conversions have their separate routes and permissions. Pool/route reconfiguration does not reopen a disabled source.

Current native accounting uses explicitly admitted ETH at `address(0)`, reviewed two-source USD pricing and exact call value. It is never an ERC20 approval target. Re-enabling either existing input does not admit a new LP or royalty currency. Only native ETH and the fixed reviewed ZZZ may be user inputs. Actual Vault venues, prices and preparation remain subject to [qualification](ACTIVATION_PREPARATION.md).

### Replace a swap route when market liquidity moves

Choose the actual target first; there is no Entry3 `addRoute` call.

- **Vault balancing venue:** review/qualify the same-pair pool and its exact key,
  runtime, prices, fees, depth and execution parameters; follow [execution pool
  admission](#add-or-remove-an-execution-pool-after-sealing) and call
  `Balancer.configureExecutionPools(bytes32[] pools,bytes32 reviewHash)` from
  governance. The supplied list is the reviewed bounded list; an empty list
  disables swaps, with no unsafe fallback. This does not migrate the LP.
- **Earned LP or royalty conversion:** use that specific converter's
  `addRoute(RoutePolicy)` or `addV4Route(Policy)`, qualify the returned immutable
  route ID, then update the matching converter worker's selected route and
  `setRouteEnabled(oldId,false)` when appropriate. Follow [typed conversion](TYPED_V4_ROUTES.md)
  and the ledger's [LP](LP_ETH_SETTLEMENT.md) / [royalty](ROYALTY_SETTLEMENT.md) procedure.
  Entry3 API source rows carry no route ID or Entry executor pin.

Immediate governance authorization has no timelock. Chain policy setters are
read dynamically only by matching reviewed consumers; a changed worker route or
runtime/configuration requires the documented journal-preserving reviewed rollout.
Old concurrent quotes can become invalid and need new review; a confirmed
approval is not repeated blindly. Already mined operations cannot be undone.

To stop an input immediately, use `ActivationAssets.setAsset(token,false,expectedCodeHash,reviewHash)` with the exact ETH-zero or fixed-ZZZ token and nonzero review hash; fresh Entry3 has no routes to disable. Disable paths deliberately avoid dependency calls needed for enabling; they can help when a token/feed is broken. Previously attached LP, shares and claims are not erased. Re-enabling requires valid current token/feed/code checks and new quotes. Pool configuration cannot silently re-enable an explicitly disabled source. See [Entry and source policy](ACTIVATION_ENTRY.md) and [routing](ACTIVATION_ENTRY.md#routing-controls).

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
pre-populate the replacement. The current schema10 observer checks these facts;
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

There is **no external handoff custody address** in accounting6/custody5.
[Collective holder exit](HOLDER_COLLECTIVE_EXIT.md) replaces both principal and
royalty-custody drains. Normal moves and parking remain reversible before exit.

| Need | Exact control and verification |
| --- | --- |
| Switch to another same-pair pool | Admit the reviewed native ETH/fixedZZZ fee tier. Simulate governance Migration.moveFunds(bucket,pool,minLP,deadline); verify actual LP/ticks, unchanged shares, retained value and deliberate sole contribution-pool cutover. No external recipient. |
| Temporarily park LP | Pause; use exact Migration.park(ParkingRequest), current nonce/epoch/LP/shares/currencies and raw minima. Principal remains attributed in the Vault. No USD oracle required; venue/token checks remain. |
| Restart parked LP | Before collective exit, revalidate feeds/venue/limits, unpause and call Migration.resume(bucket,pool,minLP,deadline). Verify actual LP and unchanged shares. |
| End collection LP | Pause and review irreversible shutdown. Governance beginCollectiveExit(reviewHash), then closeBucket for each bucket with raw ETH/ZZZ minima. No conversion or custody recipient. Pending compound joins principal; earned rewards and buyback backing remain separate. |
| Deliver principal without holder action | Governance calls allocatePrincipal(max32) to completion, then distributePrincipal(max32 IDs). Current owners receive exact allocated ETH+ZZZ. Inspect paid/deferred markers; low gas can leave later IDs unprocessed. |
| Rejected owner payment | Other payouts continue. Retry unpaid IDs, or actual owner claimPrincipal(id,recipient). ERC721 approval/operator authority cannot redirect funds. Both assets stay backed on failure. |
| Token/chain migration | Exit returns assets to holders; no protocol bridge, issuer exchange or external treasury custody remains. A fresh project/deployment does not inherit these principal rights automatically. |

The exit is permanent: unpause cannot reopen minting, activation, growth,
rebalancing or resume. Current ownership carries unpaid principal and previous
unclaimed rewards. After payout there is no second principal payment on sale.
NFTs remain transferable/royalty-eligible; all LP earnings end after final close.
Whole-collection handoff after exit is blocked because its importer does not
carry terminal principal settlement. Follow the complete runbook for exact
phases, minima, rounding, failure recovery and receipt reconciliation.

### Reconcile holders with several NFTs

Build payout batches from actual NFT IDs, not wallet addresses or mint ordinals.
A wallet may appear repeatedly and own a mix of dormant/activated NFTs with
unrelated tiers, rarity and LP shares. Allocate all captured ordinals first;
then total each payable ID's raw ETH/ZZZ for its current owner. Dormant/zero
allocations do not need delivery and may retain paid=false with nothing owed.
Rarity/visual tier are never payout multipliers. Old reward claims are separate.

Read principalOf(id), claimablePrincipal(id), remainingETH/remainingZZZ and
receipt PrincipalPaid/PrincipalDeferred for each submitted batch. Do not infer
all IDs succeeded from one successful receipt. Verify the actual paid owner in
the receipt if NFTs transferred since preview; other NFTs in either wallet must
retain their own rights. Retry only unpaid nonzero allocations. Group transfers
by wallet for reconciliation, accounting separately for network gas and other
transactions when comparing wallet ETH balances. No service restart or protocol
setting change is required for multiple NFTs per wallet.

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
| Admit royalty currency | Governance `NFT.addRoyaltyAsset(token)` | Initial scope is native ETH plus the independently verified Robinhood WETH wrapper; stablecoin conversion depends on marketplace qualification. Admission does not restrict sales or convert payouts. Separate bounded ledger (17 total including native); no arbitrary removal/sweep. Pre-admission/no-eligible-holder funds stay unallocated until separately reviewed recovery1; earned/deferred entitlements remain protected. |
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
Schema12 production observation is separate from keeper live configuration.
Leave live review/runtime pins unset and dry run enabled until real deployment
bindings, gas/spend limits, providers and schedules are qualified. Enable
compounding/conversions only with reviewed per-currency thresholds/routes, and
keep automatic width selection off for manual range policy.
Do not apply the fresh profile to an existing legacy journal or reuse its state path.
Preserve old hashes/nonces and follow [keeper recovery](KEEPER_RECOVERY.md).
Changing the example does not alter any installed service or saved journal.

### Marketplace currency and ETH payouts

Fresh royalty settlement3 pays original currencies: ETH, WETH, USDC or another
reviewed admitted token. No royalty converter, unwrap, route, feed or conversion
worker is involved. Use [settlement steps](ROYALTY_SETTLEMENT.md) and the complete
call tables. LP rewards keep their separate ETH-conversion policy.

Governance admits a reviewed token through `NFT.addRoyaltyAsset(token)`, including
after sealing, within configured capacity (initial16, reviewed maximum64ERC20 plus ETH). The current owner uses
`RoyaltyRewards.claim(id,asset)` or mixed `ClaimRouter.claimBatch` with at most32
NFT/asset/ledger entries. No approvals are required. Failed selected currencies
revert a batch; simulate/review healthy entries separately. Fractions, prior
rights, current ownership and outage cohorts remain protected. Operators can
call permissionless `sync(asset)` after a token outage to enroll waiting NFTs.

### Royalty opening and capacity controls

Follow [the complete window/capacity procedure](ROYALTY_LAUNCH_WINDOW.md).
Set NFT.setMintEnd(end) to the final OpenSea stage Unix end BEFORE minting; match
all mint paths. Governance can revise it while the previous sale remains open.
After closing it is fixed. Royalty claims open1hour later, independent of LP
claims. An activation at the deadline is late. Source's initial allocation is
lazy and automatic on healthy sync/claim/activation; no keeper opening job.
Zero initial participants and constructor/preadmission prefunds retain explicit
governance allocation. NFT ownership carries the rights, not an old wallet list.

For all reviewed unallocated units call RoyaltyRewards.allocateAllUnallocated
(asset,reviewHash). Read the exact return/event and remaining orphaned balance.
This never sweeps openingPool, earned/fraction backing or principal. For a partial
allocation keep allocateUnallocated(asset,amount,reviewHash). Both are irreversible
allocations under current active weights, require an open window/current sealed
lifecycle/unpaused/no preparation, and perform no payout or swap.

Changing end/capacity on-chain needs confirmed-state refresh, not an automatic
keeper restart. New currency admission additionally requires reviewed API/client
asset descriptors and the documented configuration reload procedure. Do not
relabel an old service or journal.

To exceed16ERC20 currencies, rehearse maximum cold/faulted activation and
API/history/canonical workloads, then governance calls
NFT.increaseRoyaltyAssetCapacity(newCapacity,capacityReviewHash), at most64.
Read assetCapacity and AssetCapacityIncreased; separately admit tokens and update
reviewed descriptors/worker profiles. Capacity cannot decrease or remove a token.
A review hash is not a gas proof. No public-chain expansion is qualified here.

Use reporting4 and explicit keeper royalty_settlement_version3 (no royalty swaps).
Old profiles/journals remain separate. CanonicalV7 requires initial allocation of
every admitted currency complete before capture; sync each after opening first.
Emergency LP/terminal return remains independent. No server restart/deployment is
implied by a source/config edit; deploy reviewed matching services separately.

### Recover unexpected royalty currencies

Review [original-currency unallocated allocation](ROYALTY_SETTLEMENT.md#unexpected-currencies-and-unallocated-recovery).
For an unsupported asset review/admit it first; existing funds become unallocated.
Governance calls `RoyaltyRewards.allocateUnallocated(asset,amount,reviewHash)`
under recovery2, sealed/current/unpaused/no preparation and positive active weight.
Amount is positive raw units bounded by `orphaned(asset)` after sync; reviewHash
is a nonzero reviewed classification/beneficiary fingerprint. No swap, unwrap,
price, approval, external recipient or keeper authority. Accounted backing is
unchanged; source-currency orphaned decreases and liabilities/index increase.
Existing earned/deferred/fraction funds are excluded. Verify
`UnallocatedRoyaltiesAllocated`, then holders claim the SAME asset. Success is
irreversible; failure reverts. No service restart is needed for the contract call.
Operating capacity starts16ERC20 and can increase after review to64;
pathological tokens remain a limit, not a sweep permit.

### Read royalty status and conversion history

Use [reporting schema4](ROYALTY_REPORTING.md):
`"royalty_reporting":{"schema":4,"converter":null}`. Authenticate exact runtime
and `ROYALTY_SETTLEMENT_VERSION()==3`, sale end and one-hour opening state.
Historical reporting3/settlement2 remains separately pinned. Each currency has a separate raw claim,
eligibility and optional current-price USD value. Non-ETH funds are claimable in
their original currency, never pending ETH. Missing prices/metadata stay explicit.
Claims alone increase lifetime paid amounts. Old conversion history remains
historical and cannot be counted as new income. Rebuild/review checkpoints after
the semantic replay change; preserve original journals/runtime profiles.

### Prepare and rotate an earnings checkpoint

Use [the exact checkpoint1 procedure](EARNINGS_CHECKPOINTS.md). The offline
`scripts/build-earnings-checkpoint.py` takes a reviewed API `--config`, confirmed
historical `--block` and new exclusive `--output`; optional offline budgets are
bounded separately. It creates only a candidate, without keys or contract writes.
Independently review its source/cutoff/raw-history evidence, then pin path/SHA-256
in `earnings_history.checkpoint` through a separately authorized API config/restart.
A served checkpoint must precede the complete24-hour window. It preserves exact
fractions/cohorts, not merely rounded totals. This first profile supports fresh
6/5/1without predecessors and accelerates earnings only; other readers stay raw.

On fault, preserve the artifact/config/WAL-consistent raw archive. A checkpoint
reorg, source change or malformed file is unavailable, never guessed zero. Restore
approved bytes, rebuild through reviewed bounded stages, or deliberately remove
the optional key/restart; full replay may still exceed its limits. No keeper,
nonce journal, wallet signing, pause or on-chain role change is required. No
installed service/configuration is changed by publishing this source.

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

A successful same-chain handoff does not qualify cross-chain finality, transport or post-halt recovery. Do not promise these are solved by external principal custody. The retired v3 principal bridge stack is not bound in new deployments. Collective exit must not have started; canonical V7 rejects terminal principal settlement. Imported local buckets retain their reviewed shares/backing. Track the remaining design in the [canonical recovery task](../TODO.md#task-security-chain-recovery).

## Stop controls

**These controls are not interchangeable.** First reconcile already-broadcast transactions; stopping a service or disabling a route cannot undo a mined operation.

| Control | Stops | Preserves / restart |
| --- | --- | --- |
| Hide a frontend action | That UI path only | Direct contract calls continue. Restore UI only after real backend/on-chain readiness. |
| Stop an API/indexer/keeper process | That service's new work | On-chain custody/rights persist; another authorized keeper/direct caller may operate. Recover durable state before restart. |
| Revoke keeper | New authorized keeper actions from that address | Permissionless claims, transfers and allowed fee synchronization remain. Governance must authorize a reviewed replacement. |
| Disable source asset | Affected contributions | Existing LP/funded claims remain. Reward/royalty conversion routes are separate controls; this stop does not disable them. Re-enable only after validation and fresh quotes. |
| Converter `setEnabled(false)` / `setRouteEnabled(id,false)` | New conversion through that converter/route | Existing earned currencies/credits stay backed; receipts and source claims keep their separate permissions. Review routes/runtime/prices and full simulation before re-enabling; an enabled getter alone is no qualification. |
| `NFT.setMintPaused(true)` | New NFT mints and new randomness requests | Governance only. Original fulfillment/finalize, existing NFT rights and LP work retain their own guards. Resume with `false`; global/lifecycle controls remain. |
| `Buyback.setOperatingTradeUSD(0)` | New buyback executions only | Immediate governance; no price/reserve query. Resize/remove keeper buyback tasks to avoid deliberate simulation failures. Accrued reserves stay classified; reopen with a reviewed positive limit no higher than `maxTradeUSD`. Preparation/canonical locks still apply. |
| `PoolRegistry.disablePool(id,stopDeposits,stopOperations)` | Pool-specific new contributions / ordinary guarded operations; no token/price/venue reads on disable | Governance only; flags only clear. Not universal pause. Reopen with full validated config; parked LP still needs resume. |
| `AccessController.setPaused(true)` | Ordinary mint, contributions, standalone harvest, rebalance/compound/buyback and moves/resume | Existing Uniswap LP stays deployed and can accrue actual in-range fees. Transfers/funded claims/royalty receipts retain separate guards. Governance unpauses with `setPaused(false)`; no other stopped flag is changed and terminal lpExitStarted is not reversed. |
| Canonical preparation | New economic work and normal protocol configuration | Existing claims/transfers/reveal/permitted drains; exact notice can be cancelled before freeze. Not a generic pause toggle. |
| Canonical freeze | Ownership and ordinary reward/accounting operations | Only handoff settlement/export/funding/abort path. Fully restore abort or complete one successor; no guardian unlock. |
| `Migration.invalidateParking(bucket)` | An unused parking authorization at its current nonce | No funds move. Collective exit has no cancel/recover/reopen path; failed individual payments stay backed for retry or owner fallback. |

There is no independent pause for every individual feature/asset payout. Do not invent one in an incident. Source: [module guards](../src/base/ZZZModule.sol), [controller](../src/ZZZAccessController.sol), [recovery matrix](CHANGE_AND_RECOVERY.md).

<a id="portfolio-mode-states-and-reward-effects"></a>

### Portfolio mode states and reward effects

These are two LP positions in one ETH/ZZZ pool, not two independently activated
NFTs or two contribution pools. Read `PortfolioPolicy.enabled(pool)`,
`configurationPending(bucket)`, `Vault.group(bucket).lpTokenId` and
`Manager.secondaryId(mainId)` at one confirmed block. Desired mode and actual
physical inventory can legitimately differ.

| Confirmed state / intent | Call, caller and inputs | Expected result and next step |
| --- | --- | --- |
| Enable optional residual management | Governance `PortfolioPolicy.setMode(pool,true,reviewHash)` using the admitted pool bytes32 and source-bound nonzero reviewed bytes32 hash. Reconcile pending transactions first. | No immediate trade or new leg. Pending geometry waits for cooldown and guarded `Vault.rebalance(bucket,minimumLiquidity,deadline)` by a permitted keeper. Normal sampled price-trigger requirements have their documented manual-geometry exception; execution guards still apply. |
| Mode enabled, residual ID0 | Read applied/pending revisions and actual main. | This can be a valid completed adjustment: natural main allocation already meets the governed floor. Do not force a40% residual, repeat adjustments or fabricate a missing leg. |
| Disable while a residual exists | Governance `setMode(pool,false,reviewHash)`; later permitted keeper `Vault.rebalance(bucket,minimumLiquidity,deadline)`. | Both legs stay owned/valued/harvested until atomic guarded merge creates one active main. Failure preserves both old legs and rights; desired false remains pending. Do not mark the residual closed or the NFT dormant. |
| Enable-disable-enable before adjustment | Read current geometry/applied revisions after each confirmed setter. | Revision advances even when the final bool repeats its original value; pending replacement and invalidated samples are not cancelled by restoring the bool. Re-review exact current policy. |
| Close residual without changing main | Paused governance `Migration.closeResidual(ParkingRequest)` with exact physical/control snapshot, nonce/epoch and raw minima. Set modefalse first if future residuals are unwanted. | Both legs harvest; only residual closes to attributed Vault idle. Main/shares/clock stay. No swap, payout or automatic idle redeployment. Unpause separately; idle limits can still block contributions until guarded recovery. |
| Urgently force one main | Set modefalse if intended, pause, then governance `Migration.emergencyRebalance(request)` with exact manifest and deliberately selected financial safeguards. | Both legs close and one main is deployed at its actual range ratio; no guaranteed50/50 USD split. This does not change desired mode. Verify outputs and unpause explicitly. Optional bypass can lose nearly all principal; never automate it as fallback. |

`minimumLiquidity` is the reviewed raw main liquidity minimum, not USD or a sum
of raw L across different ticks; `deadline` is the reviewed future Unix timestamp.
Use [review preparation](#prepare-and-check-an-offline-reviewhash) and the
[callable reference](CONTRACT_FUNCTIONS.md) for exact manifest tuples/permissions.
The helper prepares a source-bound hash, not live simulation or authorization.

Mode changes create no new NFT membership and remove none. Current owners retain
previously accrued rewards and future royalty rights. Hourly harvest still
collects both actual legs, allocating actual ETH/ZZZ receipts80/10/5/5 once per
asset with carried dust. Claims spend only funded liabilities; they do not merge,
compound, burn or redistribute other holders' balances. A failed all-in-one
replacement rolls back its closes/harvest/mint, while earlier separately mined
policy/pause transactions remain in effect. [Lifecycle evidence](../reports/lp-lifecycle-audit-20261102/VERIFICATION.md).

The fresh internal `planReplacement`/quote ABI change requires new runtime and
constructor pins for a reviewed deployment. It changes no operator call and
cannot upgrade an old deployment, service, receipt or journal by relabelling it.

<a id="multi-day-mainresidual-operation"></a>

### Multi-day main/residual operation

Activation/growth funds only the current main, then buys NFT shares of aggregate
main+residual+attributed idle/compound NAV. It does not give that NFT exclusively
main-leg rights. Entrant swaps can change both legs' token mix/value even though
residual L, IDs, centre and rebalance clock stay unchanged. Never substitute the
new target range ratio for the existing main ratio in an entry review.

Residual ticks are contained within main ticks. An active residual therefore
implies an active main under this geometry. If price exits the main, both legs
are outside on the same asset side. A mixed or fully crossed residual remains
live inventory; do not delete it, force another residual or infer a missing ID
from desired mode.60/40 is enforced at replacement, not maintained continuously.

At each operating cycle, reconcile pending receipts first; read actual IDs,
aggregate amounts, desired/applied revisions, both range states, idle/reserves,
liabilities and price health at a consistent confirmed block. Harvest both when
due. Compound uses existing main only and waits for the service's in-range,
below-threshold/no-pending-geometry policy. Ordinary adjustment retains its hard
cooldown, sampled evidence, service jitter and financial gates. Do not repeatedly
rebuild just to restore an exact60/40 ratio or respond to residual fill alone.

Review daily realized execution costs, gas, inactive time and unprocessed idle
separately from market-value changes and earned fees. After an outage, resume
from confirmed chain state and the preserved nonce/receipt journal. Mode off
requests a later whole merge; urgent residual-only close returns attributed idle
and may block entry until guarded reinvestment. A failed step never authorizes
deleting backing, resetting journals or using the manual emergency automatically.
Required feed/token/venue failures can still prevent recovery; stop affected work
and retain the exact failing evidence.

The effective growth floor is max(ProtocolPolicy growth minimum,pool minDepositUSD).
For the default5USD flow the pool must also admit5USD; see
[configuration inputs](#contribution-minimums). Read current settings rather than
assuming a5USD action floor overrides a higher pool minimum. A separately mined
approval may remain after a failed contribution; inspect it before asking again.

The [case matrix](../reports/portfolio-long-horizon-20261102/CASE_MATRIX.md) covers
trends, reversals, ordering, repeated one/two-leg transitions and recovery.
[Virtual-time contract evidence](../reports/portfolio-long-horizon-20261102/VERIFICATION.md)
does not qualify live keeper cadence, browser/RPC concurrency or target gas.
On-chain setting changes need no host restart; installing matching service/config
still uses the controlled restart and pending-recovery procedure below.

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

<a id="confirm-action-results-before-retry"></a>

### Confirm action results before retry

Changing RPC endpoints requires a reviewed configuration and controlled service
restart: existing clients retain their validated endpoint snapshot. Preserve the
same journal and resolve pending transactions/checkpoints; do not erase history
to switch providers. Call budgets cover both direct and convenience contract
reads. They do not replace the process/host watchdog for blocked network I/O.
[Current shared-client review](../reports/consolidation-20261103/REVIEW.md).

Keep transaction confirmation separate from availability of the next API read.
If the chain confirms an action but the API/prices fail for a minute, retain the
hash and confirmed status; refresh that action's post-state without submitting
again. Before retrying an unconfirmed action, recover its exact saved hash/nonce
and inspect allowances. A separately mined approval is not rolled back by a later
failed contribution, and network gas remains separate.

Verify operation events **and** current confirmed state. `FeesCollected` is the
actual combined receipt before allocation, not one NFT's payout. `Compounded`
reports released designated reserves, not total newly deployed LP if existing
idle also participates. Use actual LP/idle/reserve/share balances. Router claim
results are input-ordered raw amounts; never add unlike currencies. A failed
claim batch is atomic, not a partial payment. Conversion/claim/import is not new
income, and a reserved buyback allocation is not an executed burn.
[Action/output and fault matrix](../reports/action-resilience-audit-20261102/ACTION_MATRIX.md).

Maintenance defaults/overrides now reject unknown names. There is no
`rebalance:false` local stop setting. Use the actual documented Access/pool/pause
controls above. A validated saved transaction recovers before invalid new
maintenance values halt further work; repair config and restart with the same
journal/receipt/nonce history. Do not edit history to match a changed source hash.
[Exact fields and recovery boundary](OPERATIONS.md#maintenance-configuration-errors-and-paid-recovery).

Fresh schema10 preflight separates current `chains[].buyback_maximum_usd18` from
`constructor.maximum_buyback_usd18`. After reviewing a maximum-cap change, record
the actual pinned live getter as current policy, preserve creation provenance
and observe/validate again. Do not invent a value or edit constructor history to
make it pass. [Exact input and recovery](PRODUCTION_PREFLIGHT.md#current-buyback-maximum-and-creation-history).

For the unchanged confirmation3 policy,
`confirmation_observation_maintenance_policy_invalid` means the stored policy
record is missing, malformed, misbound or inconsistent. Preserve the original
evidence/config and collect a fresh matching observation; do not rewrite a
journal or insert guessed fields. The operation report separately uses
`maintenance_idle_policy_unavailable` to skip principal simulation after a failed
required idle-policy read. Independently due harvest remains evaluated. A report
or health checker cannot pause, repair or send transactions. Install matching
reviewed checker/source only through the authorized procedure below.

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

### Indexer startup failure and durable storage

The indexer validates SQLite-backed integer settings before creating directories
or opening a database: `chain_id`1..2^63-1, `start_block`0..2^63-2 and
`max_reorg_depth`1..2^63-2. These storage bounds are not sensible operating-size
recommendations; use the reviewed deployment anchor and practical reorg depth.
No CLI/config field, chain identity or event schema was added.

Startup reads current journal mode and rejects `OFF`, `MEMORY` or unknown modes
before schema writes. It performs schema/index setup, existing-identity check
and initial cursor insertion in ONE writer transaction. A rejected identity or
DDL/insert failure rolls that transaction back; its connection is closed.
WAL is requested only after the validated identity commits, outside the
transaction, and must actually return `wal`. A refused/failed WAL setup closes
the connection and does not start ingestion. A new database can then contain
coherently initialized empty tables/cursor for the SAME identity; this is not
partial event ingestion and is safe to retry after fixing the storage fault.

**Manage/restart:** use the existing service stop and consistent SQLite/WAL backup
procedure; review the SAME database path, chain/start/parent/contracts and storage
permissions/locking. Valid persistent databases require no schema migration or
rescan. The indexer retains current owners, log history and cursor on restart.
Installing source alone does not restart a process or repair its filesystem.

**Failure/reverse:** if identity changed, correct a mistaken config or perform the
already-reviewed separate database/rescan procedure for an intentional change.
If journal/storage admission fails, inspect the preserved files, permissions,
locks, free space and qualified WAL-capable local storage. Do not force OFF/
MEMORY, delete database/WAL, edit cursor/config identity or guess history to
obtain a successful startup. A previously used in-memory configuration is not a
supported persistent-history service. Preserve evidence before any approved
rebuild. Rollback of source does not undo an existing database or restore missing
history. Actual crash/power-loss/Unix/off-host restore qualification stays open.

[Consolidated findings and scoped verification](../reports/four-report-consolidation-20261104/VERIFICATION.md).

### Indexer anchor and ownership-history recovery

`indexer/monitor.py` validates and snapshots `start_parent_hash` when constructed.
An in-memory edit to the original configuration cannot move the running indexer's
first-block boundary or authorize rollback against another parent. A missing/null
anchor stays unanchored; it is not permission to erase all history after a reorg.
The existing database identity and SQL schema are unchanged. Null, or an exact
`0x` followed by 64 hexadecimal characters, are the accepted inputs; malformed values
fail before database creation. Valid existing anchor spelling is retained in the
stored identity, so changing its case is still a configuration change.

**Change/restart:** stop the exact reviewed indexer unit, take a consistent SQLite
backup including its WAL state, review chain/start/parent/contract identity, then
restart the source with matching configuration. No new unit name is assumed.
An intentional identity change needs a separately validated database/rescan;
do not modify an active database's cursor identity to bypass its startup check.
This source update does not restart any existing service automatically.

**Failure/reverse:** on ancestry disagreement or missing headers, retain the
database, cursor, logs and configuration. Retry a reviewed endpoint and prove the
bounded common ancestor; never substitute a new anchor to force deletion. For
rollback of this source-only update, stop the service first and use the previous
reviewed release with the same database/configuration; no schema migration is
required. Resume API earnings only after canonical coverage reconciles.

`nft_owners` now streams transfers and closes its cursor even on error. It retains
one current owner per surviving NFT rather than a Python list of every transfer.
Replay still scans historical rows and SQLite may sort them: this is not a
lifetime latency, maximum-scale or production-storage qualification. The public
API's separate complete-history bounds/unavailable behavior remain unchanged.


### API work and operating monitoring

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
retain their declared sets), helper pins and admitted assets first. The schema10
release inventory separately observes20 helpers. Bind the separate fee policy to
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

Retired `forwardLate(asset)` accepts admitted or unsupported currencies and sends
only to the authenticated immediate successor. The successor separately admits or
recovers unknown currencies; forwarding does not choose an entitlement cohort.
Current governance can use restricted [unallocated recovery](ROYALTY_SETTLEMENT.md#unexpected-currencies-and-unallocated-recovery),
with exact inputs and source classification, to convert only genuinely unallocated
value into ETH at current active weights. Existing/deferred entitlements stay
separate. Broken/illiquid/unpriced tokens can still fail; no arbitrary sweep exists.


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

Royalties are claimed in their original currencies under settlement3; WETH
remains WETH. LP holder rewards retain their separate approved ETH-conversion
path. [Royalty settlement](ROYALTY_SETTLEMENT.md), [LP settlement](LP_ETH_SETTLEMENT.md).
Never sum raw currencies or call a missing price zero. A source token claim uses
no price feed; optional USD display and LP conversions have separate requirements.

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
| Exceed normal10% loss ceilings or lower hybrid main below60% | No ordinary configurable path. Defaults2%/1%/3%; main floor6000–9999bps or single mode. Separate paused-governance emergency manifests may explicitly bypass selected financial checks; they are not a way to raise normal caps and can lose nearly all principal. |
| Holder withdrawal during normal operation, reroll rarity, overwrite owners/reward balances, sweep liabilities | Not supported. Governance terminal collective return is a separate irreversible procedure, not a holder-facing withdrawal or custody sweep. |
| Add arbitrary pair conversion, hooks, chains, cross-chain canonical replacement or post-halt recovery | Not made functional just by adding an address. Complete missing design, source support, independent review and rehearsals before relying on it. |

Future changes must preserve this distinction: what can be configured now, what requires new compatible code, what has actually been qualified, and what cannot be recovered. Do not describe a possible new deployment as a repair guaranteed to work with every already sealed predecessor.

## Reviewing an old audit recommendation before operating

Start with the [current reconciliation](../reports/full-history-reconciliation-20261104/REVIEW.md)
and [sole Todo](../TODO.md), then the exact current procedure/profile and deployed
runtime. Old wording such as “current”, “complete”, outside-only,15minutes,
creator inbox, bridge or custody recipient describes that old revision. It does
not authorize a current call or restore a removed feature. A past local incident
permission does not authorize another pending-record reset.

Read-only commands from the repository root verify the generated task ledger
and the selected static-review gate:

```bash
python scripts/sync-project-todo.py --check
python -m unittest tests_python.test_slither_review
python scripts/check-slither-review.py /path/to/captured/slither-output.json
```

The last input must be actual complete successful analyzer JSON for the reviewed
source. It is not reviewHash, a transaction or a simulation. Source/toolchain or
unreviewed detector drift must fail; do not edit historical evidence to make it
pass. [Development](DEVELOPMENT.md) explains a fresh analyzer run when justified.
These checks need no wallet, gas, pause or service restart. They neither upgrade
old deployments/services nor close external qualification. No reverse transaction
is needed; restore a mistaken documentation/default change through reviewed Git,
preserving its evidence. Never change a running journal to match a report label.

<a id="callable-contract-reference"></a>

## Callable contract reference: reads, writes, inputs and outputs

Use the [short operator tables](#operator-call-tables) for quick calls and the
[source-bound reference](CONTRACT_FUNCTIONS.md) for exact outputs, full permission
and input/value explanations. Reads may revert; writes require a confirmed receipt
and state check. A simulated return is not a transaction result. Inputs, transaction
value and network gas are separate. ABI visibility never grants operator authority.

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

<a id="manual-write-input-catalog"></a>

## Short call catalog

The former partial write catalog is consolidated into the [complete operator
call tables](#operator-call-tables) below: exact inputs, examples and brief
explanations for every current ABI function. Named tuple fields are expanded
there. The task procedures above retain their permission, sequencing, verification,
stop/restart and irreversible boundaries; the table is an index, not a bypass.

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
Direct Entry3/review-policy2 calls `executeReviewed(request,maximumLossBps,expectedContributionPolicy)`
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

On-chain policy changes need no service restart only for a **matching** source8
worker that reads them dynamically. Adopting direct Entry3/accounting6/schema10/new runtime pins
requires separate reviewed installation/configuration and controlled restart;
editing this manual does not authorize one. Preserve pending hashes/journals and
reconcile nonce/receipts/spend before any operating change. Requalify gas/load,
minimum economics, wallet review and provider behavior after material tuning.

Fixed after seal: core/helper implementations, ETH/fixed-ZZZ identities, supply/
quotas/final traits/art root,80/10/5/5, royalty weights/5% request, exact shares/
backing/current-owner rights, terminal holder return, no external custody sweep/
bridge and normal10% loss ceilings. These are not operational knobs.


## Read this before using the call tables

Use the exact verified deployment, chain, ABI and caller. No production address is
configured here. Examples are input templates, not executed transactions. In an
explorer select **Read** or **Write Contract**, the named contract and matching
overload; fill its ordered fields. A Safe must submit as the Safe. Module/callback
rows cannot be called from your wallet. Follow the linked operation's guards.

### Resolve IDs, hashes and amounts

| Input symbol | Expected source | Example read / preparation | Meaning |
| --- | --- | --- | --- |
| `NFT_ID` | Actual canonical NFT ID | `NFT.tokenAtOrdinal(1)` | Full hashed NFT identifier |
| `POOL_ID` | Admitted contribution destination | `PoolRegistry.contributionPool()` | PoolKey hash; no address |
| `BUCKET_ID` | Existing NFT/pool bucket | `Vault.nftBucket(NFT_ID)` or `Vault.poolBucket(POOL_ID)` | Shared custody account identifier |
| `EXPECTED_CONTRIBUTION_POLICY` | Current scoped entry policy | `ProtocolPolicy.entryFingerprint()` | Contribution policy; not reviewHash |
| `EXPECTED_MINT_POLICY` | Current sale/VRF policy | `Vault.mintPolicyFingerprint()` | Mint policy; not reviewHash |
| `CUSTODY_HASH` | Current emergency custody | `Migration.emergencyCustodyHash(BUCKET_ID)` | Exact emergency snapshot identity |
| `LP_TOKEN_ID` | Actual main PositionManager NFT ID | Read `Vault.group(BUCKET_ID)`; use `lpTokenId` | Physical LP; not PoPL NFT |
| `PORTFOLIO_HASH` | Current registered physical positions | `LiquidityManager.portfolioFingerprint(LP_TOKEN_ID)` | Includes current physical liquidity |
| `CURRENT_NONCE`, `CUSTODY_EPOCH` | Current parking/recovery state | `Migration.parkingNonce(BUCKET_ID)`; `Migration.custodyEpoch(BUCKET_ID)` | Reject stale operation replay |
| `REVIEW_HASH` | Your saved reviewed manifest | [Offline review procedure](#prepare-and-check-an-offline-reviewhash) | Fingerprint; never authorization proof |
| `MINT_PRICE_WEI` | Current sale terms | `Vault.mintPrice()` | Exact native mint payment |
| `UNIX_DEADLINE` | Fresh chain time and operation rules | Reviewed timestamp through allowed limit | Seconds; not an expired example |
| `*_ADDRESS`, `*_CODE_HASH` | Exact reviewed deployment/runtime inventory | [Address and runtime inventory](DEPLOYMENT_ADDRESSES.md) | Never ticker-based guesses |
| `*_USD` | USD18 integer amount | `$100 = 100000000000000000000` | Dollar value; not token units |
| `*_WEI` | Exact native ETH units | `0.05 ETH = 50000000000000000` | Native amount; gas separate |
| `RAW_UNITS` | Actual source-token decimals | `1 token = 10^actualDecimals` | No assumed stablecoin peg |
| `MINIMUM_LIQUIDITY`, ticks, minima | Reviewed simulation/physical placement | [Contribution preparation](ACTIVATION_PREPARATION.md), [emergency review](EMERGENCY_REBALANCE.md) | Not USD or guessed liquidity |

Other uppercase labels identify that operation's corresponding input; obtain them
from its linked procedure/current snapshot. They are not optional defaults. Primary
and secondary feeds must have distinct reviewed identities and independent
upstreams; replacing both with one feed is invalid. Capture review fingerprints
again after a relevant setting changes, including restore-to-old-value changes.

### Wallet flows and external token approvals

The external fixed ZZZ ERC20 is not one of the37PoPL contract ABIs. Its approval
calls are separate from NFT approvals:

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `ZZZ.allowance` | Current owner, selected spender | `allowance(OWNER_ADDRESS, ENTRY_ADDRESS)` | Read current token allowance |
| `ZZZ.approve` | Exact reviewed spender/amount | `approve(ENTRY_ADDRESS, EXACT_ZZZ_RAW_UNITS)` | Approve exact contribution only |
| `ZZZ.approve` | Confirmed stale allowance, spender | `approve(ENTRY_ADDRESS, 0)` | Revoke unused token allowance |

The spender above is for the reviewed Entry flow. Direct Vault funding uses its
own exact reviewed spender; never substitute one arbitrarily. ETH needs no ERC20
approval. Reprepare after an approval confirms. `NFT.approve/setApprovalForAll`
permits NFT transfers, not contribution spending. Do not use unlimited approvals.
Entry `increase=false` activates; `increase=true` grows existing LP. Its example
below shows native ETH; fixed-ZZZ input uses its exact token address and
transaction value0. Artwork and shares change only after confirmed actual LP.

<!-- BEGIN GENERATED OPERATOR CALLS -->

## Operator call tables

Source-bound coverage: **809 functions, 36 constructors and 12 ETH receivers**. Every overload has its own row. Internal Solidity functions are not external entrypoints.

Four columns only; explanations contain at most five words. Click a function for outputs, full caller restrictions and safety conditions. These are **unresolved input templates**, not simulated or approved transactions. Replace ALL uppercase symbols from the reviewed deployment/current snapshot. Never paste a symbol, guessed address, stale hash or illustrative setting into a wallet.

Resolve [IDs, hashes and units](#resolve-ids-hashes-and-amounts) first; see [wallet/token approvals](#wallet-flows-and-external-token-approvals) for exact funding and transaction value.

**Caller keys:** `G` governance after seal/bootstrap before seal; `B` bootstrap only; `K` keeper-authorized wallet; `H` NFT owner/approved NFT transfer caller as specified; `P` permissionless; `N` exact nominated recipient/provider; `M` fixed module/parent only; `C` authenticated callback only; `D` deployment only; `R` read, possibly guarded. These keys do not replace the linked exact permission. Governance is not automatically keeper-authorized. Guardian may pause, never unpause.

**Input format:** examples show function(arguments), not transaction calldata. Tuple/array brackets preserve ABI order; addresses and decimal integers are quoted for JSON precision. Quoted uppercase names are unresolved replacements, not literal values; replace boolean placeholders with true/false. Enter separate arguments/expanded tuple fields in the explorer or reviewed ABI tool. A tuple/array is ONE top-level argument. Use exact integer strings, never floats. Transaction value/gas are separate. Direct mint examples do not implement OpenSea primary mint.

**Order:** read identities/state → capture current inputs → review → simulate exact caller/value/calldata → sign if authorized → verify receipt/state. Failed/reverted/unresolved operations need receipt reconciliation; do not guess success, resend, reset journals or restart services from this table.

### Table navigation

- [Safety, governance and permissions](#calls-safety)
- [Daily LP management](#calls-liquidity)
- [Pools, ranges, execution and prices](#calls-policy)
- [LP rewards, royalties and claims](#calls-revenue)
- [Parking, holder return and canonical replacement](#calls-recovery)
- [NFTs, contributions and metadata](#calls-holders)
- [Bound modules, helpers and factories](#calls-internals)
- [Expanded tuple examples](#expanded-tuple-examples)
- [Deployment constructors](#deployment-constructors)
- [ETH receive hooks](#eth-receive-hooks)

<a id="calls-safety"></a>

### Safety, governance and permissions

<a id="zzzaccesscontroller"></a>

#### AccessController

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [AccessController.setPaused](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `state: bool` | `setPaused(true)` | Pause or resume ordinary operations |
| `G` [AccessController.setKeeper](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `who: address`<br>`enabled: bool` | `setKeeper(KEEPER_ADDRESS, true)` | Grant or revoke keeper |
| `G` [AccessController.setGuardian](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `who: address`<br>`enabled: bool` | `setGuardian(GUARDIAN_ADDRESS, true)` | Grant or revoke guardian |
| `G` [AccessController.proposeGovernance](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `candidate: address` | `proposeGovernance(CANDIDATE_ADDRESS)` | Propose next governance wallet |
| `N` [AccessController.acceptGovernance](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `acceptGovernance()` | Accept governance authority |
| `G` [AccessController.startPreparation](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `notice` [ZZZAccessController.PreparationNotice](#input-zzzaccesscontroller-preparationnotice) | `startPreparation(["DESTINATION_CHAIN", "SUCCESSOR_CONTROLLER_ADDRESS", "DEPLOYMENT_COMMITMENT", "REVIEW_HASH"])` | Announce reviewed canonical replacement |
| `G` [AccessController.cancelPreparation](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `noticeHash: bytes32` | `cancelPreparation(NOTICE_HASH)` | Cancel replacement preparation |
| `B` [AccessController.bindProtocolPolicy](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `implementation: address` | `bindProtocolPolicy(IMPLEMENTATION_ADDRESS)` | Bind operating policy once |
| `B` [AccessController.bind](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `id: bytes32`<br>`implementation: address` | `bind(MODULE_ID, IMPLEMENTATION_ADDRESS)` | Bind protocol module |
| `B` [AccessController.seal](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `seal()` | Seal immutable protocol bindings |

<details>
<summary>Read functions and constants (25)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [AccessController.GOVERNANCE_VERSION](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `GOVERNANCE_VERSION()` | Read governance version |
| `R` [AccessController.activationAssetsFactory](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `activationAssetsFactory()` | Read activation assets factory |
| `R` [AccessController.bootstrap](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `bootstrap()` | Read bootstrap |
| `R` [AccessController.canConfigure](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `account: address` | `canConfigure(ACCOUNT_ADDRESS)` | Read can configure |
| `R` [AccessController.canonicalHandoff](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `canonicalHandoff()` | Read canonical handoff |
| `R` [AccessController.canonicalSettling](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `canonicalSettling()` | Read canonical settling |
| `R` [AccessController.canonicalState](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `canonicalState()` | Read canonical state |
| `R` [AccessController.governance](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `governance()` | Read governance |
| `R` [AccessController.guardians](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `input0: address` | `guardians(TARGET_ADDRESS)` | Read guardians |
| `R` [AccessController.isSealed](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `isSealed()` | Read is sealed |
| `R` [AccessController.keeperAuthorized](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `caller: address` | `keeperAuthorized(CALLER_ADDRESS)` | Read keeper authorized |
| `R` [AccessController.keepers](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `input0: address` | `keepers(TARGET_ADDRESS)` | Read keepers |
| `R` [AccessController.lpExitStarted](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `lpExitStarted()` | Read lp exit started |
| `R` [AccessController.module](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `input0: bytes32` | `module(MODULE_ID)` | Read module |
| `R` [AccessController.moduleAuthorized](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `id: bytes32`<br>`caller: address` | `moduleAuthorized(MODULE_ID, CALLER_ADDRESS)` | Read module authorized |
| `R` [AccessController.paused](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `paused()` | Read paused |
| `R` [AccessController.pendingGovernance](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `pendingGovernance()` | Read pending governance |
| `R` [AccessController.preparationActive](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `preparationActive()` | Read preparation active |
| `R` [AccessController.preparationHash](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `preparationHash()` | Read preparation hash |
| `R` [AccessController.preparationNonce](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `preparationNonce()` | Read preparation nonce |
| `R` [AccessController.preparationNotice](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `preparationNotice()` | Read preparation notice |
| `R` [AccessController.preparationReadyDestination](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `preparationReadyDestination()` | Read preparation ready destination |
| `R` [AccessController.preparationStartedAt](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `preparationStartedAt()` | Read preparation started at |
| `R` [AccessController.protocolPolicy](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `protocolPolicy()` | Read protocol policy |
| `R` [AccessController.royaltyFactory](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `royaltyFactory()` | Read royalty factory |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (2)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [AccessController.canonicalTransition](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `state: uint8`<br>`settling: bool`<br>`clearPreparation: bool` | `canonicalTransition(STATE, SETTLING, CLEAR_PREPARATION)` | Advance canonical controller phase |
| `M` [AccessController.startLPExit](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | None | `startLPExit()` | Authorize terminal LP shutdown |

</details>

<a id="calls-liquidity"></a>

### Daily LP management

<a id="zzzvault"></a>

#### Vault

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `P` [Vault.collectFees](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`deadline: uint256` | `collectFees(BUCKET_ID, UNIX_DEADLINE)` | Harvest and allocate fees |
| `K` [Vault.rebalance](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256` | `rebalance(BUCKET_ID, MINIMUM_LIQUIDITY, UNIX_DEADLINE)` | Replace shared LP positions |
| `H` [Vault.activate](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`poolId: bytes32`<br>`amount0: uint256`<br>`amount1: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256`<br>`value: wei` (separate) | `activate(NFT_ID, POOL_ID, ETH_INPUT_WEI, 0, MINIMUM_LIQUIDITY, UNIX_DEADLINE); value=ETH_INPUT_WEI wei` | Activate dormant NFT liquidity |
| `H` [Vault.increase](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`amount0: uint256`<br>`amount1: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256`<br>`value: wei` (separate) | `increase(NFT_ID, ETH_INPUT_WEI, 0, MINIMUM_LIQUIDITY, UNIX_DEADLINE); value=ETH_INPUT_WEI wei` | Grow existing attached LP |
| `P` [Vault.mintDormant](CONTRACT_FUNCTIONS.md#zzzvault) | `expectedMintPolicy: bytes32`<br>`value: wei` (separate) | `mintDormant(EXPECTED_MINT_POLICY); value=MINT_PRICE_WEI wei` | Mint dormant PoPL NFT |
| `G` [Vault.reservePool](CONTRACT_FUNCTIONS.md#zzzvault) | `pool: bytes32`<br>`bucket: uint256` | `reservePool(POOL_ID, BUCKET_ID)` | Reserve historical custody capacity |

<details>
<summary>Read functions and constants (22)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Vault.ACCOUNTING_VERSION](CONTRACT_FUNCTIONS.md#zzzvault) | None | `ACCOUNTING_VERSION()` | Read accounting version |
| `R` [Vault.MAX_BUCKETS](CONTRACT_FUNCTIONS.md#zzzvault) | None | `MAX_BUCKETS()` | Read max buckets |
| `R` [Vault.RESIDUAL_EXIT_VERSION](CONTRACT_FUNCTIONS.md#zzzvault) | None | `RESIDUAL_EXIT_VERSION()` | Read residual exit version |
| `R` [Vault.access](CONTRACT_FUNCTIONS.md#zzzvault) | None | `access()` | Read access |
| `R` [Vault.bucketAt](CONTRACT_FUNCTIONS.md#zzzvault) | `index: uint256` | `bucketAt(0)` | Read bucket at |
| `R` [Vault.bucketCount](CONTRACT_FUNCTIONS.md#zzzvault) | None | `bucketCount()` | Read bucket count |
| `R` [Vault.bucketTotalShares](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: uint256` | `bucketTotalShares(BUCKET_ID)` | Read bucket total shares |
| `R` [Vault.canonicalChainId](CONTRACT_FUNCTIONS.md#zzzvault) | None | `canonicalChainId()` | Read canonical chain id |
| `R` [Vault.canonicalModule](CONTRACT_FUNCTIONS.md#zzzvault) | None | `canonicalModule()` | Read canonical module |
| `R` [Vault.contributionUSD](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: uint256` | `contributionUSD(NFT_ID)` | Read contribution usd |
| `R` [Vault.group](CONTRACT_FUNCTIONS.md#zzzvault) | `bucket: uint256` | `group(BUCKET_ID)` | Read group |
| `R` [Vault.homePoolId](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: uint256` | `homePoolId(BUCKET_ID)` | Read home pool id |
| `R` [Vault.migrationBudget](CONTRACT_FUNCTIONS.md#zzzvault) | None | `migrationBudget()` | Read migration budget |
| `R` [Vault.mintPolicyFingerprint](CONTRACT_FUNCTIONS.md#zzzvault) | None | `mintPolicyFingerprint()` | Read current mint policy |
| `R` [Vault.mintPrice](CONTRACT_FUNCTIONS.md#zzzvault) | None | `mintPrice()` | Read mint price |
| `R` [Vault.mintProceedsRecipient](CONTRACT_FUNCTIONS.md#zzzvault) | None | `mintProceedsRecipient()` | Read mint proceeds recipient |
| `R` [Vault.nftBucket](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: uint256` | `nftBucket(NFT_ID)` | Read NFT custody bucket |
| `R` [Vault.nftStatus](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256` | `nftStatus(NFT_ID)` | Read nft status |
| `R` [Vault.poolBucket](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: bytes32` | `poolBucket(POOL_ID)` | Read pool custody bucket |
| `R` [Vault.sequence](CONTRACT_FUNCTIONS.md#zzzvault) | None | `sequence()` | Read sequence |
| `R` [Vault.sharesOf](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: uint256` | `sharesOf(NFT_ID)` | Read shares of |
| `R` [Vault.totalIdle](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: address` | `totalIdle(TARGET_ADDRESS)` | Read total idle |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (12)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Vault.beginLPExit](CONTRACT_FUNCTIONS.md#zzzvault) | None | `beginLPExit()` | Commit terminal principal lock |
| `M` [Vault.canonicalBarrier](CONTRACT_FUNCTIONS.md#zzzvault) | None | `canonicalBarrier()` | Set canonical accounting barrier |
| `M` [Vault.canonicalSend](CONTRACT_FUNCTIONS.md#zzzvault) | `token: address`<br>`destination: address`<br>`amount: uint256` | `canonicalSend(ZZZ_ADDRESS, DESTINATION_ADDRESS, AMOUNT)` | Send authenticated canonical backing |
| `M` [Vault.canonicalWrite](CONTRACT_FUNCTIONS.md#zzzvault) | `kind: uint8`<br>`row: bytes` | `canonicalWrite(KIND, ROW)` | Write authenticated imported accounting |
| `M` [Vault.closeResidual](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`deadline: uint256` | `closeResidual(BUCKET_ID, UNIX_DEADLINE)` | Close residual; retain main |
| `M` [Vault.compound](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256` | `compound(BUCKET_ID, MINIMUM_LIQUIDITY, UNIX_DEADLINE)` | Reinvest designated LP reserves |
| `M` [Vault.emergencyRebalance](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256` | `emergencyRebalance(BUCKET_ID, MINIMUM_LIQUIDITY, UNIX_DEADLINE)` | Force reviewed emergency consolidation |
| `M` [Vault.exitBucketToHolders](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`minimumETH: uint256`<br>`minimumZZZ: uint256`<br>`deadline: uint256` | `exitBucketToHolders(BUCKET_ID, MINIMUM_ETH_WEI, MINIMUM_ZZZ, UNIX_DEADLINE)` | Return bucket principal internally |
| `M` [Vault.movePool](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`newPool: bytes32`<br>`minimumLiquidity: uint128`<br>`deadline: uint256` | `movePool(BUCKET_ID, POOL_ID, MINIMUM_LIQUIDITY, UNIX_DEADLINE)` | Execute authenticated pool movement |
| `C` [Vault.onERC721Received](CONTRACT_FUNCTIONS.md#zzzvault) | `input0: address`<br>`input1: address`<br>`input2: uint256`<br>`input3: bytes` | `onERC721Received(TARGET_ADDRESS, TARGET_ADDRESS, INPUT2, ENCODED_BYTES)` | Read on erc721 received |
| `M` [Vault.park](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`deadline: uint256` | `park(BUCKET_ID, UNIX_DEADLINE)` | Close LP into attributed idle |
| `M` [Vault.resume](CONTRACT_FUNCTIONS.md#zzzvault) | `id: uint256`<br>`newPool: bytes32`<br>`minimumLiquidity: uint128`<br>`deadline: uint256` | `resume(BUCKET_ID, POOL_ID, MINIMUM_LIQUIDITY, UNIX_DEADLINE)` | Redeploy parked LP principal |

</details>

<a id="zzzstrategy"></a>

#### Strategy

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `K` [Strategy.applyKeeperRange](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32` | `applyKeeperRange(POOL_ID)` | Apply approved range choice |
| `G` [Strategy.setAdditionalLossBps](CONTRACT_FUNCTIONS.md#zzzstrategy) | `limit: uint16`<br>`reviewHash: bytes32` | `setAdditionalLossBps(1, REVIEW_HASH)` | Set additional execution-loss limit |
| `G` [Strategy.setKeeperRangePolicy](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32`<br>`enabled: bool`<br>`narrowTriggerBps: uint16`<br>`widenTriggerBps: uint16`<br>`minInterval: uint32`<br>`reviewHash: bytes32` | `setKeeperRangePolicy(POOL_ID, false, NARROW_TRIGGER_BPS, WIDEN_TRIGGER_BPS, MIN_INTERVAL, REVIEW_HASH)` | Configure approved range choices |
| `G` [Strategy.setRangeOrientation](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32`<br>`orientation: uint8` | `setRangeOrientation(POOL_ID, ORIENTATION)` | Configure human-price range orientation |

<details>
<summary>Read functions and constants (27)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Strategy.EXECUTION_QUALITY_VERSION](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `EXECUTION_QUALITY_VERSION()` | Read execution quality version |
| `R` [Strategy.MAINTENANCE_POLICY_VERSION](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `MAINTENANCE_POLICY_VERSION()` | Read maintenance policy version |
| `R` [Strategy.MAX_ADDITIONAL_LOSS_BPS](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `MAX_ADDITIONAL_LOSS_BPS()` | Read max additional loss bps |
| `R` [Strategy.PORTFOLIO_VERSION](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `PORTFOLIO_VERSION()` | Read portfolio version |
| `R` [Strategy.RANGE_POLICY_VERSION](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `RANGE_POLICY_VERSION()` | Read range policy version |
| `R` [Strategy.REBALANCE_CONFIRMATION_VERSION](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `REBALANCE_CONFIRMATION_VERSION()` | Read rebalance confirmation version |
| `R` [Strategy.access](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `access()` | Read access |
| `R` [Strategy.activeKeeperRangePolicies](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `activeKeeperRangePolicies()` | Read active keeper range policies |
| `R` [Strategy.additionalLossBps](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `additionalLossBps()` | Read additional loss bps |
| `R` [Strategy.compoundPlan](CONTRACT_FUNCTIONS.md#zzzstrategy) | `id: uint256`<br>`amount0: uint256`<br>`amount1: uint256` | `compoundPlan(BUCKET_ID, AMOUNT0, AMOUNT1)` | Read compound plan |
| `R` [Strategy.executionQualityRevision](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `executionQualityRevision()` | Read execution quality revision |
| `R` [Strategy.keeperRangePolicy](CONTRACT_FUNCTIONS.md#zzzstrategy) | `input0: bytes32` | `keeperRangePolicy(POOL_ID)` | Read keeper range policy |
| `R` [Strategy.keeperRangeTarget](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32` | `keeperRangeTarget(POOL_ID)` | Read keeper range target |
| `R` [Strategy.minimumOutput](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32`<br>`direction: bool`<br>`amount: uint256` | `minimumOutput(POOL_ID, DIRECTION, AMOUNT)` | Read minimum output |
| `R` [Strategy.minimumOutputForExit](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32`<br>`direction: bool`<br>`amount: uint256` | `minimumOutputForExit(POOL_ID, DIRECTION, AMOUNT)` | Read minimum output for exit |
| `R` [Strategy.needsRebalance](CONTRACT_FUNCTIONS.md#zzzstrategy) | `id: uint256` | `needsRebalance(BUCKET_ID)` | Check raw adjustment need |
| `R` [Strategy.portfolioPolicy](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `portfolioPolicy()` | Read portfolio policy |
| `R` [Strategy.rangeOrientation](CONTRACT_FUNCTIONS.md#zzzstrategy) | `input0: bytes32` | `rangeOrientation(POOL_ID)` | Read range orientation |
| `R` [Strategy.rangeUpdatePending](CONTRACT_FUNCTIONS.md#zzzstrategy) | `id: uint256` | `rangeUpdatePending(BUCKET_ID)` | Read range update pending |
| `R` [Strategy.rebalanceCondition](CONTRACT_FUNCTIONS.md#zzzstrategy) | `id: uint256` | `rebalanceCondition(BUCKET_ID)` | Read rebalance condition |
| `R` [Strategy.rebalanceConfirmation](CONTRACT_FUNCTIONS.md#zzzstrategy) | None | `rebalanceConfirmation()` | Read rebalance confirmation |
| `R` [Strategy.rebalanceObservation](CONTRACT_FUNCTIONS.md#zzzstrategy) | `id: uint256` | `rebalanceObservation(BUCKET_ID)` | Read rebalance observation |
| `R` [Strategy.rebalanceReady](CONTRACT_FUNCTIONS.md#zzzstrategy) | `id: uint256` | `rebalanceReady(BUCKET_ID)` | Read rebalance ready |
| `R` [Strategy.swapPlan](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32`<br>`amount0: uint256`<br>`amount1: uint256` | `swapPlan(POOL_ID, AMOUNT0, AMOUNT1)` | Read swap plan |
| `R` [Strategy.target](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32` | `target(POOL_ID)` | Read target |
| `R` [Strategy.validateExitPrice](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32` | `validateExitPrice(POOL_ID)` | Read validate exit price |
| `R` [Strategy.validatePrice](CONTRACT_FUNCTIONS.md#zzzstrategy) | `poolId: bytes32` | `validatePrice(POOL_ID)` | Read validate price |

</details>

<a id="zzzrebalanceconfirmation"></a>

#### RebalanceConfirmation

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [RebalanceConfirmation.configure](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `secondsRequired: uint32`<br>`maximumGap: uint32`<br>`reviewed: bytes32` | `configure(600, 300, REVIEW_HASH)` | Configure sampled confirmation timing |
| `K` [RebalanceConfirmation.observe](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `bucket: uint256` | `observe(BUCKET_ID)` | Record sampled trigger evidence |
| `K` [RebalanceConfirmation.resetObservation](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `bucket: uint256` | `resetObservation(BUCKET_ID)` | Clear stale sampled evidence |
| `G` [RebalanceConfirmation.setRequireReferenceExit](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `required: bool`<br>`reviewed: bytes32` | `setRequireReferenceExit(REQUIRED, REVIEWED)` | Configure independent trigger corroboration |

<details>
<summary>Read functions and constants (17)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [RebalanceConfirmation.MAX_DURATION](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `MAX_DURATION()` | Read max duration |
| `R` [RebalanceConfirmation.REBALANCE_CONFIRMATION_VERSION](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `REBALANCE_CONFIRMATION_VERSION()` | Read rebalance confirmation version |
| `R` [RebalanceConfirmation.access](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `access()` | Read access |
| `R` [RebalanceConfirmation.condition](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `bucket: uint256` | `condition(BUCKET_ID)` | Read sampled trigger condition |
| `R` [RebalanceConfirmation.controlFingerprint](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `poolId: bytes32` | `controlFingerprint(POOL_ID)` | Read current control identity |
| `R` [RebalanceConfirmation.duration](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `duration()` | Read duration |
| `R` [RebalanceConfirmation.emergencyReady](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `bucket: uint256` | `emergencyReady(BUCKET_ID)` | Read emergency ready |
| `R` [RebalanceConfirmation.marketSides](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `bucket: uint256` | `marketSides(BUCKET_ID)` | Read market sides |
| `R` [RebalanceConfirmation.maxObservationGap](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `maxObservationGap()` | Read max observation gap |
| `R` [RebalanceConfirmation.observationFingerprint](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `bucket: uint256`<br>`poolId: bytes32` | `observationFingerprint(BUCKET_ID, POOL_ID)` | Read observation fingerprint |
| `R` [RebalanceConfirmation.observations](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `input0: uint256` | `observations(BUCKET_ID)` | Read observations |
| `R` [RebalanceConfirmation.policyRevision](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `policyRevision()` | Read policy revision |
| `R` [RebalanceConfirmation.ready](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `bucket: uint256` | `ready(BUCKET_ID)` | Check sampled adjustment readiness |
| `R` [RebalanceConfirmation.referenceReviewHash](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `referenceReviewHash()` | Read reference review hash |
| `R` [RebalanceConfirmation.requireReferenceExit](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `requireReferenceExit()` | Read require reference exit |
| `R` [RebalanceConfirmation.reviewHash](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `reviewHash()` | Read review hash |
| `R` [RebalanceConfirmation.strategy](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `strategy()` | Read strategy |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [RebalanceConfirmation.invalidatePolicy](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | None | `invalidatePolicy()` | Invalidate sampled policy evidence |

</details>

<a id="zzzcompounder"></a>

#### Compounder

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `K` [Compounder.compound](CONTRACT_FUNCTIONS.md#zzzcompounder) | `id: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256` | `compound(BUCKET_ID, MINIMUM_LIQUIDITY, UNIX_DEADLINE)` | Reinvest designated LP reserves |

<details>
<summary>Read functions and constants (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Compounder.access](CONTRACT_FUNCTIONS.md#zzzcompounder) | None | `access()` | Read access |

</details>

<a id="zzzbuyback"></a>

#### Buyback

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `K` [Buyback.execute](CONTRACT_FUNCTIONS.md#zzzbuyback) | `token: address`<br>`amount: uint256`<br>`poolId: bytes32`<br>`deadline: uint256` | `execute(ZZZ_ADDRESS, AMOUNT, POOL_ID, UNIX_DEADLINE)` | Execute guarded reserve buyback |
| `G` [Buyback.setMaximumTradeUSD](CONTRACT_FUNCTIONS.md#zzzbuyback) | `limit: uint256`<br>`reviewHash: bytes32` | `setMaximumTradeUSD(1, REVIEW_HASH)` | Set reviewed buyback maximum |
| `G` [Buyback.setOperatingTradeUSD](CONTRACT_FUNCTIONS.md#zzzbuyback) | `limit: uint256` | `setOperatingTradeUSD(1)` | Set buyback operating amount |

<details>
<summary>Read functions and constants (4)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Buyback.access](CONTRACT_FUNCTIONS.md#zzzbuyback) | None | `access()` | Read access |
| `R` [Buyback.maxTradeUSD](CONTRACT_FUNCTIONS.md#zzzbuyback) | None | `maxTradeUSD()` | Read max trade usd |
| `R` [Buyback.operatingTradeUSD](CONTRACT_FUNCTIONS.md#zzzbuyback) | None | `operatingTradeUSD()` | Read operating trade usd |
| `R` [Buyback.zzz](CONTRACT_FUNCTIONS.md#zzzbuyback) | None | `zzz()` | Read zzz |

</details>

<a id="calls-policy"></a>

### Pools, ranges, execution and prices

<a id="zzzpoolregistry"></a>

#### PoolRegistry

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [PoolRegistry.configureNative](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `config` [PoolConfig](#input-poolconfig) | `configureNative([["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"], "DEPOSITS_ENABLED", "OPERATIONS_ENABLED", "RANGE_BPS", "TRIGGER_BPS", "MAX_SPOT_DEVIATION_BPS", "MAX_SLIPPAGE_BPS", "MIN_REBALANCE_INTERVAL", "MIN_DEPOSIT_USD", "MAX_POSITION_USD"])` | Admit configured ETH/ZZZ pool |
| `G` [PoolRegistry.disablePool](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `poolId: bytes32`<br>`disableDeposits: bool`<br>`disableOperations: bool` | `disablePool(POOL_ID, DISABLE_DEPOSITS, DISABLE_OPERATIONS)` | Stop selected pool operations |

<details>
<summary>Read functions and constants (11)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [PoolRegistry.SELECTED_NATIVE_POOL](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | None | `SELECTED_NATIVE_POOL()` | Read selected native pool |
| `R` [PoolRegistry.access](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | None | `access()` | Read access |
| `R` [PoolRegistry.accounting](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `poolId: bytes32` | `accounting(POOL_ID)` | Read accounting |
| `R` [PoolRegistry.activationAssets](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | None | `activationAssets()` | Read activation assets |
| `R` [PoolRegistry.activationEntry](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | None | `activationEntry()` | Read activation entry |
| `R` [PoolRegistry.configurationRevision](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | None | `configurationRevision()` | Read configuration revision |
| `R` [PoolRegistry.contributionPool](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | None | `contributionPool()` | Read current contribution pool |
| `R` [PoolRegistry.contributionValue](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `poolId: bytes32`<br>`amount0: uint256`<br>`amount1: uint256` | `contributionValue(POOL_ID, AMOUNT0, AMOUNT1)` | Read contribution value |
| `R` [PoolRegistry.exists](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `input0: bytes32` | `exists(POOL_ID)` | Read exists |
| `R` [PoolRegistry.get](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `poolId: bytes32` | `get(POOL_ID)` | Read get |
| `R` [PoolRegistry.isNativePool](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `poolId: bytes32` | `isNativePool(POOL_ID)` | Read is native pool |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [PoolRegistry.applyKeeperRange](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `poolId: bytes32`<br>`width: uint16` | `applyKeeperRange(POOL_ID, WIDTH)` | Apply approved range choice |

</details>

<a id="zzzactivationassets"></a>

#### ActivationAssets

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `B` [ActivationAssets.configureZZZ](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `token: address`<br>`expectedCodeHash: bytes32`<br>`reviewHash: bytes32` | `configureZZZ(ZZZ_ADDRESS, EXPECTED_CODE_HASH, REVIEW_HASH)` | Bind fixed ZZZ identity |
| `G` [ActivationAssets.setAsset](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `token: address`<br>`enabled: bool`<br>`expectedCodeHash: bytes32`<br>`reviewHash: bytes32` | `setAsset(ZZZ_ADDRESS, true, EXPECTED_CODE_HASH, REVIEW_HASH)` | Enable or disable contribution asset |

<details>
<summary>Read functions and constants (11)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [ActivationAssets.NATIVE_ASSET_CODE_HASH](CONTRACT_FUNCTIONS.md#zzzactivationassets) | None | `NATIVE_ASSET_CODE_HASH()` | Read native asset code hash |
| `R` [ActivationAssets.SOURCE_POLICY_VERSION](CONTRACT_FUNCTIONS.md#zzzactivationassets) | None | `SOURCE_POLICY_VERSION()` | Read source policy version |
| `R` [ActivationAssets.access](CONTRACT_FUNCTIONS.md#zzzactivationassets) | None | `access()` | Read access |
| `R` [ActivationAssets.activePolicy](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `input0: address` | `activePolicy(TARGET_ADDRESS)` | Read active policy |
| `R` [ActivationAssets.isContributionAsset](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `token: address` | `isContributionAsset(ZZZ_ADDRESS)` | Read is contribution asset |
| `R` [ActivationAssets.policies](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `input0: bytes32` | `policies(ASSET_POLICY_ID)` | Read policies |
| `R` [ActivationAssets.policyAt](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `ordinal: uint256` | `policyAt(1)` | Read policy at |
| `R` [ActivationAssets.policyCount](CONTRACT_FUNCTIONS.md#zzzactivationassets) | None | `policyCount()` | Read policy count |
| `R` [ActivationAssets.registry](CONTRACT_FUNCTIONS.md#zzzactivationassets) | None | `registry()` | Read registry |
| `R` [ActivationAssets.value](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `token: address`<br>`amount: uint256` | `value(ZZZ_ADDRESS, AMOUNT)` | Value reviewed asset amount |
| `R` [ActivationAssets.zzz](CONTRACT_FUNCTIONS.md#zzzactivationassets) | None | `zzz()` | Read zzz |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [ActivationAssets.admitPoolAsset](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `token: address` | `admitPoolAsset(ZZZ_ADDRESS)` | Register pool asset identity |

</details>

<a id="zzzportfoliopolicy"></a>

#### PortfolioPolicy

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [PortfolioPolicy.setMode](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32`<br>`next: bool`<br>`reviewed: bytes32` | `setMode(POOL_ID, NEXT, REVIEWED)` | Enable or disable residual |
| `G` [PortfolioPolicy.configureMainAllocation](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32`<br>`next: uint16`<br>`reviewed: bytes32` | `configureMainAllocation(POOL_ID, 6000, REVIEWED)` | Configure minimum main allocation |
| `G` [PortfolioPolicy.configureResidualSide](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32`<br>`next: uint16`<br>`reviewed: bytes32` | `configureResidualSide(POOL_ID, 5000, REVIEW_HASH)` | Configure residual side geometry |
| `G` [PortfolioPolicy.configureResidualGap](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32`<br>`next: uint24`<br>`reviewed: bytes32` | `configureResidualGap(POOL_ID, 1, REVIEWED)` | Configure residual spacing gap |
| `G` [PortfolioPolicy.setTriggerBps](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `next: uint16`<br>`reviewed: bytes32` | `setTriggerBps(8500, REVIEW_HASH)` | Configure portfolio adjustment threshold |

<details>
<summary>Read functions and constants (25)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [PortfolioPolicy.DEFAULT_RESIDUAL_SIDE_BPS](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `DEFAULT_RESIDUAL_SIDE_BPS()` | Read default residual side bps |
| `R` [PortfolioPolicy.HARD_MAXIMUM_RESIDUAL_BPS](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `HARD_MAXIMUM_RESIDUAL_BPS()` | Read hard maximum residual bps |
| `R` [PortfolioPolicy.HARD_MINIMUM_MAIN_BPS](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `HARD_MINIMUM_MAIN_BPS()` | Read hard minimum main bps |
| `R` [PortfolioPolicy.PORTFOLIO_VERSION](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `PORTFOLIO_VERSION()` | Read portfolio version |
| `R` [PortfolioPolicy.access](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `access()` | Read access |
| `R` [PortfolioPolicy.appliedRevision](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `input0: uint256` | `appliedRevision(LP_TOKEN_ID)` | Read applied revision |
| `R` [PortfolioPolicy.configurationPending](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `bucket: uint256` | `configurationPending(BUCKET_ID)` | Read configuration pending |
| `R` [PortfolioPolicy.controlFingerprint](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32` | `controlFingerprint(POOL_ID)` | Read current control identity |
| `R` [PortfolioPolicy.controlRevision](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `input0: bytes32` | `controlRevision(POOL_ID)` | Read control revision |
| `R` [PortfolioPolicy.enabled](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `input0: bytes32` | `enabled(POOL_ID)` | Read enabled |
| `R` [PortfolioPolicy.geometryRevision](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `input0: bytes32` | `geometryRevision(POOL_ID)` | Read geometry revision |
| `R` [PortfolioPolicy.maximumResidualBps](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32` | `maximumResidualBps(POOL_ID)` | Read maximum residual bps |
| `R` [PortfolioPolicy.minimumMainBps](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32` | `minimumMainBps(POOL_ID)` | Read minimum main bps |
| `R` [PortfolioPolicy.modeReviewHash](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `input0: bytes32` | `modeReviewHash(POOL_ID)` | Read mode review hash |
| `R` [PortfolioPolicy.range](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `c` [PoolConfig](#input-poolconfig)<br>`referenceX96: uint160`<br>`orientation: uint8` | `range([["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"], "DEPOSITS_ENABLED", "OPERATIONS_ENABLED", "RANGE_BPS", "TRIGGER_BPS", "MAX_SPOT_DEVIATION_BPS", "MAX_SLIPPAGE_BPS", "MIN_REBALANCE_INTERVAL", "MIN_DEPOSIT_USD", "MAX_POSITION_USD"], REFERENCE_X96, ORIENTATION)` | Read range |
| `R` [PortfolioPolicy.residualGapSpacings](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32` | `residualGapSpacings(POOL_ID)` | Read residual gap spacings |
| `R` [PortfolioPolicy.residualRange](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32`<br>`current: uint160`<br>`mainLower: int24`<br>`mainUpper: int24`<br>`residual0: bool` | `residualRange(POOL_ID, CURRENT, MAIN_LOWER, MAIN_UPPER, RESIDUAL0)` | Read residual range |
| `R` [PortfolioPolicy.residualReviewHash](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `input0: bytes32` | `residualReviewHash(POOL_ID)` | Read residual review hash |
| `R` [PortfolioPolicy.residualSideBps](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `pool: bytes32` | `residualSideBps(POOL_ID)` | Read residual side bps |
| `R` [PortfolioPolicy.revision](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `revision()` | Read revision |
| `R` [PortfolioPolicy.strategy](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `strategy()` | Read strategy |
| `R` [PortfolioPolicy.thresholdBps](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `thresholdBps()` | Read threshold bps |
| `R` [PortfolioPolicy.thresholdSide](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `center: uint160`<br>`lower: int24`<br>`upper: int24`<br>`price: uint160` | `thresholdSide(CENTER, LOWER_TICK, UPPER_TICK, PRICE)` | Read threshold side |
| `R` [PortfolioPolicy.triggerReviewHash](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `triggerReviewHash()` | Read trigger review hash |
| `R` [PortfolioPolicy.triggerRevision](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | None | `triggerRevision()` | Read trigger revision |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [PortfolioPolicy.recordApplied](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `main: uint256`<br>`pool: bytes32` | `recordApplied(LP_TOKEN_ID, POOL_ID)` | Record applied portfolio policy |

</details>

<a id="zzzprotocolpolicy"></a>

#### ProtocolPolicy

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [ProtocolPolicy.setEntryPolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `activationUSD: uint128`<br>`growthUSD: uint128`<br>`maxIdleBps: uint16`<br>`reviewHash: bytes32` | `setEntryPolicy(100000000000000000000, 5000000000000000000, 500, REVIEW_HASH)` | Set future contribution minima |
| `G` [ProtocolPolicy.setMaintenancePolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `maxIdleBps: uint16`<br>`reviewHash: bytes32` | `setMaintenancePolicy(500, REVIEW_HASH)` | Set maintenance idle ceiling |
| `G` [ProtocolPolicy.setGasPolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `payoutGas: uint32`<br>`sourceCallGas: uint32`<br>`royaltySyncGas: uint32`<br>`reviewHash: bytes32` | `setGasPolicy(PAYOUT_GAS, SOURCE_CALL_GAS, ROYALTY_SYNC_GAS, REVIEW_HASH)` | Set bounded callback gas |
| `G` [ProtocolPolicy.setMintPrice](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `price: uint128`<br>`reviewHash: bytes32` | `setMintPrice(50000000000000000, REVIEW_HASH)` | Set future mint price |
| `G` [ProtocolPolicy.proposeMintRecipient](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `candidate: address`<br>`reviewHash: bytes32` | `proposeMintRecipient(CANDIDATE_ADDRESS, REVIEW_HASH)` | Propose future mint recipient |
| `N` [ProtocolPolicy.acceptMintRecipient](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `acceptMintRecipient()` | Accept future mint proceeds |
| `G` [ProtocolPolicy.setEvolutionThresholds](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `enhancedUSD: uint128`<br>`singularityUSD: uint128`<br>`reviewHash: bytes32` | `setEvolutionThresholds(1000000000000000000000, 10000000000000000000000, REVIEW_HASH)` | Set cosmetic evolution thresholds |
| `B` [ProtocolPolicy.configureRandomness](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `coordinator: address`<br>`expectedCodeHash: bytes32`<br>`keyHash: bytes32`<br>`subscriptionId: uint256`<br>`confirmations: uint16`<br>`callbackGas: uint32`<br>`nativePayment: bool`<br>`reviewHash: bytes32` | `configureRandomness(COORDINATOR_ADDRESS, EXPECTED_CODE_HASH, KEY_HASH, SUBSCRIPTION_ID, CONFIRMATIONS, CALLBACK_GAS, NATIVE_PAYMENT, REVIEW_HASH)` | Configure initial randomness provider |
| `G` [ProtocolPolicy.setRandomnessRequestSettings](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `confirmations: uint16`<br>`callbackGas: uint32`<br>`reviewHash: bytes32` | `setRandomnessRequestSettings(CONFIRMATIONS, CALLBACK_GAS, REVIEW_HASH)` | Set future randomness request settings |
| `G` [ProtocolPolicy.rotateRandomness](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `coordinator: address`<br>`expectedCodeHash: bytes32`<br>`keyHash: bytes32`<br>`subscriptionId: uint256`<br>`confirmations: uint16`<br>`callbackGas: uint32`<br>`nativePayment: bool`<br>`reviewHash: bytes32` | `rotateRandomness(COORDINATOR_ADDRESS, EXPECTED_CODE_HASH, KEY_HASH, SUBSCRIPTION_ID, CONFIRMATIONS, CALLBACK_GAS, NATIVE_PAYMENT, REVIEW_HASH)` | Rotate fully drained provider |

<details>
<summary>Read functions and constants (24)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [ProtocolPolicy.MAX_CALL_GAS](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `MAX_CALL_GAS()` | Read max call gas |
| `R` [ProtocolPolicy.MAX_IDLE_BPS](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `MAX_IDLE_BPS()` | Read max idle bps |
| `R` [ProtocolPolicy.MIN_CALL_GAS](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `MIN_CALL_GAS()` | Read min call gas |
| `R` [ProtocolPolicy.PROTOCOL_POLICY_VERSION](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `PROTOCOL_POLICY_VERSION()` | Read protocol policy version |
| `R` [ProtocolPolicy.access](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `access()` | Read access |
| `R` [ProtocolPolicy.configurationHash](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `configurationHash()` | Read configuration hash |
| `R` [ProtocolPolicy.configurationRevision](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `configurationRevision()` | Read configuration revision |
| `R` [ProtocolPolicy.entryFingerprint](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `entryFingerprint()` | Read current contribution policy |
| `R` [ProtocolPolicy.entryPolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `entryPolicy()` | Read entry policy |
| `R` [ProtocolPolicy.gasFingerprint](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `gasFingerprint()` | Read gas fingerprint |
| `R` [ProtocolPolicy.gasPolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `gasPolicy()` | Read gas policy |
| `R` [ProtocolPolicy.maintenanceFingerprint](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `maintenanceFingerprint()` | Read maintenance fingerprint |
| `R` [ProtocolPolicy.maintenancePolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `maintenancePolicy()` | Read maintenance policy |
| `R` [ProtocolPolicy.metadataFingerprint](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `metadataFingerprint()` | Read metadata fingerprint |
| `R` [ProtocolPolicy.metadataPolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `metadataPolicy()` | Read metadata policy |
| `R` [ProtocolPolicy.mintFingerprint](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `mintFingerprint()` | Read mint fingerprint |
| `R` [ProtocolPolicy.payoutGas](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `payoutGas()` | Read payout gas |
| `R` [ProtocolPolicy.royaltySyncGas](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `royaltySyncGas()` | Read royalty sync gas |
| `R` [ProtocolPolicy.saleFingerprint](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `saleFingerprint()` | Read sale fingerprint |
| `R` [ProtocolPolicy.salePolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `salePolicy()` | Read sale policy |
| `R` [ProtocolPolicy.sourceCallGas](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `sourceCallGas()` | Read source call gas |
| `R` [ProtocolPolicy.validateMintRecipient](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `validateMintRecipient()` | Read validate mint recipient |
| `R` [ProtocolPolicy.vrfPolicy](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `vrfPolicy()` | Read vrf policy |
| `R` [ProtocolPolicy.vrfRevision](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | None | `vrfRevision()` | Read vrf revision |

</details>

<a id="zzzoracle"></a>

#### Oracle

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [Oracle.setDualFeed](CONTRACT_FUNCTIONS.md#zzzoracle) | `token: address`<br>`primary` [ZZZOracle.SourcePolicy](#input-zzzoracle-sourcepolicy)<br>`secondary` [ZZZOracle.SourcePolicy](#input-zzzoracle-sourcepolicy)<br>`maxDeviationBps: uint16`<br>`reviewHash: bytes32` | `setDualFeed(ZZZ_ADDRESS, ["PRIMARY_FEED_ADDRESS", "PRIMARY_CODE_HASH", "PRIMARY_INDEPENDENCE_ID", "PRIMARY_MAX_AGE", "PRIMARY_FEED_DECIMALS"], ["SECONDARY_FEED_ADDRESS", "SECONDARY_CODE_HASH", "SECONDARY_INDEPENDENCE_ID", "SECONDARY_MAX_AGE", "SECONDARY_FEED_DECIMALS"], 300, REVIEW_HASH)` | Configure independent price sources |
| `G` [Oracle.setSequencerFeed](CONTRACT_FUNCTIONS.md#zzzoracle) | `source: address`<br>`expectedCodeHash: bytes32`<br>`reviewHash: bytes32` | `setSequencerFeed(SOURCE_ADDRESS, EXPECTED_CODE_HASH, REVIEW_HASH)` | Configure sequencer outage guard |

<details>
<summary>Read functions and constants (21)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Oracle.FINGERPRINT_DOMAIN](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `FINGERPRINT_DOMAIN()` | Read fingerprint domain |
| `R` [Oracle.MAX_DEVIATION_BPS](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `MAX_DEVIATION_BPS()` | Read max deviation bps |
| `R` [Oracle.PRICING_VERSION](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `PRICING_VERSION()` | Read pricing version |
| `R` [Oracle.SEQUENCER_GRACE](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `SEQUENCER_GRACE()` | Read sequencer grace |
| `R` [Oracle.access](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `access()` | Read access |
| `R` [Oracle.activePolicy](CONTRACT_FUNCTIONS.md#zzzoracle) | `input0: address` | `activePolicy(TARGET_ADDRESS)` | Read active policy |
| `R` [Oracle.activeSequencerPolicy](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `activeSequencerPolicy()` | Read active sequencer policy |
| `R` [Oracle.contributionPricing](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `contributionPricing()` | Read contribution pricing |
| `R` [Oracle.policy](CONTRACT_FUNCTIONS.md#zzzoracle) | `id: bytes32` | `policy(PRICE_POLICY_ID)` | Read policy |
| `R` [Oracle.policyAt](CONTRACT_FUNCTIONS.md#zzzoracle) | `ordinal: uint256` | `policyAt(1)` | Read policy at |
| `R` [Oracle.policyCount](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `policyCount()` | Read policy count |
| `R` [Oracle.price](CONTRACT_FUNCTIONS.md#zzzoracle) | `token: address` | `price(ZZZ_ADDRESS)` | Read price |
| `R` [Oracle.priceBounds](CONTRACT_FUNCTIONS.md#zzzoracle) | `token: address` | `priceBounds(ZZZ_ADDRESS)` | Read independent price bounds |
| `R` [Oracle.quote](CONTRACT_FUNCTIONS.md#zzzoracle) | `input: address`<br>`output: address`<br>`amount: uint256` | `quote(INPUT_ADDRESS, OUTPUT_ADDRESS, AMOUNT)` | Quote reviewed asset value |
| `R` [Oracle.referenceX96](CONTRACT_FUNCTIONS.md#zzzoracle) | `token0: address`<br>`token1: address` | `referenceX96(0x0000000000000000000000000000000000000000, ZZZ_ADDRESS)` | Read reference x96 |
| `R` [Oracle.sequencerFeed](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `sequencerFeed()` | Read sequencer feed |
| `R` [Oracle.sequencerPolicies](CONTRACT_FUNCTIONS.md#zzzoracle) | `input0: bytes32` | `sequencerPolicies(SEQUENCER_POLICY_ID)` | Read sequencer policies |
| `R` [Oracle.sequencerPolicyAt](CONTRACT_FUNCTIONS.md#zzzoracle) | `ordinal: uint256` | `sequencerPolicyAt(1)` | Read sequencer policy at |
| `R` [Oracle.sequencerPolicyCount](CONTRACT_FUNCTIONS.md#zzzoracle) | None | `sequencerPolicyCount()` | Read sequencer policy count |
| `R` [Oracle.tokenDecimals](CONTRACT_FUNCTIONS.md#zzzoracle) | `token: address` | `tokenDecimals(ZZZ_ADDRESS)` | Read token decimals |
| `R` [Oracle.value](CONTRACT_FUNCTIONS.md#zzzoracle) | `token: address`<br>`amount: uint256` | `value(ZZZ_ADDRESS, AMOUNT)` | Value reviewed asset amount |

</details>

<a id="zzzlpbalancer"></a>

#### LPBalancer

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [LPBalancer.configureExecutionPools](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `pools: bytes32[]`<br>`reviewHash: bytes32` | `configureExecutionPools(["POOLS"], REVIEWED_ROUTE_ID)` | Configure reviewed execution venues |
| `G` [LPBalancer.configureSolver](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `iterations: uint8`<br>`gasLimit: uint32`<br>`reviewHash: bytes32` | `configureSolver(ITERATIONS, GAS_LIMIT, REVIEW_HASH)` | Configure bounded sizing solver |

<details>
<summary>Read functions and constants (18)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [LPBalancer.EXECUTION_QUALITY_VERSION](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `EXECUTION_QUALITY_VERSION()` | Read execution quality version |
| `R` [LPBalancer.LP_ROUTING_VERSION](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `LP_ROUTING_VERSION()` | Read lp routing version |
| `R` [LPBalancer.MAX_ADDITIONAL_LOSS_BPS](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `MAX_ADDITIONAL_LOSS_BPS()` | Read max additional loss bps |
| `R` [LPBalancer.MAX_EXECUTION_POOLS](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `MAX_EXECUTION_POOLS()` | Read max execution pools |
| `R` [LPBalancer.access](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `access()` | Read access |
| `R` [LPBalancer.additionalLossBps](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `additionalLossBps()` | Read additional loss bps |
| `R` [LPBalancer.balanceMath](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `balanceMath()` | Read balance math |
| `R` [LPBalancer.deploymentAmounts](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `current: uint160`<br>`lower: int24`<br>`upper: int24`<br>`amount0: uint256`<br>`amount1: uint256` | `deploymentAmounts(CURRENT, LOWER_TICK, UPPER_TICK, AMOUNT0, AMOUNT1)` | Read deployment amounts |
| `R` [LPBalancer.executionPoolAt](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `index: uint256` | `executionPoolAt(0)` | Read execution pool at |
| `R` [LPBalancer.executionPoolCount](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `executionPoolCount()` | Read execution pool count |
| `R` [LPBalancer.executionRevision](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `executionRevision()` | Read execution revision |
| `R` [LPBalancer.liquidityManager](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `liquidityManager()` | Read liquidity manager |
| `R` [LPBalancer.policyFingerprint](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `target: bytes32`<br>`venue: bytes32` | `policyFingerprint(POOL_ID, POOL_ID)` | Read policy fingerprint |
| `R` [LPBalancer.poolManager](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `poolManager()` | Read pool manager |
| `R` [LPBalancer.principalAmounts](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `id: uint256` | `principalAmounts(LP_TOKEN_ID)` | Read principal amounts |
| `R` [LPBalancer.quoteGasLimit](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `quoteGasLimit()` | Read quote gas limit |
| `R` [LPBalancer.searchIterations](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `searchIterations()` | Read search iterations |
| `R` [LPBalancer.stateView](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | None | `stateView()` | Read state view |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (5)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [LPBalancer.plan](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `target: bytes32`<br>`lower: int24`<br>`upper: int24`<br>`amount0: uint256`<br>`amount1: uint256` | `plan(TARGET, LOWER_TICK, UPPER_TICK, AMOUNT0, AMOUNT1)` | Plan bounded balancing operation |
| `M` [LPBalancer.planReplacement](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `target: bytes32`<br>`lower: int24`<br>`upper: int24`<br>`amount0: uint256`<br>`amount1: uint256`<br>`mainFloor: uint16`<br>`marks: uint256[4]` | `planReplacement(POOL_ID, LOWER_TICK, UPPER_TICK, AMOUNT0, AMOUNT1, MAIN_FLOOR, ["MARKS", "MARKS", "MARKS", "MARKS"])` | Plan replacement LP inventory |
| `M` [LPBalancer.quoteCandidate](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `key` [PoolKey](#input-poolkey)<br>`direction: bool`<br>`amount: uint256` | `quoteCandidate(["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"], DIRECTION, AMOUNT)` | Quote candidate execution venue |
| `M` [LPBalancer.routePlan](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `x` [ZZZLPBalanceMath.Context](#input-zzzlpbalancemath-context)<br>`id: bytes32`<br>`direction: bool`<br>`requireActive: bool` | `routePlan(["TARGET", "SPOT", "LOWER", "UPPER", "AMOUNT0", "AMOUNT1", ["LOWER0", "UPPER0", "LOWER1", "UPPER1", "SCALE1", "REFERENCE_X96", "EXTRA_LOSS"], "MAIN_FLOOR", ["MARKS", "MARKS", "MARKS", "MARKS"]], POOL_ID, DIRECTION, REQUIRE_ACTIVE)` | Choose reviewed balancing route |
| `C` [LPBalancer.unlockCallback](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `data: bytes` | `unlockCallback(0x)` | Settle authenticated core callback |

</details>

<a id="zzzmigrationbudget"></a>

#### MigrationBudget

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [MigrationBudget.setCompoundInterval](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `poolId: bytes32`<br>`interval: uint32` | `setCompoundInterval(POOL_ID, 3600)` | Set standalone compounding interval |
| `G` [MigrationBudget.setLossLimits](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `contribution: uint16`<br>`maintenance: uint16` | `setLossLimits(200, 300)` | Set contribution/maintenance loss limits |

<details>
<summary>Read functions and constants (41)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [MigrationBudget.DEFAULT_COMPOUND_INTERVAL](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `DEFAULT_COMPOUND_INTERVAL()` | Read default compound interval |
| `R` [MigrationBudget.EMERGENCY_REBALANCE_VERSION](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `EMERGENCY_REBALANCE_VERSION()` | Read emergency rebalance version |
| `R` [MigrationBudget.IDLE_COMPOUNDING_VERSION](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `IDLE_COMPOUNDING_VERSION()` | Read idle compounding version |
| `R` [MigrationBudget.MAX_LOSS_BPS](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `MAX_LOSS_BPS()` | Read max loss bps |
| `R` [MigrationBudget.REBALANCE_CONFIRMATION_VERSION](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `REBALANCE_CONFIRMATION_VERSION()` | Read rebalance confirmation version |
| `R` [MigrationBudget.access](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `access()` | Read access |
| `R` [MigrationBudget.assertDeployed](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `assertDeployed(BUCKET_ID)` | Read assert deployed |
| `R` [MigrationBudget.assertIdle](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `assertIdle(BUCKET_ID)` | Read assert idle |
| `R` [MigrationBudget.assertIdleLoss](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`beforeValue: uint256` | `assertIdleLoss(BUCKET_ID, BEFORE_VALUE)` | Read assert idle loss |
| `R` [MigrationBudget.assertPut](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`a0: uint256`<br>`a1: uint256`<br>`spent0: uint256`<br>`spent1: uint256`<br>`before0: uint256`<br>`before1: uint256` | `assertPut(BUCKET_ID, A0, A1, SPENT0, SPENT1, BEFORE0, BEFORE1)` | Read assert put |
| `R` [MigrationBudget.balanceContext](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `balanceContext(BUCKET_ID)` | Read balance context |
| `R` [MigrationBudget.compositionEpoch](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `input0: uint256` | `compositionEpoch(BUCKET_ID)` | Read composition epoch |
| `R` [MigrationBudget.compoundInterval](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `poolId: bytes32` | `compoundInterval(POOL_ID)` | Read compound interval |
| `R` [MigrationBudget.compoundReady](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `compoundReady(BUCKET_ID)` | Read compound ready |
| `R` [MigrationBudget.contributionLossBps](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `contributionLossBps()` | Read contribution loss bps |
| `R` [MigrationBudget.emergencyActive](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `emergencyActive()` | Read emergency active |
| `R` [MigrationBudget.emergencyBucket](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `emergencyBucket()` | Read emergency bucket |
| `R` [MigrationBudget.emergencyChecks](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `emergencyChecks()` | Read emergency checks |
| `R` [MigrationBudget.emergencyFingerprint](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `emergencyFingerprint()` | Read emergency fingerprint |
| `R` [MigrationBudget.historicalCompoundValue](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `historicalCompoundValue(BUCKET_ID)` | Read historical compound value |
| `R` [MigrationBudget.idleValue](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `idleValue(BUCKET_ID)` | Read idle value |
| `R` [MigrationBudget.lastCompound](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `input0: uint256` | `lastCompound(BUCKET_ID)` | Read last compound |
| `R` [MigrationBudget.maintenanceBucket](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `maintenanceBucket()` | Read maintenance bucket |
| `R` [MigrationBudget.maintenanceLossBps](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `maintenanceLossBps()` | Read maintenance loss bps |
| `R` [MigrationBudget.maintenancePrices](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `maintenancePrices()` | Read maintenance prices |
| `R` [MigrationBudget.mintTarget](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `mintTarget(BUCKET_ID)` | Read mint target |
| `R` [MigrationBudget.nav](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `nav(BUCKET_ID)` | Read nav |
| `R` [MigrationBudget.poolTokens](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `poolId: bytes32` | `poolTokens(POOL_ID)` | Read pool tokens |
| `R` [MigrationBudget.validateCanonicalWriter](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `caller: address` | `validateCanonicalWriter(CALLER_ADDRESS)` | Read validate canonical writer |
| `R` [MigrationBudget.validateEmergency](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `bucket: uint256` | `validateEmergency(BUCKET_ID)` | Read validate emergency |
| `R` [MigrationBudget.validateHolderExit](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`migrationCaller: address` | `validateHolderExit(BUCKET_ID, MIGRATION_CALLER_ADDRESS)` | Read validate holder exit |
| `R` [MigrationBudget.validateLPReceiver](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `sender: address` | `validateLPReceiver(SENDER_ADDRESS)` | Read validate lpreceiver |
| `R` [MigrationBudget.validateMove](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`nextPool: bytes32`<br>`minimumLiquidity: uint128` | `validateMove(BUCKET_ID, POOL_ID, MINIMUM_LIQUIDITY)` | Read validate move |
| `R` [MigrationBudget.validateNativeSender](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `sender: address` | `validateNativeSender(SENDER_ADDRESS)` | Read validate native sender |
| `R` [MigrationBudget.validateOwner](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`caller: address`<br>`minted: bool`<br>`activation: bool` | `validateOwner(NFT_ID, CALLER_ADDRESS, MINTED, ACTIVATION)` | Read validate owner |
| `R` [MigrationBudget.validateRebalance](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`minimumLiquidity: uint128` | `validateRebalance(BUCKET_ID, MINIMUM_LIQUIDITY)` | Read validate rebalance |
| `R` [MigrationBudget.validateReservation](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `poolId: bytes32`<br>`bucket: uint256` | `validateReservation(POOL_ID, BUCKET_ID)` | Read validate reservation |
| `R` [MigrationBudget.validateResidualClose](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `validateResidualClose(BUCKET_ID)` | Read validate residual close |
| `R` [MigrationBudget.validateUnwind](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `validateUnwind(BUCKET_ID)` | Read validate unwind |
| `R` [MigrationBudget.valueBucket](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `bucket: uint256`<br>`amount0: uint256`<br>`amount1: uint256` | `valueBucket(BUCKET_ID, AMOUNT0, AMOUNT1)` | Read value bucket |
| `R` [MigrationBudget.vault](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `vault()` | Read vault |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (8)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [MigrationBudget.beginEmergency](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `bucket: uint256`<br>`checks: uint8` | `beginEmergency(BUCKET_ID, 31)` | Begin reviewed emergency context |
| `M` [MigrationBudget.checkpoint](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`phase: uint8` | `checkpoint(BUCKET_ID, PHASE)` | Capture maintenance valuation |
| `M` [MigrationBudget.contributionNav](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `contributionNav(BUCKET_ID)` | Measure incumbent attributed NAV |
| `M` [MigrationBudget.contributionResult](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `bucket: uint256`<br>`inputUSD: uint256`<br>`supply: uint256`<br>`incumbentNAV: uint256`<br>`incumbentDeployed: uint256`<br>`deployed: uint256`<br>`idle: uint256`<br>`limits: uint32` | `contributionResult(BUCKET_ID, INPUT_USD, SUPPLY, INCUMBENT_NAV, INCUMBENT_DEPLOYED, DEPLOYED, IDLE, LIMITS)` | Verify contribution deployment result |
| `M` [MigrationBudget.endEmergency](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | None | `endEmergency()` | Close emergency operation context |
| `M` [MigrationBudget.importComposition](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`epoch: uint64` | `importComposition(BUCKET_ID, EPOCH)` | Import physical portfolio accounting |
| `M` [MigrationBudget.recordComposition](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256` | `recordComposition(BUCKET_ID)` | Record physical portfolio accounting |
| `M` [MigrationBudget.validateContribution](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `id: uint256`<br>`bucket: uint256`<br>`inputUSD: uint256`<br>`inputTotal: uint256`<br>`minimumLiquidity: uint128`<br>`activation: bool` | `validateContribution(NFT_ID, BUCKET_ID, INPUT_USD, INPUT_TOTAL, MINIMUM_LIQUIDITY, ACTIVATION)` | Verify isolated contribution floors |

</details>

<a id="calls-revenue"></a>

### LP rewards, royalties and claims

<a id="zzzfeecontroller"></a>

#### FeeController

<details>
<summary>Read functions and constants (9)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [FeeController.FEE_INTAKE_VERSION](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | None | `FEE_INTAKE_VERSION()` | Read fee intake version |
| `R` [FeeController.access](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | None | `access()` | Read access |
| `R` [FeeController.accounted](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `input0: address` | `accounted(TARGET_ADDRESS)` | Read accounted |
| `R` [FeeController.buybackBalance](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `input0: address` | `buybackBalance(TARGET_ADDRESS)` | Read buyback balance |
| `R` [FeeController.canonicalBucketRecord](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `id: uint256`<br>`asset: address` | `canonicalBucketRecord(BUCKET_ID, ASSET_ADDRESS)` | Read canonical bucket record |
| `R` [FeeController.canonicalModule](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | None | `canonicalModule()` | Read canonical module |
| `R` [FeeController.canonicalState](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | None | `canonicalState()` | Read canonical state |
| `R` [FeeController.compoundBalance](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `input0: uint256`<br>`input1: address` | `compoundBalance(BUCKET_ID, TARGET_ADDRESS)` | Read compound balance |
| `R` [FeeController.dust](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `input0: uint256`<br>`input1: address` | `dust(BUCKET_ID, TARGET_ADDRESS)` | Read dust |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (8)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [FeeController.allocate](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `id: uint256`<br>`token: address`<br>`amount: uint256`<br>`value: wei` (separate) | `allocate(BUCKET_ID, ZZZ_ADDRESS, AMOUNT); value=SETTLEMENT_WEI wei` | Split actual harvested fees |
| `M` [FeeController.canonicalBarrier](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | None | `canonicalBarrier()` | Set canonical accounting barrier |
| `M` [FeeController.canonicalFlush](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `id: uint256`<br>`asset: address` | `canonicalFlush(BUCKET_ID, ASSET_ADDRESS)` | Flush captured accounting dust |
| `M` [FeeController.canonicalSend](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `asset: address`<br>`destination: address`<br>`amount: uint256` | `canonicalSend(ASSET_ADDRESS, DESTINATION_ADDRESS, AMOUNT)` | Send authenticated canonical backing |
| `M` [FeeController.canonicalWrite](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `kind: uint8`<br>`record: bytes` | `canonicalWrite(KIND, RECORD)` | Write authenticated imported accounting |
| `M` [FeeController.flushDust](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `id: uint256`<br>`token: address` | `flushDust(BUCKET_ID, ZZZ_ADDRESS)` | Settle incumbent fee dust |
| `M` [FeeController.releaseBuyback](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `token: address`<br>`amount: uint256` | `releaseBuyback(ZZZ_ADDRESS, AMOUNT)` | Release designated buyback reserve |
| `M` [FeeController.releaseCompound](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `id: uint256`<br>`token: address` | `releaseCompound(BUCKET_ID, ZZZ_ADDRESS)` | Release designated compound reserve |

</details>

<a id="zzzmembership"></a>

#### Membership

<details>
<summary>Read functions and constants (7)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Membership.access](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `access()` | Read access |
| `R` [Membership.canonicalAssetCount](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `canonicalAssetCount()` | Read canonical asset count |
| `R` [Membership.canonicalCount](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `canonicalCount()` | Read canonical count |
| `R` [Membership.canonicalExport](CONTRACT_FUNCTIONS.md#zzzmembership) | `row: uint256` | `canonicalExport(0)` | Read canonical export |
| `R` [Membership.canonicalValidate](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `canonicalValidate()` | Validate imported classified backing |
| `R` [Membership.eligible](CONTRACT_FUNCTIONS.md#zzzmembership) | `input0: uint256` | `eligible(NFT_ID)` | Read eligible |
| `R` [Membership.totalEligible](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `totalEligible()` | Read total eligible |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (6)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Membership.activate](CONTRACT_FUNCTIONS.md#zzzmembership) | `id: uint256` | `activate(NFT_ID)` | Register equal collective membership |
| `M` [Membership.canonicalActivate](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `canonicalActivate()` | Activate imported ledger state |
| `M` [Membership.canonicalCapture](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `canonicalCapture()` | Capture classified ledger backing |
| `M` [Membership.canonicalImport](CONTRACT_FUNCTIONS.md#zzzmembership) | `row: uint256`<br>`record: bytes` | `canonicalImport(0, RECORD)` | Import authenticated accounting row |
| `M` [Membership.canonicalSettle](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `canonicalSettle()` | Settle captured reward indexes |
| `M` [Membership.settleDust](CONTRACT_FUNCTIONS.md#zzzmembership) | None | `settleDust()` | Settle pre-membership fee dust |

</details>

<a id="zzzrewards"></a>

#### Rewards

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [Rewards.addAsset](CONTRACT_FUNCTIONS.md#zzzrewards) | `token: address` | `addAsset(ROYALTY_TOKEN_ADDRESS)` | Admit reward currency |
| `B` [Rewards.bindConverter](CONTRACT_FUNCTIONS.md#zzzrewards) | `candidate: address` | `bindConverter(CANDIDATE_ADDRESS)` | Bind conversion implementation once |
| `H` [Rewards.claim](CONTRACT_FUNCTIONS.md#zzzrewards) | `id: uint256`<br>`token: address` | `claim(NFT_ID, 0x0000000000000000000000000000000000000000)` | Claim current owner's rewards |
| `K` [Rewards.convertBatch](CONTRACT_FUNCTIONS.md#zzzrewards) | `token: address`<br>`ids: uint256[]`<br>`routeId: bytes32`<br>`minimumETH: uint256`<br>`deadline: uint256` | `convertBatch(ZZZ_ADDRESS, ["IDS"], REVIEWED_ROUTE_ID, MINIMUM_ETH_WEI, UNIX_DEADLINE)` | Convert earned balances proportionally |

<details>
<summary>Read functions and constants (25)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Rewards.MAX_ASSETS](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `MAX_ASSETS()` | Read max assets |
| `R` [Rewards.MAX_CONVERSION_NFTS](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `MAX_CONVERSION_NFTS()` | Read max conversion nfts |
| `R` [Rewards.MAX_ERC20_ASSETS](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `MAX_ERC20_ASSETS()` | Read max erc20 assets |
| `R` [Rewards.SCALE](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `SCALE()` | Read scale |
| `R` [Rewards.access](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `access()` | Read access |
| `R` [Rewards.assetCount](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `assetCount()` | Read asset count |
| `R` [Rewards.assets](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256` | `assets(0)` | Read assets |
| `R` [Rewards.canonicalAssetCount](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `canonicalAssetCount()` | Read canonical asset count |
| `R` [Rewards.canonicalBacking](CONTRACT_FUNCTIONS.md#zzzrewards) | `i: uint256` | `canonicalBacking(0)` | Read canonical backing |
| `R` [Rewards.canonicalCount](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `canonicalCount()` | Read canonical count |
| `R` [Rewards.canonicalExport](CONTRACT_FUNCTIONS.md#zzzrewards) | `row: uint256` | `canonicalExport(0)` | Read canonical export |
| `R` [Rewards.canonicalValidate](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `canonicalValidate()` | Validate imported classified backing |
| `R` [Rewards.claimable](CONTRACT_FUNCTIONS.md#zzzrewards) | `id: uint256`<br>`token: address` | `claimable(NFT_ID, ZZZ_ADDRESS)` | Read funded claimable balance |
| `R` [Rewards.collective](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256`<br>`input1: address` | `collective(NFT_ID, TARGET_ADDRESS)` | Read collective |
| `R` [Rewards.converter](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `converter()` | Read converter |
| `R` [Rewards.fraction](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256`<br>`input1: address` | `fraction(NFT_ID, TARGET_ADDRESS)` | Read fraction |
| `R` [Rewards.index](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: address` | `index(TARGET_ADDRESS)` | Read index |
| `R` [Rewards.individual](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256`<br>`input1: address` | `individual(NFT_ID, TARGET_ADDRESS)` | Read individual |
| `R` [Rewards.isAsset](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: address` | `isAsset(TARGET_ADDRESS)` | Read is asset |
| `R` [Rewards.liabilities](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: address` | `liabilities(TARGET_ADDRESS)` | Read liabilities |
| `R` [Rewards.orphaned](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: address` | `orphaned(TARGET_ADDRESS)` | Read orphaned |
| `R` [Rewards.ownerFraction](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256`<br>`input1: address` | `ownerFraction(NFT_ID, TARGET_ADDRESS)` | Read owner fraction |
| `R` [Rewards.ownerIndex](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256`<br>`input1: address` | `ownerIndex(BUCKET_ID, TARGET_ADDRESS)` | Read owner index |
| `R` [Rewards.paidIndex](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256`<br>`input1: address` | `paidIndex(NFT_ID, TARGET_ADDRESS)` | Read paid index |
| `R` [Rewards.paidOwnerIndex](CONTRACT_FUNCTIONS.md#zzzrewards) | `input0: uint256`<br>`input1: address` | `paidOwnerIndex(NFT_ID, TARGET_ADDRESS)` | Read paid owner index |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (12)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Rewards.canonicalAccept](CONTRACT_FUNCTIONS.md#zzzrewards) | `i: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalAccept(0, TARGET_ADDRESS); value=0 wei` | Accept authenticated classified backing |
| `M` [Rewards.canonicalActivate](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `canonicalActivate()` | Activate imported ledger state |
| `M` [Rewards.canonicalCapture](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `canonicalCapture()` | Capture classified ledger backing |
| `M` [Rewards.canonicalImport](CONTRACT_FUNCTIONS.md#zzzrewards) | `row: uint256`<br>`record: bytes` | `canonicalImport(0, RECORD)` | Import authenticated accounting row |
| `M` [Rewards.canonicalRelease](CONTRACT_FUNCTIONS.md#zzzrewards) | `i: uint256`<br>`destination: address` | `canonicalRelease(0, DESTINATION_ADDRESS)` | Release authenticated classified backing |
| `M` [Rewards.canonicalRestore](CONTRACT_FUNCTIONS.md#zzzrewards) | `i: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalRestore(0, TARGET_ADDRESS); value=0 wei` | Restore captured source backing |
| `M` [Rewards.canonicalSettle](CONTRACT_FUNCTIONS.md#zzzrewards) | None | `canonicalSettle()` | Settle captured reward indexes |
| `M` [Rewards.checkpointAll](CONTRACT_FUNCTIONS.md#zzzrewards) | `id: uint256` | `checkpointAll(NFT_ID)` | Checkpoint active collective members |
| `M` [Rewards.checkpointOwner](CONTRACT_FUNCTIONS.md#zzzrewards) | `id: uint256` | `checkpointOwner(NFT_ID)` | Checkpoint individual NFT rewards |
| `M` [Rewards.claimFor](CONTRACT_FUNCTIONS.md#zzzrewards) | `id: uint256`<br>`token: address`<br>`owner: address` | `claimFor(NFT_ID, 0x0000000000000000000000000000000000000000, OWNER_ADDRESS)` | Forward authenticated owner claim |
| `M` [Rewards.creditCanonicalCutoff](CONTRACT_FUNCTIONS.md#zzzrewards) | `bucketId: uint256`<br>`token: address`<br>`personal: uint256`<br>`shared: uint256`<br>`value: wei` (separate) | `creditCanonicalCutoff(BUCKET_ID, ZZZ_ADDRESS, PERSONAL, SHARED); value=SETTLEMENT_WEI wei` | Credit captured cutoff rewards |
| `M` [Rewards.creditPool](CONTRACT_FUNCTIONS.md#zzzrewards) | `bucketId: uint256`<br>`token: address`<br>`personal: uint256`<br>`shared: uint256`<br>`value: wei` (separate) | `creditPool(BUCKET_ID, ZZZ_ADDRESS, PERSONAL, SHARED); value=SETTLEMENT_WEI wei` | Credit funded LP rewards |

</details>

<a id="zzzroyaltyrewards"></a>

#### RoyaltyRewards

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `P` [RoyaltyRewards.sync](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address` | `sync(ASSET_ADDRESS)` | Synchronize actual royalty receipts |
| `P` [RoyaltyRewards.syncAll](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `syncAll()` | Synchronize all admitted currencies |
| `G` [RoyaltyRewards.allocateUnallocated](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address`<br>`amount: uint256`<br>`reviewHash: bytes32` | `allocateUnallocated(ADMITTED_ROYALTY_ASSET, UNALLOCATED_RAW_AMOUNT, REVIEW_HASH)` | Allocate reviewed original-currency royalties |
| `H` [RoyaltyRewards.claim](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `id: uint256`<br>`asset: address` | `claim(NFT_ID, 0x0000000000000000000000000000000000000000)` | Claim current owner's rewards |
| `P` [RoyaltyRewards.forwardLate](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address` | `forwardLate(ASSET_ADDRESS)` | Forward receipts to successor |
| `P` [RoyaltyRewards.fund](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address`<br>`amount: uint256` | `fund(ASSET_ADDRESS, AMOUNT)` | Fund actual received royalties |
| `G` [RoyaltyRewards.allocateAllUnallocated](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address`<br>`reviewHash: bytes32` | `allocateAllUnallocated(ADMITTED_ROYALTY_ASSET, REVIEW_HASH)` | Allocate all unallocated royalties |

<details>
<summary>Read functions and constants (38)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [RoyaltyRewards.ACTIVATION_WINDOW](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `ACTIVATION_WINDOW()` | Read activation grace duration |
| `R` [RoyaltyRewards.MAX_ASSETS](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `MAX_ASSETS()` | Read max assets |
| `R` [RoyaltyRewards.MAX_ERC20_ASSETS](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `MAX_ERC20_ASSETS()` | Read max erc20 assets |
| `R` [RoyaltyRewards.ROYALTY_RECOVERY_VERSION](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `ROYALTY_RECOVERY_VERSION()` | Read royalty recovery version |
| `R` [RoyaltyRewards.ROYALTY_SETTLEMENT_VERSION](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `ROYALTY_SETTLEMENT_VERSION()` | Read original-currency capability |
| `R` [RoyaltyRewards.SCALE](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `SCALE()` | Read scale |
| `R` [RoyaltyRewards.accounted](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `accounted(TARGET_ADDRESS)` | Read accounted |
| `R` [RoyaltyRewards.accrued](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: uint256`<br>`input1: address` | `accrued(NFT_ID, TARGET_ADDRESS)` | Read accrued |
| `R` [RoyaltyRewards.activationCount](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `activationCount()` | Read activation count |
| `R` [RoyaltyRewards.activationOrdinal](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: uint256` | `activationOrdinal(NFT_ID)` | Read activation ordinal |
| `R` [RoyaltyRewards.assetCapacity](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `assetCapacity()` | Read operating currency capacity |
| `R` [RoyaltyRewards.assetCount](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `assetCount()` | Read asset count |
| `R` [RoyaltyRewards.assets](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: uint256` | `assets(0)` | Read assets |
| `R` [RoyaltyRewards.canonicalAssetCount](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `canonicalAssetCount()` | Read canonical asset count |
| `R` [RoyaltyRewards.canonicalBacking](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `i: uint256` | `canonicalBacking(0)` | Read canonical backing |
| `R` [RoyaltyRewards.canonicalController](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `canonicalController()` | Read canonical controller |
| `R` [RoyaltyRewards.canonicalCount](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `canonicalCount()` | Read canonical count |
| `R` [RoyaltyRewards.canonicalExport](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `row: uint256` | `canonicalExport(0)` | Read canonical export |
| `R` [RoyaltyRewards.canonicalValidate](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `canonicalValidate()` | Validate imported classified backing |
| `R` [RoyaltyRewards.claimable](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `id: uint256`<br>`asset: address` | `claimable(NFT_ID, ASSET_ADDRESS)` | Read funded claimable balance |
| `R` [RoyaltyRewards.effectiveEligibleCount](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address` | `effectiveEligibleCount(ADMITTED_ROYALTY_ASSET)` | Read effective eligible prefix |
| `R` [RoyaltyRewards.eligibleCount](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `eligibleCount(TARGET_ADDRESS)` | Read eligible count |
| `R` [RoyaltyRewards.eligibleFor](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `id: uint256`<br>`asset: address` | `eligibleFor(NFT_ID, ASSET_ADDRESS)` | Read eligible for |
| `R` [RoyaltyRewards.eligibleWeight](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `eligibleWeight(TARGET_ADDRESS)` | Read eligible weight |
| `R` [RoyaltyRewards.fraction](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: uint256`<br>`input1: address` | `fraction(NFT_ID, TARGET_ADDRESS)` | Read fraction |
| `R` [RoyaltyRewards.index](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `index(TARGET_ADDRESS)` | Read index |
| `R` [RoyaltyRewards.isAsset](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `isAsset(TARGET_ADDRESS)` | Read is asset |
| `R` [RoyaltyRewards.liabilities](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `liabilities(TARGET_ADDRESS)` | Read liabilities |
| `R` [RoyaltyRewards.mintEnd](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `mintEnd()` | Read official sale end |
| `R` [RoyaltyRewards.nft](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `nft()` | Read nft |
| `R` [RoyaltyRewards.openingPool](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `openingPool(ADMITTED_ROYALTY_ASSET)` | Read initial royalty pool |
| `R` [RoyaltyRewards.orphaned](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: address` | `orphaned(TARGET_ADDRESS)` | Read orphaned |
| `R` [RoyaltyRewards.paidIndex](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: uint256`<br>`input1: address` | `paidIndex(NFT_ID, TARGET_ADDRESS)` | Read paid index |
| `R` [RoyaltyRewards.pending](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address` | `pending(ASSET_ADDRESS)` | Read unprocessed royalty receipts |
| `R` [RoyaltyRewards.royaltiesOpen](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `royaltiesOpen()` | Check royalty claim opening |
| `R` [RoyaltyRewards.royaltiesOpenAt](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `royaltiesOpenAt()` | Read royalty opening time |
| `R` [RoyaltyRewards.totalWeight](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `totalWeight()` | Read total weight |
| `R` [RoyaltyRewards.weightOf](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `input0: uint256` | `weightOf(NFT_ID)` | Read weight of |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (14)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [RoyaltyRewards.activate](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `id: uint256`<br>`weight: uint256` | `activate(NFT_ID, WEIGHT)` | Register activated royalty weight |
| `M` [RoyaltyRewards.addAsset](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `token: address` | `addAsset(ROYALTY_TOKEN_ADDRESS)` | Admit reward currency |
| `M` [RoyaltyRewards.bindCanonicalController](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `controller: address` | `bindCanonicalController(CONTROLLER_ADDRESS)` | Bind canonical controller once |
| `M` [RoyaltyRewards.canonicalAccept](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `i: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalAccept(0, TARGET_ADDRESS); value=0 wei` | Accept authenticated classified backing |
| `M` [RoyaltyRewards.canonicalActivate](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `canonicalActivate()` | Activate imported ledger state |
| `M` [RoyaltyRewards.canonicalCapture](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `canonicalCapture()` | Capture classified ledger backing |
| `M` [RoyaltyRewards.canonicalImport](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `row: uint256`<br>`record: bytes` | `canonicalImport(0, RECORD)` | Import authenticated accounting row |
| `M` [RoyaltyRewards.canonicalRelease](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `i: uint256`<br>`destination: address` | `canonicalRelease(0, DESTINATION_ADDRESS)` | Release authenticated classified backing |
| `M` [RoyaltyRewards.canonicalRestore](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `i: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalRestore(0, TARGET_ADDRESS); value=0 wei` | Restore captured source backing |
| `M` [RoyaltyRewards.canonicalSettle](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | None | `canonicalSettle()` | Settle captured reward indexes |
| `M` [RoyaltyRewards.claimFor](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `id: uint256`<br>`asset: address`<br>`owner: address` | `claimFor(NFT_ID, 0x0000000000000000000000000000000000000000, OWNER_ADDRESS)` | Forward authenticated owner claim |
| `M` [RoyaltyRewards.increaseAssetCapacity](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `capacity: uint8`<br>`reviewHash: bytes32` | `increaseAssetCapacity(32, CAPACITY_REVIEW_HASH)` | Increase authenticated currency capacity |
| `M` [RoyaltyRewards.setMintEnd](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `end: uint64` | `setMintEnd(OFFICIAL_MINT_END_UNIX_SECONDS)` | Set authenticated sale end |
| `M` [RoyaltyRewards.syncForActivation](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `asset: address` | `syncForActivation(ASSET_ADDRESS)` | Isolate optional currency synchronization |

</details>

<a id="zzzlprewardconverter"></a>

#### LPRewardConverter

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [LPRewardConverter.addRoute](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `policy` [ZZZRewardConverter.RoutePolicy](#input-zzzrewardconverter-routepolicy) | `addRoute(["SOURCE_ADDRESS", "ROUTER_ADDRESS", "FACTORY_ADDRESS", "POOL_ADDRESS", "FEE", "SOURCE_CODE_HASH", "ROUTER_CODE_HASH", "FACTORY_CODE_HASH", "POOL_CODE_HASH", "REVIEW_HASH"])` | Admit reviewed swap route |
| `G` [LPRewardConverter.addV4Route](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `policy` [ZZZV4RouteExecutor.Policy](#input-zzzv4routeexecutor-policy) | `addV4Route(["SOURCE_ADDRESS", "OUTPUT_ADDRESS", ["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"], "POOL_MANAGER_ADDRESS", "STATE_VIEW_ADDRESS", "SOURCE_CODE_HASH", "OUTPUT_CODE_HASH", "POOL_MANAGER_CODE_HASH", "STATE_VIEW_CODE_HASH", "REVIEW_HASH"])` | Admit native conversion route |
| `G` [LPRewardConverter.configureWrapper](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `policy` [ZZZRewardConverter.WrapperPolicy](#input-zzzrewardconverter-wrapperpolicy) | `configureWrapper(["CODE_HASH", "ADMIN_ADDRESS", "IMPLEMENTATION_ADDRESS", "ADMIN_OWNER_ADDRESS", "ADMIN_CODE_HASH", "IMPLEMENTATION_CODE_HASH", "REVIEW_HASH"])` | Configure reviewed wrapper policy |
| `G` [LPRewardConverter.setConversionLossBps](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `value: uint16` | `setConversionLossBps(100)` | Set conversion execution-loss limit |
| `G` [LPRewardConverter.setEnabled](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `value: bool` | `setEnabled(VALUE)` | Enable or disable conversion |
| `G` [LPRewardConverter.setRouteEnabled](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `id: bytes32`<br>`value: bool` | `setRouteEnabled(REVIEWED_ROUTE_ID, VALUE)` | Enable or disable reviewed route |

<details>
<summary>Read functions and constants (13)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [LPRewardConverter.MAX_LOSS_BPS](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `MAX_LOSS_BPS()` | Read max loss bps |
| `R` [LPRewardConverter.access](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `access()` | Read access |
| `R` [LPRewardConverter.conversionLossBps](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `conversionLossBps()` | Read conversion loss bps |
| `R` [LPRewardConverter.enabled](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `enabled()` | Read enabled |
| `R` [LPRewardConverter.ledger](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `ledger()` | Read ledger |
| `R` [LPRewardConverter.route](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `id: bytes32` | `route(REVIEWED_ROUTE_ID)` | Read route |
| `R` [LPRewardConverter.routeEnabled](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `id: bytes32` | `routeEnabled(REVIEWED_ROUTE_ID)` | Read route enabled |
| `R` [LPRewardConverter.routeExists](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `id: bytes32` | `routeExists(REVIEWED_ROUTE_ID)` | Read route exists |
| `R` [LPRewardConverter.routeKind](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `id: bytes32` | `routeKind(REVIEWED_ROUTE_ID)` | Read route kind |
| `R` [LPRewardConverter.v4Executor](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `v4Executor()` | Read v4 executor |
| `R` [LPRewardConverter.v4Route](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `id: bytes32` | `v4Route(REVIEWED_ROUTE_ID)` | Read v4 route |
| `R` [LPRewardConverter.wrapper](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `wrapper()` | Read wrapper |
| `R` [LPRewardConverter.wrapperPolicy](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | None | `wrapperPolicy()` | Read wrapper policy |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [LPRewardConverter.convert](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `source: address`<br>`amount: uint256`<br>`routeId: bytes32`<br>`minimumETH: uint256`<br>`deadline: uint256` | `convert(SOURCE_ADDRESS, AMOUNT, REVIEWED_ROUTE_ID, MINIMUM_ETH_WEI, UNIX_DEADLINE)` | Convert authenticated ledger funds |

</details>

<a id="zzzclaimrouter"></a>

#### ClaimRouter

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `H` [ClaimRouter.claimBatch](CONTRACT_FUNCTIONS.md#zzzclaimrouter) | `claims` [ZZZClaimRouter.Claim[]](#input-zzzclaimrouter-claim-array) | `claimBatch([["NFT_ID", "0x0000000000000000000000000000000000000000", false], ["NFT_ID", "0x0000000000000000000000000000000000000000", true]])` | Claim selected funded rewards |

<details>
<summary>Read functions and constants (4)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [ClaimRouter.MAX_CLAIMS](CONTRACT_FUNCTIONS.md#zzzclaimrouter) | None | `MAX_CLAIMS()` | Read max claims |
| `R` [ClaimRouter.access](CONTRACT_FUNCTIONS.md#zzzclaimrouter) | None | `access()` | Read access |
| `R` [ClaimRouter.nft](CONTRACT_FUNCTIONS.md#zzzclaimrouter) | None | `nft()` | Read nft |
| `R` [ClaimRouter.royalties](CONTRACT_FUNCTIONS.md#zzzclaimrouter) | None | `royalties()` | Read royalties |

</details>

<a id="calls-recovery"></a>

### Parking, holder return and canonical replacement

<a id="zzzmigration"></a>

#### Migration

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [Migration.park](CONTRACT_FUNCTIONS.md#zzzmigration) | `r` [ZZZMigration.ParkingRequest](#input-zzzmigration-parkingrequest) | `park(["BUCKET_ID", "POOL_ID", "LP_TOKEN_ID", "TOTAL_SHARES", "DEPOSIT_USD", "CUSTODY_EPOCH", "CURRENT_NONCE", "0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "MINIMUM0", "MINIMUM1", "UNIX_DEADLINE", "REVIEW_HASH", "PORTFOLIO_HASH"])` | Close LP into attributed idle |
| `G` [Migration.closeResidual](CONTRACT_FUNCTIONS.md#zzzmigration) | `r` [ZZZMigration.ParkingRequest](#input-zzzmigration-parkingrequest) | `closeResidual(["BUCKET_ID", "POOL_ID", "LP_TOKEN_ID", "TOTAL_SHARES", "DEPOSIT_USD", "CUSTODY_EPOCH", "CURRENT_NONCE", "0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "MINIMUM0", "MINIMUM1", "UNIX_DEADLINE", "REVIEW_HASH", "PORTFOLIO_HASH"])` | Close residual; retain main |
| `G` [Migration.resume](CONTRACT_FUNCTIONS.md#zzzmigration) | `id: uint256`<br>`pool: bytes32`<br>`minimum: uint128`<br>`deadline: uint256` | `resume(BUCKET_ID, POOL_ID, MINIMUM, UNIX_DEADLINE)` | Redeploy parked LP principal |
| `G` [Migration.moveFunds](CONTRACT_FUNCTIONS.md#zzzmigration) | `id: uint256`<br>`pool: bytes32`<br>`minimum: uint128`<br>`deadline: uint256` | `moveFunds(BUCKET_ID, POOL_ID, MINIMUM, UNIX_DEADLINE)` | Move LP between admitted pools |
| `G` [Migration.emergencyRebalance](CONTRACT_FUNCTIONS.md#zzzmigration) | `request` [EmergencyRebalance](#input-emergencyrebalance) | `emergencyRebalance(["BUCKET_ID", "CUSTODY_HASH", "31", "LOWER_TICK", "UPPER_TICK", "SWAP_POOL", "ZERO_FOR_ONE", "AMOUNT_IN", "MINIMUM_OUT", "MINIMUM_LIQUIDITY", "UNIX_DEADLINE", "REVIEW_HASH"])` | Force reviewed emergency consolidation |
| `G` [Migration.beginCollectiveExit](CONTRACT_FUNCTIONS.md#zzzmigration) | `reviewHash: bytes32` | `beginCollectiveExit(REVIEW_HASH)` | Start irreversible holder return |
| `G` [Migration.closeBucket](CONTRACT_FUNCTIONS.md#zzzmigration) | `bucket: uint256`<br>`minimumETH: uint256`<br>`minimumZZZ: uint256`<br>`deadline: uint256` | `closeBucket(BUCKET_ID, MINIMUM_ETH_WEI, MINIMUM_ZZZ, UNIX_DEADLINE)` | Close terminal principal bucket |
| `G` [Migration.allocatePrincipal](CONTRACT_FUNCTIONS.md#zzzmigration) | `maximum: uint256` | `allocatePrincipal(MAXIMUM)` | Allocate terminal holder principal |
| `G` [Migration.distributePrincipal](CONTRACT_FUNCTIONS.md#zzzmigration) | `ids: uint256[]` | `distributePrincipal(["NFT_ID"])` | Pay terminal current holders |
| `H` [Migration.claimPrincipal](CONTRACT_FUNCTIONS.md#zzzmigration) | `id: uint256`<br>`recipient: address` | `claimPrincipal(NFT_ID, RECIPIENT_ADDRESS)` | Claim failed principal payout |
| `G` [Migration.invalidateParking](CONTRACT_FUNCTIONS.md#zzzmigration) | `id: uint256` | `invalidateParking(BUCKET_ID)` | Invalidate reviewed parking nonce |
| `B` [Migration.configureZZZ](CONTRACT_FUNCTIONS.md#zzzmigration) | `token: address`<br>`codeHash: bytes32`<br>`reviewHash: bytes32` | `configureZZZ(ZZZ_ADDRESS, CODE_HASH, REVIEW_HASH)` | Bind fixed ZZZ identity |

<details>
<summary>Read functions and constants (28)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [Migration.CUSTODY_VERSION](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `CUSTODY_VERSION()` | Read custody version |
| `R` [Migration.EMERGENCY_REBALANCE_VERSION](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `EMERGENCY_REBALANCE_VERSION()` | Read emergency rebalance version |
| `R` [Migration.MAX_BATCH](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `MAX_BATCH()` | Read max batch |
| `R` [Migration.RESIDUAL_EXIT_VERSION](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `RESIDUAL_EXIT_VERSION()` | Read residual exit version |
| `R` [Migration.access](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `access()` | Read access |
| `R` [Migration.activePlan](CONTRACT_FUNCTIONS.md#zzzmigration) | `input0: uint256` | `activePlan(BUCKET_ID)` | Read active plan |
| `R` [Migration.allocationCursor](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `allocationCursor()` | Read allocation cursor |
| `R` [Migration.bucketSettlement](CONTRACT_FUNCTIONS.md#zzzmigration) | `input0: uint256` | `bucketSettlement(BUCKET_ID)` | Read bucket settlement |
| `R` [Migration.claimablePrincipal](CONTRACT_FUNCTIONS.md#zzzmigration) | `id: uint256` | `claimablePrincipal(NFT_ID)` | Read claimable principal |
| `R` [Migration.currentZZZ](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `currentZZZ()` | Read current zzz |
| `R` [Migration.custodyEpoch](CONTRACT_FUNCTIONS.md#zzzmigration) | `input0: uint256` | `custodyEpoch(BUCKET_ID)` | Read custody epoch |
| `R` [Migration.emergencyCustodyHash](CONTRACT_FUNCTIONS.md#zzzmigration) | `bucket: uint256` | `emergencyCustodyHash(BUCKET_ID)` | Read emergency custody identity |
| `R` [Migration.emergencyFingerprint](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `emergencyFingerprint()` | Read emergency fingerprint |
| `R` [Migration.emergencyRequest](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `emergencyRequest()` | Read emergency request |
| `R` [Migration.emergencyTarget](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `emergencyTarget()` | Read emergency target |
| `R` [Migration.exitMintedCount](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `exitMintedCount()` | Read exit minted count |
| `R` [Migration.exitPhase](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `exitPhase()` | Read exit phase |
| `R` [Migration.exitReviewHash](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `exitReviewHash()` | Read exit review hash |
| `R` [Migration.outstandingCount](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `outstandingCount()` | Read outstanding count |
| `R` [Migration.parkingNonce](CONTRACT_FUNCTIONS.md#zzzmigration) | `input0: uint256` | `parkingNonce(BUCKET_ID)` | Read parking nonce |
| `R` [Migration.principalOf](CONTRACT_FUNCTIONS.md#zzzmigration) | `input0: uint256` | `principalOf(NFT_ID)` | Read principal of |
| `R` [Migration.remainingBuckets](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `remainingBuckets()` | Read remaining buckets |
| `R` [Migration.remainingETH](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `remainingETH()` | Read remaining eth |
| `R` [Migration.remainingZZZ](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `remainingZZZ()` | Read remaining zzz |
| `R` [Migration.settlementBucketAt](CONTRACT_FUNCTIONS.md#zzzmigration) | `index: uint256` | `settlementBucketAt(0)` | Read settlement bucket at |
| `R` [Migration.settlementBucketCount](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `settlementBucketCount()` | Read settlement bucket count |
| `R` [Migration.validation](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `validation()` | Read validation |
| `R` [Migration.zzzCodeHash](CONTRACT_FUNCTIONS.md#zzzmigration) | None | `zzzCodeHash()` | Read zzz code hash |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Migration.payCurrentOwner](CONTRACT_FUNCTIONS.md#zzzmigration) | `id: uint256` | `payCurrentOwner(NFT_ID)` | Pay authenticated current owner |

</details>

<a id="zzzcanonicalhandoff"></a>

#### CanonicalHandoff

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [CanonicalHandoff.abort](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `abort()` | Abort canonical replacement |
| `G` [CanonicalHandoff.commit](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `commit()` | Commit canonical replacement atomically |
| `P` [CanonicalHandoff.completeImport](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `completeImport()` | Complete authenticated row import |
| `P` [CanonicalHandoff.exportRows](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8`<br>`count: uint256` | `exportRows(SLOT, 1)` | Export authenticated canonical rows |
| `G` [CanonicalHandoff.finishAbort](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `finishAbort()` | Finish fully funded abort |
| `G` [CanonicalHandoff.freeze](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `freeze()` | Freeze canonical ownership accounting |
| `P` [CanonicalHandoff.fund](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8`<br>`index: uint256` | `fund(SLOT, 0)` | Transfer authenticated canonical backing |
| `P` [CanonicalHandoff.importRows](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8`<br>`records: bytes[]` | `importRows(SLOT, ["RECORDS"])` | Import authenticated canonical rows |
| `B` [CanonicalHandoff.prepareImport](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `sourceController: address` | `prepareImport(SOURCE_CONTROLLER_ADDRESS)` | Prepare successor import binding |
| `P` [CanonicalHandoff.returnFunds](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8`<br>`index: uint256` | `returnFunds(SLOT, 0)` | Restore selected source backing |
| `P` [CanonicalHandoff.settle](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8` | `settle(SLOT)` | Settle next canonical step |

<details>
<summary>Read functions and constants (22)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [CanonicalHandoff.MAX_ROWS](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `MAX_ROWS()` | Read max rows |
| `R` [CanonicalHandoff.SCHEMA](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `SCHEMA()` | Read schema |
| `R` [CanonicalHandoff.SLOTS](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `SLOTS()` | Read slots |
| `R` [CanonicalHandoff.access](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `access()` | Read access |
| `R` [CanonicalHandoff.assetCount](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint256` | `assetCount(0)` | Read asset count |
| `R` [CanonicalHandoff.deploymentCommitment](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `deploymentCommitment()` | Read deployment commitment |
| `R` [CanonicalHandoff.destinationController](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `destinationController()` | Read destination controller |
| `R` [CanonicalHandoff.exportCursor](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint256` | `exportCursor(0)` | Read export cursor |
| `R` [CanonicalHandoff.exportRoot](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint256` | `exportRoot(0)` | Read export root |
| `R` [CanonicalHandoff.funded](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint8`<br>`input1: uint256` | `funded(0, 0)` | Read funded |
| `R` [CanonicalHandoff.handoffId](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `handoffId()` | Read handoff id |
| `R` [CanonicalHandoff.importComplete](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `importComplete()` | Read import complete |
| `R` [CanonicalHandoff.importCursor](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint256` | `importCursor(0)` | Read import cursor |
| `R` [CanonicalHandoff.importRoot](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint256` | `importRoot(0)` | Read import root |
| `R` [CanonicalHandoff.incomingFunded](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint8`<br>`input1: uint256` | `incomingFunded(0, 0)` | Read incoming funded |
| `R` [CanonicalHandoff.incomingSource](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `incomingSource()` | Read incoming source |
| `R` [CanonicalHandoff.moduleAt](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8` | `moduleAt(SLOT)` | Read module at |
| `R` [CanonicalHandoff.phase](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `phase()` | Read phase |
| `R` [CanonicalHandoff.recordCount](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint256` | `recordCount(0)` | Read record count |
| `R` [CanonicalHandoff.returned](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `input0: uint8`<br>`input1: uint256` | `returned(0, 0)` | Read returned |
| `R` [CanonicalHandoff.settlementCursor](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `settlementCursor()` | Read settlement cursor |
| `R` [CanonicalHandoff.stateRoot](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `stateRoot()` | Read state root |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (5)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [CanonicalHandoff.acceptFunding](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8`<br>`index: uint256` | `acceptFunding(SLOT, 0)` | Acknowledge authenticated funding |
| `M` [CanonicalHandoff.activate](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `activate()` | Activate authenticated successor deployment |
| `M` [CanonicalHandoff.bindFrozen](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `id: bytes32` | `bindFrozen(ID)` | Bind frozen source snapshot |
| `M` [CanonicalHandoff.cancelImport](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | None | `cancelImport()` | Cancel authenticated import |
| `M` [CanonicalHandoff.returnFunding](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `slot: uint8`<br>`index: uint256` | `returnFunding(SLOT, 0)` | Return authenticated abort funding |

</details>

<a id="calls-holders"></a>

### NFTs, contributions and metadata

<a id="zzznft"></a>

#### NFT

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `G` [NFT.addRoyaltyAsset](CONTRACT_FUNCTIONS.md#zzznft) | `token: address` | `addRoyaltyAsset(ROYALTY_TOKEN_ADDRESS)` | Admit royalty payment currency |
| `H` [NFT.approve](CONTRACT_FUNCTIONS.md#zzznft) | `to: address`<br>`tokenId: uint256` | `approve(TO_ADDRESS, NFT_ID)` | Approve one NFT transfer |
| `P` [NFT.finalizeTraits](CONTRACT_FUNCTIONS.md#zzznft) | `id: uint256` | `finalizeTraits(NFT_ID)` | Finalize original artwork draw |
| `G` [NFT.increaseRoyaltyAssetCapacity](CONTRACT_FUNCTIONS.md#zzznft) | `capacity: uint8`<br>`reviewHash: bytes32` | `increaseRoyaltyAssetCapacity(32, CAPACITY_REVIEW_HASH)` | Increase reviewed currency capacity |
| `P` [NFT.refreshMetadata](CONTRACT_FUNCTIONS.md#zzznft) | `id: uint256` | `refreshMetadata(NFT_ID)` | Refresh one NFT metadata |
| `P` [NFT.refreshMetadataRange](CONTRACT_FUNCTIONS.md#zzznft) | `firstOrdinal: uint256`<br>`lastOrdinal: uint256` | `refreshMetadataRange(1, LAST_ORDINAL)` | Refresh bounded metadata range |
| `H` [NFT.safeTransferFrom](CONTRACT_FUNCTIONS.md#zzznft) | `from: address`<br>`to: address`<br>`tokenId: uint256` | `safeTransferFrom(FROM_ADDRESS, TO_ADDRESS, NFT_ID)` | Safely transfer NFT ownership |
| `H` [NFT.safeTransferFrom](CONTRACT_FUNCTIONS.md#zzznft) | `from: address`<br>`to: address`<br>`tokenId: uint256`<br>`data: bytes` | `safeTransferFrom(FROM_ADDRESS, TO_ADDRESS, NFT_ID, 0x)` | Safely transfer NFT ownership |
| `H` [NFT.setApprovalForAll](CONTRACT_FUNCTIONS.md#zzznft) | `operator: address`<br>`approved: bool` | `setApprovalForAll(OPERATOR_ADDRESS, false)` | Set NFT operator approval |
| `B` [NFT.setBaseURI](CONTRACT_FUNCTIONS.md#zzznft) | `baseURI: string` | `setBaseURI(IPFS_BASE_URI)` | Bind permanent artwork base |
| `G` [NFT.setMintEnd](CONTRACT_FUNCTIONS.md#zzznft) | `end: uint64` | `setMintEnd(OFFICIAL_MINT_END_UNIX_SECONDS)` | Set official sale end |
| `G` [NFT.setMintPaused](CONTRACT_FUNCTIONS.md#zzznft) | `state: bool` | `setMintPaused(true)` | Pause or resume minting |
| `H` [NFT.transferFrom](CONTRACT_FUNCTIONS.md#zzznft) | `from: address`<br>`to: address`<br>`tokenId: uint256` | `transferFrom(FROM_ADDRESS, TO_ADDRESS, NFT_ID)` | Transfer NFT ownership |

<details>
<summary>Read functions and constants (44)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [NFT.MAX_METADATA_REFRESH_BATCH](CONTRACT_FUNCTIONS.md#zzznft) | None | `MAX_METADATA_REFRESH_BATCH()` | Read max metadata refresh batch |
| `R` [NFT.MAX_SUPPLY](CONTRACT_FUNCTIONS.md#zzznft) | None | `MAX_SUPPLY()` | Read max supply |
| `R` [NFT.access](CONTRACT_FUNCTIONS.md#zzznft) | None | `access()` | Read access |
| `R` [NFT.artworkBaseURI](CONTRACT_FUNCTIONS.md#zzznft) | None | `artworkBaseURI()` | Read artwork base uri |
| `R` [NFT.balanceOf](CONTRACT_FUNCTIONS.md#zzznft) | `owner: address` | `balanceOf(OWNER_ADDRESS)` | Read balance of |
| `R` [NFT.callbackGasLimit](CONTRACT_FUNCTIONS.md#zzznft) | None | `callbackGasLimit()` | Read callback gas limit |
| `R` [NFT.canonicalArtwork](CONTRACT_FUNCTIONS.md#zzznft) | `rarity: uint8`<br>`item: uint256` | `canonicalArtwork(0, ITEM)` | Read canonical artwork |
| `R` [NFT.canonicalModule](CONTRACT_FUNCTIONS.md#zzznft) | None | `canonicalModule()` | Read canonical module |
| `R` [NFT.canonicalRandomness](CONTRACT_FUNCTIONS.md#zzznft) | `id: uint256` | `canonicalRandomness(NFT_ID)` | Read canonical randomness |
| `R` [NFT.canonicalSuccessor](CONTRACT_FUNCTIONS.md#zzznft) | None | `canonicalSuccessor()` | Read canonical successor |
| `R` [NFT.claimRouter](CONTRACT_FUNCTIONS.md#zzznft) | None | `claimRouter()` | Read claim router |
| `R` [NFT.colorOf](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `colorOf(NFT_ID)` | Read color of |
| `R` [NFT.currentLPValue](CONTRACT_FUNCTIONS.md#zzznft) | `id: uint256` | `currentLPValue(NFT_ID)` | Read current lpvalue |
| `R` [NFT.evolution](CONTRACT_FUNCTIONS.md#zzznft) | `id: uint256` | `evolution(NFT_ID)` | Read evolution |
| `R` [NFT.getApproved](CONTRACT_FUNCTIONS.md#zzznft) | `tokenId: uint256` | `getApproved(NFT_ID)` | Read get approved |
| `R` [NFT.isApprovedForAll](CONTRACT_FUNCTIONS.md#zzznft) | `owner: address`<br>`operator: address` | `isApprovedForAll(OWNER_ADDRESS, OPERATOR_ADDRESS)` | Read is approved for all |
| `R` [NFT.keyHash](CONTRACT_FUNCTIONS.md#zzznft) | None | `keyHash()` | Read key hash |
| `R` [NFT.metadataRenderer](CONTRACT_FUNCTIONS.md#zzznft) | None | `metadataRenderer()` | Read metadata renderer |
| `R` [NFT.mintOrdinalOf](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `mintOrdinalOf(NFT_ID)` | Read mint ordinal of |
| `R` [NFT.mintPaused](CONTRACT_FUNCTIONS.md#zzznft) | None | `mintPaused()` | Read mint paused |
| `R` [NFT.mintedCount](CONTRACT_FUNCTIONS.md#zzznft) | None | `mintedCount()` | Read minted count |
| `R` [NFT.name](CONTRACT_FUNCTIONS.md#zzznft) | None | `name()` | Read name |
| `R` [NFT.nativePayment](CONTRACT_FUNCTIONS.md#zzznft) | None | `nativePayment()` | Read native payment |
| `R` [NFT.nextToFinalize](CONTRACT_FUNCTIONS.md#zzznft) | None | `nextToFinalize()` | Read next to finalize |
| `R` [NFT.ownerOf](CONTRACT_FUNCTIONS.md#zzznft) | `tokenId: uint256` | `ownerOf(NFT_ID)` | Read current NFT owner |
| `R` [NFT.paletteOf](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `paletteOf(NFT_ID)` | Read palette of |
| `R` [NFT.patternOf](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `patternOf(NFT_ID)` | Read pattern of |
| `R` [NFT.randomnessConfigured](CONTRACT_FUNCTIONS.md#zzznft) | None | `randomnessConfigured()` | Read randomness configured |
| `R` [NFT.randomnessCoordinator](CONTRACT_FUNCTIONS.md#zzznft) | None | `randomnessCoordinator()` | Read randomness coordinator |
| `R` [NFT.randomnessEpoch](CONTRACT_FUNCTIONS.md#zzznft) | None | `randomnessEpoch()` | Read randomness epoch |
| `R` [NFT.rarityOf](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `rarityOf(NFT_ID)` | Read rarity of |
| `R` [NFT.rarityRemaining](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `rarityRemaining(0)` | Read rarity remaining |
| `R` [NFT.remainingToReveal](CONTRACT_FUNCTIONS.md#zzznft) | None | `remainingToReveal()` | Read remaining to reveal |
| `R` [NFT.requestConfirmations](CONTRACT_FUNCTIONS.md#zzznft) | None | `requestConfirmations()` | Read request confirmations |
| `R` [NFT.requestEpochOf](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `requestEpochOf(NFT_ID)` | Read request epoch of |
| `R` [NFT.requestOf](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `requestOf(NFT_ID)` | Read request of |
| `R` [NFT.royaltyInfo](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256`<br>`salePrice: uint256` | `royaltyInfo(NFT_ID, 1000000000000000000)` | Read requested royalty payment |
| `R` [NFT.royaltyRewards](CONTRACT_FUNCTIONS.md#zzznft) | None | `royaltyRewards()` | Read royalty rewards |
| `R` [NFT.subscriptionId](CONTRACT_FUNCTIONS.md#zzznft) | None | `subscriptionId()` | Read subscription id |
| `R` [NFT.supportsInterface](CONTRACT_FUNCTIONS.md#zzznft) | `interfaceId: bytes4` | `supportsInterface(0x2a55205a)` | Read supports interface |
| `R` [NFT.symbol](CONTRACT_FUNCTIONS.md#zzznft) | None | `symbol()` | Read symbol |
| `R` [NFT.tokenAtOrdinal](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `tokenAtOrdinal(1)` | Read token at ordinal |
| `R` [NFT.tokenURI](CONTRACT_FUNCTIONS.md#zzznft) | `id: uint256` | `tokenURI(NFT_ID)` | Read token uri |
| `R` [NFT.traitsReady](CONTRACT_FUNCTIONS.md#zzznft) | `input0: uint256` | `traitsReady(NFT_ID)` | Read traits ready |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (8)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [NFT.canonicalRetire](CONTRACT_FUNCTIONS.md#zzznft) | None | `canonicalRetire()` | Retire source NFT authority |
| `M` [NFT.canonicalWriteArtwork](CONTRACT_FUNCTIONS.md#zzznft) | `rarity: uint8`<br>`item: uint256`<br>`value: uint16` | `canonicalWriteArtwork(0, ITEM, VALUE)` | Import authenticated artwork draw |
| `M` [NFT.canonicalWriteHeader](CONTRACT_FUNCTIONS.md#zzznft) | `count: uint256`<br>`next: uint256`<br>`remaining: uint256`<br>`quotas: uint16[3]`<br>`epoch: uint256` | `canonicalWriteHeader(1, NEXT, REMAINING, ["QUOTAS", "QUOTAS", "QUOTAS"], EPOCH)` | Import authenticated NFT header |
| `M` [NFT.canonicalWriteRecord](CONTRACT_FUNCTIONS.md#zzznft) | `row: uint256`<br>`value` [CanonicalNFTRecord](#input-canonicalnftrecord) | `canonicalWriteRecord(ROW, ["ID", "OWNER_ADDRESS", "RARITY", "COLOR", "PALETTE", "PATTERN", "REQUEST_ID", "REQUEST_EPOCH", "RARITY_WORD", "COLOR_WORD"])` | Import authenticated NFT record |
| `M` [NFT.mint](CONTRACT_FUNCTIONS.md#zzznft) | `to: address`<br>`id: uint256` | `mint(TO_ADDRESS, NFT_ID)` | Mint authenticated PoPL NFT |
| `M` [NFT.notifyContribution](CONTRACT_FUNCTIONS.md#zzznft) | `id: uint256` | `notifyContribution(NFT_ID)` | Register successful contribution rights |
| `M` [NFT.policyMetadataChanged](CONTRACT_FUNCTIONS.md#zzznft) | None | `policyMetadataChanged()` | Announce changed display policy |
| `C` [NFT.rawFulfillRandomWords](CONTRACT_FUNCTIONS.md#zzznft) | `requestId: uint256`<br>`words: uint256[]` | `rawFulfillRandomWords(REQUEST_ID, ["RARITY_WORD", "ARTWORK_WORD"])` | Record original provider randomness |

</details>

<a id="zzzactivationentry"></a>

#### ActivationEntry

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `H` [ActivationEntry.executeReviewed](CONTRACT_FUNCTIONS.md#zzzactivationentry) | `request` [ZZZActivationEntry.Request](#input-zzzactivationentry-request)<br>`maximumLossBps: uint16`<br>`expectedContributionPolicy: bytes32`<br>`value: wei` (separate) | `executeReviewed(["NFT_ID", "POOL_ID", "0x0000000000000000000000000000000000000000", "ETH_INPUT_WEI", "MINIMUM_LIQUIDITY", "UNIX_DEADLINE", false], 200, EXPECTED_CONTRIBUTION_POLICY); value=ETH_INPUT_WEI wei` | Activate or grow attached LP |

<details>
<summary>Read functions and constants (8)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [ActivationEntry.ENTRY_ROUTING_VERSION](CONTRACT_FUNCTIONS.md#zzzactivationentry) | None | `ENTRY_ROUTING_VERSION()` | Read entry routing version |
| `R` [ActivationEntry.REVIEW_POLICY_VERSION](CONTRACT_FUNCTIONS.md#zzzactivationentry) | None | `REVIEW_POLICY_VERSION()` | Read review policy version |
| `R` [ActivationEntry.access](CONTRACT_FUNCTIONS.md#zzzactivationentry) | None | `access()` | Read access |
| `R` [ActivationEntry.activationAssets](CONTRACT_FUNCTIONS.md#zzzactivationentry) | None | `activationAssets()` | Read activation assets |
| `R` [ActivationEntry.pricingContext](CONTRACT_FUNCTIONS.md#zzzactivationentry) | `id: uint256`<br>`pool: bytes32`<br>`packed: uint256`<br>`gross: uint256` | `pricingContext(NFT_ID, POOL_ID, PACKED, GROSS)` | Read pricing context |
| `R` [ActivationEntry.registry](CONTRACT_FUNCTIONS.md#zzzactivationentry) | None | `registry()` | Read registry |
| `R` [ActivationEntry.sourceValue](CONTRACT_FUNCTIONS.md#zzzactivationentry) | `poolId: bytes32`<br>`amount0: uint256`<br>`amount1: uint256` | `sourceValue(POOL_ID, AMOUNT0, AMOUNT1)` | Read source value |
| `R` [ActivationEntry.validateOwner](CONTRACT_FUNCTIONS.md#zzzactivationentry) | `id: uint256`<br>`vaultCallHash: bytes32` | `validateOwner(NFT_ID, VAULT_CALL_HASH)` | Read validate owner |

</details>

<a id="zzznftmetadata"></a>

#### NFTMetadata

<details>
<summary>Read functions and constants (4)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [NFTMetadata.access](CONTRACT_FUNCTIONS.md#zzznftmetadata) | None | `access()` | Read access |
| `R` [NFTMetadata.artworkItem](CONTRACT_FUNCTIONS.md#zzznftmetadata) | `rarity: uint8`<br>`item: uint256` | `artworkItem(RARITY, 0)` | Read artwork item |
| `R` [NFTMetadata.currentValue](CONTRACT_FUNCTIONS.md#zzznftmetadata) | `id: uint256` | `currentValue(NFT_ID)` | Read current value |
| `R` [NFTMetadata.render](CONTRACT_FUNCTIONS.md#zzznftmetadata) | `input` [NFTMetadataInput](#input-nftmetadatainput) | `render(["ID", "RARITY", "PALETTE", "PATTERN", "STAGE", "TRAITS_READY", "VALUATION_AVAILABLE", "VALUE_USD", "ROYALTY_WEIGHT", "IPFS_BASE_URI"])` | Read render |

</details>

<a id="calls-internals"></a>

### Bound modules, helpers and factories

<a id="zzzcontributionpricing"></a>

#### ContributionPricing

<details>
<summary>Read functions and constants (14)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [ContributionPricing.ENTRY_REVIEW_VERSION](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | None | `ENTRY_REVIEW_VERSION()` | Read entry review version |
| `R` [ContributionPricing.access](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | None | `access()` | Read access |
| `R` [ContributionPricing.active](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | None | `active()` | Read active |
| `R` [ContributionPricing.assertDeployed](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256`<br>`maxIdleBps: uint16` | `assertDeployed(BUCKET_ID, MAX_IDLE_BPS)` | Read assert deployed |
| `R` [ContributionPricing.assertPortfolioUtilization](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256`<br>`price0: uint256`<br>`price1: uint256`<br>`scale0: uint256`<br>`scale1: uint256` | `assertPortfolioUtilization(BUCKET_ID, PRICE0, PRICE1, SCALE0, SCALE1)` | Read assert portfolio utilization |
| `R` [ContributionPricing.checkMaintenance](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256`<br>`beforeValue: uint256`<br>`price0: uint256`<br>`price1: uint256`<br>`scale0: uint256`<br>`scale1: uint256`<br>`lossBps: uint16`<br>`maxIdleBps: uint16`<br>`expectedMaintenancePolicy: bytes32` | `checkMaintenance(BUCKET_ID, BEFORE_VALUE, PRICE0, PRICE1, SCALE0, SCALE1, LOSS_BPS, MAX_IDLE_BPS, EXPECTED_MAINTENANCE_POLICY)` | Read check maintenance |
| `R` [ContributionPricing.compoundReady](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256` | `compoundReady(BUCKET_ID)` | Read compound ready |
| `R` [ContributionPricing.entryIdleLimit](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256` | `entryIdleLimit(BUCKET_ID)` | Read entry idle limit |
| `R` [ContributionPricing.historicalValue](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256` | `historicalValue(BUCKET_ID)` | Read historical value |
| `R` [ContributionPricing.idleValue](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256` | `idleValue(BUCKET_ID)` | Read idle value |
| `R` [ContributionPricing.markMaintenance](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256` | `markMaintenance(BUCKET_ID)` | Read mark maintenance |
| `R` [ContributionPricing.nav](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256` | `nav(BUCKET_ID)` | Read nav |
| `R` [ContributionPricing.oracle](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | None | `oracle()` | Read oracle |
| `R` [ContributionPricing.valueBucket](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256`<br>`amount0: uint256`<br>`amount1: uint256` | `valueBucket(BUCKET_ID, AMOUNT0, AMOUNT1)` | Read value bucket |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (5)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [ContributionPricing.begin](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `nft: uint256`<br>`bucket: uint256`<br>`packed: uint256`<br>`inputUSD: uint256`<br>`limits: uint32` | `begin(NFT_ID, BUCKET_ID, PACKED, INPUT_USD, LIMITS)` | Begin contribution pricing |
| `M` [ContributionPricing.beginEntryReviewed](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `nft: uint256`<br>`pool: bytes32`<br>`source: address`<br>`amount: uint256`<br>`maximumLossBps: uint16`<br>`expectedContributionPolicy: bytes32` | `beginEntryReviewed(NFT_ID, POOL_ID, SOURCE_ADDRESS, AMOUNT, MAXIMUM_LOSS_BPS, EXPECTED_CONTRIBUTION_POLICY)` | Capture reviewed contribution context |
| `M` [ContributionPricing.contributionNav](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256` | `contributionNav(BUCKET_ID)` | Measure incumbent attributed NAV |
| `M` [ContributionPricing.endEntry](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | None | `endEntry()` | Close reviewed entry context |
| `M` [ContributionPricing.finish](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `bucket: uint256`<br>`inputUSD: uint256`<br>`supply: uint256`<br>`incumbentNAV: uint256`<br>`incumbentDeployed: uint256`<br>`deployed: uint256`<br>`idle: uint256`<br>`limits: uint32` | `finish(BUCKET_ID, INPUT_USD, SUPPLY, INCUMBENT_NAV, INCUMBENT_DEPLOYED, DEPLOYED, IDLE, LIMITS)` | Finish contribution pricing context |

</details>

<a id="zzzliquiditymanager"></a>

#### LiquidityManager

<details>
<summary>Read functions and constants (25)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [LiquidityManager.EMERGENCY_REBALANCE_VERSION](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `EMERGENCY_REBALANCE_VERSION()` | Read emergency rebalance version |
| `R` [LiquidityManager.EXECUTION_QUALITY_VERSION](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `EXECUTION_QUALITY_VERSION()` | Read execution quality version |
| `R` [LiquidityManager.LP_ROUTING_VERSION](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `LP_ROUTING_VERSION()` | Read lp routing version |
| `R` [LiquidityManager.PORTFOLIO_VERSION](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `PORTFOLIO_VERSION()` | Read portfolio version |
| `R` [LiquidityManager.RESIDUAL_EXIT_VERSION](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `RESIDUAL_EXIT_VERSION()` | Read residual exit version |
| `R` [LiquidityManager.access](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `access()` | Read access |
| `R` [LiquidityManager.activeSecondaryCount](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `activeSecondaryCount()` | Read active secondary count |
| `R` [LiquidityManager.amounts](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `id: uint256` | `amounts(LP_TOKEN_ID)` | Read amounts |
| `R` [LiquidityManager.balanceContext](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `targetPool: bytes32` | `balanceContext(POOL_ID)` | Read balance context |
| `R` [LiquidityManager.balancingRouter](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `balancingRouter()` | Read balancing router |
| `R` [LiquidityManager.executionConfig](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32`<br>`ops: bool` | `executionConfig(POOL_ID, OPS)` | Read execution config |
| `R` [LiquidityManager.executionHybridReplacement](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32` | `executionHybridReplacement(POOL_ID)` | Read execution hybrid replacement |
| `R` [LiquidityManager.executionOrdinaryReplacement](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `executionOrdinaryReplacement()` | Read execution ordinary replacement |
| `R` [LiquidityManager.executionPortfolioFingerprint](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `main: uint256` | `executionPortfolioFingerprint(LP_TOKEN_ID)` | Read execution portfolio fingerprint |
| `R` [LiquidityManager.executionSpot](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32` | `executionSpot(POOL_ID)` | Read execution spot |
| `R` [LiquidityManager.permit2](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `permit2()` | Read permit2 |
| `R` [LiquidityManager.poolManager](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `poolManager()` | Read pool manager |
| `R` [LiquidityManager.portfolioAmounts](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `main: uint256` | `portfolioAmounts(LP_TOKEN_ID)` | Read portfolio amounts |
| `R` [LiquidityManager.portfolioFingerprint](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `main: uint256` | `portfolioFingerprint(LP_TOKEN_ID)` | Read physical portfolio identity |
| `R` [LiquidityManager.positionManager](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `positionManager()` | Read position manager |
| `R` [LiquidityManager.positionOperator](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `positionOperator()` | Read position operator |
| `R` [LiquidityManager.secondaryId](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `main: uint256` | `secondaryId(LP_TOKEN_ID)` | Read secondary id |
| `R` [LiquidityManager.spot](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `poolId: bytes32` | `spot(POOL_ID)` | Read spot |
| `R` [LiquidityManager.stateView](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `stateView()` | Read state view |
| `R` [LiquidityManager.ticks](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `id: uint256` | `ticks(LP_TOKEN_ID)` | Read ticks |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (10)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [LiquidityManager.balance](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `targetPool: bytes32`<br>`existingLpId: uint256`<br>`amount0: uint256`<br>`amount1: uint256`<br>`deadline: uint256`<br>`value: wei` (separate) | `balance(POOL_ID, LP_TOKEN_ID, AMOUNT0, AMOUNT1, UNIX_DEADLINE); value=SETTLEMENT_WEI wei` | Balance attributed token inventory |
| `M` [LiquidityManager.beginEmergency](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `beginEmergency()` | Begin reviewed emergency context |
| `M` [LiquidityManager.close](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32`<br>`id: uint256`<br>`deadline: uint256` | `close(POOL_ID, LP_TOKEN_ID, UNIX_DEADLINE)` | Close registered main LP |
| `M` [LiquidityManager.closeSecondary](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32`<br>`main: uint256`<br>`deadline: uint256` | `closeSecondary(POOL_ID, LP_TOKEN_ID, UNIX_DEADLINE)` | Close registered residual LP |
| `M` [LiquidityManager.collect](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32`<br>`id: uint256`<br>`deadline: uint256` | `collect(POOL_ID, LP_TOKEN_ID, UNIX_DEADLINE)` | Harvest actual position fees |
| `M` [LiquidityManager.endEmergency](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | None | `endEmergency()` | Close emergency operation context |
| `M` [LiquidityManager.increase](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32`<br>`id: uint256`<br>`a0: uint256`<br>`a1: uint256`<br>`minL: uint128`<br>`deadline: uint256`<br>`value: wei` (separate) | `increase(POOL_ID, LP_TOKEN_ID, A0, A1, MIN_L, UNIX_DEADLINE); value=SETTLEMENT_WEI wei` | Grow existing attached LP |
| `M` [LiquidityManager.mint](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `pool: bytes32`<br>`lower: int24`<br>`upper: int24`<br>`a0: uint256`<br>`a1: uint256`<br>`minL: uint128`<br>`deadline: uint256`<br>`value: wei` (separate) | `mint(POOL_ID, LOWER_TICK, UPPER_TICK, A0, A1, MIN_L, UNIX_DEADLINE); value=SETTLEMENT_WEI wei` | Mint authenticated NFT position |
| `M` [LiquidityManager.swap](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `poolId: bytes32`<br>`zeroForOne: bool`<br>`amountIn: uint256`<br>`minimumOut: uint256`<br>`deadline: uint256`<br>`value: wei` (separate) | `swap(POOL_ID, ZERO_FOR_ONE, AMOUNT_IN, MINIMUM_OUT, UNIX_DEADLINE); value=SETTLEMENT_WEI wei` | Execute authenticated bounded swap |
| `C` [LiquidityManager.unlockCallback](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `data: bytes` | `unlockCallback(0x)` | Settle authenticated core callback |

</details>

<a id="zzzlppositionexecutor"></a>

#### LPPositionExecutor

<details>
<summary>Read functions and constants (15)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [LPPositionExecutor.LP_POSITION_EXECUTOR_VERSION](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `LP_POSITION_EXECUTOR_VERSION()` | Read lp position executor version |
| `R` [LPPositionExecutor.RESIDUAL_EXIT_VERSION](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `RESIDUAL_EXIT_VERSION()` | Read residual exit version |
| `R` [LPPositionExecutor.access](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `access()` | Read access |
| `R` [LPPositionExecutor.activeSecondaryCount](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `activeSecondaryCount()` | Read active secondary count |
| `R` [LPPositionExecutor.amounts](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `id: uint256` | `amounts(LP_TOKEN_ID)` | Read amounts |
| `R` [LPPositionExecutor.balancingRouter](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `balancingRouter()` | Read balancing router |
| `R` [LPPositionExecutor.liquidityManager](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `liquidityManager()` | Read liquidity manager |
| `R` [LPPositionExecutor.permit2](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `permit2()` | Read permit2 |
| `R` [LPPositionExecutor.poolManager](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `poolManager()` | Read pool manager |
| `R` [LPPositionExecutor.portfolioAmounts](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `mainId: uint256` | `portfolioAmounts(LP_TOKEN_ID)` | Read portfolio amounts |
| `R` [LPPositionExecutor.portfolioFingerprint](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `mainId: uint256` | `portfolioFingerprint(LP_TOKEN_ID)` | Read physical portfolio identity |
| `R` [LPPositionExecutor.positionManager](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `positionManager()` | Read position manager |
| `R` [LPPositionExecutor.secondaryId](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `input0: uint256` | `secondaryId(LP_TOKEN_ID)` | Read secondary id |
| `R` [LPPositionExecutor.stateView](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | None | `stateView()` | Read state view |
| `R` [LPPositionExecutor.ticks](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `id: uint256` | `ticks(LP_TOKEN_ID)` | Read ticks |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (5)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [LPPositionExecutor.close](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `poolId: bytes32`<br>`id: uint256`<br>`deadline: uint256` | `close(POOL_ID, LP_TOKEN_ID, UNIX_DEADLINE)` | Close registered main LP |
| `M` [LPPositionExecutor.closeSecondary](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `poolId: bytes32`<br>`main: uint256`<br>`deadline: uint256` | `closeSecondary(POOL_ID, LP_TOKEN_ID, UNIX_DEADLINE)` | Close registered residual LP |
| `M` [LPPositionExecutor.collect](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `poolId: bytes32`<br>`id: uint256`<br>`deadline: uint256` | `collect(POOL_ID, LP_TOKEN_ID, UNIX_DEADLINE)` | Harvest actual position fees |
| `M` [LPPositionExecutor.increase](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `poolId: bytes32`<br>`id: uint256`<br>`amount0: uint256`<br>`amount1: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256`<br>`value: wei` (separate) | `increase(POOL_ID, LP_TOKEN_ID, AMOUNT0, AMOUNT1, MINIMUM_LIQUIDITY, UNIX_DEADLINE); value=SETTLEMENT_WEI wei` | Grow existing attached LP |
| `M` [LPPositionExecutor.mint](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `poolId: bytes32`<br>`lower: int24`<br>`upper: int24`<br>`amount0: uint256`<br>`amount1: uint256`<br>`minimumLiquidity: uint128`<br>`deadline: uint256`<br>`value: wei` (separate) | `mint(POOL_ID, LOWER_TICK, UPPER_TICK, AMOUNT0, AMOUNT1, MINIMUM_LIQUIDITY, UNIX_DEADLINE); value=SETTLEMENT_WEI wei` | Mint authenticated NFT position |

</details>

<a id="zzzlpbalancemath"></a>

#### LPBalanceMath

<details>
<summary>Read functions and constants (7)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [LPBalanceMath.LP_BALANCE_MATH_VERSION](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | None | `LP_BALANCE_MATH_VERSION()` | Read lp balance math version |
| `R` [LPBalanceMath.balancer](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | None | `balancer()` | Read balancer |
| `R` [LPBalanceMath.deploymentAmounts](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | `current: uint160`<br>`lower: int24`<br>`upper: int24`<br>`amount0: uint256`<br>`amount1: uint256` | `deploymentAmounts(CURRENT, LOWER_TICK, UPPER_TICK, AMOUNT0, AMOUNT1)` | Read deployment amounts |
| `R` [LPBalanceMath.deploymentDebts](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | `current: uint160`<br>`lower: int24`<br>`upper: int24`<br>`liquidity: uint128` | `deploymentDebts(CURRENT, LOWER_TICK, UPPER_TICK, LIQUIDITY)` | Read deployment debts |
| `R` [LPBalanceMath.evaluate](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | `x` [ZZZLPBalanceMath.Context](#input-zzzlpbalancemath-context)<br>`price: uint160`<br>`a0: uint256`<br>`a1: uint256` | `evaluate(["TARGET", "SPOT", "LOWER", "UPPER", "AMOUNT0", "AMOUNT1", ["LOWER0", "UPPER0", "LOWER1", "UPPER1", "SCALE1", "REFERENCE_X96", "EXTRA_LOSS"], "MAIN_FLOOR", ["MARKS", "MARKS", "MARKS", "MARKS"]], PRICE, A0, A1)` | Read evaluate |
| `R` [LPBalanceMath.principalAmounts](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | `positionManager: address`<br>`state: address`<br>`id: uint256` | `principalAmounts(POSITION_MANAGER_ADDRESS, STATE_ADDRESS, LP_TOKEN_ID)` | Read principal amounts |
| `R` [LPBalanceMath.seed](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | `x` [ZZZLPBalanceMath.Context](#input-zzzlpbalancemath-context)<br>`direction: bool`<br>`fee: uint256` | `seed(["TARGET", "SPOT", "LOWER", "UPPER", "AMOUNT0", "AMOUNT1", ["LOWER0", "UPPER0", "LOWER1", "UPPER1", "SCALE1", "REFERENCE_X96", "EXTRA_LOSS"], "MAIN_FLOOR", ["MARKS", "MARKS", "MARKS", "MARKS"]], DIRECTION, FEE)` | Read seed |

</details>

<a id="zzzv4routeexecutor"></a>

#### V4RouteExecutor

<details>
<summary>Read functions and constants (7)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [V4RouteExecutor.NATIVE_ASSET_CODE_HASH](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | None | `NATIVE_ASSET_CODE_HASH()` | Read native asset code hash |
| `R` [V4RouteExecutor.ROUTE_DOMAIN](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | None | `ROUTE_DOMAIN()` | Read route domain |
| `R` [V4RouteExecutor.parent](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | None | `parent()` | Read parent |
| `R` [V4RouteExecutor.route](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `id: bytes32` | `route(REVIEWED_ROUTE_ID)` | Read route |
| `R` [V4RouteExecutor.routeEnabled](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `input0: bytes32` | `routeEnabled(REVIEWED_ROUTE_ID)` | Read route enabled |
| `R` [V4RouteExecutor.routeExists](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `input0: bytes32` | `routeExists(REVIEWED_ROUTE_ID)` | Read route exists |
| `R` [V4RouteExecutor.validate](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `id: bytes32` | `validate(REVIEWED_ROUTE_ID)` | Read validate |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (4)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [V4RouteExecutor.addRoute](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `policy` [ZZZV4RouteExecutor.Policy](#input-zzzv4routeexecutor-policy) | `addRoute(["SOURCE_ADDRESS", "OUTPUT_ADDRESS", ["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"], "POOL_MANAGER_ADDRESS", "STATE_VIEW_ADDRESS", "SOURCE_CODE_HASH", "OUTPUT_CODE_HASH", "POOL_MANAGER_CODE_HASH", "STATE_VIEW_CODE_HASH", "REVIEW_HASH"])` | Admit reviewed swap route |
| `M` [V4RouteExecutor.execute](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `id: bytes32`<br>`amountIn: uint256`<br>`minimumOut: uint256`<br>`deadline: uint256`<br>`value: wei` (separate) | `execute(REVIEWED_ROUTE_ID, AMOUNT_IN, MINIMUM_OUT, UNIX_DEADLINE); value=SETTLEMENT_WEI wei` | Execute authenticated conversion route |
| `M` [V4RouteExecutor.setRouteEnabled](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `id: bytes32`<br>`enabled: bool` | `setRouteEnabled(REVIEWED_ROUTE_ID, false)` | Enable or disable reviewed route |
| `C` [V4RouteExecutor.unlockCallback](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `payload: bytes` | `unlockCallback(PAYLOAD)` | Settle authenticated core callback |

</details>

<a id="zzzcustodyvalidation"></a>

#### CustodyValidation

<details>
<summary>Read functions and constants (6)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [CustodyValidation.access](CONTRACT_FUNCTIONS.md#zzzcustodyvalidation) | None | `access()` | Read access |
| `R` [CustodyValidation.emergencyCustodyHash](CONTRACT_FUNCTIONS.md#zzzcustodyvalidation) | `bucket: uint256` | `emergencyCustodyHash(BUCKET_ID)` | Read emergency custody identity |
| `R` [CustodyValidation.emergencyFingerprint](CONTRACT_FUNCTIONS.md#zzzcustodyvalidation) | `request` [EmergencyRebalance](#input-emergencyrebalance) | `emergencyFingerprint(["BUCKET_ID", "CUSTODY_HASH", "31", "LOWER_TICK", "UPPER_TICK", "SWAP_POOL", "ZERO_FOR_ONE", "AMOUNT_IN", "MINIMUM_OUT", "MINIMUM_LIQUIDITY", "UNIX_DEADLINE", "REVIEW_HASH"])` | Read emergency fingerprint |
| `R` [CustodyValidation.migration](CONTRACT_FUNCTIONS.md#zzzcustodyvalidation) | None | `migration()` | Read migration |
| `R` [CustodyValidation.residualMainFingerprint](CONTRACT_FUNCTIONS.md#zzzcustodyvalidation) | `bucket: uint256` | `residualMainFingerprint(BUCKET_ID)` | Read residual main fingerprint |
| `R` [CustodyValidation.validateParking](CONTRACT_FUNCTIONS.md#zzzcustodyvalidation) | `encoded: bytes` | `validateParking(ENCODED)` | Read validate parking |

</details>

<a id="zzzfeescanonical"></a>

#### FeesCanonical

<details>
<summary>Read functions and constants (7)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [FeesCanonical.access](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `access()` | Read access |
| `R` [FeesCanonical.canonicalAssetCount](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `canonicalAssetCount()` | Read canonical asset count |
| `R` [FeesCanonical.canonicalBacking](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `index: uint256` | `canonicalBacking(0)` | Read canonical backing |
| `R` [FeesCanonical.canonicalCount](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `canonicalCount()` | Read canonical count |
| `R` [FeesCanonical.canonicalExport](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `row: uint256` | `canonicalExport(0)` | Read canonical export |
| `R` [FeesCanonical.canonicalValidate](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `canonicalValidate()` | Validate imported classified backing |
| `R` [FeesCanonical.fees](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `fees()` | Read fees |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (7)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [FeesCanonical.canonicalAccept](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `index: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalAccept(0, TARGET_ADDRESS); value=0 wei` | Accept authenticated classified backing |
| `M` [FeesCanonical.canonicalActivate](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `canonicalActivate()` | Activate imported ledger state |
| `M` [FeesCanonical.canonicalCapture](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `canonicalCapture()` | Capture classified ledger backing |
| `M` [FeesCanonical.canonicalImport](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `row: uint256`<br>`record: bytes` | `canonicalImport(0, RECORD)` | Import authenticated accounting row |
| `M` [FeesCanonical.canonicalRelease](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `index: uint256`<br>`destination: address` | `canonicalRelease(0, DESTINATION_ADDRESS)` | Release authenticated classified backing |
| `M` [FeesCanonical.canonicalRestore](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `index: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalRestore(0, TARGET_ADDRESS); value=0 wei` | Restore captured source backing |
| `M` [FeesCanonical.canonicalSettle](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | None | `canonicalSettle()` | Settle captured reward indexes |

</details>

<a id="zzznftcanonical"></a>

#### NFTCanonical

<details>
<summary>Read functions and constants (6)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [NFTCanonical.access](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `access()` | Read access |
| `R` [NFTCanonical.canonicalAssetCount](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `canonicalAssetCount()` | Read canonical asset count |
| `R` [NFTCanonical.canonicalCount](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `canonicalCount()` | Read canonical count |
| `R` [NFTCanonical.canonicalExport](CONTRACT_FUNCTIONS.md#zzznftcanonical) | `row: uint256` | `canonicalExport(0)` | Read canonical export |
| `R` [NFTCanonical.canonicalValidate](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `canonicalValidate()` | Validate imported classified backing |
| `R` [NFTCanonical.nft](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `nft()` | Read nft |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (4)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [NFTCanonical.canonicalActivate](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `canonicalActivate()` | Activate imported ledger state |
| `M` [NFTCanonical.canonicalCapture](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `canonicalCapture()` | Capture classified ledger backing |
| `M` [NFTCanonical.canonicalImport](CONTRACT_FUNCTIONS.md#zzznftcanonical) | `row: uint256`<br>`record: bytes` | `canonicalImport(0, RECORD)` | Import authenticated accounting row |
| `M` [NFTCanonical.canonicalSettle](CONTRACT_FUNCTIONS.md#zzznftcanonical) | None | `canonicalSettle()` | Settle captured reward indexes |

</details>

<a id="zzzvaultcanonical"></a>

#### VaultCanonical

<details>
<summary>Read functions and constants (20)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [VaultCanonical.access](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `access()` | Read access |
| `R` [VaultCanonical.aliasBucket](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `input0: bytes32` | `aliasBucket(POOL_ID)` | Read alias bucket |
| `R` [VaultCanonical.aliases](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `input0: uint256` | `aliases(0)` | Read aliases |
| `R` [VaultCanonical.bucketIdentity](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `pool: bytes32` | `bucketIdentity(POOL_ID)` | Read bucket identity |
| `R` [VaultCanonical.canonicalAssetCount](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `canonicalAssetCount()` | Read canonical asset count |
| `R` [VaultCanonical.canonicalBacking](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `index: uint256` | `canonicalBacking(0)` | Read canonical backing |
| `R` [VaultCanonical.canonicalCount](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `canonicalCount()` | Read canonical count |
| `R` [VaultCanonical.canonicalExport](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `row: uint256` | `canonicalExport(0)` | Read canonical export |
| `R` [VaultCanonical.canonicalValidate](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `canonicalValidate()` | Validate imported classified backing |
| `R` [VaultCanonical.mintIdentity](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `ordinal: uint256` | `mintIdentity(1)` | Read mint identity |
| `R` [VaultCanonical.mintPolicyFingerprint](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `mintPolicyFingerprint()` | Read current mint policy |
| `R` [VaultCanonical.mintPrice](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `mintPrice()` | Read mint price |
| `R` [VaultCanonical.mintProceedsRecipient](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `mintProceedsRecipient()` | Read mint proceeds recipient |
| `R` [VaultCanonical.originChain](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `originChain()` | Read origin chain |
| `R` [VaultCanonical.originVault](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `originVault()` | Read origin vault |
| `R` [VaultCanonical.validateContribution](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `id: uint256`<br>`bucket: uint256`<br>`inputUSD: uint256`<br>`inputTotal: uint256`<br>`minimumLiquidity: uint128`<br>`activation: bool` | `validateContribution(NFT_ID, BUCKET_ID, INPUT_USD, INPUT_TOTAL, MINIMUM_LIQUIDITY, ACTIVATION)` | Read validate contribution |
| `R` [VaultCanonical.validateHolderExit](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `id: uint256`<br>`migrationCaller: address` | `validateHolderExit(BUCKET_ID, MIGRATION_CALLER_ADDRESS)` | Read validate holder exit |
| `R` [VaultCanonical.validateMint](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `value: uint256`<br>`ordinal: uint256`<br>`expectedPolicy: bytes32` | `validateMint(VALUE, 1, EXPECTED_POLICY)` | Read validate mint |
| `R` [VaultCanonical.validateOwner](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `id: uint256`<br>`caller: address`<br>`minted: bool`<br>`activation: bool` | `validateOwner(NFT_ID, CALLER_ADDRESS, MINTED, ACTIVATION)` | Read validate owner |
| `R` [VaultCanonical.vault](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `vault()` | Read vault |

</details>

<details>
<summary>Contract-only calls: use the parent workflow (8)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [VaultCanonical.canonicalAccept](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `index: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalAccept(0, TARGET_ADDRESS); value=0 wei` | Accept authenticated classified backing |
| `M` [VaultCanonical.canonicalActivate](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `canonicalActivate()` | Activate imported ledger state |
| `M` [VaultCanonical.canonicalCapture](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `canonicalCapture()` | Capture classified ledger backing |
| `M` [VaultCanonical.canonicalImport](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `row: uint256`<br>`record: bytes` | `canonicalImport(0, RECORD)` | Import authenticated accounting row |
| `M` [VaultCanonical.canonicalRelease](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `index: uint256`<br>`destination: address` | `canonicalRelease(0, DESTINATION_ADDRESS)` | Release authenticated classified backing |
| `M` [VaultCanonical.canonicalRestore](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `index: uint256`<br>`input1: address`<br>`value: wei` (separate) | `canonicalRestore(0, TARGET_ADDRESS); value=0 wei` | Restore captured source backing |
| `M` [VaultCanonical.canonicalSettle](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | None | `canonicalSettle()` | Settle captured reward indexes |
| `M` [VaultCanonical.registerAlias](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `pool: bytes32`<br>`bucket: uint256` | `registerAlias(POOL_ID, BUCKET_ID)` | Register authenticated local alias |

</details>

<a id="zzzpythpricefeed"></a>

#### PythPriceFeed

<details>
<summary>Read functions and constants (11)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [PythPriceFeed.MAX_CONFIDENCE_BPS](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `MAX_CONFIDENCE_BPS()` | Read max confidence bps |
| `R` [PythPriceFeed.SOURCE_CALL_GAS](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `SOURCE_CALL_GAS()` | Read source call gas |
| `R` [PythPriceFeed.core](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `core()` | Read core |
| `R` [PythPriceFeed.decimals](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `decimals()` | Read decimals |
| `R` [PythPriceFeed.expectedCoreCodeHash](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `expectedCoreCodeHash()` | Read expected core code hash |
| `R` [PythPriceFeed.expectedExponent](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `expectedExponent()` | Read expected exponent |
| `R` [PythPriceFeed.feedId](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `feedId()` | Read feed id |
| `R` [PythPriceFeed.latestRoundData](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `latestRoundData()` | Read latest round data |
| `R` [PythPriceFeed.maxAge](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `maxAge()` | Read max age |
| `R` [PythPriceFeed.maxConfidenceBps](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `maxConfidenceBps()` | Read max confidence bps |
| `R` [PythPriceFeed.reviewHash](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | None | `reviewHash()` | Read review hash |

</details>

<a id="zzzactivationassetsfactory"></a>

#### ActivationAssetsFactory

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `P` [ActivationAssetsFactory.create](CONTRACT_FUNCTIONS.md#zzzactivationassetsfactory) | None | `create()` | Create caller-bound helper |

<details>
<summary>Read functions and constants (2)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [ActivationAssetsFactory.access](CONTRACT_FUNCTIONS.md#zzzactivationassetsfactory) | None | `access()` | Read access |
| `R` [ActivationAssetsFactory.assetsOf](CONTRACT_FUNCTIONS.md#zzzactivationassetsfactory) | `input0: address` | `assetsOf(TARGET_ADDRESS)` | Read assets of |

</details>

<a id="zzzroyaltyfactory"></a>

#### RoyaltyFactory

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `P` [RoyaltyFactory.create](CONTRACT_FUNCTIONS.md#zzzroyaltyfactory) | None | `create()` | Create caller-bound helper |

<details>
<summary>Read functions and constants (1)</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `R` [RoyaltyFactory.controller](CONTRACT_FUNCTIONS.md#zzzroyaltyfactory) | None | `controller()` | Read controller |

</details>

### Expanded tuple examples

Fields are expanded recursively in exact ABI order. Uppercase symbols remain required snapshot/review inputs. These examples prove neither venue feasibility nor historical entitlement. Parameter semantics and bounds remain in the linked function/procedure.

<details>
<summary>CanonicalNFTRecord</summary>

<a id="input-canonicalnftrecord"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `value` | `(uint256,address,uint8,uint8,uint8,uint8,uint256,uint256,uint256,uint256)` | `["ID", "OWNER_ADDRESS", "RARITY", "COLOR", "PALETTE", "PATTERN", "REQUEST_ID", "REQUEST_EPOCH", "RARITY_WORD", "COLOR_WORD"]` |
| `value.id` | `uint256` | `ID` |
| `value.owner` | `address` | `OWNER_ADDRESS` |
| `value.rarity` | `uint8` | `RARITY` |
| `value.color` | `uint8` | `COLOR` |
| `value.palette` | `uint8` | `PALETTE` |
| `value.pattern` | `uint8` | `PATTERN` |
| `value.requestId` | `uint256` | `REQUEST_ID` |
| `value.requestEpoch` | `uint256` | `REQUEST_EPOCH` |
| `value.rarityWord` | `uint256` | `RARITY_WORD` |
| `value.colorWord` | `uint256` | `COLOR_WORD` |

</details>

<details>
<summary>EmergencyRebalance</summary>

<a id="input-emergencyrebalance"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `request` | `(uint256,bytes32,uint8,int24,int24,bytes32,bool,uint128,uint128,uint128,uint256,bytes32)` | `["BUCKET_ID", "CUSTODY_HASH", "31", "LOWER_TICK", "UPPER_TICK", "SWAP_POOL", "ZERO_FOR_ONE", "AMOUNT_IN", "MINIMUM_OUT", "MINIMUM_LIQUIDITY", "UNIX_DEADLINE", "REVIEW_HASH"]` |
| `request.bucket` | `uint256` | `BUCKET_ID` |
| `request.custodyHash` | `bytes32` | `CUSTODY_HASH` |
| `request.checks` | `uint8` | `31` |
| `request.lower` | `int24` | `LOWER_TICK` |
| `request.upper` | `int24` | `UPPER_TICK` |
| `request.swapPool` | `bytes32` | `SWAP_POOL` |
| `request.zeroForOne` | `bool` | `ZERO_FOR_ONE` |
| `request.amountIn` | `uint128` | `AMOUNT_IN` |
| `request.minimumOut` | `uint128` | `MINIMUM_OUT` |
| `request.minimumLiquidity` | `uint128` | `MINIMUM_LIQUIDITY` |
| `request.deadline` | `uint256` | `UNIX_DEADLINE` |
| `request.reviewHash` | `bytes32` | `REVIEW_HASH` |

</details>

<details>
<summary>NFTMetadataInput</summary>

<a id="input-nftmetadatainput"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `input` | `(uint256,uint8,uint8,uint8,uint8,bool,bool,uint256,uint8,string)` | `["ID", "RARITY", "PALETTE", "PATTERN", "STAGE", "TRAITS_READY", "VALUATION_AVAILABLE", "VALUE_USD", "ROYALTY_WEIGHT", "IPFS_BASE_URI"]` |
| `input.id` | `uint256` | `ID` |
| `input.rarity` | `uint8` | `RARITY` |
| `input.palette` | `uint8` | `PALETTE` |
| `input.pattern` | `uint8` | `PATTERN` |
| `input.stage` | `uint8` | `STAGE` |
| `input.traitsReady` | `bool` | `TRAITS_READY` |
| `input.valuationAvailable` | `bool` | `VALUATION_AVAILABLE` |
| `input.valueUSD` | `uint256` | `VALUE_USD` |
| `input.royaltyWeight` | `uint8` | `ROYALTY_WEIGHT` |
| `input.baseURI` | `string` | `IPFS_BASE_URI` |

</details>

<details>
<summary>PoolConfig</summary>

<a id="input-poolconfig"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `config` | `((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256)` | `[["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"], "DEPOSITS_ENABLED", "OPERATIONS_ENABLED", "RANGE_BPS", "TRIGGER_BPS", "MAX_SPOT_DEVIATION_BPS", "MAX_SLIPPAGE_BPS", "MIN_REBALANCE_INTERVAL", "MIN_DEPOSIT_USD", "MAX_POSITION_USD"]` |
| `config.key` | `(address,address,uint24,int24,address)` | `["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"]` |
| `config.key.currency0` | `address` | `0x0000000000000000000000000000000000000000` |
| `config.key.currency1` | `address` | `ZZZ_ADDRESS` |
| `config.key.fee` | `uint24` | `FEE` |
| `config.key.tickSpacing` | `int24` | `TICK_SPACING` |
| `config.key.hooks` | `address` | `0x0000000000000000000000000000000000000000` |
| `config.depositsEnabled` | `bool` | `DEPOSITS_ENABLED` |
| `config.operationsEnabled` | `bool` | `OPERATIONS_ENABLED` |
| `config.rangeBps` | `uint16` | `RANGE_BPS` |
| `config.triggerBps` | `uint16` | `TRIGGER_BPS` |
| `config.maxSpotDeviationBps` | `uint16` | `MAX_SPOT_DEVIATION_BPS` |
| `config.maxSlippageBps` | `uint16` | `MAX_SLIPPAGE_BPS` |
| `config.minRebalanceInterval` | `uint32` | `MIN_REBALANCE_INTERVAL` |
| `config.minDepositUSD` | `uint256` | `MIN_DEPOSIT_USD` |
| `config.maxPositionUSD` | `uint256` | `MAX_POSITION_USD` |

</details>

<details>
<summary>PoolKey</summary>

<a id="input-poolkey"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `key` | `(address,address,uint24,int24,address)` | `["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"]` |
| `key.currency0` | `address` | `0x0000000000000000000000000000000000000000` |
| `key.currency1` | `address` | `ZZZ_ADDRESS` |
| `key.fee` | `uint24` | `FEE` |
| `key.tickSpacing` | `int24` | `TICK_SPACING` |
| `key.hooks` | `address` | `0x0000000000000000000000000000000000000000` |

</details>

<details>
<summary>ZZZAccessController.PreparationNotice</summary>

<a id="input-zzzaccesscontroller-preparationnotice"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `notice` | `(uint256,address,bytes32,bytes32)` | `["DESTINATION_CHAIN", "SUCCESSOR_CONTROLLER_ADDRESS", "DEPLOYMENT_COMMITMENT", "REVIEW_HASH"]` |
| `notice.destinationChain` | `uint256` | `DESTINATION_CHAIN` |
| `notice.successorController` | `address` | `SUCCESSOR_CONTROLLER_ADDRESS` |
| `notice.deploymentCommitment` | `bytes32` | `DEPLOYMENT_COMMITMENT` |
| `notice.reviewHash` | `bytes32` | `REVIEW_HASH` |

</details>

<details>
<summary>ZZZActivationEntry.Request</summary>

<a id="input-zzzactivationentry-request"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `request` | `(uint256,bytes32,address,uint256,uint128,uint256,bool)` | `["NFT_ID", "POOL_ID", "0x0000000000000000000000000000000000000000", "ETH_INPUT_WEI", "MINIMUM_LIQUIDITY", "UNIX_DEADLINE", false]` |
| `request.nftId` | `uint256` | `NFT_ID` |
| `request.poolId` | `bytes32` | `POOL_ID` |
| `request.sourceAsset` | `address` | `0x0000000000000000000000000000000000000000` |
| `request.amountIn` | `uint256` | `ETH_INPUT_WEI` |
| `request.minimumLiquidity` | `uint128` | `MINIMUM_LIQUIDITY` |
| `request.deadline` | `uint256` | `UNIX_DEADLINE` |
| `request.increase` | `bool` | `false` |

</details>

<details>
<summary>ZZZClaimRouter.Claim[]</summary>

<a id="input-zzzclaimrouter-claim-array"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `claims` | `(uint256,address,bool)[]` | `[["NFT_ID", "0x0000000000000000000000000000000000000000", false], ["NFT_ID", "0x0000000000000000000000000000000000000000", true]]` |
| `claims[0]` | `(uint256,address,bool)` | `["NFT_ID", "0x0000000000000000000000000000000000000000", false]` |
| `claims[0].nftId` | `uint256` | `NFT_ID` |
| `claims[0].asset` | `address` | `0x0000000000000000000000000000000000000000` |
| `claims[0].royalty` | `bool` | `false` |

</details>

<details>
<summary>ZZZLPBalanceMath.Context</summary>

<a id="input-zzzlpbalancemath-context"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `x` | `(bytes32,uint160,uint160,uint160,uint256,uint256,(uint256,uint256,uint256,uint256,uint256,uint160,uint16),uint16,uint256[4])` | `["TARGET", "SPOT", "LOWER", "UPPER", "AMOUNT0", "AMOUNT1", ["LOWER0", "UPPER0", "LOWER1", "UPPER1", "SCALE1", "REFERENCE_X96", "EXTRA_LOSS"], "MAIN_FLOOR", ["MARKS", "MARKS", "MARKS", "MARKS"]]` |
| `x.target` | `bytes32` | `TARGET` |
| `x.spot` | `uint160` | `SPOT` |
| `x.lower` | `uint160` | `LOWER` |
| `x.upper` | `uint160` | `UPPER` |
| `x.amount0` | `uint256` | `AMOUNT0` |
| `x.amount1` | `uint256` | `AMOUNT1` |
| `x.prices` | `(uint256,uint256,uint256,uint256,uint256,uint160,uint16)` | `["LOWER0", "UPPER0", "LOWER1", "UPPER1", "SCALE1", "REFERENCE_X96", "EXTRA_LOSS"]` |
| `x.prices.lower0` | `uint256` | `LOWER0` |
| `x.prices.upper0` | `uint256` | `UPPER0` |
| `x.prices.lower1` | `uint256` | `LOWER1` |
| `x.prices.upper1` | `uint256` | `UPPER1` |
| `x.prices.scale1` | `uint256` | `SCALE1` |
| `x.prices.referenceX96` | `uint160` | `REFERENCE_X96` |
| `x.prices.extraLoss` | `uint16` | `EXTRA_LOSS` |
| `x.mainFloor` | `uint16` | `MAIN_FLOOR` |
| `x.marks` | `uint256[4]` | `["MARKS", "MARKS", "MARKS", "MARKS"]` |
| `x.marks[0]` | `uint256` | `MARKS` |

</details>

<details>
<summary>ZZZMigration.ParkingRequest</summary>

<a id="input-zzzmigration-parkingrequest"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `r` | `(uint256,bytes32,uint256,uint256,uint256,uint64,uint64,address,address,uint128,uint128,uint256,bytes32,bytes32)` | `["BUCKET_ID", "POOL_ID", "LP_TOKEN_ID", "TOTAL_SHARES", "DEPOSIT_USD", "CUSTODY_EPOCH", "CURRENT_NONCE", "0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "MINIMUM0", "MINIMUM1", "UNIX_DEADLINE", "REVIEW_HASH", "PORTFOLIO_HASH"]` |
| `r.bucketId` | `uint256` | `BUCKET_ID` |
| `r.poolId` | `bytes32` | `POOL_ID` |
| `r.lpTokenId` | `uint256` | `LP_TOKEN_ID` |
| `r.totalShares` | `uint256` | `TOTAL_SHARES` |
| `r.depositUSD` | `uint256` | `DEPOSIT_USD` |
| `r.custodyEpoch` | `uint64` | `CUSTODY_EPOCH` |
| `r.nonce` | `uint64` | `CURRENT_NONCE` |
| `r.token0` | `address` | `0x0000000000000000000000000000000000000000` |
| `r.token1` | `address` | `ZZZ_ADDRESS` |
| `r.minimum0` | `uint128` | `MINIMUM0` |
| `r.minimum1` | `uint128` | `MINIMUM1` |
| `r.deadline` | `uint256` | `UNIX_DEADLINE` |
| `r.reviewHash` | `bytes32` | `REVIEW_HASH` |
| `r.portfolioHash` | `bytes32` | `PORTFOLIO_HASH` |

</details>

<details>
<summary>ZZZOracle.SourcePolicy</summary>

<a id="input-zzzoracle-sourcepolicy"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `primary` | `(address,bytes32,bytes32,uint32,uint8)` | `["PRIMARY_FEED_ADDRESS", "PRIMARY_CODE_HASH", "PRIMARY_INDEPENDENCE_ID", "PRIMARY_MAX_AGE", "PRIMARY_FEED_DECIMALS"]` |
| `primary.source` | `address` | `PRIMARY_FEED_ADDRESS` |
| `primary.expectedCodeHash` | `bytes32` | `PRIMARY_CODE_HASH` |
| `primary.independenceId` | `bytes32` | `PRIMARY_INDEPENDENCE_ID` |
| `primary.maxAge` | `uint32` | `PRIMARY_MAX_AGE` |
| `primary.feedDecimals` | `uint8` | `PRIMARY_FEED_DECIMALS` |

</details>

<details>
<summary>ZZZRewardConverter.RoutePolicy</summary>

<a id="input-zzzrewardconverter-routepolicy"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `policy` | `(address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32)` | `["SOURCE_ADDRESS", "ROUTER_ADDRESS", "FACTORY_ADDRESS", "POOL_ADDRESS", "FEE", "SOURCE_CODE_HASH", "ROUTER_CODE_HASH", "FACTORY_CODE_HASH", "POOL_CODE_HASH", "REVIEW_HASH"]` |
| `policy.source` | `address` | `SOURCE_ADDRESS` |
| `policy.router` | `address` | `ROUTER_ADDRESS` |
| `policy.factory` | `address` | `FACTORY_ADDRESS` |
| `policy.pool` | `address` | `POOL_ADDRESS` |
| `policy.fee` | `uint24` | `FEE` |
| `policy.sourceCodeHash` | `bytes32` | `SOURCE_CODE_HASH` |
| `policy.routerCodeHash` | `bytes32` | `ROUTER_CODE_HASH` |
| `policy.factoryCodeHash` | `bytes32` | `FACTORY_CODE_HASH` |
| `policy.poolCodeHash` | `bytes32` | `POOL_CODE_HASH` |
| `policy.reviewHash` | `bytes32` | `REVIEW_HASH` |

</details>

<details>
<summary>ZZZRewardConverter.WrapperPolicy</summary>

<a id="input-zzzrewardconverter-wrapperpolicy"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `policy` | `(bytes32,address,address,address,bytes32,bytes32,bytes32)` | `["CODE_HASH", "ADMIN_ADDRESS", "IMPLEMENTATION_ADDRESS", "ADMIN_OWNER_ADDRESS", "ADMIN_CODE_HASH", "IMPLEMENTATION_CODE_HASH", "REVIEW_HASH"]` |
| `policy.codeHash` | `bytes32` | `CODE_HASH` |
| `policy.admin` | `address` | `ADMIN_ADDRESS` |
| `policy.implementation` | `address` | `IMPLEMENTATION_ADDRESS` |
| `policy.adminOwner` | `address` | `ADMIN_OWNER_ADDRESS` |
| `policy.adminCodeHash` | `bytes32` | `ADMIN_CODE_HASH` |
| `policy.implementationCodeHash` | `bytes32` | `IMPLEMENTATION_CODE_HASH` |
| `policy.reviewHash` | `bytes32` | `REVIEW_HASH` |

</details>

<details>
<summary>ZZZV4RouteExecutor.Policy</summary>

<a id="input-zzzv4routeexecutor-policy"></a>

| Field | ABI type | Example input |
| --- | --- | --- |
| `policy` | `(address,address,(address,address,uint24,int24,address),address,address,bytes32,bytes32,bytes32,bytes32,bytes32)` | `["SOURCE_ADDRESS", "OUTPUT_ADDRESS", ["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"], "POOL_MANAGER_ADDRESS", "STATE_VIEW_ADDRESS", "SOURCE_CODE_HASH", "OUTPUT_CODE_HASH", "POOL_MANAGER_CODE_HASH", "STATE_VIEW_CODE_HASH", "REVIEW_HASH"]` |
| `policy.source` | `address` | `SOURCE_ADDRESS` |
| `policy.output` | `address` | `OUTPUT_ADDRESS` |
| `policy.key` | `(address,address,uint24,int24,address)` | `["0x0000000000000000000000000000000000000000", "ZZZ_ADDRESS", "FEE", "TICK_SPACING", "0x0000000000000000000000000000000000000000"]` |
| `policy.key.currency0` | `address` | `0x0000000000000000000000000000000000000000` |
| `policy.key.currency1` | `address` | `ZZZ_ADDRESS` |
| `policy.key.fee` | `uint24` | `FEE` |
| `policy.key.tickSpacing` | `int24` | `TICK_SPACING` |
| `policy.key.hooks` | `address` | `0x0000000000000000000000000000000000000000` |
| `policy.poolManager` | `address` | `POOL_MANAGER_ADDRESS` |
| `policy.stateView` | `address` | `STATE_VIEW_ADDRESS` |
| `policy.sourceCodeHash` | `bytes32` | `SOURCE_CODE_HASH` |
| `policy.outputCodeHash` | `bytes32` | `OUTPUT_CODE_HASH` |
| `policy.poolManagerCodeHash` | `bytes32` | `POOL_MANAGER_CODE_HASH` |
| `policy.stateViewCodeHash` | `bytes32` | `STATE_VIEW_CODE_HASH` |
| `policy.reviewHash` | `bytes32` | `REVIEW_HASH` |

</details>

### Deployment constructors

<details>
<summary>Deployment-only inputs; no deployment authorization</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [AccessController.constructor](CONTRACT_FUNCTIONS.md#zzzaccesscontroller) | `initialGovernance: address`<br>`initialKeeper: address`<br>`initialGuardian: address` | `deploy AccessController(INITIAL_GOVERNANCE_ADDRESS, INITIAL_KEEPER_ADDRESS, INITIAL_GUARDIAN_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [ActivationAssets.constructor](CONTRACT_FUNCTIONS.md#zzzactivationassets) | `controller: address`<br>`poolRegistry: address` | `deploy ActivationAssets(CONTROLLER_ADDRESS, POOL_REGISTRY_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [ActivationAssetsFactory.constructor](CONTRACT_FUNCTIONS.md#zzzactivationassetsfactory) | None | `deploy ActivationAssetsFactory()` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [ActivationEntry.constructor](CONTRACT_FUNCTIONS.md#zzzactivationentry) | `controller: address`<br>`poolRegistry: address`<br>`assets: address` | `deploy ActivationEntry(CONTROLLER_ADDRESS, POOL_REGISTRY_ADDRESS, ASSETS_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Buyback.constructor](CONTRACT_FUNCTIONS.md#zzzbuyback) | `controller: address`<br>`zzzToken: address`<br>`maximumTradeUSD: uint256` | `deploy Buyback(CONTROLLER_ADDRESS, ZZZ_TOKEN_ADDRESS, MAXIMUM_TRADE_USD)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [CanonicalHandoff.constructor](CONTRACT_FUNCTIONS.md#zzzcanonicalhandoff) | `controller: address` | `deploy CanonicalHandoff(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [ClaimRouter.constructor](CONTRACT_FUNCTIONS.md#zzzclaimrouter) | `controller: address`<br>`nftController: address`<br>`royaltyLedger: address` | `deploy ClaimRouter(CONTROLLER_ADDRESS, NFT_CONTROLLER_ADDRESS, ROYALTY_LEDGER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Compounder.constructor](CONTRACT_FUNCTIONS.md#zzzcompounder) | `controller: address` | `deploy Compounder(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [ContributionPricing.constructor](CONTRACT_FUNCTIONS.md#zzzcontributionpricing) | `controller: address`<br>`priceOracle: address` | `deploy ContributionPricing(CONTROLLER_ADDRESS, PRICE_ORACLE_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [CustodyValidation.constructor](CONTRACT_FUNCTIONS.md#zzzcustodyvalidation) | `controller: address` | `deploy CustodyValidation(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [FeeController.constructor](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `controller: address` | `deploy FeeController(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [FeesCanonical.constructor](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `controller: address`<br>`feeController: address` | `deploy FeesCanonical(CONTROLLER_ADDRESS, FEE_CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [LPBalanceMath.constructor](CONTRACT_FUNCTIONS.md#zzzlpbalancemath) | None | `deploy LPBalanceMath()` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [LPBalancer.constructor](CONTRACT_FUNCTIONS.md#zzzlpbalancer) | `controller: address`<br>`core: address`<br>`state: address` | `deploy LPBalancer(CONTROLLER_ADDRESS, CORE_ADDRESS, STATE_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [LPPositionExecutor.constructor](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `controller: address`<br>`positionManager_: address`<br>`stateView_: address`<br>`poolManager_: address`<br>`permit2_: address`<br>`balancer_: address` | `deploy LPPositionExecutor(CONTROLLER_ADDRESS, POSITION_MANAGER_ADDRESS, STATE_VIEW_ADDRESS, POOL_MANAGER_ADDRESS, PERMIT2_ADDRESS, BALANCER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [LPRewardConverter.constructor](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `controller: address`<br>`rewards: address`<br>`wrappedETH: address` | `deploy LPRewardConverter(CONTROLLER_ADDRESS, REWARDS_ADDRESS, WRAPPED_ETH_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [LiquidityManager.constructor](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `controller: address`<br>`positionManager_: address`<br>`stateView_: address`<br>`poolManager_: address`<br>`permit2_: address`<br>`balancer_: address` | `deploy LiquidityManager(CONTROLLER_ADDRESS, POSITION_MANAGER_ADDRESS, STATE_VIEW_ADDRESS, POOL_MANAGER_ADDRESS, PERMIT2_ADDRESS, BALANCER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Membership.constructor](CONTRACT_FUNCTIONS.md#zzzmembership) | `controller: address` | `deploy Membership(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Migration.constructor](CONTRACT_FUNCTIONS.md#zzzmigration) | `controller: address` | `deploy Migration(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [MigrationBudget.constructor](CONTRACT_FUNCTIONS.md#zzzmigrationbudget) | `controller: address` | `deploy MigrationBudget(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [NFT.constructor](CONTRACT_FUNCTIONS.md#zzznft) | `controller: address`<br>`baseURI: string` | `deploy NFT(CONTROLLER_ADDRESS, IPFS_BASE_URI)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [NFTCanonical.constructor](CONTRACT_FUNCTIONS.md#zzznftcanonical) | `controller: address`<br>`collection: address` | `deploy NFTCanonical(CONTROLLER_ADDRESS, COLLECTION_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [NFTMetadata.constructor](CONTRACT_FUNCTIONS.md#zzznftmetadata) | `controller: address` | `deploy NFTMetadata(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Oracle.constructor](CONTRACT_FUNCTIONS.md#zzzoracle) | `controller: address`<br>`sequencer: address` | `deploy Oracle(CONTROLLER_ADDRESS, SEQUENCER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [PoolRegistry.constructor](CONTRACT_FUNCTIONS.md#zzzpoolregistry) | `controller: address` | `deploy PoolRegistry(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [PortfolioPolicy.constructor](CONTRACT_FUNCTIONS.md#zzzportfoliopolicy) | `controller: address` | `deploy PortfolioPolicy(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [ProtocolPolicy.constructor](CONTRACT_FUNCTIONS.md#zzzprotocolpolicy) | `controller: address`<br>`initialMintRecipient: address` | `deploy ProtocolPolicy(CONTROLLER_ADDRESS, INITIAL_MINT_RECIPIENT_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [PythPriceFeed.constructor](CONTRACT_FUNCTIONS.md#zzzpythpricefeed) | `source: address`<br>`codeHash: bytes32`<br>`id: bytes32`<br>`exponent: int32`<br>`age: uint32`<br>`confidenceBps: uint16`<br>`review: bytes32` | `deploy PythPriceFeed(SOURCE_ADDRESS, CODE_HASH, ID, EXPONENT, AGE, CONFIDENCE_BPS, REVIEW)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [RebalanceConfirmation.constructor](CONTRACT_FUNCTIONS.md#zzzrebalanceconfirmation) | `controller: address` | `deploy RebalanceConfirmation(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Rewards.constructor](CONTRACT_FUNCTIONS.md#zzzrewards) | `controller: address` | `deploy Rewards(CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [RoyaltyFactory.constructor](CONTRACT_FUNCTIONS.md#zzzroyaltyfactory) | None | `deploy RoyaltyFactory()` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [RoyaltyRewards.constructor](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `nftController: address` | `deploy RoyaltyRewards(NFT_CONTROLLER_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Strategy.constructor](CONTRACT_FUNCTIONS.md#zzzstrategy) | `controller: address`<br>`portfolio: address`<br>`confirmation: address` | `deploy Strategy(CONTROLLER_ADDRESS, PORTFOLIO_ADDRESS, CONFIRMATION_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [V4RouteExecutor.constructor](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | None | `deploy V4RouteExecutor()` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [Vault.constructor](CONTRACT_FUNCTIONS.md#zzzvault) | `controller: address`<br>`nftHomeChain: uint256`<br>`budget: address` | `deploy Vault(CONTROLLER_ADDRESS, NFT_HOME_CHAIN, BUDGET_ADDRESS)` | Deploy bound implementation |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `D` [VaultCanonical.constructor](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `controller: address`<br>`vaultController: address`<br>`chain: uint256` | `deploy VaultCanonical(CONTROLLER_ADDRESS, VAULT_CONTROLLER_ADDRESS, CHAIN)` | Deploy bound implementation |

</details>

### ETH receive hooks

<details>
<summary>No ABI arguments; sender/value authentication still applies</summary>

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Buyback.receive](CONTRACT_FUNCTIONS.md#zzzbuyback) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [FeeController.receive](CONTRACT_FUNCTIONS.md#zzzfeecontroller) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [FeesCanonical.receive](CONTRACT_FUNCTIONS.md#zzzfeescanonical) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [LPPositionExecutor.receive](CONTRACT_FUNCTIONS.md#zzzlppositionexecutor) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [LPRewardConverter.receive](CONTRACT_FUNCTIONS.md#zzzlprewardconverter) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [LiquidityManager.receive](CONTRACT_FUNCTIONS.md#zzzliquiditymanager) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Migration.receive](CONTRACT_FUNCTIONS.md#zzzmigration) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Rewards.receive](CONTRACT_FUNCTIONS.md#zzzrewards) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `P` [RoyaltyRewards.receive](CONTRACT_FUNCTIONS.md#zzzroyaltyrewards) | `value: wei` (separate) | `send ETH; data=0x; value=ROYALTY_ETH_WEI wei` | Receive marketplace ETH royalties |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [V4RouteExecutor.receive](CONTRACT_FUNCTIONS.md#zzzv4routeexecutor) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [Vault.receive](CONTRACT_FUNCTIONS.md#zzzvault) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

| Function name | Expected input | Example call inputs | Explanation |
| --- | --- | --- | --- |
| `M` [VaultCanonical.receive](CONTRACT_FUNCTIONS.md#zzzvaultcanonical) | `value: wei` (separate) | `send ETH; data=0x; value=SETTLEMENT_WEI wei` | Receive authenticated ETH settlement |

</details>

<!-- END GENERATED OPERATOR CALLS -->
