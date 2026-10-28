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
| Stop everything possible, recover and restart safely | [Stop controls](#stop-controls) and [incident recovery](#incident-recovery) |
| Move existing LP, close it temporarily, or change chains | [Custody and LP migration](#custody-and-lp-migration) |
| Change prices, sequencer checks or wrapper policy | [Dependencies and pricing](#dependencies-and-pricing) |
| Collect LP fees, compound, burn or process royalties | [Revenue operations](#revenue-operations) |
| Change the automatic fee-harvest interval | [Standalone harvesting schedule](#change-the-standalone-harvesting-interval) |
| Resolve pending artwork reveals or replace all contracts; recover failed holder-file/CLI input | [Mint and metadata](#mint-and-metadata), [whole-collection replacement](#whole-collection-replacement) |
| Change managers/keys, replace a server, update software or contain stalled RPC | [Authorities](#authorities), [services](#services-and-server-recovery) |
| Use a browser wallet locally, recover pending transactions or inspect exact approvals | [Browser-wallet signing and recovery](BROWSER_WALLET.md) |
| Run the current selected-pool read-only fork harness | [Development and fork qualification](DEVELOPMENT.md#fork-and-operating-qualification) |
| Publish poplint without changing the demo | [Demo/integration environment map](SITE_ENVIRONMENTS.md) |
| Configure reviewed API holdings; rehearse wallet sends on local Anvil only | [Reviewed website API profile](DEPLOYMENT_WEBSITE.md) |
| Know what cannot be changed after sealing | [Fixed boundaries](#fixed-boundaries) |

## Current accounting4 deployment boundary

Fresh source uses Vault.ACCOUNTING_VERSION4, Migration.CUSTODY_VERSION3,
Access.GOVERNANCE_VERSION2 and
`SCHEMA()==keccak256("ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5")`.
Verify exact chain/runtime/module pins and the [profile](POSITION_V4.md).
Eight Position words remain; statuses are None0/Active1/Outbound2/Dormant3/
Parked4/Exited5. Historical profiles/Anvil/journals keep their own meanings.

- Contribution inputs remain native ETH and one fixed ZZZ. Entry binds exact
  value/approval, current owner, original source value, caller maximum and
  actual marginal LP. Activation$100/growth$5 and2%default cap remain.
- Production LP admission is native ETH/fixedZZZ only through configureNative.
  Another reviewed fee tier is possible; ERC20-only LP admission is removed.
  Separate reward-conversion venues/currencies do not expand principal assets.
- Native LP fees retain80/10/5/5; claims and royalty weights are independent.
  Pending5%compound belongs to principal on collective exit; designated buyback
  and already earned reward/royalty backing stay separate.
- Governance may pause and permanently start collective exit, close every bucket
  without swaps/USD price reads, allocate shares and deliver ETH+ZZZ to current
  owners in batches. No external custody recipient, recovery ingress, all-ZZZ
  conversion exit or royalty drain exists. [Exact procedure](HOLDER_COLLECTIVE_EXIT.md).
- Access.lpExitStarted is irreversible. Unpause cannot restart mint, activation,
  growth, LP maintenance or canonical replacement. Old claims/transfers and future
  royalties remain available; new LP earnings end after all buckets close.
- Use explicit accounting4 API/keeper configuration and new state paths. API
  requires principal_exit runtime/address pins; keeper also binds access/fees/
  vault. Existing accounting3 poplint stays unconfigured and is not a profile4
  frontend. Public signing stays Anvil-only; no deployment is authorized here.

### Fixed ZZZ setup order

Review and configure the two-source USD policies first. Bind
`ActivationAssets.configureZZZ(token,codeHash,reviewHash)` once before
`PoolRegistry.configureNative`; deploy/bind Buyback with that same immutable ZZZ,
then call the one-time `Migration.configureZZZ`. Verify matching nonzero source,
buyback and holder-return identities before sealing. A wrong immutable identity
requires a fresh reviewed deployment, not a post-seal repair setter. Raw emergency
exit does not gain a conversion/buyback dependency.

### Deployment and integration qualification

| Need | Procedure and boundary |
| --- | --- |
| Exact version, modules, helper runtimes and addresses | [Address inventory](DEPLOYMENT_ADDRESSES.md) and [schema-6 preflight](PRODUCTION_PREFLIGHT.md), which separately observes17helpers; historicalschema5 is inspection-only. Observed code cannot approve its own runtime pin; retain creation-to-anchor policy history. |
| OpenSea primary mint and VRF | [Mint qualification](MINT_INTEGRATION_QUALIFICATION.md). Buyer gross 0.05 ETH, recipient net of actual platform fee, gas separate. Current direct mint still pays all 0.05 ETH; supported OpenSea/VRF integration is unfinished. |
| USD providers, proxy controls and update services | [Price security](PRICE_SECURITY.md), [service decisions](PRODUCTION_SERVICES.md) and optional [Pyth reader](PYTH_PRICE_SOURCE.md). Review upstream independence, update costs, funding and recovery; a matching ABI is not provider qualification. |
| Current website read/unsigned review | [Explicit native profile](NATIVE_WEBSITE_PROFILE.md). Current accounting3 must not be served with a historical accounting2 reader. Actual consumer/service acceptance remains open; public DEPLOYMENT is null and signing Anvil-only. |
| RPC and exact frozen audit inputs | [Bounded RPC qualification](RPC_PREPARATION_QUALIFICATION.md) and [frozen review bundle](FROZEN_REVIEW_BUNDLE.md). A timeout is not proof of rejecting missing blocks; package export is not audit approval. |

Source-scoped audit results belong to [reports](../reports/README.md), not to a
second release history in this manual. Current internal static coverage passes;
actual dependencies, target-chain gas/operations and independent audit remain open.


## Liquidity placement and keeper policy

For post-exit automatic payouts, configure the [principal worker and retry interval](KEEPER_RECOVERY.md#optional-automatic-principal-delivery). Repeated rejected batches default to hourly retry; serial-job priority alternates durably. Apply JSON changes through controlled restart, preserve the journal and refresh config-bound health; no contract update/resealing or new authority is required.

Read [keeper safeguards](KEEPER_SAFEGUARDS.md) for the full protection inventory
and the distinction between on-chain enforcement and bypassable service policy.

Use [idle and dust ownership](IDLE_AND_DUST.md) before any cleanup. Contributions
default to 2% (98% marginal deployed LP), conversion 1%, maintenance 3%, gas separate.
Fresh LP routing1 selects one bounded route/size using actual-core quotes and
executes zero or one balancing swap. Contributions can swap/deploy only their
own amounts; old idle/compound stays attributed for guarded maintenance and in
incumbent share NAV. Retained idle still backs the same bucket. There is no
general clear/sweep or operator dust recipient.

### Add or remove an execution pool after sealing

This changes the swap venue, not the LP contribution destination. Use the fresh
Manager `LP_ROUTING_VERSION()==1` and immutable `balancingRouter()` helper;
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

Governance can tune `configureSolver(iterations,gasLimit,reviewHash)` within4-12
iterations and100000-300000gas per attempted quote; defaults8/200000. More search
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
   `0<=narrowBps<widenBps<2500`,600seconds<=interval<=7days, and interval at
   least the pool cooldown. Trigger/deviation must fit the narrower width.
   No default production thresholds or continuous-volatility claim is supplied.
4. Verify orientation, complete `keeperRangePolicy(pool)` and configuration/review
   hashes. The fingerprint binds all PoolConfig fields except desired width plus
   orientation. A changed non-width config makes selection unavailable until
   governance re-reviews it. `keeperRangeTarget(pool)` returns0 unless all policy,
   lifecycle, actual-position, cooldown and unapplied-tick checks pass. Malformed or
   failed dependency reads can revert; report unavailable, never coerce them to0.
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
5. Refresh the schema-5 release inventory with explicit `pricing_version: 2` and
   all 15 helpers, including `Oracle.contributionPricing()` and its `oracle()`/
   `access()` bindings. Update reviewed API/preparation/earnings configurations,
   source proxy pins and service alerts at one confirmed block. Keep old deployed
   epochs and wallet journals on their original profiles.
6. Qualify $100 activation and $5 growth in actual token units through the full
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

Source reads, asset-decimals and sequencer reads have a fixed 500,000-gas call
ceiling and exact ABI checks. Qualify actual proxy gas before admission. Strategy
read snapshots last one planning call only; execution/final checks re-read. Raw
funded claims do not need USD prices. Public push-feed reads need no per-read
LINK transfer, but adapters, updates, RPCs and VRF can cost money; review each
actual product and upstream authority. [Price operating requirements](PRICE_SECURITY.md).


<a id="pending-15-minute-rebalance-confirmation"></a>

### Configure rebalance confirmation

For a fresh confirmation1 deployment, resolve `Strategy.rebalanceConfirmation()`
from the sealed Access Strategy. Verify helper/Strategy/Budget capability1,
runtime and Access/parent bindings. Old immutable deployments do not gain this
feature by editing JSON. Preserve their exact readers and original journals.

1. Governance calls the **helper**
   `configure(uint32 secondsRequired,uint32 maximumGap,bytes32 reviewed)`.
   Selected values are `900,300,<nonzero review hash>`:15 minutes with a strict
   five-minute maximum confirmed observation gap. Duration bounds60seconds-7days;
   maximumGap0 means stopped/unconfigured, otherwise at most half the duration.
   Source construction starts gap0; no reviewed operating policy is invented.
2. Simulate from the real governance wallet. Confirm `ConfirmationConfigured`,
   duration/gap/review hash and increased `policyRevision`. Any reconfiguration,
   including change-and-restore, invalidates old samples. Ordinary pause permits
   configuration; preparation/canonical locks and principal exit block it.
3. The matching keeper/API config declares `rebalance_confirmation_version:1`,
   exact helper/runtime and actual Budget/Strategy/Vault bindings. Follow the
   controlled release/config restart procedure with preserved pending receipts,
   nonce and spend records. On-chain configuration alone needs no process restart.
   Keeper preflight and health validate this policy even during LP cooldown and
   with standalone compounding disabled; they read no bucket condition or price.
4. After the hard12-hour cooldown the service checks every300seconds, rather than
   hourly, and records `observe(bucket)` through its normal simulation/fee/gas/
   journal/receipt path. The main `interval_seconds` must be at most300 to deliver
   that cadence; pending work or unavailable services may delay it. Every gap
   greater than300 restarts the window. Scheduling at exactly300 provides no
   latency allowance and may restart repeatedly. This strict choice is deliberate;
   do not silently add grace or promise execution at a fixed time.
5. Read `observations(bucket)` (identity,firstSeen,lastSeen,side), `condition(bucket)`
   and `ready(bucket)` at one canonical block. Raw `Strategy.needsRebalance` is
   not buffered readiness. Budget checks `Strategy.rebalanceReady` before execute.
   Side1 is below,2 above. A deliberate width change bypasses confirmation only,
   after the same hard cooldown. Compound yields while raw rebalance is due.
6. The service starts durable1-10minute jitter after readiness, continuing samples
   while waiting. Inside/opposite-side/changed-LP/policy/stale records restart.
   Successfully observed dependency faults clear evidence. After an off-chain
   fault, startup, interrupted recovery or observed pause, the worker persists a
   clear-only reset requirement. Confirm its authorized `resetObservation(bucket)`
   receipt before extending evidence. A failed reset transaction does not clear
   the requirement. Do not edit journals or resend an ambiguous transaction.

Relevant raw group/pool read failures invalidate that bucket's fresh window; a failed
initial global lifecycle/authority/head read marks only known fresh windows for
reset. Unrelated router, compound, harvest or health-read failures degrade their
own work. A canonical clear acknowledgement suppresses repeated paid resets
while waiting for recovery, never authorizes cached readiness. Every nonempty
foreign record requires another clear while the acknowledgement remains, even
after an earlier healthy empty read. Only our own new observation intent removes
it atomically with pending persistence. New windows draw new post-ready jitter;
routine sample renewals preserve the existing delay.

Known failed observe/rebalance receipts require an explicit reset before ordinary
worker retry. The failed transaction itself cannot persist a deletion: atomic
rollback restores its previous evidence, LP and accounting. If executing manually,
reconcile the exact receipt and confirm `resetObservation` before rebuilding the
window; never assume a failed call cleared it. A callback which clears/changes
evidence during successful-path maintenance makes the whole operation revert.

No transaction can prove every price between samples. Hidden moves and unobserved
pause/fault cycles may be missed; observations also advertise pending upkeep.
This is sampled confirmation, not continuous history, execution privacy or an
anti-manipulation guarantee. Hourly fee harvest, claims and receipt recovery stay
independent. To stop new ordinary readiness use reviewed gap0; governance cannot
use the setter to authorize a premature ordinary rebalance. [Policy and limits](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer).


### Set additional execution loss

For fresh `EXECUTION_QUALITY_VERSION()==1`, governance calls
`Strategy.setAdditionalLossBps(uint16 limit,bytes32 reviewHash)`. The initial limit
is100bps (1%) beyond actual directional LP/protocol fees; allowed0-1000bps.
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
at2,590,680gas (one venue) and5,963,090gas (four), before full maintenance and the
keeper's25% estimate padding. These are historical fixture observations, not
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
history. `stopped` means gap0; `incompatible_cadence` means a nonzero gap below300;
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
| Contribution or maintenance limit | Budget `setLossLimits(uint16 contribution,uint16 maintenance)` | Read both current values; preserve the other when changing one. Captured per-operation policy and pending custody approval floors never relax automatically. |
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

### How governance calls work

After sealing, the wallet returned by `Access.governance()` calls the governed
module **directly**. The module authenticates it through `Access.canConfigure`.
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
the immutable mint recipient do not change. See [governance semantics](GOVERNANCE.md)
and [controller source](../src/ZZZAccessController.sol).

## Authorities

| Authority | Management action | Rotation/recovery |
| --- | --- | --- |
| Governance wallet | Direct governed configuration, custody changes and replacement admission | Verify `governance()` and the wallet's own signers/threshold. Rotate via `proposeGovernance` then candidate `acceptGovernance`; zero proposal cancels. Changing owners/threshold of the same Safe uses that Safe's own process. No controller-admin recovery exists if governance is lost. |
| Guardian | Direct `AccessController.setPaused(true)` | Governance uses `setGuardian(address,bool)`. A guardian cannot unpause, choose a new pool, withdraw LP or repair lost governance. |
| Keeper | Eligible bounded maintenance; cannot approve or execute discretionary custody exits or same-pair pool moves | Governance uses `setKeeper(address,bool)`. Isolate/revoke a compromised signer, reconcile its pending transactions, then qualify a new signer and state. No salary, gas reimbursement or bounty is automatic. |
| Bootstrap | Initial bindings and sealing | `bind` and `seal` only before sealing; bootstrap is erased. Do not retain deployment keys as a supposed recovery backdoor. |
| Mint recipient | Current direct mint pays 0.05 ETH; required OpenSea path pays net after its actual platform fee from the same buyer total | Immutable Vault constructor address; receiving money grants no management authority. No post-seal setter. |

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

1. Read `PoolRegistry.get(poolId)` and copy the **entire** `PoolConfig`, including its real venue key. Change only intended settings. Use `configureNative(config)` for supported native ETH/fixedZZZ fee tiers; generic ERC20 LP admission is removed. Current accounting3 retains the real zero ETH currency; do not substitute WETH or change slot ordering.
2. Check the dependent bounds below, oracle freshness, current price/spot difference, target ticks, actual swap costs and expected gas. Review narrower-range out-of-range exposure and turnover. Simulate the new configuration and maintenance on a fork at the same state before approval.
3. Governance executes the configuration. This **does not immediately close/reopen LP**. Inspect `Strategy.rangeUpdatePending(bucketId)` and `needsRebalance(bucketId)`.
4. The authorized keeper submits `Vault.rebalance(bucketId,minimumLiquidity,deadline)` when cooldown and guards permit. A width mismatch can trigger it even at a flat price. Polling every ten minutes is only an example; it is not a guaranteed rebalance deadline.
5. Verify the new physical LP ID/ticks/center, retained value, attributed idle, unchanged NFT shares and continued claims. A successful replacement clears the width mismatch. A revert preserves the old position and leaves the desired change pending.

Before execution, restoring the old configuration may clear the width mismatch; actual physical range exit can still permit policy2 rebalance after cooldown. The movement trigger belongs to historical policy1. After execution, going back requires another valid configuration and rebalance, with fresh costs/cooldown. Stop/reconcile in-flight keeper work around a policy change: its transaction is not bound to a historical configuration hash. See [range application](RANGE_POLICY_UPDATES.md).

### Operator-selected LP policy

Fresh `Strategy.MAINTENANCE_POLICY_VERSION()==2` and Budget compound capability3
implement the settled [LP policy](LP_EXECUTION_POLICY.md). Operator selects
+/-25% or +/-50%; keep optional automatic selection disabled using governance
`Strategy.setKeeperRangePolicy(poolId,false,0,0,0,bytes32(0))` and local
`adaptive_range.enabled=false`. No new volatility analysis is involved.

Read the complete `PoolRegistry.get(poolId)` tuple and governance-call
`configureNative(fullConfig)` with reviewed fields: `rangeBps=2500` or `5000`
in orientation1, `minRebalanceInterval=43200` (12 hours), and
`maxPositionUSD=1000000000000000000000000` ($1m cumulative contributions per NFT,
USD18). Preserve actual assets, flags, fees and all other limits. These are intended
initial configuration values, not an installed deployment or $1bn capacity proof.
Governance can later change the supported interval within600seconds-7days; the
current interval is a hard minimum even when LP exits its range earlier.

After cooldown, ordinary rebalance requires actual physical range exit
(`tick < lower || tick >= upper`), or your deliberately configured desired-range
mismatch. A width change can therefore be applied while the old LP is in range.
`triggerBps` remains in the ABI/configuration but no longer authorizes ordinary
replacement in policy2. It is not a tolerated centring error. Physical LP changes
only after successful execution; top-ups do not recenter it or reset its clock.

Fresh keeper config selects maintenance2, compound3 and confirmation1 with exact
Strategy/Budget/helper runtimes and bindings. After cooldown, ordinary confirmation
evaluations are300seconds apart, inside or outside; historical policy2 without
confirmation retains hourly inside checks. The matching60second main loop handles
due checks, receipts and independent hourly harvest. Once sampled readiness is
true, it saves one60-600second jitter while continuing observations. A deliberate
range change bypasses confirmation, never hard cooldown. Revalidate fresh state
before submission; an ordinary return inside cancels readiness. Jitter survives
restart; startup's explicit confirmation reset still requires fresh evidence.
Top-ups/harvest do not redraw an existing schedule. Software jitter cannot
constrain a key bypassing Python or promise exact inclusion. Failed/ambiguous
calls keep normal pending/nonce/backoff recovery. Downtime does not replay missed
rebalances. Follow [confirmation configuration](#configure-rebalance-confirmation).

Range/cooldown/cap changes are read fresh on-chain: normally no restart or reseal.
Width configuration is not an immediate LP replacement. Read `rangeUpdatePending`
and verify actual new LP/ticks after confirmation. Lowering an interval can make
an old position eligible immediately; it does not reset its clock. Stop/reconcile
pending work around policy changes because rebalance calldata does not bind a
historical configuration hash. Never erase pending intents or repeat a transaction.

Local JSON changes (policy version, poll, thresholds or route candidates) require
a controlled restart: no hot reload. Preserve journal/pending/nonce evidence and
require fresh matching config-bound health. Old accounting4 keeper configs with
no new policy field retain explicit historical mode1 behavior; never relabel an
old runtime/journal as policy2. Accounting1/2/3 retain their own readers. No running
service changes follow from editing an example. [Recovery](KEEPER_RECOVERY.md#logs-health-and-fallback).

### Manual rebalance at a chosen time

A keeper-authorized wallet can call the existing nonpayable function:

`Vault.rebalance(bucketId,minimumLiquidity,deadline)`

This is the same guarded LP replacement as automated upkeep. It bypasses only
Python's evaluation schedule and random waiting; it cannot bypass sampled
confirmation1, hard on-chain cooldown, actual-range/operator-update eligibility, pause/lifecycle, prices or
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
   `Strategy.rebalanceReady(bucketId)`. For ordinary confirmation1, authorized
   receipt-backed `observe(bucketId)` calls must establish the reviewed window
   first; a raw true alone is insufficient. See the confirmation procedure.
   A failed price/read
   is unavailable, not false or permission to force execution. Initial12hours is
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
| `rangeBps` | 100-5000, also greater than trigger and spot tolerance | Because `triggerBps >= 100` and must be smaller, 100 itself cannot form a valid complete configuration. Wider/narrower ranges still require representable ticks. |
| `triggerBps` | At least 100 and less than range | Retained ABI/config field; historical policy1 movement trigger. Policy2 ordinary eligibility uses actual range exit or an operator range change, never this movement field. |
| `minRebalanceInterval` | 600 seconds-7 days | Minimum time between rebalances; a safety cooldown, not a governance delay. |
| `maxSpotDeviationBps` | 1-500 and less than range | Spot/reference discrepancy permitted by guarded execution. Do not widen it simply to accept a manipulated market. |
| `maxSlippageBps` | 1-1000 in fresh LP routing1; pool fee must be strictly below it in equivalent units | Operating values are not raised automatically. Selected LP fee10020pips requires at least101bps before other costs. Routing uses the tighter target/venue guard, plus actual protocol fee, impact, captured loss and caller floors. Historical profiles retain their original ceiling. |
| `minDepositUSD`, `maxPositionUSD` | Positive minimum; maximum at least minimum | Minimum for each contribution and maximum cumulative gross contribution per NFT, in 18-decimal USD units; not a live market-value ceiling or total pool cap. Lowering them cannot remove the fixed $100 activation / $5 top-up floors. The effective minimum is the larger of the action floor and configured minimum. Check existing NFT contributions/top-ups. |
| `depositsEnabled`, `operationsEnabled` | Full configure for enabling; `disablePool` can only clear flags | Different controls; see below. |

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

### Contribution minimums

For normal $5 increases, governance configures `minDepositUSD=5e18` through the
appropriate full `configure`/`configureNative` call. Activation still requires
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
4. A supported future target pair can need an internal conversion route even though user inputs remain ETH/ZZZ. Pin its exact venue, code, route and prices, simulate the full Entry operation and verify its captured contribution floor before admission. Pool/route reconfiguration does not reopen a disabled source.

Current native accounting uses explicitly admitted ETH at `address(0)`, with an independent feed and exact call value. It is never an ERC20 approval target. Accepting a new **input** does not automatically admit an LP or royalty payout currency. Only native ETH and the explicitly reviewed ZZZ identity may be user inputs. Actual ETH/ZZZ routes and services remain subject to [qualification](ACTIVATION_PREPARATION.md).

### Replace a swap route when market liquidity moves

Read/review the new route, append it with `addRoute`, qualify it, switch the backend's selected route, and use `setRouteEnabled(oldId,false)` to stop the old route. Route contents/identities are immutable; do not overwrite one in a manifest under the old hash. There is no time delay. Concurrent user quotes may revert after disablement and must be rebuilt. Already mined operations cannot be undone.

To stop an input immediately, use `ActivationAssets.setAsset(token,false,expectedCodeHash,reviewHash)` with the exact ETH-zero or fixed-ZZZ token and nonzero review hash, and disable affected Entry routes. Disable paths deliberately avoid dependency calls needed for enabling; they can help when a token/feed is broken. Previously attached LP, shares and claims are not erased. Re-enabling requires valid current token/feed/code checks and new quotes. Pool configuration cannot silently re-enable an explicitly disabled source. See [Entry and source policy](ACTIVATION_ENTRY.md) and [routing](ACTIVATION_ROUTING.md).

## Pool admission and retirement

For a supported new LP venue, first qualify tokens, feeds, reward-asset admission (`Rewards.addAsset(token)`), the exact venue key/manager and strategy. Then governance calls `configure` or the narrowly supported `configureNative`. Not every Uniswap v4 hook/native pair is supported. Native admission permits only supported static, hookless ETH/ZZZ keys on the pinned Robinhood dependencies; immutable bindings are not arbitrary venue plug-ins.

### One contribution pool at a time

`PoolRegistry.contributionPool()` is the only pool whose `depositsEnabled` flag
can be true; zero means new activations/top-ups are stopped. Initial production
configuration must select the reviewed Robinhood hookless native ETH/ZZZ pool
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`.
The policy is per registry, not a permanent chain/pair restriction. A second
enabled pool is rejected even through governance; comments/UI restrictions are
not the enforcement boundary. Disabling only operations retains its selection.

To switch contributions after sealing:

1. Review the supported destination and full config. It may be admitted with
   `depositsEnabled=false` for preparation/maintenance; this does not select it.
2. Governance disables the current pool with `disablePool(oldId,true,false)`,
   then fully validates/enables the new config through `configure` or
   `configureNative`. When moving an existing shared bucket, **move it before
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
the new selection. Full `configure` with deposits=false also clears selection,
but still requires healthy dependencies. Roll back a selection using the same
validated switch; mined contributions cannot be undone. A canonical replacement
must explicitly configure its own selection; this is not imported economic state.
No new role or governance delay is introduced, and an already sealed old registry
cannot gain this rule through a configuration call.

The Vault has **four historical local bucket slots**, including permanent reservations/imports. `Vault.reservePool(poolId,bucketId)` is governance-controlled and consumes permanent identity/capacity; repeated matching reservation is idempotent. An unfunded reservation cannot simply be deleted to recover capacity. Check occupancy/history before admitting or reserving a new bucket. Existing bucket moves/returns reuse their identity, subject to pool occupancy; NFTs cannot be arbitrarily split/merged by an admin operation.

| Desired effect | Action | What remains |
| --- | --- | --- |
| Stop fresh activation/top-up into one pool | Governance calls `PoolRegistry.disablePool(poolId,true,false)` | Existing custody and claims remain; it does not withdraw LP or stop every maintenance operation. |
| Stop ordinary price-guarded maintenance in one pool | Governance calls `PoolRegistry.disablePool(poolId,false,true)` | Existing LP remains at the venue; fresh contributions also fail execution guards. Governed exit paths can still exit a disabled source with their own checks. |
| Retire a pool but preserve users' rights | Disable new contributions, cancel conflicting plans, move or park the bucket using the next section | Retain pool/history/receipts; do not delete indexer history or reward assets. |
| Resume use | Review dependencies, configure intended flags, verify live/pause/preparation state, re-quote and simulate | Enabling a flag does not relocate parked LP or restart a stopped server. |

**Disable without healthy dependencies.** `PoolRegistry.disablePool(poolId,disableDeposits,disableOperations)` only clears the selected flags of an already admitted pool. Use `(poolId,true,true)` to clear both. A `false` argument leaves that flag unchanged; it never enables anything. At least one argument must be `true`; repeated stops are safe. The function does not call tokens, prices, wrapper, hook or venue, and does not change the PoolKey, range or limits. Read `get(poolId)` and the resulting flags in `PoolDisabled` after execution.

**Reopen only after validation.** Read the complete current config, set the intended enabled flags and call `configure` or `configureNative`. Full fresh token/price/admission/venue checks still apply; a failed attempt leaves the stopped config unchanged. A previously approved operation can still be executable: cancel obsolete approvals and coordinate keeper/user transactions before reopening. A stop cannot undo a mined transaction.

Both stop and re-enable are exact immediate governance operations; there is no new guardian or keeper permission. Global pause does not block these configuration controls. Preparation, frozen/importing/retired lifecycle states do block them: cancel reversible preparation first if configuration is needed, or use permitted drains. The existing guardian global pause remains available for incidents. `operationsEnabled=false` is not a universal freeze: claims, transfers and some receipt/harvest/exit paths are separate. For a protocol-wide incident use the stop matrix.

## Custody and LP migration

There is **no external handoff custody address** in accounting4/custody3.
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
| Compound | Keeper `Compounder.compound(bucketId,minimumLiquidity,deadline)`; contributions/rebalances also pull the bucket's compound reserve | Standalone V2 compound waits after both the last compound and LP replacement, and yields to eligible rebalance/range selection. Uses attributed backing and guards; funds never pass through keeper. Holder claim balances are separate. |
| Buy back and burn | Keeper `Buyback.execute(token,amount,poolId,deadline)` | Check reserve, oracle value ≤ current `operatingTradeUSD` ≤ immutable `maxTradeUSD`, swap minima, actual ZZZ acquired and total-supply reduction. Governance tunes the operating ceiling with `setOperatingTradeUSD`; zero stops buys. The buyback target is immutable and must be the same ZZZ as contribution and normal exit. There is no retargeting setter. Bind Buyback before `Migration.configureZZZ`; mismatched or unbound targets cannot complete setup. Token migration requires custody exit and a fresh reviewed deployment. |
| Admit LP payout asset | Governance `Rewards.addAsset(token)` | Permanent bounded history, maximum 32; do not fill slots with speculative assets. Admission is distinct from input routing. |
| Receive marketplace royalties | `NFT.royaltyInfo(tokenId,salePrice)` returns the NFT's royalty receiver and requested 5% | Configure marketplaces with the **returned contract receiver**, never a manager wallet. ERC2981 is a request, not universal enforcement on every marketplace. |
| Admit royalty currency | Governance `NFT.addRoyaltyAsset(token)` | Initial scope is native ETH plus the independently verified Robinhood WETH wrapper; stablecoin conversion depends on marketplace qualification. Admission does not restrict sales or convert payouts. Separate bounded ledger (17 total including native); no arbitrary removal/sweep. Pre-admission/no-eligible-holder funds stay quarantined. |
| Synchronize/claim royalties | Permissionless `RoyaltyRewards.sync(asset)`/`syncAll`; actual owner calls ledger `claim` or bounded ClaimRouter | Direct royalty claim synchronizes pending admitted receipts. LP claim does not harvest new venue fees. Use current owner and actual funded amounts. |

A holder can claim both streams in a **1-32 operation atomic ClaimRouter batch**, or claim individually. One failed operation reverts the whole batch; simulate and split by asset/NFT if needed. No operator can choose a different beneficiary or claim just because it holds ERC721 approval. All unclaimed rights follow the current NFT owner; already paid funds do not travel with it. An escrow that owns the NFT is the contract-level holder. Lifetime claimed display requires complete confirmed index history, including predecessors after replacement.

Pause generally preserves claims and transfers while canonical state is operating. A frozen/retired deployment has different rules; follow lifecycle status rather than presenting a failing claim button. Failed payout tokens, blacklists or recipient callbacks may still block their claims. There is no generic admin seizure/sweep/rewrite to clear a liability. Keep actual funded balances distinct from unharvested fees and UI estimates.

Stop scheduled compounding/buybacks using reviewed keeper configuration or by stopping/revoking the keeper. Accumulated reserves remain classified on-chain; no automatic transfer to the operator is allowed. LP/royalty conversion uses its separately bound guarded converter; LP payouts and the fixed 80/10/5/5 allocation are unchanged. Creator-payment inboxes and measurement jobs are retired. See [royalty/claim behavior](CLAIM_ROUTER.md).

Before enabling automated revenue operations, review the actual
[schedule and reserve checks](OPERATIONS.md#reward-timing-and-maintenance-schedule).
The current accounting4 example polls every60seconds, evaluates eligible
confirmation every300seconds and schedules standalone
harvests every3600seconds (one hour), independently from rebalancing;
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
reviewed conversion path for ETH settlement. Reserving the5% allocations does
not execute compounding or buybacks. Sealed/live active custody and other guards
remain; no harvesting after terminal LP exit.

### Coordinate compounding with rebalancing

Fresh Budget `IDLE_COMPOUNDING_VERSION()==3` exposes
`compoundInterval(poolId)` and `compoundReady(bucketId)`. Default compound
interval is3600seconds (one hour), independently from the12-hour rebalance
configuration. This is earliest eligibility, not a promise to compound hourly.

Governance calls `Budget.setCompoundInterval(poolId,intervalSeconds)` on the
exact address returned by `Vault.migrationBudget()`. Allowed600seconds-7days;
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

Current keeper policy2 verifies exact Budget runtime, mutual Vault binding and
capability3 before readiness. Enabled compound requires explicit positive
`compound_thresholds` for both actual ETH/ZZZ currencies; use raw units per asset.
Historical policy1/helper2 and older helper1 readers remain versioned separately.
No automatic journal or runtime migration is provided. Readiness does not replace
keeper authority, lifecycle, prices, gas, deadline or execution/backing checks.

Harvest first creates the designated5% reserve; standalone compound also harvests
before pulling/reinvesting it. Hourly harvesting and holder claims remain independent;
claims never run compounding/buybacks. Stop new compounds through local scheduling
or keeper revocation, reconcile pending hashes, and reopen only after fresh checks.
[Idle ownership](IDLE_AND_DUST.md), [policy/evidence](LP_EXECUTION_POLICY.md).

### Change the standalone harvesting interval

As the sole operator, edit the **actual keeper service configuration**. The
setting is `maintenance.harvest_interval_seconds`, in seconds. The current
[accounting4 example](../keeper/config.holder-exit.example.json) uses **3600 = 1 hour**.
The historical accounting3 example retains14400seconds. This is an
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
   verify actual `FeesCollected`/`FeesAllocated` receipts when eligible. A fresh
   health result or dry run is not proof that a harvest transaction occurred.

The threshold uses the chain timestamp of the keeper's last **confirmed,
successful standalone** `harvest:<bucket>` action, not its restart time. A shorter
interval or a missing previous timestamp can make harvesting due immediately at
the next eligible cycle. Contributions, rebalances, compounding and outside
manual harvests do not reset that standalone journal timestamp. Polling uses the
separate `interval_seconds` setting (example600seconds, minimum60); an interval
shorter than the polling cadence cannot make checks run more often. Pending
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

Read `Buyback.maxTradeUSD()` (immutable hard ceiling) and `operatingTradeUSD()`
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
handoff does not copy the source's operating policy. The immutable hard maximum
cannot be raised by this setter. [Evidence and limits](../reports/post-seal-controls/VERIFICATION.md).

### Coordinate token and market dependencies

Use [Creator tasks / ZZZ team](../TODO.md#creator-tasks--zzz-team) to record public
ZZZ token controls, independent price sources and market continuity evidence.
Record each answer's date, authorized contact and supporting identifiers. Request
proof of control where relevant; never request a signing key. Creator-payment
terms, per-bucket funding receivers and measurement invoices no longer form part
of the selected hookless-pool operation. Marketplace royalties remain separate.

### Start a current keeper configuration

The shipped `keeper/config.example.json` selects native accounting version3 and
LP-only fee-intake version1 explicitly. It has no creator-sync or bridge jobs,
uses separate native/profile-specific state paths and leaves live review/runtime
pins unset. It must fail closed until actual deployment pins and operating limits
are reviewed. Compounding, conversions and adaptive ranges are off in this
example; enable each only with reviewed currency-specific thresholds/routes.
Do not apply this profile to an existing legacy journal or reuse an old state path.
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

Before sealing, qualify the actual randomness coordinator/network/subscription, funding asset, gas lane, confirmations and callback budget. `NFT.configureRandomness(...)` is **one-time before seal**; coordinator, gas lane, subscription ID and payment mode stay fixed. Only future confirmations and callback gas have the bounded control below. Funding/service management uses that provider's reviewed procedures, not an invented PoPL retry function. Do not seal against an unavailable/unqualified provider.

After initial configuration, governance can call
`NFT.setRandomnessRequestSettings(confirmations,gasLimit)` directly from the governance wallet, before or after seal. Contract bounds are 3-200 confirmations and
200,000-10,000,000 callback gas; independently check the actual coordinator's
potentially narrower bounds and simulate the intended next request. Read old
`requestConfirmations()`/`callbackGasLimit()`, execute exact calldata, then verify
both getters and `RandomnessRequestSettingsChanged(previousConfirmations,
previousCallbackGasLimit,confirmations,callbackGasLimit)`. Update the current
deployment observation and provider review; keep old request transactions intact.

Only requests created afterward use the new settings. The provider retains an
old request's original arguments; no ID, epoch, fulfillment, trait, quota or draw
order is rewritten. Raising gas now **cannot repair an already-submitted failed
callback**. Stop new mints, reconcile original requests and use the provider's
reviewed recovery procedure. There is no retry/reroll/provider replacement.
Configuration is allowed while ordinarily paused; preparation, canonical locks
and callbacks into an active mint block it. A successor uses its own reviewed
settings, not an imported source policy. Existing sealed code without this setter
does not gain it by configuration. [Scoped control review](../reports/post-seal-controls/REVIEW.md).

Monitor `RandomnessRequested`, `RandomnessReceived`, `TraitsFinalized`, subscription funding and oldest unanswered request. Authenticated fulfillment stores words; anyone can call `NFT.finalizeTraits(tokenId)` **in mint-ordinal order**. A fulfilled request awaiting finalization is different from a missing provider response. Read `nextToFinalize()` and `tokenAtOrdinal(ordinal)`; never guess token IDs from ordinal numbers. Fixed 600/300/100 quotas and prepared artwork draw remain unchanged.

The read API offers `GET /v1/mint-readiness`: confirmed minted/revealed counts, unfinished draws, earliest request/epoch, whether it awaits randomness or finalization, and the separate on-chain `mint_paused` flag. `new_minting_stopped` combines this flag with lifecycle controls; it is not a provider or gas-availability check. It checks inventory consistency and canonical deployment. It does **not** verify subscription funds, provider liveness, elapsed pending time, escrow compatibility or full handoff readiness; those fields are explicitly unverified. Correlate request/fulfillment events for latency and alert thresholds. The endpoint does not deploy a monitoring service or resume the paused chat monitor.

For a provider outage, governance calls `NFT.setMintPaused(true)` directly, with no waiting period. Verify `NFT.mintPaused()` and `MintPauseChanged(true)`. This blocks new NFT mint/randomness requests, including direct Vault callers; the complete transaction reverts without spending the mint payment. Pending original fulfillment and ordered finalization continue. Existing revealed NFTs can still activate/top up, transfer, claim and undergo LP maintenance when their independent guards permit. Pausing during the NFT receiver callback also rolls back that mint atomically.

To restart, qualify provider funding/liveness and reconcile pending requests; governance calls `NFT.setMintPaused(false)`, verifies the event/getter and simulates the complete mint. It does not clear global pause, preparation, canonical locks, exhausted supply or broken provider conditions. The mint switch is an operational setting, not an exported economic entitlement: for a replacement explicitly set/review the successor's desired state before locking it for import (fresh deployment default is `false`). It is not copied from the source and is not automatically cleared by handoff/abort. Existing sealed deployments without this function cannot acquire it by configuration.

There is **no coordinator swap, reroll, administrator-selected trait or pending-request transfer**. Ordinary LP pool migration/rebalance has no reveal-completion requirement. Global pause remains the wider incident control; hiding the Mint button alone does not stop callers. A permanently unanswered draw still blocks whole-collection replacement.

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
2. Require Access.lpExitStarted()==false; terminal principal settlement cannot be imported by this successor. Prepare the compatible V5 destination as an inert importer with CanonicalHandoff.prepareImport(sourceController) before its seal, qualify actual dependencies/randomness and verify its source binding. Governance starts the exact reviewed preparation notice. New mint/contribution/maintenance/config work stops; reveal, transfers, claims and permitted local parking remain available.
3. Finish existing provider responses and ordered `finalizeTraits` calls; confirm `unfinished_draws=0`. This is the selected simple policy: reliable funded provider plus draining before replacement. Do not remove the fully-revealed check if a request is stuck. Cancel the exact notice via `cancelPreparation(noticeHash)` if postponing, then restore ordinary controls deliberately.
4. Park each live bucket locally with its exact reviewed request; do not start collective holder exit. Governance freeze() stops ownership/accounting before capture. Complete six ordered settle(slot) domains, export/import batches of at most eight and completeImport(), then exact classified fund(slot,index) legs. Recover from on-chain cursors/roots rather than an assumed last successful command.
5. Verify every root, owner, trait, share, liability, reserve and exact backing. Governance `commit()` atomically retires the source and activates one successor. Finality remains required before service/marketplace cutover. Update canonical address/runtime and complete predecessor-history configuration, payout routing and marketplace collection records; old ERC721 approvals are not imported.
6. Before commit, `abort()` cancels the importer; return every funded leg via `returnFunds`, then `finishAbort()` only after full restoration. This is not immediate unlock. After successful commit the source cannot be revived by unpausing or cancelling preparation. Late royalty receipts forward one successor at a time through the supported royalty forwarding function. There is no creator-inbox forwarding path.

A successful same-chain handoff does not qualify cross-chain finality, transport or post-halt recovery. Do not promise these are solved by external principal custody. The retired v3 principal bridge stack is not bound in new deployments. Collective exit must not have started; canonical V5 rejects terminal principal settlement. Imported local buckets retain their reviewed shares/backing. Track the remaining design in the [canonical recovery task](../TODO.md#task-security-chain-recovery).

## Stop controls

**These controls are not interchangeable.** First reconcile already-broadcast transactions; stopping a service or disabling a route cannot undo a mined operation.

| Control | Stops | Preserves / restart |
| --- | --- | --- |
| Hide a frontend action | That UI path only | Direct contract calls continue. Restore UI only after real backend/on-chain readiness. |
| Stop an API/indexer/keeper process | That service's new work | On-chain custody/rights persist; another authorized keeper/direct caller may operate. Recover durable state before restart. |
| Revoke keeper | New authorized keeper actions from that address | Permissionless claims, transfers and allowed fee synchronization remain. Governance must authorize a reviewed replacement. |
| Disable source asset / Entry route | Affected contributions/conversions | Existing LP and funded claims remain. Re-enable after dependency review, re-quote. |
| `NFT.setMintPaused(true)` | New NFT mints and new randomness requests | Governance only. Original fulfillment/finalize, existing NFT rights and LP work retain their own guards. Resume with `false`; global/lifecycle controls remain. |
| `Buyback.setOperatingTradeUSD(0)` | New buyback executions only | Immediate governance; no price/reserve query. Resize/remove keeper buyback tasks to avoid deliberate simulation failures. Accrued reserves stay classified; reopen with a reviewed positive limit no higher than `maxTradeUSD`. Preparation/canonical locks still apply. |
| `PoolRegistry.disablePool(id,stopDeposits,stopOperations)` | Pool-specific new contributions / ordinary guarded operations; no token/price/venue reads on disable | Governance only; flags only clear. Not universal pause. Reopen with full validated config; parked LP still needs resume. |
| `AccessController.setPaused(true)` | Ordinary mint, contributions, rebalance/compound/buyback and moves/resume | Transfers, funded claims and royalty receipts continue. Governance may start/close collective holder exit while paused. Pause does not start it; unpause never reverses terminal lpExitStarted. |
| Canonical preparation | New economic work and normal protocol configuration | Existing claims/transfers/reveal/permitted drains; exact notice can be cancelled before freeze. Not a generic pause toggle. |
| Canonical freeze | Ownership and ordinary reward/accounting operations | Only handoff settlement/export/funding/abort path. Fully restore abort or complete one successor; no guardian unlock. |
| `Migration.invalidateParking(bucket)` | An unused parking authorization at its current nonce | No funds move. Collective exit has no cancel/recover/reopen path; failed individual payments stay backed for retry or owner fallback. |

There is no independent pause for every individual feature/asset payout. Do not invent one in an incident. Source: [module guards](../src/base/ZZZModule.sol), [controller](../src/ZZZAccessController.sol), [recovery matrix](CHANGE_AND_RECOVERY.md).

## Services and server recovery

The heartbeat now includes `configuration_sha256`, a hash of the exact loaded
configuration. `keeper.ops health` requires the same hash, not merely chain and
sender. Old/missing/malformed or mismatched artifacts return `configuration_mismatch`.
Deploy matching writer/checker together only through an authorized rollout and
require a fresh matching cycle after a reviewed config change. Never patch the
hash, edit/reset a journal or assume this digest authenticates the host/provider.
There is no in-process config reload: finalize config before constructing Keeper.


Use the reviewed Linux/Unix release and separate service users. The fresh policy2 sample observes every60seconds and harvests hourly; historical ten-minute/four-hour examples retain their own scope. Neither schedule guarantees execution. Change reviewed config for interval, thresholds, per-bucket overrides, minimum liquidity, gas/daily budgets, RPC providers and metadata scans; restart through the deployment's service manager after checking pending work. Do not guess a production unit name or reuse the isolated staging signer/config.

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
authorize eventual payments/claims. Review the exact chain, anchor, nine core
module pins for accounting4 (historical accounting3 uses eight), required helper
pins and admitted assets first. The schema6 release inventory separately observes
17helpers. Bind the separate fee policy to
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
| Current accounting-3 balances | Rewards inventory must actually start with native ETH. An NFT that never activated cannot have positive available LP/royalty entitlement. Optional unavailable currencies remain null. Activated parked/outbound NFTs retain eligible funded rewards. |
| Wallet read budget | Accounting3/4 checks pinned `weightOf(id)` and `nftStatus(id)` per NFT. This follow-up adds one custody read to profile3; profile4 strengthens its existing status read. Historical1/2 read shapes remain. Keep16-item chunks, finite request limits and complete same-block chunk verification. Requalify actual latency/budgets before rollout; no unbounded retry or limit relaxation. |
| Display totals | Ready to claim = funded LP plus royalty balances now. Earnings 24h/all time includes earlier claims and past owners; claims/conversions are not new income. Compound/buyback/gross receipts are not additional NFT claimable funds. |

Recover by correcting provider/history/configuration evidence and rerunning the
bounded read on a separate copy. Upgrade/rollback only matching API releases
under the existing service runbook when separately authorized; never reset chain
or journals. Genuine view outages may null only their metric; malformed Boolean,
ABI, or contradictory available/value data now rejects the request. See
[earnings operations](EARNINGS_HISTORY.md) and [167-method evidence](../reports/backend-remediation-20261026/VERIFICATION.md).
Production feeds/history capacity and service acceptance remain open.

In accounting4, native royalty eligibility cannot be delayed by an external
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
| Mint price/recipient, supply/rarity quotas, trait draw rules, 80/10/5/5, requested 5% royalty rate/weights | No ordinary post-seal setter. Requires separately reviewed architecture/replacement if changed; not a UI edit. |
| Randomness provider/lane/subscription/payment mode, canonical artwork base, module bindings, core strategy/adapter implementation | Fixed at or before sealing. Future-request confirmations/callback gas have their separate bounded setter; pending draws cannot be changed or rerolled. Range orientation and approved presets are supported policy, not a replacement algorithm. No proxy-upgrade or generic patch function. |
| Lower production activation below $100 or exceed the 10% hard execution-loss ceilings | No such configuration path; growth has its separate fixed $5 floor. Governance can change current limits within 0-10%; defaults are 2% / 1% / 3%. The separate $1 local test build is not production configuration. |
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
