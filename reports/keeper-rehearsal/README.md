# Keeper service and operating rehearsals

2026-10-16. Internal operating qualification, **not independent audit or production approval**.
This work changes keeper operating tools and test fixtures, not the Solidity
custody/economic implementation. Other pre-existing unpublished repository changes
are outside this publication and remain preserved.

## Evidence

- Current reviewed runtime commit `089d391c1689c2036db518c7a9705989896a14d8`:
  **209 Ubuntu tests, zero failures/skips, and all 14 process rehearsals passed**
  in [run 38961988650](https://github.com/ABEF/AAA/actions/runs/38961988650).
  Exact logs and source-bound receipts are in `ubuntu-089d391/`.
  `server-089d391.json` independently records all 14 cases passing on the Ubuntu
  staging host with the same source hashes. `server-operating-observation.json`
  records the active isolated services, resource/network restrictions, healthy
  keeper, preserved accounting and unchanged website index hashes. These are
  initial operating checks; the multi-day soak is **not complete**.
- `ubuntu-f53fb2b/`: 194 Ubuntu unit tests, zero failures/skips, and **14 actual
  process scenarios** passed in [run 38959176755](https://github.com/ABEF/AAA/actions/runs/38959176755).
  Receipts bind the exact source hashes. The earlier failed run in `attempt1/`
  exposed missing provenance addresses in the test venue; these were supplied
  rather than relaxing the keeper's validation. Historical evidence is retained.
- The same 14-case process suite passed on the authorized Ubuntu website host,
  as unprivileged `zzz-stage` inside a resource-limited systemd job. It exercises
  real local RPC, encrypted cast signing, killed process groups, receipt accounting,
  nonce/budget preservation, missing/corrupt/unwritable state, wrong-chain/outage
  fallback and invalidated confirmed anchors. The fixture has no real LP/revenue.
- The persistent local-chain staging services passed initial maintenance and
  canonical receipt settlement, graceful restart during pending recovery and a
  forced SIGKILL/automatic restart, preserving the recorded nonce and spending.
- A state snapshot was copied over SSH to the operator's desktop, integrity checked,
  copied back, verified against unchanged current state and restored while the
  sole keeper service was stopped. This proves a controlled **same-server** restore;
  a physically different production host and lost-key governance rotation remain open.
- A forced-command SSH monitor was checked for successful read-only health/backup
  retrieval, ignored arbitrary command requests and rejected port forwarding.
  Five-minute local export plus a 30-minute desktop heartbeat is staging monitoring,
  not an independently hosted production alarm service.
- The off-host check reported failure when the keeper was deliberately stopped
  and success after restart and a fresh health/export cycle. The active
  `popl-staging-health` chat heartbeat preserves off-host snapshots and stays
  quiet on unchanged healthy observations. It requires the desktop to remain
  available; observation gaps and retention require review.
- Fresh exact-source CI/host receipts are added alongside this report. Do not treat
  an earlier source hash as evidence for later changed code.

## Actual Robinhood RPC observation

`robinhood-rpc-observation.json` records a bounded, read-only mainnet probe.
Endpoint index 0 was `https://rpc.mainnet.chain.robinhood.com`, listed in the
[official wallet setup](https://docs.robinhood.com/chain/add-network-to-wallet/);
it returned HTTP 403 from this environment. This is a failed observation, not a
claim of a worldwide provider outage. Index 1 was the existing Pinax endpoint,
`https://robinhood.rpc.pinax.network`, which passed the recorded method checks.
Overall multi-provider compatibility remains **false**. The original probe before
the unknown-hash rejection check is preserved in `robinhood-rpc-observation-v1.json`.

The sampled ordinary receipts expose `gasUsed` and `effectiveGasPrice`, with no
separate `l1Fee` and `gasUsedForL1` zero in these samples. Arbitrum documents a
[combined L1/L2 fee model](https://docs.arbitrum.io/how-arbitrum-works/inside-arbitrum-nitro)
and [combined gas estimation](https://docs.arbitrum.io/build-decentralized-apps/troubleshooting-building).
This supports investigating inclusive accounting, but three unrelated receipts
do not prove full costs for every keeper operation, fee configuration or congestion
condition. **Production fee policy stays unverified.**

## Internal review boundaries and remaining work

The new readiness check never signs or mutates state. Snapshot publication is
atomic/exclusive, omits config contents and signer material, and never automatically
restores or deletes recovery evidence. Integrity hashes are not authentication;
freshness must be reconciled against the chain and the old host fenced. Failed
or stale health/backup checks return nonzero and retain sanitized reasons.

The rehearsal accepts only its own loopback Anvil and disposable signer. Server
staging blocks non-loopback egress, uses root-owned code/pinned Foundry binaries,
limits resources and isolates keys from its read-only observer. Operator/root
compromise, cross-host fencing and real governance remain separate trust boundaries.

Open gates: sustained multi-day soak and observation gaps; independently hosted
alerts/backup retention; actual Robinhood Testnet end-to-end operation; qualified
redundant RPCs and real fee budgets; real oracle/VRF/creator terms and authority
addresses; actual pool/strategy execution and market conditions; physical server
loss and key rotation; independent audit and release/configuration approval.
No public contracts were deployed or public-chain transactions submitted.
