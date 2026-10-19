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
| `minDepositUSD`, `maxPositionUSD` | Positive minimum; maximum at least minimum | Minimum for each contribution and maximum cumulative gross contribution per NFT, in 18-decimal USD units; not a live market-value ceiling or total pool cap. Lowering them cannot remove the fixed production activation floor. Check existing NFT contributions/top-ups. |
| `depositsEnabled`, `operationsEnabled` | Full configure for enabling; `disablePool` can only clear flags | Different controls; see below. |

Ordinary rebalance and supported local move/resume must retain at least **97% of starting principal plus released compound**, measured at the same starting prices, in LP plus attributed idle; idle has its own 5% ceiling. Contributions must deploy at least **99% of gross original source value as new LP**. Network gas is separate. The user retained **per-operation limits only**: repeated permitted operations can accumulate losses. Monitor total turnover/costs and stop harmful activity; no rolling loss breaker or guarantee against impermanent loss exists.

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

Stop scheduled compounding/buybacks using reviewed keeper configuration or by stopping/revoking the keeper. Accumulated reserves remain classified on-chain; no automatic transfer to the operator is allowed. Change creator commercial terms off-chain and reconcile payments, but do not promise arbitrary payout-asset conversion or a mutable 80/10/5/5 allocation. See [external revenue](EXTERNAL_REWARDS.md), [royalty/claim behavior](CLAIM_ROUTER.md) and [measurement proposals](REVENUE_SHARE.md).

### Marketplace currency and ETH payouts

The [royalty settlement procedure](ROYALTY_SETTLEMENT.md) records the accepted
ETH pricing direction, exact OpenSea owner/editor request, asynchronous verification,
and receipt checks for listings/offers/checkouts. Do not infer that a buyer using
USDC means PoPL receives USDC, or that ETH pricing proves every order excludes it.
If stablecoin royalties cannot be excluded, guarded automatic conversion is required.
The current ledger pays each admitted currency directly; no WETH unwrap or swap
command is implemented. Do not promise ETH-only claims from this candidate.

An unreadable admitted ERC20 balance can still revert activation and `syncAll`;
healthy single-currency claims are separate. Zero royalties are valid. Investigate
the asset without bypassing accounting or removing liabilities. Activation inputs,
rarity fixed at reveal, and activation-based royalty eligibility remain distinct.
The central [settlement task](../TODO.md#task-royalty-eth-settlement) owns the
conversion/failure-isolation work and qualification; this procedure is not evidence
that those changes are implemented.

## Mint and metadata

Before sealing, qualify the actual randomness coordinator/network/subscription, funding asset, gas lane, confirmations and callback budget. `NFT.configureRandomness(...)` is **one-time before seal**; coordinator, request settings and subscription ID cannot be changed afterward. Funding/service management uses that provider's reviewed procedures, not an invented PoPL retry function. Do not seal against an unavailable/unqualified provider.

Monitor `RandomnessRequested`, `RandomnessReceived`, `TraitsFinalized`, subscription funding and oldest unanswered request. Authenticated fulfillment stores words; anyone can call `NFT.finalizeTraits(tokenId)` **in mint-ordinal order**. A fulfilled request awaiting finalization is different from a missing provider response. Read `nextToFinalize()` and `tokenAtOrdinal(ordinal)`; never guess token IDs from ordinal numbers. Fixed 600/300/100 quotas and prepared artwork draw remain unchanged.

The read API offers `GET /v1/mint-readiness`: confirmed minted/revealed counts, unfinished draws, earliest request/epoch, whether it awaits randomness or finalization, and the separate on-chain `mint_paused` flag. `new_minting_stopped` combines this flag with lifecycle controls; it is not a provider or gas-availability check. It checks inventory consistency and canonical deployment. It does **not** verify subscription funds, provider liveness, elapsed pending time, escrow compatibility or full handoff readiness; those fields are explicitly unverified. Correlate request/fulfillment events for latency and alert thresholds. The endpoint does not deploy a monitoring service or resume the paused chat monitor.

For a provider outage, governance calls `NFT.setMintPaused(true)` through the controller, with no waiting period. Verify `NFT.mintPaused()` and `MintPauseChanged(true)`. This blocks new NFT mint/randomness requests, including direct Vault callers; the complete transaction reverts without spending the mint payment. Pending original fulfillment and ordered finalization continue. Existing revealed NFTs can still activate/top up, transfer, claim and undergo LP maintenance when their independent guards permit. Pausing during the NFT receiver callback also rolls back that mint atomically.

To restart, qualify provider funding/liveness and reconcile pending requests; governance calls `NFT.setMintPaused(false)`, verifies the event/getter and simulates the complete mint. It does not clear global pause, preparation, canonical locks, exhausted supply or broken provider conditions. The mint switch is an operational setting, not an exported economic entitlement: for a replacement explicitly set/review the successor's desired state before locking it for import (fresh deployment default is `false`). It is not copied from the source and is not automatically cleared by handoff/abort. Existing sealed deployments without this function cannot acquire it by configuration.

There is **no coordinator swap, reroll, administrator-selected trait or pending-request transfer**. Ordinary LP pool migration/rebalance has no reveal-completion requirement. Global pause remains the wider incident control; hiding the Mint button alone does not stop callers. A permanently unanswered draw still blocks whole-collection replacement.

Artwork URI is fixed once configured: `setBaseURI` can populate an initially empty base only once before sealing. Keep the same IPFS/Arweave content available with redundant pinning; a gateway UI change does not change canonical metadata. Permissionless `refreshMetadata(tokenId)` or `refreshMetadataRange(firstOrdinal,lastOrdinal)` (maximum 50 inclusive ordinals) emits ERC4906 notifications. The optional keeper watcher can request refreshes, but marketplace caches choose when to refetch. Current LP valuation drives evolution and can fall; activation eligibility does not disappear just because artwork downgrades. Never replace unavailable prices with zero or lifetime deposits.

## Whole-collection replacement

This is a separately reviewed operation, not routine LP maintenance. Current implementation supports **same-chain** replacement only, with every minted draw finalized, buckets parked/None, no conflicting plans and no historical legacy bridge traffic. Read [the exact handoff sequence](CANONICAL_HANDOFF.md) before any attempt.

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
