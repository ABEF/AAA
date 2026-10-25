# PoPL operator manual

## Native website profile and service qualification - 2026-10-25

Use the [explicit native website profile](NATIVE_WEBSITE_PROFILE.md) for current
accounting2/pricing2/routing2/review1 deployments. Never run the old WETH manifest
against current code or reinterpret existing Anvil journals. The public build
still has null DEPLOYMENT and nonlocal sends remain disabled. A local source
update is not a static-server rollout or approval to enable signing.

Before service deployment, run the opt-in [RPC capability procedure](RPC_PREPARATION_QUALIFICATION.md)
with independently reviewed public genesis/runtime identifiers and private
endpoint configuration. A timeout is not proof of missing-block rejection. A
getter accepting withLog is not proof of event traces. Preserve failed reports;
do not turn an unavailable observation into a provider approval.

The current Vault is a pre-deployment private refactor with identical ABI/storage,
not an upgrade to an existing address. Rebuild and check normal bytecode gates
after every source change;313 bytes is still limited room. Update exact artifact
pins only in an independently reviewed deployment inventory. Current cap defaults
remain2/1/3%, immediate-governance maxima10%, gas separate. No permissions,
custody/reward rights, source-chain exit or recovery policy changed.

## Reviewed contributions and indexer incidents - 2026-10-25

Use [reviewed Entry policy](EXECUTION_LOSS_POLICY.md#review-time-policy-binding)
for new pricing-V2 deployments: require explicit version1 getters/configuration,
new exact selector, current runtime pins and complete simulation. A governed cap
above the encoded caller maximum rejects before funds move; prepare a new quote
instead of widening an old signed review. Other configuration is not locked by
that maximum. Old Anvil/website ABI and journals keep their original policy.

For missing/malformed/unstable indexer ancestry, follow [indexer recovery](INDEXER_RECOVERY.md).
Preserve the DB/WAL, cursor, anchors and event history. Switch only to a reviewed
configured endpoint and retry; never clear history to make an outage look current.
RPC redirects are refused, including same-host redirects: configure the actual
reviewed final endpoint explicitly. Normal bounded failover still applies.

Revealed NFT metadata now distinguishes fixed royalty trait weight from activation;
the `royalty_activated` flag is not proof every optional payment currency is ready.
Buyback's operating/max USD ceiling uses upper input bounds rounded upward;
disagreeing valid prices can require a smaller batch. Execution floors and gas
remain separate. Re-read/re-simulate after any policy/provider change.

## Liquidity placement and keeper policy - 2026-10-25

Use [idle and dust ownership](IDLE_AND_DUST.md) before any cleanup. Contributions
default to2% (98% marginal deployed LP), conversion1%, maintenance3%, gas separate.
The Vault makes at most two balancing passes using actual post-swap state; tiny
corrections are skipped. Retained idle still backs the same bucket. There is no
general clear/sweep or operator dust recipient.

Idle-only reinvestment uses the existing `Compounder.compound(bucket,minLP,deadline)`
with current prices, actual LP, captured maintenance budget and pool cooldown.
`Budget.lastCompound(bucket)` changes only on success. Configure keeper opt-in,
both actual currency thresholds and reviewed Budget pins using the specialist
[keeper/range guide](RANGE_POLICY_UPDATES.md). Stop scheduling and reconcile pending
hashes before changing services; do not reset journals or count principal as income.

### Explicit ZZZ-price orientation and two-range selection

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


## Budget feed services and label observations - 2026-10-25

Use the [pricing snapshot and cost boundary](../reports/price-reference-20261025/OBSERVATION.md)
as dated research only. Before choosing providers, record actual product terms,
subscription/update/adapter/RPC costs, payment authority and network gas. Standard
public push-feed getters need no separate per-read LINK transfer; that does not
make VRF, paid reporting or custom hosting free. Qualify the exact proxy product
and upstream administrators, not only its ticker or runtime hash.

Do not use a secondary proxy of the same upstream as independent confirmation,
nor the selected pool's spot as its own USD guard. Show observation time and feed
update time separately. Governed post-seal replacement uses the complete
setDualFeed admission procedure below and refreshed reviewed downstream policy;
it does not deploy new Oracle code or authorize a single-feed fallback.

## Price-read gas and optimized checkpoints - 2026-10-24

The [on-chain safety/cost follow-up](../reports/onchain-safety/REVIEW.md) changes
implementation, not operator permissions, limits or transaction arguments.
Qualify the exact release runtimes again before deployment. An already sealed
deployment cannot receive these code changes merely by changing its feed address.

Every price/asset-decimals/sequencer read must fit the fixed 500,000-gas call
ceiling and exact ABI length. Review real proxy/adapter behavior and worst-case
gas before admitting it. On failure, disable affected new work, retain saved
transactions, diagnose/replace the dependency through existing governance and
fully revalidate before reopening. Never bypass a failed source or increase an
execution cap automatically. The ceiling is a code bound, not a mutable setting.
Healthy uptime status transitions do not expire periodically; down/recovery
grace checks remain. Raw funded claims still need no USD price.

Strategy snapshots last only for one read-only planning call. Execution/final
contribution checks still re-read; checkpoint caching cannot be enabled across
transactions. Eligibility and NFT shares still change only through the existing
authorized lifecycle. No new server option, maintenance schedule, sweep or
custody authority is introduced. Local component gas savings are not actual
target-chain fee estimates; qualify real cold/max-state routes and feeds using
the unchanged gas/size gates in the [verification record](../reports/onchain-safety/VERIFICATION.md).

## Configure, stop and recover USD pricing - 2026-10-24

The [pricing-V2 guard](PRICE_SECURITY.md) requires two independently reviewed USD
sources per priced asset. `Oracle.setFeed` now explicitly reverts; its old
single-feed instructions are historical. Do not use one ETH/USD source plus one
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
funded claims need no USD feed; the explicitly approved paused raw custody exit
keeps its separate exact minima and no USD guarantee. Failed pools/tokens can
still prevent movement. See [preflight](PRODUCTION_PREFLIGHT.md) and
[raw recovery controls](GOVERNED_CUSTODY_HANDOFF.md).


## Current-version production preflight - 2026-10-24

Use the [schema-5 inventory runbook](PRODUCTION_PREFLIGHT.md) before presenting any
native/V4 deployment as ready. Fill approved public addresses/runtime pins and
policy first; collect one bounded canonical read snapshot separately; then run
the offline gate against the exact release commit. Unknown prices, routes,
authorities, VRF, services and audit evidence remain named blockers.

The observer cannot approve its own observations or prove route-map completeness
without creation-to-anchor history. Do not copy actual code into approved pins,
reuse a stale snapshot after configuration, or overwrite the original inventory.
On partial/mismatched reads, inspect the existing deployment and fix the cause;
no automatic reconfiguration, signing, retry transaction, reseal or reset occurs.
The public site and existing Anvil/journals are unaffected.


## Typed conversion and loss-limit operations - 2026-10-24

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


**Post-seal settings and real-funds rehearsals (2026-10-24):** [Configuration policy and cleanup boundaries](POST_SEAL_POLICY.md) distinguish existing setters from required pre-seal extensions. Use a separate mainnet rehearsal deployment; no reset/burn or general sweep exists. No public action is authorized by this design record.

**Selected pool (2026-10-24):** Robinhood Uniswap v4 native ETH/ZZZ `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`, static 1.002% LP fee, no hook. The observed protocol fee makes the combined fee about 1.101%. Hookless native admission and atomic `moveFunds` are the current candidate; external `exit` remains separately approved and paused. [Selection and limits](POOL_SELECTION.md). Production remains NOT APPROVED.

This is the management guide for the **current undeployed candidate**. It describes available controls, their effects and recovery boundaries; it does not approve a production deployment. Use the [central Todo](../TODO.md) for outstanding work and the [release record](RELEASE_CHECKLIST.md) for deployment approval. Production addresses, services and several migration capabilities remain unqualified.

## Native accounting V2 deployment boundary

The [native V2 candidate](../reports/native-eth-port/VERIFICATION.md) uses actual ETH
at currency `address(0)`. Read `Vault.ACCOUNTING_VERSION() == 2` and the handoff's
`SCHEMA() == keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2")`, then verify every
module/helper runtime and binding. Deploy a coherent new set; do not attach V2
helpers to the existing WETH-accounted local deployment or reset its journals.

- **Prices and input admission:** govern the reviewed two-source policy with
  `Oracle.setDualFeed(address(0),primary,secondary,maxDeviationBps,reviewHash)`
  for ETH with 18 decimals. Verify both sources and the full pricing-V2 policy;
  native activation policy uses
  `ActivationAssets.NATIVE_ASSET_CODE_HASH()`, a typed identity, not an ETH runtime
  hash. Enable it with `setAsset(address(0),true,sentinel,reviewHash)`; disabling
  new input never removes backing or accrued rewards. WETH is a separate ERC20.
- **Activation/growth:** `Entry.execute` with source zero carries exactly
  `amountIn` as native value; ERC20 input carries zero ETH and exact approval.
  Direct `Vault.activate/increase` also requires exactly the declared slot-0 ETH.
  Missing/extra value reverts; old prefunds cannot supply it. Approval never adds LP.
- **Fees and claims:** native fees receive the same 80/10/5/5 allocation and
  individual/equal-collective checkpoints as tokens. Current owners claim ETH
  directly; already converted credits remain separate earned balances. ZZZ still
  needs a qualified conversion route under the current cap (1% default, governance maximum 10%); gas is separate.
- **Pool moves:** `moveFunds` accepts identical actual currencies only, including
  another native ETH/ZZZ fee tier. ETH/WETH atomic conversion is unfinished and
  fails closed. Reviewed external custody completion remains a separate procedure.
- **Raw exit and return:** the existing pause/park/snapshot/approve/exit procedure
  now sends native ETH and ZZZ, without invoking WETH. It still depends on usable
  venue/token bindings. For `recover` or `completeLocal`, attach exactly the declared
  native amount as call value and approve only the ERC20 amount. Normal exit keeps
  its captured `minimumRetainedUSD(id)`; raw mode retains explicit raw minima
  and no USD guarantee.
- **Optional funding inbox:** `Fees.createRewardReceiver(nativeBucket,address(0))`
  creates a native inbox with one ETH protection slot; do not supply a wrapper.
- **Services and replacement:** API and keeper configurations explicitly select
  `accounting_version: 2`; keeper configuration requires the reviewed deployed
  runtime hash at `code_hashes.vault` and its actual `contracts.vault`. Review
  all other runtime bindings, the actual ETH feed and per-predecessor
  versions. Old journal files must not be reinterpreted as V2. Canonical funding
  transfers backing first, then sends a zero-value acknowledgment; never pay it
  twice. V1-to-V2 import is rejected pending a reviewed bridge between schemas.

The website's native V2 profile, full release inventory, real feeds/routes,
target-chain rehearsals and independent audit remain open. Public signing stays
Anvil-only and the public deployment configuration remains null.

**Keep this manual current.** Every change to an operator-facing function, permission, default, parameter, lifecycle, service or failure mode must update the affected procedure in the same change, or explicitly record why there is no operator impact. Update the task ledger and feature/evidence reference too. This is a required development/review step, not automatic synchronization. See [maintenance rules](TODO_WORKFLOW.md).

## Find the right procedure

Production minting is intended for OpenSea; the website Mint page is a demo.
Qualify the exact mint product, chain, contract integration and collection URL
before sealing, following [the mint venue procedure](OPENSEA_MINT.md).
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
| Accept/remove an activation token, or change its swap pool | [Activation assets and routes](#activation-assets-and-routes) |
| Stop minting independently | [Mint-only pause](#mint-and-metadata) |
| Stop new LP entering a pool, stop maintenance, or open another pool | [Pool admission and retirement](#pool-admission-and-retirement) |
| Stop everything possible, recover and restart safely | [Stop controls](#stop-controls) and [incident recovery](#incident-recovery) |
| Move existing LP, close it temporarily, or change chains | [Custody and LP migration](#custody-and-lp-migration) |
| Change prices, sequencer checks or wrapper policy | [Dependencies and pricing](#dependencies-and-pricing) |
| Collect fees, compound, burn, receive creator payments or royalties | [Revenue operations](#revenue-operations) |
| Resolve pending artwork reveals or replace all contracts | [Mint and metadata](#mint-and-metadata), [whole-collection replacement](#whole-collection-replacement) |
| Change managers/keys, replace a server, update software | [Authorities](#authorities), [services](#services-and-server-recovery) |
| Use a browser wallet locally, recover pending transactions or inspect exact approvals | [Browser-wallet signing and recovery](BROWSER_WALLET.md) |
| Configure reviewed API holdings; rehearse wallet sends on local Anvil only | [Reviewed website API profile](DEPLOYMENT_WEBSITE.md) |
| Know what cannot be changed after sealing | [Fixed boundaries](#fixed-boundaries) |

## Before every management operation

1. **Identify the deployment:** chain ID, controller, canonical lifecycle, sealed module addresses and code hashes from the reviewed [inventory](DEPLOYMENT_ADDRESSES.md). Read `canonicalState()`, `preparationActive()` and `paused()`. An old retired deployment is not a valid target merely because its explorer page still exists.
2. **Identify the object:** PoPL NFT token ID, mint ordinal, bucket ID, pool ID and physical Uniswap position ID are different. Read `Vault.nftBucket(tokenId)`, `group(bucketId)`, `bucketTotalShares(bucketId)` and the registry. The keeper operates on shared buckets, not 1,000 independent NFTs.
3. **Read before changing:** preserve the complete current struct, asset units/decimals, balances, shares, current parameters and pending work. Use a confirmed block and record its hash. Do not copy example addresses or raw-token thresholds into production.
4. **Prepare exact calldata with the ABI for that release.** Simulate from the actual authorized caller, including value, bounds and dependent operations. Use fresh deadlines and meaningful minimum output/liquidity. If state/configuration changes, simulate again. Simulation does not guarantee later execution or prevent MEV.
5. **Execute through the proper authority**, wait for the configured confirmations/finality, then check receipts, events, getters and economic balances. A submitted hash or successful multisig proposal is not a successful target operation.
6. **Update off-chain configuration and the operation record:** runtime pins, asset/route inventories, API/indexer/keeper configuration, frontend supported actions, review evidence and rollback plan. Never put keys, RPC secrets or runtime state in Git. Record failures and failed-transaction gas too.

### How governance calls work

After sealing, a governed module expects the **AccessController**, not your personal address or a Safe owner, as `msg.sender`. The authorized governance multisig registers the exact operation using `schedule(target,value,data,predecessor,salt,0)` (or `scheduleBatch(...,0)`); an authorized executor executes the unchanged operation. Registration and execution can occur in the same block; a suitably configured multisig can batch them. **There is no governance waiting period.** An unfinished predecessor, failed target check or wrong role still blocks execution. An open executor can execute approved calldata only.

Use `hashOperation`/`hashOperationBatch` and operation status to verify the exact target, value, calldata, predecessor and salt. Cancel an unexecuted operation with the controller's `cancel(operationId)` using its canceller role; changing parameters requires a new operation. Never blindly retry a successfully executed operation. See [governance semantics](GOVERNANCE.md) and [controller source](../src/ZZZAccessController.sol).

## Authorities

| Authority | Management action | Rotation/recovery |
| --- | --- | --- |
| Governance proposer/executor/canceller/admin roles | Governed configuration, custody changes and replacement admission | Inspect inherited role administrators and current `hasRole` values. Use authorized `grantRole`/`revokeRole` operations; verify the replacement before removing the last usable authority. Changing owners/threshold of the same Safe changes its governance without changing the controller address. |
| Guardian | Direct `AccessController.setPaused(true)` | Governance uses `setGuardian(address,bool)`. A guardian cannot unpause, choose a new pool, withdraw LP or repair lost governance. |
| Keeper | Eligible maintenance and approved migration execution | Governance uses `setKeeper(address,bool)`. Isolate/revoke a compromised signer, reconcile its pending transactions, then qualify a new signer and state. No salary, gas reimbursement or bounty is automatic. |
| Bootstrap | Initial bindings and sealing | `bind` and `seal` only before sealing; bootstrap is erased. Do not retain deployment keys as a supposed recovery backdoor. |
| Mint recipient | Receives successful 0.05 ETH mints | Immutable Vault constructor address; receiving money grants no management authority. No post-seal setter. |

Roles can technically share an address, but this combines their compromise and availability risks. Immediate governance can approve unsafe dependencies or harmful replacement code; role separation and independent transaction review are operational defenses, not an on-chain delay. If every required governance authority/key is lost, there is no hidden admin recovery. Preserve reviewed multisig recovery arrangements before launch.

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

1. Read `PoolRegistry.get(poolId)` and copy the **entire** `PoolConfig`, including its real venue key. Change only intended settings. Use `configureNative(config)` for the selected native ETH/ZZZ pool and `configure(config)` for supported hookless ERC20 pools. V2 accounting retains the real zero ETH currency; do not substitute WETH or change slot ordering.
2. Check the dependent bounds below, oracle freshness, current price/spot difference, target ticks, actual swap costs and expected gas. Review narrower-range out-of-range exposure and turnover. Simulate the new configuration and maintenance on a fork at the same state before approval.
3. Governance executes the configuration. This **does not immediately close/reopen LP**. Inspect `Strategy.rangeUpdatePending(bucketId)` and `needsRebalance(bucketId)`.
4. The authorized keeper submits `Vault.rebalance(bucketId,minimumLiquidity,deadline)` when cooldown and guards permit. A width mismatch can trigger it even at a flat price. Polling every ten minutes is only an example; it is not a guaranteed rebalance deadline.
5. Verify the new physical LP ID/ticks/center, retained value, attributed idle, unchanged NFT shares and continued claims. A successful replacement clears the width mismatch. A revert preserves the old position and leaves the desired change pending.

Before execution, restoring the old configuration may clear the width mismatch; the independent price trigger can still permit a rebalance. After execution, going back requires another valid configuration and rebalance, with fresh costs/cooldown. Stop/reconcile in-flight keeper work around a policy change: its transaction is not bound to a historical configuration hash. See [range application](RANGE_POLICY_UPDATES.md).

### Editable pool parameters and coupled limits

| Field | Current contract boundary | Practical meaning |
| --- | --- | --- |
| `rangeBps` | 100-5000, also greater than trigger and spot tolerance | Because `triggerBps >= 100` and must be smaller, 100 itself cannot form a valid complete configuration. Wider/narrower ranges still require representable ticks. |
| `triggerBps` | At least 100 and less than range | Price movement from recorded center which can trigger upkeep. |
| `minRebalanceInterval` | 600 seconds-7 days | Minimum time between rebalances; a safety cooldown, not a governance delay. |
| `maxSpotDeviationBps` | 1-500 and less than range | Spot/reference discrepancy permitted by guarded execution. Do not widen it simply to accept a manipulated market. |
| `maxSlippageBps` | 1-200; pool fee must be strictly below it in equivalent units | Selected LP fee 10020 pips therefore requires at least 101 bps; actual protocol fee, impact and complete quote must also pass execution checks. This independent venue guard and the current governed contribution-loss ceiling must both pass. |
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

An **activation route** converts a user's contribution into the LP pair. It is distinct from moving the Vault's already-held LP to another pool. Changing a USDG conversion pool does not migrate the attached LP or change its owners.

### Add or re-enable an input token

1. Review its exact chain/address, runtime and proxy authorities, decimals, transfers, liquidity, fees and price source. A symbol such as USDC does not identify an asset. Fee-on-transfer/rebasing/blacklisting or malicious callbacks can make an asset incompatible; permission to admit is not proof of compatibility.
2. Governance configures the reviewed two-source `Oracle.setDualFeed(token,primary,secondary,maxDeviationBps,reviewHash)`. Independently verify both raw rounds, policy identity, `priceBounds(token)`, decimals and source/proxy independence under [pricing operations](#configure-stop-and-recover-usd-pricing---2026-10-24). Admit the source with `ActivationAssets.setAsset(token,true,expectedCodeHash,reviewHash)` at the registry's immutable `activationAssets()` child.
3. If conversion is needed, governance calls `ActivationEntry.addRoute(RoutePolicy)`. The legacy supported path is typed **single-hop V3** into one accounting-pair asset, with pinned source/output/router/factory/pool code and fee; direct ERC20/native input is separate. Typed hookless v4 policies are also implemented through `addV4Route(Policy)`; follow [typed route setup](TYPED_V4_ROUTES.md), including explicit version/profile pins. It is not a general multi-hop router or arbitrary external executor.
4. Verify route ID, enabled status and exact factory/pool/token bindings; update reviewed backend route/feed pins and available UI choices. Simulate the complete input-to-LP operation against the current captured contribution-loss limit (2% by default), stronger route/venue minima and separate gas. Qualify actual execution before enabling real users.

Native V2 uses explicitly admitted ETH at `address(0)`, with an independent feed and exact call value. It is never an ERC20 approval target. Accepting a new **input** does not automatically admit an LP or royalty payout currency. Actual production ETH/ZZZ/USDG/USDC routes and services remain subject to [qualification](ACTIVATION_PREPARATION.md).

### Replace a swap route when market liquidity moves

Read/review the new route, append it with `addRoute`, qualify it, switch the backend's selected route, and use `setRouteEnabled(oldId,false)` to stop the old route. Route contents/identities are immutable; do not overwrite one in a manifest under the old hash. There is no time delay. Concurrent user quotes may revert after disablement and must be rebuilt. Already mined operations cannot be undone.

To stop an input immediately, use `ActivationAssets.setAsset(token,false,expectedCodeHash,reviewHash)` with the required nonzero token/review hash, and disable affected Entry routes. Disable paths deliberately avoid dependency calls needed for enabling; they can help when a token/feed is broken. Previously attached LP, shares and claims are not erased. Re-enabling requires valid current token/feed/code checks and new quotes. Pool configuration cannot silently re-enable an explicitly disabled source. See [asset controls](ACTIVATION_ASSETS.md), [Entry](ACTIVATION_ENTRY.md) and [routing](ACTIVATION_ROUTING.md).

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
   `Migration.movePool(bucket,target,minLiquidity,deadline)`, then enable target
   deposits. The existing move guard requires target operations, not deposits.
   An exact `scheduleBatch(...,0)` / `executeBatch(...)` can include this ordered
   sequence; failure rolls it all back. Enabling first lets another activation
   occupy the destination bucket and block the intended move. If intentionally
   stopping first in a separate transaction, a failed enable leaves deposits
   stopped; retry only after resolving validation failures.
3. Verify `ContributionPoolChanged`, the getter, old flag=false and new flag=true
   at a confirmed block. Update the API's reviewed target/runtime pins and UI;
   discard old quotes and simulate fresh ones. Cancel obsolete governance calls.
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

Use the [governed custody runbook](GOVERNED_CUSTODY_HANDOFF.md), which replaces
the former LP v3 bridge and pair-executor procedures. The whole-collection
ownership/reward handoff below is a separate retained feature.

| Need | Exact control and verification |
| --- | --- |
| Normal exit, all principal to ZZZ | Configure reviewed `Migration.configureZZZ`; read Budget `maintenanceLossBps()` as `L`. For reviewed pre-parking value `V`, preserve `F = V - floor(V * L / 10000)` and raw ZZZ minimum `ceil(F * 10**decimals / lowerZZZPrice)`. Pause and cancel any unsent plan before reviewed `park(ParkingRequest)`. Verify parked principal, read its stable `sourceSnapshot`, approve the exact `rawExit=false` request and verify `minimumRetainedUSD(id)`. Call `exit(id)` while paused before its ten-minute deadline. Use the greater of the preserved pre-parking raw minimum and the parked approval's required minimum; never loosen it. Parking has separate raw close minima; gas is separate. |
| Unsafe or missing swap route | Cancel an unsent normal request before parking/reapproval. Use the same reviewed parking and stable-snapshot sequence, then separately approve `rawExit=true` with exact outgoing raw minima. Both attributed assets are sent without a swap. This mode deliberately has no USD-loss guarantee and never activates automatically. |
| Failed close/swap/transfer | Inspect the reverted receipt: that transaction's custody, balances, epoch and send changes roll back. Separately confirmed parking remains parked. Fix the cause and prepare a fresh approved snapshot if it changed. Never repeat a successful send. |
| New local pool/token | Approve ordered destination currencies and minima. Recipient performs any issuer exchange externally. If the plan initially selected local holding without a pool, admit/reserve a target for the same bucket and call the one-time `bindLocalDestination(id,pool,min0,min1,reviewHash)`. It preserves the original loss budget and departure. `completeLocal` must actually fund/mint the target LP and preserve shares. Then deliberately switch the sole contribution pool/input routes. |
| New chain through your custodian | Approve source-chain custody only: `destinationChain=block.chainid`, `destinationPool=0`, `destinationCustody=recipient`, `verifier=0`, `verifierCodeHash=0`. The recipient performs any bridge/token migration externally. No on-protocol bridge is required; source principal remains outstanding/unavailable until a supported funded return/completion. This does not relocate NFTs/reward ledgers or promise remote accrual. See the runbook for exact request/approval fields. |
| Recover principal | In the current source-chain custody workflow, `recover(id,deadline,proof)` returns every actual sent asset and restores parked custody; use the local proof form from the runbook. No timeout, partial funding, balance write-off or resend. Optional direct remote-proof paths remain disabled/unqualified. |
| Restart recovered/parked LP | Revalidate prices, venue, policy and current snapshot. Unpause and govern `Migration.resume(bucket,pool,minLP,deadline)`; verify actual active LP and unchanged shares. Ordinary supported same-pair `movePool` remains in this one module. |
| Park without sending | Pause, verify `activePlan(bucket)=0`, then use exact `Migration.park(ParkingRequest)` with current pool/LP/shares/recorded contribution value/custody epoch/parking nonce/accounting currencies and raw close minima. At least one minimum must be positive; deadline is at most ten minutes. It omits source USD/inbox sync but cannot bypass an unusable venue/token or changed core/runtime binding. Native V2 parking does not call WETH or its policy. Invalidate unused parking authorization with `invalidateParking`. |
| Move royalty currencies as well | Separate `RoyaltyRewards.exitCustody(asset,recipient,expectedBalance,nonce,recipientCodeHash,reviewHash)` while paused. Per-NFT entitlements remain; that currency's claims/valuation wait for exact full `returnCustody(asset,id)`. Native ETH is asset zero. Other currencies, LP principal and royalty quarantine must not be merged. |

Record every plan/nonce, approval, exact recipient, source/destination bindings,
actual amounts/receipts and backing state. External recipients can lose funds;
governance accepts that custody trust. No source function can force their return.
Do not declare a migration complete from a transfer hash alone. Whole-collection
capture is blocked until principal and royalty external custody are resolved.

An active `sourceSnapshot` includes live LP token quantities. PoPL pause does not
stop external Uniswap swaps, so separate active approval/exit transactions can
become stale. Prefer pause, reviewed parking before any custody approval, then
the stable parked snapshot. Cancel a stale approved plan before parking; never
weaken the snapshot check. The supported direct active exit needs a reviewed
atomic controller approval/exit batch to avoid the between-transaction race;
it can still revert if the snapshot changed before inclusion. A failed parked
exit leaves the earlier parking intact. The contract's parked approval floor
starts at parked value; it does not autonomously cache the pre-parking budget.
Preserving the original rounded-up minimum across both transactions is therefore
required for the operator's reviewed pre-parking close-plus-conversion budget.
Read the captured plan floor; a later governance cap increase cannot relax it.
Follow the
[full budget and recovery procedure](GOVERNED_CUSTODY_HANDOFF.md#ordinary-migration-exit-all-principal-into-zzz).


## Dependencies and pricing

| Change/problem | Control and checks | Fallback/limit |
| --- | --- | --- |
| USD source pair / freshness / disagreement | Governance `Oracle.setDualFeed(token,primary,secondary,maxDeviationBps,reviewHash)`; verify two independent reviewed sources, exact runtimes/decimals, valid current rounds, append-only identity and `priceBounds` fingerprint | Both sources are mandatory. No single-source, stale/spot or $1 fallback. Disable affected work and follow the [pricing recovery procedure](#configure-stop-and-recover-usd-pricing---2026-10-24); raw funded claims and explicitly approved raw custody retain separate rules. |
| Sequencer feed replacement | `setSequencerFeed(source,expectedCodeHash,reviewHash)` after reviewing the new nonzero source | Replacement does not require the failed old feed to work. Existing recovery grace remains. No setter removes the protection by setting zero. |
| Optional/legacy WETH review record | Retained `PoolRegistry.approveWrapperPolicy(policy)`, then `activateWrapperPolicy(id)` after code/getter/authority review | Same fixed WETH address only; native V2 admission, parking and exit do not consult this record. It neither repairs a hostile proxy nor changes a converter's independent immutable wrapper/route bindings. Review an explicitly wrapped operation separately. |
| Pool manager, token, router or optional historical hook change | Compare actual code/config/authorities to the deployment pins; stop affected work | Some source/route policies can be replaced, but immutable venue bindings cannot be patched by changing a manifest. New unsupported implementations require compatible reviewed replacement work. |
| RPC/trace/archive outage | Use chain-checked reviewed endpoints with required hash-pinned reads and trace/receipt semantics | Never fall back to latest/unconfirmed state or a wrong chain. Serve unavailable status; retain indexes/state. |

Changing off-chain code hashes to whatever is currently deployed is not a review. Verify proxy implementation and external control as well as runtime bytecode. Governance configuration during canonical preparation is blocked; cancel preparation only if reopening is intended, not to bypass a migration freeze.

## Revenue operations

Revenue is receipt-based, not a per-minute promise. **80/10/5/5 is fixed**: individual LP shares / equal activated-NFT collective membership / compound reserve / buyback reserve. Rarity only weights the separate royalty ledger at x1/x2/x3. Source: [economics](ECONOMICS.md).

| Operation | Entry point / owner of action | Verify and recover |
| --- | --- | --- |
| Receive optional/historical creator revenue | If separately agreed, governance creates the bucket's immutable inbox via `Fees.createRewardReceiver(bucketId,wrapper)`; give the creator the verified `rewardReceiver(bucketId)` | Not required by the selected hookless pool. For native V2 use wrapper `address(0)`; qualify payout assets, percentage basis, frequency and payer agreement. Receiver is append-only, not an operator wallet or the mint recipient. Unsupported/donated tokens do not automatically become rewards. |
| Process optional/historical creator payment | Permissionless `Fees.syncExternal(bucketId)` through its bound inbox, if one exists | Compare actual received funds, allocated ledgers and reserves. Missing optional creator payments cannot be fixed by calling sync more often. No automatic debit of creator funds. |
| Harvest selected pool LP fees | Permissionless `Vault.collectFees(bucketId,deadline)` while live and locally active | Verify actual venue fees collected and funded 80/10/5/5 allocation. The selected hookless pool has a static 1.002% LP fee; PoPL earns its eligible position's share, not Uniswap's separate protocol fee. No creator payment is required for this LP income. |
| Compound | Keeper `Compounder.compound(bucketId,minimumLiquidity,deadline)` | Uses classified reserve, actual pool and guards; funds never pass through keeper. Poll/threshold changes are off-chain; insufficient funds or unsafe execution waits/reverts. |
| Buy back and burn | Keeper `Buyback.execute(token,amount,poolId,deadline)` | Check reserve, oracle value ≤ current `operatingTradeUSD` ≤ immutable `maxTradeUSD`, swap minima, actual ZZZ acquired and total-supply reduction. Governance tunes the operating ceiling with `setOperatingTradeUSD`; zero stops buys. Governance can update the reviewed target with `Buyback.setZZZ(token,codeHash,reviewHash)` after new-token/feed/burn qualification; coordinate with `Migration.configureZZZ` and current pools/routes. |
| Admit LP payout asset | Governance `Rewards.addAsset(token)` | Permanent bounded history, maximum 32; do not fill slots with speculative assets. Admission is distinct from input routing. |
| Receive marketplace royalties | `NFT.royaltyInfo(tokenId,salePrice)` returns the NFT's royalty receiver and requested 5% | Configure marketplaces with the **returned contract receiver**, never a manager wallet. ERC2981 is a request, not universal enforcement on every marketplace. |
| Admit royalty currency | Governance `NFT.addRoyaltyAsset(token)` | Initial scope is native ETH plus the independently verified Robinhood WETH wrapper; stablecoin conversion depends on marketplace qualification. Admission does not restrict sales or convert payouts. Separate bounded ledger (17 total including native); no arbitrary removal/sweep. Pre-admission/no-eligible-holder funds stay quarantined. |
| Synchronize/claim royalties | Permissionless `RoyaltyRewards.sync(asset)`/`syncAll`; actual owner calls ledger `claim` or bounded ClaimRouter | Direct royalty claim synchronizes pending admitted receipts. LP claim does not harvest new venue fees. Use current owner and actual funded amounts. |

A holder can claim both streams in a **1-32 operation atomic ClaimRouter batch**, or claim individually. One failed operation reverts the whole batch; simulate and split by asset/NFT if needed. No operator can choose a different beneficiary or claim just because it holds ERC721 approval. All unclaimed rights follow the current NFT owner; already paid funds do not travel with it. An escrow that owns the NFT is the contract-level holder. Lifetime claimed display requires complete confirmed index history, including predecessors after replacement.

Pause generally preserves claims and transfers while canonical state is operating. A frozen/retired deployment has different rules; follow lifecycle status rather than presenting a failing claim button. Failed payout tokens, blacklists or recipient callbacks may still block their claims. There is no generic admin seizure/sweep/rewrite to clear a liability. Keep actual funded balances distinct from unharvested fees, proposed creator invoices and UI estimates.

Stop scheduled compounding/buybacks using reviewed keeper configuration or by stopping/revoking the keeper. Accumulated reserves remain classified on-chain; no automatic transfer to the operator is allowed. Change creator commercial terms off-chain and reconcile payments, while royalty-only conversion uses the separately bound guarded converter; LP payouts and the fixed 80/10/5/5 allocation are unchanged. See [external revenue](EXTERNAL_REWARDS.md), [royalty/claim behavior](CLAIM_ROUTER.md) and [measurement proposals](REVENUE_SHARE.md).

### Tune or stop buyback trading

Read `Buyback.maxTradeUSD()` (immutable hard ceiling) and `operatingTradeUSD()`
(current limit), both USD18. The deployment default is the hard ceiling. Through
the existing immediate governance controller, call
`Buyback.setOperatingTradeUSD(limit)`, with `0 <= limit <= maxTradeUSD`.
Confirm `OperatingTradeLimitChanged(previous,current)` and the getter. Zero stops
new execution without querying the oracle or releasing reserves; it does not stop
LP maintenance, claims or royalty processing, and does not move accumulated funds.
Reopen by selecting a positive reviewed limit within the hard ceiling.
This is a per-trade USD limit, not a token quantity or daily/cumulative budget.
Current pricingV2 checks the upper admitted input price, rounded upward at token
precision. Reduce the raw task amount if disagreement makes it exceed the ceiling;
never switch to the lower mark just to make a batch pass.
Current pricingV2 checks the upper admitted input price, rounded upward at token
precision. Reduce the raw task amount if disagreement makes it exceed the ceiling;
never switch to the lower mark just to make a batch pass.
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

### Coordinate the creator agreement

Use [Creator tasks / ZZZ team](../TODO.md#creator-tasks--zzz-team) as the meeting agenda and decision record. For each answer, record its date, authorized contact, precise terms or public addresses, effective period and supporting evidence. Keep unresolved answers open. Request public identifiers and proof of control where relevant; never request a signing key.

Commercial agreement alone performs no contract call. Before accepting funding, independently verify the current canonical per-bucket receiver, admitted pair/wrapper and payer instructions using [external funding](EXTERNAL_REWARDS.md). Explain processing-time allocation and keep the marketplace royalty receiver separate. A proposed invoice or missing payment must not become a funded claim.

Changes to the agreement require reconciliation of old/new periods and verified payment destinations. Stop an unqualified new configuration, retain existing funded liabilities and use the applicable pool/asset/incident procedure; do not sweep or redirect a fixed receiver. Reopen only after the changed dependency and payment flow are reviewed. This coordination procedure adds no authority, setter, timelock or automatic payout.

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
`NFT.setRandomnessRequestSettings(confirmations,gasLimit)` through the existing
controller, before or after seal. Contract bounds are 3-200 confirmations and
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

For a provider outage, governance calls `NFT.setMintPaused(true)` through the controller, with no waiting period. Verify `NFT.mintPaused()` and `MintPauseChanged(true)`. This blocks new NFT mint/randomness requests, including direct Vault callers; the complete transaction reverts without spending the mint payment. Pending original fulfillment and ordered finalization continue. Existing revealed NFTs can still activate/top up, transfer, claim and undergo LP maintenance when their independent guards permit. Pausing during the NFT receiver callback also rolls back that mint atomically.

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
2. Resolve all principal and royalty external custody before announcing preparation. If preparation has already started while principal remains sent, cancel that exact notice before funded principal recovery/completion; a failed freeze does not resolve custody. Prepare the destination as an inert importer with `CanonicalHandoff.prepareImport(sourceController)` **before its seal**; qualify its dependencies/randomness and bind it to this source. Governance calls source `AccessController.startPreparation(PreparationNotice)` naming the reviewed sealed importer. Preparation stops new mint/activation/maintenance/config work while reveal, transfers, claims and permitted drains remain possible.
3. Finish existing provider responses and ordered `finalizeTraits` calls; confirm `unfinished_draws=0`. This is the selected simple policy: reliable funded provider plus draining before replacement. Do not remove the fully-revealed check if a request is stuck. Cancel the exact notice via `cancelPreparation(noticeHash)` if postponing, then restore ordinary controls deliberately.
4. Drain/park custody and resolve plans. Governance `freeze()` stops ownership/accounting before capture. Complete six ordered `settle(slot)` domains; relay all `exportRows`/`importRows` batches of at most eight, `completeImport()`, then exact classified `fund(slot,index)` legs. Resume interrupted progress from on-chain cursors/roots, never from an assumed last successful terminal command.
5. Verify every root, owner, trait, share, liability, reserve and exact backing. Governance `commit()` atomically retires the source and activates one successor. Finality remains required before service/marketplace cutover. Update canonical address/runtime and complete predecessor-history configuration, payout routing and marketplace collection records; old ERC721 approvals are not imported.
6. Before commit, `abort()` cancels the importer; return every funded leg via `returnFunds`, then `finishAbort()` only after full restoration. This is not immediate unlock. After successful commit the source cannot be revived by unpausing or cancelling preparation. Late creator/royalty receipts forward one successor at a time through the supported forwarding functions.

A successful same-chain handoff does not qualify cross-chain finality, transport or post-halt recovery. Do not promise these are solved by external principal custody. The retired v3 principal bridge stack is not bound in new deployments. Resolve outstanding principal and royalty custody before whole-collection capture; imported local buckets retain the reviewed custody controls. Track the remaining design in the [canonical recovery task](../TODO.md#task-security-chain-recovery).

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
| `AccessController.setPaused(true)` | Live mint, contributions, ordinary rebalance/compound/buyback, atomic pool moves/resume and local LP completion | Operating-state transfers/claims and supported incoming returns remain. Governance-approved `Migration.park`, normal or raw `Migration.exit`, and `RoyaltyRewards.exitCustody` deliberately remain possible while paused under their own exact guards. Pause does not revoke governance custody authority or trigger raw fallback. Only governance unpauses; preparation/canonical locks remain. |
| Canonical preparation | New economic work and normal protocol configuration | Existing claims/transfers/reveal/permitted drains; exact notice can be cancelled before freeze. Not a generic pause toggle. |
| Canonical freeze | Ownership and ordinary reward/accounting operations | Only handoff settlement/export/funding/abort path. Fully restore abort or complete one successor; no guardian unlock. |
| `Migration.cancel(id)` / `Migration.invalidateParking(bucket)` | That approved but unsent custody plan / unused parking authorization at its current nonce | Neither moves funds or erases history. A sent plan cannot be cancelled: use actual full `recover` or qualified `completeLocal`; remote recovery needs the pinned closure proof. The retired bridge stack has no active outbound switch. |

There is no independent pause for every individual feature/asset payout. Do not invent one in an incident. Source: [module guards](../src/base/ZZZModule.sol), [controller](../src/ZZZAccessController.sol), [recovery matrix](CHANGE_AND_RECOVERY.md).

## Services and server recovery

Use the reviewed Linux/Unix release and separate service users. The keeper's sample ten-minute poll and four-hour harvest schedule are not guarantees. Change reviewed config for interval, thresholds, per-bucket overrides, minimum liquidity, gas/daily budgets, RPC providers and metadata scans; restart through the deployment's service manager after checking pending work. Do not guess a production unit name or reuse the isolated staging signer/config.

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
| Suspected governance compromise | Guardian pause, secure multisig/signers, cancel unauthorized pending operations where authorized | Pause alone cannot defeat malicious governance, which can unpause/reconfigure immediately. Recover role control through legitimate admins and independent review; no guaranteed rescue. |
| Oracle stale/depegged/wrong or sequencer down | Stop affected contribution/maintenance; preserve claims; consider parking if exact close can succeed | Reviewed new feed/policy, healthy rounds/grace and fresh full simulations; never blind unpause. |
| Out of range | Warn that conventional swap fees may be absent; show observed eligibility/next-check telemetry only if real | Eligible keeper rebalance with guards. Wide range/ten-minute polling cannot guarantee always in range; no fabricated ETA. |
| Repeated slippage/loss/minimum failure | Retain old position; inspect actual conversion, venue costs, liquidity and oracle | Inspect route/timing and accounting first. Governance may deliberately review loss limits within the 10% hard bound; exact approved custody/caller minima remain. A higher limit authorizes more loss and does not repair a failed dependency. |
| Gas spike/low keeper funds/daily budget reached | Stop new submissions; continue receipt reconciliation/alerts | Refill reviewed signer or revise operating budget after analysis; gas is not taken from arbitrary holder balances. |
| Unknown broadcast/nonce drift/reorg | Stop new signing, retain exact intent/hash and canonical anchors | Reconcile confirmed/pending transactions through recovery path; no blind resend or nonce reset. |
| Token blacklist/pause, optional wrapper upgrade or venue unusable | Stop the affected exposure, preserve ledger, review the actual dependency and exact exit | Policy update only where implemented and safe; venue/token/runtime failure can block parking/claim/abort. A wrapper failure affects an explicitly wrapped operation, not native V2 custody. No blanket rescue function. |
| Creator does not pay / royalties missing | Compare payer agreement, receiver and actual transfers | Process real receipts, resolve external payments; no invented accrual. Keep separate from API history outages. |
| VRF unfulfilled / ordered reveals blocked | Verify subscription/provider/request; stop new minting if needed | Use the mint-only governance pause, then original authenticated fulfillment and ordered finalize. Resume deliberately after service checks. No reroll; postpone whole-collection replacement if unresolved. |
| Server/disk/backup failure | Stop unsafe signing; alert off-host, preserve damaged evidence | Restore/reconcile state, permissions and storage; qualify health before new work. |
| External custodian/bridge fails or original chain halts | Stop new exposure, retain approvals/receipts/backing and provider evidence | Custodian handles external recovery; the source cannot force a return. No integrated bridge is required or promised; no post-halt canonical ownership recovery exists. |
| Bad UI/API release | Roll back the service to a compatible verified build, disable affected UI actions | Verify code/ABI/config/chain/history compatibility before reopening. This does not roll back mined transactions or sealed contracts. |

For contract reverts, decode using the exact release ABI. `Unauthorized` means inspect caller/controller/roles, `Preparing` or `CanonicalLocked` means respect lifecycle, `InvalidConfiguration` may mean invalid bounds or pins, `InvalidPrice` means inspect feed/round/sequencer state, `Slippage` means execution bounds failed, and `Expired` means prepare fresh calldata. A retry is appropriate only after identifying the cause and simulating current state. Save sanitized errors and operation identity; do not log credentials or private signer output.

### Restart checklist for an actual incident

Record the cause, affected block/time/object, containment and exact state; verify recovered authority and dependencies; reconcile every in-flight transaction and classified balance; resimulate fresh intended work; restore the narrowest controls in order; execute a monitored bounded operation; verify finalized receipts, user claims and off-host health. Only then reopen normal UI/keeper work. Do not treat a green process status as economic/accounting recovery. Update the incident evidence, task ledger and this procedure if the incident revealed a missing case.

### Unsigned mint and claim service

**Authority:** the service operator enables an unhosted read-only adapter; no
governance permission or private key is needed. Wallet signatures and contracts
authorize eventual payments/claims. Review the exact chain, anchor, eight core
runtime/helper pins and admitted assets first. Bind the separate fee policy to
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

## Disposable local testing

Use the [local browser stack procedure](LOCAL_TEST_STACK.md) for Anvil-only
mint/activation/top-up/fees/royalties/transfer/claim rehearsals. The launcher owns
its local chain and disposable accounts; no production key or public RPC is used.
It simulates each typed transaction and records receipts and gas. Test venues,
prices, randomness and time advancement are explicit. Stop with Ctrl+C or the
authenticated local stop endpoint; restart creates a new isolated deployment and
indexer. Preserve receipts, inspect partial approvals before retrying and discard
old session/configuration data. Lost responses recover with Refresh and the same
operation ID. Do not bypass an uncertain-submission stop: inspect operations and
submission/receipt records, then restart the disposable chain. Requests have
strict input bounds, no queued concurrent mutations, revision checks and a
256-operation session ceiling. This does not install or qualify a production keeper.

The [existing website mode](LOCAL_WEBSITE.md) runs at `/app/` on this same origin.
Choose a local account, review exact approval and Entry separately, and inspect
current LP/earnings/claims after confirmation. The typed `/prepare` endpoint has
32 outstanding drafts and a 60-second expiry; `/action` executes the bound draft
with fresh ownership/simulation/gas checks. Claims batch at most ten NFTs and 32
currency operations per confirmation. Cancel sends nothing; approval may remain
if the later contribution is cancelled. Use Refresh to recover the same pending
operation after a lost response. New sessions clear the old intent without
resubmission. Missing prices remain unavailable, and no demo balance replaces a
failed read. The operator's root panel still funds/rebalances the fixture. Stop,
restart and evidence retention follow the same procedure above. No new authority,
production endpoint or contract configuration is introduced.

For local UI verification, a revealed dormant NFT retains its rarity multiplier
(Commun ×1, Rare ×2, Legendary ×3) in gray. Its effective royalty accounting
weight remains zero until activation. Unrevealed NFTs have no assumed multiplier.
This label correction requires no operator call, service restart or contract update.
Dormant detail views omit claims; active views retain the existing balance and
confirmed-state guards. Activation and transfer controls are unchanged.

Local wallet selection now comes from `GET /session` before the slow portfolio
read and persists through reloads in session storage, bound to that deployment.
After a launcher restart, choose the wallet again. Updating the session endpoint
requires restarting this disposable service using the procedure above; preserve
its external receipts first. A restart creates a new fixture, not a restored
persistent deployment. The public server and paused monitor are unaffected.

Refresh keeps labeled last-confirmed artwork, masks stale amounts and disables
financial actions. Dormant NFTs omit reward/history sections; active cards expose
Claim and Grow attached LP separately. Only confirmed market-value evolution
changes animate, and reduced-motion users get the same state without animation.
If a transaction confirms but reading fails, refresh balances; do not resubmit.
Busy state reads retry up to 13 attempts inside a 90-second request deadline;
writes never automatically retry as new intent. Persistent busy/error states
require inspecting the local operation/error logs. Interrupted HTTP readers no
longer trigger a second error response. These are local UI/service procedures;
no new contract permission, economic parameter or production operator call exists.

Keep the local serial lock. For public services, qualify independent per-user
wallet signing and concurrent shared-pool contributions/claims with stale quote,
ownership, nonce and load controls under the central frontend/service tasks.

## Fixed boundaries

| Desired future change | Current boundary |
| --- | --- |
| Supported source tokens, conversion routes, prices, pool parameters, operators | Governed configuration after sealing, within code constraints; immediate authorization, no delay. |
| Mint price/recipient, supply/rarity quotas, trait draw rules, 80/10/5/5, requested 5% royalty rate/weights | No ordinary post-seal setter. Requires separately reviewed architecture/replacement if changed; not a UI edit. |
| Randomness provider/lane/subscription/payment mode, canonical artwork base, module bindings, core strategy/adapter implementation | Fixed at or before sealing. Future-request confirmations/callback gas have their separate bounded setter; pending draws cannot be changed or rerolled. Range orientation and approved presets are supported policy, not a replacement algorithm. No proxy-upgrade or generic patch function. |
| Lower production activation below $100 or exceed the 10% hard execution-loss ceilings | No such configuration path. Governance can change current limits within 0-10%; defaults are 2% / 1% / 3%. The separate $1 local test build is not production configuration. |
| Redeem principal, reroll rarity, overwrite owners/reward balances, sweep liabilities | Not supported. Governance configuration is not permission to manufacture those operations. |
| Add arbitrary pair conversion, hooks, chains, cross-chain canonical replacement or post-halt recovery | Not made functional just by adding an address. Complete missing design, source support, independent review and rehearsals before relying on it. |

Future changes must preserve this distinction: what can be configured now, what requires new compatible code, what has actually been qualified, and what cannot be recovered. Do not describe a possible new deployment as a repair guaranteed to work with every already sealed predecessor.


### Local contribution form troubleshooting

The NFT dialog now shows validation, preparation and error feedback next to Review.
If acknowledgement is missing, tick the displayed checkbox; if approval just
confirmed, the same deployment/wallet/NFT/amount carries that acknowledgement to
the separate LP review. Changing the amount clears it. No approval automatically
sends Entry. A busy form cannot submit twice; failures remain visible in the dialog.
Only the NFT receiving activation/top-up has an artwork updating badge; global
stale balance guards remain. Reload the local page to load this UI-only change;
no service restart, contract call, public deployment or governance change is needed.

## Main website pending-action and storage recovery

The opt-in local **browser-wallet** mode has a separate
[signing and recovery procedure](BROWSER_WALLET.md). It uses unsigned typed
preparation, independent extension signing, exact nonce/code and bounded gas checks,
same-origin durable pending records and canonical receipt observation. Public
hosting remains a simulation. Its recovery must not be replaced by the demo or
launcher-owned signer procedures below; switching modes does not cancel a sent
transaction. No contract authority or production deployment changes.

Use the deployment-pinned read RPC for blockchain reads and receipts; the selected
extension handles authorization/signing. Review node chain/genesis, RPC origin,
CSP/CORS and fee policy together. A failed reader preserves the original hash;
never fall back to another chain, erase recovery storage or repeat an approval.
Approval completion is separate from the Entry transaction and cannot change LP
or artwork. See [reader setup, outage and recovery](BROWSER_WALLET.md#independent-read-rpc-and-recovery)
and [verification](../reports/browser-wallet/CHAIN_READER.md). Public signing and
production provider qualification remain gated. No contract role/control changed.

For type-2 receipts, use signed fee caps and the canonical block base fee to derive
execution price; retain raw RPC-reported price separately. The original reviewed
unit-price and total-cost limits still apply. Deterministic mismatches require
same-hash recovery, not another mint. See [dynamic-fee evidence](../reports/browser-wallet/DYNAMIC_FEE_RECEIPTS.md).

For connection failures, inspect the public account actually exposed to the site,
not only the account selected in the extension. Only the two disposable fixture
accounts are admitted locally. Change the wallet's site permissions as needed.
If the chain ID is 31337 but genesis verification fails, correct the run's exact
RPC URL; switching to another network with the same ID is insufficient. Refresh reads current authorization; explicit MetaMask selection reopens permissions.
Both reverify the deployment.
Failed connection leaves actions disabled and the error visible in the dialog.

If the wallet padded a transaction's gas limit, recover its original hash without
resubmission. The submitted transaction must retain the exact economic fields,
nonce and chain and stay inside hard policy limits; canonical gas used, unit price
and paid cost must also stay inside the original reviewed limits. Preserve that
review and the observed receipt. A pending receipt, altered economic field,
exceeded paid bound or changed inclusion remains unresolved for operator review;
do not erase the journal or repeat a confirmed approval. See
[connection and recovery evidence](../reports/browser-wallet/CONNECTION_RECOVERY.md)
and the full [receipt procedure](BROWSER_WALLET.md#submission-confirmation-and-artwork).

Wallet response and RPC-read waits are separate: 90 seconds for the extension,
15 seconds per read. Confirmation polls the same hash up to 21 times at 1500ms spacing,
within a 45-second monotonic read budget; no retry sends a transaction.
One confirmation requires two matching canonical block hash/number reads;
additional confirmations still require the configured depth. This avoids a
separate cached head vetoing checked inclusion. See
[automatic confirmation evidence](../reports/browser-wallet/AUTO_CONFIRMATION.md). If still unresolved,
inspect the wallet and recover the saved hash. Keep the original request and
review. Ordinary refresh shows labeled last-confirmed cards with actions disabled;
read failures or account/session changes must not present those values as current.

Local portfolio reads reuse one literal-loopback HTTP connection only within the
serialized read and close it on completion/failure. This changes no operator
permissions or production RPC configuration. A web-only update must authenticate
the original chain/session/journals; never restart Anvil to clear a slow read.
See [latency and mint follow-up](../reports/browser-wallet/MINT_WAIT_PERFORMANCE.md).

The production UI must request **Robinhood Chain**, using an independently
verified production manifest for chain ID, RPCs and contract identities. It must
not select a testnet or use an Anvil fallback. The current opt-in browser signer
continues to allow only local chain 31337; production manifest qualification and
public signing remain open. No public network values are inferred from a wallet's
network name.

The public simulation adds one `claim-testing-20261020` receipt after existing
saved actions. It preserves LP, NFT traits and cumulative claims; refreshing does
not refill a claimed receipt. Reset demo intentionally restores the starting
portfolio/history and a later page load can reinitialize that sample receipt.
The local contract adapter never uses this sample funding. Upgrade feedback uses
the supplied ACTI sound for activation (full audible clip, 3.69 seconds) and EV for
later upward tiers (1.425 seconds). The image crossfade and sound start together
after a successful contribution and refreshed increased LP/higher tier, in the
same wallet/session. Approvals, claims, failures and same-tier top-ups are silent.
Audio failure never changes transaction results; reduced motion suppresses glow.
Reload the page for updated JavaScript; existing local fixture servers already
allow the audio-only MP4 assets and need no chain reset. Static Node previews must
load the updated asset allowlist. No authority, signer or contract procedure changes.
The NFT detail view omits the Previously claimed frame; lifetime claims remain
accounted for. Earned history includes claimed and unclaimed rewards and must not
be relabeled as cumulative payouts or current claimable funds.

The main website tracks activation/top-up/claim work per NFT and mint separately.
A conflicting action on the same NFT or overlapping claim batch is rejected;
other NFTs can continue. Only a changed target artwork animates. Wallet/network
changes cancel unsent previews, and reconnecting to the old address does not
revive them. Default browser-wallet reconnection uses public-account reads only;
Disconnect clears its tab session selection. No new operator role or contract call.

Same-origin demo tabs use Web Locks for latest-state event commits and resource
conflicts. HTTPS/localhost plus a supported browser is required; unsupported locks,
failed storage, malformed history, a full 1,000-event log or a 10-second lock wait
produce explicit errors. Do not disable these checks. Refresh reads saved state
without replaying an intent. Reset demo invalidates pending work through a reset
epoch; preserve example history first if needed. It never affects on-chain funds.

Build/release the main static site through the normal approved deployment process;
reload JS after deployment. This local change does not restart the Anvil service,
production server or paused monitor. The prior release may contain lost-update
behavior; prefer a reviewed forward fix over rollback. See [evidence](../reports/frontend-state/VERIFICATION.md).
Production recovery still requires persisted transaction hashes and canonical
receipt/replacement/reorg reconciliation; browser/demo locks are not distributed
wallet authorization or a production multi-user capacity guarantee.

## Concurrent read and preparation services

Infrastructure operators configure `python -m frontend_api.server` and
`python -m frontend_api.activation_server` with the existing reviewed manifests.
Both now accept `--workers 4` (1-8) and `--max-connections 8` (1-32), per listener.
See [exact start commands, bounds and recovery](CONCURRENT_SERVICES.md). These
are separate read-only/unsigned services, with no new contract authority or signer.
Do not parallelize the disposable local launcher's mutation/signing lock.

Verify startup caps/chain and fresh `/v1/protocol` responses before exposing a
reviewed ingress proxy. Busy capacity returns 503 `service_busy` with Retry-After;
permit only finite read backoff, never a new financial submission as an automatic
retry. A failed cleanup permanently quarantines that worker slot and emits a fixed
operator-action log. Inspect and drain ingress, stop the service and all children,
retain sanitized evidence, correct the cause, then restart and verify fresh state.
Do not remove live-child directories or substitute old financial data. Reducing
workers to one is a bounded fallback; rolling back the HTTP protections is not.
Linux/provider capacity, process-group shutdown and off-host monitoring still need
qualification before hosting. No existing service or paused monitor was restarted.

Main-site unsent simulation actions expire after 15 seconds or navigation away;
returning to the page reads saved state and requires a fresh action. Ordinary tab
switching is allowed. The exact-version immutable preview cache never replaces
a storage read or an on-chain query. The local `/app/` confirmation adapter rejects
missing/nonfinite/overlong expiry, counts preparation time, and checks monotonic
and wall time plus chain/account/revision before submission. Refresh and prepare
again on expiry; recover unresolved submissions using the existing operation ID.
Only a page reload is needed for these website code changes. No economics, local
signer permissions, on-chain configuration or automatic transaction retry changed.

## Holder payout currencies

The current candidate supports LP conversion through its own fixed converter,
separate from `RoyaltyRewards.convertBatch(...)`. Follow [LP setup and recovery](LP_ETH_SETTLEMENT.md)
below. Older source-only deployments cannot gain this binding after sealing;
the [earlier audit](../reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md) applies
to those earlier sources. Never send LP ledger assets to the royalty converter
or configure arbitrary approvals. Verify actual receipt currencies, exact
converter bindings and backing before enabling native claims. Preserve source
balances and explicit pending/unavailable reporting while conversion is stopped.
Live qualification remains in the [central task](../TODO.md#task-lp-eth-settlement).

Historical pre-V2 named-fixture UI: four visible input choices (ZZZ/USDG/USDC/ETH), internal WETH accounting, a dedicated contribution dialog and confirmed per-NFT evolution refresh. That fixture's wrapping behavior does not describe native V2. See [named local rehearsal](LOCAL_TEST_STACK.md#named-input-local-rehearsal). No production authority/procedure change; public routes, ETH-only LP settlement and hosting remain open.

Contribution incidents: distinguish a rejected/preparation failure, pending/unknown
receipt, reverted receipt and confirmed LP with a failed read. Never ask for a new
submission while the original result is unknown. Recover the same operation ID and
receipt first. A reverted Entry preserves input tokens but costs gas and can leave
an earlier allowance. A successful Entry creates nonredeemable LP even when the
API subsequently fails. Separately wrapped local ETH remains wallet-owned WETH
if contribution fails. The pre-V2 native-input fixture wrapped inside Entry
atomically; native V2 Entry uses actual ETH and does not wrap. See the
[failure evidence](../reports/topup-and-reward-review/contribution-rollback.json).

## Convert LP holder fees to ETH

Follow the [LP ETH settlement procedure](LP_ETH_SETTLEMENT.md#operator-procedure) before sealing: bind a separate converter, review wrapper/routes/feeds, enable the guarded worker, and confirm exact source/native liability changes. It covers route rotation, dependency-independent stops, source-currency recovery, pending transaction reconciliation, restart and irreversible bindings. Read the converter's current `conversionLossBps()`; the default is 1% with a 10% hard maximum, gas separate. See [bounded scheduling](LP_ETH_SETTLEMENT.md#keeper-configuration-and-scheduling) for both conversion streams and maintenance.

## Local activation review during a busy refresh

For the disposable loopback website only, reload `/app/#my-nfts` to load the
client fix; no restart, reset, authority change or contract deployment is needed.
Review activation/mint/claim can wait for a portfolio refresh using at most 30
preparation attempts within the existing 90-second request timeout. Only the exact
409 busy response, emitted before preparation starts, is retried. Account/state
changes cancel the wait. Draft expiry counts from the final preparation attempt,
including processing time; rejected busy waits create no draft.
Approval and Entry still need separate confirmations. No `/action` submission or
lost response is retried automatically. If contention persists, let the other
tab finish, then prepare again; inspect pending-operation recovery before any
new submission. Never reset the live test chain merely to clear this message.
Reverting the client restores the immediate-busy error but changes no on-chain
state. See [focused verification](../reports/local-preparation-busy/VERIFICATION.md).

## Two-transaction contribution operation

**Historical pre-V2 fixture scope:** the commands and wrapping observations in
this subsection refer to the earlier WETH-accounting local build. Existing 8902
state/journals are preserved. Do not restart it with V2 sources or assume that an
old launch command qualifies a new V2 fixture; verify a separate coherent build,
configuration and state directory first.

For those local rehearsals, use `--named-assets --native-input` with a new port/state
directory; it substitutes local-only native admission, not production venue pins.
Never restart an existing lab expecting persisted chain recovery: preserve its
owned Anvil process and state, or use a separately verified web-only recovery.
Stop a pending UI flow without repeating a confirmed transaction; reread balances
and allowance before preparing again. Old unsigned drafts expire/cannot be replayed.

The holder approves exactly the required ERC20 amount once, then explicitly confirms
Entry. Direct approval must simulate successfully; a reset-only token is unsupported
rather than silently adding a third send. Already sufficient allowance needs no
approval. ETH wrapped atomically inside Entry in that pre-V2 native-input fixture;
the older WETH-only pool could not offer that path. Current native V2 Entry and
pool custody instead use actual ETH without wrapping. The local fixed activation is
$100; top-ups start at $5. This does not change production Entry's $100 minimum.

Verify receipt success, increased confirmed LP and unchanged unrelated NFTs before
celebration. Failure of the atomic Entry call reverts conversion/LP effects,
including any wrapping in the historical pre-V2 fixture; approval and paid gas
are separate. No governance/keeper permission
changes. [Runbook](LOCAL_WEBSITE.md#local-contribution-flow---2026-10-20) and
[evidence](../reports/local-contribution-flow/VERIFICATION.md).


## Two browsers using local wallets

Chrome and Codex may select different disposable accounts on the same running
loopback deployment. Reload both pages after a client update; account selection
and saved pending intent remain in each browser's session storage. No operator
permission, service restart or Anvil reset is required for this fix.

A newer unsigned draft triggers a real confirmed-state read and up to three
preparations if the other browser keeps changing state. Review the final wallet,
amount and operation before confirming. If state changes after review, an explicit
rejection sends nothing and refreshes balances; review again manually. If the
response is ambiguous, use Refresh to recover the identical saved operation ID.
Do not clear pending storage or create a replacement operation to bypass recovery.
A definite server rejection of a recovered intent is safe to clear; unresolved
outcomes remain blocked. Verify receipt and confirmed balances for success.

Stop by cancelling an unsigned review. Rollback means restoring the prior client
and reloading; it does not undo transactions and restores the stale-cache bug.
Keep both chains and their state intact. [Evidence](../reports/local-wallet-concurrency/VERIFICATION.md).


### Local submission lock recovery - 2026-10-20

The exact `/action` pre-handler busy response now waits with the identical saved
operation ID and payload (30 attempts maximum within a 90-second request timeout).
This is the narrow exception to earlier notes saying submissions never retry.
Lost responses and ambiguous outcomes still require saved-intent recovery; state
changes after review still require a new review. Reload both browsers to pick up
the client fix; use Recover status for a saved pending intent. Do not clear session
storage, repeat a confirmed approval or restart/reset Anvil. No permissions or
contract changes. Reverting the client restores the immediate lock error without
undoing transactions. [64 scoped cases and actual lock probe](../reports/local-wallet-concurrency/VERIFICATION.md#submission-lock-follow-up---2026-10-20).


## Independent local wallet confirmations - 2026-10-20

Typed local wallet drafts now pin the sender nonce. Another wallet's transaction
no longer invalidates an otherwise valid review. The server still binds the exact
saved draft/revision/account and freshly simulates unchanged calldata within the
reviewed gas ceiling; same-wallet nonce changes, expiry, owner changes and invalid
execution still require fresh review. Legacy operator actions keep global revision
checks. This supersedes the earlier rule rejecting every cross-wallet revision.

Reload both browsers after the guarded web-only upgrade on 8898. Old unsigned
reviews are invalidated: review afresh. Recover saved pending outcomes by the same
operation ID before starting new work; never clear storage to bypass uncertainty.
No new authority or contract function is introduced. Cancel an unsigned review to
stop; restoring old service code restores the global conflict behavior, not prior
chain state. Verify receipts and confirmed ownership/LP after execution. Never
reset Anvil to resolve a browser confirmation issue. The guarded external recovery
script preserves existing contracts and positions; ordinary launcher restart does
not promise persistence. Port 8896 remains on the earlier service until separately
reloaded. [70 distinct Python cases and two actual local mints](../reports/local-wallet-concurrency/NONCE_VERIFICATION.md).


## Capacity decision and manual acceptance - 2026-10-20

The user reports the six local two-wallet flows passed; see the
[manual acceptance record](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md).
This report does not change operator functions, roles, configuration, limits or
stop/restart procedures. The dedicated 10/25/100-user load campaign is deferred;
do not run it automatically or raise worker limits as part of this decision.
Continue using bounded API admission, independent user-wallet signing and saved
transaction recovery for the production integration. The shared local signer
and lock remain test-only. Production capacity is unverified, and accepting real
funds still requires the outstanding dependency and release qualification.

### Queued wallet transaction recovery

If recovery reports a changed or blocked transaction number, use the
[wallet queue procedure](BROWSER_WALLET.md#queued-or-changed-transaction-numbers).
Preserve the original hash and review; Close does not cancel a submission.
Inspect the node and wallet before any separately approved reconciliation.
Do not reset Anvil, fill nonce gaps, or erase unresolved journals. The diagnostic
does not add cancellation, replacement discovery or nonlocal signing.

For the authorized nonce 35 incident, follow the [one-time reconciliation](../reports/browser-wallet/local-mint-reconciliation/RECONCILIATION.md). Node cleanup is complete; the user browser/MetaMask step remains pending.

### Real local API rehearsal and complete wallet totals

Use [the isolated API runbook](LOCAL_API_REHEARSAL.md) to exercise actual local
contracts and reviewed preparations with the unchanged Anvil-only signer. It
explains build/configuration pins, exact RPC/account selection, bounded summary
chunks, missing-value handling, recovery and safe stop/restart. Operator authority
is local fixture ownership only; no public contract/role/provider is configured.

## Collection data operations - 2026-10-23

Use [the confirmed collection procedure](COLLECTION_READS.md) for endpoint setup,
complete inventory/current LP semantics, matched API/proxy/frontend deployment,
refresh, stop/rollback and stale/reorg/indexer recovery. This is a read-only
service change; no contract function, permission, key or transaction is added.
