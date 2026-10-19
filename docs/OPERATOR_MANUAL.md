# PoPL operator manual

This is the management guide for the **current undeployed candidate**. It describes available controls, their effects and recovery boundaries; it does not approve a production deployment. Use the [central Todo](../TODO.md) for outstanding work and the [release record](RELEASE_CHECKLIST.md) for deployment approval. Production addresses, services and several migration capabilities remain unqualified.

**Keep this manual current.** Every change to an operator-facing function, permission, default, parameter, lifecycle, service or failure mode must update the affected procedure in the same change, or explicitly record why there is no operator impact. Update the task ledger and feature/evidence reference too. This is a required development/review step, not automatic synchronization. See [maintenance rules](TODO_WORKFLOW.md).

## Find the right procedure

| I want to... | Procedure |
| --- | --- |
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

`rangeBps` is the approximate percentage **on each side of the oracle reference token1/token0 price**, with outward tick rounding. It is not half the total capital, and the center is not an unchecked spot price.

| Intended interval at reference price P | `rangeBps` | Example at P = 1 |
| --- | --- | --- |
| +/-50% | `5000` | 0.50 to 1.50 |
| +/-20% | `2000` | 0.80 to 1.20 |
| Total width 20%, meaning +/-10% | `1000` | 0.90 to 1.10 |

1. Read `PoolRegistry.get(poolId)` and copy the **entire** `PoolConfig`, including its real venue key. Change only the intended settings. For the selected native/Pons pool use `configureNative(config)`; for supported hookless ERC20 pools use `configure(config)`. Do not sort the normalized WETH/ZZZ accounting pair or replace a native venue key with its accounting key.
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
| `maxSlippageBps` | 1-200; pool fee must be strictly below it in equivalent units | Selected native/Pons admission additionally requires greater than 100. This venue guard does **not** weaken the 1% complete contribution-loss ceiling. |
| `minDepositUSD`, `maxPositionUSD` | Positive minimum; maximum at least minimum | Minimum for each contribution and maximum cumulative gross contribution per NFT, in 18-decimal USD units; not a live market-value ceiling or total pool cap. Lowering them cannot remove the fixed $100 activation / $5 top-up floors. The effective minimum is the larger of the action floor and configured minimum. Check existing NFT contributions/top-ups. |
| `depositsEnabled`, `operationsEnabled` | Full configure for enabling; `disablePool` can only clear flags | Different controls; see below. |

Ordinary rebalance and supported local move/resume must retain at least **97% of starting principal plus released compound**, measured at the same starting prices, in LP plus attributed idle; idle has its own 5% ceiling. Contributions must deploy at least **99% of gross original source value as new LP**. Network gas is separate. The user retained **per-operation limits only**: repeated permitted operations can accumulate losses. Monitor total turnover/costs and stop harmful activity; no rolling loss breaker or guarantee against impermanent loss exists.

### Contribution minimums

For normal $5 increases, governance configures `minDepositUSD=5e18` through the
appropriate full `configure`/`configureNative` call. Activation still requires
$100; each action must deploy 99% of its original value, gas separate. No per-user
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

## Activation assets and routes

An **activation route** converts a user's contribution into the LP pair. It is distinct from moving the Vault's already-held LP to another pool. Changing a USDG conversion pool does not migrate the attached LP or change its owners.

### Add or re-enable an input token

1. Review its exact chain/address, runtime and proxy authorities, decimals, transfers, liquidity, fees and price source. A symbol such as USDC does not identify an asset. Fee-on-transfer/rebasing/blacklisting or malicious callbacks can make an asset incompatible; permission to admit is not proof of compatibility.
2. Governance configures the reviewed `Oracle.setFeed(token,feed,maxAge)`. Independently verify `price(token)` and decimals. Admit the source with `ActivationAssets.setAsset(token,true,expectedCodeHash,reviewHash)` at the registry's immutable `activationAssets()` child.
3. If conversion is needed, governance calls `ActivationEntry.addRoute(RoutePolicy)`. The current supported path is typed **single-hop V3** into one accounting-pair asset, with pinned source/output/router/factory/pool code and fee; direct input/native wrapping is separate. It is not a general multi-hop router or arbitrary external executor.
4. Verify route ID, enabled status and exact factory/pool/token bindings; update reviewed backend route/feed pins and available UI choices. Simulate the complete input-to-LP operation, including the 1% limit and separate gas. Qualify actual execution before enabling real users.

Native ETH uses the admitted wrapper/native path; do not admit `address(0)` as an ERC20 source. Accepting a new **input** does not automatically admit it for LP or royalty payouts. Those have separate finite ledgers. Actual production ETH/ZZZ/USDG/USDC services/routes remain subject to [qualification](ACTIVATION_PREPARATION.md).

### Replace a swap route when market liquidity moves

Read/review the new route, append it with `addRoute`, qualify it, switch the backend's selected route, and use `setRouteEnabled(oldId,false)` to stop the old route. Route contents/identities are immutable; do not overwrite one in a manifest under the old hash. There is no time delay. Concurrent user quotes may revert after disablement and must be rebuilt. Already mined operations cannot be undone.

To stop an input immediately, use `ActivationAssets.setAsset(token,false,expectedCodeHash,reviewHash)` with the required nonzero token/review hash, and disable affected Entry routes. Disable paths deliberately avoid dependency calls needed for enabling; they can help when a token/feed is broken. Previously attached LP, shares and claims are not erased. Re-enabling requires valid current token/feed/code checks and new quotes. Pool configuration cannot silently re-enable an explicitly disabled source. See [asset controls](ACTIVATION_ASSETS.md), [Entry](ACTIVATION_ENTRY.md) and [routing](ACTIVATION_ROUTING.md).

## Pool admission and retirement

For a supported new LP venue, first qualify tokens, feeds, reward-asset admission (`Rewards.addAsset(token)`), the exact venue key/manager and strategy. Then governance calls `configure` or the narrowly supported `configureNative`. Not every Uniswap v4 hook/native pair is supported. The selected native/Pons constants and immutable adapter bindings are not arbitrary venue plug-ins.

### One contribution pool at a time

`PoolRegistry.contributionPool()` is the only pool whose `depositsEnabled` flag
can be true; zero means new activations/top-ups are stopped. Initial production
configuration must select the reviewed Robinhood ZZZ/ETH native/Pons pool
`0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f`.
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

### Move to another supported pool on the same chain

Governance calls `Migration.movePool(bucketId,newPoolId,minimumLiquidity,deadline)` after qualification and simulation. There must be no conflicting active plan; custody must be local and eligible, destination capacity/occupancy valid, and the **ordered accounting token pair must match**. Source exit price checks, destination deployment checks, aggregate 3% budget and idle ceiling remain. The operation harvests/closes/redeploys atomically; failure reverts it. Verify custody, actual LP, shares and both reward ledgers afterward.

A different fee tier/tick spacing or supported venue with that same pair can be an eligible move. Converting ZZZ/ETH principal to a different pair is **not implemented by this path**. Do not disable ordered-pair checks or use an activation swap route as a migration executor. Different-pair composition/accounting remains a separate development task.

### Park principal during an incident

1. Guardian/governance pauses globally. Read the exact current bucket/pool/LP/shares/deposit/custody-epoch/parking-nonce/token snapshot.
2. Prepare `Migration.park(ParkingRequest)` with that snapshot, reviewed raw token close minima, review hash and a deadline within ten minutes. Simulate the complete close and inspect exact resulting principal.
3. Governance executes. Parking closes LP into the Vault and preserves attributed custody/rights; it is not an owner withdrawal. It bypasses source USD prices and creator-inbox synchronization, **not** token, venue or wrapper failures. It requires the supported local active state and no conflicting active plan.
4. Confirm `Parked` status, no active physical LP, exact attributed token balances, unchanged shares and available claims. Current LP valuation is unavailable while parked; there are no venue swap fees from a closed position.

Invalidate stale parking authorizations with `Migration.invalidateParking(bucketId)` and cancel the controller operation where necessary. State drift also invalidates an exact parking snapshot. For details and tuple fields, use [parking](CUSTODY_PARKING.md) and [Migration source](../src/ZZZMigration.sol).

### Resume parked LP

Repair/qualify dependencies, choose an enabled supported same-pair destination, and simulate `Migration.resume(bucketId,newPoolId,minimumLiquidity,deadline)`. Resume requires ordinary live/unpaused state and new-work permission; governance must unpause separately. Keep unwanted deposits disabled and the keeper stopped while staging the reopening; use a reviewed exact batch if needed. Verify recreated LP, value, shares and claims before enabling normal user/keeper work. A failed resume leaves principal parked; never send it to an operator wallet to work around a revert.

### Bridge or change the home chain

Real bridging remains **disabled pending qualification**. The framework exposes `BridgeRouter.registerPolicy`, `setOutboundEnabled`, `MigrationRegistry.add`/`setEnabled`, governance `Migration.propose`/`cancel`, and keeper `Migration.execute`; registration is not production permission. Approved plans have no additional waiting period. Delivery needs authenticated transport, reviewed backing/equivalence, destination reservation, finality and correct reward/ACK paths.

Disable outbound policy/routes to stop new sends; cancel still-scheduled plans. Already sent principal cannot be cancelled by deleting its record or timing out. Keep authenticated incoming settlement and historical policy records available. Do not register a mutable provider under an old immutable policy identity. See [provider onboarding](OPERATIONS.md), [migration safety](MIGRATION_SAFETY.md) and [chain recovery design](CANONICAL_MIGRATION_DESIGN.md).

Moving LP does not move canonical NFT ownership and reward ledgers. Complete future-chain collection relocation, channel closure and post-halt recovery are not supplied by current same-chain handoff. A chain/bridge/token that permanently stops may prevent recovery; no manual procedure can guarantee movement from an unusable dependency.

## Dependencies and pricing

| Change/problem | Control and checks | Fallback/limit |
| --- | --- | --- |
| Price feed or freshness policy | Governance `Oracle.setFeed(token,feed,maxAge)`, maxAge 1-86,400 seconds, feed/asset decimals ≤18; verify actual USD semantics, rounds, freshness and oracle price | Do not substitute pool spot, assume a stablecoin is $1, or stretch maxAge to conceal stale data. Pause/disable affected entry; consider exact parking if executable. |
| Sequencer feed replacement | `setSequencerFeed(source,expectedCodeHash,reviewHash)` after reviewing the new nonzero source | Replacement does not require the failed old feed to work. Existing recovery grace remains. No setter removes the protection by setting zero. |
| Supported WETH implementation/admin change | `PoolRegistry.approveWrapperPolicy(policy)`, then `activateWrapperPolicy(id)` after live code/getter/authority review | Same canonical wrapper only. It does not approve arbitrary venue code changes or repair a hostile proxy. Parking itself can fail if wrapper bindings fail. |
| Pons hook, pool manager, token or router change | Compare actual code/config/authorities to the deployment pins; stop affected work | Some source/route policies can be replaced, but immutable venue bindings cannot be patched by changing a manifest. New unsupported implementations require compatible reviewed replacement work. |
| RPC/trace/archive outage | Use chain-checked reviewed endpoints with required hash-pinned reads and trace/receipt semantics | Never fall back to latest/unconfirmed state or a wrong chain. Serve unavailable status; retain indexes/state. |

Changing off-chain code hashes to whatever is currently deployed is not a review. Verify proxy implementation and external control as well as runtime bytecode. Governance configuration during canonical preparation is blocked; cancel preparation only if reopening is intended, not to bypass a migration freeze.

## Revenue operations

Revenue is receipt-based, not a per-minute promise. **80/10/5/5 is fixed**: individual LP shares / equal activated-NFT collective membership / compound reserve / buyback reserve. Rarity only weights the separate royalty ledger at x1/x2/x3. Source: [economics](ECONOMICS.md).

| Operation | Entry point / owner of action | Verify and recover |
| --- | --- | --- |
| Receive creator revenue | Governance creates the bucket's immutable inbox via `Fees.createRewardReceiver(bucketId,wrapper)`; give the creator the verified `rewardReceiver(bucketId)` | Qualify payout assets/native wrapping, percentage basis, frequency and payer agreement. Receiver is append-only, not an operator wallet or the mint recipient. Unsupported/donated tokens do not automatically become rewards. |
| Process creator payment | Permissionless `Fees.syncExternal(bucketId)` through its bound inbox | Compare actual received funds, allocated ledgers and reserves. Missing creator payments cannot be fixed by calling sync more often. No automatic debit of creator funds. |
| Harvest conventional venue fees | Permissionless `Vault.collectFees(bucketId,deadline)` while live and locally active | Receipt must show real funded allocation. The selected pool's zero conventional LP fee does not itself provide the creator's hook revenue. |
| Compound | Keeper `Compounder.compound(bucketId,minimumLiquidity,deadline)` | Uses classified reserve, actual pool and guards; funds never pass through keeper. Poll/threshold changes are off-chain; insufficient funds or unsafe execution waits/reverts. |
| Buy back and burn | Keeper `Buyback.execute(token,amount,poolId,deadline)` | Check reserve, oracle value ≤ immutable `maxTradeUSD`, swap minima, actual ZZZ acquired and total-supply reduction. Trade-size ceiling and target ZZZ are not mutable setters. |
| Admit LP payout asset | Governance `Rewards.addAsset(token)` | Permanent bounded history, maximum 32; do not fill slots with speculative assets. Admission is distinct from input routing. |
| Receive marketplace royalties | `NFT.royaltyInfo(tokenId,salePrice)` returns the NFT's royalty receiver and requested 5% | Configure marketplaces with the **returned contract receiver**, never a manager wallet. ERC2981 is a request, not universal enforcement on every marketplace. |
| Admit royalty currency | Governance `NFT.addRoyaltyAsset(token)` | Initial scope is native ETH plus the independently verified Robinhood WETH wrapper; stablecoin conversion depends on marketplace qualification. Admission does not restrict sales or convert payouts. Separate bounded ledger (17 total including native); no arbitrary removal/sweep. Pre-admission/no-eligible-holder funds stay quarantined. |
| Synchronize/claim royalties | Permissionless `RoyaltyRewards.sync(asset)`/`syncAll`; actual owner calls ledger `claim` or bounded ClaimRouter | Direct royalty claim synchronizes pending admitted receipts. LP claim does not harvest new venue fees. Use current owner and actual funded amounts. |

A holder can claim both streams in a **1-32 operation atomic ClaimRouter batch**, or claim individually. One failed operation reverts the whole batch; simulate and split by asset/NFT if needed. No operator can choose a different beneficiary or claim just because it holds ERC721 approval. All unclaimed rights follow the current NFT owner; already paid funds do not travel with it. An escrow that owns the NFT is the contract-level holder. Lifetime claimed display requires complete confirmed index history, including predecessors after replacement.

Pause generally preserves claims and transfers while canonical state is operating. A frozen/retired deployment has different rules; follow lifecycle status rather than presenting a failing claim button. Failed payout tokens, blacklists or recipient callbacks may still block their claims. There is no generic admin seizure/sweep/rewrite to clear a liability. Keep actual funded balances distinct from unharvested fees, proposed creator invoices and UI estimates.

Stop scheduled compounding/buybacks using reviewed keeper configuration or by stopping/revoking the keeper. Accumulated reserves remain classified on-chain; no automatic transfer to the operator is allowed. Change creator commercial terms off-chain and reconcile payments, while royalty-only conversion uses the separately bound guarded converter; LP payouts and the fixed 80/10/5/5 allocation are unchanged. See [external revenue](EXTERNAL_REWARDS.md), [royalty/claim behavior](CLAIM_ROUTER.md) and [measurement proposals](REVENUE_SHARE.md).

### Coordinate the creator agreement

Use [Creator tasks / ZZZ team](../TODO.md#creator-tasks--zzz-team) as the meeting agenda and decision record. For each answer, record its date, authorized contact, precise terms or public addresses, effective period and supporting evidence. Keep unresolved answers open. Request public identifiers and proof of control where relevant; never request a signing key.

Commercial agreement alone performs no contract call. Before accepting funding, independently verify the current canonical per-bucket receiver, admitted pair/wrapper and payer instructions using [external funding](EXTERNAL_REWARDS.md). Explain processing-time allocation and keep the marketplace royalty receiver separate. A proposed invoice or missing payment must not become a funded claim.

Changes to the agreement require reconciliation of old/new periods and verified payment destinations. Stop an unqualified new configuration, retain existing funded liabilities and use the applicable pool/asset/incident procedure; do not sweep or redirect a fixed receiver. Reopen only after the changed dependency and payment flow are reviewed. This coordination procedure adds no authority, setter, timelock or automatic payout.

### Marketplace currency and ETH payouts

The [settlement and conversion runbook](ROYALTY_SETTLEMENT.md) specifies the exact
OpenSea pricing procedure, pre-seal converter binding, reviewed wrapper/routes,
post-seal governance stop/reopen controls, keeper configuration, gas budgets,
outage recovery and event/accounting checks. Native ETH requires no conversion;
WETH unwrap is exact and stablecoin conversion enforces at most 1% execution loss.
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

Before sealing, qualify the actual randomness coordinator/network/subscription, funding asset, gas lane, confirmations and callback budget. `NFT.configureRandomness(...)` is **one-time before seal**; coordinator, request settings and subscription ID cannot be changed afterward. Funding/service management uses that provider's reviewed procedures, not an invented PoPL retry function. Do not seal against an unavailable/unqualified provider.

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

This is a separately reviewed operation, not routine LP maintenance. Current implementation supports **same-chain** replacement only, with every minted draw finalized, buckets parked/None, no conflicting plans and no historical legacy bridge traffic. Read [the exact handoff sequence](CANONICAL_HANDOFF.md) before any attempt.

Run the [read-only holder inventory and escrow cutover procedure](HOLDER_PREFLIGHT.md) before preparation and again after freeze. Every code-bearing owner requires a review of its ability to release and claim for the exact replacement; a complete inventory is not approval.

1. Independently review the proposed different-code successor, its economic compatibility and deployment commitment. Governance is trusted to approve it; there is no identical-code safeguard. Inventory every contract/escrow NFT holder: same owners at a new NFT contract address does not prove their escrow can operate it. Rehearse withdrawals/cutover while the old system is still usable; never rewrite owners to work around an incompatible escrow.
2. Prepare the destination as an inert importer with `CanonicalHandoff.prepareImport(sourceController)` **before its seal**; qualify its dependencies/randomness and bind it to this source. Governance calls source `AccessController.startPreparation(PreparationNotice)` naming the reviewed sealed importer. Preparation stops new mint/activation/maintenance/config work while reveal, transfers, claims and permitted drains remain possible.
3. Finish existing provider responses and ordered `finalizeTraits` calls; confirm `unfinished_draws=0`. This is the selected simple policy: reliable funded provider plus draining before replacement. Do not remove the fully-revealed check if a request is stuck. Cancel the exact notice via `cancelPreparation(noticeHash)` if postponing, then restore ordinary controls deliberately.
4. Drain/park custody and resolve plans. Governance `freeze()` stops ownership/accounting before capture. Complete six ordered `settle(slot)` domains; relay all `exportRows`/`importRows` batches of at most eight, `completeImport()`, then exact classified `fund(slot,index)` legs. Resume interrupted progress from on-chain cursors/roots, never from an assumed last successful terminal command.
5. Verify every root, owner, trait, share, liability, reserve and exact backing. Governance `commit()` atomically retires the source and activates one successor. Finality remains required before service/marketplace cutover. Update canonical address/runtime and complete predecessor-history configuration, payout routing and marketplace collection records; old ERC721 approvals are not imported.
6. Before commit, `abort()` cancels the importer; return every funded leg via `returnFunds`, then `finishAbort()` only after full restoration. This is not immediate unlock. After successful commit the source cannot be revived by unpausing or cancelling preparation. Late creator/royalty receipts forward one successor at a time through the supported forwarding functions.

A successful same-chain handoff does not qualify cross-chain finality, transport, historical bridge closure or post-halt recovery. Do not promise those can be added to the already sealed source later. Imported successors cannot initiate the current legacy-v3 principal bridging model. Track the remaining design in the [canonical recovery task](../TODO.md#task-security-chain-recovery).

## Stop controls

**These controls are not interchangeable.** First reconcile already-broadcast transactions; stopping a service or disabling a route cannot undo a mined operation.

| Control | Stops | Preserves / restart |
| --- | --- | --- |
| Hide a frontend action | That UI path only | Direct contract calls continue. Restore UI only after real backend/on-chain readiness. |
| Stop an API/indexer/keeper process | That service's new work | On-chain custody/rights persist; another authorized keeper/direct caller may operate. Recover durable state before restart. |
| Revoke keeper | New authorized keeper actions from that address | Permissionless claims, transfers and allowed fee synchronization remain. Governance must authorize a reviewed replacement. |
| Disable source asset / Entry route | Affected contributions/conversions | Existing LP and funded claims remain. Re-enable after dependency review, re-quote. |
| `NFT.setMintPaused(true)` | New NFT mints and new randomness requests | Governance only. Original fulfillment/finalize, existing NFT rights and LP work retain their own guards. Resume with `false`; global/lifecycle controls remain. |
| `PoolRegistry.disablePool(id,stopDeposits,stopOperations)` | Pool-specific new contributions / ordinary guarded operations; no token/price/venue reads on disable | Governance only; flags only clear. Not universal pause. Reopen with full validated config; parked LP still needs resume. |
| `AccessController.setPaused(true)` | Live mint, contribution, rebalance/compound/buyback and outgoing principal execution | Operating-state transfers/claims, authenticated incoming settlement and supported drains remain. Only governance unpauses; it does not clear preparation/canonical lock. |
| Canonical preparation | New economic work and normal protocol configuration | Existing claims/transfers/reveal/permitted drains; exact notice can be cancelled before freeze. Not a generic pause toggle. |
| Canonical freeze | Ownership and ordinary reward/accounting operations | Only handoff settlement/export/funding/abort path. Fully restore abort or complete one successor; no guardian unlock. |
| Disable bridge outbound / cancel scheduled plan | New sends / that unexecuted plan | Preserve historical policies and authenticated pending delivery. No post-send refund or timeout rescue. |

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
| Repeated slippage/loss/minimum failure | Retain old position; inspect actual conversion, venue costs, liquidity and oracle | Better route/timing or legitimate parameter review inside fixed limits; do not weaken accounting/aggregate limits to force success. |
| Gas spike/low keeper funds/daily budget reached | Stop new submissions; continue receipt reconciliation/alerts | Refill reviewed signer or revise operating budget after analysis; gas is not taken from arbitrary holder balances. |
| Unknown broadcast/nonce drift/reorg | Stop new signing, retain exact intent/hash and canonical anchors | Reconcile confirmed/pending transactions through recovery path; no blind resend or nonce reset. |
| Token blacklist/pause, wrapper upgrade or venue unusable | Stop new exposure, preserve ledger, review dependency and exact exit | Policy update only where implemented and safe; venue/token failure can block even parking/claim/abort. No blanket rescue function. |
| Creator does not pay / royalties missing | Compare payer agreement, receiver and actual transfers | Process real receipts, resolve external payments; no invented accrual. Keep separate from API history outages. |
| VRF unfulfilled / ordered reveals blocked | Verify subscription/provider/request; stop new minting if needed | Use the mint-only governance pause, then original authenticated fulfillment and ordered finalize. Resume deliberately after service checks. No reroll; postpone whole-collection replacement if unresolved. |
| Server/disk/backup failure | Stop unsafe signing; alert off-host, preserve damaged evidence | Restore/reconcile state, permissions and storage; qualify health before new work. |
| Failed bridge / original chain halted | Disable new exposure, retain authenticated channel/accounting evidence | Use reviewed provider recovery if available; no timeout multisig override or promised post-halt canonical recovery. |
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
| Randomness provider/settings, canonical artwork base, module bindings, core strategy/adapter implementation | Fixed at or before sealing. No proxy-upgrade or generic patch function. |
| Lower production activation below $100 or exceed 1%/3% execution caps | Not an operator setting. The separate $1 local test build is not production configuration. |
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

The current LP reward ledger pays its admitted source ERC20 directly. It has no
LP conversion/unwrap function. Creator ETH intake is wrapped into the accounting
asset; `RoyaltyRewards.convertBatch(...)` handles royalty balances only. There is
no operator call or keeper flag that turns current LP claims into native ETH.
Do not configure arbitrary approvals or send ledger assets to the royalty
converter. See [the audited boundaries](../reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md).

Before enabling an ETH-only user flow, complete and review the linked pre-seal
implementation. Verify actual receipt currencies, converter bindings and output
backing, not token labels. Until then preserve source-asset balances and explicit
unavailability/pending status. Existing controls can stop new maintenance or
conversions within their own documented scope; they do not add missing payout
functionality. No new authority, operator procedure or economic code is introduced
by this audit; qualification remains in the [central task](../TODO.md#task-lp-eth-settlement).

Contribution UI follow-up: four visible input choices (ZZZ/USDG/USDC/ETH), WETH internal only, dedicated contribution dialog and confirmed per-NFT evolution refresh. See [named local rehearsal](LOCAL_TEST_STACK.md#named-input-local-rehearsal). No production authority/procedure change; public routes, ETH-only LP settlement and hosting remain open.

Contribution incidents: distinguish a rejected/preparation failure, pending/unknown
receipt, reverted receipt and confirmed LP with a failed read. Never ask for a new
submission while the original result is unknown. Recover the same operation ID and
receipt first. A reverted Entry preserves input tokens but costs gas and can leave
an earlier allowance. A successful Entry creates nonredeemable LP even when the
API subsequently fails. Separately wrapped local ETH remains wallet-owned WETH
if contribution fails; public native Entry wrapping is atomic. See the
[failure evidence](../reports/topup-and-reward-review/contribution-rollback.json).
