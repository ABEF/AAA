# Development and operating procedures

**Current candidate, reviewed 2026-10-25:** actual native ETH accounting/routing V2
and dual-source pricing V2 are implemented. The selected hookless ETH/ZZZ pool
earns conventional LP fees; Pons creator funding is optional historical scope.
Typed single-hop v3 and hookless static-fee v4 conversions are supported, subject
to actual route/feed qualification. Default execution limits are 2% contributions,
1% earned-balance conversion and 3% maintenance; immediate governance can set
each to at most 10%. Read the current and captured policy, never assume defaults.

**Production NOT APPROVED.** This guide describes current operations, not a
deployment authorization. Retired bridge/pair-router instructions have been
removed from this runbook; historical evidence remains in [reports](../reports/README.md).
Existing WETH deployments, journals and old schemas retain their original meaning.

Start with the [operator manual](OPERATOR_MANUAL.md) for management decisions, exact calls, stop/restart and recovery. Keep it synchronized under [the maintenance rules](TODO_WORKFLOW.md).

Use the [feature/evidence reference](IMPLEMENTATION_STATUS.md) for source-bound
implementation status, [sole Todo](../TODO.md) for acceptance criteria and
[release record](RELEASE_CHECKLIST.md) for approval. Exact-revision CI, full
independent static review, actual provider/venue tests and operating rehearsals
must be checked separately; old green workflows do not verify later sources.

## New liquidity operating profile

The [placement/idle guide](IDLE_AND_DUST.md) and [range policy](RANGE_POLICY_UPDATES.md)
cover two-pass placement, safe idle-only reinvestment, explicit ZZZ-price orientation
and disabled-by-default reviewed two-width keeper selection. Use range_policy_version1
with matching runtime and per-pool metadata for new inverse/adaptive profiles.
Historical deployments/journals keep their original raw orientation and loss cap.
No existing service is changed by this source update.

## Build and configuration

Install the pinned Foundry toolchain and Node/npm on a networked development host. Run `scripts/install-deps.sh`, inspect the resolved lockfiles, then `scripts/verify.sh`, the pinned Slither review gate and explicit fork command in [development setup](DEVELOPMENT.md). Retain compiler output, runtime sizes, seeds and results. The static gate checks review coverage and source identity; it does not certify accepted trust assumptions.

Copy the blocked [schema-5 example](../config/production.example.json) to an
operator-owned inventory. Follow [preflight](PRODUCTION_PREFLIGHT.md) and run:

```bash
python3 scripts/validate-production-config.py --config YOUR_CONFIG --expected-commit YOUR_RELEASE_COMMIT
```

The example has deliberately unset public identities/services/evidence and must
fail. The offline validator checks supplied records, not their authenticity.
Use independent confirmed observations, complete event histories, exact deployed
runtime/initcode and dependency/proxy reviews. Inventory 17 core contracts and
all 15 schema-5 helper bindings, configured converters/executors and any optional
per-bucket inboxes as described in [addresses](DEPLOYMENT_ADDRESSES.md). Include
explicit accounting/routing/pricing versions, chain/genesis/block anchors, assets,
source pairs/ages/independence, current loss limits and complete route policies.

`DeployCore.s.sol` is **local-only** (31337/31338) and deliberately unsealed. It
does not install a retired bridge router or qualify production services. Separate
converter binding and deployment verification remain operator/release work. Do
not patch guards or relabel old state to make a template appear production-ready.

Configure reviewed pool/asset/dual-feed policies, fixed helper bindings, randomness
and permanent artwork before sealing. Read [post-seal controls](POST_SEAL_POLICY.md):
sealing fixes code, not all supported operating settings. It cannot add a missing
ETH/WETH algorithm or future-chain canonical transport. The current release uses
explicit source-chain custody for external token/chain conversion; integrated
bridging and remote NFT/reward transport are optional future scope, not launch gates.

For activation, enforce at least $100 lower-bound original source value; growth
requires at least $5 (and any stronger pool minimum). The captured contribution
limit applies across conversion and marginal LP placement together. At default
2%, at least 98% of upper-bound input value must be deployed as new lower-bound
LP value, excluding incumbent idle/compound. Network gas is separate. Direct
native input forwards exact ETH; v4 has no wrapper dependency. See [Entry](ACTIVATION_ENTRY.md),
[price security](PRICE_SECURITY.md), [typed routes](TYPED_V4_ROUTES.md) and
[execution policy](EXECUTION_LOSS_POLICY.md). Unsupported/infeasible routes fail;
there is no spot/peg/stale fallback or automatic cap increase.

A source contribution meeting the dollar minimum is not necessarily executable.
Fee, tick rounding, price impact and post-swap idle can make the marginal deployed
LP miss its captured floor even if retained LP plus idle exceeds that floor. The
[audit's thin-market example](../reports/preproduction-audit-20261025/REVIEW.md)
fails safely; it is not a live-depth observation. Require a complete fresh trace
before wallet review and reprepare after a confirmed approval. Do not relax the
floor or count incumbent/idle assets as new deployed LP to make a quote pass.
If final execution fails, Entry funds/LP changes revert, but previously mined
approval and network gas do not. Preserve the existing allowance, avoid repeating
confirmed approvals and let users revoke obsolete allowances through their wallet.

Public activation preparation/signing must remain blocked pending [review-time cap binding](EXECUTION_LOSS_POLICY.md#review-time-policy-binding-remains-open). Do not promise that the simulated contribution percentage is signed into the current Request. A governance change before inclusion can apply a higher cap; caller raw minima are separate.

For a source-price outage, [custody parking](CUSTODY_PARKING.md) is a separate governed recovery workflow: pause globally, obtain an exact bucket snapshot and independently review raw close minimums, then schedule the exact Migration request through the zero-delay controller. Execution must fit its ten-minute deadline window. Principal closes into attributed Vault balances, without creator-inbox synchronization or USD valuation. Keep upkeep disabled while Parked; existing funded claims and ownership rights remain. Unpause and use governed resume only after ordinary deployment prices recover, or propose an approved migration retaining remote-liability and backing checks. Actual venue/token/runtime failures may still block parking. Native V2 parking does not call a wrapper.

## NFT randomness, artwork and royalty setup

On the canonical chain, call `NFT.configureRandomness(coordinator,keyHash,subscriptionId,confirmations,callbackGasLimit,nativePayment)` exactly once before `Access.seal()`. Canonical sealing rejects missing randomness configuration. Use an independently verified proof-verifying coordinator on the actual selected chain, a funded subscription authorizing the NFT, appropriate finality and measured callback gas. No reviewed production coordinator or actual Robinhood fulfillment is supplied. The constructor artwork base, or the one-time `setBaseURI` for an initially empty base, must be a reviewed `ipfs://` or `ar://` root containing the matching artwork. Record `artworkBaseURI()`, all three immutable royalty/metadata/claim helper addresses/hashes and bindings, fixed provider/lane/subscription/payment parameters, current bounded future-request settings and staged fulfillment evidence in the release inventory.

Paid mint creates an unrevealed Dormant NFT and one request for two words. Monitor `requestOf(id)`, `mintOrdinalOf(id)`, `nextToFinalize()` and coordinator fulfillment. The callback stores words only. Anyone calls `finalizeTraits(id)` for the next ordinal before activation. Supply is capped at 1,000 with exactly 600 Commun, 300 Rare and 100 Legendary allocations; the first odds are 60/30/10 and later odds follow remaining quotas. Callback order cannot choose quota consumption order. Transfers preserve pending requests and finalized traits. There is no manual reveal, coordinator replacement, cancellation or reroll. `setRandomnessRequestSettings` can tune bounded confirmations/callback gas for future requests only; it cannot repair or reroll pending requests. A missing earlier fulfillment blocks all later reveals: rehearse this liveness risk before accepting mint payments.

The second VRF word consumes a fixed-inventory entry without replacement. Verify 58 palettes, four patterns, 200/500/300 color-style slots and all 2,784 renderer SVG paths. `scripts/prepare_ipfs_bundle.py` now prepares a verified reproducible upload archive, but its prepared bundle is **not uploaded or pinned**. Choose redundant pinning, independently verify the CID/import settings and every renderer path, and record retrieval/recovery evidence before configuring the immutable root. Website HTTP publication is not content-addressed production hosting.

The fixed 5% `royaltyInfo` receiver is `NFT.royaltyRewards()`, distinct from the mint recipient and LP creator inboxes. Marketplaces may decline royalty payments. Native ETH is admitted directly to this helper; additional exact-transfer ERC20 assets require reviewed governance-approved `NFT.addRoyaltyAsset(token)` admission, bounded to 16 ERC20s plus native ETH. All eligible royalties actually received go to activated Commun/Rare/Legendary at 1/2/3 weights, without an LP revenue split. Pending royalties are settled before new eligibility. Unclaimed funds follow current NFT ownership; prefunds and zero-eligibility receipts are reserved without an administrator sweep.

For OpenSea, after deployment independently verify the helper returned by `royaltyRewards()` and `royaltyInfo(id,salePrice)`, then configure that exact same-chain contract address and 5% in the collection's Creator Earnings settings. OpenSea documents a recipient/percentage setting; the current ERC-721/ERC-2981 candidate does not implement its ERC-721-C enforcement path, so payments remain optional. When a fulfilled Seaport order includes royalty consideration to that helper, the transfer occurs in the sale transaction. Verify collection-administration access and an actual staged paid sale, receipt, weighted holder claim and NFT transfer before launch. Admit each expected ERC20 payment currency, such as the reviewed WETH, before trading; pre-admission receipts are quarantined. Primary references: [OpenSea creator settings](https://support.opensea.io/en/articles/8867026-how-do-i-set-creator-earnings-on-opensea) and [Seaport consideration recipients](https://docs.opensea.io/docs/seaport-models). No production helper address exists yet.

Use `currentLPValue(id)` and `evolution(id)` availability flags rather than treating unavailable as zero live NAV. Home-chain marked LP/idle/compound share values can cross artwork thresholds upward or downward. Remote/in-flight or stale dependency states return explicitly unavailable valuation and labelled fallback artwork. Activation and royalty eligibility persist even below $100. `tokenURI` is dynamic, and reveal/contributions emit ERC-4906 events. Permissionless `refreshMetadata(id)` and `refreshMetadataRange(firstOrdinal,lastOrdinal)` emit notifications without reading prices. The inclusive range accepts at most 50 mint ordinals and emits individual events for their actual hashed token IDs. The optional keeper watcher described below detects market-driven stage/availability changes. Actual marketplace rendering/cache refresh and production operation remain unverified; Uniswap does not update these NFT caches. Claims and custody operations remain independent from metadata evaluation.

## External creator-payment setup

The creator sends funds to a dedicated per-bucket receiver rather than enumerating NFT holders. After sealing and activating a canonical bucket, governance schedules `FeeController.createRewardReceiver(bucketId, wrappedNative)` through its zero-delay controller. Review the bucket's permanent original currency pair and optional 18-decimal native wrapper first. One receiver per bucket is enforced; the factory's ceiling is sixteen but current Vault capacity permits at most four reachable home inboxes. These immutable helpers do not add a module binding or permit replacement after creation. No deployment or actual recipient address has been supplied here.

The selected pool uses conventional LP income. Only if discretionary external
funding is chosen, declare its reviewed plain-transfer/processing-time policy and
`received_funds_only` entitlement. Do not invent creator volume percentages or
turn [measurement proposals](REVENUE_SHARE.md) into payment authority. The creator
agreement/measurement tasks are conditional; authenticating any actual funding,
its currency and the complete receiver history is still required.

The canonical chain's `external_rewards` inventory must include `receiver_count`, complete `receivers` and exact-release `observation_evidence`. Derive the complete list from confirmed `RewardReceiverCreated` history and reconcile `Fees.rewardReceiverCount()`/`rewardReceiver(bucketId)` at the manifest observation block. External mode requires at least one canonical receiver; satellites contain none. Conventional-only mode cannot hide registered external receivers under the conventional label.

Each record includes `address`, immutable-specific `runtime_hash`, `bucket_id`, `home_pool_id`, `fees`, `token0`, `token1`, `wrapped_native`, `immutable_configuration=true` and `upgradeable=false`. The bucket hashes canonical chain/vault/original pool; the pair matches that original pool. Retain `observed_chain_id`, `observed_receiver`, `observed_fee_receiver`, `observed_block_number`, `observed_block_hash`, positive `observed_total_shares`, and `observed_bindings` for all five immutable getters. All observations use the same confirmed manifest block. `review_evidence` requires a named independent reviewer and exact release identity. For nonzero wrapping, `wrapper_review` includes the matching asset/address/runtime, `upgradeable=false`, `conversion=deposit:exact_1_to_1`, and release-specific evidence. A zero wrapper requires `wrapper_review=null`. Independently authenticate the underlying code, getters, event completeness and reviews; the offline validator only compares supplied records.

Published/indexed rewards and already funded local dust are checkpointed for incumbents. Unharvested venue fees and undelivered remote rewards retain collection/delivery-time collective membership; creator funds use processing-time membership. Review timing incentives separately from displayed historical fee estimates.

Publish only the checked immutable receiver and admitted currencies for the correct bucket. Native V2 sends actual ETH into the fee ledger without wrapping; an explicitly selected historical wrapper path retains its own dependency and currency identity. Direct ERC20/native receipt is pending until anyone calls receiver `sync()` or Fees `syncExternal(bucketId)`. Monitor `pending()`, processed `totalExternalFunded`, claim liabilities and segregated reserves separately. Processing remains allowed during pause and while LP is away; home compounding waits for compatible maintenance after return. Payments do not increment or clear remote transport obligations.

Before entry the Vault settles canonical dust across at most four historical buckets and processes registered inboxes under incumbent weights. Four home inboxes are reachable; the receiver factory separately permits sixteen. Checkpoint inventory supports 32 ERC20 LP currencies plus native ETH (33), and 16 ERC20 royalty currencies plus ETH (17). A stopped admitted LP asset or inbox dependency can still block entry. Qualify the combined workload and actual venue gas; raw prefunds/unsupported receipts follow quarantine rules and have no arbitrary rescue. See [funding semantics](EXTERNAL_REWARDS.md).

## Principal movement and future chains

Use [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md). Atomic `moveFunds`
requires the same actual ordered accounting pair. ETH/WETH are distinct and an
atomic boundary conversion is not implemented. A contribution-pool switch is a
separate deliberate configuration action after actual destination LP is checked.

For a normal or raw external exit: globally pause, review raw close minimums,
park, take a stable parked snapshot, approve the exact plan/recipient/mode and
then execute. Preserve the original rounded-up normal floor; parking and later
approval are not automatically one cached on-chain loss budget. Normal exit
converts principal to ZZZ. Raw exit is a separately approved no-swap transfer of
actual assets under raw minima, without a USD guarantee; it is never a fallback.

Pause blocks ordinary contributions/maintenance but **permits separately approved
pause-only custody departure**. Pause is not a custody freeze. Governance trusts
the external recipient's custody and return; the protocol cannot compel it.
Before sending, document local completion/full original-asset recovery and any
finality verifier. No real cross-chain verifier/provider/remote ledger is supplied.

Retired bridge/router/pair-executor APIs cannot be reactivated with a configuration
change. NFT ownership/reward relocation is the separate [canonical handoff](CANONICAL_HANDOFF.md).
Future-chain finality, closure, transport and lineage remain pre-seal work; post-halt
recovery is deferred. Stop at the actual implemented boundary.

## Keeper

Python 3.11+ and a Unix host are expected. Copy `keeper/config.example.json`, fill real local/testnet settings and leave `reviewed_for_live_use=false`.

```bash
python3 -m keeper.monitor --config keeper/config.local.json --once
```

### Reward timing and maintenance schedule

Rewards do not accrue on a fixed per-minute clock. Supported venue fees become funded holder balances when harvested and allocated; creator payments become funded balances when their immutable inbox is processed with `syncExternal`. The 80/10/5/5 split applies to those actual receipts, with raw-unit rounding as documented in [economics](ECONOMICS.md). Optional external funding timing is chosen by its payer; it is not required for the selected hookless pool. No keeper can manufacture missing revenue.

The example `interval_seconds=600` checks for work every ten minutes. This is a polling interval, not a guaranteed transaction schedule. `maintenance.harvest_interval_seconds=14400` makes conventional harvesting eligible every four hours since its last confirmed keeper harvest; other actions and pending confirmations may delay it. External inbox processing is attempted when a scan finds a pending payment. Conventional fees are also harvested within relevant on-chain entry/maintenance operations.

Rebalancing is conditional on `Strategy.needsRebalance(bucketId)`: the bucket must be active, operations enabled, `minRebalanceInterval` elapsed, and either the oracle-reference price has moved by at least `triggerBps` or the approved range differs from current LP ticks at the recorded center. [Range-policy application](RANGE_POLICY_UPDATES.md) uses the existing governance-approved configuration and ordinary keeper call; successful replacement clears the mismatch. Configuration/position changes require resimulation, and eligibility is not a guaranteed execution time. Execution additionally checks oracle freshness, spot deviation, slippage, minimum liquidity, deadlines, roles and pause state. Production `rangeBps`, `triggerBps`, `minRebalanceInterval` and execution bounds remain unset in the release inventory; the ten-minute polling example does not choose them. Rebalance once per shared pool, regardless of its NFT count. Compounding separately requires the configured raw-token reserve threshold. Backtesting and actual operating costs remain release gates; rebalancing does not eliminate impermanent loss.

Royalty `claimable` includes pending admitted receipts at current weights; direct royalty claims synchronize them. LP claims use already allocated balances and do not harvest/process inboxes. Both ledgers retain owner-only single-NFT/asset claims with no periodic window. The immutable [claim router](CLAIM_ROUTER.md) now combines **1–32 operations** across NFTs/assets/ledgers in one atomic owner transaction, with duplicates rejected and direct owner payouts. Verify `NFT.claimRouter()` and its `access/nft/royalties` bindings; simulate and chunk actual batches, since one failure reverts all. It does not hold user funds, accept approvals or authorize another recipient. Strategy pause does not pause claims. The public website remains simulated. Separate Anvil integration is not public wallet or marketplace qualification.

### Optional metadata notifications

`metadata_refresh` is disabled in the example. To enable it on a reviewed canonical-chain test deployment, configure its exact `nft` address outside the existing `contracts` map and its reviewed runtime Keccak hash at `code_hashes.nft`. Keep the existing shared-pool deployment identity and pending records intact. The watcher verifies controller/NFT/Vault bindings, canonical chain, seal, immutable limits and ordinal-to-token identities at a pinned confirmed block. It rotates through at most 50 NFTs per scan, comparing evolution stage, valuation availability and trait readiness; this separate notification scan never rebalances individual NFTs.

`max_refresh_batch` bounds a notification to 50 inclusive mint ordinals. The watcher uses the existing simulation, serial signer, gas/daily budgets and durable pending-transaction recovery. A baseline advances only after a matching successful confirmed receipt, canonical observation/receipt anchors and bounded observation age. It rereads the exact NFTs at the receipt block and checkpoints that state rather than the earlier trigger. Dry runs, failed or ambiguous submissions, reorgs and expired observations do not count as notified; invalidated triggers remove previous range fingerprints to force a fresh attempt. Initial scans have no invented baseline. Changed-work cursors advance after the selected nonwrapping notification range so small batches and wraparound cannot starve trailing NFTs. Pool maintenance and metadata alternate priority, and metadata notifications can continue during strategy pause. Disabling new scans still reconciles an existing metadata transaction. The fingerprint covers stage, availability and reveal, not every within-stage USD-value change. Review logs, RPC load and latency with actual feeds before live operation; external caches decide when to refetch after an ERC-4906 event.

The shared-pool keeper discovers every on-chain group using `bucketCount()` and `bucketAt(index)`. There is no NFT list: one active pool containing 1,000 NFTs is maintained through one group operation. Configure `bucket_discovery.maximum_count` and `max_per_cycle` as reviewed inventory and scan bounds. A durable round-robin cursor advances before a live submission, so a busy first pool cannot starve the others. Scanning and RPC work grow with the number of groups rather than NFT supply; the current Vault caps all historical local groups at 4, including imported custody. Returning an existing bucket reuses its slot. The keeper also retains a separate defensive ceiling of 1,000 groups per cycle; that ceiling does not enlarge the contract limit.

`maintenance` supplies defaults for all discovered groups: `sync_external_rewards`, `minimum_liquidity`, `compound`, `minimum_compound_units`, `harvest`, `harvest_interval_seconds`, and reviewed `reward_routes`. Optional `bucket_overrides` uses decimal bucket IDs only to override these defaults; it does not limit discovery. The keeper verifies the group ABI, positive shares, pool occupancy, pool-key hash, and actual local assets from the pool registry before attempting work. It never trusts caller-supplied token lists or canonical home-token addresses for satellite compounding. External synchronization defaults to enabled and requires an explicit boolean. The keeper reads the receiver from Fees, validates fees/bucket bindings and its two-amount pending ABI, then targets Fees.syncExternal only when funded amounts are pending. It continues this bounded scan during pause and remote custody; while paused it suppresses ordinary LP maintenance and buybacks. It does not initiate a governed custody exit. The existing nonce, signer, simulation, confirmation and budget guards apply unchanged. The example uses a minimal liquidity floor of 1; review per-pool bounds and raw-token compound thresholds for the deployment. On-chain oracle, price and slippage guards remain mandatory.

Buyback tasks supply a fee token, exact amount and direct approved pool ID. Legacy remote counters or configuration cannot re-enable removed transport selectors. LP maintenance runs only for Active groups; do not configure new remote reward routes on this candidate. Principal migrations and import acknowledgements remain deliberate reviewed operator calls. Discovery does not approve new routes or sign migration proposals.

Configurations containing the old `positions` NFT list are rejected. Persistent state carries `accounting_model=shared-pools-v2`; an older state file must be reviewed and deliberately migrated without deleting or bypassing any pending transaction. No automatic state reset is allowed.

For a reviewed test deployment, live mode additionally requires `--live`, reviewed runtime hashes for configured contracts, a matching encrypted `cast` wallet and private regular keystore/password files. Use a dedicated low-balance account with only keeper permissions. Do not use the governance wallet.

The program serializes transactions and writes intended nonce, destination, calldata and value durably before invoking the signer. Its pinned `cast send` call uses raw calldata as the positional argument, an explicit sender and a cleaned environment; the invalid old `--data` form has been removed. State replacement uses an exclusive random private temporary file and fsync rather than a predictable temporary path. A timeout/error leaves an ambiguous pending record. It must not be deleted just to force a retry.

```bash
python3 -m keeper.monitor --config keeper/config.local.json --resolve-pending 0xREVIEWED_TRANSACTION_HASH
```

This recovery path verifies transaction/receipt hash identity, sender, nonce, destination, calldata, value, confirmations and canonical receipt block before accepting it as the pending submission. An invalid candidate must not rewrite the pending hash. If the transaction was never broadcast or was replaced/dropped, investigate the account across trusted nodes before a human edits recovery state; there is no automatic blind nonce replacement. Preserve state files and audit logs. Signer/RPC/rollup estimates still require an actual staged network rehearsal.

Receipt recovery requires canonical quantities, status 0/1, matching hash,
sender, target, nonce, calldata, value, inclusion block/index and chain identity.
The keeper now persists `pending.fee_review` schema 1 **before signing**, capturing
gas limit, signed maximum fee, L1 allowance, total maximum cost and fee semantics.
Signed gas/caps must match that review. For type 2, execution price is derived as
`min(maxFeePerGas, baseFeePerGas + maxPriorityFeePerGas)` using the inclusion block;
the RPC's `effectiveGasPrice` is retained separately, not trusted as spend. Legacy
reported price must agree with signed `gasPrice`. L1 data cost must fit the captured
allowance and reviewed included/separate policy; required missing data fails closed.

Canonical depth/hash/timestamp and fee basis are rechecked before an atomic state
checkpoint. Actual reverted transactions consume gas but not reverted native value.
Confirmed costs are charged once to the inclusion block's UTC day. Current settings
do not reinterpret an already reviewed pending operation.

**Upgrade/recovery stop:** an older pending record without its original fee review
is preserved. When receipt/candidate verification reaches the missing review, it emits `pending_fee_review_required`; an unknown hash or unmined receipt may first report ordinary pending/ambiguous status. Stop new signing, archive the
state/logs and inspect the exact hash and original signed transaction against trusted
nodes and the original review evidence. Do not derive historical limits from today's
configuration, insert guessed values, delete pending state or resend. If the original
review cannot be established, use reviewed manual accounting/signer rotation under
[the recovery runbook](KEEPER_RECOVERY.md); automatic migration is not provided.

Gas-price, per-transaction and daily budgets apply to estimates; configure a conservative L1-fee allowance on rollups. Actual confirmation costs update accounting. These estimates are not a guarantee against a malicious RPC or changing chain-specific fee rules.

`keeper/zzz-keeper.service` is a hardening template, not an installed service. Adjust executable/config paths and service user. It defaults to dry run. Production monitoring should alert on staleness, oracle failures, missing confirmations, ambiguous nonces, missed keeper cycles, low native balance, discovery-limit breaches and repeated skipped shared pools.

## Indexer

```bash
python3 -m indexer.monitor --config indexer/config.local.json --once
```

Set a known deployment start block and parent hash, appropriate confirmations and reorg bound, and only reviewed contract addresses. Each SQLite cursor is tied to its chain, starting point and tracked contract set. Changing that identity requires an explicit rescan/new database.

Logs, block headers and the cursor commit atomically. Orphan blocks/logs are rolled back to the common ancestor. A reorg deeper than the configured safety bound halts rather than guessing. Raw events remain available when a signature is unknown or not projected into application views.

The SQLite database is an off-chain cache, not proof of ownership. Claims and custody must rely on contracts. Back up the database/configuration; a confirmed-block rescan must reproduce it. Verify multiple RPC sources for sensitive operational decisions.

### Confirmed read API and revenue measurement

The unhosted [read API](FRONTEND_API.md) serves exact confirmed NFT state/claimable balances on loopback. Optional [history configuration](FRONTEND_HISTORY.md) adds `GET /v1/wallets/{address}/nfts` and cumulative per-asset LP-plus-royalty claims. Keep indexer creation/start/parent/contract identity fixed and its full block/log coverage complete through the API target; compare wallet count/owners to on-chain state and preserve raw receipt evidence. Missing config is explicit unavailability; stale/orphan/malformed history fails the whole request. Processed lifetime/24h earnings and optional current-price USD are implemented; see [earnings history](EARNINGS_HISTORY.md). Use the read-only [independent-provider comparison](HISTORY_AUDIT.md) before serving live history. Actual full ingestion, prices and provider/load qualification remain open. Stage HTTPS proxy/load/rate limits, independent backfill comparisons, finality/reorg handling and recovery before live website integration.

Use `python3 -m zzz_ops.revenue_share snapshot --config COLLECTOR.json --block BLOCK --output SNAPSHOT.json` for a reviewed local-position sample; `calculate --input WINDOW.json --output REPORT.json` evaluates a complete window without signing or moving funds. Archive block/hash/tick/liquidity provenance and full raw fee receipts; sampled ratios do not reconstruct within-swap tick crossings. Obtain creator approval before using either proposed policy and reconcile real payments independently.

## Incident and alert rehearsal

Monitor confirmed-head lag, stale/unavailable source pairs, low gas funds, ambiguous
nonce age, reverted or uneconomic maintenance, repeated skipped pools, undistributed
funding and liabilities versus actual balances. Include external-custody plans,
raw/normal mode, exact sent currencies, original captured floors, canonical state
and unavailable valuations. A ten-minute check is not a rebalance SLA.

Preserve observations, logs, pending journals and budgets before intervention.
Stop the keeper signer if key/RPC identity is uncertain. Apply the narrowest
[stop control](OPERATOR_MANUAL.md#stop-controls); pause does not prohibit an approved
custody exit. Do not erase financial checkpoints to restart a process. Rebuild
indexer history from a verified deployment checkpoint and reconcile ownership,
raw claims/conversions/funding and original-currency backing before serving it.

Rehearse outages/restarts, process-lock and disk-write failures, backup restoration,
RPC failover, reorg/finality drift, signer loss/rotation and externally custodied
assets. Linux ownership/locking, provider honesty, chain fee semantics and actual
capacity remain qualification gates. Read-only health monitoring cannot sign,
recover keys, establish uninterrupted uptime or qualify production.

## Keeper restart and recovery gates

Follow [KEEPER_RECOVERY.md](KEEPER_RECOVERY.md) and the [internal review](../reports/keeper-recovery/REVIEW.md) before operating this candidate. Live startup requires reviewed fee accounting and intact nonce/receipt checkpoints. Never delete pending state or budgets to recover; restore and reconcile, or use approved signer rotation. Health output is separate from transaction state, and off-host alerts/backups plus actual operating rehearsals remain required. The systemd example remains dry-run.

## Economic-rights operating review - 2026-10-16

Use the [internal review](../reports/nft-rights-audit/REVIEW.md) and its
[executed tests](../reports/nft-rights-audit/VERIFICATION.md) with this runbook.
Claims use current NFT ownership and actual funded balances. Approved transfer
operators cannot claim merely through approval; escrow that becomes the owner
has holder rights. Failed EVM transactions also revert their events: inspect
receipts/errors and keeper logs, not just successful event streams.

Review each admitted reward token's availability, upgrade and blacklist powers.
An unreadable optional royalty currency defers new eligibility for that currency
while activation and healthy currencies continue. Recovery allocates unseen old
receipts to the earlier cohort before newcomers join. Other failures, including
an optional LP-funding inbox or admitted token/venue failure, can still block entry.
Do not bypass incumbent accounting or substitute an unavailable amount with zero.
Run maintenance per shared bucket; all 1,000 NFTs need no per-NFT rebalance loop.
The current capacity is four historical buckets. Retired bridge APIs cannot be
re-enabled. Remote custody requires independently qualified recipient/transport,
finality and closure verification, backing and full-return procedures; none is
supplied by local capacity reservation.

This review does not start/alter keeper services or complete the sustained soak,
production RPC/fee qualification, physical host-loss or key-rotation rehearsals.

## Independent emergency controls

Use governed `PoolRegistry.disablePool(poolId,stopDeposits,stopOperations)` to
restrict a pool without depending on healthy prices/tokens/venue. It can only
clear flags; full configure/configureNative validation is required to reopen.
Use governed `NFT.setMintPaused(true)` for an isolated mint/provider incident;
existing reveals and NFT/LP rights keep their independent guards. Both operations
respect preparation/canonical configuration locks and add no governance delay.
Follow the [operator manual](OPERATOR_MANUAL.md#stop-controls) for exact calls,
receipts, callback rollback, successor-state review and deliberate restart.
