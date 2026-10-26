# Keeper operations audit and remediation - 2026-10-26

Scope: current main9fe9997, keeper signing/recovery, read RPC, exact fees,
state durability and read-only operations. This is an internal scoped review,
not universal safety proof or production approval. No public or local financial
operation, real RPC, installed service, existing Anvil8902/journal, browser signer,
website or paused monitor was changed. The four unrelated dirty files were not
edited or tested by this slice.

## Confirmed finding and fix

**OPS-1: a fresh heartbeat could certify the wrong deployment/configuration.**
`Keeper.run_cycle` emitted chain and sender but no contract/profile/policy identity.
`health_check` accepted that artifact against a configuration for another Vault
with the same chain/signer/path, a different accounting/intake profile, or changed
provider/limits. Missing/malformed identity was also silently accepted.
This is a monitoring correctness/availability risk, not an unauthorized transfer
or an on-chain accounting defect.

The new six-method test uses the real Keeper heartbeat writer and read-only health
checker. Only the cycle body is mocked; no RPC or signer is contacted. Before:
the matching-config control passed and ten subcase assertions failed across five
methods. Original diagnostics are preserved in health-identity-before.log.

The writer now records configuration_sha256 of its exact loaded JSON configuration;
the checker requires the same canonical SHA-256. Config contents, credentialed
endpoints and signer-file paths are not exported. Old/missing/malformed or mismatched
artifacts return configuration_mismatch and cannot be healthy. Existing synthetic
Ops fixtures now contain the new binding. Journals, nonce/receipt recovery,
fee reviews, snapshot schema and contract/profile semantics are unchanged.

### Operator consequence

Deploy writer/checker together only in a separately authorized service rollout.
After a reviewed configuration change, require a fresh heartbeat from that matching
loaded configuration. Do not edit an old artifact's hash, clear a journal, reset a
chain or restart the paused monitor to make it pass. This configuration hash is
not a signature: preserve trusted transport, host/filesystem integrity, independent
alerts and actual preflight. It does not prove a service is honest or qualified.

## Reviewed controls retained without speculative edits

- Durable intent precedes the external signer. Exact target/calldata/value/nonce
  and signing-time fee review survive ambiguous stdout, failure or timeout;
  no automatic resend is performed.
- Pending receipt recovery precedes new work and verifies sender/target/hash,
  chain, nonce, economic fields, signed gas/cap and receipt inclusion. Canonical
  depth/header/timestamp are rechecked before atomic cost/nonce checkpointing.
- Dynamic execution prices derive from signed fee caps plus canonical base fee;
  inclusion-day actual spend and reverted gas are counted once. Separate L1 fees
  retain the original review/allowance; unknown/mismatched cost stops new work.
- Used signer checkpoints, both nonces, code/profile pins, lifecycle and current
  balance/stop request are checked before new submission. Immediate governance
  and dependency trust remain; simulation cannot guarantee later inclusion.
- State writes use private random temporary files, flush/fsync and atomic replace;
  directory durability is required on supported Unix before signing. A failed
  recovery save preserves old in-memory intent/costs. Locking is one-host only;
  second-host fencing and restoring actual nonce/cost state remain operator work.
- Ops snapshots are exclusive and secret-free; their hash detects corruption,
  not forged backup provenance. Verify age/identity/configuration and on-chain
  freshness separately before any restoration. No automatic repair is provided.
- RPC methods remain read-only, redirects refused, response size/request identity
  bounded and endpoint chain rechecked. No source change was justified here.
  Socket timeouts do not prove a provider/service-level uptime or total wall-time
  guarantee; target hosting, off-host stale-heartbeat alerts and real failover
  qualification remain required.

## Excluded hypothesis

A bounded nested-JSON transport probe was expected to expose a nonretryable parse
failure. On the actual Python3.12.14 runtime, all three probe methods already passed
on the unchanged RPC source. Its source and original log are retained as excluded
research evidence. No RPC change or passing-fix claim is made from that hypothesis;
this does not prove every arbitrary depth or provider safe.

## Verification and evidence

Final command:

    python -X utf8 -m unittest -v tests_python.test_keeper_health_identity tests_python.test_keeper_ops

Nineteen distinct methods pass (six new, thirteen existing affected Ops). No
unchanged Solidity, full keeper regression, actual provider or operating rehearsal
was rerun by this slice. Repeated or excluded diagnostic scopes are not added.
operations-evidence.json records exact test IDs and before/final source SHA-256s;
original owned source/fixture preimages are retained as before-*.txt.

The new regression module is tests_python/test_keeper_health_identity.py.
Only keeper/monitor.py and keeper/ops.py production code changed here; the new
module and one existing synthetic fixture complete its verification. State,
ethereum_fees and RPC remain byte-identical to the captured baseline.

Actual feed/route/VRF/OpenSea/authority choices, target gas and fee economics,
current services, authenticated off-host alerts/recovery, frozen release and
independent audit/remediation remain open. Production is NOT APPROVED.

## Final compatibility follow-up

The parent's358-method affected attempt exposed one health-fixture assumption:
KeeperPreparationTests.test_preparing_skips_rebalance_compound_buyback_and_keeps_healthy_observation
mutated the original configuration after Keeper construction and then expected
that changed configuration to match the old loaded identity. The original
aggregate failure remains in the parent's evidence; it is not relabeled passed.

The loaded fingerprint remains frozen. Rehashing mutable config at heartbeat
write time could incorrectly label cached self.contracts/accounting fields as
a different reviewed deployment. Production main loads configuration once and
provides no runtime reload API. The fixture now finalizes buybacks/maintenance
before constructing its Keeper, retaining all preparation/no-submit assertions.
Only that failed method was rerun, and it passes (health-preparation-fixture-after.log).
No production source changed for this compatibility correction. The original
19-method source scope remains intact; this adds one affected existing method,
not a second complete358-method pass. Do not sum overlapping parent/child runs.
