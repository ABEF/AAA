# Keeper service qualification and rehearsal

This is an operating candidate, not production approval. The protocol is still
undeployed. No public signing or real funds are needed for the isolated rehearsal.

## Repeatable isolated rehearsal

On an unprivileged Ubuntu user with Python 3.11+ and Foundry **1.4.4**:

```sh
python3 scripts/rehearse-keeper.py --output var/keeper-rehearsal.json
```

The command starts its own loopback Anvil, compiles a test-only venue with Solidity
0.8.26, creates a disposable encrypted signer and kills child process groups at
specific broadcast boundaries. It accepts no external RPC, real wallet or production
configuration. Temporary keys and local-chain data are removed at the end. The
JSON receipt binds every tested source and records each completed case. Failure
or missing cases do not count as qualification. CI runs it in Keeper safety regression.

Covered scenarios include receipt/cost settlement exactly once; restoration to a
new runtime directory; old-backup nonce drift; paused/revoked roles; low funds;
real HTTP outage/wrong-chain fallback; process locking; missing/corrupt state;
unwritable runtime storage; process death before/after broadcast; and invalidated
confirmed receipt anchors. An aged maintenance timestamp tests current-state
evaluation instead of replaying missed intervals. **It is not a multi-day soak**.

The venue models the keeper-facing ABI and counters only. It does not qualify
Uniswap/Pons trading, price feeds, real rewards/royalties, gas economics, metadata
marketplace refresh, real server isolation, systemd lifecycle or Robinhood services.

## Read-only checks and snapshots

Run these from the repository with the reviewed deployment configuration:

```sh
python3 -m keeper.ops --config /etc/zzz/keeper.json preflight
python3 -m keeper.ops --config /etc/zzz/keeper.json health --max-age 1800
python3 -m keeper.ops --config /etc/zzz/keeper.json snapshot --output /backup/keeper-UNIQUE-TIMESTAMP.json
python3 -m keeper.ops --config /etc/zzz/keeper.json verify-snapshot --input /backup/keeper-UNIQUE-TIMESTAMP.json --max-age 3600
```

All commands emit a sanitized JSON result and return nonzero on failure. They
never sign or modify recovery state. `preflight` checks runtime pins, seal, role,
pause, head/receipt checkpoint, both nonces, pending intent, reviewed fee policy
and funding. A pass is a point-in-time observation, **not permission to start a
second host or proof of production qualification**. Existing ambiguous intent
must be reconciled through the keeper's exact-transaction recovery path.

`health` requires a fresh successful live cycle with no pending intent, paused
strategy, blocked action or skipped bucket. Use `--allow-dry-run` explicitly for
staging. A missing/corrupt/stale heartbeat fails. Run from an independent monitor
using an authenticated read-only transport; do not publish recovery files over HTTP.
Configure and test real alert delivery, including missing-host and stale-backup alerts.

Snapshots contain the recovery state, creation time, config hash and integrity
hash; they exclude config contents and signer material. Publication is atomic
and exclusive: existing snapshots/state files are never overwritten. It is safe
to capture one atomic state version while the keeper is running, but that version
can immediately become stale. A hash detects corruption, **not forged backups**.
Use a trusted, access-controlled off-host destination with retention and separate
encrypted key custody. A changed config (including host paths) requires review.
Verification checks integrity/age/identity, not on-chain freshness or authentication.

Stop/fence the old signer before restoration. Restore the state only after review,
then run `preflight` on the new host and reconcile every transaction after the
snapshot. Never clear a pending record or reset spend/nonce to make a check pass.
There is no automatic backup deletion, state restore, transaction replacement or
total-state-loss reconstruction tool.

## Gates requiring the actual staging environment

- [ ] Record reviewed release/configuration/binary hashes and single-host fencing.
- [ ] Qualify at least two independent RPCs, head/receipt/archive behavior,
  confirmations and actual Robinhood fee accounting under real service limits.
- [ ] Run the selected service through systemd start/stop/restart and signer-child
  termination on the intended Ubuntu image with restrictive users/directories.
- [ ] Run a multi-day soak with current prices and strategy settings, then an outage
  and recovery. Record unavailable/mocked dependencies explicitly.
- [ ] Deliver off-host alarms for dead service/host, RPC outage, stale head,
  pending/ambiguous transactions, low funds, reverts, failed backups and stale backups.
- [ ] Restore a trusted off-host backup on another server, prove the previous signer
  is fenced, reconcile nonces/costs and test governance key revocation/replacement.
- [ ] Exercise disk exhaustion, full host loss and an undiscoverable transaction
  hash. Demonstrate the stop/escalation path; no blind resubmission is permitted.
- [ ] Complete Robinhood Testnet wallet/API/keeper/deployment rehearsal and an
  independent review of contracts, operations and configuration before real funds.

The central [Todo](../TODO.md), [release checklist](RELEASE_CHECKLIST.md) and
[recovery runbook](KEEPER_RECOVERY.md) retain these gates.
