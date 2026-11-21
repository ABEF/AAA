# Ubuntu normal-keeper qualification: isolated execution plan

21 November 2026. Baseline `a5570c95bbaba7472ba5370e43494b87246e0ea7`.
User-selected operating target: Ubuntu. Production remains NOT APPROVED.

The earlier Q06 Linux/systemd campaign used an inert signer and recovery-only
dispatcher. Reuse its valid source/failure evidence; advance the missing stock
daemon and real encrypted Cast path instead of repeating that campaign or the
Windows contract/economic suites.

## Environment and boundaries

Read-only inventory finds Ubuntu24.04.3/Python3.12.3/systemd255 and native
Foundry1.4.4 on the existing authorized host. Local Windows has no installed WSL
or container runtime. Existing staging Anvil is already failed; installed keeper
is inactive, nginx/observer timer remain active. Preserve those installed units,
all their files/credentials/journals and the paused desktop heartbeat.

Use a NEW root-owned lab, verified readonly tool/source copies and separate
resource-bounded transient units. Workers run unprivileged. The cache, persistent
Anvil and keeper share a NEW private network namespace; the keeper has its own
cgroup so its restart cannot reset the test chain or cache.

Only authenticated fixed-anchor read-cache entries enter the offline fork peer.
Cache misses fail closed, never return guessed zero or fabricate latest state.
Any necessary bounded public read prefetch happens outside the private namespace
before live signing, with exact source/request/result provenance, then the cache
is frozen. No private signer has public network access.

## Minimal useful journey

1. Restore the authenticated normal39-instance F6 Entry state into the owned
   Anvil. Verify source/runtime/head identity. Align only the owned chain clock
   with Ubuntu wall time and refresh controlled feed timestamps, keeping their
   answers unchanged. These remain fixtures, not current market-price evidence.
2. Create an encrypted disposable wallet privately; never publish key/password,
   encrypted keystore, wallet-new output or environment contents. Fund and
   authorize it only on the owned Anvil using existing fixture governance, then
   end setup impersonation. Stock `--initialize-state` must accept its nonce0.
3. Run actual `python3 -m keeper.monitor --config NEW --live`, with real Cast and
   the selected safeguards/budgets. Harvest is enabled; disabled optional jobs
   are recorded. An actual zero-fee harvest is useful signing/recovery evidence
   and is not described as a new fee-economics qualification.
4. Gate recovery after a real broadcast and durable hash. Prove a competing
   normal process cannot acquire the same lock. Kill/restart only the owned
   keeper, then recover the same hash once without resend or editing the journal.
   Verify actual nonce, receipt, spend and authenticated harvest clock.
5. Exercise bounded local RPC failure/failover and unhealthy/healthy observations.
   Evaluate a useful new body-stall case without weakening transport/watchdog
   guards; record which existing protection actually fires. No external alert
   messages are sent. Finish with normal SIGTERM and no unintended restart.

Keep the default hourly harvest and existing24M/full25% maintenance profile.
Any shorter fixture polling cadence is explicit, not a production default change.
Use immutable published source blobs, not the four unrelated dirty worktree files.
All evidence collection uses an explicit secret-free allowlist. Retain original
failures and source stages; stop every owned unit/process and preserve test
journals/state. Remove only validated new disposable credentials after cleanup.

## Acceptance limits

This finite Ubuntu/normal-loop/real-Cast proof does not approve production keys,
providers, complete Robinhood fees, actual market inputs, all enabled jobs,
off-host fencing/restore, external alert delivery or sustained operation. It
authorizes no installed-service rollout, public transaction, contract deployment,
sealing, website change, old-chain reset or operating journal migration.
