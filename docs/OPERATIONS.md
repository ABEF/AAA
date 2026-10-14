# Development and operating procedures

**All Solidity steps are unverified in this environment. No mainnet launch is approved.**

## Build and configuration

Install a reviewed Foundry toolchain and Node/npm on a networked development host. Run `scripts/install-deps.sh`, inspect the resolved versions/lockfile, then `scripts/verify.sh`. Retain the complete compiler output, runtime sizes, fuzz seeds and test results. Run Slither separately and triage every finding rather than merely suppressing it.

The supplied `DeployCore.s.sol` template is restricted to local chain IDs 31337/31338. It expects existing local Uniswap contracts and an explicitly selected test transport. It binds all 16 modules but deliberately does not seal configuration. It was not executed here.

For each deployment, record: chain ID and canonical NFT chain ID; contract addresses and runtime bytecode hashes; constructor arguments; PosM/PoolManager/StateView/Permit2 identities; token decimals and code/proxy authorities; USD feed denomination/heartbeat; sequencer feed; governance/guardian/keeper roles; supported burn mechanism; every complete migration/reward/acknowledgement route.

Configure feeds first, reward assets next, pools next and paired routes on both chains last. All required local identities must match module bindings. Review dependency ownership/proxy powers as well as their current code hashes. Seal only after an independent deployment review: sealing freezes module and route identities permanently.

No deposits work before `seal()`. There is no general emergency rescue or admin withdrawal after sealing. A mistaken token/route/provider setting can strand capital indefinitely.

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

1. Independently verify a fully preconfigured principal route, reverse ACK route and one reverse reward route per fee asset; verify destination vault compatibility and finality assumptions.
2. Schedule/execute the governance proposal. Review the source economic NFT, source pool, amount estimates and earliest execution time.
3. A keeper calls `ZZZMigration.execute` after the delay, paying the bridge's native fee from operator funds. Watch both source transaction finality and provider status; no source timeout permits a refund.
4. Verify the destination `PrincipalAccepted`/`ImportPending` records and exact token backing. A keeper calls receiver `finalize` with fresh bounds. Failed activation is retried without redirecting principal.
5. Send/retry the reverse acknowledgement. Confirm source `Remote` status and the exact destination location. Remote NFT rewards subsequently return via configured reward routes for canonical claims.

Source failure before successful submission reverts that transaction. Failure after the transport has taken custody requires its provider-specific recovery process, which is **not implemented by this generic adapter**. There is no safe catch-all admin recovery address.
