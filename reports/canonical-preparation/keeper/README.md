# Preparation-aware keeper verification

This is internal candidate verification, not independent audit or production
approval. No server configuration, deployed staging binary, public RPC/signature
or real asset movement was changed.

## Executed evidence

[The final receipt](verification.json) records **185 tests passed, zero failures,
errors or runtime skips**, from a 186-case inventory. The single explicit
exclusion is
`tests_python.test_keeper_recovery.RecoveryTests.test_runtime_permissions_and_symlinks_fail_closed`,
which requires POSIX ownership/permissions/symlinks unavailable on this Windows
host. The pinned Foundry `cast` CLI parser test actually ran; its binary hash is
recorded. [Raw final output](tests.log), exact before/after dependency hashes,
case IDs and [the runner](run_scoped.py) accompany the receipt. All hashed files
were unchanged during this run.

The fourteen new tests exercise real static-ABI decoding and the keeper's
submission path with fake RPC/signing subprocesses. They cover malformed and
unsupported getters, all three deferred actions, an announcement appearing at
the final balance read, unknown final state, cancellation, pending recovery,
funded inbox and remote reward delivery, harvest, metadata, transition logging,
health and preflight. Existing receipt/nonce/budget and metadata regressions were
run with them. No new real-process Anvil rehearsal was executed here;
`KeeperVenue.sol` is hash-bound as an updated local fixture only.

[Earlier attempts](prior-attempts.json) remain separate: a fixture method-name
typo, missing preparation flag in an existing explicit mock dictionary, and a
pass with two skips before fixing the child Python PATH and explicit Unix
selection. Those first attempts were console-only, so the record preserves
their outcomes and available console excerpts, not an invented complete raw log.
They are not merged into the final passing result.

## Operating interface and compatibility

The keeper requires a canonical single ABI boolean from the configured
controller's `preparationActive()`. Empty, malformed, noncanonical or reverted
responses fail closed. There is no default-false compatibility branch. Reviewed
deployment/runtime pins must identify a controller implementing this interface.
The existing deployed staging release and its older fixture/keeper are untouched;
this work does not assert that they support the new getter. Updating only the
keeper against that older fixture would stop new submissions until the complete
reviewed deployment is made compatible.

Preparation defers rebalance, compound and buyback. It leaves pending receipt
reconciliation, metadata refresh, fee harvest, funded inbox settlement and funded
reward delivery available. Existing pause behavior is separate and retained.
Submission checks preparation before simulation, after fee estimation, and before
durable intent/signing. The contract guards cover a subsequent state change before
transaction inclusion; the RPC check cannot guarantee ordering of future blocks.

Health exposes `preparation_active` as a required boolean. A healthy intentional
preparation window stays healthy and can be distinguished from errors. Unknown
older health schemas return `preparation_state_unknown`; preflight reports
`canonical_preparation_active` as a restriction on full maintenance readiness.
Logs record observed transitions rather than an unchanged announcement each cycle.

## Independent internal source review

The separately assigned reviewer identified the original migration baseline gap:
taking it after mutable harvest calls could hide principal loss during those
calls. The implementation now snapshots principal and attributed idle before
harvest and adds only the exact subsequent attributed-idle increase from compound
release. A dedicated adversarial Solidity test mutates principal and prices during
harvest; its execution belongs to the separate Solidity receipt.

No additional confirmed bypass was found in the reviewed helper/preparation
source. The immutable helper accepts checkpoints only from its creating Vault;
its external observations are static reads. Vault's reentrancy guard prevents a
second mutation between checkpoints. The cached price/decimal vector, rounded-up
97% floor and same-vector 5% idle ceiling cover close, balancing and minting for
the supported local ordered-pair move/resume paths. Failed checks roll back all
checkpoints and custody/accounting changes. Existing per-leg guards, destination
ordering and LP custody checks remain. The read-only valuation extraction does
not change the 1% activation/top-up arithmetic.

Preparation checks run both before and after new-work callbacks, including
Principal adapter sends. A matured timelock announcement inside a callback makes
the outer new work revert. Governance configuration receives the same trailing
check. The drain exception is limited to Migration cancellation, exact paused
parking and parking-nonce invalidation; it adds no arbitrary recipient or rescue
capability. Reward/ACK and authenticated inbound completion remain drains.

Protocol module configuration is restricted while preparing. Inherited timelock
role administration and operation scheduling/cancellation retain their existing
authority rules; this is not a freeze of every governance datum. The deployment's
governance delay remains fixed: the controller overrides `updateDelay` to revert.
The notice is local to the canonical controller and supplies no authenticated
instruction that stops a separately deployed satellite's keeper or custody.
Neither preparation nor this review supplies a canonical ledger freeze/export,
terminal commit, independent proof provider, asynchronous 3% guarantee or
protection against dishonest admitted price/token/venue dependencies. Initial
oracle accuracy, venue backing, wrappers and cumulative repeated-move losses
remain separate qualification/trust boundaries.
