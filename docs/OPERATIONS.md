# Development and operating procedures

**No mainnet launch or funded deployment is approved.** The [current readiness review](../reports/PRODUCTION_READINESS.md) includes real Uniswap dependency fork checks and internal hardening. It does not establish a production bridge, approved reward source, authentic deployment configuration or independent audit.

## Build and configuration

Install the pinned Foundry toolchain and Node/npm on a networked development host. Run `scripts/install-deps.sh`, inspect the resolved lockfiles, then `scripts/verify.sh`, the pinned Slither review gate and explicit fork command in [development setup](DEVELOPMENT.md). Retain compiler output, runtime sizes, seeds and results. The static gate checks review coverage and source identity; it does not certify accepted trust assumptions.

Copy `config/production.example.json` to an operator-owned configuration and complete its schema-version-3 shared-pool inventory. Run `python3 scripts/validate-production-config.py --config YOUR_CONFIG --expected-commit YOUR_RELEASE_COMMIT`. The committed example must fail: it includes pending decisions and the unsupported requested market. The validator is offline/read-only, validates consistency and evidence references, and never signs or contacts a chain. Operators and external reviewers must verify the claimed code, constructor values, roles, observations and evidence authenticity independently. A `ready` manifest result does not authorize deployment or funded use.

Every principal route additionally declares `bucket_id` and `source_pool_id` as reviewed migration scope. These fields do not change the on-chain `Route` hash. Both its source pool and destination pool must appear in their chain's `bucket_reservations` inventory for that same bucket. A reservation records `pool_id`, `bucket_id`, `home_chain_id`, `home_vault`, and `home_pool_id`; its bucket must equal `uint256(keccak256(abi.encode(homeChain, homeVault, homePoolId)))`. The original home pool remains its permanent identity even after custody moves to another pool.

At each chain's exact `observed_block`, independently query `Vault.poolBucket(pool_id)` and retain `observed_chain_id`, `observed_vault`, `observed_bucket_id`, `observed_block_number`, and `observed_block_hash`. The observation must match the reviewed permanent reservation and the inventory snapshot. `review_evidence` requires the ordinary passing exact-release commit/SHA-256/reference fields, plus `independent=true` and a named `reviewer`. The gate rejects missing, mismatched or duplicate reservations and incompatible origin assets. Its checks compare supplied records; an operator and independent reviewer must authenticate the underlying observations. An initial launch with migration disabled and no routes may use an empty reservation list.

The supplied `DeployCore.s.sol` template is restricted to local chain IDs 31337/31338. It expects existing reviewed local Uniswap contracts, creates the fixed `ZZZBridgeRouter`, and binds 16 modules to the access controller: 17 modules including that controller. It deliberately does not seal configuration or choose a production provider. It was not executed here.

For each deployment, record: chain ID and canonical NFT chain ID; all 17 contract addresses and runtime bytecode hashes including immutable constructor values; the mint-proceeds recipient; the adapter's fixed transport router; PosM/PoolManager/StateView/Permit2 identities; token decimals and code/proxy authorities; USD feed denomination/heartbeat; sequencer feed; governance/guardian/keeper roles; supported burn mechanism; complete router policy registration IDs and outbound state; and every approved provider/channel policy and principal, source-completion ACK, canonical-location ACK, and reward route.

The router has no policy-count or enumeration getter. Derive `bridge_router.registered_policy_ids` from the complete verified `PolicyRegistered` event history, starting at the deployment block and ending at the manifest's confirmed observation block/hash. Reconcile reorgs, retain disabled historical policies, and independently verify each ID using `policyExists`, `policy` and `outboundEnabled`. Derive `policy_count` from the unique complete ID list and `outbound_policy_count` from its locally sourced enabled policies; do not label an incomplete set of individually queried IDs as the full inventory. Every observed ID must appear in global `transport_policies`, and every local endpoint policy must be listed. Remote-only registrations are allowed only on the canonical chain and must correspond to reviewed principal graph metadata.

Configure feeds first, reward assets next, and pools next. All required local identities must match module bindings, including `Ids.TRANSPORT` for the router and the adapter's immutable `transport()` getter. Review dependency ownership/proxy powers as well as their current code hashes. Seal only after an independent deployment review. Sealing fixes the 16 bindings and revokes bootstrap; provider policies and routes can subsequently be added through the fixed governance timelock. The router and adapter are never replaced to select a future bridge.

Mint, activation, and holder top-ups require `seal()`. Verify the exact 0.05 ETH mint price, isolated constructor-selected recipient, and the $500 actually deployed LP activation minimum on a test deployment. There is no general emergency rescue or admin withdrawal after sealing. A mistaken token/route/provider setting can strand capital indefinitely.

## Migration-disabled initial launch

No bridge SDK/provider wrapper is currently supplied. An independently approved initial deployment can keep migration disabled: bind the audited fixed router, register no policies/providers/routes, verify zero registered and outbound policies, and seal the system. An unknown route or absent policy must fail before a successful principal transfer. A future bridge is selected by adding a reviewed policy and a new route through governance, rather than changing custody code or introducing principal redemption.

The manifest uses `migration.enabled=false`, empty `transport_policies` and `routes`, empty per-chain `providers`, an empty complete `bridge_router.registered_policy_ids` list, and observed zero `policy_count`/`outbound_policy_count`. Only the canonical chain is required in this initial inventory. Retain `migration.future_onboarding_evidence`, explicit `disabled_scope_approval`, router observation evidence, and all ordinary economics, oracle, audit, governance, Uniswap, staging, gas and operating evidence. Disabling migration does not resolve the pending Robinhood reward choice or make its native/hooked/zero-core-fee pool compatible.

This is an initial-launch scope. A system that has already used a bridge must retain its old policy, provider, route and in-flight message records when disabling new sends; it is not equivalent to the empty initial inventory. No timeout permits a principal refund.

## Future provider and channel onboarding

1. Implement and independently review the actual SDK/provider wrapper, including message-origin authentication, finality, token backing/equivalence, exact delivery, replay handling, fees, and retry/cancellation behavior. Reproduce staged provider-specific deliveries and failures on the chosen chains. Mocks and a generic interface do not establish these properties.
2. Record the complete `TransportPolicy`: `providerId`, source chain/router/provider/code hash/channel configuration hash, destination chain/router/provider/code hash/channel configuration hash, `channelId`, and `reviewHash`. The policy ID is `keccak256(abi.encode(policy))`. On each participating chain, verify the local wrapper's `router()` and `configurationHash(channelId)` getters and runtime code against the reviewed pins; verify the counterpart independently. The review hash must identify the retained review evidence.
3. Schedule exact `registerPolicy(policy)` calls through each governance timelock. For an onward satellite hop, also register the remote policy on the canonical chain as needed for graph approval. Registration is append-only and starts with outbound sends disabled. Record policy events and immutable metadata on every chain.
4. Register all required economic routes with `add(route, policyId)`. Their identities are `keccak256(abi.encode(route, policyId))`; the registry permanently binds each route to that policy. A different provider/channel policy yields a new route ID even for the same chain/pool hop. Do not mutate an old route, rebind its provider, or select a mutable default bridge.
5. Retain schema-3 per-chain wrapper inventories (`provider_id`, `channel_id`, address, runtime hash, router, configuration hash, immutability/authority review and integration evidence), permanent bucket reservations, the complete policy inventory, exact policy-to-route/bucket bindings, and counterpart observations. `migration.enabled=true` requires `evidence.multi_chain.kind=provider_staged_multichain`; each wrapper's integration record must declare `kind=provider_staged_delivery` and identify its exact provider, channel and chain. These explicit claims must be independently authenticated; they cannot relabel mock/model tests as real delivery evidence. All existing release gates remain required. Check principal, ACK/home-ACK and historical reward paths before use.
6. After review and timelock notice, explicitly call `setOutboundEnabled(policyId, true)` on its source router. Recheck source wrapper pins, destination custody, equivalent assets and route enablement. Only then schedule a separate economic migration; that move retains its additional two-day delay.

Runtime code hashing cannot prove that a wrapper is not a proxy, that its getter is honest, or that external bridge contracts/configuration cannot change. Review the implementation, channel immutability, delegatecall/proxy mechanisms, upgrade administrators, and every external authority that can alter authentication, backing or custody. Record accepted trust assumptions; refuse a mutable wrapper/configuration as an immutable policy endpoint. Remote metadata is reviewed evidence, not a cross-chain proof. A timelock gives notice and does not make an unsafe provider safe.

`setOutboundEnabled(policyId, false)` prevents new sends for that policy. It does not remove the policy or reject authenticated pending inbound settlement. The router retains the original endpoint/configuration pins and adapter nonce domain; old receipts and funded rewards must still reconcile against their original policies and routes. Inbound completion also remains available during a local strategy pause. These rules do not provide recovery from a provider that loses custody or ceases to deliver.

When rotating providers, retain disabled old policies, wrappers and routes in the complete schema-3 inventory. Mark historical/inbound-only routes explicitly `enabled=false` while preserving their original route/policy identities, bucket scope, permanent reservations, review and delivery evidence. Active routes require an explicitly enabled source policy. An enabled-migration release must contain at least one active principal route and active ACK/home-ACK/reward paths for its active principal moves; a disabled historical route cannot satisfy a new outbound obligation. Historical principal records remain attributable without promising new sends. Disabling a route cannot erase pending authenticated inbound completion or turn off the SDK/audit requirements for providers still represented in the inventory.

## Keeper

Python 3.11+ and a Unix host are expected. Copy `keeper/config.example.json`, fill real local/testnet settings and leave `reviewed_for_live_use=false`.

```bash
python3 -m keeper.monitor --config keeper/config.local.json --once
```

The shared-pool keeper discovers every on-chain group using `bucketCount()` and `bucketAt(index)`. There is no NFT list: one active pool containing 1,000 NFTs is maintained through one group operation. Configure `bucket_discovery.maximum_count` and `max_per_cycle` as reviewed inventory and scan bounds. A durable round-robin cursor advances before a live submission, so a busy first pool cannot starve the others. Scanning and RPC work grow with the number of groups rather than NFT supply; at most 1,000 groups can be scanned in one cycle.

`maintenance` supplies defaults for all discovered groups: `minimum_liquidity`, `compound`, `minimum_compound_units`, `harvest`, `harvest_interval_seconds`, and reviewed `reward_routes`. Optional `bucket_overrides` uses decimal bucket IDs only to override these defaults; it does not limit discovery. The keeper verifies the group ABI, positive shares, pool occupancy, pool-key hash, and actual local assets from the pool registry before attempting work. It never trusts caller-supplied token lists or canonical home-token addresses for satellite compounding. The example uses a minimal liquidity floor of 1; review per-pool bounds and raw-token compound thresholds for the deployment. On-chain oracle, price and slippage guards remain mandatory.

Buyback tasks supply a fee token, exact amount and direct approved pool ID. Historical funded satellite rewards can still be sent for Active, Outbound, Remote and Inbound groups, using operator-reviewed `reward_routes`; LP maintenance runs only for Active groups. Principal migrations and import acknowledgements remain deliberate reviewed operator calls. Discovery does not approve new routes or sign migration proposals.

Configurations containing the old `positions` NFT list are rejected. Persistent state carries `accounting_model=shared-pools-v1`; an older state file must be reviewed and deliberately migrated without deleting or bypassing any pending transaction. No automatic state reset is allowed.

For a reviewed test deployment, live mode additionally requires `--live`, reviewed runtime hashes for configured contracts, a matching encrypted `cast` wallet and private regular keystore/password files. Use a dedicated low-balance account with only keeper permissions. Do not use the governance wallet.

The program serializes transactions and writes intended nonce, destination, calldata and value durably before invoking the signer. Its pinned `cast send` call uses raw calldata as the positional argument, an explicit sender and a cleaned environment; the invalid old `--data` form has been removed. State replacement uses an exclusive random private temporary file and fsync rather than a predictable temporary path. A timeout/error leaves an ambiguous pending record. It must not be deleted just to force a retry.

```bash
python3 -m keeper.monitor --config keeper/config.local.json --resolve-pending 0xREVIEWED_TRANSACTION_HASH
```

This recovery path verifies transaction/receipt hash identity, sender, nonce, destination, calldata, value, confirmations and canonical receipt block before accepting it as the pending submission. An invalid candidate must not rewrite the pending hash. If the transaction was never broadcast or was replaced/dropped, investigate the account across trusted nodes before a human edits recovery state; there is no automatic blind nonce replacement. Preserve state files and audit logs. Signer/RPC/rollup estimates still require an actual staged network rehearsal.

Gas-price, per-transaction and daily budgets apply to estimates; configure a conservative L1-fee allowance on rollups. Actual confirmation costs update accounting. These estimates are not a guarantee against a malicious RPC or changing chain-specific fee rules.

`keeper/zzz-keeper.service` is a hardening template, not an installed service. Adjust executable/config paths and service user. It defaults to dry run. Production monitoring should alert on staleness, oracle failures, missing confirmations, ambiguous nonces, missed keeper cycles, low native balance, discovery-limit breaches and repeated skipped shared pools.

## Indexer

```bash
python3 -m indexer.monitor --config indexer/config.local.json --once
```

Set a known deployment start block and parent hash, appropriate confirmations and reorg bound, and only reviewed contract addresses. Each SQLite cursor is tied to its chain, starting point and tracked contract set. Changing that identity requires an explicit rescan/new database.

Logs, block headers and the cursor commit atomically. Orphan blocks/logs are rolled back to the common ancestor. A reorg deeper than the configured safety bound halts rather than guessing. Raw events remain available when a signature is unknown or not projected into application views.

The SQLite database is an off-chain cache, not proof of ownership. Claims and custody must rely on contracts. Back up the database/configuration; a confirmed-block rescan must reproduce it. Verify multiple RPC sources for sensitive operational decisions.

## Deliberate migration procedure

1. Review compatible destination runtime code and custody/proxy authorities, economically equivalent tokens at identical decimals/nominal units, and actual provider funding/finality/retry behavior. A timelock notice is not proof of perpetual destination custody.
2. Onboard any missing immutable provider/channel policies and append-only principal, source-completion ACK, canonical-location ACK, and reward routes through each deployment's governance timelock. For a satellite B-to-C hop, register its remote-only policy and principal graph edge on the canonical chain too. Confirm wrapper/runtime/configuration pins, policy-to-route bindings, explicit source outbound enablement, and canonical token mappings across all participants before moving funds; module bindings and router endpoints are not replaced.
3. Schedule/execute the source governance proposal. Review the economic NFT, source pool, next custody epoch, immutable home identity, canonical asset mappings, and earliest execution time. Each move has an additional two-day migration delay; the keeper does not select a new chain autonomously.
4. A keeper calls `ZZZMigration.execute` after the delay, paying the bridge's native fee from operator funds. Watch source finality and provider status. No timeout permits a principal refund.
5. Verify destination `PrincipalAccepted`/`ImportPending`, the retained accepted-message snapshot, epoch, and exact token backing. A revisited satellite must have a drained old `Remote` record and accept a strictly newer local epoch. A keeper calls receiver `finalize` with fresh bounds; failed LP activation is retried without redirecting principal.
6. Call destination `acknowledge(migrationId, reverseRouteId)` for source completion. Confirm that the immediately previous source becomes `Remote` and its plan completes. When that source is the canonical home, this ACK also records the new home location.
7. For an onward hop between satellites, also call `acknowledgeHome(migrationId, homeRouteId)`. Verify canonical location events in strict next-epoch order. An out-of-order notification must be retried after earlier location updates; historical exact retries cannot regress the location. ACKs use the retained hop snapshot even if custody has since moved again.
8. On canonical return, location is recorded atomically during principal import; do not construct a self-chain home ACK. Send source completion to the satellite that released custody. No imported hop remints the NFT or adds contribution Power.
9. Drain funded old remote reward budgets through their historical authorized routes, even after principal has left a source. The keeper attempts reviewed reward routes in Active, Outbound, Remote and Inbound states; it performs LP operations only in Active. Immutable NFT/token provenance selects the canonical asset; satellite dust joins the funded individual budget. Keep reward and principal reconciliation separate.

Source failure before successful submission reverts that transaction. Failure after a provider has taken custody requires its provider-specific recovery process, which is **not implemented by the generic router or adapter**. There is no safe catch-all admin recovery address. Real SDK wrappers and live bridging remain deferred until separately implemented, reviewed and staged.

This procedure covers equivalent-asset custody hops, not arbitrary asset conversion, moving the NFT off its canonical chain, or satellite holder top-ups. The requested Robinhood native-ETH/hooked pool remains unsupported and its reward integration is deferred.

## Incident and alert rehearsal

Before funded operation, configure and test alerts for keeper/indexer heartbeat, confirmed-block lag, deep reorg halts, oracle stale/down/recovery states, low keeper native balance, ambiguous nonce age, reverted maintenance, reward liabilities versus balances, principal/idle attribution, and source/destination migration epochs. Track both source-completion and canonical-location ACKs: a home location notification alone does not clear a pending source plan. Retry the correct retained ACK after verifying earlier epochs; do not edit on-chain locations or reset custody counters.

For an incident, preserve chain observations, logs and durable state first; stop the keeper signer if its key/RPC identity is uncertain. The guardian can pause strategy operations, but claims and authenticated inbound settlement remain available. Use timelocked governance for approved configuration changes. Rebuild the indexer from a verified deployment checkpoint and compare its ownership/event projection before resuming. Provider custody loss or unavailable delivery requires that provider's reviewed recovery protocol, which remains a release blocker here. Rehearse restoration and signer recovery on test infrastructure; these procedures have not been exercised on a funded deployment.
