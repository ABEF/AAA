# Development and operating procedures

**No mainnet launch or funded deployment is approved.** Current development build/test evidence is recorded in [the implementation update](../reports/IMPLEMENTATION_UPDATE.md); it does not verify a live provider transport, destination deployment, or real Uniswap lifecycle.

## Build and configuration

Install a reviewed Foundry toolchain and Node/npm on a networked development host. Run `scripts/install-deps.sh`, inspect the resolved versions/lockfile, then `scripts/verify.sh`. Retain the complete compiler output, runtime sizes, fuzz seeds and test results. Run Slither separately and triage every finding rather than merely suppressing it.

The supplied `DeployCore.s.sol` template is restricted to local chain IDs 31337/31338. It expects existing local Uniswap contracts and an explicitly selected test transport. It binds all 16 modules but deliberately does not seal configuration. It was not executed here.

For each deployment, record: chain ID and canonical NFT chain ID; contract addresses and runtime bytecode hashes; constructor arguments, including the immutable mint-proceeds recipient; PosM/PoolManager/StateView/Permit2 identities; token decimals and code/proxy authorities; USD feed denomination/heartbeat; sequencer feed; governance/guardian/keeper roles; supported burn mechanism; every complete principal, source-completion ACK, canonical-location ACK, and reward route.

Configure feeds first, reward assets next, pools next and initial routes on the participating chains last. All required local identities must match module bindings. Review dependency ownership/proxy powers as well as their current code hashes. Seal only after an independent deployment review: sealing freezes module bindings, while new append-only route identities require timelocked governance afterward. The bridge adapter's transport endpoint remains immutable.

Mint, activation, and holder top-ups require `seal()`. Verify the exact 0.05 ETH mint price, isolated constructor-selected recipient, and the $500 actually deployed LP activation minimum on a test deployment. There is no general emergency rescue or admin withdrawal after sealing. A mistaken token/route/provider setting can strand capital indefinitely.

## Keeper

Python 3.11+ and a Unix host are expected. Copy `keeper/config.example.json`, fill real local/testnet settings and leave `reviewed_for_live_use=false`.

```bash
python3 -m keeper.monitor --config keeper/config.local.json --once
```

The example has no active jobs. Configure explicit NFT IDs, minimum liquidity, fee thresholds and pool IDs; do not infer them from untrusted front-end input. A position job can include `compound=true`, its two `tokens`, `minimum_compound_units`, `harvest=true`, `harvest_interval_seconds`, and reviewed `reward_routes`. Buyback tasks supply a fee token, exact amount and direct approved pool ID.

For a reviewed test deployment, live mode additionally requires `--live`, reviewed runtime hashes for configured contracts, a matching encrypted `cast` wallet and private regular keystore/password files. Use a dedicated low-balance account with only keeper permissions. Do not use the governance wallet.

The program serializes transactions and writes intended nonce, destination, calldata and value durably before invoking the signer. A timeout/error leaves an ambiguous pending record. It must not be deleted just to force a retry.

```bash
python3 -m keeper.monitor --config keeper/config.local.json --resolve-pending 0xREVIEWED_TRANSACTION_HASH
```

This recovery path verifies sender, nonce, destination, calldata, value, confirmations and canonical receipt block. If the transaction was never broadcast or was replaced/dropped, investigate the account across trusted nodes before a human edits recovery state; there is no automatic blind nonce replacement. Preserve state files and audit logs.

Gas-price, per-transaction and daily budgets apply to estimates; configure a conservative L1-fee allowance on rollups. Actual confirmation costs update accounting. These estimates are not a guarantee against a malicious RPC or changing chain-specific fee rules.

`keeper/zzz-keeper.service` is a hardening template, not an installed service. Adjust executable/config paths and service user. It defaults to dry run. Production monitoring should alert on staleness, oracle failures, missing confirmations, ambiguous nonces, missed keeper cycles, low native balance and repeated skipped positions.

## Indexer

```bash
python3 -m indexer.monitor --config indexer/config.local.json --once
```

Set a known deployment start block and parent hash, appropriate confirmations and reorg bound, and only reviewed contract addresses. Each SQLite cursor is tied to its chain, starting point and tracked contract set. Changing that identity requires an explicit rescan/new database.

Logs, block headers and the cursor commit atomically. Orphan blocks/logs are rolled back to the common ancestor. A reorg deeper than the configured safety bound halts rather than guessing. Raw events remain available when a signature is unknown or not projected into application views.

The SQLite database is an off-chain cache, not proof of ownership. Claims and custody must rely on contracts. Back up the database/configuration; a confirmed-block rescan must reproduce it. Verify multiple RPC sources for sensitive operational decisions.

## Deliberate migration procedure

1. Review compatible destination runtime code and custody/proxy authorities, economically equivalent tokens at identical decimals/nominal units, and actual provider funding/finality/retry behavior. A timelock notice is not proof of perpetual destination custody.
2. Onboard any missing append-only principal, source-completion ACK, canonical-location ACK, and reward routes through each deployment's governance timelock. For a satellite B-to-C hop, register its remote-only principal graph edge on the canonical chain too. Confirm routes and canonical token mappings across all participants before moving funds; module bindings and transport endpoints are not replaced.
3. Schedule/execute the source governance proposal. Review the economic NFT, source pool, next custody epoch, immutable home identity, canonical asset mappings, and earliest execution time. Each move has an additional two-day migration delay; the keeper does not select a new chain autonomously.
4. A keeper calls `ZZZMigration.execute` after the delay, paying the bridge's native fee from operator funds. Watch source finality and provider status. No timeout permits a principal refund.
5. Verify destination `PrincipalAccepted`/`ImportPending`, the retained accepted-message snapshot, epoch, and exact token backing. A revisited satellite must have a drained old `Remote` record and accept a strictly newer local epoch. A keeper calls receiver `finalize` with fresh bounds; failed LP activation is retried without redirecting principal.
6. Call destination `acknowledge(migrationId, reverseRouteId)` for source completion. Confirm that the immediately previous source becomes `Remote` and its plan completes. When that source is the canonical home, this ACK also records the new home location.
7. For an onward hop between satellites, also call `acknowledgeHome(migrationId, homeRouteId)`. Verify canonical location events in strict next-epoch order. An out-of-order notification must be retried after earlier location updates; historical exact retries cannot regress the location. ACKs use the retained hop snapshot even if custody has since moved again.
8. On canonical return, location is recorded atomically during principal import; do not construct a self-chain home ACK. Send source completion to the satellite that released custody. No imported hop remints the NFT or adds contribution Power.
9. Drain funded old remote reward budgets through their historical authorized routes, even after principal has left a source. Immutable NFT/token provenance selects the canonical asset; satellite dust joins the funded individual budget. Keep reward and principal reconciliation separate.

Source failure before successful submission reverts that transaction. Failure after the transport has taken custody requires its provider-specific recovery process, which is **not implemented by this generic adapter**. There is no safe catch-all admin recovery address.

This procedure covers equivalent-asset custody hops, not arbitrary asset conversion, moving the NFT off its canonical chain, or satellite holder top-ups. The requested Robinhood native-ETH/hooked pool remains unsupported and its reward integration is deferred.
